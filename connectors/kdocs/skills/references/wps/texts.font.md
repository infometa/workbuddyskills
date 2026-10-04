# wps.texts.font

#### 功能说明

在线文字文档文本的段落字体：支持 查询/设置。查询返回当前字号、加粗、颜色等字符格式；设置按段落或字符区间写入字体样式（不支持 highlight_color，写高亮须用 wps.texts.highlight）。

**幂等性**：是 — safe

#### 支持功能

| 功能简述 | 详情 |
|--------------|------|
| 按段落查询字体信息 | [texts-font/paragraphs_query.md](texts-font/paragraphs_query.md) |
| 按段落设置字体 | [texts-font/paragraphs_update.md](texts-font/paragraphs_update.md) |
| 按字符区间查询字体信息 | [texts-font/ranges_query.md](texts-font/ranges_query.md) |
| 按字符区间设置字体 | [texts-font/ranges_update.md](texts-font/ranges_update.md) |
