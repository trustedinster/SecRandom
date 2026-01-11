"""
Nuitka 打包脚本 (重构版)
参考 build_pyinstaller.py 的结构，修复 Nuitka 崩溃问题
"""

import subprocess
import sys
import re
from pathlib import Path

# 设置控制台编码为UTF-8
if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

from packaging_utils import (
    ADDITIONAL_HIDDEN_IMPORTS,
    ICON_FILE,
    PROJECT_ROOT,
    collect_data_includes,
    collect_language_modules,
    collect_view_modules,
    normalize_hidden_imports,
)

# 导入项目配置信息
sys.path.insert(0, str(Path(__file__).parent))
from app.tools.variable import APPLY_NAME, VERSION, APP_DESCRIPTION, AUTHOR, WEBSITE

# 导入deb包构建工具
from packaging_utils_deb import DebBuilder

# 需要确保作为整体包含的包
PACKAGE_INCLUDE_NAMES = {
    "app.Language.modules",
    "app.view",
    "app.tools",
    "app.page_building",
}


def _print_packaging_summary() -> None:
    """Log a quick overview of the data and modules that will be bundled."""

    data_includes = collect_data_includes()
    hidden_imports = normalize_hidden_imports(
        collect_language_modules() + collect_view_modules() + ADDITIONAL_HIDDEN_IMPORTS
    )

    print("\nSelected data includes ({} entries):".format(len(data_includes)))
    for item in data_includes:
        kind = "dir " if item.is_dir else "file"
        print(f"  - {kind} {item.source} -> {item.target}")

    print("\nHidden imports ({} modules):".format(len(hidden_imports)))
    for name in hidden_imports:
        print(f"  - {name}")


def _check_module_exists(name: str) -> bool:
    """
    检查模块或包在文件系统中是否存在。
    这是为了防止 Nuitka 因打包配置中引用了不存在的模块而崩溃。
    """
    path = name.replace('.', '/')
    # 检查是否为模块文件
    if (PROJECT_ROOT / f"{path}.py").exists():
        return True
    # 检查是否为包
    if (PROJECT_ROOT / path / "__init__.py").exists():
        return True
    return False


def _gather_data_flags() -> list[str]:
    """收集数据文件包含标志，过滤掉纯Python代码目录"""
    flags: list[str] = []
    
    # 获取语言模块目录路径，用于过滤
    # packaging_utils 中将此目录作为 data include，但对 Nuitka 来说这是代码
    language_modules_dir = PROJECT_ROOT / "app" / "Language" / "modules"
    
    for include in collect_data_includes():
        # 修复：如果路径是 app/Language/modules，跳过数据包含
        # 因为它是Python代码包，应该通过 --include-package 包含，而不是作为数据文件
        if include.source == language_modules_dir:
            print(f"Info: Skipping data include for Python package directory: {include.source}")
            continue

        flag = "--include-data-dir" if include.is_dir else "--include-data-file"
        source = include.source
        target = include.target
        # FIX: Nuitka 不允许 file 目标为 "."
        if not include.is_dir and target == ".":
            target = Path(source).name
        flags.append(f"{flag}={source}={target}")
    return flags


def _gather_module_and_package_flags() -> tuple[list[str], list[str]]:
    """收集模块和包包含标志，并进行有效性检查"""
    hidden_names = normalize_hidden_imports(
        collect_language_modules() + collect_view_modules() + ADDITIONAL_HIDDEN_IMPORTS
    )
    
    package_names = set(PACKAGE_INCLUDE_NAMES)
    module_names: list[str] = []
    
    for name in hidden_names:
        # 关键修复：验证模块是否存在，防止 Nuitka 报错退出
        if not _check_module_exists(name):
            print(f"Warning: Skipping non-existent module/package '{name}' (Nuitka requires it to exist)")
            continue
        
        if "." not in name:
            package_names.add(name)
        else:
            module_names.append(name)
            
    package_flags = [f"--include-package={pkg}" for pkg in sorted(package_names)]
    module_flags = [f"--include-module={mod}" for mod in module_names]
    return module_flags, package_flags


def _sanitize_version(ver_str: str) -> str:
    """清理版本字符串，确保符合Nuitka要求"""
    if not ver_str:
        return "0.0.0.0"
    ver_str = ver_str.lstrip("vV").strip()
    match = re.match(r"^(\d+(\.\d+)*)", ver_str)
    if match:
        clean_ver = match.group(1)
        if "." not in clean_ver:
            clean_ver += ".0"
        return clean_ver
    return "0.0.0.0"


def get_nuitka_command() -> list[str]:
    """获取Nuitka命令列表"""
    raw_version = VERSION if VERSION else "0.0.0"
    clean_version = _sanitize_version(raw_version)
    print(f"\n版本号处理: '{raw_version}' -> '{clean_version}'")

    module_flags, package_flags = _gather_module_and_package_flags()

    cmd = [
        "uv",
        "run",
        "-m",
        "nuitka",
        "--standalone",
        "--onefile",
        "--enable-plugin=pyside6",
        "--assume-yes-for-downloads",
        "--output-dir=dist",
        "--product-name=SecRandom",
        "--file-description=公平随机抽取系统",
        f"--product-version={clean_version}",
        f"--file-version={clean_version}",
        "--copyright=Copyright (c) 2025",
        "--no-deployment-flag=self-execution",
    ]

    # 编译器选择逻辑
    if sys.platform == "win32":
        # 检测是否为 Python 3.13 及以上
        if sys.version_info >= (3, 13):
            print("\n[注意] 检测到 Python 3.13+")
            print("       Nuitka 暂不支持在此版本使用 MinGW64。")
            print(
                "       将自动切换为 MSVC (Visual Studio)。请确保已安装 C++ 生成工具。"
            )
            cmd.append("--msvc=latest")
        else:
            # Python 3.12 及以下使用 MinGW64
            cmd.append("--mingw64")
    else:
        cmd.append("--linux-onefile-icon")

    cmd.extend(_gather_data_flags())
    cmd.extend(package_flags)
    cmd.extend(module_flags)

    if sys.platform == "win32" and ICON_FILE.exists():
        cmd.append(f"--windows-icon-from-ico={ICON_FILE}")
    elif sys.platform == "linux" and ICON_FILE.exists():
        cmd.append(f"--linux-icon={ICON_FILE}")

    cmd.append("main.py")
    return cmd


def check_compiler_env() -> bool:
    """检查编译器环境"""
    if sys.platform != "win32":
        return True

    # 如果是 Python 3.13+，需要检查 MSVC（这里简单略过，交给 Nuitka 报错，因为检测 MSVC 比较复杂）
    if sys.version_info >= (3, 13):
        return True

    # 如果是 Python < 3.13，检查 MinGW64
    print("\n检查 MinGW64 环境...")
    try:
        result = subprocess.run(
            ["gcc", "--version"],
            capture_output=True,
            text=True,
            check=False,
            encoding="utf-8",
            errors="replace",
        )
        if result.returncode == 0:
            print(
                f"✓ 找到 GCC: {result.stdout.splitlines()[0] if result.stdout else 'Unknown'}"
            )
            return True
    except FileNotFoundError:
        pass

    # 简单检查路径
    common_paths = [
        r"C:\msys64\mingw64\bin",
        r"C:\mingw64\bin",
        r"C:\Program Files\mingw64\bin",
    ]
    for path in common_paths:
        if (Path(path) / "gcc.exe").exists():
            print(f"✓ 找到 MinGW64: {path}")
            return True

    print("⚠ 警告: 未找到 MinGW64，Nuitka 可能会尝试自动下载。")
    # 在 CI 环境下通常不需要交互，直接返回 True 或 False 取决于策略
    # 这里为了兼容 CI，若交互不可用则直接 True，依赖 Nuitka 自行处理或失败
    return True


def build_deb() -> None:
    """构建deb包"""
    if sys.platform != "linux":
        return

    print("\n" + "=" * 60)
    print("开始构建deb包...")
    print("=" * 60)

    try:
        DebBuilder.build_from_nuitka(
            PROJECT_ROOT, APPLY_NAME, VERSION, APP_DESCRIPTION, AUTHOR, WEBSITE
        )
        print("=" * 60)

    except Exception as e:
        print(f"构建deb包失败: {e}")
        sys.exit(1)


def main():
    """执行 Nuitka 打包"""
    print("=" * 60)
    print("开始使用 Nuitka + uv 打包 SecRandom")
    print("=" * 60)

    if sys.platform == "win32" and not check_compiler_env():
        sys.exit(1)

    _print_packaging_summary()
    cmd = get_nuitka_command()

    # 打印命令
    print("\n执行命令:")
    print(" ".join(cmd))
    print("\n" + "=" * 60)

    # 执行打包
    try:
        subprocess.run(
            cmd,
            check=True,
            cwd=PROJECT_ROOT,
            capture_output=False, # 改为 False 以便在 CI/本地看到实时输出
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        print("\n" + "=" * 60)
        print("Nuitka打包成功！")
        print("=" * 60)

        # 构建deb包（仅在Linux平台）
        build_deb()

    except subprocess.CalledProcessError as e:
        print("\n" + "=" * 60)
        print(f"打包失败: {e}")
        print(f"返回码: {e.returncode}")
        print("=" * 60)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n" + "=" * 60)
        print("用户取消打包")
        print("=" * 60)
        sys.exit(1)
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"发生意外错误: {e}")
        import traceback

        traceback.print_exc()
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
