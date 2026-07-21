# 短剧售卖方式配置（short_play_pay_type）

> 适用场景：`smart_delivery_platform` = `SMART_DELIVERY_PLATFORM_EDITION_ECOLOGY_PLAYLET`（爆剧跑量）

当智投类型为爆剧跑量时，支持设置短剧售卖方式类型。本文档说明相关字段的取值规则和校验逻辑。

---

## 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `short_play_pay_type` | enum | 否（爆剧跑量场景可选） | 短剧付费类型 |
| `sell_strategy_id` | integer | 条件必填 | 售卖策略 ID，当 `short_play_pay_type` = `SHORT_PLAY_PAY_TYPE_CHARGE_PLAY` 时**必填** |

---

## 枚举值

### short_play_pay_type（短剧付费类型）

| 枚举值 | 含义 |
|--------|------|
| `SHORT_PLAY_PAY_TYPE_FREE_PLAY` | 免费剧 |
| `SHORT_PLAY_PAY_TYPE_CHARGE_PLAY` | 收费剧（付费） |

> `SHORT_PLAY_PAY_TYPE_UNKNOWN` 为系统默认值，Agent 不应主动传入。

---

## 校验规则

1. **场景限制**：`short_play_pay_type` 和 `sell_strategy_id` 仅在 `smart_delivery_platform` = `SMART_DELIVERY_PLATFORM_EDITION_ECOLOGY_PLAYLET`（爆剧跑量）时有效
2. **条件必填**：当 `short_play_pay_type` = `SHORT_PLAY_PAY_TYPE_CHARGE_PLAY`（收费剧）时，`sell_strategy_id` **必须填写**且不能为 0
3. **免费剧无需策略**：当 `short_play_pay_type` = `SHORT_PLAY_PAY_TYPE_FREE_PLAY`（免费剧）时，`sell_strategy_id` 不需要填写

---

## 请求体示例
```json
{
    // ...
    "marketing_goal": "MARKETING_GOAL_USER_GROWTH",
    "marketing_sub_goal": "MARKETING_SUB_GOAL_UNKNOWN",
    "marketing_carrier_type": "MARKETING_CARRIER_TYPE_JUMP_PAGE",
    "marketing_asset_id": 684341515,
    "smart_delivery_platform": "SMART_DELIVERY_PLATFORM_EDITION_ECOLOGY_PLAYLET",
    "short_play_pay_type": "SHORT_PLAY_PAY_TYPE_FREE_PLAY"
}
```

---

## Agent 使用指引

1. **识别场景**：当用户选择爆剧跑量场景时，询问用户短剧是免费剧还是收费剧
2. **收费剧必须提供策略 ID**：如果用户选择收费剧但未提供 `sell_strategy_id`，必须向用户询问
3. **枚举查询**：可通过 `get-enum-options.mjs '{"fields":["short_play_pay_type"]}'` 查询枚举值
