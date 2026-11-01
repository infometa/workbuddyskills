# create_checkin_activity 字段参考

字段与平台 `POST /b/checkin/campaign/set` 入参及服务端创建校验一一对应。标注「必填」的字段缺失时创建会失败。

工具只负责创建：**不接受 `id` 与 `status`**；创建后活动缺省上架。要编辑或上下架请到路易商家后台操作。

## 主字段

| 字段 | 类型 | 必填 | 默认 | 取值范围 / 说明 |
|---|---|---|---|---|
| `name` | string | 是 | — | 活动名称，去首尾空白后不能为空 |
| `start_date` | string | 是 | — | 开始日期，`YYYY-MM-DD`（也兼容 `YYYY-MM-DD HH:mm:ss`） |
| `deadline_date` | string | 条件必填 | — | 截止日期，`YYYY-MM-DD`；`is_long_term=0` 时必须填写，且不能早于 `start_date` |
| `is_long_term` | integer | 否 | 自动 | `0`=固定期限，`1`=长期活动；未填截止日期且未指定时按长期活动处理 |
| `checkin_type` | integer | 否 | `1` | `1`=每日发帖打卡，`2`=线下扫码打卡（需要地点），`3`=线下发帖打卡（需要地点和半径） |
| `latitude` / `longitude` | number | 类型 2/3 必填 | — | 活动地点坐标 |
| `address` | string | 类型 2/3 必填 | — | 活动地点名称 |
| `checkin_radius` | integer | 类型 3 必填 | — | 打卡半径（米），1–50000；类型 2 固定 100 米 |
| `reward_type` | integer | 类型 2/3 必填 | — | 活动级奖励：`1`=积分（需 `single_checkin_integral>0`），`2`=线下发实物，`3`=线上邮寄实物（2/3 需 `prize_id`） |
| `prize_id` | integer | 条件必填 | — | 活动级实物奖励 ID；用 `list_checkin_prizes` 查询并让用户选择 |
| `claim_qr_code` | string | 条件必填 | — | 线上邮寄领奖二维码 URL；活动级 `reward_type=3` 或阶段奖励线上邮寄时必填 |
| `period_days` | integer | 否 | `7` | 打卡周期天数，必须大于 0 |
| `single_checkin_integral` | integer | 否 | `0` | 每次成功打卡赠送的积分，`0`=不发放单次积分 |
| `description` | string | 否 | — | 活动描述（向用户说明打卡方式与奖励） |
| `cover` | string | MCP Schema 选填；连接器流程必需 | — | 活动封面图路径；生成前需取得用户同意，生成后由用户确认，直接填生成结果的本地路径或图片 URL，无需额外上传 |
| `head_image` | string | MCP Schema 选填；连接器流程必需 | — | 活动列表页头图路径；生成前需取得用户同意，生成后由用户确认，直接填生成结果的本地路径或图片 URL，无需额外上传 |
| `cal_background` | string | 否 | — | 打卡日历背景图 URL |
| `activity_detail` | string | 否 | — | 活动详情富文本 HTML 片段 |
| `page_theme_color` | string | 否 | 默认主题 | 页面主体色，`#RRGGBB` |
| `need_manual_audit` | integer | 否 | `0` | 打卡帖是否需要人工审核：`0`=否，`1`=是 |
| `allow_video` | integer | 否 | `0` | 是否允许视频打卡：`0`=否，`1`=是 |
| `member_level_ids` | integer[] | 否 | `[]` | 可参与的会员等级 ID 列表，空=不限 |
| `user_label_ids` | integer[] | 否 | `[]` | 可参与的用户标签 ID 列表，空=不限（当前平台不支持用户标签，仅为契约兼容保留，不参与资格判定） |
| `goods_list` | object[] | 否 | `[]` | 活动关联的打卡商品列表，建议来自 `luyi-activity-mcp` 的 `list_products` |
| `reward_rules` | object[] | 否 | `[]` | 连续打卡奖励规则，可多档 |
| `sort_weight` | integer | 否 | `0` | 活动列表排序权重，越大越靠前 |

### `member_level_ids` 说明

- 本平台接本地成长体系，这里的 ID 是**本地等级的 index**（`/b/level/config/get` 的 `setting[].index`，默认 Lv1..Lv20）。
- 判定口径为「用户当前等级序号 >= 配置的最低等级」；游客或读不到等级时不可参与。
- 空数组表示不限等级。

## `goods_list[]` 结构

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `item_id` | integer | 是 | 商品ID（来自 `luyi-activity-mcp` 的 `list_products`） |
| `title` | string | 是 | 商品名称 |
| `sub_title` | string | 否 | 商品副标题 |
| `image` | string | 否 | 商品图片 URL |
| `price` | integer | 否 | 商品价格（分） |
| `detail_url` | string | 否 | 商品详情链接 |
| `page_url` | string | 否 | 商品落地页链接 |
| `origin` | string | 否 | 商品来源 |
| `alias` | string | 否 | 商品别名 |
| `actual_quantity` | integer | 否 | 商品实际库存数量 |

## `reward_rules[]` 结构

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `continuous_days` | integer | 是 | 连续打卡天数阈值，必须大于 0 |
| `reward_type` | string | 是 | `integral`=积分奖励，`coupon`=优惠券奖励 |
| `reward_name` | string | 否 | 奖励名称，如 `30积分` |
| `value` | integer | 否 | 奖励数值：积分奖励填积分数量 |
| `code` | string | 否 | 奖励编码（优惠券填券码），可留空 |
| `single_checkin_integral` | integer | 否 | 该档奖励附加的单次打卡积分，可留空 |

## 平台校验清单（提交前自查）

- [ ] `name` 非空
- [ ] `cover` 和 `head_image` 已经用户同意生成并确认，直接填写真实图片路径（本地路径或图片 URL），无需额外上传或公网访问检查
- [ ] `start_date` 为合法日期
- [ ] `is_long_term=0` 时 `deadline_date` 非空且不早于 `start_date`
- [ ] `period_days > 0`
- [ ] 每条 `reward_rules` 的 `continuous_days > 0`，`reward_type` 为 `integral` 或 `coupon`
- [ ] 未向工具传 `id` / `status`

## 重要说明：优惠券奖励当前不会真正发券

- `reward_type=integral` 会通过积分服务真实发放。
- `reward_type=coupon` 在 Go 侧缺少有赞优惠券客户端，**只会落下奖励记录并记日志，不会真正发券**。除非用户明确知情并接受，否则建议统一使用积分奖励。

## 查询打卡奖品库

使用工具 `list_checkin_prizes` 查询当前租户奖品库，支持参数 `keyword`（名称模糊搜索）、`page`（默认 1）和 `limit`（默认 20，最大 100）。结果提供奖品 `id`、`name`、`image`；仅当活动级奖励选线下/线上实物奖励时，将用户选中的 ID 填入 `prize_id`。此 ID 不可用 `list_products` 的商品 ID 替代。

## 服务端错误对照

| 错误信息 | 处理建议 |
|---|---|
| 活动名称不能为空 | 补 `name` |
| 活动开始日期格式不正确 | `start_date` 用 `YYYY-MM-DD` |
| 活动截止日期格式不正确 | `deadline_date` 用 `YYYY-MM-DD` |
| 活动截止日期不能早于开始日期 | 调整两个日期 |
| 打卡周期天数必须大于0 | `period_days` 用正整数 |
| 打卡奖励规则配置不正确 | 检查 `continuous_days > 0` 与 `reward_type` 取值 |
| 数据存储未就绪 | 服务端存储异常，原样转述 |
