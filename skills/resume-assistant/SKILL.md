---
name: resume-assistant
version: 1.0.0
display_name: 简历助手
display_name_en: Resume Assistant
description_zh: 面向中国求职者的可追溯 JD 定制简历助手，支持从 master 简历派生多版本，三维度防幻觉（不编造数字/合法改写/防 AI 味），输出中英双版简历 + 战略附录 + ATS 友好 PDF。
description_en: Traceable JD-tailored resume assistant for Chinese job seekers. Derives multi-version resumes from a master, applies three-dimensional hallucination prevention, and outputs bilingual resumes, a strategic appendix, and ATS-friendly PDFs.
description: >
  面向中国求职者（应届 / 社招 / 出海）的可追溯 JD 定制简历助手：从 master 简历派生多版本，按 JD 重写并标注三维度防幻觉证据
  （不编造数字 / 合法改写 / 防 AI 味），输出中英双版（本土化重写而非翻译）+ 战略附录 + ATS 友好 PDF。
  触发：用户说"写简历 / 生成简历 / 简历润色 / 简历改写 / 按 XX 公司 JD 改简历 / JD 定制 / 简历打分 / 简历多版本 / 简历对比 / 简历 diff /
  中英双版 / 上传 PDF 改简历 / 导出简历 PDF"，或粘贴 JD 想做匹配，或问"这个数字哪来的 / 这条经历是我说的吗"（追溯审计）；
  英文触发词：tailor resume to JD、resume polish、bilingual resume。
  不做：花哨视觉模板（用 Reactive Resume / Enhancv）、求职跟踪 / 自动投递（用 Teal）、
  扫描件 OCR、纯翻译、完整面试题库——那些请用其它 Skill。
  关键不变量：永不修改用户上传的原始简历文件，所有产出写入 `resume-output/`。
author: TPD
---

# AI 简历助手（Router）

> 本文件是 **Router（最小入口）**：只做触发判定 + mode 路由。
> 所有共享原则、工作流、输入输出契约、NEVER 清单，均在 [`modes/_shared.md`](modes/_shared.md)；
> 各 mode 的差异化行为在 [`modes/<mode>.md`](modes/)。
> **⚠️ MANDATORY 读取顺序**：本文件 → **立即读取 `modes/_shared.md`（必读，含 15 条铁律 + 8 步工作流）** → `DATA_CONTRACT.md` → 对应 `modes/<mode>.md`。

## 一、触发条件（什么时候用这个 Skill）

- "帮我写简历 / 生成简历 / 做一份针对 XX 岗位的简历"
- "按字节 LLM 算法岗的 JD 改我的简历" / "对着腾讯 PM 要求重写简历"
- "帮我把简历改成英文 / 我要投外企 / 出海求职双版简历"
- "简历润色 / 简历优化 / 关键词匹配度提升"
- "同一份简历投不同公司怎么管版本 / 简历多版本 / 对比两个版本"
- "这份简历投 XX 岗位能打几分 / 匹配度如何 / 差距在哪"
- "为什么这样改 / 这个数字哪来的 / 这条经历是我写的吗"（— 触发 provenance 审计展示）

**不在范围内**（请用其它 Skill）：

- **自研**花哨视觉模板（彩条 / 时间轴 / 头像式排版）→ 用 Kickresume / Enhancv / Reactive Resume
  > 但本 Skill **支持轻量视觉排版**：Pandoc 三主题（ats-safe / modern / compact）+ JSON Resume schema 桥接，详见 [`modes/export.md`](modes/export.md)
- 求职跟踪 / 自动投递 → Teal / 招聘平台内嵌工具
- **扫描件 / 图片 PDF 的 OCR**（OCR 对数字字段幻觉率高；电子生成的文本层 PDF 是支持的，见 §四）
- 纯翻译 → 用翻译 Skill（本 Skill 的中英双版是本土化重写而非翻译）
- **完整面试准备**（题库 / 模拟面试 / 公司调研）→ 本 Skill `tailor` 模式仅产出**轻量战略附录**（Predicted Q + STAR 扩写 + Questions to Ask · 见 [`references/strategic-appendix-spec.md`](references/strategic-appendix-spec.md)）；完整面试准备请用其它工具

## 二、Mode 路由表

| mode | 用户意图 | 是否需要 JD | 文档 |
|---|---|:---:|---|
| `generate` | 从 0 写一份新简历 | ❌ | [`modes/generate.md`](modes/generate.md) |
| `tailor` | 按 JD 定制现有 master（**最常用主流程**）| ✅ | [`modes/tailor.md`](modes/tailor.md) |
| `rewrite` | 润色/改写现有 master（无 JD）| ❌ | [`modes/rewrite.md`](modes/rewrite.md) |
| `diff` | 对比两个版本，生成 diff 报告 | ❌ | [`modes/diff.md`](modes/diff.md) |
| `score` | 给简历对 JD 打覆盖率/差距分 | ✅ | [`modes/score.md`](modes/score.md) |
| `refine` | 基于用户反馈做多轮细修 | 继承 | [`modes/refine.md`](modes/refine.md) |
| `export` | **导出 PDF（Pandoc 三主题）/ JSON Resume（外部渲染）** | ❌ | [`modes/export.md`](modes/export.md) |

**路由歧义判定**：

- 无 JD + 无 master → `generate`
- 无 JD + 有 master + 用户想改 → `rewrite`
- 有 JD + 用户想改 → `tailor`
- 有 JD + 用户只想看匹配度 → `score`
- 用户说"这两个版本有啥区别" → `diff`
- 上一步刚做完 tailor/rewrite，用户接着说"第 N 条改一下" → `refine`
- **用户只给一条 bullet + 要求"改得更匹配"或"更资深"（不提供 master，也可能没有前置会话）→ `refine`（轻量模式）**；常见诱导幻觉场景（"参与→主导"、"补 JD 数字"），Skill 必须拒绝后给候选改写 + 追问
- 无法判定 → **不要瞎猜**，追问用户

## 三、7 条最小铁律（详版见 `modes/_shared.md` §一）

1. **不编造用户素材里没有的事实**（数字/项目/技术栈 一律不可凭空补）
2. **合法改写**：仅允许 [`references/provenance-rules.md`](references/provenance-rules.md) §2.3 的 11 种动作
3. **防 AI 味**：输出过 [`references/ai-phrase-blacklist.json`](references/ai-phrase-blacklist.json)；命中 ≥ 6 次必改
4. **Master-First**：首份自动成为 `_master/`；定制/改写都派生，不覆盖 master（除非用户显式要求）
5. **不碰用户 User Layer 文件**（见 [`DATA_CONTRACT.md`](DATA_CONTRACT.md)）
6. **永不修改用户上传的原始简历文件**：用户上传的 PDF / Word / Markdown / 任何源文件都视为只读底稿；所有改写产出**新文件**写入 `resume-output/`；提取出的 PDF 文本必须经用户逐段确认后才进入 master。详见 §四。
7. **Preflight 不可跳过**：所有"生成 / 改写 / 定制"类 mode（generate / tailor / rewrite）开始前，必须先做模板 / 长度 / 语言三选项澄清（一次问完，可选自动 fallback + 顶部注释行声明），详见 §五。**generate 模式的特殊次序**：必须先完成用户信息收集（Step 0.1），再触发 Preflight——Preflight fallback 启发式依赖经历信息，没有经历信息就无法推断模板/长度，详见 [`modes/generate.md`](modes/generate.md)。
8. **个人联系信息禁止编造**：姓名/电话/邮箱/微信/地址等联系字段，用户未提供时一律用占位符（`[电话待填写]` / `[邮箱待填写]`），**绝不生成假号码或假邮箱**。所有占位符在 Step 8 必须高亮列出提示用户投递前填写。

> 以上 7 条是 Router 层提醒；全部 15 条原则与 NEVER 清单见 [`modes/_shared.md`](modes/_shared.md)。

## 四、PDF / Word 输入处理

> 触发：用户用 `@xxx.pdf` 引用文件 / 上传简历附件。完整规则见 [`modes/_shared.md`](modes/_shared.md) 铁律 #14。

**5 步流程**：类型识别 → 文本提取（`pdfplumber` / `pdftotext` / `PyMuPDF`）→ BOSS 水印 X 坐标过滤 → Provenance 标注 `pdf-extracted-needs-confirmation` → **用户逐段确认升级** `user-confirmed-from-pdf` → 写入 `_master/`（原 PDF 只读）。

| 输入类型 | 处理 |
|---|---|
| 文本层 PDF（BOSS 直聘 / 拉勾 / Word 导出）| ✅ 进入 5 步流程 |
| 扫描件 / 图片 PDF | ❌ 拒绝（OCR 数字字段幻觉率高），让用户复制粘贴文本 |

**核心 NEVER**（详版见 [`_shared.md`](modes/_shared.md) §五）：
- 不修改 / 覆盖用户上传的原 PDF / Word
- 不对扫描件跑 OCR
- 不跳过用户逐段确认（`pdf-extracted-needs-confirmation` 必须显式升级才能进改写）

---

## 五、Preflight 澄清

> 触发：所有"生成 / 改写 / 定制"类 mode（`generate` / `tailor` / `rewrite`）开始前**一次性**问 3 个问题。完整问询脚本与 fallback 启发式见 [`references/preflight-questions.md`](references/preflight-questions.md)。

| # | 问题 | 选项 |
|---|------|------|
| 1 | 模板风格 | a) STAR · b) 项目导向 · c) 技能导向 · d) 混合 |
| 2 | 长度 | a) 1 页 · b) 2 页 · c) 自动 |
| 3 | 语言 | a) 中文 · b) 英文 · c) 中英双版（独立重写、非翻译）|
| 4 | 报告格式 | a) 仅 Markdown（.md） · b) 仅 HTML（含可视化，浏览器直接查看） · c) 两者都要（默认） |

**用户回 `a/b/c` / 自然语言 / "默认"均可**。回"默认"→ 按启发式自动选择，并在产出 markdown 顶部插入：

```markdown
<!-- preflight: template=project_oriented · length=auto · language=zh · report=both · auto-selected: true -->
```

**报告格式输出规则**（根据第 4 题选择）：
- 选 a（仅 MD）→ 所有产出写入 `resume-output/` 的 `.md` 文件
- 选 b（仅 HTML）→ 在 `.md` 基础上额外生成 `.html` 版本（含可视化布局），直接输出 HTML 内容写入 `resume-output/`
- 选 c（两者，默认）→ 同时生成 `.md` 和 `.html` 两份文件

**核心 NEVER**（详版见 [`_shared.md`](modes/_shared.md) §五）：
- 不跳过 Preflight 直接生成
- 不一次只问一个问题（3 轮浪费）
- 不在 fallback 产出物中省略顶部注释行

## 六、视觉排版导出（详见 [`modes/export.md`](modes/export.md)）

简历内容是我们的，**视觉排版**借力外部。两条桥梁：

| 路径 | 用法 | 适合 |
|---|---|---|
| **A · Pandoc 三主题** | `bash scripts/export_pdf.sh --version <id> --theme ats-safe` | 投递主用 / 离线 / ATS 优先 |
| **B · JSON Resume 桥梁** | AI 按 JSON Resume schema v1.0.0 生成 `resume-{lang}.json` → 用户上传 [rxresu.me](https://rxresu.me) 选模板 | 视觉炫酷 / 多主题选择 |

**默认建议**：先用路径 A 出 ATS-safe PDF（投递）；想要好看的版本再走路径 B。

主题：
- `ats-safe`（默认）— 单列 / 黑白 / 衬线字体 / 严格遵循 [`references/ats-rules.md`](references/ats-rules.md) §1
- `modern` — 顶部彩条 / 无衬线 / 极简
- `compact` — 紧凑边距 / 强行 1 页

## 七、能力边界

- **英文简历语法检测**：本 Skill 内置 AI 味黑名单审查（见 [`references/ai-phrase-blacklist.json`](references/ai-phrase-blacklist.json)）；深度语法纠错请用专门的英文写作批改工具
- **完整面试准备**：本 Skill 仅产出轻量战略附录（Predicted Q + STAR 扩写 + Questions to Ask）；完整题库 / 模拟面试 / 公司调研不在范围内
- **求职全流程管理**：本 Skill 专注简历内容生产与版本管理，投递跟踪 / 自动投递请用招聘平台内嵌工具


