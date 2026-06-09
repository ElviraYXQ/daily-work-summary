#!/usr/bin/env python3
"""
基于实际消息内容分析522大促相关进线
第一步：抽样获取消息内容并分析
"""
import pandas as pd
import requests
import json
import time
from datetime import datetime

# Chatwoot API配置
CHATWOOT_BASE_URL = "https://aichat-in.urbanic-cs.com"
ACCOUNT_ID = "2"
API_TOKEN = "KcgCQYz9fcCEzSwkBRc5uQnh"

def get_conversation_messages(conv_id):
    """获取会话的所有消息"""
    url = f"{CHATWOOT_BASE_URL}/api/v1/accounts/{ACCOUNT_ID}/conversations/{conv_id}/messages"
    headers = {
        "api_access_token": API_TOKEN
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"  ⚠️  会话{conv_id}获取失败: HTTP {response.status_code}")
            return None
    except Exception as e:
        print(f"  ❌ 会话{conv_id}请求异常: {str(e)}")
        return None

def extract_user_messages(response):
    """提取用户发送的消息内容"""
    if not response:
        return []

    # API返回格式: {meta: {}, payload: [消息数组]}
    messages = response.get('payload', []) if isinstance(response, dict) else []

    user_messages = []
    for msg in messages:
        # message_type=0 表示用户发送的消息
        if msg.get('message_type') == 0:
            content = msg.get('content') or ''
            content = content.strip() if isinstance(content, str) else ''
            if content:
                user_messages.append({
                    'content': content,
                    'created_at': msg.get('created_at'),
                    'sender_type': msg.get('sender', {}).get('type') if msg.get('sender') else None
                })

    return user_messages

def sample_and_fetch_messages(csv_path, sample_size=100):
    """抽样并获取消息内容"""
    print(f"正在加载数据...")
    df = pd.read_csv(csv_path)

    print(f"✅ 数据加载完成: {len(df)} 条会话\n")

    # 按小时分层抽样，确保覆盖不同时段
    df['hour'] = pd.to_datetime(df['created_at']).dt.hour

    # 从每个小时抽样
    sample_per_hour = max(1, sample_size // df['hour'].nunique())
    sampled = df.groupby('hour').apply(
        lambda x: x.sample(min(sample_per_hour, len(x)), random_state=42)
    ).reset_index(drop=True)

    # 如果不够sample_size，再随机补充
    if len(sampled) < sample_size:
        remaining = sample_size - len(sampled)
        additional = df[~df['id'].isin(sampled['id'])].sample(
            min(remaining, len(df) - len(sampled)),
            random_state=42
        )
        sampled = pd.concat([sampled, additional]).reset_index(drop=True)

    print("=" * 100)
    print(f"📊 抽样结果: {len(sampled)} 条会话")
    print("=" * 100)
    print(f"时间分布:")
    for hour, count in sampled['hour'].value_counts().sort_index().items():
        print(f"  {hour:02d}:00 - {count} 条")

    print(f"\n正在获取消息内容...")
    print("=" * 100)

    results = []

    for idx, row in sampled.iterrows():
        conv_id = row['id']
        print(f"\n[{idx+1}/{len(sampled)}] 获取会话 {conv_id}...", end='')

        messages = get_conversation_messages(conv_id)
        user_messages = extract_user_messages(messages)

        # 合并所有用户消息
        full_content = '\n'.join([msg['content'] for msg in user_messages])

        results.append({
            'conversation_id': conv_id,
            'created_at': row['created_at'],
            'hour': row['hour'],
            'inbox_id': row['inbox_id'],
            'status': row['status'],
            'user_messages_count': len(user_messages),
            'full_content': full_content,
            'first_message': user_messages[0]['content'] if user_messages else '',
            'raw_messages': user_messages
        })

        print(f" ✅ {len(user_messages)} 条用户消息")

        # 避免请求过快
        time.sleep(0.2)

    results_df = pd.DataFrame(results)

    print("\n" + "=" * 100)
    print("✅ 消息获取完成！")
    print("=" * 100)
    print(f"总会话数: {len(results_df)}")
    print(f"有用户消息的会话: {(results_df['user_messages_count'] > 0).sum()}")
    print(f"空会话: {(results_df['user_messages_count'] == 0).sum()}")

    return results_df

def analyze_promotion_content(results_df):
    """分析消息内容，识别大促相关"""
    print("\n" + "=" * 100)
    print("🔍 分析消息内容，识别522大促相关会话")
    print("=" * 100 + "\n")

    # 大促相关关键词（更全面）
    promotion_keywords = {
        '活动相关': ['522', '5.22', '5月22', '大促', '活动', 'sale', 'mega sale', 'flash sale'],
        '优惠券': ['优惠券', 'coupon', 'voucher', '券', 'promo code'],
        '折扣': ['折扣', 'discount', '打折', 'off', '减价', '降价', '便宜'],
        '满减': ['满减', '满', '凑单', 'minimum', 'free shipping', '包邮'],
        '赠品': ['赠品', '送', 'free gift', 'gift', 'freebie'],
        '价格': ['价格', 'price', '多少钱', 'how much', 'cost'],
        '优惠': ['优惠', 'offer', 'deal', 'promotion', 'special'],
    }

    def check_promotion_keywords(text):
        """检查文本是否包含大促关键词"""
        if pd.isna(text) or not text:
            return False, []

        text_lower = text.lower()
        matched_categories = []

        for category, keywords in promotion_keywords.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    matched_categories.append(category)
                    break

        return len(matched_categories) > 0, matched_categories

    # 分析每条会话
    results = []
    for idx, row in results_df.iterrows():
        is_promotion, categories = check_promotion_keywords(row['full_content'])
        results.append({
            'is_promotion': is_promotion,
            'matched_categories': categories,
            'keyword_count': len(categories)
        })

    analysis_df = pd.DataFrame(results)
    results_df = pd.concat([results_df, analysis_df], axis=1)

    # 统计
    promotion_count = results_df['is_promotion'].sum()

    print(f"📊 识别结果:")
    print(f"  大促相关会话: {promotion_count} / {len(results_df)} ({promotion_count/len(results_df)*100:.2f}%)")
    print(f"  非大促会话: {len(results_df) - promotion_count}")

    # 分类统计
    print(f"\n📋 大促关键词类别分布:")
    all_categories = []
    for cats in results_df[results_df['is_promotion']]['matched_categories']:
        all_categories.extend(cats)

    if all_categories:
        category_counts = pd.Series(all_categories).value_counts()
        for cat, count in category_counts.items():
            print(f"  {cat}: {count} 次")

    return results_df

def display_sample_messages(results_df, promotion_only=True, n=20):
    """展示样本消息"""
    print("\n" + "=" * 100)
    if promotion_only:
        print(f"💬 展示大促相关会话样本（前{n}条）")
        display_df = results_df[results_df['is_promotion']].head(n)
    else:
        print(f"💬 展示所有会话样本（前{n}条）")
        display_df = results_df.head(n)
    print("=" * 100 + "\n")

    for idx, row in display_df.iterrows():
        print(f"【会话 {row['conversation_id']}】")
        print(f"  时间: {row['created_at']}")
        print(f"  用户消息数: {row['user_messages_count']}")
        if row['is_promotion']:
            print(f"  ✅ 大促相关 - 匹配类别: {', '.join(row['matched_categories'])}")
        else:
            print(f"  ❌ 非大促相关")

        print(f"\n  【用户消息内容】")
        if row['full_content']:
            # 只显示前500字符
            content_preview = row['full_content'][:500]
            if len(row['full_content']) > 500:
                content_preview += "..."
            print(f"  {content_preview}")
        else:
            print(f"  (无用户消息)")
        print("\n" + "-" * 100 + "\n")

def main():
    csv_path = '/Users/yixiqian/Downloads/2026-05-22-15-50-17_EXPORT_CSV_25669721_668_0.csv'

    print("\n" + "🎯 " * 30)
    print("522大促相关进线分析 - 基于实际消息内容")
    print("🎯 " * 30 + "\n")

    # 1. 抽样获取消息
    results_df = sample_and_fetch_messages(csv_path, sample_size=100)

    # 保存原始消息数据
    results_df.to_csv(
        '/Users/yixiqian/daily-work-summary/sampled_conversations_with_messages.csv',
        index=False
    )
    print(f"\n✅ 原始消息数据已保存")

    # 2. 分析大促相关
    results_df = analyze_promotion_content(results_df)

    # 3. 展示样本
    display_sample_messages(results_df, promotion_only=True, n=20)

    # 4. 保存分析结果
    results_df.to_csv(
        '/Users/yixiqian/daily-work-summary/analyzed_conversations.csv',
        index=False
    )
    print(f"✅ 分析结果已保存到: analyzed_conversations.csv")

    print("\n" + "=" * 100)
    print("⏭️  下一步")
    print("=" * 100 + "\n")
    print("1. 请review上面展示的消息样本")
    print("2. 确认哪些算大促相关，哪些不算")
    print("3. 确认分类方案（我会根据实际内容重新设计）")
    print("4. 确认后，我将对全量14,777条会话进行分析\n")

if __name__ == "__main__":
    main()
