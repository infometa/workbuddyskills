#!/usr/bin/env python3
"""AI-Shifu Course CLI - Unified tool for course CRUD operations."""

import argparse
import json
import os
import re
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv, set_key

# ── Constants ──────────────────────────────────────────────────────────────────
ENV_FILE = Path(__file__).resolve().parent.parent / ".env"

DEFAULT_BASE_URL = "https://app.ai-shifu.cn"


# ── Shared Infrastructure ──────────────────────────────────────────────────────
def load_env():
    """Load environment variables from the skill's .env file."""
    if ENV_FILE.exists():
        load_dotenv(dotenv_path=ENV_FILE, override=False)


def save_env(token):
    """Persist token to the skill's .env file."""
    env_path = str(ENV_FILE)
    if not ENV_FILE.exists():
        ENV_FILE.parent.mkdir(parents=True, exist_ok=True)
        ENV_FILE.touch(mode=0o600)
    set_key(env_path, "SHIFU_TOKEN", token)
    os.chmod(env_path, 0o600)


def resolve_auth(args):
    """Resolve token from CLI args or .env. Base URL is fixed to DEFAULT_BASE_URL."""
    token = getattr(args, "token", None) or os.environ.get("SHIFU_TOKEN")
    if not token:
        print("Error: no token available. Run 'shifu-cli.py login' first, "
              "or use --token / set SHIFU_TOKEN in .env")
        sys.exit(1)

    return DEFAULT_BASE_URL, token


def api(base_url, token, method, path, **kwargs):
    """Make an API call, exit on error."""
    url = f"{base_url}/api/shifu{path}"
    headers = {"Cookie": f"token={token}", "Content-Type": "application/json"}
    kwargs.setdefault("timeout", 30)
    resp = getattr(requests, method)(url, headers=headers, **kwargs)
    if not resp.ok:
        print(f"API error: {method.upper()} {path} (HTTP {resp.status_code})")
        print(f"  Response: {resp.text[:500]}")
        sys.exit(1)
    data = resp.json()
    if data.get("code") != 0:
        print(f"API error: {method.upper()} {path}")
        print(f"  Response: {json.dumps(data, ensure_ascii=False)}")
        sys.exit(1)
    return data.get("data")


def api_safe(base_url, token, method, path, **kwargs):
    """Make an API call, return None on error instead of exiting."""
    url = f"{base_url}/api/shifu{path}"
    headers = {"Cookie": f"token={token}", "Content-Type": "application/json"}
    kwargs.setdefault("timeout", 30)
    try:
        resp = getattr(requests, method)(url, headers=headers, **kwargs)
        if not resp.ok:
            return None
        data = resp.json()
        if data.get("code") != 0:
            return None
        return data.get("data")
    except (requests.RequestException, json.JSONDecodeError):
        return None


def api_upload(base_url, token, filename, file_bytes, mime, resource_id=None):
    """POST multipart to /api/shifu/upfile. Exits on transport / business error.

    Kept separate from api() because requests must control the multipart
    Content-Type (with boundary) itself — api() pins application/json.
    """
    url = f"{base_url}/api/shifu/upfile"
    headers = {"Cookie": f"token={token}"}
    files = {"file": (filename, file_bytes, mime)}
    data = {"resource_id": resource_id} if resource_id else None
    try:
        resp = requests.post(url, headers=headers, files=files, data=data, timeout=60)
    except requests.RequestException as e:
        print(f"API transport error: POST /upfile ({e})")
        sys.exit(1)
    if not resp.ok:
        print(f"API error: POST /upfile (HTTP {resp.status_code})")
        print(f"  Response: {resp.text[:500]}")
        sys.exit(1)
    try:
        payload = resp.json()
    except json.JSONDecodeError:
        print("API error: POST /upfile returned non-JSON response")
        print(f"  Response: {resp.text[:500]}")
        sys.exit(1)
    if payload.get("code") != 0:
        print("API error: POST /upfile")
        print(f"  Response: {json.dumps(payload, ensure_ascii=False)}")
        sys.exit(1)
    return payload.get("data")


def _post_creator_analytics(base_url, token, path, body, session=None):
    """POST to a /api/creator-analytics/<path> endpoint with auth headers.

    Shared transport helper for the DSL query and credit-detail endpoints.
    Returns (transport_ok, payload). Non-zero business codes do NOT raise —
    callers need to surface them. ``session`` is an optional
    :class:`requests.Session` for TCP / TLS connection reuse when the caller
    is fanning out many small queries.
    """

    # Tolerate `path` with or without a leading slash — callers in this
    # file consistently pass "/query" / "/credit-detail", but stripping
    # guards against a future caller forgetting the slash, which would
    # otherwise produce "/api/creator-analyticsquery". Flagged on PR #49
    # review.
    url = f"{base_url}/api/creator-analytics/{path.lstrip('/')}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Token": token,
        "Content-Type": "application/json",
    }
    http = session if session is not None else requests
    try:
        resp = http.post(url, headers=headers, json=body, timeout=30)
    except requests.RequestException as e:
        return False, {"transport_error": str(e)}
    if not resp.ok:
        return False, {"http_status": resp.status_code, "text": resp.text[:1000]}
    try:
        return True, resp.json()
    except json.JSONDecodeError:
        return False, {"parse_error": "non-JSON response", "text": resp.text[:1000]}


def api_analytics(base_url, token, body, session=None):
    """POST a DSL query to /api/creator-analytics/query."""
    return _post_creator_analytics(base_url, token, "/query", body, session=session)


def api_credit_detail(base_url, token, body, session=None):
    """POST to /api/creator-analytics/credit-detail.

    Unlike ``api_analytics``, this endpoint is not DSL-based — it expects a
    fixed schema (``shifu_bid`` + optional date/scene/type filters and
    pagination) and the backend handles the bill_usage x credit_ledger_entries
    join server-side. See ``cmd_credit_detail`` for the CLI surface.
    """
    return _post_creator_analytics(
        base_url, token, "/credit-detail", body, session=session
    )


def safe_join_path(base_dir, filename):
    """Safely join base_dir and filename, preventing path traversal attacks."""
    joined = os.path.realpath(os.path.join(base_dir, filename))
    base = os.path.realpath(base_dir)
    if not joined.startswith(base + os.sep) and joined != base:
        print(f"Warning: path traversal detected, rejecting: {filename}")
        return None
    return joined


def fmt_time(ts):
    """Format an ISO timestamp for display, return '' if missing."""
    if not ts:
        return ""
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return ts[:16] if len(ts) >= 16 else ts


def _print_verification_urls(base_url, shifu_bid, include_published=False):
    """Print admin + course preview, and (when published) the public URL.

    Skill docs instruct the LLM to transcribe these lines verbatim. Do not
    let the LLM reconstruct URLs from a template — that has historically led
    to wrong path (/shifu vs /c) and wrong param name (outline_bid vs lessonid).

    `include_published=True` adds the public student-facing URL (no preview
    query param). Callers should set it only when the course is known to be
    in a published state (e.g. right after `publish`, or in `show` which
    queries existing courses that are typically already published).
    Lesson-level URLs are intentionally not printed — they bloat reports for
    multi-lesson courses; build one on demand via `show <shifu_bid>` if needed.
    """
    print("\nVerification URLs:")
    print(f"  Admin console:    {base_url}/shifu/{shifu_bid}")
    print("    # 课程的管理后台地址：需要管理课程的内容、设置小节是否隐藏、是否付费等，在这里操作。")
    print(f"  Course preview:   {base_url}/c/{shifu_bid}?preview=true")
    print("    # 课程预览地址：仅课程作者本人可见，用于发布前后自测课程效果。")
    if include_published:
        print(f"  Published URL:    {base_url}/c/{shifu_bid}")
        print("    # 课程的公开学习地址：可以发送给学员使用。仅在课程已发布后生效。")


# ── Login ──────────────────────────────────────────────────────────────────────
def _login_post(base_url, path, payload, error_prefix):
    """POST to a user-auth endpoint and return parsed JSON, exit on failure."""
    resp = requests.post(
        f"{base_url}{path}",
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=30,
    )
    if not resp.ok:
        print(f"{error_prefix} (HTTP {resp.status_code}): {resp.text[:200]}")
        sys.exit(1)
    data = resp.json()
    if data.get("code") != 0:
        print(f"{error_prefix}: {data}")
        sys.exit(1)
    return data


def cmd_login(args):
    """SMS login and save token (non-interactive two-step flow)."""
    base_url = DEFAULT_BASE_URL

    phone = args.phone
    if not phone:
        print("Error: --phone is required for login")
        sys.exit(1)

    sms_code = args.sms_code
    masked = phone[:3] + "****" + phone[-4:] if len(phone) >= 7 else phone

    if sms_code:
        # Step 2: Verify code and save token
        print("Verifying code...")
        data = _login_post(base_url, "/api/user/login_sms",
                           {"mobile": phone, "sms_code": sms_code, "login_context": "admin"}, "Verification failed")

        token = data.get("data")
        if not token:
            print(f"No token in response: {data}")
            sys.exit(1)
        # API may return token as a dict (e.g. {"token": "..."}) or a plain string
        if isinstance(token, dict):
            token = token.get("token", "")
        if not token:
            print(f"No token string found in response data: {data}")
            sys.exit(1)

        save_env(token)
        print(f"Login successful! Token saved to {ENV_FILE}")
    else:
        # Step 1: Send SMS code only, then exit
        print(f"Sending SMS code to {masked}...")
        _login_post(base_url, "/api/user/console_send_sms_code",
                    {"mobile": phone}, "Failed to send SMS")
        print(f"SMS code sent to {masked}. "
              f"Run again with --sms-code <4-digit-code> to complete login.")


# ── List ───────────────────────────────────────────────────────────────────────
def _fetch_shifu_title(base_url, token, shifu_bid, *, table_key, session=None):
    """Fetch the current title from one of the shifu metadata tables.

    ``table_key`` selects which side of the published/draft pair to query:
    ``shifu_published_shifus`` for the live learner-facing title (Recipe
    0b) or ``shifu_draft_shifus`` for the editor copy (Recipe 0c).
    Returns the title string, or ``None`` when there is no current row
    (typically: course is unpublished, or never had a draft saved).

    ``session`` is passed through to :func:`api_analytics` to enable
    TCP/TLS connection reuse when the caller is doing one lookup per
    shifu_bid in a tight loop.
    """

    body = {
        "shifu_bid": shifu_bid,
        "table": table_key,
        "select": ["title"],
        "limit": 1,
    }
    ok, payload = api_analytics(base_url, token, body, session=session)
    if not ok or not isinstance(payload, dict) or payload.get("code") != 0:
        return None
    data = payload.get("data") or {}
    rows = data.get("rows") or []
    columns = data.get("columns") or []
    if not rows:
        return None
    try:
        title_idx = columns.index("title")
    except ValueError:
        return None
    return rows[0][title_idx]


def cmd_list(args):
    """List all courses with both draft and published titles.

    The /shifus endpoint returns the draft snapshot; we additionally run
    one analytics Recipe 0b call per shifu_bid to fetch the live published
    title. When the two diverge, the author has renamed the draft and has
    not yet republished — surface this so downstream agents do not mistake
    the draft title for the live learner-facing title.
    """
    base_url, token = resolve_auth(args)
    result = api(base_url, token, "get", "/shifus")

    if not result:
        print("No courses found.")
        return

    courses = result if isinstance(result, list) else result.get("items", [])
    if not courses:
        print("No courses found.")
        return

    rows = []
    diverged = 0
    # Reuse a single requests.Session for the per-course metadata lookups.
    # This avoids a fresh TCP / TLS handshake for every shifu_bid when the
    # author owns many courses; the handshake itself dominates latency on
    # a remote API, so connection pooling alone shaves the wall time
    # roughly in half without adding concurrency complexity.
    with requests.Session() as session:
        for c in courses:
            bid = c.get("bid", c.get("shifu_bid", ""))
            draft = c.get("name", c.get("title", ""))
            published = (
                _fetch_shifu_title(
                    base_url,
                    token,
                    bid,
                    table_key="shifu_published_shifus",
                    session=session,
                )
                if bid
                else None
            )
            if published is None:
                published_disp = "(draft only)"
            elif published == draft:
                published_disp = "(same)"
            else:
                published_disp = published
                diverged += 1
            rows.append({
                "bid": bid,
                "draft": draft,
                "published_disp": published_disp,
                "status": c.get("status", ""),
                "updated": fmt_time(c.get("updated_at", "")),
            })

    # Table output
    print(f"{'BID':<34} {'Draft Name':<26} {'Published Name':<26} {'Status':<10} {'Updated':<18}")
    print("-" * 116)
    for r in rows:
        print(
            f"{r['bid']:<34} {r['draft'][:24]:<26} {r['published_disp'][:24]:<26} "
            f"{r['status']:<10} {r['updated']:<18}"
        )

    print(f"\nTotal: {len(courses)} courses ({diverged} with draft/published title divergence)")


# ── Show ───────────────────────────────────────────────────────────────────────
def cmd_show(args):
    """Show course detail / outline tree / MarkdownFlow content."""
    base_url, token = resolve_auth(args)
    shifu_bid = args.shifu_bid
    outline_bid = args.outline_bid

    if outline_bid:
        # Show MarkdownFlow content for a specific lesson
        result = api(base_url, token, "get",
                     f"/shifus/{shifu_bid}/outlines/{outline_bid}/mdflow")
        content = result.get("data", "") if isinstance(result, dict) else result
        revision = result.get("revision", "") if isinstance(result, dict) else ""
        if revision:
            print(f"# Revision: {revision}\n")
        print(content)
    else:
        # Show course detail + outline tree
        detail = api_safe(base_url, token, "get", f"/shifus/{shifu_bid}/detail")
        if detail:
            print(f"Course: {detail.get('name', '')}")
            print(f"BID:    {shifu_bid}")
            desc = detail.get("description", "")
            if desc:
                print(f"Desc:   {desc}")
            model = detail.get("model", "")
            if model:
                print(f"Model:  {model}")
            print()

        tree = api(base_url, token, "get", f"/shifus/{shifu_bid}/outlines")
        if not tree:
            print("No outlines found.")
            return

        def print_tree(items, indent=0):
            for item in items:
                prefix = "  " * indent
                bid = item.get("bid", "")
                name = item.get("name", "")
                print(f"{prefix}- [{bid}] {name}")
                children = item.get("children", [])
                if children:
                    print_tree(children, indent + 1)

        print("Outline tree:")
        print_tree(tree if isinstance(tree, list) else [tree])

        _print_verification_urls(base_url, shifu_bid, include_published=True)


# ── History ────────────────────────────────────────────────────────────────────
def cmd_history(args):
    """Show MarkdownFlow revision history for a lesson."""
    base_url, token = resolve_auth(args)
    result = api(base_url, token, "get",
                 f"/shifus/{args.shifu_bid}/outlines/{args.outline_bid}/mdflow/history")

    if not result:
        print("No history found.")
        return

    items = result if isinstance(result, list) else result.get("items", [])
    for item in items:
        rev = item.get("revision", "")
        ts = fmt_time(item.get("created_at", ""))
        user = item.get("created_user_bid", "")
        print(f"  {rev}  {ts}  by {user}")


# ── Export ─────────────────────────────────────────────────────────────────────
def cmd_export(args):
    """Export a course to JSON via backend export API."""
    base_url, token = resolve_auth(args)
    shifu_bid = args.shifu_bid

    # Backend export API returns a file download (not standard JSON envelope)
    url = f"{base_url}/api/shifu/shifus/{shifu_bid}/export"
    headers = {"Cookie": f"token={token}"}
    resp = requests.get(url, headers=headers, timeout=60)

    if resp.status_code != 200:
        print(f"Export failed (HTTP {resp.status_code})")
        try:
            print(f"  Response: {resp.json()}")
        except Exception:
            print(f"  Response: {resp.text[:200]}")
        sys.exit(1)

    if args.output:
        outpath = args.output
        os.makedirs(os.path.dirname(outpath) or ".", exist_ok=True)
        with open(outpath, "wb") as f:
            f.write(resp.content)
        # Count lessons from exported data
        try:
            data = resp.json()
            count = len(data.get("outline_items", []))
            print(f"Exported to {outpath} ({count} lessons)")
        except Exception:
            print(f"Exported to {outpath}")
    else:
        # Pretty-print to stdout
        try:
            data = resp.json()
            print(json.dumps(data, ensure_ascii=False, indent=2))
        except Exception:
            print(resp.text)


# ── Create ─────────────────────────────────────────────────────────────────────
def cmd_create(args):
    """Create a new empty course."""
    base_url, token = resolve_auth(args)
    result = api(base_url, token, "put", "/shifus",
                 json={"name": args.name,
                       "description": args.description or ""})
    bid = result.get("bid") or result.get("shifu_bid")
    print(f"Created course: {bid}")
    print(f"  Name: {args.name}")
    _print_verification_urls(base_url, bid)


# ── Update Meta ────────────────────────────────────────────────────────────────
def cmd_update_meta(args):
    """Update course metadata (name, description, system prompt, etc.)."""
    base_url, token = resolve_auth(args)
    shifu_bid = args.shifu_bid

    # Fetch current detail to preserve unchanged fields
    current = api(base_url, token, "get", f"/shifus/{shifu_bid}/detail")

    course_prompt = current.get("system_prompt", "")
    if args.course_prompt_file:
        with open(args.course_prompt_file, "r", encoding="utf-8") as f:
            course_prompt = f.read().strip()

    keywords = current.get("keywords", "")
    if isinstance(keywords, list):
        pass  # already a list
    elif isinstance(keywords, str):
        keywords = [k.strip() for k in keywords.split(",") if k.strip()]

    payload = {
        "name": args.name if args.name is not None else current.get("name", ""),
        "description": args.description if args.description is not None
                       else current.get("description", ""),
        "avatar": current.get("avatar", ""),
        "keywords": keywords,
        "model": current.get("model", ""),
        "temperature": current.get("temperature", 0.3),
        "system_prompt": course_prompt,
        "tts_enabled": current.get("tts_enabled", False),
        "tts_provider": current.get("tts_provider", "minimax"),
        "tts_model": current.get("tts_model", ""),
        "tts_voice_id": current.get("tts_voice_id", ""),
        "tts_speed": current.get("tts_speed", 1.0),
        "tts_pitch": current.get("tts_pitch", 0),
        "tts_emotion": current.get("tts_emotion", ""),
        "use_learner_language": current.get("use_learner_language", False),
    }
    price = current.get("price")
    if price and price > 0:
        payload["price"] = price

    api(base_url, token, "post", f"/shifus/{shifu_bid}/detail", json=payload)
    print(f"Updated metadata for {shifu_bid}")


# ── Add Chapter ────────────────────────────────────────────────────────────────
def cmd_add_chapter(args):
    """Add a new top-level chapter to a course."""
    base_url, token = resolve_auth(args)
    shifu_bid = args.shifu_bid

    result = api(base_url, token, "put", f"/shifus/{shifu_bid}/outlines",
                 json={"name": args.name})
    outline_bid = result.get("bid") or result.get("outline_item_bid")
    if not outline_bid:
        print(f"Error: chapter created but response did not include a BID", file=sys.stderr)
        print(f"  Response: {json.dumps(result, ensure_ascii=False)}", file=sys.stderr)
        sys.exit(1)
    print(f"Created chapter: {outline_bid} ({args.name})")


# ── Add Lesson ─────────────────────────────────────────────────────────────────
def cmd_add_lesson(args):
    """Add a new lesson to a course."""
    base_url, token = resolve_auth(args)
    shifu_bid = args.shifu_bid

    # Create outline
    outline_payload = {"name": args.name}
    if args.parent_bid:
        outline_payload["parent_bid"] = args.parent_bid

    result = api(base_url, token, "put", f"/shifus/{shifu_bid}/outlines",
                 json=outline_payload)
    outline_bid = result.get("bid") or result.get("outline_item_bid")
    parent_label = f" under {args.parent_bid}" if args.parent_bid else ""
    print(f"Created lesson: {outline_bid} ({args.name}){parent_label}")

    # Write Teaching Prompt if provided
    if args.teaching_prompt_file:
        with open(args.teaching_prompt_file, "r", encoding="utf-8") as f:
            content = f.read()
        api(base_url, token, "post",
            f"/shifus/{shifu_bid}/outlines/{outline_bid}/mdflow",
            json={"data": content})
        print(f"  Teaching Prompt saved ({len(content)} chars)")


# ── Update Lesson ──────────────────────────────────────────────────────────────
def cmd_update_lesson(args):
    """Update MarkdownFlow content for an existing lesson (with optimistic locking)."""
    base_url, token = resolve_auth(args)
    shifu_bid = args.shifu_bid
    outline_bid = args.outline_bid

    # Step 1: Get current revision for optimistic locking
    current = api(base_url, token, "get",
                  f"/shifus/{shifu_bid}/outlines/{outline_bid}/mdflow")
    base_revision = None
    if isinstance(current, dict):
        base_revision = current.get("revision")

    # Step 2: Read new Teaching Prompt content
    with open(args.teaching_prompt_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Step 3: POST with base_revision
    payload = {"data": content}
    if base_revision:
        payload["base_revision"] = base_revision

    api(base_url, token, "post",
        f"/shifus/{shifu_bid}/outlines/{outline_bid}/mdflow",
        json=payload)
    print(f"Updated lesson {outline_bid} ({len(content)} chars)")
    if base_revision:
        print(f"  Base revision: {base_revision}")


# ── Rename Lesson ──────────────────────────────────────────────────────────────
def cmd_rename_lesson(args):
    """Rename an existing lesson."""
    base_url, token = resolve_auth(args)
    api(base_url, token, "post",
        f"/shifus/{args.shifu_bid}/outlines/{args.outline_bid}",
        json={"name": args.name})
    print(f"Renamed lesson {args.outline_bid} to: {args.name}")


# ── Delete Lesson ──────────────────────────────────────────────────────────────
def cmd_delete_lesson(args):
    """Delete a lesson from a course."""
    base_url, token = resolve_auth(args)
    api(base_url, token, "delete",
        f"/shifus/{args.shifu_bid}/outlines/{args.outline_bid}")
    print(f"Deleted lesson {args.outline_bid}")


# ── Reorder ────────────────────────────────────────────────────────────────────
def cmd_reorder(args):
    """Reorder lessons in a course."""
    base_url, token = resolve_auth(args)
    bids = [b.strip() for b in args.order.split(",") if b.strip()]
    api(base_url, token, "patch",
        f"/shifus/{args.shifu_bid}/outlines/reorder",
        json={"order": bids})
    print(f"Reordered {len(bids)} lessons")


# ── Import ─────────────────────────────────────────────────────────────────────
def _import_flat(base_url, token, json_file, shifu_bid):
    """Import from flat JSON file (original shifu-api-import.py logic)."""
    with open(json_file, "r", encoding="utf-8") as f:
        import_data = json.load(f)

    shifu_info = import_data["shifu"]
    outline_items = import_data["outline_items"]

    # Create or reuse shifu
    if shifu_bid:
        print(f"Using existing shifu: {shifu_bid}")
    else:
        print(f"Creating new shifu: {shifu_info['title']}")
        result = api(base_url, token, "put", "/shifus",
                     json={"name": shifu_info["title"],
                           "description": shifu_info.get("description", "")})
        shifu_bid = result.get("bid") or result.get("shifu_bid")
        print(f"  Created shifu: {shifu_bid}")

    # Update shifu detail
    keywords = shifu_info.get("keywords", "")
    if isinstance(keywords, str):
        keywords = [k.strip() for k in keywords.split(",") if k.strip()]
    detail_payload = {
        "name": shifu_info["title"],
        "description": shifu_info.get("description", ""),
        "avatar": shifu_info.get("avatar_res_bid", ""),
        "keywords": keywords,
        "model": shifu_info.get("llm", ""),
        "temperature": shifu_info.get("llm_temperature", 0.3),
        "system_prompt": shifu_info.get("course_prompt", ""),
    }
    price = shifu_info.get("price")
    if price and price > 0:
        detail_payload["price"] = price
    detail_payload.update({
        "tts_enabled": False,
        "tts_provider": "minimax",
        "tts_model": "",
        "tts_voice_id": "",
        "tts_speed": 1.0,
        "tts_pitch": 0,
        "tts_emotion": "",
        "use_learner_language": False,
    })
    for attempt in range(1, 4):
        result = api_safe(base_url, token, "post", f"/shifus/{shifu_bid}/detail",
                          json=detail_payload)
        if result is not None:
            print("  Updated shifu detail")
            break
        if attempt < 3:
            print(f"  Warning: failed to update shifu detail (attempt {attempt}/3), retrying...")
            time.sleep(1)
        else:
            print("Error: failed to update shifu detail after 3 attempts")
            sys.exit(1)

    # Clean existing outlines (delete children first, then parents)
    tree = api_safe(base_url, token, "get", f"/shifus/{shifu_bid}/outlines")
    if tree and isinstance(tree, list):
        for item in tree:
            for child in item.get("children", []):
                if child.get("bid"):
                    result = api_safe(base_url, token, "delete",
                                      f"/shifus/{shifu_bid}/outlines/{child['bid']}")
                    if result is None:
                        print(f"Error: failed to delete child outline: {child['bid']}")
                        sys.exit(1)
            if item.get("bid"):
                result = api_safe(base_url, token, "delete",
                                  f"/shifus/{shifu_bid}/outlines/{item['bid']}")
                if result is None:
                    print(f"Error: failed to delete outline: {item.get('name', item['bid'])}")
                    sys.exit(1)
                print(f"  Deleted old outline: {item.get('name', item['bid'])}")

    # Separate parents (chapters) and children (lessons) for two-pass creation
    parents = []
    children = []
    for item in outline_items:
        if item.get("parent_bid"):
            children.append(item)
        else:
            parents.append(item)

    bid_map = {}  # old outline_item_bid -> new API bid
    created = []
    total = len(outline_items)
    count = 0

    # Segmentation: Create parent items (chapters)
    for item in parents:
        count += 1
        title = item["title"]
        content = item.get("content", "")
        old_bid = item.get("outline_item_bid", "")

        result = api(base_url, token, "put", f"/shifus/{shifu_bid}/outlines",
                     json={"name": title})
        new_bid = result.get("bid") or result.get("outline_item_bid")
        bid_map[old_bid] = new_bid
        print(f"  [{count}/{total}] Created: {title} ({new_bid})")

        if content:
            api(base_url, token, "post",
                f"/shifus/{shifu_bid}/outlines/{new_bid}/mdflow",
                json={"data": content})
            print(f"    MarkdownFlow saved ({len(content)} chars)")

        created.append({"bid": new_bid, "title": title})
        time.sleep(0.3)

    # Orchestration: Create child items (lessons) with mapped parent_bid
    for item in children:
        count += 1
        title = item["title"]
        content = item.get("content", "")
        old_parent = item["parent_bid"]
        new_parent = bid_map.get(old_parent, old_parent)

        result = api(base_url, token, "put", f"/shifus/{shifu_bid}/outlines",
                     json={"name": title, "parent_bid": new_parent})
        new_bid = result.get("bid") or result.get("outline_item_bid")
        print(f"  [{count}/{total}] Created: {title} ({new_bid})")

        if content:
            api(base_url, token, "post",
                f"/shifus/{shifu_bid}/outlines/{new_bid}/mdflow",
                json={"data": content})
            print(f"    MarkdownFlow saved ({len(content)} chars)")

        created.append({"bid": new_bid, "title": title})
        time.sleep(0.3)

    print(f"\nDone! Shifu: {shifu_bid}")
    print(f"  Course: {shifu_info['title']}")
    print(f"  Chapters: {len(parents)}, Lessons: {len(children)}")
    _print_verification_urls(base_url, shifu_bid)
    return shifu_bid


def cmd_import(args):
    """Import a course from JSON file or course directory."""
    if args.new and args.shifu_bid:
        print("Error: omit <shifu_bid> when using --new")
        sys.exit(1)
    if not args.new and not args.shifu_bid:
        print("Error: provide <shifu_bid> or use --new")
        sys.exit(1)

    base_url, token = resolve_auth(args)
    shifu_bid = None if args.new else args.shifu_bid

    if args.course_dir:
        # Build JSON first, then import
        json_file = _build_import_json(
            course_dir=args.course_dir,
            title=getattr(args, "title", None),
            description=getattr(args, "description", None),
            keywords=getattr(args, "keywords", None),
            chapter_name=getattr(args, "chapter_name", None),
        )
        _import_flat(base_url, token, json_file, shifu_bid)
    elif args.json_file:
        _import_flat(base_url, token, args.json_file, shifu_bid)
    else:
        print("Error: provide --json-file or --course-dir")
        sys.exit(1)


# ── Build ──────────────────────────────────────────────────────────────────────
def _extract_lesson_title(content, filename):
    """Extract lesson_title from HTML comment block, fallback to filename."""
    match = re.search(r'lesson_title:\s*(.+)', content)
    if match:
        return match.group(1).strip()
    name = Path(filename).stem
    return name.replace("-", " ").title()


def _build_import_json(course_dir, title=None, description=None,
                       keywords=None, chapter_name=None, output_path=None):
    """Build import JSON from a local course directory. Returns the output file path."""
    lessons_dir = os.path.join(course_dir, "lessons")
    if not os.path.isdir(lessons_dir):
        print(f"Error: lessons directory not found: {lessons_dir}")
        sys.exit(1)

    # Read course-level prompt if exists
    course_prompt = ""
    prompt_path = os.path.join(course_dir, "course-prompt.md")
    if os.path.exists(prompt_path):
        with open(prompt_path, "r", encoding="utf-8") as f:
            course_prompt = f.read().strip()
        print(f"Loaded course prompt ({len(course_prompt)} chars)")

    # Scan lesson files
    lesson_files = sorted([
        f for f in os.listdir(lessons_dir)
        if f.startswith("lesson-") and f.endswith(".md")
    ])
    if not lesson_files:
        print(f"Error: no lesson-*.md files found in {lessons_dir}")
        sys.exit(1)

    shifu_bid = str(uuid.uuid4()).replace("-", "")

    # Determine title: explicit arg > README > directory name
    if not title:
        readme_path = os.path.join(course_dir, "README.md")
        if os.path.exists(readme_path):
            with open(readme_path, "r", encoding="utf-8") as f:
                first_line = f.readline().strip()
            if first_line.startswith("#"):
                title = first_line.lstrip("#").strip()
        if not title:
            title = Path(course_dir).name

    # Load chapter structure from structure.json if exists,
    # otherwise auto-create a single chapter wrapping all lessons
    structure_file = os.path.join(course_dir, "structure.json")
    if os.path.exists(structure_file):
        with open(structure_file, "r", encoding="utf-8") as f:
            chapter_defs = json.load(f).get("chapters", [])
    else:
        chapter_defs = None

    outline_items = []
    structure_chapters = []

    if chapter_defs:
        # Multi-chapter mode: use structure.json definitions
        for ch_idx, ch_def in enumerate(chapter_defs):
            ch_bid = str(uuid.uuid4()).replace("-", "")
            ch_title = ch_def["title"]

            # Chapter item (container, no MarkdownFlow content)
            outline_items.append({
                "outline_item_bid": ch_bid,
                "title": ch_title,
                "type": 401,
                "hidden": 0,
                "parent_bid": "",
                "position": str(ch_idx),
                "prerequisite_item_bids": "",
                "llm": "",
                "llm_temperature": 0,
                "course_prompt": "",
                "ask_enabled_status": 5101,
                "ask_llm": "",
                "ask_llm_temperature": 0.0,
                "ask_llm_system_prompt": "",
                "content": "",
            })

            lesson_children = []
            for ls_idx, ls_def in enumerate(ch_def.get("lessons", [])):
                ls_file = ls_def["file"]
                filepath = safe_join_path(lessons_dir, ls_file)
                if filepath is None:
                    continue
                if not os.path.exists(filepath):
                    print(f"Warning: file not found: {filepath}, skipping")
                    continue
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()

                item_bid = str(uuid.uuid4()).replace("-", "")
                ls_title = ls_def.get("title") or _extract_lesson_title(content, ls_file)

                outline_items.append({
                    "outline_item_bid": item_bid,
                    "title": ls_title,
                    "type": 401,
                    "hidden": 0,
                    "parent_bid": ch_bid,
                    "position": str(ls_idx),
                    "prerequisite_item_bids": "",
                    "llm": "",
                    "llm_temperature": 0,
                    "course_prompt": course_prompt,
                    "ask_enabled_status": 5101,
                    "ask_llm": "",
                    "ask_llm_temperature": 0.0,
                    "ask_llm_system_prompt": "",
                    "content": content,
                })

                lesson_children.append({
                    "bid": item_bid, "id": 0, "type": "outline",
                    "children": [], "child_count": 0,
                })

            structure_chapters.append({
                "bid": ch_bid, "id": 0, "type": "outline",
                "children": lesson_children,
                "child_count": len(lesson_children),
            })
    else:
        # Single-chapter mode: wrap all lessons under one chapter
        chapter_bid = str(uuid.uuid4()).replace("-", "")
        chapter_title = chapter_name or title

        # Chapter item (container, no MarkdownFlow content)
        outline_items.append({
            "outline_item_bid": chapter_bid,
            "title": chapter_title,
            "type": 401,
            "hidden": 0,
            "parent_bid": "",
            "position": "0",
            "prerequisite_item_bids": "",
            "llm": "",
            "llm_temperature": 0,
            "course_prompt": "",
            "ask_enabled_status": 5101,
            "ask_llm": "",
            "ask_llm_temperature": 0.0,
            "ask_llm_system_prompt": "",
            "content": "",
        })

        lesson_children = []
        for idx, filename in enumerate(lesson_files):
            filepath = safe_join_path(lessons_dir, filename)
            if filepath is None:
                continue
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            item_bid = str(uuid.uuid4()).replace("-", "")
            lesson_title = _extract_lesson_title(content, filename)

            outline_items.append({
                "outline_item_bid": item_bid,
                "title": lesson_title,
                "type": 401,
                "hidden": 0,
                "parent_bid": chapter_bid,
                "position": str(idx),
                "prerequisite_item_bids": "",
                "llm": "",
                "llm_temperature": 0,
                "course_prompt": course_prompt,
                "ask_enabled_status": 5101,
                "ask_llm": "",
                "ask_llm_temperature": 0.0,
                "ask_llm_system_prompt": "",
                "content": content,
            })

            lesson_children.append({
                "bid": item_bid, "id": 0, "type": "outline",
                "children": [], "child_count": 0,
            })

        structure_chapters.append({
            "bid": chapter_bid, "id": 0, "type": "outline",
            "children": lesson_children,
            "child_count": len(lesson_children),
        })

    import_data = {
        "version": "1.0",
        "exported_at": datetime.now().isoformat(),
        "shifu": {
            "shifu_bid": shifu_bid,
            "title": title,
            "keywords": keywords or "",
            "description": description or "",
            "avatar_res_bid": "",
            "llm": "",
            "llm_temperature": 0,
            "course_prompt": course_prompt,
            "ask_enabled_status": 5101,
            "ask_llm": "",
            "ask_llm_temperature": 0.0,
            "ask_llm_system_prompt": "",
        },
        "outline_items": outline_items,
        "structure": {
            "bid": shifu_bid,
            "id": 0,
            "type": "shifu",
            "children": structure_chapters,
            "child_count": len(structure_chapters),
        },
    }

    # Output
    if not output_path:
        output_path = os.path.join(course_dir, "shifu-import.json")

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(import_data, f, ensure_ascii=False, indent=2)

    chapters = [i for i in outline_items if not i.get("parent_bid")]
    lessons = [i for i in outline_items if i.get("parent_bid")]
    print(f"Generated {output_path}")
    print(f"  Course: {title}")
    print(f"  Chapters: {len(chapters)}, Lessons: {len(lessons)}")
    print(f"  Shifu BID: {shifu_bid}")
    return output_path


def cmd_build(args):
    """Build import JSON from local course directory (no network needed)."""
    _build_import_json(
        course_dir=args.course_dir,
        title=args.title,
        description=args.description,
        keywords=args.keywords,
        chapter_name=args.chapter_name,
        output_path=args.output,
    )


# ── Publish / Archive / Unarchive ──────────────────────────────────────────────
def cmd_publish(args):
    """Publish a course."""
    base_url, token = resolve_auth(args)
    api(base_url, token, "post", f"/shifus/{args.shifu_bid}/publish", json={})
    print(f"Published: {args.shifu_bid}")
    _print_verification_urls(base_url, args.shifu_bid, include_published=True)


def cmd_archive(args):
    """Archive a course."""
    base_url, token = resolve_auth(args)
    api(base_url, token, "post", f"/shifus/{args.shifu_bid}/archive", json={})
    print(f"Archived: {args.shifu_bid}")


def cmd_unarchive(args):
    """Unarchive a course."""
    base_url, token = resolve_auth(args)
    api(base_url, token, "post", f"/shifus/{args.shifu_bid}/unarchive", json={})
    print(f"Unarchived: {args.shifu_bid}")


def cmd_analytics_query(args):
    """Run a DSL query against the creator-analytics endpoint.

    Output is the full JSON response (success rows or business error code)
    printed to stdout. Exit code is 0 only when the API returns code == 0.
    """
    base_url, token = resolve_auth(args)

    if args.dsl_file:
        try:
            with open(args.dsl_file, "r", encoding="utf-8") as f:
                body = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            print(f"Error reading --dsl-file: {e}")
            sys.exit(1)
    else:
        try:
            body = json.loads(args.dsl)
        except json.JSONDecodeError as e:
            print(f"Error parsing --dsl JSON: {e}")
            sys.exit(1)

    if not isinstance(body, dict):
        print("Error: DSL body must be a JSON object")
        sys.exit(1)

    existing = body.get("shifu_bid")
    if existing and existing != args.shifu_bid:
        print(f"Error: shifu_bid in DSL body ({existing}) "
              f"does not match positional arg ({args.shifu_bid})")
        sys.exit(1)
    body["shifu_bid"] = args.shifu_bid

    transport_ok, payload = api_analytics(base_url, token, body)
    print(json.dumps(payload, ensure_ascii=False, indent=2))

    if not transport_ok or not isinstance(payload, dict) or payload.get("code") != 0:
        sys.exit(1)


def cmd_find_title(args):
    """Resolve a course-title keyword to the canonical current title(s).

    Three-step lookup per PDF §1 of the 2026-05-15 query handbook:
      1. List the caller's shifu_bids via /shifus.
      2. For each shifu_bid, fetch the current published title (Recipe 0b)
         and the current draft title (Recipe 0c).
      3. Match the keyword against both titles (case-insensitive, whitespace-
         normalized) and report grouped results: Published, Draft-only,
         No match.

    Historical / renamed titles never appear in this output by construction
    — Recipe 0b/0c only return the `deleted = 0` row.
    """

    base_url, token = resolve_auth(args)
    keyword = args.keyword or ""
    needle = keyword.replace(" ", "").lower()
    # Mirror the backend metadata-table `title like` floor (>= 2 non-wildcard
    # characters, see references/analytics/dsl.md). A 1-character keyword
    # would substring-match almost every title client-side and rarely help
    # the user; reject early with a clear message rather than fan out a
    # cascade of low-signal API calls.
    if len(needle) < 2:
        print(
            "Error: keyword must contain at least 2 non-whitespace characters "
            "(case-insensitive prefix / substring matching)"
        )
        sys.exit(1)

    result = api(base_url, token, "get", "/shifus")
    courses = result if isinstance(result, list) else (result or {}).get("items", [])
    if not courses:
        print("No courses found for this account.")
        return

    published_matches = []  # (shifu_bid, published_title)
    # draft_matches holds courses whose draft title matches the keyword
    # but whose published title (if any) does not. Each row carries the
    # current published title alongside so the user can see the rename
    # state at a glance ("currently published as: X" vs "draft only").
    draft_matches = []  # (shifu_bid, draft_title, published_title_or_None)

    def _matches(title):
        if not title:
            return False
        return needle in title.replace(" ", "").lower()

    with requests.Session() as session:
        for c in courses:
            bid = c.get("bid", c.get("shifu_bid", ""))
            if not bid:
                continue
            published = _fetch_shifu_title(
                base_url,
                token,
                bid,
                table_key="shifu_published_shifus",
                session=session,
            )
            if published is not None and _matches(published):
                published_matches.append((bid, published))
                continue
            # Either no published row, or the published title does not match.
            # Always check the draft — a course whose draft has been renamed
            # but not yet republished is exactly the case `find-title` exists
            # to surface. (Previous logic checked draft only when published
            # was None, which silently dropped renamed-but-still-published
            # courses; flagged in PR #48 AI review.)
            draft = _fetch_shifu_title(
                base_url,
                token,
                bid,
                table_key="shifu_draft_shifus",
                session=session,
            )
            if draft is not None and _matches(draft):
                draft_matches.append((bid, draft, published))

    if published_matches:
        print(f"Published (current live title matches '{keyword}'):")
        for bid, title in published_matches:
            print(f"  {bid}  {title}")
    if draft_matches:
        print(f"\nDraft (matches '{keyword}'; not yet republished):")
        for bid, draft, published in draft_matches:
            if published is None:
                print(f"  {bid}  {draft}  (draft only — not yet published)")
            else:
                print(
                    f'  {bid}  {draft}  (currently published as: "{published}")'
                )
    if not published_matches and not draft_matches:
        print(f"No courses you own currently have a title matching '{keyword}'.")
        print("If the user is sure of the name, they may be remembering a "
              "historical title — check `shifu-cli.py list` for current titles.")


# ── Credit Detail ──────────────────────────────────────────────────────────────
def _parse_int_list_arg(raw, flag_name):
    """Parse a comma-separated integer list argument.

    Shared by ``--scene`` and ``--usage-type`` (flagged on PR #50 review
    as duplicated logic). Reports both the parse-failure and the empty-
    result cases on stderr and exits 1, so the CLI never sends an empty
    list to the backend (which would reject it as ``11002 invalidDsl``)
    and never silently drops a malformed value.
    """

    try:
        parsed = [int(item) for item in raw.split(",") if item.strip()]
    except ValueError:
        print(
            f"Error: {flag_name} must be a comma-separated list of integers",
            file=sys.stderr,
        )
        sys.exit(1)
    if not parsed:
        print(
            f"Error: {flag_name} must contain at least one integer",
            file=sys.stderr,
        )
        sys.exit(1)
    return parsed


def cmd_credit_detail(args):
    """Fetch server-side joined credit consumption detail for one shifu.

    Calls POST /api/creator-analytics/credit-detail, which joins
    bill_usage x credit_ledger_entries on (source_bid = usage_bid AND
    source_type = USAGE). Returns a per-row payload alongside a summary
    block (total records, total credits, distinct users, distinct progress
    records, wallet creator bid, time range).

    Use this whenever the user asks about credit consumption — the DSL
    bill_daily_usage_metrics table is empty in production until the daily
    aggregation cron is enabled.
    """

    base_url, token = resolve_auth(args)
    body = {"shifu_bid": args.shifu_bid}

    # Date range — parse and validate locally so a malformed --start /
    # --end does not round-trip to the backend as 11002 invalidDsl
    # (PR #50 review). Same stderr + exit-1 style as the --scene /
    # --usage-type guards below.
    start_d = None
    end_d = None
    if args.start:
        try:
            start_d = datetime.fromisoformat(args.start).date()
        except ValueError:
            print(
                "Error: --start must be an ISO date (YYYY-MM-DD)",
                file=sys.stderr,
            )
            sys.exit(1)
        body["start_date"] = args.start
    if args.end:
        try:
            end_d = datetime.fromisoformat(args.end).date()
        except ValueError:
            print(
                "Error: --end must be an ISO date (YYYY-MM-DD)",
                file=sys.stderr,
            )
            sys.exit(1)
        body["end_date"] = args.end
    if start_d and end_d and end_d < start_d:
        print("Error: --end must be on or after --start", file=sys.stderr)
        sys.exit(1)

    if args.scene:
        body["usage_scene"] = _parse_int_list_arg(args.scene, "--scene")
    if args.usage_type:
        body["usage_type"] = _parse_int_list_arg(args.usage_type, "--usage-type")

    # --limit / --offset bounds match the backend's
    # ANALYTICS_QUERY_LIMIT_MAX (1000) and offset >= 0 contract; check
    # locally so an obvious typo reports a clean error instead of an
    # 11007 invalidLimit round-trip (PR #50 review).
    if args.limit is not None:
        if args.limit < 1 or args.limit > 1000:
            print("Error: --limit must be in [1, 1000]", file=sys.stderr)
            sys.exit(1)
        body["limit"] = args.limit
    if args.offset is not None:
        if args.offset < 0:
            print("Error: --offset must be >= 0", file=sys.stderr)
            sys.exit(1)
        body["offset"] = args.offset

    ok, payload = api_credit_detail(base_url, token, body)
    print(json.dumps(payload, ensure_ascii=False, indent=2))

    if not ok or not isinstance(payload, dict) or payload.get("code") != 0:
        sys.exit(1)


# ── Upload Image ───────────────────────────────────────────────────────────────
def _load_manifest(manifest_path):
    if not manifest_path.exists():
        return {"images": []}
    try:
        with manifest_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return {"images": []}
    if not isinstance(data, dict) or not isinstance(data.get("images"), list):
        return {"images": []}
    return data


def _write_manifest(manifest_path, manifest):
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = manifest_path.with_suffix(manifest_path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
        f.write("\n")
    tmp.replace(manifest_path)


def _update_manifest(course_dir, entry):
    """Upsert an image entry by 'local' (file path) or 'source_url' (URL upload)."""
    manifest_path = Path(course_dir) / "assets" / "image-manifest.json"
    manifest = _load_manifest(manifest_path)

    key_field = "local" if entry.get("local") else "source_url"
    key_value = entry[key_field]
    existing_idx = None
    for i, item in enumerate(manifest["images"]):
        if item.get(key_field) == key_value:
            existing_idx = i
            break
    if existing_idx is None:
        manifest["images"].append(entry)
    else:
        manifest["images"][existing_idx] = entry

    _write_manifest(manifest_path, manifest)
    print(f"info: manifest updated at {manifest_path}", file=sys.stderr)


def cmd_upload_image(args):
    """Upload a local image (with preprocessing) or a remote URL to ai-shifu OSS.

    Outputs ONLY the resulting URL to stdout — designed to be captured into the
    Teaching Prompt by an LLM or a shell pipeline. Diagnostic messages (manifest
    writes, etc.) go to stderr.
    """
    base_url, token = resolve_auth(args)

    # --file and --url are enforced as a required mutually exclusive group by
    # the argparse subparser, so we don't need to revalidate that here.
    course_dir = Path(args.course_dir).resolve() if args.course_dir else None
    alt = args.alt or ""

    if args.file:
        src_path = Path(args.file).resolve()
        if args.no_process:
            if not src_path.is_file():
                print(f"Error: file not found: {src_path}", file=sys.stderr)
                sys.exit(1)
            file_bytes = src_path.read_bytes()
            ext = src_path.suffix.lower() or ".jpg"
            mime_guess = {
                ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                ".png": "image/png", ".gif": "image/gif", ".webp": "image/webp",
            }.get(ext, "application/octet-stream")
            filename = src_path.name
            mime = mime_guess
            original_bytes = len(file_bytes)
        else:
            from image_utils import prepare_image  # local import keeps Pillow optional
            try:
                prepared = prepare_image(src_path)
            except ValueError as e:
                print(f"Error: {e}", file=sys.stderr)
                sys.exit(1)
            file_bytes = prepared.data
            filename = prepared.filename
            mime = prepared.mime
            original_bytes = prepared.original_bytes

        remote_url = api_upload(base_url, token, filename, file_bytes, mime)
        print(remote_url)

        if course_dir is not None:
            try:
                local_rel = str(src_path.relative_to(course_dir))
            except ValueError:
                local_rel = src_path.name
                print(
                    f"warning: {src_path} is outside --course-dir; "
                    f"recording only the filename ({local_rel}) in manifest "
                    "(cross-machine dedup may be imperfect)",
                    file=sys.stderr,
                )
            _update_manifest(course_dir, {
                "local": local_rel,
                "remote": remote_url,
                "alt": alt,
                "uploaded_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "bytes": len(file_bytes),
                "original_bytes": original_bytes,
                "mime": mime,
                "filename": filename,
            })
        return

    # URL upload path — backend downloads, validates Content-Type, re-hosts.
    remote_url = api(base_url, token, "post", "/url-upfile", json={"url": args.url})
    print(remote_url)

    if course_dir is not None:
        _update_manifest(course_dir, {
            "source_url": args.url,
            "remote": remote_url,
            "alt": alt,
            "uploaded_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        })


# ── CLI Entry Point ────────────────────────────────────────────────────────────
def build_parser():
    """Build and return the argument parser with all subcommands."""
    # Shared parent parser for --token on every subcommand
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument("--token", default=None,
                               help="JWT token (or SHIFU_TOKEN in .env)")

    parser = argparse.ArgumentParser(
        prog="shifu-cli",
        description="AI-Shifu Course CLI - Unified tool for course CRUD operations",
    )

    sub = parser.add_subparsers(dest="command", help="Available commands")

    # ── login ──
    p = sub.add_parser("login", parents=[parent_parser],
                       help="SMS login and save token")
    p.add_argument("--phone", required=True, help="Phone number for SMS login")
    p.add_argument("--sms-code", default=None,
                   help="4-digit SMS verification code")

    # ── list ──
    sub.add_parser("list", parents=[parent_parser], help="List all courses")

    # ── show ──
    p = sub.add_parser("show", parents=[parent_parser],
                       help="Show course detail or a lesson's Teaching Prompt")
    p.add_argument("shifu_bid", help="Course BID")
    p.add_argument("outline_bid", nargs="?", default=None,
                   help="Outline BID (omit to show tree)")

    # ── history ──
    p = sub.add_parser("history", parents=[parent_parser],
                       help="Show Teaching Prompt revision history")
    p.add_argument("shifu_bid", help="Course BID")
    p.add_argument("outline_bid", help="Outline BID")

    # ── export ──
    p = sub.add_parser("export", parents=[parent_parser],
                       help="Export course to JSON")
    p.add_argument("shifu_bid", help="Course BID")
    p.add_argument("-o", "--output", default=None, help="Output file (stdout if omitted)")

    # ── create ──
    p = sub.add_parser("create", parents=[parent_parser],
                       help="Create a new empty course")
    p.add_argument("--name", required=True, help="Course name")
    p.add_argument("--description", default=None, help="Course description")

    # ── update-meta ──
    p = sub.add_parser("update-meta", parents=[parent_parser],
                       help="Update course metadata")
    p.add_argument("shifu_bid", help="Course BID")
    p.add_argument("--name", default=None, help="New course name")
    p.add_argument("--description", default=None, help="New description")
    p.add_argument("--course-prompt-file", default=None,
                   help="File containing course-level prompt")

    # ── add-chapter ──
    p = sub.add_parser("add-chapter", parents=[parent_parser],
                       help="Add a new top-level chapter")
    p.add_argument("shifu_bid", help="Course BID")
    p.add_argument("--name", required=True, help="Chapter name")

    # ── add-lesson ──
    p = sub.add_parser("add-lesson", parents=[parent_parser],
                       help="Add a new lesson under a chapter")
    p.add_argument("shifu_bid", help="Course BID")
    p.add_argument("--name", required=True, help="Lesson name")
    p.add_argument("--teaching-prompt-file", default=None,
                   help="Teaching Prompt file (MarkdownFlow format)")
    p.add_argument("--parent-bid", required=True,
                   help="Parent chapter BID (use add-chapter to create one first)")

    # ── update-lesson ──
    p = sub.add_parser("update-lesson", parents=[parent_parser],
                       help="Update a lesson's Teaching Prompt")
    p.add_argument("shifu_bid", help="Course BID")
    p.add_argument("outline_bid", help="Outline BID")
    p.add_argument("--teaching-prompt-file", required=True,
                   help="Teaching Prompt file (MarkdownFlow format)")

    # ── rename-lesson ──
    p = sub.add_parser("rename-lesson", parents=[parent_parser],
                       help="Rename a lesson")
    p.add_argument("shifu_bid", help="Course BID")
    p.add_argument("outline_bid", help="Outline BID")
    p.add_argument("--name", required=True, help="New lesson name")

    # ── delete-lesson ──
    p = sub.add_parser("delete-lesson", parents=[parent_parser],
                       help="Delete a lesson")
    p.add_argument("shifu_bid", help="Course BID")
    p.add_argument("outline_bid", help="Outline BID")

    # ── reorder ──
    p = sub.add_parser("reorder", parents=[parent_parser],
                       help="Reorder lessons")
    p.add_argument("shifu_bid", help="Course BID")
    p.add_argument("--order", required=True,
                   help="Comma-separated list of outline BIDs in desired order")

    # ── import ──
    p = sub.add_parser("import", parents=[parent_parser],
                       help="Import a course from JSON file or course directory")
    p.add_argument("shifu_bid", nargs="?", default=None,
                   help="Existing course BID (omit with --new to create)")
    p.add_argument("--new", action="store_true",
                   help="Create a new course instead of updating")
    p.add_argument("--json-file", default=None, help="Flat import JSON file")
    p.add_argument("--course-dir", default=None,
                   help="Course directory (builds JSON then imports)")
    p.add_argument("--title", default=None,
                   help="Course title (only with --course-dir)")
    p.add_argument("--description", default=None,
                   help="Course description (only with --course-dir)")
    p.add_argument("--keywords", default=None,
                   help="Keywords, comma-separated (only with --course-dir)")
    p.add_argument("--chapter-name", default=None,
                   help="Chapter name (only with --course-dir)")

    # ── build ──
    p = sub.add_parser("build", help="Build import JSON from local course directory")
    p.add_argument("--course-dir", required=True, help="Course directory path")
    p.add_argument("-o", "--output", default=None,
                   help="Output file (default: <course-dir>/shifu-import.json)")
    p.add_argument("--title", default=None, help="Course title")
    p.add_argument("--chapter-name", default=None,
                   help="Chapter name (default: same as course title)")
    p.add_argument("--description", default=None, help="Course description")
    p.add_argument("--keywords", default=None, help="Keywords (comma-separated)")

    # ── publish ──
    p = sub.add_parser("publish", parents=[parent_parser],
                       help="Publish a course")
    p.add_argument("shifu_bid", help="Course BID")

    # ── archive ──
    p = sub.add_parser("archive", parents=[parent_parser],
                       help="Archive a course")
    p.add_argument("shifu_bid", help="Course BID")

    # ── unarchive ──
    p = sub.add_parser("unarchive", parents=[parent_parser],
                       help="Unarchive a course")
    p.add_argument("shifu_bid", help="Course BID")

    # ── analytics-query ──
    p = sub.add_parser("analytics-query", parents=[parent_parser],
                       help="Run a DSL query against the creator-analytics endpoint")
    p.add_argument("shifu_bid", help="Course BID")
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--dsl", help="DSL body as an inline JSON string")
    src.add_argument("--dsl-file", help="Path to a JSON file containing the DSL body")

    # ── find-title ──
    p = sub.add_parser("find-title", parents=[parent_parser],
                       help="Find courses by current title (published + draft)")
    p.add_argument("keyword",
                   help="Title keyword to search for (case-insensitive, "
                        "whitespace-normalized; matches current published and "
                        "draft titles only — never historical / renamed titles)")

    # ── upload-image ──
    p = sub.add_parser("upload-image", parents=[parent_parser],
                       help="Upload a local image (auto-preprocessed) or a remote URL to OSS")
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--file", help="Local image path (any common format incl. heic)")
    src.add_argument("--url", help="Remote http(s) image URL; backend re-hosts it")
    p.add_argument("--course-dir", default=None,
                   help="Course directory to record upload in assets/image-manifest.json")
    p.add_argument("--alt", default=None,
                   help="Short description of what the image conveys (stored in manifest)")
    p.add_argument("--no-process", action="store_true",
                   help="Skip local preprocessing and upload bytes as-is (debug only)")

    # ── credit-detail ──
    p = sub.add_parser("credit-detail", parents=[parent_parser],
                       help="Fetch joined credit consumption detail for one shifu")
    p.add_argument("shifu_bid", help="Course BID")
    p.add_argument("--start", help="Inclusive ISO date lower bound, e.g. 2026-05-15")
    p.add_argument("--end", help="Inclusive ISO date upper bound, e.g. 2026-05-16")
    p.add_argument("--scene",
                   help="Comma-separated usage_scene codes, e.g. 1202,1203 "
                        "(1201 debug / 1202 preview / 1203 production)")
    p.add_argument("--usage-type", dest="usage_type",
                   help="Comma-separated usage_type codes, e.g. 1101,1102 "
                        "(1101 LLM / 1102 TTS)")
    p.add_argument("--limit", type=int, default=None,
                   help="Row count cap, 1..1000 (default 100 server-side)")
    p.add_argument("--offset", type=int, default=None,
                   help="Pagination offset (default 0)")

    return parser


def main():
    load_env()

    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    commands = {
        "login": cmd_login,
        "list": cmd_list,
        "show": cmd_show,
        "history": cmd_history,
        "export": cmd_export,
        "create": cmd_create,
        "update-meta": cmd_update_meta,
        "add-chapter": cmd_add_chapter,
        "add-lesson": cmd_add_lesson,
        "update-lesson": cmd_update_lesson,
        "rename-lesson": cmd_rename_lesson,
        "delete-lesson": cmd_delete_lesson,
        "reorder": cmd_reorder,
        "import": cmd_import,
        "build": cmd_build,
        "publish": cmd_publish,
        "archive": cmd_archive,
        "unarchive": cmd_unarchive,
        "analytics-query": cmd_analytics_query,
        "find-title": cmd_find_title,
        "credit-detail": cmd_credit_detail,
        "upload-image": cmd_upload_image,
    }

    handler = commands.get(args.command)
    if handler:
        handler(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
