#!/usr/bin/env python3
"""环境检查模块。"""
from __future__ import annotations

import os
import platform
import re
import sys

from utils import ConfigError, get_platform


def _try_restore_app_key() -> dict | None:
    """尝试从持久化配置中恢复 SCRM_APP_KEY。

    当环境变量中没有 SCRM_APP_KEY 时，从 shell profile（Unix/macOS）
    或注册表（Windows）中读取之前通过 set-app-key 写入的值。

    Returns:
        找到时返回 {"source": str, "app_key": str, "profile": str}，未找到返回 None。
    """
    system = platform.system()

    if system == "Windows":
        import subprocess
        try:
            result = subprocess.run(
                ["reg", "query", "HKCU\\Environment", "/v", "SCRM_APP_KEY"],
                capture_output=True, text=True,
            )
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    line = line.strip()
                    if "SCRM_APP_KEY" in line:
                        value = line.split("REG_SZ")[-1].strip()
                        if value:
                            os.environ["SCRM_APP_KEY"] = value
                            return {"source": "registry", "app_key": value}
        except OSError:
            pass
        return None

    # Unix/macOS：从 shell profile 文件中提取
    home = os.path.expanduser("~")
    shell = os.environ.get("SHELL", "")
    candidates = []
    if "zsh" in shell:
        candidates = [os.path.join(home, ".zshrc"), os.path.join(home, ".zprofile")]
    elif "bash" in shell:
        candidates = [os.path.join(home, ".bashrc"), os.path.join(home, ".bash_profile")]
    candidates.append(os.path.join(home, ".profile"))

    pattern = re.compile(r"""^export\s+SCRM_APP_KEY=['"]?(.+?)['"]?\s*$""", re.MULTILINE)

    for target in candidates:
        if not os.path.exists(target):
            continue
        try:
            with open(target, "r", encoding="utf-8") as f:
                content = f.read()
            match = pattern.search(content)
            if match:
                app_key = match.group(1)
                os.environ["SCRM_APP_KEY"] = app_key
                return {"source": "profile", "profile": target, "app_key": app_key}
        except OSError:
            continue

    return None


def run_check_env() -> dict:
    """检查 SCRM Skill 运行前置条件。"""
    checks = {
        "python_version": {
            "ok": sys.version_info >= (3, 9),
            "detail": sys.version.split()[0],
        },
        "platform": {"ok": True, "detail": get_platform()},
        "app_key": {
            "ok": bool(os.getenv("SCRM_APP_KEY", "").strip()),
            "detail": "已配置" if os.getenv("SCRM_APP_KEY", "").strip() else "未配置 SCRM_APP_KEY",
        },
        "image_host_upload_url": {
            "ok": True,
            "detail": "已内置本地图片上传接口，仅影响本地图片上传场景",
        },
    }

    # app_key 环境变量为空时，尝试从持久化配置中恢复
    app_key_restored = None
    if not checks["app_key"]["ok"]:
        app_key_restored = _try_restore_app_key()
        if app_key_restored:
            checks["app_key"] = {
                "ok": True,
                "detail": f"从持久化配置中恢复（{app_key_restored['source']}）",
            }

    if not checks["python_version"]["ok"] or not checks["app_key"]["ok"]:
        raise ConfigError("环境检查失败", details={"checks": checks})

    result = {
        "checks": checks,
        "notes": [
            "用户ID通过 personal_access_token 接口自动获取并缓存，无需额外查询。",
            "海报来源是本地图片时，会自动调用内置上传接口获取 COS 地址。",
        ],
    }

    # 如果是从持久化配置恢复的，附带恢复信息供 AI 执行 export
    if app_key_restored:
        result["app_key_restored"] = app_key_restored
        result["export_hint"] = f"export SCRM_APP_KEY='{app_key_restored['app_key']}'"

    return result
