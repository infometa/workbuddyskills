# 接口版本迁移 Runbook（candao-review-expert-analysis-prod）

当餐道.数智经营连接器提供的 `get_review_expert_analysis_data` 返回 schema 再次变更时，按本流程迁移 skill。不要依赖 WorkBuddy 运行时连接器 ID。
目的：可复盘、可跟踪、不重复踩坑；并遵循「三处全量同步、回灌既有 skill、不平行新建」纪律。

## 0. 先验证，再动手（铁律：先评估不执行）
- 实跑一次工具拿真实返回（如 875KB JSON），**逐字段比对**是否真变了、与用户提供的 schema 是否一致。
- 不要凭记忆或旧文档直接改代码。先出一份「接口结构核对」文档落盘，再动 skill。

## 1. 保持 REPORT_DATA 形状（避免重写 ~55KB 模板）
- 只在 `scripts/gen_report.py` 的 `build_report_data(d)` 改「新 schema JSON → REPORT_DATA」映射。
- 模板 `references/interactive-report-template.html` 的 JS 逻辑**不动**；仅改注释 / 口径文案。
- 这样新版数据接入成本最低、回归风险最小。

## 2. 关键口径陷阱（本次踩过的）
- **字符串化列表**：`commentTags` / `badCommentTags` 是 Python list 的 str 表示（如 `"['其他原因']"`）→ `clean_tags()` 用 `ast.literal_eval` 解析；兼容旧坏格式。
- **两级标签体系**：`commentTags` = 一级原因；`badCommentTags` = 二级细粒度多层标签。两套**独立**，不可互推父子关系。
- **差评判定**：`commentLevel == '差评'`（旧 v2 是 `level == 'NEGATIVE'` 且包在 `reviewDetails` 里）。
- **回复率分母**：`badCommentCount`（旧 v2 是 `negativeReviews`）；周期级指标，无逐日折线。
- **评分字符串**：`commentScoreDistribution.commentScore` 是字符串 `'1'~'5'` → `int()` 后再用。
- **无 period 字段** → `PERIOD` 由 `dailyCommentTrends.commentDate` 去重得到。
- **比率字段**：`replyWithin24HoursPer` / `goodCommentCountPer` 是 0~1 小数 → ×100 展示；旧 skill 自算回复率逻辑可废弃。
- **dailyCommentTrends 无 reply 字段**；`platformTypeDesc` 已是中文（`ch()` 兜底英文 code）。

## 3. 三处全量同步（强制）
任一处改了口径，其余必须同步，否则重跑 skill 会按旧规则把内容还原：
1. `scripts/gen_report.py`
2. `SKILL.md`
3. `references/data-contract.md`
4. `references/report-guide.md`
5. `references/interactive-report-guide.md`
6. `references/mcp-tool-get_review_expert_analysis_data.md`（工具卡）
7. `references/interactive-report-template.html`（注释 / 口径文案）

## 4. preflight 闸门（坏数据提前中断）
- `hasData is False` → 不进 gen_report（属正常无数据，由 SKILL.md 上层按步骤 2 提示），不落盘、不编造。
- 缺 `dailyCommentTrends` / `reviewMetricSummary` / `commentScoreDistribution` / `commentDetails` → RuntimeError。
- `dailyCommentTrends` 为空 list → RuntimeError。
- 原则：坏数据 exit≠0，不出图、不 present_files、不编造报告。

## 5. 验证（用真实数据，非合成）
- `python -m py_compile scripts/gen_report.py` 必须 OK。
- 用真实返回重跑，DOM-stub 断言：回复率 = `replyWithin24Hours / badCommentCount`；评分合计 = `sum(count)`；关键面板**无 undefined / NaN**。
- `node --check` 校验模板内联 JS 语法。

## 6. 已知上游缺陷（MCP 侧，非 skill，单独报数据团队）
- **窗口左移**：传 `[start, end]`，多数数组返 `[start-1, end-1]`，第 end 天缺失；但 `badCommentSamples` 返 `[start, end]` 正常——同一响应内不一致，确认非 skill 问题。
- 修复需数据服务侧修正窗口参数；skill 层只能标注、无法根治。
