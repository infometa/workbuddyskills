#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
唯品会促销活动查询工具
支持查询当前所有促销活动并进行分析总结
"""

import sys
import json
import time
import urllib.request
from pathlib import Path
from typing import Dict, List, Any, Optional


def make_request(url: str, cookies: Optional[Dict[str, str]] = None, post_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    发起 HTTP POST 请求并返回 JSON 响应

    Args:
        url: 请求URL
        cookies: 可选的cookie字典
        post_data: 可选的POST数据字典

    Returns:
        JSON响应数据
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Content-Type': 'application/json'
        }

        # 添加 Cookie 头
        if cookies:
            cookie_str = '; '.join([f'{k}={v}' for k, v in cookies.items()])
            headers['Cookie'] = cookie_str

        encoded_data = None
        if post_data is not None:
            encoded_data = json.dumps(post_data, ensure_ascii=False).encode('utf-8')
            req = urllib.request.Request(url, data=encoded_data, headers=headers, method='POST')
        else:
            req = urllib.request.Request(url, headers=headers)

        with urllib.request.urlopen(req, timeout=30) as response:
            data = response.read().decode('utf-8')
            return json.loads(data)
    except Exception as e:
        return {"error": str(e)}


def analyze_activities(act_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    分析促销活动列表

    Args:
        act_list: 活动列表

    Returns:
        分析总结结果
    """
    result = {
        "总计": len(act_list),
        "按状态分组": {},
        "按类型分组": {},
        "进行中的活动": [],
        "待开始的活动": []
    }

    # 按状态和类型分组
    for act in act_list:
        # 按状态分组
        status = act.get("actStatusDesc", "未知")
        if status not in result["按状态分组"]:
            result["按状态分组"][status] = 0
        result["按状态分组"][status] += 1

        # 按类型分组
        act_type = act.get("actTypeDesc", "未知")
        if act_type not in result["按类型分组"]:
            result["按类型分组"][act_type] = 0
        result["按类型分组"][act_type] += 1

        # 按状态添加到列表
        if status == "进行中":
            result["进行中的活动"].append({
                "活动名称": act.get("actName", ""),
                "活动类型": act.get("actTypeDesc", ""),
                "开始时间": act.get("startTime", ""),
                "结束时间": act.get("endTime", ""),
                "品牌描述": act.get("brandDesc", ""),
                "活动链接": act.get("actLink", ""),
                "活动图片": act.get("bannerImg", "")
            })
        elif status == "待开始":
            result["待开始的活动"].append({
                "活动名称": act.get("actName", ""),
                "活动类型": act.get("actTypeDesc", ""),
                "开始时间": act.get("startTime", ""),
                "结束时间": act.get("endTime", ""),
                "品牌描述": act.get("brandDesc", ""),
                "活动链接": act.get("actLink", ""),
                "活动图片": act.get("bannerImg", "")
            })

    return result


def load_login_tokens() -> Optional[Dict[str, Any]]:
    """
    加载登录态
    
    Returns:
        登录态字典，包含cookies等信息；如果未登录或已过期返回None
    """
    token_file = Path.home() / ".vipshop-user-login" / "tokens.json"
    
    if not token_file.exists():
        return None
    
    try:
        with open(token_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 检查是否是新格式（包含cookies字段）
        if data and isinstance(data, dict) and 'cookies' in data:
            # 检查token是否过期
            expires_at = data.get('expires_at')
            if expires_at and time.time() > expires_at:
                return None
            return data
        return None
    except Exception as e:
        sys.stderr.write(f"加载登录态失败: {e}\n")
        return None


def get_promotions() -> Dict[str, Any]:
    """
    主函数：获取唯品会促销活动

    Returns:
        JSON格式的促销活动信息
    """
    # 检查登录状态
    login_data = load_login_tokens()
    if login_data is None:
        return {
            "error": "login_required",
            "message": "需要登录唯品会账户",
            "action": "请先登录唯品会账户后再查询促销活动"
        }

    # 提取 cookies
    cookies = {}
    login_cookies = login_data.get('cookies', {})
    if 'PASSPORT_ACCESS_TOKEN' in login_cookies:
        cookies['PASSPORT_ACCESS_TOKEN'] = login_cookies['PASSPORT_ACCESS_TOKEN']

    # API 接口
    url = "https://api.union.vip.com/vsp/common/getActListForAI"

    # 调用接口
    response = make_request(url, cookies=cookies, post_data={})

    if "error" in response:
        return {"error": f"接口调用失败: {response['error']}"}

    if response.get("code") != 1:
        # 检查是否是token过期
        if response.get("code") == 11000:
            return {"error": "token_expired", "message": response.get("msg", "token expired")}
        return {"error": f"接口错误，code={response.get('code')}, msg={response.get('msg', '')}"}

    # 获取活动列表
    act_list = response.get("data", {}).get("actList", [])

    if not act_list:
        return {"error": "暂无促销活动"}

    # 分析活动
    analysis = analyze_activities(act_list)

    # 组装完整结果
    result = {
        "code": response.get("code"),
        "msg": response.get("msg"),
        "分析总结": analysis,
        "原始数据": {
            "活动列表": act_list,
            "tid": response.get("data", {}).get("tid", "")
        }
    }

    return result


def main():
    """命令行入口 - 输出JSON格式数据"""
    result = get_promotions()

    # 输出JSON格式数据，确保中文正常显示
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
