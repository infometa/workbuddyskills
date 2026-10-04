# -*- coding: utf-8 -*-
"""
Generate the legal opinion DOCX for the labor contract resignation dispute.
Based on the consultation reply template (02_咨询回复式法律意见书模板.docx).
"""

import docx
from docx import Document
from docx.shared import Pt, Cm, RGBColor, Emu
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml.ns import qn, nsdecls
from docx.oxml import parse_xml
import os
import copy
import argparse
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_PATH = SKILL_ROOT / 'assets' / 'templates' / '02_咨询回复式法律意见书模板.docx'
DEFAULT_OUTPUT_NAME = '关于员工王某辞职争议之法律意见书.docx'

# ── helpers ──────────────────────────────────────────────

def set_run_font(run, name='楷体', size=Pt(12), bold=False, color=None):
    if size is not None:
        run.font.size = size
    run.font.bold = bold
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn('w:rFonts'))
    if rFonts is None:
        rFonts = parse_xml(f'<w:rFonts {nsdecls("w")}/>')
        rPr.insert(0, rFonts)
    rFonts.set(qn('w:eastAsia'), name)
    rFonts.set(qn('w:ascii'), name)
    rFonts.set(qn('w:hAnsi'), name)
    if name:
        run.font.name = name
    if color:
        run.font.color.rgb = color

def clear_document(doc):
    """Remove all paragraphs from the document body, keeping section properties."""
    body = doc.element.body
    # Keep only sectPr (section properties)
    for child in list(body):
        if child.tag != qn('w:sectPr'):
            body.remove(child)

def add_paragraph(doc, text='', style='Normal', font_name='楷体', font_size=Pt(12),
                 bold=False, alignment=None, first_line_indent=None,
                 line_spacing=1.5, space_before=Pt(0), space_after=Pt(0),
                 color=None):
    p = doc.add_paragraph()
    if style:
        p.style = doc.styles[style]
    if text:
        run = p.add_run(text)
        set_run_font(run, font_name, font_size, bold, color)
    if alignment is not None:
        p.alignment = alignment
    if first_line_indent is not None:
        p.paragraph_format.first_line_indent = first_line_indent
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    p.paragraph_format.line_spacing = line_spacing
    p.paragraph_format.space_before = space_before
    p.paragraph_format.space_after = space_after
    return p

def add_body_text(doc, text, indent=True):
    """Add a normal body paragraph with 楷体 12pt and first line indent."""
    return add_paragraph(doc, text, style='Normal',
                        first_line_indent=Cm(0.85) if indent else None)

def add_heading1(doc, text):
    """Add a Heading 1 paragraph."""
    p = doc.add_paragraph(text, style='Heading 1')
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    return p

def add_heading2(doc, text):
    """Add a Heading 2 paragraph."""
    p = doc.add_paragraph(text, style='Heading 2')
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    return p

def add_centered_text(doc, text, font_name='楷体', font_size=Pt(12), bold=False):
    """Add a centered paragraph (for cover page elements)."""
    return add_paragraph(doc, text, font_name=font_name, font_size=font_size,
                        bold=bold, alignment=WD_ALIGN_PARAGRAPH.CENTER)

def add_declaration_item(doc, text):
    """Add a declaration paragraph with proper formatting."""
    return add_paragraph(doc, text, style='Normal',
                        first_line_indent=Cm(0.85))

def add_conclusion_item(doc, text):
    """Add a conclusion box paragraph."""
    return add_paragraph(doc, text, style='Conclusion Box',
                        first_line_indent=Cm(0.85))

def add_law_analysis(doc, text):
    """Add a law analysis paragraph."""
    return add_paragraph(doc, text, style='Law Analysis',
                        first_line_indent=Cm(0.85))

# ── Main generation ──────────────────────────────────────

def generate(output_path):
    doc = Document(str(TEMPLATE_PATH))

    # Clear all template content
    clear_document(doc)

    # ── Cover page ──
    # Empty lines for spacing
    for _ in range(4):
        add_paragraph(doc, '')

    # Title
    p = add_paragraph(doc, '', style='Normal')
    run = p.add_run('关于员工王某辞职争议之')
    set_run_font(run, '黑体', Pt(22), bold=True, color=RGBColor(0, 0, 0))
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    p = add_paragraph(doc, '', style='Normal')
    run = p.add_run('法律意见书')
    set_run_font(run, '黑体', Pt(22), bold=True, color=RGBColor(0, 0, 0))
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Subtitle
    add_paragraph(doc, '', alignment=WD_ALIGN_PARAGRAPH.CENTER)

    for _ in range(6):
        add_paragraph(doc, '')

    # Entity and date
    add_centered_text(doc, 'AI辅助生成·待复核初稿', font_name='楷体', font_size=Pt(14))
    for _ in range(2):
        add_paragraph(doc, '')
    add_centered_text(doc, '二〇二六年八月十七日', font_name='楷体', font_size=Pt(14))

    # Page break
    from docx.enum.text import WD_BREAK
    p = add_paragraph(doc, '')
    run = p.add_run()
    run.add_break(docx.enum.text.WD_BREAK.PAGE)

    # ── 重要声明 ──
    p = add_paragraph(doc, '重要声明', style='重要声明标题',
                     alignment=WD_ALIGN_PARAGRAPH.CENTER)

    add_body_text(doc,
        '本声明为本法律意见书不可分割的组成部分。请在使用、转发或据此决策前完整阅读。')

    add_body_text(doc,
        'AI辅助生成：本法律意见书由人工智能工具辅助形成。人工智能可能发生事实遗漏、规则误引、'
        '时效判断偏差或表达歧义，不能替代具备相应专业能力人员的独立判断。')

    add_body_text(doc,
        '材料依赖：本法律意见书仅以用户提供的陈述和公开检索结果为基础。'
        '未经独立核验的材料不视为已经确认。')

    add_body_text(doc,
        '复核要求：凡涉及劳动争议、仲裁或诉讼的事项，均应由执业律师或有权专业人员复核后使用。')

    add_body_text(doc,
        '身份与签章：非律师用户不得冒用律师事务所、律师姓名、执业证号或印章。'
        '未完成签发程序的文本不得对外宣称为律师事务所出具的正式法律意见。')

    add_body_text(doc,
        '用途限制：本法律意见书仅供载明的委托事项和接收对象使用。'
        '任何第三方不得仅凭本文件替代自身调查、判断或取得专业意见。')

    # Page break before main content
    p = add_paragraph(doc, '')
    run = p.add_run()
    run.add_break(docx.enum.text.WD_BREAK.PAGE)

    # ── 致客户 ──
    add_body_text(doc, '致：【待补充：客户名称/接收对象】')
    add_body_text(doc,
        '就贵方提出的关于员工王某辞职争议事项，我们根据截至2026年8月17日已取得的信息'
        '和中国大陆现行有效法律规则，回复如下。')

    # ── 一、问题摘要 ──
    add_heading1(doc, '一、问题摘要')
    add_body_text(doc,
        '贵方就以下问题征询法律意见：某公司与员工王某签订劳动合同，约定月工资为8,000元。'
        '王某工作6个月后主动提出离职，并提前30天向公司提交了书面辞职通知。'
        '公司认为王某提前离职给业务造成影响，因此拒绝为其办理离职手续，'
        '并要求王某支付一个月工资作为"违约金"。')
    add_body_text(doc,
        '经归纳，本意见书围绕以下三个争点展开分析：'
        '（1）王某提前30天书面通知辞职的行为是否合法有效；'
        '（2）公司拒绝为王某办理离职手续是否具有法律依据；'
        '（3）公司要求王某支付一个月工资作为"违约金"是否成立。')

    # ── 二、事实基础与待核验事项 ──
    add_heading1(doc, '二、事实基础与待核验事项')
    add_body_text(doc,
        '据委托方陈述，某公司与王某签订了劳动合同，约定月工资为8,000元。'
        '王某入职后工作满6个月，主动提出离职，并提前30天以书面形式向公司提交了辞职通知。'
        '公司以王某提前离职给业务造成影响为由，拒绝为其办理离职手续，'
        '并要求王某支付一个月工资即8,000元作为"违约金"。')
    add_body_text(doc,
        '上述事实系委托方陈述，尚未经独立文件核验。以下事项有待进一步确认：'
        '劳动合同的具体条款（尤其是否约定了服务期、专业技术培训或竞业限制条款）；'
        '王某提交辞职通知的准确日期及送达方式；'
        '公司是否对王某进行过专项技术培训并支付了培训费用；'
        '公司是否因王某离职而遭受可证明的实际经济损失。')

    # ── 三、法律分析 ──
    add_heading1(doc, '三、法律分析')

    # 争点1：王某辞职行为的合法性
    add_heading2(doc, '（一）王某提前30天书面通知辞职的行为合法有效')
    add_law_analysis(doc,
        '根据《中华人民共和国劳动合同法》第三十七条，劳动者提前三十日以书面形式通知用人单位，'
        '可以解除劳动合同。该条规定赋予了劳动者单方解除劳动合同的权利（即辞职权），'
        '劳动者只需履行提前三十日书面通知的程序义务，无需用人单位批准或同意。')
    add_body_text(doc,
        '就本案而言，王某作为劳动者，工作6个月后主动提出离职，并提前30天向公司提交了书面辞职通知，'
        '其行为完全符合上述法律规定的程序要求。辞职权系劳动者的法定权利，'
        '通知到达用人单位即发生法律效力，三十日期满后劳动合同即告解除，'
        '公司是否同意不影响解除的效力。')
    add_body_text(doc,
        '从对方角度来看，公司可能主张王某的离职给业务造成了影响，因此其辞职行为不应被允许。'
        '不过，结合本事项的具体情况，法律对劳动者行使辞职权不附加任何条件，'
        '公司因业务受影响而不认可辞职效力，缺乏法律依据。'
        '即便公司因此遭受影响，亦不构成限制劳动者依法行使辞职权的正当事由。')
    add_body_text(doc,
        '综合前述情况，王某提前30天书面通知辞职的行为合法有效，'
        '劳动合同于三十日通知期满后依法解除，公司无权以未批准为由否认解除的效力。')

    # 争点2：公司拒绝办理离职手续的违法性
    add_heading2(doc, '（二）公司拒绝办理离职手续缺乏法律依据')
    add_law_analysis(doc,
        '根据《中华人民共和国劳动合同法》第五十条第一款，用人单位应当在解除或者终止劳动合同时'
        '出具解除或者终止劳动合同的证明，并在十五日内为劳动者办理档案和社会保险关系转移手续。'
        '该条为用人单位设定了在劳动合同解除后出具离职证明并办理档案和社保转移手续的法定义务，'
        '该义务的履行不以工作交接完成或离职审批通过为前提。')
    add_body_text(doc,
        '在本事项中，王某依法提前30天书面通知辞职，通知期满后劳动合同已经解除。'
        '公司拒绝为其办理离职手续，实质上是以自身意志对抗劳动者依法行使的解除权。'
        '需要正视的是，用人单位不得以工作交接未完成、离职审批未通过或劳动者存在违约争议为由，'
        '拒绝履行出具离职证明和办理档案、社保转移手续的法定义务。'
        '即使劳动者存在违约或赔偿问题，用人单位亦应另行依法主张，'
        '不得以此阻挠离职手续的办理。')
    add_body_text(doc,
        '进一步看，用人单位迟延办理离职手续可能给劳动者造成实际损失。'
        '若因未及时取得离职证明导致王某无法入职新单位或无法享受社会保险待遇，'
        '公司还应依法承担赔偿责任。')
    add_body_text(doc,
        '由此可以判断，公司拒绝为王某办理离职手续的行为违反了劳动合同法的明确规定，'
        '应当依法在劳动合同解除后十五日内为王某出具离职证明并办理档案和社会保险关系转移手续。')

    # 争点3：公司要求支付违约金的违法性
    add_heading2(doc, '（三）公司要求王某支付一个月工资作为"违约金"不能成立')
    add_law_analysis(doc,
        '根据《中华人民共和国劳动合同法》第二十五条，除本法第二十二条和第二十三条规定的情形外，'
        '用人单位不得与劳动者约定由劳动者承担违约金。'
        '第二十二条限于用人单位提供专项培训费用进行专业技术培训并约定服务期的情形，'
        '第二十三条限于竞业限制约定的情形。'
        '除以上两种情形外，用人单位不得与劳动者约定由劳动者承担违约金，'
        '已约定的条款因违反法律强制性规定而无效。')
    add_body_text(doc,
        '落到本事项，公司要求王某支付一个月工资8,000元作为"违约金"，'
        '据委托方陈述，公司并未为王某提供专项培训费用进行专业技术培训，'
        '亦未与王某约定竞业限制。因此，本案不存在劳动合同法第二十二条和第二十三条规定的'
        '可以约定违约金的法定情形。无论公司以何种名义（违约金、赔偿金或损失补偿）'
        '要求王某支付一个月工资，该要求均缺乏法律依据。')
    add_body_text(doc,
        '换一个角度看，公司也可能援引《中华人民共和国劳动合同法》第九十条，'
        '主张王某违法解除劳动合同并据此要求赔偿。'
        '该条规定，劳动者违反本法规定解除劳动合同，给用人单位造成损失的，应当承担赔偿责任。'
        '然而，王某已依法提前30天书面通知辞职，其解除劳动合同的行为完全合法，'
        '不构成"违反本法规定解除劳动合同"，因此第九十条在本事项中无适用余地。')
    add_body_text(doc,
        '还需要考虑的是，即使劳动合同中约定了"劳动者未提前通知或提前离职需支付违约金"之类的条款，'
        '该条款也因违反劳动合同法第二十五条的强制性规定而自始无效，'
        '公司不得据此向王某主张任何金额。用人单位要求劳动者先行支付违约金后才办理离职手续的做法，'
        '亦已被司法实践明确否定。')
    add_body_text(doc,
        '在现有材料范围内，公司要求王某支付一个月工资作为"违约金"没有法律依据，'
        '王某有权拒绝支付，公司不得以此为前提拖延或拒绝办理离职手续。')

    # ── 四、结论意见 ──
    add_heading1(doc, '四、结论意见')
    add_conclusion_item(doc,
        '基于本法律意见书列明的材料、事实、核查结果和保留事项，本出具主体认为：')
    add_conclusion_item(doc,
        '1. 王某提前30天书面通知辞职的行为合法有效，劳动合同于通知期满后依法解除，'
        '公司无权以未批准为由否认解除的效力。')
    add_conclusion_item(doc,
        '2. 公司拒绝为王某办理离职手续的行为违反劳动合同法第五十条的法定义务，'
        '应当依法在劳动合同解除后十五日内出具离职证明并办理档案和社会保险关系转移手续，'
        '迟延办理造成王某损失的，还应承担赔偿责任。')
    add_conclusion_item(doc,
        '3. 公司要求王某支付一个月工资8,000元作为"违约金"没有法律依据。'
        '本案不存在劳动合同法第二十二条（服务期）和第二十三条（竞业限制）规定的'
        '可约定违约金的法定情形，相关约定即使存在亦属无效。'
        '王某已依法提前30天通知辞职，不构成违法解除，亦不适用第九十条的赔偿责任。')
    add_conclusion_item(doc,
        '4. 建议王某依法配合办理工作交接，但工作交接并非公司履行离职手续义务的前置条件。'
        '若公司继续拒绝办理离职手续或以此为由扣发工资，王某可向当地劳动监察部门投诉'
        '或申请劳动仲裁，依法主张出具离职证明、办理社保转移手续及赔偿损失。')

    # ── 五、保留事项 ──
    add_heading1(doc, '五、保留事项')
    add_body_text(doc,
        '本回复未覆盖王某与公司之间劳动合同的具体条款内容、是否实际存在服务期或竞业限制约定、'
        '公司是否因王某离职遭受可证明的实际经济损失等事项。'
        '若上述事实与目前掌握情况不一致，或者相关法律规则发生变化，结论应重新评估。')
    add_body_text(doc,
        '本意见书为AI辅助生成的待复核初稿，不构成正式法律意见。'
        '涉及劳动仲裁或诉讼的，应由执业律师实质复核后使用。'
        '【待补充：律所/律师姓名/执业证号】字段须由出具主体补齐后方可对外使用。')

    # ── 签署页 ──
    p = add_paragraph(doc, '')
    run = p.add_run()
    run.add_break(docx.enum.text.WD_BREAK.PAGE)

    add_body_text(doc, '（本页无正文，为本法律意见书签署页。）')
    for _ in range(3):
        add_paragraph(doc, '')

    add_centered_text(doc, 'AI辅助生成·待复核初稿', font_name='楷体', font_size=Pt(12))
    for _ in range(2):
        add_paragraph(doc, '')

    add_body_text(doc, '负责人/授权签发人：________________    【待补充：负责人或授权签发人】')
    add_body_text(doc, '经办人员：________________________    【待补充：经办人员】')
    add_body_text(doc, '执业证号（如适用）：______________    【待补充：执业证号】')
    add_body_text(doc, '日期：2026年8月17日')
    add_body_text(doc, '印章：【仅由有权主体在完成复核和签发后加盖】')

    # Save
    output_path = Path(output_path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(output_path))
    print(f'已生成: {output_path}')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='生成咨询回复式法律意见书 DOCX 样稿')
    parser.add_argument('--output', default=DEFAULT_OUTPUT_NAME, help='输出 DOCX 路径')
    args = parser.parse_args()
    generate(args.output)
