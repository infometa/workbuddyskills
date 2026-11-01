# pin-group

固定节点组与 `group`（执行组）和 `team` 成员组不同。每个画布预置 7 个颜色组，CLI 的 `create` 会复用这些预置组。

## 用法

```text
reelmate pin-group create --canvas CANVAS_ID --name NAME --set 'node_id=[...]'
reelmate pin-group delete PIN_GROUP_ID --canvas CANVAS_ID
```

## 子命令说明

| 命令 | 作用 |
|---|---|
| `reelmate pin-group create` | 命名一个预置固定组并绑定节点 |
| `reelmate pin-group delete PIN_GROUP_ID` | 清空固定组成员（不删除预置组） |

## `reelmate pin-group create`

### 作用

按名称和节点列表选择固定组。如果已有预置组使用该名称，CLI 直接复用；否则选择一个未命名的预置组并设置名称。随后逐节点更新完整的 `group_ids`，在加入目标组的同时保留节点已有固定组。

### 参数

- `--canvas CANVAS_ID`（必填）：目标画布。
- `--name NAME`（必填）：固定组名称。
- `--set 'node_id=[...]'`：固定组成员节点 ID 数组。

### 输出

输出所使用的预置 `group_id`、名称和已绑定节点数量。

### 示例

```bash
reelmate pin-group create --canvas CANVAS_ID \
  --name favorites --set 'node_id=["NODE_ID_A"]' --json
```

## `reelmate pin-group delete PIN_GROUP_ID`

### 作用

清空指定固定组的全部成员。预置组不能被删除，组本身会保留供后续复用。

### 参数

- `PIN_GROUP_ID`、`--canvas CANVAS_ID`：固定组和画布标识。
- `--idempotency-key KEY`：幂等键。

### 输出

输出被清空的 `group_id` 和 `cleared` 操作状态。

### 示例

```bash
reelmate pin-group delete PIN_GROUP_ID --canvas CANVAS_ID --json
```

## 注意事项

- 每个画布只有 7 个预置颜色组；若没有同名组且所有预置组均已命名，`create` 会报错，不会覆盖其他名称。
- 节点绑定会替换成员列表；CLI 会先从预置组成员列表重建节点当前的完整 `group_ids`，再加入目标组。
- `delete` 只清空成员，不删除预置组。
