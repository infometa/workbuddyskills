# ATS 兼容规则（v0.3.2 新增）

> **吸收来源**：`refs/resume/_picked/resume-ats-optimizer/SKILL.md`（L43-78、L58-64、L109-143、L145-204、L296-310）+ `refs/resume/career-ops/modes/pdf.md`
>
> **使用场景**：`mode=score`（计算 ATS 友好度）+ `mode=export`（出 PDF 时按本规则约束渲染）+ `mode=tailor` Step 6（关键词覆盖率验证）

---

## §1 文件与版式硬约束

| 维度 | ✅ 安全 | ❌ 不安全 |
|---|---|---|
| **文件格式** | `.pdf`（文本层）/ `.docx` | 扫描 `.pdf`（图片）/ `.pages` / `.odt` |
| **布局** | 单列（single column） | 双列 / 多列 / 侧边栏 |
| **字体** | Helvetica / Arial / Calibri / Times New Roman / Garamond | 装饰字体 / 自定义字体 |
| **字号** | 正文 10-12pt / 标题 14-16pt | < 9pt / > 18pt（破坏视觉层级）|
| **页边距** | 上下 0.5-1 in / 左右 0.5-1 in | < 0.4 in（解析丢字）|
| **图标 / 图片** | ❌ 无 | 任何 emoji 装饰 / 头像照片 / 进度条图标 |
| **表格** | ❌ 不用 | 用表格做技能/项目（ATS 解析后顺序错乱）|
| **页眉页脚** | 仅页码 | 把姓名/邮箱放页眉页脚（部分 ATS 不读）|
| **日期格式** | `YYYY-MM` 或 `MM/YYYY` 或 `Mon YYYY` 任选其一**全文统一** | 中英混用 / 同一份里"2024年3月"和"2024-03"并存 |
| **联系方式** | 电话 + 邮箱 + LinkedIn 写在第一行下面，**纯文本** | 嵌图标 / 用 hyperlink 包裹却不写明文 |
| **特殊字符** | 标准 - · ( )  | 装饰性 ⚡ ★ ▶ 箭头 / 全角中文标点夹在英文中 |

---

## §2 节标题白/黑名单（直接用最 ATS-safe 的写法）

> 来源：`resume-ats-optimizer/SKILL.md` L58-64

### ✅ ATS 安全的节标题（推荐）

| 中文 | 英文 |
|---|---|
| 工作经历 | **Work Experience** / **Professional Experience** / **Experience** |
| 教育背景 | **Education** |
| 项目经历 | **Projects** / **Project Experience** |
| 技能 | **Skills** / **Technical Skills** |
| 个人简介 | **Summary** / **Professional Summary** |
| 证书 | **Certifications** |
| 出版物 | **Publications** |
| 荣誉 | **Awards** / **Honors** |

### ❌ 不要用的"创意"标题

`Where I've Been`（应：Work Experience）、`Academic Background`（应：Education）、`Core Competencies`（推荐 → Skills 或 Technical Skills）、`My Story`、`Adventures in Code`、`What I Bring`、`关于我`（中文环境用"个人简介"或"Summary"）

ATS 关键词匹配是按**严格字符串**或宽松同义词字典做的，自创标题命中率显著下降。

---

## §3 关键词频控启发式（Match Score）

> 来源：`resume-ats-optimizer/SKILL.md` L109-143。**这是启发式，不是工业标准**——用于"够不够 ATS"自检，不要当绝对真理。

### §3.1 Match Score 公式

```
Match Score = (简历命中的 JD 关键词数 / JD 提取的关键词总数) × 100
```

- ≥ **80%**：达标，正常投递
- 60-80%：建议补 1-2 段经历或扩 skills 段
- < 60%：JD 与背景错位较大，建议先看 `mode=score` 的差距分析再决定要不要投

### §3.2 关键词出现次数带

| 关键词类型 | 推荐出现次数 | 例子 |
|---|---|---|
| **核心硬技能**（JD 出现 ≥ 3 次的）| **2-4 次** | Python / Kubernetes / 用户增长 |
| **重要硬技能**（JD 出现 1-2 次的）| **1-2 次** | LangChain / Grafana |
| **行业术语** | **1-2 次** | OKR / GMV / DAU |
| **软技能** | **1 次足够** | leadership / 沟通 |

### §3.3 关键词放置优先级

按 ATS 解析重要性从高到低：

```
1. Summary / Professional Summary (顶部 3-4 行)
2. Skills 段
3. 最近一段 Work Experience 的前 2 个 bullet
4. Project / Education 段（次要）
```

> ⚠️ **不要堆砌**：同一个关键词在一个 bullet 里出现 ≥ 2 次 / 在 Skills 段重复列、是 keyword stuffing；ATS 现代算法（如 Workday、Greenhouse）会判降权，HR 也看得出来。

### §3.4 同义词与缩写

✅ **可以做**：在 Skills 段第一次出现时**用全称（缩写）**，例：`Customer Relationship Management (CRM)` —— 这能同时命中两套 ATS 词典。

❌ **不要做**：把"近义词"当事实陈述，例如把"参与"换成"主导"——这是事实改动而非术语优化，违反三维 Provenance 第二维。

---

## §4 ATS 友好度报告模板

> 来源：`resume-ats-optimizer/SKILL.md` L145-204；用于 `mode=score` 的输出

```markdown
# ATS 兼容性报告 · {version_label}

**Overall ATS Score**：{score}/100

| 维度 | 得分 | 状态 |
|---|---:|---|
| 文件格式 | {file_score}/100 | ✅/⚠️/❌ |
| 版式 / 布局 | {layout_score}/100 | ✅/⚠️/❌ |
| 节标题 | {section_score}/100 | ✅/⚠️/❌ |
| 关键词覆盖 | {kw_score}/100 | ✅/⚠️/❌ |
| 日期 / 联系信息 | {meta_score}/100 | ✅/⚠️/❌ |

## 关键词命中情况

| JD 关键词 | 频率（推荐）| 当前出现次数 | 命中位置 | 改进建议 |
|---|---|---:|---|---|
| Python | 2-4 | 1 | Skills | 在最近一段经历的 bullet 里加一处 |
| Kubernetes | 2-4 | 0 | — | **缺**：建议补一个相关项目 |
| ... | | | | |

**预估修订后分数**：{predicted_score}/100

## 改进清单（按优先级）

1. [P0] {action_1}
2. [P1] {action_2}
3. ...
```

---

## §5 ATS 之外的"人眼复审"反向规则

> 来源：career-ops `pdf.md` 经验

ATS 通过 ≠ HR 喜欢。即使 ATS 100 分，**HR 一眼扫**还会按以下信号筛：

| 信号 | HR 反应 |
|---|---|
| 第一段经历 bullet 数 < 3 | "经验单薄"|
| 一段经历无任何数字 | "没成果"|
| 所有 bullet 句首动词重复 ≥ 3 个相同 | "AI 写的吧"|
| 相同公司用 2 个月就跳 ≥ 3 次 | "稳定性堪忧"|
| 学校 / 公司名前后大小写不一致 | "细节不够"|

`mode=score` 输出时**应该同时给 ATS 分 + 人眼分**两栏，避免用户被"100 分 ATS"误导。

---

## §6 NEVER

- **NEVER** 用表格做 Skills 段（即使布局好看，ATS 解析后顺序错乱）
- **NEVER** 把姓名 / 邮箱嵌进图片里（OCR 成本高，HR 端 ATS 无法复制）
- **NEVER** 用双栏布局，即使看着更紧凑（ATS 按从左到右一行扫）
- **NEVER** 把"近义词替换"当 ATS 优化（违反 Provenance 第二维）
- **NEVER** 在多个段落重复同一个关键词 ≥ 5 次（keyword stuffing 被判降权）
