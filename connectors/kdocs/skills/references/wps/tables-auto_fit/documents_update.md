# wps.tables.auto_fit

#### 功能说明

设置表格的自动调整（固定列宽/适应内容/适应窗口）

**幂等性**：是 — safe

> auto_fit_behavior 缺省为 1（contents，列宽适应内容）；0=fixed 固定列宽，2=window 适应窗口

#### 调用示例

文档设置：

```json
{
  "file_id": "<FILE_ID>",
  "table_index": 1,
  "auto_fit_behavior": 1
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一
- `verb` (string, 必填): HTTP 动作：query（查询） / update（设置）。可选值：`query` / `update`
- `table_index` (number, 必填): 表格索引，从 1 开始
- `auto_fit_behavior` (number, 可选): 表格自适应方式：0=fixed 固定列宽，1=contents 适应内容（缺省），2=window 适应窗口。可选值：`0` / `1` / `2`；默认值：`1`

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

