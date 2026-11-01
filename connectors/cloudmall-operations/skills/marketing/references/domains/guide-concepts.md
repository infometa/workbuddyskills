# 营销域 — 导购体系实体模型与业务概念

> 实体模型、规则结构语义、业务规则要点。
> 状态机迁移与枚举值查 `marketing-enums.md`；能力契约见 `references/apis/marketing/`，操作流程见 `references/flows/`。

---

## 核心实体
### 导购
- 主档：`id`、`name`/`phone`（租户内唯一）、`storeId` 归属门店、`levelId`、`weworkId`、`joinTime`（yyyy-MM-dd）、`gender`（0 未知 / 1 男 / 2 女）。
- 状态：`pending` 待激活（激活走**导购端小程序**，运营端无激活端点）→ `active` 在职 → `disabled` 已停用 → `archived` 已归档（终态）。
- 统计口径注意：月度接口 `customerCount` 为本月新增客户数；总量接口 `customerCount` 为总客户数。
- **编辑含调店语义**：`storeId` 与现值不同即触发调店流程（客户归属批量处理）。

---

### 导购等级与绑定设置
- 导购等级：单租户最多 **6 个**；`levelSort` 越大等级越高；等级功能关闭（enabled=false）时等级列表返回空数组；删除前置：该等级下无非归档导购。
- 绑定设置四区域（全量覆盖式保存）：shareScene 分享场景（自动绑定开关/升级专属触发场景/生效客户范围）、autoAssign 自动分配（方式/策略/就近半径）、expire 有效期（共享 1..30 天默认 7 / 专属永久或指定天数/自动续期）、customerWall 客户墙（允许换绑/解绑）。

---

### 客户归属（公共池与绑定关系）
- **关系类型双轨**：`share_guide` 共享导购（一客户至多一个）/ `exclusive_guide` 专属导购（一客户至多一个）。
- 绑定方式六种：share_bind 分享绑定 / upgrade_exclusive 升级专属 / customer_switch 客户换绑 / nearest_store 就近门店归属 / store_round_robin 门店轮流分配 / admin_assign 运营指定。
- 失效原因：expired 锁客期到期 / manual_unbind 手动解绑 / transferred 归属转移 / guide_disabled 导购停用 / customer_switch 客户切换 / manual_release 手动释放 / new_binding_replaced 新绑定替换。
- **公共客户池**：客户被解绑且无其他活跃绑定关系时自动入池；入池原因（enterReason）：customer_switch / customer_unbind / expired / guide_disabled / admin_release / store_transfer；被分配后即从池列表消失。
- 客户 360 画像：基本信息 + 导购关系 + 消费概要 + 偏好标签（tags 本期恒为空数组）；消费概要在交易中心查询失败时降级为全零值。

---

### 目标计划
- 考核周期容器（仅周期信息）：`periodType`（monthly 月度 period=1..12 / quarterly 季度 period=1..4）、`year`、`startDate`/`endDate` 由周期自动计算、`status` 由定时任务按日期流转。
- 同租户同周期唯一；**导购目标行独立管理**（空白行 → 填值/按上期 N% 填充）；按上期填充为**覆盖式**（无上期数据的导购目标置 0）。

---

### 提成规则与明细
- 规则决定订单完成时导购提成计算口径：`calculationType`（percentage 按比例 / category 按品类差异化 / ladder 阶梯式 / combined 组合 / fixed 固定金额）、`scopes`（guide/level/store × all/specified/excluded）、`items`（order_rate/category/cumulative_ladder/fixed_per_order）、`priority`（**数字越小越优先**，订单按优先级升序取首个范围匹配的生效规则）。
- 规则状态：`draft`/`active`/`expired` 三态按时间**动态推导**（不落库）；`disabled` 为存储态（手动停用写入），**停用无重新启用通道**。
- `commissionRate` 为小数比例（0.05=5%）；fixed 规则为元金额；cumulative_ladder 的 `itemValue` 阶梯门槛以**万元数值**录入。
- 明细由订单完成事件自动落账（不可手工创建/改金额）；结算状态 pending/settled。

---

### 业绩方案与明细
- 方案决定业绩取值口径（按实收金额）与分享/专属导购分成比例（**两比例之和必须精确等于 1**）。
- **同一时刻全租户仅一个方案生效**：启用新方案自动将当前生效方案置为未生效；生效中方案不可编辑/删除；系统至少保留一个方案。
- 明细一单一条（分享导购/专属导购各自业绩），按当前生效方案自动计算落账。

---

### 导购运营看板
- 导购模块的聚合分析视图：核心指标统计（`dashboard.stats`）、双榜排名（`ranking-top` 头部 / `ranking-bottom` 尾部，识别低绩效）、双趋势（`performance-trend` 业绩 / `customer-trend` 客户）、当前生效方案 ID（`active-plan`，返回 **Long 型方案 ID**，非方案对象）。
- 时间参数体系与业绩明细查询不同：看板用 `timeRange` 枚举（today/week/month/quarter，**小写**）+ `granularity`（day/week/month，默认 day），**不是** startTime/endTime 时间窗。

---

### 推广任务
- 面向导购的任务下发载体：`taskType`（new_product 新品推广 / activity 活动推广 / daily 日常任务）、`targetCustomer`（目标人群）、`relatedContent`（关联内容：product/promotion/coupon/content/page）、`dispatch`（派发配置：范围/目标行为/频次/时间段）。
- 执行记录由系统按派发范围**异步批量生成**（在职导购）；active 状态重复下发会按当前范围再次生成执行记录（可能重复）。

---

### 话术
- 多条内容块话术（1..9 块），按分组管理，分享计数存于缓存计数器；置顶优先展示。

---

### 业务素材 / 内容素材 / 素材分组
- **业务素材**：对既有业务对象的引用（coupon/promotion/page/game/live/grass 六类，sourceId=券模板 ID/促销活动 ID 等），控制导购工作台展示；优惠券/促销标题由后端实时回源富化。
- **内容素材**：运营原创图文/视频（contentType：image/poster/video/image_poster/custom），带发布生命周期（draft/published/unpublished）与传播统计（收藏/分享/浏览/下单/导购数/门店覆盖）。
- **素材分组**：content_material 与 speech **各自独立**的两级分组树（同父级子分组≤10）；话术查询的 groupId **不含子分组**（与内容素材"含子分组"语义不同）。

---

## 业务规则要点

- **导购停用必须处置客户归属**：transferMethod 三选一必填；调店（update 传 storeId 与现值不同）同样触发客户归属批量处理——只在用户明确要求调店时才传 storeId。
- **目标计划**：同周期唯一；仅未开始可删（级联删除目标行）；按上期填充为覆盖式写（无上期数据的导购置 0）；清空目标值不可逆但目标行保留。
- **业绩方案互斥**：全租户同一时刻仅一个生效；启用即自动停用原生效方案；分成比例之和必须精确等于 1。
- **业绩方案/提成规则/明细均为系统自动落账**：运营侧只做规则配置、查询与批量标记结算，不可手工创建或修改明细金额。
