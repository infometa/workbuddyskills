"""xlsx 完整字段盘点工具 (CLI).

复用于 scripts/full_analyze.py, 拆成两段:
  1. parse_xlsx_full(path) -> (header, rows)   纯函数, 复用 xlsx_reader 的 XML 解析
  2. main()                                  CLI, 走 python -m soc_alert_pipeline.scripts.xlsx_summary <file>

功能:
  - 字段非空率柱状图
  - logsource_subtype / data_type / event_name Top 分布
  - severity / confidence 分布
  - event_timestamp 时间分布
  - src_ip / dst_ip / hostname Top 实体
  - raw_log 抽样
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path
from typing import Any

from xlsx_reader import read_xlsx


def pct(n: int, total: int) -> str:
    return f"{n} ({n*100/total:.1f}%)" if total else "0"


def summarize_xlsx(path: str | Path) -> None:
    p = Path(path).expanduser().resolve()
    print(f"[*] 加载: {p.name}")
    header, rows = read_xlsx(str(p))
    total = len(rows)
    print(f"[*] 解析完成: {total} 条记录, {len(header)} 个字段\n")

    # 1. 字段总览
    print("=" * 80)
    print("【1. 字段总览】")
    print("=" * 80)
    for i, h in enumerate(header, 1):
        non_empty = sum(1 for r in rows if r.get(h) and r.get(h) != "-")
        rate = non_empty * 100 / total
        bar = "█" * int(rate / 5)
        print(f"  {i:2d}. {h:25s}  非空率: {rate:5.1f}%  {bar}")
    print()

    # 2. 产品分布
    print("=" * 80)
    print("【2. 产品分布 (logsource_subtype)】")
    print("=" * 80)
    prod_counter = Counter(r.get("logsource_subtype", "-") for r in rows)
    for prod, cnt in prod_counter.most_common():
        print(f"  {prod:30s}  {cnt:5d}  {pct(cnt, total)}")
    print()

    # 3. data_type / data_subtype 分布
    print("=" * 80)
    print("【3. data_type / data_subtype 分布】")
    print("=" * 80)
    dt_counter = Counter(r.get("data_type", "-") for r in rows)
    for k, v in dt_counter.most_common(10):
        print(f"  data_type={k:20s}  {v:5d}  {pct(v, total)}")
    print()
    dst_counter = Counter(r.get("data_subtype", "-") for r in rows)
    for k, v in dst_counter.most_common(10):
        print(f"  data_subtype={k:30s}  {v:5d}  {pct(v, total)}")
    print()

    # 4. event_name Top 20
    print("=" * 80)
    print("【4. event_name (告警名称) Top 20】")
    print("=" * 80)
    en_counter = Counter(r.get("event_name", "-") for r in rows)
    for name, cnt in en_counter.most_common(20):
        print(f"  {cnt:5d}  {name[:70]}")
    print()

    # 5. category / subcategory 分布
    print("=" * 80)
    print("【5. category / subcategory 分布】")
    print("=" * 80)
    cat_counter = Counter(r.get("category", "-") for r in rows)
    for k, v in cat_counter.most_common(10):
        print(f"  category={k:20s}  {v:5d}  {pct(v, total)}")
    print()
    sub_counter = Counter(r.get("subcategory", "-") for r in rows)
    for k, v in sub_counter.most_common(10):
        print(f"  subcategory={k:25s}  {v:5d}  {pct(v, total)}")
    print()

    # 6. severity / confidence
    print("=" * 80)
    print("【6. severity / confidence 分布】")
    print("=" * 80)
    sev_counter = Counter(r.get("severity", "-") for r in rows)
    for k in sorted(sev_counter.keys(), key=lambda x: (x == "-", x)):
        v = sev_counter[k]
        print(f"  severity={k:5s}  {v:5d}  {pct(v, total)}")
    print()
    conf_counter = Counter(r.get("confidence", "-") for r in rows)
    for k in sorted(conf_counter.keys(), key=lambda x: (x == "-", x)):
        v = conf_counter[k]
        print(f"  confidence={k:5s}  {v:5d}  {pct(v, total)}")
    print()

    # 7. 时间分布
    print("=" * 80)
    print("【7. 时间分布 (event_timestamp)】")
    print("=" * 80)
    dates: list[str] = []
    for r in rows:
        ts = r.get("event_timestamp", "")
        if ts and ts != "-":
            try:
                dates.append(ts[:10])
            except Exception:
                pass
    date_counter = Counter(dates)
    print(f"  时间范围: {min(dates) if dates else '-'} ~ {max(dates) if dates else '-'}")
    print(f"  有效时间记录: {len(dates)} / {total}")
    for d in sorted(date_counter.keys()):
        print(f"  {d}  {'█' * (date_counter[d] // 50 + 1):30s}  {date_counter[d]}")
    print()

    # 8. 实体分布
    print("=" * 80)
    print("【8. 实体分布 Top】")
    print("=" * 80)
    src_ip = Counter(r.get("src_ip", "-") for r in rows if r.get("src_ip", "-") != "-")
    dst_ip = Counter(r.get("dst_ip", "-") for r in rows if r.get("dst_ip", "-") != "-")
    hostname = Counter(r.get("hostname", "-") for r in rows if r.get("hostname", "-") != "-")
    print(f"  [src_ip] 共 {len(src_ip)} 个独立值, Top 10:")
    for k, v in src_ip.most_common(10):
        print(f"    {v:4d}  {k}")
    print(f"  [dst_ip] 共 {len(dst_ip)} 个独立值, Top 10:")
    for k, v in dst_ip.most_common(10):
        print(f"    {v:4d}  {k}")
    print(f"  [hostname] 共 {len(hostname)} 个独立值, Top 10:")
    for k, v in hostname.most_common(10):
        print(f"    {v:4d}  {k}")
    print()

    # 9. raw_log 抽样
    print("=" * 80)
    print("【9. raw_log 抽样 (前 3 条, 截断 200 字符)】")
    print("=" * 80)
    for i, r in enumerate(rows[:3]):
        print(f"  --- R{i+1} ({r.get('event_name','')[:30]}) ---")
        raw = r.get("raw_log", "")
        if len(raw) > 300:
            raw = raw[:200] + " ...[truncated]... " + raw[-100:]
        print(f"  {raw}")
        print()


def main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv[1:]
    if not argv:
        print("usage: xlsx_summary.py <file.xlsx>")
        return 1
    summarize_xlsx(argv[0])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
