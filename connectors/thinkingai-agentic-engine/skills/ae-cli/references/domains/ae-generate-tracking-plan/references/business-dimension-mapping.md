# Business Dimension → Event/Property Mapping Table

> **Terminology**: 业务维度 = business dimension | 收入模型 = revenue model | 核心循环 = core gameplay loop | 功能入口 = functional entry | 货币体系 = currency system | 注入事件 = injected events | 事件显示名 = event display name | 必带属性 = required properties | IAA = In-App Advertising (ad monetization) | IAP = In-App Purchase | 硬货币 = hard currency (premium, e.g. diamonds) | 软货币 = soft currency (earnable, e.g. gold) | 广告场景 = ad scene | 内购物品 = IAP item | platform = client / server / both

> Used during Phase 1 Draft generation to auto-inject corresponding events and properties based on
> business dimension information collected in Phase 0.
> This file is an internal reference for the skill; Claude reads it when generating the draft.

---

## 一、Revenue Model → Required Events

| 收入模型 | 注入事件 | 事件显示名 | event_tag | platform | 必带属性 |
|---|---|---|---|---|---|
| `IAA` | `ad_show` | 广告展示 | 广告 | client | `ad_type`、`ad_placement`、`is_filled` |
| `IAA` | `ad_click` | 广告点击 | 广告 | client | `ad_type`、`ad_placement`、`ad_network` |
| `IAA` | `ad_reward_get` | 激励广告奖励领取 | 广告 | client | `ad_type`、`ad_placement`、`reward_type`、`reward_amount` |
| `IAP` | `payment` | 支付成功 | 支付 | server | `order_id`、`pay_amount`、`currency_type`、`payment_name`、`payment_type` |
| `IAP` | `payment_fail` | 支付失败 | 支付 | server | `order_id`、`fail_reason`、`payment_name` |
| `mixed` | 同 IAA + IAP 所有事件 | | | | |
| `subscription` | `subscription_start` | 订阅开始 | 订阅 | server | `subscription_id`、`plan_name`、`start_time` |
| `subscription` | `subscription_renew` | 订阅续费 | 订阅 | server | `subscription_id`、`renew_amount`、`currency_type` |
| `subscription` | `subscription_cancel` | 订阅取消 | 订阅 | server | `subscription_id`、`cancel_time`、`cancel_reason` |
| `commission` | `order_create` | 订单创建 | 交易 | server | `order_id`、`order_amount`、`commission_rate` |
| `commission` | `order_paid` | 订单支付 | 交易 | server | `order_id`、`pay_amount`、`commission_amount` |
| `commission` | `commission_settled` | 佣金结算 | 交易 | server | `settlement_id`、`commission_amount`、`settle_time` |

---

## 二、核心玩法循环 → 事件序列

解析 `core_loop` 描述，提取动作节点，映射为事件。

### 动作动词 → 事件名映射

| 动作动词 | 事件名 | 说明 |
|---|---|---|
| 刷/打/通关 | `stage_start` / `stage_complete` / `stage_fail` | 关卡类玩法 |
| 获得/获取/得到 | `token_get` / `item_get` / `hero_get` | 资源/道具/角色获取 |
| 消耗/使用/花费 | `token_consume` / `item_consume` | 资源/道具消耗 |
| 购买/商城 | `shop_open` / `shop_buy` | 商城相关 |
| 抽卡/召唤/招募 | `gacha_draw` / `recruit_draw` | 随机抽取类玩法 |
| 战斗/PVP/竞技 | `battle_start` / `battle_end` / `battle_result` | 战斗结算 |
| 任务/委托 | `task_accept` / `task_complete` | 任务系统 |
| 升级/提升 | `level_up` / `vip_levelup` | 成长系统 |
| 注册/登录/登出 | `register` / `login` / `logout` | 生命周期 |

### 示例解析

**输入**："玩家反复刷关卡获得金币，用金币抽卡获取角色"

**解析结果**：

```
节点1: 刷关卡 → stage_start / stage_complete / stage_fail  [event_tag: 关卡/Stage]
节点2: 获得金币 → token_get (token_type=gold, source=关卡)  [event_tag: 资源/Resource]
节点3: 抽卡 → gacha_draw (pool_type, draw_count)  [event_tag: 抽卡/Gacha]
节点4: 获取角色 → hero_get (hero_id, hero_star)  [event_tag: 养成/Growth]
```

---

## 三、功能入口 → 模块事件组

> 第一列"模块"即该事件的 `event_tag` 值。注入时翻译为用户语言。

| 模块 (event_tag) | 事件名 | 显示名 | platform | 典型属性 |
|---|---|---|---|---|
| 关卡 | `stage_start` | 关卡开始 | client | `stage_id`、`stage_type`、`difficulty` |
| 关卡 | `stage_complete` | 关卡完成 | server | `stage_id`、`star_rating`、`score` |
| 关卡 | `stage_fail` | 关卡失败 | server | `stage_id`、`fail_reason` |
| 抽卡 | `gacha_draw` | 抽卡 | server | `pool_type`、`draw_count`、`cost_amount` |
| 抽卡 | `hero_get` | 获得英雄 | server | `hero_id`、`hero_star`、`source` |
| 商城 | `shop_open` | 打开商城 | client | `shop_type` |
| 商城 | `shop_buy` | 商城购买 | server | `item_id`、`item_num`、`pay_amount`、`token_balance` |
| 公会 | `guild_join` | 加入公会 | server | `guild_id`、`guild_name` |
| 公会 | `guild_donate` | 公会捐献 | server | `donate_type`、`donate_amount` |
| 公会 | `guild_boss_start` | 公会BOSS战开始 | server | `guild_id`、`boss_id` |
| 排行榜 | `rank_view` | 查看排行榜 | client | `rank_type`、`rank_id` |
| 排行榜 | `rank_refresh` | 刷新排行 | client | `rank_type` |
| 排行榜 | `rank_click` | 点击排行项 | client | `rank_type`、`target_id` |
| 任务 | `task_accept` | 接受任务 | server | `task_id`、`task_type` |
| 任务 | `task_complete` | 完成任务 | server | `task_id`、`reward_amount` |
| 任务 | `task_reward_claim` | 领取任务奖励 | server | `task_id`、`reward_type` |
| 成就 | `achieve_unlock` | 解锁成就 | server | `achieve_id`、`achieve_name` |
| 成就 | `achieve_reward_claim` | 领取成就奖励 | server | `achieve_id`、`reward_amount` |
| 签到 | `daily_sign` | 每日签到 | server | `sign_day`、`consecutive_days` |
| 签到 | `sign_reward_claim` | 领取签到奖励 | server | `reward_type`、`reward_amount` |

---

## 四、货币体系 → 属性设计

### 货币类型枚举

| token_type | 显示名 | 说明 |
|---|---|---|
| `diamond` | 钻石 | 硬货币（付费） |
| `gold` | 金币 | 软货币（免费） |
| `energy` | 体力 | 限流资源 |
| `power` | 体力/能量 | 通用限流资源 |
| `alliance_point` | 联盟积分 | 公会货币 |
| `honor` | 荣誉 | 竞技货币 |
| `star_point` | 星芒 | 赛季货币 |

### 货币相关事件

| 事件名 | 显示名 | 使用场景 |
|---|---|---|
| `token_get` | 获得货币 | 任何获得虚拟货币的场景 |
| `token_consume` | 消耗货币 | 任何消耗虚拟货币的场景 |

### 货币事件属性

```json
// token_get / token_consume 通用属性
{
  "token_type": "diamond",    // 货币类型（枚举见上）
  "token_amount": 100,        // 本次变动数量
  "token_balance": 5000,      // 变动后余额
  "source": "关卡奖励",        // 来源（仅 token_get）
  "consume_type": "抽卡"      // 消耗用途（仅 token_consume）
}
```

---

## 五、事件 platform 判定规则

> **使用场景**：注入标准事件（一～四章）之外的自定义事件时，按本表判定 platform；或在 Phase 1.3 Step 3 注入前用于校验注入事件的 platform 是否合理。

| 事件类型 | platform |
|---|---|
| 用户 UI 交互（点击/浏览/打开页面） | `client` |
| 客户端状态变化（关卡开始/结束） | `client` |
| 资源/货币变动（获取/消耗） | `server` |
| 支付相关（支付/充值） | `server` |
| 业务数据落库（订单/任务完成/成就解锁） | `server` |
| 需要服务端验证（防刷/校验） | `server` |
| 两端均需（登录/登出） | `both` |
| SDK 自动采集事件 | `client` |

---

## 六、广告场景详细配置

### 广告类型枚举

| ad_type | 显示名 |
|---|---|
| `rewarded` | 激励视频 |
| `interstitial` | 插屏广告 |
| `banner` | 横幅广告 |
| `splash` | 开屏广告 |
| `native` | 原生广告 |

### IAA 模式自动注入事件

```json
[
  {
    "event_name": "ad_show",
    "display_name": "广告展示",
    "platform": "client",
    "event_tag": "广告",
    "prop_names": ["ad_type", "ad_placement", "ad_network", "is_filled", "ecpm"],
    "source": "business_dimension"
  },
  {
    "event_name": "ad_click",
    "display_name": "广告点击",
    "platform": "client",
    "event_tag": "广告",
    "prop_names": ["ad_type", "ad_placement", "ad_network"],
    "source": "business_dimension"
  },
  {
    "event_name": "ad_reward_get",
    "display_name": "激励广告奖励领取",
    "platform": "client",
    "event_tag": "广告",
    "prop_names": ["ad_type", "ad_placement", "reward_type", "reward_amount"],
    "source": "business_dimension"
  }
]
```

---

## 七、用户属性补充建议（按收入模型）

| 收入模型 | 建议添加的用户属性 |
|---|---|
| IAA | `total_ad_watch_count`（累计看广告次数）、`total_ad_revenue`（累计广告收入，单位：美分） |
| IAP | `total_pay_amount`（累计付费金额）、`first_pay_time`（首次付费时间）、`last_pay_time`（最近付费时间） |
| `subscription` | `subscription_status`（订阅状态）、`subscription_plan`（订阅计划）、`subscription_expire_time`（订阅到期时间） |
| `mixed` | 以上都要 |

---

## 八、品类专用事件模块

> 根据应用类型/游戏品类，自动注入对应模块的事件组。
> 品类由 Phase 0 的 `meta.scenario` 或用户描述推断。
>
> **event_tag 规则**：本表中每行的"模块"列即该事件的 `event_tag` 值。注入时需翻译为用户语言。
> 例如 战斗→`Battle`, 养成→`Growth`, 抽卡→`Gacha`, 资源→`Resource`, 广告→`Ads`, 支付→`Payment`。

### 8.0 通用基础模块（所有品类适用）

> 以下事件不属于任何具体功能模块（关卡/商城/抽卡等），统一使用 `基础事件`（Basic）标签。
> 区别于 `系统事件`（System Event，SDK 自动采集的 `ta_*` 事件）。

**用户生命周期**：

| 模块 | 事件名 | 显示名 | platform | 必带属性 |
|---|---|---|---|---|
| 基础事件 | `new_device` | 设备激活 | client | `channel` |
| 基础事件 | `register` | 用户注册 | server | `register_type` |
| 基础事件 | `login` | 用户登录 | both | `account_id` |
| 基础事件 | `logout` | 用户登出 | both | `session_duration` |

**成长模块**：

| 模块 | 事件名 | 显示名 | platform | 必带属性 |
|---|---|---|---|---|
| 基础事件 | `create_role` | 创建角色 | server | `role_id`、`role_name`、`server_id` |
| 基础事件 | `guide_complete` | 完成新手引导 | client | `guide_id`、`guide_step` |
| 基础事件 | `level_up` | 升级 | server | `level`、`level_before` |
| 基础事件 | `vip_levelup` | VIP升级 | server | `vip_level` |

### 8.1 游戏类 — 通用基础模块（所有游戏必选）

> 以下为游戏品类通用的基础事件，所有游戏品类均应包含。详见 8.0 通用基础模块。

### 8.2 游戏类 — 按品类

#### 8.2.1 卡牌/RPG/放置/Roguelike

| 模块 | 事件名 | 显示名 | platform | 必带属性 |
|---|---|---|---|---|
| 战斗 | `battle_start` | 战斗开始 | client | `battle_type`、`hero_info` |
| 战斗 | `battle_end` | 战斗结束 | server | `battle_type`、`battle_result`、`hero_info` |
| 战斗 | `mopping_up` | 扫荡 | server | `stage_id`、`mop_count` |
| 养成 | `hero_get` | 获得英雄 | server | `hero_id`、`hero_star`、`source` |
| 养成 | `hero_levelup` | 英雄升级 | server | `hero_id`、`level` |
| 抽卡 | `gacha_draw` | 抽卡 | server | `pool_type`、`draw_count`、`cost_amount` |
| 资源 | `token_get` | 获得货币 | server | `token_type`、`token_amount`、`source` |
| 资源 | `token_consume` | 消耗货币 | server | `token_type`、`token_amount`、`consume_type` |
| 任务 | `task_complete` | 完成任务 | server | `task_id`、`reward_amount` |
| 社交 | `guild_join` | 加入公会 | server | `guild_id` |

#### 8.2.2 SLG 策略类

| 模块 | 事件名 | 显示名 | platform | 必带属性 |
|---|---|---|---|---|
| 建筑 | `building_build` | 建造建筑 | server | `building_type`、`level` |
| 建筑 | `building_upgrade` | 升级建筑 | server | `building_id`、`level` |
| 资源 | `resource_gather_start` | 开始采集 | client | `resource_type` |
| 资源 | `resource_gather_finish` | 完成采集 | server | `resource_type`、`amount` |
| 战斗 | `battle_start` | 战斗开始 | client | `battle_type`、`troop_info` |
| 战斗 | `battle_result` | 战斗结果 | server | `battle_type`、`result`、`damage` |
| 联盟 | `alliance_create` | 创建联盟 | server | `alliance_id`、`alliance_name` |
| 联盟 | `alliance_join` | 加入联盟 | server | `alliance_id` |

#### 8.2.3 MMO

| 模块 | 事件名 | 显示名 | platform | 必带属性 |
|---|---|---|---|---|
| 副本 | `dungeon_enter` | 进入副本 | client | `dungeon_type`、`difficulty` |
| 副本 | `dungeon_complete` | 完成副本 | server | `dungeon_type`、`result` |
| 装备 | `equip_forge` | 装备打造 | server | `equip_type`、`cost` |
| 交易 | `trade_sell` | 挂售物品 | server | `item_id`、`price` |
| 交易 | `trade_buy` | 购买物品 | server | `item_id`、`price` |

#### 8.2.4 休闲/超休闲/Slots

| 模块 | 事件名 | 显示名 | platform | 必带属性 |
|---|---|---|---|---|
| 关卡 | `level_start` | 关卡开始 | client | `level_id` |
| 关卡 | `level_win` | 关卡胜利 | server | `level_id`、`score` |
| 关卡 | `level_fail` | 关卡失败 | server | `level_id`、`fail_reason` |
| 关卡 | `level_restart` | 重新开始 | client | `level_id` |
| 复活 | `revive_show` | 复活弹窗展示 | client | `level_id` |
| 复活 | `revive_use` | 使用复活 | client | `ad_type`、`level_id` |
| Slots | `spin_start` | 老虎机开始 | client | `bet_amount` |
| Slots | `spin_result` | 老虎机结果 | server | `win_amount`、`is_big_win` |

#### 8.2.5 短剧/内容类产品

| 模块 | 事件名 | 显示名 | platform | 必带属性 |
|---|---|---|---|---|
| 内容播放 | `playlet_start` | 短剧开始 | client | `playlet_id`、`episode` |
| 内容播放 | `playlet_end` | 短剧结束 | server | `playlet_id`、`duration` |
| 广告 | `reward_ad_show` | 激励广告展示 | client | `ad_placement`、`ecpm` |
| 奖励 | `coin_get` | 获得代币 | server | `coin_amount`、`source` |
| 抽奖 | `lottery_draw` | 抽奖 | server | `lottery_type`、`prize` |
| 提现 | `withdraw_apply` | 申请提现 | server | `amount` |

### 8.3 非游戏类

#### 8.3.1 电商

| 模块 | 事件名 | 显示名 | platform | 必带属性 |
|---|---|---|---|---|
| 发现 | `home_feed_expose` | 首页推荐曝光 | client | `feed_type` |
| 发现 | `search_submit` | 搜索提交 | client | `keyword` |
| 商品 | `commodity_detail` | 商品详情页 | client | `commodity_id`、`price` |
| 商品 | `add_cart` | 加入购物车 | client | `commodity_id`、`quantity` |
| 订单 | `submit_order` | 提交订单 | server | `order_id`、`total_amount` |
| 订单 | `pay_order` | 支付订单 | server | `order_id`、`pay_amount` |
| 售后 | `apply_return` | 申请退货 | server | `order_id`、`reason` |

#### 8.3.2 在线教育

| 模块 | 事件名 | 显示名 | platform | 必带属性 |
|---|---|---|---|---|
| 引导 | `consent_privacy_accept` | 隐私授权 | client | - |
| 课程 | `course_detail_view` | 课程详情页 | client | `course_id` |
| 课程 | `course_start` | 开始学习 | client | `course_id`、`lesson_id` |
| 课程 | `video_play_complete` | 视频播放完成 | server | `course_id`、`duration` |
| 报名 | `enroll_course_free` | 免费报名 | server | `course_id` |
| 报名 | `payment_success` | 支付成功 | server | `course_id`、`pay_amount` |
| 测验 | `quiz_submit` | 提交测验 | server | `quiz_id`、`score` |

#### 8.3.3 社交类

| 模块 | 事件名 | 显示名 | platform | 必带属性 |
|---|---|---|---|---|
| 内容 | `post_publish` | 发布动态 | server | `content_type` |
| 互动 | `post_like` | 点赞 | client | `post_id` |
| 互动 | `post_comment` | 评论 | client | `post_id`、`comment` |
| 关系 | `follow` | 关注 | client | `target_user_id` |
| 直播 | `live_gift_send` | 送礼物 | server | `gift_type`、`gift_count` |

#### 8.3.4 工具类（剪辑/视频）

| 模块 | 事件名 | 显示名 | platform | 必带属性 |
|---|---|---|---|---|
| 创作 | `project_create` | 创建项目 | client | `project_type` |
| 创作 | `use_function` | 使用功能 | client | `function_name`、`is_first_use` |
| 素材 | `watch_video` | 观看视频 | client | `video_id`、`duration` |
| 导出 | `project_export` | 导出项目 | client | `export_format` |

---

## 九、对象与对象组使用规范

### 核心区分

| 类型 | JSON 结构 | 适用场景 | 关系 |
|---|---|---|---|
| `object`（对象） | `{"key":"val"}` | 当前装备、出战英雄、地址信息 | 一对一 |
| `array_row`（对象组） | `[{"key":"val"}]` | 背包物品、阵容列表、排行榜 | 一对多 |

**简单判断：数据是 `{...}` 用 `object`，是 `[{...}]` 用 `array_row`。**

### 对象（object）使用场景

适用于**单个复合实体**，即一个属性里包含多个子属性，但实体本身只有一个：

| 属性名 | 适用场景 | 典型子属性 |
|---|---|---|
| `equip_info` | 当前装备详情 | `equip_id`、`equip_name`、`equip_level`、`equip_quality` |
| `hero_info` | 当前出战英雄（只有一个时） | `hero_id`、`hero_name`、`hero_level` |
| `address_info` | 收货地址 | `province`、`city`、`district`、`detail` |

### 对象书写格式

在埋点方案中：
1. **父属性行**：属性名填 `xxx_info`，类型填 `对象`
2. **子属性行**：属性名填 `xxx_info.child_name`，类型填子属性实际类型
3. 必须提供取值样例：`{"item_id":"001","item_num":5}`

### 对象组（array_row）使用场景

适用于**多个同类复合实体**，须满足三条件：

1. 一个事件属性中有多个同类实体需记录（如多艘舰船、多件物品）
2. 每个实体需记录 ≥2 个属性（否则用 `array_string` 列表即可）
3. 实体数量不固定（固定为 1 个时用 `object`）

| 对象组名 | 适用场景 | 典型子属性 |
|---|---|---|
| `hero_info` / `ship_info` / `fleet_info` | 出战阵容、角色明细 | `id`、`level`、`star`、`power` |
| `get_item_info` | 获得物品明细 | `item_id`、`item_num` |
| `cost_item_info` | 消耗物品明细 | `item_id`、`item_num` |
| `rank_info` | 排行榜信息 | `id`、`rank`、`score` |
| `hero_info` | 战斗阵容 | `hero_id`、`hero_level`、`troop_type` |

### 对象组书写格式

在埋点方案中：
1. **父属性行**：属性名填 `xxx_info`，类型填 `对象组`
2. **子属性行**：属性名填 `xxx_info.child_name`，类型填子属性实际类型
3. 必须提供取值样例：`[{"item_id":"001","item_num":5}]`

---

## 十、属性类型规范

| 类型 | JSON 类型 | 取值样例 | 适用场景 |
|---|---|---|---|
| 文本 | String | `"上海"` | 名称、渠道、ID（非纯数值时） |
| 数值 | Number | `123`、`1.23` | 金额、等级、时长、纯数值 ID |
| 布尔 | Boolean | `true`、`false` | 是否首次、是否付费 |
| 时间 | String | `"2024-01-01 00:00:00"` | 注册时间、首充时间 |
| 列表 | Array | `["a","1"]` | 标签列表、技能列表 |
| 对象 | Object | `{"item_name":"碎片","item_num":5}` | 单个复合实体 |
| 对象组 | Array(Object) | `[{"id":"001","num":5}]` | 多个同类复合实体 |

**ID 类属性类型选择**：
- ID 先后关系与数值大小正相关（如关卡 ID 1,2,3...）→ 数值
- ID 含非数值字符或无序 → 文本
- 不确定时 → 文本（更安全）

---

## 十一、模板事件增删规则

### 保留条件（不可删除）

- SDK 预置事件（`ta_app_*`）
- 充值流程事件（`init_order`、`payment`、`payment_fail`）
- 资源经济事件（`token_get`、`token_consume`）

### 新增条件（满足任一即必须新增）

1. **功能入口原则**：产品主界面有独立入口的功能模块，模板未覆盖 → 必须新增
2. **收入模型原则**：收入模型要求的事件模板未覆盖 → 必须新增（见第一章）
3. **高频行为原则**：产品研究发现的高频用户行为模板未覆盖 → 建议新增

### 新增事件最低要求

- 必须有 ≥2 个自定义属性
- 必须标注事件标签（模块归属）和采集端
- 命名符合 snake_case（事件名默认小写，用户要求保留大写时按用户要求）

---

## 附录：event_tag 多语言对照表

> 生成 event_tag 时，根据用户语言从本表选取对应翻译。
> 代码层（`src/xlsx/write.ts` 的 `CANONICAL_TAG`）也同步维护此表，用于 xlsx 输出时按业务重要性排序。

| 中文 | English | 日本語 | 한국어 |
|---|---|---|---|
| 基础事件 | Basic | 基本イベント | 기본 이벤트 |
| 系统事件 | System Event | システムイベント | 시스템 이벤트 |
| 战斗 | Battle | 戦闘 | 전투 |
| 关卡 | Stage | ステージ | 스테이지 |
| 副本 | Dungeon | ダンジョン | 던전 |
| 抽卡 | Gacha | ガチャ | 가챠 |
| 养成 | Growth | 育成 | 육성 |
| 资源 | Resource | リソース | 리소스 |
| 广告 | Ads | 広告 | 광고 |
| 支付 | Payment | 支払い | 결제 |
| 订阅 | Subscription | サブスクリプション | 구독 |
| 商城 | Shop | ショップ | 상점 |
| 任务 | Quest | クエスト | 퀘스트 |
| 成就 | Achievement | 実績 | 업적 |
| 签到 | Check-in | チェックイン | 출석체크 |
| 排行榜 | Leaderboard | ランキング | 리더보드 |
| 公会 | Guild | ギルド | 길드 |
| 社交 | Social | ソーシャル | 소셜 |
| 建筑 | Building | 建築 | 건설 |
| 联盟 | Alliance | 同盟 | 연맹 |
| 装备 | Equipment | 装備 | 장비 |
| 交易 | Trade | トレード | 거래 |
| 复活 | Revive | 復活 | 부활 |
| Slots | Slots | スロット | 슬롯 |
| 抽奖 | Lottery | 抽選 | 추첨 |
| 奖励 | Reward | 報酬 | 보상 |
| 提现 | Withdraw | 引き出し | 출금 |
| 发现 | Discovery | 発見 | 발견 |
| 商品 | Product | 商品 | 상품 |
| 订单 | Order | 注文 | 주문 |
| 售后 | After-sales | アフターサービス | A/S |
| 内容 | Content | コンテンツ | 콘텐츠 |
| 互动 | Interaction | インタラクション | 인터랙션 |
| 关系 | Relationship | 関係 | 관계 |
| 直播 | Live | ライブ | 라이브 |
| 引导 | Onboarding | オンボーディング | 온보딩 |
| 课程 | Course | コース | 코스 |
| 报名 | Enrollment | 申し込み | 신청 |
| 测验 | Quiz | クイズ | 퀴즈 |
| 创作 | Creation | 創作 | 창작 |
| 素材 | Material | 素材 | 소재 |
| 导出 | Export | エクスポート | 내보내기 |
| 内容播放 | Playback | 再生 | 재생 |