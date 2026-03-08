# ==================================================
# 导入模块
# ==================================================
from qfluentwidgets import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtNetwork import *

import asyncio
import copy
import json
import threading
import time
import uuid
from typing import Any

from loguru import logger

from app.tools.variable import *
from app.tools.path_utils import *
from app.tools.settings_default import *


# ==================================================
# 设置缓存
# ==================================================
_settings_cache_lock = threading.RLock()
_settings_cache_signature = None
_settings_cache_data = {}


def _get_settings_file_signature(settings_path):
    try:
        stat_result = settings_path.stat()
        return stat_result.st_mtime_ns, stat_result.st_size
    except OSError:
        return None


def _read_settings_file(settings_path) -> dict[str, Any]:
    if not file_exists(settings_path):
        return {}

    try:
        with open_file(settings_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        logger.exception(f"读取设置文件失败: {e}")
        return {}

    if not content or not content.strip():
        logger.warning(f"设置文件为空: {settings_path}")
        return {}

    try:
        settings_data = json.loads(content)
    except Exception as e:
        logger.exception(f"解析设置文件失败: {e}")
        return {}

    if isinstance(settings_data, dict):
        return settings_data

    logger.warning(f"设置文件根节点类型无效: {type(settings_data)}")
    return {}


def _load_settings_data_cached(force_refresh: bool = False) -> dict[str, Any]:
    global _settings_cache_signature
    global _settings_cache_data

    settings_path = get_settings_path()
    current_signature = _get_settings_file_signature(settings_path)

    with _settings_cache_lock:
        if (
            not force_refresh
            and _settings_cache_signature == current_signature
            and isinstance(_settings_cache_data, dict)
        ):
            return _settings_cache_data

        start = time.perf_counter()
        settings_data = _read_settings_file(settings_path)
        _settings_cache_signature = current_signature
        _settings_cache_data = settings_data if isinstance(settings_data, dict) else {}
        elapsed = time.perf_counter() - start
        logger.debug(
            f"设置文件已从磁盘加载: {settings_path} (耗时: {elapsed:.3f}s, force_refresh={force_refresh})"
        )
        return _settings_cache_data


def _refresh_settings_cache(settings_data: dict[str, Any]) -> None:
    global _settings_cache_signature
    global _settings_cache_data

    settings_path = get_settings_path()
    _settings_cache_signature = _get_settings_file_signature(settings_path)
    _settings_cache_data = settings_data if isinstance(settings_data, dict) else {}


def _get_default_value(first_level_key: str, second_level_key: str, default: Any = None):
    default_setting = _get_default_setting(first_level_key, second_level_key)
    if isinstance(default_setting, dict) and "default_value" in default_setting:
        return default_setting["default_value"]
    if default_setting is not None:
        return default_setting
    return default


# ==================================================
# 设置访问函数
# ==================================================
class SettingsReaderWorker(QObject):
    """设置读取工作线程"""

    finished = Signal(object)  # 信号，传递读取结果

    def __init__(self, first_level_key: str, second_level_key: str, default: Any = None):
        super().__init__()
        self.first_level_key = first_level_key
        self.second_level_key = second_level_key
        self.default = default

    def run(self):
        """执行设置读取操作"""
        try:
            value = self._read_setting_value()
            # logger.debug(f"读取设置: {self.first_level_key}.{self.second_level_key} = {value}")
            self.finished.emit(value)
        except Exception as e:
            logger.exception(f"读取设置失败: {e}")
            default_value = self._get_default_value()
            self.finished.emit(default_value)

    def _read_setting_value(self):
        """从设置文件或默认设置中读取值"""
        return readme_settings(
            self.first_level_key,
            self.second_level_key,
            default=self.default,
        )

    def _get_default_value(self):
        """获取默认设置值"""
        default_setting = _get_default_setting(
            self.first_level_key, self.second_level_key
        )
        return (
            default_setting["default_value"]
            if isinstance(default_setting, dict) and "default_value" in default_setting
            else default_setting if default_setting is not None else self.default
        )


class AsyncSettingsReader(QObject):
    """异步设置读取器，提供简洁的异步读取方式"""

    finished = Signal(object)  # 读取完成信号，携带结果
    error = Signal(str)  # 错误信号

    def __init__(
        self, first_level_key: str, second_level_key: str, default: Any = None
    ):
        super().__init__()
        self.first_level_key = first_level_key
        self.second_level_key = second_level_key
        self.default = default
        self.thread = None
        self.worker = None
        self._result = None
        self._completed = False
        self._future = None

    def read_async(self):
        """异步读取设置，返回Future对象"""
        self.thread = QThread()
        self.worker = SettingsReaderWorker(
            self.first_level_key,
            self.second_level_key,
            self.default,
        )
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self._handle_result)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self._future = asyncio.Future()
        self.thread.start()
        return self._future

    def result(self, timeout=None):
        """等待并返回结果，类似Future的result()方法"""
        if self._completed:
            return self._result
        if self.thread and self.thread.isRunning():
            if timeout is not None:
                self.thread.wait(timeout)
            else:
                self.thread.wait()
        return self._result

    def is_done(self):
        """检查是否已完成"""
        return self._completed

    def _handle_result(self, value):
        """处理设置读取结果"""
        self._result = value
        self._completed = True
        if self._future and not self._future.done():
            self._future.set_result(value)
        self.finished.emit(value)
        self._cleanup_thread()

    def _cleanup_thread(self):
        """安全地清理线程资源"""
        if self.thread and self.thread.isRunning():
            self.thread.quit()
            self.thread.wait(1000)


def readme_settings(first_level_key: str, second_level_key: str, default: Any = None):
    """读取设置

    Args:
        first_level_key: 第一层的键
        second_level_key: 第二层的键

    Returns:
        返回设置值
    """
    try:
        settings_data = _load_settings_data_cached()
        section = settings_data.get(first_level_key)
        if isinstance(section, dict) and second_level_key in section:
            value = section[second_level_key]
            return value

        return _get_default_value(first_level_key, second_level_key, default)
    except Exception as e:
        logger.exception(f"读取设置失败: {e}")
        return _get_default_value(first_level_key, second_level_key, default)


def readme_settings_async(
    first_level_key: str,
    second_level_key: str,
    default: Any = None,
    timeout=1000,
):
    """异步读取设置（简化版：直接调用同步方法）

    为保持 API 兼容性而保留，但在 Nuitka 环境下 QTimer 有兼容性问题，
    因此直接使用同步方法。实际测试表明同步方法性能已足够好。

    Args:
        first_level_key (str): 第一层的键
        second_level_key (str): 第二层的键
        default (Any, optional): 设置不存在时使用的回退值
        timeout (int, optional): 保留参数，用于兼容性

    Returns:
        Any: 设置值
    """
    _ = timeout
    return readme_settings(first_level_key, second_level_key, default=default)


def get_settings_snapshot(force_refresh: bool = False) -> dict[str, Any]:
    """获取设置快照副本，适合在热点路径一次性读取多个键。"""
    settings_data = _load_settings_data_cached(force_refresh=force_refresh)
    with _settings_cache_lock:
        return copy.deepcopy(settings_data)


class SettingsSignals(QObject):
    """设置变化信号类"""

    settingChanged = Signal(
        str, str, object
    )  # (first_level_key, second_level_key, value)


# 创建全局信号实例
_settings_signals = SettingsSignals()


def get_settings_signals():
    """获取设置信号实例"""
    global _settings_signals
    return _settings_signals


def update_settings(first_level_key: str, second_level_key: str, value: Any):
    """更新设置

    Args:
        first_level_key: 第一层的键
        second_level_key: 第二层的键
        value: 要写入的值（可以是任何类型）

    Returns:
        bool: 更新是否成功
    """
    try:
        # 获取设置文件路径
        settings_path = get_settings_path()

        # 确保设置目录存在
        ensure_dir(settings_path.parent)

        with _settings_cache_lock:
            settings_data = copy.deepcopy(_load_settings_data_cached())
            if not isinstance(settings_data, dict):
                settings_data = {}

            # 更新设置
            section = settings_data.get(first_level_key)
            if not isinstance(section, dict):
                section = {}
                settings_data[first_level_key] = section

            # 直接保存值，不保存嵌套结构
            section[second_level_key] = value

            # 写入设置文件
            with open_file(settings_path, "w", encoding="utf-8") as f:
                json.dump(settings_data, f, ensure_ascii=False, indent=4)

            _refresh_settings_cache(settings_data)

        if not (
            first_level_key == "user_info"
            and second_level_key == "total_runtime_seconds"
        ):
            logger.debug(
                f"设置更新成功: {first_level_key}.{second_level_key} = {value}"
            )

        # 发送设置变化信号
        get_settings_signals().settingChanged.emit(
            first_level_key, second_level_key, value
        )
    except Exception as e:
        logger.exception(f"设置更新失败: {e}")


def get_or_create_user_id():
    try:
        user_id = readme_settings("basic_settings", "offline_user_id")
        if isinstance(user_id, str) and user_id.strip():
            return user_id
        user_id = uuid.uuid4().hex
        update_settings("basic_settings", "offline_user_id", user_id)
        return user_id
    except Exception as e:
        logger.exception(f"获取用户ID失败: {e}")
        return uuid.uuid4().hex


def _get_default_setting(first_level_key: str, second_level_key: str):
    """获取默认设置值

    Args:
        first_level_key: 第一层的键
        second_level_key: 第二层的键

    Returns:
        默认设置值
    """
    # 从settings_default模块获取默认值
    default_settings = get_default_settings()

    # 检查设置是否存在
    if first_level_key in default_settings:
        if second_level_key in default_settings[first_level_key]:
            setting_info = default_settings[first_level_key][second_level_key]
            # 如果是嵌套结构，提取 default_value
            if isinstance(setting_info, dict) and "default_value" in setting_info:
                return setting_info["default_value"]
            # 否则直接返回值
            return setting_info

    return None


def get_safe_font_size(
    first_level_key: str, second_level_key: str, default_size: int = 12
) -> int:
    """安全地获取字体大小设置值

    Args:
        first_level_key: 第一层的键
        second_level_key: 第二层的键
        default_size: 默认字体大小

    Returns:
        int: 有效的字体大小值（1-200）
    """
    try:
        # 获取设置值
        font_size = readme_settings(first_level_key, second_level_key)

        # 验证设置值的有效性
        if font_size is None:
            return default_size

        # 尝试转换为整数
        if isinstance(font_size, str):
            if font_size.isdigit():
                font_size = int(font_size)
            else:
                logger.warning(
                    f"字体大小设置值无效（非数字字符串）: {first_level_key}.{second_level_key} = {font_size}"
                )
                return default_size
        elif isinstance(font_size, (int, float)):
            font_size = int(font_size)
        else:
            logger.warning(
                f"字体大小设置值类型无效: {first_level_key}.{second_level_key} = {font_size} (类型: {type(font_size)})"
            )
            return default_size

        # 验证范围
        if font_size <= 0 or font_size > 200:
            logger.warning(
                f"字体大小设置值超出有效范围: {first_level_key}.{second_level_key} = {font_size}"
            )
            return default_size

        return font_size

    except (ValueError, TypeError) as e:
        logger.exception(f"获取字体大小设置失败: {e}")
        return default_size
    except Exception as e:
        logger.exception(f"获取字体大小设置时发生未知错误: {e}")
        return default_size
