"""
URL处理工具 - 处理应用启动时的URL参数
"""

import argparse
from loguru import logger
from typing import Optional, Dict, Any
from PySide6.QtCore import QObject, Signal
from app.common.IPC_URL import URLIPCHandler
from app.common.IPC_URL.url_command_handler import URLCommandHandler
from app.tools.settings_access import readme_settings_async


class URLHandler(QObject):
    """URL参数处理器"""

    # 信号定义
    showSettingsRequested = Signal(str)  # 请求显示设置页面
    showMainPageRequested = Signal(str)  # 请求显示主页面
    showTrayActionRequested = Signal(str)  # 请求执行托盘操作

    def __init__(self, app_name: str = "SecRandom", protocol_name: str = "secrandom"):
        """
        初始化URL处理器

        Args:
            app_name: 应用程序名称
            protocol_name: 自定义协议名称
        """
        super().__init__()
        self.app_name = app_name
        self.protocol_name = protocol_name
        self.url_ipc_handler = URLIPCHandler(app_name, protocol_name)
        self.command_handler = URLCommandHandler()

        # 连接信号
        self.command_handler.showSettingsRequested.connect(
            self.showSettingsRequested.emit
        )
        self.command_handler.showMainPageRequested.connect(
            self.showMainPageRequested.emit
        )
        self.command_handler.showTrayActionRequested.connect(
            self.showTrayActionRequested.emit
        )

    def parse_command_line_args(self) -> Optional[Dict[str, Any]]:
        """
        解析命令行参数

        Returns:
            如果有URL参数则返回解析结果，否则返回None
        """
        parser = argparse.ArgumentParser(description=f"{self.app_name} URL Handler")
        parser.add_argument("--url", type=str, help="URL参数")

        # 解析已知的参数，忽略未知参数
        known_args, unknown_args = parser.parse_known_args()

        if known_args.url:
            return self.url_ipc_handler.handle_url_args(known_args.url)

        return None

    def handle_command_line_args(self, args: list) -> Optional[Dict[str, Any]]:
        """
        处理命令行参数

        Args:
            args: 命令行参数列表

        Returns:
            如果有URL参数则返回解析结果，否则返回None
        """
        for arg in args:
            if arg.startswith("secrandom://"):
                return self.handle_url(arg)
        return None

    def handle_url(self, url: str) -> Dict[str, Any]:
        """
        处理URL

        Args:
            url: URL字符串

        Returns:
            处理结果
        """
        logger.debug(f"URLHandler.handle_url: 处理URL: {url}")

        # 解析URL，获取动作类型
        from urllib.parse import urlparse

        parsed = urlparse(url)

        # 修复URL解析逻辑：对于 secrandom://settings/list 这样的URL，settings 是 netloc，而不是 path 的一部分
        # 我们需要将 netloc 和 path 结合起来，才能得到完整的动作类型
        if parsed.netloc and parsed.path:
            # 这是一个带有 netloc 的URL，如 secrandom://settings/list
            full_path = f"{parsed.netloc}{parsed.path}"
        elif parsed.netloc:
            # 这是一个只有 netloc 的URL，如 secrandom://settings
            full_path = parsed.netloc
        else:
            # 这是一个只有 path 的URL，如 secrandom:///lottery
            full_path = parsed.path

        logger.debug(f"URLHandler.handle_url: 解析URL完整路径: {full_path}")

        # 根据完整路径类型直接发出信号
        if "settings" in full_path:
            # 这是一个设置页面URL，发出 showSettingsRequested 信号
            logger.debug("URLHandler.handle_url: 发出 showSettingsRequested 信号")
        elif "lottery" in full_path:
            # 这是一个抽奖页面URL，发出 showMainPageRequested 信号
            logger.debug(
                "URLHandler.handle_url: 发出 showMainPageRequested 信号，参数: 'lottery_page'"
            )
            self.showMainPageRequested.emit("lottery_page")
        elif "rollcall" in full_path:
            # 这是一个点名页面URL，发出 showMainPageRequested 信号
            logger.debug(
                "URLHandler.handle_url: 发出 showMainPageRequested 信号，参数: 'roll_call_page'"
            )
            self.showMainPageRequested.emit("roll_call_page")

        # 调用 command_handler.handle_url_command(url) 处理URL
        result = self.command_handler.handle_url_command(url)
        logger.debug(f"URLHandler.handle_url: 处理结果: {result}")
        return result

    def handle_url_startup(self, url: str) -> Dict[str, Any]:
        """
        处理URL启动

        Args:
            url: URL字符串

        Returns:
            处理结果
        """
        # 直接使用URLCommandHandler处理URL
        return self.command_handler.handle_url_command(url)

    def check_single_instance(self) -> bool:
        """
        检查单实例

        Returns:
            如果是第一个实例返回True，否则返回False
        """
        # 尝试启动IPC服务器
        # 优先使用用户设置的端口，如果用户设置为0（动态分配）则使用配置文件中的端口
        user_port = readme_settings_async("basic_settings", "ipc_port") or 0
        config_port = self.url_ipc_handler.load_port_config()

        # 如果用户设置了特定端口（非0），则使用用户设置的端口
        # 如果用户设置为0（动态分配），则先尝试使用配置文件中的端口，如果配置文件中没有则使用0
        if user_port != 0:
            port = user_port
        else:
            # 用户设置为0（动态分配），使用配置文件中的端口或0
            port = config_port if config_port is not None else 0

        if self.url_ipc_handler.start_ipc_server(port):
            # 注册消息处理器
            self.url_ipc_handler.register_message_handler(
                "url", self._handle_ipc_url_message
            )
            return True
        else:
            return False

    def _handle_ipc_url_message(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理IPC URL消息
        """
        url = payload.get("url", "")
        if url:
            return self.handle_url_startup(url)
        else:
            return {"success": False, "error": "缺少URL参数"}

    def send_url_to_existing_instance(self, url: str) -> bool:
        """
        发送URL到已存在的实例

        Args:
            url: URL字符串

        Returns:
            发送成功返回True，失败返回False
        """
        port = self.url_ipc_handler.load_port_config()
        if port:
            message = {"type": "url", "payload": {"url": url}}

            response = self.url_ipc_handler.send_ipc_message(port, message)
            return response is not None and response.get("success", False)
        else:
            return False


def handle_url_arguments() -> Optional[Dict[str, Any]]:
    """
    全局函数：处理URL参数

    Returns:
        如果有URL参数则返回处理结果，否则返回None
    """
    url_handler = URLHandler()

    # 解析命令行参数
    result = url_handler.parse_command_line_args()

    if result:
        # 检查是否是单实例
        if url_handler.check_single_instance():
            # 是第一个实例，直接处理URL
            return url_handler.handle_url_startup(result.get("url", ""))
        else:
            # 已有实例运行，发送URL到现有实例
            if url_handler.send_url_to_existing_instance(result.get("url", "")):
                return {
                    "success": True,
                    "message": "URL已发送到现有实例",
                    "url": result.get("url", ""),
                }
            else:
                return {"success": False, "error": "无法连接到现有实例"}

    return None
