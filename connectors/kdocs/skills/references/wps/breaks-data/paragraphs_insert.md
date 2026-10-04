# wps.breaks.data

#### 功能说明

按段落插入分隔符

> paragraph_index 为 1-based；可由 wps.texts.range（段落 → begin/end）或 wps.texts.search 定位后换算。

#### 调用示例

段落插入：

```json
{
  "file_id": "<FILE_ID>",
  "break_type": 7,
  "paragraph_index": 1,
  "scope": "paragraphs",
  "text": "smoke example text"
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `scope` (string, 必填): 操作范围，固定为 paragraphs（按段落设置）。可选值：`paragraphs`
- `break_type` (number, 必填): 分隔符类型（WdBreakType）：2=下一页分节, 3=连续分节, 4=偶数页分节, 5=奇数页分节, 6=软回车, 7=分页符, 8=分栏符
- `paragraph_index` (number, 可选): 段落索引（scope=paragraphs 时必填）

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "paragraph_index": 1,
    "break_type": 7
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 0 表示成功 |
| `data` | object | 业务数据 |
| `message` | string | 结果说明 |

