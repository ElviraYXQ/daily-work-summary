#!/usr/bin/env python3
"""
飞书每日消息收集脚本 - GitHub Actions 版本
使用飞书 REST API 直接获取消息
"""

import os
import json
import requests
from datetime import datetime, timedelta
from collections import defaultdict
import time


def get_tenant_access_token():
    """获取应用访问令牌"""
    app_id = os.environ.get('LARK_APP_ID')
    app_secret = os.environ.get('LARK_APP_SECRET')

    if not all([app_id, app_secret]):
        raise ValueError("缺少 LARK_APP_ID 或 LARK_APP_SECRET")

    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    payload = {
        "app_id": app_id,
        "app_secret": app_secret
    }

    response = requests.post(url, json=payload, timeout=10)
    result = response.json()

    if result.get('code') == 0:
        return result.get('tenant_access_token')
    else:
        raise ValueError(f"获取 token 失败: {result}")


def search_messages_api(start_time, end_time, page_token=None, page_size=50):
    """使用飞书 API 搜索消息"""
    # 注意：这个 API 需要 user_access_token，不是 tenant_access_token
    # 我们需要从环境变量获取
    user_token = os.environ.get('LARK_USER_ACCESS_TOKEN')

    if not user_token:
        raise ValueError("缺少 LARK_USER_ACCESS_TOKEN")

    url = "https://open.feishu.cn/open-apis/search/v2/message"

    headers = {
        "Authorization": f"Bearer {user_token}",
        "Content-Type": "application/json"
    }

    params = {
        "page_size": page_size,
        "start_time": start_time,
        "end_time": end_time
    }

    if page_token:
        params['page_token'] = page_token

    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        result = response.json()

        if result.get('code') == 0:
            return result.get('data', {})
        else:
            print(f"API 错误: {result}")
            return None

    except Exception as e:
        print(f"请求失败: {str(e)}")
        return None


def get_yesterday_messages():
    """获取昨天的所有消息"""
    # 计算昨天的时间范围（Unix 时间戳）
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start = int((today - timedelta(days=1)).timestamp())
    yesterday_end = int((today - timedelta(seconds=1)).timestamp())

    print(f"📅 获取消息时间范围：")
    print(f"   开始: {datetime.fromtimestamp(yesterday_start).strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   结束: {datetime.fromtimestamp(yesterday_end).strftime('%Y-%m-%d %H:%M:%S')}")

    all_messages = []
    page_token = None
    page_count = 0
    max_pages = 20

    while page_count < max_pages:
        page_count += 1
        print(f"📦 获取第 {page_count} 页消息...")

        data = search_messages_api(yesterday_start, yesterday_end, page_token, 50)

        if not data:
            break

        messages = data.get('messages', [])
        all_messages.extend(messages)
        print(f"   ✓ 获取 {len(messages)} 条消息")

        if not data.get('has_more'):
            break

        page_token = data.get('page_token')
        time.sleep(0.5)  # 避免请求过快

    print(f"\n✅ 总共获取 {len(all_messages)} 条消息")
    return all_messages


def is_message_relevant(msg, user_name="易希倩 Queenie Yi", user_id="ou_cc38ac881bcf17d997f0cad7d9a9a621"):
    """判断消息是否与用户相关"""

    # 1. 如果是用户自己发的消息
    sender = msg.get('sender', {})
    sender_id = sender.get('id', '')
    sender_name = sender.get('name', '')

    if sender_id == user_id or sender_name == user_name:
        return True

    # 2. 检查消息内容是否@了用户
    content = msg.get('content', '')

    at_patterns = [
        f"@{user_name}",
        f"@易希倩",
        f"@Queenie Yi",
        f"@Queenie",
        user_id,
    ]

    for pattern in at_patterns:
        if pattern in content:
            return True

    # 3. 私聊消息都相关
    chat_type = msg.get('chat_type', '')
    if chat_type == 'p2p':
        return True

    return False


def filter_relevant_messages(messages):
    """过滤相关消息"""
    relevant = []
    filtered_count = 0

    for msg in messages:
        if is_message_relevant(msg):
            relevant.append(msg)
        else:
            filtered_count += 1

    print(f"   ✓ 过滤掉 {filtered_count} 条无关消息")
    print(f"   ✓ 保留 {len(relevant)} 条相关消息")

    return relevant


def categorize_messages(messages):
    """按群聊分类"""
    categorized = defaultdict(list)

    for msg in messages:
        chat_name = msg.get('chat_name', '未知群聊')
        chat_type = msg.get('chat_type', 'unknown')

        simplified_msg = {
            'time': msg.get('create_time', ''),
            'sender': msg.get('sender', {}).get('name', '未知'),
            'content': msg.get('content', '')[:200],
            'msg_type': msg.get('msg_type', 'text'),
            'is_self': msg.get('sender', {}).get('name', '') == '易希倩 Queenie Yi'
        }

        key = f"{chat_type}:{chat_name}"
        categorized[key].append(simplified_msg)

    return categorized


def analyze_messages_simple(messages):
    """简单分析"""
    if not messages:
        return {
            'total_count': 0,
            'summary': '昨天没有相关消息'
        }

    categorized = categorize_messages(messages)

    total_chats = len(categorized)
    total_messages = len(messages)

    chat_stats = []
    for chat_key, msgs in sorted(categorized.items(), key=lambda x: len(x[1]), reverse=True):
        chat_type, chat_name = chat_key.split(':', 1)
        chat_stats.append({
            'name': chat_name,
            'type': chat_type,
            'count': len(msgs),
            'messages': msgs[:10]
        })

    return {
        'total_count': total_messages,
        'total_chats': total_chats,
        'chat_stats': chat_stats,
        'summary': f'共 {total_chats} 个会话，{total_messages} 条相关消息'
    }


def generate_summary_text(analysis):
    """生成汇总文本"""
    summary = f"""
📊 **每日工作汇总 - {(datetime.now() - timedelta(days=1)).strftime('%Y年%m月%d日')}**

## 📈 总体统计

- 相关消息：{analysis['total_count']} 条
- 涉及会话：{analysis['total_chats']} 个

💡 *仅统计@了你或你参与的消息*

## 💬 主要会话

"""

    for idx, chat in enumerate(analysis['chat_stats'][:10], 1):
        chat_type_emoji = "👥" if chat['type'] == 'group' else "💬"
        summary += f"{idx}. {chat_type_emoji} **{chat['name']}** - {chat['count']} 条消息\n"

    summary += "\n---\n💡 *由 GitHub Actions 自动生成*"

    return summary


def send_to_lark(summary_text):
    """发送到飞书"""
    user_id = os.environ.get('LARK_USER_ID')
    tenant_token = get_tenant_access_token()

    if not all([user_id, tenant_token]):
        print("❌ 缺少配置")
        return False

    url = "https://open.feishu.cn/open-apis/im/v1/messages"

    headers = {
        "Authorization": f"Bearer {tenant_token}",
        "Content-Type": "application/json"
    }

    params = {"receive_id_type": "open_id"}

    payload = {
        "receive_id": user_id,
        "msg_type": "text",
        "content": json.dumps({"text": summary_text})
    }

    try:
        response = requests.post(url, headers=headers, params=params, json=payload, timeout=10)
        result = response.json()

        if result.get('code') == 0:
            print("✅ 消息发送成功")
            return True
        else:
            print(f"❌ 发送失败: {result}")
            return False

    except Exception as e:
        print(f"❌ 发送失败: {str(e)}")
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("🚀 开始执行每日工作汇总任务 (GitHub Actions)")
    print(f"⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    try:
        # 1. 获取消息
        print("\n📥 步骤 1/5: 获取昨天的消息...")
        messages = get_yesterday_messages()

        if not messages:
            print("⚠️  没有获取到消息")
            send_to_lark("📊 昨天没有消息记录")
            return

        # 2. 过滤相关消息
        print("\n🔍 步骤 2/5: 过滤与你相关的消息...")
        relevant_messages = filter_relevant_messages(messages)

        if not relevant_messages:
            print("⚠️  没有相关消息")
            send_to_lark("📊 昨天没有与你相关的消息")
            return

        # 3. 分析消息
        print("\n🔍 步骤 3/5: 分析消息...")
        analysis = analyze_messages_simple(relevant_messages)
        print("   ✓ 分析完成")

        # 4. 生成汇总
        print("\n📝 步骤 4/5: 生成汇总报告...")
        summary_text = generate_summary_text(analysis)
        print("   ✓ 报告生成完成")

        # 5. 发送到飞书
        print("\n📤 步骤 5/5: 发送到飞书...")
        send_to_lark(summary_text)

        # 保存到本地
        output_file = f"summary_{datetime.now().strftime('%Y%m%d')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, ensure_ascii=False, indent=2)
        print(f"   ✓ 详细数据已保存: {output_file}")

        print("\n" + "=" * 60)
        print("✅ 任务执行完成！")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 执行失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
