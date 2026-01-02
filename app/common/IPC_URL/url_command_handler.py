# ==================================================
# URL和IPC命令处理器
# ==================================================
from typing import Dict, Any, Optional, Callable, List
from loguru import logger
from PySide6.QtCore import QObject, Signal


# ==================================================
# 命令处理器类
# ==================================================
class URLCommandHandler(QObject):
    """URL和IPC命令处理器

    处理所有通过URL和IPC发送的命令，包括：
    - 打开设置页面
    - 切换主界面页面
    - 执行托盘功能
    - 安全验证
    """

    # 信号定义
    showSettingsRequested = Signal(str)  # 请求显示设置页面
    showMainPageRequested = Signal(str)  # 请求显示主页面
    showTrayActionRequested = Signal(str)  # 请求执行托盘操作
    securityVerificationRequested = Signal(str, dict)  # 请求安全验证

    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.security_verifier = None

        logger.debug(f"初始化URLCommandHandler - main_window: {main_window}")

        # 定义所有支持的命令映射
        self.command_map = {
            # 设置页面命令
            "settings/basic": self._handle_basic_settings,
            "settings/list": self._handle_list_settings,
            "settings/extraction": self._handle_extraction_settings,
            "settings/floating": self._handle_floating_settings,
            "settings/notification": self._handle_notification_settings,
            "settings/safety": self._handle_safety_settings,
            "settings/custom": self._handle_custom_settings,
            "settings/voice": self._handle_voice_settings,
            "settings/history": self._handle_history_settings,
            "settings/more": self._handle_more_settings,
            "settings/update": self._handle_update_settings,
            "settings/about": self._handle_about_settings,
            "settings": self._handle_settings,
            # 主界面页面命令
            "main/roll": self._handle_roll_call,
            "main/lottery": self._handle_lottery,
            "main": self._handle_main_window,
            # 托盘功能命令
            "tray/toggle": self._handle_tray_toggle,
            "tray/settings": self._handle_tray_settings,
            "tray/float": self._handle_tray_float,
            "tray/restart": self._handle_tray_restart,
            "tray/exit": self._handle_tray_exit,
            # 通用命令
            "open": self._handle_open,
            "action": self._handle_action,
            "verify": self._handle_verify,
        }

        # 需要密码验证的命令列表
        self.secure_commands = [
            "settings/safety",
            "settings/custom",
            "tray/restart",
            "tray/exit",
            "action/secure",
        ]

        # 设置页面映射
        self.settings_page_map = {
            "basic": "basicSettingsInterface",
            "list": "listManagementInterface",
            "extraction": "extractionSettingsInterface",
            "floating": "floatingWindowManagementInterface",
            "notification": "notificationSettingsInterface",
            "safety": "safetySettingsInterface",
            "custom": "customSettingsInterface",
            "voice": "voiceSettingsInterface",
            "history": "historyInterface",
            "more": "moreSettingsInterface",
            "update": "updateInterface",
            "about": "aboutInterface",
        }

        # 主页面映射
        self.main_page_map = {
            "roll": "roll_call_page",
            "lottery": "lottery_page",
        }

        logger.debug("URL命令处理器初始化完成")

    def set_security_verifier(self, verifier):
        """设置安全验证器"""
        self.security_verifier = verifier
        logger.debug("安全验证器已设置")

    def handle_url_command(
        self, url: str, require_verification: bool = True
    ) -> Dict[str, Any]:
        """处理URL命令

        Args:
            url: 完整的URL，如 secrandom://settings/basic
            require_verification: 是否需要验证

        Returns:
            处理结果字典
        """
        logger.debug(f"处理URL命令: {url}")
        try:
            logger.debug(f"收到URL命令: {url}")

            # 解析URL
            command, params = self._parse_url(url)
            logger.debug(f"解析URL命令 - 命令: {command}, 参数: {params}")

            # 检查是否需要验证
            if require_verification and self._requires_verification(command):
                logger.debug(f"命令需要验证: {command}")
                return self._request_verification(command, params)

            # 执行命令
            result = self._execute_command(command, params)
            logger.debug(f"URL命令执行成功: {command}, 结果: {result}")
            return result

        except Exception as e:
            logger.error(f"URL命令处理失败: {e}")
            return {
                "status": "error",
                "message": f"命令处理失败: {str(e)}",
                "command": url,
            }

    def handle_ipc_command(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """处理IPC命令

        Args:
            message: IPC消息字典

        Returns:
            处理结果字典
        """
        try:
            command_type = message.get("type", "")
            payload = message.get("payload", {})

            logger.debug(f"收到IPC命令: {command_type}")

            if command_type == "url":
                url = payload.get("url", "")
                require_verification = payload.get("require_verification", True)
                return self.handle_url_command(url, require_verification)

            elif command_type == "direct":
                command = payload.get("command", "")
                params = payload.get("params", {})
                require_verification = payload.get("require_verification", True)

                if require_verification and self._requires_verification(command):
                    return self._request_verification(command, params)

                return self._execute_command(command, params)

            else:
                return {
                    "status": "error",
                    "message": f"不支持的命令类型: {command_type}",
                }

        except Exception as e:
            logger.error(f"IPC命令处理失败: {e}")
            return {"status": "error", "message": f"IPC命令处理失败: {str(e)}"}

    def _parse_url(self, url: str) -> tuple:
        """解析URL

        Args:
            url: 完整的URL

        Returns:
            (命令, 参数字典) 元组
        """
        logger.debug(f"解析URL: {url}")

        # 移除协议前缀
        if url.startswith("secrandom://"):
            url = url[12:]  # 移除 "secrandom://"

        # 分割命令和参数
        parts = url.split("/")
        command = parts[0] if parts else ""

        # 构建参数
        params = {
            "args": parts[1:] if len(parts) > 1 else [],
            "full_url": f"secrandom://{url}",
        }

        # 解析查询参数
        if "?" in command:
            command, query = command.split("?", 1)
            params["query"] = self._parse_query_string(query)

        logger.debug(f"URL解析结果 - 命令: {command}, 参数: {params}")
        return command, params

    def _parse_query_string(self, query: str) -> Dict[str, Any]:
        """解析查询字符串"""
        logger.debug(f"解析查询字符串: {query}")
        if not query:
            logger.debug("查询字符串为空")
            return {}

        params = {}
        for pair in query.split("&"):
            if "=" in pair:
                key, value = pair.split("=", 1)
                params[key] = value
        logger.debug(f"查询字符串解析结果: {params}")
        return params

    def _requires_verification(self, command: str) -> bool:
        """检查命令是否需要验证"""
        requires = command in self.secure_commands
        logger.debug(f"检查命令是否需要验证 - 命令: {command}, 结果: {requires}")
        return requires or command.startswith("settings/safety")

    def _request_verification(
        self, command: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """请求验证"""
        logger.debug(f"请求验证 - 命令: {command}, 参数: {params}")
        result = {
            "success": False,
            "error": "需要验证",
            "requires_verification": True,
            "command": command,
            "params": params,
            "message": "此命令需要安全验证",
        }
        logger.debug(f"验证请求已发送: {command}")
        # 发送验证请求信号
        self.securityVerificationRequested.emit(command, params)
        return result

    def _execute_command(self, command: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行命令"""
        logger.debug(f"执行命令: {command}, 参数: {params}")
        try:
            # 查找命令处理器
            handler = self.command_map.get(command)
            if handler:
                logger.debug(f"找到命令处理器 - 命令: {command}")
                try:
                    result = handler(params)
                    logger.debug(f"命令执行成功: {command}, 结果: {result}")
                    return result
                except Exception as e:
                    logger.error(f"命令执行失败: {command}, 错误: {e}")
                    return {
                        "status": "error",
                        "message": f"命令执行失败: {str(e)}",
                        "command": command,
                    }

            # 尝试模糊匹配
            matched_command = self._fuzzy_match_command(command)
            if matched_command:
                handler = self.command_map.get(matched_command)
                if handler:
                    logger.debug(f"模糊匹配到命令: {matched_command}")
                    try:
                        result = handler(params)
                        logger.debug(
                            f"模糊匹配命令执行成功: {matched_command}, 结果: {result}"
                        )
                        return result
                    except Exception as e:
                        logger.error(
                            f"模糊匹配命令执行失败: {matched_command}, 错误: {e}"
                        )
                        return {
                            "status": "error",
                            "message": f"命令执行失败: {str(e)}",
                            "command": command,
                        }

            # 未找到匹配命令
            logger.warning(f"未知的命令: {command}")
            return {
                "status": "error",
                "message": f"未知命令: {command}",
                "available_commands": list(self.command_map.keys()),
            }

        except Exception as e:
            logger.error(f"命令执行失败: {e}")
            return {
                "status": "error",
                "message": f"命令执行失败: {str(e)}",
                "command": command,
            }

    def _fuzzy_match_command(self, command: str) -> Optional[str]:
        """模糊匹配命令"""
        logger.debug(f"模糊匹配命令: {command}")
        available_commands = list(self.command_map.keys())

        # 精确匹配
        if command in available_commands:
            logger.debug(f"精确匹配到命令: {command}")
            return command

        # 前缀匹配
        for cmd in available_commands:
            if cmd.startswith(command):
                logger.debug(f"前缀匹配到命令: {cmd} (输入: {command})")
                return cmd

        # 后缀匹配
        for cmd in available_commands:
            if cmd.endswith(command):
                logger.debug(f"后缀匹配到命令: {cmd} (输入: {command})")
                return cmd

        # 包含匹配
        for cmd in available_commands:
            if command in cmd:
                logger.debug(f"包含匹配到命令: {cmd} (输入: {command})")
                return cmd

        logger.debug(f"未匹配到命令: {command}")
        return None

    # ==================================================
    # 具体命令处理器
    # ==================================================

    def _handle_basic_settings(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理基础设置"""
        logger.debug("打开基础设置页面")
        self.showSettingsRequested.emit("basicSettingsInterface")
        return {
            "status": "success",
            "message": "基础设置页面已打开",
            "page": "basicSettingsInterface",
        }

    def _handle_list_settings(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理列表管理设置"""
        logger.debug("打开列表管理设置页面")
        self.showSettingsRequested.emit("listManagementInterface")
        return {
            "status": "success",
            "message": "列表管理设置页面已打开",
            "page": "listManagementInterface",
        }

    def _handle_extraction_settings(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理抽取设置"""
        logger.debug("打开抽取设置页面")
        self.showSettingsRequested.emit("extractionSettingsInterface")
        return {
            "status": "success",
            "message": "抽取设置页面已打开",
            "page": "extractionSettingsInterface",
        }

    def _handle_floating_settings(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理浮窗设置"""
        logger.debug("打开浮窗设置页面")
        self.showSettingsRequested.emit("floatingWindowManagementInterface")
        return {
            "status": "success",
            "message": "浮窗设置页面已打开",
            "page": "floatingWindowManagementInterface",
        }

    def _handle_notification_settings(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理通知设置"""
        logger.debug("打开通知设置页面")
        self.showSettingsRequested.emit("notificationSettingsInterface")
        return {
            "status": "success",
            "message": "通知设置页面已打开",
            "page": "notificationSettingsInterface",
        }

    def _handle_safety_settings(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理安全设置"""
        logger.debug("打开安全设置页面")
        self.showSettingsRequested.emit("safetySettingsInterface")
        return {
            "status": "success",
            "message": "安全设置页面已打开",
            "page": "safetySettingsInterface",
        }

    def _handle_custom_settings(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理自定义设置"""
        logger.debug("打开自定义设置页面")
        self.showSettingsRequested.emit("customSettingsInterface")
        return {
            "status": "success",
            "message": "自定义设置页面已打开",
            "page": "customSettingsInterface",
        }

    def _handle_voice_settings(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理语音设置"""
        logger.debug("打开语音设置页面")
        self.showSettingsRequested.emit("voiceSettingsInterface")
        return {
            "status": "success",
            "message": "语音设置页面已打开",
            "page": "voiceSettingsInterface",
        }

    def _handle_history_settings(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理历史记录设置"""
        logger.debug("打开历史记录设置页面")
        self.showSettingsRequested.emit("historyInterface")
        return {
            "status": "success",
            "message": "历史记录设置页面已打开",
            "page": "historyInterface",
        }

    def _handle_more_settings(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理更多设置"""
        logger.debug("打开更多设置页面")
        self.showSettingsRequested.emit("moreSettingsInterface")
        return {
            "status": "success",
            "message": "更多设置页面已打开",
            "page": "moreSettingsInterface",
        }

    def _handle_update_settings(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理更新设置"""
        logger.debug("打开更新设置页面")
        self.showSettingsRequested.emit("updateInterface")
        return {
            "status": "success",
            "message": "更新设置页面已打开",
            "page": "updateInterface",
        }

    def _handle_about_settings(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理关于设置"""
        logger.debug("打开关于设置页面")
        self.showSettingsRequested.emit("aboutInterface")
        return {
            "status": "success",
            "message": "关于设置页面已打开",
            "page": "aboutInterface",
        }

    def _handle_settings(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理设置命令"""
        args = params.get("args", [])

        # 如果 args 为空或者 args 中的第一个元素为空字符串，默认打开基本设置页面
        if not args or (args and args[0] == ""):
            # 默认打开基本设置页面
            logger.debug("打开设置界面 - 基本设置")
            self.showSettingsRequested.emit("basicSettingsInterface")
            return {"status": "success", "message": "设置界面已打开"}

        # 处理特定的设置页面
        page_name = args[0]
        logger.debug(f"打开设置页面: {page_name}")

        # 映射设置页面名称
        page_mapping = {
            "basic": "basicSettingsInterface",
            "list": "listManagementInterface",
            "extraction": "extractionSettingsInterface",
            "floating": "floatingWindowManagementInterface",
            "notification": "notificationSettingsInterface",
            "safety": "safetySettingsInterface",
            "voice": "voiceSettingsInterface",
            "history": "historyInterface",
            "more": "moreSettingsInterface",
            "update": "updateInterface",
            "about": "aboutInterface",
        }

        if page_name in page_mapping:
            mapped_page = page_mapping[page_name]
            logger.debug(f"切换到设置页面: {mapped_page}")
            self.showSettingsRequested.emit(mapped_page)
            return {
                "status": "success",
                "message": f"设置页面 '{page_name}' 已打开",
                "page": mapped_page,
            }
        else:
            logger.warning(f"未知的设置页面: {page_name}")
            return {
                "status": "error",
                "message": f"不支持的设置页面: {page_name}",
                "available_pages": list(page_mapping.keys()),
            }

    def _handle_roll_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理抽人功能"""
        logger.debug("切换到抽人页面")
        self.showMainPageRequested.emit("roll_call_page")
        return {
            "status": "success",
            "message": "已切换到抽人页面",
            "page": "roll_call_page",
        }

    def _handle_lottery(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理抽奖功能"""
        logger.debug("URLCommandHandler._handle_lottery: 切换到抽奖页面")
        logger.debug(
            "URLCommandHandler._handle_lottery: 发出 showMainPageRequested 信号，参数: 'lottery_page'"
        )
        self.showMainPageRequested.emit("lottery_page")
        return {
            "status": "success",
            "message": "已切换到抽奖页面",
            "page": "lottery_page",
        }

    def _handle_main_window(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理主窗口命令"""
        args = params.get("args", [])
        if args:
            page = args[0]
            if page in self.main_page_map:
                page_name = self.main_page_map[page]
                self.showMainPageRequested.emit(page_name)
                return {
                    "status": "success",
                    "message": f"已切换到{page}页面",
                    "page": page_name,
                }

        # 默认显示主窗口
        self.showMainPageRequested.emit("main_window")
        return {"status": "success", "message": "主窗口已显示", "page": "main_window"}

    def _handle_tray_toggle(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理托盘切换"""
        logger.debug("切换主窗口显示状态")
        self.showTrayActionRequested.emit("toggle_main_window")
        return {"status": "success", "message": "主窗口显示状态已切换"}

    def _handle_tray_settings(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理托盘设置"""
        logger.debug("打开设置界面")
        self.showSettingsRequested.emit("basicSettingsInterface")
        return {"status": "success", "message": "设置界面已打开"}

    def _handle_tray_float(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理托盘浮窗"""
        logger.debug("切换浮窗显示状态")
        self.showTrayActionRequested.emit("toggle_float_window")
        return {"status": "success", "message": "浮窗显示状态已切换"}

    def _handle_tray_restart(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理托盘重启"""
        logger.debug("执行重启操作")
        self.showTrayActionRequested.emit("restart_app")
        return {"status": "success", "message": "应用重启中..."}

    def _handle_tray_exit(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理托盘退出"""
        logger.debug("执行退出操作")
        self.showTrayActionRequested.emit("exit_app")
        return {"status": "success", "message": "应用退出中..."}

    def _handle_open(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理打开命令"""
        args = params.get("args", [])
        if not args:
            return {"status": "error", "message": "缺少打开目标参数"}

        target = args[0]
        logger.debug(f"打开目标: {target}")

        # 根据目标类型路由到相应处理器
        if target in ["settings", "config"]:
            return self._handle_settings({"args": args[1:] if len(args) > 1 else []})
        elif target in ["main", "window"]:
            return self._handle_main_window({"args": args[1:] if len(args) > 1 else []})
        elif target in ["tray", "menu"]:
            return self._handle_tray_toggle(params)
        else:
            return {
                "status": "error",
                "message": f"不支持的打开目标: {target}",
                "available_targets": ["settings", "main", "tray"],
            }

    def _handle_action(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理动作命令"""
        args = params.get("args", [])
        if not args:
            return {"status": "error", "message": "缺少动作类型参数"}

        action_type = args[0]
        logger.debug(f"执行动作: {action_type}")

        # 路由到具体动作
        if action_type == "roll":
            return self._handle_roll_call(params)
        elif action_type == "lottery":
            return self._handle_lottery(params)
        elif action_type == "settings":
            return self._handle_settings({"args": args[1:] if len(args) > 1 else []})
        else:
            return {
                "status": "error",
                "message": f"不支持的动作类型: {action_type}",
                "available_actions": ["roll", "lottery", "settings"],
            }

    def _handle_verify(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理验证命令"""
        # 这里可以实现具体的验证逻辑
        return {"status": "success", "message": "验证通过", "verified": True}

    def register_command(
        self,
        command: str,
        handler: Callable,
        description: str = "",
        require_verification: bool = False,
    ):
        """
        注册自定义命令

        Args:
            command: 命令名称
            handler: 命令处理器函数
            description: 命令描述
            require_verification: 是否需要验证
        """
        logger.debug(
            f"注册自定义命令 - 命令: {command}, 需要验证: {require_verification}"
        )
        self.command_map[command] = handler
        if require_verification:
            self.secure_commands.append(command)
        logger.debug(f"注册自定义命令: {command}")

    def unregister_command(self, command: str):
        """注销自定义命令"""
        logger.debug(f"注销自定义命令: {command}")
        if command in self.command_map:
            del self.command_map[command]
            if command in self.secure_commands:
                self.secure_commands.remove(command)
            logger.debug(f"注销自定义命令: {command}")
        else:
            logger.warning(f"尝试注销不存在的命令: {command}")

    def get_available_commands(self) -> List[Dict[str, Any]]:
        """获取可用命令列表"""
        logger.debug("获取可用命令列表")
        commands = []
        for name, handler in self.command_map.items():
            commands.append(
                {
                    "name": name,
                    "description": getattr(handler, "__doc__", "无描述") or "无描述",
                    "handler": handler.__name__
                    if hasattr(handler, "__name__")
                    else str(handler),
                }
            )
        logger.debug(f"可用命令数量: {len(commands)}")
        return commands

    def verify_and_execute(
        self, command: str, params: Dict[str, Any], verification_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """验证并执行命令"""
        logger.debug(
            f"验证并执行命令 - 命令: {command}, 参数: {params}, 验证数据: {verification_data}"
        )

        if not self.security_verifier:
            logger.error("安全验证器未配置")
            return {"success": False, "error": "安全验证器未配置"}

        # 执行安全验证
        logger.debug("执行安全验证")
        verification_result = self.security_verifier.verify(verification_data)
        if not verification_result["success"]:
            logger.warning(f"安全验证失败: {verification_result}")
            return verification_result

        logger.debug("安全验证通过，执行命令")
        # 执行命令
        result = self._execute_command(command, params)
        logger.debug(f"验证并执行命令完成 - 命令: {command}, 结果: {result}")
        return result
