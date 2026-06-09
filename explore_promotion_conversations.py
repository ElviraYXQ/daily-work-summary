#!/usr/bin/env python3
"""
识别522大促相关客服进线
第一步：数据探索和分类方案设计
"""
import pandas as pd
import json
import re
from collections import defaultdict

def parse_custom_attributes(attr_str):
    """解析custom_attributes JSON字符串"""
    try:
        if pd.isna(attr_str):
            return {}
        return json.loads(attr_str)
    except:
        return {}

def explore_promotion_related(file_path):
    """探索大促相关会话"""
    print("正在加载数据...")
    df = pd.read_csv(file_path)

    df['created_at'] = pd.to_datetime(df['created_at'])
    df['attrs'] = df['custom_attributes'].apply(parse_custom_attributes)
    df['ai_labels'] = df['attrs'].apply(lambda x: x.get('ub_ai_label_list', ''))
    df['ai_agent'] = df['attrs'].apply(lambda x: x.get('ub_ai_agent_id', ''))
    df['biz_name'] = df['attrs'].apply(lambda x: x.get('ub_biz_name', ''))

    print(f"✅ 数据加载完成: {len(df)} 条会话\n")

    # 1. 基于AI标签识别可能的大促相关会话
    print("=" * 100)
    print("🔍 第一步：基于AI标签识别大促相关会话")
    print("=" * 100 + "\n")

    # 大促相关关键词
    promotion_keywords = [
        'pricing', 'promotion', 'discount', 'offer', 'coupon',
        'price', 'sale', '优惠', '折扣', '促销', '活动'
    ]

    df['is_promotion_related'] = df['ai_labels'].apply(
        lambda x: any(keyword in str(x).lower() for keyword in promotion_keywords) if pd.notna(x) else False
    )

    promotion_df = df[df['is_promotion_related']]

    print(f"📊 识别到可能的大促相关会话: {len(promotion_df):,} / {len(df):,} ({len(promotion_df)/len(df)*100:.2f}%)\n")

    # 2. 查看这些会话的AI标签分布
    print("=" * 100)
    print("🏷️  大促相关会话的AI标签分布（Top 20）")
    print("=" * 100 + "\n")

    promotion_labels = promotion_df['ai_labels'].value_counts().head(20)
    for label, count in promotion_labels.items():
        pct = count / len(promotion_df) * 100
        print(f"  {count:4d} ({pct:5.2f}%) | {label}")

    # 3. 查看AI Agent分布
    print("\n" + "=" * 100)
    print("🤖 大促相关会话的AI Agent分布")
    print("=" * 100 + "\n")

    agent_dist = promotion_df['ai_agent'].value_counts().head(10)
    for agent, count in agent_dist.items():
        pct = count / len(promotion_df) * 100
        print(f"  {count:4d} ({pct:5.2f}%) | {agent}")

    # 4. 查看业务来源分布
    print("\n" + "=" * 100)
    print("📱 大促相关会话的业务来源分布")
    print("=" * 100 + "\n")

    biz_dist = promotion_df['biz_name'].value_counts().head(10)
    for biz, count in biz_dist.items():
        pct = count / len(promotion_df) * 100
        print(f"  {count:4d} ({pct:5.2f}%) | {biz}")

    # 5. 按小时分布
    print("\n" + "=" * 100)
    print("⏰ 大促相关会话的小时分布")
    print("=" * 100 + "\n")

    promotion_df['hour'] = promotion_df['created_at'].dt.hour
    hour_dist = promotion_df.groupby('hour').size()

    for hour, count in hour_dist.items():
        pct = count / len(promotion_df) * 100
        total_in_hour = len(df[df['created_at'].dt.hour == hour])
        pct_of_hour = count / total_in_hour * 100 if total_in_hour > 0 else 0
        print(f"  {hour:02d}:00 | {count:4d} 条 ({pct:5.2f}% 的大促会话) | 占该小时总量 {pct_of_hour:.2f}%")

    # 6. 提取所有唯一的AI标签进行细分
    print("\n" + "=" * 100)
    print("🗂️  所有独立的AI标签（用于分类设计）")
    print("=" * 100 + "\n")

    all_labels = []
    for labels_str in promotion_df['ai_labels'].dropna():
        for label in str(labels_str).split(','):
            label = label.strip()
            if label and any(keyword in label.lower() for keyword in promotion_keywords):
                all_labels.append(label)

    label_counts = pd.Series(all_labels).value_counts()
    print(f"共 {len(label_counts)} 种不同的大促相关标签\n")

    for label, count in label_counts.head(30).items():
        pct = count / len(promotion_df) * 100
        print(f"  {count:4d} ({pct:5.2f}%) | {label}")

    return df, promotion_df, label_counts

def design_classification_scheme(promotion_df, label_counts):
    """设计分类方案"""
    print("\n" + "=" * 100)
    print("📋 建议的大促相关进线分类方案（草案）")
    print("=" * 100 + "\n")

    classification_scheme = {
        "1. 优惠券问题": {
            "描述": "优惠券领取、使用、失效等问题",
            "关键词": ["coupon", "voucher", "优惠券"],
            "示例": "优惠券用不了、优惠券在哪里领、优惠券过期了"
        },
        "2. 折扣价格咨询": {
            "描述": "商品折扣、价格咨询、价格对比",
            "关键词": ["discount", "price", "pricing", "offer", "折扣", "价格"],
            "示例": "这个商品有折扣吗、为什么价格变了、折扣什么时候结束"
        },
        "3. 促销活动规则": {
            "描述": "大促活动规则、参与条件、时间限制",
            "关键词": ["promotion", "activity", "campaign", "促销", "活动"],
            "示例": "活动怎么参加、满减规则是什么、活动什么时候结束"
        },
        "4. 凑单包邮问题": {
            "描述": "为了满足促销条件（如满减、包邮）的凑单问题",
            "关键词": ["shipping", "free delivery", "包邮", "满减"],
            "示例": "还差多少包邮、怎么凑单、可以推荐凑单商品吗"
        },
        "5. 大促订单取消/修改": {
            "描述": "因价格变化、优惠问题等导致的订单取消或修改请求",
            "关键词": ["cancel", "modify", "change", "取消", "修改"],
            "示例": "我想取消重新下单用优惠券、价格变了想退掉"
        },
        "6. 大促期间配送问题": {
            "描述": "大促期间订单量大导致的配送延迟等问题",
            "关键词": ["delivery", "shipping", "配送", "物流"],
            "示例": "订单为什么还不发货、大促期间配送要多久"
        },
        "7. 其他大促相关": {
            "描述": "无法归入以上类别的其他大促相关问题",
            "关键词": [],
            "示例": "大促商品质量、大促退换货政策等"
        }
    }

    for category, details in classification_scheme.items():
        print(f"\n{category}")
        print(f"  📝 描述: {details['描述']}")
        print(f"  🔑 关键词: {', '.join(details['关键词']) if details['关键词'] else '无'}")
        print(f"  💡 示例: {details['示例']}")

    print("\n" + "=" * 100)
    print("❓ 需要确认的问题")
    print("=" * 100 + "\n")

    questions = [
        "1. 以上分类方案是否合理？需要增加或删除哪些类别？",
        "2. 是否有其他识别大促相关会话的方式？（如特定订单号前缀、特定商品等）",
        "3. 是否需要单独统计「大促期间的退款/退货」问题？",
        "4. 是否需要区分「新客」和「老客」的大促咨询？",
        "5. 当前基于AI标签识别，是否需要调用API获取具体消息内容进行更精确的识别？"
    ]

    for q in questions:
        print(f"  {q}")

    return classification_scheme

def sample_conversations(promotion_df, n=20):
    """抽样展示大促相关会话的详细信息"""
    print("\n" + "=" * 100)
    print(f"📌 抽样展示 {n} 条大促相关会话（用于验证分类准确性）")
    print("=" * 100 + "\n")

    samples = promotion_df.sample(min(n, len(promotion_df)))

    for idx, (_, row) in enumerate(samples.iterrows(), 1):
        print(f"【样本 {idx}】")
        print(f"  会话ID: {row['id']}")
        print(f"  时间: {row['created_at']}")
        print(f"  AI标签: {row['ai_labels']}")
        print(f"  AI Agent: {row['ai_agent']}")
        print(f"  业务来源: {row['biz_name']}")
        print(f"  渠道: inbox_id={row['inbox_id']}")
        print()

def main():
    file_path = '/Users/yixiqian/Downloads/2026-05-22-15-50-17_EXPORT_CSV_25669721_668_0.csv'

    print("\n" + "🎯 " * 30)
    print("522大促相关客服进线分析 - 第一步：数据探索与分类方案设计")
    print("🎯 " * 30 + "\n")

    # 1. 探索数据
    df, promotion_df, label_counts = explore_promotion_related(file_path)

    # 2. 设计分类方案
    classification_scheme = design_classification_scheme(promotion_df, label_counts)

    # 3. 抽样展示
    sample_conversations(promotion_df, n=15)

    # 4. 保存初步结果
    promotion_df.to_csv(
        '/Users/yixiqian/daily-work-summary/promotion_related_conversations_raw.csv',
        index=False
    )
    print(f"✅ 初步识别的大促相关会话已保存到: promotion_related_conversations_raw.csv")

    print("\n" + "=" * 100)
    print("⏭️  下一步")
    print("=" * 100 + "\n")
    print("1. 请review以上分类方案和样本数据")
    print("2. 确认分类是否合理，是否需要调整")
    print("3. 如需查看具体消息内容，我可以调用Chatwoot API获取")
    print("4. 确认后，我将执行最终的分类统计和分析\n")

if __name__ == "__main__":
    main()
