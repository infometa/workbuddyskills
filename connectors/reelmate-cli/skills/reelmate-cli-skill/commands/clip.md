# clip

`clip` 提交**整画布视频合成与裁剪**，路径挂在 `canvas/:canvas_id/clip` 与 `canvas/:canvas_id/crop`。它不是 `node create clip`（那是创建 clip 类型节点）。

这些接口目前是 **[YApi] 待实测**：路径按技术方案登记实现，响应完整保留在 `raw`，不要按猜测字段名丢掉其余键。联调不符时改测试与实现，不改命令面。不得声称已验证。

## 用法

```text
reelmate clip create --canvas CANVAS_ID --set 'shot_order=["NODE_ID",...]'
reelmate clip crop --canvas CANVAS_ID [--set ...]
```

写命令：接受 `--idempotency-key`，可用 `--dry-run` 预演（不发写请求）。写操作走 canvaswrite 的心跳、加锁、版本、写入、回读；未取得编辑权时报冲突。产出是异步任务，返回 `task_id` 后用 `reelmate task wait` 接续。

## 子命令说明

| 命令 | 作用 |
|---|---|
| `reelmate clip create` | 提交整画布视频合成，路径 `POST canvas/:canvas_id/clip` |
| `reelmate clip crop` | 提交整画布视频裁剪，路径 `POST canvas/:canvas_id/crop` |

## `reelmate clip create`

### 作用

提交整画布视频合成任务。产出是异步任务，返回 `task_id` 后用 `reelmate task wait` 接续。

### 参数

| 参数 | 必填 | 说明 |
|---|---:|---|
| `--canvas CANVAS_ID` | 是 | 目标画布 |
| `--set shot_order=` | 是 | 节点 ID 数组，顺序即成片顺序；空数组、空 ID、画布上不存在的节点 ID 都会被挡住 |
| `--workspace`、`--space` | 否 | 作用域 |
| `--idempotency-key`、`--dry-run`、`--json` | 否 | 幂等键、预演和 JSON 输出 |

### 示例

```bash
reelmate clip create --canvas CANVAS_ID --set 'shot_order=["NODE_ID"]' --dry-run --json
reelmate clip create --canvas CANVAS_ID --set 'shot_order=["NODE_ID"]' --json
```

## `reelmate clip crop`

### 作用

提交整画布视频裁剪任务。产出同样是异步任务，返回 `task_id` 后用 `reelmate task wait` 接续。

### 参数

| 参数 | 必填 | 说明 |
|---|---:|---|
| `--canvas CANVAS_ID` | 是 | 目标画布 |
| `--set ...` | 否 | 裁剪字段按当前帮助和结构化错误传入；未登记字段不得猜测 |
| `--workspace`、`--space` | 否 | 作用域 |
| `--idempotency-key`、`--dry-run`、`--json` | 否 | 幂等键、预演和 JSON 输出 |

### 示例

```bash
reelmate clip crop --canvas CANVAS_ID --dry-run --json
reelmate clip crop --canvas CANVAS_ID --json
```

## 注意事项

- 接口 **[YApi] 待实测**，字段可能与实际有出入；以 `raw` 为准。
- `shot_order` 在提交前会对照画布 `node_list` 校验节点是否存在。
- 与 `node create clip` 不同：本命令组提交合成/裁剪任务，不创建节点。
