# 会员域 — 成长值任务写操作契约

> 概念知识：`references/domains/member-concepts.md`，状态与枚举：`references/domains/member-enums.md`；运营流程：`references/flows/member-benefit.md`；任务现值读取（列表回读核验）先读 `growth-task-query.md`。
> 所有 ID 均为十进制字符串；写操作须遵守入口 Skill 的风险档位、明确确认和回读纪律。
> **工具**：`当前运行时的 Capability 写操作执行器`（`mall.action`）——单次提交、不自动重试，超时或结果不确定先回读现态再决定下一步。
> 能力索引：member.growth-task.save 保存成长值任务配置 🔴

---

## ✅ 保存成长值任务配置 — ops.member.growth-task.save

- 🔴 全租户配置——保存即生效、无审核；**growthValue（每单成长值）直接决定全租户升级速率与升级礼包触发，数值必须用户明确给出**

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| tasks | Array | ✅ | 任务配置列表（非空） |
| tasks[].taskId | String | — | 已有任务传 taskId（来自 list）；新增可空 |
| tasks[].taskType | String | ✅ | 任务类型（当前仅 `purchase`-购买商品） |
| tasks[].enabled | Boolean | ✅ | 是否启用 |
| tasks[].taskConfig | Object | ✅ | 任务配置（按 taskType 多态；purchase：`perAmt` 固定传 1、`growthValue` 1~9999） |

`taskConfig`（purchase）子结构：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| taskType | String | ✅ | 固定 `purchase` |
| perAmt | Long | ✅ | **固定传 1**（单位：分；`@Min(1)@Max(1)` 硬校验，传其他值报错；⚠️ list 回读的存量配置可能含历史默认值 perAmt=100，**保存时必须改传 1，不能原样回传**） |
| growthValue | Integer | ✅ | 每单成长值 1~9999 |

### 出参（原始返回）

`data` 为 `null`；回读 `growth-task.list` 核验。**taskId 无效（不存在/跨租户）时服务端静默跳过该条不报错**——保存后必须回读核验生效结果。

### 调用示例

```json
{"capability":"ops.member.growth-task.save","input":{"tasks":[{"taskId":"1600012345678901234","taskType":"purchase","enabled":true,"taskConfig":{"taskType":"purchase","perAmt":1,"growthValue":100}}]},"summary":"调整购买商品任务每单成长值为100"}
```
