# 澳大利亚（AU）映射

AU（澳大利亚）站与 US 站一样使用英语，列名和 type 无需语言转换，参见 [英语（US）映射](en_us.md)。

> 状态：英语路径已接入，格式待样本验收。用户已确认导出语言为英语；显式 `--site AU` 已提供严格解析路径，日期格式、时区及报告版本字段仍需以 AU 实际 CSV 为准。

## 表头检测标识

通过 `--site AU` 及英语表头标识 `date/time` 进入严格路径，完整表头以实际 CSV 为准。`auto` 下英语表头仍走既有英语解析，不推断为 AU；显式 AU 与其他语言表头不兼容时停止。

## 列名映射

与 US 站一样直接使用原始英语列名，无需翻译映射。以下为项目使用的英语字段，实际是否提供及完整字段集合以 AU 报告版本为准。

| 英语列名 | 核对用途 |
|---|---|
| date/time | 账单日期范围 |
| settlement id | 结算标识 |
| type | 类型汇总 |
| order id | 查询订单归属 |
| total | 汇总金额 |
| Transaction Status | 是否提供及报告版本差异 |
| Transaction Release Date | 是否提供及结算口径日期 |

## Type 映射

直接使用原始英语 type，无需语言转换。当前仅接受 [统一 Type 映射](../type_mapping.md) 表中的确切英语 Type 及排除项 `transfer`；未知或空 Type 即使金额为零也停止。实际类型枚举及拼写仍待 AU 原始 CSV 验收。

## 月份缩写映射

当前严格路径复用已有英语月份 `Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec`，另接受 `sept`，按完整词元匹配、忽略大小写、允许末尾点号。尚无 AU 实际日期文本，这是脚本的有限接受范围，不是本站导出格式已确认；不按国家惯例猜测数字日期顺序。

## 数字与日期格式

下表记录实际报告的证据状态；脚本已实现的有限接受范围见后文，不表示这些格式已经真实样本验证。

| 项目 | AU 格式 | 说明 |
|---|---|---|
| 小数点、千位分隔 | 待确认 | 需正负数及含千位分隔的原始金额 |
| 日期、12/24 小时制 | 待确认 | 不按国家习惯推定日期顺序 |
| 时区 | 待确认 | 不预设为澳大利亚本地时区或自动换算 |
| 编码、BOM、CSV 分隔符 | 待确认 | 需保留原始文件字节验证 |

## 代码引用

解析入口见 [`scripts/reconcile.py`](../../scripts/reconcile.py)：`CANDIDATE_COLUMNS['AU']` 保持空映射使标准英语列名直通，`CANDIDATE_MONTHS['AU']`、`parse_candidate_date` 和 `parse_candidate_csv` 执行严格校验。脚本不会读取本 Markdown，尚未完成 AU 实际账单验收。

- 使用 `--site AU`；日期接受英语 `MMM D, YYYY` 或 `DD MMM YYYY`，可只有日期，或加 24 小时制 `HH:mm:ss`／明确 AM/PM 的 12 小时制时间。不猜测 `01/02/2026` 的日月顺序。
- 时区仅接受 `PDT`、`PST`、`UTC`、`GMT`、`GMT-数字` 或无后缀；`AEDT` 等未配置标记会报错，不自动补充或换算。
- 当前入口仅接受 UTF-8（含 BOM）及逗号分隔；金额按全文件唯一、无歧义语法解析，不直接套用 US 小数点规则。英语 FBA 长名称先规范为 `FBA Transaction fees` 后汇总。
- 结算模式要求每条非 Transfer 记录有有效 `Transaction Release Date`，入账模式允许释放日期缺失；非空释放日期在两种模式下都需有效。完整规则见 [新增路径的受限解析边界](../type_mapping.md#新增路径的受限解析边界)。

按 [执行脚本](../../SKILL.md#执行脚本) 中与当前 shell 对应的绝对路径命令运行，末尾追加 `--site AU`；日期口径保持 `--date-type datetime`。Skill 根目录取实际加载位置，不切换当前工作目录。

## 来源与验证边界

- [AU 官方日期范围报告帮助入口](https://sellercentral.amazon.com.au/help/hub/reference/external/G200989190?locale=zh-CN)：报告功能线索，页面语言参数不代表 CSV 导出语言，也不能代替原始样本。
- 用户已确认：AU 站与 US 站一样使用英语。
- 待提供脱敏原始 CSV 后，核对完整表头、实际 Type、日期及金额格式；需记录报告期间、生成时间和导出语言，并保留前置说明行、编码、引号、分隔符和原始数字格式。合成测试只验证解析逻辑，不是实际导出证据。
