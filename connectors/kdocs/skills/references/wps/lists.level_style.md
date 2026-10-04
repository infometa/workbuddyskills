# wps.lists.level_style

## 1. wps.lists.level_style

#### 功能说明

对既有列表的指定级别定向设置编号样式（如一级标题大写罗马数字 I、II、III），不破坏其他级别的多级层级。

**幂等性**：是 — safe

> 以列表内任一段落定位整个列表并整体套用新模板，各级格式完整定义、不压平层级。
> 多列表文档（两个独立编号列表）传 list_block 可分别定位：编号块内独立从 1 开始，互不影响；缺省保持全文档单一编号序列。
> 与 wps.lists.apply_with_level 配合：先建好多级列表，再定制某一级样式（如一级大写罗马）。

#### 调用示例

段落设置：

```json
{
  "file_id": "<FILE_ID>",
  "level": 1,
  "number_format": "%1.",
  "number_style": 1,
  "paragraph_index": 1
}
```

多列表文档按块设置（第 1 块一级改大写罗马）：

```json
{
  "file_id": "<FILE_ID>",
  "level": 1,
  "list_block": 1,
  "number_format": "%1.",
  "number_style": 1,
  "paragraph_index": 1
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id
- `font_name` (string, 可选): 编号字体，可选
- `level` (number, 可选): 目标级别 1-9，默认 1
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id
- `number_format` (string, 可选): 编号格式，如 "%1."；缺省自动按层级生成 x.y.z. 样式
- `number_style` (number, 可选): NumberStyle 枚举：1=大写罗马(I,II,III)，2=小写罗马，0=阿拉伯，39=中文数字
- `paragraph_index` (number, 必填): 该列表内任一段落索引，从 1 起
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `list_block` (number, 可选): 可选：文档内第 N 个列表块（连续列表段落为一个块，用 wps.lists.blocks 枚举）。缺省=全部块（全文档单一编号序列）；指定=仅该块整体套用，编号块内从 1 开始

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "list_info": {
      "paragraph_index": 1,
      "list_level_number": 1,
      "list_string": "I."
    }
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 0 表示成功 |
| `data` | object | 业务数据 |
| `message` | string | 结果说明 |
