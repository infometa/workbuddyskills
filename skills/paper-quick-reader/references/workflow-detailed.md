# 详细工作流（9 步完整版）

> 从 SKILL.md 主文抽出（v0.4.7 瘦身）。主文保留浓缩表格 + 决策树；本文件保留每步的判定/分支/CP/降级路径全细节。
> **何时读**：Agent 第一次接到论文速读请求、或对某一步的判定逻辑不确定时。

## Contents

- [Step 0 mode 确认](#step-0-mode-确认)
- [Step 1 输入校验 & 深度档位判定](#step-1-输入校验--深度档位判定)
- [Step 2 解析](#step-2-解析)
- [Step 3 裸读 Skim](#step-3-裸读-skim)
- [Step 4 引导 Guided](#step-4-引导-guided)
- [Step 5 精读 Deep-dive](#step-5-精读-deep-dive)
- [Step 6 对比 Compare](#step-6-对比-compare)
- [Step 7 Provenance 审计](#step-7-provenance-审计)
- [Step 8 报告生成询问](#step-8-报告生成询问)
- [Step 9 多轮追问闭环](#step-9-多轮追问闭环)

---

```
┌─────────────────────────────────────────────────────────────────┐
│ Step 0  mode 确认                                               │
│   papers 长度 = 1 → mode = single                                │
│   papers 长度 2~10 → mode = compare（必须附 compare_dimensions）│
│   papers 长度 > 10 → 拒绝，建议分批或改用文献综述 Skill          │
│   papers 缺失 → 追问用户提供 PDF 路径或粘贴文本                   │
│   【CP-0 检查点】mode=compare 自动判定后，先向用户复述：           │
│     "识别到 N 篇论文，将进入 compare 模式，对齐维度 = [...]"，    │
│     等用户回 "确认 / 改维度 / 改篇数" 后再进 Step 2；             │
│     用户沉默或 "继续" → 默认按推断进入                             │
├─────────────────────────────────────────────────────────────────┤
│ Step 1  输入校验 & 深度档位判定                                  │
│   逐篇检查 papers[i].source：                                    │
│     - arxiv_url / arxiv_id → 走 TeX 优先分支（见 Step 2）        │
│     - pdf_path / docx_path / pasted_text → 通过                 │
│     - image_path → 拒绝并返回错误（不做 OCR）                    │
│   检查 context 决定深度档位组合：                                │
│     - context 空 → [skim]                                       │
│     - context.my_direction → [skim, guided]                     │
│     - context.specific_question → [skim, deep]                  │
│     - 都有 → [skim, guided, deep]                               │
│     - mode == compare 时追加 [compare]                          │
│   preferences.depth_hint 强制覆盖上述推断（force_skim/force_deep）│
│   preferences.writing_style：analytical（默认）/ feynman         │
│     → feynman 时读 references/feynman-style-rubric.md            │
│   preferences.include_peer_review：false（默认）/ true           │
│     → true 时 Step 5 读 references/reviewer-perspective.md       │
│   【CP-1 检查点】depth_hint=force_deep 且无 specific_question 时 │
│     **必须**先列出 AI 自拟的 5 个候选问题给用户，由用户回         │
│     "全部 / 选 1,3,5 / 改写第 2 条 / 我自己出" 后再进 Step 5；    │
│     此 CP **不可默认**——沉默必须再次追问，严禁代用户决定问什么   │
├─────────────────────────────────────────────────────────────────┤
│ Step 2  PDF / TeX / Word / 文本解析                             │
│   arxiv_url / arxiv_id 分支（v0.2.0 新增，首选）：               │
│     run: python scripts/fetch_arxiv_tex.py {input}              │
│     下载 TeX tarball + 并行 PDF（用于页码映射）                   │
│     失败时自动降级到 parse_pdf.py（PDF 回退 URL）                │
│     完整协议见 references/arxiv-fetch-protocol.md                │
│   pdf_path / docx_path / pasted_text 分支（原流程）：            │
│     run: python scripts/parse_pdf.py --input X --out paper_a.json│
│   统一输出 (text, page, section) 三元组列表                      │
│   识别 Title / Authors / Year / Venue / Abstract /              │
│     Sections / References                                        │
│   图像层 PDF → 报错退出                                          │
│   pasted_text → 追问"这段来自论文的第几页？"无答则段落编号替代   │
│   见 references/pdf-parsing-heuristics.md                       │
├─────────────────────────────────────────────────────────────────┤
│ Step 3  裸读（Skim，每篇必出）                                   │
│   读 references/summary-card-rubric.md                          │
│   抽取 6 基础字段：research_question / method / dataset /       │
│     key_results / contributions / limitations                    │
│   抽取 2 扩展字段（v0.2.0 新增）：                               │
│     - method_formula（方法公式化，2–4 核心元素）                 │
│     - one_line_plain（大白话一句话，≤40 字，无术语）              │
│   每字段必带 provenance_map[field] = {page, section}             │
│   扩展字段的 provenance 用 aggregate_pages                       │
│   生成 recommended_questions（默认 3 条，按 preferences 可调）    │
│   每条推荐问题附 why（回答这个问题对用户的价值）                  │
│   writing_style == feynman → 全部自然语言字段按 9 红线 + 4 原则重写│
├─────────────────────────────────────────────────────────────────┤
│ Step 4  引导（Guided，若 context.my_direction 存在）             │
│   读 references/guided-connection-taxonomy.md                    │
│   挖掘 3–7 条 connection_points，每条必含：                      │
│     - type（6 种之一：methodology_reusable / baseline_reference /│
│       gap_identified / data_overlap / novelty_related /         │
│       theory_extension）                                         │
│     - insight（具体到"本文的 X 可用于你的 Y"）                  │
│     - evidence_pages（必填）                                     │
│     - relevance_score（0.0-1.0）                                 │
│     - user_notes_placeholder（v0.2.0 新增，3 子字段留空给用户填） │
│   严禁产出无具体 evidence_pages 的空泛关联                        │
│   严禁 AI 预填 user_notes_placeholder（那是用户视角槽）          │
│   【CP-4 检查点】connection_points 列表生成完毕后，向用户复述     │
│     top-3（按 relevance_score 降序）+ 总数 N，问                  │
│     "保留全部 / 删除第 X 条 / 第 Y 条要重挖更具体的 evidence"，   │
│     用户沉默或 "继续" → 默认保留全部进入下一步                     │
├─────────────────────────────────────────────────────────────────┤
│ Step 5  精读（Deep-dive，若 context.specific_question 存在）    │
│   读 references/deep-dive-protocol.md                           │
│   针对 specific_question 产出：                                  │
│     - answer（综合回答）                                         │
│     - original_excerpts（≥1 条，每条必含 page + section + text） │
│     - critical_analysis 三段式：                                 │
│       * agree_with（哪些是可信的）                               │
│       * question（哪些值得质疑 / 作者未讨论）                    │
│       * complement（对用户方向的补充视角）                       │
│   论文未涉及该问题 → 诚实回答"原文未提及"，不编造                 │
│   若 preferences.include_peer_review == true 或 specific_question │
│     含审稿关键词 → 追加 peer_review 字段（5 维度 + 判决）         │
│     读 references/reviewer-perspective.md                        │
├─────────────────────────────────────────────────────────────────┤
│ Step 6  多篇对比（Compare，若 mode == compare）                 │
│   读 references/comparison-dimensions.md                         │
│   对 compare_dimensions 每个维度组装 table row：                 │
│     **表格格式（严格使用 dimension-major）**：                   │
│     table = [                                                     │
│       { "dimension": "method",                                   │
│         "rows": { "A": {content, provenance},                   │
│                   "B": {content, provenance}, ... } },           │
│       { "dimension": "dataset", "rows": {...} }, ...             │
│     ]                                                             │
│     ⚠️ 禁止使用 paper-major 格式（table[i].paper = "X"）         │
│     - 每篇论文该维度的 content + provenance{page, section}        │
│     - 取不到信息 → content = "—"（em dash）+ 说明              │
│   生成 differences_narrative 差异叙述（至少 2 个 theme）         │
│   若 context.specific_question：额外输出 cross_paper_answer      │
│   若 context.my_direction：额外输出                              │
│     key_takeaways_for_user_direction                            │
├─────────────────────────────────────────────────────────────────┤
│ Step 7  Provenance 审计（防幻觉闭环）                           │
│   run: python scripts/verify_provenance.py                      │
│     --result result.json --papers paper_a.json paper_b.json     │
│   所有含数字 / 专名 / 方法名 / 数据集名的 claim 做 ngram 校验    │
│   3-gram + 5-gram 双粒度，按置信度分级                           │
│   ngram_match_confidence: high / medium / low                   │
│   hallucination_risk: low / medium / high                       │
│   匹配失败 → 回流用户确认或从输出中移除                           │
│   输出 provenance-audit.json                                    │
│                                                                   │
│   【zh-paraphrase 注意】language=zh 时，中文改写英文原文会导致    │
│   5-gram 自然失配，触发 confidence_degraded=true —— 这是预期     │
│   信号，**不是幻觉报警**。真正需要告警的是：                      │
│     ① hallucination_risk=high（关键数字/专名被篡改）             │
│     ② failed 条数 ≥ 3 + 占比 > 40%                              │
│   如需更高 ngram 命中率，可设 preferences.language=en 让 LLM     │
│   直接复用原文 5-gram，避免 paraphrase 失配。                     │
├─────────────────────────────────────────────────────────────────┤
│ Step 8  默认不输出报告；主动询问是否生成 + 选哪种格式             │
│   【强制】默认行为：在 chat 中给出速读结论后，**不**自动生成任何   │
│   报告文件。Skill 必须在末尾主动追加询问，给用户多选/全选权：     │
│                                                                   │
│     "📋 速读已完成。需要保存为可分享/归档的报告吗？               │
│       请选择一个或多个格式（可全选；不选即跳过）：                │
│       □ pdf —— 适合发给导师/老板/打印                             │
│       □ html —— 适合在浏览器查看 / 邮件分享（单文件）             │
│       □ md —— 适合进 Obsidian/Notion/笔记系统                    │
│       □ all —— 三种全要"                                          │
│                                                                   │
│   用户选择映射 → render_report.py --format：                      │
│     "pdf"          → run: render_report.py result.json -f pdf     │
│     "html"         → run: render_report.py result.json -f html    │
│     "md"/"markdown"→ run: render_report.py result.json -f md      │
│     "all" / 多选   → run: render_report.py result.json -f all     │
│       （-f all 生成 html+md+pdf 三件齐套，文件名自动加后缀）       │
│     未选 / 沉默 / 任何拒绝（"不用 / 跳过 / no"）→ 直接跳过；      │
│     绝不追问第二次                                                │
│                                                                   │
│   产物路径：./reports/paper-reports/<ts>-<mode>-<slug>.{pdf|html|md}│
│                                                                   │
│   PDF 注意事项：                                                   │
│     - 需要本地有 weasyprint（`pip install weasyprint`）；         │
│     - 未安装时 render_report.py 会自动降级 HTML 并提示用户        │
│       "请打开 .html 后用浏览器 ⌘+P 打印为 PDF"，不报错。          │
│                                                                   │
│   严禁：                                                           │
│     - 未经用户同意直接生成任何报告（包括 HTML/MD/PDF）            │
│     - 用户未明确选格式时擅自挑一个生成                             │
│     - 仅因为 chat 内容长就主动写文件                               │
├─────────────────────────────────────────────────────────────────┤
│ Step 9  多轮追问闭环（同 session 继续问已读论文时）              │
│   触发：本轮无新 papers，且用户表述含「再问 / 继续 / 那个 /      │
│         它的 / 上面这篇」等指代性追问。                           │
│   动作：复用 parse cache + 复用上一轮 result.json，仅追加         │
│         deep_dive_answers[i]，不重出 summary_card。               │
│   完整协议（5 项动作 + 触发判定 + NEVER 列表）：                  │
│         → references/follow-up-loop-protocol.md                   │
└─────────────────────────────────────────────────────────────────┘
```
