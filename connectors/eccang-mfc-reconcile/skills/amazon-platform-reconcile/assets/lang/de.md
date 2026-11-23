# 德语（DE）映射

脚本自动检测德语 CSV（通过 `Datum/Uhrzeit` 列头），自动转换列名和类型为英文后处理。

## 表头检测标识

`Datum/Uhrzeit`

## 列名映射（DE_TO_EN_COLUMNS）

| 德语列名 | 英语列名 |
|---|---|
| Datum/Uhrzeit | date/time |
| Abrechnungsnummer | settlement id |
| Typ | type |
| Bestellnummer | order id |
| SKU | sku |
| Beschreibung | description |
| Menge | quantity |
| Marketplace | marketplace |
| Versand | fulfillment |
| Ort der Bestellung | order city |
| Bundesland | order state |
| Postleitzahl | order postal |
| Steuererhebungsmodell | tax collection model |
| Umsätze | product sales |
| Produktumsatzsteuer | product sales tax |
| Gutschrift für Versandkosten | shipping credits |
| Steuer auf Versandgutschrift | shipping credits tax |
| Gutschrift für Geschenkverpackung | gift wrap credits |
| Steuer auf Geschenkverpackungsgutschriften | giftwrap credits tax |
| Rabatte aus Werbeaktionen | promotional rebates |
| Steuer auf Aktionsrabatte | promotional rebates tax |
| Einbehaltene Steuer auf Marketplace | marketplace withheld tax |
| Verkaufsgebühren | selling fees |
| Gebühren zu Versand durch Amazon | fba fees |
| Andere Transaktionsgebühren | other transaction fees |
| Andere | other |
| Gesamt | total |
| Transaktionsstatus | Transaction Status |
| Freigabedatum der Transaktion | Transaction Release Date |

## Type 映射（DE_TO_EN_TYPE）

| 德语 Type | 英语 Type |
|---|---|
| Bestellung | Order |
| Erstattung | Refund |
| Servicegebühr | Service Fee |
| Versand durch Amazon Lagergebühr | FBA Inventory Fee |
| Übertrag | Transfer |
| Gebühren von Amazon | Amazon Fees |
| Anpassung | Adjustment |
| Liquidationen | Liquidations |
| Versanddienstleistungen | Shipping Services |
| Transaktionsgebühren für Versand durch Amazon | FBA Transaction fees |
| Liquidationsanpassungen | Liquidations Adjustments |
| Bestellung_Wiedereinzug | Order_Retrocharge |
| Erstattung_Wiedereinzug | Refund_Retrocharge |
| Verbindlichkeit | Debt |
| Sonstiges | Others |
| Gebührenanpassung | Fee Adjustment |
| Rückbuchungserstattung | Chargeback Refund |
| Lightning Deal Gebühr | Lightning Deal Fee |

## 数字与日期格式

| 项目 | 德语格式 | 英语格式 | 说明 |
|---|---|---|---|
| 小数点 | `17,54` | `17.54` | 德语用逗号，英语用点 |
| 千位分隔 | `1.202,56` | `1,202.56` | 德语用点，英语用逗号 |
| 日期 | `01.03.2026 09:17:52 UTC` | `Mar 1, 2026 9:17:52 AM PST` | DD.MM.YYYY 格式 |

## 代码引用

`scripts/reconcile.py` 中的 `DE_TO_EN_COLUMNS`、`DE_TO_EN_TYPE`
