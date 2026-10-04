# wps.texts.border

#### 功能说明

在线文字文档文本的段落边框：支持 插入/设置/查询。query 读回段落四边边框（border_info[] 专用字段，side/line_style/line_width/color，与写侧 value 口径一致）。

**幂等性**：是 — safe

#### 支持功能

| 功能简述 | 详情 |
|--------------|------|
| 插入文本的段落边框 | [texts-border/paragraphs_insert.md](texts-border/paragraphs_insert.md) |
| 查询段落四边边框（border_info） | [texts-border/paragraphs_query.md](texts-border/paragraphs_query.md) |
| 设置文本的段落边框（支持四边批量） | [texts-border/paragraphs_update.md](texts-border/paragraphs_update.md) |
