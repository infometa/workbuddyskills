# 商品域 — 状态机与枚举字典

> 查值字典：状态机迁移与前置、枚举值精确拼写（大小写与取值以本表为准）。
> 查状态含义、确认操作前置、取枚举值时读本文件；实体模型/规则结构/业务约束见 `product-concepts.md`。
> 能力契约见 `references/apis/product/`，操作流程见 `references/flows/`。

---

## SPU 展示状态

SPU 使用 `isDraft` + `isHidden` 双布尔控制，旧 `SpuStatus` 已废弃：

```
新建商品（isDraft=true）
    ↓ 保存/提交
商品正常（isDraft=false, isHidden=false）
    ↓ hide          ↓ off-shelf
隐藏（isHidden=true）  禁售（SKU 聚合不可售）
    ↓ unhide          ↓ on-shelf
商品正常            商品正常
```

列表 Tab 映射：
| Tab | 含义 |
|-----|------|
| ALL | 全部非草稿商品 |
| ON_SALE | 非隐藏、SKU 聚合可售且未被平台禁售 |
| OFF_SALE | 非隐藏，且 SKU 聚合不可售或被平台禁售 |
| HIDDEN | 隐藏 |

不存在 SOLD_OUT，售罄≠禁售。

## SKU 状态

```
ENABLED（可售） ↔ DISABLED（禁售）
```
- 生命周期：`ACTIVE`（活跃）↔ `ARCHIVED`（历史归档）
- SPU 上架 = 活跃 SKU 全部置 ENABLED；下架 = 全部置 DISABLED；SPU 可售性 = 任一活跃 SKU ENABLED

## 门店商品状态

```
ON_SHELF（上架） ↔ OFF_SHELF（下架）
```
- SKU 批量置状态后：同门店同 SPU 全部 SKU 下架 → SPU 自动 OFF_SHELF；任一 SKU 上架 → SPU 自动 ON_SHELF
- SKU 档位（toggle-shelf）控制在架 SPU 内单个规格的可售性；单条为**翻转语义**、批量为显式 `ON_SHELF`/`OFF_SHELF`

## SPU 审核状态（audit-approve / audit-reject）

```
REVIEWING → APPROVED / REJECTED（auditRemark 必填）
```
- 枚举全集：`NONE`（无需审核，运营自建）/ `REVIEWING` / `APPROVED` / `REJECTED`；另有 `DRAFT` 为 @Deprecated 存量兼容值
- 仅 `auditStatus=REVIEWING` 且来源为 GUIDE_PUBLISH 或 SUPPLIER 的商品可审核
- 运营端创建的商品（source=ADMIN）无需审核
- 审核通过 ≠ 已上架：通过后仍需执行 SPU 上架与门店上架
- 驳回原因会传达给商品编辑方，须具体可行动
- 删除商品仅限草稿/已隐藏状态（在架需先下架并隐藏）

## 评价审核状态流

```
用户提交 → RISK_CONTROLLING（风控中）
    ↓
RISK_APPROVED → PENDING_AUDIT（待人工审核）
RISK_REJECTED → REJECTED（风控直接拒绝）

PENDING_AUDIT → APPROVED（通过）/ REJECTED（拒绝）
    ↓ 超时
TIMEOUT_APPROVED（超时自动通过）
AUTO_APPROVED（系统自动通过）
```

**终态规则（运营最易踩坑）**：
- APPROVED / AUTO_APPROVED / TIMEOUT_APPROVED / REJECTED / RISK_REJECTED 均为**不可再变更的终态**
- 驳回仅对 `PENDING_AUDIT`（含"主评价已通过但追评待审"）生效；对终态评价调驳回**必然失败**
- 批量驳回前先按待审核状态过滤 ID 清单，或查 `review.tab-count` 确认数量级
- **无评价下线/隐藏能力**：对已通过的违规评价，唯一补救是**商家回复**（review.reply，官方声明/澄清）；彻底下线需后端扩展，不承诺、不编造

### 评价驳回原因枚举（rejectReason）

`SPAM`-垃圾评价 / `INAPPROPRIATE`-不当内容 / `IRRELEVANT`-与商品无关 / `OTHER`-其他（OTHER 必填 rejectRemark 补充说明）

### 评价搜索口径

- `auditStatus` 筛选的 `PENDING_AUDIT`/`REJECTED` 为**追评合并口径**（待审 Tab = 主评待审或追评待审），非单值精确匹配
- `reviewType` 为内容形态（WITH_TEXT/WITH_IMAGE/STAR_ONLY），不是首评/追评维度（追评用详情的 hasAppendReview 判断）

## 库存调整

```
操作类型：SET（设置）/ ADD（增加）/ SUBTRACT（减少）
```
- 库存调整需乐观锁（`version` 字段）
- 总库存调整可能导致预留库存被自动调低（返回 warning）

## 库存流水变更类型

`MANUAL_ADJUST`（人工调整）/ `BATCH_IMPORT`（批量导入）/ `ORDER_LOCK`（下单锁定）/ `ORDER_RELEASE`（取消释放）/ `SALE_OUTBOUND`（销售出库）/ `RETURN_INBOUND`（退货入库）

## 枚举字典

| 业务 | 值 | 说明 |
|------|---|------|
| 商品类型 productType | `PHYSICAL`-实物 / `SERVICE`-服务 / `STUDY_TOUR`-研学 / `VIRTUAL`-兼容虚拟类型 | |
| 规格模式 specMode | `SINGLE`-统一规格 / `MULTI`-多规格 | |
| SKU 状态 | `ENABLED`-可售 / `DISABLED`-禁售 | |
| 列表 Tab | `ALL` / `ON_SALE` / `OFF_SALE` / `HIDDEN` | 不存在 SOLD_OUT，售罄≠禁售 |
| 商品来源 source | `ADMIN`-运营端 / `GUIDE_PUBLISH`-导购发品 / `SUPPLIER`-供应商 | |
| 审核状态 auditStatus | `NONE` / `REVIEWING` / `APPROVED` / `REJECTED` | 另有 `DRAFT` 为 @Deprecated 存量兼容值 |
| 配送方式 code | `express`-快递 / `city_express`-同城 / `rider_delivery`-骑手 / `self_service`-门店自配 | 小写（创建/更新用）；另有系统内置码 `service_verification`-服务核销 / `virtual_fulfillment`-虚拟履约（SERVICE/STUDY_TOUR/VIRTUAL 商品由服务端强制归一为内置码，非商家可选） |
| 仓库类型 | `STORE_WAREHOUSE`-门店仓 / `FRONT_WAREHOUSE`-前置仓 / `MAIN_WAREHOUSE`-主仓 | |
| 库存调整动作 | `SET` / `ADD` / `SUBTRACT` | |
| 库存导入任务状态 | `PENDING` / `PROCESSING` / `SUCCESS` / `PARTIAL_FAIL` / `FAIL` | |
| 业务分类 bizType | `PHYSICAL` / `SERVICE_ONSITE`-到店服务 / `SERVICE_PICKUP`-上门服务 / `STUDY_TOUR`-研学 | 扩展字段预置键，驱动库存分派与门店商品筛选 |
| 到店服务状态 | `draft` / `online` / `offline`（小写） | `isDraft` 控制草稿/发布 |
| 到店服务确认模式 confirmMode | `auto`-自动确认 / `store_confirm`-门店确认 | |
| 到店服务门店范围 storeScope | `all` / `specified`（小写） | |
| FAQ 生效状态 | `IN_EFFECT`-生效中 / `NOT_STARTED`-未开始 / `EXPIRED`-已过期 | 生效期均可空（=永久） |
| 静态标签有效期类型 | `PERMANENT`-永久 / `CUSTOM`-自定义区间 | CUSTOM 须 validFrom+validTo 成对 |
| 静态标签生效状态 | `EFFECTIVE`-生效中 / `NOT_EFFECTIVE`-未生效 / `EXPIRED`-已过期 | |
| 搭配状态 | `online`-上线 / `offline`-下线（小写） | 另有 DELETED（逻辑删除态） |
| 搭配投放物料状态 | `READY` / `GENERATING` / `FAILED` | 仅此三值；retry 仅对 FAILED 可用 |
| 搭配发布方式 | `manual` / `auto`（小写） | |
| 扩展字段层级 targetLevel | `ALL` / `SPU` / `SKU` | fieldCode+targetLevel 组合唯一 |
| 扩展字段类型 fieldType | `TEXT` / `TEXTAREA` / `NUMBER` / `MONEY` / `DATE` / `DATETIME` / `BOOLEAN` / `SINGLE_SELECT` / `MULTI_SELECT` / `CASCADE` / `IMAGE` / `FILE` | 12 种 |
| 扩展字段必填规则 requiredMode | `NONE` / `ALWAYS` / `CONDITION` | 服务端仅强制 ALWAYS |
| 描述属性交互方式 interactionType | `TEXT_INPUT` / `NUMBER_INPUT` / `SELECT_SINGLE` / `SELECT_MULTIPLE` | |
| 类目层级 | 1~5 级 | 一级类目 parentCode 为空字符串 |
