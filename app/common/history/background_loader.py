from dataclasses import dataclass
from typing import Any

from app.Language.obtain_language import get_content_name_async
from app.common.history.history_reader import (
    check_roll_call_students_have_gender_or_group,
    filter_roll_call_history_by_subject,
    get_lottery_history_data,
    get_lottery_pool_list,
    get_lottery_prize_stats_data,
    get_lottery_prizes_data,
    get_lottery_session_data,
    get_roll_call_history_data,
    get_roll_call_session_data,
    get_roll_call_student_list,
    get_roll_call_student_stats_data,
    get_roll_call_students_data,
)
from app.common.history.weight_utils import calculate_weight, format_weight_for_display


@dataclass(slots=True)
class HistoryTablePayload:
    rows: list[list[str]]
    available_subjects: list[str]
    all_names: list[str]
    has_gender: bool = False
    has_group: bool = False
    has_class_record: bool = False


def _safe_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _collect_roll_call_subjects(history_data: dict[str, Any]) -> list[str]:
    subjects = set()
    students = history_data.get("students", {})
    for student_info in students.values():
        history = student_info.get("history", [])
        for record in history:
            class_name = record.get("class_name", "")
            if class_name:
                subjects.add(class_name)
    return sorted(subjects)


def _collect_lottery_subjects(history_data: dict[str, Any]) -> list[str]:
    subjects = set()
    lotterys = history_data.get("lotterys", {})
    for lottery_info in lotterys.values():
        history = lottery_info.get("history", [])
        for record in history:
            class_name = record.get("class_name", "")
            if class_name:
                subjects.add(class_name)
    return sorted(subjects)


def build_roll_call_history_payload(
    class_name: str,
    mode_index: int,
    subject_name: str,
    selected_name: str,
    sort_column: int,
    sort_order_desc: bool,
) -> HistoryTablePayload:
    cleaned_students = get_roll_call_student_list(class_name)
    all_names = [name for _, name, _, _ in cleaned_students if name]
    base_history_data = get_roll_call_history_data(class_name)
    available_subjects = _collect_roll_call_subjects(base_history_data)
    has_gender, has_group = check_roll_call_students_have_gender_or_group(
        cleaned_students
    )
    reverse_order = bool(sort_order_desc)

    if mode_index == 0:
        history_data = (
            filter_roll_call_history_by_subject(base_history_data, subject_name)
            if subject_name
            else base_history_data
        )
        students_data = get_roll_call_students_data(
            cleaned_students, history_data, subject_name
        )
        students_weight_data = calculate_weight(
            students_data,
            class_name,
            subject_name,
            history_data=history_data,
        )
        format_weight, _, _ = format_weight_for_display(
            students_weight_data, "next_weight"
        )
        weight_by_identity = {
            (str(item.get("id", "")), str(item.get("name", ""))): item
            for item in students_weight_data
        }

        if sort_column >= 0:

            def sort_key(student: dict[str, Any]):
                if sort_column == 0:
                    return student.get("id", "")
                if sort_column == 1:
                    return student.get("name", "")
                if sort_column == 2:
                    return student.get("gender", "")
                if sort_column == 3:
                    return student.get("group", "")
                if sort_column == 4:
                    return _safe_int(student.get("total_count", 0))
                if sort_column == 5:
                    key = (str(student.get("id", "")), str(student.get("name", "")))
                    return _safe_float(
                        weight_by_identity.get(key, {}).get("next_weight", 1.0)
                    )
                return ""

            students_data.sort(key=sort_key, reverse=reverse_order)

        rows = []
        for student in students_data:
            key = (str(student.get("id", "")), str(student.get("name", "")))
            weight_value = weight_by_identity.get(key, {}).get("next_weight", "")
            row = [
                str(student.get("id", "")),
                str(student.get("name", "")),
            ]
            if has_gender:
                row.append(str(student.get("gender", "")))
            if has_group:
                row.append(str(student.get("group", "")))
            row.append(
                str(student.get("total_count_str", student.get("total_count", 0)))
            )
            row.append(str(format_weight(weight_value)))
            rows.append(row)
        return HistoryTablePayload(
            rows=rows,
            available_subjects=available_subjects,
            all_names=all_names,
            has_gender=has_gender,
            has_group=has_group,
            has_class_record=False,
        )

    if mode_index == 1:
        sessions_data = get_roll_call_session_data(
            cleaned_students, base_history_data, subject_name
        )
        has_class_record = any(item.get("class_name", "") for item in sessions_data)
        format_weight, _, _ = format_weight_for_display(sessions_data, "weight")

        if sort_column >= 0:

            def sort_key(student: dict[str, Any]):
                if sort_column == 0:
                    return student.get("draw_time", "")
                if sort_column == 1:
                    return student.get("id", "")
                if sort_column == 2:
                    return student.get("name", "")
                if sort_column == 3:
                    return student.get("gender", "")
                if sort_column == 4:
                    return student.get("group", "")
                if sort_column == 5:
                    return student.get("class_name", "")
                if sort_column == 6:
                    return _safe_float(student.get("weight", ""))
                return ""

            sessions_data.sort(key=sort_key, reverse=reverse_order)
        else:
            sessions_data.sort(key=lambda item: item.get("draw_time", ""), reverse=True)

        rows = []
        for student in sessions_data:
            row = [
                str(student.get("draw_time", "")),
                str(student.get("id", "")),
                str(student.get("name", "")),
            ]
            if has_gender:
                row.append(str(student.get("gender", "")))
            if has_group:
                row.append(str(student.get("group", "")))
            if has_class_record:
                row.append(str(student.get("class_name", "")))
            row.append(str(format_weight(student.get("weight", ""))))
            rows.append(row)

        return HistoryTablePayload(
            rows=rows,
            available_subjects=available_subjects,
            all_names=all_names,
            has_gender=has_gender,
            has_group=has_group,
            has_class_record=has_class_record,
        )

    stats_data = get_roll_call_student_stats_data(
        cleaned_students, base_history_data, selected_name, subject_name
    )
    has_class_record = any(item.get("class_name", "") for item in stats_data)
    format_weight, _, _ = format_weight_for_display(stats_data, "weight")

    if sort_column >= 0:

        def sort_key(student: dict[str, Any]):
            if sort_column == 0:
                return student.get("draw_time", "")
            if sort_column == 1:
                return str(student.get("draw_method", ""))
            if sort_column == 2:
                return _safe_int(student.get("draw_people_numbers", 0))
            if sort_column == 3:
                return str(student.get("draw_gender", ""))
            if sort_column == 4:
                return str(student.get("draw_group", ""))
            if sort_column == 5:
                return str(student.get("class_name", ""))
            if sort_column == 6:
                return _safe_float(student.get("weight", ""))
            return ""

        stats_data.sort(key=sort_key, reverse=reverse_order)
    else:
        stats_data.sort(key=lambda item: item.get("draw_time", ""), reverse=True)

    rows = []
    for student in stats_data:
        draw_method = str(student.get("draw_method", ""))
        if draw_method == "0":
            mode_text = get_content_name_async(
                "roll_call_history_table", "draw_method_random"
            )
        elif draw_method == "1":
            mode_text = get_content_name_async(
                "roll_call_history_table", "draw_method_weight"
            )
        else:
            mode_text = draw_method

        row = [
            str(student.get("draw_time", "")),
            str(mode_text),
            str(student.get("draw_people_numbers", 0)),
        ]
        if has_gender:
            row.append(str(student.get("draw_gender", "")))
        if has_group:
            row.append(str(student.get("draw_group", "")))
        if has_class_record:
            row.append(str(student.get("class_name", "")))
        row.append(str(format_weight(student.get("weight", 0))))
        rows.append(row)

    return HistoryTablePayload(
        rows=rows,
        available_subjects=available_subjects,
        all_names=all_names,
        has_gender=has_gender,
        has_group=has_group,
        has_class_record=has_class_record,
    )


def build_lottery_history_payload(
    pool_name: str,
    mode_index: int,
    subject_name: str,
    selected_name: str,
    sort_column: int,
    sort_order_desc: bool,
) -> HistoryTablePayload:
    cleaned_lotterys = get_lottery_pool_list(pool_name)
    all_names = [name for _, name, _ in cleaned_lotterys if name]
    history_data = get_lottery_history_data(pool_name)
    available_subjects = _collect_lottery_subjects(history_data)
    reverse_order = bool(sort_order_desc)

    if mode_index == 0:
        lotterys_data = get_lottery_prizes_data(cleaned_lotterys, history_data)
        format_weight, _, _ = format_weight_for_display(lotterys_data, "weight")

        if sort_column >= 0:

            def sort_key(lottery: dict[str, Any]):
                if sort_column == 0:
                    return lottery.get("id", "")
                if sort_column == 1:
                    return lottery.get("name", "")
                if sort_column == 2:
                    return _safe_int(lottery.get("total_count", 0))
                if sort_column == 3:
                    return _safe_float(lottery.get("weight", ""))
                return ""

            lotterys_data.sort(key=sort_key, reverse=reverse_order)

        rows = [
            [
                str(lottery.get("id", "")),
                str(lottery.get("name", "")),
                str(lottery.get("total_count_str", lottery.get("total_count", 0))),
                str(format_weight(lottery.get("weight", 0))),
            ]
            for lottery in lotterys_data
        ]
        return HistoryTablePayload(
            rows=rows,
            available_subjects=available_subjects,
            all_names=all_names,
            has_class_record=False,
        )

    if mode_index == 1:
        lotterys_data = get_lottery_session_data(
            cleaned_lotterys, history_data, subject_name
        )
        has_class_record = any(item.get("class_name", "") for item in lotterys_data)
        format_weight, _, _ = format_weight_for_display(lotterys_data, "weight")

        if sort_column >= 0:

            def sort_key(lottery: dict[str, Any]):
                if sort_column == 0:
                    return lottery.get("draw_time", "")
                if sort_column == 1:
                    return lottery.get("id", "")
                if sort_column == 2:
                    return lottery.get("name", "")
                if sort_column == 3:
                    return lottery.get("class_name", "")
                if sort_column == 4:
                    return _safe_float(lottery.get("weight", ""))
                return ""

            lotterys_data.sort(key=sort_key, reverse=reverse_order)
        else:
            lotterys_data.sort(key=lambda item: item.get("draw_time", ""), reverse=True)

        rows = []
        for lottery in lotterys_data:
            row = [
                str(lottery.get("draw_time", "")),
                str(lottery.get("id", "")),
                str(lottery.get("name", "")),
            ]
            if has_class_record:
                row.append(str(lottery.get("class_name", "")))
            row.append(str(format_weight(lottery.get("weight", 0))))
            rows.append(row)

        return HistoryTablePayload(
            rows=rows,
            available_subjects=available_subjects,
            all_names=all_names,
            has_class_record=has_class_record,
        )

    stats_data = get_lottery_prize_stats_data(
        cleaned_lotterys, history_data, selected_name, subject_name
    )
    has_class_record = any(item.get("class_name", "") for item in stats_data)
    format_weight, _, _ = format_weight_for_display(stats_data, "weight")

    if sort_column >= 0:

        def sort_key(lottery: dict[str, Any]):
            if sort_column == 0:
                return lottery.get("draw_time", "")
            if sort_column == 1:
                return _safe_int(lottery.get("draw_lottery_numbers", 0))
            if sort_column == 2:
                return lottery.get("class_name", "")
            if sort_column == 3:
                return _safe_float(lottery.get("weight", ""))
            return ""

        stats_data.sort(key=sort_key, reverse=reverse_order)
    else:
        stats_data.sort(key=lambda item: item.get("draw_time", ""), reverse=True)

    rows = []
    for lottery in stats_data:
        row = [
            str(lottery.get("draw_time", "")),
            str(lottery.get("draw_lottery_numbers", 0)),
        ]
        if has_class_record:
            row.append(str(lottery.get("class_name", "")))
        row.append(str(format_weight(lottery.get("weight", ""))))
        rows.append(row)

    return HistoryTablePayload(
        rows=rows,
        available_subjects=available_subjects,
        all_names=all_names,
        has_class_record=has_class_record,
    )
