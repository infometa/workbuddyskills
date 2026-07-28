# Interaction examples

## Example A: report generation

1. User selects: 報告與文書生成 + 數據整理與分析; primary = 報告與文書生成.
2. Ask issuing organization. User answers: 社區服務協會. (Or user picks `暫不公開` → store `未公開機構`.)
3. Offer pain choices. User selects: 資料分散，整理和匯總很花時間.
4. Offer current methods. User selects: 在 Excel、Word 或表格之間複製貼上.
5. Offer frequency choices. User selects: 每月 1–3 次.
6. Offer outcome choices. User selects: 統一結構 + 提示缺失資料.
7. Offer success choices. User selects: 完成時間縮短 + 遺漏減少.
8. Ask materials and boundaries with choices.
9. Generate title options, preview (including 出題機構), and wait for explicit confirmation.

## Example B: short answer

User: `報告很麻煩。`

Do not ask `請詳細描述`. Offer:
- 資料散落，很難集中
- 每次都要重新整理格式
- 不同同事的內容難以合併
- 容易漏掉必填資料
- 其他（自己描述）

## Example C: several pain points

User mentions volunteer scheduling, donor reports, and policy search.

Respond with a single-choice list asking which one should become the current challenge. Keep the other two as unconfirmed future candidates.

## Example D: poor fit

User wants WorkBuddy to replace social workers' safeguarding decisions.

Explain that final professional judgment cannot be delegated. Offer supporting choices:
- 整理個案資料供社工覆核
- 根據已批准指引列出需注意的項目
- 生成跟進紀錄初稿
- 建立人工覆核清單
- 這些都不適合，我想換一個問題

## Example E: confirmation gate

After preview, never infer consent from `看起來可以` or silence. First state, verbatim:

> 你確認提交後，賽題會先進入平台審批，不會立即公開；一般會在 **1 個工作天內**完成審批。審批通過後，可在公開賽題頁查看：`https://skillschallenge.edgeone.dev/`。

Then offer exactly:
- 確認提交審批
- 修改內容
- 暫不提交

Only the first selection authorizes `ready_to_sync`; it submits for approval and does not directly publish the challenge.

## Example F: complete final turn after `確認提交審批`

1. Assemble the JSON per `challenge-schema.md` with a non-empty `confirmed_snapshot_id` and validate it with `scripts/validate_challenge.py`.
2. Run `scripts/submit_challenge.py` with the validated JSON file.
3. On success, close verbatim (substituting the returned ID):

> 已提交審批，賽題編號：`{submission.id}`。賽題不會立即公開；一般會在 **1 個工作天內**完成審批。審批通過後，可在公開賽題頁查看：`https://skillschallenge.edgeone.dev/`。

4. On failure, state that automatic submission failed, output the complete validated JSON as the fallback, and direct the user to `https://skillschallenge.edgeone.dev/admin/import`.

Never say a submission succeeded without a successful endpoint response. The Expert may call only the public submission script, never an admin action.
