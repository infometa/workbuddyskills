# 直播域 — 直播间与分类写操作契约

> 概念知识：`references/domains/live-concepts.md`，状态与枚举：`references/domains/live-enums.md`；运营流程：`references/flows/live.md`；直播间与分类现值读取（编辑基线/回读依据）先读 `room-anchor-category-query.md`。
> ID 一律十进制字符串；写操作须遵守入口 Skill 的风险档位、明确确认和回读纪律。
> **工具**：`当前运行时的 Capability 写操作执行器`（`mall.action`）——单次提交、不自动重试，超时或结果不确定先回读现态再决定下一步。
> 能力索引：live.room.update 编辑直播间 · live.room.delete 删除直播间 🔴 · live.category.create 创建分类 · live.category.update 编辑分类 · live.category.update-status 启停分类 · live.category.delete 删除分类 🔴

---

## ✅ 编辑直播间 — ops.live.room.update

- 只传需修改字段。
- 入参：`roomId` String 必填；只公开静态可选字段：`title` ≤100、`coverUrl`、`description` ≤500、`category`、`tags` ≤5、`sortOrder` Integer。旧模型的 `anchorId`、`planStartTime`、`priceValidMinutes` 不在开放契约中，不得传入。
- 前置：从分页确认对象与状态；直播中/暂停中不代为编辑。服务端实际仅拦截直播中(1)，暂停(2)可写入——纪律仍不代为编辑，且守卫触发时业务原因不透出（普通运行时异常按「系统异常」500 返回），前置状态核验必须依赖查询而非错误反馈。返回通常为空，分页回读。

```json
{"capability":"ops.live.room.update","input":{"roomId":"7200000000000000001","title":"云MALL秋季新品直播间","sortOrder":10},"summary":"更新直播间标题和排序"}
```

---

## ✅ 删除直播间 — ops.live.room.delete

- 🔴 不可逆。
- 入参：`roomId` String 必填。
- 前置：确认名称、ID、状态和关联场次；仅对已结束/已过期且服务端允许的对象执行（守卫拒绝时业务原因同样不透出，按 500「系统异常」返回）。删除会级联清理回放分片并删除外部点播媒资（媒资物理删除不可恢复；直播侧记录为逻辑删除），须明确告知且取得确认。返回通常为空，以分页查不到该对象核验。

```json
{"capability":"ops.live.room.delete","input":{"roomId":"7200000000000000001"},"summary":"删除已结束且确认无保留需要的直播间"}
```

---

## ✅ 创建分类 — ops.live.category.create

- 入参：`name` String 必填、非空且 ≤32；`sortOrder` Integer 可选、0..9999。
- 前置：列表查重（服务端另有租户内名称唯一强制，重复报 400「分类名称已存在」）；`code` 由服务端自动生成。返回通常为空，回读分类列表。

```json
{"capability":"ops.live.category.create","input":{"name":"新品首发","sortOrder":10},"summary":"创建新品首发直播分类"}
```

---

## ✅ 编辑分类 — ops.live.category.update

- 入参：`id` String、`name` String 必填；`sortOrder` Integer 可选、0..9999——但省略或 null 时会**重置为 0**（并非「不更新」），编辑时必须显式携带原排序值。编辑使用完整保存表单，名称不可省略；重名校验排除自身。

```json
{"capability":"ops.live.category.update","input":{"id":"7500000000000000001","name":"新品首发","sortOrder":20},"summary":"调整新品首发分类排序"}
```

---

## ✅ 启停分类 — ops.live.category.update-status

- 入参：`id` String、`status` Integer 必填，status 仅 0禁用/1启用（其他值服务端报 400「分类状态只能为0或1」）。
- 停用前按分类编码查询直播间并说明影响；停用仅阻断新直播间选用该分类，存量直播间不受影响。回读列表。

```json
{"capability":"ops.live.category.update-status","input":{"id":"7500000000000000001","status":1},"summary":"启用新品首发分类"}
```

---

## ✅ 删除分类 — ops.live.category.delete

- 🔴 不可逆。
- 入参：`id` String 必填。
- 前置：从分类列表取得 code，确认 `roomCount=0` 并用直播间分页复核（服务端同守卫：分类下有直播间时报 400「该分类下已有直播间，请先调整直播间分类后再删除」）；执行后回读。

```json
{"capability":"ops.live.category.delete","input":{"id":"7500000000000000001"},"summary":"删除已确认未被直播间使用的分类"}
```
