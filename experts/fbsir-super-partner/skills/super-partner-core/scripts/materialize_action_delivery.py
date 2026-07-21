#!/usr/bin/env python3
"""Materialize one Super Partner action delivery without network or overwrite."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, NoReturn


SCHEMA_VERSION = "fbsir-super-partner-action-delivery/v1"
RECEIPT_SCHEMA = "fbsir-super-partner-action-materialization-receipt/v2"
LENS_IDS = {"brainstorm", "material_red_team", "monetization"}
LENS_LABELS = {
    "brainstorm": "脑暴狂",
    "material_red_team": "材料红队",
    "monetization": "祖传变现大师",
}
EXECUTION_STATUSES = {"delivered", "awaiting_approval", "not_executed"}
EXECUTION_STATUS_LABELS = {
    "delivered": "已交付",
    "awaiting_approval": "待授权",
    "not_executed": "未执行",
}
EXECUTION_STATUS_EXPLANATIONS = {
    "delivered": "完整成品已保存在本文件中；未声称发生外部状态变化。",
    "awaiting_approval": "完整预览见下方；外部副作用尚未执行，仍需当次明确批准。",
    "not_executed": "宿主动作未执行；本文件只保存可手动使用的成品。",
}
OBSERVABLE_QUANTITY = re.compile(
    r"(?:\d+(?:\.\d+)?|[零〇一二三四五六七八九十百千]+)\s*"
    r"(?:个|条|次|人|份|项|例|单|家|位|%|％|元|分钟|小时|天)"
)
BASE_TOP_LEVEL_KEYS = {
    "schemaVersion",
    "lensId",
    "artifact",
    "executionStatus",
    "action",
    "outcome72h",
    "evidence",
}
APPROVAL_PREVIEW_KEYS = {"target", "effect", "payload", "impactBoundary"}
RESERVED_CONTROL_LINE = re.compile(
    r"^\s{0,3}(?:"
    r"#{1,6}\s*(?:立即交付|选项|矛盾与缺证|付费者与价值交换|执行状态|待你批准|"
    r"验证与回执|现在只做一步|72\s*小时裁决|依据与边界|唯一问题)\s*#*\s*"
    r"|本轮魔镜[：:].*"
    r"|状态[：:]\s*(?:已交付|已执行|待授权|未执行)(?:\s*[；;].*)?"
    r")$",
    re.MULTILINE,
)
WINDOWS_RESERVED_NAME = re.compile(
    r"^(?:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?$",
    re.IGNORECASE,
)


class ContractError(ValueError):
    """A stable, user-safe contract failure."""


def fail(code: str) -> NoReturn:
    raise ContractError(code)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def parse_json_object(path: Path) -> tuple[dict[str, Any], bytes]:
    if path.is_symlink() or not path.is_file():
        fail("input_must_be_regular_file")
    raw = path.read_bytes()
    try:
        value = json.loads(raw.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        fail("input_json_invalid")
    if not isinstance(value, dict):
        fail("input_root_must_be_object")
    return value, raw


def require_exact_keys(value: dict[str, Any], expected: set[str], label: str) -> None:
    if set(value) != expected:
        fail(f"{label}_keys_invalid")


def require_text(
    value: Any,
    label: str,
    minimum: int = 1,
    *,
    allow_multiline: bool = False,
) -> str:
    if not isinstance(value, str) or len("".join(value.split())) < minimum:
        fail(f"{label}_invalid")
    text = value.strip()
    if not allow_multiline and ("\n" in text or "\r" in text):
        fail(f"{label}_must_be_single_line")
    if RESERVED_CONTROL_LINE.search(text):
        fail(f"{label}_reserved_control_line")
    return text


def require_observable_quantity(value: Any, label: str) -> str:
    text = require_text(value, label)
    if not OBSERVABLE_QUANTITY.search(text):
        fail(f"{label}_observable_quantity_required")
    return text


def require_string_list(value: Any, label: str) -> list[str]:
    if not isinstance(value, list) or not value:
        fail(f"{label}_invalid")
    result = [require_text(item, label) for item in value]
    return result


def parse_timestamp(value: Any, label: str) -> datetime:
    text = require_text(value, label)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        fail(f"{label}_invalid")
    if parsed.tzinfo is None:
        fail(f"{label}_timezone_required")
    return parsed.astimezone(timezone.utc)


def validate_window(start: datetime, deadline: datetime, now: datetime, hours: int, label: str) -> None:
    if start > now:
        fail(f"{label}_start_in_future")
    if deadline <= now:
        fail(f"{label}_deadline_expired")
    seconds = (deadline - start).total_seconds()
    if seconds <= 0 or seconds > hours * 3600:
        fail(f"{label}_outside_{hours}h")


def validate_payload(value: dict[str, Any], now: datetime) -> dict[str, Any]:
    if value.get("executionStatus") == "completed":
        fail("execution_status_requires_host_receipt")
    if value.get("executionStatus") not in EXECUTION_STATUSES:
        fail("execution_status_invalid")
    awaiting_approval = value.get("executionStatus") == "awaiting_approval"
    if awaiting_approval and "approvalPreview" not in value:
        fail("approval_preview_required")
    if not awaiting_approval and "approvalPreview" in value:
        fail("approval_preview_not_allowed")
    expected_root_keys = BASE_TOP_LEVEL_KEYS | ({"approvalPreview"} if awaiting_approval else set())
    require_exact_keys(value, expected_root_keys, "root")
    if value.get("schemaVersion") != SCHEMA_VERSION:
        fail("schema_version_mismatch")
    if value.get("lensId") not in LENS_IDS:
        fail("lens_id_invalid")

    artifact = value.get("artifact")
    action = value.get("action")
    outcome = value.get("outcome72h")
    evidence = value.get("evidence")
    if not all(isinstance(item, dict) for item in (artifact, action, outcome, evidence)):
        fail("nested_object_invalid")

    require_exact_keys(artifact, {"type", "title", "body"}, "artifact")
    require_text(artifact["type"], "artifact_type")
    require_text(artifact["title"], "artifact_title")
    require_text(artifact["body"], "artifact_body", minimum=80, allow_multiline=True)

    if awaiting_approval:
        approval_preview = value["approvalPreview"]
        if not isinstance(approval_preview, dict):
            fail("approval_preview_object_invalid")
        require_exact_keys(approval_preview, APPROVAL_PREVIEW_KEYS, "approval_preview")
        require_text(approval_preview["target"], "approval_preview_target")
        require_text(approval_preview["effect"], "approval_preview_effect")
        require_text(
            approval_preview["payload"],
            "approval_preview_payload",
            minimum=24,
            allow_multiline=True,
        )
        require_text(approval_preview["impactBoundary"], "approval_preview_impact_boundary")

    action_required_keys = {
        "owner",
        "action",
        "target",
        "startedAt",
        "deadline",
        "completionDefinition",
        "twoMinuteStart",
    }
    if set(action) not in (action_required_keys, action_required_keys | {"trigger"}):
        fail("action_keys_invalid")
    for key in action_required_keys - {"startedAt", "deadline"}:
        require_text(action[key], f"action_{key}")
    if "trigger" in action:
        require_text(action["trigger"], "action_trigger")
    action_started_at = parse_timestamp(action["startedAt"], "action_started_at")
    action_deadline = parse_timestamp(action["deadline"], "action_deadline")
    validate_window(action_started_at, action_deadline, now, 24, "action")

    outcome_keys = {
        "metric",
        "baseline",
        "threshold",
        "evidenceSource",
        "windowStartedAt",
        "deadline",
        "onReached",
        "onNotReached",
    }
    require_exact_keys(outcome, outcome_keys, "outcome")
    for key in outcome_keys - {"windowStartedAt", "deadline", "baseline", "threshold"}:
        require_text(outcome[key], f"outcome_{key}")
    require_observable_quantity(outcome["baseline"], "outcome_baseline")
    require_observable_quantity(outcome["threshold"], "outcome_threshold")
    outcome_started_at = parse_timestamp(outcome["windowStartedAt"], "outcome_window_started_at")
    outcome_deadline = parse_timestamp(outcome["deadline"], "outcome_deadline")
    validate_window(outcome_started_at, outcome_deadline, now, 72, "outcome")

    require_exact_keys(evidence, {"facts", "inferences", "unknowns"}, "evidence")
    for key in ("facts", "inferences", "unknowns"):
        require_string_list(evidence[key], f"evidence_{key}")
    return value


def bullet_lines(values: list[str]) -> list[str]:
    return [f"- {item}" for item in values]


def render_markdown(value: dict[str, Any], output_path: Path) -> str:
    artifact = value["artifact"]
    action = value["action"]
    outcome = value["outcome72h"]
    evidence = value["evidence"]
    action_parts = [
        f"负责人：{action['owner']}",
        f"动作：{action['action']}",
        f"对象/渠道：{action['target']}",
        f"行动起点：{action['startedAt']}",
        f"截止：{action['deadline']}",
        f"完成定义：{action['completionDefinition']}",
        f"2 分钟启动版：{action['twoMinuteStart']}",
    ]
    if "trigger" in action:
        action_parts.insert(1, f"启动条件：如果{action['trigger']}，那么执行以下动作")
    action_line = f"- {'；'.join(action_parts)}。"
    approval_lines: list[str] = []
    if value["executionStatus"] == "awaiting_approval":
        approval = value["approvalPreview"]
        approval_lines = [
            "### 待你批准",
            "",
            f"目标：{approval['target']}",
            "",
            f"效果：{approval['effect']}",
            "",
            "完整预览：",
            "",
            approval["payload"].strip(),
            "",
            f"影响边界：{approval['impactBoundary']}",
            "",
        ]

    lines = [
        f"本轮魔镜：{LENS_LABELS[value['lensId']]}（{value['lensId']}）",
        "",
        "### 立即交付",
        "",
        f"成品类型：{artifact['type']}",
        "",
        f"**{artifact['title']}**",
        "",
        "可直接使用内容：",
        "",
        artifact["body"].strip(),
        "",
        "### 执行状态",
        "",
        f"状态：{EXECUTION_STATUS_LABELS[value['executionStatus']]}",
        "",
        f"说明：{EXECUTION_STATUS_EXPLANATIONS[value['executionStatus']]}",
        "",
        *approval_lines,
        "### 验证与回执",
        "",
        f"回执：`{RECEIPT_SCHEMA}`；真实写入结果以脚本标准输出为准。",
        "",
        f"目标/路径：`{output_path}`",
        "",
        "实际变化：只尝试新建这一份 Markdown，不覆盖既有文件。",
        "",
        "校验：脚本写后回读同一路径，并在独立回执中返回字节数与 SHA-256。",
        "",
        "不能证明：外部发送、发布、客户阅读、业务结果或其它宿主动作已经完成。",
        "",
        "### 现在只做一步",
        "",
        action_line,
        "",
        "### 72 小时裁决",
        "",
        f"- 指标：{outcome['metric']}",
        f"- 基线：{outcome['baseline']}",
        f"- 阈值：{outcome['threshold']}",
        f"- 证据源：{outcome['evidenceSource']}",
        f"- 窗口起点：{outcome['windowStartedAt']}",
        f"- 裁决时间：{outcome['deadline']}",
        f"- 达到后：{outcome['onReached']}",
        f"- 未达到时：{outcome['onNotReached']}",
        "",
        "### 依据与边界",
        "",
        "事实：",
        *bullet_lines(evidence["facts"]),
        "",
        "推断：",
        *bullet_lines(evidence["inferences"]),
        "",
        "未知：",
        *bullet_lines(evidence["unknowns"]),
        "",
    ]
    return "\n".join(lines)


def assert_within_workspace(candidate: Path, workspace: Path, label: str) -> Path:
    resolved_workspace = workspace.resolve(strict=True)
    if not resolved_workspace.is_dir():
        fail("workspace_root_invalid")
    resolved_candidate = candidate.resolve(strict=False)
    try:
        relative = resolved_candidate.relative_to(resolved_workspace)
    except ValueError:
        fail(f"{label}_outside_workspace")
    for part in relative.parts:
        if any(ord(character) < 32 for character in part):
            fail(f"{label}_control_character_forbidden")
        if os.name == "nt":
            if ":" in part:
                fail(f"{label}_windows_ads_forbidden")
            if part.endswith((" ", ".")) or WINDOWS_RESERVED_NAME.fullmatch(part):
                fail(f"{label}_windows_reserved_path_forbidden")
    return resolved_candidate


def resolve_workspace(value: str) -> Path:
    try:
        workspace = Path(value).resolve(strict=True)
    except OSError:
        fail("workspace_root_invalid")
    if not workspace.is_dir() or workspace.is_symlink():
        fail("workspace_root_invalid")
    return workspace


def resolve_cli_path(value: str, workspace: Path) -> Path:
    candidate = Path(value)
    return candidate if candidate.is_absolute() else workspace / candidate


def write_new_file_and_verify(output: Path, content: bytes) -> tuple[int, str]:
    if output.suffix.lower() != ".md":
        fail("output_extension_must_be_md")
    if output.exists() or output.is_symlink():
        fail("output_exists_refuse_overwrite")
    if not output.parent.is_dir() or output.parent.is_symlink():
        fail("output_parent_invalid")
    descriptor = None
    created = False
    created_identity: tuple[int, int] | None = None
    try:
        try:
            descriptor = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            fail("output_exists_refuse_overwrite")
        created = True
        descriptor_stat = os.fstat(descriptor)
        if descriptor_stat.st_ino:
            created_identity = (descriptor_stat.st_dev, descriptor_stat.st_ino)
        with os.fdopen(descriptor, "wb") as stream:
            descriptor = None
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        readback = output.read_bytes()
        if readback != content:
            fail("output_readback_mismatch")
        return len(readback), sha256_bytes(readback)
    except Exception:
        if descriptor is not None:
            os.close(descriptor)
        if created and created_identity is not None:
            try:
                current = output.lstat()
                if not stat.S_ISLNK(current.st_mode) and (current.st_dev, current.st_ino) == created_identity:
                    output.unlink(missing_ok=True)
            except OSError:
                pass
        raise


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace-root", required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        workspace = resolve_workspace(args.workspace_root)
        input_path = assert_within_workspace(resolve_cli_path(args.input, workspace), workspace, "input")
        output_path = assert_within_workspace(resolve_cli_path(args.output, workspace), workspace, "output")
        now = datetime.now(timezone.utc)
        payload, input_bytes = parse_json_object(input_path)
        validated = validate_payload(payload, now)
        rendered = render_markdown(validated, output_path).encode("utf-8")
        output_bytes, output_sha256 = write_new_file_and_verify(output_path, rendered)
        receipt = {
            "schemaVersion": RECEIPT_SCHEMA,
            "materializationStatus": "materialized",
            "userVisibleExecutionStatus": EXECUTION_STATUS_LABELS[validated["executionStatus"]],
            "hostExecutionProven": False,
            "writeMode": "new_file_only",
            "networkUsed": False,
            "externalSideEffect": False,
            "inputPath": str(input_path),
            "inputSha256": sha256_bytes(input_bytes),
            "artifactPath": str(output_path),
            "artifactBytes": output_bytes,
            "artifactSha256": output_sha256,
            "readbackVerified": True,
            "clockSource": "system_utc",
            "validatedAt": now.isoformat().replace("+00:00", "Z"),
        }
        print(json.dumps(receipt, ensure_ascii=True, sort_keys=True))
        return 0
    except ContractError as error:
        failure = {
            "schemaVersion": RECEIPT_SCHEMA,
            "materializationStatus": "failed",
            "hostExecutionProven": False,
            "code": str(error),
        }
        print(json.dumps(failure, sort_keys=True))
        return 2
    except OSError:
        failure = {
            "schemaVersion": RECEIPT_SCHEMA,
            "materializationStatus": "failed",
            "hostExecutionProven": False,
            "code": "filesystem_operation_failed",
        }
        print(json.dumps(failure, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
