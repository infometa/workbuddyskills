---
name: video-generation
description: 在用户要用提示词和可选参考素材生成 Seedance 商品视频时，先预检估价，经用户确认后幂等创建并查询结果。
version: 1.0.0
author: 极睿科技（Infimind）
---

# 视频生成

## 使用时机

用于根据提示词、参考图/视频/音频或首尾帧生成 1～12 条 Seedance 视频。如用户要先拆解一条爆款参考视频，再为目标商品生成结构同类视频，使用 `viral-video-copy`。

## 调用流程

1. 收集提示词、模型、模式、时长、分辨率、比例、数量和可选参考素材；本远程 Connector 只传 HTTPS URL。
2. 首次调用 `create_video_generation_task`时传 `dryRun=true`。预检只校验权限、素材、能力和价格，不创建任务、不调供应商、不占用积分。
3. 向用户明确展示 `estimatedCredits`、生成数、时长、分辨率和固定后比例。用户未确认时立即停止。
4. 确认后用与 dryRun 相同的业务参数正式调用，并传入稳定唯一的 `idempotencyKey` 和用户允许的 `maxCredits`。重试网络请求时复用同一幂等键。
5. 用返回的 `taskId` 和 `taskType=video_generation` 调用 `get_user_tasks`到终态。
6. 只对 completed 结果，用该 `taskId`、结果 `resultId` 和 `taskType=video_generation` 调用 `get_video_result_download_url`。

## 工具与参数

### `create_video_generation_task`

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| `prompt` | 是 | 视频画面、镜头、动作和商品约束 |
| `model` | 是 | `seedance_2_0` / `seedance_2_5` |
| `mode` | 是 | `all_in_one` / `first_last_frame` |
| `durationSeconds` | 是 | 2.0：5/10/15；2.5：5/10/15/20/25/30 |
| `resolution` | 是 | `480p` / `720p` / `1080p` |
| `aspectRatio` | 是 | `21:9` / `16:9` / `4:3` / `1:1` / `3:4` / `9:16` / `adaptive` |
| `outputCount` | 是 | 1～12 |
| `referenceImages` | 否 | HTTPS 图片；数量与能力按模型校验 |
| `referenceVideos` | 否 | HTTPS 视频；时长、编码与数量按模型校验 |
| `referenceAudios` | 否 | HTTPS 音频；2.0 不允许纯音频输入 |
| `generateAudio` | 否 | 是否生成音轨，默认 true |
| `dryRun` | 是（预检） | 首次必须 true；正式创建为 false/省略 |
| `idempotencyKey` | 正式必填 | 稳定客户端幂等键 |
| `maxCredits` | 正式必填 | 用户确认的最大整单积分，不小于已接受估价 |

`first_last_frame` 只接受按顺序的 1～2 张首/尾帧图，不传参考视频或音频。`adaptive` 只自适应画幅，分辨率仍必须明确指定。

### `get_user_tasks` / `get_video_result_download_url`

| 工具 | 参数 |
| --- | --- |
| `get_user_tasks` | 精确传 `taskId`、`taskType=video_generation`；`status` 和 `limit` 仅作可选筛选 |
| `get_video_result_download_url` | completed 后传 `taskId`、`resultId`、`taskType=video_generation` |

## 权限、积分与安全边界

- OAuth 获取与刷新：首次连接时由 WorkBuddy 打开浏览器完成 OAuth；access token 到期后由客户端使用 refresh token 自动轮换；授权失效后重新连接。
- OAuth 绑定用户、空间和 operator，不索要 Token；创建、查看、下载均由服务端分别鉴权。
- 只传 HTTPS URL，禁止本地路径、`file:`、`data:`/base64、localhost、私网/保留地址或供应商临时 URL。
- 素材的 MIME/magic、尺寸、时长、FPS、codec 和信任边界以服务端 probe 为准。
- 积分以 dryRun 估价、服务端 hold 和终态结算为准；不修改用户已确认的参数，不隐式追加输出或扣费。
- 不生成仿冒他人、未授权人像/品牌或违法内容；结果只从可信存储签发短时下载链接。

## 错误处理

只显示稳定公开 code/category 和可操作建议，不透传供应商错误、provider URL、存储 key、提示词快照或原始媒体 URL。遇到 `PROVIDER_CONTENT_SAFETY_REAL_PERSON` 或 `VIDEO_RETRY_REQUIRES_MATERIAL_ADJUSTMENT` 时，引导用户调整/移除相关素材再新建；不自动重试或重建。
