# 商户域 — 推荐配置写操作契约

> 概念知识：`references/domains/merchant-concepts.md`；运营流程：`references/flows/merchant-config.md`；现值读取先读 `recommend-config-query.md`。
> 写操作须遵守入口 Skill 的风险档位、明确确认和回读纪律。
> **工具**：`当前运行时的 Capability 写操作执行器`（`mall.action`）——单次提交、不自动重试，超时或结果不确定先回读现态再决定下一步。
> 能力索引：recommend-config.switches 仅切换开关

---

## ✅ 仅切换开关 — ops.merchant.recommend-config.switches

- 不动 appid/appsecret

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| dataReportSwitch | Boolean | ✅ | 数据上报开关 |
| recommendSwitch | Boolean | ✅ | 推荐切换开关（开启时上报必须同时开启） |

### 出参（原始返回）

脱敏结构（同查询出参）。

### 调用示例

```json
{"capability":"ops.merchant.recommend-config.switches","input":{"dataReportSwitch":true,"recommendSwitch":false},"summary":"临时关闭推荐切换但保留数据上报"}
```

---

## ⛔ 未开放（推荐配置）

| 操作 | 不开放理由 |
|------|-----------|
| 全量保存推荐配置（save，含 appid/appsecret 修改） | **密钥明文传输风险**——appsecret 需经聊天通道明文传入，会暴露在会话记录与日志中；凭据类操作请到管理后台「推荐配置」页面操作 |
