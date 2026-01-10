# ==================================================
# 点名工具类
# ==================================================
import json
from random import SystemRandom

from app.common.data.list import get_group_list, get_student_list, filter_students_data
from app.common.history.history import calculate_weight
from app.common.fair_draw.avg_gap_protection import apply_avg_gap_protection
from app.common.behind_scenes.behind_scenes_utils import BehindScenesUtils
from app.tools.config import (
    calculate_remaining_count,
    read_drawn_record,
    reset_drawn_record,
    record_drawn_student,
)
from app.tools.path_utils import get_data_path, open_file
from app.tools.settings_access import readme_settings_async, get_safe_font_size
from app.common.display.result_display import ResultDisplayUtils
from app.common.history.history import save_roll_call_history

from app.Language.obtain_language import get_any_position_value

system_random = SystemRandom()


class RollCallUtils:
    """点名工具类，提供通用的点名相关功能"""

    _student_data_cache = {}
    _drawn_record_cache = {}
    _behind_scenes_cache = {}

    @staticmethod
    def get_total_count(list_combobox_text, range_combobox_index, range_combobox_text):
        """
        根据当前选择的范围计算实际人数

        Args:
            list_combobox_text: 班级下拉框当前文本
            range_combobox_index: 范围下拉框当前索引
            range_combobox_text: 范围下拉框当前文本

        Returns:
            int: 总人数
        """
        if range_combobox_index == 0:  # 全班
            students = get_student_list(list_combobox_text)
            total_count = len([s for s in students if s.get("exist", True)])
        elif range_combobox_index == 1:  # 小组模式 - 计算小组数量
            total_count = len(get_group_list(list_combobox_text))
        else:  # 特定小组 - 计算该小组的学生数量
            students = get_student_list(list_combobox_text)
            total_count = len(
                [
                    s
                    for s in students
                    if s["group"] == range_combobox_text and s.get("exist", True)
                ]
            )
        return total_count

    @staticmethod
    def update_many_count_label_text(
        list_combobox_text,
        range_combobox_index,
        range_combobox_text,
        gender_combobox_text,
        half_repeat_setting,
        display_mode=None,
    ):
        """
        更新多数量显示标签的文本

        Args:
            list_combobox_text: 班级下拉框当前文本
            range_combobox_index: 范围下拉框当前索引
            range_combobox_text: 范围下拉框当前文本
            gender_combobox_text: 性别下拉框当前文本
            half_repeat_setting: 半重复设置值
            display_mode: 显示模式 (0: 总+剩余, 1: 总数, 2: 剩余数, 3: 不显示)

        Returns:
            tuple: (总人数, 剩余人数, 格式化文本)
        """
        # 根据范围计算实际人数
        total_count = RollCallUtils.get_total_count(
            list_combobox_text, range_combobox_index, range_combobox_text
        )

        remaining_count = calculate_remaining_count(
            half_repeat=half_repeat_setting,
            class_name=list_combobox_text,
            gender_filter=gender_combobox_text,
            group_index=range_combobox_index,
            group_filter=range_combobox_text,
            total_count=total_count,
        )

        if remaining_count == 0:
            remaining_count = total_count

        # 如果未指定显示模式，从设置中获取
        if display_mode is None:
            display_mode = readme_settings_async(
                "page_management", "roll_call_quantity_label"
            )

        # 根据显示模式和是否为小组模式选择不同的文本模板
        if range_combobox_index == 1:  # 小组模式
            if display_mode == 0:
                text_template = get_any_position_value(
                    "roll_call", "many_count_label", "text_3"
                )
            elif display_mode == 1:
                text_template = get_any_position_value(
                    "roll_call", "many_count_label", "text_4"
                )
            elif display_mode == 2:
                text_template = get_any_position_value(
                    "roll_call", "many_count_label", "text_5"
                )
            else:  # display_mode == 3, 不显示
                text_template = ""
        else:  # 学生模式
            if display_mode == 0:
                text_template = get_any_position_value(
                    "roll_call", "many_count_label", "text_0"
                )
            elif display_mode == 1:
                text_template = get_any_position_value(
                    "roll_call", "many_count_label", "text_1"
                )
            elif display_mode == 2:
                text_template = get_any_position_value(
                    "roll_call", "many_count_label", "text_2"
                )
            else:  # display_mode == 3, 不显示
                text_template = ""

        if text_template:
            formatted_text = text_template.format(
                total_count=total_count, remaining_count=remaining_count
            )
        else:
            formatted_text = ""

        return total_count, remaining_count, formatted_text

    @staticmethod
    def draw_random_students(
        class_name,
        group_index,
        group_filter,
        gender_index,
        gender_filter,
        current_count,
        half_repeat,
    ):
        """
        抽取随机学生

        Args:
            class_name: 班级名称
            group_index: 小组索引
            group_filter: 小组过滤器
            gender_index: 性别索引
            gender_filter: 性别过滤器
            current_count: 当前抽取数量
            half_repeat: 半重复设置

        Returns:
            dict: 包含抽取结果的字典
        """
        cache_key = (
            f"{class_name}_{group_index}_{group_filter}_{gender_index}_{gender_filter}"
        )

        if cache_key not in RollCallUtils._student_data_cache:
            student_file = get_data_path("list/roll_call_list", f"{class_name}.json")
            with open_file(student_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            students_data = filter_students_data(
                data, group_index, group_filter, gender_index, gender_filter
            )

            RollCallUtils._student_data_cache[cache_key] = students_data
        else:
            students_data = RollCallUtils._student_data_cache[cache_key]

        if group_index == 1:
            students_data = sorted(students_data, key=lambda x: x[3])

            students_dict_list = []
            for student_tuple in students_data:
                student_dict = {
                    "id": student_tuple[0],
                    "name": student_tuple[1],
                    "gender": student_tuple[2],
                    "group": student_tuple[3],
                    "exist": student_tuple[4],
                }
                students_dict_list.append(student_dict)

            draw_type = readme_settings_async("roll_call_settings", "draw_type")
            selected_groups = RollCallUtils.draw_random_groups(
                students_dict_list, current_count, draw_type
            )

            return {
                "selected_students": selected_groups,
                "class_name": class_name,
                "selected_students_dict": [],
                "group_filter": group_filter,
                "gender_filter": gender_filter,
            }

        students_dict_list = []
        for student_tuple in students_data:
            student_dict = {
                "id": student_tuple[0],
                "name": student_tuple[1],
                "gender": student_tuple[2],
                "group": student_tuple[3],
                "exist": student_tuple[4],
            }
            students_dict_list.append(student_dict)

        if half_repeat > 0:
            record_key = f"{class_name}_{gender_filter}_{group_filter}"
            if record_key not in RollCallUtils._drawn_record_cache:
                drawn_records = read_drawn_record(
                    class_name, gender_filter, group_filter
                )
                RollCallUtils._drawn_record_cache[record_key] = drawn_records
            else:
                drawn_records = RollCallUtils._drawn_record_cache[record_key]

            drawn_counts = {name: count for name, count in drawn_records}

            filtered_students = []
            for student in students_dict_list:
                student_name = student["name"]
                if (
                    student_name not in drawn_counts
                    or drawn_counts[student_name] < half_repeat
                ):
                    filtered_students.append(student)

            students_dict_list = filtered_students

        if not students_dict_list:
            return {"reset_required": True}

        students_dict_list = apply_avg_gap_protection(
            students_dict_list, current_count, class_name, "roll_call"
        )

        students_dict_list, behind_scenes_weights = (
            BehindScenesUtils.apply_probability_weights(
                students_dict_list, 0, class_name
            )
        )

        # 检查是否有必中人员
        guaranteed_students = BehindScenesUtils.ensure_guaranteed_selection(
            students_dict_list, behind_scenes_weights, class_name
        )
        if guaranteed_students is not None:
            # 存在必中人员，直接返回
            selected_students = []
            selected_students_dict = []
            for student in guaranteed_students:
                selected_students.append(
                    (
                        student.get("id", ""),
                        student.get("name", ""),
                        student.get("exist", True),
                    )
                )
                selected_students_dict.append(student)

            return {
                "selected_students": selected_students,
                "class_name": class_name,
                "selected_students_dict": selected_students_dict,
                "group_filter": group_filter,
                "gender_filter": gender_filter,
            }

        draw_type = readme_settings_async("roll_call_settings", "draw_type")
        if draw_type == 1:
            students_with_weight = calculate_weight(students_dict_list, class_name)
            weights = []
            for i, student in enumerate(students_with_weight):
                # 结合内幕权重和历史权重
                base_weight = student.get("weight", 1.0)
                behind_scenes_weight = (
                    behind_scenes_weights[i] if i < len(behind_scenes_weights) else 1.0
                )
                weights.append(base_weight * behind_scenes_weight)
        else:
            students_with_weight = students_dict_list
            weights = behind_scenes_weights

        draw_count = current_count
        draw_count = min(draw_count, len(students_with_weight))

        selected_students = []
        selected_students_dict = []
        for _ in range(draw_count):
            if not students_with_weight:
                break
            total_weight = sum(weights)
            if total_weight <= 0:
                random_index = system_random.randint(0, len(students_with_weight) - 1)
            else:
                rand_value = system_random.uniform(0, total_weight)
                cumulative_weight = 0
                random_index = 0
                for i, weight in enumerate(weights):
                    cumulative_weight += weight
                    if rand_value <= cumulative_weight:
                        random_index = i
                        break

            selected_student = students_with_weight[random_index]
            id = selected_student.get("id", "")
            random_name = selected_student.get("name", "")
            exist = selected_student.get("exist", True)
            selected_students.append((id, random_name, exist))
            selected_students_dict.append(selected_student)

            students_with_weight.pop(random_index)
            weights.pop(random_index)

        return {
            "selected_students": selected_students,
            "class_name": class_name,
            "selected_students_dict": selected_students_dict,
            "group_filter": group_filter,
            "gender_filter": gender_filter,
        }

    @staticmethod
    def draw_random_groups(students_dict_list, current_count, draw_type):
        """
        抽取随机小组

        Args:
            students_dict_list: 学生字典列表
            current_count: 当前抽取数量
            draw_type: 抽取类型

        Returns:
            list: 选中的小组列表
        """
        # 小组模式下，students_data已经只包含小组信息
        # 直接使用小组数据进行抽取
        draw_count = min(current_count, len(students_dict_list))

        selected_groups = []
        if draw_type == 1:
            # 权重抽取模式下，所有小组权重相同
            weights = [1.0] * len(students_dict_list)

            # 根据权重抽取小组
            for _ in range(draw_count):
                if not students_dict_list:
                    break
                total_weight = sum(weights)
                if total_weight <= 0:
                    random_index = system_random.randint(0, len(students_dict_list) - 1)
                else:
                    rand_value = system_random.uniform(0, total_weight)
                    cumulative_weight = 0
                    random_index = 0
                    for i, weight in enumerate(weights):
                        cumulative_weight += weight
                        if rand_value <= cumulative_weight:
                            random_index = i
                            break

                selected_group = students_dict_list[random_index]
                selected_groups.append(
                    (None, selected_group["name"], True)
                )  # (id, name, exist)

                students_dict_list.pop(random_index)
                weights.pop(random_index)
        else:
            # 随机抽取模式
            for _ in range(draw_count):
                if not students_dict_list:
                    break
                random_index = system_random.randint(0, len(students_dict_list) - 1)
                selected_group = students_dict_list[random_index]
                selected_groups.append(
                    (None, selected_group["name"], True)
                )  # (id, name, exist)

                students_dict_list.pop(random_index)

        return selected_groups

    @staticmethod
    def prepare_notification_settings():
        """
        准备通知设置参数

        Returns:
            dict: 通知设置参数
        """
        # 读取所有相关设置并传递给通知服务
        settings = {
            # 点名设置
            "font_size": get_safe_font_size("roll_call_settings", "font_size"),
            "animation_color_theme": readme_settings_async(
                "roll_call_settings", "animation_color_theme"
            ),
            "display_format": readme_settings_async(
                "roll_call_settings", "display_format"
            ),
            "student_image": readme_settings_async(
                "roll_call_settings", "student_image"
            ),
            # 浮窗设置
            "animation": readme_settings_async(
                "roll_call_notification_settings", "animation"
            ),
            "transparency": readme_settings_async(
                "roll_call_notification_settings", "floating_window_transparency"
            ),
            "auto_close_time": readme_settings_async(
                "roll_call_notification_settings", "floating_window_auto_close_time"
            ),
            "enabled_monitor": readme_settings_async(
                "roll_call_notification_settings", "floating_window_enabled_monitor"
            ),
            "window_position": readme_settings_async(
                "roll_call_notification_settings", "floating_window_position"
            ),
            "horizontal_offset": readme_settings_async(
                "roll_call_notification_settings", "floating_window_horizontal_offset"
            ),
            "vertical_offset": readme_settings_async(
                "roll_call_notification_settings", "floating_window_vertical_offset"
            ),
            # 通知设置
            "notification_display_duration": readme_settings_async(
                "roll_call_notification_settings", "notification_display_duration"
            ),
        }

        return settings

    @staticmethod
    def reset_drawn_records(window, class_name, gender_filter, group_filter):
        """
        重置已抽取记录

        Args:
            window: 窗口对象（用于传递self参数）
            class_name: 班级名称
            gender_filter: 性别过滤器
            group_filter: 小组过滤器
        """
        reset_drawn_record(window, class_name, gender_filter, group_filter)

    @staticmethod
    def update_start_button_state(button, total_count):
        """
        根据总人数更新开始按钮的状态

        Args:
            button: 开始按钮对象
            total_count: 总人数
        """
        if total_count == 0:
            button.setEnabled(False)
        else:
            button.setEnabled(True)

    @staticmethod
    def create_display_settings(
        settings_group="roll_call_settings", display_settings=None
    ):
        """
        创建显示设置字典

        Args:
            settings_group: 设置组名称
            display_settings: 自定义显示设置字典，如果提供则合并到默认设置中

        Returns:
            dict: 显示设置字典
        """
        if display_settings:
            font_size = display_settings.get(
                "font_size", get_safe_font_size(settings_group, "font_size")
            )
            animation_color = display_settings.get(
                "animation_color_theme",
                readme_settings_async(settings_group, "animation_color_theme"),
            )
            display_format = display_settings.get(
                "display_format",
                readme_settings_async(settings_group, "display_format"),
            )
            show_student_image = display_settings.get(
                "student_image",
                readme_settings_async(settings_group, "student_image"),
            )
            show_random = display_settings.get(
                "show_random",
                readme_settings_async(settings_group, "show_random"),
            )
        else:
            font_size = get_safe_font_size(settings_group, "font_size")
            animation_color = readme_settings_async(
                settings_group, "animation_color_theme"
            )
            display_format = readme_settings_async(settings_group, "display_format")
            show_student_image = readme_settings_async(settings_group, "student_image")
            show_random = readme_settings_async(settings_group, "show_random")

        return {
            "font_size": font_size,
            "animation_color_theme": animation_color,
            "display_format": display_format,
            "student_image": show_student_image,
            "show_random": show_random,
        }

    @staticmethod
    def display_result(
        result_grid,
        class_name,
        selected_students,
        draw_count,
        group_index,
        settings_group="roll_call_settings",
        display_settings=None,
    ):
        """
        显示抽取结果

        Args:
            result_grid: 结果网格布局
            class_name: 班级名称
            selected_students: 选中的学生列表
            draw_count: 抽取人数
            group_index: 小组索引
            settings_group: 设置组名称
            display_settings: 自定义显示设置字典
        """
        display_dict = RollCallUtils.create_display_settings(
            settings_group, display_settings
        )

        student_labels = ResultDisplayUtils.create_student_label(
            class_name=class_name,
            selected_students=selected_students,
            draw_count=draw_count,
            font_size=display_dict["font_size"],
            animation_color=display_dict["animation_color_theme"],
            display_format=display_dict["display_format"],
            show_student_image=display_dict["student_image"],
            group_index=group_index,
            show_random=display_dict["show_random"],
            settings_group=settings_group,
        )
        ResultDisplayUtils.display_results_in_grid(result_grid, student_labels)

    @staticmethod
    def record_drawn_students(
        class_name,
        selected_students,
        selected_students_dict,
        gender_filter,
        group_filter,
        half_repeat,
    ):
        """
        记录已抽取的学生

        Args:
            class_name: 班级名称
            selected_students: 选中的学生列表
            selected_students_dict: 选中的学生字典列表
            gender_filter: 性别过滤器
            group_filter: 小组过滤器
            half_repeat: 半重复设置
        """
        if half_repeat > 0:
            record_drawn_student(
                class_name=class_name,
                gender=gender_filter,
                group=group_filter,
                student_name=selected_students,
            )

        if selected_students_dict:
            save_roll_call_history(
                class_name=class_name,
                selected_students=selected_students_dict,
                group_filter=group_filter,
                gender_filter=gender_filter,
            )

    @staticmethod
    def prepare_notification_settings_by_group(
        settings_group="roll_call_notification_settings",
        display_settings=None,
    ):
        """
        根据设置组准备通知设置参数

        Args:
            settings_group: 设置组名称
            display_settings: 显示设置字典

        Returns:
            dict: 通知设置参数
        """
        if display_settings:
            font_size = display_settings.get("font_size")
            animation_color_theme = display_settings.get("animation_color_theme")
            display_format = display_settings.get("display_format")
            student_image = display_settings.get("student_image")
            show_random = display_settings.get("show_random")
        else:
            font_size = get_safe_font_size(
                settings_group.replace("_notification_settings", "_settings"),
                "font_size",
            )
            animation_color_theme = readme_settings_async(
                settings_group.replace("_notification_settings", "_settings"),
                "animation_color_theme",
            )
            display_format = readme_settings_async(
                settings_group.replace("_notification_settings", "_settings"),
                "display_format",
            )
            student_image = readme_settings_async(
                settings_group.replace("_notification_settings", "_settings"),
                "student_image",
            )
            show_random = readme_settings_async(
                settings_group.replace("_notification_settings", "_settings"),
                "show_random",
            )

        settings = {
            "font_size": font_size,
            "animation_color_theme": animation_color_theme,
            "display_format": display_format,
            "student_image": student_image,
            "show_random": show_random,
            "animation": readme_settings_async(settings_group, "animation"),
            "transparency": readme_settings_async(
                settings_group, "floating_window_transparency"
            ),
            "auto_close_time": readme_settings_async(
                settings_group, "floating_window_auto_close_time"
            ),
            "enabled_monitor": readme_settings_async(
                settings_group, "floating_window_enabled_monitor"
            ),
            "window_position": readme_settings_async(
                settings_group, "floating_window_position"
            ),
            "horizontal_offset": readme_settings_async(
                settings_group, "floating_window_horizontal_offset"
            ),
            "vertical_offset": readme_settings_async(
                settings_group, "floating_window_vertical_offset"
            ),
            "notification_display_duration": readme_settings_async(
                settings_group, "notification_display_duration"
            ),
        }

        return settings

    @staticmethod
    def show_notification_if_enabled(
        class_name,
        selected_students,
        draw_count,
        settings_group="roll_call_notification_settings",
        display_settings=None,
        is_animating=False,
    ):
        """
        如果启用了通知服务，则显示抽取结果通知

        Args:
            class_name: 班级名称
            selected_students: 选中的学生列表
            draw_count: 抽取人数
            settings_group: 设置组名称
            display_settings: 显示设置字典
            is_animating: 是否在动画过程中，如果是则不启动自动关闭定时器
        """
        call_notification_service = readme_settings_async(
            settings_group, "call_notification_service"
        )

        if not call_notification_service:
            return

        settings = RollCallUtils.prepare_notification_settings_by_group(
            settings_group, display_settings
        )

        use_main_window_when_exceed_threshold = readme_settings_async(
            settings_group, "use_main_window_when_exceed_threshold"
        )
        max_notify_count = readme_settings_async(
            settings_group, "main_window_display_threshold"
        )

        if use_main_window_when_exceed_threshold:
            if draw_count <= max_notify_count:
                ResultDisplayUtils.show_notification_if_enabled(
                    class_name,
                    selected_students,
                    draw_count,
                    settings,
                    settings_group=settings_group,
                    is_animating=is_animating,
                )
        else:
            ResultDisplayUtils.show_notification_if_enabled(
                class_name,
                selected_students,
                draw_count,
                settings,
                settings_group=settings_group,
                is_animating=is_animating,
            )
