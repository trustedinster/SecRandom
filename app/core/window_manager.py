from loguru import logger
from app.tools.settings_access import readme_settings_async


app_start_time = 0


class WindowManager:
    """窗口管理器，负责创建和管理所有窗口实例"""

    def __init__(self):
        self.main_window = None
        self.settings_window = None
        self.float_window = None
        self.url_handler = None

    def set_url_handler(self, url_handler):
        """设置URL处理器

        Args:
            url_handler: URL处理器实例
        """
        self.url_handler = url_handler

    def create_main_window(self):
        """创建主窗口实例"""
        try:
            from app.view.main.window import MainWindow

            self.create_float_window()
            self.main_window = MainWindow(
                float_window=self.float_window, url_handler_instance=self.url_handler
            )

            from app.common.safety.verify_ops import (
                should_require_password,
                require_and_run,
            )

            def handle_show_settings_requested(page_name="basicSettingsInterface"):
                """处理显示设置请求，添加验证逻辑"""
                if should_require_password("open_settings"):
                    logger.debug(f"打开设置页面需要验证：{page_name}")

                    def on_verified():
                        """验证通过后，正常打开设置页面"""
                        self.show_settings_window(page_name, is_preview=False)

                    def on_preview():
                        """点击预览按钮后，以预览模式打开设置页面"""
                        self.show_settings_window(page_name, is_preview=True)

                    require_and_run(
                        "open_settings",
                        self.main_window,
                        on_verified,
                        on_preview=on_preview,
                    )
                else:
                    logger.debug(f"打开设置页面无需验证：{page_name}")
                    self.show_settings_window(page_name, is_preview=False)

            self.main_window.showSettingsRequested.connect(
                handle_show_settings_requested
            )
            self.main_window.showSettingsRequestedAbout.connect(
                self.show_settings_window_about
            )
            self.main_window.showFloatWindowRequested.connect(self.show_float_window)

            show_startup_window = readme_settings_async(
                "basic_settings", "show_startup_window"
            )
            if show_startup_window:
                self.main_window.show()

            if self.url_handler:
                self.url_handler.showMainPageRequested.connect(
                    self.main_window._handle_main_page_requested
                )
                self.url_handler.showTrayActionRequested.connect(
                    lambda action: self.main_window._handle_tray_action_requested(
                        action
                    )
                )
                self.url_handler.showSettingsRequested.connect(
                    self.show_settings_window
                )

            startup_display_float = readme_settings_async(
                "floating_window_management", "startup_display_floating_window"
            )
            if startup_display_float:
                self.show_float_window()

            try:
                import time

                elapsed = time.perf_counter() - app_start_time
                logger.debug(f"主窗口创建完成，启动耗时: {elapsed:.3f}s")
            except Exception as e:
                logger.exception("计算启动耗时出错（已忽略）: {}", e)
        except Exception as e:
            logger.error(f"创建主窗口失败: {e}", exc_info=True)

    def create_settings_window(self, is_preview=False):
        """创建设置窗口实例

        Args:
            is_preview: 是否为预览模式，默认为 False
        """
        try:
            from app.view.settings.settings import SettingsWindow

            self.settings_window = SettingsWindow(is_preview=is_preview)
        except Exception as e:
            logger.error(f"创建设置窗口失败: {e}", exc_info=True)

    def show_settings_window(
        self, page_name="basicSettingsInterface", is_preview=False
    ):
        """显示设置窗口

        Args:
            page_name: 设置页面名称，默认为 basicSettingsInterface
            is_preview: 是否为预览模式，默认为 False
        """
        try:
            if self.settings_window is not None:
                if (
                    hasattr(self.settings_window, "is_preview")
                    and self.settings_window.is_preview != is_preview
                ):
                    logger.debug(f"重新创建设置窗口，预览模式: {is_preview}")
                    try:
                        self.settings_window.close()
                        self.settings_window.deleteLater()
                    except Exception as close_e:
                        logger.error(f"关闭现有设置窗口失败: {close_e}")
                    self.settings_window = None

            if self.settings_window is None:
                self.create_settings_window(is_preview=is_preview)

            if self.settings_window is not None:
                self.settings_window.show_settings_window()
                self.settings_window._handle_settings_page_request(page_name)
        except Exception as e:
            logger.error(f"显示设置窗口失败: {e}", exc_info=True)

    def show_settings_window_about(self):
        """显示关于窗口"""
        try:
            if self.settings_window is None:
                self.create_settings_window()
            if self.settings_window is not None:
                self.settings_window.show_settings_window_about()
        except Exception as e:
            logger.error(f"显示关于窗口失败: {e}", exc_info=True)

    def create_float_window(self):
        """创建浮窗实例"""
        try:
            from app.view.floating_window.levitation import LevitationWindow

            self.float_window = LevitationWindow()
        except Exception as e:
            logger.error(f"创建浮窗失败: {e}", exc_info=True)

    def show_float_window(self):
        """显示浮窗"""
        try:
            if self.float_window is None:
                self.create_float_window()
            if self.float_window is not None:
                self.float_window.show()
        except Exception as e:
            logger.error(f"显示浮窗失败: {e}", exc_info=True)

    def get_main_window(self):
        """获取主窗口实例"""
        return self.main_window

    def get_settings_window(self):
        """获取设置窗口实例"""
        return self.settings_window

    def get_float_window(self):
        """获取浮窗实例"""
        return self.float_window


app_start_time = 0
