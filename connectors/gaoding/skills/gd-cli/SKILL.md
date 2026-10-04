---
name: gd-cli
description: Use when creating images, videos or text with GD CLI, operating the
  focused Gaoding editor, or managing Gaoding DAM assets.
display_name: 稿定AI
display_name_en: Gaoding AI
description_zh: 连接稿定AI创作、素材、模型与编辑器能力，用自然语言完成设计工作。
description_en: Connect to Gaoding AI creative, asset, model and editor
  capabilities through natural language.
version: 1.5.6
author: 稿定AI
---

# GD CLI

## 按需发现当前能力

- 首次使用时确认 `gd-cli --version`；不确定入口时读 `gd-cli --help`，沿相关命令组选择命令，执行前读其 `--help`。本 Skill 的示例不代表完整能力清单。
- 结构化输入先读取命令公开支持的 `--schema`；模型、参数选项、价格与资源 ID 由对应目录或详情查询取得，不从旧示例猜值。发现不支持或查询失败时说明缺口，不静默替换用户明确约束。
- 同一会话可复用同一路径/版本的 help 和静态 Schema；CLI 变化后重查。动态信息在本次任务选能力或报价时查询，身份/组织变化或明确不匹配时刷新相关结果，不全量扫描无关目录。
- 发现只说明当前实装 CLI 的能力，不等于升级，也不授予生成、写入或安装权限；未知结果的恢复按错误处理指引执行。

## 读取任务指引

按用户目标只读取对应参考：

- 按业务意图选择 Agent / Tool 创作路由、发现 Model 并生成图片、视频或文本：[创作](references/creation.md)
- 操作当前 AI+ Editor 作品：[编辑器](references/editor.md)
- 发现资源库、文件夹与标签，查询、上传、下载或管理 DAM 资源：[素材管理](references/dam.md)
- 登录或选择组织：[登录与组织](references/auth-org.md)
- 处理输出、警告、失败、中断或找回丢失结果：[错误处理](references/errors.md)
- 更新 CLI 与随包 Agent Skill：[更新](references/update.md)
