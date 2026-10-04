# wps.shapes.wrap_type

#### 功能说明

在线文字文档形状环绕方式：支持 设置/查询（wrap_type 取值（JSAPI WdWrapType 官方值）：0=四周型 1=紧密型 2=穿越型 3=无环绕 4=上下型 5=衬于文字下方 6=浮于文字上方 7=嵌入型；写 7 会将浮动形状转为嵌入型（脱离 Shapes 浮动集合），非法值显式报错）。

**幂等性**：是 — safe

#### 支持功能

| 功能简述 | 详情 |
|--------------|------|
| 查询形状环绕方式 | [shapes-wrap_type/documents_query.md](shapes-wrap_type/documents_query.md) |
| 设置形状的环绕方式 | [shapes-wrap_type/documents_update.md](shapes-wrap_type/documents_update.md) |
