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
from qfluentwidgets import MSFluentWindow, NavigationItemPosition

from app.tools.variable import MINIMUM_WINDOW_SIZE, APP_INIT_DELAY
from app.tools.path_utils import get_resources_path
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
class MainWindow(MSFluentWindow):
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
            QIcon(str(get_resources_path("assets/icon", "secrandom-icon-paper.png")))
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
            "设置",
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

        # 调整侧边栏宽度以适应多语言文本
        self._adjustNavigationBarWidth()

    def _adjustNavigationBarWidth(self):
        """调整导航栏宽度以适应多语言文本，按钮保持正方形，长文本换行"""
        try:
            nav = self.navigationInterface
            if not nav or not hasattr(nav, "buttons"):
                return

            # 设置按钮的正方形尺寸
            button_size = 80  # 正方形按钮的边长

            buttons = nav.buttons()
            for button in buttons:
                button.setFixedSize(button_size, button_size)
                # 重写绘制方法使图标和文本整体居中
                self._patchButtonDraw(button, button_size)

            # 设置导航栏宽度
            nav_padding = 8
            nav_width = button_size + nav_padding
            nav.setFixedWidth(nav_width)

        except Exception as e:
            logger.debug(f"调整导航栏宽度时出错: {e}")

    def _patchButtonDraw(self, button, button_size):
        """修补按钮的绘制方法，使图标和文本整体垂直居中"""
        from PySide6.QtCore import QRectF, Qt, QRect
        from PySide6.QtGui import QPainter, QFontMetrics
        from qfluentwidgets.common.icon import drawIcon, FluentIconBase
        from qfluentwidgets.common.color import autoFallbackThemeColor
        from qfluentwidgets.common.config import isDarkTheme

        def centered_draw_icon(painter: QPainter):
            if (button.isPressed or not button.isEnter) and not button.isSelected:
                painter.setOpacity(0.6)
            if not button.isEnabled():
                painter.setOpacity(0.4)

            # 计算文本需要的行数和高度
            text = button.text()
            fm = QFontMetrics(button.font())
            text_width = button_size - 8  # 文本区域宽度

            # 计算文本换行后的高度
            text_rect = QRect(0, 0, text_width, 1000)
            bounding = fm.boundingRect(
                text_rect, Qt.AlignHCenter | Qt.TextWordWrap, text
            )
            text_height = bounding.height()

            # 计算整体内容高度（图标 + 间距 + 文本）
            icon_size = 20
            spacing = 4  # 图标和文本之间的间距
            total_height = icon_size + spacing + text_height

            # 计算垂直居中的起始位置
            start_y = (button_size - total_height) / 2
            icon_x = (button_size - icon_size) / 2
            icon_y = start_y

            if hasattr(button, "iconAni") and not button._isSelectedTextVisible:
                icon_y += button.iconAni.offset

            # 保存计算结果供 _drawText 使用
            button._calculated_text_top = start_y + icon_size + spacing

            rect = QRectF(icon_x, icon_y, icon_size, icon_size)

            selectedIcon = button._selectedIcon or button._icon

            if isinstance(selectedIcon, FluentIconBase) and button.isSelected:
                color = autoFallbackThemeColor(
                    button.lightSelectedColor, button.darkSelectedColor
                )
                selectedIcon.render(painter, rect, fill=color.name())
            elif button.isSelected:
                drawIcon(selectedIcon, painter, rect)
            else:
                drawIcon(button._icon, painter, rect)

        def wrapped_draw_text(painter: QPainter):
            if button.isSelected and not button._isSelectedTextVisible:
                return

            if button.isSelected:
                painter.setPen(
                    autoFallbackThemeColor(
                        button.lightSelectedColor, button.darkSelectedColor
                    )
                )
            else:
                painter.setPen(Qt.white if isDarkTheme() else Qt.black)

            painter.setFont(button.font())

            text = button.text()

            # 使用之前计算的文本顶部位置
            text_top = getattr(button, "_calculated_text_top", 36)
            text_rect = QRect(
                4, int(text_top), button_size - 8, button_size - int(text_top)
            )

            # 使用 Qt 的自动换行功能
            painter.drawText(
                text_rect,
                Qt.AlignHCenter | Qt.AlignTop | Qt.TextWordWrap,
                text,
            )

        from app.tools.button_draw_utils import centered_draw_background

        button._drawBackground = lambda painter: centered_draw_background(
            button, painter, button_size
        )
        button._drawIcon = centered_draw_icon
        button._drawText = wrapped_draw_text

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
