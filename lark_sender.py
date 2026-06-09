#!/usr/bin/env python3
"""
飞书消息发送模块（使用API，不依赖lark-cli）
"""

import os
import requests


def get_tenant_access_token(app_id: str, app_secret: str) -> str:
    """获取tenant_access_token"""
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    payload = {
        "app_id": app_id,
        "app_secret": app_secret
    }

    try:
        resp = requests.post(url, json=payload, timeout=10)
        data = resp.json()

        if data.get("code") == 0:
            return data.get("tenant_access_token")
        else:
            print(f"   ❌ 获取token失败: {data.get('msg')}")
            return None
    except Exception as e:
        print(f"   ❌ 获取token异常: {e}")
        return None


def send_to_lark_api(content: str) -> bool:
    """使用飞书API发送消息（不依赖lark-cli）"""
    print("\n📤 发送到飞书...")

    # 从环境变量获取配置
    app_id = os.environ.get('LARK_APP_ID', '')
    app_secret = os.environ.get('LARK_APP_SECRET', '')
    user_id = os.environ.get('LARK_USER_ID', '')

    if not all([app_id, app_secret, user_id]):
        print("   ❌ 缺少飞书配置（LARK_APP_ID/LARK_APP_SECRET/LARK_USER_ID）")
        return False

    # Step 1: 获取token
    token = get_tenant_access_token(app_id, app_secret)
    if not token:
        return False

    # Step 2: 发送消息
    url = "https://open.feishu.cn/open-apis/im/v1/messages"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=utf-8"
    }

    payload = {
        "receive_id": user_id,
        "msg_type": "text",
        "content": f'{{"text":"{content}"}}'
    }

    params = {
        "receive_id_type": "open_id"  # 使用open_id类型
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, params=params, timeout=30)
        data = resp.json()

        if data.get("code") == 0:
            print("   ✅ 推送成功")
            return True
        else:
            print(f"   ❌ 推送失败: {data.get('msg')}")
            return False

    except Exception as e:
        print(f"   ❌ 推送异常: {e}")
        return False


if __name__ == "__main__":
    # 测试
    test_content = "🌐 Savana 业内动态测试消息"
    send_to_lark_api(test_content)
