# node

节点是画布中的可执行单元。`node` 命令用于创建、查询、编辑、删除节点，管理节点连线，以及提交图片、视频、音频和文本生成任务。

## 用法

```text
reelmate node create NODE_TYPE [--canvas CANVAS_ID] [--set key=value]
reelmate node batch-create --set 'nodes=[...]' [--canvas CANVAS_ID]
reelmate node list [CANVAS_ID] [--canvas CANVAS_ID]
reelmate node get NODE_ID [--canvas CANVAS_ID]
reelmate node edit NODE_ID [--canvas CANVAS_ID] [--set key=value] [--update key=value]
reelmate node delete NODE_ID [--canvas CANVAS_ID]
reelmate node generate NODE_TYPE [NODE_ID] [--node NODE_ID] [--canvas CANVAS_ID] [--set key=value]
reelmate node table import NODE_ID --canvas CANVAS_ID --set file_id=FILE_ID
reelmate node table confirm-sheet NODE_ID --canvas CANVAS_ID --set sheet_id=SHEET_ID
reelmate node [--canvas CANVAS_ID] --left NODE_ID --right NODE_ID
```

## 子命令说明

| 命令 | 作用 |
|---|---|
| `reelmate node create NODE_TYPE` | 创建单个节点，并保存节点参数 |
| `reelmate node batch-create` | 按 JSON 批量创建节点 |
| `reelmate node list` | 列出画布节点 |
| `reelmate node get NODE_ID` | 查询单个节点 |
| `reelmate node edit NODE_ID` | 修改节点属性或生成参数 |
| `reelmate node delete NODE_ID` | 删除节点 |
| `reelmate node generate NODE_TYPE` | 提交图片、视频、音频或文本生成任务 |
| `reelmate node table import` | 表格节点导入 Excel（[YApi] 待实测） |
| `reelmate node table confirm-sheet` | 确认并加载指定 Sheet（[YApi] 待实测） |
| `reelmate node`（连线） | 创建或删除节点连线；详见 [edge.md](edge.md) 路由 |

## `reelmate node create NODE_TYPE`

### 作用

创建一个节点外壳，然后把其余 `--set` 字段写入节点 `params`。

### 参数

**位置参数**

- `NODE_TYPE`（必填）：节点类型，支持 `text`、`image`、`video`、`audio`、`table`、`script`、`asset`、`clip`、`director`、`threeDWorld`、`group`。

**选项**

| 选项 | 可重复 | 说明 |
|---|---|---|
| `--canvas CANVAS_ID` | 否 | 目标画布；省略时使用当前绑定工作区的默认画布 |
| `--workspace WORKSPACE_ID` | 否 | 显式指定工作区；显式值优先于绑定值 |
| `--space SPACE_ID` | 否 | 显式指定空间 |
| `--set key=value` | 是 | 写入节点参数；也可使用 `@file.json` 或 `@-` |
| `--idempotency-key KEY` | 否 | 写操作幂等键，建议重试时使用 |
| `--json` / `--ndjson` | 否 | 选择 JSON envelope / NDJSON 输出 |

`--set` 没有固定字段数量上限，可以重复传入多个键。以下字段用于节点外壳，不会写入 `params`：

| 字段 | 作用 | 默认值 |
|---|---|---|
| `node_type` | 节点类型；通常由位置参数 `NODE_TYPE` 提供 | 位置参数值 |
| `canvas_id` | 目标画布；通常由 `--canvas` 提供 | 当前作用域画布 |
| `name`、`node_name` | 节点名称 | `NODE_TYPE` |
| `position_x`、`positionX` | 横坐标 | 自动排布（见下） |
| `position_y`、`positionY` | 纵坐标 | 自动排布（见下） |

未显式传 `position_x`/`position_y`（两者都不传）时，CLI 会读一次画布上已有节点的位置，把新节点放到已有内容包围盒右侧（间距 180px），避免和现有节点叠在一起；画布为空则落在 `0,0`。只传其中一个坐标也视为显式指定，不会触发自动排布。

其它字段会原样保存到节点 `params`。CLI 不限制音频字段数量，但字段名称、类型和请求大小需符合服务要求。

#### 节点类型

各 `NODE_TYPE` 的常用 `params` 如下。表中标为“JSON”的字段，应作为一个 JSON 对象或数组传入；未列出的扩展字段也会被 CLI 保存。

| 顺序 | `NODE_TYPE` | 常用参数（字段及取值） |
|---:|---|---|
| 1 | `text` | `prompt` 字符串；`model` 字符串；`count` 整数；`richText` JSON（`format` 为 `plain` 或 `markdown`）；`referenceAssets`、`upstreamRefs` JSON 数组 |
| 2 | `image` | `mode`：`text2image`、`image2image`、`multi_reference`、`upscale`、`crop`、`outpaint`、`inpaint`、`erase`、`panorama`、`multi_angle_360`、`panorama_360`、`lighting`、`multi_camera_grid_9`、`story_grid_4`、`story_grid_9`、`story_grid_25`；另有 `prompt`、`model`、`count`、`settings` JSON（`ratio`、`quality`、`imageQuality`、`width`、`height`）、`creativeSetting`、`editConfig`、`referenceAssets`、`upstreamRefs` |
| 3 | `video` | `mode`：`text2video`、`image2video`、`first_frame`、`first_last_frame`、`video_reference`、`universal_reference`、`video_extend`、`video_clip`、`video_upscale`、`de_subtitle_auto`、`de_subtitle_region`、`frame_capture`、`video_edit`；另有 `prompt`、`model`、`count`、`settings` JSON（`ratio` 可为 `16:9`、`9:16`、`1:1`、`4:3`、`3:4`；`resolution` 可为 `480p`、`720p`、`1080p`、`2K`、`4K`；另有 `duration`、`enableSound`、`mouthDrive`、`shotType`、`offPeak`、`fps`）、`editConfig`、`referenceAssets`、`upstreamRefs` |
| 4 | `audio` | `audioKind`：`voiceover`、`music`、`sfx`、`ambient`；`prompt` 字符串；`model` 字符串；`duration` 数字（秒）；`count` 整数；`voice` JSON；`previewPlaybackRate` 数字 |
| 5 | `table` | `table` JSON：`active_sheet_id`、`sheet_selection_required`、`source.type`（`manual`、`excel_import` 或 `project_episode_import`）和 `sheets` |
| 6 | `script` | `runPhase`：`storyboard` 或 `asset_match`；`prompt`、`sourceText`、`model` 字符串；`shotCount` 整数；`columns`、`spawnConfig`、`upstreamRefs` JSON |
| 7 | `asset` | `sourceText`、`model` 字符串；`extractCredits` 数字；`activeTab`：`character`、`scene` 或 `prop`；`spawnConfig`、`upstreamRefs` JSON |
| 8 | `clip` | `shotOrder` 节点 ID 数组；`exportSettings` JSON（`exportTarget` 为 `canvas` 或 `local`；`resolution` 为 `480p`、`720p` 或 `1080p`；`format` 为 `mp4` 或 `webm`）；`timeline` JSON；`previewPlaybackRate` 数字 |
| 9 | `director` | 没有专属业务参数；只使用通用参考字段（如 `isReference`、`referenceRole`、`referenceLabel`） |
| 10 | `threeDWorld` | 复用图片参数结构：`mode`、`prompt`、`model`、`count`、`settings`、`editConfig`、`referenceAssets`；另可传 `worldInputIsPano` 布尔值 |
| 11 | `group` | `title` 字符串；`color` 字符串；`childNodeIds` 节点 ID 数组；`width`、`height` 数字；`collapsed`、`locked` 布尔值；`serverGroupId` 字符串 |

`audio` 的 `voice` 对象支持：

| 字段 | 取值 |
|---|---|
| `voiceId`、`voiceName`、`coverUrl`、`gender`、`language` | 字符串 |
| `tone` | `Neutral`、`Happy`、`Sad`、`Surprise`、`Angry` 等情绪值 |
| `speed`、`pitch`、`volume` | 数字 |
| `loop` | `true` 或 `false` |

### 输出

文本输出为 `NAME`、`NODE_ID`、`ACTION` 表格；`ACTION` 为 `created`。`--json` 时同时返回写入数据。

### 示例

```bash
reelmate node create text --canvas CANVAS_ID \
  --set name='旁白文案' --set prompt='欢迎来到本期节目' \
  --set model=MODEL_MARK --set count=1 --json

reelmate node create image --canvas CANVAS_ID \
  --set name='封面图' --set mode=text2image \
  --set prompt='海边日出' --set model=MODEL_MARK \
  --set settings='{"ratio":"16:9","quality":"2K"}' --json

reelmate node create video --canvas CANVAS_ID \
  --set name='开场视频' --set mode=text2video \
  --set prompt='镜头缓慢推向海边' --set model=MODEL_MARK \
  --set settings='{"ratio":"16:9","resolution":"720p","duration":5}' --json

reelmate node create audio --canvas CANVAS_ID \
  --set name='旁白' \
  --set audioKind=voiceover \
  --set prompt='欢迎来到本期节目' \
  --set model=MODEL_MARK \
  --set voice='{"voiceId":"VOICE_ID","tone":"Neutral","speed":1,"pitch":0,"volume":1}' \
  --set duration=10 \
  --set count=1 \
  --set previewPlaybackRate=1 \
  --json

reelmate node create table --canvas CANVAS_ID \
  --set name='数据表' \
  --set table='{"active_sheet_id":"sheet-1","sheet_selection_required":false,"source":{"type":"manual"},"sheets":[]}' --json

reelmate node create script --canvas CANVAS_ID \
  --set name='分镜脚本' --set runPhase=storyboard \
  --set sourceText='夜晚的城市渐渐安静下来' \
  --set model=MODEL_MARK --set shotCount=3 --json

reelmate node create asset --canvas CANVAS_ID \
  --set name='资产提取' --set sourceText='主角走进雨夜街道' \
  --set model=MODEL_MARK --set activeTab=character --json

reelmate node create clip --canvas CANVAS_ID \
  --set name='成片剪辑' --set shotOrder='["NODE_ID"]' \
  --set exportSettings='{"exportTarget":"canvas","resolution":"720p","format":"mp4"}' --json

reelmate node create director --canvas CANVAS_ID \
  --set name='导演台' --set referenceLabel='镜头编排' --json

reelmate node create threeDWorld --canvas CANVAS_ID \
  --set name='三维场景' --set mode=text2image \
  --set prompt='未来城市街区' --set model=MODEL_MARK \
  --set worldInputIsPano=false --json

reelmate node create group --canvas CANVAS_ID \
  --set name='分镜组' --set title='分镜组' --set color='#6C5CE7' \
  --set childNodeIds='["NODE_ID_1","NODE_ID_2"]' --json
```

## `reelmate node batch-create`

### 作用

从一个 `nodes` JSON 数组批量创建节点。CLI 每批最多提交 100 个节点，更多节点会拆成多个请求。

### 参数

- `--set 'nodes=[...]'`（必填）：节点对象数组，也可以写成 `--set @nodes.json` 或 `--set @-`。
- `--canvas CANVAS_ID`：未在节点对象中指定画布时使用的画布。
- `--workspace WORKSPACE_ID`、`--space SPACE_ID`：作用域参数，规则见“注意事项”。
- `--idempotency-key KEY`：写操作幂等键。

每个节点对象支持 `node_type`、`node_id`、`node_name`/`name`、`position`、`position_x`/`positionX`、`position_y`/`positionY`、`measured`、`width`、`height` 和 `params`。尺寸缺省为 `1x1`；未显式给位置的节点会按每行 5 个、间距 56px 自动网格排布（锚点在已有画布内容右侧），避免同批节点相互重叠——显式传了 `position` 或坐标的节点原样使用，不受影响。

### 输出

文本输出为每个节点一行的 `NAME`、`NODE_ID`、`ACTION` 表格；`ACTION` 为 `batch-created`。

### 示例

```bash
reelmate node batch-create --canvas CANVAS_ID \
  --set 'nodes=[{"node_type":"audio","node_name":"旁白","params":{"audioKind":"voiceover","prompt":"欢迎来到本期节目"}}]' \
  --json
```

## `reelmate node list`

### 作用

读取画布完整数据并列出其中的节点。该命令只读，不会修改远端数据。

### 参数

- `CANVAS_ID`（可选位置参数）或 `--canvas CANVAS_ID`：目标画布；两者同时提供时使用 `--canvas`。
- `--workspace WORKSPACE_ID`、`--space SPACE_ID`：作用域参数，规则见“注意事项”。
- `--no-heartbeat`：关闭画布 heartbeat，但会失去编辑权仲裁提示。

### 输出

文本输出为 `NAME`、`NODE_ID`、`ACTION` 表格；`ACTION` 为 `listed`。`--json` 返回节点数组。

### 示例

```bash
reelmate node list --canvas CANVAS_ID --json
```

## `reelmate node get NODE_ID`

### 作用

查询指定节点的完整数据。

### 参数

- `NODE_ID`（必填）：目标节点 ID。
- `--canvas CANVAS_ID`：目标画布。
- `--workspace WORKSPACE_ID`、`--space SPACE_ID`：作用域参数，规则见“注意事项”。
- `--no-heartbeat`：关闭画布 heartbeat。

### 输出

文本输出为 `NAME`、`NODE_ID`、`ACTION` 表格；`ACTION` 为 `info`。`--json` 返回节点详情。

### 示例

```bash
reelmate node get NODE_ID --canvas CANVAS_ID --json
```

## `reelmate node edit NODE_ID`

### 作用

修改已有节点。`--set` 修改节点 `params`，`--update` 修改节点自身属性（例如名称、内容）。

### 参数

- `NODE_ID`（必填）：目标节点 ID。
- `--canvas CANVAS_ID`：目标画布。
- `--set key=value`（可重复）：修改生成器参数；值支持布尔值、数字和 JSON 片段。
- `--update key=value`（可重复）：修改节点顶层属性；`--update name=...` 会写为 `node_name`。
- `--workspace WORKSPACE_ID`、`--space SPACE_ID`：作用域参数，规则见“注意事项”。
- `--idempotency-key KEY`：写操作幂等键。

同一命令同时传 `--set` 和 `--update` 时，以 `--update` 作为本次编辑内容；需要同时修改两类字段时请分两次执行。

### 输出

文本输出为 `NAME`、`NODE_ID`、`ACTION` 表格；`ACTION` 为 `updated`。

### 示例

```bash
reelmate node edit NODE_ID --canvas CANVAS_ID \
  --update name='镜头 01' --update content='备注文本' --json

reelmate node edit NODE_ID --canvas CANVAS_ID \
  --set prompt='改后的提示词' --set duration=15 --json
```

## `reelmate node delete NODE_ID`

### 作用

删除指定节点及其相关数据。该操作会改变远端画布，建议提供幂等键。

### 参数

- `NODE_ID`（必填）：目标节点 ID。
- `--canvas CANVAS_ID`：目标画布。
- `--workspace WORKSPACE_ID`、`--space SPACE_ID`：作用域参数，规则见“注意事项”。
- `--idempotency-key KEY`：写操作幂等键。

### 输出

文本输出为 `NAME`、`NODE_ID`、`ACTION` 表格；`ACTION` 为 `deleted`。

### 示例

```bash
reelmate node delete NODE_ID --canvas CANVAS_ID --idempotency-key KEY
```

## `reelmate node generate NODE_TYPE`

### 作用

提交一个节点生成任务。可指定已有节点写回生成参数与任务状态，也可以只提交任务。

### 参数

- `NODE_TYPE`（必填）：`image`、`video`、`audio` 或 `text` 等已注册类型。
- `NODE_ID`（可选位置参数）或 `--node NODE_ID`：目标节点；文本、图片、视频指定后会先把本次生成参数合并写回节点，再创建任务，任务创建成功后继续写回 `task_info`。图片指定 `--node` 时，CLI 会读取入边上游图片的 `result.items[].fileId` 并合并本节点 `referenceAssets`；有图则自动走参考生图，不必再手工传 `images`。已显式传 `images` 时以命令行为准。
- `--canvas CANVAS_ID`：目标画布。
- `--workspace WORKSPACE_ID`、`--space SPACE_ID`：作用域参数，规则见“注意事项”。
- `--set key=value`（可重复）：生成参数。图片、视频至少提供 `ai_model_mark` 或兼容的 `model`；音频不选择模型，改用 `audioKind`；提示词、时长和其它字段需符合对应模式规则。
- `--idempotency-key KEY`：生成及写回操作的幂等键。
- `--dry-run`：预演。**本命令会扣费，提交前先跑一次预演。** 不发任何请求，输出 `dry_run=true` 与 `items[0]`。预演里的模型字段是展示名，不是提交标识。核对模型展示名、`resolution`、`radio_ui`（画幅）、`qty` 和自动算出的 `width`/`height`，确认后去掉 `--dry-run` 重跑同一条命令。

图片、视频参数由节点类型、模式和所选模型联合确定。先从在线 `model list --json` 的 `params.generation.<mode>` 读取默认值与合法选项，也可用 `model params image|video MODEL_NAME --json` 查看静态规则。CLI 会补齐 Web 默认值、校验枚举和素材数量；图片 `width/height` 根据模型、`resolution`、`ratio` 自动计算，传入旧尺寸也不会覆盖规则结果。

视频模式与接口对应为：`text2video` 文生视频，`image2video`/`first_frame`/`first_last_frame` 图生视频，`universal_reference` 参考媒体生视频，`video_edit` AI 改视频，`video_extend` 视频续写。`video_edit.duration` 必须取源视频实际时长；Seedance 参考、编辑和续写的清晰度会在提交前按当前团队能力再次过滤。

文本生成常用参数：

| 参数 | 取值 | 说明 |
|---|---|---|
| `ai_model_mark` 或 `model` | 模型展示名 | 填写 `model list` 返回的 `name`；不要填写或展示提交标识 |
| `prompt` | 字符串 | 要生成或改写的文本；实际生成时应提供非空值 |

音频生成常用参数：

| 参数 | 取值 | 说明 |
|---|---|---|
| `audioKind` | `voiceover`、`music`、`sfx`、`ambient` | 旁白、配乐、音效或氛围 |
| `prompt` | 字符串 | 音频提示词或旁白文本 |
| `duration` | 数字，单位秒 | `music`/`ambient` 支持 `10/30/60`，默认 `30`；`sfx` 支持 `5/10/15`，默认 `5`；旁白接口不提交时长 |
| `voice` | JSON 对象 | `voiceover` 必须包含 `voiceId`；`tone` 支持 `Neutral/Happy/Sad/Surprise/Angry`，`speed` 为 `0.5～2`，`pitch` 为 `-12～12`，`volume` 可用画布倍率 `0.02～2` 或接口值 `1～100` |

图片和视频还可以传递模型专属扩展字段。音频由 CLI 按 Web 路由做必填项、枚举和范围校验，并移除误传的 `ai_model_mark`/`model`。文本生成会使用 `prompt`、模型标识和画布上下文，其它字段需符合服务要求。

### 输出

文本输出为 `TASK_ID`、`NODE_TYPE` 表格。文本、图片、视频指定 `NODE_ID` 时，CLI 会先按 Web 字段结构持久化本次生成参数并保留节点已有参数；该步失败会中止生成。任务创建成功后还会更新该节点的 `task_info`。

### 示例

```bash
reelmate node generate image --canvas CANVAS_ID --workspace WORKSPACE_ID --space SPACE_ID \
  --node NODE_ID --set ai_model_mark=seedream_4.5 \
  --set prompt='海边日出，金色晨光照亮海面，写实风格' --set ratio=16:9 --json

reelmate node generate image --canvas CANVAS_ID --workspace WORKSPACE_ID --space SPACE_ID \
  --node NODE_ID --set ai_model_mark='TGI 2' \
  --set prompt='保持构图，改成秋林落叶' --set ratio=16:9 --set resolution=2K --json

reelmate node generate video --canvas CANVAS_ID --workspace WORKSPACE_ID --space SPACE_ID \
  --node NODE_ID --set ai_model_mark=seedance_2.5 \
  --set mode=universal_reference --set 'images=[{"uri":"IMAGE_FILE_ID"}]' \
  --set prompt='足球场观赛，球迷看台欢呼，真实体育转播风格' \
  --set duration=5 --set ratio=16:9 --set resolution=720p --json

reelmate node generate audio --canvas CANVAS_ID --node NODE_ID \
  --set audioKind=music --set prompt='雨夜悬疑氛围配乐' --set duration=30 --json

reelmate node generate text --canvas CANVAS_ID --node NODE_ID \
  --set ai_model_mark=MODEL_MARK \
  --set prompt='请将这段素材整理成三句简洁的旁白' --json
```

## `reelmate node`（连线）

### 作用

不带子命令时用于管理节点连线：`--left`/`--right` 是确保连线存在，`--left-add`/`--left-rm` 是增量增加或删除入边。

### 参数

- `--canvas CANVAS_ID`（必填）：目标画布。
- `--left NODE_ID`、`--right NODE_ID`（可重复）：成对提供，确保对应的上游到下游连线存在。
- `--left-add NODE_ID`（可重复）：增加指定上游到目标节点的入边。
- `--left-rm NODE_ID`（可重复）：删除指定上游到目标节点的入边。
- `--semantic pipeline|reference|sequence`：连线语义，默认 `pipeline`。
- `--workspace WORKSPACE_ID`、`--space SPACE_ID`：作用域参数，规则见“注意事项”。
- `--idempotency-key KEY`：写操作幂等键。

`--left`/`--right` 不能与 `--left-add`/`--left-rm` 混用。增量模式必须恰好提供一个 `--right` 目标节点。

### 输出

每次连线操作返回 `NAME`、`NODE_ID`、`ACTION` 表格；JSON 输出包含完整连线结果。

### 示例

```bash
reelmate node --canvas CANVAS_ID \
  --left UPSTREAM_NODE_ID --right DOWNSTREAM_NODE_ID --semantic pipeline

reelmate node --canvas CANVAS_ID \
  --left-add UPSTREAM_NODE_ID --right DOWNSTREAM_NODE_ID
```

## `reelmate node table import`

### 作用

表格节点导入 Excel。路径 `POST canvas/:canvas_id/nodes/:node_id/table/import`。接口目前是 **[YApi] 待实测**。

两步必须分开：`import` 后先看返回的 Sheet 列表（在 `raw` 里），再 `confirm-sheet` **显式指定** `sheet_id`。不会自动选第一个 Sheet。

### 参数

- `NODE_ID`：位置参数或 `--node`。
- `--canvas CANVAS_ID`（必填）：目标画布。
- `--set file_id=`（必填）：已上传 Excel 的文件 ID。
- `--idempotency-key`、`--dry-run`：写命令走 canvaswrite。
- `--json`：输出 JSON。响应完整保留在 `raw`。不得声称已验证。

### 示例

```bash
reelmate node table import NODE_ID --canvas CANVAS_ID --set file_id=FILE_ID --json
```

## `reelmate node table confirm-sheet`

### 作用

确认并加载指定 Sheet。路径 `POST canvas/:canvas_id/nodes/:node_id/table/confirm-sheet`。接口目前是 **[YApi] 待实测**。

### 参数

- `NODE_ID`：位置参数或 `--node`。
- `--canvas CANVAS_ID`（必填）：目标画布。
- `--set sheet_id=`（必填）：要加载的 Sheet。
- `--idempotency-key`、`--dry-run`、`--json`。

### 示例

```bash
reelmate node table confirm-sheet NODE_ID --canvas CANVAS_ID --set sheet_id=SHEET_ID --json
```

## 注意事项

- `--set` 的值按 shell 参数传递：普通值没有空格或特殊字符时可以不加引号；带空格的文本和整个 JSON 对象应保留外层引号。例如 `--set voice='{"voiceId":"VOICE_ID"}'`。
- 所有使用画布的命令都需要 `CANVAS_ID`。显式 `--workspace`、`--canvas`、`--space` 优先；省略 `--workspace` 时，CLI 会从当前绑定工作区解析默认工作区并带入请求。
- `--set ai_model_mark=` 填写 `reelmate model list --json` 或 `reelmate model search KEYWORD --json` 返回的展示名。不要向用户展示或抄写 `id` / `ai_model_mark`。
- 写操作建议使用 `--idempotency-key`，只读 `list/get` 可以使用 `--no-heartbeat`；写操作不能关闭 heartbeat。
- `node recover` 当前暂不可用；需要恢复时请使用 `node create` 重新建立节点。
