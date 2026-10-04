#!/usr/bin/env python3
"""Local, platform-neutral helpers for the Picset MCP workflow."""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
import tempfile
import uuid
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any, TextIO
from urllib.parse import urlparse
from urllib.request import Request, urlopen as stdlib_urlopen

try:
    from scripts.oss_upload import upload_file_to_oss
except ModuleNotFoundError:
    from oss_upload import upload_file_to_oss  # type: ignore


MAX_SERVICE_BATCH_SIZE = 16
PUBLIC_UPLOAD_FIELDS = ("oss_path", "file_type", "file_size")
MAX_DELIVERY_BYTES = 30 * 1024 * 1024
DELIVERY_CHUNK_SIZE = 64 * 1024
IMAGE_CONTENT_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
_SENSITIVE_KEYS = {
    "authorization",
    "accesskeysecret",
    "securitytoken",
    "confirmationtoken",
    "confirmationhandle",
    "picsetagentsk",
    "accesstoken",
    "refreshtoken",
}

# WorkBuddy / CodeBuddy injects the host conversation id into the Agent process
# env. It is not present in the LLM prompt context, so the local client (or any
# MCP forwarder) must resolve and inject it before canvas-related tool calls.
HOST_CONVERSATION_ID_ENV = "CODEBUDDY_CONVERSATION_REQUEST_ID"
# Do not use these as conversation_id: message id changes per turn; session ids
# are Agent-process scoped, not the user-facing dialogue object.
HOST_CONVERSATION_ID_FORBIDDEN_ENV = (
    "CODEBUDDY_CONVERSATION_MESSAGE_ID",
    "CODEBUDDY_SESSION_ID",
    "CLAUDE_SESSION_ID",
)
# Preferred argument field name per tool (schema may accept snake or camel).
CONVERSATION_ARG_BY_TOOL: dict[str, str] = {
    "open_agent_canvas": "conversation_id",
    "open_agent_pricing": "conversation_id",
    "generate_agent_canvas_image": "conversationId",
    "get_agent_canvas_image_status": "conversationId",
    "get_agent_canvas_state": "conversation_id",
    "insert_agent_canvas_image": "conversation_id",
    "replace_agent_canvas_image": "conversation_id",
}


def _validate_ids(ids: Sequence[str], expected_prefix: str, label: str) -> None:
    if len(set(ids)) != len(ids):
        raise ValueError(f"{label} stable ids must be unique")
    for stable_id in ids:
        if not isinstance(stable_id, str) or not re.fullmatch(
            rf"{expected_prefix}[1-9]\d*", stable_id
        ):
            raise ValueError(
                f"{label} stable id must start with {expected_prefix}: {stable_id}"
            )


def plan_batches(
    main_ids: Sequence[str],
    detail_ids: Sequence[str],
    *,
    max_batch_size: int = MAX_SERVICE_BATCH_SIZE,
    request_id_factory: Callable[[], object] = uuid.uuid4,
) -> list[dict[str, object]]:
    """将主图/详情图稳定编号切分为不超过 16 张的批次，并为每批生成 request_id。

    该函数为 skill 执行逻辑的本地辅助函数，供参考和未来复用，不通过 CLI 暴露。
    """
    if (
        isinstance(max_batch_size, bool)
        or not isinstance(max_batch_size, int)
        or not 1 <= max_batch_size <= MAX_SERVICE_BATCH_SIZE
    ):
        raise ValueError("max_batch_size must be between 1 and 16")
    _validate_ids(main_ids, "M", "main")
    _validate_ids(detail_ids, "D", "detail")

    batches: list[dict[str, object]] = []
    for image_type, stable_ids in (("main", main_ids), ("detail", detail_ids)):
        for offset in range(0, len(stable_ids), max_batch_size):
            batch_number = offset // max_batch_size + 1
            batches.append(
                {
                    "batch_id": f"{image_type}-{batch_number}",
                    "image_type": image_type,
                    "stable_ids": list(stable_ids[offset : offset + max_batch_size]),
                    "request_id": str(request_id_factory()),
                    "status": "planned",
                }
            )
    return batches


def aggregate_estimates(
    batch_plans: Sequence[Mapping[str, object]],
    estimates: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    """按批次汇总预估积分并返回仅含公开字段的报价结果。

    该函数为 skill 执行逻辑的本地辅助函数，供参考和未来复用，不通过 CLI 暴露。
    """
    total: int | float = 0
    public_estimates: list[dict[str, object]] = []
    for batch in batch_plans:
        batch_id = str(batch.get("batch_id", ""))
        estimate = estimates.get(batch_id)
        if estimate is None:
            raise ValueError(f"missing estimate for batch {batch_id}")
        cost = estimate.get("estimated_credits")
        if (
            isinstance(cost, bool)
            or not isinstance(cost, (int, float))
            or not math.isfinite(cost)
            or cost < 0
        ):
            raise ValueError(f"invalid estimated_credits for batch {batch_id}")
        total += cost
        public_estimates.append(
            {
                "batch_id": batch_id,
                "stable_ids": list(batch.get("stable_ids", [])),
                "estimated_credits": cost,
            }
        )
    return {
        "estimated_credits": total,
        "batch_estimates": public_estimates,
    }


def map_task_items(
    stable_ids: Sequence[str],
    items: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    """按服务返回的批内 index 将稳定编号映射回任务项。

    该函数为 skill 执行逻辑的本地辅助函数，供参考和未来复用，不通过 CLI 暴露。
    """
    seen: set[int] = set()
    mapped_items: list[dict[str, object]] = []
    for item in items:
        index = item.get("index")
        if isinstance(index, bool) or not isinstance(index, int):
            raise ValueError("task item index must be an integer")
        if index in seen:
            raise ValueError(f"duplicate task item index: {index}")
        if index < 0 or index >= len(stable_ids):
            raise ValueError(f"task item index out of range: {index}")
        seen.add(index)
        mapped = dict(item)
        mapped["id"] = stable_ids[index]
        mapped_items.append(mapped)
    return mapped_items


def _normalized_key(key: object) -> str:
    return re.sub(r"[^a-z0-9]", "", str(key).casefold())


def redact_sensitive(value: object) -> object:
    """递归脱敏映射/列表中的敏感键（_SENSITIVE_KEYS），避免凭据进入输出。

    该函数为 skill 执行逻辑的本地辅助函数，供参考和未来复用，不通过 CLI 暴露。
    """
    if isinstance(value, Mapping):
        return {
            key: "[REDACTED]"
            if _normalized_key(key) in _SENSITIVE_KEYS
            else redact_sensitive(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact_sensitive(item) for item in value]
    if isinstance(value, tuple):
        return tuple(redact_sensitive(item) for item in value)
    return value


def upload_from_payload(
    payload: Mapping[str, object],
    *,
    uploader: Callable[..., Mapping[str, object]] = upload_file_to_oss,
) -> dict[str, object]:
    token = payload.get("token")
    file_path = payload.get("file_path")
    if not isinstance(token, Mapping):
        raise ValueError("token must be an object")
    structured_content = token.get("structuredContent")
    if isinstance(structured_content, Mapping):
        token = structured_content
    if not isinstance(file_path, str) or not file_path:
        raise ValueError("file_path must be a non-empty string")
    result = uploader(token, file_path)
    return {field: result[field] for field in PUBLIC_UPLOAD_FIELDS}


def _validate_delivery_items(items: Sequence[Mapping[str, object]]) -> None:
    stable_ids: list[str] = []
    for item in items:
        stable_id = item.get("id")
        image_url = item.get("image_url")
        if not isinstance(stable_id, str) or not re.fullmatch(r"[MDR][1-9]\d*", stable_id):
            raise ValueError("delivery stable id must match M1, D1 or R1 style")
        if not isinstance(image_url, str):
            raise ValueError("image_url must be a string")
        parsed_url = urlparse(image_url)
        if parsed_url.scheme != "https" or not parsed_url.netloc:
            raise ValueError("image_url must use HTTPS")
        stable_ids.append(stable_id)
    if len(set(stable_ids)) != len(stable_ids):
        raise ValueError("delivery stable ids must be unique")


def _content_type_extension(headers: Mapping[str, object]) -> str:
    content_type = headers.get("Content-Type")
    if not isinstance(content_type, str):
        raise ValueError("unsupported image content type")
    normalized_content_type = content_type.split(";", 1)[0].strip().casefold()
    try:
        return IMAGE_CONTENT_TYPES[normalized_content_type]
    except KeyError as error:
        raise ValueError("unsupported image content type") from error


def resolve_host_conversation_id(
    environ: Mapping[str, str] | None = None,
) -> str | None:
    """Return the host dialogue id from the Agent process environment.

    Prefer ``CODEBUDDY_CONVERSATION_REQUEST_ID``. Never fall back to message or
    session ids — those bind the canvas to the wrong scope.
    """
    env = os.environ if environ is None else environ
    raw = env.get(HOST_CONVERSATION_ID_ENV)
    if not isinstance(raw, str):
        return None
    conversation_id = raw.strip()
    return conversation_id or None


def inject_conversation_id(
    tool_name: str,
    args: Mapping[str, object] | None = None,
    *,
    environ: Mapping[str, str] | None = None,
    conversation_id: str | None = None,
) -> dict[str, object]:
    """Copy tool args and fill the host conversation id when the tool needs it.

    Existing ``conversation_id`` / ``conversationId`` values are left unchanged.
    Tools that do not take a conversation argument are returned unchanged.
    """
    result = dict(args or {})
    field = CONVERSATION_ARG_BY_TOOL.get(tool_name)
    if field is None:
        return result

    existing_snake = result.get("conversation_id")
    existing_camel = result.get("conversationId")
    if (
        (isinstance(existing_snake, str) and existing_snake.strip())
        or (isinstance(existing_camel, str) and existing_camel.strip())
    ):
        return result

    resolved = (
        conversation_id.strip()
        if isinstance(conversation_id, str) and conversation_id.strip()
        else resolve_host_conversation_id(environ)
    )
    if not resolved:
        return result
    result[field] = resolved
    return result


def deliver_results(
    items: Sequence[Mapping[str, object]],
    output_dir: str | Path,
    *,
    urlopen: Callable[..., Any] = stdlib_urlopen,
) -> list[dict[str, object]]:
    _validate_delivery_items(items)
    destination_dir = Path(output_dir)
    if not destination_dir.is_absolute():
        raise ValueError("output_dir must be an absolute path")
    destination_dir.mkdir(parents=True, exist_ok=True)

    delivered_files: list[dict[str, object]] = []
    for item in items:
        stable_id = str(item["id"])
        image_url = str(item["image_url"])
        request = Request(
            image_url,
            headers={"Accept": "image/jpeg, image/png, image/webp"},
        )
        output_path: Path | None = None
        temporary_path: Path | None = None
        try:
            with urlopen(request, timeout=30) as response:
                final_url = response.geturl()
                parsed_final_url = urlparse(final_url)
                if parsed_final_url.scheme != "https" or not parsed_final_url.netloc:
                    raise ValueError("final image URL must use HTTPS")
                extension = _content_type_extension(response.headers)
                output_path = destination_dir / f"{stable_id}{extension}"
                downloaded_bytes = 0
                with tempfile.NamedTemporaryFile(
                    mode="wb",
                    dir=destination_dir,
                    prefix=f".{stable_id}.",
                    suffix=".tmp",
                    delete=False,
                ) as output_file:
                    temporary_path = Path(output_file.name)
                    while chunk := response.read(DELIVERY_CHUNK_SIZE):
                        downloaded_bytes += len(chunk)
                        if downloaded_bytes > MAX_DELIVERY_BYTES:
                            raise ValueError("download exceeds 30 MiB")
                        output_file.write(chunk)
                os.replace(temporary_path, output_path)
                temporary_path = None
        except Exception:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
            raise
        delivered_files.append(
            {
                "id": stable_id,
                "path": str(output_path),
                "image_url": image_url,
            }
        )

    return delivered_files


def main(
    argv: list[str] | None = None,
    *,
    stdin: TextIO | None = None,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    parser = argparse.ArgumentParser(description="Picset local workflow client")
    parser.add_argument(
        "command",
        choices=("upload", "deliver", "host-conversation-id"),
    )
    args = parser.parse_args(argv)
    input_stream = stdin or sys.stdin
    output_stream = stdout or sys.stdout
    error_stream = stderr or sys.stderr

    try:
        if args.command == "host-conversation-id":
            conversation_id = resolve_host_conversation_id()
            if not conversation_id:
                raise ValueError(
                    f"{HOST_CONVERSATION_ID_ENV} is missing from the process "
                    "environment; do not invent an id or use MESSAGE_ID/SESSION_ID"
                )
            result = {"conversation_id": conversation_id}
        else:
            payload = json.load(input_stream)
            if not isinstance(payload, Mapping):
                raise ValueError("input must be a JSON object")
            if args.command == "upload":
                result = upload_from_payload(payload)
            else:
                items = payload.get("items")
                output_dir = payload.get("output_dir")
                if not isinstance(items, list):
                    raise ValueError("items must be an array")
                if not isinstance(output_dir, str) or not output_dir:
                    raise ValueError("output_dir must be a non-empty absolute path")
                output_path = Path(output_dir)
                if not output_path.is_absolute():
                    raise ValueError("output_dir must be an absolute path")
                result = {"files": deliver_results(items, output_path)}
        print(json.dumps(result, ensure_ascii=False, sort_keys=True), file=output_stream)
        return 0
    except Exception as error:
        public_error = {
            "error": f"{args.command}_failed",
            "message": str(error),
        }
        print(
            json.dumps(public_error, ensure_ascii=False, sort_keys=True),
            file=error_stream,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
