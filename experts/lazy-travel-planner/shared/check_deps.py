#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_deps.py · 懒人出游规划师 · 数据源可用性探测器（迁移版）

原始 OpenClaw 包里引用了 shared/check_deps.py（提供 check_or_block /
check_all / get_active_sources），但原包并未随附该文件。本文件是迁移到
WorkBuddy 专家包时补齐的可运行桩（stub），目的是：

  1. 让所有 import check_deps 的脚本（orchestrate.py / geo_fanout.py /
     build_itinerary.py / render_html.py）都能正常 import，不崩溃；
  2. 把"数据源是否就绪"的判断交给**环境变量 / 标记文件**，由 agent
     在运行时按真实可用的连接器和工具翻转；
  3. 默认全部为 False（灰 / 静态兜底），正好触发 agent 设计好的
     "优雅降级"行为——缺数据时用 WebSearch + references/ 兜底，并在
     HTML 行程书里透明标 🟡⚪。

判定来源（任一满足即视为 ok）：
  meituan_travel  : 环境变量 MEITUAN_TRAVEL_OK=1
                     或标记文件 <专家根>/data/.meituan_ok
  xhs_logged_in  : 环境变量 XHS_LOGGED_IN_OK=1
                     或标记文件 <专家根>/data/.xhs_ok
  qweather         : 环境变量 QWEATHER_OK=1
                     或标记文件 <专家根>/data/.qweather_ok
  websearch       : 恒为 True（WorkBuddy 内置联网搜索是最后防线）

严格模式（可选）：设置环境变量 LTP_STRICT_DEPS=1 后，
  check_or_block(name) 会在该数据源不可用时直接 sys.exit(2) 阻塞流程
  （复刻原"block"语义）；默认（不设置）只打印 stderr 警告并放行，
  保证流水线能跑通、让下游兜底逻辑接管。
"""

import os
import sys
from pathlib import Path


def _expert_root() -> Path:
    """check_deps.py 位于 <专家根>/shared/check_deps.py，回退两级即根。"""
    return Path(__file__).resolve().parent.parent


def _flag(name: str) -> Path:
    return _expert_root() / "data" / name


def _is_ok(env_key: str, flag_file: str) -> bool:
    if os.environ.get(env_key, "").strip() == "1":
        return True
    if _flag(flag_file).exists():
        return True
    return False


def meituan_ok() -> bool:
    return _is_ok("MEITUAN_TRAVEL_OK", ".meituan_ok")


def xhs_ok() -> bool:
    return _is_ok("XHS_LOGGED_IN_OK", ".xhs_ok")


def qweather_ok() -> bool:
    return _is_ok("QWEATHER_OK", ".qweather_ok")


def check_or_block(name: str) -> bool:
    """探测某数据源是否就绪。

    返回 True 表示放行。默认仅告警不阻塞；LTP_STRICT_DEPS=1
    时，不可用的数据源会直接 sys.exit(2)（复刻原 block 语义）。
    """
    ok = {
        "meituan_travel": meituan_ok,
        "xhs": xhs_ok,
        "xhs_logged_in": xhs_ok,
        "qweather": qweather_ok,
    }.get(name, lambda: False)()

    if ok:
        return True

    print(
        f"[check_deps] ⚠️ 数据源未就绪：{name}。"
        f"agent 应改用 WebSearch / references/ 静态知识兜底，"
        f"并在产物里标 🟡⚪ 降级。",
        file=sys.stderr,
    )
    if os.environ.get("LTP_STRICT_DEPS", "").strip() == "1":
        print(
            f"[check_deps] ❌ STRICT 模式：{name} 不可用，流程终止 (exit 2)。"
            f"配置好后重跑。",
            file=sys.stderr,
        )
        sys.exit(2)
    return True


def check_all() -> dict:
    """orchestrate.py 用：返回各数据源的 ok 状态字典。"""
    return {
        "meituan_travel": {"ok": meituan_ok()},
        "xhs_logged_in": {"ok": xhs_ok()},
    }


def get_active_sources() -> dict:
    """render_html.py 用：返回数据完整性面板需要的布尔字典。"""
    return {
        "meituan_travel": meituan_ok(),
        "xhs_logged_in": xhs_ok(),
        "qweather": qweather_ok(),
        "websearch": True,
    }


if __name__ == "__main__":
    print(json.dumps(get_active_sources(), ensure_ascii=False, indent=2))
