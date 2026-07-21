#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pdfkit — 纯 Python PDF 工具箱统一入口。

用法：
    python3 pdfkit.py help                     # 列出所有命令
    python3 pdfkit.py <command> help            # 查看命令详细帮助
    python3 pdfkit.py <command> --arg value     # 执行命令

示例：
    python3 pdfkit.py compress --input doc.pdf --output out.pdf --quality ebook
    python3 pdfkit.py ir_export --input doc.pdf --output structure.json
"""

import importlib
import importlib.util
import os
import pkgutil
import sys

# 确保 pdfkit.py 所在目录在 Python 路径中
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

# 激活 venv（如果存在，与 pdfkit.py 同目录下的 venv/）
# Windows: venv/Lib/site-packages
# macOS/Linux: venv/lib/pythonX.Y/site-packages
_VENV_DIR = os.path.join(_SCRIPT_DIR, "venv")
if os.path.isdir(_VENV_DIR):
    # Windows 结构: venv/Lib/site-packages
    _sp_win = os.path.join(_VENV_DIR, "Lib", "site-packages")
    if os.path.isdir(_sp_win) and _sp_win not in sys.path:
        sys.path.insert(0, _sp_win)
    # macOS/Linux 结构: venv/lib/pythonX.Y/site-packages
    _venv_lib = os.path.join(_VENV_DIR, "lib")
    if os.path.isdir(_venv_lib):
        for _d in os.listdir(_venv_lib):
            _sp = os.path.join(_venv_lib, _d, "site-packages")
            if os.path.isdir(_sp) and _sp not in sys.path:
                sys.path.insert(0, _sp)


def _get_extension_dir():
    """返回扩展脚本目录路径：与 skill basedir 同级的 pdfkit-extension/scripts/
    
    例如 skill basedir 为 /path/to/pdfkit-py/，则扩展目录为 /path/to/pdfkit-extension/scripts/
    _SCRIPT_DIR = pdfkit-py/scripts/  →  ../.. = pdfkit-py 的父目录
    """
    return os.path.normpath(os.path.join(_SCRIPT_DIR, "..", "..", "pdfkit-extension", "scripts"))


def _discover_extensions():
    """扫描 ../pdfkit-extension/scripts/ 目录，收集扩展命令。

    扩展脚本与内置命令遵循相同的接口约定（COMMAND, DESCRIPTION, PARAMS, handler）。
    扩展命令会带上 'extension' 标记以便区分来源。
    """
    ext_dir = _get_extension_dir()
    extensions = {}

    if not os.path.isdir(ext_dir):
        return extensions

    for fname in sorted(os.listdir(ext_dir)):
        if not fname.endswith(".py") or fname.startswith("_"):
            continue
        module_name = fname[:-3]
        fpath = os.path.join(ext_dir, fname)
        try:
            spec = importlib.util.spec_from_file_location(
                f"pdfkit_ext.{module_name}", fpath
            )
            if spec is None or spec.loader is None:
                print(f"[WARN] Cannot load extension '{fname}': invalid module spec", file=sys.stderr)
                continue
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            cmd_name = getattr(mod, "COMMAND", module_name)
            extensions[cmd_name] = {
                "module": mod,
                "module_name": module_name,
                "description": getattr(mod, "DESCRIPTION", ""),
                "params": getattr(mod, "PARAMS", []),
                "handler": getattr(mod, "handler", None),
                "is_extension": True,
                "source_file": fpath,
            }
        except Exception as e:
            print(f"[WARN] Failed to load extension '{fname}': {e}", file=sys.stderr)

    return extensions


def _discover_commands():
    """扫描 pdfkit/commands/ 目录，收集所有命令模块。"""
    commands_dir = os.path.join(_SCRIPT_DIR, "pdfkit", "commands")
    commands = {}

    for finder, module_name, is_pkg in pkgutil.iter_modules([commands_dir]):
        if module_name.startswith("_"):
            continue
        try:
            mod = importlib.import_module(f"pdfkit.commands.{module_name}")
            cmd_name = getattr(mod, "COMMAND", module_name)
            commands[cmd_name] = {
                "module": mod,
                "module_name": module_name,
                "description": getattr(mod, "DESCRIPTION", ""),
                "params": getattr(mod, "PARAMS", []),
                "handler": getattr(mod, "handler", None),
            }
        except Exception as e:
            print(f"[WARN] Failed to load command '{module_name}': {e}", file=sys.stderr)

    return commands


def _print_help(commands, extensions=None):
    """打印所有可用命令列表。"""
    category_labels = {
        "read": "Reading & Analysis",
        "edit": "Editing & Modification",
        "organize": "Organization & Transform",
        "security": "Security & Forms",
        "ir": "IR (Intermediate Representation)",
        "meta": "Meta & Utility",
        "other": "Other",
    }

    categories = {}
    for name, info in sorted(commands.items()):
        mod = info["module"]
        cat = getattr(mod, "CATEGORY", "other")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append((name, info["description"]))

    total = sum(len(v) for v in categories.values())
    ext_count = len(extensions) if extensions else 0
    print(f"pdfkit — Pure Python PDF Toolkit ({total} built-in + {ext_count} extension commands)\n")

    for cat_key in ["read", "edit", "organize", "security", "ir", "meta", "other"]:
        if cat_key not in categories:
            continue
        label = category_labels.get(cat_key, cat_key)
        print(f"  [{label}]")
        for name, desc in categories[cat_key]:
            print(f"    {name:<28} {desc}")
        print()

    # 显示扩展命令
    if extensions:
        print(f"  [Extensions ({ext_count})]")
        for name, info in sorted(extensions.items()):
            print(f"    {name:<28} {info['description']}")
        print()
    else:
        ext_dir = _get_extension_dir()
        print(f"  [Extensions]")
        print(f"    (none) — create scripts in {ext_dir}")
        print()

    print("Usage:")
    print("  python3 pdfkit.py <command> --arg value")
    print("  python3 pdfkit.py <command> help        # show command help")
    print("  python3 pdfkit.py extension --help      # show extension commands")


def _print_command_help(mod, cmd_name):
    """打印单个命令的详细帮助信息。"""
    from pdfkit.base import _build_parser
    params = getattr(mod, "PARAMS", [])
    desc = getattr(mod, "DESCRIPTION", "")
    parser = _build_parser(params, description=desc)
    # 修改 prog 显示
    parser.prog = f"python3 pdfkit.py {cmd_name}"
    parser.print_help()


def _print_extensions_help(extensions):
    """打印扩展命令的帮助信息。"""
    ext_dir = _get_extension_dir()
    print(f"pdfkit extensions — User-defined PDF scripts\n")
    print(f"  Extension directory: {ext_dir}\n")

    if extensions:
        print(f"  Available extension commands ({len(extensions)}):\n")
        for name, info in sorted(extensions.items()):
            print(f"    {name:<28} {info['description']}")
        print()
    else:
        print("  No extension scripts found.\n")
        print("  To create one, add a .py script to:")
        print(f"    {ext_dir}")
        print("  (must export COMMAND, DESCRIPTION, PARAMS, handler)")
        print()

    print("Usage:")
    print("  python3 pdfkit.py extension --help                   # this help")
    print("  python3 pdfkit.py <ext_command> help                 # extension command help")
    print("  python3 pdfkit.py <ext_command> --arg value          # run extension command")


def main():
    extensions = _discover_extensions()

    if len(sys.argv) < 2 or sys.argv[1] in ("help", "--help", "-h"):
        commands = _discover_commands()
        _print_help(commands, extensions)
        sys.exit(0)

    if sys.argv[1] == "--list":
        commands = _discover_commands()
        for name in sorted(commands):
            print(name)
        for name in sorted(extensions):
            print(f"{name}  (extension)")
        sys.exit(0)

    cmd_name = sys.argv[1]

    # extension 子命令：列出所有扩展
    if cmd_name == "extension":
        if len(sys.argv) >= 3 and sys.argv[2] not in ("help", "--help", "-h"):
            # pdfkit.py extension <ext_cmd> ... → 转发到扩展命令
            cmd_name = sys.argv[2]
            sys.argv = [sys.argv[0]] + sys.argv[2:]
        else:
            _print_extensions_help(extensions)
            sys.exit(0)

    # 查找命令模块（先内置，再扩展）
    mod = None
    is_extension = False
    try:
        mod = importlib.import_module(f"pdfkit.commands.{cmd_name}")
    except ModuleNotFoundError:
        commands = _discover_commands()
        if cmd_name in commands:
            mod = commands[cmd_name]["module"]

    # 内置未找到，查找扩展
    if mod is None and cmd_name in extensions:
        mod = extensions[cmd_name]["module"]
        is_extension = True

    if mod is None:
        print(f"Error: Unknown command '{cmd_name}'", file=sys.stderr)
        print(f"Run 'python3 pdfkit.py help' to see available commands.", file=sys.stderr)
        if not extensions:
            ext_dir = _get_extension_dir()
            print(f"Tip: You can create extension scripts in {ext_dir}", file=sys.stderr)
        sys.exit(1)

    actual_cmd = getattr(mod, "COMMAND", cmd_name)

    # pdfkit.py <command> help
    if len(sys.argv) >= 3 and sys.argv[2] in ("help", "--help", "-h"):
        _print_command_help(mod, actual_cmd)
        sys.exit(0)

    handler_fn = getattr(mod, "handler", None)
    params_schema = getattr(mod, "PARAMS", None)
    description = getattr(mod, "DESCRIPTION", "")

    if handler_fn is None:
        print(f"Error: Command '{cmd_name}' has no handler function.", file=sys.stderr)
        sys.exit(1)

    # 剥掉 pdfkit.py 和 command name，让 argparse 看到正确的参数
    sys.argv = [f"pdfkit.py {actual_cmd}"] + sys.argv[2:]

    from pdfkit.base import main as base_main
    base_main(handler_fn, params_schema=params_schema, description=description)


if __name__ == "__main__":
    main()
