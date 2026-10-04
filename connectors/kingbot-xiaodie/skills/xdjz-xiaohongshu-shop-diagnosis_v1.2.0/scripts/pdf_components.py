"""Small ReportLab building blocks; supply verified content, images and a CJK TTF.

Run: python pdf_components.py --demo OUTPUT.pdf --font Chinese.ttf
Coordinates use points measured from the top-left of an A4 portrait page.
This is a layout helper, not a shop-data collector or an automatic diagnosis.
"""
from pathlib import Path
from xml.sax.saxutils import escape
import argparse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.lib.utils import ImageReader


class ReportCanvas:
    width, height = A4
    ink = '#193A32'
    muted = '#64736D'
    paper = '#F8FAF7'

    def __init__(self, output, font, bold_font=None, store='', observed=''):
        for path in (font, bold_font or font):
            if not Path(path).is_file():
                raise FileNotFoundError(f'Font not found: {path}')
        pdfmetrics.registerFont(TTFont('DiagnosisBody', str(font)))
        pdfmetrics.registerFont(TTFont('DiagnosisBold', str(bold_font or font)))
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        self.c = canvas.Canvas(str(output), pagesize=A4)
        self.c.setTitle(f'{store}｜经营诊断报告' if store else '诊断报告版式组件')
        self.store, self.observed, self.page_number = store, observed, 0

    def text(self, value, x, top, width, height, size=11, bold=False, color=None):
        """Plain text only; fail on overflow so the caller must edit the layout."""
        style = ParagraphStyle('body', fontName='DiagnosisBold' if bold else 'DiagnosisBody',
                               fontSize=size, leading=size * 1.55, wordWrap='CJK',
                               textColor=HexColor(color or self.ink))
        paragraph = Paragraph(escape(str(value)).replace('\n', '<br/>'), style)
        _, used = paragraph.wrap(width, height)
        if used > height + 0.01:
            raise ValueError(f'Text exceeds box ({used:.1f} > {height:.1f} pt): {str(value)[:35]}')
        paragraph.drawOn(self.c, x, self.height - top - used)
        return used

    def rect(self, x, top, width, height, fill='#EDF2EC', radius=12):
        self.c.setFillColor(HexColor(fill))
        self.c.roundRect(x, self.height-top-height, width, height, radius, fill=1, stroke=0)

    def page(self, title, section, subtitle=''):
        if self.page_number:
            self.c.showPage()
        self.page_number += 1
        self.c.setFillColor(HexColor(self.paper))
        self.c.rect(0, 0, self.width, self.height, fill=1, stroke=0)
        self.text(section, 40, 29, 480, 20, size=9, color=self.muted)
        self.text(title, 40, 64, 515, 90, size=24, bold=True)
        if subtitle:
            self.text(subtitle, 40, 158, 515, 50, size=11, color=self.muted)
        self.c.setStrokeColor(HexColor('#D9E3DB'))
        self.c.line(40, 54, self.width-40, 54)
        self.text(f'{self.store}  {self.observed}', 40, self.height-42, 445, 20, size=8, color=self.muted)
        self.text(str(self.page_number), self.width-60, self.height-42, 20, 20, size=8)

    def card(self, title, body, x, top, width, height, fill='#EDF2EC'):
        self.rect(x, top, width, height, fill)
        self.text(title, x+16, top+15, width-32, 32, size=14, bold=True)
        self.text(body, x+16, top+58, width-32, height-74, size=11)

    def image(self, path, x, top, width, height):
        """Fit without distorting or cropping; use a previously verified local asset."""
        img = ImageReader(str(path))
        iw, ih = img.getSize()
        scale = min(width/iw, height/ih)
        dw, dh = iw*scale, ih*scale
        self.c.drawImage(img, x+(width-dw)/2, self.height-top-(height+dh)/2,
                         width=dw, height=dh, mask='auto')

    def arrow(self, x1, top1, x2, top2, color='#7A9485'):
        from math import atan2, cos, sin, pi
        c = self.c
        y1, y2 = self.height-top1, self.height-top2
        c.setStrokeColor(HexColor(color))
        c.setLineWidth(1.5)
        c.line(x1, y1, x2, y2)
        angle = atan2(y2-y1, x2-x1)
        for delta in (-pi/6, pi/6):
            c.line(x2, y2, x2-7*cos(angle+delta), y2-7*sin(angle+delta))

    def save(self):
        if not self.page_number:
            raise ValueError('Add at least one page before saving.')
        self.c.save()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--demo', required=True, help='Output PDF path for component QA only')
    parser.add_argument('--font', required=True, help='Local Chinese-supporting TrueType font')
    parser.add_argument('--bold-font', help='Optional local Chinese bold TrueType font')
    args = parser.parse_args()
    report = ReportCanvas(args.demo, args.font, args.bold_font, store='版式示例 · 非店铺诊断')
    report.page('沿购买过程定位优化重点', '顾客旅程 · 组件演示',
                '此页只验证中文字体、流程与留白，不包含任何实际店铺结论。')
    report.card('购买前', '看懂商品\n确认规格与适用场景', 40, 230, 156, 185)
    report.card('等待与收货', '了解进度\n按指引验货与使用', 220, 230, 156, 185, '#EAF0F5')
    report.card('售后与复购', '明确解决路径\n顺利处理问题', 400, 230, 155, 185, '#F4EEE5')
    report.arrow(198, 320, 217, 320)
    report.arrow(379, 320, 397, 320)
    report.card('每页只讲一个观点', '实际报告应为每个重点配真实证据和成品示例。\n不要用这张演示页替代店铺分析。',
                40, 460, 515, 180)
    report.save()


if __name__ == '__main__':
    main()
