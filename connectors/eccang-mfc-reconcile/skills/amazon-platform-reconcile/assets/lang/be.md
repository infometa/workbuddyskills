# 比利时（BE）映射

适用于 BE（比利时）站日期范围交易报告的候选字段整理。目前仅有法语历史字段线索；本文件不代表已覆盖该站的全部导出语言。

> 状态：候选规则已受限接入，待样本验收。法语列名与月份来自 2023 年第三方历史实现，未通过当前原始 CSV 验证；已提供独立解析路径，不代表 BE 实际账单已验收。荷兰语等其他导出语言待确认。

## 表头检测标识

`date/heure`（法语历史候选）与 FR 相同，不能单独区分站点。`auto` 仅在同时存在 `Identifiant du paiement` 或 `Numéro de la commande` 时选择 BE 受限路径；若混入 FR 特征 `numéro de versement` 或 `numéro de la commande` 则报冲突。显式 `--site BE` 仍须满足上述表头条件，不强制套用其他法语格式。

## 列名映射（法语候选）

| BE 法语列名 | 英语列名 |
|---|---|
| date/heure | date/time |
| Identifiant du paiement | settlement id |
| type | type |
| Numéro de la commande | order id |
| SKU | sku |
| description | description |
| quantité | quantity |
| site de vente | marketplace |
| expédition | fulfillment |
| ventes de produits | product sales |
| crédits d’expédition | shipping credits |
| crédits d’emballage-cadeau | gift wrap credits |
| Total des réductions | promotional rebates |
| frais de vente | selling fees |
| Frais pour le service Expédié par Amazon | fba fees |
| autres frais de transaction | other transaction fees |
| autres | other |
| total | total |

保留大小写与弯引号。`Identifiant du paiement`、`Numéro de la commande`、`Frais pour le service Expédié par Amazon` 等不能假定已由 [FR 映射](fr.md) 覆盖。税费及订单地址字段待完整表头复核后补齐。

`Transaction Status`、`Transaction Release Date` 的实际列名与适用报告版本待确认；未列出不代表实际报告没有这些字段。

## Type 映射（待确认）

| BE 原始 Type | 英语 Type |
|---|---|
| 待原始 CSV 确认 | 待确认 |

不直接套用 FR 交易类型表，也不为荷兰语自行翻译生成枚举；目标类型参见 [统一 Type 映射](../type_mapping.md)。

## 月份缩写映射（法语历史候选）

| 法语 | 英语 |
|---|---|
| janv | Jan |
| févr | Feb |
| mars | Mar |
| avr | Apr |
| mai | May |
| juin | Jun |
| juil | Jul |
| août | Aug |
| sept | Sep |
| oct | Oct |
| nov | Nov |
| déc | Dec |

来源会移除月份中的点号并转为小写；当前 CSV 是否采用这些写法仍待确认。荷兰语月份不作为 BE 已验证格式收录。

## 数字与日期格式

下表记录实际报告的证据状态；脚本已实现的有限接受范围见后文，不表示这些格式已经真实样本验证。

| 项目 | BE 格式 | 说明 |
|---|---|---|
| 小数点、千位分隔 | 待确认 | 不因法语表头而默认与 FR 相同 |
| 日期 | `DD MMM YYYY` 加时间（法语历史候选） | 尚无原始日期样例；月份标点、12/24 小时制待确认 |
| 时区 | 待确认 | 不根据站点推定或自动换算 |
| 编码、BOM、CSV 分隔符 | 待确认 | 表头文本不能证明文件字节格式 |

## 代码引用

解析入口见 [`scripts/reconcile.py`](../../scripts/reconcile.py)：`CANDIDATE_COLUMNS['BE']`、`CANDIDATE_MONTHS['BE']`、`detect_candidate_site` 及 `parse_candidate_csv`。脚本不会读取本 Markdown，BE 与既有 FR 路径独立。

- 当前只接受统一表中的确切英语 Type 及 `transfer`；未知或空本地化 Type 会停止，零金额也不例外，不借用 FR 的 `Commande` 等映射。
- 日期接受本表完整法语月份词元和 `DD MMM YYYY`，月份末尾可带点号，保留 `févr`、`août`、`déc` 等重音；可只有日期，或加 24 小时制时间／明确 AM/PM 的 12 小时制时间。荷兰语日期未接入 BE 配置。
- 当前入口仅接受 UTF-8（含 BOM）及逗号分隔；金额按全文件唯一、无歧义语法解析，不推定与 FR 使用相同小数点。时区只允许已配置后缀或无后缀，不自动换算。
- 结算模式要求每条非 Transfer 记录有有效的标准英语 `Transaction Release Date`；不猜测本地化列名。完整校验及错误边界见 [新增路径的受限解析边界](../type_mapping.md#新增路径的受限解析边界)。

## 来源与验证边界

- [历史多站点字段与月份配置（2023-07-08）](https://www.cnblogs.com/xiangshihua/p/17537388.html)：仅作法语候选依据，不是 Amazon 官方规范。
- [BE 官方日期范围报告帮助入口](https://sellercentral.amazon.com.be/help/hub/reference/external/G200989190)及[荷兰语页面入口](https://sellercentral.amazon.com.be/help/hub/reference/external/G200989190?mons_sel_locale=nl_BE)：帮助页面语言不证明实际 CSV 导出语言。
- 当前尚未取得 BE 原始 CSV；需按实际导出语言和报告版本分别核对完整表头、实际 Type、正负金额、日期、时区及交易释放日期。合成测试只验证解析逻辑，不是实际导出证据。
