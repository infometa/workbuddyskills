# wps.header_footers.shape_alignment

## 1. wps.header_footers.shape_alignment

#### 功能说明

设置在线文字文档页眉页脚的形状对齐。

**幂等性**：是 — safe

#### 调用示例

文档设置：

```json
{
  "file_id": "<FILE_ID>",
  "alignment": "smoke",
  "value": "true"
}
```

#### 参数说明

- `alignment` (string, 可选): 形状左边距（与 left 二选一，兼容旧入参名；backend 模板 ${left}）
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `header_footer_type` (number, 可选): 1=页眉，2=页脚；缺省 1
- `left` (string, 可选): 形状左边距（backend 模板 ${left}；与 alignment 二选一，left 优先）
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `section_index` (number, 可选): 节索引，从 1 开始；不传处理全部节
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一
- `value` (string, 可选): 对齐方式（backend 模板 ${alignment}；PAGE 域文本框 ParagraphFormat.Alignment）

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
