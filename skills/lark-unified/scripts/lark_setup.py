#!/usr/bin/env python3
"""
lark_setup.py - Lark CLI auto-setup script

Implements the same device flow as `lark-cli config init --new` but
works in non-TTY environments (e.g. WorkBuddy, CI, headless shells).

Usage:
    python3 lark_setup.py [--brand feishu|lark] [--no-browser]

Steps:
    1. POST to feishu app registration API (begin)
    2. Build verification URL
    3. Open browser automatically (unless --no-browser)
    4. Poll until user completes browser authorization
    5. Write App ID + Secret to lark-cli config via non-interactive flag
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request


# --- Endpoints (mirrors internal/core/endpoints.go) ---
ENDPOINTS = {
    "feishu": {
        "accounts": "https://accounts.feishu.cn",
        "open":     "https://open.feishu.cn",
    },
    "lark": {
        "accounts": "https://accounts.larksuite.com",
        "open":     "https://open.larksuite.com",
    },
}

CLI_VERSION = "1.0.0"


def post_form(url, data: dict) -> dict:
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        # Feishu returns OAuth errors (e.g. authorization_pending) as HTTP 400
        raw = e.read()
        try:
            return json.loads(raw)
        except Exception:
            raise RuntimeError(f"HTTP {e.code}: {raw.decode(errors='replace')}")


def begin_registration(brand: str) -> dict:
    """Step 1: Initiate the app registration device flow."""
    # Registration begin always uses feishu accounts endpoint
    url = ENDPOINTS["feishu"]["accounts"] + "/oauth/v1/app/registration"
    resp = post_form(url, {
        "action": "begin",
        "archetype": "PersonalAgent",
        "auth_method": "client_secret",
        "request_user_info": "open_id tenant_brand",
    })
    if "error" in resp:
        raise RuntimeError(f"Registration failed: {resp.get('error_description', resp['error'])}")
    return resp


def build_verification_url(base_url: str) -> str:
    """Append CLI tracking params (mirrors BuildVerificationURL in Go)."""
    sep = "&" if "?" in base_url else "?"
    return (
        base_url
        + sep
        + f"lpv={urllib.parse.quote(CLI_VERSION)}"
        + f"&ocv={urllib.parse.quote(CLI_VERSION)}"
        + "&from=cli"
    )


def poll_registration(device_code: str, brand: str, interval: int, expires_in: int) -> dict:
    """Step 4: Poll until user completes browser authorization."""
    url = ENDPOINTS[brand]["accounts"] + "/oauth/v1/app/registration"
    deadline = time.time() + expires_in
    current_interval = interval
    attempts = 0

    while time.time() < deadline and attempts < 200:
        attempts += 1
        time.sleep(current_interval)

        resp = post_form(url, {"action": "poll", "device_code": device_code})
        err = resp.get("error", "")

        if not err and resp.get("client_id"):
            return resp  # success

        if err == "authorization_pending":
            print("  Waiting...", flush=True)
            continue
        elif err == "slow_down":
            current_interval = min(current_interval + 5, 60)
            continue
        elif err in ("access_denied",):
            raise RuntimeError("Authorization denied by user.")
        elif err in ("expired_token", "invalid_grant"):
            raise RuntimeError("Device code expired. Please try again.")
        elif err:
            raise RuntimeError(f"Poll error: {resp.get('error_description', err)}")

    raise RuntimeError("Authorization timed out. Please try again.")


def resolve_lark_cli() -> str:
    """Find lark-cli even when npm global bin is not in PATH."""
    candidates = []
    env_cli = os.environ.get("LARK_CLI")
    if env_cli:
        candidates.append(env_cli)
    path_cli = shutil.which("lark-cli")
    if path_cli:
        candidates.append(path_cli)

    home = os.path.expanduser("~")
    candidates.extend([
        os.path.join(home, ".npm-global", "bin", "lark-cli"),
        "/usr/local/bin/lark-cli",
        "/opt/homebrew/bin/lark-cli",
    ])

    try:
        npm_prefix = subprocess.run(
            ["npm", "prefix", "-g"], capture_output=True, text=True, timeout=10
        ).stdout.strip()
        if npm_prefix:
            candidates.append(os.path.join(npm_prefix, "bin", "lark-cli"))
    except Exception:
        pass

    for candidate in candidates:
        if candidate and os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    raise RuntimeError("lark-cli not found. Install it with: env -u NODE_OPTIONS npm install -g @larksuite/cli")


def save_config(app_id: str, app_secret: str, brand: str):
    """Step 5: Write config via lark-cli non-interactive flags."""
    lark_cli = resolve_lark_cli()
    proc = subprocess.run(
        [lark_cli, "config", "init",
         "--app-id", app_id,
         "--app-secret-stdin",
         "--brand", brand],
        input=app_secret,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"lark-cli config init failed:\n{proc.stderr}")
    print(f"  {proc.stderr.strip()}" if proc.stderr.strip() else "  Config saved.")


def open_browser(url: str, no_browser: bool):
    """Open URL in the default browser, or print it if --no-browser."""
    if no_browser:
        print("\n  ACTION REQUIRED: copy and open this URL in your browser to authorize Feishu/Lark:")
        print(f"  {url}\n")
        print("  Keep this setup command running while you finish authorization in the browser.\n")
        return
    try:
        subprocess.run(["open", url], check=True)        # macOS
        print(f"  Browser opened. If it didn't open, visit:\n  {url}")
    except Exception:
        try:
            subprocess.run(["xdg-open", url], check=True)  # Linux
        except Exception:
            print(f"  Could not open browser automatically.\n  Please visit:\n  {url}")


def main():
    parser = argparse.ArgumentParser(description="Lark CLI auto-setup (no TTY required)")
    parser.add_argument("--brand", choices=["feishu", "lark"], default="feishu",
                        help="Platform brand (default: feishu)")
    parser.add_argument("--no-browser", action="store_true",
                        help="Print URL instead of opening browser")
    args = parser.parse_args()

    brand = args.brand

    print(f"[lark-setup] Starting app registration flow (brand={brand})...")

    # Step 1: Begin
    print("[lark-setup] Step 1/4: Requesting device code...")
    reg = begin_registration(brand)

    device_code = reg["device_code"]
    user_code   = reg.get("user_code", "")
    expires_in  = int(reg.get("expires_in", 300))
    interval    = int(reg.get("interval", 5))

    # Step 2: Use URL from API response directly (verification_uri_complete already has user_code)
    verification_url = reg.get("verification_uri_complete") or reg.get("verification_uri", "")

    # Step 3: Open browser
    print(f"[lark-setup] Step 2/4: Opening browser for authorization...")
    open_browser(verification_url, args.no_browser)

    # Step 4: Poll
    print("[lark-setup] Step 3/4: Waiting for you to complete authorization in browser...")
    result = poll_registration(device_code, brand, interval, expires_in)

    # Handle Lark brand retry (mirrors Go logic)
    user_info = result.get("user_info", {}) or {}
    tenant_brand = user_info.get("tenant_brand", brand)
    if not result.get("client_secret") and tenant_brand == "lark":
        print("[lark-setup]   Detected Lark tenant, retrying with lark endpoint...")
        result = poll_registration(device_code, "lark", interval, expires_in)
        tenant_brand = "lark"

    app_id     = result["client_id"]
    app_secret = result["client_secret"]
    final_brand = tenant_brand if tenant_brand in ("feishu", "lark") else brand

    print(f"[lark-setup] Authorization complete! App ID: {app_id}")

    # Step 5: Save config
    print("[lark-setup] Step 4/4: Saving configuration...")
    save_config(app_id, app_secret, final_brand)

    print(f"\n[lark-setup] Done! lark-cli is now configured.")
    print(f"  App ID: {app_id}")
    print(f"  Brand:  {final_brand}")
    print(f"\n  Run `lark-cli config show` to verify app setup.")
    print(f"  Run `lark-cli auth status` to verify user OAuth before personal data operations.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[lark-setup] Cancelled.")
        sys.exit(1)
    except Exception as e:
        print(f"\n[lark-setup] Error: {e}", file=sys.stderr)
        sys.exit(1)
