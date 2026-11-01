# storyboard

管理剧集分镜条目。**分镜（storyboard）不是分镜素材（storyboard_info）**：本命令只做分镜本体，素材挂载走 `material`。

## 按场景选子命令

| 场景 | 子命令链 | 流程文档 |
|---|---|---|
| 正式分镜 CRUD / 序号 | `list`、`get`、`add`、`edit`、`delete`、`batch-delete`、`num-update`、`ext`、`total-list` | [gui-script-video-storyboard.md](../manual/workflow/gui-script-video-storyboard.md)（环节 4） |
| Excel 回填并批量生视频 | `prompt-template` → `sheet-read` → `draft-import` → `match-assets` → `draft-batch-update` → `batch-generate` | [gui-backfill-shot-video.md](../manual/workflow/gui-backfill-shot-video.md) |
| 草稿维护 | `link-draft`、`draft-delete`、`draft-batch-update` | 本篇对应小节 |
| 首帧清单批量生视频 | `batch-generate-video` | 环节 4 特殊路径 |

## 用法

```text
reelmate storyboard list EPISODE_ID
reelmate storyboard get EPISODE_ID STORYBOARD_ID
reelmate storyboard add EPISODE_ID [--name CONTENT] [--set num=1] [--set desc=CONTENT]
reelmate storyboard edit EPISODE_ID STORYBOARD_ID [--name CONTENT] [--set desc=CONTENT] [--set cancel_link_draft=true]
reelmate storyboard delete EPISODE_ID STORYBOARD_ID
reelmate storyboard batch-delete EPISODE_ID --set 'storyboard_ids=["SB_ID_1","SB_ID_2"]'
reelmate storyboard num-update EPISODE_ID --set @nums.json
reelmate storyboard link-draft EPISODE_ID STORYBOARD_ID
reelmate storyboard ext EPISODE_ID STORYBOARD_ID --set duration=5
reelmate storyboard total-list EPISODE_ID
reelmate storyboard batch-add EPISODE_ID --set @shots.json
reelmate storyboard prompt-template OUTPUT.xlsx
reelmate storyboard sheet-read SHOTS.xlsx --set sheet=SHEET_NAME
reelmate storyboard draft-import EPISODE_ID --workspace SP_ID --set file=SHOTS.xlsx --set episode_no=1 --set duration=5
reelmate storyboard draft-batch-update EPISODE_ID --set 'items=[{"esd_id":"ESD_ID","duration":5}]'
reelmate storyboard match-assets EPISODE_ID --workspace SP_ID [--set nums=[...]] [--dry-run] [--timeout 30m] [--idempotency-key KEY]
reelmate storyboard batch-generate EPISODE_ID --set ai_model_mark=MODEL --set generate_type=1 --set ratio=16:9 --set resolution=1080p --set 'nums=[1]'
reelmate storyboard batch-generate-video EPISODE_ID --set ai_model_mark=MODEL --set ratio=16:9 --set resolution=1080p --set 'items=[{"sd_id":"SD_ID","file_id":"FILE_ID"}]'
```

## 子命令说明

| 命令 | 作用 |
|---|---|
| `reelmate storyboard list` | 列出剧集分镜 |
| `reelmate storyboard get` | 查询单个分镜详情 |
| `reelmate storyboard add` | 新增分镜 |
| `reelmate storyboard edit` | 修改分镜内容 |
| `reelmate storyboard delete` | 删除单个分镜；单条删除也走前端批量删除接口 |
| `reelmate storyboard batch-delete` | 使用明确的 ID 清单一次删除多个正式分镜 |
| `reelmate storyboard num-update` | 批量调整分镜序号（整组操作，不要逐条改） |
| `reelmate storyboard link-draft` | 查询正式分镜关联的草稿 |
| `reelmate storyboard ext` | 批量更新正式分镜扩展字段 |
| `reelmate storyboard total-list` | 查询前端使用的剧集分镜聚合列表 |
| `reelmate storyboard batch-add` | 按清单批量创建正式空白分镜 |
| `reelmate storyboard prompt-template` | 用 CLI Go 代码实时生成三列分镜提示词 `.xlsx` 空表 |
| `reelmate storyboard sheet-read` | 读取并校验 Excel 类分镜表 |
| `reelmate storyboard draft-import` | 从 Excel 分镜表批量新增或更新分镜草稿 |
| `reelmate storyboard draft-delete` | 删除明确指定的分镜草稿 |
| `reelmate storyboard draft-batch-update` | 更新明确指定的分镜草稿字段（如时长） |
| `reelmate storyboard match-assets` | 在回填完成后按 GUI 匹配资产顺序打标，为批量生视频准备参考图 |
| `reelmate storyboard batch-generate` | 只为明确选中的分镜编号批量生成参考视频/图片 |
| `reelmate storyboard batch-generate-video` | 使用首帧清单为一集内多条分镜批量生成视频 |

## `reelmate storyboard list`

### 作用

列出剧集分镜。**只返回骨架字段（`storyboard_id`/`num`/`status`/`created_at` 等），`desc`/`storyboard_description` 恒为空字符串**，不能据此判断分镜是否已有提示词、参考图或首帧——这些真实内容要用 `storyboard link-draft` 才能读到。

### 参数与输出

位置参数 `EPISODE_ID` 必填。`--json` 输出该页列表与分页状态。接口单页默认 20 条，CLI 与 Web 一样取 200 条并报服务端总数；所有列表命令的分页口径一致：**默认只取第一页**，`--set page=N` 逐页取、`--set page_size=N` 改单页条数、`--set all=true` 按服务端总数一次取完。输出带 `count`（服务端总数）、`page`、`page_size`、`has_more`、`next_page`；`has_more=true` 时不要把这份列表当成全量去做批量操作或判断某条记录不存在。

### 示例

```bash
reelmate storyboard list EPISODE_ID --json
```

## `reelmate storyboard get`

### 作用

查询单个分镜详情。**和 `storyboard list` 同样只有骨架字段，`desc`/`storyboard_description` 也是空的**，不要用它判断分镜内容是否已生成。

### 参数与输出

位置参数 `EPISODE_ID STORYBOARD_ID`。`--json` 输出完整分镜数据（骨架层面）；需要 `video_gen_prompt`/`images`/`metadata`（含首帧 `file_id`）等真实内容时改用 `storyboard link-draft EPISODE_ID STORYBOARD_ID --json`。

### 示例

```bash
reelmate storyboard get EPISODE_ID STORYBOARD_ID --json
```

## `reelmate storyboard add`

### 作用

新增分镜。

### 参数与输出

`--set num=` 指定序号，缺省为 `1`；`--name CONTENT` 写分镜名称 `name`，`--set desc=CONTENT` 写分镜描述 `desc`。
`name` 与 `desc` 是两个不同字段，可同时给。写操作支持 `--dry-run` 与 `--idempotency-key`。

### 示例

```bash
reelmate storyboard add EPISODE_ID --name '开场远景' --set num=1 --json
reelmate storyboard add EPISODE_ID --set num=1 --set desc=PROMPT --json
```

## `reelmate storyboard edit`

### 作用

修改分镜内容。

### 参数与输出

位置参数 `EPISODE_ID STORYBOARD_ID`。三个可写字段互不替代，至少给一个，否则返回 `kind=usage`：

| 入参 | 写入字段 | 用途 |
|---|---|---|
| `--name CONTENT` | `name` | 分镜名称 |
| `--set desc=CONTENT` | `desc` | 分镜描述，GUI 分镜卡片显示的正文 |
| `--set cancel_link_draft=true` | `cancel_link_draft` | 解除与生成草稿的关联 |

`--name` 和 `--set desc=` 是两个不同字段，不是同一件事的两种写法：回填提示词要写 `desc`，
只改标题才用 `--name`。写操作支持 `--dry-run` 与 `--idempotency-key`。

### 示例

```bash
reelmate storyboard edit EPISODE_ID STORYBOARD_ID --name CONTENT --json
reelmate storyboard edit EPISODE_ID STORYBOARD_ID --set desc=PROMPT --dry-run --json
```

## `reelmate storyboard delete`

### 作用

删除单个分镜；单条删除也走前端批量删除接口。

### 参数与输出

位置参数 `EPISODE_ID STORYBOARD_ID`。写操作支持 `--dry-run` 与 `--idempotency-key`。

### 示例

```bash
reelmate storyboard delete EPISODE_ID STORYBOARD_ID --json
```

## `reelmate storyboard batch-delete`

### 作用

使用明确的 ID 清单一次删除多个正式分镜。对应前端原生批量接口 `POST /web/v1/df/episode/:ep_id/storyboard/delete`，请求体只发送 `storyboard_ids`；路径参数 `ep_id` 不重复放入 JSON。ID 清单必须非空，执行前先核对 dry-run 的 `count` 和逐条 ID。

### 参数与输出

`--set 'storyboard_ids=["SB_ID_1","SB_ID_2"]'` 指定要删除的分镜。写操作支持 `--dry-run` 与 `--idempotency-key`。

### 示例

```bash
reelmate storyboard batch-delete EP_ID \
  --set 'storyboard_ids=["SB_ID_3","SB_ID_4"]' --dry-run --json
```

## `reelmate storyboard num-update`

### 作用

批量调整分镜序号。这是整组操作，不要逐条改。

### 参数与输出

`--set @nums.json` 传入序号清单。写操作支持 `--dry-run` 与 `--idempotency-key`。

### 示例

```bash
reelmate storyboard num-update EPISODE_ID --set @nums.json --json
```

## `reelmate storyboard link-draft`

### 作用

查询正式分镜当前关联的草稿。对应前端只读接口 `GET /web/v1/df/episode/{ep_id}/storyboard/{storyboard_id}/link-draft`。**这是读取分镜真实内容（`video_gen_prompt`/`image_gen_prompt`/`images[]`/`metadata`，含首帧 `file_id`）的正确入口**——`storyboard list`/`storyboard get` 只返回骨架字段，不含 `images[]`、`metadata` 和首帧，不要用它们判断分镜是否已经有内容。其中 `storyboard_description` 在列表里恒为空（即使已通过 `storyboard ext` 写入），而 `desc` 在 `storyboard edit` 写过之后列表里是有值的，只能用来确认“写过描述”，不能用来确认参考图或生成参数。

### 参数与输出

位置参数 `EPISODE_ID STORYBOARD_ID`。这是读操作，不接收 `draft_id`。

### 示例

```bash
reelmate storyboard link-draft EPISODE_ID STORYBOARD_ID --json
```

## `reelmate storyboard ext`

### 作用

批量更新正式分镜的描述、图片提示词、视频提示词、时长或首帧文件。对应前端 `PUT /web/v1/df/episode/{ep_id}/storyboard/storyboard-ext`。

### 参数与输出

单条更新可把 `STORYBOARD_ID` 作为第二个位置参数；批量更新使用 `--set items=[...]`。每项必填 `storyboard_id`，并至少提供 `storyboard_description`、`image_gen_prompt`、`video_gen_prompt`、`duration`、`first_frame_file_id` 之一。别名 `desc`、`image_prompt`、`video_prompt`、`prompt` 和 `file_id` 会转换为前端字段。

### 示例

```bash
reelmate storyboard ext EPISODE_ID STORYBOARD_ID --set duration=5 --dry-run --json
reelmate storyboard ext EPISODE_ID \
  --set 'items=[{"storyboard_id":"SB_ID","video_gen_prompt":"提示词","duration":5}]' --json
```

## `reelmate storyboard total-list`

### 作用

查询前端使用的剧集分镜聚合列表。对应 `GET /web/v1/df/episode/storyboard-total-list?ep_id=...`；该响应可能按服务端业务状态过滤，不等同于 `storyboard list` 的全部正式分镜，不能单独作为生成完成判据。

### 参数与输出

位置参数是 `EP_ID`，不是 `SP_ID`。默认只发送前端必需的 `page=1`；需要覆盖服务端分页大小时显式传 `--set page_size=`。

### 示例

```bash
reelmate storyboard total-list EP_ID --json
```

## `reelmate storyboard batch-add`

### 作用

按清单批量创建正式空白分镜。入参是分镜行数组（`--set @shots.json` 或 `--set shots=[...]`）。该接口只接受 `num`、可选 `name` 和可选 `desc`，不能用于回填提示词、资产引用或时长。

最小必填字段与代码里的 `studio.ShotRequiredFields` 同一份：

| 字段 | 含义 |
|---|---|
| `num` | 分镜序号 |
| `name` | 可选分镜名称 |
| `desc` | 可选分镜描述 |

缺 `num` 时走 `needs_input`，`missing[].desc` 带行号。出现 `prompt`、`refs`、`duration`、`video_prompt` 或 `images` 时 CLI 主动拒绝并引导到 `draft-import`，避免服务端静默忽略字段。结果分 `succeeded[]` / `failed[]`，`succeeded` 带回服务端分配的 `storyboard_id`。

### 参数与输出

`--set @shots.json` 或 `--set shots=[...]`。写操作支持 `--dry-run` 与 `--idempotency-key`。

### 示例

```bash
reelmate storyboard batch-add EP_ID --set @shots.json --json
reelmate storyboard batch-add EP_ID --set @shots.json --dry-run --json
```

## `reelmate storyboard prompt-template`

### 作用

在命令执行时由 Go 代码生成三列分镜提示词 `.xlsx`。命令离线运行，不要求登录、项目或网络；Skill、源码资源目录和构建产物均不携带静态模板文件。

模板包含「分镜提示词清单」与「填写示例」两个 Sheet。填写 Sheet 提供 100 个空白数据行。`sheet-read` / `draft-import` 默认跳过填写示例。

### 参数与输出

位置参数 `OUTPUT.xlsx` 是目标文件。默认拒绝覆盖已有文件；用户明确要求替换时传 `--set overwrite=true`。`--dry-run` 只返回目标路径和模板元数据，不写文件。

`--json` 的 `data.path` 是生成文件的绝对路径，`data.sheets` 是 Sheet 列表，`data.rows` 是空白填写行数。

```bash
reelmate storyboard prompt-template /absolute/path/shots.xlsx --json
```

## `reelmate storyboard sheet-read`

### 作用

只读解析官方分镜提示词表，输出分集映射、规范化行和行数，不登录、不访问网络。支持 `.xlsx`、`.xlsm`；旧版 `.xls` 需要另存为 `.xlsx`。

需要空表时先 `storyboard prompt-template`。用户回传的是自带分镜清单、本命令报缺少必填列时，由 Agent 按 [_backfill-contract.md](../manual/workflow/_backfill-contract.md) 转写入 `prompt-template` 生成的官方表后再调用本命令。不要让用户重填空模板。转写步骤见 [gui-backfill-shot-video.md](../manual/workflow/gui-backfill-shot-video.md)。本命令不改表。不要提供剧厂十列表格样式模板或 Skill 内本地模板路径。

### 表格列

官方表头为 `剧集号`、`分镜号`、`视频提示词`。用户表可另含 `时长` 列（非官方模板表头，`sheet-read` 仍识别）。单表可包含多集；`剧集号` 决定 `episode_no`，`分镜号` 接受 `1`/`2`/`3`、`01`/`02`/`03` 或 `1-01`。`视频提示词` 原样读出；时长优先读 `时长` 列，否则从提示词自然表述解析；参考资产仅从提示词解析或正文匹配。提示词正文无格式要求。同一集内镜号重复、缺列或单元格非法时退出非 0。十列旧表、景别/摄法变体以及 `.csv` / `.tsv` 不兼容。

默认解析所有非空业务 Sheet，跳过「填写示例」；`data.episodes[]` 返回 `episode_no`、`name`、`sheet` 和行数。`--set sheet=` 仅用于缩小到一个 Sheet（含显式读取填写示例）。

### 示例

```bash
reelmate storyboard sheet-read /absolute/path/shots.xlsx --json
reelmate storyboard sheet-read /absolute/path/shots.xlsx --set sheet=分镜清单 --json
```

## `reelmate storyboard draft-import`

### 作用

从官方三列分镜提示词表按分集批量新增或更新前端分镜草稿。命令先读取项目正式资产和 `episode parse-result`：

- 显式参考资产名单（如 `【参考资产】`、`参考资产：`）精确匹配已定稿且有 `file_id` 的资产；无显式名单时从整段提示词匹配出现的资产名；
- 资产按表格顺序转换为草稿 `images`，提示词中的名称转换为 `[[@imgN]]`；
- 提示词匹配不上已定稿资产时，仍写入原样提示词和空 `images`，留给后续 `match-assets`；
- 按 `shot_no` 找到已有 `esd_id` 时调用 `script_draft/{esd_id}/edit`，否则调用 `episode/{ep_id}/script_draft/add`。

因此重复运行会更新已有镜号，不会按镜号重复新增草稿。`--dry-run` 仍会做资产和草稿只读查询，但绝不发送写请求。

正式资产按 `resource_type` 分角色、场景、道具三次查询，每类只取已定稿的前 100 个（接口单页上限）。某一类超过 100 个时命令会在 stderr 提示该类总数与实际取到的条数：排在后面的资产按名字匹配不到，会被报成「资产不存在、未定稿或没有图片」，看到提示应先在资产库里收敛该类资产，不要把它当成表格填错。

### 参数与输出

`--set file=` 必填。单表多集时每集调用一次并传 `--set episode_no=N`；工作簿仍有多个 Sheet 时也可先用 `--set sheet=SHEET_NAME` 缩小范围。参考生视频工作流同时传 `--set ai_model_mark=MODEL`：CLI 会按 Web 当前模型规则把表内或统一覆盖的时长调整到最近合法档位，同距时取较低档，并在预演项的 `original_duration` 保留调整前值；同时校验提示词 UTF-16 长度和参考图上限。未传模型时保留通用 4 至 15 秒约束。项目由 `--workspace SP_ID` 或当前绑定工作区确定。时长默认从提示词解析；用户要求整批统一时长时才用 `--set duration=`。

写结果按 `succeeded[]` / `failed[]` 返回，每项包含源表行号、镜号、`create|update` 和实际 `esd_id`。部分失败只重跑失败行；提交后用 `episode parse-result EP_ID --json` 验证提示词、图片引用与时长。

### 示例

```bash
reelmate storyboard draft-import EP_ID --workspace SP_ID \
  --set file=/absolute/path/shots.xlsx --set episode_no=1 \
  --set ai_model_mark=vidu_q2 --dry-run --json
```

## `reelmate storyboard draft-delete`

### 作用

删除一个明确的分镜草稿。`EP_ID` 用于限定操作上下文，`ESD_ID` 必须来自命令返回或查询结果。删除不可恢复，必须先用 `--dry-run` 核对目标。

### 参数

- `EP_ID`（必填）：剧集 ID。
- `ESD_ID`（必填）：分镜草稿 ID，来自 `draft-import` 或 `link-draft` 结果。
- `--dry-run`、`--idempotency-key`、`--json`：预演、幂等与 JSON 输出。

### 示例

```bash
reelmate storyboard draft-delete EP_ID ESD_ID --dry-run --json
reelmate storyboard draft-delete EP_ID ESD_ID --idempotency-key KEY --json
```

## `reelmate storyboard draft-batch-update`

### 作用

更新明确指定的分镜草稿字段（如时长）。对应前端 `POST /web/v1/df/episode/script_draft/batch_update`。`items` 必须非空；修改单条时只传该条 `esd_id`，不要展开成整个解析结果。

### 参数与输出

`--set 'items=[{"esd_id":"ESD_ID","duration":5}]'`。写操作支持 `--dry-run` 与 `--idempotency-key`。

### 示例

```bash
reelmate storyboard draft-batch-update EP_ID \
  --set 'items=[{"esd_id":"ESD_ID","duration":5}]' --dry-run --json
```

## `reelmate storyboard match-assets`

### 作用

按 GUI「匹配资产」顺序为分镜打标。优先使用 `episode parse-result` 草稿：`storyboard_key` 为 `esd_id`；parse-result 为空时回退到正式分镜，`storyboard_key` 为 `storyboard_id`。create 请求另带 `esd_id` / `storyboard_id`（有值都传）和 `ep_id`。GET 仍有 `video_prompt` / `desc` 时继续写入 `prompt`；GET 已空则**不传 `prompt`**，由服务端按 id 向 rmdfsrv 取库内词（`storyboard_id` 优先于 `esd_id`）。命令顺序逐镜创建匹配任务并轮询结果：有草稿时把 `tagged_prompt` 写入 `video_prompt`、合格角色/场景/道具写入草稿 `images`；只有正式分镜时把 `tagged_prompt` 写入 `video_gen_prompt`。无 `esd_id` 且无 `storyboard_id`、或过滤后没有合格资产时该镜记入 `failed`，不发 create / 不覆盖已有参考图。本命令不替代 `draft-import` 的本地匹配，也不调用 `episode match-resources` 或画布 `script asset-match`。

匹配在服务端完成，命令**不查询项目资产库**：`matched_assets` 只按字段校验（`type` 为 1/2/3，且 `resource_id`、`file_id` 非空），不再拿本地资产清单当白名单 —— 资产库单页上限 100 条，用残缺清单二次核对会把服务端已经匹配对的资产丢掉。

### 参数与输出

位置参数 `EP_ID` 必填。项目由 `--workspace SP_ID` 或当前绑定工作区确定，缺 `SP_ID` 时 `needs_input` 且不发 create。可选 `--set nums=[...]` 只处理所列镜号。`--dry-run` 只读 `parse-result`、必要时 `storyboard list` 与逐条 `get`，零 create、零 edit。写操作支持 `--timeout` 与 `--idempotency-key`。create 可能扣费或触发频控；CLI 仅对 745613 有限次退避，不对 745701 重试。不提供 cancel。

结果按 `succeeded[]` / `failed[]` 返回。部分失败继续后续镜，不回滚已成功项。用户确认前不对真实项目实打。

### 示例

```bash
reelmate storyboard match-assets EP_ID --workspace SP_ID --dry-run --json
reelmate storyboard match-assets EP_ID --workspace SP_ID --json
reelmate storyboard match-assets EP_ID --workspace SP_ID --set 'nums=[2]' --json
```

## `reelmate storyboard batch-generate-video`

### 作用

对应新版 GUI 的 `POST /web/v1/df/storyboard/batch-ai-generate-video`。一次请求处理同一剧集内多条已确认分镜，是 GUI 四环节工作流在分镜单确认后的标准视频入口。多剧集项目逐集调用，每集一条批量请求，不得逐镜调用生成接口。

### 参数与输出

`EPISODE_ID`、`ai_model_mark`、`ratio`、`resolution` 和非空 `items[]` 必填。每个 item 必须同时包含正式分镜 `sd_id` 与首帧 `file_id`；任一缺失时 CLI 返回 `needs_input` 且不下单。`qty` 默认 1、范围 1～4；`mouth_drive` 与 `shot_type` 默认 `false`；`idle` 可选 `0|2`。

模型、画幅和分辨率必须先从在线 `model list video --json` 的对应模型参数中选择。这个命令不使用本地默认模型，也不把展示名猜成接口值。

成功输出保留服务端任务数组。收集其中所有非空 `task_id` 后统一执行 `task wait`，所有目标任务终态成功才算完成。

```bash
reelmate storyboard batch-generate-video EP_ID \
  --set ai_model_mark=seedance_1.6 --set ratio=16:9 \
  --set resolution=1080p --set qty=1 \
  --set 'items=[{"sd_id":"sd-1","file_id":"file-1"}]' \
  --dry-run --json
```

## `reelmate storyboard batch-generate`

### 作用

只为明确选中的分镜编号批量生成参考视频/图片。对应前端 `POST /web/v1/df/storyboard/batch-ai-generate`。`generate_type=1` 为参考图生视频，`2` 为参考图生图。必须显式传非空 `nums`；服务端兼容逻辑会在 `nums` 为空时生成全部分镜，因此 CLI 主动阻止空数组或缺省值。

### 参数与输出

`--set ai_model_mark=MODEL`、`--set generate_type=1|2`、`--set ratio=`、`--set resolution=`、`--set 'nums=[1]'`。`generate_type=1` 会按 `model list --json` 中 `params.storyboard_reference_video` 校验模型、分辨率和画幅；HITL 按 `resolution_options` 原序列 `label`（如 `1080P优惠版`、`2K超清版`），`--set resolution=` 交展示名，由 CLI 转成接口枚举。`qty` 默认 1 且只能为 1～4，`idle` 只能为 0 或 2；`mouth_drive` 按模型默认为开、关或强制开启；`is_store_draft=true` 和 Web 的 `width/height` 会自动补齐。`web_search` 从 Web 同源的 `page_init.web_search[ai_model_mark]` 自动读取，不能手工指定；Seedance 1.6/2.5 的分辨率还会按团队能力动态复核。`duration` 不属于该生成接口；分镜拆解结果已有逐条时长，调整时长应先用带同一 `ai_model_mark` 的 `draft-batch-update`，不能在这里伪造字段。写操作支持 `--dry-run` 与 `--idempotency-key`。

`generate_type=1` 自动补齐的 `width/height` 与 `resolution` 无关，恒为 `2560x1440`：Web 的 `getResolutionSize` 查的是图片分辨率表（key 为 `1K`/`2K`/`3K`/`4K`），视频的 `720p`/`1080p`/`1080p_sale` 在表里查不到，一律落到默认值。CLI 如实对齐这个行为，**看到 `720p` 配 `2560x1440` 不是换算错了**，计费与画质由 `resolution` 字段决定。

成功响应可能返回一个或多个任务 ID；从 `--json` 的 `data` 中收集全部 ID，并执行 `reelmate task wait TASK_ID... --timeout 30m --json`。所有任务终态成功才算视频生成完成。多剧集项目要逐集提交并汇总等待，不能用首集结果代表全项目。

响应会为该集**全部**分镜回一条记录，但只有 `nums` 命中的那几条带非空 `task_id` 和 `list`，未选中的是 `task_id=""`、`list=null`——服务端只是补建了 `storyboard_id` 占位，没有下单也不扣费。据此可以核对实际提交范围，不要把记录条数当成生成条数。

### 示例

```bash
reelmate storyboard batch-generate EP_ID \
  --set ai_model_mark=seedance_1.6 \
  --set generate_type=1 --set ratio=16:9 --set resolution=1080p \
  --set qty=1 --set 'nums=[1]' --dry-run --json
```

确认预演中的 `nums` 后去掉 `--dry-run`，并加唯一的 `--idempotency-key`。

## 注意事项

- 三层实体不合并：分镜 → 分镜素材 `material` → 项目资产 `resource` → 跨项目 `asset-lib`。
- 所有写子命令都支持 `--dry-run` 与 `--idempotency-key`。
- `match-assets` 在 `draft-import` 之后执行，不替代本地资产名匹配；create 可能扣费或频控，先 `--dry-run`；空匹配失败且不擦已有 `images`；用户确认前不对真实项目实打；不提供 cancel。
- 发布态以当前二进制帮助、本命令页和结构化错误为执行依据；文档未登记的字段不得猜测。
