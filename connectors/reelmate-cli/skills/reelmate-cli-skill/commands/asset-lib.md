# asset-lib

跨项目“我的资产库”命令组，用于目录、资产、资源和标签管理。

## 用法

```text
reelmate asset-lib dir create|list|rename|delete
reelmate asset-lib list|get|import|rename|delete
reelmate asset-lib search KEYWORD
reelmate asset-lib resource list|import|delete
reelmate asset-lib tag add|rm
reelmate asset-lib move
reelmate asset-lib batch-delete
reelmate asset-lib official download ELEMENT_ID
```

## 子命令说明

| 命令 | 作用 |
|---|---|
| `reelmate asset-lib dir create` | 创建资产目录 |
| `reelmate asset-lib dir list` | 列出资产目录 |
| `reelmate asset-lib dir rename` | 重命名资产目录 |
| `reelmate asset-lib dir delete` | 删除资产目录 |
| `reelmate asset-lib list` | 列出资产 |
| `reelmate asset-lib get` | 查询资产详情 |
| `reelmate asset-lib import` | 导入资产 |
| `reelmate asset-lib rename` | 重命名资产 |
| `reelmate asset-lib delete` | 删除资产 |
| `reelmate asset-lib search` | 按关键词搜索资产 |
| `reelmate asset-lib resource list` | 列出资产资源 |
| `reelmate asset-lib resource import` | 导入资产资源 |
| `reelmate asset-lib resource delete` | 删除资产资源 |
| `reelmate asset-lib tag add` | 添加标签 |
| `reelmate asset-lib tag rm` | 移除标签 |
| `reelmate asset-lib move` | 批量移动资产 |
| `reelmate asset-lib batch-delete` | 批量删除资产 |
| `reelmate asset-lib official download` | 下载官方元素 |

## `reelmate asset-lib dir create`

### 作用

创建资产目录。

### 参数与输出

参数以 `reelmate asset-lib --help` 为准。返回资产目录数据；远程错误会原样转为 CLI 错误。

### 示例

```bash
reelmate asset-lib dir create --json
```

## `reelmate asset-lib dir list`

### 作用

列出资产目录。

### 参数与输出

参数以 `reelmate asset-lib --help` 为准。

### 示例

```bash
reelmate asset-lib dir list --json
```

## `reelmate asset-lib dir rename`

### 作用

重命名资产目录。

### 参数与输出

参数以 `reelmate asset-lib --help` 为准。

### 示例

```bash
reelmate asset-lib dir rename --json
```

## `reelmate asset-lib dir delete`

### 作用

删除资产目录。会改变远端数据，执行前确认目标。

### 参数与输出

参数以 `reelmate asset-lib --help` 为准。

### 示例

```bash
reelmate asset-lib dir delete --json
```

## `reelmate asset-lib list`

### 作用

列出资产。

### 参数与输出

参数以 `reelmate asset-lib --help` 为准。

### 示例

```bash
reelmate asset-lib list --json
```

## `reelmate asset-lib get`

### 作用

查询资产详情。

### 参数与输出

参数以 `reelmate asset-lib --help` 为准。

### 示例

```bash
reelmate asset-lib get --json
```

## `reelmate asset-lib import`

### 作用

导入资产。会改变远端数据，执行前确认目标。

### 参数与输出

参数以 `reelmate asset-lib --help` 为准。

### 示例

```bash
reelmate asset-lib import --json
```

## `reelmate asset-lib rename`

### 作用

重命名资产。

### 参数与输出

参数以 `reelmate asset-lib --help` 为准。

### 示例

```bash
reelmate asset-lib rename --json
```

## `reelmate asset-lib delete`

### 作用

删除资产。会改变远端数据，执行前确认目标。

### 参数与输出

参数以 `reelmate asset-lib --help` 为准。

### 示例

```bash
reelmate asset-lib delete --json
```

## `reelmate asset-lib search`

### 作用

按关键词搜索资产。`KEYWORD` 不是资产 ID。

### 参数与输出

位置参数 `KEYWORD` 为搜索关键词。

### 示例

```bash
reelmate asset-lib search character --json
```

## `reelmate asset-lib resource list`

### 作用

列出资产资源。

### 参数与输出

参数以 `reelmate asset-lib --help` 为准。

### 示例

```bash
reelmate asset-lib resource list --json
```

## `reelmate asset-lib resource import`

### 作用

导入资产资源。

### 参数与输出

参数以 `reelmate asset-lib --help` 为准。

### 示例

```bash
reelmate asset-lib resource import --json
```

## `reelmate asset-lib resource delete`

### 作用

删除资产资源。

### 参数与输出

参数以 `reelmate asset-lib --help` 为准。

### 示例

```bash
reelmate asset-lib resource delete --json
```

## `reelmate asset-lib tag add`

### 作用

添加标签。

### 参数与输出

参数以 `reelmate asset-lib --help` 为准。

### 示例

```bash
reelmate asset-lib tag add --json
```

## `reelmate asset-lib tag rm`

### 作用

移除标签。

### 参数与输出

参数以 `reelmate asset-lib --help` 为准。

### 示例

```bash
reelmate asset-lib tag rm --json
```

## `reelmate asset-lib move`

### 作用

批量移动资产。

### 参数与输出

参数以 `reelmate asset-lib --help` 为准。

### 示例

```bash
reelmate asset-lib move --json
```

## `reelmate asset-lib batch-delete`

### 作用

批量删除资产。会改变远端数据，执行前确认目标。

### 参数与输出

参数以 `reelmate asset-lib --help` 为准。

### 示例

```bash
reelmate asset-lib batch-delete --json
```

## `reelmate asset-lib official download`

### 作用

下载官方元素。`ELEMENT_ID` 不能当作普通资产 ID 使用。

### 参数与输出

位置参数 `ELEMENT_ID` 为官方元素标识。

### 示例

```bash
reelmate asset-lib official download ELEMENT_ID --json
```

## 注意事项

- 目录写入、资产导入/删除和官方下载等操作会改变远端数据，执行前确认目标。
- `KEYWORD` 不是资产 ID，`ELEMENT_ID` 也不能当作普通资产 ID 使用。
