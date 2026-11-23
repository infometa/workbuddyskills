# 葡萄牙语（PT/BR）映射

脚本自动检测葡萄牙语 CSV（通过 `data/hora` 列头），自动转换列名和类型为英文后处理。适用于 BR（巴西）站。

## 表头检测标识

`data/hora`

## 列名映射（PT_TO_EN_COLUMNS）

| 葡萄牙语列名 | 英语列名 |
|---|---|
| data/hora | date/time |
| id de liquidação | settlement id |
| tipo | type |
| id do pedido | order id |
| sku | sku |
| descrição | description |
| quantidade | quantity |
| mercado | marketplace |
| tipo de conta | account type |
| atendimento | fulfillment |
| cidade do pedido | order city |
| estado do pedido | order state |
| postal do pedido | order postal |
| vendas do produto | product sales |
| créditos de remessa | shipping credits |
| créditos de embalagem de presente | gift wrap credits |
| descontos promocionais | promotional rebates |
| imposto de vendas coletados | marketplace withheld tax |
| tarifas de venda | selling fees |
| taxas fba | fba fees |
| taxas de outras transações | other transaction fees |
| outro | other |
| total | total |

## Type 映射（PT_TO_EN_TYPE）

| 葡萄牙语 Type | 英语 Type |
|---|---|
| Pedido | Order |
| Reembolso | Refund |
| Transferir | Transfer |
| Tarifa de serviço | Service Fee |
| Taxa de inventário FBA | FBA Inventory Fee |
| Taxas da Amazon | Amazon Fees |
| Ajuste | Adjustment |
| Liquidações | Liquidations |
| Serviços de envio | Shipping Services |
| Taxas de transação FBA | FBA Transaction fees |
| Ajustes de liquidações | Liquidations Adjustments |
| Pedido_Retrocobrança | Order_Retrocharge |
| Reembolso_Retrocobrança | Refund_Retrocharge |
| Débito | Debt |
| Outros | Others |
| Ajuste de taxa | Fee Adjustment |
| Reembolso de estorno | Chargeback Refund |
| Taxa de Lightning Deal | Lightning Deal Fee |

## 月份缩写映射（PT_MONTH_MAP）

| 葡萄牙语 | 英语 |
|---|---|
| jan. | Jan |
| fev. | Feb |
| mar. | Mar |
| abr. | Apr |
| mai. | May |
| jun. | Jun |
| jul. | Jul |
| ago. | Aug |
| set. | Sep |
| out. | Oct |
| nov. | Nov |
| dez. | Dec |

## 数字与日期格式

| 项目 | 葡萄牙语格式 | 英语格式 | 说明 |
|---|---|---|---|
| 数字 | `-8.873,00` | `-8873.00` | 点为千位分隔，逗号为小数点 |
| 日期 | `1 de dez. de 2025 07:26:52 GMT-8` | `Dec 1, 2025 7:26:52 AM PST` | 日 de 月缩写. de 年 时间 时区 |

脚本自动去除 `de` 连接词，替换月份缩写，重组为英文格式解析。

## 代码引用

`scripts/reconcile.py` 中的 `PT_TO_EN_COLUMNS`、`PT_TO_EN_TYPE`、`PT_MONTH_MAP`
