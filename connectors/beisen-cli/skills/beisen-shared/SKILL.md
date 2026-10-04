---
name: beisen-shared
version: 1.2.15
description: "北森 HR CLI 共享基础设施。本 Skill 为所有 beisen-* 业务域 Skill 的前置依赖，提供 CLI 安装检查（仅会话首次对话时执行）、SSO 认证登录（按需触发，由 CLI 返回 HTTP 401 + CLI_AUTH_005 驱动）、身份与权限说明、高风险操作门禁协议（exit 10，写方法上线后生效）、HR 数据分级展示策略、JSON 输出契约、错误处理通用策略。当任何 beisen-* Skill 被触发时，必须先读取本 Skill 确保环境就绪。"
category: 人力资源/基础设施
author: beisen
agent_created: false
allowed-tools: Bash, Read
requires-cli: ">=1.0.8"
---

# beisen-cli 共享规则

本 Skill 是 beisen-cli 所有业务域 Skill 的公共基础设施。每个业务域 Skill 必须在其 SKILL.md 第一行声明：

```markdown
**CRITICAL — 开始前 MUST 读取 [../beisen-shared/SKILL.md](../beisen-shared/SKILL.md)**
```

---

## ⚠️ 前置检查 — 仅会话首次对话时执行

> **全局 CLI 版本基线**：所有 beisen-* Skill 统一要求 `beisen-cli >= 1.0.8`（在本 Skill `requires-cli` 字段中声明）。各业务域 Skill 的版本要求应与 shared 保持一致，不低于 1.0.8，便于独立加载时自校验。

### Step 1：检查 CLI 是否安装（仅会话首次对话）

**在整个 Agent 会话中，只在第一次对话时执行版本检查。** 后续对话轮次直接执行业务命令，无需重复检查版本。

```bash
beisen-cli version
```

预期输出（退出码 0，版本号以实际为准）：

```
beisen-cli version 1.0.8
```

如果命令不存在或报错，先检查 Node.js 版本（要求 `≥ 22.20.0`）：

```bash
node -v
```

若版本不满足，停止并提示用户先升级 Node.js。Node.js 就绪后执行安装：

```bash
npm install -g beisen-cli
```

安装后再次验证版本：

```bash
beisen-cli version
```

### Step 2：直接执行业务命令（无需主动检查登录状态）

**不再主动调用 `beisen-cli auth status` 检查登录状态。** CLI 内部会在每次业务命令执行时自动校验认证状态，若凭据有效则正常返回数据，若凭据失效则返回结构化认证错误。

直接执行用户的业务命令即可。

### Step 3：响应式登录（仅在 CLI 返回认证错误时触发）

当业务命令返回以下错误时，触发登录流程：

```
HTTP 401: {"error_code":"CLI_AUTH_005","error_message":"xxxxx"}
```

**识别规则**：CLI 返回信息中同时包含 `HTTP 401` 和 `CLI_AUTH_005` → 表示凭据失效，需要重新登录。

#### 3a. 判断凭据状态，选择登录路径

收到 `CLI_AUTH_005` 后，**先执行一次 `beisen-cli auth status`** 判断本地凭据状态，据此选择路径：

| `auth status` 结果 | 含义 | 登录路径 |
|---|---|---|
| `status: "valid"` | 本地凭据未过期，但服务端已拒绝（凭据陈旧/被撤销） | → **直接走 API Key 绑定**（路径 B），不要再做 SSO 登录 |
| `status` 非 valid / 命令报错 | 本地无有效凭据 | → 先尝试 SSO 登录（路径 A） |

> **为什么 status=valid 时不要再做 SSO**：本地 token 未过期但服务端已不认可，SSO 登录会复用同一设备 ID 生成新的 device request，但服务端可能仍拒绝该设备的旧关联。API Key 绑定是独立的认证路径，可绕过此问题。

#### 3b. 路径 A — SSO 浏览器授权登录

```bash
beisen-cli auth login
```

该命令会输出一个授权链接，等待用户在浏览器中完成北森 SSO 授权。

**Agent 处理授权链接**：

1. 提取 CLI 输出中的授权 URL（用正则 `https?://[^\s]+` 匹配输出中以 `https://` 开头的完整 URL）
2. **立即**将授权链接输出给用户，提示点击链接在浏览器中完成授权。**必须提醒用户：授权链接有效期为 10 分钟，请尽快完成**
3. 等待用户确认已完成授权（登录命令会阻塞直到授权完成或超时）
4. 登录成功后：重新执行此前因认证失败的业务命令

**若 SSO 授权超时失败**（输出含"授权超时"或"CLI_AUTH_001"）→ 立即切换到路径 B（API Key 绑定），不要再重试 SSO。

#### 3c. 路径 B — API Key 绑定登录

当 SSO 不可用或凭据陈旧时，使用 API Key 绑定：

1. 告知用户：「当前 SSO 登录无法完成，请改用 API Key 方式。请在北森 web 端获取 API Key：**右上角人员头像 → 个人设置 → API Key管理 → 创建API Key**，然后将 API Key 发给我。API Key 格式示例：q/oP*xxx4w== 」
2. 用户提供 API Key 后，执行绑定命令：
   ```bash
   beisen-cli auth bind --api-key <用户提供的APIKey>
   ```
3. 绑定成功后：重新执行此前因认证失败的业务命令

#### 3d. 认证流程禁止事项

- ❌ **禁止 `auth logout` 后再 `auth login`**：logout 会清除本地凭据，若新 login 又失败则用户陷入无凭据状态
- ❌ **禁止连续多次 `auth login`**：SSO 超时后直接切换路径 B，不要反复生成授权链接
- ❌ **禁止在 status=valid 时重复 SSO 登录**：见 3a 表格，直接走路径 B
- ❌ **禁止对同一 401 错误重试业务命令**：先完成登录/绑定，再重试业务命令

---

## 认证与身份

### 身份模型

beisen-cli 不提供 `--as` 身份切换标志。执行身份由当前登录账号决定：用谁的账号登录，就以谁的身份执行操作。可查询的数据范围、是否具备管理权限，由北森后台对该账号的授权决定，而非 CLI 参数控制。

### 认证状态检查（按需）

认证状态由 CLI 内部自动校验，Agent 无需主动调用 `beisen-cli auth status`。仅当 CLI 返回 `HTTP 401` + `CLI_AUTH_005` 时才触发登录流程（见「前置检查 Step 3」）。

如需手动排查认证问题，可使用：

```bash
beisen-cli auth status
```

预期输出（凭据有效）：

```json
{
  "deviceId": "22cf...0f7a",
  "expiryTime": "2026-11-05T12:31:51Z",
  "status": "valid"
}
```

> **注意：`status: "valid"` 仅表示本地凭据未过期，不代表服务端仍认可该凭据。** 若 `auth status` 返回 valid 但业务命令仍报 `CLI_AUTH_005`，说明服务端已撤销该凭据（可能因密码变更、管理员操作、设备策略变更等），此时应直接走 API Key 绑定（Step 3 路径 B），不要再尝试 SSO 登录。

### 退出登录

```bash
beisen-cli auth logout
```

---

## 权限三层模型

```
第 1 层：身份认证 → beisen-cli auth login（SSO）/ auth bind（API Key 回退）
第 2 层：组织授权 → 企业管理员在后台开启账号的数据访问权限
第 3 层：业务 scope → 具体操作所需的权限范围
```

> **说明**： beisen-cli 的方法 inputSchema/outputSchema 中未暴露 scope 校验字段，以下 scope 清单为概念模型，供 Agent 理解权限边界；实际能否访问由后台对该登录账号的授权决定。

### 业务 scope 清单

| scope | 说明 | 对应 CLI 命令 | 风险等级 |
|-------|------|-------------|:------:|
| `beisen:approval:read` | 查询待办/已办任务及流程进度 | `approval task` | 低 |
| `beisen:knowledge:read` | 读取企业知识库 | `knowledge retrieve` | 低 |
| `beisen:staffservice:read` | 读取员工档案、考勤、组织、业务数据及菜单 | `staffservice employeeData` / `staffservice employeeWork` | 中 |
| `beisen:recruitment:read` | 读取职位、候选人申请、人才库推荐 | `recruitment job` / `recruitment apply` / `recruitment_ai talentPool` / `recruitment_ai async_task` | 中 |
| `beisen:interview:read` | 读取招聘进展、面试官待办、面试质量分析、竞品情报、招聘需求 | `interview recruitmentProgress` / `interview interviewerTodo` / `interview_ai interviewAnalysis` / `interview recruitRequirement` | 中 |

### 权限不足处理

当业务命令返回权限相关错误（如 `code` 非 `"200"`、`isSuccess: false` 或 `message` 提示无权限）时：

1. 从 `message` 提取权限不足的原因
2. 向用户说明当前账号缺少哪类访问权限
3. 引导用户联系租户管理员授权及购买安装相关的产品
4. 不要对权限错误反复重试业务命令

---

## 安全规则

### 绝对禁止

- ❌ 不要把 AppKey、AppSecret、access_token 写入 SKILL.md、references 或日志
- ❌ 不要编造 employee_id、org_id、approval_code 等标识符；必须从 CLI 返回中提取
- ❌ 不要在未获用户确认时执行薪酬查询、批量操作、数据导出
- ❌ 不要将人力资源数据（薪酬、绩效、个人信息）发送到任何外部系统
- ❌ 不要在同一轮对话中展示敏感数据后紧跟着询问"是否要分享"
- ❌ 不要在 L3 机密数据场景中跳过二次身份验证

### 严格要求

- ✅ 所有业务命令默认输出 JSON 结构化格式，可直接解析
- ✅ 所有 CLI 返回的 ID（employee_id、org_id 等）必须替换为可读名称后再展示给用户
- ✅ 涉及 L2/L3 敏感数据的查询结果，提取关键信息后摘要展示，不回显原始 JSON
- ✅ 查询他人数据时，先确认当前账号是否具备对应访问权限

> **写操作门禁协议（预留）**：当前版本所有 CLI 方法均为读操作，不触发写操作门禁。写方法上线后的 `exit 10` 强制确认协议与批量写规则详见 [references/write-protocol.md](references/write-protocol.md)。

---

## HR 数据分级展示策略

| 级别 | 分类 | 数据示例 | 展示规则 |
|:---:|------|---------|---------|
| L0 | 公开 | 组织架构、部门名称、公司公告 | 正常完整展示 |
| L1 | 内部 | 员工姓名、职位、工号、部门 | 正常展示，批量查询时默认摘要模式 |
| L2 | 敏感 | 考勤记录（他人）、绩效结果、晋升记录、候选人/求职者信息（招聘域） | 仅本人可查全部，他人查询时摘要展示；不回显原始 JSON |
| L3 | 机密 | 薪酬、工资条、身份证号、合同附件 | 二次身份验证；脱敏展示；不回显原始 JSON；不写入任何持久化存储 |

**数据展示强制规则：**

- 查询 L2/L3 级别的他人数据时 → 必须先确认当前账号是否具备管理员访问权限
- L3 数据查询 → 二次身份验证（密码或短信验证码），验证失败直接终止
- 展示 L3 数据后 → 以"薪酬/个人信息已展示，请注意信息安全"作为收尾

---

## JSON 输出契约

业务命令默认输出 JSON，退出码 0 表示 CLI 调用本身成功。CLI 实际输出为**两层嵌套结构**：

```
┌─ CLI 调用包装层（外层）──────────────────┐
│  ok: boolean    — CLI 调用是否成功       │
│  identity: string — 执行身份（如 "user"）│
│  data: object   ┌─ 业务信封层（内层）─────┐│
│                 │  code: string          ││
│                 │  data / payload: ...   ││
│                 │  message: string       ││
│                 └────────────────────────┘│
└──────────────────────────────────────────┘
```

**两层各自的职责**：

| 层级 | 字段 | 含义 | 何时关注 |
|------|------|------|---------|
| CLI 调用包装层（外层） | `ok`、`identity`、`data` | CLI 进程是否正常执行并返回了响应 | 通常无需关注；仅在排查 CLI 自身故障时参考 |
| 业务信封层（内层，位于外层 `data` 中） | `code`、`data`/`payload`、`message` | 业务请求是否成功、业务数据内容 | **始终关注此层** |

**判断业务成功一律看业务信封层的 `code == "200"`**（注意 `code` 是字符串 `"200"`，不是数字 200，也不是退出码）。外层 `ok: true` 仅表示 CLI 调用成功，不代表业务成功。

### 审批域信封（approval）

```json
{
  "ok": true,
  "identity": "user",
  "data": {
    "code": "200",
    "isSuccess": true,
    "data": [ { "instanceCode": "...", "title": "..." } ],
    "message": ""
  }
}
```

- 内层 `code == "200"` 且 `isSuccess == true` → 业务成功，结果在内层 `data` 数组
- 内层 `code != "200"` 或 `isSuccess == false` → 业务失败，原因在内层 `message`

### 知识域信封（knowledge）

> **注意**：`beisen-cli knowledge` 命令使用与其他命令不同的成功标准——`code == "0"`表示成功，非 `"0"` 表示异常。其他所有命令仍以 `code == "200"`（字符串）为成功标准。

```json
{
  "ok": true,
  "identity": "user",
  "data": {
    "code": "0",
    "message": "",
    "payload": {
      "hitKnowledgeList": [ { "title": "...", "summary": "..." } ]
    }
  }
}
```

- 内层 `code == "0"` → 业务成功，结果在 `payload.hitKnowledgeList`
- 内层 `code != "0"` → 业务失败，原因在内层 `message`

### 数据查询域信封（staffservice）

```json
{
  "ok": true,
  "identity": "user",
  "data": {
    "code": "200",
    "data": { "..." : "..." }
  }
}
```

- 内层 `code == "200"` → 业务成功，结果在内层 `data`
- 内层 `code != "200"` → 业务失败

### 调用级错误

当 CLI 自身调用失败（认证失效返回 `HTTP 401` + `CLI_AUTH_005`、参数缺失、网络异常等），退出码非 0，stderr 输出错误信息。此时外层 `ok` 可能为 `false` 或根本不返回 JSON，不属于业务信封。认证失效按「错误处理通用策略」第 1 条处理（触发响应式登录），其他错误按对应条目处理，不要尝试解析 `code`。

> **成功判断只看业务信封层**：外层 `ok: true` 仅表示 CLI 调用成功（进程正常退出），不代表业务成功。业务是否成功一律看内层 `code == "200"`。部分命令的响应可能不含外层 `ok`/`identity` 包装（直接返回业务信封），Agent 应以 `code` 字段为准统一判断。

### 输出格式约束（仅适用于 recruitment / interview）

以下输出约束仅针对 `beisen-cli recruitment` 和 `beisen-cli interview` 域命令，其他 Skill 按各自输出规则处理：

- **禁止生成 JSON 文件**：不得将查询结果以 JSON 文件形式输出给用户。
- **CSV 表头必须使用中文**：生成 CSV 文件时，表头禁止使用英文字段名（如 `name`、`educationLevel`、`phaseStatus`），必须使用中文（如"姓名""学历""阶段状态"）。

---

## ID 引用规则

> **适用于所有 beisen-cli 工具调用，包括 beisen-data-query 中的 SceneTool / SceneToolMessage / SearchFormTool / BusinessDataTool 及所有其他 CLI 工具。**

1. **只复制真实值**：当工具返回结果包含 `id`、`task_id`、`record_id`、`intentionId`、`menuId` 等标识符，你只允许直接复制工具返回 content 中真实存在的值。
2. **严禁编造 ID**：严禁自己编造、猜想、拼接任何 id。如果需要传给下一个工具的参数 id 不在刚刚 tool 返回的内容中，禁止调用工具，向用户报错说明缺少 ID。
3. **精确匹配**：调用后续工具时，引用的 ID 必须完全和 tool 返回 JSON 字符串中的字符完全一致，大小写、符号不能修改。
4. **就近取用**：不要靠记忆记录 id，所有参数值必须来源于最近 tool 角色返回的 JSON 内容。
5. **空值阻断**：如果工具返回为空 / 没有需要的 id，停止工具调用，告知用户无法继续。

---

## 全局标志

beisen-cli 业务方法不使用 `--query`/`--page`/`--size`/`--as` 等分散标志，所有方法入参统一通过 `--data` 以 JSON 字符串承载。分页、筛选条件都写在 `--data` 的 JSON 内（按各方法 inputSchema 要求）。

| 标志 | 说明 | 适用 |
|------|------|------|
| `--data` | 方法入参，JSON 字符串。无入参的方法可省略 | 所有带 inputSchema 的方法 |
| `--params` | 原始 URL/查询参数 JSON | 部分方法（无 `--data` 的方法） |
| `--format` | 输出格式：`json`\|`ndjson`\|`table`\|`csv`，默认 `json` | 所有业务方法 |
| `--jq` / `-q` | 使用 jq 表达式过滤 JSON 输出 | 所有业务方法 |
| `--output` / `-o` | 二进制响应输出文件路径 | 所有业务方法 |
| `--json` | `--format json` 的简写 | 所有业务方法 |

> **注意**：同一 API 组下的不同子命令可能使用不同的参数标志。例如 `beisen-cli staffservice employeeData` 组中，`searchFormTool` 和 `sceneToolMessageForCLI` 使用 `--params`，而 `businessDataTool` 使用 `--data`。调用前请查阅对应 Skill 文档确认具体用法。

> **不要使用 `--as`**： beisen-cli无身份切换标志，执行身份由登录账号决定。**不要使用 `--page`/`--size`**：分页字段写在 `--data` JSON 内。

---

## 日期参数格式

不同 CLI 子命令的日期参数格式由各自 inputSchema 决定，Agent 应以各 Skill 命令文档为准。常见格式速查：

| Skill / 命令域 | 参数示例 | 格式说明 |
|---------------|---------|---------|
| `beisen-cli staffservice employeeData`（数据查询流水线） | `2026/06/01-2026/06/30` | 起止日期，用 `/` 分隔，`-` 连接，月日两位补零，年份完整 |
| `beisen-cli approval task` | `2026-08-01` | 单日期，ISO 8601（`YYYY-MM-DD`） |
| `beisen-cli interview recruitmentProgress` / `interviewerTodo` | `2026-07-11` | 单日期，ISO 8601（`YYYY-MM-DD`），用于 `startDate` / `endDate` |

> **注意**：禁止将一种命令的日期格式直接套用到另一种命令。拼入 `--data` / `--params` 前，必须按目标命令 inputSchema 要求的格式转换。

---

## 错误处理通用策略

1. **认证失效**（CLI 返回 `HTTP 401` + `error_code: "CLI_AUTH_005"`）→ 按「前置检查 Step 3」处理：先 `auth status` 判断凭据状态，status=valid 走路径 B（API Key 绑定），status 非 valid 走路径 A（SSO 登录）。SSO 超时或失败后立即切路径 B，不再重试。**整个认证流程最多 1 轮 SSO + 1 轮 API Key 绑定**，若均失败则告知用户联系管理员
2. **权限不足**（`code != "200"` 且 `message` 提示无权限）→ 从 `message` 提取原因，向用户说明并引导联系租户管理员授权及购买安装相关的产品；不重试
3. **参数错误**（`--data` JSON 缺必填字段或格式不符 inputSchema）→ 先查 `beisen-cli schema` 或对应业务域 references，最多修正 1 次
4. **业务逻辑错误**（如"该审批已被处理"、"该员工不在可见范围内"）→ 解释 `message` 原因，给出下一步建议
5. **网络错误 / 超时** → 最多重试 2 次，间隔递增
6. **exit 10** → 按 [references/write-protocol.md](references/write-protocol.md) 的高风险写操作门禁协议处理，向用户确认（当前版本不会触发，预留）

**重试限制：** 同一个失败原因最多重试 1 次（网络重试除外），防止 token 消耗和耗时失控。

---

## 更新检查

检查是否有新版本：

```bash
beisen-cli update --check
```

该命令输出当前版本与最新版本的对比信息。

### 升级流程

升级前必须先确认版本，告知用户后再执行：

```bash
# 1. 检查当前版本
beisen-cli version
# 2. 检查最新版本
beisen-cli update --check
```

用户确认后，升级 CLI：

```bash
npm update -g beisen-cli
```

升级后验证：`beisen-cli version`

### 升级提醒策略

- 不是每次任务都要查更新
- 先完成用户当前请求
- 任务结束后，如仍相关，再简短告知可运行：`beisen-cli update --check`
- 不要在任务执行中途打断用户去做升级

---

## 详细参考

- [references/auth.md](references/auth.md)：认证授权流程详解
- [references/security.md](references/security.md)：安全规则
- [references/write-protocol.md](references/write-protocol.md)：高风险写操作门禁协议（预留）
- [references/error-codes.md](references/error-codes.md)：错误码参考与排查流程
