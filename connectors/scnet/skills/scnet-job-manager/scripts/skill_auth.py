"""Read SCNet's WorkBuddy OAuth token and prepare credentials for this process."""

import base64
import hashlib
import hmac
import http.client
import json
import math
import os
from pathlib import Path
import time
from urllib.parse import urlencode, urlsplit

from constant import USERINFO_URL


class SkillAuthError(RuntimeError):
    """An error safe to display without exposing tokens or keys."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def _read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError("Expected a JSON object")
    return value


def _find_token_record() -> tuple[Path, dict, str, dict]:
    """Prefer SCNet's name and URL, then accept one uniquely matching URL."""
    try:
        config_dir = os.getenv("WORKBUDDY_CONFIG_DIR") or os.getenv("CODEBUDDY_CONFIG_DIR")
        root = Path(config_dir).expanduser() if config_dir else Path.home() / ".workbuddy"
        config_path = Path(__file__).resolve().parents[3] / "mcp.json"
        # WorkBuddy may copy only the skill directory into connectors/skills.
        if not config_path.is_file():
            config_path = root / "connectors-marketplace" / "connectors" / "scnet" / "mcp.json"
        config = _read_json(config_path)
        server_url = config["mcpServers"]["scnet"]["url"]
        if not isinstance(server_url, str) or not server_url:
            raise ValueError
        specified = os.getenv("SCNET_WORKBUDDY_CREDENTIALS_FILE")
        if specified:
            paths = [Path(specified).expanduser()]
        else:
            paths = sorted((root / "connectors").glob("*/.credentials.v3.json"))
        exact_matches = []
        url_matches = []
        unreadable = False
        for path in paths:
            try:
                store = _read_json(path)
                records = store.get("mcpOAuth", {})
                if not isinstance(records, dict):
                    raise ValueError
            except (OSError, ValueError):
                unreadable = True
                continue
            for key, record in records.items():
                if isinstance(record, dict) and record.get("serverUrl") == server_url:
                    match = (path, store, key, record)
                    url_matches.append(match)
                    if record.get("serverName") == "scnet":
                        exact_matches.append(match)
        matches = exact_matches or url_matches
        if len(matches) > 1:
            raise SkillAuthError("AMBIGUOUS_TOKEN", "发现多条 SCNet 认证记录。请用 SCNET_WORKBUDDY_CREDENTIALS_FILE 指定当前账号的凭据文件；同一文件有重复记录时请在 WorkBuddy 中重新连接 SCNet。")
        if not matches:
            if unreadable:
                raise SkillAuthError("TOKEN_STORE_UNREADABLE", "无法读取 WorkBuddy 凭据文件，请使用运行 WorkBuddy 的同一系统用户。")
            raise SkillAuthError("TOKEN_NOT_FOUND", "未找到与 scnet/mcp.json 地址匹配的 WorkBuddy token，请先在 WorkBuddy 中连接并授权。")
        return matches[0]
    except SkillAuthError:
        raise
    except (OSError, ValueError, KeyError, TypeError):
        raise SkillAuthError("TOKEN_CONFIG_ERROR", "无法读取 SCNet MCP 配置或 WorkBuddy 凭据目录。") from None


def _get_access_token() -> str:
    path, store, server_key, record = _find_token_record()
    expires_at = record.get("expiresAt")
    # WorkBuddy persists Date.now() timestamps in milliseconds.
    if expires_at is not None and (
        type(expires_at) not in (int, float) or not math.isfinite(expires_at)
        or expires_at <= time.time() * 1000
    ):
        raise SkillAuthError("TOKEN_EXPIRED", "SCNet token 已过期，请在 WorkBuddy 中重新连接或完成刷新后重试。")
    try:
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        from cryptography.hazmat.primitives.kdf.hkdf import HKDF
    except ImportError:
        raise SkillAuthError("MISSING_DEPENDENCY", "缺少 cryptography，请用运行脚本的 Python 执行：python -m pip install cryptography。") from None
    try:
        header = store["encryption"]
        if (store.get("version") != 3 or header["scheme"] != "aes-256-gcm"
                or header["kdf"] != "hkdf-sha256"):
            raise ValueError
        user_id = path.parent.name
        if not user_id or user_id == "default":
            raise ValueError
        master_key = path.with_name(".master.key").read_bytes()
        salt = base64.b64decode(header["salt"], validate=True)
        if len(master_key) != 32 or len(salt) != 16:
            raise ValueError
        for value, field in ((user_id.encode("utf-8"), "userIdCheck"), (master_key, "keyCheck")):
            check = base64.b64encode(hashlib.sha256(value + salt).digest()[:16]).decode("ascii")
            if not hmac.compare_digest(check, header[field]):
                raise ValueError
        # Matches WorkBuddy OAuthCipher in the locally installed app's main/tar.js.
        key = HKDF(algorithm=hashes.SHA256(), length=32, salt=salt,
                   info=b"workbuddy-oauth-credentials-v1").derive(master_key + user_id.encode("utf-8"))
        envelope = record["accessToken"]
        iv, tag, ciphertext = (base64.b64decode(envelope[field], validate=True)
                               for field in ("iv", "tag", "ct"))
        if len(iv) != 12 or len(tag) != 16:
            raise ValueError
        aad = f"{user_id}|{server_key}|accessToken".encode("utf-8")
        token = AESGCM(key).decrypt(iv, ciphertext + tag, aad).decode("utf-8")
        if not token.strip():
            raise ValueError
        return token
    except Exception:
        # Crypto and filesystem exception messages must not expose secret values.
        raise SkillAuthError("TOKEN_DECRYPT_FAILED", "无法解密 SCNet token，请确认当前系统用户、WorkBuddy 登录账号及凭据文件一致；此实现适用于 WorkBuddy v3 凭据格式。") from None


def _fetch_userinfo(access_token: str) -> dict:
    try:
        url = urlsplit(USERINFO_URL)
        if (url.scheme not in ("http", "https") or not url.hostname
                or url.username or url.password or url.query or url.fragment):
            raise ValueError
        connection_type = http.client.HTTPSConnection if url.scheme == "https" else http.client.HTTPConnection
        connection = connection_type(url.hostname, url.port, timeout=10)
    except ValueError:
        raise SkillAuthError("INVALID_USERINFO_URL", "SCNET_USERINFO_URL 必须是不含凭据和查询参数的 HTTP(S) 地址。") from None
    try:
        # No redirects or request logging: the API carries the token in the URL.
        connection.request("GET", (url.path or "/") + "?" + urlencode({"access_token": access_token}),
                           headers={"Accept": "application/json"})
        response = connection.getresponse()
        if response.status != 200:
            raise SkillAuthError("USERINFO_HTTP_ERROR", f"获取 SCNet 认证信息失败，HTTP {response.status}。")
        raw = response.read(65537)
    except (OSError, http.client.HTTPException):
        raise SkillAuthError("USERINFO_UNAVAILABLE", "无法连接 SCNet userinfo 接口或请求超时，请检查开发环境网络。") from None
    finally:
        connection.close()
    try:
        if len(raw) > 65536:
            raise ValueError
        payload = json.loads(raw)
        # Validate the userinfo shape before interpreting absent keys. An error
        # response or invalid username must not become a key-application prompt.
        if (not isinstance(payload, dict)
                or not isinstance(payload.get("userName"), str)
                or not payload["userName"].strip()):
            raise ValueError
        if any(
            payload.get(field) is not None and not isinstance(payload[field], str)
            for field in ("ak", "sk")
        ):
            raise ValueError
        if any(payload.get(field) is None or not payload[field].strip() for field in ("ak", "sk")):
            raise SkillAuthError("ACCESS_KEYS_REQUIRED", "暂未获取到访问密钥。")
        return payload
    except (ValueError, UnicodeError):
        raise SkillAuthError("INVALID_USERINFO", "userinfo 响应必须包含非空字符串 ak、sk、userName。") from None


def get_skill_auth() -> dict[str, str]:
    """Get token, exchange for AK/SK and populate the existing process variables.

    Called internally before constructing SCNetJobClient. Never print the return
    value: it contains credentials. No token/key files are written or refreshed.
    """
    payload = _fetch_userinfo(_get_access_token())
    credentials = {"SCNET_AK": payload["ak"], "SCNET_SK": payload["sk"],
                   "SCNET_USER": payload["userName"]}
    os.environ.update(credentials)
    return credentials
