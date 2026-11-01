# 数据标签域 — 标签分类查询契约

> 概念知识：`references/domains/data-tag.md`；运营流程：`references/flows/data-tag.md`；分类维护写操作见 `category-action.md`，标签与人群包见 `tag-query.md` / `tag-action.md` / `crowd-query.md` / `crowd-action.md`。ID 均为十进制字符串。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引：data-tag.category.tree 分类树

---

## ✅ 分类树 — ops.data-tag.category.tree

- 返回根分类与一层子分类（最多两层）；`id` 可作为创建子分类、编辑或删除的目标，根分类的 parentId 固定为 `"-1"`

### 调用示例

```json
{"capability":"ops.data-tag.category.tree","input":{},"summary":"查看标签分类树"}
```
