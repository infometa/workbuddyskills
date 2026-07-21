# 模块二：段落格式

段落对齐、缩进和行间距设置。枚举值见 [enums.md](enums.md)。

---

## 对齐方式

### modifyParagraphAlignment — 修改指定段落对齐

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| n | uint32 | 是 | 段落索引 |
| algMode | enum | 是 | 对齐方式，见 [WdParagraphAlignment](enums.md#wdparagraphalignment--对齐方式) |

```json
{"id": "file_xxx", "command": "modifyParagraphAlignment", "param": {"n": 1, "algMode": 1}}
```

### modifyRangeAlignment — 修改区间内段落对齐

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| begin | uint32 | 是 | 开始位置 |
| end | uint32 | 是 | 结束位置 |
| algMode | enum | 是 | 对齐方式，见 [WdParagraphAlignment](enums.md#wdparagraphalignment--对齐方式) |

```json
{"id": "file_xxx", "command": "modifyRangeAlignment", "param": {"begin": 0, "end": 200, "algMode": 3}}
```

---

## 缩进

以下 6 个命令共享相同的参数模式，区别在于定位方式和缩进方向。

### 段落缩进命令（按 n 定位）

| 命令 | 作用 |
|------|------|
| `modifyParagraphLeftIndent` | 修改左缩进 |
| `modifyParagraphRightIndent` | 修改右缩进 |
| `modifyParagraphFirstLineIndent` | 修改首行缩进（正值首行缩进，负值悬挂缩进） |

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| n | uint32 | 是 | 段落索引 |
| indent | float | 是 | 缩进值（unit=pt 时为磅，unit=ch 时为字符数） |
| unit | string | 否 | 缩进单位，默认 `pt`（磅）；可选 `ch`（字符） |

```json
{"id": "file_xxx", "command": "modifyParagraphLeftIndent", "param": {"n": 1, "indent": 24}}
```

```json
{"id": "file_xxx", "command": "modifyParagraphFirstLineIndent", "param": {"n": 2, "indent": 2, "unit": "ch"}}
```

### 区间缩进命令（按 begin/end 定位）

| 命令 | 作用 |
|------|------|
| `modifyRangeLeftIndent` | 修改区间左缩进 |
| `modifyRangeRightIndent` | 修改区间右缩进 |
| `modifyRangeFirstLineIndent` | 修改区间首行缩进 |

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| begin | uint32 | 是 | 开始位置 |
| end | uint32 | 是 | 结束位置 |
| indent | float | 是 | 缩进值 |
| unit | string | 否 | 缩进单位，默认 `pt`；可选 `ch` |

```json
{"id": "file_xxx", "command": "modifyRangeLeftIndent", "param": {"begin": 0, "end": 200, "indent": 36, "unit": "pt"}}
```

---

## 行间距

### modifyParagraphLineSpacing — 修改段落行间距

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| n | uint32 | 是 | 段落索引 |
| spacingRule | enum | 是 | 行间距规则，见 [WdLineSpacing](enums.md#wdlinespacing--行间距) |
| spacingValue | float | 条件必填 | spacingRule 为 4(Exactly) 或 5(Multiple) 时必填，单位磅 |

```json
{"id": "file_xxx", "command": "modifyParagraphLineSpacing", "param": {"n": 1, "spacingRule": 0}}
```

```json
{"id": "file_xxx", "command": "modifyParagraphLineSpacing", "param": {"n": 2, "spacingRule": 5, "spacingValue": 36}}
```

### modifyRangeLineSpacing — 修改区间行间距

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| begin | uint32 | 是 | 开始位置 |
| end | uint32 | 是 | 结束位置 |
| spacingRule | enum | 是 | 行间距规则，见 [WdLineSpacing](enums.md#wdlinespacing--行间距) |
| spacingValue | float | 条件必填 | spacingRule 为 4(Exactly) 或 5(Multiple) 时必填，单位磅 |

```json
{"id": "file_xxx", "command": "modifyRangeLineSpacing", "param": {"begin": 0, "end": 500, "spacingRule": 1}}
```
