# 物流域 — 物流平台查询契约

> 概念知识：`references/domains/logistics.md`；写操作见 `platform-action.md`；运营流程：`references/flows/logistics.md`
> `credentials` 永不返回（AES-256-GCM 加密存储）。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引（前缀 `ops.logistics.`）：查询 platform.search · platform.supported-list · platform.enabled-list

---

## ✅ 物流平台搜索 — ops.logistics.platform.search

接受可选 `pageNum/pageSize`（默认 1/20，`pageSize` 1～100），返回分页配置；`credentials` 永不返回。

```json
{"capability":"ops.logistics.platform.search","input":{"pageNum":1,"pageSize":20},"summary":"查询物流平台配置"}
```

---

## ✅ 支持平台列表 — ops.logistics.platform.supported-list

无入参，返回运行时已支持编码（**当前为 `kuaidi100`（快递）与 `fengniao`（蜂鸟即配/即时配送 INSTANT）两个**，2026-10-12 实测）；如未来开放创建，必须先使用本结果，不要凭文档示例假定只有 kuaidi100。

```json
{"capability":"ops.logistics.platform.supported-list","input":{},"summary":"查询系统支持的物流平台"}
```

---

## ✅ 启用平台列表 — ops.logistics.platform.enabled-list

无入参，返回已启用配置，供快递公司映射选择。

```json
{"capability":"ops.logistics.platform.enabled-list","input":{},"summary":"查询已启用物流平台"}
```

---

## ⛔ 未开放（本模块）

| 能力 | 原因 |
|---|---|
| 平台创建、平台凭据变更 | 创建即启用且无法原子化先停用验证；现有连接验证与普通轨迹查询都不能确定性证明目标平台凭据有效（无法形成确定性验证闭环），走管理后台 |
