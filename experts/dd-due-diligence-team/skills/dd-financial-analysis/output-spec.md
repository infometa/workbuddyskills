# 财务专项报告输出规范

本规范适用于**独立财务专项报告**流程（`standalone-report.md`）。与画像/经营/行业专项报告架构一致：章节结构来自报告模板库，正文由 LLM 自由撰写完整 Markdown，全部数值与表格由确定性脚本产出。

> 后端受控 narrative 路径（`dd-report` 的「财务专项报告模式」+ `render.py`）另有契约，见 `render.py` 与后端 `finance-report-generation.service.ts`，不适用本规范。

## 一、职责边界

| 环节     | 责任方                                                   | 边界                                                                                              |
| -------- | -------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| 章节结构 | 报告模板库（`search_templates` + `get_report_template`） | **必须实调工具取模板**；标题/顺序/层级逐字照用 `chapterOutline`，逐章遵循 `chapterList[].content` |
| 数值计算 | `calculate.py`                                           | 单位换算、四则运算、比率、期间变化、阈值比较、计数、行业差异                                      |
| 表格排版 | `tables.py`                                              | 14 张 Markdown 表格 + 可引用数值事实字典                                                          |
| 正文撰写 | LLM                                                      | 在模板给定骨架内做定性分析、结论、风险归因、核验措施建议                                          |
| 数字守门 | `verify.py`                                              | 正文数值逐项回算，不一致不得交付                                                                  |
| 结构守门 | 章节完整性自检                                           | 定稿标题与模板 `chapterOutline` 逐条比对，缺章/改名/合并不得交付                                  |

## 二、数据引用契约（红线）

报告正文里出现的**任何数字**，必须能在 `tables.py` 输出中找到：

1. **表格**：整段插入 `tables[key].markdown`。禁止誊抄、重排、删减行、修改单元格数值。表头前标明单位。
2. **正文数值**：从 `facts[key].display` 复制（已含单位/百分号/倍/天）。禁止：
   - 对 `facts[key].value` 做任何再运算（含加减乘除、求同比、求占比）
   - 给 `display` 追加单位（会造成重复单位）
   - 写入 `facts` 与 `tables` 都没有的数字
   - 用记忆、上下文或其他期间数据推测缺失值
3. **缺失处理**：`tables[key].available === false` 或指标 `computable === false` 时，对应小节写「无」或明确说明该项资料未覆盖。表格内缺失值保持脚本输出的「—」。
4. **第三方数据**：新闻、搜索摘要中的数字不得作为公司财务事实写入正文，只能作叙述背景并标注来源性质。

### tables.py 可用表格键

| 键                                                                         | 内容                                             |
| -------------------------------------------------------------------------- | ------------------------------------------------ |
| `balance_sheet` / `income_statement` / `cash_flow`                         | 三表科目 × 最多五期                              |
| `balance_sheet_changes` / `income_statement_changes` / `cash_flow_changes` | 显著异动前五 + 同比 + 复合变化                   |
| `balance_sheet_notes` / `income_statement_notes` / `cash_flow_notes`       | 异动科目附注明细 + 占比 + 贡献                   |
| `metrics`                                                                  | 15 项标准指标 × 最多五期                         |
| `consistency`                                                              | 三表配平校验（BS-01~~08 / IS-01~~02 / CF-01~11） |
| `signals`                                                                  | 命中的规则信号                                   |
| `industry`                                                                 | 同业对标（含 Z 值）                              |
| `cross_validation`                                                         | 外部交叉验证                                     |

### tables.py 输出结构

```json
{
  "ok": true,
  "company_name": "某某企业",
  "display_unit": "万元",
  "periods": ["2023年度", "2024年度", "2025年度"],
  "tables": {
    "metrics": {
      "title": "标准财务指标（15 项）",
      "markdown": "| 指标大类 | ... |",
      "available": true,
      "note": ""
    }
  },
  "facts": {
    "current_ratio": {
      "key": "current_ratio",
      "name": "流动比率",
      "category": "偿债能力",
      "formula": "流动资产/流动负债",
      "value": 1.18,
      "value_type": "ratio",
      "display": "1.1800",
      "previous_value": 1.42,
      "previous_display": "1.4200"
    }
  },
  "consistency": {
    "all_computable_checks_passed": false,
    "critical_failed": false,
    "failed_count": 1,
    "critical_uncomputable_count": 0,
    "failed_ids": ["BS-02"],
    "uncheckable_ids": []
  },
  "signals": [
    { "rule_id": "BR-07", "name": "应收增速快于收入", "condition": "...", "severity": "medium" }
  ],
  "industry_usable": true,
  "summary": {
    "current_period_calculation_ready": true,
    "standard_metric_gaps": [],
    "must_re_extract": false
  }
}
```

## 三、报告结构（章节骨架必须来自模板库）

**唯一来源**：`search_templates("财务分析报告模板")` → `get_report_template(templateId)` 返回的 `chapterOutline`。

硬性要求：

1. 必须实际调用上述两个工具，并把 `get_report_template` 的结果落盘到 `/workspace/work/report-template.json`。
2. 报告标题**逐字照用** `chapterOutline`（序号、名称、层级、顺序全一致），不增、不删、不合并、不改名。
3. `chapterOutline` 的每一条（含子章节）都必须在报告中出现；资料不支持时**保留标题**，正文写「无」。
4. 逐章满足 `chapterList[].content` 的「必须包含的内容」「行文要求」「参考篇幅」。
5. 交付前执行章节完整性自检（`standalone-report.md` 第 10.5 步），未通过不得调用 `save_finance_report`。
6. `search_templates` 与 `list_report_templates` 均未找到财务分析类模板时，**不得静默套用兜底结构**，须先经 `ask_user_question` 让用户确认，并在文末披露「章节结构未经模板库确认」。

### 表格挂载对应关系

按模板实际章节的**语义**挂载脚本表格（以模板章节名为准，不要用下表反过来改模板）：

| 模板章节语义         | 引用的脚本表格                                 | 要点                                                                                 |
| -------------------- | ---------------------------------------------- | ------------------------------------------------------------------------------------ |
| 总体概况 / 摘要      | `facts`（四力关键指标）                        | 按模板篇幅要求，开头一句含偿债+盈利+现金流                                           |
| 数据标准化与来源     | —                                              | 口径-来源-映射-校验-可靠性；不评价经营                                               |
| 资产负债表           | `balance_sheet` + `_changes` + `_notes`        | 先结构变化，再关键科目佐证                                                           |
| 利润表               | `income_statement` + `_changes` + `_notes`     | 收入成本-期间费用-非经常-盈利质量                                                    |
| 现金流量表           | `cash_flow` + `_changes` + `_notes`            | 经营/投资/筹资三类，说明钱从哪来去哪                                                 |
| 三表勾稽自查         | `consistency`                                  | 先写通过/差异数，再写原因与措施                                                      |
| 财务比率 / 四力      | `metrics`                                      | 偿债 / 盈利 / 营运 / 成长逐项                                                        |
| 财务异动识别         | `*_changes` + `signals`                        | 按风险优先级组织，非字段罗列                                                         |
| 同业对标             | `industry`                                     | 行业与基准年度自动取自企业档案与铺底材料；未命中行业或样本不足时写明原因，不编造基准 |
| 盈利质量             | `facts`（净现比/收现比等）+ `cross_validation` | 每项按指标变化-参照-原因-影响-核验                                                   |
| 表格输出规则类子章节 | —                                              | `content` 全为写作规则时按规则在本章执行，自检清单标注 `规则型-已执行未成章`         |

文末统一附「资料与核验事项」：缺件、数据与计算边界、来源冲突、采用资料清单、未执行的验证。这是唯一的完整披露位置，不散落在正文。模板未含该章时作为附录追加，不计入模板章节数。

## 四、写作规范

- **篇幅充分**：专项报告不是摘要。每小节都要有实质分析；表格后先写 30-80 字事实总结，再展开分析段。
- **表格只呈现数据**，不把原因分析混入单元格。
- **区分事实层级**：客户进件事实、官方公开披露、第三方背景、脚本计算结果、业务推断必须可区分。
- **风险表述**：命中风险按高、中、低排序，每条写明形成原因、确定影响、核验措施。`signals` 是机械信号，不是造假认定、风险评级或审批结论。
- **原因须标依据**：缺少材料时写「可能/需核验」，不得写成企业已确认事实。
- **期间口径**：最近一期不年化；同比只与上年同期比较。
- **不估算授信额度**，不给审批结论。

## 五、保存契约

最终交付通过 MCP 工具完成，**不向沙箱 reports/ 写 JSON 追溯文件**：

1. `get_project_finance_reports(projectId)` → 版本号 = 已有最大版本号 + 1（无则 v1）
2. `create_report_upload_url(projectId, "财务专项报告.docx")` → `uploadUrl` + `cosKey`
3. HTTP PUT 上传 DOCX 原始字节到 `uploadUrl`
4. `save_finance_report(projectId, content, versionLabel, docxCosKey)`
   - `content`：完整报告 Markdown（不是摘要或大纲）
   - `docxCosKey`：第 2 步的 `cosKey`，缺省则前端无法下载 DOCX

后端保存成功后会把项目状态推进为「分析中」，并通过 SSE 通知前端刷新版本列表。只有工具返回报告版本才算生成完成。

## 六、交付前必过闸口

```bash
# 1. 权威表格与事实
python3 <scripts_dir>/tables.py --from-result --unit 万元 \
  < /workspace/work/financial-result.json \
  > /workspace/work/financial-tables.json

# 2. 正文数字回算校验（claims 覆盖正文引用的全部指标）
python3 <scripts_dir>/verify.py < /workspace/work/verify-input.json
```

`verify.py` 退出码 `0` 且 `verified:true` 才可交付；退出码 `2` 时按 `mismatches[].authoritative` 逐项修正正文后重复校验。禁止跳过该步直接保存。

**3. 章节完整性自检**：把 `/workspace/work/report-template.json` 的 `chapterOutline` 与定稿标题逐条比对，输出自检清单（见 `standalone-report.md` 第 10.5 步）。存在缺章、合并、改名、顺序错位时**禁止**调用 `save_finance_report`。

两道闸口必须**同时**通过才允许保存。
