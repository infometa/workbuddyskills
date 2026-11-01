# ad

AI 广告剧工作流命令组。

## 用法

```text
reelmate ad info SP_ID EP_ID
reelmate ad save --set material_name=... --set material_highlight=... --set material_image=FILE_ID --set style=STYLE_ID --set ratio=9:16 --set sp_type=2
reelmate ad selling-point --set material_name=... --set material_image=FILE_ID
reelmate ad plot SP_ID EP_ID
reelmate ad script SP_ID EP_ID --set brief_id=BRIEF_ID
reelmate ad asset SP_ID EP_ID [--set need_voice=1|2]
reelmate ad plan SP_ID EP_ID --set template_type=1|2
reelmate ad reset SP_ID EP_ID
```

`SP_ID`、`EP_ID` 也可分别通过 `--workspace`、`--episode` 提供；阶段命令还接受 `--set sp_id=...`、`--set ep_id=...` 作为后备输入。显式 flag 优先于位置参数，位置参数优先于 `--set`。

## 子命令说明

| 命令 | 作用 |
|---|---|
| `reelmate ad info` | 查询项目剧集详情 |
| `reelmate ad save` | 新建或更新商品广告项目/剧集 |
| `reelmate ad selling-point` | 根据商品名和商品图生成卖点 |
| `reelmate ad plot` | 生成剧情方案任务 |
| `reelmate ad script` | 按选中的 `brief_id` 生成广告脚本 |
| `reelmate ad asset` | 创建广告资产提取任务 |
| `reelmate ad plan` | 生成分镜规划 |
| `reelmate ad reset` | 重置脚本并回到剧情方案选择 |

## `reelmate ad info`

### 作用

查询项目剧集详情。

### 参数与输出

需要 `SP_ID` 和 `EP_ID`。`SP_ID`、`EP_ID` 也可分别通过 `--workspace`、`--episode` 提供。表格输出 `SP_ID`、`EP_ID`、`STAGE`、`STATUS`；`--json` 返回完整结果。

### 示例

```bash
reelmate ad info SP_ID EP_ID --json
```

## `reelmate ad save`

### 作用

新建或更新商品广告项目/剧集。

### 参数与输出

| `--set` 字段 | 必填 | 说明 |
|---|---|---|
| `material_name` | 是 | 商品名 |
| `material_highlight` | 是 | 商品卖点 |
| `material_image` | 是 | 已上传商品图的 `file_id` |
| `style` | 是 | 风格 ID |
| `ratio` | 是 | `9:16` 或 `16:9` |
| `sp_type` | 是 | 数值项目类型；当前使用 `2` |
| `theme` | 否 | 主题 ID |
| `group_ids` | 否 | 分组 ID 字符串；当前使用 `0` |
| `sp_id`、`ep_id` | 否 | 为空时新增，传值时更新；也可用 `--workspace`、`--episode` |

表格输出 `SP_ID`、`EP_ID`、`NAME`、`STAGE`、`STATUS`。

### 示例

```bash
reelmate ad save --set material_name='商品名' --set material_highlight='商品卖点' --set material_image=FILE_ID --set style=STYLE_ID --set theme=THEME_ID --set ratio=9:16 --set sp_type=2 --set group_ids=0 --json
```

## `reelmate ad selling-point`

### 作用

根据商品名和商品图生成卖点。

### 参数与输出

只需要 `material_name` 和 `material_image`，不需要 `sp_id`。表格输出 `MATERIAL_HIGHLIGHT`。

### 示例

```bash
reelmate ad selling-point --set material_name='商品名' --set material_image=FILE_ID --json
```

## `reelmate ad plot`

### 作用

生成剧情方案任务。

### 参数与输出

需要 `SP_ID` 和 `EP_ID`。表格输出 `TASK_ID`。

### 示例

```bash
reelmate ad plot SP_ID EP_ID --json
```

## `reelmate ad script`

### 作用

按选中的 `brief_id` 生成广告脚本。

### 参数与输出

需要 `SP_ID`、`EP_ID` 和必填 `brief_id`。表格输出 `EP_ID`。

### 示例

```bash
reelmate ad script SP_ID EP_ID --set brief_id=BRIEF_ID --json
```

## `reelmate ad asset`

### 作用

创建广告资产提取任务。

### 参数与输出

需要 `SP_ID` 和 `EP_ID`。可选 `need_voice`：`1` 生成配音，`2` 不生成配音。表格输出 `ET_ID`。

### 示例

```bash
reelmate ad asset SP_ID EP_ID --json
```

## `reelmate ad plan`

### 作用

生成分镜规划。

### 参数与输出

需要 `SP_ID`、`EP_ID` 和必填 `template_type`：`1` 急速模式，`2` 至尊模式。表格输出 `EP_ID`。

### 示例

```bash
reelmate ad plan SP_ID EP_ID --set template_type=1 --json
```

## `reelmate ad reset`

### 作用

重置脚本并回到剧情方案选择。

### 参数与输出

需要 `SP_ID` 和 `EP_ID`。执行成功后显示 `STATUS=success`；`--json` 成功时结果为空对象。

### 示例

```bash
reelmate ad reset SP_ID EP_ID --json
```

## 注意事项

- 除 `info` 外，这些命令都会写入项目状态或创建生成任务，并可能触发积分扣费。
- 生成命令只返回任务或剧集标识时，后续阶段和正文应重新用 `ad info` 查询，不从本次响应猜测。
- `SP_ID`、`EP_ID`、`BRIEF_ID`、`ET_ID`、`FILE_ID`、`SPACE_ID` 属于不同 ID 域，不能互换。
- 未列出的 `--set` 字段会返回 usage 错误，不会静默忽略。
