# 五、搜索

## 1. search_files

#### 功能说明

按关键词跨盘/跨目录搜索云文档，结果可包含文件与文件夹。
type 指定搜索维度（file_name / content / all）；file_type 只筛选 file / folder，不限制时省略；按文件格式筛选使用 file_exts（如 ["docx"]）。
支持按文件名、内容全文或全局检索（type 默认 all），并可按时间、创建者、后缀等条件过滤。
若只要文件夹或只要文件，请用 file_type；勿将 folder/file 填入 type。

#### 工具选择

- **适用**：按关键词/类型跨目录找文件时
- **勿用**（改用 `search_high_value_documents`）：用户用自然语言找文档，且条件包含时间、编辑/打开行为、常用程度、权限背景或宽泛主题
- **勿用**（改用 `list_files`）：已知目录、只需浏览子项时，不要用搜索代替目录遍历
- **勿用**（改用 `list_my_files`）：浏览我的云文档根目录

> 新建文件后搜索可能无法立即命中，需等待索引更新

#### 调用示例

按关键词搜索（type 默认 all，不限制文件或文件夹）：

```json
{
  "keyword": "区域周报告",
  "page_size": 20
}
```

按文件名搜索 Word 文件（格式放在 file_exts）：

```json
{
  "keyword": "项目报告",
  "type": "file_name",
  "file_type": "file",
  "file_exts": [
    "docx"
  ],
  "page_size": 10
}
```

按文件名搜索文件夹（资源类型放在 file_type）：

```json
{
  "keyword": "项目资料",
  "type": "file_name",
  "file_type": "folder",
  "page_size": 10
}
```

按文件名搜索：

```json
{
  "keyword": "区域周报告",
  "type": "file_name",
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
- `type` (string, 可选): 搜索维度，默认 all（全局搜索）。
file_name 仅搜文件名，content 仅搜文件内容，all 文件名+内容。
筛选文件夹/文件类型请用 file_type，勿将 folder/file 填入 type。
。可选值：`file_name` / `content` / `all`；默认值：`all`
- `page_size` (integer, 必填): 每页条数；建议 100；范围 0–500（含 0），传 0 表示按 50
- `page_token` (string, 可选): 翻页 token
- `file_type` (string, 可选): 资源类型筛选，不限制时省略；docx / xlsx 等文件格式使用 file_exts。可选值：`folder` / `file`
- `file_exts` (array, 可选): 按文件后缀筛选，使用字符串数组，如 ["docx"] 或 ["xlsx", "xls"]；不要把扩展名填入 type 或 file_type。
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

## 2. search_high_value_documents

#### 功能说明

你可以直接说想找什么文档，以及使用时间、编辑或打开情况等条件。
工具会在你有权限访问的文档中，优先列出与你的描述最匹配、近期常用或最近操作过的文档。
例如：“找我上周经常编辑的文件”“查一下我今天看过的文档”“找关于焦点事项的产品材料”。

#### 工具选择

- **适用**：用户直接描述想找的文档，例如“找我最近经常编辑的周报”或“查一下今天看过的文件”
- **适用**：用户希望优先看到最近用过、经常使用或与主题最相关的文档时
- **勿用**（改用 `search_files`）：用户知道明确的文件名、关键词或文件类型，并希望精确筛选或翻页查找
- **勿用**：已经找到文档，只需要读取、编辑或进行后续操作 — 这时可以直接使用已有文档信息，不必再次搜索。

**幂等性**：是

> total 可能小于 top_n，尤其是严格时间范围内没有足够候选时。

#### 调用示例

查找上周高频编辑的文件：

```json
{
  "query": "查找我上周高频编辑的文件",
  "top_n": 20
}
```

查找最近编辑的项目周报：

```json
{
  "query": "找我最近编辑过的项目周报"
}
```

查找宽泛主题的产品材料：

```json
{
  "query": "找关于焦点事项的产品材料",
  "top_n": 10
}
```

#### 参数说明

- `query` (string, 必填): 用日常语言描述你想找的文档和条件，最多 100 个字符。例如“找我最近编辑过的项目周报”或“查找今天看过的产品方案”。不要填写 file_id。
- `top_n` (integer, 可选): 最多返回多少个结果，范围 0–50；不填写或填写 0 时默认返回 20 个。

#### 返回值说明

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "items": [{"file_id": "file_xxx", "name": "项目周报", "link_url": "https://www.kdocs.cn/l/xxx", "type": "docx", "score": 0.96, "user_behavior_score": 0.88, "event_count": 12, "edit_count": 6, "open_count": 6, "last_op_time": 1730000000, "channels": ["title", "behavior", "semantic"], "rank_reason": "近期高频编辑且主题匹配", "relevance_level": "high", "evidence_priority": "behavior", "recall_fusion_score": 0.92}],
    "total": 1,
    "high_value_top_n": 1,
    "warning": "",
    "vip_used": true
  }
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.items` | array | 按匹配程度和近期使用情况排好顺序的文档列表；通常可直接使用，无需再次排序。 |
| `data.items[].file_id` | string | 文档的唯一标识，可用于后续读取或编辑。 |
| `data.items[].name` | string | 文档名称。 |
| `data.items[].link_url` | string | 文档链接。 |
| `data.items[].type` | string | 文档类型。 |
| `data.items[].permission` | object | 你对该文档可以进行哪些操作。 |
| `data.items[].creator` | object | 文档创建者信息。 |
| `data.items[].score` | number | 用于排列结果的匹配分数，请直接按返回顺序使用。 |
| `data.items[].user_behavior_score` | number | 你对该文档的使用程度。 |
| `data.items[].event_count` | integer | 你使用该文档的总次数。 |
| `data.items[].edit_count` | integer | 你编辑该文档的次数。 |
| `data.items[].open_count` | integer | 你打开该文档的次数。 |
| `data.items[].last_op_time` | integer | 你最近一次使用该文档的时间。 |
| `data.items[].channels` | array | 找到该文档的依据，例如标题、使用记录或内容主题。 |
| `data.items[].rank_reason` | string | 该文档排在前面的原因。 |
| `data.items[].relevance_level` | string | 该文档与你的描述有多匹配。 |
| `data.items[].evidence_priority` | string | 排序时优先参考的依据。 |
| `data.items[].recall_fusion_score` | number | 综合多个匹配依据得到的分数。 |
| `data.total` | integer | 实际返回的文档数量，可能少于你要求的数量。 |
| `data.high_value_top_n` | integer | 前面有多少个结果是根据近期使用情况和匹配程度筛选出来的。 |
| `data.warning` | string | 如果不为空，表示部分查找条件没有完全生效；通常仍可继续使用返回的文档列表。 |
| `data.vip_used` | boolean | 是否使用了更智能的内容理解来匹配文档。 |
