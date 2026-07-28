# Approval and publication reminder

Use this wording in the final confirmation turn, after presenting the full brief:

> 你確認提交後，賽題會先進入平台審批，不會立即公開；一般會在 **1 個工作天內**完成審批。審批通過後，可在公開賽題頁查看：`https://skillschallenge.edgeone.dev/`。

Offer exactly these actions:

- 確認提交審批
- 修改內容
- 暫不提交

Rules:

- Only `確認提交審批` sets `conversation_state.status` to `ready_to_sync`.
- This action is a submission to platform review, never direct publication.
- The admin process performs the later publish action (`ready_to_sync` → `synced`).
- Only `synced` challenges appear on the public site.

## Validate and submit (immediately after `確認提交審批`)

1. Assemble the JSON per `challenge-schema.md` (`schema_version: "1.0"`, `id: null`, status `ready_to_sync`, `explicit_confirmation: true`) and generate a non-empty `confirmed_snapshot_id`.
2. Validate with `scripts/validate_challenge.py`; fix all errors first.
3. Run `scripts/submit_challenge.py` with the validated JSON file.
4. On success, report the returned challenge ID and remind the NGO that approval normally takes 1 working day; do not output the full JSON unless requested.
5. On failure, never claim submission. Output the validated JSON as a fallback and point to `https://skillschallenge.edgeone.dev/admin/import`.

The Expert calls only the public review-submission endpoint and never uses or embeds admin credentials. Publication remains an admin action.
