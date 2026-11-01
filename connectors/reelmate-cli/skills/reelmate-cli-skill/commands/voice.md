# voice

列出普通音色、分类和克隆音色。CLI 会分别获取三个来源并聚合结果，单个来源失败会保留在 `source_errors`。

## 用法

```text
reelmate voice list [--space SPACE_ID] [--json]
```

## 子命令说明

| 命令 | 作用 |
|---|---|
| `reelmate voice list` | 查询当前空间可见音色 |

## `reelmate voice list`

### 作用

查询当前空间可用的普通、分类和克隆音色。

### 参数

- `--space SPACE_ID`：指定查询空间；省略时按当前绑定作用域解析。
- `--json`：输出 JSON。

### 输出

返回聚合后的音色列表；部分来源失败时同时返回 `source_errors`。

### 示例

```bash
reelmate voice list --space SPACE_ID --json
```

## 注意事项

- 三个来源全部失败时命令失败；部分来源失败仍会返回成功数据。
- 返回的 voice ID 可写入音频节点的 `voice.voiceId`。
