#!/usr/bin/env python3
"""
Proxy Rotation Manager
Supports residential, datacenter, and SOCKS proxies
"""

import json
import random
import time
import requests
from pathlib import Path
from typing import Optional, List, Dict
from dataclasses import dataclass
from collections import defaultdict

SECRETS_DIR = Path.home() / ".clawdbot" / "secrets"


@dataclass
class ProxyInfo:
    url: str
    type: str  # residential, datacenter, socks5
    country: Optional[str] = None
    last_used: float = 0
    fail_count: int = 0
    success_count: int = 0


class ProxyPool:
    """Manage and rotate through proxy pool"""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or (SECRETS_DIR / "proxies.json")
        self.proxies: List[ProxyInfo] = []
        self.stats: Dict[str, Dict] = defaultdict(lambda: {"success": 0, "fail": 0})
        self._load_config()
    
    def _load_config(self):
        """Load proxies from config file"""
        if not self.config_path.exists():
            return
        
        config = json.loads(self.config_path.read_text())
        
        # Load residential proxies
        for proxy in config.get("residential", []):
            if isinstance(proxy, str):
                self.proxies.append(ProxyInfo(url=proxy, type="residential"))
            else:
                self.proxies.append(ProxyInfo(
                    url=proxy.get("url"),
                    type="residential",
                    country=proxy.get("country")
                ))
        
        # Load datacenter proxies
        for proxy in config.get("datacenter", []):
            if isinstance(proxy, str):
                self.proxies.append(ProxyInfo(url=proxy, type="datacenter"))
            else:
                self.proxies.append(ProxyInfo(
                    url=proxy.get("url"),
                    type="datacenter",
                    country=proxy.get("country")
                ))
        
        # Load rotating proxy (single endpoint)
        rotating = config.get("rotating")
        if rotating:
            self.proxies.append(ProxyInfo(url=rotating, type="rotating"))
    
    def get_proxy(self, 
                  proxy_type: Optional[str] = None,
                  country: Optional[str] = None,
                  exclude_failed: bool = True) -> Optional[str]:
        """
        Get a proxy from the pool
        
        Args:
            proxy_type: Filter by type (residential, datacenter, rotating)
            country: Filter by country code
            exclude_failed: Skip proxies with high fail rate
        
        Returns:
            Proxy URL or None
        """
        candidates = self.proxies.copy()
        
        if proxy_type:
            candidates = [p for p in candidates if p.type == proxy_type]
        
        if country:
            candidates = [p for p in candidates if p.country == country]
        
        if exclude_failed:
            # Exclude proxies with >50% fail rate and at least 3 attempts
            candidates = [p for p in candidates 
                         if p.success_count + p.fail_count < 3 or 
                         p.fail_count / (p.success_count + p.fail_count) < 0.5]
        
        if not candidates:
            return None
        
        # Prefer least recently used
        candidates.sort(key=lambda p: p.last_used)
        chosen = candidates[0]
        chosen.last_used = time.time()
        
        return chosen.url
    
    def mark_success(self, proxy_url: str):
        """Mark proxy as successful"""
        for p in self.proxies:
            if p.url == proxy_url:
                p.success_count += 1
                break
        self.stats[proxy_url]["success"] += 1
    
    def mark_failed(self, proxy_url: str):
        """Mark proxy as failed"""
        for p in self.proxies:
            if p.url == proxy_url:
                p.fail_count += 1
                break
        self.stats[proxy_url]["fail"] += 1
    
    def get_stats(self) -> Dict:
        """Get proxy usage statistics"""
        return {
            "total": len(self.proxies),
            "by_type": {
                "residential": len([p for p in self.proxies if p.type == "residential"]),
                "datacenter": len([p for p in self.proxies if p.type == "datacenter"]),
                "rotating": len([p for p in self.proxies if p.type == "rotating"])
            },
            "usage": dict(self.stats)
        }


def test_proxy(proxy_url: str, test_url: str = "https://httpbin.org/ip", timeout: int = 10) -> Dict:
    """
    Test if a proxy is working
    
    Returns:
        dict: {success: bool, ip: str, latency_ms: int, error: str}
    """
    proxies = {
        "http": proxy_url,
        "https": proxy_url
    }
    
    start = time.time()
    try:
        resp = requests.get(test_url, proxies=proxies, timeout=timeout)
        latency = int((time.time() - start) * 1000)
        
        if resp.status_code == 200:
            data = resp.json()
            return {
                "success": True,
                "ip": data.get("origin"),
                "latency_ms": latency
            }
        else:
            return {
                "success": False,
                "error": f"HTTP {resp.status_code}",
                "latency_ms": latency
            }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def get_my_ip() -> str:
    """Get current public IP without proxy"""
    try:
        return requests.get("https://httpbin.org/ip", timeout=5).json()["origin"]
    except:
        return "unknown"


def create_proxy_config_template():
    """Create template proxies.json"""
    template = {
        "rotating": "http://user:pass@rotating-proxy.provider.com:port",
        "residential": [
            "socks5://user:pass@residential1.provider.com:port",
            "socks5://user:pass@residential2.provider.com:port"
        ],
        "datacenter": [
            "http://user:pass@dc1.provider.com:port",
            "http://user:pass@dc2.provider.com:port"
        ],
        "_comment": "Replace with your actual proxy credentials. Types: http, https, socks5"
    }
    
    SECRETS_DIR.mkdir(parents=True, exist_ok=True)
    config_path = SECRETS_DIR / "proxies.json"
    
    if not config_path.exists():
        config_path.write_text(json.dumps(template, indent=2))
        print(f"Created template: {config_path}")
        return config_path
    else:
        print(f"Config already exists: {config_path}")
        return None


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Proxy Manager')
    subparsers = parser.add_subparsers(dest='command')
    
    # Get proxy
    get_parser = subparsers.add_parser('get', help='Get a proxy')
    get_parser.add_argument('--type', '-t', choices=['residential', 'datacenter', 'rotating'],
                           help='Proxy type')
    get_parser.add_argument('--country', '-c', help='Country code')
    
    # Test proxy
    test_parser = subparsers.add_parser('test', help='Test a proxy')
    test_parser.add_argument('proxy', help='Proxy URL')
    
    # Test all
    test_all_parser = subparsers.add_parser('test-all', help='Test all proxies')
    
    # Stats
    stats_parser = subparsers.add_parser('stats', help='Show statistics')
    
    # Init config
    init_parser = subparsers.add_parser('init', help='Create config template')
    
    # My IP
    myip_parser = subparsers.add_parser('myip', help='Show current IP')
    
    args = parser.parse_args()
    
    if args.command == 'get':
        pool = ProxyPool()
        proxy = pool.get_proxy(proxy_type=args.type, country=args.country)
        if proxy:
            print(proxy)
        else:
            print("No proxy available")
            exit(1)
    
    elif args.command == 'test':
        result = test_proxy(args.proxy)
        print(json.dumps(result, indent=2))
        if not result["success"]:
            exit(1)
    
    elif args.command == 'test-all':
        pool = ProxyPool()
        print(f"Testing {len(pool.proxies)} proxies...")
        for p in pool.proxies:
            result = test_proxy(p.url)
            status = "✓" if result.get("success") else "✗"
            ip = result.get("ip", result.get("error", "N/A"))
            latency = result.get("latency_ms", "N/A")
            print(f"{status} [{p.type}] {p.url[:40]}... -> {ip} ({latency}ms)")
    
    elif args.command == 'stats':
        pool = ProxyPool()
        print(json.dumps(pool.get_stats(), indent=2))
    
    elif args.command == 'init':
        create_proxy_config_template()
    
    elif args.command == 'myip':
        print(get_my_ip())
    
    else:
        parser.print_help()
