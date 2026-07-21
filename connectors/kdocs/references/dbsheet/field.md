# 字段管理

## 1. dbsheet.create_fields

#### 功能说明

在指定数据表中批量创建字段。请求体为 JSON：`fields[]` 每项含 `name`、`type` 及类型特有属性（直接平铺在字段根级，**无 `data` 包装层**）；详见 param_detail 中各字段类型定义。创建成功后由服务端分配字段 `id`，**创建请求中禁止手填 `id`**。



#### 操作约束

- **禁止**：创建请求中禁止手填 `id`，`id` 仅由服务端分配
- **后置验证**：get_schema 确认字段已创建

**幂等性**：否 — 重复调用会创建重复字段，先确认是否已成功

> 字段专属属性（如 `items`、`numberFormat`、`max` 等）直接平铺在字段对象根级，**不存在 `data` 包装层**。
> 选项类字段（`SingleSelect`/`MultipleSelect`）的 `items` 直接写在字段根级；响应中 `items[].id` 由服务端分配，创建时只需传 `value`（和可选 `color`）。
> 身份证字段类型名为 `ID`；部分历史示例写作 `Id`，以平台校验为准。
> `prefer_id` 为 `true` 时，Lookup 的 `linkField`/`lookupField`、LastModifiedBy/LastModifiedTime 的 `watchedField` 须传字段 id 而非字段名。

#### 调用示例

创建多种类型字段：

```json
{
  "file_id": "string",
  "sheet_id": 3,
  "prefer_id": false,
  "fields": [
    {
      "name": "Field A",
      "type": "Checkbox",
      "width": 1080,
      "syncField": false
    },
    {
      "name": "Field B",
      "type": "SingleSelect",
      "allowAddItemWhenInputting": true,
      "items": [
        {
          "value": "待处理"
        },
        {
          "value": "进行中"
        },
        {
          "value": "已完成"
        }
      ],
      "syncField": false
    },
    {
      "name": "Field C",
      "type": "Rating",
      "max": 5,
      "syncField": false
    },
    {
      "name": "Field D",
      "type": "MultiLineText",
      "uniqueValue": false,
      "defaultValue": "Hello",
      "defaultValueType": "Normal",
      "syncField": false
    },
    {
      "name": "Field E",
      "type": "Number",
      "numberFormat": "0.00_ ",
      "syncField": false
    }
  ]
}
```


#### 参数说明

- `file_id` (string, 必填): 多维表格文件 ID（路径参数）
- `sheet_id` (integer, 必填): 数据表 ID
- `fields` (array, 必填): 待创建字段列表；每项为对象，须含 `name`、`type`，类型专属属性直接平铺在字段对象上（无 `data` 包装层），见 param_detail
  - `name` (string, 必填): 字段显示名称
  - `type` (string, 必填): 字段类型枚举（见 param_detail 完整列表）
  - `width` (integer, 可选): 字段宽度，单位缇（1/1440 英寸）
  - `syncField` (boolean, 可选): 默认 `false`，是否为同步字段
  - 类型专属属性直接平铺（如 `items`、`numberFormat`、`max` 等），**无 `data` 包装层**
  - **禁止**在创建请求中传入 `id`：`id` 仅创建成功后由服务端返回
- `prefer_id` (boolean, 可选): 默认 `false`（以字段**名称**解析关联）。为 `true` 时，**Lookup** 的 `linkField`/`lookupField`、**LastModifiedBy**/**LastModifiedTime** 的 `watchedField` 等须传**字段 id**

**请求详情**

| 项目 | 值 |
|------|-----|
| Method | `POST` |
| Content-Type | `application/json` |

**请求体根级**

| 名称 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `fields` | array[object] | 是 | 每项：`name`、`type`、类型专属属性（直接平铺，无 `data` 包装） |
| `preferId` | boolean | 否 | 默认 `false`。`true` 时 Lookup / 监控类字段中的引用须用字段 id |

**`fields[]` 通用属性**

| 属性 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | 是 | 字段显示名称 |
| `type` | string | 是 | 字段类型（下列各节枚举） |
| `width` | integer | 否 | 字段宽度，单位缇（1/1440 英寸） |
| `syncField` | boolean | 否 | 是否为同步字段，默认 `false` |
| `uniqueValue` | boolean | 否 | 是否禁止录入重复值（文本/数值类通用） |
| `defaultValue` | string | 否 | 默认值 |
| `defaultValueType` | string | 否 | `Normal` 文本默认值；`RecordCreator` 记录创建者；`RecordCreateTime` 记录创建时间 |
| `id` | string | 禁止 | 仅创建后由服务端返回，不可在 CreateField 中手填 |

以下为各 `type` 的专属属性及录入值说明（字段属性直接平铺在字段对象根级，无 `data` 包装层）。

---

**1. `MultiLineText` 多行文本**

无专属创建属性（通用属性 `uniqueValue`、`defaultValue`、`defaultValueType` 适用）。

录入值：`string`。

---

**2. `Date` 日期**

| 属性 | 类型 | 说明 |
|------|------|------|
| `numberFormat` | string | 日期显示格式（如 `yyyy/mm/dd`） |
| `defaultValueType` | string | `RecordCreateTime` 或 `Normal` |
| `defaultValue` | string | `defaultValueType=Normal` 时必填 |

录入值：`yyyy/mm/dd`。

---

**3. `Time` 时间**

| 属性 | 类型 | 说明 |
|------|------|------|
| `numberFormat` | string | 时间格式，如 `hh:mm:ss` |

录入值：`hh:mm:ss`。

---

**4. `Number` 数值**

| 属性 | 类型 | 说明 |
|------|------|------|
| `numberFormat` | string | 数值格式 |

录入值：`number`。

---

**5. `Currency` 货币**

| 属性 | 类型 | 说明 |
|------|------|------|
| `numberFormat` | string | 货币格式 |

录入值：`number`。

---

**6. `Percentage` 百分比**

| 属性 | 类型 | 说明 |
|------|------|------|
| `numberFormat` | string | 百分比格式，如 `0.00%` |

录入值：`number`。

---

**7. `ID` 身份证**

无专属创建属性（`uniqueValue` 适用）。

录入值：`string`。

---

**8. `Phone` 电话**

无专属创建属性（`uniqueValue` 适用）。

录入值：`string`。

---

**9. `Email` 电子邮箱**

无专属创建属性。

录入值：`string`。

---

**10. `Url` 超链接**

| 属性 | 类型 | 说明 |
|------|------|------|
| `displayText` | string | 按钮模式显示文本 |

录入值：`{ "address": "...", "displayText": "..." }` 或直接传字符串。

---

**11. `Checkbox` 复选框**

无专属创建属性。录入值：`boolean`。

---

**12. `SingleSelect` 单选项**

| 属性 | 类型 | 说明 |
|------|------|------|
| `allowAddItemWhenInputting` | boolean | 允许填写时新增选项 |
| `autoAddItem` | boolean | 不存在的值自动加入选项（谨慎使用） |
| `items` | array | 选项：`value`（必填）、`color`（可选 ARGB int） |

录入值：`string`。

---

**13. `MultipleSelect` 多选项**

同 `SingleSelect`。录入值：`string[]`。

---

**14. `Rating` 等级**

| 属性 | 类型 | 说明 |
|------|------|------|
| `max` | integer | 等级上限 |

录入值：`int`。

---

**15. `Complete` 进度条**

无专属创建属性。录入值：`int`（0 ~ 100）。

---

**16. `Contact` 联系人**

| 属性 | 类型 | 说明 |
|------|------|------|
| `multipleContacts` | boolean | 是否支持多联系人 |
| `noticeNewContact` | boolean | 是否通知联系人 |
| `extendFieldInfo` | object | 展示扩展信息（department/leader/email/employeeId） |

录入值：`[{ id, nickname, avatar_url }]`。

---

**17. `Attachment` 附件**

无专属创建属性。

录入值：`[{ uploadId, fileName, size, source, type, linkUrl, imgSize }]`。

---

**18. `Link` 关联**

| 属性 | 类型 | 说明 |
|------|------|------|
| `isAuto` | boolean | 是否自动关联 |
| `multipleLinks` | boolean | 是否支持关联多项 |
| `linkSheet` | integer | 关联数据表 id |
| `filter` | object | 自动关联条件 |

录入值：`["record_id_1", "record_id_2"]`。

---

**19. `Note` 富文本**

无专属创建属性。

录入值：`{ "fileId": "...", "summary": "...", "modifyDate": "yyyy/mm/dd hh:mm:ss" }`。

---

**20. `Address` 地址**

| 属性 | 类型 | 说明 |
|------|------|------|
| `addressLevel` | integer | 地址层级 |
| `detailedAddress` | boolean | 是否启用详细地址 |

录入值：`{ "districts": [...], "detail": "..." }`。

---

**21. `Cascade` 级联**

| 属性 | 类型 | 说明 |
|------|------|------|
| `displayAllLevel` | boolean | 是否显示所有级联层级 |
| `allCascadeOption` | array | 级联树配置 |
| `cascadeTitle` | string[] | 各级联项标题 |

录入值：`{ "districts": [...] }`。

---

**22. `AutoNumber` 编号**

| 属性 | 类型 | 说明 |
|------|------|------|
| `numberFormat` | string | 显示位数格式 |

自动字段，无需填写记录内容。

---

**23. `CreatedBy` 创建者**

| 属性 | 类型 | 说明 |
|------|------|------|
| `extendFieldInfo` | object | 展示扩展信息（department/leader/email/employeeId） |

自动字段，无需填写记录内容。

---

**24. `CreatedTime` 创建时间**

| 属性 | 类型 | 说明 |
|------|------|------|
| `numberFormat` | string | 时间显示格式 |

自动字段，无需填写记录内容。

---

**25. `LastModifiedBy` 最后修改者**

| 属性 | 类型 | 说明 |
|------|------|------|
| `watchedAll` | boolean | 是否监控所有字段 |
| `watchedField` | string[] | watchedAll 为 false 时必填 |

自动字段，无需填写记录内容。

---

**26. `LastModifiedTime` 最后修改时间**

| 属性 | 类型 | 说明 |
|------|------|------|
| `watchedAll` | boolean | 是否监控所有字段 |
| `watchedField` | string[] | watchedAll 为 false 时必填 |
| `numberFormat` | string | 时间显示格式 |

自动字段，无需填写记录内容。

---

**27. `Formula` 公式**

| 属性 | 类型 | 说明 |
|------|------|------|
| `formula` | string | 必须以 `=` 开头，如 `=[数值]+3` |
| `numberFormat` | string | 结果显示格式 |

自动字段，无需填写记录内容。

---

**28. `Lookup` 引用**

| 属性 | 类型 | 说明 |
|------|------|------|
| `lookupType` | integer | 1 引用字段、2 统计字段、3 查找字段 |
| `lookupSheetId` | integer | 引用数据表 id |
| `linkField` | string | 对应关联字段 id |
| `lookupField` | string | 引用字段 id |
| `aggregation` | string | 聚合函数 |
| `filter` | object | 统计/查找条件 |

自动字段，无需填写记录内容。

---

**29. `BarCode` 条码字段**

无专属创建属性。录入值：`string`。

---

**30. `SearchLookup` 查找引用**

无专属创建属性（配置沿用 Lookup 相关能力）。

---

**31. `Button` 按钮**

无专属创建属性（按钮行为由前端配置）。

---

**32. `OneWayLink` 单向关联**

同 `Link`（`isAuto`、`multipleLinks`、`linkSheet`、`filter`），但不创建反向关联字段。

录入值：关联记录 id 数组。

---

**请求体节选示例**

```json
{
  "fields": [
    {
      "name": "单选项",
      "type": "SingleSelect",
      "allowAddItemWhenInputting": true,
      "items": [{ "value": "选项1" }, { "value": "选项2" }]
    },
    {
      "name": "关联",
      "type": "Link",
      "isAuto": true,
      "multipleLinks": true,
      "linkSheet": 12
    }
  ],
  "preferId": false
}
```


#### 返回值说明

```json
{
  "detail": {
    "fields": [
      {
        "id": "K",
        "name": "状态",
        "type": "SingleSelect",
        "items": [
          { "id": "E", "value": "待处理" },
          { "id": "F", "value": "进行中" },
          { "id": "G", "value": "已完成" }
        ]
      },
      { "id": "L", "name": "截止日期", "type": "Date" }
    ]
  },
  "result": "ok"
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `detail.fields[].id` | string | 新建字段 ID |
| `detail.fields[].name` | string | 字段名称 |
| `detail.fields[].type` | string | 字段类型 |
| `detail.fields[].items` | array | 选项列表（选项类字段） |
| `result` | string | ok 表示成功 |


---

## 2. dbsheet.update_fields

#### 功能说明

批量更新数据表中已有字段的名称、选项等属性。请求体中 `fields[]` 每项必须包含 `id`，类型专属属性直接平铺在字段对象根级（无 `data` 包装层）。


#### 操作约束

- **前置检查**：get_schema 确认目标字段存在及当前属性

**幂等性**：是

> 更新字段时，`id` 为必填项（与创建字段相反，创建时禁止传入 `id`）；可通过 get_schema 获取字段 id。
> 选项类字段（SingleSelect / MultipleSelect）更新 `items` 时，含 `id` 的项为更新，不含 `id` 的项为新增，未出现的 `id` 对应选项会被删除。
> 字段专属属性（如 `items`、`numberFormat`、`max` 等）直接平铺在字段对象根级，**不存在 `data` 包装层**。

#### 调用示例

更新日期字段格式：

```json
{
  "file_id": "abc123",
  "sheet_id": 1,
  "fields": [
    {
      "id": "q",
      "name": "日期",
      "type": "Date",
      "numberFormat": "yyyy\"年\"m\"月\"d\"日\";@",
      "defaultValueType": "Normal",
      "defaultValue": "2024/11/23"
    }
  ],
  "prefer_id": true
}
```


#### 参数说明

- `file_id` (string, 必填): 多维表格文件 ID（路径参数）
- `sheet_id` (integer, 必填): 目标数据表 ID
- `fields` (array, 必填): 待更新字段列表；每项为对象，必须含 `id`，其余可更新属性与创建字段一致（见 param_detail）
  - `id` (string, **必填**): 目标字段 ID（通过 get_schema 获取）
  - `name` (string, 可选): 更新后的字段显示名称
  - `type` (string, 可选): 字段类型，更新时一般与原类型一致
  - `width` (integer, 可选): 字段宽度，单位缇（1/1440 英寸）
  - `syncField` (boolean, 可选): 默认 `false`，是否为同步字段
  - 类型专属属性直接平铺（如 `items`、`numberFormat`、`max` 等），**无 `data` 包装层**
- `prefer_id` (boolean, 可选): 默认 `false`（以字段**名称**解析关联）。为 `true` 时，**Lookup** 的 `linkField`/`lookupField`、**LastModifiedBy**/**LastModifiedTime** 的 `watchedField` 等须传**字段 id**

**请求详情**

| 项目 | 值 |
|------|-----|
| Method | `POST` |
| Content-Type | `application/json` |

**请求体根级**

| 名称 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `fields` | array[object] | 是 | 每项：`id`（必填）、`name`、`type`、类型专属属性（直接平铺，无 `data` 包装） |
| `prefer_id` | boolean | 否 | 默认 `false`。`true` 时 Lookup / 监控类字段中的引用须用字段 id |

**`fields[]` 通用属性（更新）**

| 属性 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | string | **是** | 目标字段 ID，通过 get_schema 获取 |
| `name` | string | 否 | 字段显示名称 |
| `type` | string | 否 | 字段类型，通常与原类型一致 |
| `width` | integer | 否 | 字段宽度，单位缇（1/1440 英寸） |
| `syncField` | boolean | 否 | 是否为同步字段，默认 `false` |
| `uniqueValue` | boolean | 否 | 是否禁止录入重复值（文本/数值类通用） |
| `defaultValue` | string | 否 | 默认值 |
| `defaultValueType` | string | 否 | `Normal` 文本默认值；`RecordCreator` 记录创建者；`RecordCreateTime` 记录创建时间 |

以下为各 `type` 的专属属性说明。字段属性直接平铺在字段对象根级，无 `data` 包装层。

---

**1. `MultiLineText` 多行文本**

无专属更新属性（通用属性 `uniqueValue`、`defaultValue`、`defaultValueType` 适用）。

---

**2. `Date` 日期**

| 属性 | 类型 | 说明 |
|------|------|------|
| `numberFormat` | string | 日期显示格式（Excel 风格） |
| `defaultValueType` | string | `RecordCreateTime` 或 `Normal` |
| `defaultValue` | string | `defaultValueType=Normal` 时必填 |

---

**3. `Time` 时间**

| 属性 | 类型 | 说明 |
|------|------|------|
| `numberFormat` | string | 时间格式，如 `hh:mm:ss` |

---

**4. `Number` 数值**

| 属性 | 类型 | 说明 |
|------|------|------|
| `numberFormat` | string | 数值显示格式 |

---

**5. `Currency` 货币**

| 属性 | 类型 | 说明 |
|------|------|------|
| `numberFormat` | string | 货币格式 |

---

**6. `Percentage` 百分比**

| 属性 | 类型 | 说明 |
|------|------|------|
| `numberFormat` | string | 百分比格式，如 `0.00%` |

---

**7. `ID` 身份证**

无专属更新属性（`uniqueValue` 适用）。

---

**8. `Phone` 电话**

无专属更新属性（`uniqueValue` 适用）。

---

**9. `Email` 电子邮箱**

无专属更新属性。

---

**10. `Url` 超链接**

| 属性 | 类型 | 说明 |
|------|------|------|
| `displayText` | string | 按钮模式显示文本，不填则普通链接模式 |

---

**11. `Checkbox` 复选框**

无专属更新属性。

---

**12. `SingleSelect` 单选项**

| 属性 | 类型 | 说明 |
|------|------|------|
| `allowAddItemWhenInputting` | boolean | 是否允许填写时添加选项 |
| `autoAddItem` | boolean | 选填；不存在值自动加入选项列表（谨慎使用） |
| `items` | array | 选项列表；含 `id` 的项为更新已有选项，不含 `id` 的项为新增，未出现的 `id` 对应选项会被删除；每项含 `value`（必填）、`color`（可选，ARGB int） |

---

**13. `MultipleSelect` 多选项**

同 `SingleSelect` 的 `allowAddItemWhenInputting`、`autoAddItem`、`items`。

---

**14. `Rating` 等级**

| 属性 | 类型 | 说明 |
|------|------|------|
| `max` | integer | 等级上限 |

---

**15. `Complete` 进度条**

无专属更新属性。

---

**16. `Contact` 联系人**

| 属性 | 类型 | 说明 |
|------|------|------|
| `multipleContacts` | boolean | 是否支持多联系人 |
| `noticeNewContact` | boolean | 是否通知联系人 |
| `extendFieldInfo` | object | 选填；`multipleContacts` 为 `false` 时可配置扩展信息，支持 `department`（部门）、`leader`（直属领导）、`email`（邮箱）、`employeeId`（工号），每项格式 `{"name": "显示名"}` |

---

**17. `Attachment` 附件**

| 属性 | 类型 | 说明 |
|------|------|------|
| `only_upload_by_camera` | boolean | 是否仅允许拍照上传 |

---

**18. `Link` 关联**

| 属性 | 类型 | 说明 |
|------|------|------|
| `isAuto` | boolean | 是否为自动关联 |
| `multipleLinks` | boolean | 是否支持关联多项 |
| `linkSheet` | integer | 关联数据表 id |
| `filter` | object | 仅自动关联需要；`{ "mode": "And", "conditions": [{ "curSheetFieldId": "B", "linkSheetFieldId": "B" }] }` |

---

**19. `Note` 富文本**

无专属更新属性。

---

**20. `Address` 地址**

| 属性 | 类型 | 说明 |
|------|------|------|
| `addressLevel` | int | 地址层级：1 省 … 5 省/市/区/街道/社区 |
| `detailedAddress` | boolean | 是否启用详细地址 |

---

**21. `Cascade` 级联**

| 属性 | 类型 | 说明 |
|------|------|------|
| `displayAllLevel` | boolean | 是否显示所有级联层级 |
| `allCascadeOption` | array | 级联选项树；每项含 `value`（string）、`children`（同结构数组） |
| `cascadeTitle` | string[] | 各级联项标题，如 `["省", "市"]` |

---

**22. `AutoNumber` 编号**

| 属性 | 类型 | 说明 |
|------|------|------|
| `numberFormat` | string | 如 `000000` 控制显示位数 |

---

**23. `CreatedBy` 创建者**

| 属性 | 类型 | 说明 |
|------|------|------|
| `extendFieldInfo` | object | 选填；可配置创建者扩展信息，支持 `department`（部门）、`leader`（直属领导）、`email`（邮箱）、`employeeId`（工号），每项格式 `{"name": "显示名"}` |

---

**24. `CreatedTime` 创建时间**

| 属性 | 类型 | 说明 |
|------|------|------|
| `numberFormat` | string | 如 `yyyy-mm-dd hh:mm;@` |

---

**25. `LastModifiedBy` 最后修改者**

| 属性 | 类型 | 说明 |
|------|------|------|
| `watchedAll` | boolean | 是否监控所有字段，默认 `true` |
| `watchedField` | string[] | `watchedAll=false` 时**必填**：被监控字段 id 数组 |

---

**26. `LastModifiedTime` 最后修改时间**

| 属性 | 类型 | 说明 |
|------|------|------|
| `watchedAll` | boolean | 默认 `true` |
| `watchedField` | string[] | `watchedAll=false` 时必填，字段 id 数组 |
| `numberFormat` | string | 显示格式 |

---

**27. `Formula` 公式**

| 属性 | 类型 | 说明 |
|------|------|------|
| `formula` | string | 公式串，必须以 `=` 开头，如 `"=[数值]+3"`（列名用 `[]` 包裹） |

---

**28. `Lookup` 引用**

| 属性 | 类型 | 说明 |
|------|------|------|
| `lookupType` | integer | `1` 引用字段；`2` 统计字段；`3` 查找字段。类型为 `1` 时无需传 `lookupSheetId` 和 `filter` |
| `lookupSheetId` | integer | 引用的表 id；与 `linkField` 互斥 |
| `linkField` | string | 对应的关联字段 id |
| `lookupField` | string | 被引用表中的字段 id |
| `aggregation` | string | 聚合函数：`ToString`、`Origin`、`Sum`、`Counta`、`Average`、`Max`、`Min`、`Unique`、`CountaUnique` 等 |
| `filter` | object | 仅统计 / 查找类型可用；结构同 `Link` 的 `filter` |

---

**29. `BarCode` 条码字段**

无专属更新属性。

---

**30. `SearchLookup` 查找引用**

无专属更新属性（配置沿用 Lookup 相关能力）。

---

**31. `Button` 按钮**

无专属更新属性（按钮行为由前端配置）。

---

**32. `OneWayLink` 单向关联**

同 `Link`（`isAuto`、`multipleLinks`、`linkSheet`、`filter`），但不创建反向关联字段。

---

**请求体节选示例**

```json
{
  "fields": [
    { "id": "q", "name": "日期", "type": "Date", "numberFormat": "yyyy\"年\"m\"月\"d\"日\";@", "defaultValueType": "Normal", "defaultValue": "2024/11/23" },
    { "id": "E", "name": "优先级", "type": "SingleSelect", "allowAddItemWhenInputting": true, "items": [{ "id": "B", "value": "低" }, { "id": "H", "value": "中" }, { "value": "紧急" }] }
  ],
  "prefer_id": true
}
```


#### 返回值说明

```json
{
  "code": 0,
  "msg": "",
  "data": {
    "fields": [
      {
        "name": "日期",
        "type": "Date",
        "id": "q",
        "defaultValue": "2024/11/23",
        "defaultValueType": "Normal",
        "numberFormat": "yyyy\"年\"m\"月\"d\"日\";@"
      }
    ]
  }
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | integer | 响应代码，非 0 表示失败 |
| `msg` | string | 响应信息 |
| `data.fields` | array | 更新后的字段列表，详见多维表格参数说明 |
| `more` | object | 更多的错误信息 |


---

## 3. dbsheet.delete_fields

#### 功能说明

批量删除数据表中的指定字段。


#### 操作约束

- **前置检查**：get_schema 核对拟删字段的名称和类型
- **用户确认**：删除字段不可恢复，字段数据将永久丢失，必须向用户确认字段列表

**幂等性**：是

#### 调用示例

删除多个字段：

```json
{
  "file_id": "string",
  "sheet_id": 3,
  "fields": [
    {
      "id": "C"
    },
    {
      "id": "D"
    }
  ]
}
```


#### 参数说明

- `file_id` (string, 必填): 多维表格文件 ID
- `sheet_id` (integer, 必填): 目标数据表 ID
- `fields` (array, 必填): 要删除的字段列表，每项包含 `id`

#### 返回值说明

```json
{
  "detail": {
    "fields": [
      { "id": "C", "deleted": true },
      { "id": "D", "deleted": true }
    ]
  },
  "result": "ok"
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `detail.fields` | array | 删除结果列表，每项包含 `id` 和 `deleted` |
| `result` | string | ok 表示成功 |


---

