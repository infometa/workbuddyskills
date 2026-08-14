# Agent 模板库

> Plugin 阶段二「建议」时按 `appType` 匹配模板，生成 1 Agent + N Skills 的推荐组合。
> 数仓问数（基于 SQL MCP）不在此内置，由 DW 能力模块动态生成。

---

## 一、模板匹配表

| appType | 推荐模板（默认勾选粗体） |
| --- | --- |
| `static` | **app-guide** + page-monitor |
| `api-readonly` | **app-guide** + api-tester + page-monitor |
| `crud` | **app-guide** + data-manager + smart-search + change-notifier |
| `dashboard` | **app-guide** + overview-report + anomaly-monitor + page-monitor |

---

## 二、模板目录规范

每个模板以标准文件夹形式生成到 `.agent/skills/{name}/`，遵循 DeepAgents skill 目录规范：

```
.agent/skills/{name}/
├── SKILL.md              # 必须：YAML frontmatter (name + description) + 指令
├── references/           # 可选：参考文档（LLM 按需读取）
├── scripts/              # 可选：脚本
└── assets/               # 可选：模板/资源
```

- **单文件模板**：目录内仅有 `SKILL.md`（简单 skill 无需拆分）
- **多文件模板**：`SKILL.md` + 支撑文件（模板中标注目录结构与各文件内容）

---

## 三、基础设施模板

> 与数据无关的通用能力，所有 appType 均可使用。

### 模板 1：app-guide — 应用导览助手 🌐

> **适用**：所有 appType。回答"这个应用是干什么的、能做什么、怎么用"。
> 是最基础的模板，建议每个 Agent 都包含一个。

```markdown
---
name: app-guide
description: >-
  Answer questions about what this application does, what data it has,
  and how to use it. Use as the entry-point skill when users first interact
  with the agent or ask "what can you do".
---

# 应用导览

## 触发
- 用户首次对话、问"你能做什么"、"这个系统是干嘛的"、"有什么数据"
- 任何超出其他 skill 范围的开放性问题

## 流程
1. 调用 `list_endpoints` 工具，了解本应用所有 API
2. 用自然语言总结应用功能，列出 3~5 个最有价值的能力
3. 询问用户需要哪种帮助，引导到合适的 skill

## 约束
- 不要把 list_endpoints 的原始 JSON 抛给用户，要用自然语言总结
- 如果某些功能可能涉及敏感数据，主动提醒
```

---

### 模板 2：page-monitor — 页面监控 🔧

> **适用**：所有 web 应用。检查应用本身是否健康。

```markdown
---
name: page-monitor
description: >-
  Monitor application availability via check_app_health. Reports up/down
  status, response time. Use when users ask "is the app running" or
  set up uptime monitoring.
---

# 页面监控

## 触发
- 用户问"应用是否正常"、"页面挂了吗"
- 定时健康检查

## 流程
1. 调用 `check_app_health` 工具
2. 解读返回：
   - status: healthy → "✅ 应用运行正常"
   - status: degraded → "⚠️ 应用响应异常，状态码 {code}"
   - status: unhealthy → "🚨 应用不可达"
3. 异常时调用 `send_wework` 告警（如启用）

## 默认监控规则
- 检查间隔：每 5 分钟
- 连续 2 次失败 → 告警
- 响应时间 > 5s → 性能告警

## 约束
- 单次失败不立即告警（避免抖动）
- 告警后恢复时也要发"已恢复"通知
```

---

### 模板 3：api-tester — API 探针 🧪

> **适用**：`api-readonly` / `crud`。自动测试用户应用的 API。

```markdown
---
name: api-tester
description: >-
  Smoke-test the application's APIs. Calls each endpoint with sample
  inputs, reports success/failure with response time. Use for CI-style
  health checks or before-release validation.
---

# API 探针

## 触发
- 用户说"测试一下 API"、"接口都正常吗"
- 定时探测

## 流程
1. 调用 `list_endpoints` 获取所有端点
2. 对每个 GET 端点，用最小参数集调用
3. 收集 status / 响应时间 / payload 摘要
4. 输出表格汇总：✅ / ⚠️ / ❌

## 约束
- 不主动测试 POST/PUT/DELETE（会改数据）
- 单接口超时 5s 标记为 ⚠️
- 报告里包含 curl 命令方便用户复现
```

---

### 模板 4：scheduled-task — 定时任务管家 📅（多文件）

> **适用**：所有 appType。让用户用自然语言管理定时任务（实际由 agent-server 调度）。

**目录结构：**

```
scheduled-task/
├── SKILL.md
└── references/
    └── cron-mapping.md    # 时间表达式映射规则
```

**SKILL.md：**

```markdown
---
name: scheduled-task
description: >-
  Manage scheduled tasks via natural language. Creates / lists / pauses /
  resumes / deletes scheduled jobs by calling the scheduler tools.
  Use when users say "schedule / 每 X 时 / 定时 / cron".
---

# 定时任务管家

## 触发
- "每周一上午 9 点生成周报"
- "停掉那个监控任务"
- "看看有哪些定时任务"

## 流程
1. 解析时间表达式 → 参考 `references/cron-mapping.md` 转成 interval_minutes
2. 调用相应工具：
   - 创建 → `create_scheduled_task`
   - 列表 → `list_scheduled_tasks`
   - 暂停/恢复 → `pause_scheduled_task` / `resume_scheduled_task`
   - 删除 → `delete_scheduled_task`
   - 立即执行 → `trigger_scheduled_task`
3. 把 task 描述写得**像给另一个 LLM 的 prompt**（因为到时候就是这样调用的）

## 命名规范
- 短横线 kebab-case，全英文
- 例：weekly-report / daily-health-check / monthly-anomaly-scan

## 约束
- 创建前先 list 一次，避免重名
- 间隔 < 5 分钟 → 提醒用户合理性
- description 要包含明确的"做什么"+"如果失败怎么办"
```

**references/cron-mapping.md：**

```markdown
# 时间表达式映射规则

将自然语言时间表达式转换为 interval_minutes（分钟）：

| 自然语言 | interval_minutes |
| --- | --- |
| 每小时 | 60 |
| 每天 | 1440 |
| 每周 | 10080 |
| 每月 | 43200 |

## 复合表达式

| 表达式 | 计算 | interval_minutes |
| --- | --- | --- |
| 每 2 小时 | 2 × 60 | 120 |
| 每 30 分钟 | 30 | 30 |
| 每周一 9 点 | 7 × 1440 | 10080（用 description 标注具体时间） |
| 每月 1 号 | 30 × 1440 | 43200（用 description 标注具体日期） |

## 注意事项
- interval_minutes 是 agent-server 调度器的实际执行间隔
- 具体时间点（如"周一 9 点"）通过 description 字段传递，调度器到点后触发 agent
- 不支持秒级粒度，最小间隔 5 分钟
```

---

## 四、应用数据模板

> 通过 `call_api` 访问应用自有数据（MongoDB / MySQL / SQLite 等），不涉及数仓 SQL。
> 数仓问数（基于 SQL MCP）由 DW 能力模块独立生成，不在此内置。

### 模板 5：data-manager — 数据管理 ✏️

> **适用**：`crud`。增删改查 + 批量操作，通过应用 API 访问自有数据。

```markdown
---
name: data-manager
description: >-
  Create / update / delete records via natural language. Routes to
  list_items / get_item / create_item / update_item / delete_item.
  Always confirms with the user before destructive operations.
---

# 数据管理

## 触发
- "添加一条..."、"把 X 改成 Y"、"删除..."、"批量..."

## 流程
1. 解析操作意图：增 / 改 / 删 / 批量
2. **写操作前必须用户确认**：展示将执行的动作摘要 + 影响行数
3. 调用对应工具
4. 回报结果（成功数 / 失败数 / 失败原因）

## 安全约束
- 删除操作**永远**先 list 一次确认范围，再执行
- 批量更新前先 sample 3 条展示变更预览
- 单次批量操作影响 > 100 行 → 二次确认
- 失败时不要假装成功，如实告知错误
```

---

### 模板 6：smart-search — 智能搜索 🔍

> **适用**：`crud` / `dashboard`。把模糊自然语言变成结构化搜索，通过应用 API 查询。

```markdown
---
name: smart-search
description: >-
  Search application data with fuzzy natural language. Extracts filters
  from the question, calls list_items / call_api, and returns relevant results.
  Use when users say "find / search / look up / filter".
---

# 智能搜索

## 触发
- "找一下..."、"搜索..."、"哪些 X 满足..."

## 流程
1. 从问题中提取过滤条件（字段、值、范围）
2. 选择最匹配的 list/search 工具（参考 list_endpoints）
3. 调用并按相关性返回结果（默认前 20 条）
4. 结果太多 → 摘要 + 提示用户加条件

## 约束
- 不要返回原始 JSON，要格式化成表格或要点
- 检索关键字段（id, name 等）保留
```

---

### 模板 7：overview-report — 概览报表 📈（多文件）

> **适用**：`dashboard` / `api-readonly`。生成周报/月报，通过应用 API 拉取数据。

**目录结构：**

```
overview-report/
├── SKILL.md
└── assets/
    └── report-template.md    # 报告骨架模板
```

**SKILL.md：**

```markdown
---
name: overview-report
description: >-
  Generate periodic overview reports (weekly / monthly / custom). Pulls
  metrics via call_api, computes trends, formats as Markdown.
  Use when users say "report / summary / 周报 / 月报".
---

# 概览报表

## 触发
- "生成周报 / 月报"
- 定时任务到点（agent-server 调度器触发）

## 流程
1. 确认时间范围与指标
2. 调用相关 API 拉数据
3. 计算同比/环比（如有历史数据）
4. 读取 `assets/report-template.md` 作为报告骨架，填充数据生成 Markdown 报告
5. 如启用企微 → 调用 `send_wework` 推送

## 约束
- 不编数据，所有数字都来自工具返回
- 没数据的字段标注 N/A 而不是猜
```

**assets/report-template.md：**

```markdown
# {项目名} 概览报告 — {时间范围}

## 📊 关键指标
| 指标 | 数值 | 环比 |
| --- | --- | --- |
...

## 📈 主要分布
...

## 💡 洞察
- ...
```

---

### 模板 8：anomaly-monitor — 异常监控 🚨（多文件）

> **适用**：所有有数据的 appType。指标越界告警，通过应用 API 拉取数据。

**目录结构：**

```
anomaly-monitor/
├── SKILL.md
└── assets/
    └── alert-template.md    # 告警卡片模板
```

**SKILL.md：**

```markdown
---
name: anomaly-monitor
description: >-
  Monitor key metrics and alert on anomalies. Pulls data via call_api,
  compares against thresholds, sends notifications via send_wework.
  Use when users want to set up alerts or monitoring rules.
---

# 异常监控

## 触发
- 用户配置告警规则（指标 / 阈值 / 接收人）
- 定时任务到点检查

## 流程
1. 确认监控指标和阈值
2. 调用对应 API 拉最新数据
3. 对比阈值：
   - 正常 → 静默（除非用户要求每次都汇报）
   - 异常 → 读取 `assets/alert-template.md` 填充告警卡片，调用 `send_wework` 推送
4. 异常时生成告警卡片（含数据 / 趋势 / 建议）

## 防告警风暴
- 同一指标 1 小时内只告警 1 次
- 连续 3 次正常后才能再次告警
```

**assets/alert-template.md：**

```
⚠️ 【{项目名}】指标异常

- 指标：{metric}
- 当前值：{value}（阈值：{threshold}）
- 趋势：{trend}
- 建议：{suggestion}
```

---

### 模板 9：change-notifier — 变更通知 🔔

> **适用**：`crud`。监听数据变化并通知，通过应用 API 拉取记录对比。

```markdown
---
name: change-notifier
description: >-
  Notify when business data changes. Periodically diffs key records,
  pushes notifications via send_wework. Use when users want to track
  changes or receive update alerts.
---

# 变更通知

## 触发
- 用户配置监听规则
- 定时任务到点检查变更

## 流程
1. 拉取关注的资源列表（用 list_items 或 call_api）
2. 与上次快照对比（quick & dirty: 把上次结果存到对话上下文）
3. 列出变更：新增 / 更新 / 删除
4. 调用 `send_wework` 推送

## 消息模板
\`\`\`text
[{project}] 数据变更
- ➕ 新增 {n1} 条
- ✏️ 更新 {n2} 条（{字段} 由 {旧值} → {新值}）
- ❌ 删除 {n3} 条
\`\`\`
```

---

## 五、自定义 Agent（用户完全自定义）

如果用户在阶段二选择「编辑」并要求完全自定义，逐项询问：

1. Agent 名称（kebab-case）
2. Agent 角色（一句话描述）
3. 包含哪些 Skill：从模板库选 + 完全自定义

每个 Skill 都按通用模板的 YAML frontmatter 格式生成。

---

## 六、自定义 Skill 模板

当用户描述一个模板库中没有的新 Skill 需求时，按以下模板生成：

### 单文件 Skill（简单场景）

适用于逻辑简单、无外部模板或参考文档的 skill，目录内仅有 `SKILL.md`：

```
.agent/skills/{name}/
└── SKILL.md
```

- 确保 `name` 使用 kebab-case，不与已有 skill 重名
- `description` 用英文一句话描述，供 LLM 匹配触发条件
- body 必须包含「触发」「流程」「约束」三部分

```markdown
---
name: <skill-name>
description: >-
  <English one-liner describing what this skill does and when to trigger it>
---

# <中文技能名>

## 触发
- <用户可能说的话、问的问题>
- <触发此 skill 的典型场景>

## 流程
1. <步骤 1：调用什么工具、获取什么数据>
2. <步骤 2：如何处理数据、生成什么>
3. <步骤 3：如何呈现结果、是否推送>

## 约束
- <安全或行为约束>
- <数据不出界、需要确认的操作等>
```

### 多文件 Skill（复杂场景）

当 skill 需要模板文件、参考文档、脚本等支撑资源时，使用标准多文件结构：

```
.agent/skills/{name}/
├── SKILL.md              # 必须：frontmatter + 指令
├── references/           # 参考文档（LLM 按需读取）
│   └── <ref-name>.md
├── scripts/              # 脚本（需执行的逻辑）
│   └── <script-name>.py
└── assets/               # 模板/资源（供引用的静态内容）
    └── <template-name>.md
```

**拆分原则：**
- `SKILL.md`：触发条件、流程概要、约束（始终是入口）
- `assets/`：固定的模板骨架（如报告格式、告警卡片），SKILL.md 中用"读取 `assets/xxx`"引用
- `references/`：规则文档（如映射表、配置说明），SKILL.md 中用"参考 `references/xxx`"引用
- `scripts/`：需执行的脚本（如数据处理、格式转换）

**生成规则：**
1. 根据用户描述的功能需求，推断出合理的工具调用链（list_endpoints → call_api → 项目工具）
2. 如果有对应的 MCP 项目工具，优先在流程中引用
3. 涉及写操作的 Skill 必须包含"用户确认"约束
4. 涉及敏感数据的 Skill 必须包含"脱敏"约束
5. 如果功能需要定时执行，在流程末尾提示"可通过 scheduled-task 设置为定时任务"
6. **数据源约束**：自定义 Skill 涉及数据查询时，数据应来自用户应用的 API（由 mcp_bridge.py 中的 `call_api` 包装），绝不将业务数据 hardcode 到 Skill 文件或 mcp_bridge.py 中。如果用户应用当前缺少对应的 API 端点，在生成 Skill 的同时提示用户需要新增端点
7. **多文件拆分时机**：当 SKILL.md 超过 ~100 行、含固定模板骨架、含映射规则表、含可复用脚本时，拆分到 `assets/`/`references/`/`scripts/`
