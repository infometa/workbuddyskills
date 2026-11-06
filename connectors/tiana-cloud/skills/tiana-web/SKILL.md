---
name: tiana-web
description: 使用 Tiana 创建、修改、预览和发布 Web 应用。用户要求制作账单、笔记、日历或其他 Web app 时使用；根据实时模板目录和需求决定采用模板或直接开发，并连接 SQLite 和 Git。
license: Apache-2.0
metadata:
  author: Tiana Cloud
  version: "1.0.5"
  parent: tiana
  source: https://github.com/tianacloud/agent-skills/tree/main/skills/tiana-web
display_name: "Tiana Web"
display_name_en: "Tiana Web"
description_zh: "按实时目录采用模板或直接开发，创建和发布 Web 应用。"
description_en: "Build and publish Web apps using the current template catalog or direct development."
version: "1.0.5"
author: "Tiana Cloud"
---

# Tiana Web

安装、登录和通用实例管理见 [Tiana](../tiana/SKILL.md)，SQL 与连接见 [Tiana SQLite](../tiana-sqlite/SKILL.md)，源码见 [Tiana Git](../tiana-git/SKILL.md)。

## 每个会话一次的更新检查

四个 Tiana 技能共享当前会话的更新检查记录。CLI 已满足最低版本要求且本会话尚未尝试检查时，执行 `tiana version check --skills-version 1.0.5 --json`，使用实际加载的 metadata.version。调用前在会话上下文中记为已尝试；后续轮次、重复加载或切换技能均复用该记录，检查失败也不自动重试。上下文压缩或任务交接时保留记录，新会话重新检查。

仅在 `should_notify=true` 时简短提醒并询问是否升级；用户选择稍后或检查不可用时继续原任务。CLI 仍管理检查缓存和共同的 24 小时提醒额度。升级及重载见[开始使用](../tiana/references/getting-started.md#更新)。

## 每次任务必须查询当前模板目录

**每次创建、修改或发布 Web 应用，都必须实际执行 `tiana web list-template --json`。同一会话之前查过、记得某个模板、用户未提模板，都不能代替这次调用。** 有 `data.next_cursor` 时，以 `--after CURSOR` 继续查询本次需求需要的目录页。检查命令实际成功；当前目录不可用时说明结果并按通用方式继续，不能从旧列表选包。

用户只需描述应用。根据本次返回的 `name`、`description` 判断核心功能、数据模型与可定制范围：合适的模板可加速制作，局部差异在工程中修改；没有合适模板就直接开发。已有工程继续修改自己的工程。以需求为依据决定，不要求用户选择模板，也不硬编码模板名称或模板版本。

## 创建、初始化和发布

1. 阅读 [Web 开发与发布](references/csr-apps.md)及 [JavaScript 连接](../tiana-sqlite/references/js-sdk.md)。新应用默认为本次需求创建所需的 SQLite 和 Git 实例，并等待就绪、保存实际 ID；仅在用户明确指定已有实例时核实后复用。修改已有工程时沿用其已确认绑定。实例名称按当前应用命名，模板变量使用 CLI 回执中的 ID。先确定最终入口路径；创建 Web 时用 `--entry` 固定入口，配置实际数据库和 Git 绑定，并等就绪。Web ID 取 `web create` 返回的 `data.id`。
2. 采用模板时，执行 `tiana web init-template NAME --dir PROJECT_DIR --json`。PROJECT_DIR 是用户项目的不存在目录，位于技能安装目录之外。CLI 下载并原样解压；按 [模板初始化](references/template-init.md)读取工程根部 `metadata.json`，由 Agent 完成全部变量替换及 SQLite 数据初始化。
3. 直接开发时，使用 [固定 index.html](references/index.html)、哈希路由、支持动态账号鉴权的 SDK，按实际数据库结构编写应用及构建清单。
4. **模板和直接开发都由 Agent 处理数据库初始化。** 模板先执行已配置且存在的 schema，再执行已配置且存在的 seeds；两项独立跳过，SQL 失败先核对结果并停止后续发布。
5. 构建前准备应用图标：用户明确提供图片时使用它，否则复用源码已有 `icon.png`（包括模板的 `public/icon.png`）；源码缺图时由 Agent 按标题自动生成汉字／字母加固定配色的真实 PNG，保存到源码，并确保产物根目录有 `icon.png`。查看图片并核验干净构建，细节见[应用图标](references/csr-apps.md#应用图标)。
6. 按用户需求完成交互和定制，安装依赖并从确定源码提交构建。按 [源码版本流程](../tiana-git/references/source-releases.md)完成源码同步，用 `web publish` 发布当前归档，再用 `web status --publish-id` 核对。除非用户仅要求本地开发，交付实际托管地址、资源 ID 和对应源码提交；未验证的阶段如实说明。

## 文件上传、预览与下载

应用需要文件存储时，阅读[WebApp 文件存储](references/files.md)，核对配套候选环境后使用平台提供的 `context.files`。先创建 WebApp 获得 ID 即可本地预览，无需先发布；文件路径相对于该 WebApp 的目录。
