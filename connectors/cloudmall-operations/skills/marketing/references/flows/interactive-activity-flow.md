# 营销域 — 运营流程：互动营销活动（双版本流程与奖品履约）

> 概念知识见 `references/domains/marketing-concepts.md`，状态与枚举见 `references/domains/marketing-enums.md`。
> 全部写操作遵守入口 SKILL.md 的风险档位与确认纪律。
> **能力标识约定**：本文为行文简洁使用模块短名（如 `cps-activity.save`、`popup.review`），实际调用 capability 必须使用全限定 id = `ops.marketing.` + 短名（即 `ops.marketing.cps-activity.save`），禁止把短名直接作为 capability 传入。
> 对应契约：`interactive-activity-query.md` / `interactive-activity-action.md` / `interactive-activity-prize-action.md`、`prize-template-query.md` / `prize-template-action.md`。

---

## 互动活动

**场景**：draft/formal 双版本互动活动的创建、发布、运行与奖品履约。

```
创建（interactive-activity.create，🟡 仅落 draft，UNPUBLISHED）
  → [可选] 编辑（update，只改 draft，需再次发布才生效；已发布活动奖品总量只能增不能减）
  → 发布（publish，🔴 draft 快照整包 upsert 到 formal，C 端立即可见；按开始时间落 NOT_STARTED/RUNNING）
  → 运行（formal）：暂停（pause，RUNNING/NOT_STARTED）/ 恢复（resume，仅 PAUSED）/ 结束（end，🔴 TERMINATED 终态）
  → 奖品履约：
      虚拟资产 → 自动发放（SENDING → SENDED）
      实物 → 中奖记录查询（prize-records，筛 CLAIMED 找待发货并核对收货资料）→ 发货（ship-prize，🔴 发货后 SENDED 终态不可撤销；运单号必须来自用户提供的真实物流信息，禁止编造）
  → [可选] 库存调整（update-stock，🔴 只能调大不能调小；按 prizeName 定位）
  → [可选] 复制（copy，formal 优先复制为新草稿）/ 优先级（set-priority，draft+formal 同步）/ 关联场景（save-relative-scenes，全量覆盖式）
  → 删除（delete，🔴 仅未发布或 formal 已结束/已过期；draft+formal 及库存/限流数据一并删除）
```

- 奖品池：先在奖品模板（`prize-template.*`）建模板（coupon 类必须关联促销域券模板 ID），再在活动 prizeList 中以 templateId 绑定。
- **draft/formal 双版本纪律**：编辑永远改 draft；要看 C 端实际运行配置用 `detail` 的 `detailType: formal`。
- 筛选陷阱：PUBLISHED 传入筛选非法（空列表），"已结束"用 `statusList: ["TERMINATED","EXPIRED"]`；中奖记录 EXPIRED 为惰性展示态，筛 WAITING_CLAIM 再看 expireTime。
- 数据监控 `data-monitor`（参与/发奖/转化率）；关联场景查询 `relative-scenes`。

### 品牌兑换码活动草稿

品牌方提供码、小程序输入码领奖 → 本域 `exchange-code`，仅需 COMMON；平台生成券码批次 → 促销域，两者不能互相替代。

1. 优惠券奖品先用促销域普通券模板查询按名称定位，核对详情；同名多条请用户指定，不使用批次专用 `coupon-code.templates` 代替通用查询。
2. 查询/创建本域 coupon 奖品模板，`bizTemplateId` 取券模板 ID；活动 `prizeInfo.prizeList[].templateId` 取奖品模板 ID，不能直接填券模板 ID。
3. 使用用户明确的时间和数量保存 `exchange-code` 草稿，再以 `detailType: draft` 回读核验活动类型、COMMON、奖品关联和总量；只存草稿时不发布。
4. 指定券已结束或有效期不覆盖活动时，披露后续派奖风险，不自行恢复、替换券；此风险与草稿接口是否接受分开说明。

**能力边界**：草稿保存不代表品牌兑换码导入、核验、一次性消耗或实际领奖链路已就绪。当前运营能力未登记该链路，运行时也未证实完整支持；不能仅凭 `exchange-code` 类型可保存就承诺用户输入码必能领奖，发布前须另行核验。

### 参数来源

| 参数 | 来源 |
|------|------|
| activityId（互动） | 列表/创建/复制响应（业务 ID，非主键） |
| uniqId（中奖记录） | prize-records 出参 |
| templateId（奖品模板） | 奖品模板查询/创建响应 |
| 库存增量目标值 | 用户明确给出（只能调大） |

---
