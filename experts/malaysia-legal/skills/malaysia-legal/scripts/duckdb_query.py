#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DuckDB Query Tool for Malaysia Legal Compliance Skill

Usage:
    python duckdb_query.py --list-tables
    python duckdb_query.py --schema <table_name>
    python duckdb_query.py --sql "SELECT * FROM cpi_headline LIMIT 5"
    python duckdb_query.py --search "CPI"          # find tables matching keyword
    python duckdb_query.py --sample <table_name>    # show 5 sample rows

Output: JSON to stdout, errors to stderr.
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Force UTF-8 output on Windows to avoid GBK encoding errors
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

try:
    import duckdb
except ImportError:
    print(json.dumps({"error": "duckdb not installed. Run: pip install duckdb"}), file=sys.stdout)
    sys.exit(1)

# Resolve DuckDB path relative to plugin root
SCRIPT_DIR = Path(__file__).resolve().parent
PLUGIN_ROOT = SCRIPT_DIR.parent.parent.parent  # scripts/ -> malaysia-ssm-database/ -> skills/ -> plugin root
DB_PATH = PLUGIN_ROOT / "Databases" / "malaysia.duckdb"

MAX_ROWS = 500  # safety limit to prevent huge outputs


def get_connection():
    if not DB_PATH.exists():
        return None, f"DuckDB file not found at: {DB_PATH}"
    try:
        conn = duckdb.connect(str(DB_PATH), read_only=True)
        return conn, None
    except Exception as e:
        return None, str(e)


def list_tables(conn):
    """List all tables with row counts."""
    result = conn.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'main'
        ORDER BY table_name
    """).fetchall()
    tables = []
    for (name,) in result:
        try:
            count = conn.execute(f"SELECT COUNT(*) FROM \"{name}\"").fetchone()[0]
        except:
            count = -1
        tables.append({"table": name, "rows": count})
    return tables


def get_schema(conn, table_name):
    """Get column schema for a table."""
    # Sanitize table name (only allow alphanumeric + underscore)
    safe = "".join(c for c in table_name if c.isalnum() or c == "_")
    if safe != table_name:
        return {"error": f"Invalid table name: {table_name}"}
    try:
        cols = conn.execute(f"PRAGMA table_info(\"{safe}\")").fetchall()
        columns = []
        for col in cols:
            columns.append({
                "cid": col[0],
                "name": col[1],
                "type": col[2],
                "notnull": col[3],
                "default": col[4],
                "pk": col[5]
            })
        # Also get sample using fetchall to avoid pandas dependency
        sample_cursor = conn.execute(f"SELECT * FROM \"{safe}\" LIMIT 3")
        sample_cols = [desc[0] for desc in sample_cursor.description]
        sample_rows = sample_cursor.fetchall()
        sample_records = []
        for row in sample_rows:
            record = {}
            for i, col in enumerate(sample_cols):
                record[col] = str(row[i]) if row[i] is not None else None
            sample_records.append(record)
        return {"table": safe, "columns": columns, "sample_rows": sample_records}
    except Exception as e:
        return {"error": str(e)}


def search_tables(conn, keyword):
    """Find tables whose name or columns match keyword."""
    kw = keyword.lower()
    all_tables = list_tables(conn)
    matches = []
    for t in all_tables:
        tname = t["table"].lower()
        if kw in tname:
            matches.append({"table": t["table"], "rows": t["rows"], "match": "table_name"})
            continue
        # Check column names
        try:
            cols = conn.execute(f"PRAGMA table_info(\"{t['table']}\")").fetchall()
            col_names = [c[1].lower() for c in cols]
            matched_cols = [c for c in col_names if kw in c]
            if matched_cols:
                matches.append({
                    "table": t["table"],
                    "rows": t["rows"],
                    "match": "column",
                    "columns": matched_cols
                })
        except:
            pass
    return matches


def execute_sql(conn, sql):
    """Execute arbitrary SQL and return results."""
    # Basic SQL injection prevention: block DDL/DML
    sql_upper = sql.strip().upper()
    forbidden = ["DROP", "DELETE", "INSERT", "UPDATE", "CREATE", "ALTER", "ATTACH", "DETACH", "PRAGMA"]
    for kw in forbidden:
        if sql_upper.startswith(kw):
            return {"error": f"Forbidden operation: {kw}. Only SELECT queries allowed."}
    
    # Add LIMIT if not present
    if "LIMIT" not in sql_upper:
        sql = sql.rstrip(";") + f" LIMIT {MAX_ROWS}"
    
    try:
        # Use fetchall() instead of fetchdf() to avoid pandas/numpy dependency
        cursor = conn.execute(sql)
        col_names = [desc[0] for desc in cursor.description]
        rows_raw = cursor.fetchall()
        records = []
        for row in rows_raw:
            record = {}
            for i, col in enumerate(col_names):
                record[col] = str(row[i]) if row[i] is not None else None
            records.append(record)
        return {
            "row_count": len(records),
            "truncated": len(records) >= MAX_ROWS,
            "columns": col_names,
            "rows": records
        }
    except Exception as e:
        return {"error": str(e), "sql": sql}


def sample_table(conn, table_name, n=5):
    """Get sample rows from a table."""
    safe = "".join(c for c in table_name if c.isalnum() or c == "_")
    if safe != table_name:
        return {"error": f"Invalid table name: {table_name}"}
    try:
        cursor = conn.execute(f"SELECT * FROM \"{safe}\" LIMIT {n}")
        col_names = [desc[0] for desc in cursor.description]
        rows_raw = cursor.fetchall()
        records = []
        for row in rows_raw:
            record = {}
            for i, col in enumerate(col_names):
                record[col] = str(row[i]) if row[i] is not None else None
            records.append(record)
        return {"table": safe, "sample_size": len(records), "rows": records}
    except Exception as e:
        return {"error": str(e)}


def main():
    global DB_PATH
    parser = argparse.ArgumentParser(description="DuckDB Query Tool for Malaysia BI")
    parser.add_argument("--list-tables", action="store_true", help="List all tables with row counts")
    parser.add_argument("--schema", type=str, help="Get schema for a specific table")
    parser.add_argument("--sql", type=str, help="Execute a SELECT SQL query")
    parser.add_argument("--search", type=str, help="Search tables by keyword (matches table name or column name)")
    parser.add_argument("--sample", type=str, help="Get sample rows from a table")
    parser.add_argument("--db-path", type=str, default=str(DB_PATH), help="Path to DuckDB file")
    
    args = parser.parse_args()
    
    # Override DB path if provided
    if args.db_path:
        DB_PATH = Path(args.db_path)
    
    conn, err = get_connection()
    if err:
        print(json.dumps({"error": err, "db_path": str(DB_PATH)}))
        sys.exit(1)
    
    try:
        if args.list_tables:
            result = {"tables": list_tables(conn), "total": len(list_tables(conn))}
        elif args.schema:
            result = get_schema(conn, args.schema)
        elif args.sql:
            result = execute_sql(conn, args.sql)
        elif args.search:
            result = {"keyword": args.search, "matches": search_tables(conn, args.search)}
        elif args.sample:
            result = sample_table(conn, args.sample)
        else:
            result = {"error": "No action specified. Use --help for usage."}
        
        print(json.dumps(result, ensure_ascii=False, default=str, indent=2))
    finally:
        conn.close()


if __name__ == "__main__":
    main()
