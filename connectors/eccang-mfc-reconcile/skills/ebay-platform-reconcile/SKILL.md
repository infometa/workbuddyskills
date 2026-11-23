---
name: ebay-platform-reconcile
description: eBay 平台结算单对账工具。用户提供 eBay Transaction Report CSV 文件路径，工具自动完成两阶段对账：1）提取账期、过滤 Payout/Hold、按 Order number 汇总 Net amount（空订单号归为 other）；2）通过 eccang-mfc-reconcile MCP 工具查询订单归属与结算利润明细，逐条比对输出汇总信息和差异明细。数据一律走 MCP，禁止 SQL、禁止直连数据库。账单特征：CSV 含 Order number + Legacy order ID + Net amount。当用户提到 eBay 对账、ebay settlement、ebay transaction report、ebay reconciliation 等场景时使用本技能。平台未确认时先用 platform-reconcile-router 技能判定。
compatibility: Requires Python 3.8+, openpyxl, eccang-mfc-reconcile 可访问
metadata:
  author: sicnlee
  version: "2.0"
  platform: ebay
---

# eBay 对账工具

## Step 0 — 平台自检（执行前必做）

本技能**只处理 eBay 账单**。动手前先确认文件确实是 eBay Transaction Report：

- 特征：CSV，表头含 `Order number` + `Legacy order ID` + `Net amount`，`Type` 列含 `Order` / `Payout` / `Hold`
- 表头通常不在第 1 行（前面有 Notes / Gross transaction amount 等说明行），文件编码可能是 GB18030

**若文件不是 eBay 账单，立即停止**——不要执行本技能脚本、不要输出对账结果。改由
`platform-reconcile-router` 技能判定平台，再分发到对应平台技能。跑错平台会产出满屏假差异。

## 🚫 硬性规则：禁止 SQL 查询（最高优先级）

本 skill 执行期间 **禁止** 执行任何 SQL 语句、**禁止** 直连数据库。
所有业务数据 **必须且只能** 通过 eccang-mfc-reconcile MCP 获取（脚本内置 MCP 客户端，自动连接连接器配置的 nexus 服务）。

## 完整对账流程

当用户提供一份 eBay Transaction Report CSV 文件路径后，按以下流程执行对账：

### 步骤一：提取明细数据

运行 `ebay_duizhang.py` 提取明细：

```bash
python scripts/ebay_duizhang.py <csv文件路径>
```

- 从 CSV 元数据行提取 `Start date` → start_time，`End date` → end_time，格式 `yyyy-MM-dd HH:mm:ss`
- 定位 `Transaction creation date` 所在行为真正表头，删除上方元数据
- 过滤掉 Type 为 `Payout`、`Hold` 的行
- 保留 `Order number` 和 `Net amount` 两列
- Order number 为空或 `--` 时标记为 `other`
- 输出到原文件同目录 `<原文件名>_明细.xlsx`

### 步骤二：查询订单归属并确认

运行 `ebay_compare.py` 执行完整比对（非交互环境自动跳过人工确认）：

```bash
python scripts/ebay_compare.py <csv文件路径> -y
```

- 从明细中取一个有效 Order number（非空、非 `--`、非 `other`）
- 调用 MCP 工具 `queryOrderByReferenceNo` 查询订单归属，返回 `companyCode` / `userAccount` / `platform`
- 将查询结果展示给用户确认（交互终端）；非交互环境或 `-y/--yes` 时自动跳过
- 若用户反馈信息不正确，用参数显式指定客户和店铺（跳过 MCP 归属查询与确认）：
  ```bash
  python scripts/ebay_compare.py <csv文件路径> --company-code ntz0gd9 --user-account texas_truck_parts --platform ebay
  ```

### 步骤三：查询结算利润明细并比对

- 调用 MCP 工具 `queryProfitSettlement`，入参 `companyCode` / `userAccount` / `platform` / `startTime` / `endTime`（账期取自 CSV 元数据）
- 比对口径（与历史 SQL 口径一致，由脚本在 MCP 返回上执行）：
  - `account_check_result IN ('匹配到订单', '订单已作废', '对账成功')`，`source_type = 1` 由 MCP 服务端过滤
  - 空 `orderId` 归为 `other`；同一订单多种状态时优先取非「订单已作废」的记录并累加
- 按 `Order number`（Excel）vs `orderId`（MCP）汇总比对
- 比对规则：
  - Excel 金额为 0 且 MCP 无记录 → 忽略，不计入差异
  - `other` 直接对比值，不做单订单复核
  - 其他订单仅在 Excel 中时，用已取回的明细复核「匹配到订单」口径的单订单金额
  - 金额差异容差：0.01

### 步骤四：输出结果

**控制台输出格式：**

```
======================================================================
项目              	值
----------------------------------------
客户              	ntz0gd9
店铺              	texas_truck_parts
平台              	ebay
对账时间            	2026-03-01 00:00:00 ~ 2026-03-31 23:59:59
Excel订单数        	435
MCP订单数          	432
Excel总金额        	39,515.47
MCP总金额          	39,515.47
差异              	0 条
匹配结果            	完全一致
======================================================================
```

若有差异，紧接着输出差异明细：
```
差异明细（共 N 条）：
order_id                             excel_fee_amount    mcp_fee_amount 备注
------------------------------------------------------------------------------------------
other                                       -126.00              — 仅在Excel中(MCP无记录)
```

**差异类型说明：**
- **仅在Excel中(MCP无记录)** — MCP 结算利润中该订单无匹配记录
- **仅在结算利润中** — Excel 中无此订单
- **金额不一致** — 同一订单两边金额差异 > 0.01

**导出文件：**

在原文件同目录生成 `<原文件名>_比对结果.xlsx`，最多包含 4 个 sheet：
- **汇总信息** — 客户、店铺、平台、对账时间、订单数、总金额、差异条数、匹配结果
- **差异明细** — 顶部含汇总信息，下方为差异订单列表
- **订单已作废** — 存在作废订单时生成
- **全量比对** — 顶部含汇总信息，下方为全部订单比对结果

## 文件格式要求

- 支持 eBay Transaction Report CSV 格式
- CSV 前若干行为元数据（Notes、Seller、Start date、End date 等）
- 真正表头行以 `Transaction creation date` 开头
- 必需列（大小写敏感）：
  - `Type` — 交易类型（Payout、Hold 会被过滤）
  - `Order number` — 订单号（空值归为 other）
  - `Net amount` — 净金额
- 日期格式支持中文月份（如 `3月-01-2026`）和英文（如 `Mar-01-2026`）

## MCP 服务配置

订单归属与结算利润明细全部通过 eccang-mfc-reconcile 提供的 MCP 工具获取，脚本不直连数据库，也不内置任何库表 SQL 与账号口令。

- 默认地址：`https://datacenter.eccang.com/nexus/mcp/stream`（经网关访问，无需 token）
- 覆盖方式：命令行 `--mcp-url <地址>`，或环境变量 `NEXUS_MCP_URL`
- 连通性自检：
  ```bash
  python scripts/ebay_mcp.py --list-tools
  ```

安装依赖：
```bash
pip install openpyxl
```

## 错误处理

| 错误提示 | 原因 | 解决方法 |
|---|---|---|
| 文件不存在 | 路径错误 | 检查文件路径是否正确 |
| 未找到 Transaction creation date 表头行 | CSV 格式异常 | 确认文件为 eBay Transaction Report |
| 未找到 Start date / End date | 元数据缺失 | 确认 CSV 包含账期信息 |
| 未找到列 Type/Order number/Net amount | 列名不匹配 | 检查表头列名 |
| 未提取到有效 Order number | 订单号全为空/other | 用 `--company-code` / `--user-account` 指定对账主体 |
| 订单号在 MCP 中未找到 | 订单不在 ERP 中 | 确认订单号正确，或用 `--company-code` / `--user-account` 指定 |
| MCP 服务不可达 | 地址错误或网络不通 | 检查 `--mcp-url` / `NEXUS_MCP_URL` 与网络连通性 |
| MCP 工具执行失败 | eccang-mfc-reconcile 侧查询异常 | 查看工具返回的错误信息，确认客户/店铺/账期是否有效 |
