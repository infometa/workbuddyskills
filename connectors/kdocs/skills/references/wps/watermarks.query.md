# wps.watermarks.query

## 1. wps.watermarks.query

#### 功能说明

查询在线文字文档水印（存在性、文本、斜体等属性读回）。

**幂等性**：是 — safe

> WATERMARK_QUERY proto 化专用 RPC（documents/watermarks/query）与 WatermarkInfo 字段；text 中文无 mojibake 问题
> 水印为节页眉中的艺术字/图片形状，按名称 PowerPlusWaterMarkObject*/WordPictureWatermark* 识别；JSAPI 依据 Shapes.AddTextEffect 写侧同名访问路径与 TextEffectFormat.Text/FontItalic/FontBold/FontName/FontSize、Shape.Rotation、Fill.ForeColor.RGB
> count=0 表示文档当前无水印（含删除后核验）

#### 调用示例

文档查询：

```json
{
  "file_id": "<FILE_ID>"
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "count": 1,
    "sections": 1,
    "watermarks": [
      {
        "section_index": 1,
        "type": "text",
        "name": "PowerPlusWaterMarkObject1",
        "text": "内部文件",
        "italic": -1,
        "bold": 0,
        "rotation": 315,
        "font_name": "宋体",
        "font_size": 48,
        "color": 12632256
      }
    ]
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 0 表示成功 |
| `data` | object | 业务数据 |
| `message` | string | 结果说明 |
