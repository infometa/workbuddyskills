#!/usr/bin/env python3
"""
环境预检脚本 - 在使用 futuapi 技能前运行一次

检查项：
1. futu-api SDK 是否已安装
2. OpenD 是否可连接
"""
import sys
import socket
import os
import json

# Windows UTF-8
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

output_json = "--json" in sys.argv


def _check_sdk():
    """检查 futu-api SDK 是否已安装"""
    try:
        import futu
        current = getattr(futu, "__version__", "unknown")
        return True, f"futu-api {current}"
    except ImportError:
        return False, "futu-api 未安装，请运行 /install-futu-opend 安装"


def _check_opend():
    """检查 OpenD 是否可连接"""
    host = os.getenv("FUTU_OPEND_HOST", "127.0.0.1")
    port = int(os.getenv("FUTU_OPEND_PORT", "11111"))
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    try:
        sock.connect((host, port))
        return True, f"OpenD 可连接 ({host}:{port})"
    except (ConnectionRefusedError, OSError) as e:
        return False, f"无法连接 OpenD ({host}:{port}): {e}，请先启动 OpenD"
    finally:
        sock.close()


def main():
    results = []
    all_ok = True

    for name, check_fn in [("SDK", _check_sdk), ("OpenD", _check_opend)]:
        ok, msg = check_fn()
        results.append({"check": name, "ok": ok, "message": msg})
        if not ok:
            all_ok = False

    if output_json:
        print(json.dumps({"ok": all_ok, "checks": results}, ensure_ascii=False))
    else:
        for r in results:
            status = "✓" if r["ok"] else "✗"
            print(f"  {status} {r['check']}: {r['message']}")
        if all_ok:
            print("\n环境检查通过")
        else:
            print("\n环境检查未通过，部分功能可能不可用")

    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
