#!/usr/bin/env python3
"""
mcp_diagnose.py — MCP connection diagnostic and recovery tool.

Pure Python stdlib (no pip dependencies). Handles:
- OAuth 2.0 PKCE + Dynamic Client Registration (RFC 7591)
- Token-based authentication (mcp.json headers.Authorization)
- MCP session management
- Tool catalog management

Usage:
    python3 mcp_diagnose.py auth [--port PORT]
    python3 mcp_diagnose.py auth --status
    python3 mcp_diagnose.py tools
    python3 mcp_diagnose.py registry_get
    python3 mcp_diagnose.py registry_publish <catalog_json> <expected_version>

Note: This is a diagnostic tool. For business tool calls, use the host MCP client.
"""

import argparse
import base64
import hashlib
import html
import http.server
import json
import os
import secrets
import socket
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser

# ============================================================================
# UTF-8 Encoding — prevent garbled output on Windows
# ============================================================================

if sys.stdout and hasattr(sys.stdout, 'buffer'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr and hasattr(sys.stderr, 'buffer'):
    import io
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# ============================================================================
# Configuration — 运行时从包内 mcp.json 读取，适配不同环境
# ============================================================================

# 可通过 --mcp-url CLI 参数覆盖（不使用环境变量）
_override_mcp_url = None


def _find_mcp_json():
    """从脚本位置向上查找 mcp.json（在 ZIP 包根目录或开发目录根）。"""
    current = os.path.dirname(os.path.abspath(__file__))
    for _ in range(6):
        candidate = os.path.join(current, "mcp.json")
        if os.path.isfile(candidate):
            return candidate
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    return None


def _load_config():
    """从 mcp.json 加载 MCP 配置。返回 (mcp_url, auth_header, urls_dict)。"""
    global _override_mcp_url

    mcp_json_path = _find_mcp_json()
    mcp_url = None
    auth_header = None

    if mcp_json_path:
        with open(mcp_json_path, encoding="utf-8") as f:
            mcp_config = json.load(f)
        servers = mcp_config.get("mcpServers", {})
        if servers:
            first_server = next(iter(servers.values()))
            mcp_url = first_server.get("url")
            # 检测 headers.Authorization（第二种认证方式）
            headers = first_server.get("headers", {})
            auth_header = headers.get("Authorization")

    # CLI 参数覆盖
    if _override_mcp_url:
        mcp_url = _override_mcp_url

    if not mcp_url:
        print(
            "ERROR: Cannot determine MCP URL.\n"
            "URL resolution sources (in priority order):\n"
            "1. --mcp-url CLI parameter (if provided)\n"
            "2. mcp.json mcpServers.*.url field\n\n"
            "Please ensure at least one source provides a valid URL.",
            file=sys.stderr,
        )
        sys.exit(1)

    # 从 MCP URL 手动构建 OAuth URL
    # 注意：服务器端的 /.well-known/oauth-authorization-server 发现端点
    # 返回的 URL 路径不正确（缺少 /coach 前缀），因此不使用发现端点
    parsed = urllib.parse.urlparse(mcp_url)
    path = parsed.path.rstrip('/')
    if path.endswith('/mcp'):
        path = path[:-4]

    urls = {
        "mcp_url": mcp_url,
        "register_url": f"{parsed.scheme}://{parsed.netloc}{path}/oauth/register",
        "token_url": f"{parsed.scheme}://{parsed.netloc}{path}/oauth/token",
        "authorize_url": f"{parsed.scheme}://{parsed.netloc}{path}/oauth/authorize",
        "resource": mcp_url,
    }

    return mcp_url, auth_header, urls


# 延迟初始化
_config = None


def _init_config():
    global _config
    if _config is None:
        _config = _load_config()
    return _config


def get_mcp_url():
    return _init_config()[0]


def get_auth_header():
    """获取 mcp.json 中的 Authorization header（如果存在）。"""
    return _init_config()[1]


def get_urls():
    return _init_config()[2]


def get_register_url():
    return get_urls()["register_url"]


def get_token_url():
    return get_urls()["token_url"]


def get_authorize_url():
    return get_urls()["authorize_url"]


def get_resource():
    return get_urls()["resource"]


MCP_VERSION = "2025-03-26"
REQUEST_TIMEOUT = 30  # 诊断工具不需要长超时

if sys.platform == "win32":
    CONFIG_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "coach-mcp-connect")
else:
    CONFIG_DIR = os.path.expanduser("~/.config/coach-mcp-connect")

DEFAULT_CALLBACK_PORT = 8766
CLIENT_NAME = "coach-mcp-connect-skill"


# ============================================================================
# Secure Storage
# ============================================================================


def _get_env_dir(mcp_url: str) -> str:
    """根据 MCP URL 生成环境隔离目录（与 upload_document.py 一致）"""
    domain = urllib.parse.urlparse(mcp_url).netloc
    env_dir = os.path.join(CONFIG_DIR, domain)
    os.makedirs(env_dir, mode=0o700, exist_ok=True)
    return env_dir


def _get_client_file() -> str:
    return os.path.join(_get_env_dir(get_mcp_url()), "client.json")


def _get_tokens_file() -> str:
    return os.path.join(_get_env_dir(get_mcp_url()), "tokens.json")


def _get_session_file() -> str:
    return os.path.join(_get_env_dir(get_mcp_url()), "session.json")


def _write_secure(path: str, data) -> None:
    """Write JSON with 0600 permissions. Atomic via temp-then-rename."""
    dir_path = os.path.dirname(path)
    os.makedirs(dir_path, mode=0o700, exist_ok=True)
    tmp_path = path + ".tmp"
    fd = os.open(tmp_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        os.write(fd, json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8"))
    finally:
        os.close(fd)
    os.replace(tmp_path, path)
    os.chmod(path, 0o600)


def _read_secure(path):
    """Read JSON from file. Returns None if not found or corrupt."""
    if not os.path.isfile(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def load_client():
    return _read_secure(_get_client_file())


def save_client(data):
    _write_secure(_get_client_file(), data)


def load_tokens():
    return _read_secure(_get_tokens_file())


def save_tokens(data):
    _write_secure(_get_tokens_file(), data)


def load_session():
    return _read_secure(_get_session_file())


def save_session(data):
    _write_secure(_get_session_file(), data)


def clear_session():
    try:
        os.remove(_get_session_file())
    except FileNotFoundError:
        pass


# ============================================================================
# OAuth Module
# ============================================================================


def register_client(callback_port):
    """POST /oauth/register — RFC 7591 Dynamic Client Registration."""
    callback_uri = f"http://127.0.0.1:{callback_port}/callback"
    redirect_uris = [f"http://127.0.0.1:{p}/callback" for p in range(callback_port, callback_port + 5)]
    body = json.dumps({
        "client_name": CLIENT_NAME,
        "redirect_uris": redirect_uris,
        "grant_types": ["authorization_code", "refresh_token"],
        "response_types": ["code"],
        "token_endpoint_auth_method": "none"
    }).encode("utf-8")

    req = urllib.request.Request(get_register_url(), data=body, method="POST")
    req.add_header("Content-Type", "application/json")

    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode("utf-8"))

    if "client_id" not in result:
        raise RuntimeError(f"Registration failed: {result}")

    result["_callback_port"] = callback_port
    result["_callback_uri"] = callback_uri
    save_client(result)
    return result


def generate_pkce():
    """Generate PKCE pair using S256. Returns (verifier, challenge)."""
    code_verifier = secrets.token_urlsafe(32)
    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    code_challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return code_verifier, code_challenge


def build_authorize_url(client_id, code_challenge, state, callback_uri):
    """Build authorization URL. resource parameter is MANDATORY."""
    params = urllib.parse.urlencode({
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": callback_uri,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "state": state,
        "resource": get_resource(),
    })
    return f"{get_authorize_url()}?{params}"


def _find_available_port(start_port, max_attempts=5):
    """Find an available port starting from start_port. Returns (port, is_changed)."""
    for offset in range(max_attempts):
        port = start_port + offset
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(("127.0.0.1", port))
            sock.close()
            return port, offset > 0
        except OSError:
            sock.close()
    raise OSError(f"No available port found in range {start_port}-{start_port + max_attempts - 1}")


def start_callback_server(port, expected_state, timeout=600):
    """Start HTTP server to capture OAuth callback. Returns auth code."""
    state = {"code": "", "error": ""}
    done = threading.Event()

    class CallbackHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            parsed = urllib.parse.urlparse(self.path)
            query = urllib.parse.parse_qs(parsed.query)

            if parsed.path != "/callback":
                self.send_response(404)
                self.end_headers()
                return

            if "error" in query:
                state["error"] = query["error"][0]
                self.send_response(400)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(f"<h1>Error: {html.escape(query['error'][0])}</h1>".encode())
                done.set()
                return

            if "code" not in query:
                self.send_response(400)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(b"<h1>No code parameter</h1>")
                return

            received_state = query.get("state", [None])[0]
            if received_state != expected_state:
                self.send_response(400)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(b"<h1>State mismatch</h1>")
                return

            state["code"] = query["code"][0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            msg = "<html><body><h1>Authorization successful!</h1><p>You can close this window.</p></body></html>"
            self.wfile.write(msg.encode("utf-8"))
            done.set()

        def log_message(self, format, *args):  # noqa: N802
            pass

    server = http.server.HTTPServer(("127.0.0.1", port), CallbackHandler)
    server.timeout = 1

    print(f"Listening on http://127.0.0.1:{port}/callback ...", file=sys.stderr)

    start_time = time.time()
    while not done.is_set() and (time.time() - start_time) < timeout:
        server.handle_request()

    server.server_close()

    if state["error"]:
        raise RuntimeError(f"OAuth error: {state['error']}")

    if not state["code"]:
        return None

    return state["code"]


def exchange_code(code, client_id, code_verifier, callback_uri):
    """POST /oauth/token with authorization_code grant."""
    body = urllib.parse.urlencode({
        "grant_type": "authorization_code",
        "code": code,
        "client_id": client_id,
        "redirect_uri": callback_uri,
        "code_verifier": code_verifier,
        "resource": get_resource(),
    }).encode("utf-8")

    req = urllib.request.Request(get_token_url(), data=body, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")

    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode("utf-8"))

    if "access_token" not in result:
        raise RuntimeError(f"Token exchange failed: {result}")

    save_tokens(result)
    return result


def refresh_token(client_id, refresh_token_value):
    """POST /oauth/token with refresh_token grant. Strict 4 fields only."""
    body = urllib.parse.urlencode({
        "grant_type": "refresh_token",
        "refresh_token": refresh_token_value,
        "client_id": client_id,
        "resource": get_resource(),
    }).encode("utf-8")

    req = urllib.request.Request(get_token_url(), data=body, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Token refresh failed: {e.code} {error_body}")

    if "access_token" not in result:
        raise RuntimeError(f"Token refresh failed: {result}")

    save_tokens(result)
    return result


def get_valid_token():
    """获取有效的 access token。

    认证优先级：
    1. mcp.json 中的 headers.Authorization（如果存在）
    2. 已保存的 OAuth token（自动 refresh）
    3. 返回 None，提示用户执行 auth 命令
    """
    # 1. 检查 mcp.json 的 headers.Authorization
    auth_header = get_auth_header()
    if auth_header:
        # 提取 token（可能是 "Bearer xxx" 或直接 "sk_xxx"）
        if auth_header.startswith("Bearer "):
            return auth_header[7:]
        return auth_header

    # 2. 检查已保存的 OAuth token
    tokens = load_tokens()
    client = load_client()

    if not tokens or not client:
        return None

    # 尝试使用当前 token
    access_token = tokens.get("access_token")
    if access_token:
        return access_token

    # 尝试 refresh
    refresh_token_value = tokens.get("refresh_token")
    client_id = client.get("client_id")

    if refresh_token_value and client_id:
        try:
            new_tokens = refresh_token(client_id, refresh_token_value)
            return new_tokens.get("access_token")
        except Exception as e:
            print(f"Token refresh failed: {e}", file=sys.stderr)
            return None

    return None


# ============================================================================
# MCP Session Module
# ============================================================================


def _parse_sse_response(body: str) -> dict:
    """Parse SSE response body, extract the last JSON-RPC message."""
    result = {}
    for line in body.splitlines():
        if line.startswith("data: "):
            try:
                result = json.loads(line[6:])
            except json.JSONDecodeError:
                continue
    if not result:
        raise RuntimeError("No valid JSON-RPC message found in SSE response")
    return result


def mcp_request(method, params=None, session_id=None, _retry_on_401: bool = True):
    """Make a JSON-RPC request to MCP server."""
    is_notification = method.startswith("notifications/")
    payload = {"jsonrpc": "2.0", "method": method}
    if not is_notification:
        payload["id"] = int(time.time() * 1000) % 1000000
    if params is not None:
        payload["params"] = params

    body = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(get_mcp_url(), data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json, text/event-stream")

    token = get_valid_token()
    if not token:
        raise RuntimeError(
            "Not authenticated. Run 'auth' for OAuth or configure headers.Authorization in mcp.json"
        )

    # Support direct API keys (sk_mcp_*) without Bearer prefix
    if token.startswith("sk_"):
        req.add_header("Authorization", token)
    else:
        req.add_header("Authorization", f"Bearer {token}")

    if session_id:
        req.add_header("mcp-session-id", session_id)

    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            content_type = resp.headers.get("Content-Type", "")
            response_body = resp.read().decode("utf-8")
            new_session_id = resp.headers.get("mcp-session-id")

            if not response_body.strip():
                return None, new_session_id

            # Handle SSE response (text/event-stream)
            if "text/event-stream" in content_type:
                result_msg = _parse_sse_response(response_body)
            else:
                result_msg = json.loads(response_body)

            if "error" in result_msg:
                error = result_msg["error"]
                code = error.get("code", -1)
                message = error.get("message", "Unknown error")
                raise RuntimeError(f"MCP error {code}: {message}")

            return result_msg.get("result", result_msg), new_session_id

    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")

        # Handle 401: auth expired
        if e.code == 401:
            clear_session()
            if _retry_on_401:
                tokens = load_tokens()
                client = load_client()
                if tokens and tokens.get("refresh_token") and client:
                    try:
                        refresh_token(client["client_id"], tokens["refresh_token"])
                        return mcp_request(method, params, session_id=None, _retry_on_401=False)
                    except Exception as e:
                        raise RuntimeError(
                            f"Script authentication failed (401).\n"
                            f"Token refresh attempt failed: {e}\n\n"
                            f"The script uses credentials from (in priority order):\n"
                            f"1. headers.Authorization in mcp.json (if configured)\n"
                            f"2. OAuth token cache (~/.config/coach-mcp-connect/<host>/tokens.json)\n\n"
                            f"To fix:\n"
                            f"- Run 'mcp_diagnose.py auth' to re-authenticate (refresh token may be expired)\n"
                            f"- Or check mcp.json for an outdated Authorization header\n"
                            f"- Verify mcp.json contains the correct MCP server URL"
                        )
            raise RuntimeError(
                "Script authentication failed (401).\n"
                "The script uses credentials from (in priority order):\n"
                "1. headers.Authorization in mcp.json (if configured)\n"
                "2. OAuth token cache (~/.config/coach-mcp-connect/<host>/tokens.json)\n\n"
                "To fix:\n"
                "- Run 'mcp_diagnose.py auth' to refresh your OAuth token\n"
                "- Or check mcp.json for an outdated Authorization header\n"
                "- Verify mcp.json contains the correct MCP server URL"
            )

        # Handle 404 with "Session not found"
        if "Session not found" in error_body and session_id:
            clear_session()
            return mcp_request(method, params, session_id=None)

        raise RuntimeError(f"MCP request failed: {e.code} {error_body}")


def initialize_session():
    """Initialize MCP session."""
    _, session_id = mcp_request("initialize", {
        "protocolVersion": MCP_VERSION,
        "capabilities": {},
        "clientInfo": {"name": CLIENT_NAME, "version": "1.0"}
    })

    if not session_id:
        save_session({"stateless": True})
    else:
        save_session({"session_id": session_id})

    mcp_request("notifications/initialized", session_id=session_id)
    return session_id


def get_session_id():
    """Get current session ID, initializing if needed."""
    session = load_session()
    if session:
        if session.get("stateless"):
            return None
        sid = session.get("session_id")
        if sid:
            return sid
    return initialize_session()


# ============================================================================
# Tool Calling
# ============================================================================


def list_tools():
    """List available MCP tools."""
    session_id = get_session_id()
    result, _ = mcp_request("tools/list", session_id=session_id)
    return result.get("tools", []) if result else []


def call_tool(tool_name, arguments=None):
    """Call an MCP tool. Returns the parsed result dict."""
    session_id = get_session_id()

    params = {"name": tool_name}
    if arguments is not None:
        params["arguments"] = arguments

    result, _ = mcp_request("tools/call", params, session_id=session_id)

    if result is None:
        raise RuntimeError("Tool call returned no result")

    content = result.get("content", [])
    if content and isinstance(content[0], dict):
        text = content[0].get("text", "")
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"text": text}

    return result


# ============================================================================
# Catalog Management
# ============================================================================


def registry_get():
    """Get current tool catalog from registry."""
    return call_tool("admin.registry_get", {})


def registry_publish(catalog, expected_version):
    """Publish updated tool catalog."""
    return call_tool("admin.registry_publish", {
        "catalog": catalog,
        "expectedVersion": expected_version
    })


# ============================================================================
# CLI Commands
# ============================================================================


def cmd_auth(args):
    """Handle auth command."""
    if args.status:
        # Check for legacy Authorization header in mcp.json
        auth_header = get_auth_header()
        if auth_header:
            print("⚠️  WARNING: mcp.json contains legacy Authorization header.", file=sys.stderr)
            print("   This may override your OAuth token cache and cause authentication failures.", file=sys.stderr)
            print("   Consider removing the Authorization field from mcp.json.", file=sys.stderr)
            print("   Run: grep -i 'Authorization' mcp.json", file=sys.stderr)
            print(file=sys.stderr)

        # 检查 mcp.json 的 headers.Authorization
        tokens = load_tokens()
        client = load_client()
        oauth_ok = bool(tokens and client)

        if auth_header and oauth_ok:
            print("Using headers.Authorization from mcp.json (priority over OAuth)")
            if auth_header:
                print("  ⚠️  See warning above: this may be a legacy token that could cause failures")
            client_id = (client or {}).get("client_id", "unknown")
            print(f"  OAuth tokens also present (client: {client_id})")
            print(f"  Config dir: {_get_env_dir(get_mcp_url())}")
        elif auth_header:
            token_preview = auth_header[:20] + "..." if len(auth_header) > 20 else auth_header
            print(f"Using headers.Authorization from mcp.json ({token_preview})")
            print("  ⚠️  See warning above: this may be a legacy token that could cause failures")
        elif oauth_ok:
            client_id = (client or {}).get("client_id", "unknown")
            print(f"✓ OAuth authenticated (client: {client_id})")
            print(f"  Config dir: {_get_env_dir(get_mcp_url())}")
        else:
            print("✗ Not authenticated")
            print("  Run 'auth' for OAuth or configure headers.Authorization in mcp.json")
        return

    # 如果 mcp.json 已有 headers.Authorization，提示用户
    auth_header = get_auth_header()
    if auth_header:
        print("Note: mcp.json already has headers.Authorization configured.")
        print("OAuth is not needed when using token-based authentication.")
        print("If you still want to use OAuth, continue below:")
        print()

    # 旧配置迁移：检测 HTTPS → HTTP 和端口变化
    client_file = _get_client_file()
    tokens_file = _get_tokens_file()
    if os.path.exists(client_file):
        with open(client_file) as f:
            client = json.load(f)

        existing_uris = client.get("redirect_uris", [])
        needs_reregister = any(uri.startswith("https://") for uri in existing_uris)

        old_callback_uri = client.get("_callback_uri", "")
        if old_callback_uri.startswith("https://"):
            needs_reregister = True

        current_port = args.port if hasattr(args, 'port') and args.port else DEFAULT_CALLBACK_PORT
        registered_ports = [uri.split(":")[2].split("/")[0] for uri in existing_uris if ":" in uri]
        if registered_ports and str(current_port) not in registered_ports:
            print(f"Port changed from {registered_ports} to {current_port}. Re-registering...", file=sys.stderr)
            needs_reregister = True

        if needs_reregister:
            print("Detected old HTTPS callback URI or port change. Re-registering with HTTP...", file=sys.stderr)
            os.remove(client_file)
            if os.path.exists(tokens_file):
                os.remove(tokens_file)

    # Start OAuth flow
    port = args.port or DEFAULT_CALLBACK_PORT
    try:
        port, port_changed = _find_available_port(port)
        if port_changed:
            print(f"Port {args.port} in use, using {port} instead", file=sys.stderr)
    except OSError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Register client if needed
    client = load_client()
    if not client:
        print("Registering new client...", file=sys.stderr)
        try:
            client = register_client(port)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                print(
                    "OAuth registration endpoint not found.\n"
                    "The server may not support OAuth. Configure headers.Authorization in mcp.json instead.",
                    file=sys.stderr,
                )
                sys.exit(1)
            raise
    else:
        client["_callback_port"] = port
        client["_callback_uri"] = f"http://127.0.0.1:{port}/callback"
        save_client(client)

    # Generate PKCE
    code_verifier, code_challenge = generate_pkce()
    state = secrets.token_urlsafe(16)

    if client:
        client["_code_verifier"] = code_verifier
        save_client(client)

    # Build authorize URL
    auth_url = build_authorize_url(
        client["client_id"],
        code_challenge,
        state,
        client["_callback_uri"]
    )

    print(f"\nOpening browser for authorization...", file=sys.stderr)
    print(f"If browser doesn't open, visit:\n{auth_url}\n", file=sys.stderr)

    auth_result: dict[str, str | None] = {"code": None, "error": None}

    def callback_wrapper() -> None:
        try:
            code = start_callback_server(port, state)
            auth_result["code"] = code
        except Exception as e:
            auth_result["error"] = str(e)

    server_thread = threading.Thread(target=callback_wrapper, daemon=True)
    server_thread.start()

    webbrowser.open(auth_url)

    print("Waiting for authorization callback...", file=sys.stderr)
    server_thread.join(timeout=600)

    if auth_result["error"]:
        print(f"Authorization failed: {auth_result['error']}", file=sys.stderr)
        sys.exit(1)

    if not auth_result["code"]:
        print("Timeout waiting for callback.", file=sys.stderr)
        print("You can manually complete authorization:", file=sys.stderr)
        print(f"1. Visit: {auth_url}", file=sys.stderr)
        print(f"2. After redirect, copy the 'code' parameter from the URL", file=sys.stderr)
        sys.exit(1)

    print("✓ Authorization code received", file=sys.stderr)
    print("Exchanging authorization code for tokens...", file=sys.stderr)
    try:
        tokens = exchange_code(
            auth_result["code"],
            client["client_id"],
            code_verifier,
            client["_callback_uri"]
        )
        print(f"✓ Authentication successful!", file=sys.stderr)
        print(f"✓ Tokens saved to {_get_tokens_file()}", file=sys.stderr)

        # Output Authorization header value for MCP client configuration
        if tokens and tokens.get("access_token"):
            token = tokens["access_token"]
            if token.startswith("sk_"):
                auth_value = token
            else:
                auth_value = f"Bearer {token}"

            print("\n" + "━" * 40, file=sys.stderr)
            print("MCP Client 配置 Token（有效期约 15 天）:", file=sys.stderr)
            print("━" * 40, file=sys.stderr)
            print(f"\nAuthorization header 值: {auth_value}\n", file=sys.stderr)
            print("请将上述 **值部分** 配置到你的 MCP client 的 headers.Authorization 字段。\n", file=sys.stderr)
            print("示例配置:", file=sys.stderr)
            print('  "headers": {', file=sys.stderr)
            print(f'    "Authorization": "{auth_value}"', file=sys.stderr)
            print('  }\n', file=sys.stderr)
            print("Token 过期后（MCP 调用返回 401），重新运行本命令完成浏览器 OAuth 授权。", file=sys.stderr)
    except Exception as e:
        print(f"Failed to exchange code for tokens: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_tools():
    """Handle tools command."""
    tools = list_tools()
    for tool in tools:
        print(f"- {tool['name']}: {tool.get('description', 'No description')}")


def cmd_registry_get():
    """Handle registry_get command."""
    result = registry_get()
    print(json.dumps(result, indent=2, ensure_ascii=False))


def cmd_registry_publish(args):
    """Handle registry_publish command."""
    catalog = json.loads(args.catalog)
    expected_version = args.expected_version
    result = registry_publish(catalog, expected_version)
    print(json.dumps(result, indent=2, ensure_ascii=False))


def main():
    global _override_mcp_url

    parser = argparse.ArgumentParser(description="MCP Diagnostic Tool")
    parser.add_argument("--mcp-url", help="Override MCP server URL")
    subparsers = parser.add_subparsers(dest="command", help="Command")

    # auth command
    auth_parser = subparsers.add_parser("auth", help="OAuth authentication")
    auth_parser.add_argument("--status", action="store_true", help="Show auth status")
    auth_parser.add_argument("--port", type=int, help="Callback port")

    # tools command
    subparsers.add_parser("tools", help="List available tools")

    # registry_get command
    subparsers.add_parser("registry_get", help="Get tool catalog")

    # registry_publish command
    publish_parser = subparsers.add_parser("registry_publish", help="Publish tool catalog")
    publish_parser.add_argument("catalog", help="Catalog JSON")
    publish_parser.add_argument("expected_version", type=int, help="Expected version")

    args = parser.parse_args()

    if args.mcp_url:
        _override_mcp_url = args.mcp_url

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        if args.command == "auth":
            cmd_auth(args)
        elif args.command == "tools":
            cmd_tools()
        elif args.command == "registry_get":
            cmd_registry_get()
        elif args.command == "registry_publish":
            cmd_registry_publish(args)
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        sys.exit(130)
    except SystemExit:
        raise
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
