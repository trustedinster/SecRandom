# ==================================================
# 导入库
# ==================================================
import random
import colorsys
import weakref

from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QMenu, QApplication
from PySide6.QtGui import QMouseEvent, QPalette
from PySide6.QtCore import Qt, QPoint, QTimer, QEvent
from qfluentwidgets import BodyLabel, AvatarWidget, qconfig, Theme

from app.tools.variable import (
    STUDENT_ID_FORMAT,
    NAME_SPACING,
    SUPPORTED_IMAGE_EXTENSIONS,
    AVATAR_LABEL_SPACING,
    DEFAULT_MIN_SATURATION,
    DEFAULT_MAX_SATURATION,
    DEFAULT_MIN_VALUE,
    DEFAULT_MAX_VALUE,
    LIGHT_VALUE_MULTIPLIER,
    LIGHT_MAX_VALUE_MULTIPLIER,
    DARK_VALUE_MULTIPLIER,
    DARK_MAX_VALUE_MULTIPLIER,
    LIGHT_THEME_MAX_VALUE,
    LIGHT_THEME_ADJUSTED_MAX_VALUE,
    DARK_THEME_MIN_VALUE,
    DARK_THEME_MAX_VALUE,
    LIGHTNESS_THRESHOLD,
    RGB_COLOR_FORMAT,
    GRID_ITEM_MARGIN,
    GRID_ITEM_SPACING,
    DEFAULT_AVAILABLE_WIDTH,
)
from app.tools.path_utils import file_exists, get_data_path
from app.tools.personalised import is_dark_theme
from app.tools.settings_access import readme_settings_async
from app.common.data.list import get_group_members

from random import SystemRandom

system_random = SystemRandom()

# 移除了循环导入，将导入移到函数内部使用


# ==================================================
# 触屏结果显示组件
# ==================================================
class TouchResultWidget(QWidget):
    """支持触屏操作的结果显示组件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # 触屏相关变量
        self.is_pressing = False
        self.press_pos = QPoint()
        self.long_press_timer = QTimer(self)
        self.long_press_timer.setSingleShot(True)
        self.long_press_delay = 500  # 长按延迟时间(毫秒)
        self.long_press_timer.timeout.connect(self.handle_long_press)
        self.context_menu_requested = False

        # 滑动相关变量
        self.is_sliding = False
        self.last_pos = QPoint()

        # 内存优化：使用弱引用避免循环引用
        self._cached_mouse_events = []
        self._max_cached_events = 10

    def mousePressEvent(self, event):
        """处理鼠标按下事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_pressing = True
            self.press_pos = event.pos()
            self.last_pos = event.pos()
            self.long_press_timer.start(self.long_press_delay)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """处理鼠标移动事件"""
        if self.is_pressing:
            # 计算移动距离
            delta = event.pos() - self.press_pos
            if abs(delta.x()) > 5 or abs(delta.y()) > 5:
                # 移动距离超过阈值，取消长按
                self.long_press_timer.stop()
                self.is_sliding = True

                # 实现滑动效果
                parent = self.parent()
                while parent:
                    if hasattr(parent, "verticalScrollBar") or hasattr(
                        parent, "horizontalScrollBar"
                    ):
                        # 找到滚动区域，实现滑动
                        if hasattr(parent, "verticalScrollBar"):
                            vbar = parent.verticalScrollBar()
                            vbar.setValue(vbar.value() - delta.y())
                        if hasattr(parent, "horizontalScrollBar"):
                            hbar = parent.horizontalScrollBar()
                            hbar.setValue(hbar.value() - delta.x())
                        self.last_pos = event.pos()
                        break
                    parent = parent.parent()

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """处理鼠标释放事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_pressing = False
            self.is_sliding = False
            self.long_press_timer.stop()

            # 内存优化：清理缓存的事件对象
            if len(self._cached_mouse_events) > self._max_cached_events // 2:
                self._cached_mouse_events.clear()
        super().mouseReleaseEvent(event)

    def handle_long_press(self):
        """处理长按事件"""
        if self.is_pressing and not self.is_sliding:
            # 模拟右键点击，显示上下文菜单
            self.context_menu_requested = True
            # 创建并显示上下文菜单
            menu = QMenu(self)
            # 可以添加自定义菜单项
            menu.exec(self.mapToGlobal(self.press_pos))
            self.context_menu_requested = False

    def touchEvent(self, event):
        """处理触屏事件"""
        touch_points = event.touchPoints()
        if not touch_points:
            return

        touch_point = touch_points[0]
        touch_pos = touch_point.pos().toPoint()

        # 内存优化：复用鼠标事件对象
        if touch_point.state() == Qt.TouchPointState.Pressed:
            # 触屏按下
            mouse_event = self._get_cached_mouse_event(
                QEvent.Type.MouseButtonPress, touch_pos, Qt.MouseButton.LeftButton
            )
            self.mousePressEvent(mouse_event)
        elif touch_point.state() == Qt.TouchPointState.Moved:
            # 触屏移动
            mouse_event = self._get_cached_mouse_event(
                QEvent.Type.MouseMove, touch_pos, Qt.MouseButton.LeftButton
            )
            self.mouseMoveEvent(mouse_event)
        elif touch_point.state() == Qt.TouchPointState.Released:
            # 触屏释放
            mouse_event = self._get_cached_mouse_event(
                QEvent.Type.MouseButtonRelease, touch_pos, Qt.MouseButton.LeftButton
            )
            self.mouseReleaseEvent(mouse_event)

    def _get_cached_mouse_event(self, event_type, pos, button):
        """获取缓存的鼠标事件对象，减少内存分配"""
        # 清理过期的事件缓存
        self._cached_mouse_events = [
            event for event in self._cached_mouse_events if event is not None
        ]

        if len(self._cached_mouse_events) < self._max_cached_events:
            event = QMouseEvent(
                event_type,
                pos,
                button,
                button
                if event_type != QEvent.Type.MouseButtonRelease
                else Qt.MouseButton.NoButton,
                Qt.KeyboardModifier.NoModifier,
            )
            self._cached_mouse_events.append(event)
            return event
        else:
            # 如果缓存已满，创建新事件并替换最旧的
            return QMouseEvent(
                event_type,
                pos,
                button,
                button
                if event_type != QEvent.Type.MouseButtonRelease
                else Qt.MouseButton.NoButton,
                Qt.KeyboardModifier.NoModifier,
            )


# ==================================================
# 结果显示工具类
# ==================================================
class ResultDisplayUtils:
    """结果显示工具类，提供通用的结果显示功能"""

    _color_cache = {}
    _max_cache_size = 100  # 限制颜色缓存大小
    _weak_widget_refs = weakref.WeakSet()  # 使用弱引用跟踪widget

    @staticmethod
    def _clear_color_cache():
        """清除颜色缓存"""
        ResultDisplayUtils._color_cache.clear()

    @staticmethod
    def _init_theme_listener():
        """初始化主题变化监听器"""
        if not hasattr(ResultDisplayUtils, "_theme_listener_initialized"):
            qconfig.themeChanged.connect(ResultDisplayUtils._clear_color_cache)
            ResultDisplayUtils._theme_listener_initialized = True

    @staticmethod
    def _create_avatar_widget(image_path, name, font_size):
        """
        创建头像组件

        参数:
            image_path: 图片路径
            name: 学生姓名
            font_size: 字体大小

        返回:
            AvatarWidget: 创建的头像组件
        """
        if image_path is not None:
            avatar = AvatarWidget(image_path)
        else:
            avatar = AvatarWidget()
            avatar.setText(name)

        return avatar

    @staticmethod
    def _format_student_text(
        class_name,
        display_format,
        student_id_str,
        name,
        draw_count,
        is_group_mode=False,
        show_random=0,
    ):
        """
        格式化学生显示文本

        参数:
            display_format: 显示格式 (0:学号+姓名, 1:仅姓名, 2:仅学号)
            student_id_str: 学号字符串
            name: 学生姓名或小组名称
            draw_count: 抽取人数
            is_group_mode: 是否为小组模式
            show_random: 随机组员显示格式 (0:不显示, 1:组名[换行]姓名, 2:组名[短横杠]姓名)

        返回:
            str: 格式化后的文本
        """
        # 小组模式下，根据show_random设置显示格式
        if is_group_mode:
            # 获取小组成员列表
            group_members = get_group_members(class_name, name)

            if show_random == 1:  # 组名[换行]随机选择的成员
                if group_members:
                    # 随机选择一个成员
                    selected_member = system_random.choice(group_members)
                    selected_name = selected_member["name"]
                    return f"{name}\n{selected_name}"
                else:
                    return name
            elif show_random == 2:  # 组名[短横杠]随机选择的成员
                if group_members:
                    # 随机选择一个成员
                    selected_member = system_random.choice(group_members)
                    selected_name = selected_member["name"]
                    return f"{name} - {selected_name}"
                else:
                    return name
            else:  # 不显示特殊格式 - 只显示组名
                return f"{name}"

        if display_format == 1:  # 仅显示姓名
            return f"{name}"
        elif display_format == 2:  # 仅显示学号
            return f"{student_id_str}"
        else:  # 显示学号+姓名
            if draw_count == 1:
                return f"{student_id_str}\n{name}"
            else:
                return f"{student_id_str} {name}"

    @staticmethod
    def _create_student_label_with_avatar(
        image_path, name, font_size, draw_count, text
    ):
        """
        创建带头像的学生标签

        参数:
            image_path: 图片路径
            name: 学生姓名
            font_size: 字体大小
            draw_count: 抽取人数
            text: 显示文本

        返回:
            QWidget: 包含头像和文本的容器组件
        """
        # 内存优化：使用更轻量的布局策略
        container = QWidget()
        container.setAttribute(Qt.WA_DeleteOnClose)  # 自动清理

        # 创建水平布局
        h_layout = QHBoxLayout(container)
        h_layout.setSpacing(AVATAR_LABEL_SPACING)
        h_layout.setContentsMargins(0, 0, 0, 0)

        # 创建头像
        avatar = ResultDisplayUtils._create_avatar_widget(image_path, name, font_size)
        avatar.setRadius(font_size * 2 if draw_count == 1 else font_size // 2)

        # 创建文本标签
        text_label = BodyLabel(text)

        # 添加到布局
        h_layout.addWidget(avatar)
        h_layout.addWidget(text_label)

        # 内存优化：跟踪创建的widget以便清理
        ResultDisplayUtils._weak_widget_refs.add(container)

        return container

    @staticmethod
    def _apply_label_style(
        label, font_size, animation_color, settings_group="roll_call_settings"
    ):
        """
        应用标签样式

        参数:
            label: 标签组件
            font_size: 字体大小
            animation_color: 动画颜色模式
            settings_group: 设置组名称，默认为roll_call_settings
        """
        fixed_color = readme_settings_async(settings_group, "animation_fixed_color")
        if (
            isinstance(label, QWidget)
            and hasattr(label, "layout")
            and label.layout() is not None
        ):
            layout = label.layout()
            if layout:
                for i in range(layout.count()):
                    item = layout.itemAt(i)
                    widget = item.widget()
                    if isinstance(widget, BodyLabel):
                        widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
                        style_sheet = f"font-size: {font_size}pt; "

                        if animation_color == 1:
                            style_sheet += f"color: {ResultDisplayUtils._generate_vibrant_color()} !important;"
                        elif animation_color == 2:
                            style_sheet += f"color: {fixed_color} !important;"
                        else:
                            try:
                                from qfluentwidgets import qconfig

                                default_color = (
                                    "#ffffff" if is_dark_theme(qconfig) else "#000000"
                                )
                                style_sheet += f"color: {default_color} !important;"
                            except Exception:
                                # 兜底使用黑色
                                style_sheet += "color: #000000 !important;"

                        widget.setStyleSheet(style_sheet)
        else:
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            style_sheet = f"font-size: {font_size}pt; "
            fixed_color = readme_settings_async(settings_group, "animation_fixed_color")
            if animation_color == 1:
                style_sheet += (
                    f"color: {ResultDisplayUtils._generate_vibrant_color()} !important;"
                )
            elif animation_color == 2:
                style_sheet += f"color: {fixed_color} !important;"
            else:
                try:
                    from qfluentwidgets import qconfig

                    default_color = "#ffffff" if is_dark_theme(qconfig) else "#000000"
                    style_sheet += f"color: {default_color} !important;"
                except Exception:
                    style_sheet += "color: #000000 !important;"

            label.setStyleSheet(style_sheet)

    @staticmethod
    def create_student_label(
        class_name,
        selected_students,
        draw_count=1,
        font_size=50,
        animation_color=0,
        display_format=0,
        show_student_image=False,
        group_index=0,
        show_random=0,
        settings_group="roll_call_settings",
    ):
        """
        创建学生显示标签

        参数:
            selected_students: 选中的学生列表 [(num, selected, exist), ...]
            draw_count: 抽取人数
            font_size: 字体大小
            animation_color: 动画颜色模式 (0:默认, 1:随机颜色, 2:固定颜色)
            display_format: 显示格式 (0:学号+姓名, 1:仅姓名, 2:仅学号)
            show_student_image: 是否显示学生头像
            group_index: 小组索引 (0:全班, 1:随机小组, >1:指定小组)
            show_random: 随机组员显示格式 (0:不显示, 1:组名[换行]姓名, 2:组名[短横杠]姓名)
            settings_group: 设置组名称，默认为roll_call_settings

        返回:
            list: 创建的标签列表
        """
        student_labels = []

        # 内存优化：预分配列表容量
        student_labels = [None] * len(selected_students)

        for i, (num, selected, exist) in enumerate(selected_students):
            current_image_path = None
            # 在小组模式下，尝试使用小组名称作为图片文件名
            if show_student_image:
                image_name = str(selected)
                # 内存优化：使用生成器表达式减少内存分配
                for ext in (
                    ext
                    for ext in SUPPORTED_IMAGE_EXTENSIONS
                    if file_exists(
                        get_data_path("images", f"students/{image_name}{ext}")
                    )
                ):
                    current_image_path = str(
                        get_data_path("images", f"students/{image_name}{ext}")
                    )
                    break

            # 处理学号格式化
            student_id_str = (
                STUDENT_ID_FORMAT.format(num=num) if num is not None else ""
            )

            # 处理不同模式下的名称显示
            name = (
                f"{str(selected)[0]}{NAME_SPACING}{str(selected)[1]}"
                if len(str(selected)) == 2 and group_index == 0
                else str(selected)
            )

            text = ResultDisplayUtils._format_student_text(
                class_name,
                display_format,
                student_id_str,
                name,
                draw_count,
                is_group_mode=(group_index == 1),
                show_random=show_random,
            )

            # 使用支持触屏的容器包装所有内容，确保整个区域都能响应触屏操作
            touch_container = TouchResultWidget()
            touch_container.setAttribute(Qt.WA_DeleteOnClose)  # 自动清理

            # 内存优化：使用更轻量的布局策略
            inner_layout = QVBoxLayout() if draw_count == 1 else QHBoxLayout()
            inner_layout.setContentsMargins(0, 0, 0, 0)
            inner_layout.setSpacing(0)
            touch_container.setLayout(inner_layout)

            # 在小组模式下，只在没有成员显示时才显示头像
            if show_student_image:
                label = ResultDisplayUtils._create_student_label_with_avatar(
                    current_image_path, name, font_size, draw_count, text
                )
            else:
                label = BodyLabel(text)
                label.setAttribute(Qt.WA_DeleteOnClose)  # 自动清理

            ResultDisplayUtils._apply_label_style(
                label, font_size, animation_color, settings_group
            )

            # 将标签添加到触屏容器中
            inner_layout.addWidget(label)
            student_labels[i] = touch_container

        return student_labels

    @staticmethod
    def _generate_vibrant_color(
        min_saturation=DEFAULT_MIN_SATURATION,
        max_saturation=DEFAULT_MAX_SATURATION,
        min_value=DEFAULT_MIN_VALUE,
        max_value=DEFAULT_MAX_VALUE,
        use_cache=True,
    ):
        """生成鲜艳直观的颜色

        根据当前主题自动调整颜色明亮程度：
        - 浅色主题：降低亮度范围，避免颜色过于明亮导致看不清
        - 深色主题：使用正常亮度范围，确保颜色在深色背景上清晰可见

        参数:
            min_saturation: 最小饱和度 (默认DEFAULT_MIN_SATURATION)
            max_saturation: 最大饱和度 (默认DEFAULT_MAX_SATURATION)
            min_value: 最小亮度值 (默认DEFAULT_MIN_VALUE)
            max_value: 最大亮度值 (默认DEFAULT_MAX_VALUE)
            use_cache: 是否使用颜色缓存 (默认True)

        返回:
            str: RGB格式的颜色字符串，如"rgb(255,100,50)"
        """
        ResultDisplayUtils._init_theme_listener()

        # 内存优化：限制缓存大小，防止无限增长
        if (
            use_cache
            and len(ResultDisplayUtils._color_cache)
            >= ResultDisplayUtils._max_cache_size
        ):
            # 清除最旧的50%缓存项
            keys_to_remove = list(ResultDisplayUtils._color_cache.keys())[
                : ResultDisplayUtils._max_cache_size // 2
            ]
            for key in keys_to_remove:
                ResultDisplayUtils._color_cache.pop(key, None)

        if qconfig.theme == Theme.LIGHT:  # 浅色主题
            adjusted_min_value = min(
                min_value * LIGHT_VALUE_MULTIPLIER, LIGHT_THEME_MAX_VALUE
            )
            adjusted_max_value = min(
                max_value * LIGHT_MAX_VALUE_MULTIPLIER, LIGHT_THEME_ADJUSTED_MAX_VALUE
            )
        elif qconfig.theme == Theme.AUTO:  # 自动主题
            lightness = QApplication.palette().color(QPalette.Window).lightness()
            if lightness > LIGHTNESS_THRESHOLD:  # 浅色主题
                adjusted_min_value = min(
                    min_value * LIGHT_VALUE_MULTIPLIER, LIGHT_THEME_MAX_VALUE
                )
                adjusted_max_value = min(
                    max_value * LIGHT_MAX_VALUE_MULTIPLIER,
                    LIGHT_THEME_ADJUSTED_MAX_VALUE,
                )
            else:  # 深色主题
                adjusted_min_value = min(
                    min_value * DARK_VALUE_MULTIPLIER, DARK_THEME_MIN_VALUE
                )
                adjusted_max_value = max(
                    max_value * DARK_MAX_VALUE_MULTIPLIER, DARK_THEME_MAX_VALUE
                )
        else:  # 深色主题或其他主题
            adjusted_min_value = min(
                min_value * DARK_VALUE_MULTIPLIER, DARK_THEME_MIN_VALUE
            )
            adjusted_max_value = max(
                max_value * DARK_MAX_VALUE_MULTIPLIER, DARK_THEME_MAX_VALUE
            )
        h = random.random()
        s = random.uniform(min_saturation, max_saturation)
        v = random.uniform(adjusted_min_value, adjusted_max_value)
        r, g, b = (int(c * 255) for c in colorsys.hsv_to_rgb(h, s, v))
        color_str = RGB_COLOR_FORMAT.format(r=r, g=g, b=b)

        # 内存优化：只在启用缓存时存储颜色
        if use_cache:
            ResultDisplayUtils._color_cache[color_str] = True

        return color_str

    @staticmethod
    def display_results_in_grid(result_grid, student_labels, alignment=None):
        """
        在网格布局中显示结果

        参数:
            result_grid: QGridLayout 网格布局
            student_labels: 学生标签列表
            alignment: 对齐方式 (默认为居中)
        """
        if alignment is None:
            alignment = Qt.AlignmentFlag.AlignCenter
        result_grid.setAlignment(alignment)

        # 清除现有的所有控件
        ResultDisplayUtils.clear_grid(result_grid)

        if not student_labels:
            return

        # 内存优化：使用生成器表达式减少内存分配
        label_count = len(student_labels)

        # 计算网格布局参数
        parent_widget = result_grid.parentWidget()
        available_width = (
            (parent_widget.width() - GRID_ITEM_MARGIN)
            if parent_widget
            else DEFAULT_AVAILABLE_WIDTH
        )

        # 内存优化：避免创建大型临时列表
        total_width = 0
        for label in student_labels:
            total_width += label.sizeHint().width()
        total_width += label_count * GRID_ITEM_SPACING

        if total_width > available_width and label_count > 0:
            avg_label_width = total_width / label_count
            max_columns = max(1, int(available_width // avg_label_width))
        else:
            max_columns = label_count if label_count > 0 else 1

        # 内存优化：使用迭代器而非枚举，减少内存占用
        for i in range(label_count):
            row = i // max_columns
            col = i % max_columns
            result_grid.addWidget(student_labels[i], row, col)

        # 确保父级滚动区域能够正确计算内容大小
        if parent_widget:
            parent_widget.updateGeometry()

    @staticmethod
    def clear_grid(result_grid):
        """
        清空网格布局中的所有小部件

        参数:
            result_grid: QGridLayout 网格布局
        """
        # 内存优化：批量处理减少循环开销
        count = result_grid.count()
        if count == 0:
            return

        # 批量移除和清理widget
        items_to_delete = []
        for i in range(count):
            item = result_grid.takeAt(0)
            if item and item.widget():
                widget = item.widget()
                widget.hide()  # 先隐藏
                widget.deleteLater()  # 异步删除
                items_to_delete.append(item)

        # 内存优化：只在有组件被删除时记录日志
        if count > 0:
            from loguru import logger

            logger.debug(f"本次销毁了{count}个组件")

        # 清理缓存引用
        ResultDisplayUtils._color_cache.clear()

        # 强制进行垃圾回收（可选，根据内存压力决定）
        # import gc
        # gc.collect()

    @staticmethod
    def show_notification_if_enabled(
        class_name, selected_students, draw_count=1, settings=None, settings_group=None
    ):
        """
        如果启用了通知服务，则显示抽取结果通知

        参数:
            class_name: 班级名称
            selected_students: 选中的学生列表
            draw_count: 抽取人数
            settings: 通知设置参数
        """
        # 检查是否启用了通知服务（这个检查应该由调用方完成）
        from app.common.notification.notification_service import (
            show_roll_call_notification,
        )

        show_roll_call_notification(
            class_name, selected_students, draw_count, settings, settings_group
        )

    @staticmethod
    def cleanup_memory():
        """
        清理内存占用，释放不再使用的资源
        建议在大量操作后调用此方法来释放内存
        """
        # 清理颜色缓存
        ResultDisplayUtils._color_cache.clear()

        # 清理弱引用集合
        ResultDisplayUtils._weak_widget_refs.clear()

        # 可选：强制垃圾回收
        # import gc
        # gc.collect()

        from loguru import logger

        logger.debug("ResultDisplayUtils内存清理完成")
