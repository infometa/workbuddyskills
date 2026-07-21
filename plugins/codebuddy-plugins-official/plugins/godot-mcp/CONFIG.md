# Godot MCP 环境配置说明

## 概述

Godot MCP 插件支持多环境配置，可以在开发环境和生产环境之间轻松切换。

> **注意**：本文档中的后端域名（`dev-godot-backend.example.com` / `godot-backend.example.com`）均为**占位示例**，请替换为你实际部署的后端服务地址，或联系插件作者获取。

## 环境域名

- **开发环境（本地）**: `http://dev-godot-backend.example.com`
- **生产环境**: `https://godot-backend.example.com`

## 配置文件说明

### 1. 环境变量文件

- **`.env.example`**: 环境变量模板文件（不包含敏感信息）
- **`.env.dev`**: 开发环境配置
- **`.env.prod`**: 生产环境配置

### 2. MCP 配置文件

- **`.mcp.json`**: 当前激活的 MCP 配置（由切换脚本自动生成）
- **`.mcp.dev.json`**: 开发环境 MCP 配置
- **`.mcp.prod.json`**: 生产环境 MCP 配置

## 环境变量说明

| 变量名 | 说明 | 示例值 |
|--------|------|--------|
| `GODOT_BACKEND_URL` | 后端服务地址 | `http://dev-godot-backend.example.com` |
| `GODOT_API_KEY` | API 密钥（由管理员分配） | 留空或填写实际密钥 |
| `GODOT_WS_PORT` | WebSocket 端口 | `9080` |
| `MCP_TRANSPORT` | MCP 传输方式 | `stdio` |
| `NODE_ENV` | 环境标识 | `development` 或 `production` |

## 快速开始

### 方式一：使用切换脚本（推荐）

#### Linux/macOS

```bash
# 切换到开发环境
./switch-env.sh dev

# 切换到生产环境
./switch-env.sh prod
```

#### Windows

```cmd
# 切换到开发环境
switch-env.bat dev

# 切换到生产环境
switch-env.bat prod
```

### 方式二：手动切换

```bash
# 切换到开发环境
cp .mcp.dev.json .mcp.json

# 切换到生产环境
cp .mcp.prod.json .mcp.json
```

## 使用流程

1. **首次配置**
   ```bash
   # 如果需要配置 API Key，编辑对应环境的配置文件
   vim .mcp.dev.json    # 或 .mcp.prod.json
   ```

2. **切换环境**
   ```bash
   # 使用切换脚本
   ./switch-env.sh prod
   ```

3. **重启 CodeBuddy/Claude Desktop**
   
   切换环境后，需要重启 CodeBuddy 或 Claude Desktop 使配置生效。

4. **验证配置**
   
   重启后，可以在 CodeBuddy/Claude Desktop 中测试连接是否正常。

## 配置示例

### 开发环境配置 (.mcp.dev.json)

```json
{
  "mcpServers": {
    "godot-mcp": {
      "command": "node",
      "args": ["${CODEBUDDY_PLUGIN_ROOT}/server/dist/index.js"],
      "env": {
        "MCP_TRANSPORT": "stdio",
        "GODOT_WS_PORT": "9080",
        "GODOT_BACKEND_URL": "http://dev-godot-backend.example.com",
        "GODOT_API_KEY": "",
        "NODE_ENV": "development"
      }
    }
  }
}
```

### 生产环境配置 (.mcp.prod.json)

```json
{
  "mcpServers": {
    "godot-mcp": {
      "command": "node",
      "args": ["${CODEBUDDY_PLUGIN_ROOT}/server/dist/index.js"],
      "env": {
        "MCP_TRANSPORT": "stdio",
        "GODOT_WS_PORT": "9080",
        "GODOT_BACKEND_URL": "https://godot-backend.example.com",
        "GODOT_API_KEY": "",
        "NODE_ENV": "production"
      }
    }
  }
}
```

## 注意事项

1. **安全性**
   - `.env.dev` 和 `.env.prod` 已添加到 `.gitignore`，不会被提交到版本控制
   - 如需配置 API Key，请妥善保管，不要泄露

2. **环境隔离**
   - 开发环境和生产环境使用不同的后端服务地址
   - 确保在开发环境测试无误后再切换到生产环境

3. **配置备份**
   - 切换脚本会自动备份当前配置到 `.mcp.json.backup`
   - 如遇问题可手动恢复：`cp .mcp.json.backup .mcp.json`

4. **重启应用**
   - 每次切换环境后必须重启 CodeBuddy/Claude Desktop
   - 否则旧的环境变量仍然生效

## 故障排查

### 问题：切换环境后仍然连接旧地址

**解决方案**：
1. 确认 `.mcp.json` 文件已更新
2. 完全关闭并重启 CodeBuddy/Claude Desktop
3. 检查是否有多个 CodeBuddy/Claude Desktop 进程在运行

### 问题：连接后端服务失败

**解决方案**：
1. 检查网络连接
2. 确认后端服务地址是否正确
3. 检查是否需要配置 API Key
4. 查看 CodeBuddy/Claude Desktop 日志

### 问题：找不到配置文件

**解决方案**：
1. 确保在项目根目录执行切换脚本
2. 检查 `.mcp.dev.json` 和 `.mcp.prod.json` 文件是否存在
3. 如不存在，可参考 `.env.example` 手动创建

## 相关文件

- [README.md](README.md) - 项目主文档
- [CLAUDE.md](CLAUDE.md) - Claude 使用指南
- [.env.example](.env.example) - 环境变量模板

---

**更新日期**: 2026-05-18
