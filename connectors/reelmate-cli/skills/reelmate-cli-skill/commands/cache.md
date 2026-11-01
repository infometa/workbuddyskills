# cache

查看或清理本地可重建缓存。缓存不包含凭据、设备 ID、工作区绑定或幂等账本。

## 用法

```text
reelmate cache info
reelmate cache clear --scope models|env|uploads
```

## 子命令说明

| 命令 | 作用 |
|---|---|
| `reelmate cache info` | 查看缓存状态 |
| `reelmate cache clear` | 清理指定范围缓存 |

## `reelmate cache info`

### 作用

查看缓存目录和各缓存范围的状态。

### 参数

- `--json`：输出 JSON。

### 输出

返回本地缓存状态；缓存目录不存在时返回空状态。

### 示例

```bash
reelmate cache info --json
```

## `reelmate cache clear`

### 作用

清理可以重新获取的本地缓存。

### 参数

- `--scope`（必填）：`models`、`env` 或 `uploads`。

### 输出

返回清理结果。

### 示例

```bash
reelmate cache clear --scope models
reelmate cache clear --scope uploads
```

## 注意事项

- 只影响本地缓存，不应影响登录或工作区绑定。
