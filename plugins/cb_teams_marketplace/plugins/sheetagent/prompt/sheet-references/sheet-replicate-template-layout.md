---
name: sheet-replicate-template-layout
description: >
  MANDATORY when the user asks to "reference / copy / replicate / follow the format of" an existing
  sheet (template) to modify another sheet. Triggers on "参考、模版、模板、template、copy format、
  replicate layout、follow the style of、按照…格式、照着…做、复制格式、格式一样、样式一样、
  跟…一样的格式", or any intent implying "make sheet B look like sheet A". Covers P0 properties:
  row heights, column widths, merged cells, background colors, font sizes, font colors, font
  weights, font styles, font families, font lines, number formats, text wrap,
  horizontal/vertical alignment, borders.
---

# Replicate Template Layout & Styles

> **This reference is the single source of truth for template-replication work in SheetAgent.** You MUST read and follow it whenever the user wants one sheet to visually match another sheet's layout and styling. Do **NOT** guess which properties to copy from memory — this reference defines the complete P0 property list and execution order.
>
> References to **§5.5 rule 12** (apply styling at creation) and **§5.5 rule 13** (replicate template layout) point to the sheet-agent system prompt, which is always in context alongside this reference.

## When to Trigger

Any user intent that implies "make sheet B look like sheet A":
- Keywords: 参考、模版、模板、template、copy format、replicate layout、follow the style of、按照…格式、照着…做、复制格式、格式一样、样式一样、跟…一样的格式
- Implicit intent: user provides a "sample sheet" and asks another sheet to follow its format/appearance

## Critical Principles

### ⛔ Observation over Assumption — Never Invent Formats

Format decisions MUST be based on **what the template actually contains**, never on "common patterns." This is especially critical for merged cells:

- ✅ Template has merged cells at range X → replicate that merge
- ❌ Template does NOT have a merge → do NOT add one, even if it "looks better"
- ⚠️ Before ANY `merge()` call, check that no non-empty cells (other than top-left) will be destroyed — merging is **unrecoverable data loss**

## Mandatory Preflight — Run BEFORE Any Replication

> **Every template-replication task MUST execute these checks before writing any style or layout to the target sheet.** Skipping preflight leads to silent failures (styles applied to non-existent rows/cols are lost), data destruction (merging over non-empty cells), or partial replication (target too small to hold the template's full range).

### Step 1: Identify Template & Target Sheets

```javascript
const ss = SpreadsheetApp.getActiveSpreadsheet();
const templateSheet = ss.getSheetByName("Template");
const targetSheet = ss.getSheetByName("Target");
// ❌ If either sheet is null, STOP and report to the user — do NOT create a sheet on your own initiative.
if (!templateSheet || !targetSheet) {
  return { error: "Sheet not found", templateExists: !!templateSheet, targetExists: !!targetSheet };
}
```

### Step 2: Determine the Effective Replication Range

```javascript
const templateLastRow = templateSheet.getLastRow();
const templateLastCol = templateSheet.getLastColumn();
// If user specified a sub-region (e.g. "only copy the header row 1-3"), use that instead.
// Otherwise default to the template's full used range.
const srcRows = templateLastRow;
const srcCols = templateLastCol;
```

- If the user explicitly says "only copy row 1–5" or "only the header area", scope `srcRows` / `srcCols` accordingly — do NOT blindly copy the entire sheet.
- If the template has 0 rows or 0 columns (`getLastRow() === 0`), it is empty — STOP and inform the user.

### Step 3: Ensure Target Sheet Has Enough Space

```javascript
const targetLastRow = targetSheet.getLastRow();
const targetLastCol = targetSheet.getLastColumn();
// Expand target if template is larger
if (srcRows > targetLastRow) {
  targetSheet.insertRows(targetLastRow + 1, srcRows - targetLastRow);
}
if (srcCols > targetLastCol) {
  targetSheet.insertColumns(targetLastCol + 1, srcCols - targetLastCol);
}
```

- **NEVER skip this step.** Applying `setBackgrounds()` / `setFontSizes()` to a range that exceeds the target's bounds will silently fail or throw.
- After insertion, the target is guaranteed to have at least `srcRows × srcCols` cells available.

### Step 4: Check for Existing Merges on Target (Unmerge if Needed)

```javascript
const existingMerges = targetSheet.getMergedCells();
if (existingMerges.length > 0) {
  // Unmerge all existing merges in the target's replication zone to avoid conflicts
  for (const mr of existingMerges) {
    if (mr.row <= srcRows && mr.col <= srcCols) {
      targetSheet.getRange(mr.row, mr.col, mr.numRows, mr.numCols).breakApart();
    }
  }
}
```

- Existing merges on the target can conflict with new data writes and new merges from the template.
- Only unmerge cells within the replication zone — leave merges outside that zone untouched.

### Step 5: Validate Template Style Data (Sanitize Nulls)

Before batch-applying styles, read and sanitize:

```javascript
const templateRange = templateSheet.getRange(1, 1, srcRows, srcCols);
const backgrounds = templateRange.getBackgrounds();
// Sanitize: replace null/undefined with "" (transparent/default)
for (let r = 0; r < backgrounds.length; r++) {
  for (let c = 0; c < backgrounds[r].length; c++) {
    if (!backgrounds[r][c]) backgrounds[r][c] = "";
  }
}
```

- `getBackgrounds()` may return `null` or `""` for cells with no explicit background — both are valid for `setBackgrounds()`, but `null` can cause errors on some hosts.
- Apply the same sanitization pattern to any getter that may return null (`getFontColors()`, `getFontFamilies()`, etc.).

### Preflight Checklist (mental — confirm all before proceeding)

| # | Check | Fail action |
|---|-------|-------------|
| 1 | Template sheet exists | STOP, report error |
| 2 | Target sheet exists | STOP, report error |
| 3 | Template is not empty (`getLastRow() > 0`) | STOP, report "template is empty" |
| 4 | Target has enough rows/cols | Insert rows/cols to expand |
| 5 | Target existing merges in replication zone cleared | `breakApart()` conflicting merges |
| 6 | Style arrays sanitized (no null values) | Replace null with default (`""` / `10` / `"normal"`) |

> **Only after ALL 6 checks pass should you proceed to the Execution Pattern below.**

## P0 — MUST Replicate (layout will be visually broken without these)

| Category | Property | Read API | Write API |
|----------|----------|----------|-----------|
| Layout | Row heights | `getRowHeight(row)` | `setRowHeight(row, h)` / `setRowHeights(startRow, numRows, h)` |
| Layout | Column widths | `getColumnWidth(col)` | `setColumnWidth(col, w)` / `setColumnWidths(startCol, numCols, w)` |
| Structure | Merged cells | `sheet.getMergedCells()` | `range.merge()` / `mergeAcross()` / `mergeVertically()` |
| Cell Style | Background color | `range.getBackground()` / `range.getBackgrounds()` | `range.setBackground(color)` / `range.setBackgrounds(colors)` |
| Cell Style | Font size | `range.getFontSize()` / `range.getFontSizes()` | `range.setFontSize(size)` / `range.setFontSizes(sizes)` |
| Cell Style | Font color | `range.getFontColor()` / `range.getFontColors()` | `range.setFontColor(color)` / `range.setFontColors(colors)` |
| Cell Style | Font weight (bold) | `range.getFontWeight()` / `range.getFontWeights()` | `range.setFontWeight(weight)` / `range.setFontWeights(weights)` |
| Cell Style | Font style (italic) | `range.getFontStyle()` / `range.getFontStyles()` | `range.setFontStyle(style)` / `range.setFontStyles(styles)` |
| Cell Style | Font family | `range.getFontFamily()` / `range.getFontFamilies()` | `range.setFontFamily(family)` / `range.setFontFamilies(families)` |
| Cell Style | Font line (underline/strikethrough) | `range.getFontLine()` / `range.getFontLines()` | `range.setFontLine(line)` / `range.setFontLines(lines)` |
| Cell Style | Number format | `range.getNumberFormat()` / `range.getNumberFormats()` | `range.setNumberFormat(fmt)` / `range.setNumberFormats(fmts)` |
| Cell Style | Text wrap | `range.getWrap()` / `range.getWraps()` | `range.setWrap(wrap)` / `range.setWraps(wraps)` |
| Cell Style | Horizontal alignment | `range.getHorizontalAlignment()` / `range.getHorizontalAlignments()` | `range.setHorizontalAlignment(align)` / `range.setHorizontalAlignments(aligns)` |
| Cell Style | Border | `range.getBorder()` / `range.getBorders()` | `range.setBorder(top, left, bottom, right, vertical, horizontal, color?, style?)` / `range.setBorders(borders)` |
| Cell Style | Vertical alignment | `range.getVerticalAlignment()` / `range.getVerticalAlignments()` | `range.setVerticalAlignment(align)` / `range.setVerticalAlignments(aligns)` |

### API Parameter Reference (1-based vs 0-based)

> ⚠️ **All public APIs in this reference use 1-based indexing** (consistent with Google Apps Script). The shim layer internally converts to 0-based before sending to the backend. You should NEVER pass 0-based indices to any of these APIs.

#### Sheet-level APIs (all row/col params are **1-based**)

| API | Signature | Parameter Notes |
|-----|-----------|-----------------|
| `getRange` | `getRange(row, col, numRows?, numCols?)` | `row`: 1-based row index; `col`: 1-based column index; `numRows`/`numCols`: count (default 1) |
| `getRange` | `getRange(a1Notation)` | A1 notation string, e.g. `"A1:C3"` |
| `getRowHeight` | `getRowHeight(row)` | `row`: **1-based** row index. Returns height in pixels (0 = hidden) |
| `getColumnWidth` | `getColumnWidth(col)` | `col`: **1-based** column index. Returns width in pixels (0 = hidden) |
| `setRowHeight` | `setRowHeight(row, height)` | `row`: **1-based**; `height`: pixels |
| `setRowHeights` | `setRowHeights(startRow, numRows, height)` | `startRow`: **1-based**; `numRows`: count; `height`: pixels |
| `setColumnWidth` | `setColumnWidth(col, width)` | `col`: **1-based**; `width`: pixels |
| `setColumnWidths` | `setColumnWidths(startCol, numCols, width)` | `startCol`: **1-based**; `numCols`: count; `width`: pixels |
| `insertRows` | `insertRows(row, numRows?)` | `row`: **1-based** position to insert before; `numRows`: count (default 1) |
| `insertColumns` | `insertColumns(col, numCols?)` | `col`: **1-based** position to insert before; `numCols`: count (default 1) |
| `deleteRows` | `deleteRows(row, numRows)` | `row`: **1-based** starting row; `numRows`: count |
| `deleteColumns` | `deleteColumns(col, numCols)` | `col`: **1-based** starting column; `numCols`: count |
| `moveRows` | `moveRows(startRow, numRows, destinationRow)` | All **1-based** |
| `moveColumns` | `moveColumns(startCol, numCols, destinationCol)` | All **1-based** |
| `getMergedCells` | `getMergedCells(startRow?, startCol?, numRows?, numCols?)` | Optional params are **1-based**; defaults to entire sheet |

#### `getMergedCells` Return Value (1-based)

Returns `Array<{ row, col, numRows, numCols }>` — all fields are **1-based**:
- `row`: 1-based start row of the merged region
- `col`: 1-based start column of the merged region
- `numRows`: number of rows in the merged region
- `numCols`: number of columns in the merged region

### Return Value Notes

- `getFontWeight()` returns `"bold"` or `"normal"`
- `getFontStyle()` returns `"italic"` or `"normal"`
- `getFontLine()` returns `"underline"`, `"line-through"`, or `"none"`
- `getHorizontalAlignment()` returns `"left"`, `"center"`, `"right"`, or `"general"`
- `getVerticalAlignment()` returns `"top"`, `"middle"`, or `"bottom"`
- `getBorder()` returns `{ top: BorderSide | null, bottom: BorderSide | null, left: BorderSide | null, right: BorderSide | null }` where `BorderSide = { color: string, style: string }`. `style` is one of `"SOLID"`, `"SOLID_MEDIUM"`, `"SOLID_THICK"`, `"DASHED"`, `"DOTTED"`, `"DOUBLE"`. A side is `null` if no border is set.
- `getBorders()` returns a 2D array of the same border info for every cell in the range
- `setBorders(borders)` accepts a 2D array (same shape as `getBorders()` output) and applies per-cell borders. This is the batch write counterpart of `getBorders()`.
- `getWrap()` returns `true` or `false`
- `getLastRow()` / `getLastColumn()` returns **1-based** index of the last row/column with content
- All 2D array getters return arrays indexed `[rowOffset][colOffset]` where offset starts at 0 (relative to the range's top-left corner)

## Execution Pattern

Include in the same `run_command` call that writes data and styles:

```javascript
const templateSheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("Template");
const targetSheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("Target");
const lastRow = templateSheet.getLastRow();
const lastCol = templateSheet.getLastColumn();

// 1. Copy row heights — ONLY rows within template range; leave other rows untouched
for (let r = 1; r <= lastRow; r++) {
  const h = templateSheet.getRowHeight(r);
  if (h > 0) targetSheet.setRowHeight(r, h);
}
// 2. Copy column widths — ONLY columns within template range; leave other columns untouched
for (let c = 1; c <= lastCol; c++) {
  const w = templateSheet.getColumnWidth(c);
  if (w > 0) targetSheet.setColumnWidth(c, w);
}

// 3. Copy merged cells — replicate ONLY what exists in template, skip if target has data
const mergedRanges = templateSheet.getMergedCells(); // returns array of {row, col, numRows, numCols} (1-based)
for (const mr of mergedRanges) {
  const vals = targetSheet.getRange(mr.row, mr.col, mr.numRows, mr.numCols).getValues();
  const safe = vals.every((row, r) => row.every((v, c) => (r === 0 && c === 0) || !v));
  if (safe) targetSheet.getRange(mr.row, mr.col, mr.numRows, mr.numCols).merge();
}
const templateRange = templateSheet.getRange(1, 1, lastRow, lastCol);
const targetRange = targetSheet.getRange(1, 1, lastRow, lastCol);

// 4. Copy cell styles in batch
const backgrounds = templateRange.getBackgrounds();
const fontSizes = templateRange.getFontSizes();
const fontColors = templateRange.getFontColors();
const fontWeights = templateRange.getFontWeights();
const fontStyles = templateRange.getFontStyles();
const fontFamilies = templateRange.getFontFamilies();
const fontLines = templateRange.getFontLines();
const numberFormats = templateRange.getNumberFormats();
const horizontalAlignments = templateRange.getHorizontalAlignments();
const wraps = templateRange.getWraps();
const verticalAlignments = templateRange.getVerticalAlignments();
const borders = templateRange.getBorders();

targetRange.setBackgrounds(backgrounds);
targetRange.setFontSizes(fontSizes);
targetRange.setFontColors(fontColors);
targetRange.setFontWeights(fontWeights);
targetRange.setFontStyles(fontStyles);
targetRange.setFontLines(fontLines);
targetRange.setFontFamilies(fontFamilies);
targetRange.setNumberFormats(numberFormats);
targetRange.setHorizontalAlignments(horizontalAlignments);
targetRange.setWraps(wraps);
targetRange.setVerticalAlignments(verticalAlignments);

// 5. Copy borders in batch using setBorders (counterpart of getBorders)
targetRange.setBorders(borders);
```

## Execution Priority

1. **Write data first** — populate target cells with values/formulas
2. **Apply cell styles** — backgrounds, font sizes, font colors, font weights, font styles, font families, font lines, number formats, alignments (batch via plural setters)
3. **Apply merged cells** — merge after data is written (merge only keeps top-left value)
4. **Apply row heights & column widths LAST** — prevents auto-fit from overriding explicit dimensions

## Common Pitfalls

1. **Merge before data** → only top-left cell value survives; always write data first
2. **Row height / column width too early** → writing data may trigger auto-resize; set dimensions last
3. **Null backgrounds** → `getBackgrounds()` may return `null` or `""` for default; sanitize before `setBackgrounds`
4. **Target sheet too small** → if template has more rows/cols than target, `insertRows` / `insertColumns` to expand first
5. **Partial range** → if user only wants to replicate a sub-region, scope the template/target ranges accordingly (don't blindly copy the entire sheet)
6. **Hidden rows/columns** → `getRowHeight` returns 0 for hidden rows; preserve this (set height 0 = keep hidden)
7. **Default font values** → `getFontFamily()` returns `"默认字体"` when no explicit font is set; `getFontSize()` returns `10` as default — avoid writing these defaults back if they match the target's existing defaults
8. **Do NOT touch rows/columns outside the replication zone** → only set row heights and column widths for rows/columns that fall within the template's used range (`1..lastRow`, `1..lastCol`). Columns and rows beyond the template range in the target sheet must remain unchanged — do NOT reset them to any default or zero width/height
