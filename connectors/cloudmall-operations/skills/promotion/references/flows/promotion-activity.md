# 促销域 — 运营流程：活动管理与运营总览

> 查询活动、状态操作（暂停/恢复/停用/删除）、口令码预检、商品批量导入、特殊活动类型创建要点、首页汇总与拼团统计。
> 概念知识见 `references/domains/promotion-concepts.md`，状态与枚举见 `references/domains/promotion-enums.md`。
> 全部写操作遵守入口 SKILL.md 的风险档位与确认纪律。
> 对应契约：`activity-query.md`（查询/日志/统计/叠加/口令/导入解析）、`activity-action.md`（状态操作）、`overview.md`（汇总/拼团统计）。
> 创建/审核走 `promotion-review.md` 审核链。
>
> **能力标识约定**：本文为行文简洁使用模块短名（如 `activity.pause`），
> 实际调用 capability 必须使用全限定 id = `ops.promotion.` + 短名（即 `ops.promotion.activity.pause`），
> 禁止把短名直接作为 capability 传入。

---

## 促销活动管理

**场景**：查询活动、执行暂停/恢复/停用/删除、口令码预检。

### 查询活动

1. 分页：`ops.promotion.activity.search`——按 `tab`（推荐）或 `promotionStatus` 筛状态，`title` 模糊搜标题（⚠️ 字段名是 `title` 不是 keyword），`promotionSubCode` 筛类型。
2. 详情：`ops.promotion.activity.detail`（含规则/范围/人群/商品数量；商品明细用 goods-search）。
3. 统计：`ops.promotion.activity.stats`（**promotionSubCode 必填**）。
4. 叠加规则：`ops.promotion.stackable-rules`（subCode 必填，创建前核对互斥关系）。

### 状态操作（均按状态机前置校验，先查现态再执行）

1. 暂停 `pause`：普通活动仅 预热/进行中；拼团额外允许 未开始。
2. 恢复 `resume`：仅已暂停；已过结束时间报错。
3. 停用 `stop`：未开始/预热/进行中/已暂停 → 已结束，**不可逆、商业影响**。
4. 删除 `delete`：仅草稿/未开始且不在变更审核中；拼团活动不支持删除。

### 口令码活动预检

创建口令购（ENTERPRISE_PURCHASE，即唯一支持口令人群的类型）前，用 `ops.promotion.passcode.check` 校验口令码是否被占用（返回 occupied + 归一化码 + 状态）。口令码的正式预占发生在**提审或 draft=false 创建**时；草稿态创建不做占用校验；人群包在审批通过时才物化。

### 活动商品批量导入（Excel 解析）

用户给出商品清单文件（xlsx/csv，第 0 列 spuId、第 1 列 skuId；首行为表头会被跳过，数据行从第 2 行开始）时：

1. `ops.promotion.import.parse` 解析（multipart；**纯解析无落库**）→ 得到 `successItems[]`（匹配成功的 spuId/skuId）与 `errorItems[]`（行号 + 错误原因）。
2. 向用户报告错误行（商品ID不能为空 / SKU ID不能为空 / 商品不存在 / 商品已下架 / SKU不存在），确认是否仅用成功行继续。
3. **解析≠导入完成**：成功行仍需经「创建草稿（goodsList）→ 提审 → 审核」链路提交（见 `promotion-review.md`）。

### 特殊活动类型创建要点（配置结构见 `references/apis/promotion/specialty.md`）

创建/复制/编辑/改期/提审前必须读取 `references/apis/promotion/form-validation.md`；日期和模式变化后检查整个依赖链，不能以草稿保存成功替代提审校验。

- **秒杀 / 直降 / 口令购**：SKU 一口价放 goodsList[].extJson（discountType=3、discountValue 分、可选 limitPerUser），库存仍放同一行顶层 stockPolicy/totalCount；不传 rules/operationValue。
- **周期购**：periodBuyConfig（配送方案/付费区间/赠期）+ 每商品 periodBuyGoodsConfig；**不传 rules 与 operationValue**（传了直接报错——服务端独占生成规则）；草稿可先建后补配置。
- **拼团**：grouponConfig + 每商品 grouponGoodsConfig（成团人数/每人限参/开团配额）+ 拼团价（goodsList discountType=3 + discountValue 分）；标题 ≤20 字。
- **预售**：typed字段 + 每SKU顶层显式stockPolicy/totalCount（与extJson.activityStock一致）+ 每商品extJson（见 specialty.md）。全款：活动结束<发货；定金膨胀：活动起止同步定金窗口，定金结束≤尾款开始<尾款结束<发货。修改任一时间或切模式后按 form-validation 重验；保留发货不能仅延长活动时间。
- **买赠**：rules 只写门槛 + discountType=5（**不带 gifts 预留字段**）；赠品走 goodsList（goodsRole=2，extJson 带 activityStock + giftPoolItemId——先经赠品库加入取得 giftPoolItemId）。

### 参数来源

| 参数 | 来源 |
|------|------|
| 活动 id | 搜索/详情/创建草稿响应的预分配 `promotionId`（审核后用于正式对象） |
| pendingId | 搜索（PENDING 行）/创建草稿响应 |
| promotionSubCode / tab | `promotion-enums.md` 枚举字典 |
| 互斥配置 | `ops.promotion.stackable-rules` 返回值 |

### 异常处置
- `hasPendingChange=true`（变更审核中）→ 禁止删除/停用/再编辑，先走审核链处置变更草稿。
- 状态不符 → 重查详情确认现态，向用户说明当前状态与允许的操作。

---

## 运营总览

- 首页汇总 `ops.promotion.home.summary`：10 类营销工具进行中活动数量（无入参）。
- 拼团统计 `ops.promotion.groupon.stats`（单活动）/ `stats-batch`（≤批量 promotionIds）：团数、成团率相关计数。
