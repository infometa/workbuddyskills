---
name: pdf
description: Use this skill whenever the user wants to do anything with PDF files. This includes reading or extracting text/tables from PDFs, combining or merging multiple PDFs into one, splitting PDFs apart, rotating pages, adding watermarks, creating new PDFs, filling PDF forms, encrypting/decrypting PDFs, extracting images, and OCR on scanned PDFs to make them searchable. If the user mentions a .pdf file or asks to produce one, use this skill.
license: Proprietary. LICENSE.txt has complete terms
---

# PDF Processing Guide

## Overview

This guide covers essential PDF processing operations using Python libraries and command-line tools. For advanced features, JavaScript libraries, and detailed examples, see REFERENCE.md. If you need to fill out a PDF form, read FORMS.md and follow its instructions.

## Quick Start

```python
from pypdf import PdfReader, PdfWriter

# Read a PDF
reader = PdfReader("document.pdf")
print(f"Pages: {len(reader.pages)}")

# Extract text
text = ""
for page in reader.pages:
    text += page.extract_text()
```

## Python Libraries

### pypdf - Basic Operations

#### Merge PDFs
```python
from pypdf import PdfWriter, PdfReader

writer = PdfWriter()
for pdf_file in ["doc1.pdf", "doc2.pdf", "doc3.pdf"]:
    reader = PdfReader(pdf_file)
    for page in reader.pages:
        writer.add_page(page)

with open("merged.pdf", "wb") as output:
    writer.write(output)
```

#### Split PDF
```python
reader = PdfReader("input.pdf")
for i, page in enumerate(reader.pages):
    writer = PdfWriter()
    writer.add_page(page)
    with open(f"page_{i+1}.pdf", "wb") as output:
        writer.write(output)
```

#### Extract Metadata
```python
reader = PdfReader("document.pdf")
meta = reader.metadata
print(f"Title: {meta.title}")
print(f"Author: {meta.author}")
print(f"Subject: {meta.subject}")
print(f"Creator: {meta.creator}")
```

#### Rotate Pages
```python
reader = PdfReader("input.pdf")
writer = PdfWriter()

page = reader.pages[0]
page.rotate(90)  # Rotate 90 degrees clockwise
writer.add_page(page)

with open("rotated.pdf", "wb") as output:
    writer.write(output)
```

### pdfplumber - Text and Table Extraction

#### Extract Text with Layout
```python
import pdfplumber

with pdfplumber.open("document.pdf") as pdf:
    for page in pdf.pages:
        text = page.extract_text()
        print(text)
```

#### Extract Tables
```python
with pdfplumber.open("document.pdf") as pdf:
    for i, page in enumerate(pdf.pages):
        tables = page.extract_tables()
        for j, table in enumerate(tables):
            print(f"Table {j+1} on page {i+1}:")
            for row in table:
                print(row)
```

#### Advanced Table Extraction
```python
import pandas as pd

with pdfplumber.open("document.pdf") as pdf:
    all_tables = []
    for page in pdf.pages:
        tables = page.extract_tables()
        for table in tables:
            if table:  # Check if table is not empty
                df = pd.DataFrame(table[1:], columns=table[0])
                all_tables.append(df)

# Combine all tables
if all_tables:
    combined_df = pd.concat(all_tables, ignore_index=True)
    combined_df.to_excel("extracted_tables.xlsx", index=False)
```

### reportlab - Create PDFs

> 🚨 **MANDATORY RULE — Read before writing any reportlab code**
>
> **Every reportlab script MUST import and call `setup_chinese_pdf()` first — even for English-only content.**
>
> **Step 0 — import the helper** (this skill ships it as `scripts/setup_chinese_pdf.py`):
> ```python
> import sys, os
> sys.path.insert(0, os.path.join(os.path.dirname(__file__), "scripts"))
> from setup_chinese_pdf import setup_chinese_pdf
> ```
> If your script is NOT in the skill root directory, use the absolute path to `scripts/` instead.
>
> **Then follow these rules:**
> 1. Call `cn_font, styles = setup_chinese_pdf()` as the **very first** reportlab operation.
> 2. Use the returned `styles` for all `Paragraph(...)` calls — do **NOT** call `getSampleStyleSheet()` separately.
> 3. For any custom `ParagraphStyle`, use `parent=styles['X']` so it inherits the CJK font.
> 4. For Canvas API, call `c.setFont(cn_font, size)` **before** every `c.drawString()` / `c.drawCentredString()`.
> 5. **NEVER** use `Helvetica`, `Times-Roman`, or `Courier` for any text that may contain Chinese.
>
> **Skipping any of these steps causes every Chinese character to render as a solid black box.**
> **There is NO error — the script exits 0 and the PDF looks silently broken.**
>
> All examples below already follow this pattern. You can use any of them as a starting template.

#### Basic PDF Creation
```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "scripts"))
from setup_chinese_pdf import setup_chinese_pdf

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# MUST be the very first reportlab operation
cn_font, styles = setup_chinese_pdf()

c = canvas.Canvas("hello.pdf", pagesize=letter)
width, height = letter

# Set font before drawing text (required for both English and Chinese)
c.setFont(cn_font, 12)
c.drawString(100, height - 100, "Hello World!")
c.drawString(100, height - 120, "This is a PDF created with reportlab")

# Add a line
c.line(100, height - 140, 400, height - 140)

# Save
c.save()
```

#### Create PDF with Multiple Pages
```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "scripts"))
from setup_chinese_pdf import setup_chinese_pdf

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak

# MUST be the very first reportlab operation
cn_font, styles = setup_chinese_pdf()

doc = SimpleDocTemplate("report.pdf", pagesize=letter)
story = []

# Add content — styles from setup_chinese_pdf() already have CJK font set
title = Paragraph("Report Title", styles['Title'])
story.append(title)
story.append(Spacer(1, 12))

body = Paragraph("This is the body of the report. " * 20, styles['Normal'])
story.append(body)
story.append(PageBreak())

# Page 2
story.append(Paragraph("Page 2", styles['Heading1']))
story.append(Paragraph("Content for page 2", styles['Normal']))

# Build PDF
doc.build(story)
```

#### Chinese / CJK PDF Content

> ⚠️ **IMPORTANT — NEVER fall back to English**: If the user asked for Chinese content, the PDF **must** contain Chinese. Do **not** replace Chinese content with English and claim it is a "limitation" — that is incorrect behaviour. Follow the instructions below to produce correct Chinese output on every platform.

**ReportLab's built-in fonts (Helvetica, Times-Roman, Courier) are Latin-only — they contain no CJK glyphs.** Passing Chinese text to these fonts causes characters to silently render as blank spaces or boxes. The script exits with code 0, so there is no error to catch; the PDF simply has no Chinese text.

**Why intermittent garbling happens — three traps in reportlab:**

1. **`ParagraphStyle` copies parent attributes at construction time.** `ParagraphStyle('X', parent=styles['Title'])` copies `fontName='Helvetica-Bold'` into the new object's `__dict__` immediately. Patching the parent afterwards has **no effect** on already-created children. Every style that may contain Chinese MUST receive `fontName=cn_font` explicitly, or inherit from an already-patched parent.

2. **`getSampleStyleSheet()` returns a new instance every call.** Patching one instance does not affect the next call. So `styles['Normal'].fontName = cn_font` only works for that one `styles` object.

3. **`TableStyle FONTNAME` is silently ignored for Paragraph cells.** When a table cell contains a `Paragraph` object, the Paragraph's own `fontName` wins — the `TableStyle('FONTNAME', ...)` setting has zero effect on it.

**Fix: use `setup_chinese_pdf()` below. It returns `(cn_font, styles)` where `styles` is a pre-patched stylesheet. Use it for ALL text — then Chinese never breaks.**

##### The complete solution — `setup_chinese_pdf()`

> **Preferred**: import from the pre-built module `scripts/setup_chinese_pdf.py` (see MANDATORY RULE above).  
> **Fallback**: if importing is not possible (e.g. Windows base64 workflow), copy the function below verbatim into your script.  
> Source code: `scripts/setup_chinese_pdf.py`

```python
import os
import platform
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


def setup_chinese_pdf():
    """
    Register a system CJK font and return (cn_font, styles).

    cn_font: the registered font name — pass to canvas.setFont() and any
             ParagraphStyle you create manually via fontName=cn_font.

    styles:  a StyleSheet1 where ALL default ParagraphStyles already use
             the CJK font. Use styles['Title'], styles['Normal'], etc.
             directly — Chinese will render correctly without extra args.

    Also works for child styles: ParagraphStyle('X', parent=styles['Title'])
    will inherit the CJK fontName because the parent was patched BEFORE the
    child was constructed (ParagraphStyle copies parent attrs at init time).
    """
    system = platform.system()

    if system == 'Darwin':  # macOS
        # PingFang.ttc does NOT exist on disk — it is a virtual system font.
        # STHeiti / Songti are real files present on all macOS versions.
        candidates = [
            ('/System/Library/Fonts/STHeiti Light.ttc',       'STHeiti',       0),
            ('/System/Library/Fonts/STHeiti Medium.ttc',      'STHeitiMedium', 0),
            ('/System/Library/Fonts/Supplemental/Songti.ttc', 'Songti',        0),
            ('/Library/Fonts/Arial Unicode MS.ttf',           'ArialUnicode',  0),
        ]
    elif system == 'Windows':
        candidates = []
        dirs = []
        windir = os.environ.get('WINDIR', 'C:\\Windows')
        dirs.append(os.path.join(windir, 'Fonts'))
        local = os.environ.get('LOCALAPPDATA', '')
        if local:
            dirs.append(os.path.join(local, 'Microsoft', 'Windows', 'Fonts'))
        for d in dirs:
            for fname, name, idx in [
                ('msyh.ttc',   'MicrosoftYaHei', 0),   # 微软雅黑 — Win10/11
                ('msyhbd.ttc', 'MicrosoftYaHeiBold', 0),
                ('simhei.ttf', 'SimHei',          0),   # 黑体
                ('simsun.ttc', 'SimSun',          0),   # 宋体
                ('mingliu.ttc','MingLiU',         0),   # 細明體
            ]:
                candidates.append((os.path.join(d, fname), name, idx))
    else:  # Linux
        candidates = [
            ('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', 'NotoSansCJK', 0),
            ('/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc', 'NotoSansCJK', 0),
            ('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',           'WQYZenHei',   0),
            ('/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf','DroidSans',  0),
        ]

    cn_font = None
    for font_path, font_name, idx in candidates:
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(TTFont(font_name, font_path, subfontIndex=idx))
                cn_font = font_name
                break
            except Exception:
                continue
    if cn_font is None:
        raise RuntimeError(
            f"No CJK font found on {system}.\n"
            "  macOS:   check /System/Library/Fonts/\n"
            "  Windows: ensure msyh.ttc or simhei.ttf in %WINDIR%\\Fonts\n"
            "  Linux:   sudo apt install fonts-noto-cjk"
        )

    # Build a stylesheet with ALL styles pre-patched to use the CJK font.
    # This eliminates garbling even if fontName= is accidentally omitted.
    styles = getSampleStyleSheet()
    for style in styles.byName.values():
        if isinstance(style, ParagraphStyle):
            style.fontName = cn_font

    return cn_font, styles
```

##### Using `setup_chinese_pdf()` — Platypus (Paragraph / Table)

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "scripts"))
from setup_chinese_pdf import setup_chinese_pdf

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors

# ── 1. MUST be the first reportlab call ──
cn_font, styles = setup_chinese_pdf()

# styles['Title'], styles['Normal'], styles['Heading1'] etc. already use CJK font.
# Use them directly — no need to pass fontName.

# If you create custom styles, use parent=styles['X'] so they inherit the CJK font:
title_style = ParagraphStyle('CnTitle', parent=styles['Title'], fontSize=20, alignment=TA_CENTER)
body_style  = ParagraphStyle('CnBody',  parent=styles['Normal'], fontSize=11, leading=18)
# title_style.fontName is already the CJK font — inherited from patched parent.

doc = SimpleDocTemplate("report_cn.pdf", pagesize=A4)

# ── 2. Tables: wrap EVERY cell in Paragraph(text, styles['X']) ──
# TableStyle FONTNAME is silently ignored for Paragraph cells.
# ALWAYS use Paragraph(..., styles['Normal']) for any cell that contains Chinese.
table_data = [
    [Paragraph('指标',    styles['Normal']), Paragraph('2024年',   styles['Normal'])],
    [Paragraph('市场规模', styles['Normal']), Paragraph('32.1亿元', styles['Normal'])],
]
t = Table(table_data, colWidths=[200, 150])
t.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E4057')),
    ('TEXTCOLOR',  (0, 0), (-1, 0), colors.white),
    ('GRID',       (0, 0), (-1,-1), 0.5, colors.grey),
    ('FONTNAME',   (0, 0), (-1,-1), cn_font),  # only affects plain-string cells
    ('FONTSIZE',   (0, 0), (-1,-1), 11),
]))

story = [
    Paragraph("国内市场分析报告", title_style),
    Spacer(1, 12),
    Paragraph("正文内容，中文可以正常显示。English and 中文 mixed.", body_style),
    Spacer(1, 20),
    t,
]
doc.build(story)
```

##### Using `setup_chinese_pdf()` — Canvas API

> Canvas `drawString` / `drawCentredString` requires explicit `c.setFont(cn_font, size)` before **every** call
> that contains Chinese. The font is NOT inherited between draw calls.

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "scripts"))
from setup_chinese_pdf import setup_chinese_pdf

from reportlab.pdfgen import canvas

cn_font, styles = setup_chinese_pdf()

c = canvas.Canvas("cn_canvas.pdf")

c.setFont(cn_font, 16)
c.drawString(100, 750, "你好，世界！Hello World！")

c.setFont(cn_font, 12)   # must set again when size changes
c.drawString(100, 720, "中文内容必须在 setFont 之后绘制")

c.save()
```

##### Windows: write Python scripts without any Chinese in the shell command

On Windows, both PowerShell and CMD interpret the command line before passing it
to Python. Their default encoding (GBK / CP936) **corrupts Chinese string literals**
in the shell command before Python ever sees them — even inside `python -c "..."`.

**Do NOT do this** (Chinese in the shell string — always breaks on GBK consoles):
```powershell
# ❌ WRONG — PowerShell corrupts Chinese before python receives it
python -c "open('x.py','w',encoding='utf-8').write('print(\"中文\")')"
```

**Correct approach: encode Chinese content as base64, decode inside Python**

The shell command contains **only ASCII**. Python receives the base64 string
intact regardless of the console encoding, then decodes it back to UTF-8 internally.

```powershell
# Step 1: on any machine that has Python, generate the base64 payload once:
#   python -c "import base64; print(base64.b64encode(open('script.py','rb').read()).decode())"
# Then paste the result as PAYLOAD below.

# Step 2: on Windows, run the following (all ASCII — no Chinese in the shell):
python -c "import base64,os; open('gen_report.py','wb').write(base64.b64decode('<PAYLOAD>'))"
python gen_report.py
```

**Full workflow example** (model should follow this pattern every time):

```powershell
# 1. Build the script content and base64-encode it in one python call.
#    The python -c string here is pure ASCII — base64 payload carries the Chinese.
python -c "
import base64, textwrap

script = textwrap.dedent('''
    # -*- coding: utf-8 -*-
    import os, platform
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

    def setup_chinese_pdf():
        system = platform.system()
        if system == \"Windows\":
            candidates = []
            dirs = []
            windir = os.environ.get(\"WINDIR\", \"C:\\\\Windows\")
            dirs.append(os.path.join(windir, \"Fonts\"))
            local = os.environ.get(\"LOCALAPPDATA\", \"\")
            if local:
                dirs.append(os.path.join(local, \"Microsoft\", \"Windows\", \"Fonts\"))
            for d in dirs:
                for fname, name, idx in [
                    (\"msyh.ttc\",\"MicrosoftYaHei\",0),
                    (\"simhei.ttf\",\"SimHei\",0),
                    (\"simsun.ttc\",\"SimSun\",0),
                ]:
                    candidates.append((os.path.join(d, fname), name, idx))
        elif system == \"Darwin\":
            candidates = [
                (\"/System/Library/Fonts/STHeiti Light.ttc\", \"STHeiti\", 0),
                (\"/System/Library/Fonts/STHeiti Medium.ttc\", \"STHeitiMedium\", 0),
            ]
        else:
            candidates = [
                (\"/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc\", \"NotoSansCJK\", 0),
                (\"/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc\", \"WQYZenHei\", 0),
            ]
        cn_font = None
        for font_path, font_name, idx in candidates:
            if os.path.exists(font_path):
                try:
                    pdfmetrics.registerFont(TTFont(font_name, font_path, subfontIndex=idx))
                    cn_font = font_name
                    break
                except Exception:
                    continue
        if cn_font is None:
            raise RuntimeError(\"No CJK font found\")
        styles = getSampleStyleSheet()
        for style in styles.byName.values():
            if isinstance(style, ParagraphStyle):
                style.fontName = cn_font
        return cn_font, styles

    cn_font, styles = setup_chinese_pdf()
    title_style = ParagraphStyle(\"T\", parent=styles[\"Title\"], fontSize=20, alignment=TA_CENTER)
    body_style  = ParagraphStyle(\"B\", parent=styles[\"Normal\"], fontSize=11, leading=18)
    out = os.path.join(os.path.expanduser(\"~\"), \"Desktop\", \"report_cn.pdf\")
    doc = SimpleDocTemplate(out)
    doc.build([
        Paragraph(\"\u56fd\u5185\u5e02\u573a\u5206\u6790\u62a5\u544a\", title_style),
        Spacer(1, 12),
        Paragraph(\"\u8fd9\u662f\u6b63\u6587\u5185\u5bb9\uff0c\u4e2d\u6587\u53ef\u4ee5\u6b63\u5e38\u663e\u793a\u3002\", body_style),
    ])
    print(\"PDF saved:\", out)
''').encode('utf-8')

payload = base64.b64encode(script).decode()
# Write a pure-ASCII launcher — no Chinese in the shell at all
open('launch.py', 'w').write(
    'import base64,os\\n'
    'open(\"gen_report.py\",\"wb\").write(base64.b64decode(\"' + payload + '\"))\\n'
    'os.system(\"python gen_report.py\")\\n'
)
"
python launch.py
```

> **Why this works**: `base64.b64decode(...)` is pure ASCII in the shell. The Chinese
> characters are encoded as `\uXXXX` Unicode escapes (ASCII-safe) inside the script
> string, and Python's `textwrap.dedent` + UTF-8 `encode/decode` reconstruct the
> original Chinese bytes correctly — the console encoding never touches the content.

> **Rule**: On Windows, **never** put Chinese string literals inside a shell command
> (`python -c "..."`, PowerShell heredoc, or `echo`). Always use base64 or Unicode
> escapes (`\uXXXX`) to carry non-ASCII content through the shell layer.

#### Subscripts and Superscripts

**IMPORTANT**: Never use Unicode subscript/superscript characters (₀₁₂₃₄₅₆₇₈₉, ⁰¹²³⁴⁵⁶⁷⁸⁹) in ReportLab PDFs. The built-in fonts do not include these glyphs, causing them to render as solid black boxes.

Instead, use ReportLab's XML markup tags in Paragraph objects:
```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "scripts"))
from setup_chinese_pdf import setup_chinese_pdf

from reportlab.platypus import Paragraph

# MUST be the very first reportlab operation
cn_font, styles = setup_chinese_pdf()

# Subscripts: use <sub> tag
chemical = Paragraph("H<sub>2</sub>O", styles['Normal'])

# Superscripts: use <super> tag
squared = Paragraph("x<super>2</super> + y<super>2</super>", styles['Normal'])
```

For canvas-drawn text (not Paragraph objects), manually adjust font the size and position rather than using Unicode subscripts/superscripts.

## Command-Line Tools

### pdftotext (poppler-utils)
```bash
# Extract text
pdftotext input.pdf output.txt

# Extract text preserving layout
pdftotext -layout input.pdf output.txt

# Extract specific pages
pdftotext -f 1 -l 5 input.pdf output.txt  # Pages 1-5
```

### qpdf
```bash
# Merge PDFs
qpdf --empty --pages file1.pdf file2.pdf -- merged.pdf

# Split pages
qpdf input.pdf --pages . 1-5 -- pages1-5.pdf
qpdf input.pdf --pages . 6-10 -- pages6-10.pdf

# Rotate pages
qpdf input.pdf output.pdf --rotate=+90:1  # Rotate page 1 by 90 degrees

# Remove password
qpdf --password=mypassword --decrypt encrypted.pdf decrypted.pdf
```

### pdftk (if available)
```bash
# Merge
pdftk file1.pdf file2.pdf cat output merged.pdf

# Split
pdftk input.pdf burst

# Rotate
pdftk input.pdf rotate 1east output rotated.pdf
```

## Common Tasks

### Extract Text from Scanned PDFs
```python
# Requires: pip install pytesseract pdf2image
import pytesseract
from pdf2image import convert_from_path

# Convert PDF to images
images = convert_from_path('scanned.pdf')

# OCR each page
text = ""
for i, image in enumerate(images):
    text += f"Page {i+1}:\n"
    text += pytesseract.image_to_string(image)
    text += "\n\n"

print(text)
```

### Add Watermark
```python
from pypdf import PdfReader, PdfWriter

# Create watermark (or load existing)
watermark = PdfReader("watermark.pdf").pages[0]

# Apply to all pages
reader = PdfReader("document.pdf")
writer = PdfWriter()

for page in reader.pages:
    page.merge_page(watermark)
    writer.add_page(page)

with open("watermarked.pdf", "wb") as output:
    writer.write(output)
```

### Extract Images
```bash
# Using pdfimages (poppler-utils)
pdfimages -j input.pdf output_prefix

# This extracts all images as output_prefix-000.jpg, output_prefix-001.jpg, etc.
```

### Password Protection
```python
from pypdf import PdfReader, PdfWriter

reader = PdfReader("input.pdf")
writer = PdfWriter()

for page in reader.pages:
    writer.add_page(page)

# Add password
writer.encrypt("userpassword", "ownerpassword")

with open("encrypted.pdf", "wb") as output:
    writer.write(output)
```

## Quick Reference

| Task | Best Tool | Command/Code |
|------|-----------|--------------|
| Merge PDFs | pypdf | `writer.add_page(page)` |
| Split PDFs | pypdf | One page per file |
| Extract text | pdfplumber | `page.extract_text()` |
| Extract tables | pdfplumber | `page.extract_tables()` |
| Create PDFs | reportlab | Canvas or Platypus |
| Command line merge | qpdf | `qpdf --empty --pages ...` |
| OCR scanned PDFs | pytesseract | Convert to image first |
| Fill PDF forms | pdf-lib or pypdf (see FORMS.md) | See FORMS.md |

## Next Steps

- For advanced pypdfium2 usage, see REFERENCE.md
- For JavaScript libraries (pdf-lib), see REFERENCE.md
- If you need to fill out a PDF form, follow the instructions in FORMS.md
- For troubleshooting guides, see REFERENCE.md
