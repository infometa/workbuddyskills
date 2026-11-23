---
name: hk-ai-connector
display_name: 弧酷科技AI中台
display_name_en: Huku Tech AI Platform
description: 弧酷科技AI中台为餐饮企业提供统一的业务数据服务。连接后，可通过自然语言完成门店经营、线上渠道、会员营销及品牌知识的查询与分析。
description_zh: 弧酷科技AI中台为餐饮企业提供统一的业务数据服务。连接后，可通过自然语言完成门店经营、线上渠道、会员营销及品牌知识的查询与分析。
description_en: Huku Tech AI Platform provides unified business data services for catering enterprises. Once connected, you can query and analyze store operations, online channels, member marketing, and brand knowledge in natural language.
version: 1.0.0
author: HK AI Team
examples_zh:
  - 我都有哪些技能？
  - 我的技能有哪些分类？
  - 帮我做一个数据分析的技能，然后上传到我的技能广场
examples_en:
  - What skills do I have?
  - What skill categories do I have?
  - Create a data analysis skill and upload it to my skill plaza
---

# 弧酷科技AI中台

用于查询当前登录用户的技能分类，并把技能 zip 包上传到 AI 中台“我的技能”技能库。

## 鉴权与连接

- 连接器使用 WorkBuddy 云端 OAuth。点击连接后会在浏览器中打开 AI 中台登录/授权页；凭证由 WorkBuddy 云端托管并在请求 MCP 时自动注入，连接器包、对话和工具参数里都不应出现 token、API Key 或密码。
- 授权范围是当前登录用户在 AI 中台的技能分类与技能；不同用户按各自身份返回结果。
- 工具返回 401 时，说明授权未完成或已失效，提示用户重新连接/重新授权；不要要求用户粘贴 xToken，也不要连续重试。
- 工具返回 403 时，说明当前账号无权执行该操作；如实说明权限限制，不要换身份重试。

## 推荐使用顺序

### 查询技能分类

1. 调用 `listMyCategories`，拿到当前用户的技能分类列表（分类 ID、分类名称、排序等）。
2. 上传技能前必须先调用它，取得有效的分类 ID 作为 `skillPluginTag`；首次查询时 AI 中台会自动初始化一份用户分类。

### 上传技能

1. 确认用户提供的是 **可被 AI 中台服务端下载的 zip 文件 URL**（文件服务器、腾讯云 COS 等）。WorkBuddy 不能直接把本地文件变成可下载 URL；用户只给本地路径时，先说明需要先上传到文件服务器。
2. 调用 `uploadSkill`，必填：`fileUrl`、`displayName`、`name`、`skillVersion`、`displayDescription`、`updateDescription`、`skillPluginTag`。
3. 上传后技能进入审核中状态；审核通过后由平台自动开启企业共享。不要承诺“立即可用”。

## 可用工具

| 工具 | 用途 | 关键参数 |
| --- | --- | --- |
| `listMyCategories` | 查询当前用户的技能分类列表 | 无（身份由服务端注入） |
| `uploadSkill` | 上传技能 zip 到“我的技能”技能库 | `fileUrl`、`displayName`、`name`、`skillVersion`、`displayDescription`、`updateDescription`、`skillPluginTag` |

技能参数规则：

- `name`：只能由字母组成，多个单词用 `-` 分隔，不超过 64 字符，例如 `test-upload-skill`。
- `displayName`：不超过 32 字符。
- `displayDescription` / `updateDescription`：不超过 1024 字符。
- `skillVersion`：`x.y.z`，例如 `1.0.0`。
- `skillPluginTag`：分类 ID，多个用逗号分隔，例如 `1,3`；必须先调用 `listMyCategories` 获取。
- 图标统一使用平台默认图标，不需要也不能传入。

工具参数中没有 `xToken`/`tenantId`。身份由 WorkBuddy 注入的授权凭证在 MCP 服务端解析，调用方不能覆盖；不要把 token 写进参数、回答或日志。

## 返回格式与错误处理

- 工具返回 JSON 数组，数组里通常只有一个字符串，字符串内容才是 BI 的原始 JSON（含 `code`/`msg`/`data`）。先解析外层数组，再解析字符串里的 JSON；分类列表在 `data` 中，优先给分类 ID 和名称；上传结果优先给技能记录、`skillId`、`versionId` 和审核状态。
- 空结果明确说“没有查询到”，不要编造分类或技能。
- 参数错误时指出缺失字段，向用户询问，不要自行填默认分类 ID、技能 ID 或版本号。
- 401 时提示用户在 WorkBuddy 中重新连接/重新授权；403 时说明权限不足。不要换凭证或身份重试。
- 超时或 5xx 时说服务暂不可用，建议稍后重试；不要静默返回成功。
- 上传属于写操作，执行前先向用户确认技能名称、版本号和 zip 地址。

## 不在当前范围

- 不查询专家、不与专家对话、不查询会话历史。
- 不创建/编辑专家，不修改专家提示词、知识库或插件。
- 不查询技能列表/详情、不删除技能、不改上下架状态、不处理审核。
- 不做授权服务端与用户身份映射的实现细节；OAuth 由 WorkBuddy 云端与 AI 中台授权服务完成，MCP 服务端负责校验凭证并解析用户。
