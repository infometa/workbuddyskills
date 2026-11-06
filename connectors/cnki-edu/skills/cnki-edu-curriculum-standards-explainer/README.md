# 课标解读 · cnki-edu-curriculum-standards-explainer

面向中小学教师的"课标解读"技能包。围绕国家课程标准（义务教育 2022 年版、普通高中 2017 年版及 2025 年日常修订版），按「学段 + 学科 + 课标版本 + 解读方面」四个变量，输出结构化、可落地、带安全标注的解读报告；并可调用**中国知网（CNKI）文献库**检索权威解读文献作为证据支撑。

## 包内容

```
cnki-edu-curriculum-standards-explainer/
├── SKILL.md                        # 技能主文件（frontmatter + 工作流 + 触发判断）
├── README.md                       # 本文件：安装、使用、发布说明
├── eval.yaml                       # 质量自测用例（可选）
└── references/                     # 按需加载的参考文档
    ├── prompt-library.md           # 1 个总控提示词 + 7 个方面专用提示词（核心）
    ├── workflow.md                 # 12 步工作流程详解
    ├── output-templates.md         # 通用/专用输出结构、输入模板、报告骨架
    ├── triggers.md                 # 强/弱/文献 触发关键词全表
    ├── subject-adaptation.md       # 学段适配 + 学科适配对照表
    ├── knowledge-base.md           # 知识库需求与降级策略（含文献独立降级链）
    └── cnki-retrieval.md           # 知网文献检索手册（本次新增）
```

## 七个解读方面

核心素养 · 课程性质 · 课程理念 · 课程目标 · 课程内容 · 学业质量 · 课程实施

## 知网文献引用（可选增强）

知网检索是**可选增强**：接入知网教育数据服务、经知网基教权益校验通过后生效；未接入或未通过校验时，先提示前往 **e.cnki.net** 开通 / 购买基教服务，再自动跳过知网检索、不影响主流程（不冒充权威来源）。

| 能力 | 说明 |
|---|---|
| 文献库检索 | 查"有哪些文献谈过这个课标问题"，按篇名+摘要召回 |
| 段落库检索 | 直接拿到"某段具体论述"，如学业质量内涵、水平划分的表述 |
| **标准文档检索** | **未上传课标原文时**，经知网基教权益校验通过后调用知网教育数据检索取"课标/教材"标准文档块作为权威「课标依据」来源（仅在已通过基教权益校验时启用），命中处注明来源 |
| **年限门槛** | **义务教育文献只取 2022 年起；普通高中文献只取 2017 年起**（课标颁布年之前的是旧版课标研究，不适用） |
| **版本优先级** | **2025 年日常修订版**的解读文献（含新旧修订对比、变化阐释）优先级最高、重点采用 |
| 安全底线 | 不编造文献；文献观点与课标原文分区呈现；文献与原文冲突时以原文为准 |

> 接口无年份参数，须按返回的时间字段（`PubDate`/`Year`）解析出版年后再过滤（完整规则见 `references/cnki-retrieval.md` 第三节）。

## 安装到 WorkBuddy

**方式一：个人技能（推荐）**

把整个 `cnki-edu-curriculum-standards-explainer` 文件夹放到用户级技能目录：

- Windows：`C:\Users\<你的用户名>\.workbuddy\skills\cnki-edu-curriculum-standards-explainer\`
- macOS / Linux：`~/.workbuddy/skills/cnki-edu-curriculum-standards-explainer/`

**方式二：项目级技能（多人共享）**

放到当前项目的 `.workbuddy/skills/cnki-edu-curriculum-standards-explainer/`，团队成员在同一项目内即可共享。

**方式三：从 WorkBuddy 上传**

在 WorkBuddy 的技能管理界面选择"导入 / 创建技能"，上传本文件夹（或打包后的 zip），按提示确认后即可启用。发布共享时，填写技能的展示名"cnki-edu-curriculum-standards-explainer"（中文可写"课标解读"）与描述即可。

> 安装后无需重启；下次对话中提到"课标解读"等触发词即可自动加载。

## 怎么用

直接用自然语言说需求即可，例如：

- `帮我解读小学语文 3-4 年级的核心素养`
- `初中数学"学业质量"课标怎么说的？达标什么样、怎么评？`
- `高中物理课标里"课程内容"的内容要求、学业要求、教学提示分别是什么？`
- `2022版和2025年日常修订版的英语课标有什么区别？`
- `帮我查一下知网上义务教育语文课程标准核心素养的权威解读文献，2022年之后的，最好有2025年修订版的`
- `高中化学课标 2025 年日常修订版改了什么？有没有解读文章支撑？`

若信息不全，技能会先追问学段 / 学科 / 方面，再开始解读。

**想让解读更准确**：把对应学科的课标原文（docx / pdf）一起上传，技能会按原文引用并给出章节与页码；不传的话，若已连接知网教育 MCP（`edu`）且经 `mcp__<SERVER>__userState` 校验具备基教权益，会调用 `mcp__<SERVER>__standardSearch` 检索"课标/教材"标准文档块作为课标依据，并在末尾标注 `⚠请按所用课标版本核对`；若未连接 MCP 或未通过基教权限校验，则提示前往 **e.cnki.net** 开通基教权益，且**不以模型知识冒充"课标依据"**，仅可作明确标注"通用版（未接入知网基教，知网数据增强层暂未启用）"的通用说明。

**想要文献佐证**：技能会调用知网文献库检索并逐年过滤（义教 ≥ 2022 年、高中 ≥ 2017 年，2025 年日常修订版优先），结果以"正文右上角 `[n]` 超链接序号 + 文末「参考资料」"方式呈现（点 `[n]` 跳转到文末对应篇名）。说一句"不用查文献"即可跳过。

## 自定义

- 调整输出栏目 → 改 `references/output-templates.md` 的报告骨架。
- 调整某方面的解读深度 → 改 `references/prompt-library.md` 对应段落的【输出结构】。
- 增删触发词 → 同时改 `SKILL.md` 的「触发判断」和 `references/triggers.md`。
- 调整知网检索策略（检索式、年限门槛、筛选规则、引用格式）→ 改 `references/cnki-retrieval.md`。
- 补充本地知识库（课标全文 / 解读文献 / 术语词典 / 学科映射表）→ 见 `references/knowledge-base.md` 第三节。

## 版本

- v1.2.3 — **对齐"投稿选刊"技能的文献打开/登录规则**：回退入口由研学平台 `https://x.cnki.net/search?sw=篇名` 改为知网主站标题检索 `https://kns.cnki.net/kns8s/defaultresult/index?kw=篇名`（参数由 `sw=` 改为 `kw=`）；明确"投稿选刊"的 `readUrl` 即 `mcp__<SERVER>__searchVectorBJ` 返回的 `url` 字段，形态为单篇在线阅读页 `https://ix.cnki.net/read/article/readonline?dbcode=…&tablename=…&filename=…&fileSourceType=1`；`kns.cnki.net` 与 `ix.cnki.net` 同属知网主站、共用统一账号登录，故未登录时弹出的登录页与"投稿选刊"一致（⚠️ 实测当前 `mcp__<SERVER>__searchVectorBJ` 不返回 `url`，实际走 `kns.cnki.net` 回退）。详见 cnki-retrieval.md 6.4。
- v1.2.2 — 修正文献链接与字段口径（基于 `mcp__<SERVER>__searchVectorBJ` 真实响应复核）：① 链接策略改为"篇名 `href` **优先取检索返回的 `url` 字段**（知网本篇在线阅读直链，登录由知网接管）；⚠️ 实测当前 `mcp__<SERVER>__searchVectorBJ` 响应**不返回 `url` / `文件名`**，故统一回退标题检索入口 `https://kns.cnki.net/kns8s/defaultresult/index?kw=篇名`（知网官方入口，登录由知网接管），**严禁用 `dbcode`/`tablename`/`filename` 自行拼装直链**"（与"投稿选刊"技能同款思路）；② 年期 / 发表时间改从真实返回的 `PubDate` / `Year` 解析（不再依赖并不返回的 `文件名`）；③ 明确 `Author` / `Source` / `JournalName` 等字段接口已直接返回，可直接写入报告。详见 cnki-retrieval.md 2.3 / 3.1 / 6.4。
- v1.2.1 — 修复「参考资料」篇名点击体验：篇名 `href` 由"安全搜索入口"改为检索返回的**知网研学本篇在线阅读直链**（点击**直达本篇阅读页**），`filename`/`dbcode`/`tablename` 等内部标识仅存于 `href` 属性、渲染不可见；库未收录无法取得直链时回退安全搜索入口；并明确 HTML 篇名必须显式 `text-decoration:none`（无下划线）（详见 cnki-retrieval.md 6.4–6.5）。
- v1.2.0 — 未上传课标原文时改由 `edu` 连接器的 `mcp__<SERVER>__standardSearch` 检索"课标/教材"标准文档块作为「课标依据」来源（替代纯模型知识兜底，命中注明来源）；引用标记由〔n〕统一改为右上角 `[n]` 超链接序号，跳转文末「参考资料」对应篇名（每条篇名设锚点 `id="ref-n"`）；文末「参考资料」每条篇名均渲染为可点击超链接，点击**经本篇在线阅读直链直达知网研学本篇阅读页**（`href` 取 `https://ix.cnki.net/read/article/readonline?…&filename=…&fileSourceType=1`，内部标识仅存属性），篇名在 HTML 中显式 `text-decoration:none`（无下划线）、不在文档可见区展示文件名/url/代码符号等敏感信息（详见 cnki-retrieval.md 6.4–6.5）。
- v1.1.0 — 接入中国知网（CNKI）文献检索：新增 `references/cnki-retrieval.md`，工作流扩到 12 步，新增"正文〔n〕角标 + 文末「参考资料」"引用方式、文献检索触发词、年限门槛（义教 ≥2022 / 高中 ≥2017）与 2025 年日常修订版优先策略、文献独立降级链。
- v1.0.0 — 首次成包：1 总控 + 7 专用提示词、11 步工作流、强弱触发词、学段学科适配、知识库降级策略。
