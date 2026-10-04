# 查询企业票夹

## 什么时候读取

用户要查询企业票夹、搜索企业范围发票，或按报销状态筛选企业发票时读取本文件。

## Operation

| Operation | 固定规则 |
| --- | --- |
| `invoice.enterprise.list` | 固定 `flag=6`；默认 `sreim="3"`、`bill_type=0`，只查未报销发票 |

## 输入

列表字段以 `weaver-work-cli invoice schema` 为准，字段语义与个人票夹一致。常用字段包括 `page_size`、`start_pos`、`content`、购销方、日期、金额、票种、查验状态、来源和排序。`sreim` 只有用户明确指定报销状态时才传；`bill_type` 只有用户明确要求查凭证时才传。

`sreim` 是字符串类型的查询筛选参数：`"0"` 获取全部发票，`"1"` 发票报销中，`"2"` 报销完成，`"3"` 获取未报销发票，`"4"` 获取不可报销。用户没有明确要求“全部发票/已报销/报销中/不可报销”时，必须省略 `sreim`，让 CLI 默认传 `"3"` 查询未报销发票。

`bill_type` 是票据类型筛选参数：`0` 获取发票，`1` 获取凭证。用户没有明确要求“凭证”时，必须省略 `bill_type`，让 CLI 默认传 `0` 查询发票。

## 示例

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json invoice run invoice.enterprise.list --input-json '{"page_size":10,"start_pos":0,"buyer_company":"泛微"}'

weaver-work-cli --profile eteams --json invoice run invoice.enterprise.list --input-json '{"page_size":10,"start_pos":0,"sreim":"2"}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json invoice run invoice.enterprise.list --input-json '{"page_size":10,"start_pos":0,"buyer_company":"泛微"}'

weaver-work-cli --profile eteams --json invoice run invoice.enterprise.list --input-json '{"page_size":10,"start_pos":0,"sreim":"2"}'
```

## 返回

返回 `items`、`total`、`totalAmount`、`totalAmountExcludingTax`、`hasMore` 和 `scope="enterprise"`。

## 注意

企业票夹权限失败时不要自动降级查询个人票夹，除非用户明确要求改查个人票夹。不要在输入里传 `flag`；CLI 会固定为企业票夹。
