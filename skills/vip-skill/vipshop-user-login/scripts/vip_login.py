#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
唯品会扫码登录主模块

整合二维码获取、展示、状态轮询和Cookie管理的完整登录流程。

API接口信息：
- 初始化二维码: POST https://passport.vip.com/qrLogin/initQrLogin
- 获取二维码图片: GET https://passport.vip.com/qrLogin/getQrImage?qrToken=xxx
- 轮询状态: POST https://passport.vip.com/qrLogin/checkStatus
"""

import sys
import time
import os
import argparse
import json
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass
from pathlib import Path

# 设置 stdout 编码为 UTF-8，解决 Windows 下中文显示问题
if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

import requests

# 导入子模块
from token_manager import TokenManager, TokenInfo
from qr_code_client import QRCodeClient
from status_poller import StatusPoller, LoginStatus, StatusResult
from mars_cid_generator import get_mars_cid  # AI-Generated: 导入 mars_cid 生成器
import logger  # AI-Generated: 导入日志上报模块

import re  # AI-Generated: 导入正则表达式模块

from packaging.version import parse as parse_version  # 版本号比较


# =============================================================================
# 配置参数
# =============================================================================


class Config:
    """配置类"""

    # Skill 版本号（兜底值，当接口未返回 version 时使用）
    DEFAULT_VERSION = "1.0.0"

    # API 基础配置
    BASE_URL = "https://passport.vip.com"
    INIT_QR_ENDPOINT = "/qrLogin/initQrLogin"
    GET_QR_IMAGE_ENDPOINT = "/qrLogin/getQrImage"
    CHECK_STATUS_ENDPOINT = "/qrLogin/checkStatus"

    # 轮询配置
    POLL_INTERVAL = 1  # 轮询间隔（秒），建议每秒轮询一次
    POLL_TIMEOUT = 180  # 轮询超时时间（秒），二维码有效期3分钟

    # 二维码配置
    SHOW_IN_TERMINAL = False  # 是否在终端显示二维码（False则打开图片）

    # 交互模式配置
    NON_BLOCKING_MODE = True  # 默认使用非阻塞模式（发送二维码后不等待，直接结束）


# =============================================================================
# VIP 登录管理器
# =============================================================================


@dataclass
class LoginResult:
    """登录结果"""

    success: bool
    message: str = ""
    qr_token: Optional[str] = None
    redirect_url: Optional[str] = None


class VIPLoginManager:
    """VIP登录管理器 - 整合完整登录流程"""

    def __init__(self, config: Optional[Config] = None):
        """
        初始化登录管理器

        Args:
            config: 配置对象，默认使用内置Config
        """
        self.config = config or Config()

        # 创建共享session以保持Cookie会话
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Referer": f"{self.config.BASE_URL}/",
                "Origin": self.config.BASE_URL,
                "Content-Type": "application/x-www-form-urlencoded",  # AI-Generated: 必须设置
            }
        )

        mars_cid = get_mars_cid()
        self.session.cookies.set("mars_cid", mars_cid, domain=".vip.com")

        # 初始化各模块，传入共享session
        self.qr_client = QRCodeClient(
            base_url=self.config.BASE_URL,
            init_endpoint=self.config.INIT_QR_ENDPOINT,
            image_endpoint=self.config.GET_QR_IMAGE_ENDPOINT,
            session=self.session,
        )

        self.status_poller = StatusPoller(
            base_url=self.config.BASE_URL,
            check_endpoint=self.config.CHECK_STATUS_ENDPOINT,
            poll_interval=self.config.POLL_INTERVAL,
            timeout=self.config.POLL_TIMEOUT,
            session=self.session,
        )

        self.token_manager = TokenManager()

    # AI-Generated Begin
    def _emit_qr_stdout_payload(self, qr_token: str, qr_url: str):
        """输出机器可读的二维码负载，避免智能体误提取 qrToken。"""
        payload = json.dumps(
            {
                "qrToken": qr_token,
                "qrImageUrl": qr_url,
            },
            ensure_ascii=False,
        )
        print("\n[VIPSHOP_QR_TOKEN_BEGIN]")
        print(qr_token)
        print("[VIPSHOP_QR_TOKEN_END]")
        print("[VIPSHOP_QR_URL_BEGIN]")
        print(qr_url)
        print("[VIPSHOP_QR_URL_END]")
        print("[VIPSHOP_QR_PAYLOAD_BEGIN]")
        print(payload)
        print("[VIPSHOP_QR_PAYLOAD_END]")
    # AI-Generated End

    def _validate_qr_token_format(self, qr_token: str) -> bool:
        """校验 qrToken 格式是否正确

        正确格式如：10000-098f1e2676a54ef0bbdb43e18c6ef84a
        模式：数字-32位十六进制字符串
        """
        if not qr_token:
            return False
        # 匹配模式：数字前缀-32位十六进制
        pattern = r"^\d+-[a-f0-9]{32}$"
        return bool(re.match(pattern, qr_token, re.IGNORECASE))

    def login(
        self,
        where_from: str = "",
        show_qr_callback: Optional[Callable] = None,
        status_callback: Optional[Callable[[str], None]] = None,
        send_qr_to_user_callback: Optional[Callable[[bytes, str], None]] = None,
        qr_token_to_poll: Optional[str] = None,
        blocking_mode: Optional[bool] = None,
    ) -> LoginResult:
        """
        执行完整的扫码登录流程

        Args:
            where_from: 请求来源标识（可选）
            show_qr_callback: 显示二维码的回调函数
            status_callback: 状态变更回调函数
            send_qr_to_user_callback: 发送二维码图片给用户的回调函数，接收(image_bytes, image_format)
                                     提供此回调时，发送完图片后脚本会直接结束，不会进入轮询
            qr_token_to_poll: 指定要轮询的qrToken（用于继续之前的登录流程）
            blocking_mode: 是否使用阻塞模式（轮询等待登录完成），None则使用Config.NON_BLOCKING_MODE默认值

        Returns:
            登录结果
        """
        # 如果提供了 qr_token_to_poll，先校验格式
        if qr_token_to_poll:
            if not self._validate_qr_token_format(qr_token_to_poll):
                logger.error(
                    "invalid_qr_token_format",
                    qr_token=qr_token_to_poll,
                    reason="格式不正确，期望：数字-32位十六进制",
                )
                return LoginResult(
                    success=False,
                    message=f"qrToken 格式不正确: {qr_token_to_poll}，请检查参数",
                )

            print("=" * 60)
            print("唯品会扫码登录 - 继续轮询")
            print("=" * 60)
            # AI-Generated: 记录继续轮询事件
            logger.info(
                "continue_poll", qr_token=qr_token_to_poll, where_from=where_from
            )
            return self._poll_and_complete(
                qr_token_to_poll, where_from, status_callback
            )

        print("=" * 60)
        print("唯品会扫码登录")
        print("=" * 60)

        # AI-Generated: 记录登录开始
        logger.info("login_start", where_from=where_from)

        # 步骤1: 初始化二维码（带重试）
        max_retries = 3
        qr_token = None
        init_data = None

        for attempt in range(max_retries):
            print(f"\n[1/3] 正在获取登录二维码... (尝试 {attempt + 1}/{max_retries})")
            success, qr_token, init_data = self.qr_client.init_qr_code(
                where_from=where_from
            )

            if not success or not qr_token:
                if attempt < max_retries - 1:
                    print(f"[1/3] 获取失败，{attempt + 1}秒后重试...")
                    time.sleep(attempt + 1)
                    continue
                else:
                    # AI-Generated: 记录初始化失败
                    logger.error(
                        "init_qr_login_failed",
                        error_msg=str(init_data),
                        where_from=where_from,
                    )
                    return LoginResult(
                        success=False, message=f"获取二维码失败: {init_data}"
                    )

            # 校验 qr_token 格式
            if not self._validate_qr_token_format(qr_token):
                print(f"[1/3] ✗ qrToken格式不正确: {qr_token}")
                if attempt < max_retries - 1:
                    print(f"[1/3] 正在重试...")
                    time.sleep(1)
                else:
                    logger.error(
                        "init_qr_login_invalid_format",
                        qr_token=qr_token,
                        where_from=where_from,
                    )
                    return LoginResult(
                        success=False,
                        message=f"获取二维码失败: 返回的qrToken格式不正确",
                    )
            else:
                # AI-Generated: 记录初始化成功
                logger.info(
                    "init_qr_login_success", qr_token=qr_token, where_from=where_from
                )
                print(f"[1/3] ✓ 获取qrToken成功")
                break

        # 步骤2: 获取并展示二维码
        print("\n[2/3] 正在获取二维码图片...")
        success, image_bytes, image_format = self.qr_client.get_qr_image(
            qr_token=qr_token
        )

        if not success or not image_bytes:
            # AI-Generated: 记录获取二维码图片失败
            logger.error(
                "get_qr_image_failed", qr_token=qr_token, where_from=where_from
            )
            # AI-Generated: 删除有问题的备用方案，直接报错
            return LoginResult(success=False, message="获取二维码图片失败，请稍后重试")

        # 保存二维码图片到文件（供 OpenClaw 读取发送）
        qr_file_path = self.qr_client.save_qr_image(image_bytes, image_format)

        # 展示二维码
        if show_qr_callback:
            show_qr_callback(image_bytes, image_format)
        elif self.config.SHOW_IN_TERMINAL:
            self.qr_client.display_qr_in_terminal(image_bytes)
        else:
            self.qr_client.open_qr_image(image_bytes, image_format)

        # 获取二维码链接
        qr_url = self.qr_client.get_qr_image_url(qr_token)

        # OpenClaw 环境：尝试发送图片 + 打印链接
        if os.environ.get("OPENCLAW_SESSION") == "1" and qr_file_path:
            print(f"\n[OPENCLAW_SEND_FILE]{qr_file_path}[/OPENCLAW_SEND_FILE]")

        self._emit_qr_stdout_payload(qr_token, qr_url)

        # 所有平台都打印二维码链接（AI 智能体应提取此链接以 Markdown 图片展示）
        print(f"\n🔗 二维码链接: {qr_url}")
        print(f"\n📱 请使用唯品会APP扫描上方二维码完成登录")
        print(f"\n💡 提示：点击链接可在浏览器中打开二维码")
        print(
            f"\n🔑 扫码确认后，使用命令: python scripts/vip_login.py --poll {qr_token}"
        )

        # 确定是否使用阻塞模式
        use_blocking = (
            blocking_mode
            if blocking_mode is not None
            else not self.config.NON_BLOCKING_MODE
        )

        # 非阻塞模式：发送二维码后直接结束（不轮询）
        if not use_blocking:
            # 如果有send_qr_to_user_callback，调用它发送二维码
            if send_qr_to_user_callback:
                print("\n[2/3] 正在发送二维码给用户...")
                send_qr_to_user_callback(image_bytes, image_format)
                print("[2/3] ✓ 二维码已发送给用户")

            print(f"\n[3/3] 请使用唯品会APP扫描二维码")
            print(f"      扫码确认后，使用以下命令完成登录：")
            print(f"      python scripts/vip_login.py --poll {qr_token}")

            # 保存qrToken以便后续轮询
            self._save_pending_login(qr_token, where_from)

            # 非阻塞模式，直接返回
            return LoginResult(
                success=True,
                message="二维码已发送，请扫码确认后使用 --poll 参数继续",
                qr_token=qr_token,
            )

        # 阻塞模式：继续轮询
        # 如果有send_qr_to_user_callback，发送二维码给用户
        if send_qr_to_user_callback:
            print("\n[2/3] 正在发送二维码给用户...")
            send_qr_to_user_callback(image_bytes, image_format)
            print("[2/3] ✓ 二维码已发送给用户")

        print("[2/3] ✓ 请使用唯品会APP扫描二维码")

        # 步骤3: 轮询状态
        print("\n[3/3] 等待扫码确认...")

        def on_status_change(result: StatusResult):
            if status_callback:
                status_callback(f"状态: {result.message}")

        def on_scanned(result: StatusResult):
            print(f"\n[3/3] ✓ 用户已扫码")
            print("[3/3] 等待用户确认登录...")

        def on_confirmed(result: StatusResult):
            print(f"\n[3/3] ✓ 登录已确认!")

        poll_result = self.status_poller.poll_until_complete(
            qr_token=qr_token,
            where_from=where_from,
            on_status_change=on_status_change,
            on_scanned=on_scanned,
            on_confirmed=on_confirmed,
        )

        # 检查轮询结果
        if poll_result.status != LoginStatus.CONFIRMED:
            message = poll_result.message
            if poll_result.status == LoginStatus.INVALID:
                message = "二维码已失效，请重新登录"

            # AI-Generated: 记录登录失败（主流程）
            logger.error(
                "login_failed_main",
                qr_token=qr_token,
                reason=message,
                status=str(poll_result.status),
            )
            return LoginResult(success=False, message=message, qr_token=qr_token)

        # 从登录确认响应中提取cookies (set-cookie headers)
        # 只保存必要的cookie：PASSPORT_ACCESS_TOKEN 和 mars_cid
        cookies = {}
        expires_at = 0.0  # PASSPORT_ACCESS_TOKEN 的过期时间戳

        if poll_result.raw_http_response is not None:
            # 从响应头中提取set-cookie (可能有多个)
            # 使用raw._original_response.headers.get_all获取多个Set-Cookie
            try:
                set_cookie_headers = poll_result.raw_http_response.raw._original_response.headers.get_all(
                    "Set-Cookie"
                )
            except AttributeError:
                # 如果不支持get_all，尝试用get获取单个
                set_cookie_header = poll_result.raw_http_response.headers.get(
                    "Set-Cookie", ""
                )
                set_cookie_headers = [set_cookie_header] if set_cookie_header else []

            for cookie_str in set_cookie_headers:
                if not cookie_str:
                    continue
                # 提取cookie名称和值 (第一个=前的部分和第一个=后的部分，直到;)
                if "=" in cookie_str:
                    parts = cookie_str.split(";")[0].split("=", 1)
                    if len(parts) == 2:
                        cookie_name, cookie_value = parts
                        cookie_name = cookie_name.strip()
                        # 只保存 PASSPORT_ACCESS_TOKEN
                        if cookie_name == "PASSPORT_ACCESS_TOKEN":
                            cookies[cookie_name] = cookie_value.strip()
                            # 解析 Max-Age
                            for attr in cookie_str.split(";"):
                                attr = attr.strip()
                                if attr.startswith("Max-Age="):
                                    try:
                                        max_age = int(attr.split("=", 1)[1])
                                        expires_at = time.time() + max_age
                                    except (ValueError, IndexError):
                                        pass
                                elif attr.startswith("Expires="):
                                    try:
                                        from email.utils import parsedate_to_datetime

                                        exp_str = attr.split("=", 1)[1]
                                        exp_dt = parsedate_to_datetime(exp_str)
                                        expires_at = exp_dt.timestamp()
                                    except Exception:
                                        pass

            # 同时获取session中的cookies，只保留 mars_cid
            session_cookies = self.session.cookies.get_dict()
            if "mars_cid" in session_cookies:
                cookies["mars_cid"] = session_cookies["mars_cid"]
        else:
            # 从session中获取，只保留必要的cookie
            session_cookies = self.session.cookies.get_dict()
            if "PASSPORT_ACCESS_TOKEN" in session_cookies:
                cookies["PASSPORT_ACCESS_TOKEN"] = session_cookies[
                    "PASSPORT_ACCESS_TOKEN"
                ]
            if "mars_cid" in session_cookies:
                cookies["mars_cid"] = session_cookies["mars_cid"]

        # 获取旧版本（用于版本检测提示）
        old_version = None
        old_token = self.token_manager.get_token()
        if old_token and hasattr(old_token, 'version'):
            old_version = old_token.version
        logger.info("version_check_prepare", source="complete_login", old_version=str(old_version), poll_result_version=str(poll_result.version), default_version=str(self.config.DEFAULT_VERSION))

        # 从响应中获取新版本（接口未返回时使用兜底值）
        new_version = poll_result.version or self.config.DEFAULT_VERSION

        # 先检查版本更新，确定最终写入的版本号
        update_ok = self._check_version_update(old_version, new_version)
        # 更新提示未处理时保留旧版本号，确保下次登录能再次触发提醒
        final_version = new_version if update_ok else (old_version or new_version)

        # 保存登录态（只包含必要的cookie）
        token_info = TokenInfo(
            cookies=cookies,
            user_id="",  # 不再保存用户ID
            nickname="",  # 不再保存昵称
            expires_at=expires_at,
            version=final_version,
        )

        # 保存到本地（单用户模式）
        self.token_manager.save_token("current_user", token_info)

        # 输出版本信息
        print(f"   当前版本: {final_version}")
        if not update_ok:
            print(f"   检测到可用新版本，请按受控发布流程手动更新；当前仍使用旧版本，下次登录将再次提醒")

        # 清理二维码文件
        self.qr_client.cleanup_qr_files()

        # AI-Generated: 记录登录成功
        logger.info("login_success", qr_token=qr_token)

        return LoginResult(
            success=True,
            message=f"登录成功，当前版本: {final_version}",
            qr_token=qr_token,
            redirect_url=poll_result.redirect_url,
        )

    def _save_pending_login(self, qr_token: str, where_from: str):
        """保存待处理的登录信息，以便后续轮询"""
        import json
        from pathlib import Path

        pending_file = Path.home() / ".vipshop-user-login" / "pending_login.json"
        pending_file.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "qr_token": qr_token,
            "where_from": where_from,
            "created_at": time.time(),
        }

        with open(pending_file, "w") as f:
            json.dump(data, f)

    def _load_pending_login(self) -> Optional[Dict[str, Any]]:
        """加载待处理的登录信息"""
        import json
        from pathlib import Path

        pending_file = Path.home() / ".vipshop-user-login" / "pending_login.json"

        if not pending_file.exists():
            return None

        try:
            with open(pending_file, "r") as f:
                data = json.load(f)

            # AI-Generated: 校验 qrToken 格式
            qr_token = data.get("qr_token", "")
            if not self._validate_qr_token_format(qr_token):
                print(f"[警告] pending 文件中的 qrToken 格式不正确: {qr_token}")
                logger.error(
                    "invalid_pending_qr_token",
                    qr_token=qr_token,
                    reason="从 pending_login.json 加载的 qrToken 格式不正确",
                )
                pending_file.unlink()
                return None

            # 检查是否过期（超过3分钟视为过期）
            if time.time() - data.get("created_at", 0) > 180:
                pending_file.unlink()
                return None

            return data
        except (json.JSONDecodeError, IOError):
            return None

    def _clear_pending_login(self):
        """清除待处理的登录信息"""
        from pathlib import Path

        pending_file = Path.home() / ".vipshop-user-login" / "pending_login.json"
        if pending_file.exists():
            pending_file.unlink()

    def _poll_and_complete(
        self,
        qr_token: str,
        where_from: str = "",
        status_callback: Optional[Callable[[str], None]] = None,
    ) -> LoginResult:
        """执行轮询和登录完成流程"""

        def on_status_change(result: StatusResult):
            if status_callback:
                status_callback(f"状态: {result.message}")

        def on_scanned(result: StatusResult):
            print(f"\n  ✓ 用户已扫码")
            print("  等待用户确认登录...")

        def on_confirmed(result: StatusResult):
            print(f"\n  ✓ 登录已确认!")

        print("\n[轮询] 正在检查登录状态...")

        poll_result = self.status_poller.poll_until_complete(
            qr_token=qr_token,
            where_from=where_from,
            on_status_change=on_status_change,
            on_scanned=on_scanned,
            on_confirmed=on_confirmed,
        )

        # 检查轮询结果
        if poll_result.status != LoginStatus.CONFIRMED:
            message = poll_result.message
            if poll_result.status == LoginStatus.INVALID:
                message = "二维码已失效，请重新登录"

            # AI-Generated: 记录登录失败（轮询流程）
            logger.error(
                "login_failed_poll",
                qr_token=qr_token,
                reason=message,
                status=str(poll_result.status),
            )
            return LoginResult(success=False, message=message, qr_token=qr_token)

        # 从登录确认响应中提取cookies
        # 只保存必要的cookie：PASSPORT_ACCESS_TOKEN 和 mars_cid
        cookies = {}
        expires_at = 0.0

        if poll_result.raw_http_response is not None:
            try:
                set_cookie_headers = poll_result.raw_http_response.raw._original_response.headers.get_all(
                    "Set-Cookie"
                )
            except AttributeError:
                set_cookie_header = poll_result.raw_http_response.headers.get(
                    "Set-Cookie", ""
                )
                set_cookie_headers = [set_cookie_header] if set_cookie_header else []

            for cookie_str in set_cookie_headers:
                if not cookie_str:
                    continue
                if "=" in cookie_str:
                    parts = cookie_str.split(";")[0].split("=", 1)
                    if len(parts) == 2:
                        cookie_name, cookie_value = parts
                        cookie_name = cookie_name.strip()
                        # 只保存 PASSPORT_ACCESS_TOKEN
                        if cookie_name == "PASSPORT_ACCESS_TOKEN":
                            cookies[cookie_name] = cookie_value.strip()
                            # 解析 Max-Age
                            for attr in cookie_str.split(";"):
                                attr = attr.strip()
                                if attr.startswith("Max-Age="):
                                    try:
                                        max_age = int(attr.split("=", 1)[1])
                                        expires_at = time.time() + max_age
                                    except (ValueError, IndexError):
                                        pass
                                elif attr.startswith("Expires="):
                                    try:
                                        from email.utils import parsedate_to_datetime

                                        exp_str = attr.split("=", 1)[1]
                                        exp_dt = parsedate_to_datetime(exp_str)
                                        expires_at = exp_dt.timestamp()
                                    except Exception:
                                        pass

            # 同时获取session中的cookies，只保留 mars_cid
            session_cookies = self.session.cookies.get_dict()
            if "mars_cid" in session_cookies:
                cookies["mars_cid"] = session_cookies["mars_cid"]
        else:
            # 从session中获取，只保留必要的cookie
            session_cookies = self.session.cookies.get_dict()
            if "PASSPORT_ACCESS_TOKEN" in session_cookies:
                cookies["PASSPORT_ACCESS_TOKEN"] = session_cookies[
                    "PASSPORT_ACCESS_TOKEN"
                ]
            if "mars_cid" in session_cookies:
                cookies["mars_cid"] = session_cookies["mars_cid"]

        # 获取旧版本（用于版本检测提示）
        old_version = None
        old_token = self.token_manager.get_token()
        if old_token and hasattr(old_token, 'version'):
            old_version = old_token.version
        logger.info("version_check_prepare", source="poll_login", old_version=str(old_version), poll_result_version=str(poll_result.version), default_version=str(self.config.DEFAULT_VERSION))

        # 从响应中获取新版本（接口未返回时使用兜底值）
        new_version = poll_result.version or self.config.DEFAULT_VERSION

        # 先检查版本更新，确定最终写入的版本号
        update_ok = self._check_version_update(old_version, new_version)
        # 更新提示未处理时保留旧版本号，确保下次登录能再次触发提醒
        final_version = new_version if update_ok else (old_version or new_version)

        # 保存登录态（只包含必要的cookie）
        token_info = TokenInfo(
            cookies=cookies,
            user_id="",  # 不再保存用户ID
            nickname="",  # 不再保存昵称
            expires_at=expires_at,
            version=final_version,
        )

        self.token_manager.save_token("current_user", token_info)
        self._clear_pending_login()
        self.qr_client.cleanup_qr_files()

        # 输出版本信息
        print(f"   当前版本: {final_version}")
        if not update_ok:
            print(f"   检测到可用新版本，请按受控发布流程手动更新；当前仍使用旧版本，下次登录将再次提醒")

        # 显示过期时间
        expire_readable = token_info.expire_datetime
        print(f"\n⏰ Token过期时间: {expire_readable}")

        return LoginResult(
            success=True,
            message=f"登录成功，当前版本: {final_version}",
            qr_token=qr_token,
            redirect_url=poll_result.redirect_url,
        )

    def _check_version_update(self, old_version: Optional[str], new_version: Optional[str]) -> bool:
        """
        检测版本变化并提示手动更新

        Args:
            old_version: 旧版本号
            new_version: 新版本号

        Returns:
            True 表示无需更新，False 表示检测到新版本且需要手动更新
        """
        logger.info("version_check_start", old_version=str(old_version), new_version=str(new_version))

        if not new_version:
            logger.warning("version_check_skip", reason="new_version为空")
            return True

        if not old_version:
            logger.info("version_check_skip", reason="old_version为空(新登录)")
            return True

        if old_version == new_version:
            logger.info("version_check_skip", reason=f"版本相同: {old_version}")
            return True

        try:
            old_ver = parse_version(old_version)
            new_ver = parse_version(new_version)
            logger.info("version_compare", old_parsed=str(old_ver), new_parsed=str(new_ver))
            if new_ver <= old_ver:
                logger.info("version_check_skip", reason=f"新版本未升级: {new_ver} <= {old_ver}")
                return True
        except Exception as error:
            logger.warning("version_parse_failed", error=str(error), fallback="字符串比较")
            if old_version == new_version:
                return True

        logger.info("version_update_manual_required", old_version=old_version, new_version=new_version)
        print(f"\n📢 检测到新版本: {old_version} -> {new_version}")
        print("   如需获取最新版本，请访问官方仓库：https://github.com/vipshop/vipshop-ai-skills")
        return False

    def quick_login(self, where_from: str = "") -> LoginResult:
        """
        快速登录 - 一键完成整个流程

        Args:
            where_from: 请求来源标识（可选）

        Returns:
            登录结果
        """
        return self.login(where_from=where_from)

    def get_stored_token(self, token_id: str) -> Optional[TokenInfo]:
        """
        获取已存储的token

        Args:
            token_id: Token标识

        Returns:
            Token信息
        """
        return self.token_manager.get_token(token_id)

    def list_logged_in_tokens(self):
        """列出所有已登录的token"""
        return self.token_manager.list_users()

    def print_login_summary(self):
        """打印登录状态摘要"""
        self.token_manager.print_all_tokens()


# =============================================================================
# 命令行接口
# =============================================================================


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="唯品会扫码登录工具（默认非阻塞模式）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python vip_login.py                    # 执行扫码登录（非阻塞，获取二维码后结束）
  python vip_login.py --blocking         # 阻塞模式（获取二维码后等待扫码完成）
  python vip_login.py --where-from xxx   # 指定请求来源
  python vip_login.py --list             # 列出已登录记录
  python vip_login.py --status           # 查看登录状态
  python vip_login.py --poll TOKEN       # 继续轮询指定qrToken
  python vip_login.py --continue         # 继续上次未完成的登录
        """,
    )

    parser.add_argument("--where-from", "-w", help="请求来源标识")
    parser.add_argument("--list", "-l", action="store_true", help="列出已登录的记录")
    parser.add_argument("--status", "-s", action="store_true", help="查看登录状态")
    parser.add_argument("--logout", metavar="TOKEN_ID", help="注销指定登录记录")
    parser.add_argument(
        "--terminal",
        "-t",
        action="store_true",
        help="在终端显示二维码（而不是打开图片）",
    )
    parser.add_argument(
        "--poll", metavar="QR_TOKEN", help="指定qrToken继续轮询登录状态"
    )
    parser.add_argument(
        "--continue",
        "-c",
        dest="continue_login",
        action="store_true",
        help="继续上次未完成的登录（从pending_login.json读取qrToken）",
    )
    parser.add_argument(
        "--blocking",
        "-b",
        action="store_true",
        help="使用阻塞模式（获取二维码后等待扫码完成，不立即结束）",
    )

    args = parser.parse_args()

    # 创建登录管理器
    config = Config()
    if args.terminal:
        config.SHOW_IN_TERMINAL = True
    if args.blocking:
        config.NON_BLOCKING_MODE = False

    manager = VIPLoginManager(config)

    # 处理命令
    if args.list:
        tokens = manager.list_logged_in_tokens()
        if tokens:
            print("已登录的记录:")
            for token in tokens:
                print(f"  - {token}")
        else:
            print("没有已登录的记录")
        return

    if args.status:
        manager.print_login_summary()
        return

    if args.logout:
        manager.token_manager.remove_token(args.logout)
        print(f"已注销: {args.logout}")
        return

    # 处理继续登录
    if args.continue_login:
        pending = manager._load_pending_login()
        if pending:
            print(f"继续登录流程，qrToken: {pending['qr_token'][:20]}...")
            # AI-Generated: 记录继续登录事件
            logger.info(
                "cli_continue_login",
                qr_token=pending["qr_token"],
                where_from=pending.get("where_from", "AIClaw"),
            )
            result = manager.login(
                where_from=pending.get("where_from", "AIClaw"),
                qr_token_to_poll=pending["qr_token"],
            )
        else:
            print("没有待处理的登录请求")
            logger.warning("cli_continue_login_no_pending")
            logger.flush()
            sys.exit(1)
    elif args.poll:
        # 使用指定的qrToken继续轮询
        # AI-Generated: 记录 --poll 参数使用
        logger.info(
            "cli_poll_login", qr_token=args.poll, where_from=args.where_from or "AIClaw"
        )
        result = manager.login(
            where_from=args.where_from or "AIClaw", qr_token_to_poll=args.poll
        )
    else:
        # 执行新的登录
        where_from = args.where_from or "AIClaw"
        result = manager.login(where_from=where_from)

    print("\n" + "=" * 60)
    if result.success:
        if result.message == "二维码已发送，请扫码确认后使用 --poll 参数继续":
            print(f"ℹ {result.message}")
            print(f"  qrToken: {result.qr_token}")
        else:
            print(f"✓ {result.message}")
    else:
        print(f"✗ 登录失败: {result.message}")
    print("=" * 60)

    # 等待所有日志上报完成，防止 daemon 线程被 sys.exit 杀死导致日志丢失
    logger.flush()

    sys.exit(0 if result.success else 1)


if __name__ == "__main__":
    main()
