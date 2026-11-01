# upload

上传本地文件到当前空间的云存储。CLI 会计算指纹，优先秒传；大文件走分片上传并保存本地断点。上传完成后会调用内容审核，审核未通过不会返回可继续使用的成功态。

## 用法

```text
reelmate upload PATH [--workspace WORKSPACE_ID] [--space SPACE_ID] [--json|--ndjson]
```

## 子命令说明

| 命令 | 作用 |
|---|---|
| `reelmate upload PATH` | 读取一个本地文件并上传到当前空间 |

## `reelmate upload PATH`

### 作用

上传并审核一个本地文件，成功后返回可供 `material add` 使用的 `file_id`。

### 参数

- `PATH`（必填）：本地文件路径，只能传一个位置参数。
- `--workspace WORKSPACE_ID`：显式指定工作区作用域。
- `--space SPACE_ID`：显式指定上传空间；省略时自动解析。
- `--json` / `--ndjson`：选择输出格式。

### 输出

成功数据包含 `file_id`、文件大小、是否秒传和是否从断点恢复等信息。

### 示例

```bash
reelmate upload ./assets/hero.png --space SPACE_ID --json
reelmate upload ./video.mp4 --workspace WORKSPACE_ID --space SPACE_ID --ndjson
```

## 注意事项

- 上传完成后会进行内容审核；审核未通过不会返回可继续使用的成功态。
- 无法确定空间时，命令会在本地失败，不会发送不完整请求。
- 上传 checkpoint 只属于本地恢复数据，不要提交到仓库。
