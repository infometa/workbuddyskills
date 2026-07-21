---
name: tencentads-delivery-smart-create
description: "专用于创建智投(AIM+)营销单元（原广告组）的 SDK 化技能。当用户意图涉及智投、AIM+、艾米、智能投放、自动投放、小店智投、smart delivery 的**创建**场景时，使用本技能。覆盖场景：小店艾米、商品艾米、线索艾米、内容艾米、APP艾米(游戏/阅读/AI应用)、小游戏跑量、爆剧跑量、小说智投、全域通、视频号直播智投等。本技能通过专用脚本（而非全局 CLI 工具）调用 API，脚本已处理复杂分支、字段过滤和数据转换。"
license: MIT. See LICENSE for full terms.
compatibility: any
metadata:
  author: Tencent Ads Delivery Team
  version: "0.5.8"
  icon: megaphone
  category: tencent-ads
---

> **前置依赖**：需安装 `tencentads-cli`（Node.js ≥ 20）。执行 `npm install -g tencentads-cli@latest` 安装或升级；版本过低时 `tencentads` 会给出提示。

本技能是智投广告的**执行指南**——按 7 个步骤顺序完成一条智投广告的创建。**严格按步骤顺序执行，后面的步骤依赖前面的输出，不可跳步。**

所有 API 调用均通过本技能的**专用脚本**执行，脚本负责：API 分支路由、返回数据裁剪、格式转换（rules_json 解析、geo 编码查找等）。Agent 专注于：从脚本返回结果中做出业务决策（选哪个组合、选哪个转化目标）。

> **脚本调用格式统一**：`node scripts/<脚本名>.mjs '<JSON 参数>'`
> 执行脚本时先进入本 skill 根目录，再按相对 `scripts/` 路径调用。

### ⚠️ 跨平台 JSON 参数传递规则（经实测验证）

脚本调用格式为 `node scripts/<脚本名>.mjs '<JSON参数>'`，但 **JSON 参数的引号包裹方式因操作系统/终端而异**，传递不当会导致 `JSON.parse` 报错（如 `Expected property name or '}' in JSON at position 1`）。

| 终端环境 | 正确写法 | 说明 |
|---------|---------|------|
| **Linux / macOS (Bash/Zsh)** | `node scripts/xxx.mjs '{"key":"value"}'` | ✅ 单引号包裹，内部双引号原样保留 |
| **Windows Git Bash** | `node scripts/xxx.mjs '{"key":"value"}'` | ✅ 同 Bash |
| **Windows CMD** | `node scripts/xxx.mjs "{\"key\":\"value\"}"` | ✅ 双引号包裹 + 反斜杠转义 |
| **Windows CMD (备选)** | `node scripts/xxx.mjs "{""key"":""value""}"` | ✅ 双引号包裹 + 双双引号转义 |
| **Windows PowerShell 5.x** | `node --% scripts/xxx.mjs "{\"key\":\"value\"}"` | ✅ 必须加 `--%` 停止解析符 |
| **Windows PowerShell 5.x (备选)** | `` node scripts/xxx.mjs "{\`"key\`":\`"value\`"}" `` | ✅ 反斜杠 + 反引号组合转义 |

> **⛔ PowerShell 5.x 是重灾区**：单引号 `'...'`、反引号 `` `" `` 、反斜杠 `\"` 三种常见写法**全部失败**（双引号会被吞掉）。必须使用 `--% ` 停止解析符或 `` \`" `` 组合转义。
> **⛔ Windows CMD 不支持单引号包裹字符串**，单引号会被当作普通字符传入脚本，导致 JSON 解析失败。

```
⛔ 执行顺序（不可跳步）：

步骤1 → 步骤2 → 步骤3 → 步骤4 → 步骤5 → 步骤6 → 步骤7
确定      获取      获取       确定      获取      配置       组装请求体
智投场景  四元组    推广产品   版位      转化目标  定向+时段  → create-adgroup.mjs
                    +载体               +出价
```

---

## 执行协议（高优先级，覆盖后文）

> 若本节与下文"继续执行""不要重复查询"等表述冲突，以本节为准。

1. **⛔ 步骤 1 → 2 → 3 是绝对必须执行的前三步，不可跳过。** 即使用户 input 中看起来已包含场景、四元组、商品信息，仍必须调用 `get-rules.mjs` 确认四元组、调用 `get-assets.mjs` 获取推广资产 ID。原因：不同账号的可选组合不同，自然语言描述无法直接转为精确的枚举值和 ID。步骤 4-6 中的查询子动作在满足"显式证据白名单"时可跳过，但步骤 1-3 不可。
2. **进入下一步前，必须先拿到上一步输出并确认来源。** 合法来源只有三类：用户在原始需求中明确给出、当前 session 前一步脚本返回、当前 session 前一步 API 返回。
3. **自然语言意图不能替代结构化字段。** "小游戏拉新""微信小游戏""新客增长"等描述只能用于步骤 1 识别场景，不能直接当作四元组、营销载体 ID、`conversion_id` 的依据。
4. **进入步骤 7 前必须能回答每个关键字段来自哪里。** 说不清来源的字段，不要猜。
5. **⚠️ 错误处理与重试限制**：每个脚本调用最多重试 **1 次**（换参数或换调用方式）。如果 2 次仍失败（如返回 "Mock not found"、空结果、报错），**立即跳过该步骤，用已有数据继续推进到下一步直至步骤 7**。严禁反复重试同一脚本、读取脚本源码、或切换到非脚本方式（如 `tencentads-cli api`）尝试绕过。宁可在最终请求中缺少某个字段，也不要耗尽所有轮次。
6. **显式证据白名单（仅适用于步骤 4-6 的查询子动作，步骤 1-3 不适用）**：
   - 四元组查询：用户明确给出 `marketing_goal`、`marketing_sub_goal`、`marketing_target_type`、`marketing_carrier_type` 这 4 个枚举值全部；或当前 session 已从 `get-rules.mjs` 返回中得到。
   - 推广产品 / 营销载体查询：用户明确给出构造请求体所需的完整 ID；或当前 session 已从 `get-assets.mjs` 返回中得到。
   - 转化目标查询：用户明确给出 `conversion_id`；或当前 session 已从 `get-conversions.mjs` 返回中得到。
   - 定向查询：用户没有任何定向约束时可跳过；只要用户给了定向要求，地域/设备编码通过 `get-targeting-lookup.mjs` 查询，其他枚举通过 `get-enum-options.mjs` 查询。

---

## 步骤 1（⛔ 最先执行）：确定智投场景

> **前置**：用户意图
> **输出**：`smart_delivery_platform`、`delivery_scene`（数值）

根据用户意图从下表匹配 `smart_delivery_platform` 枚举值。枚举统一前缀 `SMART_DELIVERY_PLATFORM_EDITION_`（表中用 `...` 省略）。

> ⚠️ 小店枚举名与中文业务名严重不一致：`SINGLE_PRODUCT` = 短直双开（不是"单品"），`PRODUCT_OR_LIVE` = 小店单链路（不是"品商直播合开"）。

| 分类 | 场景名称 | 枚举 key | value | 识别关键词 |
|------|----------|----------|-------|-----------|
| 小店(3000) | 短直双开 | `..._WECHAT_STORE_SINGLE_PRODUCT` | `3001` | 短直双开、短视频+直播、双链路 |
| 小店(3000) | 小店单链路智投 | `..._WECHAT_STORE_PRODUCT_OR_LIVE` | `3002` | 单链路、小店单链路 |
| 小店(3000) | 全店托管智投 | `..._WECHAT_STORE_MANAGEMENT` | `3003` | 全店托管、托管 |
| 小店(3000) | 推直播间 | `..._WECHAT_STORE_LIVE` | `3004` | 推直播间、直播间引流 |
| 小店(3000) | 推商品 | `..._WECHAT_STORE_PRODUCT` | `3005` | 推商品（仅指小店的"推商品"入口，不带"智投"二字） |
| 生态(1000) | 爆剧跑量 | `..._ECOLOGY_PLAYLET` | `1001` | 爆剧、短剧、微短剧 |
| 生态(1000) | 线索跑量 | `..._ECOLOGY_LEADS` | `1002` | 线索艾米、线索跑量、表单 |
| 生态(1000) | 小游戏跑量 | `..._MINI_GAME_PROMOTION` | `1003` | 小游戏 |
| 生态(1000) | 商品智投 | `..._DRUG_PRODUCT` | `1018` | 商品艾米、商品智投、推商品智投、医药智投（注意：带"智投"二字的"推商品智投"属于此场景，不是小店的"推商品"） |
| 生态(1000) | 小说智投 | `..._FICTION` | `1019` | 小说、网文 |
| 全域通(4000) | 全域通-直播 | `..._QYT_LIVE` | `4001` | 全域通+直播 |
| 全域通(4000) | 全域通-直购 | `..._QYT_WECHAT_STORE` | `4002` | 全域通+直购/小店 |
| APP(6000) | 游戏应用智投 | `..._GAME_APP` | `6001` | 游戏APP、游戏应用 |
| APP(6000) | 阅读应用智投 | `..._READING_APP` | `6002` | 阅读APP、阅读应用 |
| APP(6000) | AI应用智投 | `..._AI_APP` | `6003` | AI应用、AI APP |

**步骤 1 完成后你应该有**：`smart_delivery_platform` 枚举值，以及同场景的数值 `delivery_scene`（即上表 `value` 列）。

> **字段含义拆开记**：
> - `smart_delivery_platform`：字符串枚举，如 `SMART_DELIVERY_PLATFORM_EDITION_MINI_GAME_PROMOTION`
> - `delivery_scene`：数值 value，如 `1003`
> - 调 `get-rules.mjs` 时，`delivery_scene` 传 `smart_delivery_platform` **字符串枚举**，不是数值 `1003`
> - 调 `get-conversions.mjs` 等投放端内部接口时，再传数值 `delivery_scene`

---

## 步骤 2（⛔ 默认必须执行，仅白名单可跳过）：获取四元组

> **前置**：`account_id` + 步骤 1 的 `smart_delivery_platform`
> **输出**：`marketing_goal`、`marketing_sub_goal`、`marketing_target_type`、`marketing_carrier_type`

**四元组**是腾讯广告的产品术语，指**营销内容 + 转化/优化目标的完整匹配集合**，共10个字段：
- 营销内容（4个）：`marketing_goal`、`marketing_sub_goal`、`marketing_carrier_type`、`marketing_target_type`
- 转化/优化目标（6个）：`optimization_goal`、`deep_behavior_optimization_goal`、`deep_behavior_advanced_goal`、`deep_worth_optimization_goal`、`deep_worth_advanced_goal`、`forward_link_assist`

这10个字段作为一个整体定义广告的投放语义，**必须从脚本返回的可选范围中选取，禁止通过推理猜测**。

**为什么不能猜？**
- 不同账号准入的组合不同，猜错会导致 `adgroups/add` 报错
- 看似相同的场景（如"小游戏推广"），在不同账号上对应的 `marketing_goal` 可能完全不同
- 四元组错误会级联导致后续推广产品、转化目标等全部错误

**调用方式**：

```bash
node scripts/get-rules.mjs '{"account_id":"<ACCOUNT_ID>","delivery_scene":"<smart_delivery_platform枚举值>"}'
```

示例：
```bash
node scripts/get-rules.mjs '{"account_id":"123456789","delivery_scene":"SMART_DELIVERY_PLATFORM_EDITION_MINI_GAME_PROMOTION"}'
```

**脚本已处理**：内部解析 `rules_json` 嵌套 JSON 字符串，展开四层嵌套树为扁平组合列表。

**返回示例**：
```json
{
  "combinations": [
    {
      "marketing_goal": "MARKETING_GOAL_APP_PROMOTED",
      "marketing_sub_goal": "MARKETING_SUB_GOAL_APP_INSTALL",
      "marketing_target_type": "MARKETING_TARGET_TYPE_WECHAT_MINI_GAME",
      "marketing_carrier_type": "MARKETING_CARRIER_TYPE_MINI_PROGRAM"
    }
  ]
}
```

**Agent 需要做的决策**：从 `combinations` 中确定唯一的一组四元组。

### 情况 A：返回 1 个组合 → 直接确定

`combinations` 只有 1 条时，四元组已唯一确定，**不需要任何选择逻辑**，直接取该条进入步骤 3。

### 情况 B：返回多个组合 → 需要按规则选择

`combinations` 有多条时，按以下**优先级从高到低**逐层过滤，直到缩小为唯一一组。**切忌乱猜四元组，一旦选错后续推广产品、转化目标等全部级联错误。**

**选择规则（按优先级）**：

1. **（最高优先级）通过资产 ID 反推**：

   > **触发条件**：用户在 input 中明确给出了 `推广产品ID`、`产品ID`、`推广资产ID`、`资产ID`、`应用ID`、`游戏ID`、`APP ID`、`marketing_asset_id`、`product_id`、`marketing_asset_outer_id` 等资产标识。

   资产 ID 能直接关联到某个 `marketing_target_type`，因此可反推缩小四元组范围。调用 `get-assets-by-rules.mjs`：

   ```bash
   node scripts/get-assets-by-rules.mjs '{"account_id":"<ACCOUNT_ID>","combinations":<get-rules返回的combinations数组>}'
   ```

   脚本内部自动对 `marketing_target_type` 去重，每种只调一次 API，返回 `asset_map`（以 `marketing_target_type` 为 key）。返回结构与 `get-assets.mjs` **完全一致**（含 `flat_params`、`type` 等字段），可直接复用于步骤 3 的资产选择：

   ```json
   {
     "asset_map": {
       "MARKETING_TARGET_TYPE_REAL_ESTATE": {
         "asset_type": "INDUSTRY",
         "assets": [
           {
             "marketing_asset_id": "342574",
             "name": "京投发展森与天成",
             "type": "REAL_ESTATE",
             "flat_params": {
               "asset_id": "342574"
             }
           }
         ]
       },
       "MARKETING_TARGET_TYPE_WECHAT_MINI_GAME": {
         "asset_type": "ONEID",
         "assets": [
           {
             "marketing_asset_outer_id": "wx123",
             "marketing_carrier_id": "wx123",
             "name": "某小游戏",
             "type": "WECHAT_MINI_GAME",
             "flat_params": {
               "asset_id": "wx123",
               "carrier_id": "wx123",
               "asset_name": "某小游戏",
               "carrier_name": "某小游戏"
             }
           }
         ]
       }
     }
   }
   ```

   **反推流程**：
   - 遍历 `asset_map` 各 target_type 下的 `assets`，用 `flat_params.asset_id` 统一匹配用户给出的资产 ID（无需区分 `marketing_asset_id` / `marketing_asset_outer_id` / `product_outer_id`，`flat_params.asset_id` 已归一化）
   - **找到** → 确定了该资产所属的 `marketing_target_type`，在 `combinations` 中筛选含该 target_type 的组合。若缩小到唯一一组，四元组确定；若仍有多组（同一 target_type 对应多个 goal/carrier），继续走后续规则。同时**直接保存该资产的 `flat_params`**，步骤 3 选资产时无需再查
   - **找不到** → 资产 ID 反推失败，**不代表用户给的 ID 是错的**（例如小游戏 ID 可能不在 API 返回的列表中），跳过此规则，继续按后续规则选择

2. **从用户意图提取关键约束**：
   - 用户提到了"直播"/"直播间"/"视频号直播" → `marketing_carrier_type` 应含 `WECHAT_CHANNELS_LIVE`
   - 用户提到了"小游戏" → `marketing_target_type` 应含 `WECHAT_MINI_GAME`
   - 用户提到了"小程序" → `marketing_target_type` 应含 `MINI_PROGRAM_WECHAT`
   - 用户提到了"小店商品"/"商品页" → `marketing_target_type` 应含 `WECHAT_STORE_PRODUCT`
   - 用户提到了"跳转页面" → `marketing_carrier_type` 应含 `JUMP_PAGE`
   - 用户提到了"APP"/"应用" → `marketing_carrier_type` 应含 `APP_ANDROID` 或 `APP_IOS`

3. **按 `marketing_goal` 匹配用户的营销目标**：
   - 用户提到"卖货"/"下单"/"成交"/"GMV"/"ROI" → `MARKETING_GOAL_PRODUCT_SALES`
   - 用户提到"拉新"/"注册"/"激活"/"付费" → `MARKETING_GOAL_USER_GROWTH`
   - 用户提到"品牌"/"曝光" → `MARKETING_GOAL_BRAND_PROMOTION`
   - 用户提到"涨粉"/"加关注" → `MARKETING_GOAL_INCREASE_FANS_INTERACTION`
   - 用户提到"留资"/"表单"/"线索" → `MARKETING_GOAL_LEAD_RETENTION`

4. **短直双开场景特殊规则**：短直双开（`WECHAT_STORE_SINGLE_PRODUCT`）有两条链路（直播+短视频），**只需创建一条广告组**。按照直播链路选择四元组——即 `marketing_carrier_type` = `MARKETING_CARRIER_TYPE_WECHAT_CHANNELS_LIVE`、`marketing_target_type` = `MARKETING_TARGET_TYPE_WECHAT_CHANNELS_LIVE`。

5. **若过滤后仍有多个组合 → 必须向用户确认，禁止猜测**。将剩余的所有组合选项列出给用户选择。

6. **`marketing_sub_goal` 只能复用 `get-rules.mjs` 返回值，禁止语义改写**：例如用户说"注册"、"新客"时，不要自造 `MARKETING_SUB_GOAL_USER_REGISTER`；必须原样使用返回的枚举值。

> **智投强约束**：`delivery_scene` 参数传的是 `smart_delivery_platform` 字符串枚举，不是数值。

**步骤 2 完成后你应该有**：四元组 4 个值（从 combinations 数组的匹配项取）。

---

## 步骤 3：获取推广产品 + 营销载体

> **前置**：步骤 2 的 `marketing_target_type`
> **输出**：选定 asset 的 `flat_params`（ONEID 类和视频号直播类已包含 `carrier_id`；行业/商品库类不含 `carrier_id`，若 `carrier_type` 需要载体则需从用户处获取）

**调用方式**：

```bash
node scripts/get-assets.mjs '{"account_id":"<ACCOUNT_ID>","marketing_target_type":"<...>"}'
```

**脚本已处理**：自动根据 `marketing_target_type` 判断分类（ONEID / 商品库 / 行业产品库），路由到正确的 API，返回统一格式的资产列表。

**返回示例**：
```json
{
  "asset_type": "ONEID",
  "assets": [
    {
      "marketing_asset_outer_id": "wx1234567890",
      "marketing_carrier_id": "wx1234567890",
      "name": "以闪亮之名",
      "type": "WECHAT_MINI_GAME",
      "flat_params": {
        "asset_id": "wx1234567890",
        "carrier_id": "wx1234567890",
        "asset_name": "以闪亮之名",
        "carrier_name": "以闪亮之名"
      }
    }
  ]
}
```

> **重要**：如果步骤 2 中已通过 `get-assets-by-rules.mjs` 获取了 `asset_map`，且当前 `marketing_target_type` 在 map 中已有结果，**可复用该结果，无需再调 `get-assets.mjs`**。

**Agent 需要做的决策**：从返回的资产列表中确定用户要使用的资产。

**资产选择规则（按优先级）**：

1. **用户给了资产 ID**（`marketing_asset_id`、`product_id`、`marketing_asset_outer_id` 等）：
   - **在资产列表中找到** → 直接使用
   - **在资产列表中找不到** → **不判定为错误**，保留用户给的 ID 继续流程，交给后台接口校验
2. **用户给了资产名称但没给 ID** → 按名称模糊匹配资产列表，匹配到 1 条直接使用，匹配到多条列出让用户选
3. **用户未提及任何资产信息** → 若只有 1 条资产直接使用；若有多条，展示列表让用户确认选择

### 3A. 字段组装规则（flat_params 直接透传）

选定资产后，**直接使用该 asset 的 `flat_params` 对象**，在调用 `create-adgroup.mjs` 时将 `flat_params` 里的 key-value 展开到请求体顶层即可。`create-adgroup.mjs` 会根据 `marketing_target_type` 自动组装 API 所需的嵌套结构（`marketing_asset_outer_spec` / `marketing_asset_id` / `marketing_carrier_detail`）。

**flat_params 各字段含义**（与 `create-adgroup.mjs` 方式一入参完全对齐，共 7 个）：

| flat_params key | 含义 | 来源 |
|----------------|------|------|
| `asset_id` | 推广产品 ID | ONEID→outer_id / 行业→asset_id / 商品库→catalog_id |
| `carrier_id` | 载体 ID | ONEID 类和视频号直播类→自动填入（= outer_id，和 asset_id 同值）；⚠️ **行业/商品库类不含此字段**，若 `carrier_type` 需要载体则需从用户处获取后补入 |
| `catalog_id` | 商品目录 ID | 仅商品库类 |
| `asset_sub_id` | 子标识 | 商品库→product_outer_id；直播预约→notice_id（需 Agent 从 live_notices 中选择后补入） |
| `asset_name` | 资产名称 | ONEID 类自动填入 asset 的 name；create-adgroup.mjs 写入 `marketing_asset_outer_name`（仅 APP_QUICK_APP / PC_GAME 生效） |
| `carrier_name` | 载体名称 | ONEID 类自动填入 asset 的 name；create-adgroup.mjs 写入 `marketing_carrier_name`（仅 QUICK_APP / PC_GAME 载体类型生效，其他类型自动忽略） |
| `sub_carrier_id` | 载体子标识 | 直播预约→notice_id（需 Agent 从 live_notices 中选择后补入）；create-adgroup.mjs 写入 `marketing_sub_carrier_id` |

> **多传无害**：`asset_name`、`carrier_name` 在非 QUICK_APP / PC_GAME 类型时，`create-adgroup.mjs` 内部会自动过滤掉，不会传给 API。

**示例——Agent 选定 asset 后传给 create-adgroup.mjs 的参数**：
```json
{
  "account_id": "123456789",
  "adgroup_name": "...",
  "marketing_target_type": "MARKETING_TARGET_TYPE_WECHAT_MINI_GAME",
  "asset_id": "wx1234567890",
  "carrier_id": "wx1234567890",
  "asset_name": "以闪亮之名",
  "carrier_name": "以闪亮之名",
  "...其他字段..."
}
```
> 上面的 `asset_id`、`carrier_id`、`asset_name`、`carrier_name` 都是从 `assets[n].flat_params` 里展开的。

**不再需要手动组装以下嵌套结构**（`create-adgroup.mjs` 自动处理）：
- ❌ 不需要手动构造 `marketing_asset_outer_spec`
- ❌ 不需要手动构造 `marketing_carrier_detail`
- ❌ 不需要手动设置 `marketing_asset_id`（行业类）
- ✅ 只需把 `flat_params` 展开透传

### 3B. 强约束

- **白名单例外**：用户在原始需求里已明确给出完整 ID（如 `product_id`、`marketing_asset_outer_id`、`catalog_id`、`product_outer_id`、`marketing_asset_id`、`marketing_carrier_id`），则可直接使用并跳过查询。
- **空字符串不是合法结果**：不要把空字符串当作"已完成步骤 3"。查不到且用户也未提供时，保留缺失状态。
- **字段名强约束**：`marketing_asset_outer_spec` 里使用 `marketing_asset_outer_id` / `marketing_asset_outer_sub_id`，**不要写** `outer_id` / `outer_sub_id`。

**步骤 3 完成后你应该有**：选定 asset 的 `flat_params`（包含 `asset_id`、`carrier_id` 等，将在步骤 7 展开透传给 `create-adgroup.mjs`）。

---

## 步骤 4（⛔ 默认必须执行）：获取版位列表

> **前置**：步骤 1 的 `smart_delivery_platform` + 步骤 2 的四元组
> **输出**：`site_set`（数组），仅供后续 `get-conversions.mjs` 使用

智投场景下版位固定为**智能版位**（系统将智能进行版位择优投放），用户不可选择或修改。如果用户提到了版位相关需求，应告知用户：「智投场景下版位为系统智能择优投放，无需手动选择」。

本步骤的唯一目的是获取当前场景的 `site_set` 列表，**供步骤 5 查询转化目标时使用**。

```bash
node scripts/get-site-set.mjs '{"account_id":"<ACCOUNT_ID>","marketing_goal":"<MARKETING_GOAL_枚举key>","marketing_sub_goal":"<MARKETING_SUB_GOAL_枚举key>","marketing_target_type":"<MARKETING_TARGET_TYPE_枚举key>","marketing_carrier_type":"<MARKETING_CARRIER_TYPE_枚举key>"}'
```

**返回**：
```json
{
  "auto_site_set": ["SITE_SET_WECHAT", "SITE_SET_MOBILE_UNION"]
}
```

- `site_set` 列表是动态的，**不要手写示例数组**
- 后续 `get-conversions.mjs` 必须使用此处返回的真实 `site_set`

**步骤 4 完成后你应该有**：`site_set` 数组（来自脚本返回）。

---

## 步骤 5：获取转化目标 + 确定出价

> **前置**：步骤 1 的 `delivery_scene`（数值）+ 步骤 2 的四元组 + 步骤 4 的 `site_set`
> **输出**：`conversion_id`、`bid_amount`、出价相关字段

### 5A. 获取转化目标

```bash
node scripts/get-conversions.mjs '{"account_id":"<ACCOUNT_ID>","delivery_scene":<数值>,"site_set":["..."],"marketing_goal":"<MARKETING_GOAL_枚举key>","marketing_sub_goal":"<MARKETING_SUB_GOAL_枚举key>","marketing_carrier_type":"<MARKETING_CARRIER_TYPE_枚举key>","marketing_target_type":"<MARKETING_TARGET_TYPE_枚举key>","create_source_type":"<CreateSourceType的枚举值，用户未提及来源时不传此参数>"}'
```

> **注意**：`get-conversions.mjs` 的入参中，四元组字段统一传**字符串枚举 key**（如 `"MARKETING_GOAL_USER_GROWTH"`），脚本内部自动转为数值。**不需要传 `product_type`、`live_video_mode`、`live_video_sub_mode`**，脚本会根据 `marketing_carrier_type` + `delivery_scene` 自动推导。`delivery_scene` 传步骤 1 的数值。
>
> **特别注意 `marketing_sub_goal`**：这里传的必须是**步骤 2 选中的原始 key**，不能因为用户说了"注册"、"下载"、"安装"，或转化名称里带这些词，就改写成 `MARKETING_SUB_GOAL_USER_REGISTER`、`MARKETING_SUB_GOAL_MINI_GAME_APP_INSTALL` 之类的自造枚举。
>
> **`create_source_type`**：如果用户指定了转化来源，则根据用户意图传入——`PLATFORM`平台转化或`SELF_CREATED`自建转化等。用户未提及来源时不传此参数。

**脚本已处理**：通过 `access_status` 过滤仅返回已完成接入的转化目标，标注深度转化类型，裁剪无关字段。

**返回示例**：
```json
{
  "goals": [
    {
      "conversion_id": 12345,
      "name": "小游戏注册",
      "optimization_goal": "OPTIMIZATIONGOAL_APP_REGISTER",
      "bid_mode": "BID_MODE_OCPM",
      "has_deep_conversion": false,
      "create_source_type": "PLATFORM"
    },
    {
      "conversion_id": 12346,
      "name": "注册-七日变现ROI",
      "optimization_goal": "OPTIMIZATIONGOAL_APP_REGISTER",
      "bid_mode": "BID_MODE_OCPM",
      "has_deep_conversion": true,
      "deep_conversion_type": "DEEP_CONVERSION_WORTH",
      "deep_conversion_worth_goal": "OPTIMIZATIONGOAL_MONETIZATION_ROAS_7DAY",
      "create_source_type": "SELF_CREATED"
    }
  ]
}
```

**Agent 需要做的决策——conversion_id 选择规则**：

1. **用户提供了 ROI 系数** → **必须**选 `has_deep_conversion=true` 的转化ID
2. **用户未提供 ROI 系数** → 选与用户指定优化目标匹配的项
3. **用户未指定** → 取 goals 数组第一个项
4. **用户指定了转化创建来源**（如"自建转化"/"自建归因"/"自建"/"自定义转化"→ `SELF_CREATED`，"平台预置"/"平台转化"/"平台上报"/"系统预置"/"预置转化"→ `PLATFORM`）→ 在调用 `get-conversions.mjs` 时传入 `create_source_type` 过滤；**用户未提及来源时不传此参数**

**强约束**：
- `conversion_id` 只能来自：用户明确给出的 ID，或 `get-conversions.mjs` 返回
- **白名单例外**：用户在原始需求中已明确给出 `conversion_id` 数值 ID，则直接使用
- **`conversion_id: 0` 视为错误占位，不可提交**
- 若用户未明确给出且也没有成功查询到，不要编造 `0`、空字符串或占位值

### 5B. 出价字段

| 字段 | 类型 | 必填 | 说明 | 如何获取 |
|------|------|------|------|----------|
| `conversion_id` | integer | **是** | 转化ID（**放在请求体顶层**） | 5A 获取 |
| `bid_amount` | integer | **是** | 出价（单位：**分**，顶层） | 用户提供，"出价42元" → `4200` |
| `bid_mode` | enum | 否 | 出价方式 | 智投默认 `BID_MODE_OCPM` |
| `smart_bid_type` | enum | 否 | 出价类型 | `SMART_BID_TYPE_CUSTOM`（手动）或 `SMART_BID_TYPE_SYSTEMATIC`（自动） |
| `smart_cost_cap` | integer | 否 | 自动出价成本上限（分） | 用户提供 |
| `daily_budget` | integer | 否 | 日预算（分，5000~400000000） | 用户提供，"日预算1000元" → `100000` |
| `deep_conversion_worth_rate` | float | 否 | 深度ROI（对应 `DEEP_CONVERSION_WORTH`） | 用户说"深度ROI 1.5" → `1.5` |
| `deep_conversion_worth_advanced_rate` | float | 否 | 深度辅助ROI（对应 `DEEP_CONVERSION_WORTH_ADVANCED`） | 用户说"深度辅助ROI 1.812" → `1.812` |
| `deep_conversion_behavior_bid` | integer | 否 | 深度优化行为出价（分） | 用户提供 |
| `bid_scene` | enum | 场景依赖 | 出价场景 | 小游戏跑量传 `BID_SCENE_NORMAL_AVERAGE`；其他不传 |

**智投出价核心规则**：
1. **`conversion_id` 和 `bid_amount` 放在请求体顶层**
2. **不需要传 `optimization_goal`** — 智投的优化目标隐含在 `conversion_id` 中
3. 金额单位是**分**（10000分 = 100元）
4. `deep_conversion_worth_rate` 和 `deep_conversion_worth_advanced_rate` 是**两个不同字段**，支持3位小数

**步骤 5 完成后你应该有**：`conversion_id`（顶层，非 0，非空）、`bid_amount`、出价相关可选字段。

---

## 步骤 6：配置定向 + 投放时间

> **前置**：用户意图中的定向需求
> **输出**：`targeting`、`begin_date`、`end_date`、`delivery_time_ranges`

### 6A. 定向配置

- **用户未提及任何定向时**（通投）→ `targeting` 传空对象 `{}`，**跳过以下所有定向步骤**，直接进入 6B
- **用户有定向需求时** → 按下方规则构造 `targeting`

#### 智能定向模式（smart_targeting_mode）

> ⚠️ `smart_targeting_mode` 是**请求体顶层字段**（不在 `targeting` 对象内），控制定向方式——AI 自动探索还是人工圈选。与 `targeting` 内的定向内容字段（地域/年龄/性别等）是不同层级的概念。

- **用户说"不使用智能定向"/"关闭智能定向"/"手动定向"** → 传 `"smart_targeting_mode": "SMART_TARGETING_MANUAL"`
- **用户说"使用智能定向"/"开启智能定向"** → 传 `"smart_targeting_mode": "SMART_TARGETING_AUTO"`
- **用户未提及** → 不传此字段

> 不同智投场景支持的定向维度不同。如果传入了当前场景不支持的定向字段，创建时会报错并列出不支持的字段。收到此报错后，告知用户输入合适的定向。


智投广告支持**完整定向能力**，包括地域、年龄、性别、操作系统、学历、设备价格、微信广告行为等多维度定向。

**定向查询触发规则（命中任一项就必须先调用 `get-targeting-lookup.mjs`）**：
- 用户给了地域、省市区、常驻地 → `type: "geo"`
- 用户给了设备品牌 / 型号 → `type: "device"`

**不需要调用 `get-targeting-lookup.mjs` 的定向维度（脚本自动匹配枚举）**：
- **性别**：直接用 `["MALE"]` / `["FEMALE"]` / 不传
- **年龄**：直接用 `[{"min":25,"max":29}, {"min":30,"max":39}]` 格式的数组。**`min` 和 `max` 均为闭区间（包含边界值）**，即用户说"25~29岁"→ `{"min":25,"max":29}`，不是 `{"min":25,"max":30}`。每个区间对应用户给出的一段年龄范围，如果用户说了多个不同年龄段区间，就按照多个区间构造，**不要合并连续段**
- **排除已转化**：通过 `get-enum-options.mjs '{"fields":["excluded_dimension","excluded_day"]}'` 查询枚举后构造
- **操作系统**（`user_os`）：通过 `get-enum-options.mjs '{"fields":["user_os"]}'` 查询枚举值后构造（支持系统+版本号, 传 `["IOS"]` / `["ANDROID"]`（全版本），或用简化格式如 `["ANDROID_10+"]` 表示 Android 10 及以上
- **排除操作系统**（`excluded_os`）：通过 `get-enum-options.mjs '{"fields":["excluded_os"]}'` 查询枚举后构造，同 `user_os` 的简化格式，也支持 `WINDOWS`、`HARMONY` 等直接枚举
- **联网方式**（`network_type`）：通过 `get-enum-options.mjs '{"fields":["network_type"]}'` 查询枚举后构造，传用户提到的联网方式即可，如 `["WIFI"]`、`["4G"]`、`["5G"]`，脚本自动匹配为 API 枚举（如 `4G` → `NET_4G`）
- **学历**（`education`）：通过 `get-enum-options.mjs '{"fields":["education"]}'` 查询枚举后构造，传中文即可，如 `["本科", "硕士"]`，脚本自动匹配为 API 枚举（如 `本科` → `BACHELOR`）
- **设备价格**（`device_price`）：通过 `get-enum-options.mjs '{"fields":["device_price"]}'` 查询枚举后构造，传简化描述即可，如 `["2500以上"]`、`["1500-3500"]`，脚本自动展开为对应的价格区间枚举
- **微信广告行为**（`wechat_ad_behavior`）：通过 `get-enum-options.mjs '{"fields":["wechat_ad_behavior_actions"]}'` 查询枚举后构造，传中文即可，如 `{"actions": ["注册过小游戏"], "mini_game_wechat_registered_activity": "30天未活跃"}`，脚本自动匹配为 API 枚举
- **微信广告行为排除**：通过 `get-enum-options.mjs '{"fields":["wechat_ad_behavior_excluded_actions"]}'` 查询枚举后构造
- **其他枚举定向**（婚恋状态/游戏消费能力/应用安装状态等）：均通过 `get-enum-options.mjs` 查询

> ⚠️ `get-targeting-lookup.mjs` **只支持 `type: "geo"` 和 `type: "device"` 两种查询**，不支持 age、gender 等。年龄和性别不需要编码查询，直接用结构化值。

**只有在以下情况才可跳过定向查询**：用户完全没有给任何地域或设备定向约束。

**地域编码查询**：
```bash
node scripts/get-targeting-lookup.mjs '{"type":"geo","keyword":"广东"}'
# 支持批量：keyword 用空格分隔
node scripts/get-targeting-lookup.mjs '{"type":"geo","keyword":"北京 上海 广东"}'
```

> **⚠️ 地域查询效率规则（P0 级，违反会导致轮次耗尽被终止）**：
> 1. **一次查完所有地域**：脚本是本地文件查询，**无数量限制**。把用户给的所有城市名用空格拼接到一个 keyword 里一次调用即可，**不要分批，不要逐个查询**。即使 100+ 个城市也只需 1 次调用。
> 2. **省级优先原则**：如果用户说"北京"、"广东"等省级地域，直接用省名查询，会返回省级编码（如 110000）。**不要拆解为区级编码**，除非用户明确列举了具体的区/市。
> 3. **不加行政区前缀**：直接用城市名（如 `"南宁 成都 杭州"`），不要加"广西南宁"、"四川成都"等前缀。
> 4. **重名消歧**：如果查询结果中有重名地域（如"朝阳区"同时返回北京和长春的），根据用户上下文和 `parent` 字段筛选正确的。

**地域排除**（用户表达"排除某省/不投某省/除 X 外全国投放"）：
调 `get-geo-exclude.mjs`，直接返回排除后剩余省份的编码，取 `id` 组成 `regions` 数组：
```bash
node scripts/get-geo-exclude.mjs '{"exclude":"河北"}'
# → {"results":[{"id":110000,"name":"北京市","level":"province"},{"id":120000,"name":"天津市","level":"province"},...]}
```

**设备品牌型号 ID 查询**：
```bash
node scripts/get-targeting-lookup.mjs '{"type":"device","keyword":"华为"}'
```

**地域输出示例**：
```json
{
  "results": [
    {"id": 440000, "name": "广东省", "level": "province", "city_level": 4}
  ]
}
```

**设备输出示例**：
```json
{
  "results": [
    {"id": 10001, "name": "华为 Mate 60"},
    {"id": 10002, "name": "华为 P60"}
  ]
}
```

**智投支持的完整定向维度**（以下字段均放在 `targeting: { ... }` 对象内，不要放到请求体顶层）：

| 定向维度 | `targeting` 内的字段 | 说明 | 获取方式 |
|----------|-----------------|------|----------|
| 地域 | `geo_location.regions` + `geo_location.location_types` | `regions` 是**纯整数数组**（如 `[440000]`），取地域查询返回的 `id` 值；`location_types` 常用 `LIVE_IN`。**`geo_location` 只传本表列出的子字段，不要自行推测添加字段** | ✅ `get-targeting-lookup.mjs type:geo` + 枚举查询 `location_types` |
| 商圈 | `geo_location.business_districts` | 商圈 ID 数组（integer[]） | 用户提供商圈 ID |
| 自定义位置 | `geo_location.custom_locations` | 经纬度+半径定向，格式: `[{"longitude":113.26,"latitude":23.13,"radius":3000}]`，radius 单位米 | 用户提供 |
| 性别 | `gender` | 枚举查询 | ❌ 查枚举后直接构造 |
| 年龄 | `age` | 数组格式: `[{"min":25,"max":29}, {"min":30,"max":39}]`（**`min`/`max` 均为闭区间**，按用户原始区间构造，**不要合并连续段**） | ❌ 直接构造（无枚举） |
| 操作系统 | `user_os` | 支持系统+版本号（如 `IOS_VERSION_18`），枚举查询 | ❌ 查枚举后直接构造 |
| 排除操作系统 | `excluded_os` | 枚举查询 | ❌ 查枚举后直接构造 |
| 学历 | `education` | 枚举查询，传中文（如 `["本科", "硕士"]`）或枚举 key 均可，脚本自动匹配 | ❌ 查枚举后直接构造 |
| 婚恋状态 | `marital_status` | 枚举查询 | ❌ 查枚举后直接构造 |
| 联网方式 | `network_type` | 枚举查询 | ❌ 查枚举后直接构造 |
| 设备价格 | `device_price` | 枚举查询，传简化描述（如 `["2500以上"]`、`["1500-3500"]`）或枚举 key 均可，脚本自动展开 | ❌ 查枚举后直接构造 |
| 设备品牌型号 | `device_brand_model` | 嵌套结构：`{"included_list":[5,9]}` 定向 / `{"excluded_list":[1]}` 排除，**数字 ID** | ✅ `get-targeting-lookup.mjs type:device` |
| 应用安装状态 | `app_install_status` | 枚举查询（仅推广 APP 时可用） | ❌ 查枚举后直接构造 |
| 自定义人群 | `custom_audience` | 人群包 ID 列表 | 用户提供 |
| 排除人群 | `excluded_custom_audience` | 排除的人群包 ID | 用户提供 |
| 排除已转化 | `excluded_converted_audience` | 见下方格式说明 | ❌ 查枚举后直接构造 |
| 微信广告行为 | `wechat_ad_behavior` | 见下方格式说明 | ❌ 查枚举后直接构造 |

**⛔ 所有枚举值禁止凭记忆猜测，必须通过 `get-enum-options.mjs` 查询确认**：

```bash
# 查询单个/多个字段的枚举
node scripts/get-enum-options.mjs '{"fields":["education","device_price","excluded_dimension"]}'

# 查询定向相关的所有枚举
node scripts/get-enum-options.mjs '{"category":"targeting"}'
```

可查询的定向枚举字段包括：`gender`、`education`、`user_os`、`excluded_os`、`network_type`、`device_price`、`marital_status`、`app_install_status`、`location_types`、`excluded_dimension`、`excluded_day`、`wechat_ad_behavior_actions`、`wechat_ad_behavior_excluded_actions`、`smart_targeting_mode`。

> ⚠️ 智投场景下，出价方式（`bid_mode`）固定为 `BID_MODE_OCPM`，转化目标从 `get-conversions.mjs` 返回获取，版位策略固定为自动版位 —— 这些字段**不需要**通过 `get-enum-options.mjs` 查询。`get-enum-options.mjs` 在智投中**仅用于定向枚举查询**。

**`excluded_converted_audience` 格式**（仅在用户明确提到"排除已转化"时才添加，禁止自行添加）：
```json
{
  "excluded_dimension": "<通过 get-enum-options.mjs 查 excluded_dimension>",
  "excluded_day": "<通过 get-enum-options.mjs 查 excluded_day>"
}
```

**`wechat_ad_behavior` 格式**（仅在用户明确提到微信广告行为排除时才添加，禁止自行添加）：

用户说"排除已关注公众号的用户"、"排除已注册小游戏的用户"等时，构造此字段。`excluded_actions` 的枚举通过 `get-enum-options.mjs '{"fields":["wechat_ad_behavior_excluded_actions"]}'` 查询。

```json
"wechat_ad_behavior": {
  "excluded_actions": ["GDT_WECHAT_OFFICIAL_ACCOUNT_FOLLOWED"],
  "wechat_official_account_id": ["wx18c408376c727a19"]
}
```
- 涉及公众号行为时，需同时传 `wechat_official_account_id`（用户给的公众号 ID）
- 涉及企业微信行为时，需同时传 `corp_id`

**强约束**：
- 命中触发规则后，必须先调用 `get-targeting-lookup.mjs` 获取编码，再构造 `targeting`
- 不要把自然语言直接翻成粗粒度占位值
- **`targeting` 及其子结构只传上方表格中列出的字段和子字段**，不要自行推测或类推添加文档中未出现的字段
- **⛔ 所有枚举值禁止凭记忆猜测，必须通过 `get-enum-options.mjs` 查询确认**

**targeting 构造示例**：

```json
{
  "bid_amount": 5000,
  "targeting": {
    "age": [{"min": 25, "max": 29}, {"min": 30, "max": 39}],
    "gender": ["MALE"],
    "geo_location": {
      "regions": [440000, 310000],
      "location_types": ["LIVE_IN"]
    }
  }
}
```

### 6B. 投放时间与状态

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `begin_date` | string | **是** | 开始日期，格式 `YYYY-MM-DD` |
| `end_date` | string | **是** | 结束日期，格式 `YYYY-MM-DD`；未指定传 `""`（长期投放） |
| `first_day_begin_time` | string | 否 | 首日开始时间，格式 `HH:ii:ss` |
| `delivery_time_ranges` | string[] | **是** | 投放时段数组，半小时精度。|
| `configured_status` | enum | 否 | 广告状态，默认暂停(`AD_STATUS_SUSPEND`)；用户明确要求上线时传 `AD_STATUS_NORMAL` |

**`delivery_time_ranges` 格式说明**：

数组中每条格式为:全时段/全天投放/未设置：`"all"`；指定时段： `"<Weekday> <HH:MM>~<HH:MM>"`，时间精度为半小时（只支持 `:00` 或 `:30`）；
**示例**：`["all"]`=全时段；`["Monday 09:00~18:00",...,"Sunday 09:00~18:00"]`=每天9点到18点（支持 Monday-Sunday ）

```json
// 全时段（用户未指定投放时段）
"delivery_time_ranges": ["all"]
// 周二全天
"delivery_time_ranges": ["Tuesday 00:00~24:00"]
// 周一上午9点到12点，周二下午14点到18点
"delivery_time_ranges": ["Monday 09:00~12:00","Tuesday 14:00~18:00"]
// 周二全天
"delivery_time_ranges": ["Tuesday 00:00~24:00"]
```

**时间精度规则**：
- 时间只能是整点 `:00` 或半点 `:30`
- ⚠️ **如果用户说的时间不是整半小时**（如 "10:00~10:15"），需要向用户确认：精度只支持半小时，可以选择 "10:00~10:30"（多了 15 分钟），请用户确认或调整
- ⚠️ **end 边界规则**：当用户说 "23:59"、"24:00"、"午夜" 或"投到当天结束"时，一律用 `24:00` 作为结束时间
- 星期名支持全称（Monday-Sunday）

**Agent 需要做的**：从用户自然语言中理解投放时段意图，转为 `delivery_time_ranges` 数组。常见自然语言映射：
- "全天投放" / 未指定 → `["all"]`
- "工作日" → Monday 到 Friday
- "周末" → Saturday + Sunday
- "每天 X 到 Y" → 7 天都写上相同时段
- "某天"  → 如果用户没有表达时间段默认 00:00~24:00，例如某天是星期二：Tuesday 00:00~24:00
- "排除周三下午" → 列出除周三下午外的所有时段

**步骤 6 完成后你应该有**：`targeting`（如需）、`begin_date`、`end_date`、`delivery_time_ranges`。

---

## 步骤 7：组装请求体 → 创建广告组

> **前置**：步骤 1-6 的所有输出
> **动作**：按检查清单组装完整请求体，调用 `create-adgroup.mjs`

### 7A. 版位与探索策略（智投固定值，脚本自动处理）

| 字段 | 值 | 说明 |
|------|-----|------|
| `automatic_site_enabled` | `true` | 脚本自动设置，无需传入 |
| `site_set` | 不传 | 智能版位，系统自动择优 |
| `exploration_strategy` | 推荐 `AUTOMATIC_EXPLORATION` | |

### 7B. 智投专有字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `smart_delivery_platform` | enum | **是** | 步骤 1 确定的智投场景标识 |
| `smart_delivery_aigc_creative` | struct | **推荐必传** | AIGC自动创意，用户未提及默认关闭 |
| `smart_delivery_history_comp_reused_creative` | struct | **推荐必传** | 组件全库智选，用户未提及默认关闭 |
| `auto_derived_creative_enabled` | boolean | 推荐传 | 自动衍生视频创意，推荐 `true` |
| `smart_delivery_period_switch` | enum | 否 | 周期达成开关，`PERIOD_SWITCH_ON` / `PERIOD_SWITCH_OFF`。仅用户明确要求"周期达成"/"周期稳投"时传入 |
| `smart_delivery_period_days` | enum | 周期达成时**必填** | 周期天数，支持 `PERIOD_DAYS_THREE`(3天) / `PERIOD_DAYS_SEVEN`(7天) |
| `smart_delivery_period_budget` | integer | 周期达成时**必填** | 周期总预算（单位：**分**），约束：≥ 3 × 出价 × 周期天数 |
| `smart_delivery_period_continue` | enum | 周期达成时**必填** | 续投开关，`PERIOD_CONTINUE_SWITCH_ON`（长期自动续投）/ `PERIOD_CONTINUE_SWITCH_OFF`（单周期结束即停） |
| `short_play_pay_type` | enum | 爆剧跑量场景可选 | 短剧售卖方式类型，详见 [references/short-play-pay-type.md](references/short-play-pay-type.md) |
| `sell_strategy_id` | integer | 条件必填 | 售卖策略 ID，`short_play_pay_type` 为收费剧时**必填** |

**smart_delivery_aigc_creative（AIGC自动创意）**：
```json
// 关闭
{"is_open": false, "supply_strategy_type": ["SUPPLY_STRATEGY_TYPE_AIGC"]}
// 开启
{"is_open": true, "supply_strategy_type": ["SUPPLY_STRATEGY_TYPE_AIGC"]}
```

**smart_delivery_history_comp_reused_creative（全库智选）**：
```json
// 关闭
{"is_open": false, "supply_strategy_type": ["SUPPLY_STRATEGY_TYPE_HISTORY_COMP_REUSE"]}
// 开启
{"is_open": true, "supply_strategy_type": ["SUPPLY_STRATEGY_TYPE_HISTORY_COMP_REUSE"]}
```

> ⚠️ **废弃字段**：不要使用 `smart_delivery_scene_spec`、`smart_delivery_auto_creative`、`aigc_creative_switch`。

#### 爆剧跑量场景专有字段

当 `smart_delivery_platform` = `SMART_DELIVERY_PLATFORM_EDITION_ECOLOGY_PLAYLET`（爆剧跑量）时，支持设置短剧售卖方式和场景规格。**脚本自动校验：收费剧必须提供售卖策略 ID。**

- `short_play_pay_type`：`SHORT_PLAY_PAY_TYPE_FREE_PLAY`（免费剧）/ `SHORT_PLAY_PAY_TYPE_CHARGE_PLAY`（收费剧）
- `sell_strategy_id`：收费剧时**必填**，免费剧不需要

> 枚举值、校验规则、请求体示例详见 [references/short-play-pay-type.md](references/short-play-pay-type.md)

**周期达成（Period Completion）**：

完整字段定义、约束规则和 JSON 示例见 [references/smart-delivery-period.md](references/smart-delivery-period.md)（可通过 `load_skill_reference` 加载）。以下是关键要点：

- **触发条件**：仅在用户明确提出"周期达成"/"周期稳投"需求时才开启，不要自行添加
- **必填字段**：`smart_delivery_period_switch`=`PERIOD_SWITCH_ON` + `smart_delivery_period_days` + `smart_delivery_period_budget` + `smart_delivery_period_continue`
- **预算约束**：`smart_delivery_period_budget` ≥ 3 × `bid_amount` × 周期天数
- **禁止字段**：开启时不允许传 `daily_budget`、`total_budget`；`end_date` 由脚本统一设为 `""`，后端根据 `begin_date` + 周期天数自动计算实际结束日期
- **出价限制**：不允许使用自动出价（`smart_bid_type` 不能为 `SMART_BID_TYPE_SYSTEMATIC`）
- **支持场景**：线索智投（`SMART_DELIVERY_PLATFORM_EDITION_ECOLOGY_LEADS`）

#### ⛔ 创意字段场景化必填规则（P0 级，脚本会校验拦截）

以下两条规则由 `create-adgroup.mjs` 自动校验，不满足时会报错拦截。**Agent 必须在组装请求体时主动满足这些规则，避免被脚本拦截。**

**规则 A：视频号直播场景必填 `sku_id` + `catalog_id`**

| 触发条件 | 说明 |
|----------|------|
| `smart_delivery_platform` = 3002（小店单链路）或 3004（推直播间） | 投放场景 |
| `marketing_target_type` = `MARKETING_TARGET_TYPE_WECHAT_CHANNELS_LIVE` | 推广产品类型为视频号直播 |
| `marketing_carrier_type` = `MARKETING_CARRIER_TYPE_WECHAT_CHANNELS_LIVE` | 载体为视频号直播 |

**三个条件同时满足时**，`smart_delivery_aigc_creative`为开启状态时，必须额外包含：
- `sku_id`（string）— 商品 SKU ID
- `catalog_id`（integer）— 商品目录 ID

这两个值需要从用户处获取。如果用户未提供，**必须向用户询问**，不可省略。

```json
// 视频号直播场景 AIGC 创意（开启 + sku_id + catalog_id）
{
  "smart_delivery_aigc_creative": {
    "is_open": true,
    "supply_strategy_type": ["SUPPLY_STRATEGY_TYPE_AIGC"],
    "sku_id": "10000299440478",
    "catalog_id": 1023958
  }
}
```

**规则 B：非视频号直播场景必填品牌形象**

| 触发条件 | 说明 |
|----------|------|
| `smart_delivery_platform` = 3002（小店单链路）或 3003（全店托管）或 3005（推商品） | 投放场景 |
| `marketing_target_type` ≠ `MARKETING_TARGET_TYPE_WECHAT_CHANNELS_LIVE` | 推广产品类型**不是**视频号直播 |
| `marketing_carrier_type` ≠ `MARKETING_CARRIER_TYPE_WECHAT_CHANNELS_LIVE` | 载体**不是**视频号直播 |

**三个条件同时满足时**，`smart_delivery_aigc_creative` 或 `smart_delivery_history_comp_reused_creative`处于开启状态时，必须满足：
1. 在 `creative_components.brand` 数组中填写至少一个 `component_id`（品牌形象组件 ID）
2. 在 `supply_strategy_type` 数组中包含 `SUPPLY_STRATEGY_TYPE_CUSTOMER_MANUAL_CREATION`（与原有策略类型并存）
3. 注意：`SUPPLY_STRATEGY_TYPE_CUSTOMER_MANUAL_CREATION` 必须和原有的策略类型并存，不能单独使用。
结构示例：
```json
// 非视频号直播场景 AIGC 创意（开启 + 品牌形象）
{
  "smart_delivery_aigc_creative": {
    "is_open": true,
    "supply_strategy_type": [
      "SUPPLY_STRATEGY_TYPE_AIGC",
      "SUPPLY_STRATEGY_TYPE_CUSTOMER_MANUAL_CREATION"
    ],
    "creative_components": {
      "brand": [{"component_id": 1917953657934}]
    }
  }
}
// 非视频号直播场景 组件全库智选（开启 + 品牌形象）
{
  "smart_delivery_history_comp_reused_creative": {
    "is_open": true,
    "supply_strategy_type": [
      "SUPPLY_STRATEGY_TYPE_HISTORY_COMP_REUSE",
      "SUPPLY_STRATEGY_TYPE_CUSTOMER_MANUAL_CREATION"
    ],
    "creative_components": {
      "brand": [{"component_id": 1917953657934}]
    }
  }
}
```

> **⚠️ 注意**：`SUPPLY_STRATEGY_TYPE_CUSTOMER_MANUAL_CREATION` 和 `creative_components.brand` 必须**同时存在**，缺一不可。只传 brand 不加策略类型、或只加策略类型不传 brand，都会导致创建失败。

### 7C. project_ability_list（全店托管多商品场景）

**适用场景**：`smart_delivery_platform` = `SMART_DELIVERY_PLATFORM_EDITION_WECHAT_STORE_MANAGEMENT`（全店托管）且用户指定了多个商品时，或任何需要传入多个商品营销表达式的场景。

**规则**：
- 当用户指定多个商品（如"含2个商品"、"商品A和商品B"）时，**每个商品对应一条 `project_ability_list` 项**
- `project_ability_list` 替代顶层的 `marketing_asset_outer_spec`：各商品的 asset 信息放入每个 item 的 `marketing_expression.marketing_asset_outer_spec` 内
- 四元组（`marketing_goal`、`marketing_sub_goal`、`marketing_carrier_type`）在每个 item 内重复

**结构示例（2个微信小店商品，营销载体为跳转页面）**：
```json
{
  "project_ability_list": [
    {
      "project_ability_type": "ABILITY_TYPE_MARKETING_EXPRESSION",
      "ability_content": {
        "marketing_expression": {
          "marketing_goal": "MARKETING_GOAL_PRODUCT_SALES",
          "marketing_sub_goal": "MARKETING_SUB_GOAL_UNKNOWN",
          "marketing_carrier_type": "MARKETING_CARRIER_TYPE_JUMP_PAGE",
          "marketing_asset_outer_spec": {
            "marketing_target_type": "MARKETING_TARGET_TYPE_WECHAT_STORE_PRODUCT",
            "marketing_asset_outer_id": "<catalog_id>",
            "marketing_asset_outer_sub_id": "<product_outer_id_1>"
          }
        }
      }
    },
    {
      "project_ability_type": "ABILITY_TYPE_MARKETING_EXPRESSION",
      "ability_content": {
        "marketing_expression": {
          "marketing_goal": "MARKETING_GOAL_PRODUCT_SALES",
          "marketing_sub_goal": "MARKETING_SUB_GOAL_UNKNOWN",
          "marketing_carrier_type": "MARKETING_CARRIER_TYPE_JUMP_PAGE",
          "marketing_asset_outer_spec": {
            "marketing_target_type": "MARKETING_TARGET_TYPE_WECHAT_STORE_PRODUCT",
            "marketing_asset_outer_id": "<catalog_id>",
            "marketing_asset_outer_sub_id": "<product_outer_id_2>"
          }
        }
      }
    }
  ]
}
```

**字段来源**：
- `catalog_id`（即 `marketing_asset_outer_id`）和 `product_outer_id`（即 `marketing_asset_outer_sub_id`）来自步骤 3 `get-assets.mjs` 返回的 `assets[n].catalog_id` 和 `assets[n].product_outer_id`
- 单商品场景仍用顶层 `marketing_asset_outer_spec`，无需 `project_ability_list`

### 7D. 创建前自检（Pre-flight Check，⛔ 必须在调用 create-adgroup.mjs 前完成）

在组装完请求体后、真正调用创建接口前，逐项核对以下内容：
- **用户需求一致性**：用户明确给出的每个条件（定向、出价、预算、三元组、商品等）是否都被**原样保留**在请求体中，未被丢弃、修改或替换
- **字段来源可追溯**：四元组、转化目标、营销载体等关键字段是否来自**实际脚本查询结果**（而非猜测或编造）
- **编码已确认**：定向条件中的地域编码、设备 ID 等是否经过**查询脚本确认**
- **金额单位正确**：所有金额字段是否已转换为**分**

如有任何字段与用户原始需求不一致，必须**停止并说明差异原因**，等待用户确认后才能继续。

**字段检查清单（20项）**：

| # | 检查项 | 要点 |
|---|--------|------|
| 1 | `account_id` | 广告主账号ID |
| 2 | `adgroup_name` | 用户提供的原文名称，不要编造 |
| 3 | `smart_delivery_platform` | 步骤 1 确定，与场景匹配 |
| 4 | 四元组 | `marketing_goal`、`marketing_sub_goal`、`marketing_target_type`、`marketing_carrier_type` — **统一使用字符串枚举 key**（如 `"MARKETING_GOAL_USER_GROWTH"`），`create-adgroup.mjs` 脚本内部自动转为数值。**默认全部从步骤 2 的脚本返回中选出**；只有用户明确给出 4 个枚举值全部时才可直接使用 |
| 5 | `marketing_target_type` 位置 | 传在**请求体顶层**即可，`create-adgroup.mjs` 会自动将其移入 `marketing_asset_outer_spec` 内部（ONEID类/商品库类）或用于 `marketing_asset_id` 组装（行业产品库类）。**不需要手动放进 spec** |
| 6 | 资产/载体扁平字段 | 步骤 3 选定 asset 的 `flat_params` 各 key-value **展开到请求体顶层**（如 `asset_id`、`carrier_id`、`catalog_id` 等）；ONEID 类和视频号直播类已含 `carrier_id`；**行业/商品库类不含 `carrier_id`**，若 `carrier_type` 需要载体则需从用户处获取后补入；**不要手动构造 `marketing_carrier_detail`** |
| 7 | `marketing_asset_outer_spec` / `marketing_asset_id` | **不需要手动构造**，`create-adgroup.mjs` 根据 `asset_id` + `marketing_target_type` 自动组装 |
| 8 | `conversion_id`（顶层） | 步骤 5 获取。有 ROI 系数时选 `has_deep_conversion=true` 的；用户明确给出则直接使用；**禁止写 `0`、空字符串或漏传** |
| 9 | `bid_amount`（顶层） | 单位分 |
| 10 | `begin_date` / `end_date` | 未指定 end_date 传 `""` |
| 11 | `delivery_time_ranges` | 投放时段数组，每条格式 `"<Weekday> <HH:MM>~<HH:MM>"`，如 `["Monday 09:00~18:00", "Tuesday 09:00~18:00"]`；传 `["all"]` 表示全时段投放。支持 Monday-Sunday  |
| 12 | `bid_mode` | 默认 `BID_MODE_OCPM` |
| 13 | `automatic_site_enabled` | 智投必须 `true` |
| 14 | `smart_delivery_aigc_creative` | 必传，用户未提及时关闭。**视频号直播场景(3002/3004+视频号直播target+视频号直播carrier)开启时必须含 `sku_id` 和 `catalog_id`**；**非视频号直播场景(3002/3003/3005)开启时必须含 `creative_components.brand` 和 `SUPPLY_STRATEGY_TYPE_CUSTOMER_MANUAL_CREATION`**。用户未提供品牌形象时，脚本会自动查询品牌形象列表返回供选择 |
| 15 | `smart_delivery_history_comp_reused_creative` | 必传，用户未提及时关闭。**非视频号直播场景(3002/3003/3005)开启时必须含 `creative_components.brand` 和 `SUPPLY_STRATEGY_TYPE_CUSTOMER_MANUAL_CREATION`**。用户未提供品牌形象时，脚本会自动查询品牌形象列表返回供选择 |
| 16 | `bid_scene` | 小游戏跑量传 `BID_SCENE_NORMAL_AVERAGE`，其他不传 |
| 17 | `targeting` 来源 | 只要用户给了任何定向约束，地域/设备必须通过 `get-targeting-lookup.mjs` 查编码，枚举通过 `get-enum-options.mjs` 查询；定向白名单由 `create-adgroup.mjs` 自动校验，不支持的字段会报错返回 |
| 18 | `search_expansion_switch` | 用户要求时传 `SEARCH_EXPANSION_SWITCH_OPEN`，未提及不传 |
| 19 | `project_ability_list` | 全店托管多商品场景必须用此字段替代顶层 `marketing_asset_outer_spec`；单商品不需要 |
| 20 | `wechat_ad_behavior` | 用户提到微信广告行为排除时，通过 `get-enum-options.mjs` 查询枚举后构造；**用户未提及 → 不传** |
| 21 | 定向枚举值 | `education`、`network_type`、`device_price`、`excluded_dimension`、`excluded_day` 等定向枚举**必须通过 `get-enum-options.mjs` 查询确认，禁止凭记忆猜测** |
| 22 | `material_package_id`（素材标签） | 用户提及素材标签/素材包时按 [references/material-labels.md](references/material-labels.md) 取值；未提及 → **不传** |
| 23 | `smart_targeting_mode` | 智能定向模式。`SMART_TARGETING_MANUAL`（手动定向）=不使用/关闭智能定向，`SMART_TARGETING_AUTO`（智能定向）=开启/使用智能定向。枚举通过 `get-enum-options.mjs '{"fields":["smart_targeting_mode"]}'` 查询。用户未提及不传 |
| 24 | `short_play_pay_type` + `sell_strategy_id` | 仅爆剧跑量场景。用户提及短剧售卖方式时设置；收费剧必须提供 `sell_strategy_id`；未提及 → **不传** |
| 25 | 周期达成字段 | 用户明确要求"周期达成"/"周期稳投"时传入 `smart_delivery_period_switch`=`PERIOD_SWITCH_ON` + `smart_delivery_period_days` + `smart_delivery_period_budget` + `smart_delivery_period_continue`；预算 ≥ 3×出价×天数；禁止同时传 `daily_budget`/`total_budget`/`end_date`；用户未提及 → **不传任何周期达成字段** |

> ⚠️ **定向字段禁止自行添加**：`excluded_converted_audience`、`wechat_ad_behavior` 等定向字段，**只有用户明确要求时才加入 targeting**。用户没提到的定向维度一律不传。

### 7E. 执行创建

```bash
node scripts/create-adgroup.mjs '<完整参数JSON>'
```

**返回示例（成功）**：
```json
{
  "success": true,
  "adgroup_id": 987654321
}
```

**返回示例（失败）**：
```json
{
  "success": false,
  "error": { "code": 1000014, "message": "...", "message_cn": "..." }
}
```

---

## 用户意图提取规则

| 用户输入 | 对应字段 | 转换规则 |
|---------|----------|----------|
| 场景关键词 | `smart_delivery_platform` | 按步骤 1 场景参考表匹配 |
| 四元组相关 | `marketing_goal` 等 | **从步骤 2 脚本返回中选取**，禁止猜测。**统一使用字符串枚举 key**，脚本内部转数值 |
| "出价136.54元" | `bid_amount` | → `13654`（×100，分） |
| "日预算1000元" | `daily_budget` | → `100000`（×100，分） |
| "深度ROI 1.5" | `deep_conversion_worth_rate` | → `1.5`，需选 `has_deep_conversion=true` 的转化ID |
| "深度辅助ROI 1.812" | `deep_conversion_worth_advanced_rate` | → `1.812`，需选 ROI 类转化ID |
| "全国投放"/"不限地域" | `targeting.geo_location` | 不传 `geo_location` |
| "排除X省"/"不投X省"/"除X外全国" | `targeting.geo_location` | → 调 `get-geo-exclude.mjs`，取返回 `results` 中的 `id` 组成 `regions` 数组，加 `location_types: ["LIVE_IN"]` |
| 指定省市 | `targeting.geo_location` | → `get-targeting-lookup.mjs` 查编码，取返回的 `id` 组成纯整数数组放入 `regions`（如 `[440000]`），`location_types: ["LIVE_IN"]` |
| 指定性别 | `targeting.gender` | → 通过 `get-enum-options.mjs` 查 `gender` 枚举后构造 |
| 指定年龄 | `targeting.age` | → `[{"min":25,"max":29}, {"min":30,"max":39}]`，**`min`/`max` 均为闭区间（包含边界值）**，即"25~29岁"→ `{"min":25,"max":29}`，不是 `{"min":25,"max":30}`。按用户给出的区间直接构造，如果用户说了多个不同年龄段，**不要合并** |
| 指定设备 | `targeting.device_brand_model` | → `get-targeting-lookup.mjs` 搜数字ID |
| 指定操作系统 | `targeting.user_os` | 全版本：`["ANDROID"]` / `["IOS"]`；指定版本范围：如"Android 10及以上"→ `["ANDROID_VERSION_10", ..., "ANDROID_VERSION_15"]`，"iOS 14及以上"→ `["IOS_VERSION_14", ..., "IOS_VERSION_18"]` |
| 排除操作系统 | `targeting.excluded_os` | 排除特定系统版本，如排除鸿蒙纯净版 → `["ANDROID_PURE_MODE"]`，排除低版本Android → `["ANDROID_VERSION_1", "ANDROID_VERSION_2", ..., "ANDROID_VERSION_4"]` |
| 指定联网方式 | `targeting.network_type` | 如"仅WiFi"→ `["WIFI"]`，"4G及以上"→ `["NET_4G", "NET_5G", "WIFI"]` |
| 排除已转化 | `targeting.excluded_converted_audience` | → 按定向规则填写 |
| 排除小游戏注册用户（N天未活跃） | `targeting.wechat_ad_behavior` | → `{"excluded_actions": ["MINI_GAME_WECHAT_REGISTERED"], "mini_game_wechat_registered_activity": "THIRTY_DAYS_NO_ACTIVE"}` |
| 定向枚举值 | `education`、`network_type`、`device_price` 等 | **必须通过 `get-enum-options.mjs` 查询确认，禁止凭记忆猜测** |
| 项目名称 | `adgroup_name` | 按用户原文 |
| "转化来源/自建转化/平台预置" | `create_source_type` | → `CreateSourceType`，枚举通过 `get-enum-options.mjs '{"fields":["create_source_type"]}'` 查询 |
| "AIGC开启"/"AIGC创意"/"AIGC" | `smart_delivery_aigc_creative` | → **struct**：`{"is_open": true, "supply_strategy_type": ["SUPPLY_STRATEGY_TYPE_AIGC"]}`。|
| "全库智选开启"/"组件全库智选"/"历史组件复用" | `smart_delivery_history_comp_reused_creative` | → **struct**：`{"is_open": true, "supply_strategy_type": ["SUPPLY_STRATEGY_TYPE_HISTORY_COMP_REUSE"]}`。|
| "素材包/素材标签 ID 1234" | `material_package_id` | 按 [references/material-labels.md](references/material-labels.md) 取值；未提及不传 |
| "不使用智能定向"/"关闭智能定向"/"手动定向" | `smart_targeting_mode` | → `SMART_TARGETING_MANUAL`，枚举通过 `get-enum-options.mjs '{"fields":["smart_targeting_mode"]}'` 查询 |
| "使用智能定向"/"开启智能定向" | `smart_targeting_mode` | → `SMART_TARGETING_AUTO`，枚举通过 `get-enum-options.mjs '{"fields":["smart_targeting_mode"]}'` 查询 |
| "广告上线创建"/"创建后启用"/"创建后上线" | `configured_status` | → `AD_STATUS_NORMAL`，覆盖默认暂停行为 |
| "免费剧"/"免费短剧" | `short_play_pay_type` | → `SHORT_PLAY_PAY_TYPE_FREE_PLAY`（仅爆剧跑量场景） |
| "收费剧"/"付费剧"/"付费短剧" | `short_play_pay_type` | → `SHORT_PLAY_PAY_TYPE_CHARGE_PLAY`（仅爆剧跑量场景，必须同时提供 `sell_strategy_id`） |
| "售卖策略 ID xxx"/"短剧策略 ID xxx" | `sell_strategy_id` | → 整数值，收费剧场景必填 |
| "周期达成"/"周期稳投"/"固定周期" | `smart_delivery_period_switch` | → `PERIOD_SWITCH_ON`，同时必须配合 `smart_delivery_period_days`、`smart_delivery_period_budget`、`smart_delivery_period_continue`。禁止同时传 `daily_budget`/`total_budget`/`end_date` |
| "3天周期"/"三天" | `smart_delivery_period_days` | → `PERIOD_DAYS_THREE` |
| "7天周期"/"七天"/"一周" | `smart_delivery_period_days` | → `PERIOD_DAYS_SEVEN` |
| "周期预算X元" | `smart_delivery_period_budget` | → 金额×100（分），如"2000元" → `200000` |
| "续投"/"自动续投"/"长期投放" | `smart_delivery_period_continue` | → `PERIOD_CONTINUE_SWITCH_ON` |
| "不续投"/"单周期"/"投完即停" | `smart_delivery_period_continue` | → `PERIOD_CONTINUE_SWITCH_OFF` |
---

<!-- script get-available-marketing-assets → scripts/get-available-marketing-assets.mjs (injected at build time) -->
<!-- script get-android-packages → scripts/get-android-packages.mjs (injected at build time) -->

## 执行原则

1. **⛔ 用户原始需求不可修改（最高优先级原则）**：
   用户明确给定的所有业务条件（包括但不限于：定向条件、出价、预算、三元组、优化目标、商品、推广产品、广告名称等）在整个执行流程中**绝对不可被修改、替换、省略或放宽**，无论出于任何原因——包括 API 报错、冲突检测、字段校验失败、查询结果不匹配等。
   - ❌ 禁止自动修改性别/年龄/地域/操作系统等定向来绕过错误或冲突
   - ❌ 禁止自动更换商品或推广产品来绕过错误或冲突
   - ❌ 禁止去掉定向限制（改为全量投放）来绕过错误或冲突
   - ❌ 禁止更换三元组或优化目标来绕过错误或冲突
   - ❌ 禁止用更宽泛的值替代用户给出的精确条件
   - ❌ 禁止任何形式的未经用户确认的参数变更
   - 如果因为用户给定的条件导致流程无法继续（如冲突、校验失败），必须**立即停止并向用户如实报告问题**，等待用户明确指示后才能继续。
2. **严格按步骤 1→2→3→4→5→6→7 顺序执行**；只有"显式证据白名单"允许跳过对应查询
3. **用户明确给出的结构化字段可直接复用，但只豁免该字段对应的查询，不会自动豁免其他步骤**
4. **禁止把自然语言意图当作 API 返回值使用**；中文描述只能用于筛选，不等于枚举值或 ID
5. **辅助查询失败时可以继续完成最终 API，但只能使用已确认字段**；不能为了凑齐请求体编造四元组、`conversion_id`、营销载体 ID、定向枚举
6. **空字符串和 `0` 不是默认值**：它们通常表示"你没有拿到真实结果"，不要拿来伪装步骤已完成
7. **只要用户给了定向条件，就不要省略步骤 6，也不要用更宽泛的值替代精确编码**
8. **金额单位是分**（10000分 = 100元）
9. **统一使用字符串枚举 key**：四元组等字段始终传字符串 key（如 `"MARKETING_GOAL_USER_GROWTH"`），脚本内部负责转为 API 所需数值
