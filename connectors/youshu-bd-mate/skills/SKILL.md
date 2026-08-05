---
name: "有数智客 · 对公(To B)营销助手"
description: "基于企业全维数据的对公营销智能助手，提供访前报告、营销话术、行业透视、关键人画像、金融产品匹配等展业闭环能力。所有报告生成工具为异步模式，需配合 get_report_run 轮询获取结果。"
description_zh: "基于企业全维数据的对公营销智能助手，提供访前报告、营销话术、行业透视、关键人画像、金融产品匹配等展业闭环能力。所有报告生成工具为异步模式，需配合 get_report_run 轮询获取结果。"
description_en: "An intelligent corporate marketing assistant powered by full-dimensional enterprise data, offering pre-visit reports, marketing scripts, industry analysis, key person profiling, and financial product matching. All report generation tools are asynchronous — always poll with get_report_run to retrieve results."
version: "1.0.0"
author: "YouShu Open Platform"
---

# 有数智客 · 对公(To B)营销助手

## 1. 认证与连接

### 1.1 获取凭证

前往有数开放平台 `https://open.yscredit.com/mcp/guide`，点击右上角头像获取 MCP Key，将 Key 填入连接器配置界面的输入框。

Key 仅存储在本机 `~/.workbuddy` 目录下，不会上传云端。

### 1.2 凭证过期与降级

- 若调用返回 **401 Unauthorized**，表示 MCP Key 已过期或无效。
- **降级提示**：提示用户重新前往有数开放平台获取新的 MCP Key，并在连接器配置中更新凭证。
- 避免在凭证失效时重复调用工具，以免触发限流。

---

## 2. 工具调用模式（重要）

**所有报告生成工具均为异步模式**，调用后立即返回一个 `run_id`（任务标识），不会直接返回报告内容。

调用流程：

```
1. 调用报告生成工具 → 立即返回 { run_id: "xxx" }
2. 使用 get_report_run(run_id="xxx") 轮询进度
   ├── status = "queued"  → 任务排队中，稍后重试
   ├── status = "running" → 报告生成中，稍后重试
   ├── status = "completed" → 报告完成，从返回值中提取报告内容
   └── status = "failed" → 生成失败，查看错误信息
```

**轮询建议**：每次轮询间隔 2–3 秒，最多轮询 30 次。若超过 30 次仍未完成，提示用户稍后重试。

---

## 3. 可用工具

### 3.1 通用参数说明

以下 6 个报告生成工具共享相同的参数结构：

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|:--:|------|
| `enterprise_name` | string | 是 | 目标企业全称 |
| `eid` | string | 否 | 企业 ID（如有可传，辅助精准匹配） |
| `idempotency_key` | string | 否 | 幂等键，避免重复提交同一请求 |
| `user_profile_context_text` | string | 否 | 用户画像上下文（已白名单化的短文本），用于个性化报告 |
| `force_refresh` | boolean | 否 | 是否强制刷新缓存，默认 `false` |

---

### 3.2 访前一页纸 — `pre_visit_briefing_agent_mcp`

**描述**：生成访前一页纸 Agent 报告。基于企业数据，在 ToB 销售/商务拜访目标客户前，根据用户行业视角为其生成一份浓缩的客户核心情报与行动指南。

**报告包含 5 个核心模块**：企业七问概览、客户痛点分析、关键人画像、拜访策略、风险警戒线。

**触发关键词**：访前一页纸、拜访准备、客户情报、销售拜访、客户画像一页纸、访前准备

**调用示例**：
```json
{
  "enterprise_name": "XX科技有限公司",
  "user_profile_context_text": "银行对公客户经理，主营企业贷款"
}
```

---

### 3.3 营销话术 — `corporate_marketing_agent_mcp`

**描述**：生成营销话术 Agent 报告。基于目标企业近期动态信号与自身行业可提供的产品能力，在 ToB 销售/商务拜访或电话触达目标客户前，为其生成一套分阶段、可照念、合规的营销话术。

**话术覆盖**：破冰 → 需求激发 → 产品介绍 → 异议处理 → 促成全流程，支持上门拜访与电话外呼两种场景。

**触发关键词**：营销话术、话术生成、拜访话术、销售话术、电话话术、话术准备、访前话术

**调用示例**：
```json
{
  "enterprise_name": "XX科技有限公司",
  "user_profile_context_text": "银行对公客户经理，主营企业贷款与现金管理"
}
```

---

### 3.4 访前客情报告 — `pre_visit_report_agent_mcp`

**描述**：生成访前客情报告 Agent 报告。从企业近期动态中捕捉合作信号，从财务与经营数据中判断合作潜力，从公开风险信息中排查合作隐患，最终形成一份可支撑 ToB 销售/商务决策的情报级报告。

**报告帮助销售完成从「知道」到「判断」的跨越**。

**触发关键词**：访前客情报告、访前报告、拜访报告、企业分析报告、营销报告、访前营销报告

**调用示例**：
```json
{
  "enterprise_name": "XX科技有限公司",
  "force_refresh": true
}
```

---

### 3.5 行业透视 — `enterprise_industry_analyst_agent_mcp`

**描述**：生成行业透视 Agent 报告。融合工商经营信息与联网搜索数据，按「锁定主业 → 剖析行业 → 评估影响」三步动线完成分析。精准识别企业主营业务与细分赛道，深度拆解行业周期、市场规模与竞争格局，评估宏观环境对企业的具体影响与风险。

**帮助销售快速建立行业认知**，让跨行业拜访也能谈出专业深度。

**触发关键词**：企业赛道、行业研判、行业信息、行业分析、行业透视

**调用示例**：
```json
{
  "enterprise_name": "XX科技有限公司"
}
```

---

### 3.6 产品匹配 — `financial_product_matching_agent_mcp`

**描述**：生成产品匹配 Agent 报告。根据企业行业属性、经营规模、商机信号、风险偏好等特征，由大模型推断潜在金融需求并匹配最合适的前 5 类对公金融产品（含企业主个人金融类交叉销售）。

**触发关键词**：访前产品推荐、营销切入点、企业金融产品匹配、企业金融需求推断、产品推荐

**调用示例**：
```json
{
  "enterprise_name": "XX科技有限公司",
  "user_profile_context_text": "银行对公客户经理，主营企业贷款、票据贴现、现金管理"
}
```

> **合规声明**：本连接器提供的金融产品匹配结果基于企业公开数据与产品准入规则的信息撮合，**不构成投资建议或产品推荐**。最终决策需由持牌金融从业人员结合客户实际需求与风险承受能力判断。

---

### 3.7 关键人（KP）画像 — `enterprise_personnel_profile_agent_mcp`

**描述**：生成关键人（KP）画像 Agent 报告。根据企业名称与企业关键人姓名，生成企业关键决策人（高管、股东等）的人员档案、拜访建议及触达路径，辅助对公客户经理了解目标企业决策人链路并制定沟通策略。

**报告范畴**：基本信息、教育背景、职业生涯、工作理念、个人特点、爱好等。

**触发关键词**：关键人画像、人员档案、高管信息、教育背景、职业生涯、个人特点、触达路径、KP 信息、决策人

**调用示例**：
```json
{
  "enterprise_name": "XX科技有限公司",
  "user_profile_context_text": "目标关键人：张三，职务：CEO"
}
```

> **注意**：关键人姓名需通过 `user_profile_context_text` 传递，目前没有独立的 `person_name` 参数。

---

### 3.8 报告进度查询 — `get_report_run`

**描述**：按 `run_id` 返回报告任务的最新进度快照。这是**异步报告生成流程的必要环节**，必须在上一步报告生成工具返回 `run_id` 后调用。

**参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|:--:|------|
| `run_id` | string | 是 | 报告生成工具返回的任务 ID |

**返回值中的 `status` 状态**：

| status | 含义 | 操作 |
|--------|------|------|
| `queued` | 任务排队中 | 等待 2–3 秒后重试 |
| `running` | 报告生成中 | 等待 2–3 秒后重试 |
| `completed` | 报告已完成 | 从返回值中提取报告内容并呈现给用户 |
| `failed` | 生成失败 | 检查错误信息，向用户说明失败原因 |

**调用示例**：
```json
{
  "run_id": "rpt_abc123"
}
```

---

## 4. 典型调用流程

### 4.1 场景一：访前报告生成

**用户意图**："帮我生成一份XXX公司的访前报告"

```
1. 调用 pre_visit_report_agent_mcp({ enterprise_name: "XXX公司" })
   → 获取 run_id
2. 循环调用 get_report_run({ run_id }) 轮询
   → 直到 status = "completed"
3. 从返回值提取报告 → 呈现给用户
4.（可选）若用户需要一页纸摘要：
   调用 pre_visit_briefing_agent_mcp({ enterprise_name: "XXX公司" })
   → 轮询 get_report_run → 呈现
```

### 4.2 场景二：拜访话术生成

**用户意图**："我要去拜访XXX公司，帮我生成一套营销话术"

```
1. 调用 corporate_marketing_agent_mcp({
     enterprise_name: "XXX公司",
     user_profile_context_text: "描述用户角色和产品"
   })
   → 获取 run_id
2. 循环调用 get_report_run({ run_id }) 轮询
   → 直到 status = "completed"
3. 提取话术内容 → 呈现给用户
```

### 4.3 场景三：企业基本情况查询

**用户意图**："查一下XX公司的基本情况"

```
1. 调用 pre_visit_report_agent_mcp({ enterprise_name: "XX公司" })
   → 获取 run_id
2. 轮询 get_report_run → 获取完整客情报告
3. 提取基本信息（企业概况、经营状况、风险信息）→ 呈现
4.（可选）若用户追问行业：调用 enterprise_industry_analyst_agent_mcp
```

### 4.4 场景四：股权结构查询

**用户意图**："查一下XXX公司的股权结构和实际控制人"

```
1. 调用 pre_visit_report_agent_mcp({ enterprise_name: "XXX公司" })
   → 获取 run_id
2. 轮询 get_report_run → 获取完整报告
3. 从报告中提取股权结构、实际控制人相关章节 → 呈现
```

### 4.5 场景五：金融产品匹配

**用户意图**："为XXX公司匹配适合的金融产品"

```
1. 调用 financial_product_matching_agent_mcp({
     enterprise_name: "XXX公司",
     user_profile_context_text: "描述用户可提供的产品方向"
   })
   → 获取 run_id
2. 轮询 get_report_run → 直到 status = "completed"
3. 提取产品推荐列表 → 呈现
4. 输出时附带合规声明：「本结果基于公开数据的信息撮合，不构成投资建议」
```

### 4.6 并行调用优化（高级）

当用户需要多份报告时，可先并行调用多个报告工具，再逐个轮询：

```
1. 并行调用：
   - pre_visit_report_agent_mcp({ enterprise_name: "XXX" })
   - corporate_marketing_agent_mcp({ enterprise_name: "XXX" })
   → 获取 run_id_1, run_id_2
2. 逐个轮询 get_report_run:
   - get_report_run({ run_id: run_id_1 }) → 报告 A
   - get_report_run({ run_id: run_id_2 }) → 报告 B
3. 合并呈现两份报告
```

---

## 5. 注意事项

### 5.1 异步模式是必须遵守的

**不要**假设报告生成工具会直接返回结果。每次调用后必须用 `get_report_run` 轮询，否则拿到的只是 `run_id`，用户看到的是空白/无意义内容。

### 5.2 轮询超时处理

轮询次数上限建议为 **30 次**（约 60–90 秒）。若超过该次数仍为 `queued` 或 `running`，停止轮询并告知用户"报告生成耗时较长，请稍后重试"。

### 5.3 数据范围限制

- 数据来源于有数开放平台已接入的公开企业数据、工商信息、财务公告、知识产权、司法风险等。
- 部分非上市企业或小微企业可能存在数据覆盖不完整的情况。
- 报告中如出现"数据缺失"或"暂无公开信息"，应向用户说明。

### 5.4 限流策略

- 有数 MCP Server 对单 Key 设有 QPS 限制，建议报告工具调用间隔不低于 3 秒。
- 若触发限流（返回 429），应等待 3 秒后重试，最多重试 3 次。

### 5.5 错误码说明

| HTTP 状态码 | 含义 | 处理建议 |
|------------|------|---------|
| 200 | 成功 | — |
| 400 | 请求参数错误 | 检查 `enterprise_name` 是否拼写正确 |
| 401 | 凭证无效或过期 | 提示用户更新 MCP Key |
| 429 | 请求过于频繁 | 等待后重试，降低调用频率 |
| 500 | 服务端内部错误 | 稍后重试 |
| 503 | 服务暂时不可用 | 稍后重试 |

### 5.6 金融合规声明

本连接器提供的金融产品匹配结果基于企业公开数据与产品准入规则的信息撮合，**不构成投资建议或产品推荐**。最终决策需由持牌金融从业人员结合客户实际需求与风险承受能力判断。模型输出内容仅供参考，不替代专业金融顾问意见。

### 5.7 用户画像传递

- `user_profile_context_text` 用于个性化报告生成，应填入用户角色（如"银行对公客户经理"）、主营产品（如"企业贷款"）、拜访目标等**已白名单化的短文本**。
- 不要在 `user_profile_context_text` 中传递客户敏感信息或长文本。
- 若不需要个性化，可省略此参数。
