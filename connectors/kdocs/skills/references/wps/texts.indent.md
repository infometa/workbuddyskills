# wps.texts.indent

#### 功能说明

设置在线文字文档文本的段落缩进。paragraph_style.indent 的 indent_type/unit 必须为字符串：indent_type 取 "1"=左缩进/"2"=右缩进/"3"=首行缩进，unit 取 "1"=磅/"2"=字符；传数字类型会报 400001，其它名称（first_line/char 等）静默回落默认值。

**幂等性**：是 — safe

#### 支持功能

| 功能简述 | 详情 |
|--------------|------|
| 按段落设置缩进 | [texts-indent/paragraphs_update.md](texts-indent/paragraphs_update.md) |
| 按字符区间设置缩进 | [texts-indent/ranges_update.md](texts-indent/ranges_update.md) |
