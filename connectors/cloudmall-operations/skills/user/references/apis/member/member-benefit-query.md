# 会员域 — 会员权益查询契约

> 概念知识：`references/domains/member-concepts.md`，状态与枚举：`references/domains/member-enums.md`；运营流程：`references/flows/member-benefit.md`；权益写操作（启停/成长加速保存/自定义权益维护/图标上传）见 `member-benefit-action.md`。
> 出参为上游**原始业务数据**（不裁剪字段）。权益分两类：**系统固定权益**（GROWTH_ACCEL 成长加速 / UPGRADE_GIFT 升级礼包 / **POINTS_BOOST 多倍积分**，不可新增/删除；成长加速与升级礼包仅整体启停 + 专属配置；**多倍积分的配置当前未开放能力**——后端虽有 points-boost 详情/保存接口，但尚未登记 capability，遇到相关需求只整理需求并引导到管理后台，不得用其他能力替代）与**自定义权益**（运营可增删改/排序/图标上传/按 id 启停）。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引：member.benefit.list 权益列表 · member.benefit.growth-accel-detail 成长加速配置详情 · member.benefit.detail 自定义权益详情

---

## ✅ 权益列表 — ops.member.benefit.list

- 固定 + 自定义权益统一返回（固定权益行兜底始终展示）

### 入参

无。

### 出参（原始返回）

`data` 为权益行数组。**关键字段**：`id`（→ 自定义权益详情/编辑/删除/启停路径参数；固定权益由系统内置）、`benefitType`（固定=GROWTH_ACCEL/UPGRADE_GIFT；自定义=CUSTOM/BIRTHDAY/SERVICE 等 → status 路径参数仅接受固定两类）、`fixed`（true=系统固定权益）、`globalEnabled`（启停状态）、`levelIds`（自定义权益关联等级，编辑回显用；固定权益为空）、`iconUrl`、`configSummary`、`lastOperator`；**格式敏感字段**：`lastUpdatedAt`（毫秒时间戳）。

### 调用示例

```json
{"capability":"ops.member.benefit.list","input":{},"summary":"查询会员权益列表"}
```

---

## ✅ 成长加速配置详情 — ops.member.benefit.growth-accel-detail

- 保存前必读（revision 来源）

### 入参

无。

### 出参（原始返回）

对象。**关键字段**：`globalEnabled`（整体开关，由 `benefit.status` 控制）、`revision`（乐观锁版本，**保存时必须回传**，Long→string）、`levels[]`（对齐**全部等级（含停用）**：`levelId`/`levelName`/`levelEnabled`/`configs[]`）；configs 子项：`configId`、`productScopeType`（ALL_PRODUCT/SPECIFIED）、`spuIds`/`skuIds`/`categoryIds`（十进制字符串数组）、`storeScopeType`（ALL_STORE/SPECIFIED）、`storeIds`、`multiplier`（1.0~9.9）、`skuCount`（该配置覆盖的 SKU 计数）、`spuSnapshots[]`（SPU+SKU 快照数组——编辑回显专用，含已被删除的商品不再出现；保存时无需回传）。

### 调用示例

```json
{"capability":"ops.member.benefit.growth-accel-detail","input":{},"summary":"查询成长加速配置详情"}
```

---

## ✅ 权益详情 — ops.member.benefit.detail

- 自定义权益编辑前必读（回显回填用）

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 权益 ID（来自 `benefit.list` 的 `id`） |

### 出参（原始返回）

单个权益对象。**关键字段**：`benefitName`、`benefitType`、`iconUrl`、`description`、`extraConfig`（JSON 字符串，`POINTS_MULTIPLIER` 型为 `{"multiplier":x}`、其余类型原样回显）、`levelIds`（关联等级全集，编辑时须整体回传）、`sortOrder`；**枚举字段**：`enabled`（0=停用 1=启用）；**格式敏感字段**：`id`/`levelIds[]`（Long→string）。

### 调用示例

```json
{"capability":"ops.member.benefit.detail","input":{"id":"7300000000000000001"},"summary":"查询自定义权益详情"}
```
