#!/usr/bin/env python3
"""
通过飞书API获取User Access Token
需要先有 LARK_APP_ID 和 LARK_APP_SECRET
"""

import requests
import json

# 配置
LARK_APP_ID = "cli_a9418088f5b8dcb1"
LARK_APP_SECRET = input("请输入LARK_APP_SECRET: ").strip()

print("\n🔑 正在获取 tenant_access_token...")

# Step 1: 获取 tenant_access_token
url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
payload = {
    "app_id": LARK_APP_ID,
    "app_secret": LARK_APP_SECRET
}

try:
    resp = requests.post(url, json=payload, timeout=10)
    data = resp.json()

    if data.get("code") == 0:
        tenant_token = data.get("tenant_access_token")
        print(f"✅ tenant_access_token: {tenant_token[:20]}...")
        print("\n⚠️ 注意：")
        print("tenant_access_token 是应用级token，可以用于发送消息")
        print("但它不同于user_access_token（用户级token）")
        print()
        print("💡 对于发送飞书消息，使用 tenant_access_token 就够了！")
        print()
        print(f"完整token: {tenant_token}")
    else:
        print(f"❌ 获取失败: {data.get('msg')}")

except Exception as e:
    print(f"❌ 请求失败: {e}")
