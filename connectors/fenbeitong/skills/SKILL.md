---
name: fenbeitong-workbuddy
description: "分贝通 WorkBuddy Connector。用于账号与企业、差旅、申请单、订单、消费规则、发票报销、消费洞察、合规、降本及客服。"
description_zh: "通过分贝通 Connector 处理企业差旅、消费规则、发票报销、消费洞察、合规风险、降本机会和客服需求。"
description_en: "Use the Fenbeitong Connector for business travel, policies, invoices, reimbursement, consumption insights, compliance, cost reduction, and support."
version: "1.1.0"
author: "分贝通 Fenbeitong"
---

# 分贝通 WorkBuddy Connector

这份 Skill 指导 WorkBuddy 使用分贝通 MCP Connector。默认通过已启用的 Connector 调用工具，不要求用户提供或粘贴任何 Token。

## 适用场景

当用户需要处理以下分贝通业务时使用本 Skill：

- 查看当前账号、所在企业或切换企业；
- 查询酒店、机票、火车票，或创建和调整综合行程；
- 查询消费规则、申请单和商旅订单；
- 归集发票、生成费用草稿、创建或查询报销单；
- 查询消费金额、订单量、趋势、排行、结构或生成消费洞察；
- 筛查订单合规、违规、超标、异常、套现或重复风险；
- 分析可节省订单、金额、降本点、规则命中或优化空间；
- 查询产品规则、操作方法，或处理需要实际动作的问题。

只做普通旅行攻略、与分贝通无关的知识问答或不需要企业账号数据的请求时，不使用本 Skill。

## 使用边界

- 所有分贝通业务数据访问和业务操作都通过 MCP 工具完成；不要用本地脚本直接访问分贝通服务。
- 工具名称、参数、返回值和当前可用范围以 Connector 实时提供的工具描述为准，不凭记忆补充参数。
- 本 Skill 负责工具间的选择和多步流程，不替代 MCP Server 的鉴权、权限检查和副作用控制。
- 当前 WorkBuddy Connector 已验证模型可以读取工具结果的 `content`，但不能稳定读取 `structuredContent`。需要继续驱动流程的数据必须出现在模型可见文本中。
- `present_files` 是 WorkBuddy 平台内置的文件展示工具，不属于分贝通 MCP Server；需要展示本地 HTML 产物时按平台提供的接口调用。
- 只有工具真实返回成功时，才能声称已经查询、创建、修改、删除、提交或完成处置。

## 当前工具面

| 业务域 | MCP 工具 |
| --- | --- |
| 账号与企业 | `fbt_account` |
| 差旅 | `fbt_hotel_search`、`fbt_travel_search`、`fbt_trip_planner`、`fbt_apply_order`、`fbt_consumption_rules`、`fbt_order_search` |
| 发票与报销 | `fbt_invoice_management`、`fbt_expense_management`、`fbt_reimb_management` |
| 管控分析 | `fbt_consumption_insight`、`fbt_compliance_analysis`、`fbt_cost_reduction_analysis` |
| 客服 | `fbt_service_ask`、`fbt_self_solve` |

工具可能按账号状态、权限和渠道策略动态显示。上表只用于路由，不代表用户必然有权调用全部工具。

## 推荐调用顺序

1. 用户询问当前账号、企业或要求切换企业时，先调用 `fbt_account`。其他业务只有在当前企业不明确且会影响结果时才先确认企业。
2. 根据用户目标选择唯一匹配的业务工具；不要为了探索能力并行调用多个相近工具。
3. 调用前读取该工具当前的参数定义。缺少工具明确要求的关键信息时再向用户追问，不让用户填写一份与当前工具无关的完整表单。
4. 多步流程始终沿用前一步工具返回的真实业务 ID、状态和下一步参数，不猜测 ID，不重新创建同一业务对象。
5. 创建、修改、删除、提交或实际处置等有副作用的操作，遵守工具返回的确认门；查询类操作不额外制造确认步骤。

### 完整行程快速路径

用户要求新建、修改或取消包含去程、返程、会议、住宿或接驳组合的完整行程时，目标工具已经唯一确定为 `fbt_trip_planner`：

1. 工具已加载时直接调用，不先调用 `fbt_account`，不搜索或加载酒店、机票、火车票等其他差旅工具。
2. 工具尚未加载或处于 deferred 状态时，只查找并加载 `fbt_trip_planner` 这一个工具，随后立即调用；不得为了确认能力而搜索其他工具。
3. 只补问 `fbt_trip_planner` 当前调用确实缺少的关键信息，已能组成完整请求时不再增加确认轮次。
4. `fbt_trip_planner` 返回后直接进入下文规定的行程预览流程，不再调用账号或单点查询工具复核结果。

## 路由规则

- 单独查询酒店使用 `fbt_hotel_search`；单独查询机票或火车票使用 `fbt_travel_search`；完整行程的新建、修改或取消使用 `fbt_trip_planner`。
- `fbt_trip_planner` 规划成功后，最终回复必须逐项保留每个机票、火车票和酒店后的 `预订链接: <booking_url>`，不得省略、改写或把多个链接合并。展示 HTML 页面按下文“行程规划预览”流程执行；正文不输出 HTML Markdown 链接，只通过产物和 `present_files` 展示页面。同一行程的多轮修改必须沿用工具返回的同一 `conversation_id`，产物覆盖同一文件。
- 查询当前员工适用的差旅标准和消费政策使用 `fbt_consumption_rules`；查询本人商旅订单使用 `fbt_order_search`。
- 查询消费金额、订单量、趋势、排行、结构、报告或数据驱动建议使用 `fbt_consumption_insight`。它不回答消费规则，不筛查合规风险，也不测算降本空间。
- 查询违规、超标、异常、套现、重复等订单风险使用 `fbt_compliance_analysis`。它不回答一般消费情况，也不把降本机会当作违规问题。
- 查询可节省订单、金额、降本点、规则命中或优化空间使用 `fbt_cost_reduction_analysis`。它不回答一般消费情况，也不把合规风险解释成降本机会。
- 三个管控分析 Tool 的 `query` 必须传用户当轮完整原话，不提前拆解或改写分析条件；为兼容豆包，合规和降本不暴露额外可选参数，跨 Tool 背景直接并入本轮原话。
- 发票归集或票夹查询使用 `fbt_invoice_management`；把发票生成费用草稿使用 `fbt_expense_management`；创建或查询报销单使用 `fbt_reimb_management`。
- 产品规则和操作方法等知识问题使用 `fbt_service_ask`；需要重新推送、修正、诊断、建单或跟进等实际动作时使用 `fbt_self_solve`。
- `fbt_apply_order` 创建、修改或预览待提交草稿时，按下文“申请单草稿预览”流程呈现草稿编辑页；查询列表和正式提交成功时不呈现。

### 行程最终回复格式

`fbt_trip_planner` 规划成功并完成预览呈现后，最终回复使用紧凑格式。目标是在不丢失真实行程段和预订链接的前提下减少模型生成时间：

1. 开头只用一句话说明行程已规划、预览已打开，不重复复述用户需求或输出行程总览。
2. 工具返回的每个行程段只出现一次，每段一行，字段用 `｜` 分隔；只保留日期、类型或名称、起终点、起止时间、价格和必要状态。接驳、会议等没有预订链接的节点不得展开背景说明。
3. 每个 flight、train、hotel 节点的下一行必须原样输出 `预订链接: <booking_url>`；链接本身不计入精简范围，仍不得省略、缩略、合并或改写。
4. 除工具明确返回的超标、无票、缺失行程段等重要提示外，不输出“温馨提示”“两点提醒”、备选方案、通用预订指导或重复总结。
5. 不使用表格，不堆叠多级标题；非链接正文控制在 1800 个中文字符以内。短链接正常时，总回复目标不超过 3000 个字符；降级成长链接时允许超出总长度目标。

推荐形态：

```text
行程已规划，预览页已打开。

- 9/7 去程高铁｜G3 北京南 06:52 → 上海 11:33｜二等座 ¥667
  预订链接: <booking_url>
- 接驳｜上海站 12:03 → 上海中心大厦 12:25｜约22分钟 ¥27
- 会议｜上海中心大厦 14:00–16:00
- 酒店｜<酒店名>｜9/7入住、9/8离店｜¥<价格>
  预订链接: <booking_url>
- 9/8 返程高铁｜G4 上海 07:00 → 北京南 11:37｜二等座 ¥667
  预订链接: <booking_url>
```

## 本地脚本

普通工具调用不得搜索、创建或执行替代脚本。只在下列明确流程中使用随 Skill 提供的脚本；脚本只做本地数据加工和文件交付，不访问分贝通业务接口。

**脚本位于当前工作区之外**，各流程给出的命令已自带定位逻辑，整段原样复制执行即可，无需事先确认脚本是否存在。命令的动作清单是封闭的：清单内按序执行，清单外一律不做。脚本确实不存在时命令会报错，此时如实说明不可用并按该流程的降级方式处理，不要自行编写替代脚本或手工拼装 HTML。

### 申请单草稿预览

`fbt_apply_order` 需要呈现草稿时，其模型可见 `content` 末尾会给出一行「草稿编辑页（需要呈现给用户查看…）：<链接>」。**在 WorkBuddy 渠道，「呈现」一律指调用 `present_files` 在侧边栏打开，不是把链接贴在正文里让用户自己点。**

**本流程的完整动作清单（共 1 步）：**

1. `present_files` 打开该链接

链接由工具侧经短链服务处理后下发，直接原样传给 `present_files` 即可（该工具支持 URL，会走 `previewed` 通道打开）。**同时要在最终回复正文中原样给出这个链接**，方便用户自行点击；不得改写、缩略或替换成 Markdown 描述文字之外的形式。

只把链接写进正文、不调用 `present_files`，属于流程未完成。链接为空或 `present_files` 失败时，如实说明草稿预览打不开，并用 `content` 里的草稿摘要向用户转述明细。

> 中转渲染方案（`scripts/render_apply_draft.py` 把草稿渲染成本地 HTML 预览页）**已暂停使用**，脚本与工具侧代码均保留以便回退。停用原因：长 Base64 载荷由模型逐字转录频繁损坏，且模型常绕过脚本自行解码取链接，反而更慢。

### 行程规划预览

**标准成功路径共 2 步，不得插入任何其他工具调用：**

1. `Bash` 执行下方渲染命令
2. `present_files` 打开产物 —— 参数只能是上一步 stdout 返回的**本地文件路径**，禁止传入任何 URL

`present_files` 返回后立即组织最终回复。此流程禁止检查、创建或更新工作日志，禁止为日志调用 `execute_command`、`write_to_file` 或其他文件工具；除非用户在当前请求中明确要求记录工作日志。

下列动作在本流程中一律禁止，出现即属流程执行错误：

- 另行用 Glob / Read / Grep 查找脚本、阅读源码或确认参数（命令已含定位，参数以命令为准）；
- 用 `--help` 试探命令行接口；
- 用 echo / ls 检查 `CODEBUDDY_SESSION_ID`、会话记录目录等运行环境；
- 用 Grep / Read 检查生成出来的 HTML 内容。

脚本能否取到载荷由脚本自己判断，取不到会明确报错——**不需要你预先验证任何机制**。报错时直接按降级步骤处理，不要排查原因。

`fbt_trip_planner` 规划成功时，其模型可见 `content` 会要求「生成并呈现行程预览页面」。**在 WorkBuddy 渠道，「呈现」一律指按下面两步跑出本地 HTML 再用 `present_files` 在侧边栏打开，只在正文转述行程、不生成预览页属于流程未完成。** 其 `content` 末尾包含一组完整标记：

```text
[TRIP_PLAN_PAYLOAD_V1]
<URL-safe Base64>
[/TRIP_PLAN_PAYLOAD_V1]
```

1. **直接执行下面这条命令**，把 `<conversation_id>` 换成工具返回结果中的该字段值，其余原样：

   ```bash
   SCRIPT_PATH="$HOME/.workbuddy/connectors-marketplace/connectors/fenbeitong/skills/scripts/render_trip_plan.py"
   [ -f "$SCRIPT_PATH" ] || SCRIPT_PATH=$(find "$HOME/.workbuddy" -type f -name render_trip_plan.py 2>/dev/null | head -1)
   [ -f "$SCRIPT_PATH" ] || { echo "未找到 render_trip_plan.py，无法生成行程预览" >&2; exit 1; }
   python3 "$SCRIPT_PATH" --conversation-id "<conversation_id>" --output-dir outputs
   ```

   脚本会自行从当前 WorkBuddy 会话记录中取回完整载荷，因此**无需提取、也不要复制 Base64 载荷**——长 Base64 逐字转录极易损坏。排查时可加 `--diagnose`，会把查找过程打到 stderr。
   **仅当**上一步报「未能从会话记录中找到」时才降级为传载荷：提取两个标记之间的 Base64 字符串原样传入，不改写、不向用户展示该载荷，也不将其拼接成未转义的 shell 命令：

   ```bash
   python3 "$SCRIPT_PATH" --payload-base64 "<Base64>" --output-dir outputs   # 同一次 shell 会话中 SCRIPT_PATH 已设好
   ```

   读取成功脚本 stdout 中的 JSON，取 `trip_html_path`，立即调用 `present_files([trip_html_path])` 在侧边栏打开。

   同一行程修改后重复执行；脚本按 `conversation_id` 覆盖 `outputs/trip-plan-<conversation_id>.html`，不堆积历史文件。

   脚本失败时不重试规划或修改行程，也不影响已成功的业务结果；降级为用 `content` 中的行程参考信息逐项转述，并保留每个预订链接。

未列出的工具需要本地加工时，由该工具开发者把脚本随 Skill 一起提交，并写明唯一脚本路径、输入输出、失败处理和展示步骤。

## 结果与错误处理

- 优先使用工具返回的模型可见文本回答，不从不可见字段猜测结果。
- 工具要求补充信息时，只追问当前步骤缺失的信息，并在下一次调用中保留已经确认的参数。
- 登录态失效或鉴权失败时，提示用户在 WorkBuddy 中重新连接分贝通 Connector；不要要求用户在对话中发送 Token。
- 权限不足时说明当前账号或企业没有对应权限，不改用其他工具绕过。
- 超时或临时服务异常最多按工具提示重试；没有明确重试建议时，如实说明失败，不重复创建有副作用的业务对象。
- 若后续工具专属流程生成了完成文件，按 WorkBuddy 的结果展示规则将文件放入当前工作区 `outputs/`，再调用 `present_files`。没有生成文件时只返回文本结果。

## 安全边界

- 不单独展示 access token、user token、临时凭证、签名或会话标识。申请单草稿编辑链接由工具侧转为短链后下发，可以在正文中原样展示；若工具下发的是带 `token=` 参数的长链（短链服务不可用时的降级形态），则只调用 `present_files` 打开，不要在正文中展示该链接。
- 不把健康检查、工具列表或探针结果当成真实业务已经完成的证据。
- 不根据工具名称猜测未公开能力，不把查询成功描述成创建、提交或审批成功。
