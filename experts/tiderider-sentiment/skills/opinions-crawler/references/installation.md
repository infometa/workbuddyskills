# OpenCLI 安装与配置指南

## 环境要求

| 组件 | 最低版本 | 说明 |
|------|---------|------|
| Node.js | >= 20.0.0 | 运行环境和包管理器 |
| Chrome / Chromium | 最新稳定版 | 浏览器桥接 |
| 操作系统 | macOS / Windows / Linux | 全平台支持 |

检查 Node.js 版本：

```bash
node --version   # 应输出 v20.x.x 或更高
npm --version
```

如果没有安装 Node.js，推荐使用 nvm 管理：

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
nvm install 22
nvm use 22
```

## 步骤一：安装 OpenCLI CLI

```bash
npm install -g @jackwener/opencli
```

验证安装：

```bash
opencli --version
# 应输出版本号，如 1.5.5
```

## 步骤二：安装 Chrome 浏览器扩展

OpenCLI 通过 Chrome 扩展（Browser Bridge）与浏览器通信，扩展负责持有登录态并执行页面操作。

### 2.1 下载扩展

从 GitHub Releases 页面下载最新版本：

- 地址：https://github.com/jackwener/opencli/releases
- 下载 `opencli-extension-v{version}.zip`

或使用命令行下载：

```bash
# 获取最新版本号
LATEST=$(curl -s https://api.github.com/repos/jackwener/opencli/releases/latest | grep tag_name | cut -d '"' -f 4)
echo "Latest version: $LATEST"

# 下载扩展
curl -L -o /tmp/opencli-extension.zip \
  "https://github.com/jackwener/opencli/releases/download/${LATEST}/opencli-extension-${LATEST}.zip"

# 解压
unzip /tmp/opencli-extension.zip -d /tmp/opencli-extension
```

### 2.2 加载扩展

1. 打开 Chrome，地址栏输入 `chrome://extensions` 回车
2. 开启右上角的「开发者模式」开关
3. 点击「加载已解压的扩展程序」
4. 选择刚才解压后的文件夹（`/tmp/opencli-extension/`）
5. 确认扩展列表中出现了 OpenCLI Browser Bridge，且状态为已启用

### 2.3 （可选）开启远程调试

用于排查问题：

```
chrome://inspect/#remote-debugging
```

将 Remote Debugging 开关打开。

## 步骤三：验证安装

```bash
opencli doctor
```

期望输出：

```
[OK] Daemon: running on port 19825
[OK] Extension: connected (v1.x.x)
[OK] Connectivity: connected in 0.2s
```

如果 Daemon 未启动，`opencli doctor` 会自动启动 daemon 进程。

## 步骤四：登录目标网站

OpenCLI 直接复用 Chrome 的登录态，**不需要**在命令行中输入任何账号密码。

1. 在 Chrome 中打开目标网站（如 bilibili.com、x.com 等）
2. 正常完成登录
3. 确认登录成功后，即可在终端直接使用 `opencli <site>` 命令

### 关键原则

- **登录凭据永远不会离开浏览器** — 安全性由 Chrome 自身保证
- 浏览器命令分为两种数据策略：
  - `public`：走公开 API，不需要 Cookie
  - `cookie`：复用浏览器登录态抓取页面数据
  - `intercept`：拦截浏览器内 API 请求
- 如果命令返回空数据或权限错误，先确认目标网站已在 Chrome 中登录

## 首次运行

```bash
# 查看所有可用命令（无需浏览器）
opencli list

# 运行公开 API 命令（无需登录）
opencli hackernews top --limit 5

# 运行浏览器命令（需要 Chrome 已登录对应网站）
opencli bilibili hot --limit 5

# JSON 格式输出
opencli bilibili hot --limit 5 -f json
```

## 更新

```bash
# 更新 CLI
npm install -g @jackwener/opencli@latest

# 更新 Chrome 扩展：重新下载最新 zip 并覆盖加载
```

## 配置项

通过环境变量配置：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `OPENCLI_DAEMON_PORT` | 19825 | daemon 与扩展的通信端口 |
| `OPENCLI_WINDOW_FOCUSED` | false | 设为 1 时自动化窗口在前台 |
| `OPENCLI_BROWSER_CONNECT_TIMEOUT` | 30 | 浏览器连接超时（秒） |
| `OPENCLI_BROWSER_COMMAND_TIMEOUT` | 60 | 单个命令超时（秒） |
| `OPENCLI_VERBOSE` | false | 启用详细日志 |

## 常见问题

### Q: `opencli doctor` 显示 Extension 未连接

**原因**：Chrome 扩展未加载或 Chrome 未运行。

**解决**：
1. 确认 Chrome 已打开
2. 确认扩展已在 `chrome://extensions` 中启用
3. 尝试重新加载扩展（点击扩展卡片上的刷新按钮）
4. 重启 Chrome 后再次运行 `opencli doctor`

### Q: 命令返回空数据

**原因**：目标网站未在 Chrome 中登录，或登录态已过期。

**解决**：
1. 在 Chrome 中打开目标网站
2. 确认处于已登录状态
3. 刷新页面确认 Cookie 有效
4. 重新执行命令

### Q: `npm install -g` 权限错误 (EACCES)

**解决**（macOS/Linux）：

```bash
# 方案一：使用 nvm 管理 Node.js（推荐）
nvm install 22
nvm use 22

# 方案二：修改 npm 全局安装路径
mkdir ~/.npm-global
npm config set prefix '~/.npm-global'
echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.zshrc
source ~/.zshrc
```

### Q: 端口 19825 被占用

```bash
# 查看占用进程
lsof -i :19825

# 杀掉占用进程后重试
kill -9 <PID>
opencli doctor
```
