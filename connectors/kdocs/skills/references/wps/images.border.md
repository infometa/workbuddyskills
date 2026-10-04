# wps.images.border

## 1. wps.images.border

#### 功能说明

设置在线文字文档图片的边框。

**幂等性**：是 — safe

> index 是图片在文档中的当前序号（从 1 起），插入/删除图片后序号会变化；操作前先调 wps.images.list 获取最新 index，勿沿用旧序号。
> 时序约束：images.wrap 改环绕方式会把内联图转为浮动形状并可能重置边框；边框应在 wrap 之后设置，浮动图（shapes 域）可用 wps.shapes.line_width/line_color/line_dash 设置边框。

#### 参数说明

- `color` (number, 可选): 边框颜色
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `index` (number, 必填): 索引，从 1 开始
- `line_style` (number, 可选): 边框线型
- `line_width` (number, 可选): 线宽
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
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
