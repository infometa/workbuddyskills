# Enabled Automation-Rule Type Lookup

Which automation rule **types** are enabled on a set of campaigns:

```json
{
  "profileIds": [4404871489220462],
  "entity": "automationRule",
  "filters": {"amazonCampaignId": {"in": [123456789, 987654321, 555555555]}},
  "userContext": "Which automation rules are enabled on these campaigns"
}
```

Response:
```json
{
  "isError": false,
  "toolName": "get_entity_metadata",
  "data": {
    "rows": [
      {"amazonCampaignId": 123456789, "enabledRuleTypes": [2, 4], "enabledRuleNames": ["Dayparting", "Harvest Keywords"]},
      {"amazonCampaignId": 987654321, "enabledRuleTypes": [], "enabledRuleNames": []},
      {"amazonCampaignId": 555555555, "enabledRuleTypes": [17, 19], "enabledRuleNames": ["Budget Performance", "Placement Rule"]}
    ],
    "rowCount": 3
  },
  "meta": {"effectiveProfileIds": [4404871489220462], "hint": "Limit conclusions to this query's scope. Missing fields are not zero, and empty results do not prove that no matching business data exists. Do not present partial or paginated results as complete. Distinguish returned facts from analytical inferences; state limitations or query further when evidence is insufficient."}
}
```

Notes:
- `amazonCampaignId` in `filters` is **required** for this entity — there is no way to list all campaigns' rules without specifying which campaigns.
- No `orderBy`/`page`/`pageSize` effect — results always come back in the order the campaign IDs were requested.
- An empty campaign in the response (`enabledRuleTypes: []`) means that campaign simply has no automation rules enabled, not an error.
- This response is only an enabled-type summary. It cannot answer "show the rule's conditions/actions/frequency/template name" or list the account's automation templates.
- For a managed group's embedded Rule-mode configuration, query `entity: "aiGroup"` and read `aiAutomation.{ruleType}` using [`automation-rule-reading.md`](automation-rule-reading.md).
- Product inventory rules are SKU/product-scoped and are not represented by this campaign lookup; do not infer their absence from an empty `enabledRuleTypes` array.
