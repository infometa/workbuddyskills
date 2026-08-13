#!/usr/bin/env python3
"""工作台生成器：把诊断结论 JSON 渲染成自包含的可交互工作台 HTML。"""
import argparse
import json
import os
import sys


def main() -> int:
    p = argparse.ArgumentParser(description="Render a workbench HTML from diagnostic JSON.")
    p.add_argument("--template", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "template.html"))
    p.add_argument("--data", required=True, help="Path to JSON file, or inline JSON string starting with '{'")
    p.add_argument("--out", required=True, help="Output HTML path")
    args = p.parse_args()

    if args.data.lstrip().startswith("{"):
        data = json.loads(args.data)
    else:
        with open(args.data, encoding="utf-8") as f:
            data = json.load(f)

    with open(args.template, encoding="utf-8") as f:
        tpl = f.read()

    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    if "__WB_DATA__" not in tpl:
        print("ERROR: template missing __WB_DATA__ placeholder", file=sys.stderr)
        return 1
    html = tpl.replace("__WB_DATA__", payload)

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(html)
    print("OK: " + args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
