---
name: drbt-retail-insight
description: Query and analyse the drbt (drumbeatsoft) SaaS retail ERP / 进销存 data — sales revenue, cost-based gross profit, gross margin, inventory quantity, and store/staff sales rankings — and render them as a single-file HTML dashboard. This skill should be used when the user asks about 销售额 / 毛利 / 毛利率 / 库存数量 / 销量排名 / 门店排名 / 店员业绩 / 业务员业绩 for the 影石 Insta360 retail chain (郑州、武汉、洛阳、南阳、新乡、太原、宜昌 等门店), or whenever a task needs the drbt-retail-insight tools 销售明细表查询 / 进销存报表 — including when those tools have dropped out of the tool registry mid-session, which this skill recovers from by talking to the MCP endpoint directly.
---

# drbt 零售数据洞察

查询 drbt（api.drumbeatsoft.com）SaaS 零售进销存数据，做销量 / 毛利 / 库存分析与排名报告。

## 核心原则

**优先用注册表里的 MCP 工具**（`ToolSearch` 找 `销售明细表查询` / `进销存报表`，再 `DeferExecuteTool` 调用）。

**但这两个工具会在会话中途从工具注册表掉线** —— 表现为 `ToolSearch` 搜不到、`DeferExecuteTool` 返回 `Tool not found`，重试无效。此时**不要放弃、不要回复用户「无法查询」**，改用本 skill 的 `scripts/` 直连 MCP 端点。已验证该通道长期可用。

## 何时加载本 skill

- 用户问销售额、毛利、毛利率、库存数量、销量排名、门店 / 人员业绩
- 用户提到零售进销存，或提到郑东万象城、大卫城、胖东来、万象城、正弘汇等门店名
- `ToolSearch` 找不到 `销售明细表查询` / `进销存报表`

## 用法

统一用托管 Python，并设置 UTF-8 输出（否则中文在 Windows 控制台会乱码）：

```bash
PYTHONIOENCODING=utf-8 "<managed-python>" <skill>/scripts/drbt.py <command> [args]
```

托管 Python 路径：`C:/Users/11691/.workbuddy/binaries/python/versions/3.13.12/python.exe`

### 命令

```bash
# 1. 探活 + 列出可用工具（工具掉线时也用它确认服务端还活着）
drbt.py list

# 2. 原始调用任意工具，args 为 JSON 字符串
drbt.py call 销售明细表查询 --args '{"page_num":1,"page_size":1,"filter":{...}}'

# 3. 导出区间内全部明细到 JSON（含 total_row 全局汇总）
drbt.py sales --begin 2026-09-01 --end 2026-09-17 --out rows.json

# 4. 生成排名报告 HTML（门店榜 + 店员榜 + 业务员榜）
drbt.py rank --begin 2026-09-17 --end 2026-09-17 --out 今日销量排名.html
drbt.py rank --begin 2026-09-01 --end 2026-09-17 --label "9月至今" --out 9月排名.html
```

`--begin` / `--end` 是本地日期（UTC+8），脚本自动换算成接口要的毫秒时间戳（**制单日期**口径）。
`--bill-types 1,3` 可只取零售 + 批发（排除退货）。`--label` 用于报告标题与口径说明。

### 报告生成后

用 `present_files` 展示生成的 HTML（单文件看板：KPI + 横向条形图 + 明细表 + 口径说明）。

## 关键领域知识

### 字段与权限陷阱

一半的成本 / 毛利字段被权限掩码成 `"***"`，**不能直接用**。可用的只有：

| 口径 | 零售 | 批发 |
|---|---|---|
| 销售成本 | `retail_cost_money` | `wholesale_cost_money` |
| 成本毛利 | `retail_cost_gross_profit` | `wholesale_cost_gross_profit` |

被掩码（返回 `"***"`）：`business_cost_money`、`business_cost_gross_profit`、`tax_excluded_cost`、`tax_excluded_cost_gross_profit`、`item_gross_profit`、`gift_cost`、`wholesale_rebate_profit_money`。

**计算口径**：
- 销售成本 = 零售成本 + 批发成本
- 毛利 = 零售毛利 + 批发毛利
- 毛利率 = 毛利 ÷ `sale_money`（不含返利口径；若要含返利，分母换成 `after_rebate_sale_money`）

### total_row 是全局汇总

返回体 `data.total_row` 是**整个筛选区间的汇总**，不是当前页。所以 `page_size=1` 一次调用就能拿到总额与总成本，**不必翻页聚合** —— 汇总类问题优先用这招，能省掉大量往返。

**例外（已实测）**：一旦带上 `bill_type_list` 过滤，返回体里**不再有 `total_row` 字段**；该票种无数据时 `total_row` 可能为 `null`。所以按票种拆分汇总时要 `r["data"].get("total_row")` 兜底，缺失就退回拉明细自行加总。整体汇总（不带 `bill_type_list`）不受影响。

### bill_type_list

`1` 零售、`2` 零售退、`3` 批发（分销出库）、`4` 批发退。退货行走负数，直接加总即得净额。

### 出货主体 ≠ 零售门店

`institution_name` 里既有零售门店（郑州郑东万象城、洛阳大卫天地…），也有**批发主体**（河南强视公司、武汉强视公司）。做「门店排名」时必须标注批发 / 零售，否则批发主体会霸榜且与门店不可比。

### 人员维度是两种岗位

- `store_user_name`：零售门店店员（只有零售 / 零售退单有值）
- `business_account_name`：分销业务员（只有批发 / 批发退单有值）

二者岗位不同，**分两张榜**，不要混在一张榜里排。

### 进销存报表只给数量

`进销存报表` 的金额字段（`purchase_in_money`、`sale_out_money`、`end_business_cost_money` 等）**几乎全部被掩码为 `"***"`**，只有数量（`begin_qty` / `end_qty` / `sale_out_qty` …）可用。查库存数量用它；查金额 / 毛利一律走 `销售明细表查询`。

库存的期初 / 期末关系：`end_qty = begin_qty + 各口径入库 − 各口径出库`，用它交叉校验结果。

## 环境注意

- 本机 shell 是残缺的 PortableGit：**没有** `date`、`ls`、`head`、`sleep`、`rm` 等 coreutils。文件操作一律用 Read / Write / Glob / Grep 工具，或直接用 Python 的 `os` / `shutil`。
- Python 无 `tzdata`，时区必须用 `datetime.timezone(datetime.timedelta(hours=8))`，不要用 `zoneinfo`。
- 中文输出前设置 `PYTHONIOENCODING=utf-8`。

## 详细参考

- `references/mcp-direct-connection.md` — MCP 直连协议细节、配置位置、排障步骤
- `references/data-fields.md` — 完整字段清单与语义
