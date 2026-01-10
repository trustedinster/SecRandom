# ==================================================
# 点名工具类
# ==================================================
import json
from random import SystemRandom

from app.common.data.list import (
    get_group_list,
    get_student_list,
    filter_students_data,
    get_pool_list,
)
from app.common.roll_call.roll_call_utils import RollCallUtils
from app.common.history.history import calculate_weight
from app.common.behind_scenes.behind_scenes_utils import BehindScenesUtils
from app.tools.config import (
    calculate_remaining_count,
    read_drawn_record,
    read_drawn_record_simple,
    reset_drawn_record,
)
from app.tools.path_utils import get_data_path, open_file
from app.tools.settings_access import readme_settings_async, get_safe_font_size

from app.Language.obtain_language import get_any_position_value

system_random = SystemRandom()


class LotteryUtils:
    """抽奖工具类，提供通用的抽奖相关功能"""

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
    ):
        """
        更新多数量显示标签的文本

        Args:
            list_combobox_text: 班级下拉框当前文本
            range_combobox_index: 范围下拉框当前索引
            range_combobox_text: 范围下拉框当前文本
            gender_combobox_text: 性别下拉框当前文本
            half_repeat_setting: 半重复设置值

        Returns:
            tuple: (总人数, 剩余人数, 格式化文本)
        """
        # 根据范围计算实际人数
        total_count = LotteryUtils.get_total_count(
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

        # 根据是否为小组模式选择不同的文本模板
        if range_combobox_index == 1:  # 小组模式
            text_template = get_any_position_value(
                "roll_call", "many_count_label", "text_3"
            )
        else:  # 学生模式
            text_template = get_any_position_value(
                "roll_call", "many_count_label", "text_0"
            )

        formatted_text = text_template.format(
            total_count=total_count, remaining_count=remaining_count
        )

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
        pool_name=None,
        prize_list=None,
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
            pool_name: 奖池名称（用于抽奖模式下应用内幕设置）
            prize_list: 奖品列表（用于提高指定该奖品的学生的权重）

        Returns:
            dict: 包含抽取结果的字典
        """
        student_file = get_data_path("list/roll_call_list", f"{class_name}.json")
        with open_file(student_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        students_data = filter_students_data(
            data, group_index, group_filter, gender_index, gender_filter
        )

        if group_index == 1:
            # 小组模式下，按小组名称排序
            students_data = sorted(students_data, key=lambda x: x[3])  # x[3]是小组名称

            # 首先将学生数据转换为字典列表
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

            # 处理小组模式下的特殊逻辑
            draw_type = readme_settings_async("roll_call_settings", "draw_type")
            selected_groups = RollCallUtils.draw_random_groups(
                students_dict_list, current_count, draw_type
            )

            return {
                "selected_students": selected_groups,
                "class_name": class_name,
                "selected_students_dict": [],  # 小组模式下不存储学生字典
                "group_filter": group_filter,
                "gender_filter": gender_filter,
            }

        # 首先将学生数据转换为字典列表
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
            drawn_records = read_drawn_record(class_name, gender_filter, group_filter)
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
            # 注意：这里我们返回一个特殊的标记，让调用者处理
            return {"reset_required": True}

        draw_type = readme_settings_async("roll_call_settings", "draw_type")
        if draw_type == 1:
            students_with_weight = calculate_weight(students_dict_list, class_name)
            weights = []
            for student in students_with_weight:
                weights.append(student.get("weight", 1.0))
        else:
            students_with_weight = students_dict_list
            weights = [1.0] * len(students_dict_list)

        # 应用内幕设置（抽奖模式下按奖池应用权重）
        if pool_name:
            students_with_weight, behind_scenes_weights = (
                BehindScenesUtils.apply_probability_weights(
                    students_with_weight, 1, class_name, pool_name, prize_list
                )
            )

            # 检查是否有必中人员
            guaranteed_students = BehindScenesUtils.ensure_guaranteed_selection(
                students_with_weight, behind_scenes_weights, class_name, pool_name
            )
            if guaranteed_students is not None:
                # 存在必中人员，直接返回
                selected_students = []
                selected_students_dict = []
                for student in guaranteed_students:
                    selected_students.append(
                        (
                            student.get("id"),
                            student.get("name"),
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

            # 使用内幕设置的权重
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
    def get_prize_total_count(pool_name: str) -> int:
        """获取奖池奖品总数"""
        try:
            from app.common.data.list import get_pool_list

            items = get_pool_list(pool_name)
            return len([item for item in items if item.get("exist", True)])
        except Exception:
            return 0

    @staticmethod
    def update_prize_many_count_label_text(pool_name: str, display_mode=None):
        """生成奖品总数/剩余显示文本

        Args:
            pool_name: 奖池名称
            display_mode: 显示模式 (0: 总+剩余, 1: 总数, 2: 剩余数, 3: 不显示)
        """
        total_count = LotteryUtils.get_prize_total_count(pool_name)
        remaining_count = LotteryUtils.calculate_prize_remaining_count(pool_name)
        if remaining_count == 0:
            remaining_count = total_count

        # 如果未指定显示模式，从设置中获取
        if display_mode is None:
            display_mode = readme_settings_async(
                "page_management", "lottery_quantity_label"
            )

        # 根据显示模式选择不同的文本模板
        if display_mode == 0:
            text_template = get_any_position_value(
                "lottery", "many_count_label", "text_0"
            )
        elif display_mode == 1:
            text_template = get_any_position_value(
                "lottery", "many_count_label", "text_1"
            )
        elif display_mode == 2:
            text_template = get_any_position_value(
                "lottery", "many_count_label", "text_2"
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
    def draw_random_prizes(pool_name: str, current_count: int):
        """按权重抽取奖品"""
        try:
            items = get_pool_list(pool_name)
            if not items:
                return {
                    "selected_prizes": [],
                    "pool_name": pool_name,
                    "selected_prizes_dict": [],
                }
            # 非重复/半重复处理：根据 TEMP 记录过滤已达阈值的奖品（与 roll_call 一致）
            threshold = LotteryUtils._get_prize_draw_threshold()
            if threshold is not None:
                drawn_records = read_drawn_record_simple(pool_name)
                drawn_counts = {name: cnt for name, cnt in drawn_records}
                available = []
                for i in items:
                    name = i.get("name", "")
                    cnt = int(drawn_counts.get(name, 0))
                    if cnt < threshold:
                        available.append(i)
                items = available
                if not items:
                    return {"reset_required": True}

            # 应用内幕设置
            items, behind_scenes_weights = (
                BehindScenesUtils.apply_probability_weights_to_items(
                    items, 1, pool_name
                )
            )

            # 检查是否有必中奖品
            guaranteed_items = BehindScenesUtils.ensure_guaranteed_selection(
                items, behind_scenes_weights, pool_name
            )
            if guaranteed_items is not None:
                # 存在必中奖品，直接返回
                selected = []
                selected_dict = []
                for item in guaranteed_items:
                    selected.append(
                        (item.get("id"), item.get("name"), item.get("exist", True))
                    )
                    selected_dict.append(item)

                return {
                    "selected_prizes": selected,
                    "pool_name": pool_name,
                    "selected_prizes_dict": selected_dict,
                }

            # 准备权重
            weights = []
            for i, item in enumerate(items):
                base_weight = float(item.get("weight", 1))
                behind_scenes_weight = behind_scenes_weights[i]
                weights.append(base_weight * behind_scenes_weight)

            draw = min(current_count, len(items))
            selected = []
            selected_dict = []
            for _ in range(draw):
                if not items:
                    break
                total_weight = sum(weights)
                if total_weight <= 0:
                    idx = system_random.randint(0, len(items) - 1)
                else:
                    rv = system_random.uniform(0, total_weight)
                    cum = 0
                    idx = 0
                    for i, w in enumerate(weights):
                        cum += w
                        if rv <= cum:
                            idx = i
                            break
                chosen = items[idx]
                selected.append(
                    (chosen.get("id"), chosen.get("name"), chosen.get("exist", True))
                )
                selected_dict.append(chosen)
                items.pop(idx)
                weights.pop(idx)
            return {
                "selected_prizes": selected,
                "pool_name": pool_name,
                "selected_prizes_dict": selected_dict,
            }
        except Exception:
            return {
                "selected_prizes": [],
                "pool_name": pool_name,
                "selected_prizes_dict": [],
            }

    @staticmethod
    def _get_prize_draw_threshold():
        """获取奖品抽取阈值：None 表示可重复；1 表示不重复；半重复返回次数阈值"""
        try:
            mode = readme_settings_async("lottery_settings", "draw_mode")
            if mode == 1:
                return 1
            elif mode == 2:
                hr = readme_settings_async("lottery_settings", "half_repeat")
                try:
                    return int(hr) if hr else 1
                except Exception:
                    return 1
            else:
                return None
        except Exception:
            return None

    @staticmethod
    def calculate_prize_remaining_count(pool_name: str) -> int:
        """计算剩余可抽奖品数量，考虑不重复/半重复设置"""
        try:
            from app.common.data.list import get_pool_list

            threshold = LotteryUtils._get_prize_draw_threshold()
            items = [
                item for item in get_pool_list(pool_name) if item.get("exist", True)
            ]
            total = len(items)
            if threshold is None:
                return total
            drawn_records = read_drawn_record_simple(pool_name)
            drawn_counts = {name: cnt for name, cnt in drawn_records}
            remain = 0
            for i in items:
                name = i.get("name", "")
                cnt = int(drawn_counts.get(name, 0))
                if cnt < threshold:
                    remain += 1
            return remain
        except Exception:
            return 0

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
