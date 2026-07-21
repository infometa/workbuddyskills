#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pdfkit lite — 纯 Python PDF 工具箱统一入口。

用法：
    python3 -m lite <command> [args...]
    python3 -m lite --list            # 列出所有命令
    python3 -m lite <command> --help   # 查看命令帮助

示例：
    python3 -m lite compress --input doc.pdf --output out.pdf --quality ebook
    python3 -m lite rotate --input doc.pdf --output out.pdf --angle 90
    python3 -m lite ir_export --input doc.pdf --output ir.json
"""

import importlib
import os
import pkgutil
import sys


def _discover_commands():
    """扫描 lite/commands/ 目录，收集所有命令模块。

    每个命令模块必须暴露：
        - COMMAND: str           — 命令名（用于 CLI 路由）
        - DESCRIPTION: str       — 命令描述
        - PARAMS: list[dict]     — 参数 schema
        - handler(params) -> dict — 处理函数
    """
    commands_dir = os.path.join(os.path.dirname(__file__), "commands")
    commands = {}

    for finder, module_name, is_pkg in pkgutil.iter_modules([commands_dir]):
        if module_name.startswith("_"):
            continue
        try:
            mod = importlib.import_module(f"pdfkit.commands.{module_name}")
            cmd_name = getattr(mod, "COMMAND", module_name)
            commands[cmd_name] = {
                "module": mod,
                "description": getattr(mod, "DESCRIPTION", ""),
                "params": getattr(mod, "PARAMS", []),
                "handler": getattr(mod, "handler", None),
            }
        except Exception as e:
            # 导入失败跳过，不阻塞其他命令
            print(f"[WARN] Failed to load command '{module_name}': {e}", file=sys.stderr)

    return commands


def _print_command_list(commands):
    """打印所有可用命令。"""
    print("pdfkit lite — Available commands:\n")
    # 按类别分组
    categories = {}
    for name, info in sorted(commands.items()):
        mod = info["module"]
        category = getattr(mod, "CATEGORY", "other")
        if category not in categories:
            categories[category] = []
        categories[category].append((name, info["description"]))

    category_labels = {
        "read": "Reading & Analysis",
        "edit": "Editing & Modification",
        "organize": "Organization & Transform",
        "security": "Security & Forms",
        "ir": "PDFLens IR (Intermediate Representation)",
        "meta": "Meta & Utility",
        "other": "Other",
    }

    for cat_key in ["read", "edit", "organize", "security", "ir", "meta", "other"]:
        if cat_key not in categories:
            continue
        label = category_labels.get(cat_key, cat_key)
        print(f"  [{label}]")
        for name, desc in categories[cat_key]:
            print(f"    {name:<28} {desc}")
        print()

    print("Usage: python3 -m lite <command> --help")


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("--help", "-h"):
        commands = _discover_commands()
        _print_command_list(commands)
        sys.exit(0)

    if sys.argv[1] == "--list":
        commands = _discover_commands()
        for name in sorted(commands):
            print(name)
        sys.exit(0)

    cmd_name = sys.argv[1]

    # 尝试导入命令模块（先按模块名，再按 COMMAND 名查找）
    mod = None
    try:
        mod = importlib.import_module(f"pdfkit.commands.{cmd_name}")
    except ModuleNotFoundError:
        # COMMAND 名可能和模块名不同（如 watermark → watermark_enhanced）
        commands = _discover_commands()
        if cmd_name in commands:
            mod = commands[cmd_name]["module"]

    if mod is None:
        print(f"Error: Unknown command '{cmd_name}'", file=sys.stderr)
        print(f"Run 'python3 -m lite --list' to see available commands.", file=sys.stderr)
        sys.exit(1)

    handler_fn = getattr(mod, "handler", None)
    params_schema = getattr(mod, "PARAMS", None)
    description = getattr(mod, "DESCRIPTION", "")

    if handler_fn is None:
        print(f"Error: Command '{cmd_name}' has no handler function.", file=sys.stderr)
        sys.exit(1)

    # 剥掉 argv[0] 和 command name，让 argparse 看到正确的参数
    sys.argv = [f"pdfkit-lite {cmd_name}"] + sys.argv[2:]

    from pdfkit.base import main as base_main
    base_main(handler_fn, params_schema=params_schema, description=description)


if __name__ == "__main__":
    main()
