# 会员域 — 积分商城配置查询契约

> 概念知识：`references/domains/member-concepts.md`，状态与枚举：`references/domains/member-enums.md`；运营流程：`references/flows/member-points-mall.md`；商城配置更新（写操作）见 `points-mall-action.md`，积分商品见 `points-goods-query.md` / `points-goods-action.md`。
> 出参为上游**原始业务数据**（不裁剪字段）。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引：member.points-mall.config 积分商城配置查询

---

## ✅ 查询积分商城配置 — ops.member.points-mall.config

### 入参

无。

### 出参（原始返回）

配置对象。**关键字段**：`id`（配置行 ID）、`bgImageUrl`（首页头图，空=小程序内置默认图）；**枚举字段**：`enabled`（**Integer：0=关闭 / 1=开启**，注意不是布尔）。⚠️ `bgImageUrl` 出参为 60 分钟时效的 COS 预签名 URL——回传更新时可**原样回传**（保存时服务端自动剥离签名参数，与 points-goods 的 itemImage 不同）。

### 调用示例

```json
{"capability":"ops.member.points-mall.config","input":{},"summary":"查询积分商城配置"}
```
