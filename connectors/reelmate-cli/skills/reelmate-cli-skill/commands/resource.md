# resource

管理制片工坊的**项目级资产**：创建未定稿资产、用已上传图片创建已定稿资产、回填提取草稿、查询详情、在「未定稿 ↔ 定稿」之间流转。

## 三层实体边界

素材与资产是三层不同实体，命令面分别承接，任何一层都不能替代另一层：

| 层 | 实体 | 命令组 | ID |
|---|---|---|---|
| 分镜级 | `storyboard_info` | `material --storyboard` | `info_id` |
| 项目级 | `resource` | **`resource`（本篇）** | `resource_id` |
| 跨项目 | `user_knowledge` | `asset-lib` | `uk_id` |

`resource add` 创建的是**未定稿**资源，必须再调用 `confirm` 才进入正式态。add 完不等于结束。

`resource file-import` 用已上传的 `file_id` **一次创建已定稿**项目资产。它不是 `add`，也不是把图片挂到已有 `resource_id`。不得把 `file_id` 塞进 `resource add` 冒充挂图或定稿。

`resource draft-import` 写入的是资产提取操作台的**提取草稿**，成功返回 `eed_id`。它不是 `add`（未定稿正式资产 `resource_id`），不是 `file-import`（已定稿项目资产），也不是 `extract*`（服务端 AI 提取任务）。后续 `batch-draft-generate` 只能用本命令或 `draft-list` 返回的 `eed_id`，禁止用 `resource add` 的 `resource_id` 冒充。

资产库空态中的“生成角色 / 生成场景 / 生成道具”是另一条独立链路：先用 `resource add` 创建未定稿项目资产，再用 `resource generate` 为该 `resource_id` 提交文生图或参考图生图。它不需要剧本、剧集、提取任务或 `et_id`，也不使用 `batch-draft-generate`。

## 按场景选子命令

| 场景 | 子命令链 | 流程文档 |
|---|---|---|
| GUI 四环节：剧本提取资产 | `extract` → `extract-wait` → `draft-list` → `batch-draft-generate` → `batch-confirm` | [gui-script-video-asset.md](../manual/workflow/gui-script-video-asset.md) |
| GUI 回填：提示词表生图 | `preset-list` → `prompt-template` → `prompt-sheet-read` → `add` → `generate` →（子形态）`confirm-record` → `confirm` / `batch-confirm` | [gui-backfill-asset-prompt.md](../manual/workflow/gui-backfill-asset-prompt.md) |
| GUI 回填：已有图片包 | `file-import`；角色存主体时 `batch-confirm --set business_list=[3]` | [gui-backfill-asset-image.md](../manual/workflow/gui-backfill-asset-image.md) |
| 独立资产页文生图 / 图生图 | `add` → `generate` → `generate-list` → `confirm` 或 `confirm-record` | 本篇 ``resource add`` / ``resource generate`` |
| 资产库 ⇄ 项目 | `import`；跨项目库见 [asset-lib.md](asset-lib.md) | — |
| 剧集级提示词补全 / 匹配重置 | `prompt-complete` → `prompt-complete-result`；`match-reset` | [episode.md](episode.md) |
| 只读 / 排查 | `list`、`get`、`batch-info`、`generate-list`、`extract-status` | — |

## 用法

```text
reelmate resource prompt-template OUTPUT.xlsx [--set overwrite=true]
reelmate resource prompt-sheet-read ASSETS.xlsx [--set sheet=SHEET_NAME]
reelmate resource preset-list [SP_ID] --set kind=style|theme [--set res_type=1|2|3] [--set use_type=1|2] [--set lang=zh-CN|en-US]
reelmate resource generate-image-types
reelmate resource draft-import [SP_ID] --set type=TYPE --set name=NAME --set prompt=PROMPT
reelmate resource draft-import [SP_ID] --set @assets.json
reelmate resource list [SP_ID] [--set page=N] [--set page_size=N] [--set all=true] [--set resource_type=N] [--set status=N]
reelmate resource draft-list [SP_ID] --set resource_type=1|2|3
reelmate resource add [SP_ID] --set type=TYPE --set name=NAME [--set key=value ...]
reelmate resource add [SP_ID] --set @assets.json
reelmate resource generate SP_ID RESOURCE_ID --set type=TYPE --set prompt=PROMPT --set ai_model_mark=MODEL --set resolution=2K --set radio_ui=16:9
reelmate resource generate-list SP_ID RESOURCE_ID [--set page=N] [--set page_size=N] [--set all=true]
reelmate resource get SP_ID RESOURCE_ID
reelmate resource voice-desc [SP_ID] RESOURCE_ID --set audio_prompt=TEXT [--set sync_sub=true|false]
reelmate resource voice-desc [SP_ID] --set eed_id=EED_ID --set audio_prompt=TEXT
reelmate resource voice-desc [SP_ID] RESOURCE_ID --set uk_id=UK_ID
reelmate resource voice-audio [SP_ID] RESOURCE_ID FILE [--set start=SEC --set end=SEC] [--set sync_sub=true|false]
reelmate resource voice-audio [SP_ID] --set eed_id=EED_ID --set audio_file_id=FILE_ID
reelmate resource voice-library list [--set source=official|team] [--set lang=LANG] [--set all=true]
reelmate resource batch-info [SP_ID] --set 'resource_ids=["r-1","r-2"]'
reelmate resource confirm [SP_ID] --set 'resource_ids=["r-1"]'
reelmate resource confirm-record SP_ID RESOURCE_ID --set generate_id=GENERATE_ID --set name=NAME
reelmate resource unconfirm [SP_ID] --set 'resource_ids=["r-1"]'
reelmate resource batch-confirm [SP_ID] --set 'resource_ids=["r-1","r-2"]'
reelmate resource batch-draft-generate [SP_ID] --set res_type=1|2|3 --set 'eed_ids=["eed-1"]' --set ai_model_mark=MODEL --set resolution=RESOLUTION --set radio_ui=RATIO
reelmate resource file-import [SP_ID] --set type=TYPE --set name=NAME --set file_id=FILE_ID
reelmate resource file-import [SP_ID] --set @assets.json
reelmate resource import [SP_ID] --set direction=asset-to-resource --set 'uk_ids=["uk-1"]'
reelmate resource import [SP_ID] --set direction=resource-to-asset --set 'resource_ids=["r-1"]'
reelmate resource extract [SP_ID] [--set task_type=1] [--set generate_mode=1] [--set need_voice=1]
reelmate resource extract-status [SP_ID] [--set et_id=ET_ID]
reelmate resource extract-wait [SP_ID] [--set et_id=ET_ID] [--timeout 30m]
reelmate resource extract-redo [SP_ID]
reelmate resource prompt-complete EP_ID --workspace SP_ID --set 'target_assets=[...]'
reelmate resource prompt-complete-result EP_ID --workspace SP_ID
reelmate resource match-reset EP_ID
```

`SP_ID` 省略时使用当前绑定的工作区；都没有时命令返回 `needs_input` 并指出缺 `sp_id`。`prompt-complete`、`prompt-complete-result` 和 `match-reset` 的位置参数是 `EP_ID`，项目 ID 必须来自当前绑定工作区或 `--workspace SP_ID`。

## 子命令说明

| 命令 | 作用 |
|---|---|
| `reelmate resource prompt-template` | 用 CLI Go 代码实时生成资产提示词 `.xlsx` 模板 |
| `reelmate resource prompt-sheet-read` | 读取、校验用户回传表格并输出按类型拆分的草稿导入批次 |
| `reelmate resource preset-list` | 按项目类型在线查询风格或题材目录，并自动分页 |
| `reelmate resource generate-image-types` | 查询角色构图 `generate_image_type` 静态枚举 |
| `reelmate resource draft-import` | 创建或更新提取草稿并设置主子关系；返回 `eed_id` |
| `reelmate resource list` | 列出项目资产库的一页，并报告服务端总数 |
| `reelmate resource draft-list` | 列出提取任务中的资产草稿主形态；返回 `eed_id` |
| `reelmate resource add` | 创建未定稿资产，支持单条与批量 |
| `reelmate resource generate` | 通过资产库“生成角色 / 生成场景 / 生成道具”链路为已有资产生成图片 |
| `reelmate resource generate-list` | 查询一个项目资产下的图片生成记录的一页，并报告服务端总数 |
| `reelmate resource get` | 查询单个资产详情 |
| `reelmate resource voice-desc` | 保存角色音色描述，或按音色模板回填后保存 |
| `reelmate resource voice-audio` | 上传或绑定角色参考音频 |
| `reelmate resource voice-library list` | 列出官方或团队音色模板 |
| `reelmate resource batch-info` | 批量查询资产详情 |
| `reelmate resource confirm` | 资产定稿 |
| `reelmate resource confirm-record SP_ID RESOURCE_ID` | 将用户选中的独立生成记录定稿为资产当前主图 |
| `reelmate resource unconfirm` | 撤销定稿 |
| `reelmate resource batch-confirm` | 批量定稿 |
| `reelmate resource file-import` | 用已上传 `file_id` 创建已定稿项目资产 |
| `reelmate resource batch-draft-generate` | 按角色、场景或道具批量生成草稿主形态图片 |
| `reelmate resource import` | 资产库与项目资产双向导入 |
| `reelmate resource extract` | 从剧本草稿创建项目级资产提取任务，返回 `et_id` |
| `reelmate resource extract-status` | 查询项目级资产提取任务状态 |
| `reelmate resource extract-wait` | 轮询直到提取任务成功、失败或超时 |
| `reelmate resource extract-redo` | 重做失败或失效的提取任务 |
| `reelmate resource prompt-complete` | 从剧本为指定的未匹配资产补全提示词 |
| `reelmate resource prompt-complete-result` | 查询一集的资产提示词补全任务与逐项结果 |
| `reelmate resource match-reset` | 重置剧集的资产匹配 |

## `reelmate resource preset-list`

### 作用

调用 `POST /web/v1/df/user_knowledge/list` 查询资产生图可用的风格或题材。命令先读取项目详情中的 `sp_type`，再按 Web 口径过滤官方目录；默认同时返回官方与团队知识库条目。接口声明单页最多 100 条，CLI 会自动翻页直到取完，不能用超大 `page_size` 假装全量。

### 参数与输出

`--set kind=style|theme` 必填。风格按资源类型隔离，查询还必须传 `--set res_type=1|2|3`；题材不需要 `res_type`。问用户时风格只列一份展示名，不要拆成角色/场景/道具三问；提交时按名称在对应 `res_type` 列表里取 `uk_id`。`--set use_type=1|2` 可只看官方或团队目录，省略时返回两者。`--set lang=zh-CN|en-US` 透传语言筛选。

`--json` 返回项目 `sp_type`、目录 `scene`、`count` 和 `list[]`。生成请求只使用条目的 `uk_id` 作为 `style_uk_id` / `theme_uk_id`；不得把 `name` 或 `prompt_template` 当成生成参数。

```bash
reelmate resource preset-list SP_ID --set kind=style --set res_type=1 --set lang=zh-CN --json
reelmate resource preset-list SP_ID --set kind=theme --set lang=zh-CN --json
```

角色构图不是该知识库的 `scene=3`：后者是“分镜构图模板”。资产批量生图的角色构图见下方 `generate-image-types`。

## `reelmate resource generate-image-types`

### 作用

返回角色构图名称清单。清单由 CLI 源码 `studio.GenerateImageTypes()` 定义，不登录、不访问网络。只用于角色请求；场景和道具不传该字段。

### 参数与输出

无业务参数。`--json` 返回 `applies_to=["character"]`、`recommended`（推荐项名称）和 `list[{name,recommended}]`。不返回数字取值。HITL 只展示 `list[].name`，推荐项可标 `（推荐）`。提交时把名称传给 `--set generate_image_type=`，由 CLI 解析。

```bash
reelmate resource generate-image-types --json
```

## `reelmate resource prompt-template`

### 作用

在命令执行时由 Go 代码生成资产提示词 `.xlsx`。命令离线运行，不要求登录、项目或网络；Skill、源码资源目录和构建产物均不携带静态模板文件。

模板包含「资产提示词清单」与「填写示例」两个 Sheet。填写 Sheet 提供 100 个空白数据行，并为资产类型和形态提供下拉选项；用户可以复制填写 Sheet 后分页录入。业务术语固定为“主形态/子形态”。

### 参数与输出

位置参数 `OUTPUT.xlsx` 是目标文件。默认拒绝覆盖已有文件；用户明确要求替换时传 `--set overwrite=true`。`--dry-run` 只返回目标路径和模板元数据，不写文件。

`--json` 的 `data.path` 是生成文件的绝对路径，`data.sheets` 是 Sheet 列表，`data.rows` 是空白填写行数。

```bash
reelmate resource prompt-template /absolute/path/asset-prompts.xlsx --json
```

## `reelmate resource prompt-sheet-read`

### 作用

离线读取资产提示词 `.xlsx` 或 `.xlsm`，校验资产类型、名称、主形态/子形态关系和提示词，并转换为 Agent 可用于 `resource add` / `resource generate` 的分类型批次。解析器与模板生成器共用 `internal/assetprompt` 中的代码契约。

官方五列与四列方言（`资产类型`、`资产名称`、`主子资产属性`、`生图提示词`；`主`/`子`）可直接读取。其它自带清单缺列时，由 Agent 按 [_backfill-contract.md](../manual/workflow/_backfill-contract.md) 转写入 `prompt-template` 生成的官方表后再调用本命令。不要让用户重填空模板。本命令不改表。

### 参数与输出

位置参数 `ASSETS.xlsx` 是回传文件。默认按工作簿顺序汇总所有业务 Sheet，跳过「填写示例」和没有数据的空白 Sheet；可用 `--set sheet=SHEET_NAME` 只解析一个指定 Sheet。命令不要求登录、项目或网络。

子形态可以按“同一资产类型 + 主形态名称”引用其他业务 Sheet 中的主形态。该主形态在整个工作簿中必须唯一；不同 Sheet 出现同类型同名主形态时返回歧义错误。

`--json` 返回：

- `data.rows[]`：包含 `source_sheet`、源行号、业务形态和生成后的 `group_id` / `state_id` / `parent_state_id`；
- `data.batches[]`：按 `character`、`scene`、`prop` 分组，每个批次的 `items` 保留主子形态关系，供 Agent 分阶段调用 `resource add` / `resource generate`；
- `data.sheets[]`：本次实际解析并汇总的业务 Sheet；
- `data.count`：有效数据行数。

缺列或数据问题返回 `kind=usage`、`raw.needs_input=true`，`missing[]` 标明具体 Sheet、行号和字段。已填所属主形态时只做精确名称匹配；四列方言未填该列时，按子名称前缀在同类型主形态中唯一匹配，0 或 ≥2 条则 `needs_input`。

```bash
reelmate resource prompt-sheet-read /absolute/path/asset-prompts.xlsx --json
```

## `reelmate resource list`

### 作用

列出项目资产库。

### 参数与输出

`SP_ID` 省略时使用当前绑定的工作区；都没有时命令返回 `needs_input` 并指出缺 `sp_id`。

接口单页默认 20 条、上限 100 条。命令**默认只取第一页**（`page_size=100`），不替你把整个资产库翻完 —— 上万条资产要发上百次请求，停点也说不清。要不要继续往下取由你决定：

| `--set` | 说明 |
|---|---|
| `page=N` | 取第 N 页，默认 1 |
| `page_size=N` | 单页条数，默认也是上限 100 |
| `all=true` | 从起始页起按 `data.count` 一路翻到取完；连续 100 页仍未翻完会报错，此时应改用 `resource_type` / `status` 缩小范围 |
| `resource_type=N` | 0 全部、1 角色、2 场景、3 道具、4 参考视频、5 参考图片 |
| `status=N` | 0 全部、2 已定稿 |

输出里 `data.count` 是**服务端总数**，`data.list[]` 是本次取到的条目，另有 `data.page`、`data.page_size`、`data.has_more` 和（还有下一页时的）`data.next_page`。表格列 `RESOURCES` 是本次取到的条数，`COUNT` 是服务端总数，`HAS_MORE` 说明还有没有没取的。

`has_more=true` 时**不要**拿这份清单去做批量定稿、保存主体或资产名匹配：清单不全但不会报错，表现为"某几个资产没被处理"或"资产缺失"。要么按提示继续翻页，要么用 `resource_type` / `status` 把范围缩小到一页装得下。

### 示例

```bash
reelmate resource list SP_ID --json
reelmate resource list SP_ID --set page=2 --json
reelmate resource list SP_ID --set resource_type=1 --set status=2 --json
reelmate resource list SP_ID --set all=true --json
```

## `reelmate resource get`

### 作用

查询单个资产详情。

### 参数与输出

位置参数 `SP_ID RESOURCE_ID`。`--json` 输出完整资产数据。

### 示例

```bash
reelmate resource get SP_ID RESOURCE_ID --json
```

## `reelmate resource batch-info`

### 作用

批量查询资产详情。

### 参数与输出

`--set 'resource_ids=["r-1","r-2"]'` 指定要查询的资产。`SP_ID` 省略时使用当前绑定。

### 示例

```bash
reelmate resource batch-info SP_ID --set 'resource_ids=["r-1","r-2"]' --json
```

## `reelmate resource add`

### 作用

创建未定稿资产，支持单条与批量。创建的是未定稿资源，必须再调用 `confirm` 才进入正式态。

### 参数与输出

`--set type=` 与 `--set name=` 必填。`SP_ID` 省略时使用当前绑定。写操作支持 `--dry-run` 与 `--idempotency-key`。

### 资产类型

`--set type=` 取值固定为三类，传其它值直接拒绝：

| 取值 | 含义 |
|---|---|
| `character` | 角色 |
| `scene` | 场景 |
| `prop` | 道具 |

### 必填字段

| 字段 | 说明 |
|---|---|
| `type` | 资产类型，三选一 |
| `name` | 资产名称 |

CLI 会把业务类型 `character / scene / prop` 转换为后端字段 `resource_type=1 / 2 / 3`，不会把字符串 `type` 原样发送。`desc`（资产描述）和 `prompt`（生图提示词）可一并提供，其它字段原样透传。

完整字段尚未在发布契约登记，所以这里只校验一定必需的两个字段。发布态不得猜测其它字段；需要扩展时以子命令帮助和服务端结构化错误为准。

### 批量入参

批量走 `resources` 数组。`--set` 的文件形态必须是对象，所以数组包在 `resources` 键里。

### 示例

```json
{
  "resources": [
    { "type": "character", "name": "沈赫", "desc": "调查记者，左手食指有敲击习惯" },
    { "type": "scene", "name": "旧宅地下室" },
    { "type": "prop", "name": "ZIPPO 打火机" }
  ]
}
```

```bash
reelmate resource add SP_ID --set @assets.json --dry-run --json
reelmate resource add SP_ID --set @assets.json --json
```

批量逐条创建，结果分 `succeeded` 与 `failed` 两组返回，已成功的不回滚；`failed` 每项带原始 `name` / `type` 与失败原因。整体退出码取失败项中最严重的一类。

### 预演

任何写子命令加 `--dry-run` 都会打印将提交的条目清单后以退出码 0 结束，不发任何写请求：

```bash
reelmate resource add SP_ID --set type=character --set name=沈赫 --dry-run --json
```

## `reelmate resource generate`

### 作用

对应项目资产页空态中的“生成角色 / 生成场景 / 生成道具”。目标必须是 `resource add` 返回的未定稿 `resource_id`；命令直接调用图片生成接口，不创建或依赖资产提取任务。

没有参考图时调用 `/web/v1/ai/text-to-image`。传 `--set parent_file_id=FILE_ID` 时调用 `/web/v1/ai/refer-image-to-image`，并把该文件作为主形态参考图，适用于生成子形态。

```bash
reelmate resource generate SP_ID RESOURCE_ID \
  --set type=character --set prompt='人物主形态提示词' \
  --set ai_model_mark=seedream_4.0 --set resolution=2K --set radio_ui=16:9 \
  --set qty=1 --dry-run --json

reelmate resource generate SP_ID CHILD_RESOURCE_ID \
  --set type=character --set prompt='人物微笑子形态提示词' \
  --set ai_model_mark=seedream_4.0 --set resolution=2K --set radio_ui=16:9 \
  --set parent_file_id=MAIN_FILE_ID --set qty=1 --dry-run --json
```

成功输出含 `resource_id`、`task_id` 和 `mode`。随后用 `task wait TASK_ID` 等待任务，并用 `resource generate-list SP_ID RESOURCE_ID` 读取 `generate_id`、`file_id`、`task_status` 与定稿状态。19 位数字 ID（`generate_id`、`esd_id` 等）经 `--set` 传入时按字面量保留，内联、`@file` 裸数字和引号形式都不丢精度；不再需要为此改用位置参数。

`--dry-run --json` 的 `data.credits_estimate` 含 Web 询价用的 `alg_code`、`params` 和 `business_count=1`。把该对象原样交给 `credits estimate` 得到统一账单；`qty` 仍是单个资产生成的图片数。

## `reelmate resource generate-list`

查询一个项目资产的生成记录：

```bash
reelmate resource generate-list SP_ID RESOURCE_ID --json
reelmate resource generate-list SP_ID RESOURCE_ID --set page=2 --json
reelmate resource generate-list SP_ID RESOURCE_ID --set all=true --json
```

分页口径与 `resource list` 完全一致：接口单页默认 20 条、上限 100 条，命令**默认只取第一页**（`page_size=100`），`--set page=N` 逐页取、`--set all=true` 一次取完。输出顶层给出 `count`（服务端总数）、`page`、`page_size`、`has_more` 和 `next_page`，生成记录本身在 `data.list[]`。

`has_more=true` 时不要拿这份记录去挑定稿图的 `file_id` 或判断"某个 `generate_id` 不存在"：生图次数多的资产会在第 100 条之后被截断，且不报错。

### 缺参

缺 `type` 或 `name` 时返回 `kind=usage` 且 `raw.needs_input=true` 的澄清信号，`raw.missing` 逐项列出缺哪个字段（批量时带条目序号），供上层向用户追问。

## `reelmate resource confirm`

### 作用

资产定稿。`resource add` 创建的是未定稿资源，必须再调用本命令才进入正式态。

### 参数与输出

`--set 'resource_ids=[...]'` 传要流转的资产 ID，也可用 `--set resource_id=r-1` 传单条。支持 `--dry-run` 与 `--idempotency-key`。

### 示例

```bash
reelmate resource confirm SP_ID --set 'resource_ids=["RESOURCE_ID"]' --json
```

## `reelmate resource confirm-record SP_ID RESOURCE_ID`

### 作用

将某次 `resource generate` 返回的**指定生成记录**（`generate_id`）定稿为该资产的当前主图。用于独立资产页「生成角色 / 场景 / 道具」链路：同一 `resource_id` 可能有多条生成记录，需要精确绑定用户选定的一条，而不是批量 `confirm` 整资产。

### 参数与输出

| 参数 | 必填 | 说明 |
|---|---:|---|
| `SP_ID` | 是 | 项目 ID；省略绑定工作区时由当前 `workspace` 解析 |
| `RESOURCE_ID` | 是 | 项目资产 ID |
| `--set generate_id=GENERATE_ID` | 是 | 来自 `resource generate-list` 的用户选中记录 |
| `--set name=NAME` | 是 | 定稿后的资产名称 |
| `--set sync_subject=` | 否 | 透传服务端是否同步主体（按产品需要） |
| `--dry-run`、`--idempotency-key`、`--json` | 否 | 预演、幂等与 JSON 输出 |

成功时表格含 `SP_ID`、`RESOURCE_ID`、`GENERATE_ID`、`ACTION=confirm-record`。写操作需编辑权与正常心跳，不可用 `--no-heartbeat`。

### 示例

```bash
reelmate resource generate-list SP_ID RESOURCE_ID --set all=true --json
reelmate resource confirm-record SP_ID RESOURCE_ID \
  --set generate_id=GENERATE_ID --set name=NAME --dry-run --json
reelmate resource confirm-record SP_ID RESOURCE_ID \
  --set generate_id=GENERATE_ID --set name=NAME --json
```

定稿后若要把角色保存为 Seedance 主体，继续 `subject save-from-resource`；不要调用 `subject from-resource`（后者是从输入素材新建资产并同步建主体）。

## `reelmate resource unconfirm`

### 作用

撤销定稿。

### 参数与输出

与 `reelmate resource confirm` 相同。

### 示例

```bash
reelmate resource unconfirm SP_ID --set 'resource_ids=["r-1"]' --json
```

## `reelmate resource batch-confirm`

### 作用

批量定稿。还承接前端的“批量定稿并保存为主体”。角色保存为 Seedance 主体时传 `--set 'business_list=[3]'`；只定稿时不要传 `business_list`。角色和场景/道具要拆批提交，避免把非角色资产误存为主体。

### 参数与输出

`--set 'resource_ids=[...]'` 传要流转的资产 ID，也可用 `--set resource_id=r-1` 传单条。三条子命令都支持 `--dry-run` 与 `--idempotency-key`。

### 示例

```bash
reelmate resource batch-confirm SP_ID \
  --set 'resource_ids=["ROLE_RESOURCE_ID"]' \
  --set 'business_list=[3]' --dry-run --json
reelmate resource batch-confirm SP_ID \
  --set 'resource_ids=["SCENE_RESOURCE_ID","PROP_RESOURCE_ID"]' \
  --dry-run --json
```

前端接口 `POST /web/v1/df/resources/batch-confirm` 中 `business_list=3` 表示 Seedance；不传时只定稿。需要精确绑定某个 `generate_id` 时见本篇 ``resource confirm-record``；角色存主体再用 `subject save-from-resource`。

## `reelmate resource import`

### 作用

资产库与项目资产双向导入。一条命令承接两个方向，**方向是参数不是子命令**。

### 参数与输出

| `--set direction=` | 方向 | ID 参数 |
|---|---|---|
| `asset-to-resource` | 团队/公共资产库 → 项目资产 | `--set 'uk_ids=[...]'` |
| `resource-to-asset` | 项目资产 → 资产库 | `--set 'resource_ids=[...]'` |

`direction` 传其它值会报错并列出两个合法值。该命令支持 `--dry-run` 与 `--idempotency-key`。

### 示例

```bash
reelmate resource import SP_ID --set direction=asset-to-resource --set 'uk_ids=["uk-1","uk-2"]' --json
reelmate resource import SP_ID --set direction=resource-to-asset --set 'resource_ids=["r-1"]' --json
```

本命令只做资产库互导，**不能**用来把本地图片或 `upload` 得到的 `file_id` 建成项目资产。本地图导入走 `resource file-import`。

## `reelmate resource file-import`

### 作用

用已上传的 `file_id` 创建**已定稿**项目资产。对应 `POST /web/v1/df/resources/import`。成功即视为已定稿，不必再调 `resource confirm`。

三条边界：

- `file-import`：消费 `upload` 返回的 `file_id`，创建已定稿项目资产。
- `import`：只做 `asset-to-resource` / `resource-to-asset` 资产库互导。
- `add`：只创建未定稿空资产；**不得**传 `file_id` 冒充挂图或定稿。

本命令不打开本地文件、不调用 Drive、不把图片二次贴到已有 `resource_id`，也不保存 Seedance 主体。角色存主体仍走 `resource batch-confirm --set 'business_list=[3]'`。

### 参数与输出

| 字段 | 必需 | 说明 |
|---|---|---|
| `type` | 是 | `character` / `scene` / `prop`，映射为后端 `resource_type` `1` / `2` / `3` |
| `name` | 是 | 资产名称 |
| `file_id` | 是 | 非空字符串；同一资产多图时用逗号分隔的**单个字符串**，不要传数组 |

`SP_ID` 省略时使用当前绑定的工作区。写操作支持 `--dry-run` 与 `--idempotency-key`。

同一次调用只允许一种 `type`。`resources` 数组里出现多种类型时返回 `kind=usage`，不发写请求；按类型拆开多次调用。Web 已出现的可选项（如 `prompt`、`desc`）若经 `--set` 出现在条目上，原样放入对应 `list[]` 项。

成功时从 `--json` 读取 `data.success_count` 与 `data.success_list[]` 的 `resource_id`、`name`、`resource_type`、`status`、`file_id`。后端可能因重名改名，后续匹配以返回值为准，不要拿输入 `name` 当唯一键。

缺 `type` / `name` / `file_id`（或缺 `sp_id`）时返回 `kind=usage` 且 `raw.needs_input=true`。

### 示例

单条：

```bash
reelmate resource file-import SP_ID --set type=character --set name=林黛玉 --set file_id=FILE_ID --dry-run --json
reelmate resource file-import SP_ID --set type=character --set name=林黛玉 --set file_id=FILE_ID --idempotency-key KEY --json
```

同一资产多图时，`file_id` 仍是逗号分隔的单个字符串：

```bash
reelmate resource file-import SP_ID --set type=character --set name=贾宝玉 --set file_id=fid-2,fid-3 --json
```

批量形态与 `resource add` 相同，对象里带 `resources` 数组；同一次必须同一 `type`：

```json
{
  "resources": [
    { "type": "character", "name": "林黛玉", "file_id": "fid-1" },
    { "type": "character", "name": "贾宝玉", "file_id": "fid-2,fid-3" }
  ]
}
```

```bash
reelmate resource file-import SP_ID --set @assets.json --dry-run --json
reelmate resource file-import SP_ID --set @assets.json --idempotency-key KEY --json
```

角色需要保存为 Seedance 主体时，用返回的 `resource_id` 另调：

```bash
reelmate resource batch-confirm SP_ID --set 'resource_ids=["RESOURCE_ID"]' --set 'business_list=[3]' --json
```

## `reelmate resource extract`

### 作用

对应网页「AI智能提取资产」。创建**项目级**提取任务，返回提取主任务 `et_id`。

### 参数与输出

**不要**用画布的 `script asset-extract` 顶替。那条打到 `canvas/:canvas_id/nodes/:node_id/asset-extraction`，作用域是画布节点，不是制片工坊项目资产。`deeplink asset-extract` 只是资产确认页的兼容深链命令名，也不是提取命令。

后端路径：`POST /web/v1/df/extraction/task`。按钮主路径（前端 `useAssetExtraction.startExtraction`）：

```json
{ "sp_id": "SP_ID", "task_type": 1, "generate_mode": 1 }
```

| `--set` | 含义 | 默认 |
|---|---|---|
| `task_type` | `1` 清单提取、`2` 角色提示词、`3` 场景提示词、`4` 道具提示词、`5` 三个提示词一起 | `1` |
| `generate_mode` | `1` 专业 / `2` 快速；**只在 `task_type=1` 时生效** | `task_type=1` 时为 `1` |
| `need_voice` | `1` 需要音色 / `2` 不需要 | `task_type=5` 时默认 `1`；清单提取不传 |

支持 `--dry-run`（零写请求）与 `--idempotency-key`。

### 示例

```bash
reelmate resource extract SP_ID --dry-run --json
reelmate resource extract SP_ID --idempotency-key KEY --json
reelmate resource extract SP_ID --set task_type=1 --set generate_mode=2 --json
```

成功时 `data.et_id` 是提取主任务 ID。提取完成后仍可能要 `resource confirm` 定稿。用户已备好的提示词清单回填走 `resource draft-import`，**不得**用 `resource add` 代替提取草稿。

## `reelmate resource extract-status`

### 作用

查询项目级资产提取任务状态。

### 参数与输出

`--set et_id=ET_ID` 指定提取主任务。状态含义：`1` 进行中、`2` 成功、`3` 失败、`4` 已删除或失效。

### 示例

```bash
reelmate resource extract-status SP_ID --set et_id=ET_ID --json
```

## `reelmate resource extract-wait`

### 作用

轮询直到提取任务成功、失败或超时。只在状态 `2` 时成功退出；`3/4` 返回任务失败，超时不会重新提交。

### 参数与输出

`--set et_id=ET_ID` 指定提取主任务；`--timeout 30m` 设置等待上限。

### 示例

```bash
reelmate resource extract-wait SP_ID --set et_id=ET_ID --timeout 30m --json
```

## `reelmate resource extract-redo`

### 作用

重做失败或失效的提取任务。是写操作，只用于失败或失效任务，支持预演和幂等键。

### 参数与输出

`SP_ID` 省略时使用当前绑定。支持 `--dry-run` 与 `--idempotency-key`。

### 示例

```bash
reelmate resource extract-redo SP_ID --dry-run --json
reelmate resource extract-redo SP_ID --idempotency-key KEY --json
```

## `reelmate resource draft-import`

### 作用

创建或更新资产提取操作台的草稿，并设置主、子关系。对应前端已验证的 `POST /web/v1/df/extraction/asset/create` 与 `PUT /web/v1/df/extraction/asset`。成功后从 `--json` 读取每条 `eed_id`，供 `resource batch-draft-generate` 使用。

四条边界：

- `draft-import`：写提取草稿，返回 `eed_id`。
- `add`：写未定稿正式资产，返回 `resource_id`。**不得**用 `add` 代替本命令，也不得把 `resource_id` 传给 `batch-draft-generate`。
- `file-import`：用已上传图片创建已定稿项目资产。
- `extract*`：服务端 AI 智能提取任务生命周期，不接受用户已备好的提示词清单。

本命令不生图、不定稿、不保存 Seedance 主体。生图继续走 `batch-draft-generate`；定稿/存主体继续走 `batch-confirm`。

### 参数与输出

| 字段 | 必需 | 说明 |
|---|---|---|
| `type` | 是 | `character` / `scene` / `prop`，映射为后端 `resource_type` `1` / `2` / `3` |
| `name` | 是 | 图片名称；兼容别名 `asset_name` |
| `prompt` | 是 | 提示词原文 |
| `group_id` | 有子形态时是 | 一组资产的客户端分组键 |
| `state_id` | 有多行时是 | 行的客户端唯一键 |
| `parent_state_id` | 子形态是 | 指向同组主形态的 `state_id`；主形态必须为空 |
| `eed_id` | 否 | 出现则更新该草稿，否则创建 |

`SP_ID` 省略时使用当前绑定的工作区。写操作支持 `--dry-run` 与 `--idempotency-key`。同一次调用只允许一种 `type`；混合类型返回 `kind=usage`，不发写请求。批量数组键是 `items`，不要用 `add` / `file-import` 的 `resources`。

仅一条且无 `group_id` / `state_id` 时视为单独主形态。一组恰好一条主形态，其余为子形态；不得因名称相似自行合并，也不得默认第一行是主形态。先写完全部主形态，再用返回的主形态 `eed_id` 作为子形态 `parent_id`。主形态失败则该组子形态不提交；已成功项不回滚。

成功 stdout 的 `data.succeeded[]` 含 `state_id`、`group_id`、`eed_id`、`is_sub`、子形态的 `parent_eed_id`、`name`、`operation`（`create`/`update`）。`eed_id` 只从本命令或随后 `draft-list` 的 `--json` 读取，禁止臆造，也禁止把 `resource_id` 当作 `eed_id`。

缺 `type` / `name` / `prompt`（或缺关系字段）时返回 `kind=usage` 且 `raw.needs_input=true`。未知类型、混合类型、一组多个主形态、孤儿/跨组/循环/重复 `state_id` 均为 `kind=usage`，零写请求。

### 示例

单条主形态（先预演，再带幂等键提交）：

```bash
reelmate resource draft-import SP_ID --set type=character --set name=林黛玉 --set prompt='人物主形态提示词' --dry-run --json
reelmate resource draft-import SP_ID --set type=character --set name=林黛玉 --set prompt='人物主形态提示词' --idempotency-key KEY --json
```

带子形态时用 `items` 数组；`parent_state_id` 指向同组主形态：

```json
{
  "items": [
    {
      "group_id": "character-lindaiyu",
      "state_id": "character-lindaiyu-main",
      "type": "character",
      "name": "林黛玉",
      "prompt": "人物主形态提示词"
    },
    {
      "group_id": "character-lindaiyu",
      "state_id": "character-lindaiyu-smile",
      "parent_state_id": "character-lindaiyu-main",
      "type": "character",
      "name": "林黛玉-微笑",
      "prompt": "人物微笑子形态提示词"
    }
  ]
}
```

```bash
reelmate resource draft-import SP_ID --set @assets.json --dry-run --json
reelmate resource draft-import SP_ID --set @assets.json --idempotency-key KEY --json
```

成功后只把 `data.succeeded[]` 里主形态的 `eed_id` 交给生图（占位符来自上一步 `--json`，不要手写）：

```bash
reelmate resource batch-draft-generate SP_ID --set res_type=1 --set 'eed_ids=["MAIN_EED_ID"]' --set @image-params.json --json
```

已有草稿时带上一步返回或 `draft-list` 读到的 `eed_id` 走更新，不因同名再创建：

```bash
reelmate resource draft-import SP_ID --set type=character --set name=林黛玉 --set prompt='更新后的提示词' --set eed_id=EXISTING_EED_ID --json
```

## `reelmate resource draft-list`

### 作用

列出提取任务中的资产草稿并返回 `eed_id`。默认只返回主形态；显式启用全形态查询时，主形态和子形态在 `data.list[]` 中平铺返回。资产确认页的待生成条目是提取草稿，不在 `resource list` 的正式资产库里。

### 参数与输出

`--set resource_type=1|2|3`：`1` 角色、`2` 场景、`3` 道具。默认查询全部剧集（`episode_num=0`）、单页 500 条主形态（接口默认 20，这里与 Web 对齐）；`EED_ID` 取返回 `data.list[].eed_id`。查询回包 `prompt` 可能为空；不要用空 prompt 判断草稿未就绪。生图只传 `eed_id`。主形态生图只使用默认查询的顶层条目。

默认只取第一页，`--set page=N` 逐页取、`--set page_size=N` 改单页条数、`--set all=true` 按服务端总数一次取完；输出带 `count`、`page`、`page_size`、`has_more`、`next_page`，`has_more=true` 时不要当成全量用。

查询全部形态时同时传 `--set appearance_order=1 --set is_all=true`。`is_all` 必须是 JSON 布尔值 `true`，不能传数字 `1`。当前接口不返回嵌套 `sub_list`；全形态结果为平铺列表，子形态通过非空且非 `"0"` 的 `main_eed_id` 指向父形态 `eed_id`。

### 示例

```bash
reelmate resource draft-list SP_ID --set resource_type=1 --json
reelmate resource draft-list SP_ID --set resource_type=2 --json
reelmate resource draft-list SP_ID --set resource_type=3 --json
reelmate resource draft-list SP_ID --set resource_type=1 --set appearance_order=1 --set is_all=true --json
```

定稿不会让草稿形态从全形态查询中消失；待定稿和已定稿分别通过 `resource_generate_preview.preview_status=4|5` 区分。正式资产结果不保留 `main_eed_id`，需要父子关系的调用方应基于全形态查询另行保存映射。

## `reelmate resource batch-draft-generate`

### 作用

按角色、场景或道具批量生成草稿主形态图片。去掉 `--dry-run` 后真实调用 `POST /web/v1/df/resources/batch-draft-generate`。

### 参数与输出

`res_type`：`1` 角色、`2` 场景、`3` 道具。必须传非空 `eed_ids`。本命令不接收 prompt，请求体不含该字段；查询 `prompt` 为空时仍只传 `eed_id` 下单。模型、清晰度、画幅和数量按在线 `model list --json` 的 `params.generation.text2image` 校验；缺省值取所选模型规则，`width/height` 由 CLI 按 Web 尺寸表自动计算。`alg_code` 默认 `text_to_image`，`images` 默认空数组；角色构图未指定时不传 `generate_image_type`。任务状态通过重新执行 `draft-list` 读取 `resource_generate_preview.preview_status`：`1` 未生成、`2` 失败、`3` 生成中、`4` 未定稿、`5` 已定稿。

**`style_uk_id`/`theme_uk_id` 必须传成带引号的 JSON 字符串**，例如 `--set 'style_uk_id="17"'`；写成裸值 `--set style_uk_id=17` 会被 `--set` 解析成数字，不管取值大小，后端一律拒绝为 `740011 Parameter error`，且报错信息看不出是这两个字段的问题。

### 示例

```bash
reelmate resource batch-draft-generate SP_ID \
  --set res_type=1 \
  --set 'eed_ids=["EED_ID"]' \
  --set ai_model_mark=gpt_image_2.0 \
  --set resolution=2K --set radio_ui=16:9 --set qty=1 \
  --set 'style_uk_id="STYLE_UK_ID"' --set 'theme_uk_id="THEME_UK_ID"' \
  --dry-run --json
```

`--dry-run --json` 的 `data.credits_estimate` 可原样交给 `credits estimate`。其中 `business_count` 等于本批 `eed_ids` 数量，`qty` 是每个资产的生成图片数，两者不得混用。去掉 `--dry-run` 后真实调用 `POST /web/v1/df/resources/batch-draft-generate`。

## `reelmate resource prompt-complete`

### 作用

对应 Web 端资产匹配页的“从剧本补全提示词”，调用 `POST /web/v1/df/extraction/script-prompt/task`。它只为指定的未匹配占位项生成并回填视觉提示词，**不会创建项目资产，也不会把该项变成已匹配**。单独调用本命令时，完成后仍需重新检查资产匹配结果。GUI 四环节的“智能补充缺失资产”例外地在用户一次确认后编排完整链路：`prompt-complete-result` 逐项校验出非空有效 `visual_prompt` 后自动承接生图、定稿和匹配关系回写，不在提示词成功后再询问是否生图。

### 参数与输出

位置参数为 `EP_ID`，项目 ID 来自 `--workspace SP_ID` 或当前绑定工作区。`target_assets` 必须是非空数组，每项只接受：`resource_type`（`1` 角色、`2` 场景、`3` 道具）、非空 `name`、可选 `resource_id`。CLI 固定提交 `source=2` 和当前单集 `ep_ids=[EP_ID]`，用户不能覆盖这些路由字段。写操作支持 `--dry-run` 和 `--idempotency-key`。

成功响应将 `apt_id` 提升到顶层输出。Web 当前按每个可执行选中资产暂估 1 积分，但源码注明该规则尚未最终定价。确认前执行 `credits estimate --set scenario=asset_prompt_completion --set selected_actionable_count=N --json`；账单返回 `source=provisional`，用户可见文案必须写「暂估消耗」并展示原因，不能写成正式报价。

### 示例

```bash
reelmate resource prompt-complete EP_ID --workspace SP_ID \
  --set 'target_assets=[{"resource_type":1,"name":"林黛玉","resource_id":"-1"},{"resource_type":2,"name":"大观园","resource_id":"-1"}]' \
  --dry-run --json
reelmate resource prompt-complete EP_ID --workspace SP_ID \
  --set 'target_assets=[{"resource_type":1,"name":"林黛玉","resource_id":"-1"}]' \
  --idempotency-key KEY --json
```

## `reelmate resource prompt-complete-result`

### 作用

调用 `GET /web/v1/df/extraction/script-prompt/episode-tasks?sp_id=...&ep_id=...`，查询该集已有的提示词补全任务及逐项结果。该接口可能返回多次历史任务；同一 `resource_type + name` 重复出现时，以最新任务中的结果为准。

任务 `status`：`1` 处理中、`2` 成功、`3` 失败。逐项 `item_status`：`1` 处理中、`2` 已成功应用、`3` 待审核但已有候选（Web 同样按成功结果使用首个有效候选）、`4` 失败。完成判定除状态外还要验证所选项存在非空 `candidates[0].visual_prompt`；只看任务顶层成功不足以证明每个目标都有可用提示词。

```bash
reelmate resource prompt-complete-result EP_ID --workspace SP_ID --json
```

## `reelmate resource match-reset`

### 作用

重置剧集的资产匹配结果，匹配失败后重跑用。该动作会替换当前匹配结果，执行前必须先预演并由用户确认。

### 参数与输出

**位置参数是剧集 ID（`EP_ID`），不是项目 ID（`SP_ID`）** —— 这条与本命令组其它子命令不同，容易搞反。也可用 `--set ep_id=EP_ID` 传入；请求 body 必须同时携带当前工作区的 `sp_id`，CLI 会自动注入。写操作支持 `--dry-run` 与 `--idempotency-key`。

### 示例

```bash
reelmate resource match-reset EP_ID --workspace SP_ID --json
reelmate resource match-reset EP_ID --workspace SP_ID --dry-run --json
```

`reelmate subject reset --set kind=match` 与本命令共用同一条后端路径，实现上共用同一处常量；两条命令并存是有意的，一条从资产视角进入、一条从主体视角进入。解析重置（`parse-reset`）是**另一个动作**，走 `subject reset --set kind=parse`。

## `reelmate resource voice-desc`

保存角色音色描述。已入库角色走 `POST /web/v1/df/resources/bind-audio` 的 `audio_prompt`。只有提取草稿时走 `PUT /web/v1/df/extraction/asset` 的 `audio_detail`。`RESOURCE_ID` 和 `eed_id` 只能给一个。

手写 `audio_prompt` 先去掉首尾空白。超过 200 字直接拒绝，不发请求。空字符串跳过文本审核并保存，用来清空描述。非空描述先 `POST /web/v1/text-sensidetect`，只有 `risk_level=PASS` 才保存。

`--set uk_id=` 与 `audio_prompt` 互斥。命令在官方和团队启用模板里找到 `prompt_template`，截到 200 字后走同一条文本保存。

已入库角色未传 `sync_sub` 时，查询带 `is_include_sub_form=1`、`is_all=true`、`appearance_order=1` 的角色草稿。嵌套 `sub_list` 或平铺列表里 `main_eed_id` 指向该主形态的子项，只要已有 `resource_id` 就传 `sync_sub=true`，否则不传。`--set sync_sub=false` 关掉，`--set sync_sub=true` 强制同步。草稿更新不接受 `sync_sub`。

### 示例

```bash
reelmate resource voice-desc SP_ID RESOURCE_ID --set audio_prompt='男，20岁左右，嗓音沙哑' --json
reelmate resource voice-desc SP_ID --set eed_id=EED_ID --set audio_prompt= --json
reelmate resource voice-desc SP_ID RESOURCE_ID --set uk_id=UK_ID --dry-run --json
```

## `reelmate resource voice-audio`

绑定角色参考音频。本地文件是位置参数 `FILE`，只接受 mp3 或 wav，不超过 15MB。读不出时长时拒绝，不上传。短于 3 秒或长于 30 秒拒绝。3 到 5 秒直接上传后绑定。超过 5 秒且不超过 30 秒必须同时给 `--set start=` 和 `--set end=`，区间长度 3 到 5 秒；命令先上传原文件，再 `POST /web/v1/ai/audio-slicing`，等裁切任务返回新的 `file_id` 后绑定。

已有最终文件用 `--set audio_file_id=`，与 `FILE` 互斥。文本描述和参考音频分两次保存，一次请求只带其中一种。

已入库角色的 `sync_sub` 规则与 `voice-desc` 相同。`--dry-run` 只做本地校验并预览，不上传、不裁切、不保存。

### 示例

```bash
reelmate resource voice-audio SP_ID RESOURCE_ID voice.wav --json
reelmate resource voice-audio SP_ID RESOURCE_ID voice.mp3 --set start=2 --set end=6 --json
reelmate resource voice-audio SP_ID --set eed_id=EED_ID --set audio_file_id=FILE_ID --json
```

## `reelmate resource voice-library list`

列出音色描述模板。官方请求带 `scene=14`、`use_type=1`、`status=1`；团队请求带 `scene=14`、`status=1`。`--set source=official|team` 只查一边，省略时两边合并，每条带 `source`。`lang` 只在传入时发送。默认第一页 50 条，`--set all=true` 翻完。

这是提示词模板，不是 `voice list` 的 TTS 音色目录。选用模板后用 `voice-desc --set uk_id=` 保存。

### 示例

```bash
reelmate resource voice-library list --set source=official --json
reelmate resource voice-library list --set source=team --set lang=zh-CN --set all=true --json
```

## 注意事项

- `SP_ID`（制片工坊项目 ID）与工作区、画布、剧集 ID 是不同实体，不能混用。
- `resource_id`（项目资产）、`uk_id`（资产库资产）、`info_id`（分镜素材）是三层不同实体的 ID，参数传错会写到错误的实体层上。
- `resource file-import` 与 `resource import` 不是同一条命令：前者消费 `file_id` 创建已定稿项目资产，后者只做资产库互导。
- 不得把 `file_id` 传给 `resource add` 冒充挂图或定稿。
- `resource draft-import` 写提取草稿并返回 `eed_id`；`resource add` 不能代替它。`batch-draft-generate` 只能用返回的 `eed_id`，不能用 `resource_id`。
- `resource voice-desc` 和 `resource voice-audio` 保存的是角色音色。`voice list` 是 TTS 音色目录，不能用来改角色描述。`voice-library list` 只列出模板，不保存。
- 发布态以当前二进制帮助、本命令页和结构化错误为执行依据；未登记的字段不得猜测。
- 所有 ID 都要从上一步命令的 `--json` 返回里读取，不要凭记忆或从表格文本猜。
