#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import build_keyword_matrix  # noqa: E402
import score_keywords  # noqa: E402


class Response:
    def __init__(self, body: bytes):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self) -> bytes:
        return self.body


class ApiResponseHandlingTest(unittest.TestCase):
    def test_empty_sif_response_becomes_pipeline_error(self):
        with (
            patch.dict(os.environ, {"LINKFOX_AGENT_API_KEY": "test-key"}),
            patch.object(build_keyword_matrix, "urlopen", return_value=Response(b"")),
        ):
            result = build_keyword_matrix.call_sif_api(
                {"asin": "B000000001", "region": "US"}, score_keywords,
            )
        self.assertEqual(result["error"], "SIF returned an invalid JSON response")
        self.assertEqual(result["details"], "")

    def test_non_json_sellersprite_response_becomes_pipeline_error(self):
        with (
            patch.dict(os.environ, {"LINKFOX_AGENT_API_KEY": "test-key"}),
            patch.object(
                build_keyword_matrix,
                "urlopen",
                return_value=Response(b"<html>gateway error</html>"),
            ),
        ):
            result = build_keyword_matrix.call_sellersprite_api(
                {"asin": "B000000001", "region": "US"}, score_keywords,
            )
        self.assertEqual(
            result["error"], "SellerSprite returned an invalid JSON response",
        )
        self.assertIn("gateway error", result["details"])


if __name__ == "__main__":
    unittest.main()
