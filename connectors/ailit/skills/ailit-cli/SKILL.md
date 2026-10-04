---
name: ailit-cli
description: 通过本地 `ailit` CLI查询和操作智慧记 AI 进销存。适用于查询客户、商品、销售单、账户、库存、采购、欠款、对账和经营报表，以及创建客户或商品、商品调价、销售开单与退货、打印分享单据、导出对账单，或根据文字、图片、Excel 批量创建商品和销售单等场景。
author: 金蝶智慧记
version: 1.0.0


---

# Ailit CLI

ailit-cli 是操作智慧记 AI 进销存的本地命令行 Skill，支持客户、商品、销售单、库存、采购、欠款、对账及经营报表查询。
它还可创建客户和商品、处理销售开单与退货，并从图片、文字或 Excel 提取数据，完成批量建商品、对账单及销售单导出。
使用本地 `ailit` 命令作为操作智慧记AI进销存的主要接口。“智慧记 Web”指 `space.zhihuiji.cn`；“Ailit Client”指通过 `AILIT_HOME` 提供运行时认证的宿主应用。

## 简单请求与复杂场景

- 一个基础命令即可完成的查询，直接使用本文件，不读取 Reference。
- 基础查询加一次客户、商品或账户消歧，仍直接使用本文件。
- 涉及多步骤组合、批量循环、文件下载与命名、图片/Excel 提取、跨对象匹配或创建确认时，才读取对应 Reference。
- 不要仅因为请求中出现“客户”“销售单”“欠款”“商品”等关键词就读取 Reference；先判断用户的最终交付是否命中复杂场景。

复杂场景路由：

| 仅在满足以下复杂目标时读取 | Reference |
|---|---|
| 组合筛选或批量查询欠款，并生成、下载、命名一个或多个对账单 | [组合欠款查询与对账单导出](references/debt-statement-export.md) |
| 查询指定客户的未结清销售单后，批量逐单生成图片/PDF并准备微信分享 | [批量未结清销售单导出与分享](references/unpaid-sale-export-and-share.md) |
| 从用户文字或图片提取订货信息，匹配客户和商品，生成销售单预览并在确认后创建 | [根据文字或图片创建销售单](references/sale-create-from-text-or-image.md) |
| 从图片、文字、普通 Excel 或官方 Excel 模板批量创建商品 | [根据图片或 Excel 创建商品](references/product-create-from-image-or-excel.md) |

复合请求按阶段路由。例如图文开销售单时发现商品不存在，先暂停销售单流程；用户同意建商品后读取商品创建 Reference，完成后再返回销售单流程。

## 核心规则

### 认证与健康检查

- 不要在本 Skill 中管理或展示令牌。
- 配置或认证状态未知时，在业务命令前运行 `ailit doctor`。
- 普通 CLI/Codex/Claude Code 未登录时运行 `ailit auth login`，不要手动写入 token。
- 不要把 `ailit config set token ...` 作为修复手段；仅限用户明确排障时使用，且答复中不复述令牌。
- 当 `AILIT_AUTH_SOURCE=client` 时，不要运行 CLI 登录；让用户重新登录 Ailit Client，再运行 `ailit doctor`。
- 非 TTY 环境使用：

```powershell
ailit auth login --non-interactive --format json
ailit auth login --resume <workflowId> --result-set <resultSetId> --select <token> --format json
```

### 输出与格式

- 面向用户优先使用默认表格或友好摘要。
- 只有需要解析、筛选、计算或排障时才使用 `--format json`。
- CLI 返回友好中文错误时直接复用，不要改写业务含义。
- 除非排障需要，不要暴露令牌、`pay_records`、原始堆栈或内部 ID。
- `ailit sale list` 支持 `--format csv`；`ailit report` 仅汇总类（`today`/`week`/`month`/`all`/`fund-profit`）不支持 csv，列表类报表（`hot-sale`、`sale-stat`、`purchase-stat`、`customer-check`、`supplier-check`、`stock-flow`、`stock-io` 等）支持；`print` 类命令不支持 csv。

### 搜索与选择

```powershell
ailit customer search <keyword>
ailit product search <keyword>
ailit account search <keyword>
```

需要结构化处理时添加 `--format json`。规则：

- 零结果时请用户补充关键词；不要猜测或编造对象。
- 多结果时展示数字 `selectToken`、`displayName` 和 `fields`，等待用户选择。
- 使用同一命令的 `--result-set <id> --select <token> --format json` 完成选择。
- 不得把界面行号当作稳定 ID。
- 返回 `selection_validated` 后直接使用响应中的 `displayName`、`fields` 和 `meta`；必要字段齐全时不要重复查询详情。
- 商品确认后，从 `meta.productId`、`meta.productSkuId` 和 `displayName` 取得销售单草稿所需字段。

### 查询范围一致性（强制）

执行查询前，识别用户期望的数据范围；查询完成后，根据实际执行参数、CLI 返回信息及命令当前能力，判断本次实际查询范围。

- 系统支持查询未来 7 天内的单据。当用户要求全量查询销售单、进货单、对账单等单据时，结束日期固定为今天之后第 7 天；用户明确指定结束日期时，以用户指定范围为准。
- 如果实际查询范围与用户期望范围一致，正常返回结果。
- 当用户要求查询全量，全部，所有数据时，需在返回结果时，将本次实际查询的范围也告知用户。
- 如果实际查询范围小于、不同于或无法完全覆盖用户期望范围，必须在最终答复中主动说明：
  1. 用户期望的范围；
  2. 本次实际查询的范围；
  3. 未被覆盖的部分；
  4. 当前结果不能视为用户所要求范围的完整结果。
- 不得因为命令成功执行或返回了数据，就默认用户要求已被完整满足。
- 范围差异说明必须出现在最终用户答复中，不能只保留在内部推理或命令输出中。


### 变更操作安全

- 创建销售单、单个商品或通过 `product batch-create` 批量建商品前，必须先运行相应 `--dry-run`。
- 用户看到本次预览并明确回复字面确认词“确认”后，才能执行实际创建。
- 用户原始请求中的“直接创建”“没问题就保存”不能代替预览后的确认。
- `--yes`、`-y` 不能绕过 Agent 的确认门槛：`--yes`/`-y` only skips the CLI terminal prompt and must not bypass this agent confirmation contract.
- `--no-preview` 不能用于常规 Agent 流程：`--no-preview` is terminal-only and skips the interactive confirmation view.
- `sale return` 没有 `--dry-run`；执行前先复述草稿关键字段（客户、商品、数量、金额）并等待确认，不得套用销售建单的试运行规则。
- 官方 Excel 模板的 `product import` 没有 `--dry-run`；先展示文件摘要和表头检查，再等待确认。
- 创建失败或部分失败时报告并停止，不要自动重试，避免重复创建。
- “未结清”只表示查询条件；不得据此创建收款、修改状态或执行结清。
- `sale invalid` 和 `sale delete` 当前未开放，不要尝试；需要时引导用户使用智慧记 Web。

### 不支持场景处理

- 如果用户要求包含当前 CLI 不支持的能力、场景或数据时（如保质期、批次管理），必须在执行前明确告知哪些要求无法实现。
- 不得静默忽略、删除或降级处理不支持的要求，也不得将其描述为已完成。
- 如果只能完成部分需求，说明“可以完成的部分”和“无法完成的部分”，暂停操作并等待用户确认是否继续。

### 销售单草稿默认值

草稿中省略的字段由 CLI 填充：

- `shopId` → `DefaultShopID`；`warehouseId` → `DefaultWarehouseID`；`billDate` → 当天；`quantity` → 1。
- `operatorId` — filled from `DefaultOperatorID`, then the authenticated user's UID
- `unitPrice` — 最新报价 > 零售价 > 0.00；零售客户跳过报价。
- `settlement.mode` — 省略时为 `FULL`。
- `accountId` — for `FULL` settlement the CLI attempts to resolve the cash-priority payee; `ON_ACCOUNT` 不使用账户。

销售单备注只能使用用户明确提供的内容。用户没有明确提供备注时，备注必须留空，不得由 Agent 自动生成、总结或补充。

## 基础 CLI 能力

以下命令用于简单请求，可以直接执行；需要未列出的参数时运行 `ailit <command> --help`。

### 查询销售单

```powershell
ailit sale list                             # 默认：最近6个月、每页100条、按业务日期降序、全部收款状态
ailit sale list --pay-status unpaid         # 仅查询未结清
ailit sale list --pay-status paid           # 仅查询已结清
ailit sale list --pay-status all            # 查询全部状态
ailit sale list --customer "王老板"          # 按客户名称筛选
ailit sale list --today                     # 查询今天
ailit sale list --week                      # 查询本周
ailit sale list --start 2026-06-01 --end 2026-07-01
ailit sale list --customer "张三" --today --format json
ailit sale get <单据ID>                      # 使用 sale list 返回的数字ID，不是单据编号
```

规则：

- 日期范围最多为6个月；`--today`、`--week`、`--customer` 和 `--pay-status` 可以组合。
- `--customer` 多匹配时 CLI 可能选择最近有销售单的客户。存在歧义时先运行 `customer search` 并让用户确认。
- 表格包含业务日期、单据编号、客户、应收、实收、待收、收款状态、账户和备注等字段。
- `sale get`、`sale print` 和 `sale share` 使用数字单据 ID，不使用单据编号。

### 销售单打印与分享

```powershell
ailit sale print image <单据ID>              # 返回默认模板图片 URL
ailit sale print pdf <单据ID>                # 返回默认模板 PDF URL
ailit sale print pdf <单据ID> --format json  # 返回 {"url":"..."}
ailit sale share <单据ID>                    # 返回分享凭证、链接和微信小程序码
ailit sale share <单据ID> -o out.png         # 保存小程序码图片
```

这些命令不会自动下载 URL，也不会直接发送到微信联系人。只有文件实际下载或宿主收到发送成功回执后才能报告成功。

### 销售退货

`sale return` 没有 `--dry-run`。复制 `templates/sale-return.json` 为临时草稿，替换占位字段后先向用户复述关键字段，等待“确认”后再执行：

```powershell
ailit sale return --json <临时草稿文件>
```

- 必须替换数字 `company_id` 和 `items[].product_id`；不得提交模板原文件。
- `warehouse_id` 保持 `0`，由 CLI 使用 `DefaultWarehouseID`。

### 查询商品

```powershell
ailit product list                   # 默认20条/页；-p 页码，-z 每页数量
ailit product get <商品ID>            # 查询商品详情
ailit product search <keyword>       # 关键字搜索，支持结构化选择
```

通过 `product search --format json` 已取得所需 `meta` 字段时，不要重复调用 `product get`。

### 查询客户、欠款和对账

```powershell
ailit customer list                                      # 客户列表
ailit customer get <客户ID>                               # 客户详情
ailit customer search <keyword>
ailit customer debt                                      # 欠款客户列表
ailit report customer-check list                         # 默认本月、隐藏零欠款、累计欠款降序、100条/页
ailit report customer-check list --keyword "张三"         # 名称或联系人模糊查询
ailit report customer-check detail <company-id>          # 客户对账明细
ailit report supplier-check list                         # 供应商对账列表
ailit report supplier-check detail <company-id>          # 供应商对账明细
ailit customer print pdf <company-id> -s 2026-08-01 -e 2026-08-31
```

对账默认日期为当月，开始日期最多回溯最近6个月。客户支持官方对账单 PDF URL；当前 CLI 没有供应商对账单 PDF 命令。

### 查询库存、采购和报表

```powershell
ailit stock list
ailit stock low                     # 按库存升序返回库存最低的一页
ailit stock low --threshold 5       # 返回库存 <= 阈值 的商品
ailit stock out                     # 缺货商品

ailit purchase list --today
ailit purchase list --week
ailit purchase supplier

ailit report all                    # 今日/本周/本月汇总及热销，日常概览优先使用
ailit report today
ailit report week
ailit report month
ailit report hot-sale
ailit report hot-sale --start 2026-08-01 --end 2026-08-31
```

### 创建单个商品

创建前先搜索同名商品，服务端不一定阻止重复：

```powershell
ailit product search "粉色可口可乐"

ailit product create --name "粉色可口可乐" --barcode 6901234567890 --spec "500ml/瓶" --code "Coca-001" --unit "瓶" --cost 2.50 --price 3.50 --wholesale 3.20 --member-price 3.00 --stock 100 --remark "新品上架" --dry-run
```

只有用户确认后，才运行去掉 `--dry-run` 的相同命令。关键默认值：

- `--name` 必填；分类省略时使用“未分类”。
- `--unit` 可省略；提供单位名称时由 CLI 解析，不存在则自动创建。
- 价格和库存默认0；设置库存时仓库默认使用 `DefaultWarehouseID`。
- `--code` 省略时默认使用条码。
- `--supplier-id <id>` 可选；若服务端返回 *[A5331] 供应商已被删除*，运行 `ailit supplier list` 选择有效供应商ID后重试。

### 更新商品与商品元数据

```powershell
ailit product update <商品ID> --price 39.9 --cost 12

ailit product type list
ailit product type create "饮料"
ailit product type create "可乐" --parent 1234

ailit product unit list
ailit product unit create "瓶"

ailit product spec list
ailit product spec create "颜色" --detail 红 --detail 蓝 --detail 绿
```

- 创建分类、单位或规格前先执行对应 `list`，避免重复。
- `product update` 只能更新名称、条码、规格、分类、备注和部分价格；主单位、库存、供应商及 SKU 组合不能通过此命令修改。
- MVP 阶段不要尝试分类、单位或规格的 `delete` 子命令。

### 创建客户

创建前运行 `customer search` 防止重名，并通过 `customer type list` 取得分类：

```powershell
ailit customer type list
ailit customer price-level list
ailit customer create --name "王老板" --type <分类ID> --contact "王五" --phone 13700001111 --address "广州市天河区" --balance 300 --remark "VIP客户"
```

- `--name` 和 `--type` 必填。
- 没有合适分类时先运行 `ailit customer type create <名称>` 创建；加 `--parent <id>` 可创建子分类。
- `--price-level` 可选；省略时 CLI 尝试使用零售价等级，不存在时会要求明确传入。
- 其他字段（联系人、电话、地址、期初欠款、预存款、积分、折扣、邮箱、税号、银行、生日、微信等）需要时运行 `ailit customer create --help`。

## 复杂 Reference 的使用原则

- 命中复杂路由时先完整读取对应 Reference，再执行其组合流程。
- Reference 中出现的基础命令仍遵守本文件的认证、消歧、格式和确认规则。
- 简单查询不要为了寻找示例而加载 Reference。
- Reference 之间不层层嵌套；复合流程的切换由本文件路由。

## 模板与示例

- `templates/sale-quick-create-full.json`：全额结算销售单草稿。
- `templates/sale-create-on-account.json`：挂账销售单草稿。
- `templates/sale-return.json`：销售退货单草稿。
- `templates/product-batch-create.json`：批量商品草稿。
- `examples.md`：常用命令序列与建议执行顺序。

不要直接执行模板原文件。复制为临时草稿，替换全部示例值和占位 ID，完成校验及试运行后再使用。

