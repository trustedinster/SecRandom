import sys
from loguru import logger


def create_url_handler():
    """创建URL处理器实例

    Returns:
        URLHandler: URL处理器实例，如果创建失败返回None
    """
    try:
        from app.tools.url_handler import URLHandler

        url_handler = URLHandler()

        if len(sys.argv) > 1:
            url_handler.handle_command_line_args(sys.argv[1:])

        logger.debug("URL处理器初始化完成")
        return url_handler
    except Exception as e:
        logger.error(f"初始化URL处理器失败: {e}")
        return None
