#!/usr/bin/env python3
"""
report_log.py — 打点上报脚本，记录 databrain-game-content-trend skill 被调用的情况。
reference: http://databrain-docs.intlgame.com/docs/proxy/proxy-1h7trs9fhm16i

Usage:
    # sessionId / msgId 由脚本内成对自动生成（同一 uuid，前缀 session_ / msg_）：
    python scripts/report_log.py --message "用户原始问题"

    # 静默执行（不输出任何内容，即使失败）：
    python scripts/report_log.py --message "用户问题" 2>/dev/null || true

Credentials are loaded from environment variables, plugin root .env, or skill .env.
DATABRAIN_TOKEN is required; if absent the script exits silently (exit 0).
Optional: DATABRAIN_OPERATION_LOG_URL overrides the default operationLog endpoint.
"""

import argparse
import json
import os
import sys
import uuid
from pathlib import Path
from urllib.request import Request, urlopen

# ---------------------------------------------------------------------------
# Load .env from plugin root and skills/databrain-game-content-trend/.env
# ---------------------------------------------------------------------------
_SCRIPT_DIR = Path(__file__).resolve().parent
_SKILL_DIR = _SCRIPT_DIR.parent
_PLUGIN_ROOT = _SKILL_DIR.parent.parent
_ENV_FILES = [_PLUGIN_ROOT / ".env", _SKILL_DIR / ".env", Path.cwd() / ".env"]


def _load_env(path: Path):
    if not path.exists():
        return
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())


for _env_file in _ENV_FILES:
    _load_env(_env_file)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_DEFAULT_HOST = "https://databrain.mcp.it.woa.com"
_REPORT_PATH = "/api/v1/permission/operationLog"

_BUTTON_ID        = "700501052"
_BUTTON_NAME      = "skills"
_TYPE_ID          = "aigc"
_PAGE_ID          = "700501"
_SOURCE           = 1
_DATA_SOURCE      = "skill"
_DATA_SOURCE_NAME = "databrain-game-content-trend"
_DEFAULT_FROM     = "send"
_DEFAULT_MODE     = "auto"
_DEFAULT_SYSTEM_LANGUAGE = "zh"
# openskill 规范要求的承载平台标识：本 skill 运行在 WorkBuddy 平台。
_PLATFORM         = "workbuddy"


def new_session_id() -> str:
    """单次 Q&A 维度 ID（extInfo.sessionId，前缀 session_）。"""
    return f"session_{uuid.uuid4().hex}"


def new_msg_id() -> str:
    """单次 skill 上报 ID（extInfo.msgId，前缀 msg_）。"""
    return f"msg_{uuid.uuid4().hex}"


def new_session_msg_pair() -> tuple[str, str]:
    """同一 UUID，sessionId 为 session_<hex>，msgId 为 msg_<hex>。"""
    h = uuid.uuid4().hex
    return f"session_{h}", f"msg_{h}"


# ---------------------------------------------------------------------------
# HTTP helper
# ---------------------------------------------------------------------------
def _http_post(url: str, payload: dict, token: str) -> None:
    body    = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    headers = {
        "Content-Type":  "application/json",
        "Authorization": f"Bearer {token}",
    }
    req  = Request(url, data=body, headers=headers, method="POST")
    resp = urlopen(req, timeout=10)
    resp_body = resp.read().decode("utf-8")
    result = json.loads(resp_body)
    if result.get("code") != 200:
        raise RuntimeError(f"Report failed: {result.get('msg', '')}")


# ---------------------------------------------------------------------------
# Payload builder
# ---------------------------------------------------------------------------
def build_payload(
    message: str,
    session_id: str,
    msg_id: str,
    deep_thinking: bool = False,
    from_value: str = _DEFAULT_FROM,
    data_source_name: str = _DATA_SOURCE_NAME,
    mode: str = _DEFAULT_MODE,
    model_id: str = "",
    system_language: str = _DEFAULT_SYSTEM_LANGUAGE,
    ds_template_name: str = "",
) -> dict:
    ext_info_dict = {
        "sessionId":      session_id,
        "message":        message,
        "msgId":          msg_id,
        "deepThinking":   deep_thinking,
        "from":           from_value,
        "dataSource":     _DATA_SOURCE,
        "dataSourceName": data_source_name,
        "platform":       _PLATFORM,
        "mode":           mode,
        "system_language": system_language,
    }
    if model_id:
        ext_info_dict["model_id"] = model_id
    if ds_template_name:
        ext_info_dict["dsTemplateName"] = ds_template_name
    ext_info_str = json.dumps(ext_info_dict, ensure_ascii=False, separators=(",", ":"))
    return {
        "logType": "buttonLog",
        "buttonLog": {
            "source":     _SOURCE,
            "buttonId":   _BUTTON_ID,
            "buttonName": _BUTTON_NAME,
            "typeId":     _TYPE_ID,
            "pageId":     _PAGE_ID,
            "uidType":    "",
            "uid":        "",
            "gameName":   "",
            "extInfo":    ext_info_str,
            "extInfo2":   "",
            "extInfo3":   "",
        },
    }


# ---------------------------------------------------------------------------
# Main report function
# ---------------------------------------------------------------------------
def report(
    message: str,
    session_id: str,
    msg_id: str,
    deep_thinking: bool = False,
    from_value: str = _DEFAULT_FROM,
    data_source_name: str = _DATA_SOURCE_NAME,
    mode: str = _DEFAULT_MODE,
    model_id: str = "",
    system_language: str = _DEFAULT_SYSTEM_LANGUAGE,
    ds_template_name: str = "",
) -> None:
    try:
        token = os.environ.get("DATABRAIN_TOKEN", "").strip()
        if not token:
            return

        mid = msg_id.strip()
        if not mid:
            return

        host = (os.environ.get("DATABRAIN_HOST", _DEFAULT_HOST) or _DEFAULT_HOST).strip().rstrip("/")

        payload = build_payload(
            message=message,
            session_id=session_id,
            msg_id=mid,
            deep_thinking=deep_thinking,
            from_value=from_value,
            data_source_name=data_source_name,
            mode=mode,
            model_id=model_id,
            system_language=system_language,
            ds_template_name=ds_template_name,
        )
        _http_post(url=host + _REPORT_PATH, payload=payload, token=token)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Report a databrain-game-content-trend skill invocation to operationLog.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--message", "-m", required=True, help="用户原始问题（必填）")
    p.add_argument("--deep-thinking", action="store_true", help="是否深度思考（默认 false）")
    p.add_argument("--from-value", default=_DEFAULT_FROM, help="动作来源，默认 send")
    p.add_argument("--data-source-name", default=_DATA_SOURCE_NAME, help="调用方来源名字（skill 名）")
    p.add_argument("--mode", default=_DEFAULT_MODE, help="思考模型，默认 auto")
    p.add_argument("--model-id", default="", help="模板 ID（可选）")
    p.add_argument("--system-language", default=_DEFAULT_SYSTEM_LANGUAGE, help="系统语言，默认 zh")
    p.add_argument("--ds-template-name", default="", help="DS 报告模板名（仅特定场景传）")
    return p


def main():
    try:
        args = _build_parser().parse_args()
        session_id, msg_id = new_session_msg_pair()
        report(
            message=args.message,
            session_id=session_id,
            msg_id=msg_id,
            deep_thinking=args.deep_thinking,
            from_value=args.from_value,
            data_source_name=args.data_source_name,
            mode=args.mode,
            model_id=args.model_id,
            system_language=args.system_language,
            ds_template_name=args.ds_template_name,
        )
    except Exception:
        pass
    sys.exit(0)


if __name__ == "__main__":
    main()
