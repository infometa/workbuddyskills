# -*- coding: utf-8 -*-
"""
API 补充查询模块

功能：当嵌入式 IP-Country 数据库中找不到某 IP 时，通过在线 API 进行补充查询。

策略：
1. 多 API 端点容灾（全部 HTTPS，按优先级依次尝试，任一成功即返回）
   - ip.sb（首选）：返回国家+ISP+ASN+经纬度+时区，数据最丰富
   - pconline：国内 IP 精度高（省市+运营商），境外 IP 返回国家
   - country.is（兜底）：仅返回国家代码，稳定可靠
2. TOP N 策略（DDoS 场景下只查 TOP N 高频未知 IP，不逐一查询百万级 IP）
3. 速率限制（防止触发 API 限流）
4. 缓存（已查询过的 IP 不重复请求）

安全说明：
- 仅查询公网 IP 归属国，不涉及内网/私有地址
- 所有 API 端点均为 HTTPS，保证传输安全
- 所有 API 调用设置 5 秒超时，失败自动降级到下一个端点
"""

import time
import threading
import requests
from loguru import logger

try:
    from .ip_data_embedded import COUNTRY_NAMES
except ImportError:
    # 直接运行时（非包导入）
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from ip_data_embedded import COUNTRY_NAMES


# ============================================================================
# API 端点配置（按优先级排列，全部 HTTPS）
# ============================================================================
# 选型依据（实测验证）：
#   ip.sb      — HTTPS ✅，返回国家+ISP+ASN+经纬度+时区，数据最丰富
#   pconline   — HTTPS ✅，国内 IP 返回省市+运营商（精度高），境外 IP 返回国家
#   country.is — HTTPS ✅，仅返回 {"country":"US"}，数据少但稳定，做兜底

_API_ENDPOINTS = [
    {
        # ip.sb：HTTPS，返回最丰富的地理位置信息（国家+ISP+ASN+经纬度+时区）
        # 实测稳定，作为首选端点
        'name': 'ip.sb',
        'single_url': 'https://api.ip.sb/geoip/{ip}',
        'batch_url': None,
        'batch_size': 1,
        'rate_limit_interval': 0.5,
        'parse_single': lambda data: data.get('country_code'),
        'parse_batch': None,
    },
    {
        # pconline（太平洋网络）：HTTPS，国内 IP 精度高（省市+运营商）
        # 境外 IP 只返回国家代码（省市为空），但仍可用于国家级归属
        # 返回编码为 GBK，需特殊处理
        'name': 'pconline',
        'single_url': 'https://whois.pconline.com.cn/ipJson.jsp?ip={ip}&json=true',
        'batch_url': None,
        'batch_size': 1,
        'rate_limit_interval': 0.3,
        'parse_single': '_parse_pconline',  # 特殊解析函数名，见下方 _parse_pconline_response
        'parse_batch': None,
        'encoding': 'gbk',  # pconline 返回 GBK 编码
    },
    {
        # country.is：HTTPS，仅返回国家代码 {"country":"US"}
        # 数据少但稳定，作为兜底端点
        'name': 'country.is',
        'single_url': 'https://api.country.is/{ip}',
        'batch_url': None,
        'batch_size': 1,
        'rate_limit_interval': 0.5,
        'parse_single': lambda data: data.get('country'),
        'parse_batch': None,
    },
]

# 请求超时（秒）
_REQUEST_TIMEOUT = 5

# User-Agent（部分 API 要求）
_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (compatible; DDoS-Analysis-Skill/1.0)',
    'Accept': 'application/json',
}

# 速率限制锁（线程安全）
_rate_lock = threading.Lock()
_last_request_time = {}  # endpoint_name -> timestamp


def _rate_limit(endpoint_name: str, interval: float):
    """速率限制：确保同一端点两次请求间隔不小于 interval 秒"""
    with _rate_lock:
        now = time.time()
        last = _last_request_time.get(endpoint_name, 0)
        wait = interval - (now - last)
        if wait > 0:
            time.sleep(wait)
        _last_request_time[endpoint_name] = time.time()


def _code_to_cn(code: str) -> str:
    """国家代码 → 中文名"""
    if not code:
        return '未知'
    code = code.strip().upper()
    return COUNTRY_NAMES.get(code, code)


def _parse_pconline_response(resp) -> str:
    """
    解析 pconline 的特殊返回格式

    pconline 返回 GBK 编码的 JSON-like 文本，格式如：
        {"ip":"8.8.8.8","pro":"","proCode":"0","city":"","cityCode":"0","region":"","regionCode":"0","addr":"美国","regionIds":"","err":"","country":"美国"}

    特点：
    - 国内 IP：addr 含"省市"，country 为"中国"
    - 境外 IP：addr 为国家名，country 为国家名
    - 编码为 GBK，需手动设置 encoding
    - country 字段直接是中文国名（不是代码），需反查代码再转标准中文名

    Returns:
        str: 国家中文名，失败返回 None
    """
    resp.encoding = 'gbk'
    try:
        data = resp.json()
    except Exception:
        # pconline 有时返回带括号的 JSON，尝试清洗
        import json
        text = resp.text.strip()
        if text.startswith('(') and text.endswith(')'):
            text = text[1:-1]
        try:
            data = json.loads(text)
        except Exception:
            return None

    # pconline 的 country 字段直接是中文国名（如"美国"、"中国"）
    country_cn = data.get('country', '').strip()
    if country_cn and country_cn != '未知':
        return country_cn

    # 兜底：addr 字段
    addr = data.get('addr', '').strip()
    if addr:
        return addr

    return None


def lookup_single(ip: str) -> str:
    """
    通过 API 查询单个 IP 的国家归属

    依次尝试多个 API 端点，任一成功即返回。

    Args:
        ip: IPv4 地址字符串

    Returns:
        str: 国家中文名（如 "中国"），查询失败返回 "未知"
    """
    for endpoint in _API_ENDPOINTS:
        try:
            _rate_limit(endpoint['name'], endpoint['rate_limit_interval'])
            url = endpoint['single_url'].format(ip=ip)
            resp = requests.get(url, timeout=_REQUEST_TIMEOUT, headers=_HEADERS)
            if resp.status_code != 200:
                logger.debug(f"[{endpoint['name']}] {ip} HTTP {resp.status_code}")
                continue

            # 特殊端点处理（如 pconline 返回 GBK 编码 + 中文国名）
            parse_fn = endpoint['parse_single']
            if isinstance(parse_fn, str):
                # 特殊解析函数（通过名称匹配）
                if parse_fn == '_parse_pconline':
                    cn = _parse_pconline_response(resp)
                    if cn:
                        logger.debug(f"[{endpoint['name']}] {ip} -> {cn}")
                        return cn
                continue

            # 标准端点：返回 JSON，解析国家代码
            data = resp.json()
            code = parse_fn(data)
            if code:
                cn = _code_to_cn(code)
                logger.debug(f"[{endpoint['name']}] {ip} -> {code} ({cn})")
                return cn
        except Exception as e:
            logger.debug(f"[{endpoint['name']}] {ip} 查询失败: {e}")
            continue

    logger.warning(f"所有 API 端点均查询失败: {ip}")
    return '未知'


def lookup_batch(ips: list) -> dict:
    """
    批量查询多个 IP 的国家归属

    当前所有端点均仅支持单 IP 查询（无批量 API），因此直接逐个调用 lookup_single。
    多端点容灾已在 lookup_single 内部实现：ip.sb → pconline → country.is 依次尝试。

    TOP N 策略下（默认 100 IP），逐个查询约需 50 秒，可接受。

    Args:
        ips: IP 地址列表

    Returns:
        dict: {ip: 国家中文名}，查询失败的 IP 不包含在结果中
    """
    if not ips:
        return {}

    result = {}
    total = len(ips)

    for i, ip in enumerate(ips, 1):
        cn = lookup_single(ip)
        if cn != '未知':
            result[ip] = cn
        if i % 10 == 0:
            logger.info(f"批量查询进度: {i}/{total}，成功 {len(result)}")

    logger.info(f"批量查询完成: 成功 {len(result)}/{total}")
    return result


def enhance_unknown_ips(unknown_ip_counter: dict, top_n: int = 100) -> dict:
    """
    对嵌入式数据库中未知的 IP 进行 API 补充查询

    DDoS 场景下可能有大量未知 IP，采用 TOP N 策略：
    只查询出现频率最高的 N 个 IP（覆盖大部分攻击流量），避免逐一查询百万级 IP。

    Args:
        unknown_ip_counter: {ip: packet_count} 未知 IP 及其包计数
        top_n: 只查询 TOP N 个高频 IP（默认 100）

    Returns:
        dict: {ip: 国家中文名} 成功查询的 IP → 国家映射
    """
    if not unknown_ip_counter:
        return {}

    # 按包数降序排列，取 TOP N
    sorted_ips = sorted(unknown_ip_counter.items(), key=lambda x: x[1], reverse=True)
    top_ips = [ip for ip, count in sorted_ips[:top_n]]

    total_unknown = len(unknown_ip_counter)
    total_packets = sum(unknown_ip_counter.values())
    top_packets = sum(count for ip, count in sorted_ips[:top_n])

    logger.info(
        f"API 补充查询: 未知 IP {total_unknown} 个（{total_packets} 包），"
        f"查询 TOP {len(top_ips)}（覆盖 {top_packets} 包，{top_packets / total_packets * 100:.1f}%）"
    )

    if not top_ips:
        return {}

    result = lookup_batch(top_ips)
    logger.info(f"API 补充查询完成: 成功 {len(result)}/{len(top_ips)} 个 IP")
    return result


if __name__ == '__main__':
    # 测试
    print("=== 单 IP 查询测试 ===")
    test_ips = ['8.8.8.8', '1.1.1.1', '114.114.114.114']
    for ip in test_ips:
        cn = lookup_single(ip)
        print(f"  {ip} -> {cn}")

    print("\n=== 批量查询测试 ===")
    results = lookup_batch(test_ips)
    for ip, cn in results.items():
        print(f"  {ip} -> {cn}")

    print("\n=== TOP N 增强测试 ===")
    fake_counter = {'8.8.8.8': 1000, '1.1.1.1': 500, '114.114.114.114': 200}
    enhanced = enhance_unknown_ips(fake_counter, top_n=10)
    for ip, cn in enhanced.items():
        print(f"  {ip} -> {cn}")
