---
name: hr-data-sql-builder
description: 生成HR数仓StarRocks查询SQL。覆盖员工信息/人员异动/绩效/梯队等查询，含术语映射、业务规则和SQL模板。表结构从MCP resources动态获取。用户提出数据查询需求时必须使用本Skill。指标类查询（涉及率/比/占比/平均值/趋势等计算指标）必须使用indicator-query Skill。
---

## 概述

根据用户HR数据需求，生成StarRocks SQL查询腾讯HR数仓宽表。

> ⚠️ **核心原则见 RULES**：本 Skill 遵循 `hr-starrocks-query-conventions` 规则（禁止权限控制类WHERE条件）。仅允许SELECT、必须LIMIT、统计优先SQL完成。

## 数据资源说明（table）

本 Skill 基于 `table` 资源（HR 各业务场景明细宽表）生成 SQL：

- **内容覆盖度**：全面，基本覆盖 HR 业务全场景明细数据，既可明细查询，也可统计查询。
- **权限约束**：行列权限严格按照角色职责授权。例如 BP 按负责组织授予行权限，仅能查负责组织范围内明细；集团员工关系管理负责人行权限为全公司，但其列权限仅限员工关系管理职责相关（无绩效、梯队评估数据列权限）。
- **统计查询策略**：为确保统计口径准确，生成 SQL 前应优先用 `slang_query` 识别查询意图是否已有对应**统计指标术语定义**，如有则严格按术语定义执行查询。

## 数据源

表结构**必须从MCP resources动态获取**，禁止硬编码。

### MCP服务：`hr_data_service_v1`
**MCP连接检查**：若连接失败或不可用，立即终止后续步骤，引导用户连接mcp。
   -- 如果用的是codebuddy则点击右上角的齿轮，选择MCP，找到 HRIT/hr-ai-data/hr_data_service_v1，点击"连接"。
   -- 如果用的是workbuddy腾讯HR数智专家，在对话框上方点进'HR数仓查询' 进行连接。
   -- 如果用的是workbuddy AI助手，在左侧找到"连接器"，再在右上角点击"自定义连接器"，找到hr_data_service_v1，点击"连接"。
   -- 其他，按实际情况引导用户连接mcp。
**执行查询**：工具 `starrocks_query`，参数 `sql`（必填）+ `userQuestion`（必填）

**获取表结构**：
- 表列表：resource `starrocks://tables` → 获取 `table_code`/`table_name`/`table_desc`/`write_sql_background`/`default_parameters`
- 单表字段：resource `starrocks://tables/{table_code}` → 获取 `columns` 数组（含 `column_code`/`column_name`/`column_alias`/`column_type`/`column_use`/`column_group`/`sample`/`group_by_able`/`aggregate_type`）

**术语知识**：
- 术语清单：resource `starrocks://slangs` → 获取所有HR业务术语名称及同义词列表，用于识别用户问题中涉及的术语
- 术语定义查询：工具 `slang_query`，输入术语名称或同义词 → 返回匹配术语的完整定义（含术语名称、定义、分类、同义词）

### 选表策略

- 在职人数/员工现状/绩效/结构分布 → **员工信息宽表**
- 入职/离职/调动/晋升等异动 → **人员变动信息宽表**

---

## SQL生成工作流

### Step 1：术语识别与需求分析

1. **术语识别**（MCP优先，本地降级）：
   1. 从MCP resource `starrocks://slangs` 获取术语清单（含术语名称和同义词）
   2. 结合用户问题，推测哪些术语与用户意图相关（匹配关键词、简称、同义词）
   3. 使用MCP工具 `slang_query` 查询相关术语的完整定义，补充业务知识以准确理解用户意图
2. 确定：查询目标（统计/明细/趋势/对比/分布）、数据范围（组织/时间/人群）、分析维度
3. 根据选表策略，从MCP resources获取目标表字段定义
4. **反向升级检查**：判断本次查询是否属于「比率/占比/均值/上级组织对比类」统计问题（如占比、比例、率、均值、人均、向上对比等），且尚未尝试 `indicator-query`。若是，应提示用户该类统计更适合走预置指标（结果更准确、执行更高效），建议切换到 `indicator-query`；若用户明确要求走 SQL、或该查询已确认无匹配指标，则继续本 Skill 后续步骤，不强制阻塞。

### Step 2：SQL构建
1. **SELECT**：统计类用聚合函数+GROUP BY字段；明细类用业务相关字段
2. **FROM**：选择正确的表
3. **WHERE**：默认过滤条件（从`default_parameters`获取）+ 组织条件（`org_full_name LIKE`）+ 业务条件。⚠️ 禁止添加权限控制条件；
4. 调用专业术语-指标口径背景知识生成sql时，注意遵循指标口径定义的可选条件默认值
5. **GROUP BY**：统计类必选
6. **ORDER BY**：按业务逻辑排序
7. **LIMIT**：至少限制1000行

### Step 3：SQL校验清单

- [ ] 已从MCP获取表结构，表名含catalog前缀
- [ ] 默认过滤条件齐全
- [ ] 统计人数用 COUNT(DISTINCT staff_id8)
- [ ] 专业职级字段类型正确（字符串 vs 数字）
- [ ] 组织查询用 org_full_name + LIKE
- [ ] 异动查询指定 move_type_name
- [ ] 绩效等级码值正确（Outstanding/Good/Underperform）
- [ ] 大结果集有LIMIT
- [ ] 仅SELECT，禁止写操作
- [ ] 无权限控制类过滤条件（见 `hr-starrocks-query-conventions`）

### Step 4：输出SQL

---

## 业务规则参考

### 组织信息

- `org_full_name`：组织全路径（BG/线/部门/中心/组），WHERE查询组织优先用此字段 + LIKE
- `org_name`：末级组织节点名称，查单个组织节点时用
- BG/线/部门/中心/组：分层级字段，按层级分布统计时用对应字段GROUP BY
- 示例：xx线各部门在职人数 → `WHERE org_full_name LIKE '%xx线%' GROUP BY dept_name`

### 专业职级

- 专业人员：`pro_position_level_name IS NOT NULL AND manager_level_name IS NULL`
- x级专业人员：`pro_position_level_num = x`
- x族x级（如T9）：`pro_position_level_name = 'T9'`
- x级以上（带族如T9+）：`pro_position_level_name` IN 含T且数值>=9的值
- x级以上（不带族如9级+）：`pro_position_level_num >= 9`
- 职级分布GROUP BY优先用 `pro_position_level_num`

### 异动查询

- 类型映射：入职→`雇佣`、离职→`离职`、调动→`调动`、专业变化→`专业变化`、管理变化→`管理变化`
- A组织入职/离职/专业变化/管理变化：`to_org_full_name LIKE '%A组织%'`
- A组织调入：`to_org_full_name LIKE '%A组织%' AND from_org_full_name NOT LIKE '%A组织%'`
- A组织调出：`from_org_full_name LIKE '%A组织%' AND to_org_full_name NOT LIKE '%A组织%'`

---

## 安全约束

> 详细安全规范见 `hr-starrocks-query-conventions` 规则，此处仅列出校验清单摘要。

1. 仅允许 SELECT，禁止写操作关键字（INSERT、UPDATE、DELETE、DROP、ALTER、TRUNCATE、CREATE、GRANT、REVOKE、RENAME、REPLACE）
2. 大结果集必须加 LIMIT，注意如果查询结果行数等于LIMIT值，需检查是否被截断
3. 禁止权限控制类 WHERE 条件（见 `hr-starrocks-query-conventions`）

---

## 回答规范

执行查询后按以下顺序组织回答：
1. 简要说明需求理解和执行策略
2. 展示SQL/代码
3. 呈现结果（表格/列表）
4. **结果截断检测（强制）**：呈现结果前，必须检查返回行数是否**恰好等于**SQL中的LIMIT值。若相等，则数据极可能被截断，**禁止**将该数字当作实际总数展示。必须：
   - 明确告知非技术用户"当前展示了前N条记录，实际符合条件的人可能更多，结果不完整"
   - 询问用户是否需要获取完整数据，或者是否希望添加更多筛选条件缩小范围
5. 空结果时分析原因（见空结果处理规则）
6. 识别脱敏数据并提示（见脱敏识别规则）
7. 基于数据给出洞察
8. 不确定时明确告知并给出调整建议
9. 用户是非技术人员，需提供简单易用的说明

---

## 数据脱敏识别规则

> 脱敏特征、识别方法和处理规范的完整定义见 `hr-data-desensitization` 规则。

执行查询后，按 `hr-data-desensitization` 规则检测结果中的脱敏数据。发现脱敏时在结果表格后提示用户，深入排查可用 `data-table-permission-checker` Skill。

---

## 查询结果为空的处理规则

返回0行数据时，主动分析原因而非简单告知"没有数据"：

**可能原因**：
1. **条件传值有误**：组织名拼写/简称错误、时间范围不对、枚举值不正确、筛选值不存在
2. **数据权限不足**：无该表/组织的查看权限，服务端返回空结果
3. **数据本身为空**：条件合理但确实无数据

**处理**：自查SQL条件 → 可放宽条件重试 → 向用户列出可能原因并提出调整建议

---

## 维度值权限缺失的处理规则（多值 vs 单值范围）

统计/明细查询涉及的维度筛选值（组织、工作地等）存在行权限不足时，**区分"多值并列查询"与"单一范围查询"两种情形**，处理方式不同：

### 场景一：多值并列查询，部分值有权限、部分值无权限 → 正常执行，分别告知

- **判定**：用户问题包含**多个独立可枚举的维度值**（如同时问3个具体组织/部门的数据），本质是多条并列小查询，某个值无权限不影响其他值的查询意义。
- **处理**：正常执行SQL（不做前置过滤），服务端行权限会自动过滤无权限的值。拿到结果后，对比"用户请求的维度值列表" vs "结果中实际出现的维度值"，识别缺失项。
- **反馈**：正常展示有权限部分的结果；**同时明确列出因无权限被排除的具体维度值**，不要笼统说"部分数据缺失"。
- 示例：**"查询A、B、C三个部门的在职人数"**，若C无权限 → 展示A、B的在职人数结果 + 提示"C部门因无数据权限未能查询，如需查看请联系数据管理员申请权限"。

### 场景二：单一范围查询，该范围本身超出权限会导致查询结果失真 → 直接反馈权限不足，禁止静默缩小范围

- **判定**：用户问题的范围本身是**单一整体**（如某一个组织、某一上级层级），若该范围超出用户权限，SQL执行时"请求范围 ∩ 权限范围"会被服务端自动收窄，返回的是**含义已变、范围更小**的结果，而非用户实际请求的范围——这种"静默缩小范围"比直接告知无权限更容易误导用户。
- **处理**：执行SQL前，先用 `data-table-permission-checker`（`get_current_user_data_permission`）核实该维度请求值是否被权限覆盖：
  - 请求值是权限内某组织的**自身或子集** → 正常执行查询（服务端过滤天然正确，无需阻断）。
  - 请求值是权限范围的**上级/超集，或完全在权限范围之外** → **直接反馈用户权限不足**，禁止改为查询用户实际有权限的子范围后当作原范围的结果展示。
- 示例：用户仅有A部门权限，却问**"A部门的上级线数据"** → 应直接告知"您目前仅拥有A部门的数据权限，暂无上级线的查看权限，如需查看请申请权限"，而不是悄悄只返回A部门数据、却让用户以为是上级线的数据。
- **优先提示**：此类"超出权限范围的单一范围查询"（尤其上级组织对比），应先按 `ask-data`「统计查询的路径选择原则」尝试 `indicator-query`（对上级组织查询有专门设计，由 Step-6 服务端结果直接判断可行性，不存在静默缩小范围的风险）；仅当已确认 indicator 不适用/无匹配、且最终判定走 SQL 路径时，才需要执行本节的前置权限核实。

---

## 调用方式

- **直接查询**：通过MCP生成SQL并执行
- **生成调用代码**：生成SQL后参考 `data-warehouse-api-codegen` Skill 生成前端调用代码