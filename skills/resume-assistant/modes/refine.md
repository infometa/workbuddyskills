# mode: refine · 基于用户反馈做多轮细修

> **前置**：先读 [`_shared.md`](_shared.md)。本文件只讲 refine 的差异。

## 触发条件

- 用户对 `tailor` / `rewrite` 的结果不满意，要求细化："第 2 条改得太虚 / 这段用英文被动语态改一下"
- 明确 `mode: "refine"`（或紧接在某次其它 mode 之后且处于同一会话）
- **单条 bullet 防幻觉请求**（如"帮我把'参与 XX 项目'改得更匹配 JD"）——即使没有前置 tailor 会话也走 refine

## 输入

- `version_control.version_id`：要修改的版本；若省略则默认最新一次操作的 version
- `refine.feedback`：用户反馈文本 + 可选 `target_items`（指定改哪几条 bullet）

## 产物规模：轻量 vs 完整（按输入规模自动选择）

refine 有两种产物规模——自动判断，无需用户指定：

| 条件 | 产物规模 | 产出清单 |
|---|---|---|
| **≤ 1 个 bullet / 1 段短文本**（单条改写、防幻觉问答、占位符补充）| **轻量模式** | `rewrite-candidates.md`（2-4 候选 + `rewrite_action` 标注）+ `clarifying-questions.md`（1-3 个追问）+ `provenance-audit.json`（仅本次改写）。跳过 diff-report、strategic-appendix、manifest 更新。 |
| **≥ 2 个 bullet 或整段反馈**（多条细修）| **完整模式** | 原有全量产物：diff-report-refine-\<ts\>.html + 三维度审计报告 + 更新 manifest |

**为什么这样设计**：用户提一条 bullet，期望的是"给我几个候选改写 + 追问真实情况"。产出整套 diff-report + strategic-appendix 会把重点淹没在文件堆里，并让 LLM 在用户不需要的结构上浪费 token。轻量模式把注意力聚焦在"候选改写 + 提问 + 防幻觉审计"——这才是单 bullet refine 的核心价值。

## 与骨架的差异

refine 是小刀子，不跑全流程：

| Step | 差异 |
|---|---|
| Step 0 | mode 已定；**同时判断产物规模**（≤1 bullet → 轻量；≥2 → 完整）|
| Step 1 | 不追问 experiences；从当前 version `result.json` 里取素材 |
| **Step 2-3** | **跳过**（沿用目标 version 已记录的 role_family / archetype / JD）|
| Step 4 | 仅改写用户指定的 bullet（或反馈提到的段落）；保持未提段落原样 |
| Step 5 | 三维度 **全跑**（细修最容易不经意放大语气或编造）|
| Step 6 | 若 version 原先关联 JD 且完整模式 → 重算 coverage；轻量模式跳过 |
| Step 7 | **完整模式**：原地更新 version 目录 + `diff-report-refine-<ts>.html`；**轻量模式**：只写 `rewrite-candidates.md` / `clarifying-questions.md` / `provenance-audit.json`，不更新 manifest |
| Step 8 | 只对**被改动的 bullet** 跑审核；轻量模式审核内容并入 `provenance-audit.json` 的 `user_review_required` 字段 |

## refine 循环限制

- 同一 version 的 refine 次数上限：**5 次**（超过 5 次建议用户 mode=rewrite 从 master 重新派生）
- 每次 refine 必须附 `feedback` 字段，否则拒绝（防止盲目反复跑）

## refine 独有的 NEVER

- 不修改未被用户点名的 bullet（"帮我改第 3 条"不意味着其他条也可以改——用户有知情权）
- 不改变 `version_label` 或 `parent_id`（refine 是在同一版本上迭代，不是派生新版本）
- 完整模式必须生成 `diff-report-refine-<ts>.html`（用户有权知道每次细修改了什么）
- 轻量模式不生成 diff-report 和 strategic-appendix（不堆不必要的文件）

## 成功判定

**轻量模式**：
- `rewrite-candidates.md` 包含 ≥2 个候选，每个都标注 `rewrite_action` 名称
- `clarifying-questions.md` 包含 ≥1 个引导用户补充真实素材的问题
- `provenance-audit.json` 记录每个候选的 `hallucination_risk` 等级

**完整模式**：
- 用户反馈被逐条回应
- 新的 `diff-report-refine-<ts>.html` 生成
- 三维度审计通过 + 改动 bullet 的 Step 8 approved
