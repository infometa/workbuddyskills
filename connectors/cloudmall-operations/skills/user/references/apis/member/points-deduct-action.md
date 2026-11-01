# 会员域 — 积分抵扣写操作契约

> 概念知识：`references/domains/member-concepts.md`，状态与枚举：`references/domains/member-enums.md`；运营流程：`references/flows/member-points.md`；抵扣现值读取（配置查询/回填来源）先读 `points-deduct-query.md`。
> 所有 ID 均为十进制字符串；写操作须遵守入口 Skill 的风险档位、明确确认和回读纪律。
> **工具**：`当前运行时的 Capability 写操作执行器`（`mall.action`）——单次提交、不自动重试，超时或结果不确定先回读现态再决定下一步。
> 能力索引：member.points-deduct.config-save 保存积分抵扣配置 🔴

---

## ✅ 保存积分抵扣配置 — ops.member.points-deduct.config-save

- 🔴 商业影响——upsert（**商品关联先清后插**：SPECIFIED 编辑必须先读 `points-deduct.config` 回填全部既有商品清单，只传新增会静默清空旧商品）；**enabled=true 且 minDeductUnit 非空时执行完整规则校验**；**汇率数值（minDeductUnit/exchangeAmount）必须用户明确给出，禁止 AI 编造**

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| enabled | Boolean | ✅ | 积分抵扣功能开关 |
| minDeductUnit | Integer | 条件 | 最小抵扣单位（积分；enabled=true **且非空**时须 >0；enabled=true 但不传时不校验直接放行） |
| exchangeAmount | Number | 条件 | 兑换金额（元，>0，精确 2 位小数） |
| productScope | String | 条件 | `ALL` / `SPECIFIED`；SPECIFIED 时商品清单必填 |
| products | Array | 条件 | 指定商品清单（含展示信息）；**商品落库只认此字段** |
| products[].productId | String | ✅ | 商品 SPU ID（来自商品域） |
| products[].productName / spuCode / mainImage / minPrice | — | — | 商品展示信息（冗余存储，后端**不自动回填**——只传 productId 会造成空展示） |

> **productId 预检配方（跨域直查，无需加载商品域技能——本条已提供完整调用契约，直接按 capabilityId 调用即可）**：保存前先调查询能力 `ops.product.spu.detail`（入参 `{"spuId":"<商品SPU ID>"}`），确认商品存在并取 `spuName`（→productName）、`images[0]`（→mainImage）、`minPrice` 填充展示字段。返回「商品不存在」= 该 ID 未在商品域登记，**禁止直接保存**（保存不校验存在性，不存在的 ID 会落库成空展示关联），应向用户核对 ID。`spuCode` 详情无此字段可不传。
| productIds | String[] | — | ⚠️ 兼容字段**不落库**（仅参与空校验）：只传 productIds 不传 products 会**静默清空**全部商品关联——商品清单一律用 products |
| maxDeductEnabled | Boolean | — | 每单最多抵扣开关 |
| maxDeductPoints | Integer | 条件 | 每单最多抵扣积分数（开启时**应必传**——DTO 无 @NotNull，漏传**不报错落 null**；≥1） |
| minDeductEnabled | Boolean | — | 每单最少抵扣开关 |
| minDeductPoints | Integer | 条件 | 每单最少抵扣积分数（开启时**应必传**——同上漏传落 null；≥1；min 与 max 同开时须 min ≤ max；且 minDeductPoints ≥ minDeductUnit） |
| amountRatioEnabled | Boolean | — | 抵扣商品金额比例开关 |
| amountRatioPercent | Integer | 条件 | 抵扣比例 1~100（开启时必填） |

### 出参（原始返回）

`data` 为 `null`；回读 `points-deduct.config` 核验。**关闭抵扣（enabled=false）只传开关时：主配置数值规则保留（未携带字段不更新），但商品关联表每次保存先清后插、SPECIFIED 存量清单会被清空**——如需保留指定商品清单，关闭时也必须同时回传 `productScope=SPECIFIED` + 完整 `products`。

### 调用示例

```json
{"capability":"ops.member.points-deduct.config-save","input":{"enabled":true,"minDeductUnit":100,"exchangeAmount":1.00,"productScope":"ALL","maxDeductEnabled":true,"maxDeductPoints":5000},"summary":"开启积分抵扣：100积分抵1元，全商品，每单最多抵5000积分"}
```
