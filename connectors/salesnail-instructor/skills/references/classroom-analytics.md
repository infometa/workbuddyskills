# 课堂数据分析与报告

## 推荐顺序

1. `salesnail_list_courses`
2. `salesnail_get_classroom_data_dictionary`
3. 选择班级、团队、学员或商机分析
4. 使用 `salesnail_query_classroom_data` 补充证据
5. 按报告模板在当前 CLI 撰写 Markdown/文档

数据集包括 course、teams、members、actions、messages、opportunities、npcs、cards、rounds、rules、materials 和 favorability_history。

查询可按 team、round、opportunity、NPC、card、learner、auditStatus、messageKind、时间或 evidenceId 过滤。正式报告可使用 `anonymizeLearners=true`。普通用户不要请求 `includeRaw=true`。

撰写正式轮次、结案、商机或学员报告前读取 `salesnail://analytics/report-templates`。该资源提炼了现有 AI Dashboard 的商机/小组提示词以及轮次、结案 Map-Reduce 提示词，并保留"日志缺失但状态有进展时以状态事实为准并标注数据缺口"的一致性规则。

## 分析工具

- `salesnail_analyze_team_performance`：探索、决策链、资源、执行、对话和 Team Selling。
- `salesnail_analyze_learner_performance`：只分析可观察动作提交参与，不用于排名或绩效。
- `salesnail_analyze_class_performance`：班级基准、策略类型、共享赢单金额和复盘结构。
- `salesnail_analyze_opportunity_qualification`：Metrics、Economic Buyer、Decision Criteria、Decision Process、Paper Process、Pain、Champion、Competition、SPIN、决策链、资源和下一步问题。

机会诊断中的关键词命中只是 candidate semantic evidence，必须结合完整 NPC 回复判断。关键决策人不自动等于 Economic Buyer；高好感联系人不自动等于 Champion；需要内部推动证据才能升级判断。

历史轮次的动作可过滤，但商机矩阵通常仍是当前快照。好感度历史来自运行态缓存，可能为空或不完整。多币种不自动换汇。
