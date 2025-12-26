# 标准库导入
from typing import Dict, Any

# 第三方库导入
from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtNetwork import *
from qfluentwidgets import *
from loguru import logger

# 本地模块导入
from app.tools.personalised import load_custom_font, get_theme_icon, is_dark_theme
from app.tools.settings_access import (
    readme_settings_async,
    update_settings,
    get_settings_signals,
)
from app.tools.path_utils import *
from app.Language.obtain_language import get_content_combo_name_async
from app.common.extraction.extract import _is_non_class_time
from app.common.safety.verify_ops import require_and_run


class LevitationWindow(QWidget):
    """
    悬浮窗窗口类
    提供可拖拽、贴边隐藏、主题切换等功能的悬浮窗口
    """

    # ==================== 信号定义 ====================
    rollCallRequested = Signal()
    quickDrawRequested = Signal()
    lotteryRequested = Signal()
    visibilityChanged = Signal(bool)
    positionChanged = Signal(int, int)

    # ==================== 类常量 ====================
    DEFAULT_OPACITY = 0.8
    DEFAULT_PLACEMENT = 0
    DEFAULT_DISPLAY_STYLE = 0
    DEFAULT_EDGE_THRESHOLD = 5
    DEFAULT_RETRACT_SECONDS = 5
    DEFAULT_LONG_PRESS_MS = 500
    DEFAULT_BUTTON_SIZE = QSize(60, 60)
    DEFAULT_ICON_SIZE = QSize(24, 24)
    DEFAULT_SPACING = 6
    DEFAULT_MARGINS = 6  # 贴边隐藏时的最小间距
    DRAG_THRESHOLD = 3  # 拖拽触发阈值

    def __init__(self, parent=None):
        """初始化悬浮窗窗口"""
        super().__init__(parent)

        # ==================== 基础设置 ====================
        self._setup_window_properties()

        # ==================== 拖拽相关属性 ====================
        self._init_drag_properties()

        # ==================== 贴边隐藏属性 ====================
        self._init_edge_properties()

        # ==================== UI相关属性 ====================
        self._init_ui_properties()

        # ==================== 周期性置顶属性 ====================
        self._init_periodic_topmost_properties()

        # ==================== 初始化配置 ====================
        self._init_settings()

        # ==================== 构建UI ====================
        self._build_ui()
        self._apply_window()
        self._apply_position()
        self._install_drag_filters()

        # ==================== 信号连接 ====================
        self._connect_signals()

        # ==================== 主题应用 ====================
        self._apply_theme_style()

        # ==================== 启动周期性置顶 ====================
        self._start_periodic_topmost()

    # ==================== 初始化方法 ====================

    def _setup_window_properties(self):
        """设置窗口基础属性"""
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
            | Qt.NoDropShadowWindowHint
            | Qt.NoFocus
        )

    def _init_drag_properties(self):
        """初始化拖拽相关属性"""
        self._shadow = None
        self._drag_timer = QTimer(self)
        self._drag_timer.setSingleShot(True)
        self._drag_timer.timeout.connect(self._begin_drag)
        self._dragging = False
        self._press_pos = QPoint()
        self._draggable = True

    def _init_edge_properties(self):
        """初始化贴边隐藏相关属性"""
        self._indicator = None
        self._retract_timer = QTimer(self)
        self._retract_timer.setSingleShot(True)
        self._retracted = False
        self._last_stuck = False
        self._edge_threshold = self.DEFAULT_EDGE_THRESHOLD
        self._stick_to_edge = True
        self._retract_seconds = self.DEFAULT_RETRACT_SECONDS
        self._long_press_ms = self.DEFAULT_LONG_PRESS_MS

    def _init_ui_properties(self):
        """初始化UI相关属性"""
        self._buttons_spec = []
        self._font_family = load_custom_font() or QFont().family()
        self._container = QWidget(self)
        self._layout = None
        self._btn_size = self.DEFAULT_BUTTON_SIZE
        self._icon_size = self.DEFAULT_ICON_SIZE
        self._spacing = self.DEFAULT_SPACING
        self._margins = self.DEFAULT_MARGINS
        self._placement = self.DEFAULT_PLACEMENT
        self._display_style = self.DEFAULT_DISPLAY_STYLE

    def _init_periodic_topmost_properties(self):
        """初始化周期性置顶相关属性"""
        self._periodic_topmost_timer = QTimer(self)
        self._periodic_topmost_timer.timeout.connect(self._periodic_topmost)
        self._periodic_topmost_interval = 100

    def _start_periodic_topmost(self):
        """启动周期性置顶定时器"""
        self._periodic_topmost_timer.start(self._periodic_topmost_interval)

    def _periodic_topmost(self):
        """周期性将窗口置顶"""
        if self.isVisible():
            self.raise_()

    def _connect_signals(self):
        """连接信号"""
        get_settings_signals().settingChanged.connect(self._on_setting_changed)
        # 连接主题变更信号
        try:
            qconfig.themeChanged.connect(self._on_theme_changed)
        except Exception as e:
            logger.exception("连接 themeChanged 信号时出错（已忽略）: {}", e)

    def rebuild_ui(self):
        """
        重新构建浮窗UI
        删除当前布局并创建新的布局
        """
        # 清除现有按钮
        self._clear_buttons()

        # 重新创建容器布局
        container_layout = self._create_container_layout()

        # 设置新的布局
        old_layout = self._container.layout()
        if old_layout:
            QWidget().setLayout(old_layout)  # 从容器中移除旧布局

        self._container.setLayout(container_layout)

        # 重新添加按钮
        for i, spec in enumerate(self._buttons_spec):
            btn = self._create_button(spec)
            self._add_button(btn, i, len(self._buttons_spec))

        self._container.adjustSize()
        self.adjustSize()
        self._install_drag_filters()

    def _clear_buttons(self):
        """清除所有按钮"""
        # 清除顶层和底层的按钮
        if hasattr(self, "_top") and self._top and self._top.layout():
            top_layout = self._top.layout()
            while top_layout.count():
                item = top_layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()

        if hasattr(self, "_bottom") and self._bottom and self._bottom.layout():
            bottom_layout = self._bottom.layout()
            while bottom_layout.count():
                item = bottom_layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()

        # 清除容器直接包含的按钮
        container_layout = self._container.layout()
        if container_layout:
            while container_layout.count():
                item = container_layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()

    def _font(self, size):
        s = int(size) if size and int(size) > 0 else 8
        if s <= 0:
            s = 8
        f = QFont(self._font_family) if self._font_family else QFont()
        if s > 0:  # 确保字体大小大于0
            f.setPointSize(s)
        return f

    def _apply_theme_style(self):
        # 主题样式应用：深色/浅色配色修正
        dark = is_dark_theme(qconfig)
        self._container.setAttribute(Qt.WA_StyledBackground, True)
        if dark:
            self._container.setStyleSheet(
                "background-color: rgba(32,32,32,180); border-radius: 12px; border: 1px solid rgba(255,255,255,20);"
            )
        else:
            self._container.setStyleSheet(
                "background-color: rgba(255,255,255,220); border-radius: 12px; border: 1px solid rgba(0,0,0,12);"
            )

    def _icon_pixmap(self, icon):
        if hasattr(icon, "icon"):
            qicon = icon.icon()
        elif isinstance(icon, QIcon):
            qicon = icon
        else:
            qicon = QIcon()
        return qicon.pixmap(self._icon_size)

    def _init_settings(self):
        """初始化设置配置"""
        # 基础显示设置
        self._visible_on_start = self._get_bool_setting(
            "floating_window_management", "startup_display_floating_window", False
        )
        self._opacity = self._get_float_setting(
            "floating_window_management",
            "floating_window_opacity",
            self.DEFAULT_OPACITY,
        )

        # 布局设置
        self._placement = self._get_int_setting(
            "floating_window_management",
            "floating_window_placement",
            self.DEFAULT_PLACEMENT,
        )
        self._display_style = self._get_int_setting(
            "floating_window_management",
            "floating_window_display_style",
            self.DEFAULT_DISPLAY_STYLE,
        )

        # 拖拽设置
        self._draggable = self._get_bool_setting(
            "floating_window_management", "floating_window_draggable", True
        )
        self._long_press_ms = self._get_int_setting(
            "floating_window_management",
            "floating_window_long_press_duration",
            self.DEFAULT_LONG_PRESS_MS,
        )

        # 贴边设置
        self._stick_to_edge = self._get_bool_setting(
            "floating_window_management", "floating_window_stick_to_edge", True
        )
        self._retract_seconds = self._get_int_setting(
            "floating_window_management",
            "floating_window_stick_to_edge_recover_seconds",
            self.DEFAULT_RETRACT_SECONDS,
        )
        self._stick_indicator_style = self._get_int_setting(
            "floating_window_management",
            "floating_window_stick_to_edge_display_style",
            0,
        )

        # 按钮配置
        button_control_idx = self._get_int_setting(
            "floating_window_management", "floating_window_button_control", 0
        )
        self._buttons_spec = self._map_button_control(button_control_idx)

        # 贴边隐藏功能配置
        self._init_edge_hide_settings()

    def _get_bool_setting(self, section: str, key: str, default: bool = False) -> bool:
        """获取布尔类型设置"""
        return bool(readme_settings_async(section, key) or default)

    def _get_int_setting(self, section: str, key: str, default: int = 0) -> int:
        """获取整数类型设置"""
        return int(readme_settings_async(section, key) or default)

    def _get_float_setting(self, section: str, key: str, default: float = 0.0) -> float:
        """获取浮点数类型设置"""
        return float(readme_settings_async(section, key) or default)

    def _init_edge_hide_settings(self):
        """初始化贴边隐藏功能设置"""
        self.floating_window_stick_to_edge = self._get_bool_setting(
            "floating_window_management", "floating_window_stick_to_edge", False
        )
        self.custom_retract_time = self._retract_seconds  # 复用现有的贴边回收秒数配置
        self.custom_display_mode = (
            self._stick_indicator_style
        )  # 复用现有的贴边显示样式配置
        self._retracted = False

        logger.debug(f"贴边隐藏功能配置: {self.floating_window_stick_to_edge}")

    def _build_ui(self):
        # 两行布局按索引分配，避免 3+ 个按钮全部落到底部
        lay = self._container.layout()
        if lay:
            while lay.count():
                item = lay.takeAt(0)
                w = item.widget()
                if w:
                    w.setParent(None)
                    w.deleteLater()
            lay.deleteLater()
        if not self._layout:
            self._layout = QHBoxLayout(self)
            self._layout.setContentsMargins(
                self._margins, self._margins, self._margins, self._margins
            )
            self._layout.addWidget(self._container)
        else:
            self._layout.setContentsMargins(
                self._margins, self._margins, self._margins, self._margins
            )
        self._container_layout = self._create_container_layout()
        self._container.setLayout(self._container_layout)
        self._container_layout.setAlignment(Qt.AlignCenter)
        for i, spec in enumerate(self._buttons_spec):
            btn = self._create_button(spec)
            self._add_button(btn, i, len(self._buttons_spec))
        self._container.adjustSize()
        self.adjustSize()
        self._install_drag_filters()

    def _apply_window(self):
        self.setWindowOpacity(self._opacity)
        if self._visible_on_start:
            self.show()
            # 浮窗显示后立即检测边缘
            QTimer.singleShot(100, self._check_edge_proximity)
        else:
            self.hide()

    def showEvent(self, event):
        """重写showEvent，当浮窗显示时检测边缘"""
        super().showEvent(event)
        QTimer.singleShot(100, self._check_edge_proximity)

    def _apply_position(self):
        x = int(readme_settings_async("float_position", "x") or 100)
        y = int(readme_settings_async("float_position", "y") or 100)
        nx, ny = self._clamp_to_screen(x, y)
        self.move(nx, ny)

    def _clamp_to_screen(self, x, y):
        fg = self.frameGeometry()
        scr = QGuiApplication.screenAt(fg.center()) or QApplication.primaryScreen()
        geo = scr.availableGeometry()
        cx = max(geo.left(), min(x, geo.right() - self.width() + 1))
        cy = max(geo.top(), min(y, geo.bottom() - self.height() + 1))
        return cx, cy

    def _create_container_layout(self):
        if hasattr(self, "_top") and self._top:
            self._top.deleteLater()
            self._top = None
        if hasattr(self, "_bottom") and self._bottom:
            self._bottom.deleteLater()
            self._bottom = None
        if self._placement == 1:  # 垂直布局
            lay = QVBoxLayout()
            lay.setContentsMargins(
                self._margins, self._margins, self._margins, self._margins
            )
            lay.setSpacing(self._spacing)
            return lay
        if self._placement == 2:  # 水平布局
            lay = QHBoxLayout()
            lay.setContentsMargins(
                self._margins, self._margins, self._margins, self._margins
            )
            lay.setSpacing(self._spacing)
            return lay
        lay = QVBoxLayout()
        lay.setContentsMargins(
            self._margins, self._margins, self._margins, self._margins
        )
        lay.setSpacing(self._spacing)
        self._top = QWidget()
        self._top.setAttribute(Qt.WA_TranslucentBackground)
        self._bottom = QWidget()
        self._bottom.setAttribute(Qt.WA_TranslucentBackground)
        t = QHBoxLayout(self._top)
        t.setContentsMargins(0, 0, 0, 0)
        t.setSpacing(self._spacing)
        t.setAlignment(Qt.AlignCenter)
        b = QHBoxLayout(self._bottom)
        b.setContentsMargins(0, 0, 0, 0)
        b.setSpacing(self._spacing)
        b.setAlignment(Qt.AlignCenter)
        lay.addWidget(self._top)
        lay.addWidget(self._bottom)
        return lay

    def _emit_signal(self, signal):
        """发出信号的辅助方法"""
        signal.emit()

    def _handle_button_click(self, signal):
        """处理按钮点击事件，添加时间检查逻辑

        Args:
            signal: 要发出的信号
        """
        # 检查是否是闪抽按钮
        if signal == self.quickDrawRequested:
            # 检查当前时间是否在非上课时间段内
            if _is_non_class_time():
                # 检查是否需要验证流程
                if readme_settings_async("time_settings", "verification_required"):
                    # 如果需要验证流程，弹出密码验证窗口
                    logger.info("当前时间在非上课时间段内，需要密码验证")
                    require_and_run(
                        "quick_draw", self, lambda: self._emit_signal(signal)
                    )
                    return
                else:
                    # 如果不需要验证流程，直接禁止点击
                    logger.info("当前时间在非上课时间段内，禁止闪抽")
                    return
        # 发出信号
        signal.emit()

    def _create_button(self, spec: str) -> QPushButton:
        """创建按钮

        Args:
            spec: 按钮类型标识

        Returns:
            创建好的按钮实例
        """
        # 获取按钮配置信息
        button_config = self._get_button_config(spec)
        icon = button_config["icon"]
        text = button_config["text"]
        signal = button_config["signal"]

        # 根据显示样式创建不同类型的按钮
        if self._display_style == 1:
            btn = self._create_icon_only_button(icon)
        elif self._display_style == 2:
            btn = self._create_text_only_button(text)
        else:
            btn = self._create_composite_button(icon, text)

        # 连接信号
        btn.clicked.connect(lambda: self._handle_button_click(signal))
        btn.setAttribute(Qt.WA_TranslucentBackground)
        return btn

    def _get_button_config(self, spec: str) -> Dict[str, Any]:
        """获取按钮配置信息

        Args:
            spec: 按钮类型标识

        Returns:
            按钮配置字典，包含图标、文本和信号
        """
        text_map = get_content_combo_name_async(
            "floating_window_management", "floating_window_button_control"
        )
        names = list(text_map)

        button_configs = {
            "roll_call": {
                "icon": get_theme_icon("ic_fluent_people_20_filled"),
                "text": names[0],
                "signal": self.rollCallRequested,
            },
            "quick_draw": {
                "icon": get_theme_icon("ic_fluent_flash_20_filled"),
                "text": names[1],
                "signal": self.quickDrawRequested,
            },
            "lottery": {
                "icon": get_theme_icon("ic_fluent_gift_20_filled"),
                "text": names[2],
                "signal": self.lotteryRequested,
            },
        }

        # 默认配置（点名按钮）
        default_config = {
            "icon": get_theme_icon("ic_fluent_people_20_filled"),
            "text": names[0],
            "signal": self.rollCallRequested,
        }

        return button_configs.get(spec, default_config)

    def _create_icon_only_button(self, icon: QIcon) -> TransparentToolButton:
        """创建仅图标按钮"""
        btn = TransparentToolButton()
        btn.setIcon(icon)
        btn.setIconSize(self._icon_size)
        btn.setFixedSize(self._btn_size)
        btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        btn.setAttribute(Qt.WA_TranslucentBackground)
        btn.setStyleSheet("background: transparent; border: none;")
        return btn

    def _create_text_only_button(self, text: str) -> PushButton:
        """创建仅文本按钮"""
        btn = PushButton(text)
        btn.setFixedSize(self._btn_size)
        btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        btn.setFont(self._font(12))
        btn.setAttribute(Qt.WA_TranslucentBackground)
        btn.setStyleSheet("background: transparent; border: none;")
        return btn

    def _create_composite_button(self, icon: QIcon, text: str) -> QPushButton:
        """创建图文复合按钮"""
        btn = QPushButton()
        layout = QVBoxLayout(btn)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(2)
        layout.setAlignment(Qt.AlignCenter)
        btn.setStyleSheet("background: transparent; border: none;")

        # 图标标签
        icon_label = self._create_icon_label(icon)
        layout.addWidget(icon_label)

        # 文本标签
        text_label = self._create_text_label(text)
        layout.addWidget(text_label)

        # 布局设置
        layout.setAlignment(Qt.AlignCenter)
        layout.setAlignment(icon_label, Qt.AlignCenter)
        layout.setAlignment(text_label, Qt.AlignCenter)

        btn.setFixedSize(self._btn_size)
        btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        btn.setAttribute(Qt.WA_TranslucentBackground)
        return btn

    def _create_icon_label(self, icon: QIcon) -> TransparentToolButton:
        """创建图标标签（用于复合按钮）"""
        label = TransparentToolButton()
        label.setIcon(icon)
        label.setIconSize(self._icon_size)
        label.setFixedSize(self._icon_size)
        # 复合按钮图标不置灰，避免低对比；忽略鼠标事件
        label.setAttribute(Qt.WA_TransparentForMouseEvents, True)  # 忽略鼠标事件
        label.setFocusPolicy(Qt.NoFocus)  # 无焦点
        # 标签样式：居中对齐、无背景、无边框
        label.setStyleSheet("background: transparent; border: none;")
        return label

    def _create_text_label(self, text: str) -> BodyLabel:
        """创建文本标签（用于复合按钮）"""
        label = BodyLabel(text)
        label.setAlignment(Qt.AlignCenter)
        label.setFont(self._font(10))
        label.setAttribute(Qt.WA_TransparentForMouseEvents, True)  # 忽略鼠标事件
        label.setFocusPolicy(Qt.NoFocus)  # 无焦点
        # 标签样式：居中对齐、无背景、无边框
        label.setStyleSheet("background: transparent; border: none;")
        return label

    def _add_button(self, btn, index, total):
        if self._placement == 1:
            self._container.layout().addWidget(btn, 0, Qt.AlignCenter)
            return
        if self._placement == 2:
            self._container.layout().addWidget(btn, 0, Qt.AlignCenter)
            return
        # 前半放顶行，后半放底行
        split = (total + 1) // 2
        if index < split:
            self._top.layout().addWidget(btn, 0, Qt.AlignCenter)
        else:
            self._bottom.layout().addWidget(btn, 0, Qt.AlignCenter)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton and self._draggable:
            self._press_pos = e.globalPosition().toPoint()
            self._dragging = False
            self._drag_timer.stop()
            self._drag_timer.start(self._long_press_ms)

    def _begin_drag(self):
        self._dragging = True
        self.setCursor(Qt.ClosedHandCursor)
        pass

    def mouseMoveEvent(self, e):
        """处理鼠标移动事件"""
        if e.buttons() & Qt.LeftButton and self._draggable:
            cur = e.globalPosition().toPoint()

            # 检查是否需要开始拖拽
            if not self._dragging:
                delta = cur - self._press_pos
                if self._should_start_drag(delta):
                    self._begin_drag()

            # 执行拖拽
            if self._dragging:
                delta = cur - self._press_pos
                self.move(self.x() + delta.x(), self.y() + delta.y())
                self._press_pos = cur
                self._cancel_retract()

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._drag_timer.stop()
            self.setCursor(Qt.ArrowCursor)
            if self._draggable and self._dragging:
                self._dragging = False
                self._save_position()

    def _should_start_drag(self, delta: QPoint) -> bool:
        """判断是否应该开始拖拽

        Args:
            delta: 鼠标移动偏移量

        Returns:
            是否应该开始拖拽
        """
        return (
            abs(delta.x()) >= self.DRAG_THRESHOLD
            or abs(delta.y()) >= self.DRAG_THRESHOLD
        )

    def eventFilter(self, obj, event):
        """事件过滤器，处理拖拽相关事件"""
        if not self._draggable:
            return False

        if event.type() == QEvent.MouseButtonPress:
            return self._handle_mouse_press_event(event)
        elif event.type() == QEvent.MouseMove:
            return self._handle_mouse_move_event(event)
        elif event.type() == QEvent.MouseButtonRelease:
            return self._handle_mouse_release_event(event)

        return False

    def _handle_mouse_press_event(self, event) -> bool:
        """处理鼠标按下事件"""
        if event.button() == Qt.LeftButton:
            self._press_pos = event.globalPosition().toPoint()
            self._dragging = False
            self._drag_timer.stop()
            self._drag_timer.start(self._long_press_ms)
        return False

    def _handle_mouse_move_event(self, event) -> bool:
        """处理鼠标移动事件"""
        if event.buttons() & Qt.LeftButton:
            cur = event.globalPosition().toPoint()

            # 检查是否需要开始拖拽
            if not self._dragging:
                delta = cur - self._press_pos
                if self._should_start_drag(delta):
                    self._begin_drag()

            # 执行拖拽
            if self._dragging:
                delta = cur - self._press_pos
                self.move(self.x() + delta.x(), self.y() + delta.y())
                self._press_pos = cur
                return True

        return False

    def _handle_mouse_release_event(self, event) -> bool:
        """处理鼠标释放事件"""
        if event.button() == Qt.LeftButton:
            self._drag_timer.stop()
            if self._dragging:
                self._end_drag_operation()
                return True

        return False

    def _end_drag_operation(self):
        """结束拖拽操作"""
        self._dragging = False
        self.setCursor(Qt.ArrowCursor)
        self._stick_to_nearest_edge()

        self._save_position()

        # 如果启用了边缘贴边隐藏功能，在拖动结束后检查是否需要贴边
        if self.floating_window_stick_to_edge:
            QTimer.singleShot(100, self._check_edge_proximity)

    def _install_drag_filters(self):
        self._container.installEventFilter(self)
        for w in self._container.findChildren(QWidget):
            w.installEventFilter(self)

    def enterEvent(self, e):
        # 当鼠标进入窗口时，删除可能存在的自动隐藏定时器
        if hasattr(self, "_auto_hide_timer"):
            if self._auto_hide_timer.isActive():
                self._auto_hide_timer.stop()
            # 从对象中移除定时器属性，避免内存泄漏
            delattr(self, "_auto_hide_timer")

    def leaveEvent(self, e):
        # 如果启用了新的贴边隐藏功能，使用新的自动隐藏逻辑
        if self.floating_window_stick_to_edge:
            # 如果已经处于收纳状态，不需要额外处理
            if not self._retracted:
                # 清除旧的定时器
                if (
                    hasattr(self, "_auto_hide_timer")
                    and self._auto_hide_timer.isActive()
                ):
                    self._auto_hide_timer.stop()
                # 创建或重置自动隐藏定时器
                self._auto_hide_timer = QTimer(self)
                self._auto_hide_timer.setSingleShot(True)
                self._auto_hide_timer.timeout.connect(self._auto_hide_window)
                # 设置延迟时间
                self._auto_hide_timer.start(self.custom_retract_time * 1000)

    def _stick_to_nearest_edge(self):
        if not self._stick_to_edge:
            return
        fg = self.frameGeometry()
        scr = QGuiApplication.screenAt(fg.center()) or QApplication.primaryScreen()
        geo = scr.availableGeometry()
        left = fg.left() - geo.left()
        right = geo.right() - fg.right()
        self._last_stuck = False
        if left <= self._edge_threshold:
            self.move(geo.left(), self.y())
            self._last_stuck = True
            return
        if right <= self._edge_threshold:
            self.move(geo.right() - self.width() + 1, self.y())
            self._last_stuck = True

    def _cancel_retract(self):
        if self._retract_timer.isActive():
            self._retract_timer.stop()

    def _retract_into_edge(self):
        # 防多屏错位：基于当前屏幕几何
        fg = self.frameGeometry()
        scr = QGuiApplication.screenAt(fg.center()) or QApplication.primaryScreen()
        geo = scr.availableGeometry()
        if self.x() <= geo.left():
            # 完全移出屏幕左侧
            self.move(geo.left() - self.width(), self.y())
            self._retracted = True
        elif self.x() + self.width() >= geo.right():
            # 完全移出屏幕右侧
            self.move(geo.right(), self.y())
            self._retracted = True

    def _expand_from_edge(self):
        # 基于当前屏幕可用区域展开
        fg = self.frameGeometry()
        scr = QGuiApplication.screenAt(fg.center()) or QApplication.primaryScreen()
        geo = scr.availableGeometry()
        if self.x() < geo.left():
            self.move(geo.left(), self.y())
        elif self.x() + self.width() > geo.right():
            self.move(geo.right() - self.width() + 1, self.y())
        self._retracted = False

    def _check_edge_proximity(self):
        """检测窗口是否靠近屏幕边缘，并实现贴边隐藏功能（带动画效果）"""
        logger.debug("开始检查边缘贴边隐藏功能")

        # 如果有正在进行的动画，先停止它
        if (
            hasattr(self, "animation")
            and self.animation.state() == QPropertyAnimation.Running
        ):
            self.animation.stop()

        logger.debug(f"贴边隐藏功能状态: {self.floating_window_stick_to_edge}")

        # 如果贴边隐藏功能未启用，直接返回
        if not self.floating_window_stick_to_edge:
            logger.debug("贴边隐藏功能未启用，跳过检测")
            return

        # 获取屏幕尺寸
        screen = QApplication.primaryScreen().availableGeometry()

        # 获取窗口当前位置和尺寸
        window_pos = self.pos()
        window_width = self.width()
        window_height = self.height()

        # 定义边缘阈值（像素）
        edge_threshold = 5
        hidden_width = 10  # 隐藏后露出的宽度

        # 检测左边缘
        if window_pos.x() <= edge_threshold:
            # 保存主浮窗的原始位置（但不更新实际坐标）
            if not hasattr(self, "_original_position"):
                self._original_position = window_pos

            # 创建平滑动画效果
            self.animation = QPropertyAnimation(self, b"geometry")
            # 设置动画持续时间（更流畅的过渡）
            self.animation.setDuration(400)
            # 设置缓动曲线（使用更自然的缓动）
            self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)

            # 设置动画起始值（当前位置）
            self.animation.setStartValue(self.geometry())

            # 设置动画结束值（隐藏位置）- 完全移出屏幕
            end_rect = QRect(
                -window_width,
                window_pos.y(),
                window_width,
                window_height,
            )
            self.animation.setEndValue(end_rect)

            # 动画完成后创建收纳浮窗
            def on_animation_finished():
                logger.debug(
                    f"贴边隐藏动画完成，选择显示样式: {self._stick_indicator_style}"
                )
                # 根据配置选择创建收纳浮窗或箭头按钮
                if self._stick_indicator_style == 0:  # 使用收纳浮窗
                    logger.debug("创建收纳浮窗")
                    self._create_storage_window(
                        "right", 0, window_pos.y() + window_height // 2 - 30
                    )
                else:  # 使用箭头按钮
                    logger.debug("创建DraggableWidget箭头按钮")
                    self._create_arrow_button(
                        "right", 0, window_pos.y() + window_height // 2 - 15
                    )
                # 标记为已收纳状态，但保持原始坐标不变
                self._retracted = True

            self.animation.finished.connect(on_animation_finished)

            # 启动动画
            self.animation.start()
            return

        # 检测右边缘
        elif window_pos.x() + window_width >= screen.width() - edge_threshold:
            # 保存主浮窗的原始位置（但不更新实际坐标）
            if not hasattr(self, "_original_position"):
                self._original_position = window_pos

            # 创建平滑动画效果
            self.animation = QPropertyAnimation(self, b"geometry")
            # 设置动画持续时间（更流畅的过渡）
            self.animation.setDuration(400)
            # 设置缓动曲线（使用更自然的缓动）
            self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)

            # 设置动画起始值（当前位置）
            self.animation.setStartValue(self.geometry())

            # 设置动画结束值（隐藏位置）- 完全移出屏幕
            end_rect = QRect(
                screen.width(),
                window_pos.y(),
                window_width,
                window_height,
            )
            self.animation.setEndValue(end_rect)

            # 动画完成后创建收纳浮窗
            def on_animation_finished():
                logger.debug(
                    f"贴边隐藏动画完成，选择显示样式: {self._stick_indicator_style}"
                )
                # 根据配置选择创建收纳浮窗或箭头按钮
                if self._stick_indicator_style == 0:  # 使用收纳浮窗
                    logger.debug("创建收纳浮窗")
                    self._create_storage_window(
                        "left",
                        screen.width() - 30,
                        window_pos.y() + window_height // 2 - 30,
                    )
                else:  # 使用箭头按钮
                    logger.debug("创建DraggableWidget箭头按钮")
                    self._create_arrow_button(
                        "left",
                        screen.width() - 30,
                        window_pos.y() + window_height // 2 - 15,
                    )
                # 标记为已收纳状态，但保持原始坐标不变
                self._retracted = True

            self.animation.finished.connect(on_animation_finished)

            # 启动动画
            self.animation.start()
            return

        # 保存新位置（仅在窗口未贴边隐藏时）
        if (
            window_pos.x() > edge_threshold
            and window_pos.x() + window_width < screen.width() - edge_threshold
        ):
            # 只有在非收纳状态下才保存位置
            if not self._retracted:
                self._save_position()
            # 清除原始位置
            if hasattr(self, "_original_position"):
                delattr(self, "_original_position")

        self._retracted = False

    def _create_storage_window(self, direction, x, y):
        """创建只能在y轴移动的收纳浮窗"""
        # 先删除可能存在的收纳浮窗
        self._delete_storage_window()

        # 创建收纳浮窗
        self.storage_window = QWidget()
        self.storage_window.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
            | Qt.NoFocus
            | Qt.NoDropShadowWindowHint
        )
        self.storage_window.setAttribute(Qt.WA_TranslucentBackground)

        # 设置收纳浮窗尺寸
        self.storage_window.setFixedSize(30, 30)

        # 根据主题设置不同的背景颜色，与主浮窗保持一致
        dark = is_dark_theme(qconfig)
        opacity = self._opacity

        if dark:
            bg_color = f"rgba(32, 32, 32, {opacity})"
            color = "#ffffff"
        else:
            bg_color = f"rgba(255, 255, 255, {opacity})"
            color = "#000000"

        # 设置收纳浮窗样式，与主浮窗保持一致的风格
        self.storage_window.setStyleSheet(
            f"background-color: {bg_color};"
            "border-radius: 15px;"
            "border: 1px solid rgba(0, 0, 0, 12);"
            "background-clip: padding-box;"
        )

        # 创建标签显示内容
        label = BodyLabel(self.storage_window)
        label.setAlignment(Qt.AlignCenter)

        # 根据方向设置显示内容
        if direction == "right":
            label.setText(">")
        elif direction == "left":
            label.setText("<")

        label.setStyleSheet(f"color: {color}; font-size: 12px; font-weight: bold;")
        label.setGeometry(0, 0, 30, 30)

        # 设置收纳浮窗位置
        self.storage_window.move(x, y)

        # 初始化拖动相关属性
        self._storage_dragging = False
        self._storage_drag_start = QPoint()

        # 连接鼠标事件
        self.storage_window.mousePressEvent = self._on_storage_press
        self.storage_window.mouseMoveEvent = self._on_storage_move
        self.storage_window.mouseReleaseEvent = self._on_storage_release

        # 存储收纳浮窗方向和初始位置
        self._storage_direction = direction
        self._storage_initial_x = x

        # 显示收纳浮窗
        self.storage_window.show()

    def _smart_snap_to_edge(self):
        """智能吸附到屏幕边缘"""
        if not hasattr(self, "storage_window") or not self.storage_window:
            return

        # 获取屏幕信息
        screen = QApplication.primaryScreen().availableGeometry()
        current_pos = self.storage_window.pos()
        window_height = self.storage_window.height()

        # 计算吸附阈值
        snap_threshold = 50

        # 计算目标Y位置
        target_y = current_pos.y()

        # 检查是否靠近屏幕顶部或底部
        if current_pos.y() < screen.top() + snap_threshold:
            # 吸附到顶部
            target_y = screen.top() + 10
        elif current_pos.y() + window_height > screen.bottom() - snap_threshold:
            # 吸附到底部
            target_y = screen.bottom() - window_height - 10
        else:
            # 检查是否靠近其他常用位置（屏幕中央等）
            screen_center_y = screen.center().y()
            if (
                abs(current_pos.y() + window_height // 2 - screen_center_y)
                < snap_threshold
            ):
                target_y = screen_center_y - window_height // 2

        # 如果位置需要调整，添加平滑动画
        if target_y != current_pos.y():
            snap_animation = QPropertyAnimation(self.storage_window, b"geometry")
            snap_animation.setDuration(200)
            snap_animation.setEasingCurve(QEasingCurve.Type.OutBack)
            start_rect = self.storage_window.geometry()
            end_rect = QRect(
                self._storage_initial_x,
                target_y,
                start_rect.width(),
                start_rect.height(),
            )
            snap_animation.setStartValue(start_rect)
            snap_animation.setEndValue(end_rect)
            snap_animation.start()

            # 更新存储的位置
            self._storage_initial_x = self._storage_initial_x

    def _delete_storage_window(self):
        """删除收纳浮窗"""
        if hasattr(self, "storage_window") and self.storage_window:
            self.storage_window.deleteLater()
            self.storage_window = None

    def _on_storage_press(self, event):
        """收纳浮窗按下事件 - 增强拖动体验"""
        if event.button() == Qt.LeftButton:
            self._storage_drag_start = event.pos()
            self._storage_dragging = False

            # 添加按下视觉反馈
            if hasattr(self, "storage_window") and self.storage_window:
                current_style = self.storage_window.styleSheet()
                if "background-clip: padding-box;" in current_style:
                    # 提取颜色值并添加按下效果
                    rgba_part = current_style.split("rgba(")[1].split(")")[0]
                    press_style = (
                        current_style.split("background-color: rgba(")[0]
                        + "background-color: rgba("
                        + rgba_part
                        + ", "
                        + str(min(float(self._opacity) + 0.1, 1.0))
                        + ");"
                        + "border: 2px solid rgba(255, 255, 255, 0.5);"
                        + "background-clip: padding-box;"
                    )
                    self.storage_window.setStyleSheet(press_style)

    def _on_storage_move(self, event):
        """收纳浮窗移动事件 - 增强拖动体验"""
        if event.buttons() & Qt.LeftButton:
            delta = event.pos() - self._storage_drag_start
            if not self._storage_dragging:
                # 检测是否超过拖动阈值
                if abs(delta.y()) > 3:
                    self._storage_dragging = True
            if self._storage_dragging:
                # 只在y轴移动，x轴保持固定
                new_y = self.storage_window.y() + delta.y()
                # 限制在屏幕内
                screen = QApplication.primaryScreen().availableGeometry()
                new_y = max(
                    screen.top(),
                    min(new_y, screen.bottom() - self.storage_window.height()),
                )
                self.storage_window.move(self._storage_initial_x, new_y)

                # 添加拖动时的视觉反馈
                if hasattr(self, "storage_window") and self.storage_window:
                    current_style = self.storage_window.styleSheet()
                    if "background-clip: padding-box;" in current_style:
                        # 拖动时增加透明度并添加阴影效果
                        rgba_part = current_style.split("rgba(")[1].split(")")[0]
                        drag_style = (
                            current_style.split("background-color: rgba(")[0]
                            + "background-color: rgba("
                            + rgba_part
                            + ", "
                            + str(min(float(self._opacity) + 0.15, 1.0))
                            + ");"
                            + "border: 1px solid rgba(255, 255, 255, 0.4);"
                            + "background-clip: padding-box;"
                        )
                        self.storage_window.setStyleSheet(drag_style)

    def _on_storage_release(self, event):
        """收纳浮窗释放事件 - 增强交互体验"""
        if event.button() == Qt.LeftButton:
            # 恢复原始样式
            if hasattr(self, "storage_window") and self.storage_window:
                current_style = self.storage_window.styleSheet()
                if "background-clip: padding-box;" in current_style:
                    # 提取颜色值并恢复原始样式
                    rgba_part = current_style.split("rgba(")[1].split(")")[0]
                    original_style = (
                        current_style.split("background-color: rgba(")[0]
                        + "background-color: rgba("
                        + rgba_part
                        + ", "
                        + str(self._opacity)
                        + ");"
                        + "border: none;"
                        + "background-clip: padding-box;"
                    )
                    self.storage_window.setStyleSheet(original_style)

            # 智能吸附功能：释放时检查是否需要吸附到边缘
            if self._storage_dragging:
                self._smart_snap_to_edge()
            else:
                # 点击事件 - 展开主浮窗
                self._expand_window()
            self._storage_dragging = False
        elif event.button() == Qt.RightButton:
            # 右键点击 - 展开主浮窗（提供额外的交互方式）
            if not self._storage_dragging:
                self._expand_window()

    def mouseDoubleClickEvent(self, event):
        """双击事件 - 快速展开主浮窗"""
        # 检查是否在收纳窗口上双击
        if hasattr(self, "storage_window") and self.storage_window:
            # 获取鼠标位置
            mouse_pos = event.globalPos()
            storage_rect = self.storage_window.geometry()

            # 检查鼠标是否在收纳窗口范围内
            if storage_rect.contains(mouse_pos):
                # 双击收纳窗口，快速展开主浮窗
                self._expand_window()
                event.accept()
                return

        # 调用父类的双击事件处理
        super().mouseDoubleClickEvent(event)

    def _expand_window(self):
        """展开隐藏的窗口（带动画效果）"""
        # 如果收纳浮窗不存在，直接返回
        if not hasattr(self, "storage_window") or not self.storage_window:
            return

        # 保存收纳浮窗的当前位置和尺寸
        storage_window = self.storage_window
        storage_pos = storage_window.pos()
        storage_width = storage_window.width()
        storage_height = storage_window.height()

        # 获取屏幕尺寸
        screen = QApplication.primaryScreen().availableGeometry()

        # 创建收纳浮窗的退出动画
        storage_animation = QPropertyAnimation(storage_window, b"geometry")
        storage_animation.setDuration(200)
        storage_animation.setEasingCurve(QEasingCurve.Type.OutQuad)

        # 设置收纳浮窗动画的起始值和结束值
        storage_animation.setStartValue(storage_window.geometry())

        # 根据收纳浮窗的位置，将其移动到屏幕外
        if storage_pos.x() < screen.width() // 2:
            # 左侧收纳浮窗，向右移出屏幕
            storage_end_rect = QRect(
                screen.width(),
                storage_pos.y(),
                storage_width,
                storage_height,
            )
        else:
            # 右侧收纳浮窗，向左移出屏幕
            storage_end_rect = QRect(
                -storage_width,
                storage_pos.y(),
                storage_width,
                storage_height,
            )
        storage_animation.setEndValue(storage_end_rect)

        # 获取主窗口当前尺寸
        window_width = self.width()
        window_height = self.height()

        # 如果有正在进行的动画，先停止它
        if (
            hasattr(self, "animation")
            and self.animation.state() == QPropertyAnimation.Running
        ):
            self.animation.stop()

        # 定义主窗口的动画完成回调
        def on_main_animation_finished():
            self._retracted = False
            # 将窗口提升到最前面，但不激活窗口
            self.raise_()
            # 设置自动隐藏定时器
            self._auto_hide_timer = QTimer(self)
            self._auto_hide_timer.setSingleShot(True)
            self._auto_hide_timer.timeout.connect(self._auto_hide_window)
            self._auto_hide_timer.start(self.custom_retract_time * 1000)

        # 定义收纳浮窗动画完成后的回调
        def on_storage_animation_finished():
            # 删除收纳浮窗
            self._delete_storage_window()

            # 获取主窗口应该恢复到的位置
            if hasattr(self, "_original_position"):
                # 使用保存的原始位置
                target_x = self._original_position.x()
                target_y = self._original_position.y()
            else:
                # 如果没有保存的原始位置，使用默认位置
                if self.x() < screen.left():
                    # 从左侧展开
                    target_x = screen.left()
                elif self.x() + window_width > screen.right():
                    # 从右侧展开
                    target_x = screen.right() - window_width + 1
                target_y = self.y()

            # 创建主窗口的动画效果
            self.animation = QPropertyAnimation(self, b"geometry")
            self.animation.setDuration(300)
            self.animation.setEasingCurve(
                QEasingCurve.Type.OutCubic
            )  # 使用更自然的缓动曲线

            # 设置主窗口动画的起始值和结束值
            self.animation.setStartValue(self.geometry())
            main_end_rect = QRect(target_x, target_y, window_width, window_height)
            self.animation.setEndValue(main_end_rect)

            # 连接主窗口动画的完成信号
            self.animation.finished.connect(on_main_animation_finished)

            # 启动主窗口动画
            self.animation.start()

        # 连接收纳浮窗动画的完成信号
        storage_animation.finished.connect(on_storage_animation_finished)

        # 启动收纳浮窗动画
        storage_animation.start()

    def _auto_hide_window(self):
        """自动隐藏窗口"""
        # 检查是否启用了边缘贴边隐藏功能
        if self.floating_window_stick_to_edge:
            # 清除自动隐藏定时器
            if hasattr(self, "_auto_hide_timer") and self._auto_hide_timer.isActive():
                self._auto_hide_timer.stop()
            # 调用边缘检测方法隐藏窗口
            self._check_edge_proximity()

    def _save_position(self):
        update_settings("float_position", "x", self.x())
        update_settings("float_position", "y", self.y())
        self.positionChanged.emit(self.x(), self.y())

    def _create_arrow_button(self, direction, x, y):
        """创建箭头按钮用于显示隐藏的窗口"""
        # 如果已存在箭头按钮，先删除
        if hasattr(self, "arrow_button") and self.arrow_button:
            self._delete_arrow_button()

        # 创建透明的可拖动QWidget作为容器
        logger.debug(
            f"创建DraggableWidget箭头按钮，方向: {direction}, 位置: ({x}, {y})"
        )
        self.arrow_widget = DraggableWidget()
        self.arrow_widget.setFixedSize(30, 30)
        self.arrow_widget.move(x, y)
        self.arrow_widget.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
            | Qt.NoFocus
            | Qt.NoDropShadowWindowHint
        )

        # 设置容器透明
        self.arrow_widget.setAttribute(Qt.WA_TranslucentBackground)

        # 创建布局
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 创建箭头按钮
        self.arrow_button = PushButton()
        self.arrow_button.setFixedSize(30, 30)
        self.arrow_button.setFont(QFont(self._font_family, 12))

        # 根据主题设置不同的背景颜色
        dark = is_dark_theme(qconfig)
        opacity = self._opacity

        if dark:
            bg_color = f"rgba(65, 66, 66, {opacity})"
            color = "#ffffff"
        else:
            bg_color = f"rgba(240, 240, 240, {opacity})"
            color = "#000000"

        self.arrow_button.setStyleSheet(
            f"border: none; border-radius: 5px; background-color: {bg_color}; text-align: center; color: {color};"
        )

        # 根据指示器样式设置按钮内容
        if self._stick_indicator_style == 1:  # 文字模式
            self.arrow_button.setText("抽")
        elif self._stick_indicator_style == 2:  # 图标模式
            try:
                icon = get_theme_icon("ic_fluent_people_20_filled")
                self.arrow_button.setIcon(icon)
                self.arrow_button.setIconSize(QSize(20, 20))
            except Exception as e:
                logger.error(f"加载图标失败: {e}")
                # 回退到箭头模式
                if direction == "right":
                    self.arrow_button.setText(">")
                else:
                    self.arrow_button.setText("<")
        else:  # 箭头模式（默认）
            if direction == "right":
                self.arrow_button.setText(">")
            else:
                self.arrow_button.setText("<")

        # 设置按钮点击事件
        self.arrow_button.clicked.connect(lambda: self._show_hidden_window(direction))

        # 为箭头按钮容器添加点击事件处理
        def handle_click():
            if (
                not hasattr(self.arrow_widget, "_was_dragging")
                or not self.arrow_widget._was_dragging
            ) and (
                not hasattr(self.arrow_widget, "_dragging")
                or not self.arrow_widget._dragging
            ):
                self._show_hidden_window(direction)

        # 修改容器的mouseReleaseEvent，处理点击事件
        original_release = self.arrow_widget.mouseReleaseEvent

        def new_mouse_release(event):
            if original_release:
                original_release(event)
            if event.button() == Qt.LeftButton:
                handle_click()

        self.arrow_widget.mouseReleaseEvent = new_mouse_release

        # 将按钮添加到布局中
        layout.addWidget(self.arrow_button, alignment=Qt.AlignCenter)

        # 设置容器的布局
        self.arrow_widget.setLayout(layout)

        # 确保容器显示在最前面
        self.arrow_widget.raise_()
        self.arrow_widget.show()
        logger.debug(f"DraggableWidget箭头按钮已显示，位置: {self.arrow_widget.pos()}")

    def _show_hidden_window(self, direction):
        """显示隐藏的窗口（带动画效果）"""
        # 如果有正在进行的动画，先停止它
        if (
            hasattr(self, "animation")
            and self.animation.state() == QPropertyAnimation.Running
        ):
            self.animation.stop()

        # 获取屏幕尺寸
        screen = QApplication.primaryScreen().availableGeometry()

        # 获取窗口当前位置和尺寸
        window_width = self.width()
        window_height = self.height()

        # 获取箭头按钮容器的当前位置
        if hasattr(self, "arrow_widget") and self.arrow_widget:
            arrow_pos = self.arrow_widget.pos()
            arrow_height = self.arrow_widget.height()
        else:
            # 如果箭头按钮容器不存在，使用窗口的当前位置
            arrow_pos = self.pos()
            arrow_height = 30  # 默认箭头按钮高度

        # 计算窗口应该显示的位置，使窗口中心与箭头按钮中心对齐
        window_y = arrow_pos.y() + (arrow_height // 2) - (window_height // 2)

        # 确保窗口不会超出屏幕顶部和底部
        if window_y < screen.top():
            window_y = screen.top()
        elif window_y + window_height > screen.bottom():
            window_y = screen.bottom() - window_height

        # 创建动画效果
        self.animation = QPropertyAnimation(self, b"geometry")
        # 设置动画持续时间
        self.animation.setDuration(300)
        # 设置缓动曲线
        self.animation.setEasingCurve(QEasingCurve.Type.OutQuad)

        # 设置动画起始值（当前位置）
        self.animation.setStartValue(self.geometry())

        # 设置动画结束值（显示位置）
        if direction == "right":
            # 从左侧显示窗口
            end_rect = QRect(screen.left(), window_y, window_width, window_height)
        else:  # left
            # 从右侧显示窗口
            end_rect = QRect(
                screen.right() - window_width + 1, window_y, window_width, window_height
            )

        self.animation.setEndValue(end_rect)

        # 启动动画
        self.animation.start()

        # 删除箭头按钮
        self._delete_arrow_button()

        # 不保存位置，保持贴边隐藏前的原始位置

        # 将窗口提升到最前面，但不激活窗口
        self.raise_()

        # 根据自定义收回秒数设置延迟后自动隐藏窗口
        retract_time = self.custom_retract_time * 1000  # 转换为毫秒
        QTimer.singleShot(retract_time, self._auto_hide_window)

    def _delete_arrow_button(self):
        """删除箭头按钮"""
        # 删除箭头按钮容器
        if hasattr(self, "arrow_widget") and self.arrow_widget:
            self.arrow_widget.deleteLater()
            self.arrow_widget = None

        # 删除箭头按钮
        if hasattr(self, "arrow_button") and self.arrow_button:
            self.arrow_button.deleteLater()
            self.arrow_button = None

    def _on_setting_changed(self, first, second, value):
        if first == "floating_window_management":
            if second == "startup_display_floating_window":
                if bool(value):
                    self.show()
                else:
                    self.hide()
                self.visibilityChanged.emit(bool(value))
            elif second == "floating_window_opacity":
                self._opacity = float(value or 0.8)
                self.setWindowOpacity(self._opacity)
            elif second == "floating_window_placement":
                self._placement = int(value or 0)
                self.rebuild_ui()
            elif second == "floating_window_display_style":
                self._display_style = int(value or 0)
                self.rebuild_ui()
            elif second == "floating_window_stick_to_edge":
                # 同时更新旧的贴边功能和新的贴边隐藏功能
                self._stick_to_edge = bool(value)
                self.floating_window_stick_to_edge = bool(value)
                # 如果启用了功能，立即检查边缘
                if bool(value):
                    QTimer.singleShot(100, self._check_edge_proximity)
                else:
                    # 如果禁用了功能，删除收纳浮窗并展开窗口
                    self._delete_storage_window()
                    if self._retracted:
                        self._expand_from_edge()
            elif second == "floating_window_stick_to_edge_recover_seconds":
                self._retract_seconds = int(value or 0)
                self.custom_retract_time = int(value or 5)
            elif second == "floating_window_long_press_duration":
                self._long_press_ms = int(value or 500)
            elif second == "floating_window_stick_to_edge_display_style":
                self._stick_indicator_style = int(value or 0)
                self.custom_display_mode = int(value or 1)
            elif second == "floating_window_button_control":
                self._buttons_spec = self._map_button_control(int(value or 0))
                self.rebuild_ui()
            elif second == "floating_window_draggable":
                self._draggable = bool(value)
            # 当任何影响外观的设置改变时，重新应用主题样式
            self._apply_theme_style()
        elif first == "float_position":
            if second == "x":
                x = int(value or 0)
                nx, ny = self._clamp_to_screen(x, self.y())
                self.move(nx, ny)
            elif second == "y":
                y = int(value or 0)
                nx, ny = self._clamp_to_screen(self.x(), y)
                self.move(nx, ny)

    def _on_theme_changed(self):
        """当系统主题变更时调用"""
        self._apply_theme_style()

    def _map_button_control(self, idx):
        combos = [
            ["roll_call"],
            ["quick_draw"],
            ["lottery"],
            ["roll_call", "quick_draw"],
            ["roll_call", "lottery"],
            ["quick_draw", "lottery"],
            ["roll_call", "quick_draw", "lottery"],
        ]
        if idx < 0 or idx >= len(combos):
            return combos[0]
        return combos[idx]


class DraggableWidget(QWidget):
    """可垂直拖动的窗口部件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self._dragging = False
        self._drag_start_y = 0
        self._original_y = 0
        self._fixed_x = 0  # 固定的x坐标
        self._press_start_time = 0  # 记录按下时间
        self._long_press_duration = 100  # 长按时间阈值（毫秒）
        self._long_press_timer = QTimer(self)  # 长按检测计时器
        self._long_press_timer.setSingleShot(True)
        self._long_press_timer.timeout.connect(self._on_long_press)
        self._long_press_triggered = False  # 标记是否触发长按
        self._init_keep_top_timer()  # 初始化保持置顶定时器

    def setFixedX(self, x):
        """设置固定的x坐标"""
        self._fixed_x = x

    def _init_keep_top_timer(self):
        """初始化保持置顶定时器
        优化：减少定时器间隔并提高置顶效率"""
        self.keep_top_timer = QTimer(self)
        self.keep_top_timer.timeout.connect(self._keep_window_on_top)
        self.keep_top_timer.start(100)

    def _keep_window_on_top(self):
        """保持窗口置顶
        优化：简化置顶逻辑，提高效率"""
        try:
            self.raise_()  # 将窗口提升到最前面
        except Exception as e:
            logger.error(f"保持窗口置顶失败: {e}")

    def closeEvent(self, event):
        """窗口关闭事件 - 清理所有定时器资源"""
        # 停止保持置顶定时器
        if hasattr(self, "keep_top_timer") and self.keep_top_timer:
            if self.keep_top_timer.isActive():
                self.keep_top_timer.stop()
            self.keep_top_timer.deleteLater()
            self.keep_top_timer = None
            logger.info("DraggableWidget置顶定时器已停止并清理")

        # 停止长按检测计时器
        if hasattr(self, "_long_press_timer") and self._long_press_timer:
            if self._long_press_timer.isActive():
                self._long_press_timer.stop()
            self._long_press_timer.deleteLater()
            self._long_press_timer = None
            logger.info("DraggableWidget长按计时器已停止并清理")

        # 调用父类的closeEvent
        super().closeEvent(event)

    def _on_long_press(self):
        """长按触发事件"""
        self._long_press_triggered = True
        self.setCursor(Qt.ClosedHandCursor)

    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.LeftButton:
            self._press_start_time = QDateTime.currentMSecsSinceEpoch()
            self._drag_start_y = event.globalY()
            self._original_y = self.y()
            self._long_press_triggered = False
            # 重置拖动标志
            self._was_dragging = False
            # 启动长按检测计时器
            self._long_press_timer.start(self._long_press_duration)

    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        if event.buttons() & Qt.LeftButton:  # 确保左键按下
            current_time = QDateTime.currentMSecsSinceEpoch()
            # 检查是否已经长按或者移动距离足够大
            if self._long_press_triggered or (
                current_time - self._press_start_time > 100
                and abs(event.globalY() - self._drag_start_y) > 5
            ):
                if not self._dragging:
                    self._dragging = True
                    # 设置拖动标志，表示发生了拖动操作
                    self._was_dragging = True
                    self.setCursor(Qt.ClosedHandCursor)
                    # 如果还没触发长按，停止计时器
                    if not self._long_press_triggered:
                        self._long_press_timer.stop()

                # 计算新的y坐标
                new_y = self._original_y + (event.globalY() - self._drag_start_y)
                # 保持x坐标不变
                self.move(self._fixed_x, new_y)

                # 同时更新主窗口的位置
                if (
                    hasattr(self, "parent")
                    and self.parent()
                    and hasattr(self.parent(), "move")
                ):
                    # 获取主窗口的当前位置
                    parent_x = self.parent().x()
                    parent_y = self.parent().y()
                    # 更新主窗口的y坐标，保持x坐标不变
                    self.parent().move(parent_x, new_y)

    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if event.button() == Qt.LeftButton:
            # 先保存拖动状态，然后再重置
            was_dragging = self._dragging
            self._dragging = False
            self._long_press_timer.stop()  # 停止长按计时器
            self.setCursor(Qt.ArrowCursor)

            # 如果没有触发长按且移动距离很小，则视为点击
            if (
                not self._long_press_triggered
                and abs(event.globalY() - self._drag_start_y) < 5
                and not was_dragging
            ):
                pass

    def enterEvent(self, event):
        """鼠标进入窗口区域时的事件处理，不再自动展开贴边隐藏的窗口"""
        # 调用父类的enterEvent
        super().enterEvent(event)

    def leaveEvent(self, event):
        """鼠标离开窗口区域时的事件处理，不再自动贴边隐藏窗口"""
        # 调用父类的leaveEvent
        super().leaveEvent(event)
