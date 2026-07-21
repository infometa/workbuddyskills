#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
唯品会登录状态轮询模块

负责轮询二维码的登录状态，检测扫码和确认登录事件。

API接口:
- 轮询状态: POST https://passport.vip.com/qrLogin/checkStatus

状态值说明:
- NOT_SCANNED: 未扫描
- SCANNED: 已扫描
- CONFIRMED: 已确认（登录成功）
- INVALID: 已失效
"""

import sys
import io
import time
import threading
from enum import Enum
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass

import requests

import logger  # 日志上报模块


class LoginStatus(Enum):
    """登录状态枚举"""
    NOT_SCANNED = "NOT_SCANNED"   # 未扫描
    SCANNED = "SCANNED"           # 已扫描
    CONFIRMED = "CONFIRMED"       # 已确认登录（成功）
    INVALID = "INVALID"           # 已失效
    ERROR = "ERROR"               # 发生错误


@dataclass
class StatusResult:
    """状态查询结果"""
    status: LoginStatus
    status_str: str
    message: str
    redirect_url: Optional[str] = None
    version: Optional[str] = None  # skill 版本号
    raw_response: Optional[Dict] = None
    raw_http_response: Optional[requests.Response] = None  # AI-Generated: 原始HTTP响应对象，用于提取cookies


class StatusPoller:
    """状态轮询器"""
    
    # 状态字符串映射
    STATUS_MAP = {
        "NOT_SCANNED": LoginStatus.NOT_SCANNED,
        "SCANNED": LoginStatus.SCANNED,
        "CONFIRMED": LoginStatus.CONFIRMED,
        "INVALID": LoginStatus.INVALID,
    }
    
    def __init__(self, base_url: str, check_endpoint: str,
                 poll_interval: int = 1, timeout: int = 180, session: Optional[requests.Session] = None):
        """
        初始化状态轮询器
        
        Args:
            base_url: API基础URL
            check_endpoint: 状态检查接口路径
            poll_interval: 轮询间隔（秒），建议每秒轮询一次
            timeout: 总超时时间（秒），二维码有效期约3分钟
            session: 可选的共享session，用于保持Cookie会话
        """
        self.base_url = base_url.rstrip('/')
        self.check_endpoint = check_endpoint
        self.poll_interval = poll_interval
        self.timeout = timeout
        
        # 使用传入的session或创建新session
        if session is not None:
            self.session = session
        else:
            self.session = requests.Session()
            # 设置请求头
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'zh-CN,zh;q=0.9',
                'Referer': f'{self.base_url}/',
                'Origin': self.base_url,
            })
        
        self._stop_event = threading.Event()
        self._polling_thread: Optional[threading.Thread] = None
    
    def check_status(self, qr_token: str, where_from: str = "") -> StatusResult:
        """
        单次检查二维码状态
        
        Args:
            qr_token: 二维码TOKEN
            where_from: 请求来源标识（可选）
            
        Returns:
            状态结果
        """
        url = f"{self.base_url}{self.check_endpoint}"
        
        data = {
            'qrToken': qr_token
        }
        if where_from:
            data['whereFrom'] = where_from
        
        try:
            response = self.session.post(url, data=data, timeout=10)
            response.raise_for_status()
            
            result = response.json()

            # 检查响应状态码
            if result.get('code') != 200:
                message = result.get('msg', '请求失败')
                return StatusResult(
                    status=LoginStatus.ERROR,
                    status_str="ERROR",
                    message=message,
                    raw_response=result,
                    raw_http_response=response  # AI-Generated
                )
            
            # 提取状态字符串
            status_str = result.get('status', 'NOT_SCANNED')
            login_status = self.STATUS_MAP.get(status_str, LoginStatus.ERROR)
            
            # 提取消息
            message = result.get('msg', '') or self._get_status_message(login_status)
            
            # 提取跳转URL
            redirect_url = result.get('redirectUrl')
            
            # 提取版本号
            version = result.get('version')

            # 记录 checkStatus 响应（仅在 CONFIRMED 时记录完整信息，避免高频轮询刷屏）
            if login_status == LoginStatus.CONFIRMED:
                logger.info("check_status_response", status_str=status_str, version=str(version), raw_keys=str(list(result.keys())))
            else:
                logger.debug("check_status_polling", status_str=status_str, version=str(version))

            return StatusResult(
                status=login_status,
                status_str=status_str,
                message=message,
                redirect_url=redirect_url,
                version=version,
                raw_response=result,
                raw_http_response=response  # AI-Generated
            )
            
        except requests.exceptions.RequestException as e:
            return StatusResult(
                status=LoginStatus.ERROR,
                status_str="ERROR",
                message=f"请求失败: {e}",
                raw_response=None,
                raw_http_response=None  # AI-Generated
            )
        except Exception as e:
            return StatusResult(
                status=LoginStatus.ERROR,
                status_str="ERROR",
                message=f"处理失败: {e}",
                raw_response=None,
                raw_http_response=None  # AI-Generated
            )
    
    def _get_status_message(self, status: LoginStatus) -> str:
        """获取状态描述"""
        messages = {
            LoginStatus.NOT_SCANNED: "等待扫码",
            LoginStatus.SCANNED: "已扫码，等待确认",
            LoginStatus.CONFIRMED: "登录成功",
            LoginStatus.INVALID: "二维码已失效",
            LoginStatus.ERROR: "发生错误",
        }
        return messages.get(status, "未知状态")
    
    def poll_until_complete(self, qr_token: str, where_from: str = "",
                           on_status_change: Optional[Callable[[StatusResult], None]] = None,
                           on_scanned: Optional[Callable[[StatusResult], None]] = None,
                           on_confirmed: Optional[Callable[[StatusResult], None]] = None,
                           on_invalid: Optional[Callable[[StatusResult], None]] = None) -> StatusResult:
        """
        轮询直到登录完成或超时
        
        Args:
            qr_token: 二维码TOKEN
            where_from: 请求来源标识（可选）
            on_status_change: 状态变更回调
            on_scanned: 已扫码回调
            on_confirmed: 已确认登录回调
            on_invalid: 二维码失效回调
            
        Returns:
            最终结果
        """
        print(f"[StatusPoller] 开始轮询qrToken: {qr_token}")
        print(f"[StatusPoller] 轮询间隔: {self.poll_interval}秒, 超时: {self.timeout}秒")
        
        start_time = time.time()
        last_status = None
        
        while time.time() - start_time < self.timeout:
            result = self.check_status(qr_token, where_from)
            
            # 状态变更时触发回调
            if result.status != last_status:
                last_status_desc = self._get_status_message(last_status) if last_status else "初始"
                print(f"[StatusPoller] 状态变更: {last_status_desc} -> {self._get_status_message(result.status)}")
                
                if on_status_change:
                    on_status_change(result)
                
                # 特定状态回调
                if result.status == LoginStatus.SCANNED and on_scanned:
                    print("[StatusPoller] 用户已扫码，等待确认登录...")
                    on_scanned(result)
                
                elif result.status == LoginStatus.CONFIRMED and on_confirmed:
                    print("[StatusPoller] 登录已确认!")
                    on_confirmed(result)
                    return result
                
                elif result.status == LoginStatus.INVALID and on_invalid:
                    print("[StatusPoller] 二维码已失效")
                    on_invalid(result)
                    return result
                
                elif result.status == LoginStatus.ERROR:
                    print(f"[StatusPoller] 发生错误: {result.message}")
                    # 可以选择继续轮询或返回错误
            
            last_status = result.status
            
            # 检查是否已完成
            if result.status in [LoginStatus.CONFIRMED, LoginStatus.INVALID]:
                return result
            
            # 等待下一轮
            time.sleep(self.poll_interval)
        
        # 超时
        print("[StatusPoller] 轮询超时")
        return StatusResult(
            status=LoginStatus.ERROR,
            status_str="TIMEOUT",
            message="轮询超时"
        )
    
    def start_async_poll(self, qr_token: str, where_from: str = "",
                        on_status_change: Optional[Callable[[StatusResult], None]] = None,
                        on_complete: Optional[Callable[[StatusResult], None]] = None):
        """
        启动异步轮询
        
        Args:
            qr_token: 二维码TOKEN
            where_from: 请求来源标识（可选）
            on_status_change: 状态变更回调
            on_complete: 完成回调
        """
        self._stop_event.clear()
        
        def poll_worker():
            result = self.poll_until_complete(
                qr_token,
                where_from=where_from,
                on_status_change=on_status_change,
                on_confirmed=on_complete,
                on_invalid=on_complete
            )
            if on_complete:
                on_complete(result)
        
        self._polling_thread = threading.Thread(target=poll_worker, daemon=True)
        self._polling_thread.start()
    
    def stop_poll(self):
        """停止轮询"""
        self._stop_event.set()
        if self._polling_thread and self._polling_thread.is_alive():
            self._polling_thread.join(timeout=1)


def create_default_poller() -> StatusPoller:
    """创建默认配置的状态轮询器"""
    return StatusPoller(
        base_url="https://passport.vip.com",
        check_endpoint="/qrLogin/checkStatus",
        poll_interval=1,
        timeout=180
    )


if __name__ == "__main__":
    # 测试代码
    print("StatusPoller 测试")
    print("-" * 50)
    
    poller = create_default_poller()
    
    # 测试状态码映射
    print("\n状态码映射:")
    for code, status in poller.STATUS_MAP.items():
        print(f"  {code}: {status.name} - {poller._get_status_message(status)}")
