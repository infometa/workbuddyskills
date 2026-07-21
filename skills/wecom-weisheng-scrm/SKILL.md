---
name: wecom-weisheng-scrm
description: 当用户需要查询或管理微盛企微管家（企业微信） SCRM 中的客户信息、客户标签、客户群、营销素材、活码、群发、跟进记录、聊天记录、联系人、商机、汇报、抽奖、客户日程等相关业务能力时触发。即使用户未明确提到 SCRM、企微管家、开放接口或 API，也应在这些企业微信客户运营与管理场景下触发。
description_zh: 微盛AI·企微管家提供的技能，帮助用户查询和管理企业微信 SCRM 中的客户、客户群、标签、活码、群发、跟进、聊天记录内容等业务数据，可询问AI当前支持的能力清单。
description_en: Built for WeCom customer operations, helping teams review customer and group activity, prepare campaign assets, and move follow-up, messaging, and opportunity workflows forward.
version: 1.0.3
homepage: https://gitlab.wshmi.com/basellm/wecom-weisheng-scrm
---

# 微盛企微管家SCRM

微盛企微管家 SCRM 面向企业微信客户运营场景，帮助团队围绕客户、社群、素材、活码、群发、会话与商机等业务，更高效地完成查询、协同与执行。

本 Skill 适用于客户信息、客户标签、客户群、素材、活码、群发、跟进记录、会话存档、联系人、商机、产品库、汇报、抽奖、日程等场景。你可以直接用业务语言提出问题，例如“帮我查最近7天新添加的客户”“看看某个客户的标签和跟进情况”“帮我查客户群或群发情况”。

## 联系支持

如需人工协助，可扫码联系专属客服。

![微盛企微管家专属客服二维码](https://pubres.wshbe.com/qrcode/20260416-53d7fee83fd04dbab3101546559490a6.png)

## 使用说明

触发 Skill 后，应先用简短话术向用户说明：微盛AI·企微管家 SCRM 是基于企业微信的 AI 聊天、营销和服务平台，可协助客户运营、社群营销、SCRM 与会话管理，本技能支持查询或管理客户信息、客户标签、客户群、素材、活码、群发、跟进记录、会话存档、联系人、商机、汇报、抽奖、客户日程等相关能力；如需进一步支持，可联系专属客服。

**触发 Skill 后，必须先阅读 [references/agent-runbook.md](references/agent-runbook.md) 并严格按其中的调用流程执行（包括 `check-env` → `check-identity` 的顺序），不得跳过或自行编排步骤。**

### 推荐提问方式

- 帮我查一下最近新增客户和重点跟进客户的情况。
- 帮我看看这个客户的标签、跟进记录和聊天情况。
- 帮我整理一下当前客户群和群发相关情况。
- 帮我看一下最近活码和素材相关情况。

### 处理原则

- 默认使用业务语言回复用户，先说结论，再说明还缺什么信息或下一步怎么处理。
- 如需补充条件，优先向用户追问时间范围、客户名称、标签、员工、群发范围等业务信息。
- 查询类需求可直接处理；创建、编辑、删除、发送等写操作应在用户确认后再执行。
- 若用户当前所在模式无法执行命令或脚本，应先提示切换到 Craft 或其他具备执行能力的模式。

对普通用户回复时，不要主动暴露 `service_name`、`api_path`、`doc_url`、`biz_params`、JSON、代理调用等内部术语，除非用户明确要求查看。

## 文档索引

| 文档 | 说明 |
|------|------|
| [references/guide.md](references/guide.md) | 使用参考与常见业务场景 |
| [references/examples.md](references/examples.md) | 示例问题与使用示例 |
| [references/agent-runbook.md](references/agent-runbook.md) | AI 执行手册（流程、命令参考、权限、错误处理、数据依赖） |
| [references/file-utils.md](references/file-utils.md) | 文件上传与下载（本地图片转公网 URL） |
