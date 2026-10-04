#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把行家平台给的 CSV 名单转成包内静态数据（mentors.json）。

只在名单更新时手动跑一次，运行时不调用。

用法：
    python build_mentor_data.py <行家列表.csv>            # 写入 ../data/mentors.json
    python build_mentor_data.py <csv> --out /tmp/x.json   # 指定输出

CSV 必须包含这些列（列名与行家平台导出保持一致）：
    行家姓名 / 职位 / 族 / 话题名称 / 分类 / 时长 / 咨询次数
    大纲 / 资历 / 标签 / 话题权限 / 话题状态 / 下架时间
    加参数url，请使用这个链接在“经纪人专家”中推荐行家
"""
import argparse
import csv
import json
import re
import sys
from pathlib import Path

# 只保留这个前缀的链接。行家平台给的带参链接自带来源标记，
# 不许改写、不许拼接、不许换域名。
URL_PREFIX = "https://learn.woa.com/r/hangjiaTopic?"

URL_COL = "加参数url，请使用这个链接在“经纪人专家”中推荐行家"

# 族名（如「技术族（TE）」）→ 简码，供画像匹配用
CLAN_CODE = {
    "技术族": "TE",
    "产品/项目族": "PD",
    "设计族": "DG",
    "市场族": "MA",
    "专业族": "SC",
}


def clan_code(raw: str):
    """从「技术族（TE）」提出 TE；提不出返回 None，不猜。"""
    m = re.search(r"[（(]([A-Z]{2})[)）]", raw or "")
    if m:
        return m.group(1)
    for name, code in CLAN_CODE.items():
        if name and name in (raw or ""):
            return code
    return None


def split_tags(raw: str):
    """标签列可能用中英文逗号或顿号分隔。"""
    if not raw:
        return []
    parts = re.split(r"[,，、;；/]+", raw)
    return [p.strip() for p in parts if p.strip()]


def clean(text: str, limit: int = 0):
    """压掉换行和连续空白；limit>0 时截断（大纲/资历有超千字的）。"""
    if not text:
        return ""
    t = re.sub(r"\s+", " ", text).strip()
    if limit and len(t) > limit:
        t = t[:limit].rstrip() + "…"
    return t


def split_name(raw: str):
    """「jerryliang(梁镇锋)」→ ('jerryliang', '梁镇锋')。取不到中文名就留空。"""
    raw = (raw or "").strip()
    m = re.match(r"^([^(（]+)[(（]([^)）]*)[)）]\s*$", raw)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return raw, ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv_path")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    src = Path(args.csv_path)
    if not src.exists():
        print(f"找不到 CSV：{src}", file=sys.stderr)
        return 2

    out = Path(args.out) if args.out else Path(__file__).resolve().parent.parent / "data" / "mentors.json"

    with src.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    topics = []
    skipped = {"下架": 0, "缺链接": 0, "链接非法": 0}

    for r in rows:
        status = (r.get("话题状态") or "").strip()
        if status and status != "已上架":
            skipped["下架"] += 1
            continue

        url = (r.get(URL_COL) or "").strip()
        if not url:
            skipped["缺链接"] += 1
            continue
        if not url.startswith(URL_PREFIX):
            # 链接前缀不对宁可丢掉这条，也不改写成"看起来合理"的地址
            skipped["链接非法"] += 1
            continue

        rtx, cn_name = split_name(r.get("行家姓名"))
        clan_raw = (r.get("族") or "").strip()

        try:
            consult = int(float(r.get("咨询次数") or 0))
        except ValueError:
            consult = 0
        try:
            hours = float(r.get("时长") or 0) or None
        except ValueError:
            hours = None

        topics.append({
            "mentor_rtx": rtx,
            "mentor_name": cn_name,
            "position": clean(r.get("职位")),
            "clan": clan_raw,
            "clan_code": clan_code(clan_raw),
            "topic": clean(r.get("话题名称")),
            "category": clean(r.get("分类")),
            "tags": split_tags(r.get("标签")),
            "outline": clean(r.get("大纲"), 220),
            "credential": clean(r.get("资历"), 160),
            "hours": hours,
            "consult_count": consult,
            "audience": clean(r.get("话题权限")),
            "url": url,
        })

    # 稳定排序：族 → 职位 → 咨询次数倒序，让每次重建的 diff 可读
    topics.sort(key=lambda t: (t["clan_code"] or "ZZ", t["position"], -t["consult_count"], t["topic"]))

    payload = {
        "source": "行家平台导出名单（人工提供，静态快照）",
        "source_file": src.name,
        "topic_count": len(topics),
        "mentor_count": len({t["mentor_rtx"] for t in topics}),
        "clan_codes": CLAN_CODE,
        "url_prefix": URL_PREFIX,
        "note": "运行时只读本文件，禁止编造行家/话题/链接。名单更新时重跑 scripts/build_mentor_data.py。",
        "topics": topics,
    }

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"写入 {out}")
    print(f"  话题 {len(topics)} 条 / 行家 {payload['mentor_count']} 位")
    print(f"  跳过：{skipped}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
