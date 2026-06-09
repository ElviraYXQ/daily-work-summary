#!/usr/bin/env python3
"""
按问题类型分类，标注是否大促特有
"""
import pandas as pd
import requests
import json
import time
import re

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

def clean_content(content):
    """移除JSON卡片，只保留用户文字消息"""
    if not content:
        return ""

    # 移除JSON格式的卡片（更彻底）
    # 匹配 {"cardType": 开头到对应的 } 结尾
    content = re.sub(r'\{[^{}]*"cardType"[^{}]*\{.*?\}.*?\}', '', content, flags=re.DOTALL)
    content = re.sub(r'\{"cardType"[^\}]*\}', '', content, flags=re.DOTALL)

    # 移除常见的JSON残留
    content = re.sub(r'\{".*?\}', '', content, flags=re.DOTALL)
    content = re.sub(r',\{"keyId.*?\}', '', content)
    content = re.sub(r'}}+', '', content)

    # 清理多余空白
    content = '\n'.join([line.strip() for line in content.split('\n') if line.strip()])

    return content

def classify_by_issue_type(content):
    """
    按问题类型分类
    返回: {
        'categories': [问题类型列表],
        'is_promo_specific': 是否大促特有,
        'has_content': 是否有文字内容
    }
    """
    # 移除JSON，只分析文字
    content_text = clean_content(content)

    if not content_text or len(content_text) < 3:
        return {
            'categories': ['无文字消息'],
            'is_promo_specific': False,
            'has_content': False
        }

    content_lower = content_text.lower()
    categories = []
    is_promo_specific = False

    # === 大促特有问题 ===

    # 1. 免费活动咨询/投诉
    free_keywords = ['free sale', 'free day', 'free order', 'free cloth', 'free item', 'get free']
    free_simple = ['free', '免费']

    has_free = any(kw in content_lower for kw in free_keywords)
    if not has_free:
        if any(kw in content_lower for kw in free_simple):
            # 必须同时提到order/sale等，且在询问/投诉
            if any(word in content_lower for word in ['order', 'sale', 'when', 'how', 'get', 'milne', 'kaise']):
                has_free = True

    if has_free:
        categories.append('免费活动咨询/投诉')
        is_promo_specific = True

    # 2. 优惠券使用问题
    coupon_keywords = ['coupon', 'voucher', 'promo code', '优惠券']
    if any(kw in content_lower for kw in coupon_keywords):
        categories.append('优惠券使用问题')
        is_promo_specific = True

    # 3. 大促规则不清晰/投诉
    # 必须明确提到大促，且明确在询问规则/投诉不公平
    promo_explicit = ['anniversary sale', 'mega sale', '522', '5.22', 'flash sale', 'free sale', 'free day']
    promo_query = [
        'how to get', 'how to use', 'how to participate', 'how to join',
        'why not me', 'why don\'t', 'why i don', 'not eligible',
        'who can', 'terms', 'conditions', 'rules', 'details',
        '为什么我没有', '怎么参加', '如何获得', '规则'
    ]

    has_promo_mention = any(kw in content_lower for kw in promo_explicit)
    has_promo_query = any(kw in content_lower for kw in promo_query)

    if has_promo_mention and has_promo_query:
        categories.append('大促规则不清晰/投诉')
        is_promo_specific = True

    # === 日常问题（可能大促期间增多） ===

    # 4. 订单取消/修改
    if 'cancel' in content_lower:
        categories.append('订单取消/修改')

    # 5. 退款/退货
    refund_keywords = ['refund', 'return', 'exchange', '退款', '退货']
    if any(kw in content_lower for kw in refund_keywords):
        categories.append('退款/退货')

    # 6. 配送查询
    delivery_keywords = ['delivery', 'shipping', 'dispatch', 'tracking', 'shipped', '配送', '物流', '发货']
    if any(kw in content_lower for kw in delivery_keywords):
        categories.append('配送查询')

    # 7. 支付问题
    payment_keywords = ['payment', 'paid', 'pay', 'debited', 'money', 'cash on delivery', 'cod', '支付', '付款']
    if any(kw in content_lower for kw in payment_keywords):
        # 排除已归类为退款的
        if '退款/退货' not in categories:
            categories.append('支付问题')

    # 8. 技术问题-App崩溃/卡顿
    tech_keywords = ['crash', 'not working', 'error', 'network', 'unavailable', 'lag', 'freeze', 'slow', 'crashed']
    if any(kw in content_lower for kw in tech_keywords):
        categories.append('技术问题-App崩溃/卡顿')

    # 9. 商品咨询
    product_keywords = ['size', 'color', 'material', 'fabric', 'quality', '尺码', '颜色', '材质']
    price_keywords = ['price', 'discount', 'offer', '价格', '折扣']

    if any(kw in content_lower for kw in product_keywords):
        # 不包含价格相关
        if not any(kw in content_lower for kw in price_keywords):
            categories.append('商品咨询')

    # 10. 账户问题
    account_keywords = ['account', 'login', 'password', 'email', 'phone', 'wallet', '账户', '密码', '钱包']
    if any(kw in content_lower for kw in account_keywords):
        categories.append('账户问题')

    # 11. 订单状态查询
    order_status_keywords = [
        'where is my', 'order status', 'track', 'parcel', 'not received',
        'not delivered', 'when will', 'kab tak', 'details of my order',
        '订单在哪', '物流信息'
    ]
    if any(kw in content_lower for kw in order_status_keywords):
        # 排除已归类为配送查询的
        if '配送查询' not in categories:
            categories.append('订单状态查询')

    # 12. 下单失败/无法下单
    order_fail_keywords = [
        'unable to order', 'can\'t order', 'cannot place', 'place order',
        'not showing', 'can\'t open cart', 'cart not', 'out of stock',
        'not available', '无法下单', '下单失败'
    ]
    if any(kw in content_lower for kw in order_fail_keywords):
        categories.append('下单失败/无法下单')

    # 13. 地址修改
    address_keywords = ['change address', 'change my address', 'update address', 'wrong address', 'deliver on', '修改地址']
    if any(kw in content_lower for kw in address_keywords):
        categories.append('地址修改')

    # 14. 奖励/积分查询
    reward_keywords = ['reward', 'gift', 'points', 'wallet', '奖励', '积分', '礼物']
    # 需要同时包含查询词
    reward_query = ['how to', 'where is', 'when', 'received', 'get', 'see', '如何', '怎么']
    if any(kw in content_lower for kw in reward_keywords):
        if any(q in content_lower for q in reward_query):
            # 排除已归类为大促规则或免费活动的
            if '大促规则不清晰/投诉' not in categories and '免费活动咨询/投诉' not in categories:
                categories.append('奖励/积分查询')

    # 15. 负面投诉
    negative_keywords = [
        'bad experience', 'disappointed', 'hate', 'fraud', 'worst',
        'terrible', 'horrible', 'useless', 'waste', 'shit', 'fuck',
        '很差', '太差', '垃圾', '骗人'
    ]
    if any(kw in content_lower for kw in negative_keywords):
        categories.append('负面投诉')

    # 16. KOL合作请求
    collab_keywords = [
        'content creator', 'influencer', 'collaborate', 'collaboration',
        'work together', 'partnership', 'brand ambassador', 'promote'
    ]
    if any(kw in content_lower for kw in collab_keywords):
        categories.append('KOL合作请求')

    # 17. 社交/祝福
    social_keywords = [
        'happy birthday', 'mentioned you in', 'congratulations',
        'proud of you', 'wish you', '生日快乐', '祝福'
    ]
    if any(kw in content_lower for kw in social_keywords):
        categories.append('社交/祝福')

    # 18. 如果没有任何分类
    if not categories:
        # 检查是否只是简单问候
        greetings = ['hello', 'hi', 'hey', 'thank you', 'thanks']
        if any(kw in content_lower for kw in greetings) and len(content_text) < 50:
            categories.append('问候/寒暄')
        else:
            categories.append('其他')

    return {
        'categories': categories,
        'is_promo_specific': is_promo_specific,
        'has_content': True
    }

def analyze_sample_from_csv(csv_path):
    """从已有CSV重新分类"""
    print("正在加载已有数据...")
    df = pd.read_csv(csv_path)

    print(f"✅ 加载完成: {len(df)} 条会话")
    print(f"\n开始重新分类...\n")

    results = []

    for idx, row in df.iterrows():
        content = row['full_content'] if pd.notna(row['full_content']) else ''

        # 分类
        classification = classify_by_issue_type(content)

        results.append({
            'conversation_id': row['conversation_id'],
            'hour': row['hour'],
            'created_at': row['created_at'],
            'categories': classification['categories'],
            'is_promo_specific': classification['is_promo_specific'],
            'has_content': classification['has_content'],
            'content_preview': clean_content(content)[:200] if content else '',
            'full_content': content
        })

        if (idx + 1) % 100 == 0:
            print(f"  已处理: {idx + 1} / {len(df)}")

    results_df = pd.DataFrame(results)

    return results_df

def generate_text_report(results_df):
    """生成文本报告"""
    print("\n" + "=" * 100)
    print("📊 按问题类型分类结果")
    print("=" * 100)

    # 总体统计
    total = len(results_df)
    promo_specific = len(results_df[results_df['is_promo_specific'] == True])
    has_content = len(results_df[results_df['has_content'] == True])

    print(f"\n【总体概况】")
    print(f"  样本总数: {total}")
    print(f"  有文字内容: {has_content} ({has_content/total*100:.1f}%)")
    print(f"  大促特有问题: {promo_specific} ({promo_specific/total*100:.1f}%)")

    # 按问题类型统计
    print(f"\n" + "=" * 100)
    print("📋 问题类型分布（按进线量排序）")
    print("=" * 100)

    all_cats = []
    for cats in results_df['categories']:
        all_cats.extend(cats)

    cat_counts = pd.Series(all_cats).value_counts()

    print(f"\n{'排名':<5} {'问题类型':<30} {'进线数':<10} {'占比':<10} {'大促特有':<10}")
    print("-" * 75)

    promo_specific_types = ['免费活动咨询/投诉', '优惠券使用问题', '大促规则不清晰/投诉']

    for rank, (cat, count) in enumerate(cat_counts.items(), 1):
        pct = count / total * 100
        is_promo = "✅ 是" if cat in promo_specific_types else ""
        print(f"{rank:<5} {cat:<30} {count:>6}     {pct:>5.1f}%     {is_promo}")

    # 大促特有问题详细
    print(f"\n" + "=" * 100)
    print("🔴 大促特有问题详细")
    print("=" * 100)

    for cat in promo_specific_types:
        if cat in cat_counts:
            count = cat_counts[cat]
            print(f"\n【{cat}】: {count} 条 ({count/total*100:.1f}%)")

            # 展示样本
            cat_samples = results_df[results_df['categories'].apply(lambda x: cat in x)]

            samples_with_text = cat_samples[cat_samples['content_preview'].str.len() > 10]
            if len(samples_with_text) == 0:
                samples_with_text = cat_samples

            for idx, row in samples_with_text.head(2).iterrows():
                print(f"\n  案例: 会话{row['conversation_id']}")
                print(f"  {row['content_preview'][:150]}")

    # 日常问题（大促期间可能增多）
    print(f"\n" + "=" * 100)
    print("⚪ 日常问题（大促期间可能增多）")
    print("=" * 100)

    daily_types = [cat for cat in cat_counts.index if cat not in promo_specific_types and cat != '无文字消息']

    for cat in daily_types[:10]:
        count = cat_counts[cat]
        pct = count / total * 100

        # 特别标注：技术问题在大促期间集中爆发
        note = ""
        if cat == '技术问题-App崩溃/卡顿':
            note = " ⚠️ 大促期间集中爆发"

        print(f"\n【{cat}】: {count} 条 ({pct:.1f}%){note}")

def main():
    csv_path = '/Users/yixiqian/daily-work-summary/content_based_analysis_sample.csv'

    print("\n" + "🎯 " * 30)
    print("按问题类型分类 - 522大促客服进线分析")
    print("🎯 " * 30 + "\n")

    # 重新分类
    results_df = analyze_sample_from_csv(csv_path)

    # 保存结果
    results_df.to_csv(
        '/Users/yixiqian/daily-work-summary/issue_type_analysis_sample.csv',
        index=False
    )

    # 生成报告
    generate_text_report(results_df)

    print("\n✅ 分析完成！")
    print(f"结果已保存到: issue_type_analysis_sample.csv")

if __name__ == "__main__":
    main()
