# AI-HIVE Wan 3.0 契约

本文件是工具调用的最高依据。模型目录、参数与价格可能变化；执行时始终以当次 `list_models` / `get_model` 返回值为准。

## 六个 public model

| 版本 | 模式 | publicModelId                          | 媒体字段                                                         |
| ---- | ---- | -------------------------------------- | ---------------------------------------------------------------- |
| 标准 | T2V  | `public_model_wan_3_0_video`           | 无                                                               |
| 标准 | I2V  | `public_model_wan_3_0_video_i2v`       | `firstFrameMediaId` 必填，`lastFrameMediaId` 可选                |
| 标准 | R2V  | `public_model_wan_3_0_video_r2v`       | `imageMediaIds` / `videoMediaIds` / `audioMediaIds` 至少一类非空 |
| Pro  | T2V  | `public_model_wan_3_0_video_prime`     | 无                                                               |
| Pro  | I2V  | `public_model_wan_3_0_video_prime_i2v` | `firstFrameMediaId` 必填，`lastFrameMediaId` 可选                |
| Pro  | R2V  | `public_model_wan_3_0_video_prime_r2v` | `imageMediaIds` / `videoMediaIds` / `audioMediaIds` 至少一类非空 |

模式互斥。首尾帧不能放进 `imageMediaIds`；普通参考图不能冒充 `firstFrameMediaId`。AI-HIVE 当前不提供 Wan 3.0 V2V 编辑入口，不得宣称可直接编辑旧视频。

R2V 当前素材上限：参考图片最多 10 张；参考视频最多 5 段，每段 1–15 秒且总时长不超过 15 秒；参考音频最多 5 段，每段 1–15 秒且总时长不超过 15 秒；参考视频总时长与输出 `duration` 之和不超过 30 秒。执行前仍以当次模型详情中的 `videoConfig` 为准。

## 当前公共参数

- `prompt`：必填。
- `params.resolution`：`480P`、`720P`、`1080P`。
- `params.duration`：2–30 的整数；不支持 `-1` 或自动时长。
- `params.ratio`：`adaptive`、`16:9`、`4:3`、`1:1`、`3:4`、`9:16`。
- `params.audio`：布尔值；未明确需要声音时也要向用户展示其值。
- `params.seed`：可选，0–2147483647。
- `params.watermark`：可选布尔值。

不要把本地路径或公开 URL 直接写成媒体输入。先调用 `upload_media_from_path`，再把返回的 mediaId 放进对应字段。

## 明确生成时的顺序

1. `get_user_info` 获取余额。
2. `list_models({modelType:"VIDEO", detail:"full"})` 获取当前模型、routingMode、参数配置和 `pricingSnapshot`。
3. 选择与素材模式和版本完全匹配的模型；将该模型和 routingMode 对应的单个快照原样保留。
4. 按本次售价规则计算预计费用；展示计费维度、单价、duration 对应总价和余额。
5. 等用户确认 publicModelId、duration、resolution、ratio、audio 与费用。
6. 上传素材，保持各类型上传顺序与提示词 `@图片N` / `@视频N` / `@音频N` 一致。
7. 用稳定 UUID 作为 `clientRequestId` 调用 `generate_video`。
8. 返回 pending 时只用 `get_generation_task({taskId})` 查询。

## clientRequestId

- 传输中断、`REQUEST_IN_PROGRESS`：参数完全相同时复用原 ID。
- 价格快照过期：刷新 `list_models`，保持业务参数并复用原 ID 重试 1 次。
- 余额、参数、媒体或已缓存模型调用失败：修正后使用新 ID；原 ID 只会重放旧失败。
- `REQUEST_OUTCOME_UNKNOWN`：停止自动重试，不自动生成新 ID，提示人工核查。
- 任何业务参数变化都代表新逻辑请求，使用新 ID。
