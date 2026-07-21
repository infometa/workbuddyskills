# examples-index.md —— 端到端样例索引

> 本 Skill 的端到端样例(含 input.json / result.json / provenance-audit.json + 4-5 渲染产物 + 各档 README)
> 全部存放在项目根 `demos/knowledge-framework-builder/`,与 `paper-quick-reader` 风格对齐(避免污染 LLM 的 references token 视野)。

## 完整样例位置

| 类型 | 位置 |
|---|---|
| input + result + 渲染 + audit | `demos/knowledge-framework-builder/result-fixtures/` |
| (规划)HTML 报告 demo | `demos/knowledge-framework-builder/html-demos/`(v0.6 Step 9 主动询问后才生成)|

## 已落地样例(v0.2 → v0.5)

| 样例 | 模式 | 深度 | 数据源 | 节点 | 讲解 | 依赖 | 渲染 | 验证亮点 |
|---|---|---|---|---:|---:|---:|---:|---|
| `topic-only-cet/` | `topic_only` | skim | `course_topic` | 94 | 0 | 0 | 4 | v0.2 最小 dogfood:纯主题输入 + 全 ai_inference + 顶部 ⚠️ banner |
| `compact-cet/` | `topic_only` | skim | `course_topic` | 22 | 0 | 0 | 4 | v0.2 紧凑模板:小尺寸 fixture 用于回归 |
| `topic-with-focus-cet/` | `topic_only` | skim + **guided** | `course_topic + focus_topics + user_level` | 94 | **8** | 0 | 4 | v0.3 跨子树 8 个 200-500 字讲解 + `<details>` 折叠块 |
| `topic-deep-with-deps-cet/` | `topic_only` | skim + guided + **deep** | + `deep_explain + concept_dep=aggressive` | 94 | **13** | **12** | **5** | v0.4 子树 deep + 6 类依赖 + DEEP_BATCH_TRUNCATED warning + Mermaid flowchart |
| `material-markdown-ml/` ★ | **`hybrid`** | skim + guided | + `markdown_path`(真实教材) | 38 | 6 | 5 | 5 | **v0.5 真实 N-gram 闭环:32 high / 1 故意 failed / 5 ai_inference skipped** |

## 计划样例(对应 `_skill_meta.json` 的 `example_cases`)

| 样例 | 模式 | 深度 | 数据源 | 验证点 | 计划版本 |
|---|---|---|---|---|---|
| `textbook-outline-higher-math-docx/` | `material_first` | skim + guided | `docx_path`(《高等数学(同济版)》目录) | docx 零依赖解析 + 节点级 evidence_locator | v0.6 |
| `personal-notes-ml-deep/` | `material_first` | 三档全开 | `markdown_path` + `deep_explain` | 全叶子讲解 + 真 N-gram 高命中 | v0.6 |
| `hybrid-deep-with-deps/` | `hybrid` | 三档全开 + aggressive 依赖 | `markdown_path` + `course_topic` | 6 类依赖在真实材料上的挖掘质量 | v1.0 |
| `cet4-curated-syllabus/` | curated | skim + guided | 内置 CET-4 大纲 | curated_syllabus evidence_source 路径 | v1.1 |

## LLM 使用建议

- **了解输入输出契约** → 直接读 `material-markdown-ml/input.json` + `result.json` 是最快路径(覆盖最多字段)
- **写 few-shot prompt 出讲解** → 用 `topic-with-focus-cet/explanations.json` 的 1-2 条做 in-context 示例
- **写 few-shot prompt 出依赖** → 用 `material-markdown-ml/dependencies.json`(conservative, 5 边)+ `topic-deep-with-deps-cet/dependencies.json`(aggressive, 12 边)
- **debug 渲染** → 让 `scripts/render_outputs.py` 跑任一 fixture 的 `result.json` 重出 5 格式,对比 fixture 确认
- **回归测试** → 跑 `assemble_result.py` 重组装 + diff 校验
- **不要做的事** → 不要把 fixture 全文塞进 LLM Prompt,会浪费 ~5-30KB token;改用本 Skill 的 `framework-rubric.md` + `prompt-templates.md` 提供 schema + checklist

## Provenance verdict 命中分布(用于教学 / 对外宣传)

`material-markdown-ml` fixture 的 `provenance-audit.json` 是本 Skill「核心原则 4」的最佳展示样本:

```json
{
  "verdict_counts": { "high": 32, "medium": 0, "low": 0, "failed": 1, "skipped": 5 },
  "high_ratio": 0.97
}
```

含义:
- **high (32)**:LLM 生成的 evidence_locator.excerpt 在原文 N-gram 上 ≥ 0.85 命中 → 用户可放心
- **failed (1)**:`n4.5 留出法 vs 交叉验证选择` —— 我们故意伪造的 excerpt 被脚本抓住 ✅
- **skipped (5)**:LLM 自加的概括节点(`n2.3.3` `n4.4` `n6` `n6.1` `n6.2`)诚实标 ai_inference,不冒充教材

## 与本 Skill 其它文档的关系

- 各样例的设计取自 `concept-dependency-taxonomy.md` §8 的依赖图规划
- Provenance 状态(skipped / high / low / failed)的实例分别由不同样例验证(详见每个 fixture 的 README §"本例验证了 SKILL.md 的哪些契约")
- `prompt-templates.md` §8 给出了"哪个 Step 的模板对应哪个样例"的映射表
- `outline-parsing-heuristics.md` §3 的启发式样例 == `material-markdown-ml/textbook.md` 的真实 markdown ATX 命中
