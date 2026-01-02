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

from app.common.IPC_URL.csharp_ipc_handler import CSharpIPCHandler
from app.common.shortcut import ShortcutManager
from app.tools.variable import MINIMUM_WINDOW_SIZE, APP_INIT_DELAY
from app.tools.path_utils import get_data_path, get_app_root
from app.tools.personalised import get_theme_icon
from app.tools.settings_access import get_safe_font_size
from app.Language.obtain_language import (
    get_content_name_async,
    readme_settings_async,
    update_settings,
)
from app.common.safety.verify_ops import require_and_run
from app.view.main.quick_draw_animation import QuickDrawAnimation
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
    classIslandDataReceived = Signal(dict)  # 接收ClassIsland数据信号

    def __init__(self, float_window: LevitationWindow, url_handler_instance=None):
        super().__init__()
        # 设置窗口对象名称，方便其他组件查找
        self.setObjectName("MainWindow")

        # 保存URL处理器实例引用
        self.url_handler_instance = url_handler_instance

        self.roll_call_page = None
        self.settingsInterface = None

        self.roll_call_page = None
        self.settingsInterface = None

        self.shortcut_manager = ShortcutManager(self)
        self._connect_shortcut_signals()
        self.shortcut_manager._init_shortcuts()
        self._setup_shortcut_settings_listener()

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
        self.url_command_handler.classIslandDataReceived.connect(
            self._handle_class_island_data
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
        self.float_window.quickDrawRequested.connect(self._handle_quick_draw)
        self.float_window.lotteryRequested.connect(
            lambda: self._show_and_switch_to(self.lottery_page)
        )

        QTimer.singleShot(APP_INIT_DELAY, lambda: (self.createSubInterface()))

    def restart_ipc_server(self, new_port: int):
        """重启IPC服务器

        Args:
            new_port: 新的端口号
        """
        logger.info(f"正在请求重启IPC服务器，新端口: {new_port}")

        # 使用保存的url_handler实例
        if self.url_handler_instance and hasattr(
            self.url_handler_instance, "url_ipc_handler"
        ):
            url_handler = self.url_handler_instance

            if url_handler and hasattr(url_handler, "url_ipc_handler"):
                # 停止当前的IPC服务器
                url_handler.url_ipc_handler.stop_ipc_server()
                logger.info("旧IPC服务器已停止")

                # 重新启动IPC服务器，使用新端口
                if url_handler.url_ipc_handler.start_ipc_server(new_port):
                    # 重新注册消息处理器
                    url_handler.url_ipc_handler.register_message_handler(
                        "url", url_handler._handle_ipc_url_message
                    )
                    url_handler.url_ipc_handler.register_message_handler(
                        "class_island_data",
                        url_handler._handle_ipc_class_island_message,
                    )
                    logger.info(f"IPC服务器已在端口 {new_port} 上重新启动")
                    return True
                else:
                    logger.error(f"IPC服务器在端口 {new_port} 上启动失败")
                    return False
            else:
                logger.error("无法访问URLHandler实例")
                return False
        else:
            logger.error("无法获取url_handler_instance")
            return False

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
        # 只有当设置不为"不显示"（值为2）时才添加到导航栏
        if roll_call_sidebar_pos is None or roll_call_sidebar_pos != 2:
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
        # 只有当设置不为"不显示"（值为2）时才添加到导航栏
        if lottery_sidebar_pos is None or lottery_sidebar_pos != 2:
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
        # 只有当设置不为"不显示"（值为2）时才添加到导航栏
        if history_sidebar_pos is None or history_sidebar_pos != 2:
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
        # 只有当设置不为"不显示"（值为2）时才添加到导航栏
        if settings_icon_pos is None or settings_icon_pos != 2:
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
            # 直接打开设置界面（预览模式），无需验证
            settings_item.clicked.connect(
                lambda: self.showSettingsRequested.emit("basicSettingsInterface")
            )
            settings_item.clicked.connect(lambda: self.switchTo(self.roll_call_page))

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
            # 直接打开设置界面（预览模式），无需验证
            self.showSettingsRequested.emit("basicSettingsInterface")
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

    def _handle_quick_draw(self):
        """处理闪抽请求
        点击悬浮窗中的闪抽按钮时调用
        """
        logger.debug("_handle_quick_draw: 收到闪抽请求")

        # 确保roll_call_page已经创建
        if not hasattr(self, "roll_call_page") or not self.roll_call_page:
            logger.error("_handle_quick_draw: roll_call_page未创建")
            return

        logger.debug("_handle_quick_draw: roll_call_page已创建")

        # 确保roll_call_widget已经创建
        roll_call_page = self.roll_call_page
        roll_call_widget = None

        # 尝试获取roll_call_widget
        if (
            hasattr(roll_call_page, "roll_call_widget")
            and roll_call_page.roll_call_widget
        ):
            roll_call_widget = roll_call_page.roll_call_widget
            logger.debug("_handle_quick_draw: roll_call_widget已创建")
        else:
            # 尝试直接获取contentWidget
            if (
                hasattr(roll_call_page, "contentWidget")
                and roll_call_page.contentWidget
            ):
                roll_call_widget = roll_call_page.contentWidget
                logger.debug("_handle_quick_draw: 直接获取contentWidget成功")
            else:
                # 尝试创建contentWidget
                logger.debug("_handle_quick_draw: 尝试创建contentWidget")
                roll_call_page.create_content()
                QApplication.processEvents()

                # 再次尝试获取
                if (
                    hasattr(roll_call_page, "roll_call_widget")
                    and roll_call_page.roll_call_widget
                ):
                    roll_call_widget = roll_call_page.roll_call_widget
                    logger.debug(
                        "_handle_quick_draw: 创建contentWidget后获取roll_call_widget成功"
                    )
                elif (
                    hasattr(roll_call_page, "contentWidget")
                    and roll_call_page.contentWidget
                ):
                    roll_call_widget = roll_call_page.contentWidget
                    logger.debug(
                        "_handle_quick_draw: 创建contentWidget后获取contentWidget成功"
                    )
                else:
                    logger.error("_handle_quick_draw: 无法创建或获取roll_call_widget")
                    return

        logger.debug("_handle_quick_draw: 成功获取roll_call_widget")

        # 保存当前设置
        original_count = roll_call_widget.current_count
        original_list_index = roll_call_widget.list_combobox.currentIndex()
        original_range_index = roll_call_widget.range_combobox.currentIndex()
        original_gender_index = roll_call_widget.gender_combobox.currentIndex()

        try:
            # 设置抽取数量为1
            roll_call_widget.current_count = 1
            roll_call_widget.count_label.setText("1")

            # 确保所有下拉框都有内容且选择第一项
            if roll_call_widget.list_combobox.count() > 0:
                roll_call_widget.list_combobox.setCurrentIndex(0)
                # 触发班级变化事件，更新相关数据
                roll_call_widget.on_class_changed()

            if roll_call_widget.range_combobox.count() > 0:
                roll_call_widget.range_combobox.setCurrentIndex(0)

            if roll_call_widget.gender_combobox.count() > 0:
                roll_call_widget.gender_combobox.setCurrentIndex(0)

            # 触发筛选变化事件，更新相关数据
            roll_call_widget.on_filter_changed()

            # 确保所有数据已更新
            QApplication.processEvents()

            # 获取闪抽专用设置
            quick_draw_settings = {
                "draw_mode": readme_settings_async("quick_draw_settings", "draw_mode"),
                "half_repeat": readme_settings_async(
                    "quick_draw_settings", "half_repeat"
                ),
                "font_size": get_safe_font_size("quick_draw_settings", "font_size"),
                "display_format": readme_settings_async(
                    "quick_draw_settings", "display_format"
                ),
                "animation": readme_settings_async("quick_draw_settings", "animation"),
                "animation_interval": readme_settings_async(
                    "quick_draw_settings", "animation_interval"
                ),
                "autoplay_count": readme_settings_async(
                    "quick_draw_settings", "autoplay_count"
                ),
                "animation_color_theme": readme_settings_async(
                    "quick_draw_settings", "animation_color_theme"
                ),
                "student_image": readme_settings_async(
                    "quick_draw_settings", "student_image"
                ),
                "show_random": readme_settings_async(
                    "quick_draw_settings", "show_random"
                ),
                "default_class": readme_settings_async(
                    "quick_draw_settings", "default_class"
                ),
            }

            # 创建闪抽动画实例
            quick_draw_animation = QuickDrawAnimation(roll_call_widget)

            # 执行闪抽动画
            quick_draw_animation.execute_quick_draw(quick_draw_settings)

        finally:
            # 恢复原始设置
            roll_call_widget.current_count = original_count
            roll_call_widget.count_label.setText(str(original_count))

            # 恢复原始下拉框索引
            if roll_call_widget.list_combobox.count() > 0:
                roll_call_widget.list_combobox.setCurrentIndex(original_list_index)
                # 触发班级变化事件，更新相关数据
                roll_call_widget.on_class_changed()

            if roll_call_widget.range_combobox.count() > 0:
                roll_call_widget.range_combobox.setCurrentIndex(original_range_index)

            if roll_call_widget.gender_combobox.count() > 0:
                roll_call_widget.gender_combobox.setCurrentIndex(original_gender_index)

            # 触发筛选变化事件，更新相关数据
            roll_call_widget.on_filter_changed()

            # 确保所有数据已更新
            QApplication.processEvents()

    def closeEvent(self, event):
        """窗口关闭事件处理
        根据"后台驻留"设置决定是否真正关闭窗口"""
        resident = readme_settings_async("basic_settings", "background_resident")
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
        检测窗口大小变化，启动尺寸记录倒计时，避免频繁IO操作"""
        # 每次窗口大小变化时重新启动定时器，确保在窗口大小稳定后才保存
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
        # 检查是否启用了自动保存窗口大小功能
        auto_save_enabled = readme_settings_async(
            "basic_settings", "auto_save_window_size"
        )

        if auto_save_enabled:
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
        self.cleanup_shortcuts()
        try:
            loguru.logger.remove()
        except Exception as e:
            logger.error(f"日志系统关闭出错: {e}")

        QApplication.quit()
        CSharpIPCHandler.instance().stop_ipc_client()
        sys.exit(0)

    def cleanup_shortcuts(self):
        """清理快捷键"""
        if hasattr(self, "shortcut_manager"):
            self.shortcut_manager.cleanup()

    def _connect_shortcut_signals(self):
        """连接快捷键管理器的信号"""
        logger.debug("开始连接快捷键信号...")

        self.shortcut_manager.openRollCallPageRequested.connect(
            lambda: self._show_and_switch_to(self.roll_call_page)
        )
        logger.debug("快捷键信号已连接: openRollCallPageRequested")

        self.shortcut_manager.useQuickDrawRequested.connect(self._handle_quick_draw)
        logger.debug("快捷键信号已连接: useQuickDrawRequested")

        self.shortcut_manager.openLotteryPageRequested.connect(
            lambda: self._show_and_switch_to(self.lottery_page)
        )
        logger.debug("快捷键信号已连接: openLotteryPageRequested")

        self.shortcut_manager.increaseRollCallCountRequested.connect(
            self._handle_increase_roll_call_count
        )
        logger.debug("快捷键信号已连接: increaseRollCallCountRequested")

        self.shortcut_manager.decreaseRollCallCountRequested.connect(
            self._handle_decrease_roll_call_count
        )
        logger.debug("快捷键信号已连接: decreaseRollCallCountRequested")

        self.shortcut_manager.increaseLotteryCountRequested.connect(
            self._handle_increase_lottery_count
        )
        logger.debug("快捷键信号已连接: increaseLotteryCountRequested")

        self.shortcut_manager.decreaseLotteryCountRequested.connect(
            self._handle_decrease_lottery_count
        )
        logger.debug("快捷键信号已连接: decreaseLotteryCountRequested")

        self.shortcut_manager.startRollCallRequested.connect(
            self._handle_start_roll_call
        )
        logger.debug("快捷键信号已连接: startRollCallRequested")

        self.shortcut_manager.startLotteryRequested.connect(self._handle_start_lottery)
        logger.debug("快捷键信号已连接: startLotteryRequested")

        logger.debug("所有快捷键信号连接完成")

    def _handle_increase_roll_call_count(self):
        """处理增加点名人数快捷键"""
        if hasattr(self, "roll_call_page") and self.roll_call_page:
            if (
                hasattr(self.roll_call_page, "contentWidget")
                and self.roll_call_page.contentWidget
            ):
                self.roll_call_page.contentWidget.update_count(1)

    def _handle_decrease_roll_call_count(self):
        """处理减少点名人数快捷键"""
        if hasattr(self, "roll_call_page") and self.roll_call_page:
            if (
                hasattr(self.roll_call_page, "contentWidget")
                and self.roll_call_page.contentWidget
            ):
                self.roll_call_page.contentWidget.update_count(-1)

    def _handle_increase_lottery_count(self):
        """处理增加抽奖人数快捷键"""
        if hasattr(self, "lottery_page") and self.lottery_page:
            if (
                hasattr(self.lottery_page, "contentWidget")
                and self.lottery_page.contentWidget
            ):
                self.lottery_page.contentWidget.update_count(1)

    def _handle_decrease_lottery_count(self):
        """处理减少抽奖人数快捷键"""
        if hasattr(self, "lottery_page") and self.lottery_page:
            if (
                hasattr(self.lottery_page, "contentWidget")
                and self.lottery_page.contentWidget
            ):
                self.lottery_page.contentWidget.update_count(-1)

    def _handle_start_roll_call(self):
        """处理开始点名快捷键"""
        if hasattr(self, "roll_call_page") and self.roll_call_page:
            if (
                hasattr(self.roll_call_page, "contentWidget")
                and self.roll_call_page.contentWidget
            ):
                self.roll_call_page.contentWidget.start_draw()

    def _handle_start_lottery(self):
        """处理开始抽奖快捷键"""
        if hasattr(self, "lottery_page") and self.lottery_page:
            if (
                hasattr(self.lottery_page, "contentWidget")
                and self.lottery_page.contentWidget
            ):
                self.lottery_page.contentWidget.start_draw()

    def _setup_shortcut_settings_listener(self):
        """设置快捷键设置监听器，监听快捷键设置变化"""
        from app.tools.settings_access import get_settings_signals

        settings_signals = get_settings_signals()
        settings_signals.settingChanged.connect(self._on_shortcut_settings_changed)

    def _on_shortcut_settings_changed(
        self, first_level_key: str, second_level_key: str, value
    ):
        """当快捷键设置发生变化时的处理函数"""
        logger.debug(f"快捷键设置变化: {first_level_key}.{second_level_key} = {value}")

        if first_level_key == "shortcut_settings":
            if second_level_key == "enable_shortcut":
                logger.debug(f"快捷键启用状态变化: {value}")
                self.shortcut_manager.set_enabled(value)
            else:
                config_key = second_level_key
                shortcut_str = value if value else ""
                logger.debug(f"快捷键更新: {config_key} = {shortcut_str}")
                self.shortcut_manager.update_shortcut(config_key, shortcut_str)

    def restart_app(self):
        """重启应用程序
        执行安全验证后重启程序，清理所有资源"""
        try:
            working_dir = get_app_root()

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

        self.cleanup_shortcuts()

        try:
            loguru.logger.remove()
        except Exception as e:
            logger.error(f"日志系统关闭出错: {e}")

        # 完全退出当前应用程序
        QApplication.quit()
        CSharpIPCHandler.instance().stop_ipc_client()
        sys.exit(0)

    def _handle_class_island_data(self, class_island_data: dict):
        """处理ClassIsland数据
        接收并处理来自ClassIsland软件的课程表信息

        Args:
            class_island_data: 包含课程表信息的字典
        """
        logger.info("收到ClassIsland数据")
        logger.debug(f"ClassIsland数据内容: {class_island_data}")

        # 提取并处理ClassIsland数据
        try:
            # 当前所处时间点的科目
            current_subject = class_island_data.get("CurrentSubject")
            # 下一节课的科目
            next_class_subject = class_island_data.get("NextClassSubject")
            # 当前时间点状态
            current_state = class_island_data.get("CurrentState")
            # 当前所处的时间点
            current_time_layout_item = class_island_data.get("CurrentTimeLayoutItem")
            # 当前加载的课表
            current_class_plan = class_island_data.get("CurrentClassPlan")
            # 下一个课间休息类型的时间点
            next_breaking_time_layout_item = class_island_data.get(
                "NextBreakingTimeLayoutItem"
            )
            # 下一个上课类型的时间点
            next_class_time_layout_item = class_island_data.get(
                "NextClassTimeLayoutItem"
            )
            # 当前所处时间点的索引
            current_selected_index = class_island_data.get("CurrentSelectedIndex")
            # 距离上课剩余时间
            on_class_left_time = class_island_data.get("OnClassLeftTime")
            # 距下课剩余时间
            on_breaking_time_left_time = class_island_data.get("OnBreakingTimeLeftTime")
            # 是否启用课表
            is_class_plan_enabled = class_island_data.get("IsClassPlanEnabled")
            # 是否已加载课表
            is_class_plan_loaded = class_island_data.get("IsClassPlanLoaded")
            # 是否已确定当前时间点
            is_lesson_confirmed = class_island_data.get("IsLessonConfirmed")

            # 检查是否启用了ClassIsland数据源
            use_class_island_source = readme_settings_async(
                "time_settings", "class_island_source_enabled", False
            )

            if (
                use_class_island_source
                and is_class_plan_enabled
                and is_class_plan_loaded
            ):
                # 使用ClassIsland数据来判断是否为课间时间
                # 根据当前状态判断当前是否为课间时间
                is_break_time = self._is_class_island_break_time(
                    current_state, current_time_layout_item
                )

                # 更新全局状态以反映当前是否为课间时间
                # 注意：这将影响到整个应用的课间禁用行为
                self._update_class_island_break_status(is_break_time, current_state)

            # 这里可以添加根据ClassIsland数据更新UI的逻辑
            # 例如：显示当前课程信息、更新课程表显示等
            # 目前只是记录日志，后续可以根据需要添加具体功能

        except Exception as e:
            logger.error(f"处理ClassIsland数据时出错: {e}")

    def _is_class_island_break_time(
        self, current_state: str, current_time_layout_item: dict
    ) -> bool:
        """根据ClassIsland数据判断是否为课间时间

        Args:
            current_state: 当前时间点状态
            current_time_layout_item: 当前时间布局项

        Returns:
            bool: 如果当前是课间时间返回True，否则返回False
        """
        if not current_state:
            return False

        # 通常课间时间的状态包含 "break", "rest", "interval", "free" 等关键词
        # 或者当前状态明确表示是课间时间
        current_state_lower = current_state.lower()

        # 检查状态是否表明当前是课间时间
        break_indicators = [
            "break",
            "rest",
            "interval",
            "free",
            "recess",
            "pause",
            "课间",
            "休息",
            "间歇",
            "自由",
            "breaktime",
            "break_time",
            "Breaking",
        ]

        for indicator in break_indicators:
            if indicator in current_state_lower:
                return True

        # 如果时间布局项存在，可以进一步检查其类型
        if current_time_layout_item and isinstance(current_time_layout_item, dict):
            time_type = current_time_layout_item.get("Type", "")
            time_name = current_time_layout_item.get("Name", "")

            # 检查时间布局项的类型或名称是否表明是课间时间
            time_type_lower = time_type.lower()
            time_name_lower = time_name.lower()

            for indicator in break_indicators:
                if indicator in time_type_lower or indicator in time_name_lower:
                    return True

        return False

    def _update_class_island_break_status(
        self, is_break_time: bool, current_state: str
    ):
        """更新ClassIsland课间状态

        Args:
            is_break_time: 是否为课间时间
            current_state: 当前状态
        """
        logger.debug(
            f"ClassIsland课间状态更新: {'课间时间' if is_break_time else '上课时间'} (状态: {current_state})"
        )

        # 这里可以添加逻辑来更新应用的课间禁用状态
        # 例如，可以设置一个全局标志或更新设置
        try:
            # 保存当前ClassIsland的课间状态
            from app.tools.settings_access import update_settings

            update_settings(
                "time_settings", "current_class_island_break_status", is_break_time
            )
            update_settings("time_settings", "last_class_island_state", current_state)
        except Exception as e:
            logger.error(f"更新ClassIsland课间状态失败: {e}")
