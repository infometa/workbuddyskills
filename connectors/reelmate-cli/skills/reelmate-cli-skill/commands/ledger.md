# ledger

查看与解除本地幂等账本条目。纯本地命令，不需要凭据，离线可用。

幂等账本（`$REELMATE_CONFIG_DIR/state/idempotency.json`）记录每一次非幂等写的结果状态，
用来阻止「同一次写被提交两遍」。它有三态：

| 状态 | 含义 | 同键再写会怎样 |
|---|---|---|
| `pending` | 已占位，请求还没结束 | 拒绝（退出码 9，可能有另一个进程在处理） |
| `in_doubt` | 请求**已发出但结果未知**，可能已在服务端生效 | 拒绝（退出码 11），需人工复核后解除 |
| `applied` | 确认成功 | 按重放短路，返回上次结果，不再发请求 |

`in_doubt` 是这三态里唯一需要人介入的一档。它通常来自超时或 `746000`（批量写下游超时）：
当次返回是失败的，但服务端可能已经把这批写完了。CLI 无法替你判断，所以把键锁住，
等你用只读命令复核后再决定。

## 用法

```text
reelmate ledger list [--in-doubt] [--json]
reelmate ledger show KEY [--json]
reelmate ledger resolve KEY [--dry-run] [--json]
```

## 子命令说明

| 命令 | 作用 |
|---|---|
| `reelmate ledger list` | 列出账本条目 |
| `reelmate ledger show` | 查看单条的全部字段与成因 |
| `reelmate ledger resolve` | 解除一条 `in_doubt`（人工复核确认未生效后） |

## `reelmate ledger list`

### 作用

列出账本里的全部条目。被退出码 11 拦下时，用它找出卡住的是哪个键。

### 参数

- `--in-doubt`：只列出 `in_doubt` 的未决条目。
- `--json`：输出 JSON。

### 输出

表格列：`KEY`、`STATE`、`ENDPOINT`、`ITEMS`、`AT`。
JSON 另有 `total`、`in_doubt_count`；存在未决条目时带 `hint`。

账本文件不存在时输出空集，不报错（新装的 CLI 本来就没有账本）。

### 示例

```bash
reelmate ledger list --in-doubt --json
```

## `reelmate ledger show`

### 作用

查看单条的全部字段，含 `endpoint`、`item_count` 和 `note`（成因）。
`in_doubt` 条目会额外给出 `next`：下一步该做什么。

### 参数

- `KEY`（位置参数，必填）：幂等键，从 `ledger list` 获取。
- `--json`：输出 JSON。

### 示例

```bash
reelmate ledger show 'hlm-ep-batch:studio:5ab42827bba1c999650c76e9' --json
```

## `reelmate ledger resolve`

### 作用

删除一条 `in_doubt`，让同键可以重打。

**这是在放开一道重复扣费的闸门。** 只有在用只读命令复核过、确认上次那笔写
**确实没有生效**之后才用它。若上次其实已生效，解除后重打会造成重复创建或重复扣费。

只处理 `in_doubt`：
- `applied` 会被拒绝——删掉它等于放开重放保护；
- `pending` 会被拒绝——可能有另一个进程正在处理它。

### 参数

- `KEY`（位置参数，必填）：要解除的幂等键。
- `--dry-run`：只预览，不写盘。
- `--json`：输出 JSON。

### 示例

```bash
# 复核：那 120 集到底建进去了没有
reelmate episode list --workspace SP_ID --set all=true --json

# 确认未生效后再解除
reelmate ledger resolve 'hlm-ep-batch:studio:5ab42827bba1c999650c76e9' --dry-run --json
reelmate ledger resolve 'hlm-ep-batch:studio:5ab42827bba1c999650c76e9' --json
```

## 与 `--force-replay` 的分工

两者解决同一个场景的不同环节，不要混用：

| | `ledger resolve KEY` | `--force-replay KEY` |
|---|---|---|
| 时机 | 先看再决定，独立一步 | 已复核完，直接带在重打的命令上 |
| 效果 | 删掉条目，之后任何命令都可重打 | 本次执行放行一次，随后仍走完整的三态保护 |
| 对非 `in_doubt` 的键 | 拒绝并说明原因 | 拒绝并说明原因（`applied` 另给 `--no-idempotency-guard` 作为替代） |

```bash
reelmate episode batch-create --workspace SP_ID --set @episodes.json \
  --idempotency-key hlm-ep-batch --force-replay 'hlm-ep-batch:studio:5ab42827...' --json
```

## 注意事项

- 账本是**状态**不是缓存：它落在 `state/` 而不是 `cache/`。删掉整个文件等于放弃全部
  重复提交保护，同键重放会真的重复创建、重复扣费。不要把它当缓存清理。
- 被退出码 11 拦下时的标准处置顺序：`ledger list --in-doubt` → `ledger show KEY` 看接口和条数
  → 用对应的只读命令（如 `episode list --all`）复核 → 确认未生效才 `resolve` 或 `--force-replay`；
  确认已生效则**不要重打**，改为按差量补。
- 不传 `--idempotency-key` 的写同样受保护，键形如 `auto:studio:<摘要>`。这类键在成功后
  不登记 `applied`（不影响「再写一次同样的内容」），只在结果未知时留下 `in_doubt`。
