# 瑞典语（SE）映射

适用于 SE（瑞典）站日期范围交易报告的候选字段整理。文件名 `sv` 为瑞典语语言代码，站点代码仍为 `SE`。

> 状态：候选规则已受限接入，待样本验收。列名与月份来自 2023 年第三方历史实现，未通过当前原始 CSV 验证；已提供独立解析路径，不代表 SE 实际账单已验收。

## 表头检测标识

`datum/tid`（历史候选）。`auto` 可据此选择 SE 受限路径，也可显式传 `--site SE`；表头不兼容则停止。不能仅根据帮助页面语言确定 CSV 导出语言。

## 列名映射（候选）

| 瑞典语列名 | 英语列名 |
|---|---|
| datum/tid | date/time |
| reglerings-id | settlement id |
| typ | type |
| beställnings-id | order id |
| sku | sku |
| beskrivning | description |
| antal | quantity |
| marknadsplats | marketplace |
| leverans | fulfillment |
| försäljning av produkter | product sales |
| fraktkrediter | shipping credits |
| krediter för presentinslagning | gift wrap credits |
| kampanjrabatter | promotional rebates |
| försäljningsavgifter | selling fees |
| fba-avgifter | fba fees |
| övriga transaktionsavgifter | other transaction fees |
| Övrigt | other |
| totalt | total |

保留原始候选列名中的 `ä`、`ö` 和大小写，不将 `Övrigt` 自动改写成其他拼写。税费及订单地址字段待完整表头复核后补齐。

`Transaction Status`、`Transaction Release Date` 的实际列名与适用报告版本待确认；未列出不代表实际报告没有这些字段。

## Type 映射（待确认）

| 瑞典语 Type | 英语 Type |
|---|---|
| 待原始 CSV 确认 | 待确认 |

尚无可核实的 SE 站 Type 枚举，不使用自行翻译的名称作为正式映射；目标类型参见 [统一 Type 映射](../type_mapping.md)。

## 月份缩写映射（历史候选）

| 瑞典语 | 英语 |
|---|---|
| jan | Jan |
| feb | Feb |
| mars | Mar |
| apr | Apr |
| maj | May |
| juni | Jun |
| juli | Jul |
| aug | Aug |
| sep / sept | Sep |
| okt | Oct |
| nov | Nov |
| dec | Dec |

`sep / sept` 表示两个历史候选写法，不是包含斜杠的字面值。来源中的跨语言回退逻辑不作为瑞典语 CSV 规范收录。

## 数字与日期格式

下表记录实际报告的证据状态；脚本已实现的有限接受范围见后文，不表示这些格式已经真实样本验证。

| 项目 | SE 格式 | 说明 |
|---|---|---|
| 小数点、千位分隔 | 待确认 | 需核对实际金额及空格字符，不按国家习惯推定 |
| 日期 | `DD MMM YYYY` 加时间（历史候选） | 尚无原始日期样例；月份标点、12/24 小时制待确认 |
| 时区 | 待确认 | 不根据站点推定或自动换算 |
| 编码、BOM、CSV 分隔符 | 待确认 | 表头文本不能证明文件字节格式 |

## 代码引用

解析入口见 [`scripts/reconcile.py`](../../scripts/reconcile.py)：`CANDIDATE_COLUMNS['SE']`、`CANDIDATE_MARKERS`、`CANDIDATE_MONTHS['SE']` 及 `parse_candidate_csv`。脚本不会读取本 Markdown。

- 当前只接受统一表中的确切英语 Type 及 `transfer`；未知或空本地化 Type 会停止，零金额也不例外。
- 日期接受本表完整月份词元（含 `sep`／`sept`、末尾点号）和 `DD MMM YYYY`；可只有日期，或加 24 小时制时间／明确 AM/PM 的 12 小时制时间，不进入跨语言月份猜测。
- 当前入口仅接受 UTF-8（含 BOM）及逗号分隔；金额按全文件唯一、无歧义语法解析，不推定 SE 小数点，暂不接受空格千分位。时区只允许已配置后缀或无后缀，不自动换算。
- 结算模式要求每条非 Transfer 记录有有效的标准英语 `Transaction Release Date`；不猜测本地化列名。完整校验及错误边界见 [新增路径的受限解析边界](../type_mapping.md#新增路径的受限解析边界)。

## 来源与验证边界

- [历史多站点字段与月份配置（2023-07-08）](https://www.cnblogs.com/xiangshihua/p/17537388.html)：仅作候选依据，不是 Amazon 官方规范。
- [SE 官方日期范围报告帮助入口](https://sellercentral.amazon.se/help/hub/reference/external/200989190?locale=zh-CN)：报告功能线索，页面显示语言不证明导出语言。
- 当前尚未取得 SE 原始 CSV；标记实际格式已验收前，需核对完整表头、实际 Type、正负金额、月份、时区及交易释放日期，并按报告版本分别验证。合成测试只验证解析逻辑，不是实际导出证据。
