# wps.lists.data

#### 功能说明

按字符区间设置列表属性

> begin/end 为 0-based 字符区间；可由 wps.texts.search 返回的 ranges 回填。

#### 调用示例

字符区间设置：

```json
{
  "file_id": "<FILE_ID>",
  "scope": "ranges",
  "verb": "update",
  "begin": 1,
  "end": 12,
  "gallery_type": "smoke",
  "is_continue": true,
  "level": 1,
  "template_index": 1
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一
- `scope` (string, 必填): 操作范围，固定为 ranges（按字符区间设置）。可选值：`ranges`
- `verb` (string, 必填): 动作，固定为 update（设置）。可选值：`update`
- `begin` (number, 可选): 范围起点
- `end` (number, 可选): 范围终点
- `gallery_type` (string, 可选): 列表库：1/bullet/WD_BULLET_GALLERY 无序，2/number/WD_NUMBER_GALLERY 编号，3/outline/WD_OUTLINE_NUMBER_GALLERY 大纲。缺省 1。下游只认数字枚举
- `is_continue` (boolean, 可选): 是否继续前一列表
- `level` (number, 可选): 列表级别 1-9，缺省 1
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

