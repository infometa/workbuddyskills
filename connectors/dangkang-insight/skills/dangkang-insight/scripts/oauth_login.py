# -*- coding: utf-8 -*-
"""dangkang-insight —— OAuth 重新授权（PKCE 授权码流程 + 本地回调）

为什么需要这个脚本
------------------
脚本通道的令牌（`config/.token.json`）**只能刷新，不能自行获取**。当刷新返回
`invalid_grant: 平台登录会话已失效，请重新授权` 时，说明这枚 refresh_token 已经作废，
必须重新走一次完整的授权码流程。以前这一步只能靠外部手工注入令牌，本脚本把它自动化。

用法
----
    python scripts/oauth_login.py                  # 默认端口 8765，等待 900 秒
    python scripts/oauth_login.py --port 8790      # 换端口（端口变了会自动 DCR 注册新客户端）
    python scripts/oauth_login.py --new-client     # 强制重新注册 OAuth 客户端
    python scripts/oauth_login.py --client-id wb_xxxxxxxx
    python scripts/oauth_login.py --wait 1800      # 自定义等待秒数

执行完终端会打印一行 `AUTH_URL: https://...`（同时写入 `logs/oauth_auth_url.txt`）。
把这条链接交给用户，让用户**自己复制到浏览器**打开、登录平台账号并确认授权；
浏览器随后会跳回 `http://localhost:<port>/callback`，脚本自动用 code 换取 token
并写回 `config/.token.json`。

退出码
------
    0  授权成功，令牌已写入 config/.token.json
    1  超时 / 用户侧未完成授权
    2  拿到 code 但换取令牌失败
    3  端口不可用或客户端注册失败
"""

import argparse
import base64
import hashlib
import json
import os
import socket
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CONFIG_DIR = os.path.join(ROOT, "config")
LOGS_DIR = os.path.join(ROOT, "logs")
INI_PATH = os.path.join(CONFIG_DIR, "mcp.ini")
TOKEN_CACHE = os.path.join(CONFIG_DIR, ".token.json")
AUTH_URL_FILE = os.path.join(LOGS_DIR, "oauth_auth_url.txt")
RESULT_FILE = os.path.join(LOGS_DIR, "oauth_result.json")

DEFAULT_MCP_URL = "https://lxyq.cssyq.com.cn/ggyw/mcp"
DEFAULT_PORT = 8765
DEFAULT_WAIT = 900
CLIENT_NAME = "WorkBuddy dangkang-insight"


def parse_ini(path):
    """极简 INI 解析：返回 {section: {key: value}}。文件缺失返回 {}。"""
    out = {}
    try:
        with open(path, encoding="utf-8") as f:
            section = None
            for raw in f:
                line = raw.strip()
                if not line or line.startswith(("#", ";")):
                    continue
                if line.startswith("[") and line.endswith("]"):
                    section = line[1:-1].strip().lower()
                    out.setdefault(section, {})
                    continue
                if section and "=" in line:
                    k, v = line.split("=", 1)
                    out[section][k.strip().lower()] = v.strip()
    except OSError:
        return {}
    return out


def endpoints():
    cfg = parse_ini(INI_PATH).get("mcp", {})
    mcp_url = cfg.get("url") or DEFAULT_MCP_URL
    issuer = mcp_url.split("/mcp", 1)[0]
    authz = cfg.get("authorization_endpoint") or (issuer + "/oauth2/authorize")
    token = cfg.get("token_endpoint") or (issuer + "/oauth2/token")
    register = issuer + "/oauth2/register"
    return authz, token, register


def stored_client_id():
    try:
        with open(TOKEN_CACHE, encoding="utf-8") as f:
            return (json.load(f).get("client_id") or "").strip()
    except (OSError, ValueError):
        return ""


def port_available(port):
    s = socket.socket()
    try:
        s.bind(("127.0.0.1", port))
        return True
    except OSError:
        return False
    finally:
        s.close()


def pick_port(preferred):
    for p in range(preferred, preferred + 20):
        if port_available(p):
            return p
    raise RuntimeError("端口 %d~%d 均被占用" % (preferred, preferred + 19))


def register_client(register_ep, redirect_uri):
    """动态客户端注册（DCR, RFC 7591）。返回新的 client_id。"""
    body = json.dumps({
        "client_name": CLIENT_NAME,
        "redirect_uris": [redirect_uri],
        "grant_types": ["authorization_code", "refresh_token"],
        "response_types": ["code"],
        "token_endpoint_auth_method": "none",
        "scope": "mcp",
    }).encode("utf-8")
    req = urllib.request.Request(register_ep, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")
    req.add_header("User-Agent", "srd-oauth-login/1.0")
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read().decode("utf-8", "replace"))
    cid = (data.get("client_id") or "").strip()
    if not cid:
        raise RuntimeError("注册响应里没有 client_id：%s" % data)
    return cid


def build_authz_url(authz_ep, client_id, redirect_uri, state, challenge):
    return authz_ep + "?" + urllib.parse.urlencode({
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": "mcp",
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    })


def probe_authz(url):
    """轻量探活授权链接：确认客户端与 redirect_uri 被服务端接受。

    返回 (ok, detail)。ok=False 时通常是「客户端不认识这个 redirect_uri」，
    此时应改为 DCR 注册一个匹配当前端口的新客户端。
    """
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "Mozilla/5.0")
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            head = r.read(400).decode("utf-8", "replace")
            if '"error"' in head or "invalid_request" in head:
                return False, head[:300]
            return True, r.geturl()
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read(400).decode("utf-8", "replace")
        except Exception:
            pass
        return False, "HTTP %s %s" % (e.code, body[:200])
    except Exception as e:  # noqa: BLE001 - 网络异常一律降级为「探测失败」
        return False, "%s: %s" % (type(e).__name__, e)


def exchange_code(token_ep, code, redirect_uri, client_id, verifier):
    data = urllib.parse.urlencode({
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
        "code_verifier": verifier,
    }).encode("utf-8")
    req = urllib.request.Request(token_ep, data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    req.add_header("Accept", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read(600).decode("utf-8", "replace").strip()
        except Exception:  # noqa: BLE001
            pass
        raise RuntimeError("令牌端点返回 HTTP %s：%s" % (e.code, body or "(空响应)")) from e


def save_token(tk, client_id):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    payload = {
        "access_token": tk["access_token"],
        "refresh_token": tk.get("refresh_token", ""),
        "client_id": client_id,
        "expires_at": time.time() + float(tk.get("expires_in") or 0),
        "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    with open(TOKEN_CACHE, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return TOKEN_CACHE


PAGE = """<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<title>{title}</title></head>
<body style="font-family:system-ui,-apple-system,'Segoe UI',sans-serif;background:#f5f7fa;
display:flex;align-items:center;justify-content:center;height:100vh;margin:0">
<div style="background:#fff;padding:40px 56px;border-radius:12px;
box-shadow:0 8px 24px rgba(0,0,0,.08);text-align:center;max-width:520px">
<h2 style="color:{color};margin:0 0 8px;font-weight:500">{title}</h2>
<p style="color:#555;margin:0;line-height:1.6">{desc}</p></div></body></html>"""


class CallbackHandler(BaseHTTPRequestHandler):
    captured = {}

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path != "/callback":
            self.send_response(404)
            self.end_headers()
            return
        q = urllib.parse.parse_qs(parsed.query)
        self.captured.update({k: v[0] for k, v in q.items()})
        ok = "code" in self.captured
        body = PAGE.format(
            title="授权成功" if ok else "授权未完成",
            color="#16794b" if ok else "#b45309",
            desc=("请关闭本页面，回到对话继续检测。"
                  if ok else json.dumps(self.captured, ensure_ascii=False)),
        ).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
        self.server.done = True

    def log_message(self, *args):
        pass


def wait_for_code(port, deadline):
    handler_cls = type("BoundHandler", (CallbackHandler,), {"captured": {}})
    srv = HTTPServer(("127.0.0.1", port), handler_cls)
    srv.timeout = 1
    srv.done = False
    try:
        while time.time() < deadline and not srv.done:
            if "code" in handler_cls.captured or "error" in handler_cls.captured:
                break
            srv.handle_request()
    finally:
        srv.server_close()
    return handler_cls.captured


def main(argv):
    ap = argparse.ArgumentParser(description="dangkang-insight OAuth 重新授权")
    ap.add_argument("--port", type=int, default=DEFAULT_PORT, help="本地回调端口（默认 8765）")
    ap.add_argument("--wait", type=int, default=DEFAULT_WAIT, help="等待扫码/登录的秒数（默认 900）")
    ap.add_argument("--client-id", default="", help="显式指定 OAuth 客户端 ID")
    ap.add_argument("--new-client", action="store_true", help="强制重新注册 OAuth 客户端")
    args = ap.parse_args(argv[1:])

    os.makedirs(LOGS_DIR, exist_ok=True)
    authz_ep, token_ep, register_ep = endpoints()

    try:
        port = pick_port(args.port)
    except RuntimeError as e:
        print("[错误] %s" % e)
        return 3
    redirect_uri = "http://localhost:%d/callback" % port

    verifier = base64.urlsafe_b64encode(os.urandom(48)).decode().rstrip("=")
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
    state = base64.urlsafe_b64encode(os.urandom(16)).decode().rstrip("=")

    client_id = args.client_id.strip()
    if not client_id and not args.new_client:
        client_id = stored_client_id()
        if client_id and port != DEFAULT_PORT:
            client_id = ""
    if client_id:
        candidate = build_authz_url(authz_ep, client_id, redirect_uri, state, challenge)
        ok, detail = probe_authz(candidate)
        if not ok:
            print("[提示] 复用客户端 %s 失败（%s），改为重新注册客户端" % (client_id[:16], detail))
            client_id = ""
    if not client_id:
        try:
            client_id = register_client(register_ep, redirect_uri)
            print("[客户端] 已注册新的 OAuth 客户端：%s" % client_id)
        except Exception as e:  # noqa: BLE001
            print("[错误] 注册 OAuth 客户端失败：%s: %s" % (type(e).__name__, e))
            return 3

    url = build_authz_url(authz_ep, client_id, redirect_uri, state, challenge)
    with open(AUTH_URL_FILE, "w", encoding="utf-8") as f:
        f.write(url)
    print("AUTH_URL: %s" % url, flush=True)
    print("[提示] 请让用户在浏览器打开上面的链接，登录平台账号并确认授权；"
          "完成后浏览器会自动跳回本机（%s）。" % redirect_uri, flush=True)

    captured = wait_for_code(port, time.time() + args.wait)

    result = {"params": captured, "client_id": client_id, "redirect_uri": redirect_uri}
    if not captured:
        result["status"] = "timeout"
        with open(RESULT_FILE, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print("[超时] %d 秒内没有收到回调，授权链接可能已过期，请重新运行本脚本。" % args.wait)
        return 1

    if captured.get("error"):
        result["status"] = "error"
        with open(RESULT_FILE, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print("[失败] 授权被拒绝或出错：%s" % json.dumps(captured, ensure_ascii=False))
        return 1

    if captured.get("state") and captured["state"] != state:
        result["state_mismatch"] = True
        print("[警告] state 校验不一致，但仍尝试换取令牌。")

    try:
        tk = exchange_code(token_ep, captured["code"], redirect_uri, client_id, verifier)
    except Exception as e:  # noqa: BLE001
        result["status"] = "token_error"
        result["token_error"] = "%s: %s" % (type(e).__name__, e)
        with open(RESULT_FILE, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print("[失败] 换取令牌出错：%s: %s" % (type(e).__name__, e))
        return 2

    if not tk.get("access_token"):
        result["status"] = "token_error"
        result["token_response"] = {k: str(v)[:120] for k, v in tk.items()}
        with open(RESULT_FILE, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print("[失败] 令牌响应里没有 access_token：%s" % json.dumps(tk, ensure_ascii=False)[:300])
        return 2

    saved = save_token(tk, client_id)
    result["status"] = "ok"
    result["saved_to"] = saved
    result["expires_in"] = tk.get("expires_in")
    with open(RESULT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print("[成功] 授权完成，令牌已写入 %s（access_token 有效期约 %s 秒）"
          % (saved, tk.get("expires_in")))
    print("RESULT: %s" % json.dumps(
        {"status": "ok", "client_id": client_id, "expires_in": tk.get("expires_in")},
        ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
