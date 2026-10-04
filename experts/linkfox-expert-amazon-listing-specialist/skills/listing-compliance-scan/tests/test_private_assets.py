import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from private_assets import ENV_PRIVATE_ASSETS_DIR, private_assets_dir  # noqa: E402


class PrivateAssetsTest(unittest.TestCase):
    def test_default_assets_are_outside_the_skill_tree(self):
        resolved = private_assets_dir()
        self.assertEqual(
            resolved,
            ROOT.parent / "_listing-private-assets" / "data",
        )
        self.assertFalse(resolved.is_relative_to(ROOT))
        self.assertFalse((ROOT / "data").exists())
        self.assertFalse((resolved.parent / "SKILL.md").exists())

    def test_environment_override_supports_isolated_runtime_mounts(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {ENV_PRIVATE_ASSETS_DIR: temp_dir}):
                self.assertEqual(private_assets_dir(), Path(temp_dir).resolve())

if __name__ == "__main__":
    unittest.main()
