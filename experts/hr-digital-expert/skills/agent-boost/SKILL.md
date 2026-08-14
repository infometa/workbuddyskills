---
name: agent-boost
description: "Analyze any deployed web application and add a smart Agent layer to it. Triggered by /agent-boost. Scans the project, recommends an Agent + Skills combo, asks the user to confirm, then generates a standardized MCP Bridge, agent.md, SKILL files, embeds a chat widget. Registers the agent with the shared agent-server. Works for any app type — not HR specific."
---

# agent-boost

为 Web 应用增加智能 Agent 能力。本 skill 是 `/agent-boost` 命令的核心实现。

> 核心设计：Agent 大脑跑在共享的 `agent-server`（FastAPI）上；MCP Bridge 跟用户应用一起跑（plugin 标准化生成，用户不写）；定时任务在 server 端。企微等外部集成由 agent-server 管理面板在 agent 创建后独立绑定，不进入创建主线。

> MCP 服务：身份认证与状态查询通过 `hr-claw-agent-server` MCP 服务完成（完整路径见下方速查表），调用 `check_identity`、`get_agent_status` 两个工具；Agent 注册统一走 `register-agent.sh` 脚本（dev/prod 同一脚本，仅 `AGENT_SERVER_URL` 不同）。

> Shell 命令约定见 `references/shell-conventions.md`（所有阶段适用）。

---

## MCP 工具速查

> MCP 服务完整路径：`HRIT/agent-boost/hr-claw-agent-server`（调用 MCP 工具时需使用完整路径，简写 `hr-claw-agent-server` 仅用于文档简称）。

| 工具 | MCP 服务 | 用途 | 使用阶段 |
|------|---------|------|---------|
| `check_identity` | `HRIT/agent-boost/hr-claw-agent-server` | 检查当前用户身份（鉴权平台自动注入 `x-tai-identity`） | §0 路由 |
| `get_agent_status` | `HRIT/agent-boost/hr-claw-agent-server` | 查询远端 Agent 注册状态 | §0 路由 |

---

## 流程纪律

1. **主线六阶段顺序执行** — §0→§1→§2→§3→§4→§5，路线 B/C 按路由跳转但不逆行
2. **能力启用遵循注册表** — §1 detect / §2 confirm / §3 inject / §5 test 均按 `modules/registry.md` 调用已启用能力的锚点；未启用的能力全程跳过，主线不硬编码任何能力名
3. **注册成功（`state:deployed`）后必须执行 §5 验证**，通过质量门禁后才输出「完成」
4. **禁止创建 `docs/plan.md`** — 本 skill 工作流已完整定义
5. **身份认证与状态查询通过 MCP 工具完成**（`check_identity`、`get_agent_status`）；**Agent 注册统一走 `register-agent.sh` 脚本**（dev/prod 同一脚本，仅 `AGENT_SERVER_URL` 不同）
6. **脚本操作调用封装脚本** — `KEY1="v1" bash ${SKILL_DIR}/scripts/xxx.sh`（gen-bridge / register-agent / test-mcp / remote-exec / prod-deploy 等）

---

## 主线流程

| 阶段 | 加载文件 | 一句话 | 能力 Hook |
|------|----------|--------|-----------|
| §0 路由 | `phases/0-context.md` | 检测状态 → 路线 A/B/C | — |
| §1 分析 | `phases/1-analyze.md` | 扫描项目 → 核心能力矩阵 | 【detect】 |
| §2 建议 | `phases/2-suggest.md` | 模板推荐 → 逐项弹窗确认（含能力启用确认） | 【confirm】 |
| §3 创建 | `phases/3-create.md` | 生成所有代码产物（Bridge + 各能力产物；不注册不部署） | 【inject】 |
| §4 注册 | `phases/4-register.md` | 入口决策 → 部署 Bridge（如需）→ 注册 Agent → 验证 loaded | — |
| §5 验证 | `phases/5-verify.md` | MCP 工具质量 + 能力测试 → 质量门禁通过才输出完成 | 【test】 |

**能力模块：**

| 模块 | 文件 | 层级 | 覆盖 |
|------|------|------|------|
| MCP Bridge | `modules/mcp.md` | 核心（always-on） | 生成(§3) → 部署(§4) → 测试(§5) |
| API 授权 | `modules/authz.md` | 可选能力（按需启用） | detect(§1) → confirm(§2) → inject(§3) → test(§5) |
| 数仓问数 | `modules/dw-qa.md` | 可选能力（按需启用） | detect(§1) → confirm(§2) → inject(§3) → test(§5) |

> 可选能力的注册表见 `modules/registry.md`。新增可选能力不改 phase 文件，只改 registry + 加 module 文件。

各阶段详细说明中内嵌脚本调用示例，脚本清单及变量定义见各阶段文件。

---

## 产物自检（注册后强制核对）

- [ ] `.agent/agent.md` 存在，frontmatter 解析无误，body 非空
- [ ] `.agent/boost-state.json` 存在，`state` 为 `deployed`
- [ ] 每个 skill 有 `SKILL.md`，frontmatter 含 `name`/`description`
- [ ] `mcp_server/mcp_bridge.py` 包含 `call_api` 和 `list_endpoints`，py_compile 通过
- [ ] 若启用 authz：`.agent/authz/api-authz.json` 存在，`apis` 非空；`enforcement=middleware` 时授权中间件已生成并注入应用入口
- [ ] `public/chat-widget.js` + `public/agent-entry-widget-icon.svg` 存在
- [ ] `public/index.html` 末尾包含 `<script src="chat-widget.js">`（如适用）
- [ ] agent 已注册且 `loaded: true`
- [ ] §5 已执行：
      - 核心报告 `.agent/mcp-test-report.json` 存在，`summary.gate=true`
      - authz 的 L3 结果在核心报告 `l3` 段（未启用 authz 时核心 gate 仅含 L1+L2）

---

## 故障排查

详见 `troubleshooting.md`。

