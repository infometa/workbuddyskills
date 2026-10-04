# wps.breaks.data

#### 功能说明

按字符区间插入分隔符

> begin/end 为 0-based 字符区间；可由 wps.texts.search 返回的 ranges 回填。

#### 调用示例

字符区间插入：

```json
{
  "file_id": "<FILE_ID>",
  "begin": 1,
  "break_type": 7,
  "end": 74,
  "scope": "ranges"
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `scope` (string, 必填): 操作范围，固定为 ranges（按字符区间设置）。可选值：`ranges`
- `begin` (number, 可选): 区间起点（scope=ranges 时必填）
- `break_type` (number, 必填): 分隔符类型（WdBreakType）：2=下一页分节, 3=连续分节, 4=偶数页分节, 5=奇数页分节, 6=软回车, 7=分页符, 8=分栏符
- `end` (number, 可选): 区间终点（scope=ranges 时必填）

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "begin": 50,
    "end": 50,
    "break_type": 7
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 0 表示成功 |
| `data` | object | 业务数据 |
| `message` | string | 结果说明 |

