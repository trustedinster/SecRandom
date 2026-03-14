# ==================================================
# 导入库
# ==================================================

from loguru import logger
from PySide6.QtWidgets import QApplication, QLabel, QWidget, QScroller, QSizePolicy
from PySide6.QtGui import QIcon
from PySide6.QtCore import QTimer, QEvent, Signal, QSize, Qt, QThread, QObject
from PySide6.QtWidgets import QVBoxLayout
from qfluentwidgets import (
    FluentWindow,
    NavigationItemPosition,
    SingleDirectionScrollArea,
    SearchLineEdit,
)

from app.tools.variable import (
    MINIMUM_WINDOW_SIZE,
    RESIZE_TIMER_DELAY_MS,
    MAXIMIZE_RESTORE_DELAY_MS,
    SETTINGS_WINDOW_DEFAULT_WIDTH,
    SETTINGS_WINDOW_DEFAULT_HEIGHT,
)
from app.tools.path_utils import get_data_path
from app.tools.personalised import get_theme_icon
from app.tools.settings_access import (
    get_settings_snapshot,
    readme_settings_async,
    update_settings,
)
from app.tools.interaction_perf import start_interaction
from app.page_building.window_template import BackgroundLayer
from app.Language.obtain_language import get_content_name_async
from app.common.IPC_URL.url_command_handler import URLCommandHandler
from app.common.page_registry import (
    get_settings_page_by_interface,
    iter_navigable_settings_pages,
    iter_settings_page_container_names,
    iter_settings_pages,
)
from app.common.search.settings_search_controller import SettingsSearchController


# ==================================================
# 设置窗口类
# ==================================================
class SettingsWindow(FluentWindow):
    """设置窗口类
    程序的设置管理界面"""

    showSettingsRequested = Signal(str)  # 请求显示设置页面
    showSettingsRequestedAbout = Signal()
    showMainPageRequested = Signal(str)  # 请求显示主页面

    def __init__(self, parent=None, is_preview=False):
        self.resize_timer = None
        super().__init__()
        self.setObjectName("settingWindow")
        self.parent = parent
        self._is_preview = is_preview
        self._startup_settings_snapshot = get_settings_snapshot()

        self._initialize_variables()
        self._setup_timers()
        self._setup_window_properties()
        self._setup_url_handler()
        self._position_window(snapshot=self._startup_settings_snapshot)
        self._setup_splash_screen()
        self.createSubInterface()

    # ==================================================
    # 初始化方法
    # ==================================================

    def _initialize_variables(self):
        """初始化实例变量"""
        interface_names = list(iter_settings_page_container_names()) + [
            "customSettingsInterface"
        ]

        for name in interface_names:
            setattr(self, name, None)

        self._deferred_factories = {}
        self._deferred_factories_meta = {}
        self._created_pages = {}
        self._page_access_order = []
        self._pending_page_loads = set()
        self._geometry_sync_scheduled = False
        self._geometry_sync_callbacks = []
        if __debug__:
            self._geometry_sync_request_count = 0
            self._geometry_sync_run_count = 0

    def _setup_timers(self):
        """设置定时器"""
        self.resize_timer = QTimer(self)
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(
            lambda: self.save_window_size(self.width(), self.height())
        )

    def _setup_window_properties(self):
        """设置窗口属性"""
        self.resize(SETTINGS_WINDOW_DEFAULT_WIDTH, SETTINGS_WINDOW_DEFAULT_HEIGHT)
        self.setMinimumSize(MINIMUM_WINDOW_SIZE[0], MINIMUM_WINDOW_SIZE[1])
        self.setWindowTitle("SecRandom")
        self.setWindowIcon(
            QIcon(str(get_data_path("assets/icon", "secrandom-icon-paper.png")))
        )
        self._setup_background_layer()
        self._setup_settings_listener()
        self._setup_sidebar_scroll()
        self._setup_titlebar_search()

    def _setup_titlebar_search(self):
        title_bar = getattr(self, "titleBar", None)
        if title_bar is None:
            return

        if getattr(self, "_settings_search_line_edit", None) is not None:
            return

        self._settings_search_line_edit = SearchLineEdit(title_bar)
        try:
            self._settings_search_line_edit.setPlaceholderText(
                get_content_name_async("settings", "search_placeholder")
            )
        except Exception:
            pass

        self._settings_search_controller = SettingsSearchController(
            window=self,
            title_bar=title_bar,
            line_edit=self._settings_search_line_edit,
            ensure_page_ready=self._ensure_settings_page_ready,
            parent=self,
        )
        try:
            self._settings_search_line_edit.searchSignal.connect(
                self._settings_search_controller.on_search
            )
        except Exception:
            pass

        self._request_geometry_sync()

    def _position_titlebar_search(self):
        title_bar = getattr(self, "titleBar", None)
        line_edit = getattr(self, "_settings_search_line_edit", None)
        if title_bar is None or line_edit is None:
            return

        title_w = int(title_bar.width() or 0)
        title_h = int(title_bar.height() or 0)
        if title_w <= 0 or title_h <= 0:
            return

        left_reserve = 220
        right_reserve = 180
        max_w = max(200, title_w - left_reserve - right_reserve)
        target_w = min(420, max_w)

        try:
            line_edit.setFixedWidth(int(target_w))
        except Exception:
            pass

        try:
            line_edit.adjustSize()
        except Exception:
            pass

        w = int(line_edit.width() or target_w)
        h = int(line_edit.height() or 28)
        x = (title_w - w) // 2
        x = max(left_reserve, min(x, title_w - right_reserve - w))
        y = max(0, (title_h - h) // 2)
        line_edit.move(int(x), int(y))
        line_edit.raise_()

    def _setup_sidebar_scroll(self):
        navigation = getattr(self, "navigationInterface", None)
        if navigation is None:
            return
        if getattr(self, "_sidebar_scroll_area", None) is not None:
            return

        scroll_area = SingleDirectionScrollArea(self)
        scroll_area.setWidgetResizable(False)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet(
            """
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollArea QWidget {
                border: none;
                background-color: transparent;
            }
            """
        )
        QScroller.grabGesture(
            scroll_area.viewport(),
            QScroller.ScrollerGestureType.LeftMouseButtonGesture,
        )
        scroll_area.setWidget(navigation)
        scroll_area.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding
        )

        layout = getattr(self, "hBoxLayout", None) or self.layout()
        if layout is not None:
            index = layout.indexOf(navigation)
            if index < 0:
                index = 0
            layout.removeWidget(navigation)
            layout.insertWidget(index, scroll_area)

        self._sidebar_scroll_area = scroll_area
        self._sidebar_navigation_widget = navigation

        navigation.installEventFilter(self)
        scroll_area.installEventFilter(self)
        self._request_geometry_sync()

    def _sync_sidebar_scroll_geometry(self):
        scroll_area = getattr(self, "_sidebar_scroll_area", None)
        navigation = getattr(self, "_sidebar_navigation_widget", None) or getattr(
            self, "navigationInterface", None
        )
        if scroll_area is None or navigation is None:
            return

        target_width = int(navigation.width() or navigation.sizeHint().width() or 0)
        if target_width > 0 and scroll_area.width() != target_width:
            scroll_area.setFixedWidth(target_width)

        viewport_h = int(scroll_area.viewport().height() or 0)
        if viewport_h > 0 and navigation.minimumHeight() != viewport_h:
            navigation.setMinimumHeight(viewport_h)

    def _request_geometry_sync(self, callback=None):
        if callback is not None:
            self._geometry_sync_callbacks.append(callback)

        if __debug__:
            self._geometry_sync_request_count += 1

        if self._geometry_sync_scheduled:
            return

        self._geometry_sync_scheduled = True
        # Wait one event-loop turn so title bar and sidebar layout can settle.
        QTimer.singleShot(0, self._run_deferred_geometry_sync)

    def _run_deferred_geometry_sync(self):
        self._geometry_sync_scheduled = False

        if __debug__:
            self._geometry_sync_run_count += 1
            assert self._geometry_sync_run_count <= self._geometry_sync_request_count

        try:
            self._sync_sidebar_scroll_geometry()
        except Exception:
            pass

        try:
            self._position_titlebar_search()
        except Exception:
            pass

        callbacks = self._geometry_sync_callbacks
        self._geometry_sync_callbacks = []
        for callback in callbacks:
            try:
                callback()
            except Exception as e:
                logger.exception(f"执行几何同步回调失败: {e}")

    def _setup_settings_listener(self):
        try:
            from app.tools.settings_access import get_settings_signals

            get_settings_signals().settingChanged.connect(self._on_setting_changed)
        except Exception:
            pass

    def _on_setting_changed(self, first, second, value):
        if first == "background_management" and str(second or "").startswith(
            "settings_window_background_"
        ):
            try:
                if getattr(self, "_background_layer", None) is not None:
                    self._background_layer.applyFromSettings()
            except Exception:
                pass

    def _setup_background_layer(self):
        if getattr(self, "_background_layer", None) is not None:
            try:
                self._background_layer.applyFromSettings()
            except Exception:
                pass
            return

        self._background_layer = BackgroundLayer(self, "settings_window")
        self._background_layer.updateGeometryToParent()
        self._background_layer.lower()
        try:
            self._background_layer.applyFromSettings()
        except Exception:
            pass

    def _setup_url_handler(self):
        """设置URL处理器"""
        self.url_command_handler = URLCommandHandler(self)
        self.url_command_handler.showSettingsRequested.connect(
            self._handle_settings_page_request
        )

    def _setup_splash_screen(self):
        """设置启动画面"""
        from qfluentwidgets import SplashScreen

        self.splashScreen = SplashScreen(self.windowIcon(), self)
        self.splashScreen.setIconSize(QSize(256, 256))
        if getattr(self, "_show_maximized_on_init", False):
            self.showMaximized()
        else:
            self.show()

    # ==================================================
    # 属性访问器
    # ==================================================

    @property
    def is_preview(self):
        """获取是否为预览模式"""
        return self._is_preview

    @is_preview.setter
    def is_preview(self, value):
        """设置是否为预览模式，并在值改变时锁定所有已创建的页面

        Args:
            value: 是否为预览模式
        """
        self._is_preview = value
        if hasattr(self, "_created_pages"):
            for page_name, real_page in self._created_pages.items():
                if real_page and hasattr(real_page, "is_preview_mode"):
                    real_page.is_preview_mode = value
                elif real_page:
                    self._lock_all_widgets(real_page)

    def _lock_all_widgets(self, widget):
        """锁定所有子组件

        Args:
            widget: 要锁定的组件
        """
        if widget is None:
            return
        if hasattr(widget, "setEnabled"):
            widget.setEnabled(False)
        for child in widget.children():
            if isinstance(child, QWidget):
                self._lock_all_widgets(child)

    # ==================================================
    # 窗口定位与大小管理
    # ==================================================

    def _position_window(self, snapshot=None):
        """窗口定位
        根据屏幕尺寸和用户设置自动计算最佳位置"""
        settings_section = (
            snapshot.get("settings", {}) if isinstance(snapshot, dict) else {}
        )
        if not isinstance(settings_section, dict):
            settings_section = {}

        is_maximized = settings_section.get("is_maximized")
        if is_maximized is None:
            is_maximized = readme_settings_async("settings", "is_maximized")
        if is_maximized:
            pre_maximized_width = settings_section.get("pre_maximized_width")
            if pre_maximized_width is None:
                pre_maximized_width = readme_settings_async(
                    "settings", "pre_maximized_width"
                )
            pre_maximized_height = settings_section.get("pre_maximized_height")
            if pre_maximized_height is None:
                pre_maximized_height = readme_settings_async(
                    "settings", "pre_maximized_height"
                )
            self.resize(pre_maximized_width, pre_maximized_height)
            self._center_window()
            self._show_maximized_on_init = True
        else:
            self._show_maximized_on_init = False
            setting_window_width = settings_section.get("width")
            if setting_window_width is None:
                setting_window_width = readme_settings_async("settings", "width")
            setting_window_height = settings_section.get("height")
            if setting_window_height is None:
                setting_window_height = readme_settings_async("settings", "height")
            self.resize(setting_window_width, setting_window_height)
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

    def save_window_size(self, width, height):
        """保存窗口大小
        记录当前窗口尺寸，下次启动时自动恢复

        Args:
            width: 窗口宽度
            height: 窗口高度
        """
        auto_save_enabled = readme_settings_async(
            "basic_settings", "auto_save_window_size"
        )

        if auto_save_enabled:
            if not self.isMaximized():
                update_settings("settings", "height", height)
                update_settings("settings", "width", width)

    # ==================================================
    # 窗口事件处理
    # ==================================================

    def closeEvent(self, event):
        """窗口关闭事件处理
        拦截窗口关闭事件，隐藏窗口并保存窗口大小

        Args:
            event: 关闭事件对象
        """
        self.hide()
        event.ignore()
        is_maximized = self.isMaximized()
        update_settings("settings", "is_maximized", is_maximized)
        if not is_maximized:
            self.save_window_size(self.width(), self.height())

    def resizeEvent(self, event):
        """窗口大小变化事件处理
        检测窗口大小变化，启动尺寸记录倒计时

        Args:
            event: 大小变化事件对象
        """
        resize_timer = getattr(self, "resize_timer", None)
        if resize_timer is not None:
            resize_timer.start(RESIZE_TIMER_DELAY_MS)
        try:
            if getattr(self, "_background_layer", None) is not None:
                self._background_layer.updateGeometryToParent()
        except Exception:
            pass
        super().resizeEvent(event)
        self._request_geometry_sync()

    def changeEvent(self, event):
        """窗口状态变化事件处理
        检测窗口最大化/恢复状态变化，保存正确的窗口大小

        Args:
            event: 状态变化事件对象
        """
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
                        MAXIMIZE_RESTORE_DELAY_MS,
                        lambda: self.resize(pre_maximized_width, pre_maximized_height),
                    )

        super().changeEvent(event)
        if event.type() == QEvent.Type.WindowStateChange:
            self._request_geometry_sync()

    def eventFilter(self, obj, event):
        navigation = getattr(self, "_sidebar_navigation_widget", None)
        scroll_area = getattr(self, "_sidebar_scroll_area", None)
        if obj is navigation and event.type() in (
            QEvent.Type.Resize,
            QEvent.Type.LayoutRequest,
            QEvent.Type.Show,
        ):
            self._request_geometry_sync()
        elif obj is scroll_area and event.type() in (
            QEvent.Type.Resize,
            QEvent.Type.Show,
        ):
            self._request_geometry_sync()
        return super().eventFilter(obj, event)

    # ==================================================
    # 页面请求处理
    # ==================================================

    def _handle_main_page_requested(self, page_name: str):
        """处理主页面请求

        Args:
            page_name: 页面名称
        """
        logger.debug(f"设置窗口收到主页面请求: {page_name}")

        if page_name.startswith("settings_"):
            self._handle_settings_page_request(page_name)
        else:
            logger.debug(f"设置窗口转发主页面请求: {page_name}")
            if hasattr(self, "parent") and self.parent:
                self.showMainPageRequested.emit(page_name)

    def _handle_settings_page_request(self, page_name: str):
        """处理设置页面请求

        Args:
            page_name: 设置页面名称
        """
        trace = start_interaction(f"settings.{page_name}")
        logger.debug(f"处理设置页面请求: {page_name}")

        page = self._ensure_settings_page_ready(page_name)
        if page is not None:
            trace.log("shell_visible")
        else:
            logger.warning(f"未知的设置页面: {page_name}")
        return page

    def _ensure_sub_interface_created(self):
        """确保子界面已创建"""
        if not hasattr(self, "_sub_interface_created"):
            self._sub_interface_created = False

        if not self._sub_interface_created:
            logger.debug("子界面尚未创建，立即创建")
            try:
                self.createSubInterface()
                self._sub_interface_created = True
            except Exception as e:
                logger.exception(f"创建子界面失败: {e}")

    def _get_page_mapping(self):
        """获取页面映射字典

        Returns:
            dict: 页面名称到界面属性的映射
        """
        mapping = {}
        for page in iter_settings_pages():
            value = (page.interface_attr, page.item_attr)
            mapping[page.route_name] = value
            mapping[page.interface_attr] = value
        return mapping

    def _resolve_settings_page_target(self, page_name: str):
        page_mapping = self._get_page_mapping()
        if page_name not in page_mapping:
            return None

        interface_attr, item_attr = page_mapping[page_name]
        interface = getattr(self, interface_attr, None)
        nav_item = getattr(self, item_attr, None)
        if interface is None or nav_item is None:
            return None

        return interface_attr, interface

    def _ensure_settings_page_ready(self, page_name: str, on_ready=None):
        self._ensure_sub_interface_created()

        target = self._resolve_settings_page_target(page_name)
        if target is None:
            return None

        interface_attr, interface = target
        self.switchTo(interface)
        logger.debug(f"切换到设置页面: {page_name}")
        self.show()
        self.activateWindow()
        self.raise_()

        self._ensure_deferred_page_loaded(interface_attr)
        page = getattr(self, "_created_pages", {}).get(interface_attr)
        if page is None:
            logger.warning(f"设置页面不存在或尚未初始化: {page_name}")
            return None

        if on_ready is not None:
            self._request_geometry_sync(
                lambda current_page=page: on_ready(current_page)
            )

        return page

    # ==================================================
    # 界面创建与导航
    # ==================================================

    def createSubInterface(self):
        """创建子界面
        搭建子界面导航系统"""
        if hasattr(self, "_sub_interface_created") and self._sub_interface_created:
            logger.debug("子界面已创建，跳过重复创建")
            return

        from app.page_building import settings_window_page

        settings = self._get_sidebar_settings()

        for page in iter_settings_pages():
            setting_value = settings.get(page.sidebar_setting_key)
            if setting_value is None or setting_value != 2:
                self._create_page_placeholder(
                    page.interface_attr,
                    page.page_method,
                    page.is_pivot,
                    settings_window_page,
                )
        self.initNavigation()
        self._setup_background_warmup()
        self._sub_interface_created = True

    def _get_sidebar_settings(self):
        """获取侧边栏设置

        Returns:
            dict: 侧边栏设置字典
        """
        return {page.sidebar_setting_key: 0 for page in iter_navigable_settings_pages()}

    def _get_page_configs(self):
        """获取页面配置列表

        Returns:
            list: 页面配置列表
        """
        return [
            (
                page.sidebar_setting_key,
                page.interface_attr,
                page.page_method,
                page.is_pivot,
            )
            for page in iter_settings_pages()
        ]

    def _create_page_placeholder(
        self, interface_attr, page_method, is_pivot, settings_window_page
    ):
        """创建页面占位符

        Args:
            interface_attr: 界面属性名
            page_method: 页面方法名
            is_pivot: 是否为pivot页面
            settings_window_page: 设置窗口页面模块
        """
        interface = self._make_placeholder(interface_attr)
        setattr(self, interface_attr, interface)
        self._register_deferred_factory(
            interface_attr, page_method, is_pivot, settings_window_page
        )

    def _make_placeholder(self, name: str):
        """创建占位符组件

        Args:
            name: 占位符名称

        Returns:
            QWidget: 占位符组件
        """
        w = QWidget()
        w.setObjectName(name)
        layout = QVBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)
        self._set_placeholder_loading(w)
        return w

    def _set_placeholder_loading(
        self, container: QWidget, text: str = "正在加载页面..."
    ) -> None:
        layout = container.layout()
        if layout is None:
            return
        while layout.count() > 0:
            item = layout.takeAt(0)
            if not item:
                break
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        label = QLabel(text)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)

    def _make_page_factory(self, page_method, interface, settings_window_page):
        """创建页面工厂函数

        Args:
            page_method: 页面方法名
            interface: 界面对象
            settings_window_page: 设置窗口页面模块

        Returns:
            function: 工厂函数
        """

        def factory(parent=interface, is_preview=False):
            page_instance = getattr(settings_window_page, page_method)(
                parent, is_preview=is_preview
            )
            return page_instance

        return factory

    def _register_deferred_factory(
        self, interface_attr, page_method, is_pivot, settings_window_page
    ) -> None:
        interface = getattr(self, interface_attr, None)
        if interface is None:
            return

        self._deferred_factories[interface_attr] = self._make_page_factory(
            page_method, interface, settings_window_page
        )
        self._deferred_factories_meta[interface_attr] = {
            "is_pivot": is_pivot,
            "is_preview": False,
        }

    def _get_page_factory_definition(self, page_name: str):
        page = get_settings_page_by_interface(page_name)
        if page is None:
            return None
        return page.page_method, page.is_pivot

    def _setup_background_warmup(self):
        """设置后台预热"""
        try:
            self.stackedWidget.currentChanged.connect(self._on_stacked_widget_changed)
        except Exception as e:
            logger.exception("Error creating deferred page: {}", e)

    def initNavigation(self):
        """初始化导航系统
        根据用户设置构建个性化菜单导航"""
        settings = self._get_sidebar_settings()
        for page in iter_navigable_settings_pages():
            setting_value = settings.get(page.sidebar_setting_key)
            if setting_value is None or setting_value != 2:
                self._add_navigation_item(
                    page.sidebar_setting_key,
                    page.interface_attr,
                    page.item_attr,
                    page.icon_name,
                    page.language_module,
                    page.title_key,
                )

        self.splashScreen.finish()
        self.showMainPageRequested.connect(self._handle_main_page_requested)

    def _get_nav_configs(self):
        """获取导航配置列表

        Returns:
            list: 导航配置列表
        """
        return [
            (
                page.sidebar_setting_key,
                page.interface_attr,
                page.item_attr,
                page.icon_name,
                page.language_module,
                page.title_key,
            )
            for page in iter_navigable_settings_pages()
        ]

    def _add_navigation_item(
        self, setting_key, interface_attr, item_attr, icon_name, module, name_key
    ):
        """添加导航项

        Args:
            setting_key: 设置键名
            interface_attr: 界面属性名
            item_attr: 导航项属性名
            icon_name: 图标名称
            module: 模块名
            name_key: 名称键
        """
        settings = self._get_sidebar_settings()
        setting_value = settings.get(setting_key)
        interface = getattr(self, interface_attr, None)
        if interface is not None:
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

    def _load_default_page(self):
        """加载默认页面（基础设置页面）"""
        try:
            page = self._ensure_settings_page_ready("basicSettingsInterface")
            if page is not None:
                logger.debug("已自动导航到基础设置页面")
        except Exception as e:
            logger.exception(f"加载默认页面失败: {e}")

    # ==================================================
    # 页面加载与卸载
    # ==================================================

    def _on_stacked_widget_changed(self, index: int):
        """当导航切换到某个占位页时，按需创建真实页面内容，并卸载不活动的页面

        Args:
            index: 当前索引
        """
        try:
            widget = self.stackedWidget.widget(index)
            if not widget:
                return
            name = widget.objectName()

            self._unload_inactive_pages(name)

            if (
                name in getattr(self, "_deferred_factories", {})
                and widget.layout()
                and name not in getattr(self, "_created_pages", {})
            ):
                if name in self._pending_page_loads:
                    return
                self._set_placeholder_loading(widget, "正在加载页面...")
                QTimer.singleShot(
                    0,
                    lambda current_name=name: self._materialize_deferred_page(
                        current_name
                    ),
                )
        except Exception as e:
            logger.exception(f"处理堆叠窗口改变失败: {e}")

    def _clear_placeholder_layout(self, container: QWidget) -> None:
        layout = container.layout()
        if layout is None:
            return
        while layout.count() > 0:
            item = layout.takeAt(0)
            if not item:
                break
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _unload_inactive_pages(self, current_page: str):
        """卸载不活动的页面以释放内存

        Args:
            current_page: 当前激活的页面名称
        """
        MAX_CACHED_SETTINGS_PAGES = 2

        if not hasattr(self, "_created_pages"):
            self._created_pages = {}

        if not hasattr(self, "_page_access_order"):
            self._page_access_order = []

        if current_page in self._page_access_order:
            self._page_access_order.remove(current_page)
        self._page_access_order.append(current_page)

        created_pages = list(self._created_pages.keys())

        while len(created_pages) > MAX_CACHED_SETTINGS_PAGES:
            oldest_page = None
            for page_name in self._page_access_order:
                if page_name in created_pages and page_name != current_page:
                    oldest_page = page_name
                    break

            if oldest_page is None:
                break

            self._unload_settings_page(oldest_page)
            created_pages.remove(oldest_page)
            if oldest_page in self._page_access_order:
                self._page_access_order.remove(oldest_page)

    def _unload_settings_page(self, page_name: str):
        """卸载指定的设置页面以释放内存

        Args:
            page_name: 要卸载的页面名称
        """
        if not hasattr(self, "_created_pages") or page_name not in self._created_pages:
            return

        try:
            real_page = self._created_pages.pop(page_name)
            self._cleanup_page_threads(real_page)
            container = getattr(self, page_name, None)
            if container and container.layout():
                container.layout().removeWidget(real_page)

            real_page.deleteLater()

            self._restore_page_factory(page_name, container)

            logger.debug(f"已卸载设置页面 {page_name} 以释放内存")
        except RuntimeError as e:
            logger.warning(f"卸载设置页面 {page_name} 时出现警告: {e}")
        except Exception as e:
            logger.exception(f"卸载设置页面 {page_name} 失败: {e}")

    def _cleanup_page_threads(self, widget: QWidget) -> None:
        visited: set[int] = set()
        self._cleanup_threads_in_object(widget, visited)

    def _cleanup_threads_in_object(self, obj, visited: set[int]) -> None:
        if obj is None:
            return

        obj_id = id(obj)
        if obj_id in visited:
            return
        visited.add(obj_id)

        if isinstance(obj, QThread):
            self._stop_qthread(obj)
            return

        try:
            obj_dict = vars(obj)
        except Exception:
            obj_dict = {}

        for value in obj_dict.values():
            self._cleanup_threads_in_value(value, visited)

        if isinstance(obj, QObject):
            try:
                for child in obj.children():
                    self._cleanup_threads_in_object(child, visited)
            except Exception:
                pass

    def _cleanup_threads_in_value(self, value, visited: set[int]) -> None:
        if value is None:
            return

        if isinstance(value, (str, bytes, int, float, bool)):
            return

        if isinstance(value, QThread):
            self._stop_qthread(value)
            return

        if isinstance(value, dict):
            for item in value.values():
                self._cleanup_threads_in_value(item, visited)
            return

        if isinstance(value, (list, tuple, set)):
            for item in value:
                self._cleanup_threads_in_value(item, visited)
            return

        self._cleanup_threads_in_object(value, visited)

    def _stop_qthread(self, thread: QThread) -> None:
        try:
            if not thread.isRunning():
                return
        except RuntimeError:
            return

        try:
            thread.requestInterruption()
        except Exception:
            pass

        try:
            thread.quit()
        except Exception:
            pass

        try:
            finished = thread.wait(500)
        except Exception:
            finished = False

        if finished:
            return

        try:
            thread.terminate()
        except Exception:
            return

        try:
            thread.wait(500)
        except Exception:
            pass

    def _restore_page_factory(self, page_name: str, container):
        """恢复页面工厂函数

        Args:
            page_name: 页面名称
            container: 容器对象
        """
        from app.page_building import settings_window_page

        page_definition = self._get_page_factory_definition(page_name)
        if page_definition is None:
            return

        if container is not None:
            setattr(self, page_name, container)

        page_method, is_pivot = page_definition
        self._register_deferred_factory(
            page_name, page_method, is_pivot, settings_window_page
        )

    def _materialize_deferred_page(self, name: str) -> bool:
        if name in getattr(self, "_created_pages", {}):
            return True
        if name in self._pending_page_loads:
            return False

        factory = getattr(self, "_deferred_factories", {}).get(name)
        if factory is None:
            return False

        container = self._find_container_by_name(name)
        if container is None or not hasattr(container, "layout"):
            return False

        layout = container.layout()
        if layout is None:
            self._set_placeholder_loading(container, f"页面加载失败: {name}")
            return False

        self._pending_page_loads.add(name)
        try:
            logger.debug(f"正在创建页面 {name}，预览模式: {self.is_preview}")
            real_page = factory(is_preview=self.is_preview)
            if real_page is None:
                raise RuntimeError(f"延迟页面工厂返回空页面: {name}")

            self._clear_placeholder_layout(container)
            layout.addWidget(real_page)

            self._created_pages[name] = real_page
            self._deferred_factories.pop(name, None)
            logger.debug(f"设置页面已按需创建: {name}, 预览模式: {self.is_preview}")
            return True
        except Exception as e:
            self._set_placeholder_loading(container, f"页面加载失败: {name}")
            logger.exception(f"延迟创建设置页面 {name} 失败: {e}")
            return False
        finally:
            self._pending_page_loads.discard(name)

    def _create_deferred_page(self, name: str):
        """根据名字创建对应延迟工厂并把结果加入占位容器

        Args:
            name: 页面名称
        """
        try:
            container = self._find_container_by_name(name)
            if container is not None:
                self._set_placeholder_loading(container, "正在加载页面...")
            self._materialize_deferred_page(name)
        except Exception as e:
            logger.exception(f"_create_deferred_page 失败: {e}")

    def _ensure_deferred_page_loaded(self, name: str) -> None:
        self._materialize_deferred_page(name)

    def _find_container_by_name(self, name: str):
        """根据名称查找容器

        Args:
            name: 容器名称

        Returns:
            QWidget: 容器对象或None
        """
        container_attrs = list(iter_settings_page_container_names()) + [
            "customSettingsInterface"
        ]

        for attr in container_attrs:
            container_obj = getattr(self, attr, None)
            if container_obj and container_obj.objectName() == name:
                return container_obj

        return None

    # ==================================================
    # 后台预热
    # ==================================================

    def _background_warmup_pages(
        self,
        interval_ms: int = 800,
        max_preload: int = 1,
    ):
        """分批（间隔）创建剩余的设置页面，减少单次阻塞

        内存优化：完全禁用后台预热，所有页面按需加载

        Args:
            interval_ms: 每个页面创建间隔（毫秒）（已禁用）
            max_preload: 最大预加载数量（已禁用）
        """
        pass

    def _background_warmup_non_pivot(self, interval_ms: int = 80):
        """在设置窗口首次打开时，分批延时创建所有非 pivot（单页面）项

        内存优化：禁用自动预热，完全按需加载

        Args:
            interval_ms: 每个页面创建的间隔毫秒数
        """
        try:
            pass
        except Exception as e:
            logger.exception(f"后台预热非 pivot 页面失败: {e}")

    # ==================================================
    # 窗口显示
    # ==================================================

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
