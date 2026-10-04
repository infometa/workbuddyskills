---
name: tc-chengxin-analysis
description: 同程查询动态链路：简单检索直接渲染，偏好、比较、约束和行程规划进入专家分析。
---

# 同程专家查询与产物

只用于专家渠道。

## 取数

先按查询 Skill 完成必要澄清；关键条件未确认就停在提问。泛问推荐遵循免追问规则。仅比较用户数据不进入本 Skill；明确要当前价格、库存、班次、房态、开放或可订状态才实时查询。

用查询 Skill 的真实 Base directory 定位脚本：

    node "<本 Skill Base directory>/scripts/run-query-with-analysis.js" --query-script "<tc-chengxin-search Base directory>/scripts/<query-script>.js" -- <查询参数>

travel-query.js 在分隔符前加 --intent itinerary（每日安排）或 --intent selection（套餐比选）。分隔符后仅在槽位无法表达时用业务 `--query`。包装器自动处理Token和客户端；未登录或401才授权，成功后只重试一次。

无偏好、比较、约束或规划的票务/酒店/景点自动 direct 直出，不询问回复模式；火车城市/站点对缺日期由包装器按中国时区自动补次日，机票缺日期仍由查询 Skill 追问。明确要求专家解读或已有取舍条件时自动分析。`--response-mode expert` 仅供已明确的专家意图强制使用，不进入业务 query。

`direct_render` 会提示用户自然补充偏好；同一对话后续只做筛选或比较时，读取[复用本次结果继续筛选](references/follow-up-selection.md)，不要直接重新查询。

只读取 `WORKBUDDY_VISUAL_JSON_START/END` 中的回执，严格执行 `nextAction`：

- `stop_no_results`：说明无结果，不生成空方案。
- `deliver`：执行 `allowedCalls`；原样输出 `finalAnswer`，否则只读 `allowedReads` 的 reply.md。
- `run_completion_batch`：只执行一次固化的并发补查，不重新提槽或逐项试查。
- `write_plan`：严格按 `actionSequence`；只读 `allowedReads`，必要时才读 `conditionalReads`，写入 `planFilePath` 后按 `allowedCalls` 的完整参数执行渲染。
- `auth_required`：转授权 Skill；`stop_with_partial_result` 用成功资源交付并说明缺失类别。

不读 `allowedReads` 外的候选页、源码、帮助、旧快照和证据分片；不得运行 `--help` 猜命令。只有当前回执字段缺失或损坏时才读 `recovery.manifestFilePath`；重试服从 `retryBudget`。

## 复杂请求一次形成方案

按回执 planLimits 只加载当前复杂度所需内容，读完直接写plan：

- simple-selection：只读 decisionFiles，按 quickPlanTemplate 写短plan。
- complex-selection：读[单项比选](references/plan-selection.md)；首页不能核对硬条件才读 candidateFiles。
- [每日行程](references/plan-itinerary.md)：连同[通用契约](references/plan-contract.md)读取；只有某类硬条件或排期不足才读对应 candidateGroups。多快照只合并当前需求，缺项不降级成套餐。

conditionalReads 中的 candidateFiles/candidateGroups 不控制产物，且只在其 condition 成立时读取；只比较同组已返回字段。酒店距离核对参照点，unknown库存不当有票。用户数据注明“按您提供的信息”；不由评分、星级、价格或名称推断未返回事实。缺少影响选择的事实时最多一批展开：

    node "<detailScript>" --snapshot "<snapshotFilePath>" --ref "<真实ref>"

可重复 --snapshot/--ref；只读返回的 detailFiles，不重查。未知不当已满足；先核对用户条件，再比较真实代价。复杂表达才参考[自然解读](references/expert-interpretation.md)。

plan 遵守 planLimits：summary 只写结论、主要理由和关键提醒，max 是上限。简单查询不重复解读，复杂取舍才写 interpretation。通用价格、余票、库存和退改提醒不进 confirmations；可见文案不用内部术语，不写“全网最低”“首选”或未由返回字段支持的地域适配结论。

用文件工具把 plan 一次写到回执给定的 `planFilePath`，随后原样执行 `allowedCalls[0].script` 与 `allowedCalls[0].args`；不自行拼参数。多快照参数已按主查询在前固化。校验失败只修正一次，不重查或删除日期/时刻绕过；仍失败说明限制。

## 快速交付

`nextAction=deliver` 后先执行 `allowedCalls`。简单直出原样输出 `finalAnswer`；复杂分析只读 reply.md。展示失败按预算重试并说明；不再摘要、重排或删链接。完整资源在 HTML/完整 MD 中。

不写草稿、不做全文或分片检查、不读旧渲染JSON；不编造展示成功或文件链接。
