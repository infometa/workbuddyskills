# SP Budget Changes (Fine-Grained operationType Filter)

```json
{
  "profileIds": [4404871489220462],
  "dateStart": "2026-06-01",
  "dateEnd": "2026-06-30",
  "campaignTypes": ["sponsoredProducts"],
  "operationType": {"operator": "IN", "values": ["DailyBudget Increased", "DailyBudget Decreased"]},
  "pageSize": 200,
  "userContext": "SP budget adjustment records"
}
```

**Same intent, but only changes made by people** — run the query above and filter the rows
client-side: keep `changedBy` = an email or `Manual` (add `Amazon Console` only if you also
want changes made on Amazon's side), and `changeField` =
`dailyBudget` (in AI managed groups, AI's hourly `currentBudget` rows carry the same
`operationType`). Do **not** add `"changeBy": {"operator": "IN", "values": ["manual"]}` for
this — the server **rejects** `manual` outright (see [`field-reference.md`](field-reference.md) ->
changeBy); it is a UI category, not an operator, and it never covered the changes recorded
under a user's email.

Note: `operationType` (fine-grained) is more precise than `actionType` (coarse categories like `"Budget Increased"`) — use `operationType` when you need to isolate a specific sub-case.

**Check `truncated` before presenting either result as complete** — if `true`, split the date range into non-overlapping sub-windows and repeat, rather than presenting a partial result as the full history.
