# Development Pipeline Orchestrator（开发流水线编排专家）

A WorkBuddy expert that drives a feature, fix, or change **from idea to merged branch** through one disciplined pipeline — instead of jumping straight into code and hoping for the best.

## What it does

It treats "build a thing" as a verifiable, reviewable, reversible pipeline and orchestrates specialized execution units (subagents) stage by stage, holding a quality gate at each checkpoint:

- **Intent clarification first** — Before any creative or build work, explores real goals, constraints, trade-offs, and design. Turns a fuzzy "make a feature" into a structured, reviewable spec. Process comes before implementation.
- **Test-driven task planning** — Decomposes the spec into a bite-sized implementation plan assuming the executor has zero codebase context: exact file paths, complete code in every step, exact commands with expected output, clear task interfaces. DRY / YAGNI / TDD / frequent commits. No placeholders allowed.
- **Isolated workspace** — Ensures an isolated workspace (native tooling or git worktree fallback) before execution. Never starts implementation on main/master without explicit consent.
- **Subagent-driven execution** — Dispatches a fresh, isolated-context implementer subagent per task. Curates exactly the context each one needs; the subagent never inherits session history. Executes the whole plan continuously — only stops on a blocker it cannot resolve, genuine ambiguity, or completion.
- **Two-stage review gate** — Every task passes spec-compliance (no over- or under-building) **and** code-quality review; Critical/Important findings trigger a fix-and-re-review loop. A broad whole-branch review runs once at the end.
- **Parallel dispatch** — For 2+ independent problems (different files, subsystems, bugs), dispatches focused subagents concurrently instead of investigating serially.
- **Verify before completion** — Never claims "done / fixed / passing" without first running the real verification command and showing the real output.
- **Finish the branch** — After all tasks are verified green, runs the full suite, presents structured options (merge / PR / cleanup), and executes the choice.

## When to use it

Use this expert at the start of any non-trivial build or multi-step engineering effort — a new feature, a substantial change, or executing an implementation plan end to end. If you only need one stage in isolation (just planning, just execution, just a review), a stage-specific expert may be enough.

## Principles

Orchestrate, don't over-build · Think before you build · Process before implementation · Bite-sized, test-driven, verifiable tasks · Fresh subagent per task · Two-stage gate per task · Evidence before any success claim · Stop and ask when blocked, never guess.

## Files

- `.codebuddy-plugin/plugin.json` — plugin metadata
- `agents/dev-pipeline-orchestrator.md` — the expert agent definition

## Category

`02-Engineering`

## Risks & mitigations

- **Risk:** Drives subagents that execute shell commands, write code, and create commits. **Mitigation:** Work happens in an isolated workspace off main/master; review gates run between every task; verifications require real command output before any completion claim.
- **Risk:** Subagents operate on curated, partial context and can make systematic errors. **Mitigation:** Each task is reviewed independently (spec + quality); parallel dispatch results are spot-checked and the full suite is run before integration.

## 使用方式

在 WorkBuddy 中启用本专家后，直接用自然语言描述你要推进的工作即可触发，例如：

- "帮我把这个功能从想法推进到合并入主干，走完整的开发流水线"
- "把这份需求拆成测试驱动的细粒度任务计划，含精确文件路径与完整代码"
- "逐任务派子代理执行这份计划，每个任务过规格与质量双门评审"

专家会先判断你处在流水线的哪一环（意图澄清 / 任务规划 / 执行 / 评审 / 收尾），再路由到对应阶段。若你已有现成的实现计划，可直接让它进入执行阶段；若只有模糊想法，它会从意图澄清开始。执行全程在隔离工作区进行，每个任务过双重评审门，验证通过后再收尾集成。
