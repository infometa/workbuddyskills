# 查询个人票夹

## 什么时候读取

用户要查询个人票夹、搜索自己的发票，或按报销状态筛选个人发票时读取本文件。

## Operation

| Operation | 固定规则 |
| --- | --- |
| `invoice.list` | 固定 `flag=0`；默认 `sreim="3"`、`bill_type=0`，只查未报销发票 |

## 输入

列表字段以 `weaver-work-cli invoice schema` 为准。常用字段：

- `page_size`、`start_pos`
- `content`
- `date_begin`、`date_end`
- `create_tm_begin`、`create_tm_end`
- `payer_company`、`buyer_company`
- `payer_taxno`、`buyer_taxno`
- `code`、`number`
- `total_begin`、`total_end`
- `valids`、`sources`、`types`
- `sorts`
- `sreim`（只有用户明确指定报销状态时才传）
- `bill_type`（只有用户明确要求查凭证时才传）

`sreim` 是字符串类型的查询筛选参数：`"0"` 获取全部发票，`"1"` 发票报销中，`"2"` 报销完成，`"3"` 获取未报销发票，`"4"` 获取不可报销。用户没有明确要求“全部发票/已报销/报销中/不可报销”时，必须省略 `sreim`，让 CLI 默认传 `"3"` 查询未报销发票。不要为了“最近发票”“查询发票”“个人票夹”主动传 `sreim="0"`。

`bill_type` 是票据类型筛选参数：`0` 获取发票，`1` 获取凭证。用户没有明确要求“凭证”时，必须省略 `bill_type`，让 CLI 默认传 `0` 查询发票。

## 示例

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json invoice run invoice.list --input-json '{"page_size":10,"start_pos":0,"content":"滴滴"}'

weaver-work-cli --profile eteams --json invoice run invoice.list --input-json '{"page_size":10,"start_pos":0,"sreim":"2"}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json invoice run invoice.list --input-json '{"page_size":10,"start_pos":0,"content":"滴滴"}'

weaver-work-cli --profile eteams --json invoice run invoice.list --input-json '{"page_size":10,"start_pos":0,"sreim":"2"}'
```

## 返回

返回 `items`、`total`、`totalAmount`、`totalAmountExcludingTax`、`hasMore` 和 `scope="personal"`。分页时递增 `start_pos`，保持筛选条件和排序不变。

## 注意

不要在输入里传 `flag`；即使传入也会被 CLI 忽略并固定为个人票夹。空筛选条件直接省略，不要把空字符串传给 integer 字段。除非用户明确要求全部或某个报销状态，否则不要传 `sreim`；除非用户明确要求凭证，否则不要传 `bill_type`。
