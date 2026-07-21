#!/usr/bin/env python3
"""报告可读性自检：颜色对比度 + 文字溢出风险。

用法：
  python3 check_report_html.py report.html
  python3 check_report_html.py report.html --min 4.5   # 覆盖对比度阈值（默认 4.5，大字/粗体自动降到 3）

检查项：
1. 颜色对比度：每个有文字色（class 或 style）的元素，沿 DOM 找实际背景色，算 WCAG 对比度，
   低于阈值报警。等级类(.critical/.high/...)、badge、note、header 等全覆盖。
2. 溢出风险：长连续无空格串(>=40)在 td/p/code/span/li 且容器未启用换行兜底、table 列数>6、
   img/iframe 无 max-width、pre 无 overflow 处理。

仅用标准库（re/html.parser/os/sys），mac/linux/windows 通用。退出码 0=通过，1=有告警。
"""
import re,sys,os
from html.parser import HTMLParser

# ---------- 颜色工具 ----------
def _hex_to_rgb(h):
    h=h.strip().lstrip('#')
    if len(h)==3: h=''.join(c*2 for c in h)
    if len(h)!=6: return None
    try: return (int(h[0:2],16),int(h[2:4],16),int(h[4:6],16))
    except ValueError: return None

def _rel(c):
    return c/12.92 if c<=0.03928*255 else ((c/255+0.055)/1.055)**2.4

def _lum(rgb):
    r,g,b=[_rel(x*255) for x in rgb] if max(rgb)<=1 else [_rel(x) for x in rgb]
    # 上行兼容：rgb 统一按 0-255
    r,g,b=rgb
    R=_rel(r);G=_rel(g);B=_rel(b)
    return 0.2126*R+0.7152*G+0.0722*B

def contrast(fg,bg):
    a=_hex_to_rgb(fg); b=_hex_to_rgb(bg)
    if not a or not b: return None
    l1,l2=_lum(a),_lum(b)
    hi,lo=max(l1,l2),min(l1,l2)
    return (hi+0.05)/(lo+0.05)

# ---------- 解析 CSS class→color/background 映射 ----------
def parse_css(css):
    """返回 {selector: {color:.., background:..}}，仅保留单选择器的简单规则。"""
    out={}
    for block in re.finditer(r'([^{}]+)\{([^{}]*)\}',css):
        sel=block.group(1).strip()
        body=block.group(2)
        m_color=re.search(r'(?<![a-z-])color\s*:\s*([^;]+)',body)
        m_bg=re.search(r'background(?:-color)?\s*:\s*([^;]+)',body)
        m_ow=re.search(r'overflow-wrap\s*:\s*([^;]+)',body)
        m_wb=re.search(r'word-break\s*:\s*([^;]+)',body)
        if not (m_color or m_bg or m_ow or m_wb): continue
        for s in sel.split(','):
            s=s.strip()
            d=out.setdefault(s,{})
            if m_color:
                c=m_color.group(1).strip().split()[0]
                if c.startswith('#'): d['color']=c
            if m_bg:
                raw=m_bg.group(1).strip()
                if raw.startswith('#'):
                    d['background']=raw.split()[0]
                elif 'gradient' in raw or 'rgb' in raw:
                    mm=re.search(r'#([0-9a-fA-F]{3,6})',raw)
                    if mm: d['background']='#'+mm.group(1)
                    else:
                        mm=re.search(r'rgba?\(([^)]+)\)',raw)
                        if mm:
                            parts=[p.strip() for p in mm.group(1).split(',')]
                            if len(parts)>=3:
                                tohex=lambda x:'%02x'%int(float(x))
                                d['background']='#'+tohex(parts[0])+tohex(parts[1])+tohex(parts[2])
            if m_ow: d['overflow-wrap']=m_ow.group(1).strip()
            if m_wb: d['word-break']=m_wb.group(1).strip()
    return out

def load_css_map(html_text=None):
    """合并 base_style.css + HTML 内 <style> 块，返回 {selector: {color,background}}。"""
    here=os.path.dirname(os.path.abspath(__file__))
    css_path=os.path.join(here,'base_style.css')
    css=open(css_path,encoding='utf-8').read()
    if html_text:
        for m in re.finditer(r'<style[^>]*>(.*?)</style>',html_text,re.DOTALL|re.IGNORECASE):
            css+='\n'+m.group(1)
    return parse_css(css)

# ---------- HTML 解析：建 DOM 栈，收集文字节点 + 当前 color/bg ----------
VOID={'meta','br','hr','img','input','link','area','base','col','embed','source','track','wbr'}

class Node:
    __slots__=('tag','classes','style_color','style_bg','style_wrap','children_text')
    def __init__(self,tag):
        self.tag=tag; self.classes=[]; self.style_color=None; self.style_bg=None; self.style_wrap=''; self.children_text=[]

class ReportChecker(HTMLParser):
    def __init__(self,css_map,min_contrast=4.5):
        super().__init__(convert_charrefs=True)
        self.css_map=css_map
        self.min_contrast=min_contrast
        self.stack=[]
        self.issues=[]
        self._cur_text_buf=''
        self._cur_text_owner=None  # 待 flush 的文字所属 node
        self._in_skip=0  # >0 表示在 <style>/<script> 内，忽略 data
        self._tables=[]  # 嵌套 table 栈：每张表 {th:列数, wrapped:是否被.table-wrap包裹}

    def _resolve(self,node,prop):
        """沿栈找 node 的 prop（color/background）：自身 style → 自身单类(.cls) →
        后代选择器(.anc .cls，要求栈中祖先含 .anc) → 祖先重复上述 → 默认值。"""
        chain=list(reversed(self.stack+[node]))
        for n in chain:
            if prop=='color' and n.style_color: return n.style_color
            if prop=='background' and n.style_bg: return n.style_bg
            for cls in n.classes:
                v=self.css_map.get('.'+cls,{}).get(prop)
                if v: return v
            # 后代选择器：选择器形如 ".header .meta"，最后一段==当前节点某类，前面段须在祖先类里出现
            for sel,m in self.css_map.items():
                if ' ' not in sel: continue
                segs=sel.split()
                if segs[-1].lstrip('.') not in n.classes: continue
                anc_classes=set()
                for a in chain:
                    anc_classes|=set(a.classes)
                if all(s.lstrip('.') in anc_classes for s in segs[:-1]):
                    if m.get(prop): return m[prop]
        return '#2c3e50' if prop=='color' else '#f5f7fa'

    def _has_wrap(self,node):
        """沿栈查 node 及祖先是否有 overflow-wrap:anywhere/break-word 或 word-break:break-all。
        有则长串可折行，不算溢出风险。来源：inline style 或 class→CSS 映射。"""
        for n in reversed(self.stack+[node]):
            st=getattr(n,'style_wrap','')
            if st and ('anywhere' in st or 'break-word' in st or 'break-all' in st):
                return True
            for cls in n.classes:
                m=self.css_map.get('.'+cls,{})
                ow=m.get('overflow-wrap',''); wb=m.get('word-break','')
                if ow in ('anywhere','break-word') or wb in ('break-all','break-word'):
                    return True
        return False

    def _flush_text(self):
        if self._cur_text_buf.strip() and self.stack:
            node=self.stack[-1]
            # 大字/粗体判定：h1-h3/th/.card .value 视为大字，阈值降 3
            big = node.tag in ('h1','h2','h3','th') or 'value' in node.classes or 'badge' in node.classes
            fg=self._resolve(node,'color')
            bg=self._resolve(node,'background')
            r=contrast(fg,bg)
            if r is not None:
                thr = 3.0 if big else self.min_contrast
                if r < thr:
                    snippet=self._cur_text_buf.strip()[:30]
                    self.issues.append(('contrast',f'对比度 {r:.2f} < {thr}（{node.tag}.{".".join(node.classes) or "-"} fg={fg} bg={bg}）："{snippet}"'))
            # 超长无空格串检测：>=40 字符且无换行兜底才告警
            if not self._has_wrap(node):
                for sub in re.findall(r'\S{40,}',self._cur_text_buf):
                    self.issues.append(('overflow',f'超长无空格串({len(sub)}字符)在 <{node.tag}.{".".join(node.classes) or "-"}> 内且容器无 overflow-wrap/word-break："{sub[:30]}..."'))
        self._cur_text_buf=''

    def handle_starttag(self,tag,attrs):
        self._flush_text()
        if tag in ('style','script'):
            self._in_skip+=1
            return
        d=dict(attrs)
        # 溢出检测在 VOID 判断之前——img/iframe 等自闭合标签也要查
        self._check_overflow(tag,d)
        if tag in VOID: return
        node=Node(tag)
        if 'class' in d: node.classes=d['class'].split()
        if 'style' in d:
            mc=re.search(r'(?<![a-z-])color\s*:\s*(#[0-9a-fA-F]{3,6})',d['style'])
            if mc: node.style_color=mc.group(1)
            mb=re.search(r'background(?:-color)?\s*:\s*(#[0-9a-fA-F]{3,6})',d['style'])
            if mb: node.style_bg=mb.group(1)
            mw=re.search(r'(?:overflow-wrap|word-break)\s*:\s*([^;]+)',d['style'])
            if mw: node.style_wrap=mw.group(1).strip()
        self.stack.append(node)

    def handle_endtag(self,tag):
        self._flush_text()
        if tag in ('style','script'):
            if self._in_skip: self._in_skip-=1
            return
        if tag=='table':
            self._end_table()
        if tag in VOID: return
        for i in range(len(self.stack)-1,-1,-1):
            if self.stack[i].tag==tag:
                del self.stack[i:]
                break

    def handle_data(self,data):
        if self._in_skip: return
        self._cur_text_buf+=data

    def _check_overflow(self,tag,attrs):
        cls=attrs.get('class','').split()
        # 1. table 列数：>6 列在窄屏易溢出，但若被 .table-wrap 包裹（H.table 自带）则可横向滚动，降为提示不告警
        if tag=='table':
            wrapped=any('table-wrap' in a.classes for a in self.stack)
            self._tables.append({'th':0,'wrapped':wrapped})
        if tag=='th' and self._tables:
            self._tables[-1]['th']+=1
        # 2. img/iframe 无 max-width
        if tag in ('img','iframe','svg','video') and 'max-width' not in attrs.get('style','') and not any('table-wrap' in a.classes or 'container' in a.classes for a in self.stack):
            self.issues.append(('overflow',f'<{tag}> 未限 max-width，宽内容可能撑破容器（src={attrs.get("src","?")[:30]})'))
        # 3. pre 无 overflow 处理
        if tag=='pre' and 'overflow' not in attrs.get('style',''):
            self.issues.append(('overflow',f'<pre> 未设 overflow，长代码行可能横向溢出'))

    def _end_table(self):
        """</table> 时判定：列数>6 且未被 .table-wrap 包裹才告警（有 wrap 则可横向滚动，不算硬故障）。"""
        if not self._tables: return
        t=self._tables.pop()
        if t['th']>6 and not t['wrapped']:
            self.issues.append(('overflow',f'<table> 表头 {t["th"]} 列且未被 .table-wrap 包裹，窄屏下会撑破容器；用 H.table() 或外包 <div class="table-wrap">'))

    def finalize(self):
        self._flush_text()
        # 兜底：未闭合的表也判定
        while self._tables:
            self._end_table()

def scan_long_strings(html):
    """检查超长无空格串是否出现在缺乏换行兜底的容器——本体系 CSS 已全局覆盖 td/th/p/note/code 等，
    此项主要捕获 agent 通过 html() 注入的裸标签。先剥离 <style>/<script> 块，避免把 CSS 当文字。"""
    issues=[]
    text=re.sub(r'<style[^>]*>.*?</style>','',html,flags=re.DOTALL|re.IGNORECASE)
    text=re.sub(r'<script[^>]*>.*?</script>','',text,flags=re.DOTALL|re.IGNORECASE)
    for m in re.finditer(r'>([^<>]{40,})<',text):
        s=m.group(1)
        for sub in re.findall(r'\S{40,}',s):
            start=m.start()
            pre=text[:start].rsplit('>',1)[-1] if '>' in text[:start] else ''
            tag=re.match(r'<(\w+)',pre)
            tname=tag.group(1) if tag else '?'
            issues.append(('overflow',f'超长无空格串({len(sub)}字符)在 <{tname}> 内，若该容器无 overflow-wrap 可能横向溢出："{sub[:30]}..."'))
    return issues

def main():
    if len(sys.argv)<2:
        print(__doc__); sys.exit(2)
    path=sys.argv[1]
    min_c=4.5
    if '--min' in sys.argv:
        i=sys.argv.index('--min'); min_c=float(sys.argv[i+1])
    if not os.path.isfile(path):
        print(f'错误：文件不存在：{path}',file=sys.stderr); sys.exit(2)
    try:
        html=open(path,encoding='utf-8').read()
    except OSError as e:
        print(f'错误：读取失败：{e}',file=sys.stderr); sys.exit(2)
    css_map=load_css_map(html)
    chk=ReportChecker(css_map,min_contrast=min_c)
    chk.feed(html)
    chk.finalize()
    issues=chk.issues
    contrast_iss=[x for k,x in issues if k=='contrast']
    overflow_iss=[x for k,x in issues if k=='overflow']
    print(f'检查：{path}')
    print(f'  对比度告警 {len(contrast_iss)} 条（阈值 {min_c}，大字/粗体降为 3）')
    for x in contrast_iss: print('    ✗ '+x)
    print(f'  溢出告警 {len(overflow_iss)} 条')
    for x in overflow_iss: print('    ✗ '+x)
    if not issues:
        print('  ✓ 全部通过'); sys.exit(0)
    sys.exit(1)

if __name__=='__main__':
    main()
