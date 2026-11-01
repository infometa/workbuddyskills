# redraw

视频转绘工作流命令组。`redraw info` 查询指定转绘项目剧集的当前阶段；其余阶段命令的可用状态以后续发布为准。

## 用法

```text
reelmate redraw info SP_ID EP_ID [--space SPACE_ID]
reelmate redraw create [--set key=value]
reelmate redraw episode [--set key=value]
reelmate redraw bind [--set key=value]
reelmate redraw asset [--set key=value]
reelmate redraw plan [--set key=value]
```

## 子命令说明

| 命令 | 作用 |
|---|---|
| `reelmate redraw info SP_ID EP_ID` | 查询转绘项目剧集详情、阶段和状态 |
| `reelmate redraw create` | 创建转绘项目；流程待接入 |
| `reelmate redraw episode` | 创建或准备转绘剧集；流程待接入 |
| `reelmate redraw bind` | 绑定项目资源；流程待接入 |
| `reelmate redraw asset` | 生成转绘资产；流程待接入 |
| `reelmate redraw plan` | 生成分镜规划；流程待接入 |

## `reelmate redraw info SP_ID EP_ID`

### 作用

查询视频转绘项目中指定剧集的流程快照。

### 参数

**位置参数**

- `SP_ID`（必填）：视频转绘项目 ID。它是制片工坊项目 ID，不是画布 ID、节点 ID 或空间 ID。
- `EP_ID`（必填）：项目下的剧集 ID。它不是小说项目 ID，也不是任务 ID。

**选项**

| 选项 | 可重复 | 说明 |
|---|---|---|
| `--workspace SP_ID` | 否 | 以选项形式提供项目 ID；优先于位置参数 |
| `--episode EP_ID` | 否 | 以选项形式提供剧集 ID；优先于位置参数 |
| `--space SPACE_ID` | 否 | 指定生效空间 |
| `--json` / `--ndjson` | 否 | 选择 JSON envelope / NDJSON 输出 |

### 如何取得 ID

- 项目 ID：从项目创建命令的 JSON 结果中读取 `sp_id`；已有项目可用 `reelmate workspace list/info` 查询。
- 剧集 ID：运行 `reelmate episode list --workspace SP_ID --json`，读取返回项中的 `episode_id`（或 `ep_id`）。
- `SP_ID`、`EP_ID`、`CANVAS_ID`、`NODE_ID`、`SPACE_ID` 属于不同 ID 域，不能互换。

### 输出

文本输出为 `SP_ID`、`EP_ID`、`STAGE`、`STATUS` 表格；`--json` 返回完整项目详情，包括 `video_redraw_stage`、`video_redraw_stage_status`、`latest_flow` 等字段。

### 示例

```bash
reelmate workspace list --space SPACE_ID --json
reelmate episode list --workspace SP_ID --json
reelmate redraw info SP_ID EP_ID --json
reelmate redraw info --workspace SP_ID --episode EP_ID --space SPACE_ID --json
```

## `reelmate redraw create`

### 作用

创建转绘项目。流程待接入，正式接入前不要当作成功流程使用。

### 参数与输出

`--set key=value` 以后续发布和当前帮助为准；未登记字段不得猜测。

### 示例

```bash
reelmate redraw create --json
```

## `reelmate redraw episode`

### 作用

创建或准备转绘剧集。流程待接入。

### 参数与输出

`--set key=value` 以后续发布和当前帮助为准。

### 示例

```bash
reelmate redraw episode --json
```

## `reelmate redraw bind`

### 作用

绑定项目资源。流程待接入。

### 参数与输出

`--set key=value` 以后续发布和当前帮助为准。

### 示例

```bash
reelmate redraw bind --json
```

## `reelmate redraw asset`

### 作用

生成转绘资产。流程待接入。

### 参数与输出

`--set key=value` 以后续发布和当前帮助为准。

### 示例

```bash
reelmate redraw asset --json
```

## `reelmate redraw plan`

### 作用

生成分镜规划。流程待接入。

### 参数与输出

`--set key=value` 以后续发布和当前帮助为准。

### 示例

```bash
reelmate redraw plan --json
```

## 注意事项

- `redraw info` 是只读操作，不会创建或推进转绘任务。
- 缺少 `SP_ID` 或 `EP_ID` 时，CLI 返回 usage 错误，不会猜测其它 ID。
- 其它阶段命令在正式接入前不要当作成功流程使用。
