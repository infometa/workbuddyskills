---
name: youcai-media
display_name: 有彩AI媒体创作
display_name_en: Youcai AI Media Creation
description: 使用有彩AI连接器生成图片、视频、语音、音效和音乐，查询模型价格、跟进视频任务并交付素材。适用于真实媒体创作；不用于媒体分析、现有音视频剪辑或仅撰写提示词。
description_zh: 通过有彩AI选择模型、生成媒体并获取结果，正确处理授权、人民币计费、异步视频和请求重试。
description_en: Use the Youcai AI connector to select models, generate media and retrieve results, with correct handling of authorization, CNY billing, asynchronous video tasks and retries.
version: 1.0.0
author: 有彩AI
---

# 有彩AI媒体创作

使用已连接的有彩AI MCP 工具完成用户要求的媒体创作。服务地址为 https://youcai.art/api/mcp 。工具在客户端中可能带服务前缀，以下名称指实际工具名；使用已发现的工具，不自行拼接 HTTP 请求或读取本地凭据。

## 连接与创作边界

- 未连接或授权失效时，引导用户在 WorkBuddy 中连接有彩AI并完成浏览器授权。账户须满足网站公共 API 资格，并在 https://youcai.art/profile/api 建立有效 API Key 记录供授权绑定；不要让用户在聊天或连接配置中粘贴 Key、授权码或访问/刷新令牌。
- 真实生成消耗有彩AI账户人民币余额，不消耗网站积分。首次创作或费用相关问题中说明此点；先查看当前价格，不承诺免费，不用积分价格代替人民币价格。
- 用户明确要求生成时，在其数量、规格和预算范围内执行；仅询问能力、价格、方案或提示词时，不发起付费生成。不自行追加多份作品、提升高价规格或重做失败任务。
- 仅使用当前授权可见的工具。只有 `list_models` 时，不能声称已经获得生成权限；按所需能力引导用户重新授权，不自动扩大范围。
- 本连接器没有媒体分析、文字聊天、网页搜索、素材上传、通用剪辑、音轨混音、充值或 API Key 管理工具。没有可用上传工具时，请用户提供真实可访问且有权使用的 HTTPS 素材链接，不将本地路径、网页链接或 Base64 当作素材文件 URL。

## 先选模型，再组织参数

1. 读取客户端提供的工具 `inputSchema`，调用 `list_models`，参数为 `{}`。使用返回 `structuredContent.models` 中与需求匹配的模型。
2. 阅读所选模型的 `capabilities`、`parameters`、`constraints` 与 `pricing`；以本次返回为准，不记死模型名、参数枚举或价格。
3. `model` 是必填字符串，填目录中的精确模型 ID；每次新创作的 `idempotency_key` 是必填非空字符串，最多 128 字符，建议唯一 UUID。其他创作字段只传该模型支持的字段，条件必填项按其规则补齐。
4. 参考素材不足或会改变作品的关键要求不清时再询问。非关键参数可采用模型声明的默认值；不要为了“填全参数”猜测值，也不要把 `parameters`、`constraints`、价格元数据整体传给生成工具。

## 工具选择

以下生成工具均须包含 `model` 和 `idempotency_key`。具体长度、数量、枚举与默认值，以当前工具 Schema 和模型规格共同确定。

| 工具 | 用途及主要参数 |
|---|---|
| `list_models` | 不执行创作，参数 `{}`；查询图片、视频、语音、音频、音乐模型和人民币价目。 |
| `generate_image` | 静态图生成或参考图编辑；`prompt` 为必填字符串，`image_urls` 为可选 HTTPS 图片字符串数组。`size` 为可选字符串，`n` 为可选整数，默认 1，数量仍受模型限制。编辑时写清保留内容和修改目标。 |
| `generate_video` | 提交异步视频；`prompt` 为必填字符串。`mode` 可为 `text`、`first_frame`、`first_last_frame`、`reference`；素材分别放入可选 `image_urls`、`video_urls`、`audio_urls` 数组。`duration` 为可选整数秒数，默认 5，但必须满足模型/模式范围。不要把参考素材当作待剪辑列表。 |
| `get_video` | 查询已有视频任务；必填字符串 `id` 取生成返回的 `task_id`，不是 `request_id` 或素材 ID。 |
| `get_video_content` | 获取成功视频的永久链接；必填字符串 `id` 仍取 `task_id`。 |
| `cancel_video` | 仅在用户要求停止该视频任务时调用；必填字符串 `id` 取 `task_id`。取消是否成功以返回状态为准，不等于删除成片。 |
| `generate_speech` | 将已写好的文字变成旁白或朗读；`input` 为必填正文字符串。预置音色用 `voice`，音色设计用 `voice_description`，声音克隆用 `voice_sample_url`，均为字符串且按模型条件必填，不混用。正文与风格要求分开，返回 WAV 素材链接。 |
| `generate_audio` | 音效、声音场景或带台词、音乐、环境音的短音频故事；`prompt` 为必填字符串，可在其中描述声音时序。可选 `references` 为对象数组，具体结构查 Schema。音频参考仅用于音色，不能当多轨混音输入；图片参考模式须填实际朗读正文，不与音频参考混用。 |
| `generate_music` | 歌曲、配乐或纯音乐；`prompt` 为必填风格字符串，`lyrics` 为可选歌词字符串。`instrumental` 为可选布尔值，默认歌曲模式；纯音乐设 `true` 并省略歌词。不是歌曲翻唱或现有音轨混音。 |

视频模式不能只看素材数量机械选择：一张图作为首帧时用 `first_frame`；作为形象/风格参考而非首帧时，须确认模型支持并显式使用 `reference`。首尾帧模式恰好两张图，顺序为首帧、尾帧。

## 典型执行路径

- “生成咖啡品牌海报”：查询 image 模型及价格 → 整理主体、构图、风格与需要出现的文字 → 新幂等键调用 `generate_image` → 交付真实图片链接。未要求多张时默认一张。
- “把这张图做成 5 秒视频”：取得合法图片 URL → 选择支持首帧和所需时长的 video 模型 → 新幂等键提交 `generate_video` → 保存 `task_id` → 查询完成后交付视频；不能用反复提交来查进度。
- “把文案配成旁白”：保留用户正文作为 `input`，选择 speech 模型和合法音色；“温暖自然”等要求放入模型支持的风格字段，而非混入朗读正文。
- “做一个带旁白、配乐和雨声的短故事”：优先选择支持需求的 audio 模型，在一个 `prompt` 里写清台词及声音先后关系，避免无必要地拆成多次收费调用；纯音乐需求则使用 `generate_music`。

## 结果交付与异步任务

- 读取 `structuredContent` 的业务状态，同时检查 `isError`；工具调用返回不等于媒体生成成功。
- `status` 为 `succeeded` 且有 `assets` 时，交付实际 `assets[].url` 或返回的 `resource_link`，说明素材类型。必要时附 `asset_id`、`request_id`；不要编造链接或声称文件已保存到用户电脑。
- 视频返回 `queued` / `in_progress` 时，保留 `task_id`，稍后使用 `get_video` 查询，避免连续密集轮询。`succeeded` 后交付已返回的素材，或用 `get_video_content` 获取结果；`failed` / `cancelled` 停止轮询。
- 客户端不能继续等待时，如实报告任务仍在处理并保留任务 ID；不要声称已经生成，也不要承诺未配置的后台通知。
- 费用以返回 `billing` 为准，币种为 `CNY`；`reserved_amount` 是预留金额，不当作最终 `amount`。缺失金额时说明未返回，不猜测为零。

## 重试与异常处理

- 同一次创作遇到网络超时、断线、刷新授权令牌或 `request_in_progress`，保留相同幂等键及完整参数。结果不明时不得自动换键重试，避免重复消费；已有视频任务 ID 时先查询原任务。
- 同键只会续接或重放原请求，不会重新创作。确认失败后，只有用户决定重做或已有明确重试授权时，才用新键重新调用；修改参数也是新创作，须在授权范围内使用新键。
- 重新连接但授权记录未变与重新授予一条新授权不是同一情况：幂等按授权隔离。重新授权后不要假定旧键仍能防重复，先核查原任务/请求。
- `401`：交由客户端刷新或让用户重新连接；不要索取令牌。`403` / `insufficient_scope`：说明缺少的能力，引导重新授权；不能绕过。
- 参数或模型错误：重读当前 Schema 与模型目录。参考素材错误：核对 HTTPS 文件地址、可访问性和素材权限，不编造链接。
- 人民币余额不足：引导用户到网站处理，不自行充值。服务错误或结果仍不明：提供返回的 `request_id` 供网站支持核查，不转述供应商内部信息或无限重试。

公开接入说明：https://youcai.art/docs/api/mcp
