# wps.indexes.entry

## 1. wps.indexes.entry

#### 功能说明

插入在线文字文档索引项。

> 须在未保护文档上对有效区间插入 XE 索引项域；保护未解除时必失败。
> begin/end 为 0-based 且 begin>0；插入后会增加 fields 列表项。
> index_entry 为索引中显示的文字，不是 index 序号参数。
> begin/end 可由 wps.texts.search 返回的 ranges 回填。

#### 调用示例

字符区间插入：

```json
{
  "file_id": "<FILE_ID>",
  "begin": 1,
  "end": 74,
  "index_entry": "smoke index"
}
```

#### 参数说明

- `begin` (number, 必填): 范围起点
- `end` (number, 必填): 范围终点
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id
- `index_entry` (string, 必填): 索引项文本
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL

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
