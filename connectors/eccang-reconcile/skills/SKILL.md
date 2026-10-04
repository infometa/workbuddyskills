---
name: eccang-reconcile-skill
description: 易仓跨境平台账单对账技能 - 通过 nexus MCP 获取店铺信息与结算明细，核对 TikTok Shop / Tokopedia 结算 Excel 并输出差异报告
version: "1.0.0"
author: "Eccang"
---

# 易仓跨境平台账单对账 Skill

把一份平台导出的结算 Excel 丢给 AI，自动核对「平台账单」与「易仓结算数据」，输出差异明细和 Excel 对账报告。
覆盖平台：TikTok Shop、Tokopedia（同一套结算导出格式，platform 由 MCP 返回自动判定）。

## 认证说明（免鉴权）

- 本 Connector **无需用户授权**：MCP 服务为易仓内部服务，连接即可调用，不弹浏览器、不填 Token。
- 若工具调用报鉴权/网络错误：确认当前网络能否访问 `datacenter.eccang.com`（内网/VPN），仍失败则提示联系易仓数据中心管理员。
- 所有数据一律走 MCP 工具获取，**禁止** 直连数据库、禁止执行 SQL、禁止读取任何数据库配置文件。

## 可用工具

工具名前缀为 `mcp__eccang-reconcile__`（随 Connector 的 MCP Server key 走）。调用前先用 ToolSearch 加载工具 schema，确认参数后再执行。

### 1. queryOrderByReferenceNo — 按订单号查店铺/客户信息

根据 Excel 中任意一个订单号，反查该店铺的 companyCode / userAccount / platform。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| orderId | string | ✅ | 平台订单号，取自 Excel 的 `Related order ID` 列（取第一个非空、不以 `/` 开头的值） |

返回示例：

```json
{"code":"200","data":[{"companyCode":"ntwfswp","userAccount":"SOKINTOOL3631","platform":"tiktok"}]}
```

### 2. queryProfitSettlement — 按账期查结算明细

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| companyCode | string | ✅ | 客户代码，来自工具 1 |
| userAccount | string | ✅ | 店铺账号，来自工具 1 |
| platform | string | ✅ | 平台标识（tiktok / tokopedia），来自工具 1 |
| startTime | string | ✅ | 账期开始，格式 `YYYY-MM-DD 00:00:00` |
| endTime | string | ✅ | 账期结束，格式 `YYYY-MM-DD 23:59:59` |

单条记录结构：`{"orderId":"582361381117134105","settlementAmount":618020.0,"accountCheckResult":"匹配到订单"}`

> 返回结果可能很大：把完整 JSON 落盘到临时文件（如 `settlement.json`），再交给对账脚本读取，不要直接塞进对话。

## 执行流程

### Step 1 — 拿到 Excel 文件

| 情况 | 处理方式 |
|------|---------|
| 用户直接上传/粘贴了文件路径 | 直接进入 Step 2 |
| 消息里只有附件（URL / base64 / downloadCode） | 先下载或解码到本地临时目录，再进 Step 2 |
| 什么都没有 | 回复：请直接发送 .xlsx 附件，或告诉我文件的完整路径 |

### Step 2 — 解析 Excel，得到账期

按「Excel 解析规则」读取文件，得到：
- `start_time` / `end_time`（账期，用于 Step 3 的 MCP 入参）
- Excel 侧订单数、总结算金额
- 一个有效订单号（用于 Step 3 的工具 1）

### Step 3 — 调用 MCP 取数

1. 用 Step 2 取到的订单号调用 `queryOrderByReferenceNo` → 得到 companyCode / userAccount / platform。
2. 用「店铺信息 + Step 2 的账期」调用 `queryProfitSettlement` → 完整 JSON 落盘为 `settlement.json`。

> 结算明细只需按店铺 + 账期查一次，不要逐单调用。

### Step 4 — 执行对账

按「对账规则」比对两侧数据，统计订单数、总金额、差异条数、自动补齐条数。
可直接复用文末「附录：对账脚本参考实现」：把脚本写到临时文件，用真实参数执行。

### Step 5 — 回显摘要并询问是否导出报告

把控制台摘要原样回复给用户（模板见 references 输出格式）：

```
============================================================
  🎉🎊 对账结果：完全匹配！恭喜恭喜！太棒了！
============================================================
  客户代码    ：ntwfswp
  店    铺    ：SOKINTOOL3631
  平    台    ：tiktok
  账单开始时间：2026-02-01 00:00:00
  账单结束时间：2026-02-28 23:59:59
  Excel 订单总数    ：1683
  MCP 结算订单总数  ：1683
  Excel 总结算金额  ：35068361
  MCP 总结算金额    ：35068361

  ✅ 所有订单金额完美匹配，账单核对无误！
============================================================
```

有差异时输出「存在差异」版摘要（含自动补齐订单数、差异条数），并附 Top 差异订单。
随后询问：是否需要把完整对账报告（Excel）发给你？报告含 对账摘要 / 差异明细 / Excel明细 / MCP结算明细 四个 Sheet。

## Excel 解析规则

- Sheet 名固定为 `Order details`。
- 关键列：`Related order ID`（订单号）、`Total settlement amount`（结算金额）、`Order settled time`（结算时间，格式 `YYYY/MM/DD`）。
- 订单号为空或以 `/` 开头的行跳过；同一订单号金额累加。
- 账期：取所有 `Order settled time` 的最小值所在月份 → `start_time = 该月 1 日 00:00:00`，`end_time = 该月最后一天 23:59:59`。

## 对账规则

| 场景 | 处理方式 |
|------|---------|
| 两侧金额一致 | 匹配 ✅ |
| 金额不一致 | 差异：`金额差异`（记录 Excel 金额、MCP 金额、差值） |
| Excel 有、MCP 无（金额 ≠ 0） | 差异：`Excel有/MCP无` |
| Excel 有、MCP 无（金额 = 0） | 自动补齐，按匹配处理 ✅ |
| MCP 有、Excel 无 | 差异：`MCP有/Excel无` |

MCP 结算明细过滤：只统计 `accountCheckResult` 为空或属于白名单 `匹配到订单 / 订单已作废 / 对账成功` 的记录，其余（如未匹配、已冲销）不参与对账。

完全匹配的判定：订单总数一致 且 总金额一致 且 差异条数为 0。

## 注意事项

- 金额统一按整数处理（平台导出的最小货币单位），比较前转 int。
- 单次结算查询数据量可能上万条，务必落盘再处理，避免上下文溢出。
- 禁止为了取数去写 SQL 或翻数据库配置，数据只来自上述两个 MCP 工具。
- 用户问「为什么这笔不一样」时，用 `queryProfitSettlement` 的原始记录解释（结算状态、金额来源），不要臆测。

## 常见问题

| 问题 | 处理 |
|------|------|
| 文件不存在 / 路径无效 | 提示确认路径后重试 |
| Sheet 名不是 `Order details` | 提示确认是否为平台标准导出格式 |
| `queryOrderByReferenceNo` 未返回店铺信息 | 提示确认 Excel 中的订单号是否有效 |
| `queryProfitSettlement` 返回为空 | 提示确认店铺信息与账期是否正确 |
| MCP 工具不可用 / 超时 | 确认 `datacenter.eccang.com` 可达（内网/VPN），仍失败联系易仓数据中心 |

## 附录：对账脚本参考实现

Connector 只分发 Skill 文档，脚本由 Agent 在会话中写入临时文件后执行（依赖 `openpyxl`）。
用法：`python reconcile.py <excel> <shop_info.json> <settlement.json> [out.xlsx]`

```python
# -*- coding: utf-8 -*-
"""TK 平台账单对账（精简版）。店铺信息与结算明细均由 MCP 工具获取后落盘传入。"""
import sys, json, calendar
from datetime import datetime
from collections import defaultdict
import openpyxl

ALLOWED_CHECK_RESULTS = ("匹配到订单", "订单已作废", "对账成功")


def read_excel(path):
    ws = openpyxl.load_workbook(path)["Order details"]
    rows = list(ws.iter_rows(values_only=True))
    h = rows[0]
    find = lambda f: next(i for i, x in enumerate(h) if x and f(str(x)))
    i_oid = find(lambda s: "Related order ID" in s)
    i_amt = find(lambda s: s.strip() == "Total settlement amount")
    i_tm = find(lambda s: s.strip() == "Order settled time")

    data = defaultdict(lambda: {"amount": 0, "t": None})
    for r in rows[1:]:
        oid = r[i_oid]
        if oid is None:
            continue
        s = str(oid).strip()
        if not s or s.startswith("/"):
            continue
        try:
            data[s]["amount"] += int(r[i_amt]) if r[i_amt] is not None else 0
        except Exception:
            pass
        t = str(r[i_tm]).strip() if r[i_tm] else None
        if t and (data[s]["t"] is None or t > data[s]["t"]):
            data[s]["t"] = t

    dates = [v["t"] for v in data.values() if v["t"]]
    d0 = datetime.strptime(min(dates), "%Y/%m/%d")
    last = calendar.monthrange(d0.year, d0.month)[1]
    start = "%d-%02d-01 00:00:00" % (d0.year, d0.month)
    end = "%d-%02d-%02d 23:59:59" % (d0.year, d0.month, last)
    return data, start, end


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        d = json.load(f)
    return d.get("data") if isinstance(d, dict) and "data" in d else d


def load_shop(path):
    d = load_json(path)
    d = d[0] if isinstance(d, list) and d else d
    return (str(d.get("companyCode") or "").strip(),
            str(d.get("userAccount") or "").strip(),
            str(d.get("platform") or "").strip())


def load_settlement(path):
    rows = load_json(path)
    out = defaultdict(int)
    for r in rows:
        if not isinstance(r, dict):
            continue
        res = str(r.get("accountCheckResult") or "").strip()
        if res and res not in ALLOWED_CHECK_RESULTS:
            continue
        oid = str(r.get("orderId") or "").strip()
        if not oid:
            continue
        try:
            out[oid] += int(float(r["settlementAmount"])) if r.get("settlementAmount") is not None else 0
        except Exception:
            pass
    return out


def compare(excel_data, mcp_data):
    diffs, auto = [], []
    for oid, v in excel_data.items():
        amt = v["amount"]
        if oid in mcp_data:
            if amt != mcp_data[oid]:
                diffs.append([oid, amt, mcp_data[oid], amt - mcp_data[oid], "金额差异"])
        elif amt == 0:
            mcp_data[oid] = 0
            auto.append(oid)
        else:
            diffs.append([oid, amt, None, None, "Excel有/MCP无"])
    for oid, amt in mcp_data.items():
        if oid not in excel_data:
            diffs.append([oid, None, amt, None, "MCP有/Excel无"])
    return diffs, auto


def report(out_path, shop, period, ex_rows, mcp_rows, ex_amt, mcp_amt, auto, diffs,
           excel_data, mcp_data):
    code, account, platform = shop
    start, end = period
    matched = ex_rows == mcp_rows and ex_amt == mcp_amt and not diffs

    print("=" * 60)
    print("  🎉🎊 对账结果：完全匹配！" if matched else "  😢😔 对账结果：存在差异，需要核查...")
    print("=" * 60)
    print("  客户代码    ：%s" % code)
    print("  店    铺    ：%s" % account)
    print("  平    台    ：%s" % platform)
    print("  账单开始时间：%s" % start)
    print("  账单结束时间：%s" % end)
    print("  Excel 订单总数    ：%d" % ex_rows)
    print("  MCP 结算订单总数  ：%d" % mcp_rows)
    print("  Excel 总结算金额  ：%d" % ex_amt)
    print("  MCP 总结算金额    ：%d" % mcp_amt)
    print("  自动补齐订单数    ：%d" % len(auto))
    print("  差异条数          ：%d" % len(diffs))
    print("=" * 60)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "对账摘要"
    for row in [["对账摘要"], [],
                ["start_time", start], ["end_time", end], [],
                ["客户代码", code], ["店铺", account], ["平台", platform], [],
                ["", "Excel", "MCP结算", "是否一致"],
                ["订单总数", ex_rows, mcp_rows, "✅" if ex_rows == mcp_rows else "❌"],
                ["总结算金额", ex_amt, mcp_amt, "✅" if ex_amt == mcp_amt else "❌"],
                ["自动补齐订单数", len(auto), "", ""],
                ["差异条数", len(diffs), "", "✅" if not diffs else "❌"], [],
                ["对账结论", "🎉 完全匹配，账单核对无误！" if matched else "😢 存在差异，详见【差异明细】"]]:
        ws.append(row)

    wd = wb.create_sheet("差异明细")
    wd.append(["orderId", "Excel金额", "MCP金额", "差值", "差异类型"])
    for d in diffs:
        wd.append(["" if v is None else v for v in d])

    we = wb.create_sheet("Excel明细")
    we.append(["orderId", "settlementAmount", "order_settled_time"])
    for oid, v in sorted(excel_data.items(), key=lambda x: -x[1]["amount"]):
        we.append([oid, v["amount"], v["t"] or ""])

    wm = wb.create_sheet("MCP结算明细")
    wm.append(["orderId", "settlementAmount"])
    for oid, amt in sorted(mcp_data.items(), key=lambda x: -x[1]):
        wm.append([oid, amt])

    wb.save(out_path)
    print("\n📄 对账结果已输出：%s" % out_path)


def main():
    excel, shop_f, settle_f = sys.argv[1], sys.argv[2], sys.argv[3]
    out = sys.argv[4] if len(sys.argv) > 4 else excel.rsplit(".", 1)[0] + "_reconcile_result.xlsx"

    excel_data, start, end = read_excel(excel)
    shop = load_shop(shop_f)
    mcp_data = load_settlement(settle_f)
    diffs, auto = compare(excel_data, mcp_data)

    report(out, shop, (start, end),
           len(excel_data), len(mcp_data),
           sum(v["amount"] for v in excel_data.values()), sum(mcp_data.values()),
           auto, diffs, excel_data, mcp_data)


if __name__ == "__main__":
    main()
```
