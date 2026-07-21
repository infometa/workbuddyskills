#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Data Verifier Tool for Malaysia Legal Compliance Skill

Given a data point (e.g., "minimum wage", "1700", "2026"), this tool searches both DuckDB
and Reference_Texts to verify whether the number/legal fact exists in the local corpus.
This is the anti-hallucination firewall: if a number is NOT found in the corpus,
the agent must NOT output it as fact.

Usage:
    python data_verifier.py --metric "CPI" --value "133" --year "2024"
    python data_verifier.py --metric "minimum wage" --value "1500"
    python data_verifier.py --metric "GDP growth" --value "5.1" --year "2024"
    python data_verifier.py --metric "water tariff" --value "1.57"

Output: JSON with verdict: verified / not_found / partial / conflict
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Force UTF-8 output on Windows to avoid GBK encoding errors
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# Resolve paths
SCRIPT_DIR = Path(__file__).resolve().parent
PLUGIN_ROOT = SCRIPT_DIR.parent.parent.parent
DB_PATH = PLUGIN_ROOT / "Databases" / "malaysia.duckdb"
REF_TEXTS_DIR = PLUGIN_ROOT / "Reference_Texts"
PYTHON_EXE = sys.executable

# Sibling scripts
DUCKDB_SCRIPT = SCRIPT_DIR / "duckdb_query.py"
REF_SEARCH_SCRIPT = SCRIPT_DIR / "ref_text_search.py"


def run_script(script_path: str, args: List[str]) -> Dict:
    """Run a sibling Python script and return parsed JSON output."""
    try:
        cmd = [PYTHON_EXE, str(script_path)] + args
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60, encoding="utf-8")
        if result.returncode != 0:
            return {"error": result.stderr[:500]}
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return {"error": "Failed to parse JSON output", "raw": result.stdout[:500]}
    except subprocess.TimeoutExpired:
        return {"error": "Script timed out"}
    except Exception as e:
        return {"error": str(e)}


def search_duckdb_for_metric(metric: str, value: str, year: str = None) -> Dict:
    """Search DuckDB for a metric+value combination."""
    # Step 1: Find relevant tables by keyword
    search_result = run_script(str(DUCKDB_SCRIPT), ["--search", metric])
    
    if "error" in search_result:
        return {"source": "duckdb", "verdict": "error", "detail": search_result["error"]}
    
    matches = search_result.get("matches", [])
    if not matches:
        return {"source": "duckdb", "verdict": "not_found", "detail": f"No tables matched keyword: {metric}"}
    
    # Step 2: For top matches, query the data and look for the value
    findings = []
    for m in matches[:10]:  # check top 10 table matches
        table = m["table"]
        # Get schema to understand columns
        schema_result = run_script(str(DUCKDB_SCRIPT), ["--schema", table])
        if "error" in schema_result:
            continue
        
        columns = schema_result.get("columns", [])
        col_names = [c["name"] for c in columns]
        
        # Try to find year column and value column
        year_col = None
        for candidate in ["year", "date", "period", "quarter", "month"]:
            if candidate in [c.lower() for c in col_names]:
                year_col = candidate
                break
        
        # Build query - check both first 20 and last 20 rows (latest data)
        queries = []
        if year and year_col:
            queries.append(f"SELECT * FROM \"{table}\" WHERE CAST({year_col} AS VARCHAR) LIKE '%{year}%' LIMIT 50")
        else:
            # Check first 20 + last 20 (latest data is usually at the end)
            queries.append(f"SELECT * FROM \"{table}\" LIMIT 20")
            if year_col:
                queries.append(f"SELECT * FROM \"{table}\" ORDER BY {year_col} DESC LIMIT 20")
        
        rows = []
        for sql in queries:
            query_result = run_script(str(DUCKDB_SCRIPT), ["--sql", sql])
            if "error" not in query_result:
                rows.extend(query_result.get("rows", []))
        if not rows:
            continue
        
        # Check if any cell contains the value
        value_str = str(value).strip()
        # Normalize: also try with comma formatting (e.g., "1700" -> "1,700")
        value_variants = {value_str}
        if value_str.replace(".", "").isdigit():
            # Add comma-formatted version (e.g., 1700 -> 1,700)
            try:
                num = int(float(value_str))
                value_variants.add(f"{num:,}")
                # Also try with RM prefix
                value_variants.add(f"RM{num:,}")
                value_variants.add(f"RM{num}")
            except:
                pass
        
        # Identify numeric columns (skip ID/code columns like 'subclass', 'msic', 'sitc', etc.)
        skip_cols = {"subclass", "msic", "sitc", "mcoicop", "bec", "code", "id", "sector", 
                      "section", "division", "group", "class", "state", "district", 
                      "dun", "parliament", "sex", "ethnic", "nationality", "country",
                      "region", "area", "name", "description", "type", "category",
                      "level", "strata", "urban", "rural", "item", "product", "commodity",
                      "frequency", "period", "quarter", "month", "unit", "flag", "remark"}
        numeric_col_names = set()
        for col in columns:
            col_lower = col["name"].lower()
            col_type = col.get("type", "").upper()
            # Check if it's a numeric type and not a code column
            if any(t in col_type for t in ["DOUBLE", "FLOAT", "DECIMAL", "REAL", "BIGINT", "INTEGER", "INT"]):
                if col_lower not in skip_cols and "code" not in col_lower and "id" not in col_lower:
                    numeric_col_names.add(col["name"])
            # Also consider columns named 'index', 'value', 'amount', 'rate', 'price', etc.
            if col_lower in ("index", "value", "amount", "rate", "price", "wage", "salary", 
                             "cost", "revenue", "expenditure", "income", "gdp", "volume",
                             "growth", "change", "percentage", "share", "ratio"):
                numeric_col_names.add(col["name"])
        
        value_found = False
        matching_rows = []
        
        for row in rows:
            # Only check numeric columns, skip ID/code columns
            for k, v in row.items():
                if k.lower() in skip_cols or "code" in k.lower() or "id" in k.lower():
                    continue
                v_str = str(v).strip() if v is not None else ""
                # For numeric columns, do exact match
                if k in numeric_col_names:
                    try:
                        # Compare as floats
                        if float(v_str) == float(value_str):
                            value_found = True
                            matching_rows.append(row)
                            break
                    except (ValueError, TypeError):
                        pass
                else:
                    # For non-numeric, non-code columns, check if value appears
                    for variant in value_variants:
                        if v_str == variant:
                            value_found = True
                            matching_rows.append(row)
                            break
                if value_found:
                    break
        
        if value_found:
            findings.append({
                "table": table,
                "matched_rows": matching_rows[:5],
                "total_rows_checked": len(rows)
            })
    
    if findings:
        return {
            "source": "duckdb",
            "verdict": "verified",
            "detail": f"Value '{value}' found in {len(findings)} table(s)",
            "findings": findings
        }
    else:
        return {
            "source": "duckdb",
            "verdict": "not_found",
            "detail": f"Value '{value}' not found in sampled rows of {len(matches)} matching table(s)",
            "tables_checked": [m["table"] for m in matches[:10]]
        }


def search_ref_texts_for_metric(metric: str, value: str) -> Dict:
    """Search Reference_Texts for a metric+value combination."""
    # Search for the metric keyword first
    search_result = run_script(str(REF_SEARCH_SCRIPT), [metric, "--context", "3"])
    
    if "error" in search_result:
        return {"source": "reference_texts", "verdict": "error", "detail": search_result["error"]}
    
    total_matches = search_result.get("total_matches", 0)
    if total_matches == 0:
        return {"source": "reference_texts", "verdict": "not_found", "detail": f"No matches for keyword: {metric}"}
    
    # Now check if the value appears near the metric
    results = search_result.get("results", [])
    value_str = str(value).strip()
    # Normalize: also try with comma formatting (e.g., "1700" -> "1,700")
    value_variants = {value_str}
    if value_str.replace(".", "").isdigit():
        try:
            num = int(float(value_str))
            value_variants.add(f"{num:,}")
            value_variants.add(f"RM{num:,}")
            value_variants.add(f"RM{num}")
            value_variants.add(f"RM {num:,}")
            value_variants.add(f"RM {num}")
        except:
            pass
    verified_matches = []
    
    for file_result in results:
        filename = file_result["filename"]
        for match in file_result.get("matches", []):
            context = match.get("context", "")
            match_text = match.get("match", "")
            combined = context + " " + match_text
            
            # Check if any value variant appears in the context
            found = False
            for variant in value_variants:
                if variant in combined:
                    found = True
                    break
            
            if found:
                verified_matches.append({
                    "filename": filename,
                    "line_number": match["line_number"],
                    "estimated_page": match.get("estimated_page", -1),
                    "match": match_text[:300],
                    "context": context[:500]
                })
    
    if verified_matches:
        return {
            "source": "reference_texts",
            "verdict": "verified",
            "detail": f"Value '{value}' found alongside metric '{metric}' in {len(verified_matches)} location(s)",
            "findings": verified_matches[:10]
        }
    else:
        return {
            "source": "reference_texts",
            "verdict": "partial",
            "detail": f"Metric '{metric}' found in {total_matches} locations, but value '{value}' not found nearby. The specific number may not be in the corpus.",
            "metric_match_count": total_matches,
            "files_with_metric": [r["filename"] for r in results]
        }


def verify(metric: str, value: str, year: str = None) -> Dict:
    """Main verification function: checks both DuckDB and Reference_Texts."""
    duckdb_result = search_duckdb_for_metric(metric, value, year)
    ref_result = search_ref_texts_for_metric(metric, value)
    
    # Aggregate verdict
    verdicts = [duckdb_result["verdict"], ref_result["verdict"]]
    
    if "verified" in verdicts:
        overall = "verified"
    elif "conflict" in verdicts:
        overall = "conflict"
    elif "partial" in verdicts:
        overall = "partial"
    else:
        overall = "not_found"
    
    return {
        "metric": metric,
        "value": value,
        "year": year,
        "overall_verdict": overall,
        "duckdb_check": duckdb_result,
        "reference_texts_check": ref_result,
        "recommendation": {
            "verified": "Data point confirmed in local corpus. Safe to use with citation.",
            "partial": f"Metric '{metric}' exists in corpus but value '{value}' was not found. DO NOT output this number as fact. Either find the correct value in the corpus or mark as unverified.",
            "not_found": f"Neither metric nor value found in local corpus. This data point is NOT in the corpus. You must either: (1) search the web and cite the source, or (2) state that the data is not available. DO NOT use training data.",
            "conflict": "Conflicting data found. Investigate and use the most authoritative source.",
            "error": "Verification tool error. Fall back to manual checking."
        }.get(overall, "Unknown verdict.")
    }


def main():
    parser = argparse.ArgumentParser(description="Data Verifier - Anti-Hallucination Firewall")
    parser.add_argument("--metric", type=str, required=True, help="Metric name (e.g., CPI, GDP, minimum wage)")
    parser.add_argument("--value", type=str, required=True, help="Value to verify (e.g., 133, 1500, 5.1)")
    parser.add_argument("--year", type=str, default=None, help="Year filter (e.g., 2024)")
    
    args = parser.parse_args()
    
    result = verify(args.metric, args.value, args.year)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
