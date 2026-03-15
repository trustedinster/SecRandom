from app.tools.settings_access import readme_settings_async
from loguru import logger

READONLY_COMMAND_PREFIXES = ("data/",)

OPERATION_SWITCH_MAP = {
    "show_hide_floating_window": "show_hide_floating_window_switch",
    "restart": "restart_switch",
    "exit": "exit_switch",
    "set_totp": "safety_switch",
    "bind_usb": "safety_switch",
    "unbind_usb": "safety_switch",
    "toggle_totp": "safety_switch",
    "toggle_usb": "safety_switch",
    "change_verification_process": "safety_switch",
    "toggle_show_hide_floating_window_switch": "safety_switch",
    "toggle_restart_switch": "safety_switch",
    "toggle_exit_switch": "safety_switch",
    "open_settings": "open_settings_switch",
    "toggle_open_settings_switch": "safety_switch",
    "roll_call_start": "safety_switch",
    "roll_call_reset": "safety_switch",
    "lottery_start": "safety_switch",
    "lottery_reset": "safety_switch",
    "quick_draw": "safety_switch",
}

COMMAND_OPERATION_MAP = {
    "tray/settings": "open_settings",
    "tray/float": "show_hide_floating_window",
    "window/main": None,
    "window/settings": "open_settings",
    "window/float": "show_hide_floating_window",
    "window/timer": None,
    "tray/restart": "restart",
    "tray/exit": "exit",
    "roll_call/quick_draw": "quick_draw",
    "roll_call/start": "roll_call_start",
    "roll_call/reset": "roll_call_reset",
    "lottery/start": "lottery_start",
    "lottery/reset": "lottery_reset",
}


def is_readonly_command(command: str) -> bool:
    return str(command or "").startswith(READONLY_COMMAND_PREFIXES)


def resolve_operation_switch(op: str | None) -> str | None:
    if op is None:
        return None
    return OPERATION_SWITCH_MAP.get(op)


def resolve_operation_for_command(command: str) -> str | None:
    return COMMAND_OPERATION_MAP.get(command)


def should_require_password_for_command(command: str) -> bool:
    if is_readonly_command(command):
        logger.debug(f"命令无需验证（数据只读）：{command}")
        return False

    op = resolve_operation_for_command(command)
    if op is None:
        logger.debug(f"命令无需验证（默认放行）：{command}")
        return False

    return should_require_password(op)


def should_require_password(op: str) -> bool:
    if op != "toggle_safety" and not readme_settings_async(
        "basic_safety_settings", "safety_switch"
    ):
        logger.debug(f"操作无需验证（安全总开关关闭）：{op}")
        return False

    from app.common.safety.password import is_configured as password_is_configured

    if not password_is_configured():
        logger.debug(f"操作无需验证（未配置密码）：{op}")
        return False

    # 特殊处理：切换安全总开关本身需要验证
    if op == "toggle_safety":
        logger.debug(f"操作需验证（切换安全总开关）：{op}")
        return True

    k = resolve_operation_switch(op)
    if not k:
        logger.debug(f"操作需验证（默认受控）：{op}")
        return True
    ok = bool(readme_settings_async("basic_safety_settings", k))
    logger.debug(f"操作需验证：{op} -> {ok}")
    return ok


def require_and_run(op: str, parent, func, on_preview=None):
    if not should_require_password(op):
        func()
        return
    logger.debug(f"触发验证窗口：{op}")
    from app.page_building.security_window import create_verify_password_window

    create_verify_password_window(
        on_verified=func, on_preview=on_preview, operation_type=op
    )
