#!/usr/bin/env python3
"""Regression tests for skill_ops.py using temporary directories only."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

import skill_ops


def write_skill(root: Path, name: str, version: str = "1.0.0", script: str | None = None) -> Path:
    skill = root / name
    skill.mkdir(parents=True)
    content = "\n".join(
        [
            "---",
            f"name: {name}",
            'description: "用于回归测试的完整 Skill。用户说测试技能时触发，提供确定性输出和边界校验。"',
            f"version: {version}",
            "agent_created: true",
            "---",
            "",
            "# 回归测试 Skill",
            "",
            "1. 接收输入。",
            "2. 输出确定结果。",
            "",
        ]
    )
    (skill / "SKILL.md").write_text(content, encoding="utf-8")
    if script is not None:
        scripts = skill / "scripts"
        scripts.mkdir()
        (scripts / "main.py").write_text(script, encoding="utf-8")
    return skill


def degradation(capability: str) -> dict[str, str]:
    return {
        "capability": capability,
        "trigger": "credential missing or service unavailable",
        "fallback": "use user-provided trusted data",
        "user_input": "exported data",
        "limitations": "not live",
        "evidence_label": "部分验证",
        "recovery": "configure credential and rerun environment check",
        "stop_condition": "no trusted data is available",
    }


def add_dependency_manifest(skill: Path, *, required: bool = True, requires_login: bool = False) -> None:
    scripts = skill / "scripts"
    references = skill / "references"
    scripts.mkdir(exist_ok=True)
    references.mkdir(exist_ok=True)
    (scripts / "check_environment.py").write_text("print('ready')\n", encoding="utf-8")
    setup = {
        "official_home_url": "https://service.example.org",
        "official_docs_url": "https://docs.example.org/service",
        "steps": ["Open the official console", "Create a read-only credential"],
        "verify": "Run the read-only status check",
        "security": "Store credentials outside source code",
        "verified_at": "2026-08-10",
        "applies_to_version": "current cloud service",
    }
    auth_type = "token" if requires_login else "none"
    if requires_login:
        setup.update({
            "login_url": "https://service.example.org/login",
            "credential_url": "https://service.example.org/settings/keys",
            "console_path": ["Settings", "Developer", "API Keys"],
            "credential_storage": "environment variable EXAMPLE_TOKEN",
            "rotate_or_revoke": "Delete the token in the official console",
            "scopes": ["data:read"],
        })
    guide_lines = [
        "# Setup Guide", "", "## example-service",
        "Use the official service page and documentation listed below.",
        "Install the supported client, sign in at the official login page, open Settings, Developer, API Keys, and create a read-only credential.",
        "Store the credential in the EXAMPLE_TOKEN environment variable. Never paste it into chat, source code, logs, or reports.",
        "Run the read-only verification probe. If authentication fails, rotate or delete the key in the official console and create a replacement.",
    ]
    guide_lines.extend(f"- {key}: {value}" for key, value in setup.items() if isinstance(value, str) and value.startswith("https://"))
    (references / "setup-guide.md").write_text("\n".join(guide_lines) + "\n", encoding="utf-8")
    manifest = {
        "schema_version": "1",
        "capabilities": ["query-data"],
        "dependencies": [{
            "id": "example-service",
            "type": "api",
            "required": required,
            "auth_type": auth_type,
            "capabilities": ["query-data"],
            "checks": ([{"id": "credential", "type": "env", "required": required, "name": "EXAMPLE_TOKEN"}, {"id": "auth-probe", "type": "auth_probe", "required": True, "target": "example-service"}] if requires_login else [{"id": "configuration", "type": "file", "required": required, "path": "~/.example-config"}]),
            "setup": setup,
            "degradation": [degradation("query-data")],
        }],
        "functional_degradations": [degradation("query-data")],
    }
    (skill / "skill-dependencies.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def render_args(root: Path, *, requirements: bool, write: bool, resources: Path | None = None) -> argparse.Namespace:
    body = root / "body.md"
    body.write_text("# Example\n\n1. Return a result.\n", encoding="utf-8")
    return argparse.Namespace(
        name="rendered-skill",
        description="用于测试 render 和 package。用户说创建回归 Skill 时触发并输出确定结果。",
        body_file=body,
        resources_dir=resources,
        output_dir=root / "out",
        version="1.0.0",
        requirements_confirmed=requirements,
        write_confirmed=write,
    )


def run_environment_checker(manifest: dict[str, object], env: dict[str, str] | None = None, probe_results: dict[str, object] | None = None) -> tuple[int, dict[str, object]]:
    with tempfile.TemporaryDirectory() as raw:
        manifest_path = Path(raw) / "skill-dependencies.json"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        checker = Path(__file__).resolve().parents[1] / "assets" / "dependency-kit" / "check_environment.py"
        command = [sys.executable, str(checker), "--manifest", str(manifest_path)]
        if probe_results is not None:
            probe_path = Path(raw) / "probe-results.json"
            probe_path.write_text(json.dumps(probe_results), encoding="utf-8")
            command.extend(["--probe-results", str(probe_path)])
        process = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            env=env or os.environ.copy(),
            check=False,
        )
        return process.returncode, json.loads(process.stdout)


def load_environment_checker_module():
    checker_path = Path(__file__).resolve().parents[1] / "assets" / "dependency-kit" / "check_environment.py"
    spec = importlib.util.spec_from_file_location("skill_smith_environment_checker", checker_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("无法加载环境检查器")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def checker_manifest(capability: str, dependency: dict[str, object]) -> dict[str, object]:
    return {
        "schema_version": "1",
        "capabilities": [capability],
        "dependencies": [dependency],
        "functional_degradations": [degradation(capability)],
    }


def checker_setup(auth: bool = False) -> dict[str, object]:
    setup: dict[str, object] = {
        "official_home_url": "https://example.org",
        "official_docs_url": "https://example.org/docs",
        "steps": ["Follow the official guide"],
        "verify": "Run a read-only probe",
        "security": "Never print credentials",
        "verified_at": "2026-08-10",
        "applies_to_version": "current",
    }
    if auth:
        setup.update({
            "login_url": "https://example.org/login",
            "credential_url": "https://example.org/keys",
            "console_path": ["Settings", "API Keys"],
            "credential_storage": "environment variable",
            "rotate_or_revoke": "Delete the credential in the official console",
            "scopes": ["data:read"],
        })
    return setup


class SkillOpsTests(unittest.TestCase):
    def test_validate_valid_skill(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            skill = write_skill(Path(raw), "valid-skill")
            self.assertEqual(skill_ops.validate_skill(skill), [])

    def test_validate_dependency_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            skill = write_skill(Path(raw), "dependency-skill")
            add_dependency_manifest(skill, requires_login=True)
            self.assertEqual(skill_ops.validate_skill(skill), [])

    def test_validate_dependency_manifest_requires_login_urls_and_degradation(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            skill = write_skill(Path(raw), "invalid-dependency")
            add_dependency_manifest(skill, requires_login=True)
            manifest_path = skill / "skill-dependencies.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["dependencies"][0]["setup"].pop("login_url")
            manifest["dependencies"][0]["degradation"] = []
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            codes = {item.code for item in skill_ops.validate_skill(skill)}
            self.assertIn("dependency_auth_setup", codes)
            self.assertIn("dependency_degradation", codes)

    def test_validate_rejects_nested_reference(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            skill = write_skill(Path(raw), "nested-reference")
            references = skill / "references"
            references.mkdir()
            (references / "a.md").write_text("加载 @references/b.md", encoding="utf-8")
            (references / "b.md").write_text("# B", encoding="utf-8")
            codes = {item.code for item in skill_ops.validate_skill(skill)}
            self.assertIn("nested_reference", codes)

    def test_validate_rejects_platform_field_placeholder_and_short_description(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            skill = write_skill(Path(raw), "invalid-skill")
            text = (skill / "SKILL.md").read_text(encoding="utf-8")
            text = text.replace("agent_created: true\n", "")
            text = text.replace('description: "用于回归测试的完整 Skill。用户说测试技能时触发，提供确定性输出和边界校验。"', 'description: "太短"')
            text += "\n[TO" + "DO: fill this]\n"
            (skill / "SKILL.md").write_text(text, encoding="utf-8")
            codes = {item.code for item in skill_ops.validate_skill(skill)}
            self.assertTrue({"agent_created", "placeholder", "description"}.issubset(codes))

    def test_validate_rejects_non_strict_version(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            leading_zero = write_skill(root, "bad-version", "01.0.0")
            unicode_digit = write_skill(root, "unicode-version", "1１.0.0")
            self.assertIn("version", {item.code for item in skill_ops.validate_skill(leading_zero)})
            self.assertIn("version", {item.code for item in skill_ops.validate_skill(unicode_digit)})

    def test_render_requires_separate_confirmations(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self.assertNotEqual(skill_ops.command_render(render_args(root, requirements=True, write=False)), 0)
            self.assertFalse((root / "out" / "rendered-skill").exists())
            self.assertNotEqual(skill_ops.command_render(render_args(root, requirements=False, write=True)), 0)
            self.assertFalse((root / "out" / "rendered-skill").exists())

    def test_render_copies_complete_resources(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            resources = root / "resources"
            (resources / "scripts").mkdir(parents=True)
            (resources / "scripts" / "main.py").write_text("print('ok')\n", encoding="utf-8")
            args = render_args(root, requirements=True, write=True, resources=resources)
            self.assertEqual(skill_ops.command_render(args), 0)
            target = root / "out" / "rendered-skill"
            self.assertTrue((target / "scripts" / "main.py").is_file())
            self.assertEqual(skill_ops.validate_skill(target), [])

    def test_environment_checker_ready_skips_setup(self) -> None:
        dependency = {
            "id": "python-runtime",
            "type": "runtime",
            "required": True,
            "auth_type": "none",
            "capabilities": ["run"],
            "checks": [{"id": "python", "type": "python", "required": True, "min_version": "3.10"}],
            "setup": checker_setup(),
            "degradation": [degradation("run")],
        }
        code, output = run_environment_checker(checker_manifest("run", dependency))
        self.assertEqual(code, 0)
        self.assertEqual(output["status"], "ready")
        self.assertIn("跳过配置引导", output["next_action"])
        self.assertNotIn("setup", output["dependencies"][0])
        self.assertEqual(output["functional_degradations"], [])

    def test_environment_checker_needs_setup_for_required_env(self) -> None:
        dependency = {
            "id": "required-api",
            "type": "api",
            "required": True,
            "auth_type": "token",
            "capabilities": ["query"],
            "checks": [{"id": "token", "type": "env", "required": True, "name": "SKILL_SMITH_MISSING_TOKEN"}, {"id": "auth-probe", "type": "auth_probe", "required": True, "target": "example-service"}],
            "setup": checker_setup(True),
            "degradation": [degradation("query")],
        }
        env = os.environ.copy()
        env.pop("SKILL_SMITH_MISSING_TOKEN", None)
        code, output = run_environment_checker(checker_manifest("query", dependency), env)
        self.assertEqual(code, 1)
        self.assertEqual(output["status"], "needs_setup")
        self.assertIn("setup", output["dependencies"][0])

    def test_environment_checker_partial_for_optional_env(self) -> None:
        dependency = {
            "id": "optional-api",
            "type": "api",
            "required": False,
            "auth_type": "token",
            "capabilities": ["enhance"],
            "checks": [{"id": "token", "type": "env", "required": False, "name": "SKILL_SMITH_OPTIONAL_TOKEN"}, {"id": "auth-probe", "type": "auth_probe", "required": True, "target": "example-service"}],
            "setup": checker_setup(True),
            "degradation": [degradation("enhance")],
        }
        env = os.environ.copy()
        env.pop("SKILL_SMITH_OPTIONAL_TOKEN", None)
        code, output = run_environment_checker(checker_manifest("enhance", dependency), env)
        self.assertEqual(code, 0)
        self.assertEqual(output["status"], "partial")
        self.assertNotIn("setup", output["dependencies"][0])
        self.assertIn("degradation", output["dependencies"][0])

    def test_environment_checker_unavailable_for_mcp_without_probe(self) -> None:
        dependency = {
            "id": "example-mcp",
            "type": "mcp",
            "required": True,
            "auth_type": "none",
            "capabilities": ["mcp-query"],
            "checks": [{"id": "mcp", "type": "mcp", "required": True, "server": "missing-server"}, {"id": "mcp-probe", "type": "mcp_probe", "required": True, "target": "example"}],
            "setup": checker_setup(),
            "degradation": [degradation("mcp-query")],
        }
        code, output = run_environment_checker(checker_manifest("mcp-query", dependency))
        self.assertNotEqual(code, 0)
        self.assertIn(output["status"], {"needs_setup", "unavailable"})

    def test_environment_checker_mcp_ready_after_host_probe(self) -> None:
        dependency = {
            "id": "example-mcp",
            "type": "mcp",
            "required": True,
            "auth_type": "none",
            "capabilities": ["mcp-query"],
            "checks": [{"id": "mcp", "type": "mcp", "required": True, "server": "example"}, {"id": "mcp-probe", "type": "mcp_probe", "required": True, "target": "example"}],
            "setup": checker_setup(),
            "degradation": [degradation("mcp-query")],
        }
        with tempfile.TemporaryDirectory() as raw:
            home = Path(raw)
            config = home / ".workbuddy" / "mcp.json"
            config.parent.mkdir()
            config.write_text(json.dumps({"mcpServers": {"example": {"command": "example"}}}), encoding="utf-8")
            env = os.environ.copy()
            env["HOME"] = str(home)
            env["USERPROFILE"] = str(home)
            code, output = run_environment_checker(checker_manifest("mcp-query", dependency), env, {"example-mcp": {"mcp-probe": {"check_type": "mcp_probe", "target": "example", "status": "ready", "reason_code": "ok", "checked_at": "2026-08-10T03:00:00Z"}}})
        self.assertEqual(code, 0)
        self.assertEqual(output["status"], "ready")

    def test_environment_checker_required_and_optional_checks(self) -> None:
        dependency = {
            "id": "mixed-checks",
            "type": "local-tool",
            "required": True,
            "auth_type": "none",
            "capabilities": ["mixed"],
            "checks": [
                {"id": "required", "type": "python", "required": True, "min_version": "3.10"},
                {"id": "optional", "type": "env", "required": False, "name": "SKILL_SMITH_OPTIONAL_MIXED"}
            ],
            "setup": checker_setup(True),
            "degradation": [degradation("mixed")],
        }
        code, output = run_environment_checker(checker_manifest("mixed", dependency))
        self.assertEqual(code, 0)
        self.assertEqual(output["status"], "partial")

    def test_environment_checker_rejects_unknown_capability(self) -> None:
        dependency = {
            "id": "python-runtime",
            "type": "runtime",
            "required": True,
            "auth_type": "none",
            "capabilities": ["run"],
            "checks": [{"id": "python", "type": "python", "required": True, "min_version": "3.10"}],
            "setup": checker_setup(),
            "degradation": [degradation("run")],
        }
        manifest = checker_manifest("run", dependency)
        with tempfile.TemporaryDirectory() as raw:
            manifest_path = Path(raw) / "manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            checker = Path(__file__).resolve().parents[1] / "assets" / "dependency-kit" / "check_environment.py"
            process = subprocess.run([sys.executable, str(checker), "--manifest", str(manifest_path), "--capability", "unknown"], stdout=subprocess.PIPE, text=True, encoding="utf-8", check=False)
            output = json.loads(process.stdout)
        self.assertEqual(process.returncode, 2)
        self.assertEqual(output["reason_code"], "manifest_error")

    def test_environment_checker_rejects_unsafe_cli_version_command(self) -> None:
        dependency = {
            "id": "unsafe-cli",
            "type": "cli",
            "required": True,
            "auth_type": "none",
            "capabilities": ["run-cli"],
            "checks": [{"id": "cli", "type": "cli", "required": True, "command": "python", "version_args": ["-c"]}],
            "setup": checker_setup(),
            "degradation": [degradation("run-cli")],
        }
        code, output = run_environment_checker(checker_manifest("run-cli", dependency))
        self.assertEqual(code, 2)
        self.assertEqual(output["reason_code"], "manifest_error")

    def test_environment_checker_configuration_recovery(self) -> None:
        dependency = {
            "id": "recover-api",
            "type": "api",
            "required": True,
            "auth_type": "token",
            "capabilities": ["recover"],
            "checks": [{"id": "token", "type": "env", "required": True, "name": "SKILL_SMITH_RECOVERY_TOKEN"}, {"id": "auth-probe", "type": "auth_probe", "required": True, "target": "example-service"}],
            "setup": checker_setup(True),
            "degradation": [degradation("recover")],
        }
        manifest = checker_manifest("recover", dependency)
        missing_env = os.environ.copy()
        missing_env.pop("SKILL_SMITH_RECOVERY_TOKEN", None)
        _, missing_output = run_environment_checker(manifest, missing_env)
        ready_env = missing_env.copy()
        ready_env["SKILL_SMITH_RECOVERY_TOKEN"] = "configured-not-printed"
        code, ready_output = run_environment_checker(manifest, ready_env, {"recover-api": {"auth-probe": {"check_type": "auth_probe", "target": "example-service", "status": "ready", "reason_code": "ok", "checked_at": "2026-08-10T03:00:00Z"}}})
        self.assertEqual(missing_output["status"], "needs_setup")
        self.assertEqual(code, 0)
        self.assertEqual(ready_output["status"], "ready")
        self.assertNotIn("configured-not-printed", json.dumps(ready_output))
        self.assertNotIn("setup", ready_output["dependencies"][0])

    def test_environment_checker_http_reason_codes(self) -> None:
        checker = load_environment_checker_module()
        item = {"url": "https://example.org/status", "method": "HEAD", "expected_status": [200]}
        cases = {401: "auth_expired_or_invalid", 403: "permission_denied", 429: "quota_or_rate_limit", 503: "service_error"}
        for status, expected in cases.items():
            error = checker.urllib.error.HTTPError(item["url"], status, "error", {}, None)
            with patch.object(checker.urllib.request, "urlopen", side_effect=error):
                result_status, reason = checker.url_probe(item, 1, 0)
            self.assertEqual(result_status, "unavailable")
            self.assertEqual(reason, expected)

    def test_preflight_detects_network_and_dynamic_execution(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            skill = write_skill(Path(raw), "unsafe-script", script="import socket\nvalue = eval('1 + 1')\n")
            scanned, findings, complete = skill_ops.preflight(skill)
            self.assertTrue(complete)
            self.assertEqual(scanned, ["scripts/main.py"])
            categories = {item.category for item in findings}
            self.assertTrue({"network", "dynamic_execution"}.issubset(categories))

    def test_preflight_detects_file_delete(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            skill = write_skill(Path(raw), "delete-script", script="from pathlib import Path\nPath('sample.txt').unlink()\n")
            _, findings, _ = skill_ops.preflight(skill)
            self.assertIn("file_delete", {item.category for item in findings})

    def test_preflight_fails_closed_for_unsupported_script(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            skill = write_skill(Path(raw), "unsupported-script")
            scripts = skill / "scripts"
            scripts.mkdir()
            (scripts / "payload.bin").write_bytes(b"binary")
            result = skill_ops.preflight_summary(skill)
            self.assertEqual(result["static_scan_status"], "blocked")
            self.assertFalse(result["execution_authorized"])
            self.assertIn("unsupported_script", {item["category"] for item in result["capabilities"]})

    def test_preflight_without_scripts_is_not_execution_authorization(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            skill = write_skill(Path(raw), "no-scripts")
            result = skill_ops.preflight_summary(skill)
            self.assertEqual(result["static_scan_status"], "not_applicable")
            self.assertFalse(result["execution_authorized"])

    def test_package_requires_write_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            skill = write_skill(root, "package-guard")
            archive = root / "package-guard.zip"
            args = argparse.Namespace(skill_dir=skill, output=archive, overwrite=False, packaged=False, risk_ack=None, write_confirmed=False)
            self.assertNotEqual(skill_ops.command_package(args), 0)
            self.assertFalse(archive.exists())

    def test_package_blocks_high_preflight_without_ack(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            skill = write_skill(root, "blocked-package", script="import socket\n")
            archive = root / "blocked-package.zip"
            args = argparse.Namespace(skill_dir=skill, output=archive, overwrite=False, packaged=False, risk_ack=None, write_confirmed=True)
            self.assertNotEqual(skill_ops.command_package(args), 0)
            self.assertFalse(archive.exists())

    def test_archive_names_reject_windows_illegal_character(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "archive-skill"
            root.mkdir()
            fake = root / "assets" / "a?.txt"
            with self.assertRaises(ValueError):
                skill_ops.safe_archive_names(root, [fake])

    def test_dependency_template_preflight_and_package(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            skill = write_skill(root, "dependency-template")
            add_dependency_manifest(skill, requires_login=True)
            trusted = Path(__file__).resolve().parents[1] / "assets" / "dependency-kit" / "check_environment.py"
            shutil.copy2(trusted, skill / "scripts" / "check_environment.py")
            preflight = skill_ops.preflight_summary(skill)
            self.assertEqual(preflight["static_scan_status"], "pass")
            archive = root / "dependency-template.zip"
            args = argparse.Namespace(skill_dir=skill, output=archive, overwrite=False, packaged=False, risk_ack=None, write_confirmed=True)
            self.assertEqual(skill_ops.command_package(args), 0)
            self.assertTrue(archive.is_file())
            with zipfile.ZipFile(archive) as bundle:
                checker_member = "dependency-template/scripts/check_environment.py"
                self.assertIn(checker_member, bundle.namelist())
                self.assertIn("dependency-template/skill-dependencies.json", bundle.namelist())
                self.assertIn("dependency-template/references/setup-guide.md", bundle.namelist())
                self.assertEqual(hashlib.sha256(bundle.read(checker_member)).hexdigest(), skill_ops.file_sha256(trusted))
                extracted = root / "extracted"
                bundle.extractall(extracted)
            extracted_skill = extracted / "dependency-template"
            probe = root / "probe.json"
            probe.write_text(json.dumps({"example-service": {"auth-probe": {"check_type": "auth_probe", "target": "example-service", "status": "ready", "reason_code": "ok", "checked_at": "2026-08-10T03:00:00Z"}}}), encoding="utf-8")
            env = os.environ.copy()
            env["EXAMPLE_TOKEN"] = "configured-not-printed"
            process = subprocess.run(
                [sys.executable, str(extracted_skill / "scripts" / "check_environment.py"), "--manifest", str(extracted_skill / "skill-dependencies.json"), "--probe-results", str(probe)],
                stdout=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                env=env,
                check=False,
            )
            self.assertEqual(process.returncode, 0)
            self.assertEqual(json.loads(process.stdout)["status"], "ready")

    def test_package_uses_valid_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            skill = write_skill(root, "package-snapshot", script="print('ok')\n")
            archive = root / "package-snapshot.zip"
            args = argparse.Namespace(skill_dir=skill, output=archive, overwrite=False, packaged=False, risk_ack=None, write_confirmed=True)
            self.assertEqual(skill_ops.command_package(args), 0)
            with zipfile.ZipFile(archive) as bundle:
                self.assertIsNone(bundle.testzip())
                self.assertIn("package-snapshot/SKILL.md", bundle.namelist())
                self.assertIn("package-snapshot/scripts/main.py", bundle.namelist())

    def test_backup_verifies_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            skill = write_skill(root, "backup-skill")
            cache = skill / "__pycache__"
            cache.mkdir()
            (cache / "helper.pyc").write_bytes(b"cache")
            archive = root / "backups" / "backup-skill-1.0.0.zip"
            args = argparse.Namespace(skill_dir=skill, output=archive, packaged=False, write_confirmed=True)
            self.assertEqual(skill_ops.command_backup(args), 0)
            self.assertTrue(archive.is_file())
            with zipfile.ZipFile(archive) as bundle:
                self.assertIsNone(bundle.testzip())
                self.assertFalse(any("__pycache__" in name for name in bundle.namelist()))

    def test_tree_digest_distinguishes_file_boundaries(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            left = root / "left"
            right = root / "right"
            left.mkdir()
            right.mkdir()
            (left / "a").write_bytes(b"\x00\x00\x00\x01bY")
            (right / "a").write_bytes(b"")
            (right / "b").write_bytes(b"Y")
            self.assertNotEqual(skill_ops.tree_digest(left), skill_ops.tree_digest(right))

    def test_copy_snapshot_rejects_link_like_entry(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            source = write_skill(root, "linked-skill")
            outside = root / "outside.txt"
            outside.write_text("secret", encoding="utf-8")
            link = source / "linked.txt"
            try:
                link.symlink_to(outside)
            except (OSError, NotImplementedError):
                self.skipTest("当前环境不允许创建测试软链接")
            with self.assertRaises(ValueError):
                skill_ops.copy_snapshot(source, root / "snapshot")

    def test_install_dry_run_first_install_and_update(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            home = root / "home"
            source = write_skill(root / "source", "installable-skill", "1.0.0", script="print('ok')\n")
            with patch.object(Path, "home", return_value=home):
                dry_run = argparse.Namespace(skill_dir=source, apply=False, risk_ack=None, install_confirmed=False)
                self.assertEqual(skill_ops.command_install(dry_run), 0)
                target = home / ".workbuddy" / "skills" / "installable-skill"
                self.assertFalse(target.exists())

                first = argparse.Namespace(skill_dir=source, apply=True, risk_ack=None, install_confirmed=True)
                self.assertEqual(skill_ops.command_install(first), 0)
                self.assertTrue(target.is_dir())

                text = (source / "SKILL.md").read_text(encoding="utf-8")
                (source / "SKILL.md").write_text(text.replace("version: 1.0.0", "version: 1.1.0"), encoding="utf-8")
                update = argparse.Namespace(skill_dir=source, apply=True, risk_ack=None, install_confirmed=True)
                self.assertEqual(skill_ops.command_install(update), 0)
                self.assertIn("version: 1.1.0", (target / "SKILL.md").read_text(encoding="utf-8"))
                backups = list((home / ".workbuddy" / ".skill-smith" / "backups").glob("installable-skill-1.0.0-*"))
                self.assertEqual(len(backups), 1)
                self.assertEqual(skill_ops.tree_digest(backups[0]), skill_ops.tree_digest(write_skill(root / "expected", "installable-skill", "1.0.0", script="print('ok')\n")))

    def test_install_rejects_non_incremented_version(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            home = root / "home"
            source = write_skill(root / "source", "same-version", "1.0.0")
            target = write_skill(home / ".workbuddy" / "skills", "same-version", "1.0.0")
            before = (target / "SKILL.md").read_bytes()
            with patch.object(Path, "home", return_value=home):
                args = argparse.Namespace(skill_dir=source, apply=True, risk_ack=None, install_confirmed=True)
                self.assertNotEqual(skill_ops.command_install(args), 0)
            self.assertEqual((target / "SKILL.md").read_bytes(), before)

    def test_install_rejects_concurrent_transaction_lock(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            home = root / "home"
            source = write_skill(root / "source", "locked-skill", "1.0.0")
            lock = home / ".workbuddy" / ".skill-smith" / "locks" / "locked-skill.lock"
            lock.parent.mkdir(parents=True)
            lock.write_text("other", encoding="ascii")
            with patch.object(Path, "home", return_value=home):
                args = argparse.Namespace(skill_dir=source, apply=True, risk_ack=None, install_confirmed=True)
                self.assertNotEqual(skill_ops.command_install(args), 0)
            self.assertEqual(lock.read_text(encoding="ascii"), "other")
            self.assertFalse((home / ".workbuddy" / "skills" / "locked-skill").exists())

    def test_install_rolls_back_after_post_validation_failure(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            home = root / "home"
            source = write_skill(root / "source", "rollback-skill", "1.1.0", script="print('new')\n")
            target = write_skill(home / ".workbuddy" / "skills", "rollback-skill", "1.0.0", script="print('old')\n")
            old_digest = skill_ops.tree_digest(target)
            real_validate = skill_ops.validate_skill

            def fail_installed(path: Path, *, require_agent_created: bool = True) -> list[skill_ops.Issue]:
                resolved = Path(path).resolve()
                expected = (home / ".workbuddy" / "skills" / "rollback-skill").resolve()
                if resolved == expected and resolved.exists() and "version: 1.1.0" in (resolved / "SKILL.md").read_text(encoding="utf-8"):
                    return [skill_ops.Issue("injected", "SKILL.md", None, "故障注入")]
                return real_validate(Path(path), require_agent_created=require_agent_created)

            with patch.object(Path, "home", return_value=home), patch.object(skill_ops, "validate_skill", side_effect=fail_installed):
                args = argparse.Namespace(skill_dir=source, apply=True, risk_ack=None, install_confirmed=True)
                self.assertNotEqual(skill_ops.command_install(args), 0)
            restored = home / ".workbuddy" / "skills" / "rollback-skill"
            self.assertEqual(skill_ops.tree_digest(restored), old_digest)
            failed = list((home / ".workbuddy" / ".skill-smith" / "failed").glob("rollback-skill-*"))
            self.assertEqual(len(failed), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
