# ==================================================
# 导入模块
# ==================================================
import yaml
import aiohttp
import asyncio
from typing import Any, Tuple
from loguru import logger
from app.tools.path_utils import *
from app.tools.variable import *
from app.tools.settings_access import readme_settings


# ==================================================
# 辅助函数
# ==================================================
def safe_int(s: str) -> int:
    """安全地将字符串转换为整数

    Args:
        s (str): 要转换的字符串

    Returns:
        int: 转换后的整数，如果转换失败则返回 0
    """
    try:
        return int(s) if s else 0
    except ValueError:
        return 0


def _run_async_func(async_func: Any, *args: Any, **kwargs: Any) -> Any:
    """运行异步函数（同步包装器）

    Args:
        async_func: 要运行的异步函数
        *args: 位置参数
        **kwargs: 关键字参数

    Returns:
        Any: 异步函数的返回值
    """
    try:
        return asyncio.run(async_func(*args, **kwargs))
    except Exception as e:
        logger.error(f"运行异步函数失败: {e}")
        return None


def parse_version(version_str: str) -> Tuple[list[int], list[str]]:
    """解析版本号为数字部分和预发布部分

    Args:
        version_str (str): 版本号字符串，如 "1.2.3" 或 "1.2.3-alpha.1"

    Returns:
        Tuple[list[int], list[str]]: 数字部分和预发布部分的元组
    """
    if "-" in version_str:
        main_version, pre_release = version_str.split("-", 1)
        pre_parts = pre_release.split(".")
    else:
        main_version = version_str
        pre_parts = []

    # 分割主版本号为数字部分
    main_parts = list(map(safe_int, main_version.split(".")))
    return main_parts, pre_parts


# ==================================================
# 更新工具函数
# ==================================================
def get_update_source_url() -> str:
    """
    获取更新源 URL

    Returns:
        str: 更新源 URL，如果获取失败则返回默认值
    """
    try:
        # 从设置中读取更新源
        update_source = readme_settings("update", "update_source")
        source_url = SOURCE_MAP.get(update_source, "https://github.com")
        logger.debug(f"获取更新源 URL 成功: {source_url}")
        return source_url
    except Exception as e:
        logger.error(f"获取更新源 URL 失败: {e}")
        return "https://github.com"


def get_update_check_url() -> str:
    """
    获取更新检查 URL

    Returns:
        str: 更新检查 URL
    """
    source_url = get_update_source_url()
    repo_url = GITHUB_WEB

    # 构建完整的 GitHub URL
    github_raw_url = f"{repo_url}/raw/master/metadata.yaml"

    # 如果是默认源（GitHub），直接返回
    if source_url == "https://github.com":
        update_check_url = github_raw_url
    else:
        # 其他镜像源，在 GitHub URL 前添加镜像源 URL
        update_check_url = f"{source_url}/{github_raw_url}"

    logger.debug(f"生成更新检查 URL 成功: {update_check_url}")
    return update_check_url


async def get_metadata_info_async() -> dict | None:
    """
    异步获取 metadata.yaml 文件信息

    Returns:
        dict: metadata.yaml 文件的内容，如果读取失败则返回 None
    """
    try:
        update_check_url = get_update_check_url()
        logger.debug(f"从网络获取 metadata.yaml: {update_check_url}")

        async with aiohttp.ClientSession() as session:
            async with session.get(update_check_url, timeout=10) as response:
                response.raise_for_status()
                content = await response.text()
                metadata = yaml.safe_load(content)
                logger.debug("成功从网络读取 metadata.yaml 文件")
                return metadata
    except Exception as e:
        logger.error(f"从网络获取 metadata.yaml 文件失败: {e}")
        return None


def get_metadata_info() -> dict | None:
    """
    获取 metadata.yaml 文件信息（同步版本）

    Returns:
        dict: metadata.yaml 文件的内容，如果读取失败则返回 None
    """
    return _run_async_func(get_metadata_info_async)


async def get_latest_version_async(channel: int | None = None) -> dict | None:
    """
    获取最新版本信息（异步版本）

    Args:
        channel (int, optional): 更新通道，默认为 None，此时会从设置中读取
        0: 稳定通道(release), 1: 测试通道(beta), 2: 发布预览通道

    Returns:
        dict: 包含版本号和版本号数字的字典，格式为 {"version": str, "version_no": int}
    """
    try:
        # 如果没有指定通道，从设置中读取
        if channel is None:
            channel = readme_settings("update", "update_channel")

        # 获取 metadata 信息
        metadata = await get_metadata_info_async()
        if not metadata:
            return None

        channel_name = CHANNEL_MAP.get(channel, "release")
        latest = metadata.get("latest", {})
        latest_no = metadata.get("latest_no", {})

        # 获取版本信息，如果通道不存在则使用稳定通道的版本
        version = latest.get(channel_name, latest.get("release", VERSION))
        version_no = latest_no.get(channel_name, latest_no.get("release", 0))

        logger.debug(
            f"获取最新版本信息成功: 通道={channel_name}, 版本={version}, 版本号={version_no}"
        )
        return {"version": version, "version_no": version_no}
    except Exception as e:
        logger.error(f"获取最新版本信息失败: {e}")
        return None


def get_latest_version(channel: int | None = None) -> dict | None:
    """
    获取最新版本信息（同步版本）

    Args:
        channel (int, optional): 更新通道，默认为 None，此时会从设置中读取
        0: 稳定通道(release), 1: 测试通道(beta), 2: 发布预览通道

    Returns:
        dict: 包含版本号和版本号数字的字典，格式为 {"version": str, "version_no": int}
    """
    return _run_async_func(get_latest_version_async, channel)


def compare_versions(current_version: str, latest_version: str) -> int:
    """
    比较版本号，支持语义化版本号格式，包括预发布版本

    Args:
        current_version (str): 当前版本号，格式为 "vX.X.X"、"vX.X.X.X" 或 "vX.X.X-alpha.1" 等
        latest_version (str): 最新版本号，格式为 "vX.X.X"、"vX.X.X.X" 或 "vX.X.X-alpha.1" 等

    Returns:
        int: 1 表示有新版本，0 表示版本相同，-1 表示比较失败
    """
    try:
        # 检查版本号是否为空
        if not current_version or not latest_version:
            logger.error(
                f"比较版本号失败: 版本号为空，current={current_version}, latest={latest_version}"
            )
            return -1

        # 移除版本号前缀 "v"
        current = current_version.lstrip("v")
        latest = latest_version.lstrip("v")

        # 解析两个版本号
        current_main, current_pre = parse_version(current)
        latest_main, latest_pre = parse_version(latest)

        # 比较主版本号部分
        for i in range(max(len(current_main), len(latest_main))):
            current_part = current_main[i] if i < len(current_main) else 0
            latest_part = latest_main[i] if i < len(latest_main) else 0

            if latest_part > current_part:
                return 1
            elif latest_part < current_part:
                return -1

        # 主版本号相同，比较预发布版本
        # 规则：没有预发布标识符的版本 > 有预发布标识符的版本
        if not current_pre and not latest_pre:
            return 0  # 两个都是正式版本，版本号相同
        elif not current_pre:
            return -1  # 当前是正式版本，最新是预发布版本，当前版本更新
        elif not latest_pre:
            return 1  # 当前是预发布版本，最新是正式版本，有新版本

        # 两个都是预发布版本，比较预发布部分
        for i in range(max(len(current_pre), len(latest_pre))):
            if i >= len(current_pre):
                return 1  # 当前预发布部分更短，最新版本更新
            if i >= len(latest_pre):
                return -1  # 最新预发布部分更短，当前版本更新

            current_pre_part = current_pre[i]
            latest_pre_part = latest_pre[i]

            # 尝试转换为整数比较
            try:
                current_pre_int = int(current_pre_part)
                latest_pre_int = int(latest_pre_part)
                if latest_pre_int > current_pre_int:
                    return 1
                elif latest_pre_int < current_pre_int:
                    return -1
            except ValueError:
                # 不是数字，按字典序比较
                if latest_pre_part > current_pre_part:
                    return 1
                elif latest_pre_part < current_pre_part:
                    return -1

        return 0  # 版本号完全相同
    except Exception as e:
        logger.error(f"比较版本号失败: {e}")
        return -1


async def get_update_file_name_async(
    version: str, arch: str = "x64", struct: str = "dir"
) -> str:
    """
    获取更新文件名（异步版本）

    Args:
        version (str): 版本号，格式为 "vX.X.X.X"
        arch (str, optional): 架构，默认为 "x64"
        struct (str, optional): 结构，默认为 "dir"

    Returns:
        str: 更新文件名
    """
    try:
        metadata = await get_metadata_info_async()
        if not metadata:
            # 如果 metadata 读取失败，使用默认格式
            name_format = DEFAULT_NAME_FORMAT
        else:
            name_format = metadata.get("name_format", DEFAULT_NAME_FORMAT)

        # 替换占位符
        file_name = name_format.replace("[version]", version)
        file_name = file_name.replace("[arch]", arch)
        file_name = file_name.replace("[struct]", struct)

        logger.debug(f"生成更新文件名成功: {file_name}")
        return file_name
    except Exception as e:
        logger.error(f"生成更新文件名失败: {e}")
        return f"SecRandom-Windows-{version}-{arch}-{struct}.zip"


def get_update_file_name(version: str, arch: str = "x64", struct: str = "dir") -> str:
    """
    获取更新文件名（同步版本）

    Args:
        version (str): 版本号，格式为 "vX.X.X.X"
        arch (str, optional): 架构，默认为 "x64"
        struct (str, optional): 结构，默认为 "dir"

    Returns:
        str: 更新文件名
    """
    return _run_async_func(get_update_file_name_async, version, arch, struct)
