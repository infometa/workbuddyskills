# -*- coding: utf-8 -*-
"""
IP 地理位置（国家级）查询模块

数据来源：嵌入式二进制数据（ip_data_embedded.py）
- 311,728 条 IP 段记录，覆盖 250 个国家/地区
- 二分查找，O(log n) 单次查询
- 内存缓存，重复 IP 零开销
- 无外部 CSV 文件依赖，自包含

API 补充：当嵌入式数据库中找不到 IP 时，可通过 api_lookup 模块在线查询（可选）
"""

import re
import bisect
import struct
import socket
import requests
from loguru import logger

try:
    from .ip_data_embedded import (
        COUNTRY_CODES,
        COUNTRY_NAMES,
        get_binary_data,
        read_varint,
        RECORD_COUNT,
        COUNTRY_COUNT,
    )
except ImportError:
    # 直接运行时（非包导入）
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from ip_data_embedded import (
        COUNTRY_CODES,
        COUNTRY_NAMES,
        get_binary_data,
        read_varint,
        RECORD_COUNT,
        COUNTRY_COUNT,
    )


# ============================================================================
# IP-Country 二分查找表（从嵌入式二进制数据构建）
# ============================================================================

# IP-Country 缓存（ip -> result dict）
DICT_IP_CACHE = {}

# 国家代码 -> 中文名（兼容旧代码导出名）
COUNTRY_CODE_TO_CN = dict(COUNTRY_NAMES)


class IPCountryLookup:
    """基于嵌入式二进制数据的 IP-国家二分查找表"""

    def __init__(self, binary_data: bytes = None):
        """
        从二进制数据构建查找表

        Args:
            binary_data: varint 编码的二进制数据（如不提供则自动从嵌入式模块加载）
        """
        self.starts = []   # 排序的起始 IP 整数列表
        self.ends = []     # 对应的结束 IP 整数列表
        self.codes = []    # 对应的国家代码列表

        if binary_data is None:
            binary_data = get_binary_data()

        self._load_binary(binary_data)
        logger.info(
            f"IP-Country 查找表已加载: {len(self.starts)} 条记录, "
            f"{len(set(self.codes))} 个国家/地区"
        )

    def _load_binary(self, data: bytes):
        """解析 varint 二进制数据，构建排序数组"""
        offset = 0
        data_len = len(data)

        while offset < data_len:
            try:
                start_int, offset = read_varint(data, offset)
                delta, offset = read_varint(data, offset)
                idx, offset = read_varint(data, offset)
            except (IndexError, struct.error):
                break

            end_int = start_int + delta
            code = COUNTRY_CODES[idx] if idx < len(COUNTRY_CODES) else '??'

            self.starts.append(start_int)
            self.ends.append(end_int)
            self.codes.append(code)

    def lookup(self, ip: str) -> dict:
        """
        查询 IP 所属国家。

        返回与原 locate_ip 兼容的 dict 结构，或 None。
        """
        ip_int = self._ip_to_int(ip)
        if ip_int is None:
            return None

        # 二分查找：找到最后一个 start <= ip_int 的位置
        idx = bisect.bisect_right(self.starts, ip_int) - 1

        if idx >= 0 and ip_int <= self.ends[idx]:
            code = self.codes[idx]
            return {
                "iso_code": code,
                "country": code,
                "country_cn": COUNTRY_NAMES.get(code, code),
                "subdivision": None,
                "subdivision_iso": None,
                "city": None,
                "postal": None,
                "location": {
                    "latitude": None,
                    "longitude": None
                }
            }
        return None

    @staticmethod
    def _ip_to_int(ip: str):
        """将 IPv4 地址字符串转为整数"""
        try:
            return struct.unpack('!I', socket.inet_aton(ip))[0]
        except (OSError, struct.error):
            return None


# ============================================================================
# 模块启动时加载查找表（单例）
# ============================================================================

_lookup_instance = None


def _get_lookup() -> IPCountryLookup:
    """懒加载单例（延迟到首次调用，避免 import 时即解压数据）"""
    global _lookup_instance
    if _lookup_instance is None:
        _lookup_instance = IPCountryLookup()
    return _lookup_instance


def get_my_external_ip() -> str:
    """获取当前外部IP地址"""
    try:
        services = [
            'https://api.ipify.org',
            'https://icanhazip.com',
            'https://ident.me'
        ]
        for service in services:
            try:
                response = requests.get(service, timeout=5)
                ip = response.text.strip()
                if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', ip):
                    return ip
            except:
                continue
        response = requests.get('https://httpbin.org/ip', timeout=5)
        data = response.json()
        return data.get('origin', '未知').strip()
    except Exception as e:
        return f"获取IP失败: {str(e)}"


def locate_ip(ip, is_cache=False):
    """
    查询 IP 地理位置（国家级）。
    保持与原接口完全兼容的签名和返回格式。

    Args:
        ip: IPv4 地址字符串
        is_cache: 是否启用内存缓存

    Returns:
        dict: 包含 iso_code, country, country_cn, subdivision, city, postal, location
    """
    if is_cache and ip in DICT_IP_CACHE:
        return DICT_IP_CACHE[ip]

    lookup = _get_lookup()
    result = lookup.lookup(ip)

    if result is None:
        result = {
            "iso_code": None,
            "country": None,
            "country_cn": "未知",
            "subdivision": None,
            "subdivision_iso": None,
            "city": None,
            "postal": None,
            "location": {
                "latitude": None,
                "longitude": None
            }
        }

    if is_cache:
        DICT_IP_CACHE[ip] = result

    return result


def is_ip_known(ip: str) -> bool:
    """
    快速判断 IP 在嵌入式数据库中是否有归属国记录

    Args:
        ip: IPv4 地址字符串

    Returns:
        bool: True 表示数据库中有记录，False 表示未知（可考虑 API 补充）
    """
    lookup = _get_lookup()
    return lookup.lookup(ip) is not None


def get_unknown_ips(ip_list: list) -> set:
    """
    从 IP 列表中筛选出嵌入式数据库未覆盖的 IP

    Args:
        ip_list: IP 地址列表

    Returns:
        set: 未知 IP 集合
    """
    lookup = _get_lookup()
    unknown = set()
    for ip in ip_list:
        if lookup.lookup(ip) is None:
            unknown.add(ip)
    return unknown


def enhance_cache_with_api(ip_to_country_cn: dict):
    """
    将 API 查询结果写入内存缓存，使后续 locate_ip 直接命中

    Args:
        ip_to_country_cn: {ip: 国家中文名} 映射
    """
    for ip, cn in ip_to_country_cn.items():
        # 反查国家代码
        code = None
        for c, name in COUNTRY_NAMES.items():
            if name == cn:
                code = c
                break

        DICT_IP_CACHE[ip] = {
            "iso_code": code,
            "country": code,
            "country_cn": cn,
            "subdivision": None,
            "subdivision_iso": None,
            "city": None,
            "postal": None,
            "location": {
                "latitude": None,
                "longitude": None
            }
        }


if __name__ == '__main__':
    from pprint import pprint

    print(f"嵌入式数据: {RECORD_COUNT} 条记录, {COUNTRY_COUNT} 个国家/地区")
    print(f"缓存大小: {len(DICT_IP_CACHE)}")

    print("\n测试 IP 查询:")
    test_ips = ['8.8.8.8', '1.1.1.1', '114.114.114.114', '223.5.5.5']
    for ip in test_ips:
        result = locate_ip(ip, is_cache=True)
        print(f"  {ip} -> {result['country_cn']} ({result['iso_code']})")

    print(f"\n缓存命中: {len(DICT_IP_CACHE)} 个 IP")

    # 测试未知 IP 筛选
    print("\n未知 IP 筛选测试:")
    mixed = ['8.8.8.8', '0.0.0.1', '1.1.1.1', '255.255.255.255']
    unknown = get_unknown_ips(mixed)
    print(f"  输入: {mixed}")
    print(f"  未知: {unknown}")
