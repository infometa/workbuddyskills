# 报告格式与设计规范 & Design Specifications

## Color Palette
| Role | Hex Code | Usage |
|------|----------|-------|
| Primary | #1B2A4A | Headings, section titles, chart primary color |
| Secondary | #2E5090 | Subheadings, chart secondary color, accent lines |
| Table Background | #D6E4F0 | Alternating row backgrounds, callout boxes |
| White | #FFFFFF | Page background, text on dark backgrounds |
| Dark Text | #333333 | Body text |

## Typography
| Element | Font | Weight | Notes |
|---------|------|--------|-------|
| Chinese Body | Noto Serif SC ExtraLight | 200 | Serif for Chinese text |
| English Body | Lora | Regular | Serif for English text |
| Headings | Poppins | Bold/SemiBold | Sans-serif for titles |
| Data/Tables | Default system | Regular | Monospace-friendly |

## Cover Page Structure (5 Layers)

1. **专家标识** (top center)
2. **Client Company Chinese Name** (主标题, large, centered)
3. **Report Product Short Name** (副标题, medium, centered)
4. **品牌标语**: "让天下没有难做的交易" (centered)
5. **Attribution Line** (bottom center): "MAI Deal Inc. | [Date]"

### Cover Page Prohibited Elements
- Core demand labels
- Report type labels (e.g., "Type A Report")
- Version numbers
- "客户：" prefix labels

## Report Body Formatting Rules

### Investment Logic
- **Must use paragraph form** (段落形式)
- **Prohibited**: bullet points for investment logic
- **Prohibited**: "不是...而是..." sentence pattern
- **Prohibited**: em dash (—)

### Executive Summary
- Logic summary only, NO financial data
- Focus on strategic narrative and key conclusions

### Tables
- Header row: primary color background (#1B2A4A) with white text
- Data rows: alternating white and light blue (#D6E4F0)
- Border color: #2E5090

### Ownership/Equity Structure Diagrams
- Ellipse = Shareholder
- Rectangle = Company entity
- Arrow = Shareholding relationship (with %)
- Minimalist style: blue outlines + blue text, NO colored fills

## Watermark Specification
- **Applied to**: Type A-G reports, LinkedIn article PDFs (MAI proprietary research)
- **Not applied to**: Agreements, contracts, client-facing documents to be shared with counterparties
- **Parameters**:
  - Text: "MAI | [YYYY-MM-DD]"
  - Opacity: 8%
  - Color: #CCCCCC (light gray)

## File Output & Storage

### Report Files
- **Format**: docx (generated via docx-js, NOT python-docx) + PDF (generated via WeasyPrint HTML→PDF)
- **Storage**: `/MAI/reports/{client_folder}/`
- **Naming**: `{客户简称}_{报告简名}_MAI.pdf`
- **Process drafts**: keep in a local project drafts folder

### PDF Generation
- Use WeasyPrint (HTML→PDF pipeline)
- Do NOT use reportlab (Chinese/English mixed layout font issues)
- HTML template → inject content → WeasyPrint → PDF with watermark

## File Safety Rules
- **Before editing**: `cp filename filename.backup.$(date +%Y%m%d-%H%M%S)`
- **No rm command**: `mkdir -p _archive && mv oldfile _archive/`
- **Source files read-only**: user-provided source folders must not be edited
- **Large changes (>20 lines)**: Describe plan, wait for approval
