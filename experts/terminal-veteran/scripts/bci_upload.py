#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bci_upload.py — GitHub上传 + manifest更新

功能：
  1. 将格式化后的数据文件上传到GitHub数据仓库
  2. 更新manifest.json（计算hash、更新版本号）
  3. 使用gh API方式上传（兼容网络不稳定环境）

依赖：
  - gh CLI已认证
"""

import hashlib
import json
import os
import subprocess
import base64
from datetime import datetime

REPO = "chenfengwei9166/terminal-veteran-data"
MANIFEST_PATH = "manifest.json"


def _file_hash_content(content):
    """计算文本内容的SHA256前16位。"""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]


def _gh_upload_file(filepath, content, commit_msg):
    """通过gh API上传单个文件到GitHub。"""
    encoded = base64.b64encode(content.encode("utf-8")).decode("utf-8")
    api_path = f"repos/{REPO}/contents/{filepath}"

    # 先检查文件是否已存在（需要获取sha才能更新）
    existing = subprocess.run(
        ["gh", "api", api_path, "-q", ".sha"],
        capture_output=True, text=True, timeout=10
    )

    cmd = ["gh", "api", api_path, "-X", "PUT",
           "-f", f"message={commit_msg}",
           "-f", f"content={encoded}"]

    if existing.returncode == 0 and existing.stdout.strip():
        cmd.extend(["-f", f"sha={existing.stdout.strip()}"])

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

    if result.returncode != 0:
        return {"status": "error", "details": f"上传失败 {filepath}: {result.stderr[:200]}"}
    return {"status": "ok", "path": filepath}


def _fetch_manifest():
    """获取当前manifest.json。"""
    result = subprocess.run(
        ["gh", "api", f"repos/{REPO}/contents/{MANIFEST_PATH}", "-q", ".content"],
        capture_output=True, text=True, timeout=10
    )
    if result.returncode != 0:
        return None
    try:
        content = base64.b64decode(result.stdout.strip()).decode("utf-8")
        return json.loads(content)
    except Exception:
        return None


def _update_manifest(manifest, new_files, year_month):
    """更新manifest.json。"""
    year = year_month[:4]
    month = year_month[4:]

    manifest["version"] = datetime.now().strftime("%Y.%m.%d")
    manifest["last_update"] = f"{year}年{int(month)}月市场数据"

    # 构建文件列表
    existing_files = {f["file"]: f for f in manifest.get("files", [])}

    for filepath, content in new_files.items():
        file_hash = _file_hash_content(content)
        file_url = f"https://raw.githubusercontent.com/{REPO}/main/{filepath}"

        existing_files[filepath] = {
            "file": filepath,
            "hash": file_hash,
            "url": file_url,
            "description": _get_file_description(filepath),
            "update_frequency": _get_update_frequency(filepath),
        }

    manifest["files"] = list(existing_files.values())
    return manifest


def _get_file_description(filepath):
    """根据文件路径返回描述。"""
    descriptions = {
        "data/market-facts.md": "数据与事实库精选（公开数据）",
        "data/monthly-series.md": "月度数据序列",
        "data/five-year-baseline.md": "五年趋势基线",
        "data/latest-update.md": "最新月度数据快照",
        "data/provincial-analysis.md": "分省分析报告",
        "theory/quotes.md": "陈丰伟金句弹药库",
        "theory/judgments-timeline.md": "行业判断时间线",
        "theory/speech-frameworks.md": "演讲核心框架",
    }
    # 月度目录文件
    if "market-overview" in filepath:
        return "月度市场概况"
    elif "brand-competition" in filepath:
        return "品牌竞争格局"
    elif "price-segments" in filepath:
        return "价位段结构"
    elif "channels" in filepath:
        return "渠道结构"
    elif "top10-models" in filepath:
        return "TOP10机型"
    elif "provincial-analysis" in filepath and "data/" in filepath:
        return "月度分省分析"
    elif "month-comparison" in filepath:
        return "月度对比"

    return descriptions.get(filepath, "行业数据文件")


def _get_update_frequency(filepath):
    """根据文件路径返回更新频率。"""
    if filepath.startswith("theory/"):
        if "speech" in filepath:
            return "按需"
        return "季度"
    if "monthly-series" in filepath or "latest-update" in filepath:
        return "月度"
    if "five-year" in filepath:
        return "季度"
    if "market-facts" in filepath:
        return "月度"
    if "provincial" in filepath and not filepath.startswith("data/20"):
        return "月度"
    return "月度"


def upload_to_github(files, year_month):
    """
    主函数：上传数据文件到GitHub。

    参数:
        files: {文件路径: 文件内容} 字典
        year_month: 6位年月字符串

    返回:
        {"status": "ok/error", "details": "..."}
    """
    year = year_month[:4]
    month = year_month[4:]
    commit_prefix = f"更新{year}年{int(month)}月行业数据"

    uploaded = []
    errors = []

    # 上传数据文件
    for filepath, content in files.items():
        result = _gh_upload_file(filepath, content, f"{commit_prefix}: {filepath}")
        if result["status"] == "ok":
            uploaded.append(filepath)
        else:
            errors.append(filepath)

    # 更新manifest
    manifest = _fetch_manifest()
    if manifest is None:
        manifest = {"version": "", "files": []}

    manifest = _update_manifest(manifest, files, year_month)
    manifest_content = json.dumps(manifest, ensure_ascii=False, indent=2)

    manifest_result = _gh_upload_file(
        MANIFEST_PATH, manifest_content, f"{commit_prefix}: 更新manifest"
    )
    if manifest_result["status"] == "ok":
        uploaded.append(MANIFEST_PATH)
    else:
        errors.append(MANIFEST_PATH)

    if errors:
        return {
            "status": "error",
            "details": f"上传 {len(uploaded)} 个成功, {len(errors)} 个失败: {', '.join(errors[:3])}",
        }

    return {
        "status": "ok",
        "details": f"上传 {len(uploaded)} 个文件成功（含manifest）",
    }


if __name__ == "__main__":
    # 测试
    test_files = {
        "data/latest-update.md": "# 测试文件\n\n> 测试上传",
    }
    result = upload_to_github(test_files, "202605")
    print(f"状态: {result['status']}")
    print(f"详情: {result['details']}")
