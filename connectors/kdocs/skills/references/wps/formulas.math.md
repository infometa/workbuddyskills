# wps.formulas.math

#### 功能说明

插入/查询在线文字文档公式。insert 支持段落与区间两种落点；query 读回 OMath 公式列表（含 WdOMathType、所在段落与区间）。

**幂等性**：否 — safe

> insert 写通道：段落口径在目标段落末尾插入（保留原段落内容）；区间口径替换 begin/end 指定文本

#### 支持功能

| 功能简述 | 详情 |
|--------------|------|
| 插入公式 | [formulas-math/documents_insert.md](formulas-math/documents_insert.md) |
| 查询文档公式列表 | [formulas-math/documents_query.md](formulas-math/documents_query.md) |
