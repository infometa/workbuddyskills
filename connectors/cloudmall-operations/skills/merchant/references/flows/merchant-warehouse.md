# 商户域 — 仓库与配送配置流程（仓库 / 配送方式 / 运费与履约模板 / 区块）

> 对应契约：`apis/merchant/warehouse-query.md` / `warehouse-action.md`（仓库）、`apis/merchant/delivery-query.md` / `delivery-action.md`（配送方式与模板）、`apis/merchant/area-config-query.md` / `area-config-action.md`（区块/固定区域/行政区划）；概念知识：`references/domains/merchant-concepts.md`，状态机见 `references/domains/merchant-enums.md`；写操作共同纪律与字段来源见 `merchant-core.md`。

---

## 仓库配送配置（让仓库具备配送能力）

**目标**：把一个 UNCONFIGURED 仓库推进到 READY。

```
1. 建仓（warehouse.create，初始 UNCONFIGURED）——编码+省市区必填
2. 绑定配送方式（warehouse.bind-delivery-methods，全量替换语义）
   └ 先 delivery-method.list 拿可选方式；门店仓可绑四种最多 3 项（骑手与自提互斥二选一），
     前置仓/主仓仅快递类最多 2 项；不可传空数组
3. 逐配送方式绑定配送范围，二选一：
   a. 行政区域：warehouse.bind-administrative-blocks（bindType=2 全国 或 3 行政区域列表）
   b. 电子围栏区块：delivery-area-block.search 找区块 → warehouse.bind-delivery-blocks（blockIds 全量替换）
4. 逐区块绑定模板（warehouse.bind-block-template）：
   └ freight-template.search / fulfillment-template.search 先取模板 id
   └ 仅快递（express）只须运费模板；同城快递（city_express）等其余方式还须履约模板；传 null 可清除
5. 完成配置（warehouse.complete-fulfillment-config）→ configStatus=READY
6. 回读核验：warehouse.delivery-methods（看 configComplete）+ warehouse.delivery-blocks
```

**异常处理**：
- 停用状态仓库不可修改履约配置 → 先启用仓库再配置。
- 完成配置报「存在未完成区块」→ 回读 delivery-blocks 找 freightTemplateId/fulfillmentTemplateId 为空的记录补绑（报错只给数量，缺口自己查）。
- 解绑单个区块用 warehouse.unbind-delivery-block（blockRecordId 来自 delivery-blocks 返回的 id，不是区块 id）。
- 绑定配送方式不可传空数组（服务端直接拒绝）；移除某配送方式会级联删除其下全部区块配置。

## 运费/履约模板维护

```
新建运费模板：freight-template.create
  ├ BY_QUANTITY/BY_WEIGHT：chargeConfig 必填（首段/续段字段，见 delivery-action.md 参数表）
  ├ FIXED：chargeConfig 只需 fixedAmount
  ├ FREE：不传 chargeConfig
  └ BY_VOLUME 暂不可用（服务端拒绝）
新建履约模板：fulfillment-template.create（templateType 固定「预约配送」，timeConfig 结构见 delivery-action.md）
停用/启用：freight-template.update-status / fulfillment-template.update-status
删除前确认无仓库区块引用（被引用会被服务端拒绝并提示绑定信息）
```
