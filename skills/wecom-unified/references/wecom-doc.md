# 企业微信文档、表格、智能表格与智能文档管理

> 公共概念与规则请参考 [wecom-shared.md](wecom-shared.md)

管理企业微信文档和智能文档（原名智能主页）的创建、读取和编辑，表格（在线表格）的读取以及智能表格的结构（子表、字段/列）和数据（记录）管理。文档接口支持通过 `docid` 或 `url` 二选一定位文档。

> ⚠️ **重要触发规则**：只有当用户明确提到「**智能文档**」或「**智能主页**」时，才使用智能文档相关接口（`smartpage_*` 系列）。其他所有涉及「文档」的场景（如"创建文档"、"写个文档"、"帮我建个文档"等），一律使用企微文档接口（`create_doc` / `get_doc_content` / `edit_doc_content`）。

## 调用方式

通过 `wecom-cli` 调用，品类为 `doc`：

```bash
wecom-cli doc <tool_name> '<json_params>'
```

---

## URL 品类识别与接口路由

企业微信文档有四种品类，**URL 格式不同，读取内容所用的接口也不同**，切勿混用。其中**表格（在线表格）与智能表格是两类不同品类**，请通过 URL 严格区分：

| URL 模式 | 品类 | 读取内容接口 |
|---|---|---|
| `https://doc.weixin.qq.com/doc/*` | **文档**（doc_type=3） | `get_doc_content` |
| `https://doc.weixin.qq.com/sheet/*` | **表格 / 在线表格** | `get_doc_content` |
| `https://doc.weixin.qq.com/smartsheet/*` | **智能表格**（doc_type=10） | `smartsheet_get_sheet` → `smartsheet_get_records` |
| `https://doc.weixin.qq.com/smartpage/*` | **智能文档**（原名智能主页） | `smartpage_export_task` → `smartpage_get_export_result` |

**判断规则**：
- URL 路径以 `/doc/*` 开头 → 文档 → 用 `get_doc_content`
- URL 路径以 `/sheet/*` 开头 → 表格（在线表格） → 用 `get_doc_content`
- URL 路径以 `/smartsheet/*` 开头 → 智能表格 → 用 `smartsheet_get_sheet`
- URL 路径以 `/smartpage/*` 开头 → 智能文档（原名智能主页） → 用 `smartpage_export_task`

> ⚠️ **表格 ≠ 智能表格**：二者是不同品类（`/sheet/` vs `/smartsheet/`）。

## 返回格式说明

所有接口返回 JSON 对象，包含以下公共字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `errcode` | integer | 返回码，`0` 表示成功，非 `0` 表示失败 |
| `errmsg` | string | 错误信息，成功时为 `"ok"` |

当 `errcode` 不为 `0` 时，说明接口调用失败，可重试 1 次；若仍失败，将 `errcode` 和 `errmsg` 展示给用户。

### 特殊错误码

| errcode | errmsg | 含义 | 处理方式 |
|---------|--------|------|----------|
| `851002` | `incompatible doc type` | 文档品类与所调用的接口不匹配 | 根据文档 URL 重新确认品类（参见上方「URL 品类识别与接口路由」表），然后使用该品类对应的正确接口重试 |
| `851003` | `no authority` | 无权限调用该接口，**智能表格写入场景**下通常是企业可见范围 > 10 人的规模限制 | 若发生在 `smartsheet_add_records` / `smartsheet_update_records`，引导用户走 Webhook 兜底方案，详见 [wecom-doc-smartsheet-webhook.md](wecom-doc-smartsheet-webhook.md)；其他接口则按权限问题排查 |

---

## 一、文档管理

### get_doc_content

获取**文档 / 表格（在线表格） / 智能表格**的完整内容数据，统一以 Markdown 格式返回。采用**异步轮询机制**：首次调用无需传 `task_id`，接口返回 `task_id`；若 `task_done` 为 false，需携带该 `task_id` 再次调用，直到 `task_done` 为 true 时返回完整内容。

> 适用 URL：`/doc/*`、`/sheet/*`、`/smartsheet/*`。`/smartpage/*`（智能文档）不适用，请改用 `smartpage_export_task`。

- 首次调用（不传 task_id）：
```bash
wecom-cli doc get_doc_content '{"docid": "DOCID", "type": 2}'
```
- 轮询（携带上次返回的 task_id）：
```bash
wecom-cli doc get_doc_content '{"docid": "DOCID", "type": 2, "task_id": "xxx"}'
```
- 通过 URL 读取文档：
```bash
wecom-cli doc get_doc_content '{"url": "https://doc.weixin.qq.com/doc/xxx", "type": 2}'
```
- 通过 URL 读取表格（在线表格）：
```bash
wecom-cli doc get_doc_content '{"url": "https://doc.weixin.qq.com/sheet/xxx", "type": 2}'
```

参见 [API 详情](wecom-doc-get-doc-content.md)

### create_doc

新建文档（doc_type=3）或智能表格（doc_type=10）。创建成功返回 url 和 docid。

- 创建文档：
```bash
wecom-cli doc create_doc '{"doc_type": 3, "doc_name": "项目周报"}'
```
- 创建智能表格：
```bash
wecom-cli doc create_doc '{"doc_type": 10, "doc_name": "任务跟踪表"}'
```

**注意**：
- docid 仅在创建时返回，需妥善保存。创建智能表格时默认包含一个子表，可通过 `smartsheet_get_sheet` 查询其 sheet_id。
- 普通表格（在线表格，URL 含 `/sheet/`）本 skill **仅支持读取**（通过 `get_doc_content`），不支持创建

参见 [API 详情](wecom-doc-create-doc.md)。

### edit_doc_content

用 Markdown 内容覆写文档正文。`content_type` 固定为 `1`（Markdown）。

```bash
wecom-cli doc edit_doc_content '{"docid": "DOCID", "content": "# 标题\n\n正文内容", "content_type": 1}'
```

参见 [API 详情](wecom-doc-edit-doc-content.md)。

---

## 二、智能文档（原名智能主页）

适用品类：智能文档（用户说「智能文档」或「智能主页」时触发）
适用 URL：`/smartpage/*`

> ⚠️ 只有当用户明确指定「智能文档」或「智能主页」时，才使用以下接口。其他「文档」场景请使用上方的企微文档接口。

适用场景：
1. 将本地 Markdown 文件创建为智能文档
2. 异步导出智能文档内容为 Markdown

### smartpage_create

创建智能文档（原名智能主页），支持传入标题和多个子页面。每个子页面可指定标题、内容类型和本地文件路径。创建成功返回 docid 和 url。

> ⚠️ **特殊语法**：此命令必须使用 `+smartpage_create`（带 `+` 前缀），加号不可省略；该 `+` 仅适用于此命令，不要泛化到其他 `doc` 子命令。

```bash
wecom-cli doc +smartpage_create '{"title": "项目概览", "pages": [{"page_title": "需求文档", "content_type": 1, "page_filepath": "/path/to/requirements.md"}]}'
```

**注意**：
- `content_type` **必须与文件实际内容匹配**：`.md` 文件或包含 Markdown 语法的内容必须传 `1`（Markdown），仅纯文本才传 `0`。绝大多数场景应传 `1`
- docid 仅在创建时返回，需妥善保存
- 每个子页面的 Markdown 文件大小不得超过 **10MB**，超过会导致创建失败。如果文件过大，需先拆分为多个子页面再创建

参见 [API 详情](wecom-doc-smartpage-create.md)。

### smartpage_export_task

发起智能文档内容导出任务（异步）。传入 docid（或 url）和 content_type，返回 task_id。这是异步导出的第一步，需配合 `smartpage_get_export_result` 轮询获取导出结果。

- 通过 docid：
```bash
wecom-cli doc smartpage_export_task '{"docid": "DOCID", "content_type": 1}'
```
- 或通过 URL：
```bash
wecom-cli doc smartpage_export_task '{"url": "https://doc.weixin.qq.com/smartpage/xxx", "content_type": 1}'
```

参见 [API 详情](wecom-doc-smartpage-export.md)。

### smartpage_get_export_result

查询智能文档导出任务进度。传入 task_id 进行轮询，当 `task_done` 为 `true` 时返回 `content`（导出的完整文档内容）。

```bash
wecom-cli doc smartpage_get_export_result '{"task_id": "TASK_ID"}'
```

当 `task_done` 为 `true` 时，`content` 字段即为导出的 Markdown 内容。

参见 [API 详情](wecom-doc-smartpage-export.md)。

---

## 三、智能表格结构管理

### smartsheet_get_sheet

查询文档中所有子表信息，返回 sheet_id、title、类型等。

```bash
wecom-cli doc smartsheet_get_sheet '{"docid": "DOCID"}'
```

### smartsheet_add_sheet

添加空子表。新子表不含视图、记录和字段，需通过其他接口补充。

```bash
wecom-cli doc smartsheet_add_sheet '{"docid": "DOCID", "properties": {"title": "新子表"}}'
```

**注意**：新建智能表格文档默认已含一个子表，仅需多个子表时调用。

### smartsheet_update_sheet

修改子表标题。需提供 sheet_id 和新 title。

```bash
wecom-cli doc smartsheet_update_sheet '{"docid": "DOCID", "properties":{"sheet_id":"SHEET_ID", "title":"新子表"}}'
```

### smartsheet_delete_sheet

永久删除子表，**操作不可逆**。

```bash
wecom-cli doc smartsheet_delete_sheet '{"docid": "DOCID", "sheet_id": "SHEETID"}'
```

### smartsheet_get_fields

查询子表的所有字段信息，返回 field_id、field_title、field_type。

```bash
wecom-cli doc smartsheet_get_fields '{"docid": "DOCID", "sheet_id": "SHEETID"}'
```

### smartsheet_add_fields

向子表添加一个或多个字段。单个子表最多 150 个字段。

```bash
wecom-cli doc smartsheet_add_fields '{"docid": "DOCID", "sheet_id": "SHEETID", "fields": [{"field_title": "任务名称", "field_type": "FIELD_TYPE_TEXT"}]}'
```

支持的字段类型参见 [字段类型参考](wecom-doc-smartsheet-field-types.md)。

### smartsheet_update_fields

更新字段标题。**只能改名，不能改类型**（field_type 必须传原始类型）。field_title 不能更新为原值。

```bash
wecom-cli doc smartsheet_update_fields '{"docid": "DOCID", "sheet_id": "SHEETID", "fields": [{"field_id": "FIELDID", "field_title": "新标题", "field_type": "FIELD_TYPE_TEXT"}]}'
```

### smartsheet_delete_fields

删除一列或多列字段，**操作不可逆**。field_id 可通过 `smartsheet_get_fields` 获取。

```bash
wecom-cli doc smartsheet_delete_fields '{"docid": "DOCID", "sheet_id": "SHEETID", "field_ids": ["FIELDID"]}'
```

---

## 四、智能表格数据管理

### smartsheet_get_records

查询子表全部记录。

- 通过 docid：
```bash
wecom-cli doc smartsheet_get_records '{"docid": "DOCID", "sheet_id": "SHEETID"}'
```
- 或通过 URL：
```bash
wecom-cli doc smartsheet_get_records '{"url": "https://doc.weixin.qq.com/smartsheet/xxx", "sheet_id": "SHEETID"}'
```

参见 [API 详情](wecom-doc-smartsheet-get-records.md)。

### smartsheet_add_records 添加一行或多行记录(不带图片或文件)

添加一行或多行记录，单次建议 500 行内。

**调用前**必须先了解目标表的字段类型（通过 `smartsheet_get_fields`），重点关注 `field_type`。对于单选/多选（Option）字段，需注意匹配已有选项的 `id`。

```bash
wecom-cli doc smartsheet_add_records '{"docid": "DOCID", "sheet_id": "SHEETID", "records": [{"values": {"任务名称": [{"type": "text", "text": "完成需求文档"}], "优先级": [{"text": "高"}]}}]}'
```

各字段类型的值格式参见 [单元格值格式参考](wecom-doc-smartsheet-cell-value-formats.md)。

> ⚠️ 若返回 `errcode: 851003` 或 `errmsg` 包含 `no authority`（通常是企业可见范围 > 10 人的规模限制），切换到 Webhook 兜底方案，详见 [wecom-doc-smartsheet-webhook.md](wecom-doc-smartsheet-webhook.md)。

## +smartsheet_add_records_auto_file 添加一行或多行记录(带图片或文件)

添加一行或多行记录，单次建议 500 行内。与 `smartsheet_add_records` 不同之处在于，可支持本地路径传入图片、文件。对于需要添加带图片或文件的记录，请使用此接口。传入后台后，后台将自动存储并转换为image_url。

```bash
wecom-cli doc +smartsheet_add_records_auto_file '{"docid":"DOCID","sheet_id":"SHEETID","records":[{"values":{"图片":[{"image_path":"/path/to/image.jpg"}],"文件":[{"file_path":"/path/to/file.txt"}]}}]}'
```

### smartsheet_update_records 更新记录(不带图片或文件)

更新一行或多行记录，单次建议在 500 行内。需提供 record_id（通过 `smartsheet_get_records` 获取）。支持通过 `key_type` 指定 values 的 key 使用字段标题或字段 ID：

- `CELL_VALUE_KEY_TYPE_FIELD_TITLE`：key 为字段标题
- `CELL_VALUE_KEY_TYPE_FIELD_ID`：key 为字段 ID

```bash
wecom-cli doc smartsheet_update_records '{"docid": "DOCID", "sheet_id": "SHEETID", "key_type": "CELL_VALUE_KEY_TYPE_FIELD_TITLE", "records": [{"record_id": "RECORDID", "values": {"任务名称": [{"type": "text", "text": "更新后的内容"}]}}]}'
```

**注意**：创建时间、最后编辑时间、创建人、最后编辑人字段不可更新。

> ⚠️ 若返回 `errcode: 851003` 或 `errmsg` 包含 `no authority`（通常是企业可见范围 > 10 人的规模限制），切换到 Webhook 兜底方案，详见 [wecom-doc-smartsheet-webhook.md](wecom-doc-smartsheet-webhook.md)。注意 Webhook 只能更新通过 Webhook 写入的记录，人工创建的记录无法更新。

### +smartsheet_update_records_auto_file 更新记录(更新图片或文件字段)
更新一行或多行记录，单次建议在 500 行内。与 `smartsheet_update_records` 不同之处在于，可支持本地路径传入图片、文件。对于需要更新记录中的图片或文件，请使用此接口。传入后台后，后台将自动存储并转换为image_url。

```bash
wecom-cli doc +smartsheet_update_records_auto_file '{"docid": "DOCID", "sheet_id": "SHEETID", "key_type": "CELL_VALUE_KEY_TYPE_FIELD_TITLE", "records": [{"record_id": "RECORDID", "values": {"values":{"图片":[{"image_path":"/path/to/image.jpg"}],"文件":[{"file_path":"/path/to/file.txt"}]}}}]}'
```

### smartsheet_delete_records

删除一行或多行记录，单次必须在 500 行内。**操作不可逆**。record_id 通过 `smartsheet_get_records` 获取。

```bash
wecom-cli doc smartsheet_delete_records '{"docid": "DOCID", "sheet_id": "SHEETID", "record_ids": ["RECORDID1", "RECORDID2"]}'
```

---

## 典型工作流

> **关键提示**：读取内容前先看 URL 判断品类。`/doc/`、`/sheet/`、`/smartsheet/` → `get_doc_content`；`/smartpage/` → `smartpage_export_task`。只有用户明确提到「智能文档」或「智能主页」时才走 smartpage 流程，其他文档场景一律使用企微文档接口。

### 文档操作

1. **读取文档 / 表格 / 智能表格** → 
```bash
wecom-cli doc get_doc_content '{"docid": "DOCID", "type": 2}'
```
   或通过 URL（`/doc/*`、`/sheet/*`、`/smartsheet/*` 均适用）：
```bash
wecom-cli doc get_doc_content '{"url": "https://doc.weixin.qq.com/sheet/xxx", "type": 2}'
```
   若 `task_done` 为 false 则携带 `task_id` 继续轮询
2. **创建新文档** → 
```bash
wecom-cli doc create_doc '{"doc_type": 3, "doc_name": "文档名"}'
```
，保存返回的 docid
3. **编辑文档** → 先 get_doc_content 了解当前内容，再 edit_doc_content 覆写

### 智能文档操作

1. **创建智能文档**（仅当用户明确要求「智能文档」或「智能主页」时，⚠️ 命令必须带 `+` 前缀，不可省略） → 
```bash
wecom-cli doc +smartpage_create '{"title": "标题", "pages": [{"page_title": "子页面", "content_type": 1, "page_filepath": "/path/to/file.md"}]}'
```
，保存返回的 docid
2. **获取智能文档内容**（URL 含 `/smartpage/`，异步两步）：
   - **第一步**：发起导出任务 →
```bash
wecom-cli doc smartpage_export_task '{"docid": "DOCID", "content_type": 1}'
```
，获取 `task_id`
   - **第二步**：轮询导出结果 →
```bash
wecom-cli doc smartpage_get_export_result '{"task_id": "TASK_ID"}'
```
，若 `task_done` 为 `false` 则继续轮询，直到 `task_done` 为 `true`，返回的 `content` 字段即为 Markdown 内容

### 智能表格结构操作

1. **了解表结构** → 
```bash
wecom-cli doc smartsheet_get_sheet '{"docid": "DOCID"}'
```
 →
```bash
wecom-cli doc smartsheet_get_fields '{"docid": "DOCID", "sheet_id": "SHEETID"}'
```
2. **创建表结构** → `smartsheet_add_sheet` 添加子表 → `smartsheet_add_fields` 定义列
3. **修改表结构** → `smartsheet_update_fields` 改列名 / `smartsheet_delete_fields` 删列

### 智能表格数据操作

1. **读取数据** → 
```bash
wecom-cli doc smartsheet_get_records '{"docid":"DOCID","sheet_id":"SHEETID"}'
```
2. **写入数据** → 先 `smartsheet_get_fields` 了解列类型 → 若涉及成员（USER）字段，先通过通讯录的 `get_userlist` 查找人员 userid（参见 [wecom-contact.md](wecom-contact.md)） → `smartsheet_add_records` 写入
3. **更新数据** → 先 `smartsheet_get_records` 获取 record_id → 若涉及成员（USER）字段，先通过通讯录的 `get_userlist` 查找人员 userid → `smartsheet_update_records` 更新
4. **删除数据** → 先 `smartsheet_get_records` 确认 record_id → `smartsheet_delete_records` 删除
5. **写入失败 fallback** → 第 2/3 步返回 `errcode: 851003` / `no authority`（通常是企业可见范围 > 10 人的规模限制）时 → 请用户临时提供目标表的 Webhook 地址 + schema 示例 JSON（不保存到本地）→ 按 [wecom-doc-smartsheet-webhook.md](wecom-doc-smartsheet-webhook.md) 构造请求体发送

> **注意**：成员（USER）类型字段需要填写 `user_id`，不能直接使用姓名。必须先通过通讯录的 `get_userlist` 接口按姓名查找到对应的 `userid` 后再使用。
