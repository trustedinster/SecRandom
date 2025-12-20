# ==================================================
# 导入库
# ==================================================
import os

from loguru import logger
from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtNetwork import *
from qfluentwidgets import *

from app.tools.variable import *
from app.tools.path_utils import *
from app.tools.personalised import *
from app.tools.settings_default import *
from app.tools.settings_access import *
from app.tools.settings_access import get_safe_font_size
from app.Language.obtain_language import *
from app.common.data.list import *


# ==================================================
# 点名设置
# ==================================================
class roll_call_settings(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # 创建垂直布局
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setSpacing(10)

        # 添加抽取功能设置组件
        self.extraction_function_widget = roll_call_extraction_function(self)
        self.vBoxLayout.addWidget(self.extraction_function_widget)

        # 添加显示设置组件
        self.display_settings_widget = roll_call_display_settings(self)
        self.vBoxLayout.addWidget(self.display_settings_widget)

        # 添加动画设置组件
        self.animation_settings_widget = roll_call_animation_settings(self)
        self.vBoxLayout.addWidget(self.animation_settings_widget)


class roll_call_extraction_function(GroupHeaderCardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle(
            get_content_name_async("roll_call_settings", "extraction_function")
        )
        self.setBorderRadius(8)

        # 抽取模式下拉框
        self.draw_mode_combo = ComboBox()
        self.draw_mode_combo.addItems(
            get_content_combo_name_async("roll_call_settings", "draw_mode")
        )
        self.draw_mode_combo.setCurrentIndex(
            readme_settings_async("roll_call_settings", "draw_mode")
        )
        self.draw_mode_combo.currentIndexChanged.connect(self.on_draw_mode_changed)

        # 清除抽取记录方式下拉框
        self.clear_record_combo = ComboBox()
        self.clear_record_combo.addItems(
            get_content_combo_name_async("roll_call_settings", "clear_record")
        )
        self.clear_record_combo.setCurrentIndex(
            readme_settings_async("roll_call_settings", "clear_record")
        )
        self.clear_record_combo.currentIndexChanged.connect(
            lambda: update_settings(
                "roll_call_settings",
                "clear_record",
                self.clear_record_combo.currentIndex(),
            )
        )

        # 半重复抽取次数输入框
        self.half_repeat_spin = SpinBox()
        self.half_repeat_spin.setFixedWidth(WIDTH_SPINBOX)
        self.half_repeat_spin.setMinimum(0)
        self.half_repeat_spin.setSuffix("次")
        self.half_repeat_spin.setValue(
            readme_settings_async("roll_call_settings", "half_repeat")
        )
        self.half_repeat_spin.valueChanged.connect(
            lambda: update_settings(
                "roll_call_settings", "half_repeat", self.half_repeat_spin.value()
            )
        )

        # 抽取方式下拉框
        self.draw_type_combo = ComboBox()
        self.draw_type_combo.addItems(
            get_content_combo_name_async("roll_call_settings", "draw_type")
        )
        self.draw_type_combo.setCurrentIndex(
            readme_settings_async("roll_call_settings", "draw_type")
        )
        self.draw_type_combo.currentIndexChanged.connect(
            lambda: update_settings(
                "roll_call_settings", "draw_type", self.draw_type_combo.currentIndex()
            )
        )

        # 默认抽取名单下拉框
        self.default_class_combo = ComboBox()
        # 初始化班级列表（在所有组件都创建后）
        self.refresh_class_list()
        if not get_class_name_list():
            self.default_class_combo.setCurrentIndex(-1)
            self.default_class_combo.setPlaceholderText(
                get_content_name_async("roll_call_settings", "default_class")
            )
        else:
            self.default_class_combo.setCurrentText(
                readme_settings_async("roll_call_settings", "default_class")
            )
        self.default_class_combo.currentIndexChanged.connect(
            lambda: update_settings(
                "roll_call_settings",
                "default_class",
                self.default_class_combo.currentText(),
            )
        )

        # 添加设置项到分组
        self.addGroup(
            get_theme_icon("ic_fluent_document_bullet_list_cube_20_filled"),
            get_content_name_async("roll_call_settings", "draw_mode"),
            get_content_description_async("roll_call_settings", "draw_mode"),
            self.draw_mode_combo,
        )
        self.addGroup(
            get_theme_icon("ic_fluent_text_clear_formatting_20_filled"),
            get_content_name_async("roll_call_settings", "clear_record"),
            get_content_description_async("roll_call_settings", "clear_record"),
            self.clear_record_combo,
        )
        self.addGroup(
            get_theme_icon("ic_fluent_clipboard_bullet_list_20_filled"),
            get_content_name_async("roll_call_settings", "half_repeat"),
            get_content_description_async("roll_call_settings", "half_repeat"),
            self.half_repeat_spin,
        )
        self.addGroup(
            get_theme_icon("ic_fluent_drawer_add_20_filled"),
            get_content_name_async("roll_call_settings", "draw_type"),
            get_content_description_async("roll_call_settings", "draw_type"),
            self.draw_type_combo,
        )
        self.addGroup(
            get_theme_icon("ic_fluent_class_20_filled"),
            get_content_name_async("roll_call_settings", "default_class"),
            get_content_description_async("roll_call_settings", "default_class"),
            self.default_class_combo,
        )

        # 设置文件系统监视器，监控班级名单文件夹的变化
        self.setup_file_watcher()

        # 初始化时调用一次，确保界面状态与设置一致
        self.on_draw_mode_changed()

    def setup_file_watcher(self):
        """设置文件系统监视器，监控班级名单文件夹的变化"""
        # 获取班级名单文件夹路径
        roll_call_list_dir = get_data_path("list", "roll_call_list")

        # 确保目录存在
        if not roll_call_list_dir.exists():
            roll_call_list_dir.mkdir(parents=True, exist_ok=True)

        # 创建文件系统监视器
        self.file_watcher = QFileSystemWatcher()

        # 监视目录
        self.file_watcher.addPath(str(roll_call_list_dir))

        # 连接信号
        self.file_watcher.directoryChanged.connect(self.on_directory_changed)

    def on_directory_changed(self, path):
        """当目录内容发生变化时调用此方法"""
        # 延迟刷新，避免文件操作未完成
        QTimer.singleShot(500, self.refresh_class_list)

    def refresh_class_list(self):
        """刷新班级下拉框列表"""
        # 从设置文件中读取默认班级
        default_class = readme_settings_async("roll_call_settings", "default_class")

        # 获取最新的班级列表
        class_list = get_class_name_list()

        # 清空并重新添加班级列表
        self.default_class_combo.clear()
        self.default_class_combo.addItems(class_list)

        # 尝试恢复设置文件中的默认班级
        if default_class:
            self.default_class_combo.setCurrentText(default_class)
        elif not class_list:
            self.default_class_combo.setCurrentIndex(-1)
            self.default_class_combo.setPlaceholderText(
                get_content_name_async("roll_call_settings", "default_class")
            )

    def on_draw_mode_changed(self):
        """当抽取模式改变时的处理逻辑"""
        # 更新设置值
        update_settings(
            "roll_call_settings", "draw_mode", self.draw_mode_combo.currentIndex()
        )

        # 获取当前抽取模式索引
        draw_mode_index = self.draw_mode_combo.currentIndex()

        # 根据抽取模式设置不同的控制逻辑
        if draw_mode_index == 0:  # 重复抽取模式
            # 禁用清除抽取记录方式下拉框
            self.clear_record_combo.setEnabled(False)
            # 清空当前选项
            self.clear_record_combo.clear()
            self.clear_record_combo.addItems(
                get_any_position_value_async(
                    "roll_call_settings", "clear_record", "combo_items_other"
                )
            )
            # 强制设置为"无需清除"（索引2）
            self.clear_record_combo.setCurrentIndex(2)
            # 更新设置
            update_settings("roll_call_settings", "clear_record", 2)

            # 设置half_repeat_spin为0并禁用
            self.half_repeat_spin.setEnabled(False)
            self.half_repeat_spin.setRange(0, 0)
            self.half_repeat_spin.setValue(0)
            # 更新设置
            update_settings("roll_call_settings", "half_repeat", 0)

        else:  # 不重复抽取模式或半重复抽取模式
            # 启用清除抽取记录方式下拉框
            self.clear_record_combo.setEnabled(True)

            # 清空当前选项
            self.clear_record_combo.clear()

            # 添加前两个选项（不包含"无需清除"）
            self.clear_record_combo.addItems(
                get_content_combo_name_async("roll_call_settings", "clear_record")
            )

            # 设置默认选择第一个选项
            self.clear_record_combo.setCurrentIndex(0)
            # 更新设置
            update_settings("roll_call_settings", "clear_record", 0)

            # 根据具体模式设置half_repeat_spin
            if draw_mode_index == 1:  # 不重复抽取模式
                # 设置half_repeat_spin为1并禁用
                self.half_repeat_spin.setEnabled(False)
                self.half_repeat_spin.setRange(1, 1)
                self.half_repeat_spin.setValue(1)
                # 更新设置
                update_settings("roll_call_settings", "half_repeat", 1)
            else:  # 半重复抽取模式（索引2）
                # 设置half_repeat_spin为2-100范围并启用
                self.half_repeat_spin.setEnabled(True)
                self.half_repeat_spin.setRange(2, 100)
                # 如果当前值小于2，则设置为2
                if self.half_repeat_spin.value() < 2:
                    self.half_repeat_spin.setValue(2)
                    # 更新设置
                    update_settings("roll_call_settings", "half_repeat", 2)


class roll_call_display_settings(GroupHeaderCardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle(get_content_name_async("roll_call_settings", "display_settings"))
        self.setBorderRadius(8)

        # 字体大小输入框
        self.font_size_spin = SpinBox()
        self.font_size_spin.setFixedWidth(WIDTH_SPINBOX)
        self.font_size_spin.setRange(10, 1000)
        self.font_size_spin.setSuffix("px")
        self.font_size_spin.setValue(
            get_safe_font_size("roll_call_settings", "font_size")
        )
        self.font_size_spin.valueChanged.connect(
            lambda: update_settings(
                "roll_call_settings", "font_size", self.font_size_spin.value()
            )
        )

        # 结果显示格式下拉框
        self.display_format_combo = ComboBox()
        self.display_format_combo.addItems(
            get_content_combo_name_async("roll_call_settings", "display_format")
        )
        self.display_format_combo.setCurrentIndex(
            readme_settings_async("roll_call_settings", "display_format")
        )
        self.display_format_combo.currentIndexChanged.connect(
            lambda: update_settings(
                "roll_call_settings",
                "display_format",
                self.display_format_combo.currentIndex(),
            )
        )

        # 显示随机组员格式下拉框
        self.show_random_format_combo = ComboBox()
        self.show_random_format_combo.addItems(
            get_content_combo_name_async("roll_call_settings", "show_random")
        )
        self.show_random_format_combo.setCurrentIndex(
            readme_settings_async("roll_call_settings", "show_random")
        )
        self.show_random_format_combo.currentIndexChanged.connect(
            lambda: update_settings(
                "roll_call_settings",
                "show_random",
                self.show_random_format_combo.currentIndex(),
            )
        )

        # 添加设置项到分组
        self.addGroup(
            get_theme_icon("ic_fluent_text_font_20_filled"),
            get_content_name_async("roll_call_settings", "font_size"),
            get_content_description_async("roll_call_settings", "font_size"),
            self.font_size_spin,
        )
        self.addGroup(
            get_theme_icon("ic_fluent_slide_text_sparkle_20_filled"),
            get_content_name_async("roll_call_settings", "display_format"),
            get_content_description_async("roll_call_settings", "display_format"),
            self.display_format_combo,
        )
        self.addGroup(
            get_theme_icon("ic_fluent_group_list_20_filled"),
            get_content_name_async("roll_call_settings", "show_random"),
            get_content_description_async("roll_call_settings", "show_random"),
            self.show_random_format_combo,
        )


class roll_call_animation_settings(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # 创建垂直布局
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setSpacing(10)

        # 添加基础动画设置组件
        self.basic_animation_widget = roll_call_basic_animation_settings(self)
        self.vBoxLayout.addWidget(self.basic_animation_widget)

        # 添加颜色主题设置组件
        self.color_theme_widget = roll_call_color_theme_settings(self)
        self.vBoxLayout.addWidget(self.color_theme_widget)

        # 添加学生图片设置组件
        self.student_image_widget = roll_call_student_image_settings(self)
        self.vBoxLayout.addWidget(self.student_image_widget)


class roll_call_basic_animation_settings(GroupHeaderCardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle(
            get_content_name_async("roll_call_settings", "basic_animation_settings")
        )
        self.setBorderRadius(8)

        # 动画模式下拉框
        self.animation_combo = ComboBox()
        self.animation_combo.addItems(
            get_content_combo_name_async("roll_call_settings", "animation")
        )
        self.animation_combo.setCurrentIndex(
            readme_settings_async("roll_call_settings", "animation")
        )
        self.animation_combo.currentIndexChanged.connect(
            lambda: update_settings(
                "roll_call_settings", "animation", self.animation_combo.currentIndex()
            )
        )

        # 动画间隔输入框
        self.animation_interval_spin = SpinBox()
        self.animation_interval_spin.setFixedWidth(WIDTH_SPINBOX)
        self.animation_interval_spin.setMinimum(1)
        self.animation_interval_spin.setSuffix("ms")
        self.animation_interval_spin.setValue(
            readme_settings_async("roll_call_settings", "animation_interval")
        )
        self.animation_interval_spin.valueChanged.connect(
            lambda: update_settings(
                "roll_call_settings",
                "animation_interval",
                self.animation_interval_spin.value(),
            )
        )

        # 自动播放次数输入框
        self.autoplay_count_spin = SpinBox()
        self.autoplay_count_spin.setFixedWidth(WIDTH_SPINBOX)
        self.autoplay_count_spin.setMinimum(1)
        self.autoplay_count_spin.setSuffix("次")
        self.autoplay_count_spin.setValue(
            readme_settings_async("roll_call_settings", "autoplay_count")
        )
        self.autoplay_count_spin.valueChanged.connect(
            lambda: update_settings(
                "roll_call_settings", "autoplay_count", self.autoplay_count_spin.value()
            )
        )

        # 添加设置项到分组
        self.addGroup(
            get_theme_icon("ic_fluent_sanitize_20_filled"),
            get_content_name_async("roll_call_settings", "animation"),
            get_content_description_async("roll_call_settings", "animation"),
            self.animation_combo,
        )
        self.addGroup(
            get_theme_icon("ic_fluent_timeline_20_filled"),
            get_content_name_async("roll_call_settings", "animation_interval"),
            get_content_description_async("roll_call_settings", "animation_interval"),
            self.animation_interval_spin,
        )
        self.addGroup(
            get_theme_icon("ic_fluent_slide_play_20_filled"),
            get_content_name_async("roll_call_settings", "autoplay_count"),
            get_content_description_async("roll_call_settings", "autoplay_count"),
            self.autoplay_count_spin,
        )


class roll_call_color_theme_settings(GroupHeaderCardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle(
            get_content_name_async("roll_call_settings", "color_theme_settings")
        )
        self.setBorderRadius(8)

        # 颜色主题下拉框
        self.animation_color_theme_combo = ComboBox()
        self.animation_color_theme_combo.addItems(
            get_content_combo_name_async("roll_call_settings", "animation_color_theme")
        )
        self.animation_color_theme_combo.setCurrentIndex(
            readme_settings_async("roll_call_settings", "animation_color_theme")
        )
        self.animation_color_theme_combo.currentIndexChanged.connect(
            lambda: update_settings(
                "roll_call_settings",
                "animation_color_theme",
                self.animation_color_theme_combo.currentIndex(),
            )
        )

        # 动画固定颜色
        self.animation_fixed_color_button = ColorConfigItem(
            "roll_call_settings",
            "animation_fixed_color",
            readme_settings_async("roll_call_settings", "animation_fixed_color"),
        )
        self.animation_fixed_color_button.valueChanged.connect(
            lambda color: update_settings(
                "roll_call_settings", "animation_fixed_color", color.name()
            )
        )

        # 添加设置项到分组
        self.addGroup(
            get_theme_icon("ic_fluent_color_20_filled"),
            get_content_name_async("roll_call_settings", "animation_color_theme"),
            get_content_description_async(
                "roll_call_settings", "animation_color_theme"
            ),
            self.animation_color_theme_combo,
        )

        self.animationColorCard = ColorSettingCard(
            self.animation_fixed_color_button,
            get_theme_icon("ic_fluent_text_color_20_filled"),
            self.tr(
                get_content_name_async("roll_call_settings", "animation_fixed_color")
            ),
            self.tr(
                get_content_description_async(
                    "roll_call_settings", "animation_fixed_color"
                )
            ),
            self,
        )

        self.vBoxLayout.addWidget(self.animationColorCard)


class roll_call_student_image_settings(GroupHeaderCardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle(
            get_content_name_async("roll_call_settings", "student_image_settings")
        )
        self.setBorderRadius(8)

        # 学生图片开关
        self.student_image_switch = SwitchButton()
        self.student_image_switch.setOffText(
            get_content_switchbutton_name_async(
                "roll_call_settings", "student_image", "disable"
            )
        )
        self.student_image_switch.setOnText(
            get_content_switchbutton_name_async(
                "roll_call_settings", "student_image", "enable"
            )
        )
        self.student_image_switch.setChecked(
            readme_settings_async("roll_call_settings", "student_image")
        )
        self.student_image_switch.checkedChanged.connect(
            lambda: update_settings(
                "roll_call_settings",
                "student_image",
                self.student_image_switch.isChecked(),
            )
        )

        # 打开学生图片文件夹按钮
        self.open_student_image_folder_button = PushButton(
            get_content_name_async("roll_call_settings", "open_student_image_folder")
        )
        self.open_student_image_folder_button.clicked.connect(
            lambda: self.open_student_image_folder()
        )

        # 添加设置项到分组
        self.addGroup(
            get_theme_icon("ic_fluent_image_circle_20_filled"),
            get_content_name_async("roll_call_settings", "student_image"),
            get_content_description_async("roll_call_settings", "student_image"),
            self.student_image_switch,
        )
        self.addGroup(
            get_theme_icon("ic_fluent_folder_open_20_filled"),
            get_content_name_async("roll_call_settings", "open_student_image_folder"),
            get_content_description_async(
                "roll_call_settings", "open_student_image_folder"
            ),
            self.open_student_image_folder_button,
        )

    def open_student_image_folder(self):
        """打开学生图片文件夹"""
        folder_path = get_data_path(STUDENT_IMAGE_FOLDER)
        if not folder_path.exists():
            os.makedirs(folder_path, exist_ok=True)
        if folder_path:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder_path)))
        else:
            logger.error("无法获取学生图片文件夹路径")
