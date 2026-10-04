# wps.styles.definition

#### 功能说明

更新样式定义

#### 调用示例

文档设置：

```json
{
  "file_id": "<FILE_ID>",
  "alignment": 1,
  "bold": true,
  "font_name": "Arial",
  "font_size": 12,
  "style_name": "SmokeStyleSlice",
  "verb": "update"
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `verb` (string, 必填): 操作类型，固定为 update（更新）。可选值：`update`
- `alignment` (number, 可选): 段落对齐（verb=update）：0=左对齐, 1=居中, 2=右对齐, 3=两端对齐, 4=分散对齐
- `bold` (boolean, 可选): 是否加粗
- `font_name` (string, 可选): 字体名称
- `font_size` (number, 可选): 字号
- `color` (string, 可选): 字体颜色（R,G,B，与 line_color 同口径；也接受
- `style_name` (string, 必填): 样式名称

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

