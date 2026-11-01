# 营销域 — 运营流程：CPS 分销员与佣金管理

> 概念知识见 `references/domains/cps-concepts.md`，状态与枚举见 `references/domains/marketing-enums.md`。
> 全部写操作遵守入口 SKILL.md 的风险档位与确认纪律。
> **能力标识约定**：本文为行文简洁使用模块短名（如 `cps-activity.save`、`popup.review`），实际调用 capability 必须使用全限定 id = `ops.marketing.` + 短名（即 `ops.marketing.cps-activity.save`），禁止把短名直接作为 capability 传入。
> 对应契约：`cps-distributor-query.md` / `cps-distributor-action.md`、`cps-apply-query.md` / `cps-apply-action.md`（申请审核）、`cps-group-level-query.md` / `cps-group-level-action.md`（分组/等级）、`cps-commission-query.md` / `cps-commission-action.md`（佣金率体系与订单补算）、`cps-goods-promotion-query.md`（商品推广状态）。

---

## CPS 分销员管理

**场景**：分销员档案/账户/流水/绑定关系；申请审核；分组与等级调整。

### 档案与账户
1. 列表 `cps-distributor.search`（name 模糊，phone/uid 精确，type/status/groupId 筛选）→ 详情 `cps-distributor.detail`。
2. 佣金账户 `cps-distributor.account`（三余额，元）；流水 `cps-distributor.deal-records`（**pageSize 上限 50**；dealType 单选/dealTypes 多选二选一，多选优先）。
3. 绑定关系 `cps-bind-relation.search`（cpsUid/uid 精确、phone 反查；bindType/relationType 筛选）。

### 新建分销员（🔴 创建分佣主体）
- `cps-distributor.create`：只传 `employeeId`（B 端员工账号 ID）+ 可选 groupId；姓名/手机号由服务端经用户中心自动获取，**不要传 name/phone**。

### 申请审核（🔴 通过即自动创建分销员）
```
查待审核（cps-apply.search，auditStatus=0）→ 审核通过（cps-apply.audit，auditStatus=1，自动创建分销员：等级 0/未分组/启用）
                                       └ 审核驳回（auditStatus=2，auditRemark 必填）
```
- 申请设置：`cps-apply.get-settings` → `cps-apply.save-settings`（🔴 整表保存；免审核模式会让新申请直接成为分销员，自动审核按天数+动作处理存量待审单）。

### 分组 / 等级调整
- 批量启停 `cps-distributor.batch-status`（uids 1..500 + status）；批量改组 `cps-distributor.batch-group`（🔴 分组变更改变分组佣金率命中，进而改变分佣水平）。
- 分组维护见 `cps-group.create/update/delete`；等级维护见 `cps-group-level-query.md` / `cps-group-level-action.md`（启停顺序强校验 + 乐观锁）。

### 参数来源

| 参数 | 来源 |
|------|------|
| uid（分销员） | 列表/详情/创建响应 |
| employeeId | 用户域 B 端员工账号 ID（用户提供） |
| groupId | `cps-group.options` 全量分组下拉 |
| levelId（CPS） | `cps-level.list` 的业务等级号 |

### 异常处置
- 已审核的申请再次审核 → 报"已审核"，向用户说明。
- 等级启用报顺序/指标错误 → 按从低到高约束与考核指标严格递增规则修正。

---

## CPS 佣金管理
**场景**：配置四级佣金率体系（全局默认 → 分组默认 → 商品定向 → 商品×分组）。

```
查全局（cps-commission.global-rate）→ 设全局（cps-commission.set-global-rate，🔴🔴 全量兜底率）
  → [可选] 商品定向（cps-commission.batch-reset-goods-rate，覆盖式 upsert，部分失败不回滚）
  → [可选] 商品×分组（cps-commission.batch-reset-group-rate，spuIds=具体商品，🔴 前提：先设全局）
  → [可选] 分组默认（同一能力，spuIds=["0"]，设置某分组推广全部商品的默认率；groupId 不得传 -1）
  → [可选] 取消定向（cps-commission.cancel-directed，删除定向率+全部分组率，回退全局默认，幂等）
```

- 查询侧：全局分组率 `cps-commission.global-group-rates`（全量不分页）；商品分组率 `cps-commission.goods-group-rates`（spuId 必填）；单品定向率 `cps-commission.goods-rate`（**null=未设置定向**，区别于全局查询返回 0）。
- **查询返回的 rate 是生效值**（未配置的分组回填：商品定向率→全局默认），不代表已配置。
- 所有写操作的 rate 数值必须用户明确给出；set-global-rate 执行前复述「当前值 → 目标值」。
- 批量操作部分失败不回滚，按 failItems（spuId+reason）逐条处理。

---
