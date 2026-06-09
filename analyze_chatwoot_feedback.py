#!/usr/bin/env python3
"""
Chatwoot客服进线内容分析
按小时、渠道统计用户反馈情况
"""
import pandas as pd
import json
from datetime import datetime
from collections import defaultdict

def parse_custom_attributes(attr_str):
    """解析custom_attributes JSON字符串"""
    try:
        if pd.isna(attr_str):
            return {}
        return json.loads(attr_str)
    except:
        return {}

def get_inbox_name(inbox_id):
    """映射inbox_id到渠道名称"""
    inbox_map = {
        2: "APP内客服",
        4: "Instagram DM",
        11: "WhatsApp",
        14: "Facebook Messenger",
        1: "网页客服",
        3: "Twitter DM",
        34: "其他渠道"
    }
    return inbox_map.get(int(inbox_id), f"渠道{inbox_id}")

def parse_ai_labels(label_str):
    """解析AI标签并提取用户反馈类型"""
    if not label_str or label_str == 'N/A':
        return ['未分类']

    # 标签通常是 category-subcategory-detail 格式
    labels = [l.strip() for l in str(label_str).split(',')]

    # 提取主要类别
    feedback_types = []
    for label in labels:
        parts = label.split('-')
        if len(parts) >= 2:
            # 使用更易读的中文描述
            category = parts[0]
            subcategory = parts[1] if len(parts) > 1 else ''

            # 映射到中文描述
            feedback_type = map_feedback_type(category, subcategory, label)
            feedback_types.append(feedback_type)

    return feedback_types if feedback_types else ['未分类']

def map_feedback_type(category, subcategory, full_label):
    """映射反馈类型到中文描述"""
    mapping = {
        'delivery_related': {
            'delivery_timeline_status': '配送时效问题',
            'delivery_exception': '配送异常',
            'order_cancellation_request': '订单取消请求',
            'delivery_delayed': '配送延迟',
            'delivery_still_within': '配送查询（正常）',
            'default': '配送相关'
        },
        'return_related': {
            'return_pickup_status': '退货取件问题',
            'return_guidance_eligibility': '退货规则咨询',
            'return_plan_change': '退货计划变更',
            'return_window_closed': '超过退货期限',
            'picked-up_return': '已取件未更新',
            'default': '退货相关'
        },
        'refund': {
            'refund_request_status': '退款进度查询',
            'refund_timeline': '退款时效',
            'default': '退款相关'
        },
        'wallet_store_credit': {
            'wallet_status': '钱包/余额查询',
            'wallet_refund_status': '钱包退款',
            'default': '钱包相关'
        },
        'presales_queries': {
            'pricing_promotions': '价格优惠咨询',
            'product_inquiry': '商品咨询',
            'discounts_and_offers': '折扣优惠',
            'default': '售前咨询'
        },
        'post-sale_queries': {
            'customer_feedback': '客户反馈',
            'positive_feedback': '正面评价',
            'default': '售后查询'
        },
        'general_concerns': {
            'general_support': '一般咨询',
            'general_concern': '一般问题',
            'default': '一般问题'
        }
    }

    # 尝试匹配
    if category in mapping:
        for key, value in mapping[category].items():
            if key in subcategory or key in full_label:
                return value
        return mapping[category]['default']

    # 特殊处理
    if 'delivery' in full_label:
        if 'delayed' in full_label:
            return '配送延迟'
        elif 'rto' in full_label:
            return '配送异常-RTO'
        elif 'exception' in full_label:
            return '配送异常'
        return '配送相关'
    elif 'return' in full_label:
        if 'pickup' in full_label:
            return '退货取件问题'
        return '退货相关'
    elif 'refund' in full_label:
        return '退款相关'
    elif 'cancel' in full_label:
        return '订单取消'

    return '其他问题'

def analyze_feedback(file_path):
    """主分析函数"""
    print("正在加载数据...")
    df = pd.read_csv(file_path)

    # 解析时间
    df['created_at'] = pd.to_datetime(df['created_at'])
    df['hour'] = df['created_at'].dt.hour

    # 解析custom_attributes
    df['attrs'] = df['custom_attributes'].apply(parse_custom_attributes)
    df['ai_labels'] = df['attrs'].apply(lambda x: x.get('ub_ai_label_list', 'N/A'))
    df['ai_agent'] = df['attrs'].apply(lambda x: x.get('ub_ai_agent_id', 'unknown'))

    # 映射渠道名称
    df['channel'] = df['inbox_id'].apply(get_inbox_name)

    # 解析反馈类型
    df['feedback_types'] = df['ai_labels'].apply(parse_ai_labels)

    # 展开反馈类型（一条会话可能有多个标签）
    feedback_data = []
    for idx, row in df.iterrows():
        for feedback_type in row['feedback_types']:
            feedback_data.append({
                'hour': row['hour'],
                'channel': row['channel'],
                'feedback_type': feedback_type,
                'conversation_id': row['id'],
                'ai_agent': row['ai_agent']
            })

    feedback_df = pd.DataFrame(feedback_data)

    print(f"\n✅ 数据加载完成: {len(df)} 条会话, {len(feedback_df)} 个反馈标签\n")

    return df, feedback_df

def generate_hourly_channel_report(feedback_df):
    """生成按小时和渠道的统计报告"""

    print("=" * 100)
    print("📊 客服进线内容分析报告 - 按小时&渠道&反馈内容")
    print("=" * 100)

    # 1. 总体统计
    total_feedback = len(feedback_df)
    total_conversations = feedback_df['conversation_id'].nunique()

    print(f"\n【总体概况】")
    print(f"  • 总会话数: {total_conversations:,}")
    print(f"  • 总反馈标签数: {total_feedback:,}")
    print(f"  • 平均每会话标签数: {total_feedback/total_conversations:.2f}")

    # 2. 按小时统计
    print(f"\n{'=' * 100}")
    print("📅 按小时统计")
    print(f"{'=' * 100}\n")

    hourly_stats = feedback_df.groupby('hour').agg({
        'conversation_id': 'nunique',
        'feedback_type': 'count'
    }).rename(columns={
        'conversation_id': '会话数',
        'feedback_type': '反馈数'
    })

    hourly_stats['占比'] = (hourly_stats['会话数'] / total_conversations * 100).round(2)
    print(hourly_stats.to_string())

    # 3. 按渠道统计
    print(f"\n{'=' * 100}")
    print("📱 按渠道统计")
    print(f"{'=' * 100}\n")

    channel_stats = feedback_df.groupby('channel').agg({
        'conversation_id': 'nunique',
        'feedback_type': 'count'
    }).rename(columns={
        'conversation_id': '会话数',
        'feedback_type': '反馈数'
    }).sort_values('会话数', ascending=False)

    channel_stats['占比'] = (channel_stats['会话数'] / total_conversations * 100).round(2)
    print(channel_stats.to_string())

    # 4. 按反馈类型统计（Top 20）
    print(f"\n{'=' * 100}")
    print("🏷️  用户反馈内容统计（Top 20）")
    print(f"{'=' * 100}\n")

    feedback_stats = feedback_df.groupby('feedback_type').agg({
        'conversation_id': 'nunique'
    }).rename(columns={
        'conversation_id': '反馈量'
    }).sort_values('反馈量', ascending=False).head(20)

    feedback_stats['占比(%)'] = (feedback_stats['反馈量'] / total_conversations * 100).round(2)
    print(feedback_stats.to_string())

    # 5. 按小时+渠道的交叉统计
    print(f"\n{'=' * 100}")
    print("🕐 小时 × 渠道 交叉统计（会话数）")
    print(f"{'=' * 100}\n")

    hour_channel_pivot = pd.crosstab(
        feedback_df['hour'],
        feedback_df['channel'],
        values=feedback_df['conversation_id'],
        aggfunc='nunique'
    ).fillna(0).astype(int)

    print(hour_channel_pivot.to_string())

    # 6. 详细报表：小时 × 渠道 × 反馈内容
    print(f"\n{'=' * 100}")
    print("📊 详细报表：小时 | 渠道 | 反馈内容 | 反馈量 | 占比")
    print(f"{'=' * 100}\n")

    detailed_stats = feedback_df.groupby(['hour', 'channel', 'feedback_type']).agg({
        'conversation_id': 'nunique'
    }).rename(columns={
        'conversation_id': '反馈量'
    }).reset_index()

    # 计算每个小时的总量用于计算占比
    hour_totals = feedback_df.groupby('hour')['conversation_id'].nunique().to_dict()
    detailed_stats['小时总量'] = detailed_stats['hour'].map(hour_totals)
    detailed_stats['占比(%)'] = (detailed_stats['反馈量'] / detailed_stats['小时总量'] * 100).round(2)

    # 排序：按小时、反馈量降序
    detailed_stats = detailed_stats.sort_values(['hour', '反馈量'], ascending=[True, False])

    # 格式化输出
    current_hour = None
    for idx, row in detailed_stats.iterrows():
        if row['hour'] != current_hour:
            current_hour = row['hour']
            print(f"\n{'─' * 100}")
            print(f"⏰ {current_hour:02d}:00 - {current_hour:02d}:59 (共 {hour_totals[current_hour]:,} 个会话)")
            print(f"{'─' * 100}")

        print(f"  📱 {row['channel']:20s} | 🏷️  {row['feedback_type']:30s} | "
              f"📊 {row['反馈量']:4d} ({row['占比(%)']:5.2f}%)")

    # 7. 按渠道的Top反馈内容
    print(f"\n{'=' * 100}")
    print("📱 各渠道Top 5反馈内容")
    print(f"{'=' * 100}\n")

    for channel in feedback_df['channel'].unique():
        channel_data = feedback_df[feedback_df['channel'] == channel]
        top_feedback = channel_data.groupby('feedback_type')['conversation_id'].nunique().sort_values(ascending=False).head(5)

        print(f"\n【{channel}】 (共 {channel_data['conversation_id'].nunique():,} 个会话)")
        for feedback_type, count in top_feedback.items():
            pct = count / channel_data['conversation_id'].nunique() * 100
            print(f"  {count:4d} ({pct:5.2f}%) | {feedback_type}")

    return detailed_stats

def export_to_excel(detailed_stats, feedback_df, output_path):
    """导出到Excel"""
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        # Sheet 1: 详细数据
        detailed_stats.to_excel(writer, sheet_name='详细数据', index=False)

        # Sheet 2: 小时汇总
        hourly_summary = feedback_df.groupby('hour').agg({
            'conversation_id': 'nunique',
            'feedback_type': 'count'
        }).rename(columns={'conversation_id': '会话数', 'feedback_type': '反馈数'})
        hourly_summary.to_excel(writer, sheet_name='小时汇总')

        # Sheet 3: 渠道汇总
        channel_summary = feedback_df.groupby('channel').agg({
            'conversation_id': 'nunique',
            'feedback_type': 'count'
        }).rename(columns={'conversation_id': '会话数', 'feedback_type': '反馈数'})
        channel_summary.to_excel(writer, sheet_name='渠道汇总')

        # Sheet 4: 反馈类型汇总
        feedback_summary = feedback_df.groupby('feedback_type').agg({
            'conversation_id': 'nunique'
        }).rename(columns={'conversation_id': '反馈量'}).sort_values('反馈量', ascending=False)
        feedback_summary.to_excel(writer, sheet_name='反馈类型汇总')

        # Sheet 5: 小时×渠道交叉表
        hour_channel_pivot = pd.crosstab(
            feedback_df['hour'],
            feedback_df['channel'],
            values=feedback_df['conversation_id'],
            aggfunc='nunique'
        ).fillna(0).astype(int)
        hour_channel_pivot.to_excel(writer, sheet_name='小时渠道交叉表')

    print(f"\n✅ 数据已导出到: {output_path}")

def main():
    file_path = '/Users/yixiqian/Downloads/2026-05-22-15-50-17_EXPORT_CSV_25669721_668_0.csv'

    # 分析数据
    df, feedback_df = analyze_feedback(file_path)

    # 生成报告
    detailed_stats = generate_hourly_channel_report(feedback_df)

    # 导出Excel
    output_path = '/Users/yixiqian/daily-work-summary/chatwoot_feedback_analysis.xlsx'
    export_to_excel(detailed_stats, feedback_df, output_path)

    print(f"\n{'=' * 100}")
    print("✅ 分析完成！")
    print(f"{'=' * 100}\n")

if __name__ == "__main__":
    main()
