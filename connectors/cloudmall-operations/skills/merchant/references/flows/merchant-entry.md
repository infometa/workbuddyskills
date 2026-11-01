# 商户域 — 进店规则与固定区域流程

> 对应契约：`apis/merchant/entry-rule-query.md` / `entry-rule-action.md`（进店规则）、`apis/merchant/area-config-query.md` / `area-config-action.md`（固定区域部分）；概念知识：`references/domains/merchant-concepts.md`，规则类型优先级链见 `references/domains/merchant-enums.md`；写操作共同纪律与字段来源见 `merchant-core.md`。

---

## 进店规则（C 端用户进哪个店的判定优先级）

```
1. entry-rule.list 读全量规则与优先级
2. 调整优先级：entry-rule.sort（sortedIds 不含 DEFAULT_STORE；PARAM_STORE 可重排）
3. 启停：entry-rule.update-status（仅 DEFAULT_STORE 不可禁用）
4. 改参数：entry-rule.update-params —— 先看 list 返回的 ruleType 再选参数分支
   └ 改 DEFAULT_STORE 的 defaultStoreId 等效直接切换默认门店（需目标门店 ACTIVE）
```

## 固定区域（LBS 推荐的「某组织节点 → 推荐地区」映射）

```
fixed-area.search 现状 → create（orgNodeId + 地区列表）/ update（全量替换地区）
```

- 同一租户下组织节点唯一（一个节点只能配一个固定区域）；地区编码在租户内互斥；level（province/city/district）用 region.tree 的层级推导，服务端不校验枚举。
