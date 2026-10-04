#!/usr/bin/env python3
from __future__ import annotations
import os, sys, unittest
from pathlib import Path
CORE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CORE_ROOT / "scripts"))
from linkfox_paths import writable_root  # noqa: E402

class TestWritableRoot(unittest.TestCase):
    def test_returns_writable_abs_dir(self):
        d = writable_root()
        self.assertTrue(os.path.isabs(d) and os.access(d, os.W_OK))

    def test_env_override_wins_when_writable(self):
        os.environ["LISTING_WORKSPACE"] = os.path.dirname(__file__)
        try:
            self.assertEqual(writable_root(), os.path.dirname(__file__))
        finally:
            del os.environ["LISTING_WORKSPACE"]

if __name__ == "__main__":
    unittest.main()
