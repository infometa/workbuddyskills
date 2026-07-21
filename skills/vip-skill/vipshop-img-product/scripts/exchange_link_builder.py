#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VIPShop Exchange Token 链接生成器

用于生成带有 HMAC-MD5 签名的 exchange token 链接
"""

import json
import base64
import hmac
import hashlib
import urllib.parse
import time
from pathlib import Path
import sys
import os


# 日志打印开关，设置为 True 开启详细日志
DEBUG = False


def log(message: str):
    """打印日志信息"""
    if DEBUG:
        print(f"[EXCHANGE_LINK] {message}", file=sys.stderr)


def log_error(message: str, error: Exception = None):
    """打印错误日志"""
    if DEBUG:
        print(f"[EXCHANGE_LINK ERROR] {message}", file=sys.stderr)
        if error:
            print(f"  -> 异常类型: {type(error).__name__}", file=sys.stderr)
            print(f"  -> 异常信息: {error}", file=sys.stderr)


def _get_secret() -> str:
    """
    获取 secret key

    Returns:
        secret key 字符串
    """
    return "5fb86e55b72bfc50f083049130e5e76a75c2cbda6bbd6e51d59668057f5c1715"


def _get_token() -> str:
    """
    从 token 文件获取 PASSPORT_ACCESS_TOKEN
    参考 search.py 的 load_login_tokens 方法

    Returns:
        token 字符串，如果未获取到则返回空字符串
    """
    log("=" * 50)
    log("开始获取 token...")

    token_file = Path.home() / ".vipshop-user-login" / "tokens.json"
    log(f"token 文件路径: {token_file}")

    if not token_file.exists():
        log(f"❌ token 文件不存在: {token_file}")
        return ""

    log("✅ token 文件存在")

    try:
        with open(token_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        log(f"✅ 成功读取 token 文件")
        log(f"  数据类型: {type(data)}")

        # 检查是否是新格式（包含cookies字段）
        if data and isinstance(data, dict) and 'cookies' in data:
            log("✅ 数据格式正确，包含 cookies 字段")

            # 检查token是否过期
            expires_at = data.get('expires_at')
            log(f"  expires_at: {expires_at}")

            if expires_at and time.time() > expires_at:
                log("❌ token 已过期")
                return ""

            cookies = data.get('cookies', {})
            log(f"  cookies 数量: {len(cookies)}")
            log(f"  cookies 键: {list(cookies.keys())}")

            token = cookies.get("PASSPORT_ACCESS_TOKEN", "")
            if token:
                log(f"✅ 成功获取 PASSPORT_ACCESS_TOKEN")
                log(f"  token 长度: {len(token)}")
                log(f"  token 前10位: {token[:10]}...")
                return token
            else:
                log("❌ cookies 中不存在 PASSPORT_ACCESS_TOKEN")
                return ""
        else:
            log(f"❌ 数据格式不正确，缺少 cookies 字段")
            log(f"  数据内容: {str(data)[:100]}...")
            return ""

    except json.JSONDecodeError as e:
        log_error("token 文件 JSON 解析失败", e)
        return ""
    except Exception as e:
        log_error("读取 token 文件时发生异常", e)
        return ""


def _generate_signature(data: str, secret: str) -> str:
    """
    生成 HMAC-MD5 签名

    Args:
        data: 待签名的数据（Base64 编码后的字符串）
        secret: 签名密钥

    Returns:
        大写的 HMAC-MD5 签名
    """
    log(f"  生成签名 - 数据长度: {len(data)}, secret 长度: {len(secret)}")

    signature = hmac.new(
        secret.encode("utf-8"), data.encode("utf-8"), hashlib.md5
    ).hexdigest()

    result = signature.upper()
    log(f"  签名结果: {result[:20]}...")

    return result


def build_exchange_link(target_url: str) -> str:
    """
    生成 exchange token 链接

    Args:
        target_url: 目标 URL（商品详情页）

    Returns:
        完整的 exchange token 链接
    """
    log("=" * 50)
    log(f"开始生成 exchange 链接")
    log(f"目标 URL: {target_url}")

    # 获取 token
    token = _get_token()
    if not token:
        log("⚠️ token 为空，直接返回原始目标 URL")
        # 如果没有 token，直接返回原始目标 URL
        return target_url

    log("✅ 成功获取 token")

    # 获取 secret key
    secret = _get_secret()
    log(f"获取 secret key: {secret[:10]}... (长度: {len(secret)})")

    # 构造数据对象
    timestamp = int(time.time() * 1000)  # 毫秒时间戳
    data_obj = {"t": token, "ts": timestamp}
    log(f"构造数据对象: t=<token>, ts={timestamp}")

    # 转换为 JSON 字符串
    json_str = json.dumps(data_obj, separators=(",", ":"))
    log(f"JSON 字符串: {json_str[:50]}... (长度: {len(json_str)})")

    # Base64 编码
    base64_str = base64.b64encode(json_str.encode("utf-8")).decode("utf-8")
    log(f"Base64 编码结果: {base64_str[:50]}... (长度: {len(base64_str)})")

    # 生成签名
    signature = _generate_signature(base64_str, secret)
    log(f"生成签名: {signature[:20]}... (长度: {len(signature)})")

    # 构造完整链接
    base_url = "https://passport.vip.com/exchangeTokenFromApp"
    full_url = (
        f"{base_url}?"
        f"dt={urllib.parse.quote(base64_str)}&"
        f"sg={signature}&"
        f"src={urllib.parse.quote(target_url)}"
    )

    log(f"✅ 链接生成成功，总长度: {len(full_url)}")
    log(f"完整链接: {full_url[:100]}...")

    return full_url


def build_product_link(brand_id: str, product_id: str) -> str:
    """
    生成商品详情页的 exchange token 链接

    Args:
        brand_id: 品牌 ID
        product_id: 商品 ID

    Returns:
        带有 exchange token 的商品详情链接
    """
    log("=" * 50)
    log(f"生成商品链接: brand_id={brand_id}, product_id={product_id}")

    # 构造目标 URL
    target_url = f"https://detail.vip.com/detail-{brand_id}-{product_id}.html?pcf=AIClaw"
    log(f"构造目标 URL: {target_url}")

    # 生成 exchange 链接
    return build_exchange_link(target_url)


if __name__ == "__main__":
    log("=" * 50)
    log("开始测试 exchange_link_builder")
    log(f"Python 版本: {sys.version}")
    log(f"工作目录: {Path.cwd()}")

    # 测试代码
    test_url = "https://detail.vip.com/detail-123-456.html?pcf=AIClaw"
    log(f"\n测试1: 使用 URL 生成链接")
    link = build_exchange_link(test_url)
    print(f"生成的链接: {link}")

    # 测试商品链接
    log(f"\n测试2: 使用 brand_id 和 product_id 生成链接")
    product_link = build_product_link("brand123", "product456")
    print(f"商品链接: {product_link}")

    log("\n测试完成")
