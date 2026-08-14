# 部署 Provider：生产环境（流水线 + 脚本）

> 生产环境通过流水线 + 脚本部署，不依赖 CodeBuddy agent/skill。
> agent-boost 在阶段三自动将部署脚本复制到 `.agent/scripts/`，随项目代码一起打包上传。

---

## 与开发环境的区别

| 维度 | 开发环境 | 生产环境 |
|------|----------|----------|
| 触发方式 | `/agent-boost` 命令（agent + skill） | 流水线执行 `prod-deploy.sh` |
| Agent Server | MCP 服务自动处理 | `http://agent-server.prod.hrainative.woa.com` |
| 认证方式 | MCP 网关自动注入 `x-tai-identity` | `X-Staff-Name` header（脚本传，agent-server 自动解析） |
| Bridge 端口 | 自动探测（8932 起） | **固定 9999** |
| MCP 域名 | `{projectId}-internal-mcp-service.app.hrainative.woa.com` | `{projectId}-internal-mcp-service.prod.hrainative.woa.com` |
| 域名注册 | `page-deliver mcp register-mcp-svr` | **无需注册**（域名预先配置，固定指向 9999） |

---

## 前置条件

阶段三（`/agent-boost`）已在项目中生成以下文件：

```
{projectDir}/
├── .agent/
│   ├── agent.md
│   ├── boost-state.json          # 含 agentName, projectId, staffName, bridgePort
│   ├── skills/
│   └── scripts/                  # 生产部署脚本（阶段三自动复制）
│       ├── _env.sh
│       ├── register-agent.sh
│       └── prod-deploy.sh
├── mcp_server/
│   ├── mcp_bridge.py
│   └── requirements.txt
└── ...（用户应用代码）
```

---

## 执行方式

容器启动后，在容器内执行：

```bash
bash /data/services/apps/{projectId}/.agent/scripts/prod-deploy.sh
```

> 脚本路径取决于容器内应用部署路径。`PROJECT_DIR` 环境变量可覆盖默认值（当前目录）。

### 环境变量

| 变量 | 默认 | 说明 |
|------|------|------|
| `PROJECT_DIR` | 当前目录 | 项目根目录 |
| `APP_PORT` | `3000` | 应用端口（Bridge 反向调用） |
| `PROD_AGENT_SERVER` | `http://agent-server.prod.hrainative.woa.com` | 生产 agent-server 地址（HTTP，脚本直连） |

---

## 脚本执行流程

`prod-deploy.sh` 自动完成两步：

### Step 1: 启动 MCP Bridge（端口 9999）

- 安装 Python 依赖（`pip3 install -r requirements.txt`）
- PM2 启动 `mcp_bridge.py`，固定 `BRIDGE_PORT=9999`
- 健康检查（`tools/list`）

### Step 2: 注册 Agent

- 从 `boost-state.json` 读取 `agentName`、`projectId`、`staffName`
- 调用 `register-agent.sh`，通过 `X-Staff-Name` header 传递身份
- POST 注册（upsert，无需先 DELETE）→ 验证 loaded → 更新 boost-state.json
- MCP URL = `http://{projectId}-internal-mcp-service.prod.hrainative.woa.com/mcp`

---

## 认证说明

- **认证方式**：脚本通过 `X-Staff-Name` header 传递身份（agent-server `get_current_user` 自动解析）
- **staff_name 来源**：`boost-state.json` 中的 `staffName` 字段（开发环境 `/agent-boost` 时通过 MCP `check_identity` 获取并保存）

---

## 企微配置

企微机器人绑定已迁移至 agent-server 管理面板，agent 创建后按需在面板绑定（dev/prod 均如此），不再随部署脚本处理。

---

## MCP 域名

由 `scripts/_env.sh` 中的 `mcp_url()` 函数统一定义（prod 后缀 `prod.hrainative.woa.com`，dev 后缀 `app.hrainative.woa.com`）。生产域名固定指向容器 9999 端口，无需调用 `register-mcp-svr`。

> 故障排查详见 `troubleshooting.md` §8-§10。
