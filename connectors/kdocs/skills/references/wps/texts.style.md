# wps.texts.style

## 1. wps.texts.style

#### 功能说明

查询在线文字文档段落样式。

> 返回 style_info（段落样式信息）：style_name（样式名，如正文/标题1）、type/type_value（段落样式类型枚举）、built_in（是否内置样式）、outline_level（大纲级别：0=正文，1-9=标题级别）。
> 若 style_info 缺失或为空对象，说明该段落无有效样式数据（部分文档/复杂格式场景），并非调用错误；此时不要反复重试。

#### 调用示例

段落查询：

```json
{
  "file_id": "<FILE_ID>",
  "paragraph_index": 1
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id
- `paragraph_index` (number, 必填): 段落索引
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "style_info": {
      "paragraph_index": 1,
      "style_name": "正文",
      "type": "paragraph",
      "type_value": 1,
      "built_in": true,
      "outline_level": 10
    }
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 0 表示成功 |
| `data` | object | 业务数据 |
| `message` | string | 结果说明 |
