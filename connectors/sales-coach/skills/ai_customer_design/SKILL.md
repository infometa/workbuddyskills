---
name: ai_customer_design
description: 创建和修改公司培训课程、上传课程资料、查询课程并生成练习链接。触发关键词：建课、AI 客户课程、AI 设计师对话、改课、查询培训课程、生成练习链接。
metadata:
  description_zh: 创建和修改公司培训课程，上传资料并生成练习入口。
  description_en: Create and edit company training courses and generate practice links.
---

# 公司培训课程技能（ai_customer_design）

通过 MCP 协议连接企业培训服务器，执行建课、改课、查询等操作。

## 工具调用方式

业务工具（`training.*`、`organization.*`）通过 agent 的**宿主原生 MCP 工具**直接调用。

**唯一例外**：文档上传（`upload_document.py`）必须通过脚本——agent 无法处理本地文件的 base64 编码。

### 连接降级规则

建课前先执行一次 ToolSearch，查 `training.*` 工具：
- ✅ 查到 → 连接正常，直接建课
- ❌ 查不到 → **立即调用 `coach-mcp-connect` 技能修复连接**（标准链路：`mcp_diagnose.py auth` → 复制 Authorization header 值 → 配置 MCP client → 宿主 Trust/重连 → 走原生 MCP），禁止换名重试

> ⚠️ **硬规则**：ToolSearch 只执行一次。禁止"换个名字再搜一次"——这不是排查手段，是浪费调用。
> 修复成功后重新 ToolSearch 验证，然后继续建课。

> **临时降级**：修复后宿主仍未注册工具但建课紧急时，可临时通过脚本直连完成当次业务（`call_tool()`），但**必须向用户声明当前使用的是脚本降级通道，非原生 MCP**。修复完成后禁止继续用脚本跑业务。

## AI 客户异步工具集（RFC-0014）

> `training.ai_customer.{create, update, update_status, get}`——对标闪卡 `training.flashcard.*` 命名。
> submit 秒返 → 无 120s 网关超时；独立 task store → 无会话保护锁死；非流式 → 无平台流式缺陷。

### 工具清单

| 工具 | 用途 | 关键参数 |
|------|------|---------|
| `training.ai_customer.create` | 创建课程（权限分叉：管理员返回 editUrl/manageUrl，学员返回 courseId） | `{}` |

> **注意**：create 返回的 `courseName` 是占位默认名（如"用户的AI客户_1234"），内容生成完成后会被 agent 按简报自动重命名，属预期行为。若在两轮之间查询看到默认名，不要误以为改名失败。
| `training.ai_customer.update` | 异步对话（返回 taskId，后台生成分钟级完成） | `{"courseId":123,"message":"..."}` |
| `training.ai_customer.update_status` | 轮询任务状态（每 5s 一次直到 done/failed） | `{"courseId":123,"taskId":"uuid"}` |
| `training.ai_customer.get` | 读取课程完整配置（需编辑权限） | `{"courseId":123}` |

### 调用模式

```
ai_customer.update({"courseId":123, "message":"创建药品销售课程"})
→ 秒返 {"taskId":"xxx", "conversationId":"yyy", "messageSha256":"abc...", "status":"running", "pollIntervalSeconds":5}

ai_customer.update_status({"courseId":123, "taskId":"xxx"})
→ 轮询直到 {"status":"done", "response":"...", "errorCode":0} 或 {"status":"failed", "errorCode":50002, "errorMessage":"..."}
→ done 时还可能返回 {"seriesCourseId":8001, "learnUrl":"https://..."}（学员路径自动创建系列课）

ai_customer.get({"courseId":123})
→ 返回课程完整配置（验证内容是否就绪）
```

> **约定**：业务数据在 `result.structuredContent` **顶层**（无 `.data` 信封）；snake_case 后端字段经 camelCaseKeys 自动转 camelCase。

### 错误码（in-band）

HTTP 200 + `code=20000` 为业务成功，`code≠20000` 为业务失败。错误信息在 `msg` 字段。

| 码 | 含义 | 处理 |
|---|------|------|
| 40001 | 参数无效 | 检查参数（message≤8000字符、metadata键≤20） |
| 42901 | 配额超限 | 积分配额耗尽，等待或联系管理员 |
| 42902 | 频率超限（10次/分钟）或在飞任务超限（≤3个） | 等待后重试 |
| 43501 | 课程不存在 | 核对 courseId |
| 43502 | 无编辑权限 | 核对权限 |
| 43503 | 课程正在生成中（10分钟生成锁） | 等待当前任务完成 |
| 43504 | 任务不存在 / 已过期（TTL 2小时）/ 不属于当前用户 | 重新 submit |
| 43505 | fileIds 无效 | 检查文件 |
| 50002 | agent 调用失败 | 等待 ≥60s → **用同义改写的消息**重试 1 次（服务端按 messageSha256 去重，原文重发会被判重复提交；例如原文"请开始建课"改写为"计划没问题，请开始生成课程内容"）→ 仍失败则报告并附 taskId/conversationId |
| 50003 | 会话创建失败 | 等 60s 重试（冷却期） |
| 50000 | 内部错误 | 报告运维 |

## 建课工作流

```
Step 1: training.ai_customer.create({}) → courseId
  → 管理员返回 {courseId, editUrl, manageUrl}
  → 学员返回 {courseId}（系列课延迟到内容生成后自动创建）

Step 2: training.ai_customer.update({"courseId":<id>, "message":"<课程简报>"})
  → 秒返 {"taskId":"xxx", "conversationId":"yyy", "messageSha256":"...", "status":"running", "pollIntervalSeconds":5}
  → 告知用户"建课请求已提交，预计 3-6 分钟完成"

Step 3: training.ai_customer.update_status({"courseId":<id>, "taskId":"xxx"}) 轮询
  → 每 5 秒调用一次
  → status="done" → Step 4
  → status="failed" → 读 errorMessage，决定重试或报告
  → 43504（任务过期）→ 重新 Step 2
  → ⚠️ 轮询期间全程静默，禁止询问用户"还在吗"

Step 4: training.ai_customer.get({"courseId":<id>}) → 验证课程内容
  → 检查 status="create_status_created" 且 stages.length > 0
  → ✅ 建课完成 → Step 5
  → ⚠️ 内容未就绪 → 等 30s 再查（agent 可能仍在写入），轮询最长 10 分钟

Step 5: training.task.create_open_project({"courseId":<id>}) → 拿到 link → 渲染二维码
```

**多轮对话**：Step 2-3 可重复调用。agent 可能先提问/出计划，需用户确认后再调 update 发送确认消息。

> ⚠️ **实测经验**：首次 `update` 几乎必然返回计划卡片（plan card）要求确认，`update_status` 秒返 `done` 但课程并未真正创建。必须发送第二轮 `update`（如"确认，请直接建课。"或"确认，开始生成。"）才触发实际内容生成。这是**预期行为**，不是错误。
>
> **时间差异**：第一轮 update 秒返 done（<5s），第二轮 update 触发内容生成（3-8 分钟）。改课同理（实际修改约 3-5 分钟）。不要因第一轮秒返就认为建课完成。
>
> **轮询间隔建议**：第二轮 update 后的前 2 分钟用 5s 间隔快速检查，之后可放宽到 10-15s 减少请求量。

**计划卡片判定规则**：`update_status` 返回 `status=done` 且 `ai_customer.get` 显示 `stages` 为空 → 视为计划卡片待确认 → 发送确认消息（如"确认，请直接建课"）。

> **偶发：二次计划卡片**：极少数情况下，第二轮确认消息返回的仍是计划卡片（`stages` 依然为空）。此时发送更强指令，如"计划确认无误，请立即执行建课操作，无需再确认"，即可触发实际内容生成。

**文件上传建课**：Step 2 通过 `metadata.fileIds` 传递文档。先用 `upload_document.py` 脚本上传（见「文档上传」章节）→ 拿到 fileId → 轮询至解析完成 → 携带 fileIds 调 `ai_customer.update`。

### 并发与容量约束

| 约束 | 限制 | 说明 |
|------|------|------|
| 提交频率 | 10 次/分钟/用户 | 超出返回 `42902` |
| 在飞任务 | ≤3 个/用户 | 超出返回 `42902` |
| 生成锁 | 10 分钟/课程 | 同课程同时只能有一个生成任务，超出返回 `43503` |
| message 长度 | ≤8000 Unicode 字符 | 超出返回 `40001` |
| metadata 键数 | ≤20 | 超出返回 `40001`（含 fileIds 算 1 个键） |
| 任务记录 TTL | 2 小时 | 过期后查询 status 返回 `43504` |
| running 超时 | 11 分钟 | 自动标记 failed（errorCode=50002） |

**批量建课**：串行执行，避免超过并发限制。

### 建课完成的判断标准

**唯一可靠判定**：`training.ai_customer.get` 返回的 config 中 `status="create_status_created"` 且 `stages.length > 0`。

**不要依赖**：
- ❌ `update` 的 response 文字（AI 回复可能说"建课完成"但实际未完成）
- ❌ `update_status` 的 status="done"（只表示本轮对话结束，不等于课程已创建）

**原则：只信 `ai_customer.get` 的字段值。**

### 课程简报（Agent 内部检查清单）

建课前，Agent 必须能用一句话说清"这门课为什么对练习者有价值"——说不清则信息不足，需追问用户。课程简报 6 要素（场景/角色/评估/流程/知识/资料）详见 [course-workflows.md](references/course-workflows.md)。

> **参考资料**：用户已提供原始文档文件时强制走文档上传路径（见「文档上传」章节）。

## 改课工作流

```
Step 1: training.ai_customer.get({"courseId":<id>}) → 记录当前各字段的实际值（基线）

Step 2: training.ai_customer.update({"courseId":<id>, "message":"<修改诉求>"})
  → 秒返 {"taskId":"xxx", "status":"running"}
  → ⚠️ 建课后改课需等待 ~60s 冷却期，遇到 50003 等 60s 后重试，最多 3 次

Step 3: training.ai_customer.update_status({"courseId":<id>, "taskId":"xxx"}) 轮询
  → 每 5 秒一次，直到 status="done" 或 "failed"

Step 4: training.ai_customer.get({"courseId":<id>}) → 验证修改是否真的生效
  → ⚠️ AI 回复具有误导性！验证原则见「建课完成的判断标准」
  → 首轮验证失败先等 30s 再查一次
  → 验证通过 → Step 5
  → 验证失败 → 重试 Step 2-3，最多 3 次，仍无变化 → 告知用户

Step 5: training.task.create_open_project({"courseId":<id>}) → 生成新链接 → 渲染二维码
```

**注意**：AI 助手能改角色、阶段、评分等，不能改 roundLimit/timeLimit 等运行参数。

## 文档上传

**禁止**直接调用 MCP 工具 `training.file.upload_document`。Agent 没有文件 I/O 能力，无法生成 base64。

**必须**使用脚本上传：

```bash
python3 skills/ai_customer_design/scripts/upload_document.py /path/to/doc.pdf
```

脚本返回 `{"fileId": 7667, "fileName": "doc.pdf", "status": "ready", ...}`。上传成功后，在建课对话中通过 `metadata.fileIds: [fileId]` 传递。

> 脚本报错时先使用 coach-mcp-connect 技能重新连接。完整错误处理与状态说明见 [file-upload.md](references/file-upload.md)。

### 强制决策规则

当用户提供了**原始文档文件**（PDF/Word/PPT/Excel/图片等附件），**必须**走文档上传路径：
- ✅ 调用 `upload_document.py` 脚本上传 → 拿到 fileId → 在 `ai_customer.update` 中通过 `metadata.fileIds` 传递
- ❌ 禁止把文档内容提取为纯文字后只通过 `message` 传入（**例外**：当服务端 Office 解析失败且 pandoc 转换后 < 8000 字符时，参考 file-upload.md）

**判断逻辑**（按顺序命中即停）：
1. 用户已提供原始文档文件 → 强制走文档上传
2. 无原始文档但参考资料 >1000 字或含表格/图表 → 建议文档上传
3. 仅简短场景描述（<1000 字）→ 直接用对话文本

**fileIds 规则**：正整数数组，≤20 个，不可重复。仅在携带课程简报的那次 update 传入即可，后续确认轮无需重复。

## 二维码 + 链接展示（必须执行，缺一不可）

拿到练习链接后，**必须同时完成两件事**：

### ① 渲染并展示二维码**图片**

> ⚠️ **关键要求**：二维码必须是**图片**（PNG），不能是纯文本、ASCII 艺术或 Unicode 字符。必须使用 agent 最适合展示图片的方式呈现给用户（如用 Read 工具读取图片文件让其在对话中直接可见）。

```bash
# 技能包内的路径（相对于技能包根目录）
python3 skills/ai_customer_design/scripts/render_qr.py '<练习链接>'

# 多门课程时指定不同输出文件名，避免覆盖
python3 skills/ai_customer_design/scripts/render_qr.py '<练习链接>' --out course1.png
python3 skills/ai_customer_design/scripts/render_qr.py '<练习链接>' --out course2.png
```

渲染成功后，**立即用 Read 工具读取生成的图片文件**，确保用户在对话中看到二维码图片。

> **路径说明**：`render_qr.py` 位于 `ai_customer_design` 技能目录下（不是 `coach-mcp-connect`）。
> **输出位置**：`--out` 参数路径相对于**当前工作目录**（cwd），不是脚本目录。不指定 `--out` 时默认写入系统临时目录，脚本会打印实际路径。

**禁止**：
- ❌ 只输出链接文本不展示二维码图片
- ❌ 用纯文本/ASCII/Unicode 字符"画"二维码
- ❌ 只生成文件但不展示（用户必须能在对话中直接看到图片）
- ❌ 大模型直接生成二维码（必须用 render_qr.py）

### QR 降级处理

QR 生成失败时，不要中断流程——直接告知用户"二维码无法生成，请复制下方练习链接在手机浏览器中打开访问"，并附上原始练习链接文本即可。

## 错误处理

连接类错误（401/403）→ 调用 `coach-mcp-connect` 技能恢复连接。业务错误码见上方「错误码」表。

## 工具白名单

本技能仅使用以下 11 个 MCP 工具，其他工具一律禁用：

**文件管理类**：
1. `training.file.upload_document` - 上传文档
2. `training.file.status` - 查询文件解析状态

**组织查询类**：
3. `training.organization.tree` - 查询组织树

**课程管理类**：
4. `training.ai_customer.create` - 创建课程（获取 courseId）
5. `training.ai_customer.update` - 更新课程内容
6. `training.ai_customer.update_status` - 查询生成状态
7. `training.ai_customer.get` - 查询课程详情

**交付类**：
8. `training.task.create_open_project` - 创建练习任务链接

> 二维码渲染通过脚本 `render_qr.py` 实现，不使用 MCP 工具。

**查询类**：
9. `training.course.list` - 课程列表查询
10. `training.task.get_detail_list` - 学员练习明细
11. `training.enum.lookup` - 枚举值查询

如果 tools/list 返回其他同名工具（如 upload / upload_doc），**禁止使用**，参考[禁用工具列表]。

## 禁用工具列表

以下工具**禁止使用**，调用会失败或行为不一致：

### 文件上传类
- ❌ `training.file.upload`（旧版本，用 `upload_document`）
- ❌ `training.file.upload_doc`（旧版本，用 `upload_document`）
- ❌ `training.file.upload_v2`（旧版本，用 `upload_document`）

### 课程管理类
- ❌ `course.edit_ai_customer_chat`（旧版本，用 `ai_customer.update`）
- ❌ `course_chat`（旧版本，用 `ai_customer.update`）
- ❌ `course.edit`（旧版本，用 `ai_customer.update`）

### 项目管理类
- ❌ `project_open_create`（重复，用 `task.create_open_project`）

### 二维码类
- ❌ `training.course_qr.render`（不存在，二维码渲染用脚本 `render_qr.py`）

### 组织查询类
- ❌ `organization.info_get`（**不存在**，用 `training.organization.tree`）

## 红线

1. **fileIds 原样传递**：用户已提供原始文档时，必须用 `upload_document.py` 脚本上传整份文档，把 fileId 经 `metadata.fileIds` 附到 chat；**禁止**直接调用 MCP 工具上传
2. **禁止生成 base64**：不要让 agent 读取文件并生成 base64 内容，必须用脚本
3. **不主动提示 token**：除非用户主动提供，否则不要询问 token/key

