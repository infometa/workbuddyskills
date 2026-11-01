#!/usr/bin/env python3
"""把「文档 / 表格类」取数工具的响应信封落成 CSV 或 JSON。

MCP 工具只出数据、不落盘。本脚本消费工具返回的**统一信封**
`{ok, data, error, meta}`，按 `data` 段的形状落盘：

    二维表（data 里有 rows）              → {工具名}_{时间戳}.csv（UTF-8 带 BOM）
    非表结构（标量 / 文本 / 取文件 kind）  → {工具名}_{时间戳}.json

输入优先从**文件路径**读，也支持 stdin（路径写 `-` 或省略）。

落盘纪律（三条红线）：
  - `missing_fields` **绝不丢弃**：写进 CSV 首行 `#` 注释 + 同名 `.meta.json` 旁注，
    并在 stderr 提示；**绝不用 0 或空串去填缺失列**。
  - `null` 一律写**空单元格**（JSON 模式写 `null`），**绝不补 0**。
  - CSV 一律 **UTF-8 带 BOM（utf-8-sig）**：中文金融表不带 BOM 时 Excel 打开会乱码。

输出约定：成功时 **stdout 只打印产物绝对路径**；其余说明（缺列、降级、JSON 回退、
自动重命名）一律走 stderr。失败给**可行动的一行错误**（不抛裸栈）。

只用标准库（csv / json / os / sys / argparse / datetime），不引入任何第三方依赖。
"""
from __future__ import annotations

import argparse
import csv
import datetime
import json
import os
import sys

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.append(_SCRIPT_DIR)

from utils import (  # noqa: E402
    default_skill_output_dir,
    ensure_inside,
    sanitize_filename,
    unique_path,
)

# 默认落盘目录（技能工作目录下的子目录）与工具名兜底。
DEFAULT_SUBDIR = "yj_fin_data"
DEFAULT_TOOL_STEM = "fin_data"
TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"
SIDECAR_SUFFIX = ".meta.json"

EXAMPLES = """\
示例：
  # 主路径：把已保存的工具响应信封落盘（stdout 只打印产物绝对路径）
  python3 scripts/to_csv.py /tmp/quote_daily_response.json

  # 也支持从 stdin 读（例如接管道）
  cat /tmp/financial_income_response.json | python3 scripts/to_csv.py -

  # 覆盖输出目录 / 覆盖工具名 / 强制 JSON
  python3 scripts/to_csv.py resp.json --out-dir ./out --tool quote_daily --format json
"""


class ToCsvError(Exception):
    """可行动的用户级错误（不抛裸栈，直接给处置建议）。"""


# ------------------------------------------------------------------ 读入与解析 ----

def read_input(path: str) -> str:
    """读入信封原文：路径为空或 `-` 时读 stdin。"""
    if not path or path == "-":
        try:
            return sys.stdin.read()
        except OSError as e:  # pragma: no cover - 平台相关
            raise ToCsvError(f"读取 stdin 失败：{e}")

    expanded = os.path.expanduser(path)
    if not os.path.isfile(expanded):
        raise ToCsvError(f"输入文件不存在：{path}")
    try:
        # utf-8-sig：容忍编辑器写出的 BOM，避免首字符 \ufeff 让 json.loads 失败。
        with open(expanded, encoding="utf-8-sig") as f:
            return f.read()
    except UnicodeDecodeError:
        raise ToCsvError(f"输入文件不是 UTF-8 文本：{path}")
    except OSError as e:
        raise ToCsvError(f"读取输入文件失败：{path}（{e.strerror or e}）")


def parse_envelope(text: str) -> dict:
    """把原文解析成统一信封，形状不对即给可行动错误。"""
    if not text or not text.strip():
        raise ToCsvError(
            "输入为空：请把工具响应的信封 JSON 存成文件后传入，"
            "或用管道从 stdin 读（路径写 `-`）")
    try:
        envelope = json.loads(text)
    except json.JSONDecodeError as e:
        raise ToCsvError(
            f"输入不是合法 JSON（第 {e.lineno} 行第 {e.colno} 列）：{e.msg}")
    if not isinstance(envelope, dict):
        raise ToCsvError("输入不是统一信封：顶层应为 JSON 对象 {ok, data, error, meta}")
    if "ok" not in envelope:
        raise ToCsvError("输入缺 `ok` 字段，不是统一信封 {ok, data, error, meta}")
    return envelope


def describe_failure(envelope: dict) -> str:
    """把 ok=false 的信封转成一行可行动错误。"""
    err = envelope.get("error")
    if isinstance(err, dict):
        code = err.get("code") or "ERROR"
        message = err.get("message") or "工具返回失败但未给 message"
        tail = "，可重试" if err.get("retryable") else "，不要重试"
        return f"工具返回失败 ok=false（{code}）：{message}{tail}"
    return "工具返回失败 ok=false，且未给 error 详情"


# --------------------------------------------------------------------- 形状判定 ----

def _derive_columns(rows: list) -> list:
    """按首次出现顺序汇总各行键（field_list 缺失时的兜底列序）。"""
    columns: list[str] = []
    seen: set[str] = set()
    for row in rows:
        if isinstance(row, dict):
            for key in row:
                if key not in seen:
                    seen.add(key)
                    columns.append(key)
    return columns


def classify_payload(data) -> tuple[str, list, list]:
    """判定 data 段的形状，返回 (mode, columns, rows)。

    mode ∈ {"csv", "json"}：有可落表的行与列才判 `csv`，其余（标量 / 文本 /
    取文件 kind / 分页 items / 空表无列）一律 `json`，原样保留信封。
    """
    rows = None
    if isinstance(data, dict) and isinstance(data.get("rows"), list):
        rows = data["rows"]
        # 行必须是对象（键 = canonical 列名）；出现标量行说明不是本脚本认的表形状。
        if not all(isinstance(r, dict) for r in rows):
            return "json", [], []
        field_list = data.get("field_list")
        if isinstance(field_list, list) and field_list:
            columns = [c for c in field_list if isinstance(c, str)]
            for c in _derive_columns(rows):  # 防御：行里多出的键补到末尾
                if c not in columns:
                    columns.append(c)
        else:
            columns = _derive_columns(rows)
        if columns:
            return "csv", columns, rows
        return "json", [], []

    # 防御性：data 直接是对象数组（当前对外契约不是此形状，仍按表处理）。
    if isinstance(data, list) and data and all(isinstance(x, dict) for x in data):
        columns = _derive_columns(data)
        if columns:
            return "csv", columns, data
    return "json", [], []


def render_cell(value) -> str:
    """单元格渲染。🔴 null → 空串（**不是 0**）；bool → true/false；复合值 → 紧凑 JSON。"""
    if value is None:
        return ""
    if isinstance(value, bool):  # 必须在 int 之前：bool 是 int 的子类
        return "true" if value else "false"
    if isinstance(value, str):
        return value
    if isinstance(value, float):
        # 非有限数无法进 CSV；按缺失处理，绝不补 0。
        if value != value or value in (float("inf"), float("-inf")):
            return ""
        return repr(value)
    if isinstance(value, int):
        return str(value)
    try:
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    except (TypeError, ValueError):
        return str(value)


# ------------------------------------------------------------------ gap 信号采集 ----

def collect_missing_fields(envelope: dict) -> list:
    """收集缺失列：data.missing_fields 与 meta.missing_fields 两认，去重保序。"""
    missing: list[str] = []
    for seg in (envelope.get("data"), envelope.get("meta")):
        if not isinstance(seg, dict):
            continue
        vals = seg.get("missing_fields")
        if isinstance(vals, list):
            for v in vals:
                if isinstance(v, str) and v not in missing:
                    missing.append(v)
    return missing


def collect_unknown_count(envelope: dict) -> int:
    """未登记列的出现行数（>0 应告警）。"""
    data = envelope.get("data")
    if isinstance(data, dict):
        n = data.get("unknown_fields_count")
        if isinstance(n, int):
            return n
    return 0


def collect_notes(envelope: dict) -> list:
    """结果不完整的其它信号（部分 / 降级）——一并落旁注并提示。"""
    notes: list[str] = []
    data = envelope.get("data") if isinstance(envelope.get("data"), dict) else {}
    meta = envelope.get("meta") if isinstance(envelope.get("meta"), dict) else {}
    if data.get("_partial"):
        reason = data.get("_partial_reason") or "partial"
        notes.append(f"_partial={reason}")
    if meta.get("degraded"):
        notes.append("meta.degraded=true")
    return notes


# ---------------------------------------------------------------------- 落盘 ----

def write_csv(path: str, columns: list, rows: list, comment_lines: list) -> None:
    """UTF-8 带 BOM 写 CSV；comment_lines 非空时作为前置 `#` 注释行。"""
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        for line in comment_lines:
            f.write(f"# {line}\n")
        writer = csv.writer(f)
        writer.writerow(columns)
        for row in rows:
            writer.writerow([render_cell(row.get(c)) for c in columns])


def write_json(path: str, envelope: dict) -> None:
    """非表结构原样落 JSON（保留 ok/data/error/meta 全量，null 保持 null）。"""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(envelope, f, ensure_ascii=False, indent=2)
        f.write("\n")


def sidecar_path(path: str) -> str:
    """旁注文件路径：与产物同目录同名，后缀 `.meta.json`。"""
    root, _ext = os.path.splitext(path)
    return root + SIDECAR_SUFFIX


def write_sidecar(path: str, envelope: dict, missing: list, unknown: int) -> None:
    """把来源、时点、缺口信号落一份机器可读旁注（人读主件、机读旁注互不干扰）。"""
    data = envelope.get("data") if isinstance(envelope.get("data"), dict) else {}
    meta = envelope.get("meta") if isinstance(envelope.get("meta"), dict) else {}
    provenance = data.get("provenance") if isinstance(data.get("provenance"), dict) else {}
    sidecar = {
        "tool": meta.get("tool"),
        "request_id": meta.get("request_id"),
        "source": provenance.get("source"),
        "fetched_at": provenance.get("fetched_at"),
        "coverage": meta.get("coverage"),
        "degraded": meta.get("degraded"),
        "cached": meta.get("cached"),
        "stale": meta.get("stale"),
        "missing_fields": missing,
        "unknown_fields_count": unknown,
        "_partial": data.get("_partial"),
        "_partial_reason": data.get("_partial_reason"),
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(sidecar, f, ensure_ascii=False, indent=2)
        f.write("\n")


def build_output_path(out_dir: str, stem: str, ext: str) -> tuple[str, str]:
    """生成不冲突的产物绝对路径，返回 (路径, 重命名说明)。"""
    filename = sanitize_filename(f"{stem}.{ext}")
    if not filename:
        raise ToCsvError("无法由工具名生成合法文件名，请用 `--tool` 指定工具名")
    target = ensure_inside(out_dir, os.path.join(out_dir, filename))
    if os.path.exists(target):
        return unique_path(out_dir, filename), "同名文件已存在，已自动重命名"
    return target, ""


# --------------------------------------------------------------------- CLI ----

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="to_csv.py",
        description="把文档/表格类取数工具的统一信封落成 CSV（UTF-8 带 BOM）或 JSON。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=EXAMPLES,
    )
    parser.add_argument("input", nargs="?", default="-",
                        help="工具响应的信封 JSON 文件路径；`-` 或省略则从 stdin 读")
    parser.add_argument("--tool", default="",
                        help="工具名（覆盖 meta.tool；两者都缺时用 fin_data）")
    parser.add_argument("--out-dir", default="",
                        help="落盘目录（默认：技能工作目录下的 yj_fin_data/）")
    parser.add_argument("--format", default="auto", choices=("auto", "csv", "json"),
                        help="输出格式：auto（按 data 形状自动，默认）/ csv / json")
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        envelope = parse_envelope(read_input(args.input))
        if envelope.get("ok") is not True:
            raise ToCsvError(describe_failure(envelope))

        meta = envelope.get("meta") if isinstance(envelope.get("meta"), dict) else {}
        tool = sanitize_filename(args.tool) or sanitize_filename(str(meta.get("tool") or ""))
        tool = tool or DEFAULT_TOOL_STEM

        mode, columns, rows = classify_payload(envelope.get("data"))
        if args.format == "json":
            mode = "json"
        elif args.format == "csv" and mode != "csv":
            raise ToCsvError(
                "--format csv 但响应 data 不是二维表（无 rows），无法落 CSV；"
                "去掉该参数或用 --format json")

        out_dir = os.path.expanduser(args.out_dir.strip()) or default_skill_output_dir()
        os.makedirs(out_dir, exist_ok=True)
        stamp = datetime.datetime.now().strftime(TIMESTAMP_FORMAT)
        ext = "csv" if mode == "csv" else "json"
        path, rename_note = build_output_path(out_dir, f"{tool}_{stamp}", ext)

        missing = collect_missing_fields(envelope)
        unknown = collect_unknown_count(envelope)
        notes = collect_notes(envelope)

        if mode == "csv":
            comment_lines = []
            if missing:
                comment_lines.append("missing_fields: " + ", ".join(missing))
            comment_lines.extend(notes)
            write_csv(path, columns, rows, comment_lines)
        else:
            write_json(path, envelope)
        write_sidecar(sidecar_path(path), envelope, missing, unknown)
    except ToCsvError as e:
        print(f"错误：{e}", file=sys.stderr)
        return 1
    except ValueError as e:  # utils 的入参边界校验
        print(f"错误：{e}", file=sys.stderr)
        return 1

    if rename_note:
        print(rename_note, file=sys.stderr)
    if missing:
        print(
            f"警告：服务端未返回 {len(missing)} 列，已在产物中记录（绝不补 0）："
            + ", ".join(missing),
            file=sys.stderr)
    if unknown:
        print(
            f"警告：有 {unknown} 行为未登记列（不在列目录内），已按缺列处理、不并入表。",
            file=sys.stderr)
    for note in notes:
        print(f"提示：{note}", file=sys.stderr)
    if mode == "json":
        print(f"提示：data 非二维表，已落 JSON；旁注见 {sidecar_path(path)}", file=sys.stderr)
    print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
