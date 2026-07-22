# 金数据 MCP 工具完整参考

本文档列出当前对外开放的 **26 个 MCP 工具**，每个工具包含一句话用途、输入参数、输出字段、所需 OAuth scope 和常见错误。

> 工具的实际暴露名可能带客户端前缀（如 `mcp__jinshuju__list_forms`），按客户端实际名字调用即可，本文统一用裸名。

## 索引

| 类别 | 工具 |
| ---- | ---- |
| **Forms** | [`list_forms`](#list_forms) · [`list_my_submitted_forms`](#list_my_submitted_forms) · [`list_folders`](#list_folders) · [`get_form`](#get_form) · [`check_field_data`](#check_field_data) · [`create_form`](#create_form) · [`copy_form`](#copy_form) · [`move_form`](#move_form) · [`edit_form`](#edit_form) · [`edit_theme`](#edit_theme) |
| **考试 / 测评** | [`create_exam_form`](#create_exam_form) · [`edit_exam_form`](#edit_exam_form) · [`create_evaluation_form`](#create_evaluation_form) · [`edit_evaluation_form`](#edit_evaluation_form) |
| **上传** | [`prepare_form_image_upload`](#prepare_form_image_upload) · [`prepare_entry_attachment_upload`](#prepare_entry_attachment_upload) |
| **Entries** | [`list_entries`](#list_entries) · [`list_my_submitted_entries`](#list_my_submitted_entries) · [`get_entry`](#get_entry) · [`create_entry`](#create_entry) · [`create_entries`](#create_entries) · [`update_entry`](#update_entry) · [`delete_entry`](#delete_entry) |
| **Account** | [`get_current_user`](#get_current_user) · [`get_current_billing_account`](#get_current_billing_account) · [`list_account_users`](#list_account_users) |

## OAuth Scope 速查

| Scope | 涵盖工具 |
| ----- | -------- |
| `forms` | list_forms / list_my_submitted_forms / list_folders / get_form / check_field_data / create_form / copy_form / move_form / edit_form / create_exam_form / edit_exam_form / create_evaluation_form / edit_evaluation_form / prepare_form_image_upload（type=field_choice） |
| `form_setting` | edit_theme / prepare_form_image_upload（type=header） |
| `read_entries` | list_entries / list_my_submitted_entries / get_entry |
| `write_entries` | create_entry / create_entries / update_entry / delete_entry / prepare_entry_attachment_upload |
| `user` | get_current_user |
| `billing_account` | get_current_billing_account / list_account_users |

> Basic Auth / JWT 模式下不受 scope 限制；OAuth 模式下被授权的 scope 决定可调用工具集合，未授权 scope 调用会报 `Insufficient scope: <name> required`。

---

# Forms

## list_forms

**用途**：列出当前凭证名下能访问的表单（自己创建的 + 被分享协作的）。

**Scope**：`forms`

**输入**

| 参数 | 类型 | 必填 | 说明 |
| ---- | ---- | ---- | ---- |
| `name` | string | 否 | 表单名关键字（**正则匹配，大小写不敏感**），如 `"survey"` 能匹配 `Survey A` |
| `next` | string | 否 | 翻页游标（上一次响应里的 `next` 字段） |
| `limit` | integer | 否 | 默认 50；越界自动截断 |

**输出**

```json
{
  "total": 3,
  "count": 3,
  "data": [
    {
      "name": "2026 春季发布会报名表",
      "description": "活动报名收集",
      "token": "abCdEf",
      "scene": "registration",
      "form_url": "https://jinshuju.net/f/abCdEf",
      "created_at": "2026-04-20T10:00:00+08:00",
      "entries_count": 128
    }
  ],
  "next": null
}
```

**常见错误**

- `Insufficient scope: forms required` — OAuth 未授权 `forms` scope

---

## list_my_submitted_forms

**用途**：列出当前用户作为**填写者**提交过数据的表单（不一定是所有者），按最近提交时间倒序。用户模糊说"我填过的那张表单"时用这个。

**Scope**：`forms`

**输入**

| 参数 | 类型 | 必填 | 说明 |
| ---- | ---- | ---- | ---- |
| `next` | integer | 否 | 翻页偏移量（上次响应里的 `next`） |
| `limit` | integer | 否 | 默认 50，最大 50 |

**输出**

```json
{
  "total": 3,
  "count": 3,
  "data": [
    {
      "name": "2026 客户满意度调查",
      "description": "季度回访",
      "token": "abCdEf",
      "form_url": "https://jinshuju.net/f/abCdEf",
      "scene": "survey",
      "submitted_entries_count": 2,
      "last_submitted_at": "2026-06-20T10:00:00+08:00"
    }
  ],
  "next": null
}
```

> 排除快捷支付（quickpay）表单。别人拥有、你只是填写者的表单也会出现在这里。

**常见错误**

- `Insufficient scope: forms required`

---

## list_folders

**用途**：列出当前用户能管理的文件夹，**只为给 create_form / copy_form / move_form 拿 folder_token 用**。

**Scope**：`forms`

**输入**

| 参数 | 类型 | 必填 | 说明 |
| ---- | ---- | ---- | ---- |
| `limit` | integer | 否 | 默认 50，最大 100，越界自动截断 |

**输出**

```json
{
  "total": 4,
  "returned": 4,
  "data": [
    { "token": "FLD_a1b2", "name": "市场活动" },
    { "token": "FLD_c3d4", "name": "客户登记" }
  ]
}
```

> 别人的文件夹不会出现在结果里。返回字段没有 `id`，**只用 token**。

**常见错误**

- `Insufficient scope: forms required`

---

## get_form

**用途**：拿表单完整结构（字段 / 主题 / setting）。**调任何 entry 类工具前必先 get_form** 拿 `api_code`。

**Scope**：`forms`

**输入**

| 参数 | 类型 | 必填 | 说明 |
| ---- | ---- | ---- | ---- |
| `token` | string | ✅ | 表单 token **或** form id（数字 ID 也接受） |
| `include_theme` | bool | 否 | 是否返回 `theme`（页头 / 配色 / 字体等样式）。默认 `false` |
| `include_setting` | bool | 否 | 是否返回 `setting`（提交行为 / 关闭规则 / 通知规则 / 考试测评设置 / 字段显示规则）。默认 `false` |
| `include_field_rules` | bool | 否 | 是否返回字段显示规则 `field_rules`。默认 `false` |

**输出**

```json
{
  "name": "2026 春季发布会报名表",
  "token": "abCdEf",
  "description": "活动报名",
  "form_url": "https://jinshuju.net/f/abCdEf",
  "fields": [
    {
      "api_code": "field_1",
      "label": "姓名",
      "type": "NameField",
      "required": true,
      "private": false
    },
    {
      "api_code": "field_2",
      "label": "参会城市",
      "type": "DropDown",
      "required": true,
      "private": false,
      "choices": [
        { "value": "北京", "api_code": "city_bj" },
        { "value": "上海", "api_code": "city_sh" }
      ]
    },
    {
      "api_code": "field_3",
      "label": "评分",
      "type": "RatingField",
      "rating_max": 5
    },
    {
      "api_code": "field_4",
      "label": "费用明细",
      "type": "TableField",
      "init_row_length": 3,
      "dimensions": [
        { "api_code": "col_1", "label": "项目", "type": "TextField" },
        { "api_code": "col_2", "label": "金额", "type": "NumberField" }
      ]
    }
  ],
  "theme": {
    "primary_color": "#3B82F6",
    "header": { "type": "image", "has_header_image": true }
  },
  "setting": {
    "entry_submit_mode": "show_message",
    "success_message": "感谢报名！",
    "success_message_style": "text",
    "open_entry_action": "view",
    "show_serial_number_on_success": true,
    "manually_close_rule": null,
    "by_time_range_close_rule": { "start_time": "2026-05-01T09:00+08:00", "end_time": "2026-05-31T18:00+08:00" },
    "by_entries_close_rule": { "limit": 500 },
    "fill_frequency": { "fill_type": "repeatable", "condition": "by_ip", "cycle_period": "every_day", "limited_time": 3 },
    "password_required": false,
    "allowed_audience": "public",
    "notification_rules": [
      { "id": "...", "approach": "WXWORK", "url": "https://qyapi.weixin.qq.com/...", "content": "新报名：$(field_1)", "trigger_scope": "all_new", "enabled": true, "from_next": true }
    ]
  }
}
```

> ⚠️ **默认只返回核心信息**（`name` / `token` / `form_url` / `description` / `fields`）。`theme` / `setting` / `field_rules` 三块体积大，默认**不返回**，需分别传 `include_theme` / `include_setting` / `include_field_rules=true` 才带上。只为拿字段结构（`api_code`）时保持默认即可。
>
> 字段特有属性（如 `goods_items` / `reservation_items` / `associated_form_token` / `predefined_value` / `placeholder` / `range_min/max` / `precision` / `media_type` / `max_size` 等）按字段类型出现在对应 field 节点上。选项字段的 `choices[]` 中，「其他」选项（扩展输入）会带 `"is_other": true`，普通选项不带该键；预约字段 `daily_time_range_quotas` 的时刻以零填充字符串返回（`"09"` 而非 `9`）。
>
> 另外：传 `include_field_rules=true` 时返回顶层 `field_rules`（字段显示规则，结构见 [edit_form](#edit_form)）；`include_setting=true` 时考试 / 测评表单还会返回 `setting.exam_setting` / `setting.evaluation_setting`（结构与 [`create_exam_form`](#create_exam_form) / [`create_evaluation_form`](#create_evaluation_form) 的同名入参对齐，题目字段带 `customized_type` 和按选项 value 序列化的 `answers`）——重写 answers / indicators 这类整体替换列表前，先用 get_form 读出现状。

**常见错误**

- `Form cannot be found` — token 错 / 表单不属于当前账号 / 没被分享
- `Insufficient scope: forms required`

---

## create_form

**用途**：从零创建一张表单。一次性指定 name + 字段列表 + 可选 setting + 可选 folder。

> ⚠️ 考试 / 测评场景不要用本工具：`scene` 枚举已移除 `exam` / `evaluation`，请改用 [`create_exam_form`](#create_exam_form) / [`create_evaluation_form`](#create_evaluation_form)（题目答案、计分只在专用工具里可用）。

**Scope**：`forms`

**输入**

| 参数 | 类型 | 必填 | 说明 |
| ---- | ---- | ---- | ---- |
| `name` | string | ✅ | 表单名 |
| `fields` | array  | ✅ | 字段列表，每项见下表 |
| `description` | string | 否 | 表单说明 |
| `scene` | enum | 否 | 表单场景：`form`（默认）/ `survey` / `registry` / `vote` / `reservation` / `customer_acquisition` / `online_payment` |
| `setting` | object | 否 | 初次创建的关键 setting（仅 `success_message` / `open_entry_action` / `open_entry_message` / `notification_rules`）。完整 setting 用 `edit_form` 配 |
| `folder_token` | string | 否 | 表单要放进的文件夹 token |

**fields[] 通用属性**

| 字段 | 类型 | 说明 |
| ---- | ---- | ---- |
| `type` | string | 字段类型，必须是 [39 种白名单](#字段类型白名单) 之一 |
| `label` | string | 字段标签 |
| `cid` | string | 客户端引用 id：每个新字段生成一个表单内唯一的短随机 token（6-8 位字母数字，**不能含 `.`**）。`api_code` 由后端生成、**不可自行指定**；同请求内 FormulaField 公式、测评维度等需要引用新字段时用 cid |
| `required` | bool | 是否必填，与 `private` 互斥 |
| `private` | bool | 是否隐藏，设 true 时 `required` 自动置 false |
| `unique` | bool | 不允许重复值。仅 `TextField` / `NameField` / `EmailField` / `MobileField` / `TelephoneField` / `IdCardField` / `LinkField` / `FormAssociation` 支持 |
| `notes` | string | 字段提示文案（SectionBreak 时是描述正文） |
| `choices` | array | 选项字段用：`[{ value, quota?, selected?, operand_value?, image_url?, image_upload_token?, sub_choices? }]`。`selected: true` 设**默认选中**——RadioButton / DropDown / ImageRadioButton 仅一项生效，CheckBox / ImageCheckBox 可多项，CascadeDropDown 沿选中路径每级节点都设 `selected: true`。`operand_value`（选项赋值）配合字段 `calculable=true` 给每个选项赋数值，供 FormulaField 计算——开启 calculable 后**每个选项都必须给** `operand_value`；`image_upload_token` 见 [prepare_form_image_upload](#prepare_form_image_upload) |
| `statements` | array | 矩阵类用：`[{ label }]` |
| `dimensions` | array | TableField / MatrixField 用 |
| `rating_max` | int | RatingField / MatrixScaleField 用，3/5/10 |
| `predefined_value` | string / object | 默认值，类型见对应字段说明。**选择类字段（单选 / 多选 / 下拉 / 级联）不接受**，默认选中改用 `choices[].selected` |
| `other_choice_required` | bool | 选了「其他」选项后必须填写其扩展文本框（"其他选项必填"校验）。默认 false。仅 `RadioButton` / `CheckBox` / `DropDown` 且含「其他」选项时生效，其余类型忽略 |
| `placeholder` | string | 占位文本 |
| `range_min` / `range_max` | number | NumberField 取值范围 |
| `precision` | int / string | NumberField (0-14) 或 DateTimeField (`year`/`month`/`day`/`hour`/`minute`/`second`) |

> 不同字段类型还有专属属性（`max_size` / `media_type` / `goods_items` / `reservation_items` / `formula_display` / `associated_form_token` 等），全部见 [字段类型清单](#字段类型白名单)。

**setting 子参数**（创建阶段只接受这几个，更多设置走 edit_form）

| 字段 | 类型 | 说明 |
| ---- | ---- | ---- |
| `success_message` | string | 提交成功提示文案 |
| `open_entry_action` | enum | `hide` / `view` / `edit`，默认 `view` |
| `open_entry_message` | string | 已填过表单的提示文案（默认 `你已填写过该表单`） |
| `notification_rules` | array | 通知规则数组，见 [edit_form](#edit_form) 同名参数 |

**输出**

```json
{
  "name": "2026 春季发布会报名表",
  "token": "abCdEf",
  "description": "活动报名",
  "form_url": "https://jinshuju.net/f/abCdEf",
  "fields_count": 7,
  "created_at": "2026-05-17T10:00:00+08:00"
}
```

**调用示例（活动报名表）**

```json
{
  "name": "2026 春季发布会报名表",
  "description": "公司春季发布活动登记",
  "fields": [
    { "type": "NameField", "label": "姓名", "required": true },
    { "type": "MobileField", "label": "手机号", "required": true, "sms_verification": true },
    { "type": "TextField", "label": "公司" },
    { "type": "TextField", "label": "职位" },
    {
      "type": "DropDown", "label": "参会城市", "required": true,
      "choices": [{ "value": "北京" }, { "value": "上海" }, { "value": "深圳" }, { "value": "线上" }]
    },
    {
      "type": "CheckBox", "label": "感兴趣议题",
      "choices": [{ "value": "产品发布" }, { "value": "技术架构" }, { "value": "客户案例" }]
    },
    { "type": "TextArea", "label": "备注" }
  ],
  "setting": {
    "success_message": "感谢报名！我们将于活动前一周发送参会指引"
  },
  "folder_token": "FLD_a1b2"
}
```

**常见错误**

- `Name cannot be empty`
- `Fields cannot be empty`
- `Invalid field type: <Type>` — 字段类型不在白名单
- `Folder not accessible` — folder_token 不属于当前用户
- `Insufficient scope: forms required`

### 字段类型白名单

**基础（19）**：`TextField` `TextArea` `NumberField` `EmailField` `MobileField` `TelephoneField` `IdCardField` `NameField` `AddressField` `LinkField` `GeoField` `AttachmentField` `DateTimeField` `TimeField` `RatingField` `NpsField` `RadioButton` `CheckBox` `DropDown`

**进阶（14）**：`TableField` `CascadeDropDown` `SortField` `LikertField` `MatrixField` `MatrixScaleField` `ImageRadioButton` `ImageCheckBox` `GoodsField` `FormulaField` `ReservationField` `FormAssociation` `ESignatureField` `AudioField`

**装饰 / 控件（6）**：`SectionBreak`（描述字段）`PageBreak` `WidgetButton` `WidgetContact` `WidgetMap` `WidgetMarquee`

**复杂字段示例片段**

```json
{
  "type": "GoodsField", "label": "选购", "unit": "件",
  "goods_items": [
    { "layout": "without_images", "name": "黑色 T 恤", "price": 99, "inventory": 50 },
    { "layout": "images", "name": "彩色 T 恤", "price": 99, "image_urls": ["https://cdn.example.com/tshirt.jpg"] },
    {
      "layout": "price_only", "name": "爱心捐款",
      "dimensions": [{ "label": "金额", "options": [{ "label": "100" }, { "label": "500" }, { "label": "自定义", "value": "customized" }] }],
      "skus": [
        { "specification": { "金额": "100" }, "price": 100 },
        { "specification": { "金额": "500" }, "price": 500 },
        { "specification": { "金额": "customized" }, "price": 0.01 }
      ]
    }
  ]
}
```

```json
{
  "type": "ReservationField", "label": "预约场次",
  "reservation_items": [{
    "name": "诊室 A",
    "quota_setting": {
      "type": "by_time_range_repeat_daily",
      "available_days_of_week": ["monday", "tuesday", "wednesday", "thursday", "friday"],
      "time_range_mode": "same_by_wday",
      "show_left_quota": true,
      "start_time_offset": { "offset_number": 1, "unit": "day" },
      "end_time_offset": { "offset_number": 14, "unit": "day" },
      "daily_time_range_quotas": [
        { "quota": 5, "start_time": { "hour": 9, "minute": 0 }, "end_time": { "hour": 12, "minute": 0 } },
        { "quota": 5, "start_time": { "hour": 14, "minute": 0 }, "end_time": { "hour": 17, "minute": 0 } }
      ]
    }
  }]
}
```

> `start_time_offset` = 提前预约要求（须提前 N 天 / 小时预约）；`end_time_offset` = 未来可约窗口（未来可约 N 天 / 小时内）；`unit` 取 `day` / `hour`，省略则无对应限制。`start_time` / `end_time` 传 `{ hour, minute }` 整数即可，`get_form` 读回时时刻是零填充字符串（`"09"`）。

```json
{
  "type": "FormulaField", "label": "总价",
  "formula_display": "<gd-field data-api-code=\"field_2\"></gd-field> * <gd-field data-cid=\"qty7x\"></gd-field>",
  "result_display_type": "numeric",
  "precision": 2,
  "icon_type": "cny1",
  "thousands_separator": true
}
```

> 公式引用规则：**已存在的字段**用 `data-api-code`；**同一请求里新增的字段**还没有 api_code，用 `data-cid`（值是该字段的 `cid`），保存时后端解析为新分配的 api_code。表格 / 矩阵的新维度用 `data-cid="表格cid" data-dimension-cid="列cid"`。不要预测 `field_N` 序号或自行指定 api_code。

```json
{
  "type": "FormAssociation", "label": "关联客户", "required": true,
  "associated_form_token": "MASTER_TOKEN",
  "associated_field_api_codes": ["field_1"],
  "display_field_api_codes": ["field_2", "field_3"]
}
```

```json
{
  "type": "SectionBreak", "label": "活动说明",
  "notes": "请仔细阅读以下规则……",
  "show_split_line": true,
  "show_part_description": true
}
```

---

## copy_form

**用途**：基于已有表单创建新表单（继承字段、主题、setting）。

**Scope**：`forms`

**输入**

| 参数 | 类型 | 必填 | 说明 |
| ---- | ---- | ---- | ---- |
| `form_token` | string | ✅ | 源表单 token |
| `name` | string | 否 | 新表单名，默认 `"Copy of <原名>"` |
| `folder_token` | string | 否 | 新表单要放进的文件夹 token |

**输出**

```json
{
  "name": "2026 年会报名表",
  "token": "newToken",
  "description": "...",
  "form_url": "https://jinshuju.net/f/newToken",
  "fields_count": 8,
  "created_at": "2026-05-17T10:00:00+08:00"
}
```

**常见错误**

- `Form cannot be found` — 源表单 token 错
- `Folder not accessible` — folder_token 不属于当前用户
- `Failed to copy form: ...`

---

## move_form

**用途**：把表单移到指定文件夹，或移回根目录。

**Scope**：`forms`

**输入**

| 参数 | 类型 | 必填 | 说明 |
| ---- | ---- | ---- | ---- |
| `form_token` | string | ✅ | 要移动的表单 token |
| `folder_token` | string | 否 | 目标文件夹 token；**省略或传 `""` = 移出文件夹回到根目录** |

**输出**

```json
{ "form_token": "abCdEf", "folder_token": "FLD_a1b2" }
```

移出文件夹时 `folder_token` 为 `null`：

```json
{ "form_token": "abCdEf", "folder_token": null }
```

**常见错误**

- `Form cannot be found`
- `Folder not accessible` — 文件夹不存在或不属于当前用户

---

## edit_form

**用途**：原子化地更新表单——可一次性改 name / description / setting / fields（字段增删改、选项增删改名）。

> ⚠️ **删字段 / 选项前先用 [`check_field_data`](#check_field_data) 查是否有提交数据**——删除有数据的字段 / 选项会永久清除这些数据且不可恢复。`has_data=true` 时先把影响告诉用户、取得确认再删（human-in-the-loop）。edit_form 本身不做拦截、不需要任何 force 参数，直接删。

**Scope**：`forms`

**输入**

| 参数 | 类型 | 必填 | 说明 |
| ---- | ---- | ---- | ---- |
| `form_token` | string | ✅ | |
| `name` | string | 否 | 新表单名 |
| `description` | string | 否 | 新表单说明 |
| `setting` | object | 否 | 见下"setting 全字段表"；**只传要改的 key，其他保持原值** |
| `fields` | object | 否 | `{ add[], remove[], update[], update_choices[] }` 四种操作，原子化执行 |
| `field_rules` | array | 否 | 字段显示规则，见下"field_rules 显示规则"；**整体替换语义** |

**必须至少传一个 edit 操作，否则报 `No edit operations specified`。**

### setting 全字段表

| 字段 | 类型 | 说明 |
| ---- | ---- | ---- |
| `entry_submit_mode` | enum | 提交后行为 `show_message` / `redirect` / `reports` / `exam_score`；填了 `success_redirect_url` 时强制改为 `redirect` |
| `success_message` | string | 文本成功页文案 |
| `success_message_rich_text` | string | HTML 富文本成功页（需套餐支持） |
| `success_message_style` | enum | `text` / `rich_text`；只传一个 message 字段时自动设置 |
| `success_redirect_url` | string | 跳转 URL |
| `success_redirect_fields` | string[] | 跳转 URL 上拼接哪些字段的 api_code |
| `open_entry_action` | enum | `hide` / `view` / `edit`（edit 需 submitter_edit_open_entry 套餐能力） |
| `open_entry_message` | string | 已填过表单的提示语 |
| `open_entry_cancel_reservation` | bool | 预约场景：edit 时是否显示"取消预约"按钮 |
| `show_serial_number_on_success` | bool | 成功页是否显示流水号 |
| `show_submit_again` | bool | 成功页是否显示"再次提交" |
| `manually_close_rule` | object | `{ closed: bool }`，写后清除其他 close rules |
| `by_time_range_close_rule` | object | `{ start_time, end_time }` ISO 8601 |
| `by_entries_close_rule` | object | `{ limit: int }` |
| `show_close_count_down` | bool | 显示截止倒计时；只在有时间 close rule 时生效，否则静默被重置成 false |
| `show_form_before_open` | bool | 开放前是否预览表单；同上 |
| `fill_frequency` | object | `{ fill_type, condition, cycle_period, cycles_per_period, limited_time, limited_field_api_codes }` |
| `password_required` | bool | 启用访问密码闸；开启时必须同时给 `access_password` |
| `access_password` | string | 访问密码 |
| `allowed_audience` | enum | `public` / `internal` / `private` / `gd_user_only` / `weixin_followers_only` / `weixin_qiye_followers_only` |
| `notification_rules` | array | 通知规则数组，见下 |

**notification_rules** —— **替换语义**：传该 key 会重建所有 MCP 管理的规则（即 `from_next=true` 的）；传 `[]` 清空 MCP 规则；4.0 桌面的规则（`from_next=false`）不会被动。

```json
[
  {
    "approach": "WXWORK",
    "url": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=...",
    "content": "新报名：$(field_1) - $(field_2)",
    "trigger_scope": "all_new",
    "mentioned_mobile_list": ["13812345678", "@all"],
    "enabled": true
  },
  {
    "approach": "DING_TALK",
    "url": "https://oapi.dingtalk.com/robot/send?access_token=...",
    "content": "新订单：$(field_3) 元",
    "trigger_scope": "all_new"
  },
  {
    "approach": "WEBHOOK",
    "url": "https://my.server/jinshuju-hook",
    "content": "{\"name\":\"$(field_1)\",\"mobile\":\"$(field_2)\"}",
    "trigger_scope": "all_new"
  }
]
```

`approach` 必须是 `WXWORK` / `DING_TALK` / `WEBHOOK` 之一；`trigger_scope` 取值：`all_new` / `all_update` / `matched_new` / `matched_update` / `all` / `schedule_time`。

### fields 四种操作

#### `fields.add: []`

形态与 `create_form.fields[]` 完全一致（含 `cid`，同请求内公式引用新字段时必需），可额外指定 `position`（0-based 插入位置，省略则追加到末尾）。

```json
{
  "fields": {
    "add": [
      { "type": "NumberField", "label": "年龄", "range_min": 18, "range_max": 100, "position": 2 },
      { "type": "AttachmentField", "label": "简历", "max_size": 8, "max_file_quantity": 2 }
    ]
  }
}
```

#### `fields.remove: ["api_code", ...]`

只传 api_code 列表；**不接受 label**。删除前先对每个 api_code 调 [`check_field_data`](#check_field_data)，有数据则向用户确认。

```json
{ "fields": { "remove": ["field_5", "field_7"] } }
```

#### `fields.update: []`

每项必须有 `api_code`，可修改 label / required / private / notes / unique / other_choice_required / 类型专属属性。**改 TableField / MatrixField 的 dimensions / statements 时必须带 dimension/statement 的 api_code**，否则旧数据引用会失效。传 `position`（0-based 整数）可把已存在字段移到新位置，保留 api_code 和数据；在 `fields.add` 插入之后应用，多个 `position` 按升序执行，越界钳到末尾。

```json
{
  "fields": {
    "update": [
      { "api_code": "field_1", "label": "全名", "required": true, "position": 0 },
      { "api_code": "field_3", "notes": "请填整数" },
      { "api_code": "field_8", "media_type": { "type": "custom", "value": ["pdf", "docx"] }, "max_size": 10 }
    ]
  }
}
```

#### `fields.update_choices: []`

选项字段的增删改名。**改文案永远用 `update`（保留 api_code）**，不要用 `remove` + `add`，否则历史数据引用失效。切换选项的**默认选中**也用 `update`（带 `api_code` + `selected`）；`add` 的新选项也可带 `selected`。`remove` 选项前先用 [`check_field_data`](#check_field_data)（带 `choice_value`）查该选项是否有数据，有则向用户确认。

```json
{
  "fields": {
    "update_choices": [
      {
        "field_api_code": "field_status",
        "add": [{ "value": "已签约", "quota": 100 }],
        "remove": [{ "api_code": "status_obsolete" }],
        "update": [{ "api_code": "status_contacted", "value": "已联系过", "selected": true, "operand_value": 3 }]
      }
    ]
  }
}
```

### field_rules 显示规则

按触发字段的值显示目标字段，或终止填写。**整体替换语义**：传 `field_rules` 会清空现有全部规则按数组重建；传 `[]` 清空所有规则；不传则保持不变。

> ⚠️ **是全量替换、不是合并，且无法撤销**：要"加一条 / 改一条"规则而不动其余，**必须先** `get_form`（带 `include_field_rules=true`）读出当前全部规则，把改动合并进完整列表，再把**完整列表**回传。只传新规则会把已有规则全部删掉，且没有历史可回滚。

```json
{
  "field_rules": [
    {
      "targets": ["field_2", "field_5"],
      "targets_display_mode": "show",
      "operator": "or",
      "conditions": [
        { "trigger": "field_1", "comparator": "equal", "value": ["choice_A"] }
      ]
    }
  ]
}
```

| 字段 | 说明 |
| ---- | ---- |
| `targets` | 目标字段 api_code 列表；`targets_display_mode=show` 时必填，`abort` 时忽略 |
| `targets_display_mode` | `show`（命中条件时显示目标字段）/ `abort`（命中条件时终止填写） |
| `operator` | 多条件组合方式 `and` / `or`，默认 `or` |
| `conditions[].trigger` | 触发字段 api_code |
| `conditions[].comparator` | **必须匹配触发字段类型**，否则整批规则被拒（报 `Field "<label>" does not support comparator "<x>"; available comparators: ...`）。选择类字段（单选 / 多选 / 下拉 / 级联 / 排序 / 预约 / 表单关联）用 `equal`（包含任一）/ `none_in`（都不包含）；评分 / NPS 用 `between`（数值区间）；文本类（文本 / 多行 / 邮箱 / 手机 / 座机 / 链接 / 身份证）用 `like` / `not_like`。**省略时按字段类型取主 comparator**：选择→`equal`、评分 / NPS→`between`、文本→`like`（不再一律默认 `equal`） |
| `conditions[].value` | 按 comparator 取标量 / 数组 |

注意：目标字段在表单顺序上必须位于触发字段**之后**，否则该规则被静默丢弃；目标字段必须保持**普通字段（`private=false`）**——显示规则自己负责"默认隐藏、命中条件才显示"，而 `private=true` 的隐藏字段对外永远不可见，设了规则也不会显示。⚠️ 工具 schema 描述里 "mark fields you want to reveal as private=true" 一句有误，勿照做。当前规则传 `include_field_rules=true` 从 `get_form` 的 `field_rules` 读取。

### 输出

```json
{
  "name": "2026 春季发布会报名表",
  "token": "abCdEf",
  "fields_count": 9,
  "form_url": "https://jinshuju.net/f/abCdEf",
  "updated_at": "2026-05-17T11:30:00+08:00"
}
```

**常见错误**

- `Form cannot be found`
- `No edit operations specified` — 一个操作都没传
- `Invalid field type: <Type>`
- `Failed to update form: <validation messages>`
- `Insufficient scope: forms required`

---

## check_field_data

**用途**：删字段 / 选项前的只读预检查——查某个字段（或它的某个选项）是否已有提交数据。删除有数据的字段 / 选项会永久清除数据且不可恢复，所以 `edit_form` / `edit_exam_form` / `edit_evaluation_form` 执行 `fields.remove` 或 `fields.update_choices[].remove` **之前**，对每个删除目标先调本工具；`has_data=true` 时把影响告诉用户、取得确认后再删。与 PC 端删除前的检查（GraphQL `formFieldMeta.hasData`）同一套逻辑、同一结果。

**Scope**：`forms`

**输入**

| 参数 | 类型 | 必填 | 说明 |
| ---- | ---- | ---- | ---- |
| `form_token` | string | ✅ | 表单 token 或 form id |
| `field_api_code` | string | ✅ | 要检查的字段 api_code（来自 get_form）；矩阵 / 表格的列传该列 dimension 的 api_code，并配 `parent_field` |
| `choice_value` | string | 否 | 只查某个选项时传该选项 api_code；省略则查整个字段是否有数据 |
| `choice_type` | enum | 否 | 选项类型，默认 `choice`；矩阵题目 / 项目用 `statement` / `dimension`，级联用 `level_1`..`level_4`；仅配合 `choice_value` 时有意义 |
| `parent_field` | string | 否 | 矩阵 / 表格列选项的父字段 api_code |
| `check_extended_text` | bool | 否 | 为 true 时检查选项后的"其他"输入框是否有数据 |

**输出**

```json
{ "form_token": "abCdEf", "field_api_code": "field_1", "field_label": "姓名", "has_data": true }
```

查选项时多返回 `choice_value`：

```json
{ "form_token": "abCdEf", "field_api_code": "field_2", "field_label": "状态", "has_data": false, "choice_value": "status_done" }
```

**常见错误**

- `Field not found: <api_code>` — 字段不存在，先 get_form 看当前字段
- `Form cannot be found`
- `Insufficient scope: forms required`

---

## create_exam_form

**用途**：创建在线考试表单（题目带正确答案 + 分值，提交后自动判分）。考试 / 测验 / quiz / 考核场景用这个，**不要用 create_form**。

**Scope**：`forms`

**输入**

| 参数 | 类型 | 必填 | 说明 |
| ---- | ---- | ---- | ---- |
| `name` | string | ✅ | 表单名 |
| `fields` | array | ✅ | 按显示顺序排列：考生信息字段在前，题目在后。**题目字段必须带 `answers`** |
| `description` | string | 否 | 表单说明 |
| `exam_setting` | object | 否 | 考试专属设置，见下 |
| `setting` | object | 否 | 仅 `fill_frequency`（考试常用 `fill_type=once` + `condition=by_device`）和 `by_time_range_close_rule`（开放时间窗） |
| `folder_token` | string | 否 | 文件夹 token |

**fields[] 可用类型**

- **题目**（必须带 `answers`，自动判分）：`SingleSelect` 单选题 / `MultiSelect` 多选题 / `TrueOrFalse` 判断题 / `DropDownSelect` 下拉题 / `FillInBlank` 填空题 / `ShortAnswer` 简答题 / `FillInNumber` 数字填空
- **考生信息**（不计分）：`NameField` / `MobileField` / `EmailField` / `IdCardField` / `TextField` / `DropDown`
- **排版**：`SectionBreak` / `PageBreak`

其他类型不接受。每个字段都要带表单内唯一的 `cid`（同 create_form），题干放 `label`，选项放 `choices: [{ value }]`。

**answers / answer_setting_mode**

每个答案项 `{ value, score }`。`answer_setting_mode` 决定组织方式：

| 模式 | 说明 | answers 形态 |
| ---- | ---- | ---- |
| `absolute`（默认） | 全对得满分否则零分 | 恰好一项；MultiSelect 的 value 是正确选项 value 数组，其他选择题是单个选项 value，填空 / 简答是期望文本，数字填空是数字 |
| `partial_absolute` | 仅 MultiSelect，按选项部分给分，错选零分 | 每个正确选项一项，各带分值 |
| `relative` | 每个选项都有分值，无错误答案 | 每个选项一项 |

选择题答案的 value 必须与某个 choice 的 value **完全一致**。可选 `answer_explanation` 提供答案解析（提供即自动开启解析展示）。

**exam_setting**

| 字段 | 类型 | 说明 |
| ---- | ---- | ---- |
| `notice_after_filling_mode` | enum | 交卷后展示：`grade` 成绩（默认）/ `explaination` 成绩+解析 / `answer` 仅对错 / `none` 不显示。需套餐支持，否则强制 `none` |
| `show_timeout` | bool | 限时答题。**默认不开，仅用户明确要求时传 true**；与题目字段 `required` 互斥（考生信息字段必填不受影响） |
| `limited_time` | int | 限时分钟数（默认 30），配合 `show_timeout=true` |
| `need_attention` | string | 考前须知 |
| `success_message_rich_text` | string | 交卷感谢文案（HTML，需套餐支持） |
| `interval_comments` | array | 分数区间评语 `[{ start_point, end_point, comment, retry? }]`；区间闭区间、不可重叠、按 start_point 升序；**整体替换语义** |

**输出**：同 create_form（`token` / `name` / `form_url` / `fields_count` / `created_at`）。

**常见错误**

- `Invalid field type` — 用了非考试字段类型；复杂普通表单请用 create_form
- 题目字段缺 `answers` 被拒
- 答案 value 与选项 value 不匹配
- `Duplicate field cid(s)` / `Invalid field cid(s)`

---

## edit_exam_form

**用途**：编辑考试表单（create_exam_form 创建的或 exam 场景的表单）：改名 / 描述、原子化增删改题目、改答案分值、改考试设置。**仅 exam 场景表单可用**，其他表单用 edit_form。

**Scope**：`forms`

**输入**

| 参数 | 类型 | 必填 | 说明 |
| ---- | ---- | ---- | ---- |
| `form_token` | string | ✅ | |
| `name` / `description` | string | 否 | |
| `fields` | object | 否 | `{ add[], remove[], update[], update_choices[] }`，形态同 [edit_form](#edit_form)；`add` 项同 create_exam_form 的 fields[] |
| `exam_setting` | object | 否 | 同 create_exam_form |
| `setting` | object | 否 | 同 create_exam_form |

**关键语义**

- `fields.update` 里**传任意一个 `answers` / `answer_setting_mode` / `answer_explanation` 都会重建该题的整个答案库**——必须传完整 answers 列表，不能只传增量
- 改选项导致正确答案变化时，在**同一请求**里通过 `fields.update` 传新的完整 answers
- 改选项文案用 `update_choices.update`（保留 api_code），不要 remove + add
- 删题目 / 选项前先用 [`check_field_data`](#check_field_data) 查是否有数据，有则向用户确认
- 先 `get_form` 读出现有题目结构（含 `customized_type`、按选项 value 的 `answers`）再改

**输出**：同 edit_form。

**常见错误**

- 非 exam 场景表单被拒（提示用 edit_form）
- 一个操作都没传被拒
- answers 引用了不存在的选项 value

---

## create_evaluation_form

**用途**：创建测评表单。测评 / 心理测试 / 能力评估 / 培训反馈场景用这个，**不要用 create_form**。两种风格：**计分测评**（计分题型 + 选项分值，常用 `relative` 模式，可配维度报告）和**纯反馈问卷**（普通字段，不计分）。

**Scope**：`forms`

**输入**

| 参数 | 类型 | 必填 | 说明 |
| ---- | ---- | ---- | ---- |
| `name` | string | ✅ | 表单名 |
| `fields` | array | ✅ | 评价人信息在前，题目在后。**计分题型必须带 `answers`** |
| `description` | string | 否 | |
| `evaluation_setting` | object | 否 | 测评专属设置，见下 |
| `setting` | object | 否 | 同 create_exam_form 的 setting |
| `folder_token` | string | 否 | |

**fields[] 可用类型**

- **计分题型**（必须带 `answers`，按所选项分值累计得分）：`SingleSelect` / `MultiSelect` / `DropDownSelect` / `Rating`（每个分值配 score）/ `Nps`
- **普通字段**（不计分）：`NameField` / `MobileField` / `EmailField` / `IdCardField` / `TextField` / `TextArea` / `RadioButton` / `CheckBox` / `DropDown` / `RatingField` / `NpsField` / `LikertField` / `MatrixScaleField`
- **排版**：`SectionBreak` / `PageBreak`

`answers` / `answer_setting_mode` 同 [create_exam_form](#create_exam_form)，测评通常用 `relative`（每个选项一个分值）。`Rating` / `RatingField` 支持 `rating_max`（3/5/10），`LikertField` / `MatrixScaleField` 用 `statements: [{ label }]`。每个字段带唯一 `cid`——**维度绑定计分题靠 cid**。

**evaluation_setting**

| 字段 | 类型 | 说明 |
| ---- | ---- | ---- |
| `notice_after_filling_mode` | enum | 提交后展示：`reports` 测评报告（默认）/ `customize` / `none`。需套餐支持 |
| `show_report_score` | bool | 报告显示总分 |
| `show_report_radar` | bool | 报告显示维度雷达图（需配置维度） |
| `show_indicator_comments` | bool | 报告显示各维度结果分析 |
| `show_comments` | bool | 开启测评评语 |
| `need_attention` | string | 测评须知 |
| `success_message_rich_text` | string | 提交感谢文案（HTML，需套餐支持） |
| `evaluation_comments` | array | 总分区间评语 `[{ start_point, end_point, comment, retry? }]`；**整体替换语义** |
| `indicator_setting` | object | 维度设置，见下 |

**indicator_setting（维度）**

```json
{
  "indicators_scoring_mode": "summation",
  "indicators": [
    {
      "name": "沟通能力",
      "field_cids": ["q1x7a", "q2b3c"],
      "standard_score": 80,
      "indicator_comments": [{ "start_point": 0, "end_point": 40, "comment": "待提升" }]
    }
  ]
}
```

- `indicators_scoring_mode`：维度得分 = 绑定题目`summation` 求和（默认）或 `average` 平均
- 维度绑定计分题：**本次请求新建的字段用 `field_cids`**（保存时解析成 api_code），已存在的字段用 `field_api_codes`
- `indicators` 是**整体替换语义**，且维度名 ≤ 20 字

**输出**：同 create_form。

---

## edit_evaluation_form

**用途**：编辑测评表单（create_evaluation_form 创建的或 evaluation 场景的表单）。**仅 evaluation 场景表单可用**，其他表单用 edit_form。

**Scope**：`forms`

**输入**：同 edit_exam_form 的结构（`form_token` 必填 + `name` / `description` / `fields{add,remove,update,update_choices}` / `evaluation_setting` / `setting`），fields 项形态同 create_evaluation_form。

**关键语义**

- answers 整体替换语义同 edit_exam_form
- ⚠️ **更新维度必须回传 `api_code`**：维度（indicators）是整体替换的，已提交数据的维度得分挂在 `indicator_<api_code>` 下。先从 `get_form` 的 `setting.evaluation_setting.indicator_setting.indicators` 读出每个现存维度的 `api_code` 并原样回传，否则维度会被当成新建，**已提交答卷的维度得分会失效**
- `LikertField` / `MatrixScaleField` 更新 `statements` 时同理带上 statement 的 `api_code` 保持身份
- 删字段 / 选项前先用 [`check_field_data`](#check_field_data) 查是否有数据，有则向用户确认

**输出**：同 edit_form。

---

## edit_theme

**用途**：编辑表单视觉主题——颜色、背景、**头图**（外链 / 本地上传 / Base64 / **AI 生成**）、字体、容器样式、提交按钮。

**Scope**：`form_setting`（⚠️ 独立 scope，不是 `forms`）

**输入**

| 参数 | 类型 | 必填 | 说明 |
| ---- | ---- | ---- | ---- |
| `form_token` | string | ✅ | |
| `primary_color` | string | 否 | 主色 hex，如 `"#FF5733"` |
| `secondary_color` | string | 否 | 副色 hex |
| `wallpaper` | object | 否 | `{ background_color, background_image_attachment_id }`（id 传 `""` 移除） |
| `header` | object | 否 | 见下 |
| `typography` | object | 否 | `{ form_header, field_label, choice_style }`，每项 `{ font_size, font_weight, color, text_align }` |
| `form_container` | object | 否 | `{ background_color }` |
| `submit_button` | object | 否 | `{ background_color, color, font_size }` |
| `generate_header_image` | object | 否 | `{ prompt?: string }`，让 AI 生成头图；省略 prompt 时按表单名+描述自动推断 |

**header 对象**

| 字段 | 类型 | 说明 |
| ---- | ---- | ---- |
| `type` | enum | `none` / `text` / `image` |
| `text` | string | 头图区文字（type=text 时） |
| `text_style` | object | `{ font_size, font_weight, color, text_align }` |
| `background_color` | string | 头部背景色 |
| `header_image_upload_token` | string | 本地 / 会话内图片：先 [`prepare_form_image_upload`](#prepare_form_image_upload)（`type=header`）上传，再把 token 传进来 |
| `header_image_url` | string | 外链图片 URL，服务端下载创建附件 |
| `header_image_base64` | string | Base64 图片数据（⚠️ LLM 易截断，能不用就不用） |

> 三个图片参数互斥，同时传时优先级：`header_image_upload_token` > `header_image_base64` > `header_image_url`。任一图片参数生效时 `type` 自动置为 `image`。

**至少传一个改动操作，否则报 `No theme edit operations specified`。**

**输出**

```json
{
  "form_token": "abCdEf",
  "primary_color": "#3B82F6",
  "secondary_color": "#93C5FD",
  "wallpaper": { "background_color": "#FFFBEB" },
  "header": {
    "type": "image",
    "has_header_image": true,
    "background_color": "#FEF3C7"
  },
  "typography": {
    "form_header": { "font-size": "24px", "font-weight": "bold", "color": "#1F2937", "text-align": "center" },
    "field_label": { "font-size": "14px", "color": "#374151" },
    "choice_style": { "color": "#4B5563" }
  },
  "form_container": { "background_color": "#FFFFFF" },
  "submit_button": { "background_color": "#3B82F6", "color": "#FFFFFF", "font_size": "16px" }
}
```

**调用示例**

```json
{
  "form_token": "abCdEf",
  "primary_color": "#1E40AF",
  "generate_header_image": { "prompt": "蓝紫色科技感主题，适合发布会报名表的横幅头图" }
}
```

**常见错误**

- `Insufficient scope: form_setting required` — OAuth 授权时**没勾上 form_setting**（用户最常见的坑：以为 `forms` scope 就够，结果调 edit_theme 被拒）
- `Form cannot be found`
- `No theme edit operations specified`
- `Failed to update theme: <validation messages>`

---

## prepare_form_image_upload

**用途**：把**只存在于本地 / 对话上下文中的图片**上传为表单自身的图片。`type` 决定用途：`field_choice` = 图片选项（`ImageRadioButton` / `ImageCheckBox`）的选项配图，`header` = 表单头图。返回上传凭证后，调用方自行发 HTTP multipart 请求上传，再把 token 传给对应工具。

**Scope**：按 `type` 区分——`field_choice` 需要 `forms`，`header` 需要 `form_setting`

**输入**

| 参数 | 类型 | 必填 | 说明 |
| ---- | ---- | ---- | ---- |
| `type` | enum | ✅ | `field_choice` / `header` |
| `filename` | string | ✅ | 原始文件名，如 `banner.png` |
| `content_type` | string | ✅ | MIME 类型：`image/jpeg` / `image/png` / `image/gif` / `image/webp` |
| `size` | integer | ✅ | 文件精确字节数 |

**输出**

```json
{
  "method": "POST",
  "upload_url": "https://jinshuju.net/api/v1/form_image_attachments",
  "headers": {},
  "fields": { "form_image_token": "form_img_tok_..." },
  "file_field": "file",
  "form_image_token": "form_img_tok_...",
  "expires_at": "2026-06-12T08:30:00Z"
}
```

**使用流程**

1. 按返回的 `method` + `upload_url` 发 multipart/form-data 请求：带上 `fields` 里的所有键值，文件放在名为 `file`（`file_field`）的字段里
2. 上传成功（HTTP 201）后引用 token：
   - `type=field_choice` → `create_form` / `edit_form` 选项里的 `choices[].image_upload_token`
   - `type=header` → `edit_theme` 的 `header.header_image_upload_token`
3. **token 有效期 30 分钟**（见 `expires_at`），过期重新调用本工具；上传文件的 filename / content_type / size 必须与申请时完全一致
4. token 与申请时的 `type` 绑定，不能混用；`image_upload_token` / `image_url` / `image_base64` 互斥，优先级依此顺序

**常见错误**

- `type must be one of: field_choice, header.`
- `form_image_token is invalid or expired; prepare upload again` — token 过期 / 未上传 / 不是当前用户申请的
- `... was prepared with type=header; prepare upload with type=field_choice`（及反向）— token 的 type 与用途不匹配，按提示重新申请

---

## prepare_entry_attachment_upload

**用途**：把本地文件上传后写入数据的**附件字段**（AttachmentField），配合 `create_entry` / `update_entry` 使用。比 base64 内联省上下文。

**Scope**：`write_entries`

**输入**

| 参数 | 类型 | 必填 | 说明 |
| ---- | ---- | ---- | ---- |
| `form_token` | string | ✅ | |
| `field_api_code` | string | ✅ | 附件字段的 api_code；表格内附件列传表格字段的 api_code |
| `dimension_api_code` | string | 表格列时✅ | 表格字段内附件列的 api_code |
| `filename` | string | ✅ | |
| `content_type` | string | ✅ | |
| `size` | integer | ✅ | 精确字节数 |

**输出**：同 prepare_form_image_upload 的结构，`upload_url` 为 `POST /api/v1/forms/{form_token}/entry_attachments`，token 字段名为 `attachment_token`，`fields` 里还带 `field_api_code`（和可选 `dimension_api_code`）。

**使用流程**

1. multipart 上传成功（HTTP 201）后，在 `create_entry` / `update_entry` 的附件字段值里引用：`{ "field_5": [{ "attachment_token": "entry_att_tok_..." }] }`
2. token 受附件字段的 `max_size` / `max_file_quantity` 配置约束，30 分钟过期，且绑定申请时的表单 / 字段 / 用户

**常见错误**

- `attachment_token is invalid or expired; prepare upload again`
- `dimension_api_code is required when field is a table field`

---

# Entries

## list_entries

**用途**：分页列出表单的数据条目，支持复杂字段过滤（filters）。

**Scope**：`read_entries`

**输入**

| 参数 | 类型 | 必填 | 说明 |
| ---- | ---- | ---- | ---- |
| `form_token` | string | ✅ | 表单 token 或 form id |
| `next` | integer | 否 | 翻页游标（上次响应里的 `next`，即 `serial_number`） |
| `created_at` | string | 否 | ISO 8601 字符串，"创建时间 >= 此刻"的简单单边过滤（等价于 `filters=[{field:"created_at", operator:"gte", value:...}]`） |
| `filters` | array / string | 否 | 字段值条件数组，AND 组合；也可传 JSON 字符串 |

### filters 完整说明

每个元素 `{ field, operator, value }`：

| 类别 | operator | value 形式 | 示例 |
| ---- | -------- | ---------- | ---- |
| 等值 | `eq` / `ne` | 标量 | `{"field":"field_1","operator":"eq","value":"张三"}` |
| 比较 | `gt` / `gte` / `lt` / `lte` | 标量 | `{"field":"field_3","operator":"gte","value":6}` |
| 区间 | `between` / `not_between` | `[min, max]` 闭区间 | `{"field":"field_3","operator":"between","value":[80,100]}` |
| 集合 | `any_in` / `none_in` | 数组 | `{"field":"field_2","operator":"any_in","value":["city_bj","city_sh"]}` |
| 文本子串 | `like` / `not_like` | 子串字符串（不区分大小写，**不接受 SQL 通配符**） | `{"field":"field_2","operator":"like","value":"张"}` |
| 是否为空 | `null` / `not_null` | 省略 | `{"field":"field_4","operator":"not_null"}` |

**关键约束**：

1. **选项字段的 value 传 `choices[].api_code`**（如 `city_sh`），不是 label（`"上海"`）
2. `created_at` 是合法字段，可与 `gte` / `between` 等数值 operator 组合
3. **filters 中含 `created_at` 时，结果按 `created_at` 升序**；否则按 `serial_number` 升序
4. **不支持任意字段排序**——倒序 / 取前 N 在本地处理
5. operator 跟字段类型不匹配会被服务端拒，并列出该字段允许的 operator——直接照着改
6. `creator_id` 是合法过滤字段（按提交者查数据，如申诉 / 反馈记录）：**只支持 `eq`**，value 是单个用户 id 字符串（合法 ObjectId，即 entry 返回的 `creator_id`）；传非法值会被拒。例：`{"field":"creator_id","operator":"eq","value":"5f3a1c2b4d5e6f7a8b9c0d1e"}`

operator × 字段类型兼容矩阵：

| 字段类型 | 可用 operator |
| -------- | ------------- |
| 文本类（Text / TextArea / Name / Email / Mobile / Telephone / IdCard / Link） | `eq` `ne` `any_in` `none_in` `null` `not_null` `like` `not_like` |
| `NumberField` | `eq` `ne` `null` `not_null` `gte` `gt` `lte` `lt` `between` `not_between` |
| `DateTimeField` / `created_at` | `eq` `ne` `null` `not_null` `like` `gte` `gt` `lte` `lt` `between` `not_between` |
| `RatingField` / `NpsField` | `eq` `ne` `null` `not_null` `gte` `gt` `lte` `lt` |
| `RadioButton` / `CheckBox` / `DropDown` | `eq` `ne` `any_in` `none_in` `null` `not_null` `like` `not_like` |
| `FormAssociation` | `eq` `ne` `any_in` `none_in` `null` `not_null` |
| `AttachmentField` / `GeoField` / `TableField` | `null` `not_null` `like` |
| `ESignatureField` | `null` `not_null` |

### 输出

```json
{
  "total": 128,
  "count": 50,
  "data": [
    {
      "serial_number": 1,
      "token": "ENTRY_TOKEN_1",
      "creator_name": "张三",
      "creator_id": "5f3a1c2b4d5e6f7a8b9c0d1e",
      "created_at": "2026-04-20T10:00:00+08:00",
      "field_1": "张三",
      "field_2": "13812345678",
      "field_3": "city_sh",
      "field_4": ["topic_product", "topic_tech"]
    }
  ],
  "next": 51
}
```

> **单次最多 50 条**。需要更多用 `next` 翻页（值是 `serial_number`）。
>
> `creator_id` 是提交者的稳定用户 id（`get_entry` / `list_entries` 才返回；v1/v2 API、Webhook、导出等其它出口都没有）。

**调用示例**

```json
{
  "form_token": "abCdEf",
  "filters": [
    { "field": "field_3", "operator": "eq", "value": "city_sh" },
    { "field": "field_2", "operator": "like", "value": "138" },
    { "field": "created_at", "operator": "gte", "value": "2026-05-01 00:00:00" }
  ]
}
```

**常见错误**

- `Insufficient scope: read_entries required`
- `Form cannot be found`
- 400 错配：`Operator 'gte' not supported for field 'field_1' (NameField). Allowed operators: eq, ne, any_in, none_in, null, not_null, like, not_like.`

---

## list_my_submitted_entries

**用途**：列出当前用户在指定表单里**自己提交**的数据条目，按提交时间倒序。即使该表单不属于你、你只是填写者也能用（结果只含你自己的条目）。

**Scope**：`read_entries`

**输入**

| 参数 | 类型 | 必填 | 说明 |
| ---- | ---- | ---- | ---- |
| `form_token` | string | ✅ | 表单 token 或 form id |
| `next` | integer | 否 | 翻页偏移量（上次响应里的 `next`） |
| `limit` | integer | 否 | 默认 50，最大 50 |

**输出**：结构同 [`list_entries`](#list_entries)（`total` / `count` / `data[]` / `next`），`data` 里只含你自己提交的条目，`next` 是整数偏移游标。

**常见错误**

- `Form not found — check the token.`
- `Insufficient scope: read_entries required`

---

## get_entry

**用途**：拿单条 entry 的完整字段值。

**Scope**：`read_entries`

**输入**

| 参数 | 类型 | 必填 | 说明 |
| ---- | ---- | ---- | ---- |
| `form_token` | string | ✅ | 表单 token 或 form id |
| `serial_number` | integer | ✅ | 条目流水号（表单内自增） |

**输出**

```json
{
  "serial_number": 12,
  "token": "ENTRY_TOKEN_12",
  "creator_name": "张三",
  "creator_id": "5f3a1c2b4d5e6f7a8b9c0d1e",
  "created_at": "2026-05-15T14:30:00+08:00",
  "field_1": "张三",
  "field_2": "13812345678",
  "field_3": "city_sh",
  "field_4": ["topic_product"]
}
```

> `creator_id` 是提交者的稳定用户 id，可拿去 `list_entries` 用 `creator_id` filter 查该用户提交的全部数据。

**常见错误**

- `Form cannot be found`
- `Entry cannot be found` — serial_number 不存在
- `Insufficient scope: read_entries required`

---

## create_entry

**用途**：给指定表单新增一条数据。

**Scope**：`write_entries`

**输入**

| 参数 | 类型 | 必填 | 说明 |
| ---- | ---- | ---- | ---- |
| `form_token` | string | ✅ | |
| `entry` | object | ✅ | `{ api_code: value }` 形式的字段值；未知 key 静默过滤 |

**字段值规范（重点）**

- **key 必须是 `api_code`**（如 `field_1`、`field_mobile`），不是中文 label
- **选项字段的 value 传选项 `api_code`**（如 `code_male` / `city_sh`），不是 label
- 简单字段（`TextField` / `NumberField` / `MobileField` / `NameField` / `IdCardField` / `EmailField`）传**纯字符串或数字**，不要包对象
- `TableField`：对象数组，每行是 `{ dimension_api_code: value }`
- `AddressField`：`{ province, city, district, street }`
- `MultipleChoice`：api_code 数组
- 写入会被忽略：`ESignatureField` / `FormulaField`（在 `NOT_SUPPORT_UPDATE_FIELDS` 黑名单内）
- `AttachmentField`：先 [`prepare_entry_attachment_upload`](#prepare_entry_attachment_upload) 上传拿 token，再传 `[{ "attachment_token": "entry_att_tok_..." }]`；小文件也可内联 base64 `[{ "base64": "...", "file_name": "a.png", "content_type": "image/png" }]`（耗上下文，能不用就不用）；已有附件 id 可直接传。表格内附件列在行对象里用相同格式
- `MobileField` 号段正则仍然跑——保留测试号段如 `13800138000` 会被 400 拒；MCP 路径下跳过短信验证码

**输出**

```json
{
  "serial_number": 129,
  "token": "ENTRY_TOKEN_129",
  "creator_name": "<API 调用方名称>",
  "created_at": "2026-05-17T12:00:00+08:00",
  "field_1": "张三",
  "field_2": "13812345678",
  "field_3": "city_sh"
}
```

**调用示例**

```json
{
  "form_token": "abCdEf",
  "entry": {
    "field_1": "张三",
    "field_2": "13812345678",
    "field_3": "city_sh",
    "field_4": ["topic_product", "topic_tech"]
  }
}
```

**常见错误**

- `Form cannot be found`
- `Entry attributes cannot be empty` — `entry` 是 `{}` 或全是未知 key
- `Form has reached entries limit` — 表单达条目上限
- 字段 validation 错误（required 缺失 / Email 格式 / Choice 无效值 / Mobile 号段 等）— 错误信息含 `<字段>` + 具体原因
- `Insufficient scope: write_entries required`

---

## create_entries

**用途**：一次给指定表单新增多条数据。导入大量记录时**优先用本工具**，而不是循环调 `create_entry`——单次请求搞定，省去 N 次往返和 N 份冗长返回。

**Scope**：`write_entries`

**输入**

| 参数 | 类型 | 必填 | 说明 |
| ---- | ---- | ---- | ---- |
| `form_token` | string | ✅ | |
| `entries` | array | ✅ | 数据对象数组，最多 **200** 条；每个元素是 `{ api_code: value }`，格式与 [`create_entry`](#create_entry) 的 `entry` 完全一致 |

字段值规范与 [`create_entry`](#create_entry) 一致（key 必须是 `api_code`、选项传选项 `api_code`、`ESignatureField` / `FormulaField` 写入被忽略 等）。

**行为要点**

- **部分成功**：逐条校验，通过的写入、失败的跳过，并在 `errors` 中按数组下标返回原因；只要有一条成功就返回 `ok: true`。
- **不幂等**：重复调用会产生重复数据，本工具不做去重 / upsert。
- 批量写入复用 Excel 导入引擎，**跳过逐条 save 回调**，公式字段写入后异步重算。
- 只返回汇总（`created_count` + 每条错误），**不返回写入后的完整 entries**——要看明细另行 `list_entries`。

**输出**

```json
{ "ok": true, "created_count": 2, "errors": [] }
```

部分成功时 `errors` 按下标返回：

```json
{ "ok": true, "created_count": 1, "errors": [{ "index": 1, "reason": "姓名 不能为空" }] }
```

**调用示例**

```json
{
  "form_token": "abCdEf",
  "entries": [
    { "field_1": "张三", "field_2": "13812345678", "field_3": "city_sh" },
    { "field_1": "李四", "field_2": "13800000000", "field_3": "city_bj" }
  ]
}
```

**常见错误**

- `Form cannot be found`
- `Entries cannot be empty` — `entries` 为空数组
- `A batch can contain at most 200 entries` — 超过单批上限，自行分批
- `This form has reached its entry limit, ...` — 写入后会超表单条目上限，整批不写入
- `Insufficient scope: write_entries required`

---

## update_entry

**用途**：更新单条 entry。**只支持单条**，批量要逐条循环调用。

**Scope**：`write_entries`

**输入**

| 参数 | 类型 | 必填 | 说明 |
| ---- | ---- | ---- | ---- |
| `form_token` | string | ✅ | |
| `serial_number` | integer | ✅ | 目标 entry 的流水号 |
| `entry` | object | ✅ | `{ api_code: value }`，未知 key 静默过滤 |
| `is_put` | bool | 否 | 默认 `false`（PATCH，只改提供的字段）；`true` = PUT 全替换 |

⚠️ **`is_put=true` 危险**：PUT 会把未提供的字段**全部清空**。做"只改某字段"的部分更新永远保持默认 `false`。只有用户明确说"整条覆盖"且已列全所有字段值时才允许 PUT。

**输出**

```json
{
  "serial_number": 12,
  "token": "ENTRY_TOKEN_12",
  "field_1": "李四",
  "field_2": "13812345678",
  "field_3": "city_bj"
}
```

**调用示例（PATCH 改单字段）**

```json
{
  "form_token": "abCdEf",
  "serial_number": 12,
  "entry": { "field_status": "status_contacted" },
  "is_put": false
}
```

**常见错误**

- `Form cannot be found`
- `Entry cannot be found`
- `Entry attributes cannot be empty`
- 字段 validation 错误
- `Insufficient scope: write_entries required`

---

## delete_entry

**用途**：删除单条 entry。**只支持单条**，批量逐条循环；删除前必须二次确认。

**Scope**：`write_entries`

**输入**

| 参数 | 类型 | 必填 | 说明 |
| ---- | ---- | ---- | ---- |
| `form_token` | string | ✅ | |
| `serial_number` | integer | ✅ | |

**输出**

```json
{ "serial_number": 12 }
```

**常见错误**

- `Form cannot be found`
- `Entry cannot be found`
- `Failed to delete the entry, try later` — 底层 delete 失败
- `Insufficient scope: write_entries required`

---

# Account

## get_current_user

**用途**：拿当前凭证对应的用户信息。回答"我是谁 / 我属于哪个企业 / 我啥角色"时优先调。

**Scope**：`user`

**输入**：无参数

**输出**

```json
{
  "id": "abc123",
  "name": "张三",
  "email": "zhangsan@example.com",
  "mobile": "13812345678",
  "role": "owner",
  "billing_account_id": "ba_xxx",
  "created_at": "2024-01-15T10:00:00Z"
}
```

`role` 取值：`owner` / `admin` / `worker` / `outworker`。

**常见错误**

- `User cannot be found`
- `Insufficient scope: user required`

---

## get_current_billing_account

**用途**：拿当前用户所属企业账户的套餐 / 用量 / 试用信息。回答"我什么套餐 / 还剩多少额度 / 什么时候到期"时优先调。

**Scope**：`billing_account`

**输入**：无参数

**输出**

```json
{
  "id": "ba_xxx",
  "name": "示例公司",
  "subdomain": "demo",
  "users_count": 12,
  "plan": {
    "code": "professional",
    "name": "专业版",
    "end_date": "2026-12-31",
    "expired": false,
    "org_plan": false
  },
  "feature_trial": {
    "in_use": false,
    "expired": false,
    "end_date": null
  },
  "usage": {
    "sms": { "total_quota": 1000, "total_balance": 800, "month_balance": 200, "consumed_quota": 200 },
    "active_mail": { "total_quota": 500, "total_balance": 450, "month_balance": 50, "consumed_quota": 50 },
    "entry_quota": { "total_quota": 50000, "total_balance": 45000, "month_balance": 2000, "consumed_quota": 5000 },
    "storage_quota": { "total_quota": 10240, "total_balance": 8000, "month_balance": 1000, "consumed_quota": 2240 },
    "ai_points": { "total_quota": 1000, "total_balance": 700, "month_balance": 100, "consumed_quota": 300 },
    "audio_quota": { "total_quota": 3600, "total_balance": 3000, "month_balance": 600, "consumed_quota": 600 },
    "entry_transaction_quota": { "unlimited": true, "consumed_quota": 128000 }
  }
}
```

> `usage` 各项均为**原始内部单位**：`ai_points`（AI 点数）、`audio_quota` 单位是**秒**、`entry_transaction_quota`（月度收款交易额）单位是**分**（cents），展示前自行换算。无限额套餐的项返回 `{ "unlimited": true, "consumed_quota": <n> }`，此时**不含** `total_quota` / `total_balance` / `month_balance`。

**常见错误**

- `User cannot be found`
- `Billing account cannot be found`
- `Insufficient scope: billing_account required`

---

## list_account_users

**用途**：列出当前企业账户的所有成员。主要用于"把表单协作给某团队成员"前先找到对方 id。

**Scope**：`billing_account`

**输入**

| 参数 | 类型 | 必填 | 说明 |
| ---- | ---- | ---- | ---- |
| `limit` | integer | 否 | 默认 50，最大 100 |

**输出**

```json
{
  "count": 12,
  "data": [
    { "id": "u_xxx", "name": "张三", "email": "zhangsan@example.com", "mobile": "13812345678", "role": "owner", "status": "active" },
    { "id": "u_yyy", "name": "李四", "email": "lisi@example.com",     "mobile": "13898765432", "role": "worker", "status": "active" }
  ]
}
```

> ⚠️ **MCP 暂未提供 add_cooperator / share_form 类协作工具**。拿到成员 id 后实际分享操作要去后台 web 端完成。

**常见错误**

- `User cannot be found`
- `Billing account cannot be found`
- `Insufficient scope: billing_account required`

---

# 通用规则

## 鉴权方式

金数据 MCP 支持三种鉴权（同一端点 `https://jinshuju.net/mcp`）：

1. **HTTP Basic** —— `Authorization: Basic <base64(api_key:api_secret)>`。Scope 不受限（等价于全开）
2. **JWT** —— `Authorization: Bearer <jwt_token>`。Scope 不受限
3. **OAuth 2.0** —— `Authorization: Bearer <access_token>`。**Scope 按授权范围生效**，未授权 scope 调用会被拒

OAuth metadata 端点：
- `https://jinshuju.net/.well-known/oauth-protected-resource`
- `https://jinshuju.net/.well-known/oauth-authorization-server`

## 错误返回结构

工具失败时抛 `StandardError`，消息会回流给 AI 客户端，常见前缀：

- `Unknown parameter(s): <keys>. This tool only supports: <params>` — 传了工具未声明的参数（如给 list_forms 传 folder_token）；照错误信息列出的参数改
- `Insufficient scope: <scope> required` — OAuth scope 不够
- `Form cannot be found` — 表单不存在 / 无权访问
- `Entry cannot be found` — 条目不存在
- `Folder not accessible` — 文件夹不存在 / 无权管理
- `No edit operations specified` — edit_form / edit_theme 一个操作都没传
- `Invalid field type: <X>` — 不在白名单
- `Entry attributes cannot be empty` — entry 是 `{}` 或全是未知 key
- `Form has reached entries limit` — 表单达条目上限
- `Failed to <action>: <validation messages>` — 底层 service save 失败，含详细 errors
