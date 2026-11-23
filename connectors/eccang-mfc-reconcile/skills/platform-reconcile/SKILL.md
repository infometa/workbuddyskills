---
name: platform-reconcile-router
description: >
  跨境电商结算账单「平台识别 + 对账入口」。当用户上传或给出结算账单文件
  （xlsx/xls/csv）却没说清是哪个平台、文件名也不带平台名，或一份文件可能混多平台时使用：
  抽样账单里的订单号调用 eccang-mfc-reconcile MCP queryOrderByReferenceNo，由易仓系统返回的 platform
  反向确定平台与店铺账号，再交由对应平台的对账技能执行。
  触发关键词：不知道是哪个平台、帮我看看这是什么账单、这个账单对一下、多平台结算文件、
  平台识别、判断平台、reconcile this statement、which platform。
  若用户已明确平台（如「这是 Walmart 结算单」），直接调用对应平台技能，不要用本技能。
license: Proprietary
compatibility: Requires Python 3.8+；xlsx 需要 openpyxl；需 eccang-mfc-reconcile MCP HTTPS 可访问（由本连接器内置提供）。
metadata:
  author: settle-team
  version: "1.0"
  role: router
---

# 平台识别与对账路由

## 这个技能解决什么

用户直接甩一个账单文件过来，**不说平台、文件名也没有平台线索**（如 `账单.xlsx`、
`20260826-20260925income.xlsx`）。此时不能靠猜——平台由易仓系统判定：
拿账单里的订单号去查 `queryOrderByReferenceNo`，返回的 `platform` 就是权威答案，
顺带还给出 `companyCode` / `userAccount`。

**原则：先判定，再对账。判不准就问，绝不硬跑。**

## Step 1 — 运行判定脚本

```bash
python "<本技能目录>/scripts/detect_platform.py" "<账单绝对路径>" --json
```

Windows 建议加 `-X utf8`：`python -X utf8 detect_platform.py "<路径>" --json`

输出示例：

```json
{
  "file": "账单A.xlsx",
  "orders_total": 204,
  "order_columns": ["Related order ID", "Order/adjustment ID"],
  "sampled": 12,
  "method": "mcp_vote",
  "confidence": "high",
  "platform": "tiktok",
  "companyCode": "nt3kqtg",
  "userAccount": "WeiloongSnackStore",
  "votes": {"tiktok": 10},
  "hit": 10,
  "miss": 2
}
```

关键字段：

| 字段 | 含义 |
|------|------|
| `platform` | 判定平台：tiktok / walmart / ebay / amazon；`AMBIGUOUS` 表示多平台并列；`UNKNOWN` 表示判不出 |
| `confidence` | `high`＝MCP ≥3 票且 ≥80% 一致；`medium`＝票数不足但表头指纹一致；`low`＝仅指纹或仅 1-2 票 |
| `companyCode` / `userAccount` | 命中样本的店铺众数，可直接用于后续 `queryProfitSettlement` |
| `method` | `mcp_vote` / `mcp_vote+header_fingerprint` / `header_fingerprint` / `none` |
| `votes` | 各平台票数，用于解释判定依据 |

退出码：`0` 判定成功｜`3` 歧义（多平台）｜`4` 无法判定。

## Step 2 — 按 platform 分发

| platform | 加载的对账技能（skill name） | 目录 |
|----------|------------------------------|------|
| `tiktok` | `tk-platform-reconcile` | `skills/tiktok-platform-reconcile/` |
| `walmart` | `walmart-platform-reconcile` | `skills/walmart-platform-reconcile/` |
| `ebay` | `ebay-platform-reconcile` | `skills/ebay-platform-reconcile/` |
| `amazon` | `amazon-reconciliation` | `skills/amazon-platform-reconcile/` |

分发时把判定结果一并带过去（省掉平台技能里"自己查店铺"那一步）：

- `companyCode` / `userAccount` / `platform` 直接作为店铺信息
- 若平台技能支持 `--shop-info`，把 `{"companyCode":..,"userAccount":..,"platform":..}` 传进去

## Step 3 — 判定异常时的处理

| 情况 | 退出码 | 处理方式 |
|------|--------|----------|
| `confidence = high/medium` | 0 | 直接进入 Step 2 |
| `confidence = low` | 0 | 进入 Step 2，但**先向用户确认一句**：「判定为 X 平台，是否正确？」 |
| `platform = AMBIGUOUS` | 3 | 列出 `votes` 让用户选；同时提示这份账单可能混了多个平台，建议拆分后分别对账 |
| `platform = UNKNOWN` | 4 | 请用户说明平台；并提示支持的四种格式特征（见下表） |

支持的格式特征（排查用）：

| 平台 | 表头/结构特征 |
|------|---------------|
| TikTok Shop | Sheet `Order details`，含 `Related order ID`、`Total settlement amount` |
| Walmart | Sheet 含「结算单」或表头含 `Purchase Order #` + `Transaction Key` + `Amount Type` |
| eBay | 表头含 `Order number` + `Legacy order ID` + `Net amount`（Transaction Report） |
| Amazon | 表头含 `id do pedido` / `amazonOrderId` + `tipo`（葡语导出）或 `type` + `total` |

## 硬性规则

1. **禁止跳过判定直接对账**。判错平台会跑出满屏假差异，比不跑更糟。
2. **禁止 SQL、禁止直连数据库**。所有业务数据只来自 eccang-mfc-reconcile MCP。
3. 判定脚本只读表头与订单号列，**不读金额、不做对账**；对账由平台技能负责。
4. 脚本输出的 `platform` 是易仓系统的事实，不要用文件名的字面意思去推翻它。

## 常见问题

| 问题 | 原因 / 处理 |
|------|-------------|
| `hit` 为 0 或很少 | 订单在易仓侧未同步（新店铺/时差），脚本会自动扩样；仍不足 3 票时看 `confidence` 决定是否需要用户确认 |
| 脚本报「文件不存在」 | 路径含中文/空格/括号时用双引号包裹，并传绝对路径 |
| `order_columns` 为空 | 表头没识别到订单号列，检查表头是否在第 40 行以内，或让用户确认文件是否为标准导出 |
| 报 openpyxl 缺失 | 仅 xlsx 需要：`pip install openpyxl`（获用户确认后执行） |
