# 实时课堂带教

## 指挥台

调用 `salesnail_get_classroom_command_center` 读取：

- 各组当前轮次、行动点和动作量。
- 待审批动作。
- 已完成、准备完成和只差一个角色达标的商机。
- 当前轮无已批准动作、资源分散等提醒。
- 数据时间和完整性警告。

需要连续读取时复用 `snapshotId`；执行写操作后重新获取新指挥台。

## 控制操作

`salesnail_preview_classroom_control` 支持：

- approve_action：批准或驳回仍处于 pending 的动作。
- set_auto_approval。
- add_points：`pointsToAdd` 是正整数增量，不是设置余额；可指定小组或 `teamId=all`。
- next_round：指定小组或全部小组，可选择是否结转点数/好感度。
- broadcast：向指定小组发送经过转义的讲师广播。

下一轮会改变实时课堂状态且 MCP 不提供回退，必须逐项说明影响并等待确认。受邀讲师可以带教；回退轮次和强制结束不开放。
