"""CLI over the drbt retail MCP: raw calls, sales extraction, ranking reports.

Usage
-----
  python drbt.py list
  python drbt.py call 销售明细表查询 --args '{"page_num":1,"page_size":1,"filter":{...}}'
  python drbt.py sales --begin 2026-09-01 --end 2026-09-17 [--out rows.json]
  python drbt.py rank  --begin 2026-09-17 --end 2026-09-17 [--out report.html]
  python drbt.py rank  --begin 2026-09-01 --end 2026-09-17 --label "9月至今"

Date args are plain local dates (UTC+8). They are converted to the millisecond
timestamps the API expects on the *制单日期* (document creation) axis.
"""

import argparse
import datetime
import json
import os
import sys
from collections import OrderedDict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcp_client import Session  # noqa: E402

TZ = datetime.timezone(datetime.timedelta(hours=8))
BILL = {1: "零售", 2: "零售退", 3: "批发", 4: "批发退"}


def ts_start(d):
    y, m, dd = (int(x) for x in d.split("-"))
    return int(datetime.datetime(y, m, dd, 0, 0, 0, tzinfo=TZ).timestamp() * 1000)


def ts_end(d):
    y, m, dd = (int(x) for x in d.split("-"))
    return int(datetime.datetime(y, m, dd, 23, 59, 59, tzinfo=TZ).timestamp() * 1000)


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def gross(r):
    """Cost-based gross profit. Other profit fields are masked as \"***\"."""
    return num(r.get("retail_cost_gross_profit")) + num(r.get("wholesale_cost_gross_profit"))


def cost(r):
    return num(r.get("retail_cost_money")) + num(r.get("wholesale_cost_money"))


# ---------------------------------------------------------------- extraction

def fetch_rows(s, begin, end, bill_types=None, page_size=100):
    flt = {"begin_create_date_timestamp": ts_start(begin),
           "end_create_date_timestamp": ts_end(end)}
    if bill_types:
        flt["bill_type_list"] = bill_types

    head = s.payload("销售明细表查询", {"page_num": 1, "page_size": 1, "filter": flt})
    total = int(head["data"]["total"])
    summary = head["data"]["total_row"]

    rows = []
    pages = (total + page_size - 1) // page_size
    for p in range(1, pages + 1):
        r = s.payload("销售明细表查询",
                      {"page_num": p, "page_size": page_size, "filter": flt},
                      rid=200 + p)
        rows.extend(r["data"]["rows"])
    return rows, summary


def fetch_quantity_summary(s, begin, end, **extra):
    """Report-level totals straight from total_row with page_size=1."""
    flt = {"begin_create_date_timestamp": ts_start(begin),
           "end_create_date_timestamp": ts_end(end)}
    flt.update(extra)
    r = s.payload("销售明细表查询", {"page_num": 1, "page_size": 1, "filter": flt})
    return r["data"]["total_row"], int(r["data"]["total"])


# ---------------------------------------------------------------- aggregation

def blank():
    return {"sale": 0.0, "qty": 0, "gross": 0.0, "cost": 0.0,
            "bills": set(), "lines": 0, "retail_sale": 0.0, "whole_sale": 0.0}


def add(g, r):
    g["sale"] += num(r["sale_money"])
    g["qty"] += int(r["qty"])
    g["gross"] += gross(r)
    g["cost"] += cost(r)
    g["bills"].add(r["bill_id"])
    g["lines"] += 1
    if r["bill_type"] in (1, 2):
        g["retail_sale"] += num(r["sale_money"])
    else:
        g["whole_sale"] += num(r["sale_money"])


def group(rows, key):
    out = OrderedDict()
    for r in rows:
        k = r.get(key)
        if not k:
            continue
        out.setdefault(k, blank())
        add(out[k], r)
    return out


def finalize(g):
    res = [{
        "name": name,
        "sale": v["sale"],
        "qty": v["qty"],
        "gross": v["gross"],
        "rate": (v["gross"] / v["sale"] * 100) if v["sale"] else 0.0,
        "bills": len(v["bills"]),
        "lines": v["lines"],
        "retail_sale": v["retail_sale"],
        "whole_sale": v["whole_sale"],
    } for name, v in g.items()]
    res.sort(key=lambda x: x["sale"], reverse=True)
    return res


def build_analysis(rows):
    tot = blank()
    for r in rows:
        add(tot, r)
    stores = finalize(group(rows, "institution_name"))
    retail = finalize(group(rows, "store_user_name"))
    wholesale = finalize(group(rows, "business_account_name"))

    staff_by_store = {}
    for r in rows:
        who = r.get("store_user_name") or r.get("business_account_name")
        if who:
            staff_by_store.setdefault(r["institution_name"], set()).add(who)

    prods = {}
    for r in rows:
        p = prods.setdefault(r["institution_name"], {})
        p[r["product_name"]] = p.get(r["product_name"], 0) + num(r["sale_money"])

    for s in stores:
        s["staff"] = len(staff_by_store.get(s["name"], set()))
        tp = prods.get(s["name"], {})
        s["top_product"] = max(tp.items(), key=lambda kv: kv[1])[0] if tp else ""

    summary = {
        "sale": tot["sale"], "qty": tot["qty"], "gross": tot["gross"],
        "rate": (tot["gross"] / tot["sale"] * 100) if tot["sale"] else 0.0,
        "bills": len(tot["bills"]), "lines": tot["lines"],
        "stores": len(stores),
        "people": len({r.get("store_user_name") or r.get("business_account_name")
                       for r in rows
                       if (r.get("store_user_name") or r.get("business_account_name"))}),
        "retail_staff": len(retail), "whole_staff": len(wholesale),
    }
    return {"summary": summary, "stores": stores, "retail_staff": retail,
            "wholesale_staff": wholesale}


# ---------------------------------------------------------------- report

def money(v):
    return "{:,.2f}".format(v)


def rate_cls(v):
    return "pos" if v > 0 else ("neg" if v < 0 else "flat")


def store_rows(stores):
    out = []
    for i, s in enumerate(stores):
        kind = "批发" if s["whole_sale"] >= abs(s["retail_sale"]) else "零售"
        cls = "t-whole" if kind == "批发" else "t-retail"
        out.append(
            '<tr><td class="rk">%d</td><td class="nm">%s<span class="tag %s">%s</span></td>'
            '<td class="num strong">%s</td><td class="num">%s</td>'
            '<td class="num %s">%.1f%%</td><td class="num">%d</td>'
            '<td class="num">%d</td><td class="num">%d</td><td class="pd">%s</td></tr>'
            % (i + 1, s["name"], cls, kind, money(s["sale"]), money(s["gross"]),
               rate_cls(s["rate"]), s["rate"], s["qty"], s["bills"],
               s["staff"], s["top_product"]))
    return "\n".join(out)


def staff_rows(data):
    out = []
    for i, s in enumerate(data):
        out.append(
            '<tr><td class="rk">%d</td><td class="nm">%s</td>'
            '<td class="num strong">%s</td><td class="num">%s</td>'
            '<td class="num %s">%.1f%%</td><td class="num">%d</td>'
            '<td class="num">%d</td><td class="num">%d</td></tr>'
            % (i + 1, s["name"], money(s["sale"]), money(s["gross"]),
               rate_cls(s["rate"]), s["rate"], s["qty"], s["bills"], s["lines"]))
    return "\n".join(out)


CSS = """
*{box-sizing:border-box}html,body{margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;
background:#f6f7f9;color:#1f2329;line-height:1.6;font-size:14px;padding:32px 24px 56px}
.wrap{max-width:1120px;margin:0 auto}
.head{margin-bottom:24px}
h1{font-size:24px;font-weight:600;margin:0 0 6px;letter-spacing:-.2px}
.sub{color:#7a8088;font-size:13px;margin:0}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:24px 0 32px}
.kpi{background:#fff;border-radius:10px;padding:16px 18px;border:1px solid #e8eaed}
.kpi .lb{font-size:12px;color:#7a8088;margin:0 0 6px}
.kpi .vl{font-size:22px;font-weight:600;margin:0;letter-spacing:-.3px}
.kpi .ex{font-size:12px;color:#a0a5ab;margin:4px 0 0}
section{background:#fff;border:1px solid #e8eaed;border-radius:12px;padding:22px 24px 20px;margin-bottom:20px}
h2{font-size:17px;font-weight:600;margin:0 0 4px}
h2 .no{color:#378ADD;margin-right:6px}
.desc{color:#7a8088;font-size:13px;margin:0 0 20px}
h3{font-size:14px;font-weight:600;margin:24px 0 12px;color:#3d444d}
h3:first-of-type{margin-top:0}
.chartbox{position:relative;width:100%;margin-bottom:8px}
.legend{display:flex;gap:18px;font-size:12px;color:#7a8088;margin-bottom:10px}
.legend i{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:6px;vertical-align:-1px}
table{width:100%;border-collapse:collapse;font-size:13px}
th{text-align:left;font-weight:500;color:#7a8088;font-size:12px;padding:8px 10px;border-bottom:1px solid #e8eaed;white-space:nowrap}
td{padding:10px;border-bottom:1px solid #f1f2f4;vertical-align:middle}
tr:last-child td{border-bottom:none}
tbody tr:hover{background:#fafbfc}
.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.strong{font-weight:600}
.rk{width:34px;color:#a0a5ab;font-variant-numeric:tabular-nums}
tbody tr:nth-child(1) .rk{color:#BA7517;font-weight:600}
tbody tr:nth-child(2) .rk{color:#888780;font-weight:600}
tbody tr:nth-child(3) .rk{color:#993C1D;font-weight:600}
.nm{font-weight:500}
.tag{display:inline-block;font-size:11px;font-weight:400;padding:1px 6px;border-radius:4px;margin-left:8px;vertical-align:1px}
.t-retail{background:#E6F1FB;color:#185FA5}
.t-whole{background:#FAEEDA;color:#854F0B}
.pos{color:#A32D2D}.neg{color:#0F6E56}.flat{color:#7a8088}
.pd{color:#5f6670;font-size:12px;max-width:220px}
.note{background:#fafbfc;border-left:3px solid #d9dce0;padding:14px 18px;border-radius:0 8px 8px 0;font-size:13px;color:#5f6670}
.note ul{margin:6px 0 0;padding-left:18px}.note li{margin:4px 0}
.scroll{overflow-x:auto}
"""

HTML = """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
<style>__CSS__</style></head><body><div class="wrap">
<div class="head"><h1>__TITLE__</h1><p class="sub">__SUBTITLE__</p></div>
<div class="kpis">__KPIS__</div>
<section><h2><span class="no">01</span>门店销量排名</h2>
<p class="desc">按销售额降序。销货主体注明「批发 / 零售」；毛利率为负说明当日含亏本出货或退货冲减。</p>
<div class="legend"><span><i style="background:#378ADD"></i>销售额（元）</span><span><i style="background:#1D9E75"></i>成本毛利（元）</span></div>
<div class="chartbox" style="height:__H1__px"><canvas id="cStore" role="img" aria-label="各门店销售额与成本毛利横向条形图"></canvas></div>
<div class="scroll"><table><thead><tr><th>#</th><th>门店 / 主体</th><th class="num">销售额</th><th class="num">毛利</th>
<th class="num">毛利率</th><th class="num">销量</th><th class="num">单量</th><th class="num">出单人数</th><th>主力商品</th></tr></thead>
<tbody>__STORES__</tbody></table></div></section>
<section><h2><span class="no">02</span>人员销量排名</h2>
<p class="desc">零售门店由店员出单（store_user_name）、分销批发由业务员出单（business_account_name），岗位性质不同，分两张榜。</p>
<h3>2.1 零售店员榜（按销售额降序）</h3>
<div class="legend"><span><i style="background:#378ADD"></i>销售额（元）</span><span><i style="background:#1D9E75"></i>成本毛利（元）</span></div>
<div class="chartbox" style="height:__H2__px"><canvas id="cRetail" role="img" aria-label="零售店员销售额与毛利横向条形图"></canvas></div>
<div class="scroll"><table><thead><tr><th>#</th><th>店员</th><th class="num">销售额</th><th class="num">毛利</th>
<th class="num">毛利率</th><th class="num">销量</th><th class="num">单量</th><th class="num">明细行</th></tr></thead>
<tbody>__RETAIL__</tbody></table></div>
<h3>2.2 分销业务员榜（按销售额降序）</h3>
<div class="chartbox" style="height:__H3__px"><canvas id="cWhole" role="img" aria-label="分销业务员销售额与毛利横向条形图"></canvas></div>
<div class="scroll"><table><thead><tr><th>#</th><th>业务员</th><th class="num">销售额</th><th class="num">毛利</th>
<th class="num">毛利率</th><th class="num">销量</th><th class="num">单量</th><th class="num">明细行</th></tr></thead>
<tbody>__WHOLE__</tbody></table></div></section>
<section><h2>口径与说明</h2><div class="note"><ul>
<li><b>时间口径</b>：__RANGE__（制单日期，UTC+8）。</li>
<li><b>销售额</b>：sale_money，含退货负数冲减。</li>
<li><b>毛利</b>：成本毛利 = retail_cost_gross_profit + wholesale_cost_gross_profit，未计入销售返利。</li>
<li><b>毛利率</b>：毛利 ÷ 销售额。</li>
<li><b>单量</b>：按 bill_id 去重；同一单据多行明细合并计入同一门店/人员。</li>
<li><b>权限</b>：business_cost_*、tax_excluded_cost*、item_gross_profit、gift_cost 等字段返回 "***"，故毛利按成本毛利口径汇总。</li>
</ul></div></section>
</div>
<script>
const D=__DATA__;
const money=v=>v.toLocaleString('zh-CN',{minimumFractionDigits:2,maximumFractionDigits:2});
function hbar(id,l,s,g){new Chart(document.getElementById(id),{type:'bar',
 data:{labels:l,datasets:[{label:'销售额',data:s,backgroundColor:'#378ADD',borderRadius:4},
 {label:'成本毛利',data:g,backgroundColor:'#1D9E75',borderRadius:4}]},
 options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,
 plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>c.dataset.label+'：¥'+money(c.parsed.x)}}},
 scales:{x:{ticks:{color:'#7a8088',callback:v=>(v/1000)+'k'},grid:{color:'rgba(0,0,0,.05)'}},
 y:{ticks:{color:'#3d444d',font:{size:12}},grid:{display:false}}}}});}
hbar('cStore',D.stores.map(d=>d.name),D.stores.map(d=>d.sale),D.stores.map(d=>d.gross));
hbar('cRetail',D.retail.map(d=>d.name),D.retail.map(d=>d.sale),D.retail.map(d=>d.gross));
hbar('cWhole',D.whole.map(d=>d.name),D.whole.map(d=>d.sale),D.whole.map(d=>d.gross));
</script></body></html>
"""


def render(analysis, title, subtitle, range_text):
    s = analysis["summary"]
    stores, retail, whole = analysis["stores"], analysis["retail_staff"], analysis["wholesale_staff"]
    kpis = "".join([
        '<div class="kpi"><p class="lb">销售额</p><p class="vl">¥%s</p><p class="ex">%d 张单据</p></div>'
        % (money(s["sale"]), s["bills"]),
        '<div class="kpi"><p class="lb">销量</p><p class="vl">%d</p><p class="ex">%d 条明细</p></div>'
        % (s["qty"], s["lines"]),
        '<div class="kpi"><p class="lb">成本毛利</p><p class="vl">¥%s</p><p class="ex">毛利率 %.2f%%</p></div>'
        % (money(s["gross"]), s["rate"]),
        '<div class="kpi"><p class="lb">出货门店 / 主体</p><p class="vl">%d</p><p class="ex">含批发主体</p></div>'
        % s["stores"],
        '<div class="kpi"><p class="lb">出单人员</p><p class="vl">%d</p><p class="ex">店员 %d 人 + 业务员 %d 人</p></div>'
        % (s["people"], s["retail_staff"], s["whole_staff"]),
    ])
    html = (HTML
            .replace("__CSS__", CSS)
            .replace("__TITLE__", title)
            .replace("__SUBTITLE__", subtitle)
            .replace("__KPIS__", kpis)
            .replace("__STORES__", store_rows(stores))
            .replace("__RETAIL__", staff_rows(retail))
            .replace("__WHOLE__", staff_rows(whole))
            .replace("__RANGE__", range_text)
            .replace("__H1__", str(max(len(stores) * 40 + 80, 200)))
            .replace("__H2__", str(max(len(retail) * 40 + 80, 160)))
            .replace("__H3__", str(max(len(whole) * 40 + 80, 120)))
            .replace("__DATA__", json.dumps(
                {"stores": stores, "retail": retail, "whole": whole}, ensure_ascii=False)))
    return html


# ---------------------------------------------------------------- CLI

def main():
    ap = argparse.ArgumentParser(description="drbt retail MCP helper")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list")

    p_call = sub.add_parser("call")
    p_call.add_argument("tool")
    p_call.add_argument("--args", default="{}")

    for name in ("sales", "rank"):
        p = sub.add_parser(name)
        p.add_argument("--begin", required=True, help="YYYY-MM-DD")
        p.add_argument("--end", required=True, help="YYYY-MM-DD")
        p.add_argument("--bill-types", default="", help="e.g. 1,3")
        p.add_argument("--label", default="")
        p.add_argument("--out", default="")

    a = ap.parse_args()
    s = Session()
    s.open()

    if a.cmd == "list":
        for t in s.list_tools():
            print("-", t["name"], "|", (t.get("description") or "").splitlines()[0][:80])
        return

    if a.cmd == "call":
        print(json.dumps(s.payload(a.tool, json.loads(a.args)), ensure_ascii=False, indent=2))
        return

    bill_types = [int(x) for x in a.bill_types.split(",") if x.strip()] or None
    rows, total_row = fetch_rows(s, a.begin, a.end, bill_types)
    analysis = build_analysis(rows)

    if a.cmd == "sales":
        out = a.out or "sales_rows_%s_%s.json" % (a.begin, a.end)
        with open(out, "w", encoding="utf-8") as f:
            json.dump({"rows": rows, "total_row": total_row}, f, ensure_ascii=False)
        print("rows:", len(rows), "->", out)
        print("summary:", json.dumps(analysis["summary"], ensure_ascii=False))
        return

    label = a.label or ("%s ~ %s" % (a.begin, a.end) if a.begin != a.end else a.begin)
    now = datetime.datetime.now(TZ).strftime("%Y-%m-%d %H:%M")
    title = "销量排名分析 · %s" % label
    subtitle = "数据区间 %s（制单日期口径，UTC+8）· 共 %d 条明细 / %d 张单据 · 报告生成于 %s" % (
        label, analysis["summary"]["lines"], analysis["summary"]["bills"], now)
    html = render(analysis, title, subtitle, label)
    out = a.out or "销量排名_%s_%s.html" % (a.begin, a.end)
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print("written:", os.path.abspath(out))
    print(json.dumps(analysis["summary"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
