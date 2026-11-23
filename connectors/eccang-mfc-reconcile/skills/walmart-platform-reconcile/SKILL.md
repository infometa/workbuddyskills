---
name: walmart-platform-reconcile
description: Walmart 平台结算单对账工具。用户提供 Walmart 结算 CSV 或 Excel 文件路径，工具自动识别结算数据所在 sheet（一般叫“结算单”），按账期切分（一个文件可含多个账期），再通过 MCP 工具（eccang-mfc-reconcile）查询订单归属与结算利润明细。逐账期比对用于统计与定位，最终差异按订单跨账期合并后判定：同一订单可能出现在多个账期（增量结算），只有合并后金额仍对不上的才是真实差异。账单特征：表头含 Purchase Order # + Transaction Key + Amount Type。当用户提到 Walmart 对账、walmart settlement、walmart reconciliation 等场景时使用本技能。平台未确认时先用 platform-reconcile-router 技能判定。
compatibility: Requires Python 3.8+, openpyxl, eccang-mfc-reconcile 可访问
metadata:
  author: sicnlee
  version: "1.2"
  platform: walmart
---

# Walmart 对账工具

## Step 0 — 平台自检（执行前必做）

本技能**只处理 Walmart 结算单**。动手前先确认文件确实是 Walmart 导出：

- 特征：CSV 或 xlsx，表头含 `Purchase Order #` + `Transaction Key` + `Amount` + `Amount Type`，
  常见 `Transaction Type` 值 `Sale` / `Refund` / `PaymentSummary`
- 结算数据所在 sheet 一般叫「结算单」，但**也可能不在第一个 sheet**，需按表头扫描定位

**若文件不是 Walmart 结算单，立即停止**——不要执行本技能脚本、不要输出对账结果。改由
`platform-reconcile-router` 技能判定平台，再分发到对应平台技能。跑错平台会产出满屏假差异。

## 完整对账流程

当用户提供一份 Walmart 结算文件路径（CSV 或 XLSX）后，按以下流程执行对账：

### 步骤一：识别 sheet 并提取订单明细

运行 `walmart_duizhang.py` 提取订单明细：

```bash
python scripts/walmart_duizhang.py <文件路径>
```

- **识别结算数据所在 sheet**：逐个 sheet 查找表头（含全部必需列），优先取名字像「结算单」的 sheet；文件不在第一个 sheet 放数据也支持
- **按账期切分**：`Total Payable` 为数字且 `Period Start/End Date` 可解析的行是账期汇总行，其后的 `Transaction Key` 非空行归属于该账期；**一个文件可包含多个账期，全部纳入**
- 忽略无 `Transaction Key` 的费用行（如 Fee/Reimbursement，它们自带 Period 日期，但不属于订单明细）与块之间重复出现的表头行
- 输出订单明细到原文件同目录 `<原文件名>_订单明细.xlsx`（含账期列）

### 步骤二：查询订单归属并确认

运行 `walmart_compare.py` 执行完整比对：

```bash
python scripts/walmart_compare.py <文件路径>
```

- 先识别结算数据所在 sheet：不在第一个 sheet、或存在多个候选 sheet 时**提示用户确认**；确认后仍无法对账会自动改用其它候选 sheet；也可直接指定：
  ```bash
  python scripts/walmart_compare.py <文件路径> --sheet 结算单
  ```
  查看各 sheet 的探测结果（哪个能作为结算数据源）：
  ```bash
  python scripts/walmart_compare.py <文件路径> --list-sheets
  ```
- 取一个有效 `Purchase Order #`（纯数字），调用 MCP 工具 `queryOrderByReferenceNo` 查询订单归属，返回 `companyCode` / `userAccount` / `platform`
- **将查询结果展示给用户确认**，用户确认正确后才继续执行
- 若用户反馈信息不正确，用参数显式指定客户和店铺（跳过 MCP 查询与确认）：
  ```bash
  python scripts/walmart_compare.py <文件路径> --company-code ntwfswp --user-account HOADE --platform walmart
  ```
- 非交互环境（无终端）自动跳过确认，也可用 `-y/--yes` 显式跳过

### 步骤三：逐账期查询结算利润明细并比对

- 对**每个账期**调用 MCP 工具 `queryProfitSettlement`，入参 `companyCode` / `userAccount` / `platform` / `startTime`（= 该账期 start）/ `endTime`（= 该账期 end）
- 工具内部查询条件（由 eccang-mfc-reconcile 维护，脚本不内置 SQL）：
  - `source_type = 1`
  - **时间条件按平台区分**：`platform` 非空且为 `walmart` 时按报告期间过滤（`period_start_date >= startTime` 且 `period_end_date <= endTime`），此时 `startTime` / `endTime` 是**日期粒度**（`yyyy-MM-dd`，服务端不补时分秒）；其它平台沿用 `statement_time` 区间（纯日期会补全为当天 `00:00:00` / `23:59:59`）
  - `account_check_result IN ('匹配到订单', '订单已作废', '对账成功')`
  - 按 `order_id, account_check_result` 汇总 `settlementAmount`
- 按账期分别比对 `Purchase Order #`（Excel）vs `orderId`（MCP）；同一订单返回多条对账结果时，优先取非「订单已作废」的记录并累加
- 比对规则：
  - Excel 金额为 0 且 MCP 无记录 → 忽略，不计入差异
  - Excel 有记录但 MCP 无记录且金额不为 0 → 记为「仅在Excel中」
  - 金额差异容差：0.01
- **关键：逐期比对只用于统计与定位，最终差异按订单跨账期合并后判定。** 同一订单本来就可能出现在多个账期（增量结算，实测约 12% 的订单跨期），且两边对同一笔金额的归期或各期分摊比例也可能不同：
  - 合并后金额一致 → 逐期差异只是「跨期归期/分摊」，不计入差异（这类通常占绝大多数）
  - 合并后金额不一致 → 真实差异（订单级），并带上「结算单所在账期 / DB所在账期」便于定位

### 步骤四：输出结果

**控制台输出格式（以 7 个账期为例）：**

```
==============================================================================
项目              	值
----------------------------------------
客户              	ntw0ddj
店铺              	mihover
平台              	walmart
结算 sheet        	结算单
账期数              	7
订单数(逐期)      	Excel 3564 / DB 3550
订单数(去重)      	Excel 3381 / DB 3369
Excel总金额        	784,486.76
DB总金额           	785,121.57
逐期差异条目        	571 条（统计与定位用）
跨期归期/分摊       	526 条 / 263 个订单（合并后金额一致，不计入差异）
真实差异            	45 个订单（仅在Excel中 24 / 仅在结算利润中 12 / 金额不一致 9）
匹配结果            	有差异（45 个订单需核对）
==============================================================================

各账期汇总（按账期统计，最终结论见下方真实差异）：
账期                         Excel订单    DB订单        Excel总金额           DB总金额 逐期差异 跨期归期
--------------------------------------------------------------------------------------------
2026-04-18 ~ 2026-05-02        222     222       53,071.19       53,071.19    52     48
2026-05-02 ~ 2026-05-16        308     308       76,722.19       76,722.19    71     66
2026-05-16 ~ 2026-05-30        592     528       94,822.76       81,366.27    96     92
...
--------------------------------------------------------------------------------------------
合计                            3564    3550      784,486.76      785,121.57   571    526

真实差异明细（45 个订单，按订单跨账期合并后比对）：
order_id             类型                excel           db  结算单账期 → DB账期
------------------------------------------------------------------------------------------------------------
119110853858445      仅在Excel中        430.30            —  04-18~05-02 → —
119120565497322      金额不一致         281.95       256.97  07-11~07-25 → 07-11~07-25
119120668823153      仅在结算利润中          —       232.77  — → 07-11~07-25
...

跨期归期/分摊（不计入差异）：逐期条目 526 条 / 订单 263 个
  这些订单两边合并后金额一致，只是归期或各期分摊比例不同；逐期明细见导出文件「逐期差异明细」sheet
```

> 账期数为 1 时不再单列「各账期汇总」表。
> 逐期差异条目只出现在「各账期汇总」表里，不逐条打印（真实差异明细才逐条打印）；逐期条目明细在导出文件的「逐期差异明细」sheet。

**差异类型说明（订单级最终结论）：**
- **仅在Excel中** — 结算单有该订单，MCP 全部账期合并后仍没有
- **仅在结算利润中** — 结算单全部账期都没有该订单
- **金额不一致** — 同一订单跨账期合并后金额差异 > 0.01
- **跨期归期/分摊**（不计入差异）— 逐期看两边各自「缺」一次，但合并后金额一致：两边把同一笔金额归到了不同账期，或各期分摊比例不同。控制台只给汇总计数，逐期条目明细在导出文件里

**导出文件：**

在原文件同目录生成 `<原文件名>_比对结果.xlsx`，最多包含 5 个 sheet：
- **汇总信息** — 客户、店铺、平台、结算 sheet、账期数、订单数（逐期累计 / 跨期去重）、金额合计、逐期差异条目、跨期归期分摊、真实差异订单数、匹配结果，以及各账期一行统计与合计
- **真实差异** — 最终结论（订单级）：order_id / 类型 / excel金额 / db金额 / 结算单所在账期 / DB所在账期
- **逐期差异明细** — 逐期条目与归属（统计与定位）：账期 / order_id / excel_fee_amount / db_fee_amount / 备注 / 归属（真实差异 或 跨期归期/分摊）
- **订单已作废** — 存在作废订单时生成：账期 / order_id / 金额
- **全量比对** — 全部订单的逐期比对结果：账期 / order_id / excel_fee_amount / db_fee_amount / 状态

## 文件格式要求

- 支持 `.csv` 和 `.xlsx` 格式
- 表头可以不在第一行（在前 15 行内查找），块之间重复出现的表头行会被跳过
- 一个 sheet 可包含多个账期：账期汇总行（`Total Payable` 为数字）→ 该账期的订单明细行 → 下一个账期汇总行…，**全部账期都会参与对账**
- 必需列（大小写不敏感）：
  - `Transaction Key` — 交易标识
  - `Purchase Order #` — 采购订单号（用于与结算利润 orderId 匹配）
  - `Amount` — 金额
  - `Amount Type` — 金额类型
  - `Total Payable` — 应付总额（用于定位账期行）
  - `Period Start Date` — 账期开始日期
  - `Period End Date` — 账期结束日期
- 订单号容错：客户原始报告中「打开文件看不见」的字符会被自动清理后再参与比对，无需人工处理
  - 零宽字符、BOM、不间断空格/全角空格、方向控制符等隐藏字符
  - Excel 文本前缀或包裹引号（双击单元格才能看到的 `'1111`）
  - 数字被导出成文本的形式（如 `1111.0`）
- 表头列名同样做清理，列名后带隐藏字符也能识别
- 清理行数会在运行日志中提示：`[提示] N 行订单号含隐藏字符或引号，已自动清理后参与比对`

## MCP 服务配置

订单归属与结算利润明细全部通过 eccang-mfc-reconcile 提供的 MCP 工具获取，脚本不再直连数据库，也不内置任何库表 SQL 与账号口令。

- 默认地址：`https://datacenter.eccang.com/nexus/mcp/stream`（经网关访问，无需 token）
- 覆盖方式：命令行 `--mcp-url <地址>`，或环境变量 `NEXUS_MCP_URL`
- 本地联调可指向本机服务：
  ```bash
  python scripts/walmart_compare.py <文件路径> --mcp-url http://127.0.0.1:8070/nexus/mcp/stream
  ```
- 地址与工具说明见 [scripts/mcp_config.md](scripts/mcp_config.md)
- 连通性自检：
  ```bash
  python scripts/walmart_mcp.py --list-tools
  ```

安装依赖：
```bash
pip install openpyxl
```

## 错误处理

| 错误提示 | 原因 | 解决方法 |
|---|---|---|
| 文件不存在 | 路径错误 | 检查文件路径是否正确 |
| 不支持的文件格式 | 非 CSV/XLSX | 确认文件扩展名 |
| 未找到列 | 列名不匹配或选错了 sheet | 用 `--list-sheets` 查看候选 sheet，必要时 `--sheet` 指定 |
| 未找到包含结算单必需列的 sheet | sheet 名或结构不符 | 用 `--list-sheets` 查看后 `--sheet` 指定 |
| sheet 不存在 | `--sheet` 名称写错 | 用 `--list-sheets` 查看可用 sheet 名称 |
| 未能解析出账期与订单明细 | 该 sheet 没有账期汇总行/明细行 | 换 `--sheet` 指定真正的结算数据 sheet |
| 未提取到纯数字订单号 | `Purchase Order #` 非纯数字 | 用 `--company-code` / `--user-account` 指定对账主体 |
| 订单号在 MCP 中未找到 | 订单不在 ERP 中 | 确认订单号是否正确，或用 `--company-code` / `--user-account` 指定 |
| MCP 服务不可达 | 地址错误或网络不通 | 检查 `--mcp-url` / `NEXUS_MCP_URL` 与网络连通性 |
| MCP 工具执行失败 | eccang-mfc-reconcile 侧查询异常 | 查看工具返回的错误信息，确认客户/店铺/账期是否有效 |
