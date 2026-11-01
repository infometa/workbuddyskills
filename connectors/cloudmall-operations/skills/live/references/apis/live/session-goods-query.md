# 直播域 — 讲解场次与场次商品查询契约

> 概念知识：`references/domains/live-concepts.md`，状态与枚举：`references/domains/live-enums.md`；运营流程：`references/flows/live.md`。
> 场次是排期、主播、商品、回放和复盘的首选边界。所有 ID 均为十进制字符串；出参为原始业务数据。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引：live.session.search 场次分页 · live.room.sessions 直播间全部场次 · live.goods.room-list 直播间商品列表 · live.goods.session-list 场次商品列表 · live.goods.change-logs 商品变更记录

---

## ✅ 场次分页 — ops.live.session.search

- 入参：`pageNum`/`pageSize` Integer 可选，服务端默认 1/10，`pageSize` 钳制 1..100（超传静默降为 100）；`roomId` String 可选；`status` Integer 可选，只能 0已排期/1准备中/2直播中/3暂停/4已结束/5已过期/6已取消/7已禁播（非法值报 400「Unknown LiveSessionStatus code」——场次分页对 status 做枚举前置校验，与直播间分页的静默空结果不同）；`anchorId` String 可选。
- 出参：分页 `records[]`；关键字段 `id`、`roomId`、`roomCode`、`roomTitle`、`anchorId`、`anchorNickname`、`sessionTitle`、`status/statusDesc`、`category/categoryDesc`、`sessionCoverUrl`（约 30 分钟有效预签名 URL）、计划/实际起止时间、`subscribeCount`、`createdTime`。列表是安全投影，不含推流凭证。

```json
{"capability":"ops.live.session.search","input":{"pageNum":1,"pageSize":20,"roomId":"7200000000000000001","status":0},"summary":"查看直播间已排期场次"}
```

---

## ✅ 直播间全部场次 — ops.live.room.sessions

- 入参：`roomId` String 必填。
- 出参：场次数组，字段同场次列表；用于识别当前活动场次与后续排期。活动态只按返回状态判断，不自行推演。

```json
{"capability":"ops.live.room.sessions","input":{"roomId":"7200000000000000001"},"summary":"查看直播间的全部讲解场次"}
```

---

## ✅ 直播间商品列表 — ops.live.goods.room-list

- 入参：`roomId` String 必填。
- 语义：按直播间解析目标场次读取——优先当前活动场次（`currentSessionId`），无则下一待播场次（`nextSessionId`），两者皆空才回退旧房间维度数据。不作为新写入目标。
- 出参数组：每项 `spuId`、`liveGoodsId`、名称、主图、原价/直播价区间、直播库存合计、销量、浏览数、排序、讲解标记 `isExplaining`、`anchorSelected`、`skus[]`。SPU 已下架时名称为「商品已下架」、主图缺失。SKU 含 `skuId/skuName/specInfo/originalPrice/livePrice/liveStock/soldCount`；`specInfo` 是 JSON 字符串，内容为规格属性名→值的动态映射（如 `{"颜色":"黑","尺码":"XL"}`），展示时取值的有序拼接（按 JSON 文本插入序）。`minLivePrice:null` 表示该 SPU 所有 SKU 的直播价与原价均未设置；`totalLiveStock:null` 表示该 SPU 存在**不限库存**的 SKU（`liveStock` 未设置），不能按 0 处理。

```json
{"capability":"ops.live.goods.room-list","input":{"roomId":"7200000000000000001"},"summary":"查看直播间兼容商品列表"}
```

---

## ✅ 场次商品列表 — ops.live.goods.session-list

- 入参：`sessionId` String 必填。
- 出参结构同直播间商品列表，是添加、排序、移除和 SKU 更新后的回读依据。`sessionId` 不存在时不报错、返回空数组。返回中的 `livePrice` 缺失可表示当前跟随原价，`liveStock` 缺失可表示当前不限（本服务全局 non_null 序列化：null 字段在 JSON 中**整体省略**，不会出现显式 `"livePrice":null` 键——与场次数据 `viewerUv` 的缺失语义同款）；但写入能力中的 null 只是不更新，不能用于恢复这些状态。

```json
{"capability":"ops.live.goods.session-list","input":{"sessionId":"7300000000000000001"},"summary":"查看秋季专场的直播商品与SKU"}
```

---

## ✅ 商品变更记录 — ops.live.goods.change-logs

- 入参：`roomId`、`spuId` String 必填。
- 出参：变更记录数组（按时间倒序，最多返回最近 50 条），字段 `id`、`skuId`、`skuSpec`（服务端拼装标签，形如 `SKU: {skuId} | {规格} | 原价¥{x}`；SKU 记录已不存在时回退字面量「默认规格」；SKU 存在但 `specInfo` 为非法 JSON 时规格段静默回退为 `skuName`，异常不外显——`skuName` 本身也可能是落库时的兜底字面量）、`changeType`（仅 `PRICE`/`STOCK` 两类）、`oldValue`/`newValue`、`operator`、`remark`（恒为 null——全局 non_null 序列化下该键整体缺失，不会出现 `"remark":null`）、`createdTime`。
- 审计口径（重要）：①仅记录**房间维度** SKU 更新端点产生的直播价/库存**实质变更**（值相同不记录）；②本域四个场次维度写能力（添加/排序/移除/SKU 更新）**均不产生变更记录**——把「无记录」当「无变更」会误判审计结论；③50 条是截断上限，不是全量。

```json
{"capability":"ops.live.goods.change-logs","input":{"roomId":"7200000000000000001","spuId":"2058365707555589633"},"summary":"查看该商品在直播间的变更记录"}
```
