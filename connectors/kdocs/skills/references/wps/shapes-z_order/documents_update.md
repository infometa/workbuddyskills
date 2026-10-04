# wps.shapes.z_order

#### 功能说明

设置形状的叠放次序

**幂等性**：是 — safe

#### 调用示例

文档设置：

```json
{
  "file_id": "<FILE_ID>",
  "shape_item": "3",
  "zorder": "msoBringToFront"
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一
- `verb` (string, 必填): HTTP 动作：query（查询 ZOrderPosition）/ update（设置叠放次序）。可选值：`query` / `update`
- `shape_item` (string, 可选): shape item
- `zorder` (string, 可选): 叠放次序：msoBringToFront / msoSendToBack / msoBringForward / msoSendBackward。可选值：`msoBringToFront` / `msoSendToBack` / `msoBringForward` / `msoSendBackward`

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "info": {
      "index": 3,
      "name": "Rectangle 7",
      "type": 1
    }
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 0 表示成功 |
| `data` | object | 业务数据 |
| `message` | string | 结果说明 |

