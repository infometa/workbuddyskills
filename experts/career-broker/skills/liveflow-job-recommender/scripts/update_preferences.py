#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
update_preferences.py — 推荐完后写偏好。

用法：
    python update_preferences.py --rtx <your-rtx> \
      --add '{"exclude_management":true,"preferred_locations":["深圳"]}' \
      --note "本次推荐后用户确认"
"""
import argparse, json
from datetime import datetime
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--rtx', required=True)
    ap.add_argument('--add', required=True, help='JSON：要追加/覆盖的偏好字段')
    ap.add_argument('--note', default='')
    ap.add_argument('--prefs-dir',
        default=str(Path('~/CodeBuddy/职业经纪人agent/skills/'
                         'liveflow-job-recommender/prefs').expanduser()))
    args = ap.parse_args()

    prefs_path = Path(args.prefs_dir) / f'{args.rtx}-prefs.json'
    prefs_path.parent.mkdir(parents=True, exist_ok=True)

    if prefs_path.exists():
        prefs = json.loads(prefs_path.read_text(encoding='utf-8'))
    else:
        prefs = {
            'rtx': args.rtx,
            'created_at': datetime.now().isoformat(timespec='seconds'),
            'current': {},
            'history': [],
        }

    add = json.loads(args.add)
    prefs['current'].update(add)
    prefs['updated_at'] = datetime.now().isoformat(timespec='seconds')
    prefs['history'].append({
        'at': datetime.now().isoformat(timespec='seconds'),
        'added_fields': list(add.keys()),
        'note': args.note,
    })

    prefs_path.write_text(json.dumps(prefs, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'ok': True, 'path': str(prefs_path), 'current': prefs['current']},
                     ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
