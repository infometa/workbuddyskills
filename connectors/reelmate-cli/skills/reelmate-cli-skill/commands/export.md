# export

导出剧集或画布生成结果。

## 用法

```text
reelmate export EPISODE_ID [--workspace WORKSPACE_ID] [--json]
reelmate export merge EPISODE_ID [--name VIDEO_NAME] [--set key=value ...]
reelmate export get EXPORT_ID
reelmate export download EXPORT_ID --set path=LOCAL_FILE [--set overwrite=true]
```

## 子命令说明

| 命令 | 作用 |
|---|---|
| `reelmate export EPISODE_ID` | 导出指定剧集的分镜素材 |
| `reelmate export merge EPISODE_ID` | 按分镜顺序把已定稿视频合并为最终成片 |
| `reelmate export get EXPORT_ID` | 查询导出记录及最终 `file_id` |
| `reelmate export download EXPORT_ID` | 将成功的导出记录下载为本地交付文件 |

## `reelmate export EPISODE_ID`

### 作用

提交指定剧集的分镜素材导出请求。该旧用法保持兼容，不等于合并成片。

### 参数

- `EPISODE_ID`（必填）：要导出的剧集 ID。
- `--workspace WORKSPACE_ID`、`--space SPACE_ID`：作用域。
- `--json`：输出 JSON。

### 输出

返回导出任务或导出结果。

### 示例

```bash
reelmate export EPISODE_ID --workspace WORKSPACE_ID --json
```

## `reelmate export merge EPISODE_ID`

### 作用

调用剧集工作台的成片合成接口，按分镜顺序把已定稿视频合并为最终成片。不等于旧用法 `reelmate export EPISODE_ID`。

### 参数与输出

默认导出 `1920x1080`、`mp4`；可用 `--name VIDEO_NAME` 和 `--set` 覆盖。返回的 `task_id` 同时也是 `EXPORT_ID`。

### 示例

```bash
reelmate export merge EPISODE_ID --name final.mp4 \
  --set resolution_width=1920 --set resolution_height=1080 \
  --set ratio=16:9 --set file_format=mp4 --dry-run --json
```

预演确认后去掉 `--dry-run` 并加唯一的 `--idempotency-key`。返回的 `task_id` 同时也是 `EXPORT_ID`，用普通任务结果通道等待：

```bash
reelmate task wait EXPORT_ID --timeout 30m --json
reelmate export get EXPORT_ID --json
```

## `reelmate export get EXPORT_ID`

### 作用

查询导出记录及最终 `file_id`。

### 参数与输出

只输出稳定的公开导出字段，例如 `export_id`、`task_id`、`status`、`progress`、`file_id`、名称、格式和失败原因。响应中的下载地址、封面地址等短期签名 URL 不进入 stdout；实际下载只能走 `export download`。

### 示例

```bash
reelmate export get EXPORT_ID --json
```

## `reelmate export download EXPORT_ID`

### 作用

将成功的导出记录下载为本地交付文件。

### 参数与输出

只接受状态为成功（`status=2`）且带最终 `file_id` 的导出记录。CLI 按前端同款 Drive 批量下载接口换取短期签名地址，签名地址不会打印到输出；文件先写同目录临时文件，再原子改名。目标已存在时默认拒绝覆盖；确需覆盖时显式传 `--set overwrite=true`。`--out` 仍只控制命令 JSON/表格输出，不能当视频路径使用。

### 示例

```bash
reelmate export download EXPORT_ID \
  --set path=deliverables/final.mp4 --json
```

目标已存在时默认拒绝覆盖；确需覆盖时显式传 `--set overwrite=true`。`--out` 仍只控制命令 JSON/表格输出，不能当视频路径使用。

## 注意事项

- `export merge` 只合并剧集当前已定稿的视频，不会生成缺失的分镜视频。
- 导出会产生远端任务，任务 ID 可用 `reelmate task wait TASK_ID` 等待。
- GUI 环节 1→4 默认在分镜视频生成完成后结束；`export merge` 与 `export download` 仅在用户明确选择合并导出时执行。
- 用户选择合并导出后，本地 MP4 是该可选步骤的交付物，必须下载并验证后再反馈该步骤完成。
