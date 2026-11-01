# 自动测试与代码审查

适用于已有项目的检查。使用本 Skill 的运行脚本及固定执行循环，不另写等待器。安全扫描同类但入口和恢复路径不同，见 [扩展能力](extend.md)。

## 入口和范围

| 用户意图 | 一次提交 |
|---|---|
| 自动测试刚完成的功能 | `superun-ai chat test <sessionId> --timeout 600` |
| 审查刚改动的代码 | `superun-ai chat review <sessionId> --timeout 600` |
| 指定检查范围 | 上述命令加 `--input <file>`，JSON 为 `{"content":"用户原文"}`；也支持互斥的 --message，本地附件使用 --file 上传，不构造内联附件 |
| 跟进测试报告的问题 | `superun-ai chat send <sessionId> --test-followup <autoTest.sourceMessageId> --input <file> --timeout 600` |
| 跟进审查报告的问题 | `superun-ai chat send <sessionId> --review-followup <codeReview.sourceMessageId> --input <file> --timeout 600` |

不传内容时按 CLI 默认检查最近完成的内容；指定范围必须原样提交，空白内容不合法。test/review 会先告知确认的问题，再自动修复，不是只读查询，不承诺免费。明确要求后直接执行，讨论是否需要检查不触发，也不因研发完成自动执行检查。已有“审查后测试”授权在条件满足时继续有效，无需再确认。

同一 Session 串行执行，不并发 test/review/send。探索阶段、在途工作或待回答业务交互先按现有流程处理；CLI 允许已完成研发结果附带 SELECT_FEATURES 时直接检查，不能强迫用户先选择更多功能。不要将首次清单当作已完成研发。业务前置条件由 CLI 检查，不绕过。

## 等待与恢复

test/review 默认等待检查、独立后台回执、必要修复和主会话最终报告。主消息结束、后台检查结束或子会话列表为空都不证明整轮结束。先保存原进程句柄；CLI 返回 RUNNING 或 waitTimedOut 后仅按原 sessionId/messageId 继续 chat wait，不重发 test/review。未知写入结果先查一次 state；过期来源重新查询，不能用旧报告的编号猜当前问题。

- `conversation_message`：及时展示 data.messages 中真实发现和修复前告知，同一 sessionId + 消息 id 更新正文，不重复追加；过程事件不触发完成菜单。
- `task_progress`：展示当前功能与 steps/stepProgress，保持步骤顺序。工具次数和功能步骤数不代表检查问题数或通过数。
- `task_reminder`：原样展示 data.message 并链接 data.url；同一 data.id 去重，不同 ID 即使文案相同也展示。继续等原进程，不自行发起定时查询。

以上事件都不是最终结果。完整结果来自原命令 stdout JSON，不能只读日志或报告网页。

## 读取报告

`autoTest.phase` 为 test/repair，`codeReview.phase` 为 review/repair；分别保留 sourceMessageId、reportMessages、可选 previousSourceMessageId/previousReportMessages 和 error。当前 reportMessages 是本次最新报告，上一份仅追溯旧问题与编号。报告网页或截图只作辅助，不能替代对话内报告。报告缺失、error 或正文结论不足时说明无法得出有效结论。

有问题时先给“本次自动测试/代码审查发现 N 个问题，已修复 M 个，未修复 K 个”，再逐项列问题、修复内容或未修复原因。数字和详情必须来自实际报告，缺失则说明缺失，不补零、不从关键词或步骤状态机械推断。区分实际检查范围、已检查、承诺范围内未检查，以及范围外未覆盖内容。

`COMPLETED`、修复完成、复测通过、复审通过、部署验收是不同事实。没有复测/复审证据就不能说通过。修复后返回 development.previewUrl 时按 [全部端入口](project-links.md) 展示 development.routing 的各端预览，单端给“查看预览”、多端逐项列出并引导进入；缺少 routing 时用原基础链接。不拼 URL、不把预览称为正式发布，也不替换检查报告的条件引导。

## 按报告筛选后续动作

`nextActions.when` 是必须判断的展示和执行条件，不可丢弃后把所有候选列成菜单。解释器只保留条件，不自动判通过或执行命令。

| 实际报告 | 允许的引导 |
|---|---|
| 审查有效完成，无遗留问题、待确认、资料缺失或本次未审范围 | 展示“自动测试 / 继续创作 / 上线运营”；自动测试验证审查涉及或修复的功能。已授权审查后测试时直接衔接，不重复确认 |
| 测试有效完成，无问题或全部修复且复测通过 | 说明范围及真实证据，展示“继续创作 / 上线运营” |
| 测试问题全部修复，尚未复测，且没有其他缺口 | 明确尚未复测，展示“自动测试 / 继续创作 / 上线运营”；不自动重启测试 |
| 仍有未修复问题、待确认规则或资料缺失 | 只引导修复剩余问题/第 X 项，或展示具体问题；结构化问题回复原 interactionId |
| 失败、暂停、中断、报告缺失、error 或结论不明 | 先报告事实，只引导排除阻碍；可重试且用户要求时才发起对应检查，不提示通过 |
| 本次承诺范围只完成一部分 | 列出已查与未查范围，仅引导指定剩余范围继续检查；范围外未覆盖不算本次未完成 |

有未修复、待确认、缺失资料、未完成范围或无效结论时，不展示正常完成、继续创作或上线菜单，也不执行预先授权的下一项检查。若用户明确改变目标，保留这些事实并按新目标继续对应阶段。

用户提出“修复第 2 项”等要求时使用对应 followup 的 sourceMessageId 与原文，继续普通对话修复，不重新启动 test/review。两种 followup 参数互斥。新功能需求走普通 send，不带报告 followup。修复结束重新按本表判断，不自动复审相同范围。

上线仅按已有明确授权转入 [上线流程](creation-flow.md#用户明确要求上线时)。检查报告不替代部署后通过真实外部入口执行改变行为的最终验收。
