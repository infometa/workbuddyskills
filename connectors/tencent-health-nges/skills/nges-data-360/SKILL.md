---
name: nges-data-360
description: "NGES/重楼平台通用数据洞察与分析能力（只读）。根据用户的业务问题，自动分析涉及的元数据对象与字段（通过 MCP 实时查询元数据），结合用户角色（医药代表 Rep、地区经理 DSM、大区经理 RSM 等）确定数据范围（含下属团队），构造重楼 GQL（类 GraphQL）查询语句拉取并解读数据。当用户想分析拜访（visit/visit_item）、会议（events_meeting）、用户行为（user_behavior_details）等业务数据，进行统计/排名/趋势/对比/占比分析，查询自己或下属/团队的业绩，并可将结果可视化为图表（折线/柱状/饼图），或提出'分析…数据''看看…情况''统计一下…''我的团队/下属…''本月拜访量''会议完成情况''用户活跃度''谁的业绩最好''环比/同比''画个图/可视化'等数据洞察类需求时，应主动加载此 Skill。即使用户没有明确说'查询'或'GQL'，只要意图是从业务数据中获取洞察，也应触发。注意：本 Skill 专注只读的数据洞察分析，不做数据写入（增删改请使用 paris-gql-query）。"
version: "1.0.0"
author: "NGES"
---

# nges-data-360 — 重楼数据洞察与分析

把用户的业务问题转化为重楼 GQL 查询，拉取数据并给出可解读的洞察。所有平台交互（查元数据、查下属、跑查询）**全部通过 MCP 工具完成**，不依赖任何本地脚本或 `.nges` 配置。

> **定位**：只读的数据洞察。专注 query / 聚合 / 分组 / 排名 / 趋势，不做 insert/update/delete（写操作请用 `paris-gql-query`）。这样既贴合"分析"诉求，也避免在探索性分析中误改数据。

## 1) 为什么这样设计

数据洞察的难点不在于写 SQL，而在于三件容易出错的事：**问对对象和字段**、**框对数据范围**、**给出有意义的解读**。本 Skill 把流程固化为：先用元数据接口把对象/字段问清楚（绝不猜字段名），再根据用户角色框定他能看、且想看的数据范围（自己 vs 下属团队），最后构造查询并把数字翻译成业务结论。

## 2) 核心工作流

```
用户的业务问题（"本月我团队的拜访量怎么样？"）
        │
        ▼
Step 1 拆解分析意图  ──→ 指标 / 维度 / 时间范围 / 过滤 / 排序
        │
        ▼
Step 2 框定数据范围  ──→ 自己 or 下属团队？（角色感知，见 §4）
        │
        ▼
Step 3 解析对象与字段 ──→ MCP 实时查元数据（绝不猜字段，见 §3）
        │
        ▼
Step 4 构造 GQL      ──→ 过滤/聚合/分组/排序/分页/关联（见 §5、references）
        │
        ▼
Step 5 执行查询      ──→ MCP GraphqlQuery
        │
        ▼
Step 6 洞察输出+可视化 ─→ 数据 + 业务解读 + （必要时）图表 + 建议
```

### Step 1 — 拆解分析意图

把自然语言翻成结构化的分析五要素，缺失项先合理假设并在结果里说明，不要为小事反复打断用户：

- **指标**：要算什么？计数（拜访次数）、求和（费用）、平均、占比、去重计数、排名。
- **维度**：按什么分组？按人（owner/岗位）、按时间（天/月）、按类型、按产品。
- **时间范围**：默认按"本月"理解相对时间；记住日期字段是**秒级 Unix 时间戳**（见 §6）。
- **过滤**：状态、类型、特定对象等约束。
- **范围**：本人数据，还是下属/团队数据？（进入 Step 2）

### Step 2 — 框定数据范围（角色感知）

**核心原则：重楼按角色配置了行权限，执行 GQL 时会自动注入对应的数据范围过滤。** 因此默认情况下**无需手写 `owner` 或 `belong_territory` 条件**——医药代表查到的自动就是本人数据，地区/大区经理查到的自动就是其团队/下属链数据。手动再叠加范围条件多此一举，还可能与行权限取交集导致结果偏窄。

**角色识别仍然有用**，但用途变了：用来**理解返回数据的口径、组织洞察措辞、判断是否要逐人对比**，而不是拼范围条件。调用 MCP `GetStaffUserInfo`（无参，当前登录用户）取 `identity_tag`：

| identity_tag | 角色 | 行权限自动返回的范围 |
|--------------|------|---------------------|
| `representative` | 医药代表 Rep | 仅本人数据 |
| `district_manager` | 地区经理 DSM | 本人 + 下属团队 |
| `regional_manager` | 大区经理 RSM | 整条下属链 |

**只有少数场景才需要显式加范围条件**：

- 管理者想"只看自己"而非整个团队 → 加 `owner: $_uin` 主动收窄。
- 聚焦/对比"某个特定下属或某层级" → 用 `ListSubordinateTerritory` 取目标 `territory_code`，再显式 `belong_territory: {_in: [...]}`。
- "按每个成员拆开对比" → 直接 `_group_by: [owner]` 即可（行权限已把数据限定在可见集合内，分组自然按可见的本人/下属拆分），无需额外范围条件。

数据范围与角色的完整说明见 [references/roles-and-data-scope.md](references/roles-and-data-scope.md)。

### Step 3 — 解析对象与字段（绝不猜字段）

元数据是运行时配置，存在平台数据库里，**代码库里搜不到、也不能凭记忆猜**。字段名/类型一旦猜错，查询要么报错要么静默返回错数据。所以编写任何 GQL 前必须先确认对象与字段：

1. **不确定对象名时** → MCP `GetObjectList`（`DataServer.MetadataService`）按关键词搜索，拿到准确对象名。
2. **拿对象字段详情** → MCP `GetObjectsByNames`（`DataServer.MetadataService`），批量传入对象名，返回每个对象的 `fields`（含 `name`、`value_type`、选项配置）和 `relations`（关联关系）。编写聚合/过滤/赋值前**必须**核对 `value_type`。

常用业务对象（拜访、会议、用户行为）的语义说明与典型分析模板见 [references/common-scenarios.md](references/common-scenarios.md)——但其中字段仅为典型示例，**实际字段一律以 `GetObjectsByNames` 返回为准**。

### Step 4 — 构造 GQL

根据五要素拼装查询。最常用的是聚合 + 分组 + 时间过滤 + 排序：

```gql
# "本月我团队各成员的拜访次数排名"
# 行权限自动限定为当前用户可见范围（团队），无需手写 belong_territory
# 拜访明细在 visit_item（含 hcp_id）；actual_date 实际拜访日期；status=2 已提交
{
  visit_item(
    _where: {
      actual_date: {_gte: 1717171200, _lt: 1719763200}
      status: 2
    }
    _group_by: [owner]
    _order_by: {cnt: _desc}
  ) {
    owner
    cnt: _count(id)
  }
}
```

完整语法（过滤运算符、聚合函数、分组 having、关联查询、子查询、系统变量/函数）见 [references/gql-syntax.md](references/gql-syntax.md)；高频分析模板见 [references/common-scenarios.md](references/common-scenarios.md)。

### Step 5 — 执行查询

通过 MCP `DataServer__DataService__GraphqlQuery`执行：参数 `{"query": "<GQL>"}`，返回 `{"affect_rows": "0", "data": {"<对象名>": [...]}}`（`data` 为结构化对象，按对象名取结果数组；详见 mcp-tools.md）。

- 查询为只读，验证通过即可直接执行并展示，无需再次找用户确认。
- 若查询语法没把握，可先用 `GraphqlQuery` 传 `{"query": "...", "only_validate": true}` 做 dry-run 校验（不实际取数）。

MCP 工具的 server 名、方法名、参数与返回结构详见 [references/mcp-tools.md](references/mcp-tools.md)。

### Step 6 — 洞察输出与可视化

不要只甩数字。把结果翻译成业务结论：指出关键数值、对比/排名、异常点，必要时给一句可执行建议。

**必要时生成图表**：当结果呈现趋势、排名/对比、占比时，可视化比文字更直观——折线看变化、柱状比高低、饼图看构成。用脚本 `${SKILL_DIR}/scripts/render_chart.py`（`SKILL_DIR`=本 skill 根目录）把结果渲染成自包含 HTML 图表，再把路径告知用户预览。作图前记得把枚举 value 翻成中文 label、金额（×100）还原为元。单值或两三行的小结果用文字/表格即可，不必强行作图。何时作图、图型选择、结果→spec 转换详见 [references/chart-output.md](references/chart-output.md)。

输出结构见 §7。

## 3) 工具调用规范

**平台数据交互**（识别角色、查元数据、查下属、跑查询）全部通过 MCP 完成，不用 python 脚本访问平台、不读 `.nges`。调用前先用 `mcp_get_tool_description` 获取该工具的参数 schema，再用 `mcp_call_tool` 执行。

> 例外：结果可视化的 `scripts/render_chart.py` 属**本地输出渲染**，不访问平台，不在此限。

| 用途 | MCP server | 工具（方法名） | 关键参数 |
|------|-----------|---------------|----------|
| 识别当前用户角色/岗位 | `nges` | `NgesServer__NgesStaff__GetStaffUserInfo` | 无参（当前登录用户） |
| 搜索对象（不确定对象名） | `nges` | `DataServer__MetadataService__GetObjectList` | `keyword` / `object_name` / `limit` |
| 获取对象字段与关联 | `nges` | `DataServer__MetadataService__GetObjectsByNames` | `objects: [对象名...]` |
| 获取下属岗位/人员 | `nges` | `NgesServer__NgesStaff__ListSubordinateTerritory` | `territory_code` / `level` / `yearmonth` |
| 执行/校验 GQL 查询 | `nges` | `DataServer__DataService__GraphqlQuery` | `query` / `only_validate` |

> server 名以 `mcp.json` 实际配置为准

## 4) 角色与数据范围速记

| identity_tag | 角色 | 行权限自动范围 | 是否需手写范围 |
|--------------|------|---------------|---------------|
| `representative` | 医药代表 Rep | 仅本人 | 否，直接查 |
| `district_manager` | 地区经理 DSM | 本人 + 下属团队 | 否，直接查 |
| `regional_manager` | 大区经理 RSM | 整条下属链 | 否，直接查 |

> **默认不手写 `owner`/`belong_territory`**，行权限按角色自动过滤。仅在「管理者只看自己」（加 `owner: $_uin`）或「聚焦/对比特定下属」（`ListSubordinateTerritory` + `belong_territory {_in}`）时才显式收窄。角色用 `GetStaffUserInfo` 的 `identity_tag` 判断（见 Step 2）。详见 [references/roles-and-data-scope.md](references/roles-and-data-scope.md)。

## 5) 关键约束（沿用重楼 GQL 规则）

| 约束 | 说明 |
|------|------|
| **元数据先行** | 编写 GQL 前必须 `GetObjectsByNames` 确认字段名与 `value_type`，绝不猜 |
| **日期=秒级** | 所有日期/时间字段按**秒级** Unix 时间戳存储与过滤，不是毫秒 |
| **软删除** | 查询自动过滤 `delete_time=0`，无需手动加条件 |
| **聚合返回名无下划线** | GQL 写 `_count`/`_sum`，返回 JSON 字段是 `count`/`sum`（去掉下划线） |
| **`_all` 不含虚拟字段** | `_all` 只返回物理字段，关联/公式/汇总字段须显式列出 |
| **行权限自动过滤** | GQL 自动按当前用户角色注入行权限范围，**默认无需手写 `owner`/`belong_territory`**；超范围数据查不到属正常 |
| **ID 为 text** | 主键是 19 位雪花 ID，字符串类型 |

字段类型与赋值/过滤格式速查见 [references/gql-syntax.md](references/gql-syntax.md) 末尾的数据类型对照表。

## 6) 必须参考（渐进式披露）

| 资源 | 用途 | 何时读 |
|------|------|--------|
| [references/mcp-tools.md](references/mcp-tools.md) | 四个 MCP 工具的参数/返回详解与调用示例 | 调用任何 MCP 工具前 |
| [references/gql-syntax.md](references/gql-syntax.md) | 完整 GQL 查询语法（过滤/聚合/分组/排序/关联/系统变量/函数/类型） | 构造任何 GQL 时 |
| [references/roles-and-data-scope.md](references/roles-and-data-scope.md) | 角色体系（Rep/DSM/RSM）、下属查询、territory/org 数据范围 | 涉及下属/团队/按人对比时 |
| [references/common-scenarios.md](references/common-scenarios.md) | 拜访/会议/用户行为三大场景的对象语义与现成分析模板 | 分析这三类业务数据时，可直接套用模板 |
| [references/chart-output.md](references/chart-output.md) | 图表选型、`render_chart.py` 用法、结果→图表 spec 转换 | 需要把结果可视化成图表时 |

> **加载策略**：任何分析都先读 `mcp-tools.md` + `gql-syntax.md`；涉及下属/团队读 `roles-and-data-scope.md`；命中拜访/会议/用户行为场景读 `common-scenarios.md` 直接套模板；需要作图读 `chart-output.md`。

## 7) 输出契约

```
📊 {分析主题}

- 数据范围: {本人 / 团队（含下属）/ 指定岗位}
- 时间范围: {起 ~ 止}
- 涉及对象: {对象名}

【结果】
{表格或要点：关键数值、排名、对比}

【洞察】
{1-3 条业务解读：趋势、异常、对比结论}

【图表】（必要时）
{生成的 HTML 图表路径，提示在 IDE/浏览器预览}

【GQL】
\`\`\`gql
{执行的查询}
\`\`\`
```

> 简单问题可直接给结论+数字，不必拘泥格式。复杂对比/排名建议用表格；趋势/排名/占比可叠加一张图（见 chart-output.md）。

## 8) 澄清策略

能假设就假设并说明，只在以下情况澄清（猜错代价高）：

- **分析对象完全不明**：连查哪类数据都无法判断时（拜访？会议？行为？）。
- **数据范围歧义且影响结论**：分不清要"本人"还是"团队"，且两者结果差异大时。
- **指标口径模糊**：如"活跃度"可能指多种定义，需确认口径。

时间范围、排序方向、返回条数等小事，先用合理默认（本月、降序、Top 20）并在输出中注明即可。
