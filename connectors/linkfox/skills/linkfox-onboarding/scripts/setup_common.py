#!/usr/bin/env python3
"""linkfox-onboarding 共享模块：网关调用、二维码渲染、会话目录、JWT 解码、套餐/订单接口。

被 list_plans.py / create_order.py / query_order.py 复用。
不直接被命令行调用。自包含，不依赖 _shared/linkfox_paths.py。
"""

from __future__ import annotations

import io
import json
import os
import secrets
import sys
import tempfile
import time
import urllib.error
from urllib.request import urlopen, Request

# Windows 控制台默认 GBK 编码，无法输出 QR ASCII 中的 Unicode 块字符与中文。
# 把 stdout/stderr 重配置为 utf-8，保证所有脚本输出可被管道与 JSON 正确处理。
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8")
        except Exception:
            pass


_SESSION_ROOT_CACHE: str | None = None


def _get_agent_base() -> str:
    """网关基础地址：env LINKFOX_AGENT_API_URL 优先，回退 LINKFOX_TOOL_GATEWAY（其它 linkfox-* skill 用的名），缺省回退正式地址。"""
    return (os.environ.get("LINKFOX_AGENT_API_URL") or os.environ.get("LINKFOX_TOOL_GATEWAY") or "https://tool-gateway.linkfox.com").rstrip("/")


def _get_api_key() -> str:
    """读 API key：LINKFOX_AGENT_API_KEY 优先，回退 LINKFOXAGENT_API_KEY（老客户用的无下划线版本）。"""
    return os.environ.get("LINKFOX_AGENT_API_KEY") or os.environ.get("LINKFOXAGENT_API_KEY") or ""


def _get_login_base() -> str:
    """登录 + 用户信息接口域名（send_verify_code / login v3 / userInfo）。"""
    return (os.environ.get("LINKFOX_LOGIN_API_URL") or "https://api.linkfox.com").rstrip("/")


def _get_agent_user_base() -> str:
    """团队 token 接口域名（getApiToken / generateApiToken）。"""
    return (os.environ.get("LINKFOX_AGENT_USER_API_URL") or "https://agent-api.linkfox.com").rstrip("/")


# 登录链路用的固定 uid header（解出来是 {"a_id":"6a22c8b05bc916a","d_id":""}，实测可用）
_LOGIN_FIXED_UID = os.environ.get("LINKFOX_LOGIN_FIXED_UID") or "eyJhX2lkIjoiNmEyMmM4YjA1YmM5MTZhIiwiZF9pZCI6IiJ9"


def build_uid_header(access_token: str, user_id: str) -> str:
    """构造 userInfo / getApiToken 用的 uid header 值。

    规则（实测）：base64url( 紧凑 JSON {"a_id":<token JWT header.a>, "d_id":<userId>} )。
    """
    import base64
    parts = (access_token or "").split(".")
    a_id = ""
    if len(parts) >= 2:
        try:
            hdr = json.loads(base64.urlsafe_b64decode(parts[1] + "=" * (-len(parts[1]) % 4)))
            a_id = hdr.get("a", "")
        except Exception:
            pass
    obj = {"a_id": a_id, "d_id": str(user_id)}
    raw = json.dumps(obj, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(raw).decode()


def login_post(path: str, body: dict, *, with_uid: bool = False, uid: str = "") -> dict:
    """登录链路 POST：调 api.linkfox.com。

    Args:
        path: 路径，如 /user/v1/web/login
        body: 请求体 dict
        with_uid: 是否带固定 uid header（v3 login 必需，v1 可选）
        uid: 自定义 uid 值，空则用 _LOGIN_FIXED_UID

    用 requests 而非 urllib：生产 WAF 对 urllib 的请求特征敏感，会拒 uid。
    """
    try:
        import requests
    except ImportError:
        return {"_error": "缺少 requests 依赖，请运行: pip install requests"}
    url = f"{_get_login_base()}{path}"
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json;charset=UTF-8",
        "Origin": "https://ai.linkfox.com",
        "Referer": "https://ai.linkfox.com/",
        "source": "ai-linkfox-web",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
    }
    if with_uid:
        headers["uid"] = uid or _LOGIN_FIXED_UID
    try:
        r = requests.post(url, json=body or {}, headers=headers, timeout=30)
        return r.json()
    except Exception as e:
        return {"_error": str(e), "_body": getattr(e, 'response', None) and e.response.text[:500] if hasattr(e, 'response') else ""}


def agent_user_post(path: str, body: dict, *, access_token: str, user_id: str, group_id: str = "") -> dict:
    """团队 token 链路 POST：调 agent-api.linkfox.com。

    header 必带 authorization/uid/tid/source。用 requests（同 login_post 理由）。
    """
    try:
        import requests
    except ImportError:
        return {"_error": "缺少 requests 依赖，请运行: pip install requests"}
    url = f"{_get_agent_user_base()}{path}"
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json;charset=UTF-8",
        "Origin": "https://ai.linkfox.com",
        "Referer": "https://ai.linkfox.com/",
        "source": "agent-linkfox-web",
        "authorization": access_token,
        "uid": build_uid_header(access_token, user_id),
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
    }
    if group_id:
        headers["tid"] = group_id
    try:
        r = requests.post(url, json=body or {}, headers=headers, timeout=30)
        return r.json()
    except Exception as e:
        return {"_error": str(e), "_body": getattr(e, 'response', None) and e.response.text[:500] if hasattr(e, 'response') else ""}


def _linkfox_root() -> str:
    """选择可写的 linkfox 根目录。

    优先级：
      1. $ACPX_WORKSPACES 第一个路径下的 linkfox/
      2. 当前工作目录下的 linkfox/
      3. ~/linkfox/
      4. $TMPDIR/linkfox/
    只读路径自动回退。进程内缓存。
    """
    global _SESSION_ROOT_CACHE
    if _SESSION_ROOT_CACHE:
        return _SESSION_ROOT_CACHE
    candidates = []
    acpx = (os.environ.get("ACPX_WORKSPACES") or "").strip()
    if acpx:
        acpx = acpx.split(os.pathsep)[0].strip()
        if acpx:
            candidates.append(os.path.join(acpx, "linkfox"))
    candidates.append(os.path.join(os.getcwd(), "linkfox"))
    candidates.append(os.path.join(os.path.expanduser("~"), "linkfox"))
    candidates.append(os.path.join(tempfile.gettempdir(), "linkfox"))
    for root in candidates:
        try:
            os.makedirs(root, exist_ok=True)
            probe = os.path.join(root, ".write_probe")
            with open(probe, "w", encoding="utf-8") as f:
                f.write("")
            os.remove(probe)
        except OSError:
            continue
        _SESSION_ROOT_CACHE = os.path.abspath(root)
        return _SESSION_ROOT_CACHE
    _SESSION_ROOT_CACHE = os.path.abspath(candidates[-1])
    return _SESSION_ROOT_CACHE


def session_dir() -> str:
    """返回当前会话目录：<root>/<YYYY-MM-DD>/<HHMMSS-6hex>，自动创建。"""
    ts = time.time()
    date_str = time.strftime("%Y-%m-%d", time.localtime(ts))
    env_sid = os.environ.get("SESSION_ID")
    sid = env_sid.strip() if env_sid else (
        time.strftime("%H%M%S", time.localtime(ts)) + "-" + secrets.token_hex(3)
    )
    path = os.path.join(_linkfox_root(), date_str, sid)
    os.makedirs(path, exist_ok=True)
    return path


def _stderr_tag() -> str:
    return "[real]"


def gateway_post(path: str, body: dict) -> dict:
    """POST {LINKFOX_AGENT_API_URL}{path}，body 为 dict，返回 {errcode, data} 信封或裸 dict。

    Raises:
        RuntimeError: 鉴权失败（401）、计费不足（402）、无权限（403）、其它非 2xx。
    """
    base = _get_agent_base()
    url = f"{base}{path}"
    api_key = _get_api_key()

    last_exc: Exception = RuntimeError("未知错误")
    body_bytes = json.dumps(body or {}).encode()
    for attempt in range(3):
        if attempt:
            time.sleep(1 << (attempt - 1))  # 1s, 2s
        req = Request(
            url,
            method="POST",
            data=body_bytes,
            headers={
                "Content-Type": "application/json",
                "Authorization": api_key,
            },
        )
        try:
            with urlopen(req, timeout=30) as resp:
                raw = resp.read().decode()
            return json.loads(raw)
        except urllib.error.HTTPError as e:
            status = e.code
            raw = e.read().decode()[:300]
            if status == 401:
                raise RuntimeError(f"鉴权失败（401），请检查 LINKFOX_AGENT_API_KEY 或 LINKFOXAGENT_API_KEY：{raw}")
            if status == 402:
                raise RuntimeError(f"积分余额不足（402），请充值：{raw}")
            if status == 403:
                raise RuntimeError(f"无权限（403）：{raw}")
            last_exc = RuntimeError(f"HTTP {status}: {raw}")
            if status not in (408, 429, 500, 502, 503, 504):
                raise last_exc
        except Exception as e:
            last_exc = RuntimeError(f"网关请求失败: {e}")
            print(f"{_stderr_tag()} gateway_post attempt {attempt+1}/3 失败: {e}", file=sys.stderr)
    raise last_exc


def gateway_get(path: str) -> dict:
    """GET 版本，语义与 gateway_post 对齐。"""
    base = _get_agent_base()
    url = f"{base}{path}"
    api_key = _get_api_key()

    last_exc: Exception = RuntimeError("未知错误")
    for attempt in range(3):
        if attempt:
            time.sleep(1 << (attempt - 1))
        req = Request(url, method="GET", headers={"Authorization": api_key})
        try:
            with urlopen(req, timeout=30) as resp:
                raw = resp.read().decode()
            return json.loads(raw)
        except urllib.error.HTTPError as e:
            status = e.code
            raw = e.read().decode()[:300]
            if status == 401:
                raise RuntimeError(f"鉴权失败（401）：{raw}")
            if status == 402:
                raise RuntimeError(f"积分余额不足（402）：{raw}")
            if status == 403:
                raise RuntimeError(f"无权限（403）：{raw}")
            last_exc = RuntimeError(f"HTTP {status}: {raw}")
            if status not in (408, 429, 500, 502, 503, 504):
                raise last_exc
        except Exception as e:
            last_exc = RuntimeError(f"网关请求失败: {e}")
            print(f"{_stderr_tag()} gateway_get attempt {attempt+1}/3 失败: {e}", file=sys.stderr)
    raise last_exc


def render_qr(qr_content: str, session_dir_path: str) -> dict:
    """把 qr_content 渲染成本地 PNG + ASCII 字符串。

    用同目录下的 `_qrgen.py` 做纯 Python 实现（byte mode + ECC-L + 手写 PNG），
    stdlib 已经够用，**不再依赖 qrcode / pillow**——避免 onboarding 场景在没
    这两个包的机器上直接崩掉。

    Returns:
        {"png_path": str, "ascii_qr": str}
        编码失败（如 qr_content 为空 / 超出 v40 容量）时返回带 error 字段的 dict。
    """
    if not isinstance(qr_content, str) or not qr_content:
        return {"png_path": None, "ascii_qr": None, "error": "qr_content 为空"}
    try:
        from _qrgen import render as _render_qr  # 同目录模块
    except ImportError as e:
        err = f"加载内置 _qrgen.py 失败: {e}"
        print(f"{_stderr_tag()} render_qr: {err}", file=sys.stderr)
        return {"png_path": None, "ascii_qr": None, "error": err}

    os.makedirs(session_dir_path, exist_ok=True)
    ts_us = int(time.time() * 1_000_000)
    png_path = os.path.join(session_dir_path, f"qr-{ts_us}.png")
    try:
        r = _render_qr(qr_content, png_path=png_path, ascii_invert=True)
    except Exception as e:
        err = f"生成二维码失败: {e}"
        print(f"{_stderr_tag()} render_qr: {err}", file=sys.stderr)
        return {"png_path": None, "ascii_qr": None, "error": err}
    return {"png_path": r.get("png_path"), "ascii_qr": r.get("ascii", "")}


def decode_jwt_uid() -> dict:
    """解码 LINKFOX_AGENT_API_KEY（或回退 LINKFOXAGENT_API_KEY）的 JWT payload，返回 payload dict。

    Returns:
        {"sid","uid","name","type","role","refresh","extend","exp"} 等
        失败返回空 dict。
    """
    import base64
    key = _get_api_key()
    parts = key.split(".")
    if len(parts) < 2:
        return {}
    try:
        payload_b64 = parts[1] + "=" * (-len(parts[1]) % 4)
        return json.loads(base64.urlsafe_b64decode(payload_b64))
    except Exception as e:
        print(f"{_stderr_tag()} decode_jwt_uid 失败: {e}", file=sys.stderr)
        return {}


def fetch_user_info() -> dict:
    """调 GET /account/currentByAPI 拿当前用户信息。

    Returns:
        {"isTeamUser","nickName","phoneNum","userId","id",...}
    Raises:
        RuntimeError: 网关或业务错误。
    """
    body = gateway_get("/account/currentByAPI")
    errcode = body.get("errcode")
    if errcode not in (None, 200):
        raise RuntimeError(f"currentByAPI 业务错误: {body}")
    return body  # 字段直接在顶层（无 data 信封）


def fetch_packages(package_type: int) -> list:
    """调 POST /package/getByTypeByAPI 拿套餐列表。

    Args:
        package_type: 1 个人 / 5 个人积分加购 / 7 团队 / 8 团队积分加购
    Returns:
        packageList 数组，每项含 packageId/packageName/packagePrice/creditAmount 等
    Raises:
        RuntimeError: 网关或业务错误。
    """
    body = gateway_post("/package/getByTypeByAPI", {"packageType": package_type})
    errcode = body.get("errcode")
    if errcode not in (None, 200):
        raise RuntimeError(f"getByTypeByAPI 业务错误: {body}")
    return body.get("packageList", []) or []


def normalize_package(p: dict) -> dict:
    """把后端 package 字段归一化为我们 spec 的 plan 字段。

    过滤：packagePrice=0 的免费版不返回。
    支付方式：接口未返回，写死 wechat/alipay。
    """
    if float(p.get("packagePrice", 0) or 0) == 0:
        return None  # 免费版过滤掉
    ext = {}
    try:
        ext = json.loads(p.get("extJson", "{}")) if p.get("extJson") else {}
    except Exception:
        pass
    return {
        "plan_id": p.get("packageId", ""),
        "name": p.get("packageName", ""),
        "price": p.get("packagePrice", 0),
        "price_string": p.get("packagePriceString", ""),
        "original_price": p.get("originalPrice", 0),
        "original_price_string": p.get("originalPriceString", ""),
        "currency": "CNY",
        "credits": p.get("creditAmount", 0),
        "validity_period": p.get("validityPeriod", ""),
        "validity_period_type": p.get("validityPeriodType", ""),
        "description": p.get("description", ""),
        "is_recommend": bool(ext.get("isRecommend", False)),
        "logo_url": ext.get("logo", ""),
        "features": ext.get("features", []),
        "available_methods": ["wechat", "alipay"],
        "_raw": p,  # 保留原始字段供调试
    }


PAY_METHOD_MAP = {
    "wechat": "WX_PAY",
    "alipay": "ALI_PAY",
}


def create_order_real(plan_id: str, pay_method: str) -> dict:
    """调真实下单接口（个人或团队自动分流）。

    Args:
        plan_id: 套餐 ID（如 pkg_basic、pkg_team_basic）
        pay_method: wechat / alipay（脚本内转为 WX_PAY/ALI_PAY）
    Returns:
        归一化后的订单 dict：{order_id, qr_content, pay_url, pay_price, state, time_left, ...}
    Raises:
        RuntimeError: 网关或业务错误；ValueError: pay_method 非法。
    """
    if pay_method not in PAY_METHOD_MAP:
        raise ValueError(f"不支持的支付方式 {pay_method}，仅支持 wechat/alipay")
    pay_type = PAY_METHOD_MAP[pay_method]

    # 拿用户信息：isTeamUser + currentGroupId
    user = fetch_user_info()
    is_team = bool(user.get("isTeamUser"))
    group_id = user.get("currentGroupId", "")

    # memberId = JWT uid
    payload = decode_jwt_uid()
    member_id = payload.get("uid", "")
    if not member_id:
        raise RuntimeError("无法从 JWT 解出 uid，请检查 LINKFOX_AGENT_API_KEY 或 LINKFOXAGENT_API_KEY")

    body = {
        "packageId": plan_id,
        "payType": pay_type,
        "payDeviceType": "PC",
        "memberId": member_id,
        "groupId": group_id,
    }
    path = "/order/createTeamOrderByAPI" if is_team else "/order/createByAPI"
    print(f"[real] 下单 path={path} isTeamUser={is_team} memberId={member_id[:20]}... groupId={group_id}", file=sys.stderr)
    resp = gateway_post(path, body)
    errcode = resp.get("errcode")
    if errcode not in (None, 200):
        raise RuntimeError(f"下单业务错误: {resp}")

    # 归一化字段
    return {
        "order_id": resp.get("orderId", ""),
        "qr_content": resp.get("payQrcode") or resp.get("payUrl", ""),
        "qr_url": None,  # 接口不返回图片 URL，脚本本地生成 PNG
        "pay_url": resp.get("payUrl", ""),
        "pay_price": resp.get("payPrice", ""),
        "original_price": resp.get("originalPrice", ""),
        "discount_price": resp.get("discountPrice", ""),
        "state": resp.get("state", ""),
        "time_left": resp.get("timeLeft", 0),
        "expire_date": resp.get("expireDate", ""),
        "trade_no": resp.get("tradeNo", ""),
        "product": resp.get("product", ""),
        "pay_type": resp.get("payType", ""),
        "_raw": resp,
    }


def query_order_real(order_id: str) -> dict:
    """调真实订单查询接口 POST /order/getByAPI。

    Returns:
        {order_id, status, paid_at, state, pay_price, time_left, ...}
    Raises:
        RuntimeError: 网关或业务错误。
    """
    body = {"orderId": order_id}
    resp = gateway_post("/order/getByAPI", body)
    errcode = resp.get("errcode")
    if errcode not in (None, 200):
        raise RuntimeError(f"查询订单业务错误: {resp}")

    # state 枚举映射到我们的 status
    state = resp.get("state", "")
    state_map = {
        "wait_pay": "unpaid",
        "paid": "paid",
        "finished": "paid",  # 后端支付完成并已开通权益的终态
        "expire": "expired",
        "expired": "expired",
        "cancel": "cancelled",
        "cancelled": "cancelled",
    }
    status = state_map.get(state, "unknown")

    return {
        "order_id": order_id,
        "status": status,
        "state": state,  # 保留原始 state
        "paid_at": resp.get("payDate") or None,
        "pay_price": resp.get("payPrice", ""),
        "time_left": resp.get("timeLeft", 0),
        "expire_date": resp.get("expireDate", ""),
        "trade_no": resp.get("tradeNo", ""),
        "product": resp.get("product", ""),
        "_raw": resp,
    }
