# wps.tocs.data

#### 功能说明

按文档插入目录

> 须先 insert 目录再 query/update/delete；无目录时 query 报 tableOfContents not found。
> insert 需传 upper_level/lower_level 正整数，缺失报 upper_level must be a positive integer。
> insert 前先查 wps.tocs.count：已有目录（count>0）时应先用 wps.tocs.data verb=delete 删除旧目录再插入，否则会叠加多个目录（TC_119/TC_055）。
> 空标题段（无文字的标题样式段落）会被静默跳过，不报错；生成的目录条目数以实际有文字的标题为准（TC_121）。

#### 调用示例

文档插入：

```json
{
  "file_id": "<FILE_ID>",
  "lower_level": 1,
  "scope": "documents",
  "upper_level": 1,
  "verb": "insert"
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `scope` (string, 必填): 操作范围，固定为 documents（按文档设置）。可选值：`documents`
- `verb` (string, 必填): 操作类型，固定为 insert（插入）。可选值：`insert`
- `lower_level` (number, 可选): 结束标题级别
- `upper_level` (number, 可选): 起始标题级别

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "toc_index": 1
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 0 表示成功 |
| `data` | object | 业务数据 |
| `message` | string | 结果说明 |

