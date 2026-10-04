# 诊断报告输出

> 本文件定义**接口级输出结构**与**唯一交付格式（HTML 报告）**。面向用户的渲染必须以此数据为准；额外的"综合评价/求职赛道建议"等属于扩展内容，见文末"扩展节（非接口内容）"。

---

## 1. 接口返回结构

```json
{
  "resumeId": "<简历id>",
  "score": <总分 int>,
  "beatPercent": "<击败百分比，如 73%>",
  "reportDetails": [
    {
      "moduleCode": "<moduleCode>",
      "moduleName": "<模块中文名>",
      "diagnoseList": ["<诊断文案1>", "<诊断文案2>", "..."],
      "diagnoseNum": <本模块诊断条数 int>
    }
  ]
}
```

### 1.1 状态前置判断

- `runStatus != SUCCESS(1)`（分数未算完）→ 返回**空报告**（score/beatPercent/reportDetails 均不填）。
- `runStatus == SUCCESS` → 填分数；`reportStatus == SUCCESS`（诊断完成）→ 再填 `reportDetails`。

### 1.2 分数与击败百分比

- `score` = 六维求和结果。
- `beatPercent`：遍历 `scoreList`（配置见 `references/resume-score-config.json`），取**第一个**满足 `min <= score && max > score`（**左闭右开**）的配置，`beatPercent = "<beatPercent>%"`。
- 无命中区间则不设置 beatPercent（注意：**score = 100 恰好无区间命中**，因为最后一档 max=100 是右开）。

**scoreList 真实配置**（`resume-score-config.json`）：

| 区间 [min, max) | title | describe | beatPercent |
|---|---|---|---|
| [-2, -1) | 报告生成中，预计等待3-4分钟... | （空） | 0 |
| [-1, 0) | 你打败了0%的用户 | 智能评分，快来测一测你的简历吧～ | 0 |
| [0, 1) | 你打败了0%的用户 | 你的简历内容过少，需要认真完善相关信息哦 | 0 |
| [1, 10) | 打败了10%的求职者 | 你的简历内容较为简单，需要增加更多的实践经验和技能描述 | 10 |
| [10, 20) | 打败了20%的求职者 | 你的简历内容一般，需要提升你的专业技能和项目经验 | 20 |
| [20, 30) | 打败了30%的求职者 | 你的简历内容尚可，需要加强你的职业规划和个人定位 | 30 |
| [30, 40) | 打败了40%的求职者 | 你的简历内容较好，需要突出你的核心竞争力和职业亮点 | 40 |
| [40, 50) | 打败了50%的求职者 | 你的简历内容优秀，需要进一步提升你的职业素养和领导力 | 50 |
| [50, 60) | 打败了60%的求职者 | 你的简历内容出色，需要进一步强化你的团队协作和创新能力 | 60 |
| [60, 70) | 打败了70%的求职者 | 你的简历内容卓越，需要进一步优化你的职业规划和职业素养 | 70 |
| [70, 80) | 打败了80%的求职者 | 你的简历内容精彩，需要进一步强化你的领导力和创新思维 | 80 |
| [80, 90) | 打败了90%的求职者 | 你的简历内容极佳，需要进一步提升你的战略思维和执行力 | 90 |
| [90, 100) | 打败了96%的求职者 | 你的简历内容完美，你已经具备了出色的职业素养和领导力 | 96 |

> 前两档（min 为 -2 / -1）服务于"仅分数接口"的状态语义（计算中 -2 / 无记录 -1），见第 2 节。

### 1.3 报告详情装配

1. 取简历的模块列表，按 `sort` **升序**遍历。
   > 该 sort 由解析阶段赋值：**显示模块在前（按配置 JSON 数组序）+ 隐藏模块在后**，重新编号 1..N——不是配置里的 `sort` 字段。隐藏模块若有诊断明细（如 NO_DATA 空流 quirk 产生）也会出现在报告中。
2. 诊断明细按 `moduleCode` 分组。
3. 模块配置从 `references/resume-module-config.json` 按当前 `resumeType` 的 code 索引（`moduleConfig[resumeTypeCode]`，按 moduleCode 索引模块配置）。
4. **跳过**：模块无配置 或 该模块无诊断明细。
5. 模块内每条明细转文案（明细转文案规则）：

| diagnoseType | 文案模板 | 排序值 sort |
|---|---|---|
| NO_DATA(0) | `【{moduleName}】可以为你加分哦，去完善` | 最前 |
| NO_FILL(1) | `【{dataFieldName}】是简历中的重要信息，请完善` | 字段在 `moduleConfig.dataFieldList` 中的**下标**（字段不在配置中则**丢弃该条**） |
| DESCRIPTION_SUGGEST(2) | 明细的 `suggestContent` 原文（已是"描述建议N：\n..."格式） | 最后 |

6. 模块内按 sort 升序排列文案 → 即 **NO_DATA 最前 → NO_FILL 按字段配置顺序 → DESCRIPTION_SUGGEST 最后**。
7. 模块输出：`{moduleCode, moduleName, diagnoseList, diagnoseNum}`（`diagnoseNum` = 诊断条数）；`diagnoseList` 为空则不输出该模块。

---

## 2. 仅分数接口

供"只问分数不问报告"的场景：

| 情况 | 返回 score |
|---|---|
| 无评分记录 | -1 |
| 最新记录 `runStatus == 0`（计算中） | -2 |
| 计算完成 | 实际总分 |

同时按 `scoreList` 区间（左闭右开）取 `title` + `describe` 返回；另带 `runStatus` / `reportStatus` / `reportId` / `scoreTime`。

---

## 3. 用户面向交付：HTML 报告（唯一交付格式）

**最终只向用户交付 1 份 HTML 报告**（写入 `简历诊断报告_<resumeId>.html` 后用 `present_files` 展示）。**不渲染 markdown/文本版报告**；中间 JSON（filled/finalized/suggestions/gpt_score/report）不落盘，仅最终 HTML 报告文件落盘。报告只含返回的三部分：`score`、`beatPercent`、`reportDetails`（各模块诊断列表）。禁止添加六维得分明细、分数区间评价（title/describe 属于"仅分数接口"，不属于本报告）、综合评价等任何接口外信息（扩展内容见第 4 节）。

**渲染方式（模板驱动，禁止手写布局逻辑）**：

1. `Read` 读取模板：`assets/diagnose-report-template.html`（**静态占位符模板**，无任何脚本）。
2. 把 report.json 数据填入模板占位符，其余模板代码一字不改，得到**完整 HTML 报告内容**。
3. 将完整 HTML 写入最终报告文件（文件名如 `简历诊断报告_<resumeId>.html`），调用 `present_files` 交付给用户。

**占位符清单**：

| 占位符 | 数据来源 | 填充规则 |
|---|---|---|
| `{{RESUME_ID}}` | `report.resumeId` | 原样注入 |
| `{{GENERATED_AT}}` | 当前日期 | `yyyy-MM-dd` |
| `{{SCORE}}` | `report.score` | 有效（≥0）填数字；`-1`/`-2`/缺失填 `—` |
| `{{SCORE_RING_OFFSET}}` | `report.score` | `326.73 × (1 − score / 100)`，保留 2 位小数；无效填 `326.73` |
| `{{SCORE_RING_COLOR}}` | `report.score` | `score ≥ 70` → `#10b981`；`40 ≤ score < 70` → `#3b6ef6`；`score < 40` → `#f59e0b`；无效 → `#3b6ef6` |
| `{{BEAT_TEXT}}` | `report.beatPercent` | 有值 → `击败了 {beatPercent} 的求职者`；无值 → `报告生成完成` |
| `{{BEAT_TITLE}}` | `report.beatPercent` | 有值 → `你的简历整体表现`；无值 → `分数区间暂无可对比数据` |
| `{{MODULE_ROWS}}` | `report.reportDetails` | 按模板注释结构逐模块生成；数组为空 → `<div class="empty">暂无诊断明细</div>` |

**渲染纪律**：

1. `score` / `beatPercent` / `reportDetails` 三部分与接口一致；**不展示**六维得分明细、分数区间评价、综合评价。
2. `diagnoseList` 文案**逐条原样注入**，不得改写模板话术（`【…】可以为你加分哦，去完善` / `【…】是简历中的重要信息，请完善` / `描述建议N：…`）；描述建议类含 `\n` 换行，由 `.txt.suggest-body` 的 `white-space: pre-line` 保留。
3. 模块顺序 = `reportDetails` 数组顺序（report.json 已保证 sort 升序），模块内排序 NO_DATA → NO_FILL → DESCRIPTION_SUGGEST，**不得重排**。
4. `MODULE_ROWS` 内 tag 按文案内容分类：以「描述建议」开头 → 描述建议；含「可以为你加分哦」→ 可加分；含「是简历中的重要信息，请完善」→ 需完善；其他 → 建议。文案一律原样。
5. 分数未算完（runStatus≠1）时不出 HTML 版；`score` 为 -1/-2 时填 `—`。
6. `beatPercent` 缺失（如 score=100）时填「报告生成完成」，不展示百分比。

---

## 4. 扩展节（非接口内容，可选，追加到 HTML 报告末尾）

以下内容**不属于**报告标准返回，仅当用户要求"给整改方案/求职建议"时才追加，且必须**追加在 HTML 报告末尾**并标注"以下为扩展分析"：

- 综合评价段落；
- 按紧急/重要/锦上添花分级的整改计划；
- 求职赛道建议；
- 整改后简历草稿。
