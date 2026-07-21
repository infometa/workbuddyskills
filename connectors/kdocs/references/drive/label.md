# 六、标签

## 1. list_labels

#### 功能说明

分页获取云盘自定义标签列表。可按被分配者类型/ID、标签类型筛选。



#### 调用示例

基础分页：

```json
{
  "page_size": 50
}
```

按被分配者筛选：

```json
{
  "page_size": 50,
  "allotee_type": "user",
  "allotee_id": "238896429"
}
```


#### 参数说明

- `page_size` (integer, 必填): 每页条数；建议 50；范围 0–500（含 0）
- `page_token` (string, 可选): 分页 token，首次不传，后续传上次返回的 `next_page_token`
- `allotee_type` (string, 可选): 被分配者类型。可选值：`user` / `company`
- `allotee_id` (string, 可选): 被分配者 ID，与 `allotee_type` 配合使用
- `label_type` (string, 可选): 标签类型，如 `custom`

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
        "label_type": "custom",
        "allotee_type": "user",
        "allotee_id": "string",
        "ctime": 0,
        "mtime": 0,
        "hash": 0,
        "rank": 0
      }
    ],
    "next_page_token": "string"
  }
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.items` | array | 标签列表 |
| `data.items[].id` | string | 标签 ID |
| `data.items[].name` | string | 标签名称 |
| `data.items[].label_type` | string | 标签类型，如 `custom` |
| `data.items[].allotee_type` | string | 被分配者类型：`user` / `company` |
| `data.items[].allotee_id` | string | 被分配者 ID |
| `data.items[].ctime` | integer | 创建时间（时间戳，秒） |
| `data.items[].mtime` | integer | 修改时间（时间戳，秒） |
| `data.items[].hash` | integer | 标签内容哈希值 |
| `data.items[].rank` | integer | 排序权重 |
| `data.next_page_token` | string | 下一页 token，为空表示已是最后一页 |


---

## 2. create_label

#### 功能说明

创建自定义标签。



**幂等性**：否 — 重复调用可能创建同名标签，先确认是否已成功

#### 调用示例

创建用户标签：

```json
{
  "allotee_type": "user",
  "name": "我的项目"
}
```


#### 参数说明

- `allotee_type` (string, 必填): 归属者类型。可选值：`user` / `group` / `app`；默认值：`user`
- `name` (string, 必填): 标签名称，最多 240 字符
- `allotee_id` (string, 可选): 归属者 ID
- `label_type` (string, 可选): 标签类型。可选值：`custom` / `system`；默认值：`custom`
- `attr` (string, 可选): 自定义属性，最多 127 字符
- `rank` (number, 可选): 排序值，默认为创建时间戳（纳秒），建议使用默认值

#### 返回值说明

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "label": {
      "id": "string",
      "name": "我的项目",
      "label_type": "custom",
      "allotee_type": "user",
      "allotee_id": "string",
      "ctime": 1710000000,
      "mtime": 1710000000,
      "hash": "string",
      "rank": 0
    }
  }
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.label` | object | 新创建的标签信息 |
| `data.label.id` | string | 新标签 ID |
| `data.label.name` | string | 标签名称 |
| `data.label.label_type` | string | 标签类型 |
| `data.label.ctime` | integer | 创建时间（时间戳，秒） |
| `data.label.rank` | integer | 排序权重 |


---

## 3. get_label_meta

#### 功能说明

获取单个标签的详细信息。支持系统标签（固定 ID）和自定义标签。



#### 调用示例

查询系统星标标签：

```json
{
  "label_id": "1"
}
```


#### 参数说明

- `label_id` (string, 必填): 标签 ID。公网系统标签固定 ID：`1`（星标）/ `2`（待办）/ `3`（未确认协作）/ `4`（同步文件夹）/ `5`（常用）/ `6`（快速访问）

#### 返回值说明

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "id": "string",
    "name": "string",
    "label_type": "custom",
    "allotee_type": "user",
    "allotee_id": "string",
    "ctime": 0,
    "mtime": 0,
    "hash": 0,
    "rank": 0
  }
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.id` | string | 标签 ID |
| `data.name` | string | 标签名称 |
| `data.label_type` | string | 标签类型：`system`（系统标签）/ `custom`（自定义标签） |
| `data.allotee_type` | string | 被分配者类型：`user` / `company` |
| `data.allotee_id` | string | 被分配者 ID |
| `data.ctime` | integer | 创建时间（时间戳，秒），系统标签为 0 |
| `data.mtime` | integer | 修改时间（时间戳，秒），系统标签为 0 |
| `data.hash` | integer | 标签内容哈希值 |
| `data.rank` | integer | 排序权重，系统标签为 0 |


---

## 4. get_label_objects

#### 功能说明

获取指定标签下的所有对象。通过 `label_id` 查询该标签下打了标记的文件、云盘等对象列表。



#### 调用示例

自定义标签下的文件：

```json
{
  "label_id": "379727",
  "object_type": "file",
  "page_size": 50
}
```

查询系统标签"星标"下的文件：

```json
{
  "label_id": "1",
  "object_type": "file",
  "page_size": 50
}
```


#### 参数说明

- `label_id` (string, 必填): 标签 ID。公网系统标签固定 ID：`1`（星标）/ `2`（待办）/ `3`（未确认协作）/ `4`（同步文件夹）/ `5`（常用）/ `6`（快速访问）；可通过 `list_labels` 查询自定义标签 ID
- `object_type` (string, 必填): 标签对象类型。可选值：`file` / `drive` / `history` / `app` / `url`
- `page_size` (integer, 必填): 每页条数，建议 50；传 0 表示按 50；范围 0–500（含 0）
- `page_token` (string, 可选): 分页 token，首次不传，后续传上次返回的 `next_page_token`

#### 返回值说明

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "items": [
      {
        "object_id": "string",
        "object_type": "file",
        "label_id": "string",
        "ctime": 0
      }
    ],
    "next_page_token": "string"
  }
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.items` | array | 标签对象列表 |
| `data.items[].object_id` | string | 对象 ID（如文件 ID） |
| `data.items[].object_type` | string | 对象类型：`file` / `drive` 等 |
| `data.items[].label_id` | string | 标签 ID |
| `data.items[].ctime` | integer | 打标时间（时间戳，秒） |
| `data.next_page_token` | string | 下一页 token，为空表示已是最后一页 |


---

## 5. batch_add_label_objects

#### 功能说明

批量对文档对象添加指定标签（打标签）。可一次为多个文件打上同一标签。



**幂等性**：是

#### 调用示例

批量打标签：

```json
{
  "label_id": "379727",
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

- `label_id` (string, 必填): 标签 ID
- `objects` (array[object], 必填): 要打标签的文件对象列表，每项含 id 和 type
  - `id` (string, 必填): 文件 ID
  - `type` (string, 必填): 对象类型，可选值：`file` / `drive` / `history` / `app` / `url`

#### 返回值说明

```json
{
  "code": 0,
  "msg": "ok"
}

```


---

## 6. batch_remove_label_objects

#### 功能说明

批量移除对象与标签的关联。



**幂等性**：是

#### 调用示例

批量取消标签：

```json
{
  "label_id": "379727",
  "objects": [
    {
      "id": "file_id_1",
      "type": "file"
    }
  ]
}
```


#### 参数说明

- `label_id` (string, 必填): 标签 ID
- `objects` (array[object], 必填): 要取消标签的文件对象列表，每项含 id 和 type
  - `id` (string, 必填): 文件 ID
  - `type` (string, 必填): 对象类型，可选值：`file` / `drive` / `history` / `app` / `url`

#### 返回值说明

```json
{
  "code": 0,
  "msg": "ok"
}

```


---

## 7. batch_update_label_objects

#### 功能说明

批量更新标签下对象的排序或自定义属性。



**幂等性**：是

#### 调用示例

更新对象属性：

```json
{
  "label_id": "379727",
  "objects": [
    {
      "id": "file_id_1",
      "type": "file",
      "attr": "重要"
    }
  ]
}
```


#### 参数说明

- `label_id` (string, 必填): 标签 ID
- `objects` (array[object], 必填): 要更新的文件对象列表，每项含 id 和 type，可选 attr
  - `id` (string, 必填): 对象 ID
  - `type` (string, 必填): 对象类型，可选值：`file` / `drive` / `history` / `app` / `url`
  - `attr` (string, 可选): 扩展属性，最长 127 字符

#### 返回值说明

```json
{
  "code": 0,
  "msg": "ok"
}

```


---

## 8. batch_update_labels

#### 功能说明

批量修改自定义标签的名称或属性。**注意**：全局系统标签不可修改（星标-`1` / 待办-`2` / 未确认协作-`3` / 同步文件夹-`4` / 常用-`5` / 快速访问-`6`）。



**幂等性**：是

#### 调用示例

批量重命名与清空属性：

```json
{
  "labels": [
    {
      "id": "379727",
      "name": "Q2项目",
      "attr": ""
    },
    {
      "id": "379728",
      "name": "归档"
    }
  ]
}
```


#### 参数说明

- `labels` (array[object], 必填): 要更新的标签列表，每项含 id，可选 name 和 attr
  - `id` (string, 必填): 标签 ID
  - `name` (string, 可选): 新名称，最长 240 字符
  - `attr` (string, 可选): 对象自定义属性，最长 127 字符

#### 返回值说明

```json
{
  "code": 0,
  "msg": "ok"
}

```


---

