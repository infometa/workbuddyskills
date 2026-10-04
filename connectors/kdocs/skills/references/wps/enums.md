# WPS 文字枚举值参考

本文件集中定义在线文字（`wps.*`）结构化工具常用的 Word 枚举常量。

---

## WdParagraphAlignment — 对齐方式

| 工具 | 参数 |
|------|------|
| `wps.texts.alignment` | `alignment` |
| `wps.header_footers.header_alignment` / `wps.header_footers.footer_alignment` | `alignment` |
| `wps.tables.cell_alignment` / `wps.tables.row_alignment` / `wps.tables.column_alignment` | `alignment` |

| 名称 | 值 | 说明 |
|------|-----|------|
| wdAlignParagraphLeft | 0 | 左对齐 |
| wdAlignParagraphCenter | 1 | 居中 |
| wdAlignParagraphRight | 2 | 右对齐 |
| wdAlignParagraphJustify | 3 | 两端对齐 |
| wdAlignParagraphDistribute | 4 | 分散对齐 |
| wdAlignParagraphJustifyMed | 5 | 两端对齐，字符中度压缩 |
| wdAlignParagraphJustifyHi | 7 | 两端对齐，字符高度压缩 |
| wdAlignParagraphJustifyLow | 8 | 两端对齐，字符轻微压缩 |
| wdAlignParagraphThaiJustify | 9 | 泰语格式两端对齐 |

---

## WdLineSpacing — 行间距

| 工具 | 参数 |
|------|------|
| `wps.texts.line_spacing` | `spacing_rule`（`spacing_value` 为配套数值，见枚举说明） |

| 名称 | 值 | 说明 |
|------|-----|------|
| wdLineSpaceSingle | 0 | 单倍行距（默认） |
| wdLineSpace1pt5 | 1 | 1.5 倍行距 |
| wdLineSpaceDouble | 2 | 双倍行距 |
| wdLineSpaceAtLeast | 3 | 最小行距 |
| wdLineSpaceExactly | 4 | 固定行距（需指定 spacingValue，单位磅） |
| wdLineSpaceMultiple | 5 | 多倍行距（需指定 spacingValue，单位磅） |

---

## WdColorIndex — 颜色

| 工具 | 参数 |
|------|------|
| `wps.texts.highlight` | `highlight_color` |
| `wps.texts.font` / `wps.texts.font_batch` | `font_key=ColorIndex` + `font_value` / `font_items[].key=ColorIndex` |
| `wps.header_footers.header_font` / `wps.header_footers.footer_font` | `font_style.color_index` / `color_index` |
| `wps.tables.cell_background` / `wps.tables.row_background` / `wps.tables.column_background` | `color_index` |
| `wps.tables.borders` / `wps.tables.cell_border` | `border_color` / `border_key=ColorIndex` |
| `wps.texts.shading` | `shading_key=BackgroundPatternColorIndex` + `shading_value` |

| 名称 | 值 | 说明 |
|------|-----|------|
| wdByAuthor | -1 | 由文档作者定义 |
| wdAuto | 0 | 自动（默认黑色） |
| wdBlack | 1 | 黑色 |
| wdBlue | 2 | 蓝色 |
| wdTurquoise | 3 | 青绿色 |
| wdBrightGreen | 4 | 鲜绿色 |
| wdPink | 5 | 粉红色 |
| wdRed | 6 | 红色 |
| wdYellow | 7 | 黄色 |
| wdWhite | 8 | 白色 |
| wdDarkBlue | 9 | 深蓝色 |
| wdTeal | 10 | 青色 |
| wdGreen | 11 | 绿色 |
| wdViolet | 12 | 紫色 |
| wdDarkRed | 13 | 深红色 |
| wdDarkYellow | 14 | 深黄色 |
| wdGray50 | 15 | 50%灰色 |
| wdGray25 | 16 | 25%灰色 |

高亮色专用：`wdNoHighlight`(0) 清除高亮。

---

## WdUnderline — 下划线样式

| 工具 | 参数 |
|------|------|
| `wps.texts.font` / `wps.texts.font_batch` | `font_key=Underline` + `font_value` / `font_items[].key=Underline` |
| `wps.header_footers.header_font` / `wps.header_footers.footer_font` | `font_style.underline` / `underline` |

| 名称 | 值 | 说明 |
|------|-----|------|
| wdUnderlineNone | 0 | 无下划线 |
| wdUnderlineSingle | 1 | 单线（默认） |
| wdUnderlineWords | 2 | 仅单字下划线 |
| wdUnderlineDouble | 3 | 双线 |
| wdUnderlineDotted | 4 | 点线 |
| wdUnderlineThick | 6 | 粗线 |
| wdUnderlineDash | 7 | 划线 |
| wdUnderlineDotDash | 9 | 点划线 |
| wdUnderlineDotDotDash | 10 | 点点划线 |
| wdUnderlineWavy | 11 | 波浪线 |
| wdUnderlineDottedHeavy | 20 | 粗点线 |
| wdUnderlineDashHeavy | 23 | 粗划线 |
| wdUnderlineDotDashHeavy | 25 | 粗点划线 |
| wdUnderlineDotDotDashHeavy | 26 | 粗点点划线 |
| wdUnderlineWavyHeavy | 27 | 粗波浪线 |
| wdUnderlineDashLong | 39 | 长划线 |
| wdUnderlineWavyDouble | 43 | 双波浪线 |
| wdUnderlineDashLongHeavy | 55 | 长粗划线 |

---

## WdBorderIndex — 边框位置

| 工具 | 参数 |
|------|------|
| `wps.texts.border` | `border_type` |

| 名称 | 值 | 说明 |
|------|-----|------|
| wdBorderTop | -1 | 上框线 |
| wdBorderLeft | -2 | 左侧框线 |
| wdBorderBottom | -3 | 底边框线 |
| wdBorderRight | -4 | 右侧框线 |
| wdBorderHorizontal | -5 | 横向框线 |
| wdBorderVertical | -6 | 纵向框线 |
| wdBorderDiagonalDown | -7 | 斜下（左上→右下） |
| wdBorderDiagonalUp | -8 | 斜上（左下→右上） |

---

## WdLineStyle — 边框线型

| 工具 | 参数 |
|------|------|
| `wps.texts.border` | `border_key=LineStyle` |
| `wps.tables.borders` | `line_style` |
| `wps.tables.cell_border` | `border_key=LineStyle` |
| `wps.sections.border` | `line_style` / `key=LineStyle` |

| 名称 | 值 | 说明 |
|------|-----|------|
| wdLineStyleNone | 0 | 无边框 |
| wdLineStyleSingle | 1 | 单实线 |
| wdLineStyleDot | 2 | 点 |
| wdLineStyleDashSmallGap | 3 | 划线后跟小间隙 |
| wdLineStyleDashLargeGap | 4 | 划线后跟大间隙 |
| wdLineStyleDashDot | 5 | 划线后跟点 |
| wdLineStyleDashDotDot | 6 | 划线后跟两个点 |
| wdLineStyleDouble | 7 | 双实线 |
| wdLineStyleTriple | 8 | 三条细实线 |
| wdLineStyleThinThickSmallGap | 9 | 细内粗外，间隙较小 |
| wdLineStyleThickThinSmallGap | 10 | 粗内细外，间隙较小 |
| wdLineStyleThinThickThinSmallGap | 11 | 细-粗-细，间隙较小 |
| wdLineStyleThinThickMedGap | 12 | 细内粗外，间隙中等 |
| wdLineStyleThickThinMedGap | 13 | 粗内细外，间隙中等 |
| wdLineStyleThinThickThinMedGap | 14 | 细-粗-细，间隙中等 |
| wdLineStyleThinThickLargeGap | 15 | 细内粗外，间隙较大 |
| wdLineStyleThickThinLargeGap | 16 | 粗内细外，间隙较大 |
| wdLineStyleThinThickThinLargeGap | 17 | 细-粗-细，间隙较大 |
| wdLineStyleSingleWavy | 18 | 波浪型单实线 |
| wdLineStyleDoubleWavy | 19 | 波浪型双实线 |
| wdLineStyleDashDotStroked | 20 | 划线后跟粗点 |
| wdLineStyleEmboss3D | 21 | 三维阳文 |
| wdLineStyleEngrave3D | 22 | 三维阴文 |
| wdLineStyleOutset | 23 | 凸起 |
| wdLineStyleInset | 24 | 凹进 |

---

## WdLineWidth — 边框线宽

禁止传磅值小数；与 `wps.tables.borders` 的 `line_width`（磅值浮点）不是同一类型。

| 工具 | 参数 |
|------|------|
| `wps.texts.border` | `border_key=LineWidth` |
| `wps.tables.cell_border` | `border_key=LineWidth` |
| `wps.sections.border` | `key=LineWidth` |

| 名称 | 值 | 说明 |
|------|-----|------|
| wdLineWidth025pt | 2 | 0.25 磅 |
| wdLineWidth050pt | 4 | 0.50 磅 |
| wdLineWidth075pt | 6 | 0.75 磅 |
| wdLineWidth100pt | 8 | 1.00 磅（默认） |
| wdLineWidth150pt | 12 | 1.50 磅 |
| wdLineWidth225pt | 18 | 2.25 磅 |
| wdLineWidth300pt | 24 | 3.00 磅 |
| wdLineWidth450pt | 36 | 4.50 磅 |
| wdLineWidth600pt | 48 | 6.00 磅 |

---

## WdBuiltinStyle — 内置样式（标题子集）

推荐传 1–9 级别数字；负整数为 WdBuiltinStyle 备选。

| 工具 | 参数 |
|------|------|
| `wps.texts.heading` | `heading_level` |

| 名称 | 值 | 说明 |
|------|-----|------|
| wdStyleNormal | -1 | 正文 |
| wdStyleHeading1 | -2 | 标题 1 |
| wdStyleHeading2 | -3 | 标题 2 |
| wdStyleHeading3 | -4 | 标题 3 |
| wdStyleHeading4 | -5 | 标题 4 |
| wdStyleHeading5 | -6 | 标题 5 |
| wdStyleHeading6 | -7 | 标题 6 |
| wdStyleHeading7 | -8 | 标题 7 |
| wdStyleHeading8 | -9 | 标题 8 |
| wdStyleHeading9 | -10 | 标题 9 |

---

## WdRowHeightRule — 行高规则

与 `wps.tables.row_height` 的 `height`（磅值）配合使用。

| 工具 | 参数 |
|------|------|
| `wps.tables.row_height_rule` | `height_rule` |

| 名称 | 值 | 说明 |
|------|-----|------|
| wdRowHeightAuto | 0 | 自动调整行高（适应该行最大高度） |
| wdRowHeightAtLeast | 1 | 行高至少为指定最小值 |
| wdRowHeightExactly | 2 | 固定行高 |
