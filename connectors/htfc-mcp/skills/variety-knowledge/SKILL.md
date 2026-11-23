---
name: variety-knowledge
description: 查询期货品种知识库。当用户询问某品种的历史事件、相似行情案例、品种摘要或研究报告时使用。
---

# 品种知识库（variety-knowledge）

## 用途

按日期范围和品种检索事件、相似案例、摘要与报告。

## 参数

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| `start_date` | 是 | 起始日期，格式 `YYYY-MM-DD` |
| `end_date` | 是 | 结束日期，格式 `YYYY-MM-DD` |
| `action` | 否 | `events`（默认）、`similar`、`summary`、`report` |
| `variety_code` | 否 | 品种代码 |
| `new_evt_id` | 条件必填 | `action=similar` 时必填 |
| `pageNo` | 否 | 页码，默认 1 |
| `pageSize` | 否 | 每页条数 |
| `bull_bear` | 否 | 方向过滤：看多 / 看空 |
| `risk_level` | 否 | 风险等级过滤 |
| `chg_7d_min` | 否 | 7 日涨跌幅下限 |
| `chg_7d_max` | 否 | 7 日涨跌幅上限 |
| `evt_desc` | 否 | 事件描述关键字 |

## 返回

`content[0].text` 为 Python dict 字面量（单引号），不能按 JSON 解析。需要转对象时用 `ast.literal_eval`，否则原样交给模型。

## 调用示例

```json
{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"variety_knowledge","arguments":{"start_date":"2026-09-01","end_date":"2026-10-20","action":"events","variety_code":"rb"}}}
```

## Key 说明

用户在连接器配置里填写一次期赢通 API Key，客户端以 `X-API-KEY` 请求头发送，工具入参中不需要再携带 Key，也不要让用户在对话中提供 Key。

Key 相关错误：`missing_api_key`、`invalid_qiyingtong_api_key`、`qiyingtong_api_key_invalid`，处理方式同连接器配置检查。
