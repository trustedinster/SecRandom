# ==================================================
# 导入库
# ==================================================
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

from loguru import logger

from app.tools.settings_access import readme_settings_async
from app.common.data.list import get_student_list
from app.Language.obtain_language import get_content_combo_name_async
from app.common.extraction.extract import _get_current_class_info
from app.common.history.file_utils import load_history_data, save_history_data
from app.common.history.weight_utils import calculate_weight
from app.core.usage_counters import increment_usage_counters


def _initialize_history_data(history_data: Dict[str, Any]):
    """初始化历史记录数据结构"""
    keys = ["students", "group_stats", "gender_stats", "subject_stats"]
    for key in keys:
        if key not in history_data:
            history_data[key] = {}

    if "total_rounds" not in history_data:
        history_data["total_rounds"] = 0
    if "total_stats" not in history_data:
        history_data["total_stats"] = 0


def _get_subject_filter() -> Tuple[Optional[Dict], str]:
    """获取当前课程信息和科目过滤器"""
    subject_history_filter_enabled = (
        readme_settings_async("linkage_settings", "subject_history_filter_enabled")
        or False
    )

    if not subject_history_filter_enabled:
        return None, ""

    data_source = readme_settings_async("linkage_settings", "data_source")
    current_class_info = None

    if data_source == 2:
        from app.common.IPC_URL.csharp_ipc_handler import CSharpIPCHandler

        current_class_info = CSharpIPCHandler.instance().get_current_class_info()
    elif data_source == 1:
        current_class_info = _get_current_class_info()

    # 如果当前没有课程信息（课间时段），则使用课间归属的课程信息
    if not current_class_info:
        from app.common.extraction.extract import (
            _is_non_class_time,
            _get_break_assignment_class_info,
        )

        if _is_non_class_time():
            current_class_info = _get_break_assignment_class_info()

    subject_filter = current_class_info.get("name", "") if current_class_info else ""
    return current_class_info, subject_filter


def _extract_student_weight(student: Dict[str, Any]) -> Any:
    """从已选学生载荷中提取可直接复用的权重值"""
    for key in ("next_weight", "weight"):
        value = student.get(key)
        if value is not None:
            return value
    return None


def _build_student_weight_map(
    class_name: str, selected_students: List[Dict[str, Any]], subject_filter: str
) -> Dict[str, Any]:
    """构建选中学生的权重映射，缺失时才回退到全量计算"""
    weight_map: Dict[str, Any] = {}
    missing_names: set[str] = set()

    for student in selected_students:
        student_name = str(student.get("name", "") or "")
        if not student_name:
            continue

        current_weight = _extract_student_weight(student)
        if current_weight is None:
            missing_names.add(student_name)
            continue
        weight_map[student_name] = current_weight

    if not missing_names:
        return weight_map

    students_dict_list = get_student_list(class_name)
    students_with_weight = calculate_weight(
        students_dict_list, class_name, subject_filter
    )
    for student in students_with_weight:
        student_name = str(student.get("name", "") or "")
        if student_name in missing_names and student_name not in weight_map:
            weight_map[student_name] = student.get("next_weight", 0)

    return weight_map


def _update_student_history(
    history_data: Dict[str, Any],
    selected_students: List[Dict[str, Any]],
    student_weight_map: Dict[str, Any],
    current_time: str,
    current_class_info: Optional[Dict],
    group_filter: Optional[str],
    gender_filter: Optional[str],
):
    """更新学生维度的历史记录"""
    selected_names = {
        str(student.get("name", "") or "")
        for student in selected_students
        if student.get("name")
    }
    selected_count = len(selected_students)

    # 更新被选中学生的历史记录
    for student in selected_students:
        student_name = student.get("name", "")
        if not student_name:
            continue

        if student_name not in history_data["students"]:
            history_data["students"][student_name] = {
                "total_count": 0,
                "group_gender_count": 0,
                "last_drawn_time": "",
                "rounds_missed": 0,
                "history": [],
                "subject_stats": {},
            }

        student_data = history_data["students"][student_name]
        student_data["total_count"] += 1
        student_data["last_drawn_time"] = current_time
        student_data["rounds_missed"] = 0

        current_student_weight = student_weight_map.get(student_name)

        history_entry = {
            "draw_method": 1,
            "draw_time": current_time,
            "draw_people_numbers": selected_count,
            "draw_group": group_filter,
            "draw_gender": gender_filter,
            "weight": current_student_weight,
        }

        if current_class_info:
            subject_name = current_class_info.get("name", "")
            history_entry["class_name"] = subject_name

            if "subject_stats" not in student_data:
                student_data["subject_stats"] = {}

            if subject_name not in student_data["subject_stats"]:
                student_data["subject_stats"][subject_name] = {
                    "total_count": 0,
                    "group_gender_count": 0,
                }

            student_data["subject_stats"][subject_name]["total_count"] += 1

            # 更新 group_gender_count
            all_group = get_content_combo_name_async("roll_call", "range_combobox")[0]
            all_gender = get_content_combo_name_async("roll_call", "gender_combobox")[0]

            if group_filter and group_filter != all_group:
                if gender_filter and gender_filter != all_gender:
                    student_data["subject_stats"][subject_name][
                        "group_gender_count"
                    ] += 1

        student_data["history"].append(history_entry)

    # 更新未被选中学生的未选中次数
    for student_name, student_data in history_data["students"].items():
        if student_name not in selected_names:
            student_data["rounds_missed"] += 1


def _update_global_stats(
    history_data: Dict[str, Any],
    selected_students: List[Dict[str, Any]],
    current_class_info: Optional[Dict],
):
    """更新全局统计信息（小组、性别、学科）"""
    # 更新小组和性别统计
    for student in selected_students:
        group = student.get("group", "")
        gender = student.get("gender", "")

        if group:
            history_data["group_stats"][group] = (
                history_data["group_stats"].get(group, 0) + 1
            )
        if gender:
            history_data["gender_stats"][gender] = (
                history_data["gender_stats"].get(gender, 0) + 1
            )

    # 更新学科统计
    if current_class_info:
        subject_name = current_class_info.get("name", "")
        if subject_name:
            if subject_name not in history_data["subject_stats"]:
                history_data["subject_stats"][subject_name] = {
                    "group_stats": {},
                    "gender_stats": {},
                    "total_rounds": 0,
                    "total_stats": 0,
                }

            subject_stat = history_data["subject_stats"][subject_name]
            subject_stat["total_rounds"] += 1
            subject_stat["total_stats"] += len(selected_students)

            for student in selected_students:
                group = student.get("group", "")
                gender = student.get("gender", "")

                if group:
                    subject_stat["group_stats"][group] = (
                        subject_stat["group_stats"].get(group, 0) + 1
                    )
                if gender:
                    subject_stat["gender_stats"][gender] = (
                        subject_stat["gender_stats"].get(gender, 0) + 1
                    )

    # 更新总轮数和总统计数
    history_data["total_rounds"] += 1
    history_data["total_stats"] += len(selected_students)


# ==================================================
# 保存点名历史函数
# ==================================================
def save_roll_call_history(
    class_name: str,
    selected_students: List[Dict[str, Any]],
    group_filter: Optional[str] = None,
    gender_filter: Optional[str] = None,
) -> bool:
    """保存点名历史记录

    Args:
        class_name: 班级名称
        selected_students: 被选中的学生列表
        group_filter: 小组过滤器，指定本次抽取的小组范围，None表示不限制
        gender_filter: 性别过滤器，指定本次抽取的性别范围，None表示不限制

    Returns:
        bool: 保存是否成功
    """
    try:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        history_data = load_history_data("roll_call", class_name)

        _initialize_history_data(history_data)

        # 获取课程信息
        current_class_info, subject_filter = _get_subject_filter()

        student_weight_map = _build_student_weight_map(
            class_name, selected_students, subject_filter
        )

        # 更新学生历史
        _update_student_history(
            history_data,
            selected_students,
            student_weight_map,
            current_time,
            current_class_info,
            group_filter,
            gender_filter,
        )

        # 更新全局统计
        _update_global_stats(history_data, selected_students, current_class_info)

        saved = save_history_data("roll_call", class_name, history_data)
        if saved:
            increment_usage_counters(roll_call_increment=1)
        return saved

    except Exception as e:
        logger.exception(f"保存点名历史记录失败: {e}")
        return False
