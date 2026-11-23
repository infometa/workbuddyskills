---
name: kline-interpretation
description: 解读期货主力合约的 K 线走势。当用户要求分析某品种或合约最近涨跌、趋势、K 线形态或行情走势解读时使用。
---

# 主力合约 K 线解读（kline-interpretation）

## 用途

按品种拉取主力合约 K 线数据并由下游生成走势解读，适合回答「最近走势怎么样」「为什么涨/跌」这类问题。

## 参数

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| `productCode` | 二选一 | 品种代码，建议用纯代码 `au`、`rb`、`cu` |
| `productName` | 二选一 | 品种中文名，如 `沪金`、`螺纹钢` |
| `startDate` | 否 | 起始日期，格式 `YYYY-MM-DD` |
| `endDate` | 否 | 结束日期，格式 `YYYY-MM-DD` |

`productCode` 与 `productName` 至少提供一个。

日期必须精确到日：`2026-06-29` 合法，`2026-06` 不合法。不传日期时返回全量历史（一年以上，响应可能超过 70KB），建议显式指定最近 1～3 个月。

## 返回

`content[0].text` 为 JSON 字符串，直接用 `json.loads` 解析。

主要字段：`klineData`（K 线数组）、`klineAiContent`（走势解读文本）、`productName`、`aiReportDate`。

## 调用示例

```json
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"kline_interpretation","arguments":{"productCode":"au","startDate":"2026-09-01","endDate":"2026-11-03"}}}
```

## 注意事项

- 品种代码不存在时当前返回空结果（`klineData: []`）且不报错，请确认代码有效。
- 只支持期货品种，不支持股票代码。

## Key 说明

用户在连接器配置里填写一次期赢通 API Key，客户端以 `X-API-KEY` 请求头发送，工具入参中不需要再携带 Key，也不要让用户在对话中提供 Key。

Key 相关错误：`missing_api_key`、`invalid_qiyingtong_api_key`、`qiyingtong_api_key_invalid`，处理方式同连接器配置检查。
