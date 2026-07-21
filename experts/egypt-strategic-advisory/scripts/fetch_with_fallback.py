"""
fetch_with_fallback.py — 零成本多层级网络抓取工具

面向埃及战略顾问 Agent 生产环境使用。
无需 VPN、无需代理服务器、零付费依赖，纯代码实现多层降级。

架构:
  Layer 1: 直连 (碰运气)
  Layer 2: Google 网页缓存 (非实时, 高可用, 国内可达 ⭐)
  Layer 3: 公共 CORS 网关 (实时, 免费)
  Layer 4: 硬编码免费代理池 (预置 + 动态扩充)
  Layer 5: 返回 None → 调用方走语料库兜底

Usage:
    from fetch_with_fallback import fetch_with_fallback

    html = fetch_with_fallback("https://www.matrade.gov.my/...")
    if html is None:
        # 走语料库降级
        ...
"""

import re
import time
import random
import logging
from urllib.parse import urlparse

# ── HTTP 库探测 ──
try:
    from urllib.request import Request, urlopen
    from urllib.error import URLError, HTTPError
    STD_LIB_AVAILABLE = True
except ImportError:
    STD_LIB_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

logger = logging.getLogger("fetch_with_fallback")


# ════════════════════════════════════════════════════════
# 配置区
# ════════════════════════════════════════════════════════

REQUEST_TIMEOUT = 10         # 单次请求超时(秒)
PROXY_TRY_LIMIT = 20         # 免费代理尝试上限
GATEWAY_RETRIES = 2          # 每个网关重试次数
TOTAL_TIMEOUT = 50           # 总超时(秒)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/119.0.0.0 Safari/537.36",
]

# ── 免费 CORS 网关 ──
CORS_GATEWAYS = [
    "https://api.allorigins.win/raw?url={}",
    "https://corsproxy.io/?url={}",
    "https://api.codetabs.com/v1/proxy?quest={}",
]

# ── 免费代理源 (用于动态拉取) ──
PROXY_SOURCES = [
    "https://free-proxy-list.net/",
    "https://www.sslproxies.org/",
]

# ── 硬编码已知免费代理 (保底用, 即使代理源站被墙也能跑) ──
# 来源: 公开代理列表, 定期轮换
# 即使部分失效, 只要有 1-2 个能用的就够了
HARDCODED_PROXIES = [
    # 常见公开代理 (端口类型混合)
    "8.219.97.248:8080",
    "185.162.229.26:8080",
    "103.156.232.242:80",
    "188.166.212.186:8080",
    "45.77.4.188:3128",
    "104.248.63.17:3180",
    "103.151.122.146:80",
    "161.35.70.249:8080",
    "129.146.244.120:80",
    "139.59.186.195:8080",
    "45.79.68.191:8118",
    "103.149.162.194:80",
]


# ════════════════════════════════════════════════════════
# 底层 HTTP 请求 (requests > urllib)
# ════════════════════════════════════════════════════════

def _http_get(url, headers=None, timeout=None, proxies=None):
    """统一的 HTTP GET"""
    _headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    if headers:
        _headers.update(headers)
    _timeout = timeout or REQUEST_TIMEOUT

    if REQUESTS_AVAILABLE:
        return _http_get_requests(url, _headers, _timeout, proxies)
    elif STD_LIB_AVAILABLE:
        return _http_get_urllib(url, _headers, _timeout, proxies)
    else:
        raise RuntimeError("No HTTP library available")


def _http_get_requests(url, headers, timeout, proxies):
    """requests 实现"""
    kwargs = {"headers": headers, "timeout": timeout, "allow_redirects": True}
    if proxies:
        kwargs["proxies"] = proxies
    r = requests.get(url, **kwargs)
    r.raise_for_status()
    return r.text


def _http_get_urllib(url, headers, timeout, proxies):
    """urllib 降级实现"""
    req = Request(url, headers=headers)
    if proxies:
        proxy_url = proxies.get("http") or proxies.get("https") or ""
        if proxy_url:
            from urllib.request import ProxyHandler, build_opener, install_opener
            handler = ProxyHandler({"http": proxy_url, "https": proxy_url})
            opener = build_opener(handler)
            install_opener(opener)
    resp = urlopen(req, timeout=timeout)
    return resp.read().decode("utf-8", errors="replace")


# ════════════════════════════════════════════════════════
# Layer 1: 直连
# ════════════════════════════════════════════════════════

def _try_direct(url):
    """Layer 1: 直接连接 (国内能通的最快)"""
    try:
        result = _http_get(url, timeout=5)
        if result and len(result) > 200:
            logger.info("直连成功!")
            return result
    except Exception:
        pass
    return None


# ════════════════════════════════════════════════════════
# Layer 2: Google 网页缓存
# ════════════════════════════════════════════════════════
# webcache.googleusercontent.com 在国内通常可达
# 缺点: 内容可能不是最新的

def _try_google_cache(url):
    """Layer 2: 通过 Google 缓存获取"""
    cache_url = f"https://webcache.googleusercontent.com/search?q=cache:{url}"
    try:
        result = _http_get(cache_url, timeout=10)
        if result and len(result) > 500:
            logger.info("Google Cache 命中!")
            return result
    except Exception as e:
        logger.debug(f"Google Cache 失败: {e}")
    return None


# ════════════════════════════════════════════════════════
# Layer 3: 公共 CORS 网关
# ════════════════════════════════════════════════════════

def _try_gateway_layer(url):
    """Layer 3: 通过 CORS 代理网关抓取"""
    for template in CORS_GATEWAYS:
        gateway_url = template.format(url)
        for attempt in range(GATEWAY_RETRIES):
            try:
                result = _http_get(gateway_url, timeout=8)
                if result and len(result) > 200:
                    logger.info(f"CORS 网关成功: {template.split('/')[2]}")
                    return result
            except Exception as e:
                logger.debug(f"Gateway {template.split('/')[2]} attempt {attempt+1}: {e}")
                time.sleep(0.3)
    return None


# ════════════════════════════════════════════════════════
# Layer 4: 免费代理池 (硬编码 + 动态)
# ════════════════════════════════════════════════════════

def _scrape_free_proxies():
    """动态抓取免费代理 (可能被墙, 但先试试)"""
    proxies = set()
    for source_url in PROXY_SOURCES:
        try:
            html = _http_get(source_url, timeout=8)
            found = re.findall(r'(\d+\.\d+\.\d+\.\d+:\d+)', html)
            proxies.update(found)
            logger.debug(f"从 {source_url} 获取到 {len(found)} 个代理")
        except Exception as e:
            logger.debug(f"代理源 {source_url} 抓取失败: {e}")
    return list(proxies)


def _try_proxy_layer(url):
    """Layer 4: 硬编码代理 + 动态代理联合轮换"""
    # 先用硬编码的保底代理
    all_proxies = list(HARDCODED_PROXIES)

    # 再尝试动态抓取 (如果抓不到也不影响)
    try:
        dynamic = _scrape_free_proxies()
        if dynamic:
            # 去重合并
            existing = set(all_proxies)
            for p in dynamic:
                if p not in existing:
                    all_proxies.append(p)
    except Exception:
        pass

    if not all_proxies:
        logger.debug("Layer 4: 无可用代理")
        return None

    random.shuffle(all_proxies)
    tried = 0

    for proxy in all_proxies:
        if tried >= PROXY_TRY_LIMIT:
            break
        try:
            result = _http_get(
                url,
                proxies={"http": f"http://{proxy}", "https": f"http://{proxy}"},
                timeout=5,
            )
            if result and len(result) > 200:
                logger.info(f"代理成功: {proxy}")
                return result
        except Exception:
            tried += 1
            continue

    logger.debug(f"Layer 4: 试了 {tried} 个代理均失败")
    return None


# ════════════════════════════════════════════════════════
# 主入口
# ════════════════════════════════════════════════════════

def fetch_with_fallback(url, timeout=None):
    """
    多层降级网络抓取主函数

    按优先级依次尝试各层, 任一成功即返回。
    全部失败返回 None, 调用方应走语料库兜底。

    Args:
        url: 目标网页 URL
        timeout: 总超时秒数 (默认 50s)

    Returns:
        str: 网页 HTML 内容, 或 None
    """
    if not url or not url.startswith("http"):
        logger.warning(f"无效 URL: {url}")
        return None

    domain = urlparse(url).netloc
    logger.info(f"▶ 开始抓取: {domain}")

    start = time.time()
    limit = timeout or TOTAL_TIMEOUT

    layers = [
        ("直连",       _try_direct,      5),
        ("Google缓存", _try_google_cache, 10),
        ("CORS网关",   _try_gateway_layer, 15),
        ("免费代理",   _try_proxy_layer,  25),
    ]

    for name, func, budget in layers:
        elapsed = time.time() - start
        if elapsed >= limit:
            logger.warning(f"超时 ({elapsed:.0f}s), 跳过 '{name}'")
            break

        logger.info(f"  └ Layer {name} ...")
        result = func(url)

        if result is not None:
            total = time.time() - start
            logger.info(f"  ✅ Layer {name} 成功! 用时 {total:.1f}s, {len(result)} 字节")
            return result

        used = time.time() - start
        logger.info(f"  ❌ Layer {name} 失败, 已用 {used:.1f}s")

    total = time.time() - start
    logger.warning(f"✖ 全部失败! 总用时 {total:.1f}s")
    return None


# ════════════════════════════════════════════════════════
# 快捷工具
# ════════════════════════════════════════════════════════

def is_reachable(url, timeout=8):
    """快速检测直连可达性"""
    try:
        _http_get(url, timeout=timeout)
        return True
    except Exception:
        return False


# ════════════════════════════════════════════════════════
# 独立测试
# ════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    test_urls = [
        "https://www.moet.gov.ae",
        "https://www.matrade.gov.my",
    ]

    for url in test_urls:
        print(f"\n{'='*60}")
        print(f"测试: {url}")
        print(f"{'='*60}")
        result = fetch_with_fallback(url)
        if result:
            print(f"✅ 成功! 获取到 {len(result)} 字节")
            print(f"  前 150 字: {result[:150].strip()}")
        else:
            print("❌ 失败: 所有层均无法获取")
