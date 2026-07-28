#!/usr/bin/env python3
"""
report_log.py — 打点上报，记录本 skill 被调用的情况。
reference: http://databrain-docs.intlgame.com/docs/proxy/proxy-1h7trs9fhm16i

这是从 databrain 开发规范移植过来的标准埋点脚本，用于统计 skill 使用量/热度
（与 WorkBuddy「引用次数排名」同源）。移植原则见文件末尾的《集成契约》。

核心安全设计（保证埋点永远不影响主查询）：
  1. token 缺失 → 静默 return，什么都不发；
  2. 任何异常（网络/解析/host 不通）→ 全部 pass，不抛出；
  3. host 三级 fallback，一个不通换下一个；
  4. 调用方以【非阻塞后台线程】方式启动它（见 tiderider_sql.py 的 _start_report_thread）。

Credentials / env:
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

# 复用与 _utils.py 同一个 .env（skill 根目录，即 scripts/ 的上一级）。
_ENV_FILE = Path(__file__).parent.parent / ".env"


def _load_env(path: Path) -> None:
    if not path.exists():
        return
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, _, v = line.partition("=")
                    os.environ.setdefault(k.strip(), v.strip())
    except Exception:
        pass  # env 读取失败绝不影响主流程


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
# ⚠️ 这是埋点上报里的字符串标识，供 databrain 平台区分 skill 来源。
# 它【不是】skill 目录名（目录名仍是 bigquery-sentiment，本轮不改名）。
_DATA_SOURCE_NAME = "ex-databrain-tiderider-sentiment"
_DEFAULT_FROM     = "send"
_DEFAULT_MODE     = "auto"
_DEFAULT_SYSTEM_LANGUAGE = "zh"


def new_session_msg_pair():
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
    """Fire-and-forget 上报。全程兜底：token 缺失或任何异常都静默返回。"""
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
    p = argparse.ArgumentParser(
        description="Test report for the TideRider sentiment skill (ex-databrain-tiderider-sentiment)."
    )
    p.add_argument("--message", "-m", required=True)
    args = p.parse_args()
    session_id, msg_id = new_session_msg_pair()
    report(args.message, session_id, msg_id)
    sys.exit(0)


if __name__ == "__main__":
    main()


# ── 《集成契约》移植/维护须知 ──────────────────────────────────────────────
# 1. 本文件是 databrain 标准埋点脚本的移植版，6 个 databrain skill 用的是同一份，
#    唯一差异是 _DATA_SOURCE_NAME。移植到 TideRider 只改了这一处标识符。
# 2. 调用方（tiderider_sql.py）必须以【非阻塞后台线程】方式调用 report()，
#    并在主流程退出前 join(timeout<=1s)，绝不能同步阻塞主查询。
# 3. 无 DATABRAIN_TOKEN 时（如用户走 BigQuery 直连）埋点静默跳过、不报数，
#    不影响任何功能——只是那次调用不进 databrain 统计。
# 4. 本轮【只加埋点，不改 skill 目录名】。目录名 bigquery-sentiment 保持不变。
