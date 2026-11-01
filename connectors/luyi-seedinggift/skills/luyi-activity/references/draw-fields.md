# create_draw_activity 字段参考

字段与平台 `DrawActivitySaveDTO` 及服务端创建校验一一对应。标注「必填」的字段缺失时创建会失败。

## 主字段

| 字段 | 类型 | 必填 | 默认 | 取值范围 / 说明 |
|---|---|---|---|---|
| `title` | string | 是 | — | 抽奖活动标题 |
| `draw_method` | integer | 是 | — | 抽奖方式：`1`=免费抽奖，`2`=积分抽奖，`3`=关注公众号抽奖，`4`=积分+关注公众号抽奖 |
| `participate_integral` | integer | 条件必填 | `0` | 每次抽奖消耗积分；`draw_method` 为 `2`/`4` 时必填且 > 0 |
| `banner` | string | 是 | — | 活动封面图路径（建议 750×340）；须先征得用户同意生成并由用户确认，直接填生成结果的本地路径或图片 URL，无需额外上传 |
| `head_banner` | string | 是 | — | 活动头图路径（建议 750×420）；须先征得用户同意生成并由用户确认，直接填生成结果的本地路径或图片 URL，无需额外上传 |
| `prize_type` | integer | 否 | `1` | 奖品类型：`1`=实物奖品，`2`=积分奖品（不支持优惠券） |
| `prize_name` | string | 否 | — | 奖品名称；实物奖品可先用 `luyi-activity-mcp` 的 `list_products` 让用户选择 |
| `prize_num` | integer | 是 | — | 奖品数量（份），必须 > 0 |
| `prize_integral` | integer | 条件必填 | `0` | 每份积分奖品的积分数量；`prize_type=2` 时必填且 > 0 |
| `prize_cover` | string | 条件必填 | — | 奖品封面图 URL（建议 500×500）；`prize_type=1` 时必填 |
| `prize_description` | string | 否 | — | 奖品说明 |
| `win_probability` | number | 是 | — | 中奖概率（百分比），必须 > 0 且 ≤ 100 |
| `open_type` | integer | 是 | — | 开奖方式：`1`=实时开奖，`2`=人满开奖，`3`=助力开奖，`4`=定时开奖 |
| `required_participants` | integer | 条件必填 | `0` | 人满开奖所需人数；`open_type=2` 时必填且 > 0 |
| `help_probability_increase` | number | 条件必填 | `0` | 助力概率增幅；`open_type=3` 时必填且 > 0 |
| `draw_rule` | integer | 否 | `0` | 抽奖规则：`0`=每人只可抽取一次，`1`=每天一次，`2`=每天二次，`3`=每天三次 |
| `page_theme_color` | string | 否 | — | 页面主体色，`#RRGGBB`（留空用默认配色） |
| `official_account_qrcode` | string | 否 | — | 公众号二维码 URL；选填。`draw_method` 为 `3`/`4` 时商家须先完成公众号授权，C 端二维码由后端动态生成，无需上传 |
| `customer_service_qrcode` | string | 否 | — | 客服二维码 URL |
| `started_at` | string | 是 | — | 开始时间，`YYYY-MM-DD HH:mm:ss`；必须先询问用户并选定未来时间 |
| `ended_at` | string | 是 | — | 结束时间，`YYYY-MM-DD HH:mm:ss`；必须晚于开始时间 |
| `buyer_show_reward_type` | integer | 否 | `0` | 中奖晒单奖励：`0`=不开启，`1`=积分奖励 |
| `buyer_show_reward_integral` | integer | 条件必填 | `0` | 每次晒单奖励积分数；`buyer_show_reward_type=1` 时必填且 > 0 |

## 联动必填规则速查

| 触发条件 | 必须补充 |
|---|---|
| `draw_method = 2` 或 `4` | `participate_integral > 0` |
| `open_type = 2` | `required_participants > 0` |
| `open_type = 3` | `help_probability_increase > 0` |
| `prize_type = 1`（实物） | `prize_cover` |
| `prize_type = 2`（积分） | `prize_integral > 0` |
| `buyer_show_reward_type = 1` | `buyer_show_reward_integral > 0` |

## 平台校验清单（提交前自查）

- [ ] `title` 非空
- [ ] 已先询问用户并得到生成许可；`banner` 和 `head_banner` 均已生成、由用户确认，并直接填写真实图片路径（本地路径或图片 URL），无需额外上传或公网访问检查
- [ ] `draw_method` 1~4，且积分抽奖已填 `participate_integral`
- [ ] `open_type` 1~4，且人满/助力已填对应数值
- [ ] `prize_type` 为 1 或 2（不支持优惠券）
- [ ] `prize_num > 0`；实物已填 `prize_cover`；积分已填 `prize_integral`
- [ ] `win_probability` 在 (0, 100]
- [ ] `draw_rule >= 0`
- [ ] `buyer_show_reward_type` 为 0 或 1；开启晒单奖励时已填积分数量
- [ ] 未传任何优惠券字段（`prize_coupon_id`、`buyer_show_reward_coupon_id` 等）
- [ ] 时间格式为 `YYYY-MM-DD HH:mm:ss`，开始时间经用户确认且晚于当前时间，开始早于结束

## 服务端错误对照

| 错误信息 | 处理建议 |
|---|---|
| 抽奖活动标题不能为空 | 补 `title` |
| 抽奖方式不合法 | `draw_method` 取 1~4 |
| 积分抽奖时参与所需积分不能为空 | 补 `participate_integral > 0` |
| 当前仅支持实物和积分奖品 | `prize_type` 用 1 或 2 |
| 奖品数量不能为空 | 补 `prize_num > 0` |
| 实物奖品封面不能为空 | 补 `prize_cover` |
| 积分奖品数量不能为空 | 补 `prize_integral > 0` |
| 中奖概率必须大于0且不超过100 | 修正 `win_probability` |
| 抽奖类型不合法 | `open_type` 取 1~4 |
| 人满开奖时开奖所需人数不能为空 | 补 `required_participants > 0` |
| 助力抽奖时助力概率增幅不能为空 | 补 `help_probability_increase > 0` |
| 抽奖规则不合法 | `draw_rule >= 0` |
| 当前不支持优惠券晒单奖励 | `buyer_show_reward_type` 用 0 或 1 |
| 晒单积分奖励数量不能为空 | 补 `buyer_show_reward_integral > 0` |
| 当前不支持优惠券奖励 | 移除优惠券字段 |
| 抽奖开始/结束时间不合法 | 用 `YYYY-MM-DD HH:mm:ss` |
| 抽奖开始时间必须早于结束时间 | 调整两个时间 |
