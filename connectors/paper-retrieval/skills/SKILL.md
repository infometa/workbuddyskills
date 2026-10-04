---
name: "paper-retrieval"
description: "Repilot 科研智能体（对应 MCP 服务 paper-retrieval）：科研课题申报书与汇报 PPT 生成、快速学术文献检索、医学检测项目智能问答、文献综述报告生成，任务异步执行，支持状态轮询与取消。"
version: "2.0.1"
author: "Repilot"
---

# Repilot 科研智能体（paper-retrieval）

> 本 Skill 对应的 MCP 服务标识符为 `paper-retrieval`（见 mcp.json 的 `mcpServers.paper-retrieval`），对外产品名为「Repilot 科研智能体」。下文所有工具均通过该 MCP 服务调用。

本连接器提供科研辅助能力，所有任务均为**异步执行**，提交后立即返回任务ID，需通过状态查询获取最终结果。

---

## 状态与耗时汇总

| 工具名称 | 用途 | 预计耗时 | 初始状态 | 轮询状态 |
|---------|------|----------|---------|---------|
| `start_research_task` | 科研申报书 / PPT 生成 | 15–30 分钟 | `accepted` | `processing`, `completed`, `failed`, `cancelled` |
| `quick_search` | 快速文献检索 | 30~80 秒 | `accepted` | 同上 |
| `smart_assistant` | 医学智能问答 | 约 3 分钟 | `accepted` | 同上 |
| `start_detailed_report` | 详细综述报告生成 | 约 15 分钟 | `accepted` | 同上 |
| `get_task_status` | 查询任务状态 | 立即返回 | - | 同上，另可返回 `not_found` |
| `get_task_result` | 获取任务结果 | 立即返回 | - | 同上（`completed` 时返回结果） |
| `cancel_task` | 取消正在执行的任务 | 立即返回 | - | 同上 |

- **统一状态枚举**：`accepted`（已受理）、`processing`（执行中）、`completed`（完成）、`failed`（失败）、`cancelled`（已取消）、`not_found`（任务不存在）。
- **轮询建议**：
  - 短任务（quick_search）：每 30 秒查询一次，最多轮询 3 次。
  - 中任务（smart_assistant）：每 60 秒查询一次，最多轮询 4 次。
  - 长任务（start_detailed_report、start_research_task）：每 60 秒查询一次，分别最多轮询 20 次和 30 次。

---

## 可用工具

### 1. `start_research_task` - 课题申报 / 撰写 PPT
- **用途**：生成科研申报书、研究汇报 PPT、医学科普 PPT 等文档。
- **参数**：
  | 参数 | 类型 | 必填 | 说明 |
  |------|------|:----:|------|
  | `taskTitle` | string | ✅ | 用户需求描述，可包含具体方向、要求等 |
- **返回**：`{"taskId": "...", "status": "accepted"}`，随后轮询 `get_task_status`。

### 2. `quick_search` - 快速文献检索
- **用途**：快速检索学术文献，返回文献列表。
- **参数**：
  | 参数 | 类型 | 必填 | 说明 |
  |------|------|:----:|------|
  | `query` | string | ✅ | 检索关键词或问题 |
  | `sessionId` | string | - | 会话ID（可选） |
- **返回**：`{"taskId": "...", "status": "accepted"}`。

### 3. `smart_assistant` - 智能查询检测项目
- **用途**：回答医学检测项目、样本保存方法、疾病检查建议、标志物临界值等问题。
- **输出契约**：结果 JSON 中 `text` 与 `reasoning` 由服务端保证一致（不一致时以 `reasoning` 为准自动回填 `text`），可直接使用 `text` 字段作答。
- **参数**：
  | 参数 | 类型 | 必填 | 说明 |
  |------|------|:----:|------|
  | `content` | string | ✅ | 用户输入内容 |
  | `sessionId` | string | - | 会话ID（可选） |
- **返回**：`{"taskId": "...", "status": "accepted"}`。

### 4. `start_detailed_report` - 综述报告生成
- **用途**：根据课题生成详细的文献综述报告。
- **参数**：
  | 参数 | 类型 | 必填 | 说明 |
  |------|------|:----:|------|
  | `topic` | string | ✅ | 课题或研究方向 |
- **返回**：`{"taskId": "...", "status": "accepted"}`。

### 5. `get_task_status` - 查询任务状态
- **用途**：查询任意异步任务的当前状态。
- **参数**：`taskId` (string, 必填)
- **返回**：包含 `status` 字段的 JSON。

### 6. `get_task_result` - 获取任务结果
- **用途**：获取已完成任务的最终内容。
- **参数**：`taskId` (string, 必填)
- **返回**：若任务完成，返回 `result` 字段。

### 7. `cancel_task` - 取消任务
- **用途**：取消正在执行的任务。
- **参数**：`taskId` (string, 必填)

---

## 调用流程与约束

1. **提交任务**：调用对应的启动工具，传入用户需求。
2. **轮询状态**：按上述轮询建议定时调用 `get_task_status`，直到状态为 `completed`、`failed` 或 `cancelled`。
  - 若返回 `not_found`，检查任务ID是否正确。
  - 超时未完成可调用 `cancel_task` 取消。
3. **获取结果**：任务完成后调用 `get_task_result` 获取最终内容展示给用户。

## 重要限制

- **并发限制**：同一用户同时只能运行一个任务。若提交时返回 `"已有任务在运行，请稍后再试"`，请告知用户等待当前任务完成，不要重复提交。
- **异步特性**：所有工具调用都在几秒内返回，不会阻塞。请勿在单次请求中等待长时间结果。
- **认证**：使用 OAuth 2.0，Token 由 WorkBuddy 自动管理。
- **错误处理**：若 `failed`，读取 `error` 字段并向用户解释。
- **边界**：
  - 不支持同时运行多个任务。
  - 不支持实时流式输出。
  - 不支持修改已提交任务的参数（需取消后重新提交）。

## 示例对话

**用户**：帮我生成一份关于“AI 在医疗诊断中的应用”的科研申报书。  
**AI 动作**：调用 `start_research_task`，参数 `taskTitle: "AI 在医疗诊断中的应用"`。  
**AI 回复**：告知用户任务已启动，预计 15–30 分钟，并定期查询进度。

**用户**：查一下近两年关于基因编辑的文献。  
**AI 动作**：调用 `quick_search`，参数 `query: "基因编辑"`。  
**AI 回复**：告知用户约 30~80 秒后返回结果，随后调用 `get_task_result` 获取并展示列表。

**用户**（轮询时）：获取结果。  
**AI 动作**：调用 `get_task_result`，参数 `taskId: "def456"`。  
**返回**：文献列表。  
**AI 回复**：展示列表。