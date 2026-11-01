# env

查看当前 API、账号摘要、作用域来源和缓存根目录，用于排障。命令不修改远端数据。

## 用法

```text
reelmate env info [--json]
```

## 子命令说明

| 命令 | 作用 |
|---|---|
| `reelmate env info` | 查看当前配置和作用域；省略子命令时也按 `info` 处理 |

## `reelmate env info`

### 作用

输出 CLI 当前使用的 API、账号、作用域和本地缓存配置。

### 参数

- `--json`：输出 JSON。

### 输出

包含 uid 和配置来源等诊断信息，不包含 token。

### 示例

```bash
reelmate env info --json
```

## 注意事项

- 该命令只读，不会修改远端数据。
