# 报价提交（quote）

> ⛔ **对外口径**：工具名与字段名仅供内部执行，禁止出现在给用户的文字里。
> 报价回显只用业务语言：标的、结构、收益率（百分比）、备注、条数。

## 工具

`bathInsertTraderQuote`：批量提交报价。

## 报文格式

纯数组，每条报价包含：

| 字段 | 说明 |
|------|------|
| `traderWechatId` / `traderId` / `traderDept` / `deptId` | 券商身份 4 字段 |
| `consultRecordId` | 询价 ID（来自查询结果，原样回传，勿解码） |
| `yield` | 报价收益率（小数，所见即所得：填 0.09 提交 0.09） |
| `quoteRemark` | 可选备注 |
| `maxScale` | 规模（去千分位逗号，如 "7,000" → "7000"） |

示例：

```json
[
  {
    "traderWechatId": "",
    "traderId": "",
    "traderDept": "",
    "deptId": "",
    "consultRecordId": "MjAyNjA5MDQwNDkyNjE=",
    "yield": 0.09,
    "quoteRemark": "可选备注",
    "maxScale": "7000"
  }
]
```

## 提交前确认（写操作，必须）

报价为写操作，提交前必须回显关键信息让用户确认：

- 结构名称、标的、收益率（说成百分比，如 `0.09` → **9%**）、备注；
- 明确告知报价条数。

回显时用业务语言，**不要**把字段名、报文 JSON 贴给用户。

## 提交后

- 返回 `code === '0000'` 表示已接收；
- 结果由页面 toast 反馈，AI 不必复述；
- 对用户只说「已提交 N 条报价」；失败则说「提交未成功，请稍后重试」。
