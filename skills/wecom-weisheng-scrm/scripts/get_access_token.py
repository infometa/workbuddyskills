#!/usr/bin/env python3
"""获取 SCRM Personal Access Token，包含自动缓存管理。"""
import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Optional

# 将 scripts 目录添加到 sys.path 以便导入模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils import force_utf8_output, output_error, output_success, ensure_dir
from api_client import fetch_personal_access_token, ApiError

force_utf8_output()

# 缓存文件路径
CACHE_DIR = Path(__file__).resolve().parent.parent / ".cache"
CACHE_FILE = CACHE_DIR / "access_token.json"


class TokenManager:
    """管理 Personal Access Token 的获取、缓存和刷新。"""

    def __init__(self, app_key: str, base_url: str = "https://open.wshoto.com") -> None:
        self.app_key = app_key
        self.base_url = base_url
        self.cache_file = CACHE_FILE

    def get_token(self, force_refresh: bool = False) -> str:
        """获取有效的 Access Token。

        策略：
        1. 如果 force_refresh 为 True，强制刷新。
        2. 尝试从缓存读取。
        3. 如果缓存存在且未过期（预留 5 分钟缓冲），返回缓存的 token。
        4. 否则，调用接口刷新 token 并更新缓存。
        """
        cached = self._load_cache()
        if not force_refresh:
            if cached and self._is_valid(cached):
                return cached["access_token"]

        return self._refresh_token()

    def get_user_id(self) -> Optional[str]:
        """获取缓存的用户 ID。"""
        cached = self._load_cache()
        if cached:
            return cached.get("user_id")
        return None

    def _load_cache(self) -> Optional[dict[str, Any]]:
        """加载缓存。"""
        if not self.cache_file.exists():
            return None
        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # 校验缓存是否属于当前 app_key
            if data.get("app_key") != self.app_key:
                return None
            return data
        except (OSError, json.JSONDecodeError):
            return None

    def _is_valid(self, cached: dict[str, Any]) -> bool:
        """检查缓存是否有效。"""
        expires_in = cached.get("expires_in", 7200)
        create_at = cached.get("create_at", 0)

        if create_at <= 0 or create_at > time.time() + 300:
            return False

        expire_time = create_at + expires_in

        # 预留 300 秒缓冲时间
        return time.time() < (expire_time - 300)

    def _refresh_token(self) -> str:
        """从服务器刷新 Token。"""
        data = fetch_personal_access_token(self.app_key, base_url=self.base_url)
        token = data.get("access_token")
        if not token:
            raise Exception("接口返回数据缺少 access_token")

        expires_in = data.get("expires_in", 7200)
        user_id = data.get("userId") or data.get("user_id")

        cache_data = {
            "app_key": self.app_key,
            "access_token": token,
            "expires_in": expires_in,
            "create_at": int(time.time()),
            "user_id": user_id,
        }

        self._save_cache(cache_data)
        return token

    def _save_cache(self, data: dict[str, Any]) -> None:
        """保存缓存。"""
        ensure_dir(self.cache_file.parent)
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except OSError:
            pass  # 忽略写入失败，降级为不缓存


def main():
    parser = argparse.ArgumentParser(description="获取 SCRM Personal Access Token")
    parser.add_argument("--app-key", help="个人 APP KEY (默认: 环境变量 SCRM_APP_KEY)")
    parser.add_argument("--base-url", help="API Base URL (默认: https://open.wshoto.com)")
    parser.add_argument("--raw", action="store_true", help="仅输出 access_token 字符串")
    parser.add_argument("--force-refresh", action="store_true", help="强制刷新 token（忽略缓存）")

    args = parser.parse_args()

    app_key = args.app_key or os.getenv("SCRM_APP_KEY")
    base_url = args.base_url or os.getenv("SCRM_BASE_URL", "https://open.wshoto.com")

    if not app_key:
        output_error("get_access_token", "missing_app_key", "缺少 app_key，请通过 --app-key 参数或 SCRM_APP_KEY 环境变量提供")
        return

    try:
        manager = TokenManager(app_key, base_url=base_url)
        token = manager.get_token(force_refresh=args.force_refresh)

        if args.raw:
            if token:
                print(token)
            else:
                sys.exit(1)
        else:
            cached = manager._load_cache()
            data = {
                "access_token": token,
                "user_id": cached.get("user_id") if cached else None,
                "cached": not args.force_refresh and cached is not None,
            }
            output_success("get_access_token", data, "获取 Access Token 成功")
    except ApiError as e:
        if args.raw:
            sys.exit(1)
        output_error("get_access_token", "api_error", str(e), details=e.details)
    except Exception as e:
        if args.raw:
            sys.exit(1)
        output_error("get_access_token", "unknown_error", f"发生未知错误: {e}")

if __name__ == "__main__":
    main()

