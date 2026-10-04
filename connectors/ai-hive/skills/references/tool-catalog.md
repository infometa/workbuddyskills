# AI-HIVE 工具目录（references/tool-catalog.md）

适用版本：AI-HIVE Connector 1.1.4 / `@infimind-next/ai-hive-mcp@latest`
更新日期：2026-08-21

> 本表依据 npm 当前 `@latest`（核对时为 0.2.5）的实际发布 tarball。Connector 保持引用 `@latest`；如果未来工具 schema 变化，应先核对真实发布物，再同步更新本表。

## 工具清单（7 个）

| 名称 | 类型 | 分类 | 主要副作用 |
|---|---|---|---|
| `get_user_info` | 只读 | 账户 | 无 |
| `list_models` | 只读 | 模型 | 无 |
| `upload_media_from_path` | 写 | 媒体 | 上传文件并返回 `mediaId` |
| `chat_text` | 计费 | 文本 | 调用文本模型并按服务端规则计费 |
| `generate_image` | 计费 | 图片 | 创建图片任务并按服务端规则计费 |
| `generate_video` | 计费 | 视频 | 创建视频任务并按服务端规则计费 |
| `get_generation_task` | 只读 | 任务 | 查询图片或视频任务状态与结果 |

## 通用模型参数约定

调用 `chat_text`、`generate_image` 或 `generate_video` 时，以下三项必须来自同一次 `list_models` 返回的同一模型与路由：

- `publicModelId`：当前模型 ID。
- `routingMode`：`COST_FIRST` / `SPEED_FIRST` / `SUCCESS_FIRST` 中该模型实际提供的值。
- `pricingSnapshot`：对应模型与路由的价格快照，原样传入，不自行构造或修改。

模型专属的分辨率、画幅、时长、质量、声音开关等不作为顶层字段，统一放入 `params`，并严格使用 `list_models` 当前返回配置允许的键、类型和值。

## 详细参数表

### `get_user_info`

不接收参数；返回当前账户与余额摘要。

### `list_models`

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `modelType` | string | 可选 | `TEXT` / `IMAGE` / `VIDEO`；不传时请求不带类型筛选参数 |

### `upload_media_from_path`

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `path` | string | ✅ | 用户明确授权的本地文件绝对路径 |
| `filename` | string | 可选 | 覆盖上传文件名；通常省略 |
| `contentType` | string | 可选 | 覆盖 MIME 类型；不确定时省略，由客户端根据内容或扩展名识别 |

当前客户端支持：PNG/JPEG/WebP；MP3/WAV；MP4/WebM/MOV；PDF/TXT/MD/CSV/JSON/DOCX/XLSX。图片与文档单文件最大 10MiB，音频单文件最大 15MiB，视频单文件最大 100MiB。上传成功后音频返回 `mediaType=AUDIO`；显式 `contentType` 会先 trim 并转为小写，不确定时应省略，不要伪造 MIME。

### `chat_text`

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `publicModelId` | string | ✅ | 来自 `list_models` |
| `routingMode` | string | ✅ | 来自选中模型的当前路由 |
| `messages` | array | ✅ | 至少一条；每条含 `role`、非空 `content` 与可选 `mediaIds` |
| `thinkingEnabled` | boolean | 可选 | 是否启用模型思考能力；仅在模型支持时使用 |
| `pricingSnapshot` | object | ✅ | 对应模型与路由返回的快照，原样传入 |

消息 `role` 只能是 `system`、`user` 或 `assistant`。媒体附件放在对应消息的 `mediaIds` 中。`chat_text` 不接受音频，不要把 `AUDIO` 类型的 `mediaId` 放入消息。

### `generate_image`

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `publicModelId` | string | ✅ | 来自 `list_models(modelType="IMAGE")` |
| `routingMode` | string | ✅ | 来自选中模型的当前路由 |
| `prompt` | string | ✅ | 非空图片描述 |
| `batchSize` | integer | 可选 | 1–10，默认 1；候选数量会影响费用 |
| `imageMediaIds` | array | 可选 | 参考图片的 `mediaId` 列表 |
| `params` | object | 可选 | 当前模型支持的画幅、分辨率、质量等参数 |
| `pricingSnapshot` | object | ✅ | 对应模型与路由返回的快照，原样传入 |

### `generate_video`

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `publicModelId` | string | ✅ | 来自 `list_models(modelType="VIDEO")` |
| `routingMode` | string | ✅ | 来自选中模型的当前路由 |
| `prompt` | string | ✅ | 非空视频描述 |
| `imageMediaIds` | array | 可选 | 参考图片的 `mediaId` 列表 |
| `videoMediaIds` | array | 可选 | 参考、编辑或延长所用视频的 `mediaId` 列表 |
| `audioMediaIds` | array | 可选 | 外部参考音频的 `mediaId` 列表；默认空数组，仅用于当前模型配置明确支持的组合 |
| `firstFrameMediaId` | string | 可选 | 首帧图片 `mediaId` |
| `lastFrameMediaId` | string | 可选 | 尾帧图片 `mediaId` |
| `params` | object | 可选 | 当前模型支持的时长、画幅、分辨率、声音等参数 |
| `pricingSnapshot` | object | ✅ | 对应模型与路由返回的快照，原样传入 |

外部参考音频、Prompt 中的声音描述和 `params` 中的原生声音开关是三类不同输入：音频文件上传后放入 `audioMediaIds`；台词、音效、BGM 需求写入 Prompt；原生声音开关只使用当前模型配置明确暴露的 `params` 键值。模型不支持参考音频时保持 `audioMediaIds=[]`，不能用 Prompt 或开关冒充外部音频素材。

### `get_generation_task`

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `taskId` | string | ✅ | `generate_image` 或 `generate_video` 的真实返回值 |

任务状态使用 `PENDING`、`SUBMITTED`、`PROCESSING`、`COMPLETED`、`FAILED`。失败条目可能包含 `failure.code`、`failure.summary` 与 `failure.suggestion`；只展示安全字段，不输出内部诊断。
