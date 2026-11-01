# group

管理画布节点组、组模板和整组执行。

## 用法

```text
reelmate group create NAME [--canvas CANVAS_ID] [--set KEY=VALUE]
reelmate group execute GROUP_ID [--workspace WORKSPACE_ID] [--canvas CANVAS_ID] [--set KEY=VALUE]
reelmate group delete GROUP_ID [--canvas CANVAS_ID] [--idempotency-key KEY]
reelmate group template save GROUP_ID [--canvas CANVAS_ID] --set name=NAME
reelmate group template list [--canvas CANVAS_ID]
reelmate group template get TEMPLATE_ID [--canvas CANVAS_ID]
```

## 子命令说明

| 命令 | 作用 |
|---|---|
| `reelmate group create NAME` | 创建组实体和画布中的组容器，并绑定成员节点。 |
| `reelmate group execute GROUP_ID` | 按组内依赖拓扑执行节点生成任务。 |
| `reelmate group delete GROUP_ID` | 删除组及其画布组容器。 |
| `reelmate group template save GROUP_ID` | 将组保存为模板。 |
| `reelmate group template list` | 查询当前空间的组模板。 |
| `reelmate group template get TEMPLATE_ID` | 查询指定组模板。 |

## `reelmate group create NAME`

### 作用

创建节点组，并把 `node_id` 或 `node_ids` 指定的节点绑定到组容器。

### 参数

- `NAME`：组名称。
- `--canvas CANVAS_ID`：目标画布；省略时使用当前绑定画布。
- `--set node_ids=["NODE_ID_A","NODE_ID_B"]`：要加入组的节点 ID 数组，也可重复传入 `--set node_id=NODE_ID`。
- `--set position_x=NUMBER`、`--set position_y=NUMBER`：组容器左上角坐标；省略时根据成员节点位置推导，无法推导时使用 `0`。
- `--set width=NUMBER`、`--set height=NUMBER`：组容器尺寸；省略时根据成员节点范围推导。

### 输出

成功时表格包含组名称、`GROUP_ID`、组容器 `NODE_ID` 和操作；`--json` 响应中的 `data.group_id` 是组实体 ID，`data.node_id` 是画布中的组容器节点 ID。

### 示例

```bash
reelmate group create shots \
  --canvas CANVAS_ID \
  --set 'node_ids=["NODE_ID_A","NODE_ID_B"]'
```

## `reelmate group execute GROUP_ID`

### 作用

按组内节点依赖拓扑分层执行生成任务，并等待各层完成。命令返回整组执行摘要，不返回单个 `TASK_ID`；结果不再交给 `task wait`。

### 参数

- `GROUP_ID`：组实体 ID。
- `--workspace WORKSPACE_ID`：工作区 ID；显式传入时优先，否则使用当前绑定工作区。
- `--canvas CANVAS_ID`：目标画布；省略时使用当前绑定画布。
- `--set ai_model_mark=MODEL_NAME`：生成所需的模型展示名，例如 `即梦4.5`。
- `--set concurrency=NUMBER`：同一依赖层的最大并发数。
- `--set max_cycle_layers=NUMBER`：检测到环时允许继续补跑的最大层数。
- `--set max_retries=NUMBER`：节点失败后的重试次数。
- `--timeout DURATION`：等待执行完成的超时时间。
- `--dry-run`：预演。**整组执行是最贵的写操作，提交前先跑一次预演。** 不发任何写请求（仅读取画布快照推导计划），按拓扑层输出 `items[]`，每层给出 `layer`、`kind`、`count`、`node_ids` 和 `node_types`——这就是将要逐个下单的节点清单。确认后去掉 `--dry-run` 重跑。

### 输出

实时输出每个拓扑层和节点的完成状态，结束时输出 `GROUP_ID`、整体状态、完成数和失败数。发生积分不足、权限失败、超时或取消时，CLI 停止创建新的节点任务，并在摘要中保留已完成和失败计数。

### 示例

```bash
reelmate group execute GROUP_ID \
  --workspace WORKSPACE_ID \
  --canvas CANVAS_ID \
  --set ai_model_mark=seedream_4.5 \
  --set concurrency=2 \
  --timeout 30m
```

## `reelmate group delete GROUP_ID`

### 作用

软删除组实体和画布中的组容器。

### 参数

- `GROUP_ID`：要删除的组实体 ID。
- `--canvas CANVAS_ID`：目标画布；省略时使用当前绑定画布。
- `--idempotency-key KEY`：幂等键；用于网络重试时避免重复删除，不是组 ID。

### 输出

表格显示组名称、成员节点和 `deleted` 操作；`--json` 响应包含删除的 `group_id` 和组容器 `node_id`。

### 示例

```bash
reelmate group delete GROUP_ID \
  --canvas CANVAS_ID \
  --idempotency-key KEY
```

## `reelmate group template save GROUP_ID`

### 作用

将指定组保存为组模板。

### 参数

- `GROUP_ID`：要保存的组实体 ID。
- `--canvas CANVAS_ID`：目标画布；省略时使用当前绑定画布。
- `--set name=NAME`：模板名称，必填。
- `--set description=TEXT`、`cover_file_id=FILE_ID`、`sync_to_team=BOOL`、`folder_id=FOLDER_ID`：可选模板属性。

### 输出

表格显示组成员的保存结果；`--json` 响应中的 `data.template_id` 是新模板 ID。

### 示例

```bash
reelmate group template save GROUP_ID \
  --canvas CANVAS_ID \
  --set name=template-v1 \
  --json
```

## `reelmate group template list`

### 作用

查询当前空间的组模板列表。

### 参数

- `--canvas CANVAS_ID`：目标画布；省略时使用当前绑定画布。
- `--json`：输出完整模板条目，包含 `template_id`。

### 输出

表格显示模板名称和操作；使用 `--json` 可读取每个条目的 `template_id`。

### 示例

```bash
reelmate group template list --canvas CANVAS_ID --json
```

## `reelmate group template get TEMPLATE_ID`

### 作用

查询指定组模板的详细信息。

### 参数

- `TEMPLATE_ID`：组模板 ID。
- `--canvas CANVAS_ID`：目标画布；省略时使用当前绑定画布。

### 输出

返回模板名称、属性和组成员等模板详情。

### 示例

```bash
reelmate group template get TEMPLATE_ID --canvas CANVAS_ID
```

## 注意事项

- `GROUP_ID` 是组实体 ID，`NODE_ID` 是画布中组容器节点 ID；两者用途不同，后续组操作使用 `GROUP_ID`。
- `group create` 会先创建组实体，再创建并回写画布组容器；只有绑定成员节点和 `serverGroupId` 后，网页端才能重建分组效果。
- `group execute` 需要组内节点已配置可用的生成参数；例如生成命令通常需要 `ai_model_mark`。
- 组删除是软删除，超过保留窗口后无法恢复。
- `group recover` 当前暂不可用；需要恢复时请使用 `group create` 重新建立组。
- 组命令需要已确定的工作区和画布；显式 `--workspace`、`--canvas` 优先于当前绑定作用域。
