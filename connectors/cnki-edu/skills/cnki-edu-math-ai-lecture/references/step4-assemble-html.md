# 第四步提示词（v6.9 + v2 脚本装配）

> ## ⚠️ v2 执行方式声明（**优先于下文一切「你输出 HTML」措辞**）
>
> **v2 下本步默认不由模型输出 HTML。** S4 改为**脚本装配**——固定骨架 + 3 份产物，模型零输出。
>
> ```bash
> node scripts/assemble-html.js <S1.js> <S2.js> <S3.js> \
>      --title "页面标题" --qtitle "题型标题" --out <输出.html>
> ```
>
> **🌐 通用版装配**：当 S0 为通用版（无连接器 / 无权益）时，命令须加 `--generic` 标志，脚本会在页面顶部注入「⚠ 通用版 · 非知网标准解析」横幅：
> ```bash
> node scripts/assemble-html.js <S1.js> <S2.js> <S3.js> \
>      --generic --title "页面标题" --qtitle "题型标题" --out <输出.html>
> ```
> 态 B 另在页末原样输出「解锁知网数据增强层」转化卡。
>
> - **`<S3.js>`** 传 S3.5 的产物（`apply-s3.5.js` 写出的 `*.applied.js`，或旧格式的 `s3.5.js`）。
> - 骨架来自 `references/html-template.html`（由 `scripts/build-template.js` 从**本文件下方的 HTML 模板块**抽取 + 注入 6 个槽位标记，**单一真源**）。
> - 脚本会做 14 项自检（`<!DOCTYPE html>` 开头 / 无残留 `@@` / 四个数据区齐全 / 档位声明 / 两块库 / `qAcc,switchQ,recQ` / `navigationMap`+`drawFunctions` / `cleanVoiceText`+`latexToSpeech` / `ctx` 前置 / 抄写自检日志块 / `questionData` 无 `highlight` 字段 / 主脚本语法可编译），全过才写出。
> - **模型侧在这步只需做一件事**：确认脚本已就绪并执行它；**不要**再读下文模板去手写 HTML。这样可省掉全流程最大的一块输出（≈126 KB）。
>
> **为什么改**：旧流程让模型"整页重写"，而 HTML 里**内嵌着 76.8 KB 的内联库**——等于把 S3/S3.5 已经产出的代码**再抄一遍**。脚本装配零抄写失真、零截断风险、零格式返工。
>
> **模板块的角色变了，但仍在**：下文「完整 HTML 标准模板」**不是让你照抄的**，而是**模板真源**。若本文件升级（v6.9 → v7），**重跑 `node scripts/build-template.js`** 即可刷新 `references/html-template.html`，无需改 `assemble-html.js`。
>
> **回退路径（仅当脚本不可用时）**：若 `scripts/assemble-html.js` 或 `references/html-template.html` 缺失/报错，**才**启用"模型组页"——此时按下文「工作流程」与「数据填写位置对照表」把 4 份数据填进模板，产出**裸 HTML**（`<!DOCTYPE html>` 开头、无 Markdown 包裹、无说明前后缀）。
>
> ---

> **v6.9 本次修改要点（1 条）：**
> 1. **★ 布局由「手机端单列」升级为「桌面端宽屏」**（核心）：① Tab 切换栏固定在**页面顶部**；② 整页**限宽居中**（最大宽度 `1200px`、最小宽度 `680px`，CSS 变量 `--page-max` / `--page-min`）；③ 讲解 Tab 改为**「上左右 + 下整行」**——上方 `.explain-top` 内**绘图区 ｜ 整合步骤卡片区 左右并排，宽度比 1:1**，下方底部栏（语音 + 上一步/下一步）**整行**；④ 窄屏 `@media (max-width:760px)` 自动回退为单列手机布局。**配色不变**（沿用原版：背景 `#f4f7fc`、Tab 选中 `#1e293b`、题标 `#3b82f6`、步骤号琥珀 `#d97706`）。
>    - **结构变更**：新增 `.tab-bar-frame`（Tab 栏限宽居中）、新增 `.explain-top`（包裹绘图+步骤两栏）、**`.bottom-bar` 由 body 直属节点移入 `.explain-container` 内底部**。JS 的 `switchTab` 逻辑不变（仍用 `bottomBar.classList.toggle('show', tab==='explain')`，搬迁后行为一致）。

> **v6.8.1 本次修改要点（1 条）：**
> 1. **★ 修正模板骨架里的「伪真数字占位」（核心）**：原骨架 `navigationMap` 里写 `finalSummary: 30`——但上面「独立总结」是 frame 9，**10~29 帧根本没有定义**；`drawFunctions` 也只列了 2 项（`drawFrame_0, drawFrame_1`）。这类**"看着像真数字"的占位**比 `/* 完整实现 */` 更危险——它不像占位符，最容易被整段照抄，照抄后**帧号断裂、页面取不到帧、画布停在最后一帧不动**。已改为 `finalSummary: 10`（与 frame 9 紧接），并把 `drawFunctions` 补成连续的 `drawFrame_0 … drawFrame_10`，同时在骨架前新增「伪真数字占位」专项警告。

> **v6.8 本次同步（v6.7 → v6.8，共 3 条次要修正，跟随第二步 v3 与第 3.5 步 v6.7 的「语音可播性」改动）：**
> 1. **★ 给 `cleanVoiceText` 加「符号转中文」兜底替换**（核心改动）：即使第二步漏改，第四步在播放前也能兜住——`Rt△`→"直角三角形"、`△`→"三角形"、`∠`→"角"、`⊥`→"垂直于"、`∥`→"平行于"、`∽`→"相似于"、`≌`→"全等于"、`°`→"度"、`√`→"根号"、`π`→"派"、`⊙`→"圆"、`²`→"的平方"、`³`→"的立方" 等。**`Rt△` 的替换必须放在 `△` 之前**（顺序反了会把 `Rt△` 误替换为 `Rt三角形`）。
> 2. **★ 给 `latexToSpeech` 末尾加同样的兜底替换**：防止 `$...$` LaTeX 公式里的符号漏网。
> 3. **★ 把 `cleanVoiceText` / `latexToSpeech` 提升为「不得改动的第七样」**（v6.7 时它们只在"另有一条"里被提到）；同时在表格下方补充「兜底替换的边界」（明确只覆盖约 20 个"纯数学符号"；`=` `/` `+` `-` `(` `)` `α` `β` `θ` 由第二步保证）。

> **v6.7 本次同步（v6.6 → v6.7，共 3 条次要修正）：**
> 1. **「不得改动的五样东西」→「六样」**：新增第 5 项——`const qAcc = {}; let currentQ = 1; function switchQ(q){...} function recQ(item){...}` 四个声明。它们是**持久/临时分离的核心机制**，长得像"工具函数"，是"整理代码"时最可能被顺手优化的对象。原"另有两条最容易踩的"里关于这一条已提升到表内。
> 2. **「数据区 3」骨架前加 ⚠️ 提示**：明确"骨架里的 `/* 完整实现 */` 等是占位符，实际产出时每个 `function` 都必须写出完整函数体"。
> 3. **「完整 HTML 标准模板」中数据区 3 的骨架前加 ⚠️ 提示**（同第 2 条），避免模型照抄占位符。

> **v6.6 本次同步（跟随第三步 v6.6 与第 3.5 步 v6.6）：**
> 17. **新增第 5 样「不得改动」**：产物末尾的 `/* ═══ 抄写自检日志（v6.6 要求）═══ ... */` 注释块。
> 18. **输出格式硬性化**：产物必须是**裸 HTML**。
> 19. **数据区 3 描述同步 v6.6**：Step 3 产出的**解构语句不含 `recordToAccumulator`**、**含 `qAcc/switchQ/recQ` 三个辅助**、**末尾有「抄写自检日志」注释块**。
> 20. **检查清单新增 3 条**：自检日志保留、无 Markdown 包裹、无说明前缀。
> 21. **【用户输入】末尾新增输出格式细则**（3 条）。

> **本次修改要点（基于用户确认的新排版规则，v2）：**
> 1. **去掉题干条件模块**。
> 2. **去掉小问面包屑、独立解题步骤区、独立进度点**，改为"画布（上）+ 整合步骤卡片（下）"。
> 3. **整合步骤卡片**：标题行 + 目标行 + 解题步骤逐步累加 + 避坑按钮。
> 4. **标题编号规则**：审题定向=①、破冰搭桥=②、规范建模=③、独立总结=④；规范建模子步骤显示为 `③-1、③-2…`；每个小问重新从①开始。
> 5. 渲染引擎已按上述规则重写并验证。

> **v3 新增（公式渲染 + 底部栏隐藏 + 语音清洗）：**
> 6. **数学公式渲染（KaTeX）**。
> 7. **试题 Tab 隐藏底部栏**。
> 8. **语音文本清洗**：`voiceText` 里的指令标记与 `$...$` 数学公式在**播放前自动清洗**。

> **v4 新增（引号转义 + 防空白页）：**
> 9. **⚠️ 字符串引号铁律**。
> 10. **生成后必须自检语法**。
> 11. **⚠️ 省略占位符禁令**。

> **v5 新增（跟随第三步 v6.4）：**
> 12. **新增专节「不得改动的四样东西」**。
> 13. **写清「数据区 3-前置」切分线**。
> 14. **删掉「工具函数」提法**。
> 15. **`pts` 描述改为真身**。
> 16. **检查清单新增 7 条 v6.4 标志物**。

---

```markdown
# 角色设定
你是一名资深前端开发工程师，专精于移动端 HTML 教育应用开发。你已完成前序所有设计工作：
- Step 1：试题结构化（sentences + translations）
- Step 2：按小问组织的四环讲题方案（questionData 对象，无 highlight 字段；**voiceText 已全中文化，无数学符号**）
- Step 3：导航帧绘图代码（v6.7 形态：`window.__DRAW_TIER__` 档位声明 + 两块内联库 `LIB` + 解构语句（**不含 `recordToAccumulator`**）+ `qAcc/switchQ/recQ` 三个辅助 + 构造区 `pts` + `drawBaseScene` + `drawFrame_N`（**六层结构**）+ `navigationMap` + `drawFunctions` + **末尾「抄写自检日志」注释块**）

现在你需要将所有内容整合成一个**完整的、可直接运行的 HTML 文件**。

---

# 任务目标
基于以下输入材料，生成一个完整的 HTML 文件。该文件必须支持：
1. 双 Tab 结构（试题 / 讲解），**Tab 切换栏固定在页面顶部**；**整页限宽居中**（最大宽度 1200px、最小宽度 680px，见模板 CSS `--page-max` / `--page-min`；窄屏 ≤760px 自动回退为单列手机布局）
2. 试题 Tab：原题 + 数学语言翻译器
3. 讲解 Tab：**上方左右并排（绘图区 ｜ 整合步骤卡片区，宽度比 1:1）+ 下方整行底部栏**——无题干条件模块、无面包屑、无独立进度点
4. **步骤卡片标题规则**：`第X问 编号 环节 · 任务`；规范建模子步骤 `③-1、③-2…`；每问重新从①开始；总起/终局总结无编号
5. **步骤卡片内容**：目标行（仅规范建模子步骤）+ 解题步骤逐步累加（当前行高亮）+ 避坑按钮（仅破冰环节）
6. 底部栏（**位于讲解 Tab 容器内底部**）：语音控制（播放/暂停 + 进度条）+ 导航按钮（上一步/下一步）；仅在"讲解"Tab 显示
7. 按导航序列逐节点推进（整题总起 → 每小问四环 → 规范建模子步骤 → 终局总结）

---

# 输入材料
你将收到以下输入（共 4 项）：
1. **Step 1 产出的 `sentences` 数组**
2. **Step 1 产出的 `translations` 数组**
3. **Step 2 产出的完整讲题方案对象 `questionData`**（含 `questionType`、`totalIntro`、`subQuestions`、`finalSummary`；**不含 `highlight` 字段**；**`voiceText` 已全中文化**——所有 `△` `∠` `⊥` `∥` `∽` `≌` `°` `√` `π` `⊙` 等数学符号已改写为中文，但**方括号标记 `[指令性]` / `[pause Xs]` 等保留**）
4. **Step 3 产出的绘图代码（v6.7 形态）**，其结构为：
   - `window.__DRAW_TIER__` 档位声明
   - `const W = 360, H = 260` + `COLORS`
   - **两块内联库 `const LIB = (function(){ 几何内核 + 绘图层 })()`**
   - 解构语句：`const pts = LIB.pts; const { CK, ..., replayAccumulator, ... } = LIB;`
     ★ **v6.6 起：解构清单里没有 `recordToAccumulator`**
   - ★ **`const qAcc = {}; let currentQ = 1; function switchQ(q){...} function recQ(item){...}` 三个辅助**
   - `drawBaseScene` / `drawQnBase`
   - `drawFrame_0` ~ `drawFrame_N`（**六层结构**）
   - `navigationMap` / `drawFunctions`
   - ★ **末尾「抄写自检日志」注释块**
   - **其中没有任何「可粘贴的工具函数」**

---

# 工作流程（按顺序执行）

## 第一步：识别数据
- `sentences` / `translations` 是否为数组？
- `questionData` 是否包含 `subQuestions`（至少 1 项）？每个小问是否含 `stages` 四环？规范建模是否含 `subSteps`？
- `navigationMap` 是否覆盖 `totalIntro`、所有 `subQuestions[i].stages`、`finalSummary`？
- `drawFunctions` 数组长度是否与帧数一致（索引即帧号）？

## 第二步：填入数据
将四项数据分别填入 HTML 模板对应位置（见"数据填写位置对照表"）。

## 第三步：检查兼容性
- `navigationMap.subQuestions[i].stages` 结构是否与 `questionData.subQuestions[i].stages` 一一对应？
- 规范建模的 `frames` 数组长度是否等于对应 `subSteps.length`？
- `drawFunctions` 是否能覆盖所有帧号（0 ~ 最大帧号）？

---

# 完整 HTML 标准模板

以下是完整的 HTML 代码框架。**你只需做四件事**：
1. 替换 `const sentences`、`const translations`、`const questionData` 三处数据
2. **替换绘图代码区域**——范围是：档位声明 `window.__DRAW_TIER__` → `W/H` → `COLORS` → **`LIB` 整段（两块内联库，一字不改）** → **解构语句** → **`qAcc/switchQ/recQ` 三个辅助** → `drawBaseScene` → `drawFrame_N` → `navigationMap` → `drawFunctions` → **「抄写自检日志」注释块**（**切分线见下方「数据区 3-前置」**）
3. 替换 `QUESTION_TITLE` 为题型名称
4. 其他所有内容（CSS、HTML 结构、JavaScript 渲染引擎）**完全保持不变**

> ⚠️ **绘图代码整段替换，不改变量名**：
> - Step 3 产出的绘图代码**真身**是：档位声明 → `const W = 360, H = 260` → `COLORS` → 两块内联库 `const LIB = (function(){ 几何内核 + 绘图层 })();` → 解构语句（**不含 `recordToAccumulator`**）→ **`qAcc / switchQ / recQ`** → `const pts = LIB.pts;` → `drawBaseScene` → `drawFrame_N` → `navigationMap` → `drawFunctions` → **「抄写自检日志」注释块**。
> - 它里面**没有** `const pts = {...}` 这样的字面量坐标对象，也**没有**可以粘贴的「工具函数」。
> - 格式上几何点必须保持 `pts.H` 形式；若改成 `const H = {...}` 会与画布高度 `H` 冲突，报 `SyntaxError: Identifier 'H' has already been declared`。
> - **⛔ 有七样东西禁止改动**，见下方专节「不得改动的七样东西」。

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>【替换为题型名称】</title>
    <!-- KaTeX 数学公式渲染库（公式显示正确的关键，务必保留；同步加载保证顺序） -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
    <script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
    <style>

        /* 桌面端页面宽度约束：整体宽度上限 1200px、下限 680px */
        :root{--page-max:1200px;--page-min:680px}
        *{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent}
        html,body{height:100%;font-family:-apple-system,"PingFang SC",system-ui,sans-serif;background:#f4f7fc;color:#1e293b;overflow:hidden}
        body{display:flex;flex-direction:column;min-width:var(--page-min)}
        .tab-bar-wrapper{flex-shrink:0;background:#f4f7fc;padding:12px 16px 0 16px;z-index:10}
        .tab-bar-frame{max-width:var(--page-max);min-width:var(--page-min);margin:0 auto}
        .tab-bar{display:flex;background:white;border-radius:60px;padding:4px;box-shadow:0 2px 8px rgba(0,0,0,0.04)}
        .tab-btn{flex:0 0 50%;padding:12px 0;border:none;border-radius:40px;font-size:16px;font-weight:600;background:transparent;color:#64748b;cursor:pointer;text-align:center;touch-action:manipulation}
        .tab-btn.active{background:#1e293b;color:white;box-shadow:0 4px 12px rgba(30,41,59,0.15)}
        .tab-btn:active{transform:scale(0.96)}
        .tab-content-wrapper{flex:1;overflow:hidden;display:flex;flex-direction:column;max-width:var(--page-max);min-width:var(--page-min);margin:0 auto;width:100%;padding:12px 16px 12px 16px}
        .tab-content{display:none;height:100%;flex-direction:column;overflow:hidden;min-width:0}
        .tab-content.active{display:flex}
        .question-area{background:white;border-radius:20px;padding:20px 16px;box-shadow:0 2px 12px rgba(0,0,0,0.05);overflow-y:auto;flex:1}
        .q-title{font-size:15px;font-weight:600;color:#3b82f6;background:#eff6ff;display:inline-block;padding:4px 16px;border-radius:30px;margin-bottom:14px}
        .sentence-list{font-size:18px;line-height:1.9;font-weight:500}
        .sentence-list .sentence{display:block;padding:2px 0}
        .translator-section{margin-top:16px;border-top:1px dashed #e2e8f0;padding-top:16px}
        .translator-section .title{font-size:14px;font-weight:600;color:#475569;margin-bottom:8px}
        .trans-item{background:#f0f7ff;border-radius:10px;padding:8px 14px;font-size:15px;display:flex;flex-wrap:wrap;align-items:center;gap:4px 10px;margin-bottom:6px}
        .trans-item .orig{color:#475569}
        .trans-item .math{font-weight:600;color:#2563eb;font-family:"Times New Roman",serif;background:#dbeafe;padding:0 10px;border-radius:6px}
        /* 讲解 Tab = 上（绘图｜讲解 左右等比 1:1） + 下（语音/切换条） */
        .explain-container{flex:1;min-height:0;display:grid;grid-template-rows:1fr auto;grid-template-columns:1fr;gap:12px;overflow:hidden}
        .explain-top{min-height:0;display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:12px;overflow:hidden}
        .canvas-wrap{background:white;border-radius:20px;padding:10px;box-shadow:0 2px 12px rgba(0,0,0,0.05);position:relative;align-self:start}
        #stepCanvas{width:100%;aspect-ratio:360/260;display:block;background:#fff;border-radius:12px}
        .frame-badge{position:absolute;top:16px;right:16px;background:rgba(30,41,59,0.75);color:white;font-size:12px;padding:3px 10px;border-radius:20px;pointer-events:none}
        .step-content{min-height:0;overflow-y:auto;padding-bottom:10px}
        .step-item{background:white;border-radius:20px;padding:16px;box-shadow:0 2px 12px rgba(0,0,0,0.05)}
        .step-header{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:10px}
        .sq-tag{font-weight:600;color:#3b82f6;background:#eff6ff;padding:3px 12px;border-radius:20px;font-size:14px;flex-shrink:0}
        .step-idx{font-weight:700;color:#d97706;background:#fef3c7;padding:3px 10px;border-radius:20px;font-size:14px;flex-shrink:0}
        .step-title{font-size:16px;font-weight:600;color:#1e293b;flex:1;min-width:0;line-height:1.5}
        .step-count{font-size:12px;color:#94a3b8;margin-left:auto;flex-shrink:0}
        .step-body{margin-top:2px}
        .step-goal{font-size:14px;font-weight:600;color:#2563eb;background:#eff6ff;border-radius:10px;padding:8px 12px;margin-bottom:10px;line-height:1.6}
        .solution-line{font-family:"Times New Roman",serif;font-size:15px;line-height:2.0;color:#334155;padding:2px 10px;border-radius:6px;word-break:break-all}
        .solution-line.current{background:#eff6ff;color:#1d4ed8;font-weight:600;animation:fadeSlide 0.4s ease}
        .node-desc{font-size:16px;line-height:1.9;color:#334155;word-break:break-word}
        .node-desc .math{font-weight:600;color:#2563eb;font-family:"Times New Roman",serif}
        .pitfall-trigger{margin-top:12px;background:#fef2f2;color:#dc2626;border:1px solid #fecaca;border-radius:12px;padding:10px 16px;font-size:14px;font-weight:500;text-align:center;cursor:pointer}
        .pitfall-trigger:active{transform:scale(0.96)}
        .bottom-bar{flex-shrink:0;background:white;border-radius:16px;box-shadow:0 2px 12px rgba(0,0,0,0.05);padding:12px 16px;display:none;align-items:center;gap:12px}
        .bottom-bar.show{display:flex}
        .nav-btn{border:none;background:#f1f5f9;color:#1e293b;font-size:14px;font-weight:600;padding:12px 20px;border-radius:30px;cursor:pointer;transition:0.2s}
        .nav-btn:disabled{opacity:0.35}
        .nav-btn:active{transform:scale(0.95)}
        .voice-control{flex:1;display:flex;align-items:center;gap:10px;min-width:0}
        .play-btn{width:48px;height:48px;border:none;border-radius:50%;background:#1e293b;color:white;font-size:20px;cursor:pointer;flex-shrink:0;transition:0.2s}
        .play-btn:active{transform:scale(0.92)}
        .progress-wrap{flex:1;display:flex;flex-direction:column;gap:2px;min-width:0}
        #progressSlider{width:100%;accent-color:#3b82f6}
        .time-label{font-size:12px;color:#64748b;text-align:right}
        /* KaTeX 公式与周围文字对齐 */
        .katex{font-size:1.08em}
        .sentence .katex,.node-desc .katex,.step-goal .katex,.solution-line .katex,.trans-item .katex{vertical-align:middle}
        .modal-overlay{position:fixed;inset:0;background:rgba(15,23,42,0.45);display:none;align-items:center;justify-content:center;z-index:1000;padding:24px}
        .modal-overlay.show{display:flex}
        .modal{background:white;border-radius:20px;padding:20px;width:100%;max-width:340px}
        .modal-title{font-size:17px;font-weight:600;color:#1e293b;margin-bottom:12px}
        .modal-block{border-radius:12px;padding:12px;margin-bottom:10px;font-size:14px;line-height:1.7}
        .modal-block.wrong{background:#fef2f2;color:#b91c1c}
        .modal-block.right{background:#f0fdf4;color:#15803d}
        .block-label{font-weight:600;margin-bottom:4px}
        .modal-close-btn{width:100%;border:none;background:#1e293b;color:white;font-size:15px;font-weight:600;padding:12px;border-radius:30px;cursor:pointer;margin-top:6px}
        .modal-close-btn:active{transform:scale(0.97)}
        @keyframes fadeSlide { from { opacity:0; transform:translateY(6px);} to { opacity:1; transform:translateY(0);} }

        /* ===== 窄屏回退（≤760px）：单列竖排，取消最小宽度限制 ===== */
        @media (max-width:760px){
            body{min-width:0}
            .tab-bar-frame,.tab-content-wrapper{min-width:0;max-width:none}
            .tab-content-wrapper{padding:12px;padding-bottom:0}
            .explain-top{grid-template-columns:1fr;overflow:visible}
            .canvas-wrap{align-self:stretch}
            .explain-container{display:flex;flex-direction:column}
            .step-content{flex:1}
        }
        </style>
</head>
<body>
    <div class="tab-bar-wrapper" id="tabBarWrapper">
        <div class="tab-bar-frame">
        <div class="tab-bar">
            <button class="tab-btn active" data-tab="question">📖 试题</button>
            <button class="tab-btn" data-tab="explain">🎯 讲解</button>
        </div>
        </div>
    </div>
    <div class="tab-content-wrapper">
        <div class="tab-content active" id="tabQuestion">
            <div class="question-area">
                <div class="q-title" id="questionTitle">【题型名称】</div>
                <div class="sentence-list" id="sentenceList"></div>
                <div class="translator-section">
                    <div class="title">🔤 数学语言翻译器</div>
                    <div id="translatorList"></div>
                </div>
            </div>
        </div>
        <div class="tab-content" id="tabExplain">
            <div class="explain-container" id="explainBody">
                <div class="explain-top">
                    <div class="canvas-wrap">
                        <canvas id="stepCanvas" width="360" height="260"></canvas>
                        <div class="frame-badge" id="frameBadge">帧 1 / N</div>
                    </div>
                    <div class="step-content" id="stepContent"></div>
                </div>
                <div class="bottom-bar" id="bottomBar">
                    <button class="nav-btn" id="prevBtnFixed">⬅ 上一步</button>
                    <div class="voice-control">
                        <button class="play-btn" id="playBtn">▶</button>
                        <div class="progress-wrap">
                            <input type="range" id="progressSlider" min="0" max="100" value="0">
                            <span class="time-label" id="timeLabel">0:00 / 0:00</span>
                        </div>
                    </div>
                    <button class="nav-btn" id="nextBtnFixed">下一步 ➡</button>
                </div>
            </div>
        </div>
    </div>
    <div class="modal-overlay" id="pitfallModal">
        <div class="modal">
            <div class="modal-title">⚠️ 避坑指南</div>
            <div class="modal-block wrong"><div class="block-label">❌ 常见错误</div><div id="modalWrong"></div></div>
            <div class="modal-block right"><div class="block-label">✅ 正确做法</div><div id="modalRight"></div></div>
            <button class="modal-close-btn" id="closeModalBtn">我记住了</button>
        </div>
    </div>
    <script>
        // ============================================================
        //  【数据区 1】Step 1 产出：sentences / translations
        //  ⬇️ 替换为第一步的实际数据
        // ============================================================
        const sentences = [
            "句子1",
            "句子2"
        ];
        const translations = [
            { original: "原始文字片段", math: "数学表达式" }
        ];

        // ============================================================
        //  【数据区 2】Step 2 产出：questionData（不含 highlight 字段；voiceText 已全中文化）
        //  ⬇️ 替换为第二步的实际输出
        // ============================================================
        const questionData = {
            questionType: "几何证明题",
            totalIntro: null,
            subQuestions: [
                {
                    index: 1, label: "（1）", goal: "求证：...",
                    stages: [
                        { stage: "审题定向", title: "...", description: "...", voiceText: "...", showPitfall: false, pitfallContent: null, voiceDuration: 13 },
                        { stage: "破冰搭桥", title: "...", description: "...", voiceText: "...", showPitfall: true, pitfallContent: { wrong: "...", right: "..." }, voiceDuration: 16 },
                        {
                            stage: "规范建模", title: "规范建模 · 分步推导",
                            subSteps: [
                                { subIndex: 1, logicType: "A", stepTitle: "...", solutionLine: "证明：∵ ...", voiceText: "...", canvasChange: "...（持久）", voiceDuration: 9 }
                            ]
                        },
                        { stage: "独立总结", title: "...", description: "通法：...<br>易错点：...", voiceText: "...", voiceDuration: 13 }
                    ]
                }
            ],
            finalSummary: null
        };

        // ============================================================
        //  【数据区 3-前置】本模板所有 —— ⛔ 原样保留，禁止替换/删除
        //  绘图层内部直接使用 ctx / W / H 三个名字，删掉任一个画布就全线失效
        // ============================================================
        const canvasEl = document.getElementById('stepCanvas');
        const ctx = canvasEl.getContext('2d');

        // ============================================================
        //  【数据区 3】Step 3 产出 —— ⬇️ 以下整段替换为第三步的实际输出
        //  （真实内容：档位声明 + W/H + COLORS + 两块内联库 LIB 整段 + 解构语句
        //   + qAcc/switchQ/recQ + 构造区 + 绘图函数 + navigationMap + drawFunctions
        //   + 末尾「抄写自检日志」注释块）
        //
        //  ⚠️ 下面骨架里的 `/* 完整实现 */` 是**骨架占位**；
        //     实际产出时，**每个 `function` 都必须写出完整函数体**，不得残留占位符。
        //
        //  ⚠️⚠️ **特别注意「伪真数字占位」（v6.8.1 新增）**：骨架里 navigationMap 的帧号
        //     用的是**看似真实的数字**，比 `/* 完整实现 */` 更容易被整段照抄。
        //     替换时逐项核对：**帧号从 0 连续排到最大帧号，不得跳号，
        //     不得出现"比上一个帧号大得多"的孤立数字。**
        //
        //  ⬇️ 替换为第三步的实际输出
        // ============================================================
        window.__DRAW_TIER__ = 'A';   // 档位声明（A/B/C），禁止删改
        const W = 360, H = 260;       // 画布尺寸，变量名不得改
        const COLORS = { /* 颜色常量——完整实现 */ };
        const LIB = (function () {
            /* 两块内联库：几何内核 + 绘图层，整段粘贴、一字不改 */
            return { pts: {} /* 完整实现：CK, drawLine, drawMathText, finishFrame, ... */ };
        })();
        // ★ v6.6：解构语句——注意**不含 recordToAccumulator**（只能通过 recQ 累积）
        const pts = LIB.pts;
        const {
            CK, CKSummary, CKBounds, CKSpacing, CKDrawViolations,
            stateAccumulator, resetAccumulator, replayAccumulator,
            clearCanvas, finishFrame,
            drawPoint, drawLine, drawRay, drawCircle, drawArc,
            drawPolygon, hatchRegion, drawAngleArc, drawRightAngle, drawEqualMark, drawParallelMark,
            mapping, drawAxes, drawGrid, drawCurve,
            drawBar, drawHistogram, drawBrokenLine, drawSector, drawTree,
            drawMathText, drawSymbol, drawLabel,
            stopAnim, animateLine, pulseHighlight, fadeIn, colorShift, breathe, animateTransform
        } = LIB;
        // ★ v6.6：持久/临时分离机制（禁止删改）
        const qAcc = {}; let currentQ = 1;
        function switchQ(q) { /* 完整实现 */ }
        function recQ(item) { /* 完整实现 */ }
        function drawBaseScene() { /* 完整实现 */ }
        // ↓ 仅"多图题"才需要 drawQnBase；单图题可省略这两行
        function drawQ1Base() { /* 多图题——完整实现 */ }
        function drawQ2Base() { /* 多图题——完整实现 */ }
        // ↓ 实际产出时，每个帧号都要有一个 drawFrame_N，且 N 从 0 连续到最大帧号
        function drawFrame_0() { /* totalIntro——完整实现 */ }
        function drawFrame_1() { /* 完整实现 */ }
        // … drawFrame_2 … drawFrame_10 均须写出**完整函数体**，不得省略、不得留占位符
        const navigationMap = {
            totalIntro: 0,
            subQuestions: [
                {
                    index: 1, label: "（1）",
                    stages: [
                        { stage: "审题定向", frame: 1 },
                        { stage: "破冰搭桥", frame: 2 },
                        { stage: "规范建模", frames: [3,4,5,6,7,8] },
                        { stage: "独立总结", frame: 9 }
                    ]
                }
            ],
            // ⚠️ 独立总结为 frame 9，故 finalSummary 必须是紧接其后的 10。
            //    禁止照抄旧骨架的 `30`（那是伪真数字占位，会让 10~29 帧悬空、帧号断裂）。
            //    实际产出时按真实帧数写：最后一个小问的结束帧号 + 1。
            finalSummary: 10
        };
        // ⚠️ drawFunctions 必须**逐帧列全**：长度 = 最大帧号 + 1（本例为 11 项，索引 0~10）。
        //    禁止只列前两项，禁止用 `/* 完整实现：后续帧 */` 之类注释代替真实的数组项。
        const drawFunctions = [drawFrame_0, drawFrame_1, drawFrame_2, drawFrame_3, drawFrame_4, drawFrame_5, drawFrame_6, drawFrame_7, drawFrame_8, drawFrame_9, drawFrame_10];
        /* ═══ 抄写自检日志（v6.6 要求）═══
         *  _TEXT_OK         ✅ 逐字一致
         *  _SYM_OK          ✅ 逐字一致
         *  _textViolation   ✅ 4 条正则均含完整括号
         *  TOL              ✅ 0.5 / 0.5 / 1e-6
         *  CANVAS           ✅ 360 / 260 / 20
         *  SPACING_MIN      ✅ 12
         *  两块标记区        ✅ BEGIN/END 各一对，顺序未调
         * ═══════════════════════════ */

        // ============================================================
        //  【数据区 4】题型名称
        // ============================================================
        const QUESTION_TITLE = "题型 · 四环讲题";

        //  以下内容【完全保留】
        // ============================================================
        let currentIndex = 0, navSequence = [], currentUtterance = null;
        let isPaused = false, isPlaying = false, progressInterval = null, currentVoiceDuration = 8;
        const sentenceList=document.getElementById('sentenceList');
        const translatorList=document.getElementById('translatorList');
        const stepContent=document.getElementById('stepContent');
        const frameBadge=document.getElementById('frameBadge');
        const playBtn=document.getElementById('playBtn');
        const progressSlider=document.getElementById('progressSlider');
        const timeLabel=document.getElementById('timeLabel');
        const prevBtnFixed=document.getElementById('prevBtnFixed');
        const nextBtnFixed=document.getElementById('nextBtnFixed');
        const modal=document.getElementById('pitfallModal');
        const modalWrong=document.getElementById('modalWrong');
        const modalRight=document.getElementById('modalRight');
        const closeModal=document.getElementById('closeModalBtn');
        document.getElementById('questionTitle').textContent=QUESTION_TITLE;


        // ============================================================
        //  数学公式渲染 + 语音清洗工具（v3 新增，勿删；v6.8 起含符号转中文兜底）
        // ============================================================
        // 把一段文本里所有 $...$ 用 KaTeX 渲染为行内公式 HTML。
        // 若无 KaTeX（离线降级），退化为去掉 $ 与反斜杠后的纯文本，保证不显示乱码。
        function renderMath(text){
            if(!text)return '';
            const s=String(text);
            if(typeof katex!=='undefined' && katex.renderToString){
                return s.replace(/\$([^$]+)\$/g,function(m,tex){
                    try{ return katex.renderToString(tex,{throwOnError:false,displayMode:false}); }
                    catch(e){ return '<span class="math-plain">'+tex+'</span>'; }
                });
            }
            // 降级：去掉 $ 符号与常见 LaTeX 反斜杠命令，尽量可读
            return s.replace(/\$/g,'')
                    .replace(/\\sqrt/g,'√').replace(/\\frac/g,'/')
                    .replace(/\\pi/g,'π').replace(/\\times/g,'×').replace(/\\div/g,'÷')
                    .replace(/\\neq/g,'≠').replace(/\\geqslant/g,'≥').replace(/\\leqslant/g,'≤')
                    .replace(/\\cdot/g,'·').replace(/\\begin\{cases\}/g,'').replace(/\\end\{cases\}/g,'')
                    .replace(/\\angle/g,'∠').replace(/\\triangle/g,'△').replace(/\\parallel/g,'∥')
                    .replace(/\\perp/g,'⊥').replace(/\\circ/g,'°').replace(/\\sim/g,'∽')
                    .replace(/\\cong/g,'≌').replace(/\\ldots/g,'…')
                    .replace(/\\\\/g,' ').replace(/[\\{}]/g,'');
        }
        // 把含 $...$ 的 HTML 字符串渲染公式（用于 description 等已含 <br>/<span> 的内容）
        function renderMathHTML(html){
            if(!html)return '';
            const s=String(html);
            return s.replace(/\$([^$]+)\$/g,function(m,tex){
                if(typeof katex!=='undefined' && katex.renderToString){
                    try{ return katex.renderToString(tex,{throwOnError:false,displayMode:false}); }
                    catch(e){ return '<span class="math-plain">'+tex+'</span>'; }
                }
                return tex.replace(/\\sqrt/g,'√').replace(/\\frac/g,'/').replace(/\\pi/g,'π').replace(/\\times/g,'×').replace(/\\div/g,'÷').replace(/\\neq/g,'≠').replace(/\\geqslant/g,'≥').replace(/\\leqslant/g,'≤').replace(/\\cdot/g,'·').replace(/\\angle/g,'∠').replace(/\\triangle/g,'△').replace(/\\parallel/g,'∥').replace(/\\perp/g,'⊥').replace(/\\circ/g,'°').replace(/\\sim/g,'∽').replace(/\\cong/g,'≌').replace(/\\ldots/g,'…').replace(/[\\{}]/g,'');
            });
        }
        // 把 LaTeX 片段转成可被 TTS 朗读的口语文本（仅用于语音，不影响页面公式显示）
        // ★ v6.8：末尾追加"符号转中文"兜底替换，防止 LaTeX 之外的符号漏网
        function latexToSpeech(tex){
            let t=tex;
            t=t.replace(/\\frac\{([^{}]*)\}\{([^{}]*)\}/g,'$2 分之 $1');
            t=t.replace(/\\sqrt\{([^{}]*)\}/g,'根号 $1');
            t=t.replace(/\\sqrt/g,'根号');
            t=t.replace(/\\pi/g,'派');
            t=t.replace(/\\times/g,'乘');
            t=t.replace(/\\div/g,'除以');
            t=t.replace(/\\cdot/g,'点');
            t=t.replace(/\\neq/g,'不等于');
            t=t.replace(/\\geqslant/g,'大于等于');
            t=t.replace(/\\leqslant/g,'小于等于');
            t=t.replace(/\\ge(?![a-zA-Z])/g,'大于等于');
            t=t.replace(/\\le(?![a-zA-Z])/g,'小于等于');
            t=t.replace(/\\begin\{cases\}/g,'');
            t=t.replace(/\\end\{cases\}/g,'');
            t=t.replace(/\\\\/g,'；');
            t=t.replace(/\\ldots/g,'等等');
            t=t.replace(/\\circ/g,'度');
            t=t.replace(/\^\{([^{}]*)\}/g,' 的 $1 次方');
            t=t.replace(/\^([0-9])/g,' 的 $1 次方');
            t=t.replace(/_\{([^{}]*)\}/g,' 下标 $1');
            t=t.replace(/[\\{}]/g,'');
            t=t.replace(/\|([^|]*)\|/g,'$1 的绝对值');
            t=t.replace(/°/g,'度');
            // ★ v6.8 兜底：把 LaTeX 之外可能残留的符号也转中文
            // ⚠️ 注意顺序：Rt△ 必须在 △ 之前，否则 Rt△ 会被 △ 先替换成 "Rt三角形"
            t=t.replace(/Rt△/g,'直角三角形')
               .replace(/△/g,'三角形')
               .replace(/∠/g,'角')
               .replace(/⊙/g,'圆')
               .replace(/⊥/g,'垂直于')
               .replace(/∥/g,'平行于')
               .replace(/∽/g,'相似于')
               .replace(/≌/g,'全等于')
               .replace(/∴/g,'所以')
               .replace(/∵/g,'因为')
               .replace(/∈/g,'属于')
               .replace(/∪/g,'并集')
               .replace(/∩/g,'交集')
               .replace(/±/g,'正负')
               .replace(/≠/g,'不等于')
               .replace(/≥/g,'大于等于')
               .replace(/≤/g,'小于等于')
               .replace(/×/g,'乘')
               .replace(/÷/g,'除以')
               .replace(/√/g,'根号')
               .replace(/π/g,'派')
               .replace(/²/g,'的平方')
               .replace(/³/g,'的立方');
            return t.trim();
        }
        // 清洗 voiceText：去掉所有指令/情绪/停顿标记（[指令性][pause 2s] 等）与 $...$ 公式，输出纯口语文本
        // ★ v6.8：末尾追加"符号转中文"兜底替换，防止 Step 2 漏改时仍有符号漏网
        function cleanVoiceText(text){
            if(!text)return '';
            let t=String(text);
            // 1) 去掉所有 [xxx] 方括号标记（[指令性] / [启发性] / [pause 2s] / [转折] / [冲突] / [激励] 等）
            t=t.replace(/\[[^\]]*\]/g,'');
            // 2) 把 $...$ 公式转为口语（不朗读 LaTeX 源码）
            t=t.replace(/\$([^$]+)\$/g,function(m,tex){ return latexToSpeech(tex); });
            // 3) ★ v6.8 兜底：把可能残留的数学符号转为中文
            //    ⚠️ 注意顺序：Rt△ 必须在 △ 之前，否则 Rt△ 会被 △ 先替换成 "Rt三角形"
            t=t.replace(/Rt△/g,'直角三角形')
               .replace(/△/g,'三角形')
               .replace(/∠/g,'角')
               .replace(/⊙/g,'圆')
               .replace(/⊥/g,'垂直于')
               .replace(/∥/g,'平行于')
               .replace(/∽/g,'相似于')
               .replace(/≌/g,'全等于')
               .replace(/∴/g,'所以')
               .replace(/∵/g,'因为')
               .replace(/∈/g,'属于')
               .replace(/∪/g,'并集')
               .replace(/∩/g,'交集')
               .replace(/±/g,'正负')
               .replace(/≠/g,'不等于')
               .replace(/≥/g,'大于等于')
               .replace(/≤/g,'小于等于')
               .replace(/×/g,'乘')
               .replace(/÷/g,'除以')
               .replace(/°/g,'度')
               .replace(/√/g,'根号')
               .replace(/π/g,'派')
               .replace(/²/g,'的平方')
               .replace(/³/g,'的立方');
            // 4) 压缩多余空白
            t=t.replace(/\s+/g,' ').trim();
            return t;
        }


        function buildNavSequence(){
            const seq=[];
            if(navigationMap.totalIntro!==null&&questionData.totalIntro) seq.push({kind:'totalIntro',frame:navigationMap.totalIntro,data:questionData.totalIntro,subQuestion:null});
            questionData.subQuestions.forEach(function(sq,i){
                const sqMap=navigationMap.subQuestions[i]; if(!sqMap)return;
                sq.stages.forEach(function(stage,j){
                    const stMap=sqMap.stages[j]; if(!stMap)return;
                    if(stage.stage==='规范建模'&&stage.subSteps){
                        stage.subSteps.forEach(function(ss,k){ seq.push({kind:'subStep',frame:(stMap.frames||[])[k],data:ss,subQuestion:sq,stage:stage}); });
                    } else { seq.push({kind:stage.stage,frame:stMap.frame,data:stage,subQuestion:sq}); }
                });
            });
            if(navigationMap.finalSummary!==null&&questionData.finalSummary) seq.push({kind:'finalSummary',frame:navigationMap.finalSummary,data:questionData.finalSummary,subQuestion:null});
            return seq;
        }
        function renderQuestionTab(){
            sentenceList.innerHTML='';
            sentences.forEach(function(text){const span=document.createElement('span');span.className='sentence';span.innerHTML=renderMath(text);sentenceList.appendChild(span);});
            translatorList.innerHTML='';
            translations.forEach(function(t){const div=document.createElement('div');div.className='trans-item';div.innerHTML='<span class="orig">'+renderMath(t.original)+'</span> → <span class="math">'+renderMath(t.math)+'</span>';translatorList.appendChild(div);});
        }
        // 环节序号 → 中文圈号
        const CN_NUM=['①','②','③','④','⑤','⑥','⑦','⑧','⑨','⑩'];
        function stageNum(name){
            if(name==='审题定向')return 1;
            if(name==='破冰搭桥')return 2;
            if(name==='规范建模')return 3;
            if(name==='独立总结')return 4;
            return 0;
        }
        function stageTask(title){
            // "规范建模 · 分步推导证明" -> "分步推导证明"
            const i=title.indexOf('·');
            return i>=0?title.slice(i+1).trim():title;
        }
        // 整合步骤卡片：标题（第几问+编号+环节）+ 求证/目标 + 解题步骤累加
        function renderStepCard(node){
            stepContent.innerHTML='';
            const item=document.createElement('div'); item.className='step-item';

            // ---- 标题行 ----
            const header=document.createElement('div'); header.className='step-header';
            let tag='', idx='', title='';
            if(node.kind==='totalIntro'){
                title=node.data.title||'题目总览';
            } else if(node.kind==='finalSummary'){
                title=node.data.title||'整题总结';
            } else if(node.subQuestion){
                tag='第'+node.subQuestion.index+'问';
                const sn=stageNum(node.kind==='subStep'?'规范建模':node.kind);
                idx=CN_NUM[sn-1]||'';
                if(node.kind==='subStep'){
                    idx=CN_NUM[sn-1]+'-'+node.data.subIndex;
                    title='规范建模 · '+stageTask(node.stage.title)+' · '+node.data.stepTitle;
                } else {
                    title=node.kind+' · '+stageTask(node.data.title);
                }
            }
            if(tag){const t=document.createElement('span');t.className='sq-tag';t.textContent=tag;header.appendChild(t);}
            if(idx){const i=document.createElement('span');i.className='step-idx';i.textContent=idx;header.appendChild(i);}
            const tt=document.createElement('span');tt.className='step-title';tt.textContent=title;header.appendChild(tt);
            const cnt=document.createElement('span');cnt.className='step-count';cnt.textContent=(currentIndex+1)+' / '+navSequence.length;header.appendChild(cnt);
            item.appendChild(header);

            // ---- 内容区 ----
            const body=document.createElement('div'); body.className='step-body';
            if(node.kind==='subStep'){
                // 求证/目标行
                const goal=document.createElement('div'); goal.className='step-goal';
                goal.innerHTML='目标：'+renderMath(node.subQuestion.goal); body.appendChild(goal);
                // 解题步骤逐步累加
                const sq=node.subQuestion; let modelStage=null;
                sq.stages.forEach(function(s){if(s.stage==='规范建模')modelStage=s;});
                if(modelStage&&modelStage.subSteps){
                    const upTo=node.data.subIndex;
                    modelStage.subSteps.forEach(function(ss,k){
                        if(k<upTo){
                            const div=document.createElement('div');
                            div.className='solution-line'+(k===upTo-1?' current':'');
                            div.innerHTML=renderMath(ss.solutionLine);
                            body.appendChild(div);
                        }
                    });
                }
            } else {
                const desc=document.createElement('div'); desc.className='node-desc';
                desc.innerHTML=renderMathHTML(node.data.description||''); body.appendChild(desc);
            }
            item.appendChild(body);

            // ---- 避坑按钮（破冰环节） ----
            if(node.kind==='破冰搭桥'&&node.data.showPitfall&&node.data.pitfallContent){
                const pitBtn=document.createElement('div');pitBtn.className='pitfall-trigger';pitBtn.textContent='⚠️ 此处易错';
                pitBtn.addEventListener('click',function(){modalWrong.textContent=node.data.pitfallContent.wrong;modalRight.textContent=node.data.pitfallContent.right;modal.classList.add('show');document.body.style.overflow='hidden';});
                item.appendChild(pitBtn);
            }
            stepContent.appendChild(item);
        }
        function renderNode(index){
            const node=navSequence[index]; if(!node)return; currentIndex=index;
            renderStepCard(node);
            if(node.frame!==null&&node.frame!==undefined&&drawFunctions[node.frame]){drawFunctions[node.frame]();frameBadge.textContent='帧 '+(node.frame+1)+' / '+drawFunctions.length;}
            else {drawFrame_0();frameBadge.textContent='帧 -';}
            prevBtnFixed.disabled=(index===0); nextBtnFixed.disabled=(index===navSequence.length-1);
            nextBtnFixed.textContent=(index===navSequence.length-1)?'完成 ✅':'下一步 ➡';
            resetVoiceProgress();
            currentVoiceDuration=node.data.voiceDuration||8;
            timeLabel.textContent='0:00 / '+formatTime(currentVoiceDuration); progressSlider.value=0;
            if(currentUtterance){window.speechSynthesis.cancel();currentUtterance=null;isPlaying=false;isPaused=false;playBtn.textContent='▶';}
            stepContent.scrollTop=0;
        }
        function toggleVoice(){
            const node=navSequence[currentIndex]; const text=cleanVoiceText(node.data.voiceText); if(!text)return;
            if(!window.speechSynthesis)return;
            if(currentUtterance&&window.speechSynthesis.speaking&&!isPaused){window.speechSynthesis.pause();isPaused=true;isPlaying=true;playBtn.textContent='▶';clearInterval(progressInterval);return;}
            if(currentUtterance&&isPaused){window.speechSynthesis.resume();isPaused=false;isPlaying=true;playBtn.textContent='⏸';startProgress();return;}
            if(currentUtterance){window.speechSynthesis.cancel();currentUtterance=null;}
            const utterance=new SpeechSynthesisUtterance(text); utterance.lang='zh-CN'; utterance.rate=0.9;
            utterance.onend=function(){currentUtterance=null;isPlaying=false;isPaused=false;playBtn.textContent='▶';clearInterval(progressInterval);progressSlider.value=100;timeLabel.textContent=formatTime(currentVoiceDuration)+' / '+formatTime(currentVoiceDuration);};
            utterance.onerror=function(){currentUtterance=null;isPlaying=false;isPaused=false;playBtn.textContent='▶';clearInterval(progressInterval);};
            currentUtterance=utterance; window.speechSynthesis.speak(utterance);
            isPlaying=true; isPaused=false; playBtn.textContent='⏸';
            progressSlider.value=0; timeLabel.textContent='0:00 / '+formatTime(currentVoiceDuration); startProgress();
        }
        function startProgress(){
            clearInterval(progressInterval); const total=currentVoiceDuration; const startTime=Date.now();
            progressInterval=setInterval(function(){
                if(isPaused)return; const elapsed=(Date.now()-startTime)/1000;
                if(elapsed>=total){clearInterval(progressInterval);progressInterval=null;progressSlider.value=100;timeLabel.textContent=formatTime(total)+' / '+formatTime(total);return;}
                progressSlider.value=(elapsed/total)*100; timeLabel.textContent=formatTime(elapsed)+' / '+formatTime(total);
            },100);
        }
        function resetVoiceProgress(){clearInterval(progressInterval);progressInterval=null;progressSlider.value=0;}
        function formatTime(seconds){const m=Math.floor(seconds/60),s=Math.floor(seconds%60);return m+':'+(s<10?'0':'')+s;}
        function goToNode(index){
            if(index<0||index>=navSequence.length)return;
            if(currentUtterance){window.speechSynthesis.cancel();currentUtterance=null;isPlaying=false;isPaused=false;playBtn.textContent='▶';clearInterval(progressInterval);}
            renderNode(index); setTimeout(function(){toggleVoice();},300);
        }
        prevBtnFixed.addEventListener('click',function(){if(currentIndex>0)goToNode(currentIndex-1);});
        nextBtnFixed.addEventListener('click',function(){if(currentIndex<navSequence.length-1)goToNode(currentIndex+1);});
        playBtn.addEventListener('click',function(){toggleVoice();});
        closeModal.addEventListener('click',function(){modal.classList.remove('show');document.body.style.overflow='';});
        modal.addEventListener('click',function(e){if(e.target===modal){modal.classList.remove('show');document.body.style.overflow='';}});
        const tabBtns=document.querySelectorAll('.tab-btn');
        const tabContents={question:document.getElementById('tabQuestion'),explain:document.getElementById('tabExplain')};
        const tabBarWrapper=document.getElementById('tabBarWrapper');
        const bottomBar=document.getElementById('bottomBar');
        let currentTab='question',touchStartX=0,touchStartY=0,isSwiping=false;
        tabBtns.forEach(function(btn){btn.addEventListener('click',function(){switchTab(this.dataset.tab);});});
        tabBarWrapper.addEventListener('touchstart',function(e){touchStartX=e.touches[0].clientX;touchStartY=e.touches[0].clientY;isSwiping=false;},{passive:true});
        tabBarWrapper.addEventListener('touchmove',function(e){const dx=e.touches[0].clientX-touchStartX,dy=e.touches[0].clientY-touchStartY;if(Math.abs(dx)>Math.abs(dy)&&Math.abs(dx)>30){isSwiping=true;e.preventDefault();}},{passive:false});
        tabBarWrapper.addEventListener('touchend',function(e){if(!isSwiping)return;const dx=e.changedTouches[0].clientX-touchStartX;if(dx<-50&&currentTab==='question')switchTab('explain');else if(dx>50&&currentTab==='explain')switchTab('question');isSwiping=false;},{passive:true});
        function switchTab(tab){
            if(tab===currentTab)return; currentTab=tab;
            tabBtns.forEach(function(b){b.classList.toggle('active',b.dataset.tab===tab);});
            Object.keys(tabContents).forEach(function(key){tabContents[key].classList.toggle('active',key===tab);});
            // 底部导航栏只在"讲解"Tab 显示；"试题"Tab 隐藏
            if(bottomBar)bottomBar.classList.toggle('show',tab==='explain');
            if(tab==='explain'){if(!stepContent.children.length)renderNode(currentIndex);setTimeout(function(){toggleVoice();},400);}
            else {if(currentUtterance){window.speechSynthesis.cancel();currentUtterance=null;isPlaying=false;isPaused=false;playBtn.textContent='▶';clearInterval(progressInterval);}}
        }
        navSequence=buildNavSequence();
        renderQuestionTab(); renderNode(0);
        window.addEventListener('resize',function(){clearTimeout(window._resizeTimer);window._resizeTimer=setTimeout(function(){const node=navSequence[currentIndex];if(node&&node.frame!==null&&node.frame!==undefined&&drawFunctions[node.frame])drawFunctions[node.frame]();},200);});
        console.log('✅ 讲题页面已加载完成，共 '+navSequence.length+' 个导航节点');
    </script>
</body>
</html>
```

---

# ⛔ 不得改动的七样东西（v6.8 更新，最高优先级）

> 你是「前端工程师」，本能会做整理、重命名、删掉「看起来没用」的代码。**下面七样一旦动了，前面所有工作全部作废**。

| # | 不得改动的东西 | 为什么 | 自查方法 |
|---|---|---|---|
| 1 | 顶部的 `window.__DRAW_TIER__ = 'A' / 'B' / 'C';` | **它不是调试变量，是裁决依据**。检查方靠它判断「这道题该按哪一档验收」。删掉或改值 = 后续质检全部走错档 | 搜索 `__DRAW_TIER__`，确认还是第三步写的那一行、值没变 |
| 2 | `const LIB = (function(){ ... })();` 里的**两块正文**（几何内核 + 绘图层） | 里面的 `drawMathText` 就是**画布文字白名单**本身；里面的 `CK()` 就是**唯一的判定标准**。改它 = 自己重写判定标准 | 确认 `LIB` 是**一整块**、没被拆成两段、没被「整理」；确认 `const pts = LIB.pts;` 仍紧跟其后 |
| 3 | 每个 `drawFrame_N()` 的**末行** `finishFrame();` | 它负责画 `CK n/n` 角标。动画每个 tick 都会清屏，**角标必须每帧重画** | 搜索 `function drawFrame_`，逐个确认函数体最后一句是 `finishFrame();` |
| 4 | 末尾的 `CKDrawViolations()` 与 `CKSummary()`，**以及它们的先后顺序** | `CKDrawViolations()` 把「画布白名单违规」计入校验；顺序反了会漏掉这一项 | 搜索这两个名字，确认 `CKDrawViolations()` 在 `CKSummary()` **之前** |
| 5 | ★ **`const qAcc = {}; let currentQ = 1; function switchQ(q){...} function recQ(item){...}` 四个声明**（v6.7 起提升为必查项） | 它们是**持久/临时分离的核心机制**——`recQ` 是唯一的持久层入口，`switchQ` 是切小问的关键。删掉任一个，**累积机制整体失效** | 搜 `const qAcc` / `function switchQ(` / `function recQ(`，**三个声明都在、函数体完整、没有被内联或删掉** |
| 6 | ★ **产物末尾的「抄写自检日志」注释块** | 它是第 3.5 步核对**抄写失真**的依据。它长得像"无用注释"，很容易被"整理代码"时删掉 | 搜索 `抄写自检日志`，确认整个注释块 **完整保留**、**未删任何一条** |
| 7 | ★ **渲染引擎里的 `cleanVoiceText` 与 `latexToSpeech` 函数**（v6.8 起提升为必查项） | 它们是**语音清洗的第二道防线**——`cleanVoiceText` 负责去掉 `[指令性]` / `[pause 2s]` 等标记 + 兜底符号转中文；`latexToSpeech` 负责把 `$...$` 里的 LaTeX 转口语。删掉任一个，语音会读出奇怪符号或方括号标记。**特别注意 `Rt△` 的替换必须在 `△` 之前**（顺序反了会把 `Rt△` 误替换为 `Rt三角形`） | 搜 `function cleanVoiceText` / `function latexToSpeech`，**两个函数体都在、都含符号转中文兜底替换、`Rt△` 替换在 `△` 之前** |

> **另有一条最容易踩的**：
> 第三步产出里**没有** `canvasEl` / `ctx` 这两行——它们属于本模板（见「数据区 3-前置」）。替换绘图代码时**不要把这两行一起覆盖掉**，否则 `ctx` 变 `undefined`，整张画布不再绘制。

> **★ 兜底替换的边界（v6.8 明确）**：
>
> 第四步兜底**只处理"纯数学符号"**（`△` `∠` `⊥` `∥` `∽` `≌` `⊙` `°` `√` `π` `²` `³` `×` `÷` `±` `≠` `≥` `≤` `∴` `∵` `∈` `∪` `∩`）——这些是**跨字面量的图形/单位/关系符号**，替换成中文**只有唯一读法、零副作用**。
>
> **第四步兜底不处理以下符号——它们由第二步保证，第四步不兜**：
> - **`=`**：`=` 换成"等于"会把非数学语境里的 `=` 也误替换（如 URL 参数、JSON 键值对）；且 `=` 在 TTS 中通常读作"等于"，风险较低。
> - **`+` `-`**：`-` 换成"减"会把连字符（如 "5-3题" 中的连接号）也误替换。
> - **`(` `)` `[` `]` `{` `}`**：这些括号在 TTS 里默认不读或轻读，替换为"括号"反而**产生噪音**。
> - **`α` `β` `θ`** 等希腊字母：TTS 通常能读（读作 "alpha" / "beta" / "theta"），不必强制换。
> - **`/`**：分数斜杠的替换（如 `CB/CA` → "CB 比 CA"）**只在上下文明确时**才成立，`/` 也可能是 URL 或正则的一部分；**由第二步保证**，第四步不兜。
>
> **一句话总结**：第四步兜底覆盖**约 20 个"图形/单位/关系"类符号**；**`=` `+` `-` `(` `)` `α` `β` `θ` `/` 由第二步负责**。**第二道防线不是"万能替换"——它的边界是"替换有唯一读法、零副作用的符号"。**

---

# 数据填写位置对照表

| 数据项 | 模板中的位置 | 来源 |
|--------|-------------|------|
| `sentences` | 替换 `const sentences = [...]` | 第一步产出 |
| `translations` | 替换 `const translations = [...]` | 第一步产出 |
| `questionData` | 替换 `const questionData = {...}` | 第二步产出 |
| 档位声明 `window.__DRAW_TIER__` | 替换数据区 3 首行 | 第三步产出 |
| `W/H` + `COLORS` + **两块内联库 `LIB`** | 替换数据区 3（`LIB` 整段粘贴，一字不改） | 第三步产出 |
| 解构语句（`const pts = LIB.pts; const {...} = LIB;`） | 替换数据区 3（**不含 `recordToAccumulator`**） | 第三步产出 |
| ★ **`qAcc / switchQ / recQ` 三个辅助** | 替换数据区 3（紧跟解构语句之后） | 第三步产出 |
| `drawBaseScene` / `drawQnBase` | 替换 `function drawBaseScene()` | 第三步产出 |
| `drawFrame_N` | 替换 `function drawFrame_0()` 等 | 第三步产出 |
| `navigationMap` | 替换 `const navigationMap = {...}` | 第三步产出 |
| `drawFunctions` | 替换 `const drawFunctions = [...]` | 第三步产出 |
| ★ **「抄写自检日志」注释块** | 替换数据区 3 末尾（**紧跟 `drawFunctions` 之后**） | 第三步产出 |
| `QUESTION_TITLE` | 替换为题型名称 | 手动填写 |

---

# 检查清单（输出前逐项自查）

## 数据完整性
- [ ] `sentences` / `translations` 是否已替换为第一步数据？
- [ ] `questionData` 是否完整包含 `questionType`、`totalIntro`（可 null）、`subQuestions`、`finalSummary`（可 null）？
- [ ] 每个小问的 `stages` 是否包含四环？规范建模是否含 `subSteps`？
- [ ] **`questionData` 中是否不含 `highlight` 字段**（已移除，无需输出）？
- [ ] 绘图代码（档位声明 `window.__DRAW_TIER__`、`W/H`、`COLORS`、**`LIB` 整段**、**解构语句（不含 `recordToAccumulator`）**、**`qAcc/switchQ/recQ`**、`drawBaseScene`、`drawFrame_N`、`navigationMap`、`drawFunctions`、**「抄写自检日志」注释块**）是否已完整替换？

## ★ v6.6 绘图标志物（逐项必查）
- [ ] ★ **`LIB` 是否整段粘贴**（两块内联库都在，一字不改、顺序不调）？
- [ ] ★ **是否没有自己重写 `drawXxx` / `clearCanvas` / `replayAccumulator` / `stopAnim`**？
- [ ] ★ **解构语句是否包含 `recordToAccumulator`**？（**应为"否"**）
- [ ] ★ **`qAcc / switchQ / recQ` 三个辅助是否已保留**？（**四个声明**）
- [ ] ★ **每个 `drawFrame_N()` 的末行是否 `finishFrame();`**？
- [ ] ★ **`CKDrawViolations()` 是否在 `CKSummary()` 之前**？
- [ ] ★ **产物代码里 `console.assert` 命中数是否为 0**？
- [ ] ★ **每条 `CK()` 是否恰好 4 个参数**？
- [ ] ★ `window.__DRAW_TIER__` 是否仍在代码顶部、值未被改动？
- [ ] ★ **末尾「抄写自检日志」注释块是否完整保留**？

## ★ 语音可播性检查（v6.8 新增）

- [ ] ★ **`cleanVoiceText` 是否包含「符号转中文」的兜底替换**（`△`→"三角形"、`∠`→"角"、`⊥`→"垂直于"、`∥`→"平行于"、`∽`→"相似于"、`≌`→"全等于"、`°`→"度"、`√`→"根号"、`π`→"派"、`⊙`→"圆"、`²`→"的平方"、`³`→"的立方" 等）？
- [ ] ★ **`Rt△` 的替换是否放在 `△` 之前**？（顺序反了会把 `Rt△` 误替换为 `Rt三角形`）
- [ ] ★ **`latexToSpeech` 函数末尾是否也包含同样的符号转中文兜底替换**？
- [ ] ★ **`toggleVoice` 是否用 `cleanVoiceText(node.data.voiceText)` 而非原始 `voiceText`**？
- [ ] ★ **`cleanVoiceText` 是否去掉了所有 `[xxx]` 方括号标记**（`[指令性]` / `[pause 2s]` / `[转折]` 等）？
- [ ] ★ 播放语音时，**是否听不到任何符号**（"三角形""角""垂直于"都读成中文，而不是奇怪的音）？

## ★ 输出格式检查（v6.6 硬性）
- [ ] ★ **产物开头第一行是否为 `<!DOCTYPE html>`**（**不带"这是根据…"说明前缀**）？
- [ ] ★ **产物是否未被 ` ```html ` / ` ``` ` 包裹**？
- [ ] ★ **产物是否不带任何说明后缀**？

## 变量命名与语法检查（防 SyntaxError）
- [ ] 绘图代码是否**原样粘贴**，没有改任何变量名？
- [ ] 替换后**是否没有单字母变量冲突**？
- [ ] 替换后 JS 语法是否可运行（无 `SyntaxError`、无 `ReferenceError`）？
- [ ] **【引号铁律·必查】** 填入 `questionData` 的所有字符串字段中，**是否没有未转义的英文双引号 `"`**？
  - **自查法**：每个 `字段名: "..."` 行内，非转义英文双引号必须恰好 2 个
- [ ] **【省略占位符·必查】** 粘贴 Step 3 绘图代码后，代码中**是否没有 `...` 残留**？
- [ ] **【空白页排查】** 若页面空白，优先按此顺序检查：① 打开控制台看 `SyntaxError` ② 定位报错行是否含裸引号 ③ 是否为 `...` 省略占位符残留 ④ 检查 `drawFunctions` / `navigationMap` 帧号是否连续 ⑤ 检查 CSS 是否有 `display:none` 未复位

## 导航与映射
- [ ] `navigationMap.subQuestions[i]` 是否与 `questionData.subQuestions[i]` 一一对应？
- [ ] 规范建模的 `frames` 数组长度是否等于对应 `subSteps.length`？
- [ ] `drawFunctions` 是否覆盖所有帧号（0 ~ 最大帧号）？

## 页面结构（桌面端布局 v6.9）
- [ ] Tab 切换栏是否**在页面顶部**、整页是否**限宽居中**（`--page-max:1200px` / `--page-min:680px`）？
- [ ] 讲解 Tab 是否只包含"绘图 + 整合步骤卡片 + 底部栏"？
- [ ] 讲解 Tab 上方是否为 **`.explain-top` 左右并排**（绘图 `.canvas-wrap` ｜ 步骤 `.step-content`，`grid-template-columns:1fr 1fr`，1:1）？
- [ ] 底部栏 `.bottom-bar` 是否**位于讲解 Tab 容器（`#tabExplain`）内底部**（不是 body 直属）？
- [ ] 是否保留 `@media (max-width:760px)` 窄屏回退（`.explain-top` 转单列）？
- [ ] **步骤卡片标题**是否遵循 `第X问 编号 环节·任务` 格式？
- [ ] **每个小问是否重新从①开始编号**？整题总起/终局总结是否无编号？
- [ ] 规范建模子步骤卡片是否包含"目标行 + 解题步骤逐步累加（当前行高亮）"？
- [ ] 破冰环节是否显示避坑按钮，点击弹出正确内容？

## 渲染引擎（保持原样）
- [ ] CSS、HTML 结构、JavaScript 渲染引擎是否**完全保留**、未做任何修改？
- [ ] 是否**没有**任何题干高亮（highlight）相关代码？
- [ ] 是否**没有**填空（hasBlank）、总结卡片（isSummary）、变式（hasVariant）、错因（hasErrorDiagnosis）相关代码？
- [ ] **是否保留了 KaTeX 引入 + `renderMath`/`renderMathHTML`/`cleanVoiceText`/`latexToSpeech` 四个工具函数**（**v6.8 起后两者含符号转中文兜底**）？

## 公式渲染（v3 新增）
- [ ] `<head>` 中是否引入了 KaTeX 的 CSS 与 JS（**同步加载、无 defer**）？
- [ ] `renderQuestionTab` 是否用 `renderMath()` 渲染了题干句子与翻译器？
- [ ] `renderStepCard` 的目标行、解题步骤 `solutionLine` 是否用 `renderMath()` 渲染？
- [ ] 环节 `description` 是否用 `renderMathHTML()` 渲染？
- [ ] 打开页面后，`$...$` 是否已变成真正的数学公式？

## 底部栏显示（v3 新增）
- [ ] `.bottom-bar` 是否**默认 `display:none`**、加 `.show` 时才 `display:flex`？
- [ ] `switchTab` 中是否用 `bottomBar.classList.toggle('show', tab==='explain')` 控制？

## 页面功能
- [ ] 页面加载后默认显示试题 Tab，点击/滑动可切换到讲解 Tab？
- [ ] 讲解 Tab 按导航序列逐节点推进，卡片标题正确显示当前"第几问 + 步骤编号"？
- [ ] 规范建模子步骤时，解题步骤是否**逐行累加**（每进一子步骤追加一行，新增行高亮）？
- [ ] 切换节点时画布是否正确切换到对应帧（`drawFunctions[frame]`）并播放动画？
- [ ] 语音是否自动播放、可暂停/继续、进度条同步、结束恢复 ▶？
- [ ] 底部栏位于讲解 Tab 内底部（上方左右两栏 / 下方整行），内容不被遮挡？

---

# 【用户输入】
请将以下内容作为输入：

**第一部分：Step 1 产出的 sentences**
[请粘贴第一步的 sentences 数组]

**第二部分：Step 1 产出的 translations**
[请粘贴第一步的 translations 数组]

**第三部分：Step 2 产出的完整讲题方案对象**
[请粘贴第二步的完整输出（含 questionType、totalIntro、subQuestions、finalSummary；**voiceText 已全中文化**）]

**第四部分：Step 3 产出的完整绘图代码**
[请粘贴第三步的完整输出（含 window.__DRAW_TIER__ 档位声明、W/H、COLORS、两块内联库 const LIB = (function(){几何内核 + 绘图层})()、解构语句（不含 recordToAccumulator）、qAcc/switchQ/recQ 三个辅助、构造与校验区 const pts = LIB.pts、drawBaseScene、drawFrame_N（六层结构）、navigationMap、drawFunctions、末尾「抄写自检日志」注释块）]

---

★ **输出格式要求（硬性）**：

请根据以上规则生成 HTML：

1. **只输出 HTML 代码本身** —— 开头第一行直接是 `<!DOCTYPE html>`；
2. **不带任何说明前缀**，例如：
   - ❌ "这是根据您提供的输入材料生成的完整 HTML 文件。它包含…"
   - ❌ "以下是整合后的 HTML："
3. **不用 Markdown 代码块包裹**（不要 ```html / ```）；
4. **保留第三步产出末尾的「抄写自检日志」注释块**（整段不动，一字不改）。
```

---

## 本次 v6.8 改了什么（一页速查）

| # | 位置 | v6.7 | v6.8 |
|---|---|---|---|
| 1 | 顶部版本块 | v6.7，3 条 | **v6.8，3 条新改动 + 保留 v6.7 / v6.6 / v5 / v4 / v3 / v2 全部历史要点** |
| 2 | 输入材料第 3 项 | 未提 `voiceText` 中文化 | **补一句**："**`voiceText` 已全中文化**——所有数学符号已改写为中文，但**方括号标记 `[指令性]` / `[pause Xs]` 等保留**" |
| 3 | **`latexToSpeech` 函数** | 末尾直接 `return t.trim();` | **新增符号转中文兜底替换**（`Rt△` → `直角三角形` → `△` → `三角形` → `∠` → `角` … 共 20+ 条替换；**`Rt△` 在 `△` 之前**） |
| 4 | **`cleanVoiceText` 函数** | 3 步（去方括号 → LaTeX → 压空白） | **改为 4 步**：① 去方括号 ② LaTeX 转口语 ③ **★ 兜底：符号转中文** ④ 压空白。**同样注意 `Rt△` 在 `△` 之前** |
| 5 | **「不得改动的六样」→「七样」** | 节标题 + 6 行表格 + "另有一条"（含 `qAcc` / `cleanVoiceText` / `latexToSpeech` 的补充说明） | **节标题改为"七样"** + 表格**加第 7 行**（`cleanVoiceText` / `latexToSpeech`）+ **下方新增「兜底替换的边界」专段**（明确只覆盖约 20 个"纯数学符号"；`=` `/` `+` `-` `(` `)` `α` `β` `θ` 由第二步保证） |
| 6 | 检查清单 | 无语音可播性组 | **新增「★ 语音可播性检查」组（6 条）** |
| 7 | 数据填写位置对照表 | 无变化 | **无变化** |
| 8 | 渲染引擎检查清单 | "保留四个工具函数" | **补充**："v6.8 起后两者含符号转中文兜底" |
| 9 | 【用户输入】第三部分 | 未提 voiceText 中文化 | **补充**："voiceText 已全中文化" |

---

## 本次 v6.8.1 改了什么（一页速查）

| # | 位置 | v6.8 | v6.8.1 |
|---|---|---|---|
| 1 | 顶部版本块 | v6.8，3 条 | **v6.8.1，1 条新改动 + 保留 v6.8 / v6.7 / v6.6 / v5 / v4 / v3 / v2 全部历史要点** |
| 2 | 数据区 3 骨架前的 ⚠️ 提示 | 只提醒 `/* 完整实现 */` 这类**显性**占位 | **新增「伪真数字占位」专项警告**："帧号从 0 连续排到最大帧号，不得跳号，不得出现孤立的大数字" |
| 3 | 骨架 `navigationMap.finalSummary` | `30`（伪真数字占位） | **`10`**（与「独立总结」frame 9 紧接），并加注释说明"实际产出时按真实帧数写" |
| 4 | 骨架 `drawFunctions` | 只列 2 项 + `/* 完整实现：后续帧 */` 注释代替 | **逐帧列全 `drawFrame_0 … drawFrame_10`**（共 11 项），并注明"长度 = 最大帧号 + 1" |
| 5 | 骨架 `drawFrame_N` 定义区 | `drawFrame_0` / `drawFrame_1` 两行 | **补注释**："每个帧号都要有一个 `drawFrame_N`，N 从 0 连续到最大帧号" |

---

**第四步 v6.8.1 输出完成。整条流水线（0928 修正版）全部收尾。**

| 步骤 | 版本 | 状态 |
|---|---|---|
| **第一步** | **v3.1**（few-shot 违规样本修正 + 版本头补齐） | ✅ |
| **第二步** | **v3.1**（权重表补足 100% + few-shot 标记补齐 + 补 logicType + `$...$` 口径统一 + 名称统一 + 删过期便签） | ✅ |
| **第三步** | **v6.7.1**（档位声明口径 + `SPACING_MIN` 澄清 + 删过期便签） | ✅ |
| **第 3.5 步** | **v6.7.1**（`$...$` 例外 + 30px 澄清 + 编号修正 + 删过期便签） | ✅ |
| **第四步** | **v6.8.1**（骨架伪真数字占位修正） | ✅ |

**整条流水线的"语音可播性"链路现在完全闭环：**

1. **第二步**（源头）：`voiceText` 全中文化（禁止 `△` `∠` `⊥` `=` `/` 等符号），**方括号标记保留**。
2. **第三步**：生成绘图代码，不涉及 `voiceText`。
3. **第 3.5 步**（检查）：核对 `voiceText` 无数学符号、方括号标记保留、第四步模板含兜底；发现残留**打回 Step 2**。
4. **第四步**（第二道防线）：`cleanVoiceText` + `latexToSpeech` 加符号转中文兜底，即使第二步漏改也能兜住；**兜底边界明确**（`=` `/` `+` `-` `(` `)` 由第二步保证）。

**播放时用户听到的效果**：`△BCE` → "三角形BCE"；`∠ACD` → "角ACD"；`[指令性]` / `[pause 2s]` → **完全静默**（被 `cleanVoiceText` 清洗）；所有符号都读成中文，**听不到任何奇怪的英文符号名**。