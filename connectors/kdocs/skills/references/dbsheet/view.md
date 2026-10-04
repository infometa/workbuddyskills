# 视图管理

## 1. dbsheet.create_view

#### 功能说明

在指定数据表中创建新视图，支持表格、看板、画册、表单、甘特、日历等视图类型。

#### 调用约束

- **前置检查**：file_id、sheet_id、name、type 四个参数全部必填
- **前置检查**：使用该工具前必须先调用get_schema确认要操作的数据表id，不得自行捏造数据表id。
- **禁止**：`type` 必须首字母大写，禁止小写（如 `grid`），禁止非法值（如 `Dashboard`），否则返回 `InvalidArgument`
- **后置验证**：get_schema 确认视图已创建

**幂等性**：否 — 重复调用会创建多个视图，先确认是否已成功

> `type` 合法枚举值（首字母大写）：`Grid`、`Kanban`、`Gallery`、`Form`、`Gantt`、`Calendar`、`Query`
> `Calendar` 类型要求表中至少有一个 Date 字段，否则创建失败
> `Kanban` 类型自动选取首个选项字段作为分组字段，禁止手动传 `group_field`
> 所有 ID 通过 `dbsheet.get_schema` 获取，禁止凭空捏造

#### 调用示例

创建视图：

```json
{
  "file_id": "string",
  "sheet_id": 1,
  "name": "新建视图",
  "type": "Grid",
  "group_field": "状态"
}
```

#### 参数说明

- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享链接 ID
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 ID
- `sheet_id` (integer, 必填): 目标数据表 ID
- `name` (string, 必填): 视图名称
- `type` (string, 必填): 视图类型（首字母大写），禁止小写。可选值：`Grid` / `Kanban` / `Gallery` / `Form` / `Gantt` / `Calendar` / `Query`
- `prefer_id` (boolean, 可选): 是否使用字段 ID 和选项 ID 标识
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

⚠️ **调整字段顺序（`order_fields`）时必须提供数据表内全部字段，缺一不可，否则会报 `Modifying fields order failed, all fields in sheet should be provided`。**
所有字段 ID 和视图 ID 必须通过 `dbsheet.get_schema` 获取，禁止凭空捏造。`file_id`、`sheet_id`、`view_id` 三个顶层参数全部必填。
⚠️ **视图名称不能与表中已有视图重复**，否则会报 `View name conflict`。

更新视图的名称、字段顺序、字段显隐状态及列宽等展示配置。

#### 工具选择

- **勿用**（改用 `dbsheet.update_fields`）：修改主键字段属性

#### 调用约束

- **前置检查**：get_schema 确认目标视图存在
- **前置检查**：使用该工具前必须先调用get_schema和dbsheet.views_list确认要操作的数据表id和视图id，不得自行捏造数据表id和视图id。

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

- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享链接 ID
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 ID
- `sheet_id` (integer, 必填): 目标数据表 ID
- `view_id` (string, 必填): 视图 ID
- `name` (string, 可选): 新视图名称
- `prefer_id` (boolean, 可选): 是否使用字段 ID 和选项 ID 标识
- `order_fields` (array, 可选): 字段排列顺序，字段名数组（非字段 ID），需与表中所有字段一一对应
- `fields_attribute` (array, 可选): 字段显隐属性，每项包含 `field`（字段名）和 `hidden`（布尔值）
- `height` (integer, 可选): 记录行高（Twip 单位），Grid 视图专属
- `widths` (array, 可选): 字段列宽配置，每项包含 `field`（字段名）和 `width`（整数值），Grid 视图专属

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

#### 调用约束

- **前置检查**：get_schema 核对拟删视图的名称和类型；使用该工具前必须先调用get_schema和dbsheet.views_list确认要操作的数据表id和视图id，不得自行捏造数据表id和视图id。
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

- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享链接 ID
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 ID
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

列出视图

#### 调用约束

- **前置检查**：使用该工具前必须先调用get_schema确认要操作的数据表id，不得自行捏造数据表id。

**幂等性**：是

#### 调用示例

列出视图：

```json
{
  "file_id": "string",
  "sheet_id": 1
}
```

#### 参数说明

- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享链接 ID
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 ID
- `sheet_id` (integer, 必填): 数据表 ID（整数，不可传字符串）

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

获取单个视图

#### 调用约束

- **前置检查**：使用该工具前必须先调用get_schema和dbsheet.views_list确认要操作的数据表id和视图id，不得自行捏造数据表id和视图id。

**幂等性**：是

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

- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享链接 ID
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 ID
- `sheet_id` (integer, 必填): 数据表 ID（整数，不可传字符串）
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
