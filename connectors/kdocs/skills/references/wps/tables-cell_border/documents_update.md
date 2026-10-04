# wps.tables.cell_border

#### 功能说明

设置表格的单元格边框

**幂等性**：是 — safe

> 一次只写一个 border_index 的一个属性；四边全部设置需分别调用 border_index=-1/-2/-3/-4
> border_key 必须 PascalCase、border_value 必须数字字符串，写错不报错但读回不变（静默无效）

#### 调用示例

单元格上边框设为双线：

```json
{
  "file_id": "<FILE_ID>",
  "table_index": 1,
  "row": 1,
  "col": 1,
  "border_index": -1,
  "border_key": "LineStyle",
  "border_value": "7"
}
```

单元格上边框线宽 1.5 磅：

```json
{
  "file_id": "<FILE_ID>",
  "table_index": 1,
  "row": 1,
  "col": 1,
  "border_index": -1,
  "border_key": "LineWidth",
  "border_value": "12"
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一
- `verb` (string, 必填): HTTP 动作：query（查询） / update（设置）。可选值：`query` / `update`
- `border_index` (number, 必填): 边框位置索引（WdBorderIndex）：-1=上边 top、-2=左边 left、-3=下边 bottom、-4=右边 right；1=左上对角线等
- `border_key` (string, 必填): 边框属性名，PascalCase 的 Border 对象属性（大小写敏感）：LineStyle（线型）/ LineWidth（线宽）/ Color（颜色 BGR 整数）/ ColorIndex（颜色索引）/ Visible（可见性）。小写或 snake_case 键会静默无效（JS 侧变成新增属性，不报错）
- `border_value` (string, 必填): 边框属性值，纯数字枚举字符串（不支持小数与枚举名）。LineStyle（WdLineStyle）：0=无框 1=单实线 2=虚线 3=点线 4=点划线-单双点 5=点划线 6=点划线-双点 7=双线；LineWidth（WdLineWidth，单位 1/8 磅整数）：4=0.5磅 6=0.75磅 8=1磅 12=1.5磅 24=3磅；Color：BGR 整数（黑=0）
- `col` (number, 可选): 列号
- `row` (number, 可选): 行号
- `table_index` (number, 必填): 表格索引，从 1 开始

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

