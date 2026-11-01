# 硬门

所有场景共享的执行契约。场景文档只写本场景步骤和完成谓词，不复述本页。

## 入口

1. 按 [SKILL.md](../../SKILL.md) 路由表选定恰好一个场景文档。未选定前不跑写命令。咨询应答走 [user-guide.md](../user-guide.md)：原样返回全部内容后停止，不套本页进度、完成总结或写命令。
2. 只读取该场景涉及的 `commands/*.md`。命令或字段没有 contract 时，依次查看 `reelmate --help`、`reelmate COMMAND --help`；仍未定义则停止并说明缺口。
3. 进度分母来自场景文档写死的步骤表。对用户报告进度时写 `进度 n/m：动作`（例如 `进度 1/4：提取资产清单并确认`）。总步数不临场发明。四环节不要写成「环节 n/4」：分母是当前阶段文件的步骤数（项目 1、剧本 1、资产 4、分镜 3）。

## 身份与 ID

- 联网前确认登录态：已登录则复用，未登录才执行 `reelmate login`。凭据只由 CLI 管理。
- 所有 ID 只取上一跳 `--json` 的 `data`（或成功 envelope 的等价字段）。
- `error.raw.needs_input=true` 时只按 `error.raw.missing[]` 追问。

## 当前包

阶段型场景（GUI 主流程、批量回填、无限画布剧本）在开始、续跑和写操作前执行对应 `workflow detect`。只消费 `data.stage`、`completed`、`pending`、`missing`、`next_command`。把返回值当成当前包：执行它指向的步骤，不重读整本手册自行排期。

无限画布生图或生视频不套阶段机。先用 `workspace show` / `node list` 得到当前包：`create-blank`、`edit-existing` 或 `regenerate`，三选一。

探测、回引和命名 HITL 见 [_stage-machine.md](_stage-machine.md)。有限选项怎么呈现见 [_hitl-present.md](_hitl-present.md)。登录、建项、建画布见 [_bootstrap.md](_bootstrap.md)。

## 本地中间文件

Agent 需要落盘的 JSON、模板、缩略图、`task download` 产物，一律写**当前工作目录**下的 `outputs/`（相对路径，跟用户在哪执行 `reelmate` 走）。禁止再开 `generated-images-*`、`outputs/<项目拼音>`、带日期或随机后缀的新目录。覆盖同名文件时用 `overwrite=true`，不要换目录名躲避冲突。`~/.reelmate` 仍只由 CLI 自己写，不是用户产物目录。

## 写入

- 批量或付费写先 `--dry-run --json`，确认后用本次唯一 `--idempotency-key` 提交。
- 回包出现 `idempotent_replay=true`：这个 key **已经打到服务端**。用回包里的 `task_id` / `task_ids` 去 `task wait`，禁止换新 `--idempotency-key` 去重新请求。
- `--help` 未列出所需子命令时停止并报告能力缺口，不改走语义相近的命令。
- 异步任务查询到终态成功才能进入下一步。超时先 `task get` 原 ID，不重新提交。
- 部分失败只重跑 `failed[]`。远端已经前进时不得拉回旧阶段。

## 权限拒绝

收到失败 envelope 的 `error.kind=permission` 时，把 `error.message` **原样**写入用户可见回复，然后停止。禁止重试、禁止改走语义相近的命令、禁止建议换号或执行 `login`。不要改写、不要加前后缀、不要换成 Web toast 或其它解释。`error.raw` 只给测试看，不要读给用户。

新建项目在进入 `hitl.project-create` 之前，先执行 `reelmate team permission --require project.create --json`。收到 `error.kind=permission` 时按上一段停止，不要询问剧目类型或画面比例。退出码 0 再提问。绑定已有项目不执行这条预检。

付费参数提问前，按当前场景先预检，再查模型或模板目录，再进入 HITL。收到 `error.kind=permission` 时按上一段停止，不要询问该组参数。退出码 0 再继续；`permission_ready=false` 也算通过。

- 资产提示词回填进入 `hitl.paid-image-params` 前：`reelmate team permission --require resource.edit --json`
- 制片工坊拆分镜进入 `hitl.paid-video-params` 前：先 `reelmate team permission --require episode.edit --json`，再 `reelmate team permission --require storyboard.edit --json`
- Excel 分镜视频回填进入 `hitl.paid-video-params` 前：`reelmate team permission --require storyboard.edit --json`。该场景不调用 `episode match-resources`，不要预检 `episode.edit`
- 无限画布生图或生视频的步骤 3，进入对应付费参数 HITL 前：`reelmate team permission --require project.edit --json`。视频重跑先回到步骤 3，因此带上这条预检

工坊资产提取先执行 `resource extract`，不为随后的图片参数再加 `resource.edit` 预检。

## 完成

场景文档的 `done_when` 全部满足才报告完成。谓词未齐时只返回失败项和下一步，不输出完成总结。

只在向用户报告本轮任务完成时输出下面这份**固定完成总结**。阶段机中间包切换（例如 `project`→`script`）不输出。缺必填行都不算完成，先补查对应命令再写。「积分消耗」按下一节条件可整行省略，省略不算缺行。场景只能在清单后追加本场景多出来的项，不能删、不能改名、不能用「见上文」省略。本轮必须现跑命令取数，禁止用记忆或时间段估算冒充。

```
## 完成总结
- 结果：完成 | 部分失败（列出失败项）
- 剧厂项目链接：本轮 `deeplink` 返回的 `href`（场景规定的那条）
- 参数：本轮实际提交的展示名（模型、画幅、分辨率等已确认项）
- 产物：图 / 视频 / 文本 / 资产状态等本场景结果证明
- 积分消耗：实扣 N（匹配到 T/T 条生成任务）；当前余额 B
- 积分明细：请点击以下链接，前往剧厂 Web 产品端查询积分扣除明细：<本轮 `deeplink credits` 的 href>
- 未做：用户没要的本地下载、合并导出等，写明未做
```

「积分消耗」仅当流水全匹配时输出：T≥1 且 M=T（本轮全部生成 `task_id` 都匹配到消耗流水 `rm_task_id`）。写成「实扣 N（匹配到 T/T 条生成任务）；当前余额 B」，不要写「未入账」。M<T（含 0/T、部分命中）或 T=0（本轮无生成 `task_id`）时**整行不输出**。禁止把未全匹配改写成「预估」、禁止输出「实扣 N + 预估 E」、禁止用「本轮无生成扣费任务」占位，也禁止为凑这一行编数字。

「积分明细」这一行始终保留，href 必须本轮执行 `reelmate deeplink credits --json`，禁止手拼。Web 积分扣除明细是顶栏弹窗、没有独立消耗页；该深链打开剧厂首页，登录后点右上角积分查看「消耗」。不要用 `deeplink pricing`（那是充值弹窗入口）冒充扣除明细。

## 积分展示策略

所有制片工坊付费动作都走同一套确认口径，包括资产清单提取、资产提示词生成、主/子资产生图、资产匹配、缺失资产提示词补全、拆分镜和视频生成。提交前先取得统一账单、`credits balance` 和 `deeplink credits`，再在同一条确认消息中展示：

1. 每条 `line_items[]` 计费明细的动作、实际参数、业务数量 `business_count`、单业务生成数量 `qty`（有值时）和小计；同参数批量生图/视频必须明确写成「单价 × 业务数量」，不得把 `qty` 当成资产数或分镜数。
2. 总计使用账单 `data.total_cost`，区间计价同时展示 `min` / `max`；即使总计为 0 也要展示「预计消耗 0」，不能把 0 自动解释成免费。
3. 当前余额 B，以及固定文案「请点击以下链接，前往剧厂 Web 产品端查询积分扣除明细：`<href>`」。

统一账单的 `data.source` 决定展示文案：

`source` 只用来选择文案，不要把字段名或接口名写给用户。禁止把预估写成「实扣」。

| `source` | 展示规则 |
|---|---|
| `point_calculate` | 只写「预计消耗」。禁止写出 `point_calculate`、`source`、「报价来源」或「Web 同源」 |
| `web_formula` | 按 Web 当前公式与首次权益计算，写「预计消耗」并展示 `benefit_applied` |
| `provisional` | Web 页面存在暂行规则但尚未最终定价，必须写「暂估消耗」，同时展示 `reason` |
| `unavailable` | `source=unavailable` 时明确写「当前 Web 无可验证积分预估：REASON」；仍展示当前余额和积分明细链接，不得隐藏、填 0 或借用其它动作/模型价格 |

`resource generate --dry-run`、`resource batch-draft-generate --dry-run`、`storyboard batch-generate --dry-run` 和 `storyboard batch-generate-video --dry-run` 的 `credits_estimate` 是询价输入，不是价格。把它原样交给 `credits estimate`；多个异构分镜组使用 `requests[]`，同参数多业务项使用 `business_count`。TGI 2 的画质由 CLI 按生成默认补 `quality=medium`。资产清单提取、资产匹配和拆分镜使用 `credits estimate --set scenario=...` 的 Web 公式；缺失资产提示词补全使用 `provisional` 暂估；资产提示词生成当前返回 `unavailable`，也必须展示。剧集拆分不消耗积分，不查询统一账单，不展示积分预估或积分消耗；`episode split` 返回的 `task_id` 不计入完成总结的生成任务数 T。

生成后的完成总结仍只写实扣：用本轮全部生成 `task_id` 匹配流水，且 M=T、T≥1 时才输出「积分消耗」。M<T 或 T=0 时整行不输出，不用预估替代实扣。Agent 文本类生成同样遵守该规则。

## 余额不足（用户可见）

适用：`credits balance` 低于当次统一账单的 `data.total_cost`（或付费提交返回退出码 7 / 业务码 745701），且本轮尚未成功拿到生成 `task_id`。Agent 在会话内保留续跑上下文，**不要求用户本机执行命令**。

对用户可见回复必须包含：

1. **原因**：积分不足，说明预计消耗 N、当前余额 B（N 来自当次统一账单的 `data.total_cost`；B 来自当次 `credits balance`；缺一项就只写已有项，不编数字）。
2. **充值入口**：本轮 `reelmate deeplink pricing --json` 的 `href`（站点根路径上的充值弹窗）。
3. **进度 / 产物**：若已有项目或画布，给场景规定的 `deeplink project` 或 `deeplink canvas` 的 `href`；没有则不编。
4. **续跑约定**：固定收尾一句——**充值完成后回复我，我会从当前步骤继续执行。** 可同句说明无需用户自行敲 CLI。

禁止出现在用户可见回复中：

- 续跑用的 shell、`reelmate …` 命令块、环境变量赋值、`--idempotency-key` 示例。
- `workspace_id` / `SP_ID`、`canvas_id`、`node_id`、`episode_id`、`task_id` 等内部 ID（完成总结「参数」行也只写展示名，不写 ID）。
- 「请在本机执行以下命令」类指引（除非用户**明确要求**自己在终端续跑；此时可单独给可复制命令，仍不要混进默认的积分不足回复）。

仍须输出 [_hard-gate.md](_hard-gate.md) 固定完成总结（部分失败）；「积分消耗」行按上文 T=0 规则省略。积分明细链接仍要带。

积分消耗按 [credits.md](../../commands/credits.md) 核对：本轮成功返回的全部生成 `task_id` 去匹配 `credits flows --set tab=consume --json` 的 `rm_task_id`，对匹配条目取 `points` 绝对值求和；同时现查 `credits balance --json`。这才是「实扣」。`rm_task_id` 为空、缺失或不等于本轮任务号不得计入实扣。M 为命中条数，T 为本轮生成 `task_id` 条数。仅当 M=T 且 T≥1 时把求和结果写入完成总结「积分消耗」。M<T 或 T=0 时不输出该行，不得按时间段、`feature_name`、消耗页邻近行或任务回包 `points` 冒充实扣，也不为完成总结再跑 `credits estimate` 去填预估。本轮没有任何生成 `task_id`（例如只建项、只导入已有图片）时 T=0，不输出「积分消耗」，仍要输出积分明细链接，不跑预估。`resource add` / `confirm-record` / `subject save-from-resource` 在流水里没有记录，不计入 T。剧集拆分不消耗积分，`episode split` 的 `task_id` 不计入 T，完成总结不为这一步写积分预估或积分消耗。付费提交前的预估仍走统一账单：优先复用对应 `--dry-run` 的 `credits_estimate`，公式动作使用 `--set scenario=`；禁止用生成提交体里的 `tomoviee_*` 当预估算法码。

剧厂项目链接必须本轮执行场景规定的 `deeplink` 命令。完成总结这一行必须写「剧厂项目链接」，禁止改成「深链」。签名 URL 和任务中心链接不写入总结。问用户只列展示名，总结里的参数同样不写 `id` / `ai_model_mark`。

## HITL

只执行当前场景点名的 HITL 节点，以及 CLI `needs_input`。沿用历史参数必须先复述实际值。阶段探测和结果确认不能因“沿用”跳过。无限画布与制片工坊对 `hitl.paid-image-params` / `hitl.paid-video-params` 问的项不同，以当前场景文档为准；不要用下表把未点名的风格、题材、构图或提示词模板补进无限画布。文本模型不是下表确认项；生剧本见 [generate-script.md](generate-script.md)。新建项目的「画面比例」不是生图/生视频的「画幅」。

确认参数时只展示给人看的名称。推荐项只在名称后加 `（推荐）`，其它地方不要跟括号。用户回复序号或展示名都算选中；无效序号时提示后按同一批选项重选。不要把 `uk_id`、`id`、`ai_model_mark`、`generate_image_type`、模板 ID 或其它提交标识写给用户。提交时把用户选的展示名交给对应 `--set` 字段，由 CLI 解析；团队一步流和 AI拆分镜工作流模版例外，Agent 必须把所选条目映射回当次目录的字符串 `uk_id` 或 `workflow_id` 交给 `prompt_ukid`，同名项使用独立序号和描述/语言模型消歧，不按名字猜 ID。画布/预估须带已确认 `mode`，分镜走对应命令。禁止因为解析不唯一就把候选从列表删除或改推其它模型。怎么画选项（宿主选择器或回退列表）见 [_hitl-present.md](_hitl-present.md)，本页不写死排版。

凡是让用户确认有限选项的参数，都必须给出当次**全部有效可选项**，禁止收成「是否使用推荐配置 …」「请确认是否按默认配置执行」或只抛推荐包。推荐值只在对应选项后标 `（推荐）`，不能代替完整列表。列表必须出现在用户可见的最终回复里，怎么画见 [_hitl-present.md](_hitl-present.md)。场景点名必须交付的深链和摘要（不只是有限选项）也必须出现在同一条可见回复里；宿主选择器不能代替这些交付物。`hitl.asset-list-confirm` 的交付物是 `deeplink asset-confirm` 的 `data.href`，不要求在对话里列出名单。`hitl.asset-result-confirm` 的交付物是 `deeplink project` 的 `href`，要看图时再交本轮 `deeplink asset` 的 `href`（拆资产看图用 `deeplink asset-result`）；没有项目页链接不得提问。`deeplink credits` 的积分明细、`deeplink pricing` 和任务中心链接不得代替项目页。场景允许「不设置」时，把它写成选项里的一项，不要省略其它项。

上游选项会改变下游枚举时，必须分步问，禁止同一轮把尚未确定来源的下游项列出来。先确认上游，再按该结果列下游全部可选项。同一轮里互不影响的项可以一起问。用户改选上游后，丢掉旧的下游选择，按新结果重列再确认。不要在模型未定时提前写出画幅、分辨率或模板的推荐包。

当前会确认的参数、选项来源与提问顺序（新建项目三字段与 Web 一致；展示名只在本表维护，其它页不要再抄一遍）：

| 确认项 | 全部有效可选项从哪来 | 必须先确认 |
|---|---|---|
| 创作模式 | 制片工坊、无限画布。场景已钉死则复述、不弹；未钉死则列全。提交 `creation_mode`：制片工坊=`1`，无限画布=`2` | 无。与剧目类型、画面比例互不影响，可同轮 |
| 剧目类型 | [workspace.md](../../commands/workspace.md) 的展示名，按此顺序：国内仿真人剧、海外仿真人剧、2D/3D动漫。选项文案只写名称，不要带 `sp_type` 或数字，也不要列出 Web「自定义」（`workspace create` 只接受 1、2、3）。选完后再按名称提交 `2`/`3`/`1` | 无。与创作模式、画面比例互不影响，可同轮 |
| 画面比例（新建项目） | `9:16 竖屏`、`16:9 横屏`；`9:16 竖屏` 可标 `（推荐）`。提交 `ratio` 仍为 `9:16` / `16:9` | 无 |
| 风格 | 分别查 `preset-list --set kind=style --set res_type=1|2|3` 的 `list[].name`。问用户只列**一份**展示名（去重；顺序以角色目录为准，场景/道具多出的名称接在后面），标题写「风格」，不要拆成角色风格/场景风格/道具风格。对齐 Web：项目风格跨三类按名称映射，同名配置 ID 不同。提交各类 `style_uk_id` 时用所选名称在该类列表匹配；某类没有同名则停止 | 无。与题材、角色构图、图片模型互不影响，可同轮 |
| 题材 | 当次 `resource preset-list --set kind=theme` 的全部 `list[].name` | 无 |
| 角色构图 | 当次 `resource generate-image-types --json` 的全部 `list[].name` | 无 |
| 图片模型 / 视频模型 | 当次 `model list` / `search` 按 [_models.md](_models.md) 筛完后，按 `mode_order[目标模式]` 排列的全部展示名。资产生图（环节 3 / 资产提示词回填）的目标模式键是 `studio_asset_image`；剧本拆分镜的目标模式键是 `script_to_scene_refer`；分镜规划 / 回填参考生视频仍是 `universal_reference`；画布生图仍按 `text2image` 等画布模式 | 已有项目则 `sp_type` 已定；新建项目须先确认剧目类型 |
| 画幅（生图/生视频） | 所选模型目标规则的全部 `ratios`。资产生图选中后读 `params.generation.text2image`，只问一次，角色/场景/道具提交同一 `radio_ui`（对齐 Web 批量生成单一比例条） | 已确认图片或视频模型 |
| 分辨率 | 所选模型目标规则的 `resolution_options` 原序列 `label`；图片/画布视频用 `params.generation.<mode>`，资产生图选中后用 `params.generation.text2image`，分镜规划 / 回填 / 剧本拆分镜选中后用 `params.storyboard_reference_video`。资产生图本轮不问画质 | 已确认图片或视频模型。与画幅互不影响，可同轮 |
| 提示词模板 | 同时查询三类完整目录，在同一确认项中按「AI拆分镜工作流模版」「自定义工作流—AI拆分镜一步流模版」「官方工作流」排序，不单独询问来源。工作流：`episode prompt-templates --workspace SP_ID --set source=workflow --set all=true` 的完整 `list[].name`，不按模型过滤、不推荐第一项。一步流：同命令 `--set source=team-onestep --set lang=LANG --set all=true` 的完整 `list[].name`，同样不按模型过滤、不推荐第一项。官方：同命令带 `source=official`、`model=VIDEO_MODEL` 的 `resolved.candidates[]` 全部展示名；推荐用当次 `resolved.default_name`，禁止写死模板名。有 `--workspace` 时不要传 `model list` 的 `--sp-type`（海外仿真人项目是 `3`，不是 `2`）。合并、空目录与选择映射见 [拆分镜模板选择](gui-script-video-storyboard.md#模板合并与选择) | 已确认视频模型 |
| 时长 | 所选模型目标规则的全部 `durations` | 已确认视频模型。与画幅、分辨率互不影响，可同轮 |
