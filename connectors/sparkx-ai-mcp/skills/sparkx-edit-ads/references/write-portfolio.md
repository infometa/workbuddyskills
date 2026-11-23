# Portfolio membership, budget and dates

Four routes use `request.data`, require top-level `request.profileIds`, and allow 1-200
items. Read every target with `get_entity_metadata` first and keep internal and Amazon ids
separate.

## Campaign membership

`campaign + addPortfolio` and `campaign + removePortfolio` execute directly.

Each item uses the campaign's internal `id`, `profileId`, and actual `campaignType`.
`addPortfolio` also requires `amazonPortfolioId`: the destination portfolio's Amazon id,
not its internal `portfolioId`. `removePortfolio` omits it. Adding can move a campaign from
its current portfolio. Both routes support SP/SB/SD and reject an archived campaign or one
whose `processStatus` is `Archived` / `Ended`.

## Portfolio budget

`portfolio + updateBudget` always uses two-phase confirmation. Each item uses the portfolio's
internal `id`, `profileId`, and `portfolioBudget`.

- Single item, amount only: the portfolio must already have a cap; marketplace-specific range
  rules apply and JP requires an integer.
- Explicit `policy`: `dateRange`, `monthlyRecurring`, or `""` to remove the cap.
  For one item, setting a cap requires an effective positive amount no greater than
  1,000,000; an omitted amount may reuse an existing valid amount, and without an existing
  cap it is an error. For multiple items, an explicit amount may be zero, must have at most
  two decimals and at most 10 plain-decimal characters; an omitted amount asks the downstream
  to preserve existing amounts and may skip portfolios with no cap.
- Amounts are in each profile's local currency. A multi-item request must use one country,
  allows at most two decimals, and does not use the single-item marketplace ranges.

Single-item amount-only ranges:

| Marketplace | Min | Max |
|---|---:|---:|
| DE/ES/FR/IT/NL/UK/GB/US/CA/BE/IE | 1 | 1,000,000 |
| JP (integer) | 100 | 21,000,000 |
| SA/AE | 4 | 3,700,000 |
| MX | 1 | 21,000,000 |
| SG | 1.39 | 1,300,000 |
| AU | 1.4 | 1,500,000 |
| IN | 50 | 21,000,000 |
| BR | 1.32 | 5,300,000 |
| SE | 9 | 9,300,000 |
| PL | 2 | 2,000,000 |
| TR | 2 | 2,500,000 |
| EG | 7 | 7,400,000 |
| ZA | 20 | 7,000,000 |

For `dateRange`, `portfolioBudget.startDate` is required either explicitly or from a valid
current value; it cannot be cleared. `endDate` may be omitted or set to `""` to clear.
`monthlyRecurring` accepts only an optional `endDate`. Removing a cap or changing only one
amount accepts no dates.

The preview's `current` is the queried configuration; `submitted` is what MCP prepared;
`defaultSources` explains reused or preserved values; `mayBeSkipped` warns that a
multi-item omission may not update that portfolio. Phase 2 returns
`meta.submittedChanges`; it describes the submitted payload, not guaranteed Amazon state.

## Portfolio dates

`portfolio + updateDates` executes directly. Dates are valid `yyyyMMdd` strings and are
sent unchanged: do not infer a timezone, compare to today's date, or convert to UTC.

- One item: send exactly one of `startDate` or `endDate`. The portfolio must have a cap;
  `startDate` is valid only for `dateRange`; `endDate: ""` clears the end date.
- Multiple items: every item must provide `endDate`; `startDate` is not accepted.
- `startDate: ""` and explicit null are rejected. When both dates exist, end must be later
  than start.

The downstream may adjust past dates. Read the portfolio back after either route and report
the stored values rather than treating the submitted dates as final.
