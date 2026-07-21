---
name: tencentads-delivery-standard-update
description: 营销单元（原广告）/智投项目通用更新。支持修改营销单元或智投项目的多个字段（名称、日期、定向、时段、出价、预算、状态、深度转化、一键起量、创意增强、周期达成等），支持单个营销单元/项目更新和多账号多营销单元/项目批量更新。
license: MIT
compatibility: any
metadata:
  author: Tencent Ads Delivery Team
  version: "0.5.8"
  icon: megaphone
  category: tencent-ads
---

# 广告/智投项目通用更新（Adgroup General Update）

单广告（或智投项目）多字段通用更新技能，支持一次调用中同时修改广告或智投项目的多个属性。使用腾讯广告同步 `adgroups/update` API。

**适用场景**：当用户需要修改广告或智投项目的出价、预算、定向、名称、日期、时段、状态、深度转化、一键起量、创意增强、周期达成（周期预算/续投开关）等属性时，使用本技能。

> **版本说明**：本技能支持两种模式：
> - **单广告/项目更新**：`update-adgroup-general.mjs`，适用于单账号单个广告或智投项目的精细操作。
> - **批量更新**：`update-adgroup-batch.mjs`，适用于多账号多个广告/智投项目的异构字段批量操作（每个广告/项目可更新不同的字段组合）。

---

## SOP 决策流程

### 脚本选择

| 场景 | 使用脚本 | 说明 |
|------|----------|------|
| 单账号单个广告/项目 | `update-adgroup-general.mjs` | 精细操作，详细日志 |
| 多个广告/项目（同/跨账号）| `update-adgroup-batch.mjs` | 批量操作，每个广告/项目可更新不同字段 |

**选择规则**：
- 用户明确指定了 1 个广告或智投项目 -> 用 `general`
- 用户指定了 2 个及以上广告/智投项目 -> 用 `batch`
- 用户说"所有广告"/"全部广告"/"所有项目"/"全部项目" -> 先查询列表，然后用 `batch`

### 单广告/项目流程

| 步骤 | 名称 | 关键产物 |
|------|------|---------|
| 1 | 意图识别 | 是否使用本 SKILL |
| 2 | 参数构造 | `account_id` / `adgroup_id` / 更新字段 |
| 3 | 更新前自检 | 复述变更，等待用户确认（金钱/状态/定向字段必走） |
| 4 | 执行脚本 | `update-adgroup-general.mjs`（智投项目同用） |
| 5 | 回查验证 | 脚本自动回查 |
| 6 | 反思比对 | Agent 对比 `_verify` 数据与目标值 |

### 批量更新流程

| 步骤 | 名称 | 关键产物 |
|------|------|---------|
| 1 | 意图识别 | 多广告/项目更新意图 |
| 2 | 参数构造 | `tasks` 数组，每条含 `account_id` / `adgroup_id` / 更新字段 |
| 3 | 更新前自检 | 列全量受影响，逐条复述+确认（`tasks ≥ 2` 必走） |
| 4 | 执行批量脚本 | `update-adgroup-batch.mjs` |
| 5 | 汇总回查 | 脚本自动批量回查 |
| 6 | 反思比对 | Agent 对比每个广告/项目的 `_verify` 数据 |

### 步骤 1：意图识别

当用户表达以下意图时，激活本 Skill：

| 用户意图示例 | 说明 |
|-------------|------|
| "帮我把广告X的出价改为120元" | 单字段更新（绝对值） |
| "把广告X的预算调整为600元，出价改为50元" | 多字段更新（绝对值） |
| "广告X的出价下调10%" / "出价降低10%" | 出价百分比调整（用 bid_amount_adjustment: "-10%"） |
| "广告X的预算提高2倍" / "预算翻倍" | 预算倍数调整（用 daily_budget_adjustment: "*2"） |
| "广告X出价加0.5元" | 出价加减调整（用 bid_amount_adjustment: "+50"，即加50分） |
| "帮我把广告X的定向改为不限" | 定向更新 |
| "关闭广告X的智能定向" / "广告X不使用智能定向" / "广告X改为手动定向" | `smart_targeting_mode` → `SMART_TARGETING_MANUAL` |
| "开启广告X的智能定向" / "广告X使用智能定向" | `smart_targeting_mode` → `SMART_TARGETING_AUTO` |
| "把广告X的名称改为ABC" | 名称更新 |
| "暂停广告X" / "启用广告X" | 状态更新 |
| "帮我把广告X的投放时段改为工作日9-18点" | 时段更新 |
| "开启广告X的一键起量，预算500元" | 一键起量开启 |
| "关闭广告X的一键起量" | 一键起量关闭（用 auto_acquisition_enabled: false） |
| "广告X的起量预算改为500元" | 一键起量已开启时调整预算绝对值（用 `auto_acquisition_budget: 50000`，即500元=50000分），脚本内部自动先关后开 |
| "广告X的起量预算提升10%" / "起量预算增加200元" | 一键起量已开启时相对调整（用 `auto_acquisition_budget_adjustment: "+10%"` 或 `"+20000"`，即加20000分），与 `auto_acquisition_budget` 二选一 |
| "关闭广告X的创意增强" | 创意增强关闭 |
| "开启广告X的创意增强，偏好AIGC" | 创意增强开启+偏好（用 auto_derived_creative_enabled: true + auto_derived_creative_method_type_list） |
| "把广告X的深度出价改为30元" | 深度转化出价绝对值 |
| "广告X的深度出价下调15%" | 深度转化出价相对调整（用 deep_conversion_behavior_bid_adjustment: "-15%"） |
| "广告X的ROI系数改为1.5" | ROI系数绝对值（用 deep_conversion_worth_rate: 1.5） |
| "广告X的ROI上升10%" | ROI系数相对调整（用 deep_conversion_worth_rate_adjustment: "+10%"，百分比与用户表述一致） |
| "帮我把广告A和广告B的出价都调到50元" | **批量更新**：用 `update-adgroup-batch.mjs`，tasks 包含两个广告，各自 bid_amount: 5000（50元=5000分） |
| "把这3个广告全部暂停" | **批量更新**：用 `update-adgroup-batch.mjs`，tasks 各自 configured_status: "AD_STATUS_SUSPEND" |
| "广告A出价加10%，广告B预算改500，广告C暂停" | **异构批量更新**：用 `update-adgroup-batch.mjs`，每个 task 更新不同字段 |
| "帮我把项目X的出价改为120元" | 智投项目单字段更新（智投项目 ID 等同于 adgroup_id） |
| "暂停项目X" / "启用项目X" | 智投项目状态更新 |
| "把这3个智投项目全部暂停" | **批量更新**：用 `update-adgroup-batch.mjs`，tasks 各自 configured_status: "AD_STATUS_SUSPEND" |
| "项目X的预算调到800元，出价改为60元" | 智投项目多字段更新 |
| "把项目X的周期预算提高到3000元" | 周期达成项目修改周期预算。详见 [references/smart-delivery-period-update.md](references/smart-delivery-period-update.md) |
| "项目X改为续投" / "开启续投" | 周期达成项目修改续投开关。详见 [references/smart-delivery-period-update.md](references/smart-delivery-period-update.md) |
| "项目X关闭续投" / "不续投了" | 周期达成项目关闭续投。详见 [references/smart-delivery-period-update.md](references/smart-delivery-period-update.md) |

### 步骤 2：参数构造

根据广告/智投项目数量选择对应模式（智投项目 ID 等同于 adgroup_id，参数构造方式完全一致）：

**单个更新**（1 个广告或智投项目）：
- `account_id`：必填，广告主账号 ID
- `adgroup_id`：必填，广告 ID 或智投项目 ID
- 至少一个更新字段（见下方字段列表）

**批量更新**（2 个及以上广告/智投项目）：
- `tasks`：必填，数组，每个元素包含 `account_id`、`adgroup_id`（广告 ID 或智投项目 ID）和要更新的字段
- 每个 task 可更新完全不同的字段组合（异构批量）

### 步骤 3：更新前自检（Pre-update Check，必须在调用 update-adgroup-*.mjs 前完成）

更新生效后会消耗预算并影响投放表现，出价/预算这类金钱字段一旦写错可能在察觉前就产生不可挽回的扣费；定向写错也会烧错钱（投到无关人群、误变通投）。命中以下任一情况时，**禁止直接执行脚本**，必须先向用户复述变更，等待"确认/继续/OK"等明确回复后才能继续：

- 金钱字段：`bid_amount` / `daily_budget` / `deep_conversion_behavior_bid` / `deep_conversion_worth_rate` / `auto_acquisition_budget` 及其 `_adjustment` 变体、`bid_adjustment`（分版位系数）
- 状态切换：`configured_status`（暂停立即停投、启用立即开始消耗）
- 定向字段：`targeting`（任意子字段都会触发——子字段是覆盖式而非合并式，传 `{}` 直接变通投）
- 批量更新：`update-adgroup-batch.mjs` 且 tasks ≥ 2（必须列出每条受影响的 `account_id`/`adgroup_id` 及变更摘要）

**复述要求**：

- **金钱字段**：一律用「元（分）」双标注；`_adjustment` 表达式**必须先取当前值算出绝对结果**再展示，禁止只丢给用户 `"-10%"`
- **定向字段**：必须列出**变更的子字段**（如 `geo_location`、`age`、`custom_audience`），并明确写出"原值 → 新值"。**特别警示两类高危改动**：(1) 子字段被整体覆盖（如原"北京+上海"传"北京"会丢上海，要明确告知用户）；(2) `targeting: {}` 会清空全部定向变成通投，必须显式向用户确认"是否要改成不限定向"
- 用户未明确回复或要求修改 → 不要执行脚本；参数变了就重新走一遍本步骤

> 仅修改 `adgroup_name` / 日期 / 时段 / 创意衍生 / `poi_list` 等非金钱、非状态、非定向字段时可跳过本复述，但仍需完成下文「支持的更新字段」表中的单位与范围核对。

### 步骤 4：执行脚本

**单广告更新**：
```bash
node scripts/update-adgroup-general.mjs '<JSON参数>'
```

**批量更新**：
```bash
node scripts/update-adgroup-batch.mjs '<JSON参数>'
```

### 步骤 5：回查验证

> 与步骤 3 的区别：步骤 3 是「**提交前**」对照请求体确认意图；本步是「**提交后**」对照腾讯返回的最新值确认 API 实际生效结果。

脚本执行后会自动输出 `_verify` 回查数据，包含广告更新后的实际字段值（单广告在 `adgroup`，批量在 `results[].data`）。

### 步骤 6：反思比对

Agent 必须基于 `_verify` 回查数据进行反思比对：
1. 对比实际值与**步骤 3 已被用户确认的目标值**
2. 金额字段一律换算成元再比（API 返回分）
3. 如有不一致，**明确告知用户**哪些字段未达预期，并主动提示是否需要回滚（再次调用本 skill 改回原值）
4. 如回查失败，提醒用户手动确认

---

## 支持的更新字段

> ⚠️ **重要**：智投项目和标准广告支持的字段不同，使用前请确认广告类型。脚本内置的前置查询 `adgroups/get` 会返回 `smart_delivery_platform` 字段——有该字段（且非 `SMART_DELIVERY_PLATFORM_EDITION_STANDARD`）即为智投项目，否则为标准广告。

### 公共字段（标准广告 + 智投项目均可用）

| 字段 | 类型 | 说明 | 单位/格式 |
|------|------|------|-----------|
| `adgroup_name` | string | 广告/项目名称 | 最大 120 等宽字符（中文=2，英文=1） |
| `begin_date` | string | 开始投放日期 | YYYY-MM-DD |
| `end_date` | string | 结束投放日期 | YYYY-MM-DD，空串=长期投放 |
| `delivery_time_ranges` | string[] | 投放时段 | "Monday 09:00~18:00" 或 ["all"] |
| `first_day_begin_time` | string | 首日开始投放时间 | HH:MM:SS（默认 00:00:00） |
| `bid_amount` | number | 出价（绝对值） | **分**（如 120.50元 → 12050） |
| `bid_amount_adjustment` | string | 出价相对调整（与 bid_amount 二选一） | 表达式，如 "+20%"、"-10%"、"*2"、"+50"（加50分） |
| `daily_budget` | number | 日预算（绝对值） | **分**（0=不限，范围 5000~400,000,000） |
| `daily_budget_adjustment` | string | 日预算相对调整（与 daily_budget 二选一） | 表达式，如 "+30%"、"*1.5"、"-10000"（减10000分） |
| `configured_status` | string | 广告/项目状态 | AD_STATUS_NORMAL / AD_STATUS_SUSPEND |
| `targeting` | object | 定向设置 | 传空对象 {} = 不限定向（智投可设置维度因场景不同，详见智投文档） |
| `smart_targeting_mode` | string | 智能定向模式。`SMART_TARGETING_MANUAL`（手动定向）=不使用/关闭智能定向，`SMART_TARGETING_AUTO`（智能定向）=开启/使用智能定向 | 字符串枚举 |
| `deep_conversion_behavior_bid` | number | 深度优化行为出价（绝对值） | **分**（如 50元 → 5000） |
| `deep_conversion_behavior_bid_adjustment` | string | 深度优化行为出价相对调整 | 表达式，如 "+15%"、"*0.8" |
| `deep_conversion_worth_rate` | number | 深度优化期望ROI系数（绝对值） | 无单位，范围 0.001~1000 |
| `deep_conversion_worth_rate_adjustment` | string | 深度优化期望ROI系数相对调整 | 表达式，如 "+10%"、"-5%"、"*1.2"、"+0.5" |
| `auto_derived_creative_enabled` | boolean | 创意衍生开关 | true/false；开启时脚本自动查询可用衍生方式 |
| `auto_derived_creative_method_type_list` | string[] | 创意衍生偏好（开启时可选） | 不传则自动使用默认推荐项 |
| `poi_list` | array | 门店 ID 列表 | 数组，传 `[]` 表示清空 |

### 仅标准广告可用字段

| 字段 | 类型 | 说明 | 单位/格式 |
|------|------|------|-----------|
| `auto_acquisition_enabled` | boolean | 一键起量开关（⚠️ 智投项目禁用） | true/false |
| `auto_acquisition_budget` | number | 一键起量预算（绝对值） | **分**（范围 20000~10,000,000，即 200~100,000 元） |
| `auto_acquisition_budget_adjustment` | string | 一键起量预算相对调整 | 表达式，如 "+10%"、"-20%"、"+100"；仅已开启时可用 |
| `re_open_auto_acquisition` | number | 重新开启一键起量 | 1 = 重新开启 |
| `rta_id` | string | RTA 策略 ID | 字符串，直接透传给 API |
| `rta_target_id` | string | RTA 目标 ID | 字符串，直接透传给 API |
| `aoi_optimization_strategy` | string | AOI优化策略开关 | 如 `"AOI_OPTIMIZATION_STRATEGY_ENABLED"` / `"AOI_OPTIMIZATION_STRATEGY_DISABLED"` |
| `industry_value_explore` | object | 行业探索配置 | 如 `{"high_volume_exploration": true}` |

### 仅智投项目可用字段

| 字段 | 类型 | 说明 | 单位/格式 |
|------|------|------|-----------|
| `bid_adjustment` | object | 分版位出价 | 格式 `{"site_set_package": [{"site_set": ["SITE_SET_MOMENTS"], "bid_coefficient": 1.5, "deep_bid_coefficient": 1.5}]}` |
| `smart_delivery_aigc_creative` | object | 智投AIGC创意 | 如 `{"is_open": true, "supply_strategy_type": ["SUPPLY_STRATEGY_TYPE_AIGC"]}` |
| `smart_delivery_history_comp_reused_creative` | object | 全库智选 | 如 `{"is_open": true}` / `{"is_open": false}` |
| `smart_delivery_period_budget` | number | 周期达成周期预算（仅周期达成项目可修改） | **分**，只允许提升不允许降低。约束：≥ 3 × 出价 × 周期天数。详见 [references/smart-delivery-period-update.md](references/smart-delivery-period-update.md) |
| `smart_delivery_period_continue` | string | 周期达成续投开关（仅周期达成项目可修改） | `PERIOD_CONTINUE_SWITCH_ON` / `PERIOD_CONTINUE_SWITCH_OFF`。详见 [references/smart-delivery-period-update.md](references/smart-delivery-period-update.md) |

> **金额字段统一使用分**：bid_amount、daily_budget、deep_conversion_behavior_bid、auto_acquisition_budget 单位均为**分**，与腾讯广告 API 及其他 skill（创建、查询、账户更新）保持一致。Agent 需将用户表达的元乘以 100 转为分后传入（如"1000元" → `100000`）。
> **deep_conversion_worth_rate 是比率**，不是金额，不做转换。
> **相对调整表达式**：4 个金额字段（bid_amount、daily_budget、deep_conversion_behavior_bid、auto_acquisition_budget）和 1 个比率字段（deep_conversion_worth_rate）均支持 `_adjustment` 伴随字段，用于基于当前值做相对调整（与绝对值字段二选一）。支持的格式：`"+20%"`（增加百分比）、`"-10%"`（减少百分比）、`"*2"`（乘以倍数）、`"+50"`（加 50 分）、`"-30"`（减 30 分）。调整后仍需满足各字段的范围约束。当前值为 0 时不支持相对调整。注意：`auto_acquisition_budget_adjustment` 仅在一键起量已开启时可用，新开启时必须使用 `auto_acquisition_budget` 传入绝对值。

## 定向更新 SOP（targeting 字段详细指引）

当用户要求修改广告定向时，按照以下流程构造 `targeting` 对象。

> 脚本已内置 `resolveTargetingFields` 枚举自动匹配，支持传入简化值（如 `"本科"`、`"4G"`、`"ANDROID_10+"`），脚本自动转为 API 标准枚举。

### 定向查询触发规则

**命中任一项就必须先调用 `get-targeting-lookup.mjs` 查编码**：

- 用户给了地域、省市区、常驻地 → `type: "geo"`
- 用户给了设备品牌 / 型号 → `type: "device"`

```bash
# 地域编码查询（支持批量，keyword 用空格分隔）
node scripts/get-targeting-lookup.mjs '{"type":"geo","keyword":"北京 上海 广东"}'

# 设备品牌型号 ID 查询
node scripts/get-targeting-lookup.mjs '{"type":"device","keyword":"华为"}'
```

**不需要调用 `get-targeting-lookup.mjs` 的定向维度（脚本自动匹配枚举）**：

- **性别**：直接用 `["MALE"]` / `["FEMALE"]` / 不传
- **年龄**：直接用 `[{"min":25,"max":29}, {"min":30,"max":39}]` 格式的数组。**`min` 和 `max` 均为闭区间（包含边界值）**，按用户原始区间构造，**不要合并连续段**
- **操作系统**（`user_os`）：传 `["IOS"]` / `["ANDROID"]`（全版本），或用简化格式如 `["ANDROID_10+"]` 表示 Android 10 及以上，脚本自动展开为版本列表
- **排除操作系统**（`excluded_os`）：同 `user_os` 的简化格式，也支持 `WINDOWS`、`HARMONY` 等直接枚举
- **联网方式**（`network_type`）：传 `["WIFI"]`、`["4G"]`、`["5G"]`，脚本自动匹配为 API 枚举（如 `4G` → `NET_4G`）
- **学历**（`education`）：传中文即可，如 `["本科", "硕士"]`，脚本自动匹配为 API 枚举（如 `本科` → `BACHELOR`）
- **设备价格**（`device_price`）：传简化描述即可，如 `["2500以上"]`、`["1500-3500"]`，脚本自动展开为对应的价格区间枚举
- **微信广告行为**（`wechat_ad_behavior`）：传中文即可，脚本自动匹配为 API 枚举
- **排除已转化**：通过枚举查询后构造

**枚举查询**：

```bash
# 查询单个/多个字段的枚举
node scripts/get-enum-options.mjs '{"fields":["education","device_price","network_type","user_os"]}'

# 按分类查询所有定向相关枚举
node scripts/get-enum-options.mjs '{"category":"targeting"}'
```

**只有在以下情况才可跳过定向查询**：用户完全没有给任何地域或设备定向约束。

> **通投（不限定向）时传 `targeting: {}`（空对象）**。

### 完整定向维度对照表

| 定向维度 | targeting 子字段 | 说明 | 获取方式 |
|----------|-----------------|------|----------|
| 地域 | `geo_location.regions` + `geo_location.location_types` | regions 通过地域查询获取；`location_types` 常见值 `LIVE_IN`（常住） | `get-targeting-lookup.mjs type:geo` + 枚举查询 |
| 性别 | `gender` | `["MALE"]` / `["FEMALE"]` | 直接构造 |
| 年龄 | `age` | `[{"min":25,"max":29}]`（闭区间，不要合并连续段） | 直接构造 |
| 操作系统 | `user_os` | 支持简化格式如 `["ANDROID_10+"]`，脚本自动展开 | 查枚举后直接构造 |
| 排除操作系统 | `excluded_os` | 同 `user_os` 简化格式 | 查枚举后直接构造 |
| 学历 | `education` | 传中文如 `["本科", "硕士"]`，脚本自动匹配枚举 | 脚本自动匹配 |
| 婚恋状态 | `marital_status` | 枚举查询 | 查枚举后直接构造 |
| 联网方式 | `network_type` | 传 `["4G"]`、`["5G"]`，脚本自动匹配枚举 | 脚本自动匹配 |
| 设备价格 | `device_price` | 传 `["2500以上"]`，脚本自动展开为价格区间枚举 | 脚本自动匹配 |
| 设备品牌型号 | `device_brand_model` | **必须使用数字 ID**，格式 `{"included_list": [1,5], "excluded_list": []}` | `get-targeting-lookup.mjs type:device` |
| 应用安装状态 | `app_install_status` | 仅推广 APP 时可用 | 查枚举后直接构造 |
| 游戏消费能力 | `game_consumption_level` | 枚举查询 | 查枚举后直接构造 |
| 兴趣分类 | `interest_category_id_list` | 兴趣分类 ID 列表 | 通过 `tencentads-targeting` 获取 |
| 兴趣关键词 | `interest_keyword_id_list` | 兴趣关键词 ID 列表 | 通过 `tencentads-targeting` 获取 |
| 行为分类 | `behavior_category_id_list` | 行为分类 ID 列表 | 通过 `tencentads-targeting` 获取 |
| 行为关键词 | `behavior_keyword_id_list` | 行为关键词 ID 列表 | 通过 `tencentads-targeting` 获取 |
| 自定义人群 | `custom_audience` | 人群包 ID 列表 | 用户提供 |
| 排除人群 | `excluded_custom_audience` | 排除的人群包 ID | 用户提供 |
| 排除已转化 | `excluded_converted_audience` | 见下方格式说明 | 查枚举后直接构造 |
| 微信广告行为 | `wechat_ad_behavior` | 见下方格式说明 | 脚本自动匹配 |

**`excluded_converted_audience` 格式**（仅在用户明确提到"排除已转化"时才添加，禁止自行添加）：
```json
{
  "excluded_dimension": "<通过 get-enum-options.mjs 查 excluded_dimension>",
  "excluded_day": "<通过 get-enum-options.mjs 查 excluded_day>"
}
```

**`wechat_ad_behavior` 格式**（仅在用户明确提到微信广告行为定向/排除时才添加，禁止自行添加）：

正向定向（`actions`）：用户说"定向已关注公众号的用户"等；排除行为（`excluded_actions`）：用户说"排除已关注公众号的用户"等。枚举分别通过 `get-enum-options.mjs '{"fields":["wechat_ad_behavior_actions"]}'` 和 `'{"fields":["wechat_ad_behavior_excluded_actions"]}'` 查询。

```json
"wechat_ad_behavior": {
  "actions": ["GDT_WECHAT_OFFICIAL_ACCOUNT_FOLLOWED"],
  "wechat_official_account_id": ["wx18c408376c727a19"]
}
```
```json
"wechat_ad_behavior": {
  "excluded_actions": ["GDT_WECHAT_OFFICIAL_ACCOUNT_FOLLOWED"],
  "wechat_official_account_id": ["wx18c408376c727a19"]
}
```
- 涉及公众号行为时，需同时传 `wechat_official_account_id`（用户给的公众号 ID）
- 涉及企业微信行为时，需同时传 `corp_id`

### 定向更新示例

**示例 A：修改定向为北京+上海，25-45岁男性**（需要先查地域编码）

```bash
# 步骤1：查地域编码
node scripts/get-targeting-lookup.mjs '{"type":"geo","keyword":"北京 上海"}'
# 返回 110000（北京）、310000（上海）

# 步骤2：构造 targeting 并更新
node scripts/update-adgroup-general.mjs '{"account_id":12345678,"adgroup_id":111111,"targeting":{"geo_location":{"location_types":["LIVE_IN"],"regions":[110000,310000]},"age":[{"min":25,"max":45}],"gender":["MALE"]}}'
```

**示例 B：修改定向为本科以上、4G+5G、Android 10+**（无需查编码，脚本自动匹配）

```bash
node scripts/update-adgroup-general.mjs '{"account_id":12345678,"adgroup_id":111111,"targeting":{"education":["本科","硕士","博士"],"network_type":["4G","5G"],"user_os":["ANDROID_10+"]}}'
```

**示例 C：修改定向为不限（通投）**

```bash
node scripts/update-adgroup-general.mjs '{"account_id":12345678,"adgroup_id":111111,"targeting":{}}'
```

**示例 D：修改定向为指定设备品牌（苹果+华为）**（需先查设备 ID）

```bash
# 步骤1：查设备品牌 ID
node scripts/get-targeting-lookup.mjs '{"type":"device","keyword":"苹果 华为"}'
# 返回 苹果=1, 华为=5

# 步骤2：构造 targeting 并更新（注意 device_brand_model 的嵌套格式）
node scripts/update-adgroup-general.mjs '{"account_id":12345678,"adgroup_id":111111,"targeting":{"device_brand_model":{"included_list":[1,5],"excluded_list":[]}}}'
```

### 定向强约束

- 命中触发规则后，**必须先调用 `get-targeting-lookup.mjs` 获取编码**，再构造 `targeting`
- 不要把自然语言直接翻成粗粒度占位值
- 所有枚举值**禁止凭记忆猜测**，必须通过 `get-enum-options.mjs` 查询确认
- targeting 中不能包含不可修改的字段（脚本会拦截）：marketing_goal、marketing_sub_goal、marketing_target_type、marketing_carrier_type、marketing_asset_id、marketing_asset_outer_spec、subordinate_product_id、asset_name、site_set、bid_mode、optimization_goal

---

## 不支持修改的字段（创建时绑定）

以下字段在广告/智投项目创建后不可修改，如果用户要求修改这些字段，应建议到投放端手动操作或删除重建：

- marketing_goal / marketing_sub_goal（营销目的）
- marketing_target_type / marketing_carrier_type（推广产品/载体类型）
- marketing_asset_id / marketing_asset_outer_spec（推广产品）
- bid_mode / optimization_goal（出价方式/优化目标）
- site_set（版位）
- conversion_id（转化 ID）

---

## 脚本调用示例

### 示例 1：修改出价

```bash
node scripts/update-adgroup-general.mjs '{"account_id":12345678,"adgroup_id":111111,"bid_amount":12050}'
```

### 示例 2：同时修改出价和预算

```bash
node scripts/update-adgroup-general.mjs '{"account_id":12345678,"adgroup_id":111111,"bid_amount":12050,"daily_budget":60000}'
```

### 示例 3：修改定向为不限

```bash
node scripts/update-adgroup-general.mjs '{"account_id":12345678,"adgroup_id":111111,"targeting":{}}'
```

### 示例 3b：修改定向（地域+年龄+学历+联网方式）

> 地域编码需先通过 `get-targeting-lookup.mjs` 查询；学历和联网方式可直接传简化值，脚本自动匹配为 API 枚举。

```bash
# 先查地域编码
node scripts/get-targeting-lookup.mjs '{"type":"geo","keyword":"北京 上海 广州"}'
# 返回 110000, 310000, 440100

# 再执行更新
node scripts/update-adgroup-general.mjs '{"account_id":12345678,"adgroup_id":111111,"targeting":{"geo_location":{"location_types":["LIVE_IN"],"regions":[110000,310000,440100]},"age":[{"min":25,"max":45}],"education":["本科","硕士"],"network_type":["4G","5G"]}}'
```

### 示例 4：暂停广告

```bash
node scripts/update-adgroup-general.mjs '{"account_id":12345678,"adgroup_id":111111,"configured_status":"AD_STATUS_SUSPEND"}'
```

### 示例 5：开启一键起量

```bash
node scripts/update-adgroup-general.mjs '{"account_id":12345678,"adgroup_id":111111,"auto_acquisition_enabled":true,"auto_acquisition_budget":50000}'
```

### 示例 6：修改投放时段（工作日 9:00-18:00）

```bash
node scripts/update-adgroup-general.mjs '{"account_id":12345678,"adgroup_id":111111,"delivery_time_ranges":["Monday 09:00~18:00","Tuesday 09:00~18:00","Wednesday 09:00~18:00","Thursday 09:00~18:00","Friday 09:00~18:00"]}'
```

### 示例 6b：修改投放时段并指定首日开始时间

```bash
node scripts/update-adgroup-general.mjs '{"account_id":12345678,"adgroup_id":111111,"delivery_time_ranges":["Monday 09:00~18:00","Tuesday 09:00~18:00","Wednesday 09:00~18:00","Thursday 09:00~18:00","Friday 09:00~18:00"],"first_day_begin_time":"09:00:00"}'
```

### 示例 6c：仅修改首日开始时间（无需同时传投放时段）

```bash
node scripts/update-adgroup-general.mjs '{"account_id":12345678,"adgroup_id":111111,"first_day_begin_time":"11:00:00"}'
```

### 示例 7：多字段同时更新

```bash
node scripts/update-adgroup-general.mjs '{"account_id":12345678,"adgroup_id":111111,"adgroup_name":"Q2-电商-促销活动","bid_amount":8000,"daily_budget":100000,"begin_date":"2026-04-15","end_date":"2026-05-15","targeting":{"geo_location":{"location_types":["LIVE_IN"],"regions":[110000,310000,440100]},"age":[{"min":25,"max":45}]}}'
```

### 示例 8：出价下调 10%

```bash
node scripts/update-adgroup-general.mjs '{"account_id":12345678,"adgroup_id":111111,"bid_amount_adjustment":"-10%"}'
```

### 示例 9：预算翻倍

```bash
node scripts/update-adgroup-general.mjs '{"account_id":12345678,"adgroup_id":111111,"daily_budget_adjustment":"*2"}'
```

### 示例 10：出价加 0.5 元，预算增加 30%

```bash
node scripts/update-adgroup-general.mjs '{"account_id":12345678,"adgroup_id":111111,"bid_amount_adjustment":"+50","daily_budget_adjustment":"+30%"}'
```

### 示例 11：深度优化行为出价设为 30 元

```bash
node scripts/update-adgroup-general.mjs '{"account_id":12345678,"adgroup_id":111111,"deep_conversion_behavior_bid":3000}'
```

### 示例 12：深度优化行为出价下调 15%

```bash
node scripts/update-adgroup-general.mjs '{"account_id":12345678,"adgroup_id":111111,"deep_conversion_behavior_bid_adjustment":"-15%"}'
```

### 示例 13：深度优化期望ROI系数设为 1.5

```bash
node scripts/update-adgroup-general.mjs '{"account_id":12345678,"adgroup_id":111111,"deep_conversion_worth_rate":1.5}'
```

### 示例 14：深度优化期望ROI系数上调 10%

```bash
node scripts/update-adgroup-general.mjs '{"account_id":12345678,"adgroup_id":111111,"deep_conversion_worth_rate_adjustment":"+10%"}'
```

### 示例 15：关闭一键起量

```bash
node scripts/update-adgroup-general.mjs '{"account_id":12345678,"adgroup_id":111111,"auto_acquisition_enabled":false}'
```

### 示例 16：一键起量已开启时调整起量预算

> 用户说"起量预算改为500元"，当前一键起量已开启。
> 直接传入新的 `auto_acquisition_budget`（单位：分，500元=50000分）即可，脚本内部自动完成"先关闭再用新预算重新开启"的流程。

```bash
node scripts/update-adgroup-general.mjs '{"account_id":12345678,"adgroup_id":111111,"auto_acquisition_budget":50000}'
```

### 示例 16a：一键起量已开启时用相对表达式调整起量预算

> 用户说"起量预算上调10%"，当前一键起量已开启。
> 传入 `auto_acquisition_budget_adjustment` 表达式即可，脚本自动基于当前值计算目标绝对值，再执行先关后开流程。

```bash
node scripts/update-adgroup-general.mjs '{"account_id":12345678,"adgroup_id":111111,"auto_acquisition_budget_adjustment":"+10%"}'
```

### 示例 17：开启创意衍生（自动使用推荐衍生方式）

> 只需传 `auto_derived_creative_enabled: true`，脚本自动查询 `muse_derive_switch_info/get` 获取可用衍生方式并使用默认推荐项。

```bash
node scripts/update-adgroup-general.mjs '{"account_id":12345678,"adgroup_id":111111,"auto_derived_creative_enabled":true}'
```

### 示例 18：开启创意衍生并指定衍生方式

> 显式指定衍生方式列表，脚本会校验每项是否对该广告可用。

```bash
node scripts/update-adgroup-general.mjs '{"account_id":12345678,"adgroup_id":111111,"auto_derived_creative_enabled":true,"auto_derived_creative_method_type_list":["AUTO_DERIVED_CREATIVE_METHOD_TYPE_OUTPAINTING","AUTO_DERIVED_CREATIVE_METHOD_TYPE_TEMPLATE"]}'
```

### 示例 19：关闭创意衍生

```bash
node scripts/update-adgroup-general.mjs '{"account_id":12345678,"adgroup_id":111111,"auto_derived_creative_enabled":false}'
```

### 示例 20-23：周期达成项目的编辑操作

周期达成项目的编辑操作包含周期预算调整、续投开关切换等，详细说明和完整示例见 [references/smart-delivery-period-update.md](references/smart-delivery-period-update.md)。

---

## 注意事项

1. **targeting 中不能包含非法字段**：完整清单见上方"定向强约束"章节，脚本会拦截报错。

2. **targeting 枚举自动匹配**：脚本内置枚举简化值自动转换，详见上方"定向更新 SOP"章节。

3. **定向辅助脚本**：`get-targeting-lookup.mjs` 和 `get-enum-options.mjs` 在本 skill 的 `scripts/` 目录下可直接调用（软链接指向共享实现）。

4. **first_day_begin_time 交叉校验**：与 `delivery_time_ranges` 同时传入时脚本会校验首日时间槽是否在投放范围内，不兼容则报错。**重要：用户未明确要求修改 `first_day_begin_time` 时，禁止自行添加该参数**——多传会触发 API 对 `begin_date` 的连带校验，导致已投放广告更新失败。

5. **无变化字段自动跳过**：脚本会先查询广告当前值，如果某字段的目标值与当前值一致，该字段会被跳过（不调用更新 API），输出中会列出 skipped_fields。

6. **广告存在性校验**：脚本执行前会先查询广告是否存在、是否已删除。如果广告不存在或已删除，直接报错不调用更新 API。

7. **搜索广告拦截**：当前版本暂不支持搜索广告更新操作，脚本执行前会检查广告的 `site_set` 是否包含搜索版位（`SITE_SET_WECHAT_SEARCH`、`SITE_SET_QBSEARCH`、`SITE_SET_SEARCH_MOBILE_UNION`）。如果是搜索广告，脚本会直接报错并输出 `is_search_ad: true` 标识，不调用更新 API。

8. **一键起量编辑规则**：
   - ⛔ **智投项目不支持使用一键起量**：如果目标广告是智投项目，不允许执行一键起量的开启、关闭或预算调整操作。应直接拒绝并告知用户：「智投项目不支持使用一键起量功能，一键起量仅适用于标准投放广告。」
   - **新开启**（当前关闭 -> enabled=true）：**必须**同时设置 `auto_acquisition_budget`，传入绝对值（分）
   - **新关闭**（当前开启 -> enabled=false）：**不可**同时设置 budget
   - **已开启时调整 budget**：传入 `auto_acquisition_budget`（绝对值，分）或 `auto_acquisition_budget_adjustment`（相对表达式，如 "+10%"、"+20000"）均可，脚本内部自动完成先关闭再用新预算重新开启的流程（见示例 16、16a）。
   - **已关闭时**：不可单独调整 budget（如需设置请同时传 `auto_acquisition_enabled: true`）

9. **周期达成编辑规则**：详情见 [references/smart-delivery-period-update.md](references/smart-delivery-period-update.md)。核心要点：
   - ⚠️ **周期达成开关不可修改**：`smart_delivery_period_switch` 在创建时确定后无法通过编辑接口开启或关闭。非周期达成项目不能变成周期达成项目，反之亦然。
   - ⚠️ **周期达成项目的特殊限制**：如果目标项目是周期达成项目，以下限制自动生效：
     - **禁止修改**：`begin_date`（开始日期）、`end_date`（结束日期）、`targeting`（定向）、`configured_status`（启停状态）
     - **只允许提升**：`bid_amount`（出价）、`smart_delivery_period_budget`（周期预算）、`deep_conversion_behavior_bid`（深层出价）只能往上调，不能降低；`deep_conversion_worth_rate`（ROI）只允许降低（ROI 低 = 目标放宽）
     - **允许修改**：`delivery_time_ranges`（投放时段）、`first_day_begin_time`（首日时间）
     - **禁止设置**：`daily_budget`（日预算）、`total_budget`（总预算）
     - **预算约束**：修改后的 `smart_delivery_period_budget` 仍须满足 ≥ 3 × 出价 × 周期天数
   - **修改续投开关**（`smart_delivery_period_continue`）：
     - 从"不续投"→"续投"（`PERIOD_CONTINUE_SWITCH_ON`）：项目需未过期，切换后 `end_date` 自动清空（变为长期投放）
     - 从"续投"→"不续投"（`PERIOD_CONTINUE_SWITCH_OFF`）：系统自动计算当前周期的 `end_date`
   - **修改周期预算**（`smart_delivery_period_budget`）：只允许提升，不允许降低

10. **创意衍生编辑规则**：
   - **开启**（enabled=true）：脚本自动查询 `muse_derive_switch_info/get` 获取可用衍生方式。若广告不支持衍生（API 返回 `show_derive_method=false` 且无可用方式），脚本报错。可选传入 `auto_derived_creative_method_type_list` 指定偏好，不传则使用默认推荐。
   - **关闭**（enabled=false）：直接关闭，无需传 method_type_list
   - **仅更新偏好**：不传 enabled，仅传 `auto_derived_creative_method_type_list` 可单独更新衍生偏好（不校验可用性，适用于已知合法值的场景）
   - 支持中文别名自动解析：如 `["AI模板", "扩图"]` 自动转换为标准枚举 key

---

## 批量更新脚本（update-adgroup-batch.mjs）

多账号多广告/智投项目异构字段批量更新，每个广告/项目可更新完全不同的字段组合。

### 适用场景

- 用户需要同时修改 2 个及以上广告或智投项目
- 不同广告/项目需要更新不同的字段（异构）
- 跨账号批量操作

### 入参格式

```json
{
  "tasks": [
    { "account_id": 123, "adgroup_id": "111", "bid_amount": 12050 },
    { "account_id": 123, "adgroup_id": "222", "adgroup_name": "新名", "configured_status": "AD_STATUS_SUSPEND" },
    { "account_id": 456, "adgroup_id": "333", "bid_amount_adjustment": "+20%" }
  ]
}
```

每个 task 的格式与 `update-adgroup-general.mjs` 的入参完全一致（`account_id` + `adgroup_id` + 更新字段）。

### 约束

- `tasks` 数组最多 50 个元素
- 每个 task 必须包含 `account_id` 和 `adgroup_id`
- 每个 task 至少包含一个更新字段
- **如果任何一个 task 格式不合法（缺少必填字段），整个批次会被拒绝**（fast-fail）

### 执行流程

1. 预校验所有 task 格式（fast-fail）
2. 按 `account_id` 分组
3. 各账号**并行**处理：
   - 批量前置查询（同账号内一次 `adgroups/get`）
   - 逐个广告串行：`buildUpdateBody` + `adgroups/update`
4. 各账号**并行**回查验证
5. 汇总输出所有结果

### 输出格式

```json
{
  "total": 3,
  "success_count": 2,
  "fail_count": 1,
  "skip_count": 0,
  "message": "2 个成功，1 个失败，0 个跳过。请务必将失败详情告知用户",
  "results": [
    {
      "account_id": 123,
      "adgroup_id": 111,
      "success": true,
      "updated_fields": { "bid_amount": { "previous": 10000, "target": 12050, "unit": "fen" } },
      "message": "广告 111 更新成功: bid_amount 10000 -> 12050 分"
    },
    {
      "account_id": 456,
      "adgroup_id": 333,
      "success": false,
      "error": "bid_amount_adjustment: 当前出价为 0，无法进行相对调整，请使用 bid_amount 传入绝对值（单位：分）",
      "message": "广告 333 更新失败: ..."
    }
  ]
}
```

### 脚本调用示例

#### 示例 B1：同账号多广告批量更新（相同字段）

```bash
node scripts/update-adgroup-batch.mjs '{"tasks":[{"account_id":12345678,"adgroup_id":111,"bid_amount":50},{"account_id":12345678,"adgroup_id":222,"bid_amount":50}]}'
```

#### 示例 B2：同账号多广告异构更新（不同字段）

```bash
node scripts/update-adgroup-batch.mjs '{"tasks":[{"account_id":12345678,"adgroup_id":111,"bid_amount":50},{"account_id":12345678,"adgroup_id":222,"daily_budget":600,"configured_status":"AD_STATUS_SUSPEND"}]}'
```

#### 示例 B3：跨账号批量更新

```bash
node scripts/update-adgroup-batch.mjs '{"tasks":[{"account_id":11111,"adgroup_id":111,"bid_amount_adjustment":"+10%"},{"account_id":22222,"adgroup_id":222,"bid_amount_adjustment":"+10%"}]}'
```

#### 示例 B4：使用文件传参（参数较长时推荐）

```bash
node scripts/update-adgroup-batch.mjs --file /tmp/batch_params.json
```

> **批量场景的 Pre-update Check 提醒**：步骤 3 复述时必须列出每条 `(account_id, adgroup_id)` 的「当前值 → 目标值」；fast-fail 只能拒绝整批的预校验，**已执行的子任务不会自动回滚**，需在确认时告知用户。

### 部分成功场景的 Agent 行为

批量更新可能出现部分成功、部分失败的情况。Agent 必须：

1. **逐条展示结果**：遍历 `results` 数组，向用户说明每个广告的更新结果
2. **重点关注失败项**：失败广告的 `error` 和 `message` 必须完整告知用户
3. **检查 side_effects**：如果失败结果中包含 `side_effects` 字段，**必须告知用户已发生的副作用**（如一键起量在调整预算时已被关闭但主更新失败）
4. **回查比对**：对成功的广告，基于 `_verify` 数据与用户期望对比
5. **回查失败提醒**：如果输出中包含 `_verify_failed` 的广告，提醒用户手动确认这些广告的更新结果
