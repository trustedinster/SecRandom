"""
SECTL 在线状态上报模块

本模块实现了向 SECTL API 上报在线状态的功能，用于统计在线人数。
客户端应定期调用此接口（建议每 1-2 分钟）来保持在线状态。
服务端会根据 last_active 时间判断用户是否在线（5分钟内活跃视为在线）。
"""

import json
import uuid
import socket
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Dict, Any

import requests
from loguru import logger

from app.tools.path_utils import get_data_path
from app.tools.variable import (
    SECTL_API_BASE_URL,
    SECTL_PLATFORM_ID,
    SECTL_ONLINE_REPORT_INTERVAL_MS,
    SECTL_ONLINE_REPORT_TIMEOUT_SECONDS,
    SYSTEM,
)


_DEVICE_UUID_FILE = "device_uuid.json"
_online_status_reporter: Optional["OnlineStatusReporter"] = None
_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="online_status")


def _detect_device_type() -> str:
    system = SYSTEM
    if system == "windows":
        return "windows-desktop"
    elif system == "macos":
        return "macos-desktop"
    elif system == "linux":
        return "linux-desktop"
    else:
        return "unknown-desktop"


def _get_local_ip() -> str:
    ip = None
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(2)
        try:
            s.connect(("8.8.8.8", 53))
            ip = s.getsockname()[0]
        finally:
            s.close()
    except Exception:
        pass

    if not ip or ip.startswith("127."):
        try:
            hostname = socket.gethostname()
            ip = socket.getaddrinfo(hostname, None, socket.AF_INET)[0][4][0]
        except Exception:
            pass

    return ip if ip else "127.0.0.1"


def _get_public_ip(timeout_seconds: float = 5.0) -> Optional[str]:
    services = [
        "https://uapis.cn/api/v1/network/myip",
    ]

    for service in services:
        try:
            response = requests.get(service, timeout=timeout_seconds)
            if response.status_code == 200:
                data = response.json()
                ip = data.get("ip")
                if ip:
                    return ip
        except Exception:
            continue

    return None


def _get_ip_location(ip: str, timeout_seconds: float = 10.0) -> Dict[str, Any]:
    if not ip or ip == "unknown" or ip.startswith("127.") or ip == "localhost" or ip.startswith("192.168.") or ip.startswith("10."):
        return {
            "country": "本地",
            "province": "本地",
            "city": "本地",
            "district": "本地",
        }

    try:
        response = requests.get(
            f"https://uapis.cn/api/v1/network/ipinfo?ip={ip}&source=commercial",
            timeout=timeout_seconds,
        )

        if not response.ok:
            raise Exception(f"HTTP error! status: {response.status_code}")

        data = response.json()

        if data.get("ip"):
            region_parts = [p.strip() for p in (data.get("region") or "").split(" ") if p.strip()]
            return {
                "country": region_parts[0] if len(region_parts) > 0 else "未知",
                "province": region_parts[1] if len(region_parts) > 1 else "未知",
                "city": region_parts[2] if len(region_parts) > 2 else "未知",
                "district": data.get("district") or (region_parts[3] if len(region_parts) > 3 else "未知"),
            }
        else:
            raise Exception(f"IP lookup failed: {data.get('msg', 'Unknown error')}")
    except Exception:
        return {
            "country": "未知",
            "province": "未知",
            "city": "未知",
            "district": "未知",
        }


def _load_or_create_device_uuid() -> str:
    uuid_file = get_data_path(_DEVICE_UUID_FILE)

    if uuid_file.exists():
        try:
            with open(uuid_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                device_uuid = data.get("device_uuid")
                if device_uuid:
                    try:
                        uuid.UUID(device_uuid)
                        return device_uuid
                    except ValueError:
                        pass
        except Exception:
            pass

    device_uuid = str(uuid.uuid4()).lower()
    try:
        uuid_file.parent.mkdir(parents=True, exist_ok=True)
        with open(uuid_file, "w", encoding="utf-8") as f:
            json.dump({"device_uuid": device_uuid}, f)
    except Exception:
        pass

    return device_uuid


def _do_report(
    platform_id: str,
    device_uuid: str,
    device_type: str,
    ip_address: Optional[str],
    country: Optional[str],
    province: Optional[str],
    city: Optional[str],
    district: Optional[str],
) -> Dict[str, Any]:
    if not ip_address:
        ip_address = _get_public_ip(SECTL_ONLINE_REPORT_TIMEOUT_SECONDS)
        if not ip_address:
            ip_address = _get_local_ip()

    if not all([country, province, city, district]):
        location = _get_ip_location(ip_address, SECTL_ONLINE_REPORT_TIMEOUT_SECONDS)
        country = country or location.get("country", "未知")
        province = province or location.get("province", "未知")
        city = city or location.get("city", "未知")
        district = district or location.get("district", "未知")

    payload = {
        "platform_id": platform_id,
        "device_uuid": device_uuid,
        "device_type": device_type,
        "ip_address": ip_address,
        "country": country,
        "province": province,
        "city": city,
        "district": district,
    }

    try:
        response = requests.post(
            f"{SECTL_API_BASE_URL}/api/stats/online",
            json=payload,
            timeout=SECTL_ONLINE_REPORT_TIMEOUT_SECONDS,
        )

        if response.status_code >= 400:
            try:
                error_data = response.json()
                logger.warning(f"上报在线状态失败: {error_data.get('error_description', error_data.get('error', 'Unknown error'))}")
            except Exception:
                logger.warning(f"上报在线状态失败: HTTP {response.status_code}")
            return {"success": False, "error": "request_failed"}

        result = response.json()
        online_count = result.get("online_count", 0)
        update_online_count_cache(online_count)
        logger.info(f"上报在线状态成功，当前在线人数: {online_count}")
        return result

    except requests.exceptions.Timeout:
        logger.warning("上报在线状态超时")
        return {"success": False, "error": "timeout"}
    except requests.exceptions.ConnectionError:
        logger.warning("上报在线状态连接失败")
        return {"success": False, "error": "connection_error"}
    except Exception as e:
        logger.warning(f"上报在线状态失败: {e}")
        return {"success": False, "error": str(e)}


def report_online_status_async(
    platform_id: Optional[str] = None,
    device_uuid: Optional[str] = None,
    device_type: Optional[str] = None,
    ip_address: Optional[str] = None,
    country: Optional[str] = None,
    province: Optional[str] = None,
    city: Optional[str] = None,
    district: Optional[str] = None,
):
    platform_id = platform_id or SECTL_PLATFORM_ID
    device_uuid = device_uuid or _load_or_create_device_uuid()
    device_type = device_type or _detect_device_type()

    _executor.submit(
        _do_report,
        platform_id,
        device_uuid,
        device_type,
        ip_address,
        country,
        province,
        city,
        district,
    )


class OnlineStatusReporter:
    """在线状态上报器，负责定期上报在线状态（后台线程执行）"""

    def __init__(
        self,
        platform_id: Optional[str] = None,
        report_interval_ms: Optional[int] = None,
    ):
        self.platform_id = platform_id or SECTL_PLATFORM_ID
        self.report_interval_ms = report_interval_ms or SECTL_ONLINE_REPORT_INTERVAL_MS
        self.device_uuid = _load_or_create_device_uuid()
        self.device_type = _detect_device_type()
        self._ip_address: Optional[str] = None
        self._country: Optional[str] = None
        self._province: Optional[str] = None
        self._city: Optional[str] = None
        self._district: Optional[str] = None
        self._timer: Optional[threading.Timer] = None
        self._is_running = False
        self._initialized = False
        self._lock = threading.Lock()

    def _init_ip_and_location_async(self):
        def _do_init():
            ip_address = _get_public_ip(SECTL_ONLINE_REPORT_TIMEOUT_SECONDS)
            if not ip_address:
                ip_address = _get_local_ip()
            location = _get_ip_location(ip_address, SECTL_ONLINE_REPORT_TIMEOUT_SECONDS)
            self._ip_address = ip_address
            self._country = location.get("country", "未知")
            self._province = location.get("province", "未知")
            self._city = location.get("city", "未知")
            self._district = location.get("district", "未知")
            self._initialized = True
            logger.debug(f"在线状态上报器初始化完成，IP: {ip_address}, 位置: {self._country} {self._province} {self._city}")
            self._report_async()

        _executor.submit(_do_init)

    def _schedule_next_report(self):
        """调度下一次上报"""
        with self._lock:
            if not self._is_running:
                return
            self._timer = threading.Timer(
                self.report_interval_ms / 1000.0,
                self._on_timer_tick
            )
            self._timer.daemon = True
            self._timer.start()

    def _on_timer_tick(self):
        """定时器触发时的回调"""
        self._report_async()
        self._schedule_next_report()

    def start(self):
        with self._lock:
            if self._is_running:
                return

            self._is_running = True
            logger.debug("在线状态上报器正在启动...")

        self._init_ip_and_location_async()
        self._schedule_next_report()
        logger.debug(f"在线状态上报器已启动，上报间隔: {self.report_interval_ms}ms")

    def stop(self):
        with self._lock:
            if not self._is_running:
                return

            self._is_running = False
            if self._timer:
                self._timer.cancel()
                self._timer = None
        logger.debug("在线状态上报器已停止")

    def _report_async(self):
        if not self._is_running:
            return

        logger.debug(f"触发在线状态上报，IP: {self._ip_address}, 已初始化: {self._initialized}")

        _executor.submit(
            _do_report,
            self.platform_id,
            self.device_uuid,
            self.device_type,
            self._ip_address,
            self._country,
            self._province,
            self._city,
            self._district,
        )

    def report_now(self):
        self._report_async()


def get_online_status_reporter() -> Optional[OnlineStatusReporter]:
    return _online_status_reporter


def initialize_online_status_reporter(
    platform_id: Optional[str] = None,
    report_interval_ms: Optional[int] = None,
) -> OnlineStatusReporter:
    global _online_status_reporter

    if _online_status_reporter is not None:
        return _online_status_reporter

    _online_status_reporter = OnlineStatusReporter(
        platform_id=platform_id,
        report_interval_ms=report_interval_ms,
    )
    return _online_status_reporter


def start_online_status_reporter():
    global _online_status_reporter

    if _online_status_reporter is None:
        _online_status_reporter = initialize_online_status_reporter()

    _online_status_reporter.start()


def stop_online_status_reporter():
    global _online_status_reporter

    if _online_status_reporter is not None:
        _online_status_reporter.stop()


def _do_get_online_stats(platform_id: str) -> Dict[str, Any]:
    try:
        response = requests.get(
            f"{SECTL_API_BASE_URL}/api/stats/platform/{platform_id}",
            timeout=SECTL_ONLINE_REPORT_TIMEOUT_SECONDS,
        )

        if response.status_code >= 400:
            return {"success": False, "error": "request_failed"}

        result = response.json()
        return result

    except Exception:
        return {"success": False, "error": "request_failed"}


def get_online_stats_async(callback, platform_id: Optional[str] = None):
    def _do():
        result = _do_get_online_stats(platform_id or SECTL_PLATFORM_ID)
        if callback:
            callback(result)

    _executor.submit(_do)


_online_count_cache = {"count": 0, "updated_at": 0}


def get_cached_online_count() -> int:
    return _online_count_cache.get("count", 0)


def update_online_count_cache(count: int):
    import time
    _online_count_cache["count"] = count
    _online_count_cache["updated_at"] = time.time()
