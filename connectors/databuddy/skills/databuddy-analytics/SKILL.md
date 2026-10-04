---
name: databuddy-analytics
description: |
  DataBuddy连接器调用后，都一定要首先调用一次本技能，来完善相关数据分析的背景信息，才能去调用其他数据分析相关Skill（data-task-planner、intelligent-kanban、intelligent-query、report-composer）。
version: 0.2.0
author: WeData Team
tags: [workbuddy-connector, data-analysis]
---

# 简要自我介绍
DataBuddy 数据分析Skill，智能问数、指标统计、趋势对比、归因分析、预测、相关性、异动检测、智能看板或分析报告诉求时，由本 skill 承接。

# 相关环境信息

- **CLI 执行入口**：WorkBuddy 使用本机 PATH 中的真实 `wedatacli`。
- **工作空间 ID**：通过 `wedatacli GetEnv workspaceId` 获取当前会话默认的 `workspaceId`（单行文本输出，未配置时为空串）。
- **工作空间名称**：`GetEnv` 只返回 `workspaceId`，不返回名称；面向用户展示时需要通过 `wedatacli workspace list` 的 `items[].{id,name}` 按 `workspaceId` 反查对应 `name`。同一轮会话内可复用上一次 `workspace list` 的结果，不必每轮重复调用。
- **数据知识库 Key**：通过 `wedatacli GetEnv analysisSpaceKey` 获取当前会话默认的 `analysisSpaceKey`（单行文本输出，未配置时为空串；为空只表示当前未配置或未获取到数据知识库 Key）。
- **数据知识库名称**：`GetEnv` 只返回 `analysisSpaceKey`，不返回名称；面向用户展示时需要通过 `wedatacli workspace list_analysis_spaces` 的 `items[].{key,name}` 按 `analysisSpaceKey` 反查对应 `name`。同一轮会话内可复用上一次 `list_analysis_spaces` 的结果，不必每轮重复调用。
- **工作空间 文件夹**（workspace_folder）：可以在整个上下文中最近一次的user对话中找到，<user_info>标签内有定义“Workspace Folder”的值， 如果找不到就取默认值`~/.wedata`

> `GetEnv` 还支持另外 3 个 key，本 skill **不直接读取**，仅在下列场景由下游 skill 使用：
> - `region`：当前工作空间的地域字符串（如 `ap-chongqing`）。**⚠️ `workspace config_set` 已不再接受 `--region` 入参**（工具内部通过账户级 `ListWorkspaces` 反查 workspace_id 自动填入），本 skill 无需再手动传 region；下游 skill 需要"当前地域字面值"时才用 `GetEnv region` 反查。
> - `regionId`：地域的数字 ID（如 `19`），由 `region` 通过 CLI 内置映射表推导。仅 `intelligent-kanban` / `report-composer` 等拼老 CAPI 风格 URL 的 `r=<数字>` 参数时使用。
> - `consoleDomain`：DataBuddy 控制台域名（默认 `databuddy.cloud.tencent.com`，私有化 / 国际站会不同）。仅下游 skill 拼产物 https 跳转链接（file.json 打开链接、看板分享链接、代码文件详情页链接等）时使用。

# 任务执行原则

## 理解、澄清与写操作

- **先理解再行动**：当用户意图不明确时，先澄清，不要急于调用工具或猜测执行路径。
- **只问会改变问题语义的信息**：尤其在指标、对比目标、未来预测范围缺失，且不同补齐方式会改变问题含义时才向用户提问。历史点数量、默认基期、时间格式等可行性问题优先交给工具自身检查。
- **写操作需要明确正向信号**：涉及创建、修改、删除、覆盖、发布、提交等写操作时，需要用户给出明确同意，例如“确认执行”或“继续”。没有明确正向信号时，不执行写操作。
- **解释性问题不查真实数据**：当用户只是询问概念、方法、能力范围，或明确表示“不查数据 / 不调用真实数据”时，直接解释，不调用真实数据工具。只有用户要求分析真实数据时，才调用相应工具。
- **非分析类 Databuddy 诉求引导到界面**：当用户明确指定“Databuddy / DataBuddy”，但诉求不是智能问数、指标统计、趋势对比、归因、预测、相关性、异动检测、智能看板或分析报告等数据分析任务，而是配置、管理、开通、权限、页面操作等非分析类事项时，推荐用户前往 Databuddy 界面进行配置，并给出可点击的动态链接。链接按下述模板拼接：
  - **模板**：`https://{consoleDomain}/buddy?o={workspaceId}&r={regionId}#/databuddy/new-task?mode=engineering`。
  - **参数取值**：`consoleDomain` 通过 `wedatacli GetEnv consoleDomain` 获取（读取不到时回退默认 `databuddy.cloud.tencent.com`）；`workspaceId` 通过 `wedatacli GetEnv workspaceId` 获取，作为 `o` 参数；`regionId` 通过 `wedatacli GetEnv regionId` 获取，作为 `r` 参数。
  - **禁止编造**：`workspaceId` 或 `regionId` 任一读取不到时，不要输出占位或臆造值的链接，直接如实说明“未获取到当前 Workspace / Region，无法生成 Databuddy 引导链接”。

## 复杂分析任务先规划

- **复杂分析任务需要先 Plan**：当用户请求属于以下任一类型时，先调用 `data-task-planner` 生成 Plan 文档，再按 Plan 逐步执行。
  - **深度研究型**：用户需要围绕一个主题形成系统性分析结论或研究报告，需要多角度、多层次调查，单一视角回答无法覆盖。
  - **宽泛 / 模糊型**：用户问题范围大、表述笼统，隐含多个子问题，需要先拆解为多个相对独立的子任务再推进。
- **Plan 拆的是任务级事项**：一个任务内部可能调用多个原子能力，但“需要多个原子能力”本身不等于必须进入 Plan 模式。只有任务本身确实复杂或宽泛，才先规划。

## 异动 / 归因 / 预测 / 相关性分析优先使用专用工具

- **四类问题优先使用标准分析工具**：
  - 异动检测优先使用 `detect-anomaly`。
  - 归因分析优先使用 `attribute-data`。
  - 趋势预测优先使用 `predict-data`。
  - 相关性分析优先使用 `correlate-data`。
- **不要用 SQL / Python 绕过专用工具**：如果问题属于上述四类，且专用工具的入参能表达用户问题，就必须先使用专用工具产出结构化分析结果。
- **专用工具不能表达或失败后才降级**：只有当专用工具明确不支持该场景，或已经失败且不能重试时，才可以使用 `query-data`、SQL 或 Python 等其他方式。最终回答必须说明为什么没有使用标准工具、工具失败原因、实际使用的数据或 SQL、计算依据、结论和局限性。
- **没有专用工具覆盖的分析可以灵活处理**：对于不属于异动、归因、预测、相关性四类的问题，可以灵活使用 `query-data`、SQL 或 Python。
- **报告型能力不能替代标准分析工具**：只有当用户明确要求报告、复盘、汇报，或要求把标准工具输出整理成完整分析报告时，才调用已打包的报告型 Skill。报告型能力不能替代 `detect-anomaly`、`attribute-data`、`predict-data`、`correlate-data` 的结构化分析职责。

## 分析任务执行规则

以下规则适用于 `detect-anomaly`、`attribute-data`、`predict-data` 与 `correlate-data`。

- **完成用户显式提出的每一个目标**：如果一个问题同时要求历史趋势、根因分析和异动检查，每一项都必须有结果，或明确说明“因为某原因所以跳过”。历史趋势使用数据查询能力，未来预测使用 `predict-data`，根因分析使用 `attribute-data`，异动检查使用 `detect-anomaly`，相关性分析使用 `correlate-data`。不要因为上下文里出现某个相关词，就反复调用同一个工具。
- **先处理依赖关系**：对于“只有存在异动时才解释原因”这类请求，先执行异动检测。只有发现有效异动时，才把异动窗口、指标、粒度、过滤条件传给归因分析；如果没有发现异动，需要说明为什么不执行归因。若工具、指标、时间范围、粒度、过滤条件和维度集完全相同，复用上一次成功结果，不重复运行。
- **重试意图锁**：除 `predict-data` 有单独规则外，同一分析的重试只能补充取数形态、切换到明确可用的数据源，或修正已确认的字段错误。重试不得静默改变目标指标、时间范围、基期、当期、观测粒度、输出粒度、过滤条件，也不得删除用户点名的维度。任何分析意图必须变更时，先解释原因并取得用户确认。
- **预测重试意图锁优先于通用重试规则**：第一次调用 `predict-data` 必须原样传入用户原始问题，不要在 CLI 调用前改写。目标指标、物理数据源、过滤条件、显式历史范围、预测范围、预测起点、期数和输出粒度都属于不可变意图；重试时不得切换物理数据源，不得把预测范围当作历史取数范围，也不得删除、替换或平移这些信息。失败后先读取 CLI 转发的原始 `code` / `message` 和 recovery envelope。只有失败信息明确声明 `retryable=true` 时，才可以根据 `recovery_mode`、`retry_query_hint` 和 `agent_next_actions` 补充缺失信息并重试一次；当 `retryable=false` 时，只能按建议拆分编排、切换其他方法或明确宣告失败。CLI 只负责转发 recovery envelope，不会自动重新提交任务；“重试一次”是当前上下文内的编排策略，不表示 CLI 维护跨调用的尝试状态。
- **预测中的国家节假日日历**：调用 `predict-data` 时，保留用户关于国家 / 地区以及是否考虑节假日的原始表述。用户明确说“不加 / 不用 / 不考虑节假日”时，工具会禁用国家日历；用户明确国家时，工具可以传给算法选择对应国家日历。黑五、促销等词是国家日历的业务上下文，不要声称已经创建自定义事件回归器。没有可靠国家信号时，不要猜测国家，也不要默认开启节假日。
- **预测历史点规划**：用户显式给出的历史窗口、取数粒度、输出粒度和预测范围都是不可变意图。即使得到的历史点少于 20 个，也不要为了凑够 20 个点而扩展、缩短或改变粒度。只有历史窗口或粒度未指定时，才可以补齐未指定部分，并优先保证至少 20 个有效连续历史点。20 个点只是稳定性规划目标，不能替代工具内置的数据不足检查。
- **多次调用必须完整汇总**：当一个问题被拆成多次标准工具调用时，最终回答和任何报告都必须读取每次成功调用及其 artifacts，并保留每次调用的 `task_id`。不要只读最后一次调用，也不要让最后一次结果覆盖前面已经覆盖过的维度或指标。
- **复合请求按原子能力拆分**：当复合或批量分析超过单个工具的一次性能力时，按指标、实体或序列拆成多个标准工具调用，并遵守“重试意图锁”和“多次调用必须完整汇总”。无法安全拆分时，需要明确说明该场景不支持；不要通过聚合掉实体维度、删除条件、替换指标或改变粒度来声称任务已完成。
- **根据工具描述判断范围**：不要在系统提示中重复阈值、时间格式或默认参数，也不要只根据 `rate`、`ratio` 等指标名判断归因类型。按离散字段拆分是维度归因；只有拆分公式组件（如销量、价格等）或用户明确要求 Shapley 时，才是因子归因。不要仅因为 SQL 更快就跳过专用工具。
- **业务语义交给模型理解，不做关键词式拒绝**：黑五、促销、回归器、control、多序列等文本必须原样转发给对应工具，由模型结合原始问题、冻结的地域 / 语言、取数结果和算法能力进行解释。框架规则最多提示风险、能力边界和输入要求，不能因为匹配到某个关键词就拦截、删除或改写业务请求。
- **下降排名不是异动检测**：例如“下降最大的月份”“环比下降最大的月份”“增速最慢”等，属于变化计算或排名，不是统计异常。只有当用户明确询问某个值是否偏离正常范围、是否异常、是否有尖峰 / 突刺时，才调用 `detect-anomaly`。
- **必须说明异动算法的分组边界**：当前 `detect-anomaly` 算法不支持在一次调用中扫描大量实体，即不能对大量商品、商家、地区分别建模后再聚合异常实体。遇到这类请求时，不要聚合掉实体维度后声称完成任务；需要说明能力边界，并让用户在“全局单序列”“少量实体分别调用”或“替代方法”之间选择。
- **重试必须改变执行条件**：同样输入不能反复调用。最多重试一次，且只有工具明确表示可重试、给出处理建议，并且下一次调用会实际修正数据形态、字段映射或数据源时才允许重试。`predict-data` 不得切换物理数据源，只能在预测专用意图锁下修正取数形态或字段映射。时间范围、粒度等分析意图受“重试意图锁”约束，不能为了让调用成功而改变。否则应宣告失败或切换方法。

# CLI工具信息

`wedatacli` 是与 DataBuddy 平台交互的唯一 CLI 通道。调用时使用 `wedatacli` 加具体子命令的形式，最后需要带上参数`--workspace_folder`，其值从相关环境信息中可以查到，例如 `wedatacli <sub-command> ... --workspace_folder <workspace_folder>`。

## wedatacli 工作方式

- **stdout 自动落盘**：当 stdout 超过 `WEDATA_MAX_STDOUT_BYTES`（默认 `16384B`）时，CLI wrapper 会把完整结果写入 `<workspace_folder>/tmp/wedatacli-<action>-<ts>.json`，stdout 只返回 `{truncated, file, size, preview_head_1k}`。需要查看完整内容时，按需使用 `jq` / `head` 读取片段。
- **大文件读取约束**：读取文件且不指定 offset 前，先运行 `wc -l` 确认文件行数不超过 200 行；否则使用 `grep` / `head` / `tail` 定位目标区域。不要重复读取同一个文件片段超过 3 次。
- **禁止盲目重试**：当子命令失败、返回空结果或超时时，先读取错误信息。只有失败满足“重试必须改变执行条件”的规则时，才允许重试一次；否则切换到其他命令，或向用户如实说明失败。

## 可用 wedatacli 命令

每个工具按**定义 / 参数 / 使用场景限制 / 返回**四要素描述。调用前先检查“使用场景限制”，不满足限制的问题不要硬调。

### 归因调用前置澄清

`attribute-data` 当前只负责**两期对照的维度归因**，不负责把指标公式项本身做归因分解。调用前必须先把用户问题澄清为一个合格的维度归因问题：

1. **先洞察清楚，再调用归因**：针对模糊的问题，如不清楚按什么维度下拆分析、不确定使用什么指标时，优先通过 `ll` / `cat table://...` 召回指标、表、字段、时间列、可选维度等知识；必要时在归因 / 预测 / 相关性 / 异动等分析链路内部用 `query-data` 先取必要的同口径预检 / 汇总数据，确认目标指标、过滤条件、基期、当期、时间粒度和候选离散维度。
2. **调用归因时必须写清四类信息**：目标指标、当期、对照基期、离散归因维度。问题中已有的信息必须原样保留；缺失但可由知识召回或取数确认的信息再补齐；仍无法确认时先向用户澄清，不要硬调用归因。澄清完成后，若用户诉求仍是两期对照的离散维度归因，必须调用 `attribute-data` 产出标准归因结果，不得仅用 `query-data`、本地 Python、`data-analyzer` 或报告类 skill 替代。
3. **区分维度归因与指标 / 公式项分解**：品类、地区、渠道、商家、用户分群、时间桶、是否类 flag 等枚举字段是归因维度；销量、单价、订单量、客单价、分子、分母、均值、比例构成项等是指标公式组件或数值驱动项，不要写成“归因维度”。例如“GMV 下降，是卖得少了还是单价低了”应先取 GMV、销量、单价做两期公式分解；若要继续定位“销量下降主要发生在哪类对象”，再把目标指标改为销量，并选择可解释的离散维度调用 `attribute-data`。
4. **守住 cohort / 窗口指标口径**：遇到复购率、留存率、转化率、首单后 N 天内行为等问题，先明确分母实体、cohort 所属期、窗口定义、目标指标计算方式；不要把率改成事件数，也不要用窗口内后续事件时间替代 cohort 时间。
5. **禁止模糊直传**：不要把“为什么下降 / 哪里异常 / 卖得少还是单价低”这类未澄清的问题直接丢给 `attribute-data`。应先形成明确的归因执行问题，例如“2026 年 3 月相比 2026 年 2 月，drinks 类目销量下降，按 product_id、seller_state、customer_state 等离散维度做维度归因”。

### 异动检测调用前置澄清

`detect-anomaly` 只负责对**单一指标的一段连续历史时序**做 sigma 异常扫描，找出偏离正常区间的时间点，不做两期对照归因，也不做未来预测。调用前必须先把用户问题澄清为一个合格的时序异动检测问题：

1. **先判断是不是异动问题**：只有“哪里异常 / 有没有突刺 / 这段波动是否正常 / 某指标走势是否有偏离”这类**单指标历史序列异常定位**才调 `detect-anomaly`；“为什么变化 / 比某期多多少 / 哪个维度贡献的”属于归因（`attribute-data`），“未来会怎样 / 预测下阶段走势”属于预测（`predict-data`），不要把归因或预测问题塞给异动。
2. **必须写清目标指标、检测时间范围、时间粒度**：异动检测的是整段连续历史，缺粒度或范围时先通过 `ll` / `cat table://...` 召回或用 `query-data` 预检确认；若按目标粒度算下来时间点偏少（如范围太短），先扩大范围或改用更细粒度，不要硬调导致 `INSUFFICIENT_DATA`（有效数据不足）。
3. **取数须逐期连续、不得聚合成单行**：取数应按时间粒度**连续**返回该范围内的所有时间点，同一时间粒度点只保留一行（多实体先按目标指标聚合）；不要只返回“看起来异常”的点，也不要按时间排序后做 LIMIT / TOP-N 截断，序列残缺会漏检早期异动或让有效点不足，破坏检测对象。
4. **禁止模糊直传**：不要把“最近数据是不是有问题 / 看下有没有异常”这类未澄清问题直接丢给 `detect-anomaly`。应先形成明确的异动执行问题，例如“检测 GMV 从 2026-01 至 2026-06 按天的异常波动”。
5. **对比型 / 去周期型异动要先把对比口径算进取数**：`detect-anomaly` 只对**一条序列**做整体波动扫描，不会自己做“相对某基线”对比或“按周期去季节”。遇到“相对全国 / 大盘基线”“同比 / 环比基线”“hour-of-day、按周、按月循环”这类问题，不要直接把原始指标丢给异动，而要在取数（`query-data` / 生成 SQL）阶段就把对比结果算成**一列可直接检测的指标**，再对这一列跑异动：
   - “SP 相对全国基线” → 取数时算出每月“SP 占全国的比例”或“SP 减全国均值”的差值列，对差值序列检测；
   - “hour-of-day 是否异常” → 取数时算出每小时“相对该小时历史均值的残差”，对残差序列检测；
   - 若一次取数拿不全对比所需数据，先用 `query-data` 把基线序列和目标序列都取回来，在中间步骤算好差值 / 比值列，再调 `detect-anomaly`。

   题目里的对比对象（“相对全国”“相比大盘”“同小时”）属于**必须保留的语义**，澄清和取数时不得把它简化成裸指标序列。

### 相关性调用前置澄清

`correlate-data` 只负责对**目标指标 + 一批候选因子**做相关性分析，调用前必须先把用户问题澄清为一个合格的相关性问题：

1. 问题类似为**[分析目标]** 与 **[候选因子A] / [候选因子B] / ...** 的相关性，控制 **[混淆变量（如有）]**。请直接调用对应分析工具，无需搜索元信息。
2. 只有问题中要分析的相关性候选因子信息缺失时，才允许通过 `ll` / `cat` / `query-data` 预检**补齐**到问题里，不覆盖用户原话；查证到的实际列名或口径写法以附注形式追加在问题末尾，用户点名的指标名保持原样。
3. **禁止模糊直传**：不要把“看看这几个指标有没有关系”这类未澄清问题直接丢给 `correlate-data`。应先澄清出明确的执行问题，例如“2025-01 至 2026-06 按月，分析 GMV 与 UV、客单价、活动投放金额、天气温度的相关性，控制季节因素”，且澄清后**必须保留**用户列出的全部候选因子。

### 数据分析工具

#### `query-data` —— 自然语言取数

- **定义**：自然语言取数统一入口，内部自动完成语义层 / text2sql 双路路由与降级。
- **参数**：
  - `"<问题>"`（必填）：自然语言问题原文，不改写、不拆分、不加条件（相对时间由服务端解析）。
  - `--no-progress`（必填）：禁用 stderr 进度条。
  - `--draw`（可选，默认关闭）：开启服务端画图，返回 `draw_spec`（DSL）+ 长时效签名 COS 链接；**仅** `intelligent-query` skill 内部按契约组装时使用；draw 失败 / 超时不影响任务终态，仅 `draw_spec` 为空。
- **超时时间**：`300000ms`。
- **使用场景限制**：
  - 所有“查数据 / 取数 / 统计 / 排行 / 趋势 / 对比 / 看数据”类简单问数请求必须先加载 `intelligent-query` skill，由其内部按契约组装 `--draw`；直接裸调会导致前端图表锚点丢失、无法渲染。
  - 仅供报告分析过程中相关数据获取，且这些场景**禁止**传 `--draw`。
  - 走 `--draw` 路径且 `draw_spec` 非空时，返回不再展示 `Data` 表格预览（图形已承载数据表达），仅保留 `csv_path` / `row_count` / `columns` 等元信息以节省 token；需要明细数据时按 `csv_path` 本地读取。
- **返回**：`text` 模式为 Markdown（`Source` / `Metric` / `Stmt(SQL)` / `Fallback History` / `Data` 表格 / `csv_path` / `Draw Spec` 等分节）。

#### `predict-data` —— 时序趋势预测

- **定义**：自然语言驱动的端到端时序预测（Prophet，支持年 / 周季节性、节假日效应、置信区间），主要用于对业务时序指标做未来走势预测。
- **参数**：
  - `"<问题>"`（必填）：应写清**目标指标、时间粒度（按天 / 周 / 月等）、预测未来多久**，例如“预测某指标未来 30 天的走势”“按月预测下个季度 GMV”；不写未来期数与粒度时工具会自动推断，但写清可避免时间列被聚合成无法识别的格式。
  - `--no-progress`（可选）：禁用 stderr 进度条。
- **超时时间**：`300000ms`。
- **使用场景限制**：
  - 时序预测**硬性要求至少 10 个历史时间点**，低于该阈值服务端直接判定为数据不足；`<问题>` 要保证历史数据按时间粒度逐期返回（每个时间点一行，如每月一行），且历史窗口足够长（点数不足时扩大时间范围或改用更细粒度）。
  - 避免写成“基于某几个月预测下月”这类会被聚合成单值的问法。
- **返回**：`Status`（`success` / `failed`）/ `Code` / `Message` / `Result`（预测 findings JSON：`conclusion` + `quant` 未来时序点 + `suggestions` 等）/ `Artifacts`（服务端产出的数据已下载到本地 `csv_path`）。

#### `correlate-data` —— 相关性分析

- **定义**：自然语言驱动的端到端相关性分析（Spearman 秩相关，对异常值 / 非线性单调关系更稳健；对显著因子自动做残差法偏相关以控制混淆变量）。
- **参数**：
  - `"<问题>"`（必填）：应写清**目标指标、候选因子指标（可多个）、已知混淆变量（如有）、时间范围、时间粒度**。
  - `--no-progress`（可选）。
- **超时时间**：`300000ms`。
- **使用场景限制**：
  - 调用前必须完成“相关性调用前置澄清”，尤其是**原问题原样透传**红线：禁止删减候选因子、替换指标名、收窄时间范围、丢弃混淆变量、拆成多次单因子调用。
  - 结论附带 caveats “相关 ≠ 因果”，不要在回答中把相关性直接等同于因果关系。
- **返回**：`Status` / `Code` / `Message` / `Result`（相关性 findings JSON：`conclusion` + `quant`：相关系数 / 显著性 / 偏相关 / 分组分相 + `caveats`）/ `Artifacts`（本地 CSV，COS 签名链接已剔除）。

#### `attribute-data` —— 智能归因分析

- **定义**：基于已澄清的自然语言问题做端到端异动洞察、智能归因分析（两期对照的**维度归因** + 自动根因下钻）。归因回答的是“目标指标在当期相比对照基期的变化，主要由哪些**离散维度取值**贡献”，适合按品类、地区、渠道、商家、用户分群、时间桶、是否类 flag 等维度拆解。
- **参数**：
  - `"<问题>"`（必填）：**必须写清**目标指标、当期、对照基期、时间粒度、过滤条件，以及显式离散维度或“允许自动探索维度”。
  - `--no-progress`（可选）。
- **使用场景限制**：
  - 调用前必须完成“归因调用前置澄清”。
  - 归因**硬性要求至少 2 个对照周期**（当期 + 基期）；只给单个时间点时工具会自动推断基期，但该点恰为数据序列首期、无前序基期时会归因失败，建议显式给出基期。
  - **禁止**把销量 / 单价、订单量 / 客单价、分子 / 分母、数量 / 均值等指标公式组件写成“归因维度”；应先用知识召回和取数明确指标公式并做两期组件分解，必要时再对主驱动指标调用本工具下钻离散维度。
  - **超时机制**：服务端单任务预算默认 `300000ms`，CLI 侧总超时默认 `600000ms`。
- **返回**：`Status` / `Code` / `Message` / `Result`（归因 findings JSON：`conclusion` + `quant.contributions` 各维度贡献度 + `caveats`）/ `Artifacts`（本地 CSV，COS 签名链接已剔除）。

#### `detect-anomaly` —— 智能异动检测

- **定义**：基于用户自然语言问题做智能异动检测（对一段历史时序做 sigma 异常扫描，找出偏离正常区间的时间点）。分析的是**单一指标的一段历史走势是否存在异常**，不做归因那种两期对照。
- **参数**：
  - `"<问题>"`（必填）：应写清**目标指标、检测的时间范围、时间粒度**，例如“检测某指标近 90 天按天的异常波动”。
  - `--no-progress`（必填）。
- **超时时间**：`300000ms`。
- **使用场景限制**：只问“哪里异常”即可，无需给对照基期；需要两期对照时应改用 `attribute-data`。
- **返回**：Markdown 格式，含 `Status` / `Code` / `Result`，`Result` 为异动 findings JSON：`conclusion` / `quant.anomalies` 异常点 / `caveats`。

### 空间管理工具

空间管理工具的典型串联：`workspace list` 定位目标 workspace（`id`）→ `workspace list_analysis_spaces` 列出该 workspace 下可选数据知识库（`key`）→ `workspace config_set` 一次性写入默认配置（region 由 config_set 内部反查填入）。用户主动指出"切到某个 workspace / 数据知识库"时按此顺序推进；只是问"当前在哪个空间"时用 `wedatacli GetEnv workspaceId` / `wedatacli GetEnv analysisSpaceKey`（CLI 单值命令）即可，不必调 `list` / `list_analysis_spaces`。

#### `workspace list` —— 列举工作空间

- **定义**：返回当前账号可访问的**全部工作空间**（工具内部分页拉全量，Agent 无感知）。请求地域**恒定为 `ap-guangzhou`**（账户级跨地域接口的入口路由），与用户当前默认 workspace 的地域无关，也不受 `TENCENTCLOUD_REGION` 影响。
- **参数**（都可选，全部是过滤条件）：
  - `--name <kw>`：工作空间名称模糊过滤。
  - `--region <region>`：地域过滤，例如 `ap-guangzhou`。
- **使用场景限制**：
  - 用户明确要"列全部 workspace / 换个 workspace / 我有哪些空间"时使用；不要在每次问数前默认调用。
  - 输出只有 `id` / `name` / `region` 三字段（Agent 最小集合），`region` 用于展示 / 筛选场景；**下游 `workspace config_set` 不再消费该字段**——region/regionId 由 config_set 内部通过账户级 `ListWorkspaces` 反查 workspace_id 自动填入。
- **返回**：JSON，含 `items[].{id,name,region}` 与 `total_count`。

#### `workspace list_analysis_spaces` —— 列举数据知识库

- **定义**：返回**指定工作空间下的全部数据知识库**（工具内部游标分页拉全量）。
- **参数**：
  - `--workspace-id <id>`（可选）：未传时使用 CLI 默认工作空间；两者都没有 → `INVALID_ARGUMENT`。
- **使用场景限制**：
  - 只用于"当前 workspace 下能选的数据知识库有哪些 / 换一个数据知识库"；数据知识库的唯一标识是 `key`（不是 `id`）。
  - 想快速确认"当前默认数据知识库是什么"用 `wedatacli GetEnv analysisSpaceKey` 即可，不必调本命令。
- **返回**：JSON，含 `items[].{key,name}`。

#### `workspace config_set` —— 设置默认工作空间与数据知识库 ⚠️ **写操作**

- **定义**：**原子**更新 CLI 会话的默认配置，一次性切换默认工作空间及其地域与数据知识库。属于**写操作**，需遵守"写操作需要明确正向信号"红线。region/regionId 由工具内部通过账户级 `ListWorkspaces` 反查 workspace_id 的归属地域后自动填入，Agent **不再传** `--region`。
- **参数**（2 个字段，全部必填）：
  - `--workspace-id <id>`：设为默认工作空间；同时用于**反查该 workspace 归属的 region**。
  - `--analysis-space-key <key>`：设为默认数据知识库；传空串只表示清空数据知识库绑定。
- **⚠️ 断裂型变更**：老版本的 `--region <region>` 入参**已彻底移除**。传入会被 CLI flag 层直接拒绝（`unknown flag`）。这是有意为之——workspace 归属 region 是账户级服务端事实，让 Agent 手动传递只会引入配错风险（历史上出现过 workspace 在重庆但 Agent 传 `ap-guangzhou` 导致 CAPI 报 `ResourceNotFound` 的问题）。
- **使用场景限制**：
  - 用户**明确**要求切换 workspace 或数据知识库时才调用；仅仅确认当前空间不允许触发该命令。
  - `workspace-id` 不属于当前账号 / 已删除 → 工具会返回 `INVALID_ARGUMENT` 并给出"该 workspace 不在当前账号"的可辨识错误，Agent 应据此重新走 `workspace list` 让用户选择。
  - `region` 未在内置映射表中会**拒绝写入**并提示同步更新地域映射，不会静默回退到错误 regionId。
  - 变更**下次 wedatacli 调用时生效**，当前进程内已缓存的配置不刷新；写入成功后，如需在本轮继续验证，用 `wedatacli GetEnv workspaceId` / `wedatacli GetEnv analysisSpaceKey` 复核。
- **返回**：JSON，含默认工作空间、地域（由工具反查填入，Agent 可自证）、数据知识库及提示信息。

### 资产发现工具

#### `ll` —— session 资产清单

- **定义**：列出当前 workspace（+ 可选数据知识库）内的语义模型与表清单，带 `ai_context_description` 摘要。作用域来自 CLI 当前会话配置，无需手写 workspace id。
- **参数**：
  - `--page-token <N>`（可选）：仅 workspace 且资产超过 20 个时分页，默认每页 20；数据知识库通常一次拉全。
- **使用场景限制**：发现“当前空间有哪些表 / 语义模型”的**默认首选入口**；若 shell 设置了 `TENCENTCLOUD_ANALYSIS_SPACE_KEY`，会覆盖 config 中的数据知识库，清单范围随之变化。
- **返回**：文本模式为 `type + path + 描述`。

#### `cat` —— 读资产详情 / 文件内容

- **定义**：读取 session 资产详情（表结构、语义模型定义）或下载 `databuddy://` URI 指向的文件内容。
- **参数**：
  - `cat table://<catalog>.<schema>.<table>` 或 `cat semantic-model/<name>`：直接用 `ll` 输出的 path，无需拼 `databuddy://`。
  - `cat table/<a>,table/<b>`：批量查询，逗号分隔。
  - `--meta`（可选）：返回 download 信封（含 `local_path`、`uri`），仅需要落地文件路径时使用。
- **使用场景限制**：
  - `cat table` 只返回字段定义 / 注释等结构元数据，不返回行数据；要查行数据用 `query-data`。
  - 目录型 URI（catalog / schema / volume / studio）不能用 `cat`，需用 `ls`。
- **返回**：session 资产为精简 JSON（stdout 直出，已剔除 `RequestId`、空字段）；文档 / 文件为下载到本地。

### 简单问数 Skill 加载失败处理

所有“查数据 / 取数 / 统计 / 排行 / 趋势 / 对比 / 看数据”类简单问数请求，必须先 `Skill("intelligent-query")`，由 skill 内部按契约组装 `--draw` 与 `draw_spec`。

- **一次重试**：若 `Skill("intelligent-query")` 返回 `Can not find skill` / 加载失败等错误，允许且仅允许重试一次。
- **禁止静默降级**：重试仍失败时，严禁改为直接执行 `wedatacli query-data ...`（无论是否带 `--draw`）来“完成”用户问数请求。这会让用户看到无图数据、误以为系统正常，属于静默故障。
- **必须显式报错并停止**：向用户明确说明“智能问数能力当前不可用（skill 加载失败）”并停止本轮问数动作，等待用户后续指令；不要自行选择“退化为纯文本回答”。

# 可用的SKILL信息

当前数据分析路由中可直接触发以下 Skill。用户诉求命中某个 Skill 的职责时，直接调用对应 `Skill("...")`；单一明确任务不进入规划，复杂宽泛任务先规划再执行。

## `intelligent-query` —— 智能问数

把用户的一句自然语言转成可直接查看的数据结果，支持统计、环比、占比、排名、趋势、对比、数据变化等问数诉求，并可对结果做轻量二次处理，例如计算派生指标、过滤 / 排序、口径换算、生成结论表。

- **适用场景**：查数据、取数、统计、排行、趋势、对比、看数据、查看指标变化、计算简单派生指标。
- **调用方式**：命中简单问数诉求时，直接调用 `Skill("intelligent-query")`。
- **执行约束**：调用前不要先执行 `ll` / `cat` 等资产发现命令；表、字段、指标等相关信息检索由 `intelligent-query` 内部完成。
- **产出要求**：只负责取数、轻量二次加工和简洁输出；如果用户继续要求复杂研究、看板或报告交付，再按对应流程处理。

## `intelligent-kanban` —— 智能看板

基于 WeData 平台搭建交互式运营看板，采用 `htmlContent + sqlSlots` 模式组织页面与数据查询。

- **适用场景**：看板、创建看板、搭看板、大盘、驾驶舱、监控视图、KPI 看板、数据看板、业务看板、运营看板、管理看板、仪表盘看板。
- **调用方式**：消息中出现“看板”字样，或用户要求搭建大盘、驾驶舱、监控视图时，调用 `Skill("intelligent-kanban")`。
- **路由规则**：裸“仪表盘”默认按看板搭建处理，调用 `intelligent-kanban`。
- **反向区分**：如果用户只是查一下、看一下、取数、列出、统计行数、算一下，按单次问数处理，调用 `intelligent-query`。
- **返回契约**：看板产物是 DataBuddy 控制台的 AI 看板资源。runner 会自动写入 PREVIEW 并返回 `AccessKey` 与 `dashboard_url`；本 skill 面向用户的最终回复必须给出可点击的 DataBuddy 看板链接 `https://<consoleDomain>/dashboard/aiBoard/<AccessKey>?o=<workspaceId>&r=<regionId>`，用户点击后跳转 DataBuddy 查看。**唯一"产物"就是这条看板链接**；禁止在 WorkBuddy 对话中展示 `.kanban_output/` 目录路径、`kanban_spec.py` / `kanban_save_params.json` / `kanban_dsl.json` / 快照 CSV 等本地中间文件名，也不要输出"Spec 文件已创建"之类的提示（这些文件会被 WorkBuddy 误识别为产物卡片污染用户视图）。
- **缺参降级**：`workspaceId` / `regionId` / `consoleDomain` 任一读取失败导致 runner 未打印链接时，退化为在回复中给出 `AccessKey`，并如实说明"未获取到 Workspace/Region，无法生成完整看板链接，可在 DataBuddy 控制台 AI 看板列表按 AccessKey 定位"。
- **路径参数**：调用 `intelligent-kanban` 内 Step B / Step D 命令时，`<reference_dir>` = 当前 Skill 安装目录下的 `intelligent-kanban/reference/` 绝对路径（由 Skill 加载器已知），`<workspace_folder>` 取自当前 WorkBuddy session 目录；两个都通过 `export` 前置注入，不要探查 env 或改写 skill 内命令模板。

## `data-task-planner` —— 数据分析任务规划

将复杂数据分析类问题先规划后执行，接收用户问题与对话上下文，输出结构化执行 Plan。

- **适用场景**：深度分析、研究报告、多维分析、全面分析、综合分析、深入研究、系统分析。
- **深度研究型**：用户需要围绕一个主题形成体系化分析结论，需要多角度、多层次深入挖掘。
- **宽泛模糊型**：用户表述笼统、范围大，问题隐含多个子问题，需要先拆解成若干子任务逐个推进。
- **调用方式**：命中复杂分析场景时，调用 `Skill("data-task-planner")` 获取 Plan，再按 Plan 调用 `intelligent-query`、`intelligent-kanban`、`report-composer` 或 `wedatacli` 标准分析命令执行。
- **路由边界**：单一明确的数据诉求直接交给对应 Skill 或 CLI，不进入 `data-task-planner`。

## `report-composer` —— 报告交付物生成

数据分析报告、轻报告、单图网页、综合报告和看板式交付物的统一生成 Skill。它自行读取当前对话上下文，识别取数结果、SQL、结论并提炼报告骨架，再根据调用参数自动规划产物形态，生成 Markdown、HTML 或可选 `.docx` 文件。

- **适用场景**：用户明确要求报告、分析报告、周报、月报、复盘、汇报、专题、经营分析、管理层汇报，或需要把问数、归因、预测、相关性、异动检测等结果整理成可落盘交付物。
- **调用方式**：命中报告交付诉求时，调用 `Skill("report-composer", args={...})`；从当前对话已有信号里明确 `title` / `shape` / `output` / `export_docx` 等意图，用户显式提到才覆盖默认值，否则走 `auto`。
- **落盘约束**：产物写入 `<workspace_folder>/artifacts/analysis/`，文件名前缀统一为 `report_<ts>`。
- **返回契约**：返回 path-mode JSON，只包含本地路径和摘要信息，例如 `md_path`、`html_path`、`docx_path`、`shape`、`formats`、`summary`、`size_bytes`；不要在对话正文中粘贴完整报告或 HTML 源码。
- **使用边界**：`report-composer` 只负责生成交付物，不能替代 `query-data`、`attribute-data`、`predict-data`、`correlate-data`、`detect-anomaly` 等数据查询和标准分析步骤。

# 一般处理流程

1. **判断问题类型**：先判断用户问题是否属于数据分析相关诉求，例如智能问数、指标统计、趋势对比、归因、预测、相关性、异动检测、智能看板或分析报告。
2. **非分析诉求给出引导**：如果用户问题不是数据分析相关诉求，按 `# 任务执行原则` 中的边界处理；当用户明确指定 `Databuddy / DataBuddy` 但诉求属于配置、管理、开通、权限或页面操作等非分析事项时，引导用户前往 Databuddy 界面进行配置，并给出按 `https://{consoleDomain}/buddy?o={workspaceId}&r={regionId}#/databuddy/new-task?mode=engineering` 拼接的动态链接：`consoleDomain` 取 `wedatacli GetEnv consoleDomain`（缺省回退 `databuddy.cloud.tencent.com`），`workspaceId` 取 `wedatacli GetEnv workspaceId` 作 `o`，`regionId` 取 `wedatacli GetEnv regionId` 作 `r`；`workspaceId` 或 `regionId` 任一读取不到时，如实说明“未获取到当前 Workspace / Region，无法生成 Databuddy 引导链接”，不要输出占位或臆造值的链接。
3. **确认当前空间**（仅数据分析场景，即第 1 步判定为数据分析相关诉求时才走本步；非分析诉求已在第 2 步兜底，不进入本步）：先判断用户本轮是否主动指定了 `Workspace` 或数据知识库 Key。
   - **已主动指定**：调用 `wedatacli workspace config_set --workspace-id ... --analysis-space-key ...` 一次性更新 CLI 会话默认配置（region/regionId 由 config_set 内部通过账户级 `ListWorkspaces` 反查 workspace_id 自动填入，无需手动传 `--region`；数据知识库 `key` 可由 `wedatacli workspace list_analysis_spaces` 输出得到），再通过 `wedatacli GetEnv workspaceId` 与 `wedatacli GetEnv analysisSpaceKey` 读取当前配置并向用户确认。
   - **未主动指定**：通过 `wedatacli GetEnv workspaceId` 与 `wedatacli GetEnv analysisSpaceKey` 读取当前 `Workspace` 与数据知识库 Key；两者都非空时直接进入下方"两个值都非空"分支。不能带着空值继续后续分析动作：
     - `workspaceId` 为空 → 先执行 `wedatacli workspace list` 拉取候选，可能返回的 workspace 项比较多，需要在对话中将所有的工作空间名称列表都展示出来。然后再把返回的其中的 `name` 作为选项通过 `AskUserQuestion` 让用户选择目标工作空间。
     - `analysisSpaceKey` 为空且 `workspaceId` 已确定 → 先执行 `wedatacli workspace list_analysis_spaces --workspace-id <workspaceId>` 拉取候选；如果候选为空，必须停止后续分析、看板或报告动作，并如实说明“当前工作空间未获取到可选数据知识库，无法确认分析场景”；如果候选只有 1 个，直接用该候选的 `key` 执行 `wedatacli workspace config_set --workspace-id <workspaceId> --analysis-space-key <key>` 自动绑定，随后通过 `wedatacli GetEnv workspaceId` / `wedatacli GetEnv analysisSpaceKey` 复核，并告知用户已自动绑定的数据知识库名称后继续分析；如果候选多于 1 个，需要在对话中将所有的数据知识库名称列表都展示出来，然后再把返回的 `name` 作为选项通过 `AskUserQuestion` 让用户选择目标数据知识库。
     - 两者都为空 → 先追问工作空间，用户确认后再按上一条规则处理数据知识库；不要一次性混在一起。
     - 用户在 `AskUserQuestion` 中给出选择后，用 `wedatacli workspace config_set` 一次性写入所选 `workspace-id / analysis-space-key`（region 由工具反查自动填入；写操作，需符合"写操作需要明确正向信号"红线，此处用户在追问中的明确选择即视为正向信号），再通过 `wedatacli GetEnv workspaceId` / `wedatacli GetEnv analysisSpaceKey` 复核。
   - **两个值都非空**：把当前 `Workspace` 与数据知识库以**名称**形式展示给用户（`workspaceId` 通过 `wedatacli workspace list` 反查对应 `name`；`analysisSpaceKey` 通过 `wedatacli workspace list_analysis_spaces` 反查对应 `name`），格式如「工作空间：<name>、数据知识库：<name>」；ID / Key 仅在名称反查失败或用户明确要求时才附带展示，让用户知晓本轮任务的执行空间，然后继续后续分析、看板或报告生成动作。
4. **支持空间切换**：如果用户指出当前 `Workspace` 或数据知识库不正确，先用 `wedatacli workspace list` / `workspace list_analysis_spaces` 定位目标 `id` / `key`（region 无需人工获取，config_set 内部会反查），再用 `wedatacli workspace config_set --workspace-id ... --analysis-space-key ...` 一次性写入；切换后再次通过 `wedatacli GetEnv workspaceId` / `wedatacli GetEnv analysisSpaceKey` 确认，避免结果来自错误空间。写入前视为写操作，需要用户明确正向信号。
5. **自行编排执行路径**：根据用户问题选择合适的 Skill 或 `wedatacli` 命令处理。简单问数走 `intelligent-query`，智能看板走 `intelligent-kanban`，复杂宽泛分析先走 `data-task-planner`，报告交付走 `report-composer`，归因、预测、相关性、异动检测优先使用对应 CLI 标准分析命令。
6. **多轮推进直到完成**：任务可能涉及多轮确认、多次 Skill 调用或多次 CLI 调用；由当前模型根据上下文自行决定拆解、调用、汇总和收敛方式，直到用户问题被完整回答或明确说明无法继续的原因。

# 输出要求

- **每轮带环境信息**：每轮面向用户的回复都带上当前所处 `Workspace` 与数据知识库信息，方便用户确认本轮结果的输出来源。**优先展示名称（`name`），而不是 `workspaceId` / `analysisSpaceKey`**：先通过 `wedatacli GetEnv workspaceId` / `wedatacli GetEnv analysisSpaceKey` 读取当前 ID / Key（均为 CLI 命令，stdout 单行文本），再分别通过 `wedatacli workspace list` / `wedatacli workspace list_analysis_spaces` 按 ID / Key 反查对应 `name` 用于展示；同一轮会话内可复用已拉取的清单结果，避免每轮重复调用。名称反查失败时可回退展示 ID / Key 并简要说明“未反查到名称”；`GetEnv` 读取不到时如实说明“未获取到”，不要编造。
- **语言跟随调用参数**：回复语言以 WorkBuddy 调用本 Skill 时传入的语言参数为准；未传语言参数时，跟随用户本轮输入语言。代码、SQL、字段名、路径、命令和专有名词保持原样，不因回复语言切换而翻译。