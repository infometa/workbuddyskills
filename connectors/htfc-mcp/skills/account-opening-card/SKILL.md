---
name: account-opening-card
description: 返回期货预约开户卡片。当用户表达开户意愿，如询问怎么开户、想开期货账户、如何预约开户时使用。
---

# 预约开户卡片（account-opening-card）

## 用途

返回一张可点击的预约开户卡片，用于登记开户预约信息并跳转后续开户流程。本工具不需要期赢通 API Key。

## 参数

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| `query` | 否 | 用户原始问题，用于下游统计与归因 |

## 返回

`content[0].text` 为 Python dict 字面量（单引号），不能按 JSON 解析。其中的业务字段：

| 字段 | 说明 |
| --- | --- |
| `cards[].label` | 按钮文案 |
| `cards[].url` | 完整跳转链接 |
| `cards[].card_html` | 可直接渲染的卡片 HTML |
| `cards[].markdown_link` | Markdown 形式的链接 |
| `cards[].notice` | 合规提示语，须一并展示 |

`url`、`card_html`、`markdown_link` 中的链接均为完整地址，须原样透传，不要截断或改写。

## 调用示例

```json
{"jsonrpc":"2.0","id":5,"method":"tools/call","params":{"name":"get_account_opening_card","arguments":{"query":"我想开一个期货账户"}}}
```

## 合规提示

该入口仅为预约开户登记，不代表开户完成、审核通过或账户已开通。展示卡片时须保留 `notice` 文案，不要向用户承诺开户结果。
