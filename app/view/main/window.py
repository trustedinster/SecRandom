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
        self.float_window.quickDrawRequested.connect(self._handle_quick_draw)
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
