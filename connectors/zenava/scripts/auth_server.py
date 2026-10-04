#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Zenava Connector 本地授权页（WorkBuddy CLI 认证入口）。

启动本机回环 HTTP 服务并输出 http://127.0.0.1:<port>/?state=... ，
WorkBuddy（authUrlDomain=127.0.0.1 + authWaitForExit=true）打开该页面，
用户在页面填写平台 / API 地址 / 凭证，提交后写入 ~/.zenava/profile.json
（profile 名 workbuddy，并设为 currentProfile，权限 0600），随后进程以 0 退出。

仅使用 Python 标准库；不依赖 zenava 包导入。

用法：
  auth_server.py           # 启动本地授权页（默认）
  auth_server.py --status  # 检查 currentProfile 凭证完备性，输出「已连接」
  auth_server.py --logout  # 删除 workbuddy profile；若其为 current 则清空 currentProfile
"""

from __future__ import annotations

import json
import os
import re
import secrets
import subprocess
import sys
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ZENAVA_HOME = Path.home() / ".zenava"
PROFILE_PATH = ZENAVA_HOME / "profile.json"
PROFILE_NAME = "workbuddy"
PAGE_TTL_SECONDS = 300
ASSETS_DIR = Path(__file__).resolve().parent / "assets"
ALLOWED_ASSETS = {
    "workbuddy-logo.svg": "image/svg+xml",
    "zenava-logo.png": "image/png",
}

SERVER = None  # type: ignore
STATE = ""
STATE_USED = False
EXIT_CODE = 1


def _parse_form_body(raw, content_type):
    """解析表单：兼容 urlencoded 与 multipart/form-data。"""
    if not content_type:
        return {}
    if content_type.startswith("application/x-www-form-urlencoded"):
        return {k: (v[0] if v else "") for k, v in urllib.parse.parse_qs(raw).items()}
    if content_type.startswith("multipart/form-data"):
        boundary = content_type.split("boundary=", 1)[1].strip().strip('"')
        out = {}
        for part in raw.split("--" + boundary):
            if "\r\n\r\n" not in part:
                continue
            head, _, value = part.partition("\r\n\r\n")
            if value.endswith("\r\n"):
                value = value[:-2]
            m = re.search(r'name="([^"]+)"', head)
            if m:
                out.setdefault(m.group(1), value)
        return out
    return {}


def _nonempty(value) -> bool:
    return bool(value and str(value).strip())


def _load_store() -> dict:
    """Load profile.json store; preserve unknown root keys."""
    store = {"currentProfile": None, "profiles": {}}
    if not PROFILE_PATH.exists():
        return store
    try:
        raw = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError):
        return store
    if not isinstance(raw, dict):
        return store
    if isinstance(raw.get("profiles"), dict):
        store["profiles"] = dict(raw["profiles"])
        current = raw.get("currentProfile")
        store["currentProfile"] = current if current else None
        for key, value in raw.items():
            if key not in ("currentProfile", "profiles"):
                store[key] = value
        return store
    # Legacy flat map: wrap without inventing currentProfile.
    profiles = {}
    for name, entry in raw.items():
        if isinstance(entry, dict):
            profiles[name] = dict(entry)
    store["profiles"] = profiles
    return store


def _write_store(store: dict) -> None:
    ZENAVA_HOME.mkdir(parents=True, exist_ok=True)
    tmp = PROFILE_PATH.with_suffix(".json.tmp")
    tmp.write_text(
        json.dumps(store, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if os.name != "nt":
        os.chmod(tmp, 0o600)
    os.replace(tmp, PROFILE_PATH)
    if os.name != "nt":
        try:
            os.chmod(PROFILE_PATH, 0o600)
        except OSError:
            pass


def _validate(payload):
    platform = (payload.get("platform_type") or "").strip().lower()
    endpoint = (payload.get("endpoint") or "").strip()

    if platform not in ("cticloud", "clink2"):
        return None, "平台类型须为 cticloud 或 clink2。"
    if not endpoint.startswith(("https://", "http://")):
        return None, "API 地址须以 https:// 或 http:// 开头。"

    if platform == "clink2":
        access_key_id = (payload.get("access_key_id") or "").strip()
        access_key_secret = (payload.get("access_key_secret") or "").strip()
        expires_raw = (payload.get("expires") or "").strip()
        if not access_key_id or not access_key_secret:
            return None, "Clink2 须同时填写 AccessKeyId 与 AccessKeySecret。"
        expires = 60
        if expires_raw:
            try:
                expires = int(expires_raw)
            except ValueError:
                return None, "Expires 须为整数秒（1–86400）。"
            if expires < 1 or expires > 86400:
                return None, "Expires 须在 1–86400 之间。"
        cfg = {
            "platform_type": platform,
            "endpoint": endpoint.rstrip("/"),
            "access_key_id": access_key_id,
            "access_key_secret": access_key_secret,
            "expires": expires,
            "log": True,
        }
        return cfg, ""

    # cticloud: token 优先；否则 AK/SK
    vt_raw = (payload.get("validate_type") or "").strip()
    enterprise = (payload.get("enterprise_id") or "").strip()
    department = (payload.get("department_id") or "").strip()
    token = (payload.get("token") or "").strip()
    access_key_id = (payload.get("access_key_id") or "").strip()
    access_key_secret = (payload.get("access_key_secret") or "").strip()
    auth_mode = (payload.get("auth_mode") or "").strip().lower()

    use_aksk = auth_mode == "ak-sk" or (
        not token and access_key_id and access_key_secret
    )
    if use_aksk:
        if not access_key_id or not access_key_secret:
            return None, "CtiCloud AK/SK 模式须同时填写 AccessKeyId 与 AccessKeySecret。"
        expires_raw = (payload.get("expires") or "").strip()
        expires = 60
        if expires_raw:
            try:
                expires = int(expires_raw)
            except ValueError:
                return None, "Expires 须为整数秒（1–86400）。"
            if expires < 1 or expires > 86400:
                return None, "Expires 须在 1–86400 之间。"
        cfg = {
            "platform_type": platform,
            "endpoint": endpoint.rstrip("/"),
            "access_key_id": access_key_id,
            "access_key_secret": access_key_secret,
            "expires": expires,
            "validate_type": int(vt_raw) if vt_raw in ("1", "2") else 2,
            "enterprise_id": enterprise or None,
            "department_id": department or None,
            "token": None,
            "log": True,
        }
        return cfg, ""

    if vt_raw not in ("1", "2"):
        return None, "验证方式须为 1（部门编号验证）或 2（企业编号验证）。"
    validate_type = int(vt_raw)
    if validate_type == 2 and not enterprise:
        return None, "验证方式为 2（企业编号验证）时，企业编号必填。"
    if validate_type == 1 and not department:
        return None, "验证方式为 1（部门编号验证）时，部门编号必填。"
    if not token:
        return None, "接口 Token 必填（或改用 AK/SK 模式）。"

    cfg = {
        "platform_type": platform,
        "endpoint": endpoint.rstrip("/"),
        "validate_type": validate_type,
        "enterprise_id": enterprise or None,
        "department_id": department or None,
        "token": token,
        "access_key_id": None,
        "access_key_secret": None,
        "expires": None,
        "log": True,
    }
    return cfg, ""


def _save(cfg):
    store = _load_store()
    store["profiles"][PROFILE_NAME] = cfg
    store["currentProfile"] = PROFILE_NAME
    _write_store(store)


def _entry_ready(entry: dict) -> tuple[bool, str]:
    if not isinstance(entry, dict):
        return False, "profile 条目无效"
    platform = str(entry.get("platform_type") or "cticloud").strip().lower()
    endpoint = entry.get("endpoint")
    if not _nonempty(endpoint):
        return False, "缺少 endpoint"
    if platform == "clink2":
        if not _nonempty(entry.get("access_key_id")) or not _nonempty(
            entry.get("access_key_secret")
        ):
            return False, "Clink2 缺少 AccessKey"
        return True, ""
    if platform != "cticloud":
        return False, f"不支持的 platform_type: {platform}"
    if _nonempty(entry.get("token")):
        try:
            vt = int(entry.get("validate_type", 2))
        except (TypeError, ValueError):
            return False, "validate_type 无效"
        if vt == 2 and not _nonempty(entry.get("enterprise_id")):
            return False, "Token 模式缺少 enterprise_id"
        if vt == 1 and not _nonempty(entry.get("department_id")):
            return False, "Token 模式缺少 department_id"
        return True, ""
    if _nonempty(entry.get("access_key_id")) and _nonempty(
        entry.get("access_key_secret")
    ):
        return True, ""
    return False, "cticloud 鉴权不完整（需 token 或 AK/SK）"


def _cmd_status() -> int:
    """WorkBuddy 连接态：仅认 profile「workbuddy」，避免本机其它 CLI profile 误报已连接而跳过授权页。"""
    store = _load_store()
    profiles = store.get("profiles") or {}
    if PROFILE_NAME not in profiles:
        print("未连接：尚未配置 WorkBuddy 凭证（请完成连接授权页）", file=sys.stderr)
        return 1
    ok, reason = _entry_ready(profiles[PROFILE_NAME])
    if not ok:
        print(f"未连接：{reason}", file=sys.stderr)
        return 1

    # Do not live-probe the API here. On Windows, `zenava.exe` spawns a
    # python grandchild; subprocess timeout does not kill that tree, so
    # WorkBuddy's connect spinner hangs forever on `--status`.
    # ASCII token: WorkBuddy's JS statusMatch cannot reliably match
    # Chinese "已连接" from Windows cmd.exe (GBK vs UTF-8).
    print("CONNECTED")
    return 0


def _cmd_logout() -> int:
    store = _load_store()
    profiles = store.get("profiles") or {}
    if PROFILE_NAME in profiles:
        del profiles[PROFILE_NAME]
    if store.get("currentProfile") == PROFILE_NAME:
        store["currentProfile"] = None
    store["profiles"] = profiles
    if profiles or PROFILE_PATH.exists():
        _write_store(store)
    print("已登出")
    return 0


PAGE_HTML = """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>天润连接配置</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    min-height: 100vh;
    font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
    background: #d8dbe2;
    color: #1f2329;
    display: flex;
    align-items: flex-start;
    justify-content: center;
    padding: 40px 16px 48px;
  }
  .cfg {
    width: min(520px, 100%);
    background: #fff;
    border-radius: 12px;
    padding: 22px 24px 20px;
    box-shadow: 0 16px 40px rgba(20, 24, 32, .18);
    position: relative;
  }
  .brands {
    display: flex; justify-content: center; align-items: center; gap: 12px;
    margin-bottom: 14px;
  }
  .brand-circle {
    width: 52px; height: 52px; border-radius: 50%;
    display: grid; place-items: center;
    box-shadow: 0 0 0 3px #fff, 0 6px 16px rgba(20,24,32,.08);
    overflow: hidden;
  }
  .wb { background: transparent; }
  .wb img { width: 52px; height: 52px; display: block; }
  .zenava { background: #6038f8; }
  .zenava img {
    width: 52px; height: 52px; display: block;
    object-fit: contain; padding: 12px 6px;
  }
  h1 { font-size: 16px; font-weight: 650; margin-bottom: 8px; }
  .cfg-desc { color: #8c8c8c; font-size: 12px; line-height: 1.7; margin-bottom: 16px; }
  .field { display: flex; flex-direction: column; gap: 6px; margin-bottom: 14px; }
  .field > span { font-size: 13px; }
  .field input, .field select {
    height: 36px; border: 1px solid #d9d9d9; border-radius: 6px;
    padding: 0 12px; font-size: 13px; color: #1f2329; background: #fff;
    outline: none; width: 100%;
  }
  .field input:focus, .field select:focus { border-color: #3d6bff; }
  .hint { color: #8c8c8c; font-size: 12px; line-height: 1.6; margin-top: -8px; margin-bottom: 14px; }
  .howto {
    background: #f7f8fa; border-radius: 8px; padding: 10px 12px; margin-bottom: 14px;
    color: #646a73; font-size: 12px; line-height: 1.7;
  }
  .howto b { color: #1f2329; font-weight: 600; }
  .row-hidden { display: none !important; }
  .save {
    width: 100%; height: 40px; border: 0; border-radius: 8px;
    background: #3d6bff; color: #fff; font-size: 14px; cursor: pointer;
  }
  .save:hover { background: #2f5cf0; }
  .save:disabled { background: #a8b8f0; cursor: not-allowed; }
  #msg { margin-top: 12px; font-size: 13px; color: #dc2626; white-space: pre-wrap; line-height: 1.6; }
  #msg.ok { color: #16a34a; }
</style>
</head>
<body>
<div class="cfg">
  <div class="brands">
    <div class="brand-circle wb" aria-label="WorkBuddy">
      <img src="/assets/workbuddy-logo.svg" alt="WorkBuddy" />
    </div>
    <div class="brand-circle zenava" aria-label="Zenava">
      <img src="/assets/zenava-logo.png" alt="ZENAVA" />
    </div>
  </div>
  <h1>天润连接配置</h1>
  <p class="cfg-desc">配置您需要连接到的目标企业信息，后续若需要连接其他企业，直接在对话内输入相关指令即可</p>
  <form id="cfg-form">
    <input type="hidden" name="state" value="__STATE__">

    <label class="field">
      <span>选择平台</span>
      <select id="platform_type" name="platform_type">
        <option value="clink2">Clink2</option>
        <option value="cticloud">CtiCloud</option>
      </select>
    </label>

    <label class="field">
      <span>API 地址</span>
      <input id="endpoint" name="endpoint" type="text" value="https://api-bj.clink.cn" required>
    </label>
    <p class="hint" id="endpoint_hint">北京示例：https://api-bj.clink.cn；上海示例：https://api-sh.clink.cn</p>

    <div id="cticloud_auth_mode_wrap" class="row-hidden">
      <label class="field">
        <span>鉴权方式</span>
        <select id="auth_mode" name="auth_mode">
          <option value="token">token</option>
          <option value="ak-sk">aksk</option>
        </select>
      </label>
    </div>

    <div id="token_fields" class="row-hidden">
      <label class="field">
        <span>验证方式</span>
        <select id="validate_type" name="validate_type">
          <option value="2">企业编号验证</option>
          <option value="1">部门编号验证</option>
        </select>
      </label>
      <label class="field">
        <span>企业编号（enterpriseId）</span>
        <input id="enterprise_id" name="enterprise_id" type="text" placeholder="企业编号验证时必填">
      </label>
      <label class="field">
        <span>部门编号（departmentId）</span>
        <input id="department_id" name="department_id" type="text" placeholder="部门编号验证时必填">
      </label>
      <label class="field">
        <span>Token</span>
        <input id="token" name="token" type="password" placeholder="请输入token" autocomplete="off">
      </label>
      <div class="howto">
        <div><b>获取方式</b></div>
        <div>联系销售或技术支持获取</div>
      </div>
    </div>

    <div id="aksk_fields">
      <label class="field">
        <span>AccessKeyId</span>
        <input id="access_key_id" name="access_key_id" type="text" placeholder="请输入" autocomplete="off">
      </label>
      <label class="field">
        <span>AccessKeySecret</span>
        <input id="access_key_secret" name="access_key_secret" type="password" placeholder="请输入" autocomplete="off">
      </label>
      <div class="howto">
        <div><b>获取方式</b></div>
        <div id="aksk_howto">系统设置-安全设置-接口秘钥</div>
      </div>
      <label class="field">
        <span>Expires（秒，可选，默认 60）</span>
        <input id="expires" name="expires" type="number" min="1" max="86400" placeholder="60">
      </label>
    </div>

    <button class="save" type="submit" id="btn">保存并连接</button>
    <div id="msg"></div>
  </form>
</div>
<script>
  var platform = document.getElementById('platform_type');
  var authMode = document.getElementById('auth_mode');
  var endpoint = document.getElementById('endpoint');
  var endpointHint = document.getElementById('endpoint_hint');
  var tokenFields = document.getElementById('token_fields');
  var akskFields = document.getElementById('aksk_fields');
  var authModeWrap = document.getElementById('cticloud_auth_mode_wrap');
  var akskHowto = document.getElementById('aksk_howto');
  var defaults = {
    cticloud: 'https://api-1.cticloud.cn',
    clink2: 'https://api-bj.clink.cn'
  };
  function fillEndpoint() {
    var p = platform.value;
    if (endpoint.value === defaults.cticloud || endpoint.value === defaults.clink2 || !endpoint.value) {
      endpoint.value = defaults[p];
    }
    if (p === 'cticloud') {
      endpointHint.textContent = 'CtiCloud 示例：https://api-{region}.cticloud.cn；{region}=1 华东1区、2 华北2区、5 华东5区、6 华北6区';
      akskHowto.textContent = '联系销售或技术支持获取';
    } else {
      endpointHint.textContent = '北京示例：https://api-bj.clink.cn；上海示例：https://api-sh.clink.cn';
      akskHowto.textContent = '系统设置-安全设置-接口秘钥';
    }
  }
  function sync() {
    var p = platform.value;
    var mode = authMode.value;
    fillEndpoint();
    authModeWrap.className = p === 'cticloud' ? '' : 'row-hidden';
    var showToken = p === 'cticloud' && mode === 'token';
    var showAksk = p === 'clink2' || (p === 'cticloud' && mode === 'ak-sk');
    tokenFields.className = showToken ? '' : 'row-hidden';
    akskFields.className = showAksk ? '' : 'row-hidden';
  }
  platform.addEventListener('change', sync);
  authMode.addEventListener('change', sync);
  sync();
  document.getElementById('cfg-form').addEventListener('submit', function (e) {
    e.preventDefault();
    var btn = document.getElementById('btn');
    var msg = document.getElementById('msg');
    btn.disabled = true;
    msg.className = '';
    msg.textContent = '保存中...';
    fetch('/save', { method: 'POST', body: new URLSearchParams(new FormData(this)) })
      .then(function (r) { return r.json().catch(function () { return { ok: false, error: '响应解析失败' }; }); })
      .then(function (d) {
        if (d.ok) {
          msg.className = 'ok';
          msg.textContent = '已保存并连接，可以关闭此页面，返回 WorkBuddy 查看连接状态。';
        } else {
          msg.className = '';
          msg.textContent = d.error || '保存失败';
          btn.disabled = false;
        }
      })
      .catch(function (err) { msg.textContent = '网络错误：' + err.message; btn.disabled = false; });
  });
</script>
</body>
</html>"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _send_bytes(self, body: bytes, code=200, ctype="application/octet-stream"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _render(self, html, code=200, ctype="text/html; charset=utf-8"):
        self._send_bytes(html.encode("utf-8"), code, ctype)

    def _send_json(self, data, code):
        self._render(json.dumps(data, ensure_ascii=False), code, "application/json; charset=utf-8")

    def _serve_asset(self, name: str) -> bool:
        ctype = ALLOWED_ASSETS.get(name)
        if not ctype:
            return False
        path = ASSETS_DIR / name
        if not path.is_file():
            self._render("<h3 style='font-family:sans-serif'>资源不存在</h3>", 404)
            return True
        self._send_bytes(path.read_bytes(), 200, ctype)
        return True

    def do_GET(self):
        global STATE, STATE_USED
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path.startswith("/assets/"):
            name = parsed.path[len("/assets/") :].lstrip("/")
            if self._serve_asset(name):
                return
            self._render("<h3 style='font-family:sans-serif'>资源不存在</h3>", 404)
            return
        params = urllib.parse.parse_qs(parsed.query)
        if params.get("state", [""])[0] != STATE or STATE_USED:
            self._render(
                "<h3 style='font-family:sans-serif'>授权页无效或已过期，请在 WorkBuddy 中重新发起连接。</h3>",
                403,
            )
            return
        self._render(PAGE_HTML.replace("__STATE__", STATE))

    def do_POST(self):
        global STATE, STATE_USED, EXIT_CODE
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length).decode("utf-8")
        payload = _parse_form_body(raw, self.headers.get("Content-Type") or "")
        if payload.get("state") != STATE or STATE_USED:
            self._send_json({"ok": False, "error": "页面已过期，请重新发起连接。"}, 403)
            return
        cfg, err = _validate(payload)
        if err:
            self._send_json({"ok": False, "error": err}, 400)
            return
        try:
            _save(cfg)
        except Exception as exc:  # noqa: BLE001
            self._send_json({"ok": False, "error": "保存失败：" + str(exc)}, 500)
            return
        STATE_USED = True
        EXIT_CODE = 0
        self._send_json({"ok": True, "error": ""}, 200)
        threading.Thread(target=SERVER.shutdown, daemon=True).start()


def _serve_auth_page() -> int:
    global SERVER, STATE, EXIT_CODE
    STATE = secrets.token_urlsafe(16)
    EXIT_CODE = 1
    SERVER = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    port = SERVER.server_address[1]
    print("http://127.0.0.1:" + str(port) + "/auth?state=" + STATE, flush=True)
    timer = threading.Timer(PAGE_TTL_SECONDS, SERVER.shutdown)
    timer.daemon = True
    timer.start()
    SERVER.serve_forever()
    return EXIT_CODE


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        return _serve_auth_page()
    if args[0] in ("--status", "status"):
        return _cmd_status()
    if args[0] in ("--logout", "logout", "unauth"):
        return _cmd_logout()
    if args[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    print("未知参数：" + " ".join(args), file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
