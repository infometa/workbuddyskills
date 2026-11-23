---
name: exchange-announcement
description: 查询期货交易所公告与相关资讯。当用户询问上期所、大商所、郑商所、中金所等交易所的公告、通知、规则调整或近期资讯时使用。
---

# 交易所公告（exchange-announcement）

## 用途

查询指定日期范围内各期货交易所发布的公告与相关资讯，可按交易所过滤并分页返回。

## 参数

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| `start_date` | 是 | 起始日期，格式 `YYYY-MM-DD` |
| `end_date` | 是 | 结束日期，格式 `YYYY-MM-DD` |
| `exch_cd` | 否 | 交易所代码，不传则查询全部交易所 |
| `pageNo` | 否 | 页码，默认 1 |
| `pageSize` | 否 | 每页条数 |

## 返回

`content[0].text` 为 Python dict 字面量（单引号），不能按 JSON 解析。需要转对象时用 `ast.literal_eval`，否则原样交给模型。

## 调用示例

```json
{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"exchange_announcement","arguments":{"start_date":"2026-09-20","end_date":"2026-10-20","pageNo":1,"pageSize":10}}}
```

## Key 说明

用户在连接器配置里填写一次期赢通 API Key，客户端以 `X-API-KEY` 请求头发送，工具入参中不需要再携带 Key，也不要让用户在对话中提供 Key。

Key 相关错误：`missing_api_key`（未配置或未携带请求头）、`invalid_qiyingtong_api_key`（格式不合法，长度 8~512，仅可打印 ASCII）、`qiyingtong_api_key_invalid`（Key 无效或过期）。
