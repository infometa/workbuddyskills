# 直播域 — 讲解场次与场次商品写操作契约

> 概念知识：`references/domains/live-concepts.md`，状态与枚举：`references/domains/live-enums.md`；运营流程：`references/flows/live.md`；场次与商品现值读取（编辑基线/回读依据）先读 `session-goods-query.md`。
> 所有 ID 均为十进制字符串；写操作须遵守入口 Skill 的风险档位、明确确认和回读纪律。
> **工具**：`当前运行时的 Capability 写操作执行器`（`mall.action`）——单次提交、不自动重试，超时或结果不确定先回读现态再决定下一步。
> 能力索引：live.session.update 编辑场次 🔴 · live.session.cancel 取消场次 🔴 · live.session-goods.add 添加场次商品 🔴 · live.session-goods.sort 排序场次商品 🔴 · live.session-goods.remove 移除场次商品 🔴 · live.session-goods.update-sku 更新场次SKU直播价库存 🔴

---

## ✅ 编辑场次 — ops.live.session.update

- 🔴 排期影响。
- 入参：`sessionId` String 必填；可选字段 `sessionTitle` ≤100（纯空白串会被服务端拒绝「场次标题不能为空」）、`sessionCoverUrl` ≤500、`sessionDescription` ≤500、`anchorId` String（传入时服务端校验主播处于启用状态）、`planStartTime`/`planEndTime` ISO 本地日期时间、`priceValidMinutes` Integer 0..1440。body 必须存在（可为 `{}`，整体省略会 400）。
- 前置：先查场次并确认状态 0 已排期；只传变更字段，起止时间组合仍需合法。服务端守卫：`planStartTime` 必须晚于当前时间、结束晚于生效开始、同直播间时间段不可与其他场次重叠、乐观锁并发冲突报「场次已被并发修改，请刷新后重试」。返回通常为空，分页回读全部变更字段。

```json
{"capability":"ops.live.session.update","input":{"sessionId":"7300000000000000001","sessionTitle":"秋季新品专场","planStartTime":"2026-09-20T20:00:00","planEndTime":"2026-09-20T21:30:00"},"summary":"将秋季专场顺延半小时"}
```

---

## ✅ 取消场次 — ops.live.session.cancel

- 🔴 生命周期终止操作。
- 入参：`sessionId` String 必填；`reason` String 可选、≤500 字，运营纪律要求明确、可审计原因。body 可整体省略。
- 前置：仅状态 0已排期 / 1准备中 可取消（准备中场次已占用直播间当前场次，取消会一并释放）；向用户复述名称、直播间与时间。返回通常为空，回读状态应为 6；超时不重复提交。

```json
{"capability":"ops.live.session.cancel","input":{"sessionId":"7300000000000000001","reason":"主播行程调整"},"summary":"取消因主播行程调整无法进行的待播场次"}
```

---

## ✅ 添加场次商品 — ops.live.session-goods.add

- 🔴 商业影响。
- 入参：`sessionId` String 必填；`items` Array 必填且非空。`items[]`：`spuId` String 必填，`skuIds` String[] 必填且非空（`skuIds:null` 会引发服务端 500）。不得传 `spuIds`（DTO 旧接口专用字段，本端点忽略）。
- 前置：逐项调用商品域能力核对 SPU 存在、每个 SKU 属于该 SPU、规格和可售状态；去重；用户确认完整清单。Java 对 `items`、`items[].spuId`、`items[].skuIds` 均无可依赖的完整级联 Bean Validation 保证，调用纪律必须逐层补齐——服务端对 SPU/SKU 存在性与归属**零校验**，错误数据会以「默认规格/无价格」形态静默落库。
- 服务端口径：单场次商品上限 50（超出报错）；`items` 为空数组或 null 时静默成功无任何效果（回读是唯一验证）；无场次状态守卫（已结束/已取消场次同样可加商品）；已存在的 SPU 复用记录、已存在的 SKU 静默跳过（幂等）。
- 返回通常为空；用场次商品列表回读。

```json
{"capability":"ops.live.session-goods.add","input":{"sessionId":"7300000000000000001","items":[{"spuId":"2058365707555589633","skuIds":["9000012345678901234"]}]},"summary":"向秋季专场添加已核验的商品规格"}
```

---

## ✅ 排序场次商品 — ops.live.session-goods.sort

- 🔴 展示顺序影响。
- 入参：`sessionId` String 必填；`sortedSpuIds` String[] 必填且非空。
- 前置：先读取当前列表；提交完整、不重复、与现有集合一致的 SPU ID 顺序，不能只传移动项——未传入的 SPU 保持旧排序值，部分提交会产生排序值碰撞、顺序不确定。返回通常为空，回读核验顺序。
- 服务端口径：不在场次中的 SPU ID（含拼错的）静默忽略；`sessionId` 不存在时同样静默返回成功——回读是唯一验证。

```json
{"capability":"ops.live.session-goods.sort","input":{"sessionId":"7300000000000000001","sortedSpuIds":["2058365707555589633","2058365707555589634"]},"summary":"按确认顺序调整秋季专场商品"}
```

---

## ✅ 移除场次商品 — ops.live.session-goods.remove

- 🔴 从场次移除。
- 入参：`sessionId`、`spuId` String 必填。
- 前置：确认场次、商品名称与 SPU ID；说明只移除场次关联，不删除商品域商品。返回通常为空，回读确认不存在。移除不在场次中的商品静默成功（幂等），回读是唯一验证。

```json
{"capability":"ops.live.session-goods.remove","input":{"sessionId":"7300000000000000001","spuId":"2058365707555589633"},"summary":"从秋季专场移除已确认的商品"}
```

---

## ✅ 更新场次 SKU 直播价/库存 — ops.live.session-goods.update-sku

- 🔴 直接影响成交。
- 入参：`sessionId`、`skuId` String 必填；`livePrice` Number 可选且 ≥0（无小数位约束，原样存储）；`liveStock` Integer 可选且 ≥0。至少一项必须为非 null；null/省略仅表示不更新该字段，不能清空直播价/库存，也不能恢复跟随原价或不限库存。两字段全 null 时幂等成功无效果。
- 前置：先读场次商品并用商品域核对 SKU 归属（SKU 不在该场次时服务端拒绝，但该拒绝走普通运行时异常通道、按 500「系统异常」返回、具体消息不透出）；价格和库存必须由用户给出。Java DTO/运行时都未校验非负；因此 Skill 调用纪律要求只提交明确的非负数值。
- 服务端口径：本端点**不写商品变更记录**（change-logs 完全看不到此修改），也**不做托管库存池校验与同步**（房间维度旧端点才有该行为）——回读目标 SKU 是唯一验证。
- 返回通常为空；回读目标 SKU 的 `livePrice/liveStock`。

```json
{"capability":"ops.live.session-goods.update-sku","input":{"sessionId":"7300000000000000001","skuId":"9000012345678901234","livePrice":99.00,"liveStock":100},"summary":"设置秋季专场指定SKU的直播价和库存"}
```
