# 视图管理

## 1. dbsheet.create_view

#### 功能说明

在指定数据表中创建新视图，支持表格、看板、画册、表单、甘特、日历等视图类型。



#### 操作约束

- **后置验证**：get_schema 确认视图已创建

**幂等性**：否 — 重复调用会创建多个视图，先确认是否已成功

#### 调用示例

创建看板视图：

```json
{
  "file_id": "string",
  "sheet_id": 1,
  "name": "看板视图",
  "type": "Kanban",
  "group_field": "状态"
}
```


#### 参数说明

- `file_id` (string, 必填): 多维表格文件 ID
- `sheet_id` (integer, 必填): 目标数据表 ID
- `name` (string, 必填): 视图名称
- `type` (string, 必填): 视图类型：Grid / Kanban / Gallery / Form / Gantt / Calendar
- `prefer_id` (boolean, 可选): 是否使用字段 ID 作为 key
- `group_field` (string, 可选): 分组字段名称

#### 返回值说明

```json
{
  "detail": {
    "view": { "id": "I", "name": "看板视图", "type": "Kanban" }
  },
  "result": "ok"
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `detail.view.id` | string | 新建视图 ID |
| `detail.view.name` | string | 视图名称 |
| `detail.view.type` | string | 视图类型 |
| `result` | string | ok 表示成功 |


---

## 2. dbsheet.update_view

#### 功能说明

更新视图的名称、字段顺序、字段显隐状态及列宽等展示配置。


#### 操作约束

- **前置检查**：get_schema 确认目标视图存在

**幂等性**：是

#### 调用示例

重命名并调整视图配置：

```json
{
  "file_id": "string",
  "sheet_id": 1,
  "view_id": "I",
  "name": "重命名视图",
  "order_fields": [
    "B",
    "D",
    "F",
    "E",
    "C"
  ],
  "fields_attribute": [
    {
      "field": "D",
      "hidden": true
    }
  ],
  "widths": [
    {
      "field": "B",
      "width": 1600
    }
  ]
}
```


#### 参数说明

- `file_id` (string, 必填): 多维表格文件 ID
- `sheet_id` (integer, 必填): 目标数据表 ID
- `view_id` (string, 必填): 视图 ID
- `name` (string, 可选): 新视图名称
- `prefer_id` (boolean, 可选): 是否使用字段 ID 作为 key
- `order_fields` (array, 可选): 字段排列顺序，字段 ID 数组
- `fields_attribute` (array, 可选): 字段显隐属性，每项包含 `field` 和 `hidden`
- `height` (integer, 可选): 行高（Twip 单位）
- `widths` (array, 可选): 字段列宽配置，每项包含 `field` 和 `width`

#### 返回值说明

```json
{
  "detail": {
    "view": { "id": "I", "name": "重命名视图", "type": "Grid" }
  },
  "result": "ok"
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `detail.view.id` | string | 视图 ID |
| `detail.view.name` | string | 视图名称 |
| `detail.view.type` | string | 视图类型 |
| `result` | string | ok 表示成功 |


---

## 3. dbsheet.delete_view

#### 功能说明

删除指定数据表中的视图。


#### 操作约束

- **前置检查**：get_schema 核对拟删视图的名称和类型
- **用户确认**：删除视图不可恢复，必须向用户确认视图名称和 ID

**幂等性**：是

#### 调用示例

删除视图：

```json
{
  "file_id": "string",
  "sheet_id": 1,
  "view_id": "I"
}
```


#### 参数说明

- `file_id` (string, 必填): 多维表格文件 ID
- `sheet_id` (integer, 必填): 目标数据表 ID
- `view_id` (string, 必填): 视图 ID

#### 返回值说明

```json
{
  "detail": {
    "view": { "id": "I" }
  },
  "result": "ok"
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `detail.view.id` | string | 已删除的视图 ID |
| `result` | string | ok 表示成功 |


---

## 4. dbsheet.views_list

#### 功能说明


**必填 query**：无。



#### 调用示例

列出视图：

```json
{
  "file_id": "string",
  "sheet_id": 1
}
```


#### 参数说明

- `file_id` (string, 必填): 多维表格文件 ID
- `sheet_id` (integer, 必填): 数据表 ID

#### 返回值说明

```json
{
  "result": "ok",
  "detail": {}
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `result` | string | ok 表示成功 |
| `detail` | object | views 列表 |


---

## 5. dbsheet.views_get

#### 功能说明


**必填 query**：无。



#### 调用示例

获取视图：

```json
{
  "file_id": "string",
  "sheet_id": 1,
  "view_id": "B"
}
```


#### 参数说明

- `file_id` (string, 必填): 多维表格文件 ID
- `sheet_id` (integer, 必填): 数据表 ID
- `view_id` (string, 必填): 视图 ID

#### 返回值说明

```json
{
  "result": "ok",
  "detail": {}
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `result` | string | ok 表示成功 |
| `detail` | object | view 对象 |


---

