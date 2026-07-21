# -*- coding: utf-8 -*-
"""
智能登录脚本 - 先静默尝试，失败再显示窗口
支持断点续传和错误恢复
"""
from DrissionPage import ChromiumPage, ChromiumOptions
import time
import json
import sys
from pathlib import Path
from datetime import datetime

SESSIONS_DIR = Path.home() / '.clawdbot' / 'browser-sessions'
ATTEMPTS_LOG = Path.home() / '.clawdbot' / 'browser-sessions' / 'attempts.json'

# 设置输出编码
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

def log_attempt(url, success, method, notes=''):
    """记录尝试过的网站"""
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    attempts = []
    if ATTEMPTS_LOG.exists():
        attempts = json.loads(ATTEMPTS_LOG.read_text())
    
    attempts.append({
        'url': url,
        'success': success,
        'method': method,  # headless / headed
        'notes': notes,
        'timestamp': time.time()
    })
    ATTEMPTS_LOG.write_text(json.dumps(attempts, indent=2, ensure_ascii=False))

def get_browser(headless=True):
    """获取浏览器实例"""
    options = ChromiumOptions()
    if headless:
        options.headless()
    options.set_argument('--disable-blink-features=AutomationControlled')
    options.set_argument('--no-sandbox')
    options.set_argument('--disable-dev-shm-usage')
    options.set_user_agent(
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/120.0.0.0 Safari/537.36'
    )
    return ChromiumPage(options)

def save_session(page, name):
    """保存session"""
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    session_data = {
        'name': name,
        'url': page.url,
        'title': page.title,
        'cookies': dict(page.cookies()),  # 用dict()转换
        'timestamp': time.time()
    }
    path = SESSIONS_DIR / f'{name}.json'
    path.write_text(json.dumps(session_data, indent=2, ensure_ascii=False))
    print(f'Session saved: {path}')
    return path

def load_session(page, name):
    """加载session"""
    path = SESSIONS_DIR / f'{name}.json'
    if not path.exists():
        return False
    data = json.loads(path.read_text())
    for k, v in data.get('cookies', {}).items():
        try:
            page.set.cookies({k: v})
        except:
            pass
    return True

def smart_login(url, session_name, account=None, password=None):
    """
    智能登录 - 先静默尝试，失败再显示窗口
    """
    print(f'=== 登录 {url} ===')
    
    # 第一步：静默尝试加载已有session
    print('1. 尝试静默加载已有session...')
    page = get_browser(headless=True)
    try:
        page.get(url)
        time.sleep(2)
        
        if load_session(page, session_name):
            page.refresh()
            time.sleep(3)
            # 检查是否登录成功（简单检查：不在登录页）
            if 'login' not in page.url.lower() and 'passport' not in page.url.lower():
                print('已有session有效，登录成功！')
                log_attempt(url, True, 'headless', 'session_reuse')
                return page
        
        print('无有效session')
    except Exception as e:
        print(f'静默尝试失败: {e}')
    finally:
        page.quit()
    
    # 第二步：如果有账号密码，尝试静默登录
    if account and password:
        print('2. 尝试静默自动登录...')
        page = get_browser(headless=True)
        try:
            page.get(url)
            time.sleep(3)
            
            # 找输入框
            inputs = page.eles('tag:input')
            text_input = None
            pwd_input = None
            for inp in inputs:
                t = inp.attr('type') or ''
                if t == 'text' or t == 'tel' or t == 'email':
                    if not text_input:
                        text_input = inp
                if t == 'password':
                    pwd_input = inp
            
            if text_input and pwd_input:
                text_input.clear()
                text_input.input(account)
                time.sleep(0.3)
                pwd_input.clear()
                pwd_input.input(password)
                time.sleep(0.3)
                
                # 找登录按钮并点击
                btn = page.ele('tag:button') or page.ele('.btn') or page.ele('[type=submit]')
                if btn:
                    try:
                        page.run_js('arguments[0].click()', btn)
                    except:
                        btn.click()
                
                time.sleep(5)
                
                # 检查是否成功
                if 'login' not in page.url.lower() and 'passport' not in page.url.lower():
                    print('静默登录成功！')
                    save_session(page, session_name)
                    log_attempt(url, True, 'headless', 'auto_login')
                    return page
                else:
                    print('可能需要验证码，切换到显示模式')
        except Exception as e:
            print(f'静默登录失败: {e}')
        finally:
            page.quit()
    
    # 第三步：显示窗口让用户手动操作
    print('3. 打开浏览器窗口，请手动登录...')
    page = get_browser(headless=False)
    try:
        page.get(url)
        
        # 如果有账号密码，先填入
        if account and password:
            time.sleep(3)
            inputs = page.eles('tag:input')
            for inp in inputs:
                t = inp.attr('type') or ''
                if t in ('text', 'tel', 'email'):
                    inp.clear()
                    inp.input(account)
                elif t == 'password':
                    inp.clear()
                    inp.input(password)
            
            # 点击登录按钮
            time.sleep(0.5)
            btns = page.eles('tag:button')
            for btn in btns:
                txt = btn.text.lower() if btn.text else ''
                if '登录' in txt or 'login' in txt or '登入' in txt:
                    try:
                        page.run_js('arguments[0].click()', btn)
                        print('已自动点击登录按钮')
                    except:
                        pass
                    break
        
        # 等待登录完成
        print('等待登录完成...(检测到跳转后自动保存)')
        original_url = page.url
        for i in range(120):  # 最多等2分钟
            time.sleep(1)
            current = page.url
            if 'login' not in current.lower() and 'passport' not in current.lower():
                if current != original_url:
                    print('检测到登录成功！')
                    time.sleep(2)  # 等cookie写入
                    break
            if i % 15 == 0 and i > 0:
                print(f'等待中... {i}秒')
        
        save_session(page, session_name)
        log_attempt(url, True, 'headed', 'manual_login')
        print('登录完成，session已保存')
        return page
        
    except Exception as e:
        print(f'错误: {e}')
        log_attempt(url, False, 'headed', str(e))
        page.quit()
        return None

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 3:
        print('Usage: python smart_login.py <url> <session_name> [account] [password]')
        sys.exit(1)
    
    url = sys.argv[1]
    name = sys.argv[2]
    account = sys.argv[3] if len(sys.argv) > 3 else None
    password = sys.argv[4] if len(sys.argv) > 4 else None
    
    page = smart_login(url, name, account, password)
    if page:
        print(f'当前页面: {page.title}')
        print(f'URL: {page.url}')
        page.quit()
