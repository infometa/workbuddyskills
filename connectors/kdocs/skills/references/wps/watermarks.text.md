# wps.watermarks.text

## 1. wps.watermarks.text

#### 功能说明

插入在线文字文档文本水印。

#### 调用示例

文档插入：

```json
{
  "file_id": "<FILE_ID>",
  "section_index": 1,
  "text": "smoke example text"
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id
- `section_index` (number, 可选): 节索引
- `text` (string, 必填): 水印文本
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL

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
