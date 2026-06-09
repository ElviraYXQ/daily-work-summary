# 522大促客服进线分类 - Agent执行指南

## 📋 任务概述

**目标**：每日分析Chatwoot客服会话，按问题类型分类，识别大促特有问题

**输入**：Chatwoot导出的CSV文件（包含conversation_id和created_at）

**输出**：
1. 分类结果CSV文件（含categories和is_promo_specific字段）
2. 文本格式分析报告（问题类型分布、典型案例）

---

## 🔧 完整执行流程

### Step 1: 数据准备

从Chatwoot导出CSV，包含以下字段：
- `id` (conversation_id)
- `created_at` (会话创建时间)

### Step 2: 获取会话内容

通过Chatwoot API获取每个会话的用户消息：

```python
import requests

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
    """提取用户消息（message_type=0）"""
    if not response:
        return []

    messages = response.get('payload', []) if isinstance(response, dict) else []
    user_messages = []

    for msg in messages:
        if msg.get('message_type') == 0:  # 用户消息
            content = msg.get('content') or ''
            content = content.strip() if isinstance(content, str) else ''
            if content:
                user_messages.append(content)

    return user_messages
```

**注意事项**：
- API限流：每次请求后延迟0.2秒
- 异常处理：API失败时记录但继续处理
- 拼接所有用户消息为单个字符串：`full_content = '\n'.join(user_messages)`

### Step 3: 内容预处理（移除JSON卡片）

**关键步骤**：用户消息中包含大量订单卡片JSON，必须清理后再分类

```python
import re

def clean_content(content):
    """移除JSON卡片，只保留用户文字消息"""
    if not content:
        return ""

    # 移除JSON格式的卡片
    content = re.sub(r'\{[^{}]*"cardType"[^{}]*\{.*?\}.*?\}', '', content, flags=re.DOTALL)
    content = re.sub(r'\{"cardType"[^\}]*\}', '', content, flags=re.DOTALL)
    content = re.sub(r'\{".*?\}', '', content, flags=re.DOTALL)
    content = re.sub(r',\{"keyId.*?\}', '', content)
    content = re.sub(r'}}+', '', content)

    # 清理多余空白
    content = '\n'.join([line.strip() for line in content.split('\n') if line.strip()])

    return content
```

### Step 4: 问题类型分类

使用 `classification_rules_for_agent.md` 中定义的20个问题类型进行分类。

**核心分类函数**：

```python
def classify_by_issue_type(content):
    """
    按问题类型分类
    返回: {
        'categories': [问题类型列表],
        'is_promo_specific': 是否大促特有,
        'has_content': 是否有文字内容
    }
    """
    # 1. 清理JSON
    content_text = clean_content(content)

    # 2. 检查是否有文字
    if not content_text or len(content_text) < 3:
        return {
            'categories': ['无文字消息'],
            'is_promo_specific': False,
            'has_content': False
        }

    content_lower = content_text.lower()
    categories = []
    is_promo_specific = False

    # 3. 大促特有问题（3类）

    # 3.1 免费活动咨询/投诉
    free_keywords = ['free sale', 'free day', 'free order', 'free cloth', 'free item', 'get free']
    free_simple = ['free', '免费']
    has_free = any(kw in content_lower for kw in free_keywords)
    if not has_free:
        if any(kw in content_lower for kw in free_simple):
            if any(word in content_lower for word in ['order', 'sale', 'when', 'how', 'get', 'milne', 'kaise']):
                has_free = True
    if has_free:
        categories.append('免费活动咨询/投诉')
        is_promo_specific = True

    # 3.2 优惠券使用问题
    coupon_keywords = ['coupon', 'voucher', 'promo code', '优惠券']
    if any(kw in content_lower for kw in coupon_keywords):
        categories.append('优惠券使用问题')
        is_promo_specific = True

    # 3.3 大促规则不清晰/投诉（严格条件：必须同时提到大促+询问规则）
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

    # 4. 日常问题（17类）- 见classification_rules_for_agent.md完整代码
    # 4.1 订单取消/修改
    if 'cancel' in content_lower:
        categories.append('订单取消/修改')

    # 4.2 退款/退货
    refund_keywords = ['refund', 'return', 'exchange', '退款', '退货']
    if any(kw in content_lower for kw in refund_keywords):
        categories.append('退款/退货')

    # ... 其他15个类型（参考classify_by_issue_type.py完整实现）

    # 5. 兜底：如果没有任何分类
    if not categories:
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
```

**完整分类代码**：使用 `classify_by_issue_type.py` 中的完整实现

### Step 5: 生成输出

#### 输出1: CSV文件

保存包含以下字段的CSV：
- `conversation_id`: 会话ID
- `created_at`: 创建时间
- `hour`: 小时（0-23）
- `categories`: 问题类型列表（如 `['免费活动咨询/投诉', '订单取消/修改']`）
- `is_promo_specific`: 是否大促特有（True/False）
- `has_content`: 是否有文字内容（True/False）
- `content_preview`: 清理后内容的前200字符
- `full_content`: 完整原始内容（可选）

```python
import pandas as pd

results_df = pd.DataFrame(results)
results_df.to_csv('issue_type_analysis_YYYYMMDD.csv', index=False)
```

#### 输出2: 文本报告

```python
def generate_text_report(results_df):
    """生成文本报告"""
    print("\n" + "=" * 100)
    print("📊 按问题类型分类结果")
    print("=" * 100)

    # 1. 总体统计
    total = len(results_df)
    promo_specific = len(results_df[results_df['is_promo_specific'] == True])
    has_content = len(results_df[results_df['has_content'] == True])

    print(f"\n【总体概况】")
    print(f"  样本总数: {total}")
    print(f"  有文字内容: {has_content} ({has_content/total*100:.1f}%)")
    print(f"  大促特有问题: {promo_specific} ({promo_specific/total*100:.1f}%)")

    # 2. 问题类型分布（按进线量排序）
    all_cats = []
    for cats in results_df['categories']:
        all_cats.extend(cats)

    cat_counts = pd.Series(all_cats).value_counts()

    print(f"\n" + "=" * 100)
    print("📋 问题类型分布（按进线量排序）")
    print("=" * 100)
    print(f"\n{'排名':<5} {'问题类型':<30} {'进线数':<10} {'占比':<10} {'大促特有':<10}")
    print("-" * 75)

    promo_specific_types = ['免费活动咨询/投诉', '优惠券使用问题', '大促规则不清晰/投诉']

    for rank, (cat, count) in enumerate(cat_counts.items(), 1):
        pct = count / total * 100
        is_promo = "✅ 是" if cat in promo_specific_types else ""
        print(f"{rank:<5} {cat:<30} {count:>6}     {pct:>5.1f}%     {is_promo}")

    # 3. 大促特有问题详细（展示典型案例）
    print(f"\n" + "=" * 100)
    print("🔴 大促特有问题详细")
    print("=" * 100)

    for cat in promo_specific_types:
        if cat in cat_counts:
            count = cat_counts[cat]
            print(f"\n【{cat}】: {count} 条 ({count/total*100:.1f}%)")

            # 展示2个典型案例
            cat_samples = results_df[results_df['categories'].apply(lambda x: cat in x)]
            samples_with_text = cat_samples[cat_samples['content_preview'].str.len() > 10]
            if len(samples_with_text) == 0:
                samples_with_text = cat_samples

            for idx, row in samples_with_text.head(2).iterrows():
                print(f"\n  案例: 会话{row['conversation_id']}")
                print(f"  {row['content_preview'][:150]}")

    # 4. 日常问题Top 10
    print(f"\n" + "=" * 100)
    print("⚪ 日常问题（大促期间可能增多）")
    print("=" * 100)

    daily_types = [cat for cat in cat_counts.index
                   if cat not in promo_specific_types and cat != '无文字消息']

    for cat in daily_types[:10]:
        count = cat_counts[cat]
        pct = count / total * 100
        note = " ⚠️ 大促期间集中爆发" if cat == '技术问题-App崩溃/卡顿' else ""
        print(f"\n【{cat}】: {count} 条 ({pct:.1f}%){note}")
```

---

## 📊 预期输出示例

### 总体概况
```
样本总数: 14777
有文字内容: 12000 (81.2%)
大促特有问题: 2900 (19.6%)
```

### 问题类型分布（基于1000样本验证）
```
排名   问题类型                        进线数     占比      大促特有
---------------------------------------------------------------------------
1     订单取消/修改                    268      26.8%
2     其他                            208      20.8%
3     免费活动咨询/投诉                 170      17.0%     ✅ 是
4     支付问题                         161      16.1%
5     退款/退货                        103      10.3%
6     账户问题                          72       7.2%
7     订单状态查询                      54       5.4%
8     下单失败/无法下单                  54       5.4%
9     配送查询                          53       5.3%
10    奖励/积分查询                     48       4.8%
...
```

---

## ⚠️ 关键注意事项

### 1. JSON清理是强制的
必须先用 `clean_content()` 清理，否则会误判大量JSON为"其他"类

### 2. 严格匹配大促规则类
"大促规则不清晰/投诉"必须同时满足两个条件：
- 明确提到大促（anniversary sale/522等）
- 明确询问规则（how to/why not me等）

### 3. 多标签分类
单个会话可能属于多个问题类型，不要用 if-elif

### 4. API限流
Chatwoot API请求间隔至少0.2秒

### 5. 异常处理
API失败时继续处理，将content记为空字符串

---

## 🚀 快速执行命令

```bash
# 完整分析流程
python classify_by_issue_type.py

# 查看分类结果详情
python show_detailed_samples.py

# 查看"其他"类案例
python show_other_category.py
```

---

## 📁 相关文件

- `classification_rules_for_agent.md`: 完整分类规则文档
- `classify_by_issue_type.py`: 完整实现代码
- `issue_type_analysis_sample.csv`: 分类结果示例

---

## 🎯 质量检查清单

执行完成后检查：
- [ ] CSV文件包含所有必需字段
- [ ] categories字段是列表格式（不是字符串）
- [ ] is_promo_specific布尔值正确
- [ ] 大促特有问题占比在15-25%之间
- [ ] "其他"类占比低于30%
- [ ] 文本报告包含典型案例
- [ ] 无文字消息单独统计（不计入问题类型分布）
