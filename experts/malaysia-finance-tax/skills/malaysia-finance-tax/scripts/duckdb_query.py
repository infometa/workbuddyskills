"""
DuckDB Query Engine for Malaysia Finance & Tax Expert
Provides: --list-tables, --schema, --sql, --search, --sample modes
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
import sys
import os
import argparse

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'datasets', 'malaysia_finance_tax.duckdb')
ALT_DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'Databases', 'malaysia_finance_tax.duckdb')

def get_db_path():
    for p in [DB_PATH, ALT_DB_PATH]:
        resolved = os.path.abspath(p)
        if os.path.exists(resolved):
            return resolved
    return os.path.abspath(DB_PATH)

def connect():
    path = get_db_path()
    if not os.path.exists(path):
        print(json.dumps({"error": f"Database not found at {path}", "path_checked": path}, ensure_ascii=False))
        sys.exit(1)
    return duckdb.connect(path)

def list_tables():
    con = connect()
    tables = con.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='main' ORDER BY table_name").fetchall()
    result = []
    for t in tables:
        name = t[0]
        count = con.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0]
        result.append({"table": name, "rows": count})
    con.close()
    print(json.dumps(result, ensure_ascii=False, indent=2))

def show_schema(table_name=None):
    con = connect()
    if table_name:
        # Verify table exists
        exists = con.execute(f"SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='main' AND table_name=?", [table_name]).fetchone()[0]
        if not exists:
            print(json.dumps({"error": f"Table '{table_name}' not found"}, ensure_ascii=False))
            con.close()
            return
        cols = con.execute(f"SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_schema='main' AND table_name=? ORDER BY ordinal_position", [table_name]).fetchall()
        result = {"table": table_name, "columns": [{"name": c[0], "type": c[1], "nullable": c[2]} for c in cols]}
    else:
        tables = con.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='main' ORDER BY table_name").fetchall()
        result = {"tables": []}
        for t in tables:
            cols = con.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_schema='main' AND table_name=? ORDER BY ordinal_position", [t[0]]).fetchall()
            result["tables"].append({"table": t[0], "columns": [{"name": c[0], "type": c[1]} for c in cols]})
    con.close()
    print(json.dumps(result, ensure_ascii=False, indent=2))

def run_sql(sql):
    try:
        con = connect()
        result = con.execute(sql).fetchdf()
        con.close()
        # Convert to JSON serializable
        output = result.to_dict(orient='records')
        print(json.dumps(output, ensure_ascii=False, indent=2, default=str))
    except Exception as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False))

def search_tables(keyword):
    con = connect()
    tables = con.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='main' ORDER BY table_name").fetchall()
    all_results = {}
    for t in tables:
        name = t[0]
        cols = con.execute(f"SELECT column_name FROM information_schema.columns WHERE table_schema='main' AND table_name=?", [name]).fetchall()
        for col in cols:
            col_name = col[0]
            sample = con.execute(f'SELECT DISTINCT "{col_name}" FROM "{name}" WHERE CAST("{col_name}" AS VARCHAR) ILIKE ? LIMIT 5', [f'%{keyword}%']).fetchall()
            if sample:
                if name not in all_results:
                    all_results[name] = []
                for row in sample:
                    if row[0] is not None:
                        all_results[name].append({"column": col_name, "value": str(row[0])})
    con.close()
    print(json.dumps(all_results, ensure_ascii=False, indent=2))

def sample_data(table_name, limit=5):
    con = connect()
    exists = con.execute(f"SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='main' AND table_name=?", [table_name]).fetchone()[0]
    if not exists:
        print(json.dumps({"error": f"Table '{table_name}' not found"}, ensure_ascii=False))
        con.close()
        return
    cols = [c[0] for c in con.execute(f"SELECT column_name FROM information_schema.columns WHERE table_schema='main' AND table_name=? ORDER BY ordinal_position", [table_name]).fetchall()]
    data = con.execute(f'SELECT * FROM "{table_name}" LIMIT ?', [limit]).fetchdf()
    con.close()
    output = data.to_dict(orient='records')
    print(json.dumps({"table": table_name, "columns": cols, "sample": output}, ensure_ascii=False, indent=2, default=str))

def main():
    parser = argparse.ArgumentParser(description='Malaysia Finance & Tax DuckDB Query Engine')
    parser.add_argument('--list-tables', action='store_true', help='List all tables with row counts')
    parser.add_argument('--schema', nargs='?', const='__all__', help='Show schema for a table (or all tables)')
    parser.add_argument('--sql', type=str, help='Run raw SQL query')
    parser.add_argument('--search', type=str, help='Search keyword across all tables')
    parser.add_argument('--sample', nargs=2, metavar=('TABLE', 'LIMIT'), help='Sample data from a table')
    args = parser.parse_args()

    if args.list_tables:
        list_tables()
    elif args.schema:
        show_schema(None if args.schema == '__all__' else args.schema)
    elif args.sql:
        run_sql(args.sql)
    elif args.search:
        search_tables(args.search)
    elif args.sample:
        sample_data(args.sample[0], int(args.sample[1]))
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
