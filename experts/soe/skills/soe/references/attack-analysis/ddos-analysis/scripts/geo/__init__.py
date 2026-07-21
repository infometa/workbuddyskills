"""
地理位置模块
包含IP地理位置查询功能（嵌入式数据 + API 补充查询）
"""

from .iplib import (
    locate_ip,
    is_ip_known,
    get_unknown_ips,
    enhance_cache_with_api,
    get_my_external_ip,
    DICT_IP_CACHE,
)
from .api_lookup import (
    lookup_single,
    lookup_batch,
    enhance_unknown_ips,
)

__all__ = [
    'locate_ip',
    'is_ip_known',
    'get_unknown_ips',
    'enhance_cache_with_api',
    'get_my_external_ip',
    'lookup_single',
    'lookup_batch',
    'enhance_unknown_ips',
    'DICT_IP_CACHE',
]
