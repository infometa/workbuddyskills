#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
唯品会二维码客户端模块

负责获取二维码、生成二维码图片并在终端展示或打开图片文件。

API接口:
- 初始化: POST https://passport.vip.com/qrLogin/initQrLogin
- 获取图片: GET https://passport.vip.com/qrLogin/getQrImage?qrToken=xxx
"""

import sys
import os
import io
import time
import base64
import tempfile
import subprocess
import platform
from typing import Optional, Tuple
from pathlib import Path

import requests
import qrcode
from PIL import Image


class QRCodeClient:
    """二维码客户端"""
    
    def __init__(self, base_url: str, init_endpoint: str, image_endpoint: str, session: Optional[requests.Session] = None):
        """
        初始化二维码客户端
        
        Args:
            base_url: API基础URL，如 https://passport.vip.com
            init_endpoint: 初始化二维码接口路径，如 /qrLogin/initQrLogin
            image_endpoint: 获取二维码图片接口路径，如 /qrLogin/getQrImage
            session: 可选的共享session，用于保持Cookie会话
        """
        self.base_url = base_url.rstrip('/')
        self.init_endpoint = init_endpoint
        self.image_endpoint = image_endpoint
        
        # 使用传入的session或创建新session
        if session is not None:
            self.session = session
        else:
            self.session = requests.Session()
            # 设置请求头
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Referer': f'{self.base_url}/',
                'Origin': self.base_url,
            })
    
    def init_qr_code(self, where_from: str = "") -> Tuple[bool, Optional[str], Optional[dict]]:
        """
        初始化二维码，获取qrToken
        
        Args:
            where_from: 请求来源标识（可选）
            
        Returns:
            (成功标志, qrToken, 完整响应数据)
        """
        url = f"{self.base_url}{self.init_endpoint}"
        
        # 构造请求参数
        data = {}
        if where_from:
            data['whereFrom'] = where_from
        
        try:
            response = self.session.post(url, data=data, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            
            # 检查响应状态
            if result.get('code') == 200:
                qr_token = result.get('qrToken')
                if qr_token:
                    print(f"[QRCodeClient] 初始化二维码成功，qrToken: {qr_token}")
                    return True, qr_token, result
                else:
                    print(f"[QRCodeClient] 响应中未找到qrToken: {result}")
                    return False, None, result
            else:
                print(f"[QRCodeClient] 初始化二维码失败: {result.get('msg', '未知错误')}")
                return False, None, result
                
        except requests.exceptions.RequestException as e:
            print(f"[QRCodeClient] 请求失败: {e}")
            return False, None, None
        except Exception as e:
            print(f"[QRCodeClient] 处理响应失败: {e}")
            return False, None, None
    
    def get_qr_image(self, qr_token: str) -> Tuple[bool, Optional[bytes], Optional[str]]:
        """
        获取二维码图片
        
        Args:
            qr_token: 二维码TOKEN
            
        Returns:
            (成功标志, 图片二进制数据, 图片格式如'png')
        """
        url = f"{self.base_url}{self.image_endpoint}"
        params = {
            'qrToken': qr_token
        }
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            content_type = response.headers.get('Content-Type', '')
            
            # 判断响应类型 - 直接返回图片流
            if 'image' in content_type:
                # 提取格式，去除 charset 等后缀，如 "image/png;charset=UTF-8" -> "png"
                image_format = content_type.split('/')[-1].split(';')[0].strip() if '/' in content_type else 'png'
                return True, response.content, image_format
            else:
                print(f"[QRCodeClient] 未知的响应类型: {content_type}")
                return False, None, None
                
        except requests.exceptions.RequestException as e:
            print(f"[QRCodeClient] 获取二维码图片失败: {e}")
            return False, None, None
    
    def get_qr_image_url(self, qr_token: str) -> str:
        """
        获取二维码图片URL
        
        Args:
            qr_token: 二维码TOKEN
            
        Returns:
            二维码图片完整URL
        """
        return f"{self.base_url}{self.image_endpoint}?qrToken={qr_token}"
    
    def generate_qr_from_string(self, content: str, size: int = 300) -> Image.Image:
        """
        从字符串生成二维码图片（备用方案）
        
        Args:
            content: 二维码内容
            size: 二维码尺寸
            
        Returns:
            PIL Image对象
        """
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(content)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        img = img.resize((size, size), Image.Resampling.LANCZOS)
        
        return img
    
    def display_qr_in_terminal(self, image_bytes: bytes) -> bool:
        """
        保存二维码图片并显示路径（终端字符显示可能变形，推荐直接保存图片）
        
        Args:
            image_bytes: 图片二进制数据
            
        Returns:
            是否保存成功
        """
        try:
            # 保存到文件
            file_path = self.save_qr_image(image_bytes, 'png')
            
            if file_path:
                print("\n" + "=" * 50)
                print("二维码已保存，请使用唯品会APP扫描")
                print("=" * 50)
                print(f"图片路径: {file_path}")
                print("=" * 50 + "\n")
                return True
            else:
                return False
                
        except Exception as e:
            print(f"[QRCodeClient] 保存二维码失败: {e}")
            return False
    
    def open_qr_image(self, image_bytes: bytes, image_format: str = 'png') -> bool:
        """
        打开二维码图片文件（保存到固定位置并自动清理旧文件）
        
        Args:
            image_bytes: 图片二进制数据
            image_format: 图片格式
            
        Returns:
            是否成功打开
        """
        try:
            # 使用固定目录保存二维码
            qr_dir = Path.home() / ".vipshop-user-login" / "qr_codes"
            qr_dir.mkdir(parents=True, exist_ok=True)
            
            # 清理旧的二维码文件
            self._cleanup_old_qr_files(qr_dir)
            
            # 使用固定文件名（带时间戳避免冲突）
            file_path = qr_dir / f"login_qr.{image_format}"
            
            with open(file_path, 'wb') as f:
                f.write(image_bytes)
            
            print(f"[QRCodeClient] 二维码已保存到: {file_path}")
            print("[QRCodeClient] 正在打开图片...")
            
            # 根据操作系统打开图片
            system = platform.system()
            
            if system == 'Darwin':  # macOS
                subprocess.run(['open', str(file_path)], check=True)
            elif system == 'Linux':
                subprocess.run(['xdg-open', str(file_path)], check=True)
            elif system == 'Windows':
                os.startfile(str(file_path))
            else:
                print(f"[QRCodeClient] 不支持的操作系统: {system}")
                return False
            
            return True
            
        except Exception as e:
            print(f"[QRCodeClient] 打开图片失败: {e}")
            return False
    
    def _cleanup_old_qr_files(self, qr_dir: Path):
        """清理目录中的旧二维码文件"""
        try:
            for file_path in qr_dir.glob("login_qr.*"):
                try:
                    file_path.unlink()
                except Exception:
                    pass
        except Exception:
            pass
    
    def cleanup_qr_files(self):
        """清理所有二维码文件（公共接口，登录完成后可调用）"""
        try:
            qr_dir = Path.home() / ".vipshop-user-login" / "qr_codes"
            if qr_dir.exists():
                for file_path in qr_dir.iterdir():
                    try:
                        file_path.unlink()
                    except Exception:
                        pass
                # 尝试删除空目录
                try:
                    qr_dir.rmdir()
                except Exception:
                    pass
        except Exception as e:
            print(f"[QRCodeClient] 清理二维码文件失败: {e}")
    
    def save_qr_image(self, image_bytes: bytes, image_format: str = 'png', 
                     output_path: Optional[str] = None) -> Optional[str]:
        """
        保存二维码图片到指定路径
        
        Args:
            image_bytes: 图片二进制数据
            image_format: 图片格式
            output_path: 输出路径，默认为临时文件
            
        Returns:
            保存的文件路径
        """
        try:
            if output_path:
                file_path = Path(output_path)
            else:
                # 保存到默认位置
                save_dir = Path.home() / ".vipshop-user-login" / "qr_codes"
                save_dir.mkdir(parents=True, exist_ok=True)
                file_path = save_dir / f"login_qr_{int(time.time())}.{image_format}"
            
            with open(file_path, 'wb') as f:
                f.write(image_bytes)
            
            print(f"[QRCodeClient] 二维码已保存: {file_path}")
            return str(file_path)
            
        except Exception as e:
            print(f"[QRCodeClient] 保存图片失败: {e}")
            return None
    
    def get_and_show_qr_code(self, qr_token: str, show_in_terminal: bool = False) -> bool:
        """
        获取并展示二维码的便捷方法
        
        Args:
            qr_token: 二维码TOKEN
            show_in_terminal: 是否在终端显示（False则打开图片）
            
        Returns:
            是否成功
        """
        success, image_bytes, image_format = self.get_qr_image(qr_token)
        
        if not success or not image_bytes:
            print("[QRCodeClient] 获取二维码图片失败")
            return False
        
        if show_in_terminal:
            return self.display_qr_in_terminal(image_bytes)
        else:
            return self.open_qr_image(image_bytes, image_format or 'png')


# 便捷函数
def create_default_client() -> QRCodeClient:
    """创建默认配置的二维码客户端"""
    return QRCodeClient(
        base_url="https://passport.vip.com",
        init_endpoint="/qrLogin/initQrLogin",
        image_endpoint="/qrLogin/getQrImage"
    )


if __name__ == "__main__":
    # 测试代码
    print("QRCodeClient 测试")
    print("-" * 50)
    
    client = create_default_client()
    
    # 测试生成二维码
    test_content = "https://passport.vip.com/qrLogin?qrToken=test-token-12345"
    print(f"\n测试内容: {test_content}")
    
    img = client.generate_qr_from_string(test_content, size=200)
    
    # 保存测试图片
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    image_bytes = buffer.getvalue()
    
    # 测试终端显示
    print("\n测试终端显示:")
    client.display_qr_in_terminal(image_bytes)
    
    # 测试打开图片
    print("\n测试打开图片文件:")
    client.open_qr_image(image_bytes)
