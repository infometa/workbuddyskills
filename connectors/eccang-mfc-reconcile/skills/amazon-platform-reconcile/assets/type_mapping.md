# Amazon 对账类型映射与站点索引

本文维护 CSV 交易类型与 MCP 财务类型的对应关系、比较规则及站点语言文档入口。实际解析规则以 [`scripts/reconcile.py`](../scripts/reconcile.py) 为准；`lang/*.md` 仅供说明，不会被脚本加载。

## 类型映射与比较规则

### CSV Type → MCP 财务 Type

CSV Type 指语言转换后的英语交易类型；MCP 财务 Type 指 `queryFmsTransaction` 返回的财务类型编码。下表保留基础映射，最终参与比较的类型及金额还需应用后续合并、排除规则。

| CSV Type | MCP 财务 Type | 说明 |
|---|---|---|
| Order | payment_order | 订单收入 |
| Refund | refund_order | 退款 |
| Shipping Services | shipping_services | 物流服务费 |
| Service Fee | service_fee | 服务费 |
| Amazon Fees | coupon | 亚马逊费用／优惠券 |
| Liquidations | liquidation | 清算 |
| FBA Inventory Fee | fba_inventory_fee | FBA 库存费 |
| Adjustment | adjustment | 调整 |
| Order_Retrocharge | order_retrocharge | 订单追溯扣费 |
| Refund_Retrocharge | refund_order | 退款追溯；合并到 Refund |
| Liquidations Adjustments | liquidation_adjustment | 清算调整 |
| FBA Transaction fees | fba_transaction_fees | FBA 交易费 |
| Chargeback Refund | chargeback_refund | 拒付退款 |
| Lightning Deal Fee | lightning_deal_fee | 秒杀活动费；合并到 Amazon Fees |
| Fulfilment by Amazon (FBA) transaction fees | fba_transaction_fees | FBA 交易费（UK 变体） |
| Transfer | transfer | 转账／打款；排除，不参与比较 |
| Debt | debt | 欠款 |
| Others | others | 其他费用；合并到 Service Fee |
| Fee Adjustment | fee_adjustment | 费用调整 |

### 合并规则（MERGE_TYPES）

比较前，将以下类型的金额合并到目标类型：

| 原 CSV Type | 目标 CSV Type | 说明 |
|---|---|---|
| Others | Service Fee | 其他费用归入服务费 |
| Refund_Retrocharge | Refund | 两者共用 MCP 财务编码 refund_order |
| Lightning Deal Fee | Amazon Fees | 秒杀活动费归入亚马逊费用 |

`refund_order` 反向映射默认取 `Refund`。新增 8 站的受限解析路径在汇总前将 `Fulfilment by Amazon (FBA) transaction fees` 规范为 `FBA Transaction fees`，避免两个英语别名分别匹配同一财务金额；既有比较函数及 `MERGE_TYPES` 不变。

### 排除规则（SKIP_TYPES）

| CSV Type | MCP 财务 Type | 处理方式 |
|---|---|---|
| Transfer | transfer | 双方均排除，不纳入金额比较和合计 |

## 站点与语言文档索引

按 [Amazon 官方站点清单](https://developer-docs.amazon.com/sp-api/docs/marketplace-ids)整理，共有 23 个站点文档：既有解析格式 8 站、受限候选规则 7 站、受限英语路径 1 站、未接入 7 站。

文档覆盖不等于解析能力覆盖，也不代表覆盖站点的全部导出语言。“已接入”只表示存在解析路径，不表示实际账单已验收。默认 `--site auto` 按已知列名自动查找表头，不要求固定的前置说明行数；AU 的严格英语路径必须显式使用 `--site AU`。

### 既有解析格式（8 站）

以下格式保留既有解析路径；这里列出的表头和小数点沿用现有文档，不代表所有当前报告版本均已验收，也不表示已完成下述新增路径的严格校验。旧命令继续使用 `auto`，不通过 `--site` 指定这些站点。

| 语言 | 站点 | 映射文档 | 表头标识／说明 | 小数点 |
|---|---|---|---|---|
| 英语 | US | [lang/en_us.md](lang/en_us.md) | `date/time` | `.` |
| 英语 | CA | [lang/en_ca.md](lang/en_ca.md) | `date/time` | `.` |
| 英语 | UK | [lang/en_uk.md](lang/en_uk.md) | `date/time` | `.` |
| 法语 | FR | [lang/fr.md](lang/fr.md) | `date/heure` | `,` |
| 德语 | DE | [lang/de.md](lang/de.md) | `Datum/Uhrzeit` | `,` |
| 西班牙语 | MX | [lang/es.md](lang/es.md) | `fecha/hora` | `.` |
| 葡萄牙语 | BR | [lang/pt.md](lang/pt.md) | `data/hora` | `,` |
| 意大利语 | IT | [lang/it.md](lang/it.md) | `Data/Ora:` | `,` |

### 候选规则已受限接入（7 站，待样本验收）

下列候选列名和日期规则已接入独立严格路径，可按已配表头自动识别，也可显式使用 `--site ES|NL|SE|PL|TR|JP|BE`（选择一个值，大小写均可）。依据仍主要为第三方历史实现，日本另有官方帮助搜索摘要及教程线索，并未升级为当前官方 CSV 规范。实际本地化 Type、金额格式及新版交易状态／释放日期列仍待原始 CSV 验证；各文档保留来源和已排除的异常字段。

| 语言 | 站点 | 映射文档 | 表头标识／说明 | 小数点 |
|---|---|---|---|---|
| 西班牙语 | ES | [lang/es_es.md](lang/es_es.md) | `fecha y hora` | 待确认 |
| 荷兰语 | NL | [lang/nl.md](lang/nl.md) | `datum/tijd` | 待确认 |
| 瑞典语 | SE | [lang/sv.md](lang/sv.md) | `datum/tid` | 待确认 |
| 波兰语 | PL | [lang/pl.md](lang/pl.md) | `data/godzina` | 待确认 |
| 土耳其语 | TR | [lang/tr.md](lang/tr.md) | `tarih/saat` | 待确认 |
| 日语 | JP | [lang/ja.md](lang/ja.md) | `日付/時間` | 待确认 |
| 法语；其他语言待确认 | BE | [lang/be.md](lang/be.md) | `date/heure` + `Identifiant du paiement` 或 `Numéro de la commande` | 待确认 |

### 英语路径已接入（1 站，格式待样本验收）

AU 导出语言已由用户确认为英语，标准英语列名和已配置英语 Type 无需语言转换。使用 `--site AU` 进入严格路径；`auto` 下的英语表头仍进入既有英语路径，不推定为 AU。完整表头、实际 Type 枚举、日期、时区、金额格式及报告版本字段仍待 AU 原始 CSV 验收。

| 语言 | 站点 | 映射文档 | 表头标识／说明 | 小数点 |
|---|---|---|---|---|
| 英语（用户已确认） | AU | [lang/au.md](lang/au.md) | `--site AU` + `date/time`，完整表头待验收 | 待确认 |

### 待样本确认（7 站，未接入脚本）

仅有报告功能或版本更新线索，尚无可靠的站点专属原始表头。文档中的待采集字段不是可用映射，不能从帮助页语言、国家惯例或其他站点推定导出格式。

| 语言 | 站点 | 映射文档 | 表头标识／说明 | 小数点 |
|---|---|---|---|---|
| 待确认 | IE | [lang/ie.md](lang/ie.md) | 待确认 | 待确认 |
| 待确认 | SG | [lang/sg.md](lang/sg.md) | 待确认 | 待确认 |
| 待确认 | IN | [lang/in.md](lang/in.md) | 待确认 | 待确认 |
| 待确认 | AE | [lang/ae.md](lang/ae.md) | 待确认 | 待确认 |
| 待确认 | SA | [lang/sa.md](lang/sa.md) | 待确认 | 待确认 |
| 待确认 | EG | [lang/eg.md](lang/eg.md) | 待确认 | 待确认 |
| 待确认 | ZA | [lang/za.md](lang/za.md) | 待确认 | 待确认 |

## 新增路径的受限解析边界

以下规则仅适用于 ES、NL、SE、PL、TR、JP、BE，以及显式选择的 AU；不表示原有 8 站已完成同等输入校验。

### 文件、列名与 Type

- 仅接受 UTF-8（含 BOM）、逗号分隔 CSV；这是当前入口限制，不是对各站官方导出格式的断言。允许前置说明和空白行，非空数据行列数必须与表头一致。
- 显式站点与表头必须兼容；BE 必须同时有上述法语日期标识和至少一个 BE 特征字段。FR 的 `numéro de versement`／`numéro de la commande` 与 BE 特征混合时停止。检测到新增格式后，任何错误均不回退旧路径。
- 列名与 Type 只去掉两端空白，保留大小写、重音和标点。映射后必须有 `date/time`、`type`、`order id`、`total`；重复列名、多个列映射到同一目标或缺列均停止。
- 只接受上表 19 项确切英语 Type，以及排除项小写 `transfer`。尚未配置新增站点的本地化 Type，也不借用 MX／FR 翻译；未知或空 Type 即使金额为零也停止。JP 日语 Type 因此仍可能阻止整份账单对账。
- 费用行订单号可以为空，但整份文件至少要有一个订单号和一条可比较的非 Transfer 记录。

### 日期与查询集合

- ES、NL、SE、PL、TR、BE 使用各自文档月份表和 `DD MMM YYYY`；按完整词元匹配，月份不区分大小写、允许末尾点号，但必须保留重音，不做跨语言猜测。
- JP 接受 `YYYY/MM/DD`（月、日允许一位）；AU 接受 `MMM D, YYYY` 或 `DD MMM YYYY`，使用英语月份。ES／NL／SE／AU 接受 `sep`、`sept`；不猜测 `01/02/2026` 的日月顺序。
- 可只有日期，或附加 24 小时制 `HH:mm:ss`、带 `AM/PM`（含 `a.m./p.m.`）的 12 小时制时间；小时允许一位，分秒须两位。
- 时区只接受 `PDT`、`PST`、`UTC`、`GMT`、`GMT-数字` 后缀或无后缀；不自动补充或换算。`JST`、`AEDT` 等未配置标记会报错，待原始样本确认后再扩展。
- 每行入账日期必须有效；释放日期非空也必须有效。`datetime` 允许释放日期缺列或空值；`transaction` 要求每条非 Transfer 记录都有有效释放日期，不能过滤缺失行或改用入账日期。
- 不猜测本地化释放日期列名；当前新增配置需原文件中的标准英语 `Transaction Release Date`。Transfer 的释放日期可以为空，但非空仍须有效。
- 查询范围由参与金额汇总的非 Transfer 记录计算并扩展到全天；不由打款行或少量有效日期替代真实比较集合。

### 金额与失败处理

- 使用 `Decimal` 解析及累加，汇总后沿用两位小数输出接口。不按站点预设小数点，对全文件 `total` 同时校验“点小数／逗号三位分组”和“逗号小数／点三位分组”两种语法。
- 全文件仅一种语法成立才采用；两种都成立且逐行数值相同（如纯整数）也可接受。孤立 `1,234` 等两种语法数值不同的情况报歧义；没有全文件一致语法时报格式冲突。
- 支持整数、小数、前置正负号及两端空白；`1234.56`、`1,234.56`、`1234,56`、`1.234,56` 在唯一语法下可解析。拒绝空金额、非有限值、超出既有输出范围、空格千分位、货币符号、括号负数、指数及非 ASCII 数字，不补零。
- Transfer 金额同样校验，但继续排除在比较与合计之外。错误包含解析配置、CSV 物理行号、字段与原因，不输出整行订单或客户数据；输入校验在 MCP 连接前完成，失败返回 `1` 且不导出。

## 维护与验证

### 代码定位

以下常量均位于 [`scripts/reconcile.py`](../scripts/reconcile.py)。名称中的 `EXCEL`、`DB` 沿用历史命名，分别对应 CSV 侧及财务侧，不表示脚本仍然直连数据库。

| 常量 | 用途 |
|---|---|
| EXCEL_TO_DB_TYPE_MAP | CSV Type → MCP 财务 Type |
| DB_TO_EXCEL_TYPE_MAP | MCP 财务 Type → CSV Type |
| MERGE_TYPES | 类型合并规则 |
| SKIP_TYPES | 类型排除规则 |
| CANDIDATE_COLUMNS | 8 个新增配置的候选列名；AU 标准英语列名直通 |
| CANDIDATE_MARKERS | ES、NL、SE、PL、TR、JP 的独特日期表头 |
| CANDIDATE_MONTHS | 本站月份词元；JP 单独使用数字日期 |

`parse_csv` 按配置分流；`detect_candidate_site` 处理站点兼容及 BE／FR 冲突；`parse_candidate_csv`、`parse_candidate_date`、`parse_candidate_amounts` 执行新路径校验。既有实现保留在 `parse_legacy_csv`。

### 文件命名

- `es.md` 对应 MX；ES 西班牙单独使用 `es_es.md`，两者不能互换。
- `sv.md`、`ja.md` 使用语言代码，分别对应 SE、JP。
- BE、AU 及导出语言未确认的站点保留按站点代码命名的文件，不暗示仅有一种导出语言。BE 与 FR 虽共享表头标识，也不能直接互换完整映射。

### 更新流程

1. 新增或修订站点文档时，记录来源、确认范围及待验证项，并同步本索引的状态和数量。
2. 区分“语言确认”“受限接入”“实际格式验收”；新增文档或确认语言均不能自动升级为已支持。
3. 有来源的候选规则可先受限接入，但必须明确拒绝未知格式及 Type，保留待样本状态。取得脱敏原始 CSV、确认规则并完成必要的代码适配和样本验证后，才能标记相应格式已验收。

### 样本验收范围

已有两份真实账单按入账口径执行的记录，仅覆盖当时的样本与查询范围，不代表所有站点、结算口径、全费用或逐笔一致性已验收。新增受限站点仍需原始样本确认，不能按文档覆盖数量推断支持范围。

- 文件结构：完整表头、前置说明行、编码、BOM、CSV 分隔符及引号。
- 交易数据：实际 Type 枚举、正负金额、小数点、千位分隔、日期及时区。
- 版本差异：交易状态、释放日期及其空值；保留报告期间、生成时间和实际导出语言。
- 样本必须属于日期范围交易报告，不能用税务报告、订单报告或 Amazon Pay 样本替代。
- `tests/test_mcp_reconciliation.py` 的新增用例使用合成 CSV 和模拟财务响应，仅验证解析、分流、错误边界及既有行为，不构成各站本地化 Type、真实 CSV 或真实 MCP 业务验收；编码和日期测试值不是实际报告证据。

[官方报告更新公告](https://sellercentral-europe.amazon.com/seller-forums/discussions/t/8fe604f7-ecb8-4930-902e-a700f731ee66)涉及相应预留款账户及报告版本差异，历史候选字段不能视为所有账号和期间通用的完整表头。

## 输出边界

- 默认仅控制台输出，不生成 Excel；只有用户明确要求导出时才传 `--output`。
- 费用项汇总一致即结束；不一致时自动按“描述构成 → 订单聚合差异”下钻。全费用及显式附加查询仍未启用，记录总数显示“未查询”，不能用类型数量代替。
- 差异组展开为远端实际返回的所有原始 type；Service Fee 对应 service_fee/others，Amazon Fees 对应 coupon/lightning_deal_fee，Refund 对应一次 refund_order。未知远端类型原样保留，不向接口传 CSV 显示名。CSV 单边类型无原始 type 可查询时仅显示本地记录及“远端汇总缺少该类型”，不造类型、不发空 types。
- 描述只做两端空白规范化并保留原文，空值单独成组；缺 description 列标记该层不可双边比较，继续订单定位。订单按“订单号 + 比较组”汇总，保留重复交易与来源记录数，空订单号单列本地描述和物理行号，不用 SKU 自动关联。
- 下钻使用已保留的 Decimal total 和全文件数字语法，按原始类型及比较组回勾；无法解析、范围不符、金额不能回勾或旧路径未合并别名冲突时标记失败并保留既有汇总差异，不推断缺单、不导出正常报告。旧站点汇总规则未改。
- 金额回勾不能证明没有正负抵消的漏记录；汇总或订单聚合匹配均不代表交易逐笔一致。
- 报告和显式 Excel 导出展示实际查询上下文的时间口径及起止范围。默认 `datetime → entry`，可选 `transaction → settlement`，不强制询问，也不同时执行两种口径。
