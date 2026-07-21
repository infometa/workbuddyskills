#!/usr/bin/env python3
"""
东方财富股票数据抓取工具 v2.0
使用 Selenium + Chrome 获取动态加载的股票数据

支持市场：
- A股：sh600519, sz300750, bj830799
- 港股：hk/00700
- 美股：us/MU, us/AAPL

用法：
    python fetch_stock.py <股票代码> [--market <市场>] [--output <json|text>]

示例：
    python fetch_stock.py 00700 --market hk
    python fetch_stock.py MU --market us
    python fetch_stock.py 600519 --market sh
"""

import argparse
import json
import sys
import time
import re
from typing import Optional, Dict, Any, List

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, WebDriverException
except ImportError:
    print("错误：需要安装 selenium 库")
    print("请运行：pip install selenium")
    sys.exit(1)

try:
    from webdriver_manager.chrome import ChromeDriverManager
    USE_WEBDRIVER_MANAGER = True
except ImportError:
    USE_WEBDRIVER_MANAGER = False


def get_stock_url(code: str, market: str) -> str:
    """根据市场类型生成东方财富URL"""
    base_url = "https://quote.eastmoney.com"
    
    market = market.lower()
    
    if market == 'hk':
        return f"{base_url}/hk/{code}.html"
    elif market == 'us':
        return f"{base_url}/us/{code.upper()}.html"
    elif market in ['sh', 'sz', 'bj']:
        return f"{base_url}/{market}{code}.html"
    elif market == 'auto':
        # 自动识别
        if code.isdigit():
            if code.startswith('6'):
                return f"{base_url}/sh{code}.html"
            elif code.startswith(('0', '3')):
                return f"{base_url}/sz{code}.html"
            elif code.startswith(('8', '4')):
                return f"{base_url}/bj{code}.html"
            elif len(code) == 5:
                return f"{base_url}/hk/{code}.html"
        else:
            return f"{base_url}/us/{code.upper()}.html"
    
    raise ValueError(f"无法识别的市场类型: {market}")


def create_driver(headless: bool = True) -> webdriver.Chrome:
    """创建 Chrome WebDriver"""
    options = Options()
    
    if headless:
        options.add_argument('--headless')
    
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    prefs = {
        'profile.managed_default_content_settings.images': 2,
        'profile.default_content_setting_values.notifications': 2
    }
    options.add_experimental_option('prefs', prefs)
    
    try:
        if USE_WEBDRIVER_MANAGER:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
        else:
            driver = webdriver.Chrome(options=options)
        return driver
    except WebDriverException as e:
        print(f"错误：无法启动 Chrome WebDriver: {e}", file=sys.stderr)
        print("请确保已安装 Chrome 浏览器", file=sys.stderr)
        print("运行：pip install webdriver-manager", file=sys.stderr)
        sys.exit(1)


def extract_price_data(driver: webdriver.Chrome) -> Dict[str, str]:
    """
    从东方财富页面提取股票数据
    页面使用 price_down/price_up/price_draw + blinkgreen/blinkred/blinkblue 类名
    """
    data = {}
    
    # 获取所有带有 blink 类的 span 元素（这些是主要数据区域）
    blink_elements = driver.find_elements(
        By.CSS_SELECTOR, 
        "span.blinkgreen, span.blinkred, span.blinkblue"
    )
    
    # 按顺序排列的数据通常是：价格、涨跌额、涨跌幅、买入价、卖出价、最高、昨收、最低、成交额、换手率...
    blink_texts = []
    for el in blink_elements:
        text = el.text.strip()
        if text and text != "-" and text != "--":
            blink_texts.append(text)
    
    # 尝试识别数据
    if len(blink_texts) >= 1:
        # 第一个数字通常是当前价格
        data['price'] = blink_texts[0]
    
    if len(blink_texts) >= 2:
        # 第二个是涨跌额
        data['change'] = blink_texts[1]
    
    if len(blink_texts) >= 3:
        # 第三个是涨跌幅
        data['change_percent'] = blink_texts[2]
    
    # 查找更多数据：遍历所有 price_draw 元素
    draw_elements = driver.find_elements(By.CSS_SELECTOR, "span.price_draw")
    draw_texts = []
    for el in draw_elements:
        text = el.text.strip()
        if text and text != "-":
            draw_texts.append(text)
    
    # 从所有数据中识别特定字段
    all_texts = blink_texts + draw_texts
    
    for text in all_texts:
        # 识别市值（包含"万亿"或"亿"且数值较大）
        if '万亿' in text and 'market_cap' not in data:
            data['market_cap'] = text
        # 识别成交额
        elif '亿' in text and '万亿' not in text and 'amount' not in data:
            data['amount'] = text
        # 识别市盈率（两位小数的数字，通常在15-50之间）
        elif re.match(r'^\d{1,3}\.\d{2}$', text):
            val = float(text)
            if 5 < val < 200 and 'pe' not in data:
                data['pe'] = text
            elif 0 < val < 20 and 'pb' not in data and 'pe' in data:
                data['pb'] = text
        # 识别换手率（以%结尾，数值较小）
        elif text.endswith('%') and 'turnover' not in data:
            try:
                val = float(text.rstrip('%'))
                if 0 < val < 10:
                    data['turnover'] = text
            except:
                pass
    
    # 尝试从表格提取更多数据
    try:
        # 港股/美股页面的数据表格
        rows = driver.find_elements(By.CSS_SELECTOR, "div.quote-item, tr.quote-row, .data-item")
        for row in rows:
            text = row.text.strip()
            if '今开' in text or '开盘' in text:
                match = re.search(r'[\d.]+', text.split('\n')[-1] if '\n' in text else text)
                if match:
                    data['open'] = match.group()
            elif '昨收' in text:
                match = re.search(r'[\d.]+', text.split('\n')[-1] if '\n' in text else text)
                if match:
                    data['prev_close'] = match.group()
            elif '最高' in text:
                match = re.search(r'[\d.]+', text.split('\n')[-1] if '\n' in text else text)
                if match:
                    data['high'] = match.group()
            elif '最低' in text:
                match = re.search(r'[\d.]+', text.split('\n')[-1] if '\n' in text else text)
                if match:
                    data['low'] = match.group()
    except:
        pass
    
    # 获取股票名称
    try:
        # 港股/美股页面
        name_el = driver.find_element(By.CSS_SELECTOR, "h1.name, .stock-name, .quote-name, title")
        if name_el:
            name = name_el.text.strip()
            # 从 title 提取
            if '(' in name:
                name = name.split('(')[0].strip()
            data['name'] = name
    except:
        pass
    
    # 如果还没有名称，从 title 获取
    if 'name' not in data or not data['name']:
        title = driver.title
        if title:
            # "腾讯控股(00700)股票价格_行情_走势图—东方财富网"
            match = re.match(r'^(.+?)\(', title)
            if match:
                data['name'] = match.group(1).strip()
    
    return data


def fetch_stock_data(code: str, market: str, headless: bool = True, timeout: int = 15) -> Dict[str, Any]:
    """
    获取股票数据
    """
    url = get_stock_url(code, market)
    result = {
        "success": False,
        "code": code,
        "market": market.upper(),
        "url": url,
        "data": {},
        "error": None,
        "source": "东方财富",
        "fetch_time": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    driver = None
    try:
        print(f"正在启动浏览器...", file=sys.stderr)
        driver = create_driver(headless=headless)
        driver.set_page_load_timeout(timeout)
        
        print(f"正在访问: {url}", file=sys.stderr)
        driver.get(url)
        
        print(f"等待页面数据加载...", file=sys.stderr)
        time.sleep(4)  # 等待 JS 执行
        
        # 提取数据
        data = extract_price_data(driver)
        result["data"] = data
        
        # 检查是否成功获取到价格
        if data.get("price") and data["price"] != "-":
            result["success"] = True
            print(f"✅ 成功获取数据", file=sys.stderr)
        else:
            result["error"] = "无法提取价格数据"
            print(f"⚠️ 警告：{result['error']}", file=sys.stderr)
            
    except TimeoutException:
        result["error"] = f"页面加载超时 ({timeout}秒)"
        print(f"❌ 错误：{result['error']}", file=sys.stderr)
    except Exception as e:
        result["error"] = str(e)
        print(f"❌ 错误：{result['error']}", file=sys.stderr)
    finally:
        if driver:
            driver.quit()
    
    return result


def format_output(result: Dict[str, Any], output_format: str = "json") -> str:
    """格式化输出"""
    if output_format == "json":
        return json.dumps(result, ensure_ascii=False, indent=2)
    else:
        lines = []
        lines.append(f"═══════════════════════════════════════════════════")
        lines.append(f"  股票代码: {result['code']} ({result['market']})")
        lines.append(f"  数据来源: {result['source']}")
        lines.append(f"  获取时间: {result['fetch_time']}")
        lines.append(f"═══════════════════════════════════════════════════")
        
        if result["success"]:
            data = result["data"]
            name = data.get('name', '未知')
            lines.append(f"")
            lines.append(f"  📊 {name}")
            lines.append(f"")
            lines.append(f"  💰 当前价格: {data.get('price', '-')}")
            lines.append(f"  📈 涨跌额:   {data.get('change', '-')}")
            lines.append(f"  📉 涨跌幅:   {data.get('change_percent', '-')}")
            lines.append(f"")
            lines.append(f"  ┌─────────────────────────────────────────────┐")
            lines.append(f"  │ 今开: {data.get('open', '-'):>10}  │  昨收: {data.get('prev_close', '-'):>10} │")
            lines.append(f"  │ 最高: {data.get('high', '-'):>10}  │  最低: {data.get('low', '-'):>10} │")
            lines.append(f"  └─────────────────────────────────────────────┘")
            lines.append(f"")
            lines.append(f"  成交额:   {data.get('amount', '-')}")
            lines.append(f"  总市值:   {data.get('market_cap', '-')}")
            lines.append(f"  换手率:   {data.get('turnover', '-')}")
            lines.append(f"")
            lines.append(f"  市盈率(PE): {data.get('pe', '-')}")
            lines.append(f"  市净率(PB): {data.get('pb', '-')}")
        else:
            lines.append(f"")
            lines.append(f"  ❌ 获取失败: {result.get('error', '未知错误')}")
        
        lines.append(f"")
        lines.append(f"═══════════════════════════════════════════════════")
        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="东方财富股票数据抓取工具 (Selenium)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s 00700 --market hk          # 获取腾讯控股(港股)
  %(prog)s MU --market us             # 获取美光科技(美股)
  %(prog)s 600519 --market sh         # 获取贵州茅台(A股沪市)
  %(prog)s 300750 --market sz         # 获取宁德时代(A股深市)
  %(prog)s AAPL -m us -o text         # 文本格式输出
"""
    )
    parser.add_argument("code", help="股票代码")
    parser.add_argument("--market", "-m", default="auto",
                        choices=["hk", "us", "sh", "sz", "bj", "auto"],
                        help="市场类型 (默认: auto 自动识别)")
    parser.add_argument("--output", "-o", default="json",
                        choices=["json", "text"],
                        help="输出格式 (默认: json)")
    parser.add_argument("--show-browser", action="store_true",
                        help="显示浏览器窗口（调试用）")
    parser.add_argument("--timeout", "-t", type=int, default=15,
                        help="超时时间，秒 (默认: 15)")
    
    args = parser.parse_args()
    
    result = fetch_stock_data(
        code=args.code,
        market=args.market,
        headless=not args.show_browser,
        timeout=args.timeout
    )
    
    print(format_output(result, args.output))
    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
