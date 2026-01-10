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
from app.common.lottery.lottery_utils import LotteryUtils
from app.tools.variable import *
from app.common.voice.voice import TTSHandler
from app.common.music.music_player import music_player
from app.common.extraction.extract import _is_non_class_time
from app.common.safety.verify_ops import require_and_run

from app.page_building.another_window import *

from random import SystemRandom

system_random = SystemRandom()


# ==================================================
# 奖池点名类
# ==================================================
class Lottery(QWidget):
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
        lottery_container = QVBoxLayout(container)
        lottery_container.setContentsMargins(0, 0, 0, 0)

        self.result_widget = QWidget()
        self.result_layout = QVBoxLayout(self.result_widget)
        self.result_grid = QGridLayout()
        # 移除拉伸，让内容可以自由扩展，确保滚动正常
        self.result_layout.addLayout(self.result_grid)
        lottery_container.addWidget(self.result_widget)

        self.reset_button = PushButton(
            get_content_pushbutton_name_async("lottery", "reset_button")
        )
        self._set_widget_font(self.reset_button, 15)
        self.reset_button.setFixedHeight(45)
        self.reset_button.clicked.connect(lambda: self.reset_count())

        # 自定义的鼠标事件处理方法，将右键事件转换为左键事件
        def custom_mouse_press_event(widget, event):
            if event.button() == Qt.MouseButton.RightButton:
                # 将右键按下事件转换为左键按下事件
                new_event = QMouseEvent(
                    QEvent.Type.MouseButtonPress,
                    event.position(),
                    Qt.MouseButton.LeftButton,
                    Qt.MouseButton.LeftButton,
                    Qt.KeyboardModifier.NoModifier,
                )
                QApplication.sendEvent(widget, new_event)
            else:
                # 其他事件正常处理
                PushButton.mousePressEvent(widget, event)

        def custom_mouse_release_event(widget, event):
            if event.button() == Qt.MouseButton.RightButton:
                # 将右键释放事件转换为左键释放事件
                new_event = QMouseEvent(
                    QEvent.Type.MouseButtonRelease,
                    event.position(),
                    Qt.MouseButton.LeftButton,
                    Qt.MouseButton.NoButton,
                    Qt.KeyboardModifier.NoModifier,
                )
                QApplication.sendEvent(widget, new_event)
            else:
                # 其他事件正常处理
                PushButton.mouseReleaseEvent(widget, event)

        self.minus_button = PushButton("-")
        self._set_widget_font(self.minus_button, 20)
        self.minus_button.setFixedSize(45, 45)
        self.minus_button.clicked.connect(lambda: self.update_count(-1))
        # 禁用右键菜单，兼容触屏
        self.minus_button.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)

        # 动态替换按钮的鼠标事件处理方法
        original_minus_press = self.minus_button.mousePressEvent
        original_minus_release = self.minus_button.mouseReleaseEvent

        def minus_press_wrapper(event):
            custom_mouse_press_event(self.minus_button, event)

        def minus_release_wrapper(event):
            custom_mouse_release_event(self.minus_button, event)

        self.minus_button.mousePressEvent = minus_press_wrapper
        self.minus_button.mouseReleaseEvent = minus_release_wrapper

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
        # 禁用右键菜单，兼容触屏
        self.plus_button.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)

        # 动态替换按钮的鼠标事件处理方法
        original_plus_press = self.plus_button.mousePressEvent
        original_plus_release = self.plus_button.mouseReleaseEvent

        def plus_press_wrapper(event):
            custom_mouse_press_event(self.plus_button, event)

        def plus_release_wrapper(event):
            custom_mouse_release_event(self.plus_button, event)

        self.plus_button.mousePressEvent = plus_press_wrapper
        self.plus_button.mouseReleaseEvent = plus_release_wrapper

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
            get_content_pushbutton_name_async("lottery", "start_button")
        )
        self._set_widget_font(self.start_button, 15)
        self.start_button.setFixedHeight(45)
        self.start_button.clicked.connect(lambda: self.start_draw())

        self.pool_list_combobox = ComboBox()
        self._set_widget_font(self.pool_list_combobox, 12)
        self.pool_list_combobox.setFixedHeight(45)
        self.pool_list_combobox.setPlaceholderText(
            get_content_name_async("lottery", "default_empty_item")
        )
        # 延迟填充奖池列表，避免启动时进行文件IO
        self.pool_list_combobox.currentTextChanged.connect(self.on_pool_changed)

        self.list_combobox = ComboBox()
        self._set_widget_font(self.list_combobox, 12)
        self.list_combobox.setFixedHeight(45)
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
            get_content_pushbutton_name_async("lottery", "remaining_button")
        )
        self._set_widget_font(self.remaining_button, 12)
        self.remaining_button.setFixedHeight(45)
        self.remaining_button.clicked.connect(lambda: self.show_remaining_list())

        # 初始时不进行昂贵的数据加载，改为延迟填充
        self.total_count = 0
        self.remaining_count = 0

        text_template = get_any_position_value("lottery", "many_count_label", "text_0")
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
            "lottery_reset_button",
        )

        self.add_control_widget_if_enabled(
            self.control_layout,
            self.count_widget,
            "page_management",
            "lottery_quantity_control",
        )

        self.add_control_widget_if_enabled(
            self.control_layout,
            self.start_button,
            "page_management",
            "lottery_start_button",
        )

        self.add_control_widget_if_enabled(
            self.control_layout,
            self.pool_list_combobox,
            "page_management",
            "lottery_list",
        )

        self.add_control_widget_if_enabled(
            self.control_layout,
            self.list_combobox,
            "page_management",
            "lottery_roll_call_list",
        )

        self.add_control_widget_if_enabled(
            self.control_layout,
            self.range_combobox,
            "page_management",
            "lottery_roll_call_range",
        )

        self.add_control_widget_if_enabled(
            self.control_layout,
            self.gender_combobox,
            "page_management",
            "lottery_roll_call_gender",
        )

        self.add_control_widget_if_enabled(
            self.control_layout,
            self.remaining_button,
            "page_management",
            "lottery_remaining_button",
        )

        self.add_control_widget_if_enabled(
            self.control_layout,
            self.many_count_label,
            "page_management",
            "lottery_quantity_label",
        )

        scroll = SmoothScrollArea()
        scroll.setWidget(container)
        scroll.setWidgetResizable(True)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 根据页面管理设置决定控制面板位置
        lottery_method = readme_settings_async("page_management", "lottery_method")

        if lottery_method == 0:  # 左侧
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
                self.pool_list_combobox,
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

    def on_pool_changed(self):
        """当奖池选择改变时，更新奖数显示"""
        try:
            self.update_many_count_label()
            total_count = LotteryUtils.get_prize_total_count(
                self.pool_list_combobox.currentText()
            )
            LotteryUtils.update_start_button_state(self.start_button, total_count)

            # 更新剩余名单窗口
            if (
                hasattr(self, "remaining_list_page")
                and self.remaining_list_page is not None
            ):
                QTimer.singleShot(APP_INIT_DELAY, self._update_remaining_list_delayed)
        except Exception as e:
            logger.error(f"切换奖池时发生错误: {e}")

    def on_class_changed(self):
        """当班级选择改变时，更新范围选择、性别选择"""
        self.range_combobox.blockSignals(True)
        self.gender_combobox.blockSignals(True)

        try:
            self.range_combobox.clear()
            list_base_options = get_content_combo_name_async("lottery", "list_combobox")
            selected_text = self.list_combobox.currentText()
            if selected_text in (list_base_options or []):
                self.range_combobox.addItems(
                    get_content_combo_name_async("roll_call", "range_combobox")[:1]
                )
                self.gender_combobox.clear()
                self.gender_combobox.addItems(
                    get_content_combo_name_async("roll_call", "gender_combobox")[:1]
                )
                self.range_combobox.setEnabled(False)
                self.gender_combobox.setEnabled(False)
            else:
                base_options = get_content_combo_name_async(
                    "roll_call", "range_combobox"
                )
                group_list = get_group_list(selected_text)
                if group_list and group_list != [""]:
                    self.range_combobox.addItems(base_options + group_list)
                else:
                    self.range_combobox.addItems(base_options[:1])

                # 性别
                self.gender_combobox.clear()
                gender_options = get_content_combo_name_async(
                    "roll_call", "gender_combobox"
                )
                gender_list = get_gender_list(selected_text)
                if gender_list and gender_list != [""]:
                    self.gender_combobox.addItems(gender_options + gender_list)
                else:
                    self.gender_combobox.addItems(gender_options[:1])
                self.range_combobox.setEnabled(True)
                self.gender_combobox.setEnabled(True)
        except Exception as e:
            logger.error(f"切换班级时发生错误: {e}")
        finally:
            self.range_combobox.blockSignals(False)
            self.gender_combobox.blockSignals(False)

    def on_filter_changed(self):
        """当范围或性别选择改变时，更新奖数显示"""
        try:
            self.update_many_count_label()
            total_count = LotteryUtils.get_prize_total_count(
                self.pool_list_combobox.currentText()
            )
            LotteryUtils.update_start_button_state(self.start_button, total_count)

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
                pool_name = self.pool_list_combobox.currentText()
                group_filter = self.range_combobox.currentText()
                gender_filter = self.gender_combobox.currentText()
                group_index = self.range_combobox.currentIndex()
                gender_index = self.gender_combobox.currentIndex()
                half_repeat = readme_settings_async("lottery_settings", "half_repeat")

                if hasattr(self.remaining_list_page, "update_remaining_list"):
                    self.remaining_list_page.update_remaining_list(
                        pool_name,
                        group_filter,
                        gender_filter,
                        half_repeat,
                        group_index,
                        gender_index,
                        emit_signal=False,
                        source="lottery",
                    )
                else:
                    if hasattr(self.remaining_list_page, "pool_name"):
                        self.remaining_list_page.pool_name = pool_name
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
            get_content_pushbutton_name_async("lottery", "start_button")
        )
        self.start_button.setEnabled(True)
        try:
            self.start_button.clicked.disconnect()
        except Exception as e:
            logger.exception(
                "Error disconnecting start_button clicked (ignored): {}", e
            )

        self.draw_random()
        animation = readme_settings_async("lottery_settings", "animation")
        autoplay_count = readme_settings_async("lottery_settings", "autoplay_count")
        animation_interval = readme_settings_async(
            "lottery_settings", "animation_interval"
        )

        # 获取动画音乐设置
        animation_music = readme_settings_async("lottery_settings", "animation_music")

        if animation == 0:
            # 播放动画音乐
            if animation_music:
                music_player.play_music(
                    music_file=animation_music,
                    settings_group="lottery_settings",
                    loop=True,
                    fade_in=True,
                )

            self.start_button.setText(
                get_content_pushbutton_name_async("lottery", "stop_button")
            )
            self.is_animating = True
            self.animation_timer = QTimer()
            self.animation_timer.timeout.connect(self.animate_result)
            self.animation_timer.start(animation_interval)
            self.start_button.clicked.connect(lambda: self.stop_animation())
        elif animation == 1:
            # 播放动画音乐
            if animation_music:
                music_player.play_music(
                    music_file=animation_music,
                    settings_group="lottery_settings",
                    loop=True,
                    fade_in=True,
                )

            self.animation_count = 0
            self.target_animation_count = autoplay_count
            self.is_animating = True
            self.animation_timer = QTimer()
            self.animation_timer.timeout.connect(self.animate_result)
            self.animation_timer.start(animation_interval)
            self.start_button.setEnabled(False)
            self.start_button.clicked.connect(lambda: self.start_draw())
        elif animation == 2:
            if hasattr(self, "final_selected_students_dict") and hasattr(
                self, "final_pool_name"
            ):
                save_lottery_history(
                    pool_name=self.final_pool_name,
                    selected_students=self.final_selected_students_dict,
                    group_filter=self.final_group_filter,
                    gender_filter=self.final_gender_filter,
                )
            self.start_button.clicked.connect(lambda: self.start_draw())

    def start_draw(self):
        """开始抽取"""
        # 检查当前时间是否在非上课时间段内
        if _is_non_class_time():
            # 检查是否需要验证流程
            if readme_settings_async("course_settings", "verification_required"):
                # 如果需要验证流程，弹出密码验证窗口
                logger.info("当前时间在非上课时间段内，需要密码验证")
                require_and_run("lottery_start", self, self._do_start_draw)
            else:
                # 如果不需要验证流程，直接禁止点击
                logger.info("当前时间在非上课时间段内，禁止抽取")
                return
        else:
            # 如果不在非上课时间段内，直接执行抽取
            self._do_start_draw()

    def stop_animation(self):
        """停止动画"""
        if hasattr(self, "animation_timer") and self.animation_timer.isActive():
            self.animation_timer.stop()
        self.start_button.setText(
            get_content_pushbutton_name_async("lottery", "start_button")
        )
        self.start_button.setEnabled(True)
        self.is_animating = False
        try:
            self.start_button.clicked.disconnect()
        except Exception as e:
            logger.exception(
                "Error disconnecting start_button clicked during stop_animation (ignored): {}",
                e,
            )
        self.start_button.clicked.connect(lambda: self.start_draw())

        # 停止动画音乐
        music_player.stop_music(fade_out=True)

        # 播放结果音乐
        result_music = readme_settings_async("lottery_settings", "result_music")
        if result_music:
            music_player.play_music(
                music_file=result_music,
                settings_group="lottery_settings",
                loop=False,
                fade_in=True,
            )

        half_repeat = readme_settings_async("lottery_settings", "half_repeat")
        if half_repeat > 0:
            record_drawn_prize(
                pool_name=self.final_pool_name,
                prize_names=self.final_selected_students,
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
            self, "final_pool_name"
        ):
            save_lottery_history(
                pool_name=self.final_pool_name,
                selected_students=self.final_selected_students_dict,
                group_filter=self.final_group_filter,
                gender_filter=self.final_gender_filter,
            )

        if hasattr(self, "final_selected_students"):
            self.display_result(self.final_selected_students, self.final_pool_name)

            # 检查是否启用了通知服务
            call_notification_service = readme_settings_async(
                "lottery_notification_settings", "call_notification_service"
            )
            # 检查是否启用了最大浮窗通知奖数功能
            use_main_window_when_exceed_threshold = readme_settings_async(
                "lottery_notification_settings", "use_main_window_when_exceed_threshold"
            )
            # 检查奖数是否超过最大浮窗通知奖数
            max_notify_count = readme_settings_async(
                "lottery_notification_settings", "main_window_display_threshold"
            )
            if call_notification_service:
                # 准备通知设置
                settings = LotteryUtils.prepare_notification_settings()
                # 只有当没有启用阈值功能，或者启用了但抽取奖数没有超过阈值时，才显示通知
                if use_main_window_when_exceed_threshold:
                    # 如果启用了阈值功能，检查抽取奖数是否超过阈值
                    if self.current_count <= max_notify_count:
                        # 使用ResultDisplayUtils显示通知
                        ResultDisplayUtils.show_notification_if_enabled(
                            self.final_pool_name,
                            self.final_selected_students,
                            self.current_count,
                            settings,
                            settings_group="lottery_notification_settings",
                        )
                else:
                    # 如果没有启用阈值功能，直接显示通知
                    ResultDisplayUtils.show_notification_if_enabled(
                        self.final_pool_name,
                        self.final_selected_students,
                        self.current_count,
                        settings,
                        settings_group="lottery_notification_settings",
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

            # 准备奖品名单（只取名字部分）
            prize_names = [prize[1] for prize in self.final_selected_students]

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
                student_names=prize_names,
                engine_type=engine_type,
                voice_name=edge_tts_voice_name,
                class_name=self.pool_list_combobox.currentText(),
            )
        except Exception as e:
            logger.error(f"播放语音失败: {e}", exc_info=True)

    def animate_result(self):
        """动画过程中更新显示"""
        self.draw_random()

    def draw_random(self):
        """抽取随机结果"""
        pool_name = self.pool_list_combobox.currentText()
        group_index = self.range_combobox.currentIndex()
        group_filter = self.range_combobox.currentText()
        gender_index = self.gender_combobox.currentIndex()
        gender_filter = self.gender_combobox.currentText()
        half_repeat = readme_settings_async("lottery_settings", "half_repeat")

        result = LotteryUtils.draw_random_prizes(
            pool_name,
            self.current_count,
        )

        # 处理需要重置的情况
        if "reset_required" in result and result["reset_required"]:
            reset_drawn_prize_record(self, pool_name)
            return

        self.final_selected_students = result.get("selected_prizes") or result.get(
            "selected_students"
        )
        self.final_pool_name = result["pool_name"]
        self.final_selected_students_dict = result.get(
            "selected_prizes_dict"
        ) or result.get("selected_students_dict")
        self.final_group_filter = group_filter
        self.final_gender_filter = gender_filter

        # 根据"跟随学生"模式拼接显示
        try:
            list_base_options = get_content_combo_name_async("lottery", "list_combobox")
        except Exception:
            list_base_options = []
        selected_text = self.list_combobox.currentText()
        if list_base_options and selected_text not in list_base_options:
            try:
                # 获取抽中的奖品列表
                prize_names = [item[1] for item in (self.final_selected_students or [])]

                # 抽取与奖品数量相同的学生（不重复规则由学生设置决定，此处不启用半重复）
                student_result = LotteryUtils.draw_random_students(
                    selected_text,
                    0,
                    "",
                    0,
                    "",
                    len(self.final_selected_students or []),
                    0,
                    pool_name,  # 传入奖池名称，用于应用内幕设置
                    prize_names,  # 传入奖品列表，用于提高指定该奖品的学生的权重
                )
                student_names = [
                    s[1] for s in (student_result.get("selected_students") or [])
                ]
                paired = []
                for i, item in enumerate(self.final_selected_students or []):
                    pid, pname, pexist = item
                    sname = student_names[i] if i < len(student_names) else ""
                    display_name = f"{pname} {sname}" if sname else pname
                    paired.append((pid, display_name, pexist))
                self.final_selected_students = paired
            except Exception as e:
                logger.error(f"奖池跟随学生拼接失败: {e}")

        if self.is_animating:
            self.display_result_animated(
                self.final_selected_students, self.final_pool_name
            )
        else:
            self.display_result(self.final_selected_students, self.final_pool_name)

        # 检查是否启用了通知服务
        call_notification_service = readme_settings_async(
            "lottery_notification_settings", "call_notification_service"
        )
        # 检查是否启用了最大浮窗通知奖数功能
        use_main_window_when_exceed_threshold = readme_settings_async(
            "roll_call_notification_settings", "use_main_window_when_exceed_threshold"
        )
        # 检查奖数是否超过最大浮窗通知奖数
        max_notify_count = readme_settings_async(
            "roll_call_notification_settings", "main_window_display_threshold"
        )
        if call_notification_service:
            # 准备通知设置
            settings = LotteryUtils.prepare_notification_settings()
            if use_main_window_when_exceed_threshold:
                # 如果启用了阈值功能，检查抽取奖数是否超过阈值
                if self.current_count <= max_notify_count:
                    # 使用ResultDisplayUtils显示通知
                    ResultDisplayUtils.show_notification_if_enabled(
                        self.final_pool_name,
                        self.final_selected_students,
                        self.current_count,
                        settings,
                        settings_group="lottery_notification_settings",
                    )
            else:
                # 如果未启用阈值功能，直接显示通知
                ResultDisplayUtils.show_notification_if_enabled(
                    self.final_pool_name,
                    self.final_selected_students,
                    self.current_count,
                    settings,
                    settings_group="lottery_notification_settings",
                )

    def display_result(self, selected_students, pool_name):
        """显示抽取结果"""
        student_labels = ResultDisplayUtils.create_student_label(
            pool_name,
            selected_students=selected_students,
            draw_count=self.current_count,
            font_size=get_safe_font_size("lottery_settings", "font_size"),
            animation_color=readme_settings_async(
                "lottery_settings", "animation_color_theme"
            ),
            display_format=readme_settings_async("lottery_settings", "display_format"),
            show_student_image=readme_settings_async(
                "lottery_settings", "student_image"
            ),
            group_index=0,
            show_random=readme_settings_async("lottery_settings", "show_random"),
            settings_group="lottery_settings",
        )
        ResultDisplayUtils.display_results_in_grid(self.result_grid, student_labels)

    def display_result_animated(self, selected_students, pool_name):
        """动画过程中显示结果

        Args:
            selected_students: 选中的学生列表
            pool_name: 奖池名称
        """
        font_size = get_safe_font_size("lottery_settings", "font_size")
        animation_color = readme_settings_async(
            "lottery_settings", "animation_color_theme"
        )
        display_format = readme_settings_async("lottery_settings", "display_format")
        show_student_image = readme_settings_async("lottery_settings", "student_image")
        show_random = readme_settings_async("lottery_settings", "show_random")

        student_labels = ResultDisplayUtils.create_student_label(
            pool_name=pool_name,
            selected_students=selected_students,
            draw_count=self.current_count,
            font_size=font_size,
            animation_color=animation_color,
            display_format=display_format,
            show_student_image=show_student_image,
            group_index=0,
            show_random=show_random,
            settings_group="lottery_settings",
        )

        ResultDisplayUtils.display_results_in_grid(self.result_grid, student_labels)

    def _do_reset_count(self):
        """实际执行重置奖数的逻辑"""
        self.current_count = 1
        self.count_label.setText("1")
        self.minus_button.setEnabled(False)
        self.plus_button.setEnabled(True)
        pool_name = self.pool_list_combobox.currentText()
        reset_drawn_prize_record(self, pool_name)
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
        """重置奖数"""
        # 检查当前时间是否在非上课时间段内
        if _is_non_class_time():
            # 检查是否需要验证流程
            if readme_settings_async("course_settings", "verification_required"):
                # 如果需要验证流程，弹出密码验证窗口
                logger.info("当前时间在非上课时间段内，需要密码验证")
                require_and_run("lottery_reset", self, self._do_reset_count)
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
        """更新奖数

        Args:
            change (int): 变化量，正数表示增加，负数表示减少
        """
        try:
            self.total_count = LotteryUtils.get_prize_total_count(
                self.pool_list_combobox.currentText()
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
        """获取总奖数"""
        return LotteryUtils.get_prize_total_count(self.pool_list_combobox.currentText())

    def update_many_count_label(self):
        """更新多数量显示标签"""
        total_count, remaining_count, formatted_text = (
            LotteryUtils.update_prize_many_count_label_text(
                self.pool_list_combobox.currentText()
            )
        )

        self.remaining_count = remaining_count
        self.many_count_label.setText(formatted_text)

        # 根据总奖数是否为0，启用或禁用开始按钮
        LotteryUtils.update_start_button_state(self.start_button, total_count)

    def update_remaining_list_window(self):
        """更新剩余名单窗口的内容"""
        if (
            hasattr(self, "remaining_list_page")
            and self.remaining_list_page is not None
        ):
            try:
                pool_name = self.pool_list_combobox.currentText()
                group_filter = self.range_combobox.currentText()
                gender_filter = self.gender_combobox.currentText()
                group_index = self.range_combobox.currentIndex()
                gender_index = self.gender_combobox.currentIndex()
                half_repeat = readme_settings_async("lottery_settings", "half_repeat")

                # 更新剩余名单页面内容
                if hasattr(self.remaining_list_page, "update_remaining_list"):
                    self.remaining_list_page.update_remaining_list(
                        pool_name,
                        group_filter,
                        gender_filter,
                        half_repeat,
                        group_index,
                        gender_index,
                        emit_signal=False,  # 不发出信号，避免循环更新
                        source="lottery",
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
        pool_name = self.pool_list_combobox.currentText()
        group_filter = self.range_combobox.currentText()
        gender_filter = self.gender_combobox.currentText()
        group_index = self.range_combobox.currentIndex()
        gender_index = self.gender_combobox.currentIndex()
        half_repeat = readme_settings_async("lottery_settings", "half_repeat")

        window, get_page = create_remaining_list_window(
            pool_name,
            group_filter,
            gender_filter,
            half_repeat,
            group_index,
            gender_index,
            "lottery",
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
            list_dir = get_data_path("list", "lottery_list")

            if not list_dir.exists():
                list_dir.mkdir(parents=True, exist_ok=True)

            self.file_watcher.addPath(str(list_dir))

            # 初始同步当前文件到监控器，确保文件内容变动也能触发刷新
            self._sync_watcher_files()

            self.file_watcher.directoryChanged.connect(self.on_directory_changed)
            self.file_watcher.fileChanged.connect(self.on_file_changed)

        except Exception as e:
            logger.error(f"设置文件监控器失败: {e}")

    def on_directory_changed(self, path):
        """当文件夹内容发生变化时触发"""
        try:
            # 目录变更后重新同步监控的文件列表
            self._sync_watcher_files()
            QTimer.singleShot(500, self.refresh_pool_list)
        except Exception as e:
            logger.error(f"处理文件夹变化事件失败: {e}")

    def on_file_changed(self, path):
        """当文件内容发生变化时触发"""
        try:
            # 文件内容变化同样刷新下拉框
            QTimer.singleShot(500, self.refresh_pool_list)
        except Exception as e:
            logger.error(f"处理文件变化事件失败: {e}")

    def _sync_watcher_files(self):
        """同步奖池目录下的文件到文件监控器"""
        try:
            # 先移除已监控的文件，避免重复
            files = (
                list(self.file_watcher.files())
                if hasattr(self.file_watcher, "files")
                else []
            )
            if files:
                try:
                    self.file_watcher.removePaths(files)
                except Exception:
                    pass

            # 重新添加当前目录中的所有JSON文件
            lot_dir = get_data_path("list/lottery_list")
            if lot_dir.exists():
                for fp in lot_dir.glob("*.json"):
                    try:
                        self.file_watcher.addPath(str(fp))
                    except Exception:
                        pass
        except Exception as e:
            logger.error(f"同步奖池文件监控失败: {e}")

    def refresh_pool_list(self):
        """刷新奖池列表下拉框"""
        try:
            current_pool = self.pool_list_combobox.currentText()

            new_pool_list = get_pool_name_list()

            self.pool_list_combobox.blockSignals(True)

            self.pool_list_combobox.clear()
            self.pool_list_combobox.addItems(new_pool_list)

            if current_pool in new_pool_list:
                index = self.pool_list_combobox.findText(current_pool)
                if index >= 0:
                    self.pool_list_combobox.setCurrentIndex(index)
            elif new_pool_list:
                self.pool_list_combobox.setCurrentIndex(0)

            self.pool_list_combobox.blockSignals(False)

            self.on_class_changed()

        except Exception as e:
            logger.error(f"刷新奖池列表失败: {e}")

    def populate_lists(self):
        """在后台填充奖池/范围/性别下拉框并更新奖数统计"""
        try:
            # 填充奖池列表
            pool_list = get_pool_name_list()
            self.pool_list_combobox.blockSignals(True)
            self.pool_list_combobox.clear()
            if pool_list:
                self.pool_list_combobox.addItems(pool_list)
                # 应用默认抽取奖池设置
                default_pool = readme_settings_async("lottery_settings", "default_pool")
                if default_pool and default_pool in pool_list:
                    # 设置默认抽取奖池
                    index = pool_list.index(default_pool)
                    self.pool_list_combobox.setCurrentIndex(index)
                    logger.debug(f"应用默认抽取奖池: {default_pool}")
                else:
                    self.list_combobox.setCurrentIndex(0)
            self.pool_list_combobox.blockSignals(False)

            # 填充班级列表，避免空字符串导致读取学生列表警告
            list_base_options = get_content_combo_name_async("lottery", "list_combobox")
            class_list = get_class_name_list()
            self.list_combobox.blockSignals(True)
            self.list_combobox.clear()
            if class_list is not None:
                try:
                    combo_items = (list_base_options or []) + (class_list or [])
                except Exception:
                    combo_items = class_list or []
                self.list_combobox.addItems(combo_items)
                self.list_combobox.setCurrentIndex(0)
                try:
                    first_text = self.list_combobox.currentText()
                    if first_text in (list_base_options or []):
                        self.range_combobox.setEnabled(False)
                        self.gender_combobox.setEnabled(False)
                    else:
                        self.range_combobox.setEnabled(True)
                        self.gender_combobox.setEnabled(True)
                except Exception:
                    pass
            self.list_combobox.blockSignals(False)

            # 填充范围和性别选项
            self.range_combobox.blockSignals(True)
            self.range_combobox.clear()

            base_options = get_content_combo_name_async("lottery", "range_combobox")
            list_base_options = get_content_combo_name_async("lottery", "list_combobox")
            selected_text = self.list_combobox.currentText()
            if selected_text in (list_base_options or []):
                self.range_combobox.addItems(base_options[:1])
                self.gender_combobox.blockSignals(True)
                self.gender_combobox.clear()
                self.gender_combobox.addItems(
                    get_content_combo_name_async("lottery", "gender_combobox")[:1]
                )
                self.gender_combobox.blockSignals(False)
            else:
                group_list = get_group_list(selected_text)
                if group_list:
                    self.range_combobox.addItems(base_options + group_list)
                else:
                    self.range_combobox.addItems(base_options[:1])

                self.range_combobox.blockSignals(False)

                self.gender_combobox.blockSignals(True)
                self.gender_combobox.clear()
                self.gender_combobox.addItems(
                    get_content_combo_name_async("lottery", "gender_combobox")
                    + get_gender_list(selected_text)
                )
                self.gender_combobox.blockSignals(False)

            total_count, remaining_count, formatted_text = (
                LotteryUtils.update_prize_many_count_label_text(
                    self.pool_list_combobox.currentText()
                )
            )

            self.remaining_count = remaining_count
            self.many_count_label.setText(formatted_text)

            LotteryUtils.update_start_button_state(self.start_button, total_count)

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
            "lottery"
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
            "lottery_reset_button",
        )

        self.add_control_widget_if_enabled(
            self.control_layout,
            self.count_widget,
            "page_management",
            "lottery_quantity_control",
        )

        self.add_control_widget_if_enabled(
            self.control_layout,
            self.start_button,
            "page_management",
            "lottery_start_button",
        )

        self.add_control_widget_if_enabled(
            self.control_layout,
            self.pool_list_combobox,
            "page_management",
            "lottery_list",
        )

        self.add_control_widget_if_enabled(
            self.control_layout,
            self.list_combobox,
            "page_management",
            "lottery_roll_call_list",
        )

        self.add_control_widget_if_enabled(
            self.control_layout,
            self.range_combobox,
            "page_management",
            "lottery_roll_call_range",
        )

        self.add_control_widget_if_enabled(
            self.control_layout,
            self.gender_combobox,
            "page_management",
            "lottery_roll_call_gender",
        )

        self.add_control_widget_if_enabled(
            self.control_layout,
            self.remaining_button,
            "page_management",
            "lottery_remaining_button",
        )

        self.add_control_widget_if_enabled(
            self.control_layout,
            self.many_count_label,
            "page_management",
            "lottery_quantity_label",
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
