#!/usr/bin/env python3
"""
Stealth Browser Session Manager
Supports undetected-chromedriver and DrissionPage backends
"""

import argparse
import json
import sys
import time
from pathlib import Path

SESSIONS_DIR = Path.home() / ".clawdbot" / "browser-sessions"
SECRETS_DIR = Path.home() / ".clawdbot" / "secrets"


def get_drissionpage(headless=True, proxy=None, user_agent=None):
    """Initialize DrissionPage with stealth options"""
    from DrissionPage import ChromiumPage, ChromiumOptions
    
    options = ChromiumOptions()
    
    if headless:
        options.headless()
    
    # Anti-detection flags
    options.set_argument('--disable-blink-features=AutomationControlled')
    options.set_argument('--disable-dev-shm-usage')
    options.set_argument('--no-sandbox')
    options.set_argument('--disable-infobars')
    options.set_argument('--disable-extensions')
    options.set_argument('--disable-gpu')
    options.set_argument('--lang=en-US')
    
    if user_agent:
        options.set_user_agent(user_agent)
    else:
        options.set_user_agent(
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/120.0.0.0 Safari/537.36'
        )
    
    if proxy:
        options.set_proxy(proxy)
    
    return ChromiumPage(options)


def get_undetected_chrome(headless=True, proxy=None, user_agent=None):
    """Initialize undetected-chromedriver"""
    import undetected_chromedriver as uc
    
    options = uc.ChromeOptions()
    
    if headless:
        options.add_argument('--headless=new')
    
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    if user_agent:
        options.add_argument(f'--user-agent={user_agent}')
    
    if proxy:
        options.add_argument(f'--proxy-server={proxy}')
    
    driver = uc.Chrome(options=options, use_subprocess=True)
    return driver


def save_session(driver_or_page, session_name, backend='drission'):
    """Save cookies and localStorage for session persistence"""
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    session_path = SESSIONS_DIR / f"{session_name}.json"
    
    session_data = {
        "cookies": [],
        "localStorage": {},
        "backend": backend,
        "timestamp": time.time()
    }
    
    if backend == 'drission':
        session_data["cookies"] = driver_or_page.cookies.as_dict()
        try:
            ls = driver_or_page.run_js("return JSON.stringify(localStorage);")
            session_data["localStorage"] = json.loads(ls) if ls else {}
        except:
            pass
    else:  # selenium/undetected
        session_data["cookies"] = driver_or_page.get_cookies()
        try:
            ls = driver_or_page.execute_script("return JSON.stringify(localStorage);")
            session_data["localStorage"] = json.loads(ls) if ls else {}
        except:
            pass
    
    session_path.write_text(json.dumps(session_data, indent=2))
    print(f"Session saved: {session_path}")
    return session_path


def load_session(driver_or_page, session_name, backend='drission'):
    """Load cookies and localStorage from saved session"""
    session_path = SESSIONS_DIR / f"{session_name}.json"
    
    if not session_path.exists():
        print(f"No session found: {session_name}")
        return False
    
    session_data = json.loads(session_path.read_text())
    
    if backend == 'drission':
        for name, value in session_data.get("cookies", {}).items():
            driver_or_page.cookies.set({name: value})
        
        ls_data = session_data.get("localStorage", {})
        if ls_data:
            for k, v in ls_data.items():
                driver_or_page.run_js(f"localStorage.setItem('{k}', '{v}');")
    else:  # selenium/undetected
        for cookie in session_data.get("cookies", []):
            try:
                driver_or_page.add_cookie(cookie)
            except:
                pass
        
        ls_data = session_data.get("localStorage", {})
        if ls_data:
            for k, v in ls_data.items():
                driver_or_page.execute_script(f"localStorage.setItem('{k}', '{v}');")
    
    print(f"Session loaded: {session_name}")
    return True


def get_proxy():
    """Get proxy from configuration"""
    proxy_file = SECRETS_DIR / "proxies.json"
    if proxy_file.exists():
        import random
        config = json.loads(proxy_file.read_text())
        proxies = config.get("residential", [])
        if proxies:
            return random.choice(proxies)
        return config.get("rotating")
    return None


def main():
    parser = argparse.ArgumentParser(description='Stealth Browser Session')
    parser.add_argument('--url', '-u', help='URL to open')
    parser.add_argument('--session', '-s', help='Session name for persistence')
    parser.add_argument('--backend', '-b', choices=['drission', 'undetected'], 
                        default='drission', help='Browser backend')
    parser.add_argument('--headless', action='store_true', default=True,
                        help='Run headless (default: True)')
    parser.add_argument('--headed', action='store_true', 
                        help='Show browser window')
    parser.add_argument('--proxy', '-p', help='Proxy URL')
    parser.add_argument('--rotate-proxy', action='store_true',
                        help='Use rotating proxy from config')
    parser.add_argument('--save', action='store_true', 
                        help='Save session after operation')
    parser.add_argument('--load', action='store_true',
                        help='Load existing session')
    parser.add_argument('--screenshot', help='Take screenshot to path')
    parser.add_argument('--wait', type=int, default=5,
                        help='Wait seconds after page load')
    parser.add_argument('--test-stealth', action='store_true',
                        help='Test anti-detection on bot.sannysoft.com')
    
    args = parser.parse_args()
    
    headless = not args.headed
    proxy = args.proxy
    
    if args.rotate_proxy:
        proxy = get_proxy()
        if proxy:
            print(f"Using proxy: {proxy[:30]}...")
    
    # Initialize browser
    if args.backend == 'drission':
        browser = get_drissionpage(headless=headless, proxy=proxy)
    else:
        browser = get_undetected_chrome(headless=headless, proxy=proxy)
    
    try:
        # Load session if requested
        if args.load and args.session:
            # Navigate to domain first
            if args.url:
                if args.backend == 'drission':
                    browser.get(args.url)
                else:
                    browser.get(args.url)
            load_session(browser, args.session, args.backend)
            # Refresh to apply cookies
            if args.backend == 'drission':
                browser.refresh()
            else:
                browser.refresh()
        
        # Navigate
        url = args.url
        if args.test_stealth:
            url = "https://bot.sannysoft.com"
        
        if url:
            print(f"Opening: {url}")
            if args.backend == 'drission':
                browser.get(url)
                browser.wait.doc_loaded()
            else:
                browser.get(url)
            
            time.sleep(args.wait)
        
        # Screenshot
        if args.screenshot:
            if args.backend == 'drission':
                browser.get_screenshot(args.screenshot)
            else:
                browser.save_screenshot(args.screenshot)
            print(f"Screenshot saved: {args.screenshot}")
        
        # Save session if requested
        if args.save and args.session:
            save_session(browser, args.session, args.backend)
        
        # Print current URL and title
        if args.backend == 'drission':
            print(f"Title: {browser.title}")
            print(f"URL: {browser.url}")
        else:
            print(f"Title: {browser.title}")
            print(f"URL: {browser.current_url}")
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
        
    finally:
        if args.backend == 'drission':
            browser.quit()
        else:
            browser.quit()


if __name__ == "__main__":
    sys.exit(main())
