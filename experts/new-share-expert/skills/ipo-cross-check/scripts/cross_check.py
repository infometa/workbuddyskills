#!/usr/bin/env python3
"""
A 股新股多源交叉校验脚本
- 从 westock-data ipo hs / search 拉取
- 从 NeoData 自然语言 query 拉取
- 比对关键事实字段，输出结构化报告

用法：
    python3 cross_check.py sz301669
    python3 cross_check.py sz301669 --name 高特电子
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime

WESTOCK_PATHS = [
    os.path.expanduser(
        "~/.workbuddy/plugins/marketplaces/cb_teams_marketplace/plugins/finance-data/skills/westock-data/scripts/index.js"
    ),
    os.path.expanduser(
        "~/.workbuddy/plugins/marketplaces/cb_teams_marketplace/external_plugins/new-share-copilot/skills/westock-data/scripts/index.js"
    ),
    os.path.expanduser(
        "~/.workbuddy/plugins/marketplaces/experts/plugins/strategy-backtest-expert/skills/westock-data/scripts/index.js"
    ),
]
NEODATA_PATHS = [
    os.path.expanduser(
        "~/.workbuddy/plugins/marketplaces/cb_teams_marketplace/plugins/finance-data/skills/neodata-financial-search/scripts/query.py"
    ),
    os.path.expanduser(
        "~/.workbuddy/plugins/marketplaces/cb_teams_marketplace/external_plugins/new-share-copilot/skills/neodata-financial-search/scripts/query.py"
    ),
    os.path.expanduser(
        "~/.workbuddy/plugins/marketplaces/experts/plugins/strategy-backtest-expert/skills/neodata-financial-search/scripts/query.py"
    ),
]


def _glob_first(pattern):
    import glob
    for base in [
        os.path.expanduser("~/.workbuddy/plugins/marketplaces"),
        os.path.expanduser("~/.workbuddy/skills"),
    ]:
        if os.path.isdir(base):
            hits = glob.glob(os.path.join(base, "**", pattern), recursive=True)
            if hits:
                return hits[0]
    return None


def first_existing(paths):
    for p in paths:
        if os.path.isfile(p):
            return p
    # 兜底：按 basename 扫描
    if paths:
        rel_pattern = os.path.join(
            os.path.basename(os.path.dirname(os.path.dirname(paths[0]))),
            os.path.basename(os.path.dirname(paths[0])),
            os.path.basename(paths[0]),
        )
        hit = _glob_first(rel_pattern)
        if hit:
            return hit
    return None


def parse_table(stdout: str):
    rows = []
    for line in stdout.strip().splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if not cells:
            continue
        # 分隔行：所有非空 cell 都是 ---
        if all((c == "" or set(c) == {"-"}) for c in cells) and any(set(c) == {"-"} for c in cells):
            continue
        rows.append(cells)
    if len(rows) < 2:
        return []
    header = rows[0]
    return [dict(zip(header, r)) for r in rows[1:]]


def run_westock(args):
    script = first_existing(WESTOCK_PATHS)
    if not script:
        return None, "westock-data 脚本未找到"
    try:
        proc = subprocess.run(["node", script] + args, capture_output=True, text=True, timeout=30)
        if proc.returncode != 0:
            return None, proc.stderr.strip()
        return proc.stdout, None
    except Exception as e:
        return None, str(e)


PYTHON_CANDIDATES = [
    os.path.expanduser("~/.workbuddy/binaries/python/envs/default/bin/python"),
    "python3",
    "python",
]


def find_python():
    for p in PYTHON_CANDIDATES:
        if os.path.isfile(p) or p in ("python3", "python"):
            return p
    return "python3"


def run_neodata(query: str):
    script = first_existing(NEODATA_PATHS)
    if not script:
        return None, "NeoData 脚本未找到"
    py = find_python()
    try:
        proc = subprocess.run([py, script, "--query", query],
                              capture_output=True, text=True, timeout=60)
        out = proc.stdout or ""
        # neodata 脚本即便没装 requests 也走 returncode=0 + stdout 报错信息
        if "需要安装 requests" in out or "TOKEN_EXPIRED" in out or "TOKEN_MISSING" in out:
            return None, out.strip().splitlines()[0] if out.strip() else "NeoData 调用失败"
        if proc.returncode != 0:
            return None, proc.stderr.strip() or out.strip()
        return out, None
    except Exception as e:
        return None, str(e)


def fetch_westock_ipo(code: str):
    out, err = run_westock(["ipo", "hs"])
    if err:
        return None, err
    rows = parse_table(out)
    for r in rows:
        if r.get("code", "").lower() == code.lower():
            return {
                "name": r.get("name", ""),
                "price": r.get("price", ""),
                "sgrq": r.get("sgrq", ""),
                "ssrq": r.get("ssrq", ""),
                "hy": r.get("hy", ""),
            }, None
    # 不在当前 IPO 列表，尝试 search
    out2, err2 = run_westock(["search", code])
    if not err2 and out2:
        rows2 = parse_table(out2)
        if rows2:
            r = rows2[0]
            return {
                "name": r.get("name", r.get("zhongwenmingcheng", "")),
                "price": "",
                "sgrq": "",
                "ssrq": "",
                "hy": r.get("hy", ""),
            }, None
    return None, f"westock-data 中未找到 code={code}"


def extract_neodata_field(text: str, code: str, name_hint: str):
    """从 NeoData 召回文本里粗提取字段"""
    out = {"name": "", "price": "", "sgrq": "", "ssrq": "", "hy": "", "raw_excerpt": ""}
    if not text:
        return out

    out["raw_excerpt"] = text[:500]

    if name_hint and name_hint in text:
        out["name"] = name_hint

    m = re.search(r"发行价[^0-9]{0,8}([0-9]+\.[0-9]{1,3})", text)
    if m:
        out["price"] = m.group(1)

    for label, key in [("申购日", "sgrq"), ("申购日期", "sgrq"),
                       ("上市日", "ssrq"), ("上市日期", "ssrq")]:
        m = re.search(label + r"[^0-9]{0,5}(20\d{2}[-/]\d{1,2}[-/]\d{1,2})", text)
        if m:
            out[key] = m.group(1).replace("/", "-")

    m = re.search(r"(行业|所属行业|申万行业)[：: ]*([\u4e00-\u9fa5]{2,15})", text)
    if m:
        out["hy"] = m.group(2)

    return out


def cross_check(westock: dict, neodata: dict):
    rows = []

    def cmp_str(a, b):
        if not a or a == "--":
            return ("", b, "⚠️ westock 暂缺") if b else ("", "", "⚠️ 两源均缺")
        if not b:
            return (a, "", "⚠️ NeoData 暂缺")
        return (a, b, "✅" if a == b else "⚠️ 差异")

    def cmp_price(a, b):
        try:
            fa = float(a)
            fb = float(b)
            return (a, b, "✅" if abs(fa - fb) / max(fa, 0.01) < 0.01 else "⚠️ 差异")
        except (ValueError, TypeError):
            if not a or a == "--":
                return ("", b, "⚠️ westock 暂缺") if b else ("", "", "⚠️ 两源均缺")
            if not b:
                return (a, "", "⚠️ NeoData 暂缺")
            return (a, b, "⚠️ 解析失败")

    def cmp_hy(a, b):
        if not a or not b:
            if not a and not b:
                return ("", "", "⚠️ 两源均缺")
            return (a or "", b or "", "⚠️ 单源缺失")
        sa = set(re.findall(r"[\u4e00-\u9fa5]+", a))
        sb = set(re.findall(r"[\u4e00-\u9fa5]+", b))
        if a == b or sa & sb:
            return (a, b, "✅")
        return (a, b, "⚠️ 差异")

    rows.append(("名称", *cmp_str(westock.get("name", ""), neodata.get("name", ""))))
    rows.append(("申购日", *cmp_str(westock.get("sgrq", ""), neodata.get("sgrq", ""))))
    rows.append(("上市日", *cmp_str(westock.get("ssrq", ""), neodata.get("ssrq", ""))))
    rows.append(("发行价", *cmp_price(westock.get("price", ""), neodata.get("price", ""))))
    rows.append(("行业", *cmp_hy(westock.get("hy", ""), neodata.get("hy", ""))))
    return rows


def render(code: str, name: str, rows, ws_status, nd_status):
    lines = []
    lines.append("═══ 多源交叉校验报告 ═══")
    lines.append(f"代码：{code}    名称：{name or '（未提供）'}")
    lines.append(f"westock 状态：{ws_status}")
    lines.append(f"NeoData 状态：{nd_status}")
    lines.append("")
    lines.append("| 字段 | westock | NeoData | 一致 |")
    lines.append("| --- | --- | --- | --- |")
    diffs = 0
    for field, a, b, mark in rows:
        lines.append(f"| {field} | {a or '—'} | {b or '—'} | {mark} |")
        if mark.startswith("⚠️"):
            diffs += 1
    lines.append("")
    if diffs == 0:
        lines.append("总结：✅ 关键字段一致，可信度高")
    else:
        lines.append(f"总结：⚠️ 共 {diffs} 个字段存在差异或缺失，请用户根据券商发行公告复核")
    lines.append("")
    lines.append(f"数据时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("来源：westock-data（ipo hs / search）｜ NeoData query")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("code")
    ap.add_argument("--name", default="")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    args = ap.parse_args()

    if not re.match(r"^(sh|sz|bj)[0-9A-Za-z]+$", args.code):
        sys.stderr.write("❌ 代码格式错误（仅支持 A 股 sh/sz/bj 前缀）\n")
        sys.exit(1)

    westock, ws_err = fetch_westock_ipo(args.code)
    ws_status = "OK" if westock else f"失败（{ws_err}）"

    name_hint = args.name or (westock.get("name") if westock else "") or args.code
    query = f"{name_hint} {args.code} 新股 申购日 上市日 发行价 市盈率 募资额 行业"
    nd_out, nd_err = run_neodata(query)
    if nd_out:
        neodata = extract_neodata_field(nd_out, args.code, name_hint)
        nd_status = "OK"
    else:
        neodata = {"name": "", "price": "", "sgrq": "", "ssrq": "", "hy": "", "raw_excerpt": ""}
        nd_status = f"失败（{nd_err}）"

    if not westock and not neodata.get("name"):
        sys.stderr.write("❌ 两源均无数据\n")
        sys.exit(4)

    rows = cross_check(westock or {}, neodata)
    name = (westock.get("name") if westock else "") or neodata.get("name") or args.name

    if args.json:
        print(json.dumps({
            "code": args.code,
            "name": name,
            "westock": westock,
            "neodata": neodata,
            "rows": [{"field": r[0], "westock": r[1], "neodata": r[2], "mark": r[3]} for r in rows],
            "ws_status": ws_status,
            "nd_status": nd_status,
        }, ensure_ascii=False, indent=2))
    else:
        print(render(args.code, name, rows, ws_status, nd_status))


if __name__ == "__main__":
    main()
