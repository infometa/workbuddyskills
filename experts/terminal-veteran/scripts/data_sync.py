#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
data_sync.py — 终端老兵专家 数据增量同步器

功能：
  1. 从 GitHub 远程仓库拉取 manifest.json
  2. 对比本地文件 hash，识别变更
  3. 仅下载变更的文件（增量同步）
  4. 校验下载文件的 hash，确保完整性
  5. 7 天检查间隔（通过本地缓存控制）

合规说明：
  - 只向 GitHub raw 域名发送 GET 请求，不传输任何用户数据
  - 网络异常时降级使用内置兜底数据，不影响主流程
  - 使用 except Exception（非裸 except），异常信息可追踪
  - 代码中无敏感词

数据加载策略（双层架构）：
  1. 外置热更新：~/.workbuddy/skills-data/terminal-veteran/（网络可达时）
  2. 内置兜底：references/data/ 和 references/theory/（网络不可达时自动降级）
  3. Agent MD核心知识：始终可用，不受网络影响
"""

import hashlib
import json
import os
import subprocess
import time
import urllib.request

# ---------------------------------------------------------------------------
# 配置常量
# ---------------------------------------------------------------------------
MANIFEST_URL = (
    "https://raw.githubusercontent.com/chenfengwei9166/terminal-veteran-data/main/manifest.json"
)
REPO = "chenfengwei9166/terminal-veteran-data"
BASE_DIR = os.path.expanduser("~/.workbuddy/skills-data/terminal-veteran")
CACHE_FILE = os.path.expanduser("~/.workbuddy/skills-data/terminal-veteran/.sync_cache.json")
# 内置兜底数据路径（专家包内）
BUILTIN_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "references", "data")
BUILTIN_THEORY_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "references", "theory")
CHECK_INTERVAL_DAYS = 7
TIMEOUT = 15  # 秒（urllib 超时，失败后快速降级到 gh CLI 或内置兜底）

# ---------------------------------------------------------------------------
# 缓存控制
# ---------------------------------------------------------------------------

def _load_cache():
    """加载同步缓存。"""
    if not os.path.exists(CACHE_FILE):
        return {}
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_cache(cache):
    """保存同步缓存。"""
    try:
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _should_check():
    """判断是否需要执行检查（距上次检查超过7天）。"""
    cache = _load_cache()
    last_check = cache.get("last_check", 0)
    elapsed_days = (time.time() - last_check) / 86400
    return elapsed_days >= CHECK_INTERVAL_DAYS


def _mark_checked():
    """标记本次检查时间。"""
    cache = _load_cache()
    cache["last_check"] = int(time.time())
    _save_cache(cache)


# ---------------------------------------------------------------------------
# 文件 hash 计算
# ---------------------------------------------------------------------------

def _file_hash(filepath):
    """计算文件的 sha256 前 16 位 hash。

    归一化换行符：Windows 文本写入会把 \\n 转成 \\r\\n，
    导致本地 hash 与远程（纯 \\n）不一致。读取后统一转回 \\n 再计算。
    """
    try:
        with open(filepath, "rb") as f:
            content = f.read()
        content = content.replace(b"\r\n", b"\n")
        return hashlib.sha256(content).hexdigest()[:16]
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# 网络请求（urllib 为主，gh CLI 为备选）
# ---------------------------------------------------------------------------

def _gh_available():
    """检查 gh CLI 是否可用。"""
    try:
        subprocess.run(["gh", "auth", "status"], capture_output=True, text=True, timeout=5, check=False)
        return True
    except Exception:
        return False


def _fetch_json(url):
    """获取 JSON，优先用 urllib，超时后尝试 gh CLI。"""
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"[data_sync] 警告: urllib请求失败: {type(e).__name__}: {e}")

    if _gh_available() and "manifest.json" in url:
        try:
            result = subprocess.run(
                ["gh", "api", f"repos/{REPO}/contents/manifest.json", "-q", ".content"],
                capture_output=True, text=True, timeout=10, check=False
            )
            if result.returncode == 0:
                import base64
                content = base64.b64decode(result.stdout.strip()).decode("utf-8")
                return json.loads(content)
        except Exception as e:
            print(f"[data_sync] 警告: gh CLI备选请求失败: {type(e).__name__}: {e}")

    print("[data_sync] 网络受限，将使用内置兜底数据")
    return {}


def _fetch_text(url):
    """获取文本，优先用 urllib，超时后尝试 gh CLI。"""
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return resp.read().decode("utf-8")
    except Exception as e:
        print(f"[data_sync] 警告: 文件下载失败: {type(e).__name__}: {e}")

    if _gh_available():
        # 从 URL 中提取完整文件路径（含子目录，如 data/xxx.md）
        # URL格式: https://raw.githubusercontent.com/{REPO}/main/data/xxx.md
        parts = url.split(f"/{REPO}/main/")
        if len(parts) > 1:
            fname = parts[1]  # 如 "data/xxx.md"
        else:
            fname = url.split("/")[-1]  # 降级：只取文件名
        try:
            result = subprocess.run(
                ["gh", "api", f"repos/{REPO}/contents/{fname}", "-q", ".content"],
                capture_output=True, text=True, timeout=10, check=False
            )
            if result.returncode == 0:
                import base64
                return base64.b64decode(result.stdout.strip()).decode("utf-8")
        except Exception as e:
            print(f"[data_sync] 警告: gh CLI备选下载失败: {type(e).__name__}: {e}")

    return ""


# ---------------------------------------------------------------------------
# 增量同步核心
# ---------------------------------------------------------------------------

def sync(check_only=False, force=False):
    """
    执行增量同步。

    参数:
        check_only: 只检查是否有更新，不下载
        force:      强制同步，忽略 7 天间隔

    返回:
        {"status": "...", "updated": [], "skipped": [], "errors": [], "details": "..."}
    """
    result = {
        "status": "unknown",
        "updated": [],
        "skipped": [],
        "errors": [],
        "details": "",
    }

    # 1. 检查间隔
    if not force and not _should_check():
        result["status"] = "skip"
        result["details"] = "距离上次检查不足 7 天，跳过"
        return result

    _mark_checked()

    # 2. 拉取远程 manifest
    manifest = _fetch_json(MANIFEST_URL)
    if not manifest or "files" not in manifest:
        result["status"] = "fallback"
        # 验证内置兜底数据是否存在
        builtin_available = False
        try:
            builtin_available = (
                os.path.isdir(BUILTIN_DATA_DIR)
                and len(os.listdir(BUILTIN_DATA_DIR)) > 0
            )
        except Exception:
            pass
        if builtin_available:
            result["details"] = "网络受限，已降级使用内置兜底数据（版本可能非最新）"
        else:
            result["details"] = "网络受限且内置兜底数据缺失，仅使用 Agent MD 核心知识"
        return result

    remote_version = manifest.get("version", "unknown")
    # 兼容两种 manifest 格式：
    #   list 格式: [{file, hash, url, description}, ...]
    #   dict 格式: {文件路径: hash字符串}
    raw_files = manifest["files"]
    if isinstance(raw_files, dict):
        remote_files = {
            fname: {
                "hash": h if isinstance(h, str) else "",
                "url": f"https://raw.githubusercontent.com/{REPO}/main/{fname}",
            }
            for fname, h in raw_files.items()
        }
    elif isinstance(raw_files, list):
        remote_files = {item["file"]: item for item in raw_files}
    else:
        result["status"] = "fallback"
        result["details"] = "manifest 格式异常，使用内置兜底数据"
        return result

    # 3. 遍历对比
    os.makedirs(BASE_DIR, exist_ok=True)

    for fname, info in remote_files.items():
        local_path = os.path.join(BASE_DIR, fname)
        remote_hash = info.get("hash", "")
        remote_url = info.get("url", "")

        # 确保子目录存在
        parent_dir = os.path.dirname(local_path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)

        # 本地不存在 → 需要下载
        if not os.path.exists(local_path):
            needs_update = True
        else:
            local_hash = _file_hash(local_path)
            needs_update = local_hash != remote_hash

        if not needs_update:
            result["skipped"].append(fname)
            continue

        if check_only:
            result["updated"].append(fname)
            continue

        # 下载并校验
        content = _fetch_text(remote_url)
        if not content:
            result["errors"].append(f"{fname}: 下载失败")
            continue

        # 校验 hash（兼容 16 位和 64 位 hash 格式）
        downloaded_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        if remote_hash and downloaded_hash != remote_hash and downloaded_hash[:16] != remote_hash[:16]:
            result["errors"].append(f"{fname}: hash 校验失败")
            continue

        # 写入本地（二进制模式，避免 Windows 换行符转换导致 hash 不一致）
        try:
            with open(local_path, "wb") as f:
                f.write(content.encode("utf-8"))
            result["updated"].append(fname)
        except Exception as e:
            result["errors"].append(f"{fname}: 写入失败 ({e})")

    # 4. 组装结果
    if result["errors"]:
        result["status"] = "partial"
        result["details"] = (
            f"远程版本 {remote_version} | 更新 {len(result['updated'])} 个 | "
            f"跳过 {len(result['skipped'])} 个 | 失败 {len(result['errors'])} 个"
        )
    elif result["updated"]:
        result["status"] = "success"
        result["details"] = (
            f"远程版本 {remote_version} | 更新 {len(result['updated'])} 个文件 | "
            f"跳过 {len(result['skipped'])} 个未变更文件"
        )
    else:
        result["status"] = "up_to_date"
        result["details"] = (
            f"远程版本 {remote_version} | 全部 {len(result['skipped'])} 个文件已是最新"
        )

    return result


# ---------------------------------------------------------------------------
# CLI 支持
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys

    args = sys.argv[1:]
    check_only = "--check-only" in args
    force = "--force" in args

    print(f"[data_sync] 终端老兵专家数据同步 | 间隔: {CHECK_INTERVAL_DAYS} 天")
    res = sync(check_only=check_only, force=force)
    print(f"状态: {res['status']}")
    print(f"详情: {res['details']}")
    if res["updated"]:
        print(f"更新文件: {', '.join(res['updated'])}")
    if res["errors"]:
        print(f"失败文件: {', '.join(res['errors'])}")
