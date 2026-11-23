# 波兰语（PL）映射

适用于 PL（波兰）站日期范围交易报告的候选字段整理。

> 状态：候选规则已受限接入，待样本验收。列名与月份来自 2023 年第三方历史实现，未通过当前原始 CSV 验证；已提供独立解析路径，不代表 PL 实际账单已验收。

## 表头检测标识

`data/godzina`（历史候选）。`auto` 可据此选择 PL 受限路径，也可显式传 `--site PL`；表头不兼容则停止。不能仅根据帮助页面语言确定 CSV 导出语言。

## 列名映射（候选）

| 波兰语列名 | 英语列名 |
|---|---|
| data/godzina | date/time |
| identyfikator rozliczenia | settlement id |
| typ | type |
| identyfikator zamówienia | order id |
| sku | sku |
| opis | description |
| ilość | quantity |
| rynek | marketplace |
| realizacja | fulfillment |
| sprzedaż produktów | product sales |
| noty kredytowe za wysyłkę | shipping credits |
| rabaty promocyjne | promotional rebates |
| opłaty za sprzedaż | selling fees |
| opłaty za fba | fba fees |
| inne opłaty transakcyjne | other transaction fees |
| inne | other |
| suma | total |

保留波兰语重音字符。来源把疑似礼品包装字段放在 `shipping credits tax` 项下，且部分税费内容存在乱码，因此未收录该映射；礼品包装、税费及订单地址字段待完整表头复核后补齐。

`Transaction Status`、`Transaction Release Date` 的实际列名与适用报告版本待确认；未列出不代表实际报告没有这些字段。

## Type 映射（待确认）

| 波兰语 Type | 英语 Type |
|---|---|
| 待原始 CSV 确认 | 待确认 |

尚无可核实的 PL 站 Type 枚举，不使用自行翻译的名称作为正式映射；目标类型参见 [统一 Type 映射](../type_mapping.md)。

## 月份缩写映射（历史候选）

| 波兰语 | 英语 |
|---|---|
| sty | Jan |
| lut | Feb |
| mar | Mar |
| kwi | Apr |
| maj | May |
| cze | Jun |
| lip | Jul |
| sie | Aug |
| wrz | Sep |
| paź | Oct |
| lis | Nov |
| gru | Dec |

`paź` 中的 `ź` 不可替换为无重音的 `z`。月份是否有点号及其他写法需用原始 CSV 确认。

## 数字与日期格式

下表记录实际报告的证据状态；脚本已实现的有限接受范围见后文，不表示这些格式已经真实样本验证。

| 项目 | PL 格式 | 说明 |
|---|---|---|
| 小数点、千位分隔 | 待确认 | 需核对实际金额及空格字符，不按国家习惯推定 |
| 日期 | `DD MMM YYYY` 加时间（历史候选） | 尚无原始日期样例；月份标点、12/24 小时制待确认 |
| 时区 | 待确认 | 不根据站点推定或自动换算 |
| 编码、BOM、CSV 分隔符 | 待确认 | 表头文本不能证明文件字节格式 |

## 代码引用

解析入口见 [`scripts/reconcile.py`](../../scripts/reconcile.py)：`CANDIDATE_COLUMNS['PL']`、`CANDIDATE_MARKERS`、`CANDIDATE_MONTHS['PL']` 及 `parse_candidate_csv`。脚本不会读取本 Markdown。

- 当前只接受统一表中的确切英语 Type 及 `transfer`；未知或空本地化 Type 会停止，零金额也不例外。
- 日期接受本表完整月份词元和 `DD MMM YYYY`，月份末尾可带点号，`paź` 必须保留重音；可只有日期，或加 24 小时制时间／明确 AM/PM 的 12 小时制时间，不进入跨语言月份猜测。
- 当前入口仅接受 UTF-8（含 BOM）及逗号分隔；金额按全文件唯一、无歧义语法解析，不推定 PL 小数点，暂不接受空格千分位。时区只允许已配置后缀或无后缀，不自动换算。
- 结算模式要求每条非 Transfer 记录有有效的标准英语 `Transaction Release Date`；不猜测本地化列名。完整校验及错误边界见 [新增路径的受限解析边界](../type_mapping.md#新增路径的受限解析边界)。

## 来源与验证边界

- [历史多站点字段与月份配置（2023-07-08）](https://www.cnblogs.com/xiangshihua/p/17537388.html)：仅作候选依据，不是 Amazon 官方规范。
- [PL 官方日期范围报告帮助入口](https://sellercentral.amazon.pl/help/hub/reference/external/G200989190?locale=zh-CN)：报告功能线索，页面显示语言不证明导出语言。
- 当前尚未取得 PL 原始 CSV；标记实际格式已验收前，需核对完整表头、实际 Type、正负金额、月份、时区及交易释放日期，并按报告版本分别验证。合成测试只验证解析逻辑，不是实际导出证据。
