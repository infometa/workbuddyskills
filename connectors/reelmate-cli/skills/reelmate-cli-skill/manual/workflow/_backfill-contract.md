# 回填契约

给模型读。资产三类与分镜行的最小必填字段只写在本文；代码校验必须与这些表一致。参数细节见 `commands/resource.md`、`commands/storyboard.md`。

发布态以当前二进制帮助、本 Skill 和命令文档为契约。所有 ID 一律从上一步 `--json` 读取。缺字段时 CLI 返回 `error.raw.needs_input=true`；由宿主 Agent 按 `missing[]` 提问，CLI 不做 TUI。

## 规整规则（三类资产与分镜共用）

1. 自由文本先拆成行或对象，再填表。不能从散文直接 POST；资产提示词 Excel 必须先由 `resource prompt-sheet-read` 读取、校验并转换。
2. 用户说「角色沈赫」→ `type=character`，`name=沈赫`。说「场景旧宅」→ `type=scene`，`name=旧宅`。说「道具信笺」→ `type=prop`，`name=信笺`。
3. GUI 分镜视频回填只接收官方三列分镜提示词表（`.xlsx` 或 `.xlsm`）；先用 `storyboard sheet-read` 读取并校验，不要求用户手工制作 JSON。用户没有现成表时，用 `storyboard prompt-template` 生成空表。用户回传自带清单对不上三列时，由 Agent 转写成官方表后再 `sheet-read`，不要把空模板甩回去让用户重填。
4. 缺必填字段：停，按该字段「缺时问」提问，不要猜默认值。
5. 资产对象中未列的多余字段默认透传；命令文档明确给出字段白名单的接口按白名单发送。
6. 批量写入先 `--dry-run --json`，确认后再 `--idempotency-key` 提交。

## 资产提示词 Excel 的 CLI 实时生成与解析

Agent 每次进入资产提示词回填流程时调用 `resource prompt-template OUTPUT.xlsx`。CLI 使用随二进制发布的 Go 代码实时生成新的 `.xlsx`，保存到本次任务输出目录；Skill、CLI 源码及构建产物中都不保存静态模板文件。`prompt-sheet-read` 认官方五列表头，也认四列方言：`资产类型`、`资产名称`、`主子资产属性`（或 `形态`）、`生图提示词`（或 `提示词`）。`主`/`子` 视为 `主形态`/`子形态`。无「所属主形态名称」列时，子形态按名称前缀绑定主形态。CLI 不改用户原文件。

用户回传的可以是填好的官方表，也可以是自带资产清单（列名、Sheet 名、分页都可能不同）。官方五列与上述四列方言可直接 `prompt-sheet-read`。其它对不上官方列时，**禁止**把空模板甩回去让用户重填；由 Agent 把用户表转写成官方模板后再调用 `resource prompt-sheet-read ASSETS.xlsx`。CLI 读取「资产提示词清单」及其它业务 Sheet，校验并返回可直接用于后续 `resource add` / `resource generate` 的 `data.batches[]`。

转写只搬用户表里已有的字。不能编资产名称或提示词，不能默认第一行是主形态，不能按名称相似合并行。形态列整表缺失时问一次「全部按主形态还是由你标主子」，不要默填主形态。多余列可丢弃；多个描述列可原样拼接进「提示词」，拼接的必须是单元格原文。

模板生成器与解析器共享 `internal/assetprompt` 中的列定义、类型映射和主子形态规则，代码是工作簿结构的事实来源；下表描述 CLI 对外字段语义，供 Agent 处理 `needs_input` 和后续批次。

| 模板列 | 必填规则 | 转换规则 | 缺时问 |
|---|---|---|---|
| `资产类型（必填）` | 每行必填 | `角色` → `character`，`场景` → `scene`，`道具` → `prop` | 这是角色、场景还是道具？ |
| `资产名称（必填）` | 每行必填 | 写入 GUI 图片名称 `name` | 这张图片叫什么名字？ |
| `形态（必填）` | 每行必填 | `主形态`/`主` 的 `parent_state_id` 为空；`子形态`/`子` 指向所属主形态 | 这是主形态还是子形态？ |
| `所属主形态名称（子形态必填）` | 子形态必填，主形态留空；四列方言可省略本列 | 已填则在同类型内精确匹配唯一主形态；未填则去掉子名称末尾 `（…）`/`(...)` 得前缀，同类型主形态名称恰好一条以此前缀开头则绑定，0 或 ≥2 条时追问 | 这个子形态属于哪个主形态？ |
| `提示词（必填）` | 每行必填 | 原样写入 `prompt` | 这张图片的提示词是什么？ |

生成的工作簿至少包含两个 Sheet：「资产提示词清单」提供空白填写区，并为资产类型设置 `角色/场景/道具` 下拉、为形态设置 `主形态/子形态` 下拉；「填写示例」展示角色、场景、道具及主子形态关系，只供参考，不作为待提交数据。用户可以复制填写 Sheet 分页录入；未指定 `--set sheet` 时，CLI 按工作簿顺序汇总全部业务 Sheet，跳过「填写示例」和没有数据的空白 Sheet。

同一类型内主形态名称必须在整个工作簿中唯一。子形态可以跨 Sheet 引用，但必须能按“同一资产类型 + 主形态名称”精确匹配全工作簿中唯一的一条主形态；四列方言未填所属主形态时改走名称前缀唯一匹配。缺失、重复、跨类型引用、子形态引用子形态、或前缀 0/多匹配时，CLI 返回 `needs_input` 并列出 Sheet 与行号。CLI 为每组生成稳定的 `group_id`，为每行生成唯一的 `state_id`；这些是技术字段，不改变业务术语“主形态/子形态”。

## character 必填字段

| 字段 | 必填 | 缺时问 |
|---|---|---|
| type | 是 | 这是角色、场景还是道具？（取值必须是 `character`） |
| name | 是 | 这个角色叫什么名字？ |

## scene 必填字段

| 字段 | 必填 | 缺时问 |
|---|---|---|
| type | 是 | 这是角色、场景还是道具？（取值必须是 `scene`） |
| name | 是 | 这个场景叫什么名字？ |

## prop 必填字段

| 字段 | 必填 | 缺时问 |
|---|---|---|
| type | 是 | 这是角色、场景还是道具？（取值必须是 `prop`） |
| name | 是 | 这个道具叫什么名字？ |

`type` 只允许 `character` / `scene` / `prop`。写入命令：`reelmate resource add SP_ID --set @assets.json --dry-run --json`。

## 角色构图 `generate_image_type`

资产批量生图的角色构图由 CLI 源码 `studio.GenerateImageTypes()` 定义，Web 没有独立目录接口。HITL 前现查：

```bash
reelmate resource generate-image-types --json
```

只使用返回的 `data.list[]`：必须列出全部 `name`，`recommended=true` 的项写成 `特写+主视图（推荐）`，并原样写入 `--set generate_image_type=`。查询命令不返回数字取值。只用于角色请求，主形态和子形态都必须传；场景和道具不传。未指定时 CLI 不传该字段。风格走 `preset-list` 的 `res_type=1/2/3` 三次查询，问用户只列一份展示名；提交各类 `style_uk_id` 按所选名称在该类 `list[]` 匹配。题材走 `kind=theme` 一次查询，提交 `theme_uk_id`。问用户也只写名称。`style_uk_id` / `theme_uk_id` 必须带引号传成 JSON 字符串；裸数字会触发后端 `740011`。

## storyboard 必填字段

本表只约束 `storyboard batch-add` 创建正式空白分镜的接口，不用于提示词回填。

| 字段 | 必填 | 缺时问 |
|---|---|---|
| num | 是 | 这一镜的镜号是多少？ |

写入命令：`reelmate storyboard batch-add EP_ID --set @shots.json --dry-run --json`。该命令只发送前端 `storyboard-add` 接受的 `num`、可选 `name` 和可选 `desc`；出现 `prompt`、`refs`、`duration` 或 `images` 时会拒绝并引导到 `storyboard draft-import`。

## 分镜视频 Excel Sheet 与必填项

官方格式为单表三列。Agent 需要空表时调用 `storyboard prompt-template OUTPUT.xlsx`。CLI 使用随二进制发布的 Go 代码实时生成新的 `.xlsx`，保存到本次任务输出目录；Skill、CLI 源码及构建产物中都不保存静态模板文件。`sheet-read` / `draft-import` 默认跳过「填写示例」，只认「分镜提示词清单」和其它业务 Sheet。CLI 不改用户原文件。

用户回传的可以是填好的官方表，也可以是自带分镜清单（列名、Sheet 名、分页都可能不同）。对不上官方三列时，**禁止**把空模板甩回去让用户重填；由 Agent 把用户表转写成官方模板后再调用 `storyboard sheet-read SHOTS.xlsx`。

转写只搬用户表里已有的字。不能编剧集号、分镜号，不能默认整表属于第 1 集，不能按镜号或文案相似合并行。剧集号、分镜号缺失时可智能补齐并写入单元格。剧集号列整表缺失时问一次「本表全部属于第几集，还是由你逐行标集号」，不要默填第 1 集。

**表头**：必须映射出剧集号、分镜号、视频提示词；无视频提示词语义列时停止并请用户补充。**除剧集号、分镜号、视频提示词、时长列外**，其它列告知用户本次不会使用。

**视频提示词**：不作格式要求。单一提示词列原样复制；多个画面描述列默认按列序 **直接拼接单元格原文**（不插入列名、分隔符、标签或任何额外字符）。禁止为写时长而把内容拼进视频提示词。

**时长**：场景一——`sheet-read` 读单独「时长」列（若有）或从提示词解析；场景二——文件无任何时长时向用户索取整批默认值，`draft-import --set duration=`。

十列「表格样式分镜单」走转写，不要当官方表硬读。`.csv` / `.tsv` 不兼容。

一个工作簿可以在同一 Sheet 里写多集；`剧集号` 决定 `episode_no`。`--set sheet=` 只用于缩小到一个 Sheet。

| 规范列 | 模板表头 | 必填规则 | 缺时问 |
|---|---|---|---|
| `episode_no` | `剧集号` | 每行必填，接受 `第1集` / `第一集` / `1` | 这一镜属于第几集？ |
| `shot_no` | `分镜号` | 每行必填；接受 `1`/`2`/`3`、`01`/`02`/`03` 或 `1-01` | 这一镜的镜号是多少？ |
| `prompt` | `视频提示词` | 每行必填；转写时原样复制或按规则拼接描述列 | 这一镜的视频提示词是什么？ |
| `duration` | `时长`（用户表可选列，非官方模板表头） | 可选；`8` / `8秒` 等；`sheet-read` 优先于提示词内解析 | 这一镜时长多少秒？ |

同一集内 `shot_no` 必须唯一。`1` 与 `01` 视为同一镜号。写成 `1-01` 时前半段必须与该行 `剧集号` 一致。

## 分镜视频提示词内嵌字段

| 规范列 | 提示词中的时长 / 资产 | 规则 |
|---|---|---|
| `duration` | 提示词里含可解析的秒数即可 | CLI 按优先级抽取：`【时长】N秒` → `时长N秒` / `时长：N秒` / `视频时长N秒` → 首个 `N秒`；`sheet-read` 保留正整数原值；`draft-import --set ai_model_mark=MODEL` 按 Web 模型规则调整到最近合法档位并保留 `original_duration`，同距取较低档；未传模型时仍按通用 4 至 15 秒约束 |
| `asset_names` | 可选显式名单 | 可从 `【参考资产】名称`、`参考资产：名称` 等抽取，多个名称用逗号、顿号、分号或换行分隔；显式名单必须能唯一确定 `resource_id` 和 `file_id` |

没有解析到显式参考资产名单时，CLI 从整段提示词中匹配项目内已定稿资产名称。显式名单无匹配、重名、未定稿或无图片时返回 `needs_input`，不提交写请求。无显式名单且提示词也匹配不上已定稿资产时，仍写入原样提示词和空 `images`，留给后续 `storyboard match-assets`。

```bash
reelmate storyboard sheet-read SHOTS.xlsx --json
reelmate storyboard draft-import EP_ID --workspace SP_ID \
  --set file=SHOTS.xlsx --set episode_no=1 --dry-run --json
```

`draft-import` 将资产按表内顺序转换为前端草稿的 `images`，并把提示词中的资产名称替换为对应 `[[@imgN]]` 标记。新增草稿调用 `script_draft/add`，已有草稿调用 `script_draft/{esd_id}/edit`。
