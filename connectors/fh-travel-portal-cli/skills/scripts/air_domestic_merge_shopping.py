# -*- coding: utf-8 -*-
"""合并多次 domestic_shopping 结果为单一载荷，供 air_domestic_oneway_render_page.py 出页。

人工排障可选工具，不是 Agent 默认路径。各段 serialNumber 写入 item['_sn']，
避免页面预订标识跨查询混用。

用法: python air_domestic_merge_shopping.py <out.json> <src1.json> [src2.json ...]
"""
import json
import re
import sys


def peel(data):
    stack = [data]
    seen = 0
    while stack and seen < 50:
        cur = stack.pop(0)
        seen += 1
        if isinstance(cur, dict):
            if isinstance(cur.get('flightList'), list):
                return cur
            for v in cur.values():
                stack.append(v)
        elif isinstance(cur, list):
            stack.extend(cur[:20])
        elif isinstance(cur, str) and cur.strip().startswith(('{', '[')):
            try:
                stack.append(json.loads(cur))
            except Exception:
                pass
    return None


def load(path):
    raw = open(path, encoding='utf-8').read().strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r'[\[{].*', raw, re.S)
        data = json.loads(m.group(0)) if m else None
    return peel(data)


def merge_dict_lists(base, extra, key):
    """按 key 去重合并且列表。"""
    out = list(base)
    seen = {str(d.get(key)) for d in base if isinstance(d, dict)}
    for d in extra:
        if isinstance(d, dict) and str(d.get(key)) not in seen:
            seen.add(str(d.get(key)))
            out.append(d)
    return out


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    out_path = sys.argv[1]
    merged = None
    total = 0
    # 按 (航班号, 起飞时刻) 去重：同一班可能同时出现在按航司拆分的两次查询里
    # （如 MU8201 共享 KN5977）。同一实际承运的不同销售航班号不算重复，要保留。
    seen = set()
    for path in sys.argv[2:]:
        data = load(path)
        if not data:
            print('跳过(无 flightList): %s' % path, file=sys.stderr)
            continue
        sn = str(data.get('serialNumber') or '')
        fl = data.get('flightList') or []
        kept, dup = [], 0
        for item in fl:
            if not isinstance(item, dict):
                continue
            keys = [(str(s.get('flightId') or ''), str(s.get('flyDate') or ''))
                    for s in item.get('flight', []) if isinstance(s, dict)]
            if any(k in seen for k in keys):
                dup += 1
                continue
            seen.update(keys)
            item['_sn'] = sn
            kept.append(item)
        fl = kept
        if merged is None:
            merged = dict(data)
            merged['flightList'] = list(fl)
        else:
            merged['flightList'].extend(fl)
            for k in ('citys', 'airways', 'types', 'policyDescList',
                      'businessAirCabList', 'cityWeatherList', 'fcyList'):
                a, b = merged.get(k) or [], data.get(k) or []
                if isinstance(a, list) and isinstance(b, list):
                    key = {'citys': 'cityCode', 'airways': 'companyNo',
                           'types': 'type'}.get(k, 'id')
                    merged[k] = merge_dict_lists(a, b, key)
        total += len(fl)
        print('%s: %d 班(去重 -%d) sn=%s' % (path, len(fl), dup, sn), file=sys.stderr)

    if merged is None:
        print('无有效输入', file=sys.stderr)
        return 1
    merged['mcpMergedFrom'] = len(sys.argv) - 2
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(merged, f, ensure_ascii=False)
    print('合并完成: %d 班 -> %s' % (total, out_path), file=sys.stderr)
    return 0


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    raise SystemExit(main())
