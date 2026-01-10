# 导入库
from PySide6.QtWidgets import QFrame
from PySide6.QtCore import QTimer

# 导入页面模板
from app.page_building.page_template import PageTemplate, PivotPageTemplate

# 导入默认设置
from app.tools.settings_default import *
from app.Language.obtain_language import *

# 导入自定义页面内容组件
from app.view.main.roll_call import roll_call
from app.view.main.lottery import Lottery


class roll_call_page(PageTemplate):
    """创建班级点名页面"""

    def __init__(self, parent: QFrame = None):
        super().__init__(content_widget_class=roll_call, parent=parent)
        self.roll_call_widget = None

    def create_content(self):
        """后台创建内容组件，避免堵塞进程"""
        super().create_content()
        # 获取点名组件实例并连接信号
        if hasattr(self, "contentWidget"):
            self.roll_call_widget = self.contentWidget
            # 连接设置变化信号
            self.roll_call_widget.settingsChanged.connect(self.handle_settings_change)

    def handle_settings_change(self):
        """处理设置变化信号"""
        # 清除页面缓存并重新创建
        self.clear_content()
        QTimer.singleShot(0, self._recreate_content)

    def _recreate_content(self):
        """重新创建内容"""
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


class lottery_page(PageTemplate):
    """创建班级点名页面"""

    def __init__(self, parent: QFrame = None):
        super().__init__(content_widget_class=Lottery, parent=parent)
        self.lottery_widget = None

    def create_content(self):
        """后台创建内容组件，避免堵塞进程"""
        super().create_content()
        # 获取奖池组件实例并连接信号
        if hasattr(self, "contentWidget"):
            self.lottery_widget = self.contentWidget
            # 连接设置变化信号
            self.lottery_widget.settingsChanged.connect(self.handle_settings_change)

    def handle_settings_change(self):
        """处理设置变化信号"""
        # 清除页面缓存并重新创建
        self.clear_content()
        QTimer.singleShot(0, self._recreate_content)

    def _recreate_content(self):
        """重新创建内容"""
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
        super().__init__(page_config, parent)
        self.set_base_path("app.view.settings.history")
