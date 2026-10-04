# wps.lists.data

#### 功能说明

按段落设置列表属性

> paragraph_index 为 1-based；可由 wps.texts.range（段落 → begin/end）或 wps.texts.search 定位后换算。

#### 调用示例

段落设置：

```json
{
  "file_id": "<FILE_ID>",
  "scope": "paragraphs",
  "verb": "update",
  "gallery_type": "smoke",
  "is_continue": true,
  "level": 1,
  "paragraph_index": 1,
  "template_index": 1
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一
- `scope` (string, 必填): 操作范围，固定为 paragraphs（按段落设置）。可选值：`paragraphs`
- `verb` (string, 必填): 动作，固定为 update（设置）。可选值：`update`
- `gallery_type` (string, 可选): 列表库：1/bullet/WD_BULLET_GALLERY 无序，2/number/WD_NUMBER_GALLERY 编号，3/outline/WD_OUTLINE_NUMBER_GALLERY 大纲。缺省 1。下游只认数字枚举
- `is_continue` (boolean, 可选): 是否继续前一列表
- `level` (number, 可选): 列表级别 1-9，缺省 1
- `paragraph_index` (number, 可选): 段落索引，从 1 起
- `template_index` (number, 可选): 库内模板索引，从 1 起，缺省 1

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {}
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 0 表示成功 |
| `data` | object | 业务数据 |
| `message` | string | 结果说明 |

