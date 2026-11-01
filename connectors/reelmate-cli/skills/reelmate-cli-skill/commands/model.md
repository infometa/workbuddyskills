# model

查询当前空间的模型目录、可见性、参数提示和定价。查询结果只返回展示名，不含 `id` / `ai_model_mark`。生成命令的 `--set ai_model_mark=` 填写展示名，由 CLI 解析后再提交。

## 用法

```text
reelmate model list [TYPE] [--type file|image|video|audio] [--sp-type 1|2] [--offline-models]
reelmate model search KEYWORD [--sp-type 1|2] [--offline-models]
reelmate model price [--offline-models]
reelmate model params image|video MODEL_NAME
reelmate model params audio
```

## 子命令说明

| 命令 | 作用 |
|---|---|
| `reelmate model list` | 列出当前可用模型目录 |
| `reelmate model search KEYWORD` | 按关键词筛选模型目录 |
| `reelmate model price` | 查看模型定价 |
| `reelmate model params` | 查看 CLI 与 Web 同源的图片、视频或音频生成参数规则；不登录、不判断账号可见性 |

## `reelmate model list`

### 作用

查询当前空间的可用模型目录。CLI 内置目录迁移自 Web 画布的 `useCanvasModels.ts`、`modelConfig.ts`、`configs/*.ts` 与中文模型文案，在线结果再合并 `page_init` 显式可见性、团队模型能力、项目类型和定价；`script_llm_models` 只能补充已登记模型的剧本拆分镜元数据，不能创建新的画布候选。省略类型时返回全部当前可用模型。

### 参数

- `TYPE`：可选模型类型，支持 `file`、`image`、`video`、`audio`；也可用 `--type` 传入，二者不能同时使用。
- `--type file|image|video|audio`：按文件、图片、视频或音频模型过滤；`text`、`文本` 作为 `file` 的兼容别名。
- `--sp-type 1|2`：模型目录分类，`1` 为 2D/3D 动漫、`2` 为真人。它不是 `workspace create` 的完整剧目类型枚举：国内/海外真人项目都使用 `2`。
- `--offline-models`：显式使用本地静态目录，不访问远端模型源。
- `--json`：输出 JSON。

### 输出

表格只含 `NAME`、`TYPE`、`VISIBLE`、`METADATA_MISSING` 和 `PRICE`。JSON 同样不含 `id` / `ai_model_mark` / `raw` / `pricing_aliases`。HITL 和提交都只用展示名。多能力模型的 `TYPE` 以逗号分隔。JSON 的主要字段如下：

| 字段 | 含义 |
|---|---|
| `name` / `display_name` | 展示名称；生成命令的 `--set ai_model_mark=` 填这个值 |
| `type` / `types` | 模型支持的文件、图片、视频或音频能力 |
| `visible` | 当前可见性；`model list` 只返回值为 `true` 的可用模型 |
| `supported_modes` | 模型支持的画布生成模式，例如 `text2image`、`universal_reference` |
| `mode_order` | 该模型在各 Web 模式清单中的下标，从 `0` 开始；筛完后按目标模式升序朗读，不要按 mark 字母序 |
| `vendor` | Web 模型配置中的厂商/品牌归属 |
| `logo` | Web `ModelItem.logoUrl` 对应的稳定资源键（不内嵌图片二进制） |
| `description` | Web 中文模型说明 |
| `need_vip` | Web 模型项是否标记为会员模型 |
| `tags` / `activity_tags` | 时长、音频、口型、活动等 Web 展示标签 |
| `max_image_num` | Web `ModelItem` 声明的参考图上限 |
| `audio_video_support` | 是否支持音画同出 |
| `is_new` / `is_hot` / `promotions` | Web 模型项的运营标记 |
| `price` | `default_show` 规格的价格；没有默认规格时取第一档，无价格时为 `null` |
| `price_variants` | 全部价格规格，保留分辨率、时长及原价、会员价、限时价 |
| `params` | CLI 当前版本内置的参数提示；`generation.<mode>` 给出 Web 同款的接口、默认值、合法枚举、提示词和素材上限，分镜专用参考生视频规则仍保留在 `storyboard_reference_video`。分辨率 HITL 读 `resolution_options` 的 `label`，提交值仍是 `value` |
| `metadata_missing` | CLI 是否缺少该模型的本地补充元数据；不表示模型不可用 |

每档价格优先取定价配置的 `member_price`，缺失时依次回退到 `time_limited_price`、`original_price`；顶层 `price` 优先选择 `default_show=true` 的规格，没有价格时表格显示 `-`。定价配置使用独立的计费 SKU 命名，CLI 在内部关联到画布模型，不要把计费 SKU 当成模型展示名。

### 示例

```bash
reelmate model list --sp-type 2 --json
reelmate model list --type image --sp-type 2 --json
```

## `reelmate model search KEYWORD`

### 作用

按关键词筛选模型。

### 参数

- `KEYWORD`（必填）：展示名称或说明关键词。
- `--sp-type 1|2`、`--json`：模型目录分类和输出格式；映射规则同 `model list`。

### 输出

返回匹配模型的展示名和可见字段，不含提交标识。

### 示例

```bash
reelmate model search seedance --sp-type 2 --json
```

## `reelmate model price`

### 作用

查询模型价格配置。

### 参数

- `--offline-models`：显式使用本地静态目录，不访问远端价格源。
- `--json`：输出 JSON。

### 输出

返回 `price` 非空的模型条目，字段结构与 `model list --json` 一致。

定价来自远程配置。在线模式下如果定价源不可用，命令会明确报告；使用 `--offline-models` 时不会访问远程价格，若本地静态目录没有价格则返回空价格列表并给出提示。

### 示例

```bash
reelmate model price --offline-models --json
```

## `reelmate model params`

查看某个模型各生成模式的完整静态规则。图片和视频必须传展示名；音频不传模型，因为 Web 实际按 `audioKind` 路由到旁白、配乐或音效接口。

```bash
reelmate model params image 'TGI 2' --json
reelmate model params video 'Vidu Q2' --json
reelmate model params audio --json
```

返回的 `generation.<mode>` 包含 `endpoint`、默认及可选 `ratio`、`resolution`、`duration`、`count`，以及参考图片、视频、音频数量限制。该命令用于离线查看内置规则；账号可见性和 Seedance 分辨率开白必须以在线 `model list --json` 返回条目的 `params.generation` 为准。

## 从目录到生成

1. **查询**：生成前按媒体类型和项目类型执行在线 `model list --json`，将结果快照限制在当前执行中使用。
2. **选择**：从返回条目读取 `name`，并确认目标生成方式包含在 `supported_modes` 中。不要读取或向用户展示 `id` / `ai_model_mark`。
3. **校验**：读取 `params.generation.<mode>`；它已经按 Web 规则给出默认值、合法枚举、素材数量和账号级分辨率过滤。分镜批量参考生视频还可读取专用的 `params.storyboard_reference_video`。不得假设所有模型共享同一组时长、分辨率、画幅或输入模态。
4. **提交**：把选定的展示名传给 `--set ai_model_mark=`。图片和视频的字段、默认值及完整示例统一见 [node generate](node.md#reelmate-node-generate-node_type)。模型不可见或参数校验失败时重新查询目录，再按新结果提交。

```bash
reelmate model list --type image --sp-type 2 --space SPACE_ID --json
reelmate node generate image --canvas CANVAS_ID --workspace WORKSPACE_ID --space SPACE_ID \
  --node NODE_ID --set ai_model_mark='TGI 2' --set prompt='日出时的城市' --json
```

## 离线回退

远端目录不可用时，只有显式传入 `--offline-models` 才使用静态目录。离线结果用于恢复基本模型发现能力，不代表当前线上账号的完整可见性；恢复联网后重新执行在线查询。

## 注意事项

- HITL 与 `--set ai_model_mark=` 只使用 `model list` / `model search` 返回的展示名；不要读取或向用户展示 `id`、`ai_model_mark` 或计费 SKU。
- 账号可见性、Seedance 分辨率开白和当次合法枚举以**在线** `model list --json` 为准；`model params` 与 `--offline-models` 不能代替在线目录。
- 剧厂推荐画幅/分辨率/时长是工作流口径，必须在该次所选模型对应 `params.generation.<mode>` 中校验通过后再展示；细则见 [manual/workflow/_models.md](../manual/workflow/_models.md)。
- 分镜批量参考生视频除 `generation` 外还可读 `params.storyboard_reference_video`；与画布单点生成的字段边界见 [node generate](node.md#reelmate-node-generate-node_type)。
