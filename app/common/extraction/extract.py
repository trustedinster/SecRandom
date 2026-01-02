import json
import os
from pathlib import Path
from typing import Dict, Tuple

from PySide6.QtCore import QDateTime
from PySide6.QtGui import *
from PySide6.QtNetwork import *
from PySide6.QtWidgets import *
from loguru import logger
from qfluentwidgets import *

from app.Language.obtain_language import get_content_name_async
from app.common.IPC_URL.csharp_ipc_handler import CSharpIPCHandler
from app.common.extraction.cses_parser import CSESParser
from app.tools.path_utils import *
from app.tools.settings_access import readme_settings_async


def _is_non_class_time() -> bool:
    """检测当前时间是否在非上课时间段

    当'课间禁用'开关启用时，用于判断是否需要安全验证

    Returns:
        bool: 如果当前时间在非上课时间段内返回True，否则返回False
    """
    try:
        instant_draw_disable = readme_settings_async(
            "time_settings", "instant_draw_disable"
        )
        logger.debug(f"课间禁用开关是否启用: {instant_draw_disable}")
        if not instant_draw_disable:
            return False

        use_class_island_source = readme_settings_async(
            "time_settings", "class_island_source_enabled"
        )
        logger.debug(f"是否启用了ClassIsland数据源: {use_class_island_source}")
        if use_class_island_source:
            return CSharpIPCHandler.instance().is_breaking()
        else:
            current_day_of_week = _get_current_day_of_week()
            class_times = _get_class_times_by_day(current_day_of_week)
            if not class_times or not isinstance(class_times, dict):
                return False

            current_total_seconds = _get_current_time_in_seconds()
            logger.debug(f"当前时间总秒数: {current_total_seconds}")

            is_in_class_time = _is_time_in_ranges(current_total_seconds, class_times)
            logger.debug(f"当前时间是否在上课时间段内: {is_in_class_time}")

            return not is_in_class_time

    except Exception as e:
        logger.error(f"检测非上课时间失败: {e}")
        return False


def _get_current_time_in_seconds() -> int:
    """获取当前时间并转换为总秒数

    Returns:
        int: 当前时间的总秒数（从午夜开始计算）
    """
    current_time = QDateTime.currentDateTime()
    current_hour = current_time.time().hour()
    current_minute = current_time.time().minute()
    current_second = current_time.time().second()

    return current_hour * 3600 + current_minute * 60 + current_second


def _get_current_day_of_week() -> int:
    """获取当前是星期几

    Returns:
        int: 星期几（1=星期一，7=星期日）
    """
    current_time = QDateTime.currentDateTime()
    day_of_week = current_time.date().dayOfWeek()
    return day_of_week


def _parse_time_string_to_seconds(time_str: str) -> int:
    """将时间字符串转换为总秒数

    Args:
        time_str: 时间字符串，格式为 "HH:MM:SS" 或 "HH:MM"

    Returns:
        int: 时间的总秒数

    Raises:
        ValueError: 如果时间字符串格式不正确
    """
    time_parts = list(map(int, time_str.split(":")))

    if len(time_parts) < 2 or len(time_parts) > 3:
        raise ValueError(f"时间字符串格式不正确: {time_str}")

    hours = time_parts[0]
    minutes = time_parts[1]
    seconds = time_parts[2] if len(time_parts) > 2 else 0

    return hours * 3600 + minutes * 60 + seconds


def _is_time_in_ranges(current_seconds: int, time_ranges: Dict[str, str]) -> bool:
    """检查当前时间是否在任何一个时间范围内

    Args:
        current_seconds: 当前时间的总秒数
        time_ranges: 时间范围字典，格式为 {"name": "HH:MM:SS-HH:MM:SS"}

    Returns:
        bool: 如果当前时间在任何一个时间范围内返回True，否则返回False
    """
    for range_name, time_range in time_ranges.items():
        try:
            start_end = time_range.split("-")
            if len(start_end) != 2:
                logger.warning(f"时间范围格式错误: {range_name} = {time_range}")
                continue

            start_time_str, end_time_str = start_end

            start_total_seconds = _parse_time_string_to_seconds(start_time_str)
            end_total_seconds = _parse_time_string_to_seconds(end_time_str)

            if start_total_seconds <= current_seconds < end_total_seconds:
                return True

        except Exception as e:
            logger.error(f"解析时间段失败: {range_name} = {time_range}, 错误: {e}")
            continue

    return False


def _get_cses_parser() -> CSESParser | None:
    """获取CSES解析器实例

    Returns:
        CSESParser | None: 成功返回解析器实例，失败返回None
    """
    try:
        cses_dir = get_data_path("CSES")
        if not os.path.exists(cses_dir):
            logger.info("CSES目录不存在")
            return None

        cses_file_path = os.path.join(cses_dir, "cses_schedule.yml")

        if not os.path.exists(cses_file_path):
            logger.info("CSES文件不存在")
            return None

        parser = CSESParser()
        if not parser.load_from_file(cses_file_path):
            logger.error(f"加载CSES文件失败: {cses_file_path}")
            return None

        return parser

    except Exception as e:
        logger.error(f"获取CSES解析器失败: {e}")
        return None


def _get_class_times_by_day(day_of_week: int) -> Dict[str, str]:
    """获取指定星期几的上课时间段

    Args:
        day_of_week: 星期几（1=星期一，7=星期日）

    Returns:
        Dict[str, str]: 上课时间段字典，格式为 {"name": "HH:MM:SS-HH:MM:SS"}
    """
    parser = _get_cses_parser()
    if not parser:
        return {}

    try:
        class_times = parser.get_class_times_by_day_with_week(day_of_week, "all")
        if class_times:
            return class_times
    except Exception:
        pass

    return parser.get_class_times_by_day(day_of_week)


def _get_non_class_times_config() -> Dict[str, str]:
    """获取非上课时间段配置

    Returns:
        Dict[str, str]: 非上课时间段配置字典，如果获取失败返回空字典
    """
    parser = _get_cses_parser()
    if not parser:
        return {}

    non_class_times = parser.get_non_class_times()
    logger.info(f"成功从CSES文件生成{len(non_class_times)}个非上课时间段")
    return non_class_times


def _save_non_class_times_to_settings(non_class_times: Dict[str, str]) -> bool:
    """保存非上课时间段到设置文件

    Args:
        non_class_times: 非上课时间段字典

    Returns:
        bool: 保存成功返回True，否则返回False
    """
    try:
        settings_path = get_settings_path()

        if file_exists(settings_path):
            with open_file(settings_path, "r", encoding="utf-8") as f:
                settings = json.load(f)
        else:
            settings = {}

        settings["non_class_times"] = non_class_times

        with open_file(settings_path, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)

        logger.info(f"成功保存{len(non_class_times)}个非上课时间段到设置文件")
        return True

    except Exception as e:
        logger.error(f"保存非上课时间段失败: {e}")
        return False


def import_cses_schedule(file_path: str) -> Tuple[bool, str]:
    """从CSES文件导入课程表

    Args:
        file_path: CSES文件路径

    Returns:
        Tuple[bool, str]: (是否成功, 结果消息)
    """
    try:
        parser = CSESParser()

        if not parser.load_from_file(file_path):
            return False, get_content_name_async(
                "time_settings", "cses_file_format_error"
            )

        non_class_times = parser.get_non_class_times()
        if not non_class_times:
            return False, get_content_name_async(
                "time_settings", "no_valid_time_periods"
            )

        original_file_name = Path(file_path).name
        cses_data_path = get_data_path("CSES", "cses_schedule.yml")
        ensure_dir(get_data_path("CSES"))
        import shutil

        shutil.copy2(file_path, cses_data_path)
        logger.info(f"已将CSES文件保存到: {cses_data_path}")

        summary = parser.get_summary()
        import_success_msg = get_content_name_async("time_settings", "import_success")
        if "{}" in import_success_msg:
            return True, import_success_msg.format(summary)
        else:
            return True, import_success_msg

    except Exception as e:
        logger.error(f"导入CSES文件失败: {e}")
        return False, get_content_name_async("time_settings", "import_failed").format(
            str(e)
        )


def import_cses_schedule_from_content(content: str) -> Tuple[bool, str]:
    """从CSES内容字符串导入课程表

    Args:
        content: CSES格式的YAML内容

    Returns:
        Tuple[bool, str]: (是否成功, 结果消息)
    """
    try:
        parser = CSESParser()

        if not parser.load_from_content(content):
            return False, get_content_name_async(
                "time_settings", "cses_content_format_error"
            )

        non_class_times = parser.get_non_class_times()
        if not non_class_times:
            return False, get_content_name_async(
                "time_settings", "no_valid_time_periods"
            )

        summary = parser.get_summary()
        return True, get_content_name_async("time_settings", "import_success").format(
            summary
        )

    except Exception as e:
        logger.error(f"导入CSES内容失败: {e}")
        return False, get_content_name_async("time_settings", "import_failed").format(
            str(e)
        )


__all__ = ["import_cses_schedule", "import_cses_schedule_from_content"]
