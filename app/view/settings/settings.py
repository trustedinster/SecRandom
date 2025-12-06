# ==================================================
# 导入库
# ==================================================

from loguru import logger
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtGui import QIcon
from PySide6.QtCore import QTimer, QEvent, Signal
from qfluentwidgets import FluentWindow, NavigationItemPosition

from app.tools.variable import *
from app.tools.path_utils import *
from app.tools.personalised import *
from app.tools.settings_default import *
from app.tools.settings_access import *
from app.Language.obtain_language import *
from app.common.IPC_URL.url_command_handler import URLCommandHandler


# ==================================================
# 主窗口类
# ==================================================
class SettingsWindow(FluentWindow):
    """主窗口类
    程序的核心控制中心"""

    showSettingsRequested = Signal(str)  # 请求显示设置页面
    showSettingsRequestedAbout = Signal()
    showMainPageRequested = Signal(str)  # 请求显示主页面

    def __init__(self, parent=None):
        super().__init__()
        self.setObjectName("settingWindow")
        self.parent = parent

        # 初始化变量
        self._init_interface_variables()

        # resize_timer的初始化
        self.resize_timer = QTimer(self)
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(
            lambda: self.save_window_size(self.width(), self.height())
        )

        # 设置窗口属性
        window_width = 800
        window_height = 600
        self.resize(window_width, window_height)
        self.setMinimumSize(MINIMUM_WINDOW_SIZE[0], MINIMUM_WINDOW_SIZE[1])
        self.setWindowTitle("SecRandom")
        self.setWindowIcon(
            QIcon(str(get_data_path("assets/icon", "secrandom-icon-paper.png")))
        )

        # 初始化URL命令处理器
        self.url_command_handler = URLCommandHandler(self)
        self.url_command_handler.showSettingsRequested.connect(
            self._handle_settings_page_request
        )

        # 窗口定位
        self._position_window()

        # 启动页面
        self.splashScreen = SplashScreen(self.windowIcon(), self)
        self.splashScreen.setIconSize(QSize(256, 256))
        self.show()

        # 初始化子界面
        QTimer.singleShot(APP_INIT_DELAY, lambda: (self.createSubInterface()))

    def _init_interface_variables(self):
        """初始化界面变量"""
        interface_names = [
            "basicSettingsInterface",
            "listManagementInterface",
            "extractionSettingsInterface",
            "floatingWindowManagementInterface",
            "notificationSettingsInterface",
            "safetySettingsInterface",
            "customSettingsInterface",
            "voiceSettingsInterface",
            "historyInterface",
            "moreSettingsInterface",
            "updateInterface",
            "aboutInterface",
        ]

        for name in interface_names:
            setattr(self, name, None)

    def _position_window(self):
        """窗口定位
        根据屏幕尺寸和用户设置自动计算最佳位置"""
        is_maximized = readme_settings_async("settings", "is_maximized")
        if is_maximized:
            pre_maximized_width = readme_settings_async(
                "settings", "pre_maximized_width"
            )
            pre_maximized_height = readme_settings_async(
                "settings", "pre_maximized_height"
            )
            self.resize(pre_maximized_width, pre_maximized_height)
            self._center_window()
            QTimer.singleShot(APP_INIT_DELAY, self.showMaximized)
        else:
            setting_window_width = readme_settings_async("settings", "width")
            setting_window_height = readme_settings_async("settings", "height")
            self.resize(setting_window_width, setting_window_height)
            self._center_window()

    def _center_window(self):
        """窗口定位-正常居中显示
        窗口大小设置完成后，将窗口居中显示在屏幕上"""
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

    def _handle_main_page_requested(self, page_name: str):
        """处理主页面请求

        Args:
            page_name: 页面名称
        """
        logger.debug(f"设置窗口收到主页面请求: {page_name}")

        # 处理设置页面特定的页面请求
        if page_name.startswith("settings_"):
            self._handle_settings_page_request(page_name)
        else:
            # 设置窗口通常不需要处理主页面请求，可以转发给父窗口或记录日志
            logger.debug(f"设置窗口转发主页面请求: {page_name}")
            # 如果有父窗口，可以转发信号
            if hasattr(self, "parent") and self.parent:
                self.showMainPageRequested.emit(page_name)

    def _handle_settings_page_request(self, page_name: str):
        """处理设置页面请求

        Args:
            page_name: 设置页面名称 (如 'settings_basic', 'settings_about' 或 'basicSettingsInterface' 等)
        """
        logger.debug(f"处理设置页面请求: {page_name}")

        # 映射设置页面名称到对应的界面属性
        page_mapping = {
            "settings_basic": ("basicSettingsInterface", "basic_settings_item"),
            "settings_list": ("listManagementInterface", "list_management_item"),
            "settings_extraction": (
                "extractionSettingsInterface",
                "extraction_settings_item",
            ),
            "settings_floating": (
                "floatingWindowManagementInterface",
                "floating_window_management_item",
            ),
            "settings_notification": (
                "notificationSettingsInterface",
                "notification_settings_item",
            ),
            "settings_safety": ("safetySettingsInterface", "safety_settings_item"),
            "settings_voice": ("voiceSettingsInterface", "voice_settings_item"),
            "settings_history": ("historyInterface", "history_item"),
            "settings_more": ("moreSettingsInterface", "more_settings_item"),
            "settings_update": ("updateInterface", "update_item"),
            "settings_about": ("aboutInterface", "about_item"),
        }

        # 直接映射，从界面名称到对应的界面属性和导航项属性
        direct_interface_mapping = {
            "basicSettingsInterface": ("basicSettingsInterface", "basic_settings_item"),
            "listManagementInterface": (
                "listManagementInterface",
                "list_management_item",
            ),
            "extractionSettingsInterface": (
                "extractionSettingsInterface",
                "extraction_settings_item",
            ),
            "floatingWindowManagementInterface": (
                "floatingWindowManagementInterface",
                "floating_window_management_item",
            ),
            "notificationSettingsInterface": (
                "notificationSettingsInterface",
                "notification_settings_item",
            ),
            "safetySettingsInterface": (
                "safetySettingsInterface",
                "safety_settings_item",
            ),
            "voiceSettingsInterface": ("voiceSettingsInterface", "voice_settings_item"),
            "historyInterface": ("historyInterface", "history_item"),
            "moreSettingsInterface": ("moreSettingsInterface", "more_settings_item"),
            "updateInterface": ("updateInterface", "update_item"),
            "aboutInterface": ("aboutInterface", "about_item"),
        }

        # 反向映射，从界面名称到页面名称
        interface_to_page = {
            "basicSettingsInterface": "settings_basic",
            "listManagementInterface": "settings_list",
            "extractionSettingsInterface": "settings_extraction",
            "floatingWindowManagementInterface": "settings_floating",
            "notificationSettingsInterface": "settings_notification",
            "safetySettingsInterface": "settings_safety",
            "voiceSettingsInterface": "settings_voice",
            "historyInterface": "settings_history",
            "moreSettingsInterface": "settings_more",
            "updateInterface": "settings_update",
            "aboutInterface": "settings_about",
        }

        # 检查 page_name 是否是直接的界面名称
        if page_name in direct_interface_mapping:
            interface_attr, item_attr = direct_interface_mapping[page_name]
            interface = getattr(self, interface_attr, None)
            nav_item = getattr(self, item_attr, None)

            if interface and nav_item:
                logger.debug(f"切换到设置页面: {page_name}")
                self.switchTo(interface)
                self.show()
                self.activateWindow()
                self.raise_()
            else:
                logger.warning(f"设置页面不存在或尚未初始化: {page_name}")
        elif page_name in page_mapping:
            interface_attr, item_attr = page_mapping[page_name]
            interface = getattr(self, interface_attr, None)
            nav_item = getattr(self, item_attr, None)

            if interface and nav_item:
                logger.debug(f"切换到设置页面: {page_name}")
                self.switchTo(interface)
                self.show()
                self.activateWindow()
                self.raise_()
            else:
                logger.warning(f"设置页面不存在或尚未初始化: {page_name}")
        elif page_name in interface_to_page.values():
            # 如果页面名称已经是对应的界面名称，直接切换
            interface_name = None
            for iface_name, mapped_page in interface_to_page.items():
                if mapped_page == page_name:
                    interface_name = iface_name
                    break

            if interface_name and hasattr(self, interface_name):
                interface = getattr(self, interface_name)
                logger.debug(f"切换到设置界面: {interface_name}")
                self.switchTo(interface)
                self.show()
                self.activateWindow()
                self.raise_()
            else:
                logger.warning(f"设置界面不存在: {interface_name}")
        else:
            logger.warning(f"未知的设置页面: {page_name}")

    def createSubInterface(self):
        """创建子界面
        搭建子界面导航系统"""
        # 廉价创建页面：先创建轻量占位容器并注册工厂
        from app.page_building import settings_window_page

        # 存储占位 -> factory 映射
        self._deferred_factories = {}
        # 存储工厂的元信息（例如是否为 pivot 类型），用于预热策略调整
        self._deferred_factories_meta = {}

        def make_placeholder(name: str):
            w = QWidget()
            w.setObjectName(name)
            # 使用空布局以便后续将真正页面加入
            layout = QVBoxLayout(w)
            layout.setContentsMargins(0, 0, 0, 0)
            return w

        # 获取所有设置值
        settings = {
            "base_settings": readme_settings_async(
                "sidebar_management_settings", "base_settings"
            ),
            "name_management": readme_settings_async(
                "sidebar_management_settings", "name_management"
            ),
            "draw_settings": readme_settings_async(
                "sidebar_management_settings", "draw_settings"
            ),
            "floating_window_management": readme_settings_async(
                "sidebar_management_settings", "floating_window_management"
            ),
            "notification_service": readme_settings_async(
                "sidebar_management_settings", "notification_service"
            ),
            "security_settings": readme_settings_async(
                "sidebar_management_settings", "security_settings"
            ),
            "voice_settings": readme_settings_async(
                "sidebar_management_settings", "voice_settings"
            ),
            "settings_history": readme_settings_async(
                "sidebar_management_settings", "settings_history"
            ),
            "more_settings": readme_settings_async(
                "sidebar_management_settings", "more_settings"
            ),
        }

        # 定义页面配置
        page_configs = [
            ("base_settings", "basicSettingsInterface", "basic_settings_page", False),
            (
                "name_management",
                "listManagementInterface",
                "list_management_page",
                True,
            ),
            (
                "draw_settings",
                "extractionSettingsInterface",
                "extraction_settings_page",
                True,
            ),
            (
                "floating_window_management",
                "floatingWindowManagementInterface",
                "floating_window_management_page",
                True,
            ),
            (
                "notification_service",
                "notificationSettingsInterface",
                "notification_settings_page",
                True,
            ),
            (
                "security_settings",
                "safetySettingsInterface",
                "safety_settings_page",
                True,
            ),
            (
                "voice_settings",
                "voiceSettingsInterface",
                "voice_settings_page",
                True,
            ),
            ("settings_history", "historyInterface", "history_page", True),
            (
                "more_settings",
                "moreSettingsInterface",
                "more_settings_page",
                True,
            ),
        ]

        # 根据设置创建对应的界面
        for setting_key, interface_attr, page_method, is_pivot in page_configs:
            setting_value = settings.get(setting_key)
            # 如果设置不为"不显示"(值不等于2)或者设置未定义，则创建界面
            if setting_value is None or setting_value != 2:
                interface = make_placeholder(interface_attr)
                setattr(self, interface_attr, interface)

                # 使用默认参数解决闭包问题
                def make_factory(method_name=page_method, iface=interface):
                    return lambda parent=iface: getattr(
                        settings_window_page, method_name
                    )(parent)

                self._deferred_factories[interface_attr] = make_factory()
                self._deferred_factories_meta[interface_attr] = {"is_pivot": is_pivot}

        # 单独处理更新页面和关于页面
        self.updateInterface = make_placeholder("updateInterface")

        def make_update_factory(iface=self.updateInterface):
            return lambda parent=iface: settings_window_page.update_page(parent)

        self._deferred_factories["updateInterface"] = make_update_factory()
        self._deferred_factories_meta["updateInterface"] = {"is_pivot": False}

        self.aboutInterface = make_placeholder("aboutInterface")

        def make_about_factory(iface=self.aboutInterface):
            return lambda parent=iface: settings_window_page.about_page(parent)

        self._deferred_factories["aboutInterface"] = make_about_factory()
        self._deferred_factories_meta["aboutInterface"] = {"is_pivot": False}

        # 把占位注册到导航，但不要在此刻实例化真实页面
        self.initNavigation()

        # 在窗口显示后启动针对非 pivot 页面的后台预热（分批创建）
        try:
            QTimer.singleShot(300, lambda: self._background_warmup_non_pivot())
        except Exception as e:
            logger.exception("Error during settings warmup: {}", e)

        # 连接堆叠窗口切换信号，在首次切换到占位时创建真实页面
        try:
            self.stackedWidget.currentChanged.connect(self._on_stacked_widget_changed)
        except Exception as e:
            logger.exception("Error creating deferred page: {}", e)

        # 在窗口显示后启动后台预热，分批创建其余页面，避免一次性阻塞
        try:
            QTimer.singleShot(300, lambda: self._background_warmup_pages())
        except Exception as e:
            logger.exception("Error scheduling background warmup pages: {}", e)

    def _on_stacked_widget_changed(self, index: int):
        """当导航切换到某个占位页时，按需创建真实页面内容"""
        try:
            widget = self.stackedWidget.widget(index)
            if not widget:
                return
            name = widget.objectName()
            # 如果有延迟工厂且容器尚未填充内容，则创建真实页面
            if (
                name in getattr(self, "_deferred_factories", {})
                and widget.layout()
                and widget.layout().count() == 0
            ):
                factory = self._deferred_factories.pop(name)
                try:
                    real_page = factory()
                    # real_page 会在其内部创建内容（PageTemplate 会在其内部事件循环中再创建内部内容），
                    # 我们把它作为子控件加入占位容器
                    widget.layout().addWidget(real_page)
                    # 如果是 PivotPageTemplate，打开该顶层页面时预加载其所有 inner pivots（分批加载以避免卡顿）
                    try:
                        from app.page_building.page_template import PivotPageTemplate

                        if isinstance(real_page, PivotPageTemplate):
                            # 稍微延迟以确保 real_page 初始化完成
                            QTimer.singleShot(
                                50, lambda rp=real_page: rp.load_all_pages()
                            )
                    except Exception as e:
                        logger.exception("Error in deferred page creation step: {}", e)
                    logger.debug(f"设置页面已按需创建: {name}")
                except Exception as e:
                    logger.error(f"延迟创建设置页面 {name} 失败: {e}")
        except Exception as e:
            logger.error(f"处理堆叠窗口改变失败: {e}")

    def _background_warmup_pages(
        self,
        interval_ms: int = SETTINGS_WARMUP_INTERVAL_MS,
        max_preload: int = SETTINGS_WARMUP_MAX_PRELOAD,
    ):
        """分批（间隔）创建剩余的设置页面，减少单次阻塞。

        参数:
            interval_ms: 每个页面创建间隔（毫秒）
        """
        try:
            # 复制键避免在迭代时修改字典
            names = list(getattr(self, "_deferred_factories", {}).keys())
            if not names:
                return
            # 优先预热非 pivot（单页面）项，再预热 pivot 项，保持原有非 pivot 的异步加载策略
            try:
                meta = getattr(self, "_deferred_factories_meta", {})
                non_pivot = [
                    n for n in names if not meta.get(n, {}).get("is_pivot", False)
                ]
                pivot = [n for n in names if meta.get(n, {}).get("is_pivot", False)]
                ordered = non_pivot + pivot
            except Exception as e:
                logger.exception(
                    "Error ordering deferred factories (fallback to original order): {}",
                    e,
                )
                ordered = names

            # 仅预热有限数量的页面，避免一次性占用主线程
            names_to_preload = ordered[:max_preload]
            logger.debug(
                f"后台预热将创建 {len(names_to_preload)} / {len(names)} 个页面"
            )
            # 仅为要预热的页面调度创建，避免一次性调度所有页面
            for i, name in enumerate(names_to_preload):
                # 延迟创建，避免短时间内占用主线程
                QTimer.singleShot(
                    interval_ms * i,
                    (lambda n=name: self._create_deferred_page(n)),
                )
        except Exception as e:
            logger.error(f"后台预热设置页面失败: {e}")

    def _background_warmup_non_pivot(self, interval_ms: int = 80):
        """
        在设置窗口首次打开时，分批延时创建所有非 pivot（单页面）项，避免用户首次打开时卡顿。

        Args:
            interval_ms: 每个页面创建的间隔毫秒数。
        """
        try:
            names = list(getattr(self, "_deferred_factories", {}).keys())
            if not names:
                return

            meta = getattr(self, "_deferred_factories_meta", {})
            non_pivot = [n for n in names if not meta.get(n, {}).get("is_pivot", False)]
            # 逐个调度创建非 pivot 页面，分散开以减少瞬时主线程负载
            for i, name in enumerate(non_pivot):
                QTimer.singleShot(
                    interval_ms * i, (lambda n=name: self._create_deferred_page(n))
                )
        except Exception as e:
            logger.error(f"后台预热非 pivot 页面失败: {e}")

    def _create_deferred_page(self, name: str):
        """根据名字创建对应延迟工厂并把结果加入占位容器"""
        try:
            if name not in getattr(self, "_deferred_factories", {}):
                return
            factory = self._deferred_factories.pop(name)

            # 查找对应的容器
            container = None
            container_attrs = [
                "basicSettingsInterface",
                "listManagementInterface",
                "extractionSettingsInterface",
                "floatingWindowManagementInterface",
                "notificationSettingsInterface",
                "safetySettingsInterface",
                "customSettingsInterface",
                "voiceSettingsInterface",
                "historyInterface",
                "moreSettingsInterface",
                "updateInterface",
                "aboutInterface",
            ]

            for attr in container_attrs:
                container_obj = getattr(self, attr, None)
                if container_obj and container_obj.objectName() == name:
                    container = container_obj
                    break

            if container is None:
                return

            # 如果容器已经被销毁或没有 layout，则跳过
            if not container or not hasattr(container, "layout"):
                return
            layout = container.layout()
            if layout is None:
                return

            try:
                real_page = factory()
            except RuntimeError as e:
                logger.error(f"创建延迟页面 {name} 失败（父容器可能已销毁）: {e}")
                return
            except Exception as e:
                logger.error(f"创建延迟页面 {name} 失败: {e}")
                return

            try:
                layout.addWidget(real_page)
                logger.debug(f"后台预热创建设置页面: {name}")
            except RuntimeError as e:
                logger.error(f"将延迟页面 {name} 插入容器失败（容器可能已销毁）: {e}")
                return
        except Exception as e:
            logger.error(f"_create_deferred_page 失败: {e}")

    def initNavigation(self):
        """初始化导航系统
        根据用户设置构建个性化菜单导航"""
        # 获取所有设置值
        settings = {
            "base_settings": readme_settings_async(
                "sidebar_management_settings", "base_settings"
            ),
            "name_management": readme_settings_async(
                "sidebar_management_settings", "name_management"
            ),
            "draw_settings": readme_settings_async(
                "sidebar_management_settings", "draw_settings"
            ),
            "notification_service": readme_settings_async(
                "sidebar_management_settings", "notification_service"
            ),
            "security_settings": readme_settings_async(
                "sidebar_management_settings", "security_settings"
            ),
            "voice_settings": readme_settings_async(
                "sidebar_management_settings", "voice_settings"
            ),
            "settings_history": readme_settings_async(
                "sidebar_management_settings", "settings_history"
            ),
            "more_settings": readme_settings_async(
                "sidebar_management_settings", "more_settings"
            ),
        }

        # 定义导航项配置
        nav_configs = [
            (
                "base_settings",
                "basicSettingsInterface",
                "basic_settings_item",
                "ic_fluent_wrench_settings_20_filled",
                "basic_settings",
                "title",
            ),
            (
                "name_management",
                "listManagementInterface",
                "list_management_item",
                "ic_fluent_list_20_filled",
                "list_management",
                "title",
            ),
            (
                "draw_settings",
                "extractionSettingsInterface",
                "extraction_settings_item",
                "ic_fluent_archive_20_filled",
                "extraction_settings",
                "title",
            ),
            (
                "floating_window_management",
                "floatingWindowManagementInterface",
                "floating_window_management_item",
                "ic_fluent_window_apps_20_filled",
                "floating_window_management",
                "title",
            ),
            (
                "notification_service",
                "notificationSettingsInterface",
                "notification_settings_item",
                "ic_fluent_comment_note_20_filled",
                "notification_settings",
                "title",
            ),
            (
                "security_settings",
                "safetySettingsInterface",
                "safety_settings_item",
                "ic_fluent_shield_20_filled",
                "safety_settings",
                "title",
            ),
            (
                "voice_settings",
                "voiceSettingsInterface",
                "voice_settings_item",
                "ic_fluent_person_voice_20_filled",
                "voice_settings",
                "title",
            ),
            (
                "settings_history",
                "historyInterface",
                "history_item",
                "ic_fluent_history_20_filled",
                "history",
                "title",
            ),
            (
                "more_settings",
                "moreSettingsInterface",
                "more_settings_item",
                "ic_fluent_more_horizontal_20_filled",
                "more_settings",
                "title",
            ),
        ]

        # 根据设置添加导航项
        for (
            setting_key,
            interface_attr,
            item_attr,
            icon_name,
            module,
            name_key,
        ) in nav_configs:
            setting_value = settings.get(setting_key)
            # 如果设置不为"不显示"(值不等于2)或者设置未定义，则添加导航项
            if setting_value is None or setting_value != 2:
                interface = getattr(self, interface_attr, None)
                if interface is not None:
                    # 确定位置：设置为1表示底部，其他情况为顶部
                    position = (
                        NavigationItemPosition.BOTTOM
                        if setting_value == 1
                        else NavigationItemPosition.TOP
                    )

                    nav_item = self.addSubInterface(
                        interface,
                        get_theme_icon(icon_name),
                        get_content_name_async(module, name_key),
                        position=position,
                    )
                    setattr(self, item_attr, nav_item)

        # 关于页面始终显示在底部
        self.update_item = self.addSubInterface(
            self.updateInterface,
            get_theme_icon("ic_fluent_arrow_sync_20_filled"),
            get_content_name_async("update", "title"),
            position=NavigationItemPosition.BOTTOM,
        )

        self.about_item = self.addSubInterface(
            self.aboutInterface,
            get_theme_icon("ic_fluent_info_20_filled"),
            get_content_name_async("about", "title"),
            position=NavigationItemPosition.BOTTOM,
        )

        # 配置导航栏为可折叠模式
        self._setupCollapsibleNavigation()

        self.splashScreen.finish()

        # 连接信号
        self.showMainPageRequested.connect(self._handle_main_page_requested)

    def closeEvent(self, event):
        """窗口关闭事件处理
        拦截窗口关闭事件，隐藏窗口并保存窗口大小"""
        self.hide()
        event.ignore()
        is_maximized = self.isMaximized()
        update_settings("settings", "is_maximized", is_maximized)
        if is_maximized:
            pass
        else:
            self.save_window_size(self.width(), self.height())

    def resizeEvent(self, event):
        """窗口大小变化事件处理
        检测窗口大小变化，但不启动尺寸记录倒计时，减少IO操作"""
        # 正常的窗口大小变化处理
        self.resize_timer.start(500)
        super().resizeEvent(event)

    def changeEvent(self, event):
        """窗口状态变化事件处理
        检测窗口最大化/恢复状态变化，保存正确的窗口大小"""
        # 检查是否是窗口状态变化
        if event.type() == QEvent.Type.WindowStateChange:
            is_currently_maximized = self.isMaximized()
            was_maximized = readme_settings_async("settings", "is_maximized")
            if is_currently_maximized != was_maximized:
                update_settings("settings", "is_maximized", is_currently_maximized)
                if is_currently_maximized:
                    normal_geometry = self.normalGeometry()
                    update_settings(
                        "settings", "pre_maximized_width", normal_geometry.width()
                    )
                    update_settings(
                        "settings", "pre_maximized_height", normal_geometry.height()
                    )
                else:
                    pre_maximized_width = readme_settings_async(
                        "settings", "pre_maximized_width"
                    )
                    pre_maximized_height = readme_settings_async(
                        "settings", "pre_maximized_height"
                    )
                    QTimer.singleShot(
                        100,
                        lambda: self.resize(pre_maximized_width, pre_maximized_height),
                    )

        super().changeEvent(event)

    def save_window_size(self, setting_window_width, setting_window_height):
        """保存窗口大小
        记录当前窗口尺寸，下次启动时自动恢复"""
        if not self.isMaximized():
            update_settings("settings", "height", setting_window_height)
            update_settings("settings", "width", setting_window_width)

    def show_settings_window(self):
        """显示设置窗口"""
        if self.isMinimized():
            self.showNormal()
            self.activateWindow()
            self.raise_()
        else:
            self.show()
            self.activateWindow()
            self.raise_()

    def show_settings_window_about(self):
        """显示关于窗口"""
        if self.isMinimized():
            self.showNormal()
            self.activateWindow()
            self.raise_()
        else:
            self.show()
            self.activateWindow()
            self.raise_()

        self.switchTo(self.aboutInterface)

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

            # 设置导航栏展开宽度（展开时显示图标+文本，设置窗口需要更宽）
            nav.setExpandWidth(320)
            nav.setMinimumExpandWidth(320)

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
        TOUCH_EXPAND_WIDTH = 320  # 展开时的宽度（设置窗口更宽）
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

                def make_custom_paintEvent(
                    w, height, icon_size, indicator_height, compact_width
                ):
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
                            icon_x = (compact_width - icon_size) // 2 + pl
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
                            text_x = compact_width + pl
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
                    TOUCH_COMPACT_WIDTH,
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

    def _apply_sidebar_settings(self):
        """应用侧边栏设置"""
        # 由于导航项已在initNavigation中根据设置处理，这里不再需要重复处理
        pass
