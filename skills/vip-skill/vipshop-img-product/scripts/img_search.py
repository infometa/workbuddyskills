#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
唯品会图片搜索商品工具
通过图片URL或上传图片搜索相似商品
"""

import sys
import json
import time
import urllib.request
import urllib.parse
import os
from pathlib import Path
from typing import Dict, Any, Optional
from exchange_link_builder import build_product_link


# 支持的图片类型
SUPPORTED_IMAGE_TYPES = {
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'
}

# API配置
UPLOAD_API = "https://mapi-file-tx.vip.com/xupload/picture/new_upload_inner_applet.jsps"
CATEGORY_API = "https://mapi-pc.vip.com/vips-mobile/rest/shopping/skill/search/img/category/v1"
PRODUCT_API = "https://mapi-pc.vip.com/vips-mobile/rest/shopping/skill/image/product/list/v1"
API_KEY = "dafe77e7486f46eca2e17a256d3ce6b5"


def validate_image(file_path: str) -> bool:
    """
    验证文件是否为支持的图片类型
    
    Args:
        file_path: 文件路径
        
    Returns:
        是否为有效的图片文件
    """
    ext = os.path.splitext(file_path)[1].lower()
    if ext not in SUPPORTED_IMAGE_TYPES:
        return False
    
    if not os.path.exists(file_path):
        return False
    
    return True


def is_url(path: str) -> bool:
    """
    判断是否为URL
    
    Args:
        path: 路径字符串
        
    Returns:
        是否为URL
    """
    return path.startswith('http://') or path.startswith('https://')


def process_image_url(image_url: str) -> str:
    """
    处理图片URL，添加裁剪参数和webp格式

    Args:
        image_url: 原始图片URL

    Returns:
        处理后的图片URL
    """
    import re

    if not image_url:
        return image_url

    # 支持的域名列表
    supported_domains = [
        "a.appsimg.com", "b.appsimg.com", "h2.appsimg.com",
        "a.vpimg1.com", "c.vpimg1.com", "d.vpimg1.com",
        "a.vpimg2.com", "a.vpimg3.com", "a.vpimg4.com",
        "img1.vipshop.com"
    ]

    # 需要替换为 a.appsimg.com 的域名
    domains_to_replace = [
        "a.vpimg1.com", "c.vpimg1.com", "d.vpimg1.com",
        "a.vpimg2.com", "a.vpimg3.com", "a.vpimg4.com",
        "img1.vipshop.com"
    ]

    # 第一步：判断图片是否支持增加webp后缀
    url_lower = image_url.lower()
    support_webp = True

    # (1) 如果后缀是webp结尾；不支持
    if url_lower.endswith(".webp"):
        support_webp = False

    # (2) 是否是PNG结尾，不支持
    if url_lower.endswith(".png"):
        support_webp = False

    # (3) 是否是APNG，不支持（判断URL参数有ext=apng）
    if "ext=apng" in url_lower:
        support_webp = False

    # (4) 域名必须是指定域名
    domain_matched = False
    for domain in supported_domains:
        if domain in image_url:
            domain_matched = True
            break

    if not domain_matched:
        support_webp = False

    # 第二步：判断是否支持裁剪参数拼接
    support_crop = True

    # (1) 不是gif、不是apng
    if url_lower.endswith(".gif") or "ext=apng" in url_lower:
        support_crop = False

    # (2) 没有匹配到格式：(_\d+x\d+)_(\d+)\.{1}  例如：_1920x1080_30.
    pattern = r'_\d+x\d+_\d+\.'
    if re.search(pattern, image_url):
        support_crop = False

    # 第三步：处理裁剪参数拼接
    if support_crop:
        # (1) 替换域名
        for old_domain in domains_to_replace:
            if old_domain in image_url:
                image_url = image_url.replace(old_domain, "a.appsimg.com")
                break

        # (2) 添加裁剪参数：把.jpg 替换成 _200x200.jpg
        if image_url.lower().endswith(".jpg"):
            image_url = image_url[:-4] + "_200x200_90.jpg"
        elif image_url.lower().endswith(".jpeg"):
            image_url = image_url[:-5] + "_200x200_90.jpeg"

    # 第四步：处理webp参数
    if support_webp:
        # 添加 !85.webp 后缀
        image_url = image_url + "!85.webp"

    return image_url


def load_login_tokens() -> Optional[Dict[str, Any]]:
    """
    加载登录态
    
    Returns:
        登录态字典，包含mars_cid和access_token；如果未登录返回None
    """
    token_file = Path.home() / ".vipshop-user-login" / "tokens.json"
    
    if not token_file.exists():
        return None
    
    try:
        with open(token_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if data and isinstance(data, dict) and 'cookies' in data:
            # 检查token是否过期
            expires_at = data.get('expires_at')
            if expires_at and time.time() > expires_at:
                return None
            cookies = data.get('cookies', {})
            return {
                'mars_cid': cookies.get('mars_cid', ''),
                'access_token': cookies.get('PASSPORT_ACCESS_TOKEN', '')
            }
        return None
    except Exception as e:
        sys.stderr.write(f"加载登录态失败: {e}\n")
        return None


def upload_image(file_path: str, mars_cid: str, access_token: str) -> Dict[str, Any]:
    """
    第一步：上传图片到唯品会服务器
    
    使用微信小程序上传API，无需签名验证
    
    Args:
        file_path: 图片文件路径
        mars_cid: 用户标识
        access_token: 用户访问令牌
        
    Returns:
        上传结果，包含图片URL
    """
    try:
        # 构建multipart/form-data请求 - 使用微信小程序格式
        boundary = 'WABoundary+' + ''.join([format(int(time.time() * 1000) % 16, 'X') for _ in range(16)]) + 'WA'

        with open(file_path, 'rb') as f:
            file_data = f.read()

        file_name = os.path.basename(file_path)

        # 构建请求体 - 只需要 File
        body_parts = []

        # 添加文件字段
        body_parts.append(f'--{boundary}'.encode('utf-8'))
        body_parts.append(f'Content-Disposition: form-data; name="picture"; filename="{file_name}"'.encode('utf-8'))
        body_parts.append(b'Content-Type: image/jpeg')
        body_parts.append(b'')
        body_parts.append(file_data)

        body_parts.append(f'--{boundary}--'.encode('utf-8'))
        body_parts.append(b'')

        body = b'\r\n'.join(body_parts)

        # 构建URL参数
        upload_params = {
            'app_name': 'shop_weixin_mina',
            'client': 'wechat_mini_program',
            'source_app': 'shop_weixin_mina',
            'api_key': API_KEY,
            'app_version': '4.0',
            'mobile_platform': '2',
            'union_mark': 'nature',
            'mobile_channel': 'nature',
            'mars_cid': mars_cid,
            'warehouse': 'VIP_NH',
            'fdc_area_id': '944101105999',
            'province_id': '104104',
            'wap_consumer': 'C2-6'
        }

        query_string = urllib.parse.urlencode(upload_params)
        upload_url = f"{UPLOAD_API}?{query_string}"

        # 构建请求 - 微信小程序Header
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.70(0x18004638) NetType/WIFI Language/zh_CN',
            'Content-Type': f'multipart/form-data; boundary={boundary}',
            'Referer': 'https://servicewechat.com/wxe9714e742209d35f/1356/page-frame.html'
        }
        
        req = urllib.request.Request(upload_url, data=body, headers=headers, method='POST')
        
        with urllib.request.urlopen(req, timeout=30) as response:
            data = response.read().decode('utf-8')
            return json.loads(data)
            
    except Exception as e:
        return {"code": -1, "msg": f"上传图片失败: {str(e)}"}


def get_category(img_url: str, mars_cid: str) -> Dict[str, Any]:
    """
    第二步：获取图片分类信息
    
    Args:
        img_url: 图片URL
        mars_cid: 用户标识
        
    Returns:
        分类信息
    """
    try:
        params = {
            'api_key': API_KEY,
            'app_name': 'shop_android',
            'app_version': '9.72.7',
            'client': 'android',
            'client_type': 'android',
            'fdc_area_id': '944106105103',
            'functions': 'moreRect,queryTips',
            'imgUrl': img_url,
            'mars_cid': mars_cid,
            'province_id': '104104',
            'source_app': 'android',
            'warehouse': 'VIP_NH'
        }
        
        query_string = urllib.parse.urlencode(params)
        url = f"{CATEGORY_API}?{query_string}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 12; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Origin': 'https://m.vip.com',
            'Referer': 'https://m.vip.com/'
        }
        
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req, timeout=30) as response:
            data = response.read().decode('utf-8')
            return json.loads(data)
            
    except Exception as e:
        return {"code": -1, "msg": f"获取分类失败: {str(e)}"}


def get_products(img_url: str, mars_cid: str, category_type: str, rect: str, page_token: str = '') -> Dict[str, Any]:
    """
    第三步：根据分类搜索商品
    
    Args:
        img_url: 图片URL
        mars_cid: 用户标识
        category_type: 商品分类
        rect: 检测区域
        page_token: 分页token，用于获取下一页数据
        
    Returns:
        商品列表
    """
    # 每页商品数量固定为10
    limit = 10
    
    try:
        params = {
            'api_key': API_KEY,
            'app_name': 'shop_android',
            'app_version': '9.72.7',
            'categoryType': category_type,
            'client': 'android',
            'client_type': 'android',
            'extParams': '{"sellpoint":"1","priceVer":"2","mclabel":"1","cmpStyle":"1","statusVer":"2","ic2label":"1","reco":"1","uiVer":"3","preheatTipsVer":"4","router":"2","exclusivePrice":"1","uiVerMinor":"4","labelVer":"2","rank":"2","needVideoExplain":"1","preheatView":"1","needVideoGive":"1","bigBrand":"2","attr":"3","couponVer":"v2","live":"1"}',
            'fdc_area_id': '944106105103',
            'functions': 'survey,refreshFilter,couponBar,feedback,userCouponFilter,surpriseCoupon',
            'imgUrl': img_url,
            'mars_cid': mars_cid,
            'province_id': '104104',
            'rect': rect,
            'sort': '0',
            'source': 'pzg',
            'source_app': 'android',
            'warehouse': 'VIP_NH',
            'limit': str(limit)
        }
        
        # 添加分页token
        if page_token:
            params['pageToken'] = page_token
        
        query_string = urllib.parse.urlencode(params)
        url = f"{PRODUCT_API}?{query_string}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 12; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Origin': 'https://m.vip.com',
            'Referer': 'https://m.vip.com/',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Content-Length': '0'
        }
        
        req = urllib.request.Request(url, headers=headers, method='POST')
        
        with urllib.request.urlopen(req, timeout=30) as response:
            data = response.read().decode('utf-8')
            return json.loads(data)
            
    except Exception as e:
        return {"code": -1, "msg": f"搜索商品失败: {str(e)}"}


def analyze_products(product_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    分析商品数据
    
    Args:
        product_data: 商品数据
        
    Returns:
        分析结果
    """
    if not product_data or product_data.get('code') != 1:
        return {"error": product_data.get('msg', '获取商品失败')}
    
    data = product_data.get('data', {})
    products = data.get('products', [])
    page_token = data.get('pageToken', '')
    
    if not products:
        return {
            "总计": 0,
            "商品列表": [],
            "消息": "未找到相似商品",
            "下一页token": page_token if page_token else None
        }
    
    result = {
        "总计": len(products),
        "商品列表": [],
        "下一页token": page_token if page_token else None
    }
    
    for product in products:
        # 图片优先取 squareImage，否则取 smallImage
        image_url = product.get('squareImage', '') or product.get('smallImage', '')
        # 处理图片URL：添加裁剪参数和webp格式
        image_url = process_image_url(image_url)
        # 使用 build_product_link 生成带 exchange token 的链接
        product_link = build_product_link(product.get('brandId', ''), product.get('productId', ''))
        # 提取卖点信息：从labels字段获取value
        labels = product.get('labels', [])
        sell_points = [label.get('value', '') for label in labels if label.get('value')]
        # 提取价格信息
        price_obj = product.get('price', {})
        product_info = {
            "商品ID": product.get('productId', ''),
            "商品名称": product.get('title', ''),
            "品牌": product.get('brandShowName', ''),
            "特卖价": price_obj.get('salePrice', ''),
            "划线价": price_obj.get('marketPrice', ''),
            "折扣": price_obj.get('saleDiscount', ''),
            "卖点": sell_points,
            "图片": image_url,
            "商品链接": product_link
        }
        result["商品列表"].append(product_info)
    
    return result


def search_by_image_url(img_url: str, mars_cid: str, page_token: str = '') -> Dict[str, Any]:
    """
    通过图片URL搜索商品
    
    Args:
        img_url: 图片URL
        mars_cid: 用户标识
        page_token: 分页token，用于获取下一页数据
        
    Returns:
        搜索结果
    """
    # 第二步：获取分类
    category_result = get_category(img_url, mars_cid)
    if category_result.get('code') != 1:
        return {
            "code": -1,
            "msg": f"获取分类失败: {category_result.get('msg', '未知错误')}"
        }
    
    category_data = category_result.get('data', {})
    categories = category_data.get('category', [])
    detect_rect = category_data.get('detectRect', '')
    
    if not categories:
        return {
            "code": -1,
            "msg": "未识别到商品分类"
        }
    
    # 使用第一个分类
    first_category = categories[0]
    category_type = first_category.get('categoryType', '')
    category_name = first_category.get('categoryName', '')
    
    # 第三步：搜索商品
    product_result = get_products(img_url, mars_cid, category_type, detect_rect, page_token)
    
    # 分析商品
    analysis = analyze_products(product_result)
    
    # 组装完整结果
    result = {
        "code": 1,
        "msg": "success",
        "图片URL": img_url,
        "识别分类": {
            "类型": category_type,
            "名称": category_name,
            "检测区域": detect_rect,
            "所有分类": [{"类型": c.get('categoryType', ''), "名称": c.get('categoryName', '')} for c in categories]
        },
        "商品分析": analysis,
        "原始数据": product_result.get('data', {})
    }
    
    return result


def search_by_image(file_path: str, page_token: str = '') -> Dict[str, Any]:
    """
    通过图片搜索商品主函数
    
    Args:
        file_path: 图片文件路径或图片URL
        page_token: 分页token，用于获取下一页数据
        
    Returns:
        搜索结果
    """
    # 获取登录态
    login_tokens = load_login_tokens()
    if not login_tokens:
        return {
            "code": -1,
            "msg": "login_required",
            "message": "需要登录唯品会账户",
            "action": "请先登录唯品会账户后再使用图片搜索"
        }
    
    mars_cid = login_tokens.get('mars_cid', '')
    access_token = login_tokens.get('access_token', '')
    
    if not mars_cid or not access_token:
        return {
            "code": -1,
            "msg": "login_required",
            "message": "需要登录唯品会账户",
            "action": "请先登录唯品会账户后再使用图片搜索"
        }
    
    # 判断是URL还是本地文件
    if is_url(file_path):
        # 直接使用URL
        return search_by_image_url(file_path, mars_cid, page_token)
    
    # 本地文件：验证图片
    if not validate_image(file_path):
        return {
            "code": -1,
            "msg": "无效的图片文件，仅支持jpg/jpeg/png/gif/bmp/webp格式"
        }
    
    # 第一步：上传图片
    upload_result = upload_image(file_path, mars_cid, access_token)
    if upload_result.get('code') != 1:
        return {
            "code": -1,
            "msg": f"上传图片失败: {upload_result.get('msg', '未知错误')}。建议使用 --image-url 参数直接传入图片URL。"
        }
    
    img_url = upload_result.get('data', {}).get('url', '')
    if not img_url:
        return {
            "code": -1,
            "msg": "上传图片失败：未获取到图片URL"
        }
    
    return search_by_image_url(img_url, mars_cid, page_token)


def search_next_page(img_url: str, category_type: str, rect: str, page_token: str) -> Dict[str, Any]:
    """
    分页查询：直接使用缓存的分类信息，跳过第1、2步
    
    Args:
        img_url: 图片URL
        category_type: 商品分类类型
        rect: 检测区域
        page_token: 分页token
        
    Returns:
        搜索结果
    """
    # 获取登录态
    login_tokens = load_login_tokens()
    if not login_tokens:
        return {
            "code": -1,
            "msg": "login_required",
            "message": "需要登录唯品会账户",
            "action": "请先登录唯品会账户后再使用图片搜索"
        }
    
    mars_cid = login_tokens.get('mars_cid', '')
    
    if not mars_cid:
        return {
            "code": -1,
            "msg": "login_required",
            "message": "需要登录唯品会账户",
            "action": "请先登录唯品会账户后再使用图片搜索"
        }
    
    # 直接调用第三步：搜索商品（跳过上传和分类识别）
    product_result = get_products(img_url, mars_cid, category_type, rect, page_token)
    
    # 分析商品
    analysis = analyze_products(product_result)
    
    # 组装完整结果
    result = {
        "code": 1,
        "msg": "success",
        "图片URL": img_url,
        "识别分类": {
            "类型": category_type,
            "名称": "",
            "检测区域": rect,
            "所有分类": []
        },
        "商品分析": analysis,
        "原始数据": product_result.get('data', {})
    }
    
    return result


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='唯品会图片搜索商品工具')
    parser.add_argument('--image', type=str, help='图片文件路径')
    parser.add_argument('--image-url', type=str, help='图片URL（跳过上传步骤）')
    parser.add_argument('--page-token', type=str, default='', help='分页token，用于获取下一页数据')
    parser.add_argument('--category-type', type=str, help='商品分类类型（分页时使用，跳过分类识别）')
    parser.add_argument('--rect', type=str, help='检测区域（分页时使用）')
    
    args = parser.parse_args()
    
    # 分页查询：直接使用缓存的分类信息，跳过第1、2步
    if args.page_token and args.image_url and args.category_type:
        result = search_next_page(args.image_url, args.category_type, args.rect or '', args.page_token)
    elif args.image_url:
        result = search_by_image(args.image_url, args.page_token)
    elif args.image:
        result = search_by_image(args.image, args.page_token)
    else:
        print(json.dumps({
            "code": -1,
            "msg": "请提供 --image 或 --image-url 参数"
        }, ensure_ascii=False, indent=2))
        return
    
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
