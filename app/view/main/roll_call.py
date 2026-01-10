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
from app.common.music.music_player import music_player
from app.common.extraction.extract import _is_non_class_time
from app.common.safety.verify_ops import require_and_run

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

        self.press_timer = QTimer()
        self.press_timer.timeout.connect(self.handle_long_press)
        self.long_press_interval = 100
        self.long_press_delay = 500
        self.is_long_pressing = False
        self.long_press_direction = 0

        self.tts_handler = TTSHandler()

        self.is_animating = False

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
        self.result_layout.addLayout(self.result_grid)
        roll_call_container.addWidget(self.result_widget)

        self.reset_button = self._create_button(
            "roll_call", "reset_button", 15, self.reset_count
        )

        self.minus_button, self.plus_button, self.count_widget = (
            self._create_count_control_widget()
        )

        self.start_button = self._create_button(
            "roll_call", "start_button", 15, self.start_draw, is_primary=True
        )

        self.list_combobox = self._create_combobox(
            "roll_call", "default_empty_item", 12, self.on_class_changed
        )

        self.range_combobox = self._create_combobox(
            "roll_call", None, 12, self.on_filter_changed
        )

        self.gender_combobox = self._create_combobox(
            "roll_call", None, 12, self.on_filter_changed
        )

        self.remaining_button = self._create_button(
            "roll_call", "remaining_button", 12, self.show_remaining_list
        )

        self.total_count = 0
        self.remaining_count = 0

        text_template = get_any_position_value(
            "roll_call", "many_count_label", "text_0"
        )
        formatted_text = text_template.format(total_count=0, remaining_count=0)
        self.many_count_label = BodyLabel(formatted_text)
        self.many_count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._set_widget_font(self.many_count_label, 10)

        self.control_widget = QWidget()
        self.control_layout = QVBoxLayout(self.control_widget)
        self.control_layout.setContentsMargins(0, 0, 0, 0)
        self.control_layout.addStretch()

        self._add_control_widgets()

        scroll = SmoothScrollArea()
        scroll.setWidget(container)
        scroll.setWidgetResizable(True)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        roll_call_method = readme_settings_async("page_management", "roll_call_method")

        if roll_call_method == 0:
            main_layout.addWidget(self.control_widget)
            main_layout.addWidget(scroll, 1)
        else:
            main_layout.addWidget(scroll, 1)
            main_layout.addWidget(self.control_widget)

        self._adjustControlWidgetWidths()

        QTimer.singleShot(0, self.populate_lists)

    def _create_button(
        self, content_key, button_key, font_size, callback, is_primary=False
    ):
        """创建按钮

        Args:
            content_key: 内容键
            button_key: 按钮键
            font_size: 字体大小
            callback: 回调函数
            is_primary: 是否为主按钮

        Returns:
            创建的按钮
        """
        if is_primary:
            button = PrimaryPushButton(
                get_content_pushbutton_name_async(content_key, button_key)
            )
        else:
            button = PushButton(
                get_content_pushbutton_name_async(content_key, button_key)
            )
        self._set_widget_font(button, font_size)
        button.setFixedHeight(45)
        button.clicked.connect(lambda: callback())
        return button

    def _create_combobox(self, content_key, placeholder_key, font_size, callback):
        """创建下拉框

        Args:
            content_key: 内容键
            placeholder_key: 占位符键
            font_size: 字体大小
            callback: 回调函数

        Returns:
            创建的下拉框
        """
        combobox = ComboBox()
        self._set_widget_font(combobox, font_size)
        combobox.setFixedHeight(45)
        if placeholder_key:
            combobox.setPlaceholderText(
                get_content_name_async(content_key, placeholder_key)
            )
        combobox.currentTextChanged.connect(callback)
        return combobox

    def _create_count_control_widget(self):
        """创建计数控制控件

        Returns:
            tuple: (minus_button, plus_button, count_widget)
        """
        minus_button = self._create_button_with_long_press("-", 20, -1)
        plus_button = self._create_button_with_long_press("+", 20, 1)

        minus_button.setEnabled(False)
        plus_button.setEnabled(True)

        self.count_label = BodyLabel("1")
        self.count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._set_widget_font(self.count_label, 20)
        self.count_label.setFixedSize(65, 45)
        self.current_count = 1

        count_widget = QWidget()
        horizontal_layout = QHBoxLayout()
        horizontal_layout.setContentsMargins(0, 0, 0, 0)
        horizontal_layout.setSpacing(0)
        horizontal_layout.addWidget(minus_button)
        horizontal_layout.addStretch()
        horizontal_layout.addWidget(self.count_label)
        horizontal_layout.addStretch()
        horizontal_layout.addWidget(plus_button)
        count_widget.setLayout(horizontal_layout)

        return minus_button, plus_button, count_widget

    def _create_button_with_long_press(self, text, font_size, direction):
        """创建带长按功能的按钮

        Args:
            text: 按钮文本
            font_size: 字体大小
            direction: 长按方向（1为增加，-1为减少）

        Returns:
            创建的按钮
        """
        button = PushButton(text)
        self._set_widget_font(button, font_size)
        button.setFixedSize(45, 45)
        button.clicked.connect(lambda: self.update_count(direction))
        button.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)

        button.mousePressEvent = lambda event: self._custom_mouse_press_event(
            button, event
        )
        button.mouseReleaseEvent = lambda event: self._custom_mouse_release_event(
            button, event
        )

        button.pressed.connect(lambda: self.start_long_press(direction))
        button.released.connect(self.stop_long_press)

        return button

    def _custom_mouse_press_event(self, widget, event):
        """自定义鼠标按下事件，将右键转换为左键

        Args:
            widget: 控件
            event: 鼠标事件
        """
        if event.button() == Qt.MouseButton.RightButton:
            new_event = QMouseEvent(
                QEvent.Type.MouseButtonPress,
                event.position(),
                Qt.MouseButton.LeftButton,
                Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier,
            )
            QApplication.sendEvent(widget, new_event)
        else:
            PushButton.mousePressEvent(widget, event)

    def _custom_mouse_release_event(self, widget, event):
        """自定义鼠标释放事件，将右键转换为左键

        Args:
            widget: 控件
            event: 鼠标事件
        """
        if event.button() == Qt.MouseButton.RightButton:
            new_event = QMouseEvent(
                QEvent.Type.MouseButtonRelease,
                event.position(),
                Qt.MouseButton.LeftButton,
                Qt.MouseButton.NoButton,
                Qt.KeyboardModifier.NoModifier,
            )
            QApplication.sendEvent(widget, new_event)
        else:
            PushButton.mouseReleaseEvent(widget, event)

    def _add_control_widgets(self):
        """添加控制控件到布局"""
        widgets_config = [
            (self.reset_button, "page_management", "roll_call_reset_button"),
            (self.count_widget, "page_management", "roll_call_quantity_control"),
            (self.start_button, "page_management", "roll_call_start_button"),
            (self.list_combobox, "page_management", "roll_call_list"),
            (self.range_combobox, "page_management", "roll_call_range"),
            (self.gender_combobox, "page_management", "roll_call_gender"),
            (self.remaining_button, "page_management", "roll_call_remaining_button"),
            (self.many_count_label, "page_management", "roll_call_quantity_label"),
        ]

        for widget, settings_group, setting_name in widgets_config:
            self.add_control_widget_if_enabled(
                self.control_layout, widget, settings_group, setting_name
            )

    def add_control_widget_if_enabled(
        self, layout, widget, settings_group, setting_name
    ):
        """根据设置决定是否添加控件到布局"""
        try:
            # 对于数量标签，需要特殊处理显示模式
            if setting_name in ["roll_call_quantity_label", "lottery_quantity_label"]:
                display_mode = readme_settings_async(settings_group, setting_name)
                # display_mode == 3 表示不显示
                if display_mode != 3:
                    layout.addWidget(widget, alignment=Qt.AlignmentFlag.AlignCenter)
            else:
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
            min_width = 200  # 最小宽度
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

    def _do_start_draw(self):
        """实际执行开始抽取的逻辑"""
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

        animation_music = readme_settings_async("roll_call_settings", "animation_music")
        if animation_music:
            music_player.play_music(
                music_file=animation_music,
                settings_group="roll_call_settings",
                loop=True,
                fade_in=True,
            )

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
            self.stop_animation()
            self.start_button.clicked.connect(lambda: self.start_draw())

    def start_draw(self):
        """开始抽取"""
        # 检查当前时间是否在非上课时间段内
        if _is_non_class_time():
            # 检查是否需要验证流程
            if readme_settings_async("course_settings", "verification_required"):
                # 如果需要验证流程，弹出密码验证窗口
                logger.info("当前时间在非上课时间段内，需要密码验证")
                require_and_run("roll_call_start", self, self._do_start_draw)
            else:
                # 如果不需要验证流程，直接禁止点击
                logger.info("当前时间在非上课时间段内，禁止抽取")
                return
        else:
            # 如果不在非上课时间段内，直接执行抽取
            self._do_start_draw()

    def stop_animation(self):
        """停止动画"""
        is_quick_draw = hasattr(self, "is_quick_draw") and self.is_quick_draw

        if hasattr(self, "animation_timer") and self.animation_timer.isActive():
            self.animation_timer.stop()
        self.start_button.setText(
            get_content_pushbutton_name_async("roll_call", "start_button")
        )
        self.is_animating = False

        from app.common.behind_scenes.behind_scenes_utils import BehindScenesUtils

        BehindScenesUtils.clear_cache()

        try:
            self.start_button.clicked.disconnect()
        except Exception as e:
            logger.exception(
                "Error disconnecting start_button clicked during stop_animation (ignored): {}",
                e,
            )
        self.start_button.clicked.connect(lambda: self.start_draw())

        half_repeat = readme_settings_async("roll_call_settings", "half_repeat")
        RollCallUtils.record_drawn_students(
            class_name=self.final_class_name,
            selected_students=self.final_selected_students,
            selected_students_dict=self.final_selected_students_dict,
            gender_filter=self.final_gender_filter,
            group_filter=self.final_group_filter,
            half_repeat=half_repeat,
        )

        if half_repeat > 0:
            self.update_many_count_label()

            if (
                hasattr(self, "remaining_list_page")
                and self.remaining_list_page is not None
                and hasattr(self.remaining_list_page, "count_changed")
            ):
                self.remaining_list_page.count_changed.emit(self.remaining_count)

            QTimer.singleShot(APP_INIT_DELAY, self._update_remaining_list_delayed)

        if hasattr(self, "final_selected_students"):
            if not is_quick_draw:
                self.display_result(self.final_selected_students, self.final_class_name)
                RollCallUtils.show_notification_if_enabled(
                    class_name=self.final_class_name,
                    selected_students=self.final_selected_students,
                    draw_count=self.current_count,
                    settings_group="roll_call_notification_settings",
                )

            self.play_voice_result()

            music_player.stop_music(fade_out=True)

            result_music = readme_settings_async("roll_call_settings", "result_music")
            if result_music:
                music_player.play_music(
                    music_file=result_music,
                    settings_group="roll_call_settings",
                    loop=False,
                    fade_in=True,
                )

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

        result = RollCallUtils.draw_random_students(
            class_name,
            group_index,
            group_filter,
            gender_index,
            gender_filter,
            self.current_count,
            half_repeat,
        )

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

        if self.is_animating:
            self.display_result_animated(
                result["selected_students"], result["class_name"]
            )
        else:
            self.display_result(result["selected_students"], result["class_name"])

        # 检查是否启用了通知服务
        call_notification_service = readme_settings_async(
            "roll_call_notification_settings", "call_notification_service"
        )
        # 检查是否启用了最大浮窗通知人数功能
        use_main_window_when_exceed_threshold = readme_settings_async(
            "roll_call_notification_settings", "use_main_window_when_exceed_threshold"
        )
        # 检查人数是否超过最大浮窗通知人数
        max_notify_count = readme_settings_async(
            "roll_call_notification_settings", "main_window_display_threshold"
        )
        if call_notification_service:
            # 准备通知设置
            settings = RollCallUtils.prepare_notification_settings()
            # 只有当没有启用阈值功能，或者启用了但抽取人数没有超过阈值时，才显示通知
            if use_main_window_when_exceed_threshold:
                # 如果启用了阈值功能，检查抽取人数是否超过阈值
                if self.current_count <= max_notify_count:
                    # 使用ResultDisplayUtils显示通知
                    ResultDisplayUtils.show_notification_if_enabled(
                        self.final_class_name,
                        self.final_selected_students,
                        self.current_count,
                        settings,
                        settings_group="roll_call_notification_settings",
                    )
            else:
                # 如果没有启用阈值功能，直接显示通知
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
        settings_group = (
            "quick_draw_settings" if display_settings else "roll_call_settings"
        )

        RollCallUtils.display_result(
            result_grid=self.result_grid,
            class_name=class_name,
            selected_students=selected_students,
            draw_count=self.current_count,
            group_index=group_index,
            settings_group=settings_group,
            display_settings=display_settings,
        )

    def display_result_animated(self, selected_students, class_name):
        """动画过程中显示结果

        Args:
            selected_students: 选中的学生列表
            class_name: 班级名称
        """
        group_index = self.range_combobox.currentIndex()
        display_dict = RollCallUtils.create_display_settings("roll_call_settings")

        student_labels = ResultDisplayUtils.create_student_label(
            class_name=class_name,
            selected_students=selected_students,
            draw_count=self.current_count,
            font_size=display_dict["font_size"],
            animation_color=display_dict["animation_color_theme"],
            display_format=display_dict["display_format"],
            show_student_image=display_dict["student_image"],
            group_index=group_index,
            show_random=display_dict["show_random"],
            settings_group="roll_call_settings",
        )

        ResultDisplayUtils.display_results_in_grid(self.result_grid, student_labels)

    def _do_reset_count(self):
        """实际执行重置人数的逻辑"""
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

    def reset_count(self):
        """重置人数"""
        # 检查当前时间是否在非上课时间段内
        if _is_non_class_time():
            # 检查是否需要验证流程
            if readme_settings_async("course_settings", "verification_required"):
                # 如果需要验证流程，弹出密码验证窗口
                logger.info("当前时间在非上课时间段内，需要密码验证")
                require_and_run("roll_call_reset", self, self._do_reset_count)
            else:
                # 如果不需要验证流程，直接禁止点击
                logger.info("当前时间在非上课时间段内，禁止重置")
                return
        else:
            # 如果不在非上课时间段内，直接执行重置
            self._do_reset_count()

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
            self._populate_class_list()
            self._populate_range_combobox()
            self._populate_gender_combobox()
            self._update_count_label()
            self._adjustControlWidgetWidths()

        except Exception as e:
            logger.error(f"延迟填充列表失败: {e}")

    def _populate_class_list(self):
        """填充班级列表"""
        class_list = get_class_name_list()
        self.list_combobox.blockSignals(True)
        self.list_combobox.clear()
        if class_list:
            self.list_combobox.addItems(class_list)
            default_class = readme_settings_async("roll_call_settings", "default_class")
            if default_class and default_class in class_list:
                index = class_list.index(default_class)
                self.list_combobox.setCurrentIndex(index)
                logger.debug(f"应用默认抽取名单: {default_class}")
            else:
                self.list_combobox.setCurrentIndex(0)
        self.list_combobox.blockSignals(False)

    def _populate_range_combobox(self):
        """填充范围下拉框"""
        self.range_combobox.blockSignals(True)
        self.range_combobox.clear()

        base_options = get_content_combo_name_async("roll_call", "range_combobox")
        group_list = get_group_list(self.list_combobox.currentText())

        if group_list:
            self.range_combobox.addItems(base_options + group_list)
        else:
            self.range_combobox.addItems(base_options[:1])

        self.range_combobox.blockSignals(False)

    def _populate_gender_combobox(self):
        """填充性别下拉框"""
        self.gender_combobox.blockSignals(True)
        self.gender_combobox.clear()
        self.gender_combobox.addItems(
            get_content_combo_name_async("roll_call", "gender_combobox")
            + get_gender_list(self.list_combobox.currentText())
        )
        self.gender_combobox.blockSignals(False)

    def _update_count_label(self):
        """更新人数统计标签"""
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
        RollCallUtils.update_start_button_state(self.start_button, total_count)

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

    def eventFilter(self, obj, event):
        """事件过滤器，处理触屏长按事件"""
        if obj in (self.minus_button, self.plus_button):
            if event.type() == QEvent.Type.MouseButtonPress:
                # 处理左/右键点击，确保长按功能正常
                return super().eventFilter(obj, event)
            # 其他事件正常处理
        return super().eventFilter(obj, event)

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
