---
name: medlive-medical-qa
description: 医脉通医学问答。向医脉通医学问答服务提问医学问题并获取带文献引用链接的完整答案，支持多轮追问、文档问答（先用 medlive_upload_file 解析用户附件再提问）、历史答案回看与会话历史回顾（medlive_list_history）。当用户提出临床用药、适应症、剂量、禁忌、指南推荐、诊疗方案、病例分析等医学问题，或要求"照着这份文档/指南回答"、回顾之前的问答时使用。
---

# 医脉通医学问答

通过医脉通医学问答服务回答医学问题。答案由检索增强生成，适合临床用药、适应症、指南推荐、诊疗方案等场景。

## 认证

本连接器使用 OAuth 授权。用户首次连接时会打开浏览器登录医脉通账号并确认授权，**无需也不会让用户手动填写任何 Token**。

- 授权得到的凭证由 WorkBuddy 自动注入到请求头，AI **不要**在对话里询问、拼接或输出任何 Token。
- 遇到下列任一情况，按「授权已失效」处理：HTTP 401（`error: invalid_token`，缺 Bearer token），
  或工具返回 `isError: true` 且文案为「授权已失效，请重新连接本连接器以完成授权」。
  此时提示用户重新连接本连接器即可，**不要**尝试用其他方式自行绕过。

## 工具

### `medlive_ask`

向医学问答服务提问并获取完整答案。

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `query` | string | 是 | 用户的医学问题，最长 10000 字 |
| `chat_group_uuid` | string | 否 | 会话 uuid。**追问时必须传上一轮返回的值**以保持上下文；首次提问不传，服务会自动新建会话 |
| `model` | string | 否 | 检索模式，`simple`（默认）或 `medlive`（复杂检索，耗时更长） |
| `engine` | string | 否 | 检索数据源，逗号分隔；不传则用服务端默认值 |
| `file_uuids` | string[] | 否 | 要针对其提问的已上传文件 uuid，取 `medlive_upload_file` 的返回值（需为解析完成状态）；不传就是普通问答。同一会话的追问会继续带上已挂载的文档，不必重复传 |

返回值（文本形式）：

```
<完整答案>

---
log_uuid=<本次问答记录 uuid> chat_group_uuid=<会话 uuid>
```

`chat_group_uuid` 和 `log_uuid` 是后续追问与兜底必需，**在回答用户后记住它们**（`structuredContent` 里有同名字段，任取其一）；
这两个值属于程序元信息，**不要展示给用户**。

- 答案正文是已经渲染好的 Markdown（表格、`[1](https://...)` 引用链接都在里面）：**原样输出**，不要改写、总结、翻译或补充。
- 服务端判定无需检索（非医学问题、附件无文字、检索为空）时，话术作为正文正常返回，但 `structuredContent.no_answer = true`：照话术如实回复，不要补造医学结论。

### `medlive_upload_file`

把文档上传到问答服务并等待解析完成，返回 `file_uuid`；把它放进 `medlive_ask` 的 `file_uuids`，即可针对这份文档提问。上传与解析**不消耗配额**。

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `content` | string | 是 | 文件内容：完整 data URI（`data:application/pdf;name=指南.pdf;base64,<内容>`）或裸 base64 |
| `file_name` | string | 否 | 文件名，必须带扩展名；data URI 里带了 `name=` 时可省略 |

支持 pdf/doc/docx/txt 与 jpeg/png/jpg/webp/heic；pdf/doc/docx 单个不超过 50MB，其它不超过 10MB。
解析通常几秒到几分钟，工具会轮询到解析结束或超时：返回「文件仍在解析中」时**不要**拿去提问，稍后用同一个 `file_uuid` 重试。
先确认客户端能把附件按 data URI 传入；拿不到附件内容时本工具不可用，改用纯文本提问。

### `medlive_get_answer`

按 `log_uuid` 取回已生成并落库的答案。只读，不消耗配额。

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `log_uuid` | string | 是 | 问答记录 uuid，由 `medlive_ask` 返回 |

用途：`medlive_ask` 超时或流中断后的兜底；或回看历史问答。只能取回已存在的记录，不能用于提出新问题。

### `medlive_list_history`

按 `chat_group_uuid` 取回某个会话的问答历史**分页列表**。只读，不消耗配额。用于回顾一段对话、回答「我上次问了什么」「回顾这个会话」等；列表里某条需要完整答案时，用 `medlive_get_answer` 按它的 `log_uuid` 取详情。

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `chat_group_uuid` | string | 是 | 会话 uuid，由 `medlive_ask` 返回（追问时用的那个） |
| `page_size` | int | 否 | 每页条数，默认 5，最大 20 |
| `page_num` | int | 否 | 页码，从 1 开始，默认 1 |
| `order` | string | 否 | `desc`（默认，新的在前）或 `asc` |

返回值：会话信息 + 分页列表，每项含 `uuid`(=log_uuid)、`question`、`answer`（正文）、`created_at` 等。

- 列表按时间**倒序**，回顾时从第一页看最新问答；分页小步取（默认 5 条），避免一次拉全量。
- 它只列**已发生**的记录，不会发起新的问答，也不会消耗配额。

## 调用规则（重要）

1. **`medlive_ask` 会真实消耗提问用户的 M星/提问次数。** 同一个问题不要重复调用；能复用上一轮答案时不要重新提问。
2. **`medlive_ask` 是同步阻塞调用**，复杂问题可能需要 1~3 分钟：等待期间不要并发重复调用同一个问题。
3. **追问必须带 `chat_group_uuid`**，否则会新建会话、丢失上下文。用户说"接着上面问""那老年人呢"这类话时，属于追问。
4. 答案里若含「答案在流中断后从数据库取回」标注，说明本次是靠 `medlive_get_answer` 兜底取回的，内容完整可用。
5. **失败时如实转述**：工具返回的是可读错误文案（`isError: true`），把原始信息转述给用户并给出下一步（如用 `medlive_get_answer` 复核、或提示重新连接）；**不要**凭记忆补出医学结论。
6. **同一份文件只上传一次**：重复上传既慢又占服务端解析队列；解析未完成的文件不要拿去提问。
7. **`medlive_get_answer` / `medlive_list_history` 只读、不消耗配额**：回顾历史优先用 `medlive_list_history` 定位，需要某条完整答案再 `medlive_get_answer`；二者都不会新建会话。

## 典型调用

首次提问：

```json
{
  "name": "medlive_ask",
  "arguments": { "query": "阿司匹林的主要适应症是什么" }
}
```

追问（沿用上一轮的 `chat_group_uuid`）：

```json
{
  "name": "medlive_ask",
  "arguments": {
    "query": "那老年患者的剂量需要调整吗",
    "chat_group_uuid": "<上一轮返回的 chat_group_uuid>"
  }
}
```

上传文档后针对它提问（两步）：

```json
// 1) 上传，返回 structuredContent.file_uuid
{
  "name": "medlive_upload_file",
  "arguments": { "content": "data:application/pdf;name=中国脑卒中防治指导规范.pdf;base64,<base64>" }
}
// 2) 带着 file_uuid 提问
{
  "name": "medlive_ask",
  "arguments": { "query": "这份文档里推荐的食盐摄入量是多少", "file_uuids": ["<file_uuid>"] }
}
```

兜底取回：

```json
{
  "name": "medlive_get_answer",
  "arguments": { "log_uuid": "<medlive_ask 返回的 log_uuid>" }
}
```

回顾会话历史（分页，新的在前）：

```json
{
  "name": "medlive_list_history",
  "arguments": { "chat_group_uuid": "<会话 uuid>", "page_size": 5, "page_num": 1 }
}
```

## 禁止事项

- 不要把本连接器当作通用搜索引擎或非医学问题助手使用。
- 不要代替医生给出确诊结论；回答需保留来源依据，并提示以临床判断为准。
- 不要在未获得用户明确意图时批量、循环调用 `medlive_ask`（会持续消耗配额）。
