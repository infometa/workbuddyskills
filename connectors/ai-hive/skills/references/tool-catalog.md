# AI-HIVE 工具目录（references/tool-catalog.md）

适用版本：AI-HIVE Connector 1.0.0 / `@infimind-next/ai-hive-mcp@0.2.1`
更新日期：2026-07-31

## 工具清单（7 个）

| 名称 | 类型 | 分类 | 主要副作用 |
|---|---|---|---|
| `get_user_info` | 只读 | 账户 | 无 |
| `list_models` | 只读 | 模型 | 无 |
| `upload_media_from_path` | 写 | 媒体 | 上传文件并返回 `mediaId` |
| `chat_text` | 计费 | 文本 | 调 LLM，按服务端计费扣费 |
| `generate_image` | 计费 | 图片 | 创建任务，按服务端计费扣费 |
| `generate_video` | 计费 | 视频 | 创建任务，按服务端计费扣费 |
| `get_generation_task` | 只读 | 任务 | 查询图片/视频任务状态与结果 |

## 通用参数约定

- `kind`（出现在 `list_models`）：取值为 `text | image | video`，与各 SKILL 的默认范围一致。
- `model`（出现在 `chat_text / generate_image / generate_video`）：必须是 `list_models` 返回的对象（含 `publicModelId` 与 `pricingSnapshot`），客户端不得自行构造或修改。
- `taskId`（出现在 `get_generation_task`）：必须使用对应 `generate_*` 工具的**真实返回值**，不得用预检结果、他人的任务 ID 或猜测值。

## 详细参数表

### `get_user_info`

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| — | — | — | 不接收任何参数；返回账户与余额摘要 |

### `list_models`

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `kind` | string | 可选 | 服务端默认 | 资源类型：`text` / `image` / `video` |
| `cursor` | string | 可选 | 空 | 分页游标；非空时返回下一页 |

### `upload_media_from_path`

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `path` | string | ✅ | — | 用户明确授权的本地文件绝对路径 |
| `kind` | string | 可选 | 服务端推断 | 资源类型；图片填 `image`，视频填 `video` |

返回 `mediaId`，必须在 `generate_image` / `generate_video` 中引用。

### `chat_text`

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `model` | object | ✅ | — | 来自 `list_models` 的模型引用 |
| `messages` | array | ✅ | — | 对话历史与本轮输入 |
| `stream` | boolean | 可选 | `false` | 是否流式响应 |
| `temperature` | number | 可选 | 服务端默认 | 越高越发散 |
| `maxTokens` | integer | 可选 | 服务端默认 | 单次最大输出 token 数 |

### `generate_image`

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `model` | object | ✅ | — | 来自 `list_models(kind="image")` 的模型引用 |
| `prompt` | string | ✅ | — | 描述主体、构图、风格、光线与文字 |
| `count` | integer | 可选 | `1` | 候选数量；增加按比例增扣费用 |
| `size` | string | 可选 | 服务端默认 | 像素尺寸，仅使用支持的枚举值 |
| `ratio` | string | 可选 | 服务端默认 | 画幅，仅使用支持的枚举值 |
| `referenceMediaIds` | array | 可选 | — | 通过 `upload_media_from_path` 得到的 `mediaId` 列表 |

### `generate_video`

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `model` | object | ✅ | — | 来自 `list_models(kind="video")` 的模型引用 |
| `prompt` | string | ✅ | — | 描述主体、动作、镜头、光线、风格与声音 |
| `durationSeconds` | integer | 可选 | 服务端默认 | 时长（5/10/15） |
| `count` | integer | 可选 | `1` | 候选数量；增加按比例增扣费用 |
| `size` | string | 可选 | 服务端默认 | 像素尺寸 |
| `ratio` | string | 可选 | 服务端默认 | 画幅 |
| `referenceMediaIds` | array | 可选 | — | 参考媒体 `mediaId` 列表 |
| `firstFrameMediaId` | string | 可选 | — | 首帧 `mediaId`，与 `lastFrameMediaId` 配合做首尾帧过渡 |
| `lastFrameMediaId` | string | 可选 | — | 尾帧 `mediaId` |

### `get_generation_task`

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `taskId` | string | ✅ | 来自 `generate_image` / `generate_video` 的真实返回值 |
