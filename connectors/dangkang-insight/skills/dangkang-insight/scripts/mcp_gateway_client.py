#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dangkang-insight 客户端（MCP 版）。

设计要点
--------
1. **所有业务接口都经网关 MCP 调用**：本脚本是 MCP（JSON-RPC 2.0 / streamable HTTP）
   客户端，只与 config/mcp.ini 里的网关地址通信，不直连平台 OpenAPI。
   因此**不再需要 AK/SK，也不再依赖 gmssl**（原直连版依赖国密 SM4/SM3）。
2. **参数自动取齐**：userId / customerId 走 MCP `sys-user-info`，
   ddbh / cpfwbh 走 MCP `query-order`；命令行显式传入的值优先。任一工具不可用
   （例如网关未打通登录态、返回 401）时自动降级到 config/mcp.ini 的 [business] 兜底值。
   ⚠️ 例外：`nsrsbh` / `nsrmc`（**检测对象**）**不做自动兜底**——发起检测的命令 1 / 6
   缺任一项会直接报错中止，必须由用户在对话里确认后显式传入。允许（并鼓励）把
   `sys-user-info` 的「当前管理企业」作为**候选**先摆给用户选，禁止的只是**未经用户确认
   直接拿它发起检测**的越权行为（见 resolve_enterprise）。
3. **为什么还要这个脚本**（既然助手能直接调 MCP 工具）：
   a. 扫码轮询（2.2，3 秒一次、最长数分钟）与报告轮询（1.3，30 秒一次、最长 20 分钟）
      需要几十次串行调用，交给助手逐次调用不现实；脚本内循环一次命令搞定。
   b. 二维码内联渲染需要把接口 PNG 重编码成 196×196 的 1bit 迷你 PNG（见下），
      这一步必须由代码完成，助手无法可靠地逐字转抄 2 KB 的 base64。
4. 纯标准库实现，无需 pip 安装任何东西。

命令
----
  types    列出当前用户可选的检测类型（订单中的商品服务） 参数: [czrId] [cpxdm]
  cpxdms   列出平台支持的全部报告类型（cpxdm 全量清单，静态表，无需联网）
  info     取当前用户信息（sys-user-info，用于排查登录态）
  order    查询订单（query-order）   参数: [czrId] [cpxdm]
  1  发送短信验证码（接口1.1）     参数: '<企业信息JSON>'
  2  上传验证码登录（接口1.2）     参数: <nsrsbh> <taskId> <smsCode>
  3  轮询授权状态及报告（接口1.3） 参数: <nsrsbh> [轮询间隔秒=30] [最大等待秒=1200]
  4  申请付费报告（接口1.4）       参数: <nsrsbh> <zeroOrderNo> <chargeOrderNo> <zeroYwjcjlbh> <contractId> [productId] [productAttrUnique]
  5  获取风险检测概览（接口1.5）   参数: <nsrsbh> <ywjcjlbh>
  6  取码并出内联卡片（接口2.1）   参数: '<企业信息JSON>' [守护最大等待秒=240]
  7  前台等待扫码终态（接口2.2）   参数: [最大等待秒=240]

检测类型选择（两个维度，别混淆）
--------------------------------
- **cpfwbh（商品服务代码）** = 用户视角的「检测类型」，也是平台「所属服务」下拉的取值，
  决定本次检测走哪个商品服务（谁的次数被扣）。取值来自订单 spfwList[].cpfwDm。
- **cpxdm（产品线代码）** = 平台口径的「报告类型」，对应侧边栏检测类型 tab / 字典
  DM_FK_CPXDM，例如 02=财税综合合规检测、28=尽职调查、30=电商合规。一个 cpfwbh 可能
  覆盖多个 cpxdm（如 ACSY_2001 → 01,02,03）。

标准选型流程（对齐平台「继续生成」弹窗：报告类型 → 所属订单 → 所属服务）：
  ① 不确定有哪些报告类型 → 先跑 `cpxdms` 看全量清单；
  ② `types <czrId> <cpxdm>` 查该报告类型下真正可用的服务（订单+剩余次数）；
     `types <czrId>` 不带 cpxdm 则列出全部可用服务；
  ③ 让用户挑一种，把选中的 **cpfwbh** 放进企业信息 JSON，例如：
     '{"nsrsbh":"9111...","nsrmc":"某企业","ssdq":"2100","cpfwbh":"ACSY_2001"}'
  ④ 不传 cpfwbh 时脚本按「MFSY 免费版 → ACSY_2001 通用版 → ANSY_1001 包年 → 第一条」
     的优先级自动挑一个默认订单，仅作兜底。所选 cpfwbh 必须与 ddbh 对应；若该类型
     只有唯一订单，脚本会自动配对 ddbh。

⚠️ 能力边界：MCP/OpenAPI 通道（/org/auth/riskDet/*）的入参 DTO **没有 cpxdm 字段**，
   所以「报告类型」只能用于筛选与展示，**传不进检测接口**；实际生效的是 cpfwbh。
   若要让检测接口也吃到 cpxdm，需要后端在 AuthOrderLoginRequestDTO /
   AuthOrderQrcodeLoginRequestDTO 补字段并在 OrgAuthController 里 setCpxdm。

企业信息JSON示例（命令1，账号密码登录）：
  '{"nsrsbh":"9111...","nsrmc":"某企业","ssdq":"2100","sflx":"FDDBR","gryhm":"登录账号","gryhmm":"登录密码","sjhm":"接收短信手机号","cpfwbh":"ACSY_2001"}'
企业信息JSON示例（命令6，扫码登录）：
  '{"nsrsbh":"9111...","nsrmc":"某企业","ssdq":"2100","cpfwbh":"ACSY_2001"}'
（userId / customerId / ddbh / qdbm / sqInfo 均可省略，脚本自动补齐）

⚠️ 但 **nsrsbh / nsrmc / ssdq 不可省略**：它们是「检测对象」，必须由用户在对话里明确给出或确认。
   脚本不会拿 sys-user-info 的「当前管理企业」来兜底；命令 1 / 6 缺 nsrsbh 或 nsrmc 会直接报
   `[错误] 未明确指定检测对象…` 并中止。原因：账号名下有某家企业 ≠ 用户本次要检测它
   ——可以把这家企业作为**候选**提示给用户选择，但必须经用户确认后再显式传入。
"""

import base64
import configparser
import json
import os
import re
import struct
import subprocess
import sys
import time
from collections import namedtuple
import urllib.error
import urllib.parse
import urllib.request
import zlib

_HERE = os.path.dirname(os.path.abspath(__file__))
_CONFIG_PATH = os.path.join(_HERE, "..", "config", "mcp.ini")
_LOGS_DIR = os.path.join(_HERE, "..", "logs")

# ===== 读取网关配置（config/mcp.ini）=====
# 兼容三种情况：
#   1) config/mcp.ini 存在 → 正常读取；
#   2) 缺失但 config/mcp.example.md 存在 → 自动从模板生成一份默认配置
#      （内置生产网关地址、令牌留空），保证「市场下载后开箱可用」；
#   3) 都缺失 → 用内置默认值兜底，仅当连默认地址也没有时才真正报错。
_DEFAULT_MCP_URL = "https://lxyq.cssyq.com.cn/ggyw/mcp"
_cfg = configparser.ConfigParser()
if not _cfg.read(_CONFIG_PATH, encoding="utf-8"):
    _tpl = os.path.join(_HERE, "..", "config", "mcp.example.md")
    if os.path.exists(_tpl):
        try:
            with open(_tpl, encoding="utf-8") as f:
                _tpl_text = f.read()
            # 模板里真正生效的是 [mcp]/[business] 段落，直接解析即可
            _cfg.read_string(_tpl_text)
            os.makedirs(os.path.dirname(_CONFIG_PATH), exist_ok=True)
            with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
                f.write(_tpl_text)
        except Exception:
            _cfg = configparser.ConfigParser()
    if not _cfg.has_section("mcp"):
        # 兜底：用内置默认值，确保首次运行不因缺文件而崩溃
        _cfg["mcp"] = {"url": _DEFAULT_MCP_URL, "timeout": "60"}

MCP_URL = (_cfg["mcp"].get("url") or _DEFAULT_MCP_URL).strip()
MCP_TIMEOUT = int((_cfg["mcp"].get("timeout") or "60").strip() or 60)

# ---- 令牌与自动续期 ----
# access_token 会过期（网关签发 expires_in=43200 秒 ≈ 12h），refresh_token 可无损换新。
# 令牌缓存写在 config/.token.json（已在 .gitignore 中），刷新后自动落盘，下次运行直接复用。
MCP_TOKEN_CFG = (_cfg["mcp"].get("access_token") or "").strip()
MCP_REFRESH_CFG = (_cfg["mcp"].get("refresh_token") or "").strip()
MCP_CLIENT_ID = (_cfg["mcp"].get("client_id") or "").strip()
TOKEN_FILE = os.path.abspath(os.path.join(_HERE, "..", "config", ".token.json"))
# 网关把 yfp-ggyw 系接口转发到内网服务时可能丢登录态（表现为 401 账号未登录）。
# 打开此项后，这类调用会改用「同一个 Bearer 令牌直连平台公网域」兜底。
MCP_DIRECT_FALLBACK = (_cfg["mcp"].get("direct_fallback") or "").strip().lower() \
    in ("1", "true", "yes", "on")
PLATFORM_BASE = (_cfg["mcp"].get("platform_base")
                 or "https://lxyq.cssyq.com.cn").strip().rstrip("/")

_TOKENS = {"access": "", "refresh": "", "client_id": "", "expires_at": 0.0, "loaded": False}

_B = _cfg["business"] if _cfg.has_section("business") else {}
DDBH = (_B.get("ddbh") or "").strip() if _B else ""
CPFWBH = (_B.get("cpfwbh") or "").strip() if _B else ""
QDBM = ((_B.get("qdbm") or "1033").strip() if _B else "1033") or "1033"
PRODUCT_ID = (_B.get("product_id") or "").strip() if _B else ""
PRODUCT_ATTR_UNIQUE = (_B.get("product_attr_unique") or "").strip() if _B else ""

# 授权协议书内容（base64，后端仅校验非空）
SQ_TEXT = ("本人已阅读并同意《乐享云企财税合规检测服务授权协议》，"
           "授权平台依法获取电子税务局涉税数据用于合规检测。")
SQ_INFO = base64.b64encode(SQ_TEXT.encode()).decode()

# 网关侧工具名（改网关配置时同步改这里）
TOOL = {
    "user_info": "sys-user-info",
    "order": "query-order",
    "qrcode": "riskdet-get-qrcode",
    "scan": "riskdet-scan-code",
    "sms_send": "riskdet-sms-code-send",
    "sms_upload": "riskdet-sms-code-upload",
    "query_status": "riskdet-query-status",      # 接口1.3（新增工具）
    "report_apply": "riskdet-report-apply",      # 接口1.4（新增工具）
    "overview": "riskdet-risk-overview",         # 接口1.5（新增工具）
}


# ============================================================
# MCP 客户端（JSON-RPC 2.0 over streamable HTTP）
# ============================================================

_ID = [0]


def _next_id() -> int:
    _ID[0] += 1
    return _ID[0]


def _log_line(line: str):
    """把每次 MCP 调用写入 logs/YYYY-MM-DD.log（按日期归集）。"""
    os.makedirs(_LOGS_DIR, exist_ok=True)
    path = os.path.join(_LOGS_DIR, time.strftime("%Y-%m-%d") + ".log")
    with open(path, "a", encoding="utf-8") as f:
        f.write("[%s] %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), line))


def _token_endpoint() -> str:
    """推导 OAuth 令牌端点：.../ggyw/mcp → .../ggyw/oauth2/token。"""
    explicit = (_cfg["mcp"].get("token_endpoint") or "").strip()
    if explicit:
        return explicit
    if "/mcp" in MCP_URL:
        return MCP_URL.split("/mcp", 1)[0] + "/oauth2/token"
    return MCP_URL.rsplit("/", 1)[0] + "/oauth2/token"


def _read_token_cache() -> dict:
    try:
        with open(TOKEN_FILE, encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def _save_token_cache():
    try:
        os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)
        tmp = TOKEN_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump({
                "access_token": _TOKENS["access"],
                "refresh_token": _TOKENS["refresh"],
                "client_id": _TOKENS["client_id"],
                "expires_at": _TOKENS["expires_at"],
                "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            }, f, ensure_ascii=False, indent=2)
        os.replace(tmp, TOKEN_FILE)
    except Exception as exc:
        _log_line("令牌缓存写入失败：%s" % exc)


def load_tokens():
    """确定当前使用的 access/refresh token：环境变量 > 本地缓存 > config/mcp.ini。"""
    if _TOKENS["loaded"]:
        return
    _TOKENS["loaded"] = True
    cache = _read_token_cache()
    env_access = (os.environ.get("DKI_MCP_TOKEN") or "").strip()
    env_refresh = (os.environ.get("DKI_MCP_REFRESH_TOKEN") or "").strip()
    _TOKENS["access"] = env_access or (cache.get("access_token") or "") or MCP_TOKEN_CFG
    _TOKENS["refresh"] = env_refresh or (cache.get("refresh_token") or "") or MCP_REFRESH_CFG
    _TOKENS["client_id"] = (cache.get("client_id") or "") or MCP_CLIENT_ID
    try:
        _TOKENS["expires_at"] = float(cache.get("expires_at") or 0)
    except Exception:
        _TOKENS["expires_at"] = 0.0


def refresh_access_token(verbose: bool = True) -> bool:
    """用 refresh_token 换一枚新的 access_token（并落盘）。成功返回 True。

    注意：刷新令牌必须带上「当初签发它的 client_id」，否则网关报
    invalid_grant: refresh_token 与客户端不匹配。
    """
    load_tokens()
    if not _TOKENS["refresh"]:
        _log_line("令牌刷新失败：本地没有 refresh_token"
                  "（.token.json 缺失 且 mcp.ini/环境变量未配置）→ 必须重新授权一次")
        if verbose:
            print("[令牌] 没有 refresh_token，无法自动续期（请重新授权一次）。")
        return False
    if not _TOKENS["client_id"]:
        _log_line("令牌刷新失败：缺少 client_id"
                  "（刷新令牌必须带上当初签发它的客户端 ID）→ 必须重新授权一次")
        if verbose:
            print("[令牌] 缺少 client_id，无法自动续期"
                  "（刷新令牌必须带上签发它的客户端 ID）。")
        return False

    data = urllib.parse.urlencode({
        "grant_type": "refresh_token",
        "refresh_token": _TOKENS["refresh"],
        "client_id": _TOKENS["client_id"],
    }).encode()
    req = urllib.request.Request(_token_endpoint(), data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    req.add_header("Accept", "application/json")
    try:
        resp = urllib.request.urlopen(req, timeout=MCP_TIMEOUT)
        raw = resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        _log_line("令牌刷新失败 http=%s | %s" % (e.code, raw[:300]))
        if verbose:
            print("[令牌] 自动续期失败（http=%s）：%s" % (e.code, raw[:200]))
        return False
    except Exception as e:
        _log_line("令牌刷新异常 %s: %s" % (type(e).__name__, e))
        if verbose:
            print("[令牌] 自动续期异常：%s: %s" % (type(e).__name__, e))
        return False

    try:
        d = json.loads(raw)
    except Exception:
        if verbose:
            print("[令牌] 自动续期失败：响应无法解析 %s" % raw[:200])
        return False

    new_access = d.get("access_token")
    if not new_access:
        if verbose:
            print("[令牌] 自动续期失败：%s" % (d.get("error_description")
                                          or d.get("error") or raw[:200]))
        return False

    _TOKENS["access"] = new_access
    if d.get("refresh_token"):
        _TOKENS["refresh"] = d["refresh_token"]
    try:
        _TOKENS["expires_at"] = time.time() + float(d.get("expires_in") or 0)
    except Exception:
        _TOKENS["expires_at"] = 0.0
    _save_token_cache()
    if verbose:
        print("[令牌] 已自动续期，有效期 %s 秒" % d.get("expires_in"))
    return True


def ensure_token(verbose: bool = True) -> bool:
    """调用前的兜底：本地没有任何令牌时先尝试刷新一次。"""
    load_tokens()
    if _TOKENS["access"]:
        return True
    return refresh_access_token(verbose)


def save_tokens_from_response(d: dict):
    """把一次授权码/刷新流程拿到的令牌落盘（供外部脚本复用）。"""
    load_tokens()
    if d.get("access_token"):
        _TOKENS["access"] = d["access_token"]
    if d.get("refresh_token"):
        _TOKENS["refresh"] = d["refresh_token"]
    if d.get("client_id"):
        _TOKENS["client_id"] = d["client_id"]
    try:
        _TOKENS["expires_at"] = time.time() + float(d.get("expires_in") or 0)
    except Exception:
        _TOKENS["expires_at"] = 0.0
    _save_token_cache()


# ------------------------------------------------------------
# 直连平台兜底（仅当网关丢登录态时启用；仍复用同一枚 Bearer 令牌）
# ------------------------------------------------------------

_PLATFORM_ROUTES = {
    "sys-user-info": ("GET", "/ggyw/sys/user/info", None),
    "riskdet-get-qrcode": ("POST", "/ggyw/org/auth/riskDet/getQrcode", (
        "ddbh", "cpfwbh", "qdbm", "customerId", "userId", "nsrsbh", "nsrmc",
        "ssdq", "sqInfo")),
    "riskdet-scan-code": ("POST", "/ggyw/org/auth/riskDet/scanCode", (
        "taskId", "nsrsbh")),
    "riskdet-sms-code-send": ("POST", "/ggyw/org/auth/riskDet/smsCodeSend", (
        "ddbh", "cpfwbh", "qdbm", "customerId", "userId", "nsrsbh", "nsrmc",
        "ssdq", "gryhm", "gryhmm", "sflx", "sjhm", "dljgsh", "sqInfo")),
    "riskdet-sms-code-upload": ("POST", "/ggyw/org/auth/riskDet/smsCodeUpload", (
        "taskId", "nsrsbh", "smsCode")),
    "riskdet-report-apply": ("POST", "/ggyw/org/auth/report/apply", (
        "nsrsbh", "userId", "customerId", "zeroOrderNo", "chargeOrderNo",
        "zeroYwjcjlbh", "contractId", "productId", "productAttrUnique")),
}


def _json_to_md(title: str, obj) -> str:
    """把平台 JSON 渲染成与网关模板同构的「- **键**: 值」Markdown。"""
    lines = ["# " + title]
    if not isinstance(obj, dict):
        lines.append("> %s" % str(obj)[:500])
        return "\n".join(lines)

    if obj.get("code") is not None:
        lines.append("- **code**: %s" % obj.get("code"))
    if obj.get("msg") is not None:
        lines.append("- **msg**: %s" % obj.get("msg"))

    flat = obj.get("data")
    if not isinstance(flat, dict):
        flat = obj.get("user") if isinstance(obj.get("user"), dict) else None
    if isinstance(flat, dict):
        for k, v in flat.items():
            if isinstance(v, str) and v.startswith("data:image"):
                lines.append("- **%s**：" % k)
                lines.append("")
                lines.append("![电子税务局登录二维码](%s)" % v)
                lines.append("")
            elif isinstance(v, list):
                for it in v:
                    lines.append("- **%s**: %s" % (k, it))
            elif isinstance(v, (str, int, float)) and v is not None:
                lines.append("- **%s**: %s" % (k, v))
    elif flat is not None:
        lines.append("- **data**: %s" % flat)

    for k, v in obj.items():
        if k in ("code", "msg", "data", "user"):
            continue
        if isinstance(v, (str, int, float)) and v is not None:
            lines.append("- **%s**: %s" % (k, v))
    return "\n".join(lines)


def direct_platform_call(tool: str, arguments: dict):
    """绕过网关，用同一枚 Bearer 令牌直连平台公网域。返回 (is_error, text) 或 None（不支持）。"""
    route = _PLATFORM_ROUTES.get(tool)
    if not route:
        return None
    method, path, fields = route
    ensure_token(verbose=False)
    if not _TOKENS["access"]:
        return None

    url = PLATFORM_BASE + path
    data = None
    if method == "POST":
        body = {k: (arguments or {}).get(k, "") for k in (fields or ())}
        data = json.dumps(body, ensure_ascii=False).encode()
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", "Bearer " + _TOKENS["access"])
    req.add_header("Accept", "application/json")
    if method == "POST":
        req.add_header("Content-Type", "application/json")
    try:
        resp = urllib.request.urlopen(req, timeout=MCP_TIMEOUT)
        raw = resp.read().decode("utf-8", "replace")
        status = resp.status
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        status = e.code
    except Exception as e:
        return True, "直连平台异常：%s: %s" % (type(e).__name__, e)

    try:
        obj = json.loads(raw)
    except Exception:
        return True, "直连平台 http=%s 响应无法解析：%s" % (status, raw[:300])

    _log_line("直连平台 ← %s | http=%s" % (tool, status))
    title = "平台直连结果（%s）" % tool
    return False, _json_to_md(title, obj)


def _shrink(obj, limit: int = 160):
    """递归截断超长字符串（如二维码 base64），避免日志膨胀。"""
    if isinstance(obj, dict):
        return {k: _shrink(v, limit) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_shrink(v, limit) for v in obj]
    if isinstance(obj, str) and len(obj) > limit:
        return obj[:60] + "...(长度%d，已截断)" % len(obj)
    return obj


def _post_mcp(tool: str, arguments: dict, timeout: int = None):
    """发一次 MCP tools/call，返回 (payload, http_status, raw)。"""
    body = json.dumps({
        "jsonrpc": "2.0", "id": _next_id(), "method": "tools/call",
        "params": {"name": tool, "arguments": arguments or {}},
    }, ensure_ascii=False).encode()

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }
    load_tokens()
    if _TOKENS["access"]:
        headers["Authorization"] = "Bearer " + _TOKENS["access"]

    req = urllib.request.Request(MCP_URL, data=body, method="POST")
    for k, v in headers.items():
        req.add_header(k, v)

    try:
        resp = urllib.request.urlopen(req, timeout=timeout or MCP_TIMEOUT)
        raw = resp.read().decode("utf-8", "replace")
        status = resp.status
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        status = e.code
    except Exception as e:  # 网络异常绝不上抛，转为结构化错误，避免轮询线程静默死亡
        return None, 0, "%s: %s" % (type(e).__name__, e)

    payload = None
    # streamable HTTP 可能返回 SSE（text/event-stream）或单个 JSON
    if raw.lstrip().startswith("event:") or "data:" in raw[:64]:
        for line in raw.splitlines():
            line = line.strip()
            if line.startswith("data:"):
                chunk = line[5:].strip()
                if not chunk:
                    continue
                try:
                    cand = json.loads(chunk)
                except Exception:
                    continue
                if isinstance(cand, dict) and ("result" in cand or "error" in cand):
                    payload = cand
    if payload is None:
        try:
            payload = json.loads(raw)
        except Exception:
            payload = None
    return payload, status, raw


def _is_auth_failure(payload, status, raw) -> bool:
    """判断是否为「令牌缺失/过期」类失败（可用 refresh_token 自救）。"""
    if status == 401 and "账号未登录" not in (raw or ""):
        return True
    txt = raw or ""
    if "invalid_token" in txt or "missing or expired token" in txt:
        return True
    if isinstance(payload, dict) and payload.get("error"):
        err = json.dumps(payload["error"], ensure_ascii=False)
        if "invalid_token" in err or "unauthorized" in err or "route_gone" in err:
            return True
    return False


def _is_login_loss(text) -> bool:
    """是否属于「网关转发到 yfp-ggyw 时丢了平台登录态」。"""
    t = text or ""
    return "账号未登录" in t


def _try_direct(tool: str, arguments: dict, original_text: str):
    """网关丢登录态时改走平台直连兜底；返回 (is_err, text, rpc) 或 None。"""
    if not MCP_DIRECT_FALLBACK:
        return None
    if not _is_login_loss(original_text) or tool not in _PLATFORM_ROUTES:
        return None
    print("[提示] 网关丢登录态（%s），改用平台直连兜底。" % tool)
    res = direct_platform_call(tool, arguments)
    if not res or res[0]:
        return None
    _log_line("直连兜底 ✓ %s" % tool)
    return False, res[1], {"_direct": True}


def mcp_call(tool: str, arguments: dict, timeout: int = None):
    """调用网关 MCP 工具，返回 (is_error: bool, text: str, rpc: dict)。

    text 是工具响应模板渲染出来的 Markdown 文本；解析见 parse_md()。
    - 令牌过期（401 invalid_token）→ 自动用 refresh_token 续期后重试一次；
    - 网关丢登录态（401 账号未登录）→ 开启 direct_fallback 时走平台直连兜底。
    """
    _log_line("MCP → %s | args=%s"
              % (tool, json.dumps(_shrink(arguments or {}), ensure_ascii=False)))

    load_tokens()
    if not _TOKENS["access"]:
        ensure_token(verbose=True)
    elif _TOKENS["expires_at"] and time.time() >= _TOKENS["expires_at"] - 60:
        refresh_access_token(verbose=True)

    payload, status, raw = _post_mcp(tool, arguments, timeout)

    # ① 令牌过期 → 自动续期后重试一次
    if _is_auth_failure(payload, status, raw):
        _log_line("MCP ! %s | 鉴权失败，尝试自动续期" % tool)
        if refresh_access_token(verbose=True):
            payload, status, raw = _post_mcp(tool, arguments, timeout)

    if payload is None:
        if status == 0:
            _log_line("MCP ✗ %s | 网络异常 %s" % (tool, raw))
            fb = _try_direct(tool, arguments, raw)
            return fb if fb else (True, raw, {"_err": raw})
        _log_line("MCP ✗ %s | http=%s | 无法解析响应: %s" % (tool, status, raw[:400]))
        text = "http=%s 响应无法解析：%s" % (status, raw[:400])
        fb = _try_direct(tool, arguments, text)
        return fb if fb else (True, text, {"_raw": raw})

    if payload.get("error"):
        err = payload["error"]
        _log_line("MCP ✗ %s | jsonrpc error=%s"
                  % (tool, json.dumps(err, ensure_ascii=False)))
        text = "JSON-RPC 错误：%s" % json.dumps(err, ensure_ascii=False)
        fb = _try_direct(tool, arguments, text)
        return fb if fb else (True, text, payload)

    result = payload.get("result") or {}
    is_error = bool(result.get("isError"))
    parts = []
    for c in result.get("content") or []:
        if c.get("type") == "text":
            parts.append(c.get("text") or "")
        elif c.get("type") == "image":
            parts.append("[image content: mimeType=%s, len=%d]"
                         % (c.get("mimeType"), len(c.get("data") or "")))
    text = "\n".join(parts)

    _log_line("MCP ← %s | isError=%s | %s"
              % (tool, is_error, json.dumps(_shrink(text), ensure_ascii=False)))

    if is_error:
        fb = _try_direct(tool, arguments, text)
        if fb:
            return fb
    return is_error, text, payload


# ============================================================
# 工具响应（Markdown「- **键**: 值」格式）解析
# ============================================================

_KV_RE = re.compile(r"^\s*[-*]\s*\*\*([^*]+?)\*\*\s*[:：]\s*(.*?)\s*$")
_QR_RE = re.compile(r"!\[[^\]]*\]\(\s*(data:image/png;base64,[A-Za-z0-9+/=\s]+?)\s*\)")
# 网关也会以 image_blob_ref（指向宿主本地 blob 文件的 JSON）返回二维码，
# 形如 ![alt]({"type":"image_blob_ref","blob_id":"...","mime":"image/png",
#              "size":1533,"blob_path":"C:\\Users\\...\\xxx.png"})
# 这种形态不是 data URI，_QR_RE 匹配不到，必须单独解析出 blob_path 再读文件。
_QR_BLOB_RE = re.compile(
    r"!\[[^\]]*\]\(\s*(\{.*?\"type\"\s*:\s*\"image_blob_ref\".*?\})\s*\)", re.S)


def _extract_blob_path(text: str) -> str:
    """从 image_blob_ref 片段中取出 blob_path（去掉 JSON 转义），取不到返回 ''。"""
    m = _QR_BLOB_RE.search(text or "")
    if not m:
        return ""
    try:
        obj = json.loads(m.group(1))
    except Exception:
        # JSON 解析失败时退化为正则抠 blob_path
        pm = re.search(r"\"blob_path\"\s*:\s*\"((?:[^\"\\]|\\.)*)\"", m.group(1), re.S)
        if not pm:
            return ""
        try:
            return json.loads("\"%s\"" % pm.group(1))
        except Exception:
            return pm.group(1).replace("\\\\", "\\")
    path = obj.get("blob_path") or ""
    return path if isinstance(path, str) else ""


def _norm(v: str) -> str:
    """去掉值尾部的括号说明，只留主值。'0000（获取成功…）' → '0000'。"""
    if not v:
        return ""
    for sep in ("（", "("):
        if sep in v:
            v = v.split(sep, 1)[0]
    return v.strip()


def parse_md(text: str):
    """把渲染后的 Markdown 解析成 {键: 值}；同名键聚合为列表放在 _multi 里。"""
    fields, multi = {}, {}
    for line in (text or "").splitlines():
        m = _KV_RE.match(line)
        if not m:
            continue
        key = m.group(1).strip()
        val = m.group(2).strip()
        multi.setdefault(key, []).append(_norm(val))
        fields.setdefault(key, _norm(val))
    qr = _QR_RE.search(text or "")
    if qr:
        fields["qrcode"] = qr.group(1).replace("\n", "").replace("\r", "")
    else:
        # 网关以 image_blob_ref 返回时，qrcode 不是 data URI，而是本地 blob 文件路径。
        blob_path = _extract_blob_path(text or "")
        if blob_path:
            fields["qrcode_blob_path"] = blob_path
    fields["_multi"] = multi
    return fields


def fv(fields: dict, *keys, default=""):
    """按顺序取第一个非空字段值。"""
    for k in keys:
        v = fields.get(k)
        if v:
            return v
    return default


def flist(fields: dict, key: str):
    return list((fields.get("_multi") or {}).get(key) or [])


def is_ok_code(code: str) -> bool:
    return str(code).strip() in ("0000", "0", "200")


# ============================================================
# 参数自动取齐（sys-user-info + query-order）
# ============================================================

_ACCOUNT_CACHE = {}


def fetch_user_info(verbose: bool = True):
    """MCP sys-user-info → {userId, customerId, nsrsbh, nsrmc, username}。失败返回 {}。"""
    if "user" in _ACCOUNT_CACHE:
        return _ACCOUNT_CACHE["user"]
    is_err, text, _ = mcp_call(TOOL["user_info"], {})
    fields = parse_md(text)
    info = {}
    if not is_err:
        info = {
            "userId": fv(fields, "userId"),
            "customerId": fv(fields, "zhid", "customerId"),
            "nsrsbh": fv(fields, "companyTaxNo", "纳税人识别号"),
            "nsrmc": fv(fields, "companyName", "纳税人名称"),
            "username": fv(fields, "username"),
        }
    if verbose and not info.get("userId"):
        print("[警告] 经 MCP 取用户信息失败（tools/call %s）：%s"
              % (TOOL["user_info"], (text or "").strip().replace("\n", " ")[:200]))
        print("       将改用命令行传入值 / config/mcp.ini [business] 兜底值。")
    _ACCOUNT_CACHE["user"] = info
    return info


_ORDER_CACHE = {}

# 一条「订单下的商品服务」= 用户视角的一个可选检测类型。
# 字段名与 query-order 返回的服务明细一一对应：
#   ddbh     订单编号            cpfwDm   商品服务代码(cpfwbh)，即检测类型载体
#   cpfwmc   商品服务名称（平台 UI「所属服务」下拉显示的就是它）
#   cpxdm    产品线代码（01/02/03… 多个用逗号分隔，决定报告归类）
#   cpfwlxDm 商品服务类型（1=按年，0=按次）
#   ddyxqz   订单有效期止          ddmc     订单名称（平台 UI「所属订单」下拉显示它）
#   gmcs     购买次数             sycs     当月剩余可用次数（≤0 时后端不会返回该服务）
#   jczt     数据采集状态（01=采集中 02=采集成功 03=采集失败）
OrderSvc = namedtuple(
    "OrderSvc",
    "ddbh cpfwDm cpfwmc cpxdm cpfwlxDm ddyxqz ddmc gmcs sycs jczt")


def fetch_order(czrId: str, verbose: bool = True, cpxdm: str = ""):
    """MCP query-order → [OrderSvc, ...]（订单下的可用检测类型清单）。

    cpxdm 为「报告类型/产品线」过滤（可逗号分隔，空=全部）——与平台「继续生成」
    弹窗的第一级下拉一致（报告类型 → 所属订单 → 所属服务）。
    同一 (ddbh, cpfwDm) 会去重（包年订单可能返回上百条同码明细）。失败返回 []。
    """
    ckey = (czrId, str(cpxdm or "").strip())
    if ckey in _ORDER_CACHE:
        return _ORDER_CACHE[ckey]
    args = {}
    if czrId:
        args["czrId"] = czrId
    if cpxdm:
        args["cpxdm"] = cpxdm
    is_err, text, _ = mcp_call(TOOL["order"], args)
    items, cur = [], {}
    seen = set()
    sidx = -1          # 当前正在补全明细的服务在 items 中的下标
    for line in (text or "").splitlines():
        s = line.strip()
        # 新订单块："## 订单：<订单名>"
        mh = re.match(r"^##\s*订单[：:]\s*(.+?)\s*$", s)
        if mh:
            cur = {"ddmc": mh.group(1)}
            sidx = -1
            continue
        m = _KV_RE.match(s)
        if m:
            key, val = m.group(1).strip(), _norm(m.group(2))
            if key.startswith("订单编号"):
                cur["ddbh"] = val
            elif key.startswith("订单有效期"):
                cur["ddyxqz"] = val.split("至")[-1].strip() if "至" in val else val
            continue
        # 商品服务明细行：- **名称**（商品服务代码(cpfwbh) MFSY_0000｜产品线 05｜类型 1）
        m2 = re.match(r"^\s*[-*]\s*\*\*(.+?)\*\*\s*（(.*?)）\s*$", s)
        if m2 and cur.get("ddbh"):
            name, tail = m2.group(1), m2.group(2)
            dm = re.search(r"商品服务代码\(cpfwbh\)\s*([A-Za-z0-9_\-]+)", tail) \
                or re.search(r"cpfwDm[^A-Za-z0-9_\-]*([A-Za-z0-9_\-]+)", tail)
            if not dm:
                continue
            cpfwDm = dm.group(1)
            key = (cur["ddbh"], cpfwDm)
            if key in seen:      # 同一订单同一服务码只保留一条（包年 100 条明细）
                sidx = -1
                continue
            seen.add(key)
            pl = re.search(r"产品线\s*([\d,]+)", tail)
            tp = re.search(r"类型\s*(\d)", tail)
            items.append(OrderSvc(
                cur["ddbh"], cpfwDm, name,
                pl.group(1) if pl else "",
                tp.group(1) if tp else "",
                cur.get("ddyxqz", ""), cur.get("ddmc", ""),
                "", "", "",
            ))
            sidx = len(items) - 1
            continue
        # 服务明细的后续行（缩进在服务条目之下）：购买/剩余次数、数据采集状态
        if sidx >= 0:
            if "剩余可用次数" in s or "购买次数" in s:
                g = re.search(r"购买次数\s*[:：]\s*(\d+)", s)
                y = re.search(r"剩余可用次数\s*[:：]\s*(\d+)", s)
                if g or y:
                    items[sidx] = items[sidx]._replace(
                        gmcs=g.group(1) if g else items[sidx].gmcs,
                        sycs=y.group(1) if y else items[sidx].sycs)
                    continue
            if "数据采集状态" in s:
                z = re.search(r"数据采集状态\s*[:：]\s*([0-9A-Za-z]+)", s)
                if z and z.group(1).lower() not in ("null", "none"):
                    items[sidx] = items[sidx]._replace(jczt=z.group(1))
                    continue
    if verbose and not items:
        print("[警告] 经 MCP 查订单未取到商品服务明细（tools/call %s）。" % TOOL["order"])
    _ORDER_CACHE[ckey] = items
    return items


# 检测类型补充说明：cpfwDm → 该类型适用的检测场景描述。
# 仅用于把 query-order 返回的 cpfwmc 讲得更清楚，未知编码会原样展示订单里的名称。
_CPFW_HINT = {
    "MFSY_0000": "新用户免费体验版（轻量初筛，仅概览与部分指标）",
    "ACSY_2001": "财税合规检测通用版（税务 + 财务）",
    "ANSY_1001": "财税合规检测服务·包年不限次",
    "ACSY_JZDCBG001": "尽职调查检测",
    "ACSY_SSYHBG001": "应享未享税收优惠合规检测",
    "ACSY_HYZXDS001": "电商合规检测",
    "ACSY_CSQJBG001": "财税全景合规检测",
    "ACSY_CSZXBG001": "专项检测报告",
    "ACSY_CSHYBG001": "行业检测报告",
    # 以下为网关 ggyw.yaml 中列出的其它常见编码，按需补充
    "ANNSYVIP_0001": "VIP 包年服务",
}


# ---------------------------------------------------------------
# cpxdm（产品线代码 = 平台口径的「报告类型」）→ 中文名
#
# 来源：平台前端 znfk-fxmxgl-web/src/views/complianceInspectionListPage/monitor.js
#       （19 条 MONITOR_CONFIG，侧边栏检测类型 tab 的唯一映射表）
#       以及后端字典 DM_FK_CPXDM（queryCpxdm 接口的数据源）。
# 组合规则（后端 queryOrderByFk / queryOrder 自动展开）：
#       01→01,02   18→18,19   20→20,21   22→22,23   24→24,25   只传 02 会带上 05
# 注意：这是「报告类型」维度，与 cpfwbh（商品服务代码）是两个维度；
#       MCP/OpenAPI 通道传不了 cpxdm（后端 DTO 无该字段），只用于展示与 query-order 过滤。
# ---------------------------------------------------------------
_CPXDM_NAME = {
    "01,02": "税务合规检测",
    "01": "税务合规检测（简化版）",
    "02": "财税综合合规检测",
    "03": "财务合规检测",
    "05": "综合风险检测报告（免费版）",
    "06": "综合合规检测（演示版）",
    "07": "网络直播合规检测",
    "08": "废旧物资合规检测",
    "09": "发票穿透合规检测",
    "17": "企业税务月度健康检测",
    "18,19": "制造业专项合规检测",
    "18": "制造业专项合规检测",
    "19": "制造业专项合规检测",
    "20,21": "批发零售行业专项合规检测",
    "20": "批发零售行业专项合规检测",
    "21": "批发零售行业专项合规检测",
    "22,23": "金融行业专项合规检测",
    "22": "金融行业专项合规检测",
    "23": "金融行业专项合规检测",
    "24,25": "通用行业专项合规检测",
    "24": "通用行业专项合规检测",
    "25": "通用行业专项合规检测",
    "26": "研发费用加计扣除合规检测",
    "27": "企业所得税汇算清缴专项合规检测",
    "28": "尽职调查检测",
    "29": "应享未享税收优惠合规检测",
    "30": "电商合规检测",
    "31": "财税全景合规检测",
    "all": "综合合规检测（全部类型）",
}


def cpxdm_name(code: str) -> str:
    """cpxdm（产品线代码，可逗号分隔）→ 中文报告类型名。未知码原样返回。"""
    if not code:
        return ""
    code = str(code).strip()
    if code in _CPXDM_NAME:
        return _CPXDM_NAME[code]
    names, seen = [], set()
    for p in code.split(","):
        n = _CPXDM_NAME.get(p.strip())
        if n and n not in seen:
            seen.add(n)
            names.append(n)
    return " + ".join(names) if names else code


# 数据采集状态码（sjcjztDm）→ 中文
_JCZT = {"01": "采集中", "02": "采集成功", "03": "采集失败"}


def fetch_available_types(czrId: str = "", verbose: bool = True, cpxdm: str = ""):
    """汇总「当前用户可用的检测类型」——按 cpfwDm 去重。

    cpxdm 为空时列出全部；传入报告类型码（可逗号分隔）则只列该类型下可用的服务，
    与平台「继续生成」弹窗「报告类型 → 所属订单 → 所属服务」三级联动等价。

    同一编码可能有多个订单（如通用版被 3 个订单共用），主条目取「剩余可用次数最多」
    的那个订单，其余放进 tools。返回：
    [{cpfwDm, cpfwmc, hint, cpxdm, cpxdmName, cpfwlxDm, ddbh, ddmc, ddyxqz,
      gmcs, sycs, jczt, tools:[{ddbh, ddmc, ddyxqz, sycs}]}]
    """
    if not czrId:
        czrId = fetch_user_info(verbose=False).get("userId", "")
    orders = fetch_order(czrId, verbose, cpxdm)

    def _sycs(x):
        try:
            return int(x.sycs or 0)
        except (TypeError, ValueError):
            return 0

    grouped = {}
    for o in orders:
        grouped.setdefault(o.cpfwDm, []).append(o)

    result = []
    for dm, lst in grouped.items():
        main = max(lst, key=_sycs)
        others = [x for x in lst if x is not main]
        result.append({
            "cpfwDm": dm, "cpfwmc": main.cpfwmc,
            "hint": _CPFW_HINT.get(dm, ""),
            "cpxdm": main.cpxdm, "cpxdmName": cpxdm_name(main.cpxdm),
            "cpfwlxDm": main.cpfwlxDm,
            "ddbh": main.ddbh, "ddmc": main.ddmc, "ddyxqz": main.ddyxqz,
            "gmcs": main.gmcs, "sycs": main.sycs, "jczt": main.jczt,
            "tools": [{"ddbh": x.ddbh, "ddmc": x.ddmc,
                       "ddyxqz": x.ddyxqz, "sycs": x.sycs} for x in others],
        })
    return result


def render_available_types(types) -> str:
    """把可用检测类型渲染成给用户看的清单（对齐平台「所属服务」下拉的口径）。"""
    if not types:
        return "（未查询到可用检测类型，请确认订单是否有效）"
    lines = []
    for i, t in enumerate(types, 1):
        title = t["cpfwmc"] or t["hint"] or t["cpfwDm"]
        lines.append("%d. **%s**" % (i, title))
        lines.append("   - 检测类型代码：`%s`" % t["cpfwDm"])
        if t["hint"] and t["hint"] != title:
            lines.append("   - 说明：%s" % t["hint"])
        if t["cpxdm"]:
            nm = t.get("cpxdmName") or cpxdm_name(t["cpxdm"])
            lines.append("   - 报告类型：%s（产品线 %s｜%s）"
                         % (nm or "-", t["cpxdm"],
                            "按年" if t["cpfwlxDm"] == "1" else "按次"))
        if t["sycs"]:
            if t["cpfwlxDm"] == "1":
                # 按年服务：剩余 = 单月上限 − 本月已用
                lines.append("   - 本月剩余：%s 次（按年服务，单月上限）" % t["sycs"])
            else:
                gm = "／购买 %s 次" % t["gmcs"] if t["gmcs"] else ""
                lines.append("   - 可用剩余：%s 次%s" % (t["sycs"], gm))
        if t["jczt"]:
            lines.append("   - 数据采集状态：%s" % _JCZT.get(t["jczt"], t["jczt"]))
        if t["ddbh"]:
            extra = "（另有 %d 个订单可用同类型）" % len(t["tools"]) if t["tools"] else ""
            lines.append("   - 订单：%s · %s%s" % (t["ddbh"], t["ddmc"] or "-", extra))
        if t["ddyxqz"]:
            lines.append("   - 有效期至：%s" % t["ddyxqz"])
    return "\n".join(lines)


def _find_type(avail, *, cpfwbh: str = "", ddbh: str = ""):
    """在可用清单里按 cpfwbh 或 ddbh 找对应服务（含 tools 里的备用订单）。"""
    for t in avail:
        if cpfwbh and t["cpfwDm"] == cpfwbh:
            return t
        if ddbh and t["ddbh"] == ddbh:
            return t
        if ddbh:
            for sub in (t.get("tools") or []):
                if sub.get("ddbh") == ddbh:
                    return t
    return None


def resolve_enterprise(enterprise: dict, verbose: bool = True,
                       auto_type: bool = True, require_company: bool = True) -> dict:
    """补齐接口必需参数：userId/customerId/ddbh/cpfwbh/qdbm/sqInfo，以及 nsrsbh/nsrmc 默认值。

    检测对象必须经用户确认后显式传入（重要）
    ----------------------------------------
    `nsrsbh` / `nsrmc` 必须由调用方（对话里的用户）**明确指定**。发起检测的两个入口
    （命令1 账密登录、命令6 扫码登录）在缺任一项时**直接报错拦下**，绝不静默用
    `sys-user-info` 的「当前管理企业」兜底。
    允许（并鼓励）把「当前管理企业」作为**候选**先摆给用户选，禁止的只是**未经用户确认**
    就直接使用。

    历史 bug：旧版把缺省的 nsrsbh/nsrmc 用 companyTaxNo/companyName 静默填上，于是
    「用户只说了要检测、没说要测哪家」时会被默认拿去检测**当前管理企业**——检测对象越权
    且用户不知情（实测已发生）。现在改为 fail fast，把「该问用户哪家企业」这件事交回对话层。

    `require_company=False` 仅用于**不发起检测**的调用（如 1.4 付费报告申请只借本函数
    取 nsrsbh），此时不做该校验。

    cpfwbh 选取优先级（重要）
    ------------------------
    1. 调用方显式传入（用户在对话里选定的检测类型）—— **最高优先**；
    2. 未显式传入时，从订单里自动挑一个默认值：
       优先「新用户免费体验版 MFSY_*」，其次「通用版 ACSY_2001 / 包年 ANSY_1001」，
       最后才取第一条。仅用于「用户没说要哪种」时的兜底，不再静默改写用户的选择。

    ddbh ↔ cpfwbh 必须来自同一可用服务（重要）
    ------------------------------------------
    用户点名的类型若**不在可用清单里**（没买 / 次数用尽 / 编码写错），这里**直接报错拦下**，
    绝不静默换个订单凑数——历史版本用 setdefault 兜底，会产出「免费版订单 + 通用版代码」
    这种错配组合（实测：cpfwbh=ACSY_XXX 不存在时，ddbh 被填成免费体验订单，cpfwbh 仍是
    原值），错单会一路带到 1.1 / 2.1。现在改为 fail fast，并把可用清单回给调用方去问用户。
    """
    ent = dict(enterprise or {})
    info = fetch_user_info(verbose)

    # 检测对象必须由调用方（用户）显式给定，**不得默认取「当前管理企业」**。
    if require_company:
        missing = [k for k in ("nsrsbh", "nsrmc") if not str(ent.get(k) or "").strip()]
        if missing:
            raise SystemExit(
                "[错误] 未明确指定检测对象：企业信息里缺少 %s。\n"
                "       脚本不会自动使用「当前管理企业」——检测对象必须经用户确认后再显式传入。\n"
                "       做法：先向用户确认要检测哪家企业（可把「当前管理企业」作为候选提示给用户选），\n"
                "       确认后把 nsrmc 企业名称 + nsrsbh 纳税人识别号 + ssdq 所属地区（省级码）\n"
                "       写进企业信息 JSON 重试。\n" % " / ".join(missing))

    for k, src in (("userId", "userId"), ("customerId", "customerId"),
                   ("nsrsbh", "nsrsbh"), ("nsrmc", "nsrmc")):
        if not ent.get(k) and info.get(src):
            ent[k] = info[src]

    czr = ent.get("userId") or ""
    # auto_type=False 的调用方（如 1.4 付费报告申请）只借本函数补 nsrsbh，
    # 与检测类型无关，跳过可用清单查询以免多打一次接口。
    avail = fetch_available_types(czr, verbose=False) \
        if (auto_type or ent.get("cpfwbh") or ent.get("ddbh")) else []

    def _unavailable(code: str):
        return SystemExit(
            "[错误] 当前账号没有可用的检测类型 `%s`"
            "（未购买 / 剩余次数为 0 / 编码有误）。\n"
            "       请从下方可用清单里改选，把 cpfwbh 换成对应代码后重试：\n\n%s\n"
            % (code, render_available_types(avail)))

    if ent.get("cpfwbh"):
        # 用户点名了类型：必须在本账号可用清单里核验，核不过就拦下
        if not avail:
            if verbose:
                print("[警告] 未取到可用检测类型清单，跳过配对校验，"
                      "直接使用 cpfwbh=%s" % ent["cpfwbh"])
        else:
            hit = _find_type(avail, cpfwbh=ent["cpfwbh"])
            if hit is None:
                raise _unavailable(ent["cpfwbh"])
            if not ent.get("ddbh"):
                ent["ddbh"] = hit["ddbh"]
                if verbose:
                    print("[提示] 已为所选检测类型 %s 匹配订单 ddbh=%s"
                          % (ent["cpfwbh"], hit["ddbh"]))
            elif ent["ddbh"] != hit["ddbh"]:
                if verbose:
                    print("[提示] 传入的 ddbh=%s 不属于所选类型 %s，"
                          "已按类型修正为 %s"
                          % (ent["ddbh"], ent["cpfwbh"], hit["ddbh"]))
                ent["ddbh"] = hit["ddbh"]

    elif ent.get("ddbh"):
        # 只给了订单号：反查它属于哪个服务，保证两者成对
        hit = _find_type(avail, ddbh=ent["ddbh"]) if avail else None
        if hit is not None:
            ent["cpfwbh"] = hit["cpfwDm"]
            if verbose:
                print("[提示] 已按订单 ddbh=%s 反查检测类型 cpfwbh=%s"
                      % (ent["ddbh"], ent["cpfwbh"]))
        elif verbose:
            print("[警告] 传入的 ddbh=%s 不在可用清单里，cpfwbh 待 config / require 兜底"
                  % ent["ddbh"])

    else:
        # 纯兜底：用户完全没指定类型时才自动挑，且 ddbh/cpfwbh 必须成对写入
        pick = None
        if auto_type:
            for pref in ("MFSY", "ACSY_2001", "ANSY_1001"):
                pick = next((t for t in avail
                             if str(t["cpfwDm"]).upper().startswith(pref)), None)
                if pick:
                    break
            if pick is None and avail:
                pick = avail[0]
        if pick:
            ent["ddbh"] = pick["ddbh"]
            ent["cpfwbh"] = pick["cpfwDm"]
            if verbose:
                print("[提示] 未指定检测类型，已自动选默认服务：ddbh=%s, cpfwbh=%s, 名称=%s"
                      % (pick["ddbh"], pick["cpfwDm"], pick["cpfwmc"]))

    if not ent.get("ddbh") and DDBH:
        ent["ddbh"] = DDBH
    if not ent.get("cpfwbh") and CPFWBH:
        ent["cpfwbh"] = CPFWBH
    ent.setdefault("qdbm", QDBM)
    ent.setdefault("sqInfo", SQ_INFO)
    return ent


def require(ent: dict, *keys):
    miss = [k for k in keys if not ent.get(k)]
    if miss:
        raise SystemExit(
            "[错误] 缺少必需参数：%s。\n"
            "       请命令行传入，或让网关的 %s / %s 工具可用，"
            "或在 config/mcp.ini 的 [business] 里兜底。"
            % ("、".join(miss), TOOL["user_info"], TOOL["order"]))


# ============================================================
# 接口封装（全部经 MCP）
# ============================================================

def mcp_user_info():
    return mcp_call(TOOL["user_info"], {})


def mcp_query_order(czrId: str = "", cpxdm: str = ""):
    args = {}
    if czrId:
        args["czrId"] = czrId
    if cpxdm:
        args["cpxdm"] = cpxdm
    return mcp_call(TOOL["order"], args)


def step1_send_sms(enterprise: dict):
    """接口1.1 发短信验证码（MCP riskdet-sms-code-send）。"""
    ent = resolve_enterprise(enterprise)
    require(ent, "nsrsbh", "nsrmc", "ssdq", "gryhm", "gryhmm", "sflx", "sjhm")
    require(ent, "userId", "customerId", "ddbh", "cpfwbh")
    args = {k: ent.get(k) for k in (
        "nsrsbh", "nsrmc", "ssdq", "gryhm", "gryhmm", "sflx", "sjhm",
        "userId", "customerId", "ddbh", "cpfwbh", "qdbm", "sqInfo") if ent.get(k) is not None}
    args.setdefault("dljgsh", "")
    is_err, text, _ = mcp_call(TOOL["sms_send"], args)
    return is_err, text, parse_md(text)


def step2_upload_sms(nsrsbh: str, taskId: str, smsCode: str):
    """接口1.2 上传短信验证码登录（MCP riskdet-sms-code-upload）。"""
    is_err, text, _ = mcp_call(TOOL["sms_upload"], {
        "taskId": taskId, "nsrsbh": nsrsbh, "smsCode": smsCode})
    return is_err, text, parse_md(text)


def step5_overview(nsrsbh: str, ywjcjlbh: str):
    """接口1.5 获取风险检测概览（MCP riskdet-risk-overview）。"""
    is_err, text, _ = mcp_call(TOOL["overview"], {
        "ywjcjlbh": ywjcjlbh, "nsrsbh": nsrsbh or ""})
    return is_err, text, parse_md(text)


def query_status(nsrsbh: str, ywjcjlbh: str = "", account: dict = None):
    """接口1.3 查询授权状态及报告（MCP riskdet-query-status），单次调用。"""
    acct = account if account is not None else fetch_user_info(verbose=False)
    args = {"nsrsbh": nsrsbh,
            "userId": acct.get("userId", ""),
            "customerId": acct.get("customerId", "")}
    if ywjcjlbh:
        args["ywjcjlbh"] = ywjcjlbh
    is_err, text, _ = mcp_call(TOOL["query_status"], args)
    return is_err, text, parse_md(text)


def _report_ready(f: dict) -> bool:
    """报告已生成：reportUrl / reportUrl_list 里有**非空白**的地址。

    注意：网关模板即使值为空也可能渲染出 `- **reportUrl_list**:` 这一行，
    parse_md 会把它收集成 ['']——直接 bool() 判断会得到 True 而误判「已生成」。
    所以这里必须逐项 strip() 后再判断。
    """
    if str(fv(f, "reportUrl")).strip():
        return True
    return any(str(u).strip() for u in flist(f, "reportUrl_list"))


def _collect_failed(f: dict) -> bool:
    """数据采集失败（死路）：cjStatus == 3。"""
    return str(fv(f, "cjStatus")).strip() == "3"


def _fmt(sec: int) -> str:
    m, s = divmod(int(sec), 60)
    return ("%d 分 %d 秒" % (m, s)) if m else ("%d 秒" % s)


def step3_wait_report(nsrsbh: str, poll_interval: int = 30, max_wait: int = 1200,
                      verbose: bool = True):
    """接口1.3 轮询等待报告生成（一般约 10 分钟）。"""
    if not nsrsbh:
        nsrsbh = (fetch_user_info(verbose=False).get("nsrsbh") or "")
    start, attempt, last_text, last_fields = time.time(), 0, "", {}
    while True:
        attempt += 1
        is_err, text, f = query_status(nsrsbh)
        last_text, last_fields = text, f
        elapsed = int(time.time() - start)
        code = fv(f, "code")
        if is_err or (code and not is_ok_code(code)):
            if verbose:
                print("[警告] 查询授权状态返回异常（code=%s）：%s"
                      % (code, fv(f, "msg", default=text.replace("\n", " ")[:200])))
        if _report_ready(f):
            if verbose:
                print("[完成] 报告已生成，耗时约 %s，共轮询 %d 次" % (_fmt(elapsed), attempt))
            return False, text, f
        if _collect_failed(f):
            if verbose:
                print("[失败] 数据采集失败，报告无法生成：%s" % fv(f, "fail_reason", default="（未给出原因）"))
            return False, text, f
        if elapsed >= max_wait:
            if verbose:
                print("[停止] 已轮询 %s（达到上限 %s），停止轮询" % (_fmt(elapsed), _fmt(max_wait)))
            return False, text, f
        if verbose:
            print("[等待] 报告生成中（一般约 10 分钟），已等待 %s，%d 秒后重试…"
                  % (_fmt(elapsed), poll_interval))
        time.sleep(poll_interval)


def step4_apply_report(nsrsbh, zeroOrderNo, chargeOrderNo, zeroYwjcjlbh, contractId,
                       productId="", productAttrUnique=""):
    """接口1.4 申请付费报告（MCP riskdet-report-apply）。"""
    acct = fetch_user_info(verbose=False)
    ent = resolve_enterprise({"nsrsbh": nsrsbh, "nsrmc": ""}, verbose=False,
                             auto_type=False, require_company=False)
    args = {
        "nsrsbh": nsrsbh or ent.get("nsrsbh", ""),
        "userId": acct.get("userId", ""),
        "customerId": acct.get("customerId", ""),
        "zeroOrderNo": zeroOrderNo,
        "chargeOrderNo": chargeOrderNo,
        "zeroYwjcjlbh": zeroYwjcjlbh,
        "contractId": contractId,
        "productId": productId or PRODUCT_ID,
        "productAttrUnique": productAttrUnique or PRODUCT_ATTR_UNIQUE,
    }
    require(args, "nsrsbh", "userId", "customerId", "productId", "productAttrUnique")
    is_err, text, _ = mcp_call(TOOL["report_apply"], args)
    return is_err, text, parse_md(text)


# ============================================================
# 二维码内联卡片（接口2.1 返回的 PNG → 模块矩阵 → 迷你 1bit PNG）
# ============================================================

def _mask_name(n):
    n = str(n or "")
    return (n[:1] + "***") if len(n) >= 2 else (n + "***" if n else "***")


def _mask_sh(x):
    x = str(x or "")
    return (x[:4] + "******" + x[-3:]) if len(x) >= 8 else x


def _qr_matrix_from_png(png_path: str):
    """把二维码 PNG 解码为模块矩阵（'0'/'1' 行列表），纯 stdlib。解不出返回 None。"""
    try:
        with open(png_path, "rb") as f:
            d = f.read()
        if d[:8] != b"\x89PNG\r\n\x1a\n":
            return None
        pos, idat, plte = 8, b"", None
        w = h = depth = ctype = 0
        while pos + 12 <= len(d):
            ln = struct.unpack(">I", d[pos:pos + 4])[0]
            typ = d[pos + 4:pos + 8]
            chunk = d[pos + 8:pos + 8 + ln]
            if typ == b"IHDR":
                w, h, depth, ctype = struct.unpack(">IIBB", chunk[:10])
            elif typ == b"IDAT":
                idat += chunk
            elif typ == b"PLTE":
                plte = chunk
            pos += 12 + ln
        if depth != 8 or ctype not in (0, 2, 3, 4, 6):
            return None
        ch = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[ctype]
        stride = w * ch
        raw = zlib.decompress(idat)
        if len(raw) != h * (stride + 1):
            return None

        def paeth(a, b, c):
            pp = a + b - c
            pa, pb, pc = abs(pp - a), abs(pp - b), abs(pp - c)
            return a if pa <= pb and pa <= pc else (b if pb <= pc else c)

        rows, prev = [], bytearray(stride)
        for y in range(h):
            ft = raw[y * (stride + 1)]
            line = bytearray(raw[y * (stride + 1) + 1:(y + 1) * (stride + 1)])
            for x in range(stride):
                a = line[x - ch] if x >= ch else 0
                b = prev[x]
                c = prev[x - ch] if x >= ch else 0
                if ft == 1:
                    line[x] = (line[x] + a) & 255
                elif ft == 2:
                    line[x] = (line[x] + b) & 255
                elif ft == 3:
                    line[x] = (line[x] + (a + b) // 2) & 255
                elif ft == 4:
                    line[x] = (line[x] + paeth(a, b, c)) & 255
            prev = line
            rows.append(line)

        def gray(y, x):
            o = x * ch
            if ctype == 3 and plte:
                o = rows[y][o] * 3
                return (plte[o] * 299 + plte[o + 1] * 587 + plte[o + 2] * 114) // 1000
            if ch == 1:
                return rows[y][o]
            return (rows[y][o] * 299 + rows[y][o + 1] * 587 + rows[y][o + 2] * 114) // 1000

        xs, ys = [], []
        for y in range(0, h, 2):
            for x in range(0, w, 2):
                if gray(y, x) < 128:
                    xs.append(x)
                    ys.append(y)
        if not xs:
            return None
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        bw, bh = x1 - x0 + 1, y1 - y0 + 1

        best_n, best_score = None, None
        for n in range(21, 50):
            s = 0
            for gy in range(n):
                for gx in range(n):
                    vals = [gray(y0 + int((gy + f1) * bh / n), x0 + int((gx + f2) * bw / n))
                            for f1 in (0.3, 0.5, 0.7) for f2 in (0.3, 0.5, 0.7)]
                    s += max(vals) - min(vals)
            s /= n * n
            if best_score is None or s < best_score:
                best_n, best_score = n, s
        if best_score > 8.0:  # 网格没对齐，宁可回退也不出坏码
            return None
        n = best_n
        mat = []
        for gy in range(n):
            row = ""
            for gx in range(n):
                bits = sorted(gray(y0 + int((gy + f1) * bh / n), x0 + int((gx + f2) * bw / n)) < 128
                              for f1 in (0.3, 0.5, 0.7) for f2 in (0.3, 0.5, 0.7))
                row += "1" if bits[4] else "0"
            mat.append(row)
        return mat
    except Exception:
        return None


def _png_b64_from_matrix(mat, scale=4, quiet=4):
    """点阵矩阵 → 1bit 灰度 PNG 的 base64（41 模块 + 4 模块静区时约 700 字符）。"""
    pad = "0" * quiet
    w = len(mat[0]) + 2 * quiet
    blank = "0" * w
    grid = [blank] * quiet + [pad + r + pad for r in mat] + [blank] * quiet
    h = len(grid)
    W, H = w * scale, h * scale
    stride = (W + 7) // 8
    raw = bytearray()
    for row_str in grid:
        row = bytearray(stride)
        for x, ch in enumerate(row_str):
            if ch == "0":                      # 白模块：1bit 灰度置 1
                for k in range(scale):
                    xx = x * scale + k
                    row[xx >> 3] |= 1 << (7 - (xx & 7))
        for _ in range(scale):                 # 每行重复 scale 次＝纵向放大
            raw += b"\x00" + bytes(row)        # 行滤波类型 0（None）

    def _chunk(typ, data):
        return (struct.pack(">I", len(data)) + typ + data
                + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF))

    png = (b"\x89PNG\r\n\x1a\n"
           + _chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 1, 0, 0, 0, 0))
           + _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
           + _chunk(b"IEND", b""))
    return base64.b64encode(png).decode()


# 内联卡片模板（WorkBuddy show_widget 用）：宿主自带卡片壳，这里只放内容；
# 二维码用迷你 PNG + <img>，静区已烘焙进图片本身。
_QRCODE_WIDGET_HTML = """<div style="display:flex;align-items:center;gap:24px;padding:4px 2px;">
  <div style="flex:none;background:#ffffff;border-radius:8px;">
    <img src="data:image/png;base64,__B64__" alt="电子税务局登录二维码" style="display:block;width:196px;height:196px;image-rendering:pixelated;">
  </div>
  <div>
    <p style="margin:0 0 12px;font-size:16px;font-weight:500;color:#111111;line-height:1.5;white-space:nowrap;">请使用「电子税务局」App 扫码登录</p>
    <p style="margin:0 0 8px;font-size:13px;white-space:nowrap;"><span style="color:#111111;margin-right:6px;">★</span><span style="color:#111111;font-weight:500;margin-right:10px;">已认证</span><span style="color:#888888;">__NSRMC__ · __NSRSBH__</span></p>
    <p style="margin:0 0 12px;font-size:12px;white-space:nowrap;"><span style="color:#999999;margin-right:6px;">↻</span><span style="color:#888888;">扫码后自动刷新登录状态</span></p>
    <p style="margin:0;font-size:12px;white-space:nowrap;"><span style="color:#555555;margin-right:12px;">有效期 __EXPIRE__ 分钟</span><span style="color:#999999;">生成时间 __TIME__</span></p>
  </div>
</div>"""

# base64 兜底模板（点阵解码失败时用）：base64 按 ≤100 字符折行——单行超 2000 字符
# 会被静默截断（表现为二维码只剩上半截）；浏览器会忽略 data URI 中的换行。
_QRCODE_WIDGET_B64_HTML = """<div style="display:flex;align-items:center;gap:24px;padding:4px 2px;">
  <div style="flex:none;width:200px;height:200px;border:0.5px solid #e6eaf0;border-radius:8px;background:#ffffff;padding:8px;box-sizing:border-box;">
    <img src="data:image/png;base64,__B64__" alt="电子税务局登录二维码" style="width:182px;height:182px;display:block;image-rendering:pixelated;">
  </div>
  <div>
    <p style="margin:0 0 12px;font-size:16px;font-weight:500;color:#111111;line-height:1.5;white-space:nowrap;">请使用「电子税务局」App 扫码登录</p>
    <p style="margin:0 0 8px;font-size:13px;white-space:nowrap;"><span style="color:#111111;margin-right:6px;">★</span><span style="color:#111111;font-weight:500;margin-right:10px;">已认证</span><span style="color:#888888;">__NSRMC__ · __NSRSBH__</span></p>
    <p style="margin:0 0 12px;font-size:12px;white-space:nowrap;"><span style="color:#999999;margin-right:6px;">↻</span><span style="color:#888888;">扫码后自动刷新登录状态</span></p>
    <p style="margin:0;font-size:12px;white-space:nowrap;"><span style="color:#555555;margin-right:12px;">有效期 __EXPIRE__ 分钟</span><span style="color:#999999;">生成时间 __TIME__</span></p>
  </div>
</div>"""


def _b64_decode_lenient(b64: str) -> bytes:
    """宽容解码 base64：自动补 padding、忽略空白。失败返回 b""。"""
    b64 = re.sub(r"\s", "", b64 or "")
    if not b64:
        return b""
    for pad in range(4):
        t = b64 + "=" * pad
        if len(t) % 4:
            continue
        try:
            return base64.b64decode(t, validate=False)
        except Exception:
            continue
    return b""


def _png_health(png_path: str) -> str:
    """检查 PNG 是否完整可用，返回 ""（健康）或问题描述。"""
    try:
        with open(png_path, "rb") as f:
            d = f.read()
    except OSError:
        return "无法读取文件"
    if len(d) < 8 or d[:8] != b"\x89PNG\r\n\x1a\n":
        return "不是有效的 PNG 文件（魔数不对）"
    pos, idat = 8, b""
    w = h = 0
    while pos + 12 <= len(d):
        ln = struct.unpack(">I", d[pos:pos + 4])[0]
        typ = d[pos + 4:pos + 8]
        chunk = d[pos + 8:pos + 8 + ln]
        if typ == b"IHDR" and len(chunk) >= 10:
            w, h = struct.unpack(">II", chunk[:8])
        elif typ == b"IDAT":
            idat += chunk
        pos += 12 + ln
    if not idat:
        return "PNG 缺少图像数据（IEND 前无 IDAT）"
    try:
        zlib.decompress(idat)
    except Exception:
        return ("PNG 图像数据已损坏（IDAT 解压失败）——base64 在传递过程中被截断或改动过。"
                " 请改用 blob:<路径> 传入，或让网关直接返回图片内容块")
    return ""


def _resolve_qr_source(src: str, out_path: str) -> str:
    """把任意形态的二维码来源落到 out_path，返回路径（失败返回 ""）。

    支持四类（**全部纯本地，不联网、不需要令牌**，专门给「连接器包」场景用）：
      · `blob:<本地路径>`      — 网关 image_blob_ref 返回的本地文件；
      · `data:image/png;base64,...` 或裸 base64；
      · 本地 PNG 文件路径；
      · `@<文件>` / `-` / 空  — 从文件或 stdin 读取（避免超长 base64 走命令行被截断）。
    """
    if src is None:
        src = ""
    src = src.strip()
    if not src or src == "-":
        try:
            src = sys.stdin.read().strip()
        except Exception:
            return ""
    if src.startswith("@"):
        try:
            with open(src[1:].strip(), encoding="utf-8") as f:
                src = f.read().strip()
        except OSError:
            return ""
    if not src:
        return ""
    # ⚠️ blob: 必须排在 base64 判断之前——否则路径字符串会被当成 base64 解出一堆垃圾
    if src.startswith("blob:"):
        return _decode_data_uri(src, out_path)
    if src.startswith("data:") or "base64," in src[:64]:
        raw = _b64_decode_lenient(src.split(",", 1)[1] if "," in src[:64] else src)
        if raw:
            with open(out_path, "wb") as f:
                f.write(raw)
            return out_path
        return _decode_data_uri(src, out_path)
    # 裸 base64（无 data: 前缀）：先试解，失败再当路径处理
    if len(src) > 256 and re.fullmatch(r"[A-Za-z0-9+/=\s]+", src or " "):
        raw = _b64_decode_lenient(src)
        if raw:
            with open(out_path, "wb") as f:
                f.write(raw)
            return out_path
    if os.path.isfile(src):
        try:
            with open(src, "rb") as rf, open(out_path, "wb") as wf:
                wf.write(rf.read())
            return out_path
        except OSError:
            return ""
    return _decode_data_uri(src, out_path)


def cmd_qr_render(src: str, nsrmc: str = "", nsrsbh: str = "") -> int:
    """零鉴权地把二维码渲染成可内联卡片（供宿主 show_widget 直接透传）。

    与命令6 的区别：命令6 自己经 MCP 取码（需要令牌），本命令只做渲染，
    来源由调用方给——因此**在只有宿主连接器 OAuth 的环境里也能用**。
    """
    os.makedirs(_LOGS_DIR, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    out_path = os.path.abspath(os.path.join(_LOGS_DIR, "qrcode_render_%s.png" % stamp))
    png_path = _resolve_qr_source(src, out_path)
    if not png_path:
        print("[错误] 未能解析二维码来源。可传入：blob:<路径> / data:image/png;base64,… "
              "/ 本地 PNG 路径 / @<文件> / -（stdin）")
        return 2
    # 先体检：base64 在传递中被截断/改动时，这里能给出准确诊断，
    # 而不是等到卡片生成失败时报一个无关的错。
    bad = _png_health(png_path)
    if bad:
        print("[错误] 二维码图片不可用：%s" % bad)
        print("[提示] 长 base64 在命令行/转抄中极易损坏（约 2 KB 时高发）。"
              " 优先用 blob:<路径> 或本地 PNG 路径；若网关只返回 data URI，"
              " 建议改为返回图片内容块。")
        return 4
    widget = ""
    try:
        widget = _build_qrcode_widget(png_path, nsrmc, nsrsbh)
    except Exception as exc:
        print("[警告] 卡片生成失败：%s" % exc)
    if not widget:
        print("[错误] 卡片生成失败：未能从 %s 解析出二维码点阵" % png_path)
        return 3
    print("[WIDGET_BEGIN]")
    print(widget)
    print("[WIDGET_END]")
    print("[展示] 二维码PNG：%s" % png_path)
    return 0


def _build_qrcode_widget(png_path: str, nsrmc: str, nsrsbh: str) -> str:
    """生成可内联渲染的卡片片段（供宿主在对话流中展示）。失败返回空串。"""
    common = {"__NSRMC__": _mask_name(nsrmc), "__NSRSBH__": _mask_sh(nsrsbh),
              "__TIME__": time.strftime("%Y-%m-%d %H:%M:%S"), "__EXPIRE__": "3"}
    mat = _qr_matrix_from_png(png_path) if png_path else None
    if mat:
        out = _QRCODE_WIDGET_HTML.replace("__B64__", _png_b64_from_matrix(mat))
    else:
        b64 = ""
        if png_path:
            try:
                with open(png_path, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode()
            except OSError:
                b64 = ""
        if not b64:
            return ""
        out = _QRCODE_WIDGET_B64_HTML.replace(
            "__B64__", "\n".join(b64[i:i + 100] for i in range(0, len(b64), 100)))
    for k, v in common.items():
        out = out.replace(k, v)
    return out


def _decode_data_uri(qrcode: str, out_path: str):
    """把二维码落到 out_path，返回路径（失败返回 ""）。

    支持两类来源：
      · `data:image/png;base64,...` — 解码 base64 写盘；
      · `blob:<本地路径>` — 网关返回的 image_blob_ref，直接复制该文件。
    """
    if not qrcode:
        return ""
    if qrcode.startswith("blob:"):
        src = qrcode[len("blob:"):].strip()
        try:
            if not src or not os.path.isfile(src):
                return ""
            with open(src, "rb") as rf, open(out_path, "wb") as wf:
                wf.write(rf.read())
            return out_path
        except Exception:
            return ""
    b64 = qrcode.split(",", 1)[1] if "," in qrcode[:64] else qrcode
    try:
        with open(out_path, "wb") as f:
            f.write(base64.b64decode(b64))
        return out_path
    except Exception:
        return ""


# ============================================================
# 命令6/7：取码 → 内联卡片 → 分离守护轮询扫码 → 前台等待终态
# ============================================================

_RESULT_JSON = os.path.join(_LOGS_DIR, "scan_result.json")
_SCAN_FATAL_CODES = {"1006", "1008", "9999", "500"}


def _daemon_exe() -> str:
    """守护进程解释器：Windows 优先 pythonw.exe，避免弹黑框。"""
    exe = sys.executable or ""
    if os.name != "nt" or not exe:
        return exe
    cand = os.path.join(os.path.dirname(exe), "pythonw.exe")
    return cand if os.path.exists(cand) else exe


def _daemon_env() -> dict:
    return {**os.environ, "PYTHONUNBUFFERED": "1",
            "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}


_CREATE_BREAKAWAY_FROM_JOB = getattr(subprocess, "CREATE_BREAKAWAY_FROM_JOB", 0x01000000)
_DETACHED_PROCESS = getattr(subprocess, "DETACHED_PROCESS", 0x00000008)
_CREATE_NEW_PROCESS_GROUP = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200)


def _spawn_detached_daemon(enterprise: dict, max_total: int, daemon_log):
    """跨平台「真正脱离宿主」地拉起守护进程。

    宿主在一条命令执行完毕后会回收该命令名下的进程资源（POSIX 回收进程组、
    Windows 回收 Job 对象）。没有真正脱离时守护进程会在命令6返回后立刻被杀，
    端到端表现为「命令7 必然超时」。
    """
    args = [_daemon_exe(), os.path.abspath(__file__), "daemon",
            json.dumps(enterprise, ensure_ascii=False), str(max_total)]
    kwargs = {"stdout": daemon_log, "stderr": daemon_log, "cwd": _HERE,
              "env": _daemon_env()}
    if os.name != "nt":
        return subprocess.Popen(args, start_new_session=True, **kwargs)
    flags = _DETACHED_PROCESS | _CREATE_NEW_PROCESS_GROUP
    try:
        return subprocess.Popen(args, creationflags=flags | _CREATE_BREAKAWAY_FROM_JOB, **kwargs)
    except OSError:
        return subprocess.Popen(args, creationflags=flags, **kwargs)


def _get_qrcode_via_mcp(enterprise: dict):
    """接口2.1（MCP riskdet-get-qrcode）→ (ent, fields, taskId, ywjcjlbh, qrcode, err)。"""
    ent = resolve_enterprise(enterprise)
    require(ent, "nsrsbh", "nsrmc", "ssdq")
    require(ent, "userId", "customerId", "ddbh", "cpfwbh")
    args = {k: ent.get(k) for k in (
        "nsrsbh", "nsrmc", "ssdq", "ddbh", "cpfwbh", "qdbm",
        "userId", "customerId", "sqInfo") if ent.get(k) is not None}
    is_err, text, _ = mcp_call(TOOL["qrcode"], args, timeout=90)
    f = parse_md(text)
    if is_err or not is_ok_code(fv(f, "code")):
        msg = fv(f, "msg", default=text.replace("\n", " ")[:300])
        hint = ""
        if str(fv(f, "code")).strip() == "9999":
            hint = ("（9999 系统异常：多为 ssdq 地区码不受支持——该参数只认省级码，"
                    "辽宁应填 2100，填市级码如 2106 丹东市会直接报 9999）")
        if "401" in text or "账号未登录" in text:
            hint = ("（网关转发到 yfp-ggyw 业务服务时缺少登录态。请确认网关已把调用方"
                    "身份映射为该服务的登录会话，或按该服务要求补 login-user 头）")
        return ent, f, "", "", None, "%s%s" % (msg, hint)
    # 二维码可能有两种形态：内联 data URI，或指向宿主本地 blob 文件的 image_blob_ref。
    # 二者都归一化到 qrcode：data URI 原样返回，blob 引用则返回 "blob:<路径>"。
    qr = fv(f, "qrcode")
    if not qr:
        blob_path = fv(f, "qrcode_blob_path")
        if blob_path:
            qr = "blob:" + blob_path
    return ent, f, fv(f, "taskId"), fv(f, "ywjcjlbh"), qr, ""


def _write_pending(taskId: str, ywjcjlbh: str, nsrsbh: str, ent: dict,
                   baseline_uuid: str = ""):
    """取码后立即写入待查任务（taskId + 账号 + 基线 uuid），供命令7 / 守护进程轮询。

    `baseline_uuid` 必须在**用户扫码之前**取到并固化：1010（会话终结）时靠它区分
    「本次扫码产生的新记录」与「历史记录」。若等到命令7 启动后才现取基线，而用户
    已经扫过码，基线里就含了新记录，会把成功误判成过期。
    """
    os.makedirs(_LOGS_DIR, exist_ok=True)
    with open(_RESULT_JSON, "w", encoding="utf-8") as f:
        json.dump({"status": "wait", "msg": "", "taskId": taskId,
                   "ywjcjlbh": ywjcjlbh, "nsrsbh": nsrsbh,
                   "_account": {"userId": ent.get("userId", ""),
                                "customerId": ent.get("customerId", "")},
                   "_baseline_uuid": baseline_uuid,
                   "ts": time.strftime("%Y-%m-%d %H:%M:%S")}, f, ensure_ascii=False)


def scan_once(nsrsbh: str, taskId: str):
    """接口2.2 扫码状态查询（MCP riskdet-scan-code），单次。"""
    is_err, text, _ = mcp_call(TOOL["scan"], {"taskId": taskId, "nsrsbh": nsrsbh})
    return is_err, text, parse_md(text)


def step6_launch_scan(enterprise: dict, max_total: int = 240):
    """命令6（前台，几秒返回）：经 MCP 取码 → 出内联卡片 → 拉起分离守护进程轮询扫码。

    stdout 中 [WIDGET_BEGIN]…[WIDGET_END] 之间是可直接内联渲染的卡片片段。
    """
    try:
        os.remove(_RESULT_JSON)          # 清理旧结果，避免读到上一次终态
    except OSError:
        pass

    ent, f, taskId, ywjcjlbh, qrcode, err = _get_qrcode_via_mcp(enterprise)
    if err:
        return 500, {"code": "ERR", "msg": err}
    if not qrcode or not taskId:
        return 500, {"code": "ERR",
                     "msg": "取码成功但响应里没有二维码或 taskId（请检查网关 "
                            "riskdet-get-qrcode 的响应模板是否仍输出 taskId 与二维码图片）"}

    nsrsbh = ent.get("nsrsbh", "")
    stamp = time.strftime("%Y%m%d_%H%M%S")
    os.makedirs(_LOGS_DIR, exist_ok=True)
    png_path = _decode_data_uri(
        qrcode, os.path.abspath(os.path.join(_LOGS_DIR, "qrcode_live_%s.png" % stamp)))

    widget_html = ""
    if png_path:
        try:
            widget_html = _build_qrcode_widget(png_path, ent.get("nsrmc", ""), nsrsbh)
        except Exception as exc:
            print("[警告] 内联卡片生成失败（不影响扫码）：%s" % exc)
    if widget_html:
        print("[WIDGET_BEGIN]")
        print(widget_html)
        print("[WIDGET_END]")
    print("[展示] 二维码PNG：%s" % (png_path or "（未能落盘）"))

    # 基线 uuid：此刻用户还没看到二维码（stdout 尚未交付给助手），一定早于扫码，
    # 固化写进 pending，供命令7 / 守护进程在 1010 时做交叉确认。
    baseline_uuid = ""
    try:
        _, _, base = query_status(
            nsrsbh, account={"userId": ent.get("userId", ""),
                             "customerId": ent.get("customerId", "")})
        baseline_uuid = fv(base, "uuid")
    except Exception as exc:
        print("[提示] 基线 uuid 获取失败（不影响扫码）：%s" % exc)

    _write_pending(taskId, ywjcjlbh, nsrsbh, ent, baseline_uuid)
    daemon_log = open(os.path.join(_LOGS_DIR, "daemon.out"), "a", encoding="utf-8")
    _spawn_detached_daemon(ent, max_total, daemon_log)
    daemon_log.close()
    print("[提示] 守护进程已分离运行；请立即内联渲染上面的卡片，随后前台运行命令7等待扫码结果")
    return 200, {"code": "0000", "msg": "守护进程已启动",
                 "taskId": taskId, "ywjcjlbh": ywjcjlbh, "nsrsbh": nsrsbh,
                 "qrcode_png": png_path,
                 "qrcode_widget_ready": bool(widget_html)}


def _run_scan_daemon(enterprise: dict, max_total: int = 240):
    """守护进程：轮询 2.2 → 1010 时用 1.3 交叉确认 → 终态写 logs/scan_result.json。

    轮询线程与主线程共用一个 threading.Event，不依赖本地 HTTP 服务
    （内联卡片不做状态轮询，故无需起 /status 端点）。
    """
    import threading

    nsrsbh = str(enterprise.get("nsrsbh", ""))
    state = {"taskId": "", "status": "wait", "msg": "", "ywjcjlbh": ""}
    lock = threading.Lock()
    done = threading.Event()

    # 复用命令6 取到的 taskId 与账号（写在 _RESULT_JSON 的 pending 记录里）
    try:
        with open(_RESULT_JSON, encoding="utf-8") as fp:
            pending = json.load(fp)
    except Exception:
        pending = {}
    account = pending.get("_account") or None
    with lock:
        state["taskId"] = str(pending.get("taskId", ""))
        state["ywjcjlbh"] = str(pending.get("ywjcjlbh", ""))

    # 基线 uuid：优先用命令6 固化在 pending 里的（一定早于扫码）；
    # 缺失时才现取（此时若用户已扫码，基线可能已含新记录，交叉确认会偏保守）。
    baseline_uuid = str(pending.get("_baseline_uuid") or "")
    if not baseline_uuid:
        try:
            _, _, base = query_status(nsrsbh, account=account)
            baseline_uuid = fv(base, "uuid")
        except Exception:
            pass
    print("[守护] 基线 uuid=%s，taskId=%s" % (baseline_uuid, state["taskId"]))

    def _save_result():
        with lock:
            obj = {"status": state["status"], "msg": state["msg"],
                   "taskId": state["taskId"], "nsrsbh": nsrsbh,
                   "ywjcjlbh": state["ywjcjlbh"],
                   "ts": time.strftime("%Y-%m-%d %H:%M:%S")}
        with open(_RESULT_JSON, "w", encoding="utf-8") as fp:
            json.dump(obj, fp, ensure_ascii=False)

    def _finish(status, msg, ywjcjlbh=""):
        with lock:
            state["status"] = status
            state["msg"] = msg
            if ywjcjlbh:
                state["ywjcjlbh"] = ywjcjlbh
        _save_result()
        done.set()

    def _poll_scan():
        while not done.is_set():
            with lock:
                tid = state["taskId"]
            if not tid:
                print("[守护] 无 taskId，无法轮询扫码状态")
                _finish("fail", "缺少 taskId（命令6 未正确传递）")
                return
            is_err, text, f = scan_once(nsrsbh, tid)
            if is_err:
                print("[重试] 扫码状态查询失败：%s" % text.replace("\n", " ")[:200])
                time.sleep(3)
                continue
            code = str(fv(f, "code")).strip()
            if code == "0000":
                yw = fv(f, "ywjcjlbh")
                print("[完成] 扫码授权成功，ywjcjlbh=%s" % yw)
                _finish("ok", "扫码授权成功", yw)
                return
            if code in _SCAN_FATAL_CODES:
                print("[失败] 扫码授权失败（code=%s）：%s" % (code, fv(f, "msg")))
                _finish("fail", fv(f, "msg", default="扫码授权失败"))
                return
            if code == "1010":
                # 会话终结：调 1.3 交叉确认，避免「扫码成功但错过 0000」被误判为过期
                _, _, f3 = query_status(nsrsbh, account=account)
                uuid3 = fv(f3, "uuid")
                if uuid3 and uuid3 != baseline_uuid:
                    print("[完成] 会话终结但1.3出现新记录，判定成功，ywjcjlbh=%s" % uuid3)
                    _finish("ok", "扫码授权成功（经接口1.3确认）", uuid3)
                    return
                print("[过期] 二维码已过期（1010 且无新采集记录）")
                _finish("expired", "二维码已过期")
                return
            time.sleep(3)

    _save_result()  # 初始 wait 状态
    threading.Thread(target=_poll_scan, daemon=True).start()
    print("[守护] 扫码轮询已启动，最长等待 %d 秒" % max_total)

    if not done.wait(timeout=max_total):
        with lock:
            still_wait = state["status"] == "wait"
        if still_wait:
            print("[停止] 守护进程等待达上限 %d 秒" % max_total)
            _finish("expired", "等待超时（未扫码），二维码已过期")
    time.sleep(0.2)


def step7_wait_result(max_wait: int = 240, poll: int = 3):
    """命令7（前台阻塞）：自己轮询 2.2 扫码状态，直到终态或超时。

    【重要修复】原实现只读「分离守护进程」写的 logs/scan_result.json，自己不做任何
    轮询。但宿主若用 Windows Job 对象约束命令的进程树、且禁止 Job 逃逸
    （CREATE_BREAKAWAY_FROM_JOB 报 WinError 5 拒绝访问），降级后的
    DETACHED_PROCESS 仍留在同一个 Job 里，命令6 一返回就被连带回收——守护进程
    连第一行日志都写不出（daemon.out 恒为 0 字节），scan_result.json 永远停在
    _write_pending 留下的初始 "wait"。此时用户扫码其实已成功，命令7 却必然超时。

    修复方式：命令7 读取命令6 同步写下的 pending（taskId / nsrsbh / _account），
    在**前台自己**轮询 riskdet-scan-code，不再依赖守护进程；守护进程若在支持的宿主
    上正常写出终态，仍会被优先采用（行为向后兼容）。
    """
    start = time.time()

    def _read_result():
        if not os.path.exists(_RESULT_JSON):
            return None
        try:
            with open(_RESULT_JSON, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def _emit(status, msg, ywjcjlbh, taskId, nsrsbh):
        code = "0000" if status == "ok" else status
        out = {"code": code, "msg": msg, "taskId": taskId, "nsrsbh": nsrsbh}
        if status == "ok":
            out["data"] = {"nsrsbh": nsrsbh, "ywjcjlbh": ywjcjlbh}
            out["notify"] = ("✅ 扫码授权成功！检测流程已自动继续，"
                             "正在查询报告生成状态（预计约10分钟）")
        elif status == "expired":
            out["notify"] = "⚠️ 二维码已过期。如需继续扫码登录，请回复「重新生成二维码」"
        else:
            out["notify"] = "❌ 扫码授权失败：%s" % msg
        return 200, out

    r = _read_result() or {}
    taskId = str(r.get("taskId", ""))
    nsrsbh = str(r.get("nsrsbh", ""))
    account = r.get("_account") or None

    if not taskId:
        # 没有待查任务：退回读守护进程结果（或提示先取码）
        if r.get("status") in ("ok", "fail", "expired"):
            return _emit(r["status"], r.get("msg", ""), r.get("ywjcjlbh", ""), "", nsrsbh)
        return 200, {"code": "wait", "msg": "未找到待查的扫码任务（请先执行命令6 取码）",
                     "notify": "⚠️ 未找到待查的扫码任务，请先重新生成二维码"}

    # 基线 uuid：优先用命令6 固化在 pending 里的（一定早于扫码）；缺失时才现取。
    baseline_uuid = str(r.get("_baseline_uuid") or "")
    if not baseline_uuid:
        try:
            _, _, base = query_status(nsrsbh, account=account)
            baseline_uuid = fv(base, "uuid")
        except Exception:
            pass
    print("[命令7] 已接管扫码轮询（taskId=%s，基线 uuid=%s），最长等待 %d 秒"
          % (taskId, baseline_uuid or "(无)", max_wait))

    while True:
        # 1) 守护进程若已产出终态，优先采用
        r2 = _read_result() or {}
        if (r2.get("status") in ("ok", "fail", "expired")
                and str(r2.get("taskId", "")) == taskId):
            return _emit(r2["status"], r2.get("msg", ""), r2.get("ywjcjlbh", ""),
                         taskId, nsrsbh)

        # 2) 前台自己轮询接口 2.2
        is_err, text, f = scan_once(nsrsbh, taskId)
        if not is_err:
            code = str(fv(f, "code")).strip()
            if code == "0000":
                return _emit("ok", "扫码授权成功", fv(f, "ywjcjlbh") or taskId,
                             taskId, nsrsbh)
            if code == "1010":
                _, _, f3 = query_status(nsrsbh, account=account)
                uuid3 = fv(f3, "uuid")
                if uuid3 and uuid3 != baseline_uuid:
                    return _emit("ok", "扫码授权成功（经接口1.3确认）", uuid3,
                                 taskId, nsrsbh)
                return _emit("expired", "二维码已过期", "", taskId, nsrsbh)
            if code == "9999":
                # 任务 ID 失效（如二维码长时间未扫）——按「过期」处理更准确
                return _emit("expired", "扫码任务已失效（taskId 无效）", "", taskId, nsrsbh)
            if code in _SCAN_FATAL_CODES:
                return _emit("fail", fv(f, "msg", default="扫码授权失败"),
                             "", taskId, nsrsbh)

        if time.time() - start > max_wait:
            return 200, {"code": "wait", "msg": "等待超时（未扫码）",
                         "notify": "⚠️ 等待超时，二维码可能已过期。如需继续扫码登录，请回复「重新生成二维码」",
                         "taskId": taskId, "nsrsbh": nsrsbh}
        time.sleep(poll)


# ============================================================
# 其它
# ============================================================

def _print_mcp(name, res):
    is_err, text, _ = res
    print("HTTP", 500 if is_err else 200)
    print(text if text else "（无文本响应）")


USAGE = """用法：
  python mcp_gateway_client.py <命令> <参数...>

所有业务接口均经网关 MCP 调用（网关地址见 config/mcp.ini），不需要 AK/SK、不需要 gmssl。

命令：
  1  发送短信验证码（1.1）     参数: '<企业信息JSON>'
  2  上传验证码登录（1.2）     参数: <nsrsbh> <taskId> <smsCode>
  3  轮询授权状态及报告（1.3） 参数: <nsrsbh> [轮询间隔秒=30] [最大等待秒=1200]
  4  申请付费报告（1.4）       参数: <nsrsbh> <zeroOrderNo> <chargeOrderNo> <zeroYwjcjlbh> <contractId> [productId] [productAttrUnique]
  5  获取风险概览（1.5）       参数: <nsrsbh> <ywjcjlbh>
  6  取码并出内联卡片（2.1）   参数: '<企业信息JSON>' [守护最大等待秒=240]
  7  前台等待扫码终态（2.2）   参数: [最大等待秒=240]
  info   经 MCP 取当前用户信息（排查网关登录态用）
  order  经 MCP 查询订单         参数: [czrId] [cpxdm]
  types  列出当前用户可选的检测类型  参数: [czrId] [cpxdm]
  cpxdms 列出平台全部报告类型（离线，不需要令牌）
  qr     把二维码渲染成内联卡片   参数: <来源> [企业名] [税号]

企业信息JSON 里可省略 userId/customerId/ddbh/cpfwbh/qdbm/sqInfo —— 脚本会经 MCP 自动补齐。

说明：qr / cpxdms 是**纯本地命令，不联网、不需要任何令牌**；
其余命令经 MCP 调用，需要令牌（DKI_MCP_TOKEN 环境变量 > config/.token.json > config/mcp.ini）。
qr 的 <来源> 可为：blob:<路径> / data:image/png;base64,… / 本地 PNG 路径 / @<文件> / -（stdin）；
来源很长时优先用 @<文件> 或 stdin，避免命令行长度限制导致截断。
"""


def main(argv):
    cmd = argv[1] if len(argv) > 1 else "help"

    if cmd in ("help", "-h", "--help"):
        print(USAGE)
        return 0

    if cmd == "info":
        _print_mcp(TOOL["user_info"], mcp_user_info())
        return 0

    if cmd == "order":
        czr = argv[2] if len(argv) > 2 else ""
        if not czr:
            czr = fetch_user_info(verbose=False).get("userId", "")
        cpxdm = argv[3] if len(argv) > 3 else ""
        _print_mcp(TOOL["order"], mcp_query_order(czr, cpxdm))
        return 0

    if cmd == "types":
        # 列出当前用户可选的检测类型（来自订单 spfwList），供对话里让用户挑选
        czr = argv[2] if len(argv) > 2 else ""
        if not czr:
            czr = fetch_user_info(verbose=False).get("userId", "")
        cpxdm = argv[3] if len(argv) > 3 else ""
        types = fetch_available_types(czr, cpxdm=cpxdm)
        if cpxdm:
            print("# 可用检测类型（报告类型 %s %s，共 %d 种）"
                  % (cpxdm, ("· " + cpxdm_name(cpxdm)) if cpxdm_name(cpxdm) else "",
                     len(types)))
        else:
            print("# 可用检测类型（共 %d 种）" % len(types))
        print()
        print(render_available_types(types))
        print()
        print("---MACHINE---")
        print(json.dumps(types, ensure_ascii=False, indent=2))
        return 0

    if cmd == "qr":
        src = argv[2] if len(argv) > 2 else "-"
        nsrmc = argv[3] if len(argv) > 3 else ""
        nsrsbh = argv[4] if len(argv) > 4 else ""
        return cmd_qr_render(src, nsrmc, nsrsbh)

    if cmd == "cpxdms":
        # 平台支持的「报告类型」全量清单（来源 monitor.js / 字典 DM_FK_CPXDM）。
        # 用于在用户不确定要哪类报告时给出候选；再配合 `types <czrId> <cpxdm>` 查具体可用服务。
        print("# 平台支持的检测类型（报告类型 cpxdm）")
        print()
        for code, name in sorted(_CPXDM_NAME.items(),
                                 key=lambda kv: (len(kv[0]), kv[0])):
            if "," in code:
                continue
            print("- `%s`  %s" % (code, name))
        print()
        print("> 组合码（后端自动展开）：01,02 / 18,19 / 20,21 / 22,23 / 24,25；"
              "只传 02 会带上 05。")
        print("> 用法：`types <czrId> <cpxdm>` 查该报告类型下真正可用的订单与服务。")
        return 0

    if cmd == "1":
        ent = json.loads(argv[2])
        is_err, text, f = step1_send_sms(ent)
        print("HTTP", 500 if is_err else 200)
        print(text)
        return 0

    if cmd == "2":
        is_err, text, f = step2_upload_sms(argv[2], argv[3], argv[4])
        print("HTTP", 500 if is_err else 200)
        print(text)
        return 0

    if cmd == "3":
        nsrsbh = argv[2]
        interval = int(argv[3]) if len(argv) > 3 else 30
        max_wait = int(argv[4]) if len(argv) > 4 else 1200
        is_err, text, f = step3_wait_report(nsrsbh, interval, max_wait)
        print("HTTP", 500 if is_err else 200)
        print("HTTP 200 = 查询成功（具体是否已生成报告看 reportUrl / cjStatus）")
        print(text)
        if _report_ready(f):
            print("\n[结论] 报告已生成：")
            print(json.dumps({
                "uuid": fv(f, "uuid"), "reportUrl": fv(f, "reportUrl"),
                "reportUrl_list": flist(f, "reportUrl_list"),
                "reportStatus": fv(f, "reportStatus"), "cjStatus": fv(f, "cjStatus"),
            }, ensure_ascii=False, indent=2))
        return 0

    if cmd == "4":
        nsrsbh, zeroOrderNo, chargeOrderNo, zeroYwjcjlbh, contractId = argv[2:7]
        productId = argv[7] if len(argv) > 7 else ""
        productAttrUnique = argv[8] if len(argv) > 8 else ""
        is_err, text, f = step4_apply_report(
            nsrsbh, zeroOrderNo, chargeOrderNo, zeroYwjcjlbh, contractId,
            productId, productAttrUnique)
        print("HTTP", 500 if is_err else 200)
        print(text)
        return 0

    if cmd == "5":
        is_err, text, f = step5_overview(argv[2], argv[3])
        print("HTTP", 500 if is_err else 200)
        print(text)
        return 0

    if cmd == "6":
        ent = json.loads(argv[2])
        max_total = int(argv[3]) if len(argv) > 3 else 240
        st, r = step6_launch_scan(ent, max_total)
        print("HTTP", st)
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return 0

    if cmd == "daemon":
        ent = json.loads(argv[2])
        _run_scan_daemon(ent, int(argv[3]) if len(argv) > 3 else 240)
        return 0

    if cmd == "7":
        st, r = step7_wait_result(int(argv[2]) if len(argv) > 2 else 240)
        print("HTTP", st)
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return 0

    print("未知命令：%s\n\n%s" % (cmd, USAGE))
    return 1


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    sys.exit(main(sys.argv))
