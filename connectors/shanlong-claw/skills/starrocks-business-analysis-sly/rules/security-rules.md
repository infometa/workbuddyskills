# 安全规则与权限检查

## 🔒 权限检查清单

> ⚠️ **权限机制说明**：用户权限由 OpenClaw 机器人配置层预设（`SL_UNIFIED_G_ID` / `omShopCodes`），查询时通过 `#{变量名}` 占位符自动注入到 SQL 中。需验证配置的合法性（见下方检查项）。

**插值机制**：
```sql
-- ✅ 正确：用 #{变量名} 占位符，由系统自动注入
WHERE group_code = '#{SL_UNIFIED_G_ID}'                       -- 注入集团 G 号
  AND store_code IN (#{omShopCodes})                       -- 注入门店 C 号列表

-- ❌ 错误：硬编码具体值
WHERE group_code = 'G137427'                               -- 禁止硬编码集团码
  AND store_code IN ('C273353', 'C273354')                 -- 禁止硬编码门店码
```

> 💡 `#{SL_UNIFIED_G_ID}` / `#{omShopCodes}` 的真实值由机器人配置层（典型实现如 `token.json` 的 `biz_params` 字段）提供，AI **不接触**真实值，仅在 SQL 模板中使用占位符。

## 🔒 权限配置检查

每次会话初始化时，必须验证以下配置项：

---

### 检查 1：group_code 配置合法性（C0-01）

```python
# 获取机器人配置的 group_code 列表
config_group_codes = robot_config.group_codes  # list

IF len(config_group_codes) == 0:
    → 机器人未配置任何集团，返回错误："机器人未配置集团权限，请联系管理员"

IF len(config_group_codes) > 1:
    → 记录警告："检测到配置了多个 group_code: {config_group_codes}
       本系统不支持跨集团查询，将默认使用第一个 group_code"

    → 自动取第一个 group_code 作为查询范围
    → 告知用户："当前权限范围：{group_name}，如需切换请说明"

IF len(config_group_codes) == 1:
    → 正常记录当前集团上下文
```

**存储要求**：
- 将有效的 `group_code` 写入工作记忆 `MEMORY.md`
- 格式：`current_group_code = "{code}"`
- 会话中持续使用此值，直到用户明确切换

---

### 检查 2：store_code 与 group_code 对应关系（C0-02）

```python
# 获取机器人配置的 store_code 列表
config_store_codes = robot_config.store_codes  # list

IF len(config_store_codes) > 0:
    # 存在门店权限限制
    
    IF len(config_group_codes) > 1:
        → 返回错误："不支持跨集团配置门店权限"
    
    # 验证 store_code 属于 group_code
    valid_stores = query("""
        SELECT store_code 
        FROM e000.dt_store_view 
        WHERE group_code = '#{SL_UNIFIED_G_ID}' 
          AND store_code IN :config_store_codes
    """)
    
    invalid_stores = set(config_store_codes) - set(valid_stores)
    IF invalid_stores:
        → 记录警告："以下门店编码在集团中不存在：{invalid_stores}"
        → 自动过滤无效门店
    
    → 正常记录可用门店列表
```

---

## ⚠️ 查询执行检查

验证通过后，查询时仍需遵守以下规则：

### 检查 3：group_code 强制过滤（C3-00）

> ⚠️ **此检查为硬性门槛，任何 SQL 执行之前必须验证，不得跳过。**

```
IF generated_sql WHERE clause does NOT contain "group_code":
    → 拒绝执行，返回：
      "⚠️ SQL WHERE 条件中必须包含 group_code 过滤。
       group_code 的具体值由机器人配置层通过 #{SL_UNIFIED_G_ID} 占位符自动注入：
       • 所有 7 张业务表（含 dt_store_view） → #{SL_UNIFIED_G_ID}
       请补全 group_code 过滤条件后重新执行。"
    → 不执行任何 SQL，补全后重试
END IF
```

**规则说明**：
- `group_code` / `store_code` 的具体值由机器人配置层（典型实现如 `token.json` 的 `biz_params` 字段）注入，AI **不得**在 SQL 中硬编码具体值
- AI 构造 SQL 时使用 `#{SL_UNIFIED_G_ID}` / `#{omShopCodes}` 占位符，实际执行前由系统替换为机器人配置层中的对应编码
- 子查询 / CTE 中的每个 SELECT 也必须带 `group_code` 过滤
- **所有 7 张表**（含 `e000.dt_store_view` / POS视图 / 菜品视图 / CRM日汇总 / CRM会员维表 / 会员卡明细 / SCM8）均统一使用 `group_code` 字段（强制）+ `store_code` 字段（始终启用）
- **`group_code`（必填）**：所有 SQL 的 WHERE 中**必须**包含 `group_code = '#{SL_UNIFIED_G_ID}'`
- **`store_code`（始终启用）**：所有 SQL 的 WHERE 中**必须**包含 `store_code IN (#{omShopCodes})`，**无例外**
  - **`#{omShopCodes}` 的值来源分两种场景**：
    1. **用户未指定门店**：`#{omShopCodes}` 取机器人配置层默认门店码列表（全部门店），直接执行 SQL
    2. **用户明确指定门店名称/简称/别名/门店 ID**：先调用 `sl store find` 获取标准 `omShopCode`，**更新** `#{omShopCodes}` 的值为该门店码（单店或用户确认的多个），再执行 SQL
  - **禁止**在 SQL 中省略 `store_code` 过滤条件

---

### 检查 3.5：SQL 中 group_code / store_code 值范围强制校验（C3-05）⚠️

> ⚠️ **硬性门槛，所有 SQL 生成后、执行前必须验证，不得跳过。**
> **核心原则**：SQL 中出现的 `group_code` / `store_code` 值，**必须 100% 来自 `#{SL_UNIFIED_G_ID}` / `#{omShopCodes}` 占位符的注入值，AI 不得私自添加、枚举、或推断任何不在占位符范围内的值。**

```
# ========== 自动验证规则（AI 生成 SQL 后必须自检） ==========

# 规则 1：group_code 值来源唯一性
# ✅ 合法：WHERE group_code = '#{SL_UNIFIED_G_ID}'
# ❌ 非法：WHERE group_code IN ('G137427', 'G999999')  ← AI 私自加了 G999999
# ❌ 非法：WHERE group_code = 'G137427'              ← 硬编码，未使用占位符
ANY SQL WHERE clause referencing group_code:
    → MUST use #{SL_UNIFIED_G_ID} placeholder ONLY
    → MUST NOT contain hardcoded group_code values
    → MUST NOT contain additional group_code values NOT from #{SL_UNIFIED_G_ID}

# 规则 2：store_code 值来源唯一性（始终启用）
# ✅ 合法：AND store_code IN (#{omShopCodes})        ← 仅使用占位符
# ❌ 非法：AND store_code IN (#{omShopCodes}, 'C999') ← AI 私自加了 C999
# ❌ 非法：AND store_code = 'C273353'               ← 硬编码，未使用占位符
# ❌ 非法：AND store_code IN (SELECT store_code FROM ...)  ← 子查询可能返回非授权门店
ANY SQL WHERE clause referencing store_code:
    → MUST use #{omShopCodes} placeholder ONLY
    → MUST NOT contain hardcoded store_code values
    → MUST NOT contain additional store_code values NOT from #{omShopCodes}
    → MUST NOT use subquery to derive store_code (unless subquery also filters by #{SL_UNIFIED_G_ID})

# 规则 3：子查询 / CTE / JOIN 中的 group_code / store_code 同样受约束
# ❌ 非法示例：
#   WITH auth_stores AS (
#     SELECT store_code FROM e000.dt_store_view
#     WHERE group_code = '#{SL_UNIFIED_G_ID}' OR group_code = 'G999999'  ← 私自加 OR
#   )
ANY subquery / CTE / JOIN ON condition:
    → MUST also filter by group_code = '#{SL_UNIFIED_G_ID}'
    → MUST NOT add extra group_code / store_code values beyond placeholders

# ========== 违规自检 ==========
IF sql_contains_hardcoded_group_code_value:
    → 拒绝执行，返回：
      "⚠️ SQL 中检测到硬编码的 group_code 值，违反安全红线 C3-05。
       group_code 必须且仅能通过 #{SL_UNIFIED_G_ID} 占位符注入，
       不得私自添加任何具体值。请移除硬编码后重试。"
    → 不执行任何 SQL

IF sql_contains_extra_store_code_values_not_from_placeholder:
    → 拒绝执行，返回：
      "⚠️ SQL 中 store_code 过滤包含了 #{omShopCodes} 占位符范围外的取值，
       违反安全红线 C3-05。store_code 必须且仅能通过 #{omShopCodes} 占位符注入。"
    → 不执行任何 SQL

END IF
```

**典型违规场景（禁止）**：

| 违规写法 | 违规原因 | 正确写法 |
|---------|---------|---------|
| `group_code IN (#{SL_UNIFIED_G_ID}, 'G999999')` | 私自扩充 group_code 值 | `group_code = '#{SL_UNIFIED_G_ID}'` |
| `store_code IN (#{omShopCodes}, 'C999')` | 私自扩充门店码 | `store_code IN (#{omShopCodes})` |
| `group_code = 'G137427'` | 硬编码，未使用占位符 | `group_code = '#{SL_UNIFIED_G_ID}'` |
| `store_code = 'C273353'` | 硬编码 | `store_code IN (#{omShopCodes})` |
| CTE 中 `WHERE group_code = '#{SL_UNIFIED_G_ID}' OR group_code = 'G999999'` | CTE 中也不得私自加值 | 仅保留 `group_code = '#{SL_UNIFIED_G_ID}'` |

---

### 检查 4：营业表日期范围强制检查（C3-01）

> ⚠️ **此检查为硬性门槛，任何营业表查询之前必须执行，不得跳过。**

```
IF target_table == "dm.v_pos_corp_sale_analysis_with_sly":
    IF date_range IS NULL:
        → 拒绝执行，返回：
          "⚠️ 营业表数据量巨大（亿级），不支持无日期范围的全量查询。
           请指定日期范围，例如：
           • 最近7天
           • 2026年3月
           • 上个月
           • 近30天"
        → 不执行任何 SQL，等待用户提供日期范围
    END IF
END IF
```

---

### 检查 5：禁止的 SQL 模式

```
禁止执行：
- SELECT * FROM e000.dt_store_view  (无WHERE条件)
- SELECT * FROM dm.v_pos_corp_sale_analysis_with_sly  (无WHERE条件，无日期条件)
- 营业表查询不带 settle_biz_date 过滤条件（C3-01）
- 营业表查询不带 LIMIT（C3-03）
- 任何绕过机器人权限配置（如尝试查询配置外的数据）
```

> 💡 `group_code` 和 `store_code` 过滤条件由机器人配置层自动注入，SQL 模板中的占位符会被替换。

---

### 检查 6：禁止通过 brand_name 跨集团搜索（C5-02）

> ⚠️ **风险场景**：用户可能通过品牌名搜索（如"九田家"），SQL 的 `LIKE` 匹配可能返回其他集团的同名品牌。

**禁止行为**：
- ❌ `WHERE brand_name LIKE '%九田家%'` 不带 group_code 过滤
- ❌ 用户说"看看所有叫XX的门店"时不限制集团

**正确做法**：
- ✅ brand_name 搜索必须在 `group_code` 过滤之后执行
- ✅ AI 只能返回当前集团权限范围内的同名品牌
- ✅ 回复时明确标注"以下为您权限范围内的门店"

**示例**：
```
用户问："帮我看看所有叫'九田家'的门店"

❌ 错误：直接搜索所有集团的九田家门店
✅ 正确：搜索当前集团的九田家门店，并在回复中说明
   "为您找到以下【九田家】门店（共X家）：
    1. 九田家-xxx店
    2. 九田家-yyy店
    （仅显示您权限范围内的门店）"
```

---

### 检查 7：禁止暴露/查询其他集团信息（C5-01）

> ⚠️ **安全要求**：AI **只能**在回复中提及当前所属集团，**绝对禁止**暴露或查询其他集团的任何信息。

**禁止行为**：
- ❌ 查询所有集团列表（`SELECT DISTINCT group_code, group_name FROM e000.dt_store_view`）
- ❌ 提及其他集团名称："让我查询一下九田家的数据..."
- ❌ 说"我看到还有其他集团..."
- ❌ 展示其他集团的 group_code、group_name 或任何相关信息

**正确做法**：
- ✅ 在回复标题中标注当前所属集团名称（如"广西圣膳集团"）
- ✅ 直接使用机器人配置层注入的 `group_code` 查询
- ✅ 只返回用户权限范围内的数据

**示例**：
```
✅ 正确：
## 九田家集团 营收汇总（2026年3月）
📊 数据范围：2026-04-01 ~ 2026-04-07 | 九田家集团

❌ 错误：
## 九田家集团 营收汇总（2026年3月）
（用户权限属于圣膳集团，试图查询九田家）
```

---

### 检查 8：营业表 LIMIT 上限检查（C3-03）

```
IF target_table == "dm.v_pos_corp_sale_analysis_with_sly":
    IF generated_sql does NOT contain "LIMIT":
        → 拒绝执行，返回：
          "⚠️ 营业表查询必须指定返回行数上限（建议 LIMIT 100），
           防止大结果集拖垮前端渲染。请重新提问。"
        → 不执行 SQL
    END IF
END IF
```

---

## 🚫 安全红线

| ❌ 禁止 | ✅ 正确 |
|---------|--------|
| WHERE 条件中无 `group_code` 过滤 | **必须**带 `group_code = '#{SL_UNIFIED_G_ID}'`（配置层注入） |
| SQL 中硬编码 group_code 具体值 | 使用 `#{SL_UNIFIED_G_ID}` 占位符，由机器人配置层注入 |
| SQL 中 `group_code` / `store_code` 值超出 `#{变量名}` 占位符范围 | **必须 100% 使用占位符注入值**，不得私自添加/枚举/推断任何额外值（含硬编码、额外 OR 条件、子查询返回非授权值）⚠️ |
| 无日期过滤的营业表查询 | 始终带 `settle_biz_date >= :start_date AND < :end_date` |
| 营业表查询无 LIMIT | **必须**带 `LIMIT 100` |
| 门店表查询不带 delflg 过滤 | 始终带 `AND COALESCE(delflg, 0) = 0`（如目标表含该字段） |
| 字符串拼接 `'{{brand}}'` | 使用绑定参数 `:brand_name`（防 SQL 注入） |
| `SELECT *` | 只 SELECT 需要的字段 |
| `COUNT(*)` 统计门店数 | 必须使用 `COUNT(DISTINCT store_code)` |

> 💡 `group_code` / `store_code` 过滤已由机器人配置层注入，无需在 SQL 中手动添加。

---

## ⚠️ 门店数量统计去重规则（C4-01）

**核心原则**：营业表中同一 `store_code` 可能出现在不同的 `group_name` 下，必须使用 `COUNT(DISTINCT store_code)` 去重。

```sql
-- ❌ 错误：COUNT(*) 会重复计数同一门店
SELECT city, COUNT(*) AS 门店数
FROM dm.v_pos_corp_sale_analysis_with_sly
WHERE group_code = 'G037134'
GROUP BY city;

-- ✅ 正确：COUNT(DISTINCT store_code) 去重
SELECT city, COUNT(DISTINCT store_code) AS 门店数
FROM dm.v_pos_corp_sale_analysis_with_sly
WHERE group_code = 'G037134'
GROUP BY city;
```

---

## 📅 日期范围解析规则

| 用户说法 | 解析为 | 说明 |
|---------|-------|------|
| "最近" / "近期" | **拒绝解析** → 请用户明确 | 范围不明 |
| "最近7天" | today - 7 ~ today | 含今天 |
| "最近30天" | today - 30 ~ today | 含今天 |
| "上周" | 上周一 ~ 上周日 | 完整自然周 |
| "本月" | 本月1日 ~ today | 包含今天 |
| "上月" | 上月1日 ~ 上月最后一天 | 完整自然月 |
| "今天" | today ~ today | 单天 |
| "昨天" | yesterday ~ yesterday | 单天 |

---

## ⚡ 性能注意事项

### 日期范围必须使用 `>= AND <` 格式

```sql
-- ✅ 正确写法
settle_biz_date >= '2026-04-02' AND settle_biz_date < '2026-04-03'

-- ❌ 避免使用 BETWEEN
settle_biz_date BETWEEN '2026-04-02' AND '2026-04-02 23:59:59'
```

### 除零错误防护

所有除法运算必须用 `NULLIF(denominator, 0)` 包裹：

| 计算场景 | 正确写法 |
|---------|---------|
| 单均消费 | `SUM(money) / NULLIF(SUM(count), 0)` |
| 坪效 | `SUM(income) / NULLIF(SUM(area), 0)` |
| 开台率 | `SUM(open) / NULLIF(桌数 × 市别数 × 天数, 0)` |

---

## ❌ 空结果与超时处理

### MCP 连接健康检查（优先执行）

> ⚠️ **本检查在会话初始化时执行，优先于所有业务查询。**

使用以下 SQL 验证 MCP 连接是否正确指向生产库：

```sql
-- 生产库 dm.v_pos_corp_sale_analysis_with_sly 有 40 亿+ 行
-- 若 COUNT(*) 返回 0 或执行时间 < 0.1s，说明连到空库
SELECT COUNT(*) AS cnt FROM dm.v_pos_corp_sale_analysis_with_sly LIMIT 1;
```

**异常处理**（满足任一条件即触发）：

| 条件 | 处理方式 |
|------|---------|
| `cnt = 0` | 停止所有查询，向用户报告 MCP 端点配置错误 |
| 执行时间 < 0.1s（40 亿行不可能这么快） | 同上 |
| 表不存在 / 查询报错 | 停止所有查询，向用户报告 MCP 连接异常 |

**标准报错输出**（必须原样输出，不得重试）：

```
⚠️ MCP 连接异常：当前连接的数据库中没有业务数据（表行数为 0），
疑似 MCP 端点配置错误。

请检查运行环境中的 MCP 配置，确认地址是否为正确的生产库端点：
• 生产环境：环境变量 MCP_STARROCKS_URL 配置的地址

配置修正后重新发起查询。
```

> 💡 本规则旨在防止 OpenClaw 等环境下 MCP 地址错误导致 AI 反复空查、陷入死循环。

### 空结果（业务查询）

SQL 返回 0 条记录时（**排除上述 MCP 健康检查已通过的场景**）：

> 💡 **核心原则：区分"AI 构造条件错误"（允许修正重试 1 次）和"数据确实不存在"（必须立即停止）。**

#### 类型 A：允许的重试（参数/条件构造问题）

以下情况导致空结果时，**允许修正后重试 1 次**：

| 触发条件 | 允许的修正操作 |
|---------|--------------|
| `#{变量名}` 占位符缺失导致 WHERE 不全 | 执行 `rules/param-fallback.md` 中定义的预查 SQL 补全参数 |
| 日期边界格式有误 | 修正为 `>= AND <` 格式 |
| store_code 过滤了无效门店 | 从机器人配置层重新读取 `#{omShopCodes}` 或预查门店码 |

> ⚠️ 类型 A **仅允许 1 次修正重试**。修正后仍空 → 立即转入类型 B。

#### 类型 B：禁止的重试（数据不存在 / Skill 不支持）

满足以下任一条件时，**立即停止，输出标准回复模板**：

- 类型 A 修正后仍为空结果
- 业务查询参数齐全、SQL 正确但返回空（第 2 次空结果时停止）
- 7 张已知表中无所需字段

> 🛑 **类型 B 触发后绝对禁止的操作**：
> - ❌ 换日期范围再查
> - ❌ 换 group_code / store_code 编码体系
> - ❌ 换字段名组合
> - ❌ 换表名
> - ❌ 换 GROUP BY 维度
> - ❌ 任何"让我再试试""换个条件"
>
> 💡 **计数规则**：
> - 第 1 次空 → 判断是否属于类型 A → 是则修正重试
> - 修正后第 2 次仍空 / 或首次即属类型 B 的第 2 次空 → **立即终止**

标准回复模板：

```
（当前筛选条件下暂无数据）

查询条件：
• 日期范围：[xxx]
• 其他筛选：[xxx]

可能原因：
1. 该时间段内没有符合条件的营业记录
2. 门店尚未开业或已歇业
3. 筛选条件过于严格，请尝试放宽范围
```

### 查询超时（>30秒）

```
⚠️ 查询超时（数据量较大，执行时间超过 30 秒）

请尝试以下方式缩小范围：
1. 缩小日期范围（如改为近 7 天而非近 30 天）
2. 增加门店或品牌筛选条件
3. 改为查询汇总数据而非明细

您希望如何调整？
```

---

## 🔐 权限范围说明

- 用户权限由 OpenClaw 机器人配置层预设，只能查询配置范围内的数据
- `group_code` 和 `store_code` 的具体值由机器人配置层自动注入，AI 使用 `#{SL_UNIFIED_G_ID}` / `#{omShopCodes}` 占位符，**不得硬编码具体值**
- **所有 SQL 的 WHERE 条件中必须包含 `group_code` 过滤**（**所有 7 张表统一使用 `group_code` 字段**），无 `group_code` 的 SQL 拒绝执行
- `store_code` 过滤**始终启用**（所有 SQL 无条件包含 `store_code IN (#{omShopCodes})`，无例外）：
  - 用户**未指定**门店 → `#{omShopCodes}` 取 token 配置层默认门店码列表（全部门店）
  - 用户**明确指定**门店名称/简称/别名/门店 ID → 先 `sl store find` 获取 `omShopCode`，**更新** `#{omShopCodes}` 值为该门店码，再执行 SQL
- `group_code` / `store_code` 过滤条件不在对话中暴露具体值
- 若用户试图绕过权限配置查询其他数据，机器人应拒绝并提示权限不足
