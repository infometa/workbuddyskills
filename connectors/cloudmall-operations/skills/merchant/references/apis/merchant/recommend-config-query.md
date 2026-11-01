# 商户域 — 推荐配置查询契约

> 概念知识：`references/domains/merchant-concepts.md`；运营流程：`references/flows/merchant-config.md`；写操作见 `recommend-config-action.md`。
> 推荐配置为**租户级单例**：四力推荐（数据上报 + 推荐切换）与凭据（appid/appsecret）。出参为上游**原始业务数据**。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引：recommend-config.get 查询推荐配置

---

## ✅ 查询推荐配置 — ops.merchant.recommend-config.get

### 入参（无）

### 出参（原始数据）

- **枚举字段**：`dataReportSwitch`/`recommendSwitch`/`appsecretFilled`（boolean）
- **脱敏字段**：`appsecretMasked`（密钥脱敏占位，已配置为 `••••••••`、未配置为空串——**不是明文**）
- **格式敏感字段**：`lastModifiedAt`（yyyy-MM-dd HH:mm:ss）
- `appid` 为明文返回。

### 调用示例

```json
{"capability":"ops.merchant.recommend-config.get","input":{},"summary":"查看推荐配置与开关状态"}
```
