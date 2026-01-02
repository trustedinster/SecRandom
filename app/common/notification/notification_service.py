from loguru import logger

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QApplication
from PySide6.QtCore import Qt, QPoint, QTimer, QPropertyAnimation, QEasingCurve, QRect
from PySide6.QtGui import QMouseEvent
from qfluentwidgets import CardWidget, BodyLabel

from app.page_building.page_template import PageTemplate
from app.tools.variable import WINDOW_BOTTOM_POSITION_FACTOR
from app.Language.obtain_language import get_any_position_value
from app.tools.settings_access import readme_settings_async
from app.common.IPC_URL.url_ipc_handler import URLIPCHandler
from app.common.IPC_URL.csharp_ipc_handler import CSharpIPCHandler


class NotificationContentWidget(QWidget):
    """通知内容控件，用于在浮窗中显示内容"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)
        self.layout.setSpacing(10)
        self.content_widgets = []

    def update_content(self, widgets):
        """更新内容控件"""
        # 清除现有内容
        for widget in self.content_widgets:
            self.layout.removeWidget(widget)
            widget.deleteLater()
        self.content_widgets.clear()

        # 添加新内容
        for widget in widgets:
            self.layout.addWidget(widget)
            self.content_widgets.append(widget)

        # 确保新添加的 BodyLabel 可见：根据主题强制设置前景色
        try:
            from app.tools.personalised import is_dark_theme
            from qfluentwidgets import qconfig
            from qfluentwidgets import BodyLabel as QFBodyLabel

            fg = "#ffffff" if is_dark_theme(qconfig) else "#000000"

            def apply_fg_to(w):
                # 如果是直接的 BodyLabel，设置样式
                if isinstance(w, QFBodyLabel):
                    existing = w.styleSheet() or ""
                    if "color:" not in existing:
                        # 保留已有样式，追加颜色
                        w.setStyleSheet(existing + f" color: {fg};")
                else:
                    # 遍历子控件查找 BodyLabel
                    for child in w.findChildren(QFBodyLabel):
                        existing = child.styleSheet() or ""
                        if "color:" not in existing:
                            child.setStyleSheet(existing + f" color: {fg};")

            for w in self.content_widgets:
                try:
                    apply_fg_to(w)
                except Exception as e:
                    logger.exception("应用前景色到内容控件时出错: {}", e)
        except Exception:
            # 忽略主题检测错误，保持原样
            pass


class NotificationWindowTemplate(PageTemplate):
    """通知窗口页面模板"""

    def __init__(self, parent=None):
        super().__init__(content_widget_class=NotificationContentWidget, parent=parent)


class FloatingNotificationWindow(CardWidget):
    """用于显示抽取结果的浮动通知窗口"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
            | Qt.WindowDoesNotAcceptFocus
        )

        # 添加拖动支持
        self.drag_position = QPoint()

        # 添加三击关闭功能支持
        self.click_count = 0
        self.click_timer = QTimer()
        self.click_timer.setSingleShot(True)
        self.click_timer.timeout.connect(self.reset_click_count)

        # 设置UI
        self.setup_ui()

        # 订阅主题变化，确保切换主题时更新文字颜色
        try:
            from qfluentwidgets import qconfig

            qconfig.themeChanged.connect(self._on_theme_changed)
        except Exception as e:
            logger.exception("连接 themeChanged 信号时出错（已忽略）: {}", e)

        # 设置窗口圆角
        self.setBorderRadius(15)

        # 自动关闭定时器
        self.auto_close_timer = QTimer()
        self.auto_close_timer.setSingleShot(True)
        self.auto_close_timer.timeout.connect(self.start_hide_animation)

        # 倒计时更新定时器
        self.countdown_timer = QTimer()
        self.countdown_timer.timeout.connect(self.update_countdown_display)

        # 周期性置顶定时器
        self._periodic_topmost_timer = QTimer()
        self._periodic_topmost_timer.timeout.connect(self._periodic_topmost)
        self._periodic_topmost_interval = 100

        # 动画相关
        self.geometry_animation = None
        self.opacity_animation = None
        self.is_animation_enabled = True

        # 关闭动画
        self.hide_animation = None

        # 启动周期性置顶
        self._start_periodic_topmost()

    def mousePressEvent(self, event: QMouseEvent):
        """鼠标按下事件处理，用于窗口拖拽"""
        if event.button() == Qt.LeftButton:
            self.drag_position = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        """鼠标移动事件处理，用于窗口拖拽"""
        if event.buttons() == Qt.LeftButton and not self.drag_position.isNull():
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        """鼠标释放事件处理"""
        if event.button() == Qt.LeftButton:
            self.drag_position = QPoint()
            # 处理三击关闭功能
            self.handle_mouse_click()
        event.accept()

    def handle_mouse_click(self):
        """处理鼠标点击，实现三击关闭功能"""
        self.click_count += 1

        if self.click_count == 1:
            # 第一次点击启动计时器
            self.click_timer.start(500)  # 500毫秒内必须完成三次点击
        elif self.click_count == 3:
            # 第三次点击关闭窗口
            self.click_timer.stop()
            self.reset_click_count()
            self.start_hide_animation()  # 使用带动画的关闭方法

    def reset_click_count(self):
        """重置点击计数"""
        self.click_count = 0

    def setup_ui(self):
        """初始化UI组件"""
        # 创建主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 创建顶部拖动提示线容器（用于添加边距）
        self.drag_line_container = QWidget()
        self.update_drag_line_container_style()
        drag_line_layout = QHBoxLayout(self.drag_line_container)
        drag_line_layout.setContentsMargins(15, 15, 15, 0)

        # 创建顶部拖动提示线
        self.drag_line = QWidget()
        self.drag_line.setFixedHeight(5)
        self.drag_line.setFixedWidth(80)
        self.update_drag_line_style()
        drag_line_layout.addWidget(self.drag_line)

        layout.addWidget(self.drag_line_container)

        # 添加一个小的间隔元素，确保拖动条与主布局紧密连接
        spacer = QWidget()
        spacer.setFixedHeight(0)
        spacer.setStyleSheet("background-color: transparent;")
        layout.addWidget(spacer)

        # 创建背景widget，用于设置透明度
        self.background_widget = QWidget()
        self.update_background_style()
        layout.addWidget(self.background_widget)

        # 创建内容布局
        content_layout = QVBoxLayout(self.background_widget)
        content_layout.setContentsMargins(15, 15, 15, 15)
        content_layout.setSpacing(10)

        self.content_layout = QVBoxLayout()
        self.content_layout.setSpacing(10)
        content_layout.addLayout(self.content_layout)

        # 添加倒计时提示标签
        self.countdown_label = BodyLabel()
        self.countdown_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(self.countdown_label)

    def update_background_style(self):
        """根据主题更新背景样式"""
        try:
            # 导入主题判断函数
            from app.tools.personalised import is_dark_theme
            from qfluentwidgets import qconfig

            # 判断是否为深色主题
            if is_dark_theme(qconfig):
                # 深色主题使用深色背景
                background_color = "#202020"
                # 拖动线使用浅色
                self.drag_line_color = "#a0a0a0"
            else:
                # 浅色主题使用浅色背景
                background_color = "#ffffff"
                # 拖动线使用深色
                self.drag_line_color = "#606060"

            self.background_widget.setStyleSheet(
                f"background-color: {background_color}; border-top-left-radius: 0px; border-top-right-radius: 0px; border-bottom-left-radius: 15px; border-bottom-right-radius: 15px;"
            )
            self.update_drag_line_style()
            self.update_drag_line_container_style()
        except Exception as e:
            logger.exception("更新背景样式时出错（使用备用方案）: {}", e)
            # 如果无法获取主题信息，默认使用白色背景和深色拖动线
            background_color = "#ffffff"
            self.background_widget.setStyleSheet(
                "background-color: #ffffff; border-top-left-radius: 0px; border-top-right-radius: 0px; border-bottom-left-radius: 15px; border-bottom-right-radius: 15px;"
            )
            self.drag_line_color = "#606060"
            self.update_drag_line_style()
            self.update_drag_line_container_style()

    def update_drag_line_container_style(self):
        """更新拖动线容器样式"""
        if hasattr(self, "drag_line_container"):
            try:
                # 导入主题判断函数
                from app.tools.personalised import is_dark_theme
                from qfluentwidgets import qconfig

                # 判断是否为深色主题
                if is_dark_theme(qconfig):
                    # 深色主题使用深色背景
                    background_color = "#202020"
                else:
                    # 浅色主题使用浅色背景
                    background_color = "#ffffff"

                self.drag_line_container.setStyleSheet(
                    f"background-color: {background_color}; border-top-left-radius: 15px; border-top-right-radius: 15px; border-bottom-left-radius: 0px; border-bottom-right-radius: 0px;"
                )
            except Exception as e:
                logger.exception("更新拖拽线容器样式时出错（使用备用方案）: {}", e)
                # 如果无法获取主题信息，默认使用白色背景
                self.drag_line_container.setStyleSheet(
                    "background-color: #ffffff; border-top-left-radius: 15px; border-top-right-radius: 15px; border-bottom-left-radius: 0px; border-bottom-right-radius: 0px;"
                )

    def update_drag_line_style(self):
        """更新拖动线样式"""
        if hasattr(self, "drag_line") and hasattr(self, "drag_line_color"):
            self.drag_line.setStyleSheet(f"""
                QWidget {{
                    background-color: {self.drag_line_color};
                    border-radius: 2px;
                }}
            """)

    def apply_settings(self, settings=None, settings_group=None):
        """应用设置到通知窗口"""
        if settings:
            # 使用传递的设置
            transparency = settings.get("transparency", 0.6)
            auto_close_time = settings.get("auto_close_time", 5)
            self.is_animation_enabled = settings.get("animation", True)
        else:
            transparency = 0.6
            auto_close_time = 5
            self.is_animation_enabled = True

        # 保存设置组，用于后续判断是否抢占焦点
        self.settings_group = settings_group

        # 设置透明度（背景和字体透明度统一）
        self.setWindowOpacity(transparency)

        # 设置倒计时标签颜色，确保与背景对比
        try:
            from app.tools.personalised import is_dark_theme
            from qfluentwidgets import qconfig

            fg = "#ffffff" if is_dark_theme(qconfig) else "#000000"
            existing = self.countdown_label.styleSheet() or ""
            if "color:" not in existing:
                self.countdown_label.setStyleSheet(existing + f" color: {fg};")
        except Exception as e:
            logger.exception("设置倒计时标签颜色时出错: {}", e)

        # 根据设置定位窗口
        self.position_window(settings)

        # 设置自动关闭时间
        if auto_close_time > 0:
            self.auto_close_timer.stop()
            self.auto_close_timer.setInterval(auto_close_time * 1000)  # 转换为毫秒
            # 初始化倒计时并启动更新定时器
            self.countdown_timer.stop()
            self.remaining_time = auto_close_time  # 初始化为设定的自动关闭时间
            # 先显示初始倒计时
            self.countdown_label.setText(
                get_any_position_value("notification_common", "auto_close_hint").format(
                    self.remaining_time  # 显示当前设定的值
                )
            )
            self.countdown_timer.start(1000)  # 每秒更新一次
            self.auto_close_timer.start()  # 启动自动关闭定时器作为备用
        else:
            # 停止倒计时更新定时器并显示手动关闭提示
            self.countdown_timer.stop()
            self.countdown_label.setText(
                get_any_position_value("notification_common", "manual_close_hint")
            )

    def update_countdown_display(self):
        """更新倒计时显示"""
        self.remaining_time -= 1
        # 动画完成时显示倒计时
        if self.remaining_time > 0:
            self.countdown_label.setText(
                get_any_position_value("notification_common", "auto_close_hint").format(
                    self.remaining_time
                )
            )
        else:
            # 当倒计时减到0或以下时立即关闭窗口
            self.countdown_timer.stop()
            self.auto_close_timer.stop()  # 停止自动关闭定时器，防止重复关闭
            self.start_hide_animation()

    def _on_theme_changed(self):
        """主题切换时更新浮窗内文字和背景颜色"""
        try:
            from app.tools.personalised import is_dark_theme
            from qfluentwidgets import qconfig

            fg = "#ffffff" if is_dark_theme(qconfig) else "#000000"

            # 更新倒计时标签颜色
            try:
                existing = self.countdown_label.styleSheet() or ""
                parts = [
                    p.strip()
                    for p in existing.split(";")
                    if p.strip() and not p.strip().startswith("color:")
                ]
                parts.append(f"color: {fg} !important")
                self.countdown_label.setStyleSheet("; ".join(parts) + ";")
            except Exception as e:
                logger.exception("应用倒计时标签颜色时出错（已忽略）：{}", e)
                pass

            # 更新背景与拖动线样式
            try:
                self.update_background_style()
                self.update_drag_line_style()
                self.update_drag_line_container_style()
            except Exception as e:
                logger.exception("更新背景/拖拽线样式时出错（已忽略）: {}", e)
                pass
        except Exception as e:
            logger.exception("处理 _on_theme_changed 时出错（已忽略）: {}", e)
            pass

    def _get_screen_from_settings(self, settings):
        """根据设置获取屏幕"""
        screen = QApplication.primaryScreen()

        if settings:
            enabled_monitor_name = settings.get("enabled_monitor", "OFF")
            # 尝试获取指定的显示器
            if enabled_monitor_name != "OFF":
                for s in QApplication.screens():
                    if s.name() == enabled_monitor_name:
                        screen = s
                        logger.debug("使用显示器：{}", enabled_monitor_name)
                        break

        if screen is None:
            screen = QApplication.primaryScreen()

        return screen

    def _calculate_window_position(
        self, screen_geometry, position_index, horizontal_offset, vertical_offset
    ):
        """计算窗口位置"""
        window_width = 300
        window_height = 200

        # 根据设置计算位置
        # 位置映射基于语言文件:
        # 0: 中心, 1: 顶部, 2: 底部, 3: 左侧, 4: 右侧,
        # 5: 顶部左侧, 6: 顶部右侧, 7: 底部左侧, 8: 底部右侧
        if position_index == 0:  # 中心
            x = screen_geometry.center().x() - window_width // 2 + horizontal_offset
            y = screen_geometry.center().y() - window_height // 2 + vertical_offset
        elif position_index == 1:  # 顶部
            x = screen_geometry.center().x() - window_width // 2 + horizontal_offset
            y = screen_geometry.top() + vertical_offset
        elif position_index == 2:  # 底部
            x = screen_geometry.center().x() - window_width // 2 + horizontal_offset
            y = (
                screen_geometry.bottom()
                - window_height * WINDOW_BOTTOM_POSITION_FACTOR
                + vertical_offset
            )
        elif position_index == 3:  # 左侧
            x = screen_geometry.left() + horizontal_offset
            y = screen_geometry.center().y() - window_height // 2 + vertical_offset
        elif position_index == 4:  # 右侧
            x = screen_geometry.right() - window_width + horizontal_offset
            y = screen_geometry.center().y() - window_height // 2 + vertical_offset
        elif position_index == 5:  # 顶部左侧
            x = screen_geometry.left() + horizontal_offset
            y = screen_geometry.top() + vertical_offset
        elif position_index == 6:  # 顶部右侧
            x = screen_geometry.right() - window_width + horizontal_offset
            y = screen_geometry.top() + vertical_offset
        elif position_index == 7:  # 底部左侧
            x = screen_geometry.left() + horizontal_offset
            y = (
                screen_geometry.bottom()
                - window_height * WINDOW_BOTTOM_POSITION_FACTOR
                + vertical_offset
            )
        elif position_index == 8:  # 底部右侧
            x = screen_geometry.right() - window_width + horizontal_offset
            y = (
                screen_geometry.bottom()
                - window_height * WINDOW_BOTTOM_POSITION_FACTOR
                + vertical_offset
            )
        else:  # 默认为中心
            x = screen_geometry.center().x() - window_width // 2
            y = screen_geometry.center().y() - window_height // 2

        return QRect(x, y, window_width, window_height)

    def position_window(self, settings=None):
        """根据设置定位浮窗"""
        # 获取屏幕
        screen = self._get_screen_from_settings(settings)
        screen_geometry = screen.geometry()

        # 获取设置
        if settings:
            position_index = settings.get("window_position", 0)
            horizontal_offset = settings.get("horizontal_offset", 0)
            vertical_offset = settings.get("vertical_offset", 0)
        else:
            position_index = 0
            horizontal_offset = 0
            vertical_offset = 0

        # 不在定位阶段显示窗口，避免显示空白窗口
        # 通过默认尺寸计算位置，内容添加后再调整大小
        window_rect = self._calculate_window_position(
            screen_geometry, position_index, horizontal_offset, vertical_offset
        )
        self.move(window_rect.x(), window_rect.y())

    def _calculate_animation_start_geometry(
        self, final_geometry, screen_geometry, position_index
    ):
        """根据位置确定动画起始位置，确保从屏幕外进入"""
        if position_index == 0:  # 中心
            start_geometry = QRect(
                final_geometry.center().x() - final_geometry.width() // 2,
                final_geometry.center().y() - final_geometry.height() // 2,
                0,
                0,
            )
        elif position_index == 1:  # 顶部
            start_geometry = QRect(
                final_geometry.x(),
                screen_geometry.top() - final_geometry.height(),  # 从屏幕顶部外进入
                final_geometry.width(),
                final_geometry.height(),
            )
        elif position_index == 2:  # 底部
            start_geometry = QRect(
                final_geometry.x(),
                screen_geometry.bottom(),  # 从屏幕底部外进入
                final_geometry.width(),
                0,  # 高度从0开始动画
            )
        elif position_index == 3:  # 左侧
            start_geometry = QRect(
                screen_geometry.left() - final_geometry.width(),  # 从屏幕左侧外进入
                final_geometry.y(),
                0,  # 宽度从0开始动画
                final_geometry.height(),
            )
        elif position_index == 4:  # 右侧
            start_geometry = QRect(
                screen_geometry.right(),  # 从屏幕右侧外进入
                final_geometry.y(),
                0,  # 宽度从0开始动画
                final_geometry.height(),
            )
        elif position_index == 5:  # 顶部左侧
            start_geometry = QRect(
                screen_geometry.left() - final_geometry.width(),  # 从屏幕左侧外进入
                screen_geometry.top() - final_geometry.height(),  # 从屏幕顶部外进入
                0,  # 宽度从0开始动画
                0,  # 高度从0开始动画
            )
        elif position_index == 6:  # 顶部右侧
            start_geometry = QRect(
                screen_geometry.right(),  # 从屏幕右侧外进入
                screen_geometry.top() - final_geometry.height(),  # 从屏幕顶部外进入
                0,  # 宽度从0开始动画
                0,  # 高度从0开始动画
            )
        elif position_index == 7:  # 底部左侧
            start_geometry = QRect(
                screen_geometry.left() - final_geometry.width(),  # 从屏幕左侧外进入
                screen_geometry.bottom(),  # 从屏幕底部外进入
                0,  # 宽度从0开始动画
                0,  # 高度从0开始动画
            )
        elif position_index == 8:  # 底部右侧
            start_geometry = QRect(
                screen_geometry.right(),  # 从屏幕右侧外进入
                screen_geometry.bottom(),  # 从屏幕底部外进入
                0,  # 宽度从0开始动画
                0,  # 高度从0开始动画
            )
        else:  # 默认为中心，从中心缩放进入
            start_geometry = QRect(
                final_geometry.center().x() - final_geometry.width() // 2,
                final_geometry.center().y() - final_geometry.height() // 2,
                0,
                0,
            )

        return start_geometry

    def start_show_animation(self, settings=None):
        """开始显示动画"""
        # 重置动画完成标志
        if not self.is_animation_enabled:
            # 即使没有动画也要确保在正确的屏幕显示
            screen = self._get_screen_from_settings(settings)
            screen_geometry = screen.geometry()

            if settings:
                position_index = settings.get("window_position", 0)
                horizontal_offset = settings.get("horizontal_offset", 0)
                vertical_offset = settings.get("vertical_offset", 0)
            else:
                position_index = 0
                horizontal_offset = 0
                vertical_offset = 0

            # 计算最终位置
            window_rect = self._calculate_window_position(
                screen_geometry, position_index, horizontal_offset, vertical_offset
            )
            self.move(window_rect.x(), window_rect.y())

            self.show()
            self.update_countdown_display()
            return

        # 确保窗口大小已调整
        self.adjustSize()

        # 获取设置以确定动画类型
        position_index = 0
        if settings:
            position_index = settings.get("window_position", 0)

        # 根据设置计算最终位置和屏幕信息，但不移动窗口
        screen = self._get_screen_from_settings(settings)
        screen_geometry = screen.geometry()

        if settings:
            horizontal_offset = settings.get("horizontal_offset", 0)
            vertical_offset = settings.get("vertical_offset", 0)
        else:
            horizontal_offset = 0
            vertical_offset = 0

        # 计算最终位置
        window_rect = self._calculate_window_position(
            screen_geometry, position_index, horizontal_offset, vertical_offset
        )
        # 使用当前窗口的实际尺寸而不是固定尺寸
        final_geometry = QRect(
            window_rect.x(), window_rect.y(), self.width(), self.height()
        )

        # 计算动画起始位置
        start_geometry = self._calculate_animation_start_geometry(
            final_geometry, screen_geometry, position_index
        )

        # 透明度
        transparency = settings.get("transparency", 0.6)

        # 创建几何动画
        self.geometry_animation = QPropertyAnimation(self, b"geometry")
        self.geometry_animation.setDuration(750)  # 增加动画时长以获得更平滑的效果
        self.geometry_animation.setStartValue(start_geometry)
        self.geometry_animation.setEndValue(final_geometry)
        self.geometry_animation.setEasingCurve(
            QEasingCurve.OutCubic
        )  # 使用更自然的缓动曲线

        # 创建透明度动画
        self.opacity_animation = QPropertyAnimation(self, b"windowOpacity")
        self.opacity_animation.setDuration(450)
        self.opacity_animation.setStartValue(0.0)
        self.opacity_animation.setEndValue(transparency)
        self.opacity_animation.setEasingCurve(
            QEasingCurve.OutCubic
        )  # 使用更自然的缓动曲线

        # 连接动画完成信号
        self.geometry_animation.finished.connect(self.on_animation_finished)

        # 设置窗口初始位置并开始动画
        self.setGeometry(start_geometry)
        self.setWindowOpacity(0.0)  # 初始透明度为0
        self.show()

        # 确保窗口管理器处理显示事件
        QApplication.processEvents()

        # 并行启动所有动画
        self.geometry_animation.start()
        self.opacity_animation.start()

        # 立即更新倒计时显示（显示"正在抽取中"）
        self.update_countdown_display()
        # 确保颜色与当前主题同步
        try:
            self._on_theme_changed()
        except Exception as e:
            logger.exception("显示时同步主题时出错（已忽略）: {}", e)

    def on_animation_finished(self):
        """动画完成后的处理"""
        # 清理动画对象
        if hasattr(self, "geometry_animation"):
            self.geometry_animation.deleteLater()
            del self.geometry_animation
        if hasattr(self, "opacity_animation"):
            self.opacity_animation.deleteLater()
            del self.opacity_animation

        # 如果设置了自动关闭时间，则启动定时器
        if hasattr(self, "auto_close_timer") and self.auto_close_timer.interval() > 0:
            self.auto_close_timer.start()

        # 检查是否设置了"无焦点模式"
        do_not_steal_focus = False
        try:
            do_not_steal_focus = readme_settings_async(
                "floating_window_management", "do_not_steal_focus"
            )
        except Exception:
            pass

        # 如果没有设置"无焦点模式"，则确保窗口保持在最前面并激活
        if not do_not_steal_focus:
            self.raise_()
            # 仅在窗口允许接受焦点时调用激活，避免 QWindow::requestActivate 警告
            try:
                if not (self.windowFlags() & Qt.WindowDoesNotAcceptFocus):
                    self.activateWindow()
            except Exception as e:
                logger.exception("激活窗口时出错（已忽略）: {}", e)

        # 更新倒计时显示
        self.update_countdown_display()

    def _start_periodic_topmost(self):
        """启动周期性置顶定时器"""
        self._periodic_topmost_timer.start(self._periodic_topmost_interval)

    def _periodic_topmost(self):
        """周期性将窗口置顶"""
        if self.isVisible():
            self.raise_()

    def start_hide_animation(self):
        """开始隐藏动画"""
        if not self.is_animation_enabled:
            self.hide()
            return

        # 创建透明度动画
        self.hide_animation = QPropertyAnimation(self, b"windowOpacity")
        self.hide_animation.setDuration(300)
        self.hide_animation.setStartValue(self.windowOpacity())
        self.hide_animation.setEndValue(0.0)
        self.hide_animation.setEasingCurve(QEasingCurve.OutCubic)

        # 连接动画完成信号
        self.hide_animation.finished.connect(self.on_hide_animation_finished)

        # 启动动画
        self.hide_animation.start()

    def on_hide_animation_finished(self):
        """隐藏动画完成后的处理"""
        # 清理动画对象
        if self.hide_animation:
            self.hide_animation.deleteLater()
            self.hide_animation = None

        # 隐藏窗口
        self.hide()

    def update_content(
        self,
        student_labels,
        settings=None,
        font_settings_group=None,
        settings_group=None,
    ):
        """更新通知窗口的内容

        Args:
            student_labels: 包含学生信息的BodyLabel控件列表
            settings: 通知设置参数
            font_settings_group: 字体设置组名称
            settings_group: 通知设置组名称
        """
        # 保存设置组，用于后续判断是否抢占焦点
        if settings_group:
            self.settings_group = settings_group
        elif font_settings_group:
            # 如果没有提供settings_group，尝试从font_settings_group推断
            if font_settings_group == "roll_call_settings":
                self.settings_group = "roll_call_notification_settings"
            elif font_settings_group == "quick_draw_settings":
                self.settings_group = "quick_draw_notification_settings"
            elif font_settings_group == "lottery_settings":
                self.settings_group = "lottery_notification_settings"

        # 清除现有内容
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # 添加新内容
        if student_labels:
            for label in student_labels:
                # 如果有字体设置，则应用到标签上
                if font_settings_group:
                    # 检查是否使用全局字体
                    use_global_font = readme_settings_async(
                        font_settings_group, "use_global_font"
                    )
                    custom_font = None
                    if use_global_font == 1:  # 不使用全局字体，使用自定义字体
                        custom_font = readme_settings_async(
                            font_settings_group, "custom_font"
                        )
                        if custom_font and hasattr(label, "setStyleSheet"):
                            # 获取当前样式表并添加字体设置
                            current_style = label.styleSheet()
                            label.setStyleSheet(
                                f"font-family: '{custom_font}'; {current_style}"
                            )
                self.content_layout.addWidget(label)

        # 确保颜色与当前主题同步
        try:
            self._on_theme_changed()
        except Exception as e:
            logger.exception("更新内容时同步主题时出错（已忽略）: {}", e)

        # 调整窗口大小以适应内容
        self.adjustSize()

        # 检查窗口是否已经显示
        if self.isVisible():
            # 如果窗口已经显示，只更新内容和透明度，不重新定位窗口
            if settings:
                transparency = settings.get("transparency", 0.6)
                self.setWindowOpacity(transparency)

                # 重新应用倒计时设置，但不重新定位窗口
                auto_close_time = settings.get("auto_close_time", 5)
                if auto_close_time > 0:
                    self.auto_close_timer.stop()
                    self.auto_close_timer.setInterval(auto_close_time * 1000)
                    # 初始化倒计时并启动更新定时器
                    self.countdown_timer.stop()
                    self.remaining_time = auto_close_time
                    self.update_countdown_display()
                    self.auto_close_timer.start()
                    self.countdown_timer.start(1000)  # 每秒更新一次
                else:
                    # 停止倒计时更新定时器并显示手动关闭提示
                    self.countdown_timer.stop()
                    self.countdown_label.setText("连续点击3次关闭窗口")
        else:
            # 如果窗口未显示，完整初始化窗口
            self.apply_settings(settings)

            # 显示窗口
            self.start_show_animation(settings)


class FloatingNotificationManager:
    """管理浮动通知窗口"""

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FloatingNotificationManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.notification_windows = {}
            # 初始化IPC处理器
            self.ipc_handler = URLIPCHandler("SecRandom", "secrandom")
            self._initialized = True

    def send_to_classisland2(
        self,
        class_name,
        selected_students,
        draw_count=1,
        settings=None,
        settings_group=None,
    ):
        """发送通知到ClassIsland（旧版）

        Args:
            class_name: 班级名称
            selected_students: 选中的学生列表 [(学号, 姓名, 是否存在), ...]
            draw_count: 抽取的学生数量
            settings: 通知设置参数
            settings_group: 设置组名称
        """
        try:
            # 构建通知数据
            notification_data = {
                "type": "notification",
                "subtype": "roll_call",
                "class_name": class_name,
                "selected_students": [
                    {
                        "student_id": student[0],
                        "student_name": student[1],
                        "exists": student[2],
                    }
                    for student in selected_students
                ],
                "draw_count": draw_count,
            }

            # 如果提供了设置，添加显示时长
            if settings:
                display_duration = settings.get("notification_display_duration", 5)
                notification_data["display_duration"] = display_duration

            # 创建ClassIsland IPC处理器来发送消息
            classisland_ipc = URLIPCHandler("ClassIsland", "classisland")

            # 尝试从配置中加载ClassIsland的端口
            port = classisland_ipc.load_port_config()

            if port is None:
                logger.warning("无法获取ClassIsland的IPC端口，可能ClassIsland未运行")
                # 如果无法获取端口，回退到SecRandom通知服务
                logger.info("回退到SecRandom通知服务")
                self._show_secrandom_notification(
                    class_name, selected_students, draw_count, settings, settings_group
                )
                return

            # 发送IPC消息到ClassIsland
            response = classisland_ipc.send_ipc_message(port, notification_data)

            if response:
                logger.info("成功发送通知到ClassIsland: {}", response)
            else:
                logger.warning("发送通知到ClassIsland失败")
                # 如果发送失败，回退到SecRandom通知服务
                logger.info("回退到SecRandom通知服务")
                self._show_secrandom_notification(
                    class_name, selected_students, draw_count, settings, settings_group
                )

        except Exception as e:
            logger.exception("发送通知到ClassIsland时出错: {}", e)
            # 如果发生异常，回退到SecRandom通知服务
            logger.info("因错误回退到SecRandom通知服务")
            self._show_secrandom_notification(
                class_name, selected_students, draw_count, settings, settings_group
            )

    def send_to_classisland(
        self,
        class_name,
        selected_students,
        draw_count=1,
        settings=None,
        settings_group=None,
    ):
        """发送通知到ClassIsland

        Args:
            class_name: 班级名称
            selected_students: 选中的学生列表 [(学号, 姓名, 是否存在), ...]
            draw_count: 抽取的学生数量
            settings: 通知设置参数
            settings_group: 设置组名称
        """

        try:
            cs_ipc = CSharpIPCHandler.instance()
            status = cs_ipc.send_notification(
                class_name, selected_students, draw_count, settings, settings_group
            )
            if status:
                logger.info("成功发送通知到ClassIsland，结果未知")
            else:
                logger.info("因错误回退到SecRandom通知服务")
                self._show_secrandom_notification(
                    class_name, selected_students, draw_count, settings, settings_group
                )
        except Exception as e:
            logger.exception("发送通知到ClassIsland时出错: {}", e)
            # 如果发生异常，回退到SecRandom通知服务
            logger.info("因错误回退到SecRandom通知服务")
            self._show_secrandom_notification(
                class_name, selected_students, draw_count, settings, settings_group
            )

    def _show_secrandom_notification(
        self,
        class_name,
        selected_students,
        draw_count=1,
        settings=None,
        settings_group=None,
    ):
        """显示SecRandom内置通知（用于回退）"""
        # 重新调用SecRandom通知服务，使用原始的show_roll_call_result逻辑
        if settings:
            font_size = settings.get("font_size", 50)
            animation_color = settings.get("animation_color_theme", 0)
            display_format = settings.get("display_format", 0)
            show_student_image = settings.get("student_image", False)
            is_animation_enabled = settings.get("animation", True)
        else:
            # 当没有传递设置时，使用默认值
            font_size = 50
            animation_color = 0
            display_format = 0
            show_student_image = False
            is_animation_enabled = True

        # 使用ResultDisplayUtils创建学生标签（动态导入避免循环依赖）
        from app.common.display.result_display import ResultDisplayUtils

        # 确定使用的设置组
        # 如果 settings_group 是通知设置组，则使用对应的功能设置组的字体设置
        if settings_group is None:
            settings_group = "notification_settings"
        # 根据通知设置组名称确定对应的功能设置组
        if settings_group == "roll_call_notification_settings":
            font_settings_group = "roll_call_settings"
        elif settings_group == "quick_draw_notification_settings":
            font_settings_group = "quick_draw_settings"
        elif settings_group == "lottery_notification_settings":
            font_settings_group = "lottery_settings"
        else:
            font_settings_group = settings_group

        student_labels = ResultDisplayUtils.create_student_label(
            class_name=class_name,
            selected_students=selected_students,
            draw_count=draw_count,
            font_size=font_size,
            animation_color=animation_color,
            display_format=display_format,
            show_student_image=show_student_image,
            settings_group=settings_group,
            custom_font_family=font_settings_group,
        )

        # 创建或获取通知窗口
        if "floating" not in self.notification_windows:
            self.notification_windows["floating"] = FloatingNotificationWindow()

        window = self.notification_windows["floating"]
        window.is_animation_enabled = is_animation_enabled
        # 如果窗口已经存在并且有活动的自动关闭定时器，停止它以防止窗口被隐藏
        if window.auto_close_timer.isActive():
            window.auto_close_timer.stop()

        # 应用显示时长设置到窗口
        if settings:
            display_duration = settings.get("notification_display_duration", 5)
            window.apply_settings(
                {**settings, "auto_close_time": display_duration}, settings_group
            )
        else:
            window.apply_settings({"auto_close_time": 5}, settings_group)  # 默认5秒

        window.update_content(
            student_labels, settings, font_settings_group, settings_group
        )

    def get_notification_title(self):
        """获取通知标题文本（支持多语言）"""
        try:
            from app.Language.obtain_language import get_content_name_async

            return get_content_name_async(
                "notification_settings", "notification_result"
            )
        except Exception as e:
            logger.exception("获取通知标题时出错（使用备用方案）: {}", e)
            # 如果无法获取多语言文本，则使用默认文本
            return "通知结果"

    def show_roll_call_result(
        self,
        class_name,
        selected_students,
        draw_count=1,
        settings=None,
        settings_group=None,
    ):
        """在浮动通知窗口中显示点名结果

        Args:
            class_name: 班级名称
            selected_students: 选中的学生列表 [(学号, 姓名, 是否存在), ...]
            draw_count: 抽取的学生数量
            settings: 通知设置参数
            settings_group: 设置组名称，默认为notification_settings
        """
        # 获取通知服务类型设置
        notification_service_type = 0  # 默认为SecRandom通知服务
        if settings_group:
            # 根据设置组获取对应的通知服务类型设置
            try:
                notification_service_type = readme_settings_async(
                    settings_group, "notification_service_type"
                )
            except Exception as e:
                logger.warning("获取通知服务类型设置失败，使用默认值: {}", e)

        # 如果选择了ClassIsland通知服务，则发送到ClassIsland
        if notification_service_type == 1:  # 1 表示 ClassIsland 通知服务
            self.send_to_classisland(
                class_name, selected_students, draw_count, settings, settings_group
            )
            return

        # 否则使用SecRandom浮窗通知
        # 获取设置
        if settings:
            font_size = settings.get("font_size", 50)
            animation_color = settings.get("animation_color_theme", 0)
            display_format = settings.get("display_format", 0)
            show_student_image = settings.get("student_image", False)
            is_animation_enabled = settings.get("animation", True)
        else:
            # 当没有传递设置时，使用默认值
            font_size = 50
            animation_color = 0
            display_format = 0
            show_student_image = False
            is_animation_enabled = True

        # 使用ResultDisplayUtils创建学生标签（动态导入避免循环依赖）
        from app.common.display.result_display import ResultDisplayUtils

        # 确定使用的设置组
        # 如果 settings_group 是通知设置组，则使用对应的功能设置组的字体设置
        if settings_group is None:
            settings_group = "notification_settings"
        # 根据通知设置组名称确定对应的功能设置组
        if settings_group == "roll_call_notification_settings":
            font_settings_group = "roll_call_settings"
        elif settings_group == "quick_draw_notification_settings":
            font_settings_group = "quick_draw_settings"
        elif settings_group == "lottery_notification_settings":
            font_settings_group = "lottery_settings"
        else:
            font_settings_group = settings_group

        student_labels = ResultDisplayUtils.create_student_label(
            class_name=class_name,
            selected_students=selected_students,
            draw_count=draw_count,
            font_size=font_size,
            animation_color=animation_color,
            display_format=display_format,
            show_student_image=show_student_image,
            settings_group=settings_group,
            custom_font_family=font_settings_group,
        )

        # 创建或获取通知窗口
        if "floating" not in self.notification_windows:
            self.notification_windows["floating"] = FloatingNotificationWindow()

        window = self.notification_windows["floating"]
        window.is_animation_enabled = is_animation_enabled
        # 如果窗口已经存在并且有活动的自动关闭定时器，停止它以防止窗口被隐藏
        if window.auto_close_timer.isActive():
            window.auto_close_timer.stop()

        # 应用显示时长设置到窗口
        if settings:
            display_duration = settings.get("notification_display_duration", 5)
            window.apply_settings(
                {**settings, "auto_close_time": display_duration}, settings_group
            )
        else:
            window.apply_settings({"auto_close_time": 5}, settings_group)  # 默认5秒

        window.update_content(
            student_labels, settings, font_settings_group, settings_group
        )

    def close_all_notifications(self):
        """关闭所有浮动通知窗口"""
        # 关闭浮窗
        for window in self.notification_windows.values():
            if window.auto_close_timer.isActive():
                window.auto_close_timer.stop()
            window.close()
        self.notification_windows.clear()


def show_roll_call_notification(
    class_name, selected_students, draw_count=1, settings=None, settings_group=None
):
    """显示点名通知的便捷函数

    Args:
        class_name: 班级名称
        selected_students: 选中的学生列表 [(学号, 姓名, 是否存在), ...]
        draw_count: 抽取的学生数量
        settings: 通知设置参数
    """
    manager = FloatingNotificationManager()
    manager.show_roll_call_result(
        class_name, selected_students, draw_count, settings, settings_group
    )
