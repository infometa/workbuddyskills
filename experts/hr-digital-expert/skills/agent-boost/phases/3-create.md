# 阶段3 · 创建（Create）

> **目标**：生成所有代码与配置文件（`.agent/`、`mcp_server/`、`chat-widget`）。
> **约束**：只生成代码，不启动 Bridge、不注册 Agent。chat-widget 直连 agent-server Gateway 域名，无需在用户应用注入反代代码。

---

## 3.1 写入 `.agent/agent.md`（人类可读说明书）

```markdown
---
name: <agent-name>
description: <一句话描述>
version: 0.1.0
projectId: <projectId>
# 注意：此文件不存放任何机密字段（企微凭证等由 agent-server 管理面板独立绑定）
---

# <Agent 名称>

## 角色
<role description>

## 可用 Skill
- skill-name — 一句话描述

## 可用工具
（数据类工具由 MCP Bridge 提供）
- list_endpoints — 列出本应用所有 API 端点
- call_api — 调用本应用任意 API
- <项目工具，按项目类型生成>
- <各已启用能力贡献的工具，按 `modules/registry.md` §3.2 的 `contributedTools` 自动列出>

（以下由 agent runtime 原生注入，不经 MCP Bridge）
- send_wework — 推送消息到企业微信（如启用）
- create_scheduled_task / list_scheduled_tasks / trigger / pause / resume / delete_scheduled_task — 定时任务（自动携带真实创建者身份）

## 工具使用规则
（按已启用能力动态生成，未启用能力的规则不出现。示例：dw-qa 启用时）
- 涉及 HR 数据查询时，必须先 read_file /skills/dw-qa/SKILL.md，按其中流程执行
- 数仓查询工具在读取 dw-qa Skill 前不可见，读取后自动可用
- 禁止在未阅读 Skill 的情况下尝试调用数仓查询工具

## 行为约束
- 始终使用工具获取最新数据，不要凭记忆回答
- 涉及敏感数据脱敏处理
- 高影响动作（删除/批量更新）需用户确认
```

agent.md body（去掉 frontmatter 后的部分）将作为注册请求的 `systemPrompt`。

---

## 3.2 写入 `.agent/skills/{name}/`（标准 Skill 目录）

每个 Skill 以标准文件夹形式生成，遵循 DeepAgents skill 目录规范：

```
.agent/skills/{name}/
├── SKILL.md              # 必须：YAML frontmatter (name + description) + 指令
├── references/           # 可选：参考文档（LLM 按需读取）
├── scripts/              # 可选：脚本
└── assets/               # 可选：模板/资源
```

- SKILL.md 必填，frontmatter 含 `name` + `description`，body 描述触发/流程/约束
- 支撑文件按需生成，路径相对于 skill 根目录（不含 `SKILL.md` 本身）
- 无支撑文件时目录内仅有 `SKILL.md`（`files` 为空 dict）
- 模板见 `references/agent-templates.md`（含单文件和多文件模板）

---

## 3.3 写入 `.agent/.env`（密钥存放）

```
# DO NOT COMMIT — agent-boost generated
# 企微凭证已迁移至 agent-server 管理面板绑定，不再在此存放
```

> 企微绑定由 agent-server 管理面板独立负责（agent 创建后按需绑定），不再随创建流程处理。

---

## 3.4 写入 `mcp_server/`（MCP Bridge）

> MCP Bridge 核心原则、模板结构、占位符说明详见 `modules/mcp.md#gen`。

```
mcp_server/
├── mcp_bridge.py        # FastMCP Server 主程序 + 项目工具（按模板生成）
└── requirements.txt     # 标准依赖（mcp + httpx + uvicorn）
```

**生成步骤：**

1. 确定 Bridge 端口（起始探测点，实际由 `_find_free_port()` 自动分配）：

```bash
export BRIDGE_PORT=${BRIDGE_PORT:-8932}
echo "✅ MCP Bridge 起始探测端口: ${BRIDGE_PORT}（实际端口自动分配）"
```

2. 调用 `gen-bridge.sh` 渲染模板（**禁止用 `python3 -c` 内联拼接**）：

```bash
PROJECT_NAME="{projectName}" \
PROJECT_ID="{projectId}" \
APP_PORT="{appPort}" \
BRIDGE_PORT="${BRIDGE_PORT:-8932}" \
KNOWN_ENDPOINTS_JSON='<全部 API 端点 JSON 数组（含 authz 新增接口）>' \
PROJECT_TOOLS='<按 appType 选取的项目工具代码，static 传 "# no project-specific tools">' \
bash ${SKILL_DIR}/scripts/gen-bridge.sh "{projectDir}/mcp_server"
# 输出: mcp_bridge.py + requirements.txt → {projectDir}/mcp_server/
# 渲染后自动执行 py_compile 语法检查
```

3. 按 `appType` 准备 `PROJECT_TOOLS`（详见 `modules/mcp.md#gen`）。`call_api` 和 `list_endpoints` 已内置，不需额外处理。

> **KNOWN_ENDPOINTS_JSON 来源**：
> - 未启用 authz：取 §1 分析的 `apis`
> - 启用 authz：将 §1 分析的 `apis` 与 §2 授权清单（`.agent/authz/api-authz.json`）合并——授权清单中的**所有**接口（含 `reuse:false` 的新增接口）都进入 KNOWN_ENDPOINTS，并携带 `requiredRole`。`list_endpoints` 透出权限信息（详见 `modules/mcp.md#gen`）。
> - authz #inject 生成的新 API 代码在此步骤**之前**已由 §2 confirm 确认并写入授权清单，KNOWN_ENDPOINTS 据此渲染，无需 inject 后再更新。
>
> **架构说明**：MCP Bridge 是 **Python FastMCP** 进程，部署在**应用容器内**，与应用同生命周期；监听 `0.0.0.0:${BRIDGE_PORT}`，通过 `register-mcp-svr` 注册域名后，agent-server 通过域名访问。

---

## 3.5 【CAPABILITY HOOK · inject】

> 紧接 MCP Bridge 骨架生成之后执行。对每个已启用的能力，依次执行其 `#inject` 锚点，生成代码产物（中间件 / 配置 / Bridge 工具片段）并注入。
> **执行方式**：按 `modules/registry.md` §3.1 能力清单表顺序，对 `enabled=true` 的能力逐一 inject。
>   - 各能力的 inject 产出独立文件（如 authz 的中间件 + 清单）。
>   - 若能力需向 MCP Bridge 贡献工具，通过 `PROJECT_TOOLS` 追加片段（见 `modules/mcp.md#gen`），最后统一渲染。
>   - 各能力贡献的工具名在 `modules/registry.md` §3.2 的 `contributedTools` 列声明，§3.1 agent.md "可用工具"段据此自动列出。
>
> **前置依赖校验**（`dependsOn`）：inject 前检查该能力声明依赖的核心层/能力是否已就绪：
> - 依赖未就绪 → 跳过本能力 inject，输出告警"⚠️ {userLabel} 依赖 {dependsOn} 未就绪，已跳过"，**不阻断主线**（其他能力继续执行）
> - 依赖就绪 → 正常执行 inject
> - 例：authz 若有依赖未就绪则跳过 inject
>
> 各能力的 inject 细节见对应 `modules/{name}.md#inject`。主线不硬编码任何能力名。

---

## 3.6 嵌入 chat-widget

> **版本检测**：如果 `{projectDir}/.agent/boost-state.json` 已存在且含 `widgetVersion` 字段，对比该值与模板 `assets/templates/chat-widget.js` 中的 `WIDGET_VERSION`。
> - **版本一致**：跳过复制，提示"chat-widget 已是最新版本"
> - **版本不一致**：覆盖复制，提示"chat-widget 已更新到 vX.X.X"
> - **无 boost-state.json（首次）**：直接复制

加载 `references/chat-widget.md`，按其中流程复制 `assets/templates/chat-widget.js` 并注入 `public/index.html`。

从 `assets/templates/chat-widget.js` 文件头部读取 `WIDGET_VERSION` 值，用于写入 boost-state.json（跨平台兼容写法，不依赖 PCRE grep）：
```bash
WIDGET_VERSION=$(grep -o "WIDGET_VERSION = '[^']*'" "${SKILL_DIR}/assets/templates/chat-widget.js" | head -1 | sed "s/.*= '//;s/'$//")
WIDGET_VERSION="${WIDGET_VERSION:-0.0.0}"
echo "📦 chat-widget 版本: ${WIDGET_VERSION}"
```

---

## 3.7 生成生产部署脚本

> 将部署脚本复制到 `.agent/scripts/`，随代码提交后由生产流水线使用。

```bash
mkdir -p "{projectDir}/.agent/scripts"
cp ${SKILL_DIR}/scripts/_env.sh          "{projectDir}/.agent/scripts/"
cp ${SKILL_DIR}/scripts/register-agent.sh "{projectDir}/.agent/scripts/"
cp ${SKILL_DIR}/scripts/prod-deploy.sh    "{projectDir}/.agent/scripts/"
chmod +x "{projectDir}/.agent/scripts/"*.sh
echo "✅ 生产部署脚本已复制到 .agent/scripts/"
```

> 生产环境部署流程详见 `deploy/prod.md`。

---

## 3.8 阶段三产出确认 · 写入 boost-state.json

```
✅ 代码生成完成（尚未注册、尚未部署）

产物：
  📄 .agent/agent.md
  📁 .agent/skills/*/（标准 Skill 目录：SKILL.md + 支撑文件）
  📄 .agent/.env
  🔌 mcp_server/（Python Bridge, 容器内 0.0.0.0:{BRIDGE_PORT}）
  🔐 各已启用能力产物（如 authz 的授权清单 + 中间件）
  💬 public/chat-widget.js + public/agent-entry-widget-icon.svg（支持 ?agent= 覆盖）
  📄 .agent/scripts/（生产部署脚本）

下一步 → 阶段四（注册）。
```

🔴 **阶段三完成时必须写入 boost-state.json**（字段定义见 `state/boost-state.md`）：

```bash
# staffName 来自 §0.0 MCP check_identity 获取的 STAFF_NAME 变量
mkdir -p "{projectDir}/.agent"
# SKILLS_META_JSON：按本次生成的 skill 列表构建，每项含 name + hasFiles
# 例：'[{"name":"app-guide","hasFiles":false},{"name":"overview-report","hasFiles":true}]'
SKILLS_META_JSON='{<按实际生成 skill 构建>}'
# CAPABILITIES_JSON：按本次 §2 实际启用的能力动态生成，每项含 enabled + configRef + 能力详情
# 未启用的能力不出现。例（authz 启用时）：
#   '{"authz":{"enabled":true,"configRef":".agent/authz/api-authz.json","enforcement":"middleware","framework":"express","roleSource":"db","generatedApis":["GET /api/employees/:id"]}}'
CAPABILITIES_JSON='{<按实际启用能力生成>}'

cat > "{projectDir}/.agent/boost-state.json" << BOOST_EOF
{"schemaVersion":1,"agentName":"{agentName}","projectId":"{projectId}","projectDir":"{projectDir}","staffName":"{staffName}","state":"created","skills":${SKILLS_META_JSON:-[]},"bridgePort":"${BRIDGE_PORT:-8932}","widgetVersion":"${WIDGET_VERSION}","capabilities":${CAPABILITIES_JSON:-{}},"createdAt":"$(date -u +%Y-%m-%dT%H:%M:%SZ)"}
BOOST_EOF
echo "✅ boost-state.json 已写入（state=created）"

```

> **注意**：`mcpUrl` 字段在 §4 部署注册后写入，§3 创建阶段不含此字段。
> `capabilities` 段是能力启用的唯一事实源，各能力的详情（如 authz 的 enforcement/framework/roleSource/generatedApis）直接内嵌在对应能力条目下，不再单独设 `authz` 顶层字段。

> 🔴 **阶段三结束时禁止停止**：必须继续进入阶段四。
> 阶段四会根据路线决定是否需要部署（详见 `phases/4-register.md` §4.0 入口决策）。
