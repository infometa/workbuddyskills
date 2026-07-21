# 数据表管理

## 1. dbsheet.get_schema

#### 功能说明

获取多维表格文档的 Schema 信息，包括所有数据表、字段和视图的结构。可指定单个数据表 ID，不填则返回全部。



#### 调用示例

获取全部数据表结构：

```json
{
  "file_id": "string"
}
```

获取指定数据表结构：

```json
{
  "file_id": "string",
  "sheet_id": 1
}
```


#### 参数说明

- `file_id` (string, 必填): 多维表格文件 ID
- `sheet_id` (integer, 可选): 指定数据表 ID，不填则返回所有表
- `reserve_no_permission_sheet` (boolean, 可选): 是否保留无权限的表；默认值：`false`
- `show_very_hidden` (boolean, 可选): 是否显示深度隐藏的表；默认值：`true`
- `include_all_record_ids` (boolean, 可选): 是否返回所有记录 ID；默认值：`false`

#### 返回值说明

```json
{
  "detail": {
    "sheets": [
      {
        "id": 3,
        "name": "数据表",
        "primary_field_id": "B",
        "records_count": 100,
        "record_ids": ["A", "B"],
        "fields": [
          { "id": "B", "name": "名称", "type": "SingleLineText", "description": "字段备注" },
          { "id": "C", "name": "数量", "type": "Number", "description": "字段备注" }
        ],
        "views": [
          { "id": "B", "name": "表格视图", "type": "grid", "records_count": 10 }
        ]
      }
    ],
    "book_type": "db"
  },
  "result": "ok"
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `detail.sheets[].id` | integer | 数据表 ID |
| `detail.sheets[].name` | string | 数据表名称 |
| `detail.sheets[].primary_field_id` | string | 主字段 ID |
| `detail.sheets[].records_count` | integer | 总记录数 |
| `detail.sheets[].record_ids` | array | 所有记录 ID（需开启 `include_all_record_ids`） |
| `detail.sheets[].fields` | array | 字段列表 |
| `detail.sheets[].views` | array | 视图列表 |
| `detail.book_type` | string | 文档类型标识，固定为 db |
| `result` | string | ok 表示成功 |


---

## 2. dbsheet.create_sheet

#### 功能说明

在多维表格文档中创建新的数据表，支持同时指定初始视图和字段。`fields[]` 中每个字段必须包含 `name`、`type`，字段专属参数直接平铺在字段对象根级（无 `data` 包装层）。



#### 操作约束

- **后置验证**：get_schema 确认数据表已创建

**幂等性**：否 — 重复调用会创建多个数据表，先确认是否已成功

> 此接口的 `fields[]` 配置不使用 `data` 包装层，所有字段属性（如 `items`、`numberFormat`）直接写在字段对象根级
> `dbsheet.create_sheet` 与 `dbsheet.create_fields` 在字段参数结构上保持一致：字段专属参数均直接平铺在字段对象根级
> 视图类型（`views[].type`）请求传入小写（如 `grid`），响应返回首字母大写（如 `Grid`）
> `Url` 字段传字符串时地址和显示文本相同；传对象时可分别设置 `address` 和 `displayText`
> 需要对字段做精细配置（如日期格式、关联目标表等）时，建议创建数据表后再通过 `dbsheet.update_fields` 补充

#### 调用示例

创建带初始字段的数据表：

```json
{
  "file_id": "string",
  "name": "新数据表",
  "views": [
    {
      "name": "默认视图",
      "type": "grid"
    }
  ],
  "fields": [
    {
      "name": "名称",
      "type": "SingleLineText"
    },
    {
      "name": "状态",
      "type": "SingleSelect",
      "items": [
        {
          "value": "待处理"
        },
        {
          "value": "已完成"
        }
      ]
    }
  ]
}
```


#### 参数说明

- `file_id` (string, 必填): 多维表格文件 ID（路径参数）
- `name` (string, 必填): 数据表名称
- `sync_type` (string, 可选): 同步类型；默认值：`None`
- `after_sheet_id` (integer, 可选): 插入到指定数据表之后
- `before_sheet_id` (integer, 可选): 插入到指定数据表之前
- `views` (array, 可选): 初始视图列表（见 param_detail 视图类型枚举）
  - `name` (string, 必填): 视图名称
  - `type` (string, 必填): 视图类型枚举，小写，如 `grid`、`kanban`、`gallery` 等（见 param_detail）
- `fields` (array, 可选): 初始字段列表（见 param_detail 字段类型枚举与参数明细）；字段配置直接平铺在字段对象根级（无 `data` 包装层）
  - `name` (string, 必填): 字段显示名称
  - `type` (string, 必填): 字段类型枚举（见 param_detail）
  - `syncField` (boolean, 可选): 是否为同步字段，默认 `false`
  - `width` (integer, 可选): 字段宽度，单位缇（1/1440 英寸）
  - 类型专属参数直接平铺（如 `items`、`numberFormat`、`max`、`linkSheet` 等）

**请求体根级**

| 名称 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | 是 | 新建数据表名称 |
| `syncType` | string | 否 | 同步类型，默认 `None` |
| `afterSheetId` | integer | 否 | 在指定数据表后创建 |
| `beforeSheetId` | integer | 否 | 在指定数据表前创建 |
| `views` | array[object] | 否 | 初始视图列表 |
| `fields` | array[object] | 否 | 初始字段列表，字段参数直接平铺，无 `data` |

**`fields[]` 通用参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | 是 | 字段显示名称 |
| `type` | string | 是 | 字段类型 |
| `syncField` | boolean | 否 | 是否为同步字段，默认 `false` |
| `width` | integer | 否 | 字段宽度，单位缇（1/1440 英寸） |
| `uniqueValue` | boolean | 否 | 是否禁止重复（文本/数值类常用） |
| `defaultValue` | string | 否 | 默认值 |
| `defaultValueType` | string | 否 | `Normal` / `RecordCreator` / `RecordCreateTime` |

---

**字段类型枚举（`fields[].type`）**

| 类型值 | 说明 | 是否自动字段 |
|--------|------|------------|
| `MultiLineText` | 多行文本 | 否 |
| `Date` | 日期 | 否 |
| `Time` | 时间 | 否 |
| `Number` | 数值 | 否 |
| `Currency` | 货币 | 否 |
| `Percentage` | 百分比 | 否 |
| `ID` | 身份证 | 否 |
| `Phone` | 电话 | 否 |
| `Email` | 电子邮箱 | 否 |
| `Url` | 超链接 | 否 |
| `Checkbox` | 复选框 | 否 |
| `SingleSelect` | 单选项 | 否 |
| `MultipleSelect` | 多选项 | 否 |
| `Rating` | 等级 | 否 |
| `Complete` | 进度条 | 否 |
| `Contact` | 联系人 | 否 |
| `Attachment` | 附件 | 否 |
| `Link` | 关联 | 否 |
| `Note` | 富文本 | 否 |
| `Address` | 地址 | 否 |
| `Cascade` | 级联 | 否 |
| `AutoNumber` | 编号 | **是** |
| `CreatedBy` | 创建者 | **是** |
| `CreatedTime` | 创建时间 | **是** |
| `LastModifiedBy` | 最后修改者 | **是** |
| `LastModifiedTime` | 最后修改时间 | **是** |
| `Formula` | 公式 | **是** |
| `Lookup` | 引用 | **是** |
| `BarCode` | 条码字段 | **是** |
| `SearchLookup` | 查找引用 | **是** |
| `Button` | 按钮 | **是** |
| `OneWayLink` | 单向关联 | **是** |

---

**各字段类型的可用参数（创建字段配置）**

说明：以下参数都直接写在 `fields[]` 元素根级，不使用 `data`。

| 字段类型 | 可用参数（除 `name`、`type`、`syncField`、`width` 外） |
|---------|------|
| `MultiLineText` | `uniqueValue`、`defaultValue`、`defaultValueType` |
| `Date` | `numberFormat`、`defaultValue`、`defaultValueType` |
| `Time` | `numberFormat` |
| `Number` | `numberFormat`、`uniqueValue`、`defaultValue`、`defaultValueType` |
| `Currency` | `numberFormat` |
| `Percentage` | `numberFormat` |
| `ID` | `uniqueValue` |
| `Phone` | `uniqueValue` |
| `Email` | 无专属参数 |
| `Url` | `displayText` |
| `Checkbox` | 无专属参数 |
| `SingleSelect` | `allowAddItemWhenInputting`、`autoAddItem`、`items[]`（`value: string` 必填，`color: integer` 可选） |
| `MultipleSelect` | `allowAddItemWhenInputting`、`autoAddItem`、`items[]`（同 `SingleSelect`） |
| `Rating` | `max`（integer） |
| `Complete` | 无专属参数 |
| `Contact` | `multipleContacts`、`noticeNewContact`、`extendFieldInfo`（object） |
| `Attachment` | 无专属参数 |
| `Link` | `isAuto`、`multipleLinks`、`linkSheet`、`filter`（object） |
| `Note` | 无专属参数 |
| `Address` | `addressLevel`、`detailedAddress` |
| `Cascade` | `displayAllLevel`、`allCascadeOption`、`cascadeTitle` |
| `AutoNumber` | `numberFormat` |
| `CreatedBy` | `extendFieldInfo` |
| `CreatedTime` | `numberFormat` |
| `LastModifiedBy` | `watchedAll`、`watchedField` |
| `LastModifiedTime` | `watchedAll`、`watchedField`、`numberFormat` |
| `Formula` | `formula`、`numberFormat` |
| `Lookup` | `lookupType`、`lookupSheetId`、`linkField`、`lookupField`、`aggregation`、`filter` |
| `BarCode` | 无专属参数 |
| `SearchLookup` | 无专属参数（配置沿用 `Lookup` 相关能力） |
| `Button` | 无专属参数 |
| `OneWayLink` | `isAuto`、`multipleLinks`、`linkSheet`、`filter` |

---

**视图类型枚举（`views[].type`）**

请求传入小写，响应返回首字母大写（如请求 `grid` → 响应 `Grid`）。

| 请求值 | 说明 |
|--------|------|
| `grid` | 表格视图 |
| `kanban` | 看板视图 |
| `gallery` | 画册视图 |
| `form` | 表单视图 |
| `gantt` | 甘特视图 |
| `query` | 查询视图 |
| `calendar` | 日历视图 |

---

**各字段类型的记录值传入格式（写记录时参考）**

| 字段类型 | 值格式 | 示例 |
|---------|--------|------|
| `MultiLineText` | string | `"文本内容"` |
| `Date` | string（yyyy/mm/dd） | `"2025/11/15"` |
| `Time` | string（hh:mm:ss） | `"11:12:15"` |
| `Number` / `Currency` / `Percentage` | int \| float | `123` |
| `ID` / `Phone` / `Email` | string | `"18800000000"` |
| `Url` | object 或 string | `{"address":"https://…","displayText":"百度"}` 或 `"https://…"`（同时设置地址和文本） |
| `Checkbox` | boolean | `true` |
| `SingleSelect` | string（选项 value） | `"选项1"` |
| `MultipleSelect` | string[]（选项 value 数组） | `["选项1","选项2"]` |
| `Rating` / `Complete` | int | `3` / `80` |
| `Contact` | object[] | `[{"id":"uid","nickname":"张三","avatar_url":"https://…"}]` |
| `Attachment` | object[] | `[{"uploadId":"…","fileName":"a.png","size":1024,"source":"Cloud","type":"image/png"}]`；`linkUrl`、`imgSize` 选填 |
| `Link` | string[] | `["record_id_1","record_id_2"]` |
| `Address` | object | `{"districts":["广东省","珠海市","香洲区"],"detail":"详细地址"}` |
| `Cascade` | object | `{"districts":["一级","二级"]}` |
| `Note` | object | `{"fileId":"…","summary":"摘要","modifyDate":"2025/12/31 10:00:00"}` |
| `AutoNumber`、`CreatedBy`、`CreatedTime`、`LastModifiedBy`、`LastModifiedTime`、`Formula`、`Lookup` | — | **自动字段，无需填写** |


#### 返回值说明

```json
{
  "detail": {
    "sheet": {
      "id": 6,
      "name": "sheetName",
      "primaryFieldId": "L",
      "fields": [
        { "id": "L", "name": "field1", "type": "SingleLineText" },
        {
          "id": "M",
          "name": "field2",
          "type": "SingleSelect",
          "items": [
            { "id": "K", "value": "A" },
            { "id": "L", "value": "B" },
            { "id": "M", "value": "C" }
          ]
        }
      ],
      "views": [
        { "id": "J", "name": "view1", "type": "Grid" },
        { "id": "K", "name": "view2", "type": "Kanban" },
        { "id": "L", "name": "view3", "type": "Gallery" }
      ]
    }
  },
  "result": "ok"
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `detail.sheet.id` | integer | 新建数据表 ID |
| `detail.sheet.name` | string | 数据表名称 |
| `detail.sheet.primaryFieldId` | string | 主字段 ID |
| `detail.sheet.fields[].id` | string | 字段 ID |
| `detail.sheet.fields[].name` | string | 字段显示名称 |
| `detail.sheet.fields[].type` | string | 字段类型 |
| `detail.sheet.fields[].items` | array | 选项列表（SingleSelect / MultipleSelect），每项含 id、value |
| `detail.sheet.views[].id` | string | 视图 ID |
| `detail.sheet.views[].name` | string | 视图名称 |
| `detail.sheet.views[].type` | string | 视图类型 |
| `result` | string | ok 表示成功 |


---

## 3. dbsheet.update_sheet

#### 功能说明

修改数据表的名称或主字段设置。


#### 操作约束

- **前置检查**：get_schema 确认目标数据表存在

**幂等性**：是

#### 调用示例

重命名数据表：

```json
{
  "file_id": "string",
  "sheet_id": 6,
  "name": "新名称"
}
```


#### 参数说明

- `file_id` (string, 必填): 多维表格文件 ID
- `sheet_id` (integer, 必填): 目标数据表 ID
- `name` (string, 可选): 新名称
- `prefer_id` (boolean, 可选): 是否使用字段 ID 作为 key
- `primary_field` (string, 可选): 主字段名称

#### 返回值说明

```json
{
  "detail": {
    "sheet": {
      "id": 6,
      "name": "新名称",
      "primary_field_id": "L",
      "fields": [],
      "views": []
    }
  },
  "result": "ok"
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `detail.sheet.id` | integer | 数据表 ID |
| `detail.sheet.name` | string | 数据表名称 |
| `result` | string | ok 表示成功 |


---

## 4. dbsheet.delete_sheet

#### 功能说明

删除多维表格中的指定数据表。


#### 操作约束

- **前置检查**：get_schema 核对拟删数据表的名称和内容
- **用户确认**：删除数据表不可恢复，必须向用户确认数据表名称和 ID

**幂等性**：是

#### 调用示例

删除数据表：

```json
{
  "file_id": "string",
  "sheet_id": 6
}
```


#### 参数说明

- `file_id` (string, 必填): 多维表格文件 ID
- `sheet_id` (integer, 必填): 要删除的数据表 ID

#### 返回值说明

```json
{
  "detail": {
    "sheet": { "id": 6 }
  },
  "result": "ok"
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `detail.sheet.id` | integer | 已删除的数据表 ID |
| `result` | string | ok 表示成功 |


---

## 5. dbsheet.sheet_batch_create

#### 功能说明


**前置条件**：有创建数据表权限；单次批量条数与字段结构以文档上限为准。



#### 操作约束

- **后置验证**：建议 dbsheet.get_schema 核对

**幂等性**：否 — 重复调用会创建多个数据表，先确认是否已成功

#### 调用示例

批量建表：

```json
{
  "file_id": "string",
  "body": {
    "sheets": []
  }
}
```


#### 参数说明

- `file_id` (string, 必填): 多维表格文件 ID
- `body` (object, 必填): JSON 请求体，须含 sheets 数组，数组元素描述待建数据表

**body 根级必填**

| 字段 | 类型 | 说明 |
|------|------|------|
| `sheets` | array | 每个元素描述一个待建数据表（名称、字段、视图等），子字段以接口约定为准（batch-create-sheet） |


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
| `detail` | object | 创建结果 |


---

## 6. dbsheet.sheet_batch_delete

#### 功能说明


**前置条件**：确认目标 `sheet_ids` 内数据均可删除；不可逆。



#### 操作约束

- **前置检查**：get_schema 确认待删数据表名称和内容
- **用户确认**：删除后表及记录不可恢复

**幂等性**：否 — 不可恢复操作，禁止自动重试

#### 调用示例

批量删除：

```json
{
  "file_id": "string",
  "body": {
    "sheet_ids": [
      2,
      3
    ]
  }
}
```


#### 参数说明

- `file_id` (string, 必填): 多维表格文件 ID
- `body` (object, 必填): JSON 请求体，须含 sheet_ids 字段，数组元素为待删除数据表 ID

**body 根级必填**

| 字段 | 类型 | 说明 |
|------|------|------|
| `sheet_ids` | array[integer] | 待删除数据表 ID 列表 |


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
| `detail` | object | 接口返回详情 |


---

