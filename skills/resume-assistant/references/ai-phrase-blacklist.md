# AI 文风黑名单 · 中英双语

> **目标**：防止生成的简历"听起来像 AI 写的"——即使每个事实都对，也要写得像人话。这是 provenance 的**第三维度**（前两维：不编造事实 + 合法改写）。
>
> **来源**：英文黑名单全量迁移自 `srbhr/Resume-Matcher` 的 `AI_PHRASE_BLACKLIST`（26K ⭐ 项目的工程实践）；中文黑名单由本 Skill v0.2 基于国内招聘语境新增。
>
> **数据源 vs 文档**（v0.3 起拆分）：
> - 本文档（`.md`）：人类可读的说明、触发规则、设计理由
> - `ai-phrase-blacklist.json`：机器数据源，`scripts/audit_ai_flavor.py` 的唯一读取目标
> - 当两者不一致时，**以 JSON 为准**，应更新本文档对齐

---

## 一、运行时行为

### 1.1 触发时机

以下 mode 的输出**必须**经过黑名单审计：

- `mode=generate` · 从零生成
- `mode=rewrite` · 润色改写
- `mode=tailor` · JD 定制
- `mode=refine` · 多轮细修

### 1.2 报告分级

| 命中次数 | 级别 | Skill 行为 |
|---|---|---|
| 0 | INFO | 静默通过 |
| 1-2 | INFO | 在 `provenance-audit.json` 记录，不打扰用户 |
| 3-5 | WARN | 在 CLI 输出警告 + 建议 replacement |
| ≥6 | **ERROR** | 必须改 —— Skill 主动应用 REPLACEMENTS 或请用户选择 |

### 1.3 自动修复

用户在 `preferences.auto_fix_ai_flavor` 的控制：

- `"aggressive"`：所有命中自动替换，记录于 `provenance.action = "ai_flavor_fix"`
- `"report_only"`（默认）：仅报告，让用户决定
- `"off"`：跳过黑名单审计（不推荐）

### 1.4 Provenance 记录

每次自动修复记录完整追踪：

```json
{
  "bullet_id": "exp_2_bullet_3",
  "action": "ai_flavor_fix",
  "risk": "low",
  "original": "Spearheaded the architecture of a cutting-edge ML platform",
  "modified": "Led the design of an ML platform",
  "triggered_words": ["spearheaded", "architected", "cutting-edge"],
  "hallucination_risk": "none"
}
```

---

## 二、英文黑名单（English Blacklist）

### 2.1 过度使用的动词（Over-used verbs）

| 命中词 | 建议替换 |
|---|---|
| `spearheaded` | `led` |
| `orchestrated` | `coordinated` |
| `championed` | `advocated for` |
| `synergized` | `collaborated` |
| `leveraged` | `used` |
| `revolutionized` | `transformed` |
| `pioneered` | `introduced` |
| `catalyzed` | `initiated` |
| `operationalized` | `implemented` |
| `architected` | `designed` |
| `envisioned` | `planned` |
| `effectuated` | `achieved` |
| `endeavored` | `worked to` |
| `facilitated` | `helped` |
| `utilized` | `used` |

### 2.2 企业套话（Corporate buzzwords）

`synergy`, `synergies`, `paradigm`, `paradigm shift`, `best-in-class`, `world-class`, `cutting-edge`, `bleeding-edge`, `game-changer`, `game-changing`, `disruptive`, `disruptor`, `holistic`, `robust`, `scalable`, `actionable`, `impactful`, `proactive`, `proactively`, `stakeholder`, `deliverables`, `bandwidth`, `circle back`, `deep dive`, `move the needle`, `low-hanging fruit`, `touch base`, `value-add`

> ⚠️ `stakeholder` / `scalable` / `robust` 在特定技术语境是合法词 —— 审计脚本应结合上下文，不在同一句里出现 ≥2 个才报错。

### 2.3 填充短语（Filler phrases）

`in order to` → `to` ｜ `for the purpose of` → `to` ｜ `with a view to` → `to` ｜ `at the end of the day` → ❌ 删除 ｜ `moving forward` → ❌ 删除 ｜ `going forward` → ❌ 删除 ｜ `on a daily basis` → `daily` ｜ `on a regular basis` → `regularly` ｜ `in a timely manner` → `on time` / `promptly` ｜ `at this point in time` → `now` ｜ `due to the fact that` → `because` ｜ `in the event that` → `if` ｜ `in light of the fact that` → `because`

### 2.4 标点嫌疑（Punctuation signals）

| 符号 | 问题 | 处理 |
|---|---|---|
| `—`（em-dash）| AI 大量使用，人类简历少用 | 替换为 `-` 或拆句 |
| `--` | em-dash 变体 | 同上 |
| `  ` · 多空格 | AI 常见 | 收敛为单空格 |

---

## 三、中文黑名单（Chinese Blacklist · 本 Skill 新增）

### 3.1 大厂黑话动词

| 命中词 | 建议替换 | 说明 |
|---|---|---|
| 赋能 | 帮助 / 支持 / 让 X 能做到 Y | "赋能业务"改为"让业务能做到……" |
| 打造 | 搭建 / 做出 / 开发 | "打造一款产品" → "做出一款产品" |
| 夯实 | 巩固 / 加强 | |
| 沉淀 | 积累 / 整理成文 / 形成方法论 | "沉淀 SOP" → "整理成 SOP 文档" |
| 拉通 | 协调 / 对接 / 打通 | |
| 搭建（过度）| 做 / 建 | 一个简历 ≤ 2 次 |
| 赋能 + 打造 同句 | — | **连用立即 ERROR** |

### 3.2 大厂黑话名词

| 命中词 | 建议替换 |
|---|---|
| 抓手 | 切入点 / 方法 / 措施 |
| 闭环 | 完整流程 / 端到端 |
| 心智 | 用户认知 / 品牌印象 |
| 颗粒度 | 精细程度 / 粒度 |
| 组合拳 | 多个动作 / 一整套方案 |
| 壁垒 | 优势 / 门槛 |
| 势能 | 动能 / 影响力 |
| 体感 | 感受 / 体验 |
| 势头 | 发展趋势 |
| 心智锚点 | 用户第一印象 |

### 3.3 空话短语

| 命中短语 | 处理 |
|---|---|
| 对齐一下 | 达成共识 / 同步一下 |
| 互联网下半场 | ❌ 直接删（空话）|
| 降本增效 | 优化成本 + 提高效率（分开讲）|
| 全链路 | 端到端 / 全流程 |
| 可持续发展 | 具体讲目标（如"支撑未来 3 年业务扩展"）|
| 生态 / 生态圈 | 具体描述（合作伙伴 / 合作方 / 用户网络）|
| 结果导向 | ❌ 删（每条 bullet 都应该是结果导向，不必自称）|
| 高效完成 | ❌ 删（"高效"是主观评价，没有量化）|

### 3.4 词汇多样性规则

即使单个词不在黑名单，**同一份简历**中同一个"黑话级动词"出现 ≥3 次也要报 WARN。常见问题词：

- "负责" —— 每份简历建议 ≤ 4 次，多了要用 `主导 / 推动 / 主持 / 设计 / 搭建 / 交付` 等替换
- "优化" —— ≤ 3 次
- "参与" —— 只在真的不是主导时用，多于 2 次要问用户"这几项真都只是参与吗？"

---

## 四、白名单（合法保留）

以下词虽然常被批评"套路化"，但在简历技术语境是**不可避免的术语**，不列入黑名单：

- **技术栈术语**：`scalable` / `microservices` / `distributed` / `high-availability` / 分布式 / 高可用 / 微服务
- **STAR/XYZ 必要动词**：`improved` / `reduced` / `increased` / `achieved` / `delivered` / 提升 / 降低 / 实现
- **量化指标术语**：`CTR` / `GMV` / `DAU` / `MAU` / `ROI` / `SLA`（虽然像黑话但已是行业通用语）

---

## 五、自定义扩展

用户可在 `<workspace>/.resume-assistant/custom-blacklist.yaml` 追加：

```yaml
# 用户自定义禁用词（公司/行业级）
banned_terms:
  zh:
    - 我司           # 某些公司禁止
    - 鄙司
  en:
    - guru           # 过时词
    - ninja
    - rockstar

# 用户自定义替换建议
replacements:
  zh:
    鄙司: 原公司
```

Skill 读取后合并到运行时黑名单，优先级高于内置。

---

## 六、与 provenance-rules.md 的关系

`provenance-rules.md` 定义**什么 action 是合法的**（6 种：verbatim_copy / minor_polish / keyword_inject / structure_reorder / quantify_placeholder / ai_flavor_fix）。

本文档是 `ai_flavor_fix` 这一 action 的**词典依据**。两者配合使用：

```
[生成 bullet]
  → provenance-rules 判断：这次改动属于哪种 action？
  → 若是 ai_flavor_fix → 查 ai-phrase-blacklist 词典 → 应用 replacement
  → 记录 provenance 完整追踪
```

---

## 附录 · 维护流程

1. **季度审视**：每季度跟进一次 AI 文风新词（"赋能"→ 新出现的词）
2. **社区反馈**：用户报告误判时，审视是否加入白名单
3. **版本号**：本文件升级需同步更新 `_skill_meta.json` 的 `version`
