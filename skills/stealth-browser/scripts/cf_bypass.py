#!/usr/bin/env python3
"""
Cloudflare Bypass Utilities
Methods: DrissionPage (native), FlareSolverr (Docker), cloudscraper
"""

import json
import time
import requests
from pathlib import Path


def bypass_cloudflare_drission(url: str, headless: bool = True, timeout: int = 30):
    """
    Bypass Cloudflare using DrissionPage (most reliable for JS challenges)
    
    Returns:
        dict: {cookies: dict, user_agent: str, content: str, url: str}
    """
    from DrissionPage import ChromiumPage, ChromiumOptions
    
    options = ChromiumOptions()
    if headless:
        options.headless()
    
    options.set_argument('--disable-blink-features=AutomationControlled')
    options.set_user_agent(
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/120.0.0.0 Safari/537.36'
    )
    
    page = ChromiumPage(options)
    
    try:
        page.get(url)
        
        # Wait for CF challenge to complete (look for challenge elements to disappear)
        start = time.time()
        while time.time() - start < timeout:
            # Check if still on challenge page
            if "challenge" in page.url.lower() or "cdn-cgi" in page.url.lower():
                time.sleep(1)
                continue
            
            # Check for common CF challenge indicators
            html = page.html.lower()
            if "checking your browser" in html or "please wait" in html:
                time.sleep(1)
                continue
            
            # Challenge passed
            break
        
        return {
            "cookies": page.cookies.as_dict(),
            "user_agent": page.user_agent,
            "content": page.html,
            "url": page.url,
            "success": True
        }
    
    finally:
        page.quit()


def bypass_cloudflare_flaresolverr(url: str, flaresolverr_url: str = "http://localhost:8191/v1", timeout: int = 60):
    """
    Bypass Cloudflare using FlareSolverr (Docker container)
    
    Start FlareSolverr first:
        docker run -d --name flaresolverr -p 8191:8191 ghcr.io/flaresolverr/flaresolverr
    
    Returns:
        dict: {cookies: list, user_agent: str, content: str, url: str}
    """
    payload = {
        "cmd": "request.get",
        "url": url,
        "maxTimeout": timeout * 1000
    }
    
    try:
        resp = requests.post(flaresolverr_url, json=payload, timeout=timeout + 10)
        data = resp.json()
        
        if data.get("status") == "ok":
            solution = data.get("solution", {})
            return {
                "cookies": solution.get("cookies", []),
                "user_agent": solution.get("userAgent"),
                "content": solution.get("response"),
                "url": solution.get("url"),
                "success": True
            }
        else:
            return {
                "success": False,
                "error": data.get("message", "Unknown error")
            }
    
    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "error": "FlareSolverr not running. Start with: docker run -d --name flaresolverr -p 8191:8191 ghcr.io/flaresolverr/flaresolverr"
        }


def bypass_cloudflare_cloudscraper(url: str, **kwargs):
    """
    Bypass Cloudflare using cloudscraper (Python library)
    Works for simpler challenges, may fail on advanced protection
    
    pip install cloudscraper
    
    Returns:
        dict: {cookies: dict, content: str, url: str}
    """
    import cloudscraper
    
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'mobile': False
        }
    )
    
    try:
        resp = scraper.get(url, **kwargs)
        return {
            "cookies": dict(resp.cookies),
            "content": resp.text,
            "url": resp.url,
            "status_code": resp.status_code,
            "success": resp.status_code == 200
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def get_cf_clearance(url: str, method: str = "auto"):
    """
    Get Cloudflare clearance cookies
    
    Args:
        url: Target URL
        method: 'drission', 'flaresolverr', 'cloudscraper', or 'auto'
    
    Returns:
        dict with cookies and user_agent for use in subsequent requests
    """
    methods = {
        "drission": bypass_cloudflare_drission,
        "flaresolverr": bypass_cloudflare_flaresolverr,
        "cloudscraper": bypass_cloudflare_cloudscraper
    }
    
    if method != "auto":
        return methods[method](url)
    
    # Auto: try methods in order of reliability
    for name, func in [("drission", bypass_cloudflare_drission), 
                       ("cloudscraper", bypass_cloudflare_cloudscraper),
                       ("flaresolverr", bypass_cloudflare_flaresolverr)]:
        try:
            result = func(url)
            if result.get("success"):
                result["method"] = name
                return result
        except Exception as e:
            continue
    
    return {"success": False, "error": "All methods failed"}


def apply_cf_cookies_to_session(session: requests.Session, cf_result: dict):
    """
    Apply Cloudflare bypass cookies to a requests Session
    
    Args:
        session: requests.Session object
        cf_result: Result from bypass functions
    """
    if not cf_result.get("success"):
        raise ValueError("Cannot apply failed CF result")
    
    cookies = cf_result.get("cookies", {})
    user_agent = cf_result.get("user_agent")
    
    # Handle both dict and list cookie formats
    if isinstance(cookies, list):
        for cookie in cookies:
            session.cookies.set(cookie["name"], cookie["value"], domain=cookie.get("domain"))
    else:
        for name, value in cookies.items():
            session.cookies.set(name, value)
    
    if user_agent:
        session.headers["User-Agent"] = user_agent


def test_cf_protection(url: str) -> dict:
    """
    Test if a URL has Cloudflare protection
    
    Returns:
        dict: {protected: bool, type: str, headers: dict}
    """
    try:
        resp = requests.get(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }, timeout=10, allow_redirects=True)
        
        cf_headers = {k: v for k, v in resp.headers.items() if k.lower().startswith("cf-")}
        
        is_protected = False
        protection_type = None
        
        if resp.status_code == 403:
            is_protected = True
            protection_type = "blocked"
        elif resp.status_code == 503:
            is_protected = True
            protection_type = "challenge"
        elif "cf-ray" in resp.headers:
            if "challenge" in resp.text.lower() or "__cf" in resp.text:
                is_protected = True
                protection_type = "js_challenge"
            else:
                protection_type = "cdn_only"
        
        return {
            "protected": is_protected,
            "type": protection_type,
            "status_code": resp.status_code,
            "cf_headers": cf_headers
        }
    
    except Exception as e:
        return {
            "protected": None,
            "error": str(e)
        }


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Cloudflare Bypass')
    parser.add_argument('url', help='Target URL')
    parser.add_argument('--method', '-m', choices=['auto', 'drission', 'flaresolverr', 'cloudscraper'],
                        default='auto', help='Bypass method')
    parser.add_argument('--test', '-t', action='store_true', help='Test if URL has CF protection')
    parser.add_argument('--save-cookies', '-s', help='Save cookies to file')
    
    args = parser.parse_args()
    
    if args.test:
        result = test_cf_protection(args.url)
        print(json.dumps(result, indent=2))
    else:
        print(f"Bypassing Cloudflare for: {args.url}")
        result = get_cf_clearance(args.url, args.method)
        
        if result.get("success"):
            print(f"✓ Success using method: {result.get('method', args.method)}")
            print(f"  Cookies: {len(result.get('cookies', {}))} items")
            print(f"  User-Agent: {result.get('user_agent', 'N/A')[:50]}...")
            
            if args.save_cookies:
                Path(args.save_cookies).write_text(json.dumps({
                    "cookies": result.get("cookies"),
                    "user_agent": result.get("user_agent")
                }, indent=2))
                print(f"  Saved to: {args.save_cookies}")
        else:
            print(f"✗ Failed: {result.get('error')}")
            exit(1)
