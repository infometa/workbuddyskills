# provenance-spec.md —— 节点级 Provenance 数据模型与匹配规则

> **文档定位**:`scripts/verify_provenance.py` 的**契约文档** + LLM 在 Step 3 / 4 / 6 标注 evidence_source 时的**取值标准**。
> 继承 `paper-quick-reader/references/provenance-rules.md` 的 ngram 匹配核心,但**校验单元从 claim 改为 tree node**。

---

## 1. 三种 evidence_source 定义

每个 framework_tree 节点必须带 `evidence_source` 字段(由 LLM 在 Step 3 标注,scripts/assemble_result.py 兜底填默认值):

| 取值 | 定义 | 何时用 | 信任级别 |
|---|---|---|---|
| `user_material` | 节点 title + 内容**直接来自用户提供的 material_files** | material_first / hybrid 模式且 ngram 命中 | **最高** |
| `curated_syllabus` | 节点来自**内置课纲库**(CET-4/6 / 408 / 考研政治...) | v1.1+ 启用 | **高** |
| `ai_inference` | 节点为 LLM 推断,**无外部锚点** | topic_only 默认 / hybrid 中未匹配 | **低** |

**优先级**:`user_material > curated_syllabus > ai_inference`

> 同一节点 evidence_source 不可同时取两值;若一个节点既出现在 material 中又匹配课纲库,优先标 `user_material`(用户原话最权威)。

---

## 2. evidence_locator 数据模型

仅当 `evidence_source ∈ {user_material, curated_syllabus}` 时,节点必须带 `evidence_locator`:

```json
{
  "id": "n2.4.3",
  "title": "隐藏虚拟(suggest / demand / insist 后 should + do)",
  "evidence_source": "user_material",
  "evidence_locator": {
    "file": "textbook-grammar-ch3.md",
    "section": "§3.4 虚拟语气",
    "page": null,
    "excerpt": "在 suggest, demand, insist 等动词后宾语从句中,谓语用 should + 动词原形,should 可省略"
  }
}
```

字段语义:

| 字段 | 类型 | 必填 | 含义 |
|---|---|---|---|
| `file` | string | ✓ | 来自哪个 material_file 的路径(相对 input.json 同目录) |
| `section` | string | ⨯ | 章节标识(优先,可读性强);若不可得用 `page` |
| `page` | int / null | ⨯ | PDF 页码(从 1 起);Markdown / DOCX 缺省 |
| `excerpt` | string | ✓ | 原文片段(15-200 字),用于 ngram 校验的 ground truth |

> **section 与 page 至少有一个非空**;两者都缺失 → audit 标 failed。

---

## 3. ngram 匹配规则(继承 paper-quick-reader)

### 3.1 文本归一化(`normalize`)

1. Unicode NFC normalization
2. 全部小写
3. 标点符号 → 单空格(`. , ; : ( ) [ ] { } " " ' '`)
4. 多空格压缩为单空格

### 3.2 分词(`tokenize`)

- 英文:按空白分词
- 中文:**逐字拆**(每个汉字一个 token)
- 中英混排:整 token 保留(如 `CET-4`、`should + do`)

### 3.3 双粒度 ngram

```python
n3 = 3-gram set 取自 normalize+tokenize 后的 token 列表
n5 = 5-gram set 取自同上
```

3-gram 抓"高频共现",5-gram 抓"原文锁定"。

### 3.4 命中阈值

```python
hit3 = |excerpt.n3 ∩ material.n3| / |excerpt.n3|
hit5 = |excerpt.n5 ∩ material.n5| / |excerpt.n5|

if hit5 >= 0.60 or hit3 >= 0.85:  verdict = "high"
elif hit3 >= 0.60:                verdict = "medium"
elif hit3 >= 0.30:                verdict = "low"
else:                             verdict = "failed"
```

> 阈值出处:与 `paper-quick-reader/references/provenance-rules.md` §6 完全一致,通过该 skill 的 calibration 套件验证。

---

## 4. 五种 verdict 状态机

| verdict | 触发 | UI 渲染 | scripts 行为 |
|---|---|---|---|
| `high` | hit5≥0.6 或 hit3≥0.85 | 绿色徽标 ✓ | 通过 |
| `medium` | 0.6 ≤ hit3 < 0.85 | 黄色徽标 ◐ | 通过(提示用户复核) |
| `low` | 0.3 ≤ hit3 < 0.6 | 橙色徽标 △ | 通过 + ⚠️ 在 audit recommendations |
| `failed` | hit3 < 0.3 | 红色徽标 ✗ | **建议 LLM 删除该节点或重写**(audit 标 user_review_required) |
| `skipped` | evidence_source = ai_inference 或 无 material | 灰色 — | 跳过(本来就不应做 ngram) |

---

## 5. 三种审计路径(scripts/verify_provenance.py)

### 5.1 路径 A · `topic_only_no_material`

触发:mode == `topic_only` 或 `--material` 为空

行为:
- 不做 ngram 匹配
- 全节点 verdict = `skipped`
- audit.summary.user_review_required = `true`(强制)
- audit.summary.ui_banner_required = `true`
- banner_message = "本框架完全为 AI 推断,建议核对教材"

例:`demos/knowledge-framework-builder/result-fixtures/topic-only-cet/provenance-audit.json`

### 5.2 路径 B · `ngram_node_level`

触发:mode ∈ {`material_first`, `hybrid`} 且 `--material` 非空

行为:
- 标准化 + tokenize 全部 material 文件
- 构建 haystack 的 3-gram / 5-gram 集合(每条 material 一份)
- 对每个 evidence_source = `user_material` 的节点:
  - 取 evidence_locator.excerpt → tokenize → 算 hit3 / hit5
  - 按 §4 状态机给出 verdict
- 跳过 evidence_source = `ai_inference` 的节点(verdict = skipped)
- audit.summary.high_ratio < 0.60 → ⚠️ 触发"整篇置信度降级"(沿用 paper-quick-reader 的 DEGRADED_HIGH_RATIO_THRESHOLD)

### 5.3 路径 C · `curated_syllabus_match`(v1.1+)

触发:节点 evidence_source = `curated_syllabus` 且本课程命中内置课纲库

行为:与路径 B 类似,但 haystack = 内置课纲库的 markdown 文件

---

## 6. 节点 vs claim:与 paper-quick-reader 的差异

| 维度 | paper-quick-reader | knowledge-framework-builder |
|---|---|---|
| 校验单元 | claim(摘要卡 7 字段)| tree node(每个节点)|
| 平均单元长度 | 50-150 字 | 5-30 字(title)+ 0-500 字(explanation)|
| ngram 阈值 | 同 §3.4 | 同 §3.4(继承)|
| Provenance 字段 | `evidence_locators[]` 数组 | `evidence_locator` 单值(节点单源)|
| 整篇降级 | 0.60 / 3 个 failed | 同标准 |
| 跨语言 paraphrase 自动放宽 | ✅ | ✅(同算法)|

### 为什么节点单源(单 evidence_locator)?

- 论文摘要卡的一个 claim 可能拼接多段原文,需要数组
- 知识框架的一个节点 title / explanation **应当能被材料的连续一段定位**;如果不能,说明分类粒度不当(应拆成两个节点)

---

## 7. UI banner 强制规则(SKILL.md 核心原则 2)

| audit 状态 | banner | 文本(可定制)|
|---|---|---|
| topic_only | ⚠️ 红 | "本框架完全为 AI 推断,建议核对教材" |
| material_first 且 high_ratio ≥ 0.7 | ℹ️ 绿 | "节点级溯源完成,X/Y 高置信度匹配" |
| material_first 且 high_ratio < 0.6 | ⚠️ 黄 | "节点级溯源置信度偏低,建议复核 N 个 failed 节点" |
| hybrid 且 ai_inference > 50% | ⚠️ 黄 | "AI 推断节点占比 XX%,建议追加 material_files" |

`render_outputs.py` 通过读取 `result.json.warnings[]` 自动注入 banner 到 markdown / markmap.html / mermaid.md / opml(后者写入 `<outline _note=...>`)。

---

## 8. 已知不完美的地方(诚实陈述)

1. **章节级 vs 段落级粒度**:本规范当前以"节点 1 个 evidence_locator"为前提,但叶子级节点("affect vs effect")可能横跨原文多段,届时 excerpt 选哪段成为人工/LLM 判断题
2. **课纲库膨胀风险**:v1.1 内置课纲后,curated_syllabus 优先级如何与用户私有教材冲突?暂定:用户 material 优先,但 audit 输出双锚点对比
3. **跨语言匹配**:用户 material 是中文教材但 LLM 用英文术语标 title 时,ngram 命中率会偏低;v0.5 起需要加 paper-quick-reader 同款的 paraphrase 自动放宽

---

## 9. 调用脚本

```bash
# topic_only / 无 material → skipped audit
python3 scripts/verify_provenance.py \
    --result result.json \
    --out provenance-audit.json --pretty

# material_first / hybrid → ngram 匹配
python3 scripts/verify_provenance.py \
    --result result.json \
    --material textbook.md notes.md syllabus.md \
    --out provenance-audit.json --pretty
```

退出码:`0` 完成 / `1` 参数错 / `2` result.json 缺关键字段。

---

## 10. 与本 Skill 其它文档的引用关系

- `SKILL.md` Step 7 → 本文档 §5(三种审计路径)
- `framework-rubric.md` §7 → 本文档 §1(evidence_source 取值)
- `concept-dependency-taxonomy.md` §3 → 本文档 §2(若依赖来自材料,locator 字段相同)
- `examples-index.md` → 本文档 §5.1 的 fixture 路径
