---
name: awesun-skill
description: 向日葵（AweSun）远程控制 CLI 工具。提供设备列表管理、远程会话管理、远程桌面控制、远程命令执行、远程文件传输、端口转发、远程关机/重启/唤醒等功能。用户提到向日葵、AweSun、远程控制、远程连接、远程桌面、远程文件、远程截图、远程关机时必须使用此 skill。
version: "1.0.0"
author: "Oray"
---

# 向日葵远程控制

通过 `awesun-cli` 命令行工具管理向日葵远程控制设备，支持设备管理、远程桌面、命令执行、文件传输、端口转发等操作。

## 前置安装

首次使用需全局安装 CLI 工具：

```bash
npm install -g @aweray/awesun-cli
```

## 账号管理

必须先登录才能使用其他命令。

```bash
# 扫码登录（推荐，--url 返回登录 URL 而不是打开浏览器）
awesun-cli login --qrcode --url

# 用户名密码登录
awesun-cli login --user <username>

# 检查登录状态
awesun-cli login status

# 登出
awesun-cli logout

# 清除所有缓存凭证登出
awesun-cli logout --clean
```

## 工具能力

### 1. 设备管理工具

| 命令 | 描述 |
|------|------|
| `device ls` | 分页列出所有设备，返回设备基本信息（remote_id、设备名、在线状态等） |
| `device search <keyword>` | 根据关键词模糊搜索设备，支持设备名称模糊匹配 |
| `device info <remote-id>` | 查询指定设备的详细信息（设备状态、系统信息、网络信息等） |
| `device add` | 添加新设备到设备列表，需指定名称和描述 |
| `device update <remote-id>` | 更新设备的元数据信息（名称、描述等） |
| `device rm <remote-id>` | 从设备列表中移除指定设备 |
| `device grant` | 管理设备访问权限（添加/移除/批量授权） |
| `device shutdown <remote-id>` | 远程关闭指定设备 |
| `device restart <remote-id>` | 远程重启指定设备 |
| `device wakeup <remote-id>` | 远程唤醒指定设备（需设备支持网络唤醒） |

**典型使用流程：**

```bash
# 1. 搜索设备获取 remote_id
awesun-cli device search "办公室" --limit 10

# 2. 查看设备详情
awesun-cli device info 12345

# 3. 远程关机
awesun-cli device shutdown 12345
```

> `shutdown`/`restart` 不带密码会提示输入访问密码；加 `--username` 会提示输入系统密码。

### 2. 远程会话管理工具

| 命令 | 描述 |
|------|------|
| `session connect` | 发起与指定设备的远程会话连接。返回 session_id 用于后续操作 |
| `session disconnect <session-id>` | 断开指定的远程会话 |
| `session status <session-id>` | 查询远程会话的连接状态 |
| `session ls` | 查询当前所有活跃的远程会话列表 |
| `session screenshot <session-id>` | 对远程会话截图，保存到指定路径 |
| `session exec <session-id> <cmd>` | 在 cmd2(Windows) 或 ssh(Linux/Mac) 会话中执行命令 |

**连接类型说明（`--type` 参数）：**

| 类型 | 说明 |
|------|------|
| `desktop` | 远程桌面控制（可执行鼠标键盘操作） |
| `file` | 远程文件管理（浏览/上传/下载/删除等） |
| `ssh` | Linux/Mac 远程 SSH 终端 |
| `cmd` | Windows 远程命令行 |
| `forward` | 端口转发 |

**连接密码规则：**

- `--fastcode <CODE>`: 提示输入访问密码
- `--remote-id <ID>`: 默认提示输入访问密码
- `--remote-id <ID> --username <USER>`: 提示输入系统密码

**典型使用流程：**

```bash
# 1. 搜索设备
awesun-cli device search "办公室电脑" --limit 1
# 假设返回 remote_id: 12345

# 2. 建立远程桌面连接
awesun-cli session connect --type desktop --remote-id 12345
# 返回 session_id: abc123xyz

# 3. 查看活跃会话
awesun-cli session ls

# 4. 断开连接
awesun-cli session disconnect abc123xyz
```

### 3. 桌面控制工具

用于在远程桌面会话中执行自动化操作，坐标使用归一化值(0.0-1.0)。仅在 `type=desktop` 的会话中可用。

| 命令 | 描述 |
|------|------|
| `desktop mouse move` | 移动鼠标到指定归一化坐标，不进行点击 |
| `desktop mouse click` | 模拟鼠标点击（左键/右键/中键），支持双击 |
| `desktop mouse drag` | 模拟鼠标拖拽，从起点拖拽到终点 |
| `desktop mouse scroll` | 模拟鼠标滚轮，支持方向和次数 |
| `desktop type` | 在远程桌面中输入文本 |
| `desktop paste` | 将文本粘贴到远程桌面 |
| `desktop key combo` | 模拟组合键（如 Ctrl+Alt+Del） |
| `desktop key press` | 按下或释放按键序列 |

**典型使用流程（自动化操作）：**

```bash
# 1. 建立远程桌面连接获取 session_id
awesun-cli session connect --type desktop --remote-id 12345
# 返回 session_id: abc123xyz

# 2. 截图查看当前状态
awesun-cli session screenshot abc123xyz --output /tmp/screen.png

# 3. 根据截图识别坐标，执行操作
# 点击某个位置
awesun-cli desktop mouse click abc123xyz --x 0.5 --y 0.5 --button left

# 输入文本
awesun-cli desktop type abc123xyz "Hello World"

# 按回车
awesun-cli desktop key press abc123xyz --keys enter --press down
awesun-cli desktop key press abc123xyz --keys enter --press up

# 组合键 Ctrl+C
awesun-cli desktop key combo abc123xyz --keys ctrl,c
```

### 4. 远程文件管理工具

仅在 `type=file` 的会话中可用。

| 命令 | 描述 |
|------|------|
| `file ls` | 浏览远程设备文件目录，支持路径和关键词过滤 |
| `file mkdir` | 在远程设备上创建新文件夹 |
| `file rm` | 删除远程文件或文件夹（`-r` 递归删除） |
| `file mv` | 重命名/移动远程文件或文件夹 |
| `file transfer` | 创建文件传输任务，支持上传(up)和下载(down) |
| `file transfer status` | 查询文件传输任务的状态和进度 |
| `file transfer cancel` | 取消正在进行的文件传输任务 |

**典型使用流程（文件传输）：**

```bash
# 1. 建立文件会话
awesun-cli session connect --type file --remote-id 12345
# 返回 session_id: file_session_001

# 2. 浏览远程目录
awesun-cli file ls file_session_001 --path /home/user/documents

# 3. 下载文件
awesun-cli file transfer file_session_001 \
  --type down \
  --remote /home/user/documents/report.pdf \
  --local ~/Downloads/report.pdf
# 返回 transfer_id

# 4. 监控传输进度
awesun-cli file transfer status file_session_001 --transfer-id <transfer-id>

# 5. 如需取消传输
awesun-cli file transfer cancel file_session_001 --transfer-id <transfer-id>
```

**注意事项：**

- 文件操作仅在 `type=file` 的会话中可用
- 删除文件/文件夹前，先用 `file ls` 确认路径正确
- 传输任务创建后需定期查询状态直到完成或失败

### 5. 远程命令执行工具

| 命令 | 描述 |
|------|------|
| `session exec` | 在远程设备上执行命令。需先建立 `cmd`(Windows) 或 `ssh`(Linux/Mac) 会话 |

**典型使用流程：**

```bash
# 1. 建立 SSH 会话
awesun-cli session connect --type ssh --remote-id 12345
# 返回 session_id: ssh_session_001

# 2. 执行远程命令
awesun-cli session exec ssh_session_001 "ls -la /var/log"

# 3. 获取 SSH 连接地址（用于手动连接）
awesun-cli ssh address ssh_session_001
```

### 6. 端口转发工具

| 命令 | 描述 |
|------|------|
| `forward config` | 配置端口转发通道，将远程设备端口映射到本地 |

**典型使用流程：**

```bash
# 1. 建立端口转发会话
awesun-cli session connect --type forward --remote-id 12345
# 返回 session_id: forward_session_001

# 2. 配置端口转发（通过 channels JSON 配置）
awesun-cli forward config forward_session_001 --channels '{"local_port":18080,"remote_port":8080}'

# 现在可以通过 localhost:18080 访问远程设备的 8080 端口
```

---

## 完整场景示例

### 场景1：远程桌面自动化操作

```bash
# 1. 搜索设备
awesun-cli device search "办公室电脑" --limit 1
# 假设返回 remote_id: 12345

# 2. 建立远程桌面连接
awesun-cli session connect --type desktop --remote-id 12345
# 返回 session_id: desktop_session_001

# 3. 截图查看当前状态
awesun-cli session screenshot desktop_session_001 --output /tmp/screen.png

# 4. Read 工具读取截图内容，识别目标坐标

# 5. 执行一系列自动化操作
# 点击开始菜单 (左下角，归一化坐标)
awesun-cli desktop mouse click desktop_session_001 --x 0.01 --y 0.99 --button left

# 输入"记事本"搜索
awesun-cli desktop type desktop_session_001 "notepad" --delay 100

# 按回车打开
awesun-cli desktop key combo desktop_session_001 --keys enter

# 6. 完成后断开连接
awesun-cli session disconnect desktop_session_001
```

### 场景2：批量文件下载

```bash
# 1. 搜索设备
awesun-cli device search "服务器" --limit 1
# 假设返回 remote_id: 12345

# 2. 建立文件会话
awesun-cli session connect --type file --remote-id 12345
# 返回 session_id: file_session_001

# 3. 浏览远程日志目录
awesun-cli file ls file_session_001 --path /var/logs

# 4. 下载日志文件
awesun-cli file transfer file_session_001 \
  --type down \
  --remote /var/logs/app.log \
  --local ~/Downloads/app.log
# 返回 transfer_id: transfer_001

# 5. 监控传输状态直到完成
awesun-cli file transfer status file_session_001 --transfer-id transfer_001
```

### 场景3：远程诊断

```bash
# 1. 搜索设备并建立 SSH 会话
awesun-cli session connect --type ssh --remote-id 12345
# 返回 session_id: ssh_session_001

# 2. 执行诊断命令
awesun-cli session exec ssh_session_001 "df -h"
awesun-cli session exec ssh_session_001 "free -m"
awesun-cli session exec ssh_session_001 "top -b -n 1 | head -20"
awesun-cli session exec ssh_session_001 "systemctl status nginx"

# 3. 断开连接
awesun-cli session disconnect ssh_session_001
```

---

## 工具调用最佳实践

### 1. ID 依赖与上下文管理

- **信任上下文**：对话历史中已获取的 remote_id 或 session_id 视为有效，避免重复查询
- **链路完整性**：确保命令输出中的 ID 准确传递到后续命令，避免断链
- **异常重试**：仅当命令返回 ID 无效错误时，才重新执行查询流程

### 2. 会话建立准则

- **会话复用优先**：执行远程操作前，先检查上下文是否有有效 session_id
- **桌面类型限制**：仅在 `type=desktop` 的会话中使用 `desktop` 系列命令
- **文件类型限制**：仅在 `type=file` 的会话中使用 `file` 系列命令
- **命令执行限制**：`session exec` 仅在 `type=cmd` 或 `type=ssh` 的会话中可用

### 3. 截图策略

- 首次操作或界面变更后必须截图
- 连续操作且界面未变时禁止重复截图，基于上一次截图坐标直接执行
- 单次截图应尽可能识别出当前任务所需的所有目标坐标

### 4. 登录前置检查

- 所有命令执行前必须确认已登录（`awesun-cli login status`）
- 未登录时先引导用户扫码或用户名密码登录

## 全局选项

| 选项 | 说明 |
|------|------|
| `--output` / `-o` | 输出格式: `table`（默认）, `json`, `yaml`, `wide` |
| `--verbose` / `-v` | 详细日志模式，用于调试 |
| `--help` / `-h` | 显示命令帮助 |

## 环境信息

- **日志目录**: `~/awesun-cli/log/`
- **后台守护进程**: 需要时自动启动，可通过 `awesun-cli stop-daemon` 停止
- **清除缓存**: `awesun-cli config clean-cache`
- 输出结果解析推荐使用 `-o json` 格式

## 辅助参考

### 截图与桌面控制

执行桌面自动化操作需要先从截图中识别目标坐标，详细指南参见：

- `references/ui-locator.md`: 从截图中识别 UI 元素位置的视觉引导，输出归一化坐标
- `references/ui-patterns.md`: UI 元素特征对照表（按钮、输入框、图标、导航等识别要点）

### 坐标工具

```bash
# 像素坐标 → 归一化坐标
python3 scripts/coordinates.py norm <pixel_x> <pixel_y> <width> <height>

# 验证归一化坐标有效性
python3 scripts/coordinates.py validate <x> <y>
```
