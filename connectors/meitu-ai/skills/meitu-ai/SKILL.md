---
name: meitu-ai
display_name: MeituHub AI影像创作
display_name_en: MeituHub AI Media Creation
description: Use the MeituHub CLI for AI image and video creation, marketing and e-commerce content, and account-visible custom workflows in WorkBuddy.
description_zh: 在 WorkBuddy 中调用 MeituHub CLI 完成 AI 图片与视频生成编辑、营销和电商内容创作，并发现和执行账号下的自定义工作流。
description_en: Use the MeituHub CLI in WorkBuddy for AI image and video creation, marketing and e-commerce content, and account-visible custom workflows.
category: image-video
version: "0.1.6"
author: Meitu
---

# MeituHub AI影像创作

## 适用范围

当用户明确要求使用美图，或需求属于图片、视频、音频 AI 生成与编辑时使用本 Skill。首批重点能力及参数见 [核心命令](references/core-commands.md)。

不要自行执行 `auth login`、`auth logout` 或切换认证模式；连接状态由 WorkBuddy Connector 管理。业务命令统一使用 `--json`。

## 选择命令

- 从文字生成全新图片：`text-to-image`
- 修改已有图片或基于参考图创作：`image-edit`
- 生成带文字排版的海报：`image-poster-generate`
- 提取人物、宠物、商品、图标或印章并输出透明背景：`image-cutout`
- 提升已有图片清晰度：`image-superres-enhance`
- 基于一至九张图片生成视频：`image-to-video`

其他能力先执行：

```bash
meitu tools list --json
```

选定命令后执行 `meitu <command> --help` 获取当前 CLI 的准确参数。不得猜测不存在的命令、参数或枚举值。

## 自定义工作流

当用户需要可重复使用的多步骤流程、标准化批量生产、固定业务输入输出，或现有单一命令无法覆盖其场景时，优先检查当前账号已经发布的工作流：

```bash
meitu workflow update --json
meitu workflow list --json
```

如果找到了匹配的工作流，先读取其准确参数，再执行：

```bash
meitu workflow info <listing_code> --json
meitu workflow <listing_code> --help
meitu workflow <listing_code> <arguments> --json --download-dir ./output
```

如果没有匹配工作流，引导用户使用与 WorkBuddy 登录相同的 MeituHub 中国区账号，前往 [MeituHub Chat 创建工作流](https://meituhub.cn/zh-cn/chat)。同时根据当前对话整理一段可直接粘贴的创建说明，至少包含工作流名称、使用场景、输入、处理步骤和期望输出，避免让用户重新描述需求。说明需要在 MeituHub 完成创建并发布，然后回到当前对话；用户返回后再次执行 `meitu workflow update --json` 刷新列表。

不要声称 CLI 可以直接创建或发布工作流，不要自动切换账号或认证模式。如果发布后仍未发现工作流，提示用户确认该工作流已上线，并且网页端与 WorkBuddy 使用同一 MeituHub 账号。

## 执行规则

1. 保留用户提示词中的专有名词、品牌名和需要渲染的文字，不擅自翻译。
2. 输入媒体可使用 WorkBuddy 提供的本地绝对路径或公开 HTTPS URL。
3. 多值图片参数使用一个复数参数后跟多个独立值，例如 `--image_list image1 image2`。
4. 对包含空格或特殊字符的提示词、路径和 URL 做安全参数传递；不得把用户内容当作 shell 语法执行。
5. 默认将产物下载到当前任务的 `./output` 目录：

```bash
meitu <command> <arguments> --json --download-dir ./output
```

6. 解析完整 JSON 中的 `ok`、`code`、`message`、`task_id`、`data.result.urls`、`downloaded_files` 以及服务端返回的操作链接字段。优先把本地下载文件交付给用户；没有下载文件时再返回远程 URL。
7. 若长任务返回可继续等待的 `task_id`，执行：

```bash
meitu task wait <task_id> --interval-ms 2000 --timeout-ms 600000 --json --download-dir ./output
```

8. 不自动付费、充值或重复提交可能产生费用的生成任务。参数错误可以修正后重试；服务错误最多重试一次；内容合规错误不重试。

## 错误处理

- `execution_auth_available` 为 false、401/403 或提示登录失效：引导用户在 Connector 页面重新连接，不在业务对话中索取 Token、AK 或 SK。
- 任何失败结果只要包含非空的充值或操作链接，不受错误码限制，依次读取 `action.url`、`action_url`、`data.recharge_url`、`data.action_url`、`data.purchase_url`、`recharge_url` 或 `purchase_url`。使用服务端返回的完整 URL 原值，不自行拼接参数、替换域名或改写路径。
- 返回码为 `80001`、`80002`，或错误信息明确表示余额、额度或权益不足，但服务端没有返回上述链接时，使用 `https://meituhub.cn/zh-cn/pricing` 作为普通套餐入口。该入口不是账号专属链接。
- 将最终地址转换为 Markdown 文本超链接，不要直接输出字段名或裸链接。固定按下面的样式回复，并用实际地址原值替换 `RECHARGE_URL`：

```markdown
当前余额或权益不足，请充值或购买套餐后重试。

[前往 MeituHub 充值](RECHARGE_URL)

充值完成后请回到当前对话，我可以继续处理刚才的任务。
```

- 只向用户展示充值入口，不自动打开链接、不发起充值或购买，也不因余额不足重复提交生成任务。若服务端没有返回链接且错误信息不表示余额、额度或权益不足，不展示充值入口。
- 输入资源无法读取：请用户提供存在的本地文件或可公开访问的 HTTPS URL。
- 参数不合法：运行该命令的 `--help`，按展示的参数和值修正。
- 超时且有 `task_id`：只等待现有任务，不重复创建任务。

## 输出

向用户说明使用的能力、成功生成的文件或链接，以及必要的 `task_id`。不要输出完整凭证、Authorization 请求头或本地会话文件内容。
