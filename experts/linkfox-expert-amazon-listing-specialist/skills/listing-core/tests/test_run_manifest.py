#!/usr/bin/env python3
from __future__ import annotations
import json, os, subprocess, sys, tempfile, unittest
from pathlib import Path
CORE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CORE_ROOT / "scripts"))
from run_manifest import (  # noqa: E402
    complete_timing,
    init_manifest,
    record_timing,
    set_final,
    update_stage,
)

class TestRunManifest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.run_dir = self.tmp.name
    def tearDown(self):
        self.tmp.cleanup()

    def test_init_creates_three_pending_stages(self):
        p = init_manifest(self.run_dir, "benchmark", {"insight": "standard", "keywords": "pro"})
        self.assertTrue(os.path.isabs(p))
        m = json.loads(Path(p).read_text())
        self.assertEqual(m["kind"], "listingRunManifest")
        self.assertEqual(m["schema_version"], 1)
        self.assertEqual([s["id"] for s in m["stages"]], ["facts", "insight", "write"])
        self.assertTrue(all(s["status"] == "pending" for s in m["stages"]))
        self.assertEqual(m["profile"]["keywords"], "pro")

    def test_update_stage_sets_status_and_artifacts(self):
        p = init_manifest(self.run_dir, "create", {"insight": "off", "keywords": "standard"})
        update_stage(p, "facts", "active")
        m = update_stage(p, "facts", "complete",
                         artifacts=[{"name": "product-facts.md", "path": "/abs/a.md", "kind": "markdown"}],
                         metrics={"product_detail_ms": 1194})
        facts = next(s for s in m["stages"] if s["id"] == "facts")
        self.assertEqual(facts["status"], "complete")
        self.assertEqual(facts["artifacts"][0]["name"], "product-facts.md")
        self.assertEqual(facts["attempts"], 1)
        self.assertGreaterEqual(facts["duration_ms"], 0)
        self.assertEqual(facts["metrics"]["product_detail_ms"], 1194)

    def test_reactivating_failed_stage_increments_attempts(self):
        p = init_manifest(self.run_dir, "rewrite", {})
        update_stage(p, "write", "active")
        update_stage(p, "write", "failed")
        m = update_stage(p, "write", "active")
        write = next(s for s in m["stages"] if s["id"] == "write")
        self.assertEqual(write["attempts"], 2)

    def test_update_rejects_bad_status_and_stage(self):
        p = init_manifest(self.run_dir, "rewrite", {})
        with self.assertRaises(ValueError):
            update_stage(p, "facts", "done")
        with self.assertRaises(ValueError):
            update_stage(p, "l3", "active")

    def test_reinit_preserves_progress_and_final(self):
        # 分段交付：S1 前先 init，run_full.py start 的二次 init 不得重置进度
        p = init_manifest(self.run_dir, "benchmark", {"profile": "standard"})
        first = json.loads(Path(p).read_text())
        update_stage(p, "facts", "complete",
                     artifacts=[{"name": "product-facts.md", "path": "/abs/a.md", "kind": "markdown"}],
                     activate="insight")
        set_final(p, listing_md="/abs/f.md")
        p2 = init_manifest(self.run_dir, "benchmark", {"profile": "standard", "marketplace": "US"})
        self.assertEqual(p, p2)
        m = json.loads(Path(p2).read_text())
        facts = next(s for s in m["stages"] if s["id"] == "facts")
        insight = next(s for s in m["stages"] if s["id"] == "insight")
        self.assertEqual(facts["status"], "complete")
        self.assertEqual(facts["artifacts"][0]["name"], "product-facts.md")
        self.assertEqual(insight["status"], "active")
        self.assertEqual(m["final"]["listing_md"], "/abs/f.md")
        self.assertEqual(m["profile"]["marketplace"], "US")
        self.assertEqual(m["created_at"], first["created_at"])
        self.assertEqual(m["timing"]["started_at"], first["timing"]["started_at"])
        self.assertEqual(
            m["timing"]["_started_at_epoch_ms"],
            first["timing"]["_started_at_epoch_ms"],
        )

    def test_records_substeps_and_total_wall_clock(self):
        p = init_manifest(self.run_dir, "benchmark", {})
        record_timing(p, "evidence_plan", "active")
        record_timing(p, "evidence_plan", "complete", duration_ms=12.6,
                      metrics={"cache_hits": 4})
        m = complete_timing(p)
        step = m["timing"]["steps"]["evidence_plan"]
        self.assertEqual(step["status"], "complete")
        self.assertEqual(step["duration_ms"], 13)
        self.assertEqual(step["metrics"]["cache_hits"], 4)
        self.assertIn("completed_at", m["timing"])
        self.assertGreaterEqual(m["timing"]["total_duration_ms"], 0)

    def test_update_activate_lights_next_stage_once(self):
        p = init_manifest(self.run_dir, "create", {})
        m = update_stage(p, "facts", "complete", activate="insight")
        insight = next(s for s in m["stages"] if s["id"] == "insight")
        self.assertEqual(insight["status"], "active")
        # 已推进的阶段不会被 activate 拉回 active
        update_stage(p, "insight", "complete")
        m = update_stage(p, "facts", "complete", activate="insight")
        insight = next(s for s in m["stages"] if s["id"] == "insight")
        self.assertEqual(insight["status"], "complete")
        with self.assertRaises(ValueError):
            update_stage(p, "facts", "complete", activate="nope")

    def test_set_final_records_paths(self):
        p = init_manifest(self.run_dir, "benchmark", {})
        m = set_final(p, listing_md="/abs/f.md", check_report="/abs/c.json")
        self.assertEqual(m["final"]["listing_md"], "/abs/f.md")

    def test_cli_update_with_relative_path_prints_absolute(self):
        """Verify that CLI update command prints absolute path even when given relative manifest path."""
        p = init_manifest(self.run_dir, "benchmark", {})
        saved_cwd = os.getcwd()
        try:
            os.chdir(self.run_dir)
            rel_manifest = "run-manifest.json"
            result = subprocess.run(
                ["python3", str(CORE_ROOT / "scripts" / "run_manifest.py"),
                 "update", "--manifest", rel_manifest, "--stage", "facts", "--status", "complete"],
                capture_output=True, text=True
            )
            self.assertEqual(result.returncode, 0)
            output = result.stdout.strip()
            self.assertTrue(output.startswith("Saved full response: /"))
            self.assertTrue(os.path.isabs(output.split("Saved full response: ")[1]))
        finally:
            os.chdir(saved_cwd)

if __name__ == "__main__":
    unittest.main()
