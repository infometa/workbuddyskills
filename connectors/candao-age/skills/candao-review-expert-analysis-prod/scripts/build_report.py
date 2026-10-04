#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""餐道口碑报告：一步生成 + 校验（纯 Python，无计时）。

封装 scripts/gen_report.py（生成 + 轻量校验），再补一层结构化校验：
  - 解析注入模板的 REPORT_DATA，报告 dates / stores / channels / 差评条数；
  - 扫描危险 token 的「值形态」（NaN / undefined / Infinity / %%），排除 isNaN() 函数名。
生成或校验失败即非零退出，方便 agent 一次调用、一步交付 HTML。

用法：
    python build_report.py <data.json> <output.html> [template.html]
若省略 template.html，默认使用脚本同目录 ../references/interactive-report-template.html。
"""

import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GEN = os.path.join(HERE, 'gen_report.py')


def validate_html(path):
    """解析 REPORT_DATA 并扫描危险 token（值形态，非函数名）。"""
    with open(path, encoding='utf-8') as f:
        s = f.read()

    # REPORT_DATA 为单行 JSON：取 const REPORT_DATA = 之后到行尾，首个 { 到最后一个 }
    idx = s.find('const REPORT_DATA = ')
    if idx < 0:
        raise RuntimeError('HTML 中未找到 REPORT_DATA 定义')
    line = s[idx:].split('\n', 1)[0]
    bi = line.find('{')
    if bi < 0:
        raise RuntimeError('REPORT_DATA 行未找到 {')
    ei = line.rfind('}')
    if ei < 0 or ei < bi:
        raise RuntimeError('REPORT_DATA 行未找到闭合 }')
    rd = json.loads(line[bi:ei + 1])

    bad = []
    for tok in ('undefined', 'Infinity', '%%'):
        if tok in s:
            bad.append(tok)
    # NaN 仅认「值形态」：:NaN / NaN, / (NaN) / 'NaN' / "NaN" / 运算符后 NaN；
    # 排除 isNaN( 函数调用（模板合法数据校验写法，非真实 NaN 值）
    if re.search(r':NaN|NaN,|\(NaN\)|\'NaN\'|"NaN"|(?<=[= (])NaN', s):
        bad.append('NaN')

    print('  校验: dates=%d stores=%d channels=%d 差评=%d 危险token=%s'
          % (len(rd.get('DATES', [])), len(rd.get('STORES', [])),
             len(rd.get('CHANNELS', [])), len(rd.get('QUOTES', [])),
             'none' if not bad else ','.join(bad)))
    if bad:
        raise RuntimeError('HTML 含危险 token: ' + ','.join(bad))


def main():
    if len(sys.argv) < 3:
        print('用法: python build_report.py <data.json> <output.html> [template.html]')
        sys.exit(1)
    data_path, out_path = sys.argv[1], sys.argv[2]
    tpl = sys.argv[3] if len(sys.argv) >= 4 else None

    # 1) 生成（gen_report.py 内含轻量校验，失败即抛错退出）
    gen = [sys.executable, GEN, data_path, out_path]
    if tpl:
        gen.append(tpl)
    r = subprocess.run(gen)
    if r.returncode != 0:
        print('[build] gen_report.py 失败，终止', file=sys.stderr)
        sys.exit(r.returncode)

    # 2) 结构化校验（无计时）
    validate_html(out_path)
    print('[build] 完成 ->', out_path)


if __name__ == '__main__':
    main()
