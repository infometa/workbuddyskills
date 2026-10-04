# 手工新增发票

## 什么时候读取

用户要手工录入一张发票，且已经提供或可以整理出完整 `info` 对象时读取本文件。开始前也读取共享高风险协议：`../../weaver-e10-shared-connector/references/high-risk-write.md`。

## Operation

| 阶段 | Operation | 必填输入 |
| --- | --- | --- |
| 准备新增 | `invoice.add.prepare` | `info`、`scope` |
| 确认新增 | `invoice.add.apply` | `info`、`continuation`、`confirm=true` |

## 注意

`scope` 必须是 `personal` 或 `enterprise`。CLI 会做票面字段校验和号码重复检查；不要在业务输入中放认证字段或内部控制字段。

`.prepare` 返回 `preview`、`continuation`、`expiresInSeconds` 和 `workflow.state="AWAITING_CONFIRMATION"`。展示风险后等待用户明确确认，再调用 `.apply`。
