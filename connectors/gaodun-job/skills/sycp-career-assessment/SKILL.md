---
name: sycp-career-assessment
display_name: 生涯测评
display_name_en: Career Path Assessment
description: 当用户提到生涯测评、生涯规划、大学生涯方向、公考/考研/留学/打工人/自由职业/躺平倾向时调用本Skill，用于分析大学生的生涯方向倾向。
description_zh: 生成 10 道题的生涯方向测评，通过 6 选一答题方式分析用户在公考/央国企、自由职业、打工人、留学、保研/考研、躺平六大方向的倾向……
description_en: Use when users mention career path assessment, college student life planning, or choices between public servant exam / central state-owned enterprises……
category: 15-Education
version: 2.1.1
author: Gaodun
---

# 生涯测评 Skill

## Overview

生成生涯测评题目并计算结果，覆盖 6 个生涯方向：

- A：公考/央国企
- B：自由职业
- C：打工人
- D：留学
- E：保研/考研
- F：躺平

本版本为 10 题简版，每题 6 选一（A-F），每个选项归属一个生涯方向标签。
6 个标签均匀分布，共 60 个选项，适合做早期演示、训练和平台上传使用。

## When to Use This Skill

在以下场景触发本 skill：

- 用户明确说出"做生涯测评""测生涯方向""启动生涯规划测评"这类完整指令
- 用户直接询问"我大学适合走哪条路""我适合公考还是考研""帮我测一下我的生涯方向"
- 用户主动提及"打开生涯测评""开始生涯测评""做生涯测评""生涯测评开始"
- 用户说"我想了解自己的生涯方向""帮我做个生涯测试"
- 用户历史对话3轮内明确提过要做生涯测评，当前轮次说"继续""开始吧""下一步"
- 用户直接发送"生涯测评""生涯规划测评"作为唯一指令，无其他无关内容

在以下场景需要二次确认后才触发（命中后先弹出确认话术，用户同意再启动）：

- 用户只单独发送"生涯"两个字，没有后续补充
- 用户讨论某类生涯方向后，说"我好像就是这种人""我感觉我符合这个方向"
- 用户提到"我朋友说适合走公考，想验证一下"，没有直接说要启动测评
- 用户在讨论生涯规划相关话题后，说"帮我测测看"，没有明确指向其他工具

## When NOT to Use This Skill

以下场景**不触发**本 skill：

- 用户仅询问生涯规划科普："大学四年应该怎么规划""公考和考研哪个难"
- 用户仅查询某类方向的介绍："公考需要准备什么""留学申请流程""考研科目"
- 用户讨论生涯规划的非测评应用场景："如何写大学规划书""生涯规划面试技巧"
- 用户在讨论其他完全无关的话题时，偶然提到生涯方向："我室友天天躺平""我朋友考研上岸了"
- 用户明确要求其他类型的测试："我要做MBTI测试""帮我测霍兰德职业兴趣""生成九型人格测试"
- 用户的需求是内容生成类："帮我写一篇大学生活规划小红书文案""生成考研复习短视频脚本"
- 用户同时提出多个混合需求，且没有明确表示要做测评
- 用户明确表示"我不想做测评""我只是想了解大学规划知识"

## 红线清单（绝对禁止清单）

本 skill 一旦被触发，下列行为**绝对禁止**。禁止任何"为了适配用户/为了让结果更好看/为了给朋友/为了省事/为了换 UI/为了演示"的偏离尝试——触犯任何一条即为输出违规，必须回头重走标准流程。

1. **禁止自行设计 HTML/CSS/JS**：禁止凭印象写"看起来差不多"的卡片；禁止套用之前展示过的版本（即使那一次的输出看起来已经稳定）。**必须** `Read references/template.md` 后，按 §5.1 / §5.2 byte-stable 复刻。
2. **禁止改造、合并、简化 template.md 本体**：禁止改 class 名、改色值、改圆角、改字号；禁止把 `.sycp-assessment-card` 改成 `.assessment-card` 之类的别名；禁止裁剪 `<style>` 块（含 `.option-btn` / `.option-btn.selected` 规则）、禁止把 `<style>` 改成 inline；禁止删减 `<script>` 里的 IIFE 包裹、try/catch、`TAG_PROFILES` / `OPTION_TO_TAG` / `PRIORITY` 嵌入常量。option-btn 样式在 `<style>` 块 class 规则内（元素无 inline style），submit-btn 保留 inline style，均照抄 template.md。
3. **禁止派生请求走捷径（最常见违规）**：用户说"再来一份""朋友也要测""给同事也来一套""试试换个 UI""重置再来一遍"——一律重新 `Read references/template.md` + 走 §5.1 标准流程，**不允许**把"上一次的卡片"复制过来改 ID 后缀（如 `-friend` / `-v2`）当新产物输出。新卡片必须是 template.md 的 byte-stable 实例，所有 ID、class、style、文案与首发保持逐字符一致。
4. **禁止预选 / 预填答案**：初始 HTML 中任何 `option-btn` 都不得带 `selected` class 或选中态样式（选中态由 `.option-btn.selected` class 规则承载，初始不得引用）；不得为了"演示"预先勾选某个标签。
5. **禁止省略题目或替代 content**：10 题必须逐题完整渲染 `question-row`，1→10 不跳号；每题的 6 个选项 `contentA-F` 必须照抄 `references/questions.md` 原文，禁止用省略号（如 `A. 办公室...`）或自行归纳；不得为某用户压缩到 5 题、合并相邻题、调整题干顺序。
6. **禁止变更 DOM 结构**：禁止把 `<button class="submit-btn">` 换成 `<input type="submit">` 或把外层卡片从 `<div class="sycp-assessment-card">` 换成 `<form>` / `<section>` / 自定义容器；禁止在题目之间插入额外小标题、装饰区块、说明文案（除非 template.md 已经写死）；禁止加 emoji / icon / banner / 渐变色 / 自定义图。
7. **禁止用 Write / Bash / Edit 落盘 HTML 文件**：模板只能通过 `show_widget` 以 inline HTML 片段渲染到对话流；不得写入学员电脑本地 `.html`、不得引导用户打开本地文件作答、不得把模板以 Markdown 代码块形式输出让用户复制粘贴。
8. **禁止跳过题库读取**：必须 `Read references/questions.md`；题库读取失败或不足 10 题时直接报错并停止，不得凭印象补题。
9. **禁止跑题 / 任意修辞**：用户问"再来一遍""换个背景色""做新版本"等都不能成为脱离 §5.1 的理由；本 skill 只产出标准 §5.1 / §5.2 卡片，不产出其他视觉变体；不嵌入"朋友版""v2"等自定义标题。
10. **禁止把 Visualizer 报错当成"自己重写"的提示**：当 `show_widget` 因 widget 沙箱限制（如 `<form>` 标签不能用 / loading_messages 为空）报错时，正确做法是回到 template.md 检查对应约束并把 HTML 改成模板允许的形式（删 `<form>` 等），而不是从零另起一套新模板。
11. **禁止冒用"派生卡片"概念**：哪怕为了"互不干扰"也不允许给同一会话渲染第二张题目内容不同/样式不同的卡片；本 skill 的输出在单次会话内是单一的 §5.1 实例，重复触发走"重置 / 新测评"流程，重新进入标准渲染。

## 题目元数据

```yaml
assessment_id: SYCP-10-001
assessment_name: "生涯测评（10题简版）"
question_total: 10
tag_count: 6   # A/B/C/D/E/F
tag_list:
  - {tag: A, name: 公考/央国企, priority: 2}
  - {tag: B, name: 自由职业, priority: 5}
  - {tag: C, name: 打工人, priority: 4}
  - {tag: D, name: 留学, priority: 3}
  - {tag: E, name: 保研/考研, priority: 1}
  - {tag: F, name: 躺平, priority: 6}
question_bank_path: "sycp-career-assessment/references/questions.md"
tag_profiles_path: "sycp-career-assessment/references/tag_profiles.md"
algorithm_path: "sycp-career-assessment/references/algorithm.md"
score_calculation_path: "sycp-career-assessment/scripts/calculate_sycp.py"
score_function: "calculate_scores"
entrypoint: "python sycp-career-assessment/scripts/calculate_sycp.py --answers '{\"1\":\"A\",\"2\":\"B\"}'"
config_source: "需求方提供的 sycpData.json + 6 段固定文案；落盘到 references/tag_profiles.md"
```

## 文件职责与加载策略（关键）

| 文件 | 内容 | 何时读取 |
|---|---|---|
| `references/questions.md` | 10 题题库（题干/提示语/选项/标签） | 每次触发测评必读 |
| `references/template.md` | **§5.1 答题卡片 + §5.2 结果卡片完整 HTML/CSS/JS 模板（byte-stable 本体）** | **仅渲染测评卡片前读取**（按需加载，勿常驻） |
| `references/tag_profiles.md` | 6 个方向 × 4 段生产文案 | 算分/渲染结果时查表 |
| `references/algorithm.md` | 评分算法说明 | 需要核对算法时 |
| `scripts/calculate_sycp.py` | 评分脚本（`calculate_scores`） | 需要脚本算分时 |

**加载原则**：触发本 skill 后，**只读取** `references/questions.md`（题库）+ 本文件；只有在需要渲染交互卡片时，才额外读取 `references/template.md`。不要一次性读取所有引用文件。

## 题目加载硬约束（关键）

1. 本 skill **仅提供 10 题简版**，不在任何场景下询问用户"要做几题"、不提供版本二选一入口。
2. 触发测评后必须直接进入 10 题答题流程，不得插入"选择题目数量"的中间步骤。
3. 题目必须从 `references/questions.md` 的 `## 题目 N` 小节读取，按 `id` 1→10 原序展示；**禁止模型自行编造或凭印象生成题目**。
4. 题库共 10 题，每题必须包含 `id` / `question` / `prompt` / `options`（每个 option 含 `option` / `content` / `tag`）四要素，渲染时不得遗漏任一字段，尤其不得省略 `options.content`。
5. 若题库读取失败或不足 10 题，必须直接报错说明，不得用"部分题目"凑数、不得用模型自拟题补齐。
6. 一次性展示全部 10 道题，不得分页、不得"先展示前几题"、不得逐题加载。

## 工作流程

1. 判断用户是否需要"开始测评"或"已有答案直接算分"。
2. 如为新测评：
   a. **Read** `references/questions.md` 加载题库（顶部 `> key: value` 为元数据；`## 标签说明` 为 6 方向标签；`## 题目 N` 小节含 `**题干**`、`**提示语**`、选项表 `| 选项 | 内容 | 标签 |`）。
   b. **Read** `references/template.md` 获取 §5.1 答题卡片模板（byte-stable 本体，本文件不再内嵌模板）。
   c. **用 show_widget** 将 §5.1 模板逐字渲染到当前对话流，按占位符规则填入题库数据（每题 6 个 `option-btn` 完整输出，禁止省略）。
   d. 用户作答后，由模板内嵌 `<script>` 完成校验与评分（算法与 `scripts/calculate_sycp.py` 的 `calculate_scores` 逐字段一致）。
3. 若用户提供答案要求算分：调用 `scripts/calculate_sycp.py` 或按同等算法计算，返回 JSON 报告。
4. 返回用户报告：胜出生涯方向 + 各标签计数/百分比 + 4 段文案。

**渲染通道唯一化（关键）**：测评卡片**只能**通过 show_widget 以内联 HTML 片段（`<style>` + `<div>` + `<script>`）渲染到当前对话流。**绝对禁止**用 Write/Bash 生成 `.html` 文件到学员电脑、禁止引导学员打开本地文件作答、禁止把模板输出为 Markdown 代码块让用户复制。题库读取失败或 show_widget 渲染失败时，唯一正确行为是向用户明确报错并停止。

## 渲染前自检 Checklist（show_widget 之前必走）

调用 `show_widget` 渲染答题卡片之前，模型必须对照下表逐项自检，任一项不符必须回头修正：

| # | 检查项 | 通过条件 |
|---|---|---|
| 1 | 已 `Read references/questions.md` | 10 题全部存在，每题含 id/question/prompt/6 个选项（content + tag） |
| 2 | 已 `Read references/template.md` | §5.1 + §5.2 两段模板本体已读入上下文 |
| 3 | `<style>` 块是否原样输出 | 静态元素 CSS 文本与 template.md 逐字符一致（class 名/属性值/缩进都一致） |
| 4 | 6 个 `.option-btn` 是否无 inline style、`.submit-btn` 的 inline `style` 是否原样 | option-btn 不带 style 属性（样式由 `.option-btn` / `.option-btn.selected` class 规则控制）；submit-btn style 与 template.md 完全相同（顺序、值、空格均一致） |
| 5 | 10 个 `question-row` 是否齐全 | `data-qid` 从 1 到 10 各出现一次，无重复、无遗漏 |
| 6 | 每题 6 个 `option-btn` 是否齐全 | 每题 A-F 均存在，`data-tag` 与 `OPTION_TO_TAG[qid][letter]` 一致 |
| 7 | `<script>` 块是否原样输出 | IIFE/try/catch/`TAG_PROFILES` 6 项/`OPTION_TO_TAG` 10 项/`PRIORITY`/`TOTAL=10`/`esc()`/选项点击/提交校验/结果拼接全部保留 |
| 8 | 是否有 `<form>` 标签 | 不允许 `<form>` / `document.forms` / `form.querySelector` |
| 9 | 是否引入 emoji/icon/装饰元素 | 整段 HTML 只允许 template.md 已写死的元素，不追加任何装饰 |
| 10 | 初始态是否无预选 | 没有任何 `.option-btn` 带 `selected` class 或选中态样式（初始 HTML 不带 `style` 属性） |
| 11 | 是否走 `show_widget` 渲染 | 不允许 Write/Bash/Edit 落盘 `.html`，不允许以 Markdown 代码块输出 |

只有 11 项全部 ✅，才能调用 `show_widget`。任何一项 ❌ 必须回头修补，禁止"先发出去再说"。

## 模板稳定性硬约束（红线级——违反任何一条即视为输出违规）

模板本体在 `references/template.md`，渲染时必须严格按下述规则（与模板内注释一致）：

1. **byte-stable**：模型只能替换模板中 `{...}` 占位符（`{qid}`/`{question}`/`{prompt}`/`{contentX}` 及 §5.2 占位符），**不得**增删 DOM 节点、改写 class 名、调整色值/字号/间距/圆角、引入额外元素（emoji/icon/装饰）。
2. **样式全部由 `<style>` 块 class 规则与 submit-btn inline style 承载**：卡片容器/标题/题目行/进度条/section/`.option-btn`（含 `.selected` 选中态）等一律用模板顶部 `<style>` 块；仅 `.submit-btn` 保留 inline `style` 属性（模板已写死，照抄）。option-btn 的选中态由 `<script>` 在点击时切换 `selected` class 触发，JS 写入的 inline style 值与 class 规则一致（视觉等价）。
3. **初始态禁止预选**：模型在初始 HTML 中**不得**给任何 `option-btn` 加 `selected` class 或选中态样式；选中态只能由模板内嵌 `<script>` 在用户点击时动态切换。
4. **交互全部由模板内嵌 `<script>` 实现**：选项互斥切换、进度条更新、提交校验（未答完滚动聚焦第一个未答题 + 显示 `.incomplete-tip`，不弹窗）、全答完按嵌入数据 `OPTION_TO_TAG` + `TAG_PROFILES` + `PRIORITY` 计算胜出标签与 `display_score`，原样拼接 §5.2 结果卡片 HTML 写入 `.answers-output`。
5. **结果卡片结构固定**：`result-header`（`h2` 方向名 + `score-display` + `summary`）→ `tag-detail`（4 段 `section` 按 1→2→3→4）→ `footer-hint`；**不渲染**顶部大字母（`dominant-letter`）与「各方向得分」`stat-row`。
6. **跨用户一致**：所有用户渲染的答题卡片 DOM 骨架、`<style>` 块 CSS、`<script>` 文本必须 byte-equal；允许随答题进度变化的字段仅限 `.selected` class 分布、`.progress-text` 内容、`.progress-bar-inner` 的 `width`。不得因用户身份/历史作答预填答案、改变顺序或省略内容。

## 评分规则

### 1. 标签计数

每道题的每个选项归属一个标签（A-F）。用户作答归一化为 `A`-`F`，匹配到的选项所对应的 `tag` 字段 +1：

- 答案归一：`1-6` → `A-F`，`A-F` 直通
- 6 个标签计数之和 = 已作答题数

### 2. 标签百分比

```text
percent[tag] = score[tag] / total_questions * 100   # 保留两位小数 ROUND_HALF_UP
```

### 3. 胜出标签

```text
max_count = max(score[A..F])
candidates = [t for t in [A,B,C,D,E,F] if score[t] == max_count]
dominant_tag = min(candidates, key=PRIORITY)
```

平局优先级：保研/考研(E=1) > 公考/央国企(A=2) > 留学(D=3) > 打工人(C=4) > 自由职业(B=5) > 躺平(F=6)

### 4. 总分（display_score，0-100）

```text
display_score = round(score[dominant_tag] / total_questions * 100)   # ROUND_HALF_UP 取整
```

例：胜出标签 A 计数 4 → 4/10*100 = 40.00 → `40`

### 5. 角色详情（4 段文案）

依据 `dominant_tag` 在 `references/tag_profiles.md` 中按 `tag` 查表，输出 `tag` / `name` / `priority` / `section_1`~`section_4`。**4 段文案必须为生产原文，不允许模型自行撰写或改写**。6 个方向必须全部覆盖，缺一不可。

## 输出格式

本 skill 的评分结果必须以 JSON 返回，结构固定如下（示例：A=4, B=1, C=2, D=1, E=1, F=1）：

```json
{
  "assessment_id": "SYCP-10-001",
  "assessment_name": "生涯测评（10题简版）",
  "status": "completed",
  "answered_count": 10,
  "total_questions": 10,
  "display_score": 40,
  "max_score": 100,
  "dominant_tag": "A",
  "dominant_name": "公考/央国企",
  "tag_counts": {"A": 4, "B": 1, "C": 2, "D": 1, "E": 1, "F": 1},
  "tag_stats": [
    {"tag": "A", "name": "公考/央国企", "score": 4, "percent": 40.00},
    {"tag": "B", "name": "自由职业", "score": 1, "percent": 10.00},
    {"tag": "C", "name": "打工人", "score": 2, "percent": 20.00},
    {"tag": "D", "name": "留学", "score": 1, "percent": 10.00},
    {"tag": "E", "name": "保研/考研", "score": 1, "percent": 10.00},
    {"tag": "F", "name": "躺平", "score": 1, "percent": 10.00}
  ],
  "tag_detail": {
    "tag": "A",
    "name": "公考/央国企",
    "priority": 2,
    "section_1_title": "天选公考/央国企圣体",
    "section_1": "【天选公考/央国企圣体】\n生来就是为了报效祖国！未来国家建设的中坚力量非你莫属！\n",
    "section_2_title": "大学四年规划",
    "section_2": "公考/央国企人的大学四年规划：\n绩点：大学四年认真学习，争取各科高分通过，提升绩点\n技能：高分通过英语四六级、国家计算机二级考试\n身份：入党；竞选学生会/社团主席\n背提：参加专业相关竞赛、科研项目，进入企业实习\n论文：写完毕业论文并通过答辩",
    "section_3_title": "备考路径",
    "section_3": "备考：\n大一--了解公考/央国企的报考要求及考试内容\n大二--明确公考/央国企入职路径与目标\n大三--复习申论、行测、公基等考试内容\n大四--参加公考/央国企笔试、面试，成功上岸",
    "section_4_title": "寄语",
    "section_4": "志当存高远，慎始而敢行！"
  },
  "analysis": {
    "summary": "用户在 10 道题中，公考/央国企 方向选了 4 次（最多），生涯测评结果为：公考/央国企。",
    "recommendation": "公考/央国企"
  }
}
```

### 确定性输出约束

1. 结果必须以脚本计算结果为唯一准绳，不允许模型自由推断分数或生涯方向。
2. `tag_counts` 必须按固定顺序输出 6 个标签：`{"A","B","C","D","E","F"}`。
3. `dominant_tag` 必须由"最高计数 + 平局优先级"规则得出，不能由模型自行命名。
4. 百分比必须保留两位小数，使用 `decimal.ROUND_HALF_UP`（与 Java `BigDecimal.ROUND_HALF_UP` 一致），不允许 Python 默认 banker's rounding。
5. `display_score` 为胜出标签百分比取整数（ROUND_HALF_UP），不允许模型自由发挥。
6. `tag_detail` 必须从 `references/tag_profiles.md` 按 `dominant_tag` 查表得到；**4 段文案必须为生产原文**。
7. `analysis.summary` 必须使用固定模板：`"用户在 10 道题中，{dominant_name} 方向选了 {counts[dominant_tag]} 次（最多），生涯测评结果为：{dominant_name}。"`；`analysis.recommendation` 必须为 `tag_detail.name` 字符串。
8. 同一组 `answers` 必须在多次调用间产生 byte-equal 的 JSON 输出（无随机数、无时间戳、无外部网络/DB 依赖）。
9. 若题目不完整，返回 `status: "incomplete"` 并列出缺失题号；不得强行生成完整结论。
10. 输出必须为纯 JSON，不允许嵌套说明、Markdown 代码块或额外字段。

## 评分入口

评分脚本位置：`scripts/calculate_sycp.py`，评分函数：`calculate_scores(answers, questions, tag_profiles)`。

示例命令：

```bash
python sycp-career-assessment/scripts/calculate_sycp.py \
  --answers '{"1":"A","2":"B","3":"A","4":"B"}' \
  --questions-path sycp-career-assessment/references/questions.md \
  --tag-profiles-path sycp-career-assessment/references/tag_profiles.md
```

## 重要原则

- 题库必须明确给出题目编号、题干、提示语和选项标签归属；
- 评分逻辑必须单独写在脚本文件中，不能隐含在对话里；
- 用户提交题目后，必须返回测试结果、得分和生涯方向；
- 若题目缺失或答案格式不合法，先要求用户补全，不要直接伪造结果；
- 选项标签映射必须保持一一对应；
- 同一组作答必须产出 byte-equal 的 JSON（无随机性）。

## 目录结构

```text
sycp-career-assessment/
├── SKILL.md                 # 指令层（本文件，精简版）
├── references/
│   ├── algorithm.md         # 算法说明
│   ├── questions.md         # 10 题题库（源自 sycpData.json）
│   ├── tag_profiles.md      # 6 个生涯方向 × 4 段文案
│   └── template.md          # §5.1/§5.2 渲染模板本体（byte-stable，按需读取）
└── scripts/
    └── calculate_sycp.py    # 评分脚本
```

## 资源说明

- 题库参考：`references/questions.md`（源自需求方提供的 `sycpData.json`）
- 生涯方向档案：`references/tag_profiles.md`（6 个方向 × 4 段文案，源自需求方固定文案）
- 渲染模板：`references/template.md`（§5.1 答题卡片 + §5.2 结果卡片，byte-stable 本体，仅渲染前读取）
- 算法说明：`references/algorithm.md`
- 评分脚本：`scripts/calculate_sycp.py`
- 报告文案单一来源：需求方提供的 6 段固定文案；文案需要变更时，重新覆盖 `references/tag_profiles.md` 即可生效，无需改动评分脚本
