---
name: live
display_name: 云MALL直播
display_name_en: CloudMall Live
description: 本域定位：直播运营（直播间/主播/挂载），非商品/交易管理。直播域运营：直播间（查询/编辑/删除/封禁筛选）、主播（简表/关联直播间）、直播分类（创建/编辑/启停/删除）、讲解场次（分页/编辑/取消排期）、场次商品（添加/排序/移除/直播价/直播库存/变更记录）、回放记录、直播统计看板（总览/趋势/排行）、场次复盘数据（详情/五分钟趋势/商品转化）。防混淆：商品价格库存→商品域；订单/售后→交易域；优惠券/秒杀→促销域；会员积分→用户域。实时开播/关播/禁播/推流/IM/内容审核未开放。
description_zh: 按任务类型路由最小加载路径，通过已登记 capability 执行直播域查询与写操作；实时链路、凭证和未登记操作只说明边界，不承诺执行。
description_en: Task-typed minimal loading paths for live-domain operations (rooms, anchors, categories, sessions, session goods, replays, and stats); execute registered capabilities for queries and bounded writes, and only describe boundaries for real-time controls and credentials.
allowed-tools: cloudmall_query,cloudmall_action
version: 0.3.1
author: 云MALL
---

# 云MALL直播域运营技能包

> 本技能按**任务类型路由最小加载路径**；下方能力路由表是本域唯一的 capability → 契约文件索引。写操作的前置条件/状态约束在对应契约锚点内，本表不重复。
> 本域没有既有直播参考文档。领域规则来自当前 Java 运行时实现与运营前端的交叉核验，禁止用直播行业常识补写状态迁移或字段语义。

## 业务目的定位（本域是什么）

> 本域的业务本质是**管理直播运营——直播间/主播/商品挂载/数据复盘是"直播卖货"的运营工具**。
> 不是商品管理（商品域）、不是交易执行（交易域）。
> 简单判断：说"直播/主播/直播间/挂商品/开播/复盘"→本域。

## 任务类型路由

| 任务类型 | 最小加载路径 |
|---------|-------------|
| **简单查询**（查直播间/主播/分类/场次/场次商品/回放/统计看板/复盘数据现值） | 能力路由表 → 定位契约文件 → 读目标 `## ✅ capability` 锚点 → 直接调用查询执行器（跳过 L1/L2） |
| **写操作**（编辑/删除直播间、分类管理、场次编辑/取消、场次商品添加/排序/移除、SKU 直播价/库存） | 通用约定 + 风险档位（本文件）→ `references/flows/live.md` 对应流程段（排期/商品编排/分类维护）→ 契约文件锚点 → 按风险档位确认后调用 |
| **概念咨询/异常排查**（状态含义/操作前置/枚举值/回放状态/统计口径） | `references/domains/live-enums.md`（状态机与枚举字典）→ 契约文件锚点 |
| **概念咨询/异常排查**（实体关系/数据口径/统计看板与场次数据中心差异/实现缺口纪律） | `references/domains/live-concepts.md`（实体模型与业务规则）→ 契约文件锚点 |

## 能力路由表（唯一索引）

> 所有 capability 完整 id = `ops.` + 下表短名（如 `ops.` + `live.session.search`）。契约文件均在 `references/apis/live/` 下。🔴 = 风险档位高危（见下方操作风险档位）。

### 查询能力（Capability 查询执行器）

| 契约文件 | capabilities |
|---|---|
| `room-anchor-category-query.md` | live.room.search 直播间分页 · live.anchor.brief-list 主播简表 · live.anchor.rooms 主播关联直播间 · live.category.list 分类列表 |
| `session-goods-query.md` | live.session.search 场次分页 · live.room.sessions 直播间全部场次 · live.goods.room-list 直播间商品列表 · live.goods.session-list 场次商品列表 · live.goods.change-logs 商品变更记录 |
| `replay-stat-data.md` | live.replay.search 回放记录分页 · live.stat.overview 统计总览 · live.stat.trend 统计趋势 · live.stat.rank 直播间排行 · live.stat.sessions 统计场次分页 · live.data.session-search 场次数据分页 · live.data.session-detail 场次数据详情 · live.data.session-trend 场次五分钟趋势 · live.data.session-goods 场次商品转化分页 |

### 写能力（Capability 写操作执行器）

| 契约文件 | capabilities |
|---|---|
| `room-anchor-category-action.md` | live.room.update 编辑直播间 · live.room.delete 删除直播间 🔴 · live.category.create 创建分类 · live.category.update 编辑分类 · live.category.update-status 启停分类 · live.category.delete 删除分类 🔴 |
| `session-goods-action.md` | live.session.update 编辑场次 🔴 · live.session.cancel 取消场次 🔴 · live.session-goods.add 添加场次商品 🔴 · live.session-goods.sort 排序场次商品 🔴 · live.session-goods.remove 移除场次商品 🔴 · live.session-goods.update-sku 更新SKU直播价库存 🔴 |

## 通用约定（直播域共享）

- 查询调用 `当前运行时的 Capability 查询执行器`，写操作调用 `当前运行时的 Capability 写操作执行器`；输入统一为 `{capability,input,summary}`。只调用能力路由表已登记标识。
- 入参字段名以契约参数表为准，**大小写敏感**；未读到目标能力的参数表之前，不要凭直觉或惯例拼写参数名（拼错只能得到缺参报错再返工）。
- 所有业务 ID，包括直播间、主播、场次、分类、SPU、SKU、会员 ID，均使用十进制字符串，禁止转为 Number。
- 身份由连接授权绑定；不询问、不传入租户、账号、令牌、服务名、内部地址或权限码。查询需 `mall.query`，写入需 `mall.action`，仍受当前账号实时业务权限限制。
- 分页从 `pageNum=1,pageSize=20` 起步；建议 `pageSize<=100`。失败不是空数据。
- 成功信封为 `{capability,data,traceId}`；`data` 是原始业务结果。错误按 `AUTH_REQUIRED`、`SCOPE_INSUFFICIENT`、`PERMISSION_DENIED`、`INPUT_INVALID`、`UPSTREAM_ERROR`、`UPSTREAM_TIMEOUT` 处理。
- 写操作单次提交且不自动重试。执行前读现态，执行后回读；超时表示结果不确定，先回读再决定是否重试。
- 日期时间严格使用契约指定格式；状态码为整数；布尔值只能是 `true/false`。金额单位按字段契约解释：`paidAmountFen` 与统计列表的 `totalAmount` 均为分。
- Java 当前缺少的交叉字段校验，不得描述成服务端保证；由调用纪律在提交前补齐。

### 操作风险档位（写操作前必读）

| 档位 | 已开放操作 | 强制纪律 |
|---|---|---|
| 🔴 不可逆 | 删除直播间、分类；移除场次商品 | 确认对象名称、ID、影响范围；回读或用列表确认 |
| 🔴 商业影响 | 场次排期编辑/取消；直播价、直播库存；场次商品增删排序 | 用户明确确认排期、商品/SKU 清单、价格和库存；不得代填 |
| 🟡 配置写 | 编辑直播间；创建/编辑分类；启停分类 | 先读重名或现态，执行后回读 |

**字段确认红线（禁止 AI 编造）**：直播价（livePrice）与直播库存（liveStock）数值、排期起止时间（planStartTime/planEndTime）与直播价有效时长（priceValidMinutes）、取消场次原因（reason）、场次商品清单（items 的 SPU/SKU 全集）、排序完整清单（sortedSpuIds 全集）、直播间标题/封面/分类/标签/排序值、分类名称与排序值——必须由用户明确给出或从查询结果回读，禁止代填或编造。

### 调用前完整性检查（强制）

1. 展开读取入参表的全部叶子字段；出现嵌套结构（如 `items[]`、`sortedSpuIds[]`、`skus[]`）继续读取其字段说明。
2. 区分必填、条件必填与可选：场次编辑 body 必须存在（可为 `{}`，整体省略会 400）；SKU 直播价/库存至少一项非 null（全 null 幂等无效果）；取消场次 body 可整体省略。
3. 枚举使用 Layer 1 字典精确值并保持大小写；状态类字段确认是整数 code（直播间五态/场次八态/回放四态/分类 0/1/封禁 0/1）。
4. 确认时间格式（场次计划起止为 ISO 本地日期时间如 `2026-09-20T20:00:00`；回放与场次数据筛选为 `yyyy-MM-dd HH:mm:ss`；统计日期为 `yyyy-MM-dd`，建议成对传入）与金额单位（`paidAmountFen`/`totalAmount` 均为分）；ID 一律十进制字符串。
5. 确认对象当前状态（场次编辑仅状态 0 已排期；取消仅 0已排期/1准备中；直播间直播中/暂停中不代为编辑；删除分类前确认 `roomCount=0` 并用直播间分页复核）。
6. 全量/完整清单语义的操作必须先读现态回填：商品排序提交完整、不重复、与现有集合一致的 `sortedSpuIds`（只传移动项会产生排序值碰撞）；分类编辑必须显式携带原 `sortOrder`（省略或 null 会重置为 0）；编辑类操作只传用户要求变更的字段。

## 未开放（不调用，只整理需求）

| 未开放业务能力 | 原因与处理 |
|---|---|
| IM 状态、实时在线数、操作记录、成员禁言/踢出、全员禁言、群公告、补建 IM 群 | 外部实时态与异步最终一致链路，人员管控副作用强；只说明需在直播运营台处理 |
| 创建直播间 | 创建时会建立外部 IM 群并生成推流资源，返回流与群标识；不是纯静态写入，当前不开放 |
| 创建场次 | 创建结果包含 `streamName` 流标识；为避免敏感流信息进入 DIRECT 原始返回，当前不开放 |
| 推流地址生成/轮换、开播准备、推流凭证与流信息 | 防盗链敏感凭证；不得查询、展示、代为轮换 |
| 私有回放播放地址/临时播放凭证 | 短时授权凭证；只开放回放记录，不开放播放地址 |
| 开播、关播、结束、暂停恢复、禁播/封禁 | 实时生命周期控制，误操作影响在播链路；未登记，不得用其他能力替代 |
| 直播中商品讲解切换 | 实时导购状态；未开放 |
| 旧直播间维度商品添加、排序、移除、价格/库存更新 | 旧兼容模型会模糊具体场次；写入只开放场次维度。运营前端现行房间页仍在使用 room 维度写入（双轨并存），本技能包一律走场次维度；用户要求房间维度操作时转直播运营台 |
| 删除回放 | 不可恢复且涉及外部媒资分片清理 |
| 场次数据文件导出 | 文件流型导出（CSV 二进制流）；产品决策仅开放 URL 型导出，走管理后台 |
| 直播间详情、场次详情 | 原始详情混有推流、流名、群组或回放等敏感字段；用已开放安全列表投影定位对象 |
| 内容审核查询与单条处理 | 查询原样包含 `streamName` 和审核截图，DIRECT 无法裁剪敏感字段；单条处理还会决定实时处置，均不开放 |
| 内容审核批量处理 | Java 运营端未实现批量处理，不得描述为可执行待开放能力 |
| 主播分页/详情/创建/编辑 | Java 直接复用持久化实体，原始返回含租户与审计字段，写入也存在额外字段绑定风险；需 Java 补专用保存 DTO 与安全 VO 后再开放 |
| 主播启停/删除 | 安全分页/详情未开放，无法完成读现态与写后回读闭环；待 Java 安全 VO 补齐后再开放 |
| 回调、开放网关、应用端、内部库存与埋点采集 | 非运营开放能力边界 |

用户命中未开放意图时，明确说明当前不能执行，并整理对象、期望动作和原因供人工处理；不得猜 capability。

直播间/主播查询中的封面、头像等媒体字段可能是约 30 分钟有效的预签名预览 URL：只用于当前已授权运营会话内预览，不复述完整签名参数、不外发。回放记录的 `coverUrl` 是未经签名的原始 URL（实现未走签名链路），同样按媒体纪律不得外发。它不同于完全未登记的推流凭证、流名、群组标识和回放播放凭证，后者不属于开放能力。
