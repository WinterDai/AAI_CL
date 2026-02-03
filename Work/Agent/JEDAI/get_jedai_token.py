#!/usr/bin/env python3
"""
获取JEDAI认证Token
用于Continue配置
"""
import requests
import getpass
import json
from datetime import datetime, timedelta

# JEDAI服务器地址
JEDAI_URL = "http://sjf-dsgdspr-084.cadence.com:5668"

def get_token():
    """获取JEDAI Token"""
    print("=" * 60)
    print("JEDAI Token获取工具")
    print("=" * 60)
    
    username = getpass.getuser()
    print(f"\n用户名: {username}")
    password = getpass.getpass("请输入LDAP密码: ")
    
    try:
        response = requests.post(
            f"{JEDAI_URL}/api/v1/security/login",
            headers={"Content-Type": "application/json"},
            json={
                "username": username,
                "password": password,
                "provider": "LDAP"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            token = response.json()["access_token"]
            expires_at = datetime.now() + timedelta(hours=10)
            
            print("\n✓ Token获取成功！")
            print("=" * 60)
            print(f"Token: {token}")
            print("=" * 60)
            print(f"有效期: 10小时")
            print(f"过期时间: {expires_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print("\n将此Token复制到Continue配置文件中的apiKey字段")
            
            # 保存到文件
            token_file = "jedai_token.txt"
            with open(token_file, 'w') as f:
                f.write(f"Token: {token}\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Expires: {expires_at.strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            print(f"\nToken已保存到: {token_file}")
            return token
            
        else:
            print(f"\n❌ 认证失败: {response.status_code}")
            print(response.text)
            return None
            
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        return None

if __name__ == "__main__":
    get_token()
