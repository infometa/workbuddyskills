# 视频生成参数

适用于 `generate_video`。依据 2026-10-28 当前连接的工具定义整理；运行时定义变化时以当前工具为准。每次调用生成一条独立视频任务，不负责拼接成片。

## 模型选择

用户未指定时使用默认 `wan3.0-video`。用户指定的模型不在允许清单时说明限制，提供可选项，不偷偷换模型执行。

| 展示名称 | `model` | `model_version` | 常用输出配置 |
|---|---|---|---|
| 万相 3.0 | `wan3.0-video` | 省略 | `duration`、`resolution`（`720P` / `1080P`）、`aspectRatio` |
| MiniMax H3 | `drama_video_hailuo_h3` | 省略 | `duration`（工具描述约 4～15 秒）、`resolution`（`768P` / `2K`）、固定 `aspectRatio`，不能为 `adaptive` |
| 可灵 3.0 | `Kling` | `3.0`；省略时服务端默认 3.0 | `duration`、`resolution`（`720P` / `1080P`）、`aspectRatio`、`hasAudio` |
| Seedance 2.0 | `ep-20260727095359-b5lpl` | 省略 | `duration`、`resolution`（常用 `720p`）、`aspectRatio` |
| Seedance 2.0 fast | `ep-20260730154538-b8lpd` | 省略 | 同上 |
| Seedance 2.0 mini | `ep-20260730154612-445g6` | 省略 | 同上 |

大小写有业务含义，按各模型要求填写。这里的“常用”不是所有组合均可用的保证，服务端返回能力/参数错误时停止该项，不盲试其他付费组合。

## 文字与素材

- `prompt` 必填：描述主体、动作、镜头、环境、风格，保持在约 4000 字以内；URL、模型、时长秒数不塞进提示词。
- `outputConfig` 为对象，字段名是 camelCase；视频不支持 `count`。
- `file_infos` 为对象数组，不能传 URL 字符串数组。每项有真实 `url`、`type` 和 `role`。
- 图片：`type: image`；首帧 `role: first_frame`，尾帧 `role: last_frame`，参考图 `role: reference_image`。
- 视频：`type: video`、`role: reference_video`；音频：`type: audio`、`role: reference_audio`。
- 可灵当前只消费图片，不传参考视频或音频。万相、MiniMax H3 和 Seedance 2.0 工具描述支持混合素材；首尾帧放在参考图前。Seedance 素材明确填写 `type`、`role`；已有 `type: video` 时可省略 `hasReferenceVideo`。
- 不为缺失素材捏造链接，不把用户指定首帧当普通参考图；模型不支持用户所需素材时先说明差异。

## 默认参数示例

仅当用户没有另行指定时使用这些缺省值；提交前说明时长、比例、分辨率和积分消耗。

```json
{
  "prompt": "清晨的海边，一只白色海鸥从礁石飞起，镜头缓慢向前推进，海面反射暖色日光，写实电影画面",
  "model": "wan3.0-video",
  "outputConfig": {
    "duration": 5,
    "resolution": "1080P",
    "aspectRatio": "16:9"
  }
}
```

不要用 `model_version` 表达分辨率、时长或计费档。不要传 `spaceId`、`projectId`、`MODEL-*`；不要因画面描述需要音效就承诺一定生成音频，须按所选模型当前能力处理。

提交后立即保存真实任务 ID，按任务状态参考查询；文档中的 10～15 秒分镜规划不表示所有模型都支持相同时长。用户需要较长成片时先说明单段能力与不提供拼接的限制，不擅自拆成多条收费任务。
