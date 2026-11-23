---
name: 喜鹊标书
description: 使用 WorkBuddy 连接器市场中的喜鹊标书，完成参数配置、大纲与目录审阅、修改、正文生成及 Word 导出。适用于招标文件、技术标和商务标任务；连接与 API Key 由 WorkBuddy 管理。
---

# 喜鹊标书工作流

本 Skill 随 WorkBuddy 市场连接器安装。仅通过当前连接器提供的 `xique_*` MCP 工具执行业务。
禁止直接运行标书 CLI、启动 MCP 服务或创建辅助业务脚本。不得把日志、进程状态当作生成完成依据。
工具命名空间以宿主实际提供的名称为准；发布配置的 source 为 `xique-bid`，平台生成的连接器 ID 以发布后台为准。

## 连接、认证和更新

1. 用户首次使用时，在 WorkBuddy 的“连接器 → 喜鹊标书”中点击连接，并在密码输入框填写自己的 API Key。禁止在对话中索取密钥。
2. 开始业务前调用一次 `xique_runtime_status`，核对 `connectionMode=workbuddy-token`、`nodeSupported=true`、`cliFound=true`、`pluginVersion >= 0.10.45`、`cliVersion >= 0.3.23` 和 `apiKeyConfigured=true`。
3. `loggedIn=true` 只表示已配置凭证，`credentialVerified=false` 表示此只读检查尚未验证密钥有效性。不能据此声称喜鹊账号授权已经通过验证。
4. Key 缺失、`WORKBUDDY_CONNECTION_REQUIRED` 或后端明确返回凭证失效时，请用户到连接器中重新填写 API Key 并连接，然后恢复同一 `runId/cid/uuid`；用户完成连接之前不循环轮询，不创建替代任务，不打开本机登录页。权限不足、余额不足、网络故障分别报告实际原因，不能全部当作登录失效。
5. 安装、更新和重新连接由 WorkBuddy 的连接器界面完成。工具不可用或版本不足时引导用户更新市场连接器，不执行外部安装器，不修改用户的 `mcp.json`，不引导改走自定义 MCP 或修改信任记录。
6. 如果同时安装过旧版自定义“喜鹊标书”或独立同名技能，提示用户完成迁移后仅保留当前市场入口；不得自行删除旧凭证或任务。市场版不得回退到其他客户端保存的旧 API Key。

字段映射参见 `references/configuration.md`，卡片交互参见 `references/interactive-configuration.md`。以下业务确认规则在市场版同样生效。

## 交互原则

1. 取得源文件后先调用一次 `xique_prepare_source`。它只上传并解析文件，不生成大纲。持续查询返回的
   `runId`；当 `xique_generation_status` 返回 `status=awaiting_input` 且 `stage=bid-config` 时，必须立即显式调用
   `xique_bid_configuration(runId)`。状态工具只报告阶段，不负责打开配置卡；这样 WorkBuddy 才会按带有 MCP App 元数据的阶段工具渲染卡片。
2. `xique_bid_configuration` 必须绑定该 `runId`，在一页中展示真实多标包/EPC选项、普通参数和暗标生成方式。
   普通文件不显示多标包/EPC字段。用户提交后不得再次打开配置卡或允许二次选择。
3. 只在用户之后单独修改某一项时使用 `xique_select_option`。
4. 使用 `xique_outline_start`、`xique_special_project_selection`、`xique_period_confirmation`、
   `xique_reference_basis_selection`、`xique_outline_confirmation`、`xique_outline_update_confirmation` 和
   `xique_directory_confirmation` 展示对应阶段卡片。规划模式必须按“智能解读→大纲→目录→正文”推进，快速模式按“大纲→正文”推进。
5. 返回 `interactionMode=mcp-app` 时，WorkBuddy 会自动打开关联 MCP App。立即结束当前回复并等待用户点击；
   禁止调用 `read_me`、`show_widget`，禁止输出编号文本选项，禁止改用 `AskUserQuestion`。
6. 每张 MCP App 卡片只能提交一次。第一次提交时立即锁定，即使超时或传输结果不确定也不得恢复点击，
   应查询当前工作流状态，避免重复请求。
7. MCP App 点击生成的 `【喜鹊标书配置批量选择】`、`【喜鹊标包与EPC选择】`、
   `【喜鹊标书配置选择】` 或 `【喜鹊标书确认】` 消息属于明确的用户输入。
8. 不得给枚举选项追加 `Other` 或 `其他补充`。

## 一页配置要求

必须先通过 `xique_prepare_source` 解析文件，再展示完整配置页。禁止先展示普通配置后重新上传文件，
也禁止由代理直接运行 `init` 并把解析对象手工传给配置工具。

配置页字段顺序与喜鹊web端保持一致；排版相关设置采用折叠分组：
1. 如果已预解析出多标包/EPC，在最顶部显示「多标包选择」和「EPC项目编写范围」；
2. 篇幅 → 写作质量 → 计划模式 → 正文风格 → 表格数量 → 图片设置（直接展示）→ 暗标设置 → 导出格式设置（表格样式、表格颜色、流程图样式、导出模板、模板5自定义编号、导出布局、自动编号、修改标记、页边距、图片尺寸）→ 输出路径。

必须展示完整合法值：

- 篇幅：`极短篇（50–100页）`、`超短篇（100–200页）`、`短篇（200–350页）`、
  `中篇（350–500页）`、`中长篇（500–800页）`、`长篇（800–1200页）`、
  `超长篇（1200–1500页）`。传给 MCP 时只传括号前的名称。
- 写作质量：`标准写作`、`专家智笔`、`旗舰智笔`。极短篇和超短篇固定使用标准写作，并说明喜鹊前端也会禁用专家智笔和旗舰智笔。
- 计划模式：`快速`、`规划`，默认快速。
- 正文风格：`增强图文`、`全表格式`、`丰富图文`、`基础配图`、`纯文字`。
- 表格：`无（不插入表格）`、`少量（约每4页1表）`、`丰富（约每2页1表）`；传给 MCP 时只传名称。
- 表格颜色：`黑色`、`蓝色`、`红色`、`绿色`、`紫色`、`青色`、`橙色`。
- 表格样式：`纯净版`、`表头强化`、`斑马条纹`、`全底色白框`。
- 图片设置必须展示全部选项：`我的图库`、`实拍风格图`、`PPT式插图`、`流程图`、`无配图`。
- 流程图样式：`灰色`、`紫色`、`蓝色`、`绿色`、`橙色`、`红色`。
- 暗标设置：`按通用方式生成`（默认）、`按暗标生成`。提交后必须真实进入大纲请求的
  `blindBidConfirm.blindGenerationMode=normal|blind`，不能只停留在界面字段。
- 导出模板：
  - `模板1｜章节目次（第一章→第一节→一、）`
  - `模板2｜中文层级（一、→（一）→1）`
  - `模板3｜全数字分级（1→1.1→1.1.1）`
  - `模板4｜章节+数字（第一章→1→1.1）`
  - `模板5｜自定义编号（可视化设置）`，选择后在“导出格式设置”中显示“模板5自定义编号”，不要求用户输入 JSON。
- 导出布局：`常规`、`全表`、`精排`。
- 自动编号：`开启`、`关闭`；修改标记：`关闭`、`开启`。
- 输出路径：`默认`、`指定路径`。只有选择指定路径后才允许询问绝对路径。

多标包和EPC只显示本次预解析任务返回的真实选项，不显示占位项，不允许手工填写 ID。
EPC 选项只允许 `全部编写`、`只写施工`、`只写设计`、`这不是EPC项目`，不得由用户手输或由模型虚构。

WorkBuddy 标准流程必须展示 `计划模式=快速/规划`。配置消息中已提供计划模式时，必须原样提交：`规划` 对应 `--plan-mode 1`，`快速` 对应 `--plan-mode 0`，不得把规划改成快速；只有配置消息没有该字段时，才补默认 `快速`（`--plan-mode 0`）。
不得展示高级样式 JSON 输入框；模板5使用 WorkBuddy 的可视化导出设置卡生成结构化编号配置。
不得在普通配置页要求用户输入多标包 ID、标包类型或 EPC 类型。

图片设置分组默认展开，用户打开配置页即可看到并选择全部选项：`我的图库`、`实拍风格图`、`PPT式插图`、`流程图`、`无配图`，并在同一分组中提供流程图样式；图片尺寸仍在下方单独设置。
`xique_bid_configuration` 在构建一页配置时必须内部调用 `xique_gallery_status` 查询当前用户图库状态；
用户之后单独修改图片设置时，也必须先调用一次 `xique_gallery_status`，不得根据字段是否存在推断图库可用。

- 有图片时显示 `我的图库（可用，共N张）`；
- 无图片或查询失败时显示 `我的图库（暂无图片，不可选）` 并保持关闭；
- 实拍风格图同时控制 `sceneImg=1` 和 `onlineImg=1`，不得单独展示联网搜图；
- PPT式插图对应 `infoImg=1`，流程图对应 `mermaidImg=1`；
- 无配图与其他图片类型互斥；
- 选择流程图时展示 `灰色`、`紫色`、`蓝色`、`绿色`、`橙色`、`红色`。

`xique_bid_configuration` 的 WorkBuddy 参数卡会预选：标准、快速、基础配图、丰富表格、按通用方式生成暗标、
纯净版、蓝色、仅流程图、灰色流程图、模板1、常规、自动编号开启、修改标记关闭、默认输出路径。
篇幅保持未选择，用户可以修改任何预选项；只有点击 `提交全部配置` 后，卡片实际值才算用户选择。
不得绕过配置卡或在用户提交前把这些预选值传给 `xique_prepare_bid`。

只有用户明确说 `用默认配置`、`你自己定` 或 `随便先跑一版` 时，才可补齐完整默认配置中的
篇幅=短篇，并采用上述预选值。响应依据不能在此阶段补齐，必须等待喜鹊生成候选后再选择。

任何问题绕过参数默认均为关闭。只有用户明确授权某一个具体例外时，才能开启对应例外，
不得把一次授权扩展到其他问题。

## 生成完整标书

1. 调用 `xique_runtime_status` 并按上方“连接、认证和更新”核对环境。未配置 API Key 时，请用户到 WorkBuddy 连接器中连接；不要创建或上传任务。
2. 取得源文件绝对路径，调用一次 `xique_prepare_source`，记录返回的 `runId`。
3. 持续调用 `xique_generation_status(runId, waitSec=60)`。返回 `awaiting_input/bid-config` 后，立即显式调用绑定该
   `runId` 的 `xique_bid_configuration` 打开统一配置卡；不得等待用户追问，也不得把状态工具返回的状态文本当成配置已提交。
   不得提前调用 `xique_prepare_bid`，不得重新上传源文件。
4. 用户提交统一配置卡后，直接把 `structuredContent.config`（含 `sourceRunId`）传给一次
   `xique_prepare_bid`，不得再次询问或改写已选择字段。
5. 原样展示 `xique_prepare_bid` 返回的完整配置摘要，明确说明尚未开始生成。
6. 调用 `xique_outline_start(context=完整配置摘要, confirmationId=准备结果)`，展示
   `确认开始`、`返回修改`、`取消`。配置摘要之后的点击才是有效生成确认。
7. 用户点击确认后，只调用一次 `xique_generate_bid`。返回的 `runId` 与预解析任务相同；该调用复用已有
   `cid/uuid`，只启动大纲生成，不得再次解析、上传或创建任务。
8. 立即调用 `xique_generation_status(runId, waitSec=60)`，状态为 `queued` 或 `running` 时持续查询同一任务。
   本地轮询窗口到期不是失败，不得创建替代任务。
9. 规划模式的智能解读只作为后台阶段，不向用户展示 `analysis-review`，也不打开智能解读确认卡。后台检测到
   `analysis_ready` 后会自动对同一 `cid` 执行一次 `plan confirm-outline`（即后端 `/task/generateDirectoryByCid`）并继续生成大纲。
   持续查询同一 `runId`，不得调用 `xique_prepare_analysis_continue`、`xique_analysis_confirmation`、
   `xique_continue_analysis`、`xique_generate_bid`、`xique_continue_bid` 或 `write` 来推进这个内部阶段。
10. 仅恢复旧版本创建的历史任务时，若状态为 `awaiting_input/special-config`，使用
   `xique_special_project_selection` / `xique_apply_special_project_selection` 继续同一任务；新标准流程不得进入此阶段。
11. 状态变为 `awaiting_input/period-confirm` 时，只调用一次 `xique_period_confirmation`，展示并收集
   `periodMode`、`contractPeriod`；日期已知时再收集 `contractStartDate` 和 `contractEndDate`。随后只调用一次
   `xique_apply_period_confirmation`，继续同一 `runId`，不得重新上传或创建任务。
12. 状态变为 `awaiting_input/bidder-role` 时，只调用一次 `xique_bidder_role_selection(runId)` 展示“我们自己生产 / 我们采购供应”；用户选择后只调用一次 `xique_apply_bidder_role_selection`，传入卡片返回的 `runId` 和 `bidderRole`，继续同一任务；不得把它误解为暗标设置，也不得重新上传或创建任务。旧版本已标记为 `blocked` 但错误详情包含 `bidderIdentity_judgement` 的任务，也按此方式恢复。`epcEngineer_judgement` 是分类值：只有 `1` 表示必须进入 EPC 编写范围选择，`0` 表示不需要 EPC 范围；不得把 `0` 当作缺失配置，也不得在供应方式提交后重新打开 EPC 卡或停留在 `special-config-sync`。
12.1. 商务标任务（`originType=3`）在统一配置卡中必须选择投标公司。配置卡通过
    `POST /xq/enterprise/company/list` 展示企业资信库真实公司，提交 `bidderCompanyId` 和
    `bidderCompanyName` 到 `/task/preSet`；列表为空或请求失败时保持必填并明确提示，不能让缺少公司的任务进入后台后再卡住。
12.2. 状态变为 `awaiting_input/supplement` 时，必须按 `supplementIssue` 打开补充卡：`score_judgement` 使用
   `xique_score_supplement`，其余问题使用 `xique_parse_supplement`。评分细则卡必须提供“输入评分细则”和“上传评分文件”两种方式；文本提交支持 HTML，文件提交填写本机绝对路径，支持 `.doc/.docx/.pdf/.xlsx/.xls`。
   `requirement_exist` 只能输入或上传招标需求，不能选择跳过；`requirement_judgement`、`billOfQuantities_judgement`、
   `score_judgement` 可明确选择“不补充，直接生成”；`directory_judgement` 只输入技术方案目录要求，或明确选择不采用，不能上传目录文件。
   用户提交后只调用一次 `xique_apply_parse_supplement`（评分兼容别名为 `xique_apply_score_supplement`），必须传卡片携带的同一
   `runId`，并继续查询该任务；禁止重新调用 `xique_prepare_source`、`xique_prepare_bid` 或 `xique_generate_bid`。后台若返回新的补充问题，按新的
   `supplementIssue` 再打开补充卡；如果返回 `scoreAndDirectory_judgement`，必须改用
   `xique_outline_basis_selection`，选择“融合评分和参考目录 / 仅依据评分 / 仅依据参考目录”，再调用
   `xique_apply_outline_basis_selection`（对应 `/proxy/saveDirectoryBasis`）；只有后续真实候选目录生成并返回
   `reference_selection_required` 时，才改用 `xique_reference_basis_selection`；如果返回 `bidderIdentity_judgement`，必须改用
   `xique_bidder_role_selection`。这两类后续选择仍沿用同一 `runId/cid/uuid`，不能把它们误当成评分/需求补充，
   否则会出现任务一直等待或重复提交；没有新的待处理状态时才按原快速/规划阶段继续。
   如果返回未列入上述清单的 `*_judgement=0`，不要猜测补充类型或继续轮询；保留同一 `runId`，
   报告 `unsupported_intermediate_state` 并提示升级插件后恢复。
13. 状态变为 `awaiting_input/basis-selection` 时，只调用一次 `xique_outline_basis_selection(runId)`，选择解析阶段的“融合评分和参考目录 / 仅依据评分 / 仅依据参考目录”，随后只调用一次 `xique_apply_outline_basis_selection`，继续同一 `runId`；不得把它当作候选目录预览，也不得重新上传文件。
14. 状态变为 `awaiting_input/reference-selection` 时，只调用一次 `xique_reference_basis_selection(runId)`。卡片用“融合响应 / 仅格式要求 / 仅评分要求”三个页签展示喜鹊返回的完整候选目录树；切换页签只能预览，不得将其解读为用户确认。用户只有点击“按当前思路生成大纲”后，才只调用一次 `xique_apply_reference_basis_selection`，继续查询同一 `runId`；不得重新调用 `xique_generate_bid`、重新上传文件或重复提交响应依据。
14. 状态变为 `awaiting_confirmation/outline-review` 时，完整展示 `outlineDetail.outLine` 的每一行，包含标题、主题、
   重要性和 id。每个数组元素显示为独立编号块，并核对显示数量等于数组长度；不得只显示章节数量或摘要。
15. 调用一次 `xique_prepare_outline_continue(runId)`，把完整大纲、摘要、准确的 `runId` 和
    `confirmationId` 传给 `xique_outline_confirmation`，展示：
    `确认大纲并生成正文`、`修改大纲`、`暂不继续`。
16. 快速模式用户点击 `确认大纲并生成正文` 后，只调用一次 `xique_continue_bid`。规划模式用户点击
    `确认大纲并生成目录` 后，也只调用一次 `xique_continue_bid`；该调用只启动目录生成。
17. 规划模式目录完成后，完整展示目录树。修改时必须提交全部根节点和完整子树，保留所有已有节点 `id`，目录名称使用 `text`；
    不得只提交被修改的章节。只有用户明确要求删除节点时才可传 `allowDelete=true`。通过 `xique_prepare_directory_update` /
    `xique_apply_directory_update` 修改并保存；保存失败时必须重新查看、重新预览并再次确认，禁止自动重复保存；保存后调用一次 `xique_prepare_directory_continue`，再用 `xique_directory_confirmation` 展示
    `确认目录并生成正文`。用户确认后只调用一次 `xique_continue_content`。
18. 继续调用 `xique_generation_status(runId, waitSec=60)` 直到 `completed`、`failed` 或 `blocked`。
19. 只有结果同时满足 `status=completed`、`fileExists=true` 和 `savedPath` 非空时才报告成功。
    随即调用 `present_files(savedPath)`，让 Word 文件直接显示在 WorkBuddy，并提供绝对路径。
    同时告知用户如需调整编号、页边距或图片尺寸，可对同一 `cid` 调用 `xique_export_configuration` 重新导出，
    不会重新生成正文。
20. 后台明确返回失败或阻塞时立即报告准确原因，不得等待用户主动追问。

新任务只有一种多标包/EPC交互：先预解析，再在统一配置页一次选择。不得退回“先普通配置、生成后再弹特殊配置”的流程。
EPC 选项只允许 `全部编写`、`只写施工`、`只写设计`、`这不是EPC项目`，不得由用户手输或由模型虚构。
暗标生成方式默认选择“按通用方式生成”，用户可根据需求切换为“按暗标生成”，自动避开身份信息。

## 修改大纲

用户选择 `修改大纲` 后：

1. 询问具体修改要求，基于最新结构化大纲构造完整 `outLine` 数组。
2. 保留所有未修改章节及 id；只有用户明确要求删除时才移除现有行；新增行不带 id。
3. 调用 `xique_prepare_outline_update`，完整展示新增、修改、删除、移动、重要性变化和续写要求。
4. 调用 `xique_outline_update_confirmation`，展示 `确认保存修改`、`返回调整`、`取消`。
5. 只有点击 `确认保存修改` 后才调用 `xique_apply_outline_update`。
6. 保存后完整展示最新大纲，并明确说明：`修改已保存，但正文尚未开始，仍需确认最终大纲`。
7. 对同一个 `runId` 重新执行大纲最终确认，不得返回配置页或创建新任务。

## 再次生成与单独导出

用户说 `再跑一遍` 时，只复用最近一次由用户明确确认的配置；如果无法确定最近确认配置，则重新展示配置页。
重新准备后仍必须展示摘要并取得新的生成确认。

单独导出现有任务或用户要求调整已生成文件时，先调用 `xique_export_configuration(cid)` 打开一次性导出设置卡。
卡片在默认收起的“导出格式设置”中展示表格样式、表格颜色、模板/布局、标题和正文编号、起始编号、页边距、横向/纵向图片尺寸、自动编号和修改标记；图片来源保持直接展示，输出路径单独展示；选择模板5后显示对应编号字段。模板5自定义编号采用与 Web 页面一致的分组排版：标题级编号控件归入“标题设置”，正文编号控件归入“正文序号设置”，并按卡片宽度自动换行；字段语义和提交的 `customNumbering` 结构保持不变；
用户提交后卡片会自动调用 `xique_prepare_export` 暂存结构化配置。展示摘要并等待新的明确确认，确认后才能调用 `xique_export_bid`。

任务返回 `OUTLINE_BLOCKED` 或 `WRITE_BLOCKED` 时，保留并报告 `cid`，用中文解释问题，
只询问缺失选择或具体绕过授权，然后重新展示完整配置摘要并等待确认。

当前 WorkBuddy 任务保持打开时持续轮询并自动交付文件。WorkBuddy 被关闭、任务中断或客户端强制结束回合后，
后台任务仍可继续，但不得声称可以在应用关闭后主动推送通知；用户回来后使用原 `runId` 恢复查询。

绝不在没有非空 `savedPath` 的情况下宣称标书生成成功。
