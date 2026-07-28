#!/usr/bin/env python3
"""
舆情 AI 摘要报告：POST create_summary → 轮询 get_summary → 输出 report_zh / report_en。

与 databrain-opinion-metrics 一致：支持 DATABRAIN_HOST 显式设置或多域名 fallback、operationLog 打点。

用法:
    python scripts/get_opinion_summary.py \\
        --game_id u10000000066 \\
        --entity_type mobile \\
        --start_date 2026-03-01 \\
        [--end_date 2026-03-05] \\
        [--message "用户原始问题"] \\
        [--language zh en] \\
        [--channel twitter reddit steam] \\
        [--top_n 10] \\
        [--output_lang zh] \\
        [--task_type advanced|basic] \\
        [--date_type day|week|month|custom] \\
        [--json]

认证:
    DATABRAIN_TOKEN — 必填，Bearer token（脚本内自动加 Bearer 前缀）
    DATABRAIN_HOST  — 可选；未设置时按 intlgame → woa → global 顺序尝试
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import threading
import time
from pathlib import Path
from urllib.parse import urlparse

import httpx

from report_log import new_session_msg_pair, report

_CREATE_PATH = "/api/v1/opinion_pc/summary/advanced/create_summary"
_GET_PATH = "/api/v1/opinion_pc/summary/advanced/get_summary"

_FALLBACK_HOSTS = (
    "https://databrain.intlgame.com",
    "https://databrain.woa.com",
    "https://databrain-global.intlgame.com",
)

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_GAME_ID_RE = re.compile(r"^[ue][0-9a-f]+$")

_DEFAULT_BASIC_PROMPT = (
    "你是游戏社群专家，擅长根据玩家对游戏的评论进行专业的解读和分析洞察。"
    "请根据目前游戏的玩家评论生成简要可执行的摘要报告，需要重点突出 Top 3 个最积极和最消极的游戏相关话题（如果有），"
    "并为每个话题提供具体的例子。最后以简洁的可执行的摘要来结束报告，需要尽可能详细，并提供相关的评论示例。\n"
    "注意：所有内容必须根据提供的玩家评论进行回答，不要尝试编造话题结果和内容。不要使用 Markdown 文本格式输出。\n\n"
    "返回格式：\n"
    "GPT 摘要：\n"
    "<摘要>\n"
    "正面话题：\n"
    "<正面话题列表格式。编号．主题名称：玩家的主要意见，以及重点细节评论>\n"
    "负面话题：\n"
    "<负面话题格式列表。编号．主题名称：玩家主要意见，以及重点细节评论>\n"
    "可执行的摘要报告：\n"
    "中性话题：\n"
    "<中性话题格式列表。编号．主题名称：玩家主要意见，以及重点细节评论>\n"
    "可执行的摘要报告：\n"
    "<玩家意见概述，以及可执行性的建议>"
)

_resolved_host: str | None = None


def _validate_game_id(game_id: str) -> str:
    if not _GAME_ID_RE.match(game_id):
        print(
            f"[ERROR] Invalid game_id: {game_id!r}. "
            "Must start with 'u' (mobile) or 'e' (PC) followed by hex characters.",
            file=sys.stderr,
        )
        sys.exit(1)
    return game_id


def _validate_date(date_str: str, label: str = "date") -> str:
    if not _DATE_RE.match(date_str):
        print(
            f"[ERROR] Invalid {label}: {date_str!r}. Expected YYYY-MM-DD.",
            file=sys.stderr,
        )
        sys.exit(1)
    return date_str


def _load_dotenv() -> None:
    skill_dir = Path(__file__).parent.parent
    env_path = skill_dir / ".env"
    if env_path.is_file():
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, _, v = line.partition("=")
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    if k and os.environ.get(k) is None:
                        os.environ[k] = v


def _is_trusted_host(host: str) -> bool:
    hostname = urlparse(host).hostname or ""
    if hostname in ("databrain.intlgame.com", "databrain.woa.com"):
        return True
    if hostname.startswith("databrain-") and hostname.endswith(".intlgame.com"):
        return True
    return False


def _get_config() -> tuple[str, list[str]]:
    global _resolved_host
    _load_dotenv()
    token = os.environ.get("DATABRAIN_TOKEN", "").strip()
    if not token:
        print(
            "[ERROR] DATABRAIN_TOKEN not set. 请由服务端通过环境变量注入。",
            file=sys.stderr,
        )
        sys.exit(1)

    explicit = os.environ.get("DATABRAIN_HOST", "").strip().rstrip("/")
    if explicit:
        if not _is_trusted_host(explicit):
            print(
                f"[ERROR] DATABRAIN_HOST '{explicit}' 不在受信任域名列表中。",
                file=sys.stderr,
            )
            sys.exit(1)
        return token, [explicit]

    if _resolved_host:
        return token, [_resolved_host]

    return token, list(_FALLBACK_HOSTS)


def _headers(token: str) -> dict:
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }


def _resolve_id_type(entity_type: str, game_id: str) -> str:
    if entity_type == "mobile":
        return "unified_id"
    return "unified_edition_id" if len(game_id) > 15 else "edition_id"


def _do_report(message: str, session_id: str, msg_id: str) -> None:
    try:
        report(
            message=message or "databrain-opinion-summary",
            session_id=session_id,
            msg_id=msg_id,
        )
    except Exception:
        pass


def _start_report_thread(message: str, session_id: str, msg_id: str) -> threading.Thread:
    t = threading.Thread(
        target=_do_report,
        args=(message, session_id, msg_id),
        daemon=False,
    )
    t.start()
    return t


def create_summary_once(host: str, token: str, payload: dict) -> tuple[int, dict]:
    url = host + _CREATE_PATH
    with httpx.Client(timeout=30) as client:
        resp = client.post(url, json=payload, headers=_headers(token))
        if resp.status_code >= 400:
            preview = (resp.text or "").strip()[:800]
            print(
                f"[ERROR] create_summary HTTP {resp.status_code} @ {url}: {preview}",
                file=sys.stderr,
            )
        resp.raise_for_status()
        return resp.status_code, resp.json()


def create_summary_with_fallback(
    hosts: list[str], token: str, payload: dict
) -> tuple[str, str]:
    global _resolved_host
    last_data: dict | None = None
    last_http_err: str | None = None
    for h in hosts:
        try:
            _, data = create_summary_once(h, token, payload)
        except httpx.HTTPError as e:
            last_http_err = f"{h}: {e.__class__.__name__}: {e}"
            if len(hosts) > 1:
                print(f"[fallback] {h} create failed ({e.__class__.__name__}), next...", file=sys.stderr)
            continue
        last_data = data
        if data.get("code") != 0:
            if len(hosts) > 1:
                print(f"[fallback] {h} create code!=0: {data}, next...", file=sys.stderr)
            continue
        task_id = data.get("data", {}).get("task_id")
        if not task_id:
            if len(hosts) > 1:
                print(f"[fallback] {h} missing task_id in {data}, next...", file=sys.stderr)
            continue
        if len(hosts) > 1:
            _resolved_host = h
        print(f"[INFO] Task created: {task_id} (host={h})", file=sys.stderr)
        return h, task_id

    detail = last_data if last_data is not None else last_http_err
    print(f"[ERROR] create_summary failed on all hosts. Last: {detail}", file=sys.stderr)
    sys.exit(1)


def poll_summary(
    host: str,
    token: str,
    game_id: str,
    task_id: str,
    top_n: int,
    interval: float = 5.0,
    max_wait: float = 7200.0,
) -> dict:
    url = host + _GET_PATH
    payload = {"game_id": game_id, "task_id": task_id, "top_n": top_n}
    elapsed = 0.0
    with httpx.Client(timeout=30) as client:
        while elapsed < max_wait:
            resp = client.post(url, json=payload, headers=_headers(token))
            resp.raise_for_status()
            data = resp.json()
            if data.get("code") != 0:
                print(f"[ERROR] get_summary failed: {data}", file=sys.stderr)
                sys.exit(1)
            block = data.get("data")
            if not isinstance(block, dict):
                print(f"[ERROR] get_summary unexpected response (no data object): {data}", file=sys.stderr)
                sys.exit(1)
            task_status = block.get("task_status", "")
            print(f"[INFO] task_status={task_status} (elapsed={elapsed:.0f}s)", file=sys.stderr)
            if task_status == "success":
                return block
            if task_status in ("failed", "error"):
                print(
                    f"[ERROR] get_summary task failed: status={task_status!r} data={block}",
                    file=sys.stderr,
                )
                sys.exit(1)
            time.sleep(interval)
            elapsed += interval
    print(f"[ERROR] Timed out after {max_wait}s waiting for task {task_id}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="舆情 AI 摘要（create_summary + get_summary）")
    parser.add_argument("--game_id", required=True, help="unified_edition_id（u… 手游 / e… PC）")
    parser.add_argument(
        "--entity_type",
        required=True,
        choices=["mobile", "pc", "console"],
        help="平台类型；game_id 以 u 开头一般为 mobile，以 e 开头一般为 pc/console",
    )
    parser.add_argument("--start_date", required=True, help="开始日期 YYYY-MM-DD")
    parser.add_argument("--end_date", default=None, help="结束日期 YYYY-MM-DD，默认与 start_date 相同")
    parser.add_argument(
        "--message",
        default="",
        metavar="MSG",
        help="用户原始问题，用于埋点上报（建议总是传入）",
    )
    parser.add_argument("--language", nargs="*", default=[], help="语种过滤，如 zh en；不传表示全部")
    parser.add_argument("--channel", nargs="*", default=None, help="渠道过滤；不传表示全部")
    parser.add_argument(
        "--task_type",
        choices=["advanced", "basic"],
        default="basic",
        help="摘要类型：basic（默认）= 摘要报告；advanced = 含量化数据的高级报告（用户明确要求时使用）",
    )
    parser.add_argument(
        "--date_type",
        default="day",
        choices=["day", "week", "month", "custom"],
        help="create_summary 必填：时间粒度（JSON 字段 date_type，勿用 DateType）；单日/昨日用 day（默认）",
    )
    parser.add_argument("--prompt", default=None, help="basic 模式自定义 prompt")
    parser.add_argument("--top_n", type=int, default=10, help="各维度 Top-N，默认 10")
    parser.add_argument("--output_lang", choices=["zh", "en"], default="zh")
    parser.add_argument(
        "--json",
        action="store_true",
        help="将 get_summary 成功后的完整 data 对象以 JSON 打印到 stdout",
    )
    args = parser.parse_args()

    token, hosts = _get_config()
    session_id, msg_id = new_session_msg_pair()
    report_thread = _start_report_thread(args.message, session_id, msg_id)

    try:
        game_id = _validate_game_id(args.game_id.strip())
        start_date = _validate_date(args.start_date.strip(), "--start_date")
        end_raw = (args.end_date or args.start_date).strip()
        end_date = _validate_date(end_raw, "--end_date")
        if end_date < start_date:
            print(
                f"[ERROR] --end_date {end_date!r} is before --start_date {start_date!r}.",
                file=sys.stderr,
            )
            sys.exit(1)

        prompt = args.prompt
        if args.task_type == "basic" and not prompt:
            prompt = _DEFAULT_BASIC_PROMPT

        start_time = f"{start_date} 00:00:00"
        end_time = f"{end_date} 23:59:59"
        channels = args.channel or []
        id_type = _resolve_id_type(args.entity_type, game_id)
        print(f"[INFO] id_type={id_type} (game_id len={len(game_id)})", file=sys.stderr)

        create_payload: dict = {
            "task_type": args.task_type,
            "start_time": start_time,
            "end_time": end_time,
            "edition_unified_id": game_id,
            "entity_type": args.entity_type,
            "id_type": id_type,
            # API 必填；字段名为 snake_case date_type（非 DateType）。缺省会导致 HTTP 400。
            "date_type": args.date_type,
        }
        if args.language:
            create_payload["language"] = args.language
        if channels:
            create_payload["channel"] = channels
        if args.task_type == "basic" and prompt:
            create_payload["prompt"] = prompt

        print(f"[DEBUG] create_summary payload: {json.dumps(create_payload, ensure_ascii=False)}", file=sys.stderr)
        host, task_id = create_summary_with_fallback(hosts, token, create_payload)
        report_data = poll_summary(host, token, game_id, task_id, args.top_n)

        if args.json:
            print(json.dumps(report_data, ensure_ascii=False, indent=2))
            return

        report_key = "report_zh" if args.output_lang == "zh" else "report_en"
        report_text = report_data.get(report_key, "")
        if not report_text:
            fallback_key = "report_en" if args.output_lang == "zh" else "report_zh"
            report_text = report_data.get(fallback_key, "")

        if not report_text:
            print("[WARN] Report is empty.", file=sys.stderr)

        print(report_text)
    finally:
        report_thread.join(timeout=1.0)


if __name__ == "__main__":
    main()
