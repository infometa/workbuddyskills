---
name: tiana
description: 使用 Tiana Cloud 管理实例、安装 CLI、登录和恢复账号会话。通用 Tiana 任务从此技能开始；Web 应用创建发布使用 tiana-web，数据库和分支使用 tiana-sqlite，Git 仓库和源码同步使用 tiana-git。
license: Apache-2.0
metadata:
  author: Tiana Cloud
  version: "1.0.5"
  source: https://github.com/tianacloud/agent-skills/tree/main/skills/tiana
display_name: "Tiana Cloud"
display_name_en: "Tiana Cloud"
description_zh: "Tiana 通用入口：CLI 安装、账号登录与实例管理。"
description_en: "Tiana CLI installation, account login and instance management."
version: "1.0.5"
author: "Tiana Cloud"
---

# Tiana Cloud

本技能使用 `@tianacloud/cli`，包内提供 `tiana` 和 `git-remote-tiana`。安装与登录阅读[开始使用](references/getting-started.md)；Windows 安装或命令找不到时阅读 [Windows CLI 安装](references/windows-install.md)和 [PATH 与 helper 排查](references/windows-git-helper.md)。在 Agent 实际执行命令的环境中操作。默认 online；用户在任务中明确指定环境时，按开始使用中的环境规则传给每次 CLI/Git 调用。

## 每个会话一次的更新检查

四个 Tiana 技能共享当前会话的更新检查记录。CLI 已满足最低版本要求且本会话尚未尝试检查时，执行 `tiana version check --skills-version 1.0.5 --json`，使用实际加载的 metadata.version。调用前在会话上下文中记为已尝试；后续轮次、重复加载或切换技能均复用该记录，检查失败也不自动重试。上下文压缩或任务交接时保留记录，新会话重新检查。

仅在 `should_notify=true` 时简短提醒并询问是否升级；用户选择稍后或检查不可用时继续原任务。CLI 仍管理检查缓存和共同的 24 小时提醒额度。升级及重载见[开始使用](references/getting-started.md#更新)。

## 选择工作流程

| 任务 | 技能 |
| --- | --- |
| 创建、修改、预览、发布 Web 应用 | [tiana-web](../tiana-web/SKILL.md) |
| SQLite 查询、连接、建表及数据库分支 | [tiana-sqlite](../tiana-sqlite/SKILL.md) |
| Git 实例、仓库、源码版本同步 | [tiana-git](../tiana-git/SKILL.md) |
| 登录、账号、额度、通用实例管理 | 本技能 |

组合请求中，安装完成后继续用户要求的任务。按需读取对应技能和直接链接的参考资料，跨技能文件按宿主返回的安装目录解析。

## 管理实例

阅读 [CLI 命令与恢复](references/cloud-cli.md)，通过 CLI 操作。

1. `tiana status` 检查账号和租户用量。需要登录时，按[开始使用](references/getting-started.md)展示浏览器授权链接，确认登录后继续。
2. 复用已核实的资源；需要查找时用 `tiana sqlite list/show` 或 `tiana git list/show`。名称有歧义时让用户选择，后续使用完整实例 ID。
3. 缺少资源才执行 `tiana sqlite create NAME --wait` 或 `tiana git create NAME --wait`。accepted 只表示受理，成功等待后才能连接。
4. 创建中断且保留待完成请求时，用相同产品、名称和参数恢复原请求；已经成功时用 show 核实原实例，不能通过重复创建修复连接。

## 凭据与结果

CLI 保存账号登录态。登录失败或凭据过期时复用原实例完成登录；不读取凭据文件、向命令手动注入 Token 或把密钥写入源码。资源、Endpoint、账号权限及结果不明的处理见[实例与凭据](references/instances-and-tokens.md)。以实际返回的状态和错误判断结果，不把未执行的操作报告为已完成。
