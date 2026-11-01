# 直播域 — 回放、统计与场次数据查询契约

> 概念知识：`references/domains/live-concepts.md`，状态与枚举：`references/domains/live-enums.md`；运营流程：`references/flows/live.md`。
> 本文件全部为只读能力。回放播放凭证、数据文件导出和内容审核查询/处理均未开放。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引：live.replay.search 回放记录分页 · live.stat.overview 统计总览 · live.stat.trend 统计趋势 · live.stat.rank 直播间排行 · live.stat.sessions 统计场次分页 · live.data.session-search 场次数据分页 · live.data.session-detail 场次数据详情 · live.data.session-trend 场次五分钟趋势 · live.data.session-goods 场次商品转化分页

---

## ✅ 回放记录分页 — ops.live.replay.search

- 入参：`pageNum`/`pageSize` Integer 可选（服务端默认 1/10）；`keyword` String 可选；`anchorId` String 可选；`replayStatus` Integer 可选，仅 0无/1生成中/2可回放/3已过期——不传时隐含排除「无回放(0)」记录，显式传 0 才会查出无回放记录；`startTime`/`endTime` String 可选，格式 `yyyy-MM-dd HH:mm:ss`。
- 出参：分页 `records[]`；关键字段 `roomId`、`roomCode`、`roomTitle`、`anchorId`、`anchorNickname`、实际起止、时长秒、`replayStatus`、`replayFileId`、`coverUrl`（⚠️ 回放封面为**原始 URL 直出、未经预签名**——与本域直播间分页封面/主播头像的 30 分钟预签名口径不同，仍按媒体纪律不得外发）。记录“可回放”不代表播放地址已纳入开放能力。

```json
{"capability":"ops.live.replay.search","input":{"pageNum":1,"pageSize":20,"replayStatus":2,"startTime":"2026-09-01 00:00:00","endTime":"2026-09-10 23:59:59"},"summary":"查询时间范围内已生成的回放记录"}
```

---

## ✅ 统计总览 — ops.live.stat.overview

- 入参为空。
- 出参：`totalRooms`、`totalViewers`、`totalComments`、`totalGoodsClicks`，SQL 聚合经 COALESCE 补 0，四字段恒返回。注意 `totalRooms` 是**统计记录数**（每场次结束落一行统计行，含旧房间级历史行），不是直播间去重数。

```json
{"capability":"ops.live.stat.overview","input":{},"summary":"查看直播运营总览"}
```

---

## ✅ 统计趋势 — ops.live.stat.trend

- 入参：`startDate`、`endDate` String 可选，格式 `yyyy-MM-dd`；两者均不传时服务端默认近 30 天；只传单边时另一边独立取默认（`startDate` 缺省=29 天前、`endDate` 缺省=今天），可能产生意外范围——建议成对传入。`startDate > endDate` 不报错、返回空数组。
- 出参数组：`date`、`viewers`、`comments`。按天聚合，按**统计快照落库时间**分桶（非场次开播时间），范围内无数据的日期补 0 返回。

```json
{"capability":"ops.live.stat.trend","input":{"startDate":"2026-09-01","endDate":"2026-09-10"},"summary":"查看近十日直播观看与评论趋势"}
```

---

## ✅ 直播间排行 — ops.live.stat.rank

- 入参为空。
- 出参数组：`roomId`、`roomTitle`、`anchorName`（房间无场次时为空串）、`totalViewers`、`totalComments`。按观看数降序取**前 10 条统计行**（同一直播间多场次可重复出现）。排行顺序采用原始返回，不自行更换指标排序。

```json
{"capability":"ops.live.stat.rank","input":{},"summary":"查看直播间运营排行"}
```

---

## ✅ 统计场次分页 — ops.live.stat.sessions

- 入参：`pageNum`/`pageSize` Integer 可选（服务端默认 1/10，无上限钳制）；`startDate`/`endDate` String 可选，格式 `yyyy-MM-dd`——过滤基准是**统计快照落库时间**（场次结束时写入），不是场次计划/实际开播时间。
- 出参：分页记录；关键字段 `roomId`、`roomTitle`、`anchorName`、观看、峰值在线、评论、点赞、商品点击、`totalOrders`、`totalAmount`（**单位为分**，来源支付事件实付金额累加）、时长秒、创建时间。该旧统计投影以直播间字段命名，不等同于数据中心的场次明细。

```json
{"capability":"ops.live.stat.sessions","input":{"pageNum":1,"pageSize":20,"startDate":"2026-09-01","endDate":"2026-09-10"},"summary":"分页查看直播统计明细"}
```

---

## ✅ 场次数据分页 — ops.live.data.session-search

- 入参：`pageNum`/`pageSize` Integer 可选，默认 1/10，`pageSize` 钳制 1..100；`keyword` String 可选；`sessionId`/`roomId` String 可选；`status` Integer 可选，取场次八态 0..7（此处为裸等值过滤，非法值不报错、返回空结果——与场次分页的枚举前置校验不同）；`planStartTimeBegin`/`planStartTimeEnd` String 可选，格式 `yyyy-MM-dd HH:mm:ss`。
- 出参分页：`records[]` 含 `sessionId/sessionTitle/roomId/roomTitle/roomCode/status/statusDesc/planStartTime/actualStartTime/viewerUv/statStatus`。`viewerUv` 未采集时字段整体缺失（null 字段序列化省略，语义等价于「未采集」）；`statStatus` 为 COLLECTING/FINALIZING/FINALIZED 或字段缺失。

```json
{"capability":"ops.live.data.session-search","input":{"pageNum":1,"pageSize":20,"status":4,"planStartTimeBegin":"2026-09-01 00:00:00","planStartTimeEnd":"2026-09-10 23:59:59"},"summary":"查找已结束场次的复盘数据"}
```

---

## ✅ 场次数据详情 — ops.live.data.session-detail

- 入参：`sessionId` String 必填，来自数据分页。
- 出参：基础字段加主播、实际结束、时长、统计时间与延迟、观看 UV/PV、当前/峰值在线、平均观看秒、点赞/评论/分享、商品点击 UV/PV、下单人数、支付订单数、`paidAmountFen`。可空指标不补 0；金额以分返回。无统计行时 `statStatus` 恒回 `COLLECTING`（不回缺失），且点赞/评论/支付等指标回退为实时值——与分页行的缺失语义不同。`FINALIZED` 后若再收到支付事件会重开为 `FINALIZING` 做对账修正，终态不是绝对终态。

```json
{"capability":"ops.live.data.session-detail","input":{"sessionId":"7300000000000000001"},"summary":"查看秋季专场核心复盘指标"}
```

---

## ✅ 场次五分钟趋势 — ops.live.data.session-trend

- 入参：`sessionId` String 必填。
- 出参数组：`bucketTime`、`viewerUv`、`viewerPv`、`onlinePeak`、`interactionCount`、`goodsClickUv`、`paidOrderCount`、`paidAmountFen`。除 `onlinePeak`（该桶观察到的在线峰值）外，各指标均为**桶内增量**（负差截断为 0），可跨桶求和；`interactionCount` 为点赞+评论+分享增量之和。不能求和 `onlinePeak` 当总在线。

```json
{"capability":"ops.live.data.session-trend","input":{"sessionId":"7300000000000000001"},"summary":"查看秋季专场五分钟趋势"}
```

---

## ✅ 场次商品转化分页 — ops.live.data.session-goods

- 入参：`sessionId` String 必填；`pageNum`/`pageSize` Integer 可选（服务端默认 1/10，`pageSize` 钳制 1..100）。
- 出参分页：`liveGoodsId`、`spuId/goodsName/goodsCoverUrl`、点击 UV/PV、下单人数、支付订单数、`paidAmountFen`（分）。**商品名称/封面为当前商品资料优先**：SPU 仍存在时以商品中心当前名称/主图返回（统计快照本身不落名称/封面）；仅当商品中心异常或 SPU 已删除时为空。排序为支付金额降序、其次点击降序。

```json
{"capability":"ops.live.data.session-goods","input":{"sessionId":"7300000000000000001","pageNum":1,"pageSize":20},"summary":"查看秋季专场商品转化表现"}
```
