---
name: infimind-video-generation
display_name: 极睿视频生成
display_name_en: Infimind Video Generation
description: 根据用户提供的文本与媒体素材，通过极睿视频完成视频生成预检、费用确认、任务创建和状态跟踪。
description_zh: 适用于极睿视频的文生视频、图生视频、首尾帧、多模态参考和视频编辑，并在正式扣费前完成预检与单独授权。
description_en: Create and track Infimind videos from text, images, video, or audio, with preflight validation and separate authorization before any billable task.
category: design # 暂用分类；最终枚举待 WorkBuddy 团队确认
version: 1.0.0
author: 极睿科技（Infimind）
permissions:
  provisional: true
  read:
    - "仅限当前对话中用户主动选择的图片、视频和音频"
  network:
    - "仅通过已启用的极睿视频 Connector 调用 get_user_info、create_video_task 与 get_video_status"
---

# 极睿视频生成

## 能力范围

本 Skill 使用 `infimind-video` Connector 提供的以下工具：

- `get_user_info`：检查 Token、可用积分和 VIP 状态；不接收参数。
- `create_video_task`：预检或创建视频任务；`dryRun: true` 只校验与估算，`dryRun: false` 才正式创建。
- `get_video_status`：使用正式创建返回的 `taskId` 查询任务状态。

视频内容拆解、脚本提取或卖点分析应改用 `infimind-video-analysis`。

## 适用场景

- 根据文字生成视频，或用单张图片驱动画面。
- 用首帧与尾帧控制镜头过渡。
- 组合多张图片、参考视频或音频生成视频。
- 用多张人物、商品或场景图片保持参考一致性。
- 基于一个视频和可选参考图完成视频编辑。
- 查询当前对话中已创建任务的进度和结果。

## 非适用场景

- 用户只想分析已有视频而不生成新视频。
- 素材不在当前对话中、路径不可访问，且用户未提供安全的公网 HTTP/HTTPS URL。
- 用户要求绕过积分、VIP、版权、安全审核或平台限制。
- 用户未确认对素材拥有必要权利，或请求涉及明显违法、侵权、欺诈、骚扰、色情及其他敏感内容。
- 用户只询问创意建议且没有要求创建任务；此时直接提供文字建议，不调用付费工具。

## 事实与合规边界

1. 只把工具真实返回的 `taskId`、状态、积分估算、警告、结果链接和错误作为事实，不编造任务、进度或成功结果。
2. 不宣称对版权或肖像权作出法律判定。若素材包含第三方作品、商标、音乐或人物，先提醒用户确认已经获得必要授权。
3. 涉及公众人物时，不帮助制作误导性政治传播、虚假新闻、冒充、诈骗或虚假代言；不把合成内容描述为真实拍摄。
4. 对未成年人、裸露、暴力、仇恨、违法活动和其他敏感内容采取保守判断；无法确认合规时停止创建并说明原因。
5. 不主动扩展素材用途，不上传当前任务不需要的文件，不把用户媒体用于训练或其他未授权目的。
6. Token 只应在 WorkBuddy Connector 凭证设置中填写。不得索取或要求用户在对话中粘贴 Token，也不得回显、记录或写入示例。

## 输入检查

正式调用前逐项确认：

1. 明确用户要生成的内容、用途、时长、画幅、清晰度、语言和声音要求；缺失的关键条件先询问。
2. 本地素材必须来自用户在当前对话中主动选择的文件；远程素材只接受可安全读取的公网 HTTP/HTTPS URL，不猜测本地路径。
3. 视频支持 MP4/MOV，音频支持 MP3/WAV。私网、localhost、`file:` URL 或无法安全访问的远程文件应停止处理并请用户更换。
4. 逐项核对素材数量、顺序和模型限制。首尾帧中第一张必须是首帧；引用 `@imageN` 时必须与图片顺序一致。
5. 调用 `get_user_info` 检查账户、积分与 VIP 状态。SD、HA 需要 VIP；不满足时说明限制，不静默切换模型。
6. 对视频或音频预检，尽量提供与素材顺序一一对应的时长数组，否则可能无法得到积分估算。

## 模型与任务模式

| 用户目标 | `model` | `taskMode` | 素材字段 | 关键限制 |
|---|---|---|---|---|
| 普通文生视频、单图生视频 | `SA` | 不传 | `sourceImage` 可选 | 10 或 15 秒；不要传 `resolution` |
| 多图片、视频、音频综合参考 | `SD` | `allinone` | `sourceImages`、`sourceVideos`、`sourceAudios` | 最多 9 图、3 视频、3 音频；5/10/15 秒 |
| 首尾帧过渡 | `SD` | `firstlast` | `sourceImages` | 第一张是首帧，最多 2 张且首帧必填 |
| HA 文生或单图生成 | `HA` | `standard` | `sourceImage` 可选 | 5/10/15 秒，可设置 `ratio` |
| HA 多图人物或商品参考 | `HA` | `reference` | `sourceImages` | 最多 9 图；提示词保留 `@imageN` 标记 |
| HA 视频编辑 | `HA` | `edit` | `sourceVideos`、可选 `sourceImages` | 最多 1 个视频和 5 张图；时长由输入视频决定 |

优先使用 `model: SA | SD | HA`。`route: S2 | S5 | S6` 只是旧客户端兼容字段，新请求不要使用。

## 工具参数

### `get_user_info`

不传参数。只使用返回的账户状态、积分与 VIP 信息进行资格判断，不展示敏感凭证。

### `create_video_task`

- `prompt`：必填，描述主体、动作、场景、镜头、光线、风格和声音；不擅自加入用户没有要求的人物、品牌或事实。
- `sourceImage`：单图入口；适用于 SA 或 HA standard。
- `sourceImages`：多图入口；顺序必须与首尾帧或 `@imageN` 引用一致。
- `sourceVideos` / `sourceAudios`：多模态参考素材数组。
- `sourceVideoDurationSeconds` / `sourceAudioDurationSeconds`：与对应素材按顺序匹配的时长数组，用于提高预检估算完整性。
- `size`：仅传服务支持的枚举值；不要从自然语言猜造未支持尺寸。
- `seconds`：仅传 5、10 或 15，并服从模型限制。
- `language`：按用户期望的提示词或音频语言填写。
- `count`：1 至 12；多条结果会增加消耗，必须纳入费用确认。
- `model`：`SA`、`SD` 或 `HA`；选择依据见上表。
- `taskMode`：与模型组合匹配，不传未定义模式。
- `resolution`：仅在支持的模型与模式中使用；SA 不传。
- `ratio`：按用户确认的画幅填写；不可与不兼容的尺寸组合。
- `generateAudio`：只有用户明确需要生成声音时开启。
- `webSearchEnabled`：只有用户明确需要联网补充信息且场景合规时开启。
- `dryRun`：预检固定为 `true`；获得独立费用授权后，正式创建才设为 `false`。

### `get_video_status`

只传正式创建返回的 `taskId`。不得猜测 ID，也不得用预检结果或其他用户的任务 ID 查询。

## 费用授权

1. 先以最终参数调用一次 `create_video_task`，设置 `dryRun: true`。
2. 展示预检返回的 `estimatedCredits`、`validationWarnings`、权限限制和素材错误；明确说明这一步没有创建任务。
3. 如果没有返回积分估算，明确说明“当前无法提供具体数值，但正式创建会消耗积分”，不得编造估算。
4. 向用户单独询问是否接受本次消耗并创建任务。最初的“生成”“创建”“直接做”不等于预检后的扣费授权。
5. 用户拒绝、未回复或授权不明确时，不得正式创建。
6. 只有收到清晰肯定答复，才使用已经展示过的业务参数创建一次正式任务，并把 `dryRun` 改为 `false`。
7. 用户更改模型、时长、数量、素材或其他影响消耗的参数时，重新预检并重新取得授权。

## 状态与错误处理

- 正式创建成功后保存真实 `taskId`，只查询这一 ID，直到服务返回 `completed` 或 `failed`。
- `pending` / `processing`：简要报告工具返回的真实状态或进度；没有进度值时不要自行估算百分比。
- `completed`：返回所有可用视频链接、缩略图和工具明确给出的部分失败信息。
- `failed`：保留可安全展示的 `errorCode`、`errorCategory`、错误摘要和 `retryable`，不暴露内部凭证或堆栈。
- 超时或网络结果不明确：有 `taskId` 时先查询原任务；不知道是否创建成功时不要再次创建。
- 任何可能再次扣费的重试，都要说明风险并获得新的单独确认。
- 鉴权失败：引导用户访问 `https://aigc-next.iclip.cn/mcp-tokens` 撤销失效 Token 或创建新 Token，再到 Connector 设置更新凭证并重新连接。

## 输出模板

### 预检结果

- 模型与模式：工具实际接受的值
- 时长、画幅和数量：最终参数
- 预计消耗：`estimatedCredits`，未返回则明确写“当前不可估算”
- 警告与限制：`validationWarnings` 及可操作的修正建议
- 下一步：等待用户明确确认，不写成已经创建

### 正式结果

- 任务 ID：真实 `taskId`
- 最终状态：工具返回值
- 视频与缩略图：逐项列出可用链接
- 异常：说明失败子任务或安全的错误信息

## 示例

用户说“用两张人物参考图生成 10 秒 9:16 走秀视频”，应选择 `model: HA`、`taskMode: reference`、`sourceImages`、`seconds: 10`、`ratio: 9:16`。先完成账户与素材检查，再以 `dryRun: true` 预检；展示预计积分和警告，得到单独确认后仅创建一次，最后使用返回的 `taskId` 查询状态。

For English requests, follow the same input validation, account check, dry-run disclosure, separate post-check authorization, single creation, and status-polling sequence. Return user-facing results in English and never request a token in chat.
