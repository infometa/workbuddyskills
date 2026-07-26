"""CLI: read a JSON spec file -> emit a PPTX."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

from .builder import build_from_spec, PresentationBuilder, _REGISTRY


def main(argv=None) -> int:
    p = argparse.ArgumentParser(
        prog="mckinsey-pptx",
        description="Build McKinsey-style PPTX decks from a JSON spec.",
    )
    p.add_argument("input", nargs="?",
                   help="Path to JSON file containing a list of slide specs.")
    p.add_argument("-o", "--output", default="output.pptx",
                   help="Where to write the .pptx (default: output.pptx).")
    p.add_argument("--list-types", action="store_true",
                   help="List available slide types and exit.")
    p.add_argument("--demo", action="store_true",
                   help="Build a demo deck covering all slide types.")
    p.add_argument("--section-marker", default=None,
                   help="Default section marker text for every slide.")
    args = p.parse_args(argv)

    if args.list_types:
        for k in sorted(set(_REGISTRY)):
            print(k)
        return 0

    if args.demo:
        from examples.demo import build as build_demo
        out = build_demo(args.output)
        print(f"wrote {out}")
        return 0

    if not args.input:
        p.error("input file required (or use --demo / --list-types)")

    data = json.loads(Path(args.input).read_text())
    if not isinstance(data, list):
        print("input JSON must be a list of slide-spec objects", file=sys.stderr)
        return 1
    out = build_from_spec(data, args.output,
                          default_section_marker=args.section_marker)
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
