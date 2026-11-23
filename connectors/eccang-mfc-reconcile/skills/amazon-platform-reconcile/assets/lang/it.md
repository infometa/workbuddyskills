# 意大利语（IT）映射

脚本自动检测意大利语 CSV（通过 `Data/Ora:` 列头），自动转换列名和类型为英文后处理。

## 表头检测标识

`Data/Ora:`

## 列名映射（IT_TO_EN_COLUMNS）

| 意大利语列名 | 英语列名 |
|---|---|
| Data/Ora: | date/time |
| Numero pagamento | settlement id |
| Tipo | type |
| Numero ordine | order id |
| SKU | sku |
| Descrizione | description |
| Quantità | quantity |
| Marketplace | marketplace |
| Gestione | fulfillment |
| Città di provenienza dell'ordine | order city |
| Provincia di provenienza dell'ordine | order state |
| CAP dell'ordine | order postal |
| modello di riscossione delle imposte | tax collection model |
| Vendite | product sales |
| imposta sulle vendite dei prodotti | product sales tax |
| Accrediti per le spedizioni | shipping credits |
| imposta accrediti per le spedizioni | shipping credits tax |
| Accrediti per confezioni regalo | gift wrap credits |
| imposta sui crediti confezione regalo | giftwrap credits tax |
| Sconti promozionali | promotional rebates |
| imposta sugli sconti promozionali | promotional rebates tax |
| trattenuta IVA del marketplace | marketplace withheld tax |
| Commissioni di vendita | selling fees |
| Costi del servizio Logistica di Amazon | fba fees |
| Altri costi relativi alle transazioni | other transaction fees |
| Altro | other |
| totale | total |

## Type 映射（IT_TO_EN_TYPE）

| 意大利语 Type | 英语 Type |
|---|---|
| Ordine | Order |
| Rimborso | Refund |
| Trasferimento | Transfer |
| Commissione di servizio | Service Fee |
| Costo di stoccaggio Logistica di Amazon | FBA Inventory Fee |
| Tariffe e commissioni Amazon | Amazon Fees |
| Tariffe e commissioni Amazon - Correzione | Fee Adjustment |
| Tariffe e commissioni Amazon - Inversione | Amazon Fees |
| Adeguamento | Adjustment |
| Liquidazioni | Liquidations |
| Servizi di spedizione | Shipping Services |
| Commissioni sulle transazioni di Logistica di Amazon | FBA Transaction fees |
| Rettifiche di liquidazione | Liquidations Adjustments |
| Ordine_Retro-addebito | Order_Retrocharge |
| Rimborso_Retro-addebito | Refund_Retrocharge |
| Debito | Debt |
| Altro | Others |
| Rimborso da chargeback | Chargeback Refund |
| Commissione Lightning Deal | Lightning Deal Fee |

## 月份缩写映射（IT_MONTH_MAP）

| 意大利语 | 英语 |
|---|---|
| gen | Jan |
| feb | Feb |
| mar | Mar |
| apr | Apr |
| mag | May |
| giu | Jun |
| lug | Jul |
| ago | Aug |
| set | Sep |
| ott | Oct |
| nov | Nov |
| dic | Dec |

## 数字与日期格式

| 项目 | 意大利语格式 | 英语格式 | 说明 |
|---|---|---|---|
| 数字 | `-387,70` | `-387.70` | 逗号为小数点（同法语/德语） |
| 日期 | `2 gen 2026 14:13:41 UTC` | `Jan 2, 2026 2:13:41 PM PST` | 日 月缩写 年 24h时间 时区 |

脚本自动替换月份缩写，重组为英文格式解析。

## 代码引用

`scripts/reconcile.py` 中的 `IT_TO_EN_COLUMNS`、`IT_TO_EN_TYPE`、`IT_MONTH_MAP`
