---
name: ihr-conference
description: "iHR360 面谈/会议：搜索历史面谈记录、按需读取会话文档预览或完整详情、带参创建并发起面谈。查询历史面谈时先搜索候选；读取内容时再取文档；发起面谈前必须确认人员 ID 和时间。"
metadata:
  requires:
    bins: ["ihr-cli"]
  cliHelp: "ihr-cli conference --help"
---

# conference (v1)

**CRITICAL — 开始前 MUST 先阅读 [`../ihr-shared/SKILL.md`](../ihr-shared/SKILL.md)，其中包含共享运行规则、时间处理原则和 JSON 协议。**

## 核心概念

- **ConferenceSession**：面谈/会议会话，通过 `conferenceSessionId` 标识。
- **Search Result**：首轮搜索返回的候选会话集合，包含 `conferenceSessionIds`、`returnedCount`、`truncated` 和可选 `previewItems`。
- **Preview Item**：标准化会话预览项，包含搜索状态、时间、多类预览文本，以及 `currentQueryUserIdentity`。搜索结果没有基础信息权限时会删除整条预览项，其他受限字段返回 `null`。
- **Session Documents**：按会话 ID 读取的文档化结果，是搜索后的第二步动作；每项通过 `access` 表达四类内容权限，按需使用 `fullDetail=true` 读取完整转写。
- **Avatar Template**：数字人面试配置模板。`+search-avatar-template` 和 `+create-avatar-template` 返回的 `templateId` 是数字人模板业务 ID，可作为 `+launch --interviewCode` 使用；它不是 conference 大纲模板 `templateId`。
- **Launch Request**：带参创建并发起面谈的请求。目的和模板使用静态 ID，普通系统内人员必须先通过 `ihr-cli base +selectStaffs` 查找并确认；可选 `outline.mdText` 传入 Markdown 格式面谈大纲。数字人面谈通过 `thirdPartyPlatform=DIGITAL_AVATAR` 或 `interviewMode=DIGITAL_AVATAR` 和 `digitalAvatarConfig.interviewCode` 选择，不暴露后端角色码。

## 核心场景

### 1. 搜索历史面谈记录

1. 当用户在问“开过的会”“历史面谈”“最近发生过的面谈”“某段时间聊过什么”时，优先使用本技能。
2. 默认先执行搜索，再决定是否继续读取会话文档。
3. 搜索结果很多时，优先返回候选和预览，不要直接全量读取详情。

### 2. 读取会话文档

1. 当用户已经指定会话，或明确需要摘要、待办、转写摘要、完整转写等内容时，再读取会话文档。
2. `+documents` 是 `+search` 之后的第二步动作，不应默认替代搜索。
3. 只有用户明确需要逐句完整转写时才开启 `--fullDetail`，避免不必要地读取和返回大体量内容。

### 3. 创建并发起面谈

1. 当用户明确说“发起、预约、创建会议、安排面谈”时，才使用 `+launch`。
2. 如果用户只说“准备一下、拟一个面谈安排”，不要发起；可以先整理参数或使用 `--dry-run`。
3. 如果只给了人员姓名，优先按内部人员处理，先调用 `ihr-cli base +selectStaffs` 查找候选并确认 `id`，不能凭姓名猜 staffId；只有用户明确说明是外部人员，或内部人员查找无匹配且用户确认按外部人员处理时，才允许不传 `staffId`。
4. 如果缺少时间、面谈官、面谈对象，先追问，不调用发起接口。
5. 用户提供面谈大纲时，按 Markdown 文本传入 `--outlineMdText` 或 JSON 的 `outline.mdText`；未提供或内容为空时由服务端后台自动生成。
6. 如果用户明确要求数字人面谈，先确认数字人面试模板：已有模板时可用 `+search-avatar-template` 查询；没有合适模板时可用 `+create-avatar-template` 创建。返回的 `templateId` 填到 `+launch --interviewCode`。
7. 数字人面谈候选人必须有 `name` 和 `phone` 或 `email`，可以没有 `staffId`。
8. 数字人面谈不要要求或构造 `roleCode`、`DA_*`、`REGULAR_*`。数字人面谈官用 `sourceType=DIGITAL_HUMAN` 表示，`staffId` 是数字人配置 ID；未给面谈官或唯一数字人面谈官未给 `staffId` 时会默认补 `1`。

## 资源关系

```text
ConferenceSession
├── Search Result
│   ├── conferenceSessionIds[]
│   └── previewItems[]
│       ├── status
│       ├── startTime / endTime / createTime
│       ├── finalScore
│       ├── basicText / outlineText / smartMinutesText / topicText
│       ├── summaryText / todoText / transcriptSummaryText
│       └── currentQueryUserIdentity
└── Session Documents
    └── previewItems[]
        ├── access.basicInfo / outline / smartSummary / transcript
        ├── status
        ├── startTime / endTime / createTime
        ├── basicText / outlineText / smartMinutesText / topicText
        ├── summaryText / todoText / transcriptSummaryText
        ├── currentQueryUserIdentity
        └── transcriptSegments[]  # 仅 fullDetail=true 且允许查看转写时返回

Launch Request
├── purposeId / templateId
├── startTime / duration / interviewMode / thirdPartyPlatform
├── digitalAvatarConfig
├── interviewers[]
├── interviewees[]
├── others[]
└── outline.mdText

Avatar Template
├── templateId  # 用作 +launch --interviewCode
├── templateName / interviewName
├── jobTitle / digitalHumanId
├── questionsCount / usageCount / hasDraft
└── updatedAt
```

> **路由规则**：用户先问“有哪些历史面谈/聊过什么/最近开过什么”时，优先使用 `+search`。只有在用户明确需要阅读内容、摘要、待办、转写摘要，或已指定 `conferenceSessionId` 时，才进入 `+documents`。用户明确要创建、预约或发起面谈，且关键参数已确认时，才进入 `+launch`。
>
> **禁止误用**：`+launch` 有真实副作用，会创建会话并发起三方会议。人员、时间或意图不确定时不要调用。
>
> **默认策略**：先搜候选，再按需读文档；不要把会话文档读取当成首轮入口。
>
> **权限语义**：`+search` 与 `+documents` 的无权限响应不同。搜索没有基础信息权限时删除整条 `previewItem`，且不返回 `access`；文档批量读取会按请求顺序保留每个 session，无基础信息权限或 session 不可用时仅返回 `conferenceSessionId` 和四项全为 `DENIED` 的 `access`，其他业务字段为 `null`。
>
> **人员依赖**：`+launch` 依赖 `ihr-cli base +selectStaffs`。拿到姓名时优先查找内部人员；分项参数或 JSON 里的内部人员必须使用已确认的 `staffId`，不要把姓名直接当作人员 ID。只有用户明确说明是外部人员，或内部人员查找无匹配且用户确认按外部人员处理时，外部人员才可以没有 `staffId`，但必须提供姓名、手机号、邮箱等足够识别和联系的信息。参与人未传 `sourceType` 时，有 `staffId` 的人员按当前产品补 `IHR360/WORK100`，没有 `staffId` 的人员补 `EXTERNAL`。
>
> **面谈大纲**：`+launch` 支持 Markdown 格式大纲。传入 `outline.mdText` 后，服务端会直接保存该大纲，不触发后台自动生成；不传或传空白时，服务端按模板后台生成大纲。
>
> **数字人面谈**：数字人面谈仍使用 `+launch`，传 `thirdPartyPlatform=DIGITAL_AVATAR` 或 `interviewMode=DIGITAL_AVATAR`，并传 `digitalAvatarConfig.interviewCode`。如果用户没有给出可用 `interviewCode`，先用 `+search-avatar-template` 搜索；没有合适模板时再用 `+create-avatar-template` 创建。候选人只允许一个，必须有联系方式；`others` 不支持；真人监考官只有在允许介入时才作为非 `DIGITAL_HUMAN` 面谈官传入，且必须且只能有一个。不要向用户暴露后端角色码。

## Shortcuts（推荐优先使用）

Shortcut 是对常用操作的高级封装（`ihr-cli conference +<verb>`）。有 Shortcut 的操作优先使用。

| Shortcut | 说明 |
|----------|------|
| [`+search`](references/ihr-conference-search.md) | 搜索历史面谈记录，支持结构化条件、文本搜索和首轮预览 |
| [`+documents`](references/ihr-conference-documents.md) | 按会话 ID 读取文档化预览或完整转写详情 |
| [`+search-avatar-template`](references/ihr-conference-avatar-template.md) | 查询已有数字人面试模板，返回可作为 `interviewCode` 的 `templateId` |
| [`+create-avatar-template`](references/ihr-conference-avatar-template.md) | 创建并发布数字人面试模板，返回可作为 `interviewCode` 的 `templateId` |
| [`+launch`](references/ihr-conference-launch.md) | 带参创建并发起面谈，要求人员 ID 已确认 |

## Current Implementation

当前主实现已经在 `ihr-cli` 子项目内：

| Shortcut | 当前命令 |
|----------|----------|
| `ihr-cli conference +search` | `ihr-cli conference +search` |
| `ihr-cli conference +documents` | `ihr-cli conference +documents` |
| `ihr-cli conference +search-avatar-template` | `ihr-cli conference +search-avatar-template` |
| `ihr-cli conference +create-avatar-template` | `ihr-cli conference +create-avatar-template` |
| `ihr-cli conference +launch` | `ihr-cli conference +launch` |

## Scenes

可复用的自然语言测试问题集位于：

1. [`scenes/ihr-conference-skill-test-questions.txt`](scenes/ihr-conference-skill-test-questions.txt)

## 能力入口

公开入口只有 `ihr-cli conference +search`、`ihr-cli conference +documents` 和 `ihr-cli conference +launch`。字段契约通过命令 help 或 schema 能力确认；不要在 skill 中暴露底层路径，也不要使用 `ihr-interface`、raw API、curl/httpie/wget 或自写 HTTP client。
