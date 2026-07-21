# 校准集（Calibration Set）· v1.0.0

> 本目录收录 **55 篇真题锚点样例作文 + 人工参考分 + 定档 rationale**，用于：
>
> 1. **few-shot 定档**：Skill 在 Step 3 判定时可参考档内样卷
> 2. **回归测试**：每次 Skill 迭代必须通过 `scripts/calibrate.py --check-band-range --check-v16` **55/55 全绿**才能发布
> 3. **差异化证据**：这是网易有道 / 批改网 / 通用 LLM 都不公开的 —— 本 Skill 明确声明"用这批样本做过对齐"，可追溯可审计

---

## 总览

| 维度 | 规模 | 说明 |
|------|-----|------|
| **锚点样例总数** | **55 篇** | 覆盖 6 级别 × 5 档位 × 多题型子类 |
| **金标样例数** | **15 篇** | 专门锚定边界场景与多 critical 叠加 |
| **letter_category 覆盖** | **10 / 11** | 仅 `other` 未覆盖 |
| **chart_subtype 覆盖** | **7 / 7 满覆盖** | 含 2024 首考 `table` + 2025 首考 `line_graph` |
| **全档覆盖级别数** | **5 / 6** | CET4 / CET6 / Postgrad1A / Postgrad1B / Postgrad2A；Postgrad2B 锚点档补全进行中 |

### 按级别分布

| 级别 | 样例数 | 档位覆盖 |
|------|:---:|---------|
| CET4 | 9 | 2 / 5 / 8 / 11 / 14（五档全） |
| CET6 | 9 | 2 / 5 / 8 / 11 / 14（五档全） |
| Postgrad1A | 11 | 1 / 2 / 3 / 4 / 5（五档全） |
| Postgrad1B | 6 | 1 / 2 / 3 / 4 / 5（五档全） |
| Postgrad2A | 9 | 1 / 2 / 3 / 4 / 5（五档全） |
| Postgrad2B | 11 | 1 / 3 / 4 / 5（第 2 档待补） |

---

## 目录结构

```
references/calibration/
├── README.md                         # 本文件
├── cross-exam-analysis.md            # 基于 55 篇的跨考试系统对照推演
│
├── samples/                          # 锚点样例（按级别 × 档位 × 题型子类组织）
│   ├── cet4-*.md                     # CET-4 系列 9 篇
│   ├── cet6-*.md                     # CET-6 系列 9 篇
│   └── postgrad/                     # 考研系列 37 篇
│       ├── README.md
│       ├── postgrad1a-*.md           # 英一 A 节 11 篇
│       ├── postgrad1b-*.md           # 英一 B 节 6 篇
│       ├── postgrad2a-*.md           # 英二 A 节 9 篇
│       └── postgrad2b-*.md           # 英二 B 节 11 篇
│
└── cross-level/                      # 跨级别对照样例
    ├── README.md
    ├── cross-level-01-high.md        # 高水平：CET-4 14 → CET-6 13
    ├── cross-level-02-mid.md         # 中等：CET-4 11 → CET-6 8
    └── cross-level-03-low.md         # 偏弱：CET-4 8 → CET-6 5
```

---

## letter_category 覆盖矩阵（Postgrad A 节 letter 题）

| letter_category | 样例文件 | 档位 |
|-----------------|---------|:---:|
| `inquiry` | `postgrad/postgrad1a-03-band-inquiry-letter-01.md` | 3 |
| `application` | `postgrad/postgrad2a-03-band-application-letter-01.md` | 3 |
| `recommendation` | `postgrad/postgrad1a-04-band-recommendation-letter-01.md` | 4 |
| `invitation` | `postgrad/postgrad2a-03-band-invitation-letter-01.md` | 3 |
| `suggestion` | `postgrad/postgrad1a-03-band-suggestion-letter-01.md` | 3 |
| `reply` | `postgrad/postgrad2a-04-band-reply-letter-01.md` | 4 ★ 金标 |
| `apology` | `postgrad/postgrad1a-03-band-apology-letter-01.md` | 3 ★ 金标 |
| `congratulation` | `postgrad/postgrad2a-03-band-congratulation-letter-01.md` | 3 |
| `thank` | `postgrad/postgrad1a-03-band-thank-you-letter-01.md` | 3 |
| `complaint` | `postgrad/postgrad1a-04-band-complaint-letter-01.md` | 4 ★ 金标 |
| `other` | — | 未覆盖（兜底枚举值，实际题中极罕见）|

---

## chart_subtype 覆盖矩阵（Postgrad2B 图表题）

| chart_subtype | 样例文件 | 档位 | 备注 |
|---------------|---------|:---:|------|
| `bar_chart` | `postgrad/postgrad2b-03-band-bar-chart-01.md` | 3 | ★ 金标：数据 5/5 全精确但缺对比表达 → 降 3 档 |
| `pie_chart` | `postgrad/postgrad2b-03-band-pie-chart-01.md` | 3 | |
| `table` | `postgrad/postgrad2b-03-band-table-01.md` | 3 | **2024 首考题型** |
| `line_graph` | `postgrad/postgrad2b-04-band-line-graph-01.md` | 4 | **2025 首考题型**；★ 金标：速率 0.8 pp/year + 平台识别 + 倒装 |
| `multi_bar` | `postgrad/postgrad2b-04-band-multibar-01.md` | 4 | ★ 金标：两组并列 + 数据覆盖 89% + 双维归因 |
| `multi_pie` | `postgrad/postgrad2b-03-band-multi-pie-01.md` | 3 | ★ 金标：数据 8/8 精确但缺相似点 → 降 3 档 |
| `mixed` | `postgrad/postgrad2b-04-band-mixed-01.md` | 4 | |

---

## 金标样例清单（15 篇）

> 金标 = 专门锚定边界场景 / 多 critical 叠加 / 新子类首批锚点；这 15 篇是回归测试的"硬指标"。

| # | 文件 | 定位价值 |
|:-:|------|---------|
| 1 | `postgrad/postgrad1a-02-band-letter-01.md` | Directions 照搬 15 词 + 署名违规 |
| 2 | `postgrad/postgrad1a-01-band-letter-01.md` | 4 类 critical 故障叠加：偏题 + 签名错 + 6 处 grammar + 字数 44% 不足 |
| 3 | `postgrad/postgrad1b-01-band-cartoon-01.md` | 字数不足 0.51 shortfall 跨档下跌 |
| 4 | `postgrad/postgrad2a-02-band-notice-01.md` | Directions 照搬 10+9 词 + 署名违规 |
| 5 | `postgrad/postgrad2a-01-band-notice-01.md` | 4 类 critical 故障叠加：偏题 + 格式 4 重违规 + 8 处 critical + 字数 42% 不足 |
| 6 | `postgrad/postgrad2b-01-band-chart-01.md` | 数据错位 4 处 + 字数不足 0.52 双重扣分 |
| 7 | `cet4-08-band-news-report-01.md` | news_report 末句第一人称 + 主观评价双重违规 → 硬降 8 档 |
| 8 | `cet6-11-band-proverb-01.md` | proverb 双核结构齐全 + CET6 词汇卡位 low-mid tier 11 档 |
| 9 | `postgrad/postgrad1a-04-band-complaint-letter-01.md` | complaint 语域坚定克制 + 证据定量 + 双方案诉求 4 档 |
| 10 | `postgrad/postgrad2b-04-band-multibar-01.md` | multi_bar 两组并列 + 数据覆盖率 89% + 归因双维 4 档 |
| 11 | `postgrad/postgrad1a-03-band-apology-letter-01.md` | apology 语域降级：say sorry / Sorry again 口语模板 + a news 冠词 critical |
| 12 | `postgrad/postgrad2a-04-band-reply-letter-01.md` | reply 日期复述 + 来信诉求复述 + 倒装 "Equally helpful is..." 第四档 |
| 13 | `postgrad/postgrad2b-03-band-bar-chart-01.md` | bar_chart 数据 5/5 精确但缺对比表达 → 降 3 档 |
| 14 | `postgrad/postgrad2b-04-band-line-graph-01.md` | line_graph 速率 0.8 pp/year + 平台识别 + 倒装 "Worth noting is..." 第四档 |
| 15 | `postgrad/postgrad2b-03-band-multi-pie-01.md` | multi_pie 数据 8/8 全精确但缺相似点 → 降 3 档 |

---

## 单篇样例 Markdown 格式

```markdown
---
exam_level: CET4
task_subtype: news_report
band: 8
raw_score: 8
calibration_status: fully_calibrated
reference_source: "2023-06 CET-4 真题阅卷样卷"
prompt: |
  题目原文 / Directions ……
---

# 样例作文原文

正文……

# 人工阅卷批注

- 切题度：……
- 表达清晰：……
- 连贯性：……
- 语言错误：……

## 标注错误

- ¶2 第 3 句："..." → "..."（主谓一致）

## 为什么是 8 档不是 11 档

- 边界判定：……

## 为什么是 8 档不是 5 档

- 边界判定：……
```

---

## 回归测试

```bash
# 档次范围一致性校验（band 与 raw_score 必须一致落在对应档区间内）
python scripts/calibrate.py --check-band-range

# v1.6 枚举白名单校验（task_subtype × exam_level / letter_category / chart_subtype / calibration_status）
python scripts/calibrate.py --check-v16

# 输出：55/55 样例全绿 + 覆盖矩阵 + letter_category × chart_subtype × calibration_status 三维分布表 + 低频理论题型清单
```

**发布门槛**：任何改版必须通过 `--check-band-range --check-v16` **55/55 全绿**，否则不允许发版。

---

## 跨级别对照 · 跨考试对照

- **跨级别对照**（同一作文在 CET-4 vs CET-6 的降档规律）：见 `cross-level/README.md`
- **跨考试对照**（55 篇样例推导出的 6 级别间等效分映射）：见 `cross-exam-analysis.md` + `scripts/estimate_cross_exam.py`

---

## 数据来源合规

- 样例**仅用于内部校准与 few-shot 参考**，不对外分发
- 真题样例严格遵守 "CC-BY-NC" 或"教育合理使用"原则，**不得商用**
- 人工阅卷批注为本项目自行撰写，不复制任何商业培训机构的参考答案原文
