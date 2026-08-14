# 部署 Provider：手动模式

> 当没有自动部署工具（如 page-deliver）时使用。输出清晰的部署指引，由用户或运维完成容器部署。

---

## 部署指引

### 1. 将项目部署到容器

将以下文件部署到目标容器中：
- 应用代码（按项目自身方式）
- `mcp_server/` 目录（包含 MCP Bridge）

### 2. 在容器内启动 MCP Bridge

```bash
# 进入 mcp_server 目录
cd /path/to/app/mcp_server

# 安装 Python 依赖
pip3 install -r requirements.txt

# 启动 Bridge（端口自动探测，写入 .bridge-port）
APP_BASE_URL=http://127.0.0.1:{APP_PORT} \
BRIDGE_HOST=0.0.0.0 \
BRIDGE_NAME={projectId}-bridge \
pm2 start mcp_bridge.py --name {projectId}-bridge --interpreter python3

# 查看端口
cat .bridge-port
```

### 3. 确认 Bridge 可访问

```bash
# 从 agent-server 所在机器测试
curl -s -X POST http://{容器IP}:{BRIDGE_PORT}/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
# 应返回 tools 列表
```

### 4. 提供 MCP URL 完成注册

部署和验证完成后，告知如下信息：

> ✅ Bridge 部署完成。
> MCP URL：`http://{容器IP}:{BRIDGE_PORT}/mcp`
>
> 我将用此 URL 注册 Agent 到 agent-server。

然后回到主流程 `phases/4-register.md` 完成注册。
