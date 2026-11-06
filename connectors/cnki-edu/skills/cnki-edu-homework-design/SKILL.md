---
name: cnki-edu-homework-design
display_name: 作业设计
display_name_en: Homework Design
description: 中小学各学科分层作业设计：课标对齐、CNKI 学术溯源、政策红线校验与排版交付一体化。
description_zh: 中小学各学科分层作业设计：课标对齐、学术溯源、政策红线校验与排版交付一体化。
description_en: "Tiered K-12 homework design across subjects: curriculum alignment, academic sourcing, policy compliance checks and ready-to-deliver formatting."
category: education
version: 1.0.1
author: 知网 edu
---

# 中小学作业设计 AI

## 这套东西要解决什么

教师备课最耗时、AI 最能帮上忙的环节是**内容编制**——找题、创题、分层。但普通 AI 出题有三个致命缺陷：答案可能出错、不知道本地学情、题目没有出处。

所以本 skill 的方法论核心只有一句话：**给每道题加上四道可验证的锚**。

| 锚点 | 没有它 | 有它 |
|---|---|---|
| 出处 | AI 随手编情境，数据不可查 | 挂 CNKI 真实文献，可点溯源 |
| 对齐 | 泛泛"符合教学要求" | 绑定课标具体条目 + 核心素养 |
| 分层依据 | 难度标签凭感觉贴 | 布鲁姆认知层级 + 知识点/步骤数硬规则 |
| 学段合规 | 小学低段也出书面作业（政策红线） | `allow_written=false` 代码级拦截 |

差异化不来自"模型更聪明"，来自**约束更硬**。所以本 skill 把大部分精力放在生成之后的**硬校验**上——写了规则从没见它拦过东西，等于没写。

---

## 先确认范围：只做内容编制

作业链路有六段：目标设定 → 内容编制 → 布置实施 → 反馈批改 → 学情分析 → 个性化迭代。
用户说"作业设计"通常只指**内容编制**；若含批改/学情，先确认边界——两者的学科难点和合规要求完全不同，混做会两边都不深。

---

## 数据入口：只有一处，就是 CNKI 基础教育 MCP

**本 skill 的全部真实数据（题库 + 学术文献 + 知识点 + 教材目录）都只从 WorkBuddy 连接器里的「CNKI 基础教育」MCP 取**，工具名一律 `mcp__<SERVER>__*`。

| 数据 | 走哪个接口 | 禁止的做法 |
|---|---|---|
| 题库（真题候选题） | `mcp__<SERVER>__tkSearchQuestion`（关键词）/ `mcp__<SERVER>__tkSearchSubjectQuestion`（考点，优先） | 用本地题库文件、或拿公开网络检索结果拼题库 |
| 试题官方解析 | `mcp__<SERVER>__tkQuestionAnalysis`（按 SID 逐个取） | 让模型凭空写解析当作官方解析 |
| 学术文献（溯源） | `mcp__<SERVER>__searchVectorBJ` | 凭记忆编一条"看起来很像"的文献；用公开检索结果冒充 CNKI 文献 |
| 学科码 / 知识点 / 教材 | `mcp__<SERVER>__tkSubject` / `mcp__<SERVER>__tkPoint` / `mcp__<SERVER>__tkBook` | 硬编码猜学科码 |

> **工具名前缀取自连接器在 WorkBuddy 里的「显示名」，不是 `mcp.json` 里的 key，而且会随用户重命名而变。**
> 当前是 `mcp__<SERVER>__`，但历史上已经变过两次（`edu` → `知网基教` → `edu`），本机 `mcp.json` 里的 key 始终叫 `edu`。
> **写错前缀的表现是「查不到这个工具」**，极易被误判成「接口坏了 / 报 500」，实际是从来没调对过名字——
> 历史上为此白试过 6 次。
> **不确定当前前缀是什么时跑一次 `reconcile`**，它会自动反推真实前缀并直接告诉你该改成什么（见下节）。

接口名只在一个地方定义：`scripts/mcp_adapters.py` 顶部的 `MCP_PROVIDER` + `MCP_ENDPOINTS`。
表里存**短名**（`mcp__<SERVER>__tkSearchQuestion`），全名由 `full_tool()` 拼出来，**改前缀只需要改那一行**，不要全文替换工具名。

### 🔐 前置权限校验（最高优先级，必须最先执行）（开工前置三步，顺序不能乱）

> 权限校验的「三态诊断 / 通用版兜底 / 强制转化卡 / 连接器加载指引」统一见本技能 `references/_shared.md`「一、权限固定提示」，本章节仅保留本技能专属说明，不重复展开。

> **本技能属①档强依赖**：核心产出需知网数据支撑，无权益即停止、不编造（通用版兜底与转化卡原文见 `references/_shared.md`「一、权限固定提示」）。

| 步 | 动作 | 失败意味着什么 |
|---|---|---|
| 1 | **`ToolSearch(tool_names=["userState"])` 反查真实工具名，再调 `mcp__<SERVER>__userState`（无参数，成本极低）——本技能第一个工具调用** | 返回 **false**（态 B）→ 账号没基教权益：按`references/_shared.md`「一、权限固定提示」「通用版兜底 + 强制转化卡」处理——① 不调用任何 `tk*`/`mcp__<SERVER>__searchVectorBJ` 工具；② 通用版完成不依赖知网数据的部分，并原样输出「解锁知网数据增强层」；**不要把"查不到题"误判成"题库无覆盖"**。**态 A｜查不到该工具 / 调用报错**（连接器未加载/掉线）→ 按 `references/_shared.md`「一、权限固定提示」给「连接器加载指引」、**不**输出转化卡，也不要调用任何 edu 工具。 |
| 2 | 仅当 `mcp__<SERVER>__userState` 返回 **true** 时，再 `ToolSearch(tool_names=["tkSearchQuestion"])` 精确查名，确认题库接口可装载 | 查不到＝**连接器没连 / 工具未装载**（去连接器管理页启用），不是接口坏了 |
| 3 | 仅当 `mcp__<SERVER>__userState` 返回 **true** 且 `mcp__<SERVER>__tkSearchQuestion` 可装载时，按技能主流程第 1–3 步正常往下跑 | — |

> 🛑 **无权益时的处理（`mcp__<SERVER>__userState` 返回 false / 工具不可达 一律走「通用版兜底 + 强制转化卡」）**：
> 转化卡原文与"严禁编造知网数据"条款统一见 [_shared.md](references/_shared.md)「权限固定提示」，本 skill 不再重复誊写——无权益时走通用版并原样输出转化卡。

现象区分与降级策略见 **`references/workbuddy-mcp.md`**。

### 登记表是静态的：升级连接器后必须做一次对账

`MCP_ENDPOINTS` 必须手写（每个接口的参数、返回、坑只能人来写清），所以它**天然滞后于连接器**——
连接器新增接口，脚本自己感知不到。补救办法是定期对一次账：

```bash
# Agent 侧用 ToolSearch 列出连接器当前暴露的全部工具 -> 落盘 tools.json
python scripts/mcp_adapters.py reconcile --tools tools.json
```

对账报告会分四类报出偏差：`OK` 登记且可用 / **`BLOCKER` 登记了但连不上**（优先怀疑前缀写错）/
**`NEW` 连得上但没登记**（就是"新接口会不会漏"的答案，需人工评估）/ `INFO` 曾判为不存在又出现了。

> 这套机制是被坑出来的：查第一批 12 个接口时，登记表里只有 8 个，
> 漏了 `mcp__<SERVER>__tkQuestionAnalysis`（试题官方解析）、`mcp__<SERVER>__tkQuestionType`（题型字典）、
> `mcp__<SERVER>__tkQuestionFrom`（试题来源字典）、`mcp__<SERVER>__userState`（权益校验）四个——其中前三个都能直接提升出题质量。

---

## 标准流程（八步）

在 WorkBuddy 里，八步默认由你在对话中直接完成：第 1–3 步靠脚本，第 4–5 步你按 prompt 模板自己生成并自校验，第 7 步渲染后交付。下面的命令照抄即可。

### 运行环境

| 项 | 值 |
|---|---|
| Python | 用当前环境可用的 `python` 或 `python3`；只有当裸命令不可用时，才退回绝对路径 |
| 脚本位置 | 本 skill 目录下的 `scripts/`，命令一律以 skill 目录为工作目录执行 |
| 平台 | 纯标准库实现（argparse/json/re/dataclasses），无第三方依赖，Windows / macOS / Linux 通用 |
| 交付 | 产出可看结果必须调 `present_files`，否则用户看不到 |

```bash
python scripts/homework_kit.py packs --subject 数学 --stage "初中(7-9)"
```

> 若 `python` 命令在本机不可用（部分 Windows 环境），用 `py -3` 或该环境的 Python 绝对路径替换开头的 `python`，其余参数不变。

### 第 1 步 · 收齐约束，别急着生成

缺一项就问，猜出来的参数会直接变成错误的作业单。最小必填集：

```
学科 | 学段 | 年级 | 单元/主题 | 课标条目(可空) | 班级水平
分层比例(ratio) | 题型偏好 | 题量 | 时长上限 | 是否情境化
供给模式(supply) | 作业用途(job_type) | gen_cap(可选，覆盖预设原创额度) | 每题指认(overrides，可选)
共享材料(shared_material，可选) | 一段课文/史料/实验情境/图表；填了即进入「同材异层」模式，全部题目基于它分层，材料在作业单顶部只渲染一次
同主题作文分层(自动生效) | 当题型偏好含「写作」且填了单元/主题时自动进入：三层均围绕该主题命题、题型统一为写作，分别给出由浅入深的不同立意，适配各层学情（见下文「同主题作文分层」小节）
```

**必问的一项：`job_type`（这份作业拿来干什么）**。它决定真题/改编/原创的配比——见第 3 步，
它是目前对产出形态影响最大的单个参数。教师没说的话，用默认值 `课后巩固` 并在交付说明里标注
「以下为默认假设，可调整」。`gen_cap` 可不填（默认按用途预设），填了就锁死原创额度。

### 第 2 步 · 加载约束包

```bash
python scripts/homework_kit.py packs --subject 数学 --stage "初中(7-9)"
```

6 个学科包 × 4 个学段包的完整定义见 **`references/constraint-packs.md`**。

**学科包和学段包必须分开**：学科决定"出什么题型"，学段横切决定"能出多难、出多少、能不能出书面"。合在一起写会变成 24 份重复维护。
**冲突消解优先级**：政策合规（`allow_written`/`max_minutes`）› 学段 › 学科 › 通用。
例：数学包允许"应用题"，但小学低段 `allow_written=false` → 不出书面应用题，改写为"用小棒摆一摆，说给同桌听"。

### 第 3 步 · 供给路由（关键，别跳过）

```bash
python scripts/homework_kit.py route --params params.json --out-plan plan_auto.json
```

见 **`references/supply-modes.md`**。核心结论：**供给跟着「作业用途」走，默认混合（mix），不是三选一**。

### 先问：这份作业要不要拿去打分

这是开工前唯一需要确认的决定性变量，比"要出几道题"重要得多：

- **作业的目的是「学会」**，所以学生见到考过的真题不是缺点——那意味着真实难度、真实设问、答案已被考试校验。**以练为目的的作业里，真题可以直接用。**
- **只有承担评价功能**（周测、月测、单元测验，要出分、要横向比较）时才必须压制原题，否则学生背答案、成绩失真。

所以三档配额按用途预设如下（由 `_split_quota` 按最大余数法分配，题量小时会有 ±1 题浮动）：

| job_type（用途） | 原题 | 改编 | 原创 | 依据 |
|---|---|---|---|---|
| 课前预学 | 70% | 20% | 10% | 摸底不需打分，真题是最可信的基线 |
| **课后巩固（默认）** | 40% | 50% | 10% | 刚讲过同构例题，需变式防照抄，但留真题对标真实难度 |
| 单元作业 | 35% | 50% | 15% | 真题交代真实考查方式，改编担梯度 |
| 阶段测验（周测/月测） | 10% | 60% | 30% | 唯一必须压制原题的场景 |
| 备考复习 | 65% | 30% | 5% | 熟悉真题本身就是备考内容 |
| 错题重做 | 5% | 75% | 20% | 同考点二刷，留原题等于背答案 |

跑 `python scripts/homework_kit.py presets` 可随时打出这张表。
`supply` 另有三个单档值 `retrieve` / `adapt` / `generate`，教师明确说"全部用真题"这类要求时用。

#### 逐题指认 overrides：改一题不用全盘切换

配额是统计意义上的默认值，而教师见过这些题、比配额更懂本班，所以支持逐题指认：

```json
"overrides": {"2": "retrieve", "5": "generate"}
```

指认优先于配额，计划里会多出「教师逐题指认」一行；若这下动到了配额，还会多一行「配额调整」把改动讲清楚。
题号越界、档名非法的指认会被忽略并写进 `overrides_invalid`，**不静默吞掉**。

这是"让老师选"最直接的落地：教师不必为了改其中一道题，去整体切换作业用途。

#### 一题多变式包：给一道真题派生 N 个变式

一道真题最值钱的不是题本身，是它背后的**考点模板**。做完作业单后常用这一步补分层 B 卷和错题隔周二刷：

```bash
python scripts/homework_kit.py variants --bank bank.json --bank-id Q07 \
  --subject 物理 --stage "初中(7-9)" --n 3 --out-plan variant_plan.json
python scripts/homework_kit.py variants --items items.json --id 4 --kinds retune,reverse
```

四种派生方式：`retune` 同构换数（二刷防背答案）· `rescene` 换情境（解决情境陈旧）·
`reverse` 逆向设问（升一层到拓展）· `recondition` 增减条件（练审题建模）。

产出的计划结构与主计划同形（全部 `adapt`、`gen_max=0`），可直接喂给 `validate --plan` 走逐题比对。
注意变式全是改编题，所以每一道都要求答案一致性验算——改了数据沿用母题答案是这套东西最贵的错误。

没有题库就跳过本步、全部按 `generate` 处理（脚本会自动放开原创额度并标注降级原因），但必须在交付说明里提示"建议接入题库以降低成本与风险"。

#### A. 用 CNKI 基础教育 MCP 取真实候选题（题库）

题库必须走 `mcp__<SERVER>__tk*` 系列，不允许拿本地文件或公开检索结果拼题库。**两种检索方式，考点优先**：

```bash
# 方式一（推荐）：按考点取题 —— 比关键词准得多
#   关键词检索会把「综合题里只嵌一问目标考点」的题混进来，
#   八年级浮力误选热机效率题的病根就在这。
python scripts/mcp_adapters.py code --subject 物理 --stage "初中(7-9)"   # -> {"subjectCode": 21}
#   mcp__<SERVER>__tkPoint(subjectCode=21) 取考点名（返回极大，用 point 子命令抽命中项，别全量读）
#   mcp__<SERVER>__tkSearchSubjectQuestion(subjectCode=21, point=["浮力"], yr="2025", ps=10)
#      可加：dg 难度档(11易/12较易/13中档/14较难/15难) · yr 年份 · so 来源 · ct 题型
#      → 服务端直接筛完再返回，比事后按 Degree 分档准

# 方式二：关键词检索（考点拿不到时的兜底）
#   mcp__<SERVER>__tkSearchQuestion(keyword="浮力", subjectCode=21, ps=10)
#   注意：keyword 不能带空格（多概念拆成多次检索再合并），ps 上限 10

# 两种返回结构一致，同一个命令标准化
python scripts/mcp_adapters.py bank --raw raw_bank.json --out bank.json
```

**按考点检索多返回三个字段**（关键词检索没有），对选题很有用：

| 字段 | 值 | 用途 |
|---|---|---|
| `SourceReports` | 完整试卷名，如「2025-2026学年湖南省衡阳市衡阳县八年级（下）期末物理试卷」 | 比 `Label` 简称「（2026春•衡阳县期末）」信息量大得多，真题新鲜度以此为准，不用再猜 |
| `RealCount` / `PaperCount` | 真实考试引用次数 / 收录试卷数 | 真题含金量的量化参考，选「考过的题」时优先取 RealCount 高的 |

`Degree` → 分层档：<0.6 基础 / 0.6–0.85 巩固 / >0.85 拓展；`SID` → `bank_id`；`Label` → 试卷出处（印在作业单上的那行）。
**候选数必须 ≥ 题量 × 1.5**。候选不足时路由会标 `reused:true` 并告警，校验器也会拦「孪生题」（两题同 `based_on`）——但那只是兜底，正解是先把候选补足（多检索几个关键词、拆成多个考点分别检索，或放宽 `Degree` 分档）。

#### A2. 取官方解析（retrieve 真题必须取，adapt 强烈建议取）

搜题接口**只带回答案、不带解析**（`Analyse` / `Method` 字段是空的）。过去作业单的 `analysis` 全靠模型写，
第 14 条验算就成了「模型改编 → 模型复算 → 模型判一致」的自证循环，**改错了也查不出来**。官方解析是出题方给的解，
拿它当外部基准才叫校验。**retrieve 真题更要取**——它的答案已被考试校验，但解析同样不在搜题返回里，不回查就只能留「回查原卷」占位。

```bash
# 对选定的题逐个取（需 SID + 学科码；无批量接口，按需取）
#   mcp__<SERVER>__tkQuestionAnalysis(SID="...", subjectCode=21)   ->  raw_analysis.json
python scripts/mcp_adapters.py analysis --raw raw_analysis.json --out analysis.json

# 合并进题库：官方解析与考点按 SID 挂到对应题上
python scripts/mcp_adapters.py bank --raw raw_bank.json --analysis raw_analysis.json --out bank.json

# 回填进作业单（LLM 主流程：先 generate 出 items.json，再回填；只动 retrieve 档的
#   答案/解析/考点，题面一字不改，validate 官方答案交叉校验必过）
python scripts/fill_analysis.py --items items.json --analysis raw_analysis.json --out items.json
# 也可用已标准化的 analysis.json；匹配不到 SID 的 retrieve 题自动留「回查原卷」占位，绝不编造
```

`fill_analysis.py` 是通用回填工具，LLM 主流程（八步）与 `bank_to_items.py` 一键落地都能用：后者传 `--analysis`
即在内部分发同一套清洗+回填逻辑。解析里的分数表（MathJye）、上下标、HTML 标签由 `mcp_adapters.strip_html`
统一规整为可读文本（`F_1`、`1/3`、`2/3×1/4=1/6` 等）。

#### B. 直接调题库出真表格（数学/理科数据表一键落地）

题库 `Content` 是带 `<table class="edittable">` 的 **HTML**，表格数据完全结构化（不是图片、不是乱码）。
用 `bank_to_items.py` 把一道/多道真题直接变成 `items.json` + `plan.json`，**数据表自动落真表格**，
不再手动抄数、不再编造数字，子问题 `(1)(2)(3)` 与填空 `（ ）` 也一并解析：

```bash
# 1) 先调 MCP 拿真题（subjectCode=10 数学；关键词勿带空格）
#    mcp__<SERVER>__tkSearchQuestion(keyword="折线统计图", subjectCode=10, ps=10)
#    把返回的 data 数组存成 bank_raw.json
# 2) 适配成作业设计单三件套（origin=retrieve、source_id=题库 SID、source_label=题库 Label）
python scripts/bank_to_items.py \
  --bank bank_raw.json --sids <SID1>,<SID2> \
  --subject 数学 --stage "小学中高段(3-6)" \
  --std "《义务教育数学课程标准（2022年版）》第三学段『数据的收集、整理与表达』…" \
  --literacy "数据意识、应用意识" \
  --out OUTDIR
# 3) 校验（事实级：source_id 命中计划 bank_id）+ 出 Word
python homework_kit.py validate --items OUTDIR/items.json --subject 数学 --stage "小学中高段(3-6)" --plan OUTDIR/plan.json
python homework_kit.py render   --items OUTDIR/items.json --subject 数学 --stage "小学中高段(3-6)" --plan OUTDIR/plan.json \
  --format docx --audience both --out OUTDIR/作业设计单.docx
```

适配要点（已在脚本内处理）：
- `<table class="edittable">` → 结构化 `table` 字段（首行表头、其余数据行），`render` 用 `doc.add_table()` 出**真表格**；
- `<del>…</del>` 保留内文字（如「废旧电池」是题面正常词，不是答案）；
- `<!--BA--><div class="quizPutTag">…<!--EA-->` 填空标记 → 中文 `（ ）`；`五（2）班` 里的 `（2）` **不会**被误当小题号；
- `<img>` 原题配图（如折线统计图）：`bank_to_items.py` 会**自动下载**到 `OUTDIR/figures/fig1.png` 并写入 `item.figures`，`render`/`build_student_md` 输出 `![caption](abspath)` 标记，`md_to_docx` 用 `add_picture` 真正嵌入 Word——**原题附图不再丢**（早期版本直接删 `<img>` 导致折线图缺失，已修）；
- 原图嵌入范围由 `render` 的 `--figures` 控制：`both`(默认，学生+教师都嵌) / `teacher`(仅教师备课参考，避免在学生卷里提前给出(1)的答案图) / `student` / `none`；
- **严禁把带第三方平台水印的原图直接嵌入成品**：题库外链图（如 `img.jyeoo.net`）的像素/元数据里常带「菁优网」署名。`bank_to_items.py` 下载后做字节级检测（`菁优网`/`jyeoo`），命中即告警——必须**按题目真实数据用 matplotlib 本地重绘**（中文字体用 `C:/Windows/Fonts/msyh.ttc`）覆盖 `figures/figN.png` 后再生成；同理正文/图注/来源声明里不得出现「来源平台：菁优网」「试题来源：CNKI…（原题来源平台：…）」等第三方与内部来源表述，只保留对外有意义的「原题标注：2025春•临县期末」这类试卷出处；
- `retrieve` 真题答案在源题库，**不靠 AI 编造**：① 优先用 `mcp__<SERVER>__tkQuestionAnalysis(SID, subjectCode)` 取**官方答案与解析**（`Method`=详解、`Analyse`=简析、`Discuss`=点评、`Points`/`Topics`=考点/专题），清洗 HTML 后写入 item 的 `answer`/`analysis`/`points` 字段，教师区「参考答案与解析」下完整展示（学生区绝不含答案）；② `mcp__<SERVER>__tkQuestionAnalysis` 接口异常/无解析时，才退化为「回查原卷/题库」占位提示。**不印 SID**——SID 是内部流水号，对外无意义且属内部接口字段，严禁印到成品上；`validate` 对 retrieve 已豁免 `answer/analysis` 必填。


返回里 `Method` 是详解正文、`Analyse` 是简析、`Discuss` 是点评，`Points` / `Topics` 是考点与专题——
**这两个字段只有解析接口回填**，搜题返回里是空的。合并后校验器自动做交叉校验：

| 情况 | 处理 |
|---|---|
| retrieve 题答案与官方答案不符 | **阻塞**——retrieve 的定义就是原样使用，答案也不得改 |
| adapt 题改了答案，但 `recompute` 里没提原答案 | 提醒，要求在 recompute 里说明为什么变了 |
| 答案中的数值在官方解析里一个都找不到 | 提醒，可能是算错或单位换算有误 |

回填动作由 `scripts/fill_analysis.py` 完成：把 `mcp__<SERVER>__tkQuestionAnalysis` 结果按 SID 写进 retrieve 档的
`answer`/`analysis`/`points`，并写入 `official_answer` 供上面这条交叉校验（与 `answer` 同值必过）；
匹配不到 SID 的 retrieve 题留「回查原卷」占位，绝不编造解析。

**不是每道题都有解析**，返回为空的题不要编解析——解析留空，或由模型基于题面自写并标注来源。
另外 `dg` 难度档方向存疑（接口标注「11=易(0.8~1.0)」与 Degree 越大越难方向相反，推测指的是正确率），
**只用它做筛选，定档一律用返回的 `Degree`**。

#### B. 用 CNKI 基础教育 MCP 取真实文献（学术溯源）

文献检索走 `mcp__<SERVER>__searchVectorBJ`（**它是 edu MCP 里唯一的文献检索入口**）。
`mcp__<SERVER>__searchLiteratureKnowledge` 在当前 edu MCP 中**不存在**，别照抄旧文档——已登记在 `mcp_adapters.py` 的 `DEPRECATED_TOOLS` 里。

```bash
# 1) 调 mcp__<SERVER>__searchVectorBJ(text="阿基米德原理 探究教学", query_type=3, type="0")
#    -> 原始 JSON 落盘 raw_lit.json（参数名是 text，不是 query；query_type=3 按主题检索）
# 2) 标准化（解析文件名中的年份/期号，标出接口没给的字段）
python scripts/mcp_adapters.py lit --raw raw_lit.json --out lit.json
# 3) 按篇名补齐作者/刊名/卷/页后回填
python scripts/mcp_adapters.py lit --raw raw_lit.json --out lit.json --fill fill.json
```

**这个接口只给一半字段**——返回 `篇名 / 正文(摘要) / 小标题 / 文件名 / product / 相关度`，**不返回作者、刊名、卷、页码**。处理办法：

- `文件名` 形如 `<刊码+年份+期号+序号>` → 可解出年份与期号（**仅对 `product=CJFD` 成立**；`CAPJ` 优先出版不解析期号）。
- 接口没给的字段一律留 `None` → 渲染成灰色【待补充】，**绝不猜**。缺=待补，填错=编造。
- 要补齐就按篇名去核实真实作者/刊名，回填时与文件名解析出的年份/期号**交叉校验**；冲突时保留 CNKI 文件名的值并把分歧写进 `notes`。
- `lit_report` 会给出体检报告：几条完整、几条待补、几条是优先出版。

详见 **`references/workbuddy-mcp.md`** 第三节与 **`references/source-citation.md`**。

### 同材异层（共享材料）模式

语文/英语/政史地/理化生等学科大量作业是「一份材料 + 多层任务」（如一篇课文出基础字词→巩固赏析→拓展写话）。
这类需求在 `params.json` 里填 `shared_material`（一段课文/史料/实验情境/图表）即可，填了就进入同材异层模式：

- `build_prompt` 把材料原样注入 prompt，并约束模型：各题 `stem` 只写设问、用「根据材料」指代，`material` 字段留空；`meta` 回写 `shared_material` 一份。
- `render` 在作业单**顶部只渲染一次**材料，下面按层列题，不再逐题重复材料块（每层一道或多道都支持，由 `total_count` + `ratio` 控制）。
- 不填 `shared_material` 则维持原行为（每题各自带 `material`，适合字词/计算等离散题）。

判定信号很直接：老师是否围绕「一份材料」出题——给了材料走此模式，要一串离散题则走默认模式。

### 同主题作文分层模式

语文等学科常见诉求是「围绕一个作文主题，给基础较弱/中等/优秀学生分别出不同立意的作文」——三层都是作文，不是基础层退化成字词默写、拓展层才写。这类需求在 `params.json` 里**只需填 `unit`（单元/主题）+ `types` 含「写作」**即可，引擎会自动进入同主题作文分层模式：

- `build_prompt` 检测到写作类 + 给定 `unit` 时，注入「同主题作文分层」约束：三层均**围绕该同一主题命题、题型统一为写作**，分别给出由浅入深的立意方向，并禁止把基础层退化成字词默写或阅读理解。
- 三层立意方向（已与 A/B/C 学情对齐）：基础层=平实记叙（把事写清楚、情感真实，对应语言建构与运用）；巩固层=细节描写 + 情感升华（对应思维发展与审美鉴赏）；拓展层=立意新颖 / 思想深刻 / 创意表达（对应审美鉴赏·文化传承）。
- 硬约束：三层 `rubric` 量规须对应各层培养目标（基础=内容完整·语言通顺；巩固=细节·情感；拓展=立意·创意）。
- 不填 `unit` 或题型不含写作则维持原行为。

判定信号很直接：老师是否「围绕一个作文主题要不同立意的作文」——是就填 `unit` + 写作题型走此模式，要的是离散读写题则不触发。

### 三层语义（A/B/C）统一对照

skill 的「基础 / 巩固 / 拓展」三层，就是业界常说的 A/B/C 分层作业框架，全学科统一适用：

| 分层 | 对应框架 | 面向学情 | 培养目标（核心素养） | 认知层级（布鲁姆） |
|---|---|---|---|---|
| 基础 | A 基础巩固层 | 基础薄弱、需夯实核心知识的学生 | 学科基础观念/技能（如语言建构、数学运算） | 记忆·理解 |
| 巩固 | B 能力提升层 | 掌握基础、需提升综合应用的学生 | 知识迁移与综合应用（如科学思维、逻辑推理） | 应用·分析 |
| 拓展 | C 拓展创新层 | 学有余力、善思辨探究的学生 | 开放探究与跨学科创新（如科学探究、审美创造） | 评价·创造 |

- 每层的「面向学情」与「培养目标（核心素养）」已写进 `SUBJECT_PACKS` 全部 6 个学科包的 `levels` 定义（物理/化学/生物通用，及语文/数学/英语/政史地/音体美信），随 `build_prompt` 整体注入生成提示词。模型出题须贴合对应学情、解析/答案须服务于该层培养目标（见 `BASE_TEMPLATE` 第 3 锚与 3b 条硬约束）。
- `render` 在作业单每层标题下印出该层「面向学情 ｜ 培养目标」，方便教师一眼判断分层是否合理。

### 第 4 步 · 拼装 prompt

prompt ≠ 一段话，而是 `通用模板 + 学科包 + 学段包 + 供题计划` 的拼装结果。完整模板与输出 schema 见 **`references/prompt-template.md`**。

```bash
python scripts/homework_kit.py prompt --params params.json
```

**把抽象要求翻译成硬性条件**（这是用户反复强调的工作方式）：

| 抽象要求 | prompt 里的硬性条件 |
|---|---|
| 有学术依据 | `sources` ≥1 条且 `generic=false`，否则禁止生成该题 |
| 对齐课标 | `meta.std_aligned` 必填，且必须是真实条目不得杜撰 |
| 分层科学 | 各层 levels 已含「面向学情 / 培养目标」与知识点·步骤硬规则，出题须贴合学情、解析须服务目标（三层语义见上表） |
| 语言规范 | 题干分句≤学段上限；禁用"超纲/竞赛/极难" |
| 答案正确 | 每题必附 `answer`+`analysis`；应用题数据须有唯一可算解 |
| 反幻觉 | `sources` 须真实可检索，禁止编造 |

### 第 5 步 · 生成 + 硬校验

```bash
python scripts/homework_kit.py validate --items llm_out.json --subject 数学 --stage "初中(7-9)" --plan plan.json
```

十三条硬校验 + 四条新增检查，覆盖：课标对齐 · 政策书面红线 · 总时长 · 溯源必填 · 必填字段 · 分句长度 · 认知层级上限 · 禁例关键词 · 原创超限 · 缺 `source_id` · 缺 `based_on` · 原创无素材 · **是否照办了供题计划**。退出码非 0 表示被拦。

**防「纯 AI 编造」是这套校验的底线，且分两层强制：**
- **结构级（无条件执行，不依赖计划）**：每题必须声明合法 `origin`，且对应档位带齐依据——`retrieve` 须有 `source_id`、`adapt` 须有 `based_on` + 答案一致性验算、`generate` 须有至少一条 `generic=false` 的真实 CNKI 文献。**不传 `--plan` 也会拦**；旧版这些检查被误关在 `if plan:` 里，无计划时编造题会直接通过，已修复。
- **事实级（传了 `--plan` 才生效）**：声明的 `source_id` / `based_on` 必须命中计划里真实抓取的候选题 `bank_id`，否则即引用计划外或编造的题源——这才是真正堵死"编个编号蒙混过关"的一关。

即：**每题要么来自原题（retrieve）、要么基于原题创作（adapt）、要么基于知网文献创作（generate），绝不允许无出处。** 官方解析交叉校验（`mcp__<SERVER>__tkQuestionAnalysis` 拿到的题库答案当外部基准）也在此层无条件执行，打破"模型改编→模型复算→模型判一致"的自证循环。

第 13 条专管 mix 配额不被架空：计划写明 `retrieve` 的题若被输出成 `adapt`，等于把"可以原样用的真题"又改了一遍，必须拦。

### 第 14 条：改编题的答案一致性验算（阻塞）

教师不信任 AI 出题，源头从来不是"题出得不够好"，而是**改了数据没改成答案**。一次错答案，整套东西就不会被用第二次，所以这条必须阻塞：

```json
"answer_check": {"changed": ["把 2 kg 改成 4 kg"], "recompute": "G=mg=4×10=40 N，故浮力为 40 N", "verdict": "一致"}
```

三者缺一即拦；`verdict` 不是「一致」也拦（说明改编数据与答案对不上，要么改数据要么改答案，不许带着"不一致"交付）；`changed` 为空同样拦——没列改动项意味着压根没改，那不是改编。
另外做了数值烟测：答案里的数值在 `recompute` 与 `analysis` 中都找不到时给出提醒（不阻塞，可能是表述差异）。

> **历史产出会在这里被拦**：本条上线前生成的 `items.json` 没有任何验算记录，重跑校验必然失败。
> 这正是要抓的东西——要么用新 prompt 重跑让模型真正重算一遍，要么人工逐题复核后回填，**不要为了让它"通过"而编一条假验算**。

另有**告警级**检查（不阻塞，退出码仍为 0）：**来源文献著录缺口**·**溯源未优先期刊**·**真题早于现行课程方案**·**题源出处缺年份**·**retrieve 题面被擅自改动**·**答案数值在复算里找不到**·**adapt 题答案与官方答案不同但未说明原因**·**答案数值在官方解析中找不到**。以 `~` 前缀输出，并单列到作业单末尾。

> **`--plan` 要传最终审定的那份计划**，通常是 `plan.json`。`plan_auto.json` 是 route 吐出的机器初稿，
> 人工调整后另存为 `plan.json` 是正常流程——此时若拿 `plan_auto.json` 去校验，第 13 条会如实报出两者差异，
> 这不是误报，是在提醒你"实际交付的题与机器初稿不一致"。

**没有脚本可跑时，你自己当校验器**——按同一份清单逐条过一遍，尤其是这四条：小学低段有没有出书面题、材料/情境题有没有给溯源、有没有编 sources、应用题数据有没有唯一可算解。

### 第 6 步 · 修正回环

不要用"失败→回到生成"的无限回环。用**一次修正**：把 `issues` 清单原样回喂给模型逐条改，改完复检，仍不过就带标记交付教师人工处理，并在输出里保留拦截说明，不要假装通过。

### 第 7 步 · 渲染交付

```bash
python scripts/homework_kit.py render --items llm_out.json --subject 数学 --stage "初中(7-9)" --out 作业单.md
```

每题显示「题库原题/改编变式/原创生成」标签 + 原题出处（附带新鲜度「近3年·期末卷·校级」）+ 改编自 + **答案一致性验算过程**（改编题）；`retrieve` 真题只显示原题出处、**不挂「学术溯源」**（直接使用原题不须走文献接口）；「学术溯源」仅在改编/原创结合了 CNKI 文献时出现；答案折叠；末尾给题目来源统计。

**🎓 双版本交付（强制，不可省略）**：渲染交付时必须**同时产出两份文件**——「学生作答版」与「教师讲评版」，两版题目须完全一致：
- **学生作答版**：`--audience student`，仅含题干、选项与作答区，**绝不含答案、解析、溯源**（严守 skill 红线「学生区绝不含答案」）；直接打印发学生独立作答。
- **教师讲评版**：`--audience teacher`（缺省即此），含答案、解析、原题出处、课标/素养标注，供审题与讲评。
脚本原生支持 `student` / `teacher` / `both`（`both` = 学生作业纸 + 教师备课参考合册）。**不得只交付合并版或只交付教师版——缺学生版等于把答案直接发给学生。** 无论用脚本还是模型自渲染（无脚本 / 通用版手写 HTML·MD），都须落地这两份独立文件。两份示例：

```bash
# 学生作答版（无答案）
python scripts/homework_kit.py render --items llm_out.json --subject 数学 --stage "初中(7-9)" \
    --format docx --audience student --out 作业单_学生版.docx
# 教师讲评版（含答案/解析/出处）
python scripts/homework_kit.py render --items llm_out.json --subject 数学 --stage "初中(7-9)" \
    --format docx --audience teacher --out 作业单_教师版.docx
```

**给老师的交付格式（推荐 Word）**：加 `--format docx` 可直接产出 A4 版 `.docx`（课标/素养/题目来源信息卡、分层学情与培养目标、来源标签配色、答案核验），老师可直接打印或二次编辑。需本机装有 `python-docx`；缺 `docx` 依赖时回退为 `--format md`。**严禁向成品写入 SID 等内部流水号，也不印「著录缺口」内部说明块——这些仅在校验器/开发侧使用。**（内部标识不进入成品的通用红线见 [_shared.md](references/_shared.md)「干净输出红线」）

```bash
python scripts/homework_kit.py render --items llm_out.json --subject 数学 --stage "初中(7-9)" \
    --format docx --subtitle "一元二次方程的应用 · 初中数学 · 课后巩固" \
    --out 作业设计单_一元二次方程的应用.docx
```

若 `params` 填了 `shared_material`，材料统一在作业单**顶部展示一次**，各题只列设问、不再重复材料块（见上文「同材异层模式」）。

交付时必须写清："**这是待审草稿，答案需教师复核后才可布置**"。

### 第 8 步 · 验证这套东西合不合适

**顺序不能反**：先自己跑通（L1）→ 再找教研员验题（L2）→ 最后找老师试用（L3）。一上来就找老师试是最贵的错——一个低级 bug 就能毁掉整套东西的信任，而这种 bug 你自己跑 30 组就能抓到。详见 **`references/validation.md`**。

**一票否决**：答案错误率 > 0 → 直接判不可用，不进下一层。
**判定合适**：流程稳定跑通 + 答案零错误 + 编辑率 ≤40% 且教师愿意再用。

---

## 两条不可协商的红线

1. **政策合规**。小学一二年级不布置书面家庭作业；小学三至六年级书面作业≤60 分钟/天；初中≤90 分钟/天（"双减"）。`allow_written` 与 `max_minutes` 在代码层拦截，不能靠模型自觉。政策数值为公开文件参考值，正式上线前按当地最新文件校准；高中无全国统一规定，一律用【待补充】占位而非编数字。
2. **领土与价值观**。政史地材料必须真实可查并标来源+时间；必须使用合规标准地图；涉及台湾、香港、澳门必须表述为中国的一部分。建议做成生成前白名单过滤 + 生成后关键词拦截双重保险。

---

## 学术溯源

规则全部收在 **`references/source-citation.md`**，需要挂 `sources` 或校验器报了溯源提醒时才读。这里只留三句话：

- **文献只能来自 edu MCP**：检索走 `mcp__<SERVER>__searchVectorBJ`，再用 `mcp_adapters.py lit` 标准化。**不允许凭记忆写文献名，也不允许用公开检索结果冒充 CNKI 文献**。
- **来源优先级**：期刊论文 > 学位论文 > 报纸 > 专著 > 文集析出 > 教材。期刊能给出完整的「作者·篇名·来源期刊·年份·期」，教师可在 CNKI 精确定位；教材不是学术来源。
- **唯一绝对禁止**：编一个看起来很像的文献名。接口没返回的字段（作者/刊名/卷/页）留 `None` 渲染成灰色【待补充】——**缺=待补，填错=编造**。编造的溯源比没有溯源更糟，它是这套差异化方案的地基。
- **范围**：「学术溯源」是 CNKI 文献标记，只在「改编/原创且结合了知网数据」时出现；`retrieve` 真题是题库原样取用，只显示「原题出处」，不挂文献溯源、也不计入「著录缺口」提醒。
- **查无文献＝说没有，绝不编造**：`generate`（原创生成）必须挂经 `mcp__<SERVER>__searchVectorBJ` 实检返回的真实篇名；若检索相关主题无结果，**本题不得作为 generate**——应改为 `adapt`（基于某道真实原题），并在作业单如实标注「未检索到可引用 CNKI 文献」。渲染器对无 `sources` 的改编/原创题会自动打印这条提示，不要删、不要改成虚构文献。`adapt` 题以原题为底，可附 CNKI 文献增强但不强制；附的文献同样必须真实可检索。

---

## 参考文件地图

- **跨场景公共约定（权限固定提示 / 干净输出红线 / 触发词格式 / 版本与完工标准 / MCP 前缀自检）**：[_shared.md](references/_shared.md)

| 文件 | 什么时候读 |
|---|---|
| `references/constraint-packs.md` | 每次出题前，确认该学科+学段的硬性规则 |
| `references/prompt-template.md` | 要写/改 prompt，或接真实大模型时 |
| `references/supply-modes.md` | 涉及题库、原创占比、供给策略时 |
| `references/source-citation.md` | 要挂 `sources`，或校验器报了溯源/著录缺口时 |
| `references/workbuddy-mcp.md` | 要连 CNKI 基础教育 MCP、调题库/文献/知识点时（含接口登记表、字段缺口与降级策略） |
| `references/validation.md` | 方案做完了要验证能不能用 |
| `scripts/homework_kit.py` | 拼 prompt、路由、校验、渲染全程调用 |
| `scripts/mcp_adapters.py` | edu MCP 原始返回清洗：学科码解析、题库标准化、文献解析与著录补齐、候选体检 |
| `scripts/bank_to_items.py` | 题库 HTML（`Content` 含 `<table class="edittable">` 与 `<img>`）→ `items.json`+`plan.json`：数据表直接落真表格，原题配图自动下载嵌入 `figures/`，子问题/填空一并解析，retrieve 档自动带 SID；传 `--analysis` 时同步回填官方答案与解析 |
| `scripts/fill_analysis.py` | 通用回填工具：`mcp__<SERVER>__tkQuestionAnalysis` 原始/标准化结果 → `items.json` 的 retrieve 档（按 SID 写 answer/analysis/points，题面不动）；匹配不到的留「回查原卷」占位 |

---

## 已有最佳实践（踩过的坑）

- **校验器不能只是装饰**：构造必被拦的用例（超时长、书面红线、`gen_cap=0`、题库无覆盖、把 retrieve 写成 adapt）去看它拦不拦。
- **供给必须问「作业用途」，不能默认全改编**：曾经七八份作业全是 `adapt`，教师拿不到一道能原样布置的真题。
  根因是 `supply` 三档互斥单选，选了改编就整份改编——现在默认 `mix`，配额由 `job_type` 决定。
  同时注意：**与 KPI 相关的判定式场景（周测/月测/单元测验）必须压制原题**，否则背答案让成绩失真。
- **`retrieve` 题不是「少改一点」，是「一字不改」**：它的全部价值在于可以直接布置、答案已被考试校验。
  模型擅自润色表述、优化数字的冲动极强，一旦照做，原题和改编就没有任何区别了。
  所以第 13 条校验专门拦「计划写明 retrieve 却输出了别的 origin」。
- **mix 模式下，底座选错的代价比全改编时更高**：`adapt` 时模型还能顺手把不适合的部分改掉，
  `retrieve` 一字不改，**没有任何补救机会**。实测八年级《浮力》的 retrieve 题选到了含热机效率与功率的
  综合题（学生彼时没学到）。所以 mix 模式下必须比从前更严格地人工审核检索底座，
  尤其警惕「综合题只在一问里考目标知识点」这种情况。
- **改编题的答案一致性验算必须由模型显式写出来**（第 14 条阻塞）：只要 `answer_check`，不要"我复核过了"这种口头保证。
  写出来的过程还能让教师顺着 `recompute` 查，而不是自己动手重算一遍。
- **早于现行课程方案的真题要先机器筛一遍**：2022 版义务教育课程方案（高中为 2017 版课标 2020 年修订）
  是硬分界线，之前出版的真题考法、数据都可能已不适用。这条能自动判出来，别留给人。
- **变式包才是"改编"的主场**：不要为了凑题把每道题都改一遍；挑一道命题质量高的真题留作 `retrieve`，
  再派生 2–3 个变式填分层 B 卷和错题二刷，审题成本比全改编低一个量级。
- **给教师的应该是"可改的数组"，不是"已定的答案"**：配额可以被 `overrides` 逐题改，
  变式类型和个数也可以改（`-n` / `--kinds`）。凡是有默认值的地方，都要留一个教师能改的口子。
- **给 adapt 题做相似度比对**：`adapt` 题与候选题干 >80% 相似判照抄，这是最容易偷懒的地方。
- **抽查 sources 真实性**：随机抽 20 条用 `mcp__<SERVER>__searchVectorBJ` 实检索一遍（篇名检索不到＝这条有问题），这是 L2 验证里最不能省的一步。
- **L3 最有价值的信号是"教师改了什么"**，不是分数。多人都在改同一处，那就是下一版必修点。
- **候选题不足会产出孪生题**：3 条候选出 6 题时同一 `SID` 被分配两次。路由已修（层内未用→全库未用→被迫复用三级取题，复用题标 `reused:true` 并告警），校验器也会拦「两题同 `based_on`」。但仍应先把候选补足到 ≥ 题量×1.5，别指望兜底。
- **复合学科包必须问清二级学科**：理化生/政史地不指定物理还是化学就检索，会混出物理题和化学题。
- **`mcp__<SERVER>__tkPoint` 返回 30 万字符**，会被截断落盘。只按需用 `point` 子命令抽命中项，不要全量读进上下文。
- **改完脚本必须跑一次 `ast.parse` + `import` 再宣布完成**：本地编辑在文件尾部做多处替换时，出现过"调用点改了、函数定义没改"的悬空引用。
- **引用课文/教材原文必须有底稿，否则显式标核校**：模型凭记忆写台词会出错（实测写出"侍萍三次'天哪'"且第二三句文字完全相同，题库里只有摘要、无从核对）。凡引用原文：有底稿照抄并注出处；无底稿就写〔按任教教材节选核校〕并给教师替换方案。**绝不能凭记忆硬写原文**——答案错了是"一票否决"级事故。
- **学科包只有 6 个，教师说的学科名要过一遍别名表**：`SUBJECT_PACKS` 只有 语文/数学/英语/理化生/政史地/音体美信。实测传 `物理` 时旧版 `get_pack` 静默 fallback 成**数学包**——题型里没有实验设计、推荐刊物是《数学通报》，整套规则张冠李戴还不报错。现已加 `SUBJECT_ALIAS`（物理/化学/生物→理化生，历史/地理/政治→政史地…），未命中直接报错不再退化。**新增学科包时必须同步别名表**。
- **路由只按 Degree 分层匹配，不校验知识点契合与超纲**：实测八年级《浮力》路由选中了考热机效率、推力功率、深海压强的题——它们确实是"浮力"关键词命中的综合题，但热机、功率彼时尚未学到。综合题只在其中一问考目标知识点时尤其危险。**路由产出后必须人工审一遍底座的知识点**，不能只看分层匹配度。
- **溯源只有教材时，"期刊优先"提醒原本会静默**：校验器把 textbook 排除在学术溯源外，导致"整题只挂教材"这一最该提醒的情形反而没告警。现已补：只有教材溯源时提示"教材不算学术来源，建议补引期刊论文"。
- **`mcp__<SERVER>__tkSearchQuestion` 关键词不能带空格**：传 `"雷雨 曹禺"` → nginx 400；改单关键词 `"雷雨"` 正常。多概念检索就分多次检索再合并。
- **长材料放 `material` 字段，题干保持短句**：高中分句上限 35 字，把大段材料塞进 `stem` 必然被拦。渲染时 `material` 单独成块（支持 Markdown 表格），`stem` 只留设问。
- **同材异层优先用 `params.shared_material`，别把同一段材料分别塞进各题的 `material`**：前者顶部渲染一次、版式干净；后者会让同一段材料在作业单里重复出现 N 次（旧行为，已不推荐）。共享材料模式下，各题 `material` 留空、`stem` 用「根据材料」指代即可。
- **检索同一单元时会混入"还没学到的课文"**：讲完第 18 课出题，检索命中里常有第 19、20 课的课文（同单元综合题），这不是知识点超纲而是**课时进度超纲**，按考点/关键词都躲不开，只能人工审底座。处理办法是走 `adapt` 把语段改写成纯本课的语境，并在 `answer_check.changed` 里写清删掉了什么。
- **`retrieve` 与「分句上限」冲突时，`retrieve` 赢**：真题原设问常常就超学段分句上限（实测小学题设问 25 字 > 20 字上限），为凑字数改写它，等于把 `retrieve` 悄悄做成 `adapt`——那正是第 13 条要拦的事。分句上限约束的是**模型自撰的题干**，所以校验器对 `origin=retrieve` 只提醒不阻塞；确要拆分应改走 `adapt` 并在 `notes` 注明。
- **判断 retrieve 题面有没有被改，要比对 `material` + `stem`**：只比 `stem` 会让所有"段落放 material、设问放 stem"的题必然误报。改回真题原文时注意连小题要求（如"（用加点词写句子）"）都不要润色。
