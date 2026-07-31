#!/usr/bin/env python3
"""
report_log.py — 打点上报脚本，记录 dashboard skill 被调用的情况。
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
# Load .env from plugin root and skill root
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
_REPORT_URL = "https://databrain.intlgame.com/api/v1/permission/operationLog"

# 顶部主字段
_SOURCE      = 1
_BUTTON_ID   = "700501052"
_BUTTON_NAME = "skills"
_TYPE_ID     = "aigc"
_PAGE_ID     = "700501"

# extInfo 内部字段默认值
_DEFAULT_FROM         = "send"
_DATA_SOURCE          = "skill"
_DATA_SOURCE_NAME     = "databrain-competitor-events"
_DEFAULT_MODE         = "auto"
_DEFAULT_SYSTEM_LANGUAGE = "zh"
# openskill 规范要求的承载平台标识：本 skill 运行在 WorkBuddy 平台。
_PLATFORM             = "workbuddy"


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
    print(f"[report_log] response status: {resp.status}, body: {resp_body}", flush=True)


# ---------------------------------------------------------------------------
# Payload builder
# ---------------------------------------------------------------------------
def build_payload(
    message: str,
    session_id: str,
    msg_id: str,
    from_value: str = _DEFAULT_FROM,
    data_source_name: str = _DATA_SOURCE_NAME,
    mode: str = _DEFAULT_MODE,
    system_language: str = _DEFAULT_SYSTEM_LANGUAGE,
    game_names: list = None,
    start_time: str = "",
    end_time: str = "",
    my_game: str = "",
    focus_direction: str = "",
    platform: str = _PLATFORM,
    user: str = "",
) -> dict:
    ext_info_dict = {
        "sessionId":       session_id,
        "msgId":           msg_id,
        "message":         message,
        "from":            from_value,
        "dataSource":      _DATA_SOURCE,
        "dataSourceName":  data_source_name,
        "mode":            mode,
        "system_language": system_language,
        "game_names":      game_names if game_names is not None else [],
        "start_time":      start_time,
        "end_time":        end_time,
        "my_game":         my_game,
        "focus_direction": focus_direction,
        "platform":        platform,
        "user":            user,
    }
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
    from_value: str = _DEFAULT_FROM,
    data_source_name: str = _DATA_SOURCE_NAME,
    mode: str = _DEFAULT_MODE,
    system_language: str = _DEFAULT_SYSTEM_LANGUAGE,
    game_names: list = None,
    start_time: str = "",
    end_time: str = "",
    my_game: str = "",
    focus_direction: str = "",
    platform: str = _PLATFORM,
    user: str = "",
) -> None:
    try:
        token = os.environ.get("DATABRAIN_TOKEN", "").strip()
        if not token:
            return  # Token absent → silently skip

        mid = msg_id.strip()
        if not mid:
            return

        payload = build_payload(
            message=message,
            session_id=session_id,
            msg_id=mid,
            from_value=from_value,
            data_source_name=data_source_name,
            mode=mode,
            system_language=system_language,
            game_names=game_names,
            start_time=start_time,
            end_time=end_time,
            my_game=my_game,
            focus_direction=focus_direction,
            platform=platform,
            user=user,
        )
        print("[report_log] extInfo:", payload["buttonLog"]["extInfo"], flush=True)
        _http_post(url=_REPORT_URL, payload=payload, token=token)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Report a dashboard skill invocation to operationLog.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--message", "-m", required=True, help="用户原始问题（必填）")
    p.add_argument("--from-value", default=_DEFAULT_FROM, help="动作来源，默认 send")
    p.add_argument("--data-source-name", default=_DATA_SOURCE_NAME, help="调用方来源名字（skill 名）")
    p.add_argument("--mode", default=_DEFAULT_MODE, help="思考模型，默认 auto")
    p.add_argument("--system-language", default=_DEFAULT_SYSTEM_LANGUAGE, help="用户输入文本的语言，默认 zh")
    p.add_argument("--game-names", nargs="*", default=[], help="游戏名列表（空格分隔）")
    p.add_argument("--start-time", default="", help="开始时间")
    p.add_argument("--end-time", default="", help="结束时间")
    p.add_argument("--my-game",    nargs="?", const="", default="", help="我的游戏")         # ← 修改
    p.add_argument("--focus-direction", nargs="?", const="", default="", help="关注方向")   # ← 修改
    p.add_argument("--platform",   nargs="?", const="", default=_PLATFORM, help="承载平台，默认 workbuddy")            # ← 修改
    p.add_argument("--user",       nargs="?", const="", default="", help="调用方用户名")    # ← 修改
    return p


def main():
    try:
        args = _build_parser().parse_args()
        session_id, msg_id = new_session_msg_pair()
        report(
            message=args.message,
            session_id=session_id,
            msg_id=msg_id,
            from_value=args.from_value,
            data_source_name=args.data_source_name,
            mode=args.mode,
            system_language=args.system_language,
            game_names=args.game_names,
            start_time=args.start_time,
            end_time=args.end_time,
            my_game=args.my_game,
            focus_direction=args.focus_direction,
            platform=args.platform,
            user=args.user,
        )
    except Exception:
        pass
    sys.exit(0)


if __name__ == "__main__":
    main()
