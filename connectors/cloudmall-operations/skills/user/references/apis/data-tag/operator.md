# 数据标签域 — 运算符契约

> 创建规则前先查询。规则结构见 `references/domains/data-tag.md`；运营流程：`references/flows/data-tag.md`。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引：data-tag.operator.list 运算符列表

---

## ✅ 运算符列表 — ops.data-tag.operator.list

返回 `code`、显示名称、符号和 `applicableTypes`；仅使用返回且适用于目标标签值类型的编码。该接口实际返回的 9 个编码为 `eq`、`neq`、`gt`、`lt`、`gte`、`lte`、`between`、`in`、`not_in`（⚠️ 不是 ne/ge/le/nin——人群包 queryCondition 解析层虽同时接受两套别名，但以本接口返回为准）。**⚠️ 标签 valueDefine 例外**：规则标签的 valueDefine 规则项仅支持 eq/ne/gt/lt/ge/le/in/nin/between 短码，neq/gte/lte/not_in 不受支持（详见 `tag-action.md`）。

### 调用示例

```json
{"capability":"ops.data-tag.operator.list","input":{},"summary":"查询规则标签可用运算符"}
```
