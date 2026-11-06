---
name: cnki-edu-ai-zujuan-paper
display_name: 智能组卷
display_name_en: AI Test Paper Composer
description: 从组卷要求或双向细目表出发，智能匹配知识点、实时选题并逐题取解析，一键产出试卷、解析与细目表三件套。
description_zh: 从组卷要求或双向细目表出发，实时选题、逐题取解析，一键产出试卷、解析与细目表三件套。
description_en: Composes exam papers from requirements or a blueprint with live question selection and per-question analysis, delivering paper, solutions and blueprint in one run.
category: education
version: 1.0.1
author: 知网 edu
---

# AI 组卷 · 成卷编排技能

把「组卷意图」变成「成品试卷三件套」。本技能是**编排层**：拆解需求、归一化参数、驱动选题、取解析、排版与导出。**取数**交给已连接的 `edu` MCP 的 `tk*` 工具。

> **版本 v1.0（对外发布版）**：本技能已实现「接口错误 fail-fast + 题位判重」的成熟处置机制——**任一接口（服务级）出错 → 立即退避重试第二次；第二次仍失败 → 立即停止任务并结构化报告给用户**，不得自动续跑、不得改路径硬跑；**参数级错误（考点名无效 `code:500`）不触发本规则、走降级**；**唯一例外**＝链路 B `mcp__<SERVER>__tkQuestionSame`：**先执行文档化等价降级（关键词召回，须显式标注）**，**降级后仍连续 2 次失败才中止**（两接口计数独立）。题位判重（SID 判重 + 题干哈希兜底）一并生效。**版本演进见 `CHANGELOG.md`。**

> **本文件的定位**：**路由 + 索引 + 红线**。规则**正文**一律在 `references/`，此处只给「一句话口径 + 路径」。读细则按「参考文档」节的**批读纪律**执行。

## 🔐 前置权限校验（最高优先级，必须最先执行）

> 权限校验的「三态诊断 / 通用版兜底 / 强制转化卡 / 连接器加载指引」统一见本技能 `references/_shared.md`「一、权限固定提示」，本章节仅保留本技能专属说明，不重复展开。

> **本技能属①档强依赖**：核心产出需知网数据支撑，无权益即停止、不编造（通用版兜底与转化卡原文见 `references/_shared.md`「一、权限固定提示」）。

本技能的**全部真实数据**（题库真题 / 官方解析 / 知识点 / 学科码 / 教材目录）均来自「知网 edu（基教）」MCP，即 `edu` 连接器的 `tk*` 工具（`mcp__<SERVER>__tkSearchQuestion` / `mcp__<SERVER>__tkSearchSubjectQuestion` / `mcp__<SERVER>__tkQuestionAnalysis` / `mcp__<SERVER>__tkPoint` / `mcp__<SERVER>__tkSubject` / `mcp__<SERVER>__tkBook` 等），需账号拥有「知网基教」权益才能调用。在调用**任何** edu MCP 数据工具**之前**，必须先做权限校验：

0. **先 `ToolSearch(tool_names:["userState"])` 确认 edu 工具在本会话「可解析」**：若查不到 → 属**态 A（连接器未加载/掉线）**，按`references/_shared.md`「一、权限固定提示」给「连接器加载指引」，**不要**直接给购买权益卡，也不要调用任何 edu 工具。
1. 调用 `mcp__<SERVER>__userState` 工具（edu MCP 提供的权益校验接口，**无参数**）。
   - 工具名写法：`mcp__<SERVER>__userState`（`<SERVER>` 取自连接器「显示名」，会随重命名变化；若查不到，用 `ToolSearch(tool_names:["userState"])` 反查真实名称后再调用）。
2. **返回 `true`** → 账号有基教权益，正常进入流程。
3. **返回 `false`（态 B）** → 账号**没有**基教权益，按`references/_shared.md`「一、权限固定提示」「通用版兜底 + 强制转化卡」处理：
   - 不调用任何 `tk*` 工具，改走通用版完成不依赖知网数据的部分；
   - 也不要用"接口报错 / 无结果 / 题库无覆盖"去猜测原因——根因就是没权限；
   - **⛔ 严禁编造知网数据**：不得改用大模型自身知识、公开网络资料、本地文件等非知网接口数据来"凑"出标为知网来源的题库 / 解析 / 知识点；通用版完成不依赖知网数据的部分，并原样输出「解锁知网数据增强层」。

> ⚠️ 无基教权益时的处理（通用版兜底 + 强制转化卡）统一见 [_shared.md](references/_shared.md)「权限固定提示」，本 skill 不再重复誊写。

## 何时使用
- 用户给出**组卷要求**：学段 / 学科 / 范围 / 题型 / 题量 / 来源 / 难度 / 分数
- 用户给出**双向细目表**（Excel、表格或文本），要求据此组卷
- 用户给出**原题文本或截图**，要求出相似题 / 变式题（题找题）→ 见下方**场景 g**
- 用户要对**已成卷**做换题 / 换序 / 改分 / 相似题替换
- **用户说「找 N 道课后练习题 / 练习题 / 巩固题 / 课后作业 / 出一份练习」——默认也走本技能（产出练习卷三件套），不要只停在 「按知识点搜题、给一份题单」的做法。** 路由判据：用户要的是「可直接使用的练习卷」而非「看一眼题」即走组卷（例：「帮我找 5 道物质的量课后练习题，覆盖三个不同难度」→ 组卷，非搜题）。

## 两条产物链路（先分流，再执行）

| | 链路 A · 标准组卷 | **链路 B · 场景 g 题找题·相似题巩固** |
|---|---|---|
| 锚点 | **知识点**（用户给要求/细目表） | **用户给的原题**（文本或图片） |
| 产物 | 三件套：试卷 docx + 解析 docx + 双向细目表 html | **两份**：试卷 docx（不含解析）+ 解析 docx（**不出细目表**） |
| 结构 | 题型分节（选择 / 填空 / 解答） | **分组**：第 N 组 = 原题 + 相似练习 1、2… |
| 流程 | S1–S8（下方主流程） | **S1g–S7g**，见 `references/similar-question.md` |

> **分流判据（一句话）**：产物里是否**必须出现用户给的那道原题**？必须 → 链路 B；不必（用户原题只是提问素材）→ 链路 A。
> 详细触发判定（4 条全中口径 + 正例/反例表）见 `references/similar-question.md §1`。

## 产物

**链路 A（三份独立交付物）**
1. **试卷 `.docx`** —— **仅试卷**，不含任何解析；自包含（题图内嵌），可直接打印分发
2. **解析 `.docx`** —— **独立文件**，含逐题「题头重列 + 【考点】【分析】【解答】」
3. **双向细目表 `.html`** —— 「内容 × 认知层次」双向表 + 「题号 × 分值 × 知识点 × 层次」逐题对照表
（过程 HTML 供预览与转档，不作为最终交付）

**链路 B（场景 g，两份独立文件）**
1. **试卷 `.docx`** —— 「原题 + 相似练习」分组卷，**不含解析**；自包含（题图内嵌），可直接打印
2. **解析 `.docx`** —— **独立文件**，逐题「题头重列 + 【考点】【分析】【解答】」
3. 过程 HTML（试卷 / 解析两份，仅供预览与转档）　❌ **不产出双向细目表**

> ⚠️ **两条链路都必须「试卷 / 解析」分两份独立文件交付**（用户硬性要求）。渲染器用 `--part paper` / `--part analysis` 分别产出两个 HTML，再各自转 docx。**不要**交付单份「合卷」（`--part both` 仅作兼容保留，默认不用）。

## 依赖与前置
- `edu` MCP 已连接（`tk*` 工具）
- **脚本清单（`scripts/` · 优先用一键脚本，参数用 `--help` 查）**

| 脚本 | 用途 |
|---|---|
| ★ `finish.sh --spec … --prefix … [--work-dir .] [--split-blocks "…"] [--allow-missing] picks_*.json` | **链路 A 收尾一条龙**（校验→幂等合并→组装→导出→自检 = **1 轮**）；退出码 `0`齐全/`1`缺题/`2`降级/`3`自检失败 |
| ★ `shrink_candidates.py table｜pool｜assemble` | **取数与决策分离核心**：原始返回→紧凑候选表 / 解析池 / 按「题位→短 ID」**自动回填** picks |
| `tkpoint_cache.py prep｜save｜status｜names｜map` | 知识点树缓存 + 知识点归一化（`prep` 一次到位，**S3.5 提速主力**） |
| `build_questions.py --spec … --picks … [--split-blocks …] [--partial]` | 合并 + MathJye 线性化 + 题号重排 + **缺口校验** → `questions.json`+`blueprint.json` |
| `render_all.sh <q.json> <bp.json> <prefix> [out_dir]` | 一键出三份 HTML + **并行**转两份 docx |
| `render_blocks.sh` + `merge_docx.sh` | 分块渲染 + **块级并行转档** + 缝合（正确处理题图 rels） |
| `validate_picks.py --spec … [--quiet] picks_*.json` | 题号连续 / 每题完整 / 识别 `PARTIAL` / 算 `missing` |
| `merge_and_gap.py --spec … [--existing …] --out merged.json picks_*.json` | 幂等合并（**绝不覆盖好题**）+ `missing` |
| `selfcheck_paper.py <试卷.docx> <解析.docx> [--blueprint …] [--questions …]` | 成卷自检 |
| 单环节按需：`render_paper.py`（`--part paper｜analysis｜both`）、`render_blueprint.py`、`render_similar.py`（链路 B）、`to_docx.sh`（自动调 `fix_hanging_indent.py`/`fix_page_break.py`） | — |
- **装载（T1 · 省 1–2 轮）**：`ToolSearch` **一次传多个 `tool_names`**，用**一条消息**装齐本卷要用的工具（`mcp__<SERVER>__tkSubject`/`mcp__<SERVER>__tkPoint`/`mcp__<SERVER>__tkSearchSubjectQuestion`/`mcp__<SERVER>__tkQuestionAnalysis`/`mcp__<SERVER>__tkQuestionSame`/`mcp__<SERVER>__tkQuestionFrom`/`mcp__<SERVER>__tkQuestionType`），**不要**分多次装载。
- **参考文档（按需读取 · 每份每任务只读一次）**
  - 🔴 **链路 A 必读**（T1 **同轮批量读**，一次读完）：`references/efficiency.md`（提速细则 + **照抄式调用样式**）、`references/fault-tolerance.md`（容错与续跑）
  - 用时才读：`references/normalization.md`（学科码 / 难度 / 认知层次 / 题型码 / 来源码 / 知识点归一化）、`references/layout-standard.md`（排版硬约束）、`references/edu-api-notes.md`（接口实测坑）、`references/session-state.md`（再编辑）、`references/similar-question.md`（**链路 B 必读**）
  - **📌 批读纪律（强制）**：同一份 reference **在同一任务内只读一次**；需要多份时**在该阶段首轮一次性批量读**；**禁止**在后续步骤重复读同一份（重复读 = 白白重付一轮上下文成本）。

## 提速口径（索引 · 细则与调用样式见 `references/efficiency.md`）

> **实测**：25 题卷**全部 API 纯耗时仅 ≈20 s**，墙钟却 **1195 s** → **≈1175 s 是「模型轮次间隙」**。
> **结论：省轮 = 省墙钟；减少 API 调用 ≠ 提速。**

| # | 口径（强制） | 细则 |
|---|---|---|
| 1 | **能一次脚本做完的，绝不拆多次调用** —— S7 用 `finish.sh`、S3.5 用 `prep`（各 =1 轮） | §2.1-1 |
| 2 | **同轮混合流水线**：每轮同发「新题位 search + 已选题 analysis」，**不要**「先全搜完再全解析」 | §2.1-2 |
| 3 | **并发默认 4，仅题量 >20 才探 6**；429 → `sleep 3` 重试 1 次并**回落 3**；保留 ~1.5 s 轻量间隔；**429 连续 2 次 → 立即中止并返回错误（fail-fast，见容错 §6）** | §2.1-3 / §2.2-7 |
| 4 | **载体选最轻**：优先主线程直发并同轮并发；子代理仅用于隔离大 payload，且 **≤2 个** | §2.1-4 |
| 5 | **上下文卫生 + 取数与决策分离**：原始返回**只落盘**，模型只看**紧凑候选表**、决策**只回「题位→短 ID」**，题干/选项/答案/考点由 `assemble` **自动回填** | §2.1-5 / §2.3 |
| 6 | **阈值前置**：`dg` 放宽 / `so` 兜底做成首轮参数；每个知识点**各发一次**搜题（**禁止合并 `point[]`**） | §2.2-2 / §2.2-4 |

- **轮次预算（25 题）= ≈11–14 轮**（早期版本为 ≈26 轮）：装载+归一化 1（T1）→ 搜题 5–6（T2–T6）→ **集中决策 1**（T7）→ 解析+补缺 5–6（T8–T12）→ 收尾 1（T13）。**每轮只容 4–5 次调用**（50 次调用的硬底 ≈10 轮）。**Turn Plan 完整表见 `efficiency.md §2.1`；照抄式调用命令见 `efficiency.md §3`。**
- **🛑 停止条件（强制）**：搜题 + 解析**合计 ≤ T13**；补缺**有界重试 ≤2 次**；到顶仍缺 → 转**降级交付**；**服务级接口错误连续 2 次 → 立即中止并返回结构化错误（fail-fast）**。**禁止**无休止「生成 → 检查 → 再生成」。
- **🔇 输出纪律（强制）**：决策步**只输出 JSON**（如 `{"1":"s03","2":"s11"}`），**不解释、不复述题干、不展开推理**；校验 / 自检失败**只回报错片段与必要上下文**，不重述全文。
- **轻量模式（≤10 题且知识点已知）**：跳过 S3.5 全量 `mcp__<SERVER>__tkPoint`；同轮并发 4 + 选中即原子落盘；收尾直接 `finish.sh` → 单卷 **≈30–60 s**。

## 容错口径（索引 · 细则见 `references/fault-tolerance.md`）

> **根因**：25 题的搜索+解析大 HTML（≈1 MB）若全塞进**单个子代理**一次性产出 → 上下文**自动压缩** → 摘要失真并丢掉部分题目 → **只落盘少量题**。
> **不是 API 失败，是「无检查点的一次性大产出」必败。**

| 层 | 红线 |
|---|---|
| **A 预防** | **分块**（≤8–9 题/块，连续题号）+ **逐题原子落盘**（拿到 1 题立即写，**绝不**跑完才写）+ 大 HTML 落盘、不进上下文 |
| **B 检测** | 进 build 前**必跑** `validate_picks.py`；识别 `PARTIAL` 残卷；每 3 题报一次进度 |
| **C 恢复** | `merge_and_gap.py` 算 `missing` → **只补 missing**；**绝不覆盖已成功的好题**；单题重试 ≤2；降级顺序 `放宽 dg → 去 so → 关键词兜底` |
| **D 兜底** | 子代理不可靠时**主线程按 missing 直接补拉**；仍缺 → **降级交付**（N/M 题成品 + 缺题清单），**绝不 0 交付**；分块 picks **永久保留**为断点 |
| **E 中止** | **接口错误硬规则（强制）**：任一**服务级**接口错误（`429` / 超时 / `5xx` / 「系统繁忙」）→ **立即退避重试第二次**；**第二次仍失败 → 立即中止任务并向用户返回结构化错误**（接口名 / 次数 / 原始消息 / 已完成题位 / 建议），**不得**自动续跑、不得改路径硬跑。参数级错误（`code:500` 考点名无效）**不触发**、走降级；零星单题失败仍走有界重试。链路 B `mcp__<SERVER>__tkQuestionSame` **唯一例外**：先执行文档化等价降级（关键词召回，须标注），降级后仍连败才停（两接口计数独立）。细则见 `references/fault-tolerance.md §6` |

- **📌 会话与恢复（强制）**：一次任务在**一个会话内**完成；中间态**一律落盘**（`raw_*.json` / `picks_*.json` / `work-dir/`），跨阶段**从文件恢复**，不依赖会话记忆。
- **禁止用「每步压缩上下文」的方式续命** —— 自动压缩会**丢已读内容与已抓数据**（这正是上述根因）。

## 并行边界（哪些能并行 · 哪些必须串行）

**✅ 可并行（各任务无共享可变状态）**
- 各题位的 `mcp__<SERVER>__tkSearchSubjectQuestion` / `mcp__<SERVER>__tkQuestionAnalysis`（同轮并发 4）
- 各分块的取数与渲染（各自写**自己的** `raw_s<n>.json` / `picks_<块>.json` / 块 docx）
- `ToolSearch` 装载 ‖ `tkpoint_cache.py prep`（T1 同轮并发）

**⛔ 必须串行（共享作用域，禁止拆成并行子任务）**
- `assemble`（吃同一份 `sidmap`/`pool`/`spec` → 单一 picks）、`merge_and_gap`（输出单一 merged）、`finish.sh`（单一 `work-dir`）：**每个任务只跑一次，串行执行**
- `tkpoint_cache.py save`（缓存文件唯一）：**禁止并发写**
- `render_blueprint.py`（依赖全卷）：**必须在 picks 全部落定之后**

> **判据（一句话）**：拆分后若多份产物**要共享同一份可写状态**（同一输出文件 / 同一累积器 / 同一映射表）→ **不可拆**；只有**读同一份只读输入、各写各自输出**的子任务才可并行。

## 工作流程

**先做一次分流**（见「两条产物链路」）：命中链路 B 的 4 条触发判定 → **跳到 `references/similar-question.md` 的 S1g–S7g**，不执行下方 S2–S8；否则走链路 A 的 S1–S8。

### S1 场景识别（链路 A）
判定场景以确定默认题量 / 难度 / 输出形态：
- **a** 正式考试测验（期中/期末/单元考）→ 满分 120(初中)/150(高中)，易∶中∶难 ≈3∶5∶2
- **b** 日常练习作业 → 题量小、紧扣当堂知识点　｜　**c** 个性化练习 → 围绕薄弱点
- **d** 专项薄弱突破 → 同知识点多题、梯度递进　｜　**e** 自主刷题 → 不限来源可杂
- **f** 考前冲刺/升学备考/假期衔接 → **不主动进入**；用户点名则按通用方法组卷
- **g 题找题·相似题巩固**（给原题文本/图片 + "巩固 / 专项练习 / 错题"）→ **走独立链路 B，整条链路切换** → `references/similar-question.md`

> ⚠️ 场景 g 与 a–f **不是并列关系**：a–f 是"组卷目的"，g 是"输入形态（给了原题）+ 目的"的组合。

### S2 参数确定（缺则推断，推断不了再追问）
需要：学段、学科、范围（知识点 / 章节 / 教材版本+年级学期）、题型、题量、来源、难度、分数。**归一化一律查 `references/normalization.md`**（学段+学科→`subjectCode`；年级+学期→教材版本可调 `mcp__<SERVER>__tkBook(subjectCode)`；认知层次词仅作推导输入，对外难度一律五档）。

### S3 生成/校对细目表
- 用户**已给**细目表 → **不得直接拿细目表里的知识点名去搜题**，必须先执行 **S3.5 归一化**。
- 用户**未给** → 按 S2 参数拟一份细目表（模块 × 知识点 × 认知层次 × 分值），**随首轮搜题一并给出**（细目表 + 首轮候选同轮呈现：用户过目的同时题已在拉）——**不要**为「等用户确认」单独占一轮。

### S3.5 知识点归一化（**强制前置，不可跳过**）
> 「先拉知识点 → 匹配 → 再搜题」三步法。**绝不**假设细目表知识点名 = 库标准考点名。

1. **一次到位**：`tkpoint_cache.py prep --subject-code <N> [--points "点1,点2,…"]` —— 一次返回「缓存状态 + 叶名 / 映射候选」（把原先 `status`+`names`+`map` 三次调用压成 1 轮）。
   - `cached=false` → 调 `mcp__<SERVER>__tkPoint(subjectCode)` 拉全量树，交脚本落盘 `tkpoint_cache.py save <raw.json> --subject-code <N>`（**可交子代理做**，避免 1.4 MB payload 污染主上下文），再 `prep` 一次。
   - ⚠️ **轻量模式（≤10 题且知识点已知）可跳过**，直接用已知考点名搜题。
2. **匹配**：每行取 `best` —— 高置信（唯一/包含）直接用；多候选/跨义 → AI 在候选内复核；宽知识点可给多个组成 `point[]`；低/无匹配 → 标「待兜底」。
3. **降级兜底**（**仅**当低/无匹配，或直搜报 `code:500 查询失败！` / `String index out of range: -1`）：改走 `mcp__<SERVER>__tkSearchQuestion(keyword=知识点关键词, subjectCode, type=ct)`，挑主题最贴合者。**兜底是例外，不是默认路径。**

> **产出**：一张「细目表知识点 → 库标准考点名（+置信度/候选/兜底标记）」映射表，随细目表留档；**选题记录同时保留「细目表原名」与「库标准名」两列**。

### S4 智能选题（**取数与决策分离 · 分块并行 · 逐题原子落盘**）
- **默认映射（详见 `normalization.md §3/§6`）**：分值→题型（2分选择 / 4分多选或填空 / 6·8·12分解答）；认知层次→难度（了解 dg11 / 理解 dg12 / 掌握 dg13 / 运用 dg15）。
- **① 取数**：每题位发一次 `mcp__<SERVER>__tkSearchSubjectQuestion(subjectCode, point=[单个库标准考点名], ct, dg, so, ps=10)` → **立即落盘** `raw_s<N>.json`（不解析、不复述）。并发与混合口径见「提速口径 #2/#3」，**禁止合并 `point[]`**（#6）。
- **② 瘦身**：`shrink_candidates.py table` → 上下文里**只出现紧凑候选表**（一行一题），原始 HTML 不留对话。
- **③ 集中决策（T7，1 轮）**：读紧凑表 → **只输出「题位→短 ID」** `sel.json`；搜题阶段**先不选题**。
- **④ 装配**：`shrink_candidates.py assemble` → 题干 / 选项 / 答案 / 考点 / 解析**全部自动回填**。
- **⑤ 分块 + 原子落盘 + 进度**：题位切 **3 块**（①1–9 ②10–18 ③19–25，每块 ≤8–9 题）；**逐题原子落盘**；**每 3 题报进度**。
- **⑥ 降级**：候选不足 → `dg=0`（保留 so）补一轮 → 仍不足 → 去 so → 关键词兜底。
- **题找题**：命中场景 g → **切链路 B**（相似题优先 `mcp__<SERVER>__tkQuestionSame`）；仅当原题同时指向知识点 / 难度体系（仍走链路 A）时，按「解析原题 → 抽知识点 / 题型 / 难度 → 标准知识点搜题」处理。

### S5 编排（**不单独占轮**）
按细目表组装：**全局题号重排**（选择 → 填空 → 解答）、**分值累计校验 = 满分**、难度结构核对。⚠️ **本步由脚本完成、不单独占一轮**——全在 `build_questions.py` 内做完，而它已并入 S7 的 `finish.sh`。同时保留**可寻址的会话状态**（见 `references/session-state.md`），以支持 S8。

### S6 取解析（**与 S4 同轮混合 + 原子落盘**）
- 对**全部题（含选择题）**取解析：`mcp__<SERVER>__tkQuestionAnalysis(SID, subjectCode)` → `Analyse / Method / Discuss / Points / Answers`。并发与同轮混合口径**同 S4**（见「提速口径 #2/#3」）。
- **原子落盘**：题位选定 SID **即刻发起解析**，解析一到**立刻追加写入本块 picks**（与后续搜题并行）；**绝不**「全部跑完才写」。原始返回落盘 `raw_a<N>.json`，收尾前 `pool` 归并。

### S7 校验 · 续跑 · 排版导出（**一条命令收尾**）

> **★ 首选（口径 #1）—— 一步到位，只花 1 轮模型往返**：
> ```bash
> # 走瘦身路径时：先装配 picks，再与 finish 串成一条命令
> python3 scripts/shrink_candidates.py assemble --sidmap cand_sidmap.json --pool cand_pool.json \
>      --analysis-pool analysis_pool.json --spec spec.json --map sel.json --out picks_1.json
> bash scripts/finish.sh --spec spec.json --prefix <out_prefix> --work-dir . \
>      [--split-blocks "1-9,10-18,19-25"] [--allow-missing] picks_1.json picks_2.json picks_3.json
> ```
> 一次跑完「**校验 → 幂等合并/补缺 → 组装 → 排版导出 → 自检**」（原需 5 次调用 = 5 轮）。
> **退出码**：`0`=三件套齐全且自检通过 ｜ `1`=缺题待补（按 `missing` 只补缺口后续跑）｜ `2`=已降级交付（产物可用 + 缺题清单）｜ `3`=自检失败（产物已生成，需人工核对）。

- **续跑（失败只补缺口）**：退出码 `1`/`2` 时**只补 `missing` 题号**，把新补的 picks 丢回 `finish.sh` 重跑（`--existing` 保证**已成功的好题永不重拉/覆盖**；必要时主线程直接接手补拉）。细则见「容错口径 C/D」。
- **交付**：用 `present_files` 交付**三份**（试卷 docx / 解析 docx / 细目表 html）。需要**单环节**时才用 `render_paper.py` / `render_blueprint.py` / `to_docx.sh`（命令见 `efficiency.md §3.4`）。❌ **不要**用 `--part both` 出单份合卷作为交付物。

> **链路 B（场景 g）的 S7g —— 产出两份独立文件**：
> `python3 scripts/render_similar.py <groups.json> --part paper -o <paper.html>` → `bash scripts/to_docx.sh <paper.html> <试卷.docx>`；
> `python3 scripts/render_similar.py <groups.json> --part analysis -o <analysis.html>` → `bash scripts/to_docx.sh <analysis.html> <解析.docx>`；
> 用 `present_files` 交付**两份**（试卷 docx + 解析 docx，**无细目表**）。

### S8 结果引导（再编辑）
支持：改单题（题型/知识点/难度）、增/删/替换题、相似题替换、限定来源后重换。均基于 S5 会话状态按 `no`（题号）定位。

## 硬约束（只留红线 · 细则见 references）

- **知识点归一化（强制）**：细目表知识点**不得直连**搜题 → 必须走 **S3.5**（先取库标准考点名，再搜题）。降级仅限低/无匹配或直搜报 `code:500 查询失败！` / `String index out of range: -1`。细则见 `references/normalization.md §7`。
- **产物形态（强制）**：链路 A 交付**三份独立文件**（试卷 docx 无解析 / 解析 docx / 细目表 html）；链路 B 交付**两份独立文件**（试卷 docx 无解析 / 解析 docx）。**两条链路均禁止**用单份「合卷」代替。
- **合规红线**：试题**实时拉取、仅会话内使用、不落库、不缓存题干/选项/答案/解析/图片**。**可缓存**的仅限**元数据**（知识点树 / 码表 / 映射表）。导出物内嵌图片属「用户交付物」，与「不缓存试题内容」不冲突（导出时一次性抓取）。细则见 `efficiency.md §4`。
- **元数据不外显（强制）**：接口返回的**元数据字段值**（`SID` / `Label` / `SourceReports` / `Degree` 原值 / `Subject` / `Cate` / **库内部考点名**）**一律不进入对话输出与三份交付物**；难度对外只给**五档**、题源标注不展示、平台名与版权尾缀不落款、细目表不渲染「库标准考点名」、解析【考点】**只取教师侧命名**（不回退接口考点名）。细则见 `efficiency.md §4`。
- **取数与决策分离（强制）**：**原始返回只落盘，不进（主）模型上下文**；模型只看紧凑候选表，决策**只回「题位→短 ID」**；**禁止**把原始大 HTML 黏进对话、**禁止**手抄完整内部 ID（长串、贵且易错）。细则见 `efficiency.md §2.3`。
- **轮次（强制）**：**减少模型轮次优先于减少 API 调用**；能在一个脚本进程里做完的，绝不拆成多次调用。细则见 `efficiency.md §2.1`。
- **容错与续跑（强制）**：**禁止**单个代理整包 25 题且"跑完才写文件"；必须分块 + 逐题原子落盘；进 build 前必跑 `validate_picks.py`；缺题只补 `missing`；仍缺则降级交付。细则见 `references/fault-tolerance.md`。
- **接口错误处置（强制 · fail-fast）**：**服务级**接口错误（`429` / 超时 / 连接失败 / `5xx` / 「系统繁忙」）**连续 2 次失败 → 立即中止任务并返回结构化错误**（接口名 / 连续次数 / 原始错误 / 已完成题位 / 建议），**不得**改路径或降级硬跑；**参数级**错误（考点名无效 `code:500 查询失败！` / `String index out of range: -1`）**不计入**连续失败、按既有规则降级；**零星**单题失败仍走有界重试 ≤2 后记 `missing` 续跑。细则见 `references/fault-tolerance.md §6`。
- **题位判重（强制）**：`assemble` 阶段**趁 SID 仍在池中先按 SID 判重**（重复 → 返回码 `2`、要求重新决策；`--allow-dup` 可强制通过），判重通过后写入 picks **仍不落 SID**（即「先保留 SID 判重、判重后再剥离」）；`validate_picks.py` 再用**题干哈希**兜底防「不同 SID 同题」。**禁止**把 `SID` 写进交付物（元数据红线）。
- **并行边界（强制）**：共享可写状态的步骤（`assemble` / `merge_and_gap` / `finish.sh` / `tkpoint_cache save`）**禁止并行**，各只跑一次。见「并行边界」节。
- **题图**：一律走 `render_paper.IMG`（题库图片域名，可用环境变量 `ZJ_IMG_HOST` 覆盖）+ `referrerpolicy="no-referrer" loading="lazy"`；不落地缓存；**去除题库图片的 `float:right`**，题图统一独立成段居中。
- **排版（强制）**：严格遵循 `references/layout-standard.md`（v1.6）——**选项绝不折行**、**页边距显式传参**、**行距逐元素显式声明**、**字号钉死在元素上**、**悬挂缩进靠 `fix_hanging_indent.py` 后处理**。
- **渲染四细项（强制，均已在 `render_paper.py` 实现）**：① **数学标记线性化**（`normalize_math()`：MathJye 分数表 → `(分子)/(分母)`、上下标 → `<sub>/<sup>`，`class="edittable"` 真数据表保留）；② **解析「解：」去重**（`Method` 自带前缀不得再加）；③ **小问分行**（`split_subq()` 只在段首 / 句末标点含 `）` / 标签 `>` 后判边界，**切勿**无条件替换 `（N）`——"五（2）班"会被误拆）；④ **解答题图位置**（题干叙述 → 图居中 → 小问，由 `extract_stem_figs()` + `split_at_first_subq()` 重排；其余题型不改）。见 `layout-standard.md §6-4/5/8/12`。
- **异常降级**：选题 0 命中（**参数级 / 内容级**）→ 放宽 dg → 去 so → 换同义知识点 → 标「待确认」，**不阻断整卷**；**服务级**接口错误（`429` / 「系统繁忙」/ 超时 / `5xx`）**连续 2 次失败 → 立即中止并返回错误**（见 `fault-tolerance.md §6`）；**唯一例外**＝链路 B `mcp__<SERVER>__tkQuestionSame`：**先执行文档化等价降级（关键词召回，须显式标注已切换）**，**降级后仍连续 2 次失败才中止**（两接口失败计数各自独立），**不得静默改道**。
- **场景 g 产物约束（强制）**：链路 B 必须交付**两份独立文件**；**不产出双向细目表**；组内定位用「原题 / 相似练习 N」角色标签，不做全程题号重排。见 `references/similar-question.md §3`。

## 跨场景公共约定

权限固定提示 / 干净输出红线 / 触发词格式 / 版本与完工标准 / MCP 前缀自检：统一见 [_shared.md](references/_shared.md)。本 skill 的前置权限校验口径与「严禁编造知网数据」红线均与之对齐。
