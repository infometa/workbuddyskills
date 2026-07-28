#!/usr/bin/env python3
"""
从 Databrain 查询指定游戏的 opinion 类型竞品列表。
从环境变量 DATABRAIN_TOKEN 读取 token。

用法:
  python get_competitor_list.py "<unified_id>"
  例：python get_competitor_list.py "uef4312b08dde07820374dd57086ea2fb"

输出:
  第一行 OK 或 EMPTY，OK 时后续每行为一个竞品游戏的 entity_name。
  出错时打印到 stderr 并以 exit code 1 退出。
"""
import os
import sys
import json
import urllib.request
from pathlib import Path

# 加载 .env：环境变量 > plugin 根目录 > skill 目录 > 当前目录
script_dir = Path(__file__).resolve().parent
skill_dir = script_dir.parent
plugin_root = skill_dir.parent.parent
for p in [plugin_root / '.env', skill_dir / '.env', Path(os.getcwd()) / '.env']:
    if p.exists():
        for raw in p.read_text(encoding='utf-8').splitlines():
            line = raw.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip())

if len(sys.argv) < 2:
    print("Usage: get_competitor_list.py <unified_id>", file=sys.stderr)
    sys.exit(1)

token = os.environ.get('DATABRAIN_TOKEN', '')
unified_id = sys.argv[1]
host = os.environ.get('DATABRAIN_INTL_HOST', 'https://databrain.intlgame.com')
url = f'{host}/api/v1/opinion_pc/global/query'

sql = (
    'select competitor_type, competitor_unified_id, a.entity_name '
    'FROM `tencent-databrain-prod.common.unified_competitor`, '
    "UNNEST(SPLIT(competitor_unified_id, '|')) AS competitor_unified_id "
    'left join tencent-databrain-prod.common.app_detail a '
    'on competitor_unified_id = a.app_id '
    f"WHERE unified_id='{unified_id}' and competitor_type='opinion' "
    'order by competitor_type, competitor_unified_id'
)

req = urllib.request.Request(
    url,
    data=json.dumps({'sql': sql}).encode('utf-8'),
    headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {token}'},
    method='POST'
)
try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        content = resp.read().decode('utf-8')
    lines = [l for l in content.strip().splitlines() if l.strip()]
    if len(lines) <= 1:
        print('EMPTY')
    else:
        print('OK')
        for line in lines[1:]:
            print(line.split(',', 2)[-1].strip())
except Exception as e:
    print(f'ERROR: {e}', file=sys.stderr)
    sys.exit(1)
