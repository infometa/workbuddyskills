# wps.sections.page_setup

#### 功能说明

在线文字文档节的节页面设置：支持 查询/设置。update 的 key 仅接受 PageSetup 的 PascalCase 属性（PageWidth/PageHeight/Orientation/TopMargin/BottomMargin/LeftMargin/RightMargin/Gutter/HeaderDistance/FooterDistance/SectionStart/VerticalAlignment/LinesPage）；先设 Orientation 再设宽高/边距（Orientation 会联动交换宽高与边距）；query 响应中 page_setup 字段为 snake_case。

**幂等性**：是 — safe

#### 支持功能

| 功能简述 | 详情 |
|--------------|------|
| 查询节的节页面设置 | [sections-page_setup/documents_query.md](sections-page_setup/documents_query.md) |
| 设置节的节页面设置 | [sections-page_setup/documents_update.md](sections-page_setup/documents_update.md) |
