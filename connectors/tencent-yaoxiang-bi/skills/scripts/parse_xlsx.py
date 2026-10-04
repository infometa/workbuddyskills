#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Robust xlsx parser using only Python stdlib (zipfile + xml.etree).
Standalone xlsx parser (kept independent
for this skill's self-contained workflow). Already-fixed:
  - .rels Target 前导斜杠 bug → normalize via lstrip('/') + normpath

Use when openpyxl raises `Fill() takes no arguments` or numpy/pandas
fails to import in the managed python venv (macOS Team ID signature issue).

Usage:
    python parse_xlsx.py /path/to/file.xlsx [/tmp/out.json]
Then read JSON: dict[sheet_name] -> list of rows, each row = list of cells.
"""
import zipfile, json, sys, posixpath
from xml.etree import ElementTree as ET

NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
RID = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'
T_NS = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t'


def col_to_idx(col):
    idx = 0
    for c in col:
        if c.isalpha():
            idx = idx * 26 + (ord(c.upper()) - 64)
    return idx - 1


def parse(path, out=None):
    z = zipfile.ZipFile(path)

    # shared strings
    ss = []
    try:
        root = ET.fromstring(z.read('xl/sharedStrings.xml'))
        for si in root.findall('m:si', NS):
            ss.append(''.join(t.text or '' for t in si.iter(T_NS)))
    except KeyError:
        pass

    # sheet name -> rId
    wb = ET.fromstring(z.read('xl/workbook.xml'))
    sheets = [(s.get('name'), s.get(RID)) for s in wb.find('m:sheets', NS).findall('m:sheet', NS)]

    # rId -> target
    rels = ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
    rid2t = {r.get('Id'): r.get('Target') for r in rels}

    def parse_sheet(target):
        # Targets in xl/_rels/workbook.xml.rels are relative to xl/ and may appear as:
        #   'worksheets/sheet1.xml', '/xl/worksheets/sheet1.xml', 'xl/worksheets/sheet1.xml',
        #   or '../worksheets/sheet1.xml'. Normalize them all to a package path.
        t = target.lstrip('/')
        if t.startswith('../'):
            t = posixpath.normpath(posixpath.join('xl', t))
        elif not t.startswith('xl/'):
            t = 'xl/' + t
        root = ET.fromstring(z.read(t))
        data = root.find('m:sheetData', NS)
        rows, maxc = [], 0
        for row in data.findall('m:row', NS):
            cells = {}
            for c in row.findall('m:c', NS):
                ref = c.get('r')
                col = ''.join(ch for ch in ref if ch.isalpha())
                ci = col_to_idx(col)
                t = c.get('t')
                v = c.find('m:v', NS)
                isel = c.find('m:is', NS)
                val = None
                if t == 's' and v is not None:
                    val = ss[int(v.text)]
                elif t == 'inlineStr' and isel is not None:
                    val = ''.join(x.text or '' for x in isel.iter(T_NS))
                elif v is not None:
                    val = v.text
                cells[ci] = val
                maxc = max(maxc, ci)
            rows.append(cells)
        return [[c.get(i) for i in range(maxc + 1)] for c in rows]

    result = {}
    for name, rid in sheets:
        grid = parse_sheet(rid2t[rid])
        grid = [r for r in grid if any(x not in (None, '') for x in r)]
        result[name] = grid

    if out:
        with open(out, 'w') as f:
            json.dump(result, f, ensure_ascii=False)
    return result


if __name__ == '__main__':
    path = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else '/tmp/xlsx_data.json'
    r = parse(path, out)
    print('saved to', out)
    for name in r:
        print(' -', name, len(r[name]), 'rows')
