# ==================================================
# 导入库
# ==================================================

from PySide6.QtWidgets import QApplication, QSystemTrayIcon
from PySide6.QtGui import QIcon, QCursor
from PySide6.QtCore import QTimer, QEvent, QPoint, Signal
from qfluentwidgets import Action, SystemTrayMenu
from loguru import logger

from app.tools.variable import MENU_AUTO_CLOSE_TIMEOUT
from app.common.safety.verify_ops import require_and_run
from app.tools.path_utils import get_data_path
from app.Language.obtain_language import readme_settings_async, get_content_name_async
from app.common.IPC_URL.url_command_handler import URLCommandHandler


# ==================================================
# 托盘图标管理器类
# ==================================================
class Tray(QSystemTrayIcon):
    """系统托盘图标管理器

    负责管理托盘图标和菜单，提供右键菜单功能。
    继承自QSystemTrayIcon以简化实现。
    """

    showSettingsRequested = Signal(str)  # 请求显示设置页面
    showSettingsRequestedAbout = Signal()
    showFloatWindowRequested = Signal()
    showTrayActionRequested = Signal(str)  # 请求执行托盘操作

    def __init__(self, parent=None):
        """
        初始化系统托盘图标

        Args:
            parent: 父窗口对象，通常为主窗口
        """
        super().__init__(parent)
        self.main_window = parent
        self.setIcon(
            QIcon(str(get_data_path("assets/icon", "secrandom-icon-paper.png")))
        )
        self.setToolTip("SecRandom")
        self.activated.connect(self._on_tray_activated)

        # 初始化URL命令处理器
        self.url_command_handler = URLCommandHandler(self)
        self.url_command_handler.showTrayActionRequested.connect(
            self._handle_tray_action_requested
        )

        # 初始化菜单自动关闭定时器
        self._init_menu_timer()

        # 连接信号
        self.showTrayActionRequested.connect(self._handle_tray_action_requested)

    def _init_menu_timer(self):
        """初始化菜单自动关闭定时器"""
        self.menu_timer = QTimer(self)
        self.menu_timer.setSingleShot(True)
        self.menu_timer.timeout.connect(self._on_menu_timeout)

    def _on_tray_activated(self, reason):
        """处理托盘图标点击事件
        当用户点击托盘图标时，显示菜单"""
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.Context,
        ):
            # 每次都创建全新的菜单
            self._create_fresh_menu()

            pos = QCursor.pos()
            screen = QApplication.primaryScreen().availableGeometry()
            menu_size = self.tray_menu.sizeHint()
            if pos.x() + menu_size.width() > screen.right():
                adjusted_x = pos.x() - menu_size.width()
            else:
                adjusted_x = pos.x()
            if pos.y() + menu_size.height() > screen.bottom():
                adjusted_y = pos.y() - menu_size.height()
            else:
                adjusted_y = pos.y()
            adjusted_x = max(
                screen.left(), min(adjusted_x, screen.right() - menu_size.width())
            )
            adjusted_y = max(
                screen.top(), min(adjusted_y, screen.bottom() - menu_size.height())
            )
            adjusted_pos = QPoint(adjusted_x, adjusted_y - 35)
            self.tray_menu.popup(adjusted_pos)
            self.menu_timer.start(MENU_AUTO_CLOSE_TIMEOUT)

    def _create_fresh_menu(self):
        """创建全新的托盘菜单"""
        # 如果已有菜单，先删除
        if hasattr(self, "tray_menu"):
            self.tray_menu.deleteLater()

        # 创建新菜单
        self.tray_menu = SystemTrayMenu(parent=self.main_window)

        # 关于SecRandom
        self.about_action = Action(
            "SecRandom", triggered=lambda: self.showSettingsRequestedAbout.emit()
        )
        self.tray_menu.addAction(self.about_action)

        self.tray_menu.addSeparator()

        # 收集需要显示的菜单项
        menu_items = []

        # 主界面控制
        show_hide_main_window = readme_settings_async(
            "tray_management", "show_hide_main_window"
        )
        if show_hide_main_window is not False:
            toggle_main_window_action = Action(
                get_content_name_async("tray_management", "show_hide_main_window"),
                triggered=self.main_window.toggle_window,
            )
            menu_items.append(toggle_main_window_action)

        # 设置界面
        open_settings = readme_settings_async("tray_management", "open_settings")
        if open_settings is not False:
            open_settings_action = Action(
                get_content_name_async("tray_management", "open_settings"),
                triggered=lambda: self.showSettingsRequested.emit(
                    "basicSettingsInterface"
                ),
            )
            menu_items.append(open_settings_action)

        # 暂时显示/隐藏浮窗
        show_hide_float_window = readme_settings_async(
            "tray_management", "show_hide_float_window"
        )
        if show_hide_float_window is not False:
            show_hide_float_window_action = Action(
                get_content_name_async("tray_management", "show_hide_float_window"),
                triggered=lambda: require_and_run(
                    "show_hide_floating_window",
                    self.main_window,
                    self.main_window._toggle_float_window,
                ),
            )
            menu_items.append(show_hide_float_window_action)

        if (
            show_hide_main_window or open_settings or show_hide_float_window
        ):  # 至少一个菜单项
            separator = "separator"
            menu_items.append(separator)

        # 重启
        restart = readme_settings_async("tray_management", "restart")
        if restart is not False:
            restart_action = Action(
                get_content_name_async("tray_management", "restart"),
                triggered=lambda: require_and_run(
                    "restart", self.main_window, self.main_window.restart_app
                ),
            )
            menu_items.append(restart_action)

        # 退出
        exit_setting = readme_settings_async("tray_management", "exit")
        if exit_setting is not False:
            exit_action = Action(
                get_content_name_async("tray_management", "exit"),
                triggered=lambda: require_and_run(
                    "exit", self.main_window, self.main_window.close_window_secrandom
                ),
            )
            menu_items.append(exit_action)

        # 添加菜单项（不使用分隔符）
        for item in menu_items:
            if item == "separator":  # 分割线
                self.tray_menu.addSeparator()
            else:
                self.tray_menu.addAction(item)

        self.tray_menu.installEventFilter(self)

    def _on_menu_timeout(self):
        """菜单超时自动关闭
        当用户5秒内没有操作菜单时，自动关闭菜单"""
        if self.tray_menu.isVisible():
            self.tray_menu.close()

    def eventFilter(self, obj, event):
        """事件过滤器

        监听菜单相关事件，当用户点击菜单外部时自动关闭菜单。

        Args:
            obj: 事件对象
            event: 事件类型

        Returns:
            bool: 是否拦截事件
        """
        if obj == self.tray_menu:
            if event.type() in (QEvent.Type.MouseButtonPress, QEvent.Type.Hide):
                self.menu_timer.stop()
        if event.type() == QEvent.Type.MouseButtonPress and self.tray_menu.isVisible():
            click_pos = event.globalPosition().toPoint()
            menu_rect = self.tray_menu.geometry()
            if not menu_rect.contains(click_pos):
                self.tray_menu.close()
                self.menu_timer.stop()
                return True
        return super().eventFilter(obj, event)

    def show_tray_icon(self):
        """显示托盘图标"""
        if not self.isVisible():
            self.show()

    def _handle_tray_action_requested(self, action: str):
        """处理托盘操作请求

        Args:
            action: 托盘操作类型 ('toggle_main_window', 'settings', 'float', 'restart', 'exit')
        """
        logger.debug(f"托盘收到操作请求: {action}")
        if action == "toggle_main_window":
            # 切换主窗口显示状态
            self.main_window.toggle_window()
        elif action == "settings":
            # 打开设置页面
            self.showSettingsRequested.emit("basicSettingsInterface")
        elif action == "float":
            # 切换浮窗显示状态
            self.showFloatWindowRequested.emit()
        elif action == "restart":
            # 重启应用程序
            require_and_run("restart", self.main_window, self.main_window.restart_app)
        elif action == "exit":
            # 退出应用程序
            require_and_run(
                "exit", self.main_window, self.main_window.close_window_secrandom
            )
        else:
            logger.warning(f"未知的托盘操作: {action}")
