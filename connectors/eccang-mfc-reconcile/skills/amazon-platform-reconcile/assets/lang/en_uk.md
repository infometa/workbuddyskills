# 英国（UK）英语映射

UK 站使用英文列头和英文 type（同 US），但日期格式和部分 type 名称有差异。

## 日期格式

| 项目 | UK 格式 | US 格式 | 说明 |
|---|---|---|---|
| 日期 | `1 Nov 2025 00:35:59 UTC` | `Nov 1, 2025 12:35:59 AM PST` | DD MMM YYYY 24h格式 |

脚本自动检测 `DD MMM YYYY` 格式并解析。

## 数字格式

同 US，点做小数点，逗号做千位分隔。

## Type 变体

| UK Type | 标准 Type | DB Type |
|---|---|---|
| Fulfilment by Amazon (FBA) transaction fees | FBA Transaction fees | fba_transaction_fees |

## 表头检测标识

`date/time`（同 US，通过日期格式 DD MMM YYYY 自动识别）

## 备注

- 列名与 US 基本一致
- `Fulfilment`（UK 拼写）vs `Fulfillment`（US 拼写）
- 24 小时制日期格式
