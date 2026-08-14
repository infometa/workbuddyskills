# 阶段0 · 上下文检测与路由

> **目标**：检测本地和远端状态，路由到正确的执行路线。
> **约束**：每次 `/agent-boost` 触发时首先执行。

---

## 0.0 身份认证

调用 `hr-claw-agent-server` MCP 服务的 `check_identity` 工具检查当前用户身份：

- `{"authenticated": true, "userId": "xxx"}` → 身份有效，`STAFF_NAME=userId`，进入 §0.1
- `{"authenticated": false}` → 提示用户：「MCP 连接异常或未登录，请检查 MCP 服务 `hr-claw-agent-server` 是否正常连接，并确认已在鉴权平台完成登录」

> 身份认证由鉴权平台通过 `x-tai-identity` header 自动完成，MCP 网关解码后获取 `userId`。用户首次使用时需在鉴权平台点击登录。

---

## 0.1 检测本地和远端状态

### 本地状态（直接读文件）

1. 检查 `{projectDir}/.agent/agent.md` 是否存在
   - 存在 → `HAS_AGENT=true`，读取 frontmatter 中的 `name` 字段作为 `AGENT_NAME`
   - 不存在 → `HAS_AGENT=false`

2. 检查 `{projectDir}/.agent/boost-state.json` 是否存在
   - 存在 → 读取内容，获取 `state`、`agentName`、`projectId` 等
   - 不存在 → `state: "new"`

### 远端状态（MCP 工具）

若本地存在 `.agent/agent.md`（已知 `AGENT_NAME`），调用 `hr-claw-agent-server` MCP 服务的 `get_agent_status` 工具：

- `{"exists": true, "loaded": true, "skillCount": N}` → 已注册且已加载
- `{"exists": true, "loaded": false}` → 已注册但未加载
- `{"exists": false}` → 未注册

> 若 MCP 工具调用失败，提示用户：「MCP 连接异常，请检查 MCP 服务 `hr-claw-agent-server` 是否正常连接」

---

## 0.2 路由判断

| 本地 `.agent/` | Agent Server | 场景 | 下一步 |
|---------------|-------------|------|--------|
| 不存在 | — | 首次创建 | → **路线 A：全新创建** |
| 存在 | 已注册·loaded=true | 已有正常运行 Agent | → **路线 B：快速模式**（询问意图） |
| 存在 | 已注册·loaded=false | 注册了但 Bridge 不通 | → 提示排查，或路线 B 选重新部署 |
| 存在 | 未注册 | 代码有但未注册 | → **路线 C：重新注册**（跳过 §§1-3） |

---

## 0.3 路线 A：全新创建

按 §1→§2→§3→§4 全流程执行。

---

## 0.4 路线 B：快速模式（意图快问）

检测到已有 Agent 时，**必须先询问用户意图**，不做任何操作：

```
🔍 检测到已有 Agent：{agentName}
   状态：{已部署 / 未部署} · {N} 个 Skill

   这次想做什么？
   1) ✏️ 修改现有 Skill — 只改 prompt/规则，修改后自动注册更新
   2) ➕ 新增一个 Skill — 快速添加新能力，保留现有配置
   3) 🔄 重新部署 — 代码有改动，跳过分析直接部署上线
   4) 🔁 从头创建 — 覆盖现有配置，全新开始
```

| 用户选 | 跳转目标 | 说明 |
|--------|----------|------|
| 1 | → §2 修改模式 | 展示 Skill 列表 → 选要改的 → 编辑 SKILL.md → 判断是否需要部署 → 注册更新 |
| 2 | → §2 轻量版 | 选模板/自定义 Skill → §3 生成新 Skill（不重建已有文件）→ 判断是否需要部署 → 注册更新 |
| 3 | → §4 | 跳过 §§1-3，直接部署 + 注册 |
| 4 | → §1 | 全流程，覆盖已有 `.agent/` 和注册 |

---

## 0.5 路线 C：重新注册

```
🔍 检测到 .agent/ 存在但 Agent 未注册。

   快速选项：
   1) 🔗 重新注册 — 部署后注册
   2) 🔁 从头创建 — 覆盖现有配置，全新开始
```

| 用户选 | 跳转目标 |
|--------|----------|
| 1 | → §4（部署+注册），或直接快速注册 |
| 2 | → §1 全流程 |
