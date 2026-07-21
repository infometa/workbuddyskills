# Provenance Rules（字段级追溯与防幻觉规则）

> **这是 resume-assistant Skill 最核心的一份规则文档**。
> 任何简历生成/改写动作都必须遵守；任何违反 provenance 规则的输出视为**严重质量事故**。
>
> 这份规则同时解决了市面竞品最大的痛点：**AI 简历工具的通病是幻觉造数字、编项目**。
> 本 Skill 的第一护城河就是**每条生成内容都能追溯到用户原始素材**。
>
> **v0.2 升级**：从"两维度"（不编造 + 合法改写）升级为"**三维度**"——新增第三维度「防 AI 味」，吸收自 `srbhr/Resume-Matcher` 的 `AI_PHRASE_BLACKLIST` 工程实践。

---

## 0. 三维度总览（v0.2 新增）

| 维度 | 原则 | 工具 / 清单 | 动作 |
|---|---|---|---|
| **一** | 不编造事实（no fabrication）| `provenance.source` + 素材溯源 | `verbatim_copy` / `minor_polish` / `keyword_inject` / `structure_reorder` / `quantify_placeholder` / `fabricate`❌ |
| **二** | 合法改写（legitimate rewrite）| 6 种允许 action 的风险分级 | 见下文 §3 |
| **三** | 防 AI 味（anti AI flavor · 🆕）| [`ai-phrase-blacklist.md`](ai-phrase-blacklist.md) 中英双语 73+ 词 | `ai_flavor_fix` |

> 三维度是**并集关系**——任何一维违反都视为质量事故。

---

## 1. 核心原则（The 3 Commandments）

### 1.1 原则 1：无中生有禁令

> **用户原始素材（experiences / jd / legacy_resume）里没有的客观事实，AI 绝不能补。**

严格禁止的"无中生有"情形：

| 禁止项 | 具体例子 | 为什么是灾难 |
|---|---|---|
| ❌ 编数字 | 用户说"提升了性能"，AI 写"性能提升 300%" | 面试一问就露馅 |
| ❌ 编项目 | 用户没提过的项目名 / 客户名 / 产品名 | 无法回答细节追问 |
| ❌ 编技术栈 | 用户没写 Redis，AI 加上"用 Redis 做缓存" | 面试考察时崩盘 |
| ❌ 编职级/title | 用户是"开发"，AI 写"技术负责人" | 背调会查真实职级 |
| ❌ 编时间跨度 | 用户说"做过一段时间"，AI 写"负责 2 年" | 社保/劳动合同会对不上 |
| ❌ 编团队规模 | 用户没说团队人数，AI 写"带领 5 人团队" | 背调即穿帮 |
| ❌ 编客户 / 合作方 | 用户没提具体公司，AI 编"服务客户包括 XX" | 严重失信 |

### 1.2 原则 2：改写不等于改事实

允许 AI 做的**措辞级改写**（`rewrite`）：

| 允许的动作 | 示例 |
|---|---|
| ✅ 口语→书面 | "搞定了那个 bug" → "修复了生产环境关键缺陷" |
| ✅ 合并冗余 | "做了 A，还做了 B" → "承担 A 与 B 两项工作" |
| ✅ 拆分长句 | 一个长句拆成两条 bullet |
| ✅ 动词替换 | "做" → "负责 / 承担 / 设计 / 实现"（在用户语气许可范围内）|
| ✅ 调整顺序 | 按 STAR 或 XYZ 公式重排 |
| ✅ 补充上下文连接词 | "为了提升…，实施了…" |

**严格区分语气升级**：

| 用户原文 | 允许改 | 禁止改 |
|---|---|---|
| "参与了XX" | "参与" / "协助" | ❌ "主导" / "负责" / "牵头" |
| "负责了XX" | "负责" / "承担" | ❌ "主导" / "架构" |
| "帮忙做了" | "协助" / "参与" | ❌ "主导" |

所有会触发语气升级的词（见 [keyword-taxonomy.md](keyword-taxonomy.md) `seniority_markers`）→ 必须走**强制用户审核**流程。

### 1.3 原则 3：缺量化就占位，绝不编数

如果某条 bullet 明显需要量化但用户原始素材没有数据：

- ✅ 正确做法：输出 `"性能优化了 ____%（请补充具体数字）"`，并在 `provenance-audit.json` 标记 `requires_user_input: true`
- ❌ 错误做法：编一个"看起来合理"的数字（20% / 50% / 300%）

**占位符标准格式**：
- 百分比：`____%`
- 人数：`____ 人`
- 时间：`____ 周 / 月`
- 金额：`¥____ / $____`
- 次数：`____ 次`

---

## 2. Provenance 字段定义

每一条生成的 bullet 都必须有 provenance 记录，写入 `provenance-audit.json`。

### 2.1 provenance 对象 schema

```json
{
  "bullet_id": "exp-1-bullet-2",
  "bullet_text": "基于 Transformer 架构重构推荐召回模型，离线 AUC 提升 3.2%",
  "source": {
    "from_field": "experiences[0].projects[1].description",
    "raw_text": "用transformer改了召回，auc涨了"
  },
  "rewrite_actions": [
    "colloquial_to_formal",
    "add_technical_context",
    "preserve_metric"
  ],
  "llm_additions": [],
  "llm_inferences": [
    {
      "content": "离线",
      "rationale": "AUC 一般指离线评估指标，补充'离线'提高表述准确度",
      "risk_level": "low"
    }
  ],
  "placeholder_fields": [],
  "hallucination_risk": "low",
  "requires_user_review": false,
  "review_status": "auto-approved"
}
```

### 2.2 字段含义

| 字段 | 类型 | 说明 |
|---|---|---|
| `bullet_id` | string | 唯一 ID，格式 `<section>-<index>-bullet-<n>` |
| `bullet_text` | string | 最终生成的文本 |
| `source.from_field` | string | 原始素材中的字段路径 |
| `source.raw_text` | string | 原始文本（引文）|
| `rewrite_actions` | string[] | 改写动作清单（见 2.3）|
| `llm_additions` | object[] | LLM 补充的内容（必须为空或低风险）|
| `llm_inferences` | object[] | LLM 做的合理推断（需标 risk_level）|
| `placeholder_fields` | object[] | 需要用户补数据的占位符 |
| `hallucination_risk` | enum | `none` / `low` / `medium` / `high` |
| `requires_user_review` | bool | risk ≥ medium 时必须 true |
| `review_status` | enum | `pending` / `auto-approved` / `user-approved` / `user-rejected` |

### 2.3 rewrite_actions 枚举

| action | 含义 | 风险 | 维度 |
|---|---|:---:|:---:|
| `colloquial_to_formal` | 口语→书面 | ✅ 低 | 二 |
| `merge` | 合并冗余 | ✅ 低 | 二 |
| `split` | 拆分长句 | ✅ 低 | 二 |
| `reorder_star` | 按 STAR 重排 | ✅ 低 | 二 |
| `reorder_xyz` | 按 XYZ 公式重排 | ✅ 低 | 二 |
| `verb_upgrade` | 动词替换（同级语气）| ⚠️ 中 | 二 |
| `add_technical_context` | 补充技术上下文 | ⚠️ 中 | 二 |
| `add_metric_placeholder` | 加量化占位符 | ✅ 低 | 一 |
| `preserve_metric` | 保留原量化数据 | ✅ 低 | 一 |
| `tone_escalation` | 语气升级（参与→主导）| 🚨 高 —— **必须用户审核** | 二 |
| `infer_missing_detail` | 推断缺失细节 | 🚨 高 —— **必须用户审核** | 二 |
| `ai_flavor_fix` 🆕 | 替换 AI 味词（查 `ai-phrase-blacklist.md`）| ✅ 低 | 三 |

> **🆕 v0.2 新增 `ai_flavor_fix`**：仅替换黑名单词为同义平替，不增删事实。完整词典见 [`ai-phrase-blacklist.md`](ai-phrase-blacklist.md)。触发条件与替换规则见 §3.4。

### 2.4 hallucination_risk 判定矩阵

```
IF 存在 tone_escalation OR infer_missing_detail
    → risk = "high"  → 强制用户审核
ELIF 存在 add_technical_context
    → risk = "medium"  → 强制用户审核
ELIF 存在 verb_upgrade
    → risk = "medium"  → 建议用户审核
ELIF 只做 colloquial_to_formal / merge / split / reorder_*
    → risk = "low"  → 自动批准
```

---

## 3. 审计流程（Step 5 的具体实现）

### 3.1 ngram 比对

对每条生成 bullet 做 bigram/trigram 比对：

```python
def compute_provenance_coverage(bullet: str, raw_text: str) -> float:
    """返回 bullet 中有多少比例的实词在 raw_text 里出现过。"""
    bullet_tokens = set(tokenize(bullet))
    raw_tokens = set(tokenize(raw_text))
    if not bullet_tokens:
        return 0.0
    return len(bullet_tokens & raw_tokens) / len(bullet_tokens)
```

判定：

- `coverage ≥ 0.7` → 高度复用原文，risk = low
- `0.4 ≤ coverage < 0.7` → 有合理改写，risk = medium，需看具体 action
- `coverage < 0.4` → 严重偏离原文，risk = high，强制审核

### 3.2 具体实体检测

用**命名实体识别（NER）+ 正则**对以下类别做白名单匹配：

| 实体类型 | 检测规则 | 违规处理 |
|---|---|---|
| 数字（百分比/金额/人数）| `\d+%` / `\d+人` 等 | 必须在 raw_text 出现，否则替换为占位符 |
| 技术栈 keyword | 对照 `keyword-taxonomy.md` | 用户原文未出现 → 删除或打 high risk |
| 公司名 / 产品名 | 对照用户 basic_info.target_positions[].company + experiences[].company | 用户未提及 → 删除 |
| 职级词（主导/架构）| 对照 `seniority_markers` | 用户原文无 → 降级或打 high risk |

### 3.4 AI 文风审计（维度三 · v0.2 新增）

每次 `mode=generate/rewrite/tailor/refine` 的输出都**强制**经过 AI 文风审计：

```python
# 伪代码 —— 详见 ai-phrase-blacklist.md §1
def audit_ai_flavor(bullet: str, lang: "zh"|"en") -> AIFlavorReport:
    blacklist = load_blacklist(lang)          # 加载中/英黑名单
    hits = [w for w in blacklist if w in bullet.lower()]
    level = {
        0:    "INFO",
        1-2:  "INFO",
        3-5:  "WARN",
        6+:   "ERROR",
    }[len(hits)]

    if preferences.auto_fix_ai_flavor == "aggressive" and hits:
        modified = apply_replacements(bullet, hits)
        record_provenance(action="ai_flavor_fix",
                          triggered_words=hits,
                          original=bullet, modified=modified,
                          risk="low")
```

**关键约束**：
- `ai_flavor_fix` **不修改任何事实字段**（数字 / 项目名 / 公司名 / 技术栈）—— 只替换表达层面的"AI 味"词
- 每次替换**必须**记录完整 provenance（原文 → 替换文字 → 触发词列表）
- 命中 ≥6 次的 bullet 必须强制用户审核

### 3.5 展示给用户的审核清单

所有 `requires_user_review: true` 的条目，在 Step 8 逐项展示：

```
⚠️ 需要您确认的条目 3 条：

[1/3] 风险等级：🚨 高
    经历 1 · bullet 2
    AI 生成："主导了搜索排序模型的优化工作"
    您的原文："参与了一个推荐模型的活儿"
    动作：tone_escalation（参与 → 主导）+ infer_missing_detail（推荐→搜索排序）
    请选择：
      ✅ 属实，保留
      ✏️ 修改为：___________
      🗑️ 删除这条

[2/3] 风险等级：⚠️ 中
    ...
```

---

## 4. 用户审核 UX 规范

### 4.1 审核粒度

- **bullet-level**：每条 bullet 单独审核
- **不合并批量操作**：不能一次"全部批准"，因为审核的目的是让用户过一遍，防止面试被问时穿帮
- **可撤回**：审核完可以再改

### 4.2 交互格式

- 审核发起时：明确告知"共 N 条待审核，预计需要您 X 分钟"
- 每条之间有编号 `[1/N]`
- 修改后的内容立即回写到 result.json 并重新计算 coverage

### 4.3 审核完成判定

```
ALL bullets WHERE requires_user_review = true
    → review_status IN ("user-approved", "user-rejected")
    ⇒ 全部审核完成 ⇒ result.json.review_status = "approved"
```

否则 result.json 顶层 `review_status = "partial"`，并拒绝导出最终 PDF。

---

## 5. 审计报告输出（provenance-audit.json）

完整 schema：

```json
{
  "schema_version": "1.0",
  "generated_at": "2026-04-23T16:00:00+08:00",
  "version_label": "v1-bytedance-llm",
  "stats": {
    "total_bullets": 24,
    "risk_distribution": {
      "none": 0,
      "low": 18,
      "medium": 4,
      "high": 2
    },
    "requires_review_count": 6,
    "reviewed_count": 6,
    "approved_count": 5,
    "rejected_count": 1,
    "placeholder_count": 3
  },
  "review_status": "approved",
  "bullets": [
    { /* provenance 对象，见 §2.1 */ },
    ...
  ],
  "placeholders": [
    {
      "bullet_id": "exp-0-bullet-1",
      "placeholder": "____%",
      "context": "性能优化了 ____%",
      "prompt": "请补充性能提升的具体百分比"
    }
  ]
}
```

---

## 6. 常见违规案例（反面教材）

### 案例 1：编造量化数据

- 用户原文：`"优化了接口响应时间"`
- ❌ 错误输出：`"优化接口响应时间，P99 从 500ms 降至 100ms，性能提升 80%"`
- ✅ 正确输出：`"优化接口响应时间（原 P99 ____ms → ____ms，请补充）"`

### 案例 2：语气升级没标记

- 用户原文：`"帮同事一起做了个小工具"`
- ❌ 错误输出：`"主导开发了团队内部效率工具"`
- ✅ 正确输出：`"协助开发团队内部工具"`（保持"协助"语气）

### 案例 3：AI 自己补技术栈

- 用户原文：`"用 Python 写了爬虫"`
- ❌ 错误输出：`"使用 Python + Scrapy + Redis + MongoDB 构建分布式爬虫"`
- ✅ 正确输出：`"使用 Python 开发数据采集脚本（具体技术栈：Python；如使用其它框架请补充）"`

### 案例 4：编合作方名字

- 用户原文：`"给一个大厂客户做项目"`
- ❌ 错误输出：`"为字节跳动、阿里等头部客户交付定制化方案"`
- ✅ 正确输出：`"为头部互联网公司客户交付定制化方案"`（抽象化而非具名）

---

## 7. 实现清单（开发者视角）

- [ ] `scripts/provenance_audit.py`：加载 experiences + 生成 bullets，做 §3 全套检查
- [ ] `scripts/render_audit_report.py`：渲染审计 JSON 为 Markdown / HTML 报告
- [ ] 在 SKILL 工作流 Step 5 强制调用 audit
- [ ] 在 Step 8 强制用户审核闭环
- [ ] `result.json` 顶层 `review_status` 未到 `approved` → 拒绝导出终稿 PDF

## 版本

| 版本 | 日期 | 变更 |
|---|---|---|
| 0.1.0 | 2026-04-23 | 初稿：3 原则 + provenance schema + 审计流程 + 审核 UX + 反面教材 |
