# 模块三：字符格式

字符样式（key-value 模式）和高亮色设置。枚举值见 [enums.md](enums.md)。

---

## 字符样式（key-value 模式）

### modifyParagraphFontStyle — 修改段落字符样式

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| n | uint32 | 是 | 段落索引 |
| key | string | 是 | 字符属性名，见下表 |
| value | 见下表 | 是 | 属性值，类型随 key 变化 |

### modifyRangeFontStyle — 修改区间字符样式

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| begin | uint32 | 是 | 开始位置 |
| end | uint32 | 是 | 结束位置 |
| key | string | 是 | 字符属性名 |
| value | 见下表 | 是 | 属性值 |

### key-value 对照表

| key | value 类型 | 含义 | value 说明 |
|-----|-----------|------|-----------|
| Name | string | 字体名称 | 如 `"宋体"`、`"Arial"` |
| Size | uint32 | 字号 | 如 12、14、18 |
| ColorIndex | enum | 字体颜色 | 见 [WdColorIndex](enums.md#wdcolorindex--颜色) |
| Bold | bool | 加粗 | true / false |
| Italic | bool | 倾斜 | true / false |
| Underline | enum | 下划线样式 | 见 [WdUnderline](enums.md#wdunderline--下划线样式)，默认 wdUnderlineNone(0) |

### 调用示例

```json
{"id": "file_xxx", "command": "modifyParagraphFontStyle", "param": {"n": 1, "key": "Bold", "value": true}}
```

```json
{"id": "file_xxx", "command": "modifyParagraphFontStyle", "param": {"n": 1, "key": "Name", "value": "黑体"}}
```

```json
{"id": "file_xxx", "command": "modifyParagraphFontStyle", "param": {"n": 1, "key": "Size", "value": 18}}
```

```json
{"id": "file_xxx", "command": "modifyRangeFontStyle", "param": {"begin": 0, "end": 50, "key": "ColorIndex", "value": 6}}
```

> 设置同一段落的多个字符属性需分多次调用，每次传一个 key-value。

---

## 高亮色

### modifyParagraphHighlight — 修改段落高亮色

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| n | uint32 | 是 | 段落索引 |
| highColor | enum | 是 | 高亮色，见 [WdColorIndex](enums.md#wdcolorindex--颜色) |

### modifyRangeHighlight — 修改区间高亮色

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| begin | uint32 | 是 | 开始位置 |
| end | uint32 | 是 | 结束位置 |
| highColor | enum | 是 | 高亮色 |

### 调用示例

```json
{"id": "file_xxx", "command": "modifyParagraphHighlight", "param": {"n": 1, "highColor": 7}}
```

```json
{"id": "file_xxx", "command": "modifyRangeHighlight", "param": {"begin": 0, "end": 50, "highColor": 6}}
```

清除高亮：传 `highColor: 0`（wdNoHighlight）。
