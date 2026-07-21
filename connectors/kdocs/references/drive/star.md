# 七、收藏

## 1. list_star_items

#### 功能说明

获取当前用户的收藏（星标）列表，支持分页和排序。



#### 调用示例

获取收藏列表：

```json
{
  "page_size": 20
}
```


#### 参数说明

- `page_size` (integer, 必填): 每页条数；建议 20；范围 1–500
- `page_token` (string, 可选): 分页 token，首次不传，后续传上次返回的 `next_page_token`
- `order` (string, 可选): 排序方向。可选值：`desc` / `asc`
- `order_by` (string, 可选): 排序字段，如 `ctime` / `mtime` / `rank`
- `include_exts` (string, 可选): 包含的文件后缀，逗号分隔，如 `docx,xlsx`
- `exclude_exts` (string, 可选): 排除的文件后缀，逗号分隔
- `with_permission` (boolean, 可选): 是否返回文件操作权限信息
- `with_link` (boolean, 可选): 是否返回文件分享信息

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
| `data.items` | array[FileInfo] | 收藏文件列表，结构见附录 A |
| `data.next_page_token` | string | 下一页 token，为空表示已是最后一页 |


---

## 2. batch_create_star_items

#### 功能说明

批量添加收藏


**幂等性**：是

#### 调用示例

批量添加收藏：

```json
{
  "objects": [
    {
      "id": "file_id_1",
      "type": "file"
    },
    {
      "id": "file_id_2",
      "type": "file"
    }
  ]
}
```


#### 参数说明

- `objects` (array[object], 必填): 要收藏的文件对象列表，每项含 id 和 type
  - `id` (string, 必填): 文件 ID
  - `type` (string, 必填): 类型，取值 `file` / `drive`

#### 返回值说明

```json
{
  "code": 0,
  "msg": "ok"
}

```


---

## 3. batch_delete_star_items

#### 功能说明

批量移除收藏（取消星标）。



**幂等性**：是

#### 调用示例

批量移除收藏：

```json
{
  "objects": [
    {
      "id": "file_id_1",
      "type": "file"
    }
  ]
}
```


#### 参数说明

- `objects` (array[object], 必填): 要移除收藏的文件对象列表，每项含 id 和 type
  - `id` (string, 必填): 文件 ID
  - `type` (string, 必填): 类型，取值 `file` / `drive`

#### 返回值说明

```json
{
  "code": 0,
  "msg": "ok"
}

```


---

