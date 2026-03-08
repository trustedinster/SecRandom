import time

from loguru import logger

from app.common.history.file_utils import get_all_history_names, load_history_data
from app.tools.settings_access import readme_settings_async, update_settings


def calculate_total_draw_counts():
    """计算总抽取次数。"""
    roll_call_total = 0
    for class_name in get_all_history_names("roll_call"):
        data = load_history_data("roll_call", class_name)
        roll_call_total += int(data.get("total_rounds", 0) or 0)

    lottery_total = 0
    for pool_name in get_all_history_names("lottery"):
        data = load_history_data("lottery", pool_name)
        lotterys = data.get("lotterys", {})
        if not isinstance(lotterys, dict):
            continue

        draw_times = set()
        for entry in lotterys.values():
            if not isinstance(entry, dict):
                continue
            hist = entry.get("history", [])
            if not isinstance(hist, list):
                continue
            for record in hist:
                if not isinstance(record, dict):
                    continue
                draw_time = record.get("draw_time")
                if draw_time:
                    draw_times.add(draw_time)
        lottery_total += len(draw_times)

    total_draw_count = roll_call_total + lottery_total
    return total_draw_count, roll_call_total, lottery_total


def _normalize_stored_counter(value):
    if value is None:
        return None
    try:
        normalized = int(value)
    except Exception:
        return None
    if normalized < 0:
        return None
    return normalized


def get_stored_draw_counts():
    """读取已缓存的抽取统计；若旧版本字段缺失或值不合法则返回 None。"""
    stored_total = _normalize_stored_counter(
        readme_settings_async("user_info", "total_draw_count", None)
    )
    stored_roll_call = _normalize_stored_counter(
        readme_settings_async("user_info", "roll_call_total_count", None)
    )
    stored_lottery = _normalize_stored_counter(
        readme_settings_async("user_info", "lottery_total_count", None)
    )

    if None in (stored_total, stored_roll_call, stored_lottery):
        return None
    if stored_total != stored_roll_call + stored_lottery:
        return None
    return stored_total, stored_roll_call, stored_lottery


def persist_draw_counts(
    total_draw_count: int, roll_call_total: int, lottery_total: int
) -> tuple[int, int, int]:
    """持久化抽取统计字段。"""
    update_settings("user_info", "total_draw_count", int(total_draw_count or 0))
    update_settings("user_info", "roll_call_total_count", int(roll_call_total or 0))
    update_settings("user_info", "lottery_total_count", int(lottery_total or 0))
    return (
        int(total_draw_count or 0),
        int(roll_call_total or 0),
        int(lottery_total or 0),
    )


def recompute_and_persist_draw_counts() -> tuple[int, int, int]:
    """全量重算并回写抽取统计，兼容旧数据格式。"""
    start = time.perf_counter()
    totals = persist_draw_counts(*calculate_total_draw_counts())
    elapsed = time.perf_counter() - start
    logger.debug(f"抽取统计补算完成，耗时: {elapsed:.3f}s")
    return totals


def increment_usage_counters(
    *, roll_call_increment: int = 0, lottery_increment: int = 0
) -> tuple[int, int, int]:
    """优先增量维护抽取统计；旧版本缺字段时自动回退到全量重算。"""
    stored_counts = get_stored_draw_counts()
    if stored_counts is None:
        return recompute_and_persist_draw_counts()

    total_draw_count, roll_call_total, lottery_total = stored_counts
    roll_call_total += max(0, int(roll_call_increment or 0))
    lottery_total += max(0, int(lottery_increment or 0))
    total_draw_count = roll_call_total + lottery_total
    return persist_draw_counts(total_draw_count, roll_call_total, lottery_total)
