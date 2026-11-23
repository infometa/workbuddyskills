# 法语（FR）映射

脚本自动检测法语 CSV（通过 `date/heure` 列头），自动转换列名和类型为英文后处理。

## 表头检测标识

`date/heure`

## 列名映射（FR_TO_EN_COLUMNS）

| 法语列名 | 英语列名 |
|---|---|
| date/heure | date/time |
| numéro de versement | settlement id |
| type | type |
| numéro de la commande | order id |
| quantité | quantity |
| Marketplace | marketplace |
| traitement | fulfillment |
| ville d'où provient la commande | order city |
| Région d'où provient la commande | order state |
| code postal de la commande | order postal |
| Modèle de perception des taxes | tax collection model |
| ventes de produits | product sales |
| Taxes sur la vente des produits | product sales tax |
| crédits d'expédition | shipping credits |
| taxe sur les crédits d'expédition | shipping credits tax |
| crédits sur l'emballage cadeau | gift wrap credits |
| Taxes sur les crédits cadeaux | giftwrap credits tax |
| Rabais promotionnels | promotional rebates |
| Taxes sur les remises promotionnelles | promotional rebates tax |
| Taxes retenues sur le site de vente | marketplace withheld tax |
| frais de vente | selling fees |
| Frais Expédié par Amazon | fba fees |
| autres frais de transaction | other transaction fees |
| autre | other |
| total | total |
| Statut de la transaction | Transaction Status |
| Date de sortie de la transaction | Transaction Release Date |

## Type 映射（FR_TO_EN_TYPE）

| 法语 Type | 英语 Type |
|---|---|
| Commande | Order |
| Remboursement | Refund |
| Frais de service | Service Fee |
| Frais de stock Expédié par Amazon | FBA Inventory Fee |
| Transfert | Transfer |
| Amazon Fees | Amazon Fees |
| Ajustement | Adjustment |
| Liquidations | Liquidations |
| Services de livraison | Shipping Services |
| Frais de transaction FBA | FBA Transaction fees |
| Ajustement des liquidations | Liquidations Adjustments |
| Commande_Retrocharge | Order_Retrocharge |
| Remboursement_Retrocharge | Refund_Retrocharge |
| Dette | Debt |
| Solde négatif | Debt |
| Autres | Others |
| Ajustement des frais | Fee Adjustment |
| Remboursement de rétrofacturation | Chargeback Refund |
| Frais de Lightning Deal | Lightning Deal Fee |

## 月份缩写映射（FR_MONTH_MAP）

| 法语 | 英语 |
|---|---|
| janv. | Jan |
| févr. | Feb |
| mars | Mar |
| avr. | Apr |
| mai | May |
| juin | Jun |
| juil. | Jul |
| août | Aug |
| sept. | Sep |
| oct. | Oct |
| nov. | Nov |
| déc. | Dec |

## 数字与日期格式

| 项目 | 法语格式 | 英语格式 | 说明 |
|---|---|---|---|
| 小数点 | `17,54` | `17.54` | 法语用逗号，英语用点 |
| 千位分隔 | `1.202,56` | `1,202.56` | 法语用点，英语用逗号 |
| 日期 | `2 avr. 2026 11:48:46 UTC` | `Apr 2, 2026 12:04:33 AM PST` | 日月顺序不同，月份缩写不同 |

## 代码引用

`scripts/reconcile.py` 中的 `FR_TO_EN_COLUMNS`、`FR_TO_EN_TYPE`、`FR_MONTH_MAP`
