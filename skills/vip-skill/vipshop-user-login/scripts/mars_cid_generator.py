#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mars_cid 生成器模块

用于生成唯品会设备标识 mars_cid，需要在请求 cookie 中携带。
算法源自 JS 版本：version 1.0.0.20171020

使用方法:
    from mars_cid_generator import MarsCidGenerator
    
    # 生成新的 mars_cid
    mars_cid = MarsCidGenerator.create()
    
    # 验证 mars_cid 格式
    is_valid = MarsCidGenerator.validate(mars_cid)
"""

import time
import re
import secrets
from typing import Optional


class MarsCidGenerator:
    """mars_cid 生成器"""
    
    @staticmethod
    def create() -> str:
        """
        创建 mars_cid
        
        Returns:
            安全加密的 mars_cid 字符串
        """
        timestamp = MarsCidGenerator._pad(int(time.time() * 1000), 13)  # 13位时间戳（毫秒）
        rand_str = MarsCidGenerator._rand(32)  # 32位随机十六进制字符串
        timestamp_mar_id = f"{timestamp}_{rand_str}"
        return MarsCidGenerator.encrypt(timestamp_mar_id)
    
    @staticmethod
    def encrypt(timestamp_mar_id: str) -> str:
        """
        安全加密 mars_cid
        
        Args:
            timestamp_mar_id: 时间戳+随机数，格式为 "timestamp_mar_id"
            
        Returns:
            安全加密的 mars_cid
        """
        # 分割 mar Id
        parts = timestamp_mar_id.split("_")
        if len(parts) != 2:
            return timestamp_mar_id
        
        timestamp, mar_id = parts
        if not timestamp or not mar_id:
            return timestamp_mar_id
        
        # 计算 timestamp 所有数字之和
        timestamp_sum = sum(int(c) for c in timestamp if c.isdigit())
        replace_index = timestamp_sum % 32
        
        # 计算所有十六进制字符值之和（除了 replace_index 位置的字符）
        dechex_sum = timestamp_sum
        mar_id_len = len(mar_id)
        
        for i in range(mar_id_len):
            if i != replace_index:
                try:
                    dechex_sum += int(mar_id[i], 16)
                except ValueError:
                    # 如果不是有效的十六进制字符，跳过
                    pass
        
        replace_value = format(dechex_sum % 16, 'x')  # 转为十六进制字符串
        
        # 组装结果
        result = (
            timestamp + "_" +
            mar_id[:replace_index] +
            replace_value +
            mar_id[replace_index + 1:]
        )
        return result
    
    @staticmethod
    def _pad(num: int, n: int) -> str:
        """
        补0，将数字填充到指定长度
        
        Args:
            num: 原数字
            n: 目标位数
            
        Returns:
            补0后的字符串
        """
        return str(num).zfill(n)
    
    @staticmethod
    def _rand(length: int = 32) -> str:
        """
        生成指定长度的随机十六进制字符串
        
        Args:
            length: 长度，默认32位
            
        Returns:
            随机十六进制字符串，例如：bb534acdd50ba1519bb4dcf534112ddc
        """
        import secrets
        return secrets.token_hex(length // 2)
    
    @staticmethod
    def validate(mars_cid: str) -> bool:
        """
        验证 mars_cid 格式是否有效
        
        Args:
            mars_cid: 要验证的 mars_cid 字符串
            
        Returns:
            是否有效
        """
        if not mars_cid:
            return False
        
        # 格式: 13位数字_timestamp_32位十六进制
        pattern = r'^\d{13}_[0-9a-f]{32}$'
        return bool(re.match(pattern, mars_cid))


class DeviceManager:
    """设备管理器，用于持久化保存设备ID"""
    
    CONFIG_DIR = ".vipshop-user-login"
    DEVICE_FILE = "device.json"
    
    def __init__(self):
        self._mars_cid: Optional[str] = None
        self._load_device()
    
    def _get_config_path(self):
        """获取配置文件路径"""
        from pathlib import Path
        config_dir = Path.home() / self.CONFIG_DIR
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / self.DEVICE_FILE
    
    def _load_device(self):
        """加载设备信息"""
        import json
        config_path = self._get_config_path()
        
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    data = json.load(f)
                    self._mars_cid = data.get('mars_cid')
            except (json.JSONDecodeError, IOError):
                self._mars_cid = None
        
        # 如果没有有效的 mars_cid，生成一个新的
        if not self._mars_cid or not MarsCidGenerator.validate(self._mars_cid):
            self._mars_cid = MarsCidGenerator.create()
            self._save_device()
    
    def _save_device(self):
        """保存设备信息"""
        import json
        config_path = self._get_config_path()
        
        data = {
            'mars_cid': self._mars_cid,
            'created_at': time.time()
        }
        
        try:
            with open(config_path, 'w') as f:
                json.dump(data, f, indent=2)
        except IOError:
            pass
    
    def get_mars_cid(self) -> str:
        """获取 mars_cid，如果不存在则生成"""
        if not self._mars_cid:
            self._mars_cid = MarsCidGenerator.create()
            self._save_device()
        return self._mars_cid
    
    def regenerate(self) -> str:
        """重新生成 mars_cid"""
        self._mars_cid = MarsCidGenerator.create()
        self._save_device()
        return self._mars_cid


# 全局设备管理器实例
_device_manager: Optional[DeviceManager] = None


def get_device_manager() -> DeviceManager:
    """获取全局设备管理器实例"""
    global _device_manager
    if _device_manager is None:
        _device_manager = DeviceManager()
    return _device_manager


def get_mars_cid() -> str:
    """
    获取 mars_cid 的便捷函数
    
    Returns:
        mars_cid 字符串（自动从配置文件加载或生成新的）
    """
    return get_device_manager().get_mars_cid()


if __name__ == "__main__":
    # 测试代码
    print("MarsCidGenerator 测试")
    print("-" * 50)
    
    # 测试生成 mars_cid
    print("\n1. 测试生成 mars_cid:")
    for i in range(3):
        cid = MarsCidGenerator.create()
        is_valid = MarsCidGenerator.validate(cid)
        print(f"   生成: {cid}")
        print(f"   验证: {'✓ 有效' if is_valid else '✗ 无效'}")
        print()
    
    # 测试加密算法
    print("2. 测试加密算法:")
    test_input = "1699123456789_1234567890abcdef1234567890abcd"
    encrypted = MarsCidGenerator.encrypt(test_input)
    print(f"   输入: {test_input}")
    print(f"   输出: {encrypted}")
    
    # 测试设备管理器
    print("\n3. 测试设备管理器:")
    dm = DeviceManager()
    mars_cid = dm.get_mars_cid()
    print(f"   mars_cid: {mars_cid}")
    print(f"   验证结果: {'✓ 有效' if MarsCidGenerator.validate(mars_cid) else '✗ 无效'}")
