---
name: starrocks-business-analysis-sly
description: "该技能用于通过 MCP 查询餐饮企业门店经营数据，涵盖门店画像、营收客流、优惠结算、菜品套餐、渠道来源、员工绩效、运营效率、会员分析、供应链进销存等多维分析，支持跨品牌跨区域对比。典型场景：查门店列表/营收排名/客单价/翻台率/优惠占比/套餐占比/小程序渠道/服务员排名/环比同比/会员消费排行/复购留存/积分流转/优惠券核销/RFM分层/采购分析/耗用分差/毛利/进销存/盘点差异等。"
description_zh: "商龙餐饮经营数据分析技能，覆盖门店画像、营收排名、客单价、翻台率、优惠占比、菜品分析、渠道占比、员工绩效、环比同比、会员消费排行、复购留存、积分流转、供应链原物料等 78 个分析意图"
description_en: "Shanlong Catering Business Insights skill. Queries StarRocks data warehouse covering store profiles, revenue, customer flow, discounts, dishes, channels, staff performance, efficiency, member analytics, and supply chain across 78 analysis intents."
version: "1.0.149"
author: "Shanlong Tech"
---

# starrocks-business-analysis-sly

## 快速导航

| 模块 | 文件 | 说明 |
|------|------|------|
| Intent 速查 | [intents/_index.md](intents/_index.md) | 78 个 Intent 一览表（编号 1-50、76-103，其中 51-75 保留） |
| **🏪 门店画像**（Intent 1-5） | [intent-01-store-profile.md](intents/intent-01-store-profile.md) | 门店列表、地理分布、品牌排名、管理类型、规模 |
| **💰 营收分析**（Intent 6-9） | [intent-02-revenue.md](intents/intent-02-revenue.md) | 营收趋势、门店排名、品项原价、坪效 |
| **👥 客流与客群**（Intent 10-14） | [intent-03-customer-flow.md](intents/intent-03-customer-flow.md) | 销售渠道、场景、来源、客群、翻台率、续单 |
| **🎁 优惠与结算**（Intent 15-19） | [intent-04-discount.md](intents/intent-04-discount.md) | 优惠折扣、服务费、押金、签单、发票 |
| **🍽️ 菜品与套餐**（Intent 20-22） | [intent-05-dishes.md](intents/intent-05-dishes.md) | 套餐、会员、退菜分析（账单层） |
| **📱 渠道与来源**（Intent 23-24） | [intent-06-channel.md](intents/intent-06-channel.md) | 小程序渠道、订单类型 |
| **👨‍🍳 员工绩效**（Intent 25-27） | [intent-07-staff-performance.md](intents/intent-07-staff-performance.md) | 服务员、收银员、业务员绩效 |
| **⏱️ 运营效率**（Intent 28-32） | [intent-08-efficiency.md](intents/intent-08-efficiency.md) | 时段、天气、出品、用餐时长、评分 |
| **📊 多维对比**（Intent 33-41） | [intent-09-multi-dimension.md](intents/intent-09-multi-dimension.md) | 环比、同比、跨维度、直营加盟、区域品牌、桌区 |
| **🥩 菜品明细分析**（Intent 42-50） | [intent-10-item-analysis.md](intents/intent-10-item-analysis.md) | 菜品排行、大类占比、套餐、毛利、退菜、渠道品项、赠送分析 |
| **🏅 会员分析**（Intent 76-94） | [intent-11-member.md](intents/intent-11-member.md) | 会员概况、消费排行、复购留存、充值积分、优惠券、价值分层 |
| **💳 会员卡型分析**（Intent 95-97） | [intent-11-member.md](intents/intent-11-member.md) | 卡型分布、跨品牌多卡、余额分布/沉睡资金 |
| **📦 供应链原物料**（Intent 98-103） | [intent-12-scm.md](intents/intent-12-scm.md) | 采购分析、耗用分差、毛利、进销存、盘点差异、趋势 |
| 安全规则 | [rules/security-rules.md](rules/security-rules.md) | 权限检查清单 |
| 输出规范 | [rules/output-format.md](rules/output-format.md) | 输出格式标准 |
| Intent 未命中 | [rules/intent-fallback.md](rules/intent-fallback.md) | 5级降级处理 |
| **参数缺失补全** | [rules/param-fallback.md](rules/param-fallback.md) | `#{变量名}` 占位符按需预查询补全与失败处理 |
| **🏪 门店编码获取 CLI** | [rules/param-fallback.md](rules/param-fallback.md#八门店编码获取-cli用户指定门店时使用) | `sl store find` 名称 → omShopCode 解析 |
| 表结构 | [references/table-schema.md](references/table-schema.md) | 数据表速查 |

---

## 用途

当用户提出以下需求时启用本技能：

| 分类 | 业务说明 | 典型问题 |
|------|----------|----------|
| 🏪 门店画像 | 静态基础信息 | 有多少门店、在哪、什么品牌 |
| 💰 营收分析 | 收入核心指标 | 营收多少、最赚钱是哪家 |
| 👥 客流与客群 | 人从哪来、多少人 | 外卖占比、客单价、翻台率 |
| 🎁 优惠与结算 | 省多少钱、怎么结账 | 优惠多少、押金、签单、发票 |
| 🍽️ 菜品与套餐 | 卖什么、点什么 | 套餐占比、会员消费、退菜分析 |
| 📱 渠道与来源 | 线上还是线下 | 小程序占比、订单类型 |
| 👨‍🍳 员工绩效 | 谁干得好 | 服务员/收银员/业务员排名 |
| ⏱️ 运营效率 | 快不快、好不好 | 用餐时长、出品速度、评分 |
| 📊 多维对比 | 交叉、趋势、对比 | 环比同比、区域品牌对比 |
| 🥩 菜品明细分析 | 品项销售/毛利/退菜/渠道 | 畅销菜、毛利率、套餐排行、退菜品项 |
| 🏅 会员分析 | 会员消费/充值/积分/优惠券 | 高价值会员、复购率、留存率、积分流转、优惠券核销、价值分层 |
| 💳 会员卡型 | 卡型结构/多卡会员/余额分布 | 卡型占比、跨品牌多卡、储值余额、积分沉淀、沉睡资金 |
| 📦 供应链原物料 | 库存/采购/耗用/毛利 | 库存现状、采购占销比、耗用分差、毛利率、进销存、盘点差异、周转天数 |

---

## ⚠️ 执行前必读（AI 行为约束）

### 🔐 权限机制

> 🔐 **插值机制**：在 SQL 语句中使用 `#{变量名}` 占位符，系统会在执行前自动将变量值插入 SQL 中。**所有 7 张业务表统一使用一套编码**：

| 变量名 | 对应表.字段 | 说明 | 示例值 |
|--------|------------|------|--------|
| `#{SL_UNIFIED_G_ID}` | `group_code`（**所有 7 张表统一**） | 集团 G 号（商龙云统一集团编码） | `G137427` |
| `#{omShopCodes}` | `store_code`（**所有 7 张表统一**） | 门店 C 号（商龙云统一门店编码列表，逗号分隔） | `'C273353','C273354',...` |
| `#{omShopCodeOrgNameMap}` | — | 门店码→门店名映射（辅助信息） | `{"C273353":"张福记陇海店",...}` |

**SQL 占位符写法示例**：

```sql
-- ✅ 正确：用 #{变量名} 占位符，由系统自动插入
WHERE group_code = '#{SL_UNIFIED_G_ID}'                       -- 单值占位符
  AND store_code IN (#{omShopCodes})                      -- 多值列表占位符（字面插入）

-- ❌ 错误：硬编码具体值（绝对禁止）
WHERE group_code = 'G137427'                              -- 禁止硬编码集团码
  AND store_code IN ('C273353', 'C273354', 'C273355')     -- 禁止硬编码门店码
```

**关键约束**：
- **AI 永不接触真实值**：SQL 模板中只出现 `#{变量名}`，真实 G 号 / 门店列表由系统注入，AI 不在对话或代码中暴露具体值
- **变量来源**：`#{SL_UNIFIED_G_ID}` / `#{omShopCodes}` / `#{omShopCodeOrgNameMap}` 的真实值由机器人配置层（典型实现如 `token.json` 的 `biz_params` 字段）提供，AI **不接触**真实值
- **跨集团零容忍**：禁止试图查询配置外的集团 / 门店，若用户要求越权查询应直接拒绝

> ✅ **统一编码原则**：7 张表（`e000.dt_store_view` / `dm.v_pos_corp_sale_analysis_with_sly` / `dm.v_item_sale_analysis_with_sly` / `dm.dm_crm_card_sum_day_p_store` / `dm.v_crm_member_with_sly` / `dw.dwd_crm_member_card_p_with_sly` / `dm.dm_ljc_scm8_store_rm_item_consume_analysis_day_p_group_view`）均含 `group_code` + `store_code` 字段，且分别代表**集团 G 号**和**门店 C 号**。**所有表可直接通过 `group_code` + `store_code` 关联**，无需任何多码映射。
>
> 💡 `e000.dt_store_view` 同时保留 `cy_store_code`（餐饮门店编号）和 `cy_group_code`（餐饮集团编号），仅作为历史/对账用途，业务查询统一使用 `group_code` + `store_code`。

### 🔐 安全规则

> 详见 [rules/security-rules.md](rules/security-rules.md)

核心约束速览：

| 约束项 | 要求 |
|--------|------|
| **单轮查询上限** | 每轮最多执行 **10 次** `sl starrocks read-query`，超限立即停止并报告；命中 Intent 且槽位齐全时目标 ≤ **2** 次（含可选轻量探活） |
| **空结果分类** | 类型 A（参数构造问题）允许修正后重试 **1 次**；类型 B（数据不存在）**强制停止** |
| **MCP 探活** | **禁止**会话初全表 `COUNT(*)`；正常首问直接业务 SQL。仅当首条业务 SQL 报连接/表不存在类错误时，再跑带 `group_code`+`store_code`+近 30 天日期的 `SELECT 1 ... LIMIT 1`；POS 探活无行**不**判 MCP 空库 |
| **group_code 强制注入** | **所有 SQL 的 WHERE 条件中必须包含 `group_code` 过滤**，具体值由机器人配置层通过 `#{SL_UNIFIED_G_ID}` 占位符注入，AI 不得省略、不得硬编码、不得跨集团查询 |
| **group_code / store_code 值范围强制校验** ⚠️ | SQL 中出现的 `group_code` / `store_code` 值**必须 100% 来自 `#{SL_UNIFIED_G_ID}` / `#{omShopCodes}` 占位符的注入值**，AI 不得私自添加、枚举、或推断任何不在占位符范围内的值（含硬编码、额外 OR 条件、子查询返回非授权值） |
| **store_code 始终启用** | 所有 SQL 的 WHERE 中**必须**包含 `store_code IN (#{omShopCodes})`（无例外）；`#{omShopCodes}` 的值分两种场景：① 用户未指定门店 → 取 token 默认全部门店码列表；② 用户明确指定门店 → 先 `sl store find` 获取 `omShopCode`，更新 `#{omShopCodes}` 值后再执行 SQL |
| **禁止跨集团搜索** | 只能查当前 token 中的 group_code，禁止越权 |
| **禁止无日期范围查询** | 营业表必须指定 `settle_biz_date` 范围，否则拒绝执行 |
| **禁止无 LIMIT 查询** | 营业表查询必须带 LIMIT，防止全表扫描 |

> 💡 空结果标准回复模板、MCP 异常回复模板、类型 A/B 完整规则 → 详见 [rules/security-rules.md](rules/security-rules.md)

### 🔗 编码预查规则（按需补全策略）

> 💡 `#{SL_UNIFIED_G_ID}` / `#{omShopCodes}` 占位符的真实值通常由机器人配置层（典型实现如 `token.json` 的 `biz_params` 字段）提供，**优先直接使用**。  
> 正常运行时 `#{omShopCodes}` 始终由系统注入；仅在配置异常导致其缺失或为空时，才按以下规则尝试预查补全。补全失败时必须停止并提示修复配置，**不得**省略 `store_code IN (#{omShopCodes})` 执行集团级查询。

#### 按需预查补全规则

| 缺失参数 | 必填前置参数 | 补全 SQL（简化版） | 失败处理 |
|---------|------------|-----------------|--------------|
| `omShopCodes` | 有 `#{SL_UNIFIED_G_ID}` | `SELECT CONCAT("'", GROUP_CONCAT(DISTINCT store_code SEPARATOR "','"), "'") FROM dm.v_pos_corp_sale_analysis_with_sly WHERE group_code = '#{SL_UNIFIED_G_ID}' AND settle_biz_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY) LIMIT 1` | 🛑 停止执行，提示用户修复 `omShopCodes` 门店权限配置；不得去掉 `store_code` 过滤 |
| `SL_UNIFIED_G_ID` | 无前置可用 | — | ⚠️ 拒绝执行，提示用户配置 `SL_UNIFIED_G_ID` 后再查询 |

> ⚠️ **POS 视图 40 亿行**，预查必须带 **近 30 天日期窗口**（`settle_biz_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)`），否则超时。

#### 最低门槛检查（核心参数全缺时）

若 `SL_UNIFIED_G_ID` 缺失或为空：

> ⚠️ 当前账号未配置集团编码权限，无法执行数据查询。请联系管理员在机器人配置中添加 `SL_UNIFIED_G_ID` 参数。

> 💡 详细补全逻辑与降级行为 → [rules/param-fallback.md](rules/param-fallback.md)

### 🏪 门店编码获取 CLI（用户指定门店时必走）

> 🎯 **触发条件**：用户输入中**明确出现**门店名称 / 简称 / 别名 / 门店 ID 时，必须先调用 `sl store find` 获取标准 `omShopCode`，再用于 SQL 拼接。
> **不触发**：用户问"集团/全部门店"等无具体门店指向的查询时跳过此步，直接用 token 默认权限。

#### 命令格式

> 路径见「CLI 入口」；Bash 下一键兼容：

```bash
SL="$HOME/.slclaw/bin/sl"; [ -f "$HOME/.slclaw/bin/sl.cmd" ] && SL="$HOME/.slclaw/bin/sl.cmd"

# 按名称查询
"$SL" store find --type crm --name "<门店关键词>" --format json

# 按关键词 / 门店 ID 混合查询
"$SL" store find --type crm --keyword "<门店关键词或门店ID>" --format json
```

#### 返回结果判定规则

CLI 返回 **门店候选 JSON 数组**，每条候选含：

| 字段 | 用途 |
|------|------|
| `omShopCode` | **后续 `omShopCodes` 参数的取值**（门店 C 号） |
| `orgName` | 向用户展示的门店名称（消歧用） |

| 命中数 | AI 行为 |
|--------|--------|
| 0 条（空数组） | 🛑 停止，提示「未找到匹配门店」 |
| 1 条 | ✅ 直接使用该 `omShopCode`，无需确认 |
| ≥ 2 条 | ⚠️ **列表展示让用户确认**，**禁止静默选第一条** |

#### Token 缺门店清单降级

CLI 提示 token 缺门店清单（如 `token missing store list`）时：

1. 先执行 `sl token refresh dc` 刷新门店权限
2. **重试一次**同一条 `sl store find`
3. 仍失败 → 按"未找到门店"模板告知用户

> 💡 完整 CLI 说明、消歧模板、流程图、与 SQL 预查补全的对比 → [rules/param-fallback.md#八门店编码获取-cli用户指定门店时使用](rules/param-fallback.md#八门店编码获取-cli用户指定门店时使用)

### 🔒 安全规则（违反则拒绝执行）

| 检查项 | 要求 | 违规处理 |
|--------|------|----------|
| **group_code 强制过滤** | 所有 SQL 的 WHERE 必须含 `group_code`，值由配置层注入 | 拒绝执行，补全后重试 |
| **store_code 归属** | 只能查询机器人配置层配置的门店 | 过滤无效门店，拒绝越权查询 |
| **禁止跨集团搜索** | 安全要求（C5-02） | 拒绝执行，提示权限不足 |
| **禁止暴露其他集团** | 安全要求（C5-01） | 拒绝执行，提示权限不足 |
| **日期范围** | 用户必须指定起止日期 | 未指定则询问，拒绝全量查询 |
| **LIMIT 上限** | 强制要求防止全表扫描 | 拒绝无上限查询 |

> 💡 详细检查逻辑 → [rules/security-rules.md](rules/security-rules.md)

### 📋 输出规范（每次查询必须执行）

| 规范项 | 要求 |
|--------|------|
| **数据范围说明** | **必须**在结果末尾附上（见下方模板） |
| **输出格式** | **必须**使用 output-format.md 中的标准格式 |
| **信息安全** | **禁止**在结果中暴露 SQL 参数或内部实现 |

#### 数据范围说明模板（每次必须附加）

```
---
📊 数据范围：{start_date} ~ {end_date} | 【集团名称】
💡 提示：数据为 T-1 日结，今日实时数据暂不可用
💡 仅显示您权限范围内的数据
```

---

## 极简执行路径（积分优先）

> ⚡ **首问默认走本路径。** WorkBuddy 积分按轮次/工具调用计费；禁止探索性绕路。

对「已命中 Intent 且槽位齐全」的问法，强制：

1. 用「CLI 入口」的 **Bash 一键兼容** 调用（自动选 Windows `sl.cmd` / macOS `sl`），**禁止** `which` / `where` / Bash 内 `%USERPROFILE%\...`
2. 只打开 [`intents/_index.md`](intents/_index.md) → **对应 1 个** intent 文件（禁止扫全部分类文档）
3. 套模板拼 **1 条** SQL（含 `group_code` / `store_code` / 日期 / LIMIT）
4. 用上述绝对路径执行 **1 次** `starrocks read-query`（优先 Bash，勿先绕 PowerShell）
5. 单轮目标：业务查询 ≤ **2** 次 CLI（第 2 次仅用于类型 A 修正重试，或连接失败后的轻量探活）

**明确禁止**：找 path、Bash 写 `%USERPROFILE%\...`、未命中前通读全部 intent、会话初全表 `COUNT(*)`、用 Python/Node 脚本转发查询。

---

## 执行流程

```
路径固定（Bash 一键兼容绝对路径，禁止 which/where / 禁止 %USERPROFILE%\...）
    ↓
用户输入
    ↓
1️⃣ 识别 Intent & 提取 Slot（只读 _index → 1 个 intent 文件）
    ↓
1.5️⃣ 门店识别（**用户明确指定门店名称/简称/别名/门店 ID 时必走**）
    → 调用 `sl store find` 把门店名 → omShopCode
    → 0 候选：停止并提示
    → 1 候选：直接使用，**更新** `#{omShopCodes}` 值为该门店码
    → ≥2 候选：列表让用户确认（禁止静默选第一条），**更新** `#{omShopCodes}` 值为用户确认的门店码
    → token 缺清单：先 `sl token refresh dc` 再重试一次
    → 用户未指定门店：跳过此步，`#{omShopCodes}` 保持 token 默认全部门店码
    ↓
2️⃣ 日期范围检查（仅营业表，未指定则询问）
    ↓
3️⃣ 参数按需补全检查（仅占位符缺失时）
    → 构建 SQL 前检查当前 Intent 所需 `#{变量名}` 是否可用
    → 若缺失：执行对应预查 SQL 补全（见「🔗 编码预查规则」章节）
    → 补全失败：停止执行并按 `rules/param-fallback.md` 提示用户修复配置；不得去掉 `store_code` 过滤
    ↓
4️⃣ 构建 SQL → 直接执行业务查询（正常首问不做全表健康检查）
    → ⚠️ WHERE 条件中必须包含 `group_code = '#{SL_UNIFIED_G_ID}'` AND `store_code IN (#{omShopCodes})`（两条均无条件始终启用）
    → ⚠️ **值范围校验（C3-05）**：SQL 中出现的 group_code / store_code 值必须 100% 来自 #{SL_UNIFIED_G_ID} / #{omShopCodes} 占位符
    ↓
5️⃣ 若业务 SQL 报连接/表不存在 → 轻量探活（见 security-rules）；POS 无行不判 MCP 空库
    ↓
6️⃣ 展示结果 & 简要建议
```

> 💡 `#{变量名}` 选用规则详见「🔐 权限机制」章节。核心原则：**所有 7 张表统一使用 `#{SL_UNIFIED_G_ID}`（→ `group_code`）+`#{omShopCodes}`（→ `store_code`）**。

---

## 表结构

| 表名 | 用途 | 数据量 |
|------|------|--------|
| `e000.dt_store_view` | 门店主数据 | 268,125 家 |
| `dm.v_pos_corp_sale_analysis_with_sly` | 营业明细（视图） | 40亿+ 条 |
| `dm.v_item_sale_analysis_with_sly` | 菜品销售（视图） | 2.7亿 条 |
| `dm.dm_crm_card_sum_day_p_store` | 会员每日汇总（新表） | 1.4亿 条 |
| `dm.v_crm_member_with_sly` | 会员维表（视图） | 17.4亿 会员 |
| `dw.dwd_crm_member_card_p_with_sly` | 会员卡明细表 | 17.7亿 卡 |
| `dm.dm_ljc_scm8_store_rm_item_consume_analysis_day_p_group_view` | SCM8 原物料耗用视图 | 2.6亿 行 |

### ⚠️ 会员日汇总表门店字段说明

> 📌 **默认取数口径**：统计消费、储值、积分、用券等数据时，**默认取交易门店的数据**。

| 字段 | 含义 | 用途 |
|------|------|------|
| `store_code` | **交易门店**的商龙云门店号 | ✅ **默认取此字段** |
| `saled_shop_code` | 会员卡**售卡**云端门店号 | 需用户明确要求时使用 |
| `o2o_store_code` | 交易**云端**门店号 | 需用户明确要求时使用 |
| `mem_store_code` | 会员**注册**门店 | 需用户明确要求时使用 |

> 💡 如需按"注册门店"或"售卡门店"统计，需主动询问用户并调整查询条件。

### 🔗 七表关联关系

> ✅ **所有 7 张表的 `group_code`（集团 G 号） + `store_code`（门店 C 号）字段含义完全一致，可直接 JOIN。**

```
e000.dt_store_view（门店主数据，仅含 4 字段：store_code / group_code / cy_store_code / cy_group_code）
│
│  JOIN on group_code + store_code
│
├──→ dm.v_pos_corp_sale_analysis_with_sly（POS 营业明细）
├──→ dm.v_item_sale_analysis_with_sly（菜品销售）
├──→ dm.dm_crm_card_sum_day_p_store（会员日汇总）
├──→ dm.v_crm_member_with_sly（会员维表）
├──→ dw.dwd_crm_member_card_p_with_sly（会员卡明细）
└──→ dm.dm_ljc_scm8_store_rm_item_consume_analysis_day_p_group_view（SCM8 原物料耗用）

会员体系内部关联：
dm_crm_card_sum_day_p_store ←── group_code + store_code + mem_code ──→ v_crm_member_with_sly
dm_crm_card_sum_day_p_store ←── group_code + store_code + mem_card_no ──→ dwd_crm_member_card_p_with_sly.card_no
```

> 💡 详细字段 → [references/table-schema.md](references/table-schema.md)

---

## CLI 入口

### 🔧 CLI 可执行路径（强制 · Windows / macOS 兼容）

> WorkBuddy / Agent 执行环境通常 **没有** 把 `~/.slclaw/bin` 加入 PATH。
> 下文所有 `sl ...` 均指 `$HOME/.slclaw/bin` 下的绝对路径，**禁止**先 `which` / `where` / 搜索安装目录。
>
> ⚠️ WorkBuddy 在 Windows 上默认走 **PortableGit Bash**，不是 `cmd.exe`。`%USERPROFILE%\...` 与反斜杠路径会在 Bash 里触发 `fg: no job control` 等失败。

| 平台 | 可执行文件 | 说明 |
|------|------------|------|
| macOS / Linux | `$HOME/.slclaw/bin/sl` | POSIX 入口 |
| Windows（Bash / WorkBuddy） | `$HOME/.slclaw/bin/sl.cmd` | **必须**用 `.cmd`；裸 `sl` shebang 在 PortableGit 下常 exit 126 |
| Windows（PowerShell 备用） | `$env:USERPROFILE\.slclaw\bin\sl.cmd` | 仅 Bash 不可用时使用 |

#### ✅ 首选：Bash 一键兼容（Mac / Linux / Windows Git Bash）

> 优先用 **Bash** 工具执行；一行内自动选 `sl.cmd`（Windows）或 `sl`（Mac/Linux）。

```bash
SL="$HOME/.slclaw/bin/sl"; [ -f "$HOME/.slclaw/bin/sl.cmd" ] && SL="$HOME/.slclaw/bin/sl.cmd"; "$SL" starrocks read-query --query 'SELECT 1'
```

业务查询把末尾换成真实 SQL 即可，例如：

```bash
SL="$HOME/.slclaw/bin/sl"; [ -f "$HOME/.slclaw/bin/sl.cmd" ] && SL="$HOME/.slclaw/bin/sl.cmd"; "$SL" starrocks read-query --query "SELECT 1"
```

| 命令形态 | 用途 |
|----------|------|
| `"$SL" starrocks read-query --query '...'` | 执行单个只读查询 |
| `"$SL" store find --type crm --name '...' --format json` | 门店名 → omShopCode |

#### Windows PowerShell 备用（仅 Bash 不可用时）

```powershell
& "$env:USERPROFILE\.slclaw\bin\sl.cmd" starrocks read-query --query 'SELECT 1'
```

> 必须让 stdout **直接打印**到工具结果。禁止只写 `$output = & ...` 却不 `Write-Output $output`（WorkBuddy 可能只回报 exit code、看不到 JSON）。

#### ❌ 禁止（已实测踩坑）

| 写法 | 问题 |
|------|------|
| Bash 里用 `%USERPROFILE%\.slclaw\bin\sl.cmd` | cmd 变量/反斜杠在 Bash 不展开 → `fg: no job control` |
| Windows Bash 直接跑 `$HOME/.slclaw/bin/sl`（无 `.cmd`） | PortableGit 下 node shebang 常失败（exit 126） |
| 依赖 PATH / `which` / `where` / 搜索安装目录 | 环境无 PATH，浪费轮次 |
| Python / Node 脚本转发查询 | 禁止；统一直接调绝对路径 CLI |

### 🔧 CLI 配置说明

> ⚠️ **MCP 地址不在 skill 中硬编码**，而是由 `sl starrocks` 在运行时自动读取配置。

当前 CLI 仅支持 `read-query --query`。多步骤分析需在单轮 10 次上限内逐条调用上述绝对路径下的 `sl starrocks read-query --query ...`。

**禁止**使用 Python、Node/JS 脚本或其他中间脚本转发查询。

---

## 核心概念

### 三个金额指标

| 指标 | 字段 | 关系 |
|------|------|------|
| 营业应收 | `recv_money` | 最大，未减优惠 |
| 实收金额 | `busi_income` | 次高，扣除优惠 |
| 纯收金额 | `real_income` | 最小，再减杂项 |

> 💡 详细说明 → [references/business-context.md](references/business-context.md)

### 翻台率计算

| 指标 | 公式 |
|------|------|
| 开台率 | 总开台数 ÷ Σ(每天桌数 × 当天市别数) × 100% |
| 翻台率 | 开台率 - 1（若 < 0 则显示 0） |

> 💡 详细说明 → [references/business-context.md](references/business-context.md)

---

## 📝 文档维护说明

### 路径引用规则

| 引用场景 | 相对路径格式 | 示例 |
|---------|-------------|------|
| 同级目录引用 | `filename.md` | `intents/_index.md` → `intent-01-05-store.md` |
| 上级目录引用 | `../folder/file.md` | `intents/_index.md` → `../rules/security-rules.md` |
| 锚点链接 | `#anchor-name` | `intent-06-15-business.md#intent-6-revenuetrendanalysis---营收趋势分析` |

### Intent 维护规则

1. **新增/修改 Intent** 时，必须同步更新：
   - `intents/_index.md` 的「Intent 详细索引」
   - `intents/_index.md` 的「快速匹配指南」
2. **新增 Intent 文件** 时，需在 `_index.md` 添加对应链接
3. **锚点命名规范**：`intent-{序号}-{小写驼峰名称}--{中文说明}`

### 内容引用原则

| 概念 | 权威来源 | 其他文件引用方式 |
|------|---------|----------------|
| 三个金额指标 | `references/business-context.md` | 仅摘要，标注「详见...」 |
| 翻台率计算 | `references/business-context.md` | 仅公式，标注「详见...」 |
| 表结构字段 | `references/table-schema.md` | 标注「详见...」 |
| 安全规则 | `rules/security-rules.md` | SKILL.md 仅放摘要表格 |

### 禁止事项

- ❌ 禁止在多个文件重复完整的业务概念解释
- ❌ 禁止删除 `rules/security-rules.md` 中的任何安全检查项
- ❌ 禁止绕过机器人权限配置查询范围外的数据
- ❌ 禁止 SQL WHERE 条件中省略 `group_code` 过滤（必须由配置层注入）
- ❌ 禁止在 SQL 中硬编码 `group_code` / `store_code` 具体值（使用 `#{SL_UNIFIED_G_ID}` / `#{omShopCodes}` 占位符）
- ❌ 禁止在 SQL 中私自添加、枚举、或推断任何不在 `#{SL_UNIFIED_G_ID}` / `#{omShopCodes}` 占位符范围内的值（含额外 OR 条件、额外 IN 元素、子查询返回非授权值）
- ❌ 禁止在 SQL 的 WHERE 中省略 `store_code IN (#{omShopCodes})` 条件（所有 SQL 无条件始终启用）
- ❌ 禁止移除营业表的 `LIMIT` 要求
- ❌ 禁止在用户**明确指定门店**时跳过 `sl store find` 直接用 `e000.dt_store_view` LIKE 模糊查询
- ❌ 禁止在 `sl store find` 返回多个候选时静默选择第一条（必须列表让用户确认）
