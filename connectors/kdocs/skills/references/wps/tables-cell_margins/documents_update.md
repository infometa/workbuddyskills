# wps.tables.cell_margins

#### 功能说明

设置表格的单元格边距

**幂等性**：是 — safe

> datas 必填：4 个整数字符串 [上,下,左,右]（磅，1 厘米 ≈ 28.35 磅，0.19 厘米 ≈ 5 磅）；带 row/col 时写单格，不带时写整表默认边距
> 写后可用 verb=query 独立读回实际生效值确证

#### 调用示例

整表设置左右边距 5 磅、上下边距 0：

```json
{
  "file_id": "<FILE_ID>",
  "table_index": 1,
  "datas": [
    "0",
    "0",
    "5",
    "5"
  ]
}
```

单格设置（row/col 定位）：

```json
{
  "file_id": "<FILE_ID>",
  "table_index": 1,
  "row": 1,
  "col": 1,
  "datas": [
    "0",
    "0",
    "5",
    "5"
  ]
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一
- `verb` (string, 必填): HTTP 动作：query（查询） / update（设置）。可选值：`query` / `update`
- `col` (number, 可选): 列号（从 1 开始）；row/col 均不传时设置整表默认边距
- `datas` (array, 必填): 批量设置数据，固定 4 个整数字符串元素，顺序=[上,下,左,右] 边距（磅，取整），如 ["0","0","5","5"]
- `height` (number, 可选): 兜底单值口径：仅上边距（磅，取整）；推荐用 datas 四元组
- `row` (number, 可选): 行号（从 1 开始）；row/col 均不传时设置整表默认边距
- `table_index` (number, 必填): 表格索引，从 1 开始
- `width` (number, 可选): 兜底单值口径：仅左边距（磅，取整）；推荐用 datas 四元组

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {"tableIndex": 1, "row": 0, "col": 0, "topMargin": 0, "bottomMargin": 0, "leftMargin": 5.4, "rightMargin": 5.4}
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 0 表示成功 |
| `data` | object | 业务数据（含写入后的 topMargin/bottomMargin/leftMargin/rightMargin 回显，磅） |
| `message` | string | 结果说明 |

