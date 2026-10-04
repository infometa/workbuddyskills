# 积分确认协议

积分确认只管理最终视频生成前的费用确认门。状态流固定为：`not_ready -> awaiting_confirmation -> confirmed -> invalidated`。

## 状态含义

- `not_ready`：完整脚本或复刻方案尚未确认，不允许预估积分。
- `awaiting_confirmation`：已调用 `estimate_video_generation` 并向用户展示预计积分、时长、比例、数量、声音选择和关键素材摘要，正在等待用户确认消耗积分。
- `confirmed`：用户已明确确认消耗积分并生成，本次确认只对当前脚本、方案、素材、时长、比例、数量、声音选择和生成输入有效。
- `invalidated`：预估后脚本、方案、素材、时长、比例、数量或其他生成输入发生变化，旧预估和旧确认失效。

## 调用顺序

完整脚本或方案确认先于 `estimate_video_generation`：未确认完整脚本、脚本、方案或复刻方案时，不得调用 `estimate_video_generation`。

积分确认先于 `generate_video`：未确认积分时，不得调用 `generate_video`。

用户修改脚本、方案、素材、时长、比例、数量、`generate_audio`、参考音频、商品 `video_refs`、复刻 `target_video`、人物三视图 `model_image_ref` 或其他生成输入后，必须把 `credit_confirmation.status` 置为 `invalidated`，丢弃旧预估和旧确认，再回到 `not_ready` 或重新执行脚本确认与预估流程。预估与正式生成必须使用同一个 `generate_audio` 和同一组业务素材；默认 `generate_audio=true`，只有用户明确要求静音时为 `false`。

固定模特商品视频更换人物三视图后，旧商品脚本也同时失效：必须先用新的 `model_image_ref` 重新生成并确认商品脚本，再重新预估。复刻方案分析当前不消费人物三视图，因此复刻更换 `model_image_ref` 只要求重新预估和确认，不宣称旧复刻方案因人物素材变化而重新分析。

向用户确认时只说明预计消耗积分和可理解的生成摘要，不展示内部任务 ID、项目 ID、服务端脚本 ID、请求 ID、任务 ID、最终 prompt 或凭据。

最终生成返回积分不足时，必须用自然中文说明当前积分不足、本次预计消耗和下一步充值操作，并展示当前环境配置的充值入口。不得展示错误码、原始错误字段、内部任务 ID、项目 ID、请求 ID 或底层参数；充值后用户回复“重试”时，继续使用已确认的脚本、方案、素材意图和同一生成请求，不重新确认费用，除非用户修改生成输入。

## WorkBuddy 充值入口

最终生成返回积分不足时，必须展示充值链接：https://picsetai.cn/pricing?scene=workbuddy。只用自然中文说明积分不足和充值后可重试，不得展示错误码或原始错误字段。
