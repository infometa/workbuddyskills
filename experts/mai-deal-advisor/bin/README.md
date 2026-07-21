# Tool Notes

Runnable scripts are bundled under `bin/` for local verification. They use only local files or public HKEX endpoints.

## Source-Grounding Gate

```bash
grounding_gate.py draft.md
```

Exit code `1` means the draft has numbers that need primary-source confirmation or explicit uncertainty labeling.

## Cap-Table Reconciliation Gate

```bash
recon_gate.py cap_table.xlsx
```

Exit code `1` means the cap table has reconciliation issues such as inconsistent implied share bases or duplicated disclosure lines.

## HKEX Announcement Fetcher

```bash
hkexnews_fetch.py 00700
```

Returns announcement date, title, and URL for the requested HK ticker and date range.

Plain `.txt` and `.md` files require no extra packages. `.xlsx` checks require `openpyxl`; `.docx` checks require `python-docx`.
