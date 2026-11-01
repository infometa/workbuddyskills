---
name: ticnote-guide
description: 指导 AI 使用 TicNote MCP 工具管理录音转写、AI 总结、知识库和播客，覆盖上传、转写、总结、翻译、分享和深度研究等全流程操作
description_zh: 指导 AI 使用 TicNote MCP 工具管理录音转写、AI 总结、知识库和播客，覆盖上传、转写、总结、翻译、分享和深度研究等全流程操作
description_en: Guide AI to use TicNote MCP tools for managing audio transcription, AI summaries, knowledge base and podcasts, covering upload, transcription, summarization, translation, sharing and deep research
version: 1.0.6
author: TicNote
---

# TicNote 智能笔记 — AI 使用指南

TicNote 是一款 AI 驱动的智能笔记与录音转写平台。通过本连接器，AI 可以帮助用户管理知识库、转写音视频、生成总结、翻译内容、创建分享和播客，以及进行深度研究。

## 前置条件

- 用户需先在 WorkBuddy 中连接 TicNote 账号：点击「连接」后 WorkBuddy 自动打开 TicNote 授权页，用户使用手机号 + 验证码登录并完成授权（OAuth 2.1 + PKCE）
- 授权后，所有工具调用由 WorkBuddy 自动携带凭证 Authorization，对应的值是授权获取的
- Token 过期时 WorkBuddy 会自动刷新；刷新失败时工具调用返回 401，此时提示用户在 WorkBuddy 中重新连接 TicNote

## 能力范围

本连接器共提供 19 个工具，覆盖知识库浏览、上传、转写、总结、翻译、分享、播客、深度研究、用户设置和文件整理。

- **不提供删除能力**：如需删除文件，请引导用户在 TicNote App 中操作
- **不提供凭证类工具**：不会生成、返回或要求用户提供 AppKey / Token

## 统一返回格式

所有工具返回 JSON 字符串：

```json
{"code": 200, "msg": "success", "data": {...}}
```

- `code=200` 表示成功，非 200 表示失败
- 失败时 `msg` 包含错误描述，`data` 为 null

## 关键 ID 说明

TicNote 中有两类文件 ID，**务必区分**：

| ID 名称 | 来源 | 用途 |
|---|---|---|
| `id`（recordId） | `loadFileTree` 节点的 `id` 字段 | 文件详情、转写、总结、删除、重命名、复制、移动、分享（大多数接口） |
| `fileId` | `loadFileTree` 节点的 `fileId` 字段 | 仅 `localFileSummary`（非音频文件总结）的 `taskId` 参数使用 |

> `fileId` 通常比 `id` 小 1。绝大多数接口使用 `id`（recordId），只有 `localFileSummary` 例外使用 `fileId`。

## 文件状态 status 枚举

`loadFileTree` 节点和 `fileDetailV2` 返回的 `status` 字段统一使用以下枚举：

| status | 含义 | 说明 |
|---|---|---|
| `-1` | 准备中 | 文件正在准备，暂不可操作 |
| `0` | 上传成功 | 文件已上传，尚未转写/总结 |
| `1` | 转写中 | 转写任务进行中，继续轮询 |
| `2` | 成功 | **终态**：全部处理完成，转写内容和总结均可读取 |
| `3` | 失败 | **终态**：处理失败，提示用户重新提交 |
| `4` | 转写成功 | 转写已完成（`transcribeJson` 可读取），总结尚未完成 |
| `5` | 总结中 | 总结任务进行中，继续轮询 |

- **轮询结束条件**：`status=2`（成功）或 `status=3`（失败）
- 只需要转写文本时，`status=4` 即可读取 `transcribeJson`，无需等到总结完成
- 正常流转：`-1/0 → 1（转写中）→ 4（转写成功）→ 5（总结中）→ 2（成功）`，任一环节出错变为 `3`

---

## 工具分类与使用场景

### 一、知识库浏览

#### getChatList — 获取项目/文件夹列表

- **用途**：列出用户所有知识库项目和文件夹，支持模糊搜索
- **参数**：`query`（可选，搜索关键词，不传返回全量）
- **关键返回**：`chats[].project_id` 可作为 `loadFileTree` 的 `rootId` 参数
- **典型用法**：用户说「查看我的项目」或「搜索名为 XX 的项目」

#### loadFileTree — 获取文件树

- **用途**：获取文件树结构，包含目录节点和文件节点
- **参数**：
  - `parentId`（可选）：父节点 ID，只加载该层级子节点
  - `rootId`（可选）：从 `getChatList` 的 `project_id` 获取，限定项目范围；为空则返回全部
- **关键返回**：
  - `id`：节点 ID（**recordId**），后续大多数接口使用此值
  - `fileId`：底层文件 ID，仅 `localFileSummary` 使用
  - `name`：文件或目录名称
  - `type`：`file`=文件，`directory`=目录
  - `status`：文件状态，取值见「文件状态 status 枚举」（2=成功，3=失败）
  - `voiceInfo.transcribeId`：转写任务 ID
  - `voiceInfo.summaryId`：总结任务 ID
  - `subRemark`：JSON 字符串，含 `duration`（时长秒）、`originSuffix`（原始格式）、`notRead`（是否未读）

---

### 二、文件详情与状态轮询

#### fileDetailV2 — 获取文件详情

- **用途**：获取文件完整详情，包含转写内容、总结内容、任务状态；也是异步任务的轮询入口
- **参数**：`recordId`（必填，使用 `loadFileTree` 节点的 `id` 字段，**不是 fileId**）
- **关键返回**：
  - `status`：文件状态，取值见「文件状态 status 枚举」：-1=准备中，0=上传成功，1=转写中，2=成功，3=失败，4=转写成功，5=总结中
  - `transcribeJson`：转写内容 JSON 数组字符串（status=4 或 2 时有值），每项含 `speaker`/`start`/`end`/`text`
  - `summaryJson`：总结内容 JSON 字符串（status=2 时有值），含 `title`/`md2`（Markdown）/`mind2`（思维导图）/`keywords`
  - `transcribeId`：转写任务 ID
  - `summaryId`：总结任务 ID（生成播客时使用）
  - `podcastUrl`：播客音频 URL（播客生成完成后有值）
  - `language`：检测到的语言，如 `zh`、`en`
- **轮询用法**：提交异步任务后，每隔 3～5 秒调用本接口检查 `status`，直到 `status=2`（成功）或 `status=3`（失败）；`1`/`4`/`5` 为中间状态，需继续轮询
- **注意**：MCP 接口中 `fileUrl` 和 `formatUrl` 固定返回 null，不暴露文件直链

---

### 三、文件上传（三步走）

上传文件到知识库的完整流程：

**方式 A：有公网 URL（推荐，更简单）**

直接调用 `uploadToKnowledge`，在 `filesJson` 的 `fileUrl` 中传入文件的公网 URL，跳过 COS 上传步骤。

**方式 B：无公网 URL，需先上传到 COS**

1. 调用 `applyOssToken` 获取 COS 临时凭证
2. 使用凭证中的 `tmpSecretId`/`tmpSecretKey`/`sessionToken`，通过腾讯云 COS SDK 或 HTTP PUT 上传文件到 `bucket`/`cosRegion`
3. 调用 `uploadToKnowledge`，在 `fileUrl` 中传入 COS 文件的公网 URL

#### applyOssToken — 获取 COS 临时上传凭证

- **用途**：上传三步走的第一步，获取腾讯云 COS 临时凭证
- **参数**：无
- **关键返回**：
  - `bucket`：COS Bucket 名称
  - `cosRegion`：COS 地域，如 `ap-nanjing`
  - `expiredTime`：凭证过期时间（Unix 秒）
  - `credentials.tmpSecretId`：临时 SecretId
  - `credentials.tmpSecretKey`：临时 SecretKey
  - `credentials.sessionToken`：会话 Token

#### uploadToKnowledge — 注册文件到知识库

- **用途**：上传三步走的最后一步，将文件注册到知识库，支持批量
- **参数**：
  - `parentId`（可选）：目标父目录 ID；从 `getChatList` 的 `project_id`、`loadFileTree` 目录节点 `id` 或 `mkdir` 返回值获取
  - `filesJson`（必填）：文件列表 JSON 数组，每项字段：
    - `fileName`（必填）：文件名含后缀，如 `meeting.mp3`
    - `fileType`（必填）：格式后缀，如 `mp3`/`m4a`/`mp4`/`pdf`/`docx`
    - `fileUrl`（可选）：文件公网 URL
    - `recordTime`（可选）：录音时间戳（毫秒），不传使用服务端当前时间
    - `sn`（可选）：设备 SN 号，手机录制传 `local`
- **关键返回**：`successFiles[].recordId`（后续转写/总结接口使用此值作为 fileId）

---

### 四、转写与总结

#### commitTranscribeTask — 提交 ASR 转写任务

- **用途**：对音视频文件提交语音转文字任务（**异步**）
- **参数**：`requestJson`（JSON 字符串），字段：
  - `fileId`（必填）：文件节点 ID（recordId），从 `loadFileTree.id` 或 `uploadToKnowledge` 返回的 `recordId` 获取
  - `language`（可选）：识别语言；可选值：`zh`/`zh-Hant`/`en`/`ja`/`fr`/`de`/`es`/`it`/`pl`/`pt`/`ru`/`ko`/`cs`；不传自动检测
  - `hasSpeakers`（可选）：是否区分说话人，默认 false
  - `template`（可选）：总结模板名称，如 `Autopilot`
  - `templateCustomize`（可选）：自定义模板内容，传此字段则忽略 `template`
  - `model`（可选）：LLM 模型名称
  - `detailLevel`（可选）：总结详细程度，`conciser`=简洁 / `more_details`=详细
- **关键返回**：`transcribeId`（转写任务 ID）、`summaryId`（总结任务 ID）
- **后续**：用 `fileDetailV2` 轮询 `status`：`1`=转写中 → `4`=转写成功 → `5`=总结中 → `2`=成功；`3`=失败

#### reSummary — 重新触发音频总结

- **用途**：对已转写完成的音频重新生成总结（**异步**）
- **参数**：`requestJson`（JSON 字符串），字段：
  - `fileId`（必填）：文件节点 ID（recordId），从 `loadFileTree.id` 获取
  - `lang`（可选）：输入文本语言，如 `zh`/`en`，不传自动检测
  - `template`（可选）：总结模板名称
  - `templateCustomize`（可选）：自定义模板内容
  - `hasSpeakers`（可选）：是否区分说话人
  - `model`（可选）：LLM 模型名称
  - `detailLevel`（可选）：`conciser` / `more_details`
- **后续**：用 `fileDetailV2` 轮询 `status`
- **⚠️ 高风险**：重新总结会**覆盖原有总结内容**，执行前须向用户确认

#### localFileSummary — 触发非音频文件总结

- **用途**：对 PDF、Word、TXT 等非音频文件触发总结（**异步**）
- **参数**：
  - `taskId`（必填）：⚠️ **使用 `loadFileTree` 节点的 `fileId` 字段，不是 `id`/`recordId`**
  - `projectId`（可选）：项目 ID
  - `model`（可选）：LLM 模型名称
  - `detailLevel`（可选）：`conciser` / `more_details`
- **注意**：会检查用户权益余量，不足时返回错误
- **后续**：用 `fileDetailV2` 轮询 `status`

---

### 五、翻译

#### translate — 翻译转写内容

- **用途**：对已转写完成的文件发起翻译（**异步**，同时触发重新总结，会覆盖原有总结内容）
- **参数**：`dtoJson`（JSON 字符串），字段：
  - `transcribeId`（可选）：转写任务 ID；从 `commitTranscribeTask` 返回或 `fileDetailV2.transcribeId` 获取
  - `fileId`（可选）：文件 ID；与 `transcribeId` 二选一传入，优先传 `transcribeId`
  - `targetLanguage`（必填）：目标语言代码，如 `zh`/`en`/`ja`/`ko`/`fr`/`de`/`es`/`it`/`ru`/`pt`
- **关键返回**：新的 `transcribeId` 和 `summaryId`
- **后续**：用 `fileDetailV2` 轮询 `status`
- **⚠️ 高风险**：翻译会触发重新总结，**覆盖原有总结内容**，执行前须向用户确认

---

### 六、分享

#### createShare — 创建分享链接

- **用途**：为指定文件创建分享链接，返回 shareCode
- **参数**：
  - `shareType`（必填）：`audio`（音频）/ `localFile`（本地文件，如 PDF/Word）/ `translation`（翻译内容）
  - `params`（必填）：JSON 字符串，audio 类型字段：
    - `fileId`（必填）：文件 ID（使用 `loadFileTree.id`）
    - `tabs`（可选）：展示标签页，数组，可选值：`summary`/`transcript`/`mindMap`/`moment`
- **关键返回**：`data` 直接为 shareCode 字符串
- **⚠️ 高风险**：分享链接**无需登录即可访问**，会暴露文件标题、转写全文、总结及音频播放地址。执行前须向用户确认要分享的文件和展示的标签页（`tabs`），并提醒用户链接可被任何持有者查看

#### getShare — 访问分享内容

- **用途**：通过分享码访问分享内容（**无需登录**）
- **参数**：
  - `shareType`（必填）：分享类型，`audio`/`localFile`/`translation`
  - `shareCode`（必填）：由 `createShare` 返回的 `data` 字段值
- **关键返回**（audio 类型）：
  - `title`：文件标题
  - `formatUrl`：音频播放 URL（WAV 格式）
  - `segments[]`：转写片段数组，每项含 `start`/`end`/`text`/`speaker`
  - `summaryResult.md2`：Markdown 格式总结内容
  - `summaryResult.mind2`：Markdown 格式思维导图内容
  - `summaryResult.keywords`：关键词列表

---

### 七、播客生成

#### generatePodcast — 生成播客音频

- **用途**：基于总结内容生成播客音频（**异步**）
- **参数**：`dtoJson`（JSON 字符串），字段：
  - `summaryId`（可选）：音频文件的总结任务 ID，从 `fileDetailV2.summaryId` 获取；与 `localFileId` 二选一
  - `localFileId`（可选）：非音频文件 ID；生成非音频文件播客时使用；与 `summaryId` 二选一
- **后续**：用 `fileDetailV2` 轮询 `podcastUrl` 字段，有值即为生成完成

---

### 八、深度研究

#### deepResearchQuery — 发起深度研究

- **用途**：基于知识库内容进行 AI 深度分析和研究报告生成（**异步**）
- **参数**：`dtoJson`（JSON 字符串），字段：
  - `projectId`（可选）：项目 ID，限定研究范围
  - `question`（可选）：研究问题，如「分析本次会议的核心决策点和行动项」

---

### 九、用户设置

#### getUserSetting — 获取用户设置

- **用途**：获取当前登录用户的个人设置
- **参数**：无
- **关键返回**：
  - `radioSaveStyle`：录音保存方式，`{ local: 0/1, app: 0/1, cloud: 0/1 }`
  - `cloudSyncStyle`：云同步设置，`{ auto: 0/1 }`
  - `autoTranscribeStyle`：自动转写设置，`{ auto: true/false }`
  - `languageStyle`：界面语言，`{ language: "zh"/"en" }`
  - `transcribeLanguage`：默认转写语言，`{ language: "zh"/"en"/... }`
  - `industryKey`：行业关键词标识

#### saveUserSetting — 保存用户设置

- **用途**：修改当前用户的个人设置，只传需要修改的字段，未传字段保持不变
- **参数**：`dtoJson`（JSON 字符串），所有字段均可选：
  - `radioSaveStyle`：录音保存方式，`{ local: 0/1, app: 0/1, cloud: 0/1 }`
  - `cloudSyncStyle`：云同步，`{ auto: 0/1 }`（1=开启自动同步）
  - `autoTranscribeStyle`：自动转写，`{ auto: true/false }`
  - `languageStyle`：界面语言，`{ language: "zh"/"en" }`
  - `transcribeLanguage`：默认转写识别语言，`{ language: "zh"/"en"/...语言代码 }`
  - `industryKey`：行业关键词

---

### 十、文件管理

#### mkdir — 创建目录

- **用途**：在知识库中创建新目录（文件夹）
- **参数**：
  - `parentId`（可选）：父目录 ID；为空时在根目录创建；从 `getChatList.project_id` 或 `loadFileTree` 目录节点 `id` 获取
  - `dtoJson`（必填）：`{ "title": "目录名称", "color": "颜色标识（可选）", "icon": "图标标识（可选）" }`
- **关键返回**：`data` 为新创建目录的 recordId（Long），可作为后续接口的 `parentId`

#### editKnowledge — 重命名/更新文件元数据

- **用途**：重命名文件或目录，或更新颜色/图标
- **参数**：
  - `recordId`（必填）：从 `loadFileTree.id` 获取
  - `dtoJson`（必填）：可选字段 `title`（新名称）/`color`/`icon`，只传需要修改的字段

#### copyKnowledge — 复制文件到目标目录

- **用途**：将指定文件（支持批量）复制到目标目录
- **参数**：
  - `targetParentId`（必填）：目标目录 ID
  - `recordIdsJson`（必填）：要复制的 recordId 数组，如 `[123, 456]`

#### moveKnowledge — 移动文件到目标目录

- **用途**：将指定文件（支持批量）移动到目标目录
- **参数**：
  - `targetParentId`（必填）：目标目录 ID
  - `recordIdsJson`（必填）：要移动的 recordId 数组，如 `[123, 456]`
- **⚠️ 执行前建议向用户确认**，移动后文件位置将改变

---

## 典型使用流程

### 流程一：上传文件并转写总结

```
1. getChatList          → 获取 project_id（作为 rootId）
2. loadFileTree         → 找到目标目录的 id（作为 parentId）
3. [可选] applyOssToken → 获取 COS 临时凭证（有公网 URL 可跳过）
4. [可选] 上传文件到 COS → 使用 credentials 直传文件
5. uploadToKnowledge    → 注册文件，返回 recordId
6. commitTranscribeTask → 提交转写任务，fileId = 上一步的 recordId
7. fileDetailV2         → 每隔 3~5 秒轮询 status，直到 status=2（成功）或 3（失败）
8. [可选] generatePodcast → 传入 summaryId 生成播客音频
```

### 流程二：翻译已有文件

```
1. loadFileTree    → 获取文件节点 id（recordId）
2. fileDetailV2    → 获取 transcribeId
3. translate       → 发起翻译，传入 transcribeId 和 targetLanguage
                     ⚠️ 会覆盖原有总结，需用户确认
4. fileDetailV2    → 轮询 status 直到 2（成功）或 3（失败）
```

### 流程三：创建分享并访问

```
1. loadFileTree   → 获取文件节点 id
2. createShare    → 创建分享，shareType="audio"，获取 shareCode
3. getShare       → 使用 shareCode 访问分享内容（无需鉴权）
```

### 流程四：非音频文件（PDF/Word）总结

```
1. loadFileTree       → 获取文件节点（同时记录 id 和 fileId）
2. localFileSummary   → 提交总结，taskId = loadFileTree.fileId（⚠️ 不是 id）
3. fileDetailV2       → 轮询 status 直到 2（成功）或 3（失败），使用 loadFileTree.id 作为 recordId
```

### 流程五：整理知识库

```
1. getChatList        → 获取所有项目列表
2. loadFileTree       → 获取指定项目的文件树
3. mkdir              → 创建新目录，获取新目录的 recordId
4. moveKnowledge      → 将文件移动到新目录（需用户确认）
5. editKnowledge      → 重命名文件或目录
```

---

## 错误处理

| 错误场景 | 处理方式 |
|---|---|
| `code` 非 200 | 向用户展示 `msg` 中的错误信息 |
| 权益不足（总结/翻译）| 提示用户权益已用完，需在 TicNote App 中购买 |
| 文件不存在 | 提示用户检查文件是否已被删除 |
| 转写/总结失败（status=3）| 提示用户重新提交任务或联系支持 |
| 转写/总结超时（长时间停留在 status=1 转写中 或 5 总结中）| 提示用户稍后再次查询，或重新提交 |
| COS 凭证过期 | 重新调用 `applyOssToken` 获取新凭证 |
| 鉴权失效（401）| WorkBuddy 会自动刷新 Token；仍失败时提示用户在 WorkBuddy 中重新连接 TicNote 账号 |

## 高风险操作确认规则

以下操作执行前**必须向用户确认**，得到明确同意后再调用：

| 工具 | 风险说明 |
|---|---|
| `translate` | 翻译会**触发重新总结，覆盖原有总结内容** |
| `reSummary` | 重新总结会**覆盖原有总结内容** |
| `createShare` | 生成**公开可访问**的分享链接，可能泄露转写全文、总结和音频 |
| `moveKnowledge` | 移动文件会改变文件位置，影响原有目录结构 |
| `saveUserSetting` | 修改账号级设置（自动转写、云同步、默认语言等），影响后续所有录音 |
