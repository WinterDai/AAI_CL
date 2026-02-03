import os
import requests
import json
import getpass
import urllib3
from pathlib import Path
from typing import Optional

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

JEDAI_URLS = [
    "https://jedai-ai:2513",           # Primary
    "http://jedai-ai.cadence.com:5668", # Backup
]

TOKEN_CACHE_FILE = Path.home() / ".jedai_token"

class JedaiAuth:
    def __init__(self):
        self.username = os.environ.get("JEDAI_USERNAME") or os.environ.get("USER") or os.environ.get("USERNAME")
        self.password = os.environ.get("JEDAI_PASSWORD")
        self.token = None
        self.connected_url = None
        self._load_cached_token()

    def _load_cached_token(self):
        token_env = os.environ.get("JEDAI_TOKEN")
        if token_env:
            self.token = token_env
            self.connected_url = JEDAI_URLS[0]
            return

        if TOKEN_CACHE_FILE.exists():
            try:
                with open(TOKEN_CACHE_FILE, 'r') as f:
                    data = json.load(f)
                    if data.get("username") == self.username:
                        self.token = data.get("token")
                        self.connected_url = data.get("url")
            except:
                pass

    def save_token(self):
        if not self.token: return
        try:
            with open(TOKEN_CACHE_FILE, 'w') as f:
                json.dump({
                    "username": self.username,
                    "token": self.token,
                    "url": self.connected_url
                }, f)
            TOKEN_CACHE_FILE.chmod(0o600)
        except:
            pass

    def connect(self, force=False):
        if self.token and self.connected_url and not force:
            return True

        if not self.password:
            print("Interactive password input required (or set JEDAI_PASSWORD env var).")
            self.password = getpass.getpass(f"Password for {self.username}: ")

        for url in JEDAI_URLS:
            try:
                print(f"Connecting to {url}...")
                resp = requests.post(
                    f"{url}/api/v1/security/login",
                    json={"username": self.username, "password": self.password, "provider": "LDAP"},
                    headers={"Content-Type": "application/json"},
                    timeout=10,
                    verify=False
                )
                if resp.status_code == 200:
                    self.token = resp.json()["access_token"]
                    self.connected_url = url
                    self.save_token()
                    print("Login successful.")
                    return True
                else:
                    print(f"Login failed at {url}: {resp.status_code}")
            except Exception as e:
                print(f"Connection error to {url}: {e}")
        return False

    def get_token(self):
        if not self.token:
            if not self.connect():
                raise Exception("Authentication failed")
        return self.token
    
    def refresh_token(self):
        """强制刷新token"""
        self.clear_token()
        return self.connect(force=True)
    
    def clear_token(self):
        self.token = None
        if TOKEN_CACHE_FILE.exists():
            try:
                TOKEN_CACHE_FILE.unlink()
            except:
                pass
    
    def validate_token(self):
        """验证token是否有效"""
        if not self.token or not self.connected_url:
            return False
        
        try:
            # 使用简单的API调用来验证token
            resp = requests.get(
                f"{self.connected_url}/api/v1/models",
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=5,
                verify=False
            )
            return resp.status_code == 200
        except:
            return False
    
    def get_valid_token(self):
        """获取有效的token，如果过期则自动刷新"""
        if self.token and self.validate_token():
            return self.token
        
        print("Token expired or invalid, refreshing...")
        if self.refresh_token():
            return self.token
        else:
            raise Exception("Failed to refresh authentication token")
