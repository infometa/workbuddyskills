# S3 洞察与关键词计划

## 输入

- 只读 `02-insight/insight-input.json`；不要再次读取 Product Detail、matrix 或 facts 文件。

## 操作

1. 从评论归纳人群、场景、痛点、期望、顾虑、信任证据和使用边界；不得把评论主观体验改写成产品参数。
2. 形成最多 20 个买家问题并标记来源；证据弱的问题保留为 `weak/unanswered`。
3. 将候选词归一为 core / scene / pain / attribute；去除竞品品牌、弱相关和无事实支撑的功效词。
4. 默认做 1 次独立语义调用并给出 `question_coverage`；“诊断并优化”已有通过 handoff 校验的同快照 Audit 洞察包时直接复用，不重复调用。评论明细只能来自用户已同意的结果。

一次输出 `kind=listingInsightBundle`、`schema_version=1`，包含 `insight_markdown`、`buyer_questions`、`keywords`；不要分别写三次文件。

## 输出

- `insight.md`：紧凑的四柱与买家问题摘要。诊断结论、问题描述与建议一律用中文书写（引用的关键词、原文片段保留原文），不因目标站点是英文站而改用英文。
- 洞察 bundle 落盘后运行一次 `run_pipeline.py prepare-write`。脚本严格校验并拆出原有 `insight.md`、`buyer-questions.json`、`keywords.json`，回填 matrix 证据，同时生成 `spec.json` 与紧凑 `writer-input.json`。

  `keywords` 必须是四组词 JSON；形状不合法立即失败。脚本只做无损归一和证据回填，不参与语义分类。
  用户手输词必须 `source=user` + `search_volume=null`；四组全空时标 `keyword_data_unavailable`，不要落空壳文件。

  `locked` / `banned` 的正式产物是字符串数组；脚本也兼容 `{word, source, search_volume}` 对象并无损归一。
  `locked` 必须已存在于四个词组；品牌名由 `spec.brands` 传递，不要放入 `locked`。
  `locked` 进 `spec.keywords.locked`；`banned` 与 `--banned-terms` 合流后按 `banned_term` 校验。
  `--matrix` 只回填证据，绝不根据 `field` 猜词类；禁止先尝试传入 `scored_table`、失败后再改格式。

## 词表回写（`[fieldAdjust:keywords]`）

出稿后用户在词表工作台调整时触发，**不重跑采集与洞察**，零新增付费检索。
正文四种子句可任意组合，逐条落到 `keywords.json`：

| 子句 | 动作 |
| --- | --- |
| `锁定：A、B` | 追加到 `locked`，写作时必须埋入 |
| `禁用：A、B` | 追加到 `banned`，强度等同避讳词 |
| `移入标题：A、B` | 把已有词迁移到 `core` 组 |
| `新增并锁定：A、B（场景词）` | 词表中不存在的新词，按括号内词类写入对应组，同时追加到 `locked` |

新增词由用户手动输入，没有检索数据：写 `source=user`、`search_volume=null`，
禁止为其编造 volume/rank（同 `keyword_data_unavailable` 判定）。
词类到字段的落位规则不变：core→Title、scene/pain→Bullet Points、attribute→Item Highlights 与后台属性，装配口径以 `build_spec.py` 的 `keywords` 块为准。

回写后：重装配 spec → 只重写受词表变化影响的字段 → `validate_fields.py` 只校验该字段
→ `run_manifest.py update` 回写 manifest；其余字段逐字不变。

## 用途

Writer 消费问题映射和字段词表；JSON/Markdown 摘要复用同一来源。

- **落盘**：只保存摘要和结构化问题/词表，不复制完整评论和 SIF 全表。
- **读取**：Writer 只读 Top N 与四柱摘要。
- **判定**：无 SIF 成功数据时标 `keyword_data_unavailable`，禁止伪造 volume/rank。
