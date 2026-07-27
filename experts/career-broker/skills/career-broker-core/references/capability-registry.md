# 全局能力编号表（capability registry）

> 意图路由 LLM 输出的执行序列只能从这张表里选编号。
> 主入口 agent 拿到编号 → 按序调用对应 skill 的对应能力。

---

## 编号规则

```
<skill 简码>.<能力序号>
```

| 简码 | skill |
|---|---|
| CB | career-broker 主入口直答 |
| PP | profile-perception 画像构建 |
| QA | career-qa 职业问答 |
| AC | ai-career-agent 测评解读 |
| CC | career-development-consultant 职业发展咨询 |
| LJ | liveflow-job-recommender 活水机会推荐 |
| RG | resume-generator 在职简历生成 |

---

## CB · career-broker 主入口直答

| 编号 | 名称 | 说明 |
|---|---|---|
| CB.BASIC_LIVEFLOW_ELIGIBILITY | 基础活水准入判断 | 不调用 `career-qa`；主入口用内置基础活水规则 + recruit-mcp infoDetail 当前用户 basic 直接判断 |

---

## PP · profile-perception（画像构建）

| 编号 | 名称 | 说明 |
|---|---|---|
| PP.ENTRY | 直接画像入口 | 直接进入数据画像生成；测评仅作为生成后的软性素质补充 |
| PP.A0 | 拉当前用户 basic | 调 recruit-mcp infoDetail，写职位/职级/工作地/员工属性/部门与入司前经历 |
| PP.A1 | 拉近 3 期自评 | 调 自评MCP.listMyAssessments + getSelfAssess，作为司内经历主干 |
| PP.A2 | 早期自评汇总 | LLM 提炼更早期司内主线 |
| PP.A3 | 并行采 TAPD/工蜂 | 多源数据合并；basic 优先来自 infoDetail |
| PP.A4 | 三轴 LLM 提炼 | skills / experiences / traits |
| PP.A4.1 | 兜底追问 basic（仅 infoDetail 失败且 LJ 调用时触发） | 写 basic.position/level/work_location/staff_property |
| PP.A5 | 渲染两份画像 + 写长期记忆 | profile.json + profile_compact.json + 覆盖 memory.md「画像」段 |
| PP.A6 | 给用户看 | profile_summary.md 展示 |
| PP.FULL | 一键全流程 | 直接 A0→A6 生成画像；生成后提示可通过测评补充软性素质 |

> **PP.FULL 不再三选一**：用户主动说“做画像”时直接进入数据画像生成。
> LJ.PRECHECK 触发时同样直接进 A0/A1（推岗位前补画像，必须出完整版）。

---

## QA · career-qa（职业问答，双路由）

| 编号 | 名称 | 说明 |
|---|---|---|
| QA.FILTER | 敏感词前置过滤 | 8 类硬规则拦截（先于路由） |
| QA.ROUTE | 路由判断 | 关键词命中 → recruit_knowledge / xiaoq；默认 xiaoq |
| QA.ASK_RECRUIT_KNOWLEDGE | 调 recruit-mcp 招聘问询知识库 | 活水/招聘类（search_knowledge） |
| QA.ASK_XIAOQ | 调学堂小Q MCP | HR/IT/行政/财经/新人/学习类（覆盖广） |
| QA.FULL | 一键问询 | FILTER + ROUTE + 对应 ASK |

> 基础活水准入判断先走 `CB.BASIC_LIVEFLOW_ELIGIBILITY`，不进入 QA。其他问询类再走 QA.FULL（内部自带路由判断）。

---

## AC · ai-career-agent（测评解读，DNA 驱动）

| 编号 | 名称 | 触发条件 |
|---|---|---|
| AC.OPEN | 测评解读入口 | 用户主动求"看自己"层面的深度解读（雷达图怎么看 / 八锚啥意思 / 我的画像怎么样） |
| AC.M1 | 深度报告解读 + 写长期记忆 | 用户贴 DNA 后；CC.T6 写盘后追加；用户问"帮我看完整解读" |
| AC.M2 | 方向倾向（画像层） | 用户问"我适合什么方向"——只给画像层倾向，不给具体岗位（岗位走 LJ.FULL） |
| AC.M3 | 心理支持（B≥3.5 触发） | 解析到 B≥3.5 自动触发 / 用户表达明显负面情绪 |
| AC.M6 | AI 时代竞争力倾向（推测式） | 用户问"AI 时代怎么提升 / 会不会被替代 / 我有什么优势" |

> **AC 不复刻**：CC.T1（方向建议）/ CC.T4（30 天计划）/ LJ（具体岗位）。
> 涉及这些时由 AC HANDOFF 给对应 skill。

---

## CC · career-development-consultant（职业发展咨询）

主体：教练对话流（始终运行），调用以下"动作工具"：

> **CC 进度显性化**：开场用选择器选 `coach_mode`——`lite` 简要版 5 步、`full` 详细版 16 步；每条回复以 `n/5` 或 `n/16 步骤名` 开头（见 SKILL.md §1 进度标注规则）。默认 lite。

| 编号 | 名称 | 触发条件 |
|---|---|---|
| CC.OPEN | 入口（可能 offer 测评） | 进入 skill 第一句必做；测评 offer 受全局上限约束（见下方“测评 offer 全局限次”） |
| CC.T1 | 给方向建议 | step 8-10 探索阶段 |
| CC.T2 | 案例陪伴 | step 11-13 深化阶段 / **用户主动求案例时立即触发**（最高优先级，主入口可直接路由 `["CC.T2"]`） |
| CC.T2_KM | km 经验文章兜底 | T2 case 0 hit 后用户答应转 km / 用户主动求"经验文章/实战复盘"时；缺 km MCP 走带可复用 PAT 检测的引导 |
| CC.T3 | 课程推荐（QLearning） | step 14-15 承诺阶段 |
| CC.T4 | 30 天行动计划 | step 14-15 承诺阶段 |
| CC.T5 | 邀请测评 | 入口 + step 5-6；**受测评 offer 全局上限约束（跨 skill 共享计数，最多 2 次）**；用户选"做"时调 preview_url 把测评页打开在右侧；**T5 不做深度解读，仅 offer + 写盘 ack** |
| CC.T6 | 测评回流 profile | 用户贴 DNA 时静默调；**T6 调 ai-career-agent 的 scripts/parse_result_code.py + merge_assessment_into_profile.py 写盘**，深度解读交给 ai-career-agent.M1 |
| CC.HANDOFF_LJ | 衔接活水机会推荐 | 用户对方向有承诺时；**整段对话最多主动衔接 1 次**，提过活水但用户没回应就不再二次引导，除非用户自己再提 |

---

## LJ · liveflow-job-recommender（活水机会推荐）

| 编号 | 名称 | 说明 |
|---|---|---|
| LJ.PRECHECK_MCP | 自检 recruit-mcp | 缺则引导装 setup/06，或转方向模式 |
| LJ.PRECHECK_PROFILE | 前置检查画像 | 缺画像 → 路由层切 PP.FULL（跳 ENTRY） |
| LJ.S1 | LLM 决策落点 | 输出 5-7 个职位 GUID |
| LJ.S2 | API 召回 | positionInfoRequests OR 召回 |
| LJ.S3 | 反向标注 + 段位筛 | 本地过滤 |
| LJ.S4 | 加权打分 | top 5-7 |
| LJ.OUT | 经纪人口吻输出 | 渲染推荐结果，附 huoshui 详情链接 |
| LJ.S1_ONLY | 只给方向（mcp 缺/失败兜底） | 跑 S1 后跳 S2-S4，OUT 改方向格式 |
| LJ.PREF | 推完问意向沉淀 | 一句话问 Y/N |
| LJ.FULL | 一键推荐 | PRECHECK_MCP→PRECHECK_PROFILE→S1→S2→S3→S4→OUT→PREF |

---

## RG · resume-generator（在职简历生成）

| 编号 | 名称 | 说明 |
|---|---|---|
| RG.FULL | 生成在职经历简历描述 | 先输出隐私声明 → 取自评MCP原文 → 提炼在职经历 → 写成动宾+量化的简历文档 → **写成 .md 文件并用 present_files 打开在右侧预览**（不再把全文贴聊天里） |

> RG 主要在 LJ 推荐完成后衔接（用户可能要投递）；也可由用户主动"帮我写在职简历"触发。
> 取自评数据前必须先输出隐私声明（见 privacy-statement.md）；简历内容只来自自评原文，不编不注水。

---

## 测评 offer 全局限次（跨 skill 统一）

「测评 offer」= 专家**主动**邀请用户做职业DNA测评。CC 入口选择器 / CC.T5 / PP 画像后置提示 / AC 无码引导都可能 offer，必须共享一个**会话级全局计数 `assessment_offered`**：

- 任何 skill 主动 offer 一次 → 全局 +1；`assessment_offered >= 2` 后所有 skill 不再主动 offer。
- `profile.json#assessment` 已有数据 → 任何 skill 都直接用、不再 offer。
- 用户**主动**要测评（"我想做测评"）→ 不计入次数，直接打开测评页。

完整规则见 `skills/career-broker-core/references/broker-runtime-mechanism.md` §5.5。

---

## 路由 LLM 输出格式

意图路由 LLM 输出严格 JSON：

```json
{
  "intent": "<问询 / 画像 / 发展建议 / 司内资源获取 / 活水机会 / 闲聊>",
  "sequence": ["<编号1>", "<编号2>", ...],
  "context_to_pass": {
    "user_query": "<用户原话>",
    "extracted_direction": "<可选：教练→活水机会推荐时的方向>"
  },
  "_reason": "<一句话路由理由>"
}
```

---

## 典型路由示例

| 用户原话 | sequence | 备注 |
|---|---|---|
| "我现在可以活水吗" | `["CB.BASIC_LIVEFLOW_ELIGIBILITY"]` | 主入口直答：内置基础规则 + infoDetail basic，不走 QA |
| "活水有试用期吗" | `["QA.FULL"]` | QA 内部走 recruit-mcp 招聘问询知识库 |
| "VPN 连不上" | `["QA.FULL"]` | QA 内部走小Q |
| "年假怎么算" | `["QA.FULL"]` | QA 内部走小Q |
| "帮我做画像" | `["PP.FULL"]` | |
| "我最近卡住了 / 给点职业建议" | `["CC.OPEN"]` | 之后由教练流自主调用 T1-T6 |
| "有没有像我这样的人转过 / 类似案例 / 谁走过这条路" | `["CC.T2"]` | 直接进案例陪伴，不必走 T1-T6 全流程 |
| "有没有 X 的经验文章 / 实战复盘 / km 上有吗" | `["CC.T2_KM"]` | 直接进 km 兜底；缺 km MCP 时走可复用 PAT 引导 |
| "看看现在有什么岗" | `["LJ.FULL"]` | 前置检查不通过 → 自动插 PP.FULL；推完可一句话引导 RG 生成在职简历 |
| "帮我根据自评写一段在职简历 / 我的在职经历怎么写" | `["RG.FULL"]` | 取自评原文生成在职经历描述 |
| "我想活水但不知道往哪" | `["CC.OPEN"]` | **先教练理方向**，不直接进 LJ；承诺方向后教练自己调 HANDOFF_LJ。区别于"看看现在有什么岗"（明确要岗→直接 LJ.FULL） |
| "帮我看看我适合什么 / 我适合什么方向" | 有测评数据 → `["AC.M2"]`；无测评数据 → `["CC.OPEN"]` | AC.M2 只给画像层方向倾向、不给具体岗；要具体岗再 HANDOFF LJ。**不要**直接进 LJ.FULL（用户没明说要看岗） |
| "我做过什么 / 我的经历 / 我擅长什么" | `["PP.FULL"]` | 走画像；若用户明说"写成简历"才走 RG.FULL |
| "做完测评了，DNA: ..." | `["CC.T6", "AC.M1"]` | 先静默写盘，再切 ai-career-agent 给深度解读 |
| "我的画像怎么样 / 雷达图怎么看 / 八锚啥意思" | `["AC.OPEN"]` | 测评深度解读 skill |
| "AI 时代我会被替代吗 / 我有什么优势" | `["AC.M6"]` | 推测式 AI 时代竞争力分析（需要已有 assessment 数据） |
