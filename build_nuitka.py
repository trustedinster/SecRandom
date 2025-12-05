"""Nuitka packaging helper for SecRandom using the shared packaging utilities."""

from __future__ import annotations

import subprocess
import sys
import re
from pathlib import Path

# 设置Windows控制台编码为UTF-8
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

from app.tools.variable import APPLY_NAME, VERSION, APP_DESCRIPTION, AUTHOR, WEBSITE
from packaging_utils_deb import DebBuilder

PACKAGE_INCLUDE_NAMES = {
    "app.Language.modules",
    "app.view",
    "app.tools",
    "app.page_building",
}


def _print_packaging_summary() -> None:
    data_includes = collect_data_includes()
    hidden_names = normalize_hidden_imports(
        collect_language_modules() + collect_view_modules() + ADDITIONAL_HIDDEN_IMPORTS
    )
    package_names = sorted(
        {name for name in hidden_names if "." not in name} | PACKAGE_INCLUDE_NAMES
    )
    module_names = [name for name in hidden_names if "." in name]

    print(f"\nSelected data includes ({len(data_includes)} entries):")
    for item in data_includes:
        kind = "dir " if item.is_dir else "file"
        print(f"  - {kind} {item.source} -> {item.target}")
    print(f"\nRequired packages ({len(package_names)} entries):")
    for pkg in package_names:
        print(f"  - {pkg}")
    print(f"\nHidden modules ({len(module_names)} entries):")
    for mod in module_names:
        print(f"  - {mod}")


def _gather_data_flags() -> list[str]:
    flags: list[str] = []
    for include in collect_data_includes():
        flag = "--include-data-dir" if include.is_dir else "--include-data-file"
        source = include.source
        target = include.target
        # FIX: Nuitka 不允许 file 目标为 "."
        if not include.is_dir and target == ".":
            target = Path(source).name
        flags.append(f"{flag}={source}={target}")
    return flags


def _gather_module_and_package_flags() -> tuple[list[str], list[str]]:
    hidden_names = normalize_hidden_imports(
        collect_language_modules() + collect_view_modules() + ADDITIONAL_HIDDEN_IMPORTS
    )
    package_names = set(PACKAGE_INCLUDE_NAMES)
    module_names: list[str] = []
    for name in hidden_names:
        if "." not in name:
            package_names.add(name)
        else:
            module_names.append(name)
    package_flags = [f"--include-package={pkg}" for pkg in sorted(package_names)]
    module_flags = [f"--include-module={mod}" for mod in module_names]
    return module_flags, package_flags


def _sanitize_version(ver_str: str) -> str:
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


def get_nuitka_command():
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

    # === 编译器选择逻辑 ===
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


def check_compiler_env():
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
    return input("是否继续? (y/n): ").lower() == "y"


def build_deb() -> None:
    if sys.platform != "linux":
        return
    print("\n" + "=" * 60 + "\n开始构建deb包...\n" + "=" * 60)
    try:
        DebBuilder.build_from_nuitka(
            PROJECT_ROOT, APPLY_NAME, VERSION, APP_DESCRIPTION, AUTHOR, WEBSITE
        )
    except Exception as e:
        print(f"构建deb包失败: {e}")
        sys.exit(1)


def main():
    print("=" * 60)
    print(
        f"开始打包 SecRandom (Python {sys.version_info.major}.{sys.version_info.minor} on {sys.platform})"
    )
    print("=" * 60)

    if sys.platform == "win32" and not check_compiler_env():
        sys.exit(1)

    _print_packaging_summary()
    cmd = get_nuitka_command()

    print("\n执行命令:")
    print(" ".join(cmd))
    print("\n" + "=" * 60)

    try:
        # capture_output=False 允许看到实时进度
        subprocess.run(
            cmd,
            check=True,
            cwd=PROJECT_ROOT,
            capture_output=False,
            encoding="utf-8",
            errors="replace",
        )
        print("\n" + "=" * 60 + "\nNuitka打包成功！\n" + "=" * 60)
        build_deb()
    except subprocess.CalledProcessError as e:
        print(f"\n打包失败 (返回码: {e.returncode})")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n用户取消打包")
        sys.exit(1)


if __name__ == "__main__":
    main()
