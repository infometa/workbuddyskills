#!/usr/bin/env python3
"""权限白名单预检查脚本。

用途：检查 .codebuddy/settings.json 中的权限白名单是否存在、是否与
      permissions-allowlist.yaml 保持一致。

输出：JSON 格式，包含 status 和 missing 字段。
  - status: "missing" | "outdated" | "current"
  - missing: 缺失的权限条目列表

示例：
  python3 check_permissions.py                           # 使用默认路径
  python3 check_permissions.py --allowlist /path/to/allowlist.yaml
"""

import json
import os
import pathlib


def check_permissions(settings_path: str, allowlist_path: str) -> dict:
    """检查权限白名单：是否存在 + 是否与最新白名单条目一致。"""
    if not os.path.exists(settings_path):
        return {"status": "missing", "missing": []}

    try:
        with open(settings_path, encoding="utf-8") as f:
            settings = json.load(f)
        current_perms = settings.get("permissions", {}).get("allow", [])

        # 核心 4 项存在性检查
        has_core = (
            any("index_db" in p for p in current_perms)
            and any("merge_findings" in p for p in current_perms)
            and any("ts_parser" in p for p in current_perms)
            and any(".codebuddy/security-scan/runs" in p for p in current_perms)
        )
        if not has_core:
            return {"status": "missing", "missing": []}

        # 从 allowlist 中解析预期的权限列表
        expected_perms = []
        with open(allowlist_path, encoding="utf-8") as f:
            in_allow = False
            for line in f:
                stripped = line.strip()
                if stripped == "permissions_allow:":
                    in_allow = True
                elif stripped.startswith("permissions_deny:"):
                    in_allow = False
                elif in_allow and stripped.startswith('- "'):
                    rule = stripped[3:]  # 去掉 '- "'
                    rule = rule.split('"')[0]  # 取引号内内容
                    expected_perms.append(rule)

        # 通过条目内容比对判断是否一致
        current_set = set(current_perms)
        missing = [p for p in expected_perms if p not in current_set]

        if missing:
            return {
                "status": "outdated",
                "missing": missing,
            }

        return {"status": "current", "missing": []}
    except Exception:
        return {"status": "missing", "missing": []}


def main():
    # 默认 allowlist 路径：脚本同级目录的上层 resource/permissions-allowlist.yaml
    plugin_root = os.environ.get(
        "CODEBUDDY_PLUGIN_ROOT",
        str(pathlib.Path(__file__).resolve().parent.parent),
    )
    default_allowlist = os.path.join(plugin_root, "resource", "permissions-allowlist.yaml")

    import argparse

    parser = argparse.ArgumentParser(description="权限白名单预检查")
    parser.add_argument(
        "--allowlist",
        default=default_allowlist,
        help="permissions-allowlist.yaml 路径（默认：插件 resource 目录）",
    )
    args = parser.parse_args()

    allowlist_path = args.allowlist
    project_path = ".codebuddy/settings.json"
    user_path = str(pathlib.Path.home() / ".codebuddy" / "settings.json")

    # 优先检查项目级，再检查用户级
    result = check_permissions(project_path, allowlist_path)
    if result["status"] == "missing":
        user_result = check_permissions(user_path, allowlist_path)
        if user_result["status"] != "missing":
            result = user_result

    print(json.dumps(result))


if __name__ == "__main__":
    main()
