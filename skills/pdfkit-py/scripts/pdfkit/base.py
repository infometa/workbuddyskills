#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pdfkit lite 基础框架。

所有命令脚本的公共入口，支持两种输入模式：
1. CLI 模式：python3 -m lite compress --input x.pdf --output y.pdf --quality ebook
2. JSON stdin 模式（向后兼容）：echo '{"input":"x.pdf"}' | python3 -m lite.commands.compress

每个命令脚本声明 PARAMS schema，base.main() 自动生成 argparse。
handler 函数签名不变：handler(params: dict) -> dict。
"""

import argparse
import io
import json
import os
import sys
import traceback


# ---------------------------------------------------------------------------
# PARAMS schema → argparse 转换
# ---------------------------------------------------------------------------

_TYPE_MAP = {
    "str": str,
    "int": int,
    "float": float,
    "json": str,  # 先收字符串，后续 json.loads
}


def _build_parser(params_schema, description=""):
    """根据 PARAMS schema 构建 argparse.ArgumentParser。

    Schema 格式::

        [
            {"name": "input",  "type": "str",  "required": True,  "help": "Input PDF"},
            {"name": "quality","type": "str",  "required": False, "default": "ebook",
             "choices": ["screen","ebook","printer","prepress"], "help": "Quality"},
            {"name": "verbose","type": "bool", "required": False, "default": False},
            {"name": "edits",  "type": "json", "required": False, "help": "JSON array"},
        ]

    type 支持: str, int, float, bool (--flag/--no-flag), json (json.loads)
    """
    parser = argparse.ArgumentParser(
        description=description,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # 全局 --config 逃生舱
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="JSON config file; keys are merged with CLI args (CLI takes precedence)",
    )

    for p in params_schema:
        name = p["name"]
        ptype = p.get("type", "str")
        required = p.get("required", False)
        default = p.get("default", None)
        choices = p.get("choices", None)
        help_text = p.get("help", "")

        flag = f"--{name}"

        if ptype == "bool":
            # --flag / --no-flag 对
            parser.add_argument(
                flag,
                action="store_true",
                default=default if default is not None else False,
                help=help_text,
            )
            parser.add_argument(
                f"--no-{name}",
                dest=name,
                action="store_false",
                help=f"Disable {name}",
            )
        else:
            kwargs = {
                "type": _TYPE_MAP.get(ptype, str),
                "default": default,
                "help": help_text,
            }
            if required:
                kwargs["required"] = True
            if choices:
                kwargs["choices"] = choices
            parser.add_argument(flag, **kwargs)

    return parser


def _parse_cli(params_schema, description=""):
    """从 CLI 参数解析出 params dict。

    处理 --config 合并逻辑和 type=json 的后处理。
    """
    parser = _build_parser(params_schema, description)
    args = parser.parse_args()
    params = vars(args)

    # --config 文件合并
    config_path = params.pop("config", None)
    if config_path:
        if not os.path.exists(config_path):
            parser.error(f"Config file not found: {config_path}")
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)
        # config 作为底层，CLI 参数覆盖
        merged = dict(config_data)
        for k, v in params.items():
            if v is not None:
                merged[k] = v
        params = merged

    # type=json 后处理
    json_fields = {p["name"] for p in params_schema if p.get("type") == "json"}
    for field in json_fields:
        val = params.get(field)
        if isinstance(val, str):
            try:
                params[field] = json.loads(val)
            except json.JSONDecodeError as e:
                parser.error(f"Invalid JSON for --{field}: {e}")

    # 清除 None 值（让 handler 可以用 .get() 拿默认值）
    params = {k: v for k, v in params.items() if v is not None}

    return params


def _parse_stdin():
    """从 stdin 读取 JSON 参数（向后兼容模式）。"""
    return json.loads(sys.stdin.read())


# ---------------------------------------------------------------------------
# 公共入口
# ---------------------------------------------------------------------------

def main(handler, params_schema=None, description=""):
    """双模式统一入口。

    - 有 CLI 参数（sys.argv > 1）且有 schema → argparse 解析
    - 否则 → JSON stdin（完全向后兼容）

    输出格式统一为 JSON：
        {"ok": true, "data": ...} 或 {"ok": false, "error": ..., "traceback": ...}

    Args:
        handler: 处理函数，签名 handler(params: dict) -> dict
        params_schema: PARAMS 列表，None 则只走 stdin 模式
        description: 命令描述文本
    """
    # Windows 下 sys.stdout/stdin 默认使用系统编码（如 GBK），遇到 emoji 等字符会报错，
    # 强制切换为 UTF-8 以保证 JSON 输出/输入不会因编码问题失败。
    if sys.platform == "win32":
        try:
            if hasattr(sys.stdout, "reconfigure"):
                sys.stdout.reconfigure(encoding="utf-8")
            elif hasattr(sys.stdout, "buffer"):
                sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        except Exception:
            pass
        try:
            if hasattr(sys.stdin, "reconfigure"):
                sys.stdin.reconfigure(encoding="utf-8")
            elif hasattr(sys.stdin, "buffer"):
                sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8")
        except Exception:
            pass

    # 捕获 stderr（第三方库输出不干扰 JSON 输出）
    _original_stdout = sys.stdout
    _stderr_capture = io.StringIO()
    sys.stderr = _stderr_capture

    def _write_json(obj):
        """将 obj 序列化为 JSON，始终以 UTF-8 字节写入 stdout。
        
        直接操作 stdout.buffer（如存在）可彻底绕过 Windows GBK 编码问题，
        即使 reconfigure 在某些重定向场景下未能生效也能正常输出。
        """
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        out = _original_stdout
        if hasattr(out, "buffer"):
            out.buffer.write(data)
            out.buffer.flush()
        else:
            out.write(data.decode("utf-8"))
            out.flush()

    try:
        # 决定输入模式
        if len(sys.argv) > 1 and params_schema:
            params = _parse_cli(params_schema, description)
        else:
            params = _parse_stdin()

        # 临时重定向 stdout，防止第三方库 print 干扰 JSON
        _capture = io.StringIO()
        sys.stdout = _capture

        result = handler(params)

        sys.stdout = _original_stdout
        _write_json({"ok": True, "data": result})

    except SystemExit as e:
        # argparse 的 --help 或 error 会触发 SystemExit
        sys.stdout = _original_stdout
        sys.stderr = sys.__stderr__
        raise

    except Exception as e:
        sys.stdout = _original_stdout
        stderr_content = _stderr_capture.getvalue()
        error_info = {
            "ok": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
        }
        if stderr_content:
            error_info["stderr"] = stderr_content[-500:]
        _write_json(error_info)

    sys.stdout.flush()
