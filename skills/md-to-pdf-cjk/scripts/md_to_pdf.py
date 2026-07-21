#!/usr/bin/env python3
"""Convert Markdown to PDF with Chinese font support.

Usage: python3 md_to_pdf.py <input.md> <output.pdf>

Uses reportlab for PDF generation. Supports:
- Chinese characters (auto-detects system CJK fonts)
- Markdown headers, lists, bold, tables
- Emoji (rendered as text)
"""
import sys
import re
import os

def find_cjk_font():
    """Find available CJK font on the system."""
    candidates = [
        '/usr/share/fonts/google-noto-cjk/NotoSansCJK-Regular.ttc',
        '/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc',
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
        '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc',
    ]
    # Also search broadly
    for root in ['/usr/share/fonts', '/usr/local/share/fonts']:
        if os.path.isdir(root):
            for dirpath, _, filenames in os.walk(root):
                for fn in filenames:
                    if 'CJK' in fn and fn.endswith(('.ttc', '.ttf')):
                        candidates.append(os.path.join(dirpath, fn))
    
    for path in candidates:
        if os.path.exists(path):
            return path
    return None

def md_to_pdf(md_path, pdf_path):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    
    # Register CJK font
    font_path = find_cjk_font()
    if font_path:
        try:
            pdfmetrics.registerFont(TTFont('CJK', font_path))
            base_font = 'CJK'
        except:
            pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
            base_font = 'STSong-Light'
    else:
        try:
            pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
            base_font = 'STSong-Light'
        except:
            base_font = 'Helvetica'
    
    # Read markdown
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Setup styles
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='CJKNormal', fontName=base_font, fontSize=10, leading=14))
    styles.add(ParagraphStyle(name='CJKTitle', fontName=base_font, fontSize=18, leading=22, spaceAfter=12))
    styles.add(ParagraphStyle(name='CJKH1', fontName=base_font, fontSize=16, leading=20, spaceAfter=10, spaceBefore=16))
    styles.add(ParagraphStyle(name='CJKH2', fontName=base_font, fontSize=14, leading=18, spaceAfter=8, spaceBefore=12))
    styles.add(ParagraphStyle(name='CJKH3', fontName=base_font, fontSize=12, leading=16, spaceAfter=6, spaceBefore=10))
    
    # Build PDF
    doc = SimpleDocTemplate(pdf_path, pagesize=A4, 
                           leftMargin=20*mm, rightMargin=20*mm,
                           topMargin=20*mm, bottomMargin=20*mm)
    story = []
    
    def clean_md(text):
        """Convert basic markdown to reportlab XML."""
        text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
        text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)
        text = re.sub(r'`(.+?)`', r'<font color="darkred">\1</font>', text)
        return text
    
    in_table = False
    table_rows = []
    
    for line in content.split('\n'):
        stripped = line.strip()
        
        # Table handling
        if '|' in stripped and stripped.startswith('|'):
            cells = [c.strip() for c in stripped.split('|')[1:-1]]
            if all(set(c) <= set('- :') for c in cells):
                continue  # separator row
            if not in_table:
                in_table = True
                table_rows = []
            table_rows.append(cells)
            continue
        elif in_table:
            # End of table
            if table_rows:
                t = Table(table_rows, repeatRows=1)
                t.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (-1, -1), base_font),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e0e0e0')),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ]))
                story.append(t)
                story.append(Spacer(1, 6))
            in_table = False
            table_rows = []
        
        if not stripped:
            story.append(Spacer(1, 6))
        elif stripped.startswith('# '):
            story.append(Paragraph(clean_md(stripped[2:]), styles['CJKTitle']))
        elif stripped.startswith('## '):
            story.append(Paragraph(clean_md(stripped[3:]), styles['CJKH1']))
        elif stripped.startswith('### '):
            story.append(Paragraph(clean_md(stripped[4:]), styles['CJKH2']))
        elif stripped.startswith('#### '):
            story.append(Paragraph(clean_md(stripped[5:]), styles['CJKH3']))
        elif stripped.startswith('- ') or stripped.startswith('* '):
            story.append(Paragraph('• ' + clean_md(stripped[2:]), styles['CJKNormal']))
        elif re.match(r'^\d+\.\s', stripped):
            story.append(Paragraph(clean_md(stripped), styles['CJKNormal']))
        elif stripped.startswith('---'):
            story.append(Spacer(1, 12))
        else:
            story.append(Paragraph(clean_md(stripped), styles['CJKNormal']))
    
    doc.build(story)
    print(f"{os.path.getsize(pdf_path)} bytes written to {pdf_path}")

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <input.md> <output.pdf>")
        sys.exit(1)
    md_to_pdf(sys.argv[1], sys.argv[2])
