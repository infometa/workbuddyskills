# 数据标签域 — 标签分类写操作契约

> 概念知识：`references/domains/data-tag.md`；运营流程：`references/flows/data-tag.md`；分类树检索先读 `category-query.md`。ID 均为十进制字符串；写操作须遵守入口 Skill 的风险档位、影响说明和回读纪律（确认由运行时权限模式兜底）。
> **工具**：`当前运行时的 Capability 写操作执行器`（`mall.action`）——单次提交、不自动重试，超时或结果不确定先回读现态再决定下一步。
> 能力索引：data-tag.category.create 创建分类 · data-tag.category.update 编辑分类 · data-tag.category.delete 删除分类 🔴

---

## ✅ 创建分类 — ops.data-tag.category.create

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | String | ✅ | 分类名称，最多 50 字符 |
| parentId | String | ✅ | 父分类 ID（来自 `category.tree`；根传 `"-1"`） |
| sort | Integer | — | 排序 |
| description | String | — | 描述，最多 200 字符 |
| scope | Integer | — | 只允许确认过权限边界时传（0=全局 / 1=租户）。**scope=0 会创建后续不可改/不可删的全局分类** |

创建前先确认父分类。

### 调用示例

```json
{"capability":"ops.data-tag.category.create","input":{"name":"营销人群","parentId":"-1","sort":10},"summary":"创建营销人群标签分类"}
```

---

## ✅ 编辑分类 — ops.data-tag.category.update

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 分类 ID（来自 `category.tree`） |
| name | String | ✅ | 分类名称，最多 50 字符 |
| sort | Integer | — | 排序 |
| description | String | — | 描述，最多 200 字符 |

**全局分类（scope=0）不可编辑**（服务端拒绝）。

### 调用示例

```json
{"capability":"ops.data-tag.category.update","input":{"id":"6000000000000000001","name":"营销人群","sort":10},"summary":"调整营销人群分类名称和排序"}
```

---

## ✅ 删除分类 — ops.data-tag.category.delete

- 🔴 不可恢复。先查询分类树确认目标**无关联标签且无子分类**——两者任一存在服务端均拒绝删除；**全局分类不可删除**

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 分类 ID（来自 `category.tree`） |

### 调用示例

```json
{"capability":"ops.data-tag.category.delete","input":{"id":"6000000000000000001"},"summary":"删除已确认无标签关联的分类"}
```
