# 常见问题排查

## 1. Agent 注册后 `loaded: false`

**根因**：Bridge 端口不通（PM2 未启动 / 端口未就绪）。

**修复**：
1. 确认 MCP URL 使用 `http://{projectId}-internal-mcp-service.app.hrainative.woa.com/mcp`（域名通过 `register-mcp-svr` 关联到容器 IP:port）
2. 检查容器内 PM2 状态：`pm2 list | grep bridge`

---

## 2. Agent 返回旧数据

**根因**：Agent Server 运行时缓存未刷新。

**说明**：注册接口（`POST /api/agent/register`）内部已内置 unload 旧实例 → upsert 配置 → load 新实例 → 清缓存 全流程，无需先 DELETE。正常情况下不会出现旧数据复用。

**排查**（若仍出现）：
1. 确认注册请求的 `mcpServers.url` 已更新为新地址
2. 检查 agent-server 日志中是否有 `unload` / `load` 记录
3. 手动触发 reload：`curl -s -X POST -H "X-Staff-Name: {staffName}" ${AGENT_SERVER_URL}/api/agent/{agentName}/reload`
4. 验证 loaded 字段：`curl -s -H "X-Staff-Name: {staffName}" ${AGENT_SERVER_URL}/api/agent/{agentName} | python3 -c "import sys,json; print(json.load(sys.stdin).get('loaded'))"`

---

## 3. 端口冲突：`address already in use`

**修复**：
```bash
lsof -i :{port} 2>/dev/null || ss -tlnp | grep {port}
BRIDGE_PORT={new-start-port} pm2 restart {projectId}-bridge --update-env
```

> `mcp_bridge.py` 已内置 `_find_free_port()` 自动探测，一般不会冲突。若仍有冲突，说明容器内 Bridge 进程过多。

---

## 4. `gen-bridge.sh` 报 `syntax check failed`

**根因**：`PROJECT_TOOLS` 环境变量中包含的 Python 代码有语法错误。

**修复**：查看错误行号，检查 `PROJECT_TOOLS` 代码片段的缩进和引号后重新渲染。

---

## 5. `remote-exec` 不可用（降级处理）

当 `page-deliver` 不可用或 `anydev` CLI 缺失时，流程自动降级为手动部署（`deploy/manual.md`）。若手动部署后仍有问题，参见 agent-server 管理面板日志。

---

## 6. Bridge 崩溃：依赖缺失

```bash
pip3 install -r requirements.txt
pm2 restart {projectId}-bridge
```

---

## 7. MCP 测试脚本参数错误

**根因**：`test-mcp.sh` 必填 `MCP_LOCAL_URL` 未传或 Bridge 未启动。

**修复**：
```bash
# 确认 Bridge 已启动且 .bridge-port 文件存在
cat {mcpDir}/.bridge-port
# 传正确的环境变量
MCP_LOCAL_URL="http://127.0.0.1:$(cat {mcpDir}/.bridge-port)/mcp" \
REPORT_OUT="{projectDir}/.agent/mcp-test-report.json" \
bash ${SKILL_DIR}/scripts/test-mcp.sh
```

---

## 8. 生产环境 Bridge 启动失败

```bash
pm2 logs {projectId}-bridge --lines 50
# 常见：依赖未安装 → pip3 install -r requirements.txt
# 常见：端口占用 → lsof -i :9999
```

## 9. 生产环境 Agent loaded=false

- 检查 Bridge 是否在 9999 端口运行：`curl -s http://127.0.0.1:9999/mcp -X POST -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'`
- 检查 prod 域名是否指向本容器 9999
- 查看 agent-server 日志：`https://agent-server.prod.hrainative.woa.com` 管理面板

## 10. 生产环境 Agent 注册失败（401 未认证）

- 确认 `boost-state.json` 中 `staffName` 非空
- 确认 `register-agent.sh` 请求中包含 `X-Staff-Name: ${STAFF_NAME}` header
- 确认 `AGENT_SERVER_URL` 指向生产域名（`*.prod.hrainative.woa.com`，触发 Gateway 信任）

---

## 11. 授权：该拦的没拦 / 不该拦却拦了

**根因与修复**（详见 `modules/authz.md`）：
- **该拦没拦**：授权中间件未匹配到该路由 → 检查 `.agent/authz/api-authz.json` 的 `apis[].path` 是否与真实路由一致（`:id`/`{id}` 占位）；确认中间件已在应用入口注册且在路由之前。
- **不该拦却拦了**：`requiredRole` 定得过严，或 Role Resolver 解析失败 → 检查清单该接口的 `requiredRole`；`source=db` 时确认连接可达、`keyColumn`/`roleColumn`/`adminValues` 正确。
- **DB 名单不生效**：Resolver 连接点识别有误 → 优先改用现成函数（`custom`），或兜底同步为 `static`（见 `modules/authz.md#inject` 三级兜底）。
- **全部被拒**：中间件加载清单失败会 fail-safe 拒绝受限访问 → 查应用日志 `[agent-authz]`，确认清单路径可达（`AGENT_AUTHZ_MANIFEST` 或默认 `.agent/authz/api-authz.json`）。

---

## 12. MCP 测试（§5）失败

**根因与修复**（详见 `modules/mcp.md#test`）：
- **L1 连通失败** → 见本文 §1/§3（Bridge 未起 / 端口不通）。
- **L2 工具调不通** → `call_api` 路径与应用真实 API 不符，或应用缺该 API → 回 §3 修 `PROJECT_TOOLS` 或补新增 API。
- **L3 权限不符** → 见本文 §11。
- **测试脚本报 unparseable response** → Bridge 返回非预期格式；确认 `Accept: application/json, text/event-stream` 且 Bridge 为 `stateless_http=True`。

---

## 13. Windows 环境问题

| 症状 | 根因 | 修复 |
|------|------|------|
| `bash: command not found` 或 `.sh` 语法错误 | 未安装 Git for Windows，在原生 CMD/PowerShell 中直接执行脚本 | `win-adapter.md` Step 2（自动下载安装 Git for Windows） |
| `python3: command not found` | Windows 上 Python 注册为 `python` 而非 `python3` | `win-adapter.md` Step 3（创建 `/usr/bin/python3` 包装） |
| 脚本报路径/转义错误 | 反斜杠 `\` 被 bash 当作转义字符 | 路径改用正斜杠 `C:/Users/...` 或 Git Bash 挂载路径 `/c/Users/...` |

> 所有 Windows 环境问题均由 `references/win-adapter.md` 在首次运行时自动适配。网络不通时需手动安装 [Git for Windows](https://git-scm.com/download/win) 后重启 IDE。

---

## 14. `remote-exec` 嵌套引号与复杂命令

**根因**：通过 `anydev remote-exec` 执行含 JSON 字面量、`$(...)` 子shell、多层引号的命令时，shell 引号与 JSON 转义相互冲突，导致 `BAD_INPUT: invalid JSON` 或 `exit code 1`。

> `scripts/remote-exec.sh` 已用 Python `json.dumps()` 处理 CMD 环境变量的 JSON 转义（L37-43），**单层引号和无 JSON 的命令不会出问题**。问题仅出在 CMD 内部含 JSON 字面量 + `$(...)` 子shell 的组合场景。

### 最佳实践：按命令复杂度分级处理

**Level 1 — 简单命令（无 JSON、无子shell）**：直接传 CMD
```bash
CMD="pm2 stop ${BRIDGE_NAME} 2>/dev/null || true; echo CLEANUP_OK"
bash ${SKILL_DIR}/scripts/remote-exec.sh --stdout
```

**Level 2 — 含 `$(...)` 子shell 但无 JSON**：用 `\$(...)` 转义为字面 `$`
```bash
# \$(cat ...) 在容器侧展开为 $(cat ...)
CMD="curl -s http://127.0.0.1:\$(cat ${MCP_DIR}/.bridge-port)/mcp"
bash ${SKILL_DIR}/scripts/remote-exec.sh --stdout
```

**Level 3 — 含 JSON 字面量 + 子shell（最易错）**：拆成"写脚本 → 执行脚本"两步
```bash
# Step A: 用 remote-exec 写一个 .sh 文件到容器（CMD 仅含 heredoc，无 JSON 嵌套）
CMD="cat > /tmp/_test_mcp.sh <<'SCRIPT'
#!/usr/bin/env bash
PORT=\$(cat ${MCP_DIR}/.bridge-port)
curl -s -X POST http://127.0.0.1:\${PORT}/mcp \\
  -H 'Content-Type: application/json' \\
  -H 'Accept: application/json, text/event-stream' \\
  -d '{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"tools/list\"}'
SCRIPT
echo SCRIPT_WRITTEN"
bash ${SKILL_DIR}/scripts/remote-exec.sh --stdout

# Step B: 执行该脚本
CMD="bash /tmp/_test_mcp.sh"
bash ${SKILL_DIR}/scripts/remote-exec.sh --stdout
```

> **原则**：CMD 越简单越好。当 CMD 内出现 ≥2 层引号嵌套或 JSON 字面量时，**必须**改用 Level 3 的"写脚本 → 执行脚本"模式。`deploy/anydev.md` §2 Step 3 的 curl+JSON 命令已按 Level 2 模式给出，若仍报错则升级为 Level 3。
