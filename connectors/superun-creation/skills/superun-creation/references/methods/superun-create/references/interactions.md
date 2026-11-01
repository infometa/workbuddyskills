# 交互回复

宿主必须按 [展示协议](host-presentation.md) 实际呈现问题、选项和当前阅读内容；CLI JSON 不是展示完成证明。

使用当前 `interactionId`、`actions`、`questions/details` 和 `answerSchema`。CLI 提交前会重查交互；宿主负责把用户决定转换为输入，不复制 Card parser、Tool reply 或业务哨兵。`nextActions.input` 只有固定 action，不是完整答案，也不能不经 schema 核对就机械合并。

收集答案优先调用 [宿主原生提问工具](host-tools.md#用户提问)；不能把 superun 的 `ASK_USER_TOOL` 交互类型当作宿主工具名。仅在工具不可用或无法完整表达当前问题时降级为文本。

## 问卷一次展示、答齐后提交

PRD、ASK_USER_TOOL、ASK_USER_MESSAGE 一次展示当前交互的全部问题和全部选项：保留题目原文、选项标签及说明，标出题号、选项编号、multiSelect 和 allowOther。推荐项可以标注，不能当成用户已选。不得只展示题号/选项编号，也不重新概括成宿主自己的问题。展示编号与 question.id/options.index 保持明确映射；实际 selectedIndices 从 0 开始。提示“请按题号回答，例如1A、2B，也可以补充自己的要求”，例子不代表固定题数或答案。

用户只答了一部分时保留已答内容，一次展示剩余题目及选项，不逐题挤牙膏，也不替用户填空。答案齐全后统一提交；已有明确且仍匹配当前题目的回答不重复询问。没有用户响应就保持当前交互，不倒计时、不自动跳过。

## 功能清单分页多选

仅适用于 SELECT_FEATURES，不把需求澄清的必答规则套到功能选择：

- 使用多选弹框，每个功能对应“编号＋原始 title”的独立选项，不预选、不拼功能组合；标题包含总功能数，分页标明全局页码。说明按需展开，支持用户直接给出明确的功能编号或“全部”。
- 按宿主选项容量分页，每页保留“本页不选”入口；此项表示本页选择为空，不是功能，也不取消其他页的选择。与本页真实功能同时选中时只澄清该页，不替用户决定。
- 一次弹框收多页答案、或逐页分别收答，都先按 sessionId、interactionId 和页码暂存结果；回改同一页覆盖该页选择，其他页保留。超过单次题数限制时继续下一批弹框，以页码区分，不能因 interactionId 相同跳过后续页，也不重复询问已完成页。
- 全部页明确选择或明确不选后，汇总真实 featureIds、去重，一次性提交 SELECT；不能边翻页边发开发请求。“本页不选”不传给 CLI；全部不选时说明未启动开发。关闭、取消、缺失回答不当成不选，也不提交已收集的部分结果。交互已过期时重新读取当前清单，不沿旧编号提交。

| kind | 回答与后续 |
|---|---|
| PRD_CLARIFICATION | `action: GENERATE_STYLES`（可省略）和 answers；不传已移除的 styleCount，首次固定生成一个方案；当前无 REFINE。提交后 CLI 自动生成风格，不再问是否生成，也不重复调用 style generate |
| ASK_USER_TOOL / ASK_USER_MESSAGE | 按 schema 提交 answers 和允许的 action；普通问答通常 SUBMIT，可跳过时使用 skip 命令；不以 chat send 代替 reply |
| SECRET_INPUT / PLUGIN_SECRET_INPUT | `{"values":{"当前要求的键名":"安全输入值"}}`；只提交 details.keys 要求的键，安全输入且不回显。schema 不要求 action 时不要照搬 nextActions.input 添加字段；默认 SUBMIT 由 CLI 处理 |
| PLUGIN_ACTION | 当前动作 ENABLE/SKIP，启用时可带 config；交互归属与 Tool 回填由 CLI 处理，不能先独立 enable 再重复 Tool reply |
| DDL_CONFIRMATION | 按 details.summary 说明实际变更，用当前 action APPROVE；服务端自动批准的 DDL 不会作为该交互返回，不额外制造确认 |
| STYLE_SELECTION | 按返回 schema 填 action 和真实 choiceId；用原始 index 对应 A/B/C/D 打开当前批次预览页面并附链接，选择后 CLI 静默生成并确认规划，直接返回功能清单，不构造 URL |
| ENTER_IDEATION | 当前 action ENTER，主要用于旧 Stage0 会话；不要给新建项目强行加这一步 |
| APPROVE_ARCHITECTURE_PLAN | stylePlanning 中唯一规划审批且允许 APPROVE 时继续 chat wait，由 CLI 内部处理，不手工批准或展示审批；其他独立规划调整展示当前规划原文及“确认规划 / 调整功能”；明确确认才 APPROVE。调整内容原文通过 chat send 提交，等更新方案或问题后再次展示入口，不能确认旧方案或将修改塞进 APPROVE |
| SELECT_FEATURES | 首次清单按 CLI 顺序展示全部“编号＋完整功能名称（details.features[].title）”，description 在用户追问时展开，不能只给编号或改写名称；用本渠道多选弹框按上述分页规则收答，工具不适用时提示回复编号或具体需求。直接需求原文走 chat send；用户明确选择清单后 `{"action":"SELECT","featureIds":[真实ID]}`，支持明确全选，不默认全选或用序号代替 ID；确认规划不是全选。已有 development.previewUrl 时按研发完成引导展示代码审查/自动测试/安全扫描/继续创作/上线运营；有检查上下文时优先按质量检查的条件引导 |
| START_EXECUTION | 当前 action EXECUTE，若 schema/来源允许 featureIds 才携带；不要自己填 planBatchId 或后端 extra |

PRD 示例（ID 与选项仅示意）：

```json
{"action":"GENERATE_STYLES","answers":[{"questionId":"q0","selectedIndices":[1],"otherValue":""}]}
```

普通 Ask 示例：

```json
{"action":"SUBMIT","answers":[{"questionId":"q0","selectedIndices":[0],"otherValue":""}]}
```

按下列命令提交已完成的 JSON 文件：

```text
superun-ai chat interaction reply <sessionId> <interactionId> --input <file> --timeout 600
```

SKIP 必须由该交互明确允许，并对应用户的跳过决定；用 `chat interaction skip` 避免手造跳过 payload。Secret 缺少安全输入渠道时，让用户在 CLI 的安全环境完成后继续，不能索要明文聊天密钥。

提交后回到固定执行循环读取新结果。阶段转换查 creation-flow.md；不要在这里推断应用已完成。

ReadLogs、自动批准 DDL、插件配置中的自动等待和 toolCallOwned 由 CLI/服务端处理；不额外出题、重复回填，也不把 --no-wait 当作取消插件配置等待。
