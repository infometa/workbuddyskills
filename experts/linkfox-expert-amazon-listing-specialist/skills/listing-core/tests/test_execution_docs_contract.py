#!/usr/bin/env python3
"""守住权威流程文档与实际脚本 CLI 的最小静态契约。"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


AGENT_ROOT = Path(__file__).resolve().parents[3]
REPO_ROOT = AGENT_ROOT.parents[1]
CORE_ROOT = Path(__file__).resolve().parents[1]
DEPENDENCIES = json.loads((AGENT_ROOT / "dependencies.json").read_text(encoding="utf-8"))
DOCS = [
    *sorted(AGENT_ROOT.glob("*.md")),
    *sorted(
        doc
        for skill_dir in (AGENT_ROOT / "skills").glob("listing-*")
        for doc in skill_dir.rglob("*.md")
    ),
]
SCRIPT_REF_RE = re.compile(r"skills/[\w.-]+/scripts/[\w./-]+")
COMMAND_RE = re.compile(r"python(?:3)?\s+(skills/[\w.-]+/scripts/[\w.-]+\.py|scripts/[\w.-]+\.py)\b")
FLAG_RE = re.compile(r"(?<!\w)(--[a-z0-9-]+)")
SUPPORTED_FLAG_RE = re.compile(r"['\"](--[a-z0-9-]+)(?:=)?['\"]")
DEPENDENCY_SCRIPT_RE = re.compile(r"<skill_path>/scripts/([\w.-]+)")


def _bash_commands(text: str) -> list[str]:
    commands: list[str] = []
    for block in re.findall(r"```bash\n(.*?)```", text, flags=re.DOTALL):
        current = ""
        for raw_line in block.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if current or line.startswith(("python ", "python3 ", "node ", "echo ")):
                part = line[:-1].strip() if line.endswith("\\") else line
                current = f"{current} {part}".strip()
                if not line.endswith("\\"):
                    commands.append(current)
                    current = ""
        if current:
            commands.append(current)
    return commands


def _dependency_script(dependency: dict, script_name: str) -> Path | None:
    for skills_root in (AGENT_ROOT / "skills", REPO_ROOT / "linkfoxagent-v2"):
        candidate = skills_root / dependency["name"] / "scripts" / script_name
        if candidate.is_file():
            return candidate
    return None


def _resolve_script(doc: Path, reference: str) -> Path:
    if reference.startswith("skills/"):
        return AGENT_ROOT / reference
    for parent in (doc.parent, *doc.parents):
        candidate = parent / reference
        if candidate.is_file():
            return candidate
        if parent == AGENT_ROOT:
            break
    script_name = Path(reference).name
    for dependency in DEPENDENCIES.get("skills", []):
        if f"scripts/{script_name}" not in str(dependency.get("invoked_via") or ""):
            continue
        candidate = _dependency_script(dependency, script_name)
        if candidate:
            return candidate
    return doc.parent / reference


class ExecutionDocsContractTest(unittest.TestCase):
    def test_artifact_saver_examples_select_one_input_mode(self) -> None:
        errors: list[str] = []
        for doc in DOCS:
            for command in _bash_commands(doc.read_text(encoding="utf-8")):
                if not re.search(r"save-(?:json|text)-artifact\.mjs", command):
                    continue
                modes = int("--stdin" in command) + int("--source" in command)
                if modes != 1:
                    errors.append(f"{doc.name}: saver command must select exactly one input mode")
        self.assertEqual(errors, [])

    def test_dependency_invocations_match_source_scripts(self) -> None:
        errors: list[str] = []
        for dependency in DEPENDENCIES.get("skills", []):
            invocation = str(dependency.get("invoked_via") or "")
            match = DEPENDENCY_SCRIPT_RE.search(invocation)
            if not match:
                continue
            if "[--" in invocation or "[<" in invocation:
                errors.append(f"{dependency['name']}: ambiguous optional-argument syntax")
            script = _dependency_script(dependency, match.group(1))
            if not script:
                errors.append(f"{dependency['name']}: script not found: {match.group(1)}")
                continue
            supported = set(SUPPORTED_FLAG_RE.findall(script.read_text(encoding="utf-8")))
            unknown = sorted(set(FLAG_RE.findall(invocation)) - supported)
            if unknown:
                errors.append(f"{dependency['name']}: unsupported flags: {unknown}")
        self.assertEqual(errors, [])

    def test_all_internal_hot_path_script_references_exist(self) -> None:
        missing: list[str] = []
        for doc in DOCS:
            for reference in SCRIPT_REF_RE.findall(doc.read_text(encoding="utf-8")):
                if not (AGENT_ROOT / reference.rstrip(".,;:)")).is_file():
                    missing.append(f"{doc.name}: {reference}")
        self.assertEqual(missing, [])

    def test_bash_examples_use_declared_cli_flags(self) -> None:
        errors: list[str] = []
        for doc in DOCS:
            text = doc.read_text(encoding="utf-8")
            self.assertNotIn("[--", text, doc.as_posix())
            for command in _bash_commands(text):
                match = COMMAND_RE.search(command)
                if not match:
                    continue
                script = _resolve_script(doc, match.group(1))
                if not script.is_file():
                    errors.append(f"{doc.name}: script not found: {match.group(1)}")
                    continue
                supported = set(SUPPORTED_FLAG_RE.findall(script.read_text(encoding="utf-8")))
                unknown = sorted(set(FLAG_RE.findall(command)) - supported)
                if unknown:
                    errors.append(f"{doc.name}: {script.name}: {unknown}")
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
