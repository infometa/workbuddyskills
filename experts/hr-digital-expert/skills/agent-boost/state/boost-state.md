# boost-state.json 状态管理

> `boost-state.json` 是 agent-boost 的状态文件，记录 Agent 的生命周期状态。
> 位于 `{projectDir}/.agent/boost-state.json`。

---

## 字段定义

```json
{
  "schemaVersion": 1,
  "agentName": "string",
  "projectId": "string",
  "projectDir": "string",
  "staffName": "string",
  "state": "new | created | deployed",
  "skills": [
    {"name": "skill-name-1", "hasFiles": false},
    {"name": "skill-name-2", "hasFiles": true}
  ],
  "bridgePort": "string",
  "widgetVersion": "string",
  "capabilities": {
    "authz": {
      "enabled": true,
      "configRef": ".agent/authz/api-authz.json",
      "enforcement": "middleware | reuse-existing | none",
      "framework": "express | fastapi | flask",
      "roleSource": "db | static | env | custom | none",
      "generatedApis": ["GET /api/employees/:id"]
    },
    "dw-qa": {
      "enabled": true,
      "configRef": ".agent/dw-qa/config.json",
      "skillDir": ".agent/skills/dw-qa",
      "mcpDependency": "hr_data_service_v1",
      "sqlCount": 48,
      "tableCount": 27,
      "features": ["组织看板", "HC管理", "招聘看板", "员工画像"]
    }
  },
  "createdAt": "ISO8601",
  "registeredAt": "ISO8601",
  "lastDeployedAt": "ISO8601",
  "mcpUrl": "http://{projectId}-internal-mcp-service.app.hrainative.woa.com/mcp"
}
```

| 字段 | 类型 | 写入时机 | 说明 |
|------|------|----------|------|
| `schemaVersion` | int | §3 | 固定 1 |
| `agentName` | string | §3 | Agent 名称 |
| `projectId` | string | §3 | 项目唯一标识 |
| `projectDir` | string | §3 | 项目绝对路径 |
| `staffName` | string | §3 | Agent owner（来自 §0 MCP `check_identity`） |
| `state` | string | §3→§4 | 状态机：`new` → `created` → `deployed` |
| `skills` | array | §3 | Skill 元数据列表，每项含 `name`（skill 名称）+ `hasFiles`（是否有支撑文件） |
| `bridgePort` | string | §3 | MCP Bridge 端口（开发环境自动探测，默认 8932 起；生产脚本使用固定值 9999） |
| `widgetVersion` | string | §3 | chat-widget.js 组件版本号（语义化版本） |
| `capabilities` | object | §3 | 能力启用清单（唯一事实源），各能力详情内嵌在对应条目下 |
| `createdAt` | ISO8601 | §3 | 创建时间 |
| `registeredAt` | ISO8601 | §4 | 注册时间 |
| `lastDeployedAt` | ISO8601 | §4 | 最后部署时间 |
| `mcpUrl` | string | **§4** | MCP Bridge 访问 URL（§3 创建阶段不含此字段，§4 部署注册后写入） |

> **`widgetVersion`**：阶段三写入时取 `assets/templates/chat-widget.js` 中的 `WIDGET_VERSION` 值。后续重新执行 `/agent-boost` 时，对比此字段与模板中的版本号，不一致则自动覆盖用户项目的 `public/chat-widget.js`。

> **`capabilities`**：能力启用清单（能力模块注册表的状态承载，见 `modules/registry.md`）。记录本应用启用了哪些可选能力及其配置文件路径和详情。阶段三写入，阶段四注册时保留。重新跑 `/agent-boost`（路线 B）时模型读此字段判断哪些能力的 hook 需要执行。**动态生成**：按本次实际启用的能力写入，不预设固定字段。每个条目含 `enabled`（是否启用）+ `configRef`（配置文件相对路径）+ 各能力自定义详情字段。`mcpDependency` 字段（如有）供 §4 注册时读取，自动追加到 Agent 的 `mcp_servers`。已注册能力见 `modules/registry.md` §3.1（当前：authz、dw-qa）。

> **`skills`**：标准格式 `[{"name": "...", "hasFiles": true/false}]`。`hasFiles` 表示该 skill 目录下是否有支撑文件（references/scripts/assets 等），用于注册时决定是否收集 `files` 字段。

---

## 状态机

```
new ──▶ created ──▶ deployed
         (§3.8 完成)   (§4 注册成功)
```

| state | 含义 | 写入时机 |
|-------|------|----------|
| `new` | 无 Agent，首次创建 | 默认值 |
| `created` | 代码已生成，未注册 | 阶段三 §3.8 结束时写入 |
| `deployed` | 已注册到 agent-server | 阶段四 `register-agent.sh` Step 3 写入（重建模式，保留关键字段） |

> **重建模式（保留关键字段）**：阶段四 `register-agent.sh` Step 3 读取旧文件，重建 dict 写入——运行时字段（`state`/`registeredAt`/`lastDeployedAt`/`mcpUrl`）更新为最新值，`createdAt`/`bridgePort`/`staffName`/`skills`/`widgetVersion`/`capabilities`/`authz` 从旧文件继承。

---

## 写入职责

| 时机 | 执行者 | 写入位置 |
|------|--------|----------|
| 阶段三完成（state=created） | 模型在 `phases/3-create.md` §3.8 中执行 heredoc | 本文件 |
| 阶段四注册成功（state=deployed） | `register-agent.sh` Step 3（Python 重建写入，保留关键字段） | 本文件 |

> 具体写入命令见 `phases/3-create.md` §3.8 和 `scripts/register-agent.sh`，本文件仅定义字段和状态机。
