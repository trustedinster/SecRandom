# ==================================================
# 导入库
# ==================================================
from datetime import datetime
from typing import Dict, List, Any, Optional

from loguru import logger

from app.tools.settings_access import readme_settings_async
from app.common.data.list import get_student_list
from app.Language.obtain_language import get_content_combo_name_async
from app.common.extraction.extract import _get_current_class_info
from app.common.history.file_utils import load_history_data, save_history_data
from app.common.history.weight_utils import calculate_weight


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
        students_dict_list: 完整的学生列表，用于计算权重
        group_filter: 小组过滤器，指定本次抽取的小组范围，None表示不限制
        gender_filter: 性别过滤器，指定本次抽取的性别范围，None表示不限制

    Returns:
        bool: 保存是否成功
    """
    try:
        # 获取当前时间
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 加载现有历史记录
        history_data = load_history_data("roll_call", class_name)

        # 初始化数据结构
        if "students" not in history_data:
            history_data["students"] = {}
        if "group_stats" not in history_data:
            history_data["group_stats"] = {}
        if "gender_stats" not in history_data:
            history_data["gender_stats"] = {}
        if "total_rounds" not in history_data:
            history_data["total_rounds"] = 0
        if "total_stats" not in history_data:
            history_data["total_stats"] = 0
        if "subject_stats" not in history_data:
            history_data["subject_stats"] = {}

        # 获取被选中的学生名称列表
        selected_names = [s.get("name", "") for s in selected_students]

        # 获取当前课程信息（用于科目过滤）
        current_class_info = None
        subject_history_filter_enabled = (
            readme_settings_async("course_settings", "subject_history_filter_enabled")
            or False
        )

        if subject_history_filter_enabled:
            data_source = readme_settings_async("course_settings", "data_source")
            if data_source == 2:
                from app.common.IPC_URL.csharp_ipc_handler import CSharpIPCHandler

                current_class_info = (
                    CSharpIPCHandler.instance().get_current_class_info()
                )
            elif data_source == 1:
                current_class_info = _get_current_class_info()
            else:
                current_class_info = None

            # 如果当前没有课程信息（课间时段），则使用课间归属的课程信息
            if not current_class_info:
                from app.common.extraction.extract import (
                    _is_non_class_time,
                    _get_break_assignment_class_info,
                )

                if _is_non_class_time():
                    current_class_info = _get_break_assignment_class_info()

        # 提取科目名称
        subject_filter = ""
        if current_class_info:
            subject_filter = current_class_info.get("name", "")

        # 计算权重
        students_dict_list = get_student_list(class_name)
        students_with_weight = calculate_weight(
            students_dict_list, class_name, subject_filter
        )

        # 更新每个被选中学生的历史记录
        for student in selected_students:
            student_name = student.get("name", "")
            if not student_name:
                continue

            # 如果学生不存在于历史记录中，创建新记录
            if student_name not in history_data["students"]:
                history_data["students"][student_name] = {
                    "total_count": 0,
                    "group_gender_count": 0,
                    "last_drawn_time": "",
                    "rounds_missed": 0,
                    "history": [],
                    "subject_stats": {},
                }

            # 更新学生的基本信息
            student_data = history_data["students"][student_name]
            student_data["total_count"] += 1
            student_data["last_drawn_time"] = current_time
            student_data["rounds_missed"] = 0  # 重置未选中次数

            draw_method = 1

            # 获取当前被选中学生的权重信息
            current_student_weight = None
            for student_with_weight in students_with_weight:
                if student_with_weight.get("name") == student_name:
                    current_student_weight = student_with_weight.get("next_weight", 0)
                    break

            history_entry = {
                "draw_method": draw_method,
                "draw_time": current_time,
                "draw_people_numbers": len(selected_students),
                "draw_group": group_filter,
                "draw_gender": gender_filter,
                "weight": current_student_weight,
            }

            # 如果能获取到课程信息，则添加到历史记录中并更新学科统计
            if current_class_info:
                subject_name = current_class_info.get("name", "")
                history_entry["class_name"] = subject_name

                # 更新学生级别的学科统计
                if "subject_stats" not in student_data:
                    student_data["subject_stats"] = {}

                if subject_name not in student_data["subject_stats"]:
                    student_data["subject_stats"][subject_name] = {
                        "total_count": 0,
                        "group_gender_count": 0,
                    }

                subject_stat = student_data["subject_stats"][subject_name]
                subject_stat["total_count"] += 1

                # 统计 group_gender_count（小组和性别都有限制）
                all_group = get_content_combo_name_async("roll_call", "range_combobox")[
                    0
                ]
                all_gender = get_content_combo_name_async(
                    "roll_call", "gender_combobox"
                )[0]

                if group_filter and group_filter != all_group:
                    if gender_filter and gender_filter != all_gender:
                        subject_stat["group_gender_count"] += 1

            student_data["history"].append(history_entry)

        # 更新未被选中的学生的未选中次数
        for student_name, student_data in history_data["students"].items():
            if student_name not in selected_names:
                student_data["rounds_missed"] += 1

        # 更新小组和性别统计
        for student in selected_students:
            group = student.get("group", "")
            gender = student.get("gender", "")

            # 更新小组统计
            if group not in history_data["group_stats"]:
                history_data["group_stats"][group] = 0
            history_data["group_stats"][group] += 1

            # 更新性别统计
            if gender not in history_data["gender_stats"]:
                history_data["gender_stats"][gender] = 0
            history_data["gender_stats"][gender] += 1

        # 更新学科统计（顶层）
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

                    # 更新学科小组统计
                    if group:
                        if group not in subject_stat["group_stats"]:
                            subject_stat["group_stats"][group] = 0
                        subject_stat["group_stats"][group] += 1

                    # 更新学科性别统计
                    if gender:
                        if gender not in subject_stat["gender_stats"]:
                            subject_stat["gender_stats"][gender] = 0
                        subject_stat["gender_stats"][gender] += 1

        # 更新总轮数和总统计数
        history_data["total_rounds"] += 1
        history_data["total_stats"] += len(selected_students)

        # 保存历史记录
        return save_history_data("roll_call", class_name, history_data)

    except Exception as e:
        logger.error(f"保存点名历史记录失败: {e}")
        return False
