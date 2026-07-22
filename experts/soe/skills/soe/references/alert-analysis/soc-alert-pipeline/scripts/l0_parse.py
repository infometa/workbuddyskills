#!/usr/bin/env python3
"""L0 批量解析 CLI - 把 SOC 导出 xlsx / WAF CSV 解析成 JSON Lines (含资产关联)

支持输入格式:
  - .xlsx  : SOC 导出 xlsx (含 raw_log 列) 或 天幕直出 xlsx (中文列头)
  - .csv   : 腾讯云 WAF 攻击日志直出 CSV (中文列头, 12 字段)

用法:
  # 解析御界数据 (xlsx, 默认自动加载 host-资产/ 目录的资产 CSV)
  python3 l0_parse.py soc日志/event/esSearch_20260706145614.xlsx --out l0_output/yujie_l0.jsonl

  # 解析主机安全数据 (限定 100 条预览)
  python3 l0_parse.py soc日志/event/esSearch_20260706144610.xlsx --limit 100

  # 解析 WAF 攻击日志 (CSV 直出)
  python3 l0_parse.py attacklog-1780556626.csv --out l0_output/waf_l0.jsonl --product waf

  # 禁用资产关联
  python3 l0_parse.py xxx.xlsx --no-assets

  # 指定资产目录
  python3 l0_parse.py xxx.xlsx --assets /path/to/asset-csvs/
"""
from __future__ import annotations
import argparse
import csv
import json
import sys
from pathlib import Path

# 允许从项目根目录直接运行
# SCRIPT_DIR = skills/soe/references/alert-analysis/soc-alert-pipeline/scripts/
# 项目根 = SCRIPT_DIR.parent.parent.parent.parent.parent (5 层)
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent.parent.parent.parent
sys.path.insert(0, str(SCRIPT_DIR))

# 资产库在独立 skill: asset-manager
# scripts/ → soc-alert-pipeline/ → alert-analysis/ → references/ → asset-management/asset-manager/scripts/
ASSET_SKILL_DIR = SCRIPT_DIR.parent.parent.parent / "asset-management" / "asset-manager" / "scripts"
sys.path.insert(0, str(ASSET_SKILL_DIR))

from xlsx_reader import read_xlsx
from parsers.registry import get_parser, detect_product, supported_products
from parsers.waf_parser import WafParser
from parsers.tianmu_parser import TianmuParser
from parsers.yujie_flat_parser import YujieFlatParser
from asset_resolver import AssetResolver, load_default_assets


# ==================== 输入读取 (xlsx + csv) ====================

def read_csv_file(path: Path) -> tuple[list[str], list[dict]]:
    """读取 CSV 文件, 返回 (header, rows), 与 read_xlsx 接口一致

    用于腾讯云 WAF 攻击日志直出 CSV (UTF-8 with BOM, 中文列头).
    """
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            return [], []
        header = [h.strip() for h in header]
        rows: list[dict] = []
        for line in reader:
            if not line or all(not c.strip() for c in line):
                continue
            # 与 read_xlsx 一致: row 是 dict (列名 → 值)
            # 对齐长度: 不足补空, 多余截断
            values = (line + [""] * len(header))[: len(header)]
            row = {k: (v or "").strip() for k, v in zip(header, values)}
            rows.append(row)
        return header, rows


def read_any(path: Path) -> tuple[list[str], list[dict]]:
    """按文件扩展名分发到对应 reader

    Returns:
        (header, rows) - header 是列名列表, rows 是 dict 列表
    """
    ext = path.suffix.lower()
    if ext == ".xlsx":
        return read_xlsx(path)
    if ext == ".csv":
        return read_csv_file(path)
    raise ValueError(f"不支持的文件格式: {ext} (仅支持 .xlsx / .csv)")


def is_waf_format(header: list[str]) -> bool:
    """检测是否为 WAF 直出格式 (中文列头, 无 raw_log)"""
    return any(col in header for col in WafParser.IDENTIFIER_COLS)


def is_tianmu_format(header: list[str]) -> bool:
    """检测是否为天幕直出格式 (中文列头, 无 raw_log)"""
    return any(col in header for col in TianmuParser.IDENTIFIER_COLS)


def is_yujie_flat_format(header: list[str]) -> bool:
    """检测是否为御界直出格式 (EVE 风格英文列头, 无 raw_log)

    御界控制台单独导出, 列头含 alert.signature / fileinfo.filename 等带点号字段.
    # TODO: CWP 直出 / CFW 直出 待用户提供样本后补充对应 is_xxx_format 函数.
    """
    return any(col in header for col in YujieFlatParser.IDENTIFIER_COLS)


def process_row(
    row: dict,
    row_idx: int,
    source_file: str,
    force_product: str | None,
    asset_resolver: AssetResolver | None = None,
) -> dict:
    """处理单行 xlsx 数据, 调用对应 parser, 返回 L0 输出 dict

    Args:
        row: xlsx 单行 (dict)
        row_idx: 行号
        source_file: 来源文件名
        force_product: 强制指定的产品代号 (None 自动识别)
        asset_resolver: 资产解析器 (None 不做资产关联)
    """
    raw_log = row.get("raw_log", "")

    # 1. 选 product
    if force_product:
        product = force_product.lower()
    else:
        product = detect_product(row)

    # 2. 没识别到 product, 跳过
    if not product:
        return {
            "row": row_idx,
            "source_file": source_file,
            "parse_status": "skipped",
            "parse_errors": ["无法识别 product (logsource_subtype/字段都不匹配)"],
            "raw_log_preview": raw_log[:200] if raw_log else "",
        }

    # 3. 选 parser
    parser = get_parser(product)
    if not parser:
        return {
            "row": row_idx,
            "source_file": source_file,
            "product": product,
            "parse_status": "skipped",
            "parse_errors": [f"no parser for product={product}, supported={supported_products()}"],
            "raw_log_preview": raw_log[:200] if raw_log else "",
        }

    # 4. 调用 parser
    result = parser.parse(raw_log, row)
    out = result.to_dict()
    out["row"] = row_idx
    out["source_file"] = source_file
    out["product"] = product

    # 5. 把 OCSF 关键字段也带出来 (便于 L1 / 调试)
    out["ocsf"] = {
        k: row.get(k, "") for k in (
            "event_id", "event_name", "event_timestamp", "severity", "confidence",
            "category", "subcategory", "logsource_subtype", "data_type", "data_subtype",
            "hostname",
        ) if k in row
    }

    # 6. 资产关联 (可选, 按产品走不同关联逻辑)
    if asset_resolver is not None:
        try:
            asset_info = asset_resolver.enrich_event(out.get("parsed", {}), product=product)
            out["asset"] = asset_info
        except Exception as e:
            out["asset"] = {"error": f"资产关联失败: {type(e).__name__}: {e}"}

    return out


def main():
    ap = argparse.ArgumentParser(
        description="L0 批量解析 SOC 导出 xlsx / WAF CSV → JSON Lines (含资产关联)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("input", type=Path, help="输入文件路径 (.xlsx 或 .csv)")
    ap.add_argument("--out", type=Path, default=None,
                    help="输出 JSONL 文件路径 (默认 stdout)")
    ap.add_argument("--product", type=str, default=None,
                    help="强制指定产品代号 (yujie / cwp / tianmu / waf), 跳过自动识别")
    ap.add_argument("--limit", type=int, default=None,
                    help="限制处理行数 (用于调试 / 预览)")
    ap.add_argument("--pretty", action="store_true",
                    help="输出带缩进 (默认每行一条 JSON)")
    ap.add_argument("--assets", type=Path, default=None,
                    help="资产 CSV 目录 (默认 host-资产/)")
    ap.add_argument("--no-assets", action="store_true",
                    help="禁用资产关联")
    args = ap.parse_args()

    if not args.input.exists():
        print(f"[ERR] 输入文件不存在: {args.input}", file=sys.stderr)
        sys.exit(1)

    # 1. 加载资产库 (除非 --no-assets)
    asset_resolver = None
    if not args.no_assets:
        asset_dir = args.assets or (PROJECT_ROOT / "host-资产")
        if asset_dir.exists():
            try:
                asset_resolver = load_default_assets(PROJECT_ROOT)
                stats = asset_resolver.stats()
                print(f"[INFO] 资产库加载: total={stats['total']} "
                      f"(by_layer={stats['by_layer']}, by_type={stats['by_type']})",
                      file=sys.stderr)
            except Exception as e:
                print(f"[WARN] 资产库加载失败 (跳过资产关联): {type(e).__name__}: {e}",
                      file=sys.stderr)
        else:
            print(f"[INFO] 资产目录不存在, 跳过资产关联: {asset_dir}", file=sys.stderr)

    # 2. 读输入 (按扩展名分发)
    print(f"[INFO] 读取: {args.input}", file=sys.stderr)
    try:
        header, rows = read_any(args.input)
    except Exception as e:
        print(f"[ERR] 文件解析失败: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(2)
    print(f"[INFO] header={len(header)} cols, rows={len(rows)}", file=sys.stderr)

    # 格式识别: raw_log 列(SOC导出) / 天幕直出 / WAF直出 / 御界直出
    # TODO: CWP 直出 / CFW 直出 待用户提供样本后补充识别分支
    has_raw_log = "raw_log" in header
    is_tianmu = is_tianmu_format(header)
    is_waf = is_waf_format(header)
    is_yujie_flat = is_yujie_flat_format(header)
    if not has_raw_log and not is_tianmu and not is_waf and not is_yujie_flat:
        print(f"[ERR] 未识别的格式: 无 raw_log 列, 且非天幕/WAF/御界 直出格式, header={header}",
              file=sys.stderr)
        sys.exit(3)
    if is_tianmu:
        print(f"[INFO] 检测到天幕直出格式 (无 raw_log, 中文列头)", file=sys.stderr)
    if is_waf:
        print(f"[INFO] 检测到 WAF 直出格式 (无 raw_log, 中文列头)", file=sys.stderr)
    if is_yujie_flat:
        print(f"[INFO] 检测到御界直出格式 (无 raw_log, EVE 风格英文列头)", file=sys.stderr)

    # 3. 限制行数
    if args.limit:
        rows = rows[:args.limit]
        print(f"[INFO] 限制处理: {args.limit} 行", file=sys.stderr)

    # 4. 打开输出
    out_f = open(args.out, "w", encoding="utf-8") if args.out else sys.stdout
    n_ok, n_partial, n_failed, n_skipped = 0, 0, 0, 0
    n_asset_matched = 0
    n_match_by_method = {"ip_appid": 0, "ip_vpcid": 0, "ip_only": 0, "hostname": 0, "none": 0}

    for i, row in enumerate(rows):
        rec = process_row(row, i, args.input.name, args.product, asset_resolver)
        if args.pretty:
            out_f.write(json.dumps(rec, ensure_ascii=False, indent=2) + "\n")
        else:
            out_f.write(json.dumps(rec, ensure_ascii=False) + "\n")

        status = rec.get("parse_status", "ok")
        if status == "ok":
            n_ok += 1
        elif status == "partial":
            n_partial += 1
        elif status == "failed":
            n_failed += 1
        else:  # skipped
            n_skipped += 1

        # 统计资产关联命中
        asset_info = rec.get("asset", {})
        if isinstance(asset_info, dict):
            method = asset_info.get("match_method", "none")
            n_match_by_method[method] = n_match_by_method.get(method, 0) + 1
            if asset_info.get("victim_asset"):
                n_asset_matched += 1

    if args.out:
        out_f.close()
        print(f"[OK] 写出: {args.out}", file=sys.stderr)
    print(
        f"[STATS] ok={n_ok} partial={n_partial} failed={n_failed} skipped={n_skipped} / total={len(rows)}",
        file=sys.stderr,
    )
    if asset_resolver is not None:
        print(f"[STATS] 资产关联命中: {n_asset_matched}/{len(rows)} "
              f"({n_asset_matched * 100 // max(len(rows), 1)}%)",
              file=sys.stderr)
        print(f"[STATS] 关联方法分布: {n_match_by_method}", file=sys.stderr)


if __name__ == "__main__":
    main()
