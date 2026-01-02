from typing import Tuple, Optional
from PySide6.QtCore import QSharedMemory
from PySide6.QtNetwork import QLocalSocket, QLocalServer
from loguru import logger

from app.tools.variable import SHARED_MEMORY_KEY


def check_single_instance() -> Tuple[QSharedMemory, bool]:
    """检查单实例，防止多个程序副本同时运行

    Returns:
        tuple: (QSharedMemory, bool) 共享内存对象和是否为第一个实例
    """
    shared_memory = QSharedMemory(SHARED_MEMORY_KEY)
    if not shared_memory.create(1):
        logger.info("检测到已有 SecRandom 实例正在运行，尝试激活已有实例")
        if shared_memory.attach():
            try:
                local_socket = QLocalSocket()
                local_socket.connectToServer(SHARED_MEMORY_KEY)
                if local_socket.waitForConnected(1000):
                    local_socket.write(b"activate")
                    local_socket.flush()
                    local_socket.waitForBytesWritten(1000)
                    logger.info("已发送激活信号到已有实例")
                local_socket.disconnectFromServer()
            except Exception as e:
                logger.error(f"激活已有实例失败: {e}")
            finally:
                return shared_memory, False
        else:
            logger.error("无法附加到共享内存")
            return shared_memory, False

    logger.info("单实例检查通过，可以安全启动程序")
    return shared_memory, True


def setup_local_server(
    main_window, float_window, url_handler
) -> Optional[QLocalServer]:
    """设置本地服务器，用于接收激活窗口的信号

    Args:
        main_window: 主窗口实例
        float_window: 浮窗实例
        url_handler: URL处理器实例

    Returns:
        QLocalServer: 本地服务器对象
    """
    server = QLocalServer()
    if not server.listen(SHARED_MEMORY_KEY):
        logger.error(f"无法启动本地服务器: {server.errorString()}")
        return None

    def handle_new_connection():
        """处理新的连接请求"""
        logger.debug("setup_local_server.handle_new_connection: 收到新的连接请求")
        socket = server.nextPendingConnection()
        if socket:
            if socket.waitForReadyRead(1000):
                data = socket.readAll()
                data_str = (
                    data.data().decode("utf-8")
                    if isinstance(data.data(), bytes)
                    else str(data.data())
                )
                logger.debug(
                    f"setup_local_server.handle_new_connection: 收到数据: {data_str}"
                )

                if data == b"activate":
                    if main_window:
                        main_window.show()
                        main_window.raise_()
                        main_window.activateWindow()
                        logger.debug(
                            "setup_local_server.handle_new_connection: 已激活主窗口"
                        )
                elif data_str.startswith("url:"):
                    url = data_str[4:]
                    logger.debug(
                        f"setup_local_server.handle_new_connection: 收到URL参数: {url}"
                    )
                    if url_handler:
                        logger.debug(
                            "setup_local_server.handle_new_connection: 调用 url_handler.handle_url(url)"
                        )
                        result = url_handler.handle_url(url)
                        logger.debug(
                            f"setup_local_server.handle_new_connection: url_handler.handle_url(url) 结果: {result}"
                        )
                        if main_window and "settings" not in url:
                            main_window.show()
                            main_window.raise_()
                            main_window.activateWindow()
                            logger.debug(
                                "setup_local_server.handle_new_connection: 已激活主窗口"
                            )
                else:
                    logger.warning(
                        f"setup_local_server.handle_new_connection: 未知的数据类型: {data_str}"
                    )
            socket.disconnectFromServer()

    server.newConnection.connect(handle_new_connection)
    logger.debug("setup_local_server: 本地服务器已启动，等待激活信号")
    return server


def send_url_to_existing_instance(url: str) -> bool:
    """向已运行的实例发送URL参数

    Args:
        url: 要发送的URL

    Returns:
        bool: 是否发送成功
    """
    try:
        local_socket = QLocalSocket()
        local_socket.connectToServer(SHARED_MEMORY_KEY)
        if local_socket.waitForConnected(1000):
            local_socket.write(f"url:{url}".encode("utf-8"))
            local_socket.flush()
            local_socket.waitForBytesWritten(1000)
            logger.debug(f"已发送URL参数到已有实例: {url}")
            local_socket.disconnectFromServer()
            return True
    except Exception as e:
        logger.error(f"发送URL参数到已有实例失败: {e}")
    return False
