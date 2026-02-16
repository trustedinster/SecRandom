import base64
import json
import os
import socket
import struct
import threading
import time
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import requests
from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto.Protocol.KDF import PBKDF2
from PySide6.QtCore import QObject, QStandardPaths, Signal, QTimer
from PySide6.QtWidgets import QHBoxLayout, QWidget
from loguru import logger
from qfluentwidgets import BodyLabel, GroupHeaderCardWidget, PushButton

from app.Language.obtain_language import (
    get_content_description_async,
    get_content_name_async,
)
from app.tools.personalised import get_theme_icon

CN_TZ = timezone(timedelta(hours=8))
_PENALTY_MARK = "SECTL_ALIPAY_PENALTY_V1"
_PENALTY_FILENAME = ".SECTL_ALIPAY_PENALTY"


@dataclass(frozen=True)
class _AlipayConfig:
    start_date_raw: str
    end_date_raw: str
    password_raw: str

    @property
    def start_dt(self) -> datetime:
        return _parse_shanghai_dt(self.start_date_raw)

    @property
    def end_dt(self) -> datetime:
        return _parse_shanghai_dt(self.end_date_raw)


def _parse_shanghai_dt(value: str) -> datetime:
    dt = datetime.strptime(value, "%Y-%m-%d_%H:%M:%S")
    return dt.replace(tzinfo=CN_TZ)


def _query_ntp_unix_seconds(server: str, timeout_seconds: float = 2.0) -> float:
    msg = b"\x1b" + 47 * b"\0"
    addr = (server, 123)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.settimeout(timeout_seconds)
        s.sendto(msg, addr)
        data, _ = s.recvfrom(1024)
    if len(data) < 48:
        raise ValueError("NTP response too short")
    unpacked = struct.unpack("!12I", data[0:48])
    tx_seconds = unpacked[10]
    tx_fraction = unpacked[11]
    ntp_time = tx_seconds + tx_fraction / 2**32
    return ntp_time - 2208988800


def _format_countdown(delta_seconds: int) -> str:
    delta_seconds = max(0, int(delta_seconds))
    hours = delta_seconds // 3600
    minutes = (delta_seconds % 3600) // 60
    seconds = delta_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


class _Signals(QObject):
    ntp_synced = Signal(float)
    config_loaded = Signal(object)
    config_failed = Signal(str)


class AlipayPasswordCard(GroupHeaderCardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._signals = _Signals()
        self._signals.ntp_synced.connect(self._on_ntp_synced)
        self._signals.config_loaded.connect(self._on_config_loaded)
        self._signals.config_failed.connect(self._on_config_failed)

        self.setTitle(get_content_name_async("about", "sectl_alipay_password"))
        self.setBorderRadius(8)

        self._status_label = BodyLabel(
            get_content_name_async("about", "sectl_alipay_loading")
        )
        self._status_label.setWordWrap(True)

        self._copy_button = PushButton(
            get_content_name_async("about", "sectl_alipay_copy_password")
        )
        self._copy_button.setEnabled(False)
        self._copy_button.clicked.connect(self._copy_password)

        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(8)
        row_layout.addWidget(self._status_label, 1)
        row_layout.addWidget(self._copy_button, 0)

        self.addGroup(
            get_theme_icon("ic_fluent_payment_20_filled"),
            get_content_name_async("about", "sectl_alipay_password_item"),
            get_content_description_async("about", "sectl_alipay_password_item"),
            row,
        )

        self._cfg_lock = threading.Lock()
        self._config: _AlipayConfig | None = None
        self._config_error: str | None = None
        self._config_last_fetch_monotonic = -1e9
        self._config_fetching = False

        self._ntp_lock = threading.Lock()
        self._ntp_base_unix: float | None = None
        self._ntp_sync_monotonic: float | None = None
        self._ntp_last_sync_monotonic = -1e9
        self._ntp_syncing = False

        self._revealed_password: str | None = None

        self._timer = QTimer(self)
        self._timer.setInterval(250)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

        self._trigger_config_fetch()
        self._trigger_ntp_sync()

    def _get_penalty_until_unix(self) -> int:
        payload = self._read_penalty_payload()
        if not payload:
            return 0
        if payload.get("mark") != _PENALTY_MARK:
            return 0
        try:
            return int(payload.get("until_unix", 0))
        except Exception:
            return 0

    def _ensure_penalty(self, now_unix: int, until_unix: int):
        until_unix = max(int(until_unix), 0)
        if until_unix <= 0:
            return
        existing = self._get_penalty_until_unix()
        if existing >= until_unix:
            return
        payload = {
            "mark": _PENALTY_MARK,
            "at_unix": int(now_unix),
            "until_unix": int(until_unix),
        }
        self._write_penalty_payload(payload)

    def _render_penalty(self, now_unix: int, penalty_until_unix: int) -> bool:
        if penalty_until_unix <= 0:
            return False
        remain = int(penalty_until_unix - now_unix)
        if remain <= 0:
            return False
        self._status_label.setText(
            get_content_name_async("about", "sectl_alipay_penalty_active").format(
                countdown=_format_countdown(remain)
            )
        )
        self._copy_button.setEnabled(False)
        return True

    def _get_documents_root(self) -> Path | None:
        try:
            doc_path = QStandardPaths.writableLocation(
                QStandardPaths.StandardLocation.DocumentsLocation
            )
            if doc_path:
                return Path(doc_path)
        except Exception:
            pass
        return None

    def _get_penalty_file_path(self) -> Path | None:
        root = self._get_documents_root()
        if root is None:
            return None
        return root / _PENALTY_FILENAME

    def _read_penalty_payload(self) -> dict | None:
        path = self._get_penalty_file_path()
        if path is None:
            return None
        try:
            if not path.exists():
                return None
            text = path.read_text(encoding="utf-8", errors="strict")
            data = json.loads(text)
            if isinstance(data, dict):
                return data
            return None
        except Exception:
            return None

    def _write_penalty_payload(self, payload: dict):
        path = self._get_penalty_file_path()
        if path is None:
            return
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path = path.with_name(f"{path.name}.tmp")
            tmp_path.write_text(
                json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
                encoding="utf-8",
                errors="strict",
            )
            os.replace(tmp_path, path)
            self._set_hidden_system_attributes(path)
        except Exception as e:
            logger.debug(f"写入惩罚文件失败: {e}")

    def _set_hidden_system_attributes(self, path: Path):
        try:
            import ctypes

            FILE_ATTRIBUTE_HIDDEN = 0x2
            FILE_ATTRIBUTE_SYSTEM = 0x4
            attrs = FILE_ATTRIBUTE_HIDDEN | FILE_ATTRIBUTE_SYSTEM
            ctypes.windll.kernel32.SetFileAttributesW(str(path), attrs)
        except Exception:
            return

    def _hide_card(self):
        if not self.isVisible():
            return
        try:
            if self._timer.isActive():
                self._timer.stop()
        except Exception:
            pass
        self.setVisible(False)

    def _maybe_hide_if_ended(self):
        now = self._get_now_shanghai()
        if now is None:
            return
        with self._cfg_lock:
            cfg = self._config
        if cfg is None:
            return
        if now > cfg.end_dt:
            self._hide_card()

    def _tick(self):
        self._maybe_hide_if_ended()
        if not self.isVisible():
            return

        now = self._get_now_shanghai()
        if now is None:
            self._status_label.setText(
                get_content_name_async("about", "sectl_alipay_syncing_time")
            )
            self._copy_button.setEnabled(False)
            self._trigger_ntp_sync()
            self._trigger_config_fetch()
            return
        now_unix = int(now.timestamp())

        penalty_until_unix = self._get_penalty_until_unix()
        if self._render_penalty(now_unix, penalty_until_unix):
            self._trigger_ntp_sync()
            self._trigger_config_fetch()
            return

        self._trigger_ntp_sync()
        self._trigger_config_fetch()

        with self._cfg_lock:
            cfg = self._config
            cfg_error = self._config_error

        if cfg is None:
            if cfg_error:
                self._status_label.setText(
                    get_content_name_async("about", "sectl_alipay_fetch_failed").format(
                        error=cfg_error
                    )
                )
            else:
                self._status_label.setText(
                    get_content_name_async("about", "sectl_alipay_loading")
                )
            self._copy_button.setEnabled(False)
            return

        if now < cfg.start_dt:
            seconds_left = int((cfg.start_dt - now).total_seconds())
            self._status_label.setText(
                get_content_name_async("about", "sectl_alipay_countdown").format(
                    countdown=_format_countdown(seconds_left)
                )
            )
            self._copy_button.setEnabled(False)
            return

        if now > cfg.end_dt:
            self._hide_card()
            return

        if self._revealed_password is None:
            try:
                self._revealed_password = self._decrypt_password(
                    cfg.password_raw, cfg.start_date_raw, cfg.end_date_raw
                )
            except Exception as e:
                logger.exception(f"支付宝口令解密失败: {e}")
                self._revealed_password = ""

        if self._revealed_password:
            self._status_label.setText(
                get_content_name_async("about", "sectl_alipay_revealed").format(
                    password=self._revealed_password
                )
            )
            self._copy_button.setEnabled(True)
        else:
            if now >= cfg.start_dt:
                self._ensure_penalty(now_unix, int(cfg.end_dt.timestamp()))
                penalty_until_unix = self._get_penalty_until_unix()
                if self._render_penalty(now_unix, penalty_until_unix):
                    return
            self._status_label.setText(
                get_content_name_async("about", "sectl_alipay_decrypt_failed")
            )
            self._copy_button.setEnabled(False)

    def _copy_password(self):
        if not self._revealed_password:
            return
        try:
            from PySide6.QtWidgets import QApplication

            QApplication.clipboard().setText(self._revealed_password)
        except Exception as e:
            logger.exception(f"复制支付宝口令失败: {e}")

    def _get_now_shanghai(self) -> datetime | None:
        with self._ntp_lock:
            base_unix = self._ntp_base_unix
            base_mono = self._ntp_sync_monotonic
        if base_unix is None or base_mono is None:
            return None
        now_unix = base_unix + (time.perf_counter() - base_mono)
        return datetime.fromtimestamp(now_unix, tz=timezone.utc).astimezone(CN_TZ)

    def _trigger_ntp_sync(self):
        with self._ntp_lock:
            if self._ntp_syncing:
                return
            if time.perf_counter() - self._ntp_last_sync_monotonic < 30:
                return
            self._ntp_syncing = True
            self._ntp_last_sync_monotonic = time.perf_counter()

        def job():
            try:
                unix_seconds = _query_ntp_unix_seconds("ntp1.aliyun.com")
                self._signals.ntp_synced.emit(float(unix_seconds))
            except Exception as e:
                logger.debug(f"NTP 同步失败: {e}")
            finally:
                with self._ntp_lock:
                    self._ntp_syncing = False

        threading.Thread(target=job, daemon=True).start()

    def _on_ntp_synced(self, unix_seconds: float):
        with self._ntp_lock:
            self._ntp_base_unix = unix_seconds
            self._ntp_sync_monotonic = time.perf_counter()
        self._maybe_hide_if_ended()

    def _trigger_config_fetch(self):
        with self._cfg_lock:
            if self._config_fetching:
                return
            if time.perf_counter() - self._config_last_fetch_monotonic < 60:
                return
            self._config_fetching = True
            self._config_last_fetch_monotonic = time.perf_counter()

        def job():
            try:
                resp = requests.get("https://aionflux.cn/alipay/alipay.json", timeout=6)
                resp.raise_for_status()
                data = resp.json()
                self._signals.config_loaded.emit(data)
            except Exception as e:
                self._signals.config_failed.emit(str(e))
            finally:
                with self._cfg_lock:
                    self._config_fetching = False

        threading.Thread(target=job, daemon=True).start()

    def _on_config_loaded(self, data):
        try:
            start_date = str(data.get("start_date", "")).strip()
            end_date = str(data.get("end_date", "")).strip()
            password = str(data.get("password", "")).strip()
            if not start_date or not end_date:
                raise ValueError("invalid alipay payload")
            _parse_shanghai_dt(start_date)
            _parse_shanghai_dt(end_date)
            cfg = _AlipayConfig(
                start_date_raw=start_date, end_date_raw=end_date, password_raw=password
            )
        except Exception as e:
            with self._cfg_lock:
                self._config = None
                self._config_error = str(e)
            return

        with self._cfg_lock:
            self._config = cfg
            self._config_error = None

        self._revealed_password = None
        self._maybe_hide_if_ended()

    def _on_config_failed(self, error: str):
        with self._cfg_lock:
            self._config = None
            self._config_error = error
        self._revealed_password = None

    def _decrypt_password(
        self, password_raw: str, start_date: str, end_date: str
    ) -> str:
        if not password_raw:
            return ""
        if not password_raw.startswith("enc:v1:"):
            return password_raw
        payload_b64 = password_raw[len("enc:v1:") :]
        raw = base64.urlsafe_b64decode(payload_b64.encode("utf-8"))
        if len(raw) < 16 + 12 + 16 + 1:
            raise ValueError("payload too short")
        salt = raw[0:16]
        nonce = raw[16:28]
        tag = raw[28:44]
        ciphertext = raw[44:]
        key_material = f"SECTL|ALIPAY|alipay|{start_date}|{end_date}".encode("utf-8")
        key = PBKDF2(
            key_material, salt, dkLen=32, count=200000, hmac_hash_module=SHA256
        )
        cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
        plaintext = cipher.decrypt_and_verify(ciphertext, tag)
        return plaintext.decode("utf-8", errors="strict").strip()
