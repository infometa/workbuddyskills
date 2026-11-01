# 商户域 — 门店运营流程（建店履约 / 隔离与网店模式）

> 对应契约：`apis/merchant/store-query.md`（门店查询）、`apis/merchant/store-action.md`（门店写操作）、`apis/merchant/store-isolation-query.md` 与 `apis/merchant/store-isolation-action.md`（隔离与网店模式）、`apis/merchant/org-query.md` / `org-action.md`（组织）、`apis/merchant/pickup-site-query.md` / `pickup-site-action.md`（自提点）、`apis/merchant/map.md`（选址）；概念知识：`references/domains/merchant-concepts.md`；写操作共同纪律与字段来源见 `merchant-core.md`。

---

## 门店履约链路初始化（新建门店并开通履约）

**目标**：从零创建一家可接单的门店，并把它接入仓库与自提点履约网络。

```
0. 欠参检查（先问后写）：详细地址（具体到门牌）、所属区域节点、门店类型任一未由用户明确给出
   → 主动追问确认后再执行，不提交；地址类红线不因"用户给过模糊地址"而豁免（"在深圳南山区"不算详细地址）；
   orgNodeId 只接受用户指定的区域，禁止从 org.tree 结果里自行挑选一个区域填入
1. 查组织树定位区域节点（ops.merchant.org.tree → 找 type=REGION 的节点 id）
2. 查行政区划树拿省市编码（ops.merchant.region.tree）
3. 创建门店（ops.merchant.store.create）——初始状态 SUSPENDED，自动建默认仓/自提点
4. 激活门店（ops.merchant.store.update-status，status=ACTIVE）
5. 按需绑定外部仓库：查可绑仓库（store.available-warehouses）→ bind-warehouse（可多次）
   └ 需要调整扣减库存顺序时：store.sort-warehouses
6. 按需绑定自提点：查可绑自提点（store.available-pickup-sites）→ bind-pickup-site（可多次）
7. 回读核验：store.detail + store.warehouses + store.pickup-sites
```

**异常处理**：
- 创建被拒（PHYSICAL 缺省市区地址）→ 补全 province/city/district/address 后重提。
- 激活失败 → 检查当前状态是否 SUSPENDED（DRAFT 才能→ACTIVE 的路径不适用于新建店，新建店是 SUSPENDED→ACTIVE）。
- 默认仓库/自提点（isDefault=1）不可解绑；其余解绑用 unbind-warehouse / unbind-pickup-site。
- 超时后**先 store.search 按门店名查是否已创建**，确认未创建才可重新提交。

## 门店隔离与网店模式

**场景**：多网点模式下配置门店间数据互不可见；切换单/多网点模式。

1. `ops.merchant.store-mode.get` 确认当前模式（含 `mode` 与乐观锁 `version`；隔离配置属多网点能力，单网点下无意义）→
2. （如需）`ops.merchant.store-mode.update`（mode=multi + version 乐观锁）→
3. `ops.merchant.store-isolation.store-ids` 查已隔离门店全集（排除已配置项，避免重复配置）→
4. `ops.merchant.store-isolation.search` 看现有隔离关系（一条记录=一个被隔离门店）→
5. 确认待隔离门店清单（复述给用户——隔离后门店间数据互不可见）→ `batch-add`（storeIds 扁平列表）→
6. 回读 search 核验；解除/恢复隔离用 update-status（isolated 布尔），清理记录用 delete（记录 id 来自 search 出参）。
