# wps.watermarks.text_italic

## 1. wps.watermarks.text_italic

#### 功能说明

插入在线文字文档斜体文字水印。

**幂等性**：是 — safe

#### 调用示例

文档插入：

```json
{
  "file_id": "<FILE_ID>",
  "file_path": "https://www.wps.cn/favicon.ico",
  "section_index": 1,
  "text": "smoke example text"
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `file_path` (string, 可选): file path
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `section_index` (number, 可选): 节索引，从 1 开始
- `text` (string, 必填): 文本内容
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一

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
