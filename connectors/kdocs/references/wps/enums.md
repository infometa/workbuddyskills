# WPS 文字枚举值参考

本文件集中定义所有 Core Execute 命令共享的枚举常量。

---

## WdParagraphAlignment — 对齐方式

用于 `modifyParagraphAlignment` / `modifyRangeAlignment` 的 `algMode` 参数。

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

用于 `modifyParagraphLineSpacing` / `modifyRangeLineSpacing` 的 `spacingRule` 参数。

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

用于 `modifyParagraphFontStyle` / `modifyRangeFontStyle` 的 `ColorIndex` 值，以及 `modifyParagraphHighlight` / `modifyRangeHighlight` 的 `highColor` 参数。

| 名称 | 值 | 说明 |
|------|-----|------|
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

高亮色专用：`wdNoHighlight`(0) 清除高亮，`wdByAuthor`(-1) 由作者定义。

---

## WdUnderline — 下划线样式

用于 `modifyParagraphFontStyle` / `modifyRangeFontStyle` 的 `Underline` 值。

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
