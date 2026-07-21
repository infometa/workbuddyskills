# -*- coding: utf-8 -*-
"""tencent-musician-skills 内部工具：获取 tme-header-token

设计：
    本 Skill 已内嵌完整登录能力（check_login.py / login.py /
    get_token_from_browser.py），不依赖任何外部 skill、不再读取
    `TME_HEADER_TOKEN` 环境变量。

获取逻辑：
    直接调用同目录 `check_login.py`，由它负责：
        缓存 ~/.tme-login/token.json  （秒级命中，99% 场景）
         → storage_state.json 无头刷新
         → 有头扫码登录（login.py）
         → 手动粘贴兜底

对外接口：
    get_tme_header_token() -> str
        成功返回 token（非空字符串），失败抛出 RuntimeError
"""
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
CHECK_LOGIN_SCRIPT = SCRIPT_DIR / "check_login.py"


def _eprint(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def get_tme_header_token(allow_interactive: bool = True) -> str:
    """获取 tme-header-token

    Args:
        allow_interactive: 是否允许触发有头扫码登录
            - True（默认）：缓存失效时会弹 Chromium 让用户扫码
            - False：传 --no-login，只走缓存 + 无头刷新，失败直接报错

    Returns:
        非空的 token 字符串

    Raises:
        RuntimeError: 无法获取有效 token
    """
    if not CHECK_LOGIN_SCRIPT.exists():
        raise RuntimeError(
            f"check_login.py 缺失：{CHECK_LOGIN_SCRIPT}\n"
            f"本 skill 部署不完整，请重新拉取 skill"
        )

    cmd = [sys.executable, str(CHECK_LOGIN_SCRIPT)]
    if not allow_interactive:
        cmd.append("--no-login")

    try:
        # stderr 透传给用户（check_login.py 的进度提示有用）
        # stdout 捕获拿 token 本体
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=None,
            text=True,
            timeout=600,  # 有头扫码给 10 分钟
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError("调用 check_login.py 超时")
    except Exception as e:
        raise RuntimeError(f"调用 check_login.py 失败: {e}")

    if result.returncode != 0:
        raise RuntimeError(
            "check_login.py 获取 Token 失败，请根据上方提示操作（重新登录 / 检查 Playwright 安装）"
        )

    out = (result.stdout or "").strip()
    if not out:
        raise RuntimeError("check_login.py 未返回 Token")

    # check_login.py 约定：stdout 最后一行是 token 本体
    return out.splitlines()[-1].strip()