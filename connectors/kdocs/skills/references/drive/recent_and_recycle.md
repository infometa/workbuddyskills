# 八、最近与回收站

## 1. list_latest_items

#### 功能说明

获取当前用户最近访问的文档列表，支持分页、过滤和排序。

#### 调用示例

获取最近访问列表：

```json
{
  "page_size": 20
}
```

#### 参数说明

- `page_size` (integer, 必填): 每页条数；建议 20；范围 1–500
- `page_token` (string, 可选): 分页 token
- `include_exts` (string, 可选): 包含的文件后缀，逗号分隔
- `exclude_exts` (string, 可选): 排除的文件后缀，逗号分隔
- `include_creators` (string, 可选): 包含的创建者 ID，逗号分隔
- `exclude_creators` (string, 可选): 排除的创建者 ID，逗号分隔
- `with_permission` (boolean, 可选): 是否返回权限信息
- `with_link` (boolean, 可选): 是否返回分享信息

#### 返回值说明

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "items": [
      {
        "id": "string",
        "name": "string",
        "type": "file",
        "drive_id": "string",
        "mtime": 0
      }
    ],
    "next_page_token": "string"
  }
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.items` | array[FileInfo] | 最近访问文件列表，结构见附录 A |
| `data.next_page_token` | string | 下一页 token，为空表示已是最后一页 |


---

## 2. list_deleted_files

#### 功能说明

获取回收站文件列表，支持分页和按云盘过滤。

> 返回的 `items[].id` 用于 `restore_deleted_file` 的 `file_id`，勿与 `get_file_info` 的 id 混用

#### 调用示例

列出回收站文件：

```json
{
  "page_size": 20
}
```

#### 参数说明

- `page_size` (integer, 必填): 每页条数；建议 20；范围 1–100
- `page_token` (string, 可选): 分页 token
- `drive_id` (string, 可选): 按云盘过滤
- `with_ext_attrs` (boolean, 可选): 是否返回扩展属性
- `with_drive` (boolean, 可选): 是否返回所属云盘信息

#### 返回值说明

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "items": [
      {
        "id": "string",
        "name": "string",
        "type": "file",
        "drive_id": "string",
        "parent_id": "string",
        "ctime": 0,
        "mtime": 0
      }
    ],
    "next_page_token": "string"
  }
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.items` | array[FileInfo] | 回收站文件列表，结构见附录 A |
| `data.next_page_token` | string | 下一页 token，为空表示已是最后一页 |


---

## 3. restore_deleted_file

#### 功能说明

将回收站中的文件还原到删除前的位置。须先调用 `list_deleted_files` 获取待恢复文件的 `id`。

#### 调用约束

- **前置检查**：file_id 须来自 list_deleted_files 的 items[].id；勿用 get_file_info / url / link_id

**幂等性**：是

> 标准流程：`list_deleted_files` → 向用户确认目标文件 → `restore_deleted_file(file_id=items[].id)`
> 批量恢复时逐个调用本工具

#### 调用示例

还原回收站文件：

```json
{
  "file_id": "string"
}
```

#### 参数说明

- `file_id` (string, 必填): 回收站文件 ID，取自 `list_deleted_files` 返回的 `items[].id`

`file_id` 必须来自 `list_deleted_files` 响应的 `items[].id`。
回收站文件不在普通文件索引中，勿使用 `url`、`link_id` 或 `get_file_info` 得到的 id。

#### 返回值说明

```json
{
  "code": 0,
  "msg": "ok"
}

```
