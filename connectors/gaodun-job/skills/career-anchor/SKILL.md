---
name: career-anchor
display_name: 职业锚测评
display_name_en: Career Anchor Assessment
description: 当用户提到职业价值观、职业锚、工作长期发展取向时调用本Skill，用于识别其核心职业价值取向并解读测评结果。
description_zh: 评估技术职能、管理、自主独立、安全稳定、创业创造等职业价值取向，并输出职业锚类型解读。
description_en: Use when users mention career anchors, work values, or long-term development orientations to identify core career values.
category: 15-Education
version: 2.1.0
author: Gaodun
---

# 职业锚测评 Skill

## Overview

生成职业锚测评题目并计算结果，覆盖 8 个维度：

- TF：技术职能型
- GM：管理型
- AU：自主型
- SE：安全型
- EC：创造型
- SV：服务型
- CH：挑战型
- LS：生活型

本测评共 40 题，每题评分 1-6 分，每个维度均匀分布 5 道题目。最终结果为得分最高的前三个维度组合（如 TF+GM+AU）。

## When to Use This Skill

在以下场景触发本 skill：

- 用户明确说出"测职业锚""做职业锚测试""帮我测一下职业锚""启动职业锚测评"这类完整指令
- 用户直接询问"我是什么职业锚""生成我的职业锚报告""帮我算我的职业锚类型"
- 用户主动提及"打开职业锚测评工具""开始职业锚测评"
- 用户说"我要做职业倾向测试，指定是职业锚的""我想测职业锚的完整维度"
- 用户历史对话3轮内明确提过要做职业锚测评，当前轮次说"继续""开始吧""下一步"
- 用户直接发送"职业锚测评""职业锚测试"作为唯一指令，无其他无关内容

在以下场景需要二次确认后才触发职业锚测评 Skill（命中后先弹出确认话术，用户同意再启动）：

- 用户只单独发送"职业锚"三个字，没有后续补充任何内容
- 用户讨论某类职业锚特征后，说"我好像就是这种人""我感觉我符合这个类型"
- 用户说"我想了解自己的职业倾向""帮我做个职业测试"，没有明确指定是职业锚
- 用户说"我想看看我的职业价值观是什么样的""分析一下我的职业倾向"，没有限定测评类型
- 用户提到"我朋友说我是XX型职业锚，想验证一下"，没有直接说要启动测评
- 用户在讨论职业锚相关话题后，说"帮我测测看"，没有明确指向其他测评工具
- 用户说"我想做个测试看看我适合什么职业锚类型"，表述模糊未直接唤起测评

## When NOT to Use This Skill

以下场景**不触发**本 skill：

- 用户仅询问职业锚基础科普："职业锚有多少种类型""职业锚的八个维度是什么""职业锚的起源是什么"
- 用户仅查询某类职业锚的特征："技术职能型的特点是什么""管理型适合什么职业""自主型的优缺点"
- 用户讨论职业锚的非测评应用场景："职业锚面试技巧""用职业锚做职业规划""职业锚职场应用"
- 用户在讨论其他完全无关的话题时，偶然提到职业锚："我昨天和朋友聊到职业锚""我同事是管理型"
- 用户明确要求其他类型的测试："我要做MBTI测试""帮我测霍兰德职业兴趣""生成九型人格测试"
- 用户的需求是内容生成类："帮我写一篇职业锚主题的小红书文案""生成职业锚相关的短视频脚本"
- 用户同时提出多个混合需求，且没有明确表示要做测评："帮我查职业锚类型，再写一份职业规划方案"
- 用户明确表示"我不想做测评""我只是想了解职业锚的知识"，直接拦截所有测评唤起

## 题目元数据

```yaml
assessment_id: CAREER-ANCHOR-40-001
assessment_name: "职业锚测评"
question_total: 40
dimension_count: 8   # TF/GM/AU/SE/EC/SV/CH/LS
dimension_distribution: 每个维度5题
result_dimensions: 3  # 取得分最高的前三个维度
references_path: "references/questions.md"
algorithm_path: "references/algorithm.md"
score_calculation_path: "scripts/calculate_career_anchor.py"
score_function: "calculate_scores"
entrypoint: "python scripts/calculate_career_anchor.py --answers '{\"1\":5,\"2\":4}'"
card_spec: "内嵌于本文件 §0（答题卡片渲染规范，含完整代码块）"
report_spec: "内嵌于本文件 §R（报告渲染规范，含完整代码块）"
```

## references 数据文件结构

测评数据（题库 / 8 维度详情）以 **2 个 H2 段** 组织，每段必须包含一段散文说明 + 一个 ```json 代码块，段顺序固定如下（**H2 标题改名会破坏脚本解析，禁止改名**）：

1. `## 题库` → 40 题题库数组
2. `## 维度详情` → 8 维度详情数组

**文件形态**：
- `references/questions.md`（含 `## 题库`）
- `references/dimensions.md`（含 `## 维度详情`）
- 每个文件内**仍必须保留对应的 H2 标题与 ```json 代码块**（解析锚点不变）

## 题目加载硬约束（关键）

1. 本 skill **仅有唯一测评流程**：展示 40 题 → 用户作答 → 输出完整测评报告。不存在其他题数或版本，不询问用户"要做多少题"、不提供任何"版本二选一"入口。
2. 触发测评后必须直接展示全部 40 题进入答题流程，不得插入任何"选择题目数量""选择版本"的中间步骤。
3. 题目必须从 `references/questions.md` 文件中读取 `questions` 数组，按 `questionIndex` 1→40 原序展示；**禁止模型自行编造或凭印象生成题目**。
4. 题库共 40 题，每题必须包含 `questionIndex` / `questionText` / `dimensionCode` / `dimensionName` 四要素，渲染时不得遗漏任一字段。
5. 若题库读取失败或不足 40 题，必须直接报错说明，不得用"部分题目"凑数、不得用模型自拟题补齐。
6. 一次性展示全部 40 道题，不得分页、不得"先展示前几题"、不得逐题加载。

### 题目数据加载流程

模型在渲染交互卡片前，**必须先读取题库文件**，不得凭训练数据回忆题目：

1. 通过 Read 工具读取题库文件 `references/questions.md`，解析其 ```json 代码块为数组。
2. 按数组顺序（questionIndex 1→40）渲染全部 40 题，不得打乱、不得省略、不得改写题干/维度归属；**渲染动作必须遵循"题目卡片渲染规范"（§0 内联约束），禁止自绘样式**。
3. 若 Read 工具调用失败、返回内容不足 40 题、或解析报错，模型**必须**向用户返回明确的错误提示（如"题库文件读取失败，请检查 references/questions.md 文件是否存在且包含 40 题"），**不得**：
   - 用模型自拟/凭印象/从训练数据回忆的题目补齐
   - 用"部分题目"凑数渲染卡片
   - 返回空卡片或不做任何响应
   - 静默跳过题目渲染只输出其他元素（标题、进度条、维度标签等）

## 工作流程

本 skill 只有一条流程：**展示 40 题 → 用户在卡片内作答 → 点击"提交测评" → 模型直接输出完整测评报告**。具体步骤：

1. 渲染完整交互卡片展示全部 40 题（按 §0 规范渲染），用户在卡片内完成作答（每题评分 1-6 分）。
2. 用户点击"提交测评"时：
   - 存在未作答题目 → 卡片内自动滚动到第一个未答题并高亮提示，**不提交、不出报告**；
   - 已答完全部 40 题 → 卡片内 JS 通过宿主回传机制（`sendPrompt()`）将答案 JSON 自动作为用户消息发送。
3. 模型收到答案后对答案进行校验，确保题目编号、答案值（1-6）正确。
4. 调用评分脚本计算 8 个维度得分 + 排序 + 取前三个维度。
5. **直接**返回用户完整测评报告（按 §R 规范渲染）：报告头部（标签/主标题/副标题）→ 职业价值观类型（前三类型名称用 `+` 连接）→ 八维度雷达图 → 前三职业锚类型详解。

**强制约束（不允许有其他链路）**：用户点击"提交测评"且答完全部题目后，模型必须**直接输出完整测评报告**。禁止以下任何行为：要求用户复制/粘贴答案回传、要求用户手动输入答案、先输出答案 JSON 等待用户确认、把出报告推迟到用户再次追问之后、以任何形式要求用户参与答案传递。

## WorkBuddy 视觉化交互卡片约束（关键）

本 skill 在 Workbody / WorkBuddy 场景下，不仅需要返回结构化 JSON，也必须支持可视化内联交互卡片：即在对话中直接渲染一个 HTML/CSS/JS 组件，模拟真实测评页面，且在聊天窗口中保持稳定的视觉结构。

### 渲染总则（所有渲染的最高约束，必须遵守）

本 skill **不依赖任何外部模板文件**，样式与结构以**本文件内嵌的规范代码块**为唯一来源。渲染时必须遵守：

1. **代码块即规范**：§0（答题卡片）与 §R（报告）下方给出的完整代码块（骨架 + `<style>` + `<script>`）是**唯一允许的输出形式**。渲染时从本文件逐字复制这些代码块，**只替换其中唯一的数据占位符**（`__QUESTIONS__` / `__REPORT__`），其余字符（含空格、换行、缩进、类名、色值）一律不得改动。
2. **禁止凭记忆渲染**：每次渲染前必须**重新读取本文件对应章节**的代码块，禁止凭训练数据或上一次输出的印象"复述"样式；即使同一会话内第二次渲染（如"重新作答"），也必须重新复制同一份代码块，保证与第一次**逐字节一致**。
3. **禁止自绘样式**：禁止重新设计布局、更换类名/色值/字号、增删 DOM 结构、追加额外样式或脚本；任何"看起来差不多"的自定义输出都是违规。
4. **禁止静态化坐标**：雷达图坐标一律由代码块内 JS 用 `Math.cos/Math.sin` 在浏览器端精确计算，模型**禁止**预计算、硬编码、手算任何 SVG 坐标值。
5. **失败处理**：若本文件 §0/§R 代码块缺失或占位符不存在，必须报错检查，不得自绘卡片/报告凑数。
6. **输出通道硬约束（关键）**：题目卡片与测评报告**必须**通过 Visualizer（show_widget）以 `widget_code` 形式在对话中内联渲染，**禁止生成本地 HTML 文件**（含 outputs 目录、临时目录等任何落盘路径），禁止用文件路径或"打开本地页面"方式替代内联渲染；若 show_widget 等渲染工具不可用，**必须向用户明确报错并等待环境支持或用户确认**，不得自行降级为文件输出，不得自绘样式凑数。

### 派生请求禁止走捷径（关键，最常见违规）

用户提出**派生请求**时（典型话术："再来一份""朋友也要测""给同事也来一套""试试换个 UI""重置再来一遍""换个颜色/风格"），模型必须：

1. 一律重新 `Read` 数据源文件（`references/questions.md` 题库、`references/dimensions.md` 维度详情），并**重新从本文件 §0 / §R 逐字复制对应代码块**，完整走标准渲染流程（§0 答题卡片 / §R 报告，含重新跑评分脚本）；不得依赖上一轮的输出或记忆印象。
2. **禁止"拷贝+改名"充当新产物**：不允许把"上一次的卡片/报告"复制过来仅改 ID 后缀（如 `-friend` / `-v2`）、改类名、改标题、换人名/昵称就当作新测评输出；任何复用上一轮 DOM/样式/文案的"派生粘贴"行为一律视为违规。
3. 新卡片/报告必须是 `references/questions.md` + 本文件 §0/§R 代码块的 **byte-stable 实例**：所有 ID（如 `anchor-card` / `anchor-list` / `anchor-rpt` / `rType` / `rRadar` / `rDims`）、class、style、文案（标题、副标题、按钮、提示语、维度名称）与首次测评输出保持**逐字符一致**；同一会话内多次测评，唯一允许变化的只有数据占位符（`__QUESTIONS__` / `__REPORT__`）内的实际数据。
4. "试试换个 UI""换个样式"类请求**一律拒绝样式变更**：本 skill 样式唯一来源是 §0/§R 内嵌代码块，不存在"换 UI"选项；用户只能重新作答获取新结果，渲染样式必须与首发完全一致（数据可不同，外观必须相同）。

### 0. 题目卡片渲染规范（内联约束，强制）

**渲染流程（强制）**：

1. Read 题库 `references/questions.md`，取出其中 ```json 代码块内的 40 题 JSON 数组**原文**（含首尾方括号 `[` `]`）；
2. 从**本文件本小节下方**逐字复制三部分代码（HTML 骨架 → `<style>` → `<script>`），拼接为完整交互组件；
3. 将 `<script>` 中**唯一占位符** `__QUESTIONS__` 替换为步骤 1 的题库数组原文；**除该占位符外，其余内容必须逐字节照抄，禁止改动任何字符**；
4. 将拼接替换完成的完整内容作为交互组件（Visualizer show_widget）的 `widget_code` 输出。

**代码块 1/3 —— HTML 骨架（逐字复制）**：

```html
<div id="anchor-card">
  <div class="q-head">
    <h2 class="q-title">职业锚测评</h2>
    <span class="q-count">0 / 40</span>
  </div>
  <p class="q-sub">共 40 题，请根据真实感受从 1-6 中选择一个数字</p>
  <div class="q-track"><i></i></div>
  <div id="anchor-list"></div>
  <div class="q-foot">
    <span class="q-tip"></span>
    <button type="button" class="q-submit">提交测评 ↗</button>
  </div>
</div>
```

**代码块 2/3 —— 样式（逐字复制到 `<style>` 标签内）**：

```css
#anchor-card{font-family:var(--font-sans);color:var(--color-text-primary);max-width:680px;margin:0 auto}
#anchor-card .q-head{display:flex;justify-content:space-between;align-items:baseline;gap:12px;flex-wrap:wrap;margin-bottom:2px}
#anchor-card .q-title{font-size:18px;font-weight:500;margin:0}
#anchor-card .q-sub{font-size:13px;color:var(--color-text-secondary);margin:2px 0 12px}
#anchor-card .q-count{font-size:13px;font-weight:500;color:var(--color-text-secondary)}
#anchor-card .q-track{height:6px;border-radius:999px;background:var(--color-background-secondary);overflow:hidden;margin-bottom:16px}
#anchor-card .q-track i{display:block;height:100%;width:0;border-radius:999px;background:var(--color-text-info);transition:width .2s}
#anchor-card .q-item{background:var(--color-background-primary);border:0.5px solid var(--color-border-tertiary);border-radius:var(--border-radius-lg);padding:14px 18px;margin-top:12px;scroll-margin-top:12px}
#anchor-card .q-item.miss{border-color:var(--color-text-danger);box-shadow:0 0 0 1px var(--color-text-danger)}
#anchor-card .q-top{display:flex;gap:10px;align-items:flex-start}
#anchor-card .q-num{flex:none;min-width:28px;height:28px;border-radius:999px;background:var(--color-background-secondary);color:var(--color-text-secondary);font-size:13px;font-weight:500;display:flex;align-items:center;justify-content:center;margin-top:1px}
#anchor-card .q-body{flex:1;min-width:0}
#anchor-card .q-text{font-size:14px;font-weight:500;line-height:1.6;margin:0}
#anchor-card .q-dim{font-size:12px;color:var(--color-text-tertiary);line-height:1.5;margin:6px 0 10px}
#anchor-card .q-opts{display:grid;grid-template-columns:repeat(6,1fr);gap:8px}
#anchor-card .q-opt{font-family:inherit;font-size:13px;font-weight:500;line-height:1;text-align:center;padding:10px 8px;border-radius:var(--border-radius-md);cursor:pointer;background:#F5F6F8;border:1px solid #E5E7EB;color:#3A3F47;transition:background .15s,border-color .15s,color .15s}
#anchor-card .q-opt:hover{border-color:var(--color-border-secondary)}
#anchor-card .q-opt.on{background:#E8F1FF;border:1px solid #4E8CFF;color:#1E4FB8;box-shadow:inset 0 -2px 0 #4E8CFF}
#anchor-card .q-foot{display:flex;align-items:center;justify-content:center;gap:12px;margin-top:18px;flex-wrap:wrap}
#anchor-card .q-tip{font-size:13px;color:var(--color-text-danger);display:none}
#anchor-card .q-submit{font-family:inherit;font-size:14px;font-weight:500;padding:10px 24px;border-radius:var(--border-radius-md);cursor:pointer;background:#4E8CFF;color:#FFFFFF;border:1px solid #4E8CFF;transition:background .15s}
#anchor-card .q-submit:hover{background:#3A78E0}
@media (max-width:560px){#anchor-card .q-opts{grid-template-columns:repeat(3,1fr)}}
```

**代码块 3/3 —— 交互脚本（逐字复制到 `<script>` 标签内，仅替换 `__QUESTIONS__`）**：

```html
<script>
(function(){
  var QUESTIONS = __QUESTIONS__;
  var total = QUESTIONS.length;
  var answers = {};
  var list = document.getElementById('anchor-list');
  list.innerHTML = QUESTIONS.map(function(q){
    var opts = [1,2,3,4,5,6].map(function(v){
      return '<button type="button" class="q-opt" data-v="'+v+'">'+v+'</button>';
    }).join('');
    return '<div class="q-item" data-i="'+q.questionIndex+'">'
      + '<div class="q-top"><span class="q-num">'+q.questionIndex+'</span>'
      + '<div class="q-body"><p class="q-text">'+q.questionText+'</p>'
      + '<p class="q-dim">'+q.dimensionName+'</p>'
      + '<div class="q-opts">'+opts+'</div></div></div></div>';
  }).join('');
  var countEl = document.querySelector('#anchor-card .q-count');
  var trackEl = document.querySelector('#anchor-card .q-track i');
  var tipEl = document.querySelector('#anchor-card .q-tip');
  var submitEl = document.querySelector('#anchor-card .q-submit');
  function refresh(){
    var n = Object.keys(answers).length;
    countEl.textContent = n + ' / ' + total;
    trackEl.style.width = (n / total * 100) + '%';
  }
  list.addEventListener('click', function(e){
    var btn = e.target.closest ? e.target.closest('.q-opt') : null;
    if(!btn) return;
    var item = btn.closest('.q-item');
    var idx = item.getAttribute('data-i');
    var opts = item.querySelectorAll('.q-opt');
    for(var j = 0; j < opts.length; j++){ opts[j].classList.remove('on'); }
    btn.classList.add('on');
    answers[idx] = parseInt(btn.getAttribute('data-v'), 10);
    refresh();
  });
  submitEl.addEventListener('click', function(){
    var miss = [];
    for(var i = 1; i <= total; i++){
      if(answers[String(i)] === undefined){ miss.push(i); }
    }
    if(miss.length){
      var first = miss[0];
      tipEl.textContent = '还有 ' + miss.length + ' 题未作答，请先完成第 ' + first + ' 题';
      tipEl.style.display = 'block';
      var target = list.querySelector('.q-item[data-i="'+first+'"]');
      if(target){
        target.classList.add('miss');
        target.scrollIntoView({behavior:'smooth', block:'center'});
        setTimeout(function(){ target.classList.remove('miss'); }, 1600);
      }
      return;
    }
    tipEl.style.display = 'none';
    if(window.sendPrompt){
      window.sendPrompt('[职业锚测评提交] 我的答案如下：' + JSON.stringify(answers));
    }
  });
})();
</script>
```

**代码块已内置的行为（验收标准，禁止另行实现或修改）**：
- 顶部标题 `职业锚测评`、副标题 `共 40 题，请根据真实感受从 1-6 中选择一个数字`、右侧进度文本 `已答 / 40`、进度条；
- 40 题全量连续展示，每题左侧顺序编号（questionIndex 1→40）+ 题干 + 维度名称 + 六个评分按钮 `1` / `2` / `3` / `4` / `5` / `6`；
- 点击评分：同题六个按钮互斥选中；选中态固定色值（未选中浅灰 `#F5F6F8`/`#E5E7EB`/`#3A3F47`，选中淡蓝 `#E8F1FF`/`#4E8CFF`/`#1E4FB8`）；进度文本与进度条实时更新；
- 提交按钮文案固定 `提交测评 ↗`，**始终可见可点**（禁止延迟出现、禁止 disabled）：存在未作答 → 给第一个未答题加高亮并 `scrollIntoView` 滚动定位，提示"还有 N 题未作答，请先完成第 X 题"，约 1.6s 后移除高亮；已答完 → 调用 `sendPrompt('[职业锚测评提交] 我的答案如下：' + JSON.stringify(answers))` 回传（key 为 questionIndex 1→40，value 为 1-6）。

**禁止事项**：
- 禁止自绘题目卡片、禁止改写代码块中任何字符、禁止更换类名/色值/布局、禁止在代码块外追加任何样式或脚本；
- 禁止分页/逐题加载/打乱题序/省略题目/改写题干；
- 禁止用纯文本或 Markdown 替代交互卡片；
- 若题库读取失败或本文件代码块缺失，必须明确报错，不得用自拟题/部分题凑数；
- **禁止生成本地 HTML 文件**（任何落盘路径）或用文件形式替代内联交互卡片；show_widget 不可用时必须报错并等待环境支持，不得自行降级；
- 禁止派生请求走捷径（"再来一份""朋友也要测""给同事也来一套""试试换个 UI""重置再来一遍"）：必须重新 Read 题库 + 重新复制本小节代码块输出，禁止复制上一张卡片改 ID 后缀（如 `-friend` / `-v2`）充当新产物，新卡片必须与首发逐字符一致（见"派生请求禁止走捷径"小节）。

## 输出格式

### 报告渲染规范（内联约束，强制）

**渲染流程（强制）**：

1. 调用评分脚本 `python scripts/calculate_career_anchor.py --answers '<答案 JSON>'`，获取纯 JSON 计算结果（脚本输出为 byte-equal 确定性 JSON，含 `dimension_scores` / `top_three_dimensions` / `anchor_type` 等全部字段）；
2. 从**本文件本小节下方**逐字复制三部分代码（HTML 骨架 → `<style>` → `<script>`），拼接为完整报告组件；
3. 将 `<script>` 中**唯一占位符** `__REPORT__` 替换为步骤 1 脚本输出的 JSON 对象**原文**（含首尾花括号 `{` `}`）；**除该占位符外，其余内容必须逐字节照抄，禁止改动任何字符**；
4. 将拼接替换完成的完整内容作为交互组件（Visualizer show_widget）的 `widget_code` 输出。

**代码块 1/3 —— HTML 骨架（逐字复制）**：

```html
<div id="anchor-rpt">
  <div class="r-hdr">
    <p class="r-tag">职业锚测评</p>
    <h2 class="r-title">职业锚测评报告</h2>
    <p class="r-sub">你的职业价值观类型</p>
    <span class="r-line"></span>
  </div>
  <div class="r-type-row" id="rType"></div>
  <div class="r-radar" id="rRadar"></div>
  <div id="rDims"></div>
</div>
```

**代码块 2/3 —— 样式（逐字复制到 `<style>` 标签内）**：

```css
#anchor-rpt{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;color:#222;max-width:680px;margin:0 auto;background:transparent}
#anchor-rpt .r-hdr{padding:6px 0 14px;text-align:left}
#anchor-rpt .r-tag{font-size:12px;font-weight:500;letter-spacing:2px;color:#3B6D11;opacity:.6;margin:0}
#anchor-rpt .r-title{font-size:28px;font-weight:700;letter-spacing:4px;color:#3B6D11;margin:6px 0 0}
#anchor-rpt .r-sub{font-size:14px;color:#3B6D11;margin:8px 0 0}
#anchor-rpt .r-line{display:block;width:56px;height:2px;background:#3B6D11;opacity:.5;margin-top:12px;border:0}
#anchor-rpt .r-type-row{font-size:34px;font-weight:700;letter-spacing:1px;color:#3B6D11;text-align:left;margin:20px 0 4px;line-height:1.3}
#anchor-rpt .r-type-row .r-plus{color:#3B6D11;opacity:.4;font-weight:400;margin:0 6px}
#anchor-rpt .r-radar{background:transparent;padding:10px 0;margin-top:8px}
#anchor-rpt .r-radar svg{display:block;width:100%;max-width:420px;height:auto;margin:0 auto}
#anchor-rpt .r-radar .r-grid{stroke:#3B6D11;stroke-opacity:.18;stroke-width:1;fill:none}
#anchor-rpt .r-radar .r-axis{stroke:#3B6D11;stroke-opacity:.35;stroke-width:1}
#anchor-rpt .r-radar .r-poly{fill:rgba(59,109,17,.12);stroke:#3B6D11;stroke-width:2;stroke-linejoin:round}
#anchor-rpt .r-radar .r-pt{fill:#3B6D11}
#anchor-rpt .r-radar .r-pt.win{fill:#EF4444}
#anchor-rpt .r-radar text{font-family:inherit}
#anchor-rpt .r-radar .r-lb{font-size:11px;font-weight:600;fill:#3B6D11}
#anchor-rpt .r-dim{padding:14px 0;margin:0}
#anchor-rpt .r-dim+.r-dim{border-top:1px solid rgba(59,109,17,.25)}
#anchor-rpt .r-dn{font-size:15px;font-weight:600;color:#3B6D11;margin:0 0 6px}
#anchor-rpt .r-desc{font-size:13px;line-height:1.7;color:#222}
```

**代码块 3/3 —— 报告渲染脚本（逐字复制到 `<script>` 标签内，仅替换 `__REPORT__`）**：

```html
<script>
(function(){
  var REPORT = __REPORT__;
  var ORDER = ['TF','GM','AU','SE','EC','SV','CH','LS'];
  var NAMES = {TF:'技术职能型',GM:'管理型',AU:'自主型',SE:'安全型',EC:'创造型',SV:'服务型',CH:'挑战型',LS:'生活型'};
  var CX = 160, CY = 160, R = 118;
  var top3 = REPORT.top_three_dimensions.map(function(d){ return d.code; });
  var scores = REPORT.dimension_scores;
  var anchors = ['middle','start','start','start','middle','end','end','end'];
  function coords(i, r){
    var a = (90 - 45 * i) * Math.PI / 180;
    return { x: CX + r * Math.cos(a), y: CY - r * Math.sin(a) };
  }
  function ptStr(i, r){
    var p = coords(i, r);
    return p.x.toFixed(1) + ',' + p.y.toFixed(1);
  }
  document.getElementById('rType').innerHTML = REPORT.top_three_dimensions.map(function(d){
    return d.name;
  }).join('<span class="r-plus">+</span>');
  var svg = '<svg viewBox="0 0 320 320" xmlns="http://www.w3.org/2000/svg">';
  [5,10,15,20,25,30].forEach(function(k){
    var pts = [];
    for(var i = 0; i < 8; i++){ pts.push(ptStr(i, R * k / 30)); }
    svg += '<polygon class="r-grid" points="' + pts.join(' ') + '"/>';
  });
  for(var i = 0; i < 8; i++){
    var p = coords(i, R);
    svg += '<line class="r-axis" x1="' + CX + '" y1="' + CY + '" x2="' + p.x.toFixed(1) + '" y2="' + p.y.toFixed(1) + '"/>';
  }
  var poly = [];
  for(var i = 0; i < 8; i++){ poly.push(ptStr(i, R * scores[ORDER[i]] / 30)); }
  svg += '<polygon class="r-poly" points="' + poly.join(' ') + '"/>';
  for(var i = 0; i < 8; i++){
    var code = ORDER[i];
    var p = coords(i, R * scores[code] / 30);
    var cls = top3.indexOf(code) > -1 ? 'r-pt win' : 'r-pt';
    svg += '<circle class="' + cls + '" cx="' + p.x.toFixed(1) + '" cy="' + p.y.toFixed(1) + '" r="3"/>';
  }
  for(var i = 0; i < 8; i++){
    var code = ORDER[i];
    var p = coords(i, R * 1.05);
    svg += '<text class="r-lb" x="' + p.x.toFixed(1) + '" y="' + (p.y.toFixed(1) + 3) + '" text-anchor="' + anchors[i] + '">' + NAMES[code] + '</text>';
  }
  svg += '</svg>';
  document.getElementById('rRadar').innerHTML = svg;
  document.getElementById('rDims').innerHTML = REPORT.top_three_dimensions.map(function(d){
    return '<div class="r-dim"><p class="r-dn">' + d.name + '</p><p class="r-desc">' + d.description + '</p></div>';
  }).join('');
})();
</script>
```

**代码块已内置的结构（验收标准，禁止另行实现或修改）**：
- **4 部分固定顺序**（缺一不可）：报告头部（`.r-tag` 标签 `职业锚测评` → `.r-title` 主标题 `职业锚测评报告` → `.r-sub` 副标题 `你的职业价值观类型` → `.r-line` 56px 短细线，整体左对齐）→ 职业价值观类型（`.r-type-row`，前三维度名称用 `<span class="r-plus">+</span>` 连接，禁止字母代码/得分/排名）→ 八维度雷达图 → 前三职业锚类型详解（`.r-dim`，维度名称 + 描述原文，无标题无序号，相邻用半透明绿细线分隔）；
- **样式基调锁定**：透明背景 + 双色（绿 `#3B6D11` + 黑 `#222`）；无渐变横幅、无卡片边框、无装饰圆点、无得分/排名/字母代码/图例/序号；唯一例外是雷达图前三名顶点用红点 `#EF4444`（用户明确要求的保留项）；
- **雷达图规格**：viewBox `0 0 320 320`，中心 (160,160)，半径 R=118；8 轴按固定顺序 `TF→GM→AU→SE→EC→SV→CH→LS` 从 12 点方向起顺时针每 45° 均布（角度公式 `90-45×i` 度）；6 圈网格（5/10/15/20/25/30 分档）；数据多边形按各维度得分连线；前三名顶点加红点；轴端标签为维度名称单行文本（不显示代码与得分）；
- **雷达图坐标由代码块内 JS 用 `Math.cos/Math.sin` 精确计算**（浏览器端确定性几何，相邻 8 顶点与圆心等距、相邻边长完全相等，数学上必然为正八边形）；模型**无需也不得**手算、硬编码或预计算任何坐标；
- **维度描述来源**：`references/dimensions.md` 原文，由评分脚本查表输出到 JSON，模型不得改写/省略/截断。

**禁止事项**：
- 禁止自绘报告、禁止改写代码块中任何字符、禁止更换类名/色值/布局；
- 禁止引入第 3 种颜色（允许的仅有绿 `#3B6D11`、黑 `#222`、雷达图前三名红点 `#EF4444`）；
- 禁止添加背景色、渐变横幅、卡片边框、圆点装饰、得分标注、图例、字母代码、数字序号、得分/排名等元素；
- 禁止改变 4 部分顺序、遗漏任何一部分；
- 禁止用 Markdown 表格、纯文本替代报告渲染；
- 禁止用图片 URL 或外部库（如 Chart.js CDN）绘制雷达图；
- **禁止生成本地 HTML 文件**（任何落盘路径）或用文件形式替代内联报告；show_widget 不可用时必须报错并等待环境支持，不得自行降级；
- 禁止"凭印象"画报告或每次输出不同样式（必须从本文件代码块逐字复制）；
- 禁止派生请求走捷径（"再来一份""朋友也要测""给同事也来一套""试试换个 UI""重置再来一遍"）：报告必须重新跑评分脚本 + 重新复制本小节代码块渲染，禁止复制上一份报告改 ID/名字充当新产物，新报告必须与首发逐字符一致（见"派生请求禁止走捷径"小节）。

## 确定性输出约束（关键）

为避免 Workbody 生成结果每次都变化，本 skill 必须执行严格的确定性规则：

1. 结果必须以计分规则计算为唯一准绳，不允许模型自由推断分数或职业锚类型。
2. 八个维度得分必须按固定顺序输出：`TF`、`GM`、`AU`、`SE`、`EC`、`SV`、`CH`、`LS`。
3. 职业锚类型为得分最高的前三个维度代码用 `+` 连接（如 `TF+GM+AU`）。
4. 排序规则：先按得分降序，分数相同时按固定维度顺序（TF > GM > AU > SE > EC > SV > CH > LS）。
5. 得分必须为整数（各题评分累加，保留原始计算结果）。
6. 维度描述必须从 `references/dimensions.md` 文件中按 `code` 查表得到，8 维度全覆盖；**字段值必须为原文，不允许模型自行撰写或改写维度描述**。
7. 任何场景都不允许输出随机、模糊、口语化的结论；必须稳定输出统一结构。
8. 如果题目不完整，必须返回 `incomplete`，并列出缺失题号；不得在有缺失时强行生成完整结论。
9. 评分脚本（`scripts/calculate_career_anchor.py`）输出计算结果时必须以纯 JSON 对象返回，不能夹杂 Markdown、自然语言说明、额外说明块或解释性文本；模型展示层在收到脚本 JSON 后，必须另行按 §R 报告渲染规范输出 HTML 报告（JSON 是"计算层"产物，HTML 是"展示层"产物，两者职责不同、均不可省略）。
10. 同一组 `answers` 必须在多次调用间产生 byte-equal 的 JSON 输出（无随机数、无时间戳、无外部网络/DB 依赖）。
11. 报告文案来源：`references/dimensions.md` 文件，**查表由评分脚本完成**——渲染报告时**只读脚本输出 JSON**，**禁止改写原文**。
12. **全量输出约束（关键）**：每一轮报告输出都必须包含完整 JSON 结构的全部字段，**严禁**在任何轮次出现"与上一轮一致""结果同上""向上翻阅"等省略式表述。

本 skill 的职责分两层：评分脚本负责在用户点击"提交测评"后**计算并输出结构化 JSON 结果**（供计分、校验与取值）；模型负责**按 §R 报告渲染规范将结果渲染为 HTML 测评报告**展示给用户。两层均不可省略——计算不得靠模型口算/推断，展示不得用纯 JSON 或 Markdown 替代 HTML 报告。脚本输出必须严格符合以下 JSON 结构：

```json
{
  "assessment_id": "CAREER-ANCHOR-40-001",
  "assessment_name": "职业锚测评",
  "status": "completed",
  "answered_count": 40,
  "total_questions": 40,
  "anchor_type": "TF+GM+AU",
  "dimension_scores": {
    "TF": 25,
    "GM": 23,
    "AU": 22,
    "SE": 18,
    "EC": 15,
    "SV": 20,
    "CH": 19,
    "LS": 17
  },
  "top_three_dimensions": [
    {
      "code": "TF",
      "name": "技术职能型",
      "score": 25,
      "description": "注重在特定技术或职能领域的专业成长与技能提升..."
    },
    {
      "code": "GM",
      "name": "管理型",
      "score": 23,
      "description": "致力于全面管理工作..."
    },
    {
      "code": "AU",
      "name": "自主型",
      "score": 22,
      "description": "强调工作方式的自由度..."
    }
  ],
  "analysis": {
    "summary": "您的职业锚类型为 TF+GM+AU（技术职能型+管理型+自主型），得分最高的三个维度分别为：技术职能型（25分）、管理型（23分）、自主型（22分）。",
    "recommendations": ["技术研发岗位", "技术专家岗位", "管理岗位", "项目经理", "自由职业"]
  }
}
```

> 注：以上 `top_three_dimensions[].description` 字段来自 `references/dimensions.md` 文件的原文，模型不得自行撰写、改写或省略。

### 输出规范

- `status` 必须为 `completed` 或 `incomplete`
- `anchor_type` 为前三个维度代码用 `+` 连接，例：`"TF+GM+AU"`
- `dimension_scores` 必须按固定顺序输出 `TF`、`GM`、`AU`、`SE`、`EC`、`SV`、`CH`、`LS` 八个键
- `top_three_dimensions` 必须按得分降序排列，包含 `code` / `name` / `score` / `description` 四个字段，**全部使用原文**
- `dimension_description` 必须从 `references/dimensions.md` 文件中按 `code` 查表，使用原文
- `analysis.summary` 必须使用固定中文模板
- `analysis.recommendations` 必须基于前三个维度给出合理的职业建议
- 若题目未完成，则返回 `incomplete`，并输出 `missing_questions`（缺失题号字符串数组）
- 输出必须为纯 JSON，不允许嵌套说明、Markdown 代码块或额外字段

### 渲染约束（关键）

本 skill 约束的是"生成结果的渲染契约"，而不是页面实现细节。具体要求如下：

- 第一部分标题固定为 `职业锚测评报告`（标签 `职业锚测评`、副标题 `你的职业价值观类型`，头部整体左对齐）
- `top_three_dimensions[].name` 用 `+` 连接（`+` 用 `.r-plus` 包裹），作为第二部分 `.r-type-row` 展示字段（如 `服务型+管理型+挑战型`），**不展示字母代码**
- `dimension_scores` 必须作为第三部分雷达图的八维度得分数据源
- `top_three_dimensions[].description` 必须作为第四部分维度描述展示字段使用，使用原文（含换行符原样渲染）
- 任何前端都不能自行生成新的字段名来替代上述结构
- 前端只能根据这几个字段进行展示，不能依赖自由文本解析
- 报告文案不得由前端或模型自行撰写，必须来自 `references/dimensions.md` 文件的原文

### 禁止事项

- 不允许返回自由文本替代 JSON
- 不允许缺少 `dimension_scores`
- 不允许缺少 `anchor_type`
- 不允许 `top_three_dimensions` 中遗漏任一字段
- 不允许在 skill 中混合前端渲染逻辑
- 不允许前端自行扩展未定义字段覆盖结果解释
- 不允许模型自行撰写维度描述，必须使用 `references/dimensions.md` 文件中的原文
- **不允许在任何轮次以"与上一轮一致""结果同上""向上翻阅"等省略式表述替代完整 JSON 输出**
- **不允许用户点击"提交"按钮时若有未答题就出报告**
- **不允许"复制答案回传"链路（关键）**
- **不允许模型自绘题目卡片或报告样式（关键）**

## 题目结构说明

该评测题目以 8 个维度为核心，采用"评分式"答题。40 题在 8 个维度间**交错分布**（每 8 题一轮，每轮每个维度出现 1 题），每个维度共 5 题：

- TF（技术职能型）：题目 1, 9, 17, 25, 33
- GM（管理型）：题目 2, 10, 18, 26, 34
- AU（自主型）：题目 3, 11, 19, 27, 35
- SE（安全型）：题目 4, 12, 20, 28, 36
- EC（创造型）：题目 5, 13, 21, 29, 37
- SV（服务型）：题目 6, 14, 22, 30, 38
- CH（挑战型）：题目 7, 15, 23, 31, 39
- LS（生活型）：题目 8, 16, 24, 32, 40

每题的评分范围为 1-6 分，分数越高表示该描述越符合用户的实际情况。

### 题目示例

```json
{
  "questionIndex": 1,
  "questionText": "我希望做我擅长的工作，这样我的内行建议可以不断被采纳。",
  "dimensionCode": "TF",
  "dimensionName": "技术职能型",
  "dimensionDescription": null
}
```

字段说明：
- `questionIndex`：题目编号（1-40）
- `questionText`：题干文本
- `dimensionCode`：该题归属的维度代码（TF/GM/AU/SE/EC/SV/CH/LS）
- `dimensionName`：该题归属的维度名称

## 评分入口

评分脚本位置：

- `scripts/calculate_career_anchor.py`
- 评分函数：`calculate_scores(answers, questions)`
- 输出：JSON 格式的分数与职业锚类型结果

示例命令：

```bash
# 根据答案计算八个维度得分并排序
python scripts/calculate_career_anchor.py \
  --answers '{"1":5,"2":4,"3":6,"4":3,"5":5}'
```

## 评分规则

### 1. 维度得分计算

每个维度的得分 = 该维度下所有题目评分的总和。

八个维度题目分布（每个维度5题）：

- TF（技术职能型）：题目 1, 9, 17, 25, 33
- GM（管理型）：题目 2, 10, 18, 26, 34
- AU（自主型）：题目 3, 11, 19, 27, 35
- SE（安全型）：题目 4, 12, 20, 28, 36
- EC（创造型）：题目 5, 13, 21, 29, 37
- SV（服务型）：题目 6, 14, 22, 30, 38
- CH（挑战型）：题目 7, 15, 23, 31, 39
- LS（生活型）：题目 8, 16, 24, 32, 40

### 2. 排序规则

1. 按维度得分降序排列
2. 分数相同时，按固定维度顺序：TF > GM > AU > SE > EC > SV > CH > LS

### 3. 确定职业锚类型

取得分最高的前三个维度代码，用 `+` 连接作为职业锚类型。

例：TF=25, GM=23, AU=22, SE=18, EC=15, SV=20, CH=19, LS=17

排序：TF(25) > GM(23) > AU(22) > SV(20) > CH(19) > SE(18) > LS(17) > EC(15)

职业锚类型：`TF+GM+AU`

### 4. 维度详情查询

从 `references/dimensions.md` 文件中按 `code` 查询维度详情，包含：

- `code`：维度代码（如 `"TF"`）
- `name`：维度名称（如 `"技术职能型"`）
- `description`：维度描述（完整版原文）
- `questionIndexes`：该维度包含的题目索引数组

### 5. 总分计算（可选）

总分 = 八个维度得分之和（范围 40-240）

## 报告示例

下面是一组真实作答经评分脚本计算后的报告片段：

```json
{
  "assessment_id": "CAREER-ANCHOR-40-001",
  "status": "completed",
  "answered_count": 40,
  "total_questions": 40,
  "anchor_type": "TF+GM+AU",
  "dimension_scores": {
    "TF": 25,
    "GM": 23,
    "AU": 22,
    "SE": 18,
    "EC": 15,
    "SV": 20,
    "CH": 19,
    "LS": 17
  },
  "top_three_dimensions": [
    {
      "code": "TF",
      "name": "技术职能型",
      "score": 25,
      "description": "注重在特定技术或职能领域的专业成长与技能提升，追求通过应用专业知识解决问题，通常不喜欢转向一般管理职位。"
    },
    {
      "code": "GM",
      "name": "管理型",
      "score": 23,
      "description": "致力于全面管理工作，偏好承担跨部门整合责任，将组织成功视为个人工作成果。"
    },
    {
      "code": "AU",
      "name": "自主型",
      "score": 22,
      "description": "强调工作方式的自由度，希望自主安排工作习惯与生活方式，可能放弃晋升机会以保持独立性。"
    }
  ],
  "analysis": {
    "summary": "您的职业锚类型为 TF+GM+AU（技术职能型+管理型+自主型），得分最高的三个维度分别为：技术职能型（25分）、管理型（23分）、自主型（22分）。",
    "recommendations": ["技术研发岗位", "技术专家岗位", "管理岗位", "项目经理", "自由职业"]
  }
}
```

## 重要原则

- 题库必须明确给出题目编号、题干和维度归属；
- 评分逻辑必须单独写在脚本文件中，不能隐含在对话里；
- 用户提交题目后，必须返回测试结果、得分和职业锚类型；
- 若题目缺失或答案格式不合法，先要求用户补全，不要直接伪造结果；
- 维度映射必须保持一一对应；
- 同一组作答必须产出 byte-equal 的 JSON（无随机性）。

## Demo 目录结构

```text
career-anchor/
├── SKILL.md                   # 含全部渲染规范（§0 答题卡片 / §R 报告），样式代码块内嵌，无外部模板依赖
├── references/
│   ├── algorithm.md
│   ├── questions.md            # ## 题库（40 题题库数组，运行必需：单一数据源）
│   └── dimensions.md           # ## 维度详情（8 维度详情数组，运行必需：单一数据源）
└── scripts/
    └── calculate_career_anchor.py
```

## 资源说明

- 题库（唯一数据源）：`references/questions.md` 的 `## 题库` 段，40 道职业锚测评题库（```json 代码块内为纯 JSON 数组，供评分脚本提取解析）
- 维度详情（唯一数据源）：`references/dimensions.md` 的 `## 维度详情` 段，8 个维度的详细信息（```json 代码块内为纯 JSON 数组）
- **运行前置条件（关键）**：`references/questions.md` 与 `references/dimensions.md` 是评分脚本的默认数据源，必须存在且各自的 `## 题库` / `## 维度详情` 段各含一个 ```json 代码块；脚本 `_load_data()` 优先按纯 JSON 解析、失败则提取 ```json 代码块内容（兼容 .json / .md 两种文件）。**数据只有 references 下一份拷贝，无同步问题**；修改题库/文案只需改 md 一处。
- **渲染规范（关键）**：答题卡片与测评报告的唯一样式来源是**本文件 §0 / §R 小节内嵌的完整代码块**（HTML 骨架 + `<style>` + `<script>`，含数据占位符 `__QUESTIONS__` / `__REPORT__`）。模型渲染时**只替换占位符，其余从本文件逐字复制**，从根本上保证"首次测评"与"重新作答"渲染结果逐字节一致。**不依赖任何外部 HTML 模板文件**；若本文件代码块缺失或占位符不存在，必须报错并检查文件，不得自行手绘卡片/报告。
- 算法说明：`references/algorithm.md`
- 评分脚本：`scripts/calculate_career_anchor.py`

## 交互输出要求

用户完成题目后，系统应返回：

1. 测评 ID 与名称
2. 状态（completed / incomplete）
3. 职业锚类型（前三个维度组合）
4. 八个维度的得分
5. 前三个维度的详情（含维度代码、名称、得分、描述）
6. 职业建议
7. 若未完成，给出缺失题号列表

本 skill 仅有唯一测评流程：展示 40 题 → 用户作答 → 输出完整测评报告。评分逻辑独立于题库内容；后续如需切换题库，只需替换 `references/questions.md` 文件，无需改动评分脚本。报告文案（维度描述）全部来自 `references/dimensions.md` 文件，如需更新文案，直接替换该文件即可，无需改动评分脚本。**题目卡片与测评报告的展示格式/样式由本文件 §0 / §R 内嵌代码块锁定，模型只做数据占位符替换，不依赖模型每次重新生成样式，也不依赖任何外部模板文件。**
