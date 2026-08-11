---
name: sheet-pivot-tables
description: >
  Pivot table creation, configuration, inspection, and modification patterns for spreadsheet
  operations. Read before any `createPivotTable` / `getPivotTableDetail` / `getPivotTable` /
  `update` / `remove`, or any task that creates, modifies, or removes a pivot table, or a request
  that implies one: 创建透视表 / 数据透视 / 汇总分析 / 分组统计 / 行分组 / 列分组 / 值汇总 /
  筛选透视 / 修改透视表 / 删除透视表; "create / add / build a pivot table"; "summarize / group /
  aggregate data"; "pivot by / group by / break down by"; "update / modify / change pivot";
  "remove / delete pivot".
---

# Sheet Pivot Tables — Authoritative Guide for All Pivot Table Operations

> **This reference is the single source of truth for pivot table work in SheetAgent.** You MUST read and follow it before **any** pivot table action — `createPivotTable` (create), `getPivotTableDetail` (inspect), `getPivotTable` (hydrate for modification), `update` (commit), `remove` (delete). Do **NOT** compose pivot table parameters from memory: the two-step create+update pattern, source-column indexing (1-based), and the modify-vs-rebuild decision all live here, and getting them wrong produces empty pivots or a failing `run_command`.

## Pivot Tables

### Two-Step Pattern (REQUIRED)

1. `Range.createPivotTable(pivotTableId, sourceData, name?)` — creates an **empty** pivot table at the anchor cell (the `Range` you call this on is the top-left anchor) and returns a `PivotTable`. `pivotTableId` MUST be unique (caller-generated); the engine uses it for subsequent update/delete/inspect.
2. Configure fields via the returned `PivotTable`, then **call `pt.update()` exactly once** to commit. Without `update()` the pivot is a blank skeleton.

> Use **`set*` setters + a single `update()`** for the lowest op-count and highest reliability. Chained `add*` accumulators are also supported (and equivalent in result), but you still must `update()` at the end.

**Source-column indices are 1-based** (Apps-Script style). `pivotTableId` survives across calls — refer to it in `getPivotTableDetail`, `update`, `remove`.

### Example — Create + Commit in One Call (Recommended)

```javascript
const sheet = SpreadsheetApp.getActiveSheet();
const sourceData = sheet.getRange(2, 1, 10, 5);   // A2:E11
const anchor = sheet.getRange(1, 7);              // G1
const pt = anchor.createPivotTable('pt_demo', sourceData, 'Demo Pivot');
pt.setRowGroups([1])                              // group by col 1 (1-based)
  .setPivotValues([
    { sourceDataColumn: 2, summarizeFunction: 'SUM' },
    { sourceDataColumn: 3, summarizeFunction: 'AVERAGE' },
  ])
  .update();                                      // ← REQUIRED: commit once
// Echo the final config back to the model — saves a second run_command.
return sheet.getPivotTableDetail('pt_demo');
```

### Example — Chained `add*` (Also Valid, End with `update()`)

```javascript
const pt = anchor.createPivotTable('pt_demo', sourceData);
pt.addRowGroup(1);
pt.addPivotValue(2, 'SUM');
pt.addPivotValue(3, 'AVERAGE');
pt.update();                                      // ← REQUIRED
return sheet.getPivotTableDetail('pt_demo');      // optional: confirm
```

### Inspecting an Existing Pivot (Read-Only)

```javascript
return sheet.getPivotTableDetail('pt_demo');
// → { pivot_table_id, pivot_table_name,
//     anchor_sheet_id, anchor_row, anchor_col,                  // 1-based
//     row_group_columns: number[],   // 1-based source columns; [] when not set
//     column_group_columns: number[],// 1-based source columns; [] when not set
//     pivot_values: [{source_data_column /*1-based*/, summarize_function}],
//     filters:      [{source_data_column /*1-based*/}],
//     source_sheet_id,
//     source_data_range?: { sheet_id, start_row, start_col, end_row, end_col, num_rows, num_cols } // 1-based, closed
//   }
```

### Modifying an Existing Pivot (Recommended Path — No Rebuild)

```javascript
// 1) Identify the pivot. Prefer **name** (or a known pivot_table_id) — this
//    works on every host. `getPivotTable(idOrName)` accepts either: it tries
//    the argument as an id first, then falls back to name lookup.
const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetById('000001');
const pt = sheet.getPivotTable('Monthly Summary'); // pass id OR name

// (Optional) When the user only describes the pivot vaguely, you MAY enumerate
// to discover it. `getObjectList` is best-effort: on hosts where the upstream
// tool is not registered yet, it returns `[]` (with a console warning) instead
// of throwing — fall back to the by-name path above in that case.
//   const pivots = sheet.getObjectList(['pivotTable']);
//   const target = pivots.find((o) => o.name.includes('Monthly')) ?? pivots[0];
//   const pt = sheet.getPivotTable(target.object_id);

// 2) Apply the delta. update() is replace-semantic, but the instance already
//    carries existing row_groups / column_groups / pivot_values / filters,
//    so untouched categories stay intact.
const detail = sheet.getPivotTableDetail(undefined, 'Monthly Summary');
const removeCol = 2; // 1-based source column to drop from values
pt.setPivotValues(
  detail.pivot_values
    .filter((v) => v.source_data_column !== removeCol)
    .map((v) => ({
      sourceDataColumn: v.source_data_column,
      summarizeFunction: v.summarize_function,
    })),
).update();

return sheet.getPivotTableDetail(detail.pivot_table_id);
```

### Key Warnings

> ⚠️ Always **prefer `getPivotTable(id|name) + update()`** over delete+recreate when the user asks to tweak an existing pivot. Calling `createPivotTable` with the same `pivot_table_id` returns `pivot_table_id already exists`.

> ⚠️ `update()` is **whole-config replacement**. To change just one category (e.g. "drop one value column"), pull the current config via `getPivotTableDetail` first, mutate the relevant array, then `set*` and `update()`. Categories you don't `set*` on the hydrated instance stay as-is.

> ⚠️ `getObjectList` is **best-effort**: on hosts that haven't registered `sheet_get_object_list` yet, it returns `[]`. Don't loop on it — if it's empty and the user gave you a name/id, go straight to `getPivotTable(idOrName)`.

> ⚠️ Forgetting `pt.update()` after `add*`/`set*` is the #1 cause of "pivot is empty" bugs. Always close the chain with `.update()`.

> 💡 The script's top-level `return` value is surfaced back to the model as `[return] ...` in the `run_command` log. Use it to verify state in the **same** call instead of issuing a follow-up `run_command`.

## API Reference — Pivot Table Types

```typescript
class PivotTable {
  // NOTE: This class is WRITE-ONLY. To READ a pivot table's configuration
  // (row/column groups, values, filters, anchor, source range, etc.), call
  // `sheet.getPivotTableDetail(pivotTableId?, pivotTableName?)` instead.
  // Methods such as getPivotTables / getPivotTableById / getRowGroups /
  // getColumnGroups / getPivotValues / getFilters / getAnchorCell DO NOT EXIST.
  //
  // After configuring fields via add* / set*, you MUST call `update()` exactly
  // once to commit; otherwise the pivot stays an empty skeleton.
  // Source-data column indices are 1-based (Apps-Script convention).

  // Incremental accumulators (chainable):
  addRowGroup(sourceDataColumn: number): PivotTable;
  addColumnGroup(sourceDataColumn: number): PivotTable;
  addPivotValue(sourceDataColumn: number, summarizeFunction:
    | "SUM" | "COUNT" | "COUNTA" | "AVERAGE" | "MAX" | "MIN" | "PRODUCT"
    | "COUNTNUMS" | "STDEV" | "STDEVP" | "VAR" | "VARP"): PivotTable;
  addFilter(sourceDataColumn: number,
    filterCriteria?: { visibleValues?: string[] }): PivotTable;
  addCalculatedPivotValue(name: string, formula: string): PivotTable;

  // Bulk setters — replace the whole field (recommended path).
  setRowGroups(cols: number[]): PivotTable;
  setColumnGroups(cols: number[]): PivotTable;
  setPivotValues(values: Array<{
    sourceDataColumn: number;
    summarizeFunction: string;
  }>): PivotTable;
  setFilters(items: Array<{
    sourceDataColumn: number;
    visibleValues?: string[];
  }>): PivotTable;
  setCalculatedPivotValues(items: Array<{
    name: string;
    formula: string;
  }>): PivotTable;

  // Commit accumulated configuration (replace semantics). REQUIRED.
  update(): PivotTable;

  getSourceDataRange(): Range;
  getName(): string;
  remove(): void;
}

interface PivotTableDetailData {
  pivot_table_id: string;
  pivot_table_name: string;
  anchor_sheet_id: string;
  /** Anchor row (1-based, top-left of the pivot table). */
  anchor_row: number;
  /** Anchor column (1-based). */
  anchor_col: number;
  /** Source-data column indices (1-based) used as row grouping fields. Empty when none. */
  row_group_columns: number[];
  /** Source-data column indices (1-based) used as column grouping fields. Empty when none. */
  column_group_columns: number[];
  /** Value fields with summarize function (SUM/AVERAGE/COUNT/...). `source_data_column` is 1-based. */
  pivot_values: Array<{
    source_data_column: number;
    summarize_function: string;
  }>;
  /** Page-field filters. `source_data_column` is 1-based. */
  filters: Array<{ source_data_column: number }>;
  source_sheet_id: string;
  /** Source range in 1-based, closed-interval coordinates (start_row..end_row inclusive). */
  source_data_range?: {
    sheet_id: string;
    start_row: number;
    start_col: number;
    end_row: number;
    end_col: number;
    num_rows: number;
    num_cols: number;
  };
}

interface PivotTableObjectInfoData {
  row_group_count: number;
  column_group_count: number;
  value_count: number;
}

// Sheet methods related to pivot tables:
// sheet.getPivotTableDetail(pivotTableId?: string, pivotTableName?: string): PivotTableDetailData;
// sheet.getPivotTable(pivotTableIdOrName: string): PivotTable;
// sheet.getObjectList(objectTypes?: string[], namePattern?: string): SheetObjectData[];
// range.createPivotTable(id: string, sourceData: Range, name?: string): PivotTable;
```
