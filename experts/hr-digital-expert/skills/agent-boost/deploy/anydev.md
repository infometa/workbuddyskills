# 部署 Provider：AnyDev（page-deliver）

> 本文件是 agent-boost 的一个**可选部署后端**。依赖 page-deliver 插件提供 `full-deploy` 和 `remote-exec` 能力。
> 如果 page-deliver 不可用，降级到 `deploy/manual.md` 的指引模式。

---

## 前置检测

部署前确认 page-deliver 可用：

```bash
# 从 SKILL_DIR 推导 plugins 根目录（以 plugins/ 为锚点，不依赖目录深度）
PLUGINS_ROOT="${SKILL_DIR%%/plugins/*}/plugins"
PD="${PLUGINS_ROOT}/page-deliver/skills/page-deliver/bin/page-deliver.js"
PD_SKILL_DIR="${PLUGINS_ROOT}/page-deliver/skills/page-deliver"

if [ ! -f "$PD" ]; then
  echo "DEPLOY_PROVIDER=manual"
  echo "⚠️ page-deliver 不可用，降级为手动部署模式"
  exit 0
fi
echo "✅ page-deliver found: ${PD}"
```

---

## 1. 部署应用（仅部署应用代码）

```bash
echo '{"projectDir":"{projectDir}"}' \
  | node $PD anydev full-deploy --input -
# 返回 {envInsId, ip, port, pm2Name, appPath, ...}
```

> `full-deploy` 仅处理应用本身（打包/上传/PM2 启动），不碰 MCP Bridge。
> `mcp_server/` 目录会随 `full-deploy` 打包上传到容器 `{appPath}/mcp_server/`。

> 🔴 **强制续走**：full-deploy 完成后**禁止停止**。
> 必须紧接着执行「2. 部署 MCP Bridge」，然后回到 `phases/4-register.md` 完成注册。

---

## 2. 部署 MCP Bridge（通过 remote-exec 独立部署）

> 以下 5 步通过 `anydev remote-exec` 在容器内完成：清旧进程 → 装依赖 → 启动 Bridge → 读实际端口 → 健康检查。
> `remote-exec` 会自动从 `.deploy-state.json` 读取 `envInsId`，自动解析 any CLI 二进制（page-deliver 内部 `resolveInternalSkillDir()` 定位 `bin/anydev/any-linux`）。
> `remote-exec.sh` 只接受 `PD`、`PROJECT_DIR`、`CMD` 三个必填环境变量；`PD_SKILL_DIR` 为可选 hint（未设置时自动遍历目录树发现）。

```bash
# 读取容器 IP 和端口（full-deploy 已写入 .deploy-state.json）
IP=$(node -e "console.log(JSON.parse(require('fs').readFileSync('{projectDir}/.deploy-state.json','utf8')).ip || '')")
PORT=$(node -e "console.log(JSON.parse(require('fs').readFileSync('{projectDir}/.deploy-state.json','utf8')).port || '')")
BRIDGE_NAME="{projectId}-bridge"
MCP_DIR="/data/services/apps/{projectId}/mcp_server"

# 公共参数（后续每步复用）
export PD="$PD"
export PROJECT_DIR="{projectDir}"
export PD_SKILL_DIR="${PD_SKILL_DIR}"
export CMD   # 后续 CMD= 赋值自动导出给 remote-exec.sh

# Step 0: 清理旧 Bridge 进程
CMD="pm2 stop ${BRIDGE_NAME} 2>/dev/null || true; pm2 delete ${BRIDGE_NAME} 2>/dev/null || true; rm -f ${MCP_DIR}/.bridge-port; echo CLEANUP_OK"
bash ${SKILL_DIR}/scripts/remote-exec.sh --stdout
# 期望输出包含 CLEANUP_OK

# Step 1: 安装 Python 依赖
CMD="python3 --version 2>/dev/null || (yum install -y python3-pip -q 2>&1); pip3 install -q -r ${MCP_DIR}/requirements.txt 2>&1; echo DEPS_OK"
bash ${SKILL_DIR}/scripts/remote-exec.sh --stdout
# 期望输出包含 DEPS_OK，否则停止并报错

# Step 2: PM2 启动 Bridge（不设 BRIDGE_PORT，让 _find_free_port 自动探测）
CMD="cd ${MCP_DIR} && APP_BASE_URL=http://127.0.0.1:${PORT} BRIDGE_HOST=0.0.0.0 BRIDGE_NAME=${BRIDGE_NAME} pm2 start mcp_bridge.py --name ${BRIDGE_NAME} --interpreter python3 --cwd ${MCP_DIR} --update-env && sleep 3 && pm2 save && echo BRIDGE_OK"
bash ${SKILL_DIR}/scripts/remote-exec.sh --stdout
# 期望输出包含 BRIDGE_OK + pm2 状态 online

# Step 2.5: 读取 Bridge 实际端口
CMD="cat ${MCP_DIR}/.bridge-port 2>/dev/null || echo NO_PORT_FILE"
BRIDGE_PORT=$(bash ${SKILL_DIR}/scripts/remote-exec.sh --stdout | grep -oE '[0-9]+' | head -1)
echo "Bridge port: ${BRIDGE_PORT}"

# Step 3: Bridge 健康检查（tools/list）
# 注意：\$(cat ...) 中的 \$ 转义为字面 $，在容器侧执行
CMD="curl -s -X POST http://127.0.0.1:\$(cat ${MCP_DIR}/.bridge-port)/mcp -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' -d '{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"tools/list\"}'"
HEALTH_STDOUT=$(bash ${SKILL_DIR}/scripts/remote-exec.sh --stdout)
# 解析 MCP 响应中的 tools 数组（兼容 SSE data: {...} 和纯 JSON）
TOOL_COUNT=$(echo "$HEALTH_STDOUT" | python3 -c "
import sys, json
raw = sys.stdin.read()
line = next((l for l in raw.splitlines() if l.startswith('data:')), None)
payload = line[5:].strip() if line else raw.strip()
try:
    print(len(json.loads(payload).get('result',{}).get('tools',[])))
except Exception:
    print(0)
")
echo "Bridge tools count: $TOOL_COUNT"
```

> 此处 `tools/list` 仅验证**连通性**（L1）。工具可调用性（L2）与权限符合性（L3）在阶段五 `phases/5-verify.md`（`scripts/test-mcp.sh`）中验证。

> ⚠️ **关键要点**：
> - 所有 `remote-exec` 调用通过 `scripts/remote-exec.sh` 封装，**禁止手拼 JSON 字符串**（嵌套引号会导致 `BAD_INPUT: invalid JSON`）
> - `CMD` 中的 `\$(...)` 会转义为字面 `$(...)`，在容器侧执行（如动态读取 `.bridge-port`）
> - Step 2 设 `BRIDGE_HOST=0.0.0.0`，**不设 BRIDGE_PORT 环境变量**，让 `_find_free_port()` 自动探测
> - Step 3 的 `Accept` 头**必须同时含** `application/json, text/event-stream`（FastMCP 强制要求）
> - 上述 5 步逐一执行，任一步失败则停止并报错

---

## 3. 注册 MCP 服务域名（关联域名 → IP:port）

> 🔴 **必须步骤**：Bridge 部署完成后，需调用 page-deliver 的 `mcp register-mcp-svr` 命令，
> 将 `{projectId}-internal-mcp-service.app.hrainative.woa.com` 域名关联到容器的 IP:port。
> 这样 agent-server 才能通过域名访问 MCP Bridge，而非直连 IP:port。

```bash
# 从 boost-state.json 读取 staffName（agent owner，§0 MCP check_identity 获取）
STAFF_NAME=$(python3 -c "import json; print(json.load(open('{projectDir}/.agent/boost-state.json')).get('staffName',''))" 2>/dev/null || echo "")

echo "{\"projectId\":\"${PROJECT_ID}\",\"host\":\"${IP}\",\"port\":${BRIDGE_PORT},\"staffName\":\"${STAFF_NAME}\"}" \
  | node $PD mcp register-mcp-svr --input -
# 期望输出含 "registered": true
```

> 注册成功后，nginx 即可通过 `{projectId}-internal-mcp-service.app.hrainative.woa.com` 域名转发到容器的 `IP:BRIDGE_PORT`。
> MCP URL（用于 agent 注册）= `http://${PROJECT_ID}-internal-mcp-service.app.hrainative.woa.com/mcp`

完成后回到主流程 `phases/4-register.md` 进行注册：

```bash
# 传递给注册阶段
export IP="$IP"
export BRIDGE_PORT="$BRIDGE_PORT"
# MCP URL 使用域名（register-mcp-svr 已将域名关联到 IP:BRIDGE_PORT）
export MCP_URL="http://${PROJECT_ID}-internal-mcp-service.app.hrainative.woa.com/mcp"
echo "✅ 部署完成。IP=${IP} BRIDGE_PORT=${BRIDGE_PORT} MCP_URL=${MCP_URL}"
```
