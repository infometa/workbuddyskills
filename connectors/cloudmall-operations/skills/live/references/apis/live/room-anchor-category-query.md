# 直播域 — 直播间、主播与分类查询契约

> 概念知识：`references/domains/live-concepts.md`，状态与枚举：`references/domains/live-enums.md`；运营流程：`references/flows/live.md`。
> 出参为原始业务数据；未列展示字段原样透传。ID 一律十进制字符串。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引：live.room.search 直播间分页 · live.anchor.brief-list 主播简表 · live.anchor.rooms 主播关联直播间 · live.category.list 分类列表

---

## ✅ 直播间分页 — ops.live.room.search

- 入参：`pageNum` Integer 可选（服务端默认 1）；`pageSize` Integer 可选（服务端默认 10，无上限钳制，建议 1..100）；`status` Integer 可选，只能 0待开播/1直播中/2暂停/3已结束/4已过期（错误值不报错、返回空结果）；`category` String 可选，分类编码；`banStatus` Integer 可选，0正常/1封禁；`keyword` String 可选，匹配标题或房间码。
- 出参：分页 `records[]`；关键字段 `id`、`roomCode`、`title`、`status/statusDesc`、`category/categoryDesc`、`tags`、`banStatus`、`banReason`、计划/实际时间、`subscribeCount`、`sortOrder`、`anchorId`、`anchorNickname`、`anchorAvatarUrl`、`createdTime`。运营端列表**不投影** `currentSessionId`/`nextSessionId`/`defaultAnchorId`（实体字段，列表恒不返回）；当前/下一场次经 `ops.live.room.sessions` 获取。封面、主播头像等媒体字段可能是约 30 分钟有效的预签名 URL，仅限当前授权运营预览，不复述完整签名参数或外发（COS 未配置的环境降级为原始 URL）。

```json
{"capability":"ops.live.room.search","input":{"pageNum":1,"pageSize":20,"status":0,"keyword":"云MALL新品"},"summary":"查找待开播的新品直播间"}
```

---

## ✅ 主播简表 — ops.live.anchor.brief-list

- 入参为空。
- 出参：数组，每项三键——`id`（十进制字符串）、`nickname`、`avatarUrl`（约 30 分钟有效的头像 COS 预签名 URL，仅限当前授权运营预览，不复述完整签名参数或外发；无头像时为空串）。仅返回启用状态主播，按昵称升序；用于场次选择，不据此判断完整状态或会员绑定。

```json
{"capability":"ops.live.anchor.brief-list","input":{},"summary":"列出可选择的主播"}
```

---

## ✅ 主播关联直播间 — ops.live.anchor.rooms

- 入参：`anchorId` String 必填；`pageNum`/`pageSize` Integer 可选（服务端默认 1/10）。
- 出参：关联直播间分页；关联口径为直播间主播、默认主播或场次主播三个维度之一命中。出参字段集小于直播间分页（`tags`/`banStatus`/`banReason`/主播信息恒缺失）。删除/禁用主播前必须查询（服务端删除主播时会校验存在关联直播间并拒绝）。

```json
{"capability":"ops.live.anchor.rooms","input":{"anchorId":"7100000000000000001","pageNum":1,"pageSize":20},"summary":"查看主播关联的直播间"}
```

---

## ✅ 分类列表 — ops.live.category.list

- 入参 `enabledOnly` Boolean 可选，默认 false。
- 出参数组：`id`、`code`、`name`、`sortOrder`、`status`(0/1)、`roomCount`（字符串——全局 Long→String 序列化对计数字段同样生效，比较时先转数字）、时间。创建直播间时用 `code`，不能传名称或分类 ID。该接口有初始化副作用：租户首次调用会种子 6 个默认分类并把历史空分类直播间迁移到「其他」。

```json
{"capability":"ops.live.category.list","input":{"enabledOnly":false},"summary":"列出直播分类及启停状态"}
```
