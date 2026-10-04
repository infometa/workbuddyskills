# wps.texts.format_copy

## 1. wps.texts.format_copy

#### 功能说明

将源段落格式复制到目标段落范围（格式刷）。搬运维度：字体（name/size/bold/italic/underline/color）、段落（alignment/lineSpacing）、底纹 shading、四边边框 borders（lineStyle/lineWidth/color）、高亮 highlight、缩放 scaling。含清语义：源无底纹/边框/高亮/缩放非 100 时清除目标对应属性。返回 data.props 列出实际生效维度，data.snapshot 为源段格式快照。

**幂等性**：是 — safe

> 写操作报 500002 且读操作正常时，先排查文档保护态（wps.protection.disable 后重试），再排查参数；不要盲目重试。

#### 调用示例

段落设置：

```json
{
  "file_id": "<FILE_ID>",
  "format_items": [
    {
      "key": "Bold",
      "value": "true"
    }
  ],
  "source_paragraph": 1,
  "target_end": 2,
  "target_start": 2
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `format_items` (array, 可选): 高级：直接传 source_paragraph/target_start/target_end 键值对，与上述三参数二选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `source_paragraph` (number, 必填): 源段落索引，从 1 开始
- `target_end` (number, 必填): 目标结束段落索引，从 1 开始
- `target_start` (number, 必填): 目标起始段落索引，从 1 开始
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
