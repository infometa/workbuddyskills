#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
data_fetch.py — 从知识库读取月度报告

功能：
  1. 搜索指定月份的综合分析报告和分省分析报告
  2. 获取报告原文内容
  3. 返回结构化数据

依赖：
  - ~/.config/ima/client_id 和 ~/.config/ima/api_key（Mac/Linux）
  - %USERPROFILE%\\.config\\ima\\client_id 和 api_key（Windows）
  - ~/.workbuddy/skills/ima-skills/ima_api.cjs

跨平台说明：
  - 使用 subprocess.run 替代 os.system，防止命令注入
  - stdout/stderr 重定向跨平台兼容（不依赖 /dev/null）
  - 自动检测 node 可执行文件路径（Mac/Linux/Windows）
  - 凭证路径自动适配操作系统
"""

import json
import os
import shutil
import subprocess
import tempfile

# 知识库API配置
SKILL_DIR = os.path.expanduser("~/.workbuddy/skills/ima-skills")
# 跨平台凭证路径：Windows 上 ~ 展开为 %USERPROFILE%
CLIENT_ID_FILE = os.path.join(os.path.expanduser("~/.config/ima"), "client_id")
API_KEY_FILE = os.path.join(os.path.expanduser("~/.config/ima"), "api_key")
KB_ID = "iMcQGV1yFJ95ZY_2Civak4-0-J9NNFCWSCYYYd0806E="
FOLDER_ID = "7467227984964220"
OUT_FILE = os.path.join(tempfile.gettempdir(), "ima_data_resp.json")


def _find_node():
    """检测 node 可执行文件路径，跨平台兼容。

    返回:
        node 可执行文件路径字符串，找不到返回 None。
    """
    # 1. 优先使用 PATH 中的 node
    node_path = shutil.which("node")
    if node_path:
        return node_path
    # 2. 尝试常见安装路径（Windows）
    if os.name == "nt":
        candidates = [
            os.path.join(os.environ.get("ProgramFiles", ""), "nodejs", "node.exe"),
            os.path.join(os.environ.get("APPDATA", ""), "npm", "node.exe"),
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "nodejs", "node.exe"),
        ]
        for c in candidates:
            if c and os.path.exists(c):
                return c
    # 3. 尝试常见安装路径（Mac/Linux）
    else:
        candidates = [
            "/usr/local/bin/node",
            "/usr/bin/node",
            "/opt/homebrew/bin/node",
        ]
        for c in candidates:
            if os.path.exists(c):
                return c
    return None


def _load_credentials():
    """加载知识库凭证。"""
    try:
        client_id = open(CLIENT_ID_FILE, "r", encoding="utf-8").read().strip()
        api_key = open(API_KEY_FILE, "r", encoding="utf-8").read().strip()
        return client_id, api_key
    except Exception:
        return None, None


def _ima_api(endpoint, payload, opts):
    """调用知识库API。

    使用 subprocess.run 替代 os.system，防止命令注入。
    stdout 写入临时文件，stderr 静默丢弃（跨平台兼容）。
    """
    # 检查 node 和 ima_api.cjs 是否可用
    node_bin = _find_node()
    if not node_bin:
        print("[data_fetch] 错误: 未找到 node 可执行文件")
        return None

    ima_api_script = os.path.join(SKILL_DIR, "ima_api.cjs")
    if not os.path.exists(ima_api_script):
        print(f"[data_fetch] 错误: 知识库API脚本不存在: {ima_api_script}")
        return None

    # 清理旧输出文件
    if os.path.exists(OUT_FILE):
        try:
            os.remove(OUT_FILE)
        except Exception:
            pass

    body = json.dumps(payload, ensure_ascii=False)
    opts_json = json.dumps(opts)

    # 使用 subprocess.run，避免 os.system 的命令注入风险
    # stdout 重定向到文件，stderr 用 DEVNULL 静默（跨平台兼容）
    try:
        with open(OUT_FILE, "w", encoding="utf-8") as out_f:
            result = subprocess.run(
                [node_bin, ima_api_script, f"openapi/wiki/v1/{endpoint}", body, opts_json],
                stdout=out_f,
                stderr=subprocess.DEVNULL,
                timeout=30,
                check=False,
            )
        if result.returncode != 0:
            print(f"[data_fetch] 知识库API调用失败，返回码: {result.returncode}")
            return None
    except subprocess.TimeoutExpired:
        print("[data_fetch] 知识库API调用超时（30秒）")
        return None
    except Exception as e:
        print(f"[data_fetch] 知识库API调用异常: {type(e).__name__}: {e}")
        return None

    try:
        with open(OUT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[data_fetch] 输出文件解析失败: {type(e).__name__}: {e}")
        return None


def search_knowledge(keyword, kb_id=KB_ID):
    """搜索知识库。"""
    client_id, api_key = _load_credentials()
    if not client_id:
        return {"status": "error", "details": "知识库凭证未配置"}

    opts = {"clientId": client_id, "apiKey": api_key}
    payload = {
        "keyword": keyword,
        "knowledge_base_id": kb_id,
        "page_size": 5,
        "page_index": 1,
    }
    result = _ima_api("search_knowledge", payload, opts)
    if not result or result.get("code") != 0:
        return {"status": "error", "details": f"搜索失败: {keyword}"}

    return {"status": "ok", "data": result.get("data", {})}


def get_media_content(media_id):
    """获取知识库媒体内容。"""
    client_id, api_key = _load_credentials()
    opts = {"clientId": client_id, "apiKey": api_key}
    payload = {"media_id": media_id, "knowledge_base_id": KB_ID}
    result = _ima_api("get_media_info", payload, opts)
    if not result or result.get("code") != 0:
        return None
    return result.get("data", {})


def fetch_monthly_reports(year_month):
    """
    主函数：获取指定月份的市场报告。

    参数:
        year_month: 6位年月字符串，如 "202605"

    返回:
        {
            "status": "ok",
            "month": year_month,
            "comprehensive": {"title": ..., "intro": ..., "content": ...},
            "provincial": {"title": ..., "intro": ..., "content": ...},
            "details": "..."
        }
    """
    # 格式化年份和月份
    year = year_month[:4]
    month = year_month[4:]

    # 搜索综合分析报告
    comp_keyword = f"手机市场月度综合分析报告-{year_month}"
    comp_result = search_knowledge(comp_keyword)

    if comp_result["status"] != "ok":
        return {
            "status": "error",
            "details": f"未找到综合分析报告: {comp_keyword}",
        }

    # 从搜索结果提取信息
    comp_data = comp_result.get("data", {})
    comp_items = comp_data.get("list", comp_data.get("items", []))

    if not comp_items:
        return {
            "status": "error",
            "details": f"综合分析报告搜索结果为空: {comp_keyword}",
        }

    comp_item = comp_items[0]  # 取第一个结果
    comp_title = comp_item.get("title", "")
    comp_intro = comp_item.get("intro", comp_item.get("summary", ""))
    comp_media_id = comp_item.get("media_id", "")

    # 搜索分省分析报告
    prov_keyword = f"手机市场月度分省分析报告-{year_month}"
    prov_result = search_knowledge(prov_keyword)
    prov_data = prov_result.get("data", {}) if prov_result["status"] == "ok" else {}
    prov_items = prov_data.get("list", prov_data.get("items", []))
    prov_item = prov_items[0] if prov_items else {}
    prov_title = prov_item.get("title", "")
    prov_intro = prov_item.get("intro", prov_item.get("summary", ""))
    prov_media_id = prov_item.get("media_id", "")

    return {
        "status": "ok",
        "month": year_month,
        "comprehensive": {
            "title": comp_title,
            "intro": comp_intro,
            "media_id": comp_media_id,
        },
        "provincial": {
            "title": prov_title,
            "intro": prov_intro,
            "media_id": prov_media_id,
        },
        "details": f"综合报告: {comp_title} | 分省报告: {prov_title or '未找到'}",
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("用法: python3 data_fetch.py YYYYMM")
        sys.exit(1)
    result = fetch_monthly_reports(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))
