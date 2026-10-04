# 三、文件组织

## 1. move_file

#### 功能说明

批量移动文件(夹)。大批量时可能异步，返回非空 `task_ids`。移入回收站不是移动语义；`file_ids` 跨盘时整批拒绝，请按源盘拆批。

#### 调用约束

- **前置检查**：确认目标文件夹存在（get_file_info）
- **用户确认**（批量操作（多个 file_ids））：批量移动需向用户确认文件列表和目标位置
- **后置验证**：get_file_info 确认 parent_id 为目标文件夹

**幂等性**：是

> `task_ids` 非空时，移动尚未完成，需后续确认

#### 调用示例

移动文件到目标文件夹（源盘自动反查）：

```json
{
  "file_ids": [
    "string"
  ],
  "dst_parent_id": "string"
}
```

移动到用户指定盘的根：

```json
{
  "file_ids": [
    "string"
  ],
  "dst_drive_id": "string",
  "dst_parent_id": "0"
}
```

#### 参数说明

- `drive_id` (string, 可选): 源文件所在云盘 ID。不传则按 file_ids 解析
- `file_ids` (array[string], 必填): 文件 ID 列表
- `dst_drive_id` (string, 可选): 目标云盘 ID。dst_parent_id 为 "0" 时必传；指向具体文件夹时可省略
- `dst_parent_id` (string, 必填): 目标父文件夹 ID。两种情况：目标是具体文件夹时传该文件夹 ID；目标是某盘根目录时传 "0"（须同时传 dst_drive_id）

#### 返回值说明

```json
{
  "data": {
    "task_ids": []
  },
  "code": 0,
  "message": "成功"
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.task_ids` | array[string] | 批量任务 ID 列表；单文件移动时通常为空数组 |


---

## 2. rename_file

#### 功能说明

重命名文件（夹）。仅修改文件名，不影响文档内部标题。⚠️ 若用户要改智能文档的「文档标题」，应使用 `otl.block_update`（title 块），而非本工具。

**`drive_id`**：源文件所在云盘 ID。不传则按 `file_id` 解析。

**幂等性**：是

#### 调用示例

重命名文件：

```json
{
  "drive_id": "string",
  "file_id": "string",
  "dst_name": "2024年Q1销售总结.otl"
}
```

file_id：

```json
{
  "file_id": "string",
  "dst_name": "2024年Q1销售总结.otl"
}
```

#### 参数说明

- `drive_id` (string, 可选): 源文件所在云盘 ID。不传则按 file_id 解析
- `file_id` (string, 必填): 文件（夹）ID
- `dst_name` (string, 必填): 新文件名，须带上后缀。例: `abc.txt`。支持格式：otl, doc, xls, ppt, pptx, wdoc, wxls, wppt, h5, pom, pof, docx, xlsx, ksheet, dbt, pdf

#### 返回值说明

返回通用文件信息结构，详见附录 A。

---

## 3. copy_file

#### 功能说明

复制文件到指定目录（可跨盘）。

**`drive_id`**（非必填）：源文件所在云盘 ID。不传则按 `file_id` 解析。

**幂等性**：否 — 重复调用会创建多个副本，先确认是否已成功

#### 调用示例

复制到目标目录：

```json
{
  "drive_id": "src_drive_id",
  "file_id": "file_id_1",
  "dst_drive_id": "dst_drive_id",
  "dst_parent_id": "dst_folder_id"
}
```

仅 file_id（不传 drive_id）：

```json
{
  "file_id": "file_id_1",
  "dst_drive_id": "dst_drive_id",
  "dst_parent_id": "dst_folder_id"
}
```

#### 参数说明

- `drive_id` (string, 可选): 源文件所在云盘 ID
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享链接 ID
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 ID
- `dst_drive_id` (string, 可选): 目标云盘 ID。dst_parent_id 为 "0" 时必传；指向具体文件夹时可省略
- `dst_parent_id` (string, 必填): 目标父目录 ID。两种情况：目标是具体文件夹时传该文件夹 ID；目标是某盘根目录时传 "0"（须同时传 dst_drive_id）

#### 返回值说明

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "id": "string",
    "name": "string",
    "type": "file",
    "drive_id": "string",
    "parent_id": "string"
  }
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.id` | string | 新文件 ID |
| `data.name` | string | 文件名 |
| `data.type` | string | 文件类型 |
| `data.drive_id` | string | 目标云盘 ID |
| `data.parent_id` | string | 目标父目录 ID |


---

## 4. check_file_name

#### 功能说明

检查文件名在指定目录下是否已存在。常用于上传、复制、移动等操作前的同名预检查。不接收 `parent_path`。

#### 工具选择

- **适用**：上传、复制、移动前检查目标目录是否已有同名
- **勿用**（改用 `create_empty_file`）：需要按路径创建空白文档 — 本工具不接收 parent_path
- **勿用**（改用 `upload_new_file`）：需要按路径上传文件 — 本工具不接收 parent_path

#### 调用示例

检查文件名是否占用：

```json
{
  "drive_id": "string",
  "parent_id": "string",
  "name": "Q1销售报告.docx"
}
```

#### 参数说明

- `drive_id` (string, 可选): 目标云盘 ID。不传则使用个人云盘
- `parent_id` (string, 可选): 父目录 ID，根目录为 "0"。"0" 是某个盘的根，不是个人盘根；不传则使用个人云盘根
- `name` (string, 必填): 待检查的文件名（含后缀）

#### 返回值说明

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "is_exist": true,
    "file_id": "string"
  }
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.is_exist` | boolean | 文件名是否已存在 |
| `data.file_id` | string | 若已存在，返回已有文件 ID |


---

## 5. save_as_file

#### 功能说明

将源文件复制到目标云盘目录，生成新文件；源文件保留不变。支持指定目标文件名及重名处理策略。

**`drive_id`**（非必填）：源文件所在云盘 ID。不传则按 `file_id` 解析。

与相关工具的区别：`copy_file` 不支持指定目标文件名；`move_file` 源位置不保留；`rename_file` 原地重命名。

**幂等性**：否 — 重复调用会创建多个副本，先确认是否已成功

> 团队文档库的 dst_drive_id 可先通过 list_doclibs 获取
> 成功后从 data.id 取新 file_id 供后续操作使用

#### 调用示例

另存为到同盘根目录，自动加后缀避免重名：

```json
{
  "drive_id": "src_drive_id",
  "file_id": "src_file_id",
  "dst_drive_id": "src_drive_id",
  "dst_parent_id": "0",
  "name": "副本.docx",
  "on_name_conflict": "rename"
}
```

另存为到团队文档库根目录（不指定文件名）：

```json
{
  "drive_id": "src_drive_id",
  "file_id": "src_file_id",
  "dst_drive_id": "team_drive_id",
  "dst_parent_id": "0"
}
```

#### 参数说明

- `drive_id` (string, 可选): 源文件所在云盘 ID
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享链接 ID
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 ID
- `dst_drive_id` (string, 可选): 目标云盘 ID。dst_parent_id 为 "0" 时必传；指向具体文件夹时可省略
- `dst_parent_id` (string, 必填): 目标父文件夹 ID。两种情况：目标是具体文件夹时传该文件夹 ID；目标是某盘根目录时传 "0"（须同时传 dst_drive_id）
- `name` (string, 可选): 目标文件名；建议含后缀（如 "副本.docx"）以避免与同名文件冲突
- `on_name_conflict` (string, 可选): 目标目录已有同名文件时的处理策略；默认 rename（自动加序号后缀），fail=报错中止（需明确不允许覆盖时用）。可选值：`fail` / `rename`

#### 返回值说明

```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "id": "new_file_id",
    "name": "副本.docx",
    "drive_id": "dst_drive_id",
    "parent_id": "0",
    "link_id": "link_id_xxx",
    "link_url": "https://www.kdocs.cn/l/xxx"
  }
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.id` | string | 新文件的 file_id |
| `data.name` | string | 新文件名称 |
| `data.drive_id` | string | 新文件所在云盘 ID |
| `data.parent_id` | string | 新文件父目录 ID |
| `data.link_id` | string | 分享 link_id（若有） |
| `data.link_url` | string | 文档打开链接（若有） |
