# 日语（JP）映射

适用于 JP（日本）站日期范围交易报告的候选字段整理。文件名 `ja` 为日语语言代码，站点代码仍为 `JP`。

> 状态：候选规则已受限接入，待样本验收。依据官方帮助搜索摘要、公开教程及 2023 年第三方历史实现整理，未通过当前原始 CSV 验证；已提供独立解析路径，未知日语 Type 仍会停止，不能承诺 JP 实际账单完整可对账。

## 表头检测标识

`日付/時間`（候选，来自官方帮助搜索摘要）。`auto` 可据此选择 JP 受限路径，也可显式传 `--site JP`；表头不兼容则停止。历史第三方配置中的日本日期列被商品标题污染，已排除该错误值。

## 列名映射（候选）

除日期列外，下表主要沿用历史字段配置。官方帮助搜索摘要另有 `決済番号`、`合計` 线索，但不构成完整原始表头验证。

| 日语列名 | 英语列名 |
|---|---|
| 日付/時間 | date/time |
| 決済番号 | settlement id |
| トランザクションの種類 | type |
| 注文番号 | order id |
| SKU | sku |
| 説明 | description |
| 数量 | quantity |
| Amazon 出品サービス | marketplace |
| フルフィルメント | fulfillment |
| 市町村 | order city |
| 都道府県 | order state |
| 郵便番号 | order postal |
| 税金徴収型 | tax collection model |
| 商品売上 | product sales |
| 商品の売上税 | product sales tax |
| 配送料 | shipping credits |
| 配送料の税金 | shipping credits tax |
| ギフト包装手数料 | gift wrap credits |
| ギフト包装クレジットの税金 | giftwrap credits tax |
| プロモーション割引額 | promotional rebates |
| プロモーション割引の税金 | promotional rebates tax |
| 源泉徴収税を伴うマーケットプレイス | marketplace withheld tax |
| 手数料 | selling fees |
| FBA 手数料 | fba fees |
| トランザクションに関するその他の手数料 | other transaction fees |
| その他 | other |
| 合計 | total |

历史来源把 `Amazonポイントの費用` 放在监管费税额项下，语义不符，未采纳；不能将积分费用擅自归入监管费税额。

`Transaction Status`、`Transaction Release Date` 的实际列名、是否提供及适用版本待确认，不自行翻译补入映射。

## Type 映射（待确认）

| 日语 Type | 英语 Type |
|---|---|
| 待原始 CSV 确认 | 待确认 |

已找到 `トランザクションの種類` 列名线索，但尚无可逐项核实的实际 Type 枚举。目标类型参见 [统一 Type 映射](../type_mapping.md)，不将商品描述或费用列标题当作 Type。

## 月份缩写映射

暂无已核实的日语月份缩写。历史解析使用斜杠分隔的数字日期，不需要月份名称转换；这不代表所有报告版本均采用相同格式。

## 数字与日期格式

下表记录实际报告的证据状态；脚本已实现的有限接受范围见后文，不表示这些格式已经真实样本验证。

| 项目 | JP 格式 | 说明 |
|---|---|---|
| 小数点、千位分隔、精度 | 待确认 | 不因日元惯例而推定 CSV 没有小数 |
| 日期 | `YYYY/MM/DD` 加时间（历史候选） | 尚无当前原始日期样例；位数、12/24 小时制待确认 |
| 时区 | 待确认 | 不根据站点推定为 JST 或自动换算 |
| CSV 分隔符 | 逗号（教程线索） | 尚未取得原始文件进行字节级验证 |
| 编码、BOM | 待确认 | 教程中的编码转换步骤不能证明原始文件统一采用某种编码 |

## 代码引用

解析入口见 [`scripts/reconcile.py`](../../scripts/reconcile.py)：`CANDIDATE_COLUMNS['JP']`、`CANDIDATE_MARKERS`、`parse_candidate_date` 的数字日期分支及 `parse_candidate_csv`。脚本不会读取本 Markdown。

- 当前只接受统一表中的确切英语 Type 及 `transfer`；未知或空日语 Type 会停止，零金额也不例外。日语表头可识别不等于日语交易类型已覆盖。
- 日期接受 `YYYY/MM/DD`，月、日允许一位或两位；可只有日期，或加 24 小时制 `HH:mm:ss`／明确 AM/PM 的 12 小时制时间。不需要月份翻译，不接受污染日期值。
- 时区仅接受 `PDT`、`PST`、`UTC`、`GMT`、`GMT-数字` 或无后缀；`JST` 尚未配置，会报错，不按 JP 自动补充或换算。
- 当前入口仅接受 UTF-8（含 BOM）及逗号分隔；金额按全文件唯一、无歧义语法解析，不推定日元无小数。结算模式要求每条非 Transfer 记录有有效的标准英语 `Transaction Release Date`，不猜测日语列名。完整规则见 [新增路径的受限解析边界](../type_mapping.md#新增路径的受限解析边界)。

按 [执行脚本](../../SKILL.md#执行脚本) 中与当前 shell 对应的绝对路径命令运行，末尾追加 `--site JP`；日期口径保持 `--date-type datetime`。Skill 根目录取实际加载位置，不切换当前工作目录。

## 来源与验证边界

- [JP 官方日期范围报告帮助入口](https://sellercentral.amazon.co.jp/help/hub/reference/external/G200989190)：本次仅取得相关搜索摘要，未完整获取帮助正文。
- [日语交易报告教程](https://www.tool4seller.com/jp/blog/transaction-report.html)：有 CSV 逗号分隔说明及列名线索；教程中的固定前置行数不能推广到所有报告。
- [历史多站点字段与日期配置（2023-07-08）](https://www.cnblogs.com/xiangshihua/p/17537388.html)：仅作候选依据，已排除发现的污染值和错位字段。
- 当前尚未取得 JP 原始 CSV；标记实际格式已验收前，需核对完整表头、实际 Type、正负金额、日期、时区及交易释放日期，并按报告版本分别验证。合成测试只验证解析逻辑，不是实际导出证据。
