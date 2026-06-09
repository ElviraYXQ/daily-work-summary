#!/usr/bin/env python3
"""
基于会话原始内容进行大促分析
三层分类 + 细分类型
"""
import pandas as pd
import requests
import json
import time
import random

# Chatwoot API配置
CHATWOOT_BASE_URL = "https://aichat-in.urbanic-cs.com"
ACCOUNT_ID = "2"
API_TOKEN = "KcgCQYz9fcCEzSwkBRc5uQnh"

def get_conversation_messages(conv_id):
    """获取会话消息"""
    url = f"{CHATWOOT_BASE_URL}/api/v1/accounts/{ACCOUNT_ID}/conversations/{conv_id}/messages"
    headers = {"api_access_token": API_TOKEN}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def extract_user_messages(response):
    """提取用户消息"""
    if not response:
        return []

    messages = response.get('payload', []) if isinstance(response, dict) else []
    user_messages = []

    for msg in messages:
        if msg.get('message_type') == 0:
            content = msg.get('content') or ''
            content = content.strip() if isinstance(content, str) else ''
            if content:
                user_messages.append(content)

    return user_messages

def classify_by_content(content):
    """
    基于内容进行三层分类
    返回: (层级, 细分类型列表)

    层级:
    1 - 高置信度大促相关
    2 - 不确定
    3 - 高置信度非大促
    """
    if not content:
        return 2, ['无消息内容']

    import re

    # 移除JSON卡片，只分析用户文字消息
    content_text = re.sub(r'\{"cardType".*?\}', '', content, flags=re.DOTALL)
    content_text = '\n'.join([line.strip() for line in content_text.split('\n') if line.strip()])

    # 如果移除JSON后没有文字内容
    if not content_text or len(content_text) < 3:
        if '"cardType":"order"' in content or '"cardType":"goods"' in content:
            return 2, ['发送订单卡片-无文字说明']
        return 2, ['无消息内容']

    content_lower = content_text.lower()

    # === 第一层：高置信度大促相关 ===
    # 只包含明确与大促直接相关的咨询/投诉

    categories_level1 = []

    # 1. 免费活动咨询/投诉
    free_keywords = ['free sale', 'free day', 'free order', 'free cloth', 'free item', 'get free']
    free_simple = ['free', '免费']

    has_free = any(kw in content_lower for kw in free_keywords)
    if not has_free:
        # 检查简单的"free"，但需要结合上下文
        if any(kw in content_lower for kw in free_simple):
            # 必须同时提到order/sale/item等，且在询问/投诉免费相关
            if any(word in content_lower for word in ['order', 'sale', 'when', 'how', 'get', 'milne', 'kaise']):
                has_free = True

    if has_free:
        categories_level1.append('免费活动咨询/投诉')

    # 2. 优惠券相关
    coupon_keywords = ['coupon', 'voucher', 'promo code', '优惠券']
    if any(kw in content_lower for kw in coupon_keywords):
        categories_level1.append('优惠券相关')

    # 3. 价格/折扣咨询
    price_keywords = ['discount', 'offer', 'deal', 'promotion', '折扣', '优惠']
    if any(kw in content_lower for kw in price_keywords):
        # 排除已经归类为优惠券的
        if '优惠券相关' not in categories_level1:
            categories_level1.append('价格/折扣咨询')

    # 4. 技术问题-App崩溃/卡顿（大促期间特有）
    tech_issues = ['crash', 'not working', 'error', 'network unavailable', 'app crash', 'lag', 'freeze']
    tech_context = ['sale', 'order', 'app', 'server', 'cart', 'payment']

    if any(kw in content_lower for kw in tech_issues):
        # 必须同时提到sale/order等大促相关背景
        if any(ctx in content_lower for ctx in tech_context):
            categories_level1.append('技术问题-App崩溃/卡顿')

    # 5. 其他明确大促相关
    explicit_promo = ['522', '5.22', 'mega sale', 'flash sale', 'anniversary sale', 'anniversary', '周年庆']
    if any(kw in content_lower for kw in explicit_promo):
        # 如果还没有其他分类，归为"其他大促相关"
        if not categories_level1:
            categories_level1.append('其他大促相关')

    # 如果有第1层分类，返回
    if categories_level1:
        return 1, categories_level1

    # === 第三层：高置信度非大促 ===

    categories_level3 = []

    # 1. 明确的非大促问题（问候/寒暄）
    non_promo = [
        'hello', 'hi', 'hey', 'good morning', 'thank you',
        'how are you', 'what is this', 'who are you',
        '你好', '谢谢'
    ]

    # 检查问候（内容很短且只是简单问候）
    if any(kw in content_lower for kw in non_promo):
        if len(content_text) < 50:
            categories_level3.append('问候/寒暄')

    # 2. 账户/会员相关（日常）
    account_keywords = ['password', 'login', 'account', 'email', 'phone number', '账户', '密码']
    if any(kw in content_lower for kw in account_keywords):
        categories_level3.append('账户问题')

    # 3. 商品咨询（非价格）
    product_keywords = ['size', 'material', 'fabric', 'color', 'measurement', '尺码', '材质', '颜色']
    price_keywords = ['price', 'discount', 'offer', 'deal', '价格', '折扣', 'coupon', 'voucher']

    if any(kw in content_lower for kw in product_keywords):
        # 确保不包含价格相关
        if not any(kw in content_lower for kw in price_keywords):
            categories_level3.append('商品咨询')

    # 如果有第三层标签，返回
    if categories_level3:
        return 3, categories_level3

    # === 第二层：不确定 ===

    categories_level2 = []

    # 订单相关（无法判断是否因大促）
    if 'cancel' in content_lower:
        categories_level2.append('订单取消-原因不明')

    if any(kw in content_lower for kw in ['delivery', 'shipping', 'dispatch', 'tracking', '配送', '物流']):
        categories_level2.append('配送查询-原因不明')

    if any(kw in content_lower for kw in ['refund', 'return', 'exchange', '退款', '退货']):
        categories_level2.append('退款退货-原因不明')

    # 其他不确定
    if not categories_level2:
        categories_level2.append('其他不确定')

    return 2, categories_level2

def analyze_sample(csv_path, sample_size=1000):
    """抽样分析"""
    print("正在加载数据...")
    df = pd.read_csv(csv_path)

    # 按小时分层抽样
    df['hour'] = pd.to_datetime(df['created_at']).dt.hour

    # 只抽样04:00-05:00（AI标签覆盖率高）
    df_reliable = df[df['hour'].isin([4, 5])]

    # 随机抽样
    sample_df = df_reliable.sample(min(sample_size, len(df_reliable)), random_state=42)

    print(f"✅ 抽样完成: {len(sample_df)} 条会话")
    print(f"时间范围: 04:00-05:00")
    print(f"\n开始获取消息内容...\n")

    results = []

    for idx, row in sample_df.iterrows():
        conv_id = row['id']
        print(f"[{len(results)+1}/{len(sample_df)}] 会话 {conv_id}...", end='')

        # 获取消息
        response = get_conversation_messages(conv_id)
        user_messages = extract_user_messages(response)

        # 合并消息
        full_content = '\n'.join(user_messages)

        # 分类
        level, categories = classify_by_content(full_content)

        results.append({
            'conversation_id': conv_id,
            'hour': row['hour'],
            'created_at': row['created_at'],
            'user_message_count': len(user_messages),
            'content_preview': full_content[:200] if full_content else '',
            'level': level,
            'categories': categories,
            'full_content': full_content
        })

        print(f" 层级{level}, {len(categories)}个标签")

        time.sleep(0.2)

    results_df = pd.DataFrame(results)

    return results_df

def generate_text_report(results_df):
    """生成文本报告"""
    print("\n" + "=" * 100)
    print("📊 基于会话内容的分类结果")
    print("=" * 100)

    # 总体统计
    total = len(results_df)
    level1 = len(results_df[results_df['level'] == 1])
    level2 = len(results_df[results_df['level'] == 2])
    level3 = len(results_df[results_df['level'] == 3])

    print(f"\n【总体分布】")
    print(f"  样本总数: {total}")
    print(f"  ├─ 第1层（高置信度大促相关）: {level1} ({level1/total*100:.1f}%)")
    print(f"  ├─ 第2层（不确定）: {level2} ({level2/total*100:.1f}%)")
    print(f"  └─ 第3层（高置信度非大促）: {level3} ({level3/total*100:.1f}%)")

    # 第1层详细
    print(f"\n" + "=" * 100)
    print(f"第1层：高置信度大促相关（{level1}条）")
    print("=" * 100)

    level1_df = results_df[results_df['level'] == 1]
    if len(level1_df) > 0:
        all_cats = []
        for cats in level1_df['categories']:
            all_cats.extend(cats)

        cat_counts = pd.Series(all_cats).value_counts()
        print(f"\n细分类型分布:")
        for cat, count in cat_counts.items():
            print(f"  {count:4d} ({count/level1*100:5.1f}%) | {cat}")

    # 第2层详细
    print(f"\n" + "=" * 100)
    print(f"第2层：不确定（{level2}条）")
    print("=" * 100)

    level2_df = results_df[results_df['level'] == 2]
    if len(level2_df) > 0:
        all_cats = []
        for cats in level2_df['categories']:
            all_cats.extend(cats)

        cat_counts = pd.Series(all_cats).value_counts()
        print(f"\n细分类型分布:")
        for cat, count in cat_counts.items():
            print(f"  {count:4d} ({count/level2*100:5.1f}%) | {cat}")

    # 第3层详细
    print(f"\n" + "=" * 100)
    print(f"第3层：高置信度非大促（{level3}条）")
    print("=" * 100)

    level3_df = results_df[results_df['level'] == 3]
    if len(level3_df) > 0:
        all_cats = []
        for cats in level3_df['categories']:
            all_cats.extend(cats)

        cat_counts = pd.Series(all_cats).value_counts()
        print(f"\n细分类型分布:")
        for cat, count in cat_counts.items():
            print(f"  {count:4d} ({count/level3*100:5.1f}%) | {cat}")

    # 展示样本
    print(f"\n" + "=" * 100)
    print("样本展示（每层前5条）")
    print("=" * 100)

    for level in [1, 2, 3]:
        level_name = {1: "高置信度大促相关", 2: "不确定", 3: "高置信度非大促"}[level]
        print(f"\n【第{level}层：{level_name}】")

        level_df = results_df[results_df['level'] == level]
        for idx, row in level_df.head(5).iterrows():
            print(f"\n  会话{row['conversation_id']} | {row['hour']:02d}:00 | 分类: {', '.join(row['categories'])}")
            preview = row['content_preview'][:150]
            if len(row['content_preview']) > 150:
                preview += "..."
            print(f"  内容: {preview}")

def main():
    csv_path = '/Users/yixiqian/Downloads/2026-05-22-15-50-17_EXPORT_CSV_25669721_668_0.csv'

    print("\n" + "🎯 " * 30)
    print("基于会话原始内容的大促分析")
    print("🎯 " * 30 + "\n")

    # 抽样分析
    results_df = analyze_sample(csv_path, sample_size=1000)

    # 保存结果
    results_df.to_csv(
        '/Users/yixiqian/daily-work-summary/content_based_analysis_sample.csv',
        index=False
    )

    # 生成报告
    generate_text_report(results_df)

    print("\n✅ 抽样分析完成！")
    print(f"结果已保存到: content_based_analysis_sample.csv")

if __name__ == "__main__":
    main()
