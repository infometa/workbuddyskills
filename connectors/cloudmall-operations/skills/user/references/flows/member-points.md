# 会员子域 — 积分体系流程（明细/活动/抵扣）

> 对应契约：`apis/member/point-flow.md`（积分明细）、`apis/member/points-activity-query.md` / `apis/member/points-activity-action.md`（积分活动）、`apis/member/points-deduct-query.md` / `apis/member/points-deduct-action.md`（积分抵扣）；概念知识：`references/domains/member-concepts.md`，状态与枚举：`references/domains/member-enums.md`；写操作共同纪律（风险档位/超时不重试）见入口 Skill 护栏段。

## 积分明细查询

**场景**：租户维度排查积分发放/消耗记录（区别于单会员流水）。

### 操作步骤

1. `ops.member.point-flow.search`：时间范围（yyyy-MM-dd HH:mm:ss；**跨度 ≤180 天**，只传单边时间会被静默忽略须成对传）/手机号/tradeType/channelId 筛选
2. 单条详情：`point-flow.detail`（按 search 返回的流水 id）
3. 口径说明：租户维度默认过滤 freeze/rollback 中间态与系统平台流水（uid=PLATFORM）；显式指定 tradeType=freeze/rollback 时中间态不再被排除（审计用）；会员维度流水（`ops.member.member.points-flows`）已过滤 freeze/rollback 中间态；积分调整产生的流水 activityDesc 为运营调整

## 积分活动管理

**场景**：消费送积分活动的创建、编辑与启停（商业影响）。

### 操作步骤

1. **看列表**：`ops.member.points-activity.search`（仅分页，无筛选）→ 取 `records[].id`
2. **创建**：`points-activity.create`——activityName（≤50 字，同租户唯一）+ pointsPerYuan（≥1）+ itemConfigType（0 全部商品 / 1 按类目带 categoryItems / 2 按商品带 productItems[{skuId}]）；创建后为**停用**态
3. **编辑** 🔴（部分更新）：`points-activity.update`
   - 未携带的数值/规则字段（limitPeriod/dailyPointsLimit/expiry*/ruleContent 等）**保留旧值**（不置空）；编辑前仍建议先 `points-activity.detail` 回读确认现值
   - items 配置**先删后增**：可获/不可获积分清单须按意图完整提交（只传新增会清掉既有清单）；不可获维度始终按提交内容保存
4. **启停**：`points-activity.enable` / `disable`（重复启用/停用报错）
5. **删除** 🔴：`points-activity.delete`（仅停用态可删）
6. **核验**：search/detail 回读

### 参数来源

| 参数 | 来源 |
|------|------|
| itemConfigType=1 的 categoryCode | 商品域类目树（ops.product.category.tree） |
| itemConfigType=2 的 skuId | 商品域 SKU 搜索（ops.product.sku.search） |

## 积分抵扣配置

**场景**：下单积分抵现规则（商业影响）。

### 操作步骤

1. **读现配置**：`ops.member.points-deduct.config`（无配置时返回默认值）
2. **保存** 🔴：`points-deduct.config-save`
   - enabled=true 且 minDeductUnit 非空时完整校验：minDeductUnit>0、exchangeAmount>0 两位小数、productScope=ALL|SPECIFIED（SPECIFIED 时 products 清单必填）
   - **SPECIFIED 编辑必须先读 `points-deduct.config` 回填全部既有商品清单**（保存为商品关联先清后插，只传新增会静默清空旧商品）
   - 汇率数值（minDeductUnit/exchangeAmount）必须用户明确给出，禁止 AI 编造
   - 每单最多/最少抵扣与金额比例均有开关+数值对
   - 商品清单 products[{productId, productName, spuCode, mainImage, minPrice}]——productId 为商品域 SPU ID
   - 关闭抵扣（enabled=false）只传开关：数值规则保留，但 **SPECIFIED 商品关联仍会被清空**（关联表每次保存先清后插）——需保留清单必须同时回传 productScope=SPECIFIED + 完整 products
3. **核验**：回读 `points-deduct.config`
