---
name: tk-platform-reconcile
description: >
  TikTok Shop / Tokopedia 平台账单对账工具（仅限这两个平台）。
  账单特征：xlsx，Sheet 名为 Order details，含 Related order ID、Total settlement amount、
  Order settled time。用户提供 TK 结算 Excel 路径后，通过 eccang-mfc-reconcile MCP
  （mcp__eccang-mfc-reconcile__queryOrderByReferenceNo / mcp__eccang-mfc-reconcile__queryProfitSettlement）获取店铺信息与结算明细，
  自动逐单核对并输出差异报告。
  触发词：TK 对账、TikTok 账单对账、TikTok Shop settlement、Tokopedia 结算核对。
  【硬性要求】执行期间禁止查询 SQL、禁止直连数据库，数据一律走 MCP。
  平台未确认时不要使用本技能，先调用 platform-reconcile-router 判定平台。
license: Proprietary
compatibility: Requires Python 3.8+, openpyxl. 需要 eccang-mfc-reconcile MCP 服务已连接（mcp__nexus，由本连接器内置提供，见「eccang-mfc-reconcile MCP 接入说明」章节）。
metadata:
  author: settle-team
  version: "2.2"
  platform: TikTok Shop / Tokopedia
---

# TK 平台账单对账工具

## Step 0 — 平台自检（执行前必做）

本技能**只处理 TikTok Shop / Tokopedia 账单**。动手前先确认文件确实是 TK 导出：

- 特征：xlsx，存在 Sheet `Order details`，含 `Related order ID`、`Total settlement amount`、`Order settled time`
- 若只有一个含糊的 `Sheet1`、或没有 `Related order ID` 列，说明不是 TK 标准导出

**若文件不是 TK 账单，立即停止**——不要执行本技能脚本、不要输出对账结果。改由
`platform-reconcile-router` 技能判定平台，再分发到对应平台技能。跑错平台会产出满屏假差异。

## 🚫 硬性规则：禁止 SQL 查询（最高优先级）

本 skill 执行期间 **禁止** 执行任何 SQL 语句、**禁止** 直连数据库、
**禁止** 读取或使用数据库连接配置（如 assets/.env）。

所有业务数据 **必须且只能** 通过 eccang-mfc-reconcile MCP 工具获取：

| 数据 | 调用工具（完整名） | 入参 |
|------|-------------------|------|
| 店铺/客户信息（companyCode / userAccount / platform） | `mcp__eccang-mfc-reconcile__queryOrderByReferenceNo` | orderId（订单号） |
| 结算明细（orderId / settlementAmount / accountCheckResult） | `mcp__eccang-mfc-reconcile__queryProfitSettlement` | companyCode / userAccount / platform / startTime / endTime |

> 调用前先用 ToolSearch 搜索并加载上述 `mcp__eccang-mfc-reconcile__*` 工具，确认参数后再执行；
> 工具返回的 JSON 需完整保存到本地临时文件，供对账脚本读取。

## eccang-mfc-reconcile MCP 接入说明

本 skill 依赖的 eccang-mfc-reconcile MCP 服务 **由本连接器（eccang-mfc-reconcile）内置提供**，
安装并连接连接器后，`mcp__eccang-mfc-reconcile__*` 工具即可通过 ToolSearch 加载使用，无需手动配置。

> 连接器内置配置（仅供排查参考，无需修改）：
> `mcpServers.eccang-mfc-reconcile` = `{ "type": "streamableHttp", "url": "https://datacenter.eccang.com/nexus/mcp/stream" }`

## Agent 执行流程

用户通过聊天发送 Excel 文件路径后，按以下步骤执行：

### Step 1 — 获取 Excel 文件

收到用户消息后，按以下优先级逐一判断：

---

**情况 A：消息中包含文件附件（钉钉对话框直接发送文件）**

钉钉对话框发送的文件不会自动落盘到服务器，需根据平台提供的内容选择处理方式：

| 平台提供的内容 | 处理方式 |
|--------------|---------|
| 文件下载 URL | 先下载到本地临时目录，再按下方 Step 2-4 流程执行 |
| base64 文件内容 | 先解码到本地临时目录，再按下方 Step 2-4 流程执行 |
| `downloadCode` / `mediaId` | 先调用 DingTalk API 换取下载 URL，再下载到本地临时目录 |

> 钉钉机器人消息中，文件类型消息（msgtype=file）通常携带 `downloadCode`，
> 需调用 `https://oapi.dingtalk.com/robot/message/download` 换取真实下载地址。

---

**情况 B：消息中包含本地文件路径**

消息中出现 `.xlsx` 或 `.xls` 路径时（文件已在服务器上），直接进入 Step 2。

---

**情况 C：消息中既无附件也无路径**

主动回复用户：
> 请通过以下方式提供 Excel 文件：
> 1. 直接在对话框中发送文件（.xlsx）
> 2. 告诉我文件在服务器上的完整路径

---

### Step 2 — 读取 Excel 并调用 MCP 工具获取数据

拿到 Excel 文件后，先运行 dry-run 模式读取账期与订单信息：

```bash
python scripts/reconcile.py "<excel_path>" --dry-run
```

输出示例（账期用于下一步 MCP 调用参数）：
```
[DRY-RUN] 账期信息：
  start_time：2026-02-01 00:00:00
  end_time  ：2026-02-28 23:59:59
```

> 若 Excel 读取失败（缺 Sheet、无订单等），按「常见问题处理」提示用户后停止。

随后依次调用两个 eccang-mfc-reconcile MCP 工具（先 ToolSearch 加载再调用）：

**① 根据订单号查询店铺/客户信息 → 调用 `mcp__eccang-mfc-reconcile__queryOrderByReferenceNo`**

从 Excel 的 `Related order ID` 列任取一个有效订单号（优先第一个非空、不以 `/` 开头的）：

```json
{"orderId": "<从Excel取出的订单号>"}
```

返回示例：
```json
{"code":"200","data":[{"companyCode":"ntwfswp","userAccount":"SOKINTOOL3631","platform":"tiktok"}]}
```

**② 根据结算日期查询结算明细 → 调用 `mcp__eccang-mfc-reconcile__queryProfitSettlement`**

根据店铺信息与 Step 2 输出的账期（start_time / end_time）调用：

```json
{
  "companyCode": "ntwfswp",
  "userAccount": "SOKINTOOL3631",
  "platform": "tiktok",
  "startTime": "2026-02-01 00:00:00",
  "endTime": "2026-02-28 23:59:59"
}
```

返回数据量可能很大，需将返回的 JSON 完整保存到本地临时文件（如系统临时目录下的 `settlement.json`），
供 Step 3 脚本读取。

> 说明：店铺信息也可通过 `mcp__eccang-mfc-reconcile__queryOrderByReferenceNo` 逐单查询，但结算明细
> 只需按店铺+账期查询一次即可覆盖全部订单。

---

### Step 3 — 执行对账脚本

| 场景 | 命令 |
|------|------|
| 本地路径 | `python scripts/reconcile.py "<excel_path>" --shop-info '<店铺信息JSON>' --settlement-file "<settlement.json路径>"` |
| 钉钉附件 | 先下载到本地临时目录，命令同上 |

参数说明：
- `--shop-info`：Step 2 中 `mcp__eccang-mfc-reconcile__queryOrderByReferenceNo` 的返回 JSON（可直接传完整返回，脚本自动解析）
- `--settlement-file`：Step 2 中 `mcp__eccang-mfc-reconcile__queryProfitSettlement` 返回 JSON 落盘后的文件路径
- `--out`：可选，指定输出报告路径（默认与 Excel 同目录）

---

### Step 4 — 将结果回显给用户

脚本执行完成后，把控制台输出的对账摘要直接回复给用户，格式示例：

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
  💪 你的数据真的很干净，继续保持！加油！
============================================================
```

---

### Step 5 — 询问是否发送 Excel 报告

摘要回显后，询问用户：

> 是否需要将完整对账报告（Excel 文件）发送给您？
> 报告包含：对账摘要 / 差异明细 / Excel明细 / MCP结算明细

---

## 对账规则

| 场景 | 处理方式 |
|------|----------|
| Excel 与 MCP 结算金额一致 | 标记匹配 ✅ |
| Excel 金额 ≠ MCP 结算金额 | 记录差异：`金额差异` |
| Excel 有、MCP 无（金额 ≠ 0） | 记录差异：`Excel有/MCP无` |
| Excel 有、MCP 无（金额 = 0） | 自动补齐，标记匹配 ✅ |
| MCP 有、Excel 无 | 记录差异：`MCP有/Excel无` |

---

## 常见问题处理

| 问题 | 处理方式 |
|------|----------|
| 文件不存在 | 提示用户确认路径后重试 |
| MCP 工具调用失败 | 确认 eccang-mfc-reconcile MCP 连接是否正常，重试调用 |
| `mcp__eccang-mfc-reconcile__queryOrderByReferenceNo` 未返回店铺信息 | 提示用户确认 Excel 中 orderId 是否有效 |
| `mcp__eccang-mfc-reconcile__queryProfitSettlement` 返回为空 | 提示确认店铺信息与账期是否正确 |
| Sheet 名不是 `Order details` | 提示用户确认是否为 TK 平台标准导出格式 |

---

## 数据依赖

| 数据 | 获取方式 |
|------|----------|
| 店铺信息（companyCode / userAccount / platform） | MCP `mcp__eccang-mfc-reconcile__queryOrderByReferenceNo`（入参：订单号） |
| 结算明细（orderId / settlementAmount / accountCheckResult） | MCP `mcp__eccang-mfc-reconcile__queryProfitSettlement`（入参：companyCode / userAccount / platform / startTime / endTime） |

脚本不再直连数据库，无需数据库连接配置。**执行期间禁止任何 SQL 查询，数据一律来自上述两个 MCP 工具。**

输出模板：[references/OUTPUT_TEMPLATE.md](references/OUTPUT_TEMPLATE.md)
