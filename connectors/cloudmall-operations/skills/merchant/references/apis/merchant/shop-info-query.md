# 商户域 — 店铺信息查询契约

> 概念知识：`references/domains/merchant-concepts.md`；运营流程：`references/flows/merchant-config.md`（租户级配置族）；写操作见 `shop-info-action.md`。
> 店铺信息为**租户级单例**（无 id 参数，服务端按当前授权身份定位）。出参为上游**原始业务数据**。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引：shop-info.get 店铺信息查询

---

## ✅ 店铺信息查询 — ops.merchant.shop-info.get

- **说明**：查询当前租户的店铺基本信息；无入参（身份由连接绑定）。

### 出参（原始数据）

- **路径参数来源**：`shopId`（标识店铺）、`version`（integer 乐观锁版本号 → 编辑时必传回传）
- **格式敏感字段**：`createTime`（yyyy-MM-dd HH:mm:ss）
- **展示字段**：`shopName`、`shopLogo`、`loginBackground`、`loginBrandLogo`、`defaultAvatar`、`loginProtocolText`（含 `{{protocol:N}}` 占位符）、`miniProgramLink`（小程序路径如 /pages/index/index）

### 调用示例

```json
{"capability":"ops.merchant.shop-info.get","input":{},"summary":"查看店铺基本信息"}
```

---

## ⛔ 未开放（店铺信息）

| 操作 | 不开放理由 |
|------|-----------|
| 品牌展示查询（brand-display，公开接口） | 已弃用，将删除；C 端改用 /app 路径 |
| 首页商城信息（home/shop-info） | 访问统计字段当前为后端 Mock 数据，开放无意义 |
| 初始化引导清单（settings/init-checklist 系列） | 运维向导面，跨服务初始化路由，不属运营开放能力 |
