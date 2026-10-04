---
name: nges-precall
description: "NGES 访前准备（PreCall）能力。对标 ADP 标品四模块架构：客户画像 / 医生推荐 / 拜访策略 / 拜访计划。帮助医药代表、DSM、KA 在 WorkBuddy 对话中完成访前全流程：查询医生画像、按角色化权重推荐优先拜访医生、按采纳阶段生成拜访策略（NBA/话术/资料）、创建拜访计划（only_validate 预校验+确认后写入）。当用户说'某医生画像''这周该拜访谁''帮我准备拜访''明天要见某医生''做个拜访计划''访前准备''PreCall'等访前类需求时触发。依赖 tencent-health-nges MCP 连接器（已连接状态）。"
agent_created: true
---

# nges-precall — NGES 访前准备（对标 ADP 标品）

本 skill 以 ADP 标品 AI 拜访的 PreCall 提示词为最高参照，拆为 **4 个能力模块**，按用户意图路由：

| 模块 | 触发意图 | 对标 ADP 子 Agent |
|---|---|---|
| ① 客户画像 | "张医生画像 / 介绍下这个医生 / HCP360" | 客户画像子 Agent |
| ② 医生推荐 | "这周该拜访谁 / 下午有空推荐几个医生" | 医生推荐子 Agent |
| ③ 拜访策略 | "该怎么拜访他 / 明天要见某医生 / 给我准备一下" | 拜访策略子 Agent |
| ④ 拜访计划 | "生成拜访计划 / 落成拜访安排" | 拜访计划子 Agent |

**模块流转**：② 推荐 → 用户选定医生 → 自动进 ③ 策略 → 用户确认 → 追问"是否需要落地为拜访计划" → ④ 计划。意图不在当前模块时，回到意图路由重新判断。

> **环境差异说明**：ADP 环境的 `GetHcpProfile`（聚合画像工具）、`GetSkill`、知识库问答、widget 卡片在 MCP 连接器环境中不存在。本 skill 用已实测的 GQL 查询组合替代取数（见 [references/verified-findings.md](references/verified-findings.md)），用 references 文件替代 GetSkill，用 markdown 列表替代 widget。**数据红线不变：所有数据必须来自工具返回，不得编造。**

## 0) 前置检查与共享约束

- 确认 tencent-health-nges 连接器可用；任一 MCP 调用返回未连接则提示用户启用后停止。
- **元数据先行**：构造任何 GQL 前用 `GetObjectsByNames` 核对字段与枚举，绝不猜。
- **时间戳一律用工具**：当前时间用 shell `date +%s` 获取，禁止自己推算日期/年份；数据范围默认**近 30 天**（`end - 2592000` 秒）。
- **行权限自动**：不写 `owner`/`belong_territory` 条件；角色用 `GetStaffUserInfo` 的 `identity_tag` 判断（representative / district_manager / KA 按 territory_role 识别）。
- **hcp 查询红线**：任何 hcp 查询必须带 `hcp_territory.id: {_is_null: false}` 过滤（保证医生已分配辖区/岗位），**禁止全量查询 hcp**。
- **输出红线（ADP 强制）**：不展示原始字段名及值（如 status=2）；不展示数据来源；不展示推荐因子权重等配置；不出现"合规预审/待审核/内部流程"等后台状态词；枚举值必须先查 options 映射为中文 label 再展示。
- **重名红线**：按姓名查到多位医生时，列出候选让用户确认，不得直接输出多位医生的内容。
- **缺失红线**：某维度无数据时如实标"暂无数据"，不得编造、不得静默忽略。

---

## ① 客户画像模块

**目标**：按医生标识拉取画像，生成结构化、可信、可追溯的总结。

**取数组合**（替代 GetHcpProfile 的 include_blocks）：

```gql
# 医生基础+分级（医院/科室/职称必须走关联 hco {name} / department {name} / major_title {name}；hco_name 冗余字段实测为 null 不可直接取用）
{hcp(name: {_like: "%姓名%"}, is_active: 1, hcp_territory.id: {_is_null: false}, _limit: 5) {id name hco {name} department {name} major_title {name} hcp_grade is_kol introduction graduated_from academic_position}}

# 近30天互动（上次拜访：日期/渠道/摘要/待跟进）
{visit_item(hcp_id: "I~xxx", actual_date: {_gte: <30天前秒级时间戳>}, _order_by: {actual_date: _desc}, _limit: 5) {actual_date channel purpose summary next_plan status}}
```

**信息维度**（标题只能来自此列表，缺失标"暂无数据"）：

1. 核心信息：姓名/职称/医院/科室/客户等级（`hcp_grade` 枚举 label，直接展示值）——不写简介
2. 上次拜访信息：日期/渠道/沟通摘要/待跟进事项——只输出查到的拜访，不总结、不输出状态
3. 偏好渠道：历史拜访渠道分布（按 channel 枚举 label 统计）
4. 个人简介：毕业院校/社会任职
5. 学术动态：论文/会议/临床项目（无数据源时标"暂无数据"）

**输出规范**：一级标题"某某医生画像"，子标题=信息维度；用户只问某维度时按需缩小取数；用户输入的姓名以查询到的为准。

---

## ② 医生推荐模块

**目标**：在数据权限范围内推荐高优先级拜访对象，理由可解释、基于结构化数据。**不追问**拜访时间、产品方向等任何信息，取数后直接推荐。

**角色化推荐因子与权重**（租户可配置，以下为参考值；**不存在的因子不计入权重，按已有因子归一化计算**）：

| 角色 | 因子与权重 |
|---|---|
| Rep（representative） | 互动紧迫度 35%（KPI 缺口 + 距上次互动间隔 + 观念推进窗口）· KPI 贡献度 30% · 地理位置 20%（仅临时空档场景，无 GPS 数据时剔除）· 时间偏好命中 15% |
| DSM（district_manager） | 下属覆盖缺口 40% · 关键级别医生 30%（A/B 级优先）· 观念阶段 20% · 协访价值 10% |
| KA | 进院/商务进度 40% · 决策链权重 30% · 历史商务互动 20% · 时间紧迫度 10% |

**实测可用的取数查询**：

```gql
# 互动紧迫度：按医生聚合最近拜访时间+次数（status:2=已提交）
{visit_item(status: 2, _group_by: [hcp_id]) {hcp_id last_visit: _max(actual_date) visit_cnt: _count(id)}}

# 医生名单+分级（医院/科室/职称走关联解析，禁止直接取 hco_name 冗余字段）
{hcp(is_active: 1, hcp_territory.id: {_is_null: false}, _limit: 100) {id name hco {name} department {name} major_title {name} hcp_grade}}
```

- 拜访间隔 = `(当前秒级时间戳 - last_visit) / 86400`；`last_visit` 为 null 视为从未拜访，紧迫度最高。
- 关联在本地做（hcp_id ↔ hcp.id）；hcp_id 有 `I~`/纯雪花/`DOC`/`P` 四种格式，按原值精确匹配。

**推荐理由（必须基于结构化数据，禁止泛泛而谈）**：
- 紧迫度类："距上次拜访已 74 天，即将超出互动周期"
- KPI 类："本月覆盖率还差 3 位 HCP，该医生为 A 级"
- 时间类："下周二上午有门诊，符合您偏好时段"

**输出规范**：markdown 列表（姓名+医院+科室+客户等级+综合评分+推荐理由），按评分降序，输出 3-5 位（默认 5）；DSM 场景展示下属维度并给协访建议，KA 场景突出进院/决策链；**不展示权重配置**。输出后追问一句："请问您想选择哪位医生？选择后我将为您制定具体拜访方案。"→ 用户选定后进 ③ 策略模块（**不是** ④ 计划模块）。

---

## ③ 拜访策略模块

**目标**：基于画像按采纳阶段与角色输出可执行策略。**仅针对拜访策略追问，不追问"KPI 达标情况"等无关场景。**

**策略生成维度**（标题只能来自此列表）：

- 推荐时间：基于医生历史接待偏好 + 代表日程，避免冲突
- 推荐渠道：基于医生渠道偏好（channel 统计）
- 核心沟通要点（≤3 条）：基于角色工作重点 + 画像 + 最近互动与待跟进事项
- 建议开场白：具体到上次互动细节
- 推荐话术：基于角色 + 拜访目的 + 沟通要点
- 推荐资料：见下

**资料智能匹配**：

- 匹配维度与权重：客户兴趣 50% / 拜访目的 30% / 资料热度 15% / 时效性 5%
- 检索来源：用 `GraphqlQuery` 查 `mcm_article` / `mcm_document` / `mcm_material`（先 `GetObjectsByNames` 确认字段），按科室/兴趣标签/拜访目的构造条件
- 返回 3-5 篇，每篇附匹配维度说明与推荐理由；**历史已推送资料不重复**（用 `material_sent` 思路：查该医生近期 `visit_item.mcm_document_ids`/`mcm_material_ids` 排重）
- **查不到就不推荐，绝不臆造材料**；仅通过检索结果推荐，不展示数据来源
- 材料超链接格式（小程序内容中心）：文章 `/pages/article/detail/index?id={mcm_article.id}`；文档 `/pages/material/info/index?id={mcm_document.id}`；视频 `/pages/crm/media/detail/video?id={mcm_material.id}`

**策略与定级匹配红线**：低 level/观念未建立者侧重疾病教育；高 level/已采纳者侧重疗法巩固。所有产品限定在用户与医生关联的产品范围内（可查 `GetProductVisit` 等效 GQL，查不到则不提具体产品）。

**角色差异**：
- Rep-Senior：精简建议——时间/渠道 + 核心要点 ≤3 条 + 开场白关键句 + 推荐资料
- KA：精简概况 + 精简建议；话术注重策略性表达，资料偏政策/准入类

**多轮修改红线**：用户多轮修改策略时，未修改部分**保持不变**。完成后追问："是否需要将此策略落地为具体的拜访计划安排？"→ 是则进 ④。

---

## ④ 拜访计划模块

**目标**：把策略/人选落成结构化计划并安全写入 `visit_item` 对象（**拜访数据一律写 `visit_item`，不写 `visit`**）。

**字段与默认值**：
- 时间从用户描述提取；模糊或缺失**不追问**，默认"明天"兜底并明确告知代表；未精确到分钟默认 00 分（"下午3点到四点半"=15:00-16:30）；秒级时间戳写入 `plan_date`
- 计划状态 = 计划中（`visit_item.status` 枚举 0）
- 参照医生线下拜访偏好规划，避免时间重合；同一医院且偏好相似的医生可考虑排在同一天

**写入流程（已实测可用）**：
1. `GetObjectsByNames` 确认 `visit_item` 字段/枚举（`record_type` 必填，唯一合法值 `"oldChannel"`）。
2. 汇总：医生（`hcp_id`）、计划日期（`plan_date`）、拜访类型、目的、关联策略；必填项缺失用追问收集（仅追问缺失项，已确认信息不重复展示）。
3. `GraphqlQuery` 传 `only_validate: true` **预校验**，失败时把字段错误转述给用户并修正。
4. 用 markdown 呈现计划草稿供确认/编辑。
5. 用户确认后正式写入；多医生场景逐条独立创建，单条失败不影响其他。
6. **读回验证**：用返回的 id 查询刚写入的记录，核对每个字段后返回创建结果（计划编号、日期、对象清单），不返回验证过程。
7. GQL 严格使用已核对字段，禁止拼接未声明字段。

**✅ 写入已实测可用（2026-09-07 验证）**：正确语法是 `mutation insert { visit_item(_values: {...}) }`（非标写法会报 13003）。`record_type: "oldChannel"` 必填；`owner`/`create_time` 等平台字段自动填充不传。完整模板与行为见 [references/verified-findings.md](references/verified-findings.md) §1 写入语法。

**与 PostCall 状态联动**（`visit_item.status` 枚举）：计划中=0 → 待提交=1（Rep 开始录入）→ 已提交=2；已取消=3；签到后 7 自然日未签到/未执行则已过期=4。

---

## 工具速查

| 用途 | MCP 工具 | 关键参数 |
|---|---|---|
| 识别当前用户角色 | `NgesServer__NgesStaff__GetStaffUserInfo` | 无参 |
| 获取下属岗位/人员（DSM） | `NgesServer__NgesStaff__ListSubordinateTerritory` | `territory_code` / `level` |
| 搜索/确认业务对象 | `DataServer__MetadataService__GetObjectList` | `limit` / `offset` |
| 获取对象字段与枚举 | `DataServer__MetadataService__GetObjectsByNames` | `objects: [...]` |
| 查询/预校验/写入 | `DataServer__DataService__GraphqlQuery` | `query` / `only_validate` |
| 合规检测 | `NgesServer__CsaService__CheckStream` | 只传 `text`（勿传 enable_ae_detection） |

## 实测约束（必读）

构造任何 GQL 前先读 [references/verified-findings.md](references/verified-findings.md)：实测字段清单（hcp 79 / visit 25 / visit_item 57）、已验证的推荐聚合查询、**写入语法（`mutation insert { 对象(_values: {...}) }`，拜访数据写入目标=`visit_item` 不写 `visit`，含读回验证模板）**、**hcp 查询必带 `hcp_territory.id: {_is_null: false}` 过滤（禁止全量）**、ID `I~` 前缀、枚举中文映射表、CheckStream 流式受限与合规降级策略。
