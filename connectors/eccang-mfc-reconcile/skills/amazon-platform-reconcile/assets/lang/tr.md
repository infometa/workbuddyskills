# 土耳其语（TR）映射

适用于 TR（土耳其）站日期范围交易报告的候选字段整理。

> 状态：候选规则已受限接入，待样本验收。列名与月份来自 2023 年第三方历史实现，未通过当前原始 CSV 验证；已提供独立解析路径，不代表 TR 实际账单已验收。

## 表头检测标识

`tarih/saat`（历史候选）。`auto` 可据此选择 TR 受限路径，也可显式传 `--site TR`；表头不兼容则停止。不能仅根据帮助页面语言确定 CSV 导出语言。

## 列名映射（候选）

| 土耳其语列名 | 英语列名 |
|---|---|
| tarih/saat | date/time |
| hesap kesim no | settlement id |
| tip | type |
| sipariş no | order id |
| sku | sku |
| açıklama | description |
| adet | quantity |
| pazar yeri | marketplace |
| gönderim | fulfillment |
| ürün satışları | product sales |
| kargo kredileri | shipping credits |
| promosyon indirimleri | promotional rebates |
| satış ücretleri | selling fees |
| Amazon Lojistik ücretleri | fba fees |
| diğer işlem ücretleri | other transaction fees |
| diğer | other |
| toplam | total |

保留 `ı`、`ş`、`ğ`、`ü`、`ö`、`ç` 等原始字符，不以无重音拼写替换。税费、礼品包装及订单地址字段待完整表头复核后补齐。

`Transaction Status`、`Transaction Release Date` 的实际列名与适用报告版本待确认；未列出不代表实际报告没有这些字段。

## Type 映射（待确认）

| 土耳其语 Type | 英语 Type |
|---|---|
| 待原始 CSV 确认 | 待确认 |

尚无可核实的 TR 站 Type 枚举，不使用自行翻译的名称作为正式映射；目标类型参见 [统一 Type 映射](../type_mapping.md)。

## 月份缩写映射（历史候选）

| 土耳其语 | 英语 |
|---|---|
| Oca | Jan |
| Şub | Feb |
| Mar | Mar |
| Nis | Apr |
| May | May |
| Haz | Jun |
| Tem | Jul |
| Ağu | Aug |
| Eyl | Sep |
| Eki | Oct |
| Kas | Nov |
| Ara | Dec |

保留来源大小写和重音；月份是否存在其他写法需用原始 CSV 确认。

## 数字与日期格式

下表记录实际报告的证据状态；脚本已实现的有限接受范围见后文，不表示这些格式已经真实样本验证。

| 项目 | TR 格式 | 说明 |
|---|---|---|
| 小数点、千位分隔 | 待确认 | 不按国家习惯推定 |
| 日期 | `DD MMM YYYY` 加时间（历史候选） | 尚无原始日期样例；月份标点、12/24 小时制待确认 |
| 时区 | 待确认 | 不根据站点推定或自动换算 |
| 编码、BOM、CSV 分隔符 | 待确认 | 表头文本不能证明文件字节格式 |

## 代码引用

解析入口见 [`scripts/reconcile.py`](../../scripts/reconcile.py)：`CANDIDATE_COLUMNS['TR']`、`CANDIDATE_MARKERS`、`CANDIDATE_MONTHS['TR']` 及 `parse_candidate_csv`。脚本不会读取本 Markdown。

- 当前只接受统一表中的确切英语 Type 及 `transfer`；未知或空本地化 Type 会停止，零金额也不例外。
- 日期接受本表完整月份词元和 `DD MMM YYYY`，月份末尾可带点号，`Şub`、`Ağu` 等必须保留重音；可只有日期，或加 24 小时制时间／明确 AM/PM 的 12 小时制时间，不进入跨语言月份猜测。
- 当前入口仅接受 UTF-8（含 BOM）及逗号分隔；金额按全文件唯一、无歧义语法解析，不推定 TR 小数点。时区只允许已配置后缀或无后缀，不自动换算。
- 结算模式要求每条非 Transfer 记录有有效的标准英语 `Transaction Release Date`；不猜测本地化列名。完整校验及错误边界见 [新增路径的受限解析边界](../type_mapping.md#新增路径的受限解析边界)。

## 来源与验证边界

- [历史多站点字段与月份配置（2023-07-08）](https://www.cnblogs.com/xiangshihua/p/17537388.html)：仅作候选依据，不是 Amazon 官方规范。
- [TR 官方日期范围报告帮助入口](https://sellercentral.amazon.com.tr/help/hub/reference/external/G200989190?mons_sel_locale=tr_TR)：报告功能线索，页面显示语言不证明导出语言。
- 当前尚未取得 TR 原始 CSV；标记实际格式已验收前，需核对完整表头、实际 Type、正负金额、月份、时区及交易释放日期，并按报告版本分别验证。合成测试只验证解析逻辑，不是实际导出证据。
