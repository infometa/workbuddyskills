# 乐享智能表格

> **前置条件**：本skill 需要已配置乐享 MCP 连接。如未配置，请先读取 `references/setup.md`。
> **触发场景**：用户提到「智能表格」「乐享表格」「知识库里的表格」或需要对乐享中的结构化数据增删查改时使用。

---

## 工具概览

###📋 表格结构管理
- `smartsheet_create` — 用SQL DDL CREATE TABLE 创建智能表格
- `smartsheet_fetch` — 获取表格 schema、视图、摘要（不含行数据）
- `smartsheet_list` — 列出条目关联的智能表格摘要
- `smartsheet_list_smartsheets` — 列出条目下所有智能表格（获取 smartsheet_id）
- `smartsheet_update_schema` — 用 ALTER TABLE SQL DDL 修改表格 schema

### 📊 字段（列）管理
- `smartsheet_list_fields` — 列出所有字段及类型配置
- `smartsheet_create_field` — 新增字段（列）
- `smartsheet_update_field` — 更新字段名称或配置（如选项、日期格式）
- `smartsheet_delete_field` — 删除字段

### 👁️ 视图管理
- `smartsheet_list_views` — 列出所有视图
- `smartsheet_create_view` — 创建视图
- `smartsheet_update_view` — 更新视图
- `smartsheet_delete_view` — 删除视图

### 📝 记录（行）操作
- `smartsheet_list_records` — 分页获取记录，支持按视图筛选
- `smartsheet_describe_record` — 获取单条记录详情
- `smartsheet_create_records` — 批量创建记录（单次≤ 50 条）
- `smartsheet_update_records` — 批量更新记录（单次 ≤ 50 条，仅更新指定字段）
- `smartsheet_delete_records` — 批量删除记录（单次 ≤ 50 条）

---

## 标准工作流

### 1. 找到智能表格

从条目（页面）找到关联的智能表格：

```
Step 1: 获取 entry_id（从用户提供的链接或搜索）

Step 2: smartsheet_list_smartsheets(entry_id=<entry_id>)
  → 返回智能表格列表，取smartsheet_id

Step 3: smartsheet_fetch(entry_id, smartsheet_id)
  → 获取表格 schema（字段定义、视图列表）
```

### 2. 查询/读取数据

```
smartsheet_list_records(
  entry_id=<entry_id>,
  smartsheet_id=<smartsheet_id>,
  view_id=<可选，按视图筛选>
)
→ 分页返回记录列表
```

>如需获取字段 ID和字段名的映射关系，先调用 `smartsheet_list_fields`。

### 3. 新增数据

```
smartsheet_create_records(
  entry_id=<entry_id>,
  smartsheet_id=<smartsheet_id>,
  records=[
    { "fields": { "<field_id>": <CellValue>, ... } },
    ...
  ]
)
```

> `fields` 中的 key 为 `field_id`（通过 `smartsheet_list_fields` 获取），value 为对应类型的 CellValue。

### 4. 更新数据

```
smartsheet_update_records(
  entry_id=<entry_id>,
  smartsheet_id=<smartsheet_id>,
  records=[
    { "record_id": "<record_id>", "fields": { "<field_id>": <new_value> } },
    ...
  ]
)
```

> 仅更新指定字段，其他字段保持不变。

### 5. 删除数据

```
smartsheet_delete_records(
  entry_id=<entry_id>,
  smartsheet_id=<smartsheet_id>,
  record_ids=["<record_id1>", "<record_id2>", ...]
)
```

### 6. 创建新智能表格

```
smartsheet_create(
  entry_id=<entry_id>,
  ddl="CREATE TABLE 表名 (
    字段1 TEXT,
    字段2 NUMBER,
    字段3 SELECT OPTIONS ('选项A', '选项B')
  )"
)
```

> 使用 SQL DDL 语法定义表结构，支持 TEXT、NUMBER、DATE、SELECT 等常见类型。

### 7. 修改表结构

```
smartsheet_update_schema(
  entry_id=<entry_id>,
  smartsheet_id=<smartsheet_id>,
  ddl="ALTER TABLE 表名 ADD COLUMN 新字段 TEXT;
       ALTER TABLE 表名 MODIFY COLUMN 字段名 NUMBER;"
)
```

> 支持多条ALTER TABLE 语句。

---

## ⚠️ 核心注意事项

1. **所有记录操作都需要 `entry_id` + `smartsheet_id`**：`entry_id` 是知识条目 ID，`smartsheet_id` 是表格自身 ID，二者缺一不可
2. **先获取 smartsheet_id**：操作记录前务必先调用 `smartsheet_list_smartsheets` 获取 `smartsheet_id`
3. **field_id 而非字段名**：`create_records` / `update_records` 中 `fields` 的 key 是 `field_id`，需先调用 `smartsheet_list_fields` 获取
4. **批量限制**：create/update/delete 单次 ≤ 50 条，超出时分批执行
5. **`smartsheet_fetch` 不返回行数据**：行数据通过 `smartsheet_list_records` 获取
6. 参数不确定时以 `get_tool_schema(tool_name="xxx")` 返回为准
