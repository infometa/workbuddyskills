#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
腾讯电子签合同AI工具主入口
支持 Python 2.7+ / 3.x，零第三方依赖。

导出文件（合同 docx / 审查批注与摘要 / 对比报告与明细）在获取到链接后
自动下载到技能根目录 downloads/ 下；JSON 输出中的 _downloaded_files 为已
下载文件的本地绝对路径（下载失败时回退为输出原链接，_downloaded_files 为空）。

Usage:
    python3 scripts/tencent_esign.py <command> [args...]

Commands:
    auth-check                          检查 Token 是否已配置
    auth-save   <token>                 保存 Token
    auth-validate <token>               验证并保存 Token
    upload      <file...>               上传文件(支持多个)，返回 ResourceId
    call        <action> '<json>'       调用任意 API
    wait-draft  <task_id>               轮询起草任务直到完成，返回含 _links_md
    wait-review <task_id>               轮询单个审查任务直到完成
    wait-compare <task_id> [原文件名]    轮询对比任务直到完成，自动下载报告到 ./downloads/（文件名：原文件名_对比报告/差异明细）
    review-batch '<["id1","id2"]>'      轮询多个审查任务并返回摘要+链接（多文件必用）
    review-links <task_id>              获取已完成审查任务的预览/下载链接列表
    compare-links <task_id> [原文件名]   获取已完成对比任务的预览/下载链接并自动下载（文件名规则同 wait-compare）
    review-progress-url <task_id>       获取审查进行中的实时查看链接
    compare-progress-url <task_id>      获取对比进行中的实时查看链接
    search-laws '<json>'                法条检索，返回结构化结果列表
    version                             显示版本信息
"""

import json
import os
import re
import socket
import ssl
import sys
import time
import uuid

PY3 = sys.version_info[0] >= 3

if PY3:
    from http.client import HTTPSConnection, HTTPConnection
    from urllib.parse import urlparse, urljoin
    from pathlib import Path
else:
    from httplib import HTTPSConnection, HTTPConnection
    from urlparse import urlparse, urljoin

TOKEN_FILE = os.path.join(os.path.expanduser("~"), ".esign-token")


# ---------------------------------------------------------------------------
# Config (cached at module level)
# ---------------------------------------------------------------------------

_config_cache = None

_DEFAULT_CONFIG = {
    "baseUrl": "https://appgw.ess.tencent.cn/plugin/openapi/",
    "fileUploadUrl": "https://file.ess.tencent.cn/upload/",
    "version": "v1.2.0",
}

def load_config():
    global _config_cache
    if _config_cache is not None:
        return _config_cache
    if PY3:
        script_dir = str(Path(__file__).parent.absolute())
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
    config_file = os.path.join(script_dir, "config.json")
    try:
        if os.path.exists(config_file):
            with open(config_file, "r") as f:
                cfg = json.load(f)
            merged = dict(_DEFAULT_CONFIG)
            merged.update(cfg)
            _config_cache = merged
        else:
            _config_cache = dict(_DEFAULT_CONFIG)
    except (IOError, ValueError, OSError) as e:
        sys.stderr.write("Warning: config.json 读取失败 (%s)，使用默认配置\n" % str(e))
        _config_cache = dict(_DEFAULT_CONFIG)
    return _config_cache


# ---------------------------------------------------------------------------
# Token helpers
# ---------------------------------------------------------------------------

def get_token():
    """Token 统一从 ~/.esign-token 文件读取（由 auth-save / auth-validate 命令写入），不读环境变量。

    单一数据源：写入即生效，不存在环境变量旧值遮蔽文件新值的问题。
    """
    try:
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, "r") as f:
                t = f.read().strip()
            if t and t != "***************":   # 掩码防护：防止脱敏值被误当真 Token
                return t
    except (IOError, OSError) as e:
        sys.stderr.write("Warning: 读取 Token 文件失败: %s\n" % str(e))
    return ""


def save_token(token):
    try:
        token_dir = os.path.dirname(TOKEN_FILE)
        if token_dir and not os.path.exists(token_dir):
            os.makedirs(token_dir)
        with open(TOKEN_FILE, "w") as f:
            f.write(token.strip())
        try:
            os.chmod(TOKEN_FILE, 0o600)
        except Exception:
            pass
        return TOKEN_FILE
    except (IOError, OSError) as e:
        sys.stderr.write("Warning: 保存 Token 失败: %s\n" % str(e))
        return None


# ---------------------------------------------------------------------------
# HTTP (persistent connections with auto-reconnect)
# ---------------------------------------------------------------------------

_conn_pool = {}

MAX_RETRIES = 3


def _get_conn(url):
    """Get or create a persistent HTTPS/HTTP connection for the given URL's host."""
    parsed = urlparse(url)
    host = parsed.hostname
    port = parsed.port
    scheme = parsed.scheme

    if not host:
        raise ValueError("无效的 URL: %s" % url)

    key = "%s:%s:%s" % (scheme, host, port or (443 if scheme == "https" else 80))

    conn = _conn_pool.get(key)
    if conn is not None:
        return conn, parsed

    if scheme == "https":
        ctx = ssl.create_default_context()
        conn = HTTPSConnection(host, port or 443, timeout=120, context=ctx)
    else:
        conn = HTTPConnection(host, port or 80, timeout=120)

    _conn_pool[key] = conn
    return conn, parsed


def _drop_conn(url):
    """Remove a cached connection (call after unrecoverable errors)."""
    parsed = urlparse(url)
    key = "%s:%s:%s" % (parsed.scheme, parsed.hostname,
                        parsed.port or (443 if parsed.scheme == "https" else 80))
    conn = _conn_pool.pop(key, None)
    if conn:
        try:
            conn.close()
        except Exception:
            pass


def _parse_response(raw, status_code):
    """Parse HTTP response body, tolerating empty or non-JSON content."""
    if not raw or not raw.strip():
        if 200 <= status_code < 300:
            return {"Response": {}}
        return {"error": "HTTP %d: (空响应)" % status_code}
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        return {"error": "HTTP %d: %s" % (status_code, raw[:500])}


def _request(url, method, body, headers, timeout=120):
    """Send an HTTP request with connection reuse. Retries up to MAX_RETRIES on transient failures."""
    if not url:
        return {"error": "URL 未配置，请检查 config.json 或环境变量。"}

    last_err = None
    for attempt in range(MAX_RETRIES):
        try:
            conn, parsed = _get_conn(url)
            path = parsed.path
            if parsed.query:
                path = path + "?" + parsed.query

            conn.timeout = timeout
            conn.request(method, path or "/", body=body, headers=headers)
            resp = conn.getresponse()
            raw = resp.read()
            if PY3:
                raw = raw.decode("utf-8")

            if resp.status in (502, 503, 504) and attempt < MAX_RETRIES - 1:
                sys.stderr.write("HTTP %d, 第 %d 次重试...\n" % (resp.status, attempt + 1))
                _drop_conn(url)
                time.sleep(min(2 ** attempt, 5))
                continue

            return _parse_response(raw, resp.status)

        except ValueError as e:
            return {"error": str(e)}
        except Exception as e:
            last_err = e
            _drop_conn(url)
            if attempt < MAX_RETRIES - 1:
                wait = min(2 ** attempt, 5)
                sys.stderr.write("连接异常 (%s), %ds 后第 %d 次重试...\n" % (str(e), wait, attempt + 1))
                time.sleep(wait)

    return {"error": "网络错误 (重试 %d 次后失败): %s" % (MAX_RETRIES, str(last_err))}


# ---------------------------------------------------------------------------
# File download (export files land in the skill's downloads/ directory)
# ---------------------------------------------------------------------------

CONTENT_TYPE_EXT_MAP = {
    "application/pdf": ".pdf",
    "application/msword": ".doc",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/vnd.ms-excel": ".xls",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
}

_FILENAME_UNSAFE_RE = re.compile(r'[\\/:*?"<>|\r\n\t]')

_KNOWN_EXTS = (".pdf", ".doc", ".docx", ".xls", ".xlsx")

DOWNLOAD_MAX_REDIRECTS = 5


def _sanitize_filename(name):
    cleaned = _FILENAME_UNSAFE_RE.sub("_", (name or "").strip()).strip(" .")
    return cleaned[:80] if cleaned else "file"


def _strip_known_ext(name):
    low = (name or "").lower()
    for e in _KNOWN_EXTS:
        if low.endswith(e):
            return (name or "")[:-len(e)]
    return name or ""


def _get_download_dir():
    """下载目录：技能根目录下的 downloads/（基于脚本自身位置定位，不依赖 cwd）。"""
    skill_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    d = os.path.join(skill_root, "downloads")
    if not os.path.exists(d):
        os.makedirs(d)
    return d


def _unique_path(directory, filename):
    candidate = os.path.join(directory, filename)
    base, ext = os.path.splitext(filename)
    i = 1
    while os.path.exists(candidate):
        candidate = os.path.join(directory, "%s(%d)%s" % (base, i, ext))
        i += 1
    return candidate


def _ext_from_url(url):
    ext = os.path.splitext(os.path.basename(urlparse(url).path))[1]
    if ext and 1 < len(ext) <= 6 and ext[1:].isalnum():
        return ext.lower()
    return ""


def _is_internal_host(host):
    """SSRF 防护：拒绝内网/私有网段地址；解析失败视为不安全。"""
    if not host:
        return True
    h = host.strip().lower()
    if h == "localhost" or h.endswith(".local") or h.endswith(".internal"):
        return True
    try:
        ip = socket.gethostbyname(h)
    except Exception:
        return True
    parts = ip.split(".")
    if len(parts) != 4:
        return True
    try:
        a, b = int(parts[0]), int(parts[1])
    except ValueError:
        return True
    if a in (0, 9, 10, 11, 21, 30, 127) or a >= 224:
        return True
    if a == 169 and b == 254:
        return True
    if a == 192 and b == 168:
        return True
    if a == 172 and 16 <= b <= 31:
        return True
    return False


def _download_file(url, base_name, default_ext=".bin", max_redirects=DOWNLOAD_MAX_REDIRECTS):
    """下载 url 到技能目录 downloads/ 下。返回 (本地绝对路径, None) 或 (None, 错误信息)。

    - 手动跟随 301/302/303/307/308 重定向（上限 max_redirects），每跳校验目标 host 非内网
    - 5xx / 网络异常指数退避重试（共 MAX_RETRIES 次尝试）
    - 扩展名三级推断：URL path → Content-Type → 调用方默认值
    - 同名文件自动加 (1)(2) 序号，不覆盖已有文件
    - 预签名 URL 无需鉴权头（与 API 网关不同域，连接池按 host 天然隔离）
    - 失败原因仅由调用方记录到 stderr，输出回退为原链接文案，不向用户暴露
    """
    if not url:
        return None, "URL 为空"
    last_err = None
    for attempt in range(MAX_RETRIES):
        current = url
        try:
            for _ in range(max_redirects + 1):
                parsed = urlparse(current)
                host = parsed.hostname or ""
                if _is_internal_host(host):
                    return None, "目标地址为内网/无效主机，已拒绝下载: %s" % host
                conn, _p = _get_conn(current)
                path = parsed.path
                if parsed.query:
                    path = path + "?" + parsed.query
                conn.request("GET", path or "/", headers={"Accept": "*/*"})
                resp = conn.getresponse()
                if resp.status in (301, 302, 303, 307, 308):
                    loc = resp.getheader("Location") or ""
                    resp.read()
                    if not loc:
                        return None, "HTTP %d 且缺少 Location" % resp.status
                    current = urljoin(current, loc)
                    continue
                if resp.status == 200:
                    content_type = (resp.getheader("Content-Type") or "").split(";")[0].strip().lower()
                    ext = _ext_from_url(current) or CONTENT_TYPE_EXT_MAP.get(content_type, "") or default_ext
                    filename = _sanitize_filename(_strip_known_ext(base_name)) + ext
                    final_path = _unique_path(_get_download_dir(), filename)
                    with open(final_path, "wb") as f:
                        while True:
                            chunk = resp.read(65536)
                            if not chunk:
                                break
                            f.write(chunk)
                    return final_path, None
                if resp.status >= 500:
                    resp.read()
                    raise IOError("HTTP %d" % resp.status)
                resp.read()
                return None, "HTTP %d" % resp.status
            return None, "重定向次数超限（>%d 次）" % max_redirects
        except Exception as e:
            last_err = e
            _drop_conn(current)
            if attempt < MAX_RETRIES - 1:
                wait = min(2 ** attempt, 5)
                sys.stderr.write("下载异常 (%s), %ds 后第 %d 次重试...\n" % (str(e), wait, attempt + 1))
                time.sleep(wait)
    return None, "下载失败 (重试 %d 次后): %s" % (MAX_RETRIES, str(last_err))


def _format_export_line(url, local_path, link_text, local_text, fail_text):
    """导出行三态：已下载→本地路径文案；有 URL→原链接文案（与自动下载功能加入前逐字一致）；无 URL→失败提示。"""
    if local_path:
        return local_text % local_path
    if url:
        return link_text % url
    return fail_text


def call_api(action, params, token=None):
    if token is None:
        token = get_token()
    if not token:
        return {"error": "Token 未配置。请先运行 auth-validate <token>（推荐，验证后写入 ~/.esign-token）或 auth-save <token>。"}

    cfg = load_config()
    url = os.environ.get("ESIGN_BASE_URL", cfg.get("baseUrl", ""))

    if "Action" not in params:
        params["Action"] = action

    _PLATFORM_ACTIONS = {
        "CreateDraftContractByPromptsTask",
        "CreateBatchContractReviewTask",
        "CreateContractComparisonTask",
        "DescribeRiskIdentificationLawDocuments",
    }
    _KNOWN_PLATFORMS = {"claude code", "codebuddy", "workbuddy", "qclaw", "codex"}
    if action in _PLATFORM_ACTIONS:
        val = (params.get("SkillPlatformName") or "").strip()
        if not val or val.lower() not in _KNOWN_PLATFORMS:
            params["SkillPlatformName"] = "其它"

    body = json.dumps(params, ensure_ascii=False)
    if PY3:
        body = body.encode("utf-8")

    headers = {
        "Content-Type": "application/json",
        "X-Tc-Version": "2020-11-11",
        "x-tc-action": action,
        "Authorization": token,
        "X-Skill-Version": cfg.get("version", "v1.0.0"),
    }

    return _request(url, "POST", body, headers, timeout=120)


# ---------------------------------------------------------------------------
# Auth commands
# ---------------------------------------------------------------------------

def cmd_auth_check():
    token = get_token()
    if token:
        out({"success": True, "message": "Token 已配置", "preview": token[:8] + "..."})
    else:
        out({"success": False, "message": "未找到 Token。请前往 https://qian.tencent.com/aiSkill 获取 SIGN-TOKEN。"})
        sys.exit(1)


def cmd_auth_save(token):
    path = save_token(token)
    if path:
        out({"success": True, "message": "Token 已保存至 " + path})
    else:
        out({"success": False, "message": "Token 保存失败，请检查 ~/.esign-token 的写入权限。"})
        sys.exit(1)


def cmd_auth_validate(token):
    result = call_api("DescribeContractReviewTask",
                      {"Action": "DescribeContractReviewTask", "TaskId": "__validate__"},
                      token=token)
    auth_fail = False
    server_error = False
    if "error" in result:
        err = str(result["error"]).lower()
        for kw in ("401", "403", "unauthorized", "authfailure", "invalidcredential", "forbidden"):
            if kw in err:
                auth_fail = True
                break
        for kw in ("500", "502", "503", "429", "timeout", "network error"):
            if kw in err:
                server_error = True
                break
    else:
        resp = result.get("Response", {})
        if "Error" in resp:
            code = resp["Error"].get("Code", "")
            auth_codes = ("AuthFailure", "UnauthorizedOperation", "InvalidCredential",
                          "AuthFailure.SignatureFailure", "AuthFailure.TokenFailure")
            if code in auth_codes:
                auth_fail = True
            elif code in ("InternalError", "RequestLimitExceeded"):
                server_error = True

    if auth_fail:
        out({"success": False, "message": "Token 验证失败。请前往 https://qian.tencent.com/aiSkill 重新获取 SIGN-TOKEN。"})
        sys.exit(1)
    elif server_error:
        out({"success": False, "message": "服务暂时不可用，无法验证 Token，请稍后重试。", "detail": result})
        sys.exit(1)
    else:
        path = save_token(token)
        if path:
            out({"success": True, "message": "已成功安装。Token 已验证并保存。", "path": path})
        else:
            out({"success": True, "message": "Token 验证通过，但保存到 ~/.esign-token 失败，请检查 home 目录写入权限。"})


# ---------------------------------------------------------------------------
# Upload (multipart/form-data to dedicated file endpoint)
# ---------------------------------------------------------------------------

def build_multipart(file_paths, business_type="DOCUMENT"):
    boundary = "----EsignBoundary" + uuid.uuid4().hex
    parts = []

    # business_type field
    header = (
        "--%s\r\n"
        "Content-Disposition: form-data; name=\"business_type\"\r\n"
        "\r\n"
        "%s\r\n" % (boundary, business_type)
    )
    parts.append(header.encode("utf-8") if PY3 else header)

    # file fields
    for fp in file_paths:
        fname = os.path.basename(fp).replace('"', '\\"').replace('\n', '_')
        with open(fp, "rb") as f:
            data = f.read()
        header = (
            "--%s\r\n"
            "Content-Disposition: form-data; name=\"file\"; filename=\"%s\"\r\n"
            "Content-Type: application/octet-stream\r\n"
            "\r\n" % (boundary, fname)
        )
        if PY3:
            parts.append(header.encode("utf-8") + data + b"\r\n")
        else:
            parts.append(header + data + b"\r\n")

    footer = ("--%s--\r\n" % boundary)
    parts.append(footer.encode("utf-8") if PY3 else footer)

    body = b"".join(parts)
    content_type = "multipart/form-data; boundary=%s" % boundary
    return body, content_type


def upload_single(file_path, token, url):
    try:
        body, content_type = build_multipart([file_path])
    except (IOError, OSError) as e:
        return {"error": "读取文件失败 (%s): %s" % (file_path, str(e))}
    headers = {
        "Content-Type": content_type,
        "AccessToken": token,
    }
    return _request(url, "POST", body, headers, timeout=300)


def cmd_upload(file_paths):
    for fp in file_paths:
        if not os.path.exists(fp):
            out({"error": "文件不存在: " + fp})
            sys.exit(1)

    token = get_token()
    if not token:
        out({"error": "Token 未配置。请先运行 auth-validate <token>（推荐，验证后写入 ~/.esign-token）或 auth-save <token>。"})
        sys.exit(1)

    cfg = load_config()
    url = os.environ.get("ESIGN_FILE_URL", cfg.get("fileUploadUrl", ""))

    if len(file_paths) == 1:
        result = upload_single(file_paths[0], token, url)
        out(result)
        if "error" in result:
            sys.exit(1)
    else:
        results = []
        resource_ids = []
        for fp in file_paths:
            result = upload_single(fp, token, url)
            results.append(result)
            if "error" in result:
                out({"error": "上传 %s 失败" % fp, "detail": result})
                sys.exit(1)
            rid = result.get("Response", {}).get("ResourceId", "")
            resource_ids.append(rid)
            sys.stderr.write("已上传: %s -> %s\n" % (os.path.basename(fp), rid))
        out({"Response": {"ResourceIds": resource_ids, "TotalCount": len(resource_ids), "Details": results}})


# ---------------------------------------------------------------------------
# Generic call
# ---------------------------------------------------------------------------

def cmd_call(action, params_json):
    try:
        params = json.loads(params_json)
    except Exception as e:
        out({"error": "JSON 解析失败: %s" % str(e)})
        sys.exit(1)
    out(call_api(action, params))


# ---------------------------------------------------------------------------
# Polling helpers
# ---------------------------------------------------------------------------

MAX_POLL_ERRORS = 5

def poll(action, task_id, success_status, fail_status, max_wait=600, exit_on_fail=True):
    """Poll until task reaches a terminal status or max_wait is exceeded.

    Never gives up early due to transient network/API errors — only a terminal
    status from the server (success or fail) or a timeout stops the loop.
    Consecutive errors are logged and counted, but polling continues until the
    server explicitly signals completion or max_wait seconds have elapsed.

    If exit_on_fail=False, returns the result even on fail_status instead of
    calling sys.exit(). Useful for batch processing where individual failures
    should not abort the whole run.
    """
    interval = 3
    elapsed = 0
    consecutive_errors = 0
    while elapsed < max_wait:
        result = call_api(action, {"Action": action, "TaskId": task_id})
        if "error" in result:
            consecutive_errors += 1
            sys.stderr.write("轮询出错 (%d/%d，继续等待): %s\n" % (consecutive_errors, MAX_POLL_ERRORS, result["error"]))
            # Log a warning after MAX_POLL_ERRORS consecutive failures, but keep polling.
            if consecutive_errors >= MAX_POLL_ERRORS:
                sys.stderr.write("警告: 已连续 %d 次轮询出错，继续等待服务端响应...\n" % consecutive_errors)
            time.sleep(interval)
            elapsed += interval
            interval = min(int(interval + 2), 10)
            continue
        consecutive_errors = 0
        resp = result.get("Response", {})
        if "Error" in resp:
            err_code = resp["Error"].get("Code", "")
            sys.stderr.write("服务端错误 (%s)，等待后重试...\n" % err_code)
            time.sleep(interval)
            elapsed += interval
            interval = min(int(interval + 2), 10)
            continue
        status = resp.get("Status", -1)
        status_labels = {
            "DescribeDraftContractByPromptsTask": {0: "已创建", 1: "执行中", 2: "成功", 3: "失败"},
            "DescribeContractReviewTask":         {1: "创建成功", 2: "排队中", 3: "执行中", 4: "成功", 5: "失败"},
            "DescribeContractComparisonTask":     {0: "待创建", 1: "对比中", 2: "成功", 3: "失败"},
        }
        label = status_labels.get(action, {}).get(status, "未知")
        if status in (success_status if isinstance(success_status, (list, tuple)) else [success_status]):
            sys.stderr.write("[%s] 任务 %s 状态: %s(%s) ✓\n" % (action, task_id, label, status))
            return result
        if status in (fail_status if isinstance(fail_status, (list, tuple)) else [fail_status]):
            sys.stderr.write("[%s] 任务 %s 状态: %s(%s) ✗\n" % (action, task_id, label, status))
            if exit_on_fail:
                out(result)
                sys.exit(1)
            else:
                return result
        sys.stderr.write("[%s] 任务 %s 状态: %s(%s), 已等待 %ds, %ds 后再次查询...\n" % (
            action, task_id, label, status, elapsed, interval))
        time.sleep(interval)
        elapsed += interval
        interval = min(int(interval + 2), 10)
    if exit_on_fail:
        out({"error": "超时 (%d秒)" % max_wait})
        sys.exit(1)
    return {"error": "超时 (%d秒)" % max_wait}


def cmd_wait_draft(task_id, is_revision=False):
    result = poll("DescribeDraftContractByPromptsTask", task_id, success_status=2, fail_status=3, max_wait=600)
    resp = result.get("Response", {})
    name = resp.get("ContractName", "")
    url = resp.get("ContractUrl", "")
    status = resp.get("Status", -1)
    if url:
        dl_path, dl_err = _download_file(url, (name if name else "合同") + "_起草合同", default_ext=".docx")
        if dl_path:
            result["_links_md"] = "📄 合同《%s》已下载到本地：`%s`（请前往该目录查看）" % (
                name if name else "合同", dl_path)
            result["_downloaded_files"] = [dl_path]
        else:
            sys.stderr.write("[WARN] wait-draft: 合同文件自动下载失败 (%s)，回退为链接输出\n" % dl_err)
            result["_links_md"] = "📄 [点击下载《%s》](%s)（链接 20 分钟内有效）" % (name if name else "合同", url)
    else:
        sys.stderr.write("[WARN] wait-draft: ContractUrl 为空 (task_id=%s), 完整响应: %s\n" % (
            task_id, json.dumps(resp, ensure_ascii=False)))
        result["_links_md"] = ""
    if status == 2:
        if is_revision:
            result["_next_steps"] = (
                "还需要继续调整吗？\n"
                "- **a. 继续修改** — 告诉我需要调整的内容\n"
                "- **b. 下载保存** — 直接使用\n"
                "- **c. 签署合同** — 直接发起和签署合同"
            )
        else:
            result["_next_steps"] = (
                "接下来你可以：\n"
                "- **a. 修改合同** — 告诉我需要调整的内容\n"
                "- **b. 下载保存** — 直接使用\n"
                "- **c. 签署合同** — 直接发起和签署合同\n"
                "- **d. 刷新链接** — 重新获取下载链接（链接过期时使用）"
            )
    out(result)


def cmd_wait_review(task_id, limit=10, offset=0):
    """Wait for review task and return formatted risk summary with pagination.

    Returns:
        _summary: overview line (total risks, high risk count)
        _risks_md: pre-formatted markdown table of risks (sorted by severity)
        _has_more: True if there are more risks beyond the current page
        _total: total risk count
        _shown: number shown in this response
        _offset: current offset (for requesting next page)
    """
    result = poll("DescribeContractReviewTask", task_id, success_status=4, fail_status=5, max_wait=600)
    resp = result.get("Response", {})

    total_risk = resp.get("TotalRiskCount", 0)
    high_risk = resp.get("HighRiskCount", 0)
    risks = resp.get("Risks", [])

    # Sort by severity: high > medium > low > info
    level_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2, "INFO": 3}
    risks.sort(key=lambda r: level_order.get(r.get("RiskLevel", "INFO").upper(), 99))

    # Paginate
    page_risks = risks[offset:offset + limit]
    has_more = (offset + limit) < len(risks)

    # Build summary
    summary = "共发现 **%d** 项风险，其中高风险 **%d** 项。" % (total_risk, high_risk)

    # Build markdown table
    level_map = {"HIGH": "🔴 高", "MEDIUM": "🟡 中", "LOW": "🔵 低", "INFO": "ℹ️ 提示"}
    lines = []
    lines.append("| 序号 | 风险名称 | 等级 | 原文 | 描述 | 修改建议 |")
    lines.append("|------|----------|------|------|------|----------|")
    for i, risk in enumerate(page_risks, offset + 1):
        name = risk.get("RiskName", "")
        level = level_map.get(risk.get("RiskLevel", "").upper(), risk.get("RiskLevel", ""))
        content = risk.get("Content", "")
        desc = risk.get("RiskDescription", "")
        advice = risk.get("RiskAdvice", "")
        # Truncate very long fields to prevent single-cell overflow
        if len(content) > 80:
            content = content[:77] + "..."
        if len(desc) > 100:
            desc = desc[:97] + "..."
        if len(advice) > 100:
            advice = advice[:97] + "..."
        # Escape pipe characters in table cells
        content = content.replace("|", "\\|").replace("\n", " ")
        desc = desc.replace("|", "\\|").replace("\n", " ")
        advice = advice.replace("|", "\\|").replace("\n", " ")
        name = name.replace("|", "\\|").replace("\n", " ")
        lines.append("| %d | %s | %s | %s | %s | %s |" % (i, name, level, content, desc, advice))

    risks_md = "\n".join(lines)

    # Pagination hint
    if has_more:
        remaining = len(risks) - (offset + limit)
        risks_md += "\n\n> 还有 **%d** 项风险未显示，回复「查看更多」可继续查看。" % remaining

    out({
        "task_id": task_id,
        "Status": resp.get("Status"),
        "_has_more": has_more,
        "_total": total_risk,
        "_shown": len(page_risks),
        "_offset": offset,
    })
    # Print formatted markdown directly (not JSON-encoded) so the model outputs it verbatim.
    # Inside JSON, newlines become \n escape sequences which the model must mentally parse
    # and reconstruct — leading to unstable output (sometimes table, sometimes bullet list).
    # Printing directly means the model sees a ready-to-copy markdown table in its command output.
    print("")
    print(summary)
    print("")
    print(risks_md)


def _fetch_export_url(action, params, url_field, label):
    """Call an export API once and return (url, should_retry).

    Returns:
        (url, True)   — URL obtained successfully
        ("", True)    — empty URL, no error; server may still be generating, caller should retry
        ("", False)   — server returned a business error; no point retrying, caller should stop
    """
    r = call_api(action, params)
    sys.stderr.write("[导出链接] %s 响应: %s\n" % (label, json.dumps(r, ensure_ascii=False)))
    err = r.get("Response", {}).get("Error")
    if err:
        sys.stderr.write("[ERROR] %s 获取失败: %s - %s\n" % (
            label, err.get("Code", ""), err.get("Message", "")))
        return "", False
    url = r.get("Response", {}).get(url_field, "")
    return url, True


def _get_review_links(task_id, base_name=None, max_attempts=8, retry_delay=15):
    """Fetch all review links with retry for all endpoints.

    The web preview URL is available almost immediately after task completion,
    but the two export endpoints need extra server-side generation time.
    Strategy: fetch web_url on attempt 0, skip export endpoints until attempt 1.
    Stops retrying an endpoint as soon as the server returns a business error.

    When an export URL is obtained, the file is downloaded immediately to the
    skill's downloads/ directory (short-lived presigned URL — download on
    receipt). Returns (link_lines, downloaded_local_paths).
    """
    web_url = ""
    url1 = ""
    url2 = ""
    url1_failed = False  # True = server returned a business error, stop retrying
    url2_failed = False

    for attempt in range(max_attempts):
        if attempt > 0:
            pending = []
            if not web_url: pending.append("在线查看")
            if not url1 and not url1_failed: pending.append("批注文件")
            if not url2 and not url2_failed: pending.append("摘要Excel")
            if not pending:
                break
            sys.stderr.write("审查导出链接未就绪(%s)，%ds 后重试 (%d/%d)...\n" % (
                "/".join(pending), retry_delay, attempt, max_attempts - 1))
            time.sleep(retry_delay)

        if not web_url:
            r = call_api("DescribeContractReviewWebUrl", {"TaskId": task_id})
            sys.stderr.write("[审查链接] WebUrl 响应: %s\n" % json.dumps(r, ensure_ascii=False))
            web_url = r.get("Response", {}).get("WebUrl", "")

        # Export endpoints need server-side generation time — skip on attempt 0.
        if attempt > 0:
            if not url1 and not url1_failed:
                # word文件存在落盘延迟，导致导出批注文件失败，增加等待时间
                time.sleep(3)
                url1, retry = _fetch_export_url(
                    "ExportContractReviewResult",
                    {"TaskId": task_id, "FileType": 1},
                    "Url", "审查批注文件(FileType=1)")
                if not retry:
                    url1_failed = True

            if not url2 and not url2_failed:
                url2, retry = _fetch_export_url(
                    "ExportContractReviewResult",
                    {"TaskId": task_id, "FileType": 2},
                    "Url", "审查摘要Excel(FileType=2)")
                if not retry:
                    url2_failed = True

        all_done = web_url and (url1 or url1_failed) and (url2 or url2_failed)
        if all_done:
            break

    # 导出文件自动下载（在线预览链接保留展示）；失败静默回退为链接文案
    base = _strip_known_ext(base_name) if base_name else "合同审查"
    dl1, err1 = _download_file(url1, base + "_审查批注", default_ext=".docx") if url1 else (None, None)
    dl2, err2 = _download_file(url2, base + "_审查摘要", default_ext=".xlsx") if url2 else (None, None)
    if err1:
        sys.stderr.write("[WARN] 审查批注文件自动下载失败: %s\n" % err1)
    if err2:
        sys.stderr.write("[WARN] 审查摘要自动下载失败: %s\n" % err2)

    links = [
        "📊 [在线查看审查结果](%s)（3小时内有效）" % web_url
            if web_url else "📊 在线查看审查结果：获取失败，请选择「刷新链接」重试",
        _format_export_line(
            url1, dl1,
            "📝 [下载带风险批注的文件](%s)（20 分钟内有效）",
            "📝 批注文件已下载到本地：`%s`（请前往该目录查看）",
            "📝 下载带风险批注的文件：获取失败，请选择「刷新链接」重试"),
        _format_export_line(
            url2, dl2,
            "📋 [下载审查结果摘要（Excel）](%s)（20 分钟内有效）",
            "📋 审查摘要（Excel）已下载到本地：`%s`（请前往该目录查看）",
            "📋 下载审查结果摘要（Excel）：获取失败，请选择「刷新链接」重试"),
    ]
    downloaded = [p for p in (dl1, dl2) if p]
    return links, downloaded


def _links_block(links):
    """Join a list of pre-formatted Markdown link strings into a single ready-to-paste block."""
    return "\n".join(links)


def cmd_review_batch(task_ids_json, names_json=None):
    """Poll ALL task IDs to completion first, then fetch all links in one pass.

    Phase 1: poll every task until it reaches a terminal status (success=4 or
             fail=5).  Individual failures are recorded but do NOT abort the
             batch — remaining tasks continue to be polled.
    Phase 2: once every task has a terminal status, fetch the three download /
             preview links for each successful task.  Separating the two phases
             means link-fetching starts only after all audit work is done, which
             avoids the race between a slow task and an eager link request on an
             already-finished one.
    """
    try:
        task_ids = json.loads(task_ids_json)
        if not isinstance(task_ids, list):
            task_ids = [task_ids]
    except Exception as e:
        out({"error": "JSON 解析失败: %s" % str(e)})
        sys.exit(1)

    if not task_ids:
        out({"error": "task_ids 数组为空"})
        sys.exit(1)

    # Parse optional file names list
    file_names = []
    if names_json:
        try:
            file_names = json.loads(names_json)
            if not isinstance(file_names, list):
                file_names = []
        except (ValueError, TypeError):
            file_names = []

    # ── Phase 1: wait for every task to finish ────────────────────────────────
    results = []
    for task_id in task_ids:
        sys.stderr.write("轮询任务 %s ...\n" % task_id)
        poll_result = poll(
            "DescribeContractReviewTask", task_id,
            success_status=4, fail_status=5,
            max_wait=600, exit_on_fail=False,
        )

        if "error" in poll_result:
            results.append({
                "task_id": task_id,
                "failed": True,
                "error": poll_result.get("error", "任务失败"),
            })
            sys.stderr.write("任务 %s 失败，继续处理剩余任务\n" % task_id)
            continue

        resp = poll_result.get("Response", {})
        if resp.get("Status") == 5:
            results.append({
                "task_id": task_id,
                "failed": True,
                "error": resp.get("Message", "审查失败"),
            })
            sys.stderr.write("任务 %s 审查失败，继续处理剩余任务\n" % task_id)
            continue

        results.append({
            "task_id": task_id,
            "failed": False,
            "total_risk_count": resp.get("TotalRiskCount", 0),
            "high_risk_count": resp.get("HighRiskCount", 0),
        })

    # ── Phase 2: fetch links for all successful tasks ─────────────────────────
    sys.stderr.write("所有审查任务已完成，开始统一获取链接...\n")
    all_downloaded = []
    for idx, r in enumerate(results, 1):
        if r.get("failed"):
            r["_links_block"] = ""
            continue
        fname = file_names[idx - 1] if idx - 1 < len(file_names) else None
        link_items, dl_files = _get_review_links(r["task_id"], base_name=fname)
        r["_links_block"] = _links_block(link_items)
        if dl_files:
            r["_downloaded_files"] = dl_files
            all_downloaded.extend(dl_files)

    # ── Phase 3: build output ─────────────────────────────────────────────────
    # Build a single ready-to-paste block so the model never rewrites any URL.
    output_lines = []
    for idx, r in enumerate(results, 1):
        # Use file name if available, otherwise fall back to task_id
        label = file_names[idx - 1] if idx - 1 < len(file_names) else r["task_id"]
        if r.get("failed"):
            output_lines.append("**文件 %d**（%s）：审查失败——%s" % (idx, label, r.get("error", "")))
        else:
            block = r.get("_links_block", "")
            if block:
                output_lines.append("**文件 %d**（%s）\n%s" % (idx, label, block))
            else:
                output_lines.append("**文件 %d**（%s）：链接暂未就绪，请稍后选择「刷新链接」重试。" % (idx, label))
        output_lines.append("")  # blank line between files

    any_failed = any(r.get("failed") for r in results)
    out({
        "success": not any_failed or len(results) > 1,
        "task_count": len(results),
        "results": results,
        "_downloaded_files": all_downloaded,
        "_links_output": "\n".join(output_lines).strip(),
        "_next_steps": (
            "你可以：\n"
            "- **a. 重新审查** — 补充重点审查要求后重新审查\n"
            "- **b. 按建议重新起草** — 基于风险建议和原合同重新生成一份合同\n"
            "- **c. 刷新链接** — 重新获取预览和下载链接（链接过期时使用）\n"
            "- **d. 查看审查记录** — 对历史合同审查任务进行查看"
        ),
    })


def cmd_wait_compare(task_id, base_name=None):
    result = poll("DescribeContractComparisonTask", task_id, success_status=2, fail_status=3, max_wait=600)
    # Fetch all three links after task completion.  The web preview URL is
    # available almost immediately, but the two export endpoints (PDF annotation
    # and Excel diff) need extra time for the server to generate the files.
    # Strategy: fetch web_url on attempt 0, then wait before first export attempt.
    # Stop retrying an endpoint immediately when the server returns a business error.
    try:
        web_url = ""
        url0 = ""
        url1 = ""
        url0_failed = False
        url1_failed = False
        max_attempts = 8
        retry_delay = 15
        for attempt in range(max_attempts):
            if attempt > 0:
                pending = []
                if not web_url: pending.append("在线预览")
                if not url0 and not url0_failed: pending.append("PDF批注")
                if not url1 and not url1_failed: pending.append("Excel明细")
                if not pending:
                    break
                sys.stderr.write("对比导出链接未就绪(%s)，%ds 后重试 (%d/%d)...\n" % (
                    "/".join(pending), retry_delay, attempt, max_attempts - 1))
                time.sleep(retry_delay)

            if not web_url:
                r = call_api("DescribeContractDiffTaskWebUrl", {"TaskId": task_id})
                sys.stderr.write("[对比链接] WebUrl 响应: %s\n" % json.dumps(r, ensure_ascii=False))
                web_url = r.get("Response", {}).get("WebUrl", "")

            # Export endpoints need server-side generation time — skip on attempt 0
            # so the server has at least retry_delay seconds before first request.
            if attempt > 0:
                if not url0 and not url0_failed:
                    url0, retry = _fetch_export_url(
                        "ExportContractComparisonTask",
                        {"TaskId": task_id, "ExportType": 0},
                        "ResourceUrl", "对比PDF批注(ExportType=0)")
                    if not retry:
                        url0_failed = True
                if not url1 and not url1_failed:
                    url1, retry = _fetch_export_url(
                        "ExportContractComparisonTask",
                        {"TaskId": task_id, "ExportType": 1},
                        "ResourceUrl", "对比Excel明细(ExportType=1)")
                    if not retry:
                        url1_failed = True

            all_done = web_url and (url0 or url0_failed) and (url1 or url1_failed)
            if all_done:
                break

        # 导出文件自动下载（在线预览链接保留展示）；失败静默回退为链接文案
        # 文件名规则：原文件名_对比报告 / 原文件名_差异明细；未传文件名时回退 对比任务_<任务ID前缀>
        base = _sanitize_filename(base_name) if base_name else "对比任务_%s" % task_id[:12]
        dl0, err0 = _download_file(url0, base + "_对比报告", default_ext=".pdf") if url0 else (None, None)
        dl1, err1 = _download_file(url1, base + "_差异明细", default_ext=".xlsx") if url1 else (None, None)
        if err0:
            sys.stderr.write("[WARN] 对比批注报告自动下载失败: %s\n" % err0)
        if err1:
            sys.stderr.write("[WARN] 对比差异明细自动下载失败: %s\n" % err1)

        links = [
            "📊 [在线预览对比结果](%s)（3 小时内有效）" % web_url
                if web_url else "📊 在线预览对比结果：获取失败，请选择「刷新链接」重试",
            _format_export_line(
                url0, dl0,
                "📝 [下载带批注的结果文件（PDF）](%s)（20 分钟内有效）",
                "📝 批注报告（PDF）已下载到本地：`%s`（请前往该目录查看）",
                "📝 下载带批注的结果文件（PDF）：获取失败，请选择「刷新链接」重试"),
            _format_export_line(
                url1, dl1,
                "📋 [下载差异明细（Excel）](%s)（20 分钟内有效）",
                "📋 差异明细（Excel）已下载到本地：`%s`（请前往该目录查看）",
                "📋 下载差异明细（Excel）：获取失败，请选择「刷新链接」重试"),
        ]

        result["_links_block"] = _links_block(links)
        downloaded = [p for p in (dl0, dl1) if p]
        if downloaded:
            result["_downloaded_files"] = downloaded
    except Exception as e:
        sys.stderr.write("[ERROR] 获取对比链接异常 (task_id=%s): %s\n" % (task_id, str(e)))
    result["_next_steps"] = (
        "你可以：\n"
        "- **a. 审查新版合同** — 对修改后的版本进行风险审查\n"
        "- **b. 刷新链接** — 重新获取预览和下载链接（链接过期时使用）\n"
        "- **c. 查看对比记录** — 对历史合同对比任务进行查看"
    )
    out(result)


def cmd_review_progress_url(task_id):
    """Get the in-progress WebUrl for a review task and return a pre-formatted link."""
    result = call_api("DescribeContractReviewWebUrl", {"TaskId": task_id})
    web_url = result.get("Response", {}).get("WebUrl", "")
    if web_url:
        out({"success": True, "_links_md": "[点击这里](%s) 实时查看进度" % web_url})
    else:
        out({"success": False, "_links_md": "", "detail": result})


def cmd_compare_progress_url(task_id):
    """Get the in-progress WebUrl for a comparison task and return a pre-formatted link."""
    result = call_api("DescribeContractDiffTaskWebUrl", {"TaskId": task_id})
    web_url = result.get("Response", {}).get("WebUrl", "")
    if web_url:
        out({"success": True, "_links_md": "[点击这里](%s) 实时查看进度" % web_url})
    else:
        out({"success": False, "_links_md": "", "detail": result})


def cmd_review_list_url():
    """Get the review task list page URL and return a pre-formatted link."""
    result = call_api("DescribeContractReviewTaskListWebUrl", {})
    if "error" in result:
        out({"success": False, "_links_md": "", "error": result["error"]})
        return
    resp = result.get("Response", {})
    if "Error" in resp:
        out({"success": False, "_links_md": "", "error": resp["Error"]})
        return
    web_url = resp.get("WebUrl", "")
    if web_url:
        out({"success": True, "_links_md": "您可立即[点击链接](%s)，进入腾讯电子签，查看您的合同审查历史记录🌹" % web_url})
    else:
        out({"success": False, "_links_md": "", "detail": result})


def cmd_compare_list_url():
    """Get the comparison task list page URL and return a pre-formatted link."""
    result = call_api("DescribeContractDiffTaskListWebUrl", {})
    if "error" in result:
        out({"success": False, "_links_md": "", "error": result["error"]})
        return
    resp = result.get("Response", {})
    if "Error" in resp:
        out({"success": False, "_links_md": "", "error": resp["Error"]})
        return
    web_url = resp.get("WebUrl", "")
    if web_url:
        out({"success": True, "_links_md": "您可立即[点击链接](%s)，进入腾讯电子签，查看您的合同对比历史记录🌹" % web_url})
    else:
        out({"success": False, "_links_md": "", "detail": result})


def cmd_search_laws(params_json):
    """Call DescribeRiskIdentificationLawDocuments and return pre-formatted Markdown results."""
    try:
        params = json.loads(params_json)
    except Exception as e:
        out({"error": "JSON 解析失败: %s" % str(e)})
        sys.exit(1)

    result = call_api("DescribeRiskIdentificationLawDocuments", params)
    if "error" in result:
        out(result)
        sys.exit(1)

    response = result.get("Response", {})
    if "Error" in response:
        out(result)
        sys.exit(1)

    total = response.get("Total", 0)
    docs = response.get("DocumentList", [])
    shown = len(docs)

    results_list = []
    for doc in docs:
        title = doc.get("Title", "")
        law_no = doc.get("LawNo", "")
        href = doc.get("Href", "")
        segments = doc.get("HighlightSegmentList", [])[:3]

        title_md = "**📜 [%s](%s)**" % (title, href) if href else "**📜 %s**" % title

        seg_lines = []
        for seg in segments:
            seg_type = seg.get("SegmentType", "")
            text = seg.get("Text", "")
            seg_lines.append("**%s**：%s" % (seg_type, text))

        results_list.append({
            "title_md": title_md,
            "law_no": law_no,
            "segments": seg_lines,
        })

    out({
        "success": True,
        "total": total,
        "shown": shown,
        "_results_list": results_list,
        "_next_steps": (
            "你可以：\n"
            "- **a. 继续查看更多结果** — 加载下一页\n"
            "- **b. 缩小范围重新检索** — 提供更具体的关键词\n"
            "- **c. 将相关法条应用到合同** — 基于检索结果起草或审查合同"
        ),
    })


def cmd_review_links(task_id):
    """Fetch all download/preview links for a completed review task and return a ready-to-paste block."""
    link_items, downloaded = _get_review_links(task_id)
    data = {"success": True, "_links_block": _links_block(link_items)}
    if downloaded:
        data["_downloaded_files"] = downloaded
    out(data)


def cmd_compare_links(task_id, max_attempts=6, retry_delay=10, base_name=None):
    """Fetch all three comparison links with retry.

    Only retries endpoints that have not yet returned a URL.
    Stops retrying an endpoint immediately when the server returns a business error.
    Always returns exactly 3 lines.
    """
    web_url = ""
    url0 = ""
    url1 = ""
    url0_failed = False
    url1_failed = False

    for attempt in range(max_attempts):
        if attempt > 0:
            pending = []
            if not web_url: pending.append("在线预览")
            if not url0 and not url0_failed: pending.append("PDF批注")
            if not url1 and not url1_failed: pending.append("Excel明细")
            if not pending:
                break
            sys.stderr.write("对比链接未就绪(%s)，%ds 后重试 (%d/%d)...\n" % (
                "/".join(pending), retry_delay, attempt, max_attempts - 1))
            time.sleep(retry_delay)

        if not web_url:
            r = call_api("DescribeContractDiffTaskWebUrl", {"TaskId": task_id})
            sys.stderr.write("[对比链接] WebUrl 响应: %s\n" % json.dumps(r, ensure_ascii=False))
            web_url = r.get("Response", {}).get("WebUrl", "")

        if not url0 and not url0_failed:
            url0, retry = _fetch_export_url(
                "ExportContractComparisonTask",
                {"TaskId": task_id, "ExportType": 0},
                "ResourceUrl", "对比PDF批注(ExportType=0)")
            if not retry:
                url0_failed = True

        if not url1 and not url1_failed:
            url1, retry = _fetch_export_url(
                "ExportContractComparisonTask",
                {"TaskId": task_id, "ExportType": 1},
                "ResourceUrl", "对比Excel明细(ExportType=1)")
            if not retry:
                url1_failed = True

        if web_url and (url0 or url0_failed) and (url1 or url1_failed):
            break

    # 导出文件自动下载（在线预览链接保留展示）；失败静默回退为链接文案
    # 文件名规则：原文件名_对比报告 / 原文件名_差异明细；未传文件名时回退 对比任务_<任务ID前缀>
    base = _sanitize_filename(base_name) if base_name else "对比任务_%s" % task_id[:12]
    dl0, err0 = _download_file(url0, base + "_对比报告", default_ext=".pdf") if url0 else (None, None)
    dl1, err1 = _download_file(url1, base + "_差异明细", default_ext=".xlsx") if url1 else (None, None)
    if err0:
        sys.stderr.write("[WARN] 对比批注报告自动下载失败: %s\n" % err0)
    if err1:
        sys.stderr.write("[WARN] 对比差异明细自动下载失败: %s\n" % err1)

    links = [
        "📊 [在线预览对比结果](%s)（3 小时内有效）" % web_url
            if web_url else "📊 在线预览对比结果：获取失败，请选择「刷新链接」重试",
        _format_export_line(
            url0, dl0,
            "📝 [下载带批注的结果文件（PDF）](%s)（20 分钟内有效）",
            "📝 批注报告（PDF）已下载到本地：`%s`（请前往该目录查看）",
            "📝 下载带批注的结果文件（PDF）：获取失败，请选择「刷新链接」重试"),
        _format_export_line(
            url1, dl1,
            "📋 [下载差异明细（Excel）](%s)（20 分钟内有效）",
            "📋 差异明细（Excel）已下载到本地：`%s`（请前往该目录查看）",
            "📋 下载差异明细（Excel）：获取失败，请选择「刷新链接」重试"),
    ]

    data = {"success": True, "_links_block": _links_block(links)}
    downloaded = [p for p in (dl0, dl1) if p]
    if downloaded:
        data["_downloaded_files"] = downloaded
    out(data)


# ---------------------------------------------------------------------------
# Output / main
# ---------------------------------------------------------------------------

def out(data):
    try:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    except (TypeError, ValueError):
        print(json.dumps({"error": "输出序列化失败", "raw": str(data)}, ensure_ascii=False, indent=2))


def print_usage():
    usage = """腾讯电子签合同AI工具

用法: python3 scripts/tencent_esign.py <command> [args...]

导出文件自动下载:
    合同/批注/摘要/对比报告等导出文件在链接获取成功后立即下载到技能目录 downloads/，
    JSON 输出的 _downloaded_files 字段为本地路径列表（下载失败回退为原链接输出）。

鉴权:
    auth-check                          检查 Token 是否已配置
    auth-save   <token>                 保存 Token（跳过验证）
    auth-validate <token>               验证并保存 Token

文件:
    upload <file...>                    上传文件(支持多个，逐个上传)，返回 ResourceId

API 调用:
    call <action> '<json_params>'       调用任意 API（action 为接口名）

轮询等待:
    wait-draft   <task_id>              等待起草任务完成（Status 2=成功 3=失败），返回结果含 _links_md
    wait-review  <task_id>              等待单个审查任务完成（Status 4=成功 5=失败）
    wait-compare <task_id> [原文件名]    等待对比任务完成（Status 2=成功 3=失败），自动下载报告到 ./downloads/（文件名：原文件名_对比报告/差异明细，未传时回退 对比任务_<任务ID前缀>）
    review-batch '<["id1","id2",...]>'  轮询多个审查任务并一次性返回所有结果和链接（多文件审查必须用此命令）

链接获取（返回 _links_md，可直接粘贴到回复中）:
    review-links          <task_id>    获取已完成审查任务的预览/下载链接
    compare-links         <task_id> [原文件名]  获取已完成对比任务的预览/下载链接并自动下载（文件名规则同 wait-compare）
    review-progress-url   <task_id>    获取审查进行中的实时查看链接
    compare-progress-url  <task_id>    获取对比进行中的实时查看链接

法律检索（返回 _results_md，含格式化结果和带超链接的原文链接）:
    search-laws '<json>'               调用法条检索并返回格式化结果

其他:
    version                             显示版本信息

调用示例:
    python3 scripts/tencent_esign.py auth-check
    python3 scripts/tencent_esign.py upload /path/to/contract.pdf /path/to/another.pdf
    python3 scripts/tencent_esign.py call CreateBatchContractReviewTask '{"ResourceIds":["yDxxx"],"PolicyType":0}'
    python3 scripts/tencent_esign.py wait-review yDxxxTaskId
"""
    print(usage)


def main():
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "version":
        cfg = load_config()
        out({"name": cfg.get("name", "tencent-esign-contract"), "version": cfg.get("version", "unknown")})
        sys.exit(0)
    elif cmd == "auth-check":
        cmd_auth_check()
    elif cmd == "auth-save":
        if len(sys.argv) < 3:
            out({"error": "缺少 token 参数"})
            sys.exit(1)
        cmd_auth_save(sys.argv[2])
    elif cmd == "auth-validate":
        if len(sys.argv) < 3:
            out({"error": "缺少 token 参数"})
            sys.exit(1)
        cmd_auth_validate(sys.argv[2])
    elif cmd == "upload":
        if len(sys.argv) < 3:
            out({"error": "缺少文件路径参数"})
            sys.exit(1)
        cmd_upload(sys.argv[2:])
    elif cmd == "call":
        if len(sys.argv) < 4:
            out({"error": "用法: call <action> '<json_params>'"})
            sys.exit(1)
        cmd_call(sys.argv[2], sys.argv[3])
    elif cmd == "wait-draft":
        if len(sys.argv) < 3:
            out({"error": "缺少 task_id"})
            sys.exit(1)
        is_revision = "--revision" in sys.argv[3:]
        cmd_wait_draft(sys.argv[2], is_revision=is_revision)
    elif cmd == "wait-review":
        if len(sys.argv) < 3:
            out({"error": "缺少 task_id"})
            sys.exit(1)
        # Parse optional --limit N and --offset N
        rv_limit = 10
        rv_offset = 0
        args_rest = sys.argv[3:]
        for i, a in enumerate(args_rest):
            if a == "--limit" and i + 1 < len(args_rest):
                try: rv_limit = int(args_rest[i + 1])
                except ValueError: pass
            elif a == "--offset" and i + 1 < len(args_rest):
                try: rv_offset = int(args_rest[i + 1])
                except ValueError: pass
        cmd_wait_review(sys.argv[2], limit=rv_limit, offset=rv_offset)
    elif cmd == "review-batch":
        if len(sys.argv) < 3:
            out({"error": "缺少 task_ids JSON 数组"})
            sys.exit(1)
        names_arg = sys.argv[3] if len(sys.argv) >= 4 else None
        cmd_review_batch(sys.argv[2], names_json=names_arg)
    elif cmd == "wait-compare":
        if len(sys.argv) < 3:
            out({"error": "缺少 task_id"})
            sys.exit(1)
        cmd_wait_compare(sys.argv[2], base_name=(sys.argv[3] if len(sys.argv) >= 4 else None))
    elif cmd == "review-links":
        if len(sys.argv) < 3:
            out({"error": "缺少 task_id"})
            sys.exit(1)
        cmd_review_links(sys.argv[2])
    elif cmd == "compare-links":
        if len(sys.argv) < 3:
            out({"error": "缺少 task_id"})
            sys.exit(1)
        cmd_compare_links(sys.argv[2], base_name=(sys.argv[3] if len(sys.argv) >= 4 else None))
    elif cmd == "review-progress-url":
        if len(sys.argv) < 3:
            out({"error": "缺少 task_id"})
            sys.exit(1)
        cmd_review_progress_url(sys.argv[2])
    elif cmd == "compare-progress-url":
        if len(sys.argv) < 3:
            out({"error": "缺少 task_id"})
            sys.exit(1)
        cmd_compare_progress_url(sys.argv[2])
    elif cmd == "review-list-url":
        cmd_review_list_url()
    elif cmd == "compare-list-url":
        cmd_compare_list_url()
    elif cmd == "search-laws":
        if len(sys.argv) < 3:
            out({"error": "缺少 json 参数"})
            sys.exit(1)
        cmd_search_laws(sys.argv[2])
    else:
        out({"error": "未知命令: " + cmd})
        print_usage()
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.stderr.write("\n操作已取消\n")
        sys.exit(130)
    except Exception as e:
        out({"error": "未预期的异常: %s" % str(e)})
        sys.exit(1)
