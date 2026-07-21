# Instantly-Specific Rules

## Valid Variables (ONLY these — no others)

| Variable | Usage |
|----------|-------|
| `{{firstName\|there}}` | Prospect first name, fallback "there" |
| `{{companyName\|your company}}` | Prospect company, fallback "your company" |
| `{{personalization}}` | Custom personalization field (set per lead) |
| `{{sendingAccountFirstName}}` | Sender's first name (from sending account) |

**Never use:**
- Square-bracket placeholders like `[Competitor A]`, `[Your Company]`, `[Industry]`
- Custom variables not listed above — they won't render in Instantly
- If a concept can't be expressed with valid variables, rewrite the copy to not need it

## firstName Rule (Critical)
- **Always require firstName** during lead upload. Filter out leads without first name.
- Do NOT rely on the `|there` fallback as a design choice — it signals a bad list.
- If the list has >5% missing firstName, flag it before launch.

## Sequence Structure

- **Steps:** 5-6 max (not 8). Diminishing returns after 6.
- **Step delays (days after previous step):**
  - Step 1: Day 0 (immediate)
  - Step 2: Day 2
  - Step 3: Day 4-7
  - Step 4: Day 7
  - Step 5: Day 7-14
  - Step 6 (breakup): Day 7-14 after Step 5

## A/B Testing
- **Step 1 only:** Test 2 subject line variants (A/B)
- Don't A/B test body copy in early campaigns — isolate subject line variable first
- Winning subject line = whichever hits higher open rate at 100+ sends per variant

## Signature Format
```
{{sendingAccountFirstName}}
```
- No company name, no title, no tagline — unless explicitly requested
- Keep it human. Feels like it came from a person, not a company.

## Deliverability Rules

### Send Limits
- **Safe:** 30 emails/day per account
- **Aggressive:** 50 emails/day per account (only with score 90+, warmed 30+ days)
- Never exceed 50/day per account without explicit discussion

### Warmup Requirements
- **Minimum:** 14 days warmup before first campaign
- **Minimum score:** 80+ warmup score
- Accounts below 80 or under 14 days: DO NOT add to active campaigns

### Domain Setup (must verify before launch)
- SPF: configured and passing
- DKIM: configured and passing
- DMARC: policy set (at minimum p=none with reporting)
- MX records: pointing correctly
- Custom tracking domain: set up in Instantly (subdomain, not root domain)

### Spam Signals to Avoid
- Words: "free", "guarantee", "no risk", "limited time", "act now", "click here"
- Excessive links (max 1 per email, ideally 0 in Steps 1-2)
- Images in cold email (never)
- HTML formatting (plain text only)
- All-caps words
- Exclamation points in subject lines

## Upload Requirements
Leads must have:
- `firstName` (required — filter out if missing)
- `email` (required)
- `companyName` (required for `{{companyName}}` variable)
- `personalization` (required if using `{{personalization}}` in sequence)

Validate list before upload. Bad data = bad deliverability.
