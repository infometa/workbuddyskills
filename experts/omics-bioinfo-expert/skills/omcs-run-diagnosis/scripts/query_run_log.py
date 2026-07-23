#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
组学平台 DescribeRunLogs 查询脚本（omcs-run-diagnosis Skill 专用）

通过 omics-platform-cli 认证，调用 /omics/api/cgi (JSON-RPC) 查询任务运行日志。

认证方式：
  1. 读取 ~/.omics-platform-cli/auth.json 中的 session_id
  2. 通过 /userinfo 接口自动获取当前用户 Uin
  3. 使用 session_id + uin 调用 RunService.DescribeRunLogs

用法:
  # 单任务模式（Uin 自动获取）
  python3 query_run_log.py --run-uuid <UUID>

  # 批次模式
  python3 query_run_log.py --run-group-id <GROUP_ID>

  # 手动指定 Uin（可选，覆盖自动获取的值）
  python3 query_run_log.py --run-uuid <UUID> --run-uin <UIN>

  # 手动指定环境
  python3 query_run_log.py --run-uuid <UUID> --env prod|dev
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import time
import urllib.request
import urllib.error
import uuid
from pathlib import Path

# ---------- 常量 ----------
OMICS_AUTH_FILE = Path.home() / ".omics-platform-cli" / "auth.json"

# 环境配置
ENVIRONMENTS = {
    "prod": {
        "name": "生产环境",
        "base_url": "https://omics.qq.com",
    },
    "dev": {
        "name": "测试环境",
        "base_url": "https://genomics.qq.com",
    },
}
DEFAULT_ENV = "prod"
OMICS_CGI_PATH = "/omics/api/cgi"


# ---------- omics CLI / 认证工具函数 ----------

def find_omics_cli() -> str | None:
    """查找 omics-platform-cli 可执行文件。返回路径或 None。"""
    for candidate in [
        os.path.expanduser("~/.local/bin/omics"),
        "/usr/local/bin/omics",
    ]:
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    return shutil.which("omics")


def install_omics_cli() -> str:
    """自动安装 omics-platform-cli。

    通过官方 install.sh 脚本安装，安装完成后再次查找并返回 CLI 路径。
    失败时抛 RuntimeError。
    """
    import subprocess
    import platform

    install_url = (
        "https://cnb.cool/tencenthealthcareomics/"
        "omics-platform-cli/-/raw/main/install.sh"
    )

    print("[安装] 正在安装 omics-platform-cli ...", file=sys.stderr)
    print(f"[安装] 安装脚本: {install_url}", file=sys.stderr)

    # 检测 curl 或 wget
    curl_cmd = shutil.which("curl")
    wget_cmd = shutil.which("wget")

    try:
        if curl_cmd:
            cmd = f"{curl_cmd} -fsSL {install_url} | bash"
            result = subprocess.run(
                ["bash", "-c", cmd],
                capture_output=True, text=True, timeout=120,
            )
        elif wget_cmd:
            cmd = f"{wget_cmd} -qO- {install_url} | bash"
            result = subprocess.run(
                ["bash", "-c", cmd],
                capture_output=True, text=True, timeout=120,
            )
        else:
            raise RuntimeError(
                "无法自动安装：系统缺少 curl 和 wget。\n"
                "请手动安装 omics-platform-cli：\n"
                f"  前往 Release 页面下载: https://cnb.cool/tencenthealthcareomics/omics-platform-cli/-/releases\n"
                f"  选择对应平台（darwin-arm64 / darwin-amd64 / linux-amd64）"
            )

        if result.returncode != 0:
            stderr = result.stderr.strip()[:300]
            raise RuntimeError(
                f"安装脚本执行失败 (exit code {result.returncode})。\n"
                f"错误输出: {stderr}\n"
                "请尝试手动安装：\n"
                f"  前往 Release 页面下载: https://cnb.cool/tencenthealthcareomics/omics-platform-cli/-/releases"
            )
    except subprocess.TimeoutExpired:
        raise RuntimeError(
            "安装超时（120秒），可能是网络问题。\n"
            "请尝试手动安装：\n"
            f"  前往 Release 页面下载: https://cnb.cool/tencenthealthcareomics/omics-platform-cli/-/releases"
        )

    # 安装完成后再次查找
    cli = find_omics_cli()
    if cli is None:
        # 可能安装到了新路径但当前 shell 的 PATH 未更新
        common_paths = [
            os.path.expanduser("~/.local/bin/omics"),
            "/usr/local/bin/omics",
        ]
        for p in common_paths:
            if os.path.isfile(p) and os.access(p, os.X_OK):
                cli = p
                break
        if cli is None:
            raise RuntimeError(
                "安装脚本执行成功，但未找到 omics 命令。\n"
                "可能需要重新打开终端或手动执行:\n"
                "  source ~/.bashrc  # 或 ~/.zshrc"
            )

    print(f"[安装] omics-platform-cli 安装成功: {cli}", file=sys.stderr)
    return cli


def read_omics_session() -> tuple[str, bool]:
    """读取 omics 登录态。
    返回 (session_id, is_valid):
      - session_id: 非空字符串 (若已登录且未过期)
      - is_valid: True 表示 session 存在且未过期
    """
    if not OMICS_AUTH_FILE.exists():
        return "", False
    try:
        auth = json.loads(OMICS_AUTH_FILE.read_text("utf-8"))
        session_id = auth.get("session_id", "")
        expires_at = auth.get("expires_at", 0)
        if not session_id:
            return "", False
        if expires_at > 0 and time.time() > expires_at:
            return session_id, False
        return session_id, True
    except (OSError, ValueError, KeyError):
        return "", False


def _http_json(url: str, method: str = "GET",
               headers: dict | None = None,
               cookies: dict | None = None,
               body: dict | None = None,
               timeout: int = 15) -> dict:
    """最小化的 HTTP JSON 请求（只用标准库）。"""
    data = json.dumps(body).encode("utf-8") if body else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    if cookies:
        cookie_str = "; ".join(f"{k}={v}" for k, v in cookies.items())
        req.add_header("Cookie", cookie_str)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {raw[:300]}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"网络请求失败: {exc.reason}") from exc


def get_user_uin(base_url: str, session_id: str) -> str:
    """调用 /userinfo 接口获取当前用户的 UIN。

    返回 uin 字符串。失败时抛异常。
    """
    url = base_url + "/userinfo"
    result = _http_json(url, headers={"X-Session-Id": session_id})
    uin = result.get("uin", "") or result.get("Uin", "")
    if not uin:
        # 尝试从 nickname 等字段提示
        raise RuntimeError(
            f"/userinfo 接口未返回 uin 字段，响应: {json.dumps(result, ensure_ascii=False)[:200]}\n"
            "请确认已登录正确的账号（执行 omics login）"
        )
    return str(uin)


def check_auth(base_url: str) -> tuple[str, str]:
    """统一认证流程：检查 CLI 安装 → 读取 session → 获取 uin。

    返回 (session_id, uin)。
    失败时抛 RuntimeError，包含友好的操作引导。
    """
    # 1. 检查 CLI 是否安装
    cli = find_omics_cli()
    if cli is None:
        raise RuntimeError(
            "omics-platform-cli 未安装。\n"
            "安装方式:\n"
            "  Linux/macOS: curl -fsSL https://cnb.cool/tencenthealthcareomics/"
            "omics-platform-cli/-/raw/main/install.sh | bash\n"
            "  或从 Release 页面下载: https://cnb.cool/tencenthealthcareomics/"
            "omics-platform-cli/-/releases\n"
            "安装后执行 omics login 完成登录授权。"
        )

    # 2. 读取登录态
    session_id, is_valid = read_omics_session()
    if not session_id:
        raise RuntimeError(
            "未检测到 omics 登录凭证 (~/.omics-platform-cli/auth.json)。\n"
            "请执行: omics login"
        )
    if not is_valid:
        raise RuntimeError(
            "omics 登录凭证已过期。\n"
            "请执行: omics login"
        )

    # 3. 获取用户 Uin
    uin = get_user_uin(base_url, session_id)
    return session_id, uin


# ---------- 日志查询 ----------

def query_run_logs(base_url: str, session_id: str, run_uin: str,
                   run_uuid: str = "", run_group_id: str = "") -> dict:
    """通过 /omics/api/cgi 调用 RunService.DescribeRunLogs。

    返回 JSON-RPC 响应的 result 字段。
    失败时抛 RuntimeError。
    """
    url = base_url + OMICS_CGI_PATH
    req_id = uuid.uuid4().hex[:22]

    params: dict = {"RunUin": run_uin}
    if run_uuid:
        params["RunUuid"] = run_uuid
    if run_group_id:
        params["RunGroupId"] = run_group_id

    payload = {
        "id": req_id,
        "jsonrpc": "2.0",
        "method": "RunService.DescribeRunLogs",
        "params": params,
    }

    result = _http_json(
        url,
        method="POST",
        headers={
            "X-Session-Id": session_id,
            "Origin": base_url,
            "Referer": base_url + "/platform/overview",
        },
        cookies={"omics_session": session_id},
        body=payload,
        timeout=30,
    )

    # JSON-RPC 错误处理
    if "error" in result:
        err = result["error"]
        err_msg = err.get("message", str(err)) if isinstance(err, dict) else str(err)
        if any(kw in err_msg for kw in ("401", "403", "session", "unauthorized", "Unauthorized")):
            raise RuntimeError(
                f"omics 登录凭证已失效 ({err_msg})。\n"
                "请执行: omics login"
            )
        raise RuntimeError(f"RunService.DescribeRunLogs 失败: {err_msg}")

    return result.get("result", {})


def main():
    import argparse

    parser = argparse.ArgumentParser(description="查询组学平台任务运行日志（通过 omics-platform-cli 认证）")
    parser.add_argument("--run-uuid", default="", help="RunUuid（单任务模式必填，与 --run-group-id 至少传一个）")
    parser.add_argument("--run-group-id", default="", help="RunGroupId（批次模式必填，与 --run-uuid 至少传一个；同时传时服务端按 RunGroupId 走）")
    parser.add_argument("--run-uin", default="", help="任务所属用户 Uin（可选，默认自动从 /userinfo 获取当前登录用户的 Uin）")
    parser.add_argument("--env", choices=["prod", "dev"], default=DEFAULT_ENV, help=f"环境（默认 {DEFAULT_ENV}）")
    args = parser.parse_args()

    if not args.run_uuid and not args.run_group_id:
        parser.error("--run-uuid 与 --run-group-id 至少要传一个")

    env = ENVIRONMENTS[args.env]
    base_url = env["base_url"]

    # --- 认证 ---
    try:
        session_id, auto_uin = check_auth(base_url)
    except RuntimeError as exc:
        print(json.dumps({"error": str(exc), "action": "login"}, ensure_ascii=False, indent=2))
        sys.exit(1)

    # 用户手动指定 --run-uin 时覆盖自动获取的值
    run_uin = args.run_uin or auto_uin

    print(f"[认证] session_id: ***{session_id[-6:] if len(session_id) > 6 else '***'}", file=sys.stderr)
    print(f"[认证] Uin: {run_uin} ({'手动指定' if args.run_uin else '自动获取'})", file=sys.stderr)
    print(f"[环境] {env['name']} ({base_url})", file=sys.stderr)

    # --- 查询日志 ---
    try:
        rsp = query_run_logs(
            base_url=base_url,
            session_id=session_id,
            run_uin=run_uin,
            run_uuid=args.run_uuid,
            run_group_id=args.run_group_id,
        )

        # 判断是否有有效结果
        logs = rsp.get("Logs")
        if logs:
            output = {
                "environment": env["name"],
                "base_url": base_url,
                "run_uin": run_uin,
                "response": rsp,
            }
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print(json.dumps({
                "environment": env["name"],
                "base_url": base_url,
                "message": "该环境未找到该任务的日志",
                "response": rsp,
            }, ensure_ascii=False, indent=2))
            sys.exit(1)

    except RuntimeError as exc:
        err_msg = str(exc)
        action = "login" if "login" in err_msg else "unknown"
        print(json.dumps({"error": err_msg, "action": action}, ensure_ascii=False, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
