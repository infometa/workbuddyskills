# 物流域 — 快递公司写操作契约

> 概念知识：`references/domains/logistics.md`；运营流程：`references/flows/logistics.md`
> **先读现值**：写入前用 `express-company-query.md` 的 search 查询现有快递公司及启用平台，复用已有编码并检查重复；写入后重新查询并逐项核对。
> 快递公司为跨订单、售后共享配置：新增、编辑、停用、删除都按高风险配置写入处理，执行前向用户确认对象和历史运单影响（改码、停用或删除没有历史运单引用保护，旧订单轨迹可能失效）。
> **工具**：`当前运行时的 Capability 写操作执行器`（`mall.action`）——单次提交、不自动重试，超时或结果不确定先回读。
> 能力索引（前缀 `ops.logistics.`）：写 express-company.create 🔴 · express-company.update 🔴 · express-company.update-status 🔴 · express-company.delete 🔴 · express-company.sync-wechat-delivery 🔴

---

## ✅ 新增快递公司 — ops.logistics.express-company.create

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| companyName | String | 是 | 1～50 字符 |
| companyCode | String | 是 | 最多 30 字符，严格匹配 `^[A-Za-z0-9_-]+$`，必须唯一 |
| logoUrl | String | 否 | 最多 500 字符 |
| sortOrder | Number | 否 | 越小越靠前，默认 0 |
| platformMappings | Array | 否 | 映射列表；每项见下表 |

映射项的 `platformCode` 必填且最多 30 字符，必须来自启用平台列表且同一列表内不可重复；`platformExpressCode` 必填且最多 50 字符。不要传 `platformName`，该字段即使传入也不入库。服务端当前不校验重复项或平台存在性，调用前必须完成校验。

创建成功后立即启用并进入发货/售后选择，没有停用草稿阶段；必须按高风险写入确认。

```json
{"capability":"ops.logistics.express-company.create","input":{"companyName":"顺丰速运","companyCode":"shunfeng","sortOrder":10,"platformMappings":[{"platformCode":"kuaidi100","platformExpressCode":"shunfeng"}]},"summary":"新增顺丰快递公司配置"}
```

---

## ✅ 更新快递公司 — ops.logistics.express-company.update

`id` 为必填十进制字符串。其余字段与新增相同但均可选，另可传 `status`，调用纪律仅允许 `0` 或 `1`（Java 当前未校验范围）；`platformMappings` 一旦传入即全量替换，空数组会清空映射（遗漏旧项会删除其映射）。修改 `companyCode` 没有历史运单引用保护，可能使旧单轨迹失效，必须单独确认。

```json
{"capability":"ops.logistics.express-company.update","input":{"id":"6100000000000000001","companyName":"顺丰速运","sortOrder":10},"summary":"更新快递公司名称与排序"}
```

---

## ✅ 启停快递公司 — ops.logistics.express-company.update-status

`id` 必填十进制字符串；`status` 必填且只能为 `0` 或 `1`。停用后历史单也无法用该编码查询轨迹，历史单也不出现在发货选择列表，执行前确认影响。

```json
{"capability":"ops.logistics.express-company.update-status","input":{"id":"6100000000000000001","status":1},"summary":"启用快递公司"}
```

---

## ✅ 删除快递公司 — ops.logistics.express-company.delete

`id` 必填十进制字符串；执行逻辑删除，当前开放能力集不可恢复，且没有历史运单引用保护。删除前优先停用观察。

```json
{"capability":"ops.logistics.express-company.delete","input":{"id":"6100000000000000001"},"summary":"删除已确认不再使用的快递公司"}
```

---

## ✅ 微信运力同步 — ops.logistics.express-company.sync-wechat-delivery

无入参；按名称匹配已有快递公司并写入微信平台映射，返回匹配数量。属于共享配置批量写入；执行前确认用户明确要求，执行后报告匹配数量并回读。

```json
{"capability":"ops.logistics.express-company.sync-wechat-delivery","input":{},"summary":"同步微信运力映射"}
```
