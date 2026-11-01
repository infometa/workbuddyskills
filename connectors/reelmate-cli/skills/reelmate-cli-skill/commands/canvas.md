# canvas

画布是工作区中的内容容器，节点、连线和组都归属于画布。

## 用法

```text
reelmate canvas create NAME [--workspace WORKSPACE_ID] [--space SPACE_ID]
reelmate canvas list [--workspace WORKSPACE_ID]
reelmate canvas get CANVAS_ID
reelmate canvas edit CANVAS_ID NAME
reelmate canvas delete CANVAS_ID [--episode EPISODE_ID]
reelmate canvas template publish --canvas CANVAS_ID --name NAME
reelmate canvas template list
reelmate canvas template get TEMPLATE_ID
reelmate canvas template apply TEMPLATE_ID --canvas CANVAS_ID
```

## 子命令说明

| 命令 | 作用 |
|---|---|
| `reelmate canvas create NAME` | 在工作区中创建画布 |
| `reelmate canvas list` | 列出工作区画布 |
| `reelmate canvas get CANVAS_ID` | 查看画布详情 |
| `reelmate canvas edit CANVAS_ID NAME` | 修改画布名称 |
| `reelmate canvas delete CANVAS_ID` | 删除画布对应的剧集容器 |
| `reelmate canvas template publish` | 发布整画布模板（[YApi] 待实测） |
| `reelmate canvas template list` | 列出整画布模板（[YApi] 待实测） |
| `reelmate canvas template get` | 查看整画布模板（[YApi] 待实测） |
| `reelmate canvas template apply` | 按模板批量生成画布元素（[YApi] 待实测） |

## `reelmate canvas create NAME`

### 作用

创建画布模式画布。

### 参数

- `NAME`（必填）：画布名称。
- `--workspace WORKSPACE_ID`、`--space SPACE_ID`：目标作用域。
- `--name NAME`：也可用选项提供名称。
- `--idempotency-key KEY`、`--json`：幂等键和输出格式。

### 输出

返回 `canvas_id`、`episode_id` 和画布名称。

### 示例

```bash
reelmate canvas create demo --workspace WORKSPACE_ID --space SPACE_ID --json
```

## `reelmate canvas list`

### 作用

列出当前工作区的画布。

### 参数

- `--workspace WORKSPACE_ID`：指定工作区。
- `--space SPACE_ID`：指定空间。
- `--no-heartbeat`、`--json`：只读关闭 heartbeat 或输出 JSON。

### 输出

返回画布名称、`canvas_id`、项目 ID 和版本等信息。

### 示例

```bash
reelmate canvas list --workspace WORKSPACE_ID --json
```

## `reelmate canvas get CANVAS_ID`

### 作用

查询画布完整数据。

### 参数

- `CANVAS_ID`（必填）：目标画布。
- `--workspace WORKSPACE_ID`、`--space SPACE_ID`：作用域。
- `--no-heartbeat`、`--json`：只读选项。

### 输出

返回画布、节点和连线数据。

### 示例

```bash
reelmate canvas get CANVAS_ID --no-heartbeat --json
```

## `reelmate canvas edit CANVAS_ID NAME`

### 作用

修改画布名称。

### 参数

- `CANVAS_ID`、`NAME`（必填）：画布 ID 和新名称。
- `--workspace WORKSPACE_ID`、`--space SPACE_ID`：作用域。
- `--idempotency-key KEY`：写操作幂等键。

### 输出

返回更新后的画布摘要。

### 示例

```bash
reelmate canvas edit CANVAS_ID renamed --idempotency-key KEY --json
```

## `reelmate canvas delete CANVAS_ID`

### 作用

删除画布对应的剧集容器。

### 参数

- `CANVAS_ID`（必填）：目标画布。
- `--episode EPISODE_ID`：已知剧集 ID 时跳过映射查询。
- `--workspace WORKSPACE_ID`、`--space SPACE_ID`、`--idempotency-key KEY`：作用域和幂等键。

### 输出

返回删除结果。

### 示例

```bash
reelmate canvas delete CANVAS_ID --episode EPISODE_ID --idempotency-key KEY --json
```

## `reelmate canvas template publish`

### 作用

发布整画布模板。路径 `POST canvas/:canvas_id/tpls`。接口目前是 **[YApi] 待实测**。

整画布模板（`canvas-tpls` / `canvas/:id/tpls`）与 `group template`（节点组模板）是**两回事**，不要混用。

### 参数

- `--canvas CANVAS_ID`（必填）：目标画布。
- `--name NAME`（必填）：模板名称。
- `--idempotency-key`、`--dry-run`：写命令走 canvaswrite。
- `--json`：输出 JSON。响应完整保留在 `raw`。不得声称已验证。

### 示例

```bash
reelmate canvas template publish --canvas CANVAS_ID --name demo --json
```

## `reelmate canvas template list`

### 作用

列出整画布模板。路径 `GET canvas-tpls`。只读。接口目前是 **[YApi] 待实测**。

`tpl_type` 是必填参数，默认 `2`（官方画布模块），与 Web 列官方模板时一致；`--set tpl_type=1` 取新手引导模板（Web 另有 `3` 表示「从剧本到成片」引导）。输出的 `tpl_type` 字段回显本次实际用的类型。

### 参数

- `--set page=N` / `--set page_size=N` / `--set all=true`：分页。接口单页默认 100 条，CLI 与 Web 一样传 `page=1`、`page_size=100`。默认只取第一页，`--set page=N` 逐页取、`--set page_size=N` 改单页条数、`--set all=true` 按服务端总数一次取完；输出带 `count`、`page`、`page_size`、`has_more`、`next_page`，`has_more=true` 时不要当成全量用。
- `--json`：输出 JSON。

### 示例

```bash
reelmate canvas template list --json
reelmate canvas template list --set tpl_type=1 --json
```

## `reelmate canvas template get`

### 作用

查看整画布模板。路径 `GET canvas-tpls/:template_id`。只读。接口目前是 **[YApi] 待实测**。

### 参数

- `TEMPLATE_ID`（必填）：模板标识。
- `--json`：输出 JSON。

### 示例

```bash
reelmate canvas template get TEMPLATE_ID --json
```

## `reelmate canvas template apply`

### 作用

按模板批量生成画布元素。路径 `POST canvas/:canvas_id/tpls/:template_id/elements/batch-create`。写命令走 canvaswrite。接口目前是 **[YApi] 待实测**。

### 参数

- `TEMPLATE_ID`（必填）：模板标识。
- `--canvas CANVAS_ID`（必填）：目标画布。
- `--idempotency-key`、`--dry-run`、`--json`。

### 示例

```bash
reelmate canvas template apply TEMPLATE_ID --canvas CANVAS_ID --json
```

## 注意事项

- 工作区 `creation_mode=1` 表示制片工坊，`creation_mode=2` 表示无限画布；CLI 默认创建制片工坊工作区。使用本命令组前，应绑定已有无限画布工作区，或用 `workspace create --set creation_mode=2` 创建。
- `CANVAS_ID`、`WORKSPACE_ID`、`SPACE_ID` 应从相应命令的 JSON 结果或当前绑定配置取得。
