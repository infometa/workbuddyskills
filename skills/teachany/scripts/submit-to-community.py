#!/usr/bin/env python3
"""Compatibility wrapper for legacy TeachAny skill path.

Historically some users called:
  ~/.codebuddy/skills/teachany/scripts/submit-to-community.py

The real implementation belongs to the TeachAny repository root because it
needs repository workflows and community/pending context. This wrapper keeps
that legacy command working while the executable skill is consolidated under
./skill.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def find_repo() -> Path | None:
    env = os.environ.get("TEACHANY_REPO")
    candidates = []
    if env:
        candidates.append(Path(env).expanduser())
    candidates.extend([
        Path.home() / "CodeBuddy" / "一次函数" / "teachany-opensource",
        Path.home() / "teachany-opensource",
        Path.home() / "CodeBuddy" / "teachany-opensource",
        Path.home() / "WorkBuddy" / "teachany-opensource",
    ])
    for repo in candidates:
        if (repo / "scripts" / "submit-to-community.py").exists():
            return repo
    return None


def main() -> int:
    repo = find_repo()
    if repo is None:
        print("❌ 未找到 teachany-opensource 仓库，无法执行 submit-to-community.py", file=sys.stderr)
        print("   请设置 TEACHANY_REPO=/path/to/teachany-opensource 后重试。", file=sys.stderr)
        return 1
    script = repo / "scripts" / "submit-to-community.py"
    return subprocess.call([sys.executable, str(script), *sys.argv[1:]], cwd=str(repo))


if __name__ == "__main__":
    raise SystemExit(main())
