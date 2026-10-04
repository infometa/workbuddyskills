# wps.images.insert

#### 功能说明

按段落插入图片（file_path 为图片 URL）

> paragraph_index 为 1-based；可由 wps.texts.range（段落 → begin/end）或 wps.texts.search 定位后换算。
> 段落/区间插入的新图 index 在 apis-pb 增字段前无法直接回传，需定位时用 wps.images.list 或改用 scope=documents（响应带 index）。
> 未传 width/height 时按图片原始纵横比自动派生尺寸（四舍五入取整，单位磅）；需精确尺寸请显式传 width/height。

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一
- `scope` (string, 必填): 操作范围，固定为 paragraphs（按段落设置）。可选值：`paragraphs`
- `file_path` (string, 必填): 图片在线 URL，不能传本地路径。先 upload_attachment 上传到本文档，再用 download_attachment 取 download_url 传入
- `height` (number, 可选): 高度
- `paragraph_index` (number, 可选): 段落序号（scope=paragraphs 时必填，从 1 起）
- `position` (string, 可选): 插入位置：before/after
- `width` (number, 可选): 宽度

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "width": 120,
    "height": 80,
    "paragraph_index": 2
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 0 表示成功 |
| `data` | object | 业务数据 |
| `message` | string | 结果说明 |

