"""
Data Verifier - Anti-Hallucination Firewall for Malaysia Finance & Tax Expert
Verifies whether a specific data point exists in the corpus.
Returns: verified / not_found / partial / conflict
"""
try:
    import duckdb
except ImportError:
    import subprocess
    import sys
    print("duckdb not found, auto-installing...", file=sys.stderr)
    subprocess.check_call([sys.executable, "-m", "pip", "install", "duckdb", "--quiet"])
    import duckdb
import json
import os
import re
import argparse
import sys

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPTS_DIR)
DB_PATH = os.path.join(SKILL_DIR, 'datasets', 'malaysia_finance_tax.duckdb')
REF_TEXTS_DIR = os.path.abspath(os.path.join(SKILL_DIR, '..', '..', 'Reference_Texts'))

def verify_in_duckdb(fact_type, value, threshold=0.8):
    """
    Verify a fact against DuckDB database.
    fact_type: e.g. 'tax_rate', 'sst_rate', 'opr', 'forex'
    value: value to verify
    """
    if not os.path.exists(DB_PATH):
        return {"source": "duckdb", "status": "not_found", "reason": "Database not found"}
    
    con = duckdb.connect(DB_PATH)
    result = {"source": "duckdb", "status": "not_found", "matches": []}
    
    try:
        if fact_type == 'tax_rate':
            v = float(value)
            rows = con.execute("""
                SELECT category, entity_type, rate_pct, income_range_min, income_range_max, description
                FROM tax_rates WHERE ABS(rate_pct - ?) < 1.0
            """, [v]).fetchall()
            if rows:
                result["status"] = "verified"
                result["matches"] = [{"category": r[0], "entity": r[1], "rate": r[2], "range": f"{r[3]:,.0f}-{r[4]:,.0f}"} for r in rows]
        
        elif fact_type == 'sst_rate':
            v = float(value)
            rows = con.execute("""
                SELECT tax_type, category, rate_pct, description
                FROM sst_rates WHERE ABS(rate_pct - ?) < 1.0
            """, [v]).fetchall()
            if rows:
                result["status"] = "verified"
                result["matches"] = [{"type": r[0], "category": r[1], "rate": r[2], "desc": r[3]} for r in rows]
        
        elif fact_type == 'opr':
            v = float(value)
            rows = con.execute("""
                SELECT effective_date, opr_rate_pct, statement_summary
                FROM bnm_opr_history WHERE ABS(opr_rate_pct - ?) < 0.1
                ORDER BY effective_date DESC LIMIT 5
            """, [v]).fetchall()
            if rows:
                result["status"] = "verified"
                result["matches"] = [{"date": str(r[0]), "rate": r[1], "summary": r[2]} for r in rows]
        
        elif fact_type == 'forex':
            rows = con.execute("""
                SELECT currency_code, currency_name, rate_to_myr, date_recorded
                FROM forex_rates WHERE currency_code = ? OR currency_name ILIKE ?
            """, [value.upper(), f'%{value}%']).fetchall()
            if rows:
                result["status"] = "verified"
                result["matches"] = [{"currency": r[0], "name": r[1], "rate": r[2], "date": str(r[3])} for r in rows]
        
        elif fact_type == 'incentive':
            rows = con.execute("""
                SELECT incentive_name, type, benefit_rate_pct, duration_years, eligible_sectors
                FROM tax_incentives WHERE incentive_name ILIKE ? OR description ILIKE ?
            """, [f'%{value}%', f'%{value}%']).fetchall()
            if rows:
                result["status"] = "verified"
                result["matches"] = [{"name": r[0], "type": r[1], "rate": r[2], "duration": r[3], "sectors": r[4]} for r in rows]
        
        elif fact_type == 'deadline':
            rows = con.execute("""
                SELECT obligation, deadline_text, penalty, authority FROM compliance_deadlines
                WHERE obligation ILIKE ? OR description ILIKE ?
            """, [f'%{value}%', f'%{value}%']).fetchall()
            if rows:
                result["status"] = "verified"
                result["matches"] = [{"obligation": r[0], "deadline": r[1], "penalty": r[2], "authority": r[3]} for r in rows]
                
    except Exception as e:
        result["status"] = "error"
        result["reason"] = str(e)
    
    con.close()
    return result

def verify_in_ref_texts(fact, file_filter=None):
    """Verify a fact in Reference_Texts files"""
    if not os.path.exists(REF_TEXTS_DIR):
        return {"source": "ref_texts", "status": "not_found", "reason": "Reference_Texts directory not found"}
    
    result = {"source": "ref_texts", "status": "not_found", "matches": []}
    pattern = re.compile(re.escape(fact), re.IGNORECASE)
    
    for filename in sorted(os.listdir(REF_TEXTS_DIR)):
        if not filename.endswith('.txt') or filename.endswith('_meta.json'):
            continue
        if file_filter and file_filter.lower() not in filename.lower():
            continue
        
        filepath = os.path.join(REF_TEXTS_DIR, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        matches = list(pattern.finditer(content))
        if matches:
            result["status"] = "verified"
            result["matches"].append({
                "file": filename,
                "count": len(matches),
                "context_snippets": [content[max(0, m.start()-50):m.end()+50].replace('\n', ' ') for m in matches[:3]]
            })
    
    return result

def main():
    parser = argparse.ArgumentParser(description='Data Verifier - Anti-Hallucination Firewall')
    parser.add_argument('--fact-type', choices=['tax_rate', 'sst_rate', 'opr', 'forex', 'incentive', 'deadline', 'withholding', 'general'], 
                        default='general', help='Type of fact to verify')
    parser.add_argument('--value', type=str, required=True, help='Value to verify')
    parser.add_argument('--check-duckdb', action='store_true', help='Verify against DuckDB database')
    parser.add_argument('--check-texts', action='store_true', help='Verify against Reference_Texts')
    parser.add_argument('--file-filter', type=str, help='Filter Reference_Texts files by name')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    
    args = parser.parse_args()
    
    results = {"query": {"fact_type": args.fact_type, "value": args.value}}
    
    if args.check_duckdb:
        results["duckdb"] = verify_in_duckdb(args.fact_type, args.value)
    
    if args.check_texts:
        results["ref_texts"] = verify_in_ref_texts(args.value, args.file_filter)
    
    # Determine overall status
    verified_sources = []
    not_found_sources = []
    for k, v in results.items():
        if k == 'query':
            continue
        if v.get('status') == 'verified':
            verified_sources.append(k)
        elif v.get('status') == 'not_found':
            not_found_sources.append(k)
    
    if verified_sources and not not_found_sources:
        results["overall_status"] = "verified"
    elif verified_sources and not_found_sources:
        results["overall_status"] = "partial"
        results["warning"] = f"Found in {', '.join(verified_sources)}, but not confirmed in {', '.join(not_found_sources)}"
    else:
        results["overall_status"] = "not_found"
        results["warning"] = "This data point was NOT found in any local corpus source. Verify with official sources."
    
    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2, default=str))
    else:
        status_icon = {'verified': '✅', 'partial': '⚠️', 'not_found': '❌', 'error': '🔴'}
        icon = status_icon.get(results['overall_status'], '❓')
        print(f"\n{'='*50}")
        print(f"📊 Data Verification Result")
        print(f"{'='*50}")
        print(f"  Fact: {args.value} (type: {args.fact_type})")
        print(f"  Status: {icon} {results['overall_status'].upper()}")
        
        if 'warning' in results:
            print(f"  ⚠️  {results['warning']}")
        
        for source_type in ['duckdb', 'ref_texts']:
            if source_type in results:
                r = results[source_type]
                if r['status'] == 'verified':
                    print(f"\n  ✅ Verified in {source_type}: {len(r['matches'])} match(es)")
                    for m in r['matches'][:3]:
                        print(f"     • {json.dumps(m, ensure_ascii=False)[:150]}")

if __name__ == '__main__':
    main()
