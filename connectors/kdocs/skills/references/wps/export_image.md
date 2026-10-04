# wps.export_image

## 1. wps.export_image

#### 功能说明

将在线文字导出为 `png` 或 `jpeg` 图片。该接口走图片导出链路。

**幂等性**：否 — 导出为异步任务，用 task_id 轮询结果而非重复提交

#### 调用示例

导出为 PNG 长图：

```json
{
  "file_id": "023bf8fd81ab3d089b9d284a29d9b143",
  "format": "png",
  "dpi": 150,
  "from_page": 1,
  "to_page": 3,
  "combine_long_pic": true
}
```

#### 参数说明

- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `format` (string, 必填): 导出图片格式。可选值：`png` / `jpeg`
- `dpi` (number, 可选): 导出图片 DPI。可选值：`96` / `150` / `300`；默认值：`96`
- `water_mark` (boolean, 可选): 是否添加水印；默认值：`true`
- `from_page` (number, 可选): 起始页码；默认值：`1`
- `to_page` (number, 可选): 结束页码；默认值：`9999`
- `combine_long_pic` (boolean, 可选): 是否合并为长图；`false` 表示逐页；默认值：`true`
- `use_xva` (boolean, 可选): 是否启用 XVA 渲染
- `client_id` (string, 可选): 导出时可选的客户端标识
- `password` (string, 可选): 源文档密码
- `store_type` (string, 可选): 存储类型，如 `ks3`、`cloud`

#### 返回值说明

```json
{
  "code": 0,
  "data": {
    "url": "https://xxx.wps.cn/export/image.png",
    "file_id": "string"
  }
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.url` | string | 导出图片的下载地址 |
| `data.file_id` | string | 导出图片的文件 ID |
