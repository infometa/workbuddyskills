# create_seeding_activity 字段参考

字段与平台 `SeedingActivitySaveDTO` 及服务端创建校验一一对应。标注「必填」的字段缺失时创建会失败。

## 主字段

| 字段 | 类型 | 必填 | 默认 | 取值范围 / 说明 |
|---|---|---|---|---|
| `title` | string | 是 | — | 活动名称，不能为空 |
| `cover` | string | 是 | — | 活动封面图路径，不能为空；须先征得用户同意生成并由用户确认，直接填生成结果的本地路径或图片 URL，无需额外上传 |
| `head_image` | string | 是 | — | 活动头图路径，不能为空；须先征得用户同意生成并由用户确认，直接填生成结果的本地路径或图片 URL，无需额外上传 |
| `description` | string | 是 | — | 活动描述，不能为空 |
| `apply_started_at` | string | 是 | — | 报名开始时间，`YYYY-MM-DD HH:mm:ss`；必须先询问用户并选定未来时间 |
| `apply_ended_at` | string | 是 | — | 报名结束时间，`YYYY-MM-DD HH:mm:ss`，必须晚于开始时间 |
| `statistic_days` | integer | 否 | `1` | 数据统计周期（天），1~30 |
| `quota` | integer | 否 | `0` | 活动名额，`0`=不限人数，大于 0 为限定名额 |
| `content_type` | integer | 否 | `0` | 内容形式：`0`=不限，`1`=图文，`2`=视频 |
| `topic_tags` | string[] | 否 | `[]` | 小红书话题/标签，如 `["#母婴种草"]` |
| `reference_link` | string | 否 | — | 小红书参考笔记链接，可留空 |
| `page_theme_color` | string | 否 | — | 页面主体色，必须是 `#RRGGBB`（可留空用默认配色） |
| `prize_qrcode` | string | 条件必填 | — | 领奖二维码 URL；当存在实物奖励（`reward_type=4`）时必填 |
| `seeding_goods` | object | 否 | `null` | 主推种草商品，建议来自 `luyi-activity-mcp` 的 `list_products` |
| `reward_settings` | object[] | 是 | — | 奖励设置，**1~3 档** |

### `seeding_goods` 结构

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | integer | 商品ID（来自 `luyi-activity-mcp` 的 `list_products`） |
| `name` | string | 商品名称 |
| `image` | string | 商品图片 URL |
| `detail` | string | 商品详情 |

## `reward_settings[]` 结构

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `reward_type` | integer | 是 | `1`=积分奖励，`4`=实物奖励（当前仅支持这两种，不支持优惠券） |
| `integral` | integer | 条件必填 | `reward_type=1` 时必填，且必须大于 0 |
| `physical_reward_id` | integer | 条件必填 | `reward_type=4` 时必填，且必须是当前商家**实物奖励库**中已存在的记录 |
| `triggers` | object[] | 是 | 触发条件，至少 1 条；同一档内 `trigger_type` 不能重复 |

### `reward_settings[].triggers[]` 结构

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `trigger_type` | integer | 是 | `1`=点赞，`2`=收藏，`3`=评论 |
| `threshold` | integer | 是 | 触发阈值，必须大于 0 |

## 平台校验清单（提交前自查）

- [ ] 已先询问用户并得到生成许可；`cover` 和 `head_image` 均已生成、由用户确认，并直接填写真实图片路径（本地路径或图片 URL），无需额外上传或公网访问检查

- [ ] 报名开始时间经用户确认且晚于当前时间；报名时间非空、格式正确、开始早于结束
- [ ] `statistic_days` 在 1~30 之间
- [ ] `quota >= 0`，`content_type` 为 0/1/2
- [ ] `page_theme_color` 为空或 `#RRGGBB`
- [ ] `reward_settings` 数量 1~3，`reward_type` 只为 1 或 4
- [ ] 积分奖励 `integral > 0`；实物奖励 `physical_reward_id > 0` 且真实存在
- [ ] 每档 `triggers` 非空、`threshold > 0`、`trigger_type` 不重复
- [ ] 存在实物奖励时 `prize_qrcode` 非空

## 重要说明：实物奖励 ≠ 商品

- `seeding_goods`（种草商品）来自 `luyi-activity-mcp` 的商品查询工具（`list_products`，底层为 `wb_products`）。
- `reward_settings[].physical_reward_id`（实物**奖励**）来自路易后台独立的**实物奖励库**，两者是不同数据源。
- 本连接器只提供创建能力，无法查询实物奖励库。若用户要做实物奖励，请让其在路易商家后台的实物奖励列表中确认 `physical_reward_id`；无法确认时建议改用积分奖励。

## 服务端错误对照

| 错误信息 | 处理建议 |
|---|---|
| 种草活动标题不能为空 | 补 `title` |
| 活动封面不能为空 | 补 `cover` |
| 活动头图不能为空 | 补 `head_image` |
| 活动描述不能为空 | 补 `description` |
| 报名时间不能为空 | 补 `apply_started_at` / `apply_ended_at` |
| 报名开始时间必须早于结束时间 | 调整两个时间 |
| 数据统计周期必须在1到30天之间 | 调整 `statistic_days` |
| 活动名额不能为负数 | 调整 `quota` |
| 内容形式不合法 | `content_type` 用 0/1/2 |
| 页面主题色格式不正确 | 用 `#RRGGBB` |
| 奖励设置至少配置1个, 最多3个 | `reward_settings` 数量 1~3 |
| 当前仅支持积分和实物奖励 | `reward_type` 用 1 或 4 |
| 积分奖励的积分值不能为空 | 补 `integral` 且 > 0 |
| 实物奖励不能为空 | 补 `physical_reward_id` |
| 奖励触发条件不合法 | `trigger_type` 1~3、`threshold` > 0 |
| 同一奖励的触发条件中触发类型不能重复 | 去重 `trigger_type` |
| 奖励触发条件不能为空 | 每档至少 1 条 `triggers` |
| 选择实物奖励时领奖二维码不能为空 | 补 `prize_qrcode` |
| 实物奖励不存在 | `physical_reward_id` 不属于当前商家或不存在 |
