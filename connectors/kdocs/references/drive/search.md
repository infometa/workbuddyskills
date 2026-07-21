# 五、搜索

## 1. search_files

#### 功能说明

支持按文件名、内容全文搜索，可按时间、创建者、文件类型等条件过滤。


> 新建文件后搜索可能无法立即命中，需等待索引更新

#### 调用示例

搜索文档：

```json
{
  "keyword": "区域周报告",
  "type": "all",
  "file_type": "file",
  "parent_ids": [
    "string"
  ],
  "page_size": 20,
  "order": "desc",
  "order_by": "mtime",
  "with_total": true
}
```


#### 参数说明

- `keyword` (string, 可选): 搜索关键字
- `type` (string, 必填): 搜索类型。可选值：`file_name`表示搜索文件名，`content`表示搜索文件内容，`all`表示全局搜索。
- `page_size` (integer, 必填): 每页条数；建议 100；范围 0–500（含 0），传 0 表示按 50
- `page_token` (string, 可选): 翻页 token
- `file_type` (string, 可选): 文件类型筛选。可选值：`folder` / `file`
- `file_exts` (array, 可选): 文件后缀过滤
- `drive_ids` (array, 可选): 搜索云盘 ID列表
- `parent_ids` (array, 可选): 搜索目录列表
- `creator_ids` (array, 可选): 创建者 ID 列表。公网只支持选择是否自己创建的文件
- `modifier_ids` (array, 可选): 编辑者 ID 列表
- `sharer_ids` (array, 可选): 分享者 ID 列表
- `receiver_ids` (array, 可选): 接收者 ID 列表
- `time_type` (string, 可选): 时间范围类型。可选值：`ctime` / `mtime` / `otime` / `stime`
- `start_time` (integer, 可选): 最小时间
- `end_time` (integer, 可选): 最大时间
- `with_permission` (boolean, 可选): 是否返回文件操作权限
- `with_link` (boolean, 可选): 是否返回文件分享信息
- `with_total` (boolean, 可选): 是否返回搜索到的总条数
- `with_drive` (boolean, 可选): 是否返回云盘信息
- `order` (string, 可选): 排序方式。可选值：`desc` / `asc`
- `order_by` (string, 可选): 排序字段。可选值：`ctime` / `mtime`
- `scope` (array, 可选): 搜索范围。可选值：`all` / `share_by_me` / `share_to_me` / `latest` / `personal_drive` / `group_drive` / `recycle` / `customize` / `latest_opened` / `latest_edited`
- `channels` (array, 可选): 渠道信息
- `device_ids` (array, 可选): 设备 ID 列表
- `exclude_channels` (array, 可选): 排除渠道信息
- `exclude_file_exts` (array, 可选): 排除文件后缀
- `filter_user_id` (integer, 可选): 创建者分享者过滤
- `file_ext_groups` (array, 可选): 文件分组后缀
- `search_operator_name` (boolean, 可选): 是否搜索文件的创建者或分享者

#### 返回值说明

```json
{
  "data": {
    "items": [
      {
        "file": {
          "created_by": {
            "avatar": "string",
            "company_id": "string",
            "id": "string",
            "name": "string",
            "type": "user"
          },
          "ctime": 0,
          "drive_id": "string",
          "ext_attrs": [
            { "name": "string", "value": "string" }
          ],
          "id": "string",
          "link_id": "string",
          "link_url": "string",
          "modified_by": {
            "avatar": "string",
            "company_id": "string",
            "id": "string",
            "name": "string",
            "type": "user"
          },
          "mtime": 0,
          "name": "string",
          "parent_id": "string",
          "shared": true,
          "size": 0,
          "type": "folder",
          "version": 0
        },
        "file_src": {
          "name": "string",
          "path": "string",
          "type": "link"
        },
        "highlights": {
          "example_key": ["string"]
        },
        "otime": 0
      }
    ],
    "next_page_token": "string",
    "total": 0
  },
  "code": 0,
  "msg": "string"
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.items` | array | 搜索结果列表 |
| `data.items[].file` | object | 文件信息，通用文件信息结构（附录 A） |
| `data.items[].file_src` | object | 文件位置信息 |
| `data.items[].file_src.name` | string | 来源名称 |
| `data.items[].file_src.path` | string | 文件路径 |
| `data.items[].file_src.type` | string | 来源类型：`link` / `user_private` / `user_roaming` / `group_normal` / `group_dept` / `group_whole` |
| `data.items[].highlights` | map[string][]string | 匹配关键字 |
| `data.items[].otime` | integer | 文件打开时间 |
| `data.next_page_token` | string | 下一页 token |
| `data.total` | integer | 资源集合总数（仅 `with_total=true` 时返回） |


---

