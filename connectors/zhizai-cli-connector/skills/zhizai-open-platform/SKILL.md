---
name: zhizai-open-platform
version: 1.0.0
description: |
  通过智在记录开放 API 连接笔记数据：鉴权、检索/问答/总结（动态模版路由）、笔记 CRUD、场景与知识卡、笔记集、团队、消息与录音卡。
  用户要查笔记、写周报/复盘、新建编辑删除笔记、管团队/笔记集/录音卡，或配置 ZHIZAI_REC_API_KEY 时使用。
  基准地址为常量 ZHIZAI_BASE_URL；鉴权 Header 直接传 Key（无 Bearer）。
metadata:
  openclaw:
    emoji: "📒"
    requires: {}
    optionalEnv:
      - ZHIZAI_REC_API_KEY
---

# 智在记录 · 开放平台

让用户在当前 AI 中用自然语言访问智在记录：检索与总结、维护笔记、管理场景/笔记集/团队与录音卡。本 Skill 理解意图、加载对应领域参考，再按官方 REST API 执行真实操作。

## 能力与外部影响

- 按用户请求调用 `https://openapi.zzjilu.com/api/v1` 下的开放接口，读取或修改当前 API Key 对应账号的数据。
- 鉴权依赖环境变量 `ZHIZAI_REC_API_KEY`（请求头 `Authorization` 直接传 Key，**不要**加 `Bearer`）。
- 新建/编辑/删除笔记、加人删团队、发消息等会修改远端数据，须遵守下方确认规则。
- 限流最高 **2 次/秒**；连续调用宜间隔 ≥500ms。
- 不会自行安装其他软件、下载覆盖本 Skill，或在回复中泄露完整 Key。

## 能力概览

| 用户想做什么 | 典型说法 | 完成后应返回什么 |
| --- | --- | --- |
| 基于笔记问答/总结 | “本周会议总结一下”“帮我写周报” | 按模版或语义结构整理的真实结论；无笔记时诚实说明 |
| 查找笔记 | “最近有哪些录音”“找一下报销相关” | 真实 `id`、标题、中文类型、时间、摘要/总结 |
| 新建/上传笔记 | “存这篇文档”“记一条文本” | 真实笔记 ID、标题、`note_state`；未完成时说明进度 |
| 改删与进度 | “改标题”“删掉这条”“处理完了吗” | 最终状态；删除/覆盖先确认；进度≠正文 |
| 场景与知识卡 | “有哪些总结场景”“看知识卡” | 真实场景/卡片列表，可用 ID |
| 笔记集 | “我创建的笔记集”“打开某某集” | 真实知识库名称、ID、集内条目 |
| 团队 | “建个团队”“加个成员” | 真实团队/成员 ID；危险操作先确认 |
| 录音卡 / 发消息 | “查一下这张卡”“给某某发消息” | 用量/连接状态或发送结果；敏感字段脱敏 |
| 连接与鉴权 | “配置 Key”“用口令换 Key” | Key 是否可用；口令换 Key 不展示完整密钥 |

不要要求用户记接口路径。用户用自然语言表达目标即可。

## 首次连接

1. 检查 `ZHIZAI_REC_API_KEY` 是否已配置且非空。未配置：只提示配置该变量，并推荐 [智在记录开发者](https://www.zzjilu.com/pc/developer)；不继续调业务接口。
2. 用无写入验收：`POST /note/queryNoteList`，`pageNum=1`、`pageSize=1`。`resultCode=="0"` 才可说已连接。
3. 只有用户同意时才创建测试笔记；必须返回真实 `id`、标题与 `note_state`。
4. 本会话已成功调用过任一接口后，可不再重复强调 Key 检查。

常量（非环境变量）：`ZHIZAI_BASE_URL` = `https://openapi.zzjilu.com/api/v1`。下文路径均接在该基准之后。

## 每次任务的执行闭环

1. **理解目标**：对象、动作、时间范围与输出版式；指代不清时先澄清。
2. **加载领域参考**：只读取本次任务涉及的 `references/*.md`，不要凭印象猜路径、参数或返回字段。
3. **确认真实 ID**：笔记、场景、笔记集、团队、成员等一律使用接口返回的真实 ID；重名时让用户选择。
4. **按官方 API 调用**：JSON 用 `content-type: application/json`；上传用 `multipart/form-data`；遵守限流。
5. **判断结果**：先看 HTTP（400/401/406=无权限），再看 `resultCode=="0"`；异步创建用 `queryNoteStatus` 轮询，不能把“已提交”说成“已完成”。
6. **必要时复读**：更新、删除、归档类操作后按需再查列表/详情确认最终状态。
7. **回复用户**：先结论，再给必要字段；失败说明原因与下一步，不泄露 Key/`stack`。

## 路由

匹配用户意图后，**必须读取并遵循**对应领域参考：

- 鉴权、口令换 Key、解析 token：[`references/auth.md`](references/auth.md)
- 笔记检索/问答/总结（含动态模版）、CRUD、上传下载：[`references/note.md`](references/note.md)
- 场景与知识卡：[`references/scene.md`](references/scene.md)
- 笔记集（我创建/我收到/详情）：[`references/knowledge.md`](references/knowledge.md)
- 团队与成员：[`references/team.md`](references/team.md)
- 消息与录音卡：[`references/msg-device.md`](references/msg-device.md)

多领域任务按步骤依次读取。例如“按场景总结本周会议笔记”先读 `note`（模版管线），需要 `sceneId` 时再读 `scene`。

边界模糊且答案依赖笔记内容时：**默认走 `note` 中的动态模版管线**。

## 结果呈现标准

- **总结/问答**：按最终选用模版填充真实笔记；缺失标「未提及」；不默认整段贴出模版原文。
- **笔记列表**：`id`、`title`、中文类型、`create_time`；有 `summary` 用总结否则 `abstract`。`note_type` 必须转中文（见 `note.md`）。
- **新建成功**：返回真实 ID、标题、`note_state`；`pending` 等说明处理中并可查进度。
- **进度查询**：只报告系统处理阶段，不当作正文内容。
- **空结果**：柔和说明未找到及相关检索范围，可建议换词/调时间，禁止编造。
- **失败**：用户能理解的短句 + 可执行下一步；禁止展示完整 Key、`stack`、未脱敏 `errorInfos`。

## 统一规则

- 真实操作只走开放 API；字段与 curl 以对应 `references/*.md` 的「接口协议」为准。
- `resultCode != "0"` 一律失败；优先用 `resultMsg` 短句说明。
- ID、fileId 始终按返回原样传递，禁止臆造。
- 修改笔记路径为 **`POST /note/updateNoteInfo`**（不是 `updateNote`）；摘要请求字段为 `abstractContent`。
- 删除笔记、删团队/成员、发消息、覆盖性修改须先确认。
- 群聊或共享会话中不主动展开私密全文与手机号。
- 口令换 Key：口令与返回的 Key **禁止**在对话中完整展示。

## 常见恢复方式

- HTTP 400/401/406 或鉴权失败：读 `references/auth.md`，检查 `ZHIZAI_REC_API_KEY`，引导开发者页，不回显 Header。
- 限流：等待后重试，不高频循环。
- 笔记不存在 / 非录音却下音频：说明真实原因，改用正确 ID 或接口。
- 创建后长期 `pending`：用 `queryNoteStatus` 查询，提示稍后查看，不伪造已完成总结。
- 网络中断或结果不确定：只做查询核验，不自动重复写入。
