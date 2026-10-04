# wps.shapes.align

## 1. wps.shapes.align

#### 功能说明

设置在线文字文档形状的对齐。

**幂等性**：是 — safe

> group/align/distribute 需至少 2 个形状；shape_names 来自 wps.shapes.list。
> 对设置了相对定位（relative_to）或跟随文字列的锚定形状，align 可能不生效（返回 code=0 但位置不变，TC_091）；此时改用 wps.shapes.props 直接设置 Left/Top 兜底，并用 wps.shapes.list 读回核验。

#### 调用示例

文档设置：

```json
{
  "file_id": "<FILE_ID>",
  "align_cmd": 1,
  "relative_to_page": false,
  "shape_names": [
    "Rectangle 1",
    "Rectangle 2"
  ]
}
```

#### 参数说明

- `align_cmd` (number, 可选): 对齐命令（以实现为准）：0=左对齐、1=水平居中、2=右对齐、3=顶端对齐、4=垂直居中、5=底端对齐、6=横向分布、7=纵向分布。
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `relative_to_page` (boolean, 可选): relative to page
- `shape_names` (array, 可选): shape names
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
