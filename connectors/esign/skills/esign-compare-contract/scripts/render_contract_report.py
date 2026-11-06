#!/usr/bin/env python3
"""Render source-backed local HTML; standard library only, no remote resources."""
import argparse
from collections import Counter
from datetime import date
from difflib import SequenceMatcher
import html
import importlib.util
import json
from pathlib import Path
import re
import sys

CSS = '''
:root{color-scheme:light;--ink:#172a38;--muted:#526675;--line:#dce5e9;--accent:#166761}
*{box-sizing:border-box}body{margin:0;background:#f2f5f6;color:var(--ink);font:16px/1.7 system-ui,-apple-system,"PingFang SC","Microsoft YaHei",sans-serif}
main{max-width:1200px;margin:32px auto;padding:36px;background:white;border:1px solid var(--line);border-radius:16px}
h1{font-size:30px;margin:0 0 18px}h2{font-size:23px;margin:32px 0 16px}h3{font-size:19px;margin:0 0 10px}h4{font-size:15px;margin:0 0 8px;color:var(--muted)}
p{margin:8px 0;white-space:pre-wrap;overflow-wrap:anywhere}a{color:var(--accent);overflow-wrap:anywhere}a:focus-visible{outline:3px solid #ddac42;outline-offset:3px}
.meta{color:var(--muted);font-size:14px}.meta div{overflow-wrap:anywhere}.nav{display:block;margin:18px 0;padding:12px 0;border-block:1px solid var(--line)}
.nav ol{list-style:none;padding:0;margin:8px 0 16px}.nav li{margin:0;border-bottom:1px solid #edf1f3}.nav a{display:block;padding:9px 4px;text-decoration:none}.nav a:hover{background:#f2f7f6;text-decoration:underline}.nav h3{font-size:16px;margin:16px 0 4px}
.change-summary{font-weight:600}.impact{margin-top:14px}.table-wrap{max-width:100%}table{border-collapse:collapse;width:100%;table-layout:fixed;margin:14px 0}th,td{text-align:left;vertical-align:top;padding:10px;border:1px solid var(--line);overflow-wrap:anywhere;white-space:pre-wrap}th{background:#eef4f5}details{margin-top:16px}summary{cursor:pointer;color:var(--accent);font-weight:600;padding:6px 0}details[open]>summary{margin-bottom:12px}.highlights{margin:10px 0;padding-left:22px}
.card{border:1px solid var(--line);border-radius:12px;padding:20px;margin:16px 0;scroll-margin-top:16px;break-inside:avoid}
.badge{display:inline-block;border-radius:5px;background:#edf3f4;color:var(--muted);padding:1px 8px;font-size:13px;margin-left:8px}.high{background:#fcecea;color:#9a332c}.mid{background:#fff4d9;color:#835c04}.low{background:#e8f3ed;color:#286643}
.columns{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:16px}.columns.single{grid-template-columns:minmax(0,1fr)}
.quote{white-space:pre-wrap;overflow-wrap:anywhere;margin:0;padding:14px;background:#f6f8f9;border-left:3px solid #b7cbd2;line-height:1.9;color:#223743}
del{background:#ffe5e2;color:#882d28;text-decoration:line-through}ins{background:#dff2e8;color:#19583b;text-decoration:underline;text-underline-offset:3px}
.location{font-size:14px;color:var(--muted);margin:0 0 10px}.warning{border-left:4px solid #cb9637;padding:10px 16px;background:#fff8e9;margin:16px 0}.conclusion{padding:20px;background:#eef6f4;border-radius:12px;margin-bottom:20px}
section{scroll-margin-top:16px}.stack>div{margin:14px 0}ul{padding-left:22px}li{margin:8px 0;overflow-wrap:anywhere}footer{border-top:1px solid var(--line);margin-top:32px;padding-top:12px;font-size:13px;color:var(--muted)}
@media(max-width:760px){main{margin:0;padding:20px 16px;border:0;border-radius:0}h1{font-size:25px}.columns{grid-template-columns:minmax(0,1fr)}.card{padding:16px}}
@media print{body{background:white}main{border:0;margin:0;padding:0}.nav{display:none}a{color:inherit}.card{break-inside:auto}}
'''
CLASSES={'material':'实质变更','non_material':'非实质变更','uncertain':'待确认变化'}
OPS={'add':'新增','delete':'删除','modify':'修改','replace':'替换',None:'变化待确认'}

def esc(value): return html.escape(value, quote=True)
def text(value, label, allow_empty=False):
    if not isinstance(value,str) or (not allow_empty and not value.strip()):
        raise ValueError(label+'必须为'+('字符串' if allow_empty else '非空字符串'))

def fields(value, keys, label):
    if not isinstance(value,dict) or set(value)!=set(keys): raise ValueError(label+'字段不符合协议')

def string_list(value,label):
    if not isinstance(value,list): raise ValueError(label+'必须为数组')
    for item in value: text(item,label)

def no_duplicates(pairs):
    result={}
    for key,value in pairs:
        if key in result: raise ValueError('JSON字段重复：'+key)
        result[key]=value
    return result

def paragraphs(items): return ''.join('<p>'+esc(item)+'</p>' for item in items)
def warning(items): return '<div class="warning">'+paragraphs(items)+'</div>' if items else ''
def normalize(value): return value.replace('\r\n','\n').replace('\r','\n')

def marked(before,after,uncertain=False):
    if uncertain: return esc(before),esc(after)
    left=[];right=[]
    # Keep dates, amounts and percentages whole; quotes remain byte-for-byte text.
    pattern=r"\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d[\d,]*(?:\.\d+)?%?|[A-Za-z_]+|\s+|[^\s]"
    first,last=re.findall(pattern,before),re.findall(pattern,after)
    for tag,a,b,c,d in SequenceMatcher(None,first,last,autojunk=False).get_opcodes():
        x,y=esc(''.join(first[a:b])),esc(''.join(last[c:d]))
        left.append('<del>'+x+'</del>' if tag in ('delete','replace') and x else x)
        right.append('<ins>'+y+'</ins>' if tag in ('insert','replace') and y else y)
    return ''.join(left),''.join(right)

def validate_presentation(view, result):
    fields(view,('differences',),'展示数据')
    if not isinstance(view['differences'],list): raise ValueError('展示条目必须为数组')
    original={row['id']:row for row in result['differences']}; seen=set()
    for row in view['differences']:
        fields(row,('id','title','change_summary','fact_status','table_changes'),'展示条目')
        for key in ('id','title','change_summary','fact_status'): text(row[key],key)
        if row['id'] not in original or row['id'] in seen: raise ValueError('展示ID必须与差异明细一一对应')
        seen.add(row['id']); evidence=original[row['id']]
        if len(row['title'])>36 or len(row['change_summary'])>100: raise ValueError('短标题最多36字，变化说明最多100字')
        if row['fact_status'] not in ('confirmed','unconfirmed'): raise ValueError('差异事实状态不合法')
        if row['fact_status']=='unconfirmed' and evidence['classification']!='uncertain': raise ValueError('事实未核实的条目必须为待确认分类')
        if row['fact_status']=='confirmed' and evidence['operation'] is None: raise ValueError('事实已确认必须明确操作类型')
        if not isinstance(row['table_changes'],list): raise ValueError('表格变化必须为数组')
        cells=set()
        for cell in row['table_changes']:
            fields(cell,('label','before','after'),'表格字段')
            text(cell['label'],'字段名称')
            if len(cell['label'])>60: raise ValueError('表格字段名称过长')
            if cell['label'] in cells: raise ValueError('表格字段重复')
            cells.add(cell['label'])
            if not cell['before'] and not cell['after']: raise ValueError('表格字段不能两侧均空')
            for key in ('before','after'):
                text(cell[key],key,True)
                if cell[key] and normalize(cell[key]) not in normalize(evidence[key]):
                    raise ValueError('表格值未在该条对应原文中找到')
    if seen!=set(original): raise ValueError('展示条目与差异明细数量或ID不一致')
    return {row['id']:row for row in view['differences']}


def compare_body(result, presentation=None):
    rows=result['differences'];cov=result['coverage']; presentation=presentation or {}
    body='<div class="meta"><div>基准文件：'+esc(result['files']['base'])+'</div><div>比对文件：'+esc(result['files']['compare'])+'</div></div>'
    if cov['status']=='partial': body+=warning(['部分内容尚不能确认，两份文件是否一致尚无法判断。'])
    body+=warning(list(dict.fromkeys(cov['limitations'])))
    if not rows:
        return body+('<p>未发现正文差异。</p>' if cov['status']=='complete' else '')
    def display(row):
        return presentation.get(row['id'],{'title':(row['base_location'] or row['compare_location'])[:36],
            'change_summary':'','fact_status':'unconfirmed' if row['classification']=='uncertain' else 'confirmed','table_changes':[]})
    body+='<nav class="nav" aria-label="差异导航"><strong>差异目录</strong><ol>'
    for i,row in enumerate(rows,1):
        view=display(row)
        body+=f'<li><a href="#diff-{i}">'+esc(row['id']+' · '+view['title'])+'</a></li>'
    body+='</ol><a href="#summary">分类总结</a></nav><section id="differences"><h2>差异明细</h2>'
    for i,row in enumerate(rows,1):
        view=display(row);unknown=view['fact_status']=='unconfirmed'
        before,after=marked(row['before'],row['after'],unknown)
        label='差异待核实' if unknown else ('影响待确认' if row['classification']=='uncertain' else CLASSES[row['classification']])
        operation='变化待确认' if unknown else OPS[row['operation']]
        body+=f'<article class="card" id="diff-{i}"><h3>'+esc(row['id']+' · '+view['title'])+f'<span class="badge">{operation}</span><span class="badge">{label}</span></h3>'
        if view['change_summary']: body+='<p class="change-summary">'+esc(view['change_summary'])+'</p>'
        same=row['base_location'] and row['base_location']==row['compare_location']
        if same: body+='<p class="location">'+esc(row['base_location'])+'</p>'
        if view['table_changes']:
            body+='<div class="table-wrap"><table><thead><tr><th scope="col">字段</th><th scope="col">基准值</th><th scope="col">比对值</th></tr></thead><tbody>'
            for cell in view['table_changes']:
                left,right=esc(cell['before']),esc(cell['after'])
                if not unknown and cell['before']!=cell['after']:
                    left='<del>'+left+'</del>' if left else ''
                    right='<ins>'+right+'</ins>' if right else ''
                empty='未取得值' if unknown else '空白／无对应值'
                body+='<tr><th scope="row">'+esc(cell['label'])+'</th><td>'+(left or empty)+'</td><td>'+(right or empty)+'</td></tr>'
            body+='</tbody></table></div><details><summary>查看对应原文</summary>'
            # Raw table quotes retain extraction evidence without presenting separator noise as business changes.
            before,after=esc(row['before']),esc(row['after'])
        body+='<div class="columns'+(' single' if not (before and after) else '')+'">'
        for label,location,quote in [('基准原文',row['base_location'],before),('比对原文',row['compare_location'],after)]:
            if quote:
                body+='<div><h4>'+label+'</h4>'
                if not same: body+='<p class="location">'+esc(location)+'</p>'
                body+='<blockquote class="quote">'+quote+'</blockquote></div>'
        body+='</div>'
        if view['table_changes']: body+='</details>'
        if row['analysis'] and row['analysis']!=view['change_summary']:
            body+='<div class="impact"><h4>变化说明与影响</h4><p>'+esc(row['analysis'])+'</p></div>'
        if row['questions']: body+='<div class="warning"><strong>待确认事项</strong>'+paragraphs(row['questions'])+'</div>'
        body+='</article>'
    body+='</section><section id="summary"><h2>分类总结</h2>'
    for key,label in CLASSES.items():
        group=[(i,row) for i,row in enumerate(rows,1) if row['classification']==key]
        if group:
            body+='<h3>'+label+f'（{len(group)}项）</h3><ul>'
            for i,row in group:
                view=display(row)
                body+=f'<li><a href="#diff-{i}">'+esc(row['id']+' · '+view['title'])+'</a>'
                if view['change_summary']: body+='：'+esc(view['change_summary'])
                body+='</li>'
            body+='</ul>'
    return body+'</section>'


def validate_review(data,source):
    fields({k:v for k,v in data.items() if k!='highlights'},('file_name','perspective','conclusion','risks','wording','questions','limitations'),'审查结果')
    highlights=data.get('highlights',[]);string_list(highlights,'重点')
    if len(data['conclusion'])>180: raise ValueError('审查结论最多180字，详情放入问题项')
    if len(highlights)>3 or any(len(item)>70 for item in highlights): raise ValueError('重点最多3条，每条最多70字')
    for key in ('file_name','conclusion'): text(data[key],key)
    text(data['perspective'],'perspective',True);string_list(data['limitations'],'limitations')
    source=normalize(source)
    if not source.strip(): raise ValueError('正文为空')
    for key in ('risks','wording','questions'):
        if not isinstance(data[key],list): raise ValueError(key+'必须为数组')
    ids=set(); fingerprints=set()
    for row in data['risks']:
        fields(row,('id','level','title','location','quote','missing_basis','impact','suggestion','replacement'),'风险项')
        for key in row: text(row[key],key,key in ('quote','missing_basis','replacement'))
        if len(row['title'])>36: raise ValueError('问题短标题最多36字')
        if row['level'] not in ('高','中','低'): raise ValueError('风险等级不合法')
        if row['id'] in ids: raise ValueError('风险ID重复')
        ids.add(row['id'])
        signature=(row['location'],row['title'],row['quote'])
        if signature in fingerprints: raise ValueError('风险项重复')
        fingerprints.add(signature)
        if row['quote']:
            if normalize(row['quote']) not in source: raise ValueError('风险引用未在正文找到')
            if row['missing_basis']: raise ValueError('有引文时不填写缺失依据')
        elif not row['missing_basis'].strip(): raise ValueError('缺失条款必须有查找依据')
    for row in data['wording']:
        fields(row,('location','quote','suggestion'),'文字问题')
        for key in row: text(row[key],key)
        if normalize(row['quote']) not in source: raise ValueError('文字问题引用未在正文找到')
    for row in data['questions']:
        if not isinstance(row,dict) or not {'question','impact'} <= set(row) or set(row)-{'question','impact','risk_id'}:
            raise ValueError('待确认事项字段不符合协议')
        for key in row: text(row[key],key)
        if 'risk_id' in row and row['risk_id'] not in ids:
            raise ValueError('待确认事项关联风险不存在')
    return data

def review_body(data):
    counts=Counter(row['level'] for row in data['risks'])
    body='<div class="meta"><div>合同：'+esc(data['file_name'])+'</div>'
    if data['perspective']: body+='<div>审查立场：'+esc(data['perspective'])+'</div>'
    body+='</div><section class="conclusion"><h2 style="margin-top:0">审查结论</h2><p>'+esc(data['conclusion'])+'</p>'
    if data.get('highlights'): body+='<ul class="highlights">'+''.join('<li>'+esc(item)+'</li>' for item in data['highlights'])+'</ul>'
    for key,css in [('高','high'),('中','mid'),('低','low')]:
        if counts[key]: body+=f'<span class="badge {css}">{key}风险 {counts[key]}</span>'
    body+='</section>'
    rows=sorted(data['risks'],key=lambda x:('高','中','低').index(x['level']))
    questions=[row for row in data['questions'] if not row.get('risk_id')]
    # Retain older payload limitations without putting generic notices ahead of findings.
    questions += [{'question':item,'impact':''} for item in dict.fromkeys(data['limitations'])]
    entry_count=len(rows)+len(data['wording'])+len(questions)
    if entry_count>=5:
        body+='<nav class="nav" aria-label="目录"><strong>目录</strong>'
        for level in ('高','中','低'):
            group=[(i,row) for i,row in enumerate(rows,1) if row['level']==level]
            if group:
                body+='<h3>'+level+'风险</h3><ol>'
                for i,row in group: body+=f'<li><a href="#risk-{i}">'+esc(row['id']+' · '+row['title'])+'</a></li>'
                body+='</ol>'
        if data['wording']: body+='<a href="#wording">文字问题</a>'
        if questions: body+='<a href="#questions">待确认事项</a>'
        body+='</nav>'
    if rows:
        body+='<section><h2>问题与修改建议</h2>'
        for i,row in enumerate(rows,1):
            body+=f'<article class="card" id="risk-{i}"><h3>{esc(row["id"])} · {esc(row["title"])}<span class="badge">{row["level"]}风险</span></h3><p class="location">'+esc(row['location'])+'</p><div class="stack">'
            body+='<div><h4>依据</h4>'
            body+=('<blockquote class="quote">'+esc(row['quote'])+'</blockquote>' if row['quote'] else '<p>'+esc(row['missing_basis'])+'</p>')+'</div>'
            body+='<div><h4>可能影响</h4><p>'+esc(row['impact'])+'</p></div><div><h4>修改建议</h4><p>'+esc(row['suggestion'])+'</p></div>'
            if row['replacement']: body+='<div><h4>建议条款</h4><blockquote class="quote">'+esc(row['replacement'])+'</blockquote></div>'
            for item in data['questions']:
                if item.get('risk_id')==row['id']:
                    body+='<div class="warning"><p>'+esc(item['question'])+'</p><p>'+esc(item['impact'])+'</p></div>'
            body+='</div></article>'
        body+='</section>'
    if data['wording']:
        body+='<section id="wording"><h2>文字问题</h2>'
        for i,row in enumerate(data['wording'],1): body+=f'<article class="card" id="wording-{i}"><h3>'+esc(row['location'])+'</h3><blockquote class="quote">'+esc(row['quote'])+'</blockquote><p>'+esc(row['suggestion'])+'</p></article>'
        body+='</section>'
    if questions:
        body+='<section id="questions"><h2>待确认事项</h2>'
        for i,row in enumerate(questions,1):
            body+=f'<article class="card" id="question-{i}"><h3>待确认 {i}</h3><p>'+esc(row['question'])+'</p>'
            if row['impact']: body+='<p>'+esc(row['impact'])+'</p>'
            body+='</article>'
        body+='</section>'
    return body


def filename(kind,name,day):
    stem=Path(name.replace('\\','/')).name
    stem=re.sub(r'\.(pdf|docx?|txt|md|html?)$','',stem,flags=re.I)
    stem=re.sub(r'[<>:"/\\|?*\x00-\x1f]','-',stem).strip(' .') or '合同'
    # Leave room for Chinese prefix, date and suffix under a 255-byte component limit.
    while len(stem.encode('utf-8'))>165: stem=stem[:-1]
    return ('合同比对报告' if kind=='compare' else '合同审查报告')+'-'+stem+'-'+day+'.html'

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kind',required=True,choices=('compare','review'))
    parser.add_argument('--input-file',required=True);parser.add_argument('--source-text',required=True)
    parser.add_argument('--compare-text');parser.add_argument('--validator')
    parser.add_argument('--presentation-file',help='Optional source-backed compare display fields')
    parser.add_argument('--output-dir',required=True);parser.add_argument('--date',default=date.today().isoformat())
    args=parser.parse_args()
    try:
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}',args.date): raise ValueError('日期必须为YYYY-MM-DD')
        date.fromisoformat(args.date)
        data=json.loads(Path(args.input_file).read_text(encoding='utf-8-sig'),object_pairs_hook=no_duplicates)
        source=Path(args.source_text).read_text(encoding='utf-8-sig')
        if args.kind=='compare':
            if not args.compare_text: raise ValueError('比对需要第二份正文')
            validator=Path(args.validator) if args.validator else Path(__file__).with_name('validate_compare_result.py')
            spec=importlib.util.spec_from_file_location('contract_compare_validator',validator)
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
            data=module.validate(data,source,Path(args.compare_text).read_text(encoding='utf-8-sig'))
            view=None
            if args.presentation_file:
                view=validate_presentation(json.loads(Path(args.presentation_file).read_text(encoding='utf-8-sig'),object_pairs_hook=no_duplicates),data)
            title='合同比对报告'; name=data['files']['base']; body=compare_body(data,view)
        else:
            if args.presentation_file: raise ValueError('展示文件仅用于比对')
            data=validate_review(data,source);title='合同审查报告';name=data['file_name'];body=review_body(data)
        document='<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'; base-uri \'none\'; form-action \'none\'"><title>'+title+'</title><style>'+CSS+'</style></head><body><main><h1>'+title+'</h1>'+body+'<footer>日期：'+args.date+'</footer></main></body></html>'
        folder=Path(args.output_dir).resolve(); folder.mkdir(parents=True,exist_ok=True)
        # Same name/day retains the prescribed filename, using a fresh subfolder on collision.
        dest=folder/filename(args.kind,name,args.date); counter=1
        while True:
            try:
                with dest.open('x',encoding='utf-8') as handle: handle.write(document)
                break
            except FileExistsError:
                counter+=1; sub=folder/f'第{counter}次';sub.mkdir(exist_ok=True);dest=sub/dest.name
        print(json.dumps({'file':str(dest),'file_name':dest.name},ensure_ascii=False))
        return 0
    except Exception as exc:
        print('报告未生成：'+str(exc),file=sys.stderr);return 1

if __name__=='__main__': raise SystemExit(main())
