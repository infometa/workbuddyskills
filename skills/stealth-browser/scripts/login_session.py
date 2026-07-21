#!/usr/bin/env python3
"""
Interactive Login Session Manager
Opens browser for manual login, then saves session for future headless use
"""

import argparse
import json
import sys
import time
from pathlib import Path

SESSIONS_DIR = Path.home() / ".clawdbot" / "browser-sessions"


def login_and_save(url: str, session_name: str, wait_for_url: str = None, timeout: int = 300):
    """
    Open browser for manual login, wait for success, then save session
    
    Args:
        url: Login page URL
        session_name: Name for saved session
        wait_for_url: URL pattern to wait for (indicates successful login)
        timeout: Max seconds to wait for login
    """
    from DrissionPage import ChromiumPage, ChromiumOptions
    
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Visible browser for manual login
    options = ChromiumOptions()
    options.set_argument('--disable-blink-features=AutomationControlled')
    options.set_argument('--start-maximized')
    options.set_user_agent(
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/120.0.0.0 Safari/537.36'
    )
    
    page = ChromiumPage(options)
    
    try:
        print(f"打开登录页面: {url}")
        print(f"请在浏览器中手动登录...")
        print(f"登录成功后会自动保存会话 (超时: {timeout}秒)")
        print("-" * 50)
        
        page.get(url)
        
        start_time = time.time()
        initial_url = page.url
        logged_in = False
        
        while time.time() - start_time < timeout:
            current_url = page.url
            
            # Check if URL changed (likely logged in)
            if wait_for_url:
                if wait_for_url in current_url:
                    logged_in = True
                    break
            else:
                # Heuristics: URL changed away from login page
                if current_url != initial_url and 'login' not in current_url.lower():
                    # Wait a bit more to ensure cookies are set
                    time.sleep(2)
                    logged_in = True
                    break
            
            time.sleep(1)
            
            # Show progress
            elapsed = int(time.time() - start_time)
            if elapsed % 10 == 0:
                print(f"等待登录中... ({elapsed}秒)")
        
        if not logged_in:
            # Ask user to confirm
            print("\n未检测到自动跳转。是否已登录成功？")
            confirm = input("输入 y 保存会话，n 取消: ").strip().lower()
            if confirm != 'y':
                print("已取消")
                return None
        
        # Save session
        session_data = {
            "name": session_name,
            "url": page.url,
            "title": page.title,
            "cookies": page.cookies.as_dict(),
            "localStorage": {},
            "timestamp": time.time()
        }
        
        try:
            ls = page.run_js("return JSON.stringify(localStorage);")
            session_data["localStorage"] = json.loads(ls) if ls else {}
        except:
            pass
        
        session_path = SESSIONS_DIR / f"{session_name}.json"
        session_path.write_text(json.dumps(session_data, indent=2, ensure_ascii=False))
        
        print("-" * 50)
        print(f"✓ 会话已保存: {session_path}")
        print(f"  当前页面: {page.title}")
        print(f"  Cookies: {len(session_data['cookies'])} 个")
        print(f"  localStorage: {len(session_data['localStorage'])} 项")
        
        return session_path
        
    finally:
        page.quit()


def use_saved_session(url: str, session_name: str, headless: bool = True, action: str = None):
    """
    Use a previously saved session
    
    Args:
        url: URL to navigate to
        session_name: Name of saved session
        headless: Run in headless mode
        action: Optional action to perform (screenshot, html, etc)
    """
    from DrissionPage import ChromiumPage, ChromiumOptions
    
    session_path = SESSIONS_DIR / f"{session_name}.json"
    if not session_path.exists():
        print(f"会话不存在: {session_name}")
        print(f"请先运行: python login_session.py login -u <url> -s {session_name}")
        return None
    
    session_data = json.loads(session_path.read_text())
    
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
        # Navigate first to set domain
        page.get(url)
        
        # Apply cookies
        for name, value in session_data.get("cookies", {}).items():
            try:
                page.cookies.set({name: value})
            except:
                pass
        
        # Apply localStorage
        for k, v in session_data.get("localStorage", {}).items():
            try:
                v_escaped = json.dumps(v) if not isinstance(v, str) else f'"{v}"'
                page.run_js(f"localStorage.setItem('{k}', {v_escaped});")
            except:
                pass
        
        # Refresh to apply
        page.refresh()
        page.wait.doc_loaded()
        
        print(f"✓ 已加载会话: {session_name}")
        print(f"  当前页面: {page.title}")
        print(f"  URL: {page.url}")
        
        if action == "screenshot":
            path = f"{session_name}_screenshot.png"
            page.get_screenshot(path)
            print(f"  截图: {path}")
        elif action == "html":
            print(page.html[:2000])
        
        return page
        
    except Exception as e:
        print(f"错误: {e}")
        page.quit()
        return None


def list_sessions():
    """List all saved sessions"""
    if not SESSIONS_DIR.exists():
        print("暂无保存的会话")
        return
    
    sessions = list(SESSIONS_DIR.glob("*.json"))
    if not sessions:
        print("暂无保存的会话")
        return
    
    print(f"已保存的会话 ({len(sessions)} 个):")
    print("-" * 60)
    for path in sessions:
        try:
            data = json.loads(path.read_text())
            name = path.stem
            url = data.get("url", "N/A")
            cookies = len(data.get("cookies", {}))
            print(f"  {name:<20} | {cookies:>3} cookies | {url[:40]}")
        except:
            print(f"  {path.stem:<20} | (无法读取)")


def delete_session(session_name: str):
    """Delete a saved session"""
    session_path = SESSIONS_DIR / f"{session_name}.json"
    if session_path.exists():
        session_path.unlink()
        print(f"已删除: {session_name}")
    else:
        print(f"会话不存在: {session_name}")


def main():
    parser = argparse.ArgumentParser(description='登录会话管理器')
    subparsers = parser.add_subparsers(dest='command')
    
    # Login command
    login_parser = subparsers.add_parser('login', help='打开浏览器登录并保存会话')
    login_parser.add_argument('-u', '--url', required=True, help='登录页面URL')
    login_parser.add_argument('-s', '--session', required=True, help='会话名称')
    login_parser.add_argument('--wait-url', help='等待的目标URL (可选)')
    login_parser.add_argument('--timeout', type=int, default=300, help='超时秒数')
    
    # Use command
    use_parser = subparsers.add_parser('use', help='使用已保存的会话')
    use_parser.add_argument('-u', '--url', required=True, help='目标URL')
    use_parser.add_argument('-s', '--session', required=True, help='会话名称')
    use_parser.add_argument('--headed', action='store_true', help='显示浏览器')
    use_parser.add_argument('--screenshot', action='store_true', help='截图')
    
    # List command
    list_parser = subparsers.add_parser('list', help='列出所有会话')
    
    # Delete command  
    del_parser = subparsers.add_parser('delete', help='删除会话')
    del_parser.add_argument('session', help='会话名称')
    
    args = parser.parse_args()
    
    if args.command == 'login':
        login_and_save(args.url, args.session, args.wait_url, args.timeout)
    elif args.command == 'use':
        action = 'screenshot' if args.screenshot else None
        page = use_saved_session(args.url, args.session, not args.headed, action)
        if page and args.headed:
            input("按回车关闭浏览器...")
            page.quit()
    elif args.command == 'list':
        list_sessions()
    elif args.command == 'delete':
        delete_session(args.session)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
