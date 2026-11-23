# -*- coding: utf-8 -*-
"""飞鹤商旅:国内推荐往返(journeyType=1)查询结果 → 往返组合分析页 一键生成器。

用法:
  python air_domestic_roundtrip_render_page.py <src> --from-city 北京 --to-city 西宁 \
      --go-date 2026-09-20 --ret-date 2026-10-12 \
      [--out 输出.html] [--full-note]

说明:
  - 源:本轮 `domestic_shopping`(journeyType=1) 的返回。`<src>` 为 `-` 时从 stdin 读，
    否则从该文件读(查询结果落盘文件直接传路径即可)。
  - 与单程页不同:往返结果中每个 flightList 行 = 一个「去程舱位 × 返程舱位」的固定组合,
    不存在单程那种「卡片 + 展开舱位表」。卡片内纵向排「去程 / 返程」两段,每段单行紧凑
    (badge+起降时刻机场 ── 时长 ── 到达,信息段:航班号·航司·直飞/经停·机型·餐食·准点率·
    舱位码·余位·行李),两段均不显示单程价;右侧中部一列集中展示往返含税总价 + 去下单。
    每段信息行在行李重量后内联「行李政策」「退改政策」两个链接:行李政策弹层展示该段舱位
    托运/手提行李额(baggage.checkBaggage/carryBaggage + luggage 备注)；退改政策：文案齐全用 CSS
    弹层，退或改任一为空且有 cabId 时做退改政策补查（页内直调 domestic_rule，与国际「查舱位」同形态）。
  - 行数可能上千(推荐往返把去程与回程按舱位两两组合)。模板 JS 全部数据在 RT 中,
    列表按帧分块插入,卡片 content-visibility:auto 跳过视口外内部排版(不分页、
    不侦听 resize)。静态区仅当行数 ≤ 400 时全量预渲染;超过时只静态渲染前 200 行
    并在 SUB 注明「JS 开启后加载全部 N 组」(无 JS 预览通道仍能看到样例)。
  - 输出:自包含 HTML,含 蓝色去下单按钮(免登跳转 #/bookingPricing,flyType=2、
    最外层 serialNumber/flightId/cabId;代购舱同样生成链接，仅用徽标提示) / 红色协议价标签(不显 enterpriseId) /
    每程独立退改政策弹层 / 去程·返程时段筛选 / 航司筛选 / 排序,可直接浏览器打开。
"""
import json, io, re, sys, os, datetime, argparse
from urllib.parse import urlparse

from mcp_envelope import decode, find_envelope, peel_candidates

for _stream in (sys.stdout, sys.stderr):
    try:
        # Windows 控制台默认 GBK，打印 ¥ / 城市名会崩。
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(SKILL_DIR, 'assets', 'air-domestic-roundtrip-page.html')
PAGE_BUSI_JS = os.path.join(SKILL_DIR, 'assets', 'air-domestic-page-busi.js')

CITY_HINT = {'PEK': '首都', 'PKX': '大兴', 'XNN': '西宁'}

WEEK = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']

# 静态全量阈值:超过则只渲染前 STATIC_CAP 行(JS 全量仍在 RT)
STATIC_FULL_MAX = 400
STATIC_CAP = 200

# 页面全局：免登配置（与单程页同机制：host 来自 config.json，code 取自当次 shopping）
_CFG = {"host": "", "infoCode": "", "forwardCode": "", "forwardBase": "",
        "busiRule": "", "adult": 1, "links": False}


def _load_mcp_base():
    """config.json 的 MCP 根地址（portal_config）；缺配置返回空串。"""
    try:
        from portal_config import mcp_base, forward_base, domestic_rule_url
        return mcp_base(), forward_base(), domestic_rule_url()
    except (OSError, RuntimeError, ImportError, ValueError):
        return '', '', ''


def _order_link_rt(r):
    """推荐往返组合行「去下单」forward 链接（flyType=2）。

    最外层 serialNumber + flightId(去程) + cabId(去/回相同取第一程)；不要 flightList。
    代购与普通舱同一条免登 forward 链路（仅用徽标区分）。
    """
    if not _CFG["links"]:
        return ''
    from sso_forward import build_forward_url, build_domestic_order_route
    route = build_domestic_order_route(
        r['sn'], r['go']['no'], r['go']['cab']['cabId'],
        adult=str(_CFG["adult"] or 1), fly_type='2')
    return build_forward_url(route, _CFG["host"], _CFG["forwardCode"])


def _tgq_btn_rt(sn, cab_id, flight_no='', cab=''):
    """shopping 退/改缺文案时的退改政策补查按钮（mcpCall domestic_rule）。"""
    if not sn or not cab_id:
        return ''
    return ('<button type="button" class="lnk cab-tgq" data-sn="%s" data-cabid="%s" '
            'data-flight="%s" data-cab="%s" title="退改文案不完整，点击现场查询">退改政策</button>'
            % (_esc_a(sn), _esc_a(cab_id), _esc_a(flight_no or ''), _esc_a(cab or '')))


def esc_json(o):
    return json.dumps(o, ensure_ascii=False, separators=(',', ':'))


def _esc(s):
    return str(s if s is not None else '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def _esc_a(s):
    return _esc(s).replace('"', '&quot;')


def _qty_n(n):
    if n == 'A':
        return 9
    if isinstance(n, str) and n.isdigit():
        return int(n)
    return 9


def _t_m(t):
    hh, mm = t.split(':')
    return int(hh) * 60 + int(mm)


def _dur(f):
    d = _t_m(f['dep'])
    a = _t_m(f['arr'])
    return a + 1440 - d if a < d else a - d


def _fmt_ot(ot):
    ot = str(ot or '').strip()
    if not ot or ot.lower() in ('null', 'none', 'nan'):
        return ''
    if ot.endswith('.0'):
        ot = ot[:-2]
    return ot


def _apt_term(apt, term):
    apt = (apt or '').strip()
    term = (term or '').strip()
    if not apt:
        return term
    return apt + ('(' + term + ')' if term else '')


def _fmt_dur(m):
    h, mm = divmod(m, 60)
    return ('%d小时%d分钟' % (h, mm)) if h else ('%d分钟' % mm)


def _share_txt(s):
    return ('<span class="tag-share" title="实际承运 %s">共享 %s</span>' % (_esc(s), _esc(s))) if s else ''


def _ot_txt(ot):
    return ('<span class="fl-ot">准点率%s%%</span>' % _esc(ot)) if ot else ''


def _stop_txt(f):
    return ('<span class="tg tg-stop">经停%s</span>' % _esc(f['stop'])) if f.get('stop') else '<span class="tg tg-a">直飞</span>'


def _meta_bits_html(f):
    """信息段: 航班号+航司 · 共享 · 直飞/经停 · 机型 · 餐食 · 准点率 · 舱位(协议/代购/余位/行李)。"""
    cab = f['cab']
    bits = ['<b class="fno">%s</b>' % _esc(f['no'])]
    if f.get('air'):
        bits.append('<span class="air">%s</span>' % _esc(f['air']))
    if f.get('share'):
        bits.append(_share_txt(f['share']))
    bits.append(_stop_txt(f))
    if f.get('ac'):
        bits.append('<span>%s</span>' % _esc(f['ac']))
    bits.append('<span>%s</span>' % _esc(('餐食 ' + f['meal']) if f.get('meal') else '无餐食'))
    if f.get('ot'):
        bits.append('<span class="fl-ot">准点率%s%%</span>' % _esc(f['ot']))
    cname = ((cab.get('cab') or '') + ' ' + (cab.get('cn') or '')).strip()
    if cname:
        bits.append('<span class="cab-chip%s">%s</span>' % (' ent' if cab.get('ent') else '', _esc(cname)))
    if cab.get('ent'):
        bits.append('<span class="tag-ent">协议价</span>')
    if cab.get('buy'):
        bits.append('<span class="tag-buy">代购</span>')
    if cab.get('n'):
        bits.append('<span>余 %d 位</span>' % _qty_n(cab['n']))
    if cab.get('w'):
        bits.append('<span>%skg</span>' % _esc(cab['w']))
    html = '<i class="dot">·</i>'.join(bits)
    # 行李弹层始终 CSS；退改政策：齐全用 CSS，缺一侧且有 cabId 页内直调 domestic_rule
    bag = ('<label class="lnk lk-first" for="bchk%d">行李政策</label>'
           % int(f.get('bpid', -1)))
    rule = ''
    cab_id = (cab.get('cabId') or '') if isinstance(cab, dict) else ''
    if f.get('needTgq') and cab_id and f.get('sn'):
        rule = _tgq_btn_rt(f.get('sn') or '', cab_id, f.get('no') or '', cab.get('cab') or '')
    if not rule and f.get('rpid') is not None:
        rule = '<label class="lnk" for="rchk%d">退改政策</label>' % int(f['rpid'])
    html += bag
    if rule:
        html += '<span class="lk-sep">|</span>' + rule
    return html


def _seg_html(f, idx):
    """去/返一段单行: badge + 起降(时刻·机场) ─ 时长 ─ 到达, 右侧信息段(含行李/退改政策链接)。"""
    dep_apt = _apt_term(f.get('dep_apt', ''), f.get('dep_term', ''))
    arr_apt = _apt_term(f.get('arr_apt', ''), f.get('arr_term', ''))
    p1 = '<em class="s-p1">+1</em>' if _t_m(f['arr']) < _t_m(f['dep']) else ''
    return ('<div class="seg">'
            '<span class="s-badge">%s</span>'
            '<span class="s-date">%s</span>'
            '<span class="s-tm">%s</span><span class="s-ap">%s</span>'
            '<span class="s-fly"><i></i><em>%s</em><i></i></span>'
            '<span class="s-tm">%s%s</span><span class="s-ap">%s</span>'
            '<div class="s-info">%s</div>'
            '</div>' % (
                '去' if idx == 0 else '返',
                _esc(f.get('ds', '')),
                _esc(f['dep']), _esc(dep_apt),
                _fmt_dur(_dur(f)),
                _esc(f['arr']), p1, _esc(arr_apt),
                _meta_bits_html(f)))


def _row_html(r, idx):
    op_ent = '<div class="op-ent">含协议价</div>' if r['anyEnt'] else ''
    # 去下单 = 免登跳转下单页(#/bookingPricing, flyType=2, 最外层 serialNumber/flightId/cabId)
    url = _order_link_rt(r)
    book = ('<a class="btn-book" href="%s" target="_blank" rel="noopener">去下单</a>' % _esc_a(url)
            if url else '<span class="cab-dim">链接未生成</span>')
    return ('<div class="rt-row" data-i="%d">'
            '<div class="legs">%s%s</div>'
            '<div class="ops"><div class="pu">'
            '<div class="op-price"><div class="op-total">¥%d</div>'
            '<div class="op-tl">往返含税合计</div></div>'
            '%s%s'
            '</div></div>'
            '</div>' % (
                idx,
                _seg_html(r['go'], 0), _seg_html(r['ret'], 1),
                r['total'],
                op_ent, book))


def _norm(txt):
    t = (txt or '').replace('\r\n', '\n').replace('\r', '\n')
    if '\n' not in t and '；' in t:
        t = t.replace('；', '\n')
    return t


def build_rules_html(RT, rr_list, cc_list):
    """每个唯一 (退票文本, 改签文本) 组合一块弹层(去/回各自一段);给每个 leg 写 rpid。

    退或改任一为空且有 cabId 的腿：不挂 CSS 弹层，改由页内按钮做退改政策补查（直调 domestic_rule）。
    """
    seen = {}
    for r in RT:
        for leg in (r['go'], r['ret']):
            if leg.get('needTgq') and (leg.get('cab') or {}).get('cabId'):
                leg['rpid'] = None
                continue
            key = (leg.get('rfi', -1), leg.get('cci', -1))
            if key not in seen:
                seen[key] = len(seen)
            leg['rpid'] = seen[key]
    parts = []
    for (rf, ch), pid in sorted(seen.items(), key=lambda kv: kv[1]):
        def _txt(ri, which):
            lst = rr_list if which == 'r' else cc_list
            if ri is None or ri < 0 or ri >= len(lst):
                return ('该舱位未提供%s规则文本' % ('退票' if which == 'r' else '改签')), True
            return lst[ri], False
        r_t, r_e = _txt(rf, 'r')
        c_t, c_e = _txt(ch, 'c')
        parts.append(
            '<div class="rt" id="rt%d"><input type="checkbox" id="rchk%d" class="rchk">'
            '<label class="rmask" for="rchk%d"></label>'
            '<div class="rpop">'
            '<div class="rtitle">退改签规则</div>'
            '<div class="rsub">票价不含机建燃油 · 含税总价=票价+机建+燃油 · 规则以实际下单为准</div>'
            '<div class="rsec"><div class="rh">退票规则</div><div class="rtx%s">%s</div></div>'
            '<div class="rsec"><div class="rh">改签规则</div><div class="rtx%s">%s</div></div>'
            '<label class="rclose" for="rchk%d">关 闭</label>'
            '</div></div>'
            % (pid, pid, pid,
               ' empty' if r_e else '', _esc(r_t),
               ' empty' if c_e else '', _esc(c_t),
               pid))
    parts.append(
        '<div class="rt" id="rtLive"><input type="checkbox" id="rchkLive" class="rchk">'
        '<label class="rmask" for="rchkLive"></label>'
        '<div class="rpop">'
        '<div class="rtitle">退改签规则</div>'
        '<div class="rsub" id="rtLiveSub">票价不含机建燃油 · 规则以实际下单为准</div>'
        '<div class="rsec"><div class="rh">退票规则</div><div class="rtx" id="rtLiveRefund"></div></div>'
        '<div class="rsec"><div class="rh">改签规则</div><div class="rtx" id="rtLiveChange"></div></div>'
        '<label class="rclose" for="rchkLive">关 闭</label>'
        '</div></div>')
    return ''.join(parts)


def _bag_bits(b):
    """一件行李 → '1件 · 20kg · 尺寸40x60x100CM' 形式;空 dict 返回 ''。"""
    if not b or not (b.get('weight') or b.get('number') or b.get('size')):
        return ''
    seg = []
    if b.get('number'):
        seg.append('%s件' % b['number'])
    if b.get('weight'):
        seg.append('%skg' % b['weight'])
    if b.get('size'):
        seg.append('尺寸%s' % b['size'])
    return ' · '.join(seg)


def build_bag_html(RT, bb_list):
    """每个唯一行李额组合一块弹层(去/回各自一段);给每个 leg 写 bpid。"""
    seen = {}
    for r in RT:
        for leg in (r['go'], r['ret']):
            key = (json.dumps(leg.get('bag_chk') or {}, sort_keys=True),
                   json.dumps(leg.get('bag_carry') or {}, sort_keys=True),
                   leg.get('lug') or '')
            if key not in seen:
                seen[key] = len(seen)
                bb_list.append((leg.get('bag_chk') or {}, leg.get('bag_carry') or {}, leg.get('lug') or ''))
            leg['bpid'] = seen[key]
    parts = []
    for pid, (chk, carry, lug) in enumerate(bb_list):
        chk_t, carry_t = _bag_bits(chk), _bag_bits(carry)
        parts.append(
            '<div class="rt" id="bt%d"><input type="checkbox" id="bchk%d" class="rchk">'
            '<label class="rmask" for="bchk%d"></label>'
            '<div class="rpop">'
            '<div class="rtitle">行李政策</div>'
            '<div class="rsub">免费行李额以值机柜台实际测量为准 · 超限部分需按航司标准付费</div>'
            '<div class="rsec"><div class="rh">托运行李</div><div class="rtx%s">%s</div></div>'
            '<div class="rsec"><div class="rh">手提行李</div><div class="rtx%s">%s</div></div>'
            '%s'
            '<label class="rclose" for="bchk%d">关 闭</label>'
            '</div></div>'
            % (pid, pid, pid,
               ' empty' if not chk_t else '', chk_t or '该舱位未提供托运行李额',
               ' empty' if not carry_t else '', carry_t or '该舱位未提供手提行李额',
               ('<div class="rsec"><div class="rh">其他说明</div><div class="rtx">%s</div></div>' % _esc(lug)) if lug else '',
               pid))
    return ''.join(parts)


def build_static(RT, rr_list, cc_list, bb_list, cap):
    """cap=-1 全量;否则只渲染前 cap 行并返回是否截断。"""
    rows = RT[:cap] if cap > 0 else RT
    # 规则/行李索引要先于行渲染计算(行内链接依赖 rpid/bpid)
    build_rules_html(RT, rr_list, cc_list)
    build_bag_html(RT, bb_list)
    cards = ''.join(_row_html(r, i) for i, r in enumerate(rows))
    return cards


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument('src', help='本轮 domestic_shopping(journeyType=1) 返回：文件路径，或 `-` 表示 stdin')
    ap.add_argument('--from-city', required=True, help='出发城市显示名,如 北京')
    ap.add_argument('--to-city', required=True, help='到达城市显示名,如 西宁')
    ap.add_argument('--go-date', default='', help='去程日期 YYYY-MM-DD(缺省取数据首段日期)')
    ap.add_argument('--ret-date', default='', help='返程日期 YYYY-MM-DD(缺省取数据次段日期)')
    ap.add_argument('--out', default='', help='输出 HTML 路径(缺省 feihe-rt-<from>-<to>.html)')
    ap.add_argument('--full-note', action='store_true', help='标题注明(因公·协议价)后缀')
    ap.add_argument('--adult', type=int, default=1, help='下单页 adultCount(=查询 passengerNum,默认 1)')
    ap.add_argument('--no-order-links', action='store_true',
                    help='不生成去下单跳转配置(纯静态分析页)')
    return ap.parse_args()


def load_data(path):
    raw = sys.stdin.read().strip() if path == '-' else io.open(path, encoding='utf-8').read().strip()
    data = decode(raw)
    if isinstance(data, str):
        m = re.search(r'[\[{].*', data, re.S)
        if not m:
            raise SystemExit('源文件不是 JSON，也截取不到 JSON 片段')
        data = decode(m.group(0))
    # requestSeqNo 在 content 信封层（不在 structuredContent），先取出来供页脚展示。
    env = find_envelope(data)
    seq_no = str((env or {}).get('requestSeqNo') or '').strip()
    for candidate in peel_candidates(data):
        if isinstance(candidate, dict) and isinstance(candidate.get('flightList'), list):
            return candidate, seq_no
        if candidate == '内容请读 structuredContent' or (
            isinstance(candidate, str) and (
                '请把structuredContent' in candidate
                or '不在content里面' in candidate
            )
        ):
            continue
    raise SystemExit('源数据中无 flightList（解封后仍未找到 domestic_shopping 载荷）')


def _airline_name(airways, fid):
    m = re.match(r'^([A-Z0-9]{2})', fid or '')
    code = m.group(1) if m else (fid or '')
    for a in airways:
        if a.get('companyNo') == code:
            return a.get('companyName') or a.get('fullCompanyName') or code
    return code


def _leg_obj(s, idx, port_name, types, air_name, fly_date_txt):
    al = s.get('airLine') or ''
    dep3, arr3 = al[:3], al[3:6]
    dep_apt = port_name.get(dep3) or CITY_HINT.get(dep3, dep3) or dep3
    arr_apt = port_name.get(arr3) or CITY_HINT.get(arr3, arr3) or arr3
    cs = [c for c in s.get('cabins', []) if (c.get('price') or 0) > 0]
    cs.sort(key=lambda c: c.get('price') or 0)
    if not cs:
        return None
    c = cs[0]
    # 行李: baggage.checkBaggage / carryBaggage {weight,number,size} + luggage 备注;
    # weight 兜底取 baggage.checkBaggage.weight
    bg = c.get('baggage') or {}
    cbk = bg.get('checkBaggage') or {}
    cbl = bg.get('carryBaggage') or {}
    lug = str(bg.get('luggage') or '').strip()
    w = str(c.get('weight') or '').strip()
    if not w:
        w = str(cbk.get('weight') or '').strip()
    np_ = c.get('normalPrice') or c.get('price') or 0
    np_ = np_ if np_ > 0 else (c.get('price') or 0)
    eid = str(c.get('enterpriseId') or '').strip()
    src = str(c.get('source') or '').strip()
    # 往返行每舱退改政策文本直接在 refund/change 顶层(单程在 rule.refundText 内,两者都兼容)
    rule = c.get('rule') or {}
    rfi_txt = rule.get('refundText') if isinstance(rule, dict) and rule.get('refundText') else c.get('refund')
    cci_txt = rule.get('changeText') if isinstance(rule, dict) and rule.get('changeText') else c.get('change')
    obj = {
        'no': s.get('flightId') or '',
        'air': air_name,
        'dep': (s.get('flyDate') or '')[11:16],
        'arr': (s.get('arrDate') or '')[11:16],
        'dep_apt': dep_apt, 'arr_apt': arr_apt,
        'dep_term': str(s.get('fromPort') or '').strip(),
        'arr_term': str(s.get('toPort') or '').strip(),
        'stop': int(s.get('stop') or 0),
        'ac': types.get(str(s.get('type')), str(s.get('type') or '—')),
        'meal': (s.get('meal') or '无')[:12],
        'ot': _fmt_ot(s.get('onTime')),
        'share': str(s.get('shareId') or '').strip(),
        'acf': int(s.get('acf') or 0),
        'baf': int(s.get('baf') or 0),
        'fp': int(s.get('fullPrice') or 0),
        'dateTxt': fly_date_txt,
        'ds': fly_date_txt[5:] if fly_date_txt else '',  # 短日期 MM-DD(周X), 蓝圈后展示
        'price': c.get('price') or 0,   # 与行尾合计、JS 选中明细共用
        'rfi_txt': rfi_txt, 'cci_txt': cci_txt,
        'bag_chk': cbk, 'bag_carry': cbl, 'lug': lug,
        'cab': {
            'cab': c.get('cab') or '',
            'cn': c.get('cabName') or '',
            'price': c.get('price') or 0,
            'np': np_,
            'ent': eid,
            'buy': src in ('2', '3', '7'),
            'n': str(c.get('num') or '').strip(),
            'w': w,
            'cabId': str(c.get('cabId') or '').strip(),
        },
    }
    return obj


def build(args):
    data, request_seq_no = load_data(args.src)

    # ---- 免登：host/forwardBase/busiRule 引用 config.json，code 取自当次 shopping ----
    base_url, fwd_base, rule_url = _load_mcp_base()
    _CFG['host'] = urlparse(base_url).netloc if base_url else ''
    _CFG['forwardBase'] = fwd_base
    _CFG['busiRule'] = rule_url
    _CFG['adult'] = args.adult or 1
    _CFG['infoCode'] = str(data.get('infoCode') or '').strip()
    _CFG['forwardCode'] = str(data.get('forwardCode') or '').strip()
    if args.no_order_links:
        _CFG['links'] = False
        _CFG['infoCode'] = ''
        _CFG['forwardCode'] = ''
    else:
        _CFG['links'] = bool(_CFG['host'] and _CFG['infoCode'] and _CFG['forwardCode'])
        if not _CFG['links']:
            print('[错误] 未取到 infoCode/forwardCode/host，拒绝交付死页面（去下单跳转会失效）。\n'
                  '  处理：① 确认 domestic_shopping 成功结果最外层带 infoCode 与 forwardCode 后重跑；\n'
                  '  ② 只要纯静态分析页（无去下单跳转）时，显式加 --no-order-links 重跑。',
                  file=sys.stderr)
            raise SystemExit(3)

    fl_items = data.get('flightList') or []
    airways = data.get('airways') or []
    port_name = {}
    for c in data.get('citys', []):
        if isinstance(c, dict) and c.get('cityCode'):
            port_name[c['cityCode']] = c.get('airPortName') or ''
    types = {}
    for t in data.get('types', []):
        if isinstance(t, dict) and t.get('type') is not None:
            types[str(t['type'])] = t.get('name') or ''
    serial_number = str(data.get('serialNumber') or '').strip()

    # ---- 组装 RT(每行=去×回组合) ----
    rr_map, cc_map = {}, {}
    rr_list, cc_list = [], []
    bb_list = []  # 唯一行李额组合(去/回各自一段,弹层复用)

    def _ridx(txt, mp, lst):
        txt = _norm(txt)
        if not txt:
            return -1
        if txt not in mp:
            mp[txt] = len(lst)
            lst.append(txt)
        return mp[txt]

    RT = []
    go_date = ret_date = ''
    for item in fl_items:
        segs = item.get('flight', [])
        if len(segs) < 2:
            continue
        go_s, ret_s = segs[0], segs[1]
        go_d = (go_s.get('flyDate') or '')[:10]
        ret_d = (ret_s.get('flyDate') or '')[:10]
        if not go_date:
            go_date = go_d
        ret_date = ret_d or ret_date
        if not go_d or not ret_d:
            continue
        def _dtxt(d):
            dt = datetime.date.fromisoformat(d)
            return '%s(%s)' % (d, WEEK[dt.weekday()])
        go = _leg_obj(go_s, 0, port_name, types,
                      _airline_name(airways, go_s.get('flightId')), _dtxt(go_d))
        ret = _leg_obj(ret_s, 1, port_name, types,
                       _airline_name(airways, ret_s.get('flightId')), _dtxt(ret_d))
        if not go or not ret:
            continue
        go['rfi'] = _ridx(go.get('rfi_txt'), rr_map, rr_list)
        go['cci'] = _ridx(go.get('cci_txt'), cc_map, cc_list)
        ret['rfi'] = _ridx(ret.get('rfi_txt'), rr_map, rr_list)
        ret['cci'] = _ridx(ret.get('cci_txt'), cc_map, cc_list)
        go.pop('rfi_txt', None)
        go.pop('cci_txt', None)
        ret.pop('rfi_txt', None)
        ret.pop('cci_txt', None)
        # 退或改任一为空 → 点击做退改政策补查（页内直调 domestic_rule，需 cabId + sn）
        go['needTgq'] = (go['rfi'] < 0 or go['cci'] < 0)
        ret['needTgq'] = (ret['rfi'] < 0 or ret['cci'] < 0)
        go['sn'] = serial_number
        ret['sn'] = serial_number
        RT.append({
            'k': '',  # 占位,下方按最终顺序补
            'sn': serial_number,
            'go': go, 'ret': ret,
            'total': (go['price'] + go['acf'] + go['baf']) + (ret['price'] + ret['acf'] + ret['baf']),
            'anyEnt': bool(go['cab']['ent']) or bool(ret['cab']['ent']),
        })
    for i, r in enumerate(RT):
        r['k'] = str(i)
    if not RT:
        raise SystemExit('无有效去程×返程舱位组合')
    # 默认按总价排序,与模板 fSort=total 一致
    RT.sort(key=lambda r: r['total'])
    for i, r in enumerate(RT):
        r['k'] = str(i)

    # 首段日期兜底标题参数
    if not args.go_date:
        args.go_date = go_date
    if not args.ret_date:
        args.ret_date = ret_date

    # ---- 统计与文案 ----
    def _dtxt_short(d):
        try:
            dt = datetime.date.fromisoformat(d)
            return '%s(%s)' % (d, WEEK[dt.weekday()])
        except Exception:
            return d
    go_n = len({r['go']['no'] for r in RT})
    ret_n = len({r['ret']['no'] for r in RT})
    ent_n = sum(1 for r in RT if r['anyEnt'])
    air_n = len({r['go']['air'] for r in RT} | {r['ret']['air'] for r in RT})
    min_r = min(RT, key=lambda r: r['total'])
    direct = all((r['go'].get('stop') == 0 and r['ret'].get('stop') == 0) for r in RT)

    route_mid = '%s→%s' % (args.from_city, args.to_city)
    h1 = '%s ↔ %s · 推荐往返航班组合' % (args.from_city, args.to_city)
    title = ('%s 往返 %s→%s' % (route_mid, _dtxt_short(args.go_date), _dtxt_short(args.ret_date))) + ('(因公·协议价)' if args.full_note else '')
    trunc_note = ''
    cap = -1
    if len(RT) > STATIC_FULL_MAX:
        cap = STATIC_CAP
        trunc_note = ' · 静态预览前 %d 组，JS 开启后加载全部 %d 组' % (STATIC_CAP, len(RT))
    sub = ('feihe-cli 国内推荐往返 · 因公口径 · %d 组(去程%d班×返程%d班)%s · 最低往返含税 ¥%d(%s+%s)%s'
           % (len(RT), go_n, ret_n, (' · 全部直飞' if direct else ''),
              min_r['total'], min_r['go']['no'], min_r['ret']['no'], trunc_note))

    # ---- 渲染模板 ----
    tpl = io.open(TEMPLATE, encoding='utf-8').read()
    tpl = re.sub(r'^<!--.*?-->\s*', '', tpl, count=1, flags=re.S)
    _busi_mark = '/*@@AIR_DOMESTIC_PAGE_BUSI@@*/'
    assert _busi_mark in tpl, '页内 busi 锚点缺失'
    tpl = tpl.replace(_busi_mark, io.open(PAGE_BUSI_JS, encoding='utf-8').read(), 1)
    reps = {
        '{{TITLE}}': title,
        '{{H1}}': h1,
        '{{SUB}}': sub,
        '{{SEQ_FOOT}}': (
            '<div style="color:#e8eaed;font-size:10px;margin-top:6px;text-align:center">'
            '请求流水号 requestSeqNo：<span style="user-select:all">%s</span></div>'
            % _esc(request_seq_no) if request_seq_no else ''),
    }
    for k, v in reps.items():
        assert k in tpl, '占位符缺失: ' + k
        tpl = tpl.replace(k, v)
    airs = sorted({r['go']['air'] for r in RT} | {r['ret']['air'] for r in RT})
    air_opts = '<option value="">全部航司</option>' + ''.join('<option>%s</option>' % _esc(a) for a in airs)
    assert '{{STATIC_AIR_OPTS}}' in tpl
    tpl = tpl.replace('{{STATIC_AIR_OPTS}}', air_opts, 1)
    assert '{{STATIC_CNT}}' in tpl
    tpl = tpl.replace('{{STATIC_CNT}}', '共 %d / %d 组往返' % (len(RT), len(RT)), 1)
    # 静态 KPI(无 JS 兜底;与模板 JS kpis() 输出同构)
    kpi_html = ('<div class="kpi"><div class="v">%d<em>组</em></div><div class="l">去程%d班 × 返程%d班组合</div></div>'
                '<div class="kpi"><div class="v">¥%d<em>起</em></div><div class="l">最低往返合计 %s→%s</div></div>'
                '<div class="kpi"><div class="v">%d<em>/%d</em></div><div class="l">含协议价组合</div></div>'
                '<div class="kpi"><div class="v">%d<em>家</em></div><div class="l">执飞航司</div></div>'
                % (len(RT), go_n, ret_n, min_r['total'], min_r['go']['no'], min_r['ret']['no'],
                   ent_n, len(RT), len(airs)))
    assert '{{STATIC_KPIS}}' in tpl
    assert tpl.count('{{STATIC_KPIS}}') == 1
    tpl = tpl.replace('{{STATIC_KPIS}}', kpi_html, 1)
    # 静态行与规则/行李弹层(先分配 rpid/bpid,再渲染行)
    rules_html = build_rules_html(RT, rr_list, cc_list)
    bag_html = build_bag_html(RT, bb_list)
    rows_html = ''.join(_row_html(r, i) for i, r in enumerate(RT[:cap] if cap > 0 else RT))
    assert tpl.count('{{STATIC_LIST}}') == 1
    tpl = tpl.replace('{{STATIC_LIST}}', rows_html, 1)
    assert tpl.count('{{STATIC_RULES}}') == 1
    tpl = tpl.replace('{{STATIC_RULES}}', rules_html + bag_html, 1)
    # 数据块(bpid 分配完再清掉原始行李 dict,避免冗余进 JS)
    for r in RT:
        for leg in (r['go'], r['ret']):
            leg.pop('bag_chk', None)
            leg.pop('bag_carry', None)
            leg.pop('lug', None)
    tpl = tpl.replace('var RT=[]; //@@RT@@', 'var RT=' + esc_json(RT) + ';', 1)
    tpl = tpl.replace('var RR=[]; //@@RR@@', 'var RR=' + esc_json(rr_list) + ';', 1)
    tpl = tpl.replace('var CC=[]; //@@CC@@', 'var CC=' + esc_json(cc_list) + ';', 1)
    assert 'var QUERY_SN=""; //@@SN@@' in tpl
    tpl = tpl.replace('var QUERY_SN=""; //@@SN@@', 'var QUERY_SN=' + esc_json(serial_number) + ';', 1)
    # CFG 注入（JS 动态行与 Python 静态行共用同一免登配置）
    page_cfg = {'host': _CFG['host'], 'infoCode': _CFG['infoCode'], 'forwardCode': _CFG['forwardCode'],
               'forwardBase': _CFG.get('forwardBase') or '',
               'busiRule': _CFG.get('busiRule') or '',
               'order': {'adult': _CFG['adult']}}
    assert 'var CFG=null; //@@CFG@@' in tpl, 'CFG 锚点缺失'
    tpl = tpl.replace('var CFG=null; //@@CFG@@', 'var CFG=' + esc_json(page_cfg) + ';', 1)

    out = args.out or 'feihe-rt-%s-%s-%s.html' % (
        (args.from_city), (args.to_city), args.go_date.replace('-', ''))
    # newline='': Windows 下不要把模板里的 \n 写成 \r\n
    io.open(out, 'w', encoding='utf-8', newline='').write(tpl)

    # 自检：只查静态 HTML 结构与占位符。不要对 <script> 做括号计数——
    # 注入的 RT/RR/CC JSON 字符串常含半角括号，且本页有 2 段 script，计数会误报。
    # 单程出页已按同样口径只做静态区检查。
    resid = re.findall(r'\{\{\w+\}\}', tpl)
    static_part = tpl[:tpl.find('<script>')]
    div_ok = len(re.findall(r'<div\b', static_part)) == static_part.count('</div>')
    print('OUT:', out)
    print('往返组合 %d · 去程航班 %d · 返程航班 %d · 含协议价组合 %d · 航司 %d' % (len(RT), go_n, ret_n, ent_n, air_n))
    print('最低往返含税 ¥%d (%s %s + %s %s) · %s' % (
        min_r['total'], min_r['go']['no'], min_r['go']['dep'], min_r['ret']['no'], min_r['ret']['dep'],
        '全部直飞' if direct else '含经停'))
    print('静态区div平衡:%s · 残留占位符:%s' % ('OK' if div_ok else 'FAIL', resid or '无'))
    buy_n = sum(1 for r in RT if r['go']['cab'].get('buy') or r['ret']['cab'].get('buy'))
    print('去下单跳转链接:%s（含代购舱 %d 组,与其他舱位同一免登链路）' % (
        '已生成(免登forward→#/bookingPricing)' if _CFG['links'] else '未生成(缺code/host)', buy_n))
    if not div_ok or resid:
        raise SystemExit('自检失败,输出文件不可用')
    return out, len(RT), go_n, ret_n, ent_n, min_r['total']


if __name__ == '__main__':
    a = parse_args()
    build(a)
