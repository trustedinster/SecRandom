# ==================================================
# 导入库
# ==================================================
import sys
import subprocess

import loguru
from loguru import logger
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtGui import QIcon
from PySide6.QtCore import QTimer, QEvent, Signal
from qfluentwidgets import FluentWindow, NavigationItemPosition

from app.tools.variable import MINIMUM_WINDOW_SIZE, APP_INIT_DELAY
from app.tools.path_utils import get_data_path
from app.tools.path_utils import get_app_root
from app.tools.personalised import get_theme_icon
from app.Language.obtain_language import get_content_name_async
from app.Language.obtain_language import readme_settings_async, update_settings
from app.common.safety.verify_ops import require_and_run
from app.page_building.main_window_page import (
    roll_call_page,
    lottery_page,
    history_page,
)
from app.view.tray.tray import Tray
from app.view.floating_window.levitation import LevitationWindow
from app.common.IPC_URL.url_command_handler import URLCommandHandler


# ==================================================
# 主窗口类
# ==================================================
class MainWindow(FluentWindow):
    """主窗口类
    程序的核心控制中心"""

    showSettingsRequested = Signal(str)  # 请求显示设置页面
    showSettingsRequestedAbout = Signal()
    showFloatWindowRequested = Signal()
    showMainPageRequested = Signal(str)  # 请求显示主页面
    showTrayActionRequested = Signal(str)  # 请求执行托盘操作

    def __init__(self, float_window: LevitationWindow):
        super().__init__()
        # 设置窗口对象名称，方便其他组件查找
        self.setObjectName("MainWindow")

        self.roll_call_page = None
        self.settingsInterface = None

        self.roll_call_page = None
        self.settingsInterface = None

        # resize_timer的初始化
        self.resize_timer = QTimer(self)
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(
            lambda: self.save_window_size(self.width(), self.height())
        )

        # 设置窗口属性
        self.setMinimumSize(MINIMUM_WINDOW_SIZE[0], MINIMUM_WINDOW_SIZE[1])
        self.setWindowTitle("SecRandom")
        self.setWindowIcon(
            QIcon(str(get_data_path("assets/icon", "secrandom-icon-paper.png")))
        )

        self._position_window()

        # 初始化URL命令处理器
        self.url_command_handler = URLCommandHandler(self)
        self.url_command_handler.showMainPageRequested.connect(
            self._handle_main_page_requested
        )
        self.url_command_handler.showSettingsRequested.connect(
            self.showSettingsRequested.emit
        )
        self.url_command_handler.showTrayActionRequested.connect(
            self._handle_tray_action_requested
        )

        # 导入并创建托盘图标
        self.tray_icon = Tray(self)
        self.tray_icon.showSettingsRequested.connect(self.showSettingsRequested.emit)
        self.tray_icon.showSettingsRequestedAbout.connect(
            self.showSettingsRequestedAbout.emit
        )
        self.tray_icon.showFloatWindowRequested.connect(
            self.showFloatWindowRequested.emit
        )
        self.tray_icon.showTrayActionRequested.connect(
            self.showTrayActionRequested.emit
        )
        self.tray_icon.show_tray_icon()

        self.float_window = float_window
        self.showFloatWindowRequested.connect(self._toggle_float_window)
        self.showMainPageRequested.connect(self._handle_main_page_requested)
        self.showTrayActionRequested.connect(self._handle_tray_action_requested)
        self.float_window.rollCallRequested.connect(
            lambda: self._show_and_switch_to(self.roll_call_page)
        )
        self.float_window.lotteryRequested.connect(
            lambda: self._show_and_switch_to(self.lottery_page)
        )

        QTimer.singleShot(APP_INIT_DELAY, lambda: (self.createSubInterface()))

    def _position_window(self):
        """窗口定位
        根据屏幕尺寸和用户设置自动计算最佳位置"""
        is_maximized = readme_settings_async("window", "is_maximized")
        if is_maximized:
            pre_maximized_width = readme_settings_async("window", "pre_maximized_width")
            pre_maximized_height = readme_settings_async(
                "window", "pre_maximized_height"
            )
            self.resize(pre_maximized_width, pre_maximized_height)
            self._center_window()
            QTimer.singleShot(APP_INIT_DELAY, self.showMaximized)
        else:
            window_width = readme_settings_async("window", "width")
            window_height = readme_settings_async("window", "height")
            self.resize(window_width, window_height)
            self._center_window()

    def _center_window(self):
        """窗口居中
        将窗口移动到屏幕中心"""
        screen = QApplication.primaryScreen()
        desktop = screen.availableGeometry()
        w, h = desktop.width(), desktop.height()

        target_x = w // 2 - self.width() // 2
        target_y = h // 2 - self.height() // 2

        self.move(target_x, target_y)

    def _apply_window_visibility_settings(self):
        """应用窗口显示设置
        根据用户保存的设置决定窗口是否显示"""
        try:
            self.show()
        except Exception as e:
            logger.error(f"加载窗口显示设置失败: {e}")

    def createSubInterface(self):
        """创建子界面
        搭建子界面导航系统"""

        self.roll_call_page = roll_call_page(self)
        self.roll_call_page.setObjectName("roll_call_page")

        self.lottery_page = lottery_page(self)
        self.lottery_page.setObjectName("lottery_page")

        self.history_page = history_page(self)
        self.history_page.setObjectName("history_page")

        self.settingsInterface = QWidget(self)
        self.settingsInterface.setObjectName("settingsInterface")

        # 为所有子页面安装事件过滤器，点击时自动折叠导航栏
        for page in [self.roll_call_page, self.lottery_page, self.history_page]:
            page.installEventFilter(self)

        self.initNavigation()

    def initNavigation(self):
        """初始化导航系统
        根据用户设置构建个性化菜单导航"""
        # 获取点名侧边栏位置设置
        roll_call_sidebar_pos = readme_settings_async(
            "sidebar_management_window", "roll_call_sidebar_position"
        )
        roll_call_position = (
            NavigationItemPosition.TOP
            if (roll_call_sidebar_pos is None or roll_call_sidebar_pos != 1)
            else NavigationItemPosition.BOTTOM
        )

        self.addSubInterface(
            self.roll_call_page,
            get_theme_icon("ic_fluent_people_20_filled"),
            get_content_name_async("roll_call", "title"),
            position=roll_call_position,
        )

        # 获取奖池侧边栏位置设置
        lottery_sidebar_pos = readme_settings_async(
            "sidebar_management_window", "lottery_sidebar_position"
        )
        lottery_position = (
            NavigationItemPosition.TOP
            if (lottery_sidebar_pos is None or lottery_sidebar_pos != 1)
            else NavigationItemPosition.BOTTOM
        )

        self.addSubInterface(
            self.lottery_page,
            get_theme_icon("ic_fluent_gift_20_filled"),
            get_content_name_async("lottery", "title"),
            position=lottery_position,
        )

        # 获取历史记录侧边栏位置设置
        history_sidebar_pos = readme_settings_async(
            "sidebar_management_window", "main_window_history"
        )
        history_position = (
            NavigationItemPosition.TOP
            if (history_sidebar_pos is None or history_sidebar_pos != 1)
            else NavigationItemPosition.BOTTOM
        )

        self.addSubInterface(
            self.history_page,
            get_theme_icon("ic_fluent_history_20_filled"),
            get_content_name_async("history", "title"),
            position=history_position,
        )

        # 获取设置图标位置设置
        settings_icon_pos = readme_settings_async(
            "sidebar_management_window", "settings_icon"
        )
        settings_position = (
            NavigationItemPosition.BOTTOM
            if (settings_icon_pos == 1)
            else NavigationItemPosition.TOP
        )

        settings_item = self.addSubInterface(
            self.settingsInterface,
            get_theme_icon("ic_fluent_settings_20_filled"),
            get_content_name_async("settings", "title"),
            position=settings_position,
        )
        settings_item.clicked.connect(
            lambda: require_and_run(
                "open_settings",
                self,
                lambda: self.showSettingsRequested.emit("basicSettingsInterface"),
            )
        )
        settings_item.clicked.connect(lambda: self.switchTo(self.roll_call_page))

        # 配置导航栏为可折叠模式
        self._setupCollapsibleNavigation()

    def _setupCollapsibleNavigation(self):
        """配置可折叠的导航栏
        默认折叠只显示图标，点击汉堡菜单展开显示完整文本
        针对触摸屏优化：增大图标尺寸和间距"""
        try:
            nav = self.navigationInterface
            if not nav:
                return

            # 触摸屏优化的尺寸常量
            TOUCH_COMPACT_WIDTH = 60  # 折叠时的侧边栏宽度
            TOUCH_ITEM_HEIGHT = 55  # 导航项高度

            # 设置导航栏展开宽度（展开时显示图标+文本）
            nav.setExpandWidth(280)
            nav.setMinimumExpandWidth(280)

            # 隐藏返回按钮，避免与标题栏冲突
            nav.setReturnButtonVisible(False)

            if hasattr(nav, "panel") and nav.panel:
                panel = nav.panel

                # 增加顶部边距，避免汉堡菜单与标题栏冲突
                # 标题栏高度通常是48px
                panel.vBoxLayout.setContentsMargins(0, 48, 0, 5)

                # 修改面板的初始宽度
                panel.resize(TOUCH_COMPACT_WIDTH, panel.height())

                # 重写 collapse 方法以使用自定义宽度
                original_collapse = panel.collapse

                def custom_collapse():
                    from PySide6.QtCore import QPropertyAnimation, QRect, QSize
                    from qfluentwidgets.components.navigation import (
                        NavigationTreeWidgetBase,
                    )

                    if panel.expandAni.state() == QPropertyAnimation.Running:
                        return

                    for item in panel.items.values():
                        w = item.widget
                        if isinstance(w, NavigationTreeWidgetBase) and w.isRoot():
                            w.setExpanded(False)

                    panel.expandAni.setStartValue(
                        QRect(panel.pos(), QSize(panel.width(), panel.height()))
                    )
                    panel.expandAni.setEndValue(
                        QRect(panel.pos(), QSize(TOUCH_COMPACT_WIDTH, panel.height()))
                    )
                    panel.expandAni.setProperty("expand", False)
                    panel.expandAni.start()

                    panel.menuButton.setToolTip(panel.tr("Open Navigation"))

                panel.collapse = custom_collapse

                # 为所有导航项应用触摸屏优化的尺寸
                # 通过替换 setCompacted 方法来持久化自定义高度
                self._applyTouchOptimizedNavItems(panel)

                # 菜单按钮也需要增大高度
                if hasattr(panel, "menuButton") and panel.menuButton:
                    self._patchNavigationToolButton(panel.menuButton)

                # 强制更新布局
                panel.updateGeometry()
                nav.updateGeometry()

                # 延迟折叠导航栏，确保布局计算完成
                QTimer.singleShot(50, panel.collapse)

        except Exception as e:
            logger.debug(f"配置可折叠导航栏时出错: {e}")

    def _applyTouchOptimizedNavItems(self, panel):
        """为导航项应用触摸屏优化的尺寸

        通过替换每个导航项的 setCompacted 方法和 paintEvent 方法，确保在导航栏展开/折叠时
        保持自定义的高度，并使图标和指示器居中
        """
        from PySide6.QtGui import QPainter, QColor
        from PySide6.QtCore import Qt, QRectF, QMargins
        from qfluentwidgets.common.font import setFont
        from qfluentwidgets.common.icon import drawIcon
        from qfluentwidgets.common.config import isDarkTheme
        from qfluentwidgets.common.color import autoFallbackThemeColor

        # 触摸屏优化的尺寸常量
        TOUCH_ITEM_HEIGHT = 55  # 比默认36px更大，适合触摸
        TOUCH_COMPACT_WIDTH = 60  # 折叠时的宽度
        TOUCH_EXPAND_WIDTH = 280  # 展开时的宽度
        TOUCH_FONT_SIZE = 14  # 字体大小
        TOUCH_ICON_SIZE = 20  # 图标大小（默认16）
        TOUCH_INDICATOR_HEIGHT = 18  # 指示器高度（默认16）

        for item in panel.items.values():
            if hasattr(item, "widget") and item.widget:
                widget = item.widget

                # 获取实际需要绑定paintEvent的widget
                target_widget = (
                    widget.itemWidget
                    if hasattr(widget, "itemWidget") and widget.itemWidget
                    else widget
                )

                # 设置字体大小
                setFont(target_widget, TOUCH_FONT_SIZE)

                # 保存原始的 paintEvent 方法并创建自定义绘制
                original_paintEvent = target_widget.paintEvent

                def make_custom_paintEvent(w, height, icon_size, indicator_height):
                    def custom_paintEvent(e):
                        painter = QPainter(w)
                        painter.setRenderHints(
                            QPainter.Antialiasing
                            | QPainter.TextAntialiasing
                            | QPainter.SmoothPixmapTransform
                        )
                        painter.setPen(Qt.NoPen)

                        if w.isPressed:
                            painter.setOpacity(0.7)
                        if not w.isEnabled():
                            painter.setOpacity(0.4)

                        # 获取margins
                        m = (
                            w._margins()
                            if hasattr(w, "_margins")
                            else QMargins(0, 0, 0, 0)
                        )
                        pl, pr = m.left(), m.right()

                        # 计算垂直居中位置
                        icon_y = (height - icon_size) // 2
                        indicator_y = (height - indicator_height) // 2

                        c = 255 if isDarkTheme() else 0
                        globalRect = w.mapToGlobal(w.rect().topLeft())

                        # 绘制背景和指示器
                        can_draw_indicator = (
                            w._canDrawIndicator()
                            if hasattr(w, "_canDrawIndicator")
                            else w.isSelected
                        )
                        if can_draw_indicator:
                            painter.setBrush(QColor(c, c, c, 6 if w.isEnter else 10))
                            painter.drawRoundedRect(w.rect(), 5, 5)
                            # 绘制指示器 - 垂直居中
                            light_color = (
                                w.lightIndicatorColor
                                if hasattr(w, "lightIndicatorColor")
                                else QColor()
                            )
                            dark_color = (
                                w.darkIndicatorColor
                                if hasattr(w, "darkIndicatorColor")
                                else QColor()
                            )
                            painter.setBrush(
                                autoFallbackThemeColor(light_color, dark_color)
                            )
                            painter.drawRoundedRect(
                                pl, indicator_y, 3, indicator_height, 1.5, 1.5
                            )
                        elif w.isEnter and w.isEnabled():
                            painter.setBrush(QColor(c, c, c, 10))
                            painter.drawRoundedRect(w.rect(), 5, 5)

                        # 绘制图标 - 垂直居中，更大的尺寸
                        icon = w._icon if hasattr(w, "_icon") else None
                        if icon:
                            icon_x = (TOUCH_COMPACT_WIDTH - icon_size) // 2 + pl
                            drawIcon(
                                icon,
                                painter,
                                QRectF(icon_x, icon_y, icon_size, icon_size),
                            )

                        # 绘制文本（仅展开时）
                        if not w.isCompacted:
                            painter.setFont(w.font())
                            text_color = (
                                w.textColor()
                                if hasattr(w, "textColor")
                                else QColor(255, 255, 255)
                                if isDarkTheme()
                                else QColor(0, 0, 0)
                            )
                            painter.setPen(text_color)
                            text_x = TOUCH_COMPACT_WIDTH + pl
                            text = (
                                w._text
                                if hasattr(w, "_text")
                                else w.text()
                                if hasattr(w, "text")
                                else ""
                            )
                            painter.drawText(
                                QRectF(text_x, 0, w.width() - text_x - pr, height),
                                Qt.AlignVCenter,
                                text,
                            )

                        painter.end()

                    return custom_paintEvent

                # 替换 paintEvent
                target_widget.paintEvent = make_custom_paintEvent(
                    target_widget,
                    TOUCH_ITEM_HEIGHT,
                    TOUCH_ICON_SIZE,
                    TOUCH_INDICATOR_HEIGHT,
                )

                # 保存原始的 setCompacted 方法
                original_setCompacted = widget.setCompacted

                # 创建新的 setCompacted 方法，使用自定义尺寸
                def make_custom_setCompacted(
                    w, target_w, orig_method, height, compact_w, expand_w
                ):
                    def custom_setCompacted(isCompacted):
                        # 先调用原始方法以保持其他逻辑
                        orig_method(isCompacted)
                        # 然后覆盖尺寸为我们想要的值
                        if isCompacted:
                            w.setFixedSize(compact_w, height)
                        else:
                            w.setFixedSize(expand_w, height)
                        # 如果是 NavigationTreeWidget，还需要设置内部的 itemWidget
                        if target_w and target_w != w:
                            if isCompacted:
                                target_w.setFixedSize(compact_w, height)
                            else:
                                target_w.setFixedSize(expand_w, height)

                    return custom_setCompacted

                # 替换方法
                widget.setCompacted = make_custom_setCompacted(
                    widget,
                    target_widget if target_widget != widget else None,
                    original_setCompacted,
                    TOUCH_ITEM_HEIGHT,
                    TOUCH_COMPACT_WIDTH,
                    TOUCH_EXPAND_WIDTH,
                )

                # 立即应用当前状态的尺寸
                widget.setCompacted(widget.isCompacted)

    def _patchNavigationToolButton(self, button):
        """为导航工具按钮（如菜单按钮）应用触摸屏优化尺寸，并使图标居中"""
        from PySide6.QtGui import QPainter, QColor
        from PySide6.QtCore import Qt, QRectF
        from qfluentwidgets.common.icon import drawIcon
        from qfluentwidgets.common.config import isDarkTheme

        TOUCH_BUTTON_WIDTH = 60  # 按钮宽度与侧边栏一致
        TOUCH_BUTTON_HEIGHT = 55  # 按钮高度与导航项一致
        TOUCH_ICON_SIZE = 20  # 图标大小

        original_setCompacted = button.setCompacted

        def custom_setCompacted(isCompacted):
            original_setCompacted(isCompacted)
            button.setFixedSize(TOUCH_BUTTON_WIDTH, TOUCH_BUTTON_HEIGHT)

        button.setCompacted = custom_setCompacted
        button.setFixedSize(TOUCH_BUTTON_WIDTH, TOUCH_BUTTON_HEIGHT)

        # 重写 paintEvent 使图标居中
        original_paintEvent = button.paintEvent

        def custom_paintEvent(e):
            painter = QPainter(button)
            painter.setRenderHints(
                QPainter.Antialiasing | QPainter.SmoothPixmapTransform
            )
            painter.setPen(Qt.NoPen)

            if button.isPressed:
                painter.setOpacity(0.7)
            if not button.isEnabled():
                painter.setOpacity(0.4)

            # 绘制悬停背景
            if button.isEnter and button.isEnabled():
                c = 255 if isDarkTheme() else 0
                painter.setBrush(QColor(c, c, c, 10))
                painter.drawRoundedRect(button.rect(), 5, 5)

            # 绘制图标 - 居中
            icon = button._icon if hasattr(button, "_icon") else None
            if icon:
                icon_x = (TOUCH_BUTTON_WIDTH - TOUCH_ICON_SIZE) / 2
                icon_y = (TOUCH_BUTTON_HEIGHT - TOUCH_ICON_SIZE) / 2
                drawIcon(
                    icon,
                    painter,
                    QRectF(icon_x, icon_y, TOUCH_ICON_SIZE, TOUCH_ICON_SIZE),
                )

            painter.end()

        button.paintEvent = custom_paintEvent

    def _collapseNavigationPanel(self):
        """折叠导航栏面板"""
        try:
            nav = self.navigationInterface
            if nav and hasattr(nav, "panel") and nav.panel:
                if not nav.panel.isCollapsed():
                    nav.panel.collapse()
        except Exception as e:
            logger.debug(f"折叠导航栏时出错: {e}")

    def eventFilter(self, watched, event):
        """事件过滤器 - 监听子页面的点击事件，自动折叠导航栏"""
        if event.type() == QEvent.MouseButtonPress:
            self._collapseNavigationPanel()
        return super().eventFilter(watched, event)

    def mousePressEvent(self, event):
        """鼠标点击事件 - 点击主区域时自动折叠导航栏"""
        self._collapseNavigationPanel()
        super().mousePressEvent(event)

    def _toggle_float_window(self):
        if self.float_window.isVisible():
            self.float_window.hide()
        else:
            self.float_window.show()

    def _handle_main_page_requested(self, page_name: str):
        """处理主页面请求

        Args:
            page_name: 页面名称 ('roll_call_page', 'lottery_page' 或 'main_window')
        """
        logger.info(
            f"MainWindow._handle_main_page_requested: 收到主页面请求: {page_name}"
        )
        if page_name == "main_window":
            # 如果请求的是主窗口，直接显示主窗口
            logger.debug("MainWindow._handle_main_page_requested: 显示主窗口")
            self.show()
            self.raise_()
            self.activateWindow()
        elif (
            hasattr(self, f"{page_name}") and getattr(self, f"{page_name}") is not None
        ):
            logger.debug(
                f"MainWindow._handle_main_page_requested: 切换到页面: {page_name}"
            )
            self._show_and_switch_to(getattr(self, page_name))
        else:
            logger.warning(
                f"MainWindow._handle_main_page_requested: 请求的页面不存在: {page_name}"
            )

    def _handle_tray_action_requested(self, action: str):
        """处理托盘操作请求

        Args:
            action: 托盘操作类型 ('toggle_main_window', 'settings', 'float', 'restart', 'exit')
        """
        logger.debug(f"收到托盘操作请求: {action}")
        if action == "toggle_main_window":
            self.toggle_window()
        elif action == "settings":
            require_and_run(
                "open_settings",
                self,
                lambda: self.showSettingsRequested.emit("basicSettingsInterface"),
            )
        elif action == "float":
            self._toggle_float_window()
        elif action == "restart":
            require_and_run("restart", self, self.restart_app)
        elif action == "exit":
            require_and_run("exit", self, self.close_window_secrandom)
        else:
            logger.warning(f"未知的托盘操作: {action}")

    def _show_and_switch_to(self, page):
        if self.isMinimized():
            self.showNormal()
        self.show()
        self.activateWindow()
        self.raise_()
        self.switchTo(page)

    def closeEvent(self, event):
        """窗口关闭事件处理
        根据“后台驻留”设置决定是否真正关闭窗口"""
        resident = readme_settings_async("basic_settings", "background_resident")
        resident = True if resident is None else resident
        if resident:
            self.hide()
            event.ignore()

            # 保存当前窗口状态
            is_maximized = self.isMaximized()
            update_settings("window", "is_maximized", is_maximized)
            if is_maximized:
                pass
            else:
                self.save_window_size(self.width(), self.height())
        else:
            event.accept()

    def resizeEvent(self, event):
        """窗口大小变化事件处理
        检测窗口大小变化，但不启动尺寸记录倒计时，减少IO操作"""
        self.resize_timer.start(500)
        super().resizeEvent(event)

    def changeEvent(self, event):
        """窗口状态变化事件处理
        检测窗口最大化/恢复状态变化，保存正确的窗口大小"""
        # 检查是否是窗口状态变化
        if event.type() == QEvent.Type.WindowStateChange:
            is_currently_maximized = self.isMaximized()
            was_maximized = readme_settings_async("window", "is_maximized")

            # 如果最大化状态发生变化
            if is_currently_maximized != was_maximized:
                # 更新最大化状态
                update_settings("window", "is_maximized", is_currently_maximized)

                # 如果进入最大化，保存当前窗口大小作为最大化前的大小
                if is_currently_maximized:
                    # 获取正常状态下的窗口大小
                    normal_geometry = self.normalGeometry()
                    update_settings(
                        "window", "pre_maximized_width", normal_geometry.width()
                    )
                    update_settings(
                        "window", "pre_maximized_height", normal_geometry.height()
                    )
                # 如果退出最大化，恢复到最大化前的大小
                else:
                    pre_maximized_width = readme_settings_async(
                        "window", "pre_maximized_width"
                    )
                    pre_maximized_height = readme_settings_async(
                        "window", "pre_maximized_height"
                    )
                    # 延迟执行，确保在最大化状态完全退出后再调整大小
                    QTimer.singleShot(
                        100,
                        lambda: self.resize(pre_maximized_width, pre_maximized_height),
                    )

        super().changeEvent(event)

    def save_window_size(self, width, height):
        """保存窗口大小
        记录当前窗口尺寸，下次启动时自动恢复"""
        # 只有在非最大化状态下才保存窗口大小
        if not self.isMaximized():
            update_settings("window", "height", height)
            update_settings("window", "width", width)

    def toggle_window(self):
        """切换窗口显示状态
        在显示和隐藏状态之间切换窗口，切换时自动激活点名界面"""
        if self.isVisible():
            self.hide()
            if self.isMinimized():
                self.showNormal()
                self.activateWindow()
                self.raise_()
        else:
            if self.isMinimized():
                self.showNormal()
                self.activateWindow()
                self.raise_()
            else:
                self.show()
                self.activateWindow()
                self.raise_()

    def close_window_secrandom(self):
        """关闭窗口
        执行安全验证后关闭程序，释放所有资源"""
        try:
            loguru.logger.remove()
        except Exception as e:
            logger.error(f"日志系统关闭出错: {e}")

        QApplication.quit()
        sys.exit(0)

    def restart_app(self):
        """重启应用程序
        执行安全验证后重启程序，清理所有资源"""
        try:
            working_dir = str(get_app_root())

            filtered_args = [arg for arg in sys.argv if not arg.startswith("--")]

            startup_info = subprocess.STARTUPINFO()
            startup_info.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            subprocess.Popen(
                [sys.executable] + filtered_args,
                cwd=working_dir,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                | subprocess.DETACHED_PROCESS,
                startupinfo=startup_info,
            )
        except Exception as e:
            logger.error(f"启动新进程失败: {e}")
            return

        try:
            loguru.logger.remove()
        except Exception as e:
            logger.error(f"日志系统关闭出错: {e}")

        # 完全退出当前应用程序
        QApplication.quit()
        sys.exit(0)
