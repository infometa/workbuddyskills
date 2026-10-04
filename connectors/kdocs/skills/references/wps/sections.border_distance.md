# wps.sections.border_distance

## 1. wps.sections.border_distance

#### 功能说明

设置在线文字文档节的页面边框距正文距离。

**幂等性**：是 — safe

#### 调用示例

文档设置：

```json
{
  "file_id": "<FILE_ID>",
  "border_distance_bottom": 1,
  "border_distance_from": 1,
  "border_distance_left": 1,
  "border_distance_right": 1,
  "border_distance_top": 1,
  "section_index": 1
}
```

#### 参数说明

- `border_distance_bottom` (number, 可选): border distance bottom
- `border_distance_from` (number, 可选): border distance from
- `border_distance_left` (number, 可选): border distance left
- `border_distance_right` (number, 可选): border distance right
- `border_distance_top` (number, 可选): border distance top
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `section_index` (number, 可选): 节索引，从 1 开始
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
