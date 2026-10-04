# wps.images.insert

#### 功能说明

按字符区间插入图片（file_path 为图片 URL）

> begin/end 为 0-based 字符区间；可由 wps.texts.search 返回的 ranges 回填。
> 未传 width/height 时按图片原始纵横比自动派生尺寸（四舍五入取整，单位磅）；需精确尺寸请显式传 width/height。

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一
- `scope` (string, 必填): 操作范围，固定为 ranges（按字符区间设置）。可选值：`ranges`
- `begin` (number, 可选): 区间起点（scope=ranges 时必填）
- `end` (number, 可选): 区间终点（scope=ranges 时必填）
- `file_path` (string, 必填): 图片在线 URL，不能传本地路径。先 upload_attachment 上传到本文档，再用 download_attachment 取 download_url 传入
- `height` (number, 可选): 高度
- `width` (number, 可选): 宽度

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "width": 120,
    "height": 80
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 0 表示成功 |
| `data` | object | 业务数据 |
| `message` | string | 结果说明 |

