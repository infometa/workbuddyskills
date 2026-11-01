# task

任务命令用于查询异步生成、等待终态和处理失败任务。

## 用法

```text
reelmate task get TASK_ID
reelmate task list
reelmate task wait TASK_ID [TASK_ID ...]
reelmate task cancel TASK_ID
reelmate task retry TASK_ID
reelmate task regenerate TASK_ID
reelmate task download TASK_ID --set path=LOCAL_DIR [--set overwrite=true] [--dry-run] --json
reelmate task delete TASK_ID
```

## 子命令说明

| 命令 | 作用 |
|---|---|
| `reelmate task get TASK_ID` | 查询任务详情 |
| `reelmate task list` | 查看空间任务列表 |
| `reelmate task wait TASK_ID` | 等待一个或多个任务终态 |
| `reelmate task cancel TASK_ID` | 取消任务 |
| `reelmate task retry TASK_ID` | 重试失败任务 |
| `reelmate task regenerate TASK_ID` | 使用原任务信息重新生成 |
| `reelmate task download TASK_ID` | 下载任务产物 |
| `reelmate task delete TASK_ID` | 删除任务记录 |

## `reelmate task get TASK_ID`

### 作用

查询单个任务。

### 参数

- `TASK_ID`（必填）：任务 ID。
- `--space SPACE_ID`、`--json`：空间和输出格式。

### 输出

返回任务状态、参数、错误和产物信息。

### 示例

```bash
reelmate task get TASK_ID --json
```

## `reelmate task list`

### 作用

列出当前空间任务。

所有列表命令的分页口径一致：**默认只取第一页**，`--set page=N` 逐页取、`--set page_size=N` 改单页条数、`--set all=true` 按服务端总数一次取完。输出带 `count`（服务端总数）、`page`、`page_size`、`has_more`、`next_page`；`has_more=true` 时不要把这份列表当成全量去做批量操作或判断某条记录不存在。

### 参数

- `--space SPACE_ID`：指定空间；省略时按绑定作用域解析。
- `--set page=N` / `--set page_size=N` / `--set all=true`：分页。
- `--json`：输出 JSON。

### 输出

返回任务列表和状态摘要。

### 示例

```bash
reelmate task list --space SPACE_ID --json
```

## `reelmate task wait TASK_ID [TASK_ID ...]`

### 作用

阻塞等待一个或多个任务进入终态。

### 参数

- `TASK_ID`（至少一个）：待等待任务，可重复位置传入。
- `--timeout DURATION`：显式设置客户端超时；默认无超时。
- `--ndjson`：逐行输出进度或终态。

### 输出

返回任务终态；收到中断信号时停止等待，不自动取消远端任务。

### 示例

```bash
reelmate task wait TASK_ID --timeout 2h
reelmate task wait TASK_A TASK_B --ndjson
```

## `reelmate task cancel TASK_ID`

### 作用

取消任务。

### 参数

- `TASK_ID`（必填）：任务 ID。
- `--space SPACE_ID`、`--idempotency-key KEY`：空间和幂等键。
- `--dry-run`：预演，不发请求，输出将要打到的 `method` 与 `endpoint`。

### 输出

返回取消结果。

### 示例

```bash
reelmate task cancel TASK_ID --idempotency-key KEY --json
```

## `reelmate task retry TASK_ID`

### 作用

重试失败任务。

### 参数

- `TASK_ID`（必填）：失败任务 ID。
- `--space SPACE_ID`、`--idempotency-key KEY`：空间和幂等键。
- `--dry-run`：预演，不发请求，输出将要打到的 `method` 与 `endpoint`。**重试会重复下单扣费**，提交前先跑一次。

### 输出

返回新的任务或重试结果。

### 示例

```bash
reelmate task retry TASK_ID --idempotency-key KEY --json
```

## `reelmate task regenerate TASK_ID`

### 作用

使用原任务信息重新提交生成。

### 参数

- `TASK_ID`（必填）：原任务 ID。
- `--space SPACE_ID`、`--idempotency-key KEY`：空间和幂等键。
- `--dry-run`：预演，不发请求，输出将要打到的 `method` 与 `endpoint`。**重新提交会再次扣费**，提交前先跑一次。

### 输出

返回新任务 ID。

### 示例

```bash
reelmate task regenerate TASK_ID --idempotency-key KEY --json
```

## `reelmate task download TASK_ID`

### 作用

把成功任务的全部产物下载到本地目录。命令读取 `task_infos[].asset_info.file_id`，同时支持图片、视频和混合多产物任务。

### 参数

- `TASK_ID`（必填）：已完成任务 ID。
- `--set path=LOCAL_DIR`（必填）：本地产物目标目录。
- `--set overwrite=true`：允许替换目录中的同名文件；默认 `false`，任一目标冲突都会在下载开始前整体失败。
- `--space SPACE_ID`：任务空间。
- `--dry-run`：只输出 `task_id`、`path`、`overwrite`，不请求任务或 Drive，也不写文件。
- `--json`：输出稳定 JSON 字段。

### 输出

返回 `task_id` 和 `files[{file_id,path,size}]`。输出不包含 Drive 短期签名 URL。

服务端文件名会清洗为基础文件名；同名产物按稳定顺序添加 `-2`、`-3` 等后缀，缺少文件名时使用 `file_id`。

### 示例

```bash
reelmate task download TASK_ID \
  --space SPACE_ID \
  --set path=downloads \
  --json
```

## `reelmate task delete TASK_ID`

### 作用

删除任务记录。

### 参数

- `TASK_ID`（必填）：任务 ID。
- `--space SPACE_ID`、`--idempotency-key KEY`：空间和幂等键。
- `--dry-run`：预演，不发请求，输出将要打到的 `method` 与 `endpoint`。

### 输出

返回删除结果。

### 示例

```bash
reelmate task delete TASK_ID --idempotency-key KEY --json
```

## 注意事项

- `TASK_ID` 通常来自 `node generate` 或其它生成命令的成功返回。
- `group execute` 在 CLI 内部等待整组完成，不产生需要外部再次等待的单一任务 ID。
- 任务终态会映射到对应退出码，脚本不要只依赖表格文本。
