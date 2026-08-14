# 能力模块 · MCP Bridge

> **本文件是 MCP Bridge 能力的唯一 owner**，覆盖其全生命周期：**生成 → 部署 → 测试**。
> 主线各阶段只做编排，MCP 相关细节一律委派到本文件对应锚点：
>
> | 锚点 | 被调用阶段 | 职责 |
> |------|-----------|------|
> | [`#principles`](#principles-核心设计原则) | 全局 | Bridge 核心约束 |
> | [`#gen`](#gen-生成阶段-3) | §3 创建 | 渲染 `mcp_bridge.py`、按 appType 选工具 |
> | [`#deploy`](#deploy-部署阶段-4) | §4 注册 | 部署形态、注册域名 |
> | [`#test`](#test-测试阶段-5) | §5 验证 | 工具可调用性 + 权限预期测试 |
>
> 模板本体：`assets/templates/mcp_bridge.py.template`
> 生成脚本：`scripts/gen-bridge.sh` · 测试脚本：`scripts/test-mcp.sh`

---

## #principles 核心设计原则

MCP Bridge 是**反向代理 + 工具门面**。核心约束：

| 原则 | 含义 |
|------|------|
| **不持有数据** | Bridge 永无状态，所有业务数据通过 HTTP 反向调用用户应用获取。绝不 hardcode 数据到 Bridge。 |
| **真相源唯一** | 用户应用是数据的唯一真相源。Bridge 只是 transparent proxy。 |
| **标准化生成** | `mcp_bridge.py` 按模板生成，项目特有逻辑通过 `${PROJECT_TOOLS}` 注入。 |
| **call_api 通道** | 项目工具通过 `call_api` 从应用取数，不直连数据库。 |
| **透传身份** | Bridge 从入站请求头解析真实终端用户（`X-Staff-Name` / `X-Staff-Id`），并在 `call_api` 时透传给应用；**授权判断在应用侧完成**（见 `modules/authz.md`），Bridge 不做拦截。 |
| **兜底机制** | `list_endpoints` + `call_api` 保证 Agent 总能探索和调用所有 API。 |

### 部署形态（同容器独立进程，agent-server 直连）

| 层 | 实体 | 位置 | 如何访问 |
|---|---|---|---|
| Bridge | `mcp_bridge.py`（FastMCP 独立进程） | **应用容器内**，监听 `0.0.0.0:{BRIDGE_PORT}` | agent-server 通过 MCP 域名访问 |
| 应用 | 业务 API（Express/FastAPI/…） | 同容器 | 监听 `{APP_PORT}` |
| 大脑 | agent-server | 共享服务 | 通过 MCP 域名访问 Bridge |

```
agent-server ──▶ MCP 域名 /mcp ──▶ Python Bridge (0.0.0.0)
                                       └─call_api（透传 X-Staff-*）──▶ 127.0.0.1:{APP_PORT}（业务 API + 授权中间件）
```

> MCP 域名规则由 `scripts/_env.sh` 的 `mcp_url()` 唯一定义。

### 不要做的事

| ❌ 不要 | ✅ 应该 |
| --- | --- |
| 把业务数据 hardcode 到 mcp_bridge.py | bridge 永远反向 HTTP 调用用户应用 |
| 在 bridge 里直连数据库 | 让用户应用提供 API，bridge 调用 API |
| 在 bridge 里做鉴权拦截 | 透传 `X-Staff-*`，授权在应用侧（`modules/authz.md`） |
| 在 bridge 里跑定时任务调度循环 | 定时任务由 agent-server 原生注入，不经 Bridge |
| 在 mcp_bridge.py 之外创建扩展文件 | 所有工具统一写在 `${PROJECT_TOOLS}` 区域 |
| 让 Bridge 监听 `127.0.0.1` | 默认监听 `0.0.0.0`，agent-server 直连 |
| 把 secret 写进 mcp_bridge.py | 通过环境变量传入 |

---

## #gen 生成阶段（§3）

### 目录结构

```text
mcp_server/
├── mcp_bridge.py        # 主桥 + 项目工具（plugin 生成，重新 /agent-boost 会覆盖）
└── requirements.txt     # 标准依赖（mcp + httpx + uvicorn，gen-bridge.sh 自动复制）
```

> 所有项目特有工具通过 `${PROJECT_TOOLS}` 占位符注入到 mcp_bridge.py 中，
> 与通用工具（`list_endpoints` / `call_api_tool` / `check_app_health`）在同一文件内。
> 重新 /agent-boost 会覆盖整个 mcp_bridge.py，如需保留手动添加的工具请提前备份。

### 占位符与渲染

模板 `assets/templates/mcp_bridge.py.template` 含 `${...}` 占位符，由 `scripts/gen-bridge.sh` 做纯文本替换（避免 `python3 -c` 转义地狱）：

| 占位符 | 来源 | 示例 |
|--------|------|------|
| `${PROJECT_NAME}` | §1 分析推断 | `employee-dashboard` |
| `${PROJECT_ID}` | §1 分析或 `.deploy-state.json` | `employee-dashboard-20260608` |
| `${APP_PORT}` | §1 分析（`backend.port`） | `3456` |
| `${BRIDGE_PORT}` | §3 起始探测端口 | `8932` |
| `${KNOWN_ENDPOINTS_JSON}` | §1 分析（`apis`）+ §2 授权清单（`requiredRole`），合成 Python 列表字面量 | `[{"method":"GET","path":"/api/x","requiredRole":"user"}]` |
| `${PROJECT_TOOLS}` | §1 分析 + §3 模型生成 | `@mcp.tool()\ndef query_dashboard(...)` |

**渲染调用**（§3 中执行）：
```bash
export BRIDGE_PORT=${BRIDGE_PORT:-8932}
PROJECT_NAME="{projectName}" \
PROJECT_ID="{projectId}" \
APP_PORT="{appPort}" \
BRIDGE_PORT="${BRIDGE_PORT}" \
KNOWN_ENDPOINTS_JSON='<§1 apis 合并 §2 requiredRole 后的 JSON 数组>' \
PROJECT_TOOLS='<按 appType 选取的项目工具代码，static 传 "# no project-specific tools">' \
bash ${SKILL_DIR}/scripts/gen-bridge.sh "{projectDir}/mcp_server"
# 渲染后自动执行 py_compile 语法检查，并复制 requirements.txt
```

> **KNOWN_ENDPOINTS 携带 `requiredRole`**：授权清单确认后（`modules/authz.md#confirm`），
> 每个端点的 `requiredRole` 合入 KNOWN_ENDPOINTS，`list_endpoints` 会把它透出给 LLM，
> 便于 Agent 调用前预判权限（真正的拦截仍在应用侧中间件）。无授权清单时该字段省略。

### 模板结构概览

| 区块 | 作用 |
|------|------|
| `_find_free_port()` | 从 `BRIDGE_PORT` 起探测空闲端口，写入 `.bridge-port` |
| 配置区 | `APP_BASE_URL` / `BRIDGE_HOST` / `BRIDGE_PORT` / `BRIDGE_NAME`，均支持环境变量覆盖 |
| `KNOWN_ENDPOINTS` | §1 分析结果（含 §2 `requiredRole`）注入，`list_endpoints` 返回此列表 |
| `_resolve_caller()` | 从入站 MCP 请求头解析真实终端用户身份（`X-Staff-Name` / `X-Staff-Id`） |
| `call_api()` | 通用反向调用：拼接 URL + 透传 `X-Staff-*` 身份头 + httpx 请求 |
| `list_endpoints` / `call_api_tool` / `check_app_health` | 三个必备 MCP 工具 |
| `${PROJECT_TOOLS}` | 项目特有工具（按 appType 选取 + 定制工具），通过 `call_api` 转发 |
| `_FixHostMiddleware` | ASGI 中间件，绕过 FastMCP TrustedHost 校验，支持跨机器访问 |
| `uvicorn.run()` | 监听 `0.0.0.0:${BRIDGE_PORT}` |

### 项目工具（`${PROJECT_TOOLS}`）

工具通过 `@mcp.tool()` 装饰器注册，内部用 `call_api` 反向调用用户应用 API 取数：

```python
@mcp.tool()
def search_tools(keyword: str = "") -> str:
    """搜索工具/资源。keyword 为空时返回全部"""
    params = {"q": keyword} if keyword else {}
    return call_api("GET", "/api/tools", params=params)
```

模型可在阶段三根据项目分析结果生成定制工具，所有工具代码通过 `PROJECT_TOOLS` 环境变量传给 `gen-bridge.sh`。渲染后 `gen-bridge.sh` 执行 `py_compile` 语法检查。

**按 appType 选取的默认项目工具**（只生成 list_endpoints 中真实存在的 API 对应包装，每个包装一行 `call_api` 转发）：

<details>
<summary>appType: dashboard</summary>

```python
@mcp.tool()
def query_dashboard(dimension: str = "all") -> str:
    """查询数据看板。dimension 可选 all 或各业务维度（见 list_endpoints）"""
    return call_api("GET", "/api/dashboard", params={"dimension": dimension})
```
</details>

<details>
<summary>appType: crud</summary>

```python
@mcp.tool()
def list_items(resource: str, limit: int = 50, offset: int = 0, **filters) -> str:
    """通用列表查询。resource 为资源名（如 items/users），filters 转为 query 参数"""
    return call_api("GET", f"/api/{resource}", params={"limit": limit, "offset": offset, **filters})

@mcp.tool()
def get_item(resource: str, id: str) -> str:
    """通用详情查询"""
    return call_api("GET", f"/api/{resource}/{id}")

@mcp.tool()
def create_item(resource: str, data: dict) -> str:
    """通用创建（写操作前请用户确认）"""
    return call_api("POST", f"/api/{resource}", body=data)

@mcp.tool()
def update_item(resource: str, id: str, data: dict) -> str:
    """通用更新"""
    return call_api("PUT", f"/api/{resource}/{id}", body=data)

@mcp.tool()
def delete_item(resource: str, id: str) -> str:
    """通用删除（高危：调用前必须用户确认）"""
    return call_api("DELETE", f"/api/{resource}/{id}")
```
</details>

<details>
<summary>appType: api-readonly</summary>

```python
@mcp.tool()
def query_api(endpoint: str, **filters) -> str:
    """查询某个只读 API 端点。endpoint 为 list_endpoints 返回的路径"""
    return call_api("GET", endpoint, params=filters if filters else None)
```
</details>

<details>
<summary>appType: static</summary>

仅 `call_api_tool` + `check_app_health`，不生成额外包装。
</details>

### KNOWN_ENDPOINTS 写入格式

```json
[
  { "method": "GET", "path": "/api/dashboard", "summary": "查询员工数据看板",
    "requiredRole": "user",
    "params": [{"name": "dimension", "in": "query", "type": "string", "enum": ["all","stats","dept"]}] },
  { "method": "POST", "path": "/api/config", "summary": "更新配置", "requiredRole": "admin" },
  { "method": "GET", "path": "/api/health", "summary": "健康检查", "requiredRole": "public" }
]
```

### requirements.txt

由 `gen-bridge.sh` 从 `assets/templates/requirements.txt` 自动复制，无需手动创建。内容：

```text
mcp>=1.0.0
httpx>=0.27.0
uvicorn>=0.30.0
```

> **容器内 Python 依赖预装（必需）**：若容器无 `pip3`，需先安装 `python3-pip`，再 `pip3 install -r requirements.txt`。
> agent-boost 部署流程（`deploy/anydev.md`）会通过 `anydev remote-exec` 自动安装并启动 Bridge。
> 若 PM2 日志显示 `ModuleNotFoundError: No module named 'httpx'`，说明容器缺少依赖，手动执行上述命令。
> Bridge 本身不直连数据库 —— 通过 `call_api` 反向调用应用 API 取数。

---

## #deploy 部署阶段（§4）

Bridge 部署是 `deploy/` provider 的责任（`deploy/anydev.md` 或 `deploy/manual.md`），依次完成：
1. 部署应用（`mcp_server/` 随应用打包上传）
2. 部署 Bridge（装依赖 → PM2 启动 → 读实际端口 → **连通性检查 tools/list**）
3. 注册 MCP 服务域名（`register-mcp-svr` 关联域名 → 容器 IP:port）

> 容器内由 PM2 守护（与应用同生命周期）：
> ```bash
> pm2 start mcp_bridge.py --name "${PROJECT_ID}-bridge" --interpreter python3 \
>   --cwd /data/services/apps/${PROJECT_ID}/mcp_server
> ```

**MCP 注册地址**：agent-server 注册时 `mcpServers.url` 填域名（由 `_env.sh` 的 `mcp_url()` 生成）。
Bridge 监听 `0.0.0.0:{BRIDGE_PORT}`，实际端口由 `_find_free_port()` 探测并写入 `.bridge-port`，`register-mcp-svr` 注册时读取该文件。**无需在用户应用中加 `/mcp` 反代**。

> §4 部署阶段的 `tools/list` 只验证**连通性**（Bridge 能否被访问、能否列出工具）。
> **工具能否成功调用、权限是否符合预期**属于质量门禁，见 [`#test`](#test-测试阶段-5)。

---

## #test 测试阶段（§5）

> **目标**：连通性之外，验证每个工具能否**成功调用**、权限是否**符合预期**。MCP 工具质量直接决定 Agent 体验。
> **执行者**：`scripts/test-mcp.sh`（模型只传环境变量，不写复杂 shell）。
> **输入**：Bridge 可达地址 + 授权清单（`modules/authz.md#confirm` 产出，仅 authz 启用时）+ 测试身份。
> **输出**：核心报告 `.agent/mcp-test-report.json`（L1+L2+L3 合并；L3 仅 authz 启用时存在）。
>
> **核心层 vs 能力层**（见 `modules/registry.md` §7）：
> - **核心 L1+L2**：本脚本执行，所有应用必跑，报告在 `.agent/mcp-test-report.json`
> - **能力 L3**：authz 的权限测试当前复用本脚本 L3（通过 `AUTHZ_MANIFEST` 触发）；后续新增能力各自独立 test 脚本，报告在 `.agent/{name}/test-report.json`

### 三层测试

| 层 | 测什么 | 方法 | 破坏性防护 | 归属 |
|----|--------|------|-----------|------|
| **L1 连通** | tools/list 有工具 | JSON-RPC `tools/list` | 无副作用 | 核心 |
| **L2 可调用** | 每个**只读**工具能否成功 tools/call | 最小/样例参数调用，记录成功率 + 耗时 + 错误摘要 | 只测 GET/只读工具；写工具跳过成功路径 | 核心 |
| **L3 权限** | 权限是否符合预期 | 对受保护端点：用 **non-admin 身份**（合成假名）→ 期望被拒（403）；用 **admin 身份**（取自名单/DB 样例）→ 期望放行 | 写接口仅测「拒绝路径」（403 不改数据）；成功路径仅对只读工具验证 | authz 能力 |

> **身份如何注入**：`test-mcp.sh` 向 Bridge 的 `/mcp` 发 JSON-RPC，请求头带 `X-Staff-Name` / `X-Staff-Id`，
> Bridge 透传到应用，应用侧授权中间件据此放行或拒绝——与真实链路完全一致。
> L3 的**权限预期用例**由 `modules/authz.md#test` 依据授权清单生成，喂给本脚本。
> **后续新增能力的专属工具测试**由各能力 `#test` 锚点负责（见 `modules/registry.md` §七）。

### 调用示例

```bash
MCP_LOCAL_URL="http://127.0.0.1:$(cat {mcpDir}/.bridge-port)/mcp" \
AUTHZ_MANIFEST="{projectDir}/.agent/authz/api-authz.json" \
REPORT_OUT="{projectDir}/.agent/mcp-test-report.json" \
ADMIN_STAFF="{admin 样例工号}" \
NONADMIN_STAFF="agent-boost-probe-nonadmin" \
bash ${SKILL_DIR}/scripts/test-mcp.sh
# 生产/远端：通过 deploy provider 的 remote-exec 在容器内执行同一脚本
```

### 结果判定与优化闭环

| 现象 | 归因 | 回到 |
|------|------|------|
| L1 失败 | Bridge 未起 / 端口不通 | `troubleshooting.md` §1/§3 |
| L2 工具报错 | `call_api` 路径错 / 应用缺该 API | §3 修 `PROJECT_TOOLS` 或补 API（`modules/authz.md#confirm` 的新增 API） |
| L3 该拦没拦 | 中间件未覆盖该路由 / 清单遗漏 | §3 `modules/authz.md#inject` 修中间件或清单 |
| L3 不该拦却拦了 | requiredRole 定得过严 / 名单解析失败 | §2 重确认清单 或 §3 检查 Role Resolver |

- 通过 → §5 输出「✅ MCP 质量门禁通过」，主线结束。
- 有失败 → 按上表定位并修复，重新跑 `test-mcp.sh`（幂等）。
