---
name: tiana-git
description: 使用 Tiana Git 管理 Git 实例和原生仓库，关联项目远程地址、同步源码分支及应用版本。SQLite 数据库分支使用 tiana-sqlite；托管 Web 构建发布使用 tiana-web。
license: Apache-2.0
metadata:
  author: Tiana Cloud
  version: "1.0.5"
  parent: tiana
  source: https://github.com/tianacloud/agent-skills/tree/main/skills/tiana-git
display_name: "Tiana Git"
display_name_en: "Tiana Git"
description_zh: "用户 Git 实例、原生仓库与应用源码版本同步。"
description_en: "User Git instances, native repositories and application source versions."
version: "1.0.5"
author: "Tiana Cloud"
---

# Tiana Git

安装 CLI、浏览器登录和通用资源恢复见 [Tiana](../tiana/SKILL.md)。本技能操作用户自己的 Git 实例；使用原生 Git 和包内的 `git-remote-tiana`。

## 每个会话一次的更新检查

四个 Tiana 技能共享当前会话的更新检查记录。CLI 已满足最低版本要求且本会话尚未尝试检查时，执行 `tiana version check --skills-version 1.0.5 --json`，使用实际加载的 metadata.version。调用前在会话上下文中记为已尝试；后续轮次、重复加载或切换技能均复用该记录，检查失败也不自动重试。上下文压缩或任务交接时保留记录，新会话重新检查。

仅在 `should_notify=true` 时简短提醒并询问是否升级；用户选择稍后或检查不可用时继续原任务。CLI 仍管理检查缓存和共同的 24 小时提醒额度。升级及重载见[开始使用](../tiana/references/getting-started.md#更新)。

## 实例与仓库

1. 在实际命令环境核验 `git --version`、`tiana version` 和 `git-remote-tiana` 路径。Windows 阅读 [helper 排查](../tiana/references/windows-git-helper.md)。
2. 阅读 [CLI 命令](../tiana/references/cloud-cli.md)，复用已核实的 Git 实例；需要查找时 `tiana git list/show`，缺少才 `tiana git create NAME --wait`。等待就绪后保存完整实例 ID 和实际 Endpoint。
3. 根据返回 Endpoint 使用 `tiana://HOST[:PORT]/repo.git`。原生 Git 自动调用 helper，账号凭据由 CLI 管理；不把 Token 放入 remote URL。
4. 克隆、fetch、commit、branch 和 push 使用原生 Git。Git refs 与 SQLite 数据库分支是不同对象。保持已有 remote、跟踪设置及用户工作区；新远程名称冲突时先核对目标。

## 同步应用源码

阅读 [源码与版本](references/source-releases.md)，确认项目托管选择和实际推送范围。全新 Tiana 应用创建自己的 Tiana Git；已有外部仓库首次同步时确认用户选择。提交源码与锁文件，排除凭据，普通推送并核验远端对应版本引用。

Web 发布时从干净、确定的源码提交构建，给产物清单同时写实际 `git_instance_id` 和完整 `source_commit`；提交号只生成到忽略的构建目录。推送失败停止关联的 Web 发布，结果不明先读取远端状态。Web 构建和上传见 [Tiana Web](../tiana-web/SKILL.md)。
