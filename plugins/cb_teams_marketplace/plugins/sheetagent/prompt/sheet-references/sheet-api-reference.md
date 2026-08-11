---
name: sheet-api-reference
description: >
  Complete TypeScript API reference for all SpreadsheetApp, Spreadsheet, Sheet, Range, PivotTable,
  EmbeddedChart, Filter, Utility, and related interfaces available in SheetAgent scripts.
  Read before any `run_command` script that uses APIs you are unsure about, or when you need to
  verify exact method signatures, parameter types, or return shapes. You may ONLY use APIs listed
  here (or in another reference file you have read). Do NOT guess API names from memory.
  Covers: SpreadsheetApp globals / ChartType enum / Spreadsheet / Sheet / Range / PivotTable /
  EmbeddedChart / Filter / Utility / BorderSide / TableInfo / ChartOptions / ConditionalFormat
  interfaces / ProtectRange interfaces (CLOUD_AGENT only).
---

# Sheet API Reference — Complete TypeScript Declarations

> **You may ONLY use the APIs listed below.** Do not guess API names from memory. If an API is not listed here, treat it as unavailable. Calling an undocumented API will cause a runtime error. If the required API does not exist, use JavaScript logic with existing APIs to achieve the goal (e.g., sort data in a JS array then write back with `setValues`). Do NOT guess or invent API methods.

## 1. API Reference

```typescript
declare global {
  var SpreadsheetApp: {
    getActiveSpreadsheet(): Spreadsheet;
    getActiveSheet(): Sheet;
    getActiveRange(): Range;

    Dimension: {
      ROWS: "ROWS";
      COLUMNS: "COLUMNS";
    };
    BorderStyle: {
      DOTTED: "DOTTED";
      DASHED: "DASHED";
      SOLID: "SOLID";
      SOLID_MEDIUM: "SOLID_MEDIUM";
      SOLID_THICK: "SOLID_THICK";
      DOUBLE: "DOUBLE";
    };
    ChartType: {
      AREA: "AREA";
      LINE: "LINE";
      RADAR: "RADAR";
      SCATTER: "SCATTER";
      PIE: "PIE";
      DOUGHNUT: "DOUGHNUT";
      BAR: "BAR";
      COLUMN: "COLUMN";
      PIE_OF_PIE: "PIE_OF_PIE";
      BUBBLE: "BUBBLE";
      /** Custom combo chart — MUST be used together with ChartOptions.series[i].type / .axis.
       *  If every series omits `type`, the backend falls back to its built-in default and
       *  renders **all series as clustered columns** (a semantically neutral fallback;
       *  it does NOT auto-add a line or area, which is rarely what the user wants).
       *  Always set series[i].type / .axis explicitly, OR switch to one of the three
       *  Excel presets below. See the **sheet-charts** reference (Combo Charts) for the recommended patterns. */
      CUSTOM_COMBO: "CUSTOM_COMBO";
      /** Excel preset combo — clustered column + line, sharing one y-axis. The last series defaults to the line. */
      CLUSTERED_COLUMN_AND_LINE_COMBO: "CLUSTERED_COLUMN_AND_LINE_COMBO";
      /** Excel preset combo — clustered column + line, with the line bound to the SECONDARY axis.
       *  **Strongly recommended for "revenue + growth-rate" style dual-axis scenarios** where the
       *  two metrics have very different magnitudes. */
      CLUSTERED_COLUMN_AND_LINE_ON_SECONDARY_AXIS_COMBO: "CLUSTERED_COLUMN_AND_LINE_ON_SECONDARY_AXIS_COMBO";
      /** Excel preset combo — stacked area + clustered column. The first series defaults to the area. */
      STACKED_AREA_AND_CLUSTERED_COLUMN_COMBO: "STACKED_AREA_AND_CLUSTERED_COLUMN_COMBO";
      TREEMAP: "TREEMAP";
      STACKED_BAR: "STACKED_BAR";
      PERCENT_STACKED_BAR: "PERCENT_STACKED_BAR";
      STACKED_COLUMN: "STACKED_COLUMN";
      PERCENT_STACKED_COLUMN: "PERCENT_STACKED_COLUMN";
      STACKED_LINE: "STACKED_LINE";
      PERCENT_STACKED_LINE: "PERCENT_STACKED_LINE";
      MARKER_LINE: "MARKER_LINE";
      STACKED_MARKER_LINE: "STACKED_MARKER_LINE";
      PERCENT_STACKED_MARKER_LINE: "PERCENT_STACKED_MARKER_LINE";
      STACKED_AREA: "STACKED_AREA";
      PERCENT_STACKED_AREA: "PERCENT_STACKED_AREA";
      BAR_OF_PIE: "BAR_OF_PIE";
      SMOOTH_LINE_AND_MARKER_SCATTER: "SMOOTH_LINE_AND_MARKER_SCATTER";
      SMOOTH_LINE_SCATTER: "SMOOTH_LINE_SCATTER";
      STRAIGHT_LINE_AND_MARKER_SCATTER: "STRAIGHT_LINE_AND_MARKER_SCATTER";
      STRAIGHT_LINE_SCATTER: "STRAIGHT_LINE_SCATTER";
      MARKER_RADAR: "MARKER_RADAR";
      FILLED_RADAR: "FILLED_RADAR";
      FUNNEL: "FUNNEL";
      HISTOGRAM: "HISTOGRAM";
      WATERFALL: "WATERFALL";
    };
  };

  class Spreadsheet {
    getActiveSheet(): Sheet;
    getActiveRange(): Range;
    getSheetById(sheetId: string): Sheet;
    getSheetByName(name: string): Sheet | null;
    getSheets(): Sheet[];
    insertSheet(): Sheet;
    insertSheet(sheetIndex: number): Sheet;
    insertSheet(sheetName: string): Sheet;
    insertSheet(sheetName: string, sheetIndex: number): Sheet;
    deleteSheet(sheet: Sheet): void;
    moveActiveSheet(pos: number): void;
    moveSheet(srcIndex: number, desIndex: number): void;
    /** Duplicate an existing worksheet; newName is optional (max 31 chars). */
    copySheet(sheet: Sheet, newName?: string): Sheet;
  }

  class Sheet {
    getName(): string;
    getSheetId(): string;
    getLastRow(): number;
    getLastColumn(): number;

    getRange(a1Notation: string): Range;
    getRange(row: number, col: number): Range;
    getRange(row: number, col: number, numRows: number, numCols: number): Range;
    getDataRange(): Range;
    getActiveRange(): Range;

    /** Read the FULL configuration of an existing pivot table on this sheet.
     *  This is the ONLY way to inspect a pivot table — the PivotTable class
     *  is write-only and has no getRowGroups()/getPivotValues()/getFilters()/
     *  getAnchorCell() etc. Do NOT call GAS-style APIs like
     *  sheet.getPivotTables() / spreadsheet.getPivotTableById() — they DO NOT EXIST.
     *  Example: const detail = sheet.getPivotTableDetail("pt_demo");
     *           // detail.row_group_columns / column_group_columns /
     *           // source_data_range / anchor_row / anchor_col ... */
    getPivotTableDetail(pivotTableId?: string, pivotTableName?: string): PivotTableDetailData;
    getObjectList(objectTypes?: string[], namePattern?: string): SheetObjectData[];
    /** Hydrate an existing pivot table by id (or name) into a PivotTable instance
     *  that is PRE-POPULATED with the current row/column groups, values and filters.
     *  Use this — NOT `createPivotTable` with the same id — to modify an existing pivot.
     *  After mutating with set*/add* call `pt.update()` once to commit. Replace-semantic
     *  applies, but untouched categories stay intact because the instance already carries
     *  the existing config. */
    getPivotTable(pivotTableIdOrName: string): PivotTable;

    insertRows(row: number, numRows?: number): void;
    deleteRow(row: number): void;
    deleteRows(row: number, numRows: number): void;
    /** Move `numRows` rows starting at `startRow` so they land before `destinationRow` (all 1-based). */
    moveRows(startRow: number, numRows: number, destinationRow: number): void;
    /** Move `numColumns` columns starting at `startColumn` so they land before `destinationColumn` (all 1-based). */
    moveColumns(startColumn: number, numColumns: number, destinationColumn: number): void;

    /** Row height APIs — unit: pixels (px). Both parameters and return values are in pixels. */
    getRowHeight(row: number): number;
    setRowHeight(row: number, height: number): void;
    setRowHeights(startRow: number, numRows: number, height: number): void;
    setRowHeightsForced(startRow: number, numRows: number, height: number): void;

    insertColumns(col: number, numCols?: number): void;
    deleteColumn(col: number): void;
    deleteColumns(col: number, numCols: number): void;
    /** Column width APIs — unit: pixels (px). Both parameters and return values are in pixels. */
    getColumnWidth(col: number): number;
    setColumnWidth(col: number, width: number): void;
    setColumnWidths(startCol: number, numCols: number, width: number): void;

    /** Freeze top N rows (0 = unfreeze rows, keeps column freeze). */
    setFrozenRows(rows: number): void;
    /** Freeze left N columns (0 = unfreeze columns, keeps row freeze). */
    setFrozenColumns(columns: number): void;

    /** Hide / show rows, columns and sheet tab. Indexes are 1-based; data is preserved (UI-only). */
    hideRow(rowIndex: number): Sheet;
    hideRows(rowIndex: number, numRows?: number): Sheet;
    showRows(rowIndex: number, numRows?: number): Sheet;
    unhideRow(rowIndex: number): Sheet;
    hideColumn(columnIndex: number): Sheet;
    hideColumns(columnIndex: number, numColumns?: number): Sheet;
    showColumns(columnIndex: number, numColumns?: number): Sheet;
    unhideColumn(columnIndex: number): Sheet;
    hideSheet(): Sheet;
    showSheet(): Sheet;
    isSheetHidden(): boolean;

    newChart(
      drawingId: string,
      chartType: "AREA" | "LINE" | "RADAR" | "SCATTER" | "PIE" | "DOUGHNUT" | "BAR" | "COLUMN"
        | "PIE_OF_PIE" | "BUBBLE" | "TREEMAP" | "FUNNEL" | "HISTOGRAM" | "WATERFALL"
        // Combo chart types (see the **sheet-charts** reference — Combo Charts):
        // - CUSTOM_COMBO MUST be paired with ChartOptions.series[i].type / .axis.
        // - The other three are Excel presets — they render correctly without series.type.
        | "CUSTOM_COMBO"
        | "CLUSTERED_COLUMN_AND_LINE_COMBO"
        | "CLUSTERED_COLUMN_AND_LINE_ON_SECONDARY_AXIS_COMBO"
        | "STACKED_AREA_AND_CLUSTERED_COLUMN_COMBO"
        | "STACKED_BAR" | "PERCENT_STACKED_BAR"
        | "STACKED_COLUMN" | "PERCENT_STACKED_COLUMN"
        | "STACKED_LINE" | "PERCENT_STACKED_LINE"
        | "MARKER_LINE" | "STACKED_MARKER_LINE" | "PERCENT_STACKED_MARKER_LINE"
        | "STACKED_AREA" | "PERCENT_STACKED_AREA"
        | "BAR_OF_PIE"
        | "SMOOTH_LINE_AND_MARKER_SCATTER" | "SMOOTH_LINE_SCATTER"
        | "STRAIGHT_LINE_AND_MARKER_SCATTER" | "STRAIGHT_LINE_SCATTER"
        | "MARKER_RADAR" | "FILLED_RADAR",
      dataRange: Range,
      anchorRow: number, anchorCol: number,
      offsetX: number, offsetY: number,
      width: number, height: number,
      options?: ChartOptions,
    ): EmbeddedChart;
    /** Compatibility no-op: chart is already inserted at newChart() time. */
    insertChart(chart: EmbeddedChart): void;
    // To DELETE a chart, pass its chartId directly:
    //   sheet.removeChart('chart_001');
    // No need to call getCharts() first. If you don't know the id, look it up via getCharts()
    // and then pass the matched chart's id.
    // NEVER call newChart(existingId, ...) to obtain a handle — chartId must be unique
    // at creation, so reusing an existing id conflicts in the backend instead of returning the chart.
    removeChart(chartId: string): void;
    // Insert an image at the specified cell position. row and col are 1-based.
    // imageData: base64 encoded image data or data URI (e.g. "data:image/png;base64,...")
    insertImage(row: number, col: number, imageData: string): void;
    // To DELETE an image
    // Note: this API is not yet implemented;
    removeImage(drawingId: string): void;
    getCharts(): EmbeddedChart[];
    // columns[].col: 0-based column index, e.g., to filter the 4th column, pass col = 3
    createFilter(range: Range): Filter;
    // Handle to this sheet's existing filter (adjust/remove without re-creating).
    getFilter(): Filter;
    getSheetName(): string;

    // [CLOUD_AGENT only]
    // Mark a range as private (content masked from viewers); isUnset=true removes the marking. All params 1-based.
    setPrivateRange(startRow: number, startCol: number, numRows: number, numCols: number, isUnset?: boolean): void;
    // Set dropdown/multi-select validation on A1-notation ranges; type NONE removes the rule.
    setDataValidation(type: "LIST" | "MULTIPLE_LIST" | "NONE", ranges: string[], options?: Array<{ text: string; id?: string; text_color?: string; bg_color?: string }>): void;
    // Set dropdown/multi-select validation on whole columns; colIndexes are 0-based [{start,end}]; ignoreRows skips header rows.
    setDataValidationByColumns(type: "LIST" | "MULTIPLE_LIST" | "NONE", colIndexes: Array<{ start: number; end: number }>, ignoreRows?: number, options?: Array<{ text: string; id?: string; text_color?: string; bg_color?: string }>): void;

    /** Add a new conditional format rule. Returns { cf_id } — save for update/remove. */
    addConditionalFormat(params: AddConditionalFormatParams): { cf_id: string };
    /** Query existing rules on this sheet (optionally filtered by range). */
    getConditionalFormats(params: GetConditionalFormatsParams): { items: ConditionalFormatItem[] };
    /** Full replacement of an existing rule identified by cf_id. */
    updateConditionalFormat(params: UpdateConditionalFormatParams): void;
    /** Remove one rule by cf_id, or all rules when is_remove_all: true. */
    removeConditionalFormat(params: RemoveConditionalFormatParams): void;

    // [CLOUD_AGENT only]
    /** Protect a range or the entire sheet. Returns { protect_range_id } — save for update/delete. */
    addProtectRange(params: AddProtectRangeParams): { protect_range_id: string };
    /** Change the protected range identified by protect_range_id. */
    updateProtectRange(params: UpdateProtectRangeParams): void;
    /** Remove a protection by protect_range_id. */
    deleteProtectRange(params: DeleteProtectRangeParams): void;
    /** List all protections on this sheet. */
    getProtectRanges(params: GetProtectRangesParams): { items: ProtectRangeItem[] };
  }

  /** Return shape of Range.auditFormulaConsistency(). All row/col indices are 0-based. */
  interface FormulaConsistencyReport {
    /** true when every formula cell shares the majority R1C1 pattern and there are no gaps. */
    is_consistent: boolean;
    total_formula_cells: number;
    distinct_patterns: number;
    majority_pattern: string;
    majority_count: number;
    groups: Array<{ r1c1: string; count: number; cells: Array<{ row: number; col: number }> }>;
    outliers: Array<{ row: number; col: number; r1c1: string }>;
    gaps: Array<{ row: number; col: number }>;
  }

  interface Range {
    getSheetId(): string;
    getRow(): number;
    getColumn(): number;
    getNumRows(): number;
    getNumColumns(): number;
    getA1Notation(): string;

    getValue(): string | number | boolean | null;
    getValues(): any[][];
    setValue(value: any): void;
    setValues(values: any[][]): void;
    clear(): void;
    clearFormat(): Range;

    setFormula(formula: string): void;
    setFormulas(formulas: string[][]): void;
    getFormula(): string;
    getFormulas(): string[][];
    /** Audit this rectangle for formula-pattern consistency (R1C1-normalised):
     *  flags outlier formulas and non-formula gaps. Useful for the audit-spreadsheet flow. */
    auditFormulaConsistency(): FormulaConsistencyReport;

    getNumberFormat(): string;
    getNumberFormats(): string[][];
    setNumberFormat(fmt: string): void;
    setNumberFormats(fmts: string[][]): void;

    getBackground(): string;
    getBackgrounds(): string[][];
    setBackground(color: string | null): void;
    setBackgrounds(colors: (string | null)[][]): void;

    setFontColor(color: string): void;
    setFontColors(colors: string[][]): void;
    getFontColor(): string;
    getFontColors(): string[][];
    setFontFamily(family: string): void;
    setFontFamilies(families: string[][]): void;
    getFontFamily(): string;
    getFontFamilies(): string[][];
    setFontSize(size: number): void;
    setFontSizes(sizes: number[][]): void;
    getFontSize(): number;
    getFontSizes(): number[][];
    setFontLine(line: "underline" | "line-through" | "none"): void;
    setFontLines(lines: string[][]): void;
    getFontLine(): string;
    getFontLines(): string[][];
    setFontWeight(weight: "bold" | "normal"): void;
    setFontWeights(weights: string[][]): void;
    getFontWeight(): string;
    getFontWeights(): string[][];
    setFontStyle(style: "italic" | "normal"): void;
    setFontStyles(styles: string[][]): void;
    getFontStyle(): string;
    getFontStyles(): string[][];
    setWrap(wrap: boolean): void;
    setWraps(wraps: boolean[][]): void;
    getWrap(): boolean;
    getWraps(): boolean[][];
    setVerticalAlignment(align: "top" | "middle" | "bottom"): void;
    setVerticalAlignments(aligns: string[][]): void;
    getVerticalAlignment(): string;
    getVerticalAlignments(): string[][];

    setHorizontalAlignment(align: "left" | "center" | "right" | "general" | "general-left" | "justify"): void;
    setHorizontalAlignments(aligns: string[][]): void;
    getHorizontalAlignment(): string;
    getHorizontalAlignments(): string[][];

    merge(): void;
    mergeAcross(): void;
    mergeVertically(): void;
    breakApart(): void;

    createPivotTable(id: string, sourceData: Range, name?: string): PivotTable;

    getBorder(): { top: BorderSide | null; bottom: BorderSide | null; left: BorderSide | null; right: BorderSide | null };
    getBorders(): { top: BorderSide | null; bottom: BorderSide | null; left: BorderSide | null; right: BorderSide | null }[][];
    setBorder(
      top: boolean, left: boolean, bottom: boolean, right: boolean,
      vertical: boolean, horizontal: boolean, color?: string, style?: string,
    ): Range;
    setBorders(borders: { top: BorderSide | null; bottom: BorderSide | null; left: BorderSide | null; right: BorderSide | null }[][]): Range;
    insertCells(shiftDimension: "ROWS" | "COLUMNS"): Range;
    deleteCells(shiftDimension: "ROWS" | "COLUMNS"): void;
    sort(column: number): Range;
    sort(spec: { column: number; ascending?: boolean }): Range;
    sort(specs: { column: number; ascending?: boolean }[]): Range;
  }

  class Utility {
    static sleep(ms: number): void;
    static describeSheets(ss: Spreadsheet): { name: string; rows: number; cols: number }[];

    static readDataInBatches(
      sheet: Sheet, startRow: number, numCols: number,
      cb: (rows: any[][]) => void, batchSize?: number,
    ): void;

    static groupBy(data: any[][], keyCol: number, valueCol: number): {
      key: any; sum: number; count: number; avg: number;
    }[];
    static validateData(data: any[][], keyCols: number[]): {
      emptyRows: number[]; duplicateRows: number[];
    };

    static deleteRowsWhere(
      sheet: Sheet, info: TableInfo,
      predicate: (row: any[]) => boolean,
    ): { deleted: number; remaining: number };
    static keepRowsWhere(
      sheet: Sheet, info: TableInfo,
      predicate: (row: any[]) => boolean,
    ): { kept: number; removed: number };
    static deduplicateRows(sheet: Sheet, info: TableInfo, keyCol: number): {
      kept: number; removed: number;
    };

    static findAndReplace(sheet: Sheet, info: TableInfo, search: string, replace: string): number;
    static copyRowsTo(
      src: Sheet, dst: Sheet, srcInfo: TableInfo,
      predicate: (row: any[]) => boolean,
    ): number;
  }

  interface BorderSide {
    color: string;  // hex color e.g. "FF000000"
    style: string;  // "SOLID" | "SOLID_MEDIUM" | "SOLID_THICK" | "DASHED" | "DOTTED" | "DOUBLE"
  }

  interface TableInfo {
    startRow: number; startCol: number; endRow: number; endCol: number;
    orientation: "ROW" | "COLUMN" | "MATRIX";
    headers: string[]; numCols: number; numDataRows: number;
    cells: Record<string, any>;
    formulas: Record<string, string>;
    formats: Record<string, string>;
    hasMore: boolean;
  }

  enum FilterCriteriaType {
    VALUE = 0,
    COLOR = 1,
    CONDITION = 2,
  }

  interface FilterColumnCriteria {
    // col: 0-based column index, e.g., to filter the 4th column, pass col = 3
    col: number;
    criteria: {
      type: FilterCriteriaType;
      visible_values: string[];
    };
  }

  interface ChartTextStyle {
    fontFamily?: string;
    fontSize?: number;
    color?: string;
    bold?: boolean;
    italic?: boolean;
  }

  interface ChartOptions {
    // Note: there is NO chart-level `textStyle` here. Backend silently
    // ignores `textStyle` at the top of `options`; set `textStyle` on each
    // visible sub-block instead (see the **sheet-charts** reference — recommended sizes:
    // title 16/bold, axis title 12/bold, legend 12, tick label 11,
    // data label 10–11).
    title?: {
      text?: string;
      visible?: boolean;
      overlay?: boolean;
      textStyle?: ChartTextStyle;
    };
    /** Note: there is intentionally NO `type` field here. The x-axis type
     *  (CATEGORY / VALUE / DATE) is inferred from the source column's data type
     *  at chart creation and is **immutable** afterwards — the backend rejects
     *  any attempt to set/change it with `xAxis.type switching ... is not
     *  supported` and fails the whole run_command. To change the axis type,
     *  fix the source column (its numberFormat / value) and re-create the
     *  chart via newChart(...). See the **sheet-charts** reference (Axes). */
    xAxis?: {
      visible?: boolean;
      title?: {
        text?: string;
        visible?: boolean;
        textStyle?: ChartTextStyle;
      };
      labelPosition?: "HIGH" | "LOW" | "NEXT_TO" | "NONE";
      numberFormat?: string;
      majorTickMark?: "CROSS" | "INSIDE" | "OUTSIDE" | "NONE";
      minorTickMark?: "CROSS" | "INSIDE" | "OUTSIDE" | "NONE";
      gridlines?: boolean;
      minorGridlines?: boolean;
      textStyle?: ChartTextStyle;
    };
    yAxis?: {
      visible?: boolean;
      title?: {
        text?: string;
        visible?: boolean;
        textStyle?: ChartTextStyle;
      };
      scale?: {
        min?: number;
        max?: number;
        orientation?: "MIN_MAX" | "MAX_MIN";
      };
      majorUnit?: number;
      minorUnit?: number;
      labelPosition?: "HIGH" | "LOW" | "NEXT_TO" | "NONE";
      numberFormat?: string;
      majorTickMark?: "CROSS" | "INSIDE" | "OUTSIDE" | "NONE";
      minorTickMark?: "CROSS" | "INSIDE" | "OUTSIDE" | "NONE";
      gridlines?: boolean;
      minorGridlines?: boolean;
      textStyle?: ChartTextStyle;
    };
    /** Secondary y-axis (right side). Only takes effect in combo charts that have
     *  at least one SECONDARY series; ignored otherwise. Field shape is identical
     *  to yAxis — the backend matches them by OOXML val_ax.ax_pos == 'r'.
     *  Compatibility: when `secondaryYAxis` is omitted, the backend falls back and
     *  applies `yAxis` to the secondary axis too (legacy behavior). To keep primary
     *  and secondary `scale.min/max` independent, you MUST provide both explicitly.
     *  Typical example (column revenue + crosses-zero growth-rate line; each axis
     *  computed from a data-scan (see the **sheet-charts** reference) on its own source columns):
     *    yAxis:          { scale: { min: 0,     max: 500  }, numberFormat: '#,##0', gridlines: true  },
     *    secondaryYAxis: { scale: { min: -0.20, max: 0.40 }, numberFormat: '0.0%',  gridlines: false } */
    secondaryYAxis?: {
      visible?: boolean;
      title?: {
        text?: string;
        visible?: boolean;
        textStyle?: ChartTextStyle;
      };
      scale?: {
        min?: number;
        max?: number;
        orientation?: "MIN_MAX" | "MAX_MIN";
      };
      majorUnit?: number;
      minorUnit?: number;
      labelPosition?: "HIGH" | "LOW" | "NEXT_TO" | "NONE";
      numberFormat?: string;
      majorTickMark?: "CROSS" | "INSIDE" | "OUTSIDE" | "NONE";
      minorTickMark?: "CROSS" | "INSIDE" | "OUTSIDE" | "NONE";
      gridlines?: boolean;
      minorGridlines?: boolean;
      textStyle?: ChartTextStyle;
    };
    legend?: {
      visible?: boolean;
      position?: "TOP" | "BOTTOM" | "LEFT" | "RIGHT" | "TOP_RIGHT";
      overlay?: boolean;
      textStyle?: ChartTextStyle;
    };
    series?: Array<{
      color?: string;
      dataLabel?: {
        visible?: boolean;
        showValue?: boolean;
        showPercentage?: boolean;
        showCategoryName?: boolean;
        showSeriesName?: boolean;
        position?:
          | "BEST_FIT"
          | "CENTER"
          | "INSIDE_BASE"
          | "INSIDE_END"
          | "OUTSIDE_END"
          | "ABOVE"
          | "BELOW"
          | "LEFT"
          | "RIGHT";
        numberFormat?: string;
        textStyle?: ChartTextStyle;
      };
      /** Per-series chart type (combo charts only). When any series[i].type
       *  disagrees with the top-level chartType, the shim auto-rewrites the
       *  whole chart_type to customCombo on the wire. OOXML only allows mixing
       *  COLUMN / STACKED_COLUMN / LINE / MARKER_LINE / AREA / STACKED_AREA;
       *  other values (PIE / SCATTER / BUBBLE / RADAR / ...) are silently
       *  ignored by the backend. See the **sheet-charts** reference (Combo Charts). */
      type?:
        | "COLUMN" | "STACKED_COLUMN"
        | "LINE" | "MARKER_LINE"
        | "AREA" | "STACKED_AREA";
      /** Numeric axis this series is bound to. SECONDARY = right-side secondary
       *  axis (required for "revenue + growth-rate" style dual-axis charts);
       *  defaults to PRIMARY. Only takes effect in combo charts (a chart with
       *  at least one series whose type differs from the top-level chartType,
       *  or where the top-level type is CUSTOM_COMBO / a secondary-axis preset). */
      axis?: "PRIMARY" | "SECONDARY";
    }>;
  }

  class EmbeddedChart {
    getChartType(): string;
    getDrawingId(): string;
    getTitle(): string;
    /** Top-left anchor row (0-based); -1 when unknown. Use with getCharts() to
     *  probe existing charts' positions before placing a new one. */
    getAnchorRow(): number;
    /** Top-left anchor column (0-based); -1 when unknown. */
    getAnchorCol(): number;
    /** Chart width in px; -1 when the backend does not report a size. */
    getWidth(): number;
    /** Chart height in px; -1 when the backend does not report a size. */
    getHeight(): number;
    setOptions(options: ChartOptions): EmbeddedChart;
    getOptions(): ChartOptions;
    setChartType(chartType: string): EmbeddedChart;
    setTitle(title: string): EmbeddedChart;
    setPosition(anchorRow: number, anchorCol: number, offsetX: number, offsetY: number): EmbeddedChart;
    setSize(width: number, height: number): EmbeddedChart;
    setDataRange(range: Range): EmbeddedChart;
    getDataRange(): Range;
    remove(): void;
  }

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

  class Filter {
    remove(): void;
    /** Set the "visible values" criteria for one column (columnPosition is 1-based).
     *  An empty visibleValues array hides every value in that column; columns not
     *  passed keep their existing criteria. */
    setColumnFilterCriteria(columnPosition: number, visibleValues: string[]): void;
  }

  interface AdapterGridRange {
    sheet_id: string;
    start_row_index: number;
    start_col_index: number;
    end_row_index: number;
    end_col_index: number;
  }

  interface ChartObjectInfoData {
    chart_type: string;
  }

  interface PivotTableObjectInfoData {
    row_group_count: number;
    column_group_count: number;
    value_count: number;
  }

  interface TableObjectInfoData {
    has_header: boolean;
    column_count: number;
  }

  interface FloatImageObjectInfoData {
    width: number;
    height: number;
  }

  interface SheetObjectData {
    object_id: string;
    object_type: string;
    name: string;
    display_range?: AdapterGridRange;
    data_range?: AdapterGridRange;
    chart_info?: ChartObjectInfoData;
    pivot_table_info?: PivotTableObjectInfoData;
    table_info?: TableObjectInfoData;
    float_image_info?: FloatImageObjectInfoData;
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

  type ConditionalFormatOp =
    | "GT" | "LT" | "GTE" | "LTE" | "EQ" | "NEQ"
    | "BETWEEN" | "NOT_BETWEEN"
    | ">" | "<" | ">=" | "<=" | "==" | "!=";

  interface ConditionalFormatStyle {
    /** Hex color with leading #, e.g. "#FF0000" */
    font_color?: string;
    /** Hex color with leading #, e.g. "#FFFF00" */
    bg_color?: string;
    bold?: boolean;
    italic?: boolean;
    underline?: boolean;
    strikethrough?: boolean;
  }

  interface ConditionalFormatRule {
    /** Rule type — determines which extra sub-object is required. */
    type:
      | "CF_CELL_IS"        // requires cell_is
      | "CF_UNIQUE_VALUES"  // no extra fields
      | "CF_DUPLICATE_VALUES" // no extra fields
      | "CF_TOP10"          // requires top10
      | "CF_ABOVE_AVERAGE"; // optional above_average sub-object
    /** Required when type === "CF_CELL_IS" */
    cell_is?: {
      op: ConditionalFormatOp;
      /** One formula for single-value ops; two formulas for BETWEEN / NOT_BETWEEN. */
      formulas: string[];
    };
    /** Required when type === "CF_TOP10" */
    top10?: {
      /** Number of top/bottom items or percentage points (1–1000). */
      rank: number;
      /** true = bottom N instead of top N */
      bottom?: boolean;
      /** true = treat rank as a percentage */
      percent?: boolean;
    };
    /** Optional when type === "CF_ABOVE_AVERAGE" */
    above_average?: {
      /** true = above average (default); false = below average */
      above_average?: boolean;
      /** true = include cells equal to the average */
      equal_average?: boolean;
      /** Standard deviation multiplier (0 = use mean directly) */
      std_dev?: number;
    };
    /** At least one style field must be set. */
    style: ConditionalFormatStyle;
  }

  interface AddConditionalFormatParams {
    /** Range strings — each entry is "SheetID$A1:B100" or plain "A1:B100". */
    ranges: string[];
    rule: ConditionalFormatRule;
  }

  interface GetConditionalFormatsParams {
    /** Optional: filter results to rules that overlap these ranges. */
    ranges?: string[];
  }

  interface ConditionalFormatItem {
    cf_id: string;
    priority: number;
    ranges: string[];
    rule: ConditionalFormatRule;
  }

  interface UpdateConditionalFormatParams {
    cf_id: string;
    ranges: string[];
    rule: ConditionalFormatRule;
  }

  interface RemoveConditionalFormatParams {
    /** Remove a specific rule by id. Mutually exclusive with is_remove_all. */
    cf_id?: string;
    /** true = remove ALL rules on the sheet. Mutually exclusive with cf_id. */
    is_remove_all?: boolean;
  }

  // [CLOUD_AGENT only]
  interface ProtectRangeCoord {
    /** 0-based row index (closed interval). */
    start_row: number;
    /** 0-based column index (closed interval). */
    start_col: number;
    end_row: number;
    end_col: number;
  }

  interface AddProtectRangeParams {
    sheet_id: string;
    /** Protect a specific cell range. Mutually exclusive with whole_sheet. */
    range?: ProtectRangeCoord;
    /** true = protect the entire sheet. Mutually exclusive with range. */
    whole_sheet?: boolean;
  }

  interface UpdateProtectRangeParams {
    sheet_id: string;
    protect_range_id: string;
    /** New range to protect. Mutually exclusive with whole_sheet. */
    range?: ProtectRangeCoord;
    /** Forward-compat flag; the current backend requires `range` and may ignore this field. */
    whole_sheet?: boolean;
  }

  interface DeleteProtectRangeParams {
    sheet_id: string;
    protect_range_id: string;
  }

  interface GetProtectRangesParams {
    sheet_id: string;
  }

  interface ProtectRangeItem {
    protect_range_id: string;
    /** Present when a specific range is protected (not whole_sheet). */
    range?: ProtectRangeCoord;
    /** true when the entire sheet is protected. */
    whole_sheet?: boolean;
  }
}
```

## Key Constraints

- All batch setter methods require 2D arrays with dimensions exactly matching the target `Range`
- Use `clear()` to erase content; `setValue(null)` writes the literal string `"null"`
- After `setFormula()`, verify the result and fall back if the formula errors
- Delete columns from back to front to avoid index shifting
- `groupBy` and `deduplicateRows` use **0-based** column indices
- `newChart()` uses **0-based** `anchorRow` and `anchorCol`
- Color values must be hex strings with a leading `#`
- If a needed API is not listed above, use plain JavaScript with documented APIs to achieve the goal

## API Constraint

- You may **ONLY** use APIs documented in this API Reference, in a reference file you have read (e.g. the `sheet-charts` reference), or in currently loaded skills
- Do **NOT** rely on prior knowledge of any API — if it is not in the API Reference, a reference file you have read, or a loaded skill, it does not exist
- Calling an undocumented API will cause a runtime error
- If the required API does not exist, use JavaScript logic with existing APIs to achieve the goal (e.g., sort data in JS array then write back with setValues). Do NOT guess or invent API methods.
