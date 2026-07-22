#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bci_fetch.py — 从IMA知识库读取BCI月度报告

功能：
  1. 搜索指定月份的综合分析报告和分省分析报告
  2. 获取报告原文内容
  3. 返回结构化数据

依赖：
  - ~/.config/ima/client_id 和 ~/.config/ima/api_key
  - ~/.workbuddy/skills/ima-skills/ima_api.cjs
"""

import json
import os
import subprocess
import tempfile

# IMA配置
SKILL_DIR = os.path.expanduser("~/.workbuddy/skills/ima-skills")
CLIENT_ID_FILE = os.path.expanduser("~/.config/ima/client_id")
API_KEY_FILE = os.path.expanduser("~/.config/ima/api_key")
KB_ID = "iMcQGV1yFJ95ZY_2Civak4-0-J9NNFCWSCYYYd0806E="
FOLDER_ID = "7467227984964220"
OUT_FILE = os.path.join(tempfile.gettempdir(), "ima_bci_resp.json")


def _load_credentials():
    """加载IMA凭证。"""
    try:
        client_id = open(CLIENT_ID_FILE, "r", encoding="utf-8").read().strip()
        api_key = open(API_KEY_FILE, "r", encoding="utf-8").read().strip()
        return client_id, api_key
    except Exception as e:
        return None, None


def _ima_api(endpoint, payload, opts):
    """调用IMA API。"""
    ima_api = f"node {SKILL_DIR}/ima_api.cjs"
    if os.path.exists(OUT_FILE):
        os.remove(OUT_FILE)
    body = json.dumps(payload, ensure_ascii=False)
    opts_json = json.dumps(opts)
    cmd = f'{ima_api} "openapi/wiki/v1/{endpoint}" \'{body}\' \'{opts_json}\' > {OUT_FILE} 2>/dev/null'
    rc = os.system(cmd)
    if rc != 0:
        return None
    try:
        with open(OUT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def search_knowledge(keyword, kb_id=KB_ID):
    """搜索知识库。"""
    client_id, api_key = _load_credentials()
    if not client_id:
        return {"status": "error", "details": "IMA凭证未配置"}

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
    主函数：获取指定月份的BCI报告。

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
        print("用法: python3 bci_fetch.py YYYYMM")
        sys.exit(1)
    result = fetch_monthly_reports(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))
