---
name: auth_permission
description: "业务Skill执行前的权限检查服务，这是系统安全基础步骤。如果业务Skill中添加了前置条件指向这里，必须在执行其他业务 Skill 前先调用本Skill，做认证和鉴权操作。同时，auth_permission也支持重置登录态操作（清除当前Agent身份）。"
---

# auth_permission，认证+权限检测

> ⚠️ **执行前必须先识别用户当前操作系统**，并按下表加载对应文件作为本 Skill 的真正执行说明。**只读其一，不要把两个文件都跑一遍。**

| 操作系统 | 应加载的文件 | 说明 |
| --- | --- | --- |
| macOS / Linux（bash / zsh） | [`SKILL_unix.md`](./SKILL_unix.md) | 使用 POSIX 前缀内联环境变量、`curl` + `chmod` 安装 authcli |
| Windows（PowerShell） | [`SKILL_windows.md`](./SKILL_windows.md) | 使用 `$env:KEY=...` 设置环境变量、`Invoke-WebRequest` 安装 authcli.exe |

## 路由判定步骤
1. 通过 shell 探测当前操作系统（任选其一）：
   - 已知是 PowerShell（`$PSVersionTable` 可用、提示符以 `PS` 开头、命令分隔符为 `;`）→ **Windows**
   - 已知是 bash / zsh（`uname -s` 可用）→ **macOS / Linux**
2. 按上表打开对应的 `SKILL_*.md`，**严格遵循其中的安装、鉴权、重置、安全规范**执行。
3. 两个文件的字段、参数、动态参数（ResourceID / CredentialId）、安全机制完全一致，差别**仅在于 shell 语法与安装脚本**。
