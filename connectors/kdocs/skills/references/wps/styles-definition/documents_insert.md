# wps.styles.definition

#### 功能说明

插入样式定义

#### 调用示例

文档插入：

```json
{
  "file_id": "<FILE_ID>",
  "bold": true,
  "font_name": "Arial",
  "font_size": 12,
  "style_name": "SmokeStyleSliceInsert",
  "style_type": 1,
  "verb": "insert"
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `verb` (string, 必填): 操作类型，固定为 insert（插入）。可选值：`insert`
- `bold` (boolean, 可选): 是否加粗
- `font_name` (string, 可选): 字体名称
- `font_size` (number, 可选): 字号
- `color` (string, 可选): 字体颜色（R,G,B，与 line_color 同口径；也接受
- `style_name` (string, 必填): 样式名称
- `style_type` (number, 可选): 样式类型

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

