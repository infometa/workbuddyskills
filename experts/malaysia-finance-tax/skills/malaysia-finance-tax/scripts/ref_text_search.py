"""
Reference_Texts Search Engine for Malaysia Finance & Tax Expert
Searches .txt files in the Reference_Texts directory using keyword/regex.
Returns: file name, line number, context, estimated page number
"""
import os
import re
import json
import argparse
from pathlib import Path

REF_TEXTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'Reference_Texts'))

def find_txt_files():
    """Find all .txt files in Reference_Texts directory (excluding _meta.json)"""
    txt_files = []
    if not os.path.exists(REF_TEXTS_DIR):
        return txt_files
    for f in sorted(os.listdir(REF_TEXTS_DIR)):
        if f.endswith('.txt') and not f.endswith('_meta.txt'):
            txt_files.append(os.path.join(REF_TEXTS_DIR, f))
    return txt_files

def load_meta(txt_path):
    """Load _meta.json for a txt file if exists"""
    meta_path = txt_path.replace('.txt', '_meta.json')
    if os.path.exists(meta_path):
        with open(meta_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def search_keyword(keyword, case_insensitive=True, context_lines=3, file_filter=None):
    """Search keyword across all .txt files, return matches with context"""
    results = []
    pattern = re.compile(re.escape(keyword), re.IGNORECASE) if case_insensitive else re.compile(re.escape(keyword))
    
    files = find_txt_files()
    if not files:
        return {"error": f"Reference_Texts directory not found or empty: {REF_TEXTS_DIR}"}
    
    for filepath in files:
        filename = os.path.basename(filepath)
        
        # Apply file filter if specified
        if file_filter and file_filter.lower() not in filename.lower():
            continue
        
        meta = load_meta(filepath)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        file_matches = []
        for i, line in enumerate(lines):
            if pattern.search(line):
                start = max(0, i - context_lines)
                end = min(len(lines), i + context_lines + 1)
                
                context = []
                for j in range(start, end):
                    prefix = '>' if j == i else ' '
                    context.append(f"{prefix} L{j+1}: {lines[j].rstrip()}")
                
                file_matches.append({
                    "line": i + 1,
                    "estimated_page": i // 30 + 1,  # Rough estimate: ~30 lines per page
                    "text": line.strip(),
                    "context": "\n".join(context)
                })
        
        if file_matches:
            results.append({
                "file": filename,
                "title": meta.get('title', filename),
                "category": meta.get('category', ''),
                "size_kb": meta.get('size_kb', 0),
                "matches": len(file_matches),
                "list": file_matches
            })
    
    return results

def search_regex(regex_pattern, context_lines=3):
    """Search using regex pattern"""
    try:
        pattern = re.compile(regex_pattern)
    except re.error as e:
        return {"error": f"Invalid regex: {str(e)}"}
    
    results = []
    for filepath in find_txt_files():
        filename = os.path.basename(filepath)
        meta = load_meta(filepath)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        file_matches = []
        for i, line in enumerate(lines):
            if pattern.search(line):
                start = max(0, i - context_lines)
                end = min(len(lines), i + context_lines + 1)
                context_lines_raw = []
                for j in range(start, end):
                    prefix = '>' if j == i else ' '
                    context_lines_raw.append(f"{prefix} L{j+1}: {lines[j].rstrip()}")
                file_matches.append({
                    "line": i + 1,
                    "text": line.strip(),
                    "context": "\n".join(context_lines_raw)
                })
        
        if file_matches:
            results.append({
                "file": filename,
                "title": meta.get('title', filename),
                "category": meta.get('category', ''),
                "matches": len(file_matches),
                "list": file_matches
            })
    
    return results

def list_all_files():
    """List all Reference_Texts files with metadata"""
    files_info = []
    for filepath in find_txt_files():
        filename = os.path.basename(filepath)
        meta = load_meta(filepath)
        files_info.append({
            "file": filename,
            "title": meta.get('title', ''),
            "title_zh": meta.get('title_zh', ''),
            "category": meta.get('category', ''),
            "year": meta.get('year', ''),
            "chars": meta.get('chars', 0),
            "size_kb": meta.get('size_kb', 0)
        })
    return files_info

def main():
    parser = argparse.ArgumentParser(description='Malaysia Finance & Tax Reference_Texts Search Engine')
    parser.add_argument('--keyword', type=str, help='Keyword to search for')
    parser.add_argument('--regex', type=str, help='Regex pattern to search')
    parser.add_argument('--context', type=int, default=3, help='Lines of context around match')
    parser.add_argument('--file-filter', type=str, help='Filter: only search files containing this string in name')
    parser.add_argument('--list-files', action='store_true', help='List all Reference_Texts files with metadata')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    args = parser.parse_args()

    if args.list_files:
        info = list_all_files()
        if args.json:
            print(json.dumps(info, ensure_ascii=False, indent=2))
        else:
            print(f"\n{'='*60}")
            print(f"📚 Reference_Texts Files ({len(info)} total)")
            print(f"{'='*60}")
            for f in info:
                print(f"  📄 {f['file']}")
                print(f"     Title: {f['title_zh'] or f['title']}")
                print(f"     Category: {f['category']} | Size: {f['size_kb']} KB")
                print()
        return

    if args.keyword:
        results = search_keyword(args.keyword, context_lines=args.context, file_filter=args.file_filter)
    elif args.regex:
        results = search_regex(args.regex, context_lines=args.context)
    else:
        parser.print_help()
        return

    if isinstance(results, dict) and 'error' in results:
        print(json.dumps(results, ensure_ascii=False))
        return

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        total = sum(r['matches'] for r in results)
        print(f"\n{'='*60}")
        print(f"🔍 Found {total} matches in {len(results)} files")
        print(f"{'='*60}")
        for r in results:
            print(f"\n📄 {r['file']} ({r['category']}) - {r['matches']} matches")
            for m in r['list'][:5]:  # Show first 5 matches
                print(f"  L{m['line']}: {m['text'][:120]}")
            if len(r['list']) > 5:
                print(f"  ... and {len(r['list']) - 5} more matches")

if __name__ == '__main__':
    main()
