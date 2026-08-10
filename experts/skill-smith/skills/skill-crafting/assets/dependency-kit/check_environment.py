#!/usr/bin/env python3
"""Read-only environment checker for dependency-aware WorkBuddy Skills."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

VERSION_RE = re.compile(r"(?<![0-9])(0|[1-9][0-9]{0,5})(?:\.(0|[1-9][0-9]{0,5}))?(?:\.(0|[1-9][0-9]{0,5}))?", re.ASCII)
VALID_TYPES = {"cli", "cli_probe", "env", "file", "json_field", "mcp", "mcp_probe", "auth_probe", "python", "url"}
PROBE_REASON_CODES = {"ok", "auth_expired_or_invalid", "permission_denied", "quota_or_rate_limit", "service_error", "network_or_timeout", "version_incompatible", "configuration_invalid", "mcp_not_registered", "probe_failed"}
EVIDENCE_LABELS = {"已验证", "部分验证", "推断", "未验证"}
SETUP_OUTPUT_FIELDS = {
    "official_home_url", "official_docs_url", "download_url", "login_url",
    "credential_url", "console_path", "scopes", "credential_storage", "steps",
    "verify", "rotate_or_revoke", "verified_at", "applies_to_version",
}


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError(f"JSON 根节点必须是对象：{path}")
    return data


def parse_version(value: str) -> tuple[int, int, int] | None:
    match = VERSION_RE.search(value)
    if not match:
        return None
    return tuple(int(item or 0) for item in match.groups())


def nested_field(data: Any, field: str) -> bool:
    current = data
    for part in field.split("."):
        if not isinstance(current, dict) or part not in current:
            return False
        current = current[part]
    return current not in (None, "", [], {})


def filtered_setup(setup: Any) -> dict[str, Any]:
    if not isinstance(setup, dict):
        return {}
    return {key: setup[key] for key in SETUP_OUTPUT_FIELDS if key in setup}


def validate_manifest(manifest: dict[str, Any]) -> None:
    top_allowed = {"schema_version", "capabilities", "dependencies", "functional_degradations"}
    dependency_allowed = {"id", "type", "required", "auth_type", "capabilities", "checks", "setup", "degradation"}
    check_allowed = {"id", "type", "required", "target", "command", "min_version", "name", "path", "field", "server", "url", "method", "expected_status"}
    setup_allowed = {"official_home_url", "official_docs_url", "download_url", "login_url", "credential_url", "console_path", "scopes", "credential_storage", "steps", "verify", "rotate_or_revoke", "security", "verified_at", "applies_to_version"}
    degradation_allowed = {"capability", "trigger", "fallback", "user_input", "limitations", "evidence_label", "recovery", "stop_condition"}
    if set(manifest) - top_allowed:
        raise ValueError(f"清单包含未知顶层字段：{sorted(set(manifest) - top_allowed)}")
    if manifest.get("schema_version") != "1":
        raise ValueError("schema_version 必须为字符串 1")
    capabilities = manifest.get("capabilities")
    if not isinstance(capabilities, list) or not capabilities or not all(isinstance(item, str) and item for item in capabilities):
        raise ValueError("capabilities 必须是非空字符串数组")
    declared_capabilities = set(capabilities)
    dependencies = manifest.get("dependencies")
    if not isinstance(dependencies, list):
        raise ValueError("dependencies 必须是数组")
    functional = manifest.get("functional_degradations")
    if not isinstance(functional, list) or not functional:
        raise ValueError("functional_degradations 必须是非空数组")
    covered = set()
    required_degradation_fields = {"capability", "trigger", "fallback", "user_input", "limitations", "evidence_label", "recovery", "stop_condition"}
    for index, item in enumerate(functional):
        if not isinstance(item, dict) or not required_degradation_fields <= set(item) or set(item) - degradation_allowed:
            raise ValueError(f"functional_degradations[{index}] 字段不完整或含未知字段")
        for field in required_degradation_fields:
            if not isinstance(item[field], str) or (field != "user_input" and not item[field].strip()):
                raise ValueError(f"functional_degradations[{index}].{field} 无效")
        if item["evidence_label"] not in EVIDENCE_LABELS:
            raise ValueError(f"functional_degradations[{index}].evidence_label 无效")
        covered.add(item["capability"])
    if declared_capabilities - covered:
        raise ValueError(f"以下功能缺少普通功能降级：{sorted(declared_capabilities - covered)}")
    if covered - declared_capabilities:
        raise ValueError(f"普通功能降级引用未声明功能：{sorted(covered - declared_capabilities)}")
    seen = set()
    for index, dependency in enumerate(dependencies):
        if not isinstance(dependency, dict):
            raise ValueError(f"dependencies[{index}] 必须是对象")
        if set(dependency) - dependency_allowed:
            raise ValueError(f"dependencies[{index}] 含未知字段：{sorted(set(dependency) - dependency_allowed)}")
        dependency_id = dependency.get("id")
        if not isinstance(dependency_id, str) or not dependency_id or dependency_id in seen:
            raise ValueError(f"dependencies[{index}].id 缺失或重复")
        seen.add(dependency_id)
        dependency_capabilities = dependency.get("capabilities")
        if not isinstance(dependency_capabilities, list) or not dependency_capabilities:
            raise ValueError(f"dependencies[{index}].capabilities 必须是非空数组")
        unknown = set(dependency_capabilities) - declared_capabilities
        if unknown:
            raise ValueError(f"依赖 {dependency_id} 引用了未声明功能：{sorted(unknown)}")
        checks = dependency.get("checks")
        if not isinstance(checks, list) or not checks or not all(isinstance(item, dict) for item in checks):
            raise ValueError(f"依赖 {dependency_id} 的 checks 必须是非空对象数组")
        required_checks = 0
        check_types = set()
        for check in checks:
            if set(check) - check_allowed:
                raise ValueError(f"依赖 {dependency_id} 的检查含未知字段：{sorted(set(check) - check_allowed)}")
            if check.get("type") not in VALID_TYPES or not isinstance(check.get("required"), bool):
                raise ValueError(f"依赖 {dependency_id} 存在无效检查")
            check_types.add(check["type"])
            if check["required"]:
                required_checks += 1
            if check.get("type") in {"auth_probe", "mcp_probe", "cli_probe"}:
                if not isinstance(check.get("target"), str) or not check["target"].strip():
                    raise ValueError(f"依赖 {dependency_id} 的探测缺少 target")
                if check["required"] is not True:
                    raise ValueError(f"依赖 {dependency_id} 的关键探测必须为 required")
            if check.get("type") == "cli":
                command = str(check.get("command", ""))
                if not safe_cli_name(command) or "version_args" in check:
                    raise ValueError(f"依赖 {dependency_id} 的 CLI 检查只能确认安全命令名是否存在")
            if check.get("min_version") and parse_version(str(check["min_version"])) is None:
                raise ValueError(f"依赖 {dependency_id} 的 min_version 无效")
            if any(field in check for field in ("auth_env", "auth_header", "auth_scheme")):
                raise ValueError(f"依赖 {dependency_id} 不得在通用 URL 检查中传递凭据")
        if dependency.get("required") is True and required_checks == 0:
            raise ValueError(f"必需依赖 {dependency_id} 至少需要一个必需检查")
        setup = dependency.get("setup")
        required_setup = {"official_home_url", "official_docs_url", "steps", "verify", "security", "verified_at", "applies_to_version"}
        if not isinstance(setup, dict) or not required_setup <= set(setup) or set(setup) - setup_allowed:
            raise ValueError(f"依赖 {dependency_id} 配置说明缺失或含未知字段")
        for field in ("official_home_url", "official_docs_url", "download_url", "login_url", "credential_url"):
            if field in setup and (not isinstance(setup[field], str) or not setup[field].startswith("https://")):
                raise ValueError(f"依赖 {dependency_id} 的 {field} 必须为 HTTPS URL")
        auth_type = dependency.get("auth_type")
        if auth_type not in {"none", "browser-login", "token", "api-key", "oauth", "service-account"}:
            raise ValueError(f"依赖 {dependency_id} 的 auth_type 无效")
        if auth_type != "none":
            for field in ("login_url", "console_path", "credential_storage", "rotate_or_revoke"):
                if field not in setup or setup[field] in ("", []):
                    raise ValueError(f"依赖 {dependency_id} 缺少认证配置字段 {field}")
        if auth_type in {"token", "api-key", "oauth", "service-account"}:
            for field in ("credential_url", "scopes"):
                if field not in setup or setup[field] in ("", []):
                    raise ValueError(f"依赖 {dependency_id} 缺少凭据配置字段 {field}")
        if auth_type != "none" and "auth_probe" not in check_types:
            raise ValueError(f"认证依赖 {dependency_id} 必须包含 auth_probe")
        if dependency.get("type") == "mcp" and not {"mcp", "mcp_probe"} <= check_types:
            raise ValueError(f"MCP 依赖 {dependency_id} 必须同时检查注册和最小能力探测")
        if dependency.get("type") == "cli" and not {"cli", "cli_probe"} <= check_types:
            raise ValueError(f"CLI 依赖 {dependency_id} 必须同时包含存在性检查和可信版本/状态探测")
        if dependency.get("type") == "api" and not ({"url", "auth_probe"} & check_types):
            raise ValueError(f"API 依赖 {dependency_id} 必须包含匿名健康探测或可信认证探测")
        degradations = dependency.get("degradation")
        if not isinstance(degradations, list) or not degradations:
            raise ValueError(f"依赖 {dependency_id} 缺少依赖故障降级")
        degradation_capabilities = set()
        for degradation in degradations:
            if not isinstance(degradation, dict) or not required_degradation_fields <= set(degradation) or set(degradation) - degradation_allowed:
                raise ValueError(f"依赖 {dependency_id} 的 degradation 字段不完整或含未知字段")
            for field in required_degradation_fields:
                if not isinstance(degradation[field], str) or (field != "user_input" and not degradation[field].strip()):
                    raise ValueError(f"依赖 {dependency_id} 的 degradation.{field} 无效")
            if degradation["evidence_label"] not in EVIDENCE_LABELS:
                raise ValueError(f"依赖 {dependency_id} 的 evidence_label 无效")
            degradation_capabilities.add(degradation["capability"])
        unknown_degradation = degradation_capabilities - set(dependency_capabilities)
        missing_degradation = set(dependency_capabilities) - degradation_capabilities
        if unknown_degradation:
            raise ValueError(f"依赖 {dependency_id} 的降级引用未关联功能：{sorted(unknown_degradation)}")
        if missing_degradation:
            raise ValueError(f"依赖 {dependency_id} 的以下功能缺少降级：{sorted(missing_degradation)}")


def safe_cli_name(command: str) -> bool:
    return bool(command and Path(command).name == command and "/" not in command and "\\" not in command and re.fullmatch(r"[A-Za-z0-9._-]+", command))


def external_probe(dependency_id: str, item: dict[str, Any], probe_results: dict[str, Any]) -> dict[str, Any]:
    check_id = str(item.get("id", ""))
    dependency_results = probe_results.get(dependency_id)
    evidence = dependency_results.get(check_id) if isinstance(dependency_results, dict) else None
    if not isinstance(evidence, dict):
        return {"status": "unavailable", "reason_code": "probe_required", "detail": "需要由可信宿主执行最小只读探测"}
    status = evidence.get("status")
    reason = evidence.get("reason_code")
    check_type = evidence.get("check_type")
    target = evidence.get("target")
    checked_at = evidence.get("checked_at")
    valid_pair = (status == "ready" and reason == "ok") or (status in {"missing", "unavailable"} and reason in PROBE_REASON_CODES - {"ok"})
    if not valid_pair or check_type != item.get("type") or target != item.get("target") or not isinstance(checked_at, str) or not checked_at.endswith("Z"):
        return {"status": "unavailable", "reason_code": "configuration_invalid", "detail": "外部探测结果与依赖、类型或目标不匹配"}
    return {"status": status, "reason_code": str(reason), "detail": f"已读取 {checked_at} 的可信脱敏探测结果"}


def url_probe(item: dict[str, Any], timeout: int, retries: int) -> tuple[str, str]:
    url = str(item.get("url", ""))
    if not url.startswith("https://"):
        return "unavailable", "configuration_invalid"
    method = str(item.get("method", "HEAD")).upper()
    if method not in {"HEAD", "GET"}:
        return "unavailable", "configuration_invalid"
    headers = {"User-Agent": "WorkBuddy-Skill-Environment-Check/1"}
    expected = item.get("expected_status", [200, 204])
    attempts = max(1, min(retries + 1, 3))
    for attempt in range(attempts):
        try:
            request = urllib.request.Request(url, method=method, headers=headers)
            with urllib.request.urlopen(request, timeout=timeout) as response:
                code = response.status
            return ("ready", "ok") if code in expected else ("unavailable", "service_error")
        except urllib.error.HTTPError as exc:
            if exc.code == 401:
                return "unavailable", "auth_expired_or_invalid"
            if exc.code == 403:
                return "unavailable", "permission_denied"
            if exc.code == 429:
                return "unavailable", "quota_or_rate_limit"
            if exc.code >= 500 and attempt + 1 < attempts:
                continue
            return "unavailable", "service_error"
        except (urllib.error.URLError, TimeoutError):
            if attempt + 1 < attempts:
                continue
            return "unavailable", "network_or_timeout"
    return "unavailable", "service_error"


def check_item(dependency_id: str, item: dict[str, Any], *, allow_network: bool, timeout: int, retries: int, probe_results: dict[str, Any]) -> dict[str, Any]:
    check_type = item.get("type")
    result = {
        "id": item.get("id", check_type),
        "type": check_type,
        "required": bool(item.get("required", True)),
        "status": "unavailable",
        "reason_code": "configuration_invalid",
        "detail": "检查定义无效",
    }

    if check_type == "env":
        name = str(item.get("name", ""))
        configured = bool(name and os.environ.get(name, "").strip())
        result.update(status="ready" if configured else "missing", reason_code="ok" if configured else "credential_missing", detail=f"环境变量 {name} {'已配置' if configured else '未配置'}")
        return result

    if check_type == "file":
        raw = str(item.get("path", ""))
        path = Path(os.path.expandvars(raw)).expanduser()
        exists = bool(raw and path.exists())
        result.update(status="ready" if exists else "missing", reason_code="ok" if exists else "file_missing", detail=f"文件或目录 {raw} {'存在' if exists else '不存在'}")
        return result

    if check_type == "json_field":
        raw = str(item.get("path", ""))
        field = str(item.get("field", ""))
        path = Path(os.path.expandvars(raw)).expanduser()
        if not path.is_file():
            result.update(status="missing", reason_code="file_missing", detail=f"JSON 配置不存在：{raw}")
            return result
        try:
            present = nested_field(load_json(path), field)
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
            result.update(status="unavailable", reason_code="configuration_invalid", detail=f"JSON 配置无法解析：{raw}")
            return result
        result.update(status="ready" if present else "missing", reason_code="ok" if present else "field_missing", detail=f"配置字段 {field} {'存在' if present else '缺失'}")
        return result

    if check_type == "mcp":
        server = str(item.get("server", ""))
        config_path = Path.home() / ".workbuddy" / "mcp.json"
        if not config_path.is_file():
            result.update(status="missing", reason_code="mcp_not_registered", detail="WorkBuddy MCP 配置文件不存在")
            return result
        try:
            config = load_json(config_path)
            registered = server in config.get("mcpServers", {})
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
            result.update(status="unavailable", reason_code="configuration_invalid", detail="WorkBuddy MCP 配置无法解析")
            return result
        if not registered:
            result.update(status="missing", reason_code="mcp_not_registered", detail=f"MCP {server} 未注册")
        else:
            result.update(status="ready", reason_code="ok", detail=f"MCP {server} 已注册；最终可用性由独立 mcp_probe 决定")
        return result

    if check_type == "python":
        minimum = parse_version(str(item.get("min_version", "")))
        current = sys.version_info[:3]
        ready = minimum is None or current >= minimum
        result.update(status="ready" if ready else "unavailable", reason_code="ok" if ready else "version_incompatible", detail=f"Python {current[0]}.{current[1]}.{current[2]}；最低要求 {item.get('min_version', '未指定')}")
        return result

    if check_type == "cli":
        command = str(item.get("command", ""))
        if not safe_cli_name(command):
            return result
        executable = shutil.which(command)
        if not executable:
            result.update(status="missing", reason_code="cli_missing", detail=f"CLI {command} 未安装或不在 PATH")
            return result
        result.update(status="ready", reason_code="ok", detail=f"CLI {command} 已找到；版本和登录状态由独立 cli_probe 决定")
        return result

    if check_type in {"auth_probe", "mcp_probe", "cli_probe"}:
        result.update(**external_probe(dependency_id, item, probe_results))
        return result

    if check_type == "url":
        if not allow_network:
            result.update(status="unavailable", reason_code="network_probe_not_enabled", detail="未启用网络探测")
            return result
        status, reason = url_probe(item, timeout, retries)
        result.update(status=status, reason_code=reason, detail=f"HTTPS 探测结果：{reason}")
        return result

    return result


def select_dependencies(manifest: dict[str, Any], capabilities: set[str]) -> list[dict[str, Any]]:
    dependencies = manifest["dependencies"]
    if not capabilities:
        return dependencies
    declared = set(manifest["capabilities"])
    unknown = capabilities - declared
    if unknown:
        raise ValueError(f"请求了清单未声明的功能：{sorted(unknown)}")
    selected = [dependency for dependency in dependencies if capabilities & set(dependency["capabilities"])]
    if not selected:
        raise ValueError("当前功能没有关联任何依赖；请修复功能与依赖映射")
    return selected


def dependency_status(check_results: list[dict[str, Any]]) -> str:
    required = [item for item in check_results if item["required"]]
    optional = [item for item in check_results if not item["required"]]
    if any(item["status"] == "missing" for item in required):
        return "missing"
    if any(item["status"] == "unavailable" for item in required):
        return "unavailable"
    if any(item["status"] != "ready" for item in optional):
        return "partial"
    return "ready"


def main() -> int:
    parser = argparse.ArgumentParser(description="检查当前 Skill 的依赖和运行环境")
    parser.add_argument("--manifest", type=Path, default=Path(__file__).resolve().parents[1] / "skill-dependencies.json")
    parser.add_argument("--capability", action="append", default=[], help="本次请求涉及的功能，可重复传入")
    parser.add_argument("--network", action="store_true", help="允许执行清单中的匿名只读 HTTPS 健康探测")
    parser.add_argument("--probe-results", type=Path, help="可信宿主生成的脱敏 auth_probe/mcp_probe 结果 JSON")
    parser.add_argument("--timeout", type=int, default=10)
    parser.add_argument("--retries", type=int, default=1)
    args = parser.parse_args()

    try:
        manifest = load_json(args.manifest)
        validate_manifest(manifest)
        dependencies = select_dependencies(manifest, set(args.capability))
        probe_results = load_json(args.probe_results) if args.probe_results else {}
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"status": "unavailable", "reason_code": "manifest_error", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 2

    results = []
    has_required_missing = False
    has_required_unavailable = False
    has_optional_problem = False

    for dependency in dependencies:
        check_results = [check_item(dependency["id"], item, allow_network=args.network, timeout=max(1, min(args.timeout, 30)), retries=max(0, min(args.retries, 2)), probe_results=probe_results) for item in dependency["checks"]]
        status = dependency_status(check_results)
        dependency_required = bool(dependency["required"])
        if dependency_required and status == "missing":
            has_required_missing = True
        elif dependency_required and status == "unavailable":
            has_required_unavailable = True
        elif status in {"missing", "unavailable", "partial"}:
            has_optional_problem = True
        failures = [item for item in check_results if item["status"] != "ready"]
        item = {
            "id": dependency["id"],
            "type": dependency["type"],
            "required": dependency_required,
            "capabilities": dependency["capabilities"],
            "status": status,
            "checks": failures if failures else [{"id": check["id"], "status": "ready", "reason_code": "ok"} for check in check_results],
        }
        if status == "missing" and dependency_required:
            item["setup"] = filtered_setup(dependency["setup"])
        elif status in {"unavailable", "partial", "missing"}:
            item["degradation"] = dependency["degradation"]
        results.append(item)

    if has_required_missing:
        status = "needs_setup"
    elif has_required_unavailable:
        status = "unavailable"
    elif has_optional_problem:
        status = "partial"
    else:
        status = "ready"

    visible_results = results if status == "ready" else [item for item in results if item["status"] != "ready"]
    affected_capabilities = {capability for item in visible_results for capability in item["capabilities"]}
    visible_functional_degradations = [item for item in manifest["functional_degradations"] if item["capability"] in affected_capabilities] if status != "ready" else []
    output = {
        "status": status,
        "requested_capabilities": args.capability,
        "dependencies": visible_results,
        "functional_degradations": visible_functional_degradations,
        "next_action": {
            "ready": "跳过配置引导，进入正常流程",
            "partial": "进入可用流程，只说明受影响功能、限制和降级",
            "needs_setup": "只展示缺失必需项的配置步骤，完成后重新检查",
            "unavailable": "展示结构化故障原因、恢复步骤和安全降级",
        }[status],
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0 if status in {"ready", "partial"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
