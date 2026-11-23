# 西班牙语（ES 西班牙）映射

适用于 ES（西班牙）站日期范围交易报告的候选字段整理。MX（墨西哥）站的既有映射仍见 [es.md](es.md)，两者不能直接互换。

> 状态：候选规则已受限接入，待样本验收。列名与月份来自 2023 年第三方历史实现，未通过当前原始 CSV 验证；已提供独立解析路径，不代表 ES 实际账单已验收。

## 表头检测标识

`fecha y hora`（历史候选；不同于 MX 的 `fecha/hora`）。`auto` 可据此选择 ES 受限路径，也可显式传 `--site ES`；表头不兼容则停止。不能仅凭西班牙语或站点名称判断实际导出格式。

## 列名映射（候选）

| 西班牙语列名 | 英语列名 |
|---|---|
| fecha y hora | date/time |
| identificador de pago | settlement id |
| tipo | type |
| número de pedido | order id |
| sku | sku |
| descripción | description |
| cantidad | quantity |
| web de Amazon | marketplace |
| gestión logística | fulfillment |
| ciudad de procedencia del pedido | order city |
| comunidad autónoma de procedencia del pedido | order state |
| código postal de procedencia del pedido | order postal |
| Formulario de recaudación de impuestos | tax collection model |
| ventas de productos | product sales |
| impuesto de ventas de productos | product sales tax |
| abonos de envío | shipping credits |
| impuestos por abonos de envío | shipping credits tax |
| abonos de envoltorio para regalo | gift wrap credits |
| devoluciones promocionales | promotional rebates |
| impuesto retenido en el sitio web | marketplace withheld tax |
| tarifas de venta | selling fees |
| tarifas de Logística de Amazon | fba fees |
| tarifas de otras transacciones | other transaction fees |
| otro | other |
| total | total |

历史来源中的部分税费列使用英文占位，未作为西班牙语映射收录。`Transaction Status`、`Transaction Release Date` 的实际列名与适用报告版本待确认；未列出不代表实际报告没有这些字段。

## Type 映射（待确认）

| 西班牙语 Type | 英语 Type |
|---|---|
| 待原始 CSV 确认 | 待确认 |

尚无 ES 站实际 Type 枚举依据，不直接套用 MX 的 `Pedido`、`Reembolso` 等映射。目标英语类型见 [统一 Type 映射](../type_mapping.md)，其中的类型不代表本次已经在 ES 报告中观察到。

## 月份缩写映射（历史候选）

| 西班牙语 | 英语 |
|---|---|
| ene | Jan |
| feb | Feb |
| mar | Mar |
| abr | Apr |
| may | May |
| jun | Jun |
| jul | Jul |
| ago | Aug |
| sep / sept | Sep |
| oct | Oct |
| nov | Nov |
| dic | Dec |

`sep / sept` 表示两个历史候选写法，不是包含斜杠的字面值。来源还包含其他语言和数字日期的回退分支，不能据此认定这些格式均属于 ES 当前导出规范。

## 数字与日期格式

下表记录实际报告的证据状态；脚本已实现的有限接受范围见后文，不表示这些格式已经真实样本验证。

| 项目 | ES 格式 | 说明 |
|---|---|---|
| 小数点、千位分隔 | 待确认 | 不套用 MX 的点小数格式，也不按国家习惯推定 |
| 日期 | `DD MMM YYYY` 加时间（历史候选） | 尚无原始日期样例；月份标点、12/24 小时制待确认 |
| 时区 | 待确认 | 不根据站点推定或自动换算 |
| 编码、BOM、CSV 分隔符 | 待确认 | 历史字段配置不能证明文件字节格式 |

## 代码引用

解析入口见 [`scripts/reconcile.py`](../../scripts/reconcile.py)：`CANDIDATE_COLUMNS['ES']`、`CANDIDATE_MARKERS`、`CANDIDATE_MONTHS['ES']` 及 `parse_candidate_csv`。脚本不会读取本 Markdown，ES 与既有 MX 路径独立。

- 当前只接受统一表中的确切英语 Type 及 `transfer`；`Pedido`、`Reembolso` 等未配置 ES 本地化 Type 会停止，零金额也不例外。
- 日期接受本表完整月份词元（含 `sep`／`sept`、末尾点号）和 `DD MMM YYYY`；可只有日期，或加 24 小时制时间／明确 AM/PM 的 12 小时制时间。保留重音，不借用 MX 月份解析。
- 当前入口仅接受 UTF-8（含 BOM）及逗号分隔；金额按全文件唯一、无歧义语法解析，不推定 ES 小数点。时区只允许已配置后缀或无后缀，不自动换算。
- 结算模式要求每条非 Transfer 记录有有效的标准英语 `Transaction Release Date`；不猜测本地化列名。完整校验及错误边界见 [新增路径的受限解析边界](../type_mapping.md#新增路径的受限解析边界)。

## 来源与验证边界

- [历史多站点字段与月份配置（2023-07-08）](https://www.cnblogs.com/xiangshihua/p/17537388.html)：仅作候选依据，不是 Amazon 官方规范。
- 当前尚未取得 ES 原始 CSV；标记实际格式已验收前，需核对完整表头、实际 Type、正负金额、月份、时区及交易释放日期，并按报告版本分别验证。合成测试只验证解析逻辑，不是实际导出证据。
