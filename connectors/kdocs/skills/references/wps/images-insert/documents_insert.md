# wps.images.insert

#### 功能说明

按文档插入图片（file_path 为图片 URL）

> 图片尺寸/位置按 0.75 磅栅格吸附：写入的宽高会被内核取整到 0.75 磅的整数倍，读回值与写入值允许 ±0.75 磅偏差。
> 未传 width/height 时按图片原始纵横比自动派生尺寸（四舍五入取整，单位磅）；需精确尺寸请显式传 width/height。

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一
- `scope` (string, 必填): 操作范围，固定为 documents（按文档设置）。可选值：`documents`
- `file_path` (string, 必填): 图片在线 URL，不能传本地路径。先 upload_attachment 上传到本文档，再用 download_attachment 取 download_url 传入
- `height` (number, 可选): 高度
- `width` (number, 可选): 宽度

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "index": 1,
    "width": 1,
    "height": 1,
    "count": 1
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 0 表示成功 |
| `data` | object | 业务数据 |
| `message` | string | 结果说明 |

