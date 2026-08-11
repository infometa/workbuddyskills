---
name: audit-spreadsheet
description: >
  Audit a spreadsheet for formula accuracy, errors, and common mistakes. Scopes to a selected range,
  a single sheet, or the entire workbook. Triggers on "audit this sheet", "check my formulas",
  "find formula errors", "QA this spreadsheet", "sanity check this", "something's off in this sheet",
  "review this spreadsheet".
---

# Audit Spreadsheet

Audit formulas and data for accuracy and mistakes. Scope determines depth — from a quick formula check on a selection up to a full pass over every sheet in the workbook.

---

## Step 1: Determine scope

If the user already gave a scope, use it. Otherwise **ask them**:

> What scope do you want me to audit?
> - **selection** — just the currently selected range
> - **sheet** — the current active sheet only
> - **workbook** — every sheet in the file, including cross-sheet links and hidden tabs

---

## Step 2: Run checks

Run every check below for the chosen scope. Each check is independent and self-contained.

### Check: Formula errors
- **Look for:** `#REF!`, `#VALUE!`, `#N/A`, `#DIV/0!`, `#NAME?`
- **How:** scan all formula cells; flag any whose evaluated value is an error code.
- **Default severity:** Critical

### Check: Hardcodes inside formulas
- **Look for:** numeric literals embedded in formulas, e.g. `=A1*1.05`
- **How:** parse each formula; business-input literals (rates, prices, multipliers) should be cell refs.
- **Default severity:** Warning

### Check: Inconsistent formulas
- **Look for:** a formula that breaks the pattern of its row/column neighbors.
- **How:** compare each formula to its neighbors; flag outliers in shape, function, or referenced range.
- **Default severity:** Warning

### Check: Off-by-one ranges
- **Look for:** `SUM`/`AVERAGE`/etc. that miss the first or last row of the data block.
- **How:** compare range bounds to the surrounding data block's actual boundaries.
- **Default severity:** Critical

### Check: Pasted-over formulas
- **Look for:** a cell that looks like it should be a formula but holds a hardcoded value.
- **How:** in columns of formulas, flag any cell whose value is a literal.
- **Default severity:** Critical

### Check: Circular references
- **Look for:** intentional or accidental cycles.
- **Default severity:** Critical

### Check: Broken cross-sheet links
- **Look for:** references to cells that have moved or been deleted.
- **Default severity:** Critical

### Check: Cross-sheet range alignment
- **Applies to:** `AVERAGE`, `SUM`, `OFFSET`, `INDEX`, `VLOOKUP`, `MATCH`, and similar range-consuming functions when the target is another sheet.
- **Look for:** ranges that *look* reasonable but don't match the source sheet's actual row/column boundaries.
- **How:**
  1. Open the source sheet; read its actual structure (header rows, group separators, data block boundaries).
  2. Verify the referenced range matches the source's real layout — infer layout from the source, never from the formula.
- **Traps:**
  - `AVERAGE(OtherSheet!A2:A100)` — does row 100 actually end the data, or is it mid-group?
  - Repeating-block sources ("every 11 rows is one period") — is the period length right?
  - `OFFSET` / dynamic ranges — is the stride consistent with the source?
  - `VLOOKUP` / `MATCH` — is the lookup column the column you think it is?
- **Rule:** "the range looks reasonable" is never sufficient. If you didn't open the source sheet, you didn't verify the reference.
- **Default severity:** Critical

### Check: Unit/scale mismatches
- **Look for:** thousands mixed with millions, % stored as whole numbers, currency mixed across regions.
- **Default severity:** Warning

### Check: Hidden rows/tabs
- **Look for:** overrides or stale calculations tucked into hidden ranges.
- **Default severity:** Warning

---

## Step 3: Report

Output a findings table:

| # | Sheet | Cell/Range | Severity | Category | Issue | Suggested Fix |
|---|---|---|---|---|---|---|

**Severity:**
- **Critical** — wrong output (formula broken, returns an error, produces an incorrect result)
- **Warning** — risky (hardcodes, inconsistent formulas, edge-case failures)
- **Info** — style/best-practice (color coding, layout, naming)

**Default: report first, fix on request.** If the user explicitly told you to fix as you go (e.g. "audit and fix", "don't ask, just fix"), skip the check-in and fix directly.

---

## Notes

- **Hardcoded overrides are the #1 source of silent bugs** — search aggressively.
- **Sign convention errors** (positive vs negative for inflows vs outflows) are extremely common.
