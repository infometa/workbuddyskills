# mode: tailor · 基于 master 针对 JD 做定制（**最常用主流程**）

> **前置**：先读 [`_shared.md`](_shared.md)。本文件只讲 tailor 的差异。

## 触发条件

- 用户说："按 XX 公司 JD 改我的简历 / 对着这个岗位重写简历"
- 用户提供 JD 文本 **且** `_master/` 已存在
- 用户明确要求 `mode: "tailor"`

## 输出定位

**派生版 → `resume-output/<version_label>/`**，`parent_id: "<master_version_id>"`，`is_master: false`。

`version_label` 推导规则（按优先级）：
1. 用户显式提供 `version_control.version_label`
2. 从 JD 推断：`<company>-<role_family>-<timestamp>`（示例：`bytedance-ai-platform-20260424`）
3. Fallback：`tailor-<timestamp>`

## 与骨架的差异

| Step | 差异 |
|---|---|
| Step 0 | mode 已定 |
| **Step 0.5** | **必跑** · Preflight 三选项：模板 / 长度 / 语言（v0.3.2 · `references/preflight-questions.md`）。若 master 已有 preferences 字段且用户未明确改，**继承 master**，仅在用户主动改时问 |
| Step 1 | 若 `_master/` 存在 → 跳过 experiences 追问，以 master 为素材源；若用户提供新素材则合并 |
| **Step 2** | **必跑** · `python3 scripts/parse_jd.py --jd-file <X>`，记录 `role_family / seniority / ai_archetype` |
| Step 3 | archetype 输出挂到当前 version 的 `result.json.archetype`；措辞库按 `(role_family, archetype, language)` 三元组切换 |
| Step 4 | 主要动作是**重写 master 的每条 bullet** 以命中 JD 关键词。动作列表严格限制于 provenance-rules §2.3 的 11 种 `rewrite_action`；**bullet 写法参考** [`../references/bullet-formulas.md`](../references/bullet-formulas.md) §1-§5（X-Y-Z + STAR + CAR + 量化策略 + 缺数 fallback）|
| Step 5 | 三维度 Provenance 全部必跑。**维度二特别检查**：是否出现语气升级（"参与"→"主导"）|
| **Step 6** | **必跑** · `coverage_before`（master vs JD）vs `coverage_after`（当前定制版 vs JD）；目标定制版 ≥ 80%；**关键词频控**遵循 [`../references/ats-rules.md`](../references/ats-rules.md) §3（核心词 2-4 次 / 重要词 1-2 次）|
| **Step 7** | 写 `resume-output/<version_label>/` + **必生成** `diff-report.html`（base=master）+ `jd-match-report.md` + **🆕 v0.3.2 默认追加 `strategic-appendix.md`**（4 章节：Strengths / Gap / Interview Tips / CL Hooks · 规格见 [`../references/strategic-appendix-spec.md`](../references/strategic-appendix-spec.md)）|
| Step 8 | 审核要点：**语气升级 / 数字夸大 / 技能增补 3 类改写**全部必须用户确认 |

## 典型对话开场

> 用户：（粘贴字节 AI 平台岗位 JD）"按这个 JD 改我的简历"
>
> Skill（应）：
> 1. 读 `_manifest.json` 确认有 `_master/` → mode = tailor
> 2. 跑 `parse_jd.py` → 得到 `role_family=tech`、`ai_archetype=AI_Platform_LLMOps`（高置信度）
> 3. 推导 `version_label` = `bytedance-ai-platform-20260424`
> 4. 按 archetype 的 `framing_hint`（"系统稳定性/SLO/评测体系/故障排查"）重写 master 里与平台相关的 bullet
> 5. 如果 master 缺 JD 关键词（如 "evals"），**不编造** → 在 `jd-match-report.md` 列出缺失项请用户补素材
> 6. Step 5/6 → Step 8 审核

## tailor 独有的 NEVER

- **NEVER** 覆盖 master 本身（master 只能通过 `mode: rewrite` 或用户显式 `mode: generate --force-new-master` 变更）
- **NEVER** 删除 master 不含但"看起来 JD 需要"的技能（不编，但也不从其它地方挪）
- **NEVER** 跳过 `diff-report.html` 生成（用户有知情权）
- **NEVER** 在 coverage < 60% 时仍标记 `processing_status = ready`（需 WARN 用户）
- **NEVER**（v0.3.2）跳过 strategic-appendix.md 产出（除非用户在 preflight 明确说"只要简历，不要附录"）
- **NEVER**（v0.3.2）在 strategic-appendix.md 里编造用户没说过的事（"建议补一门 XX 课程"——除非用户素材里出现过该意向）

## 成功判定

- `_manifest.json` 新增一条 `version`，`parent_id` 指向 master
- 定制版 `coverage_after ≥ 80%`（或 WARN 用户并允许 override）
- 三维度审计通过 + Step 8 用户 approved
- `diff-report.html` 正确生成（可以用浏览器打开看）
