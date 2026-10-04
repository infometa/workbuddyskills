#!/usr/bin/env python3
"""Fast local parser for listing batch attachments.

The script accepts a host-provided local path or file URI and returns a compact JSON summary. It intentionally samples rows instead of
dumping whole files into the agent context.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
import urllib.parse
import zipfile


ASIN_RE = re.compile(r"\b[A-Z0-9]{10}\b", re.I)
SUPPORTED_EXTS = {".csv", ".tsv", ".txt", ".xlsx", ".xls", ".json", ".md", ".html", ".htm"}
MAX_ZIP_MEMBER_BYTES = 20 * 1024 * 1024


def resolve_input(source: str, _work_dir: Path) -> Path:
    if source.startswith("file://"):
      source = urllib.parse.urlparse(source).path
    parsed = urllib.parse.urlparse(source)
    if parsed.scheme and parsed.scheme != "file":
        raise ValueError("only local paths and file:// URIs are supported")
    path = Path(source).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"attachment file does not exist: {path}")
    return path


def _read_text(path: Path, limit_bytes: int = 512 * 1024) -> str:
    data = path.read_bytes()[:limit_bytes]
    for encoding in ("utf-8-sig", "utf-8", "gb18030", "latin-1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def _row_limit(max_rows: int, all_rows: bool) -> int | None:
    return None if all_rows else max_rows


def parse_delimited(path: Path, max_rows: int, all_rows: bool = False) -> dict:
    text = _read_text(path)
    delimiter = "\t" if path.suffix.lower() == ".tsv" else ","
    sample = text.splitlines()
    if path.suffix.lower() == ".txt":
        rows = [[line.strip()] for line in sample if line.strip()]
    else:
        rows = list(csv.reader(sample, delimiter=delimiter))
    rows = [row for row in rows if any(str(cell).strip() for cell in row)]
    headers = [str(cell).strip() for cell in rows[0]] if rows else []
    limit = _row_limit(max_rows, all_rows)
    data_rows = rows[1:] if headers else rows
    body = data_rows if limit is None else data_rows[:limit]
    asins = []
    for row in body:
        asins.extend(ASIN_RE.findall(" ".join(str(cell) for cell in row)))
    return {
        "type": "table" if path.suffix.lower() != ".txt" else "text",
        "file": str(path),
        "headers": headers,
        "sampleRows": body,
        "rowCountSampled": len(body),
        "rowCountTotal": len(data_rows),
        "asinCandidates": sorted(set(asin.upper() for asin in asins)),
        "truncated": False if limit is None else len(data_rows) > limit,
    }


def parse_xlsx(path: Path, max_rows: int, all_rows: bool = False) -> dict:
    try:
        import openpyxl  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on runtime packages
        raise RuntimeError("openpyxl is required to parse xlsx attachments") from exc
    workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
    sheet = workbook[workbook.sheetnames[0]]
    rows = []
    limit = _row_limit(max_rows, all_rows)
    for row in sheet.iter_rows(values_only=True):
        values = ["" if cell is None else str(cell).strip() for cell in row]
        if any(values):
            rows.append(values)
        if limit is not None and len(rows) > limit + 1:
            break
    headers = rows[0] if rows else []
    body = rows[1:] if limit is None else rows[1: limit + 1] if headers else []
    asins = []
    for row in body:
        asins.extend(ASIN_RE.findall(" ".join(row)))
    return {
        "type": "spreadsheet",
        "file": str(path),
        "sheet": sheet.title,
        "headers": headers,
        "sampleRows": body,
        "rowCountSampled": len(body),
        "rowCountTotal": max((sheet.max_row or 1) - 1, 0) if headers else len(body),
        "asinCandidates": sorted(set(asin.upper() for asin in asins)),
        "truncated": False if limit is None else len(rows) > limit + 1,
    }


def parse_text_like(path: Path, max_rows: int, all_rows: bool = False) -> dict:
    text = _read_text(path)
    if path.suffix.lower() in {".html", ".htm"}:
        text = re.sub(r"<[^>]+>", " ", text)
        text = html.unescape(text)
    source_lines = [line.strip() for line in text.splitlines() if line.strip()]
    lines = source_lines if all_rows else source_lines[:max_rows]
    asins = ASIN_RE.findall("\n".join(lines))
    return {
        "type": "text",
        "file": str(path),
        "lines": lines,
        "rowCountTotal": len(source_lines),
        "asinCandidates": sorted(set(asin.upper() for asin in asins)),
        "truncated": False if all_rows else len(source_lines) > max_rows,
    }


def parse_file(path: Path, max_rows: int, all_rows: bool = False) -> dict:
    suffix = path.suffix.lower()
    if suffix in {".csv", ".tsv", ".txt"}:
        return parse_delimited(path, max_rows, all_rows)
    if suffix == ".xlsx":
        return parse_xlsx(path, max_rows, all_rows)
    if suffix == ".xls":
        raise ValueError("legacy .xls is not supported; save the attachment as .xlsx before processing")
    if suffix in {".json", ".md", ".html", ".htm"}:
        return parse_text_like(path, max_rows, all_rows)
    raise ValueError(f"unsupported attachment type: {suffix or path.name}")


def should_skip_zip_member(info: zipfile.ZipInfo) -> tuple[bool, str | None]:
    name = info.filename
    parts = Path(name).parts
    if info.is_dir():
        return True, "directory"
    if "__MACOSX" in parts or any(part.startswith(".") for part in parts):
        return True, "hidden_or_macosx"
    if info.file_size > MAX_ZIP_MEMBER_BYTES:
        return True, "too_large"
    if Path(name).suffix.lower() not in SUPPORTED_EXTS:
        return True, "unsupported_type"
    return False, None


def parse_zip(path: Path, max_files: int, max_rows: int, work_dir: Path, all_rows: bool = False) -> dict:
    parsed = []
    skipped = []
    extract_dir = work_dir / f"zip-{path.stem}"
    extract_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path) as archive:
        for info in archive.infolist():
            skip, reason = should_skip_zip_member(info)
            if skip:
                skipped.append({"name": info.filename, "reason": reason})
                continue
            if len(parsed) >= max_files:
                skipped.append({"name": info.filename, "reason": "max_files_reached"})
                continue
            target = extract_dir / Path(info.filename).name
            with archive.open(info) as src, target.open("wb") as dst:
                shutil.copyfileobj(src, dst)
            try:
                parsed.append(parse_file(target, max_rows, all_rows))
            except Exception as exc:
                skipped.append({"name": info.filename, "reason": f"parse_failed: {exc}"})
    return {
        "type": "zip",
        "file": str(path),
        "parsedFileCount": len(parsed),
        "skippedFileCount": len(skipped),
        "parsed": parsed,
        "skipped": skipped[:50],
        "truncated": any(item.get("reason") == "max_files_reached" for item in skipped),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", help="ACP resource_link uri, local file path, or HTTP(S) URL")
    parser.add_argument("--max-files", type=int, default=20)
    parser.add_argument("--max-rows", type=int, default=20)
    parser.add_argument("--all-rows", action="store_true", help="Parse all rows instead of sampling max-rows")
    parser.add_argument("--out", help="Optional JSON output path")
    args = parser.parse_args()

    work_dir = Path(tempfile.mkdtemp(prefix="listing-attachment-"))
    try:
        path = resolve_input(args.source, work_dir)
        result = parse_zip(path, args.max_files, args.max_rows, work_dir, args.all_rows) if path.suffix.lower() == ".zip" else parse_file(path, args.max_rows, args.all_rows)
        payload = json.dumps(result, ensure_ascii=False, indent=2)
        if args.out:
            out = Path(args.out).expanduser()
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(payload, encoding="utf-8")
            print(f"Attachment summary: {out}")
        else:
            print(payload)
        return 0
    except Exception as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
