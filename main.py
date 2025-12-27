# ==================================================
# 导入库
# ==================================================
import os
import sys
import time

from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *
from PySide6.QtNetwork import *
from qfluentwidgets import *

from loguru import logger

from app.tools.variable import *
from app.tools.path_utils import *
from app.tools.settings_default import *
from app.tools.settings_access import *
from app.Language.obtain_language import *
from app.tools.config import *

# 全局窗口引用（延迟创建）
main_window = None
settings_window = None
float_window = None

# 全局变量，用于存储本地服务器实例
local_server = None

# 全局URL处理器实例
url_handler = None

# 全局更新检查线程实例
update_check_thread = None

# 导入更新相关模块
from app.tools.update_utils import *
from app.tools.config import send_system_notification

# 添加项目根目录到Python路径
project_root = str(get_app_root())
if project_root not in sys.path:
    sys.path.insert(0, project_root)


# ==================================================
# 显示调节
# ==================================================
"""根据设置自动调整DPI缩放模式"""


def configure_dpi_scale():
    """在创建QApplication之前配置DPI缩放模式"""
    # 先设置环境变量，这些必须在QApplication创建之前设置
    try:
        from app.tools.settings_access import readme_settings_async

        dpiScale = readme_settings_async("basic_settings", "dpiScale")
        if dpiScale == "Auto":
            # 自动模式 - 使用PassThrough策略
            QApplication.setHighDpiScaleFactorRoundingPolicy(
                Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
            )
            os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
            logger.debug("DPI缩放已设置为自动模式")
        else:
            # 手动模式 - 禁用自动缩放，使用固定缩放因子
            os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
            os.environ["QT_SCALE_FACTOR"] = str(dpiScale)
            logger.debug(f"DPI缩放已设置为{dpiScale}倍")
    except Exception as e:
        # 如果读取设置失败，使用默认的自动缩放
        logger.warning(f"读取DPI设置失败，使用默认设置: {e}")
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
        os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"


# ==================================================
# 单实例检查相关函数
# ==================================================
def check_single_instance():
    """检查单实例，防止多个程序副本同时运行

    Returns:
        tuple: (QSharedMemory, bool) 共享内存对象和是否为第一个实例
    """
    shared_memory = QSharedMemory(SHARED_MEMORY_KEY)
    if not shared_memory.create(1):
        logger.info("检测到已有 SecRandom 实例正在运行，尝试激活已有实例")
        # 尝试附加到共享内存
        if shared_memory.attach():
            # 尝试通过本地套接字激活已有实例
            try:
                local_socket = QLocalSocket()
                local_socket.connectToServer(SHARED_MEMORY_KEY)
                if local_socket.waitForConnected(1000):
                    # 发送激活窗口的信号
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


def setup_local_server():
    """设置本地服务器，用于接收激活窗口的信号

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
                    # 激活主窗口
                    if main_window:
                        main_window.show()
                        main_window.raise_()
                        main_window.activateWindow()
                        logger.debug(
                            "setup_local_server.handle_new_connection: 已激活主窗口"
                        )
                elif data_str.startswith("url:"):
                    # 处理URL参数
                    url = data_str[4:]  # 移除"url:"前缀
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
                        # 只有在处理主界面相关的URL命令时才激活主窗口
                        # 对于设置页面相关的URL命令，不激活主窗口
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


# ==================================================
# 字体设置相关函数
# ==================================================
def apply_font_settings():
    """应用字体设置 - 优化版本，使用字体管理器异步加载"""
    font_family = readme_settings_async("basic_settings", "font")

    setFontFamilies([font_family])
    QTimer.singleShot(FONT_APPLY_DELAY, lambda: apply_font_to_application(font_family))


def apply_font_to_application(font_family):
    """应用字体设置到整个应用程序，优化版本使用字体管理器

    Args:
        font_family (str): 字体家族名称
    """
    try:
        current_font = QApplication.font()
        app_font = QFont(font_family, current_font.pointSize())
        widgets_updated = 0
        widgets_skipped = 0
        for widget in QApplication.allWidgets():
            if isinstance(widget, QWidget):
                if update_widget_fonts(widget, app_font, font_family):
                    widgets_updated += 1
                else:
                    widgets_skipped += 1
        logger.debug(
            f"已应用字体: {font_family}, 更新了{widgets_updated}个控件字体, 跳过了{widgets_skipped}个已有相同字体的控件"
        )
    except Exception as e:
        logger.error(f"应用字体失败: {e}")


def update_widget_fonts(widget, font, font_family):
    """更新控件及其子控件的字体，优化版本减少内存占用，特别处理ComboBox等控件

    Args:
        widget: 要更新字体的控件
        font: 要应用的字体
        font_family: 目标字体家族名称

    Returns:
        bool: 是否更新了控件的字体
    """
    if widget is None:
        return False

    try:
        if not hasattr(widget, "font") or not hasattr(widget, "setFont"):
            return False
        current_widget_font = widget.font()
        if current_widget_font.family() == font_family:
            updated = False
        else:
            new_font = QFont(font.family(), current_widget_font.pointSize())
            new_font.setBold(current_widget_font.bold())
            new_font.setItalic(current_widget_font.italic())
            widget.setFont(new_font)
            updated = True

        if isinstance(widget, QWidget):
            children = widget.children()
            for child in children:
                if isinstance(child, QWidget):
                    child_updated = update_widget_fonts(child, font, font_family)
                    if child_updated:
                        updated = True
        return updated
    except Exception as e:
        logger.exception("更新控件字体时发生异常: {}", e)
        return False


def start_main_window():
    """创建主窗口实例"""
    global main_window
    try:
        from app.view.main.window import MainWindow

        create_float_window()  # Ensure the global float window is created
        main_window = MainWindow(float_window=float_window)
        # 连接显示设置请求信号，添加验证逻辑
        from app.common.safety.verify_ops import (
            should_require_password,
            require_and_run,
        )

        def handle_show_settings_requested(page_name="basicSettingsInterface"):
            """处理显示设置请求，添加验证逻辑"""
            # 检查是否需要验证
            if should_require_password("open_settings"):
                logger.debug(f"打开设置页面需要验证：{page_name}")

                # 显示验证窗口，带有预览选项
                def on_verified():
                    """验证通过后，正常打开设置页面"""
                    show_settings_window(page_name, is_preview=False)

                def on_preview():
                    """点击预览按钮后，以预览模式打开设置页面"""
                    show_settings_window(page_name, is_preview=True)

                require_and_run(
                    "open_settings", main_window, on_verified, on_preview=on_preview
                )
            else:
                # 不需要验证，直接打开设置页面
                logger.debug(f"打开设置页面无需验证：{page_name}")
                show_settings_window(page_name, is_preview=False)

        main_window.showSettingsRequested.connect(handle_show_settings_requested)
        main_window.showSettingsRequestedAbout.connect(show_settings_window_about)
        main_window.showFloatWindowRequested.connect(show_float_window)

        # 根据设置决定是否启动时显示主窗口
        show_startup_window = readme_settings_async(
            "basic_settings", "show_startup_window"
        )
        if show_startup_window:
            main_window.show()

        # 连接 URLHandler 信号到 main_window 信号处理器
        global url_handler
        if url_handler:
            url_handler.showMainPageRequested.connect(
                main_window._handle_main_page_requested
            )
            url_handler.showTrayActionRequested.connect(
                lambda action: main_window._handle_tray_action_requested(action)
            )

            # 连接 URLHandler 信号到设置窗口显示方法
            url_handler.showSettingsRequested.connect(show_settings_window)

        # 根据设置决定是否启动时显示浮窗
        startup_display_float = readme_settings_async(
            "floating_window_management", "startup_display_floating_window"
        )
        if startup_display_float:
            show_float_window()

        try:
            elapsed = time.perf_counter() - app_start_time
            logger.debug(f"主窗口创建完成，启动耗时: {elapsed:.3f}s")
        except Exception as e:
            logger.exception("计算启动耗时出错（已忽略）: {}", e)
    except Exception as e:
        logger.error(f"创建主窗口失败: {e}", exc_info=True)


def create_settings_window(is_preview=False):
    """创建设置窗口实例

    Args:
        is_preview: 是否为预览模式，默认为 False
    """
    global settings_window
    try:
        from app.view.settings.settings import SettingsWindow

        settings_window = SettingsWindow(is_preview=is_preview)
    except Exception as e:
        logger.error(f"创建设置窗口失败: {e}", exc_info=True)


def show_settings_window(page_name="basicSettingsInterface", is_preview=False):
    """显示设置窗口

    Args:
        page_name: 设置页面名称，默认为 basicSettingsInterface
        is_preview: 是否为预览模式，默认为 False
    """
    try:
        global settings_window
        # 如果已经存在设置窗口，检查其is_preview属性是否与当前请求的一致
        if settings_window is not None:
            # 如果当前设置窗口的预览模式与请求的不一致，销毁并重新创建
            if (
                hasattr(settings_window, "is_preview")
                and settings_window.is_preview != is_preview
            ):
                logger.debug(f"重新创建设置窗口，预览模式: {is_preview}")
                # 关闭并销毁现有窗口
                try:
                    settings_window.close()
                    settings_window.deleteLater()
                except Exception as close_e:
                    logger.error(f"关闭现有设置窗口失败: {close_e}")
                settings_window = None

        # 如果设置窗口不存在，创建新的
        if settings_window is None:
            create_settings_window(is_preview=is_preview)

        if settings_window is not None:
            settings_window.show_settings_window()
            # 处理设置页面跳转
            settings_window._handle_settings_page_request(page_name)
    except Exception as e:
        logger.error(f"显示设置窗口失败: {e}", exc_info=True)


def show_settings_window_about():
    """显示关于窗口"""
    try:
        global settings_window
        if settings_window is None:
            create_settings_window()
        if settings_window is not None:
            settings_window.show_settings_window_about()
    except Exception as e:
        logger.error(f"显示关于窗口失败: {e}", exc_info=True)


def create_float_window():
    """创建浮窗实例"""
    global float_window
    try:
        from app.view.floating_window.levitation import LevitationWindow

        float_window = LevitationWindow()
    except Exception as e:
        logger.error(f"创建浮窗失败: {e}", exc_info=True)


def show_float_window():
    """显示浮窗"""
    try:
        global float_window
        if float_window is None:
            create_float_window()
        if float_window is not None:
            float_window.show()
    except Exception as e:
        logger.error(f"显示浮窗失败: {e}", exc_info=True)


# ==================================================
# 应用程序初始化相关函数
# ==================================================
def check_for_updates_on_startup():
    """
    应用启动时检查更新
    根据自动更新模式设置执行相应的更新操作
    异步执行，避免阻塞应用启动进程
    """

    # 创建一个QThread来执行更新检查，避免阻塞主线程
    class UpdateCheckThread(QThread):
        def run(self):
            try:
                # 读取自动更新模式设置
                auto_update_mode = readme_settings_async("update", "auto_update_mode")
                logger.debug(f"自动更新模式: {auto_update_mode}")

                # 如果是模式0（不自动检查更新），直接返回
                if auto_update_mode == 0:
                    logger.debug("自动更新模式为0，不执行更新检查")
                    return

                # 获取最新版本信息
                logger.debug("开始检查更新")
                latest_version_info = get_latest_version()

                if not latest_version_info:
                    logger.debug("获取最新版本信息失败")
                    return

                latest_version = latest_version_info["version"]
                latest_version_no = latest_version_info["version_no"]

                # 比较版本号
                compare_result = compare_versions(VERSION, latest_version)

                # 获取下载文件夹路径
                download_dir = get_data_path("downloads")
                ensure_dir(download_dir)

                # 构建预期的文件名
                expected_filename = DEFAULT_NAME_FORMAT
                expected_filename = expected_filename.replace(
                    "[version]", latest_version
                )
                expected_filename = expected_filename.replace("[system]", SYSTEM)
                expected_filename = expected_filename.replace("[arch]", ARCH)
                expected_filename = expected_filename.replace("[struct]", STRUCT)
                expected_file_path = download_dir / expected_filename

                # 检查是否有已下载的更新文件（模式3：自动安装）
                if (
                    expected_file_path.exists()
                    and compare_result == 1
                    and auto_update_mode == 3
                ):
                    logger.debug(
                        f"发现已下载的更新文件，开始自动安装: {expected_file_path}"
                    )
                    # 自动安装更新
                    success = install_update(str(expected_file_path))
                    if success:
                        logger.debug("自动安装更新成功")
                    else:
                        logger.error("自动安装更新失败")
                    return

                if compare_result == 1:
                    # 有新版本
                    logger.debug(f"发现新版本: {latest_version}")

                    # 发送系统通知
                    title = get_content_name_async(
                        "update", "update_notification_title"
                    )
                    content = get_content_name_async(
                        "update", "update_notification_content"
                    ).format(version=latest_version)
                    send_system_notification(
                        title, content, url="https://secrandom.netlify.app/download"
                    )

                    # 如果是模式2或3，自动下载更新
                    if auto_update_mode in [2, 3]:
                        logger.debug(
                            f"自动更新模式为{auto_update_mode}，开始自动下载更新"
                        )

                        # 检查文件是否已存在
                        if expected_file_path.exists():
                            logger.debug(
                                f"更新文件已存在，跳过下载: {expected_file_path}"
                            )
                            return

                        # 自动下载更新
                        file_path = download_update(latest_version)
                        if file_path:
                            logger.debug(f"自动下载更新成功: {file_path}")
                        else:
                            logger.error("自动下载更新失败")
                elif compare_result == 0:
                    # 当前是最新版本
                    logger.debug("当前已是最新版本")
                else:
                    # 版本比较失败
                    logger.debug("版本比较失败")
            except Exception as e:
                logger.error(f"启动时检查更新失败: {e}")

    # 启动更新检查线程
    global update_check_thread
    update_check_thread = UpdateCheckThread()
    update_check_thread.start()


def initialize_app():
    """初始化应用程序"""
    # 管理设置文件，确保其存在且完整
    manage_settings_file()

    # 初始化URL处理器
    initialize_url_handler()

    # 加载主题
    QTimer.singleShot(
        APP_INIT_DELAY,
        lambda: (
            # 读取主题设置并安全映射到Theme
            (
                lambda: (
                    setTheme(Theme.DARK)
                    if readme_settings_async("basic_settings", "theme") == "DARK"
                    else (
                        setTheme(Theme.AUTO)
                        if readme_settings_async("basic_settings", "theme") == "AUTO"
                        else setTheme(Theme.LIGHT)
                    )
                )
            )()
        ),
    )

    # 加载主题颜色
    QTimer.singleShot(
        APP_INIT_DELAY,
        lambda: (setThemeColor(readme_settings_async("basic_settings", "theme_color"))),
    )

    # 清除重启记录
    QTimer.singleShot(APP_INIT_DELAY, lambda: (remove_record("", "", "", "restart")))

    # 检查是否需要安装更新
    QTimer.singleShot(APP_INIT_DELAY, lambda: (check_for_updates_on_startup()))

    # 创建主窗口实例（但不自动显示）
    QTimer.singleShot(APP_INIT_DELAY, lambda: (start_main_window()))

    # 应用字体设置
    QTimer.singleShot(APP_INIT_DELAY, lambda: (apply_font_settings()))

    # 记录初始化完成时间
    logger.debug("应用初始化调度已启动，主窗口将在延迟后创建")


def initialize_url_handler():
    """初始化URL处理器"""
    global url_handler
    try:
        from app.tools.url_handler import URLHandler

        # 创建URL处理器实例
        url_handler = URLHandler()

        # 处理命令行参数中的URL
        if len(sys.argv) > 1:
            url_handler.handle_command_line_args(sys.argv[1:])

        logger.debug("URL处理器初始化完成")
    except Exception as e:
        logger.error(f"初始化URL处理器失败: {e}")


# ==================================================
# 主程序入口
# ==================================================
def main_async():
    """主异步函数，用于启动应用程序"""
    QTimer.singleShot(APP_INIT_DELAY, initialize_app)


if __name__ == "__main__":
    program_dir = str(get_app_root())

    # 更改当前工作目录
    if os.getcwd() != program_dir:
        os.chdir(program_dir)
        logger.debug(f"工作目录已设置为: {program_dir}")

    # 配置日志系统
    logger.remove()
    # 首先配置日志系统
    configure_logging()

    # 记录应用启动时间，用于诊断各阶段耗时
    app_start_time = time.perf_counter()

    # 首先进行单实例检查
    shared_memory, is_first_instance = check_single_instance()

    if not is_first_instance:
        # 不是第一个实例，检查是否有URL参数需要处理
        if len(sys.argv) > 1 and any(
            arg.startswith("secrandom://") for arg in sys.argv
        ):
            # 有URL参数，发送到已运行的实例处理
            try:
                local_socket = QLocalSocket()
                local_socket.connectToServer(SHARED_MEMORY_KEY)
                if local_socket.waitForConnected(1000):
                    # 发送URL参数
                    for arg in sys.argv[1:]:
                        if arg.startswith("secrandom://"):
                            local_socket.write(f"url:{arg}".encode("utf-8"))
                            local_socket.flush()
                            local_socket.waitForBytesWritten(1000)
                            logger.debug(f"已发送URL参数到已有实例: {arg}")
                            break
                    local_socket.disconnectFromServer()
            except Exception as e:
                logger.error(f"发送URL参数到已有实例失败: {e}")

        logger.info("程序将退出，已有实例已激活")
        sys.exit(0)

    # 设置本地服务器，用于接收激活窗口的信号
    local_server = setup_local_server()
    if not local_server:
        logger.error("无法启动本地服务器，程序将退出")
        shared_memory.detach()
        sys.exit(1)

    # 在创建QApplication之前配置DPI缩放
    configure_dpi_scale()

    app = QApplication(sys.argv)

    import gc

    gc.enable()  # 开启垃圾回收器

    try:
        resident = readme_settings_async("basic_settings", "background_resident")
        resident = True if resident is None else resident
        app.setQuitOnLastWindowClosed(not resident)
    except Exception:
        app.setQuitOnLastWindowClosed(APP_QUIT_ON_LAST_WINDOW_CLOSED)

    # 解决Dialog和FluentWindow共存时的窗口拉伸问题
    app.setAttribute(Qt.ApplicationAttribute.AA_DontCreateNativeWidgetSiblings)

    try:
        # 初始化应用程序
        main_async()
        app.exec()

        # 程序退出时释放共享内存
        shared_memory.detach()

        # 关闭本地服务器
        if local_server:
            local_server.close()

        # 等待更新检查线程完成
        if update_check_thread and update_check_thread.isRunning():
            logger.debug("等待更新检查线程完成...")
            # 设置一个超时时间，避免无限等待
            update_check_thread.wait(5000)  # 等待5秒
            if update_check_thread.isRunning():
                logger.warning("更新检查线程未在超时时间内完成，强制终止")
                # 注意：QThread没有直接的终止方法，这里主要是确保线程对象被正确引用

        gc.collect()

        sys.exit()
    except Exception as e:
        logger.error(f"应用程序启动失败: {e}")

        # 程序异常退出时释放共享内存
        try:
            shared_memory.detach()
        except Exception as detach_e:
            logger.exception("程序退出时分离共享内存失败: {}", detach_e)
        # 关闭本地服务器
        try:
            if local_server:
                local_server.close()
        except Exception as close_e:
            logger.exception("程序退出时关闭本地服务器失败: {}", close_e)
        # 等待更新检查线程完成（异常退出情况）
        try:
            if update_check_thread and update_check_thread.isRunning():
                logger.debug("等待更新检查线程完成...")
                update_check_thread.wait(5000)  # 等待5秒
        except Exception as thread_e:
            logger.exception("处理更新检查线程时发生错误: {}", thread_e)
        sys.exit(1)
