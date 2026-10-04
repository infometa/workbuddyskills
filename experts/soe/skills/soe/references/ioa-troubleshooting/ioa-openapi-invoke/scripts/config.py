"""
ioa-openapi-invoke 配置加载（支持多客户切换）。

配置来源优先级（高 -> 低）：
1. 命令行 --config 指定的 JSON 文件
2. 环境变量 IOA_BASE_URL / IOA_SECRET_ID / IOA_SECRET_KEY 等
3. 内置占位（无效，需用户覆盖）

支持字段：
- base_url:        iOA 后台地址，例如 https://ioa.example.com:8443
- secret_id / secret_key:               明文凭证
- encrypted_secret_id / encrypted_secret_key:  机器密钥加密后的密文（优先于明文）
- verify_ssl:      是否校验 SSL 证书（私有化自签名场景常为 false），默认 false
- timeout:         HTTP 超时秒数，默认 30
- service:         签名 CredentialScope 的 service 段；私有化默认推导为 "capi"，
                   SaaS（ioa.tencentcloudapi.com）需显式设为 "ioa"
- path_prefix:     接口路径前缀，默认 "/capi"
- api_version:     X-TC-Version，默认 "2022-06-01"
"""

import json
import os
from typing import Dict, Optional, Tuple

try:
    from .crypto_utils import decrypt_credential
except ImportError:
    from crypto_utils import decrypt_credential


DEFAULT_CONFIG = {
    "base_url": "",
    "secret_id": "",
    "secret_key": "",
    "verify_ssl": False,
    "timeout": 30,
    "service": "",          # 空 => 自动从 path 推导（私有化为 capi）
    "path_prefix": "/capi",
    "api_version": "2022-06-01",
}


def _load_from_file(path: str) -> Dict:
    if not path:
        return {}
    if not os.path.isfile(path):
        raise FileNotFoundError(f"配置文件不存在: {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"配置文件必须是 JSON 对象: {path}")
    return data


def _load_from_env() -> Dict:
    env_map = {
        "base_url": "IOA_BASE_URL",
        "secret_id": "IOA_SECRET_ID",
        "secret_key": "IOA_SECRET_KEY",
        "encrypted_secret_id": "IOA_ENCRYPTED_SECRET_ID",
        "encrypted_secret_key": "IOA_ENCRYPTED_SECRET_KEY",
        "verify_ssl": "IOA_VERIFY_SSL",
        "timeout": "IOA_TIMEOUT",
        "service": "IOA_SERVICE",
        "path_prefix": "IOA_PATH_PREFIX",
        "api_version": "IOA_API_VERSION",
    }
    cfg: Dict = {}
    for key, env_name in env_map.items():
        value = os.environ.get(env_name)
        if value is None or value == "":
            continue
        if key == "verify_ssl":
            cfg[key] = value.lower() in ("1", "true", "yes", "on")
        elif key == "timeout":
            try:
                cfg[key] = int(value)
            except ValueError:
                pass
        else:
            cfg[key] = value
    return cfg


def _resolve_credential(plain: str, encrypted: str) -> str:
    if plain:
        return plain
    if encrypted:
        try:
            return decrypt_credential(encrypted)
        except Exception:
            return ""
    return ""


def load_config(config_path: Optional[str] = None) -> Dict:
    cfg = dict(DEFAULT_CONFIG)
    cfg.update(_load_from_env())
    if config_path:
        cfg.update(_load_from_file(config_path))

    final = {
        "base_url": str(cfg.get("base_url", "")).strip().rstrip("/"),
        "secret_id": _resolve_credential(
            str(cfg.get("secret_id", "")).strip(),
            str(cfg.get("encrypted_secret_id", "")).strip()),
        "secret_key": _resolve_credential(
            str(cfg.get("secret_key", "")).strip(),
            str(cfg.get("encrypted_secret_key", "")).strip()),
        "verify_ssl": bool(cfg.get("verify_ssl", False)),
        "timeout": int(cfg.get("timeout", 30) or 30),
        "service": str(cfg.get("service", "")).strip(),
        "path_prefix": "/" + str(cfg.get("path_prefix", "/capi")).strip().strip("/"),
        "api_version": str(cfg.get("api_version", "2022-06-01")).strip(),
    }
    return final


def validate_config(config: Dict) -> Tuple[bool, str]:
    if not config.get("base_url"):
        return False, "缺少 base_url"
    if not config["base_url"].startswith("http"):
        return False, "base_url 必须以 http(s):// 开头"
    if not config.get("secret_id"):
        return False, "缺少 secret_id（或解密失败）"
    if not config.get("secret_key"):
        return False, "缺少 secret_key（或解密失败）"
    return True, "ok"
