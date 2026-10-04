#!/usr/bin/env python3
"""受控落盘 LLM 原始响应：stdin → UTF-8 JSON 文件。

存在理由：Windows/WorkBuddy 宿主用 shell 重定向落盘会写入 UTF-16LE BOM，
或把模型响应硬编码进临时脚本转写——两者都破坏「原始响应原样落盘」的物证链。
本脚本把落盘动作收敛到 skill 内：只接受 stdin 传入，拒绝非 UTF-8、
非 JSON、以及 resume 字段含字面量 \\n/\\r（shell 转写特征）的内容。
"""
import json
import sys
from pathlib import Path


def fail(msg: str, code: int = 2):
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(code)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    out = None
    args = sys.argv[1:]
    if len(args) == 2 and args[0] == "--out":
        out = Path(args[1])
    if out is None:
        fail("用法: save_response.py --out <响应文件路径>（响应 JSON 从 stdin 读入）")

    raw = sys.stdin.buffer.read()
    if not raw.strip():
        fail("stdin 为空：请把 LLM 原始响应用管道/重定向传入 stdin")
    if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
        fail("响应是 UTF-16（带 BOM）：不要用 PowerShell `>` 重定向落盘，改经本脚本 stdin 传入")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        fail("响应不是合法 UTF-8：不要用 shell 重定向落盘，改经本脚本 stdin 传入")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        fail(f"响应不是合法 JSON: {exc}")
    if not isinstance(payload, dict):
        fail("响应必须是 JSON 对象")
    resume = payload.get("resume")
    if isinstance(resume, str) and ("\\n" in resume or "\\r" in resume):
        fail("resume 含字面量 \\n/\\r（shell 转写特征）：请将 LLM 原始 JSON 直接经 stdin 传入，禁止手工转写")

    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_name(out.name + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(out)
    print(json.dumps({"ok": True, "path": str(out.resolve())}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
