# 物流域 — 物流平台写操作契约

> 概念知识：`references/domains/logistics.md`；运营流程：`references/flows/logistics.md`
> **先读现值**：写入前用 `platform-query.md` 的 search / supported-list 查询当前配置与运行时支持的平台编码，不允许凭空创建未支持平台；平台创建与凭据变更未开放（见 `platform-query.md` 未开放块）。
> 平台为共享配置：停用或删除没有映射及历史运单引用保护，可能回落到其他平台并返回误导性的空轨迹，执行前确认轨迹查询是否依赖该平台；当前开放能力集不含平台删除恢复操作。
> **工具**：`当前运行时的 Capability 写操作执行器`（`mall.action`）——单次提交、不自动重试，超时或结果不确定先回读。
> 能力索引（前缀 `ops.logistics.`）：写 platform.update 🔴 · platform.update-status 🔴 · platform.test-connection 🟡 · platform.delete 🔴

---

## ✅ 更新物流平台 — ops.logistics.platform.update

`id` 必填十进制字符串；仅开放 `platformName`（最多 50）与 `remark`（最多 200）的非敏感编辑。虽然服务端还接受 `credentials/status`，开放能力不得传这两个字段：凭据变更无确定性验证闭环，状态应使用专用能力。`platformCode` 不可修改。

```json
{"capability":"ops.logistics.platform.update","input":{"id":"6200000000000000001","platformName":"快递100","remark":"生产物流查询平台"},"summary":"更新物流平台展示信息"}
```

---

## ✅ 启停物流平台 — ops.logistics.platform.update-status

`id` 必填十进制字符串；`status` 必填且只能为 `0` 或 `1`。启用仅在用户已有外部验证证据并明确要求时执行。

```json
{"capability":"ops.logistics.platform.update-status","input":{"id":"6200000000000000001","status":1},"summary":"基于已有外部验证证据启用物流平台"}
```

---

## ✅ 连接验证 — ops.logistics.platform.test-connection

`id` 必填十进制字符串；返回 `success/message`。本能力只能作为诊断信号：当前实现可能把部分平台错误判为成功，而普通轨迹也无法确定性补证，禁止把 `success=true` 表述为凭据有效。不自动重试。

```json
{"capability":"ops.logistics.platform.test-connection","input":{"id":"6200000000000000001"},"summary":"验证物流平台连接"}
```

---

## ✅ 删除物流平台 — ops.logistics.platform.delete

`id` 必填十进制字符串；执行逻辑删除，当前开放能力集不可恢复。

```json
{"capability":"ops.logistics.platform.delete","input":{"id":"6200000000000000001"},"summary":"删除已确认不再使用的物流平台配置"}
```
