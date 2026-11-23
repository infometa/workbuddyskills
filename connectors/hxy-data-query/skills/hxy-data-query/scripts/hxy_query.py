#!/usr/bin/env python3
"""沪小游技能的只读调用入口，仅使用 Python 3.8+ 标准库。"""

import argparse
import http.client
import json
import os
import re
import socket
import ssl
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

VERSION = "2.0.1"
ENDPOINT = "https://travelwork-api.bawutech.com/open/api/mcp"
PROTOCOLS = ("2025-11-25", "2025-06-18")
REQUEST_LIMIT = 64 * 1024
RESPONSE_LIMIT = 4 * 1024 * 1024
TIMEOUT = 30


class SkillError(Exception):
    def __init__(self, error_code, message, code=400):
        self.result = {"errorCode": error_code, "message": message, "code": code}
        super().__init__(message)


class ArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        # 不回显错误的命令行参数，避免用户误将密钥作为参数时泄露。
        raise SkillError("INVALID_ARGUMENT", "命令或参数无效，请运行 --help 查看用法。")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise SkillError("REDIRECT_BLOCKED", "服务地址发生重定向，已停止发送凭证。", 502)


def parse_json(raw):
    def object_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError()
            result[key] = value
        return result

    def invalid_constant(value):
        raise ValueError()

    return json.loads(raw, object_pairs_hook=object_pairs, parse_constant=invalid_constant)


def credentials(file_name):
    """只读取显式指定的配置或环境变量，不搜索其他应用的凭证。"""
    if file_name:
        try:
            path = Path(file_name).expanduser()
            if os.name == "posix" and path.stat().st_mode & 0o077:
                raise SkillError("CONFIG_INVALID", "凭证文件仅允许本人访问，请先设置文件权限为 600。")
            with path.open("rb") as stream:
                raw = stream.read(8193)
            if len(raw) > 8192:
                raise ValueError()
            config = parse_json(raw)
            key, secret = config.get("tenantKey"), config.get("tenantSecret")
        except (OSError, ValueError, AttributeError, RecursionError):
            raise SkillError("CONFIG_INVALID", "无法读取凭证文件，请检查路径与 JSON 格式。") from None
    else:
        key, secret = os.environ.get("TENANT_KEY"), os.environ.get("TENANT_SECRET")
    if not key or not secret:
        raise SkillError("AUTH_REQUIRED", "请配置 TENANT_KEY 和 TENANT_SECRET，或通过 --credentials-file 指定凭证文件。", 401)
    if any(not isinstance(v, str) or len(v) > 1024
           or any(ord(c) < 33 or ord(c) > 126 for c in v) for v in (key, secret)):
        raise SkillError("CONFIG_INVALID", "租户凭证格式无效，请检查是否包含空格或换行。")
    return key, secret


def read_arguments(raw):
    if raw == "-":
        raw = sys.stdin.read(REQUEST_LIMIT + 1)
    if len(raw.encode("utf-8")) > REQUEST_LIMIT:
        raise SkillError("INVALID_ARGUMENT", "查询参数超过 64KB 限制。")

    try:
        value = parse_json(raw)
        if not isinstance(value, dict):
            raise ValueError()
        return value
    except (ValueError, RecursionError):
        raise SkillError("INVALID_ARGUMENT", "查询参数必须是有效 JSON 对象，不能包含重复键或非有限数值。") from None


def response_message(response, request_id):
    """兼容 JSON 和 SSE 响应，只消费当前请求，不开启订阅或自动重试。"""
    content_type = response.headers.get_content_type()
    if content_type == "application/json":
        body = response.read(RESPONSE_LIMIT + 1)
        if len(body) > RESPONSE_LIMIT:
            raise SkillError("RESPONSE_TOO_LARGE", "响应过大，请缩小查询范围。", 502)
        return parse_json(body)
    if content_type != "text/event-stream":
        raise SkillError("PROTOCOL_ERROR", "服务返回了不支持的响应格式。", 502)
    size, data, deadline = 0, [], time.monotonic() + TIMEOUT
    while time.monotonic() < deadline:
        line = response.readline(RESPONSE_LIMIT + 1 - size)
        size += len(line)
        if size > RESPONSE_LIMIT:
            raise SkillError("RESPONSE_TOO_LARGE", "响应过大，请缩小查询范围。", 502)
        text = line.decode("utf-8").rstrip("\r\n")
        if not text and data:
            message = parse_json("\n".join(data))
            data = []
            if isinstance(message, dict) and message.get("id") == request_id:
                return message
        elif text.startswith("data:"):
            data.append(text[5:].lstrip(" "))
        if not line:
            break
    raise SkillError("PROTOCOL_ERROR", "未收到完整查询结果，请稍后重试。", 502)


class McpClient:
    def __init__(self, key, secret):
        self.headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream",
                        "X-Tenant-Key": key, "X-Tenant-Secret": secret}
        try:
            context = ssl.create_default_context()
            # macOS 独立安装的 Python 可能未附带 CA；仅补用系统可信证书，保留显式配置。
            if sys.platform == "darwin" and not os.environ.get("SSL_CERT_FILE") \
                    and not os.environ.get("SSL_CERT_DIR") and ssl.get_default_verify_paths().cafile is None:
                system_ca = Path("/etc/ssl/cert.pem")
                if system_ca.is_file():
                    context.load_verify_locations(cafile=str(system_ca))
        except OSError:
            raise SkillError("TLS_ERROR", "无法加载可信 CA，请检查 Python 证书配置。", 503) from None
        self.opener = urllib.request.build_opener(NoRedirect(), urllib.request.HTTPSHandler(context=context))
        self.sequence = 0

    def post(self, method, params, notification=False):
        self.sequence += 1
        request_id = self.sequence
        body = {"jsonrpc": "2.0", "method": method, "params": params}
        if not notification:
            body["id"] = request_id
        try:
            encoded = json.dumps(body, ensure_ascii=False, allow_nan=False).encode("utf-8")
        except (ValueError, RecursionError):
            raise SkillError("INVALID_ARGUMENT", "请求包含无法编码的值或嵌套过深。") from None
        if len(encoded) > REQUEST_LIMIT:
            raise SkillError("INVALID_ARGUMENT", "完整请求超过 64KB 限制。")
        request = urllib.request.Request(ENDPOINT, data=encoded, headers=self.headers, method="POST")
        try:
            with self.opener.open(request, timeout=TIMEOUT) as response:
                if notification:
                    if response.status != 202:
                        raise SkillError("PROTOCOL_ERROR", "服务未接受初始化通知。", 502)
                    return None
                message = response_message(response, request_id)
                session = response.headers.get("Mcp-Session-Id")
                if method == "initialize" and session:
                    if not all(33 <= ord(c) <= 126 for c in session):
                        raise SkillError("PROTOCOL_ERROR", "服务返回了无效会话。", 502)
                    self.headers["Mcp-Session-Id"] = session
        except urllib.error.HTTPError as error:
            messages = {401: ("AUTHENTICATION_FAILED", "租户凭证无效或已失效，请核对配置。"),
                        403: ("ACCESS_DENIED", "服务拒绝访问，请核对租户状态及授权。"),
                        429: ("RATE_LIMITED", "查询繁忙，请稍后重试。")}
            reason, message = messages.get(error.code, ("HTTP_ERROR", "服务请求失败，请稍后重试。"))
            error.close()
            raise SkillError(reason, message, error.code) from None
        except urllib.error.URLError as error:
            if isinstance(error.reason, ssl.SSLCertVerificationError):
                raise SkillError("TLS_ERROR", "证书验证失败，请为当前 Python 配置可信 CA；不要关闭证书校验。", 503) from None
            if isinstance(error.reason, (socket.timeout, TimeoutError)):
                raise SkillError("NETWORK_TIMEOUT", "查询超时，请稍后重试。", 504) from None
            raise SkillError("NETWORK_ERROR", "无法连接沪小游服务，请检查网络后重试。", 503) from None
        except (socket.timeout, TimeoutError):
            raise SkillError("NETWORK_TIMEOUT", "查询超时，请稍后重试。", 504) from None
        except http.client.HTTPException:
            raise SkillError("NETWORK_ERROR", "网络连接中断，未取得完整结果。", 503) from None
        except (ValueError, UnicodeError, RecursionError):
            raise SkillError("PROTOCOL_ERROR", "服务未返回有效的 JSON 查询结果。", 502) from None
        if not isinstance(message, dict) or message.get("jsonrpc") != "2.0" \
                or type(message.get("id")) is not int or message["id"] != request_id:
            raise SkillError("PROTOCOL_ERROR", "服务响应与当前请求不匹配。", 502)
        if "error" in message:
            raise SkillError("PROTOCOL_ERROR", "服务拒绝 MCP 请求，请核对服务版本与调用参数。", 502)
        if not isinstance(message.get("result"), dict):
            raise SkillError("PROTOCOL_ERROR", "服务响应缺少查询结果。", 502)
        return message["result"]

    def call(self, tool, arguments):
        initialized = self.post("initialize", {"protocolVersion": PROTOCOLS[0], "capabilities": {},
                                               "clientInfo": {"name": "hxy-skill", "version": VERSION}})
        version = initialized.get("protocolVersion")
        capabilities = initialized.get("capabilities")
        if version not in PROTOCOLS or not isinstance(capabilities, dict) or "tools" not in capabilities:
            raise SkillError("PROTOCOL_ERROR", "服务协议版本或工具能力不兼容，请更新接入包。", 502)
        self.headers["MCP-Protocol-Version"] = version
        self.post("notifications/initialized", {}, notification=True)
        result = self.post("tools/call", {"name": tool, "arguments": arguments})
        data = result.get("structuredContent")
        if not isinstance(data, dict) or not isinstance(result.get("isError"), bool):
            raise SkillError("PROTOCOL_ERROR", "服务未返回预期的结构化结果，请核对 MCP 版本。", 502)
        return {"isError": result["isError"], "result": data}


def main():
    parser = ArgumentParser(description="沪小游只读查询；凭证通过环境变量或显式文件提供，不接受命令行密钥。")
    parser.add_argument("--credentials-file", help="包含 tenantKey/tenantSecret 的私有 JSON 文件；优先于环境变量")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor", help="离线检查凭证是否已配置；不验证凭证有效性、不访问网络")
    sub.add_parser("resources", help="读取当前租户授权资源")
    describe = sub.add_parser("describe", help="读取 1–10 个资源的参数、授权及示例")
    describe.add_argument("resource_codes", nargs="+")
    query = sub.add_parser("query", help="按原 MCP 参数查询，输出只包含服务端已授权数据")
    query.add_argument("--request-json", required=True, help="hxy_query 的 JSON 参数对象；- 表示从标准输入读取")
    secrets = ()
    try:
        args = parser.parse_args()
        arguments = {}
        tool = "hxy_list_resources"
        if args.command == "describe":
            if not 1 <= len(args.resource_codes) <= 10 or any(
                    not re.fullmatch(r"[a-z][a-z0-9]*(\.[a-z0-9]+){1,4}", code) for code in args.resource_codes):
                raise SkillError("INVALID_ARGUMENT", "请提供 1–10 个有效的资源标识。")
            tool, arguments = "hxy_describe_resource", {"resourceCodes": args.resource_codes}
        elif args.command == "query":
            tool, arguments = "hxy_query", read_arguments(args.request_json)
        secrets = credentials(args.credentials_file)
        if args.command == "doctor":
            output = {"isError": False, "result": {"configured": True, "authenticated": False,
                      "message": "本地凭证格式检查通过；请运行 resources 验证连接和实际授权。", "version": VERSION}}
        else:
            output = McpClient(*secrets).call(tool, arguments)
    except SkillError as error:
        output = {"isError": True, "result": error.result}
    except (OSError, ValueError):
        output = {"isError": True, "result": {"errorCode": "CLIENT_ERROR", "code": 500,
                  "message": "本地运行失败，请检查 Python 环境与配置。"}}
    def redact(value):
        if isinstance(value, str):
            for secret in secrets:
                value = value.replace(secret, "[REDACTED]")
        elif isinstance(value, dict):
            value = {key: redact(item) for key, item in value.items()}
        elif isinstance(value, list):
            value = [redact(item) for item in value]
        return value

    print(json.dumps(redact(output), ensure_ascii=False, allow_nan=False))
    return 1 if output["isError"] else 0


if __name__ == "__main__":
    sys.exit(main())
