#!/usr/bin/env python3
"""
CAPTCHA Solving Utilities
Supports 2Captcha, Anti-Captcha, and CapSolver
"""

import json
import time
import requests
from pathlib import Path

SECRETS_DIR = Path.home() / ".clawdbot" / "secrets"


def load_api_keys():
    """Load CAPTCHA API keys from secrets"""
    key_file = SECRETS_DIR / "captcha.json"
    if key_file.exists():
        return json.loads(key_file.read_text())
    return {}


def solve_recaptcha_v2(site_key: str, page_url: str, invisible: bool = False, provider: str = None) -> str:
    """
    Solve reCAPTCHA v2
    
    Args:
        site_key: The site key (data-sitekey attribute)
        page_url: The page URL where CAPTCHA is displayed
        invisible: Whether it's invisible reCAPTCHA
        provider: Force specific provider (2captcha, anticaptcha, capsolver)
    
    Returns:
        CAPTCHA token or None if failed
    """
    keys = load_api_keys()
    
    # Try providers in order
    providers = [provider] if provider else ['capsolver', '2captcha', 'anticaptcha']
    
    for p in providers:
        if p == '2captcha' and keys.get('2captcha'):
            return _solve_2captcha_recaptcha(keys['2captcha'], site_key, page_url, invisible)
        elif p == 'anticaptcha' and keys.get('anticaptcha'):
            return _solve_anticaptcha_recaptcha(keys['anticaptcha'], site_key, page_url, invisible)
        elif p == 'capsolver' and keys.get('capsolver'):
            return _solve_capsolver_recaptcha(keys['capsolver'], site_key, page_url, invisible)
    
    raise ValueError("No CAPTCHA API keys configured. Add keys to ~/.clawdbot/secrets/captcha.json")


def solve_recaptcha_v3(site_key: str, page_url: str, action: str = "verify", min_score: float = 0.7, provider: str = None) -> str:
    """
    Solve reCAPTCHA v3
    
    Args:
        site_key: The site key
        page_url: The page URL
        action: The action value (usually found in grecaptcha.execute call)
        min_score: Minimum required score (0.1-0.9)
        provider: Force specific provider
    
    Returns:
        CAPTCHA token or None if failed
    """
    keys = load_api_keys()
    
    if keys.get('2captcha'):
        api_key = keys['2captcha']
        resp = requests.post("http://2captcha.com/in.php", data={
            "key": api_key,
            "method": "userrecaptcha",
            "googlekey": site_key,
            "pageurl": page_url,
            "version": "v3",
            "action": action,
            "min_score": min_score,
            "json": 1
        }).json()
        
        if resp.get("status") != 1:
            raise ValueError(f"2Captcha error: {resp.get('request')}")
        
        task_id = resp["request"]
        return _poll_2captcha(api_key, task_id)
    
    raise ValueError("No reCAPTCHA v3 provider available")


def solve_hcaptcha(site_key: str, page_url: str, provider: str = None) -> str:
    """
    Solve hCaptcha
    
    Args:
        site_key: The site key (data-sitekey attribute)
        page_url: The page URL
        provider: Force specific provider
    
    Returns:
        CAPTCHA token or None if failed
    """
    keys = load_api_keys()
    
    if keys.get('anticaptcha'):
        api_key = keys['anticaptcha']
        resp = requests.post("https://api.anti-captcha.com/createTask", json={
            "clientKey": api_key,
            "task": {
                "type": "HCaptchaTaskProxyless",
                "websiteURL": page_url,
                "websiteKey": site_key
            }
        }).json()
        
        if resp.get("errorId"):
            raise ValueError(f"Anti-Captcha error: {resp.get('errorDescription')}")
        
        task_id = resp["taskId"]
        return _poll_anticaptcha(api_key, task_id)
    
    if keys.get('2captcha'):
        api_key = keys['2captcha']
        resp = requests.post("http://2captcha.com/in.php", data={
            "key": api_key,
            "method": "hcaptcha",
            "sitekey": site_key,
            "pageurl": page_url,
            "json": 1
        }).json()
        
        if resp.get("status") != 1:
            raise ValueError(f"2Captcha error: {resp.get('request')}")
        
        task_id = resp["request"]
        return _poll_2captcha(api_key, task_id)
    
    raise ValueError("No hCaptcha provider available")


def solve_turnstile(site_key: str, page_url: str, provider: str = None) -> str:
    """
    Solve Cloudflare Turnstile
    
    Args:
        site_key: The Turnstile site key
        page_url: The page URL
        provider: Force specific provider
    
    Returns:
        CAPTCHA token or None if failed
    """
    keys = load_api_keys()
    
    if keys.get('capsolver'):
        api_key = keys['capsolver']
        resp = requests.post("https://api.capsolver.com/createTask", json={
            "clientKey": api_key,
            "task": {
                "type": "AntiTurnstileTaskProxyLess",
                "websiteURL": page_url,
                "websiteKey": site_key
            }
        }).json()
        
        if resp.get("errorId"):
            raise ValueError(f"CapSolver error: {resp.get('errorDescription')}")
        
        task_id = resp["taskId"]
        return _poll_capsolver(api_key, task_id)
    
    if keys.get('2captcha'):
        api_key = keys['2captcha']
        resp = requests.post("http://2captcha.com/in.php", data={
            "key": api_key,
            "method": "turnstile",
            "sitekey": site_key,
            "pageurl": page_url,
            "json": 1
        }).json()
        
        if resp.get("status") != 1:
            raise ValueError(f"2Captcha error: {resp.get('request')}")
        
        task_id = resp["request"]
        return _poll_2captcha(api_key, task_id)
    
    raise ValueError("No Turnstile provider available")


def inject_captcha_token(page, token: str, captcha_type: str = "recaptcha"):
    """
    Inject solved CAPTCHA token into page
    
    Args:
        page: DrissionPage or Selenium driver
        token: The solved CAPTCHA token
        captcha_type: recaptcha, hcaptcha, or turnstile
    """
    if captcha_type == "recaptcha":
        js = f"""
            document.getElementById('g-recaptcha-response').innerHTML = '{token}';
            if (typeof ___grecaptcha_cfg !== 'undefined') {{
                Object.entries(___grecaptcha_cfg.clients).forEach(([k,v]) => {{
                    if (v.callback) v.callback('{token}');
                }});
            }}
        """
    elif captcha_type == "hcaptcha":
        js = f"""
            document.querySelector('[name="h-captcha-response"]').value = '{token}';
            document.querySelector('[name="g-recaptcha-response"]').value = '{token}';
        """
    elif captcha_type == "turnstile":
        js = f"""
            document.querySelector('[name="cf-turnstile-response"]').value = '{token}';
        """
    else:
        raise ValueError(f"Unknown captcha type: {captcha_type}")
    
    # Execute based on driver type
    if hasattr(page, 'run_js'):
        page.run_js(js)
    else:
        page.execute_script(js)


# Private helper functions

def _solve_2captcha_recaptcha(api_key, site_key, page_url, invisible=False):
    resp = requests.post("http://2captcha.com/in.php", data={
        "key": api_key,
        "method": "userrecaptcha",
        "googlekey": site_key,
        "pageurl": page_url,
        "invisible": 1 if invisible else 0,
        "json": 1
    }).json()
    
    if resp.get("status") != 1:
        raise ValueError(f"2Captcha error: {resp.get('request')}")
    
    return _poll_2captcha(api_key, resp["request"])


def _solve_anticaptcha_recaptcha(api_key, site_key, page_url, invisible=False):
    task_type = "RecaptchaV2TaskProxyless"
    if invisible:
        task_type = "RecaptchaV2EnterpriseTaskProxyless"
    
    resp = requests.post("https://api.anti-captcha.com/createTask", json={
        "clientKey": api_key,
        "task": {
            "type": task_type,
            "websiteURL": page_url,
            "websiteKey": site_key,
            "isInvisible": invisible
        }
    }).json()
    
    if resp.get("errorId"):
        raise ValueError(f"Anti-Captcha error: {resp.get('errorDescription')}")
    
    return _poll_anticaptcha(api_key, resp["taskId"])


def _solve_capsolver_recaptcha(api_key, site_key, page_url, invisible=False):
    resp = requests.post("https://api.capsolver.com/createTask", json={
        "clientKey": api_key,
        "task": {
            "type": "ReCaptchaV2TaskProxyLess",
            "websiteURL": page_url,
            "websiteKey": site_key,
            "isInvisible": invisible
        }
    }).json()
    
    if resp.get("errorId"):
        raise ValueError(f"CapSolver error: {resp.get('errorDescription')}")
    
    return _poll_capsolver(api_key, resp["taskId"])


def _poll_2captcha(api_key, task_id, max_attempts=60):
    for _ in range(max_attempts):
        time.sleep(3)
        result = requests.get(
            f"http://2captcha.com/res.php?key={api_key}&action=get&id={task_id}&json=1"
        ).json()
        
        if result.get("status") == 1:
            return result["request"]
        elif result.get("request") != "CAPCHA_NOT_READY":
            raise ValueError(f"2Captcha error: {result.get('request')}")
    
    raise TimeoutError("CAPTCHA solving timed out")


def _poll_anticaptcha(api_key, task_id, max_attempts=60):
    for _ in range(max_attempts):
        time.sleep(3)
        result = requests.post("https://api.anti-captcha.com/getTaskResult", json={
            "clientKey": api_key,
            "taskId": task_id
        }).json()
        
        if result.get("status") == "ready":
            return result["solution"]["gRecaptchaResponse"]
        elif result.get("errorId"):
            raise ValueError(f"Anti-Captcha error: {result.get('errorDescription')}")
    
    raise TimeoutError("CAPTCHA solving timed out")


def _poll_capsolver(api_key, task_id, max_attempts=60):
    for _ in range(max_attempts):
        time.sleep(3)
        result = requests.post("https://api.capsolver.com/getTaskResult", json={
            "clientKey": api_key,
            "taskId": task_id
        }).json()
        
        if result.get("status") == "ready":
            return result["solution"].get("gRecaptchaResponse") or result["solution"].get("token")
        elif result.get("errorId"):
            raise ValueError(f"CapSolver error: {result.get('errorDescription')}")
    
    raise TimeoutError("CAPTCHA solving timed out")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Solve CAPTCHAs')
    parser.add_argument('--type', '-t', choices=['recaptcha2', 'recaptcha3', 'hcaptcha', 'turnstile'],
                        required=True, help='CAPTCHA type')
    parser.add_argument('--sitekey', '-k', required=True, help='Site key')
    parser.add_argument('--url', '-u', required=True, help='Page URL')
    parser.add_argument('--action', '-a', default='verify', help='Action (reCAPTCHA v3)')
    parser.add_argument('--provider', '-p', help='Force specific provider')
    
    args = parser.parse_args()
    
    try:
        if args.type == 'recaptcha2':
            token = solve_recaptcha_v2(args.sitekey, args.url, provider=args.provider)
        elif args.type == 'recaptcha3':
            token = solve_recaptcha_v3(args.sitekey, args.url, args.action, provider=args.provider)
        elif args.type == 'hcaptcha':
            token = solve_hcaptcha(args.sitekey, args.url, provider=args.provider)
        elif args.type == 'turnstile':
            token = solve_turnstile(args.sitekey, args.url, provider=args.provider)
        
        print(f"Token: {token}")
    except Exception as e:
        print(f"Error: {e}")
        exit(1)
