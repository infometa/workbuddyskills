# wps.footnote_endnotes.footnote_font

## 1. wps.footnote_endnotes.footnote_font

#### 功能说明

设置在线文字文档脚注/尾注的字体（font_style 强类型；省略 font_style 时读回当前属性）。

**幂等性**：是 — safe

#### 调用示例

设置脚注字号：

```json
{
  "file_id": "<FILE_ID>",
  "index": 1,
  "font_style": {
    "font_size": 9
  }
}
```

读回脚注字号：

```json
{
  "file_id": "<FILE_ID>",
  "index": 1
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `font_style` (object, 可选): 字体样式对象，键取 font_size(磅值)/bold(1|0)/color(数值) 恰好其一；省略则读回当前属性
- `index` (number, 可选): 脚注索引，从 1 开始
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "item": {
      "index": 1,
      "text": "脚注测试内容",
      "reference": "_Ref123456",
      "type": 1,
      "begin": 120,
      "end": 121,
      "font_style": {
        "font_size": 9,
        "bold": false,
        "color_index": "-16777216"
      }
    }
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 0 表示成功 |
| `data` | object | 业务数据 |
| `message` | string | 结果说明 |
