# wps.watermarks.image

## 1. wps.watermarks.image

#### 功能说明

插入在线文字文档图片水印。

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id
- `file_path` (string, 必填): 图片在线 URL，不能传本地路径。先 upload_attachment 上传到本文档，再用 download_attachment 取 download_url 传入
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id
- `section_index` (number, 可选): 节索引
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
