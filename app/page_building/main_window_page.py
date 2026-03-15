# 导入库
from PySide6.QtWidgets import QFrame
from PySide6.QtCore import Qt

# 导入页面模板
from app.page_building.page_template import PageTemplate, PivotPageTemplate

# 导入默认设置
from app.tools.settings_default import *
from app.Language.obtain_language import *
from app.tools.settings_access import get_settings_signals

from app.tools.theme_loader import ThemeLoader


class _ThemedMainPage(PageTemplate):
    """Shared wrapper for theme-aware main pages."""

    THEME_NAME = ""
    CONTENT_ATTR_NAME = ""
    THEME_SETTING_KEYS = ()

    def __init__(self, parent: QFrame = None):
        widget_class = ThemeLoader.load_theme_widget(
            self.THEME_NAME, self._get_default_widget_class()
        )
        setattr(self, self.CONTENT_ATTR_NAME, None)
        super().__init__(content_widget_class=widget_class, parent=parent)
        get_settings_signals().settingChanged.connect(self._on_global_setting_changed)

    @staticmethod
    def _get_default_widget_class():
        raise NotImplementedError

    def _on_global_setting_changed(self, group, key, value):
        if group == "theme_management" and key in self.THEME_SETTING_KEYS:
            self.content_widget_class = ThemeLoader.load_theme_widget(
                self.THEME_NAME, self._get_default_widget_class()
            )
            self.handle_settings_change()

    def create_content(self):
        """后台创建内容组件，避免堵塞进程"""
        super().create_content()
        if not hasattr(self, "contentWidget"):
            return

        content_widget = self.contentWidget
        setattr(self, self.CONTENT_ATTR_NAME, content_widget)

        if content_widget and content_widget.property("theme_html_wrapper"):
            if hasattr(self, "_inner_layout_lazy") and self._inner_layout_lazy:
                self._inner_layout_lazy.setAlignment(Qt.AlignmentFlag.AlignTop)
                self._inner_layout_lazy.setContentsMargins(0, 0, 0, 0)
                self._inner_layout_lazy.setSpacing(0)
            if hasattr(self, "_main_layout_lazy") and self._main_layout_lazy:
                self._main_layout_lazy.setContentsMargins(0, 0, 0, 0)
                self._main_layout_lazy.setSpacing(0)

        if hasattr(content_widget, "settingsChanged"):
            content_widget.settingsChanged.connect(self.handle_settings_change)

    def handle_settings_change(self):
        """处理设置变化信号"""
        self.clear_content()
        self.create_content()

    def clear_content(self):
        """清除内容"""
        if hasattr(self, "_inner_layout_lazy") and self._inner_layout_lazy.count() > 0:
            item = self._inner_layout_lazy.takeAt(0)
            if item and item.widget():
                widget = item.widget()
                widget.deleteLater()
        self.content_created = False
        self.contentWidget = None
        setattr(self, self.CONTENT_ATTR_NAME, None)


class roll_call_page(_ThemedMainPage):
    """创建班级点名页面"""

    THEME_NAME = "roll_call"
    CONTENT_ATTR_NAME = "roll_call_widget"
    THEME_SETTING_KEYS = (
        "roll_call_theme_id",
        "roll_call_theme_type",
    )

    @staticmethod
    def _get_default_widget_class():
        from app.view.main.roll_call import roll_call

        return roll_call


class lottery_page(_ThemedMainPage):
    """创建班级点名页面"""

    THEME_NAME = "lottery"
    CONTENT_ATTR_NAME = "lottery_widget"
    THEME_SETTING_KEYS = (
        "lottery_theme_id",
        "lottery_theme_type",
    )

    @staticmethod
    def _get_default_widget_class():
        from app.view.main.lottery import Lottery

        return Lottery


class history_page(PivotPageTemplate):
    """创建历史记录页面"""

    def __init__(self, parent: QFrame = None):
        page_config = {
            "roll_call_history_table": get_content_name_async(
                "roll_call_history_table", "title"
            ),
            "lottery_history_table": get_content_name_async(
                "lottery_history_table", "title"
            ),
        }
        super().__init__(page_config, parent, base_path="app.view.settings.history")
