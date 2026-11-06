---
name: ticnote-guide
description: 指导 AI 使用 TicNote MCP 工具管理录音转写、AI 总结和知识库，覆盖上传、转写、总结、翻译、分享等全流程操作
description_zh: 指导 AI 使用 TicNote MCP 工具管理录音转写、AI 总结和知识库，覆盖上传、转写、总结、翻译、分享等全流程操作
description_en: Guide AI to use TicNote MCP tools for managing audio transcription, AI summaries and knowledge base, covering upload, transcription, summarization, translation and sharing
version: 1.0.6
author: TicNote
---

# TicNote 智能笔记 — AI 使用指南

TicNote 是一款 AI 驱动的智能笔记与录音转写平台。通过本连接器，AI 可以帮助用户浏览知识库、上传并转写音视频、生成总结、翻译内容和创建分享。

## 前置条件

- 用户需先在 WorkBuddy 中连接 TicNote 账号：点击「连接」后 WorkBuddy 自动打开 TicNote 授权页，用户使用手机号 + 验证码登录并完成授权（OAuth 2.1 + PKCE）
- 授权后，所有工具调用由 WorkBuddy 自动携带凭证 Authorization，对应的值是授权获取的
- Token 过期时 WorkBuddy 会自动刷新；刷新失败时工具调用返回 401，此时提示用户在 WorkBuddy 中重新连接 TicNote

## 能力范围

本连接器共提供 11 个工具：

| 分类 | 工具 |
|---|---|
| 知识库浏览 | `loadFileTree`、`fileDetailV2` |
| 文件上传 | `applyOssToken`、`uploadToKnowledge` |
| 转写与总结 | `commitTranscribeTask`、`reSummary`、`localFileSummary` |
| 翻译 | `translate` |
| 分享 | `createShare`、`getShare` |
| 文件管理 | `mkdir` |

## 统一返回格式

所有工具返回 JSON 字符串：

```json
{"code": 200, "msg": "success", "data": {...}}
```

- `code=200` 表示成功，非 200 表示失败
- 失败时 `msg` 包含错误描述，`data` 为 null

## 关键 ID 说明

TicNote 中有两类 ID，**务必区分，传错会导致「文件不存在」**：

| ID 名称 | 来源 | 用于 |
|---|---|---|
| `recordId` | `loadFileTree` / `uploadToKnowledge` / `fileDetailV2` 返回项的 `recordId`；`mkdir` 的返回值 | `fileDetailV2` 的 `recordId`、`uploadToKnowledge` / `mkdir` 的 `parentId` |
| `fileId` | `loadFileTree` / `uploadToKnowledge` / `fileDetailV2` 返回项的 `fileId` | `commitTranscribeTask`、`reSummary`、`translate`、`createShare`（audio）、`localFileSummary` 的 `fileId` |

> 记忆方法：**查详情、选目录用 `recordId`；对文件内容做处理（转写/总结/翻译/分享）用 `fileId`**。
> 两者数值通常相差 1，但不能互相替代。

## 文件状态 status 枚举

`loadFileTree` 返回项和 `fileDetailV2` 返回的 `status` 字段统一使用以下枚举：

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

## 支持的语言编码

转写（`commitTranscribeTask.language`）和翻译（`translate.targetLanguage`）支持**同一套 100 种语言编码**，必须使用下表中的 `code` 值。

- 用户用自然语言指定语言时（如「翻译成繁体中文」「转写粤语」），先映射为下表的 `code`（`zh-Hant`、`yue`），再调用接口
- 常用：`zh` 中文简体、`en` 英语、`ja` 日语、`es` 西班牙语、`fr` 法语、`de` 德语、`ru` 俄语、`it` 意大利语、`ko` 韩语、`zh-Hant` 繁体中文、`yue` 粤语
- 爪哇语使用 `jw`（不是 `jv`），挪威语使用 `no`
- 转写时 `language` 不传则自动检测；翻译时 `targetLanguage` 必填

<details>
<summary>完整语言编码表（100 种，按常用度排序）</summary>

| code | 名称 | 说明 |
|---|---|---|
| `zh` | 中文简体-普通话（翻译：中文(简体)） | 中文（简体）/普通话 |
| `en` | English | 英语 |
| `ja` | 日本語 | 日语 |
| `es` | Español | 西班牙语 |
| `fr` | Français | 法语 |
| `de` | Deutsch | 德语 |
| `ru` | Русский | 俄语 |
| `it` | Italiano | 意大利语 |
| `ko` | 한국어 | 韩语 |
| `zh-Hant` | 中文(繁體)-國語（翻译：中文(繁體)） | 中文（繁体）/国语 |
| `yue` | 中文(繁體)-粵語 | 中文（繁体）/粤语 |
| `pt` | Português | 葡萄牙语 |
| `ar` | العربية | 阿拉伯语 |
| `hi` | हिन्दी | 印地语 |
| `id` | Bahasa Indonesia | 印度尼西亚语 |
| `vi` | Tiếng Việt | 越南语 |
| `th` | ไทย | 泰语 |
| `tr` | Türkçe | 土耳其语 |
| `ms` | Bahasa Melayu | 马来语 |
| `nl` | Nederlands | 荷兰语 |
| `pl` | Polski | 波兰语 |
| `uk` | Українська | 乌克兰语 |
| `tl` | Tagalog | 他加禄语 |
| `fa` | فارسی | 波斯语 |
| `bn` | বাংলা | 孟加拉语 |
| `ur` | اردو | 乌尔都语 |
| `sv` | Svenska | 瑞典语 |
| `he` | עברית | 希伯来语 |
| `el` | Ελληνικά | 希腊语 |
| `cs` | Čeština | 捷克语 |
| `ro` | Română | 罗马尼亚语 |
| `hu` | Magyar | 匈牙利语 |
| `da` | Dansk | 丹麦语 |
| `fi` | Suomi | 芬兰语 |
| `no` | Norsk | 挪威语 |
| `ca` | Català | 加泰罗尼亚语 |
| `ta` | தமிழ் | 泰米尔语 |
| `te` | తెలుగు | 泰卢固语 |
| `mr` | मराठी | 马拉地语 |
| `gu` | ગુજરાતી | 古吉拉特语 |
| `pa` | ਪੰਜਾਬੀ | 旁遮普语 |
| `kn` | ಕನ್ನಡ | 卡纳达语 |
| `ml` | മലയാളം | 马拉雅拉姆语 |
| `sw` | Kiswahili | 斯瓦希里语 |
| `bg` | Български | 保加利亚语 |
| `hr` | Hrvatski | 克罗地亚语 |
| `sr` | Српски | 塞尔维亚语 |
| `sk` | Slovenčina | 斯洛伐克语 |
| `sl` | Slovenščina | 斯洛文尼亚语 |
| `lt` | Lietuvių | 立陶宛语 |
| `lv` | Latviešu | 拉脱维亚语 |
| `et` | Eesti | 爱沙尼亚语 |
| `kk` | Қазақ тілі | 哈萨克语 |
| `uz` | O'zbek | 乌兹别克语 |
| `az` | Azerbaijan dili | 阿塞拜疆语 |
| `ka` | ქართული | 格鲁吉亚语 |
| `hy` | Հայերեն | 亚美尼亚语 |
| `be` | Беларуская | 白俄罗斯语 |
| `mk` | Македонски | 马其顿语 |
| `bs` | Bosanski | 波斯尼亚语 |
| `sq` | Shqip | 阿尔巴尼亚语 |
| `is` | Íslenska | 冰岛语 |
| `mn` | Монгол | 蒙古语 |
| `ne` | नेपाली | 尼泊尔语 |
| `si` | සිංහල | 僧伽罗语 |
| `km` | ខ្មែរ | 高棉语 |
| `lo` | ລາວ | 老挝语 |
| `my` | မြန်မာ | 缅甸语 |
| `jw` | Basa Jawa | 爪哇语 |
| `su` | Basa Sunda | 巽他语 |
| `af` | Afrikaans | 南非荷兰语 |
| `am` | አማርኛ | 阿姆哈拉语 |
| `ha` | Hausa | 豪萨语 |
| `yo` | Yorùbá | 约鲁巴语 |
| `so` | Soomaali | 索马里语 |
| `sn` | Chishona | 绍纳语 |
| `mg` | Malagasy | 马达加斯加语 |
| `ps` | پښتو | 普什图语 |
| `tg` | Тоҷикӣ | 塔吉克语 |
| `tk` | Türkmen | 土库曼语 |
| `tt` | Татар теле | 鞑靼语 |
| `ba` | Башҡорт | 巴什基尔语 |
| `ln` | Lingála | 林加拉语 |
| `gl` | Galego | 加利西亚语 |
| `cy` | Cymraeg | 威尔士语 |
| `la` | Latina | 拉丁语 |
| `mi` | Reo Māori | 毛利语 |
| `br` | Brezhoneg | 布列塔尼语 |
| `oc` | Occitan | 奥克语 |
| `lb` | Lëtzebuergesch | 卢森堡语 |
| `mt` | Malti | 马耳他语 |
| `fo` | Føroyskt | 法罗语 |
| `nn` | Nynorsk | 新挪威语 |
| `yi` | ייִדיש | 意第绪语 |
| `sd` | سنڌي | 信德语 |
| `as` | অসমীয়া | 阿萨姆语 |
| `bo` | བོད་ཡིག | 藏语 |
| `ht` | Kreyòl ayisyen | 海地克里奥尔语 |
| `haw` | Hawai'i | 夏威夷语 |
| `sa` | संस्कृतम् | 梵语 |

</details>

---

## 工具分类与使用场景

### 一、知识库浏览

#### loadFileTree — 获取文件列表

- **用途**：一次性获取当前用户知识库中的所有文件和子目录
- **参数**：无
- **关键返回**：`data` 为数组，每项字段：
  - `recordId`：节点 ID，用于 `fileDetailV2`；目录项还可作为 `parentId`
  - `fileId`：底层文件 ID，用于转写/总结/翻译/分享
  - `parentRecorId`：父目录 recordId
  - `name`：文件或目录名称
  - `type`：`file`=文件，`directory`=目录
  - `fileType`：文件业务类型，如 `upload_recording`
  - `status`：文件状态，取值见「文件状态 status 枚举」（2=成功，3=失败）
- **典型用法**：用户说「看看我有哪些录音」「找名字含 XX 的文件」时，调用本接口后在返回结果中按 `name` 筛选
- **说明**：返回扁平数组（不是嵌套树），可通过 `parentRecorId` 判断归属关系

#### fileDetailV2 — 获取文件详情

- **用途**：获取文件详情，包含转写内容、总结内容、任务状态；也是异步任务的轮询入口
- **参数**：`recordId`（必填，使用 `loadFileTree` 返回项的 `recordId` 字段，**不是 fileId**）
- **关键返回**：
  - `recordId` / `fileId`：文件 ID
  - `name`：文件名；未命名的录音返回录音时间（`yyyy-MM-dd HH:mm`）
  - `fileType`：文件业务类型
  - `status`：文件状态，取值见「文件状态 status 枚举」：-1=准备中，0=上传成功，1=转写中，2=成功，3=失败，4=转写成功，5=总结中
  - `durationSecs`：音频时长（秒）
  - `keyWords`：关键词
  - `transcribeJson`：转写内容 JSON 数组字符串（status=4 或 2 时有值），每项含 `speaker`/`start`/`end`/`text`
  - `summaryJson`：总结内容 JSON 字符串（status=2 时有值），含 `title`/`md2`（Markdown）/`mind2`（思维导图）/`keywords`
- **轮询用法**：提交异步任务后，每隔 3～5 秒调用本接口检查 `status`，直到 `status=2`（成功）或 `status=3`（失败）；`1`/`4`/`5` 为中间状态，需继续轮询

---

### 二、文件上传（三步走）

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
  - `parentId`（可选）：目标父目录 ID；从 `loadFileTree` 中 `type=directory` 项的 `recordId` 或 `mkdir` 返回值获取
  - `filesJson`（必填）：文件列表 JSON 数组，每项字段：
    - `fileName`（必填）：文件名含后缀，如 `meeting.mp3`
    - `fileType`（必填）：格式后缀，如 `mp3`/`m4a`/`mp4`/`pdf`/`docx`
    - `fileUrl`（可选）：文件公网 URL
    - `recordTime`（可选）：录音时间戳（毫秒），不传使用服务端当前时间
    - `sn`（可选）：设备 SN 号，手机录制传 `local`
- **关键返回**：`successFiles[]`，每项含 `recordId`（用于 `fileDetailV2` 轮询）和 `fileId`（用于 `commitTranscribeTask` 等处理接口）

---

### 三、转写与总结

#### commitTranscribeTask — 提交 ASR 转写任务

- **用途**：对音视频文件提交语音转文字任务（**异步**）
- **参数**：`requestJson`（JSON 字符串），字段：
  - `fileId`（必填）：⚠️ 底层文件 ID，使用 `loadFileTree` 返回项或 `uploadToKnowledge` 返回的 `fileId` 字段，**不是 `recordId`**
  - `language`（可选）：识别语言编码，取值见「支持的语言编码」（如 `zh`/`en`/`ja`/`zh-Hant`/`yue`）；不传自动检测
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
  - `fileId`（必填）：⚠️ 底层文件 ID，使用 `loadFileTree` 返回项的 `fileId` 字段，**不是 `recordId`**
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
  - `fileId`（必填）：⚠️ **使用 `loadFileTree` 返回项的 `fileId` 字段，不是 `recordId`**
- **说明**：服务端使用默认模型和详细总结（`more_details`）生成，无需传入其他参数
- **关键返回**：`{"success": true}` 表示任务已提交
- **注意**：会检查用户权益余量，不足时返回错误
- **后续**：用 `fileDetailV2` 轮询 `status`

---

### 四、翻译

#### translate — 翻译转写内容

- **用途**：对已转写完成的文件发起翻译（**异步**，同时触发重新总结，会覆盖原有总结内容）
- **参数**：`dtoJson`（JSON 字符串），字段：
  - `fileId`（必填）：⚠️ 底层文件 ID，使用 `loadFileTree` / `fileDetailV2` 返回的 `fileId` 字段，**不是 `recordId`**；服务端自动取该文件最新一次转写记录作为翻译源
  - `targetLanguage`（必填）：目标语言编码，取值见「支持的语言编码」（如 `zh`/`en`/`ja`/`ko`/`zh-Hant`/`yue`）；以 `-zh` 结尾的代码会自动转为 `zh`
- **前置条件**：文件 `status` 为 `4`（转写成功）或 `2`（成功）
- **关键返回**：新的 `transcribeId` 和 `summaryId`
- **后续**：用 `fileDetailV2`（传 `recordId`）轮询 `status`
- **⚠️ 高风险**：翻译会触发重新总结，**覆盖原有总结内容**，执行前须向用户确认

---

### 五、分享

#### createShare — 创建分享链接

- **用途**：为指定文件创建分享链接，返回 shareCode
- **参数**：
  - `shareType`（必填）：`audio`（音频）/ `localFile`（本地文件，如 PDF/Word）/ `translation`（翻译内容）
  - `params`（必填）：JSON 字符串，audio 类型字段：
    - `fileId`（必填）：⚠️ 底层文件 ID，使用 `loadFileTree` 返回项的 `fileId` 字段，**不是 `recordId`**
    - `tabs`：**无需传入**，服务端固定为 `summary`/`transcript`/`mindMap`，传入也会被覆盖
- **关键返回**：`data` 直接为 shareCode 字符串
- **⚠️ 高风险**：分享链接**无需登录即可访问**，会暴露文件标题、转写全文、总结及音频播放地址。执行前须向用户确认要分享的文件，并提醒用户链接可被任何持有者查看

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

### 六、文件管理

#### mkdir — 创建目录

- **用途**：在知识库中创建新目录（文件夹）
- **参数**：
  - `parentId`（可选）：父目录 ID；为空时在根目录创建；从 `loadFileTree` 中 `type=directory` 项的 `recordId` 获取
  - `dtoJson`（必填）：`{ "title": "目录名称", "color": "颜色标识（可选）", "icon": "图标标识（可选）" }`
- **关键返回**：`data` 为新创建目录的 recordId（Long），可作为后续接口的 `parentId`

---

## 典型使用流程

### 流程一：上传文件并转写总结

```
1. [可选] loadFileTree  → 找到目标目录（type=directory）的 recordId 作为 parentId，不传则上传到根目录
2. [可选] applyOssToken → 获取 COS 临时凭证（有公网 URL 可跳过）
3. [可选] 上传文件到 COS → 使用 credentials 直传文件
4. uploadToKnowledge    → 注册文件，记录返回的 recordId 和 fileId
5. commitTranscribeTask → 提交转写任务，fileId = 上一步的 fileId（⚠️ 不是 recordId）
6. fileDetailV2         → 传 recordId，每隔 3~5 秒轮询 status，直到 2（成功）或 3（失败）
```

### 流程二：翻译已有文件

```
1. loadFileTree    → 获取文件的 recordId 和 fileId
2. fileDetailV2    → 传 recordId，确认 status 为 4 或 2（已转写）
3. translate       → 传 fileId 和 targetLanguage（⚠️ 会覆盖原有总结，需用户确认）
4. fileDetailV2    → 传 recordId，轮询 status 直到 2（成功）或 3（失败）
```

### 流程三：创建分享并访问

```
1. loadFileTree   → 获取文件的 fileId
2. createShare    → shareType="audio"，params={"fileId": ...}，获取 shareCode（需用户确认）
3. getShare       → 使用 shareCode 访问分享内容（无需鉴权）
```

### 流程四：非音频文件（PDF/Word）总结

```
1. loadFileTree       → 获取文件的 recordId 和 fileId
2. localFileSummary   → 提交总结，传 fileId（⚠️ 不是 recordId）
3. fileDetailV2       → 传 recordId，轮询 status 直到 2（成功）或 3（失败）
```

### 流程五：整理知识库

```
1. loadFileTree       → 获取所有文件和子目录
2. mkdir              → 创建新目录，返回新目录的 recordId（可作为后续上传的 parentId）
```

---

## 错误处理

| 错误场景 | 处理方式 |
|---|---|
| `code` 非 200 | 向用户展示 `msg` 中的错误信息 |
| 权益不足（总结/翻译）| 提示用户权益已用完，需在 TicNote App 中购买 |
| 文件不存在 | 先检查是否把 `recordId` 和 `fileId` 传反了；确认无误后提示用户检查文件是否已被删除 |
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
