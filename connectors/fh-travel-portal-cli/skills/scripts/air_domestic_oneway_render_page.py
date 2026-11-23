# -*- coding: utf-8 -*-
"""飞鹤商旅:国内机票查询结果 → 交互分析页 一键生成器。

用法:
  python air_domestic_oneway_render_page.py - --from-city 长沙 --to-city 成都 \
      --date 2026-09-03 --date-text 2026-09-03(周四) --from-code CSX --to-code CTU1 \
      [--out 输出.html] [--side auto|dep|arr] [--adult 1] [--top-open 5]

说明:
  - 源:`domestic_shopping` 的返回（参数 `-` 表示从 stdin 读）。
  - 机场维度自动推断:查看所有航段 airLine(如 CSXCTU / CSXTFU / PEKXNN / PKXXNN),
    前3位=出发机场三字码、后3位=到达机场三字码;若出发侧有多个机场(聚合码查询
    如 BJS1/CTU1 会返回 PEK+PKX 或 CTU+TFU),则多机场侧在"出发",反之为"到达"。
  - 输出:自包含 HTML,含 蓝色去下单按钮 / 红色协议价标签(不显 enterpriseId)/
    舱位四列对齐 / 余位徽标(A→9位) / 退改政策弹层 / 筛选排序,可直接浏览器打开。
  - v3.4.0:前 --top-open(默认5)个推荐航班默认展开舱位;每个舱位「去下单」=
    免登 forward 跳转飞鹤国内下单页(#/bookingPricing?serialNumber&flightId&cabId&flyType=1&payType=1&agent=1)；
    其余航班点「更多」只展开本次 shopping 已返回的舱位（首屏每班预览前 3 档，可「展开全部」），
    不再页内直调 domestic_shopping_by_flight_id。
    下单链接用 shopping 下发的 forwardCode；页内退改用 infoCode。取不到两个 code 则拒绝带下单按钮的页。
"""
import json, io, re, sys, os, datetime, glob, argparse
from urllib.parse import urlparse

from mcp_envelope import decode, find_envelope, peel_candidates

for _stream in (sys.stdout, sys.stderr):
    try:
        # Windows 控制台默认 GBK，打印 ¥ / 城市名会崩。
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TEMPLATE = os.path.join(SKILL_DIR, 'assets', 'air-domestic-oneway-page.html')
PAGE_BUSI_JS = os.path.join(SKILL_DIR, 'assets', 'air-domestic-page-busi.js')

def _load_mcp_base():
    """config.json 的 MCP 根地址（portal_config）；缺配置返回空串。"""
    try:
        from portal_config import mcp_base, forward_base, domestic_rule_url
        return mcp_base(), forward_base(), domestic_rule_url()
    except (OSError, RuntimeError, ImportError, ValueError):
        return '', '', ''


# 常见机场名(用于卡片/筛选展示;多机场侧一般会给出区名,这里按 IATA 补充城市名)
# CTU1/BJS1/SHA1 是城市聚合码不是机场，留空以免筛选项出现「CTU1」。
CITY_HINT = {'PEK': '首都', 'PKX': '大兴', 'CTU': '双流', 'TFU': '天府',
             'CSX': '黄花', 'XNN': '西宁', 'SHA': '虹桥', 'PVG': '浦东',
             'CAN': '白云', 'SZX': '宝安', 'NKG': '禄口', 'HGH': '萧山',
             'XIY': '咸阳', 'CKG': '江北', 'KMG': '长水', 'WUH': '天河',
             'TSN': '滨海', 'TNA': '遥墙', 'HRB': '太平', 'SHE': '桃仙',
             'DLC': '周水子', 'HET': '白塔', 'NNG': '吴圩', 'KWL': '两江',
             'URC': '地窝堡', 'LHW': '中川', 'FOC': '长乐', 'XMN': '高崎',
             'CGO': '新郑', 'CTU1': '', 'BJS1': '', 'SHA1': ''}

WEEK = ['周一','周二','周三','周四','周五','周六','周日']

def esc_json(o):
    # 紧凑 JSON 注入模板 JS；ensure_ascii=False 保留中文，和页面 JSON.parse 对拍。
    return json.dumps(o, ensure_ascii=False, separators=(',', ':'))

# ---- 静态预渲染:与模板 JS 的 esc/qtyN/flightHTML/kpis/dists 输出保持一致,
#      使页面在 JS 被禁(如部分预览通道)时仍能看到首屏航班数据。----

# 页面全局：免登配置（render 时注入，静态行与 JS 行共用 infoCode/forwardCode）
_CFG = {"host": "", "infoCode": "", "forwardCode": "", "forwardBase": "",
        "busiRule": "", "adult": 1, "top_open": 5, "links": False}

def _order_link(sn, flight_no, cab_id):
    """静态「去下单」forward 链接；未配置 forwardCode 时返回空。

    跳转目标 = 国内下单页 #/bookingPricing，最外层 serialNumber/flightId/cabId
    （选舱后才有 cabId；flightId=航段级航班号）。不要传 flightList。
    """
    if not _CFG["links"] or not cab_id:
        return ''
    from sso_forward import build_forward_url, build_domestic_order_route
    route = build_domestic_order_route(
        sn, flight_no, cab_id,
        adult=str(_CFG["adult"] or 1), fly_type='1')
    return build_forward_url(route, _CFG["host"], _CFG["forwardCode"])


def _tgq_btn(sn, cab_id, flight_no='', cab=''):
    """shopping 退/改缺文案时的退改政策补查按钮（mcpCall domestic_rule，同国际查舱位）。"""
    if not sn or not cab_id:
        return ''
    return ('<button type="button" class="cab-link cab-tgq" data-sn="%s" data-cabid="%s" '
            'data-flight="%s" data-cab="%s" title="退改文案不完整，点击现场查询">退改签</button>'
            % (_esc_a(sn), _esc_a(cab_id), _esc_a(flight_no or ''), _esc_a(cab or '')))


def _esc(s):
    return str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def _esc_a(s):
    # 去下单 href 在 HTML 属性里，引号必须再转一次，否则 key 含舱码时标签截断。
    return _esc(s).replace('"', '&quot;')

def _qty_n(n):
    # 航司余位 A 表示 9 张以上；筛选用数字比大小，按 9 计，和页面徽标「余 9 位」一致。
    if n == 'A':
        return 9
    if n.isdigit():
        return int(n)
    return 9

def _t_m(t):
    hh, mm = t.split(':')
    return int(hh) * 60 + int(mm)

def _dur(f):
    d = _t_m(f['dep'])
    a = _t_m(f['arr'])
    # 到达时刻小于出发=跨日；不加 1440 时长变负数，排序和中间那列会坏。
    return a + 1440 - d if a < d else a - d

def _fmt_dur(m):
    """显示用飞行时长：145 → 2h25m；排序仍用 _dur 原始分钟。"""
    h, mm = divmod(int(m or 0), 60)
    return ('%dh%dm' % (h, mm)) if h else ('%dm' % mm)

def _fmt_ot(ot):
    """准点率:源为字符串 '100.0'/'97.0'/'';去除 .0 后返回 '100'/'' 等(空则不展示)。
    注意:服务端有概率返回字面字符串 'null'(实测 84/168 条),必须当作空处理。"""
    ot = str(ot or '').strip()
    if not ot or ot.lower() in ('null', 'none', 'nan'):
        return ''
    if ot.endswith('.0'):
        ot = ot[:-2]
    return ot

def _apt_term(apt, term):
    """机场+航站楼拼接:机场(航站楼),如 首都机场(T3);航站楼为空则仅机场名。"""
    apt = (apt or '').strip()
    term = (term or '').strip()
    if not apt:
        return term
    return apt + ('(' + term + ')' if term else '')

def _static_cab_rows(f, c, ri):
    ent = bool(c['ent'])
    np_ = c['np']
    acf = f.get('acf', 0)
    baf = f.get('baf', 0)
    total = c['price'] + acf + baf
    fp = f.get('fp', 0)
    disc = ('%.1f折' % (c['price'] / fp * 10)) if fp and fp > 0 else '—'
    if ent:
        fare_html = '<span class="price-ent">¥%d</span>' % c['price']
    else:
        fare_html = '<span class="price-n">¥%d</span>' % c['price']
    old_span = ('<span class="pr-old">门市¥%d</span> ' % np_) if np_ > c['price'] else ''
    price_html = ('<div class="prcell"><div class="pr-fare">%s <span class="pr-tax">(含税 ¥%d)</span></div>'
                  '<div class="pr-sub">%s<span class="pr-disc">%s</span></div></div>' % (fare_html, total, old_span, disc))
    # 去下单：所有舱位(含代购 source 2/3/7)同一条免登 forward；代购仅用 .tag-buy 徽标
    url = _order_link(f.get('sn') or '', f.get('no') or '', c.get('cabId') or '')
    cell = ('<a class="btn-book" href="%s" target="_blank" rel="noopener">去下单</a>' % _esc_a(url)
            if url else '<span class="cab-dim">链接未生成</span>')
    acts = ''
    if c.get('needTgq') and c.get('cabId'):
        acts = _tgq_btn(f.get('sn') or '', c.get('cabId') or '', f.get('no') or '', c.get('cab') or '')
    if not acts and c.get('rp') is not None:
        acts = '<label class="cab-link" for="rchk%d">退改签</label>' % c['rp']
    if c.get('bp', -1) >= 0:
        if acts:
            acts += '<span class="cab-acts-sep">·</span>'
        acts += '<label class="cab-link" for="chk_lg%d">行李</label>' % c['bp']
    return ('<tr><td><span class="cab-code">' + _esc(c['cab']) + '</span>' + ('<span class="tag-buy">代购</span>' if c.get('buy') else '') + '</td>'
            '<td><span class="cab-name">' + _esc(c['cn']) + '</span>' + ('<span class="tag-ent">协议价</span>' if ent else '') + '</td>'
            '<td>' + ('<span class="cab-qty" title="剩余座位数">余 %d 位</span>' % _qty_n(c['n']) if c['n'] else '<span class="cab-dim">—</span>') + '</td>'
            '<td style="text-align:right">' + (c['w'] + 'kg' if c['w'] else '—') + '</td>'
            '<td style="text-align:right">' + price_html + '</td>'
            '<td style="text-align:right">' + acts + '</td>' +
            '<td style="text-align:right;width:110px">' + cell + '</td></tr>')

def _static_cab_bar(f, idx):
    return ''

def _static_card(f, idx):
    c = f['cabins'][0]
    total = c['price'] + f.get('acf', 0) + f.get('baf', 0)
    # 仅前 top_open 默认展开；其余点「更多」展开本地 shopping 舱位（首屏预览前 3 档）。
    # 到达时刻早于出发：跨日，时间轴上标 +1，避免看成当天更早到达。
    arr_p1 = '<span class="p1">+1</span>' if _t_m(f['arr']) < _t_m(f['dep']) else ''
    # 机场路线:机场名(航站楼)-机场名(航站楼),放到时间轴中间(替代原城市对文案)
    route = _apt_term(f.get('dep_apt', ''), f.get('dep_term', '')) + '-' + _apt_term(f.get('arr_apt', ''), f.get('arr_term', ''))
    # 共享航班标签(显示实际承运航班号 shareId)
    share_id = f.get('share', '')
    share_tag = ('<span class="tag-share" title="实际承运 %s">共享 %s</span>' % (_esc(share_id), _esc(share_id))) if share_id else ''
    ot_tag = ('<span class="fl-ot">准点率%s%%</span>' % _esc(f.get('ot', ''))) if f.get('ot') else ''
    # 原生交互结构:details/summary 展开舱位(无 JS 可用),与 JS 版 flightHTML 严格同构
    # 前 top_open 个推荐航班默认展开（与 JS openSet/idx<TOP_OPEN 同构）
    open_attr = ' open' if idx < _CFG['top_open'] else ''
    open_tag = '<details class="card" id="card%d"%s><summary class="card-head">' % (idx, open_attr)
    mid = ('<div class="fl-time"><span class="big dep">' + f['dep'] + '</span>'
           '<span class="mid">%s<br><span class="rt-line">%s</span></span>' % (_fmt_dur(_dur(f)), _esc(route)) +
           '<span class="big arr">' + f['arr'] + arr_p1 + '</span></div>')
    info = ('<div class="fl-info"><span class="fl-no">' + _esc(f['no']) + '</span>' + share_tag +
            '<div class="fl-air">' + _esc(f['air']) + '</div>' +
            '<div class="fl-sub"><span>' + _esc(f['ac']) + '</span><span>餐食 ' + _esc(f['meal']) + '</span>' +
            ot_tag +
            '<span class="fl-fee">机建¥%d 燃油¥%d</span></div></div>' % (f.get('acf', 0), f.get('baf', 0)))
    display_cabins = f.get('displayCabins') or f['cabins']
    cap_txt = '含税总价起 · %d个舱位' % len(f['cabins'])
    price = ('<div class="fl-price"><div class="lp">¥%d</div>' % total +
             '<div class="cap" id="cap%d">' % idx + ('含协议价舱 · ' if c['ent'] else '') + cap_txt + '</div></div>')
    btn = '<span class="more-btn" id="mb%d"><span class="mo">更多</span><span class="mc">收起</span></span>' % idx
    rows = ''.join(_static_cab_rows(f, cb, ri) for ri, cb in enumerate(display_cabins))
    if len(display_cabins) < len(f['cabins']):
        rows += (
            '<tr><td colspan="7" style="text-align:center">'
            '<button type="button" class="btn-cab-more" data-more-idx="%d">'
            '展开全部 %d 个舱位</button></td></tr>'
        ) % (idx, len(f['cabins']))
    # 结构与 JS 版 flightHTML 严格同构:summary 关闭后是 cab-wrap(舱位表)
    table = ('<div class="cab-wrap" id="cw%d">' % idx + _static_cab_bar(f, idx)
             + '<table class="cab-table"><thead><tr>'
             '<th style="text-align:left">舱位</th><th style="text-align:left">等级</th>'
             '<th style="text-align:left">余量</th><th style="text-align:right">免费托运</th><th style="text-align:right">票价·含税总价</th>'
             '<th style="text-align:right">退改/行李</th><th style="text-align:right">去下单</th></tr></thead><tbody>'
             + rows + '</tbody></table></div>')
    return open_tag + mid + info + price + btn + '</summary>' + table + '</details>'

def build_rules_html(FL, rr_list, cc_list):
    """为每个唯一的 (退票规则, 改签规则) 组合生成 checkbox CSS 弹层，
    并为每个唯一行李文本生成行李弹层；给每个舱位写入 rp / bp。

    shopping 退票或改签文案任一为空且具备 cabId 的舱位：不挂 CSS 弹层，改由页面
    按钮做退改政策补查：页内直调 domestic_rule（与国际「查舱位」同形态，needTgq=true）。
    """
    pairs = {}
    for f in FL:
        for c in f['cabins']:
            if c.get('needTgq') and c.get('cabId'):
                c['rp'] = None
                continue
            pr = (c['rfi'], c['cci'])
            if pr not in pairs:
                pairs[pr] = len(pairs)
            c['rp'] = pairs[pr]
    parts = []
    for (rfi, cci), pid in sorted(pairs.items(), key=lambda kv: kv[1]):
        rf = rr_list[rfi] if 0 <= rfi < len(rr_list) else ''
        cf = cc_list[cci] if 0 <= cci < len(cc_list) else ''
        no_rule_hint = '本舱位未附带退改规则文本'
        rf_tx = _esc(rf) if rf else no_rule_hint
        cf_tx = _esc(cf) if cf else no_rule_hint
        rf_cls = '' if rf else ' empty'
        cf_cls = '' if cf else ' empty'
        parts.append(
            '<div class="rt" id="rt%d"><input type="checkbox" id="rchk%d" class="rchk">'
            '<label class="rmask" for="rchk%d"></label>'
            '<div class="rpop">'
            '<div class="rtitle">退改签规则</div>'
            '<div class="rsub">票价不含机建燃油 · 含税总价=票价+机建+燃油 · 规则以实际下单为准</div>'
            '<div class="rsec"><div class="rh">退票规则</div><div class="rtx%s">%s</div></div>'
            '<div class="rsec"><div class="rh">改签规则</div><div class="rtx%s">%s</div></div>'
            '<label class="rclose" for="rchk%d">关 闭</label>'
            '</div></div>' % (pid, pid, pid, rf_cls, rf_tx, cf_cls, cf_tx, pid))
    # 退改政策补查共用弹层（mcpCall domestic_rule 写入）
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
    # 按唯一行李文本去重，生成行李弹层并为舱位写 bp
    lugg = {}
    for f in FL:
        for c in f['cabins']:
            lg = c.get('lg') or ''
            if lg and lg not in lugg:
                lugg[lg] = len(lugg)
            c['bp'] = lugg.get(lg, -1)
    for lg, lid in sorted(lugg.items(), key=lambda kv: kv[1]):
        parts.append(
            '<div class="rt" id="rt_lg%d"><input type="checkbox" id="chk_lg%d" class="rchk">'
            '<label class="rmask" for="chk_lg%d"></label>'
            '<div class="rpop">'
            '<div class="rtitle">行李政策</div>'
            '<div class="rsub">免费托运行李与随身携带额度以实际出票舱位为准</div>'
            '<div class="rtx">%s</div>'
            '<label class="rclose" for="chk_lg%d">关 闭</label>'
            '</div></div>' % (lid, lid, lid, _esc(lg), lid))
    return ''.join(parts)

def build_static_html(FL, side, apt_all, apt_title):
    """生成无 JS 也能展示的静态首屏片段,返回替换字典。

    静态列表只渲前 PAGE_SIZE 班（与 JS 本地分页首页一致）；完整 FL 仍注入脚本供筛/排/翻页。
    """
    PAGE_SIZE = 20
    tot = len(FL)
    tot_cab = sum(len(f['cabins']) for f in FL)
    ent_cab = sum(1 for f in FL for c in f['cabins'] if c['ent'])
    airs = sorted({f['air'] for f in FL})
    # 主机场分布计数(用于机场分布条)
    cnt = {}
    for f in FL:
        cnt[f['apt']] = cnt.get(f['apt'], 0) + 1
    # 最低价航班(按含税总价)
    def _tot(f):
        return f['cabins'][0]['price'] + f.get('acf', 0) + f.get('baf', 0)
    mf = min(FL, key=_tot)
    min_total = _tot(mf)

    # KPI(与模板 kpis() 一致)
    kpis = ('<div class="kpi"><div class="v">%d<em>班</em></div><div class="l">全部直飞 无经停</div></div>' % tot +
            '<div class="kpi"><div class="v">¥%d<em>起</em></div><div class="l">最低含税价 %s%s</div></div>' %
            (min_total, mf['no'], '(协议价)' if mf['cabins'][0]['ent'] else '') +
            '<div class="kpi"><div class="v">%d<em>/%d</em></div><div class="l">协议价舱位(enterpriseId 非空)</div></div>' % (ent_cab, tot_cab) +
            '<div class="kpi"><div class="v">%d<em>家</em></div><div class="l">执飞航司</div></div>' % len(airs))

    # 机场分布条(与模板 dists() 一致)
    ks = list(cnt.keys())
    ma = max(list(cnt.values()) + [1])
    apt_rows = ''.join(
        '<div class="bar-row"><span class="bl">%s</span><div class="bt"><div class="bf" style="width:%s%%"></div></div><span class="bv">%d班</span></div>'
        % ((k + '出发') if side == 'dep' else ('抵' + k), '%.2f' % (cnt[k] / ma * 100), cnt[k]) for k in ks)
    # 时段分布条(与模板 dists() 一致:h<9→0, <12→1, <15→2, <18→3, <21→4, else 5)
    prd = [["06-09", 0], ["09-12", 0], ["12-15", 0], ["15-18", 0], ["18-21", 0], ["21-24", 0]]
    for f in FL:
        h = int(f['dep'][:2])
        i = 0 if h < 9 else (1 if h < 12 else (2 if h < 15 else (3 if h < 18 else (4 if h < 21 else 5))))
        prd[i][1] += 1
    mp = max([p[1] for p in prd] + [1])
    prd_rows = ''.join(
        '<div class="bar-row"><span class="bl">%s</span><div class="bt"><div class="bf" style="width:%s%%"></div></div><span class="bv">%d班</span></div>'
        % (p[0], '%.2f' % (p[1] / mp * 100), p[1]) for p in prd)

    # 下拉选项
    apt_opts = '<option value="">%s</option>' % apt_all + ''.join('<option value="%s">%s</option>' % (_esc_a(a), _esc(a)) for a in ks)
    air_opts = '<option value="">全部航司</option>' + ''.join('<option>%s</option>' % _esc(a) for a in airs)

    # 航班列表(静态首屏=本地分页首页；JS 正常时 render() 会覆盖)
    shown = min(PAGE_SIZE, tot)
    cards = ''.join(_static_card(f, i) for i, f in enumerate(FL[:PAGE_SIZE]))
    if tot > PAGE_SIZE:
        cnt_txt = '共 %d / %d 班 · 显示 1–%d（翻页需页面脚本）' % (tot, tot, shown)
    else:
        cnt_txt = '共 %d / %d 班 · 显示 1–%d' % (tot, tot, shown) if tot else '共 0 / 0 班 · 显示 0–0'

    return {
        '{{STATIC_KPIS}}': kpis,
        '{{STATIC_APT_DIST}}': apt_rows,
        '{{STATIC_PRD_DIST}}': prd_rows,
        '{{STATIC_APT_OPTS}}': apt_opts,
        '{{STATIC_AIR_OPTS}}': air_opts,
        '{{STATIC_CNT}}': cnt_txt,
        '{{STATIC_LIST}}': cards,
    }

def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument('src', help='domestic_shopping 的返回；`-` 表示从 stdin 读')
    ap.add_argument('--from-city', required=True, help='出发城市显示名,如 长沙')
    ap.add_argument('--to-city', required=True, help='到达城市显示名,如 成都')
    ap.add_argument('--from-code', default='', help='出发城市码(可选,用于文件名)')
    ap.add_argument('--to-code', default='', help='到达城市码(可选,用于文件名)')
    ap.add_argument('--date', default='', help='航班日期 YYYY-MM-DD(缺省取数据首班日期)')
    ap.add_argument('--date-text', default='', help='标题日期文案,如 2026-09-03(周四)(缺省自动生成)')
    ap.add_argument('--out', default='', help='输出 HTML 路径(缺省 feihe-<from>-<to>-<date>.html)')
    ap.add_argument('--side', default='auto', choices=['auto', 'dep', 'arr'],
                    help='多变机场所在侧:auto 自动推断 / dep 出发 / arr 到达')
    ap.add_argument('--full-note', action='store_true',
                    help='标题注明(因公·协议价)后缀')
    ap.add_argument('--adult', type=int, default=1, help='下单页 adultCount(默认 1)')
    ap.add_argument('--top-open', type=int, default=5,
                    help='默认展开舱位的推荐航班数(默认 5)；其余航班点「更多」展开本地 shopping 舱位')
    ap.add_argument('--no-order-links', action='store_true',
                    help='不生成去下单链接配置(纯静态分析页)')
    return ap.parse_args()

def load_data(path):
    raw = sys.stdin.read().strip() if path == '-' else io.open(path, encoding='utf-8').read().strip()
    data = decode(raw)
    if isinstance(data, str):
        # 源文本前面可能有 MCP 日志前缀，不是纯 JSON；从第一个 [ 或 { 截。
        m = re.search(r'[\[{].*', data, re.S)
        if not m:
            raise SystemExit('源文件不是 JSON，也截取不到 JSON 片段')
        data = decode(m.group(0))
    # requestSeqNo 在 content 信封层（不在 structuredContent），取出来供页脚展示。
    env = find_envelope(data)
    seq_no = str((env or {}).get('requestSeqNo') or '').strip()
    for candidate in peel_candidates(data):
        # 信封套几层不固定；优先 structuredContent，带着 flightList 的才是 domestic_shopping 载荷。
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

def infer_multi_side(segs, preferred='auto', port_name=None):
    """返回 (side, airports) —— 多机场侧与 {三字码:显示名}。"""
    port_name = port_name or {}
    def _disp(code):
        return port_name.get(code) or CITY_HINT.get(code, code)
    dep_set, arr_set = {}, {}
    for s in segs:
        al = s.get('airLine') or ''
        if len(al) >= 6:
            d, a = al[:3], al[3:6]
            dep_set.setdefault(d, _disp(d))
            arr_set.setdefault(a, _disp(a))
    if preferred != 'auto':
        side = preferred
    else:
        # 两侧机场数相同（都是单机场或一样多）时挂到达侧，避免把出发城市名标成「多机场」。
        side = 'dep' if len(dep_set) > len(arr_set) else ('arr' if len(arr_set) > len(dep_set) else 'arr')
    airports = dep_set if side == 'dep' else arr_set
    return side, airports

def build(args):
    data, request_seq_no = load_data(args.src)

    # ---- 免登：host/forwardBase/busiRule 引用 config.json，code 取自当次 shopping ----
    base_url, fwd_base, rule_url = _load_mcp_base()
    _CFG['host'] = urlparse(base_url).netloc if base_url else ''
    _CFG['forwardBase'] = fwd_base
    _CFG['busiRule'] = rule_url
    _CFG['adult'] = args.adult or 1
    _CFG['top_open'] = args.top_open if args.top_open is not None else 5
    _CFG['infoCode'] = str(data.get('infoCode') or '').strip()
    _CFG['forwardCode'] = str(data.get('forwardCode') or '').strip()
    if args.no_order_links:
        _CFG['links'] = False
        _CFG['infoCode'] = ''
        _CFG['forwardCode'] = ''
    else:
        _CFG['links'] = bool(_CFG['host'] and _CFG['infoCode'] and _CFG['forwardCode'])
        if not _CFG['links']:
            print('[错误] 未取到 infoCode/forwardCode/host，拒绝交付死页面（去下单/退改会失效）。\n'
                  '  处理：① 确认 domestic_shopping 成功结果最外层带 infoCode 与 forwardCode 后重跑；\n'
                  '  ② 只要纯静态分析页（无下单链接）时，显式加 --no-order-links 重跑。',
                  file=sys.stderr)
            raise SystemExit(3)

    fl_items = data.get('flightList') or []
    airways = {a.get('companyNo'): a.get('companyName') for a in data.get('airways', []) if isinstance(a, dict) and a.get('companyNo')}
    # 机场名(cityCode 三字码 → airPortName 机场全称,如 PEK→首都机场 / PKX→大兴机场 / XNN→曹家堡机场)
    port_name = {}
    for c in data.get('citys', []):
        if isinstance(c, dict) and c.get('cityCode'):
            port_name[c['cityCode']] = c.get('airPortName') or ''
    types = {}
    for t in data.get('types', []):
        if isinstance(t, dict) and t.get('type') is not None:
            types[str(t['type'])] = t.get('name') or ''
    # 机型字典经常没有 919；不补会在卡片上显示数字 919。
    types['919'] = 'C919'

    # 汇集全部航段,推断多变机场侧
    segs = []
    for item in fl_items:
        for s in item.get('flight', []):
            segs.append(s)
    if not segs:
        raise SystemExit('源数据中无航段(flightList[].flight 为空)')
    side, airports = infer_multi_side(segs, args.side, port_name)

    # 日期
    d0 = (segs[0].get('flyDate') or '')[:10]
    date = args.date or d0
    if not args.date_text:
        dt = datetime.date.fromisoformat(date)
        args.date_text = '%s(%s)' % (date, WEEK[dt.weekday()])

    # ---- 组装 FL / RR / CC ----
    rr_map, cc_map = {}, {}   # 文本 → 索引
    rr_list, cc_list = [], []
    def _norm(txt):
        # 源数据退改政策规则文本带 \r\n,归一为 \n 以便按内容去重且与原版一致
        t = (txt or '').replace('\r\n', '\n').replace('\r', '\n')
        # 部分规则文本无换行、以中文分号连接,按「；」拆分换行,保证弹层可读
        if '\n' not in t and '；' in t:
            t = t.replace('；', '\n')
        return t
    def ridx(txt, mp, lst):
        txt = _norm(txt)
        if not txt:
            return -1
        if txt not in mp:
            mp[txt] = len(lst); lst.append(txt)
        return mp[txt]

    serial_number = str(data.get('serialNumber') or '').strip()
    FL, total_ent = [], 0
    for item in fl_items:
        group_id = str(item.get('flightId') or '').strip()
        # 若载荷经 air_domestic_merge_shopping 合并，item 可能带本段查询的 serialNumber（_sn）；
        # 单结果载荷没有该字段，回退到顶层 serialNumber。禁止跨查询混用标识。
        item_sn = str(item.get('_sn') or '').strip() or serial_number
        for s in item.get('flight', []):
            fid = s.get('flightId') or ''
            mpref = re.match(r'^([A-Z0-9]{2})', fid)
            air = airways.get(mpref.group(1), mpref.group(1) if mpref else fid)
            apt3 = (s.get('airLine') or '')[:3] if side == 'dep' else (s.get('airLine') or '')[3:6]
            apt_disp = airports.get(apt3, apt3 or '')
            # 出发/到达机场(前后3位 IATA→机场全称)及航站楼、共享航班、准点率
            al = s.get('airLine') or ''
            dep3, arr3 = al[:3], al[3:6]
            dep_apt = port_name.get(dep3) or CITY_HINT.get(dep3, dep3) or dep3
            arr_apt = port_name.get(arr3) or CITY_HINT.get(arr3, arr3) or arr3
            dep_term = str(s.get('fromPort') or '').strip()
            arr_term = str(s.get('toPort') or '').strip()
            share = str(s.get('shareId') or '').strip()
            ot = _fmt_ot(s.get('onTime'))
            cabins = []
            for c in s.get('cabins', []):
                pr = c.get('price') or 0
                if pr <= 0:
                    # 售罄/无价舱位进页面会算出负折扣，去下单链接也会带上空价。
                    continue
                np_ = c.get('normalPrice') or pr
                w_ = str(c.get('weight') or '').strip()
                eid = str(c.get('enterpriseId') or '').strip()
                src = str(c.get('source') or '').strip()
                rule = c.get('rule') or {}
                cab_id = str(c.get('cabId') or '').strip()
                lg_ = (c.get('luggage') or '').strip().replace('\r\n', '\n').replace('\r', '\n')
                rfi = ridx(rule.get('refundText'), rr_map, rr_list)
                cci = ridx(rule.get('changeText'), cc_map, cc_list)
                cabins.append({
                    'cab': c.get('cab') or '',
                    'cn': c.get('cabName') or '',
                    'price': pr, 'np': np_ if np_ > 0 else pr,
                    'w': w_, 'ent': eid,
                    'buy': src in ('2', '3', '7'),  # source=2/3/7 为代购舱位（仅徽标）
                    'n': str(c.get('num') or '').strip(),
                    'cabId': cab_id,
                    'lg': lg_,
                    'bp': -1,
                    'rfi': rfi,
                    'cci': cci,
                    # 退或改任一为空：点击做退改政策补查（页内直调 domestic_rule，需 cabId）
                    'needTgq': (rfi < 0 or cci < 0),
                })
                if eid:
                    total_ent += 1
            if not cabins:
                continue
            # 卡片「起」价取第一舱，必须先按价格排；同价再按舱码，避免每次生成顺序乱跳。
            cabins.sort(key=lambda x: (x['price'], x['cab']))
            for i, row in enumerate(cabins):
                row['k'] = row.get('cabId') or ('%s_%s_%d' % (fid, row['cab'], i))
            FL.append({
                'no': fid, 'gid': group_id, 'sn': item_sn,
                'air': air,
                'dep': (s.get('flyDate') or '')[11:16],
                'arr': (s.get('arrDate') or '')[11:16],
                'apt': apt_disp,
                'ac': types.get(str(s.get('type')), str(s.get('type')) or '—'),
                # 个别餐食字段是长说明，卡片一行会被撑破。
                'meal': (s.get('meal') or '无')[:12],
                'acf': int(s.get('acf') or 0),  # 机场建设费(航班级,各舱位相同)
                'baf': int(s.get('baf') or 0),  # 燃油附加费(航班级,各舱位相同)
                'fp': int(s.get('fullPrice') or 0),  # Y舱全价票价(用于算折扣)
                'share': share,  # 共享航班(shareId 非空=实际由他航承运)
                'dep_apt': dep_apt, 'arr_apt': arr_apt,  # 出发/到达机场名
                'dep_term': dep_term, 'arr_term': arr_term,  # 出发/到达航站楼
                'ot': ot,  # 准点率(去 .0 的百分数字符串,空=无数据)
                'cabins': cabins,
            })
    # 因公口径按起飞时刻排，不按价格（和 shopping 的 sortBy=DEPARTURE_TIME 一致）。
    FL.sort(key=lambda f: f['dep'])
    if not FL:
        raise SystemExit('无有效舱位航班')

    # ---- 统计（裁剪前全量口径，进 KPI 注入与控制台输出） ----
    tot_cab = sum(len(f['cabins']) for f in FL)
    apt_cnt = {}
    for f in FL:
        apt_cnt[f['apt']] = apt_cnt.get(f['apt'], 0) + 1
    air_cnt = len({f['air'] for f in FL})
    min_price = min(f['cabins'][0]['price'] + f.get('acf', 0) + f.get('baf', 0) for f in FL)
    ent_fl = sum(1 for f in FL if any(c['ent'] for c in f['cabins']))

    # ---- 渐进展示：保留真实全量舱位；首屏每班只渲染前三档，点「展开全部」看其余。----
    cabin_preview = 3
    for i, f in enumerate(FL):
        f['entAny'] = 1 if any(c['ent'] for c in f['cabins']) else 0
        f['displayCabins'] = f['cabins'][:cabin_preview]
    prerender_cab = sum(len(f['displayCabins']) for f in FL)
    side_txt = '出发' if side == 'dep' else '到达'
    multi_apt = len(apt_cnt) > 1
    apt_dist = ' '.join('%s %s' % (k, apt_cnt[k]) for k in sorted(apt_cnt))
    sub_tail = ('(%s机场分布: %s)' % (side_txt, apt_dist)) if multi_apt else ''
    sub = 'feihe-cli 国内航班查询 · 因公口径 · %d 班直飞%s · 点击「更多」展开全部舱位价格' % (len(FL), sub_tail)

    route_mid = '%s→%s' % (args.from_city, args.to_city)
    h1 = '%s → %s · %s航班分析' % (args.from_city, args.to_city, args.date_text)
    title = ('%s %s 航班分析' % (route_mid, args.date_text)) + ('(因公·协议价)' if args.full_note else '')
    apt_all = '全部%s机场' % side_txt
    apt_title = '%s机场分布' % side_txt

    # ---- 渲染模板 ----
    tpl = io.open(TEMPLATE, encoding='utf-8').read()
    tpl = re.sub(r'^<!--.*?-->\s*', '', tpl, count=1, flags=re.S)
    _busi_mark = '/*@@AIR_DOMESTIC_PAGE_BUSI@@*/'
    assert _busi_mark in tpl, '页内 busi 锚点缺失'
    tpl = tpl.replace(_busi_mark, io.open(PAGE_BUSI_JS, encoding='utf-8').read(), 1)
    reps = {
        '{{TITLE}}': title, '{{H1}}': h1, '{{SUB}}': sub,
        '{{APT_SIDE}}': side, '{{APT_ALL}}': apt_all,
        '{{APT_TITLE}}': apt_title,
        '{{TOP_OPEN}}': str(_CFG['top_open']),
        '{{SEQ_FOOT}}': (
            '<div style="color:#e8eaed;font-size:10px;margin-top:6px;text-align:center">'
            '请求流水号 requestSeqNo：<span style="user-select:all">%s</span></div>'
            % _esc(request_seq_no) if request_seq_no else ''),
    }
    for k, v in reps.items():
        assert k in tpl, '占位符缺失: ' + k
        tpl = tpl.replace(k, v)  # 全量替换(HTML 静态区与 JS 变量区可能各出现一次)
    # 静态首屏注入(无 JS 兜底;JS 正常时首帧 render() 会即时覆盖为同构内容)
    # 注意顺序:build_rules_html 会给每个舱位写入 rp(规则组合索引),必须先于航班卡生成调用
    rules_html = build_rules_html(FL, rr_list, cc_list)
    assert '{{STATIC_RULES}}' in tpl, '规则弹层占位符缺失'
    assert tpl.count('{{STATIC_RULES}}') == 1, '规则弹层占位符须唯一'
    tpl = tpl.replace('{{STATIC_RULES}}', rules_html, 1)
    for k, v in build_static_html(FL, side, apt_all, apt_title).items():
        assert k in tpl, '静态占位符缺失: ' + k
        assert tpl.count(k) == 1, '静态占位符须唯一: ' + k
        tpl = tpl.replace(k, v, 1)
    # 数据块注入
    tpl = tpl.replace('var FL=[]; //@@FL@@', 'var FL=' + esc_json(FL) + ';', 1)
    tpl = tpl.replace('var RR=[]; //@@RR@@', 'var RR=' + esc_json(rr_list) + ';', 1)
    tpl = tpl.replace('var CC=[]; //@@CC@@', 'var CC=' + esc_json(cc_list) + ';', 1)
    assert 'var QUERY_SN=""; //@@SN@@' in tpl, 'QUERY_SN 锚点缺失'
    tpl = tpl.replace('var QUERY_SN=""; //@@SN@@', 'var QUERY_SN=' + esc_json(serial_number) + ';', 1)
    # 全量统计注入（KPI 卡片用）
    kpi_data = {'fl': len(FL), 'cab': tot_cab, 'ent': total_ent}
    assert 'var KPI=__KPI__;' in tpl, 'KPI 锚点缺失'
    tpl = tpl.replace('var KPI=__KPI__;', 'var KPI=' + esc_json(kpi_data) + ';', 1)
    # 免登配置（code 只进本机 HTML；禁止打印/落日志）
    page_cfg = {'host': _CFG['host'], 'infoCode': _CFG['infoCode'], 'forwardCode': _CFG['forwardCode'],
               'forwardBase': _CFG.get('forwardBase') or '',
               'busiRule': _CFG.get('busiRule') or '',
               'order': {'adult': _CFG['adult']}}
    assert 'var CFG=__PAGE_CFG__;' in tpl, 'CFG 锚点缺失'
    tpl = tpl.replace('var CFG=__PAGE_CFG__;', 'var CFG=' + esc_json(page_cfg) + ';', 1)
    assert 'var TOP_OPEN=__TOP_OPEN__;' in tpl, 'TOP_OPEN 锚点缺失'
    tpl = tpl.replace('var TOP_OPEN=__TOP_OPEN__;', 'var TOP_OPEN=%d;' % _CFG['top_open'], 1)

    out = args.out or 'feihe-%s-%s-%s.html' % (
        (args.from_code or args.from_city), (args.to_code or args.to_city), date.replace('-', ''))
    # newline='': Windows 下不要把模板里的 \n 写成 \r\n，否则 JS 字符串和自检会对不上。
    io.open(out, 'w', encoding='utf-8', newline='').write(tpl)

    # 静态区标签平衡自检:div 开闭不平衡会导致洋葱嵌套,empty/note 被吞进卡片,
    # render() 清空 list 时连它们一起清掉并中断顶层脚本(退改政策等按钮全部失效)
    static_part = tpl[:tpl.find('<script>')]
    div_ok = len(re.findall(r'<div\b', static_part)) == static_part.count('</div>')
    det_ok = static_part.count('<details') == static_part.count('</details>')
    sum_ok = static_part.count('<summary') == static_part.count('</summary>')
    print('OUT:', out)
    print('航班 %d · 舱位 %d · 协议舱 %d · 航司 %d' % (len(FL), tot_cab, total_ent, air_cnt))
    print('多变机场侧:%s · %s · 最低含税价 ¥%d · 含协议价航班 %d/%d' % (side_txt, apt_dist, min_price, ent_fl, len(FL)))
    print('默认展开前 %d 个推荐航班 · 去下单链接:%s · 页内退改:%s' % (
        _CFG['top_open'],
        '已生成(免登forward)' if _CFG['links'] else '未生成(缺code/host)',
        '已配置' if (_CFG['infoCode'] and _CFG.get('busiRule')) else '未配置'))
    print('静态区div平衡:%s · details平衡:%s · summary平衡:%s' % (
          'OK' if div_ok else 'FAIL',
          'OK' if det_ok else 'FAIL', 'OK' if sum_ok else 'FAIL'))
    if not div_ok or not det_ok or not sum_ok:
        raise SystemExit('自检失败,输出文件不可用')
    return out, FL, total_ent, min_price, ent_fl

if __name__ == '__main__':
    a = parse_args()
    build(a)
