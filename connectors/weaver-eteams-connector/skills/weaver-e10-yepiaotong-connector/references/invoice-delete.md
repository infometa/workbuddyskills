# 删除发票

## 什么时候读取

用户要删除已有发票时读取本文件。开始前也读取共享高风险协议：`../../weaver-e10-shared-connector/references/high-risk-write.md`。

## Operation

| 阶段 | Operation | 必填输入 |
| --- | --- | --- |
| 准备删除 | `invoice.delete.prepare` | `fid`，可选 `scope` |
| 确认删除 | `invoice.delete.apply` | `continuation`、`confirm=true` |

## 注意

删除固定为软删除 `flag=0`。CLI 会确认当前状态允许删除，并在删除后回查目标不再可见。

`.prepare` 返回 `preview`、`continuation`、`expiresInSeconds` 和 `workflow.state="AWAITING_CONFIRMATION"`。展示风险后等待用户明确确认，再调用 `.apply`。

如果返回 `partial/write_uncertain`，停止自动重跑 apply；向用户报告 `data` 中的目标 `fid`、`workflow.state` 和需要人工确认的内容。
