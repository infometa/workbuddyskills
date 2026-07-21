#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VIPShop Token 管理模块

负责Token的获取、存储、读取和刷新。
Token存储在本地文件 ~/.vipshop-user-login/tokens.json
"""

import json
import os
import time
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta


@dataclass
class TokenInfo:
    """Token信息数据类 - 简化版，主要保存cookies用于后续请求"""
    cookies: Dict[str, str]  # 登录态cookies
    user_id: Optional[str] = None
    nickname: Optional[str] = None
    created_at: float = 0.0
    expires_at: float = 0.0  # 从PASSPORT_ACCESS_TOKEN的Max-Age计算出的过期时间戳
    version: Optional[str] = None  # skill 版本号
    
    def __post_init__(self):
        if self.created_at == 0.0:
            self.created_at = time.time()
    
    @property
    def access_token(self) -> str:
        """兼容旧代码，返回空字符串"""
        return ""
    
    @property
    def is_expired(self) -> bool:
        """检查登录态是否已过期（基于PASSPORT_ACCESS_TOKEN的过期时间）"""
        # 如果有明确的过期时间，使用它
        if self.expires_at > 0:
            # 提前5分钟认为过期
            return time.time() > (self.expires_at - 300)
        # 否则使用默认7天
        default_expires_in = 7 * 24 * 3600
        if not self.created_at:
            return True
        expire_time = self.created_at + default_expires_in
        return time.time() > (expire_time - 300)
    
    @property
    def expire_datetime(self) -> str:
        """获取过期时间的格式化字符串"""
        expire_timestamp = 0
        if self.expires_at > 0:
            expire_timestamp = self.expires_at
        elif self.created_at > 0:
            expire_timestamp = self.created_at + 7 * 24 * 3600
        
        if expire_timestamp == 0:
            return "未知"
        dt = datetime.fromtimestamp(expire_timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典 - 只保存必要的字段"""
        data = {
            "cookies": self.cookies,
            "created_at": self.created_at,
            "expires_at": self.expires_at
        }
        if self.version:
            data["version"] = self.version
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TokenInfo':
        """从字典创建TokenInfo"""
        return cls(**data)


class TokenManager:
    """Token管理器 - 单用户模式，固定key存储"""
    
    DEFAULT_STORAGE_DIR = Path.home() / ".vipshop-user-login"
    DEFAULT_TOKEN_FILE = DEFAULT_STORAGE_DIR / "tokens.json"
    SINGLE_USER_KEY = "current_user"  # 固定key，单用户模式
    
    def __init__(self, token_file: Optional[str] = None):
        """
        初始化Token管理器
        
        Args:
            token_file: Token文件路径，默认使用 ~/.vipshop-user-login/tokens.json
        """
        self.token_file = Path(token_file) if token_file else self.DEFAULT_TOKEN_FILE
        self._ensure_storage_dir()
        self._token_info: Optional[TokenInfo] = None  # 单用户，直接存储TokenInfo
        self._load_tokens()
    
    def _ensure_storage_dir(self):
        """确保存储目录存在"""
        self.token_file.parent.mkdir(parents=True, exist_ok=True)
        # 设置目录权限，仅所有者可读写
        os.chmod(self.token_file.parent, 0o700)
    
    def _load_tokens(self):
        """从文件加载token（单用户模式）"""
        if not self.token_file.exists():
            return
        
        try:
            with open(self.token_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 检查是否是新格式（包含cookies字段）
            if data and isinstance(data, dict) and 'cookies' in data:
                self._token_info = TokenInfo.from_dict(data)
                print(f"[TokenManager] 已加载登录态")
            else:
                # 旧格式，删除重新登录
                print(f"[TokenManager] 检测到旧格式登录态，请重新登录")
                self.token_file.unlink()
        except Exception as e:
            print(f"[TokenManager] 加载token失败: {e}")
    
    def _save_tokens(self):
        """保存token到文件（单用户模式）"""
        try:
            if self._token_info is None:
                return True
            
            data = self._token_info.to_dict()
            
            # 先写入临时文件，再重命名，保证原子性
            temp_file = self.token_file.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # 设置文件权限，仅所有者可读写
            os.chmod(temp_file, 0o600)
            temp_file.replace(self.token_file)
            
            return True
        except Exception as e:
            print(f"[TokenManager] 保存token失败: {e}")
            return False
    
    def save_token(self, user_id: str, token_info: TokenInfo) -> bool:
        """
        保存登录态（单用户模式，新登录会覆盖旧登录态）
        
        Args:
            user_id: 用户ID（保留参数兼容旧代码，但不使用）
            token_info: Token信息
            
        Returns:
            是否保存成功
        """
        self._token_info = token_info
        return self._save_tokens()
    
    def get_token(self, user_id: str = "") -> Optional[TokenInfo]:
        """
        获取当前登录态（单用户模式，user_id参数被忽略）
        
        Args:
            user_id: 用户ID（兼容旧代码，不使用）
            
        Returns:
            Token信息，如果不存在或已过期返回None
        """
        if self._token_info is None:
            return None
        
        if self._token_info.is_expired:
            print(f"[TokenManager] 登录态已过期")
            return None
        
        return self._token_info
    
    def get_cookies(self) -> Dict[str, str]:
        """
        获取当前登录态的cookies（方便给其他接口使用）
        
        Returns:
            cookies字典，如果没有登录态返回空字典
        """
        token = self.get_token()
        if token and token.cookies:
            return token.cookies
        return {}
    
    def get_valid_token(self, user_id: str = "") -> Optional[str]:
        """
        获取有效的access_token字符串（单用户模式）
        
        Args:
            user_id: 用户ID（兼容旧代码，不使用）
            
        Returns:
            有效的access_token，如果不存在或已过期返回None
        """
        token_info = self.get_token()
        if token_info and not token_info.is_expired:
            return token_info.access_token
        return None
    
    def remove_token(self, user_id: str = "") -> bool:
        """
        清除登录态
        
        Args:
            user_id: 用户ID（兼容旧代码，不使用）
            
        Returns:
            是否删除成功
        """
        self._token_info = None
        if self.token_file.exists():
            try:
                self.token_file.unlink()
            except Exception as e:
                print(f"[TokenManager] 删除token文件失败: {e}")
                return False
        return True
    
    def list_users(self) -> list:
        """
        检查是否有登录态
        
        Returns:
            如果有登录态返回 ["current_user"]，否则返回空列表
        """
        if self._token_info is not None:
            return [self.SINGLE_USER_KEY]
        return []
    
    def clear_all_tokens(self) -> bool:
        """
        清除登录态
        
        Returns:
            是否清除成功
        """
        return self.remove_token()
    
    def get_token_summary(self, user_id: str = "") -> Optional[Dict[str, Any]]:
        """
        获取登录态的摘要信息
        
        Args:
            user_id: 用户ID（兼容旧代码，不使用）
            
        Returns:
            Token摘要信息
        """
        token = self._token_info
        if not token:
            return None
        
        return {
            "user_id": token.user_id,
            "nickname": token.nickname,
            "cookies_count": len(token.cookies) if token.cookies else 0,
            "created_at": token.created_at,
            "is_expired": token.is_expired
        }
    
    def print_all_tokens(self):
        """打印当前登录态信息"""
        if not self._token_info:
            print("[TokenManager] 没有存储的登录态")
            return

        summary = self.get_token_summary()
        if summary:
            status = "已过期" if summary["is_expired"] else "有效"
            expire_time = self._token_info.expire_datetime
            print("\n[TokenManager] 当前登录态:")
            print("-" * 60)
            print(f"用户: {summary['nickname'] or summary['user_id'] or '未知'}")
            print(f"Cookies数量: {summary['cookies_count']}")
            print(f"状态: {status}")
            print(f"过期时间: {expire_time}")
            print("-" * 60)


# 便捷函数
def get_default_manager() -> TokenManager:
    """获取默认的Token管理器实例"""
    return TokenManager()


if __name__ == "__main__":
    # 测试代码
    manager = TokenManager()
    
    # 打印所有token
    manager.print_all_tokens()
    
    # 测试保存token
    test_token = TokenInfo(
        cookies={"PASSPORT_ACCESS_TOKEN": "test_access_token_12345"},
        user_id="test_user_001",
        nickname="测试用户",
        expires_at=time.time() + 3600
    )
    
    manager.save_token("test_user_001", test_token)
    print("\n保存测试token成功")
    
    # 再次打印
    manager.print_all_tokens()
