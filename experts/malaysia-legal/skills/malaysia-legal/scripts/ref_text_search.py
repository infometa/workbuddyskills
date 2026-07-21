#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reference Text Search Tool for Malaysia Legal Compliance Skill

Searches across all .txt files in Reference_Texts/ directory using keywords or regex.
Returns matching lines with context, file name, and approximate page number.

Usage:
    python ref_text_search.py "CPI 2024"
    python ref_text_search.py "water tariff RM" --context 3
    python ref_text_search.py "minimum wage" --files mida_codb_2024.txt,bnm_emr_2025.txt
    python ref_text_search.py --regex "RM[0-9]+\\.[0-9]+/m"
    python ref_text_search.py --list-files

Output: JSON to stdout.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple

# Force UTF-8 output on Windows to avoid GBK encoding errors
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# Resolve Reference_Texts path relative to plugin root
SCRIPT_DIR = Path(__file__).resolve().parent
PLUGIN_ROOT = SCRIPT_DIR.parent.parent.parent  # scripts/ -> malaysia-ssm-database/ -> skills/ -> plugin root
REF_TEXTS_DIR = PLUGIN_ROOT / "Reference_Texts"

MAX_MATCHES_PER_FILE = 30
MAX_TOTAL_MATCHES = 100
CONTEXT_LINES = 2


def list_files():
    """List all .txt files with metadata."""
    if not REF_TEXTS_DIR.exists():
        return {"error": f"Reference_Texts directory not found: {REF_TEXTS_DIR}"}
    
    files = []
    for f in sorted(REF_TEXTS_DIR.glob("*.txt")):
        size = f.stat().st_size
        files.append({
            "filename": f.name,
            "size_bytes": size,
            "size_mb": round(size / 1024 / 1024, 2)
        })
    return {"directory": str(REF_TEXTS_DIR), "file_count": len(files), "files": files}


def estimate_page_number(line_text: str, all_lines_before: int, total_lines: int, meta_pages: int = None) -> int:
    """Estimate page number based on PAGE BREAK markers or line ratio."""
    # Look for page break markers in the line
    if "--- PAGE BREAK ---" in line_text or "--- PAGE" in line_text:
        # This is a page break line itself
        return -1
    
    # If we have meta info about page count, estimate by ratio
    if meta_pages and total_lines > 0:
        return max(1, int((all_lines_before / total_lines) * meta_pages))
    
    return -1  # unknown


def search_keyword(keyword: str, context_lines: int = CONTEXT_LINES, file_filter: List[str] = None) -> Dict:
    """Search for a keyword across all .txt files."""
    if not REF_TEXTS_DIR.exists():
        return {"error": f"Reference_Texts directory not found: {REF_TEXTS_DIR}"}
    
    kw_lower = keyword.lower()
    results = []
    total_matches = 0
    
    txt_files = sorted(REF_TEXTS_DIR.glob("*.txt"))
    
    for txt_file in txt_files:
        if file_filter and txt_file.name not in file_filter:
            continue
        
        try:
            with open(txt_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except Exception as e:
            continue
        
        file_matches = []
        current_page = 1
        
        for i, line in enumerate(lines):
            # Track page breaks
            if "--- PAGE BREAK ---" in line or "--- PAGE" in line:
                current_page += 1
                continue
            
            if kw_lower in line.lower():
                # Get context
                start = max(0, i - context_lines)
                end = min(len(lines), i + context_lines + 1)
                context = []
                for j in range(start, end):
                    prefix = ">>>" if j == i else "   "
                    context.append(f"{prefix} L{j+1}: {lines[j].rstrip()}")
                
                file_matches.append({
                    "line_number": i + 1,
                    "estimated_page": current_page,
                    "match": line.strip()[:500],
                    "context": "\n".join(context)
                })
                
                total_matches += 1
                if len(file_matches) >= MAX_MATCHES_PER_FILE:
                    break
        
        if file_matches:
            results.append({
                "filename": txt_file.name,
                "match_count": len(file_matches),
                "matches": file_matches
            })
        
        if total_matches >= MAX_TOTAL_MATCHES:
            break
    
    return {
        "keyword": keyword,
        "total_matches": total_matches,
        "files_searched": len(txt_files) if not file_filter else len(file_filter),
        "files_with_matches": len(results),
        "truncated": total_matches >= MAX_TOTAL_MATCHES,
        "results": results
    }


def search_regex(pattern: str, context_lines: int = CONTEXT_LINES, file_filter: List[str] = None) -> Dict:
    """Search using regex pattern across all .txt files."""
    if not REF_TEXTS_DIR.exists():
        return {"error": f"Reference_Texts directory not found: {REF_TEXTS_DIR}"}
    
    try:
        regex = re.compile(pattern, re.IGNORECASE)
    except re.error as e:
        return {"error": f"Invalid regex: {e}"}
    
    results = []
    total_matches = 0
    
    txt_files = sorted(REF_TEXTS_DIR.glob("*.txt"))
    
    for txt_file in txt_files:
        if file_filter and txt_file.name not in file_filter:
            continue
        
        try:
            with open(txt_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except:
            continue
        
        file_matches = []
        current_page = 1
        
        for i, line in enumerate(lines):
            if "--- PAGE BREAK ---" in line or "--- PAGE" in line:
                current_page += 1
                continue
            
            if regex.search(line):
                start = max(0, i - context_lines)
                end = min(len(lines), i + context_lines + 1)
                context = []
                for j in range(start, end):
                    prefix = ">>>" if j == i else "   "
                    context.append(f"{prefix} L{j+1}: {lines[j].rstrip()}")
                
                file_matches.append({
                    "line_number": i + 1,
                    "estimated_page": current_page,
                    "match": line.strip()[:500],
                    "context": "\n".join(context)
                })
                
                total_matches += 1
                if len(file_matches) >= MAX_MATCHES_PER_FILE:
                    break
        
        if file_matches:
            results.append({
                "filename": txt_file.name,
                "match_count": len(file_matches),
                "matches": file_matches
            })
        
        if total_matches >= MAX_TOTAL_MATCHES:
            break
    
    return {
        "regex": pattern,
        "total_matches": total_matches,
        "files_searched": len(txt_files) if not file_filter else len(file_filter),
        "files_with_matches": len(results),
        "truncated": total_matches >= MAX_TOTAL_MATCHES,
        "results": results
    }


def main():
    global REF_TEXTS_DIR
    parser = argparse.ArgumentParser(description="Reference Text Search Tool")
    parser.add_argument("keyword", type=str, nargs="?", help="Keyword to search (case-insensitive)")
    parser.add_argument("--regex", type=str, help="Regex pattern to search")
    parser.add_argument("--context", type=int, default=CONTEXT_LINES, help=f"Context lines around match (default: {CONTEXT_LINES})")
    parser.add_argument("--files", type=str, help="Comma-separated list of files to search (default: all)")
    parser.add_argument("--list-files", action="store_true", help="List all .txt files with sizes")
    parser.add_argument("--ref-dir", type=str, default=str(REF_TEXTS_DIR), help="Path to Reference_Texts directory")
    
    args = parser.parse_args()
    
    # Override directory if provided
    if args.ref_dir:
        REF_TEXTS_DIR = Path(args.ref_dir)
    
    file_filter = None
    if args.files:
        file_filter = [f.strip() for f in args.files.split(",")]
    
    if args.list_files:
        result = list_files()
    elif args.regex:
        result = search_regex(args.regex, args.context, file_filter)
    elif args.keyword:
        result = search_keyword(args.keyword, args.context, file_filter)
    else:
        result = {"error": "No search term provided. Use --help for usage."}
    
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
