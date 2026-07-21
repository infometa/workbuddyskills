#!/usr/bin/env python3
"""
IOC 提取器 - 从勒索信和系统信息中提取威胁情报指标
"""

import re
from typing import Dict, List


# IOC 正则模式
IOC_PATTERNS = {
    "btc_address": re.compile(r"\bbc1[ac-hj-np-z02-9]{6,87}\b|\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b"),
    "eth_address": re.compile(r"\b0x[a-fA-F0-9]{40}\b"),
    "xmr_address": re.compile(r"\b4[0-9AB][0-9a-zA-Z]{93,104}\b"),
    "tor_onion": re.compile(r"\b[a-z2-7]{16,56}\.onion\b", re.IGNORECASE),
    "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
    "telegram": re.compile(r"(?:@|t\.me/)([A-Za-z0-9_]{5,32})", re.IGNORECASE),
    "tox_id": re.compile(r"\b[A-Fa-f0-9]{76}\b"),
    "session_id": re.compile(r"\b05[a-f0-9]{64}\b", re.IGNORECASE),
    "url": re.compile(r'https?://[^\s<>"\']+'),
    "ransom_id": re.compile(r"[A-F0-9]{8}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{12}", re.IGNORECASE),
    "victim_id": re.compile(r"\b[A-Z0-9]{6,10}-[A-Z0-9]{6,10}\b"),
}


def extract_iocs(text: str) -> Dict[str, List[str]]:
    """
    从文本中提取各类 IOC

    Args:
        text: 待分析文本（勒索信内容、系统日志等）

    Returns:
        按类型分组的 IOC 列表
    """
    iocs = {}
    for ioc_type, pattern in IOC_PATTERNS.items():
        matches = pattern.findall(text)
        # 去重并保持顺序
        seen = set()
        unique = []
        for m in matches:
            if isinstance(m, tuple):
                m = m[0]
            if m not in seen:
                seen.add(m)
                unique.append(m)
        if unique:
            iocs[ioc_type] = unique
    return iocs


def extract_extensions(filenames: List[str]) -> List[str]:
    """从文件名列表中提取加密扩展名"""
    extensions = set()
    for f in filenames:
        if "." in f:
            ext = "." + f.rsplit(".", 1)[-1]
            extensions.add(ext.lower())
    return sorted(extensions)


def extract_contact_methods(note: str) -> Dict[str, List[str]]:
    """从勒索信中提取攻击者联系方式"""
    contacts = {}
    iocs = extract_iocs(note)
    contact_types = ["tor_onion", "email", "telegram", "tox_id", "session_id"]
    for ct in contact_types:
        if ct in iocs:
            contacts[ct] = iocs[ct]
    return contacts


if __name__ == "__main__":
    import sys
    text = sys.stdin.read()
    result = extract_iocs(text)
    for ioc_type, values in result.items():
        print(f"\n{ioc_type}:")
        for v in values:
            print(f"  - {v}")
