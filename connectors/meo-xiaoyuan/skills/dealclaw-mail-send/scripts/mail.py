#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""dealclaw-mail-send · 跨平台邮件发送 CLI（纯标准库，零第三方依赖）

一个自包含的发信工具：调 Resend HTTP API 把邮件发出去，并跟踪投递终态。
可在 Windows / macOS / Linux 上以完全相同的方式运行（Python 3.8+）。

设计约束（为跨平台与可分发而设）
--------------------------------
1. **纯标准库**：只用 argparse / json / urllib / base64 / pathlib / time。
   没有 fcntl、没有 msvcrt、没有 requests、没有 yaml。
2. **无平台绑定**：不出现任何硬编码盘符或用户名；配置目录由 ``Path.home()`` 派生。
3. **无外部技能依赖**：不发信前不依赖任何别的技能包、不读 SQLite 事实层。
4. **编码安全**：所有文件读写显式 ``encoding="utf-8"``；stdout 强制 UTF-8，
   避免 Windows 默认 cp936 下中文/emoji 正文写文件时炸掉。
5. **配置三级回退**：命令行参数 > 环境变量 > 配置文件。

两个必须知道的事实（实测得出，不是猜测）
----------------------------------------
1. **必须带浏览器风格 User-Agent**。urllib 默认的 ``Python-urllib/3.x`` 会被
   Cloudflare 以 error code 1010 拒掉（HTTP 403），请求根本到不了 Resend，
   现象很像「key 无效」或「域名没验证」，实际是被边缘节点拦了。
2. ``Authorization: Bearer <key>`` 与裸 key 都能通过，两种写法等价。

安全
----
API key 是账号级发信凭据，拿到即可用本账号下任意已验证域名发信。
本工具**只从环境变量或配置文件读取**，绝不硬编码；``config`` 与 ``init --show``
输出时一律打码。请勿把配置文件提交进任何仓库。

用法
----
    python mail.py init --api-key re_xxx --from 'Name <you@yourdomain.com>'
    python mail.py doctor
    python mail.py domains
    python mail.py send --to someone@example.com --subject 'Hi' --text 'hello'
    python mail.py send --to someone@example.com --subject 'Hi' \
        --html-file card.html --text 'fallback' --wait
    python mail.py get --id <email_id>
"""
from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import platform
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

__version__ = "1.0.0"

# 目标最低版本：3.8（避免 3.9+ / 3.10+ 独有语法，便于广泛分发）
MIN_PY = (3, 8)
if sys.version_info < MIN_PY:
    sys.stderr.write(
        "需要 Python %d.%d 或更高版本，当前为 %d.%d\n"
        % (MIN_PY[0], MIN_PY[1], sys.version_info[0], sys.version_info[1])
    )
    raise SystemExit(2)

APP_NAME = "dealclaw-mail-send"

DEFAULT_API_BASE = "https://api.resend.com"
# DealClaw 平台配置下发接口（可选能力，见 key 子命令）
PLATFORM_API_BASE = "https://micro.tradechina.com/blade-agent-adapter"

# 浏览器 UA：缺了它会被 Cloudflare 1010 拦（见模块文档第 1 条）
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

# 投递终态：轮询到这些就停
TERMINAL_EVENTS = {"delivered", "bounced", "complained", "failed", "canceled"}

RETRY_STATUS = {408, 425, 429, 500, 502, 503, 504}


# --------------------------------------------------------------------------- #
# 基础设施
# --------------------------------------------------------------------------- #
def _force_utf8_io() -> None:
    """Windows 控制台默认 cp936/GBK，中文正文与 JSON 会乱码或抛异常。"""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def emit(value, as_json: bool = True) -> None:
    if as_json:
        print(json.dumps(value, ensure_ascii=False, indent=2))
    else:
        print(value)


def die(msg: str, code: int = 2) -> "None":
    emit({"ok": False, "error": msg})
    raise SystemExit(code)


def mask(secret: str) -> str:
    if not secret:
        return ""
    if len(secret) <= 12:
        return secret[:2] + "*" * max(0, len(secret) - 2)
    return "%s...%s(len=%d)" % (secret[:8], secret[-4:], len(secret))


def config_dir() -> Path:
    override = os.environ.get("MAIL_CONFIG_DIR", "").strip()
    if override:
        return Path(override).expanduser()
    # 三平台统一：~/.config/dealclaw-mail-send/
    # Windows 上 Path.home() 形如 C:\Users\<user>，不牵扯任何硬编码
    return Path.home() / ".config" / APP_NAME


def config_path() -> Path:
    return config_dir() / "config.json"


def load_config() -> "dict":
    p = config_path()
    if not p.exists():
        return {}
    try:
        with p.open(encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception as exc:
        die("配置文件无法解析：%s（%s）" % (p, exc))


def save_config(cfg: "dict") -> Path:
    d = config_dir()
    d.mkdir(parents=True, exist_ok=True)
    p = config_path()
    with p.open("w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    # POSIX 上收紧权限，避免同机其他用户读到 key
    try:
        os.chmod(str(p), 0o600)
    except Exception:
        pass
    return p


def resolve(args, key: str, env_names, cfg_names, default: str = "") -> "tuple":
    """三级回退：CLI > env > 配置文件。返回 (值, 来源)。"""
    cli = (getattr(args, key, "") or "").strip()
    if cli:
        return cli, "cli"
    for e in env_names:
        v = (os.environ.get(e, "") or "").strip()
        if v:
            return v, "env:%s" % e
    cfg = load_config()
    for c in cfg_names:
        v = str(cfg.get(c, "") or "").strip()
        if v:
            return v, "config"
    return default, ("default" if default else "")


def resolve_api_key(args) -> str:
    v, src = resolve(args, "api_key", ["MAIL_API_KEY", "RESEND_API_KEY"], ["api_key"])
    if not v:
        die(
            "缺少 API key。三种配置方式任选其一：\n"
            "  1) python mail.py init --api-key re_xxx --from 'Name <you@domain>'\n"
            "  2) export RESEND_API_KEY=re_xxx\n"
            "  3) python mail.py send --api-key re_xxx ...\n"
            "（若是 DealClaw 平台租户，可用 python mail.py key --supplier-id <id> --save 自动获取）"
        )
    args._key_source = src
    return v


# --------------------------------------------------------------------------- #
# HTTP
# --------------------------------------------------------------------------- #
def http_json(method: str, url: str, *, headers: "dict" = None,
              payload=None, timeout: int = 30, retries: int = 2,
              retry_status=None) -> "tuple":
    """发 HTTP 请求，返回 (status, body)。0 表示网络层失败。

    对 429/5xx 做指数退避重试；4xx 不重试（重试也没用）。
    """
    retry_status = retry_status or RETRY_STATUS
    data = None
    hdrs = {"Accept": "application/json", "User-Agent": UA}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        hdrs["Content-Type"] = "application/json; charset=utf-8"
    if headers:
        hdrs.update(headers)

    last = (0, "no attempt")
    for attempt in range(retries + 1):
        req = urllib.request.Request(url, data=data, method=method, headers=hdrs)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode("utf-8", "replace")
                try:
                    return resp.status, (json.loads(raw) if raw.strip() else {})
                except Exception:
                    return resp.status, raw
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", "replace")
            try:
                body = json.loads(raw) if raw.strip() else {}
            except Exception:
                body = raw[:500]
            last = (exc.code, body)
            if exc.code not in retry_status:
                return last
        except Exception as exc:
            last = (0, "%s: %s" % (type(exc).__name__, exc))
        if attempt < retries:
            time.sleep(1.5 * (2 ** attempt))
    return last


def resend_call(method: str, path: str, key: str, payload=None,
                api_base: str = DEFAULT_API_BASE, timeout: int = 30,
                retries: int = 2) -> "tuple":
    return http_json(
        method, "%s%s" % (api_base.rstrip("/"), path),
        headers={"Authorization": "Bearer %s" % key},
        payload=payload, timeout=timeout, retries=retries,
    )


def explain_http(status: int, body) -> str:
    """把 Resend 的失败翻译成人话，顺带把两个高频误判点标出来。"""
    if status == 0:
        return "网络层失败（无法连接）：%s" % body
    if status == 401:
        return "API key 无效或已被轮换（HTTP 401）。重新取一把 key。"
    if status == 403:
        return (
            "HTTP 403 —— 通常是 Cloudflare 边缘拦截（error code 1010），"
            "而不是权限问题：检查请求是否带了浏览器 User-Agent。原始响应：%s" % body
        )
    if status == 422:
        return "请求被拒（HTTP 422），多为发件域名未验证或字段格式不对：%s" % body
    if status == 429:
        return "触发限流（HTTP 429），稍后重试或降低发送频率：%s" % body
    return "HTTP %s：%s" % (status, body)


# --------------------------------------------------------------------------- #
# 子命令
# --------------------------------------------------------------------------- #
def cmd_init(args) -> int:
    """写入/更新配置文件。只覆盖显式给出的项，其余保留。"""
    cfg = load_config()
    changes = {}
    if args.api_key:
        cfg["api_key"] = args.api_key.strip()
        changes["api_key"] = mask(cfg["api_key"])
    if args.from_:
        cfg["from"] = args.from_.strip()
        changes["from"] = cfg["from"]
    if args.reply_to:
        cfg["reply_to"] = args.reply_to.strip()
        changes["reply_to"] = cfg["reply_to"]
    if args.api_base:
        cfg["api_base"] = args.api_base.strip()
        changes["api_base"] = cfg["api_base"]

    if args.show:
        _, src_key = resolve(args, "api_key", ["MAIL_API_KEY", "RESEND_API_KEY"], ["api_key"])
        _, src_from = resolve(args, "from_", ["MAIL_FROM"], ["from"])
        emit({
            "ok": True,
            "config_file": str(config_path()),
            "config_file_exists": config_path().exists(),
            "resolved": {
                "api_key": mask(cfg_value_for("api_key")),
                "api_key_source": src_key or "(未配置)",
                "from": cfg_value_for("from"),
                "from_source": src_from or "(未配置)",
                "api_base": cfg_value_for("api_base") or DEFAULT_API_BASE,
            },
        })
        return 0

    if not changes:
        die("没有要写入的项。用法：init --api-key re_xxx --from 'Name <you@domain>'"
            "；或加 --show 查看当前配置。")

    p = save_config(cfg)
    emit({"ok": True, "config_file": str(p), "updated": changes,
          "note": "已按最小权限写入（POSIX 下 chmod 600）。请勿提交进仓库。"})
    return 0


def cfg_value_for(key: str) -> str:
    return str(load_config().get(key, "") or "")


def cmd_config(args) -> int:
    """展示生效配置及其来源（key 打码）。"""
    cfg = load_config()
    out = {"ok": True, "config_file": str(config_path()),
           "config_file_exists": config_path().exists(), "resolved": {}}
    for label, key, envs, cfgs in (
        ("api_key", "api_key", ["MAIL_API_KEY", "RESEND_API_KEY"], ["api_key"]),
        ("from", "from_", ["MAIL_FROM"], ["from"]),
        ("reply_to", "reply_to", ["MAIL_REPLY_TO"], ["reply_to"]),
        ("api_base", "api_base", ["MAIL_API_BASE"], ["api_base"]),
    ):
        v, src = resolve(args, key, envs, cfgs,
                         default=(DEFAULT_API_BASE if key == "api_base" else ""))
        out["resolved"][label] = mask(v) if key == "api_key" else v
        out["resolved"][label + "_source"] = src or "(未配置)"
    emit(out)
    return 0


def cmd_domains(args) -> int:
    key = resolve_api_key(args)
    base, _ = resolve(args, "api_base", ["MAIL_API_BASE"], ["api_base"], DEFAULT_API_BASE)
    st, body = resend_call("GET", "/domains", key, api_base=base,
                           timeout=args.timeout, retries=args.retries)
    if st != 200 or not isinstance(body, dict):
        emit({"ok": False, "http": st, "reason": explain_http(st, body)})
        return 1
    rows = [{"name": d.get("name"), "status": d.get("status"),
             "region": d.get("region"), "id": d.get("id")}
            for d in (body.get("data") or [])]
    emit({"ok": True, "count": len(rows), "domains": rows,
          "usable": sorted(r["name"] for r in rows if r["status"] == "verified")})
    return 0


def _posix_path_hint(raw: str) -> str:
    """跨平台复制命令时的经典坑：Windows 上 '/tmp/x' 会被解释为盘符相对路径。

    MSYS/Git-Bash 风格的路径喂给 Windows 版 Python，既不是绝对路径也不会报语法错，
    只会「文件不存在」，很容易误以为是脚本坏了。这里主动提示。
    """
    if os.name == "nt" and raw.startswith("/") and not re.match(r"^/[a-zA-Z]/", raw):
        return ("\n  提示：当前是 Windows，而 '%s' 是 POSIX 风格路径，会被解释为盘符相对路径"
                "（即 %s）。请改用 C:\\\\... 这样的绝对路径，"
                "或用 pwd -W 取得 Git-Bash 路径对应的 Windows 路径。" % (raw, raw.replace("/", "\\")))
    return ""


def _read_text_file(path: str, what: str) -> str:
    p = Path(path).expanduser()
    if not p.exists():
        die("%s文件不存在：%s%s" % (what, p, _posix_path_hint(path)))
    try:
        # 显式 utf-8：Windows 默认 cp936 会让含 emoji / 特殊符号的正文直接报错
        return p.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        die("%s不是 UTF-8 编码：%s（%s）。请先转成 UTF-8。" % (what, p, exc))


def _load_html(args) -> str:
    """--html-file 优先于 --html。长正文走文件传参，避免命令行转义与编码问题。"""
    path = (getattr(args, "html_file", "") or "").strip()
    if path and path not in ("-", "/dev/stdin"):
        return _read_text_file(path, "HTML 正文")
    if path in ("-", "/dev/stdin"):
        return sys.stdin.read()
    return getattr(args, "html", "") or ""


def _build_attachments(paths) -> "list":
    out = []
    for raw in (paths or []):
        p = Path(raw).expanduser()
        if not p.exists():
            die("附件不存在：%s%s" % (p, _posix_path_hint(raw)))
        if not p.is_file():
            die("附件不是文件：%s" % p)
        if p.stat().st_size > 40 * 1024 * 1024:
            die("附件超过 40MB 上限（Resend 限制）：%s" % p)
        ctype = mimetypes.guess_type(p.name)[0] or "application/octet-stream"
        out.append({
            "filename": p.name,
            "content": base64.b64encode(p.read_bytes()).decode("ascii"),
            "content_type": ctype,
        })
    return out


def _split_recipients(values) -> "list":
    """支持 --to a@x --to b@y，也支持 --to 'a@x,b@y'。"""
    out = []
    for v in (values or []):
        for part in str(v).split(","):
            part = part.strip()
            if part:
                out.append(part)
    return out


def cmd_send(args) -> int:
    key = resolve_api_key(args)
    base, _ = resolve(args, "api_base", ["MAIL_API_BASE"], ["api_base"], DEFAULT_API_BASE)
    from_, src_from = resolve(args, "from_", ["MAIL_FROM"], ["from"])
    if not from_:
        die("缺少发件人。用 --from '显示名 <you@yourdomain.com>'，"
            "或 init --from 写入配置，或 export MAIL_FROM=...")

    to = _split_recipients(args.to)
    if not to:
        die("缺少收件人：--to someone@example.com（多个用逗号或重复 --to）")

    reply_to, _ = resolve(args, "reply_to", ["MAIL_REPLY_TO"], ["reply_to"])

    html = _load_html(args)
    text = args.text or ""
    if getattr(args, "text_file", ""):
        text = _read_text_file(args.text_file, "纯文本正文")
    if not html and not text:
        text = "（无正文）"

    payload = {"from": from_, "to": to, "subject": args.subject}
    if html:
        # html 与 text 同给 → Resend 发 multipart/alternative：
        # 支持 HTML 的客户端渲染 html，纯文本客户端/反垃圾降级读 text
        payload["html"] = html
    if text:
        payload["text"] = text
    if reply_to:
        payload["reply_to"] = reply_to
    if args.tag:
        payload["tags"] = [{"name": "source", "value": args.tag}]
    if args.attach:
        payload["attachments"] = _build_attachments(args.attach)

    if args.dry_run:
        redacted = dict(payload)
        if "attachments" in redacted:
            # 复制每个附件对象并打码 base64 内容，保留 filename / content_type 便于核对
            redacted["attachments"] = [
                dict(a, content="<base64 %d chars>" % len(a.get("content", "")))
                for a in redacted["attachments"]
            ]
        emit({"ok": True, "dry_run": True, "would_send": redacted,
              "from_source": src_from, "api_base": base})
        return 0

    st, body = resend_call("POST", "/emails", key, payload,
                           api_base=base, timeout=args.timeout, retries=args.retries)
    if st not in (200, 201) or not isinstance(body, dict) or "id" not in body:
        emit({"ok": False, "http": st, "reason": explain_http(st, body),
              "request": {k: v for k, v in payload.items() if k != "attachments"}})
        return 1

    out = {"ok": True, "http": st, "id": body["id"], "from": from_,
           "to": to, "subject": args.subject}
    if args.wait:
        out["final"] = wait_terminal(body["id"], key, args.timeout, base, args.retries)
    emit(out)
    return 0


def _iso_local(ts) -> str:
    """把 Resend 返回的时间转成本机时区的可读字符串。

    Resend 的 ``created_at`` 是形如 ``2026-09-22 08:53:52.749000+00`` 的 ISO 字符串
    （UTC），**不是** unix 时间戳；直接用 int() 会抛异常、退回原字符串，
    于是字段名叫 local 却输出 UTC —— 必须真的解析。

    兼容 ``+00`` / ``Z`` / 数字时间戳三种形态，并保持 Python 3.8 可用
    （3.8 的 fromisoformat 不吃 'Z'，也不吃 ' +00' 这种两位偏移）。
    """
    if ts is None or ts == "":
        return ""
    if isinstance(ts, (int, float)):
        try:
            return time.strftime("%Y-%m-%d %H:%M:%S %z", time.localtime(int(ts)))
        except Exception:
            return str(ts)
    s = str(ts).strip()
    if re.fullmatch(r"\d{9,}", s):  # 纯数字 → 当作 unix 秒
        return time.strftime("%Y-%m-%d %H:%M:%S %z", time.localtime(int(s)))
    try:
        from datetime import datetime, timezone  # noqa: PLC0415
        t = s.replace(" ", "T")
        if t.endswith("Z"):
            t = t[:-1] + "+00:00"
        t = re.sub(r"([+-]\d{2})$", r"\1:00", t)  # '+00' -> '+00:00'
        dt = datetime.fromisoformat(t)
        if dt.tzinfo is None:  # 无时区信息时按 UTC 解释
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone().strftime("%Y-%m-%d %H:%M:%S %z")
    except Exception:
        return s


def wait_terminal(email_id: str, key: str, timeout: int,
                  api_base: str, retries: int = 2) -> "dict":
    """轮询直到 last_event 进入终态或超时。"""
    started = time.time()
    deadline = started + max(10, timeout)
    last = {}
    while True:
        st, body = resend_call("GET", "/emails/%s" % email_id, key,
                               api_base=api_base, timeout=20, retries=retries)
        if st == 200 and isinstance(body, dict):
            last = body
            if str(body.get("last_event", "")).lower() in TERMINAL_EVENTS:
                return {"last_event": str(body.get("last_event")).lower(),
                        "waited_s": round(time.time() - started, 1)}
        if time.time() >= deadline:
            return {"last_event": str(last.get("last_event") or "unknown").lower(),
                    "timeout": True, "waited_s": round(time.time() - started, 1)}
        time.sleep(3)


def cmd_get(args) -> int:
    key = resolve_api_key(args)
    base, _ = resolve(args, "api_base", ["MAIL_API_BASE"], ["api_base"], DEFAULT_API_BASE)
    st, body = resend_call("GET", "/emails/%s" % args.id, key,
                           api_base=base, timeout=args.timeout, retries=args.retries)
    if st != 200 or not isinstance(body, dict):
        emit({"ok": False, "http": st, "reason": explain_http(st, body)})
        return 1
    emit({"ok": True, "id": body.get("id"), "to": body.get("to"),
          "from": body.get("from"), "subject": body.get("subject"),
          "last_event": body.get("last_event"),
          "created_at": body.get("created_at"),
          "created_at_local": _iso_local(body["created_at"])
          if body.get("created_at") else None})
    return 0


def cmd_key(args) -> int:
    """（可选，DealClaw 平台专有）从平台配置接口取发信 key。

    实测口径：``X-Supplier-Id`` 与 ``X-Feishu-Open-Id`` 两个头**只校验非空**，
    不校验真实性、也不做租户隔离 —— 任何能构造出这两个头的人都能取到同一把 key。
    因此本能力仅为便利而设，别把它当访问控制。
    """
    supplier_id = (args.supplier_id or "").strip()
    if not supplier_id:
        die("缺少 --supplier-id")
    open_id = (args.open_id or "").strip() or ("ou_%s" % supplier_id)
    # 平台端点可覆盖：便于换环境（测试/生产）或换到自建网关
    platform_base = (os.environ.get("MAIL_PLATFORM_API_BASE", "").strip()
                     or PLATFORM_API_BASE).rstrip("/")
    url = "%s/agent/config/getApiKeys.json" % platform_base
    st, body = http_json("POST", url, payload={}, timeout=args.timeout,
                         retries=args.retries,
                         headers={"X-Supplier-Id": supplier_id, "X-Feishu-Open-Id": open_id})
    if st != 200 or not isinstance(body, dict):
        emit({"ok": False, "http": st, "reason": explain_http(st, body)})
        return 1
    data = body.get("data") or {}
    key = str(data.get("resendApiKey") or "").strip()
    if not key:
        emit({"ok": False, "error": "平台未返回 resendApiKey",
              "response_keys": sorted(data.keys())})
        return 1

    out = {"ok": True, "api_key": mask(key), "length": len(key),
           "supplier_id": supplier_id, "open_id": open_id,
           "platform_base": platform_base}
    if args.save:
        cfg = load_config()
        cfg["api_key"] = key
        if args.from_:
            cfg["from"] = args.from_
        p = save_config(cfg)
        out["saved_to"] = str(p)
    else:
        out["api_key_full"] = key
        out["hint"] = "加 --save 可写入配置文件（不打印明文）"
    emit(out)
    return 0


def cmd_doctor(args) -> int:
    """环境自检：一次性告诉你能不能发、缺什么。"""
    checks = []

    def add(name, ok, detail):
        checks.append({"check": name, "ok": bool(ok), "detail": str(detail)})

    py = "%d.%d.%d" % sys.version_info[:3]
    add("python_version", sys.version_info >= MIN_PY,
        "%s（要求 >= %d.%d）" % (py, MIN_PY[0], MIN_PY[1]))
    add("platform", True, "%s / %s" % (platform.system(), platform.machine()))

    enc = getattr(sys.stdout, "encoding", "") or "?"
    add("stdout_encoding", True, enc)

    cp = config_path()
    add("config_file", True, "%s（%s）" % (cp, "存在" if cp.exists() else "不存在，将用 env/cli"))

    # 标准库可用性（无第三方依赖）
    try:
        import urllib.request as _u  # noqa: F401
        add("stdlib_only", True, "urllib/json/base64/pathlib 均可用，无第三方依赖")
    except Exception as exc:
        add("stdlib_only", False, str(exc))

    # key
    key, src = resolve(args, "api_key", ["MAIL_API_KEY", "RESEND_API_KEY"], ["api_key"])
    add("api_key", bool(key), mask(key) + (" (来源 %s)" % src if src else ""))

    # from
    from_, src_from = resolve(args, "from_", ["MAIL_FROM"], ["from"])
    add("from_address", bool(from_),
        "%s (来源 %s)" % (from_, src_from) if from_ else "未配置（send 时必须提供 --from 或 MAIL_FROM）")
    if from_:
        m = re.search(r"<([^>]+)>", from_)
        addr = (m.group(1) if m else from_).strip()
        add("from_format", "@" in addr, "解析出地址：%s" % addr)

    # 网络与 key 有效性
    base, _ = resolve(args, "api_base", ["MAIL_API_BASE"], ["api_base"], DEFAULT_API_BASE)
    add("api_base", True, base)
    if key:
        st, body = resend_call("GET", "/domains", key, api_base=base,
                               timeout=args.timeout, retries=0)
        add("api_reachable_and_key_valid", st == 200, explain_http(st, body) if st != 200 else "GET /domains 200")
        if st == 200 and isinstance(body, dict):
            verified = sorted(d["name"] for d in (body.get("data") or [])
                              if d.get("status") == "verified")
            add("verified_domains_present", bool(verified),
                "可用域名：%s" % (", ".join(verified) if verified else "无（发信会被 422 拒）"))

    blocking = [c for c in checks if not c["ok"]]
    emit({"ok": not blocking, "version": __version__,
          "checks": checks,
          "verdict": "可以发信" if not blocking
          else "存在问题：%s" % "; ".join(c["check"] for c in blocking)})
    return 0 if not blocking else 1


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def _add_common(p):
    p.add_argument("--api-key", default="", help="发信 key；缺省读 MAIL_API_KEY / RESEND_API_KEY")
    p.add_argument("--api-base", default="", help="缺省 %s" % DEFAULT_API_BASE)
    p.add_argument("--timeout", type=int, default=30, help="单次请求超时秒数")
    p.add_argument("--retries", type=int, default=2, help="429/5xx 重试次数")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="mail.py",
        description="dealclaw-mail-send · 跨平台邮件发送 CLI（纯标准库，零第三方依赖）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="示例：\n"
               "  python mail.py init --api-key re_xxx --from 'Name <you@domain.com>'\n"
               "  python mail.py doctor\n"
               "  python mail.py send --to a@b.com --subject Hi --text hello --wait\n",
    )
    p.add_argument("--version", action="version", version="%(prog)s " + __version__)
    sub = p.add_subparsers(dest="cmd", required=True)

    i = sub.add_parser("init", help="写入/更新配置文件")
    i.add_argument("--api-key", default="")
    i.add_argument("--from", dest="from_", default="")
    i.add_argument("--reply-to", default="")
    i.add_argument("--api-base", default="")
    i.add_argument("--show", action="store_true", help="只显示当前配置，不写入")
    i.set_defaults(func=cmd_init)

    c = sub.add_parser("config", help="显示生效配置与来源（key 打码）")
    c.add_argument("--api-key", default="")
    c.add_argument("--api-base", default="")
    c.set_defaults(func=cmd_config)

    d = sub.add_parser("doctor", help="环境自检：能不能发、缺什么")
    _add_common(d)
    d.add_argument("--from", dest="from_", default="")
    d.set_defaults(func=cmd_doctor)

    dm = sub.add_parser("domains", help="列域名与验证状态（顺带校验 key）")
    _add_common(dm)
    dm.set_defaults(func=cmd_domains)

    s = sub.add_parser("send", help="发一封信")
    _add_common(s)
    s.add_argument("--from", dest="from_", default="", help="如 'Name <you@yourdomain.com>'")
    s.add_argument("--to", action="append", required=True, help="可重复或逗号分隔")
    s.add_argument("--subject", required=True)
    s.add_argument("--text", default="", help="纯文本正文")
    s.add_argument("--text-file", default="", help="从 UTF-8 文件读纯文本正文")
    s.add_argument("--html", default="", help="HTML 正文")
    s.add_argument("--html-file", default="", help="从 UTF-8 文件读 HTML 正文（优先于 --html；'-' 读 stdin）")
    s.add_argument("--reply-to", default="")
    s.add_argument("--tag", default="", help="打标签，便于在后台按来源筛选")
    s.add_argument("--attach", action="append", default=[],
                   help="附件路径，可重复；单个上限 40MB")
    s.add_argument("--wait", action="store_true", help="轮询到投递终态")
    s.add_argument("--dry-run", action="store_true", help="只打印请求体，不发送")
    s.set_defaults(func=cmd_send)

    g = sub.add_parser("get", help="按 id 查投递状态")
    _add_common(g)
    g.add_argument("--id", required=True)
    g.set_defaults(func=cmd_get)

    k = sub.add_parser("key", help="（可选）从 DealClaw 平台接口取 key")
    _add_common(k)
    k.add_argument("--supplier-id", default="", help="租户/供应商 ID")
    k.add_argument("--open-id", default="", help="缺省 ou_<supplier-id>")
    k.add_argument("--from", dest="from_", default="", help="配合 --save 一并写入发件人")
    k.add_argument("--save", action="store_true", help="写入配置文件（不打印明文 key）")
    k.set_defaults(func=cmd_key)

    return p


def main(argv=None) -> int:
    _force_utf8_io()
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
