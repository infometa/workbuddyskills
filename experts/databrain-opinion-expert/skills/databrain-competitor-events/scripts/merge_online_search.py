"""
merge_online_search.py
用法：python merge_online_search.py <timestamp> <cache_dir> <output_path>

将 cache_dir 下所有匹配 _online_search_*_{timestamp}.json 的文件合并，
并按 total_engagement 降序排列，写入 output_path。
"""
import json
import glob
import os
import sys


def main():
    if len(sys.argv) != 4:
        print("Usage: merge_online_search.py <timestamp> <cache_dir> <output_path>")
        sys.exit(1)

    timestamp, cache_dir, output_path = sys.argv[1], sys.argv[2], sys.argv[3]

    pattern = os.path.join(cache_dir, f"_online_search_*_{timestamp}.json")
    files = sorted(glob.glob(pattern))

    if not files:
        print(f"ERROR: no files matched pattern: {pattern}")
        sys.exit(1)

    all_events = []
    for fpath in files:
        with open(fpath, encoding="utf-8") as f:
            events = json.load(f)
        for ev in events:
            ev.setdefault("source_file", os.path.basename(fpath))
        all_events.extend(events)
        print(f"  loaded {len(events)} events from {os.path.basename(fpath)}")

    all_events.sort(key=lambda e: e.get("total_engagement", 0), reverse=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_events, f, ensure_ascii=False, indent=2)

    print(f"merged {len(files)} files, {len(all_events)} events → {output_path}")


if __name__ == "__main__":
    main()
