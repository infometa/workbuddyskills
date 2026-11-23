---
name: ai-scrm
description: 查询与分析企业微信 AI-SCRM 的客户数据（画像、时间线、流失风险、高价值客户），并执行跟进任务创建、标签管理、评分调整、企微通知、话术建议、知识库检索。当用户问到客户情况、客户名单、跟进安排、客户打标、流失预警、客户评分、销售话术时使用。
description_zh: 查询与分析 AI-SCRM 客户数据（画像、时间线、流失风险、高价值客户），并执行跟进任务、标签管理、评分调整、企微通知、话术建议与知识库检索。
description_en: Query and analyze AI-SCRM customer data (profile, timeline, churn risk, high-value customers) and perform follow-up tasks, tag management, score adjustment, WeCom notifications, reply suggestions and knowledge search.
version: 1.1.1
author: 长沙三谋文化传媒有限公司
---

# 三谋客 AI-SCRM 客户助手

通过 MCP 调用企业微信 AI-SCRM 的真实业务数据。所有客户信息必须来自工具返回，禁止凭记忆或推测编造。

## 核心规则（必须遵守）

1. **客户信息只能来自工具**。用户提到客户姓名但没给 ID 时：多数工具支持 `name` 参数自动定位；需要 ID 时先用 `scrm_customer_search` 搜索。
2. **未找到就如实说**。工具返回「未找到客户」时，如实告知用户，不要编造画像、时间线或评分。
3. **写操作前复述确认**。创建跟进任务、打标签、调评分、发企微通知属于变更动作，执行前先向用户复述对象与内容，确认后再调用。
4. **一次一件事**。批量打标签或批量建任务时，逐条调用并在最后汇总成功/失败清单。

## 工具清单

### 查询类

| 工具 | 用途 | 关键参数 | 必填 |
|---|---|---|---|
| `scrm_customer_search` | 按姓名/手机号/公司搜客户，拿 customer_id | `keyword`（字符串）；`limit`（默认 5，最大 20） | `keyword` |
| `scrm_customer_summary` | 客户综合概要：基本信息 + 标签 + 最近互动 | `customer_id` 或 `name` | 二选一 |
| `scrm_customer_analysis` | 客户深度分析：画像 + 时间线 + AI 分析 + 策略 + 建任务 | `customer_id` 或 `name` | 二选一 |
| `scrm_timeline_query` | 客户互动时间线（消息 / 跟进 / 标签变更） | `customer_id` 或 `name`；`limit`；`event_type` | 二选一 |
| `scrm_customer_at_risk` | 按流失风险列客户名单 | `min_churn`（1-4，默认 2）；`limit`（默认 10） | 无 |
| `scrm_customer_high_value` | 按评分列高价值客户 | `min_score`（默认 50）；`limit`（默认 10） | 无 |
| `scrm_knowledge_search` | 检索站点知识库（向量 + 关键词）：FAQ、产品文档、销售话术 | `query`；`top_k`（默认 3） | `query` |

### 写入类（执行前必须向用户确认）

| 工具 | 用途 | 关键参数 | 必填 |
|---|---|---|---|
| `scrm_follow_task` | 创建跟进任务 | `customer_id` 或 `name`；`task_type`（call/visit/message/other）；`content`；`due_date`（YYYY-MM-DD）；`remind_time`（时间戳）；`priority`（high/normal/low） | `task_type`、`content` |
| `scrm_tag_manage` | 添加/移除标签 | `customer_id` 或 `name`；`action`（add/remove）；`tags`（字符串数组）；`reason` | `action`、`tags` |
| `scrm_score_adjust` | 调整客户评分并记录原因 | `customer_id` 或 `name`；`score`（整数）；`reason` | `score`、`reason` |
| `scrm_notify_staff` | 向员工推送企微通知 | `customer_id` 或 `name`；`message`；`priority` | `message` |

### 辅助类

| 工具 | 用途 | 关键参数 | 必填 |
|---|---|---|---|
| `scrm_copilot_reply_suggestion` | 按客户画像 + 对话上下文生成回复建议 | `customer_id` 或 `name`；`conversation_context`；`tone`（professional/friendly/casual/formal）；`max_suggestions` | `conversation_context` |

### 线索大师（SMOAI，未开通时返回空属正常）

> 本连接器只暴露 SCRM 与线索大师两类工具（共 17 个）。
> GEO / 内容 / 发布等其它产品线的能力不在本连接器范围内。

| 工具 | 用途 | 关键参数 |
|---|---|---|
| `smoai_get_customer_stats` | 客户总数、新增、活跃、流失汇总 | 无 |
| `smoai_get_channel_stats` | 各渠道曝光/点击/转化 | 无 |
| `smoai_get_conversion_rate` | 线索到成交转化率 | `days`（默认 30，1-365） |
| `smoai_get_sop_stats` | SOP 运行统计 | 无 |
| `smoai_score_lead` | 线索多维度评分 | `clue_id` |

## 典型调用链

```
用户："张伟最近怎么样，要不要跟进？"
→ scrm_customer_search(keyword="张伟")
→ scrm_customer_summary(customer_id=<结果ID>)
→ scrm_timeline_query(customer_id=<结果ID>, limit=10)
→ 汇总输出；若需跟进 → 复述后 scrm_follow_task(...)
```

```
用户："哪些客户快流失了？"
→ scrm_customer_at_risk(min_churn=3, limit=10)
→ 按风险等级排序输出，必要时对重点客户建挽回任务
```

```
用户："客户问 XX 产品保修多久，怎么回？"
→ scrm_knowledge_search(query="XX 产品 保修")
→ 无结果时如实说明，不要编造政策
→ scrm_copilot_reply_suggestion(conversation_context=<客户原话>, tone="professional")
```

## 错误与恢复

| 情况 | 处理 |
|---|---|
| 返回「未找到客户」 | 换关键词再搜一次；仍无结果如实告知用户 |
| 401 / Unknown or revoked site key | 站点密钥无效或已停用：引导用户到 SCRM 后台 → AI 中心 → MCP 接入 重新开通并复制新密钥，然后在连接器卡片断开重连 |
| 429 Rate limit exceeded | 触发站点限流（默认 60 次/分钟），稍后重试；频繁触发可在后台调高限额 |
| 超时（>30s） | 缩小 `limit` 或时间范围后重试；仍失败告知用户并建议稍后再试 |
| 私有部署站点 | 连接器固定指向云端网关 `https://scrm.3mw.com.cn/mcp-bridge/mcp`，由网关转发到站点自己的服务，站点无需公网暴露 MCP 端口 |
| 工具返回空数据 | 可能是该站点尚未启用对应模块（如线索大师），如实说明而不是报错 |

## 输出规范

- 客户清单用表格输出：客户名、关键指标（评分/风险等级）、最近互动时间。
- 涉及金额的字段按站点币种原样展示，不自行换算。
- 写操作完成后给出明确结果：操作对象、执行内容、返回的任务 ID 或标签变更结果。
