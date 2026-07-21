---
name: hsk-cli
description: |
  HSK CLI 运维助手 — 内网穿透、文件托管、项目部署。
  触发词：公网访问、外网访问、暴露端口、上传文件、部署预览、内网穿透
---

# HSK CLI — 零配置公网预览

## 功能说明
提供零配置的内网穿透、文件托管和项目部署能力，支持 Windows/macOS/Linux 多平台。

## 安装

**前置要求**：Node.js >= 14

```bash
# 全局安装（推荐）
npm install -g @aweray/hsk-cli

# 或使用 npx 免安装运行
npx @aweray/hsk-cli <command>
```

首次运行时，CLI 会自动检测当前平台并下载对应的原生客户端二进制到 `~/.hsk/bin/`，无需手动配置。

**支持平台**：macOS (Intel/Apple Silicon)、Linux (amd64)、Windows (amd64)

如果用户环境中尚未安装 hsk-cli，先引导用户执行上述安装命令，再继续后续操作。

## 调用方式
- 所有操作通过 `hsk-cli` 命令行工具执行（使用 Bash 工具）
- 推荐追加 `--format json` 获取结构化输出，便于解析
- 可用 `--dry-run` 预览不执行

## 何时使用

✅ **应该使用**:
- 用户需要暴露本地服务到公网（内网穿透）
- 用户需要上传文件或目录获取公网链接（文件托管）
- 用户需要构建并部署前端项目（Build + Upload）
- 用户提到「公网访问」「外网访问」「暴露端口」「上传文件」

❌ **不应该使用**:
- 简单的文件系统操作（使用 bash 直接操作）
- 纯网络诊断（使用 curl/wget 等工具）
- 不依赖公网预览的本地开发任务

## 策略选择（严格优先级）

1. 用户要分享文件/目录 → `host`（多文件项目必须上传整个目录）
2. 用户要部署前端项目 → `deploy`（自动 build 后上传构建产物）
3. 用户要暴露 WebSocket/API/动态服务 → `tunnel`
4. 不确定时 → 先 `deploy`，失败再 `tunnel`

## 支持的命令

### 文件托管
```bash
# 上传单文件
hsk-cli host ./document.pdf --format json

# 上传目录（自动打包 zip）
hsk-cli host ./dist/ --format json

# 指定入口文件（目录无 index.html 时）
hsk-cli host ./dist/ --entry-file version.html --format json

# 更新已有资源
hsk-cli host ./dist/ --resource-id <id> --format json

# 复用已有资源
hsk-cli host ./dist/ --reuse --format json
```

### 构建并部署
```bash
# 自动 build 并上传
hsk-cli deploy --format json

# 跳过构建，直接上传现有目录
hsk-cli deploy --no-build --format json

# 更新已有资源
hsk-cli deploy --resource-id <id> --format json
```

### 内网穿透
```bash
# 前台模式（按 Ctrl+C 停止）
hsk-cli tunnel --ip 127.0.0.1 --port 9000 --format json

# 后台模式（CLI 立即退出，隧道持续运行）
hsk-cli tunnel --ip 127.0.0.1 --port 9000 --detach --format json

# 复用已有隧道
hsk-cli tunnel --ip 127.0.0.1 --port 9000 --reuse --format json
```

### 隧道管理
```bash
# 查看后台隧道
hsk-cli tunnel list

# 停止指定 PID
hsk-cli tunnel stop --pid <PID>

# 停止全部
hsk-cli tunnel stop --all
```

### 状态检测
```bash
# 检查资源状态（进程存活 + URL 可访问）
hsk-cli status --format json
```

### 系统命令
```bash
# 预下载客户端
hsk-cli download [--arch <arch>]

# 更新客户端
hsk-cli update [--arch <arch>] [--force]

# 显示平台信息
hsk-cli platform
```

## 沙盒环境规则

- 浏览器打不开 → 直接告诉用户链接，不要 `--open`
- 进程保活不了 → 前台运行，不要 `--detach`
- 网络不通 → 改用 `host`，不要重复 `tunnel`

检测方法：
- `echo $CI` — 非空表示沙盒/CI
- `[ -w "$HOME" ]` — 失败表示文件系统受限
- `[ -d "$HOME/.hsk" ]` — 不存在表示无法持久化

## 输出格式
结果以 JSON 格式输出（`--format json`），包含：
- `public_url`：公网访问链接
- `resource_id`：资源 ID（用于后续更新）
- `success`：操作是否成功
- `mode`：操作模式（create/update/reused）

## 错误码

| 错误码 | 场景 | 应对 |
|--------|------|------|
| `TIMEOUT` | 启动超时（30秒） | 检查本地服务是否监听、网络是否正常 |
| `BINARY_NOT_FOUND` | 客户端未下载 | 运行 `hsk-cli download` 或 `hsk-cli update` |
| `FILE_NOT_FOUND` | 文件不存在 | 提示用户检查路径 |
| `INVALID_PORT` | 端口无效 | 端口号 1-65535；macOS/Linux < 1024 需 root |
| `UPLOAD_FAILED` | 上传失败 | 检查网络、文件大小 |
| `PROCESS_EXIT` | 进程异常退出 | 检查本地服务、端口冲突 |
| `PERMISSION_DENIED` | 权限不足 | macOS 检查"本地网络"权限；端口 < 1024 需 sudo |
| `ENTRY_FILE_MISSING` | 目录无入口文件 | 提示使用 `--entry-file` |

## 注意事项

- 首次运行时自动下载对应平台的原生客户端二进制到 `~/.hsk/bin/`
- 多文件项目必须上传整个目录，不能只传单个 HTML 文件
- macOS 下隧道无法连接时检查「本地网络」权限
- 用户更新内容后，先用 `hsk-cli status` 检测链接是否有效，不要直接说"继续使用旧链接"
