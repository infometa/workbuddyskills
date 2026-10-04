#!/usr/bin/env python3
"""Render an fbt_apply_order draft preview into the WorkBuddy workspace."""

from __future__ import annotations

import argparse
import base64
import hashlib
import html
import json
import os
import re
import secrets
import sys
import tempfile
from pathlib import Path
from urllib.parse import parse_qsl, quote, urlencode, urlparse, urlunparse


MAX_PAYLOAD_BYTES = 512 * 1024
ALLOWED_EDIT_HOST_SUFFIXES = ("fenbeitong.com", "fenbeijinfu.com")
EDIT_PATH = "/nonav/normal/views/customForm/add"
START_MARKER = "[DRAFT_PREVIEW_PAYLOAD_V1]"
END_MARKER = "[/DRAFT_PREVIEW_PAYLOAD_V1]"


def _text(value: object, fallback: str = "-") -> str:
    if value in (None, "", [], {}):
        return fallback
    return html.escape(str(value))


def _amount(value: object) -> str:
    try:
        return f"¥{float(value):,.2f}"
    except (TypeError, ValueError):
        return "-"


def _payload_digest(payload: dict) -> str:
    canonical_payload = dict(payload)
    canonical_payload.pop("integrity_sha256", None)
    canonical = json.dumps(
        canonical_payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _valid_integrity(payload: dict) -> bool:
    expected = str(payload.get("integrity_sha256") or "")
    return bool(expected) and secrets.compare_digest(expected, _payload_digest(payload))


def _decode_payload(encoded: str, *, require_integrity: bool = True) -> dict:
    try:
        raw = base64.b64decode(encoded.encode("ascii"), altchars=b"-_", validate=True)
    except (UnicodeEncodeError, ValueError) as exc:
        raise ValueError("草稿预览载荷不是有效的 Base64") from exc
    if len(raw) > MAX_PAYLOAD_BYTES:
        raise ValueError("草稿预览载荷超过 512 KiB 限制")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("草稿预览载荷不是有效的 UTF-8 JSON") from exc
    if not isinstance(payload, dict):
        raise ValueError("草稿预览载荷必须是 JSON object")
    if payload.get("version") != 1 or payload.get("kind") != "fbt_apply_order_draft":
        raise ValueError("不支持的草稿预览载荷版本")
    if not isinstance(payload.get("application"), dict):
        raise ValueError("草稿预览载荷缺少 application")
    if require_integrity and not _valid_integrity(payload):
        raise ValueError("草稿预览载荷完整性校验失败")
    return payload


def _marker_payloads(text: str):
    cursor = 0
    while True:
        start = text.find(START_MARKER, cursor)
        if start < 0:
            return
        start += len(START_MARKER)
        end = text.find(END_MARKER, start)
        if end < 0:
            return
        encoded = text[start:end].strip()
        if encoded:
            yield encoded
        cursor = end + len(END_MARKER)


def _recover_from_workbuddy_session(apply_id: str) -> dict | None:
    """Read the exact MCP result instead of trusting model-copied opaque data."""
    session_id = os.environ.get("CODEBUDDY_SESSION_ID") or os.environ.get("CLAUDE_SESSION_ID")
    if not session_id or not apply_id:
        return None
    projects_root = Path.home() / ".workbuddy" / "projects"
    if not projects_root.is_dir():
        return None
    candidates = sorted(
        projects_root.glob(f"**/{session_id}.jsonl"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    for transcript in candidates:
        try:
            lines = transcript.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for line in reversed(lines):
            if START_MARKER not in line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if record.get("type") != "function_call_result":
                continue
            output = record.get("output") or {}
            text = output.get("text") if isinstance(output, dict) else ""
            if not isinstance(text, str):
                continue
            for encoded in _marker_payloads(text):
                try:
                    payload = _decode_payload(encoded, require_integrity=False)
                except ValueError:
                    continue
                # New MCP results must pass their embedded digest. Old results
                # predate the digest and are accepted only from this exact
                # function_call_result transcript, never from model-copied CLI.
                if payload.get("integrity_sha256") and not _valid_integrity(payload):
                    continue
                if str(payload.get("apply_id") or "") == apply_id:
                    return payload
    return None


def _load_payload(encoded: str) -> dict:
    try:
        return _decode_payload(encoded)
    except ValueError as original_error:
        try:
            copied = _decode_payload(encoded, require_integrity=False)
        except ValueError:
            raise original_error
        recovered = _recover_from_workbuddy_session(str(copied.get("apply_id") or ""))
        if recovered is None:
            raise original_error
        return recovered


def _session_lookup_report(apply_id: str) -> list:
    """逐步检查会话记录恢复链路，返回可读诊断行。"""
    lines = []
    env_key = next((k for k in ("CODEBUDDY_SESSION_ID", "CLAUDE_SESSION_ID")
                    if os.environ.get(k)), None)
    session_id = os.environ.get(env_key, "") if env_key else ""
    lines.append(f"[1] session 环境变量 : {env_key or '未设置(CODEBUDDY_SESSION_ID / CLAUDE_SESSION_ID 都为空)'}")
    lines.append(f"[2] session_id       : {session_id or '(空)'}")

    root = Path.home() / ".workbuddy" / "projects"
    lines.append(f"[3] projects 目录    : {root} -> {'存在' if root.is_dir() else '不存在'}")
    if not session_id or not root.is_dir():
        lines.append("[!] 链路中断：拿不到 session_id 或找不到 projects 目录")
        return lines

    files = sorted(root.glob(f"**/{session_id}.jsonl"),
                   key=lambda path: path.stat().st_mtime, reverse=True)
    lines.append(f"[4] 匹配 transcript  : {len(files)} 个")
    if not files:
        lines.append("[!] 链路中断：没有与当前 session_id 同名的 .jsonl")
    return lines


def _load_payload_by_apply_id(apply_id: str, verbose: bool) -> dict:
    """只凭 apply_id 从会话记录取回原始载荷，模型无需搬运 Base64。"""
    if verbose:
        print("\n".join("  " + line for line in _session_lookup_report(apply_id)),
              file=sys.stderr)
    payload = _recover_from_workbuddy_session(apply_id)
    if payload is None:
        raise ValueError(
            "未能从当前 WorkBuddy 会话记录中找到该 apply_id 的草稿载荷；"
            "请改用 --payload-base64 传入完整载荷"
        )
    return payload


def _safe_edit_url(value: object) -> str:
    """校验编辑链接。

    编辑链接现在优先走短链服务（短链域名不可预知，域名/路径白名单无法覆盖），
    因此这里只做协议校验，挡住 javascript:/data: 一类伪协议。防伪造依赖载荷的
    integrity_sha256 与会话记录恢复这两层，域名白名单原本只是第三层冗余。
    仍是分贝通长链时按原规则规范化 query，避免多余参数进入页面。
    """
    url = str(value or "").strip()
    if not url:
        return ""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        return ""

    host = parsed.hostname.lower()
    is_fenbeitong_long_url = any(
        host == suffix or host.endswith("." + suffix)
        for suffix in ALLOWED_EDIT_HOST_SUFFIXES
    ) and parsed.path == EDIT_PATH
    if not is_fenbeitong_long_url:
        return url                      # 短链原样放行

    query_items = parse_qsl(parsed.query, keep_blank_values=True)
    apply_ids = [value for key, value in query_items if key == "apply_id" and value]
    if len(apply_ids) != 1:
        return ""
    query_values = {key: value for key, value in query_items}
    normalized_items = [("apply_id", apply_ids[0])]
    # createTime 是工具侧加的防缓存参数，剔除它会让同一草稿的多次预览地址相同
    for key in ("title", "state", "token", "createTime"):
        value = query_values.get(key)
        if value:
            normalized_items.append((key, value))
    normalized_query = urlencode(
        normalized_items,
        quote_via=quote,
        encoding="utf-8",
        errors="strict",
    )
    return urlunparse(parsed._replace(query=normalized_query))


def _render(payload: dict) -> str:
    application = dict(payload["application"])
    application.setdefault("apply_id", payload.get("apply_id"))
    edit_url = _safe_edit_url(payload.get("edit_url"))

    dates = " 至 ".join(
        value
        for value in (
            str(application.get("start_date") or ""),
            str(application.get("end_date") or ""),
        )
        if value
    ) or "-"
    cities = "、".join(str(item) for item in application.get("cities") or []) or "-"
    departments = "、".join(str(item) for item in application.get("departments") or []) or "-"

    trip_rows: list[str] = []
    for item in application.get("trip_items") or []:
        if not isinstance(item, dict):
            continue
        route = " → ".join(
            value
            for value in (
                str(item.get("start_city") or ""),
                str(item.get("arrival_city") or ""),
            )
            if value
        )
        if not route:
            route = "、".join(str(value) for value in item.get("cities") or [])
        route = route or str(item.get("city") or "-")
        item_dates = " 至 ".join(
            value
            for value in (
                str(item.get("start_date") or ""),
                str(item.get("end_date") or ""),
            )
            if value
        ) or "-"
        trip_rows.append(
            "<tr>"
            f"<td>{_text(item.get('category'))}</td>"
            f"<td>{_text(route)}</td>"
            f"<td>{_text(item_dates)}</td>"
            f'<td class="amount">{_amount(item.get("estimated_amount"))}</td>'
            "</tr>"
        )
    if not trip_rows:
        trip_rows.append('<tr><td colspan="4" class="empty">暂无申请项</td></tr>')

    edit_button = (
        f'<a class="primary" href="{html.escape(edit_url, quote=True)}" '
        'target="_blank" rel="noopener noreferrer" referrerpolicy="no-referrer">编辑草稿</a>'
        if edit_url
        else '<span class="disabled">编辑入口暂不可用</span>'
    )
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="referrer" content="no-referrer">
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
  <title>{_text(application.get('form_name'), '申请单草稿')}</title>
  <style>
    *{{box-sizing:border-box}}
    body{{margin:0;background:#f5f6f8;color:#1f2329;font:14px/1.55 -apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif}}
    main{{max-width:920px;margin:0 auto;padding:28px 24px 40px}}
    header{{display:flex;align-items:flex-start;justify-content:space-between;gap:20px;margin-bottom:22px}}
    h1{{font-size:22px;line-height:1.35;margin:0 0 6px;font-weight:650}}
    .id{{color:#646a73;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12px}}
    .status{{display:inline-flex;align-items:center;padding:4px 9px;border-radius:4px;background:#fff3e8;color:#b74f00;font-size:12px;white-space:nowrap}}
    section{{background:#fff;border:1px solid #e5e6eb;border-radius:8px;margin-bottom:16px;padding:20px}}
    h2{{font-size:15px;margin:0 0 16px}}
    dl{{display:grid;grid-template-columns:120px minmax(0,1fr) 120px minmax(0,1fr);gap:14px 18px;margin:0}}
    dt{{color:#646a73}} dd{{margin:0;overflow-wrap:anywhere}}
    table{{width:100%;border-collapse:collapse;table-layout:fixed}}
    th,td{{padding:11px 10px;border-bottom:1px solid #eef0f3;text-align:left;vertical-align:top;overflow-wrap:anywhere}}
    th{{color:#646a73;font-size:12px;font-weight:500;background:#fafbfc}}
    .amount{{text-align:right;font-variant-numeric:tabular-nums}} .empty{{text-align:center;color:#8f959e}}
    footer{{display:flex;justify-content:space-between;align-items:center;gap:16px;margin-top:22px}}
    .note{{color:#8f959e;font-size:12px}}
    .primary,.disabled{{display:inline-flex;align-items:center;justify-content:center;min-width:104px;height:36px;padding:0 16px;border-radius:6px;text-decoration:none;font-weight:550}}
    .primary{{background:#ff8e22;color:#fff}} .primary:hover{{background:#ed7d10}}
    .disabled{{background:#e5e6eb;color:#8f959e}}
    @media(max-width:680px){{main{{padding:18px 14px 28px}}header{{align-items:center}}dl{{grid-template-columns:96px minmax(0,1fr)}}section{{padding:16px}}th:nth-child(3),td:nth-child(3){{display:none}}footer{{align-items:flex-end}}}}
  </style>
</head>
<body>
  <main>
    <header>
      <div><h1>{_text(application.get('form_name'), '申请单草稿')}</h1><div class="id">{_text(application.get('apply_id'))}</div></div>
      <span class="status">{_text(application.get('state_name'), '待提交')}</span>
    </header>
    <section>
      <h2>申请信息</h2>
      <dl>
        <dt>申请事由</dt><dd>{_text(application.get('reason'))}</dd>
        <dt>预估金额</dt><dd>{_amount(application.get('estimated_amount'))}</dd>
        <dt>出差日期</dt><dd>{_text(dates)}</dd>
        <dt>出差城市</dt><dd>{_text(cities)}</dd>
        <dt>所属部门/项目</dt><dd>{_text(departments)}</dd>
        <dt>补充说明</dt><dd>{_text(application.get('description'), '无')}</dd>
      </dl>
    </section>
    <section>
      <h2>申请项</h2>
      <table><thead><tr><th>类型</th><th>行程</th><th>日期</th><th class="amount">金额</th></tr></thead>
      <tbody>{''.join(trip_rows)}</tbody></table>
    </section>
    <footer>
      <span class="note">编辑页使用分贝通正常网页登录态。</span>
      {edit_button}
    </footer>
  </main>
</body>
</html>"""


def _write_preview(payload: dict, output_dir: Path) -> Path:
    apply_id = str(payload.get("apply_id") or "draft").strip()
    safe_apply_id = re.sub(r"[^A-Za-z0-9._-]+", "_", apply_id)[:120] or "draft"
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / f"apply-draft-{safe_apply_id}.html"
    rendered = _render(payload)

    temp_path: str | None = None
    try:
        fd, temp_path = tempfile.mkstemp(prefix=f".{target.name}.", dir=output_dir)
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(rendered)
        # POSIX uses this to keep the draft private; Windows may ignore POSIX
        # mode bits, so the workspace's filesystem ACLs remain authoritative.
        os.chmod(temp_path, 0o600)
        os.replace(temp_path, target)
    finally:
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description="生成 WorkBuddy 申请单草稿预览")
    # 二选一：优先 --apply-id（模型只需复制一个 id，不搬运 Base64）
    parser.add_argument("--apply-id")
    parser.add_argument("--payload-base64")
    parser.add_argument("--output-dir", default="outputs")
    parser.add_argument("--diagnose", action="store_true",
                        help="把会话记录查找过程打到 stderr，用于排查恢复链路")
    args = parser.parse_args()
    if not args.apply_id and not args.payload_base64:
        parser.error("需要 --apply-id 或 --payload-base64 其中之一")
    try:
        if args.apply_id:
            payload = _load_payload_by_apply_id(args.apply_id.strip(), args.diagnose)
        else:
            payload = _load_payload(args.payload_base64.strip())
        target = _write_preview(payload, Path(args.output_dir))
    except (OSError, ValueError) as exc:
        print(f"生成申请单草稿预览失败：{exc}", file=sys.stderr)
        return 2
    print(json.dumps({
        "apply_id": payload.get("apply_id"),
        "draft_html_path": str(target),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
