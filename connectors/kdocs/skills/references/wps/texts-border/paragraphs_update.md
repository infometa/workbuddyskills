# wps.texts.border

#### 功能说明

设置文本的段落边框（支持四边批量）

**幂等性**：是 — safe

> 写操作报 500002 且读操作正常时，先排查文档保护态（wps.protection.disable 后重试），再排查参数；不要盲目重试。

#### 调用示例

四边统一双线红色：

```json
{
  "file_id": "<FILE_ID>",
  "paragraph_index": 3,
  "border_style": {
    "all": {
      "line_style": 7,
      "color": "FF0000"
    }
  }
}
```

上边双线、下边单线（其余不动）：

```json
{
  "file_id": "<FILE_ID>",
  "paragraph_index": 3,
  "border_style": {
    "top": {
      "line_style": 7
    },
    "bottom": {
      "line_style": 1
    }
  }
}
```

仅左边虚线：

```json
{
  "file_id": "<FILE_ID>",
  "paragraph_index": 3,
  "border_style": {
    "left": {
      "line_style": 3,
      "line_width": 1.5
    }
  }
}
```

段落设置：

```json
{
  "file_id": "<FILE_ID>",
  "verb": "update",
  "border_type": 1,
  "key": "Bold",
  "paragraph_index": 1,
  "value": "true"
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一
- `verb` (string, 必填): 操作类型，固定为 update（更新）。可选值：`update`
- `border_style` (object, 可选): 按边批量写边框（推荐）。对象键为 all/top/left/bottom/right， 值为样式对象 {line_style, line_width, color}。 all 为四边统一快捷写法；显式边优先。与 border_type 二选一，优先。
- `border_type` (number, 可选): 单边模式边框方位 WdBorderIndex：-1=上 / -2=左 / -3=下 / -4=右 （缺省 0 视为 -1）。与 border_style 二选一（border_style 优先）。。可选值：`-1` / `-2` / `-3` / `-4`
- `key` (string, 可选): 单边模式边框属性名（Border 对象属性）：LineStyle（线型）/ LineWidth（线宽）/ Color（颜色） （缺省 LineStyle）。
- `paragraph_index` (number, 必填): 段落索引，从 1 开始
- `value` (string, 可选): 单边模式属性值（与 query 读回口径一致）。key=LineWidth 时为 WdLineWidth： 2=0.25磅 / 4=0.5磅（默认）/ 6=0.75磅 / 8=1磅 / 12=1.5磅 / 18=2.25磅 / 24=3磅 / 36=4.5磅 / 48=6磅；key=LineStyle 时为 WdLineStyle：0=none / 1=单实线 / 2=点 / 3=划线小间隙 / 5=划线加点 / 6=划线加两点 / 7=双实线 / 8=三条细线 / 18=波浪单线（双线是 7）；key=Color 时为 WdColor/RGB 数值。

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

