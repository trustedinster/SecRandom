# ==================================================
# 导入库
# ==================================================

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
from app.Language.obtain_language import *


# ==================================================
# 公平抽取设置
# ==================================================
class fair_draw(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # 创建垂直布局
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setSpacing(10)

        # 添加基础公平设置组件
        self.basic_fair_settings_widget = basic_fair_settings(self)
        self.vBoxLayout.addWidget(self.basic_fair_settings_widget)

        # 添加权重范围设置组件
        self.weight_range_settings_widget = weight_range_settings(self)
        self.vBoxLayout.addWidget(self.weight_range_settings_widget)

        # 添加抽取后屏蔽设置组件
        self.shield_settings_widget = shield_settings(self)
        self.vBoxLayout.addWidget(self.shield_settings_widget)

        # 添加频率函数设置组件
        self.frequency_settings_widget = frequency_settings(self)
        self.vBoxLayout.addWidget(self.frequency_settings_widget)

        # 添加平衡权重设置组件
        self.balance_weight_settings_widget = balance_weight_settings(self)
        self.vBoxLayout.addWidget(self.balance_weight_settings_widget)

        # 添加冷启动设置组件
        self.cold_start_settings_widget = cold_start_settings(self)
        self.vBoxLayout.addWidget(self.cold_start_settings_widget)


class basic_fair_settings(GroupHeaderCardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle(
            get_content_name_async("fair_draw_settings", "basic_fair_settings")
        )
        self.setBorderRadius(8)

        # 总抽取次数是否纳入计算
        self.fair_draw_switch = SwitchButton()
        self.fair_draw_switch.setOffText(
            get_content_switchbutton_name_async(
                "fair_draw_settings", "fair_draw", "disable"
            )
        )
        self.fair_draw_switch.setOnText(
            get_content_switchbutton_name_async(
                "fair_draw_settings", "fair_draw", "enable"
            )
        )
        self.fair_draw_switch.setChecked(
            readme_settings_async("fair_draw_settings", "fair_draw")
        )
        self.fair_draw_switch.checkedChanged.connect(
            lambda: update_settings(
                "fair_draw_settings", "fair_draw", self.fair_draw_switch.isChecked()
            )
        )

        # 抽小组次数是否纳入计算
        self.fair_draw_group_switch = SwitchButton()
        self.fair_draw_group_switch.setOffText(
            get_content_switchbutton_name_async(
                "fair_draw_settings", "fair_draw_group", "disable"
            )
        )
        self.fair_draw_group_switch.setOnText(
            get_content_switchbutton_name_async(
                "fair_draw_settings", "fair_draw_group", "enable"
            )
        )
        self.fair_draw_group_switch.setChecked(
            readme_settings_async("fair_draw_settings", "fair_draw_group")
        )
        self.fair_draw_group_switch.checkedChanged.connect(
            lambda: update_settings(
                "fair_draw_settings",
                "fair_draw_group",
                self.fair_draw_group_switch.isChecked(),
            )
        )

        # 抽性别次数是否纳入计算
        self.fair_draw_gender_switch = SwitchButton()
        self.fair_draw_gender_switch.setOffText(
            get_content_switchbutton_name_async(
                "fair_draw_settings", "fair_draw_gender", "disable"
            )
        )
        self.fair_draw_gender_switch.setOnText(
            get_content_switchbutton_name_async(
                "fair_draw_settings", "fair_draw_gender", "enable"
            )
        )
        self.fair_draw_gender_switch.setChecked(
            readme_settings_async("fair_draw_settings", "fair_draw_gender")
        )
        self.fair_draw_gender_switch.checkedChanged.connect(
            lambda: update_settings(
                "fair_draw_settings",
                "fair_draw_gender",
                self.fair_draw_gender_switch.isChecked(),
            )
        )

        # 距上次抽取时间是否纳入计算
        self.fair_draw_time_switch = SwitchButton()
        self.fair_draw_time_switch.setOffText(
            get_content_switchbutton_name_async(
                "fair_draw_settings", "fair_draw_time", "disable"
            )
        )
        self.fair_draw_time_switch.setOnText(
            get_content_switchbutton_name_async(
                "fair_draw_settings", "fair_draw_time", "enable"
            )
        )
        self.fair_draw_time_switch.setChecked(
            readme_settings_async("fair_draw_settings", "fair_draw_time")
        )
        self.fair_draw_time_switch.checkedChanged.connect(
            lambda: update_settings(
                "fair_draw_settings",
                "fair_draw_time",
                self.fair_draw_time_switch.isChecked(),
            )
        )

        # 添加设置项到分组
        self.addGroup(
            get_theme_icon("ic_fluent_lottery_20_filled"),
            get_content_name_async("fair_draw_settings", "fair_draw"),
            get_content_description_async("fair_draw_settings", "fair_draw"),
            self.fair_draw_switch,
        )
        self.addGroup(
            get_theme_icon("ic_fluent_lottery_20_filled"),
            get_content_name_async("fair_draw_settings", "fair_draw_group"),
            get_content_description_async("fair_draw_settings", "fair_draw_group"),
            self.fair_draw_group_switch,
        )
        self.addGroup(
            get_theme_icon("ic_fluent_lottery_20_filled"),
            get_content_name_async("fair_draw_settings", "fair_draw_gender"),
            get_content_description_async("fair_draw_settings", "fair_draw_gender"),
            self.fair_draw_gender_switch,
        )
        self.addGroup(
            get_theme_icon("ic_fluent_lottery_20_filled"),
            get_content_name_async("fair_draw_settings", "fair_draw_time"),
            get_content_description_async("fair_draw_settings", "fair_draw_time"),
            self.fair_draw_time_switch,
        )


class weight_range_settings(GroupHeaderCardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle(
            get_content_name_async("fair_draw_settings", "weight_range_settings")
        )
        self.setBorderRadius(8)

        # 设置基础权重
        self.base_weight_spinbox = DoubleSpinBox()
        self.base_weight_spinbox.setFixedWidth(WIDTH_SPINBOX)
        self.base_weight_spinbox.setRange(0.01, 1000.00)
        self.base_weight_spinbox.setValue(
            readme_settings_async("fair_draw_settings", "base_weight")
        )
        self.base_weight_spinbox.valueChanged.connect(
            lambda: update_settings(
                "fair_draw_settings", "base_weight", self.base_weight_spinbox.value()
            )
        )

        # 设置权重范围最小值
        self.min_weight_spinbox = DoubleSpinBox()
        self.min_weight_spinbox.setFixedWidth(WIDTH_SPINBOX)
        self.min_weight_spinbox.setRange(0.01, 1000.00)
        self.min_weight_spinbox.setValue(
            readme_settings_async("fair_draw_settings", "min_weight")
        )
        self.min_weight_spinbox.valueChanged.connect(
            lambda: update_settings(
                "fair_draw_settings", "min_weight", self.min_weight_spinbox.value()
            )
        )

        # 设置权重范围最大值
        self.max_weight_spinbox = DoubleSpinBox()
        self.max_weight_spinbox.setFixedWidth(WIDTH_SPINBOX)
        self.max_weight_spinbox.setRange(0.01, 1000.00)
        self.max_weight_spinbox.setValue(
            readme_settings_async("fair_draw_settings", "max_weight")
        )
        self.max_weight_spinbox.valueChanged.connect(
            lambda: update_settings(
                "fair_draw_settings", "max_weight", self.max_weight_spinbox.value()
            )
        )

        # 添加设置项到分组
        self.addGroup(
            get_theme_icon("ic_fluent_scale_fit_20_filled"),
            get_content_name_async("fair_draw_settings", "base_weight"),
            get_content_description_async("fair_draw_settings", "base_weight"),
            self.base_weight_spinbox,
        )
        self.addGroup(
            get_theme_icon("ic_fluent_scale_fit_20_filled"),
            get_content_name_async("fair_draw_settings", "min_weight"),
            get_content_description_async("fair_draw_settings", "min_weight"),
            self.min_weight_spinbox,
        )
        self.addGroup(
            get_theme_icon("ic_fluent_scale_fit_20_filled"),
            get_content_name_async("fair_draw_settings", "max_weight"),
            get_content_description_async("fair_draw_settings", "max_weight"),
            self.max_weight_spinbox,
        )


class shield_settings(GroupHeaderCardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle(get_content_name_async("fair_draw_settings", "shield_settings"))
        self.setBorderRadius(8)

        # 启用抽取后屏蔽
        self.shield_enabled_switch = SwitchButton()
        self.shield_enabled_switch.setOffText(
            get_content_switchbutton_name_async(
                "fair_draw_settings", "shield_enabled", "disable"
            )
        )
        self.shield_enabled_switch.setOnText(
            get_content_switchbutton_name_async(
                "fair_draw_settings", "shield_enabled", "enable"
            )
        )
        self.shield_enabled_switch.setChecked(
            readme_settings_async("fair_draw_settings", "shield_enabled")
        )
        self.shield_enabled_switch.checkedChanged.connect(
            lambda: update_settings(
                "fair_draw_settings",
                "shield_enabled",
                self.shield_enabled_switch.isChecked(),
            )
        )

        # 屏蔽时间
        self.shield_time_spinbox = DoubleSpinBox()
        self.shield_time_spinbox.setFixedWidth(WIDTH_SPINBOX)
        self.shield_time_spinbox.setRange(0.1, 60.00)
        self.shield_time_spinbox.setValue(
            readme_settings_async("fair_draw_settings", "shield_time")
        )
        self.shield_time_spinbox.valueChanged.connect(
            lambda: update_settings(
                "fair_draw_settings", "shield_time", self.shield_time_spinbox.value()
            )
        )

        # 屏蔽时间单位
        self.shield_time_unit_combobox = ComboBox()
        self.shield_time_unit_combobox.setFixedWidth(WIDTH_SPINBOX)
        self.shield_time_unit_combobox.addItems(
            get_content_combo_name_async("fair_draw_settings", "shield_time_unit")
        )
        self.shield_time_unit_combobox.setCurrentIndex(
            readme_settings_async("fair_draw_settings", "shield_time_unit")
        )
        self.shield_time_unit_combobox.currentIndexChanged.connect(
            lambda: update_settings(
                "fair_draw_settings",
                "shield_time_unit",
                self.shield_time_unit_combobox.currentIndex(),
            )
        )

        # 添加设置项到分组
        self.addGroup(
            get_theme_icon("ic_fluent_shield_20_filled"),
            get_content_name_async("fair_draw_settings", "shield_enabled"),
            get_content_description_async("fair_draw_settings", "shield_enabled"),
            self.shield_enabled_switch,
        )
        self.addGroup(
            get_theme_icon("ic_fluent_shield_20_filled"),
            get_content_name_async("fair_draw_settings", "shield_time"),
            get_content_description_async("fair_draw_settings", "shield_time"),
            self.shield_time_spinbox,
        )
        self.addGroup(
            get_theme_icon("ic_fluent_shield_20_filled"),
            get_content_name_async("fair_draw_settings", "shield_time_unit"),
            get_content_description_async("fair_draw_settings", "shield_time_unit"),
            self.shield_time_unit_combobox,
        )


class frequency_settings(GroupHeaderCardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle(
            get_content_name_async("fair_draw_settings", "frequency_settings")
        )
        self.setBorderRadius(8)

        # 频率惩罚函数类型
        self.frequency_function_combobox = ComboBox()
        self.frequency_function_combobox.setFixedWidth(WIDTH_SPINBOX)
        self.frequency_function_combobox.addItems(
            get_content_combo_name_async("fair_draw_settings", "frequency_function")
        )
        self.frequency_function_combobox.setCurrentIndex(
            readme_settings_async("fair_draw_settings", "frequency_function")
        )
        self.frequency_function_combobox.currentIndexChanged.connect(
            lambda: update_settings(
                "fair_draw_settings",
                "frequency_function",
                self.frequency_function_combobox.currentIndex(),
            )
        )

        # 频率惩罚权重
        self.frequency_weight_spinbox = DoubleSpinBox()
        self.frequency_weight_spinbox.setFixedWidth(WIDTH_SPINBOX)
        self.frequency_weight_spinbox.setRange(0.01, 5.00)
        self.frequency_weight_spinbox.setValue(
            readme_settings_async("fair_draw_settings", "frequency_weight")
        )
        self.frequency_weight_spinbox.valueChanged.connect(
            lambda: update_settings(
                "fair_draw_settings",
                "frequency_weight",
                self.frequency_weight_spinbox.value(),
            )
        )

        # 添加设置项到分组
        self.addGroup(
            get_theme_icon("ic_fluent_arrow_clockwise_20_filled"),
            get_content_name_async("fair_draw_settings", "frequency_function"),
            get_content_description_async("fair_draw_settings", "frequency_function"),
            self.frequency_function_combobox,
        )
        self.addGroup(
            get_theme_icon("ic_fluent_arrow_clockwise_20_filled"),
            get_content_name_async("fair_draw_settings", "frequency_weight"),
            get_content_description_async("fair_draw_settings", "frequency_weight"),
            self.frequency_weight_spinbox,
        )


class balance_weight_settings(GroupHeaderCardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle(
            get_content_name_async("fair_draw_settings", "balance_weight_settings")
        )
        self.setBorderRadius(8)

        # 小组平衡权重
        self.group_weight_spinbox = DoubleSpinBox()
        self.group_weight_spinbox.setFixedWidth(WIDTH_SPINBOX)
        self.group_weight_spinbox.setRange(0.01, 5.00)
        self.group_weight_spinbox.setValue(
            readme_settings_async("fair_draw_settings", "group_weight")
        )
        self.group_weight_spinbox.valueChanged.connect(
            lambda: update_settings(
                "fair_draw_settings", "group_weight", self.group_weight_spinbox.value()
            )
        )

        # 性别平衡权重
        self.gender_weight_spinbox = DoubleSpinBox()
        self.gender_weight_spinbox.setFixedWidth(WIDTH_SPINBOX)
        self.gender_weight_spinbox.setRange(0.01, 5.00)
        self.gender_weight_spinbox.setValue(
            readme_settings_async("fair_draw_settings", "gender_weight")
        )
        self.gender_weight_spinbox.valueChanged.connect(
            lambda: update_settings(
                "fair_draw_settings",
                "gender_weight",
                self.gender_weight_spinbox.value(),
            )
        )

        # 时间因子权重
        self.time_weight_spinbox = DoubleSpinBox()
        self.time_weight_spinbox.setFixedWidth(WIDTH_SPINBOX)
        self.time_weight_spinbox.setRange(0.01, 5.00)
        self.time_weight_spinbox.setValue(
            readme_settings_async("fair_draw_settings", "time_weight")
        )
        self.time_weight_spinbox.valueChanged.connect(
            lambda: update_settings(
                "fair_draw_settings", "time_weight", self.time_weight_spinbox.value()
            )
        )

        # 添加设置项到分组
        self.addGroup(
            get_theme_icon("ic_fluent_scales_20_filled"),
            get_content_name_async("fair_draw_settings", "group_weight"),
            get_content_description_async("fair_draw_settings", "group_weight"),
            self.group_weight_spinbox,
        )
        self.addGroup(
            get_theme_icon("ic_fluent_scales_20_filled"),
            get_content_name_async("fair_draw_settings", "gender_weight"),
            get_content_description_async("fair_draw_settings", "gender_weight"),
            self.gender_weight_spinbox,
        )
        self.addGroup(
            get_theme_icon("ic_fluent_scales_20_filled"),
            get_content_name_async("fair_draw_settings", "time_weight"),
            get_content_description_async("fair_draw_settings", "time_weight"),
            self.time_weight_spinbox,
        )


class cold_start_settings(GroupHeaderCardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle(
            get_content_name_async("fair_draw_settings", "cold_start_settings")
        )
        self.setBorderRadius(8)

        # 冷启动模式开关
        self.cold_start_enabled_switch = SwitchButton()
        self.cold_start_enabled_switch.setOffText(
            get_content_switchbutton_name_async(
                "fair_draw_settings", "cold_start_enabled", "disable"
            )
        )
        self.cold_start_enabled_switch.setOnText(
            get_content_switchbutton_name_async(
                "fair_draw_settings", "cold_start_enabled", "enable"
            )
        )
        self.cold_start_enabled_switch.setChecked(
            readme_settings_async("fair_draw_settings", "cold_start_enabled")
        )
        self.cold_start_enabled_switch.checkedChanged.connect(
            lambda: update_settings(
                "fair_draw_settings",
                "cold_start_enabled",
                self.cold_start_enabled_switch.isChecked(),
            )
        )

        # 冷启动轮次
        self.cold_start_rounds_spinbox = SpinBox()
        self.cold_start_rounds_spinbox.setFixedWidth(WIDTH_SPINBOX)
        self.cold_start_rounds_spinbox.setRange(1, 100)
        self.cold_start_rounds_spinbox.setValue(
            readme_settings_async("fair_draw_settings", "cold_start_rounds")
        )
        self.cold_start_rounds_spinbox.valueChanged.connect(
            lambda: update_settings(
                "fair_draw_settings",
                "cold_start_rounds",
                self.cold_start_rounds_spinbox.value(),
            )
        )

        # 添加设置项到分组
        self.addGroup(
            get_theme_icon("ic_fluent_arrow_rotate_clockwise_20_filled"),
            get_content_name_async("fair_draw_settings", "cold_start_enabled"),
            get_content_description_async("fair_draw_settings", "cold_start_enabled"),
            self.cold_start_enabled_switch,
        )
        self.addGroup(
            get_theme_icon("ic_fluent_arrow_rotate_clockwise_20_filled"),
            get_content_name_async("fair_draw_settings", "cold_start_rounds"),
            get_content_description_async("fair_draw_settings", "cold_start_rounds"),
            self.cold_start_rounds_spinbox,
        )
