# 商户域 — 地图能力契约

> 概念知识：`references/domains/merchant-concepts.md`；运营流程：`references/flows/merchant-store.md`（门店/自提点选址辅助）。
> 覆盖 POI 地点搜索（门店/自提点选址辅助）。出参为上游**原始业务数据**。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引：map.suggestion POI 关键词搜索

---

## ✅ POI 关键词搜索 — ops.merchant.map.suggestion

- **说明**：代理腾讯地图 WebService 进行 POI 搜索，返回候选地点（建店/自提点选址时把坐标、地址候选给用户确认）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| keyword | String | 是 | 搜索关键词 |
| region | String | 否 | 限制城市范围 |
| pageSize | Integer | 否 | 默认 10，最大 20 |

### 出参（原始数据）

- **透传结构**：字段由腾讯地图 API 定义（不做二次封装）——常见 `title`、`address`、`location`（`lat`/`lng`——**选址坐标来源**）、`province`/`city`/`district`
- ⚠️ 坐标为**腾讯系 GCJ-02**；门店坐标用 GCJ-02、自提点用 WGS84（需换算时如实说明，不静默混用）。

### 调用示例

```json
{"capability":"ops.merchant.map.suggestion","input":{"keyword":"深圳湾科技生态园","region":"深圳"},"summary":"搜一下这个园区的候选坐标用于建店选址"}
```

---

## ⛔ 未开放（地图）

| 操作 | 不开放理由 |
|------|-----------|
| 地图密钥配置（map/config 查询/保存/恢复默认） | 租户级腾讯地图密钥（WS_KEY/WS_SK/GLJS_KEY）管理面——密钥敏感（SK 加密存储/脱敏回显），走管理后台，不开放给 Agent 读取或写入 |
| GL JS Key 下发（gljs-key） | 前端 SDK 密钥下发面，非运营数据 |
| 行政区域 GeoJSON（geojson/{code}） | 前端地图渲染辅助数据（全局限流 120 次/分钟），Agent 无消费场景 |
