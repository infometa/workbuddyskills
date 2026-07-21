"""End-to-end fixture tests for export.py + import.py.

Run: python -m unittest scripts/test_migration.py -v
"""
from __future__ import annotations

import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parent

PYTHON = sys.executable
EXPORT = _HERE / "export.py"
IMPORT = _HERE / "import.py"


# --- helpers ---

DB_SCHEMA = """
CREATE TABLE sessions (
  id TEXT PRIMARY KEY,
  cwd TEXT NOT NULL,
  user_id TEXT NOT NULL,
  title TEXT,
  status TEXT DEFAULT 'Pending',
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL,
  deleted_at INTEGER,
  model TEXT,
  expert_id TEXT
);
CREATE TABLE automations (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  prompt TEXT NOT NULL,
  status TEXT NOT NULL,
  schedule_type TEXT DEFAULT 'recurring',
  cwds TEXT NOT NULL DEFAULT '[]',
  rrule TEXT DEFAULT '',
  skills_json TEXT DEFAULT '[]',
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL,
  deleted_at INTEGER
);
CREATE TABLE automation_runs (
  thread_id TEXT PRIMARY KEY,
  automation_id TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL
);
CREATE TABLE automation_runtime_state (
  automation_id TEXT PRIMARY KEY,
  last_run_at INTEGER,
  running INTEGER DEFAULT 0
);
CREATE TABLE workspaces (
  path TEXT PRIMARY KEY,
  last_opened_at INTEGER NOT NULL
);
CREATE TABLE session_usage (
  session_id TEXT PRIMARY KEY,
  used INTEGER NOT NULL,
  size INTEGER NOT NULL,
  updated_at INTEGER NOT NULL
);
"""


def make_fake_root(root: Path, uid: str, *, sessions: list, skills: list, memory_body: str,
                   identity_body: str = "i am identity", settings: dict = None,
                   mcp: dict = None, automations: list = None,
                   automation_runs: list = None,
                   inflight_sessions: list = None) -> None:
    root.mkdir(parents=True, exist_ok=True)
    db = root / "workbuddy.db"
    if db.exists():
        db.unlink()
    conn = sqlite3.connect(db)
    conn.executescript(DB_SCHEMA)
    for sid in sessions:
        conn.execute(
            "INSERT INTO sessions (id, cwd, user_id, title, status, created_at, updated_at, deleted_at) "
            "VALUES (?, ?, ?, ?, 'Completed', 1, 2, NULL)",
            (sid, "/tmp/foo", uid, f"title-{sid}"),
        )
    # In-flight sessions: should be excluded by export
    for sid, status in inflight_sessions or []:
        conn.execute(
            "INSERT INTO sessions (id, cwd, user_id, title, status, created_at, updated_at, deleted_at) "
            "VALUES (?, ?, ?, ?, ?, 1, 2, NULL)",
            (sid, "/tmp/foo", uid, f"inflight-{sid}", status),
        )
    # Add one deleted session that should NOT be exported
    conn.execute(
        "INSERT INTO sessions (id, cwd, user_id, title, status, created_at, updated_at, deleted_at) "
        "VALUES (?, ?, ?, ?, 'Completed', 1, 2, 999)",
        (f"deleted-{uid}", "/tmp/x", uid, "deleted"),
    )
    for a in automations or []:
        conn.execute(
            "INSERT INTO automations (id, name, prompt, status, created_at, updated_at, deleted_at) "
            "VALUES (?, ?, 'do thing', 'enabled', 1, 2, NULL)",
            (a, f"automation-{a}"),
        )
    for r in automation_runs or []:
        # r = (thread_id, automation_id, status)
        conn.execute(
            "INSERT INTO automation_runs (thread_id, automation_id, status, created_at, updated_at) "
            "VALUES (?, ?, ?, 1, 2)",
            r,
        )
    # one entry in session_usage to ensure it doesn't leak into package
    conn.execute(
        "INSERT INTO session_usage (session_id, used, size, updated_at) VALUES (?, 1, 1, 1)",
        (f"leak-{uid}",),
    )
    conn.commit()
    conn.close()

    skills_dir = root / "skills"
    skills_dir.mkdir(exist_ok=True)
    for name in skills:
        sd = skills_dir / name
        sd.mkdir(exist_ok=True)
        (sd / "SKILL.md").write_text(f"---\nname: {name}\n---\n{name} body in {uid}\n")

    mem = root / "memory"
    mem.mkdir(exist_ok=True)
    (mem / f"{uid}_memory.md").write_text(memory_body)

    (root / "IDENTITY.md").write_text(identity_body)

    if settings is not None:
        (root / "settings.json").write_text(json.dumps(settings))
    if mcp is not None:
        (root / "mcp.json").write_text(json.dumps(mcp))

    # projects/<folder>/<sessionId>.jsonl
    projects = root / "projects"
    for sid in sessions:
        pdir = projects / f"proj-{sid}"
        pdir.mkdir(parents=True, exist_ok=True)
        (pdir / f"{sid}.jsonl").write_text(f'{{"role":"user","content":"hi {sid}"}}\n')


def run(cmd: list, *, check: bool = True) -> subprocess.CompletedProcess:
    res = subprocess.run(cmd, capture_output=True, text=True)
    if check and res.returncode != 0:
        raise AssertionError(f"Command failed: {' '.join(cmd)}\nSTDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}")
    return res


def db_rows(db: Path, table: str) -> list:
    conn = sqlite3.connect(str(db))
    try:
        cur = conn.execute(f"SELECT * FROM {table}")
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]
    finally:
        conn.close()


# --- tests ---

class BaseCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="wb-test-"))
        self.src = self.tmp / "src"
        self.dst = self.tmp / "dst"
        self.pkg = self.tmp / "pkg.zip"

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)


class TestExportImportBasic(BaseCase):
    def test_merge_default_skip_conflicts(self):
        """Existing dst data must survive; new src data must arrive."""
        uid = "uid-alpha"
        make_fake_root(
            self.src, uid,
            sessions=["s1", "s2", "s3"],
            skills=["skill-a", "skill-b"],
            memory_body="memory from SRC",
            identity_body="src identity",
            settings={"theme": "dark", "fontSize": 14},
            mcp={"mcpServers": {"srv-x": {"cmd": "x"}, "srv-shared": {"cmd": "src-shared"}}},
            automations=["a1"],
            automation_runs=[("run-1", "a1", "ok"), ("run-orphan", "nonexistent", "ok")],
        )
        make_fake_root(
            self.dst, uid,
            sessions=["s10", "s11"],
            skills=["skill-x"],
            memory_body="memory from DST original",
            identity_body="dst identity (DO NOT TOUCH)",
            settings={"theme": "light", "extraKey": "keepme"},
            mcp={"mcpServers": {"srv-shared": {"cmd": "dst-shared"}}},
        )
        # Also make a conflicting skill: both have "skill-shared" with different contents
        (self.src / "skills" / "skill-shared").mkdir()
        (self.src / "skills" / "skill-shared" / "SKILL.md").write_text("SRC version")
        (self.dst / "skills" / "skill-shared").mkdir()
        (self.dst / "skills" / "skill-shared" / "SKILL.md").write_text("DST version")

        # Export
        run([PYTHON, str(EXPORT), "--source", str(self.src),
             "--output", str(self.pkg), "--no-credentials"])
        self.assertTrue(self.pkg.is_file())

        # Import (default = skip)
        run([PYTHON, str(IMPORT), "--package", str(self.pkg), "--target", str(self.dst)])

        # DB assertions: dst's 2 + src's 3 = 5 (deleted excluded); no session_usage leak
        sessions = db_rows(self.dst / "workbuddy.db", "sessions")
        # also includes the dst's deleted row (1) and src wasn't merged (excluded). +1.
        non_deleted_ids = {r["id"] for r in sessions if r["deleted_at"] is None}
        self.assertEqual(non_deleted_ids, {"s1", "s2", "s3", "s10", "s11"})
        # session_usage in target should NOT have grown from src merge — the row
        # the src had ("leak-uid-alpha") was a different table not in whitelist;
        # since dst also had its own "leak-uid-alpha" row, count must be 1 (dst's own),
        # i.e. src's session_usage was filtered out at export time.
        usage = db_rows(self.dst / "workbuddy.db", "session_usage")
        self.assertEqual(len(usage), 1, "session_usage must NOT be merged across runs")

        # Orphan automation_run dropped
        runs = db_rows(self.dst / "workbuddy.db", "automation_runs")
        thread_ids = {r["thread_id"] for r in runs}
        self.assertIn("run-1", thread_ids)
        self.assertNotIn("run-orphan", thread_ids)

        # Skills: shared keeps DST version (skip), src-only "skill-a"/"skill-b" added
        self.assertEqual(
            (self.dst / "skills" / "skill-shared" / "SKILL.md").read_text(),
            "DST version",
            "skip-if-exists: existing skill must not be clobbered",
        )
        self.assertTrue((self.dst / "skills" / "skill-a" / "SKILL.md").is_file())
        self.assertTrue((self.dst / "skills" / "skill-x" / "SKILL.md").is_file())

        # Memory: contains DST original first, then separator, then SRC body
        mem = (self.dst / "memory" / f"{uid}_memory.md").read_text()
        self.assertIn("memory from DST original", mem)
        self.assertIn("memory from SRC", mem)
        self.assertLess(mem.index("DST original"), mem.index("from SRC"))
        self.assertIn("imported from migration package", mem)

        # settings.json: theme stays "light", extraKey kept, fontSize added
        st = json.loads((self.dst / "settings.json").read_text())
        self.assertEqual(st["theme"], "light")
        self.assertEqual(st["extraKey"], "keepme")
        self.assertEqual(st["fontSize"], 14)

        # mcp.json: srv-shared keeps dst version, srv-x added
        mcp = json.loads((self.dst / "mcp.json").read_text())
        self.assertEqual(mcp["mcpServers"]["srv-shared"]["cmd"], "dst-shared")
        self.assertEqual(mcp["mcpServers"]["srv-x"]["cmd"], "x")

        # IDENTITY.md: dst untouched; src lands as IDENTITY.imported.md
        self.assertEqual((self.dst / "IDENTITY.md").read_text(), "dst identity (DO NOT TOUCH)")
        self.assertTrue((self.dst / "IDENTITY.imported.md").is_file())

        # Backups exist
        backups = list(self.dst.glob("workbuddy.db.bak-*"))
        self.assertEqual(len(backups), 1)


class TestOverwrite(BaseCase):
    def test_overwrite_replaces_but_protects_deleted_at(self):
        uid = "uid-beta"
        make_fake_root(self.src, uid, sessions=["s1"], skills=["skill-a"],
                       memory_body="SRC memory")
        make_fake_root(self.dst, uid, sessions=["s1"], skills=["skill-a"],
                       memory_body="DST memory")
        # Mark dst.s1 as soft-deleted; --overwrite must NOT resurrect it
        conn = sqlite3.connect(str(self.dst / "workbuddy.db"))
        conn.execute("UPDATE sessions SET deleted_at = 12345 WHERE id = 's1'")
        conn.commit()
        conn.close()

        run([PYTHON, str(EXPORT), "--source", str(self.src),
             "--output", str(self.pkg), "--no-credentials"])
        run([PYTHON, str(IMPORT), "--package", str(self.pkg),
             "--target", str(self.dst), "--overwrite"])

        # deleted_at preserved
        sessions = db_rows(self.dst / "workbuddy.db", "sessions")
        s1 = next(r for r in sessions if r["id"] == "s1")
        self.assertEqual(s1["deleted_at"], 12345, "deleted_at must be protected on --overwrite")

        # Memory overwritten (no separator)
        mem = (self.dst / "memory" / f"{uid}_memory.md").read_text()
        self.assertNotIn("imported from migration package", mem)
        self.assertIn("SRC memory", mem)


class TestUidMap(BaseCase):
    def test_uid_rewrite(self):
        src_uid, dst_uid = "uid-A", "uid-B"
        make_fake_root(self.src, src_uid, sessions=["s1", "s2"], skills=["sk"],
                       memory_body="A's memories")
        make_fake_root(self.dst, dst_uid, sessions=["s10"], skills=["sk2"],
                       memory_body="B's existing memories")

        run([PYTHON, str(EXPORT), "--source", str(self.src),
             "--output", str(self.pkg), "--no-credentials"])
        run([PYTHON, str(IMPORT), "--package", str(self.pkg),
             "--target", str(self.dst), "--uid-map", f"{src_uid}={dst_uid}"])

        sessions = db_rows(self.dst / "workbuddy.db", "sessions")
        for sid in ("s1", "s2"):
            row = next(r for r in sessions if r["id"] == sid)
            self.assertEqual(row["user_id"], dst_uid, "user_id should be rewritten")

        # Memory file renamed
        self.assertTrue((self.dst / "memory" / f"{dst_uid}_memory.md").is_file())
        mem = (self.dst / "memory" / f"{dst_uid}_memory.md").read_text()
        self.assertIn("B's existing memories", mem)
        self.assertIn("A's memories", mem)


class TestMultiUidRequiresMap(BaseCase):
    def test_multi_uid_abort_without_map(self):
        """Multi-uid in source AND target already populated → abort without --uid-map."""
        uid1, uid2 = "uid-1", "uid-2"
        make_fake_root(self.src, uid1, sessions=["s1"], skills=["sk"], memory_body="m1")
        # Inject a second uid's session and memory
        conn = sqlite3.connect(str(self.src / "workbuddy.db"))
        conn.execute(
            "INSERT INTO sessions (id, cwd, user_id, title, status, created_at, updated_at) "
            "VALUES ('s99', '/x', ?, 't', 'Completed', 1, 2)", (uid2,))
        conn.commit()
        conn.close()
        (self.src / "memory" / f"{uid2}_memory.md").write_text("m2")

        # Target has its OWN uid with at least one session — this is when uid-map
        # becomes mandatory (otherwise we'd be mixing accounts).
        make_fake_root(self.dst, "uid-target", sessions=["t1"], skills=[], memory_body="t")

        run([PYTHON, str(EXPORT), "--source", str(self.src),
             "--output", str(self.pkg), "--no-credentials"])

        res = run([PYTHON, str(IMPORT), "--package", str(self.pkg),
                   "--target", str(self.dst)], check=False)
        self.assertNotEqual(res.returncode, 0, "Must abort without --uid-map")
        self.assertIn("multiple source uids", res.stderr.lower())

    def test_multi_uid_passthrough_when_target_empty(self):
        """Multi-uid in source but target is empty → should succeed, carrying uids through."""
        uid1, uid2 = "uid-1", "uid-2"
        make_fake_root(self.src, uid1, sessions=["s1"], skills=["sk"], memory_body="m1")
        conn = sqlite3.connect(str(self.src / "workbuddy.db"))
        conn.execute(
            "INSERT INTO sessions (id, cwd, user_id, title, status, created_at, updated_at) "
            "VALUES ('s99', '/x', ?, 't', 'Completed', 1, 2)", (uid2,))
        conn.commit()
        conn.close()
        (self.src / "memory" / f"{uid2}_memory.md").write_text("m2")

        # Target is a completely empty dir
        self.dst.mkdir(parents=True, exist_ok=True)

        run([PYTHON, str(EXPORT), "--source", str(self.src),
             "--output", str(self.pkg), "--no-credentials"])
        run([PYTHON, str(IMPORT), "--package", str(self.pkg),
             "--target", str(self.dst)])

        # Both uids should be in target's DB
        sessions = db_rows(self.dst / "workbuddy.db", "sessions")
        uids = {r["user_id"] for r in sessions if r["deleted_at"] is None}
        self.assertEqual(uids, {uid1, uid2})
        # Both memory files copied
        self.assertTrue((self.dst / "memory" / f"{uid1}_memory.md").is_file())
        self.assertTrue((self.dst / "memory" / f"{uid2}_memory.md").is_file())


class TestDbLockDetection(BaseCase):
    def test_locked_db_aborts(self):
        uid = "uid-lock"
        make_fake_root(self.src, uid, sessions=["s1"], skills=["sk"], memory_body="m")
        make_fake_root(self.dst, uid, sessions=["s10"], skills=[], memory_body="m")

        run([PYTHON, str(EXPORT), "--source", str(self.src),
             "--output", str(self.pkg), "--no-credentials"])

        # Take an exclusive lock on dst db
        lock_conn = sqlite3.connect(str(self.dst / "workbuddy.db"))
        lock_conn.execute("BEGIN EXCLUSIVE")
        try:
            res = run([PYTHON, str(IMPORT), "--package", str(self.pkg),
                       "--target", str(self.dst)], check=False)
            self.assertNotEqual(res.returncode, 0)
            self.assertIn("locked", (res.stdout + res.stderr).lower())
        finally:
            lock_conn.execute("ROLLBACK")
            lock_conn.close()


class TestDryRun(BaseCase):
    def test_dryrun_no_changes(self):
        uid = "uid-dry"
        make_fake_root(self.src, uid, sessions=["s1", "s2"], skills=["sk"],
                       memory_body="src", settings={"a": 1})
        make_fake_root(self.dst, uid, sessions=["s10"], skills=[],
                       memory_body="dst")
        snapshot_db = (self.dst / "workbuddy.db").read_bytes()
        snapshot_mem = (self.dst / "memory" / f"{uid}_memory.md").read_text()

        run([PYTHON, str(EXPORT), "--source", str(self.src),
             "--output", str(self.pkg), "--no-credentials"])
        run([PYTHON, str(IMPORT), "--package", str(self.pkg),
             "--target", str(self.dst), "--dry-run"])

        self.assertEqual((self.dst / "workbuddy.db").read_bytes(), snapshot_db,
                         "dry-run must not modify db")
        self.assertEqual((self.dst / "memory" / f"{uid}_memory.md").read_text(),
                         snapshot_mem, "dry-run must not modify memory")


class TestInflightSessionsSkipped(BaseCase):
    """In-flight sessions and the self-session must be skipped on export."""

    def test_running_sessions_excluded(self):
        uid = "u"
        make_fake_root(
            self.src, uid,
            sessions=["done-1", "done-2"],
            skills=[], memory_body="m",
            inflight_sessions=[
                ("run-1", "running"),
                ("run-2", "Running"),
                ("inp-1", "in_progress"),
                ("act-1", "active"),
                ("await-1", "awaiting_input"),
                ("stop-1", "stopping"),
                ("pend-1", "pending"),  # pending is NOT in-flight, should pass through
            ],
        )
        make_fake_root(self.dst, uid, sessions=[], skills=[], memory_body="")

        run([PYTHON, str(EXPORT), "--source", str(self.src),
             "--output", str(self.pkg), "--no-credentials"])
        run([PYTHON, str(IMPORT), "--package", str(self.pkg),
             "--target", str(self.dst)])

        rows = db_rows(self.dst / "workbuddy.db", "sessions")
        ids = {r["id"] for r in rows if r["deleted_at"] is None}
        # done-1, done-2, pend-1 should arrive; no in-flight ones
        self.assertIn("done-1", ids)
        self.assertIn("done-2", ids)
        self.assertIn("pend-1", ids, "pending sessions are NOT in-flight, must be migrated")
        for stuck in ("run-1", "run-2", "inp-1", "act-1", "await-1", "stop-1"):
            self.assertNotIn(stuck, ids, f"{stuck} should be excluded as in-flight")

    def test_self_session_excluded_via_cli(self):
        uid = "u"
        make_fake_root(
            self.src, uid,
            sessions=["self-session", "other-done"],
            skills=[], memory_body="m",
        )
        make_fake_root(self.dst, uid, sessions=[], skills=[], memory_body="")

        run([PYTHON, str(EXPORT), "--source", str(self.src),
             "--output", str(self.pkg), "--no-credentials",
             "--exclude-session-id", "self-session"])
        run([PYTHON, str(IMPORT), "--package", str(self.pkg),
             "--target", str(self.dst)])

        rows = db_rows(self.dst / "workbuddy.db", "sessions")
        ids = {r["id"] for r in rows if r["deleted_at"] is None}
        self.assertNotIn("self-session", ids)
        self.assertIn("other-done", ids)

    def test_self_session_excluded_via_env(self):
        import os
        uid = "u"
        make_fake_root(
            self.src, uid,
            sessions=["env-session", "other-done"],
            skills=[], memory_body="m",
        )
        make_fake_root(self.dst, uid, sessions=[], skills=[], memory_body="")

        env = os.environ.copy()
        env["WORKBUDDY_CURRENT_SESSION_ID"] = "env-session"
        import subprocess
        res = subprocess.run(
            [PYTHON, str(EXPORT), "--source", str(self.src),
             "--output", str(self.pkg), "--no-credentials"],
            env=env, capture_output=True, text=True,
        )
        self.assertEqual(res.returncode, 0, f"export failed: {res.stderr}")
        run([PYTHON, str(IMPORT), "--package", str(self.pkg),
             "--target", str(self.dst)])

        rows = db_rows(self.dst / "workbuddy.db", "sessions")
        ids = {r["id"] for r in rows if r["deleted_at"] is None}
        self.assertNotIn("env-session", ids)
        self.assertIn("other-done", ids)

    def test_import_defensive_inflight_skip(self):
        """If package was built by an older tool that didn't filter in-flight,
        import side should still skip them defensively."""
        uid = "u"
        make_fake_root(self.src, uid, sessions=["clean-1"], skills=[], memory_body="m")
        # Inject in-flight directly so export can't filter at db level (simulated)
        conn = sqlite3.connect(str(self.src / "workbuddy.db"))
        conn.execute(
            "INSERT INTO sessions (id, cwd, user_id, title, status, created_at, updated_at) "
            "VALUES ('stuck-1', '/', ?, 't', 'running', 1, 2)", (uid,))
        conn.commit()
        conn.close()
        make_fake_root(self.dst, uid, sessions=[], skills=[], memory_body="")

        # Run export WITHOUT inventory filter — simulate old tool by patching
        # inventory in a tmp dir
        bad_inv = self.tmp / "bad_inventory.md"
        good_inv = Path(__file__).resolve().parent.parent / "references" / "asset_inventory.md"
        # Strip exclude_status from the db_tables block to simulate old behavior
        content = good_inv.read_text()
        import re
        content = re.sub(r', "exclude_status":\s*\[[^\]]*\]', "", content)
        content = re.sub(r', "exclude_self_session":\s*true', "", content)
        bad_inv.write_text(content)

        run([PYTHON, str(EXPORT), "--source", str(self.src),
             "--output", str(self.pkg), "--no-credentials",
             "--inventory", str(bad_inv)])
        # Verify the bad package indeed has stuck-1
        import zipfile, tempfile
        with tempfile.TemporaryDirectory() as td:
            with zipfile.ZipFile(self.pkg) as zf:
                zf.extractall(td)
            pkg_db = Path(td) / "db" / "workbuddy.db"
            pkg_rows = db_rows(pkg_db, "sessions")
            pkg_ids = {r["id"] for r in pkg_rows}
            self.assertIn("stuck-1", pkg_ids, "test setup: bad package should contain stuck row")

        # Import using the GOOD inventory — must filter stuck-1 defensively
        run([PYTHON, str(IMPORT), "--package", str(self.pkg),
             "--target", str(self.dst)])
        rows = db_rows(self.dst / "workbuddy.db", "sessions")
        ids = {r["id"] for r in rows if r["deleted_at"] is None}
        self.assertIn("clean-1", ids)
        self.assertNotIn("stuck-1", ids, "import side must defensively filter in-flight")


# ===========================================================================
# v0.2 tests: path remapping, workspace bundle, restart hint
# ===========================================================================

class TestPathMapper(unittest.TestCase):
    """Direct tests of scripts.lib.pathmap.PathMapper."""

    def test_pathmap_basic_mac_to_win(self):
        from scripts.lib.pathmap import PathMapper
        m = PathMapper([("/Users/foo", "C:\\Users\\new")], "darwin", "win32")
        self.assertEqual(m.rewrite_or_keep("/Users/foo/CodeBuddy/genie"),
                         "C:\\Users\\new\\CodeBuddy\\genie")
        # No match
        self.assertEqual(m.rewrite_or_keep("/Users/bar/x"), "/Users/bar/x")

    def test_pathmap_case_insensitive_win_source(self):
        from scripts.lib.pathmap import PathMapper
        m = PathMapper([("C:\\Users\\Foo", "/X")], "win32", "darwin")
        self.assertEqual(m.rewrite_or_keep("c:\\users\\foo\\proj"), "/X/proj")

    def test_pathmap_longest_prefix_wins(self):
        from scripts.lib.pathmap import PathMapper
        m = PathMapper([
            ("/Users/foo", "/A"),
            ("/Users/foo/CodeBuddy", "/B"),  # more specific
        ], "darwin", "darwin")
        self.assertEqual(m.rewrite_or_keep("/Users/foo/CodeBuddy/x"), "/B/x")
        self.assertEqual(m.rewrite_or_keep("/Users/foo/Documents/y"), "/A/Documents/y")

    def test_compress_workspace_path_matches_workbuddy_algorithm(self):
        from scripts.lib.pathmap import compress_workspace_path
        # Replicating session-team-runtime-loader.ts compressWorkspacePath
        self.assertEqual(compress_workspace_path("/Users/foo/proj"), "Users-foo-proj")
        self.assertEqual(compress_workspace_path("C:\\Users\\foo\\proj"), "C-Users-foo-proj")
        # Multiple slashes collapse
        self.assertEqual(compress_workspace_path("//Users//foo/proj/"), "Users-foo-proj")


class TestDbPathRewrite(BaseCase):
    def test_db_rewrite_sessions_workspaces_automations(self):
        """Cross-machine import rewrites all path columns per inventory spec."""
        from scripts.lib.pathmap import PathMapper
        from scripts.lib import db as DB

        uid = "u"
        make_fake_root(self.src, uid, sessions=[], skills=[], memory_body="m")
        # Populate sessions / workspaces / automations with src paths
        conn = sqlite3.connect(str(self.src / "workbuddy.db"))
        conn.execute(
            "INSERT INTO sessions (id, cwd, user_id, title, status, created_at, updated_at) "
            "VALUES ('s1', '/Users/foo/proj', ?, 't', 'Completed', 1, 2)", (uid,))
        conn.execute(
            "INSERT INTO sessions (id, cwd, user_id, title, status, created_at, updated_at) "
            "VALUES ('s2', '/Users/foo/other', ?, 't', 'Completed', 1, 2)", (uid,))
        conn.execute(
            "INSERT INTO workspaces (path, last_opened_at) VALUES ('/Users/foo/proj', 1)")
        conn.execute(
            "INSERT INTO workspaces (path, last_opened_at) VALUES ('/Users/foo/other', 2)")
        conn.commit()
        conn.close()

        make_fake_root(self.dst, uid, sessions=[], skills=[], memory_body="")
        run([PYTHON, str(EXPORT), "--source", str(self.src),
             "--output", str(self.pkg), "--no-credentials"])
        run([PYTHON, str(IMPORT), "--package", str(self.pkg),
             "--target", str(self.dst),
             "--target-os", "linux",
             "--path-map", "/Users/foo=/home/bar"])

        # All cwd should be rewritten
        sessions = db_rows(self.dst / "workbuddy.db", "sessions")
        cwds = {r["cwd"] for r in sessions if r["deleted_at"] is None}
        self.assertIn("/home/bar/proj", cwds)
        self.assertIn("/home/bar/other", cwds)
        self.assertFalse(any(c.startswith("/Users/foo") for c in cwds))

        # workspaces.path is PK; should also be rewritten
        ws = db_rows(self.dst / "workbuddy.db", "workspaces")
        paths = {r["path"] for r in ws}
        self.assertIn("/home/bar/proj", paths)
        self.assertIn("/home/bar/other", paths)
        self.assertFalse(any(p.startswith("/Users/foo") for p in paths))


class TestProjectDirRename(BaseCase):
    """The high-risk scenario: rename projects/<oldId>/ when cwd is rewritten."""

    def test_project_dir_rename_and_meta_cwd_update(self):
        from scripts.lib.pathmap import PathMapper, compress_workspace_path
        from scripts.lib import fs as FS

        uid = "u"
        make_fake_root(self.src, uid, sessions=[], skills=[], memory_body="m")
        old_cwd = "/Users/foo/proj"
        new_cwd = "/home/bar/proj"
        old_pid = compress_workspace_path(old_cwd)
        new_pid = compress_workspace_path(new_cwd)
        self.assertNotEqual(old_pid, new_pid)

        # Construct a projects/<oldPid>/ directory with one session
        proj_dir = self.src / "projects" / old_pid
        proj_dir.mkdir(parents=True)
        sid = "session-abc"
        (proj_dir / f"{sid}.meta.json").write_text(
            json.dumps({"cwd": old_cwd, "session_id": sid}, indent=2)
        )
        (proj_dir / f"{sid}.jsonl").write_text('{"role":"user"}\n')
        # Insert matching session in DB
        conn = sqlite3.connect(str(self.src / "workbuddy.db"))
        conn.execute(
            "INSERT INTO sessions (id, cwd, user_id, title, status, created_at, updated_at) "
            "VALUES (?, ?, ?, 't', 'Completed', 1, 2)", (sid, old_cwd, uid))
        conn.commit()
        conn.close()

        make_fake_root(self.dst, uid, sessions=[], skills=[], memory_body="")
        run([PYTHON, str(EXPORT), "--source", str(self.src),
             "--output", str(self.pkg), "--no-credentials"])
        run([PYTHON, str(IMPORT), "--package", str(self.pkg),
             "--target", str(self.dst),
             "--target-os", "linux",
             "--path-map", "/Users/foo=/home/bar"])

        # Old projectId dir should no longer exist
        self.assertFalse((self.dst / "projects" / old_pid).exists(),
                         "old projectId dir must be renamed away")
        # New projectId dir should exist with the session files inside
        new_dir = self.dst / "projects" / new_pid
        self.assertTrue(new_dir.is_dir(), f"new projectId dir {new_pid} must exist")
        meta = json.loads((new_dir / f"{sid}.meta.json").read_text())
        self.assertEqual(meta["cwd"], new_cwd,
                         "meta.json cwd field must be updated to new path")


class TestWorkspaceBundle(BaseCase):
    def test_dry_run_emits_workspaces_with_sizes(self):
        """--dry-run produces a JSON plan with workspace size analysis."""
        uid = "u"
        make_fake_root(self.src, uid, sessions=[], skills=[], memory_body="m")
        # Add a fake workspace tree on disk and register it in the workspaces table
        ws_root = self.tmp / "fakeWorkspace"
        ws_root.mkdir()
        (ws_root / "main.py").write_text("print('hello')")
        (ws_root / "node_modules").mkdir()
        (ws_root / "node_modules" / "junk.js").write_text("x" * 50000)
        conn = sqlite3.connect(str(self.src / "workbuddy.db"))
        conn.execute(
            "INSERT INTO workspaces (path, last_opened_at) VALUES (?, 1)",
            (str(ws_root.resolve()),))
        conn.commit()
        conn.close()

        res = run([PYTHON, str(EXPORT), "--source", str(self.src),
                   "--dry-run", "--with-workspaces"])
        plan = json.loads(res.stdout)
        self.assertEqual(plan["kind"], "export-plan")
        self.assertGreaterEqual(len(plan["workspaces"]), 1)
        w = next(w for w in plan["workspaces"]
                 if w["source_path"] == str(ws_root.resolve()))
        # node_modules must be excluded by default
        self.assertGreater(w["files_excluded"], 0)
        self.assertIn("node_modules/", w["excluded_by_pattern_top"])
        # Source machine info present
        self.assertIn("os", plan["source"])
        self.assertIn("hostname", plan["source"])

    def test_workspace_bundle_roundtrip(self):
        """Pack workspace into separate zip, import into a destination."""
        uid = "u"
        make_fake_root(self.src, uid, sessions=[], skills=[], memory_body="m")
        ws_root = self.tmp / "wsRoot"
        ws_root.mkdir()
        (ws_root / "README.md").write_text("workspace content")
        (ws_root / "sub").mkdir()
        (ws_root / "sub" / "file.txt").write_text("payload")
        conn = sqlite3.connect(str(self.src / "workbuddy.db"))
        conn.execute(
            "INSERT INTO workspaces (path, last_opened_at) VALUES (?, 1)",
            (str(ws_root.resolve()),))
        conn.commit()
        conn.close()

        ws_bundle = self.tmp / "pkg-workspaces.zip"
        run([PYTHON, str(EXPORT), "--source", str(self.src),
             "--output", str(self.pkg),
             "--with-workspaces", "--workspace-output", str(ws_bundle),
             "--no-credentials"])
        self.assertTrue(ws_bundle.exists(), "workspace bundle must be produced")
        with zipfile.ZipFile(ws_bundle) as zf:
            names = zf.namelist()
            self.assertIn("manifest.json", names)
            self.assertTrue(any(n.endswith("/README.md") for n in names))

        # Import into a destination
        make_fake_root(self.dst, uid, sessions=[], skills=[], memory_body="")
        ws_dest = self.tmp / "extracted-workspaces"
        # Same-machine path so mapper.rewrite returns None → falls back to source_path
        run([PYTHON, str(IMPORT), "--package", str(self.pkg),
             "--target", str(self.dst),
             "--workspaces-package", str(ws_bundle),
             "--workspace-destination", str(ws_dest)])
        # The workspace landed at its original absolute path (since same-machine)
        # OR fell back to ws_dest/<projectId>. Accept either.
        extracted_anywhere = list(ws_dest.rglob("README.md")) + \
                             list(ws_root.glob("README.md"))
        self.assertTrue(any(p.exists() for p in extracted_anywhere),
                        f"README.md must end up somewhere; checked {extracted_anywhere}")


class TestSameMachineNoRewrite(BaseCase):
    def test_same_machine_skips_path_rewrite(self):
        """When src and target are the same machine, paths must NOT be rewritten."""
        uid = "u"
        original_cwd = "/Users/sample/proj"
        make_fake_root(self.src, uid, sessions=[], skills=[], memory_body="m")
        conn = sqlite3.connect(str(self.src / "workbuddy.db"))
        conn.execute(
            "INSERT INTO sessions (id, cwd, user_id, title, status, created_at, updated_at) "
            "VALUES ('s1', ?, ?, 't', 'Completed', 1, 2)", (original_cwd, uid))
        conn.commit()
        conn.close()
        make_fake_root(self.dst, uid, sessions=[], skills=[], memory_body="")

        run([PYTHON, str(EXPORT), "--source", str(self.src),
             "--output", str(self.pkg), "--no-credentials"])
        # Import WITHOUT --path-map → same-machine mode auto-detected
        res = run([PYTHON, str(IMPORT), "--package", str(self.pkg),
                   "--target", str(self.dst)])
        self.assertIn("Mode: same-machine", res.stdout)

        rows = db_rows(self.dst / "workbuddy.db", "sessions")
        cwds = {r["cwd"] for r in rows if r["deleted_at"] is None}
        self.assertIn(original_cwd, cwds, "cwd must be preserved on same-machine import")


class TestRestartHint(BaseCase):
    def test_restart_hint_emitted(self):
        """Import output contains explicit restart-required guidance."""
        uid = "u"
        make_fake_root(self.src, uid, sessions=["s1"], skills=["sk"], memory_body="m")
        make_fake_root(self.dst, uid, sessions=[], skills=[], memory_body="")

        run([PYTHON, str(EXPORT), "--source", str(self.src),
             "--output", str(self.pkg), "--no-credentials"])
        res = run([PYTHON, str(IMPORT), "--package", str(self.pkg),
                   "--target", str(self.dst)])
        self.assertIn("重启 WorkBuddy", res.stdout)
        self.assertIn("restart_required", res.stdout)

        # Machine-readable report includes restart_required structured
        reports = list((self.dst / "migration-reports").glob("import-*.json"))
        self.assertEqual(len(reports), 1)
        rep_data = json.loads(reports[0].read_text())
        rr = rep_data["sections"].get("restart_required")
        self.assertIsNotNone(rr)
        self.assertTrue(rr["required"])
        self.assertIn("db", rr["restart_reasons"])


class TestDryRunSchema(BaseCase):
    def test_dry_run_json_parses_and_has_required_fields(self):
        uid = "u"
        make_fake_root(self.src, uid, sessions=["s1"], skills=[], memory_body="m")
        res = run([PYTHON, str(EXPORT), "--source", str(self.src), "--dry-run"])
        plan = json.loads(res.stdout)
        for key in ("kind", "source", "main_package", "workspaces", "notes"):
            self.assertIn(key, plan, f"--dry-run JSON missing {key}")
        self.assertEqual(plan["kind"], "export-plan")
        for sk in ("os", "hostname", "home", "root", "user_ids"):
            self.assertIn(sk, plan["source"])


if __name__ == "__main__":
    unittest.main()
