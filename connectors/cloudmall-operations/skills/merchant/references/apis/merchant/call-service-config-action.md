# 商户域 — 客服配置写操作契约

> 概念知识：`references/domains/merchant-concepts.md`；运营流程：`references/flows/merchant-config.md`；现值读取先读 `call-service-config-query.md`。
> 写操作须遵守入口 Skill 的风险档位、明确确认和回读纪律。
> **工具**：`当前运行时的 Capability 写操作执行器`（`mall.action`）——单次提交、不自动重试，超时或结果不确定先回读现态再决定下一步。
> 能力索引：call-service-config.save 保存客服配置

---

## ✅ 保存客服配置 — ops.merchant.call-service-config.save

- upsert 语义（不存在则创建，存在则更新）
- **提交前格式预判（先判后写）**：phoneNumber 仅接受 1 开头 11 位手机号或 `0XX(X)-XXXXXXX(X)(-分机)` 座机；明显非法（400/800 号、位数不对）直接向用户说明格式要求并请更正，不提交换取服务端拒绝；enabled=true 且 phoneNumber/serviceTime 缺失时先追问再保存。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| enabled | Boolean | ✅ | 开关；true=开启 false=关闭 |
| phoneNumber | String | 条件 | enabled=true 时必填（服务端校验）；格式：手机号 `1` 开头 11 位，或座机 `0XX(X)-XXXXXXX(X)(-分机)` |
| serviceTime | String | 条件 | enabled=true 时必填；服务时间文本，≤50 字符 |

### 出参（原始返回）

无返回数据；执行后回读核验。关闭开关（enabled=false）时**保留**原电话与服务时间不覆盖，重新开启无需重填。

### 调用示例

```json
{"capability":"ops.merchant.call-service-config.save","input":{"enabled":true,"phoneNumber":"13800138000","serviceTime":"工作日 9:00-18:00"},"summary":"开启电话客服并配置服务时间"}
```
