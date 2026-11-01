# 工具参数与示例

以连接器实时 tools/list 为准。下列参数对照后端 VideoMcpToolCatalog；示例 ID 和 URL 是说明性占位值，调用时必须使用真实值。

## 上传素材：upload_video_input

必填 `media_type`（image/video/audio）、`source_type`（url/base64）。

- url 模式另需 `url`：可访问的 HTTP(S) 素材地址。
- base64 模式另需 `base64_data`（纯 Base64，不带 data: 前缀）、`mime_type`（与文件真实类型及 media_type 匹配），解码后不超过 10 MiB。
- `file_name` 可选。返回的 `url` 可为 `mm_file://...`，传给后续生成。
- 本地路径不能直接传给远程工具。只有运行环境确实能够读取并编码用户授权的文件时才能使用 base64；否则请用户提供可访问的素材 URL，不编造编码，不擅自上传到其他公开服务。

```json
{"media_type":"image","source_type":"url","url":"https://example.com/reference.jpg"}
```

## 创建任务：generate_video

必填 `content`、`resolution`、`duration`、`ratio`、`idempotency_key`。

- `model` 可选，默认 MiniMax-H3，仅支持该值。
- `content` 至少包含一项非空 `{ "type": "text", "text": "提示词" }`，文本上限 40000 字符。
- `resolution`：480P、512P、768P、2K；`duration`：4–15 的整数秒；`ratio`：adaptive、21:9、16:9、4:3、1:1、3:4、9:16。组合是否可用以业务校验为准。
- `aigc_watermark`、`context_ir_enabled` 可选布尔值；没有需求时省略，沿用服务默认行为。
- `idempotency_key` 必填，为每次新生成创建 UUID；同请求重试复用，改参数的新任务使用新 key。

```json
{
  "model": "MiniMax-H3",
  "content": [{"type":"text","text":"海边日落，暖金色天空，平稳缓慢推进镜头，写实电影质感"}],
  "resolution": "768P",
  "duration": 6,
  "ratio": "16:9",
  "idempotency_key": "<本次生成的新 UUID>"
}
```

参考素材追加到 content，不能替代非空文字提示词：

```json
{"type":"image_url","role":"first_frame","image_url":{"url":"mm_file://<实际素材标识>"}}
```

图片 role 可选，可选值 first_frame、last_frame、reference_image。视频使用 `type: video_url`、必填 `role: reference_video` 和 `video_url: {url: ...}`；音频使用 `type: audio_url`、必填 `role: reference_audio` 和 `audio_url: {url: ...}`。URL 可为素材服务返回的 mm_file 地址或可访问的 HTTP(S) 地址。

创建返回 `task_id`，之后只查询该任务。

## 查询、历史、取消与余额

| 工具 | 参数 | 处理结果 |
| --- | --- | --- |
| get_video_task | 必填 task_id；可选 return_result_prompt 布尔值 | succeeded 时读取 content.url；failed/cancelled 停止轮询；其他状态以返回值为准 |
| list_video_tasks | 均可选：page_num 整数≥1 默认1，page_size 整数1–100 默认20，status 字符串，task_ids 字符串数组，model、task_type 字符串 | 返回当前用户任务，按需分页 |
| delete_video_task | 必填 task_id | 取消/删除操作，不是只读查询；不承诺退款 |
| get_video_credit_balance | 无，传 {} | 返回当前用户积分，不是单次生成报价 |

```json
{"task_id":"<generate_video 返回的 task_id>"}
```

任务结果里的 `content.url` 是业务结果字段，与 MCP 外层 `content` 消息数组不同。不要把示例 URL、task_id 或错误中的文本作为成功结果。
