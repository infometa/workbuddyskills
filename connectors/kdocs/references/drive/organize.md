# 三、文件组织

## 1. move_file

#### 功能说明

批量移动文件(夹)。大批量时可能异步，返回非空 `task_ids`。


#### 操作约束

- **前置检查**：确认目标文件夹存在（get_file_info）
- **用户确认**（批量操作（多个 file_ids））：批量移动需向用户确认文件列表和目标位置
- **后置验证**：get_file_info 确认 parent_id 为目标文件夹
- **提示**：`task_ids` 非空时，移动尚未完成，需后续确认

**幂等性**：是

#### 调用示例

移动文件到目标文件夹：

```json
{
  "drive_id": "string",
  "file_ids": [
    "string"
  ],
  "dst_drive_id": "string",
  "dst_parent_id": "string"
}
```


#### 参数说明

- `drive_id` (string, 必填): 云盘 ID
- `file_ids` (array[string], 必填): 文件 ID 列表
- `dst_drive_id` (string, 必填): 目标云盘 ID
- `dst_parent_id` (string, 必填): 目标文件夹 ID，根目录为 "0"

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

重命名文件（夹）。

**`drive_id`**（非必填）：

- **有明确的云盘ID** 必传。
- **没有**：不传。



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

- `drive_id` (string, 可选): 目标云盘 ID
- `file_id` (string, 必填): 文件（夹）ID
- `dst_name` (string, 必填): 新文件名，须带上后缀。例: `abc.txt`。支持格式：otl, doc, xls, ppt, pptx, wdoc, wxls, wppt, h5, pom, pof, docx, xlsx, ksheet, dbt, pdf

#### 返回值说明

返回通用文件信息结构，详见附录 A。

---

## 3. copy_file

#### 功能说明

复制文件到指定目录（可跨盘）。

**`drive_id`**（非必填）：

- **有明确的 drive_id** 必传。
- **没有**：不传。



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
- `file_id` (string, 必填): 源文件 ID
- `dst_drive_id` (string, 必填): 目标云盘 ID
- `dst_parent_id` (string, 必填): 目标父目录 ID，根目录为 "0"

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

检查文件名在指定目录下是否已存在。常用于上传、复制、移动等操作前的同名预检查。


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

- `drive_id` (string, 必填): 云盘 ID
- `parent_id` (string, 必填): 父目录 ID，根目录为 "0"
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

