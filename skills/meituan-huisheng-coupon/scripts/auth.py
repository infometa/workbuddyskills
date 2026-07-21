#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, io
if hasattr(sys.stdout, 'buffer') and sys.stdout.encoding.lower().replace('-','') != 'utf8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
if hasattr(sys.stderr, 'buffer') and sys.stderr.encoding.lower().replace('-','') != 'utf8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
"""
huisheng-coupon-tool 内嵌认证模块 v1.0.4
基于 meituan-c-user-auth v1.0.4 内嵌，用户无需单独安装 meituan-c-user-auth。
对接 EDS Claw 短信登录接口，管理 user_token 与 device_token。

接口文档：https://km.sankuai.com/collabpage/2752893495（新版）

用法示例：
  python auth.py version-check
  python auth.py status
  python auth.py token-verify
  python auth.py send-sms --phone 13812345678
  python auth.py verify --phone 13812345678 --code 123456
  python auth.py logout
  python auth.py clear-device-token
"""

import argparse
import hashlib
import json
import random
import sys
import time
from pathlib import Path

# ── 常量 ──────────────────────────────────────────────────────────────
AUTH_KEY       = "meituan-c-user-auth"
LOCAL_VERSION  = "1.0.4"   # 内嵌版本号，与 SKILL.md 中 version 字段保持一致

# Skill 公开主页（clawhub.ai，外网可访问）
SKILL_PAGE_URL = "https://clawhub.ai/meituan-zhengchang/huisheng-coupon-tool"


def _resolve_auth_file() -> Path:
    """
    跨平台确定 Token 存储路径，优先级：
    1. 环境变量 XIAOMEI_AUTH_FILE（显式指定，最高优先级，适合沙箱/CI/非小美搭档 Agent）
    2. ~/.xiaomei-workspace/auth_tokens.json（macOS / Linux / Windows 统一路径）

    设计说明：
    - 统一使用 ~/.xiaomei-workspace/，无论 macOS、Linux 还是 Windows（Git Bash 下 Path.home()
      均能正确解析为用户主目录）。
    - 不再区分 Linux 有点/无点目录分支，避免不同 Agent 行为不一致。
    - 非小美搭档 Agent（如 Friday Claw、第三方 Agent）可通过 XIAOMEI_AUTH_FILE 环境变量
      指定自定义路径，实现完全隔离（如 /tmp/xxx_auth.json）。
    """
    import os

    # 优先读环境变量（适合沙箱/CI/其他 Agent 自定义路径）
    env_path = os.environ.get("XIAOMEI_AUTH_FILE")
    if env_path:
        return Path(env_path)

    # 统一使用 ~/.xiaomei-workspace/，跨平台一致
    return Path.home() / ".xiaomei-workspace" / "auth_tokens.json"


AUTH_FILE = _resolve_auth_file()

# ── 日志路径 ──────────────────────────────────────────────────────────
import tempfile as _tempfile
_AUTH_LOG_FILE = Path(_tempfile.gettempdir()) / "huisheng" / "huisheng_auth.log"

# 线上外网域名
BASE_URL = "https://peppermall.meituan.com"

# 接口路径
SMS_CODE_GET_PATH    = "/eds/claw/login/sms/code/get"
SMS_CODE_VERIFY_PATH = "/eds/claw/login/sms/code/verify"
TOKEN_VERIFY_PATH    = "/eds/claw/login/token/verify"



# ── 版本检测 ──────────────────────────────────────────────────────────

def _parse_version(text: str) -> str:
    """从文本中提取 version: "x.y.z" 格式的版本号"""
    import re
    m = re.search(r'version:\s*["\']([^"\']+)["\']', text)
    return m.group(1) if m else ""


def cmd_version_check(remote_version: str = ""):
    """
    检查本地 Skill 版本，与 clawhub.ai 上的远程版本对比。

    设计说明：
    远程版本需由调用方（小美）通过 WebFetch 访问 clawhub.ai 页面后，
    将解析到的版本字符串通过 --remote 参数传入。
    若未传入 --remote，则仅展示本地版本信息。
    """
    result = {
        "local_version": LOCAL_VERSION,
        "skill_page_url": SKILL_PAGE_URL,
    }

    remote_ver = remote_version.strip() if remote_version else ""

    if not remote_ver:
        # 未传入远程版本，仅展示本地版本
        result["remote_version"] = None
        result["up_to_date"] = None
        result["message"] = f"当前本地版本：{LOCAL_VERSION}"
        result["hint"] = f"如需检测最新版本，请访问：{SKILL_PAGE_URL}"
    elif remote_ver == LOCAL_VERSION:
        result["remote_version"] = remote_ver
        result["up_to_date"] = True
        result["message"] = f"✅ 当前已是最新版本 {LOCAL_VERSION}"
    else:
        result["remote_version"] = remote_ver
        result["up_to_date"] = False
        result["message"] = (
            f"⚠️ 发现新版本！本地：{LOCAL_VERSION}，最新：{remote_ver}。"
            f"建议前往以下地址更新以获取最新能力：{SKILL_PAGE_URL}"
        )
        result["upgrade_url"] = SKILL_PAGE_URL

    print(json.dumps(result, ensure_ascii=False))


# ── 设备ID生成 ────────────────────────────────────────────────────────

def generate_device_token(seed: str) -> str:
    """
    生成设备唯一标识（device_token）。
    算法：MD5（seed + 毫秒时间戳 + 0~1000随机整数）
    - 登录时（有完整手机号）：seed = 手机号
    - token-verify 时（无完整手机号）：seed = phone_masked（脱敏号）
    device_token 与设备绑定，一旦生成后永不覆盖。
    """
    ts_ms = int(time.time() * 1000)
    rand_int = random.randint(0, 1000)
    raw = f"{seed}{ts_ms}{rand_int}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


# ── 存储操作 ──────────────────────────────────────────────────────────

def load_auth() -> dict:
    if AUTH_FILE.exists():
        with open(AUTH_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def _now() -> str:
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _get_device_token() -> str:
    """从 auth_tokens.json 读取 device_token，读取失败返回空字符串"""
    try:
        return load_auth().get(AUTH_KEY, {}).get("device_token", "")
    except Exception:
        return ""


def _xor_encrypt(data: str, ai_scene: str) -> str:
    """XOR 加密，返回带 flag 前缀的 hex 字符串。
    前缀 '1:' = key 用 sha256(device_token + aiScene)
    前缀 '0:' = 降级，key 用 sha256(aiScene)
    flag 保证解密时能还原正确的 key，不依赖运行时环境。
    与 issue.py 加密方式完全一致。
    """
    device_token = _get_device_token()
    if device_token:
        seed = device_token + ai_scene
        flag = "1"
    else:
        seed = ai_scene
        flag = "0"
    key_bytes = hashlib.sha256(seed.encode()).digest()
    data_bytes = data.encode("utf-8")
    result = bytes(b ^ key_bytes[i % 32] for i, b in enumerate(data_bytes))
    return flag + ":" + result.hex()


def _load_ai_scene() -> str:
    """从 config.json 读取 aiScene，读取失败返回空字符串"""
    try:
        config_path = Path(__file__).parent / "config.json"
        with open(config_path, encoding="utf-8") as f:
            return json.load(f).get("aiScene", "")
    except Exception:
        return ""


def write_auth_log(entry: dict):
    """将鉴权操作记录加密后追加写入日志文件，任何异常静默跳过。
    加密方式与 issue.py 的 write_log 完全一致：sha256(device_token + aiScene)
    """
    try:
        _AUTH_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        raw = json.dumps(entry, ensure_ascii=False)
        ai_scene = _load_ai_scene()
        encrypted = _xor_encrypt(raw, ai_scene) if ai_scene else raw
        with open(_AUTH_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(encrypted + "\n")
    except Exception:
        pass


def save_auth(data: dict):
    import os, stat
    AUTH_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(AUTH_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    # 仅当前用户可读写（0600），防止其他用户读取 Token
    try:
        os.chmod(AUTH_FILE, stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass  # Windows 不支持 chmod，静默跳过


def get_token_data() -> dict:
    return load_auth().get(AUTH_KEY, {})


def save_token_data(token_data: dict):
    auth = load_auth()
    auth[AUTH_KEY] = token_data
    save_auth(auth)


def logout_token_data():
    """
    退出登录：仅将 user_token 置为空字符串。
    device_token 及其他字段保持不变，以保留设备唯一标识。
    规则：任何情况下 device_token 存在且不为空时，均不得修改或删除。
    """
    auth = load_auth()
    entry = auth.get(AUTH_KEY, {})
    entry["user_token"] = ""          # 置空，表示已退出登录
    auth[AUTH_KEY] = entry
    save_auth(auth)


# ── 命令：status（本地检查，不调用接口）────────────────────────────────

def cmd_status():
    """仅检查本地存储的 Token 是否存在，不调用远程接口，不做本地过期校验"""
    token_data = get_token_data()
    user_token = token_data.get("user_token")
    device_token = token_data.get("device_token")
    phone_masked = token_data.get("phone_masked", "")

    if user_token:
        write_auth_log({"time": _now(), "action": "status", "result": "has_token", "phone_masked": phone_masked})
        print(json.dumps({
            "success": True,
            "valid": True,
            "user_token": user_token,
            "device_token": device_token,
            "phone_masked": phone_masked,
            "check_mode": "local"
        }, ensure_ascii=False))
    else:
        write_auth_log({"time": _now(), "action": "status", "result": "no_token", "phone_masked": phone_masked})
        print(json.dumps({
            "success": True,
            "valid": False,
            "reason": "no_token",
            "device_token": device_token,
            "phone_masked": phone_masked,
            "check_mode": "local"
        }, ensure_ascii=False))


# ── 命令：token-verify（调用远程接口校验）─────────────────────────────

def cmd_token_verify():
    """调用 /eds/claw/login/token/verify 验证 Token 有效性"""
    import httpx

    token_data = get_token_data()
    user_token = token_data.get("user_token")
    phone_masked = token_data.get("phone_masked", "")

    # 规则2：token-verify 时检查 device_token，不存在则用 phone_masked 生成并持久化
    existing_device_token = token_data.get("device_token")
    if not existing_device_token:
        seed = phone_masked if phone_masked else "unknown"
        new_device_token = generate_device_token(seed)
        token_data["device_token"] = new_device_token
        save_token_data(token_data)
        existing_device_token = new_device_token

    if not user_token:
        write_auth_log({
            "time": _now(),
            "action": "token-verify",
            "request": {"url": BASE_URL + TOKEN_VERIFY_PATH, "phone_masked": phone_masked},
            "result": {"success": False, "error": "NO_TOKEN", "reason": "no_token"},
        })
        print(json.dumps({
            "success": True,
            "valid": False,
            "reason": "no_token",
            "device_token": existing_device_token,
            "phone_masked": phone_masked,
            "check_mode": "remote"
        }, ensure_ascii=False))
        return

    url = BASE_URL + TOKEN_VERIFY_PATH
    log_entry = {
        "time": _now(),
        "action": "token-verify",
        "request": {
            "url": url,
            "phone_masked": phone_masked,
            "token_masked": user_token[:8] + "****" if user_token else "",
        },
    }

    try:
        resp = httpx.post(
            url,
            params={"token": user_token},
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
                "X-Requested-With": "XMLHttpRequest",
            },
            timeout=10,
            verify=False
        )
        log_entry["response"] = {"http_status": resp.status_code, "body": resp.text[:500]}
        resp_data = resp.json()
        code = resp_data.get("code")

        if code == 0:
            # Token 有效
            log_entry["result"] = {"success": True, "code": 0, "valid": True}
            write_auth_log(log_entry)
            print(json.dumps({
                "success": True,
                "valid": True,
                "user_token": user_token,
                "device_token": existing_device_token,
                "phone_masked": phone_masked,
                "check_mode": "remote"
            }, ensure_ascii=False))

        elif code == 20005:
            # Token 不存在或已过期（服务端确认）
            # 规则4：只将 user_token 置为空字符串，不删除 device_token
            logout_token_data()
            log_entry["result"] = {"success": False, "code": 20005, "error": "TOKEN_EXPIRED"}
            write_auth_log(log_entry)
            print(json.dumps({
                "success": True,
                "valid": False,
                "reason": "token_expired_or_invalid",
                "device_token": existing_device_token,
                "phone_masked": phone_masked,
                "check_mode": "remote",
                "message": resp_data.get("message", "用户未登录或 Token 已过期，请重新登录")
            }, ensure_ascii=False))

        else:
            # 其他错误（如系统繁忙），不修改本地缓存
            log_entry["result"] = {"success": False, "code": code, "error": "TOKEN_VERIFY_ERROR"}
            write_auth_log(log_entry)
            print(json.dumps({
                "success": False,
                "error": "TOKEN_VERIFY_ERROR",
                "code": code,
                "message": resp_data.get("message", "Token 校验失败"),
                "check_mode": "remote"
            }, ensure_ascii=False))
            sys.exit(1)

    except Exception as e:
        log_entry["response"] = {"error": "NETWORK_ERROR", "detail": str(e)}
        log_entry["result"] = {"success": False, "error": "NETWORK_ERROR"}
        write_auth_log(log_entry)
        print(json.dumps({
            "success": False,
            "error": "NETWORK_ERROR",
            "message": str(e)
        }, ensure_ascii=False))
        sys.exit(1)


# ── 命令：send-sms ────────────────────────────────────────────────────

def cmd_send_sms(phone: str):
    """调用 /eds/claw/login/sms/code/get 发送验证码"""
    import httpx

    # 读取已有 device_token，若不存在则先生成（此时还无法用手机号生成，用 phone 即可）
    existing = get_token_data()
    existing_dt = existing.get("device_token")
    if existing_dt:
        uuid_val = existing_dt
    else:
        uuid_val = generate_device_token(phone)
        # 提前持久化：send-sms 时即锁定 device_token，避免后续 verify 再生成不同值
        existing["device_token"] = uuid_val
        existing["phone_masked"] = phone[:3] + "****" + phone[-4:]
        save_token_data(existing)

    phone_masked = phone[:3] + "****" + phone[-4:]
    url = BASE_URL + SMS_CODE_GET_PATH
    body = {
        "mobile": phone,    # 接口字段名为 mobile
        "uuid": uuid_val    # 设备唯一标识，对接接口 uuid 扩展字段
    }

    log_entry = {
        "time": _now(),
        "action": "send-sms",
        "request": {
            "url": url,
            "phone_masked": phone_masked,
        },
    }

    try:
        resp = httpx.post(
            url,
            json=body,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
                "X-Requested-With": "XMLHttpRequest",
            },
            timeout=10,
            verify=False
        )
        log_entry["response"] = {"http_status": resp.status_code, "body": resp.text[:500]}
        resp_data = resp.json()
        code = resp_data.get("code")

        if code == 0:
            log_entry["result"] = {"success": True, "code": 0}
            write_auth_log(log_entry)
            print(json.dumps({
                "success": True,
                "phone_masked": phone_masked,
                "message": f"验证码已发送至手机号 {phone_masked}，请打开手机短信查看验证码，60秒内有效"
            }, ensure_ascii=False))

        elif code == 20001:
            # 手机号 Token 加密服务失败，服务端问题，稍后重试
            log_entry["result"] = {"success": False, "code": 20001, "error": "SMS_MOBILE_TOKEN_ENCRYPT_FAIL"}
            write_auth_log(log_entry)
            print(json.dumps({
                "success": False,
                "error": "SMS_MOBILE_TOKEN_ENCRYPT_FAIL",
                "code": 20001,
                "message": "短信服务暂时不可用，请稍后重试"
            }, ensure_ascii=False))
            sys.exit(1)

        elif code == 20002:
            # 频控：验证码已存在
            log_entry["result"] = {"success": False, "code": 20002, "error": "SMS_VERIFY_CODE_EXIST"}
            write_auth_log(log_entry)
            print(json.dumps({
                "success": False,
                "error": "SMS_VERIFY_CODE_EXIST",
                "code": 20002,
                "message": "短信验证码已发送，请1分钟后再试"
            }, ensure_ascii=False))
            sys.exit(1)

        elif code == 20004:
            # 手机号未注册美团
            log_entry["result"] = {"success": False, "code": 20004, "error": "CLAW_USER_NOT_REGISTERED"}
            write_auth_log(log_entry)
            print(json.dumps({
                "success": False,
                "error": "CLAW_USER_NOT_REGISTERED",
                "code": 20004,
                "message": "该手机号未注册美团，请先下载美团APP并完成注册登录"
            }, ensure_ascii=False))
            sys.exit(1)

        elif code == 20006:
            # 单手机号日限（默认5次/天）
            log_entry["result"] = {"success": False, "code": 20006, "error": "SMS_MOBILE_DAILY_LIMIT"}
            write_auth_log(log_entry)
            print(json.dumps({
                "success": False,
                "error": "SMS_MOBILE_DAILY_LIMIT",
                "code": 20006,
                "message": "该手机号今日发送短信次数已达上限，请明天再试"
            }, ensure_ascii=False))
            sys.exit(1)

        elif code == 20007:
            # 全局日限（默认1000条/天）
            log_entry["result"] = {"success": False, "code": 20007, "error": "SMS_DAILY_TOTAL_LIMIT"}
            write_auth_log(log_entry)
            print(json.dumps({
                "success": False,
                "error": "SMS_DAILY_TOTAL_LIMIT",
                "code": 20007,
                "message": "短信发送总次数已达今日上限，请明天再试"
            }, ensure_ascii=False))
            sys.exit(1)

        elif code == 20010:
            # Rhino 限流触发，需用户完成安全验证，data.redirectUrl 为跳转链接
            data = resp_data.get("data") or {}
            redirect_url = data.get("redirectUrl", "")
            log_entry["result"] = {"success": False, "code": 20010, "error": "SMS_SECURITY_VERIFY_REQUIRED", "redirect_url": redirect_url}
            write_auth_log(log_entry)
            print(json.dumps({
                "success": False,
                "error": "SMS_SECURITY_VERIFY_REQUIRED",
                "code": 20010,
                "redirect_url": redirect_url,
                "message": (
                    "需要完成安全验证后才能接收短信验证码。"
                    f"请点击以下链接完成验证：{redirect_url}。"
                    "完成验证后，系统会自动发送短信验证码，请留意手机短信。"
                ) if redirect_url else "需要完成安全验证，请稍后重试"
            }, ensure_ascii=False))
            sys.exit(1)

        else:
            log_entry["result"] = {"success": False, "code": code, "error": "SMS_SEND_FAILED"}
            write_auth_log(log_entry)
            print(json.dumps({
                "success": False,
                "error": "SMS_SEND_FAILED",
                "code": code,
                "message": resp_data.get("message", "验证码发送失败")
            }, ensure_ascii=False))
            sys.exit(1)

    except Exception as e:
        log_entry["response"] = {"error": "NETWORK_ERROR", "detail": str(e)}
        log_entry["result"] = {"success": False, "error": "NETWORK_ERROR"}
        write_auth_log(log_entry)
        print(json.dumps({
            "success": False,
            "error": "NETWORK_ERROR",
            "message": str(e)
        }, ensure_ascii=False))
        sys.exit(1)


# ── 命令：verify ──────────────────────────────────────────────────────

def cmd_verify(phone: str, code: str):
    """调用 /eds/claw/login/sms/code/verify 验证验证码，成功后写入 user_token"""
    import httpx

    phone_masked = phone[:3] + "****" + phone[-4:]

    # 读取 device_token，此时 send-sms 应已持久化，直接复用
    existing = get_token_data()
    existing_dt = existing.get("device_token")
    if existing_dt:                                   # 规则5：存在且不为空则复用
        uuid_val = existing_dt
    else:                                             # 兜底：若未经 send-sms 直接调 verify
        uuid_val = generate_device_token(phone)
        existing["device_token"] = uuid_val
        save_token_data(existing)

    url = BASE_URL + SMS_CODE_VERIFY_PATH
    body = {
        "mobile": phone,            # 接口字段名为 mobile
        "smsVerifyCode": code,      # 接口字段名为 smsVerifyCode
        "uuid": uuid_val            # 设备唯一标识，对接接口 uuid 扩展字段
    }

    log_entry = {
        "time": _now(),
        "action": "verify",
        "request": {
            "url": url,
            "phone_masked": phone_masked,
        },
    }

    try:
        resp = httpx.post(
            url,
            json=body,
            headers={
               "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
                "X-Requested-With": "XMLHttpRequest",
            },
            timeout=10,
            verify=True
        )
        log_entry["response"] = {"http_status": resp.status_code, "body": resp.text[:500]}
        resp_data = resp.json()
        resp_code = resp_data.get("code")

        if resp_code == 0:
            # 成功，从 data.token 获取 Token
            data = resp_data.get("data") or {}
            user_token = data.get("token")
            if not user_token:
                log_entry["result"] = {"success": False, "code": 0, "error": "MISSING_TOKEN"}
                write_auth_log(log_entry)
                print(json.dumps({
                    "success": False,
                    "error": "MISSING_TOKEN",
                    "message": "接口返回成功但 data.token 为空"
                }, ensure_ascii=False))
                sys.exit(1)

            device_token = uuid_val
            is_new_device = not bool(existing.get("device_token"))

            token_data = {
                "user_token": user_token,
                "device_token": device_token,
                "phone_masked": phone_masked,
                "authed_at": int(time.time())
            }
            save_token_data(token_data)

            log_entry["result"] = {"success": True, "code": 0}
            write_auth_log(log_entry)

            result = {
                "success": True,
                "user_token": user_token,
                "device_token": device_token,
                "phone_masked": phone_masked,
                "message": "认证成功，user_token 已写入"
            }
            if is_new_device:
                result["device_token_generated"] = True
                result["hint"] = "首次认证，device_token 已生成并持久化"
            print(json.dumps(result, ensure_ascii=False))

        elif resp_code == 20003:
            log_entry["result"] = {"success": False, "code": 20003, "error": "SMS_VERIFY_CODE_ERROR"}
            write_auth_log(log_entry)
            print(json.dumps({
                "success": False,
                "error": "SMS_VERIFY_CODE_ERROR",
                "code": 20003,
                "message": "短信验证码错误或已过期，请重新获取"
            }, ensure_ascii=False))
            sys.exit(1)

        elif resp_code == 20004:
            log_entry["result"] = {"success": False, "code": 20004, "error": "CLAW_USER_NOT_REGISTERED"}
            write_auth_log(log_entry)
            print(json.dumps({
                "success": False,
                "error": "CLAW_USER_NOT_REGISTERED",
                "code": 20004,
                "message": "该手机号未注册美团，请先下载美团APP并完成注册登录"
            }, ensure_ascii=False))
            sys.exit(1)

        else:
            log_entry["result"] = {"success": False, "code": resp_code, "error": "VERIFY_FAILED"}
            write_auth_log(log_entry)
            print(json.dumps({
                "success": False,
                "error": "VERIFY_FAILED",
                "code": resp_code,
                "message": resp_data.get("message", "验证失败，请重试")
            }, ensure_ascii=False))
            sys.exit(1)

    except Exception as e:
        log_entry["response"] = {"error": "NETWORK_ERROR", "detail": str(e)}
        log_entry["result"] = {"success": False, "error": "NETWORK_ERROR"}
        write_auth_log(log_entry)
        print(json.dumps({
            "success": False,
            "error": "NETWORK_ERROR",
            "message": str(e)
        }, ensure_ascii=False))
        sys.exit(1)


# ── 命令：logout ──────────────────────────────────────────────────────

def cmd_logout():
    """退出当前登录状态：仅将 user_token 置为空字符串，保留 device_token"""
    token_data = get_token_data()
    device_token = token_data.get("device_token")
    phone_masked = token_data.get("phone_masked", "")

    # 规则3+4：仅置空 user_token，device_token 保持不变
    logout_token_data()

    write_auth_log({"time": _now(), "action": "logout", "result": "success", "phone_masked": phone_masked})
    result = {
        "success": True,
        "message": "已退出登录，user_token 已清除，下次需重新验证登录",
        "device_token_preserved": bool(device_token),
        "phone_masked": phone_masked
    }
    print(json.dumps(result, ensure_ascii=False))


# ── 命令：clear-device-token ──────────────────────────────────────────

def cmd_clear_device_token():
    """清除设备标识（device_token），同时清除 user_token 和 phone_masked。
    仅在用户明确输入「清除设备标识」时调用，退出登录不触发此操作。
    """
    import os, stat
    auth = load_auth()
    entry = auth.get(AUTH_KEY, {})

    had_device_token = bool(entry.get("device_token"))
    phone_masked = entry.get("phone_masked", "")

    # 清除所有认证相关字段
    entry["user_token"] = ""
    entry["device_token"] = ""
    entry["phone_masked"] = ""
    auth[AUTH_KEY] = entry

    AUTH_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(AUTH_FILE, "w", encoding="utf-8") as f:
        json.dump(auth, f, ensure_ascii=False, indent=2)
    try:
        os.chmod(AUTH_FILE, stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass

    write_auth_log({"time": _now(), "action": "clear-device-token", "result": "success", "had_device_token": had_device_token, "phone_masked": phone_masked})
    result = {
        "success": True,
        "message": "设备标识已清除，下次登录将生成新的 device_token",
        "device_token_cleared": had_device_token
    }
    print(json.dumps(result, ensure_ascii=False))


# ── 入口 ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="美团C端用户Agent认证工具（内嵌于 huisheng-coupon-tool）")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # version-check
    p_vc = subparsers.add_parser("version-check", help="检查本地 Skill 版本，与远程广场版本对比")
    p_vc.add_argument("--remote", default="", help="从 Friday 广场获取到的远程版本号（可选）")

    # status - 本地检查
    subparsers.add_parser("status", help="本地检查 Token 是否存在")

    # token-verify - 远程校验
    subparsers.add_parser("token-verify", help="调用远程接口校验 Token 有效性")

    # send-sms
    p_sms = subparsers.add_parser("send-sms", help="发送短信验证码")
    p_sms.add_argument("--phone", required=True, help="手机号（11位）")

    # verify
    p_verify = subparsers.add_parser("verify", help="验证码核验并写入 Token")
    p_verify.add_argument("--phone", required=True, help="手机号（11位）")
    p_verify.add_argument("--code", required=True, help="6位短信验证码")

    # logout
    subparsers.add_parser("logout", help="退出登录，清除 user_token（保留 device_token）")

    # clear-device-token
    subparsers.add_parser("clear-device-token", help="清除设备标识（device_token），仅在用户明确要求时调用")

    args = parser.parse_args()

    if args.command == "version-check":
        cmd_version_check(args.remote)
    elif args.command == "status":
        cmd_status()
    elif args.command == "token-verify":
        cmd_token_verify()
    elif args.command == "send-sms":
        cmd_send_sms(args.phone)
    elif args.command == "verify":
        cmd_verify(args.phone, args.code)
    elif args.command == "logout":
        cmd_logout()
    elif args.command == "clear-device-token":
        cmd_clear_device_token()


if __name__ == "__main__":
    main()
