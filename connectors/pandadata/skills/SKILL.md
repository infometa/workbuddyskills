---
name: pandadata
description: Query and analyze financial data through the PandaData MCP Connector. Use whenever users ask for Chinese, Hong Kong, or U.S. equity data, futures, options, funds, macroeconomic indicators, quantitative factors, trading calendars, market comparisons, or data-backed financial trend summaries.
---

# PandaData financial data

Use PandaData as the source of record for supported financial datasets. Retrieve evidence before making data-dependent claims, distinguish observations from interpretation, and never invent missing values.

## Tool workflow

The Connector may namespace tool names. Match the available PandaData tools by their logical names below.

1. Call `auth_status` before the first real data request. If authentication is required or expired, ask the user to complete the WorkBuddy OAuth login and stop the data workflow until it succeeds.
2. If the exact `get_*` method is unknown, call `search_methods` with concise domain terms. Prefer this over loading the full catalog with `list_methods`.
3. Call `get_method_doc` for the selected method before every data request. Use its documented parameter names, types, required fields, units, enumerations, and example as the authoritative contract.
4. Clarify only details that materially change the query, such as instrument identifier, market, date range, frequency, adjustment convention, currency, or statistical definition.
5. Call `call_pandadata` with the documented method and a `params` object. Only documented `get_*` methods are valid. Do not add a top-level row `limit`; returned row counts are controlled by the user's service quota.
6. For a comparison or analysis, fetch each required dataset with aligned dates, frequencies, adjustment conventions, and units before calculating or summarizing.

Use `sdk_status` only to diagnose service or catalog availability. Use `list_methods` when the user explicitly asks to browse a category or when focused searches cannot identify a method.

## Method selection

- Search using the user's business concept first, then narrow by market, asset class, frequency, or field name.
- When several methods are plausible, compare their summaries and parameters. Ask the user to choose only if the difference changes the intended result.
- Never guess an endpoint, method name, security identifier format, parameter, enum value, or response field.
- If a method is unknown, use the server's suggestions and repeat discovery before attempting another call.

## Result handling

- State the queried instruments or indicators, market, date range, frequency, and important data conventions.
- Present compact tables for comparisons when helpful. Keep raw facts, calculations, and interpretation visibly distinct.
- Identify missing periods, null values, stale observations, differing units, and non-trading days that affect the conclusion.
- If the dataset is large, summarize it and show representative rows unless the user explicitly requests the full result.
- Mention the PandaData method name so the query can be reproduced.

## Errors

- `reauth_required`: stop and request OAuth login; do not retry in a loop.
- Permission or quota error: explain the restriction accurately. Reauthentication does not grant a higher data entitlement.
- Empty result: verify the identifier, market, trading calendar, date range, and method parameters before concluding that no data exists.
- Gateway or service error: report the useful error detail and suggest retrying later; do not fabricate fallback data.

## Financial safety

Provide data retrieval, organization, calculations, comparisons, and neutral trend interpretation. Do not promise returns or issue direct buy/sell instructions. State that outputs are for research and informational purposes when the user could treat the analysis as investment guidance.

Never ask the user to paste a password, JWT, access token, refresh token, or API key into the conversation. Authentication belongs in WorkBuddy's OAuth flow.
