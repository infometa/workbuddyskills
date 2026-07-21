---
name: tencentads-delivery-standard-create
description: "专用于创建常规(标准)展示营销单元（原广告组）的 SDK 化技能。当用户意图涉及常规投放、标准营销单元创建、CPC/CPM/oCPM/oCPC出价营销单元的**创建**场景时，使用本技能。当用户未明确提到智投关键词或者用户指定了手动版位的，应优先使用本技能。覆盖场景：电商推广、APP下载注册、品牌曝光、销售线索收集、内容变现等常规展示营销单元。本技能通过专用脚本（而非全局 CLI 工具）调用 API，脚本已处理复杂分支、字段过滤和数据转换。**注意：如果当用户明确提到智投、项目、AIM+、艾米等关键词，应使用 tencentads-delivery-smart-create 技能**"
license: MIT. See LICENSE for full terms.
compatibility: any
metadata:
  author: Tencent Ads Delivery Team
  version: "0.5.8"
  icon: megaphone
  category: tencent-ads
---

# 腾讯广告 - 常规(标准)广告组创建：按步执行

> **前置依赖**：需安装 `tencentads-cli`（Node.js ≥ 20）。执行 `npm install -g tencentads-cli@latest` 安装或升级；版本过低时 `tencentads` 会给出提示。

本技能是常规展示广告的**执行指南**——按 7 个步骤顺序完成一条常规广告组的创建。**严格按步骤顺序执行，后面的步骤依赖前面的输出，不可跳步。**

所有 API 调用均通过本技能的**专用脚本**执行，脚本负责：API 分支路由、返回数据裁剪、格式转换（rules_json 解析、geo 编码查找等）。Agent 专注于：从脚本返回结果中做出业务决策（选哪个组合、选哪个转化目标、选什么出价方式）。

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

### 常规广告与智投的关键区别（执行参考）

> 以下差异直接影响步骤 6 请求体的构建，执行时需注意。

| 维度 | 常规投放 | 智投(AIM+) |
|------|----------|------------|
| 标识 | 不传 `smart_delivery_platform` | 必传特定的 `smart_delivery_platform` |
| 出价方式 | 支持 CPC / CPM / oCPM / oCPC | 仅 oCPM |
| 转化配置 | `conversion_id` + `bid_mode` + `bid_amount` | `conversion_id`（顶层）+ `bid_amount`（顶层） |
| 版位 | 手动选择或自动版位 | 统一自动版位 |
| 定向 | **完整能力**（地域/年龄/性别/兴趣/行为/人群包等） | 受限 |

```
⛔ 执行顺序（不可跳步）：

步骤1 → 步骤1A(可选) → 步骤2 → 步骤3 → 步骤4 → 步骤5 → 步骤6
获取      资产反推       确定      确定       获取      配置       组装请求体
四元组    四元组         推广产品   版位       转化目标  定向+时间  → create-adgroup.mjs
          (有资产线索时)  +载体               +出价
```

---

## 执行协议（高优先级，覆盖后文）

> 若本节与下文"继续执行""不要重复查询"等表述冲突，以本节为准。

### ⛔ 出价方式与步骤跳过规则

> 步骤 1、2、5、6 无论什么出价方式都**必须执行**。以下规则只影响步骤 3~4：

- **CPC/CPM（轻量路径）**：
  - 步骤 3：自动版位 → 直接设 `automatic_site_enabled: true`，**跳过 `get-site-set.mjs`**；手动版位 → 仍需查询
  - 步骤 4：跳过 4B 转化查询，只需 `bid_mode` + `bid_amount`
- **oCPM/oCPC（完整路径）**：
  - 步骤 3~4 全部执行（步骤 4 的 `get-conversions.mjs` 依赖步骤 3 返回的 `site_set`）

1. **⛔ 步骤 1 → 2 是绝对必须执行的前两步，不可跳过。** 即使用户 input 中看起来已包含四元组、商品信息，仍必须调用 `get-rules.mjs` 确认四元组、调用 `get-assets.mjs` 获取推广资产 ID。原因：不同账号的可选组合不同，自然语言描述无法直接转为精确的枚举值和 ID。**例外：步骤 1A 成功确定资产后，步骤 2 可跳过 `get-assets.mjs` 调用**（但仍需从 1A 的数据构造字段）。步骤 3-5 中的查询子动作在满足"显式证据白名单"或"出价方式跳过规则"时可跳过，但步骤 1 不可。
2. **进入下一步前，必须先拿到上一步输出并确认来源。** 合法来源只有三类：用户在原始需求中明确给出、当前 session 前一步脚本返回、当前 session 前一步 API 返回。
3. **自然语言意图不能替代结构化字段。** "电商推广""品牌曝光"等描述只能用于步骤 1 筛选四元组，不能直接当作四元组、营销载体 ID、`conversion_id` 的依据。
4. **进入步骤 6 前必须能回答每个关键字段来自哪里。** 说不清来源的字段，不要猜。
5. **⚠️ 错误处理与重试限制**：每个脚本调用最多重试 **1 次**（换参数或换调用方式）。如果 2 次仍失败（如返回 "Mock not found"、空结果、报错），**立即跳过该步骤，用已有数据继续推进到下一步直至步骤 6**。严禁反复重试同一脚本、读取脚本源码、或切换到非脚本方式（如 `tencentads-cli api`）尝试绕过。宁可在最终请求中缺少某个字段，也不要耗尽所有轮次。
6. **显式证据白名单（仅适用于步骤 3-5 的查询子动作，步骤 1 不适用）**：
   - 四元组查询：用户明确给出 `marketing_goal`、`marketing_sub_goal`、`marketing_target_type`、`marketing_carrier_type` 这 4 个枚举值全部；或当前 session 已从 `get-rules.mjs` 返回中得到。
   - 推广产品 / 营销载体查询：用户明确给出构造请求体所需的完整 ID；或当前 session 已从 `get-assets.mjs` 返回中得到；**或步骤 1A 的 `get-assets-by-rules.mjs` 已成功匹配到资产**。
   - 转化目标查询：用户明确给出 `conversion_id`；或当前 session 已从 `get-conversions.mjs` 返回中得到。
   - 定向查询：用户没有任何定向约束时可跳过；只要用户给了地域、年龄、性别、排除已转化、设备等要求，就必须先调用 `get-targeting-lookup.mjs`。

---

## 步骤 1（⛔ 最先执行）：获取四元组

> **前置**：`account_id` + 用户营销需求
> **输出**：`marketing_goal`、`marketing_sub_goal`、`marketing_target_type`、`marketing_carrier_type`

**四元组**是腾讯广告的产品术语，指**营销内容 + 转化/优化目标的完整匹配集合**，共10个字段：
- 营销内容（4个）：`marketing_goal`、`marketing_sub_goal`、`marketing_carrier_type`、`marketing_target_type`
- 转化/优化目标（6个）：`optimization_goal`、`deep_behavior_optimization_goal`、`deep_behavior_advanced_goal`、`deep_worth_optimization_goal`、`deep_worth_advanced_goal`、`forward_link_assist`

这10个字段作为一个整体定义广告的投放语义，**必须从脚本返回的可选范围中选取，禁止通过推理猜测**。

**为什么不能猜？**
- 不同账号准入的组合不同，猜错会导致 `adgroups/add` 报错
- 看似相同的场景（如"电商推广"），在不同账号上对应的 `marketing_goal` 可能完全不同
- 四元组错误会级联导致后续推广产品、转化目标等全部错误

**调用方式**：

```bash
node scripts/get-rules.mjs '{"account_id":"<ACCOUNT_ID>"}'
```

示例：
```bash
node scripts/get-rules.mjs '{"account_id":"123456789"}'
```

**脚本已处理**：内部调用 `get_rules_by_advertiser`（不传 `delivery_scene`，获取常规广告可用组合），解析 `rules_json` 嵌套 JSON 字符串，按 `marketing_goal` 分组输出紧凑格式。

**返回格式说明**：

| 返回字段 | 含义 |
|---------|------|
| `goals` | 所有可用的 `marketing_goal` 列表 |
| `total` | 组合总数 |
| `default_sub_goal` | 大多数条目的 `marketing_sub_goal` 值（条目中无 `s` 时取此值） |
| `by_goal` | 按 goal 分组，每条含 `t`=marketing_target_type、`c`=marketing_carrier_type、`pt`=product_type；`s`=marketing_sub_goal（仅当与 default_sub_goal 不同时出现） |

> **所有枚举值均为完整 key（如 `MARKETING_TARGET_TYPE_APP_ANDROID`），可直接使用。**

**返回示例**：
```json
{
  "goals": ["MARKETING_GOAL_PRODUCT_SALES", "MARKETING_GOAL_USER_GROWTH"],
  "total": 5,
  "default_sub_goal": "MARKETING_SUB_GOAL_UNKNOWN",
  "by_goal": {
    "MARKETING_GOAL_PRODUCT_SALES": [
      {"t": "MARKETING_TARGET_TYPE_CONSUMER_PRODUCT", "c": "MARKETING_CARRIER_TYPE_JUMP_PAGE", "pt": 30}
    ],
    "MARKETING_GOAL_USER_GROWTH": [
      {"s": "MARKETING_SUB_GOAL_APP_ACQUISITION", "t": "MARKETING_TARGET_TYPE_APP_ANDROID", "c": "MARKETING_CARRIER_TYPE_APP_ANDROID", "pt": 43}
    ]
  }
}
```

**Agent 需要做的决策**：当返回多个组合时，根据用户意图选择正确的一组。

**选择规则（按优先级逐层过滤）**：

1. **先从用户意图提取关键约束**：
   - 用户提到了"卖货"/"电商"/"商品销售" → `marketing_goal` 应含 `PRODUCT_SALES`
   - 用户提到了"APP下载"/"拉新"/"注册" → `marketing_goal` 应含 `USER_GROWTH`
   - 用户提到了"品牌"/"曝光" → `marketing_goal` 应含 `BRAND_PROMOTION`
   - 用户提到了"线索"/"表单"/"留资" → `marketing_goal` 应含 `LEAD_RETENTION`
   - 用户提到了"涨粉"/"加关注" → `marketing_goal` 应含 `INCREASE_FANS_INTERACTION`
   - 用户提到了"小程序" → `marketing_target_type` 应含 `MINI_PROGRAM_WECHAT`
   - 用户提到了"APP"/"应用"作为**推广产品**（非营销载体） → `marketing_target_type` 应含 `APP_ANDROID` 或 `APP_IOS`。
   - 用户提到了"小游戏" → `marketing_target_type` 应含 `WECHAT_MINI_GAME`
   - 用户提到了"视频号直播"作为**推广对象**（非营销载体） → `marketing_target_type` 应含 `WECHAT_CHANNELS_LIVE`
   - 用户提到了"视频号直播"作为**营销载体** → `marketing_carrier_type` 应含 `WECHAT_CHANNELS_LIVE`（⛔ 不要据此设置 `marketing_target_type`）
   - 用户提到了"跳转页面" → `marketing_carrier_type` 应含 `JUMP_PAGE`
   - 用户提到了"新游推广"/"新游上线"/"新游首发"/"游戏上线" → `marketing_sub_goal` 应含 `NEW_GAME_LAUNCH`
   - 用户提到了"新游测试"/"测试服"/"删档测试"/"试玩"/"新客试玩" → `marketing_sub_goal` 应含 `NEW_GAME_TEST`
   - 用户提到了"新游预约"/"预约" → `marketing_sub_goal` 应含 `NEW_GAME_RESERVE`
   - 用户提到了"平稳期"/"长线运营"/"平稳期推广" → `marketing_sub_goal` 应含 `PLATEAU_PHASE_LAUNCH`
   - 用户提到了"小游戏新客"/"小游戏拉新"/"新客增长" → `marketing_sub_goal` 应含 `MINI_GAME_NEW_CUSTOMER_GROWTH`
   - 用户提到了"小游戏回流"/"小游戏促活"/"回流促活" → `marketing_sub_goal` 应含 `MINI_GAME_RETURN_CUSTOMER_ENGAGEMENT`

2. **按 `marketing_goal` 匹配用户的营销目标**

3. **按 `marketing_target_type` 匹配用户的推广对象类型**

   > ⛔⛔⛔ **前置强制检查（最高优先级）：用户是否同时给了「推广产品 ID 或名称」？**
   > - **是** → **禁止在步骤 1 确定 `marketing_target_type`，必须直接跳到步骤 1A**，把该 `marketing_goal` 下的**全部** combinations 传入，由脚本自动匹配。即使用户同时说了"营销载体: iOS应用"，也**绝对不能**据此把 combinations 缩窄为只含 `APP_IOS` 的那一个。
   > - **否** → 继续按下面的规则选择。
   >
   > ⚠️ `marketing_target_type` 反映的是"产品/店铺/内容"的类型，不要与优化目标、出价方式混淆。无法直接确定时，按 `marketing_goal` 过滤后从剩余项中选择。
   >
   > ⛔ **"营销载体"只能确定 `marketing_carrier_type`，禁止用来推断或缩窄 `marketing_target_type`。**

   > ⚠️ **商品库类 `marketing_target_type` 选择规则**（仅当 `PRODUCT_SALES` 且 combinations 同时含 `CONSUMER_PRODUCT`、`WECHAT_STORE_PRODUCT`、`WECHAT_STORE` 中多个时）：
   > 1. 用户明确说了"商品库" → 选 `CONSUMER_PRODUCT`
   > 2. 用户明确说了"微信小店"/"视频号小店" → 选 `WECHAT_STORE_PRODUCT`（推广单个商品）或 `WECHAT_STORE`（推广整个店铺），根据用户意图区分
   > 3. 用户给了推广产品名称或 ID → **⛔ 禁止暂定，必须直接进入步骤 1A** 通过资产反推确定。传给 1A 的 combinations 按 1A-① 规则过滤（只按 `marketing_goal` 过滤，其余维度全量）。
   > 4. 用户未明确且未给任何资产线索 → **暂定 `CONSUMER_PRODUCT`**，步骤 2 会根据资产查询结果自动回退（见步骤 2B「商品库类空资产回退」）

4. **⛔ 穷尽以上规则后仍无法唯一确定 `marketing_target_type` 时（强制检查点）**：
   > **先回答：用户是否给了推广产品的名称或 ID？**
   > - **是** → **立即进入步骤 1A**，通过资产反推确定四元组。**禁止猜测 `marketing_target_type`**。传给 1A 的 combinations 按 1A-① 规则过滤（只按 `marketing_goal` 过滤，其余维度全量）。
   > - **否** → 向用户列出剩余 combinations 中的 `marketing_target_type` 选项确认，附中文含义帮助选择。


5. **若过滤后 `marketing_carrier_type` 仍有多个可选值（即同一 `marketing_goal` + `marketing_target_type` 对应多种 carrier_type），必须向用户确认营销载体类型，不能自行猜测**。此时应将 combinations 中实际剩余的所有 `marketing_carrier_type` 选项列出给用户，让用户选择。例如："根据您的推广目标，当前支持以下营销载体：1) XXX  2) YYY  3) ZZZ，请问您要使用哪种？"（其中 XXX/YYY/ZZZ 替换为 combinations 中实际返回的 carrier_type 值）
6. **`marketing_sub_goal` 只能复用 `get-rules.mjs` 返回值，禁止语义改写**：例如用户说"注册"、"新客"、"拉新"时，也**不要**自造 `MARKETING_SUB_GOAL_USER_REGISTER`；如果步骤 1 返回的是 `MARKETING_SUB_GOAL_MINI_GAME_NEW_CUSTOMER_GROWTH` 或 `MARKETING_SUB_GOAL_APP_ACQUISITION`，后续所有脚本都必须原样复用

**步骤 1 完成后你应该有**：四元组 4 个值 + `product_type`（从 combinations 数组的匹配项取）。`product_type` 需透传给步骤 3 和步骤 4 的脚本。

---

## 步骤 1A（可选，有资产线索时执行）：通过资产反推四元组

> **⛔ 前置门禁：步骤 1 过滤后只剩 1 个 combination → 四元组已确定，直接跳到步骤 2，禁止进入 1A。** 即使用户给了推广产品 ID/名称也不需要 1A——资产查询在步骤 2 完成。
>
> **触发条件**（仅当通过前置门禁后）：用户提到了推广产品/资产的 **ID 或名称**，**且**步骤 1 过滤后仍有 **2 个及以上** combinations 无法唯一确定四元组。
>
> **不触发的情况**：① 步骤 1 已经唯一确定了四元组（只剩 1 个 combination）② 用户没有给出任何资产 ID 或名称线索

**目的**：通过查询账号下所有可能组合的真实资产列表，用用户给的资产 ID 或名称进行匹配，精确锁定四元组，**避免向用户确认**。

### 1A-① 预过滤（由脚本自动完成）

**⛔ 规则不变：只按 `marketing_goal` 过滤，`marketing_target_type` 和 `marketing_carrier_type` 维度不做任何缩窄。**

脚本内部自动调用 `get_rules_by_advertiser` API 获取全量 combinations，并按传入的 `marketing_goal` 过滤。**Agent 不需要透传 combinations 数组。** 脚本还支持传入 `marketing_target_type` 进行**优先查询**（非缩窄）：优先查该类型的资产并尝试匹配，命中则跳过其余类型的 API 调用以加速返回，未命中则自动 fallback 全量查询。脚本还会在资产匹配成功且载体类型需要时**自动查询载体列表**，结果通过 `carrier_result` 返回（详见 1A-③+）。

### 1A-② 调用 get-assets-by-rules.mjs

```bash
node scripts/get-assets-by-rules.mjs '{"account_id":"<ACCOUNT_ID>","marketing_goal":"<用户确定的MARKETING_GOAL或不传>","marketing_target_type":"<用户明确的TARGET_TYPE或不传>","match_hint":{"asset_id":"<用户给的ID或null>","asset_name":"<用户给的名称或null>"},"carrier_hint":{"carrier_id":"<用户给的载体ID或null>","carrier_name":"<用户给的载体名称或null>"}}'
```

**参数说明**：
- `account_id`：必填
- `marketing_goal`：可选。传入后脚本只查该 goal 下的 combinations（等价于原来 Agent 手动按 goal 过滤）。用户明确了 goal 就传，未明确就不传（脚本查全量）
- `marketing_target_type`：可选。用户明确了推广产品类型时传入（如用户说"小程序"就传 `MARKETING_TARGET_TYPE_MINI_PROGRAM_WECHAT`）。脚本会优先查该类型下的资产，匹配成功则跳过其余类型查询以加速返回；未传或优先查未命中时自动 fallback 全量查询。**注意**：这里传 `marketing_target_type` 仅影响查询顺序（优先查 → fallback 全量），不等同于步骤 1 中"缩窄 combinations"——即使传了，脚本仍保证不漏查其他类型
- `match_hint`：用户给了资产 ID 就传 `asset_id`，给了名称就传 `asset_name`，两个都给了就都传（ID 优先匹配）
- `carrier_hint`：可选，用户给了载体 ID 传 `carrier_id`，给了载体名称传 `carrier_name`

**返回示例（unique_match）**：
```json
{
  "asset_dict": {
    "MARKETING_GOAL_PRODUCT_SALES|MARKETING_SUB_GOAL_UNKNOWN|MARKETING_TARGET_TYPE_PRODUCT_AGGREGATION_PAGE|MARKETING_CARRIER_TYPE_JUMP_PAGE": {
      "combination": {
        "marketing_goal": "MARKETING_GOAL_PRODUCT_SALES",
        "marketing_sub_goal": "MARKETING_SUB_GOAL_UNKNOWN",
        "marketing_target_type": "MARKETING_TARGET_TYPE_PRODUCT_AGGREGATION_PAGE",
        "marketing_carrier_type": "MARKETING_CARRIER_TYPE_JUMP_PAGE",
        "product_type": 30
      },
      "asset_type": "INDUSTRY",
      "assets": [
        { "marketing_asset_id": "578879856", "name": "某资产名" }
      ]
    },
    "其他组合...": { "combination": {...}, "asset_type": "...", "assets": "[3 items, omitted]" }
  },
  "match_result": {
    "status": "unique_match",
    "match_type": "id_exact",
    "matched_items": [
      {
        "combination_key": "MARKETING_GOAL_PRODUCT_SALES|...|MARKETING_CARRIER_TYPE_JUMP_PAGE",
        "combination": { "marketing_goal": "...", "marketing_sub_goal": "...", "marketing_target_type": "...", "marketing_carrier_type": "...", "product_type": 30 },
        "asset_type": "INDUSTRY",
        "asset": { "marketing_asset_id": "578879856", "name": "某资产名" }
      }
    ]
  },
  "carrier_result": {
    "status": "found",
    "carriers": [
      { "carrier_id": "417200582", "carrier_name": "唯品会" }
    ],
    "matched_carrier": { "carrier_id": "417200582", "carrier_name": "唯品会" }
  }
}
```

> 注意：`unique_match` 时脚本会自动裁剪非命中 combination 的 `assets`（显示为 `"[N items, omitted]"`），减少上下文开销。

### 1A-③ 匹配结果处理

脚本返回的 `match_result` 已按优先级完成匹配，直接根据 `status` 处理：

| `match_result.status` | 含义 | 处理方式 |
|----------------------|------|---------|
| `unique_match` | 恰好 1 个 combination 下命中 1 条资产 | ✅ 直接使用 `matched_items[0].combination` 作为四元组，`matched_items[0].asset` 作为资产信息。**验证一致性**：如果用户同时给了营销目标线索（如"线索收集"），检查命中的 `marketing_goal` 是否一致。一致 → 直接使用；不一致 → 向用户提示矛盾并给出选项 |
| `multiple_match` | 同一资产存在于多个 combination 下 | 列出 `matched_items` 中各 combination 的中文说明供用户选择 |
| `name_multiple_match` | 名称匹配到多个不同资产 | 列出 `matched_items` 中各资产的 ID、名称、所属 combination 供用户确认 |
| `no_match` | 所有 combination 下都没找到匹配 | 去掉预过滤，用全部 combinations 重新查一次（不传 `match_hint` 之外的过滤条件）。仍然 `no_match` → 列出 `asset_dict` 中有资产的 combination 供用户参考，并给出可能原因（ID 输错、资产不在该账户下等） |

### 1A-③+ 载体查询结果处理（`carrier_result`）

当资产匹配成功（`unique_match` / `multiple_match`）且载体类型不是 `JUMP_PAGE` 时，脚本**自动查询载体列表**并返回 `carrier_result`。

| `carrier_result.status` | 含义 | 处理方式 |
|------------------------|------|---------|
| `found` + `matched_carrier` 不为 null | 载体查询成功且匹配到载体 | ✅ 已反映在 `flat_params.carrier_id` 中，直接透传 |
| `found` + `matched_carrier` 为 null | 载体查询成功但未匹配到（多个载体且无 hint） | 列出 `carriers` 供用户选择 |
| `not_needed` | ONEID/视频号类资产已包含 carrier_id，或载体类型为 JUMP_PAGE | 已反映在 `flat_params.carrier_id` 中（ONEID 类），或不需要 carrier_id（JUMP_PAGE） |
| `no_carriers` | 查询成功但该账号下无载体 | 向用户确认载体信息 |
| `skipped` | 资产匹配未成功，未触发载体查询 | 正常流程，后续步骤 2 处理 |
| `match_failed` | 载体查询接口调用失败 | 从用户输入获取载体 ID，或向用户确认 |

> **载体查询的接口路由**（脚本内部自动判断，Agent 无需关心）：
> - 统一通过 `bff_promoted_objects/get` 接口查询，脚本根据 `marketing_carrier_type` 自动映射到对应的 `promoted_object_type`

### 1A-④ 步骤 1A 完成后的影响

| 1A 结果 | 对后续步骤的影响 |
|---------|----------------|
| **成功确定四元组 + 资产 + 载体**（`unique_match` + `carrier_result.matched_carrier`） | ✅ 四元组已确定，脚本已输出 `flat_params` → **步骤 2 可跳过**，直接将 `flat_params` 中的字段透传给步骤 6 的 `create-adgroup.mjs` |
| **成功确定四元组 + 资产**（`unique_match`，但载体未匹配） | ✅ 四元组已确定，`flat_params` 已输出（可能缺少 `carrier_id`）→ **步骤 2 可跳过 `get-assets.mjs` 调用**，载体 ID 待后续步骤获取 |
| **未能确定**（`multiple_match` / `name_multiple_match` / `no_match`） | 已向用户确认 → 得到答案后确定四元组，进入步骤 2 正常执行 |

---

## 步骤 2（⛔ 默认必须执行）：获取推广产品 + 营销载体

> **前置**：步骤 1 的 `marketing_target_type`、`marketing_carrier_type`、`marketing_goal`
> **输出**：`asset_id`、`carrier_id` 等扁平 ID（步骤 6 传给 `create-adgroup.mjs`，由脚本自动组装为 API 所需的嵌套结构）

> ⚡ **快速路径**：如果步骤 1A 的 `match_result.status` 为 `unique_match`，**可跳过 `get-assets.mjs` 调用**，直接使用脚本返回的 `flat_params` 中的扁平 ID。

> ⚡ **ONEID 类自动短路**：当用户给了明确的资产 ID 时，通过 `asset_hint.asset_id` 传给 `get-assets.mjs`，脚本内部会自动短路（不调 API，直接返回 `shortcut: true`），返回的 `flat_params` 可直接透传。用户给的是名称时传 `asset_hint.asset_name`，脚本不会短路，走正常查询。

**调用方式**（步骤 1A 未执行或未成功时）：

```bash
node scripts/get-assets.mjs '{"account_id":"<ACCOUNT_ID>","marketing_target_type":"<...>","marketing_carrier_type":"<...>","marketing_goal":"<...>","product_type":<number>,"carrier_hint":{"carrier_id":"...","carrier_name":"..."},"asset_hint":{"asset_id":"...","asset_name":"..."}}'
```

**参数说明**：
- `account_id`、`marketing_target_type`：必填
- `marketing_carrier_type`、`marketing_goal`：可选
- `product_type`：可选，来自步骤 1 的 `combination.product_type`，载体查询时使用
- `carrier_hint`：可选，用于载体匹配。用户给了载体 ID 就传 `carrier_id`，给了载体名称就传 `carrier_name`
- `asset_hint`：可选，用户给了明确的资产 ID 就传 `asset_id`，给了资产名称就传 `asset_name`。ONEID 类传 `asset_id` 时脚本自动短路

> **⚡ 载体查询已内置**：当传入 `marketing_carrier_type` + `product_type`（或 `carrier_hint`）时，脚本会**自动查询并匹配载体**，返回 `carrier_result` 字段。无需额外调用 `get-assets-by-rules.mjs` 来获取载体 ID。

**脚本已处理**：自动根据 `marketing_target_type` 判断分类（ONEID / 商品库 / 行业产品库），路由到正确的 API，返回统一格式的资产列表。同时自动查询载体（如需要）。

**返回示例（ONEID 类）**：
```json
{
  "asset_type": "ONEID",
  "assets": [
    {
      "marketing_asset_outer_id": "wx1234567890",
      "marketing_carrier_id": "wx1234567890",
      "name": "我的小程序",
      "type": "MINI_PROGRAM_WECHAT"
    }
  ],
  "carrier_result": {
    "status": "not_needed",
    "reason": "ONEID/视频号类资产已包含 marketing_carrier_id"
  }
}
```

**Agent 需要做的决策——资产选择规则（⛔ 禁止默认选第一个）**：

1. **用户提及了产品/商品名称** → 从 `assets` 中选 `asset_name`（或 `name`）与用户意图最相关的项
2. **仅 1 个资产** → 直接使用
3. **多个且无法区分** → 展示给用户确认

### 2A. 透传 `flat_params` 给步骤 6（⛔ 不要手动构造嵌套结构）

> **核心原则：Agent 只负责将脚本返回的扁平 ID 透传给步骤 6 的 `create-adgroup.mjs`。嵌套结构（`marketing_asset_outer_spec`、`marketing_asset_id`、`marketing_carrier_detail`）全部由 `create-adgroup.mjs` 根据 `marketing_target_type` / `marketing_carrier_type` 自动组装，Agent 不要手动构造。**

**`get-assets-by-rules.mjs` 的 `flat_params`**：

脚本会为**每条 `matched_items`** 都计算并挂载 `flat_params`（与 `create-adgroup.mjs` 入参直接对齐）：
- `unique_match` → 顶层也输出 `flat_params`（= `matched_items[0].flat_params`），**Agent 直接透传即可**
- `multiple_match` / `name_multiple_match` → 用户选完后，取对应项的 `matched_items[n].flat_params` 即可，无需手动提取字段

```json
{
  "flat_params": {
    "asset_id": "342574",        // INDUSTRY → marketing_asset_id; ONEID → marketing_asset_outer_id; CATALOG → catalog_id
    "carrier_id": "417200582",   // 优先 carrier_result.matched_carrier，其次 ONEID 资产的 marketing_carrier_id
    "catalog_id": "123456",      // 仅商品库类
    "asset_sub_id": "...",       // 商品库子 ID / ONEID 子包 / 直播预约 notice_id 等（可选）
    "sub_carrier_id": "..."      // 通常与 asset_sub_id 同值（可选）
  }
}
```

**`get-assets.mjs` 的 `flat_params`**：

`get-assets.mjs` 也会为**每条 `assets`** 都挂载 `flat_params`，格式与上面一致。Agent 选完后直接取 `assets[n].flat_params` 透传即可。`assets` 恰好 1 条时顶层也输出 `flat_params`（= `assets[0].flat_params`）。

> **总结：无论走哪个脚本、匹配到几条，每条结果都带 `flat_params`。Agent 选定后直接透传，永远不需要手动判断"该取哪个字段"。**

**`asset_sub_id` / `sub_carrier_id` 补充说明**（`flat_params` 已自动处理，以下仅供了解）：
- **APP_ANDROID**：子包标识（如 `"0;00011609313139363030393334"`），`asset_sub_id` 和 `sub_carrier_id` 填同一值
- **PC_GAME**：区服标识（如 `"hwbz"`），`asset_sub_id` 和 `sub_carrier_id` 填同一值
- **WECHAT_CHANNELS_LIVE_RESERVATION**：直播预约 `notice_id`（如 `"finderlivenotice-..."`），`asset_sub_id` 和 `sub_carrier_id` 填同一值
- **商品库类**（CONSUMER_PRODUCT / WECHAT_STORE_PRODUCT / COMMODITY_SET / WECHAT_STORE_PRODUCT_SET）：`asset_sub_id` = `product_outer_id` / `wechat_store_id` / `commodity_set_id`
- 无子级时不传这两个字段即可

**`carrier_id` 的来源**（按优先级）：
1. `flat_params.carrier_id`（两个脚本每条结果都带，最简单直接）
2. 用户明确给出的载体 ID。**⛔ 用户给的"推广产品 ID"不是载体 ID，两者不可互换。**
3. 以上都没有时，需向用户确认

**视频号直播预约场景补充**：`get-assets.mjs` 返回含 `live_notices`，Agent 必须选取 `notice_id`（格式 `finderlivenotice-xxx`），同时传给 `asset_sub_id` 和 `sub_carrier_id`。多场次选择：① 用户指定 → 匹配 ② 未指定 → `start_time` 最晚且在投放日期内 ③ 都不在范围 → `start_time` 最晚。（`get-assets-by-rules.mjs` 的 `flat_params` 中已自动选取最晚场次，如需用户指定可覆盖）

> **脚本会根据 `marketing_target_type` 自动判断三分类（ONEID / 商品库 / 行业产品库），组装正确的 `marketing_asset_outer_spec` 或 `marketing_asset_id`。根据 `marketing_carrier_type` 自动判断是否需要 `marketing_carrier_detail`。不需要手动构造这些嵌套结构。**

### 2B. 强约束

- **白名单例外**：用户在原始需求里已明确给出完整 ID（如 `catalog_id`、`product_outer_id`、`marketing_asset_id` 等），则可直接作为对应的扁平 ID 使用并跳过查询。ONEID 类用户给了资产 ID 时通过 `asset_hint.asset_id` 传给 `get-assets.mjs`，脚本会自动短路处理。
- **空字符串不是合法结果**：不要把空字符串当作"已完成步骤 2"。查不到且用户也未提供时，保留缺失状态。
- **⚠️ 商品库类空资产回退（脚本已自动处理）**：`get-assets.mjs` 内部已实现自动回退——当 `CONSUMER_PRODUCT` 查询返回空资产时，脚本会自动尝试 `WECHAT_STORE_PRODUCT`，反之亦然。**Agent 无需手动重试或切换类型**。
  - 回退成功时，返回结果中会包含 `actual_marketing_target_type`（实际生效的类型）和 `fallback_applied: true`
  - **⛔ Agent 必须检查返回的 `actual_marketing_target_type` 字段**：如果与传入的类型不同，说明发生了回退，后续步骤 3~7 都必须使用 `actual_marketing_target_type` 的值（而非原始传入值）
  - 如果返回 `assets: []` 且无 `fallback_applied`，说明两种类型都没有资产，按正常的空结果处理（保留缺失状态）
- **跳转页面载体 (`MARKETING_CARRIER_TYPE_JUMP_PAGE`)**：不需要传 `carrier_id`，但推广资产仍需正常查询

**步骤 2 完成后你应该有**：`flat_params`（包含 `asset_id`、`carrier_id` 等扁平 ID），或已从脚本返回中选定了一条带 `flat_params` 的资产。这些值不能是空字符串。

---

## 步骤 3（⛔ oCPM/oCPC 必须执行）：确定版位

> **前置**：步骤 1 的 `marketing_target_type`、`marketing_carrier_type`
> **输出**：`site_set`（数组）或确认使用自动版位

> ⚡ **快速路径**：仅 CPC/CPM + 自动版位 → 直接设 `automatic_site_enabled: true`，**跳过本步查询**，进入步骤 4。
>
> ⛔ **oCPM/oCPC 时必须调用 `get-site-set.mjs`**，即使用户已明确指定了版位名称。原因：步骤 4 的 `get-conversions.mjs` 依赖此步返回的 `available_site_set` 来构造 `site_set` 参数，用户给的版位名称不能直接替代。

版位决定了广告的投放位置。常规广告支持**手动选择版位**和**自动版位**两种模式。

**版位确定规则**：

1. **用户指定了版位** → 先调用 `get-site-set.mjs`，再从脚本返回的真实 `available_site_set` 中选择（如"投朋友圈" → `["SITE_SET_MOMENTS"]`；如"投腾讯平台与内容媒体/PCAD" → 按 3B 一级分类展开为 `["SITE_SET_KANDIAN", "SITE_SET_QQ_MUSIC_GAME", "SITE_SET_TENCENT_NEWS", "SITE_SET_TENCENT_VIDEO"]` 再与 `available_site_set` 取交集）。**确定最终的用户版位列表供步骤 4B 和步骤 6 使用**
2. **用户要求自动版位** → `automatic_site_enabled: true`，仍需查询可用版位列表，后续 `get-conversions.mjs` 传入 `auto_site_set` 中的版位
3. **用户未指定版位** → 推荐自动版位，仍需调用 `get-site-set.mjs` 获取版位列表

### 3A. 获取可用版位列表

```bash
node scripts/get-site-set.mjs '{"account_id":"<ACCOUNT_ID>","marketing_goal":"<MARKETING_GOAL_枚举key>","marketing_sub_goal":"<MARKETING_SUB_GOAL_枚举key>","marketing_target_type":"<MARKETING_TARGET_TYPE_枚举key>","marketing_carrier_type":"<MARKETING_CARRIER_TYPE_枚举key>"}'
```

示例：
```bash
node scripts/get-site-set.mjs '{"account_id":"123456789","marketing_goal":"MARKETING_GOAL_USER_GROWTH","marketing_sub_goal":"MARKETING_SUB_GOAL_UNKNOWN","marketing_target_type":"MARKETING_TARGET_TYPE_APP_ANDROID","marketing_carrier_type":"MARKETING_CARRIER_TYPE_APP_ANDROID"}'
```

**脚本已处理**：内部自动设置 `bid_mode`、`buying_type`、`campaign_type` 等 API 必传参数，调用方只需传四元组枚举 key。

**返回**：
```json
{
  "available_site_set": ["SITE_SET_MOMENTS", "SITE_SET_WECHAT", "SITE_SET_MOBILE_UNION", "SITE_SET_QQ_MUSIC_GAME", "SITE_SET_TENCENT_VIDEO", "SITE_SET_CHANNELS", "SITE_SET_MOBILE_YYB"],
  "auto_site_set": ["SITE_SET_MOMENTS", "SITE_SET_WECHAT", "SITE_SET_MOBILE_UNION"],
  "non_multi_site_set": ["SITE_SET_MOBILE_YYB"]
}
```

### 3B. 版位枚举对照表（权威）

> ⚠️ **此表为 API 真实枚举 key 与中文名称的对照表，以 API 文档为准。Agent 在从用户自然语言映射版位时，必须参考此表，严禁凭猜测使用表中不存在的 key。**

| 枚举值 | 说明 | 用户常见说法 | 备注 |
|--------|------|-------------|------|
| `SITE_SET_MOMENTS` | 微信朋友圈 | "朋友圈" | |
| `SITE_SET_WECHAT` | 微信公众号与小程序 | "公众号"、"小程序" | |
| `SITE_SET_MOBILE_UNION` | 腾讯广告联盟 | "优量汇"、"联盟"、"广告联盟" | |
| `SITE_SET_TENCENT_NEWS` | 腾讯新闻 | "腾讯新闻" | |
| `SITE_SET_TENCENT_VIDEO` | 腾讯视频 | "腾讯视频" | |
| `SITE_SET_MOBILE_YYB` | 应用宝 | "应用宝" | |
| `SITE_SET_PCQQ` | 腾讯广告电脑端（PC） | "QQ"、"PC QQ"、"电脑端" | |
| `SITE_SET_KANDIAN` | QQ浏览器（原腾讯看点） | "QQ浏览器"、"看点" | |
| `SITE_SET_QQ_MUSIC_GAME` | QQ、腾讯音乐及游戏 | "QQ音乐"、"腾讯音乐"、"QQ游戏" | |
| `SITE_SET_CHANNELS` | 微信视频号 | "视频号" | |
| `SITE_SET_WECHAT_PLUGIN` | 微信新闻插件 | "微信插件"、"微信新闻插件" | |
| `SITE_SET_SEARCH_SCENE` | 搜索场景 | "搜索"、"搜索场景" | |
| `SITE_SET_WECHAT_SEARCH` | 微信搜一搜 | "微信搜索"、"搜一搜" | ⚠️ 仅支持搜索广告 |
| `SITE_SET_QBSEARCH` | QQ浏览器等搜索 | "QQ浏览器搜索" | ⚠️ 仅支持搜索广告 |
| `SITE_SET_SEARCH_MOBILE_UNION` | 腾讯广告联盟搜索 | "联盟搜索" | |

> **⛔ `site_set` 枚举值只允许使用上表第一列的 key，禁止自行从中文翻译构造枚举名。** 脚本返回什么就用什么。
>
> **⚠️ 标注"仅支持搜索广告"的版位**（`SITE_SET_WECHAT_SEARCH`、`SITE_SET_QBSEARCH`）**在非搜索场景下不可使用**，不要将其加入普通展示广告的 `site_set`。

#### 版位集合一级分类对照表
| 一级分类名称 | 包含的版位枚举值 | 常见说法 |
|-------------|-----------------|-------------|
| 微信视频号 | `SITE_SET_CHANNELS` | "视频号" |
| 微信朋友圈 | `SITE_SET_MOMENTS` | "朋友圈" |
| 微信公众号与小程序 | `SITE_SET_WECHAT`、`SITE_SET_WECHAT_PLUGIN` | "公众号"、"小程序"、"公众号与小程序" |
| 腾讯平台与内容媒体(PCAD) | `SITE_SET_KANDIAN`、`SITE_SET_QQ_MUSIC_GAME`、`SITE_SET_TENCENT_NEWS`、`SITE_SET_TENCENT_VIDEO` | "腾讯平台"、"内容媒体"、"腾讯平台与内容媒体"、"PCAD" |
| 腾讯广告联盟 | `SITE_SET_MOBILE_UNION` | "优量汇"、"联盟"、"广告联盟" |
| 应用宝 | `SITE_SET_MOBILE_YYB` | "应用宝" |
| 腾讯广告电脑端（PC） | `SITE_SET_PCQQ` | "QQ"、"PC QQ"、"电脑端" |
| 微信搜一搜 | `SITE_SET_WECHAT_SEARCH` | "微信搜索"、"搜一搜"（⚠️ 仅搜索广告） |
| QQ浏览器等 | `SITE_SET_QBSEARCH` | "QQ浏览器搜索"（⚠️ 仅搜索广告） |
| 腾讯广告联盟搜索 | `SITE_SET_SEARCH_MOBILE_UNION` | "联盟搜索" |
| 搜索场景 | `SITE_SET_SEARCH_SCENE` | "搜索场景" |

### 3C. 强约束

- **手动版位**：`automatic_site_enabled: false` + `site_set` 数组（来自脚本返回的 `available_site_set` 或用户指定，按上表映射）
- **自动版位**（推荐）：`automatic_site_enabled: true`，`site_set` 不传

#### ⚠️ 传给 `get-conversions.mjs` 的 `site_set` 参数规则（仅 oCPM/oCPC 需关注，CPC/CPM 跳过）

> **⛔ `site_set` 只能包含 `available_site_set` 中存在的版位。** 必须传入用户最终选择的版位列表**（即手动版位场景下用于 `adgroups/add` 的 `site_set`，自动版位场景下传 `auto_site_set`），**要根据用户实际选择的版位传入，不要盲目传完整的 `available_site_set`**。

| 场景 | `get-conversions.mjs` 的 `site_set` |
|------|--------------------------------------|
| **自动版位** | 传 `auto_site_set` **完整数组原样传入**，不要只传用户提到的"优先版位" |
| **手动版位** | 传 **用户指定版位 ∩ `available_site_set`**（取交集） |

> ⚠️ 用户说的"优先版位"（如"优先视频号"）≠ `site_set` 参数。"优先版位"影响的是 `priority_site_set`，而 `get-conversions.mjs` 的 `site_set` 是查询范围，自动版位时必须传 `auto_site_set` 全量。

**❌ 典型错误**：自动版位时只传了 `["SITE_SET_CHANNELS"]`（用户的优先版位）→ 应传 `auto_site_set` 全量。

**步骤 3 完成后你应该有**：版位模式（自动/手动）+ 供步骤 4 使用的 `site_set`（oCPM/oCPC 时：自动版位 = `auto_site_set` 全量，手动版位 = 用户指定 ∩ `available_site_set`；CPC/CPM + 自动版位时无需 `site_set`）。

### 3D. 版位定投场景（`scene_spec`，可选）

> **`scene_spec` 是请求体根层级字段（与 `targeting` 并列），用于对已选版位内的流量做精细筛选。**
> **默认"不限"（不传），仅在用户明确提到定投/屏蔽特定流量场景时才构造。**

**场景定向完整字段**（以下字段均放在 `scene_spec: { ... }` 对象内）：

| 场景维度 | `scene_spec` 内的字段 | 类型 | 说明 | 获取方式 |
|---------|---------------------|------|------|---------|
| 联盟场景定向 | `mobile_union` | enum[] | 腾讯广告联盟流量场景定向（如信息流原生、开屏等） | ✅ `get-enum-options.mjs '{"fields":["scene_spec_mobile_union"]}'` |
| 联盟场景屏蔽 | `exclude_mobile_union` | enum[] | 联盟流量场景屏蔽 | ✅ `get-enum-options.mjs '{"fields":["scene_spec_exclude_mobile_union"]}'` |
| 联盟自定义定投 | `union_position_package` | integer[] | 定投联盟流量包 ID 列表 | 用户提供流量包 ID |
| 联盟自定义屏蔽 | `exclude_union_position_package` | integer[] | 屏蔽联盟流量包 ID 列表 | 用户提供流量包 ID |
| 联盟媒体类型 | `mobile_union_category` | integer[] | 联盟媒体类型场景定向 ID | 用户提供 |
| 腾讯新闻场景 | `tencent_news` | enum[] | 腾讯新闻流量场景 | ✅ `get-enum-options.mjs '{"fields":["scene_spec_tencent_news"]}'` |
| 广告展示场景 | `display_scene` | enum[] | 广告展示场景 | ✅ `get-enum-options.mjs '{"fields":["scene_spec_display_scene"]}'` |
| QQ浏览器场景 | `qbsearch_scene` | enum[] | QQ浏览器、应用宝流量场景 | ✅ `get-enum-options.mjs '{"fields":["scene_spec_qbsearch_scene"]}'` |
| PC端定投 | `pc_scene` | enum[] | PC端定投场景 | ✅ `get-enum-options.mjs '{"fields":["scene_spec_pc_scene"]}'` |
| 搜一搜场景 | `wechat_search_scene` | enum[] | 搜一搜流量场景 | ✅ `get-enum-options.mjs '{"fields":["scene_spec_wechat_search_scene"]}'` |
| 微信公众号小程序定投 | `wechat_position` | integer[] | 定投指定公众号/小程序的 ID 列表 | 用户提供 |
| 视频号定投 | `wechat_channels_scene` | integer[] | 定投指定视频号的 ID 列表 | 用户提供 |
| 微信场景定向 | `wechat_scene` | struct | 微信流量细分场景，子字段见下方 | 用户提供 |

**`wechat_scene` 子字段**：

| 子字段 | 类型 | 说明 |
|--------|------|------|
| `official_account_media_category` | integer[] | 公众号媒体类型 ID |
| `mini_program_and_mini_game` | integer[] | 小程序/小游戏流量类型 ID |
| `pay_scene` | integer[] | 订单详情页消费场景 ID |

**构造示例**：

定投联盟流量包 + 屏蔽指定流量包：
```json
"scene_spec": {
  "union_position_package": [6001403],
  "exclude_union_position_package": [91019]
}
```

定投指定公众号 + 联盟信息流场景：
```json
"scene_spec": {
  "mobile_union": ["MOBILE_UNION_SCENE_IN_FEEDS_NATIVE"],
  "wechat_position": [123456, 789012]
}
```

> ⚠️ **枚举类字段**（`mobile_union`、`exclude_mobile_union`、`tencent_news`、`display_scene`、`qbsearch_scene`、`pc_scene`、`wechat_search_scene`）**必须通过 `get-enum-options.mjs` 查询确认枚举值，禁止猜测**。
> ⚠️ **ID 列表类字段**（`union_position_package`、`exclude_union_position_package`、`wechat_position`、`mobile_union_category`、`wechat_channels_scene`、`wechat_scene` 子字段）**直接传用户给出的 ID**。
> ⚠️ 用户未提到任何版位定投场景需求时，**不传 `scene_spec`**（等同于 UI 上全部选"不限"）。

---

## 步骤 4：获取转化目标 + 确定出价

> **前置**：步骤 1 的四元组 + 步骤 2 的资产 ID + 步骤 3 的 site_set
> **输出**：`conversion_id`（可选）、`bid_mode`、`smart_bid_type`、`bid_amount`（手动出价时）或 `daily_budget`（自动出价时）

> ⚡ **快速路径**：CPC/CPM → 跳过 4B 转化查询，只需确定 `bid_mode` + `bid_amount`，然后进入步骤 5。

### 4A. 确定出价方式 (bid_mode)

根据用户意图确定出价方式：

| 枚举值 | 说明 | 需要 conversion_id |
|--------|------|-------------------|
| `BID_MODE_CPC` | 按点击付费 | 否 |
| `BID_MODE_CPM` | 按千次展示付费 | 否 |
| `BID_MODE_OCPM` | 优化千次展示出价（**推荐**） | **是** |
| `BID_MODE_OCPC` | 优化点击出价 | **是** |

**核心规则**：
1. **CPC/CPM**：只需 `bid_mode` + `bid_amount`，**不需要**查询转化目标，跳过步骤 4B
2. **oCPM/oCPC**：需 `bid_mode` + `conversion_id`，手动出价（`CUSTOM`）还需 `bid_amount`
3. 用户未指定出价方式时，默认使用 `BID_MODE_OCPM`

#### 4A-2. 确定出价方案（`smart_bid_type`）

| 出价方案 | 用户意图 | 传参 |
|---------|---------|------|
| **手动出价 `CUSTOM`**（默认） | 给了具体出价金额 / "稳定投放" / 未提及 | `smart_bid_type: SMART_BID_TYPE_CUSTOM`，`bid_amount` 必填且 > 0 |
| **最大转化量 `SYSTEMATIC`** | "最大转化" / "自动出价" / "系统出价" / "优先跑量" | `smart_bid_type: SMART_BID_TYPE_SYSTEMATIC`，`daily_budget` 必填且 > 0，**不传 `bid_amount`** |

> CPC/CPM 固定走手动出价。oCPM/oCPC 根据用户意图选择，默认手动出价。

**`SYSTEMATIC`（最大转化量）约束**：
1. `daily_budget` **必填且 > 0**，用户未给时**必须向用户确认**
2. `bid_amount` **不传**
3. 必须是 oCPM/oCPC
4. ⛔ 不能同时开启：`auto_acquisition_enabled`、`live_recommend_strategy_enabled`、`aoi_optimization_strategy`

**控制成本（仅 `SYSTEMATIC` 可用）**：

根据是否配置了 ROI 深度优化，选择对应字段（**二选一，互斥**）：

| 广告类型 | 判断条件 | 使用字段 | 范围 |
|---------|---------|---------|------|
| **非 ROI** | 未配 `deep_conversion_type` 为 `WORTH`/`WORTH_ADVANCED` | `custom_cost_cap`（分） | 0 < 值 ≤ 2,000,000 |
| **ROI** | 配了 `deep_conversion_type` 为 `WORTH` 或 `WORTH_ADVANCED` | `custom_cost_roi_cap`（float） | > 0 |

> 都需同时传 `cost_constraint_scene: COST_CONSTRAINT_SCENE_OPEN`

### 4B. 获取转化目标（仅 oCPM/oCPC 需要）

```bash
node scripts/get-conversions.mjs '{"account_id":"<ACCOUNT_ID>","site_set":["<用户表达的版位>"],"available_site_set":["<步骤3返回的全量可用版位>"],"non_multi_site_set":["<步骤3返回的non_multi_site_set>"],"marketing_carrier_id":"<步骤2返回的载体ID>","asset_id":"<步骤2返回的行业资产ID>","marketing_goal":"<MARKETING_GOAL_枚举key>","marketing_sub_goal":"<MARKETING_SUB_GOAL_枚举key>","marketing_carrier_type":"<MARKETING_CARRIER_TYPE_枚举key>","marketing_target_type":"<MARKETING_TARGET_TYPE_枚举key>","create_source_type":"<CreateSourceType的枚举值，用户未提及来源时不传此参数>"}'
```

> **注意**：常规广告不需要传 `delivery_scene`。四元组字段统一传**字符串枚举 key**，脚本内部自动转为数值。`bid_mode` 来自步骤 4A 的出价方式（如 `BID_MODE_OCPM`），用于按出价方式过滤转化目标。
>
> **`create_source_type`**：如果用户指定了转化来源，则根据用户意图传入——`PLATFORM`平台转化或`SELF_CREATED`自建转化等。用户未提及来源时不传此参数。
>
> **⛔ `site_set` 参数来源**：必须严格按步骤 3C 的规则传入——自动版位时传步骤 3 返回的 **`auto_site_set` 完整数组**（不是用户提到的"优先版位"子集），手动版位时传用户指定版位与 `available_site_set` 的交集。
>
> **⛔ `available_site_set` 参数**：**必须同时传入**步骤 3 返回的 `available_site_set` 完整数组（即 `get-site-set.mjs` 返回的全量可用版位列表）。脚本内部会用 `site_set` ∩ `available_site_set` 取交集，作为防御性校验，确保只传入合法版位。**即使你认为 `site_set` 已经是正确的子集，也必须传 `available_site_set`。**
>
> **⛔ `non_multi_site_set` 参数**：**必须同时传入**步骤 3 返回的 `non_multi_site_set` 数组（不支持多版位组合的版位列表，即 `site_set_multi=0` 的版位）。脚本内部会自动过滤掉这些版位（除非用户只选了一个版位），避免查询转化目标时传入不支持多版位组合的版位。
>
> **⛔ 行业产品库类（步骤 2 返回 `asset_type: "INDUSTRY"`）** 传 `asset_id`！
>
> **`marketing_carrier_id`** 和 **`asset_id`** 是两个独立参数，由脚本按两个维度分别决定是否传给 API：
> - **`marketing_carrier_id`**（→ API 的 `product_id`）：传入 `flat_params.carrier_id`。脚本根据 `marketing_carrier_type` 判断是否传：除页面跳转 (`JUMP_PAGE`) 外的载体类型都传。
> - **`asset_id`**（→ API 的 `marketing_asset_id`）：仅**行业产品库类**需要传（`asset_type: "INDUSTRY"` 时），传入 `flat_params.asset_id`。ONEID 类和商品库类不需要传此字段。
> - 两者可以都传、只传一个、或都不传，互不排斥。
>
> **⛔ 特别注意**：当 `asset_type: "INDUSTRY"` 时，**必须**将 `flat_params.asset_id` 作为 `asset_id` 传入本脚本，否则转化目标查询可能会失败！

**脚本已处理**：通过 `access_status` 过滤仅返回已完成接入的转化目标，标注深度转化类型，裁剪无关字段。

**返回示例**：
```json
{
  "goals": [
    {
      "conversion_id": 12345,
      "name": "APP激活",
      "optimization_goal": "OPTIMIZATIONGOAL_APP_ACTIVATE",
      "bid_mode": "BID_MODE_OCPM",
      "has_deep_conversion": false,
      "create_source_type": "PLATFORM"
    },
    {
      "conversion_id": 12346,
      "name": "注册-首日付费ROI",
      "optimization_goal": "OPTIMIZATIONGOAL_APP_REGISTER",
      "bid_mode": "BID_MODE_OCPM",
      "has_deep_conversion": true,
      "deep_conversion_type": "DEEP_CONVERSION_WORTH",
      "deep_conversion_worth_goal": "OPTIMIZATIONGOAL_1DAY_PURCHASE_ROAS",
      "create_source_type": "SELF_CREATED"
    }
  ]
}
```

**Agent 需要做的决策——conversion 选择规则**：

1. **排除 `permission=1` 的项**（脚本已过滤，但仍需意识到约束）
2. **用户提供了深度出价参数时**（ROI 系数或行为出价金额），按以下三步选择：
   - **Step A — 确定出价字段**：根据用户自然语言，参考文末「用户意图提取规则」表，确定对应的出价字段名（如 `deep_conversion_worth_rate`）
   - **Step B — 反推 deep_conversion_type**：根据下方 4D 映射表，从出价字段名反推对应的 `deep_conversion_type`（如 `deep_conversion_worth_rate` → `DEEP_CONVERSION_WORTH`）
   - **Step C — 从 goals 中选择**：在 goals 列表中，找 `has_deep_conversion=true` 且 `deep_conversion_type` 与 Step B 结果一致的转化ID。**不同 `deep_conversion_type` 的 conversion_id 不可互换**
3. **用户指定了优化目标（但没给深度出价参数）** → 按 `name` 字段匹配
4. **用户未指定** → 取 goals 数组第一个项
4. **用户指定了转化创建来源**（如"自建转化"/"自建归因"/"自建"/"自定义转化"→ `SELF_CREATED`，"平台预置"/"平台转化"/"平台上报"/"系统预置"/"预置转化"→ `PLATFORM`）→ 在调用 `get-conversions.mjs` 时传入 `create_source_type` 过滤；**用户未提及来源时不传此参数**

### 4C. 出价字段清单

| 字段 | 类型 | 必填 | 说明 | 如何获取 |
|------|------|------|------|----------|
| `bid_mode` | enum | 否 | 出价方式 | 用户提供，默认 `BID_MODE_OCPM` |
| `bid_amount` | integer | 手动出价必填 | 出价（单位：**分**）。`CUSTOM` 时必填且 > 0；**`SYSTEMATIC` 时不传** | "出价5元" → `500` |
| `conversion_id` | integer | oCPM/oCPC 必填 | 转化ID | 4B 获取 |
| `deep_conversion_spec` | struct | 否 | 深度转化优化配置 | 见下方 |
| `deep_conversion_behavior_bid` | integer | 否 | 深度OG出价（分）（对应 `DEEP_CONVERSION_BEHAVIOR`） | 用户说"深度出价X元"/"深度行为出价"/"深度OG出价" |
| `deep_conversion_behavior_advanced_bid` | integer | 否 | 深度辅助OG出价（分）（对应 `DEEP_CONVERSION_BEHAVIOR_ADVANCED`） | 用户说"深度辅助出价X元"/"深度辅助OG出价" |
| `deep_conversion_worth_rate` | float | 否 | 深度ROI出价 / 深度转化价值率（对应 `DEEP_CONVERSION_WORTH`） | 用户说"深度ROI X"/"深度转化价值率X"，支持3位小数 |
| `deep_conversion_worth_advanced_rate` | float | 否 | 深度辅助ROI（对应 `DEEP_CONVERSION_WORTH_ADVANCED`） | 用户说"深度辅助ROI X"，支持3位小数 |
| `smart_bid_type` | enum | **是** | `SMART_BID_TYPE_CUSTOM`（手动出价，默认）或 `SMART_BID_TYPE_SYSTEMATIC`（最大转化量）。见 4A-2 决策表 | 根据用户意图选择 |
| `daily_budget` | integer | **是** | 日预算（分，5000~400000000）。`CUSTOM`：用户未提及传 `0`（不限）；**`SYSTEMATIC`：必填且 > 0，用户未给时向用户确认** | "日预算1000元" → `100000` |
| `total_budget` | integer | 否 | 总消耗限额（分，0 或 5000~20000000000）。用于限制广告整个生命周期的总花费上限。`0` 表示不限制；如需限制则须 > 5000 且 < 20000000000。用户未提及 → 不传；用户提及"总预算X元"/"总消耗限额X元" → 传 `X*100` | "总预算5000元" → `500000` |
| `cost_constraint_scene` | enum | 否 | **仅 `SYSTEMATIC` 可用**。传 `COST_CONSTRAINT_SCENE_OPEN` 开启。与下两字段联动（按 ROI/非 ROI 二选一） | 用户说"成本上限"/"控制成本" |
| `custom_cost_cap` | integer | 否 | **非 ROI 广告**的成本上限（分，0 < 值 ≤ 2,000,000）。需先开启 `cost_constraint_scene`。⛔ ROI 广告不能传此字段 | "成本上限50元" → `5000` |
| `custom_cost_roi_cap` | float | 否 | **ROI 广告**的期望 ROI（> 0）。需先开启 `cost_constraint_scene`。⛔ 非 ROI 广告不能传此字段 | "成本ROI 1.5" → `1.5` |
| `user_action_sets` | array | 否 | 用户行为数据源 | `user_action_sets/get` |

### 4D. 深度转化优化

oCPM/oCPC 可选配置，**前置条件**：步骤 4B 的 `get-conversions.mjs` 返回中，选中的转化目标 `has_deep_conversion=true`。

| deep_conversion_type | 说明 |
|---------------------|------|
| 通过 `get-enum-options.mjs '{"fields":["deep_conversion_type"]}'` 查询 | 包含深度行为优化、深度价值优化等 |

**⚠️ 二选一规则**：深度/深度辅助出价一级扁平字段与 `deep_conversion_spec` 嵌套结构**互斥，不能同时传**：
**常规广告使用 `conversion_id`，因此直接传一级扁平字段即可**。

**一级扁平字段示例**（用户说"深度ROI 1.5"）：

```json
{
  "conversion_id": 12345,
  "deep_conversion_worth_rate": 1.5
}
```

> `deep_conversion_type` 取自 `get-conversions.mjs` 返回，根据类型选用对应的一级出价字段：
> - `DEEP_CONVERSION_WORTH` → `deep_conversion_worth_rate`（深度ROI出价 / 深度转化价值率）
> - `DEEP_CONVERSION_WORTH_ADVANCED` → `deep_conversion_worth_advanced_rate`（深度辅助ROI）
> - `DEEP_CONVERSION_BEHAVIOR` → `deep_conversion_behavior_bid`（深度OG出价）
> - `DEEP_CONVERSION_BEHAVIOR_ADVANCED` → `deep_conversion_behavior_advanced_bid`（深度辅助OG出价）
>
> ⛔ **不同 `deep_conversion_type` 的 conversion_id 不可互换**。例如 `DEEP_CONVERSION_WORTH` 对应的 conversion_id 和 `DEEP_CONVERSION_WORTH_ADVANCED` 对应的是不同的 conversion_id，必须根据脚本返回的 `deep_conversion_type` 精确选择。

**强约束**：
- `conversion_id` 只能来自：用户明确给出的 ID，或 `get-conversions.mjs` 返回
- **白名单例外**：用户在原始需求中已明确给出完整的 `conversion_id` 数值 ID，则直接使用
- CPC/CPM 出价不需要 `conversion_id`
- **`optimization_goal` 不需要传**，API 会根据 `conversion_id` 自动推导

**步骤 4 完成后你应该有**：`bid_mode`、`smart_bid_type`、`conversion_id`（oCPM/oCPC时）；`CUSTOM` 还有 `bid_amount`，`SYSTEMATIC` 还有 `daily_budget`。

---

## 步骤 5：配置定向 + 投放时间

> **前置**：用户意图中的定向需求
> **输出**：`targeting`、`begin_date`、`end_date`、`delivery_time_ranges`

### 5A. 定向配置

常规广告拥有**完整定向能力**，支持地域、年龄、性别、兴趣、行为、人群包等多维度定向。

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
- **其他枚举定向**（学历/联网方式/设备价格/婚恋状态等）：均通过 `get-enum-options.mjs 查询

> ⚠️ `get-targeting-lookup.mjs` **只支持 `type: "geo"` 和 `type: "device"` 两种查询**，不支持 age、gender 等。年龄和性别不需要编码查询，直接用结构化值。

**只有在以下情况才可跳过定向查询**：用户完全没有给任何地域或设备定向约束。

> ⚠️ **通投（不限定向）时仍需传 `targeting: {}`（空对象）**，不要省略该字段。

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
    {"id": 440000, "name": "广东省", "level": "province", `"city_level": 4}
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

**常规广告支持的完整定向维度**（以下字段均放在 `targeting: { ... }` 对象内，不要放到请求体顶层）：

| 定向维度 | `targeting` 内的字段 | 说明 | 获取方式 |
|----------|-----------------|------|----------|
| 地域 | `geo_location.regions` + `geo_location.location_types` | `regions` 是**纯整数数组**（如 `[440000]`），取地域查询返回的 `id` 值；`location_types` 常用 `LIVE_IN` | ✅ `get-targeting-lookup.mjs type:geo` + 枚举查询 `location_types` |
| 地域优选 | `geo_location.geo_location_auto_audience` | 是否使用地域优选（boolean）。`true`=开启，系统自动扩展相似地域；用户未提及不传 | ❌ 直接传 boolean |
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
| 游戏消费能力 | `game_consumption_level` | 枚举查询 | ❌ 查枚举后直接构造 |
| 自定义人群 | `custom_audience` | 人群包 ID 列表 | 用户提供 |
| 排除人群 | `excluded_custom_audience` | 排除的人群包 ID | 用户提供 |
| 排除已转化 | `excluded_converted_audience` | 见下方格式说明 | ❌ 查枚举后直接构造 |
| 微信广告行为 | `wechat_ad_behavior` | 见下方格式说明 | ❌ 查枚举后直接构造 |

**⛔ 所有枚举值禁止凭记忆猜测，必须通过 `get-enum-options.mjs` 查询确认**：

```bash
# 查询单个/多个字段的枚举
node scripts/get-enum-options.mjs '{"fields":["education","device_price","excluded_dimension"]}'

# 按分类查询所有枚举
node scripts/get-enum-options.mjs '{"category":"targeting"}'    # 定向相关
node scripts/get-enum-options.mjs '{"category":"scene_spec"}'   # 场景定向
node scripts/get-enum-options.mjs '{"category":"bid"}'          # 出价相关
node scripts/get-enum-options.mjs '{"category":"conversion"}'   # 转化相关
node scripts/get-enum-options.mjs '{"category":"strategy"}'     # 探索策略
node scripts/get-enum-options.mjs '{"category":"switch"}'       # 开关类
```

可查询的枚举字段包括但不限于：`gender`、`education`、`user_os`、`excluded_os`、`network_type`、`device_price`、`marital_status`、`app_install_status`、`location_types`、`excluded_dimension`、`excluded_day`、`wechat_ad_behavior_actions`、`wechat_ad_behavior_excluded_actions`、`bid_mode`、`smart_bid_type`、`deep_conversion_type`、`deep_conversion_goal`、`exploration_strategy`、`search_expand_targeting_switch`、`search_expansion_switch`、`cost_constraint_scene`、`configured_status`、`ecom_pkam_switch`、`smart_coupon_mode`、`live_recommend_strategy_enabled`、`dynamic_ad_type`、`short_play_pay_type`、`smart_targeting_mode`、`adx_realtime_type`、`game_consumption_level`、`conversion_behavior_list` 等。

**`excluded_converted_audience` 格式**（⚠️ 仅在用户明确提到"排除已转化"时才添加，禁止自行添加）：
```json
{
  "excluded_dimension": "<通过 get-enum-options.mjs 查 excluded_dimension>",
  "excluded_day": "<通过 get-enum-options.mjs 查 excluded_day>"
}
```

**`wechat_ad_behavior` 格式**（⚠️ 仅在用户明确提到微信广告行为排除时才添加，禁止自行添加）：

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
- **`targeting` 是必填字段**：即使用户没有明确表达任何定向需求，也必须传 `targeting: {}`（空对象），不能省略该字段
- **`targeting` 及其子结构只传上方表格中列出的字段和子字段**，不要自行推测或类推添加文档中未出现的字段

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

无定向需求（通投）时传空对象：`"targeting": {}`

### 5B. 投放时间与状态

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `begin_date` | string | **是** | 开始日期，格式 `YYYY-MM-DD` |
| `end_date` | string | **是** | 结束日期，格式 `YYYY-MM-DD`；未指定传 `""`（长期投放） |
| `first_day_begin_time` | string | 否 | 首日开始投放时间，格式 `HH:ii:ss`（如 `"10:00:00"`）|
| `delivery_time_ranges` | string[] | **是** | 投放时段数组 |
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
- "排除周三下午" → 列出除周三下午外的所有时段，这时候agent需要列出其他有效的时段


**步骤 5 完成后你应该有**：`targeting`（如需）、`begin_date`、`end_date`、`delivery_time_ranges`。

---

## 步骤 6：组装请求体 → 创建广告组

> **前置**：步骤 1-5 的所有输出
> **动作**：按检查清单组装完整请求体，调用 `create-adgroup.mjs`

### 6A. 站点与版位

| 模式 | 字段设置 |
|------|---------|
| **自动版位**（推荐） | `automatic_site_enabled: true`，不传 `site_set` |
| **手动版位** | `automatic_site_enabled: false` + `site_set: [...]` |
| **自动版位 + 优先版位** | `automatic_site_enabled: true` + `priority_site_set: [...]`，**不传 `site_set`** |

> ⚠️ **`priority_site_set`（优先版位集合）**：当 `automatic_site_enabled: true` 且用户同时指定了"优先投放某些版位"时使用。填入用户指定的版位枚举数组（参考步骤 3B 枚举表），系统会在自动版位的基础上优先在这些版位投放。

### 6B. 常规广告特有说明

- **不传** `smart_delivery_platform` — 这是常规广告，不是智投
- **不传** `optimization_goal` — API 会根据 `conversion_id` 自动推导，无需传此字段
- **可传** `exploration_strategy` — 版位探索策略，枚举值通过 `get-enum-options.mjs '{"fields":["exploration_strategy"]}'` 查询

### 6C. 创意控制字段

创意通过 `dynamic_creatives/add` 接口单独创建，adgroup 级别可传以下控制字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `auto_derived_creative_enabled` | boolean | 创意增强 MAX 开关，推荐 `true` |
| `auto_derived_creative_preference` | struct | 创意增强 MAX 偏好设置，`auto_derived_creative_enabled` 为 `true` 时可传，子字段 `auto_derived_creative_method_type_list` 为 `AutoDerivedCreativeMethodType` 枚举数组，脚本自动匹配 |
| `auto_derived_landing_page_switch` | boolean | 是否开启自动衍生落地页开关 |

### 6D. 创建前自检（Pre-flight Check，⛔ 必须在调用 create-adgroup.mjs 前完成）

在组装完请求体后、真正调用创建接口前，逐项核对以下内容：
- **用户需求一致性**：用户明确给出的每个条件（定向、出价、预算、三元组、商品等）是否都被**原样保留**在请求体中，未被丢弃、修改或替换
- **字段来源可追溯**：四元组、转化目标、营销载体等关键字段是否来自**实际脚本查询结果**（而非猜测或编造）
- **编码已确认**：定向条件中的地域编码、设备 ID 等是否经过**查询脚本确认**
- **金额单位正确**：所有金额字段是否已转换为**分**

如有任何字段与用户原始需求不一致，必须**停止并说明差异原因**，等待用户确认后才能继续。

**字段检查清单**：

| # | 检查项 | 要点 |
|---|--------|------|
| 1 | `account_id` | 广告主账号ID |
| 2 | `adgroup_name` | 用户提供的原文名称，不要编造 |
| 3 | 四元组 | `marketing_goal`、`marketing_sub_goal`、`marketing_target_type`、`marketing_carrier_type` — **统一使用字符串枚举 key**，`create-adgroup.mjs` 脚本内部自动转换。**默认全部从步骤 1 的脚本返回中选出** |
| 4 | 资产+载体（⚠️ **直接透传 `flat_params`，脚本自动组装**） | 将 `flat_params` 中的字段（`asset_id`、`carrier_id`、`catalog_id`、`asset_sub_id`、`sub_carrier_id` 等）直接传入即可。**脚本根据 `marketing_target_type` 自动组装 `marketing_asset_outer_spec` 或 `marketing_asset_id`，根据 `marketing_carrier_type` 自动组装 `marketing_carrier_detail`。** ⛔ `carrier_id` ≠ `asset_id`，两者来源不同，脚本会校验并拒绝相同值。**⛔ 无 `flat_params`（步骤 2 / 1A 均未成功）→ 必须回步骤 2 补跑 `get-assets.mjs`，禁止直接调用本脚本。** |
| 5 | 资产+载体（旧方式，仍兼容） | 也可直接传 `marketing_asset_outer_spec` / `marketing_asset_id` / `marketing_carrier_detail`，脚本原样透传。但**推荐使用上方扁平 ID 方式以避免组装错误** |
| 6 | `bid_mode` | CPC / CPM / oCPM / oCPC |
| 7 | `bid_amount` | `CUSTOM`：必填且 > 0，单位分；**`SYSTEMATIC`（最大转化）：不传** |
| 8 | `optimization_goal` | **不需要传**，API 根据 `conversion_id` 自动推导 |
| 9 | `conversion_id` | 仅当步骤 4 返回真实值或用户明确给出时才传；**不要填 `0`** |
| 10 | `begin_date` / `end_date` | 未指定 end_date 传 `""` |
| 11 | `delivery_time_ranges` | 投放时段数组，每条格式 `"<Weekday> <HH:MM>~<HH:MM>"`，如 `["Monday 09:00~18:00", "Tuesday 09:00~18:00"]`；传 `["all"]` 表示全时段投放。支持 Monday-Sunday  |
| 12 | `automatic_site_enabled` / `site_set` | 自动版位 = `true` 不传 site_set；手动 = `false` + site_set 数组，枚举值只用步骤 3B 表格中的 key，不要自行构造。**搜索场景必须用 `SITE_SET_SEARCH_SCENE`，严禁用 `SITE_SET_SEARCH`** |
| 13 | `targeting` 来源 | 只要用户给了任何定向约束，就必须来自步骤 5 查询或明确特例；不要用粗粒度占位值代替 |
| 14 | `scene_spec` | 版位定投场景（步骤 3D），用户提到定投/屏蔽特定流量场景时按 3D 表格构造；**用户未提及 → 不传**。枚举类子字段必须通过 `get-enum-options.mjs` 查询，ID 类子字段直接传用户给的 ID |
| 15 | `auto_acquisition_enabled` / `auto_acquisition_budget` | 用户说"开启一键起量"时传 `true` + 预算（单位分）；未提及不传。⛔ **`SYSTEMATIC`（最大转化/自动出价）时不可使用** |
| 16 | `search_expansion_switch` | **搜索扩量**开关（⚠️ 不是搜索定向拓展），枚举通过 `get-enum-options.mjs '{"fields":["search_expansion_switch"]}'` 查询；未提及不传 |
| 17 | `search_expand_targeting_switch` | **搜索定向拓展**开关（⚠️ 不是搜索扩量），**前置条件：仅当 `search_expansion_switch` = `SEARCH_EXPANSION_SWITCH_OPEN`（即搜索扩量已开启）时才可打开**；枚举通过 `get-enum-options.mjs '{"fields":["search_expand_targeting_switch"]}'` 查询；未提及不传 |
| 18 | `daily_budget` | `CUSTOM`：用户未提及传 `0`（不限）；**`SYSTEMATIC`：必填且 > 0**；不要省略此字段 |
| 19 | `wechat_ad_behavior` | 用户提到微信广告行为排除时，通过 `get-enum-options.mjs` 查询枚举后构造；**用户未提及 → 不传** |
| 20 | 定向枚举值 | `education`、`network_type`、`device_price`、`excluded_dimension`、`excluded_day` 等定向枚举**必须通过 `get-enum-options.mjs` 查询确认，禁止凭记忆猜测** |
| 21 | `priority_site_set` | **若传了 `exploration_strategy: STEADY_EXPLORATION`，则 `priority_site_set` 为必填数组** |
| 22 | `feedback_id` | 监测链接组 ID（integer，非必填）。在 DataNexus 中维护，用户给了就直接传数字 ID；**用户未提及 → 不传**。⚠️ ADX 程序化广告不可填写 |
| 23 | `cost_constraint_scene` 等 | **仅 `SYSTEMATIC`（最大转化）可用**。非 ROI 广告用 `custom_cost_cap`（分），ROI 广告用 `custom_cost_roi_cap`（float），两者互斥不能同时传。用户未提及不传 |
| 24 | `configured_status` | 广告初始状态，脚本默认 `AD_STATUS_SUSPEND`（暂停）。用户明确要求上线/启用时传 `AD_STATUS_NORMAL`。枚举通过 `get-enum-options.mjs '{"fields":["configured_status"]}'` 查询 |
| 25 | `ecom_pkam_switch` | 一方人群跑量加强开关（电商场景），枚举通过 `get-enum-options.mjs '{"fields":["ecom_pkam_switch"]}'` 查询。`ECOM_PKAM_SWITCH_OPEN`=开启，`ECOM_PKAM_SWITCH_CLOSE`=关闭。用户未提及不传 |
| 26 | `smart_coupon_mode` | 小店智券开关（微信小店电商场景），枚举通过 `get-enum-options.mjs '{"fields":["smart_coupon_mode"]}'` 查询。`SWITCH_STATUS_ON`=开启，`SWITCH_STATUS_OFF`=关闭。用户未提及不传 |
| 27 | `smart_targeting_mode` | 智能定向模式。`SMART_TARGETING_MANUAL`（手动定向）=不使用/关闭智能定向，`SMART_TARGETING_AUTO`（智能定向）=开启/使用智能定向。枚举通过 `get-enum-options.mjs '{"fields":["smart_targeting_mode"]}'` 查询。用户未提及不传 |
| 28 | `dynamic_ad_type` | 动态广告类型（DPA/DCA 场景），枚举通过 `get-enum-options.mjs '{"fields":["dynamic_ad_type"]}'` 查询。如 `DYNAMIC_AD_TYPE_DYNAMIC_PRODUCT`=动态商品广告，`DYNAMIC_AD_TYPE_DYNAMIC_CONTENT`=动态内容广告。用户未提及不传 |
| 29 | `short_play_pay_type` | 短剧付费类型（短剧推广场景），枚举通过 `get-enum-options.mjs '{"fields":["short_play_pay_type"]}'` 查询。`SHORT_PLAY_PAY_TYPE_FREE_PLAY`=免费剧，`SHORT_PLAY_PAY_TYPE_CHARGE_PLAY`=收费剧。用户未提及不传 |
| 30 | `rta_id` / `rta_target_id` | RTA 投放：`rta_id`=RTA 客户 ID（integer），`rta_target_id`=RTA 策略 ID（string）。用户给了就直接传；未提及不传 |
| 31 | `dsp_id` | ADX 程序化广告 DSP ID（integer）。用户给了就直接传；未提及不传 |
| 32 | `adx_realtime_type` | ADX 素材实时回复类型，枚举通过 `get-enum-options.mjs '{"fields":["adx_realtime_type"]}'` 查询。如 `ADX_REALTIME_TYPE_NO_AUDIT`=免审广告。仅 ADX 场景使用；用户未提及不传 |
| 33 | `sell_strategy_id` | 售卖策略 ID（integer）。用户给了就直接传；未提及不传 |
| 34 | `live_recommend_strategy_enabled` | 直播种草人群探索开关（直播电商场景），枚举通过 `get-enum-options.mjs '{"fields":["live_recommend_strategy_enabled"]}'` 查询。用户未提及不传 |
| 35 | `poi_list` | 门店 ID 列表（string[]，本地生活场景）。用户给了就直接传；未提及不传 |
| 36 | `enable_steady_exploration` | 是否稳步探索更多版位（boolean）。用户提到"稳步探索"时传 `true`；未提及不传 |
| 37 | `mpa_spec` | 动态商品广告属性（DPA），**当 `dynamic_ad_type` = `DYNAMIC_AD_TYPE_DYNAMIC_PRODUCT` 时必填**。ADX 不可用。结构：`{"recommend_method_ids": [<推荐方式ID>], "product_catalog_id": "<商品库ID>", "product_series_id": "<商品集合ID>"}`。其中 `recommend_method_ids`（integer[]，1~16个）必填，`product_catalog_id`（string）和 `product_series_id`（string）选填。用户未提及 DPA 不传 |
| 38 | `dca_spec` | 动态内容广告属性（DCA），**当 `dynamic_ad_type` = `DYNAMIC_AD_TYPE_DYNAMIC_CONTENT` 时可设置**。结构：`{"recommend_method_ids": [95], "set_id": "<素材集合ID>"}`。`recommend_method_ids`（integer[]，目前仅支持 RTA优选=`95`，需申请权限），`set_id`（string，素材集合 ID）。用户未提及 DCA 不传 |
| 39 | `aoi_optimization_strategy` | 高价值范围探索（灰度功能，需联系客户运营开通）。ADX 不可用。结构：`{"aoi_optimization_strategy_enabled": true, "aoi_id_list": [<AOI区域ID>]}`。`aoi_optimization_strategy_enabled`（boolean）必填，`aoi_id_list`（integer[]，最多1000个）选填。用户未提及不传 |
| 40 | `additional_product_spec` | 附加商品属性（电商多商品场景）。ADX 不可用。结构：`{"product_catalog_id": "<商品库ID>", "product_outer_id": "<商品ID>"}`。两个字段均为 string 且必填。用户未提及不传 |
| 41 | `total_budget` | 总消耗限额（分，0=不限，限制时须 > 5000 且 < 20000000000），**用户未提及 → 不传** |
| 42 | `material_package_id`（素材标签） | 用户提及素材标签/素材包时按 [references/material-labels.md](references/material-labels.md) 取值；未提及 → **不传**。ADX 不可填写 |
> ⚠️ **定向字段禁止自行添加**：`excluded_converted_audience`、`wechat_ad_behavior` 等定向字段，**只有用户明确要求时才加入 targeting**。用户没提到的定向维度一律不传。


### 6E. 执行创建

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
| 营销目的相关 | `marketing_goal` | **从步骤 1 脚本返回中选取**，禁止猜测 |
| "CPC出价"/"按点击" | `bid_mode` | → `BID_MODE_CPC`（不需要步骤 4B/5） |
| "CPM"/"千次展示" | `bid_mode` | → `BID_MODE_CPM`（不需要步骤 4B/5） |
| "oCPM"/"优化千展" | `bid_mode` | → `BID_MODE_OCPM`（需要步骤 4B/5） |
| "oCPC"/"优化点击" | `bid_mode` | → `BID_MODE_OCPC`（需要步骤 4B/5） |
| "出价5元" | `bid_amount` | → `500`（×100，分） |
| "日预算1000元" | `daily_budget` | → `100000`（×100，分） |
| 未提及日预算 | `daily_budget` | → `0`（不限日预算，**必须传**） |
| "总预算5000元"/"总消耗限额5000元" | `total_budget` | → `500000`（×100，分）；`0`=不限，限制时须 > 5000 且 < 20000000000 |
| "深度ROI 1.5"/"深度转化价值率X" | `deep_conversion_worth_rate` | → `1.5`，选 `deep_conversion_type=DEEP_CONVERSION_WORTH` 的转化ID（⚠️ 不是"深度辅助优化"那个） |
| "深度辅助ROI X" | `deep_conversion_worth_advanced_rate` | → 选 `deep_conversion_type=DEEP_CONVERSION_WORTH_ADVANCED` 的转化ID（名称含"深度辅助优化"） |
| "深度出价X元"/"深度行为出价"/"深度OG出价" | `deep_conversion_behavior_bid` | → 金额×100 转分，选 `deep_conversion_type=DEEP_CONVERSION_BEHAVIOR` 的转化ID |
| "深度辅助出价X元"/"深度辅助OG出价" | `deep_conversion_behavior_advanced_bid` | → 金额×100 转分，选 `deep_conversion_type=DEEP_CONVERSION_BEHAVIOR_ADVANCED` 的转化ID |
| "投朋友圈" | `site_set` | → `["SITE_SET_MOMENTS"]`，手动版位 |
| "PCAD"/"腾讯平台与内容媒体" | `site_set` | → `["SITE_SET_KANDIAN", "SITE_SET_QQ_MUSIC_GAME", "SITE_SET_TENCENT_NEWS", "SITE_SET_TENCENT_VIDEO"]`（按步骤 3B 一级分类展开）|
| "自动版位" | `automatic_site_enabled` | → `true` |
| "全国投放"/"不限地域" | `targeting.geo_location` | 不传 `geo_location` |
| "排除X省"/"不投X省"/"除X外全国" | `targeting.geo_location` | → 先调 `get-geo-exclude.mjs` 获取剩余省份 keyword，再调 `get-targeting-lookup.mjs` 查编码，组成 `regions` 数组 |
| 指定省市 | `targeting.geo_location` | → `get-targeting-lookup.mjs` 查编码，取返回的 `id` 组成纯整数数组放入 `regions`（如 `[440000]`），`location_types: ["LIVE_IN"]` |
| 指定性别 | `targeting.gender` | → 通过 `get-enum-options.mjs` 查 `gender` 枚举后构造 |
| 指定年龄 | `targeting.age` | → `[{"min":25,"max":29}, {"min":30,"max":39}]`，**`min`/`max` 均为闭区间（包含边界值）**，即"25~29岁"→ `{"min":25,"max":29}`，不是 `{"min":25,"max":30}`。按用户给出的区间直接构造，如果用户说了多个不同年龄段，**不要合并** |
| 指定设备 | `targeting.device_brand_model` | → `get-targeting-lookup.mjs` 搜数字ID |
| 指定操作系统 | `targeting.user_os` | 全版本：`["ANDROID"]` / `["IOS"]`；指定版本范围：如"Android 10及以上"→ `["ANDROID_VERSION_10", ..., "ANDROID_VERSION_15"]`，"iOS 14及以上"→ `["IOS_VERSION_14", ..., "IOS_VERSION_18"]` |
| 排除操作系统 | `targeting.excluded_os` | 排除特定系统版本，如排除鸿蒙纯净版 → `["ANDROID_PURE_MODE"]`，排除低版本Android → `["ANDROID_VERSION_1", "ANDROID_VERSION_2", ..., "ANDROID_VERSION_4"]` |
| 指定联网方式 | `targeting.network_type` | 如"仅WiFi"→ `["WIFI"]`，"4G及以上"→ `["NET_4G", "NET_5G", "WIFI"]` |
| 排除已转化 | `targeting.excluded_converted_audience` | → 按定向规则填写 |
| 广告名称 | `adgroup_name` | 按用户原文 |
| "开启一键起量" | `auto_acquisition_enabled` | → `true`；同时需要起量预算 |
| "起量预算200元" | `auto_acquisition_budget` | → `20000`（×100，分） |
| "搜索场景" | `site_set` | → 包含 `SITE_SET_SEARCH_SCENE`
| "开启/关闭搜索定向拓展" | `search_expand_targeting_switch` | → `SEARCH_EXPAND_TARGETING_SWITCH_OPEN` / `CLOSE`（⚠️ 不是搜索扩量） |
| "开启/关闭搜索扩量" | `search_expansion_switch` | → `SEARCH_EXPANSION_SWITCH_OPEN` / `CLOSE`（⚠️ 不是搜索定向拓展） |
| "关闭自动版位" | `automatic_site_enabled` | → `false` + 手动指定 `site_set` 数组 |
| "开启自动版位，优先投X/Y/Z" | `automatic_site_enabled` + `priority_site_set` | → `automatic_site_enabled: true` + `priority_site_set: ["SITE_SET_X", ...]`；**不传 `site_set`** |
| 排除小游戏注册用户（N天未活跃） | `targeting.wechat_ad_behavior` | → `{"excluded_actions": ["MINI_GAME_WECHAT_REGISTERED"], "mini_game_wechat_registered_activity": "THIRTY_DAYS_NO_ACTIVE"}` |
| "搜索关键词：游戏下载" | `search_bidwords` | → 构造 search_bidword 数组，详见 7F 说明 |
| "稳步探索版位" | `exploration_strategy` | → `STEADY_EXPLORATION`，**⚠️ 必须同时传 `priority_site_set`**，否则创建失败 |
| "优先投朋友圈和视频号" | `priority_site_set` | → `["SITE_SET_WECHAT_MOMENTS", "SITE_SET_CHANNELS"]`（仅 `STEADY_EXPLORATION` 时）；若用户未指定具体优先版位，用 `site_set` 全量值 |
| "监测链接组ID 12345"/"feedback_id 12345" | `feedback_id` | → `12345`（直接使用用户给出的数字 ID，integer 类型） |
| "成本上限X元" | `cost_constraint_scene` + `custom_cost_cap` | → **仅 `SYSTEMATIC`**。`COST_CONSTRAINT_SCENE_OPEN` + `custom_cost_cap: X*100`（分）。⛔ ROI 广告改用 `custom_cost_roi_cap` |
| "成本ROI上限 X" | `cost_constraint_scene` + `custom_cost_roi_cap` | → **仅 `SYSTEMATIC` + ROI 广告**。`COST_CONSTRAINT_SCENE_OPEN` + `custom_cost_roi_cap: X` |
| "稳定投放"/"均匀投放" | `smart_bid_type` | → `SMART_BID_TYPE_CUSTOM`（手动出价） |
| "最大转化"/"优先跑量"/"自动出价"/"系统出价" | `smart_bid_type` | → `SMART_BID_TYPE_SYSTEMATIC`（最大转化），`daily_budget` 必填且 > 0，不传 `bid_amount` |
| "开启/关闭一方人群跑量加强"/"开启/关闭PKAM" | `ecom_pkam_switch` | → `ECOM_PKAM_SWITCH_OPEN` / `ECOM_PKAM_SWITCH_CLOSE`，枚举通过 `get-enum-options.mjs '{"fields":["ecom_pkam_switch"]}'` 查询 |
| "开启/关闭小店智券"/"开启/关闭智能优惠券" | `smart_coupon_mode` | → `SWITCH_STATUS_ON` / `SWITCH_STATUS_OFF`，枚举通过 `get-enum-options.mjs '{"fields":["smart_coupon_mode"]}'` 查询 |
| "手动定向"/"不使用智能定向"/"不开启智能定向"/"关闭智能定向" | `smart_targeting_mode` | → `SMART_TARGETING_MANUAL`，枚举通过 `get-enum-options.mjs '{"fields":["smart_targeting_mode"]}'` 查询 |
| "智能定向"/"使用智能定向"/"开启智能定向" | `smart_targeting_mode` | → `SMART_TARGETING_AUTO`，枚举通过 `get-enum-options.mjs '{"fields":["smart_targeting_mode"]}'` 查询 |
| "动态商品广告"/"DPA" | `dynamic_ad_type` | → `DYNAMIC_AD_TYPE_DYNAMIC_PRODUCT`，枚举通过 `get-enum-options.mjs '{"fields":["dynamic_ad_type"]}'` 查询 |
| "动态内容广告"/"DCA" | `dynamic_ad_type` | → `DYNAMIC_AD_TYPE_DYNAMIC_CONTENT` |
| "短剧免费"/"免费剧" | `short_play_pay_type` | → `SHORT_PLAY_PAY_TYPE_FREE_PLAY`，枚举通过 `get-enum-options.mjs '{"fields":["short_play_pay_type"]}'` 查询 |
| "短剧收费"/"收费剧"/"付费剧" | `short_play_pay_type` | → `SHORT_PLAY_PAY_TYPE_CHARGE_PLAY` |
| "RTA客户ID 12345"/"rta_id 12345" | `rta_id` | → `12345`（直接传 integer） |
| "RTA策略ID abc"/"rta_target_id abc" | `rta_target_id` | → `"abc"`（直接传 string） |
| "DSP ID 12345"/"dsp_id 12345" | `dsp_id` | → `12345`（ADX 程序化广告场景，直接传 integer） |
| "ADX免审"/"免审广告" | `adx_realtime_type` | → `ADX_REALTIME_TYPE_NO_AUDIT`，枚举通过 `get-enum-options.mjs '{"fields":["adx_realtime_type"]}'` 查询 |
| "售卖策略ID 12345" | `sell_strategy_id` | → `12345`（直接传 integer） |
| "开启直播种草"/"直播种草人群探索" | `live_recommend_strategy_enabled` | → `true`（boolean），枚举通过 `get-enum-options.mjs '{"fields":["live_recommend_strategy_enabled"]}'` 查询参考 |
| "门店ID xxx"/"poi_list" | `poi_list` | → `["xxx"]`（string 数组，本地生活场景直接传用户给出的门店 ID 列表） |
| "广告暂停创建"/"创建后暂停" | `configured_status` | → `AD_STATUS_SUSPEND`（当前已为默认值，无需额外传入） |
| "广告上线创建"/"创建后启用"/"创建后上线" | `configured_status` | → `AD_STATUS_NORMAL`，覆盖默认暂停行为 |
| "转化来源/自建转化/平台预置" | `create_source_type` | → `CreateSourceType`，枚举通过 `get-enum-options.mjs '{"fields":["create_source_type"]}'` 查询 |
| "素材包/素材标签 ID 1234" | `material_package_id` | 按 [references/material-labels.md](references/material-labels.md) 取值；未提及不传。⛔ ADX 不可填写 |
---

## ⚠️ 四元组枚举值使用规则（防幻觉）

> 四元组的全部10个字段（营销内容：`marketing_goal`、`marketing_sub_goal`、`marketing_carrier_type`、`marketing_target_type`；转化/优化目标：`optimization_goal`、`deep_behavior_optimization_goal`、`deep_behavior_advanced_goal`、`deep_worth_optimization_goal`、`deep_worth_advanced_goal`、`forward_link_assist`）**必须从 `get-rules.mjs` 返回的 `combinations` 中选取，禁止自行编造或语义改写**。
> 例如 `MARKETING_CARRIER_TYPE_MINI_GAME`、`MARKETING_GOAL_APP_MONETIZATION`、`MARKETING_CARRIER_TYPE_APP` 这类"看起来合理但 API 不存在"的值，会直接导致报错。
> `marketing_sub_goal` 只能原样复用 `get-rules.mjs` 返回的 key，不能因为用户说了"注册"/"下载"就改写成自造枚举。

### marketing_goal 意图速查（值域稳定，共 5 个）
|---------------|----------|
| 用户增长（APP下载/拉新/注册/激活/付费/游戏推广 A| `MARKETING_GOAL_USER_GROWTH` |
| 商品销售 电商/卖货/成交/GMV/ROI | `MARKETING_GOAL_PRODUCT_SALES` |
| 线索留资 表单/留资/线索收集 | `MARKETING_GOAL_LEAD_RETENTION` |
| 品牌推广 品牌/曝光 | `MARKETING_GOAL_BRAND_PROMOTION` |
| 涨粉互动 涨粉/加关注 | `MARKETING_GOAL_INCREASE_FANS_INTERACTION` |

### marketing_target_type 易混淆速查（60+ 枚举，仅列易错项）

> 完整值域以 `get-rules.mjs` 返回为准，下表仅帮助区分易混淆项。

| 枚举 key | 含义 | ⚠️ 易混淆提示 |
|----------|------|-----------|
| `MARKETING_TARGET_TYPE_WECHAT_WORK` | 企业微信 | 仅"推广企微"时选；"扫码加微信"不是企微 |
| `MARKETING_TARGET_TYPE_STORE` | 平台店铺 | ≠ 个人店铺，≠ 本地门店，≠ 微信小店 |
| `MARKETING_TARGET_TYPE_LOCAL_STORE` | 本地门店 | ≠ 平台店铺 |
| `MARKETING_TARGET_TYPE_CONSUMER_PRODUCT` | 商品（商品库） | 用户说"商品库"时选此项，≠ 微信小店商品，≠ `PRODUCT` |
| `MARKETING_TARGET_TYPE_WECHAT_STORE_PRODUCT` | 微信小店商品 | 推广**单个商品**；≠ `WECHAT_STORE`（店铺级） |
| `MARKETING_TARGET_TYPE_WECHAT_STORE` | 微信小店店铺 | 推广**整个店铺**；≠ `WECHAT_STORE_PRODUCT`，≠ `STORE` |
| `MARKETING_TARGET_TYPE_PRODUCT` | 教育产品 | ⚠️ 不是通用"商品"，通用商品用 `CONSUMER_PRODUCT` |
| `MARKETING_TARGET_TYPE_TRAFFIC` | 汽车商品 | ⚠️ 不是"流量" |
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
2. **严格按步骤 1→(1A)→2→3→4→5→6 顺序执行**；只有"显式证据白名单"或"出价方式快速路径"允许跳过对应查询；步骤 1A 在有资产线索且四元组未唯一确定时执行
3. **CPC/CPM 出价时可跳过步骤 3 的版位查询（自动版位场景）、步骤 4B（转化目标查询）**——参见执行协议中的"出价方式决定的步骤执行路径"表
4. **用户明确给出的结构化字段可直接复用，但只豁免该字段对应的查询，不会自动豁免其他步骤**
5. **禁止把自然语言意图当作 API 返回值使用**；中文描述只能用于筛选，不等于枚举值或 ID
6. **辅助查询失败时可以继续完成最终 API，但只能使用已确认字段**；不能为了凑齐请求体编造四元组、营销载体 ID、定向枚举
7. **空字符串和 `0` 不是默认值**：它们通常表示"你没有拿到真实结果"，不要拿来伪装步骤已完成
8. **只要用户给了定向条件，就不要省略步骤 5，也不要用更宽泛的值替代精确编码**
9. **金额单位是分**（10000分 = 100元）
10. **统一使用字符串枚举 key**：四元组等字段始终传字符串 key（如 `"MARKETING_GOAL_USER_GROWTH"`），脚本内部负责转为 API 所需数值
11. **campaign_id 不需要** — v3.0 展示广告中 adgroup 直接属于 account
12. **广告名称唯一性** — 同一账号下广告名称必须唯一
13. 有报错请提供 `trace_id`

---
