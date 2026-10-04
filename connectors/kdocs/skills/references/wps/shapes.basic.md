# wps.shapes.basic

## 1. wps.shapes.basic

#### 功能说明

插入在线文字文档形状的基本形状。

**幂等性**：是 — safe

> 插入响应 info.shape_item 即新形状标识（数字串 index），可直接用于 wps.shapes.info / 各 shapes update 工具定位，无需插后 wps.shapes.list。
> 插入时传入的 left/top 坐标会被引擎锚定回流归一化，回读值可能与写入值不同（如写入 left=72 回读 -18，TC_086）；核验形状位置应以 wps.shapes.list 读回值为准，不要用插入入参断言。

#### 调用示例

文档插入：

```json
{
  "file_id": "<FILE_ID>",
  "height": 50,
  "left": 72,
  "shape_type": 1,
  "top": 72,
  "width": 100
}
```

#### 参数说明

- `begin` (number, 可选): 锚定起点（0-based，不传锚文档起始）
- `end` (number, 可选): 锚定终点（0-based，不传锚文档起始）
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `height` (number, 可选): 高度
- `left` (number, 可选): left
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `shape_type` (number, 可选): 形状类型（MsoAutoShapeType 十进制值）：1=矩形(msoShapeRectangle)、5=圆角矩形(msoShapeRoundedRectangle)、9=椭圆(msoShapeOval)、7=等腰三角形(msoShapeIsoscelesTriangle)、61=直线(msoShapeLine)、33=右箭头(msoShapeRightArrow)、34=左箭头(msoShapeLeftArrow)、35=上箭头(msoShapeUpArrow)、36=下箭头(msoShapeDownArrow)；完整枚举见 jsapi wiki word-shapes.md 及 MsoAutoShapeType 标准。
- `top` (number, 可选): top
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一
- `width` (number, 可选): 宽度

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "info": {
      "height": 50,
      "index": 3,
      "left": -18,
      "name": "Rectangle 3",
      "shape_item": "3",
      "top": 72,
      "type": 1,
      "width": 100
    }
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 0 表示成功 |
| `data` | object | 业务数据 |
| `message` | string | 结果说明 |
