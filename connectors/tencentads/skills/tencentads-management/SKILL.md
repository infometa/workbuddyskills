---
name: tencentads-management
description: 腾讯营销（原腾讯广告）管理 — 跨账户查询营销单元（原广告）/创意/素材等多层级数据及报表指标；查看营销单元完整配置（定向、出价、转化、版位等）与智能投放项目详情；获取创意列表及组件详情，单创意时自动解析组件并获取图片/视频预览 URL；管理关键词和否定词的增删改查；创建推广内容资产。
license: MIT
compatibility: any
metadata:
  author: Tencent Ads Delivery Team
  version: "0.5.8"
  icon: megaphone
  category: tencent-ads
---

# 腾讯广告管理（Tencent Ads Management）

> **前置依赖**：需安装 `tencentads-cli`（Node.js ≥ 20）。执行 `npm install -g tencentads-cli@latest` 安装或升级；版本过低时 `tencentads` 会给出提示。

腾讯广告的综合管理技能，提供以下核心能力：

1. **综合数据报表查询**（`query-report.mjs`）：支持跨账户查询广告/创意/组件/素材等多层级数据，同时返回属性字段和报表指标数据。
2. **广告详情查询**（`query-adgroups.mjs`）：获取广告的完整配置信息，包括定向设置、出价策略、转化规格、版位配置、投放时段等详细属性。
3. **智能投放项目详情查询**（`query-adgroups.mjs`）：获取智能投放项目的详细配置信息，支持按需指定返回字段。
4. **创意列表查询**（`query-creatives.mjs`）：获取创意的完整信息，包括创意组件引用、投放模式、创意类型等。当查询结果只有 1 条创意时，脚本自动解析组件详情并获取图片/视频预览 URL，一次调用即可返回完整的创意 + 组件 + 素材预览信息。
5. **操作日志查询**（`query-operation-logs.mjs`）：查询广告/创意对象的操作日志，返回每次操作（新建/修改）前后的字段变化详情，支持按日期范围、对象 id、操作动作等过滤，详见 [references/operation-log-list-get.md](references/operation-log-list-get.md)。
6. **关键词管理**（`bidword/add.mjs` / `bidword/update.mjs` / `bidword/delete.mjs` / `bidword/get.mjs`）：管理广告的关键词（竞价词），支持创建、更新、删除和查询操作。
7. **否定词管理**（`negativewords/add.mjs` / `negativewords/update.mjs` / `negativewords/get.mjs`）：管理广告的否定词，支持新增、更新和查询操作。
8. **推广内容资产管理**：创建推广内容资产（marketing_asset），支持金融、教育、房地产、旅游、餐饮等多种资产类型。详细说明见 [references/marketing-asset.md](references/marketing-asset.md)，**执行前务必先读取该文档**。

> **重要提示**: 本技能基于腾讯广告营销 API（api.e.qq.com）API。以本文档为准，字段名称、参数结构可能与开放 API 不同，请勿混淆。

所有 API 调用均通过本技能的**专用脚本**执行，脚本负责参数构建与数据处理。Agent 只需关注：从用户意图中提取查询参数，并解读返回的数据。

### 脚本选择指南

| 用户意图 | 推荐脚本 | 说明 |
|---------|---------|------|
| 查看广告/创意效果数据（**明确提到**消耗、曝光、点击、转化、ROI 等指标） | `query-report.mjs` | 返回广告/创意报表指标 |
| 查看广告分时/按天趋势 | `query-report.mjs` | 按时间维度聚合报表数据 |
| 查看账户汇总数据 | `query-report.mjs` | 全账户维度汇总 |
| 查看分地域/分城市/分年龄/分性别投放数据 | `query-report.mjs` | 使用对应 `level`（如 `REGION`/`CITY`/`AGE`/`GENDER`），脚本自动推导 `group_by` 和过滤条件 |
| **笼统说"查询广告数据"/"看下广告"等，未明确提到指标** | **`query-adgroups.mjs`** | **默认视为查看广告实体，而非报表** |
| **笼统说"查询创意数据"/"看下创意"等，未明确提到指标** | **`query-creatives.mjs`** | **默认视为查看创意实体，而非报表** |
| 查看广告实体（定向、出价、转化、版位等） | `query-adgroups.mjs` | 返回广告完整配置信息 |
| 查看广告实体-定向明细 | `query-adgroups.mjs` | 包含地域、年龄、性别等定向 |
| 查看已删除的广告 | `query-adgroups.mjs` | 支持 is_deleted 过滤 |
| 根据广告名称搜索广告详情 | `query-adgroups.mjs` | 支持 adgroup_name 过滤 |
| 查看智能投放项目详情 | `query-adgroups.mjs` | 返回智投项目完整配置，支持按需指定 fields |
| 查看智投项目能力配置（如 AIGC、自动创意等） | `query-adgroups.mjs` | 包含 project_ability_list、smart_delivery_aigc_option 等字段 |
| 查看广告/创意的操作日志（新建/修改记录、字段变更前后对比） | `query-operation-logs.mjs` | 必传 `account_id`、`operation_object_type`（`ADGROUP`/`DYNAMIC_CREATIVE`/`JOINT_BUDGET`）、`start_date`、`end_date`；可选 `object_id` 指定具体广告/创意 id |
| 创建关键词/竞价词 | `bidword/add.mjs` | 为广告添加关键词 |
| 更新关键词/竞价词 | `bidword/update.mjs` | 修改关键词的匹配方式、出价等 |
| 删除关键词/竞价词 | `bidword/delete.mjs` | 删除广告下的关键词 |
| 查询关键词/竞价词 | `bidword/get.mjs` | 查询广告下的关键词列表 |
| 新增否定词 | `negativewords/add.mjs` | 为广告添加否定词 |
| 更新否定词 | `negativewords/update.mjs` | 更新广告的否定词等 |
| 查询否定词 | `negativewords/get.mjs` | 查询广告下的否定词列表 |

> **脚本调用格式统一**：
> - **Bash / Zsh / Git Bash**：`node scripts/<脚本名>.mjs '<JSON 参数>'`（直接传 JSON 字符串）
> - **Windows PowerShell**：`node scripts/<脚本名>.mjs --base64 <Base64字符串>`（**必须使用 --base64**）
>
> 执行脚本时先进入本 skill 根目录，再按相对 `scripts/` 路径调用。

### ⚠️ 跨平台 JSON 参数传递规则（经实测验证）

#### Bash / Zsh / Git Bash

直接传 JSON 字符串，单引号包裹即可：
```bash
node scripts/query-report.mjs '{"account_ids":["73412663"],"date_range":{"start_date":"2026-04-13","end_date":"2026-04-13"},"level":"ADGROUP"}'
```

#### Windows PowerShell

PowerShell 的引号解析规则复杂，直接传 JSON 字符串会导致双引号被吞掉。**必须使用 `--base64` 方式**，通过 Here-String 构造 JSON 再编码为 Base64，彻底规避引号问题：
```powershell
$json = @'
{"account_ids":["73412663"],"date_range":{"start_date":"2026-04-13","end_date":"2026-04-13"},"level":"ADGROUP"}
'@
$base64 = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($json))
node scripts/query-report.mjs --base64 $base64
```

> **⚠️ Here-String 格式要求极其严格（违反则 PowerShell 直接报语法错误）：**
>
> 1. **`@'` 后面必须立即换行**，同一行不能跟任何字符（包括空格）
> 2. **`'@` 必须单独一行且顶格写**，前面不能有空格或缩进
> 3. JSON 内容从 `@'` 的**下一行**开始书写
>
> ```powershell
> # ❌ 错误：@' 后面直接跟了 JSON 内容
> $json = @'{"account_ids":["73412663"]}'@
>
> # ❌ 错误：'@ 前面有空格
> $json = @'
> {"account_ids":["73412663"]}
>   '@
>
> # ✅ 正确：@' 后立即换行，'@ 顶格独占一行
> $json = @'
> {"account_ids":["73412663"]}
> '@
> ```

```
⛔ SOP 决策流程（严格按顺序执行，不可跳步）：

步骤1                步骤2                步骤2.5                                                              步骤3
意图识别  ─────→    分流路由   ─────→  字段名确认(> **🚫🚫🚫 禁止猜测字段名！违反此规则 = 查询失败！**)   ─────→       执行查询
是否使用本SKILL      │
                     ├─ 路径A（报表/效果数据）─→ 字段名确认（见步骤2.5）─→ query-report.mjs → 结束
                     │
                     ├─ 路径B（项目/广告/创意详情）
                     │    │
                     │    └─ query-adgroups / query-creatives
                     │       （有时间范围时通过 filtering 中 created_time 筛选）
                     │
                     └─ 路径C（营销资产查询）─→ 见下方"营销资产查询（路径 C）"

创意查询分支：
  query-creatives.mjs 自动判断：
    │
    ├─ 查询结果只有 1 条创意（单个创意详情）
    │    → 自动执行完整解析流程：
    │      ├─ 1. 从 creative_components 提取 component_id
    │      ├─ 2. 批量拉取组件详情
    │      ├─ 3. 从组件中提取 image_id / video_id
    │      ├─ 4. 获取图片/视频预览 URL
    │      └─ 5. 内联到 _component_detail + _preview，一次返回完整创意+组件+素材预览
    │
    └─ 查询结果有多条创意（创意列表）
         → 只返回创意基本信息，不解析组件
```

---

<!-- script get-available-marketing-assets → scripts/get-available-marketing-assets.mjs (injected at build time) -->
<!-- script get-android-packages → scripts/get-android-packages.mjs (injected at build time) -->

## SOP 决策流程（高优先级，覆盖后文冲突）

> 若本节与下文表述冲突，以本节为准。

### 步骤1：意图识别 — 是否使用本 SKILL

用户意图必须命中以下**任一类别**，才进入本 SKILL 的处理流程：

| 类别 | 命中关键词 / 场景示例 |
|------|----------------------|
| **A. 报表/效果数据** | **必须明确提到指标关键词**：消耗、曝光、点击、转化、ROI、分时趋势、按天数据、账户汇总、效果对比、数据报表、投放效果 |
| **B. 实体列表/详情查询** | 智能投放项目（简称"项目"、"智投项目"）、竞价广告（又称"3.0广告"）、创意（又称"动态创意"、"新创意"）的列表查询、详情查看、配置查询、定向设置、组件内容 |
| **C. 营销资产查询** | 安卓应用包、安卓渠道包、推广产品、营销资产等资产信息查询 |

> ⚠️ **关键规则**：用户笼统说"查询广告数据"、"看下创意数据"等，**未明确提到指标关键词（消耗、曝光、点击等）**时，一律归入 **B 类（实体查询）**，而非 A 类（报表）。只有明确提到指标或趋势时才走报表。

❌ **不命中** → 不使用本 SKILL，交给其他技能处理。

### 步骤 1.5：确定实体类型 — `tencent_ads_type` 参数（所有脚本通用）

> **⚠️ 必须在调用任何脚本前确定 `tencent_ads_type`，该参数直接影响返回字段的命名。**
>
> **`tencent_ads_type` 是枚举类型，只允许以下三个值，传其他值脚本会报错退出：**

| 用户意图 | `tencent_ads_type` 枚举值 | 返回字段示例 |
|---------|-------------|-------------|
| 智能投放项目（"项目"、"智投项目"） | `"smart"` | `project_id`、`project_name`、`project.*` |
| 竞价广告（"竞价广告"、"3.0广告"、"非智投"） | `"standard"` | `adgroup_id`、`adgroup_name`、`adgroup.*` |
| 所有广告（"广告"、未明确说明、**默认**） | `"all"`（默认） | `adgroup_id`、`adgroup_name`、`adgroup.*`（保持原始字段名） |

**规则**：
- 用户提到"项目"、"智投项目"、"智能投放项目" → `tencent_ads_type: "smart"`
- 用户提到"竞价广告"、"3.0广告"、"非智投广告" → `tencent_ads_type: "standard"`
- 用户只说"广告"或未明确说明 → `tencent_ads_type: "all"`（**默认**，包含智投项目 + 竞价广告，不注入 `smart_delivery_platform` 过滤，不做字段重命名）
- **⚠️ 只允许传 `"smart"` / `"standard"` / `"all"` 三个枚举值之一**，传其他任何值（如 `"project"`、`"ad"` 等）脚本会直接报错
- `tencent_ads_type` 对所有脚本（`query-report.mjs`、`query-adgroups.mjs`、`query-creatives.mjs`）均适用

### 步骤2：分流路由 — 报表 or 详情

> ⚠️ **时间范围修饰对象判断（必须在分流前执行）**
>
> 用户说的时间范围修饰的是「报表数据」还是「广告实体」？
>
> | 用户说法 | 时间修饰对象 | 走向 |
> |---------|------------|------|
> | "最近一周的消耗" / "最近7天的效果" / "上周的报表" | 报表数据 | 路径 A |
> | "最近一周的广告" / "最近7天的项目" / "上周的创意" （**无效果指标词**） | 广告实体 | 路径 B（`filtering` 加 `created_time`） |
> | "最近一周内创建的广告" / "这周新建的项目" | 广告实体 | 路径 B（`filtering` 加 `created_time`） |
>
> **判断规则**：用户说"最近N天/周的广告/项目/创意"但**没有提到任何效果指标词**（消耗、曝光、点击、转化、ROI等）→ 一律视为查广告实体，走路径 B，通过 `filtering` 中的 `created_time` 筛选。

```
命中类别 A（报表/效果数据）且时间范围修饰的是报表数据
  └─→ 直接走【路径 A】

命中类别 B（实体列表/详情，不涉及报表指标）
或 用户说"最近N天的广告/项目/创意"但无效果指标词
  └─→ 进入【路径 B】二次意图判断
```

#### ⚠️ "数据"一词的歧义消解规则

用户说"查看创意/广告的数据"时，**必须判断是否包含效果指标意图**，不能仅凭"数据"二字走路径 A：

| 用户说法 | 是否含效果指标词 | 走向 |
|---------|----------------|------|
| "查创意数据"、"看一下这个广告的数据"、"查询这个创意" | ❌ 无（消耗/曝光/点击/转化等） | 路径 B → `query-creatives` / `query-adgroups` |
| "查创意的消耗数据"、"看广告的曝光/点击/转化数据" | ✅ 有 | 路径 A → `query-report` |

**规则**：仅有"数据"二字、**不带任何效果指标词**（消耗、曝光、点击、转化、ROI、成本等）→ 默认视为查询实体详情，走路径 B。

---

#### 路径 A：与报表/效果数据相关 → `query-report.mjs`

直接使用 `query-report.mjs`，一次请求同时返回实体属性 + 报表指标，**流程结束**。

| 典型场景 | 说明 |
|---------|------|
| 查看广告列表及效果数据（消耗、曝光、点击等） | 返回广告基本属性 + 报表指标 |
| 查看广告分时/按天趋势 | 按时间维度聚合报表数据 |
| 查看账户汇总数据 | 全账户维度汇总 |
| 按消耗/曝光等指标排序或筛选 | 支持 order_by + post_filtering |
| 拉取全部广告/导出所有数据/统计全量数据 | 使用 `fetch_all: true` 自动分页拉取 |

> ⚠️ **路径 A 排除规则**：用户说"最近N天的广告/项目/创意"但未提及任何效果指标词 → **不走路径 A**，转路径 B。

#### 路径 B：与项目/广告/创意详情相关（不涉及报表指标） → 直接调用详情脚本

根据用户查询目标，直接调用对应的详情脚本。如果用户带有时间范围筛选条件（如"最近3天的广告"、"这周新建的项目"），通过 `filtering` 中的 `created_time` 进行筛选，无需先走 `query-report.mjs`。

| 用户查询目标 | 调用脚本 | 时间范围处理 |
|-------------|---------|-------------|
| 项目详情 / 广告详情（定向、出价、转化、版位、能力配置等） | `query-adgroups.mjs` | 有时间范围时加 `filtering` 中 `created_time` 条件 |
| 创意详情（创意组件内容、投放模式、创意类型等） | `query-creatives.mjs` | 有时间范围时加 `filtering` 中 `created_time` 条件 |
| 创意列表（批量查看创意基本信息） | `query-creatives.mjs` | 有时间范围时加 `filtering` 中 `created_time` 条件 |

> **⚠️ 创意查询的组件解析策略（脚本自动判断，Agent 无需控制）**：
> - **查询结果只有 1 条创意**：脚本自动从 `creative_components` 中提取所有 `component_id`，调用组件详情接口拉取组件详情，再从组件中提取 `image_id` / `video_id`，获取预览 URL。最终将组件内容内联到 `_component_detail` 字段，图片/视频预览信息内联到 `_preview` 字段。
> - **查询结果有多条创意**：只返回创意基本信息，不解析组件，避免大量 API 请求影响性能。

#### 路径 C：营销资产查询

当用户需要查询营销资产（推广产品、应用包、渠道包等）时，根据资产类型选择对应的查询方式：

| 资产类型 | 查询方式 | 说明 |
|---------|---------|------|
| **安卓应用包 / 渠道包** | `node scripts/get-android-packages.mjs` | 查看 [shared/references/android-app-assets.md](../shared/references/android-app-assets.md) |
| **其他营销资产** | 暂未补充，可参考创建 SKILL（`delivery-standard-create` / `delivery-smart-create`）中的 `get-assets.mjs` 查询方式 | 后续按需扩展 |

### 步骤 2.5：字段名确认 — 不在常用映射表中的字段必须先查字典

> **⚠️ 强制规则：禁止猜测字段名！**
>
> 当用户请求的报表指标或广告字段**不在下方「常用报表字段映射」表中**时，**必须先用 `--query-fields` 查询字段字典**，确认准确的 API 字段名后再构造请求。
>
> **绝对禁止**根据英文命名规律自行拼凑字段名（如猜测 "关注数" → `wechat_official_account_follower_count`，实际应为 `scan_follow_user_count`）。API 字段名与直觉差异极大，猜测几乎必错。
>
> **判断标准**：逐一检查用户要求的每个指标/字段，如果在「常用报表字段映射」或「常用 fields 字段」表中能找到精确对应 → 直接使用；找不到 → **必须查字典**。
>
> **查字典方法**：
> - 报表指标字段：`node scripts/query-report.mjs --query-fields "关键词1,关键词2"`
> - 广告配置字段：`node scripts/query-adgroups.mjs --query-fields "关键词1,关键词2"`
>
> **示例**：用户要求查看"5秒播放数、关注数、关注成本、关注率"
> 1. 检查常用映射表 → 这4个指标都不在表中
> 2. 执行：`node scripts/query-report.mjs --query-fields "5秒播放,关注"`
> 3. 从返回结果中确认准确字段名，再构造 `fields` 参数

### 步骤3：执行查询 — 快速参考

| 脚本 | 核心能力 | 典型入参 |
|------|---------|---------|
| `query-report.mjs` | 跨账户报表 + 属性查询 | `account_ids` + `date_range` + `tencent_ads_type` |
| `query-adgroups.mjs` | 广告/项目完整配置详情 | `account_id` + `adgroup_ids` + `tencent_ads_type` |
| `query-creatives.mjs` | 创意列表 + 单创意自动解析组件/素材预览 | `account_id` + `adgroup_ids` 或 `creative_ids` + `tencent_ads_type` |
| `query-operation-logs.mjs` | 广告/创意操作日志（新建/修改字段变更详情） | `account_id` + `operation_object_type` + `start_date` + `end_date`，可选 `object_id` |

---

## 脚本：query-report.mjs

> **这是本技能的核心脚本**，封装了报表查询的全部复杂逻辑。

### 脚本自动处理的逻辑（Agent 无需关心）

1. **标准过滤条件**：根据 `level` 自动构建基础过滤条件 + 智投/非智投区分条件（通过 `LEVEL_FILTERING_CONFIG` 配置驱动）
   - 广告层级（ADGROUP 等）：`adgroup.brand_ad_type` + `adgroup.campaign_type` + `adgroup.smart_delivery_platform`
   - 创意层级（DYNAMIC_CREATIVE）：`dynamic_creative.brand_ad_type` + `adgroup.campaign_type` + `dynamic_creative.smart_delivery_platform`
   - 维度层级（REGION/CITY/AGE/GENDER 等）：使用对应 `report.*` 前缀
2. **模糊搜索字段自动切换**：`fuzzy_name` 在广告层级使用 `adgroup.fuzzy_name`，在创意层级使用 `dynamic_creative.fuzzy_name`
3. **group_by 推导**：根据 `level` 自动推导合适的 `group_by`（如 ADGROUP → `["adgroup_id"]`，DYNAMIC_CREATIVE → `["dynamic_creative_id"]`，REGION → `["area_id"]`）
4. **fields 补全**：未指定 `fields` 时，自动包含该 level 的默认属性字段 + 常用报表字段
5. **返回数据裁剪**：移除空对象和无效字段，减少 Agent 解析负担
6. **默认排序**：未指定 `order_by` 时，自动使用 `[{"sort_field": "report.default_order_by", "sort_type": "ASCENDING"}]`，**Agent 无需手动传 `order_by`，除非用户明确要求按某个指标排序**

### 调用方式

```bash
node scripts/query-report.mjs '<JSON 参数>'
```

### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `account_ids` | string[] | **是** | 广告主账号 ID 数组（如 `["123"]` 或 `["123", "456"]`），单账户也用数组格式 |
| `date_range` | struct | **是** | 报表统计时间窗口 `{ "start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD" }`。**注意：这是报表系统的统计区间，不是广告创建时间或投放时间。** 按创建时间筛选广告实体请用 `filtering` 中的 `adgroup.created_time`。 |
| `tencent_ads_type` | enum | 否 | 广告实体类型，**枚举值只允许 `"smart"` / `"standard"` / `"all"` 三者之一**，默认 `"all"`。详见步骤 1.5 |
| `level` | enum | 否 | 数据维度，默认 `"ADGROUP"`。可选：ADVERTISER / ADGROUP / DYNAMIC_CREATIVE / COMPONENT / BIDWORD / CHANNEL / REGION / CITY / AGE / GENDER / IMAGE / VIDEO / QUERYWORD / LANDING_PAGE / MARKETING_ASSET / AUDIENCE / JOINT_BUDGET_RULE / PRODUCT_CATALOG / AOI / PROJECT_CREATIVE / VIDEO_AGGREGATION / CREATIVE_ASSET / VIDEO_HIGHLIGHT / WECHAT_SHOP_PRODUCT 等 |
| `adgroup_ids` | string[] | 否 | 指定广告 ID 列表（传入后自动切为指定 ID 查询模式） |
| `creative_ids` | string[] | 否 | 指定创意 ID 列表 |
| `component_ids` | string[] | 否 | 指定组件 ID 列表 |
| `fields` | string[] | 否 | 自定义返回字段（不传则自动补全属性+报表字段） |
| `group_by` | string[] | 否 | 自定义聚合维度（不传则根据 level 自动推导） |
| `time_line` | enum | 否 | 时间口径，默认 `"REQUEST_TIME"` |
| `order_by` | struct[] | 否 | 排序条件。**通常不需要传**，脚本会自动使用默认排序。仅当用户明确要求按某个指标排序时才传，如 `[{"sort_field": "report.cost", "sort_type": "DESCENDING"}]` |
| `filtering` | struct[] | 否 | 额外自定义过滤条件（追加到标准过滤之后） |
| `post_filtering` | struct[] | 否 | 后置过滤条件（基于报表指标筛选） |
| `page` | integer | 否 | 页码，默认 1 |
| `page_size` | integer | 否 | 每页条数，默认 20 |
| `fetch_all` | boolean | 否 | 是否自动分页拉取全部数据，默认 false。开启后忽略 `page` 参数，自动翻页直到拉完所有数据（`page_size` 自动提升至至少 100 以减少请求次数）。详见下方 **`fetch_all` 使用规则** |
| `is_total` | boolean | 否 | 是否全账户汇总，默认 false |
| `report_only` | boolean | 否 | 仅查报表数据（不返回实体属性），默认 false |
| `fuzzy_name` | string | 否 | 名称模糊搜索。广告层级（ADGROUP）时搜索广告名称，创意层级（DYNAMIC_CREATIVE）时搜索创意名称 |

### 使用示例

#### 1. 查询所有广告列表（最常用，默认模式）

```bash
node scripts/query-report.mjs '{"account_ids":["39412855"],"date_range":{"start_date":"2026-03-25","end_date":"2026-03-25"}}'
```

> 不传 `tencent_ads_type`、`fields`、`group_by` 时，脚本默认 `tencent_ads_type: "all"`（智投项目 + 竞价广告全部返回） + 默认属性与报表字段 + `group_by: ["adgroup_id"]`。

#### 2. 查询智投广告

```bash
node scripts/query-report.mjs '{"account_ids":["39412855"],"date_range":{"start_date":"2026-03-25","end_date":"2026-03-25"},"tencent_ads_type":"smart"}'
```

#### 3. 查询指定广告 ID 的数据

```bash
node scripts/query-report.mjs '{"account_ids":["39412855"],"date_range":{"start_date":"2026-03-25","end_date":"2026-03-25"},"adgroup_ids":["72536365535"]}'
```

> 传了 `adgroup_ids` 后，脚本自动切换到 `specified` 模式，只使用 ID 过滤，不加基础 3 条和智投/非智投条件。

#### 4. 查看指定广告的分时趋势

```bash
node scripts/query-report.mjs '{"account_ids":["39412855"],"date_range":{"start_date":"2026-03-25","end_date":"2026-03-25"},"adgroup_ids":["72536365535"],"group_by":["date","hour"],"page_size":100}'
```

> 分时查询：`group_by` 使用 `["date", "hour"]`，脚本自动精简 fields 只保留报表指标。

#### 5. 查看指定广告的按天趋势

```bash
node scripts/query-report.mjs '{"account_ids":["39412855"],"date_range":{"start_date":"2026-03-19","end_date":"2026-03-25"},"adgroup_ids":["72536365535"],"group_by":["date"]}'
```

#### 6. 按消耗排序

```bash
node scripts/query-report.mjs '{"account_ids":["39412855"],"date_range":{"start_date":"2026-03-25","end_date":"2026-03-25"},"order_by":[{"sort_field":"report.cost","sort_type":"DESCENDING"}]}'
```

#### 7. 用后置过滤筛选高消耗广告

```bash
node scripts/query-report.mjs '{"account_ids":["39412855"],"date_range":{"start_date":"2026-03-25","end_date":"2026-03-25"},"post_filtering":[{"field":"report.cost","operator":"GREATER","values":["100000"]}]}'
```

#### 8. 查询创意级别数据

查询智投项目下的创意列表：

```bash
node scripts/query-report.mjs '{"account_ids":["39412855"],"date_range":{"start_date":"2026-03-25","end_date":"2026-03-25"},"level":"DYNAMIC_CREATIVE","tencent_ads_type":"smart"}'
```

查询竞价广告下的创意列表：

```bash
node scripts/query-report.mjs '{"account_ids":["39412855"],"date_range":{"start_date":"2026-03-25","end_date":"2026-03-25"},"level":"DYNAMIC_CREATIVE","tencent_ads_type":"standard"}'
```

按创意名称模糊搜索（`fuzzy_name` 在创意层级自动使用 `dynamic_creative.fuzzy_name`）：

```bash
node scripts/query-report.mjs '{"account_ids":["39412855"],"date_range":{"start_date":"2026-03-25","end_date":"2026-03-25"},"level":"DYNAMIC_CREATIVE","fuzzy_name":"品牌创意"}'
```

按投放模式筛选（只看组件化创意），通过 `filtering` 追加：

```bash
node scripts/query-report.mjs '{"account_ids":["39412855"],"date_range":{"start_date":"2026-03-25","end_date":"2026-03-25"},"level":"DYNAMIC_CREATIVE","filtering":[{"field":"dynamic_creative.delivery_mode","operator":"EQUALS","values":["DELIVERY_MODE_COMPONENT"]}]}'
```

按创意状态筛选（竞价广告创意用 `DYNAMIC_CREATIVE_STATUS_*`，智投项目创意用 `SMART_DYNAMIC_CREATIVE_STATUS_*`）：

```bash
node scripts/query-report.mjs '{"account_ids":["39412855"],"date_range":{"start_date":"2026-03-25","end_date":"2026-03-25"},"level":"DYNAMIC_CREATIVE","tencent_ads_type":"standard","filtering":[{"field":"dynamic_creative.system_status","operator":"IN","values":["DYNAMIC_CREATIVE_STATUS_PENDING","DYNAMIC_CREATIVE_STATUS_ACTIVE"]}]}'
```

按创意类型筛选（客户自建 vs 妙思自动生成）：

```bash
node scripts/query-report.mjs '{"account_ids":["39412855"],"date_range":{"start_date":"2026-03-25","end_date":"2026-03-25"},"level":"DYNAMIC_CREATIVE","filtering":[{"field":"dynamic_creative.source","operator":"EQUALS","values":["AD_CREATIVE_SOURCE_NORMAL"]}]}'
```

> **创意层级自动处理说明**：
> - `operation_status` 过滤自动使用 `dynamic_creative.operation_status`（不是 `adgroup.operation_status`）
> - 智投/非智投区分自动使用 `dynamic_creative.smart_delivery_platform`（不是 `adgroup.smart_delivery_platform`）
> - `fuzzy_name` 自动使用 `dynamic_creative.fuzzy_name`（不是 `adgroup.fuzzy_name`）

#### 9. 查询账户汇总数据

```bash
node scripts/query-report.mjs '{"account_ids":["39412855"],"date_range":{"start_date":"2026-03-25","end_date":"2026-03-25"},"is_total":true,"page_size":1}'
```

#### 10. 按名称模糊搜索广告

```bash
node scripts/query-report.mjs '{"account_ids":["39412855"],"date_range":{"start_date":"2026-03-25","end_date":"2026-03-25"},"fuzzy_name":"品牌推广"}'
```

#### 10.5. 多账户同时查询

```bash
node scripts/query-report.mjs '{"account_ids":["39412855","73412663"],"date_range":{"start_date":"2026-03-25","end_date":"2026-03-25"}}'
```

> `account_id` 支持传入数组，一次请求同时查询多个账户的数据。返回结果中每条数据包含 `account_id` 字段，可区分所属账户。

#### 10.6. 自动分页拉取全部广告数据

```bash
node scripts/query-report.mjs '{"account_ids":["39412855"],"date_range":{"start_date":"2026-03-25","end_date":"2026-03-25"},"fetch_all":true}'
```

> 开启 `fetch_all` 后，脚本自动翻页拉取所有数据，最终返回的 `page_info` 中 `total_number` 为全部条数，`total_page` 固定为 1。

##### `fetch_all` 使用规则

| 用户意图 | `fetch_all` 值 | 说明 |
|---------|---------------|------|
| 普通列表查询（"查看广告"、"看下效果"） | `false`（默认） | 只需要当前页数据，默认返回 20 条 |
| "拉取全部广告" / "导出所有数据" / "一共有多少条广告" | `true` | 用户明确要求全量数据 |
| "帮我统计所有广告的消耗总和" / 需要对全量数据做聚合分析 | `true` | 需要拉取全部后才能汇总计算 |
| "查看所有消耗大于 100 的广告" / 全量筛选 | `true` | 需要全量数据才能完整筛选 |
| "列出全部在投广告" / "所有正在投放的项目" | `true` | 用户要求完整列表 |
| 用户明确指定了 page / page_size | `false` | 用户自行控制分页，不需要自动拉取 |

> ⚠️ **判断关键词**：当用户使用"全部"、"所有"、"一共"、"总共"、"导出"、"拉取全量"、"完整列表"等词汇时，应设置 `fetch_all: true`。
> 当用户只是普通查询或明确指定了分页参数时，保持默认 `fetch_all: false`。
```

#### 11. 查询指定广告的分地域投放数据（受众分析-地域报表）

```bash
node scripts/query-report.mjs '{"account_ids":["39412855"],"date_range":{"start_date":"2026-03-25","end_date":"2026-03-25"},"level":"REGION","adgroup_ids":["72536365535"]}'
```

> **分地域查询关键点**：当用户要求"分地域"、"按地域"、"各地区"、"省份分布"等维度查看投放数据时，**必须使用 `level: "REGION"`**，脚本会自动推导 `group_by: ["area_id"]` 和正确的过滤条件。同理，"分城市" → `level: "CITY"`，"分年龄" → `level: "AGE"`，"分性别" → `level: "GENDER"`。**切勿使用 `level: "ADGROUP"` 来查询地域/城市/年龄/性别维度的数据。**

#### 12. 按创建时间筛选广告/项目（adindex 实体过滤）

> **适用场景**：用户说"最近 N 天内创建的项目/广告"、"本周新建的广告"等——这是对**广告实体**的筛选，不是报表时间窗口。
> - `date_range` 用近期时间（如当天）即可，其值不影响广告实体的筛选
> - 创建时间用 `filtering` 中的 `adgroup.created_time`，值为 **`YYYY-MM-DD HH:mm:ss` 格式**（如 `"2026-03-18 00:00:00"`），脚本内部自动转为时间戳

查询最近一周内创建的智投项目（不关心报表数据）：

```bash
node scripts/query-report.mjs '{
  "account_ids": ["39412855"],
  "date_range": {"start_date": "2026-03-27", "end_date": "2026-03-27"},
  "tencent_ads_type": "smart",
  "filtering": [
    {"field": "adgroup.created_time", "operator": "GREATER_EQUALS", "values": ["<7天前 YYYY-MM-DD 00:00:00>"]},
    {"field": "adgroup.created_time", "operator": "LESS_EQUALS",    "values": ["<今天 YYYY-MM-DD 23:59:59>"]}
  ],
  "fields": [
    "account_id",
    "adgroup.adgroup_id",
    "adgroup.adgroup_name",
    "adgroup.configured_status_cn",
    "adgroup.system_status_cn",
    "adgroup.smart_delivery_platform",
    "adgroup.project_ability_spec",
    "adgroup.begin_date"
  ]
}'
```

> `fields` 里不含 `report.*` 字段时，`date_range` 仅作为接口必填项存在，对结果无实质影响。

#### 13. 查询创意资产（文案素材）级别数据

当用户要查文案素材（标题/描述）维度的投放效果时，使用 `CREATIVE_ASSET` 级别。注意：过滤条件使用 `report.*` 字段，不使用 `adgroup.*` 字段。

```bash
node scripts/query-report.mjs '{"account_ids":["39412855"],"date_range":{"start_date":"2026-03-25","end_date":"2026-03-25"},"level":"CREATIVE_ASSET","group_by":["creative_asset_id","adgroup_id","dynamic_creative_id"],"order_by":[{"sort_field":"report.cost","sort_type":"DESCENDING"}],"fields":["creative_asset.creative_asset_id","creative_asset.creative_asset_name","creative_asset.component_id","creative_asset.component_type","creative_asset.component_value","creative_asset.component_custom_name","creative_asset.account_id","report.cost","report.view_count","report.valid_click_count","report.ctr","report.thousand_display_price","report.cpc","report.conversions_rate","report.adgroup_id","report.dynamic_creative_id"],"filtering":[{"field":"report.brand_ad_type","operator":"EQUALS","values":["BRAND_AD_TYPE_NONE"]},{"field":"report.campaign_type","operator":"EQUALS","values":["CAMPAIGN_TYPE_NORMAL"]},{"field":"report.creative_asset_sub_type","operator":"IN","values":["DESCRIPTION","TITLE"]}]}'
```

> **CREATIVE_ASSET 查询要点**：
> - `level` 设为 `"CREATIVE_ASSET"`，`group_by` 包含 `"creative_asset_id"`
> - `filtering` 使用 `report.*` 字段（如 `report.brand_ad_type`、`report.campaign_type`、`report.creative_asset_sub_type`），**不使用** `adgroup.*` 字段
> - 按素材子类型过滤文案：`report.creative_asset_sub_type` IN `["DESCRIPTION", "TITLE"]`

#### 14. 查询组件级别数据

```bash
node scripts/query-report.mjs '{"account_ids":["39412855"],"date_range":{"start_date":"2026-03-25","end_date":"2026-03-25"},"level":"COMPONENT"}'
```

### 返回结构

```json
{
  "file_path": "/absolute/path/to/output/report_39412855_ADGROUP_20260325_20260325_20260325T103000.json",
  "summary": {
    "total_rows": 150,
    "page_info": {
      "page": 1,
      "page_size": 20,
      "total_number": 150,
      "total_page": 8
    },
    "level": "ADGROUP",
    "date_range": { "start_date": "2026-03-25", "end_date": "2026-03-25" },
    "account_ids": [39412855],
    "tencent_ads_type": "all"
  },
  "preview": [
    {
      "account_id": 39412855,
      "adgroup": {
        "adgroup_id": 123456,
        "adgroup_name": "广告名称",
        "configured_status": "AD_STATUS_NORMAL"
      },
      "report": {
        "cost": 10000,
        "view_count": 50000,
        "valid_click_count": 1200,
        "ctr": "2.40"
      }
    }
  ]
}
```

> **输出说明**：脚本会将完整查询结果写入 `output/` 目录下的 JSON 文件，stdout 只返回文件路径、摘要信息和前 3 条预览数据。模型可通过 `file_path` 读取完整数据文件，编写实时分析脚本生成数据报告。

> **数据文件格式**：`output/report_<账户ID>_<level>_<日期范围>_<时间戳>.json`，内容为 `{ "list": [...], "page_info": {...} }`。

### 常用报表字段映射（用户描述 → fields 字段名）

当用户提到以下指标时，请在 `fields` 参数中使用对应的字段名：

| 用户描述 | fields 字段名 | 说明 |
|---------|-------------|------|
| 消耗/花费 | `report.cost` | 广告消耗金额 |
| 曝光量/展示量 | `report.view_count` | 广告曝光次数 |
| 点击量 | `report.valid_click_count` | 有效点击次数 |
| 点击率/CTR | `report.ctr` | 点击率 |
| 转化数/转化量 | `report.conversions_count` | 转化次数 |
| 转化成本 | `report.conversions_cost` | 每次转化的成本 |
| 转化率 | `report.conversions_rate` | 转化率 |
| 落地页按钮点击量 | `report.lan_button_click_count` | 落地页按钮点击次数 |
| 账户余额 | `report.balance` | 账户剩余金额 |
| 出价/出价金额 | `report.cost_price` | 广告出价 |
| 营销内容 | `report.marketing_content` | 营销内容信息 |
| 地域/地区 | `report.area` | 地域名称（分地域查询时使用） |
| 千次曝光成本/CPM | `report.thousand_display_price` | 每千次曝光成本 |
| 点击均价/CPC | `report.click_cost` | 每次点击成本 |
| 深度转化数 | `report.deep_conversions_count` | 深度转化次数 |
| 深度转化成本 | `report.deep_conversions_cost` | 深度转化成本 |
| 微信加粉成本 | `report.wechat_cost_stage1` | 微信加粉阶段成本 |
| 企微加粉成本 | `report.wechat_cost_stage2` | 企微加粉阶段成本 |

> **提示**：当用户要求查看多个指标时，请将所有对应的 `report.*` 字段都加入 `fields` 数组中。如果用户没有明确指定指标，可以不传 `fields`，脚本会自动使用默认字段集。
>
> **⚠️ 强制规则**：上表仅列出最常用的 18 个字段，报表系统共有 854 个字段。**如果用户提到的指标不在上表中，必须先执行 `node scripts/query-report.mjs --query-fields "关键词"` 查询字段字典，确认准确字段名后再构造请求。禁止自行猜测或拼凑字段名。**

---

## 核心脚本

| 脚本 | 用途 |
|------|------|
| query-report.mjs | 跨账户查询广告/创意/素材的列表数据+报表指标（核心入口，融合属性查询与效果数据） |
| query-adgroups.mjs | 获取广告完整配置信息（定向、出价、转化、版位等） |
| query-creatives.mjs | 获取创意列表及组件详情；单创意时自动解析组件并获取图片/视频预览 URL |

## 请求参数

### 必填参数

| 参数名 | 类型 | 说明 | 限制 |
|--------|------|------|------|
| date_range | struct | 日期范围 | 最早支持365天内数据 |
| date_range.start_date | string | 开始日期 | YYYY-MM-DD，≤ end_date |
| date_range.end_date | string | 结束日期 | YYYY-MM-DD，≥ start_date |
| level | enum | 数据维度级别 | 见下方 level 枚举值 |

### 可选参数

| 参数名 | 类型 | 说明 | 限制/默认值 |
|--------|------|------|------------|
| account_id_list | integer[] | 广告主账号 ID 列表 | 最多 400 个，不支持代理商 ID |
| filtering | struct[] | 前置过滤条件 | 数组 1-40 个，见下方过滤条件说明 |
| or_filtering | struct[][] | 二维过滤条件（OR 逻辑） | 数组 1-40 个 |
| post_filtering | struct[] | 后置过滤条件（基于报表指标筛选） | 数组 1-32 个 |
| order_by | struct[] | 排序字段 | 最多 2 个排序条件，示例：`[{"sort_field": "report.cost", "sort_type": "DESCENDING"}]` |
| time_line | enum | 时间口径 | REQUEST_TIME / REPORTING_TIME / ACTIVE_TIME |
| group_by | string[] | 聚合参数 | 数组 1-10 个。每个 level 只支持特定的 group_by 值，见下方 **level 数据维度与 group_by 对应表** |
| page | integer | 页码 | 1-99999，默认 1 |
| page_size | integer | 每页条数 | 1-99999999，默认 10 |
| report_only | boolean | 仅查报表数据模式（true=只返回报表指标，不返回实体属性数据） | 默认 false |
| is_total | boolean | 是否为汇总数据（全账户级汇总） | 默认 false |
| fields | string[] | 指定返回的字段列表 | 数组 1-1024 个，最大长度 64 字符/项 |
| operating_scene_type | enum | 操作平台场景类型 | 枚举 OperatingSceneType |
| organization_id | integer | 业务单元 ID | 0-9999999999 |
| request_source | enum | 请求来源 | 枚举 RequestSourceType |

**level 数据维度与 group_by 对应表**：

每个 `level` 只支持特定的 `group_by` 值，不传时脚本自动使用默认值。自定义 `group_by` 时必须从该 level 的合法值中选取，**禁止使用不在此表中的值**。

| level | 说明 | 适用场景 | 合法 group_by 值 | 默认值 | group_by 说明 |
|-------|------|---------|-----------------|--------|-------------|
| ADVERTISER | 账户级别 | 当用户要求"账户级别报表"、"账户维度数据"时使用。不返回具体广告/创意明细，只返回账户粒度汇总数据 | `date`, `hour` | `["date"]` | 只支持时间维度，**不支持** `account_id`、`site_set`；按小时查用 `["date", "hour"]` |
| ADGROUP | 广告级别 | **最常用**。当用户要求"广告数据"、"广告列表"、"投放数据"时使用（未明确指定其他 level 时默认使用） | `adgroup_id`, `date`, `hour`, `site_set` | `["adgroup_id"]` | 按天趋势用 `["adgroup_id", "date"]`；按小时趋势用 `["adgroup_id", "date", "hour"]`；按版位用 `["adgroup_id", "site_set"]` |
| DYNAMIC_CREATIVE | 动态创意级别 | 当用户要求查看"创意效果"、"创意对比"、"创意列表"时使用（指普通广告的动态创意，非智投项目创意）。注意与 `PROJECT_CREATIVE` 区分 | `dynamic_creative_id`, `adgroup_id`, `date`, `hour`, `site_set` | `["dynamic_creative_id", "adgroup_id"]` | 必须包含 `dynamic_creative_id`；按小时趋势用 `["dynamic_creative_id", "date", "hour"]` |
| COMPONENT | 组件级别 | 当用户提到"素材组件"、"组件ID"、"组件效果"、"组件报表"时使用。`filtering` 可按 `component_id`、`component_sub_type` 等筛选。注意：用户说"视频素材组件"或"图片素材组件"时也应使用此 level，而非 VIDEO/IMAGE | `component_id`, `date`, `hour` | `["component_id"]` | |
| CREATIVE_ASSET | 创意资产级别 | 当用户要查询文案类素材（标题/描述）的投放效果时使用。`filtering` 使用 `report.*` 字段（非 `adgroup.*`） | `creative_asset_id`, `adgroup_id`, `dynamic_creative_id`, `date`, `product_catalog_id`, `product_series_id`, `product_outer_id` | `["creative_asset_id", "adgroup_id", "dynamic_creative_id"]` | 支持商品维度 |
| CHANNEL | 渠道级别 | 渠道包报表 | `channel_id` | `["channel_id"]` | 不支持时间维度 |
| BIDWORD | 竞价词级别 | 搜索分析-关键词报表。当用户提到"竞价词"、"关键词出价"时使用 | `bidword_id`, `date` | `["bidword_id"]` | |
| QUERYWORD | 搜索词级别 | 搜索分析-搜索词报表。当用户提到"搜索词"时使用 | `queryword_id`, `queryword`, `date` | `["queryword_id"]` | |
| IMAGE | 图片素材级别 | 当用户要求按图片 ID 查看图片素材效果时使用（素材分析-图片素材报表）。注意：若用户说的是"图片组件"或"图片素材组件"，应使用 `COMPONENT` level | `image_id`, `date` | `["image_id"]` | |
| VIDEO | 视频素材级别 | 当用户要求按视频 ID 查看视频素材效果时使用（素材分析-视频素材报表）。注意：若用户说的是"视频组件"或"视频素材组件"，应使用 `COMPONENT` level | `video_id`, `date` | `["video_id"]` | |
| MEDIA | 素材级别 | 素材报表 | `media_id`, `date` | `["media_id"]` | |
| VIDEO_AGGREGATION | 视频聚合级别 | 当用户要求按视频 MD5 聚合查看素材效果时使用 | `md5` | `["md5"]` | |
| VIDEO_HIGHLIGHT | 视频高光帧级别 | 视频高光帧分析报表 | `md5`, `play_index` | `["md5"]` | `play_index` 需要后端开关 |
| MARKETING_ASSET | 产品资产级别 | 当用户提到"推广产品"、"产品资产"、"营销资产"时使用。查看推广产品维度的投放效果 | `marketing_asset_id`, `date`, `product_catalog_id`, `product_series_id`, `product_outer_id` | `["marketing_asset_id"]` | 支持商品维度 |
| LANDING_PAGE | 落地页级别 | 当用户提到"落地页"时使用 | `landing_page_id`, `vangogh_landing_page_id`, `date` | `["landing_page_id"]` | `group_by` 用 `landing_page_id` 而非 `landing_page_url` |
| PRODUCT_CATALOG | 商品级别 | 当用户提到"商品目录"、"商品系列"、"商品ID"、"多商品广告"、"商品维度"时使用。查看商品目录/系列/单品维度的投放效果。注意与 `MARKETING_ASSET`（推广产品）区分 | `product_catalog_id`, `product_series_id`, `product_outer_id`, `date` | `["product_catalog_id"]` | 支持商品层级维度 |
| WECHAT_SHOP_PRODUCT | 微信小店商品级别 | 当用户提到"微信小店商品"、"视频号商品"、"小店商品"时使用 | `wechat_channels_product_id`, `wechat_channels_shop_id`, `date` | `["date"]` | |
| JOINT_BUDGET_RULE | 联合预算规则级别 | 联合广告预算规则 | `joint_budget_rule_id`, `date` | `["joint_budget_rule_id"]` | |
| PROJECT_CREATIVE | 智投项目创意级别 | 当用户提到"智投项目创意"、"项目创意"、"指定项目下的创意"时使用。注意与 `DYNAMIC_CREATIVE` 区分：用户提到"项目 ID + 创意"时用此 level，而非 `DYNAMIC_CREATIVE` | `dynamic_creative_id`, `adgroup_id`, `date`, `hour` | `["dynamic_creative_id", "adgroup_id"]` | |
| REGION | 省份/地域级别 | 分地域投放数据。当用户要求"分地域"、"按地域"、"各地区"、"省份分布"、"地域报表"时使用。可配合 `adgroup_ids` 查看指定广告的地域分布 | `area_id`, `adgroup_id`, `date` | `["area_id"]` | `adgroup_id` 可选 |
| CITY | 城市级别 | 分城市投放数据。当用户要求"分城市"、"按城市"、"城市报表"时使用 | `city_id`, `adgroup_id`, `date` | `["city_id"]` | `adgroup_id` 可选 |
| AGE | 年龄级别 | 分年龄投放数据。当用户要求"分年龄"、"按年龄"、"年龄报表"时使用 | `age`, `adgroup_id`, `date` | `["age"]` | `adgroup_id` 可选 |
| GENDER | 性别级别 | 分性别投放数据。当用户要求"分性别"、"按性别"、"性别报表"时使用 | `gender`, `adgroup_id`, `date` | `["gender"]` | `adgroup_id` 可选 |
| AOI | AOI 级别 | AOI 报表 | `aoi_id`, `adgroup_id`, `date` | `["aoi_id"]` | `adgroup_id` 可选 |
| AUDIENCE | 人群包级别 | 受众分析-人群包报表。当用户提到"人群包"、"受众分析"、"人群定向"时使用 | `audience_id`, `account_id`, `adgroup_id`, `dynamic_creative_id`, `date`, `hour` | `["audience_id", "account_id"]` | 支持多维度组合 |

> **关键参数组合规则（必须遵守，否则 report 会返回空对象）**:
>
> 0. **`order_by` 排序规则**：
>    - **脚本已自动处理默认排序**：未传 `order_by` 时，脚本自动使用 `[{"sort_field": "report.default_order_by", "sort_type": "ASCENDING"}]`。**通常不需要手动传 `order_by`**。
>    - **仅当用户明确要求排序时才传**：当用户描述中包含排序意图（如"按 XX 从高到低"、"按 XX 排序"等），按用户意图构造：
>    - 格式：`[{"sort_field": "report.xxx", "sort_type": "DESCENDING"}]`
>    - `sort_type` 枚举值：`DESCENDING`（降序，从高到低）、`ASCENDING`（升序，从低到高）
>    - 示例：用户说"按曝光量从高到低排序" → `[{"sort_field": "report.view_count", "sort_type": "DESCENDING"}]`
>    - 示例：用户说"按消耗升序" → `[{"sort_field": "report.cost", "sort_type": "ASCENDING"}]`
>    - **最多支持 2 个排序条件**
>
> 1. **`group_by` 事实上必填**：虽然协议定义为可选，但不传 `group_by` 时接口几乎不会返回有效 report 数据。每个 level 的合法值和默认值见上方 **level 数据维度与 group_by 对应表**。
>    - **`hour` 必须配 `date`**：使用 `hour` 时必须同时带 `date`（如 `["date", "hour"]` 或 `["adgroup_id", "date", "hour"]`），单独传 `hour` 不带 `date` 不会报错但数据不完整（不同天的同一小时会被合并）。
>    - **分时/按天趋势查询**：查看指定广告的分时趋势 → `group_by: ["date", "hour"]`；查看指定广告的按天趋势 → `group_by: ["date"]`；查看广告列表的每日汇总 → `group_by: ["adgroup_id", "date"]`。
>
> 2. **`filtering` 强烈推荐**：不传过滤条件时，接口可能返回空结果或无法匹配到有效数据。
>
>    **场景一：查询广告列表（无指定 adgroup_id）**— 需要完整的标准过滤（基础 3 条 + 智投/非智投条件），详见下方。
>
>    **场景二：查询指定广告 ID 的数据（如分时趋势、按天趋势）**— **只需传 `adgroup.adgroup_id` 过滤即可**，不需要加基础 3 条和智投/非智投条件，因为已经精确定位到具体广告。
>    ```json
>    [{"field": "adgroup.adgroup_id", "operator": "EQUALS", "values": ["72536365535"]}]
>    ```
>
>    **场景一的标准过滤分为基础 3 条 + 第 4 条智投/非智投区分条件**：
>

   ⚠️ **重要：`filtering` 中的过滤字段层级必须与 `level` 匹配，不同 level 使用不同的过滤字段前缀：**
   - `level` 为 `ADGROUP`、`COMPONENT` 等 → 使用 `adgroup.*` 层级过滤字段
   - `level` 为 `DYNAMIC_CREATIVE` → **混合使用**：`operation_status` 和 `brand_ad_type` 使用 `dynamic_creative.*`，`campaign_type` 使用 `adgroup.*`（见下方详细说明）
   - `level` 为 `CREATIVE_ASSET`（创意资产级别）→ 使用 `report.*` 层级过滤字段（如 `report.brand_ad_type`、`report.campaign_type`、`report.creative_asset_sub_type`），**不使用** `adgroup.*` 层级过滤
   - `level` 为 `ADVERTISER`（账户级别报表）→ 不需要也不应该传任何实体层级的过滤条件

   **基础过滤条件（仅适用于 `level` 为 `ADGROUP`/`DYNAMIC_CREATIVE`/`COMPONENT` 等实体级别时）**：

   广告层级（`level=ADGROUP`）：
>    ```json
>    {"field": "adgroup.brand_ad_type", "operator": "EQUALS", "values": ["BRAND_AD_TYPE_NONE"]},
>    {"field": "adgroup.campaign_type", "operator": "EQUALS", "values": ["CAMPAIGN_TYPE_NORMAL"]}
>    ```

   创意层级（`level=DYNAMIC_CREATIVE`，注意 `brand_ad_type` 前缀变为 `dynamic_creative.*`）：
>    ```json
>    {"field": "dynamic_creative.operation_status", "operator": "EQUALS", "values": ["CALCULATE_STATUS_EXCLUDE_DEL"]},
>    {"field": "dynamic_creative.brand_ad_type", "operator": "EQUALS", "values": ["BRAND_AD_TYPE_NONE"]},
>    {"field": "adgroup.campaign_type", "operator": "EQUALS", "values": ["CAMPAIGN_TYPE_NORMAL"]}
>    ```
>
>
>    > ⚠️ **`operation_status` 仅在查询广告列表或创意列表时添加，查询报表数据（如汇总统计、效果分析等纯报表场景）时不添加此条件。**
>    > 使用 `query-report.mjs` 脚本时，以上基础过滤条件**由脚本自动构建**，无需手动传入。
>
>    **`CREATIVE_ASSET` 级别的过滤条件（使用 `report.*` 字段，不使用 `adgroup.*`）**：
>    ```json
>    {"field": "report.brand_ad_type", "operator": "EQUALS", "values": ["BRAND_AD_TYPE_NONE"]},
>    {"field": "report.campaign_type", "operator": "EQUALS", "values": ["CAMPAIGN_TYPE_NORMAL"]}
>    ```
>    如需按素材子类型过滤（如只看文案描述和标题）：
>    ```json
>    {"field": "report.creative_asset_sub_type", "operator": "IN", "values": ["DESCRIPTION", "TITLE"]}
>    ```
>    > ⚠️ 注意：`CREATIVE_ASSET` 级别**不需要**也**不应该**加 `adgroup.operation_status`、`adgroup.smart_delivery_platform` 等 `adgroup.*` 过滤条件。
>
>    **第 4 条：`smart_delivery_platform`（必须根据查询意图选择，同样仅适用于实体级别）**：
>
>    > ⚠️ **广告层级（ADGROUP）与创意层级（DYNAMIC_CREATIVE）使用不同的字段**：
>    > - `level=ADGROUP` → 使用 `adgroup.smart_delivery_platform`
>    > - `level=DYNAMIC_CREATIVE` → 使用 `dynamic_creative.smart_delivery_platform`
>    > - 使用 `query-report.mjs` 脚本时，脚本会根据 `level` **自动选择正确的字段**，无需手动指定。
>
>    - **查智投广告/创意**（默认，当前大部分广告都是智投广告）：
>      ```json
>      {"field": "adgroup.smart_delivery_platform", "operator": "GREATER_EQUALS", "values": ["SMART_DELIVERY_PLATFORM_EDITION_SCENE"]}
>      ```
>      或（创意层级）：
>      ```json
>      {"field": "dynamic_creative.smart_delivery_platform", "operator": "GREATER_EQUALS", "values": ["SMART_DELIVERY_PLATFORM_EDITION_SCENE"]}
>      ```
>    - **查非智投广告/创意**（用户明确要求查非智投/竞价广告时）：
>      ```json
>      {"field": "adgroup.smart_delivery_platform", "operator": "LESS", "values": ["SMART_DELIVERY_PLATFORM_EDITION_SCENE"]}
>      ```
>      或（创意层级）：
>      ```json
>      {"field": "dynamic_creative.smart_delivery_platform", "operator": "LESS", "values": ["SMART_DELIVERY_PLATFORM_EDITION_SCENE"]}
>      ```

>    **⚠️ 智投和非智投不能在同一次请求中混合查询，每次请求只能查其中一种。**
>
>    **意图判断规则**：
>    - 用户说"查非智投广告"、"查常规广告"、"查老广告"、"不含智投"、"排除智投"、"竞价广告"、"只看竞价"、"不含智投项目" → 查**常规广告（非智投）**（`LESS`），只需一次请求
>    - 用户说"查智投广告"、"智投项目"、"智投报表" → 查**智投广告**（`GREATER_EQUALS`），只需一次请求
>    - 用户说"两种都看"、"智投和非智投都要" → 先查**智投广告**（`GREATER_EQUALS`），再查**常规广告（非智投）**（`LESS`），共两次请求（顺序发，不要并行）
>    - **⚠️ 如果意图不确定（用户未明确指定智投或非智投），应发两次请求：先智投 `GREATER_EQUALS`，再非智投 `LESS`，以保证最终数据的准确性和完整性**
>
> 3. **`fields` 必须包含所需字段**：
>    - **查询广告列表时**：`fields` 必须同时包含属性字段（如 `adgroup.adgroup_id`、`adgroup.adgroup_name`）和报表字段（如 `report.cost`），否则 report 会返回空对象。
>    - **查询指定广告的分时/按天趋势时**：`fields` **只需包含用户关心的报表指标即可**（如 `["report.view_count", "report.view_user_count"]`），不需要额外加 `adgroup.*` 属性字段和 `account_id`，因为已经通过 filtering 精确定位到了具体广告。
>    - **实体级别查询**（`level` 为 `ADGROUP`、`DYNAMIC_CREATIVE`、`COMPONENT` 等）：必须**同时包含属性字段和报表字段**，仅请求 `report.*` 字段而不请求对应的属性字段（如 `adgroup.adgroup_id`）会导致 report 返回空。应**同时请求** `adgroup.*` 和 `report.*` 字段。
>    - **账户级别查询**（`level` 为 `ADVERTISER`）：查询的是账户维度汇总报表，**只需传用户关心的 `report.*` 报表字段即可，不需要也不应该传 `account_id`、`adgroup.*` 等属性字段**，否则会导致参数冗余。
       >      - ✅ 正确：`"fields": ["report.view_count", "report.cost"]`
>      - ❌ 错误：`"fields": ["account_id", "report.view_count", "report.cost"]`
>
> 4. **`is_total` 的正确用法**：
>    - `is_total: false`（默认）= 返回**逐条明细数据**（每个广告/创意一行），**这是最常用的模式**
>    - `is_total: true` = 返回**全账户汇总**（所有广告合并为一条），此时仍需传 `group_by`、`filtering` 和 `fields`（包含属性+报表字段）
>    - **查询广告列表时请使用 `is_total: false`**
>
> 5. **`date_range` vs `adgroup.created_time`：两套独立系统，含义完全不同**
>
>    本接口底层由两个独立系统协同工作：
>    - **报表系统**：负责 `report.*` 字段的统计数据，由 `date_range` 控制统计区间
>    - **adindex（广告实体索引）**：负责返回哪些广告/创意实体，由 `filtering` 中的 `adgroup.created_time` 等条件控制
>
>    | 用途 | 参数 | 示例 |
>    |------|------|------|
>    | 控制报表指标的统计时间窗口 | `date_range` | `{"start_date":"2026-03-01","end_date":"2026-03-27"}` |
>    | 筛选某段时间内**创建**的广告/项目 | `filtering` 中 `adgroup.created_time` | `{"field":"adgroup.created_time","operator":"GREATER_EQUALS","values":["2026-03-20 00:00:00"]}` |
>
>    **⚠️ 关键区别**：
>    - `date_range` **不是**广告的创建时间，也不是投放时间，是**报表统计窗口**
>    - 如果某广告在 `date_range` 范围内没有消耗/曝光，`report.*` 字段会返回空，但广告实体本身仍然存在
>    - 只查广告/项目实体信息（不关心消耗数据）时，`date_range` 设为任意有效时间段即可（通常用近期时间）
>
>    **意图判断规则（模型必须遵守）**：
>
>    | 用户说的 | 正确做法 |
>    |---------|---------|
>    | "最近一周的消耗数据" / "最近7天的报表" | `date_range` = 最近7天，不加 `created_time` 过滤 |
>    | "最近一周内创建的广告/项目" | `date_range` = 当天（或近期），`filtering` 加 `adgroup.created_time` >= 7天前的时间戳 |
>    | **"最近一周的广告/项目/创意"（无效果指标词）** | **同"创建"处理：`date_range` = 当天，`filtering` 加 `adgroup.created_time` 范围，走路径 B** |
>    | "最近一周内创建且有投放数据的广告" | `date_range` = 最近7天，`filtering` 同时加 `adgroup.created_time` 范围 |
>    | "查看某个项目的历史数据" | `date_range` = 目标历史时间段，`filtering` 加 `adgroup.adgroup_id` |
>
>    **`created_time` 时间格式**：值为 `YYYY-MM-DD HH:mm:ss` 格式字符串（如 `"2026-03-21 00:00:00"`），脚本内部自动转为 API 所需的 Unix 时间戳。
>    ```json
>    // 示例：筛选 2026-03-21 00:00:00 ~ 2026-03-27 23:59:59 创建的项目
>    {"field": "adgroup.created_time", "operator": "GREATER_EQUALS", "values": ["2026-03-21 00:00:00"]},
>    {"field": "adgroup.created_time", "operator": "LESS_EQUALS",    "values": ["2026-03-27 23:59:59"]}
>    ```
>
> 6. **`report_only` 默认不要传**：`report_only: true` 表示仅查报表指标数据、不返回实体属性（广告名称、状态等）。只有在用户明确只需要效果数据（如"今天总消耗多少"）而不关心广告属性时才设为 `true`。**大多数查询都需要同时看到广告属性和报表数据，因此默认不传或设为 `false`。**

### time_line 时间口径枚举值

| 值 | 说明 |
|----|------|
| REQUEST_TIME | 广告播放口径（默认） |
| REPORTING_TIME | 转化回传口径 |
| ACTIVE_TIME | 激活时间口径 |

## 过滤条件（filtering）

### filtering 结构

```json
{
  "field": "过滤字段",
  "operator": "操作符",
  "values": ["值1", "值2"]
}
```

### 常用过滤字段

#### 广告层级（adgroup.*）

| 字段 | 说明 | 支持的操作符 |
|------|------|-------------|
| adgroup.adgroup_id | 广告 ID | EQUALS, IN |
| adgroup.fuzzy_name | 广告名称模糊搜索 | EQUALS |
| adgroup.operation_status | 运营状态 | EQUALS, IN |
| adgroup.system_status | 系统状态 | EQUALS, IN |
| adgroup.configured_status | 配置状态 | EQUALS, IN |
| adgroup.site_set | 版位 | EQUALS, IN, HAS_ANY |
| adgroup.created_time | 创建时间 | LESS, LESS_EQUALS, GREATER, GREATER_EQUALS |
| adgroup.campaign_type | 推广类型 | EQUALS |
| adgroup.brand_ad_type | 品牌广告类型 | EQUALS |
| adgroup.smart_delivery_platform | 智投平台版本 | EQUALS, IN, LESS, GREATER_EQUALS |
| adgroup.begin_date | 开始日期 | 时间戳操作符 |
| adgroup.end_date | 结束日期 | 时间戳操作符 |
| adgroup.optimization_goal | 优化目标 | - |
| adgroup.deep_optimization_goal | 深度优化目标 | - |

#### 动态创意层级（dynamic_creative.*）

| 字段 | 说明 | 支持的操作符 |
|------|------|-------------|
| dynamic_creative.dynamic_creative_id | 创意 ID | EQUALS, IN |
| dynamic_creative.fuzzy_name | 创意名称模糊搜索 | EQUALS |
| dynamic_creative.adgroup_id | 所属广告 ID | EQUALS, IN |
| dynamic_creative.operation_status | 运营状态（用于创意列表过滤，值同 adgroup.operation_status） | EQUALS, IN |
| dynamic_creative.system_status | 系统状态（见下方枚举值说明） | EQUALS, IN |
| dynamic_creative.delivery_mode | 投放模式：`DELIVERY_MODE_COMPONENT`（组件化创意）/`DELIVERY_MODE_CUSTOM`（自定义创意） | EQUALS, IN |
| dynamic_creative.source | 创意类型来源：`AD_CREATIVE_SOURCE_NORMAL`（客户自建创意）/`AD_CREATIVE_SOURCE_AUTO`（妙思自动生成） | EQUALS, IN |
| dynamic_creative.smart_delivery_platform | 智投平台版本（创意层级的智投/非智投区分，值同 adgroup.smart_delivery_platform） | EQUALS, IN, LESS, GREATER_EQUALS |
| dynamic_creative.created_time | 创建时间（Unix 时间戳） | LESS, LESS_EQUALS, GREATER, GREATER_EQUALS |
| dynamic_creative.brand_ad_type | 品牌广告类型 | EQUALS |

**`dynamic_creative.system_status` 枚举值说明**：

> 竞价广告（非智投）下的创意与智投项目下的创意，system_status 枚举值不同：

| 枚举值 | 适用场景 | 说明 |
|--------|---------|------|
| `DYNAMIC_CREATIVE_STATUS_PENDING` | 竞价广告创意 | 审核中 |
| `DYNAMIC_CREATIVE_STATUS_ACTIVE` | 竞价广告创意 | 投放中 |
| `DYNAMIC_CREATIVE_STATUS_SUSPEND` | 竞价广告创意 | 暂停 |
| `DYNAMIC_CREATIVE_STATUS_AUDIT_FAILED` | 竞价广告创意 | 审核不通过 |
| `DYNAMIC_CREATIVE_STATUS_DELETED` | 竞价广告创意 | 已删除 |
| `SMART_DYNAMIC_CREATIVE_STATUS_USING` | 智投项目创意 | 启用中 |
| `SMART_DYNAMIC_CREATIVE_STATUS_SUSPEND` | 智投项目创意 | 已暂停 |
| `SMART_DYNAMIC_CREATIVE_STATUS_DELETED` | 智投项目创意 | 已删除 |

#### 组件层级（component.*）

| 字段 | 说明 | 支持的操作符 |
|------|------|-------------|
| component.component_id | 组件 ID | EQUALS, IN, NOT_IN |
| component.component_type | 组件类型 | EQUALS, IN |
| component.fuzzy_name | 组件名称模糊搜索 | EQUALS |
| component.component_sub_type | 组件子类型 | EQUALS, IN |
| component.approval_status | 审核状态 | EQUALS, IN |
| component.operation_status | 运营状态 | EQUALS, IN |
| component.created_time | 创建时间（`YYYY-MM-DD HH:mm:ss` 格式，脚本自动转时间戳） | 时间操作符 |
| component.generation_type | 生成类型 | EQUALS, IN |
| component.quality_status | 质量状态 | EQUALS, IN |
| component.potential_status | 潜力状态 | EQUALS, IN |
| component.shared_account_id | 共享账户 ID | EQUALS, IN |
| component.scene | 场景 | EQUALS, IN |

#### 报表层级（report.*）

| 字段 | 说明 | 支持的操作符 |
|------|------|-------------|
| report.adgroup_id | 广告 ID | EQUALS, IN |
| report.dynamic_creative_id | 创意 ID | EQUALS, IN |
| report.component_id | 组件 ID | EQUALS, IN |
| report.component_type | 组件类型 | EQUALS, IN |
| report.image_id | 图片 ID | EQUALS, IN |
| report.video_id | 视频 ID | EQUALS, IN |
| report.marketing_asset_id | 产品 ID | EQUALS, IN |
| report.marketing_target_type | 营销目标类型 | EQUALS, IN |
| report.audience_id | 人群 ID | EQUALS, IN |
| report.landing_page_id | 落地页 ID | EQUALS, IN |
| report.brand_ad_type | 品牌广告类型 | EQUALS |
| report.campaign_type | 推广类型 | - |
| report.smart_delivery_platform | 智投平台版本 | EQUALS, IN, LESS, GREATER_EQUALS |
| report.creative_asset_id | 创意资产 ID | EQUALS, IN |

#### 素材层级

| 字段 | 说明 | 支持的操作符 |
|------|------|-------------|
| image.image_id | 图片 ID | EQUALS, IN |
| image.label_name | 图片标签 | EQUALS |
| video.video_id | 视频 ID | EQUALS, IN |
| video.label_name | 视频标签 | EQUALS |

#### 产品层级（marketing_asset.*）

| 字段 | 说明 | 支持的操作符 |
|------|------|-------------|
| marketing_asset.marketing_asset_id | 产品 ID | EQUALS, IN |
| marketing_asset.marketing_target_type | 营销目标类型 | EQUALS, IN |
| marketing_asset.fuzzy_name | 产品名称模糊搜索 | EQUALS |

### 后置过滤条件（post_filtering）

用于基于报表指标数值进行筛选，在数据返回后过滤。

支持的过滤字段：
- `report.cost` - 消耗
- `report.view_count` - 展示量
- `report.valid_click_count` - 有效点击量
- `report.conversions_count` - 转化数
- `report.conversions_cost` - 转化成本
- `report.conversions_rate` - 转化率

### 操作符说明

| 操作符 | 说明 |
|--------|------|
| EQUALS | 等于（单值匹配） |
| IN | 在列表中（多值匹配） |
| NOT_IN | 不在列表中 |
| LESS | 小于 |
| LESS_EQUALS | 小于等于 |
| GREATER | 大于 |
| GREATER_EQUALS | 大于等于 |
| CONTAINS | 包含 |
| HAS_ANY | 数组包含任意值 |

## 响应结构

```json
{
  "data": {
    "list": [
      {
        "account_id": 39412855,
        "account": { ... },
        "adgroup": {
          "adgroup_id": 123456,
          "adgroup_name": "广告名称",
          "configured_status": "AD_STATUS_NORMAL",
          "system_status": "ADGROUP_STATUS_NORMAL",
          ...
        },
        "dynamic_creative": { ... },
        "component": { ... },
        "bidword": { ... },
        "report": {
          "cost": 10000,
          "view_count": 50000,
          "valid_click_count": 1200,
          "ctr": "2.40",
          "conversions_count": 100,
          "conversions_cost": 10000,
          ...
        },
        "image": { ... },
        "media": { ... },
        "video": { ... },
        "marketing_asset": { ... },
        "joint_budget_rule": { ... },
        "product_catalog": { ... },
        "project_creative": { ... },
        "video_aggregation": { ... },
        "creative_asset": { ... },
        "jump_info": { ... }
      }
    ],
    "page_info": {
      "page": 1,
      "page_size": 20,
      "total_number": 150,
      "total_page": 8
    },
    "update_time": "2025-11-29 10:30:00"
  }
}
```

### list 每项返回结构

| 字段 | 类型 | 说明 |
|------|------|------|
| account_id | integer | 广告主帐号 ID |
| account | struct | 账户信息 |
| adgroup | struct | 广告属性（google_struct 动态字段） |
| dynamic_creative | struct | 动态创意属性 |
| component | struct | 组件属性 |
| bidword | struct | 竞价词属性 |
| report | struct | **报表指标数据**（google_struct 动态字段） |
| image | struct | 图片素材信息 |
| media | struct | 媒体信息 |
| video | struct | 视频素材信息 |
| marketing_asset | struct | 产品资产信息 |
| joint_budget_rule | struct | 联合预算规则信息 |
| product_catalog | struct | 商品信息 |
| project_creative | struct | 项目创意信息 |
| video_aggregation | struct | 视频聚合信息 |
| creative_asset | struct | 创意资产信息 |
| jump_info | struct | 跳转信息 |

## 常用 fields 字段

### 广告属性字段（adgroup.*）

| 字段 | 说明 |
|------|------|
| adgroup.adgroup_id | 广告 ID |
| adgroup.adgroup_name | 广告名称 |
| adgroup.is_deleted | 是否已删除 |
| adgroup.status | 广告状态 |
| adgroup.status_cn | 广告状态中文 |
| adgroup.configured_status | 配置状态（开/关） |
| adgroup.adgroup_status | 广告投放状态 |
| adgroup.system_status | 系统状态 |
| adgroup.system_status_cn | 系统状态中文 |
| adgroup.system_status_tips | 系统状态提示 |
| adgroup.optimization_goal | 优化目标 |
| adgroup.optimization_goal_cn | 优化目标中文 |
| adgroup.marketing_goal | 营销目的 |
| adgroup.marketing_goal_cn | 营销目的中文 |
| adgroup.marketing_target_type | 营销目标类型 |
| adgroup.marketing_target_type_cn | 营销目标类型中文 |
| adgroup.marketing_carrier_type | 营销载体类型 |
| adgroup.marketing_carrier_type_cn | 营销载体类型中文 |
| adgroup.promoted_object_type | 推广目标类型 |
| adgroup.promoted_object_type_cn | 推广目标类型中文 |
| adgroup.total_budget | 总预算 |
| adgroup.daily_budget | 日预算 |
| adgroup.bid_amount | 出价金额 |
| adgroup.bid_mode | 竞价模式 |
| adgroup.bid_scene | 竞价场景 |
| adgroup.billing_event | 计费事件 |
| adgroup.buying_type | 购买类型 |
| adgroup.begin_date | 开始日期 |
| adgroup.end_date | 结束日期 |
| adgroup.site_set | 版位 |
| adgroup.site_set_cn | 版位中文 |
| adgroup.smart_delivery_platform | 智投平台版本 |
| adgroup.smart_delivery_scene | 智投场景 |
| adgroup.smart_bid_type | 出价方式 |
| adgroup.smart_bid_type_cn | 出价方式中文 |
| adgroup.targeting_translation | 定向翻译 |
| adgroup.time_series | 投放时段 |
| adgroup.deep_conversion_spec | 深度转化规格 |
| adgroup.joint_budget_rule_id | 联合预算规则 ID |
| adgroup.marketing_asset_id | 营销资产 ID |
| adgroup.flow_lock_status | 锁量状态 |
| adgroup.exploration_strategy | 自动版位探索策略 |
| adgroup.automatic_site_enabled | 自动版位是否开启 |
| adgroup.dynamic_creative_id | 动态创意 ID |
| adgroup.placement_group_id | 版位组 ID |
| adgroup.display_id | 展示 ID |
| adgroup.adgroup_operation | 广告操作信息 |
| adgroup.ad_count | 广告数量 |
| adgroup.date_set | 日期设置 |
| adgroup.negative_word_cnt | 否定词数量 |
| adgroup.dynamic_ad_type | 动态广告类型 |
| adgroup.dynamic_ad_type_text | 动态广告类型文本 |
| adgroup.dynamic_creative_status_info | 动态创意状态信息 |
| adgroup.adcreative_preview_list | 创意预览列表 |
| adgroup.created_by_industry_platform | 行业平台创建标识 |
| adgroup.ad_created_source | 广告创建来源 |
| adgroup.search_intelligent_extension | 搜索智能拓展 |
| adgroup.live_video_mode | 直播视频模式 |
| adgroup.live_video_sub_mode | 直播视频子模式 |

### 报表指标字段（report.*）

> **完整字段列表见下方「字段字典参考 → 报表指标字典」**，此处仅列举最常用的字段：

**基础效果指标：**

| 字段 | 说明 |
|------|------|
| report.cost | 消耗（分） |
| report.view_count | 曝光量/展示量 |
| report.valid_click_count | 点击量/有效点击量 |
| report.ctr | 点击率（%） |
### 其他常用字段

| 字段 | 说明 |
|------|------|
| account_id | 广告主帐号 ID |

## 通用参数说明

以下公共约定由构建阶段自动内联：

以下内容为腾讯广告营销 API（`api.e.qq.com`）各 skill 共享的公共约定，会在构建阶段自动内联到目标 skill 文档中。各 skill 不需要重复这些内容。

## 基础信息

- **Base URL**: `https://api.e.qq.com`
- **认证方式**: API Key 鉴权（api.e.qq.com），授权请使用 `tencentads auth login`，状态查看使用 `tencentads auth status`
- **权限要求**: 需登录api.e.qq.com 并具有对应账户操作权限
- **时区**: GMT+8（北京时间）
- **金额单位**: 分（不是元），示例：`10000` 分 = `100` 元人民币
- **时间戳**: API 底层为秒级 Unix timestamp，但脚本统一使用 `YYYY-MM-DD HH:mm:ss` 格式（如 `"2026-03-18 00:00:00"`），脚本内部自动完成格式转换

## 调用方式

所有接口均通过 `tencent-ads` CLI 工具调用（agent 通过 bash 执行）。API Key 鉴权由 CLI 自动处理（通过 X-MKT-API-Key header），无需手动传入。

### GET 请求

```bash
tencentads-cli api '{
  "method": "GET",
  "path": "/v3.0/xxx/get",
  "account_id": "YOUR_ACCOUNT_ID",
  "params": {"page": 1, "page_size": 10}
}'
```

### POST 请求

```bash
tencentads-cli api '{
  "method": "POST",
  "path": "/v3.0/xxx/add",
  "account_id": "YOUR_ACCOUNT_ID",
  "body": {"account_id": 12345, "field1": "value1"}
}'
```

### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| method | string | 否 | GET 或 POST（默认 GET） |
| path | string | **是** | API 路径 |
| account_id | string | **是** | 广告账户 ID |
| params | object | 否 | GET 查询参数（JSON 对象） |
| body | object | 否 | POST 请求体（JSON 对象） |

> **严格规则**：调用任何接口时，**必须严格使用该接口文档中声明的 HTTP 方法（GET / POST）**，不得擅自更改。使用错误的请求方法会导致服务端返回 `405 Method Not Allowed`。

## 通用响应格式

所有接口返回的 JSON 响应都遵循以下格式：

```json
{
  "code": 0,
  "message": "",
  "message_cn": "",
  "data": {
    // 接口特定的响应数据
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| code | integer | 响应码，0 表示成功，非 0 表示错误 |
| message | string | 英文错误消息（成功时为空） |
| message_cn | string | 中文错误消息（成功时为空） |
| data | object | 响应数据对象 |

## 错误处理

`tencentads-cli api` 返回的 JSON 响应中包含 `code` 字段：
- `code` 为 0 表示成功
- `code` 非 0 时，检查 `message_cn` 获取中文错误说明

### 常见错误码

| 错误码 | 说明 | 处理方式 |
|--------|------|----------|
| 0 | 成功 | - |
| 3 | 参数错误 | 检查请求参数格式和必填项 |
| 5 | 权限不足 | 确认 API Key 有效且具有相应权限 |
| 6 | 系统错误 | 重试或联系技术支持 |
| 1001 | `timestamp` 超时 | 确保请求时间戳在当前时间 ±300 秒内 |
| 1002 | `nonce` 重复 | 使用新的随机字符串 |

## 数值单位说明

### 金额单位
- 所有涉及金额的字段（出价、预算等）单位均为**分**（不是元）
- 示例：`10000` 分 = `100` 元人民币
- 日预算范围：5000-400000000 分（50 元-400 万元）

### 时间单位
- 时间字段（`created_time`、`last_modified_time`、`completed_time`）：统一使用 `YYYY-MM-DD HH:mm:ss` 格式（如 `"2026-03-18 00:00:00"`），脚本内部自动与 API 的 Unix 时间戳互转
- 日期格式：`YYYY-MM-DD`
- 时间格式：`HH:ii:ss`
- 时区：`GMT+8`（北京时间）

## 分页参数

大多数列表查询接口支持以下分页参数：

### 标准分页

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| page | integer | 1 | 页码（1-100） |
| page_size | integer | 10 | 每页数量（1-100） |

### 游标分页

| 参数名 | 类型 | 说明 |
|--------|------|------|
| pagination_mode | enum | 分页方式：`PAGINATION_MODE_NORMAL`（标准）/ `PAGINATION_MODE_CURSOR`（游标） |
| cursor | string | 游标值，有效期 24 小时 |

### 分页响应

```json
{
  "page_info": {
    "page": 1,
    "page_size": 10,
    "total_number": 100,
    "total_page": 10
  }
}
```

## 过滤参数

大多数查询接口支持 `filtering` 参数进行条件过滤：

### filtering 结构

```json
{
  "filtering": [
    {
      "field": "字段名",
      "operator": "操作符",
      "values": ["值1", "值2"]
    }
  ]
}
```

### 操作符说明

| 操作符 | 说明 | 示例 |
|--------|------|------|
| EQUALS | 等于 | `{"field": "status", "operator": "EQUALS", "values": ["NORMAL"]}` |
| CONTAINS | 模糊匹配 | `{"field": "name", "operator": "CONTAINS", "values": ["测试"]}` |
| LESS | 小于 | `{"field": "created_time", "operator": "LESS", "values": ["2026-04-01 00:00:00"]}` |
| LESS_EQUALS | 小于等于 | `{"field": "created_time", "operator": "LESS_EQUALS", "values": ["2026-04-01 23:59:59"]}` |
| GREATER | 大于 | `{"field": "created_time", "operator": "GREATER", "values": ["2026-03-01 00:00:00"]}` |
| GREATER_EQUALS | 大于等于 | `{"field": "created_time", "operator": "GREATER_EQUALS", "values": ["2026-03-01 00:00:00"]}` |
| IN | IN 操作符 | `{"field": "id", "operator": "IN", "values": ["1", "2", "3"]}` |

## 最佳实践

1. **请求方法**：严格按照各接口文档声明的 HTTP 方法（GET/POST）发起请求，不得混用
2. **错误处理**：始终检查响应中的 `code` 字段
3. **重试机制**：对于系统错误（`code = 6`），可以实施指数退避重试
4. **API Key 如失效需重新配置
5. **分页处理**：对于大数据量查询，使用游标分页性能更好
6. **字段筛选**：使用 `fields` 参数只请求需要的字段，减少数据传输

## 字段字典参考

以下字典由构建阶段自动内联，包含所有可用字段的完整定义。

> **🚫 强制规则：遇到不在常用映射表中的字段名时，必须先查字典，禁止猜测！**
>
> 用户描述中提到的字段名称往往与 API 实际字段名差异很大，例如：
> - "AIGC 创意" → `smart_delivery_aigc_option`（而非 `aigc_creative`）
> - "锁量" → `flow_lock_status`（而非 `lock_status`）
> - "关注数" → `scan_follow_user_count`（而非 `wechat_official_account_follower_count`）
> - "5秒播放数" → 需查字典确认（而非 `video_play_5s_count`）
>
> 本文档不可能穷举所有字段，但 `adgroup-fields.json`（236 个字段）和 `report-fields.json`（854 个字段）中有完整的字段定义。
>
> **强制做法**：当用户提到的字段**不在上方「常用报表字段映射」或「常用 fields 字段」表中**时，**必须先用 `--query-fields` 查询字段字典**，确认正确字段名后再构造请求。**绝对禁止根据英文命名规律自行拼凑字段名。**
>
> 示例：用户说"帮我查询最近一周开启 AIGC 的广告"
> 1. 先查字典：`node scripts/query-adgroups.mjs --query-fields "aigc"`
> 2. 得到匹配字段（如 `smart_delivery_aigc_option`、`smart_delivery_aigc_creative` 等）
> 3. 再用正确的字段名构造查询请求的 `fields` 或 `filtering` 参数
>
> 示例：用户说"查看5秒播放数、关注数、关注成本"
> 1. 这些指标不在常用映射表中 → **必须查字典**
> 2. 执行：`node scripts/query-report.mjs --query-fields "5秒播放,关注"`
> 3. 从返回结果中确认准确字段名，再构造 `fields` 参数

### 广告字段字典（adgroup.*）

广告字段定义存储在 `resources/adgroup-fields.json` 中（共 236 个字段，按分类组织：定向设置、广告基本信息、营销配置、投放时间与预算、出价与优化、深度优化、一键起量、版位与场景定向、创意相关、转化与数据源、搜索定向、动态广告、其他、智投项目专有、报表广告维度属性、分页）。

**查询方式**：通过 `query-adgroups.mjs --query-fields [关键词]` 获取字段定义。

| 用法 | 说明 |
|------|------|
| `query-adgroups.mjs --query-fields` | 返回全部广告字段（字段名、类型、中文名、分类、说明） |
| `query-adgroups.mjs --query-fields "定向"` | 按分类/中文名过滤，返回定向相关字段 |
| `query-adgroups.mjs --query-fields "bid"` | 按字段名过滤，返回包含 bid 的字段 |
| `query-adgroups.mjs --query-fields "出价,预算,定向"` | 多关键词批量查询，逗号分隔，匹配任意一个即返回 |

**自动中文名附加**：`query-adgroups.mjs` 查询广告数据时，返回的每个字段自动附加中文名（如 `adgroup_name: "xxx"` 旁会有 `广告名称: "xxx"`），无需手动翻译。

### 报表指标字典（report.*）

报表指标字段定义存储在 `resources/report-fields.json` 中（共 854 个字段，按分类组织）。

**查询方式**：通过 `query-report.mjs --query-fields [关键词]` 获取字段定义。

| 用法 | 说明 |
|------|------|
| `query-report.mjs --query-fields` | 返回全部报表指标字段（字段名、类型、中文名、分类、说明） |
| `query-report.mjs --query-fields "视频"` | 按分类/中文名过滤，返回视频相关字段 |
| `query-report.mjs --query-fields "cost"` | 按字段名过滤，返回包含 cost 的字段 |
| `query-report.mjs --query-fields "cost,click,impression"` | 多关键词批量查询，逗号分隔，匹配任意一个即返回 |

> **⚠️ 强制使用场景**：只要用户提到的报表指标**不在「常用报表字段映射」表中**，就**必须**先用 `--query-fields` 查询字段字典，确认正确的 `report.*` 字段名后再构造查询请求。这是强制步骤，不可跳过。

## 分页信息

| 字段名 | 类型 | 中文名称 | 说明 |
|--------|------|----------|------|
| page_info | struct | 分页配置信息 | |
| page | integer | 搜索页码 | 默认值：1 |
| page_size | integer | 一页显示的数据条数 | 默认值：10 |
| total_number | integer | 总条数 | |
| total_page | integer | 总页数 | |

## 注意事项

1. **请求方式**: 该接口使用 **POST** 方法，参数放在请求体中（非 URL 参数）。

2. **fields 字段格式**: fields 中的字段使用 `对象.属性` 的格式，如 `adgroup.adgroup_id`、`report.cost`。顶层的 `account_id` 不带前缀。
   - **查询广告列表时**：fields 必须同时包含属性字段（如 `adgroup.*`）和报表字段（`report.*`），否则 report 会返回空对象。
   - **查询指定广告的分时/按天趋势时**：fields 只需包含用户关心的 `report.*` 指标即可。

3. **金额单位**: 所有金额字段单位为**分**。
   - 示例：`report.cost = 10000` 表示消耗 100 元
   - `adgroup.total_budget = 100000` 表示预算 1000 元

4. **日期范围**: 最早支持查询近 365 天的数据。`start_date` ≤ `end_date`，格式 `YYYY-MM-DD`。当天和昨天的日期均可使用。

5. **分页**: 支持大页面（page_size 最大 99999999），但建议按需设置合理的分页大小。数据量大时注意响应时间。

6. **report_only（慎用）**: 设为 `true` 时表示**仅查报表指标数据，不返回实体属性数据**（广告名称、状态、预算、出价等业务字段都不会返回）。适用场景：用户只需要效果数据（消耗、点击、转化等）而不关心广告属性信息，如纯数据汇总统计。**查询广告列表时应使用默认值 `false`（或不传此参数）**，以同时获取广告属性和报表数据。

> 7. **`group_by`（关键）**: 聚合参数决定了数据的汇总维度。**不传 group_by 会导致 report 返回空对象**。每个 level 的合法值和默认值见 **level 数据维度与 group_by 对应表**。

8. **二维过滤（or_filtering）**: 支持 OR 逻辑组合过滤。外层数组为 OR 关系，内层 `and_filtering` 数组为 AND 关系。

9. **常见的返回空数据原因排查**:
   - **`list` 返回空数组（`total_number: 0`）**：
     - **缺少 `smart_delivery_platform` 过滤或方向错误**（最常见原因）→ 智投和非智投必须分开查。**默认应用 `LESS`（查常规广告/非智投）。** 若用户明确要求查智投，用 `GREATER_EQUALS`。
     - 使用了 `report_only: true` 导致不返回实体属性数据 → **去掉 `report_only` 或设为 `false`**
     - `filtering` 其他条件过于严格 → 先用基础 3 条 + 智投/非智投过滤查询
   - **`report` 返回空对象（`report: {}`）**：
     - 缺少 `group_by` 参数 → 加上 `"group_by": ["adgroup_id"]`（列表查询）或 `["date", "hour"]`（分时查询）
     - 查询广告列表时缺少 `filtering` 参数 → 至少加上基础 3 条过滤 + 智投/非智投条件
     - 查询广告列表时 `fields` 只有 `report.*` 没有 `adgroup.*` → 补充属性字段
   - **以上各项需同时正确才能返回有效数据**

10. **🚫 禁止重复调用（极其重要）**：
    - **脚本调用成功返回了 `list` 数据（即使所有指标值为 0），说明参数正确、接口正常，应直接使用返回数据向用户展示，绝不要因为数据值全为 0 而反复修改参数重试。**
    - 数据值为 0 是正常的业务情况（如该日期没有投放、没有消耗等），不代表参数有误。
    - **区分"接口报错"和"数据为零"**：
      - 接口报错（返回 `error` 字段、HTTP 错误等）→ 检查参数后可重试 **1 次**
      - `list` 返回空数组（`total_number: 0`）→ 可按第 9 条排查后重试 **1 次**
      - `list` 有数据但 `report` 中的值为 0 → **这是正常结果，直接使用，禁止重试**
    - **严禁以下行为**：反复调整 `group_by`、`level`、`fields`、`is_total` 等参数尝试"修复"数据；绕过脚本直接调用底层 API；查看脚本源码试图排查问题。这些行为浪费大量步骤且不会改变结果。

---

## 脚本：query-adgroups.mjs

> **广告详情查询脚本**，用于获取广告的完整配置信息。

### 适用场景

- 需要查看广告的**详细配置**（定向、出价、转化规格、版位、投放时段等），而不仅是基本属性和报表数据
- 需要查看**已删除的广告**信息
- 需要根据**广告名称、状态、创建时间**等条件筛选广告
- 需要获取广告的**定向设置详情**（地域、年龄、性别、设备等）
- 需要查看广告的**深度转化规格**、**用户行为数据源**等高级配置

### 与 query-report.mjs 的区别

| 对比项 | query-report.mjs | query-adgroups.mjs |
|--------|-----------------|-------------------|

| 返回报表数据 | ✅ 返回消耗、曝光、点击等报表指标 | ❌ 不返回报表数据 |
| 返回配置详情 | ⚠️ 仅返回基本属性 | ✅ 返回完整配置（定向、出价、转化、版位等） |
| 需要日期范围 | ✅ 必填 | ❌ 不需要 |
| 支持跨账户 | ✅ 支持 | ❌ 单账户 |
| 查看已删除广告 | ❌ 不支持 | ✅ 支持 |
| 支持游标分页 | ❌ | ✅ 支持 |

### 调用方式

```bash
node scripts/query-adgroups.mjs '<JSON 参数>'
```

### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `account_id` | string | **是** | 广告主账号 ID |
| `tencent_ads_type` | enum | 否 | 广告实体类型，**枚举值只允许 `"smart"` / `"standard"` / `"all"` 三者之一**，默认 `"all"`。详见步骤 1.5 |
| `adgroup_ids` | string[] | 否 | 指定广告 ID 列表（按 ID 精确查询） |
| `fields` | string[] | 否 | 自定义返回字段（不传则使用默认字段集） |
| `filtering` | struct[] | 否 | 过滤条件数组 |
| `page` | integer | 否 | 页码，默认 1（最大 100） |
| `page_size` | integer | 否 | 每页条数，默认 10（最大 100） |
| `is_deleted` | boolean | 否 | 是否查询已删除广告，默认 false |
| `pagination_mode` | enum | 否 | 分页方式：`PAGINATION_MODE_NORMAL`（默认）/ `PAGINATION_MODE_CURSOR` |
| `cursor` | string | 否 | 游标值（配合游标分页模式使用） |

### 过滤条件（filtering）

| 字段 | 说明 | 支持的操作符 |
|------|------|-------------|
| `adgroup_id` | 广告 ID | EQUALS, IN（IN 时最多 100 个） |
| `adgroup_name` | 广告名称 | CONTAINS |
| `created_time` | 创建时间（`YYYY-MM-DD HH:mm:ss` 格式，脚本自动转时间戳） | GREATER, LESS, GREATER_EQUALS, LESS_EQUALS |
| `last_modified_time` | 最后修改时间（`YYYY-MM-DD HH:mm:ss` 格式，脚本自动转时间戳） | GREATER, LESS, GREATER_EQUALS, LESS_EQUALS |
| `configured_status` | 客户设置的状态 | EQUALS, IN |
| `material_package_id` | 素材包 ID | EQUALS |
| `joint_budget_rule_id` | 联合预算规则 ID | EQUALS |
| `auto_derived_creative_enabled` | 创意增强 MAX 开关 | EQUALS |
| `rta_target_id` | RTA 目标 ID | EQUALS |

### 使用示例

#### 1. 查询指定广告 ID 的详情（最常用）

```bash
node scripts/query-adgroups.mjs '{"account_id":"39412855","adgroup_ids":["72536365535"]}'
```

#### 2. 查询账户下所有广告列表

```bash
node scripts/query-adgroups.mjs '{"account_id":"39412855"}'
```

#### 3. 查询指定返回字段

```bash
node scripts/query-adgroups.mjs '{"account_id":"39412855","fields":["adgroup_id","adgroup_name","configured_status","targeting","bid_amount","daily_budget"]}'
```

#### 4. 根据广告名称模糊搜索

```bash
node scripts/query-adgroups.mjs '{"account_id":"39412855","filtering":[{"field":"adgroup_name","operator":"CONTAINS","values":["品牌推广"]}]}'
```

#### 5. 按状态筛选广告

```bash
node scripts/query-adgroups.mjs '{"account_id":"39412855","filtering":[{"field":"configured_status","operator":"EQUALS","values":["AD_STATUS_NORMAL"]}]}'
```

#### 6. 查询已删除的广告

```bash
node scripts/query-adgroups.mjs '{"account_id":"39412855","is_deleted":true}'
```

#### 7. 使用游标分页获取全量数据

```bash
# 第一次请求
node scripts/query-adgroups.mjs '{"account_id":"39412855","pagination_mode":"PAGINATION_MODE_CURSOR","page_size":100}'

# 后续请求（使用上一次返回的 cursor）
node scripts/query-adgroups.mjs '{"account_id":"39412855","pagination_mode":"PAGINATION_MODE_CURSOR","page_size":100,"cursor":"xxx"}'
```

#### 8. 按创建时间筛选（查最近 7 天创建的广告）

```bash
node scripts/query-adgroups.mjs '{"account_id":"39412855","filtering":[{"field":"created_time","operator":"GREATER_EQUALS","values":["2026-04-03 00:00:00"]}]}'
```

> `created_time` 支持 `YYYY-MM-DD HH:mm:ss` 格式，脚本自动转为 Unix 时间戳。也支持直接传时间戳。

### 返回结构

```json
{
  "list": [
    {
      "adgroup_id": 72536365535,
      "adgroup_name": "广告名称",
      "campaign_id": 12345,
      "configured_status": "AD_STATUS_NORMAL",
      "system_status": "ADGROUP_STATUS_NORMAL",
      "marketing_goal": "MARKETING_GOAL_PRODUCT_SALES",
      "bid_amount": 5000,
      "optimization_goal": "OPTIMIZATIONGOAL_ECOMMERCE_ORDER",
      "begin_date": "2026-03-20",
      "end_date": "2026-04-20",
      "daily_budget": 100000,
      "targeting": {
        "geo_location": { "regions": [110000, 310000] },
        "age": [{ "min": 18, "max": 45 }],
        "gender": ["MALE", "FEMALE"]
      },
      "site_set": ["SITE_SET_WECHAT"],
      "bid_mode": "BID_MODE_OCPM",
      "smart_bid_type": "SMART_BID_TYPE_CUSTOM",
      ...
    }
  ],
  "page_info": {
    "page": 1,
    "page_size": 10,
    "total_number": 50,
    "total_page": 5
  }
}
```

### 注意事项

1. **请求方式**: 该脚本使用 **GET** 方法。
2. **金额单位**: 所有金额字段单位为**分**（如 `bid_amount = 5000` 表示出价 50 元）。
3. **分页限制**: 普通分页模式下 `page` 最大 100，`page_size` 最大 100。需获取全量数据时推荐使用**游标分页模式**。
4. **字段选择**: 未指定 `fields` 时脚本自动使用默认字段集，覆盖基础信息、定向、出价、转化、智投项目配置（含周期达成、成本保障、直播加热等）等全量字段。如需查看特定字段，建议显式传入 `fields` 参数。
5. **与 query-report.mjs 配合**: 先用 `query-report.mjs` 获取广告列表和报表数据，找到感兴趣的广告后，再用 `query-adgroups.mjs` 查看其详细配置。

---

### 智能投放项目详情查询

> **智能投放项目复用了 adgroup（广告）的接口**，因此接口中的字段名与项目概念的对应关系如下：
>
> | 项目概念 | 接口字段 | 说明 |
> |---------|---------|------|
> | 项目 ID | `adgroup_id` | 智投项目 ID 对应接口中的广告 ID |
> | 项目名称 | `adgroup_name` | 智投项目名称对应接口中的广告名称 |
> | 项目状态 | `configured_status` / `system_status` | 项目的配置状态与系统状态 |
> | 项目预算 | `daily_budget` / `total_budget` | 项目日预算与总预算 |
> | 项目出价 | `bid_amount` | 项目出价对应接口中的广告出价 |
> | 项目创建时间 | `created_time` | 项目创建时间（返回 `YYYY-MM-DD HH:mm:ss` 格式） |
> | 项目修改时间 | `last_modified_time` | 项目最后修改时间（返回 `YYYY-MM-DD HH:mm:ss` 格式） |
>
> 其他字段也类同，接口层面项目与广告共用同一套数据结构，调用方式完全一致。

智能投放项目详情的获取使用 `query-adgroups.mjs` 脚本。脚本支持按需指定 `fields` 参数来获取所需字段；如果不指定 `fields`，脚本内置了覆盖智投项目全量配置的默认字段集（包括周期达成、成本保障、直播加热等），无需手动传入。

#### 使用示例

##### 1. 获取智能投放项目详情（使用默认字段，最常用）

```bash
node scripts/query-adgroups.mjs '{"account_id":"39412855","adgroup_ids":["72536365535"]}'
```

> 不指定 `fields` 时，脚本自动返回上述所有默认字段。

##### 2. 按需获取指定字段

```bash
node scripts/query-adgroups.mjs '{"account_id":"39412855","adgroup_ids":["72536365535"],"fields":["adgroup_id","adgroup_name","smart_delivery_platform","smart_delivery_scene","project_ability_list","smart_delivery_aigc_option","smart_targeting_status"]}'
```

> 只需要查看智投相关配置时，可以通过 `fields` 按需获取，减少返回数据量。

##### 3. 查询账户下所有智投项目详情

```bash
node scripts/query-adgroups.mjs '{"account_id":"39412855","page_size":100}'
```

##### 4. 按项目名称搜索智投项目详情

```bash
node scripts/query-adgroups.mjs '{"account_id":"39412855","filtering":[{"field":"adgroup_name","operator":"CONTAINS","values":["智投项目关键词"]}]}'
```

#### 智投项目专有字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| smart_delivery_platform | enum | 行业智投平台类型 |
| smart_delivery_scene | enum | 智投投放场景 |
| smart_delivery_scene_spec | struct | 场景化投放信息（含投放目标、转化 ID 列表等） |
| smart_delivery_aigc_option | enum | 智投 AIGC 选项 |
| smart_delivery_auto_creative | struct | 智投自动创意信息（含是否开启、供给策略、组件等） |
| smart_delivery_history_comp_reused_creative | struct | 智投历史组件复用创意 |
| smart_delivery_aigc_creative | struct | 智投 AIGC 创意配置 |
| smart_delivery_live_boost | enum | 直播加热 |
| smart_targeting_status | enum | 广告智能定向状态 |
| project_ability_list | array | 场景化投放原子能力列表 |
| project_ability_spec | struct | 场景化投放原子能力（含营销表达、优化出价） |
| boost_source_project_id | int64 | 加热源项目 ID |
| exploration_strategy | enum | 自动版位探索策略（自动版位开启时生效） |
| flow_lock_status | enum | 锁量状态 |
| aoi_optimization_strategy | struct | 高价值范围探索 |
| cost_guarantee_status | enum | 成本保障状态 |
| cost_guarantee_money | int64 | 成本保障赔付金额（单位：分） |
| expected_roi_mix_factor | float64 | 混变系数（0.0001~9999.9999） |
| smart_coupon_mode | enum | 小店智券开关 |
| auto_derived_creative_preference | struct | 创意增强 MAX 偏好设置 |
| enable_breakthrough_siteset | boolean | 是否支持版位突破 |
| live_recommend_strategy_enabled | boolean | 直播种草人群探索 |
| audience_model_bid_adjustment | struct | 后效建模优化功能 |
| additional_product_spec | struct | 附加商品属性 |
| incubation_optimization_goal | enum | 孵化优化目标 |
| conversion_name | string | 转化名称 |
| completed_time | integer | 广告总限额到达时间戳（unix 秒级） |
| smart_delivery_period_switch | enum | 周期达成 |
| smart_delivery_period_budget | integer | 周期预算（单位：分，0 表示不限） |
| smart_delivery_period_days | enum | 周期天数 |
| smart_delivery_period_continue | enum | 周期续投 |
| smart_delivery_period_begin_date | string | 周期开始日期 |
| smart_delivery_period_end_date | string | 周期结束日期 |

---

## 脚本：query-creatives.mjs

> **创意列表查询脚本**，用于获取创意的完整信息。

### 适用场景

- 需要查看广告下的**创意列表**及其组成结构（创意组件引用）
- 需要了解创意的**投放模式、创意类型、创意状态**等配置信息
- 需要查看创意中**组件的具体内容**（标题文案、描述文案、图片、视频等）
- 需要查看**已删除的创意**信息
- 需要根据**创意名称、广告 ID、创建时间**等条件筛选创意

### 与其他脚本的区别

| 对比项 | query-report.mjs | query-creatives.mjs |
|--------|-----------------|---------------------|
| 返回报表数据 | ✅ 返回消耗、曝光、点击等报表指标 | ❌ 不返回报表数据 |
| 返回创意组件详情 | ⚠️ 仅返回创意级别基本属性 | ✅ 返回完整的 creative_components 结构 |
| 自动解析组件内容 | ❌ | ✅ 自动拉取组件详情并内联 |
| 需要日期范围 | ✅ 必填 | ❌ 不需要 |
| 支持跨账户 | ✅ 支持 | ❌ 单账户 |
| 查看已删除创意 | ❌ 不支持 | ✅ 支持 |
| 支持游标分页 | ❌ | ✅ 支持 |

### 调用方式

```bash
node scripts/query-creatives.mjs '<JSON 参数>'
```

### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `account_id` | string | **是** | 广告主账号 ID |
| `tencent_ads_type` | enum | 否 | 广告实体类型，**枚举值只允许 `"smart"` / `"standard"` / `"all"` 三者之一**，默认 `"all"`。详见步骤 1.5 |
| `creative_ids` | string[] | 否 | 指定创意 ID 列表（按 ID 精确查询） |
| `adgroup_ids` | string[] | 否 | 按广告 ID 过滤创意 |
| `fields` | string[] | 否 | 自定义返回字段（不传则使用默认字段集） |
| `filtering` | struct[] | 否 | 过滤条件数组 |
| `page` | integer | 否 | 页码，默认 1（最大 100） |
| `page_size` | integer | 否 | 每页条数，默认 10（最大 100） |
| `is_deleted` | boolean | 否 | 是否查询已删除创意，默认 false |
| `pagination_mode` | enum | 否 | 分页方式：`PAGINATION_MODE_NORMAL`（默认）/ `PAGINATION_MODE_CURSOR` |
| `cursor` | string | 否 | 游标值（配合游标分页模式使用） |

### 过滤条件（filtering）

| 字段 | 说明 | 支持的操作符 |
|------|------|-------------|
| `dynamic_creative_id` | 创意 ID | EQUALS, IN（IN 时最多 100 个） |
| `dynamic_creative_name` | 创意名称 | CONTAINS |
| `adgroup_id` | 所属广告 ID | EQUALS, IN（IN 时最多 100 个） |
| `created_time` | 创建时间（`YYYY-MM-DD HH:mm:ss` 格式，脚本自动转时间戳） | GREATER, LESS, GREATER_EQUALS, LESS_EQUALS |
| `last_modified_time` | 最后修改时间（`YYYY-MM-DD HH:mm:ss` 格式，脚本自动转时间戳） | GREATER, LESS, GREATER_EQUALS, LESS_EQUALS |
| `configured_status` | 客户设置的状态 | EQUALS, IN |
| `source` | 创意来源 | EQUALS, IN |
| `component_id` | 组件 ID | EQUALS |
| `data_model_version` | 数据模型版本 | EQUALS |
| `smart_delivery_template_dc_id` | 智投模板创意 ID | EQUALS, IN |

### 返回的创意详情字段

#### 创意基础信息

| 字段 | 类型 | 说明 |
|------|------|------|
| dynamic_creative_id | integer | 创意 ID |
| dynamic_creative_name | string | 创意名称 |
| adgroup_id | int64 | 所属广告 ID（若 `smart_delivery_platform >= SMART_DELIVERY_PLATFORM_EDITION_SCENE` 则为**智能投放项目 ID**，展示时应标注"项目ID"；否则为**竞价广告 ID**，展示时标注"广告ID"） |
| smart_delivery_platform | enum | 智投平台版本，用于区分是否为智投广告。枚举值含义见下方说明 |
| creative_template_id | integer | 创意形式 ID |
| delivery_mode | enum | 投放模式 |
| dynamic_creative_type | enum | 动态创意类型 |
| configured_status | enum | 客户设置的状态（`AD_STATUS_NORMAL` / `AD_STATUS_SUSPEND`） |
| created_time | integer | 创建时间（时间戳） |
| last_modified_time | integer | 最后修改时间（时间戳） |
| is_deleted | boolean | 是否已删除 |

#### smart_delivery_platform 枚举值说明

| 艾米类型 | 场景 | 枚举值 | 是否智投 |
|----------|------|--------|---------|
| 默认 | 常规3.0广告（非智投） | `SMART_DELIVERY_PLATFORM_EDITION_STANDARD` | ❌ 否 |
| 小店艾米 | 短直双开智投 | `SMART_DELIVERY_PLATFORM_EDITION_WECHAT_STORE_SINGLE_PRODUCT` | ✅ 是 |
| 小店艾米 | 小店单链路智投 | `SMART_DELIVERY_PLATFORM_EDITION_WECHAT_STORE_PRODUCT_OR_LIVE` | ✅ 是 |
| 小店艾米 | 全店托管 | `SMART_DELIVERY_PLATFORM_EDITION_WECHAT_STORE_MANAGEMENT` | ✅ 是 |
| 小店艾米 | 推直播间 | `SMART_DELIVERY_PLATFORM_EDITION_WECHAT_STORE_LIVE` | ✅ 是 |
| 小店艾米 | 推商品 | `SMART_DELIVERY_PLATFORM_EDITION_WECHAT_STORE_PRODUCT` | ✅ 是 |
| 商品艾米 | 商品智投 | `SMART_DELIVERY_PLATFORM_EDITION_DRUG_PRODUCT` | ✅ 是 |
| 线索艾米 | 线索跑量 | `SMART_DELIVERY_PLATFORM_EDITION_ECOLOGY_LEADS` | ✅ 是 |
| 内容艾米 | 爆剧跑量 | `SMART_DELIVERY_PLATFORM_EDITION_ECOLOGY_PLAYLET` | ✅ 是 |
| 内容艾米 | 小说智投 | `SMART_DELIVERY_PLATFORM_EDITION_FICTION` | ✅ 是 |
| 内容艾米 | 小游戏跑量 | `SMART_DELIVERY_PLATFORM_EDITION_MINI_GAME_PROMOTION` | ✅ 是 |
| APP艾米 | 游戏应用智投 | `SMART_DELIVERY_PLATFORM_EDITION_GAME_APP` | ✅ 是 |
| APP艾米 | 阅读应用智投 | `SMART_DELIVERY_PLATFORM_EDITION_READING_APP` | ✅ 是 |
| APP艾米 | AI应用智投 | `SMART_DELIVERY_PLATFORM_EDITION_AI_APP` | ✅ 是 |
| APP艾米 | 游戏大推（即将下线） | `SMART_DELIVERY_PLATFORM_EDITION_BIG_GAME_PROMOTION` | ✅ 是 |
| - | 全域通-直播场景 | `SMART_DELIVERY_PLATFORM_EDITION_QYT_LIVE` | ✅ 是 |
| - | 全域通-直购场景 | `SMART_DELIVERY_PLATFORM_EDITION_QYT_WECHAT_STORE` | ✅ 是 |

> **判断规则**：`smart_delivery_platform` 为 `SMART_DELIVERY_PLATFORM_EDITION_STANDARD` 时为竞价广告（非智投），其余枚举值均为智投项目。
>
> **展示规则**：智投项目的 `adgroup_id` 展示为"项目ID"；竞价广告的 `adgroup_id` 展示为"广告ID"。

#### 创意组件（creative_components）

> **核心字段**：包含创意使用的所有组件引用信息。

`creative_components` 是一个 map 结构，key 为组件类型标识，value 为该类型的组件配置。常见的组件类型包括：

| 组件类型 | 说明 |
|---------|------|
| title | 标题 |
| description | 描述/文案 |
| image | 图片 |
| image_list | 图片列表（多图） |
| video | 视频 |
| brand | 品牌信息 |
| jump_info | 跳转链接/落地页 |
| action_button | 行动按钮 |
| consult | 咨询组件 |
| phone | 电话组件 |
| form | 表单组件 |
| label | 标签 |
| show_data | 数据展示 |
| marketing_pendant | 营销挂件 |
| floating_zone | 悬浮区域 |
| end_page | 结束页 |
| wechat_channels | 视频号组件 |
| short_video | 短视频组件 |
| element_story | 故事元素 |

每个组件通常包含 `component_id`（引用的组件 ID）。当查询结果只有 1 条创意时，脚本会自动拉取组件详情，并以 `_component_detail` 字段内联到各组件中，包含组件的实际内容（文案文本、图片 URL、视频 URL 等）。此外还会自动获取图片/视频的预览 URL，以 `_preview` 字段内联到对应素材中。

#### 其他字段

| 字段 | 类型 | 说明 |
|------|------|------|
| impression_tracking_url | string | 曝光监控地址 |
| click_tracking_url | string | 点击监控链接 |
| program_creative_info | struct | 程序化创意信息 |
| auto_derived_program_creative_switch | boolean | 自动生成更多素材开关 |
| marketing_asset_verification | struct | 资产验真信息 |
| creative_set_approval_status | enum | 创意审核状态 |
| asset_inconsistent_status | enum | 资产落地页一致性状态 |
| source_dynamic_creative_id | integer | 来源创意 ID |

### 使用示例

#### 1. 查询指定广告下的所有创意（最常用）

```bash
node scripts/query-creatives.mjs '{"account_id":"39412855","adgroup_ids":["72536365535"]}'
```

> 自动解析组件详情，返回创意完整信息 + 组件内容。

#### 2. 查询指定创意 ID 的详情

```bash
node scripts/query-creatives.mjs '{"account_id":"39412855","creative_ids":["98765432"]}'
```

#### 3. 查询账户下所有创意列表

```bash
node scripts/query-creatives.mjs '{"account_id":"39412855","page_size":20}'
```

#### 4. 按创意名称模糊搜索

```bash
node scripts/query-creatives.mjs '{"account_id":"39412855","filtering":[{"field":"dynamic_creative_name","operator":"CONTAINS","values":["品牌推广"]}]}'
```

#### 5. 查询已删除的创意

```bash
node scripts/query-creatives.mjs '{"account_id":"39412855","is_deleted":true}'
```

#### 7. 使用游标分页获取全量创意

```bash
# 第一次请求
node scripts/query-creatives.mjs '{"account_id":"39412855","pagination_mode":"PAGINATION_MODE_CURSOR","page_size":100}'

# 后续请求（使用上一次返回的 cursor）
node scripts/query-creatives.mjs '{"account_id":"39412855","pagination_mode":"PAGINATION_MODE_CURSOR","page_size":100,"cursor":"xxx"}'
```

#### 8. 指定返回字段

```bash
node scripts/query-creatives.mjs '{"account_id":"39412855","fields":["dynamic_creative_id","dynamic_creative_name","adgroup_id","creative_components","configured_status"]}'
```

### 返回结构

```json
{
  "list": [
    {
      "dynamic_creative_id": 98765432,
      "dynamic_creative_name": "创意名称-横版视频",
      "adgroup_id": 72536365535,
      "creative_template_id": 1708,
      "delivery_mode": "DELIVERY_MODE_DEFAULT",
      "dynamic_creative_type": "DYNAMIC_CREATIVE_TYPE_NORMAL",
      "creative_components": {
        "title": [{
          "component_id": 11111,
          "_component_detail": {
            "component_id": 11111,
            "component_value": {
              "title": { "content": "这是标题文案" }
            },
            "component_sub_type": "TITLE",
            "component_custom_name": "品牌标题"
          }
        }],
        "description": [{
          "component_id": 22222,
          "_component_detail": {
            "component_id": 22222,
            "component_value": {
              "description": { "content": "这是描述文案" }
            },
            "component_sub_type": "DESCRIPTION"
          }
        }],
        "video": [{
          "component_id": 33333,
          "_component_detail": {
            "component_id": 33333,
            "component_value": {
              "video": {
                "video_id": "abc123",
                "_preview": {
                  "video_id": "abc123",
                  "preview_url": "https://example.com/video_preview.mp4",
                  "key_frame_image_url": "https://example.com/keyframe.jpg",
                  "width": 1280,
                  "height": 720
                }
              }
            },
            "component_sub_type": "VIDEO"
          }
        }],
        "image": [{
          "component_id": 44444,
          "_component_detail": {
            "component_id": 44444,
            "component_value": {
              "image": {
                "image_id": "def456",
                "_preview": {
                  "image_id": "def456",
                  "preview_url": "https://example.com/image_preview.jpg",
                  "width": 800,
                  "height": 600
                }
              }
            },
            "component_sub_type": "IMAGE"
          }
        }]
      },
      "configured_status": "AD_STATUS_NORMAL",
      "created_time": 1742860800,
      "last_modified_time": 1742947200,
      "is_deleted": false
    }
  ],
  "page_info": {
    "page": 1,
    "page_size": 10,
    "total_number": 1,
    "total_page": 1
  }
}
```

> **`_component_detail` 字段**：当查询结果只有 1 条创意时，脚本自动为每个包含 `component_id` 的组件引用附加 `_component_detail` 字段，其中包含完整组件信息。
>
> **`_preview` 字段**：对于组件中包含 `image_id` 或 `video_id` 的素材，脚本自动获取预览信息（`preview_url`、尺寸等），以 `_preview` 字段内联到对应素材对象中。

### 注意事项

1. **请求方式**: 该脚本使用 **GET** 方法。
2. **组件自动解析**: 当查询结果只有 1 条创意时，脚本自动解析组件详情并获取图片/视频预览 URL，无需额外配置。多条创意时不解析组件，避免大量 API 请求影响性能。
3. **分页限制**: 普通分页模式下 `page` 最大 100，`page_size` 最大 100。需获取全量数据时推荐使用**游标分页模式**。
4. **与 query-report.mjs 配合**: 先用 `query-report.mjs` 获取创意级别的报表数据（level: DYNAMIC_CREATIVE），找到需要查看详情的创意后，再用 `query-creatives.mjs` 传入 `creative_ids` 查看其完整组件内容。
5. **与 query-adgroups.mjs 配合**: 先用 `query-adgroups.mjs` 获取广告详情，再用 `query-creatives.mjs` 按 `adgroup_id` 查询该广告下的所有创意。
6. **展示 adgroup_id 时区分广告/项目**：返回数据中的 `adgroup_id` 根据 `smart_delivery_platform` 字段决定展示名称：
   - `EDITION_SCENE` 或 `EDITION_SCENE_PRO` → 展示为**项目ID**（智能投放项目）
   - `EDITION_STANDARD` 或 `EDITION_NONE`（或字段缺失）→ 展示为**广告ID**（竞价广告）
7. **⚠️ 预览 URL 必须展示（强制）**：脚本返回的 `_preview.preview_url`（视频/图片预览链接）和 `_cover_preview.preview_url`（封面预览链接）**必须在回复中以可点击链接的形式呈现给用户**，不得省略或忽略。具体规则：
   - 视频组件：展示视频 `preview_url`（🎥 视频预览链接）和封面 `preview_url`（🖼️ 封面链接）
   - 图片组件：展示图片 `preview_url`（🖼️ 图片预览链接）
   - 每个素材组件单独列出，用 Markdown 链接格式 `[描述](URL)` 呈现
   - **绝对禁止**因内容过长、信息繁杂等原因而省略预览 URL

---

## 脚本：关键词管理（bidword）

管理广告的关键词（竞价词）。关键词用于搜索扩量场景，当广告开启搜索扩量（`search_expansion_switch = SEARCH_EXPANSION_SWITCH_OPEN`）后，可为广告设置搜索关键词。

> 详细参数、示例和返回值见 [references/bidword.md](references/bidword.md)

| 脚本 | 功能 | 必填参数 |
|------|------|---------|
| `scripts/bidword/add.mjs` | 创建关键词 | account_id, list[{adgroup_id, bidword, match_type}] |
| `scripts/bidword/update.mjs` | 更新关键词 | account_id, list[{bidword_id, ...}] |
| `scripts/bidword/delete.mjs` | 删除关键词 | account_id, list (bidword_id 数组) |
| `scripts/bidword/get.mjs` | 查询关键词 | account_id |

---

## 脚本：否定词管理（adgroup_negativewords）

管理广告组级别的否定关键词。否定词用于排除不相关的搜索词，避免广告在不相关的搜索结果中展示。

> 详细参数、示例和返回值见 [references/negativewords.md](references/negativewords.md)

| 脚本 | 功能 | 必填参数 |
|------|------|---------|
| `scripts/negativewords/add.mjs` | 新增否定词 | account_id, adgroup_id, phrase_negative_words, exact_negative_words |
| `scripts/negativewords/update.mjs` | 更新否定词（全量替换） | account_id, adgroup_id, phrase_negative_words, exact_negative_words |
| `scripts/negativewords/get.mjs` | 查询否定词 | account_id, adgroup_ids |

---

## 推广内容资产管理

创建和查询推广内容资产（marketing_asset）。**执行前必须先读取** [references/marketing-asset/overview.md](references/marketing-asset/overview.md)。

> 详细流程说明（CPV/SPU/电商分类、创建步骤、参数说明、约束等）见 [references/marketing-asset/overview.md](references/marketing-asset/overview.md)

---

## 相关技能

- **tencentads-adgroups** - 管理广告（创建/更新/删除广告）
- **tencentads-delivery-smart** - 智投选参指南（智投报表需与非智投分开查询）
- **tencentads-delivery-standard** - 常规投放选参指南
- **tencentads-creatives** - 管理动态创意
- **tencentads-components** - 管理创意组件
- **tencentads-batch** - 批量调整广告
- **tencentads-materials** - 管理素材
