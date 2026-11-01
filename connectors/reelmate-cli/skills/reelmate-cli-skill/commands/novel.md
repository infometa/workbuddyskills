# novel

管理 GUI 剧本项目。`novel` 使用独立的 `NT_ID` 标识剧本项目，不使用画布节点 ID、工作区 ID 或剧集 ID。

## 用法

```text
reelmate novel config [--json]
reelmate novel create --name NAME --set key=value ...
reelmate novel analyze FILE
reelmate novel direct FILE [--name NAME] [--set key=value ...]
reelmate novel derive FILE [--name NAME] --set episode_count=N [--set key=value ...]
reelmate novel derive --nt-id SOURCE_NT_ID --name NAME --set episode_count=N [--set key=value ...]
reelmate novel overseas FILE [--name NAME] --set episode_count=N [--set key=value ...]
reelmate novel overseas --nt-id SOURCE_NT_ID --name NAME --set episode_count=N [--set key=value ...]
reelmate novel list [--set key=value ...]
reelmate novel get NT_ID
reelmate novel idea list NT_ID
reelmate novel idea set NT_ID NI_ID
reelmate novel character NT_ID
reelmate novel material NT_ID
reelmate novel material list NT_ID
reelmate novel material set NT_ID NM_ID
reelmate novel outline NT_ID
reelmate novel chapter NT_ID
reelmate novel episode NT_ID
reelmate novel script NT_ID
reelmate novel finalize NT_ID
reelmate novel rename NT_ID --name NEW_NAME
reelmate novel delete NT_ID
```

## 子命令说明

| 命令 | 作用 |
|---|---|
| `reelmate novel config` | 查询原创剧本创建所需的真实配置选项 |
| `reelmate novel create` | 创建原创剧本项目并启动创意规划方案生成 |
| `reelmate novel analyze` | 上传小说并从内容分析开始改编 |
| `reelmate novel direct` | 上传小说、提交改编设定并直接开始改编 |
| `reelmate novel derive` | 从已有剧本或本地剧本进行创意裂变 |
| `reelmate novel overseas` | 从已有剧本或本地剧本转换海外剧本 |
| `reelmate novel list` | 查询当前账号可见的剧本项目 |
| `reelmate novel get` | 查询一个剧本项目的详情 |
| `reelmate novel idea list` | 查询原创创意规划方案列表 |
| `reelmate novel idea set` | 选定一条原创创意规划方案 |
| `reelmate novel character` | 触发原创核心角色生成 |
| `reelmate novel material` | 触发原创剧本素材生成 |
| `reelmate novel material list` | 查询原创剧本素材列表 |
| `reelmate novel material set` | 选定一条原创剧本素材 |
| `reelmate novel outline` | 触发原创剧本总纲及设定生成 |
| `reelmate novel chapter` | 触发原创剧本分卡章纲生成 |
| `reelmate novel episode` | 触发原创剧本集纲生成 |
| `reelmate novel script` | 触发原创分集剧本生成 |
| `reelmate novel finalize` | 定稿并完成剧本改编 |
| `reelmate novel rename` | 修改一个剧本项目的名称 |
| `reelmate novel delete` | 删除一个剧本项目 |

## `reelmate novel config`

### 作用

查询剧本创建所需的服务端配置。命令读取 `ai_original_noval`、`rmai_novel_audience_config`、`three_dimensional_genre_options`、`three_dimensional_genre_foreign_options`、`genre_highlight_config_list`、`direct_script_adaptation_level_list` 和 `ai_noval_overseas_adaptation`，用于取得原创、小说直改、创意裂变和海外改编所需的真实选项对象。

### 参数与输出

| 参数 | 必填 | 说明 |
|---|---:|---|
| `--json` | 否 | 按配置键输出完整配置；配置值中的 JSON 字符串会解码为对象或数组 |

默认输出为选项表格，每行是一个选项对象，包含 `CONFIG_KEY`、`GROUP`、`RES_ID`、`VALUE`、`NAME` 和 `DESC`。`CONFIG_KEY` 表示选项来源，`GROUP` 对应创建参数分组；嵌套选项会逐行展开，不会压成一列 JSON。配置只提供 `value` 时，表格会按网页端规则将该值同时显示为 `RES_ID`，可直接用于创建参数。

### 示例

```bash
reelmate novel config
reelmate novel config --json
```

配置结构可能随站点、语言和后端发布变化。创建剧本前应使用当前命令结果中的完整选项对象，不要根据展示名称自行编造 `res_id` 或 `value`。

网页端不会展示 `res_id`，但提交时仍会携带选项对象。默认选择规则如下：剧本类型和受众优先选择 `is_default=true` 的配置项，否则使用第一项；题材、情绪和故事模式优先选择 `value=0` 或 `value=AUTO` 的自动项，否则使用第一项。`AUTO` 只属于后三类选项，不能用作 `script_format.value`。国内剧的稳定 `script_format.value` 是字符串 `"1"`。

## `reelmate novel create`

### 作用

创建原创剧本项目。创建请求会同时启动创意规划方案生成，因此不是只保存一个名称。

### 参数

| 参数 | 必填 | 类型 | 说明 |
|---|---:|---|---|
| `--name NAME` 或位置参数 `NAME` | 是 | 字符串 | 剧本名称，不能为空；名称重复会返回冲突错误 |
| `--set user_input=TEXT` | 是 | 字符串 | 创作灵感或改编需求，不能为空 |
| `--set subject_matter=JSON` | 否 | 对象 | 题材选项；未传时按 Web 自动项规则从运行时配置选择 |
| `--set emotion=JSON` | 否 | 非空数组 | 算法情绪选项；未传时选择运行时配置中的自动项 |
| `--set mode=JSON` | 否 | 非空数组 | 故事模式选项；未传时选择运行时配置中的自动项 |
| `--set audience=JSON` | 否 | 对象 | 目标受众选项；未传时选择 Web 默认项 |
| `--set script_format=JSON` | 否 | 对象 | 剧本类型选项；未传时选择 Web 默认项 |
| `--set episode_count=N` | 是 | 整数 | 目标集数，范围为 `1` 到 `100` |
| `--set episode_word=N` | 否 | 整数 | 每集字数；国内剧默认 `750`，海外剧本默认 `450` |
| `--set region=JSON` | 条件必填 | 对象 | 海外剧本的区域选项；国内剧默认 `{}` |
| `--set arc_setting_type=N` | 否 | 整数 | 默认 `1`；显式传 `2` 时必须同时提供 `first_arc_setting` |
| `--set arc_count=N` | 否 | 整数 | 分卡数；不使用分卡时传 `0`。启用时不能大于集数，且每卡最多覆盖 `15` 集 |
| `--set first_arc_setting=JSON` | 条件必填 | 对象 | `arc_setting_type=2` 时的精细分卡设置 |
| `--set key=value` | 否 | 标量或 JSON | 传递其它后端支持的创建字段；同名字段以后传入的值覆盖前值 |

`--set` 可以重复使用，也可以使用 `--set @file.json` 或 `--set @-` 传入对象。值会按以下规则解析：布尔值、数字和合法 JSON 片段保持对应类型，其它内容按字符串处理。带空格的文本和 JSON 对象/数组需要加引号。

题材、情绪、故事模式、受众、剧本类型和区域选项通常来自网页端配置。选项对象一般包含以下字段，具体值以当前配置为准：

```json
{
  "res_id": "OPTION_RES_ID",
  "value": "OPTION_VALUE",
  "name": "选项名称",
  "desc": "选项说明"
}
```

示例中的占位符含义如下：

| 占位符 | 对应字段 | 含义 |
|---|---|---|
| `THEME_RES_ID` | `subject_matter.res_id` | 题材选项的配置资源 ID |
| `EMOTION_RES_ID` | `emotion[].res_id` | 情绪选项的配置资源 ID |
| `MODE_RES_ID` | `mode[].res_id` | 故事模式选项的配置资源 ID |
| `AUDIENCE_RES_ID` | `audience.res_id` | 受众选项的配置资源 ID |
| `SCRIPT_FORMAT_RES_ID` | `script_format.res_id` | 剧本类型选项的配置资源 ID |
| `REGION_RES_ID` | `region.res_id` | 海外剧本区域选项的配置资源 ID |
| `*_VALUE` | 对应对象的 `value` | 选项的业务值或配置值，不一定等于 `res_id` |

`res_id` 是配置选项的身份标识，`value` 是该选项的业务值；前端优先用 `res_id` 识别选项，缺少时才回退到 `value`。`name` 只是展示名称，`desc` 是说明文字，不能用剧本的 `NT_ID`、工作区 ID 或画布节点 ID 来替代这些字段。

不要把 `OPTION_RES_ID` 等占位符直接提交到服务端，也不要把画布节点 ID 当作选项 ID。

### 如何取得真实值

这些值由服务端配置下发，不是按中文名称自行编造的固定编号。使用以下方式取得：

1. 运行 `reelmate novel config --json` 获取当前服务端下发的完整配置。
2. 按 `subject_matter`、`emotion`、`mode`、`audience`、`script_format`、`region` 找到需要的选项。
3. 完整复制选项中的 `res_id`、`value`、`name`，以及存在的 `desc`、`prompt_template`，不要只复制展示名称。
4. 把复制出的对象放入 `novel-create.json`，再用 `--set @novel-create.json` 创建。切换站点、语言或剧本类型后应重新查询，不要长期复用另一套配置。

如果某个选项只有 `value` 没有 `res_id`，可以暂时让 `res_id` 与 `value` 相同；但只要配置返回了 `res_id`，就应优先使用配置中的原值。国内剧本的 `region` 通常传 `{}`，海外剧本必须复制当前选中的区域对象。

不要显式传空字符串 `"res_id":""`。如果配置项没有独立的 `res_id`，应省略该字段，或按网页端归一化规则令 `res_id` 与 `value` 相同。对象中的 `value`、`name` 必须来自同一个配置项，不能把不同选项的值和名称拼在一起。

### 示例

### 最简示例

未显式传入题材、情绪、故事模式、受众、剧本类型和区域时，CLI 会读取当前 Web 配置并按网页端规则补齐；集数和创作灵感仍需提供：

```bash
reelmate novel create --name='旧案回声' \
  --set 'user_input=一名记者调查旧案，发现所有线索都指向自己的家人。' \
  --set episode_count=12 --json
```

### 完整示例

使用 JSON 文件可以避免 shell 对数组和对象的引号处理问题。下面展示的是一组已通过 `novel config` 核实的国内悬疑剧配置；服务端配置可能变化，执行前仍应重新查询。

```json
{
  "subject_matter": {
    "res_id": "A05",
    "value": "A05",
    "name": "悬疑犯罪",
    "desc": "案件、犯罪、推理、刑侦、卧底、打假、旧案、取证。"
  },
  "emotion": [
    {
      "res_id": "B03",
      "value": "B03",
      "name": "悬疑刺激",
      "desc": "紧张、好奇、危险、真相递进、反转。"
    }
  ],
  "mode": [
    {
      "res_id": "C08",
      "value": "C08",
      "name": "探秘解谜",
      "desc": "追寻真相，线索递进，谜底反转。"
    }
  ],
  "audience": {
    "res_id": "1",
    "value": "male",
    "name": "男频",
    "desc": "迎合男性受众，重视剧情爽点"
  },
  "user_input": "一名记者调查旧案，发现所有线索都指向自己的家人。",
  "arc_setting_type": 1,
  "arc_count": 0,
  "episode_count": 12,
  "episode_word": 750,
  "script_format": {
    "res_id": "1",
    "value": "1",
    "name": "国内剧本",
    "desc": "全中文，国内团队制作国内剧"
  },
  "region": {}
}
```

```bash
reelmate novel create --name='旧案回声' --set @novel-create.json --json
```

也可以直接以内联参数传入，例如：

```bash
reelmate novel create --name='旧案回声' \
  --set 'user_input=一名记者调查旧案，发现所有线索都指向自己的家人。' \
  --set episode_count=12 \
  --set episode_word=750 \
  --set 'subject_matter={"res_id":"A05","value":"A05","name":"悬疑犯罪","desc":"案件、犯罪、推理、刑侦、卧底、打假、旧案、取证。"}' \
  --set 'emotion=[{"res_id":"B03","value":"B03","name":"悬疑刺激","desc":"紧张、好奇、危险、真相递进、反转。"}]' \
  --set 'mode=[{"res_id":"C08","value":"C08","name":"探秘解谜","desc":"追寻真相，线索递进，谜底反转。"}]' \
  --set 'audience={"res_id":"1","value":"male","name":"男频","desc":"迎合男性受众，重视剧情爽点"}' \
  --set 'script_format={"res_id":"1","value":"1","name":"国内剧本","desc":"全中文，国内团队制作国内剧"}' \
  --set 'region={}' --json
```

### 失败与重试

- CLI 会在发送请求前校验名称、灵感和 `episode_count`；只传 `--name` 或缺少必填值不会发起创建请求。
- 对于已经通过本地校验的请求，后端仍可能先写入项目记录，再让创意规划方案生成失败。
- 因此创建命令即使返回错误，项目也可能已经出现在 `novel list` 中，并显示“创意规划方案生成失败”等状态。这是已落库记录，不代表生成成功。
- `740115` 表示服务端在创建主记录后回查生成记录失败。CLI 会回查列表，并尽量在错误的 `raw.created_nt_id` 和 `raw.created_status` 中返回已落库记录；该错误不能靠原样重试解决。
- 同名剧本会返回业务冲突（`748201`），请更换名称；不要通过重复提交来重试生成。
- 创建请求是写操作，未知失败时不要立即重复执行。先用 `novel list` 确认是否已有同名或刚创建的 `NT_ID`。

## `reelmate novel analyze`

### 作用

对应网页端“从分析开始改编小说”。命令上传本地小说，以任务路由类型 `4` 创建拆解任务，等待拆解成功后启动内容分析。

### 参数

| 参数 | 必填 | 说明 |
|---|---:|---|
| `FILE` | 是 | `.txt` 或 `.docx` 本地文件，最大 `30MB` |
| `--json` | 否 | 输出完整任务数据 |

### 示例

此入口不接受 `--set`。它只完成上传、拆解和内容分析启动，不提前提交后续改编设定。

```bash
reelmate novel analyze ./novel.docx --json
```

## `reelmate novel direct`

### 作用

对应网页端“直接开始改编小说”。命令上传本地小说，以任务路由类型 `5` 拆解并等待成功，然后提交改编设定并启动剧本分析任务。

### 参数

| 参数 | 必填 | 说明 |
|---|---:|---|
| `FILE` | 是 | `.txt` 或 `.docx` 本地文件，最大 `30MB` |
| `--name NAME` | 否 | 剧本名称；默认取文件名并移除扩展名，最长 `50` 个字符 |
| `--set theme=JSON` | 否 | 题材选项对象；默认使用配置中的自动题材，没有自动项时使用第一项 |
| `--set audience=JSON` | 否 | 受众选项对象；默认使用配置中的第一项 |
| `--set adaptation_type=VALUE` | 否 | 改编程度；默认使用配置中标记为默认的选项，没有默认标记时使用第一项 |
| `--set episode_count=N` | 否 | 目标集数，默认 `40`，范围 `1` 到 `120` |
| `--set script_highlight=JSON` | 否 | 看点选项数组；默认使用配置中的自动看点，没有自动项时使用第一项 |
| `--set chapter_start=N` | 否 | 起始章节，默认 `1` |
| `--set chapter_end=N` | 否 | 结束章节，默认使用拆解结果的总章节数 |
| `--set episode_word=N` | 否 | 每集字数，默认 `750`，范围 `300` 到 `2000` |
| `--set user_input=TEXT` | 否 | 其它改编要求 |
| `--set arc_setting_type=N` | 否 | `1` 为快捷设置，`2` 为精细设置；默认 `1` |
| `--set arc_count=N` | 否 | 分卡数，默认 `0` |
| `--set first_arc_setting=JSON` | 条件必填 | `arc_setting_type=2` 时必填 |
| `--set uk_id=ID` | 否 | 知识库 ID；默认使用当前账号最近创建的编剧知识库，查询不到时为空 |

`episode_duration` 与网页端当前提交行为一致：未显式设置时使用当前 `episode_word` 的值；显式传入时按原值提交。选择完全遵从配置时，初始拆解仍是路由类型 `5`，服务端在设定完成后可能把任务切换为路由类型 `9`。

### 示例

目标集数还受原文规模限制：不能超过所选章节数的 `6` 倍，也不能超过所选原文按每 `500` 字一集计算的上限。`user_input` 最长 `10000` 个字符。`adaptation_type=strict_faithful` 时命令与网页端一致，强制提交 `arc_setting_type=1`、`arc_count=0` 并忽略 `first_arc_setting`。

```bash
reelmate novel direct ./novel.txt --json
reelmate novel direct ./novel.txt --set episode_count=24 --json
```

不传 `--set` 时，命令会按网页端首次打开设置弹窗时的规则读取动态默认项，并使用 `episode_count=40`。只有需要覆盖默认选项时才需要传入 `--set` 或参数文件。

## `reelmate novel derive`

### 作用

对应网页端“从已有剧本进行创意裂变”。本地文件来源会上传并以任务路由类型 `8` 拆解；剧本库来源会先从已定稿剧本创建新的裂变任务。两种来源随后提交相同的裂变设定并启动创意规划方案生成。

### 参数与输出

来源与设定参数如下。未传题材、看点、受众、剧本类型和区域时，CLI 会读取当前 Web 配置并补齐与“从剧本调用”弹窗相同的默认值；集数仍需显式传入。

### 来源参数

| 参数 | 必填 | 说明 |
|---|---:|---|
| `FILE` | 二选一 | `.txt` 或 `.docx` 本地文件，最大 `30MB` |
| `--nt-id SOURCE_NT_ID` | 二选一 | 剧本库中已定稿源剧本的 `NT_ID` |
| `--name NAME` | 条件必填 | 剧本库来源必填；本地文件来源默认取文件名 |

### 设定参数

| 参数 | 必填 | 说明 |
|---|---:|---|
| `--set theme=JSON` | 否 | 题材选项对象；未传时按网页端自动题材规则从运行时配置选择 |
| `--set script_highlight=JSON` | 否 | 看点选项数组；未传时选择网页端自动看点，数组至少一项 |
| `--set audience=JSON` | 否 | 受众选项对象；未传时选择当前网页配置的默认项或第一项 |
| `--set script_format=JSON` | 否 | 剧本类型选项对象；裂变入口未传时优先选择 `is_ai_rewrite_default=true` 的类型 |
| `--set region=JSON` | 条件必填 | 海外剧本类型的区域选项；国内裂变默认提交 `{}`，未传海外区域时按当前 Web 联动配置选择默认项 |
| `--set episode_count=N` | 是 | 目标集数，范围 `1` 到 `100` |
| `--set episode_word=N` | 否 | 每集字数；国内默认 `750`，海外默认 `450`，范围分别为 `300` 到 `3000`、`100` 到 `800` |
| `--set user_input=TEXT` | 否 | 创意裂变方向，默认空字符串，最长 `10000` 个字符 |。

### 示例

`adaptation_level` 是后端固定契约，命令始终提交 `light`，不会接受调用方改成其它值。国内剧本按网页端行为提交空的 `region` 对象；选择需要区域的剧本类型时应传入联动配置返回的区域对象。

未传题材、看点、受众、剧本类型和区域时，CLI 会读取当前 Web 配置并补齐与“从剧本调用”弹窗相同的默认值；集数仍需显式传入：

```bash
reelmate novel derive ./final-script.docx --set episode_count=12 --json
reelmate novel derive --nt-id SOURCE_NT_ID --name '新篇' --set episode_count=12 --json
```

`--nt-id` 是网页端“从剧本调用”入口使用的已定稿源剧本 `NT_ID`；本地文件入口和剧本库入口共用同一套默认规则。显式传入的 `--set` 值会覆盖对应默认项。

```bash
reelmate novel derive ./final-script.docx --name '旧案回声·新篇' --set @derive-settings.json --json
reelmate novel derive --nt-id 1941095147108827211 --name '旧案回声·新篇' --set @derive-settings.json --json
```

## `reelmate novel overseas`

### 作用

对应网页端“从已有剧本转海外剧本”。来源行为和后端任务链与 `derive` 相同，前端没有为出海单独定义任务路由类型；差异由海外 `script_format` 和 `region` 配置对象表达。

### 参数与输出

参数与 `derive` 相同；未显式传入时，CLI 会按网页端“从剧本调用”弹窗的出海默认值补齐：

| 参数 | 必填 | 说明 |。

### 示例
|---|---:|---|
| `--set script_format=JSON` | 否 | 使用 `ai_noval_overseas_adaptation` 中的海外剧本类型对象；未传时优先选择 `is_script_overseas_default=true` 的类型 |
| `--set region=JSON` | 否 | 海外类型的区域对象；未传时选择当前 Web 联动配置的默认区域 |
| `--set episode_word=N` | 否 | 每集词数，默认 `450`，范围 `100` 到 `800` |

海外入口的题材、看点、受众和创意需求也沿用 `derive` 的网页默认规则，`episode_count` 仍需显式传入：

```bash
reelmate novel overseas ./final-script.docx --set episode_count=12 --json
reelmate novel overseas --nt-id SOURCE_NT_ID --name 'Northbound' --set episode_count=12 --json
reelmate novel overseas ./final-script.docx --name 'Northbound' --set @overseas-settings.json --json
reelmate novel overseas --nt-id 1941095147108827211 --name 'Northbound' --set @overseas-settings.json --json
```

## 上传和状态行为

四条入口都只在后端明确返回成功后输出成功 envelope。本地来源先复用 `reelmate upload` 的 Drive/PDS 上传状态机，再创建拆解任务；测试不会连接真实服务。

拆解状态 `1` 表示处理中，命令每 `5` 秒查询一次；`2` 表示成功并继续下一步；`3` 表示失败并返回 `upstream` 结构化错误和任务失败退出码。网页端允许 `fail_type=10` 或 `11` 的拆解成功结果继续，CLI 同样继续，并在 JSON 输出的 `split_fail_type`、`split_message` 中保留服务端警告。未知状态不会被当成成功。

成功输出中的 `status` 表示后续任务已经由服务端接受：

| 入口子命令 | 成功时 `status` |
|---|---|
| `reelmate novel analyze` | `content_analysis_started` |
| `reelmate novel direct` | `script_analysis_started` |
| `reelmate novel derive` | `fission_idea_started` |
| `reelmate novel overseas` | `fission_idea_started` |

## `reelmate novel list`

### 作用

列出当前账号可见的剧本项目。默认返回第一页，每页 `20` 条。

### 参数

| 参数 | 必填 | 说明 |
|---|---:|---|
| `--set key=value` | 否 | 查询筛选条件，可重复传入；例如 `status=16`、`nt_ids=1941095147108827211` |
| `--json` | 否 | 输出完整 JSON，不做表格投影 |

### 示例

```bash
reelmate novel list
reelmate novel list --set status=16 --json
reelmate novel list --set nt_ids=1941095147108827211 --json
```

表格输出包含 `NT_ID`、`TITLE` 和 `STATUS`。状态是后端当前状态，可能是草稿、生成中或生成失败。

## `reelmate novel get`

### 作用

按 `NT_ID` 查询单个剧本项目详情。

### 参数

| 参数 | 必填 | 说明 |
|---|---:|---|
| `NT_ID` | 是 | `novel list` 返回的剧本项目 ID；不能使用画布节点 ID、工作区 ID 或剧集 ID |
| `--json` | 否 | 输出完整项目数据 |

### 示例

```bash
reelmate novel get 1941095147108827211 --json
```

## `reelmate novel idea list`

### 作用

查询原创剧本项目的创意规划方案列表。对应网页端创意方案卡片使用的只读接口 `GET /web/v1/df/novel/:nt_id/original_script/idea`。命令不会选中方案，也不会触发角色生成。

### 参数

| 参数 | 必填 | 说明 |
|---|---:|---|
| `NT_ID` | 是 | `novel create` 或 `novel list` 返回的剧本项目 ID，必须作为唯一位置参数传入 |
| `--json` | 否 | 输出服务端完整列表数据，包含 `total` 和 `list` |

表格输出包含 `NI_ID`、`TITLE` 和 `SELECTED`。`NI_ID` 来自每条方案的 `ni_id`，后续 `novel idea set` 需要这个值。`SELECTED` 对应 `is_select`，`1` 表示当前已选中。创意方案仍在生成时，列表可能为空。

`novel get` 只返回项目详情，不含方案列表。缺少 `NT_ID` 或传入多余位置参数时，命令会在发送请求前返回 `usage` 错误。旧命令 `novel ideas` 不再作为别名。

### 示例

```bash
reelmate novel idea list 1941095147108827211
reelmate novel idea list 1941095147108827211 --json
```

## `reelmate novel idea set`

### 作用

在原创剧本项目中提交选中的创意规划方案。对应网页端“使用该方案”，请求体只提交当前 `NI_ID` 且 `selected=true`。命令不会列出方案，也不会取消当前选中项。

### 参数

| 参数 | 必填 | 说明 |
|---|---:|---|
| `NT_ID` | 是 | `novel create` 或 `novel list` 返回的剧本项目 ID |
| `NI_ID` | 是 | 要选中的创意规划方案 ID，来自 `novel idea list` 返回的 `ni_id`，不是 `NT_ID` |
| `--json` | 否 | 输出包含 `action`、`nt_id`、`ni_id` 和服务端数据的成功 envelope |

先用 `reelmate novel idea list NT_ID` 取得 `NI_ID`，再传给本命令。`is_select=1` 表示当前已选中。旧写法 `reelmate novel idea NT_ID NI_ID` 不再作为别名。

### 示例

```bash
reelmate novel idea set 1941095147108827211 1941095147108828001
reelmate novel idea set 1941095147108827211 1941095147108828001 --json
```

成功后 JSON 含 `action=selected`。缺少 `NT_ID` 或 `NI_ID`、传入多余位置参数时，命令会在发送写请求前返回 `usage` 错误。

## `reelmate novel character`

### 作用

在已选定创意规划方案后，触发原创核心角色生成。对应网页端从创意方案进入角色阶段的下一步，请求路径是 `original_script/characters`，不是小说改编线的 `core_character/generate`。

### 参数

| 参数 | 必填 | 说明 |
|---|---:|---|
| `NT_ID` | 是 | 已选定创意方案的剧本项目 ID，必须作为唯一位置参数传入 |
| `--json` | 否 | 输出包含 `action`、`nt_id`、`status` 和服务端数据的成功 envelope |

### 示例

```bash
reelmate novel character 1941095147108827211
reelmate novel character 1941095147108827211 --json
```

成功后 JSON 含 `status=character_started`，表示服务端已接受生成请求。缺少 `NT_ID` 或传入多个位置参数时，命令会在发送写请求前返回 `usage` 错误。

## `reelmate novel material`

### 作用

在核心角色生成完成后，触发原创剧本素材生成。对应网页端「下一步：构建素材」，请求路径是 `original_script/materials`。不是画布/制片工坊的 `reelmate material` 命令。

### 参数

| 参数 | 必填 | 说明 |
|---|---:|---|
| `NT_ID` | 是 | 已完成角色生成的剧本项目 ID，必须作为唯一位置参数传入 |
| `--json` | 否 | 输出包含 `action`、`nt_id`、`status` 和服务端数据的成功 envelope |

### 示例

```bash
reelmate novel material 1941095147108827211
reelmate novel material 1941095147108827211 --json
```

成功后 JSON 含 `status=material_started`，表示服务端已接受生成请求。缺少 `NT_ID` 或传入多个位置参数时，命令会在发送写请求前返回 `usage` 错误。旧写法 `novel materials` 不再作为别名。

网页端构建素材后还可以勾选素材。`novel material NT_ID` 只触发生成，不会列出或选中素材。列出和勾选用下面两条命令。

## `reelmate novel material list`

### 作用

查询原创剧本项目的素材列表。对应网页端素材卡片使用的只读接口 `GET /web/v1/df/novel/:nt_id/original_script/materials`。命令不会选中素材，也不会触发总纲生成。

### 参数

| 参数 | 必填 | 说明 |
|---|---:|---|
| `NT_ID` | 是 | `novel create` 或 `novel list` 返回的剧本项目 ID，必须作为唯一位置参数传入 |
| `--json` | 否 | 输出服务端完整列表数据，包含 `total` 和 `list` |

表格输出包含 `TITLE`、`NM_ID`、`SELECTED` 和 `CONTENT`。`TITLE` 按列表顺序显示为 `素材1`、`素材2`，与网页素材卡片标题一致。`NM_ID` 来自每条素材的 `nm_id`，后续 `novel material set` 需要这个值。`SELECTED` 对应 `is_select`，`1` 表示当前已选中。表格里的 `CONTENT` 只显示前 10 个字符，超出部分加 `...`；`--json` 仍返回完整 `content`。素材仍在生成时，列表可能为空。

### 示例

```bash
reelmate novel material list 1941095147108827211
reelmate novel material list 1941095147108827211 --json
```

## `reelmate novel material set`

### 作用

在原创剧本项目中勾选一条素材。对应网页端素材卡片复选框，请求体提交当前 `NM_ID` 且 `selected=true`。命令不会列出素材，也不会取消当前选中项。网页点「下一步：剧本总纲及设定」前不强制勾选；本命令只同步勾选状态。

### 参数

| 参数 | 必填 | 说明 |
|---|---:|---|
| `NT_ID` | 是 | `novel create` 或 `novel list` 返回的剧本项目 ID |
| `NM_ID` | 是 | 要选中的素材 ID，来自 `novel material list` 返回的 `nm_id`，不是 `NT_ID` |
| `--json` | 否 | 输出包含 `action`、`nt_id`、`nm_id` 和服务端数据的成功 envelope |

先用 `reelmate novel material list NT_ID` 取得 `NM_ID`，再传给本命令。`is_select=1` 表示当前已选中。

### 示例

```bash
reelmate novel material set 1941095147108827211 1941095147108829001
reelmate novel material set 1941095147108827211 1941095147108829001 --json
```

成功后 JSON 含 `action=selected`。缺少 `NT_ID` 或 `NM_ID`、传入多余位置参数时，命令会在发送写请求前返回 `usage` 错误。

## `reelmate novel outline`

### 作用

在剧本素材生成完成后，触发原创剧本总纲及设定生成。对应网页端「下一步：剧本总纲及设定」，请求路径是 `original_script/summary_outline`。命令不会拉取或编辑总纲详情。

### 参数

| 参数 | 必填 | 说明 |
|---|---:|---|
| `NT_ID` | 是 | 已完成素材生成的剧本项目 ID，必须作为唯一位置参数传入 |
| `--json` | 否 | 输出包含 `action`、`nt_id`、`status` 和服务端数据的成功 envelope |

### 示例

```bash
reelmate novel outline 1941095147108827211
reelmate novel outline 1941095147108827211 --json
```

成功后 JSON 含 `status=outline_started`，表示服务端已接受生成请求。缺少 `NT_ID` 或传入多个位置参数时，命令会在发送写请求前返回 `usage` 错误。旧写法 `novel summary` 和 `novel summary_outline` 不再作为别名。

## `reelmate novel chapter`

### 作用

在剧本总纲及设定生成完成后，触发原创剧本分卡章纲生成。对应网页端「下一步：剧本分卡章纲」，请求路径是 `original_script/chapters_outline`。不是已有的 `novel outline`（总纲及设定），也不会拉取或编辑章纲详情。

### 参数

| 参数 | 必填 | 说明 |
|---|---:|---|
| `NT_ID` | 是 | 已完成总纲及设定生成的剧本项目 ID，必须作为唯一位置参数传入 |
| `--json` | 否 | 输出包含 `action`、`nt_id`、`status` 和服务端数据的成功 envelope |

### 示例

```bash
reelmate novel chapter 1941095147108827211
reelmate novel chapter 1941095147108827211 --json
```

成功后 JSON 含 `status=chapter_started`，表示服务端已接受生成请求。缺少 `NT_ID` 或传入多个位置参数时，命令会在发送写请求前返回 `usage` 错误。旧写法 `novel chapters`、`novel cards`、`novel chapter_outline` 和 `novel chapters_outline` 不再作为别名。

## `reelmate novel episode`

### 作用

在剧本分卡章纲生成完成后，触发原创剧本集纲生成。对应网页端「下一步：剧本集纲」，请求路径是 `original_script/episodes_outline`。不是制片工坊的 `reelmate episode`，也不会拉取或编辑集纲详情。

### 参数

| 参数 | 必填 | 说明 |
|---|---:|---|
| `NT_ID` | 是 | 已完成分卡章纲生成的剧本项目 ID，必须作为唯一位置参数传入 |
| `--json` | 否 | 输出包含 `action`、`nt_id`、`status` 和服务端数据的成功 envelope |

### 示例

```bash
reelmate novel episode 1941095147108827211
reelmate novel episode 1941095147108827211 --json
```

成功后 JSON 含 `status=episode_started`，表示服务端已接受生成请求。缺少 `NT_ID` 或传入多个位置参数时，命令会在发送写请求前返回 `usage` 错误。旧写法 `novel episodes`、`novel episode_outline` 和 `novel episodes_outline` 不再作为别名。

## `reelmate novel script`

### 作用

在剧本集纲生成完成后，触发原创分集剧本生成。对应网页端「下一步：分集剧本」，请求路径是 `original_script/episodes`。不是已有的 `novel episode`（集纲），也不是画布侧的 `reelmate script`，也不会拉取或编辑分集剧本详情。

### 参数

| 参数 | 必填 | 说明 |
|---|---:|---|
| `NT_ID` | 是 | 已完成集纲生成的剧本项目 ID，必须作为唯一位置参数传入 |
| `--json` | 否 | 输出包含 `action`、`nt_id`、`status` 和服务端数据的成功 envelope |

### 示例

```bash
reelmate novel script 1941095147108827211
reelmate novel script 1941095147108827211 --json
```

成功后 JSON 含 `status=script_started`，表示服务端已接受生成请求。缺少 `NT_ID` 或传入多个位置参数时，命令会在发送写请求前返回 `usage` 错误。旧写法 `novel scripts` 不再作为别名。

## `reelmate novel finalize`

### 作用

在分集剧本生成完成后，定稿并完成剧本改编。对应网页端「定稿，完成剧本改编」，请求路径是 `POST /web/v1/df/novel/:nt_id/finalize`。这是整任务定稿（状态 16 已定稿），不是已有的 `novel script`（分集剧本生成），也不是 `novel agent finalize`（单集版本/会话锁定）。

### 参数

| 参数 | 必填 | 说明 |
|---|---:|---|
| `NT_ID` | 是 | 已完成分集剧本生成的剧本项目 ID，必须作为唯一位置参数传入 |
| `--json` | 否 | 输出包含 `action`、`nt_id`、`status` 和服务端数据的成功 envelope |

### 示例

```bash
reelmate novel finalize 1941095147108827211
reelmate novel finalize 1941095147108827211 --json
```

成功后 JSON 含 `status=finalized`，表示服务端已接受定稿请求。缺少 `NT_ID` 或传入多个位置参数时，命令会在发送写请求前返回 `usage` 错误。旧写法 `novel finalized` 和 `novel complete` 不再作为别名。

## `reelmate novel rename`

### 作用

按 `NT_ID` 修改剧本名称。命令只更新名称，不改变剧本内容或生成状态。

### 参数

| 参数 | 必填 | 说明 |
|---|---:|---|
| `NT_ID` | 是 | `novel list` 返回的剧本项目 ID，必须作为唯一位置参数传入 |
| `--name NEW_NAME` | 是 | 新剧本名称，不能为空或只包含空白字符，最长 `50` 个字符 |
| `--json` | 否 | 输出包含 `action`、`nt_id`、`name` 和服务端数据的成功 envelope |

### 示例

```bash
reelmate novel rename 1941095147108827211 --name '旧案回声·修订版'
reelmate novel rename 1941095147108827211 --name '旧案回声·修订版' --json
```

名称与已有剧本重复时会返回结构化 `conflict` 错误和业务码 `748201`，应更换名称后再执行。缺少 `NT_ID`、传入多个位置参数、名称为空或超过 `50` 个字符时，命令会在发送写请求前返回 `usage` 错误。

## `reelmate novel delete`

### 作用

按 `NT_ID` 提交剧本项目删除请求。服务端确认成功后，命令输出 `deleted`。

### 参数

| 参数 | 必填 | 说明 |
|---|---:|---|
| `NT_ID` | 是 | `novel list` 返回的剧本项目 ID，必须作为唯一位置参数传入 |
| `--json` | 否 | 输出包含 `action`、`nt_id` 和服务端数据的成功 envelope |

### 示例

```bash
reelmate novel delete 1941095147108827211
reelmate novel delete 1941095147108827211 --json
```

### 删除风险

`delete` 是破坏性写操作，执行时不会再次交互确认。CLI 不提供恢复已删除剧本的命令；执行前必须核对 `NT_ID`，并确认所需内容已经另行备份。业务失败或未知网络失败时，不要连续重复删除，应先用 `novel list` 或 `novel get` 核实项目状态。

## 注意事项

`novel` 操作的是当前登录账号下的剧本项目。显式 `--space` 优先；当前目录绑定属于其他账号时，CLI 不会使用该目录的空间，而会回退到当前登录账号的 `space_id`。

- `novel` 项目使用 `NT_ID`；它与画布侧的 `script`、节点和制片工坊剧集是不同实体。
- 原创剧本配置应通过 `novel config` 实时查询；不要缓存为长期不变的固定枚举。
- `--set` 中的 JSON 对象和数组建议放入文件，通过 `--set @file.json` 传入。
- 写操作前先确认剧本名称、选项值和集数；生成失败后优先查询 `novel list`，不要盲目重复创建。
