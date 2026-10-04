# 编辑发票

## 什么时候读取

用户要修改已有发票字段时读取本文件。开始前也读取共享高风险协议：`../../weaver-e10-shared-connector/references/high-risk-write.md`。

## Operation

| 阶段 | Operation | 必填输入 |
| --- | --- | --- |
| 准备编辑 | `invoice.update.prepare` | `fid`、`scope`、`changes` |
| 确认编辑 | `invoice.update.apply` | `continuation`、`confirm=true` |

## 允许修改字段

以 `weaver-work-cli invoice schema` 为准，当前包括：

```text
code
number
comm_info.pro.date
comm_info.price.amount
comm_info.price.total
comm_info.price.dtax
comm_info.buyer.company
comm_info.buyer.tcode
comm_info.payer.company
comm_info.payer.tcode
fylx
currency
currencyName
```

## 注意

CLI 会先取完整详情、确认可编辑、生成变更预览，再在 apply 时校验目标未变化并保留附件关联。禁止修改 `fid/id`、附件关联、`sedit`、Dubbo 字段、认证字段、`skipFlag=1` 等内部字段。

`.prepare` 返回 `preview`、`continuation`、`expiresInSeconds` 和 `workflow.state="AWAITING_CONFIRMATION"`。展示风险后等待用户明确确认，再调用 `.apply`。
