---
name: cnki-edu-math-ai-lecture
display_name: AI 讲题
display_name_en: AI Problem Walkthrough
description: 初中数学试题一键生成 AI 讲题网页：画布动画 + 语音旁白 + 步骤卡片，离线单文件可直接运行。
description_zh: 初中数学试题一键生成 AI 讲题网页：画布动画 + 语音旁白 + 步骤卡片，离线单文件可直接运行。
description_en: 'One-shot pipeline that turns a single junior-high math question into a runnable interactive lecture web page. The teaching paradigm and quality gates are strictly preserved; the full-chain speedup acts only on the mechanical input/output side: script-generated navigation structure, report/patch-only Step 3.5 (no full code re-transcription), script-assembled Step 4 (no full HTML re-write), one-command mechanical checks, tiered reading of reference docs.'
category: education
version: 1.0.1
author: 知网 edu
---

# 初中数学 AI 讲题 · cnki-edu-math-ai-lecture

> **一句话**：用户发一张初中数学试题图 → 召回题库标准解析 → 产出**一个可直接运行的单页 HTML**。
>
> 本 skill 是「题库召回（S0）」+ 原有五步提示词（Step 1 / 2 / 3 / 3.5 / 4）的**编排外壳**。
> 五步提示词的方法论与约束**原样保留**，本 skill 只负责：把输入接上、把步骤串起来、把易错环节脚本化。

---

## 〇、v2 相对原版改了什么（一张表）

> **原则**：**讲题范式、质量铁律、22 项体检、CK 硬门槛、voiceText 中文化——一条不改**。v2 砍掉的全部是「**让模型重抄已经存在的文本**」。

| 环节 | 原版 | v2 | 效果 |
|---|---|---|---|
| **S3 结构层** | 模型手写 `navigationMap` + `drawFunctions` | 产物写一行 `/* @@STRUCTURE@@ */` → `scripts/build-structure.js` 按 S2 展开 | 消除帧号错位类错误；结构确定性 |
| **S3.5 输出** | 报告 + **整份代码重抄一遍**（实测 80.5 KB，零修正也照抄） | 报告 + `/* @@NO_CHANGE@@ */`（或 `@@CHANGES_BEGIN/END` 局部补丁）→ `scripts/apply-s3.5.js` 装配 | 模型输出 **−95%**；**抄写失真归零** |
| **S4 组页** | 模型**整页重写 HTML**（≈126 KB，含 76.8 KB 内联库再抄一遍） | `scripts/assemble-html.js` 脚本装配（模板 + S1/S2/S3） | 模型输出 **→ 0**；零截断 |
| **机械校验** | 8 个独立命令散跑 | `scripts/run-s3-checks.js` **一条命令**跑完（含内联库注入） | 少 7 轮工具往返 |
| **S2 输入** | 四份方法论全文（79.9 KB） | **分级**：常规题读 `00-essence.md`（16.2 KB）；难题读四篇全文 | 输入 **−64%**（常规题） |

**质量只增不减**：不重抄 = 抄写失真归零；机械项由脚本独立复算，报告只能引用不能自造。

---

## 〇bis、v2 执行纪律（★ 最省时的一条，零成本）

1. **一次任务在一个会话内连续跑完**；**禁止中途 `/compact` 或让会话被摘要切分**——本项目实测：一次 41 分钟的异常，根因就是"压缩 → 已读进上下文的 references 被丢弃 → 下一步整套重读"（同一段输入，正常 118.7 s，被拉到 20+ min）。
2. **跨阶段要换上下文时**：把中间态**落到临时文件**（`s1.js` / `s2.js` / …），**开新会话继续**，而**不是**靠压缩续命。
3. **参考文件批读**：本阶段要用的 `references/` 在**一个批次**里一次读完，减少往返。
4. **S3 不读四份方法论**（它们只在 S2 读）；S3 的输入＝试题图 + 题库解析 + S1 产物 + S2 产物。
5. 输出阶段加一句约束：**「本题为代码/结构生成，直接产出结果，不要展开推理过程」**。

---

## 一、产物形态

最终交付一个 HTML 单页，含：

| 区域 | 内容 |
|---|---|
| 上方画布 | Canvas 360×260，几何图形**逐帧动画**（持久元素累积 / 临时强调随讲随撤） |
| 右下角标 | `CK n/n` 绿底角标（**硬门槛**，红底或 `CK --` 一律视为未交付） |
| 下方卡片 | 整合步骤卡：标题行 + 目标行 + 解题步骤逐步累加 + 避坑按钮 |
| 试题 Tab | 题干 + 数学语言翻译器（Step 1 产出） |
| 语音 | TTS 旁白，与画布动画同步（"声图联动"） |

---

## 二、开始前的前置检查（必做）

0. **🔐 前置权限校验（最高优先级，必须最先执行）**：本 skill 依赖 edu 题库 MCP（`mcp__<SERVER>__tkSearchQuestion` / `mcp__<SERVER>__tkQuestionAnalysis` 等），需账号拥有「知网基教」权益才能调用。进入任何生成环节、**调用任何 `tk*` 工具之前**，先调 `mcp__<SERVER>__userState`（edu MCP 的权益校验接口，**无参数**；工具名前缀取自连接器「显示名」，会随重命名变化，查不到时用 `ToolSearch(tool_names:["userState"])` 反查）。

> 权限校验的「三态诊断 / 通用版兜底 / 强制转化卡 / 连接器加载指引」统一见本技能 `references/_shared.md`「一、权限固定提示」，本章节仅保留本技能专属说明，不重复展开。

> **本技能属②档弱依赖**：讲题网页本体可由模型直接产出，知网题库召回仅作标准解析/溯源增强层；无权益/未连接时走通用版并标注「⚠ 通用版 · 非知网标准解析」（详见 `references/_shared.md`「一、权限固定提示」）。
   - **返回 `true`** → 具备知网基教权益，继续下方检查。
   - **明确返回 `false`（态 B）** → 视为**未开通知网基教权益**：按`references/_shared.md`「一、权限固定提示」「通用版兜底 + 强制转化卡」处理（不调用任何 `tk*` 工具、不编造知网数据、不伪造 CNKI 溯源），并原样输出「解锁知网数据增强层」（原文见 [_shared.md](references/_shared.md)「权限固定提示」）；随后**继续产出讲题网页（通用版）**，交付物开头标注「⚠ 通用版 · 未接入知网基教，解析由模型生成、非知网标准解析」。
   - **态 A｜工具不可达**（`ToolSearch` 查不到 `userState`）→ 连接器未加载/掉线，按`references/_shared.md`「一、权限固定提示」给「连接器加载指引」（**非阻塞提示，不中止流程**）、**不**输出转化卡，也不要调用任何 `tk*` 工具；随后**转入通用版流程继续产出讲题网页**。
   - 不得把失败原因解释成别的（不要说"题库没这题""接口有问题"）——`mcp__<SERVER>__userState` 校验非 `true` 的根因就是没权限 / 没连接。

> **知网依赖度（本技能适用 · ② 弱依赖 / 可选增强）**：讲题网页本体（四环三阶讲解 + 画布动画 + 语音）可由模型基于题干与图形**直接产出**；知网题库召回（`mcp__<SERVER>__tkSearchQuestion` / `mcp__<SERVER>__tkQuestionAnalysis`）只作为**标准解析 / 溯源增强层**——命中时挂上权威解析，缺失时降级为模型通用讲解。**权益 ≠ 闸门**：无权益 / 未连接时仍产出讲题网页（通用版），仅在交付物开头标注「⚠ 通用版 · 未接入知网基教，解析由模型生成、非知网标准解析」，且**严禁编造**任何知网数据与 CNKI 溯源。
1. **题库 MCP 是否可用（连接层）**：已通过权益校验后，确认 `mcp__<SERVER>__tkSearchQuestion` / `mcp__<SERVER>__tkQuestionAnalysis` 可调用（连接器已启用、工具可装载）。若连接器未启用 / 工具装载失败 → 视为**态 A（未接入知网 edu 连接器）**，按 `references/_shared.md`「一、权限固定提示」给「连接器加载指引」、**不**输出转化卡（不要用模型自行解题替代）。
2. **输入是否是一张试题图**：若用户只给文字，可以继续（Step 1 支持文本输入），但要明确告知"无原图，图形关系靠文字推断，画布还原度会下降"。
3. **学段学科**：本 skill 当前只覆盖**初中数学**（`subjectCode = 20`）。其他学段/学科请先确认。

---

## 三、流水线总览

```
用户发图
  │
  ├─ S0  识题 + 题库召回  ── 命中 → 拿到标准解析 JSON
  │                        └─ 未命中 / 无连接器 / 无权益 → 转入通用版（模型生成解析，继续 S1→S4）
  │
  ├─ S1  试题结构化        → { sentences, translations }        （裸 JS 对象）
  ├─ S2  讲题方案          → questionData 对象（四环三阶 + voiceText 全中文）
  ├─ S3  绘图代码          → 档位声明 + LIB + 构造区 + drawFrame_N + /* @@STRUCTURE@@ */
  │        ├─ 模式 A（full）：模型整段粘贴两块内联库
  │        └─ 模式 B（slim）：模型只写注入标记 → scripts/assemble-artifact.js 注入真源  ★ 推荐
  │        └─ v2：结构层（navigationMap/drawFunctions）由 scripts/build-structure.js 展开 ★
  ├─ S3.5 代码校对         → 报告 + 变更区块（v2：不重抄代码）→ scripts/apply-s3.5.js 装配
  └─ S4  整合 HTML         → ★ v2：scripts/assemble-html.js 脚本装配（模板 + S1/S2/S3）
```

**v2 一条命令收口**（S3 之后到交付）：

```bash
node scripts/build-structure.js <s2.js> --inject <s3-raw.js> --out <s3.js>   # 展开结构层
node scripts/run-s3-checks.js   <s3.js> --s2 <s2.js> --dump <s3.assembled.js> # 注入内联库 + 32 项体检
# …（S3.5 模型校对 → 产出报告 + @@NO_CHANGE@@ / @@CHANGES@@）
node scripts/apply-s3.5.js      <报告产物> <s3.assembled.js> --out <s3.5.js>  # 装配（零修正走 NO_CHANGE）
node scripts/assemble-html.js   <s1.js> <s2.js> <s3.5.js> --qtitle "题型" --out <讲题.html>
```

**逐步执行时**：每一步都要把对应的 `references/` 文件**完整读入**当作该步的提示词正文使用，并严格按其「输出格式」约束产出（裸对象 / 裸代码 / 裸 HTML，不带 Markdown 包裹、不带说明前缀）。

---

## 四、S0 · 识题 + 题库召回

> 口径（2026-10-21 修订）：召回命中即用知网标准解析；召回不到 / 无连接器 / 无权益时**不编造知网数据**，由模型基于题干 + 图形生成「通用版解析」继续后续流程（S1→S4），交付物开头标注非知网标准解析。

1. **读图**：用多模态能力读出题干全文、图形关系（点/线/角/位置）、图中标注（如 `AB=6`、`∠ABC=90°`）。
2. **关键词召回**：`mcp__<SERVER>__tkSearchQuestion({ keyword, subjectCode: 20, ps: 5, pi: 1 })`
   - 关键词取**最长、最独特**的题面子串（图形结构 + 关键条件 + 求证目标拼成一句话），避免只用"旋转""相似"这类高频词。
   - **🔴 接口硬约束（实测踩坑）**：`keyword` 不得含**空格 / `∠` / `=` / `°` / 标点**等符号，否则接口直接返回 **400**。必须用「**长串无空格的中文子串**」，例如 `正方形的边CD绕点D逆时针旋转`、`过点P作AB的垂线`。含空格的多词（`"正方形 旋转 平分"`）必 400，单个汉字（`"旋转"`）可正常返回。
3. **候选打分比对**：对每条候选按 ① 题干关键条件是否齐全 ② 图形结构是否一致 ③ 小问数量与目标是否一致 打分，选出最优（优先看 `sid` 是否等于金标准；命中位置通常在前 5 内）。
4. **取解析**：`mcp__<SERVER>__tkQuestionAnalysis({ SID, subjectCode: 20 })` → 返回 `Analyse / Method / Discuss / DisplayAnswer / Points / Topics/ SubStruct` 全字段。
5. **兜底召回**（第 2 步关键词召回为空时）：
   - `mcp__<SERVER>__tkPoint({ subjectCode: 20 })` 取考点列表 → `mcp__<SERVER>__tkSearchSubjectQuestion({ point: [...], subjectCode: 20, ps, pi, dg: 0 })`
6. **未命中 / 无连接器 / 无权益处理**：以下四种情形统一转入通用版，**不编造知网数据**、不停止任务：
   - 关键词召回无候选；
   - 兜底召回（第 5 步）无候选；
   - 连接器不可用（态 A，工具不可解析）；
   - 权益校验非 `true`（态 B）。
   均由模型基于题干 + 图形生成解析，继续 S1→S4；交付物开头以「⚠ 通用版 · 未接入知网基教，解析由模型生成、非知网标准解析」标注。通用版解析仅供参考，知网标准解析需接入后获取。
7. **通用版装配**：通用版流程在 S4 调用 `assemble-html.js` 时加 `--generic` 标志（如 `node scripts/assemble-html.js <S1.js> <S2.js> <S3.js> --generic --out <讲题.html>`），脚本会在页面顶部注入「⚠ 通用版」标注横幅（替换模板占位 `<!-- @@GENERIC_BANNER@@ -->`）。态 B 仍另在文末原样输出「解锁知网数据增强层」转化卡。

### ⚠️ 合规约束（来自题库方 API 约定，必须遵守）

- 试题内容**不可本地缓存**：召回结果只放在**临时文件**里，流程结束即清理。
- **不可用后台程序直接调用**题库接口：必须是用户在场的一次性交互。
- 有**调用次数限制**：不做定时/批量抓取；同一道题最多重试 2 次召回。

### S0 实测（2026-09-29 · V3.0 验证集 6 道真题）

用各题目录下的 `解析.txt`（题库标准解析 JSON，含金标准 `sid`）作金标准，实测关键词召回能否命中同一题：

| 题 | 主题 | 召回关键词（长串无空格） | 命中位置 | 命中金标准 sid |
|---|---|---|---|---|
| 试题4 | 图形的对称 | `四边形ABCD沿CD翻折` | 2/5 | ✅ |
| 试题5 | 图形的相似 | `正方形的边CD绕点D逆时针旋转` | 2/5 | ✅ |
| 试题9 | 二次函数 | `过点P作AB的垂线` | 5/5 | ✅ |
| 试题10 | 三角形 | `过AC的中点D作AC的垂线` | 1/5 | ✅ |
| 试题14 | 图形的平移 | 多组长串未命中原 sid，但命中**同题等价题**（高唐县期末，题干与图片 svg 完全一致） | — | ⚠️ 等价命中 |
| 试题15 | 图形的旋转 | `将BE绕点B逆时针旋转60` | 3/5 | ✅ |

**结论**：6/6 均可召回（5 题命中原 sid + 1 题命中等价题）。**唯一未命中原 sid 的 Q14**，换更长的子串/考点兜底仍常落在"近等价变体"上，说明部分偏冷门题需人工补一长串特征词。召回率对"典型真题"高、**对"冷门/改编题"会掉**，属预期内风险（已在故障表标注）。

---

## 五、S1 / S2 / S3.5 / S4 · 逐步执行

| 步 | 提示词文件 | 输入 | 输出 |
|---|---|---|---|
| S1 | `references/step1-parse-question.md` | 试题原图 + 题库 JSON（第 4 节的字段） | 裸 JS 对象 `{ sentences, translations }` |
| S2 | `references/step2-lecture-plan.md` | 试题原图 + S1 产物 + **方法论**（见下） | 裸 JS 对象 `questionData` |
| S3 | `references/step3-drawing-code.slim.md` | 原图 + 解析 + S1 + S2 | 裸绘图代码（`LIB` 两行注入标记；结构层只写 `/* @@STRUCTURE@@ */`） |
| S3.5 | `references/step3.5-code-review.md` | S3 **装配后**产物（+ `questionData` 的 `voiceText`） | **报告 + 变更区块**（v2：不重抄代码） |
| S4 | `references/step4-assemble-html.md` | S1 + S2 + S3.5 装配产物 | 完整 HTML（v2：由 `scripts/assemble-html.js` 装配） |

**S2 的方法论输入（v2 分级，★ 省 64% 输入）**：

| 题目类型 | 读什么 | 体积 |
|---|---|---|
| **常规题**（默认） | `references/00-essence.md` —— 四篇的**操作版精要**（保留全部可执行规则/清单/量化/易错点） | 16.2 KB |
| **难题**（A 档几何构造 / 多问综合 / 冷门改编） | 四篇全文（`01`~`04`，按「三文档递进学习法」顺序） | 79.9 KB |

- 常规题读精要即可；**一旦 S3/S3.5 出现"讲题逻辑/四环结构"类问题，立刻改用四篇全文重跑 S2**（精要不足以支撑疑难判定）。
- 四篇全文**原样保留**（`01-teaching-heart.md` / `02-four-ring-manual.md` / `03-example-library.md` / `04-audio-canvas-sync.md`），作为 fallback。

> S2 是整条链路的"质量中枢"，**方法论必需**；漏读会直接导致 S3.5 打回。

---

## 六、S3 · 两种模式（本 skill 的核心设计）

差异**只有一个变量**：两块内联库（几何内核 v2.2 + 绘图层 v1.1，共 1215 行）**由谁写进产物**。

| | 模式 A（full） | 模式 B（slim）★ 当前默认 |
|---|---|---|
| 提示词 | `references/step3-drawing-code.full.md`（2301 行） | `references/step3-drawing-code.slim.md`（1119 行） |
| 模型动作 | 从提示词槽位**整段粘贴** 1215 行库代码 | 在 `LIB` 内**只写两行注入标记** |
| 库正文来源 | 模型输出**包含**库正文 | 模型输出**不含**库正文；由 `scripts/assemble-artifact.js` 注入真源 |
| 抄写失真风险 | 🔴 有（历史踩坑：`_textViolation` 正则括号丢失、漏粘绘图层） | 🟢 无（脚本保证逐字等于真源） |
| 模型输出量 | ~1300 行 | ~100 行 |

### 模式 B 执行方式

1. 模型按 `step3-drawing-code.slim.md` 产出，`LIB` 内形如：

   ```javascript
   const LIB = (function () {
     /* @@INJECT:GEOM_KERNEL@@ */
     /* @@INJECT:DRAW_LAYER@@ */
     // ── 构造区 ──
     ...
   ```

2. 把模型输出存成文件（如 `_work/step3-raw.js` 的临时路径），然后：

   ```bash
   node scripts/assemble-artifact.js <模型产物文件>
   # 默认输出 <原名>.assembled.js
   ```

3. 装配脚本会：按标记注入真源（缩进自动对齐）→ 校验两块指纹唯一、无残留标记 → 抽查 `window.__DRAW_TIER__` → 写出。
   装配后的产物与模式 A **逐字等价**，可直接交给 S3.5。

### v2 附加：结构层由脚本生成（P2-3）

`navigationMap` 与 `drawFunctions` 是**纯机械映射**（帧号如何分配到「四环」），完全由 S2 的 `totalIntro` / `subQuestions[].stages[].subSteps` / `finalSummary` 决定，**不需要模型推理**。

- **S3 产物里**：结构层位置只写一行 `/* @@STRUCTURE@@ */`（**不手写** `navigationMap` / `drawFunctions`）。
- **展开**：`node scripts/build-structure.js <s2.js> --inject <s3-raw.js> --out <s3.js>`
  - 优先展开 `@@STRUCTURE@@` 占位标记；
  - 若模型仍手写了结构层（旧格式），脚本识别并**整段替换**（向后兼容）。
- **帧分配规则**（脚本与 S3 提示词 §1.1 同源）：`frame 0 = totalIntro` → 每问依次 审题定向(1) / 破冰搭桥(1) / 规范建模(= `subSteps.length`) / 独立总结(1) → 末帧 = `finalSummary`。
- **已验证**：试题7（2 问 / 17 帧）用脚本生成的结构层与原模型手写版**语义完全一致**，且替换后过 30/30 体检、去注释后**逐行一致**。
- **诚实说明**：此项省下的**输出 token 不多**（该段仅 ≈1 KB）；它的价值在**确定性与正确性**（消除帧号错位——手写错位会让页面停在最后一帧），**不在速度**。

> **等价性已用脚本验证**：
> `references/同步内联库.js --check --target references/step3-drawing-code.full.md` → exit 0
> （即 full 版槽位里的库＝真源逐字；而 slim 注入的也是同一真源）

### 实测数据（2026-09-29 · V3.0 验证集 6 道真题，配对盲测）

同一份 Step1/Step2 输入、每个模式各一个独立执行体、共 12 份产物，全部经 `verify-artifact.js` 独立复算：

**S3 双模式配对（模型实际输出行数，不含脚本注入的库）：**

| 题 | full 模型输出 | slim 模型输出 | 缩减 |
|---|---|---|---|
| 试题4 图形的对称 | 1894 | 687 | 63.7% |
| 试题5 图形的相似 | 2106 | 869 | 58.7% |
| 试题9 二次函数 | 1972 | 734 | 62.8% |
| 试题10 三角形 | 1875 | 775 | 58.7% |
| 试题14 图形的平移 | 1996 | 775 | 61.2% |
| 试题15 图形的旋转 | 2089 | 997 | 52.3% |
| **均值** | **1989** | **806** | **59.5%** |

**全链路校验结论（6 题 × 双模式）：**

| 指标 | A · full | B · slim |
|---|---|---|
| 22 项独立体检通过率 | 6/6 ✅ | 6/6 ✅ |
| 两块库与真源逐字一致 | ✅ | ✅（脚本注入） |
| 产物语法（node --check） | ✅ | ✅ |
| 逐题帧数（S3 装配后） | 22/32/26/23/28/31 | 与 full 完全一致 |
| S3.5 校后 `s3.5.js` 22 项 | 6/6 ✅ | 6/6 ✅（库保真 1109 行/题） |
| 最终 out.html 可运行 | 6/6 ✅ 语法合法 | 6/6 ✅ 语法合法 |

**要点**：
- 成本优势（−59.5% 输出量）是**机制性**的 —— 输出量直接决定截断风险，1215 行库一旦被截断产物必报废；slim 把这块完全交给脚本，模型零负担。
- 6 轮真题下 **full 模式仍逐字正确**（抄写失真未被触发），故"slim 更省"可确定，"slim 更不易错"仍**未获证**（需更多轮才能归因）。
- 两版帧数**本轮逐题完全一致**（上轮合成题曾出现 8 vs 7 波动），说明帧结构波动是模型随机性而非模式差异。
- S3.5 校对**真实生效**：每题增 91~201 / 删 22~107 行（修构造逻辑，未动帧结构），证明"独立复算"环节不可或缺。
- 历史合成题单轮对比（1 轮 −79%）见工作区 `S3两版对比实验报告.md`；真题批量见 `六题真题对比实验报告.md`。

> **默认模式结论**：**模式 B（slim）定为默认**。机制性省成本 + 截断风险归零已坐实；"更不易错"待多轮统计，但即使 full 也不更易错，slim 无 downside。切换 full 只需改 S3 提示词引用。

---

## 七、目录结构

```
cnki-edu-math-ai-lecture/
├── SKILL.md                              ← 本文件
├── references/
│   ├── step1-parse-question.md            S1 提示词（v3.1）
│   ├── step2-lecture-plan.md              S2 提示词（v3.1）
│   ├── step3-drawing-code.full.md         S3 提示词 · 模式 A（v6.7.1，2301 行，库已内联）
│   ├── step3-drawing-code.slim.md         S3 提示词 · 模式 B（1103 行，库由脚本注入；★ v2 已改为只写 @@STRUCTURE@@）
│   ├── step3.5-code-review.md             S3.5 提示词（v6.7.1 + v2 输出侧瘦身）
│   ├── step4-assemble-html.md             S4 提示词（v6.8.1 + v2 脚本装配声明）
│   ├── 00-essence.md                      ★ v2 新增：四篇精要（常规题默认读，16.2 KB）
│   ├── 01~04-*.md                         四篇全文（难题读 / fallback，原样保留）
│   ├── html-template.html                 ★ v2 新增：HTML 模板真源（509 行 / 34.6 KB，含 6 槽位）
│   ├── 几何内核.js                         真源 v2.2（管「点在哪」）
│   ├── 绘图层.js                           真源 v1.1（管「长什么样」）
│   └── 同步内联库.js                        同步/校验工具（--check / --dry / --write）
└── scripts/
    ├── build-slim-step3.js                从 full 版生成 slim 版（⚠️ v2 下勿盲目重跑，见 §九）
    ├── assemble-artifact.js               模式 B 装配：把真源注入模型产物
    ├── verify-artifact.js                 产物体检：逐字保真 / 骨架完整 / 违规项（独立复算）
    ├── build-template.js                  ★ v2 新增：从 S4 提示词抽 HTML 模板 → references/html-template.html
    ├── build-structure.js                 ★ v2 新增：展开 /* @@STRUCTURE@@ */ → navigationMap + drawFunctions
    ├── assemble-html.js                   ★ v2 新增：S4 脚本装配（模板 + S1/S2/S3 → 完整 HTML）
    ├── apply-s3.5.js                      ★ v2 新增：S3.5 报告/代码分离装配（@@NO_CHANGE@@ / @@CHANGES@@）
    └── run-s3-checks.js                   ★ v2 新增：机械校验一条命令（注入内联库 + 32 项体检）
```

**v2 新脚本一图速查：**

| 脚本 | 一句话职责 | 替代掉的原动作 |
|---|---|---|
| `build-template.js` | 从 S4 提示词抽 ```html 块 → 6 槽位模板 | 一次性生成，非每单执行 |
| `build-structure.js` | S2 → `navigationMap` + `drawFunctions` | 模型手写结构层（P2-3） |
| `run-s3-checks.js` | 注入两块内联库 + 32 项体检（含实跑 CK + 页面加载模拟 K） | 8 个独立命令散跑（P1-B） |
| `apply-s3.5.js` | 报告 + `@@NO_CHANGE@@`/补丁 → 装配 `s3.5.js` | 模型重抄整份代码（P0-A） |
| `assemble-html.js` | 模板 + S1/S2/S3.5 → 完整 HTML 单页 | 模型整页重写 HTML（P0-B） |

> `verify-artifact.js` 是**独立复算**工具，用于校验任意 S3 产物（不采信模型自称）：
> ```bash
> node scripts/verify-artifact.js <产物.js>          # 22 项体检报告
> node scripts/verify-artifact.js <产物.js> --json   # 结构化输出，供批量/多轮对比
> ```
> 退出码：0 全通过 / 1 有问题。可接在 `assemble-artifact.js` 之后作为流水线闸门。
>
> `run-s3-checks.js` 是 v2 的**加强版闸门**（32 项，含 A 语法 vm 编译 / B 两块库逐字保真 / H 实跑 CK / I 帧结构 / J voiceText 符号扫描 / **K 页面加载模拟（逐帧执行 drawFrame_N）**），日常用它替代上面的散跑：
> ```bash
> node scripts/run-s3-checks.js <产物.js> [--s2 <s2.js>] [--dump <装配后文件>] [--json]
> ```

---

## 八、铁律（违反即返工）

1. **坐标禁止手写数字**，只能由几何内核构造函数算出。
2. **`CKSummary()` 必须全绿（n/n）**，角标绿底才算通过；有 ❌ 要回头改**基础参数**，不许改期望值 / 删条目。
3. **两块内联库不得手改、不得自写同名函数**（模式 B 下由脚本注入，模型更不该碰）。
4. **画布文字必须走 `drawMathText` / `drawSymbol` / `drawLabel`**，不得直接 `fillText` 中文或数字。
   **★ 分路（实测踩坑）**：结论标记（`✓ ✗ ？ ！ ✕`）用 `drawSymbol`；**数学关系符**（`∽ ≌ ⊥ ∥ ∠ △ ⊙` 等）用 `drawMathText`——两者白名单不同。`recQ` 记关系符用 `type:'text'`、记标记用 `type:'symbol'`，使首绘与帧重放（`replayAccumulator`）走同一条绘制路径；用错会在帧重放时触发画布白名单告警（∽ 在重放帧上还会不显示）。
5. **持久 / 临时分离**：`stateAccumulator` 只收持久元素（`recQ` 写入）；`pulseHighlight` 类临时强调不 `recQ`；产物代码区 `recordToAccumulator(` 命中数必须为 0。
6. **每个 `drawFrame_N` 末行必须 `finishFrame()`**；每帧顶层动画调用数 ≤ 1。
7. **输出格式纯净**：S1/S2 裸对象、S3/S3.5 裸代码、S4 裸 HTML，不带 Markdown 包裹、不带说明前缀。
8. **S3.5 必须独立复算**，不得采信 Step 3 自己写的 ✅。

### v2 附加铁律（★ 违反即返工，且会直接抵消提速）

9. **S3 不手写结构层**：`navigationMap` / `drawFunctions` 一律只写 `/* @@STRUCTURE@@ */`，由 `scripts/build-structure.js` 展开。手写会退回原版的"帧号错位"风险。
10. **S3.5 不重抄代码**：只输出「校对报告 + 变更区块」；零修正写 `/* @@NO_CHANGE@@ */`，有修正写 `@@CHANGES_BEGIN/END` 包裹的 `<<<OLD>>>`/`<<<NEW>>>` 补丁。**禁止**把整份代码再抄一遍（这正是 v2 砍掉的 34% 输出黑洞）。
11. **S4 不手写 HTML**：整页 HTML 由 `scripts/assemble-html.js` 装配；模型只负责产出 S1/S2/S3.5 三段。**禁止**模型重写整页（这是 54% 输出黑洞）。
12. **报告不得自造机械结论**：CK 全绿、库保真、帧结构这些**机械项**必须由 `run-s3-checks.js` / `verify-artifact.js` 跑出来，报告只能引用脚本结果，**不能凭印象写"已通过"**。
13. **不得盲目重跑 `build-slim-step3.js`**：v2 已手工改过 `step3-drawing-code.slim.md`（加 `@@STRUCTURE@@` 声明、删手写结构层说明）。重跑会**用 full 版覆盖掉这些 v2 改动**。若确需重跑，先备份当前 slim 文件并事后把 v2 改动重新贴回（详见 §九）。
14. **本质不变**：以上 9~13 全部只改「谁生成这段文本」，**改不了一条讲题范式、一条质量铁律、一项体检标准**——质量只增不减（重抄归零 = 抄写失真归零）。

---

## 九、库升级时的纪律

真源**只有一个**：`references/几何内核.js` / `绘图层.js`。

```bash
# 1) 改真源后，先校验 full 版槽位与真源是否一致
cd references
node 同步内联库.js --check --target ../../references/step3-drawing-code.full.md   # 不一致 → exit 1

# 2) 需要时把真源同步回 full 版槽位（会自动备份原件）
node 同步内联库.js --write --target ../../references/step3-drawing-code.full.md

# 3) 重新生成 slim 版
cd ../../scripts && node build-slim-step3.js
```

> **改了真源忘同步** → full 版提示词里是旧库；**忘了重跑 build-slim** → 两版不一致，对比实验失效。

### ⚠️ v2 特别提醒：`step3-drawing-code.slim.md` 已被 v2 手工改过

v2 对 slim 版做过**两处手工修改**（这两处与内联库无关）：

1. 卷首新增「⚠️ v2 附加声明（结构层交由脚本生成）」；
2. 正文把「手写 `navigationMap` / `drawFunctions`」的骨架与检查清单项改为「只写 `/* @@STRUCTURE@@ */`」。

`build-slim-step3.js` 是**从 full 版整段重生 slim**，**不含**上述 v2 改动——**直接重跑会覆盖它们**。

**正确顺序（三选一）**：

```bash
# A. 若不涉及改库：根本不要跑 build-slim-step3.js（v2 默认不跑）
# B. 若确实升级了内联库：先备份 → 重跑 → 手工把 v2 两处改动贴回
cd scripts && cp ../references/step3-drawing-code.slim.md ../references/step3-drawing-code.slim.md.v2bak
node build-slim-step3.js
# 然后用 diff 比对备份，把 v2 声明与 @@STRUCTURE@@ 改动重新合并回去
# C. 若只是校对提示词：只改 full 版对应文字，v2 的 slim 单独手工同步
```

> **回归校验**：改完 slim 后跑一次
> ```bash
> node scripts/run-s3-checks.js <一份既有 s3 产物> --s2 <对应 s2.js>
> ```
> 确认 32/32 仍通过，即证明 slim 的 v2 声明未破坏产物结构。

---

## 十、故障处理

| 现象 | 处理 |
|---|---|
| 题库召回为空 | 按 S0 第 6 条**停止并告知**，不自行解题 |
| 召回命中"近等价变体"而非原 sid（冷门/改编题） | 用更长、更独特的无空格子串再试 1~2 次；仍不行则按 S0 第 6 条停止（等同"未命中"，不勉强用变体解析） |
| 关键词含空格/符号触发 400 | 去掉空格与 `∠ = °` 等符号，改用长串无空格中文子串（见 S0 第 2 条） |
| 模型没写注入标记（模式 B） | 让 S3 重跑；或临时切 `step3-drawing-code.full.md` |
| 装配后指纹出现 >1 次 | 模型自写了同名库函数 → 删掉模型自写部分后重新装配 |
| `CKSummary()` 非全绿 | 打回 S3 改基础参数（缩边长 / 调角度 / 平移顶点 / 减标签） |
| `voiceText` 残留数学符号 | 打回 S2 重做（S3.5 §0.10.4 口径） |

### v2 新脚本故障项

| 现象 | 处理 |
|---|---|
| `build-structure.js` 报「未找到 `@@STRUCTURE@@` 也未找到既有结构层」 | S3 产物既没写占位标记、也没手写结构层 → 回 S3 补 `/* @@STRUCTURE@@ */` |
| `build-structure.js` 报「`subSteps` 缺失 / 帧号不连续」 | 多半是 S2 的 `questionData` 结构不完整 → 回 S2 补 `stages[].subSteps` |
| `apply-s3.5.js` 报「`<<<OLD>>>` 片段命中 0 次」 | S3.5 写的 OLD 片段与装配后代码不一致（空格/换行）→ 让 S3.5 重取**逐字唯一**片段 |
| `apply-s3.5.js` 报「`<<<OLD>>>` 片段命中 >1 次」 | OLD 片段不唯一 → 让 S3.5 加长片段到唯一 |
| `apply-s3.5.js` 报「未找到档位声明 / 抄写自检日志 / 校对报告」 | S3.5 没按 v2 输出格式 → 回 S3.5 按 `references/step3.5-code-review.md` 「# 第九步」重出 |
| `assemble-html.js` 报「槽位未命中 / 模板缺标记」 | `references/html-template.html` 被改坏或缺失 → 重跑 `node scripts/build-template.js` 重建 |
| `assemble-html.js` 主 `<script>` 语法编译失败 | 多半是 S3.5 补丁改动破坏了语法 → 回 S3.5 修，或在装配报告里看报错行号 |
| `run-s3-checks.js` H 项（实跑 CK）失败 | 构造区几何参数不过关 → 回 S3 改基础参数（同「CKSummary 非全绿」） |
| `run-s3-checks.js` I 项（帧结构）失败 | 结构层与 S2 不同步 → 重跑 `build-structure.js` 再装配 |
| `run-s3-checks.js` 报「两块库保真失败」 | slim 版本升级导致库不一致 → 按 §九 流程同步真源，勿盲目重跑 build-slim |
| `run-s3-checks.js` **K 项**报「`xxx is not defined`」 | 帧函数/产物区引用了未解构到顶层的构造点或几何算子（它们都在 `LIB` IIFE 内）→ 在产物顶层补 `const { … } = pts;` 与 `const { … } = LIB;`（解构用到的即可） |
| `run-s3-checks.js` **K 项**报帧内「画布白名单违规」 | 帧里画了汉字/数字/等式，或把关系符（`∽ ≌ …`）误用 `drawSymbol` → 按 §八 铁律 4 分路：关系符走 `drawMathText`、`recQ` 记 `type:'text'` |
| H 项全绿但页面打开仍白屏 | 问题在**帧函数体内**（H 只跑 `CKSummary`，不调用 `drawFrame_N`）→ 看 K 项报错。若无 K 项，说明是旧版校验脚本，先更新到含 K 段的 `run-s3-checks.js` |
| `build-structure.js` 展开后页面报 `navigationMap is not defined` | 产物里 `@@STRUCTURE@@` 的外层注释定界符（`/* … */`）未一起替换 → 用 v2 当前版 `build-structure.js`（其 `MARK_RE` 会一并替换注释壳） |

## 跨场景公共约定

权限固定提示 / 干净输出红线 / 触发词格式 / 版本与完工标准 / MCP 前缀自检：统一见 [_shared.md](references/_shared.md)。本 skill 的前置权限校验口径与「严禁编造知网数据」红线均与之对齐。
