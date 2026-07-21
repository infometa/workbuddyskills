#!/usr/bin/env python3
"""
Browser Session Manager
Handles cookie persistence, localStorage sync, and multi-profile management
"""

import json
import time
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any

SESSIONS_DIR = Path.home() / ".clawdbot" / "browser-sessions"
PROFILES_DIR = Path.home() / ".clawdbot" / "browser-profiles"


def init_dirs():
    """Initialize storage directories"""
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)


class SessionManager:
    """Manage browser sessions with cookie and localStorage persistence"""
    
    def __init__(self, session_name: str):
        init_dirs()
        self.session_name = session_name
        self.session_file = SESSIONS_DIR / f"{session_name}.json"
        self.data = self._load()
    
    def _load(self) -> dict:
        """Load session data from file"""
        if self.session_file.exists():
            return json.loads(self.session_file.read_text())
        return {
            "name": self.session_name,
            "created": datetime.now().isoformat(),
            "updated": None,
            "cookies": {},
            "localStorage": {},
            "metadata": {}
        }
    
    def save(self):
        """Save session data to file"""
        self.data["updated"] = datetime.now().isoformat()
        self.session_file.write_text(json.dumps(self.data, indent=2))
    
    def set_cookies(self, cookies: Dict[str, Any], domain: str = None):
        """Store cookies, optionally grouped by domain"""
        if domain:
            if "cookies_by_domain" not in self.data:
                self.data["cookies_by_domain"] = {}
            self.data["cookies_by_domain"][domain] = cookies
        else:
            self.data["cookies"] = cookies
        self.save()
    
    def get_cookies(self, domain: str = None) -> Dict[str, Any]:
        """Get cookies, optionally for specific domain"""
        if domain and "cookies_by_domain" in self.data:
            return self.data["cookies_by_domain"].get(domain, {})
        return self.data.get("cookies", {})
    
    def set_local_storage(self, ls_data: dict, origin: str = None):
        """Store localStorage data"""
        if origin:
            if "localStorage_by_origin" not in self.data:
                self.data["localStorage_by_origin"] = {}
            self.data["localStorage_by_origin"][origin] = ls_data
        else:
            self.data["localStorage"] = ls_data
        self.save()
    
    def get_local_storage(self, origin: str = None) -> dict:
        """Get localStorage data"""
        if origin and "localStorage_by_origin" in self.data:
            return self.data["localStorage_by_origin"].get(origin, {})
        return self.data.get("localStorage", {})
    
    def set_metadata(self, key: str, value: Any):
        """Store arbitrary metadata"""
        self.data["metadata"][key] = value
        self.save()
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata value"""
        return self.data["metadata"].get(key, default)
    
    def export_for_browser(self, browser_type: str = "drission") -> dict:
        """Export session in format suitable for browser injection"""
        return {
            "cookies": self.data.get("cookies", {}),
            "localStorage": self.data.get("localStorage", {}),
            "format": browser_type
        }
    
    def import_from_browser(self, page, browser_type: str = "drission"):
        """Import cookies and localStorage from active browser page"""
        if browser_type == "drission":
            self.data["cookies"] = page.cookies.as_dict()
            try:
                ls = page.run_js("return JSON.stringify(localStorage);")
                self.data["localStorage"] = json.loads(ls) if ls else {}
            except:
                pass
            self.data["metadata"]["url"] = page.url
            self.data["metadata"]["title"] = page.title
        else:  # selenium/undetected
            # Convert cookie list to dict
            cookies = {}
            for c in page.get_cookies():
                cookies[c["name"]] = {
                    "value": c["value"],
                    "domain": c.get("domain"),
                    "path": c.get("path"),
                    "secure": c.get("secure"),
                    "httpOnly": c.get("httpOnly")
                }
            self.data["cookies"] = cookies
            try:
                ls = page.execute_script("return JSON.stringify(localStorage);")
                self.data["localStorage"] = json.loads(ls) if ls else {}
            except:
                pass
            self.data["metadata"]["url"] = page.current_url
            self.data["metadata"]["title"] = page.title
        
        self.save()
    
    def apply_to_browser(self, page, browser_type: str = "drission"):
        """Apply saved session to browser page"""
        if browser_type == "drission":
            # Set cookies
            for name, cookie_data in self.data.get("cookies", {}).items():
                if isinstance(cookie_data, str):
                    page.cookies.set({name: cookie_data})
                else:
                    page.cookies.set({name: cookie_data.get("value", "")})
            
            # Set localStorage
            ls = self.data.get("localStorage", {})
            if ls:
                for k, v in ls.items():
                    v_escaped = json.dumps(v) if not isinstance(v, str) else f'"{v}"'
                    page.run_js(f"localStorage.setItem('{k}', {v_escaped});")
        else:  # selenium
            for name, cookie_data in self.data.get("cookies", {}).items():
                try:
                    if isinstance(cookie_data, str):
                        page.add_cookie({"name": name, "value": cookie_data})
                    else:
                        page.add_cookie({
                            "name": name,
                            "value": cookie_data.get("value", ""),
                            "domain": cookie_data.get("domain"),
                            "path": cookie_data.get("path", "/"),
                            "secure": cookie_data.get("secure", False)
                        })
                except:
                    pass
            
            ls = self.data.get("localStorage", {})
            if ls:
                for k, v in ls.items():
                    v_escaped = json.dumps(v) if not isinstance(v, str) else f'"{v}"'
                    page.execute_script(f"localStorage.setItem('{k}', {v_escaped});")


def list_sessions() -> List[dict]:
    """List all saved sessions"""
    init_dirs()
    sessions = []
    for f in SESSIONS_DIR.glob("*.json"):
        try:
            data = json.loads(f.read_text())
            sessions.append({
                "name": f.stem,
                "created": data.get("created"),
                "updated": data.get("updated"),
                "url": data.get("metadata", {}).get("url"),
                "cookies_count": len(data.get("cookies", {}))
            })
        except:
            pass
    return sessions


def delete_session(session_name: str) -> bool:
    """Delete a saved session"""
    session_file = SESSIONS_DIR / f"{session_name}.json"
    if session_file.exists():
        session_file.unlink()
        return True
    return False


def create_profile(profile_name: str) -> Path:
    """Create a new browser profile directory"""
    init_dirs()
    profile_path = PROFILES_DIR / profile_name
    profile_path.mkdir(exist_ok=True)
    return profile_path


def get_profile_path(profile_name: str) -> Optional[Path]:
    """Get path to existing profile or None"""
    profile_path = PROFILES_DIR / profile_name
    return profile_path if profile_path.exists() else None


def list_profiles() -> List[str]:
    """List all browser profiles"""
    init_dirs()
    return [d.name for d in PROFILES_DIR.iterdir() if d.is_dir()]


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Session Manager')
    subparsers = parser.add_subparsers(dest='command')
    
    # List sessions
    list_parser = subparsers.add_parser('list', help='List sessions')
    
    # Show session
    show_parser = subparsers.add_parser('show', help='Show session details')
    show_parser.add_argument('name', help='Session name')
    
    # Delete session
    del_parser = subparsers.add_parser('delete', help='Delete session')
    del_parser.add_argument('name', help='Session name')
    
    # List profiles
    profiles_parser = subparsers.add_parser('profiles', help='List profiles')
    
    # Create profile
    create_parser = subparsers.add_parser('create-profile', help='Create profile')
    create_parser.add_argument('name', help='Profile name')
    
    args = parser.parse_args()
    
    if args.command == 'list':
        sessions = list_sessions()
        if sessions:
            print(f"{'Name':<20} {'Updated':<25} {'URL':<40} {'Cookies'}")
            print("-" * 100)
            for s in sessions:
                print(f"{s['name']:<20} {s.get('updated', 'N/A')[:25]:<25} {(s.get('url') or 'N/A')[:40]:<40} {s['cookies_count']}")
        else:
            print("No sessions found")
    
    elif args.command == 'show':
        sm = SessionManager(args.name)
        print(json.dumps(sm.data, indent=2))
    
    elif args.command == 'delete':
        if delete_session(args.name):
            print(f"Deleted: {args.name}")
        else:
            print(f"Session not found: {args.name}")
    
    elif args.command == 'profiles':
        profiles = list_profiles()
        if profiles:
            for p in profiles:
                print(p)
        else:
            print("No profiles found")
    
    elif args.command == 'create-profile':
        path = create_profile(args.name)
        print(f"Created: {path}")
    
    else:
        parser.print_help()
