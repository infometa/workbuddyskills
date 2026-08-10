#!/usr/bin/env python3
"""Deterministic Skill creation, validation, preflight, packaging, backup, and installation."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
import unicodedata
import uuid
import zipfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
VERSION_RE = re.compile(r"^((?:0|[1-9][0-9]{0,5}))\.((?:0|[1-9][0-9]{0,5}))\.((?:0|[1-9][0-9]{0,5}))$", re.ASCII)
AT_REFERENCE_RE = re.compile(r"(?<![\w@])@((?:references|scripts|assets)/[A-Za-z0-9._/\\-]+)")
MARKDOWN_LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
PLACEHOLDER_RE = re.compile(
    r"\[TO" + r"DO(?:\]|:)|\bTO" + r"DO\s*:|your " + "logic here|replace with " + "actual",
    re.IGNORECASE,
)
HISTORY_RE = re.compile(r"^#{1,4}\s*(?:changelog|change log|更新记录|变更记录)\s*$", re.IGNORECASE | re.MULTILINE)
STATE_MARKER_RE = re.compile(r"[（(](?:已调整|已验证|已修复|\d+\.\d+(?:\.\d+)?\s*版本)[）)]")
ABSOLUTE_PATH_RE = re.compile(
    r"(?:[A-Za-z]:[\\/]" + "Users" + r"[\\/]|/" + "Users" + r"/|/" + "home" + r"/|/" + "tmp" + r"/)"
)
SECRET_RE = re.compile(
    r"AKIA[0-9A-Z]{16}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|"
    r"\b(?:sk|ghp|github_pat)_[A-Za-z0-9_-]{16,}\b"
)
ENCODED_BLOB_RE = re.compile(r"^[A-Za-z0-9+/=_-]{160,}$")

TEXT_SUFFIXES = {
    ".md", ".txt", ".py", ".pyw", ".json", ".yaml", ".yml", ".toml",
    ".ini", ".cfg", ".csv", ".tsv", ".sh", ".ps1", ".bat", ".cmd",
    ".js", ".mjs", ".cjs",
}
PYTHON_SUFFIXES = {".py", ".pyw"}
TEXT_SCRIPT_SUFFIXES = {"", ".sh", ".ps1", ".bat", ".cmd", ".js", ".mjs", ".cjs"}
EXCLUDED_DIRS = {
    ".git", ".hg", ".svn", "__pycache__", "node_modules", ".venv", "venv",
    ".pytest_cache", ".mypy_cache", ".ruff_cache", "dist",
}
EXCLUDED_FILES = {".DS_Store", "Thumbs.db"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".tmp", ".swp", ".swo"}
WINDOWS_RESERVED = {
    "CON", "PRN", "AUX", "NUL", "CLOCK$",
    *(f"COM{index}" for index in range(1, 10)),
    *(f"LPT{index}" for index in range(1, 10)),
}
MAX_FILES = 2000
MAX_SINGLE_FILE_BYTES = 50 * 1024 * 1024
MAX_TOTAL_BYTES = 100 * 1024 * 1024
REPARSE_ATTRIBUTE = 0x400


@dataclass(frozen=True)
class Issue:
    code: str
    path: str
    line: int | None
    message: str
    severity: str = "error"


@dataclass(frozen=True)
class Capability:
    category: str
    path: str
    line: int | None
    detail: str
    severity: str


def emit(payload: dict[str, Any], *, error: bool = False) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2), file=sys.stderr if error else sys.stdout)


def fail(message: str, code: int = 2) -> int:
    emit({"ok": False, "error": message}, error=True)
    return code


def parse_scalar(raw: str) -> Any:
    value = raw.strip()
    if not value:
        return ""
    if value.startswith('"') and value.endswith('"'):
        return json.loads(value)
    if value.startswith("'") and value.endswith("'"):
        return ast.literal_eval(value)
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    return value


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str, list[Issue]]:
    lines = text.splitlines()
    issues: list[Issue] = []
    if not lines or lines[0].strip() != "---":
        return {}, text, [Issue("frontmatter_missing", "SKILL.md", 1, "SKILL.md 必须以 frontmatter 开头")]
    end = next((index for index in range(1, len(lines)) if lines[index].strip() == "---"), None)
    if end is None:
        return {}, "", [Issue("frontmatter_unclosed", "SKILL.md", 1, "frontmatter 缺少结束分隔符")]
    metadata: dict[str, Any] = {}
    for index in range(1, end):
        line = lines[index]
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            issues.append(Issue("frontmatter_invalid", "SKILL.md", index + 1, "frontmatter 仅支持顶层 key: value"))
            continue
        key, raw = line.split(":", 1)
        key = key.strip()
        if key in metadata:
            issues.append(Issue("frontmatter_duplicate", "SKILL.md", index + 1, f"字段重复：{key}"))
            continue
        try:
            metadata[key] = parse_scalar(raw)
        except (ValueError, SyntaxError) as exc:
            issues.append(Issue("frontmatter_value", "SKILL.md", index + 1, f"字段 {key} 无法解析：{exc}"))
    return metadata, "\n".join(lines[end + 1 :]), issues


def relative(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def is_link_like(path: Path) -> bool:
    if path.is_symlink():
        return True
    junction = getattr(path, "is_junction", None)
    if callable(junction) and junction():
        return True
    try:
        attributes = getattr(os.lstat(path), "st_file_attributes", 0)
    except OSError:
        return False
    return bool(attributes & REPARSE_ATTRIBUTE)


def iter_entries(root: Path) -> Iterable[Path]:
    stack = [root]
    while stack:
        current = stack.pop()
        entries = sorted(os.scandir(current), key=lambda item: item.name)
        for entry in entries:
            path = Path(entry.path)
            yield path
            if entry.is_dir(follow_symlinks=False) and not is_link_like(path):
                stack.append(path)


def iter_files(root: Path) -> Iterable[Path]:
    for path in iter_entries(root):
        if path.is_file() and not is_link_like(path):
            yield path


def line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def clean_markdown_target(raw: str) -> str:
    target = raw.strip()
    if target.startswith("<") and ">" in target:
        target = target[1 : target.index(">")]
    elif " " in target:
        target = target.split(None, 1)[0]
    return target.split("#", 1)[0].split("?", 1)[0].strip()


def validate_reference(root: Path, source: Path, target: str, line: int) -> Issue | None:
    if not target or target.startswith("#") or re.match(r"^(?:https?|mailto|tel|data):", target, re.I):
        return None
    candidate = (source.parent / target).resolve(strict=False)
    if not within(candidate, root):
        return Issue("reference_escape", relative(source, root), line, f"引用逃出 Skill 目录：{target}")
    if not candidate.exists():
        return Issue("dead_reference", relative(source, root), line, f"引用目标不存在：{target}")
    return None


def validate_dependency_manifest(root: Path) -> list[Issue]:
    manifest_path = root / "skill-dependencies.json"
    if not manifest_path.exists():
        return []
    issues: list[Issue] = []
    display = "skill-dependencies.json"
    if is_link_like(manifest_path) or not manifest_path.is_file():
        return [Issue("dependency_manifest", display, None, "依赖清单必须是普通 JSON 文件")]
    try:
        raw = manifest_path.read_text(encoding="utf-8-sig")
        data = json.loads(raw)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return [Issue("dependency_manifest", display, None, f"依赖清单无法解析：{exc}")]
    if SECRET_RE.search(raw):
        issues.append(Issue("dependency_secret", display, None, "依赖清单疑似包含真实凭据"))
    if not isinstance(data, dict) or data.get("schema_version") != "1":
        issues.append(Issue("dependency_schema", display, None, "schema_version 必须为字符串 1"))
        return issues
    top_allowed = {"schema_version", "capabilities", "dependencies", "functional_degradations"}
    dependency_allowed = {"id", "type", "required", "auth_type", "capabilities", "checks", "setup", "degradation"}
    check_allowed = {"id", "type", "required", "target", "command", "min_version", "name", "path", "field", "server", "url", "method", "expected_status"}
    setup_allowed = {"official_home_url", "official_docs_url", "download_url", "login_url", "credential_url", "console_path", "scopes", "credential_storage", "steps", "verify", "rotate_or_revoke", "security", "verified_at", "applies_to_version"}
    degradation_allowed = {"capability", "trigger", "fallback", "user_input", "limitations", "evidence_label", "recovery", "stop_condition"}
    evidence_labels = {"已验证", "部分验证", "推断", "未验证"}
    if set(data) - top_allowed:
        issues.append(Issue("dependency_unknown_field", display, None, f"未知顶层字段：{sorted(set(data) - top_allowed)}"))
    capabilities = data.get("capabilities")
    if not isinstance(capabilities, list) or not capabilities or not all(isinstance(item, str) and item.strip() for item in capabilities):
        issues.append(Issue("capabilities", display, None, "capabilities 必须是非空字符串数组"))
        declared_capabilities: set[str] = set()
    else:
        declared_capabilities = set(capabilities)
        if len(declared_capabilities) != len(capabilities):
            issues.append(Issue("capabilities_duplicate", display, None, "capabilities 不得重复"))
    degradation_fields = ("capability", "trigger", "fallback", "user_input", "limitations", "evidence_label", "recovery", "stop_condition")
    functional = data.get("functional_degradations")
    covered: set[str] = set()
    if not isinstance(functional, list) or not functional:
        issues.append(Issue("functional_degradations", display, None, "functional_degradations 必须是非空数组"))
    else:
        for index, item in enumerate(functional):
            prefix = f"functional_degradations[{index}]"
            if not isinstance(item, dict) or set(item) - degradation_allowed:
                issues.append(Issue("functional_degradation_item", display, None, f"{prefix} 必须是对象且不得含未知字段"))
                continue
            for field in degradation_fields:
                if not isinstance(item.get(field), str) or (field != "user_input" and not item[field].strip()):
                    issues.append(Issue("functional_degradation_field", display, None, f"{prefix}.{field} 必填"))
            if item.get("evidence_label") not in evidence_labels:
                issues.append(Issue("functional_degradation_label", display, None, f"{prefix}.evidence_label 无效"))
            if isinstance(item.get("capability"), str):
                covered.add(item["capability"])
    if declared_capabilities - covered:
        issues.append(Issue("functional_degradation_coverage", display, None, f"以下功能缺少普通功能降级：{sorted(declared_capabilities - covered)}"))
    if covered - declared_capabilities:
        issues.append(Issue("functional_degradation_unknown", display, None, f"普通功能降级引用未声明功能：{sorted(covered - declared_capabilities)}"))
    dependencies = data.get("dependencies")
    if not isinstance(dependencies, list):
        issues.append(Issue("dependency_list", display, None, "dependencies 必须是数组"))
        dependencies = []
    seen: set[str] = set()
    allowed_types = {"mcp", "cli", "api", "account", "local-tool", "runtime", "model", "network", "permission"}
    allowed_auth = {"none", "browser-login", "token", "api-key", "oauth", "service-account"}
    allowed_checks = {"cli", "cli_probe", "env", "file", "json_field", "mcp", "mcp_probe", "auth_probe", "python", "url"}
    guide_urls: set[str] = set()
    for index, dependency in enumerate(dependencies):
        prefix = f"dependencies[{index}]"
        if not isinstance(dependency, dict) or set(dependency) - dependency_allowed:
            issues.append(Issue("dependency_item", display, None, f"{prefix} 必须是对象且不得含未知字段"))
            continue
        dependency_id = dependency.get("id")
        if not isinstance(dependency_id, str) or not NAME_RE.fullmatch(dependency_id) or dependency_id in seen:
            issues.append(Issue("dependency_id", display, None, f"{prefix}.id 必须唯一且为 kebab-case"))
        else:
            seen.add(dependency_id)
        if dependency.get("type") not in allowed_types:
            issues.append(Issue("dependency_type", display, None, f"{prefix}.type 无效"))
        if dependency.get("auth_type") not in allowed_auth:
            issues.append(Issue("dependency_auth_type", display, None, f"{prefix}.auth_type 无效"))
        if not isinstance(dependency.get("required"), bool):
            issues.append(Issue("dependency_required", display, None, f"{prefix}.required 必须为布尔值"))
        dependency_capabilities = dependency.get("capabilities")
        if not isinstance(dependency_capabilities, list) or not dependency_capabilities:
            issues.append(Issue("dependency_capabilities", display, None, f"{prefix}.capabilities 必须是非空数组"))
        elif set(dependency_capabilities) - declared_capabilities:
            issues.append(Issue("dependency_capability_unknown", display, None, f"{prefix} 引用了未声明功能"))
        checks = dependency.get("checks")
        check_types: set[str] = set()
        required_check_count = 0
        if not isinstance(checks, list) or not checks:
            issues.append(Issue("dependency_checks", display, None, f"{prefix}.checks 必须是非空数组"))
        else:
            for check_index, check in enumerate(checks):
                check_prefix = f"{prefix}.checks[{check_index}]"
                if not isinstance(check, dict) or check.get("type") not in allowed_checks or set(check) - check_allowed:
                    issues.append(Issue("dependency_check", display, None, f"{check_prefix} 检查类型无效或含未知字段"))
                    continue
                check_types.add(check["type"])
                if not isinstance(check.get("id"), str) or not check["id"].strip():
                    issues.append(Issue("dependency_check_id", display, None, f"{check_prefix}.id 必填"))
                if not isinstance(check.get("required"), bool):
                    issues.append(Issue("dependency_check_required", display, None, f"{check_prefix}.required 必须为布尔值"))
                elif check["required"]:
                    required_check_count += 1
                if check.get("type") in {"auth_probe", "mcp_probe", "cli_probe"}:
                    if not isinstance(check.get("target"), str) or not check["target"].strip():
                        issues.append(Issue("dependency_probe_target", display, None, f"{check_prefix}.target 必填"))
                    if check.get("required") is not True:
                        issues.append(Issue("dependency_probe_required", display, None, f"关键探测 {check_prefix} 必须为 required"))
                if check.get("type") == "cli":
                    command = str(check.get("command", ""))
                    if not command or Path(command).name != command or "/" in command or "\\" in command or "version_args" in check or not re.fullmatch(r"[A-Za-z0-9._-]+", command):
                        issues.append(Issue("dependency_cli_command", display, None, f"{check_prefix} 只能检查安全 CLI 命令名是否存在"))
                if check.get("min_version") and not re.fullmatch(r"(?:0|[1-9][0-9]{0,5})(?:\.(?:0|[1-9][0-9]{0,5})){0,2}", str(check["min_version"])):
                    issues.append(Issue("dependency_check_version", display, None, f"{check_prefix}.min_version 无效"))
                if any(field in check for field in ("auth_env", "auth_header", "auth_scheme")):
                    issues.append(Issue("dependency_probe_secret", display, None, f"{check_prefix} 不得把环境变量凭据发送到清单 URL"))
        if dependency.get("required") is True and required_check_count == 0:
            issues.append(Issue("dependency_required_check", display, None, f"必需依赖 {prefix} 至少需要一个必需检查"))
        setup = dependency.get("setup")
        if not isinstance(setup, dict) or set(setup) - setup_allowed:
            issues.append(Issue("dependency_setup", display, None, f"{prefix}.setup 必须是对象且不得含未知字段"))
        else:
            required_setup = ("official_home_url", "official_docs_url", "steps", "verify", "security", "verified_at", "applies_to_version")
            for field in required_setup:
                value = setup.get(field)
                if field == "steps":
                    valid = isinstance(value, list) and bool(value)
                else:
                    valid = isinstance(value, str) and bool(value.strip())
                if not valid:
                    issues.append(Issue("dependency_setup_field", display, None, f"{prefix}.setup.{field} 必填"))
            for field in ("official_home_url", "official_docs_url", "download_url", "login_url", "credential_url"):
                value = setup.get(field)
                if value is not None:
                    if not isinstance(value, str) or not value.startswith("https://"):
                        issues.append(Issue("dependency_url", display, None, f"{prefix}.setup.{field} 必须是 HTTPS URL"))
                    else:
                        guide_urls.add(value)
            if isinstance(setup.get("verified_at"), str) and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", setup["verified_at"]):
                issues.append(Issue("dependency_verified_at", display, None, f"{prefix}.setup.verified_at 必须为 YYYY-MM-DD"))
            auth_type = dependency.get("auth_type")
            if auth_type != "none":
                for field in ("login_url", "console_path", "credential_storage", "rotate_or_revoke"):
                    value = setup.get(field)
                    valid = isinstance(value, list) and bool(value) if field == "console_path" else isinstance(value, str) and bool(value.strip())
                    if not valid:
                        issues.append(Issue("dependency_auth_setup", display, None, f"{prefix}.setup.{field} 对认证依赖必填"))
            if auth_type in {"token", "api-key", "oauth", "service-account"}:
                for field in ("credential_url", "scopes"):
                    value = setup.get(field)
                    valid = isinstance(value, list) and bool(value) if field == "scopes" else isinstance(value, str) and value.startswith("https://")
                    if not valid:
                        issues.append(Issue("dependency_credential_setup", display, None, f"{prefix}.setup.{field} 对凭据依赖必填"))
            if auth_type != "none" and "auth_probe" not in check_types:
                issues.append(Issue("dependency_auth_probe", display, None, f"认证依赖 {prefix} 必须包含 auth_probe"))
            if dependency.get("type") == "mcp" and not {"mcp", "mcp_probe"} <= check_types:
                issues.append(Issue("dependency_mcp_probe", display, None, f"MCP 依赖 {prefix} 必须同时包含注册检查和最小能力探测"))
            if dependency.get("type") == "cli" and not {"cli", "cli_probe"} <= check_types:
                issues.append(Issue("dependency_cli_probe", display, None, f"CLI 依赖 {prefix} 必须同时包含存在性检查和可信版本/状态探测"))
            if dependency.get("type") == "api" and not ({"url", "auth_probe"} & check_types):
                issues.append(Issue("dependency_api_probe", display, None, f"API 依赖 {prefix} 必须包含匿名健康探测或可信认证探测"))
        degradation = dependency.get("degradation")
        if not isinstance(degradation, list) or not degradation:
            issues.append(Issue("dependency_degradation", display, None, f"{prefix}.degradation 必须是非空数组"))
        else:
            dependency_degradation_capabilities: set[str] = set()
            for degradation_index, item in enumerate(degradation):
                degradation_prefix = f"{prefix}.degradation[{degradation_index}]"
                if not isinstance(item, dict) or set(item) - degradation_allowed:
                    issues.append(Issue("dependency_degradation_item", display, None, f"{degradation_prefix} 必须是对象且不得含未知字段"))
                    continue
                for field in degradation_fields:
                    if not isinstance(item.get(field), str) or (field != "user_input" and not item[field].strip()):
                        issues.append(Issue("dependency_degradation_field", display, None, f"{degradation_prefix}.{field} 必填"))
                if item.get("evidence_label") not in evidence_labels:
                    issues.append(Issue("dependency_degradation_label", display, None, f"{degradation_prefix}.evidence_label 无效"))
                if isinstance(item.get("capability"), str):
                    dependency_degradation_capabilities.add(item["capability"])
            if isinstance(dependency_capabilities, list):
                if dependency_degradation_capabilities - set(dependency_capabilities):
                    issues.append(Issue("dependency_degradation_unknown", display, None, f"{prefix}.degradation 引用未关联功能"))
                if set(dependency_capabilities) - dependency_degradation_capabilities:
                    issues.append(Issue("dependency_degradation_missing", display, None, f"{prefix}.capabilities 存在未覆盖降级的功能"))
    checker = root / "scripts" / "check_environment.py"
    guide = root / "references" / "setup-guide.md"
    if not checker.is_file() or is_link_like(checker):
        issues.append(Issue("dependency_checker", "scripts/check_environment.py", None, "依赖型 Skill 必须包含环境检查脚本"))
    if not guide.is_file() or is_link_like(guide):
        issues.append(Issue("dependency_guide", "references/setup-guide.md", None, "依赖型 Skill 必须包含配置指南"))
    else:
        try:
            guide_text = guide.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeError):
            guide_text = ""
        if len(guide_text.strip()) < 200:
            issues.append(Issue("dependency_guide_depth", "references/setup-guide.md", None, "配置指南过短，必须包含安装、登录、权限、存储、验证、轮换和撤销步骤"))
        for dependency_id in seen:
            if dependency_id not in guide_text:
                issues.append(Issue("dependency_guide_coverage", "references/setup-guide.md", None, f"配置指南未覆盖依赖 {dependency_id}"))
        for url in guide_urls:
            if url not in guide_text:
                issues.append(Issue("dependency_guide_url", "references/setup-guide.md", None, f"配置指南缺少清单中的官方 URL：{url}"))
    return issues


def validate_skill(skill_dir: Path, *, require_agent_created: bool = True) -> list[Issue]:
    root = skill_dir.expanduser()
    issues: list[Issue] = []
    if is_link_like(root) or not root.is_dir():
        return [Issue("skill_root", str(root), None, "Skill 路径不存在、不是目录或为链接/重解析点")]
    root = root.resolve()
    skill_file = root / "SKILL.md"
    if not skill_file.is_file() or is_link_like(skill_file):
        return [Issue("skill_file", "SKILL.md", None, "缺少普通文件 SKILL.md")]
    try:
        skill_text = skill_file.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as exc:
        return [Issue("skill_read", "SKILL.md", None, f"无法读取 SKILL.md：{exc}")]

    metadata, body, fm_issues = parse_frontmatter(skill_text)
    issues.extend(fm_issues)
    name = metadata.get("name")
    description = metadata.get("description")
    version = metadata.get("version")
    if not isinstance(name, str) or not NAME_RE.fullmatch(name) or len(name) > 64:
        issues.append(Issue("name", "SKILL.md", None, "name 必须为 1—64 字符 kebab-case"))
    elif name != root.name:
        issues.append(Issue("name_directory", "SKILL.md", None, f"name {name!r} 与目录名 {root.name!r} 不一致"))
    if not isinstance(description, str) or len(description.strip()) < 20 or len(description) > 1024:
        issues.append(Issue("description", "SKILL.md", None, "description 必须是 20—1024 字符完整描述"))
    if not isinstance(version, str) or not VERSION_RE.fullmatch(version):
        issues.append(Issue("version", "SKILL.md", None, "version 必须为严格 MAJOR.MINOR.PATCH，每段最多 6 位且无前导零"))
    if require_agent_created and metadata.get("agent_created") is not True:
        issues.append(Issue("agent_created", "SKILL.md", None, "WorkBuddy 本地模型创建 Skill 必须包含 agent_created: true"))
    if not body.strip():
        issues.append(Issue("body_empty", "SKILL.md", None, "正文不能为空"))
    if len(body.splitlines()) > 500:
        issues.append(Issue("body_length", "SKILL.md", None, "正文超过 500 行"))

    entry_count = 0
    total_bytes = 0
    try:
        for path in iter_entries(root):
            entry_count += 1
            if entry_count > MAX_FILES:
                issues.append(Issue("file_count", ".", None, f"文件与目录数量超过 {MAX_FILES}"))
                break
            if is_link_like(path):
                issues.append(Issue("link_like", relative(path, root), None, "Skill 包内禁止软链接、junction 和重解析点"))
            elif path.is_file():
                size = path.stat().st_size
                total_bytes += size
                if size > MAX_SINGLE_FILE_BYTES:
                    issues.append(Issue("file_size", relative(path, root), None, "单文件超过 50MB"))
                if total_bytes > MAX_TOTAL_BYTES:
                    issues.append(Issue("package_size", ".", None, "包体未压缩总量超过 100MB"))
                    break
    except OSError as exc:
        issues.append(Issue("walk_error", ".", None, f"无法完整遍历包体：{exc}"))

    try:
        files = list(iter_files(root))
    except OSError as exc:
        files = []
        issues.append(Issue("walk_error", ".", None, f"无法完整读取包体：{exc}"))
    for path in files:
        display = relative(path, root)
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeError) as exc:
            issues.append(Issue("text_read", display, None, f"无法按 UTF-8 读取：{exc}"))
            continue
        for match in PLACEHOLDER_RE.finditer(text):
            issues.append(Issue("placeholder", display, line_number(text, match.start()), "发现占位内容"))
        for match in STATE_MARKER_RE.finditer(text):
            issues.append(Issue("state_marker", display, line_number(text, match.start()), "发现修改状态标注"))
        if HISTORY_RE.search(text):
            issues.append(Issue("history_section", display, None, "发现 changelog 或变更记录章节"))
        for index, line in enumerate(text.splitlines(), 1):
            if ABSOLUTE_PATH_RE.search(line):
                issues.append(Issue("absolute_path", display, index, "发现具体用户绝对路径"))
        if path.suffix.lower() == ".md":
            for match in MARKDOWN_LINK_RE.finditer(text):
                target = clean_markdown_target(match.group(1))
                issue = validate_reference(root, path, target, line_number(text, match.start()))
                if issue:
                    issues.append(issue)
            for match in AT_REFERENCE_RE.finditer(text):
                target = match.group(1).replace("\\", "/")
                if path != skill_file:
                    issues.append(Issue("nested_reference", display, line_number(text, match.start()), "加载式引用只能出现在顶层 SKILL.md"))
                issue = validate_reference(root, path, target, line_number(text, match.start()))
                if issue:
                    issues.append(issue)
        if display.startswith("scripts/") and path.suffix.lower() in PYTHON_SUFFIXES:
            try:
                compile(path.read_bytes(), str(path), "exec")
            except SyntaxError as exc:
                issues.append(Issue("python_syntax", display, exc.lineno, exc.msg))
            except (OSError, UnicodeError, ValueError) as exc:
                issues.append(Issue("python_read", display, None, str(exc)))

    issues.extend(validate_dependency_manifest(root))
    unique = {(item.code, item.path, item.line, item.message): item for item in issues}
    return sorted(unique.values(), key=lambda item: (item.path, item.line or 0, item.code))


def command_validate(args: argparse.Namespace) -> int:
    issues = validate_skill(args.skill_dir, require_agent_created=not args.packaged)
    emit({"ok": not issues, "skill_dir": str(args.skill_dir), "issues": [asdict(item) for item in issues]})
    return 1 if issues else 0


def copy_snapshot(source: Path, destination: Path) -> tuple[int, int]:
    if is_link_like(source) or not source.is_dir():
        raise ValueError(f"源目录无效或为链接/重解析点：{source}")
    source = source.resolve()
    source_digest_before = tree_digest(source, skip_excluded=True)
    destination.mkdir(parents=True, exist_ok=False)
    file_count = 0
    total_bytes = 0

    def copy_dir(src: Path, dst: Path) -> None:
        nonlocal file_count, total_bytes
        if is_link_like(src) or not within(src.resolve(strict=True), source):
            raise ValueError(f"复制期间目录变为链接或逃出源目录：{src}")
        for entry in sorted(os.scandir(src), key=lambda item: item.name):
            src_path = Path(entry.path)
            if entry.name in EXCLUDED_DIRS or entry.name in EXCLUDED_FILES or src_path.suffix.lower() in EXCLUDED_SUFFIXES:
                continue
            if is_link_like(src_path):
                raise ValueError(f"拒绝复制链接、junction 或重解析点：{src_path}")
            dst_path = dst / entry.name
            if entry.is_dir(follow_symlinks=False):
                dst_path.mkdir()
                copy_dir(src_path, dst_path)
                continue
            if not entry.is_file(follow_symlinks=False):
                raise ValueError(f"拒绝复制非普通文件：{src_path}")
            size = src_path.stat().st_size
            file_count += 1
            total_bytes += size
            if file_count > MAX_FILES or size > MAX_SINGLE_FILE_BYTES or total_bytes > MAX_TOTAL_BYTES:
                raise ValueError("包体超过文件数或大小限制")
            flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
            fd = os.open(src_path, flags)
            try:
                with os.fdopen(fd, "rb", closefd=True) as source_file, open(dst_path, "xb") as target_file:
                    shutil.copyfileobj(source_file, target_file, length=1024 * 1024)
            except BaseException:
                try:
                    os.close(fd)
                except OSError:
                    pass
                raise
            shutil.copystat(src_path, dst_path, follow_symlinks=False)

    copy_dir(source, destination)
    source_digest_after = tree_digest(source, skip_excluded=True)
    snapshot_digest = tree_digest(destination, skip_excluded=True)
    if source_digest_before != source_digest_after or source_digest_after != snapshot_digest:
        raise ValueError("复制期间源目录发生变化，快照已拒绝")
    return file_count, total_bytes


def tree_digest(root: Path, *, skip_excluded: bool = False) -> str:
    digest = hashlib.sha256()
    files = sorted(iter_files(root), key=lambda item: item.relative_to(root).as_posix())
    for path in files:
        relative_path = path.relative_to(root)
        if skip_excluded and excluded(relative_path):
            continue
        rel = relative_path.as_posix().encode("utf-8")
        content_digest = hashlib.sha256()
        size = 0
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                size += len(chunk)
                content_digest.update(chunk)
        digest.update(b"F")
        digest.update(len(rel).to_bytes(4, "big"))
        digest.update(rel)
        digest.update(size.to_bytes(8, "big"))
        digest.update(content_digest.digest())
    return digest.hexdigest()


def command_render(args: argparse.Namespace) -> int:
    if not args.requirements_confirmed or not args.write_confirmed:
        return fail("render 要求同时传入 --requirements-confirmed 和 --write-confirmed")
    name = args.name.strip()
    if not NAME_RE.fullmatch(name) or len(name) > 64:
        return fail("name 必须为 1—64 字符 kebab-case")
    if not VERSION_RE.fullmatch(args.version):
        return fail("version 必须为严格 MAJOR.MINOR.PATCH")
    if len(args.description.strip()) < 20 or len(args.description) > 1024:
        return fail("description 必须为 20—1024 字符完整描述")
    if not args.body_file.is_file() or is_link_like(args.body_file):
        return fail(f"正文文件不存在或为链接：{args.body_file}")
    try:
        body = args.body_file.read_text(encoding="utf-8-sig").strip()
    except (OSError, UnicodeError) as exc:
        return fail(f"无法读取正文：{exc}")
    if not body or body.startswith("---"):
        return fail("正文必须非空且不能包含 frontmatter")
    if PLACEHOLDER_RE.search(body):
        return fail("正文包含占位内容")
    output_root = args.output_dir.expanduser()
    if output_root.exists() and is_link_like(output_root):
        return fail("输出父目录不能是链接或重解析点")
    output_root.mkdir(parents=True, exist_ok=True)
    output_root = output_root.resolve()
    target = output_root / name
    if target.exists() or is_link_like(target):
        return fail(f"目标已存在，拒绝覆盖：{target}")
    stage_root = Path(tempfile.mkdtemp(prefix=f".{name}-render-", dir=output_root))
    staged = stage_root / name
    try:
        staged.mkdir()
        document = "\n".join([
            "---", f"name: {name}",
            f"description: {json.dumps(args.description.strip(), ensure_ascii=False)}",
            f"version: {args.version}", "agent_created: true", "---", "", body, "",
        ])
        (staged / "SKILL.md").write_text(document, encoding="utf-8", newline="\n")
        if args.resources_dir:
            resources = args.resources_dir.expanduser()
            if is_link_like(resources) or not resources.is_dir():
                return fail("resources-dir 必须是普通目录")
            allowed = {"scripts", "references", "assets"}
            for entry in sorted(os.scandir(resources), key=lambda item: item.name):
                if entry.name not in allowed:
                    return fail(f"resources-dir 根目录只允许 scripts、references、assets：{entry.name}")
                copy_snapshot(Path(entry.path), staged / entry.name)
        issues = validate_skill(staged)
        if issues:
            emit({"ok": False, "error": "生成内容校验失败", "issues": [asdict(item) for item in issues]}, error=True)
            return 1
        os.rename(staged, target)
        emit({"ok": True, "skill": name, "path": str(target), "digest": tree_digest(target)})
        return 0
    finally:
        if stage_root.exists():
            shutil.rmtree(stage_root, ignore_errors=True)


def dotted_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = dotted_name(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    return ""


def scan_python(path: Path, display: str) -> list[Capability]:
    findings: list[Capability] = []
    try:
        text = path.read_text(encoding="utf-8-sig")
        tree = ast.parse(text, filename=str(path))
    except (OSError, UnicodeError, SyntaxError) as exc:
        return [Capability("parse_error", display, getattr(exc, "lineno", None), str(exc), "high")]
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            modules = [alias.name for alias in node.names] if isinstance(node, ast.Import) else [node.module or ""]
            for module in modules:
                root = module.split(".")[0]
                if root in {"requests", "httpx", "aiohttp", "urllib", "socket", "http", "ftplib", "smtplib"}:
                    findings.append(Capability("network", display, node.lineno, f"导入网络模块：{module}", "high"))
                if root in {"subprocess", "pty", "ctypes"}:
                    findings.append(Capability("subprocess_or_native", display, node.lineno, f"导入进程或本机接口模块：{module}", "high"))
                if root in {"base64", "marshal", "pickle", "dill"}:
                    findings.append(Capability("dynamic_or_encoded", display, node.lineno, f"导入编码或反序列化模块：{module}", "medium"))
        if isinstance(node, ast.Call):
            name = dotted_name(node.func)
            if name in {"eval", "exec", "builtins.eval", "builtins.exec", "__import__"}:
                findings.append(Capability("dynamic_execution", display, node.lineno, f"动态执行或导入：{name}", "high"))
            if name in {"os.system", "os.popen", "subprocess.run", "subprocess.Popen", "subprocess.call", "subprocess.check_output"}:
                findings.append(Capability("subprocess", display, node.lineno, f"子进程调用：{name}", "high"))
            delete_names = {"unlink", "remove", "rmdir", "rmtree", "removedirs"}
            mutation_names = {"write_text", "write_bytes", "mkdir", "makedirs", "rename", "replace", "move", "copy", "copy2", "copytree"}
            if name in delete_names or any(name.endswith(f".{item}") for item in delete_names):
                findings.append(Capability("file_delete", display, node.lineno, f"文件删除：{name}", "high"))
            if name in mutation_names or any(name.endswith(f".{item}") for item in mutation_names):
                findings.append(Capability("file_mutation", display, node.lineno, f"文件写入或移动：{name}", "medium"))
            if name in {"open", "io.open", "pathlib.Path.open", "os.open"}:
                findings.append(Capability("file_access", display, node.lineno, f"底层文件访问：{name}", "medium"))
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if SECRET_RE.search(node.value):
                findings.append(Capability("credential", display, getattr(node, "lineno", None), "发现疑似硬编码凭据", "high"))
            if ENCODED_BLOB_RE.fullmatch(node.value.strip()):
                findings.append(Capability("obfuscation", display, getattr(node, "lineno", None), "发现异常长编码数据", "high"))
    return findings


def scan_text_script(path: Path, display: str) -> list[Capability]:
    try:
        text = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as exc:
        return [Capability("parse_error", display, None, str(exc), "high")]
    rules = [
        ("network", "high", re.compile(r"\b(?:curl|wget|Invoke-WebRequest|Invoke-RestMethod|fetch|XMLHttpRequest)\b", re.I)),
        ("subprocess", "high", re.compile(r"\b(?:Start-Process|cmd(?:\.exe)?\s+/c|powershell(?:\.exe)?\s+-|bash\s+-c|sh\s+-c|child_process)\b", re.I)),
        ("dynamic_execution", "high", re.compile(r"\b(?:eval|Invoke-Expression|Function)\s*\(?", re.I)),
        ("file_delete", "high", re.compile(r"(?:\brm\s+(?:-[^\s]+\s+)?|\bdel\s+|\berase\s+|Remove-Item\b|find\b[^\n]*-delete\b|\bunlink\b)", re.I)),
        ("file_mutation", "medium", re.compile(r"\b(?:Set-Content|Add-Content|Out-File|Move-Item|Copy-Item|tee|dd|mv|cp)\b|(?:^|\s)>+\s*[^&]", re.I)),
        ("obfuscation", "high", re.compile(r"\b(?:FromBase64String|EncodedCommand|base64\s+(?:-d|--decode))\b", re.I)),
    ]
    findings: list[Capability] = []
    for index, line in enumerate(text.splitlines(), 1):
        for category, severity, pattern in rules:
            if pattern.search(line):
                findings.append(Capability(category, display, index, f"发现 {category} 能力", severity))
        if SECRET_RE.search(line):
            findings.append(Capability("credential", display, index, "发现疑似硬编码凭据", "high"))
    return findings


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def trusted_environment_checker_hash() -> str | None:
    trusted = Path(__file__).resolve().parents[1] / "assets" / "dependency-kit" / "check_environment.py"
    try:
        return file_sha256(trusted)
    except OSError:
        return None


def preflight(skill_dir: Path) -> tuple[list[str], list[Capability], bool]:
    root = skill_dir.expanduser()
    scanned: list[str] = []
    findings: list[Capability] = []
    complete = True
    if is_link_like(root) or not root.is_dir():
        return scanned, [Capability("input", str(root), None, "Skill 目录无效", "high")], False
    root = root.resolve()
    scripts = root / "scripts"
    if not scripts.exists():
        return scanned, findings, True
    if is_link_like(scripts):
        return scanned, [Capability("link_like", "scripts", None, "scripts 目录是链接或重解析点", "high")], False
    try:
        entries = list(iter_entries(scripts))
    except OSError as exc:
        return scanned, [Capability("scan_error", "scripts", None, f"无法完整扫描：{exc}", "high")], False
    for path in entries:
        if is_link_like(path):
            findings.append(Capability("link_like", relative(path, root), None, "脚本路径是链接或重解析点", "high"))
            complete = False
            continue
        if not path.is_file():
            continue
        display = relative(path, root)
        suffix = path.suffix.lower()
        if suffix in PYTHON_SUFFIXES:
            scanned.append(display)
            python_findings = scan_python(path, display)
            trusted_hash = trusted_environment_checker_hash()
            if display == "scripts/check_environment.py" and trusted_hash and file_sha256(path) == trusted_hash:
                python_findings = [
                    Capability(item.category, item.path, item.line, f"受信任环境检查模板：{item.detail}", "medium")
                    if item.category in {"network", "subprocess", "subprocess_or_native"}
                    else item
                    for item in python_findings
                ]
            findings.extend(python_findings)
        elif suffix in TEXT_SCRIPT_SUFFIXES:
            scanned.append(display)
            findings.extend(scan_text_script(path, display))
        else:
            findings.append(Capability("unsupported_script", display, None, "无法静态分析的脚本或二进制类型", "high"))
            complete = False
    unique = {(item.category, item.path, item.line, item.detail, item.severity): item for item in findings}
    return sorted(scanned), sorted(unique.values(), key=lambda item: (item.path, item.line or 0, item.category)), complete


def preflight_summary(skill_dir: Path) -> dict[str, Any]:
    scanned, findings, complete = preflight(skill_dir)
    high = sum(1 for item in findings if item.severity == "high")
    scripts_present = (skill_dir.expanduser() / "scripts").exists()
    status = "not_applicable" if not scripts_present else ("pass" if complete and high == 0 else "blocked")
    return {
        "ok": status in {"pass", "not_applicable"},
        "static_scan_status": status,
        "scan_complete": complete,
        "scanned_files": scanned,
        "summary": {"total": len(findings), "high": high, "medium": len(findings) - high},
        "capabilities": [asdict(item) for item in findings],
        "execution_authorized": False,
        "manual_review_required": scripts_present,
    }


def command_preflight(args: argparse.Namespace) -> int:
    result = preflight_summary(args.skill_dir)
    result["skill_dir"] = str(args.skill_dir)
    emit(result)
    return 1 if result["static_scan_status"] == "blocked" else 0


def excluded(relative_path: Path) -> bool:
    return (
        any(part in EXCLUDED_DIRS for part in relative_path.parts)
        or relative_path.name in EXCLUDED_FILES
        or relative_path.suffix.lower() in EXCLUDED_SUFFIXES
    )


def package_files(root: Path) -> list[Path]:
    return sorted(
        (path for path in iter_files(root) if not excluded(path.relative_to(root))),
        key=lambda item: item.relative_to(root).as_posix(),
    )


def safe_archive_names(root: Path, files: list[Path]) -> dict[Path, str]:
    normalized: dict[str, str] = {}
    result: dict[Path, str] = {}
    for path in files:
        rel = path.relative_to(root)
        parts = (root.name, *rel.parts)
        for part in parts:
            invalid_windows = any(character in part for character in '<>"|?*')
            control_character = any(ord(character) < 32 for character in part)
            if "\\" in part or ":" in part or invalid_windows or control_character or part in {"", ".", ".."} or part.endswith((" ", ".")):
                raise ValueError(f"跨平台不安全的 ZIP 成员名：{rel.as_posix()}")
            stem = part.split(".", 1)[0].upper()
            if stem in WINDOWS_RESERVED:
                raise ValueError(f"Windows 保留文件名：{rel.as_posix()}")
        archive_name = "/".join(parts)
        key = unicodedata.normalize("NFC", archive_name).casefold()
        if key in normalized and normalized[key] != archive_name:
            raise ValueError(f"跨平台文件名碰撞：{normalized[key]} 与 {archive_name}")
        normalized[key] = archive_name
        result[path] = archive_name
    return result


def assert_preflight_gate(skill_dir: Path, risk_ack: str | None) -> dict[str, Any]:
    result = preflight_summary(skill_dir)
    if result["static_scan_status"] == "blocked" and not (risk_ack and risk_ack.strip()):
        raise ValueError("脚本静态预检阻断；经人工复核接受风险时必须提供 --risk-ack")
    return result


def create_archive(snapshot: Path, output: Path, overwrite: bool) -> dict[str, Any]:
    files = package_files(snapshot)
    names = safe_archive_names(snapshot, files)
    fd, raw_temp = tempfile.mkstemp(prefix=f".{snapshot.name}-", suffix=".zip.tmp", dir=output.parent)
    os.close(fd)
    temp_path = Path(raw_temp)
    placeholder_created = False
    try:
        with zipfile.ZipFile(temp_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for path in files:
                archive.write(path, names[path])
        with zipfile.ZipFile(temp_path) as archive:
            if archive.testzip() is not None or sorted(archive.namelist()) != sorted(names.values()):
                raise ValueError("ZIP 完整性或成员清单检查失败")
        if not overwrite:
            exclusive = os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_BINARY", 0)
            holder = os.open(output, exclusive)
            os.close(holder)
            placeholder_created = True
        os.replace(temp_path, output)
        placeholder_created = False
        return {"file_count": len(files), "bytes": output.stat().st_size, "sha256": hashlib.sha256(output.read_bytes()).hexdigest()}
    finally:
        if temp_path.exists():
            temp_path.unlink()
        if placeholder_created and output.exists() and output.stat().st_size == 0:
            output.unlink()


def snapshot_for_operation(source: Path, parent: Path, prefix: str) -> tuple[Path, Path]:
    stage_root = Path(tempfile.mkdtemp(prefix=prefix, dir=parent))
    snapshot = stage_root / source.name
    copy_snapshot(source, snapshot)
    return stage_root, snapshot


def command_package(args: argparse.Namespace) -> int:
    if not args.write_confirmed:
        return fail("package 写入 ZIP，必须传入 --write-confirmed")
    source = args.skill_dir.expanduser()
    issues = validate_skill(source, require_agent_created=not args.packaged)
    if issues:
        emit({"ok": False, "error": "Skill 校验失败", "issues": [asdict(item) for item in issues]}, error=True)
        return 1
    source = source.resolve()
    output = args.output.expanduser().absolute() if args.output else source.parent / f"{source.name}.zip"
    if output.suffix.lower() != ".zip":
        return fail("输出必须是 .zip")
    if within(output.resolve(strict=False), source):
        return fail("输出 ZIP 不能位于 Skill 内部")
    if output.exists() and not args.overwrite:
        return fail("输出已存在；确认替换时同时传入 --overwrite")
    output.parent.mkdir(parents=True, exist_ok=True)
    stage_root: Path | None = None
    try:
        stage_root, snapshot = snapshot_for_operation(source, output.parent, f".{source.name}-package-")
        snapshot_issues = validate_skill(snapshot, require_agent_created=not args.packaged)
        if snapshot_issues:
            emit({"ok": False, "error": "打包快照校验失败", "issues": [asdict(item) for item in snapshot_issues]}, error=True)
            return 1
        try:
            preflight_result = assert_preflight_gate(snapshot, args.risk_ack)
        except ValueError as exc:
            return fail(str(exc), 1)
        archive = create_archive(snapshot, output, args.overwrite)
        emit({"ok": True, "output": str(output), "snapshot_digest": tree_digest(snapshot), "preflight": preflight_result, **archive})
        return 0
    finally:
        if stage_root and stage_root.exists():
            shutil.rmtree(stage_root, ignore_errors=True)


def command_backup(args: argparse.Namespace) -> int:
    if not args.write_confirmed:
        return fail("backup 写入备份，必须传入 --write-confirmed")
    source = args.skill_dir.expanduser()
    issues = validate_skill(source, require_agent_created=not args.packaged)
    if issues:
        emit({"ok": False, "error": "待备份 Skill 校验失败", "issues": [asdict(item) for item in issues]}, error=True)
        return 1
    source = source.resolve()
    output = args.output.expanduser().absolute()
    if output.suffix.lower() != ".zip" or within(output.resolve(strict=False), source):
        return fail("备份必须是位于 Skill 目录外的 .zip")
    if output.exists():
        return fail("备份目标已存在，拒绝覆盖")
    output.parent.mkdir(parents=True, exist_ok=True)
    stage_root: Path | None = None
    try:
        stage_root, snapshot = snapshot_for_operation(source, output.parent, f".{source.name}-backup-")
        snapshot_issues = validate_skill(snapshot, require_agent_created=not args.packaged)
        if snapshot_issues:
            return fail("备份快照校验失败", 1)
        source_digest = tree_digest(source, skip_excluded=True)
        snapshot_digest = tree_digest(snapshot, skip_excluded=True)
        if source_digest != snapshot_digest:
            return fail("备份快照与源目录摘要不一致", 1)
        archive = create_archive(snapshot, output, False)
        emit({"ok": True, "backup": str(output), "source_digest": source_digest, **archive})
        return 0
    finally:
        if stage_root and stage_root.exists():
            shutil.rmtree(stage_root, ignore_errors=True)


def version_tuple(value: str) -> tuple[int, int, int] | None:
    match = VERSION_RE.fullmatch(value)
    return tuple(map(int, match.groups())) if match else None


def read_metadata(skill_dir: Path) -> dict[str, Any]:
    text = (skill_dir / "SKILL.md").read_text(encoding="utf-8-sig")
    metadata, _, _ = parse_frontmatter(text)
    return metadata


def ensure_state_directory(path: Path) -> None:
    if path.exists() and is_link_like(path):
        raise ValueError(f"状态目录不能是链接或重解析点：{path}")
    path.mkdir(parents=True, exist_ok=True)
    if is_link_like(path):
        raise ValueError(f"状态目录不能是链接或重解析点：{path}")


def acquire_operation_lock(lock_path: Path) -> int:
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    if is_link_like(lock_path.parent):
        raise ValueError("锁目录不能是链接或重解析点")
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_BINARY", 0)
    try:
        descriptor = os.open(lock_path, flags)
    except FileExistsError as exc:
        raise ValueError(f"同名 Skill 已有安装事务运行：{lock_path}") from exc
    os.write(descriptor, str(os.getpid()).encode("ascii"))
    return descriptor


def release_operation_lock(lock_path: Path, descriptor: int | None) -> None:
    if descriptor is None:
        return
    os.close(descriptor)
    if lock_path.exists() and not is_link_like(lock_path):
        lock_path.unlink()


def command_install(args: argparse.Namespace) -> int:
    source = args.skill_dir.expanduser()
    issues = validate_skill(source)
    if issues:
        emit({"ok": False, "error": "源 Skill 校验失败", "issues": [asdict(item) for item in issues]}, error=True)
        return 1
    source = source.resolve()
    try:
        preflight_result = assert_preflight_gate(source, args.risk_ack)
    except ValueError as exc:
        return fail(str(exc), 1)
    install_root = Path.home() / ".workbuddy" / "skills"
    if install_root.exists() and is_link_like(install_root):
        return fail("用户级安装根目录不能是链接或重解析点")
    target = install_root / source.name
    if source == target.resolve(strict=False):
        return fail("源目录已经是安装目标")
    new_version_text = str(read_metadata(source).get("version", ""))
    new_version = version_tuple(new_version_text)
    old_version: tuple[int, int, int] | None = None
    old_version_text: str | None = None
    if target.exists():
        if is_link_like(target) or not target.is_dir():
            return fail("现有安装目标不是普通目录")
        old_version_text = str(read_metadata(target).get("version", ""))
        old_version = version_tuple(old_version_text)
        if new_version is None or old_version is None or new_version <= old_version:
            return fail("更新安装要求新版 version 严格高于旧版")
    state_root = Path.home() / ".workbuddy" / ".skill-smith"
    transaction = uuid.uuid4().hex
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = state_root / "backups" / f"{source.name}-{old_version_text or 'none'}-{timestamp}-{transaction[:8]}"
    failed = state_root / "failed" / f"{source.name}-{timestamp}-{transaction[:8]}"
    plan = {
        "skill": source.name,
        "source": str(source),
        "target": str(target),
        "new_version": new_version_text,
        "old_version": old_version_text,
        "backup": str(backup) if target.exists() else None,
        "failed_quarantine": str(failed),
        "preflight": preflight_result,
        "actions": ["校验源包", "静态预检", "复制到 staging", "校验 staging", "备份旧版" if target.exists() else "首次安装", "原子落位", "安装后核验", "失败自动回滚"],
    }
    if not args.apply:
        emit({"ok": True, "dry_run": True, "plan": plan})
        return 0
    if not args.install_confirmed:
        return fail("install --apply 会写入用户级目录，必须传入 --install-confirmed")
    install_root.mkdir(parents=True, exist_ok=True)
    staging_root = state_root / "staging"
    ensure_state_directory(staging_root)
    ensure_state_directory(backup.parent)
    ensure_state_directory(failed.parent)
    lock_path = state_root / "locks" / f"{source.name}.lock"
    lock_descriptor: int | None = None
    stage_parent = staging_root / f"install-{source.name}-{transaction}"
    staged = stage_parent / source.name
    target_moved = False
    had_target = target.exists()
    original_digest: str | None = None
    try:
        lock_descriptor = acquire_operation_lock(lock_path)
        had_target = target.exists()
        if had_target:
            current_version_text = str(read_metadata(target).get("version", ""))
            current_version = version_tuple(current_version_text)
            if new_version is None or current_version is None or new_version <= current_version:
                return fail("获得安装锁后发现目标版本已变化，新版不再高于当前版本", 1)
            old_version_text = current_version_text
            backup = state_root / "backups" / f"{source.name}-{old_version_text}-{timestamp}-{transaction[:8]}"
        copy_snapshot(source, staged)
        staged_issues = validate_skill(staged)
        if staged_issues:
            emit({"ok": False, "error": "staging 校验失败", "issues": [asdict(item) for item in staged_issues]}, error=True)
            return 1
        staged_version_text = str(read_metadata(staged).get("version", ""))
        if staged_version_text != new_version_text:
            return fail("staging 版本与已确认的新版本不一致", 1)
        source_digest = tree_digest(source, skip_excluded=True)
        staged_digest = tree_digest(staged, skip_excluded=True)
        if source_digest != staged_digest:
            return fail("staging 与当前源目录摘要不一致", 1)
        assert_preflight_gate(staged, args.risk_ack)
        if target.exists():
            original_digest = tree_digest(target)
            os.replace(target, backup)
            target_moved = True
            if tree_digest(backup) != original_digest:
                raise RuntimeError("备份摘要验证失败")
        os.replace(staged, target)
        installed_issues = validate_skill(target)
        if installed_issues:
            raise RuntimeError("安装后校验失败")
        installed_digest = tree_digest(target, skip_excluded=True)
        if installed_digest != tree_digest(source, skip_excluded=True):
            raise RuntimeError("安装后目录摘要与源目录不一致")
        emit({
            "ok": True,
            "dry_run": False,
            "installed_to": str(target),
            "backup": str(backup) if target_moved else None,
            "version": new_version_text,
            "digest": installed_digest,
            "preflight": preflight_result,
        })
        return 0
    except BaseException as exc:
        rollback_errors: list[str] = []
        try:
            if had_target:
                if backup.exists():
                    if target.exists():
                        os.replace(target, failed)
                    os.replace(backup, target)
                    target_moved = False
                    if original_digest and tree_digest(target) != original_digest:
                        rollback_errors.append("恢复后的旧版摘要不一致")
            elif target.exists():
                os.replace(target, failed)
        except BaseException as rollback_exc:
            rollback_errors.append(str(rollback_exc))
        message = f"安装失败，已执行回滚：{exc}"
        if rollback_errors:
            message += f"；回滚异常：{'；'.join(rollback_errors)}"
        return fail(message, 130 if isinstance(exc, KeyboardInterrupt) else 1)
    finally:
        if stage_parent.exists():
            shutil.rmtree(stage_parent, ignore_errors=True)
        release_operation_lock(lock_path, lock_descriptor)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Skill Smith 包内确定性操作")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate", help="校验 Skill")
    validate.add_argument("skill_dir", type=Path)
    validate.add_argument("--packaged", action="store_true", help="允许随专家包分发的 Skill 不含 agent_created")
    validate.set_defaults(func=command_validate)

    render = subparsers.add_parser("render", help="从完整正文创建 Skill")
    render.add_argument("name")
    render.add_argument("--description", required=True)
    render.add_argument("--body-file", required=True, type=Path)
    render.add_argument("--resources-dir", type=Path, help="可选资源目录，根级只允许 scripts、references、assets")
    render.add_argument("--output-dir", required=True, type=Path)
    render.add_argument("--version", default="1.0.0")
    render.add_argument("--requirements-confirmed", action="store_true")
    render.add_argument("--write-confirmed", action="store_true")
    render.set_defaults(func=command_render)

    preflight_parser = subparsers.add_parser("preflight", help="静态扫描 scripts")
    preflight_parser.add_argument("skill_dir", type=Path)
    preflight_parser.set_defaults(func=command_preflight)

    package = subparsers.add_parser("package", help="校验快照并打包 Skill")
    package.add_argument("skill_dir", type=Path)
    package.add_argument("--output", type=Path)
    package.add_argument("--overwrite", action="store_true")
    package.add_argument("--packaged", action="store_true", help="打包随专家包分发的 Skill")
    package.add_argument("--risk-ack", help="人工复核接受静态预检高风险的说明")
    package.add_argument("--write-confirmed", action="store_true")
    package.set_defaults(func=command_package)

    backup_parser = subparsers.add_parser("backup", help="校验并完整备份 Skill")
    backup_parser.add_argument("skill_dir", type=Path)
    backup_parser.add_argument("--output", required=True, type=Path)
    backup_parser.add_argument("--packaged", action="store_true")
    backup_parser.add_argument("--write-confirmed", action="store_true")
    backup_parser.set_defaults(func=command_backup)

    install = subparsers.add_parser("install", help="预览或执行用户级安装")
    install.add_argument("skill_dir", type=Path)
    install.add_argument("--apply", action="store_true")
    install.add_argument("--risk-ack", help="人工复核接受静态预检高风险的说明")
    install.add_argument("--install-confirmed", action="store_true")
    install.set_defaults(func=command_install)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except KeyboardInterrupt:
        return fail("操作被中断", 130)
    except (OSError, ValueError, RuntimeError, zipfile.BadZipFile) as exc:
        return fail(str(exc), 1)


if __name__ == "__main__":
    raise SystemExit(main())
