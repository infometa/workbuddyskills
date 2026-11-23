# 西班牙语（ES/MX）映射

脚本自动检测西班牙语 CSV（通过 `fecha/hora` 列头），自动转换列名和类型为英文后处理。适用于 MX（墨西哥）站。

## 表头检测标识

`fecha/hora`

## 列名映射（ES_TO_EN_COLUMNS）

| 西班牙语列名 | 英语列名 |
|---|---|
| fecha/hora | date/time |
| Id. de liquidación | settlement id |
| tipo | type |
| Id. del pedido | order id |
| descripción | description |
| cantidad | quantity |
| marketplace | marketplace |
| cumplimiento | fulfillment |
| ciudad del pedido | order city |
| estado del pedido | order state |
| código postal del pedido | order postal |
| modelo de recaudación de impuestos | tax collection model |
| ventas de productos | product sales |
| impuesto de ventas de productos | product sales tax |
| créditos de envío | shipping credits |
| impuesto de abono de envío | shipping credits tax |
| créditos por envoltorio de regalo | gift wrap credits |
| impuesto de créditos de envoltura | giftwrap credits tax |
| Tarifa reglamentaria | regulatory fee |
| Impuesto sobre tarifa reglamentaria | regulatory fee tax |
| descuentos promocionales | promotional rebates |
| impuesto de reembolsos promocionales | promotional rebates tax |
| impuesto de retenciones en la plataforma | marketplace withheld tax |
| tarifas de venta | selling fees |
| tarifas fba | fba fees |
| tarifas de otra transacción | other transaction fees |
| otro | other |
| total | total |
| Estado de la transacción | Transaction Status |
| Fecha de liberación de la transacción | Transaction Release Date |

## Type 映射（ES_TO_EN_TYPE）

| 西班牙语 Type | 英语 Type |
|---|---|
| Pedido | Order |
| Reembolso | Refund |
| Tarifa de servicio | Service Fee |
| Tarifa de inventario en logística de Amazon | FBA Inventory Fee |
| Trasferir | Transfer |
| Tarifas de Amazon | Amazon Fees |
| Ajuste | Adjustment |
| Liquidaciones | Liquidations |
| Servicios de envío | Shipping Services |
| Tarifas de transacción de logística de Amazon | FBA Transaction fees |
| Ajustes de liquidaciones | Liquidations Adjustments |
| Pedido_Retrocargo | Order_Retrocharge |
| Reembolso_Retrocargo | Refund_Retrocharge |
| Deuda | Debt |
| Otros | Others |
| Ajuste de tarifa | Fee Adjustment |
| Reembolso de contracargo | Chargeback Refund |
| Tarifa de oferta del día | Lightning Deal Fee |

## 月份缩写映射（ES_MONTH_MAP）

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
| sep | Sep |
| oct | Oct |
| nov | Nov |
| dic | Dec |

## 数字与日期格式

| 项目 | 西班牙语格式 | 英语格式 | 说明 |
|---|---|---|---|
| 小数点 | `668.94` | `668.94` | MX 站用点做小数点（同英语） |
| 日期 | `28 feb 2026 10:26:33 p.m. GMT-8` | `Feb 28, 2026 10:26:33 PM PST` | DD MMM YYYY，月份小写缩写，a.m./p.m. |

## 代码引用

`scripts/reconcile.py` 中的 `ES_TO_EN_COLUMNS`、`ES_TO_EN_TYPE`、`ES_MONTH_MAP`
