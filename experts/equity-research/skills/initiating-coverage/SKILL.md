---
name: initiating-coverage
description: Create institutional-quality equity research initiation reports through a 5-task workflow. Tasks 1 & 2 can run in parallel. Tasks 3-5 have sequential dependencies. Each task produces specific deliverables. Triggers on "initiating coverage", "first coverage report", "write initiation report".
---

# Initiating Coverage

Create institutional-quality equity research initiation reports (JPMorgan/Goldman Sachs/Morgan Stanley format) through a structured 5-task workflow.

## Task Overview

| Task | Name | Dependencies | Output |
|------|------|-------------|--------|
| **1** | Company Research | None | 6-8K word .md document |
| **2** | Financial Modeling | None | Excel model (6 tabs) |
| **3** | Valuation Analysis | Task 2 | Valuation .md + Excel tabs |
| **4** | Chart Generation | Tasks 1, 2, 3 | 25-35 PNG charts (.zip) |
| **5** | Report Assembly | ALL (1-4) | 30-50 page .docx report |

**Parallelism**: Tasks 1 & 2 have no mutual dependency — execute them in parallel when possible to save time. Tasks 3→4→5 are strictly sequential.

## Execution Rules

- Execute ONE task per user request unless Tasks 1 & 2 are both requested (parallel OK)
- Verify prerequisites before starting Tasks 3-5
- Deliver specified outputs only — no extra summaries or completion documents
- Default font: Times New Roman

---

## Task 1: Company Research

**Purpose**: Research business, management, competitive position, industry, and risks.

**Prerequisites**: Company name or ticker only.

**Process**: Load `references/task1-company-research.md` for detailed workflow.

**Output**: `[Company]_Research_Document_[Date].md` (6,000-8,000 words)
- Company overview & history
- Management bios (300-400 words × 3-4 execs)
- Products & services analysis
- Industry overview & competitive analysis (5-10 competitors)
- TAM sizing
- Risk assessment (8-12 risks across 4 categories)

---

## Task 2: Financial Modeling

**Purpose**: Build comprehensive Excel financial model with projections.

**Prerequisites**: Access to 10-K/financial statements OR user-provided financials.

**Process**: Load `references/task2-financial-modeling.md` for detailed workflow.

**Output**: `[Company]_Financial_Model_[Date].xlsx` (6 tabs)
1. Revenue Model — product + geography breakdown
2. Income Statement — 40-50 line items, 3-5Y historical + 5Y projected
3. Cash Flow Statement — historical + projected
4. Balance Sheet — historical + projected
5. Scenarios — Bull/Base/Bear comparison
6. DCF Inputs — prepared for Task 3

---

## Task 3: Valuation Analysis

**Purpose**: DCF, comparables, and precedent transactions valuation.

**Prerequisites**: Task 2 financial model must exist.

**Process**: Load `references/task3-valuation.md` for detailed workflow.

**Output**:
- `[Company]_Valuation_Analysis_[Date].md` (4-6 pages)
- 4 Excel tabs added to Task 2 file (DCF, Sensitivity, Comps, Summary)
- Price target, recommendation (BUY/HOLD/SELL), upside %

---

## Task 4: Chart Generation

**Purpose**: Generate 25-35 professional financial charts.

**Prerequisites**: Tasks 1, 2, 3 all complete + external market data access.

**Process**: Load `references/task4-chart-generation.md` for detailed workflow.

**4 Mandatory Charts** ⭐:
- chart_03: Revenue by product (stacked area)
- chart_04: Revenue by geography (stacked bar)
- chart_28: DCF sensitivity (2-way heatmap)
- chart_32: Valuation football field (horizontal bars)

**Output**: `[Company]_Charts_[Date].zip` (25-35 PNG files at 300 DPI + chart_index.txt)

---

## Task 5: Report Assembly

**Purpose**: Assemble comprehensive final DOCX report from all previous outputs.

**Prerequisites**: ALL Tasks 1-4 must be complete.

**Process**: Load `references/task5-report-assembly.md` for detailed workflow.

**Key principles**:
- Use DOCX and XLSX skills for file operations
- Text-dense with charts every 200-300 words (60-80% page coverage)
- Copy Task 1 content verbatim, extract Task 2/3 tables, embed Task 4 charts

**Output**: `[Company]_Initiation_Report_[Date].docx`
- 30-50 pages, 10,000-15,000 words
- 25-35 embedded charts, 12-20 tables
- Professional formatting with clickable hyperlinks

---

## Task Reference Files

Load ONLY the reference file for the task being performed:
- `references/task1-company-research.md` — Company research workflow
- `references/task2-financial-modeling.md` — Financial modeling workflow
- `references/task3-valuation.md` — Valuation methodology
- `references/task4-chart-generation.md` — Chart generation workflow
- `references/task5-report-assembly.md` — Report assembly workflow
- `assets/report-template.md` — Report structure template
- `assets/quality-checklist.md` — Quality checks

## Quality Standards

- Institutional quality (JPMorgan/Goldman/Morgan Stanley level)
- All numbers cite sources with timestamps
- Stale data (>90d) labeled [STALE], missing data labeled [MISSING]
- All citations include clickable hyperlinks
