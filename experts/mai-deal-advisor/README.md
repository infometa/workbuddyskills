# MAI Lab M&A Expert Pack

中文名：MAI Lab并购专家包

Version: 1.0.1

Free WorkBuddy expert package for disciplined M&A analysis workflows.

This package is intentionally thin. It helps users structure reports, run source and arithmetic checks, monitor HKEX announcements, and identify when a question needs senior human review. It does not contain MAI's proprietary judgment library, deal-specific cases, client files, or private transaction know-how.

## Included

- Three-phase report workflow: startup, analysis, closing checklist
- Report format rules and sanitized report templates
- Source-grounding gate: `bin/grounding_gate.py`
- Cap-table reconciliation gate: `bin/recon_gate.py`
- HKEX announcement fetcher: `bin/hkexnews_fetch.py`
- `[ESCALATE]` card format for complex judgment questions
- Intake form handoff: `https://api.mai.deals/workbuddy/intake?source=mai-lab-ma-expert-pack-v1.0.1`

## Versioning

This is the first WorkBuddy listing candidate with platform-compatibility fixes. Future updates should use semantic versions such as `1.1.0` and keep the intake `source` value versioned for funnel tracking.

## Excluded

- Real deal-specific judgment entries
- Private client files, internal project files, or case analysis payloads
- Automatic messages to counterparties or external people
- Commercial collection logic

## Safe Demos

Use `references/safe-demos.md` to show what the expert can do without exposing private materials:

- HKEX announcement check
- Cap-table reconciliation gate
- Complex transaction question escalation

## Install

Place this directory at:

```bash
~/.workbuddy/plugins/marketplaces/my-experts/plugins/mai-deal-advisor/
```

Then register it in WorkBuddy using the platform's expert registration flow.

## Verification

Before shipping a report draft, run the gate tools on local files:

```bash
grounding_gate.py draft.md
recon_gate.py cap_table.xlsx
hkexnews_fetch.py 00700
```

If either gate exits with code `1`, the draft is not ready to deliver.

## Dependencies

Plain `.txt` and `.md` checks use only Python's standard library. To scan `.xlsx` files, install `openpyxl`; to scan `.docx` files, install `python-docx`.

```bash
python -m pip install openpyxl python-docx
```

## Disclaimer

AI-generated analysis from this package is for workflow support and reference only. It is not investment advice, a securities recommendation, legal advice, or a commitment by MAI Deal Inc. Users must verify source materials and make decisions with qualified human review.
