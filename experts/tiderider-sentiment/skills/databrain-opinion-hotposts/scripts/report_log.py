#!/usr/bin/env python3
"""
report_log.py — 打点上报，记录 databrain-opinion-hotposts skill 被调用的情况。
reference: http://databrain-docs.intlgame.com/docs/proxy/proxy-1h7trs9fhm16i

Credentials:
    DATABRAIN_TOKEN — 认证 token；缺失时静默跳过上报
    DATABRAIN_HOST  — 若已设置则只用该 host；否则按优先级 fallback
"""

import argparse
import json
import os
import sys
import uuid
from pathlib import Path
from urllib.request import Request, urlopen

_ENV_FILE = Path(__file__).parent.parent / ".env"


def _load_env(path: Path) -> None:
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


_load_env(_ENV_FILE)

_FALLBACK_HOSTS = (
    "https://databrain.intlgame.com",
    "https://databrain.woa.com",
    "https://databrain-global.intlgame.com",
)
_REPORT_PATH = "/api/v1/permission/operationLog"

_BUTTON_ID        = "700501052"
_BUTTON_NAME      = "skills"
_TYPE_ID          = "aigc"
_PAGE_ID          = "700501"
_SOURCE           = 1
_DATA_SOURCE      = "skill"
_DATA_SOURCE_NAME = "ex-databrain-opinion-hotposts"
_DEFAULT_FROM     = "send"
_DEFAULT_MODE     = "auto"
_DEFAULT_SYSTEM_LANGUAGE = "zh"


def new_session_msg_pair() -> tuple[str, str]:
    h = uuid.uuid4().hex
    return f"session_{h}", f"msg_{h}"


def _http_post(url: str, payload: dict, token: str) -> None:
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    req = Request(url, data=body, headers=headers, method="POST")
    resp = urlopen(req, timeout=10)
    result = json.loads(resp.read().decode("utf-8"))
    if result.get("code") != 0:
        raise RuntimeError(f"Report failed: {result.get('msg', '')}")


def build_payload(message: str, session_id: str, msg_id: str,
                  data_source_name: str = _DATA_SOURCE_NAME) -> dict:
    ext_info = {
        "sessionId": session_id,
        "message": message,
        "msgId": msg_id,
        "deepThinking": False,
        "from": _DEFAULT_FROM,
        "dataSource": _DATA_SOURCE,
        "dataSourceName": data_source_name,
        "mode": _DEFAULT_MODE,
        "system_language": _DEFAULT_SYSTEM_LANGUAGE,
    }
    return {
        "logType": "buttonLog",
        "buttonLog": {
            "source": _SOURCE,
            "buttonId": _BUTTON_ID,
            "buttonName": _BUTTON_NAME,
            "typeId": _TYPE_ID,
            "pageId": _PAGE_ID,
            "uidType": "",
            "uid": "",
            "gameName": "",
            "extInfo": json.dumps(ext_info, ensure_ascii=False, separators=(",", ":")),
            "extInfo2": "",
            "extInfo3": "",
        },
    }


def report(message: str, session_id: str, msg_id: str,
           data_source_name: str = _DATA_SOURCE_NAME) -> None:
    try:
        token = os.environ.get("DATABRAIN_TOKEN", "").strip()
        if not token or not msg_id.strip():
            return
        explicit = os.environ.get("DATABRAIN_HOST", "").strip().rstrip("/")
        hosts = [explicit] if explicit else list(_FALLBACK_HOSTS)
        payload = build_payload(message, session_id, msg_id.strip(), data_source_name)
        for h in hosts:
            try:
                _http_post(h + _REPORT_PATH, payload, token)
                return
            except Exception:
                continue
    except Exception:
        pass


def main():
    p = argparse.ArgumentParser(description="Test report for databrain-opinion-alert skill.")
    p.add_argument("--message", "-m", required=True)
    args = p.parse_args()
    session_id, msg_id = new_session_msg_pair()
    report(args.message, session_id, msg_id)
    sys.exit(0)


if __name__ == "__main__":
    main()
