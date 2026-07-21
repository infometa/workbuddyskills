"""SQLite operations: export-side reduce DB, import-side ATTACH + merge."""
from __future__ import annotations

import json
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


# --- locking ---

def acquire_write_lock(db_path: Path, *, retries: int = 3, wait: float = 0.5) -> sqlite3.Connection:
    """Try to grab an immediate write lock. Raise BlockingIOError if blocked.

    Caller is responsible for closing the connection (which releases the lock).
    """
    last_err: Optional[Exception] = None
    for _ in range(retries):
        try:
            conn = sqlite3.connect(str(db_path), timeout=2.0)
            conn.execute("BEGIN IMMEDIATE")
            return conn
        except sqlite3.OperationalError as e:
            last_err = e
            try:
                conn.close()  # type: ignore[name-defined]
            except Exception:
                pass
            time.sleep(wait)
    raise BlockingIOError(
        f"Target DB is locked (WorkBuddy seems running): {db_path}. "
        f"Underlying: {last_err}"
    )


# --- schema introspection ---

def table_columns(conn: sqlite3.Connection, schema: str, table: str) -> List[str]:
    cur = conn.execute(f"PRAGMA {schema}.table_info({table})")
    return [row[1] for row in cur.fetchall()]


def column_intersection(
    conn: sqlite3.Connection, target_schema: str, source_schema: str, table: str
) -> List[str]:
    src = set(table_columns(conn, source_schema, table))
    dst = set(table_columns(conn, target_schema, table))
    common = [c for c in table_columns(conn, target_schema, table) if c in src]
    if src - dst:
        # We don't need to report here; caller will warn via report module.
        pass
    return common


def table_exists(conn: sqlite3.Connection, schema: str, table: str) -> bool:
    cur = conn.execute(
        f"SELECT 1 FROM {schema}.sqlite_master WHERE type='table' AND name=?",
        (table,),
    )
    return cur.fetchone() is not None


def get_create_sql(conn: sqlite3.Connection, schema: str, table: str) -> str:
    cur = conn.execute(
        f"SELECT sql FROM {schema}.sqlite_master WHERE type='table' AND name=?",
        (table,),
    )
    row = cur.fetchone()
    if not row:
        raise ValueError(f"Table {schema}.{table} not found")
    return row[0]


# --- export side: reduce source DB to a minimal new DB ---

def export_reduced_db(
    source_db: Path,
    output_db: Path,
    tables: List[Dict[str, Any]],
    *,
    exclude_session_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Create output_db with only specified tables (filtered, no soft-deleted).

    Returns dict with keys:
        counts: {table_name: row_count}
        excluded: {table_name: {"by_status": N, "by_self_session": N}}
    """
    if output_db.exists():
        output_db.unlink()
    output_db.parent.mkdir(parents=True, exist_ok=True)

    # Open target (new empty), attach source by plain path (we only SELECT from src)
    conn = sqlite3.connect(str(output_db))
    try:
        conn.execute(f"ATTACH DATABASE ? AS src", (str(source_db),))
        counts: Dict[str, int] = {}
        excluded: Dict[str, Dict[str, int]] = {}
        for t in tables:
            name = t["name"]
            if not table_exists(conn, "src", name):
                counts[name] = 0
                continue
            # Recreate schema via src's CREATE TABLE statement (main schema)
            create_sql = get_create_sql(conn, "src", name)
            conn.execute(create_sql)

            # Build WHERE clause
            where_parts: List[str] = []
            params: List[Any] = []
            if t.get("has_deleted_at"):
                where_parts.append("deleted_at IS NULL")
            ex_status = t.get("exclude_status") or []
            if ex_status:
                placeholders = ",".join("?" for _ in ex_status)
                where_parts.append(f"status NOT IN ({placeholders})")
                params.extend(ex_status)
            if t.get("exclude_self_session") and exclude_session_ids:
                placeholders = ",".join("?" for _ in exclude_session_ids)
                where_parts.append(f"id NOT IN ({placeholders})")
                params.extend(exclude_session_ids)

            where = (" WHERE " + " AND ".join(where_parts)) if where_parts else ""

            # Count what we're excluding for the report
            sec_excluded: Dict[str, int] = {}
            if ex_status:
                placeholders = ",".join("?" for _ in ex_status)
                cur = conn.execute(
                    f"SELECT COUNT(*) FROM src.{name} "
                    f"WHERE status IN ({placeholders}) "
                    f"{'AND deleted_at IS NULL' if t.get('has_deleted_at') else ''}",
                    ex_status,
                )
                sec_excluded["by_status"] = cur.fetchone()[0]
            if t.get("exclude_self_session") and exclude_session_ids:
                placeholders = ",".join("?" for _ in exclude_session_ids)
                cur = conn.execute(
                    f"SELECT COUNT(*) FROM src.{name} "
                    f"WHERE id IN ({placeholders})",
                    exclude_session_ids,
                )
                sec_excluded["by_self_session"] = cur.fetchone()[0]
            if sec_excluded:
                excluded[name] = sec_excluded

            conn.execute(
                f"INSERT INTO {name} SELECT * FROM src.{name}{where}", params
            )
            cur = conn.execute(f"SELECT COUNT(*) FROM {name}")
            counts[name] = cur.fetchone()[0]
        conn.commit()
        conn.execute("DETACH DATABASE src")
        return {"counts": counts, "excluded": excluded}
    finally:
        conn.close()


# --- import side: merge package DB into target DB ---

def merge_table(
    conn: sqlite3.Connection,
    target_schema: str,
    source_schema: str,
    table: str,
    *,
    overwrite: bool,
    extra_where: str = "",
    transform_user_id: Optional[Dict[str, str]] = None,
) -> Tuple[int, int]:
    """Merge src.table into target_schema.table.

    Returns (rows_inserted, rows_skipped_or_replaced).

    overwrite=False → INSERT OR IGNORE
    overwrite=True  → INSERT OR REPLACE, with sessions.deleted_at protection
                      handled by caller (stash_then_replace_sessions).

    transform_user_id={src_uid: dst_uid, ...} when provided, applied to
    user_id column on insert (only for tables that have user_id).
    """
    if not table_exists(conn, source_schema, table):
        return (0, 0)
    cols = column_intersection(conn, target_schema, source_schema, table)
    if not cols:
        return (0, 0)
    col_list = ", ".join(cols)
    select_cols = []
    for c in cols:
        if c == "user_id" and transform_user_id:
            # Build CASE expression
            case = "CASE user_id"
            for src_uid, dst_uid in transform_user_id.items():
                case += f" WHEN {sqlite3_literal(src_uid)} THEN {sqlite3_literal(dst_uid)}"
            case += " ELSE user_id END"
            select_cols.append(case)
        else:
            select_cols.append(c)
    select_list = ", ".join(select_cols)
    verb = "INSERT OR REPLACE" if overwrite else "INSERT OR IGNORE"
    where = f" WHERE {extra_where}" if extra_where else ""

    # Count what's about to change
    cur = conn.execute(f"SELECT COUNT(*) FROM {source_schema}.{table}{where}")
    src_rows = cur.fetchone()[0]
    cur = conn.execute(f"SELECT COUNT(*) FROM {target_schema}.{table}")
    before = cur.fetchone()[0]
    conn.execute(
        f"{verb} INTO {target_schema}.{table} ({col_list}) "
        f"SELECT {select_list} FROM {source_schema}.{table}{where}"
    )
    cur = conn.execute(f"SELECT COUNT(*) FROM {target_schema}.{table}")
    after = cur.fetchone()[0]
    inserted = after - before
    skipped = src_rows - inserted
    return (inserted, max(skipped, 0))


def sqlite3_literal(s: str) -> str:
    """Quote a string for inline SQL (only for safe alphanumeric/uuid values)."""
    return "'" + s.replace("'", "''") + "'"


def protect_sessions_deleted_at(conn: sqlite3.Connection, target_schema: str) -> Dict[str, Optional[int]]:
    """Snapshot (id → deleted_at) before --overwrite merge so we can re-apply."""
    cur = conn.execute(
        f"SELECT id, deleted_at FROM {target_schema}.sessions "
        f"WHERE deleted_at IS NOT NULL"
    )
    return {row[0]: row[1] for row in cur.fetchall()}


def restore_sessions_deleted_at(
    conn: sqlite3.Connection, target_schema: str, snapshot: Dict[str, Optional[int]]
) -> int:
    """Re-apply deleted_at values clobbered by INSERT OR REPLACE."""
    count = 0
    for sid, deleted_at in snapshot.items():
        cur = conn.execute(
            f"UPDATE {target_schema}.sessions SET deleted_at = ? "
            f"WHERE id = ? AND deleted_at IS NULL",
            (deleted_at, sid),
        )
        count += cur.rowcount
    return count


# --- automation_runs orphan handling ---

def count_orphan_runs(conn: sqlite3.Connection, source_schema: str, target_schema: str) -> int:
    """Count automation_runs in src whose automation_id won't exist in target after merge.

    'Won't exist' = not in target.automations AND not in src.automations.
    """
    if not table_exists(conn, source_schema, "automation_runs"):
        return 0
    cur = conn.execute(
        f"""SELECT COUNT(*) FROM {source_schema}.automation_runs sr
            WHERE sr.automation_id NOT IN (SELECT id FROM {target_schema}.automations)
              AND sr.automation_id NOT IN (SELECT id FROM {source_schema}.automations)"""
    )
    return cur.fetchone()[0]


# --- path rewriting in DB columns (cross-machine import) ---

def rewrite_path_columns(
    conn: sqlite3.Connection,
    schema: str,
    db_columns_spec: List[Dict[str, Any]],
    mapper,  # PathMapper, untyped to avoid circular import
) -> Dict[str, Dict[str, int]]:
    """For each column spec in db_columns_spec, walk every row and rewrite
    matched paths via mapper. Handles 'json_array' typed columns specially.

    Returns: {table_name: {column: rewritten_count}}
    """
    result: Dict[str, Dict[str, int]] = {}
    for spec in db_columns_spec:
        table = spec["table"]
        column = spec["column"]
        col_type = spec.get("type", "scalar")  # 'scalar' | 'json_array'
        is_pk = spec.get("pk", False)
        if not table_exists(conn, schema, table):
            continue
        cols = table_columns(conn, schema, table)
        if column not in cols:
            continue
        pk_col = _primary_key_column(conn, schema, table) or "rowid"
        rewritten = 0

        cur = conn.execute(f"SELECT {pk_col}, {column} FROM {schema}.{table}")
        rows = cur.fetchall()
        for pk_val, val in rows:
            if val is None:
                continue
            if col_type == "json_array":
                try:
                    arr = json.loads(val)
                    if not isinstance(arr, list):
                        continue
                    new_arr = []
                    changed = False
                    for item in arr:
                        if isinstance(item, str):
                            r = mapper.rewrite(item)
                            if r:
                                new_arr.append(r.new_path)
                                changed = True
                                continue
                        new_arr.append(item)
                    if changed:
                        conn.execute(
                            f"UPDATE {schema}.{table} SET {column} = ? "
                            f"WHERE {pk_col} = ?",
                            (json.dumps(new_arr, ensure_ascii=False), pk_val),
                        )
                        rewritten += 1
                except (json.JSONDecodeError, TypeError):
                    continue
            else:
                if not isinstance(val, str):
                    continue
                r = mapper.rewrite(val)
                if r:
                    if is_pk:
                        # Must handle PK collisions: skip if new path already
                        # exists in target, else update.
                        cur2 = conn.execute(
                            f"SELECT 1 FROM {schema}.{table} WHERE {column} = ?",
                            (r.new_path,),
                        )
                        if cur2.fetchone():
                            # Collision: delete the old row (target wins)
                            conn.execute(
                                f"DELETE FROM {schema}.{table} WHERE {pk_col} = ?",
                                (pk_val,),
                            )
                        else:
                            conn.execute(
                                f"UPDATE {schema}.{table} SET {column} = ? "
                                f"WHERE {pk_col} = ?",
                                (r.new_path, pk_val),
                            )
                            rewritten += 1
                    else:
                        conn.execute(
                            f"UPDATE {schema}.{table} SET {column} = ? "
                            f"WHERE {pk_col} = ?",
                            (r.new_path, pk_val),
                        )
                        rewritten += 1
        result.setdefault(table, {})[column] = rewritten
    conn.commit()
    return result


def _primary_key_column(
    conn: sqlite3.Connection, schema: str, table: str
) -> Optional[str]:
    cur = conn.execute(f"PRAGMA {schema}.table_info({table})")
    for row in cur.fetchall():
        # row = (cid, name, type, notnull, dflt_value, pk)
        if row[5] == 1:
            return row[1]
    return None
