#!/usr/bin/env python3
"""Verify the package SHA-256 manifest against the current package tree."""
from pathlib import Path
import argparse, hashlib, json
from common import EXCLUDED_NAMES, EXCLUDED_PARTS, EXCLUDED_SUFFIXES

def package_files(root: Path):
    for path in sorted(root.rglob("*")):
        if not path.is_file(): continue
        rel = path.relative_to(root)
        if path.name in EXCLUDED_NAMES or path.name == "FILE-MANIFEST.sha256.json" or path.suffix.lower() in EXCLUDED_SUFFIXES: continue
        if any(part in EXCLUDED_PARTS or (part.startswith(".") and part != ".codebuddy-plugin") for part in rel.parts): continue
        yield path, rel.as_posix()

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("package_dir"); ap.add_argument("--manifest", default="FILE-MANIFEST.sha256.json"); args = ap.parse_args()
    root = Path(args.package_dir).expanduser().resolve(); manifest_path = root / args.manifest
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    actual = {rel: hashlib.sha256(path.read_bytes()).hexdigest() for path, rel in package_files(root)}
    expected = manifest.get("files", {})
    missing = sorted(set(expected) - set(actual)); extra = sorted(set(actual) - set(expected)); changed = sorted(k for k in set(actual) & set(expected) if actual[k] != expected[k])
    if missing or extra or changed:
        print(f"manifest mismatch: missing={missing}, extra={extra}, changed={changed}"); raise SystemExit(1)
    print(f"manifest ok: {len(actual)} files")

if __name__ == "__main__": main()
