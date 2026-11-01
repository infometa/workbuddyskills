# script

`script` 作用在**画布脚本节点**上（`canvas/:canvas_id/nodes/:node_id/*`），是画布模式的剧本流水线：拆分镜、抽资产、匹配/重匹配资产、优化剧本。

`novel` 是 **GUI 剧本项目实体**（`df/novel/*`，主键 `nt_id`）。两条命令面、两套后端路径，不可混用。不要把「改剧本」发到画布节点上，也不要把画布拆分镜发到 `novel`。

发布态以当前二进制帮助、本命令页和结构化错误为执行依据；文档未登记的字段不得猜测。

## 用法

```text
reelmate script storyboard --canvas CANVAS_ID --node NODE_ID [--set script_text=...]
reelmate script asset-extract --canvas CANVAS_ID --node NODE_ID [--set script_text=...]
reelmate script asset-match --canvas CANVAS_ID --node NODE_ID
reelmate script rematch --canvas CANVAS_ID --node NODE_ID
reelmate script cancel --canvas CANVAS_ID --node NODE_ID
reelmate script optimize --canvas CANVAS_ID --node NODE_ID
```

六条都是写命令：接受 `--idempotency-key`，可用 `--dry-run` 预演（不发写请求，退出码 0）。写操作经由 canvaswrite 的心跳、加锁、版本、写入、回读链路；未取得编辑权时报冲突，不静默覆盖。

产出是异步任务，命令返回 `task_id` 后用 `reelmate task wait` 接续。命令本身不做长轮询。

`asset-extract` 在拿到 `task_id` 后会先把节点写回为 `node_mode=ai_generating`，并持久化
`task_info={"task_id":"...","status":"processing","task_type":"asset_extraction"}`，这样 Web
端刷新画布后仍能看到并恢复资产提取任务。该状态写回失败时，命令会报告“任务已创建但写回失败”，不会伪装成完整成功。

## 子命令说明

全部挂在 `POST canvas/:canvas_id/nodes/:node_id/` 前缀下：

| 命令 | 作用 |
|---|---|
| `reelmate script storyboard` | 拆分镜，路径 `storyboard-parse` |
| `reelmate script asset-extract` | 抽资产，路径 `asset-extraction` |
| `reelmate script asset-match` | 匹配资产，路径 `storyboard-asset-match` |
| `reelmate script rematch` | 重匹配资产，路径 `storyboard-asset-rematch` |
| `reelmate script cancel` | 取消资产匹配，路径 `storyboard-asset-match/cancel` |
| `reelmate script optimize` | 优化剧本，路径 `script-optimization` |

## `reelmate script storyboard`

### 作用

在画布脚本节点上拆分镜。路径 `POST canvas/:canvas_id/nodes/:node_id/storyboard-parse`。

### 参数

| 参数 | 必填 | 说明 |
|---|---:|---|
| `--canvas CANVAS_ID` | 是 | 目标画布 |
| `--node NODE_ID` | 是 | 脚本节点 |
| `--set script_text=` | 否 | 剧本正文 |
| `--workspace`、`--space` | 否 | 作用域 |
| `--idempotency-key`、`--dry-run`、`--json` | 否 | 幂等键、预演和 JSON 输出 |

### 示例

```bash
reelmate script storyboard --canvas CANVAS_ID --node NODE_ID --dry-run --json
reelmate script storyboard --canvas CANVAS_ID --node NODE_ID --json
```

## `reelmate script asset-extract`

### 作用

从画布脚本节点抽资产。路径 `asset-extraction`。产出是画布侧资产，不是制片工坊 `resource`。

### 参数

与 `reelmate script storyboard` 相同，可带 `--set script_text=`。

### 示例

```bash
reelmate script asset-extract --canvas CANVAS_ID --node NODE_ID --dry-run --json
```

## `reelmate script asset-match`

### 作用

匹配画布脚本节点资产。路径 `storyboard-asset-match`。

### 参数

`--canvas` 与 `--node` 必填；不使用 `script_text`。

### 示例

```bash
reelmate script asset-match --canvas CANVAS_ID --node NODE_ID --dry-run --json
```

## `reelmate script rematch`

### 作用

重匹配画布脚本节点资产。路径 `storyboard-asset-rematch`。

### 参数

`--canvas` 与 `--node` 必填。

### 示例

```bash
reelmate script rematch --canvas CANVAS_ID --node NODE_ID --dry-run --json
```

## `reelmate script cancel`

### 作用

取消画布脚本节点的资产匹配。路径 `storyboard-asset-match/cancel`。

### 参数

`--canvas` 与 `--node` 必填。

### 示例

```bash
reelmate script cancel --canvas CANVAS_ID --node NODE_ID --dry-run --json
```

## `reelmate script optimize`

### 作用

优化画布脚本节点上的剧本。路径 `script-optimization`。

### 参数

与 `reelmate script storyboard` 相同，可带 `--set script_text=`。

### 示例

```bash
reelmate script optimize --canvas CANVAS_ID --node NODE_ID --dry-run --json
```

## 注意事项

- `asset-extract` 产出的是**画布侧**资产。它与制片工坊的 `resource` 是否互通尚未确认，不要声称两者可以互相转换。
- 与 `novel` 的边界见开篇：`script` ≠ `novel`。
