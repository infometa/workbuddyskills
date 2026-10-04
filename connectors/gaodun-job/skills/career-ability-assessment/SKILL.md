---
name: career-ability-assessment
display_name: 职业能力测评
display_name_en: Career Competency Assessment
description: 当用户提到职业能力测评或能力评估时调用本Skill，用于分析能力结构并提出提升建议。
description_zh: 评估沟通协作、逻辑分析、执行推进、学习适应、问题解决等职业能力，并输出能力结构解读。
description_en: Use when users mention career competencies, capability assessments to analyze their competency profile.
category: 15-Education
version: 2.0.1
author: Gaodun
---

# 职业能力倾向测评 Skill

## Overview

生成职业能力倾向测评题目并收集作答，覆盖 2 部分、17 个职业能力维度，共 85 题：

**第一部分 · 天赋能力（6 维，第 1–30 题）**

- 语言能力 / 写作能力 / 数学能力 / 空间能力 / 动觉能力 / 审美能力

**第二部分 · 通用能力（11 维，第 31–85 题）**

- 逻辑思维 / 研究分析 / 创新能力 / 灵活应变 / 人际交往 / 组织协调 / 风险防范 / 商业思维 / 用户洞察 / 细节洞察 / 情绪控制

每题五级作答：完全符合（8）/ 比较符合（6）/ 一般符合（4）/ 比较不符合（2）/ 完全不符合（0），**正向计分**（越符合得分越高）。每维度 5 题，维度得分 = 该维度 5 题得分之和，范围 0–40；报告页按 100 分制展示（偶数×2.5 恒为整数，无需四舍五入）。

> **功能范围**：本 skill 实现问卷渲染（`show_widget` 内联卡片）、85 位紧凑序列提交、评分脚本 `calculate_scores.py`、结果报告卡输出契约（Top 5 能力卡片 + 17 维得分条，100 分制）。

## When to Use This Skill

在以下场景触发本 skill：

- 用户希望做职业能力测评或能力倾向测试；
- 用户问“我有哪些职业能力优势”“测测我的职业能力”；
- 用户希望复用该题库做职业能力测评页面；
- 用户已给出一组五级作答结果，要求生成职业能力画像。

## 题目元数据

```yaml
assessment_id: CAREER-ABILITY-85-001
assessment_name: "职业能力倾向测评（85题版）"
question_total: 85
dimension_count: 17
part_count: 2
parts:
  - id: 1
    name: "天赋能力"
    title: "第一部分"
    seq_range: "1-30"
    dimensions: ["语言能力", "写作能力", "数学能力", "空间能力", "动觉能力", "审美能力"]
  - id: 2
    name: "通用能力"
    title: "第二部分"
    seq_range: "31-85"
    dimensions: ["逻辑思维", "研究分析", "创新能力", "灵活应变", "人际交往", "组织协调", "风险防范", "商业思维", "用户洞察", "细节洞察", "情绪控制"]
answer_options:
  - { option: "A", label: "完全符合",   score: 8 }
  - { option: "B", label: "比较符合",   score: 6 }
  - { option: "C", label: "一般符合",   score: 4 }
  - { option: "D", label: "比较不符合", score: 2 }
  - { option: "E", label: "完全不符合", score: 0 }
question_bank_path: "career-ability-assessment/references/questions.json"
algorithm_path: "career-ability-assessment/references/algorithm.md"
score_calculation_path: "career-ability-assessment/scripts/calculate_scores.py"
score_function: "calculate_scores"
submission_format: "85 位 A-E 紧凑字符序列（正向计分，防截断）"
entrypoint: "python career-ability-assessment/scripts/calculate_scores.py --answers 'ABCAB...'"
```

## 工作流程

1. 判断用户是需要“开始测评”还是“已有答案直接算分”。
2. 如为新测评，渲染问卷卡片并收集五级作答。
3. 校验作答：题号、选项（A–E）、维度映射正确。
4. 调用评分脚本计算 17 个维度得分。
5. 返回职业能力画像：17 维分数（100 分制）、Top 5 优势能力卡片、各维度得分条。

## WorkBuddy 视觉化交互卡片约束（核心执行规范）

1. **唯一渲染通道**：
   生成测评页面的 HTML/CSS/JS 代码后，**必须且只能**调用内置的 `show_widget` 工具，将代码作为参数传入，以触发聊天窗口的原生卡片渲染。
   - `show_widget` 是 WorkBuddy 平台**原生渲染工具**，直接以 `tool_use` 发起调用即可；**严禁在思考阶段用 `ToolSearch` 或任何工具发现机制去"确认 `show_widget` 是否存在"**——原生工具不通过 `ToolSearch` 暴露，检索不到 ≠ 工具不存在 ≠ 环境不支持。
   - 正确流程：直接发起 `show_widget` 调用 → 成功即渲染；仅当调用被实际执行后返回错误或被拒绝，才按下条「异常处理」处理。

2. **绝对禁止项**：
   - **严禁**直接将 HTML/CSS/JS 代码以 Markdown 代码块的形式输出。
   - **严禁**生成或提供独立的 `.html` 文件下载链接。
   - **严禁**在不调用 `show_widget` 的情况下直接输出组件代码。

3. **异常处理**：
   仅当 `show_widget` 调用**被实际发起并返回错误、或被用户/平台拒绝**时，才视为渲染失败。此时仅向用户输出**一句话**纯文本提示（如："当前环境暂不支持内联渲染，请稍后重试或检查配置"），**绝对不允许**：
   - 退化为生成独立 HTML 页面；
   - 退化为把问卷/题目以纯文本逐题列出（**禁止输出"文本版 85 题"等替代问卷**——那等于让用户在聊天里逐题手答，体验崩坏，且仍非卡片渲染）；
   - 把思考过程、工具检索结果暴露给用户。
   - **关键**：思考阶段用 `ToolSearch` 找不到 `show_widget`，**不构成**渲染失败，不得据此放弃渲染——必须仍直接发起 `show_widget` 调用。

4. **视觉稳定性要求**：
   传入 `show_widget` 的代码需保持结构稳定，避免使用可能导致聊天窗口高度剧烈跳动的复杂外部依赖。

5. **模块加载前置（避免临场纠结）**：
   - 本 skill 的问卷卡与结果报告卡均走平台 `interactive` 渲染通道。若平台通过 `read_me` 机制按需加载模块，确保 `interactive` 已加载即可；**无需加载 `chart` / `diagram` 等额外模块**。
   - 问卷的 5 级按钮组、报告卡的得分条与能力卡片，**全部用纯 HTML + CSS 实现**（得分条用 `<div>` + CSS `width`）；**严禁引入 chart.js / echarts / d3 或任何外部图表库/CDN 脚本**——非必需且会引发高度跳动。

### 1. 渲染目标

当用户触发“开始测评”或“职业能力测评”时，必须返回一个可渲染的内联卡片，而不是纯文本说明。

该内联卡片必须包含：

- 顶部标题：`职业能力倾向测评`
- 二级说明（引言，原样取自题库 `questionConfig.desc`）：`本测评将帮助你系统发掘自身的天赋潜能与职业通用能力优势……请根据直觉快速作答。`
- 顶部进度条：显示已答题数/总题数，例如 `已答 17 / 85`
- 题目列表：每题显示全局序号 + 题干（题干取自题库 `stem`，原样不得改写）
- 每题答题区域：**5 个分段按钮**，从左到右依次为 完全不符合 / 比较不符合 / 一般符合 / 比较符合 / 完全符合
- 分段展示：85 题按 2 部分（第一部分 1–30 / 第二部分 31–85）分段，每段上方有分段标题与提示词
- 底部交互：提交按钮（全部答完才可点）

### 2. 视觉结构要求

视觉结构必须遵循以下稳定版布局：

- 整体是白色/浅灰背景的卡片容器，边框柔和、圆角适中
- 标题大字号、深色字体；引言中等字号、灰色字体，位于标题下方
- 进度文本位于标题区右侧，如 `已答 17 / 85`；进度条位于标题区下方
- 题目行高统一，题干左对齐，选项按钮组在题干下方一行排列
- 题目行之间用浅边框分隔
- **5 级按钮组（关键）**：每题下方一组 5 个等宽按钮（`flex: 1 1 0`，单行不换行），从左到右依次为 完全不符合(E) → 比较不符合(D) → 一般符合(C) → 比较符合(B) → 完全符合(A)，配色按“不同意→同意”语义渐变（左红右绿），**不允许出现无底色（白底/透明）状态**：
  - 未选中：5 个按钮均为灰底（`#E5E7EB` 底 / **`#4B5563` 深灰字**，确保灰底上文字清晰可读）
  - 选中 `E 完全不符合`：该按钮红底白字（`#DC2626` / `#FFFFFF`）——位于最左
  - 选中 `D 比较不符合`：该按钮橙底白字（`#F97316` / `#FFFFFF`）
  - 选中 `C 一般符合`：该按钮琥珀底白字（`#F59E0B` / `#FFFFFF`）——位于正中
  - 选中 `B 比较符合`：该按钮绿底白字（`#22C55E` / `#FFFFFF`）
  - 选中 `A 完全符合`：该按钮深绿底白字（`#15803D` / `#FFFFFF`）——位于最右
  - **按钮左右位置 ≠ 提交编码顺序**：视觉上从左到右是 E→D→C→B→A，但紧凑提交序列第 `i` 位对应 `seq=i` 题、值为用户所选选项的编码（A=完全符合…E=完全不符合），与按钮在 DOM 中的位置无关；`data-option` 即选项编码，提交时按 `seq` 顺序拼成 85 位序列，不按按钮位置拼。
  - 同一题只能有一个按钮带语义色，互斥；点击未选中项时，原带色按钮必须**背景与字色同步**立即变回灰底深灰字，避免出现双带色或白底残态
  - **字色恢复（关键，防止文字消失）**：按钮从选中态切回未选中灰底态时，**字色必须同步从白字恢复为深灰字（`#4B5563`）**，绝不允许背景已变灰但字色仍停留在白字——白字配灰底会导致文字几乎不可见（用户反馈"按钮字体变白消失"）。即每个按钮的 `(背景, 字色)` 必须成对切换：未选 = `(#E5E7EB, #4B5563)`，选中 = `(语义色, #FFFFFF)`，二者不得错位。
  - 切换必须即时、无延迟；hover 可有轻微高亮但不得与上述选中色混淆
  - 按钮文案**只显示选项标签**（完全符合 等），**不得显示分数**（8/6/4/2/0），避免作答偏差
- 在页面底部可显示辅助说明

### 3. 分段提示词要求（必须严格遵守）

85 道题必须按题库真实顺序存储为 2 个连续区段，每段上方显示固定标题与提示词，不得改写语义、删减或自由替换：

1. 第一部分标题：`第一部分 · 天赋能力`
   - 提示词：`以下题目评估你的 6 项天赋能力：语言、写作、数学、空间、动觉、审美。请根据第一直觉快速作答，无需过度思考。`

2. 第二部分标题：`第二部分 · 通用能力`
   - 提示词：`以下题目评估你的 11 项通用能力：逻辑思维、研究分析、创新、灵活应变、人际交往、组织协调、风险防范、商业思维、用户洞察、细节洞察、情绪控制。请根据第一直觉快速作答，无需过度思考。`

题库真实顺序如下：

- 第一部分：第 1–30 题（语言 1–5 / 写作 6–10 / 数学 11–15 / 空间 16–20 / 动觉 21–25 / 审美 26–30）
- 第二部分：第 31–85 题（逻辑 31–35 / 研究分析 36–40 / 创新 41–45 / 灵活应变 46–50 / 人际 51–55 / 组织协调 56–60 / 风险 61–65 / 商业 66–70 / 用户洞察 71–75 / 细节 76–80 / 情绪 81–85）

要求：

- 两段必须依次连续出现，且题目区段与标题一一对应
- 每段上方都必须显示标题与提示词
- 题号必须保留为真实全局序号 `seq`（1–85），不得重排
- 每段内部题目必须属于对应分段，不得跨段混排

### 4. 交互约束

- 一次性展示全部 85 道题，不能分页、不能逐题加载
- 题目必须按真实题库区段顺序展示：第一部分 1–30，第二部分 31–85
- 每题必须只有一个有效答案：`A` / `B` / `C` / `D` / `E`
- 用户点击某按钮时，必须只切换该题的选中状态，不应多选；点击同题另一按钮立即切换（互斥）
- 题号 `seq` 与题目一一对应
- 进度条与进度文本依据已答题数/85 自动更新
- 当用户完成全部 85 题后，提交按钮可点击，点击后触发最终计算
- **提交按钮交互状态（关键）**：
  - 未答完 85 题前：提交按钮置灰（disabled），不可点击，文案如 `请完成所有题目后再提交（已答 X/85）`，配色为 `(#E5E7EB` 灰底 / `#4B5563` 深灰字`)`——**disabled 态字色必须为深灰 `#4B5563`，严禁用白字**（白字配灰底会看不见，这是"按钮字体变白消失"的高频原因）。
  - 已答完 85 题后：提交按钮高亮可点击，文案如 `提交并生成能力画像`，配色为 `(#15803D` 深绿底 / `#FFFFFF` 白字`)`——可点态才用白字，且必须配深色底，保证对比度。
  - 按钮状态必须实时响应答题进度，不允许延迟更新
  - **答题进度与提交按钮联动逻辑（关键，必须实现，不得省略）**：进度文本、进度条宽度、提交按钮的 `disabled / 文案 / (背景,字色)` 三者必须由**同一套答题状态**驱动、实时同步，不得各自为政。渲染模型须将下列契约落实为卡片内 `<script>`，**不得只写静态 HTML**（静态写死 `已答 17/85` 或 `disabled` 即视为未实现）：
    ```js
    // 状态：seq(1-85) → 选项编码(A-E)；同题重选覆盖旧值，保证一题一答
    const answered = {};
    function recalc() {
      const count = Object.keys(answered).length;        // 已答题数（0-85）
      const pct = (count / 85 * 100);                     // 进度百分比
      // 1) 进度文本（标题区右侧）
      progressText.textContent = `已答 ${count} / 85`;
      // 2) 进度条宽度：fill 必须有显式 background（与得分条同理，见报告卡§4）
      progressBarFill.style.width = pct + '%';
      // 3) 提交按钮：未答完置灰 disabled，答完高亮可点
      if (count === 85) {
        submitBtn.disabled = false;
        submitBtn.textContent = '提交并生成能力画像';
        submitBtn.style.background = '#15803D';           // 深绿底
        submitBtn.style.color = '#FFFFFF';                // 白字（仅可点态用白字）
      } else {
        submitBtn.disabled = true;
        submitBtn.textContent = `请完成所有题目后再提交（已答 ${count}/85）`;
        submitBtn.style.background = '#E5E7EB';            // 灰底
        submitBtn.style.color = '#4B5563';                // 深灰字（disabled 严禁白字）
      }
    }
    // 每个答题按钮：点击即互斥记录该题选项，随后 recalc() 同步三处
    answerBtn.addEventListener('click', () => {
      answered[seq] = option;      // 同题另一按钮点击会覆盖，天然互斥
      // 同题按钮成对切回灰底深灰字、被选按钮切语义色白字（见 §2）
      recalc();
    });
    // 提交：仅 count===85 时可达，拼 85 位 A-E 紧凑序列提交（见「提交数据格式约束」）
    submitBtn.addEventListener('click', () => {
      if (submitBtn.disabled) return;                    // 双保险，拦截未答完
      const seqStr = Array.from({length: 85}, (_, i) => answered[i + 1]).join('');
      submit(seqStr);                                    // 85 位序列，严禁 JSON
    });
    ```
    - **三处必须由同一次 `recalc()` 同步驱动**：进度文本、进度条宽度、提交按钮状态；任一滞后或不更新即视为未实现。
    - **初始渲染（关键，防静态陷阱）**：页面加载时 `answered = {}`、`count = 0`，提交按钮必须为 **disabled 灰底深灰字**、文案 `请完成所有题目后再提交（已答 0/85）`、进度条宽度 `0%`、进度文本 `已答 0 / 85`。**严禁初始即为可点高亮态、严禁静态写死 `已答 17/85`**（§6 示意中的 `17/85` 仅为结构示例，不是初始值）。
    - **字色与背景成对切换**：提交按钮在 disabled↔可点切换时，`(背景, 字色)` 必须整体成对切（`灰底/深灰字` ↔ `深绿底/白字`），不得只切其一——错位会导致白字配灰底(消失)或深灰字配深绿底(看不清)。
  - **字色与背景成对切换（关键）**：提交按钮从 disabled → 可点时，`(背景, 字色)` 必须整体从 `(灰底, 深灰字)` 切到 `(深绿底, 白字)`，不得只切背景不切字色、或只切字色不切背景——错位会导致白字配灰底(消失)或深灰字配深绿底(看不清)。
- **提交数据格式约束（关键）**：
  - 用户点击提交时，卡片**必须以 85 位紧凑 A-E 字符序列**提交答案（如 `ABCABCABC...`，按 `seq` 1→85 顺序排列，`A`=完全符合 … `E`=完全不符合），**严禁使用 JSON 对象格式**（如 `{"1":"A",...}`）提交。
  - 原因：JSON 格式约 530 字符量级，传输过程中在约 530 字符处被系统截断，导致答案丢失；紧凑序列仅 85 字符，远低于截断阈值，不会丢失。
  - 提交序列长度必须等于 85；不足 85 视为未答完，由提交按钮置灰逻辑拦截。
  - 序列第 i 位对应 `seq=i` 的题（1-based）：第 1 位 = 第 1 题，第 85 位 = 第 85 题，顺序与题库一致，不得错位。
- 交互必须发生在当前对话流的内联组件中，而不是返回普通纯文本

### 5. HTML / Visualizer 输出要求

如果系统支持 WorkBuddy 的 Visualizer / 内联 HTML 渲染，返回内容必须满足：

- 以 HTML 片段或可渲染组件形式输出，而不是纯 Markdown
- 必须保留视觉层结构：标题、引言、进度、分段标题、题目列表、5 级按钮组
- 不能出现散乱的自然语言说明替代卡片
- 不能直接输出仅有 JSON 字段而没有交互容器
- 不能让前端自行“自由发挥”生成不同布局
- 只允许按本 skill 规定的结构渲染，不允许引入无关内容

### 6. 参考示意结构

以下内容仅用于描述结构，不应被当作自由文本输出；真正交互时，应按本 skill 的稳定规则渲染：

```html
<div class="assessment-card">
  <h2>职业能力倾向测评</h2>
  <div class="intro">本测评将帮助你系统发掘自身的天赋潜能与职业通用能力优势……请根据直觉快速作答。</div>
  <div class="progress-row">
    <!-- 初始渲染：宽度 0%、文本「已答 0 / 85」，随答题 recalc() 同步更新（见 §4 联动逻辑） -->
    <div class="progress-bar"><div class="progress-bar-fill" style="width:0%"></div></div>
    <span class="progress-text">已答 0 / 85</span>
  </div>

  <div class="part-title">第一部分 · 天赋能力</div>
  <div class="part-prompt">以下题目评估你的 6 项天赋能力……</div>

  <div class="question-row">
    <div class="question-number">1</div>
    <div class="question-text">我能够用简洁明了的语言，清晰地表达我的观点和思路。</div>
    <div class="answer-options">
      <!-- 5 级按钮组：DOM 从左到右 E→D→C→B→A（配色与交互见 §2）；data-option=选项编码，不按 DOM 位置提交 -->
      <button data-option="E">完全不符合</button>
      <button data-option="D">比较不符合</button>
      <button data-option="C">一般符合</button>
      <button data-option="B">比较符合</button>
      <button data-option="A">完全符合</button>
    </div>
  </div>
  <!-- ... 第 1–30 题为第一部分 ... -->

  <div class="part-title">第二部分 · 通用能力</div>
  <div class="part-prompt">以下题目评估你的 11 项通用能力……</div>
  <!-- ... 第 31–85 题为第二部分 ... -->

  <!-- 初始渲染即 disabled 灰底深灰字、文案「已答 0/85」；随答题 recalc() 同步（见 §4 联动逻辑），静态写死 17/85 视为未实现 -->
  <button class="submit-btn" disabled>请完成所有题目后再提交（已答 0/85）</button>
</div>
```

### 7. 禁止事项

> 按钮配色、互斥、不显示分数等约束已在 **§2** 详述，本节不再重复，仅列 §2 未覆盖项。

- 不允许输出纯文本描述替代卡片
- 不允许缺失 5 级按钮组（必须 5 个按钮，对应 A–E）
- 不允许没有进度条和题号
- 不允许在页面中出现无关长文案或随机推理内容
- 不允许模型自行更换布局结构，必须保持 WorkBuddy 交互卡片的稳定格式
- 不允许把 85 题混排成一大段，必须按 2 部分分段展示

## WorkBuddy 结果报告卡渲染约束（核心执行规范）

用户提交 85 位作答序列、评分脚本返回 JSON 后，必须渲染**结果报告卡**（而非纯文本或裸 JSON）。本节约束报告卡的渲染契约，确保不靠模型临场推断。

### 0. 模块前置与渲染技术（关键，避免临场纠结）

- **渲染前先确认 `interactive` 模块已加载**：若平台通过 `read_me` 机制按需加载渲染模块，结果卡同样走 `interactive` 通道，无需加载 `chart` / `diagram` 等额外模块。
- **得分条与能力卡片用纯 HTML + CSS 渲染**：得分条用 `<div>` + CSS `width: <score>%` 实现，能力卡片用 `<div>` 网格实现。**严禁引入 chart.js / echarts / d3 / 任何外部图表库或 CDN 脚本**——它们会导致聊天窗口高度剧烈跳动且非必需。
- **唯一渲染通道仍为 `show_widget`**：生成 HTML/CSS/JS 后必须且只能传入 `show_widget`；严禁把代码以 Markdown 代码块输出、严禁提供 `.html` 下载。`show_widget` 是平台原生工具，直接发起 `tool_use` 调用即可，**严禁用 `ToolSearch` 去"确认其是否存在"**（检索不到不等于不存在）。仅当调用**被实际发起并返回错误或被拒绝**时，才输出一句话纯文本提示；**绝不退化为独立 HTML、也不退化为纯文本版报告卡或逐条列出分数**。

### 1. 报告卡视觉结构

报告卡为一个内联卡片，自上而下包含：

1. **顶部标题区**：标题 `职业能力画像` + 总分（100 分制）+ 完成状态
2. **上半部分 · Top 5 能力卡片**：5 张能力卡片横向网格排列，每张含维度名、分数（100 分制）、`highScoreDesc` 高分解读文案（**不渲染任何图片**）
3. **并列第 5 补充说明**：若第 5 名存在同分未入选维度（`runnerUp` 非空），在卡片下方补一句"同时，你在 xxx、xxx 能力方面得分也比较高"
4. **下半部分 · 17 维度得分条**：17 条横向得分条，每条 = 维度名（左）+ 得分条（中，宽度按 100 分制分数）+ 分数值（右）
5. 底部辅助说明

### 2. Top 5 能力卡片样式要求

- 5 张卡片用 `grid-template-columns: repeat(auto-fit, minmax(150px, 1fr))` 自适应排列，窄屏自动换行
- 每张卡片结构：维度名（粗体）→ 分数（大字号，100 分制，如 `85`）→ `highScoreDesc` 文案（小字号灰色，**原样取自评分结果 `reportTextList[].highScoreDesc`，不得改写或自由发挥**）
- **不渲染图片**：卡片不显示 `icon` 图片，也不使用 `bgImg` 作底图（外部图床在卡片渲染环境常加载失败导致图片花屏）；卡片背景统一用浅渐变 `linear-gradient(180deg, #f2f8ff, #edf6ff)` 兜底
- 排序：按 `reportTextList` 数组顺序（已降序），Top 1 在最左
- 分数颜色：随分数高低语义渐变（≥80 深绿、60–79 绿、40–59 琥珀、<40 灰），与问卷按钮组语义一致

### 3. 并列第 5 补充说明（关键）

- 取评分结果 `runnerUp` 数组（与第 5 名同分但未入选卡片的维度）
- 若 `runnerUp` 非空，在 Top 5 卡片网格**下方**显示一行说明文案，模板固定：
  `同时，你在 xxx、xxx 能力方面得分也比较高。`
  - `xxx` 用顿号 `、` 连接 `runnerUp[].name`，末尾加 `能力方面得分也比较高。`
  - 示例：`runnerUp` 为 `[商业思维, 情绪控制]` → `同时，你在 商业思维、情绪控制 能力方面得分也比较高。`
- 若 `runnerUp` 为空（第 5 名无并列），不显示该行
- 维度名**原样取自 `runnerUp[].name`**，不得改写

### 4. 17 维度得分条样式要求

- 共 17 条，顺序按评分结果 `details` 数组（固定优先级顺序：语言→写作→数学→空间→动觉→审美→逻辑→研究分析→创新→灵活应变→人际→组织协调→风险→商业→用户洞察→细节→情绪控制）
- 每条结构：`<维度名>` | `<得分条>` | `<分数>`
- 得分条实现：外层 `<div class="bar-track">`（**灰底 `#E5E7EB`**，圆角、固定宽度、高度 10px）+ 内层 `<div class="bar-fill" style="width: <score>%; background: <对应档位色>">`（`width` 取 100 分制 `score` 值，`background` 按下表档位取固定 hex）。**`width` 与 `background` 必须同时写在 `bar-fill` 的 style 内，缺一不可**——只写 `width` 不写 `background` 会导致 `bar-fill` 无填充色（即"得分条没有颜色"的成因）。
- 分数值显示在条右侧，100 分制整数（来自 `details[].score`），满分 100
- **得分条填充色（关键，必须有颜色）**：按 100 分制 `score` 分档取固定 hex 写入 `bar-fill` 的 `background`，不得留空、不得用透明、不得用与灰底 `#E5E7EB` 同色的值（同色会看不见）：

  | score 区间 | background 取值 | 语义 |
  |---|---|---|
  | ≥80 | `#15803D` 深绿 | 优势突出 |
  | 60–79 | `#22C55E` 绿 | 较强 |
  | 40–59 | `#F59E0B` 琥珀 | 中等 |
  | <40 | `#9CA3AF` 中灰 | 偏弱 |

  - `bar-fill` 的 style **必须显式包含 `background`** 字段（值取上表对应色）；严禁省略 `background`——省略时 `bar-fill` 继承父级灰底或透明，导致得分条看起来无颜色。
  - `width:0%`（score=0）时 bar-fill 宽度为 0、无可视色块属正常，但 `background` 仍须按 <40 档设为 `#9CA3AF`，不得留空。
- 17 条等高、左对齐、条之间留浅间距，不得错位

### 5. 参考示意结构

以下仅描述结构，真正交互时按本 skill 规则渲染：

```html
<div class="result-card">
  <h2>职业能力画像</h2>
  <div class="total">综合能力得分：49 / 100</div>

  <!-- 上半：Top 5 能力卡片（reportTextList，不渲染图片） -->
  <div class="ability-cards">
    <div class="ability-card">
      <div class="ability-name">动觉能力</div>
      <div class="ability-score">70</div>
      <div class="ability-desc">你的肢体协调能力较强，动作敏捷、反应迅速……</div>
    </div>
    <!-- ... 其余 4 张，顺序按 reportTextList ... -->
  </div>

  <!-- 并列第 5 补充说明（runnerUp 非空时显示） -->
  <div class="runner-up">同时，你在 商业思维、情绪控制 能力方面得分也比较高。</div>

  <!-- 下半：17 维度得分条（details） -->
  <div class="score-bars">
    <div class="bar-row">
      <span class="bar-label">动觉能力</span>
      <!-- bar-fill 的 style 必须同时含 width 和 background（见§4），只写 width 不写 background 会无色 -->
      <div class="bar-track"><div class="bar-fill" style="width:70%; background:#22C55E"></div></div>
      <span class="bar-value">70</span>
    </div>
    <!-- ... 其余 16 条，顺序按 details ... -->
  </div>
</div>
```

### 6. 数据来源映射（关键，禁止自由发挥）

| 报告卡区域 | 数据字段 | 来源 |
|---|---|---|
| Top 5 卡片 | 维度名 / 分数 / 解读 | `reportTextList[].name/score/highScoreDesc`（**不含 icon/bgImg**） |
| 并列第 5 说明 | 维度名列表 | `runnerUp[].name`（非空时显示） |
| 得分条 | 维度名 / 分数 / 宽度 | `details[].name/score`（`width = score%`） |
| 总分 | 综合能力得分 | `totalScore` / `maxTotalScore` |

- 所有文案**必须原样取自评分脚本输出**，不得由模型改写、缩写、扩写 `highScoreDesc`
- 得分条宽度必须等于 `details[].score`（0–100），不得用原始分或自行估算
- Top 5 必须等于 `reportTextList` 全部 5 项，不得增删
- 并列第 5 说明的维度名必须等于 `runnerUp[].name`，不得自行增删或改写

### 7. 禁止事项

- 不允许用纯文本或裸 JSON 替代报告卡
- 不允许引入 chart.js / echarts / d3 或任何外部图表库/CDN
- 不允许得分条用 canvas / svg 复杂绘制（用纯 CSS `width` 即可）
- 不允许改写 `highScoreDesc` 文案
- 不允许 Top 5 卡片数量不为 5
- 不允许得分条数量不为 17
- 不允许用原始分（0–40）显示，必须 100 分制
- 不允许 `show_widget` 失败时退化为独立 HTML 文件
- 不允许在能力卡片中渲染图片（`icon`/`bgImg`），避免图床加载失败导致花屏

## 题目结构说明

题库 `references/questions.json` 顶层结构：

```json
{
  "assessment_id": "CAREER-ABILITY-85-001",
  "question_total": 85,
  "dimension_count": 17,
  "answer_options": [ { "option": "A", "label": "完全符合", "score": 8 }, ... ],
  "questionConfig": {
    "title": "职业能力倾向测评",
    "desc": "（引言，原样展示）",
    "partList": [
      { "id": 1, "name": "天赋能力", "title": "第一部分",
        "dimensionList": [ { "id": 10000, "name": "语言能力", "sort": 16,
          "icon": "...", "bgImg": "...", "desc": "...", "highScoreDesc": "...",
          "questionList": [ { "seq": 1, "id": "<uuid>", "stem": "..." }, ... ] } ] }
    ]
  }
}
```

- 每题含 `seq`（全局序号 1–85，紧凑提交序列按此对齐）、`id`（题库 UUID，结果回溯用）、`stem`（题干，原样展示）
- 每维度含 `desc`（维度定义，参考用）、`highScoreDesc`（高分解读文案，结果卡用）、`icon`/`bgImg`（题库保留，但结果卡不渲染图片，避免图床花屏）
- 5 级选项与计分定义在顶层 `answer_options`，所有维度共用，无需每维重复

### 题目示例

```json
{
  "seq": 1,
  "id": "1d9881deec644f698d7c3445f5b68007",
  "stem": "我能够用简洁明了的语言，清晰地表达我的观点和思路。",
  "answer_type": "five_level_agree"
}
```

## 提交数据格式

问卷提交时输出 **85 位 A-E 紧凑字符序列**，按 `seq` 1→85 顺序排列：

```
ABCABCABCABCABCABCABCABCABCAB C ... (共 85 位)
```

- 每位取值：`A` 完全符合 / `B` 比较符合 / `C` 一般符合 / `D` 比较不符合 / `E` 完全不符合
- 长度必须 = 85；不足 85 视为未答完，由提交按钮置灰逻辑拦截
- 严禁 JSON 对象格式提交（约 530 字符会被截断，85 字符安全）

> 该序列即评分脚本 `calculate_scores.py` 的输入。

## 评分入口

评分脚本位置：

- `career-ability-assessment/scripts/calculate_scores.py`
- 评分函数：`calculate_scores`
- 输入：85 位 A-E 紧凑序列（或兼容 JSON 对象）
- 输出：JSON 格式的 17 维度分数、降序排名、Top N 优势维度预览、总分、完成状态

示例命令：

```bash
# 推荐：紧凑序列（85 位 A-E 字符串，约 85 字符，不触发传输截断）
python career-ability-assessment/scripts/calculate_scores.py \
  --answers 'ABCABCABCABCABCABCABCABCABCABCABCABCABCABCABCABCABCABCABCABCABCABCABCABCABCABCABCABCABCABCABCABCABCA'

# 指定 Top N 优势维度数量（默认 5，报告页能力卡片数）
python career-ability-assessment/scripts/calculate_scores.py --answers 'ABCAB...' --top-n 5

# 兼容：旧 JSON 对象格式（约 530 字符，不推荐，存在被截断风险）
python career-ability-assessment/scripts/calculate_scores.py \
  --answers '{"1":"A","2":"B","3":"C","4":"D","5":"E"}'
```

## 评分规则

### 1. 维度分数

每题对应一个能力维度（题库 `dimensionList` 标注），用户作答 A–E 按正向计分累加到对应维度：

| 选项 | 标签 | 分数 |
|---|---|---|
| A | 完全符合 | 8 |
| B | 比较符合 | 6 |
| C | 一般符合 | 4 |
| D | 比较不符合 | 2 |
| E | 完全不符合 | 0 |

```
score[dimension] = sum(answer_score for question in dimension if answered)
```

- 每维度 5 题，维度得分范围 0–40
- 17 个维度各自独立计分

### 2. 结果排序

按维度分数降序排列，取 **Top 5** 优势维度（报告页上半部分能力卡片）；分数相同按维度固定优先级（题库 `partList→dimensionList` 插入顺序）取靠前者，确保确定性。Top N 可由 `--top-n` 参数调整（默认 5）。

### 3. 分数换算

40 分制原始分换算为 100 分制显示分（报告页得分条与卡片分数均用 100 分制）。计分映射为 8/6/4/2/0 均为偶数，每维 5 题原始分必为偶数，换算恒为整数，**无需四舍五入**：

```text
score100   = rawScore * 100 / 40   # = rawScore * 2.5（偶数×2.5 必为整数）
totalScore = totalRaw * 100 / 680   # 总分：满分 680 → 100
```

### 4. 报告输出

评分脚本输出 JSON，结构对齐前端报告页（上半 Top5 能力卡片 + 下半 17 维得分条）：

```json
{
  "assessment_id": "CAREER-ABILITY-85-001",
  "status": "completed",
  "answered_count": 85,
  "total_questions": 85,
  "dimension_count": 17,
  "totalScore": 49,
  "maxTotalScore": 100,
  "top_n": 5,
  "details": [
    { "id": 10000, "name": "语言能力", "sort": 16, "score": 65, "rawScore": 26, "maxScore": 100 }
  ],
  "ranked_dimensions": [
    { "id": 10004, "name": "动觉能力", "sort": 2, "score": 70 }
  ],
  "top_dimensions": [
    { "id": 10004, "name": "动觉能力", "sort": 2, "score": 70 }
  ],
  "reportTextList": [
    {
      "id": 10004,
      "name": "动觉能力",
      "score": 70,
      "highScoreDesc": "你的肢体协调能力较强，动作敏捷、反应迅速……"
    }
  ],
  "runnerUp": [
    { "id": 20007, "name": "商业思维", "score": 60 },
    { "id": 20010, "name": "情绪控制", "score": 60 }
  ],
  "qrCodePath": "pages/career-ability/index"
}
```

- `totalScore`：100 分制总分（满分 100）；`details` 各项 `score` 亦为 100 分制（满分 100），`rawScore` 为 40 分制原始分（保留校验用）
- `details`：17 维得分，按固定优先级顺序排列（报告页下半部分得分条数据源）
- `ranked_dimensions`：17 维按分数降序，分数相同按固定优先级取靠前者
- `top_dimensions`：Top 5 优势维度
- `reportTextList`：Top 5 能力卡片数据源（报告页上半部分），每项含 `name`/`score`/`highScoreDesc`（**不含 icon/bgImg**，卡片不渲染图片避免图床花屏），文案取自题库预定义，不允许自由发挥
- `runnerUp`：与第 5 名同分但未入选卡片的维度数组（并列第 5）；非空时报告卡在 Top 5 下方补"同时，你在 xxx、xxx 能力方面得分也比较高"，`xxx` 取 `runnerUp[].name`；为空则不显示
- `qrCodePath`：固定跳转路径
- 若 `status == incomplete`，输出 `missing_questions` 列出缺失题号
- 输出必须为纯 JSON，确定性（同输入→同输出），不允许模型自由发挥文案

## 重要原则

- 题库必须明确给出 `seq`、`id`、`stem`、维度归属；题干原样展示不得改写
- 问卷渲染逻辑写在 `show_widget` 内联卡片中，评分逻辑单独写在脚本文件，不能隐含在对话里
- 用户提交 85 位序列后，返回 17 维度分数（100 分制）、降序排名、Top 5 优势能力卡片、并列第 5 补充说明、各维度得分条
- 若作答不完整或格式不合法，先要求用户补全，不要伪造结果
- 题目与维度一一映射，维度 `id`/`sort`/`desc`/`highScoreDesc` 保留；`icon`/`bgImg` 题库保留但结果卡不渲染（避免图床花屏）

## Demo 目录结构

```text
career-ability-assessment/
├── SKILL.md
├── references/
│   ├── algorithm.md
│   └── questions.json
└── scripts/
    └── calculate_scores.py
```

## 资源说明

- 题库参考：`references/questions.json`
- 算法说明：`references/algorithm.md`
- 评分脚本：`scripts/calculate_scores.py`

## 交互输出要求

用户完成题目并提交 85 位序列后，系统应返回：

1. 测评 ID
2. 测评标题
3. 17 个维度分数（`details`，固定优先级顺序）
4. Top 优势维度排序（`ranked_dimensions` / `top_dimensions`）
5. 优势维度的能力解读（`reportTextList` 中的 `highScoreDesc`）
6. 若未完成，给出缺失题号（`missing_questions`）
