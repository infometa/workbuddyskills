# wps.texts.tab_stops

#### 功能说明

设置文本的制表位

**幂等性**：是 — safe

> 写操作报 500002 且读操作正常时，先排查文档保护态（wps.protection.disable 后重试），再排查参数；不要盲目重试。

#### 调用示例

段落设置：

```json
{
  "file_id": "<FILE_ID>",
  "verb": "update",
  "paragraph_index": 1,
  "tab_alignment": 1,
  "tab_leader": 1,
  "tab_position": 1
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一
- `verb` (string, 必填): 操作类型，固定为 update（更新）。可选值：`update`
- `paragraph_index` (number, 必填): 段落索引，从 1 开始
- `tab_alignment` (number, 可选): tab alignment
- `tab_leader` (number, 可选): tab leader
- `tab_position` (number, 可选): tab position

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {}
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 0 表示成功 |
| `data` | object | 业务数据 |
| `message` | string | 结果说明 |

