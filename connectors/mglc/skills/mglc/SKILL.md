---
name: mglc
description: 灵创 AI 创作 - 生成图片、视频、剧本、分镜，管理SD 合规素材库 和项目
version: "1.0.0"
author: "灵创 AI"
---

# 灵创 AI 创作 Skill

本 Skill 提供通过 `mglc` CLI 操作灵创 AI 创作平台的完整能力。

## 安装

### 快速安装（可直接升级到最新版本）

```bash
curl -fsSL https://aigc-assets.mgtv.com/mglc/install.sh | bash
```

安装指定版本：

```bash
curl -fsSL https://aigc-assets.mgtv.com/mglc/install.sh | bash -s -- 0.1.13
```

> 安装脚本默认安装到 `~/.local/bin`，不需要 `sudo`。若该目录不在 `PATH`，脚本会输出需要添加的环境变量。

### Windows

在 PowerShell 中执行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -Command "iwr https://aigc-assets.mgtv.com/mglc/install.ps1 -UseBasicParsing | iex"
```

安装器会将 `mglc.exe` 安装到 `%LOCALAPPDATA%\Programs\mglc\bin`，并添加到用户 `PATH`。安装完成后请打开新的终端。

### 从旧版升级

如果旧版本安装在系统目录（如 `/usr/local/bin`），先清理旧二进制：

```bash
command -v mglc
sudo rm -f /usr/local/bin/mglc
sudo rm -f /usr/local/share/man/man1/mglc*.1
```

然后重新执行快速安装命令即可。

### 卸载

```bash
curl -fsSL https://aigc-assets.mgtv.com/mglc/uninstall.sh | bash
```

Windows PowerShell：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -Command "iwr https://aigc-assets.mgtv.com/mglc/uninstall.ps1 -UseBasicParsing | iex"
```

该命令会删除 `mglc.exe`、用户 `PATH` 中的安装目录，以及 `%USERPROFILE%\.mglc` 配置目录。

## 认证说明

### WorkBuddy 首次授权

在 WorkBuddy 中使用时，先创建设备授权：

```bash
mglc auth --source workbuddy
```

该命令的 stdout 仅输出授权 URL。用户在浏览器确认后，任意需要认证的 `mglc` 业务命令（包括 `mglc status`）都会自动兑换待授权设备码、保存 Bearer Token，并继续执行原命令。授权仍在等待确认时，返回未登录状态；无需在业务命令前额外轮询 `status`。

### AK/SK 备用登录

非 WorkBuddy 环境可配置 Access Key 和 Secret Key：

```bash
mglc login --access-key YOUR_AK --secret-key YOUR_SK
```

- **获取凭证**：联系企业管理员申请灵创平台 AK/SK
- **有效期**：长期有效，可随时更换
- **存储位置**：默认保存在 `~/.mglc/` 目录

### 通过环境变量配置

也可以通过环境变量配置凭证（优先级高于本地存储）：

```bash
export MGLC_ACCESS_KEY=your_ak
export MGLC_SECRET_KEY=your_sk
```

### 检查登录状态

```bash
mglc status
```

如果返回错误码 `10002`，表示未登录或浏览器授权尚未确认；需要完成浏览器授权或重新执行认证。

### 退出登录

```bash
mglc logout
```

## 全局命令

### mglc help - 查看帮助

```bash
# 全局帮助
mglc help

# 查看子命令帮助
mglc image help
mglc video help
mglc project help
```

### mglc version - 查看版本

```bash
mglc version
```

## 输出格式

所有命令默认输出 JSON 格式：

```json
{
  "code": 0,
  "data": { ... },
  "msg": "success"
}
```

## 错误码说明

| 错误码 | 含义 | 解决方案 |
|--------|------|----------|
| 0 / 200 | 成功 | - |
| 10001 | 参数错误 | 检查命令参数是否正确 |
| 10002 | 未登录或等待浏览器授权 | 完成 WorkBuddy 浏览器授权，或配置 AK/SK |
| 10003 | 无权限 | 联系管理员开通权限 |
| 10051 | 数据不存在 | 检查 ID 是否正确 |
| 10061 | 额度不足 | 联系管理员充值 |
| 10071 | 任务失败 | 检查参数或重试 |
| 10101 | 服务不可用 | 检查网络或稍后重试 |

## 子 Skill 模块

| Skill | 命令前缀 | 功能 |
|-------|----------|------|
| user | `mglc logout/user info` | 退出登录、用户信息查询 |
| model | `mglc model` | 模型列表、模型能力查询 |
| image | `mglc image` | 图片生成、图生图、图片超分 |
| video | `mglc video` | 视频生成、图生视频、状态查询 |
| audio | `mglc audio` | 音乐、配乐、配音生成和状态查询 |
| timbre | `mglc timbre` | 音色库查询、收藏、设计和克隆 |
| virtual-ip | `mglc virtual-ip` | SD 合规素材库资产管理（用于真实IP创作） |
| project | `mglc project/episode/script/storyboard/subject/session` | 项目、剧集、剧本、分镜、(角色/场景/道具)设定、会话管理 |

## 使用建议

1. **先授权**：在 WorkBuddy 中先执行 `mglc auth --source workbuddy` 并完成浏览器确认
2. **查模型**：用 `mglc model list` 查看可用模型
3. **从简单开始**：先用 `mglc image generate` 快速体验
4. **项目工作流**：项目 → 剧集 → 剧本 → 分镜 → AI 生成
5. **异步任务**：视频、图片、音频生成等异步任务用 `mglc task status` 查询, 状态码：0 已提交，1 运行中，2 成功，3 失败，4 已取消
6. **帮助**：当遇到问题时，使用 `-h` 或 `--help` 查看帮助
