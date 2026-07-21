"""
私域领券工具（huisheng-coupon-tool）- 版本校验脚本
用法：python version_check.py
说明：向远端接口校验当前 Skill 版本是否为最新，版本校验地址待补充。
      此脚本当前不执行版本检查逻辑，仅占位，后续有接口地址后再补充。
"""

import json

# TODO: 版本校验接口地址，待补充
VERSION_CHECK_URL = ""

# 当前 Skill 版本号
CURRENT_VERSION = "1.0.0"


def check_version():
    """
    向远端接口校验当前版本是否为最新。
    VERSION_CHECK_URL 为空时跳过校验，直接返回 skip 状态。
    """
    if not VERSION_CHECK_URL:
        print(json.dumps({
            "status": "skip",
            "message": "版本校验地址未配置，跳过校验"
        }, ensure_ascii=False))
        return

    # TODO: 补充实际校验逻辑
    # import httpx
    # resp = httpx.get(VERSION_CHECK_URL, params={"version": CURRENT_VERSION}, timeout=10)
    # ...
    pass


if __name__ == "__main__":
    check_version()
