# 阶段4 · 部署与注册

> **目标**：部署 Bridge（如需）并注册 Agent 到 agent-server。
> **约束**：注册与部署解耦——注册只需 agentName、skills、systemPrompt 和 MCP URL。Bridge 如何部署是 deploy/ provider 的责任。

---

## 4.0 入口决策

| 路线 | 场景 | 走向 |
|------|------|------|
| A | 全新创建 | §4.1 完整部署 → §4.2 注册 |
| C 选1 | 代码有但未注册 | §4.1 完整部署 → §4.2 注册 |
| B 选3 | 重新部署 | §4.1 完整部署 → §4.2 注册 |
| B 选1/2 | 只改了 skill/prompt | §4.3 快速注册（跳过部署） |

---

## 4.1 部署 Bridge（路线 A / C / B选3）

> 部署是 `deploy/` provider 的责任。§4 只负责拿到 MCP_URL 后注册。

**步骤 1：选择 provider**

检测 page-deliver 可用性：
- 可用 → 加载 `deploy/anydev.md` 执行
- 不可用 → 加载 `deploy/manual.md` 执行

**步骤 2：按 provider 步骤完成部署**

provider 会依次完成：
1. 部署应用（打包上传 + PM2 启动）
2. 部署 MCP Bridge（安装依赖 + PM2 启动 + 健康检查）
3. 注册 MCP 服务域名（`register-mcp-svr` 关联域名 → 容器 IP:port）

**步骤 3：获得 MCP URL**

部署完成后，MCP URL = `http://{projectId}-internal-mcp-service.app.hrainative.woa.com/mcp`

继续进入 §4.2 注册。

---

## 4.2 注册 Agent

> 通过 `register-agent.sh` 脚本完成：读取 skill 文件 → 构建 body → curl 注册到 agent-server（unload → upsert → load → 验证）。
> 认证：`X-Staff-Name` header（dev 直连地址，prod 生产地址，均由 `_env.sh` 管理）。
> dev/prod 统一使用此脚本，仅 `AGENT_SERVER_URL` 不同。

### 调用脚本

```bash
AGENT_NAME="{agentName}" \
PROJECT_ID="{projectId}" \
PROJECT_DIR="{projectDir}" \
STAFF_NAME="{staffName}" \
MCP_URL="http://{projectId}-internal-mcp-service.app.hrainative.woa.com/mcp" \
bash ${SKILL_DIR}/scripts/register-agent.sh
```

> `AGENT_SERVER_URL` 默认从 `_env.sh` 读取（dev 直连），`prod-deploy.sh` 覆盖为生产地址。
> 脚本自动完成：读取 `agent.md` → system_prompt；读取 `skills/*/` → skills 数组；读取 `boost-state.json` → mcp_servers（含能力 MCP 依赖）；curl 注册；重建写 boost-state.json（保留创建期字段）。

### 检查结果

- `loaded=true` → 注册成功，继续 §4.4
- `loaded=false` → 警告 Bridge 可能未就绪
- 脚本失败 → 检查 agent-server 连接（`_env.sh` 中的 `AGENT_SERVER_URL` 是否可达）

---

## 4.3 路线 B 快速注册（跳过部署）

> **仅路线 B 选1/2 触发。** 其他路线走 §4.1 完整部署。

### 部署决策

```
改动范围检测：
  ├── 只改了 .agent/skills/（含 SKILL.md 及支撑文件）或 .agent/agent.md
  │     → 无需重新部署，直接「快速注册」（秒级生效）
  │
  └── 改了 server.js / mcp_server/ / public/...
        → 需要重新部署，走 §4.1 完整部署
```

### 快速注册（不重新部署）

从 `boost-state.json` 读取 `mcpUrl`，调用 `register-agent.sh`（与 §4.2 相同，脚本自动读取 skill 文件 + 构建 body + 注册）。

**边界检查**：若 `boost-state.json` 中 `mcpUrl` 为空（从未部署过），快速注册无法进行，提示用户先走 §4.1 完整部署。

---

## 4.4 注册完成 → 转入 §5 验证

```
✅ 注册成功

🧠 Agent   ：{agentName} (已加载)

下一步 → 阶段五（验证）：MCP 工具质量 + 授权校验。

> 企微机器人已改为 agent 创建后到 agent-server 管理面板按需绑定，不再随创建流程处理。
```

> 🔴 **注册成功后禁止直接输出「完成」**：必须继续进入 `phases/5-verify.md` 完成 MCP 质量门禁后，才输出最终「完成」。
> 快速注册路线（§4.3）改动若仅涉及 skill/prompt（未动 mcp_server/ 与授权），可跳过 §5。
