# file

通过 `file_id` 或 `object_id` 反查云盘文件信息。命令走 Drive API，与主站 API 的 header 和 token 不同。

## 用法

```text
reelmate file metadata FILE_ID [--space SPACE_ID] [--json]
reelmate file object OBJECT_ID [--space SPACE_ID] [--json]
reelmate file sign-url FILE_ID [--space SPACE_ID] [--json]
```

## 子命令说明

| 命令 | 作用 |
|---|---|
| `reelmate file metadata FILE_ID` | 查询文件元数据 |
| `reelmate file object OBJECT_ID` | 按对象 ID 查询文件信息 |
| `reelmate file sign-url FILE_ID` | 获取短期签名访问地址 |

## `reelmate file metadata FILE_ID`

### 作用

查询云盘文件元数据。

### 参数

- `FILE_ID`（必填）：云盘文件标识。
- `--space SPACE_ID`：查询空间。
- `--json`：输出 JSON。

### 输出

返回脱敏后的文件 ID、名称、大小、空间和服务端字段。

### 示例

```bash
reelmate file metadata FILE_ID --space SPACE_ID --json
```

## `reelmate file object OBJECT_ID`

### 作用

按云盘对象 ID 查询文件信息。

### 参数

- `OBJECT_ID`（必填）：对象标识，不能用 `FILE_ID` 替代。
- `--space SPACE_ID`：查询空间。
- `--json`：输出 JSON。

### 输出

返回对象对应的文件信息。

### 示例

```bash
reelmate file object OBJECT_ID --space SPACE_ID --json
```

## `reelmate file sign-url FILE_ID`

### 作用

获取文件的短期签名访问地址。

### 参数

- `FILE_ID`（必填）：云盘文件标识。
- `--space SPACE_ID`：查询空间。
- `--json`：输出 JSON。

### 输出

返回短期签名 URL。

### 示例

```bash
reelmate file sign-url FILE_ID --space SPACE_ID --json
```

## 注意事项

- 每个子命令恰好接受一个 ID。
- `FILE_ID` 可从 `reelmate upload PATH --json` 的 `file_id` 取得；`OBJECT_ID` 必须由上游系统提供。
- 签名地址只用于短期访问，不要写入日志或长期配置。
