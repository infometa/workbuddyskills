#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""餐道外卖评价报告生成器（零依赖，仅 Python 标准库）。

读取 get_review_expert_analysis_data 工具返回的 JSON，映射为 REPORT_DATA，
注入 skill 内置模板 references/interactive-report-template.html，产出自包含 HTML 报告。
LLM 不再手写 HTML，只负责调工具取数并落盘 data.json，本脚本完成重活。

适配连接器 2026-09 改版后的返回结构（新版 schema）：
    logId / hasData / commentDetails / reviewMetricSummary / orderAndReceiptSummary /
    badCommentReasonDistribution / commentScoreDistribution / dailyCommentTrends / badCommentSamples
关键口径：
    - 差评以 commentLevel=='差评' 判定（工具口径：好评 5 分、中评 3-4 分、差评 0-2 分）；
      旧 v2 的 reviewDetails.rows[].level=='NEGATIVE' 已改为 commentDetails[].commentLevel。
    - 差评原因分布统一取 badCommentTags（二级细粒度多层级，形如 "口味问题-味道异常" / "制作/错漏送-做错货不对板"）；
      每条按首个 "-" 拆为「一级-二级」两层（一级=大类/二级=具体细项），命中多个时以字符串化列表给出。
      commentTags（旧一级体系：菜品口味/菜品份量/…/菜品异物/其他原因）不再驱动原因分布。
      badCommentTags 为"字符串化的 Python 列表"（形如 "['口味问题-味道异常', ...]"），须用 clean_tags() 经 ast.literal_eval 还原。
    - 所有比例为 0~1 小数；汇总时分子分母分别求和再相除，不平均各行比例。
    - 24h差评回复率（周期级）= replyWithin24Hours / badCommentCount（来自 reviewMetricSummary，
      与工具 replyWithin24HoursPer 口径一致；美团 1-48h、其他 1-24h 已内置）；dailyCommentTrends 无 reply 字段，
      故无逐日折线，日趋势图改画周期级参考虚线。
    - commentScoreDistribution.commentScore 为字符串 '1'~'5'，需转 int；无 date 维度（整周期汇总）。
    - 接口无 period 字段，统计周期从 dailyCommentTrends 的 commentDate 推导（注意 MCP 窗口左移 bug，见 data-contract.md）。

用法：
    python gen_report.py <data.json> <output.html> [template.html]
若省略 template.html，默认使用脚本同目录 ../references/interactive-report-template.html。
"""
import ast
import json
import os
import re
import sys

# 平台 code -> 中文名（工具返回的 platformTypeDesc 现已是中文，这里仅作兜底）；
# 若数据偶尔回英文 code（MT/ELE/TB/JD…）也能正确映射。
PLAT = {
    'ELE': '饿了么', 'MT': '美团', 'TB': '淘宝闪购', 'JD': '京东秒送',
    'DOUYIN': '抖音', 'DY': '抖音', 'OTHER': '其他', 'UNK': '其他',
}

# 固定分类配色（badCommentTags 一级大类，两级同色；一级 = '-' 前部分）
TAGCOLOR = {
    '口味问题': '#1971c2', '分量问题': '#e8590c', '制作/错漏送': '#2f9e44',
    '异物问题': '#e03131', '服务态度': '#c2255c', '缺餐具': '#9c36b5',
    '配送超时': '#0c8599', '包装/撒漏': '#099268', '其他原因': '#868e96',
    '笼统差评': '#f08c00',
}


def ch(code):
    """平台中文名（platformTypeDesc 已是中文，直接返回；英文 code 走兜底映射）。"""
    if code is None:
        return '其他'
    return PLAT.get(code, code) if code in PLAT else code


def to_int(v):
    """把 '1'~'5' 之类的字符串/数字安全转 int，失败返回 None。"""
    try:
        return int(str(v).strip())
    except (ValueError, TypeError, AttributeError):
        return None


def num(v, default=0.0):
    """订单量 / 实收金额类字段安全转 float；None / 空 / 非法 → default(0.0)。

    兜底无订单的门店×渠道组合返回 null 的情况
    （orderNum / totalActualReceipt / preOrderNum / preTotalActualReceipt 曾出现 null，
     触发 MCP 传输层 output schema 校验失败，整体响应被拒——该问题需数据团队在
     后端把 null 补 0 或把 schema 放宽为可空；本函数仅保证「数据若能到达」时口径自洽）。
    """
    if v is None:
        return default
    try:
        return float(v)
    except (ValueError, TypeError, AttributeError):
        return default


def clean_tags(v):
    """还原工具返回的"字符串化的 Python 列表"。

    新版接口把标签存为字符串化列表，形如：
        "['其他原因']"
        "['口味问题-味道异常', '分量问题-份量偏少', ...]"
        "[]"
    统一还原为 list[str]。

    数仓写入偶发序列化损坏，本函数一并兜底还原，避免脏标签进报告：
        - 嵌套双层括号 "[['其他原因-其他''门店出品']"（literal_eval 成功，
          相邻字面量被合并为 '其他原因-其他门店出品'，属已知脏值，如实保留）；
        - 两条标签被 ']' 拼接残留："笼统差评-笼统不满]口味问题-味道异常"
          （literal_eval 失败 → 兜底按 '|'、','、'[' 拆开还原为两条）；
        - 尾随空格 "'分量问题-份量偏少 '"（list comp 内 strip 去除）；
        - 一级标签泄漏进二级："其他原因"（合法单值，保留）。
    损坏兜底仅在 literal_eval 失败时触发；正常格式行为不变。
    """
    if v is None:
        return []
    if isinstance(v, list):
        return [str(x).strip() for x in v if str(x).strip()]
    s = str(v).strip()
    if not s or s in ('[]', "['']", '[""]'):
        return []
    try:
        out = ast.literal_eval(s)
        if isinstance(out, (list, tuple)):
            items = [str(x).strip() for x in out if str(x).strip()]
        else:
            items = [str(out).strip()] if str(out).strip() else []
    except (ValueError, SyntaxError):
        # 损坏兜底：剥括号、统一按 | / , 拆分（']' 拼接残留在此被还原为两条）
        s2 = s.strip('[]').replace('[', '|').replace(']', '|').replace("'", '').replace('"', '')
        items = [x.strip() for x in re.split(r'[|,]+', s2) if x.strip()]
    # 二次清洗：单标签内若仍含 '['/']'（拼接残留没拆干净）再拆一次
    final = []
    for it in items:
        it = it.strip()
        if not it:
            continue
        if '[' in it or ']' in it:
            for piece in re.split(r'[\[\]]+', it):
                piece = piece.strip()
                if piece:
                    final.append(piece)
        else:
            final.append(it)
    return final


def dedupe_content(s):
    """工具 content 形如 正文【餐品评论】*****:正文;*****:正文; 取第一段。"""
    if not s:
        return ''
    if '【餐品评论】' in s:
        return s.split('【餐品评论】')[0].strip()
    return s.strip()


def build_report_data(d):
    cd = d.get('commentDetails') or []

    # 差评明细：commentLevel=='差评'（新接口无 reviewDetails 包裹，全量评论在 commentDetails）
    QUOTES = []
    for r in cd:
        if (r.get('commentLevel') or '') != '差评':
            continue
        # 二级细粒度标签 badCommentTags 形如「一级-二级」（如 口味问题-味道异常 / 制作/错漏送-做错货不对板）；
        # 命中多个时以字符串化列表给出，clean_tags 还原为多条；下面按首个 '-' 拆出 一级/二级 两层。
        raw2 = clean_tags(r.get('badCommentTags'))
        t1 = []; t2 = []; pairs = []
        for full in raw2:
            s = full.strip()
            if '-' in s:
                a, b = s.split('-', 1)
            else:
                a = b = s  # 无 '-' 的兜底标签（如「其他原因」），一级二级同值
            a = a.strip(); b = b.strip()
            if not a and not b:
                continue
            if not a:
                a = b
            if not b:
                b = a
            t1.append(a); t2.append(b); pairs.append([a, b])
        QUOTES.append({
            'id': r.get('commentId') or r.get('commentTime') or '',
            'date': (r.get('commentDate') or '')[:10],
            'store': (r.get('storeName') or '').strip(),
            'ch': ch(r.get('platformTypeDesc')),
            'score': to_int(r.get('commentScore')),
            'text': dedupe_content(r.get('commentContent')),
            # 一级（badCommentTags 中 '-' 前部分）；仅驱动原因分布
            'tags1': t1,
            # 二级（badCommentTags 中 '-' 后部分，与 tags1 同序对齐）
            'tags2': t2,
            # 原始「一级-二级」整串，用于差评明细卡片 chip 展示
            'tags2full': raw2,
            # 一级-二级 配对（每条一次，用于各维度计数）
            'pairs': pairs,
            'replied': bool(r.get('replyTime')) or bool((r.get('replyContent') or '').strip()),
        })

    # 日指标：dailyCommentTrends（date × store × channel），无 reply 字段
    daily = d.get('dailyCommentTrends') or []
    DAILY = [{
        'date': (r.get('commentDate') or '')[:10],
        'store': (r.get('storeName') or '').strip(),
        'ch': ch(r.get('platformTypeDesc')),
        'total': r.get('commentCount') or 0,
        'pos': r.get('goodCommentCount') or 0,
        'neg': r.get('badCommentCount') or 0,
        # 回复率分母 = 差评数（周期级，无逐日回复数据；relig 仅用于聚合占位，回复率实际由 METRICS 计算）
        'relig': r.get('badCommentCount') or 0,
        'rep24': 0,
    } for r in daily]

    # 评分分布：commentScoreDistribution（store × channel × score，无 date，整周期汇总）
    SCORES = []
    for r in (d.get('commentScoreDistribution') or []):
        sc = to_int(r.get('commentScore'))
        if sc is None:
            continue
        SCORES.append({
            'date': None,
            'store': (r.get('storeName') or '').strip(),
            'ch': ch(r.get('platformTypeDesc')),
            'score': sc,
            'count': r.get('commentScoreCount') or 0,
        })

    # 本期/上期指标：reviewMetricSummary（store × channel，扁平 preXxx 字段）
    rm = d.get('reviewMetricSummary') or []
    METRICS = []
    for r in rm:
        METRICS.append({
            'store': (r.get('storeName') or '').strip(),
            'ch': ch(r.get('platformTypeDesc')),
            'cur': {
                'total': r.get('commentCount') or 0,
                'pos': r.get('goodCommentCount') or 0,
                'neg': r.get('badCommentCount') or 0,
                # 24h 回复率分母 = 差评数(badCommentCount)，与工具 replyWithin24HoursPer 口径一致
                'relig': r.get('badCommentCount') or 0,
                'rep24': r.get('replyWithin24Hours') or 0,
            },
            'prev': {
                'total': r.get('preCommentCount') or 0,
                'pos': r.get('preGoodCommentCount') or 0,
                'neg': r.get('preBadCommentCount') or 0,
                'relig': r.get('preBadCommentCount') or 0,
                'rep24': r.get('preReplyWithin24Hours') or 0,
            },
        })

    # 订单与实收：orderAndReceiptSummary（store × channel，无 date）
    # 注：无订单的门店×渠道组合可能返回 null，这里用 num() 兜成 0.0，
    # 保证口径自洽（null→0 表示「该组合本期无订单」）。
    BUSINESS = [{
        'store': (r.get('storeName') or '').strip(),
        'ch': ch(r.get('platformTypeDesc')),
        'curOrder': num(r.get('orderNum')),
        'curAmt': num(r.get('totalActualReceipt')),
        'prevOrder': num(r.get('preOrderNum')),
        'prevAmt': num(r.get('preTotalActualReceipt')),
    } for r in (d.get('orderAndReceiptSummary') or [])]

    # 维度并集（保证即使某门店/渠道无差评也出现在筛选器）
    stores = {(x.get('store') or '') for x in QUOTES if x.get('store')}
    stores |= {(r.get('storeName') or '').strip() for r in daily if r.get('storeName')}
    chans = {x.get('ch') for x in QUOTES if x.get('ch')}
    chans |= {ch(r.get('platformTypeDesc')) for r in daily if r.get('platformTypeDesc')}
    stores.discard('')
    chans.discard('')
    STORES = sorted(stores)
    CHANNELS = sorted(chans)

    # 统计周期：新接口无 period 字段，从 dailyCommentTrends 的 commentDate 推导；
    # 若日趋势为空则退化为 commentDetails 日期。注意 MCP 窗口左移 bug（见 data-contract.md）。
    dt_dates = sorted({(r.get('commentDate') or '')[:10]
                       for r in daily if r.get('commentDate')})
    if not dt_dates:
        dt_dates = sorted({(r.get('commentDate') or '')[:10]
                           for r in cd if r.get('commentDate')})
    DATES = dt_dates
    PERIOD = {
        'start': dt_dates[0] if dt_dates else None,
        'end': dt_dates[-1] if dt_dates else None,
        'prevStart': None, 'prevEnd': None,
        'through': dt_dates[-1] if dt_dates else None,
        'timeZone': 'Asia/Shanghai',
    }

    # 一级标签顺序（badCommentTags 中 '-' 前部分，按差评命中降序，"其他原因"强制末位）
    # 注意：与模板 aggTag1Count 一致，按「每条差评去重」计数（一条差评带多个同大类二级标签只计 1 次），
    # 使排序依据与柱状图高度/占比口径同源，避免「排序按出现次数、高度按去重」的不一致。
    cnt1 = {}
    for q in QUOTES:
        seen = set()
        for t in q['tags1']:
            if t not in seen:
                cnt1[t] = cnt1.get(t, 0) + 1
                seen.add(t)
    ordered1 = [t for t in sorted(cnt1, key=lambda x: (-cnt1[x], x)) if t != '其他原因']
    if '其他原因' in cnt1:
        ordered1.append('其他原因')
    TAG1ORDER = ordered1

    # 二级标签（badCommentTags 中 '-' 后部分），按「一级 → [二级降序]」聚合（两级下钻用）
    cnt2 = {}  # (一级,二级) -> 命中数
    for q in QUOTES:
        for a, b in q['pairs']:
            cnt2[(a, b)] = cnt2.get((a, b), 0) + 1
    TAG2MAP = {}
    for (a, b), c in cnt2.items():
        TAG2MAP.setdefault(a, {})[b] = TAG2MAP.get(a, {}).get(b, 0) + c
    for a in TAG2MAP:
        TAG2MAP[a] = [b for b, _ in sorted(TAG2MAP[a].items(), key=lambda kv: (-kv[1], kv[0]))]

    META = {
        'totalCount': len(QUOTES),
        'returnedCount': len(QUOTES),
        'truncated': False,  # 新接口无 200 条上限封装，QUOTES 即全量差评
    }

    return {
        'PERIOD': PERIOD, 'DATES': DATES, 'STORES': STORES, 'CHANNELS': CHANNELS,
        'DAILY': DAILY, 'SCORES': SCORES, 'QUOTES': QUOTES,
        'TAG1ORDER': TAG1ORDER, 'TAG2MAP': TAG2MAP, 'TAGCOLOR': TAGCOLOR,
        'METRICS': METRICS, 'BUSINESS': BUSINESS, 'META': META,
    }


def preflight(d):
    """坏数据/缺字段时提前失败，避免生成空壳 HTML（与 SKILL.md「结果处理·获取失败判定」呼应）。

    data.json 必须是经工具正常返回落盘的完整 JSON。新接口关键字段缺失或
    dailyCommentTrends 为空，说明上游获取已失败，不应继续硬生成报告。
    """
    if d.get('hasData') is False:
        raise RuntimeError('hasData=false：所选范围暂无评价数据，报告未生成（须停止分析，不编造报告）')
    missing = [k for k in ('dailyCommentTrends', 'reviewMetricSummary',
                           'commentScoreDistribution', 'commentDetails')
               if k not in d]
    if missing:
        raise RuntimeError('data.json 缺失关键字段，无法生成报告: ' + ', '.join(missing))
    if not isinstance(d.get('dailyCommentTrends'), list) or len(d['dailyCommentTrends']) == 0:
        raise RuntimeError('dailyCommentTrends 为空，无逐日趋势数据，无法生成报告')


def render(data_json_path, output_path, template_path):
    with open(data_json_path, encoding='utf-8') as f:
        d = json.load(f)
    preflight(d)
    rd = build_report_data(d)

    with open(template_path, encoding='utf-8') as f:
        tpl = f.read()

    payload = json.dumps(rd, ensure_ascii=False, separators=(',', ':'))
    # 用 lambda 做替换，避免 payload 中的反斜杠被当作正则转义
    new_tpl, n = re.subn(r'/\*__DATA__\*/\s*\{\}', lambda m: payload, tpl, count=1)
    if n == 0:
        raise RuntimeError('模板中未找到 /*__DATA__*/{} 标记，无法注入')

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(new_tpl)

    # 轻量校验：标记已替换 + 注入 JSON 可解析
    assert '/*__DATA__*/' not in new_tpl, '注入失败：标记残留'
    m = re.search(r'const REPORT_DATA = (\{.*\})\s*;', new_tpl)
    if not m:
        raise RuntimeError('注入后未找到 REPORT_DATA 定义')
    json.loads(m.group(1))

    print('OK ->', output_path)
    print('  日期', len(rd['DATES']), '天 | 门店', len(rd['STORES']),
          '家 | 渠道', len(rd['CHANNELS']), '个 | 差评', len(rd['QUOTES']), '条')
    print('  一级标签顺序', rd['TAG1ORDER'])
    print('  二级标签（一级 %d 类 / 二级 %d 种）' % (len(rd['TAG1ORDER']), sum(len(v) for v in rd['TAG2MAP'].values())),
          '| 明细', rd['META']['returnedCount'], '/', rd['META']['totalCount'])


def main():
    if len(sys.argv) < 3:
        print('用法: python gen_report.py <data.json> <output.html> [template.html]')
        sys.exit(1)
    data_json_path = sys.argv[1]
    output_path = sys.argv[2]
    if len(sys.argv) >= 4:
        template_path = sys.argv[3]
    else:
        template_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            '..', 'references', 'interactive-report-template.html')
    render(data_json_path, output_path, template_path)


if __name__ == '__main__':
    main()
