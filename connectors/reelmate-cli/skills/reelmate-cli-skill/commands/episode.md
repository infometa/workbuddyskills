# episode

管理制片工坊剧集，并将剧本文件拆解为分镜素材。`match-resources` 是制片工坊拆分镜流程的资产匹配入口，不是分镜视频生成命令。

## 按场景选子命令

| 场景 | 子命令链 | 流程文档 |
|---|---|---|
| 剧集 CRUD | `list`、`create`、`get`、`edit`、`delete`、`batch-create` | [gui-script-video.md](../manual/workflow/gui-script-video.md) |
| 剧本导入与拆集 | `split`、`split-list`、`split-delete` | [gui-script-video-script.md](../manual/workflow/gui-script-video-script.md) |
| 四环节：资产匹配与拆分镜 | `prompt-templates`、`match-resources`、`parse`、`parse-retry`、`parse-result` | [gui-script-video-storyboard.md](../manual/workflow/gui-script-video-storyboard.md) |
| 保存已有匹配关系 | `save-resource-matches` | 本篇 ``save-resource-matches`` |

## 用法

```text
reelmate episode list [--workspace WORKSPACE_ID] [--set creation_mode=0|1|2]
reelmate episode create [--workspace WORKSPACE_ID] [--name NAME]
reelmate episode get EPISODE_ID
reelmate episode edit EPISODE_ID [--name NAME]
reelmate episode delete EPISODE_ID
reelmate episode batch-create --set @episodes.json
reelmate episode split SCRIPT_PROJECT_ID --set file_id=FILE_ID|nt_id=NOVEL_ID
reelmate episode split-list [SP_ID]
reelmate episode split-delete [SP_ID] --set 'split_ids=["s-1"]'
reelmate episode prompt-templates [--sp-type 1|2|3] [--set ratio=16:9|9:16] [--set model=MODEL_MARK]
reelmate episode prompt-templates --workspace SP_ID --set source=team-onestep [--set lang=zh-CN] [--set all=true]
reelmate episode prompt-templates --workspace SP_ID --set source=workflow [--set all=true]
reelmate episode match-resources EPISODE_ID --set generate_mode=1 --set refer2video_model=... --set prompt_use_type=1 --set prompt_type=... --set script=... [--set parse_mode=3|4]
reelmate episode match-resources --set 'ep_ids=["ep-1","ep-2"]' --set generate_mode=2 --set refer2image_model=... --set image2video_model=... --set prompt_use_type=1 --set prompt_type=... [--set parse_mode=1|2]
reelmate episode save-resource-matches EPISODE_ID --set @episode-resources.json
reelmate episode parse EPISODE_ID [--set character_importance=0] [--set scene_importance=0] [--set prop_importance=0]
reelmate episode parse-retry EPISODE_ID
reelmate episode parse-result EPISODE_ID
```

## 子命令说明

| 命令 | 作用 |
|---|---|
| `reelmate episode list` | 列出剧集 |
| `reelmate episode create` | 创建剧集 |
| `reelmate episode get` | 查询剧集详情 |
| `reelmate episode edit` | 修改剧集名称 |
| `reelmate episode delete` | 删除剧集 |
| `reelmate episode batch-create` | 一次创建多集，结果分 `succeeded` / `failed` / `unconfirmed` |
| `reelmate episode split` | 将剧本项目拆解为分镜 |
| `reelmate episode split-list` | 列出拆解结果 |
| `reelmate episode split-delete` | 删除拆解结果 |
| `reelmate episode prompt-templates` | 查询官方或团队一步流模板目录，拿 `match-resources` 需要的 `prompt_type` 或 `prompt_ukid` |
| `reelmate episode match-resources` | 配置工作流模型并触发资产匹配（单集或批量） |
| `reelmate episode save-resource-matches` | 直接保存本集资产匹配关系，不运行匹配算法 |
| `reelmate episode parse` | 确认主体匹配清单并启动分镜提示词拆解 |
| `reelmate episode parse-retry` | 重试一次已失败的分镜拆解，对应 GUI「分镜脚本拆解失败，请点击重试」 |
| `reelmate episode parse-result` | 查询分镜提示词拆解结果；`status` 1 进行中、2 成功、3 失败 |

## `reelmate episode list`

### 作用

列出剧集。

所有列表命令的分页口径一致：**默认只取第一页**，`--set page=N` 逐页取、`--set page_size=N` 改单页条数、`--set all=true` 按服务端总数一次取完。输出带 `count`（服务端总数）、`page`、`page_size`、`has_more`、`next_page`；`has_more=true` 时不要把这份列表当成全量去做批量操作或判断某条记录不存在。

### 参数与输出

`--workspace WORKSPACE_ID` 指定项目；省略时使用当前绑定。`--json` 输出该页列表与分页状态。单页 20 条，与 Web 剧集列表页一致；响应里的 `count` 是字符串型，CLI 已归一成整数。

默认只列制片工坊剧集，请求带 `creation_mode=1`（`canvas_id=0`），与 Web 工坊 tab 一致。`--set creation_mode=0` 列出全部，`--set creation_mode=2` 只列无限画布剧集。画布工程列表请用 `canvas list`，不要用本命令的默认结果去判断「剧本是否已导入」。

### 示例

```bash
reelmate episode list --workspace WORKSPACE_ID --json
reelmate episode list --workspace WORKSPACE_ID --set creation_mode=0 --json
```

## `reelmate episode create`

### 作用

创建剧集。

### 参数与输出

`--workspace WORKSPACE_ID` 指定项目，`--name NAME` 指定剧集名称。写操作支持 `--dry-run` 与 `--idempotency-key`。

### 示例

```bash
reelmate episode create --workspace WORKSPACE_ID --name demo --json
```

## `reelmate episode get`

### 作用

查询剧集详情。

### 参数与输出

位置参数 `EPISODE_ID` 必填。`--json` 输出完整剧集数据。

### 示例

```bash
reelmate episode get EP_ID --json
```

## `reelmate episode edit`

### 作用

修改剧集名称。

### 参数与输出

位置参数 `EPISODE_ID` 必填，`--name NAME` 指定新名称。写操作支持 `--dry-run` 与 `--idempotency-key`。

### 示例

```bash
reelmate episode edit EP_ID --name demo --json
```

## `reelmate episode delete`

### 作用

删除剧集。会改变远端数据，执行前确认目标。

### 参数与输出

位置参数 `EPISODE_ID` 必填。写操作支持 `--dry-run` 与 `--idempotency-key`。

### 示例

```bash
reelmate episode delete EP_ID --dry-run --json
```

## `reelmate episode batch-create`

### 作用

一次创建多集，结果分 `succeeded` / `failed` / `unconfirmed`。

### 参数与输出

`--set @episodes.json` 顶层使用 `items`，每项为 `{"sort":1,"name":"第1集","s_script_id":"拆集结果ID"}`；兼容旧顶层键 `episodes` 及每项的 `title` / `split_id` 别名，发送前会转换为 GUI 当前接口字段。

`succeeded[]` 只包含服务端逐项确认过的剧集。服务端只回受理凭证（如 `task_id`）而没有逐项结果时，提交项进入 `unconfirmed[]`，`succeeded[]` 为空，并附 `hint`。`unconfirmed` 非空不算失败，退出码仍为 `0`，但必须用 `episode list` 复核后才能当成已创建。

### 示例

```bash
reelmate episode batch-create --set @episodes.json --json
```

## `reelmate episode split`

### 作用

将剧本项目拆解为分镜。

### 参数与输出

位置参数是 `SCRIPT_PROJECT_ID`。`--set file_id=FILE_ID` 来自已上传的剧本文件，或 `--set nt_id=NOVEL_ID` 来自已定稿的小说剧本。

### 示例

```bash
reelmate episode split SCRIPT_PROJECT_ID --set file_id=FILE_ID --json
```

## `reelmate episode split-list`

### 作用

列出拆解结果。

### 参数与输出

位置参数 `SP_ID` 可省略并使用当前绑定。`--json` 输出该页列表与分页状态。

`page` 与 `page_size` 在这个接口上都是必填的，CLI 与 Web 一样传 `page=1`、`page_size=500`。默认只取第一页，`--set page=N` 逐页取、`--set page_size=N` 改单页条数、`--set all=true` 按服务端总数一次取完；输出带 `count`、`page`、`page_size`、`has_more`、`next_page`，`has_more=true` 时不要当成全量用。

### 示例

```bash
reelmate episode split-list SP_ID --json
reelmate episode split-list SP_ID --set all=true --json
```

## `reelmate episode split-delete`

### 作用

删除拆解结果。会改变远端数据，执行前确认目标。

### 参数与输出

`--set 'split_ids=["s-1"]'` 指定要删除的拆解 ID。写操作支持 `--dry-run` 与 `--idempotency-key`。

### 示例

```bash
reelmate episode split-delete SP_ID --set 'split_ids=["s-1"]' --json
```

## `reelmate episode prompt-templates`

### 作用

查询官方分镜、团队「AI拆分镜一步流模版」或团队「AI拆分镜工作流模版」目录。只读命令，不扣费。`--set source=official` 为默认，保持原有 `templates` / `resolved` 输出；`--set source=team-onestep` 与 `--set source=workflow` 各查一份独立团队目录。

`prompt_type` 携带的是这里的模板 **id**，不是「1 = 默认」这类枚举；必须实时查，不可凭记忆填。填错的后果是匹配「受理成功」但解析出 0 条分镜——比直接报错难查得多。

### 参数与输出

以下类型、画幅、模型分组与 `resolved` 规则用于**官方模板**。团队一步流见本节后面的说明。

`--sp-type` 取项目的 `sp_type` 原样传入，接受 `1`（2D/3D 动漫）、`2`（真人）、`3`（海外仿真人）；超出该范围以 `kind=usage` 拒绝。这与 `model list --sp-type` 不是一回事——那个是模型目录的动漫/真人二分类，只认 `1|2`，**海外仿真人项目在 model list 里也是 2，但本命令必须传 3**。

有 `--workspace` 时 `--sp-type` **可省**：命令自己去读项目详情的 `sp_type`，与 Web `ScriptPromptSelect` 的 `sp_type: String(currentSeriesDetail.sp_type ?? 1)` 同一来源。传了则必须与项目一致，否则以 `kind=usage` 拒绝、不发目录请求——把 model list 的 `2` 传给海外项目会列出国内「天幕分镜大师1.3」，匹配能受理但拆分镜解析出 0 条。

`--set ratio=16:9|9:16`（也接受 `1`/`2`）**可省**：不传时命令自己去读生效项目的 `ratio` 并换算，与 Web 恒传 `ratio === '16:9' ? '1' : '2'` 得到同一个值。传了则以传入值为准，不会被项目画幅覆盖（同一项目下按另一画幅取模板是合法用法）。

`ratio` 本身仍是恒发参数，不能真的缺：服务端缺 `ratio` 时按自己的默认口径返回另一套模板，而模板 id 跨组无效，拿错的表现是「匹配受理成功、解析出 0 条分镜」而不是报错。所以自动读失败时（项目详情请求失败、没回 `ratio` 字段、回了 `16:9`/`9:16` 之外的写法）命令以 `kind=usage` 加 `raw.needs_input=true` 追问、不发模板目录请求（`needs_input` 是 `raw` 里的判别位，不是 `kind` 的取值），补一个 `--set ratio=` 即可继续。`--sp-type` 读不到项目值时同样追问，补 `--sp-type 1|2|3`。

HITL 只展示 `--set model=` 后 `resolved.candidates[]` 的 `name`，禁止把整张 `templates` 表或其它剧目类型的模板列给用户。

响应 `templates` 按模型标识分组。分组随模型上线增减，**不要按固定分组名解析**；线上当前包含 `normal`、`seedance_1.6`、`seedance_2.5`、`seedance_overseas_2.0`、`seedance_overseas_2.5`、`vidu_q2`、`wan_3.0` 等。

带 `--set model=MODEL_MARK` 时额外返回 `resolved`，按 Web 的规则替你选好分组与默认项：分组名即模型标识，**该分组缺失或为空则退回 `normal`**（线上 `vidu_q2` 分组就是空的），默认项取 `default=true`，没有则取首项。

| `resolved` 字段 | 含义 |
|---|---|
| `group` | 实际生效的分组名 |
| `fallback_to_normal` | 是否因该模型分组为空而退回 `normal` |
| `default_prompt_type` | 可直接用作 `prompt_type` 的模板 id |
| `candidates[]` | 该分组下全部模板 |

团队一步流使用当前账号与团队作用域，通过 `POST /web/v1/df/user_knowledge/list` 查询。与 Web 相同，请求固定 `scene=5`、`status=1`、`use_type=2`，`sp_type=[0,项目真实 sp_type]`，`lang` 默认 `zh-CN`，可通过 `--set lang=`指定 Web 当前界面的完整语言码。必须能读到项目真实类型；海外项目保留 `3`。不读取画幅，也不按 `model` 筛选，不套用官方 `normal` 分组或默认模板规则。

默认第 1 页、每页 10 条；支持 `page`、`page_size`（最大 100）、`all=true`。Skill 确认前必须取全目录，不能把第一页当成全部。响应含 `source=team-onestep`、`prompt_use_type=2`、`list[]` 及标准分页字段；每项保留字符串 `uk_id`、`name`（缺名回退 `desc`）、`desc`（若有）、`status`、`language_model`，不展开完整 `prompt_template`。同名项不得去重，用序号及描述/语言模型消歧，内部保留序号到 `uk_id` 的映射。

空目录明确表示当前项目和语言下没有可用团队一步流模板；接口失败保留原错误。不得静默退回官方。

AI拆分镜工作流模版使用当前账号与团队作用域，通过 `GET /web/v1/asset/workflows` 查询。不传模型、画幅、语言或 `sp_type`。接口会返回禁用项，CLI 只保留 `status=1`（缺 `status` 视为启用）。默认第 1 页、每页 20 条；支持 `page`、`page_size`（最大 200）、`all=true`。Skill 确认前必须取全目录。响应含 `source=workflow`、`prompt_use_type=3`、`list[]` 及标准分页字段；每项保留字符串 `workflow_id`、`name`、`description`、`status`、`total_points`，不展开节点编排。同名项不得去重，用序号及描述消歧，内部保留序号到 `workflow_id` 的映射。空目录表示当前团队没有可用工作流模版；接口失败保留原错误，不得静默退回一步流或官方。`total_points` 只供展示，不能当作拆分镜计价模板 ID。

### 示例

```bash
reelmate episode prompt-templates --workspace SP_ID --set model=vidu_q2 --json
reelmate episode prompt-templates --workspace SP_ID --sp-type 3 --set ratio=9:16 --set model=Seedance 2.5 --json
reelmate episode prompt-templates --workspace SP_ID --set source=team-onestep --set lang=zh-CN --set all=true --json
reelmate episode prompt-templates --workspace SP_ID --set source=workflow --set all=true --json
```

## `reelmate episode match-resources`

### 作用

GUI 环节 4 的资产匹配从这里下单。批量分支对应前端 `episode/batch/resources` 接口，是**资产匹配 + 自动拆分镜**的组合任务：服务端在每集资产匹配完成后自动继续分镜提示词拆解，Web 没有资产匹配确认环节，不需要再逐集调用 `episode parse`。提交即会先后产生「资产匹配」和「拆解分镜脚本」两笔扣费，拆分镜费率约为资产匹配的 16 倍，提交前必须一并展示两笔账单。这不是资产确认页的主形态批量生图入口；环节 3 生图使用 `resource batch-draft-generate`。新版 GUI 工作流必须传 `ep_ids` 使用批量接口做匹配。写操作先 `--dry-run`。

### 参数与输出

单集给 `EP_ID` 位置参数时仍保留旧的 `POST episode/:ep_id/resources`；批量给 `--set ep_ids=[...]`，走 `POST /web/v1/df/episode/batch/resources`。GUI 四环节工作流只使用后者做资产匹配。

批量接口成功时返回匹配任务 `task_id`，CLI 将其提升到输出 `data.task_id`。但该 ID 当前不能由通用 `task get/wait` 稳定查询：实测 `task get` 返回 `740015 not found data`，`task wait` 持续显示 `unknown 0%`。应改为逐集轮询 `episode match-result EP_ID`，以 `data.status=2` 确认资产匹配成功；再逐集轮询 `parse-result` 等待自动拆分镜结束。只有匹配已成功、`episode get` 的 `is_any_parse=false` 且 `parse-result` 仍为 `status=0`、间隔复查后仍如此时，才补调一次 `episode parse`。`match-resources` 请求受理成功只代表任务已创建，不代表资产匹配或分镜拆解完成。

（曾经文档里写的「更新已有配置用 `--set update=true` 走 `PUT episode/:ep_id/resources`」是错的：该 `PUT` 对应 GUI 的 `putSaveMaterialData`，只接受 `resources{characters,scenes,props}`，发模型参数会被判 `740011`。直接写匹配关系请使用 `episode save-resource-matches`。）

三个模型字段语义不同，**不要合并成一个 `model` 参数**。模型标识必须来自与项目类型匹配的 `reelmate model list --sp-type ... --json`，**不可凭记忆填**，CLI 也不会硬编码默认模型。

#### `sp_type` 必须先读出来，再选模型和模板

`sp_type` 不是可以按项目名猜的东西（「红楼梦」并不等于仿真人剧）。先读：

```bash
reelmate workspace info --workspace SP_ID --json   # 取 data.sp_type 与 data.ratio
```

官方 `prompt-templates` 使用项目真实 `sp_type=1|2|3`，有 `--workspace` 时自动读取，显式 `--sp-type` 必须与项目一致；`model list` 使用动漫/真人二分类，项目为 `3` 时模型目录传 `2`。不同项目类型的官方模板 ID 不互通；把另一类型的模板配给当前项目，服务端可能受理后在 `parse-result` 中以 `status=3`、`single_script_parse_task_id=null`、`expect_consum_points=0` 失败。团队一步流则按 `[0,项目真实 sp_type]` 查当前团队启用目录，不能用官方 ID。

模型侧还有 `need_vip`。模型和模板必须**同属项目的 `sp_type`，且账号的 VIP 权益覆盖该模型**，否则两种错法各有一种失败形态：

| 错法 | 表现 |
|---|---|
| 模板 id 取自别的 `sp_type` 空间 | `parse` 返回 200 且有 `et_id`，但 `parse-result` 恒为 `status=3`、无 task、`expect_consum_points=0` |
| 模型 `need_vip=true` 而账号无权益 | `parse` 直接 400 `740019 call other service api err`，连 `et_id` 都没有 |

`740019` 是下游调用失败后的笼统码，不含具体原因；剧集状态会先到 `operate=4`，失败后回落到 `operate=3` 并置 `if_next_operate_fail=true`。两种失败都不扣费，但都要新建剧集才能重试。

| 字段 | 含义 |
|---|---|
| `refer2video_model` | 参考生视频模型 |
| `refer2image_model` | 参考生图模型 |
| `image2video_model` | 图生视频模型 |
| `generate_mode` | 1 = 参考生视频，2 = 图生视频 |
| `parse_mode` | 可选；参考生视频智能模式不传，宫格传 3，专业传 4；图生视频脚本传 1、直出传 2 |

`generate_mode=1` 只要求 `refer2video_model`；`generate_mode=2` 要求 `refer2image_model` 和 `image2video_model`。所需模型字段缺失时走 `needs_input`，`missing[].desc` 会提示用 `reelmate model list` 查当前可见模型。参数原样透传，CLI 不自行取默认。

除模型外还有两组必填项，**服务端不校验，缺了照样受理，但解析会静默出 0 条分镜**，所以 CLI 在下单前就要求齐：

| 字段 | 含义 |
|---|---|
| `prompt_use_type` | 提示词来源：1 = 官方模板（配 `prompt_type`），2 = 团队 AI 拆分镜一步流（配 `prompt_ukid=uk_id`），3 = AI拆分镜工作流模版（配 `prompt_ukid=workflow_id`） |
| `prompt_type` | 官方模板展示名或 id。展示名按 Web `ScriptPromptSelect` 当前模型分组（空则 `normal`）解析成 id 再提交；宫格/分镜单模式传 `0` |
| `prompt_ukid` | 团队模板 ID，必须来自所选来源的目录；一步流使用字符串 `uk_id`，工作流模版使用字符串 `workflow_id`。命令写 `--set 'prompt_ukid="ID"'` 防止长数字精度丢失 |
| `script` | 剧集原文；国内真人项目（`sp_type=2`）≤ 5000 字符，海外真人项目（`sp_type=3`）≤ 8000 字符；取自 `episode get EP_ID --json` 的 `ep_content`（仅单集分支必填） |

`prompt_type` 发给服务端的是模板 id，不是「1 = 默认」这类枚举——yapi 上的旧注释会把人带偏，实测传 `1` 被判 `740011`。Web 给人看模板 `name`，提交时发 `item.id`。CLI 的 `--set prompt_type=` 同时接受展示名和数字 id；展示名会按**当前项目 sp_type** 下该模型分组解析成 id，解析不到则拒绝提交，不会把名称原样 POST。

团队一步流和 AI拆分镜工作流模版都只用于 `generate_mode=1`。预演与正式提交都会重新查询完整启用目录：一步流按当前项目、团队和 `lang`，工作流模版按当前团队且不看项目类型。ID 不存在或已禁用时拒绝提交；不要把模板名称交给 `prompt_ukid`。官方来源禁止混入 `prompt_ukid`，团队来源禁止混入 `prompt_type`；若传 `source`，必须与 `prompt_use_type` 一致（`official` / `team-onestep` / `workflow`）。`lang` 默认 `zh-CN`，只作用于一步流，须与选择时一致。`source`、`lang`、分页及展示字段仅供本地校验，不发给资产匹配接口。团队预演显示 `prompt_source` 和实际查询到的 `prompt_name`。

一步流和工作流模版同样由组合任务自动拆分镜。提交前取不到可验证的拆分镜计价模板 ID，拆分镜账单标不可预估并说明原因，不能用团队 `uk_id`、`workflow_id` 或工作流 `total_points` 代替；官方来源的计价模板 ID 就是所选 `prompt_type`，匹配后 `episode get` 回读的 `prompt_tpl_id` 与之相同。

`script` 是单集接口真正参与匹配的正文；不传等于让服务端拿空文本匹配，表现为 `expect_consum_points=0`、`success_num=0`，既不报错也没结果。注意匹配时传入的 `script` 会覆盖 `ep_content`。Web 端在剧本输入框本地写死了同一组限制：国内真人项目固定 5000，海外真人项目固定 8000，超限时“下一步，匹配本集资产”会禁用。

上述 5000/8000 是 Web 输入框和旧版单集接口的 `script` 参数限制。CLI 在单集正文超过 5000 字时会读取项目详情中的权威 `sp_type`，只有 `sp_type=3` 才放宽到 8000。批量接口不接收 `script`，只接收 `ep_ids`，服务端自行读取剧集记录中的 `ep_content`；因此批量分支不套用这个客户端参数限制。线上以 7812 字国内真人剧集实测，批量匹配最终返回 `status=2`，且回读 `ep_content` 仍为完整 7812 字，说明该限制不能外推到批量接口。

`ep_id` 只走路径，CLI 不会把它放进 JSON body（放进去服务端判 `740011` 且 `msg` 里没有字段线索）；即使显式 `--set ep_id=...` 也会被剔除。

只有旧服务返回逐项结果而没有 `task_id` 时，CLI 才按兼容逻辑输出 `succeeded[]` / `failed[]` / `unconfirmed[]`。新版匹配任务响应不得按逐集结果解释。

### 示例

GUI 四环节流程应一次把 `episode list` 返回的全部正式剧集 ID 放入 `ep_ids` 提交资产匹配。组合任务会自动拆分镜；对每个 `EP_ID` 查 `match-result` 和 `parse-result` 确认结果，不得只处理第一集。

团队一步流预演（`TEAM_UK_ID` 替换为当次目录返回的字符串 ID）。工作流模版把来源换成 `--set prompt_use_type=3 --set 'prompt_ukid="WORKFLOW_ID"'`，去掉 `lang`：

```bash
reelmate episode match-resources --workspace SP_ID --set 'ep_ids=["EP-1"]' \
  --set generate_mode=1 --set refer2video_model='Seedance 2.0 VIP' \
  --set prompt_use_type=2 --set 'prompt_ukid="TEAM_UK_ID"' \
  --set lang=zh-CN --dry-run --json
```

官方模板流程：

```bash
# 1. 读项目类型，后面的 --sp-type 都由它推出，不要猜
reelmate workspace info --workspace SP_ID --json          # 取 data.sp_type，设为 $SPT
# 2. 查该分类下可见且 need_vip 与账号权益相符的模型。
#    注意 model list 的 --sp-type 只认动漫/真人二分类 1|2，不能把 $SPT 原样传：
#    $SPT=1 用 --sp-type 1；$SPT=2 或 3 用 --sp-type 2。
reelmate model list video --sp-type 1|2 --json             # 看 name / need_vip / supported_modes
# 3. 查模板：有 --workspace 时不要传 --sp-type。Web 用项目 sp_type；
#    海外仿真人是 3，把上一步 model list 的 2 传进来会列出国内 1.3。
reelmate episode prompt-templates --workspace SP_ID --set model=MODEL_B --json
# 4. 批量预演、提交并等待组合任务
reelmate episode match-resources --set 'ep_ids=["EP-1","EP-2"]' \
  --set refer2video_model=MODEL_B --set generate_mode=1 \
  --set prompt_use_type=1 --set prompt_type=PROMPT_TYPE --dry-run --json
reelmate episode match-resources --set 'ep_ids=["EP-1","EP-2"]' \
  --set refer2video_model=MODEL_B --set generate_mode=1 \
  --set prompt_use_type=1 --set prompt_type=PROMPT_TYPE \
  --idempotency-key KEY --json
reelmate episode match-result EP-1 --json   # 逐集轮询至 data.status=2
reelmate episode match-result EP-2 --json
reelmate episode parse-result EP-1 --json   # 自动拆分镜，逐集轮询至终态
reelmate episode parse-result EP-2 --json
```

## `reelmate episode save-resource-matches`

### 作用

把本集当前资产清单直接写入匹配关系接口 `PUT /web/v1/df/episode/:ep_id/resources`。本命令不运行资产匹配算法，不调用 `resource match-reset`，也不接受模型、模板或剧本文本参数。适用于把新生成并定稿的资产确定性替换到原未匹配占位项。

### 参数与输出

位置参数 `EPISODE_ID` 必填。`--set` 必须提供 `resources.characters`、`resources.scenes`、`resources.props` 三个数组，空类别也要显式传 `[]`。该接口按完整快照保存，因此应先用 `episode match-result` 读取最新清单，只替换目标项并原样保留全部非目标项；不得提交只包含新增资产的局部数组。请求体只发送 `resources`，不会把 `sp_id`、模型字段或 `update` 发给接口。

写操作支持 `--dry-run` 与 `--idempotency-key`。提交后再次调用 `episode match-result`，确认目标项已是 `status=2`，且 `resource_id/file_id` 与刚定稿的资产一致。

### 示例

```bash
reelmate episode save-resource-matches EP_ID --workspace SP_ID \
  --set @episode-resources.json --dry-run --json
reelmate episode save-resource-matches EP_ID --workspace SP_ID \
  --set @episode-resources.json --idempotency-key SAVE_KEY --json
```

## `reelmate episode parse`

### 作用

确认主体匹配清单并启动分镜提示词拆解。GUI 四环节工作流的批量 `match-resources` 是组合任务，会在匹配完成后自动拆分镜，**正常路径不调用本命令**。本命令只用于组合任务没有带起拆分镜时的补调：该集 `match-result` 为 `status=2`、`episode get` 的 `is_any_parse=false`、`parse-result` 仍为 `status=0`，且间隔复查后仍如此。`is_any_parse=true` 或 `parse-result` 为 `status=1`/`2` 时禁止调用，否则会重复下单扣费。补调不传三个 importance 字段。

### 参数与输出

位置参数 `EPISODE_ID` 必填。可选 `--set character_importance=0`、`--set scene_importance=0`、`--set prop_importance=0`。写操作支持 `--dry-run` 与 `--idempotency-key`。

成功时返回 `data.et_id`，之后用 `episode parse-result EPISODE_ID --json` 轮询：`status` 1 进行中、2 成功、3 失败。`status=2` 但 `list` 为空或 `null` 是静默失败的信号（常见原因是 `match-resources` 选的模型 + 模板组合在后端不兼容，且接口和前端都不会提前校验或警告），只能新建一集换配置重来。成功时 `success_num` 可能为 0、`episode get` 的 `split_task_id` 可能为 `"0"`，二者都不作为失败判据。`parse-result.list[]` 拿到的是分镜**草稿**（字段 `esd_id`），还不是正式分镜 `sd_id`；`storyboard get`/`storyboard list` 此时查到的内容字段（`desc`/`storyboard_description`）是空的，要看真实内容须用 `storyboard link-draft`。

### 示例

```bash
reelmate episode parse EP_ID --dry-run --json
```

## `reelmate episode parse-retry`

### 作用

重试一集已经失败的分镜拆解，对应 GUI 报「分镜脚本拆解失败，请点击重试」时那颗按钮，走 `POST episode/:ep_id/parse-retry`。

它和 `parse` 是两个端点，不能互相替代：`parse` 用于首次下单，剧集一旦被置 `if_next_operate_fail=true`，重复 `POST parse` 只会拿回同一个错误。这是花钱的写操作。

### 参数与输出

位置参数 `EPISODE_ID` 必填，`sp_id` 由 CLI 从生效工作区补齐。返回 `et_id`，之后仍用 `episode parse-result` 轮询。支持 `--dry-run` 与 `--idempotency-key`。

**返回 `740015 not found data` 说明服务端没有可重试的任务**，不是命令用错了；常见原因是模型或模板配错（见 `match-resources` 的 `sp_type` 对齐规则），重试无从下手，GUI 上点那颗按钮同样没有反应。这种剧集只能新建一集、用正确配置重走匹配。`split_task_id` 在拆分镜成功时也可能为 `"0"`，不能用它判断有无可重试任务。

### 示例

```bash
reelmate episode parse-retry EP_ID --dry-run --json
reelmate episode parse-retry EP_ID --json
reelmate episode parse-result EP_ID --json
```

## `reelmate episode parse-result`

### 作用

查询分镜提示词拆解结果。`status` 1 进行中、2 成功、3 失败。

### 参数与输出

位置参数 `EPISODE_ID` 必填。`--json` 输出完整结果。

### 示例

```bash
reelmate episode parse-result EP_ID --json
```

## 注意事项

- `FILE_ID` 来自已上传的剧本文件，`NOVEL_ID` 来自已定稿的小说剧本。
- `batch-create` 的 `@episodes.json` 顶层使用 `items`，每项为 `{"sort":1,"name":"第1集","s_script_id":"拆集结果ID"}`；兼容旧顶层键 `episodes` 及每项的 `title` / `split_id` 别名，发送前会转换为 GUI 当前接口字段。
- 所有写子命令都支持 `--dry-run` 与 `--idempotency-key`。
- 选模型和模板前先用 `workspace info --workspace SP_ID --json` 读 `sp_type`，不要按项目名推断；`prompt-templates` 与 `model list` 的 id 空间按 `sp_type` 隔离，`--sp-type` 必须传。两者的 `--sp-type` 口径不同：`prompt-templates` 原样接受项目的 `1|2|3`，`model list` 只认动漫/真人二分类 `1|2`（`sp_type=2|3` 都映射成 `2`），把 `3` 原样传给 `model list` 会被以 `kind=usage` 拒绝。
- GUI 四环节使用批量 `match-resources` 提交全部剧集的资产匹配 + 自动拆分镜组合任务；逐集查询 `match-result` 与 `parse-result`，不逐集调用 `episode parse`，仅在组合任务未带起拆分镜时按 `episode parse` 小节的条件补调一次。缺失资产补充在拆分镜之后按需进行。
- 发布态以当前二进制帮助、本命令页和结构化错误为执行依据；文档未登记的字段不得猜测。
- 删除、拆解和 `match-resources` 会改变远端数据并可能扣费，执行前确认目标。
