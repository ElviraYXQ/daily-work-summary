#!/usr/bin/env python3
"""
522大促进线内容全量分析
基于实际消息内容进行分类统计
"""
import pandas as pd
import requests
import json
import time
from collections import defaultdict

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

def classify_promotion_conversation(content):
    """
    基于消息内容分类大促相关进线
    返回: (是否大促相关, 分类列表)
    """
    if not content:
        return False, []

    content_lower = content.lower()
    categories = []

    # 1. "免费活动"相关（每小时抽奖免单）
    free_keywords = ['free sale', 'free day', 'free order', 'free cloth', '0 rs', '免费']
    if any(kw in content_lower for kw in free_keywords):
        categories.append('免费活动咨询/投诉')

    # 2. 活动期间技术问题
    tech_keywords = ['crash', 'network unavailable', 'app crash', 'not working', 'error', '崩溃', '卡', 'lag']
    if any(kw in content_lower for kw in tech_keywords):
        categories.append('技术问题-App崩溃/卡顿')

    # 3. 活动规则咨询
    rule_keywords = ['how to', 'terms', 'conditions', 'rules', 'anniversary sale', 'wallet', '规则', '怎么']
    if any(kw in content_lower for kw in rule_keywords):
        if '免费活动咨询/投诉' not in categories:  # 避免重复
            categories.append('活动规则咨询')

    # 4. 订单取消/修改
    cancel_keywords = ['cancel', 'cancel my order', '取消']
    if any(kw in content_lower for kw in cancel_keywords):
        categories.append('订单取消/修改')

    # 5. 价格/折扣咨询
    price_keywords = ['price', 'discount', 'offer', 'deal', '价格', '折扣', '优惠']
    # 检查是否包含订单卡片（JSON格式）
    has_order_card = '"cardType":"order"' in content or '"cardType":"goods"' in content
    if any(kw in content_lower for kw in price_keywords) or (has_order_card and 'showPromotePrice' in content):
        if len(categories) == 0:  # 如果还没有其他分类，再加这个
            categories.append('价格/折扣咨询')

    # 6. 配送问题
    delivery_keywords = ['delivery', 'shipping', 'dispatch', 'transit', '配送', '物流', '发货']
    if any(kw in content_lower for kw in delivery_keywords):
        categories.append('配送问题')

    # 7. 退款/退货问题
    refund_keywords = ['refund', 'return', 'exchange', '退款', '退货']
    if any(kw in content_lower for kw in refund_keywords):
        categories.append('退款/退货')

    # 8. 正面反馈
    positive_keywords = ['thank', 'good', 'nice', 'love', 'amazing', 'great', '⭐']
    if any(kw in content_lower for kw in positive_keywords):
        if len(categories) == 0:
            categories.append('正面反馈')

    # 判断是否大促相关
    is_promotion = len(categories) > 0

    # 如果没有明确分类，但包含一些通用大促关键词，标记为"其他大促相关"
    if not is_promotion:
        general_keywords = ['sale', '522', '5.22', 'promotion', 'activity', '活动']
        if any(kw in content_lower for kw in general_keywords):
            is_promotion = True
            categories.append('其他大促相关')

    return is_promotion, categories

def analyze_all_conversations_fast(csv_path):
    """
    快速全量分析（不调用API，基于现有数据）
    """
    print("正在加载CSV数据...")
    df = pd.read_csv(csv_path)

    print(f"✅ 加载完成: {len(df)} 条会话\n")

    # 解析custom_attributes获取AI标签
    def parse_attrs(attr_str):
        try:
            if pd.isna(attr_str):
                return {}
            return json.loads(attr_str)
        except:
            return {}

    df['attrs'] = df['custom_attributes'].apply(parse_attrs)
    df['ai_labels'] = df['attrs'].apply(lambda x: x.get('ub_ai_label_list', ''))
    df['biz_name'] = df['attrs'].apply(lambda x: x.get('ub_biz_name', ''))
    df['hour'] = pd.to_datetime(df['created_at']).dt.hour

    # 基于AI标签进行快速分类
    print("正在基于AI标签进行分类...")

    results = []
    for idx, row in df.iterrows():
        ai_labels = str(row['ai_labels']).lower()
        biz_name = str(row['biz_name']).lower()

        categories = []
        is_promotion = False

        # 基于AI标签分类
        if 'pricing' in ai_labels or 'promotion' in ai_labels or 'discount' in ai_labels:
            is_promotion = True

            if 'coupon' in ai_labels or 'voucher' in ai_labels:
                categories.append('优惠券相关')

            if 'discount' in ai_labels or 'offer' in ai_labels:
                categories.append('价格/折扣咨询')

            if 'free_item' in ai_labels:
                categories.append('免费活动咨询/投诉')

        if 'order_cancellation' in ai_labels or 'cancel' in ai_labels:
            is_promotion = True
            categories.append('订单取消/修改')

        if 'delivery' in ai_labels or 'shipping' in ai_labels:
            is_promotion = True
            categories.append('配送问题')

        if 'refund' in ai_labels or 'return' in ai_labels:
            is_promotion = True
            categories.append('退款/退货')

        if 'positive_feedback' in ai_labels:
            is_promotion = True
            categories.append('正面反馈')

        if 'app' in ai_labels and 'issue' in ai_labels:
            is_promotion = True
            categories.append('技术问题-App崩溃/卡顿')

        if not categories and is_promotion:
            categories.append('其他大促相关')

        results.append({
            'conversation_id': row['id'],
            'created_at': row['created_at'],
            'hour': row['hour'],
            'inbox_id': row['inbox_id'],
            'is_promotion': is_promotion,
            'categories': categories,
            'category_count': len(categories)
        })

        if (idx + 1) % 1000 == 0:
            print(f"  已处理: {idx + 1} / {len(df)}")

    results_df = pd.DataFrame(results)

    print(f"\n✅ 分类完成！")

    return df, results_df

def generate_final_report(df, results_df):
    """生成最终统计报告"""
    print("\n" + "=" * 100)
    print("📊 522大促进线内容统计报告（基于AI标签分类）")
    print("=" * 100)

    # 1. 总体统计
    total_conv = len(results_df)
    promotion_conv = results_df['is_promotion'].sum()

    print(f"\n【总体概况】")
    print(f"  • 总会话数: {total_conv:,}")
    print(f"  • 大促相关会话: {promotion_conv:,} ({promotion_conv/total_conv*100:.2f}%)")
    print(f"  • 非大促会话: {total_conv - promotion_conv:,} ({(total_conv - promotion_conv)/total_conv*100:.2f}%)")

    # 2. 按小时分布
    print(f"\n" + "=" * 100)
    print("⏰ 大促进线按小时分布")
    print("=" * 100)

    promo_df = results_df[results_df['is_promotion']]
    hourly_dist = promo_df.groupby('hour').size()
    hourly_total = results_df.groupby('hour').size()

    print(f"\n{'小时':<10} {'大促进线':<15} {'总进线':<15} {'占比':<10}")
    print("-" * 50)
    for hour in sorted(hourly_dist.index):
        promo_count = hourly_dist.get(hour, 0)
        total_count = hourly_total.get(hour, 0)
        pct = promo_count / total_count * 100 if total_count > 0 else 0
        print(f"{hour:02d}:00     {promo_count:>6,}         {total_count:>6,}         {pct:>5.1f}%")

    # 3. 按渠道分布
    print(f"\n" + "=" * 100)
    print("📱 大促进线按渠道分布")
    print("=" * 100)

    merged_df = promo_df.merge(df[['id', 'inbox_id']], left_on='conversation_id', right_on='id', how='left')

    inbox_map = {
        2: "APP内客服",
        4: "Instagram DM",
        11: "WhatsApp",
        14: "Facebook Messenger",
    }

    channel_dist = merged_df['inbox_id_y'].value_counts()
    print(f"\n{'渠道':<20} {'进线数':<10} {'占比':<10}")
    print("-" * 40)
    for inbox_id, count in channel_dist.head(10).items():
        channel_name = inbox_map.get(int(inbox_id), f"渠道{inbox_id}")
        pct = count / len(promo_df) * 100
        print(f"{channel_name:<20} {count:>6,}     {pct:>5.1f}%")

    # 4. 按类型分类统计
    print(f"\n" + "=" * 100)
    print("🏷️  大促进线按类型分布（Top 20）")
    print("=" * 100)

    all_categories = []
    for cats in promo_df['categories']:
        if cats:
            all_categories.extend(cats)

    if all_categories:
        category_counts = pd.Series(all_categories).value_counts()

        print(f"\n{'排名':<5} {'类型':<30} {'进线数':<10} {'占比':<10}")
        print("-" * 60)
        for rank, (cat, count) in enumerate(category_counts.head(20).items(), 1):
            pct = count / promotion_conv * 100
            print(f"{rank:<5} {cat:<30} {count:>6,}     {pct:>5.1f}%")

    # 5. 详细交叉分析
    print(f"\n" + "=" * 100)
    print("📊 详细统计：小时 × 类型")
    print("=" * 100)

    # 展开categories
    expanded = []
    for _, row in promo_df.iterrows():
        for cat in row['categories']:
            expanded.append({
                'hour': row['hour'],
                'category': cat,
                'conversation_id': row['conversation_id']
            })

    expanded_df = pd.DataFrame(expanded)

    if len(expanded_df) > 0:
        for hour in sorted(expanded_df['hour'].unique()):
            hour_data = expanded_df[expanded_df['hour'] == hour]
            cat_counts = hour_data['category'].value_counts()

            print(f"\n【{hour:02d}:00 - {hour:02d}:59】 (共 {len(hour_data)} 条)")
            for cat, count in cat_counts.head(10).items():
                pct = count / len(hour_data) * 100
                print(f"  {cat:<30} {count:>4} ({pct:>5.1f}%)")

    return {
        'total': total_conv,
        'promotion': promotion_conv,
        'category_counts': category_counts if all_categories else None
    }

def export_results(df, results_df, output_path):
    """导出结果到Excel"""
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        # Sheet 1: 所有会话分类结果
        results_df.to_excel(writer, sheet_name='分类结果', index=False)

        # Sheet 2: 大促相关会话
        promo_df = results_df[results_df['is_promotion']]
        promo_df.to_excel(writer, sheet_name='大促相关', index=False)

        # Sheet 3: 按小时汇总
        hourly_summary = promo_df.groupby('hour').size().reset_index(name='count')
        hourly_summary.to_excel(writer, sheet_name='按小时汇总', index=False)

        # Sheet 4: 按类型汇总
        all_cats = []
        for cats in promo_df['categories']:
            all_cats.extend(cats)
        if all_cats:
            cat_summary = pd.Series(all_cats).value_counts().reset_index()
            cat_summary.columns = ['类型', '数量']
            cat_summary.to_excel(writer, sheet_name='按类型汇总', index=False)

    print(f"\n✅ 结果已导出到: {output_path}")

def main():
    csv_path = '/Users/yixiqian/Downloads/2026-05-22-15-50-17_EXPORT_CSV_25669721_668_0.csv'

    print("\n" + "🎯 " * 30)
    print("522大促进线内容全量分析")
    print("🎯 " * 30 + "\n")

    # 分析
    df, results_df = analyze_all_conversations_fast(csv_path)

    # 生成报告
    stats = generate_final_report(df, results_df)

    # 导出
    output_path = '/Users/yixiqian/daily-work-summary/promotion_522_analysis_final.xlsx'
    export_results(df, results_df, output_path)

    print("\n" + "=" * 100)
    print("✅ 分析完成！")
    print("=" * 100)
    print(f"\n关键数据:")
    print(f"  • 大促相关会话: {stats['promotion']:,} / {stats['total']:,}")
    print(f"  • 占比: {stats['promotion']/stats['total']*100:.2f}%")

    if stats['category_counts'] is not None:
        print(f"\nTop 5 问题类型:")
        for idx, (cat, count) in enumerate(stats['category_counts'].head(5).items(), 1):
            print(f"  {idx}. {cat}: {count:,}")

if __name__ == "__main__":
    main()
