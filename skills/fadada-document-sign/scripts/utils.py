#!/usr/bin/env python3
"""法大大电子签 Skill 公共工具函数。

提供：
- 签名计算
- HTTP请求封装
- 配置管理
- 错误处理
"""

import argparse
import hashlib
import hmac
import json
import os
import sys
import time
import uuid
from typing import Any, Callable, Dict, Optional


# =============================================================================
# 配置管理
# =============================================================================

def load_config() -> Dict[str, str]:
    """加载法大大 API 配置。
    
    优先级：环境变量 > 配置文件
    
    Returns:
        包含 app_id, app_secret, open_corp_id, environment 的字典
    """
    return {
        "app_id": os.environ.get("FADADA_APP_ID", ""),
        "app_secret": os.environ.get("FADADA_APP_SECRET", ""),
        "open_corp_id": os.environ.get("FADADA_OPEN_CORP_ID", ""),
        "environment": os.environ.get("FADADA_ENV", "production"),  # 默认正式环境
    }


def validate_config(config: Dict[str, str]) -> None:
    """验证配置是否完整。
    
    Args:
        config: 配置字典
        
    Raises:
        ValueError: 配置不完整时抛出
    """
    missing = []
    if not config.get("app_id"):
        missing.append("FADADA_APP_ID")
    if not config.get("app_secret"):
        missing.append("FADADA_APP_SECRET")
    
    if missing:
        raise ValueError(f"缺少必需配置: {', '.join(missing)}")


# =============================================================================
# API基础
# =============================================================================

class FASCClient:
    """法大大 FASC API 5.0 HTTP 客户端。"""
    
    # API 地址
    PROD_URL = "https://api.fadada.com/api/v5"      # 正式环境
    UAT_URL = "https://uat-api.fadada.com/api/v5"   # UAT测试环境
    
    def __init__(self, config: Optional[Dict[str, str]] = None):
        """初始化客户端。
        
        Args:
            config: 配置字典，默认从环境变量加载
        """
        if config is None:
            config = load_config()
        
        validate_config(config)
        
        self.app_id = config["app_id"]
        self.app_secret = config["app_secret"]
        self.open_corp_id = config.get("open_corp_id", "")
        self.environment = config.get("environment", "production")
        
        # 根据环境选择 API 地址
        if self.environment == "uat":
            self.server_url = self.UAT_URL
        else:
            self.server_url = self.PROD_URL
        
        # Token 缓存
        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0
        
        # 自动获取 openCorpId（如果未配置）
        if not self.open_corp_id:
            self.open_corp_id = self._fetch_default_open_corp_id()
    
    def _fetch_default_open_corp_id(self) -> str:
        """通过 API 获取应用归属企业的 openCorpId。
        
        调用 /app/get-openId-list 接口，设置 idType="corp" 和 owner=true
        获取应用归属企业的默认 openCorpId。
        
        Returns:
            企业的 openCorpId
            
        Raises:
            APIError: 获取失败时抛出
        """
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info("未配置 openCorpId，正在通过 API 获取应用归属企业信息...")
        
        biz_content = {
            "idType": "corp",
            "owner": True,  # 仅查询应用归属企业
            "listPageNo": 1,
            "listPageSize": 1
        }
        
        result = self.request("/app/get-openId-list", biz_content)
        
        open_id_infos = result.get("openIdInfos", [])
        if not open_id_infos:
            raise APIError(
                "无法获取应用归属企业信息，请确认应用已开通企业签署权限",
                code="NO_OWNER_CORP"
            )
        
        corp_info = open_id_infos[0]
        open_corp_id = corp_info.get("openId", "")
        corp_name = corp_info.get("name", "未知企业")
        
        logger.info(f"成功获取应用归属企业: {corp_name} (openCorpId: {open_corp_id})")
        
        return open_corp_id
    
    def _sort_parameters(self, params: Dict[str, Any]) -> str:
        """按 key ASCII 排序并拼接成字符串。"""
        sorted_params = sorted([
            (k, str(v)) for k, v in params.items() 
            if v is not None and v != ""
        ])
        return "&".join([f"{k}={v}" for k, v in sorted_params])
    
    def _generate_signature(self, param_str: str, timestamp: str) -> str:
        """FASC 5.0 签名算法（两步 HMAC-SHA256）。
        
        Args:
            param_str: 排序后的参数字符串
            timestamp: 时间戳
            
        Returns:
            签名字符串（小写）
        """
        # 第一步：对参数字符串计算 SHA256
        sign_text = hashlib.sha256(param_str.encode("utf-8")).hexdigest()
        
        # 第二步：用时间戳计算临时密钥
        secret_signing = hmac.new(
            self.app_secret.encode("utf-8"),
            timestamp.encode("utf-8"),
            hashlib.sha256
        ).digest()
        
        # 第三步：计算最终签名
        signature = hmac.new(
            secret_signing,
            sign_text.encode("utf-8"),
            hashlib.sha256
        ).hexdigest().lower()
        
        return signature
    
    def _build_headers(
        self,
        access_token: Optional[str] = None,
        biz_content: Optional[str] = None,
        grant_type: Optional[str] = None
    ) -> tuple[Dict[str, str], Dict[str, str]]:
        """构建请求头和数据体。
        
        Args:
            access_token: 访问凭证
            biz_content: 业务参数 JSON 字符串
            grant_type: 授权类型 (client_credential / authorization_code)
            
        Returns:
            (headers, data) 元组
        """
        timestamp = str(int(time.time() * 1000))
        nonce = uuid.uuid4().hex[:32]
        
        # 构建签名参数
        sign_params = {
            "X-FASC-App-Id": self.app_id,
            "X-FASC-Sign-Type": "HMAC-SHA256",
            "X-FASC-Timestamp": timestamp,
            "X-FASC-Nonce": nonce,
            "X-FASC-Api-SubVersion": "5.1"
        }
        
        if access_token:
            sign_params["X-FASC-AccessToken"] = access_token
        
        if grant_type:
            sign_params["X-FASC-Grant-Type"] = grant_type
        
        if biz_content:
            sign_params["bizContent"] = biz_content
        
        # 计算签名
        param_str = self._sort_parameters(sign_params)
        signature = self._generate_signature(param_str, timestamp)
        
        # 构建请求头
        headers = {
            "X-FASC-App-Id": self.app_id,
            "X-FASC-Sign-Type": "HMAC-SHA256",
            "X-FASC-Sign": signature,
            "X-FASC-Timestamp": timestamp,
            "X-FASC-Nonce": nonce,
            "X-FASC-Api-SubVersion": "5.1",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        if access_token:
            headers["X-FASC-AccessToken"] = access_token
        
        if grant_type:
            headers["X-FASC-Grant-Type"] = grant_type
        
        # 构建数据体
        data = {}
        if biz_content:
            data["bizContent"] = biz_content
        
        return headers, data
    
    def get_access_token(self) -> str:
        """获取 Access Token（带缓存）。

        Returns:
            访问凭证字符串

        Raises:
            APIError: 获取失败时抛出
        """
        # 检查缓存
        if self._access_token and time.time() < self._token_expires_at:
            return self._access_token

        # 调用获取凭证接口
        url = f"{self.server_url}/service/get-access-token"

        timestamp = str(int(time.time() * 1000))
        nonce = uuid.uuid4().hex[:32]

        # 构建签名参数
        sign_params = {
            "X-FASC-App-Id": self.app_id,
            "X-FASC-Sign-Type": "HMAC-SHA256",
            "X-FASC-Timestamp": timestamp,
            "X-FASC-Nonce": nonce,
            "X-FASC-Grant-Type": "client_credential",
            "X-FASC-Api-SubVersion": "5.1"
        }

        # 计算签名
        param_str = self._sort_parameters(sign_params)
        signature = self._generate_signature(param_str, timestamp)

        # 构建请求头（使用 application/json）
        headers = {
            "X-FASC-App-Id": self.app_id,
            "X-FASC-Sign-Type": "HMAC-SHA256",
            "X-FASC-Sign": signature,
            "X-FASC-Timestamp": timestamp,
            "X-FASC-Nonce": nonce,
            "X-FASC-Grant-Type": "client_credential",
            "X-FASC-Api-SubVersion": "5.1",
            "Content-Type": "application/json"
        }

        # 构建请求体（包含 appId）
        biz_content = json.dumps({
            "appId": self.app_id,
            "grantType": "client_credential"
        }, separators=(",", ":"))

        import requests
        response = requests.post(url, headers=headers, json=biz_content, timeout=30)
        result = response.json()

        code = result.get("code")
        if code != "100000":
            msg = result.get("msg", "获取访问凭证失败")
            raise APIError(msg, code=code)

        # 更新缓存
        self._access_token = result["data"]["accessToken"]
        expires_in = int(result["data"].get("expiresIn", 7200))
        self._token_expires_at = time.time() + expires_in - 300

        return self._access_token
    
    def request(
        self,
        endpoint: str,
        biz_content: Optional[Dict] = None,
        access_token: Optional[str] = None,
        method: str = "POST"
    ) -> Dict[str, Any]:
        """发起 API 请求。
        
        Args:
            endpoint: API 端点路径
            biz_content: 业务参数字典
            access_token: 访问凭证（不传则自动获取）
            method: 请求方法 GET/POST
            
        Returns:
            API 响应数据字典
            
        Raises:
            APIError: 请求失败时抛出
        """
        url = f"{self.server_url}{endpoint}"
        
        # 自动获取 Token（除获取凭证接口外）
        if access_token is None and endpoint != "/service/get-access-token":
            access_token = self.get_access_token()
        
        # 构建请求体
        biz_content_str = None
        if biz_content:
            biz_content_str = json.dumps(biz_content, separators=(",", ":"), ensure_ascii=False)
        
        headers, data = self._build_headers(access_token, biz_content_str)
        
        import requests
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, params=data, timeout=30)
            else:
                response = requests.post(url, headers=headers, data=data, timeout=30)
            
            response.raise_for_status()
            result = response.json()
            
            code = result.get("code")
            if code != "100000":
                msg = result.get("msg", "API请求失败")
                raise APIError(msg, code=code)
            
            return result.get("data", {})
            
        except requests.RequestException as e:
            raise APIError(f"请求失败: {e}")


# =============================================================================
# 错误处理
# =============================================================================

class FASCError(Exception):
    """法大大电子签基础错误类。"""
    pass


class APIError(FASCError):
    """API 调用错误。"""
    
    def __init__(self, message: str, code: str = None):
        super().__init__(message)
        self.code = code


class FileError(FASCError):
    """文件处理错误。"""
    pass


# =============================================================================
# 工具函数
# =============================================================================

def load_skill_context(raw: str) -> dict:
    """解析 skill context JSON。
    
    Args:
        raw: JSON 字符串或空字符串
        
    Returns:
        解析后的字典，空字符串返回空字典
    """
    if not raw or not raw.strip():
        return {}
    
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"Invalid --skill-context-json payload: {exc}", file=sys.stderr)
        return {}


def with_retry(max_attempts: int = 3, backoff: str = "exponential") -> Callable:
    """重试装饰器。
    
    Args:
        max_attempts: 最大重试次数
        backoff: 退避策略 "exponential" 或 "linear"
        
    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as exc:
                    if attempt == max_attempts:
                        raise
                    
                    if backoff == "exponential":
                        delay = 2 ** (attempt - 1)
                    else:
                        delay = attempt
                    
                    time.sleep(delay)
            
            raise RuntimeError(f"Max retries ({max_attempts}) exceeded")
        
        return wrapper
    return decorator


# =============================================================================
# 响应处理
# =============================================================================

def success_response(data: Any = None, message: str = "成功") -> dict:
    """构建成功响应。
    
    Args:
        data: 响应数据
        message: 消息文本
        
    Returns:
        标准响应字典
    """
    return {
        "success": True,
        "message": message,
        "data": data or {}
    }


def error_response(message: str, code: str = None, details: Any = None) -> dict:
    """构建错误响应。
    
    Args:
        message: 错误消息
        code: 错误码
        details: 详细错误信息
        
    Returns:
        标准错误响应字典
    """
    result = {
        "success": False,
        "error": message
    }
    if code:
        result["code"] = code
    if details:
        result["details"] = details
    
    return result


def print_result(result: dict) -> None:
    """输出结果并退出。
    
    Args:
        result: 结果字典
    """
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 根据成功/失败设置退出码
    if result.get("success"):
        sys.exit(0)
    else:
        sys.exit(1)
