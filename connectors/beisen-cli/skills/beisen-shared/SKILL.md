---
name: beisen-shared
version: 1.1.9
description: "北森 HR CLI 共享基础设施。本 Skill 为所有 beisen-* 业务域 Skill 的前置依赖，提供 CLI 安装检查、SSO 认证登录、身份与权限说明、高风险操作门禁协议（exit 10，写方法上线后生效）、HR 数据分级展示策略、JSON 输出契约、错误处理通用策略。当任何 beisen-* Skill 被触发时，必须先读取本 Skill 确保环境就绪。"
category: 人力资源/基础设施
author: beisen
agent_created: false
allowed-tools: Bash, Read
---

# beisen-cli 共享规则

本 Skill 是 beisen-cli 所有业务域 Skill 的公共基础设施。每个业务域 Skill 必须在其 SKILL.md 第一行声明：

```markdown
**CRITICAL — 开始前 MUST 读取 [../beisen-shared/SKILL.md](../beisen-shared/SKILL.md)**
```

---

## ⚠️ 前置检查 — 使用任何业务命令前必须执行

### Step 1：检查 CLI 是否安装

```bash
beisen-cli version
```

如果命令不存在或报错，执行安装：

```bash
npm install -g beisen-cli
```

安装后再次验证版本：

```bash
beisen-cli version
```

要求版本满足 `>=1.0.1`。

### Step 2：检查登录状态

```bash
beisen-cli auth status
```

- 输出 `authorized` → 已认证，可以继续使用
- 输出 `unauthorized` → 需要完成 Step 3

### Step 3：完成登录（仅未认证时执行）

优先使用 SSO 浏览器授权登录：

```bash
beisen-cli auth login
```

该命令会输出一个授权链接，引导用户在浏览器中完成北森 SSO 授权，授权完成后 CLI 自动获取 token。

**Agent 处理授权链接**：

1. 提取 CLI 输出中的授权 URL
2. 将授权链接直接输出给用户，提示用户点击链接在浏览器中完成北森 SSO 授权
3. 等待用户确认已完成授权
4. 验证登录状态（`beisen-cli auth status`）
5. 登录成功后：若用户此前有未完成的任务，继续执行后续任务；若无任务，结束当前流程，等待用户的下一条指令

**回退方案**：若 `auth login` 等待授权超时失败（如进程被 kill、exit 137，或浏览器未在窗口期内完成授权），改用 API Key 绑定登录：

```bash
beisen-cli auth bind --api-key <你的APIKey>
```

该命令将已有 API Key 绑定到当前设备并保存设备凭据，作为浏览器 SSO 不可用时的替代登录方式（需先从北森管理后台获取 API Key）。

---

## 认证与身份

### 身份模型

beisen-cli 不提供 `--as` 身份切换标志。执行身份由当前登录账号决定：用谁的账号登录，就以谁的身份执行操作。可查询的数据范围、是否具备管理权限，由北森后台对该账号的授权决定，而非 CLI 参数控制。

### 检查设备凭据

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

- `status: "valid"` → 设备凭据有效，可继续
- `status` 为其他值或 token 已过期 → 重新登录

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
| `beisen:approval:read` | 查询待办/已办任务及流程进度 | `approval task` / `approval approval` / `approval approvalUser` | 低 |
| `beisen:knowledge:read` | 读取企业知识库 | `knowledge retrieve` | 低 |
| `beisen:staffservice:read` | 读取员工档案、考勤、组织、业务数据及菜单 | `staffservice employeeData` / `staffservice employeeWork` | 中 |
| `beisen:recruitment:read` | 读取职位、候选人申请、人才库推荐 | `recruitment job` / `recruitment apply` / `recruitment talentPool` / `recruitment async_task` | 中 |
| `beisen:interview:read` | 读取招聘进展、面试官待办、面试质量分析、竞品情报、招聘需求 | `interview recruitmentProgress` / `interview interviewerTodo` / `interview interviewAnalysis` / `interview recruitRequirement` | 中 |

### 权限不足处理

当业务命令返回权限相关错误（如 `code` 非 `"200"`、`isSuccess: false` 或 `message` 提示无权限）时：

1. 从返回信封的 `message` 字段提取错误原因
2. 向用户说明当前账号缺少哪类数据访问权限及其用途
3. 引导用户联系企业管理员在后台开通对应权限
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
- ✅ 危险操作必须先展示操作摘要（操作类型、目标对象、影响范围），用户确认后才执行
- ✅ 单次批量写入/删除不超过 50 条；超过时拆批并逐批确认
- ✅ 所有 CLI 返回的 ID（employee_id、org_id 等）必须替换为可读名称后再展示给用户
- ✅ 涉及 L2/L3 敏感数据的查询结果，提取关键信息后摘要展示，不回显原始 JSON
- ✅ 查询他人数据时，先确认当前账号是否具备对应访问权限

---

## 高风险操作门禁协议（exit 10）

> **说明**： beisen-cli的方法均为读操作，不触发写操作门禁。以下 `exit 10` / `--yes` / `--dry-run` 协议为写方法上线后的预留设计，当前版本不会出现 exit 10。Agent 仍应了解该协议，以便写方法可用时正确处理。

beisen-cli 对高风险写操作有强制确认门禁。当 Agent 不带 `--yes` 调用高风险命令时，CLI 返回 exit code 10 + 结构化 JSON（exit code 10 即为确认信号，不需要判断 `ok`）：

```json
{
  "type": "confirmation",
  "subtype": "confirmation_required",
  "risk": "high-risk-write",
  "action": "<command>",
  "hint": "add --yes to confirm"
}
```

**Agent 遇到 exit 10 时必须：**

1. 识别 `type == "confirmation"` 和 `subtype == "confirmation_required"`
2. 向用户展示操作摘要（操作类型、目标对象、影响范围、风险等级）
3. 等待用户显式回复"确认 / 同意 / 执行"
4. 用户确认后，在原始命令末尾追加 `--yes` 重试
5. 用户拒绝 → 终止流程，不要擅自改写参数或跳过门禁

**绝对不允许：**
- 看到 exit 10 就默认加 `--yes` 静默重试（等于禁用安全门禁）
- 把 `confirmation_required` 当作网络错误或权限错误处理
- 在用户未明确同意前追加 `--yes` 重试

---

## HR 数据分级展示策略

| 级别 | 分类 | 数据示例 | 展示规则 |
|:---:|------|---------|---------|
| L0 | 公开 | 组织架构、部门名称、公司公告 | 正常完整展示 |
| L1 | 内部 | 员工姓名、职位、工号、部门 | 正常展示，批量查询时默认摘要模式 |
| L2 | 敏感 | 考勤记录（他人）、绩效结果、晋升记录 | 仅本人可查全部，他人查询时摘要展示；不回显原始 JSON |
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

```json
{
  "ok": true,
  "identity": "user",
  "data": {
    "code": "200",
    "message": "",
    "payload": {
      "hitKnowledgeList": [ { "title": "...", "summary": "..." } ]
    }
  }
}
```

- 内层 `code == "200"` → 业务成功，结果在 `payload.hitKnowledgeList`
- 内层 `code != "200"` → 业务失败，原因在内层 `message`

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

当 CLI 自身调用失败（未登录、参数缺失、网络异常等），退出码非 0，stderr 输出错误信息。此时外层 `ok` 可能为 `false` 或根本不返回 JSON，不属于业务信封，Agent 应按「错误处理通用策略」处理，不要尝试解析 `code`。

> **成功判断只看业务信封层**：外层 `ok: true` 仅表示 CLI 调用成功（进程正常退出），不代表业务成功。业务是否成功一律看内层 `code == "200"`。部分命令的响应可能不含外层 `ok`/`identity` 包装（直接返回业务信封），Agent 应以 `code` 字段为准统一判断。

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

> **不要使用 `--as`**： beisen-cli无身份切换标志，执行身份由登录账号决定。**不要使用 `--page`/`--size`**：分页字段写在 `--data` JSON 内。

---

## 错误处理通用策略

1. **认证失败**（未登录 / token 过期，退出码非 0）→ 引导用户重新登录，不重试业务 API
2. **权限不足**（`code != "200"` 且 `message` 提示无权限）→ 从 `message` 提取原因，向用户说明并引导联系管理员授权；不重试
3. **参数错误**（`--data` JSON 缺必填字段或格式不符 inputSchema）→ 先查 `beisen-cli schema` 或对应业务域 references，最多修正 1 次
4. **业务逻辑错误**（如"该审批已被处理"、"该员工不在可见范围内"）→ 解释 `message` 原因，给出下一步建议
5. **网络错误 / 超时** → 最多重试 2 次，间隔递增
6. **exit 10** → 按高风险操作门禁协议处理，向用户确认（beisen-cli不会触发，预留）

**重试限制：** 同一个失败原因最多重试 1 次（网络重试除外），防止 token 消耗和耗时失控。

---

## 更新检查

beisen-cli 提供 `beisen-cli update` 命令用于升级。业务命令输出中不附带版本通知字段。

- 不是每次任务都要查更新
- 先完成用户当前请求
- 如仍相关，再简短告知可运行：`beisen-cli update`

---

## 详细参考

- [references/auth.md](references/auth.md)：认证授权流程详解
- [references/security.md](references/security.md)：安全规则与门禁协议
- [references/error-codes.md](references/error-codes.md)：错误码参考与排查流程
