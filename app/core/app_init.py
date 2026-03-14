from PySide6.QtCore import QTimer
from loguru import logger

from app.tools.config import remove_record
from app.tools.settings_access import readme_settings_async
from app.tools.update_utils import check_for_updates_on_startup
from app.tools.variable import APP_INIT_DELAY
from app.core.font_manager import (
    apply_font_settings,
    ensure_application_font_point_size,
)
from app.core.window_manager import WindowManager
from app.core.utils import safe_execute


class AppInitializer:
    """应用程序初始化器，负责协调所有初始化任务"""

    def __init__(self, window_manager: WindowManager) -> None:
        """初始化应用初始化器

        Args:
            window_manager: 窗口管理器实例
        """
        self.window_manager = window_manager

    def initialize(self) -> None:
        """初始化应用程序"""
        self._schedule_initialization_tasks()
        logger.debug("应用初始化调度已启动，主窗口将在延迟后创建")

    def _schedule_initialization_tasks(self) -> None:
        """调度所有初始化任务"""
        guide_completed = readme_settings_async("basic_settings", "guide_completed")
        init_delay = 0 if not guide_completed else APP_INIT_DELAY

        if init_delay > 0:
            QTimer.singleShot(init_delay, self._run_startup_phase)
        else:
            self._run_startup_phase()

        self._register_post_show_tasks()

    def _register_post_show_tasks(self) -> None:
        self.window_manager.register_after_first_window_shown(
            self._run_post_first_window_tasks
        )

    def _run_startup_phase(self) -> None:
        """执行首窗显示前的关键初始化任务。"""
        startup_steps = (
            (apply_font_settings, "应用字体设置失败"),
            (self._apply_theme, "加载主题失败"),
            (self._apply_theme_color, "加载主题颜色失败"),
            (self._clear_restart_record_now, "清除重启记录失败"),
            (self.window_manager.create_main_window, "创建主窗口失败"),
        )

        for step, error_message in startup_steps:
            safe_execute(step, error_message=error_message)

    def _run_post_first_window_tasks(self) -> None:
        """在首个窗口显示后启动非关键任务。"""
        safe_execute(
            self._run_main_window_post_show_tasks,
            error_message="启动主窗口延后任务失败",
        )
        safe_execute(
            lambda: check_for_updates_on_startup(None),
            error_message="检查更新失败",
        )
        QTimer.singleShot(
            1500,
            lambda: safe_execute(
                self._do_warmup_face_detector_devices,
                error_message="预热摄像头设备失败",
            ),
        )

    def _run_main_window_post_show_tasks(self) -> None:
        main_window = getattr(self.window_manager, "main_window", None)
        if main_window is None:
            return

        if hasattr(main_window, "schedule_post_startup_tasks"):
            main_window.schedule_post_startup_tasks()

    def _apply_theme(self) -> None:
        """应用主题设置"""
        from qfluentwidgets import setTheme, Theme

        theme = readme_settings_async("basic_settings", "theme")
        if theme == "DARK":
            setTheme(Theme.DARK)
        elif theme == "AUTO":
            setTheme(Theme.AUTO)
        else:
            setTheme(Theme.LIGHT)
        ensure_application_font_point_size()

    def _apply_theme_color(self) -> None:
        """加载主题颜色"""
        from qfluentwidgets import setThemeColor

        setThemeColor(readme_settings_async("basic_settings", "theme_color"))

    def _clear_restart_record_now(self) -> None:
        """清除重启记录"""
        remove_record("", "", "", "restart")

    def _do_warmup_face_detector_devices(self) -> None:
        from app.common.camera_preview_backend import warmup_camera_devices_async

        warmup_camera_devices_async(force_refresh=True)
