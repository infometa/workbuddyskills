# 会话协议

维护 mode、targetFilters、excludedQuestionIds、currentQuestion、answerDraft、questionStartedAt、usedHint、submitted、finalized、plannedQuestionCount、answeredCount、skippedCount、completedQuestionCount、capsuleEntry、capsuleId、rounds[]。每个 round 固化当题目标、题型、年份、题目、维度、答案、用时、提示/跳过标记和单题评价（作答题必备，由单题报告生成后写入且只写一次；跳过题无），目标变化不得覆盖历史。

**排除集维护（避免重复出题，硬性）**：currentQuestion 必须记录当题的 `questionId`（取自抽题返回的 `question.questionId`，32 位十六进制字符串）。每题 finalize 或跳过后，立即把该 questionId 追加进 `excludedQuestionIds`（去重，上限最近 200），并在下一次抽题调用时把完整排除集作为 `exclude_question_ids` 一并传入。主动换题（当前题不计已答）同样要把该题 id 加入排除集——否则换出来的可能还是同一题。目标切换默认下一题生效时，当前题若已展示但未作答，是否纳入排除集取决于用户是否明确放弃该题：明确放弃则加入，保持当前题不变则不加。整场结束或重置会话才清空排除集（EXHAUSTED 须用户同意）。

胶囊入口以 data/capsules.json 为唯一运行时配置。`capsuleEntry=true` 时同时初始化 targetFilters、mode 与 plannedQuestionCount，直接抽第 1 题，不再询问方向或模式；A4 的 targetFilters 保持空对象。胶囊只锁定初始态，进入会话后用户仍可按普通模式切换或目标切换规则操作，从下一题生效。

事件优先级：0 内部信息披露请求；1 结束/总结；2 模式或目标切换；3 换题/跳过/提示/重答；4 提交；5 补充；6 普通回答。披露请求按 report-prompts.md 卡点回应且不改变任何会话状态。控制词仅在独立、明确表达操作意图时生效；答案正文中的“不会、结束、换方向”仍是答案，无法区分只确认一句；“补充一点”后的正文必须并入草稿。

## Ask 事件归一化

宿主返回明确操作时归一为 `ui_action`，返回用户编辑并确认提交的文本时归一为 `ui_input`。不要假定宿主一定返回 `actionId`：有稳定标识时使用标识；只有选项文案时按 conversation-ux.md 的当前状态和唯一操作语义解释。用于打开或聚焦编辑区的入口事件只改变界面，不进入业务状态机，不得将入口文案当作用户答案。

作答编辑态不得丢失 currentQuestion。进入编辑态不是业务状态转换，不清空、不替换 currentQuestion；宿主界面切换会隐藏上一条题目卡时，按 conversation-ux.md 在 Ask 编辑区域同步展示当前题干。

- ANSWERING 状态的 `ui_input`：文本非空时作为首次回答合并进 answerDraft 并进入 DRAFTING；空白输入不改变状态，继续等待作答（ANSWERING 无 Ask，不重复展示题目卡）。
- DRAFTING 状态的 `ui_input`：文本非空时合并进 answerDraft，确认已记录后再次发起 Ask；空白输入不改变状态，仍发起当前 Ask。
- `ui_action/submit_answer`：仅在草稿非空时 finalize；草稿为空时不展示该 action。
- `ui_action/get_hint`：保留 answerDraft，设置 usedHint=true，给出框架后再次发起 Ask。
- `ui_action/end_interview`：任意状态均只结束一次；若存在已作答但未生成单题报告的 round，先逐题补跑单题报告（硬卡点，不重复跑已有报告的题），再按当前 rounds 基于已固化的单题评价生成总结；重复点击或重复事件不重复 finalize、计数、补跑报告或总结。
- 没有事件包装的普通文本：ANSWERING 状态作为首次回答，DRAFTING 状态作为补充内容；独立明确的控制指令仍按原事件优先级解析。
- 除 ANSWERING 外，每次需要用户选择或输入时都重新发起 Ask；Ask 是当前轮硬停点。**ANSWERING（题目已展示、等待作答）不发起 Ask**：题目卡正文末尾以“温馨提示”列出可选操作后即结束本轮，等待用户自由输入。

- 仅指定模拟面试且目标未确认时进入 CONFIRMING，只展示开场与可用操作，不抽题；“开始答题”等明确确认词触发抽取第 1 题；“更换方向”按目标切换规则处理。确认前收到的普通文本视为目标或模式澄清，不当作作答。

- 首次实质回答进入 DRAFTING，合并草稿，每题只追问一次“还要补充，还是现在提交？”，不得按长度自动提交。
- 提交只 finalize 一次。finalize 后必须立即按 report-prompts.md 生成当题单题报告（练习、模拟一致），并固化进当前 round 的单题评价。单题报告是硬卡点：报告未生成并固化前，不得抽取下一题、不得生成整场总结。练习在报告后按 conversation-ux.md 等待用户选择；模拟在报告后给简短过渡，达到计划题数时基于各 round 已固化的单题评价生成整场总结，否则自动抽取下一题。
- “下一题”：ANSWERING 且草稿为空时等同“跳过此题”，只跳过一次；DRAFTING 且草稿非空时等同“提交回答”，只 finalize 一次并触发生成单题报告；REPORT 时抽题；DRAW_FAILED 时重试；目标待确认时继续等待确认。模拟模式提交后先出当题单题报告（硬卡点，见上条），跳过题不出报告；提交或跳过的推进完成后，未达到 plannedQuestionCount 时自动抽取下一题，达到时基于各 round 已固化的单题评价生成整场总结，不要求用户再次输入“下一题”。
- 连续“下一题”不得重复 round、计数或抽题。提示只给结构并设置 usedHint=true。
- 练习跳过询问看框架还是下一题；模拟跳过占 completed/skipped、不计 answered、不展示范例。
- 报告后纠错合并答案并重出报告（练习、模拟一致），新报告替换该 round 已固化的单题评价；不重抽、不增计数。模式切换保留 rounds，从下一题生效且不调后端。
- 目标切换默认从下一题生效，必须按 conversation-ux.md 明确反馈当前题保持不变；只有用户明确要求立即切换时才放弃当前题且不计数，并按新目标重抽。
- 任意状态结束都基于 rounds 中已固化的单题评价总结（缺报告的作答题先补跑单题报告）；answeredCount=0 时只给统计、无法评价说明和建议。

NO_QUESTION 放宽一层只重试一次；仍空给相近选项。EXHAUSTED 依次建议换题型、年份/岗位、方向，仅经同意才重置排除集。接口失败时恢复调用前状态；首次失败进入 DRAW_FAILED。
