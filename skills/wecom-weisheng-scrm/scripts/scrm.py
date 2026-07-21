#!/usr/bin/env python3
"""scrm.py - SCRM Skill CLI 主入口。

基于 wshoto-open 开放平台 Claw 模块，动态发现并调用可用业务接口。
所有业务接口通过通用代理 /claw/proxy/forward 调用，不在 Skill 中硬编码。

@author jzc
@date 2026-04-02 17:11
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

_scripts_dir = Path(__file__).parent
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))

from utils import ConfigError, SCRMError, ValidationError, force_utf8_output, output_error, output_success
from environment import run_check_env
from api_client import SCRMClient
from get_access_token import TokenManager
from identity_manager import IdentityManager
from claw_client import ClawClient
from chat_mode import save_chat_mode, CHAT_MODE_KEY, CHAT_MODE_ZONE
from file_utils import upload_image
from raw_fetcher import fetch_raw_text

force_utf8_output()


# ---------------------------------------------------------------------------
# 命令处理函数
# ---------------------------------------------------------------------------

def cmd_check_env(args, client=None):
    """检查运行环境。"""
    return run_check_env()


def cmd_set_app_key(args, client=None):
    """将 SCRM_APP_KEY 持久化写入用户环境（跨平台）。"""
    import platform

    app_key = args.app_key_value.strip()
    if not app_key:
        raise ValueError("APP_KEY 不能为空")

    system = platform.system()

    if system == "Windows":
        import subprocess
        subprocess.run(
            ["setx", "SCRM_APP_KEY", app_key],
            capture_output=True, text=True,
        )
        os.environ["SCRM_APP_KEY"] = app_key
        return {
            "platform": "Windows",
            "action": "setx",
            "note": "已通过 setx 写入用户环境变量，重新打开终端后生效",
        }

    # Unix/macOS：写入 shell profile
    home = os.path.expanduser("~")
    shell = os.environ.get("SHELL", "")
    candidates = []
    if "zsh" in shell:
        candidates = [os.path.join(home, ".zshrc"), os.path.join(home, ".zprofile")]
    elif "bash" in shell:
        candidates = [os.path.join(home, ".bashrc"), os.path.join(home, ".bash_profile")]
    candidates.append(os.path.join(home, ".profile"))

    target = next((f for f in candidates if os.path.exists(f)), candidates[0])

    export_line = f"export SCRM_APP_KEY='{app_key}'"
    export_pattern = re.compile(r"^export\s+SCRM_APP_KEY=.*$", re.MULTILINE)

    existing = ""
    if os.path.exists(target):
        with open(target, "r", encoding="utf-8") as f:
            existing = f.read()

    if export_pattern.search(existing):
        new_content = export_pattern.sub(export_line, existing)
        action_taken = "updated"
    else:
        new_content = existing.rstrip("\n") + f"\n\n# SCRM Skill 凭证\n{export_line}\n"
        action_taken = "appended"

    with open(target, "w", encoding="utf-8") as f:
        f.write(new_content)

    os.environ["SCRM_APP_KEY"] = app_key

    return {
        "platform": system,
        "profile": target,
        "action": action_taken,
        "note": f"已写入 {target}，重新打开终端后生效",
    }


def cmd_set_chat_mode(args, client=None):
    """配置会话归档模式。

    非交互模式下 --mode 为必填，不允许回退到交互式输入。
    """
    if not args.mode:
        raise ValidationError("非交互模式下 --mode 为必填，请通过 --mode <key|zone> 指定模式")
    save_chat_mode(args.mode)
    return {"mode": args.mode}


def cmd_check_identity(args, client):
    """获取用户身份信息（超管/分管/员工）。"""
    user_id = client.user_id
    identity_mgr = IdentityManager(client, user_id)
    result = identity_mgr.get_identity()
    return result


def cmd_list_apis(args, client):
    """从接口仓库匹配调用规则。"""
    claw = ClawClient(client)
    result = claw.get_api_list(keyword=args.keyword)
    return result


def cmd_call_api(args, client):
    """通过通用代理调用业务接口。"""
    claw = ClawClient(client)
    biz_params = json.loads(args.biz_params) if args.biz_params else {}
    # 在 args 上标记操作类型，供 main() 错误处理时使用
    args._write_operation = claw._is_write_operation(args.uri)
    result = claw.forward(
        service_name=args.service_name,
        uri=args.uri,
        method=args.method,
        biz_params=biz_params,
    )
    return result


def cmd_upload_image(args, client):
    """上传本地图片，返回公网 URL 和 file_id。"""
    path = Path(args.path).expanduser().resolve()
    if not path.exists() or not path.is_file():
        raise ValidationError(f"文件不存在：{path}")
    return upload_image(path, client=client)


def cmd_fetch_raw_doc(args, client=None):
    """读取受控远程文档原文。"""
    return fetch_raw_text(args.url, timeout=args.timeout, max_bytes=args.max_bytes)


# ---------------------------------------------------------------------------
# 子命令注册
# ---------------------------------------------------------------------------

def _add_base_subparsers(subparsers) -> None:
    """基础子命令。"""
    p = subparsers.add_parser("check-env", help="检查运行环境")
    p.set_defaults(handler=cmd_check_env, success_message="环境检查通过")

    p = subparsers.add_parser("set-app-key", help="将 SCRM_APP_KEY 持久化写入 shell profile")
    p.add_argument("app_key_value", help="APP_KEY 的值（personal_access_token）")
    p.set_defaults(handler=cmd_set_app_key, success_message="APP_KEY 已持久化")

    p = subparsers.add_parser(
        "set-chat-mode",
        help="配置会话归档模式（key=密钥模式 / zone=专区模式），配置一次后持久生效",
    )
    _add_argument_aliases(p, "--mode", choices=[CHAT_MODE_KEY, CHAT_MODE_ZONE], default=None,
                   help="key=密钥模式，zone=专区模式")
    p.set_defaults(handler=cmd_set_chat_mode, success_message="会话归档模式配置成功")

    p = subparsers.add_parser("fetch-raw-doc", help="受控读取远程文档原文，仅允许 open.wshoto.com")
    p.add_argument("--url", required=True, help="目标文档 URL")
    p.add_argument("--timeout", type=int, default=20, help="请求超时时间，默认 20 秒")
    p.add_argument("--max-bytes", type=int, default=2 * 1024 * 1024, help="最大读取字节数，默认 2097152")
    p.set_defaults(handler=cmd_fetch_raw_doc, success_message="远程文档读取成功")


def _add_claw_subparsers(subparsers) -> None:
    """Claw 动态接口相关子命令。"""
    p = subparsers.add_parser("check-identity", help="获取用户身份（超管/分管/员工）")
    p.set_defaults(handler=cmd_check_identity, success_message="用户身份获取成功")

    p = subparsers.add_parser("list-apis", help="通过关键词从接口仓库匹配调用规则")
    _add_argument_aliases(p, "--keyword", required=True,
                   help="逗号分隔的多个关键词，模糊匹配 api_name")
    p.set_defaults(handler=cmd_list_apis, success_message="接口匹配成功")

    p = subparsers.add_parser("call-api", help="通过通用代理调用业务接口")
    _add_argument_aliases(p, "--service-name", required=True,
                   help="下游服务名，如 wshoto-basebiz-service")
    p.add_argument("--uri", required=True,
                   help="下游接口 URI，如 /bff/bizCustomer/private/h5/customer/pageQuery")
    p.add_argument("--method", default="POST",
                   help="HTTP 方法，默认 POST")
    _add_argument_aliases(p, "--biz-params", default=None,
                   help="业务参数 JSON 字符串，如 '{\"currentIndex\":1,\"pageSize\":10}'")
    p.set_defaults(handler=cmd_call_api, success_message="接口调用成功")

    p = subparsers.add_parser("upload-image", help="上传本地图片，返回公网 URL 和 file_id")
    p.add_argument("--path", required=True, help="本地图片文件路径")
    p.set_defaults(handler=cmd_upload_image, success_message="图片上传成功")


def _add_argument_aliases(parser, name, **kwargs):
    """注册一个带连字符的参数，同时支持下划线格式的别名。

    例如 _add_argument_aliases(p, "--service-name", ...) 会同时注册
    --service-name 和 --service_name 作为同一个参数的两个 flag，
    两种写法都能正常使用，required 校验也都能正确生效。
    """
    prefix = "--" if name.startswith("--") else ""
    base = name.lstrip("-")
    alias_base = base.replace("-", "_")
    if alias_base != base:
        parser.add_argument(name, prefix + alias_base, **kwargs)
    else:
        parser.add_argument(name, **kwargs)


def build_parser() -> argparse.ArgumentParser:
    """构造命令行参数解析器。"""
    parser = argparse.ArgumentParser(
        prog="scrm",
        description="SCRM Skill CLI - 基于 Claw 模块动态发现并调用业务接口",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--app-key", help="覆盖环境变量 SCRM_APP_KEY")
    parser.add_argument("--base-url", default="", help="覆盖环境变量 SCRM_BASE_URL")

    subparsers = parser.add_subparsers(dest="action", metavar="ACTION")
    subparsers.required = True

    _add_base_subparsers(subparsers)
    _add_claw_subparsers(subparsers)

    return parser


def main() -> None:
    """程序入口。"""
    parser = build_parser()
    args = parser.parse_args()

    if args.app_key:
        os.environ["SCRM_APP_KEY"] = args.app_key
    if args.base_url:
        os.environ["SCRM_BASE_URL"] = args.base_url

    action = args.action
    try:
        # 不需要 client 的命令
        if action in ("check-env", "set-app-key", "set-chat-mode", "fetch-raw-doc"):
            result = args.handler(args)
            output_success(action, result, getattr(args, "success_message", "执行成功"))
            return

        # 需要 client 的命令：先做环境检查，再获取 token
        app_key = os.getenv("SCRM_APP_KEY")
        base_url = os.getenv("SCRM_BASE_URL", "https://open.wshoto.com")
        run_check_env()

        token_manager = TokenManager(app_key, base_url=base_url)
        access_token = token_manager.get_token()
        user_id = token_manager.get_user_id()
        client = SCRMClient(access_token, base_url=base_url, user_id=user_id)

        result = args.handler(args, client)
        output_success(action, result, getattr(args, "success_message", "执行成功"))
    except ValidationError as exc:
        output_error(action, "validation_error", str(exc),
                     details={**exc.details, "write_operation": getattr(args, "_write_operation", False)})
    except ConfigError as exc:
        output_error(action, "config_error", str(exc), details=exc.details)
    except SCRMError as exc:
        output_error(action, "scrm_error", str(exc),
                     details={**exc.details, "write_operation": getattr(args, "_write_operation", False)})
    except json.JSONDecodeError as exc:
        output_error(action, "json_error", f"JSON 解析失败：{exc}")
    except Exception as exc:
        output_error(action, "unexpected_error", f"执行失败：{exc}",
                     details={"write_operation": getattr(args, "_write_operation", False)})


if __name__ == "__main__":
    main()
