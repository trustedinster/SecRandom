# ==================================================
# 导入库
# ==================================================

from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtNetwork import *
from qfluentwidgets import *

from app.tools.variable import *
from app.tools.path_utils import *
from app.tools.personalised import *
from app.tools.settings_default import *
from app.tools.settings_access import *
from app.Language.obtain_language import *

from app.common.data.list import *
from app.common.history.history import *
from app.common.display.result_display import *
from app.tools.config import *
from app.common.roll_call.roll_call_utils import RollCallUtils
from app.tools.variable import *
from app.common.voice.voice import TTSHandler

from app.page_building.another_window import *

from random import SystemRandom

system_random = SystemRandom()


# ==================================================
# 班级点名类
# ==================================================
class roll_call(QWidget):
    # 添加一个信号，当设置发生变化时发出
    settingsChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.file_watcher = QFileSystemWatcher()
        self.setup_file_watcher()

        # 长按功能相关变量
        self.press_timer = QTimer()
        self.press_timer.timeout.connect(self.handle_long_press)
        self.long_press_interval = 100  # 长按时连续触发的间隔时间(毫秒)
        self.long_press_delay = 500  # 开始长按前的延迟时间(毫秒)
        self.is_long_pressing = False  # 是否正在长按
        self.long_press_direction = 0  # 长按方向：1为增加，-1为减少

        # 初始化TTS处理器
        self.tts_handler = TTSHandler()

        self.initUI()
        self.setupSettingsListener()

    def handle_long_press(self):
        """处理长按事件"""
        if self.is_long_pressing:
            # 更新定时器间隔为连续触发间隔
            self.press_timer.setInterval(self.long_press_interval)
            # 执行更新计数
            self.update_count(self.long_press_direction)

    def start_long_press(self, direction):
        """开始长按

        Args:
            direction (int): 长按方向，1为增加，-1为减少
        """
        self.long_press_direction = direction
        self.is_long_pressing = True
        # 设置初始延迟
        self.press_timer.setInterval(self.long_press_delay)
        self.press_timer.start()

    def stop_long_press(self):
        """停止长按"""
        self.is_long_pressing = False
        self.press_timer.stop()

    def closeEvent(self, event):
        """窗口关闭事件，清理资源"""
        try:
            if hasattr(self, "file_watcher"):
                self.file_watcher.removePaths(self.file_watcher.directories())
                self.file_watcher.removePaths(self.file_watcher.files())
            # 停止长按定时器
            if hasattr(self, "press_timer"):
                self.press_timer.stop()
        except Exception as e:
            logger.error(f"清理文件监控器失败: {e}")
        super().closeEvent(event)

    def initUI(self):
        """初始化UI"""
        container = QWidget()
        roll_call_container = QVBoxLayout(container)
        roll_call_container.setContentsMargins(0, 0, 0, 0)

        self.result_widget = QWidget()
        self.result_layout = QVBoxLayout(self.result_widget)
        self.result_grid = QGridLayout()
        self.result_layout.addStretch()
        self.result_layout.addLayout(self.result_grid)
        self.result_layout.addStretch()
        roll_call_container.addWidget(self.result_widget)

        self.reset_button = PushButton(
            get_content_pushbutton_name_async("roll_call", "reset_button")
        )
        self._set_widget_font(self.reset_button, 15)
        self.reset_button.setFixedHeight(45)
        self.reset_button.clicked.connect(lambda: self.reset_count())

        self.minus_button = PushButton("-")
        self._set_widget_font(self.minus_button, 20)
        self.minus_button.setFixedSize(45, 45)
        self.minus_button.clicked.connect(lambda: self.update_count(-1))

        # 添加长按连续减功能
        self.minus_button.pressed.connect(lambda: self.start_long_press(-1))
        self.minus_button.released.connect(self.stop_long_press)

        self.count_label = BodyLabel("1")
        self.count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._set_widget_font(self.count_label, 20)
        self.count_label.setFixedSize(65, 45)
        self.current_count = 1

        self.plus_button = PushButton("+")
        self._set_widget_font(self.plus_button, 20)
        self.plus_button.setFixedSize(45, 45)
        self.plus_button.clicked.connect(lambda: self.update_count(1))

        # 添加长按连续加功能
        self.plus_button.pressed.connect(lambda: self.start_long_press(1))
        self.plus_button.released.connect(self.stop_long_press)

        self.minus_button.setEnabled(False)
        self.plus_button.setEnabled(True)

        self.count_widget = QWidget()
        horizontal_layout = QHBoxLayout()
        horizontal_layout.setContentsMargins(0, 0, 0, 0)
        horizontal_layout.setSpacing(0)
        horizontal_layout.addWidget(self.minus_button)
        horizontal_layout.addStretch()
        horizontal_layout.addWidget(self.count_label)
        horizontal_layout.addStretch()
        horizontal_layout.addWidget(self.plus_button)
        self.count_widget.setLayout(horizontal_layout)

        self.start_button = PrimaryPushButton(
            get_content_pushbutton_name_async("roll_call", "start_button")
        )
        self._set_widget_font(self.start_button, 15)
        self.start_button.setFixedHeight(45)
        self.start_button.clicked.connect(lambda: self.start_draw())

        self.list_combobox = ComboBox()
        self._set_widget_font(self.list_combobox, 12)
        self.list_combobox.setFixedHeight(45)
        self.list_combobox.setPlaceholderText(
            get_content_name_async("roll_call", "default_empty_item")
        )
        # 延迟填充班级列表，避免启动时进行文件IO
        self.list_combobox.currentTextChanged.connect(self.on_class_changed)

        self.range_combobox = ComboBox()
        self._set_widget_font(self.range_combobox, 12)
        self.range_combobox.setFixedHeight(45)
        # 延迟填充范围选项
        self.range_combobox.currentTextChanged.connect(self.on_filter_changed)

        self.gender_combobox = ComboBox()
        self._set_widget_font(self.gender_combobox, 12)
        self.gender_combobox.setFixedHeight(45)
        # 延迟填充性别选项
        self.gender_combobox.currentTextChanged.connect(self.on_filter_changed)

        self.remaining_button = PushButton(
            get_content_pushbutton_name_async("roll_call", "remaining_button")
        )
        self._set_widget_font(self.remaining_button, 12)
        self.remaining_button.setFixedHeight(45)
        self.remaining_button.clicked.connect(lambda: self.show_remaining_list())

        # 初始时不进行昂贵的数据加载，改为延迟填充
        self.total_count = 0
        self.remaining_count = 0

        text_template = get_any_position_value(
            "roll_call", "many_count_label", "text_0"
        )
        # 使用占位值，实际文本将在 populate_lists 中更新
        formatted_text = text_template.format(total_count=0, remaining_count=0)
        self.many_count_label = BodyLabel(formatted_text)
        self.many_count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._set_widget_font(self.many_count_label, 10)

        self.control_widget = QWidget()
        self.control_layout = QVBoxLayout(self.control_widget)
        self.control_layout.setContentsMargins(0, 0, 0, 0)
        self.control_layout.addStretch()

        # 根据页面管理设置决定是否添加控件
        self.add_control_widget_if_enabled(
            self.control_layout,
            self.reset_button,
            "page_management",
            "roll_call_reset_button",
        )

        self.add_control_widget_if_enabled(
            self.control_layout,
            self.count_widget,
            "page_management",
            "roll_call_quantity_control",
        )

        self.add_control_widget_if_enabled(
            self.control_layout,
            self.start_button,
            "page_management",
            "roll_call_start_button",
        )

        self.add_control_widget_if_enabled(
            self.control_layout, self.list_combobox, "page_management", "roll_call_list"
        )

        self.add_control_widget_if_enabled(
            self.control_layout,
            self.range_combobox,
            "page_management",
            "roll_call_range",
        )

        self.add_control_widget_if_enabled(
            self.control_layout,
            self.gender_combobox,
            "page_management",
            "roll_call_gender",
        )

        self.add_control_widget_if_enabled(
            self.control_layout,
            self.remaining_button,
            "page_management",
            "roll_call_remaining_button",
        )

        self.add_control_widget_if_enabled(
            self.control_layout,
            self.many_count_label,
            "page_management",
            "roll_call_quantity_label",
        )

        scroll = SmoothScrollArea()
        scroll.setWidget(container)
        scroll.setWidgetResizable(True)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 根据页面管理设置决定控制面板位置
        roll_call_method = readme_settings_async("page_management", "roll_call_method")

        if roll_call_method == 0:  # 左侧
            main_layout.addWidget(self.control_widget)
            main_layout.addWidget(scroll, 1)
        else:  # 右侧
            main_layout.addWidget(scroll, 1)
            main_layout.addWidget(self.control_widget)

        # 统一调整控件宽度以适应文本内容
        self._adjustControlWidgetWidths()

        # 在事件循环中延迟填充下拉框和初始统计，减少启动阻塞
        QTimer.singleShot(0, self.populate_lists)

    def add_control_widget_if_enabled(
        self, layout, widget, settings_group, setting_name
    ):
        """根据设置决定是否添加控件到布局"""
        try:
            is_enabled = readme_settings_async(settings_group, setting_name)
            if is_enabled:
                layout.addWidget(widget, alignment=Qt.AlignmentFlag.AlignCenter)
        except Exception as e:
            logger.error(f"添加控件 {setting_name} 时出错: {e}")
            # 出错时默认添加控件
            layout.addWidget(widget, alignment=Qt.AlignmentFlag.AlignCenter)

    def _adjustControlWidgetWidths(self):
        """统一调整控件宽度以适应文本内容"""
        try:
            # 收集所有需要调整宽度的控件
            widgets_to_adjust = [
                self.reset_button,
                self.count_widget,
                self.start_button,
                self.list_combobox,
                self.range_combobox,
                self.gender_combobox,
                self.remaining_button,
                self.many_count_label,
            ]

            # 计算所有控件文本所需的最大宽度
            max_text_width = 0
            for widget in widgets_to_adjust:
                fm = widget.fontMetrics()
                # 检查按钮/标签文本
                if hasattr(widget, "text") and widget.text():
                    text_width = fm.horizontalAdvance(widget.text())
                    max_text_width = max(max_text_width, text_width)
                # 检查占位符文本
                if hasattr(widget, "placeholderText") and widget.placeholderText():
                    text_width = fm.horizontalAdvance(widget.placeholderText())
                    max_text_width = max(max_text_width, text_width)
                # 检查下拉框所有选项的宽度
                if hasattr(widget, "count"):
                    for i in range(widget.count()):
                        item_text = widget.itemText(i)
                        if item_text:
                            text_width = fm.horizontalAdvance(item_text)
                            max_text_width = max(max_text_width, text_width)

            # 计算统一宽度（文本宽度 + 边距 + 下拉框箭头空间）
            padding = 60  # 左右边距 + 下拉箭头空间
            min_width = 165  # 最小宽度
            unified_width = max(min_width, max_text_width + padding)

            # 设置所有控件的固定宽度
            for widget in widgets_to_adjust:
                widget.setFixedWidth(int(unified_width))

        except Exception as e:
            logger.debug(f"调整控件宽度时出错: {e}")

    def on_class_changed(self):
        """当班级选择改变时，更新范围选择、性别选择和人数显示"""
        self.range_combobox.blockSignals(True)
        self.gender_combobox.blockSignals(True)

        try:
            self.range_combobox.clear()
            # 范围
            base_options = get_content_combo_name_async("roll_call", "range_combobox")
            group_list = get_group_list(self.list_combobox.currentText())
            # 如果有小组，才添加"抽取全部小组"选项
            if group_list and group_list != [""]:
                # 添加基础选项和小组列表
                self.range_combobox.addItems(base_options + group_list)
            else:
                # 只添加基础选项，跳过"抽取全部小组"
                self.range_combobox.addItems(base_options[:1])  # 只添加"抽取全部学生"

            # 性别
            self.gender_combobox.clear()
            gender_options = get_content_combo_name_async(
                "roll_call", "gender_combobox"
            )
            gender_list = get_gender_list(self.list_combobox.currentText())
            # 如果有性别，才添加"抽取全部性别"选项
            if gender_list and gender_list != [""]:
                # 添加基础选项和性别列表
                self.gender_combobox.addItems(gender_options + gender_list)
            else:
                # 只添加基础选项，跳过"抽取全部性别"
                self.gender_combobox.addItems(
                    gender_options[:1]
                )  # 只添加"抽取全部性别"

            # 使用统一的方法更新剩余人数显示
            self.update_many_count_label()

            # 根据当前选择的范围计算实际的总人数
            total_count = RollCallUtils.get_total_count(
                self.list_combobox.currentText(),
                self.range_combobox.currentIndex(),
                self.range_combobox.currentText(),
            )

            # 根据总人数是否为0，启用或禁用开始按钮
            RollCallUtils.update_start_button_state(self.start_button, total_count)

            # 更新剩余名单窗口
            if (
                hasattr(self, "remaining_list_page")
                and self.remaining_list_page is not None
            ):
                QTimer.singleShot(APP_INIT_DELAY, self._update_remaining_list_delayed)
        except Exception as e:
            logger.error(f"切换班级时发生错误: {e}")
        finally:
            self.range_combobox.blockSignals(False)
            self.gender_combobox.blockSignals(False)

    def on_filter_changed(self):
        """当范围或性别选择改变时，更新人数显示"""
        try:
            # 使用统一的方法更新剩余人数显示
            self.update_many_count_label()

            # 根据当前选择的范围计算实际的总人数
            total_count = RollCallUtils.get_total_count(
                self.list_combobox.currentText(),
                self.range_combobox.currentIndex(),
                self.range_combobox.currentText(),
            )

            # 根据总人数是否为0，启用或禁用开始按钮
            RollCallUtils.update_start_button_state(self.start_button, total_count)

            if (
                hasattr(self, "remaining_list_page")
                and self.remaining_list_page is not None
            ):
                QTimer.singleShot(APP_INIT_DELAY, self._update_remaining_list_delayed)
        except Exception as e:
            logger.error(f"切换筛选条件时发生错误: {e}")

    def _update_remaining_list_delayed(self):
        """延迟更新剩余名单窗口的方法"""
        try:
            if (
                hasattr(self, "remaining_list_page")
                and self.remaining_list_page is not None
            ):
                class_name = self.list_combobox.currentText()
                group_filter = self.range_combobox.currentText()
                gender_filter = self.gender_combobox.currentText()
                group_index = self.range_combobox.currentIndex()
                gender_index = self.gender_combobox.currentIndex()
                half_repeat = readme_settings_async("roll_call_settings", "half_repeat")

                if hasattr(self.remaining_list_page, "update_remaining_list"):
                    self.remaining_list_page.update_remaining_list(
                        class_name,
                        group_filter,
                        gender_filter,
                        half_repeat,
                        group_index,
                        gender_index,
                        emit_signal=False,
                        source="roll_call",
                    )
                else:
                    if hasattr(self.remaining_list_page, "class_name"):
                        self.remaining_list_page.class_name = class_name
                    if hasattr(self.remaining_list_page, "group_filter"):
                        self.remaining_list_page.group_filter = group_filter
                    if hasattr(self.remaining_list_page, "gender_filter"):
                        self.remaining_list_page.gender_filter = gender_filter
                    if hasattr(self.remaining_list_page, "group_index"):
                        self.remaining_list_page.group_index = group_index
                    if hasattr(self.remaining_list_page, "gender_index"):
                        self.remaining_list_page.gender_index = gender_index
                    if hasattr(self.remaining_list_page, "half_repeat"):
                        self.remaining_list_page.half_repeat = half_repeat

                    if hasattr(self.remaining_list_page, "count_changed"):
                        self.remaining_list_page.count_changed.emit(
                            self.remaining_count
                        )
        except Exception as e:
            logger.error(f"延迟更新剩余名单时发生错误: {e}")

    def start_draw(self):
        """开始抽取"""
        self.start_button.setText(
            get_content_pushbutton_name_async("roll_call", "start_button")
        )
        self.start_button.setEnabled(True)
        try:
            self.start_button.clicked.disconnect()
        except Exception as e:
            logger.exception(
                "Error disconnecting start_button clicked (ignored): {}", e
            )
        self.draw_random()
        animation = readme_settings_async("roll_call_settings", "animation")
        autoplay_count = readme_settings_async("roll_call_settings", "autoplay_count")
        animation_interval = readme_settings_async(
            "roll_call_settings", "animation_interval"
        )
        if animation == 0:
            self.start_button.setText(
                get_content_pushbutton_name_async("roll_call", "stop_button")
            )
            self.is_animating = True
            self.animation_timer = QTimer()
            self.animation_timer.timeout.connect(self.animate_result)
            self.animation_timer.start(animation_interval)
            self.start_button.clicked.connect(lambda: self.stop_animation())
        elif animation == 1:
            self.is_animating = True
            self.animation_timer = QTimer()
            self.animation_timer.timeout.connect(self.animate_result)
            self.animation_timer.start(animation_interval)
            self.start_button.setEnabled(False)
            QTimer.singleShot(
                autoplay_count * animation_interval,
                lambda: [
                    self.animation_timer.stop(),
                    self.stop_animation(),
                    self.start_button.setEnabled(True),
                ],
            )
            self.start_button.clicked.connect(lambda: self.start_draw())
        elif animation == 2:
            if hasattr(self, "final_selected_students_dict") and hasattr(
                self, "final_class_name"
            ):
                save_roll_call_history(
                    class_name=self.final_class_name,
                    selected_students=self.final_selected_students_dict,
                    group_filter=self.final_group_filter,
                    gender_filter=self.final_gender_filter,
                )
            self.start_button.clicked.connect(lambda: self.start_draw())

    def stop_animation(self):
        """停止动画"""
        # 检查是否是闪抽模式
        is_quick_draw = hasattr(self, "is_quick_draw") and self.is_quick_draw

        if hasattr(self, "animation_timer") and self.animation_timer.isActive():
            self.animation_timer.stop()
        self.start_button.setText(
            get_content_pushbutton_name_async("roll_call", "start_button")
        )
        self.is_animating = False
        try:
            self.start_button.clicked.disconnect()
        except Exception as e:
            logger.exception(
                "Error disconnecting start_button clicked during stop_animation (ignored): {}",
                e,
            )
        self.start_button.clicked.connect(lambda: self.start_draw())

        half_repeat = readme_settings_async("roll_call_settings", "half_repeat")
        if half_repeat > 0:
            record_drawn_student(
                class_name=self.final_class_name,
                gender=self.final_gender_filter,
                group=self.final_group_filter,
                student_name=self.final_selected_students,
            )

            self.update_many_count_label()

            if (
                hasattr(self, "remaining_list_page")
                and self.remaining_list_page is not None
                and hasattr(self.remaining_list_page, "count_changed")
            ):
                self.remaining_list_page.count_changed.emit(self.remaining_count)

            # 更新剩余名单窗口
            QTimer.singleShot(APP_INIT_DELAY, self._update_remaining_list_delayed)

        if hasattr(self, "final_selected_students") and hasattr(
            self, "final_class_name"
        ):
            save_roll_call_history(
                class_name=self.final_class_name,
                selected_students=self.final_selected_students_dict,
                group_filter=self.final_group_filter,
                gender_filter=self.final_gender_filter,
            )

        if hasattr(self, "final_selected_students"):
            # 如果是闪抽模式，不调用display_result，避免覆盖闪抽结果
            if not is_quick_draw:
                self.display_result(self.final_selected_students, self.final_class_name)

                # 检查是否启用了通知服务
                call_notification_service = readme_settings_async(
                    "roll_call_notification_settings", "call_notification_service"
                )
                if call_notification_service:
                    # 准备通知设置
                    settings = RollCallUtils.prepare_notification_settings()

                    # 使用ResultDisplayUtils显示通知
                    ResultDisplayUtils.show_notification_if_enabled(
                        self.final_class_name,
                        self.final_selected_students,
                        self.current_count,
                        settings,
                        settings_group="roll_call_notification_settings",
                    )

            # 播放语音
            self.play_voice_result()

    def play_voice_result(self):
        """播放语音结果"""
        try:
            # 准备语音设置
            voice_settings = {
                "voice_volume": readme_settings_async(
                    "basic_voice_settings", "volume_size"
                ),
                "voice_speed": readme_settings_async(
                    "basic_voice_settings", "speech_rate"
                ),
                "system_voice_name": readme_settings_async(
                    "basic_voice_settings", "system_voice_name"
                ),
            }

            # 准备学生名单（只取名字部分）
            student_names = [name[1] for name in self.final_selected_students]

            # 获取语音引擎类型
            voice_engine = readme_settings_async("basic_voice_settings", "voice_engine")
            engine_type = 1 if voice_engine == "Edge TTS" else 0

            # 获取Edge TTS语音名称
            edge_tts_voice_name = readme_settings_async(
                "basic_voice_settings", "edge_tts_voice_name"
            )

            # 调用语音播放
            self.tts_handler.voice_play(
                config=voice_settings,
                student_names=student_names,
                engine_type=engine_type,
                voice_name=edge_tts_voice_name,
                class_name=self.list_combobox.currentText(),
            )
        except Exception as e:
            logger.error(f"播放语音失败: {e}", exc_info=True)

    def animate_result(self):
        """动画过程中更新显示"""
        self.draw_random()

    def draw_random(self):
        """抽取随机结果"""
        class_name = self.list_combobox.currentText()
        group_index = self.range_combobox.currentIndex()
        group_filter = self.range_combobox.currentText()
        gender_index = self.gender_combobox.currentIndex()
        gender_filter = self.gender_combobox.currentText()

        half_repeat = readme_settings_async("roll_call_settings", "half_repeat")

        # 使用工具类抽取随机学生
        result = RollCallUtils.draw_random_students(
            class_name,
            group_index,
            group_filter,
            gender_index,
            gender_filter,
            self.current_count,
            half_repeat,
        )

        # 处理需要重置的情况
        if "reset_required" in result and result["reset_required"]:
            RollCallUtils.reset_drawn_records(
                self, class_name, gender_filter, group_filter
            )
            return

        self.final_selected_students = result["selected_students"]
        self.final_class_name = result["class_name"]
        self.final_selected_students_dict = result["selected_students_dict"]
        self.final_group_filter = result["group_filter"]
        self.final_gender_filter = result["gender_filter"]

        self.display_result(result["selected_students"], result["class_name"])

        # 检查是否启用了通知服务
        call_notification_service = readme_settings_async(
            "roll_call_notification_settings", "call_notification_service"
        )
        if call_notification_service:
            # 准备通知设置
            settings = RollCallUtils.prepare_notification_settings()

            # 使用ResultDisplayUtils显示通知
            ResultDisplayUtils.show_notification_if_enabled(
                self.final_class_name,
                self.final_selected_students,
                self.current_count,
                settings,
                settings_group="roll_call_notification_settings",
            )

    def display_result(self, selected_students, class_name, display_settings=None):
        """显示抽取结果

        Args:
            selected_students: 选中的学生列表
            class_name: 班级名称
            display_settings: 显示设置字典，如果提供则使用这些设置，否则使用默认的点名设置
        """
        group_index = self.range_combobox.currentIndex()

        # 如果提供了显示设置，则使用这些设置，否则使用默认的点名设置
        if display_settings:
            font_size = display_settings.get(
                "font_size", get_safe_font_size("roll_call_settings", "font_size")
            )
            animation_color = display_settings.get(
                "animation_color_theme",
                readme_settings_async("roll_call_settings", "animation_color_theme"),
            )
            display_format = display_settings.get(
                "display_format",
                readme_settings_async("roll_call_settings", "display_format"),
            )
            show_student_image = display_settings.get(
                "student_image",
                readme_settings_async("roll_call_settings", "student_image"),
            )
            show_random = display_settings.get(
                "show_random",
                readme_settings_async("roll_call_settings", "show_random"),
            )
            settings_group = "quick_draw_settings"
        else:
            font_size = get_safe_font_size("roll_call_settings", "font_size")
            animation_color = readme_settings_async(
                "roll_call_settings", "animation_color_theme"
            )
            display_format = readme_settings_async(
                "roll_call_settings", "display_format"
            )
            show_student_image = readme_settings_async(
                "roll_call_settings", "student_image"
            )
            show_random = readme_settings_async("roll_call_settings", "show_random")
            settings_group = "roll_call_settings"

        student_labels = ResultDisplayUtils.create_student_label(
            class_name=class_name,
            selected_students=selected_students,
            draw_count=self.current_count,
            font_size=font_size,
            animation_color=animation_color,
            display_format=display_format,
            show_student_image=show_student_image,
            group_index=group_index,
            show_random=show_random,
            settings_group=settings_group,
        )
        ResultDisplayUtils.display_results_in_grid(self.result_grid, student_labels)

    def reset_count(self):
        """重置人数"""
        self.current_count = 1
        self.count_label.setText("1")
        self.minus_button.setEnabled(False)
        self.plus_button.setEnabled(True)
        class_name = self.list_combobox.currentText()
        gender = self.gender_combobox.currentText()
        group = self.range_combobox.currentText()
        RollCallUtils.reset_drawn_records(self, class_name, gender, group)
        self.clear_result()
        self.update_many_count_label()

        # 更新剩余名单窗口
        if (
            hasattr(self, "remaining_list_page")
            and self.remaining_list_page is not None
        ):
            QTimer.singleShot(APP_INIT_DELAY, self._update_remaining_list_delayed)

        if (
            hasattr(self, "remaining_list_page")
            and self.remaining_list_page is not None
            and hasattr(self.remaining_list_page, "count_changed")
        ):
            self.remaining_list_page.count_changed.emit(self.remaining_count)

    def clear_result(self):
        """清空结果显示"""
        ResultDisplayUtils.clear_grid(self.result_grid)

    def update_count(self, change):
        """更新人数

        Args:
            change (int): 变化量，正数表示增加，负数表示减少
        """
        try:
            self.total_count = RollCallUtils.get_total_count(
                self.list_combobox.currentText(),
                self.range_combobox.currentIndex(),
                self.range_combobox.currentText(),
            )
            self.current_count = max(1, int(self.count_label.text()) + change)
            self.count_label.setText(str(self.current_count))
            self.minus_button.setEnabled(self.current_count > 1)
            self.plus_button.setEnabled(self.current_count < self.total_count)
        except (ValueError, TypeError):
            self.count_label.setText("1")
            self.minus_button.setEnabled(False)
            self.plus_button.setEnabled(True)

    def get_total_count(self):
        """获取总人数"""
        return RollCallUtils.get_total_count(
            self.list_combobox.currentText(),
            self.range_combobox.currentIndex(),
            self.range_combobox.currentText(),
        )

    def update_many_count_label(self):
        """更新多数量显示标签"""
        total_count, remaining_count, formatted_text = (
            RollCallUtils.update_many_count_label_text(
                self.list_combobox.currentText(),
                self.range_combobox.currentIndex(),
                self.range_combobox.currentText(),
                self.gender_combobox.currentText(),
                readme_settings_async("roll_call_settings", "half_repeat"),
            )
        )

        self.remaining_count = remaining_count
        self.many_count_label.setText(formatted_text)

        # 根据总人数是否为0，启用或禁用开始按钮
        RollCallUtils.update_start_button_state(self.start_button, total_count)

    def update_remaining_list_window(self):
        """更新剩余名单窗口的内容"""
        if (
            hasattr(self, "remaining_list_page")
            and self.remaining_list_page is not None
        ):
            try:
                class_name = self.list_combobox.currentText()
                group_filter = self.range_combobox.currentText()
                gender_filter = self.gender_combobox.currentText()
                group_index = self.range_combobox.currentIndex()
                gender_index = self.gender_combobox.currentIndex()
                half_repeat = readme_settings_async("roll_call_settings", "half_repeat")

                # 更新剩余名单页面内容
                if hasattr(self.remaining_list_page, "update_remaining_list"):
                    self.remaining_list_page.update_remaining_list(
                        class_name,
                        group_filter,
                        gender_filter,
                        half_repeat,
                        group_index,
                        gender_index,
                        emit_signal=False,  # 不发出信号，避免循环更新
                        source="roll_call",
                    )
            except Exception as e:
                logger.error(f"更新剩余名单窗口内容失败: {e}")

    def show_remaining_list(self):
        """显示剩余名单窗口"""
        # 如果窗口已存在，则激活该窗口并更新内容
        if (
            hasattr(self, "remaining_list_page")
            and self.remaining_list_page is not None
        ):
            try:
                # 获取窗口实例
                window = self.remaining_list_page.window()
                if window is not None:
                    # 激活窗口并置于前台
                    window.raise_()
                    window.activateWindow()
                    # 更新窗口内容
                    self.update_remaining_list_window()
                    return
            except Exception as e:
                logger.error(f"激活剩余名单窗口失败: {e}")
                # 如果激活失败，继续创建新窗口

        # 创建新窗口
        class_name = self.list_combobox.currentText()
        group_filter = self.range_combobox.currentText()
        gender_filter = self.gender_combobox.currentText()
        group_index = self.range_combobox.currentIndex()
        gender_index = self.gender_combobox.currentIndex()
        half_repeat = readme_settings_async("roll_call_settings", "half_repeat")

        window, get_page = create_remaining_list_window(
            class_name,
            group_filter,
            gender_filter,
            half_repeat,
            group_index,
            gender_index,
            "roll_call",
        )

        def on_page_ready(page):
            self.remaining_list_page = page

            if page and hasattr(page, "count_changed"):
                page.count_changed.connect(self.update_many_count_label)
                self.update_many_count_label()

        get_page(on_page_ready)

        window.windowClosed.connect(lambda: setattr(self, "remaining_list_page", None))

        window.show()

    def setup_file_watcher(self):
        """设置文件监控器，监控名单文件夹的变化"""
        try:
            list_dir = get_data_path("list", "roll_call_list")

            if not list_dir.exists():
                list_dir.mkdir(parents=True, exist_ok=True)

            self.file_watcher.addPath(str(list_dir))

            self.file_watcher.directoryChanged.connect(self.on_directory_changed)
            self.file_watcher.fileChanged.connect(self.on_file_changed)

        except Exception as e:
            logger.error(f"设置文件监控器失败: {e}")

    def on_directory_changed(self, path):
        """当文件夹内容发生变化时触发"""
        try:
            QTimer.singleShot(500, self.refresh_class_list)
        except Exception as e:
            logger.error(f"处理文件夹变化事件失败: {e}")

    def on_file_changed(self, path):
        """当文件内容发生变化时触发"""
        try:
            QTimer.singleShot(500, self.refresh_class_list)
        except Exception as e:
            logger.error(f"处理文件变化事件失败: {e}")

    def refresh_class_list(self):
        """刷新班级列表下拉框"""
        try:
            current_class = self.list_combobox.currentText()

            new_class_list = get_class_name_list()

            self.list_combobox.blockSignals(True)

            self.list_combobox.clear()
            self.list_combobox.addItems(new_class_list)

            if current_class in new_class_list:
                index = self.list_combobox.findText(current_class)
                if index >= 0:
                    self.list_combobox.setCurrentIndex(index)
            elif new_class_list:
                self.list_combobox.setCurrentIndex(0)

            self.list_combobox.blockSignals(False)

            self.on_class_changed()

        except Exception as e:
            logger.error(f"刷新班级列表失败: {e}")

    def populate_lists(self):
        """在后台填充班级/范围/性别下拉框并更新人数统计"""
        try:
            # 填充班级列表
            class_list = get_class_name_list()
            self.list_combobox.blockSignals(True)
            self.list_combobox.clear()
            if class_list:
                self.list_combobox.addItems(class_list)
                self.list_combobox.setCurrentIndex(0)
            self.list_combobox.blockSignals(False)

            # 填充范围和性别选项
            self.range_combobox.blockSignals(True)
            self.range_combobox.clear()

            # 获取基础选项
            base_options = get_content_combo_name_async("roll_call", "range_combobox")

            # 获取小组列表
            group_list = get_group_list(self.list_combobox.currentText())

            # 如果有小组，才添加"抽取全部小组"选项
            if group_list:
                # 添加基础选项和小组列表
                self.range_combobox.addItems(base_options + group_list)
            else:
                # 只添加基础选项，跳过"抽取全部小组"
                self.range_combobox.addItems(base_options[:1])  # 只添加"抽取全部学生"

            self.range_combobox.blockSignals(False)

            self.gender_combobox.blockSignals(True)
            self.gender_combobox.clear()
            self.gender_combobox.addItems(
                get_content_combo_name_async("roll_call", "gender_combobox")
                + get_gender_list(self.list_combobox.currentText())
            )
            self.gender_combobox.blockSignals(False)

            # 使用工具函数更新标签文本
            total_count, remaining_count, formatted_text = (
                RollCallUtils.update_many_count_label_text(
                    self.list_combobox.currentText(),
                    self.range_combobox.currentIndex(),
                    self.range_combobox.currentText(),
                    self.gender_combobox.currentText(),
                    readme_settings("roll_call_settings", "half_repeat"),
                )
            )

            self.remaining_count = remaining_count
            self.many_count_label.setText(formatted_text)

            # 根据总人数是否为0，启用或禁用开始按钮
            RollCallUtils.update_start_button_state(self.start_button, total_count)

            # 重新调整控件宽度以适应下拉框内容
            self._adjustControlWidgetWidths()

        except Exception as e:
            logger.error(f"延迟填充列表失败: {e}")

    def setupSettingsListener(self):
        """设置设置监听器，监听页面管理设置变化"""
        from app.tools.settings_access import get_settings_signals

        settings_signals = get_settings_signals()
        settings_signals.settingChanged.connect(self.onSettingsChanged)

    def onSettingsChanged(self, first_level_key, second_level_key, value):
        """当设置发生变化时的处理函数"""
        # 只处理页面管理相关的设置变化
        if first_level_key == "page_management" and second_level_key.startswith(
            "roll_call"
        ):
            # 直接更新UI
            self.updateUI()
            # 发出信号让父组件处理
            self.settingsChanged.emit()

    def updateUI(self):
        """更新UI控件的可见性"""
        # 清除现有布局中的控件
        self.clearLayout(self.control_layout)

        # 根据页面管理设置决定是否添加控件
        self.add_control_widget_if_enabled(
            self.control_layout,
            self.reset_button,
            "page_management",
            "roll_call_reset_button",
        )

        self.add_control_widget_if_enabled(
            self.control_layout,
            self.count_widget,
            "page_management",
            "roll_call_quantity_control",
        )

        self.add_control_widget_if_enabled(
            self.control_layout,
            self.start_button,
            "page_management",
            "roll_call_start_button",
        )

        self.add_control_widget_if_enabled(
            self.control_layout, self.list_combobox, "page_management", "roll_call_list"
        )

        self.add_control_widget_if_enabled(
            self.control_layout,
            self.range_combobox,
            "page_management",
            "roll_call_range",
        )

        self.add_control_widget_if_enabled(
            self.control_layout,
            self.gender_combobox,
            "page_management",
            "roll_call_gender",
        )

        self.add_control_widget_if_enabled(
            self.control_layout,
            self.remaining_button,
            "page_management",
            "roll_call_remaining_button",
        )

        self.add_control_widget_if_enabled(
            self.control_layout,
            self.many_count_label,
            "page_management",
            "roll_call_quantity_label",
        )

    def clearLayout(self, layout):
        """清除布局中的所有控件"""
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().setParent(None)

    def _set_widget_font(self, widget, font_size):
        """为控件设置字体"""
        # 确保字体大小有效
        try:
            # 确保font_size是有效的整数
            if not isinstance(font_size, (int, float)):
                font_size = int(font_size) if str(font_size).isdigit() else 12

            font_size = int(font_size)
            if font_size <= 0:
                font_size = 12  # 使用默认字体大小

            custom_font = load_custom_font()
            if custom_font:
                widget.setFont(QFont(custom_font, font_size))
        except (ValueError, TypeError) as e:
            logger.warning(f"设置字体大小失败，使用默认值: {e}")
            # 使用默认字体大小
            custom_font = load_custom_font()
            if custom_font:
                widget.setFont(QFont(custom_font, 12))
