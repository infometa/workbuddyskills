# 交易域 — 运营流程：售后配置与原因库管理

> 四组租户级售后配置（自动退款/退运费规则/售后时效/退库存）与售后原因库维护。
> 概念知识见 `references/domains/trade-concepts.md`，枚举见 `references/domains/trade-enums.md`；执行闭环见 `trade-core.md`。
> 对应契约：`aftersale-config-query.md` / `aftersale-config-action.md`、`aftersale-reason-query.md` / `aftersale-reason-action.md`。
> 全部写操作遵守入口 SKILL.md 的风险档位与确认纪律。

---

读取 [售后配置契约](../apis/trade/aftersale-config-query.md)、[售后配置写契约](../apis/trade/aftersale-config-action.md) 与 [售后原因库契约](../apis/trade/aftersale-reason-query.md)、[售后原因库写契约](../apis/trade/aftersale-reason-action.md)。

1. 四组售后配置（自动退款/退运费规则/售后时效/退库存）均为租户级共享配置且全量覆盖：先读现值（auto-refund.get / freight-rule.list / timeout-config.get / inventory-config.get），向用户复述当前值与目标变更，确认后构造**完整**提交，回读核对。
2. 运费规则必须从 `freight-rule.list` 取全部 11 条后只改目标项再完整提交；`editable=false` 的规则原样回传；`reset` 覆盖全部自定义，执行前明确告知。
3. 时效与退库存配置影响超时自动流转和库存回补等全租户行为（🔴）：逐项复述新旧值，确认后提交。金额阈值单位是分。
4. 原因维护：`reason.list`（按 subTab）读现值 → 从 `reason.group-list` 取真实大类名 → 新增/编辑/启停/排序后回读。删除（🔴）前确认不再使用并向用户说明历史售后保留快照不受影响。
5. 配置变更均写配置操作日志（模块 `AFTER_SALE_CONFIG`），需要追溯时用交易运营日志查询能力。自动退款配置当前无执行消费方（实现缺口），如实说明配置是规则意图而非执行承诺。
