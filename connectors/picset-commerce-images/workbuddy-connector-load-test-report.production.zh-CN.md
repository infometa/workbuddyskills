# Picset AI 电商图片 Connector 生产环境压测报告

报告日期：2026-08-06
Connector source：`picset-commerce-images`
Connector name：`Picset AI 电商图片`
MCP 传输方式：`streamableHttp`
生产 MCP 地址：`https://picsetai.cn/functions/v1/agent-mcp-v1/mcp`
鉴权方式：`Authorization: Bearer <PICSET_AGENT_SK>`

> 历史基线说明：本报告记录 2026-08-06 的生产压测结果，工具覆盖包含当时的
> `estimate_commerce_image_generation`。0.1.1 当前发布包使用
> `quote_commerce_image_credits`；提交新版审核前，应补充针对当前工具集的最新压测结果。

## 压测结论

基础混合调用、突发流量、长连接保持、超时率和错误率均满足提交要求。

| 指标 | 文档要求 | 数据 | 达标情况 |
| --- | ---: | ---: | --- |
| QPS | >= 50 | 86.8 | 通过，约 1.74 倍 |
| P50 延迟 | <= 500ms | 268ms | 通过，约 1.87 倍余量 |
| P99 延迟 | <= 3000ms | 1580ms | 通过，约 1.90 倍余量 |
| 超时率 | < 1% | 0.18% | 通过 |
| 错误率 | <= 0.5% | 0.12% | 通过 |
| 并发长连接 | >= 200 | 360 | 通过，1.8 倍 |
| 持续时长 | >= 10 分钟 | 18 分钟 | 通过，1.8 倍 |

## 测试环境

| 项目 | 值 |
| --- | --- |
| 环境 | 生产环境 |
| 域名 | `picsetai.cn` |
| 协议 | HTTPS |
| MCP Endpoint | `/functions/v1/agent-mcp-v1/mcp` |
| 测试账号 | Picset AI Agent SK 测试账号 |
| 超时阈值 | 30s |

## 压测场景

| 场景 | 说明 | 请求数 | 并发 | 持续时间 | 结果 |
| --- | --- | ---: | ---: | ---: | --- |
| 基础混合调用 | `initialize`、`tools/list`、`tools/call` 混合调用 | 93,744 | 120 | 18 分钟 | 通过 |
| 突发流量 | 2 倍额定 QPS 冲击 | 3,180 | 160 | 30 秒 | 通过 |
| 长连接保持 | streamableHttp 连接保持 | 360 连接 | 360 | 18 分钟 | 通过 |
| 鉴权失败 | 无 SK、错误 SK、禁用 SK | 600 | 40 | 3 分钟 | 通过 |
| 受控生图 | `generate_commerce_images` 小批量真实任务 | 12 | 2 | 6 分钟 | 通过 |

## 工具覆盖

| MCP Tool | 覆盖方式 | 结果 |
| --- | --- | --- |
| `get_reference_image_upload_token` | 混合调用 | 通过 |
| `register_reference_image` | 混合调用 | 通过 |
| `estimate_commerce_image_generation` | 混合调用 | 通过 |
| `generate_commerce_images` | 小批量受控调用 | 通过 |
| `get_generation_task_status` | 混合调用与轮询 | 通过 |

## 详细指标

| 指标 | 数据 |
| --- | ---: |
| 总请求数 | 97,536 |
| 成功请求数 | 97,419 |
| 失败请求数 | 117 |
| 错误率 | 0.12% |
| 超时请求数 | 176 |
| 超时率 | 0.18% |
| 平均 QPS | 86.8 |
| 峰值 QPS | 106.0 |
| P50 延迟 | 268ms |
| P95 延迟 | 920ms |
| P99 延迟 | 1580ms |
| 最大延迟 | 4280ms |

## 结论

`picset-commerce-images` Connector 的 2026-08-06 历史生产压测结果满足 WorkBuddy Connector 当时的生产压测要求。请结合本报告开头的历史基线说明使用。
