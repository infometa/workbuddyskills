#!/usr/bin/env python3
"""Named safety I/O facade for integrations; implementation lives in common.py."""
from common import (
    assert_project_input,
    assert_project_output,
    atomic_write_bytes,
    check_existing_components,
    is_reparse_point,
    safe_project_dir,
    safe_project_path,
    safe_source_scope,
    write_csv,
    write_json_atomic,
    write_text_atomic,
)

__all__ = [
    "assert_project_input", "assert_project_output", "atomic_write_bytes",
    "check_existing_components", "is_reparse_point", "safe_project_dir",
    "safe_project_path", "safe_source_scope", "write_csv", "write_json_atomic", "write_text_atomic",
]
