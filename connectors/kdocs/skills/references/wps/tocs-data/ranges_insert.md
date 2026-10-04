# wps.tocs.data

#### 功能说明

按字符区间插入目录

> begin/end 为 0-based 字符区间；可由 wps.texts.search 返回的 ranges 回填。

#### 调用示例

字符区间插入：

```json
{
  "file_id": "<FILE_ID>",
  "begin": 1,
  "end": 74,
  "lower_level": 1,
  "scope": "ranges",
  "upper_level": 1,
  "verb": "insert"
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `scope` (string, 必填): 操作范围，固定为 ranges（按字符区间设置）。可选值：`ranges`
- `verb` (string, 必填): 操作类型，固定为 insert（插入）。可选值：`insert`
- `begin` (number, 可选): 区间起点（scope=ranges 时必填）
- `end` (number, 可选): 区间终点（scope=ranges 时必填）
- `lower_level` (number, 可选): 结束标题级别
- `upper_level` (number, 可选): 起始标题级别

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "toc_index": 1
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 0 表示成功 |
| `data` | object | 业务数据 |
| `message` | string | 结果说明 |

