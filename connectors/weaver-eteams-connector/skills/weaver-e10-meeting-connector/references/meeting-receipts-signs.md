# 回执与签到

## 何时使用

查会议回执情况、给某人回执（参加/不参加/请假）、查签到记录与统计。

## 输入要点

- 回执更新**必须传回执记录主键 `id`**（不是 `memberId`）；`prepare` 会自动按 `memberId` 回查定位。
- `attendStatus` 枚举：`0`=未填写、`1`=参加、`2`=不参加（回执"否/请假"传 2）。
- 回执列表接口必须带 `isMobile`（CLI 缺省 `false`；缺失会导致后端 NPE→500，已被 CLI 托管）。

## 命令

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json meeting run meeting.receipt.list --input-json '{"mtId":"1305624900858404950"}'
weaver-work-cli --profile eteams --json meeting run meeting.receipt.update.prepare --input-json '{"mtId":"1305624900858404950","memberId":"101","attendStatus":2,"remark":"请假"}'
# 用户确认后：
weaver-work-cli --profile eteams --json meeting run meeting.receipt.update.apply --input-json '{"confirm":true,"continuation":"<prepare返回的continuation>","mtId":"1305624900858404950","memberId":"101","attendStatus":2,"remark":"请假"}'
weaver-work-cli --profile eteams --json meeting run meeting.sign.list --input-json '{"mtId":"1305624900858404950"}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json meeting run meeting.receipt.list --input-json '{"mtId":"1305624900858404950"}'
weaver-work-cli --profile eteams --json meeting run meeting.receipt.update.prepare --input-json '{"mtId":"1305624900858404950","memberId":"101","attendStatus":2,"remark":"请假"}'
# 用户确认后：
weaver-work-cli --profile eteams --json meeting run meeting.receipt.update.apply --input-json '{"confirm":true,"continuation":"<prepare返回的continuation>","mtId":"1305624900858404950","memberId":"101","attendStatus":2,"remark":"请假"}'
weaver-work-cli --profile eteams --json meeting run meeting.sign.list --input-json '{"mtId":"1305624900858404950"}'
```

## 输出处理

- `receipt.list` 返回 `receipts[]`（含 `id`/`memberId`/`attendStatus`/`remark`）；`receipt.update.prepare` 返回 `preview`（含定位到的回执记录 `id`）。
- `sign.list` 返回 `signs[]` 与 `summary`（`total`/`signed`/`unsigned`），输出 Markdown 表格。

## 注意

- `prepare` 找不到参会人回执记录时报 `receipt_not_found`：先用 `meeting.receipt.list` 核对 `memberId`。
- `apply` 前必须取得用户对"目标回执 + 状态 + 备注"的明确确认。

## 失败处理

- `target_changed` / `continuation_expired`：重新 prepare 再确认。
- 写请求发出后网络中断 → `partial/write_uncertain`：禁止自动重试，先 `meeting.receipt.list` 回查是否已生效。
