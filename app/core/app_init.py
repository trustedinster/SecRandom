from PySide6.QtCore import QTimer
from loguru import logger

from app.tools.settings_default import manage_settings_file
from app.tools.config import remove_record
from app.tools.settings_access import readme_settings_async
from app.tools.update_utils import check_for_updates_on_startup
from app.tools.variable import APP_INIT_DELAY
from app.core.font_manager import apply_font_settings
from app.core.window_manager import WindowManager


class AppInitializer:
    """应用程序初始化器，负责协调所有初始化任务"""

    def __init__(self, window_manager: WindowManager):
        """初始化应用初始化器

        Args:
            window_manager: 窗口管理器实例
        """
        self.window_manager = window_manager

    def initialize(self):
        """初始化应用程序"""
        self._manage_settings_file()
        self._schedule_initialization_tasks()
        logger.debug("应用初始化调度已启动，主窗口将在延迟后创建")

    def _manage_settings_file(self):
        """管理设置文件，确保其存在且完整"""
        manage_settings_file()

    def _schedule_initialization_tasks(self):
        """调度所有初始化任务"""
        self._load_theme()
        self._load_theme_color()
        self._clear_restart_record()
        self._check_updates()
        self._create_main_window()
        self._apply_font_settings()

    def _load_theme(self):
        """加载主题设置"""
        from qfluentwidgets import setTheme, Theme

        QTimer.singleShot(
            APP_INIT_DELAY,
            lambda: (
                setTheme(Theme.DARK)
                if readme_settings_async("basic_settings", "theme") == "DARK"
                else (
                    setTheme(Theme.AUTO)
                    if readme_settings_async("basic_settings", "theme") == "AUTO"
                    else setTheme(Theme.LIGHT)
                )
            ),
        )

    def _load_theme_color(self):
        """加载主题颜色"""
        from qfluentwidgets import setThemeColor

        QTimer.singleShot(
            APP_INIT_DELAY,
            lambda: setThemeColor(
                readme_settings_async("basic_settings", "theme_color")
            ),
        )

    def _clear_restart_record(self):
        """清除重启记录"""
        QTimer.singleShot(APP_INIT_DELAY, lambda: remove_record("", "", "", "restart"))

    def _check_updates(self):
        """检查是否需要安装更新"""
        QTimer.singleShot(APP_INIT_DELAY, lambda: check_for_updates_on_startup(None))

    def _create_main_window(self):
        """创建主窗口实例（但不自动显示）"""
        QTimer.singleShot(
            APP_INIT_DELAY, lambda: self.window_manager.create_main_window()
        )

    def _apply_font_settings(self):
        """应用字体设置"""
        QTimer.singleShot(APP_INIT_DELAY, lambda: apply_font_settings())
