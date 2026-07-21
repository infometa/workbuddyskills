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

将回收站文件还原到原位置


**幂等性**：是

#### 调用示例

还原回收站文件：

```json
{
  "file_id": "string"
}
```


#### 参数说明

- `file_id` (string, 必填): 回收站中的文件 ID（由 `list_deleted_files` 返回）

#### 返回值说明

```json
{
  "code": 0,
  "msg": "ok"
}

```


---

