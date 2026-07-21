#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
唯品会商品搜索工具
支持搜索商品并获取详细信息
"""

import sys
import json
import time
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Dict, List, Any, Optional

# 设置 stdout 编码为 utf-8，解决 Windows 上的编码问题
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 导入 exchange_link_builder 中的函数
from exchange_link_builder import build_product_link

import logger


def load_login_tokens() -> Optional[Dict[str, Any]]:
    """
    加载登录态
    
    Returns:
        登录态字典，包含cookies等信息；如果未登录或已过期返回None
    """
    token_file = Path.home() / ".vipshop-user-login" / "tokens.json"
    
    if not token_file.exists():
        return None
    
    try:
        with open(token_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 检查是否是新格式（包含cookies字段）
        if data and isinstance(data, dict) and 'cookies' in data:
            # 检查token是否过期
            expires_at = data.get('expires_at')
            if expires_at and time.time() > expires_at:
                return None
            return data
        return None
    except Exception as e:
        sys.stderr.write(f"加载登录态失败: {e}\n")
        logger.error("load_login_tokens_failed", error_msg=str(e))
        return None


def url_encode(text: str) -> str:
    """URL 编码文本"""
    return urllib.parse.quote(text)


def make_request(url: str, cookies: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    发起 HTTP GET 请求并返回 JSON 响应

    Args:
        url: 请求URL
        cookies: 可选的cookie字典

    Returns:
        JSON响应数据
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': 'https://www.vip.com/',
            'Origin': 'https://www.vip.com'
        }

        req = urllib.request.Request(url, headers=headers)

        # 如果有cookies，构建Cookie头
        if cookies:
            cookie_str = '; '.join([f'{k}={v}' for k, v in cookies.items()])
            req.add_header('Cookie', cookie_str)

        with urllib.request.urlopen(req, timeout=30) as response:
            data = response.read().decode('utf-8')
            return json.loads(data)
    except Exception as e:
        return {"error": str(e)}


def search_products(keyword: str, cookies: Dict[str, str], mars_cid: str, page_offset: int = 0, price_min: Optional[int] = None, price_max: Optional[int] = None) -> Dict[str, Any]:
    """
    搜索商品 - 获取商品ID列表

    Args:
        keyword: 搜索关键词
        cookies: 登录态 cookies
        mars_cid: 设备ID
        page_offset: 分页偏移量，默认为0
        price_min: 价格区间最小值，可选
        price_max: 价格区间最大值，可选

    Returns:
        搜索结果，包含商品ID列表和总数
    """
    BATCH_SIZE = 10
    base_url = "https://mapi-pc.vip.com/vips-mobile/rest/shopping/skill/search/product/rank"

    params = {
        'keyword': keyword,
        'app_name': 'shop_pc',
        'app_version': '4.0',
        'warehouse': 'VIP_NH',
        'fdc_area_id': '944101105114',
        'client': 'pc',
        'mobile_platform': '1',
        'province_id': '104104',
        'api_key': 'dafe77e7486f46eca2e17a256d3ce6b5',
        'mars_cid': mars_cid,
        'wap_consumer': 'c',
        'is_default_area': '0',
        'standby_id': 'nature',
        'pageOffset': str(page_offset),
        'channelId': '1',
        'batchSize': str(BATCH_SIZE)
    }

    # 添加价格区间参数
    if price_min is not None:
        params['priceMin'] = str(price_min)
    if price_max is not None:
        params['priceMax'] = str(price_max)

    url = f"{base_url}?{urllib.parse.urlencode(params)}"
    response = make_request(url, cookies if cookies else None)

    if "error" in response:
        return {"error": f"搜索请求失败: {response['error']}"}

    if response.get("code") != 1:
        # 检查是否是token过期
        if response.get("code") == 11000:
            return {"error": "token_expired", "message": response.get("msg", "token expired")}
        return {"error": f"搜索接口错误，code={response.get('code')}"}

    data = response.get("data", {})
    total = data.get("total", 0)
    products = data.get("products", [])

    # 提取所有商品ID并截断为 batchSize 数量
    product_ids = [p.get("pid") for p in products if p.get("pid")]
    if len(product_ids) > BATCH_SIZE:
        product_ids = product_ids[:BATCH_SIZE]
        products = products[:BATCH_SIZE]

    return {
        "total": total,
        "product_ids": product_ids,
        "products": products
    }


def get_product_details(product_ids: List[str], cookies: Dict[str, str], mars_cid: str) -> Dict[str, Any]:
    """
    获取商品详细信息

    Args:
        product_ids: 商品ID列表
        cookies: 登录态 cookies
        mars_cid: 设备ID

    Returns:
        商品详细信息
    """
    if not product_ids:
        return {"error": "没有商品ID"}

    base_url = "https://mapi-pc.vip.com/vips-mobile/rest/shopping/skill/product/module/list/v2"

    params = {
        'app_name': 'shop_pc',
        'app_version': '4.0',
        'warehouse': 'VIP_NH',
        'fdc_area_id': '944101105114',
        'client': 'pc',
        'mobile_platform': '1',
        'province_id': '104104',
        'api_key': 'dafe77e7486f46eca2e17a256d3ce6b5',
        'mars_cid': mars_cid,
        'is_default_area': '0',
        'productIds': ','.join(product_ids),
        'scene': 'search',
        'standby_id': 'nature',
        'extParams': '{"stdSizeVids":"","preheatTipsVer":"3","couponVer":"v2","exclusivePrice":"1","iconSpec":"2x","ic2label":1,"superHot":1,"bigBrand":"1"}'
    }

    url = f"{base_url}?{urllib.parse.urlencode(params)}"
    response = make_request(url, cookies if cookies else None)
    
    if "error" in response:
        return {"error": f"商品详情请求失败: {response['error']}"}
    
    if response.get("code") != 1:
        # 检查是否是token过期
        if response.get("code") == 11000:
            return {"error": "token_expired", "message": response.get("msg", "token expired")}
        return {"error": f"商品详情接口错误，code={response.get('code')}"}
    
    return response.get("data", {})


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


def format_product_detail(product: Dict[str, Any], index: int) -> Dict[str, Any]:
    """
    格式化单个商品详情为字典结构

    Args:
        product: 商品数据
        index: 商品序号

    Returns:
        商品信息字典
    """
    product_id = product.get("productId", "")
    brand_id = product.get("brandId", "")
    title = product.get("title", "")
    price = product.get("price", {})

    # 使用 build_product_link 生成带 exchange token 的链接
    product_link = build_product_link(brand_id, product_id)

    # 提取价格信息
    sale_price = price.get("salePrice", "")
    price_label = price.get("priceLabel", "价格")
    market_price = price.get("marketPrice", "")
    sale_discount = price.get("saleDiscount", "")
    sell_tips = price.get("sellTips", "")
    brand = product.get("brandShowName", "")

    # 提取图片信息
    small_image = product.get("smallImage", "")
    square_image = product.get("squareImage", "")
    
    # 处理图片URL：添加裁剪参数和webp格式
    image_url = process_image_url(square_image or small_image)

    # 返回结构化数据
    return {
        "序号": index,
        "商品ID": product_id,
        "商品链接": product_link,
        "商品名": title,
        "商品图片": image_url,
        "特卖价": sale_price,
        "划线价": market_price,
        "折扣": sale_discount,
        "卖点": sell_tips,
        "品牌": brand
    }


def search_vipshop(keyword: str, page_offset: int = 0, price_min: Optional[int] = None, price_max: Optional[int] = None) -> Dict[str, Any]:
    """
    主函数：搜索唯品会商品

    Args:
        keyword: 搜索关键词
        page_offset: 分页偏移量，默认为0
        price_min: 价格区间最小值，可选
        price_max: 价格区间最大值，可选

    Returns:
        JSON格式的搜索结果
    """
    if not keyword:
        logger.warning("search_empty_keyword")
        return {"error": "请提供搜索关键词"}

    # 检查登录态
    login_data = load_login_tokens()
    if login_data is None:
        logger.warning("search_no_login")
        return {
            "error": "login_required",
            "message": "需要登录唯品会账户",
            "action": "请先登录唯品会账户后再搜索商品"
        }

    # 提取登录态信息
    cookies = {}
    mars_cid = ''
    login_cookies = login_data.get('cookies', {})
    if 'PASSPORT_ACCESS_TOKEN' in login_cookies:
        cookies['PASSPORT_ACCESS_TOKEN'] = login_cookies['PASSPORT_ACCESS_TOKEN']
    if 'mars_cid' in login_cookies:
        mars_cid = login_cookies['mars_cid']

    # 步骤1: 搜索商品
    logger.info("search_start", keyword=keyword, page_offset=str(page_offset))
    search_result = search_products(keyword, cookies, mars_cid, page_offset, price_min, price_max)

    if "error" in search_result:
        # 检查是否是token过期
        if search_result.get("error") == "token_expired":
            logger.error("search_token_expired", keyword=keyword)
            return {"error": "token_expired", "message": "登录已过期，请重新登录"}
        logger.error("search_api_failed", keyword=keyword, error_msg=search_result['error'])
        return {"error": f"接口调用失败：{search_result['error']}"}

    total = search_result.get("total", 0)
    product_ids = search_result.get("product_ids", [])

    if total == 0:
        logger.info("search_no_result", keyword=keyword)
        return {"error": "未找到相关商品"}

    logger.info("search_success", keyword=keyword, total=str(total), product_ids=product_ids)

    # 步骤2: 获取商品详情
    logger.info("search_detail_start", keyword=keyword, product_ids=product_ids)
    detail_result = get_product_details(product_ids, cookies, mars_cid)

    if "error" in detail_result:
        # 检查是否是token过期
        if detail_result.get("error") == "token_expired":
            logger.error("search_detail_token_expired", keyword=keyword)
            return {"error": "token_expired", "message": "登录已过期，请重新登录"}
        # 详情接口失败，降级为返回商品ID
        logger.error("search_detail_failed", keyword=keyword, error_msg=detail_result['error'])
        return {
            "error": f"商品详情接口失败：{detail_result['error']}",
            "总数": total,
            "商品ID列表": product_ids
        }

    products = detail_result.get("products", [])

    if not products:
        logger.warning("search_detail_empty", keyword=keyword)
        return {
            "error": "未获取到商品详情",
            "总数": total,
            "商品ID列表": product_ids
        }

    # 步骤3: 格式化为结构化数据
    batch_size = 10
    max_pages = 10
    max_total = 100
    
    # 限制总数最大为100
    display_total = min(total, max_total)
    
    current_page = page_offset // batch_size + 1
    total_pages = min((display_total + batch_size - 1) // batch_size, max_pages)
    
    formatted_products = []
    for i, product in enumerate(products, page_offset + 1):
        formatted_products.append(format_product_detail(product, i))

    logger.info("search_complete", keyword=keyword, total=str(display_total), current_page=str(current_page), result_count=str(len(products)))

    result = {
        "搜索关键词": keyword,
        "总数": display_total,
        "当前页": current_page,
        "总页数": total_pages,
        "当前展示": len(products),
        "每页数量": batch_size,
        "当前偏移": page_offset,
        "商品列表": formatted_products
    }

    # 添加价格区间信息（如果有）
    if price_min is not None or price_max is not None:
        price_range = ""
        if price_min is not None:
            price_range += f"¥{price_min}"
        else:
            price_range += "不限"
        price_range += "-"
        if price_max is not None:
            price_range += f"¥{price_max}"
        else:
            price_range += "不限"
        result["价格区间"] = price_range

    return result


def main():
    """命令行入口 - 输出JSON格式数据"""
    if len(sys.argv) < 2:
        sys.stderr.write("用法: python search.py <搜索关键词> [--page-offset <偏移量>] [--price-min <最小价>] [--price-max <最大价>]\n")
        sys.stderr.write("示例: python search.py 连衣裙\n")
        sys.stderr.write("示例: python search.py 连衣裙 --page-offset 20\n")
        sys.stderr.write("示例: python search.py 连衣裙 -p 40\n")
        sys.stderr.write("示例: python search.py 连衣裙 --price-min 100 --price-max 300\n")
        sys.stderr.write("示例: python search.py 连衣裙 -p 20 --price-min 50 --price-max 200\n")
        sys.exit(1)

    # 解析参数
    args = sys.argv[1:]
    keyword = ""
    page_offset = 0
    price_min = None
    price_max = None

    i = 0
    while i < len(args):
        if args[i] in ['--page-offset', '-p']:
            if i + 1 < len(args):
                page_offset = int(args[i + 1])
                i += 2
            else:
                sys.stderr.write("错误: --page-offset 需要一个数值参数\n")
                sys.exit(1)
        elif args[i] == '--price-min':
            if i + 1 < len(args):
                price_min = int(args[i + 1])
                i += 2
            else:
                sys.stderr.write("错误: --price-min 需要一个数值参数\n")
                sys.exit(1)
        elif args[i] == '--price-max':
            if i + 1 < len(args):
                price_max = int(args[i + 1])
                i += 2
            else:
                sys.stderr.write("错误: --price-max 需要一个数值参数\n")
                sys.exit(1)
        else:
            if keyword:
                keyword += " " + args[i]
            else:
                keyword = args[i]
            i += 1

    result = search_vipshop(keyword, page_offset, price_min, price_max)

    # 输出JSON格式数据，确保中文正常显示
    print(json.dumps(result, ensure_ascii=False, indent=2))

    # 等待所有日志上报完成
    logger.flush()


if __name__ == "__main__":
    main()
