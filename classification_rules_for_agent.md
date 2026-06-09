# 522大促客服进线分类规则

## 📋 分类目标

对Chatwoot客服会话按**问题类型**进行分类，标注是否为"大促特有"问题。

---

## 🔧 预处理步骤

### 1. 清理JSON卡片内容

用户消息中包含大量JSON格式的订单卡片，**必须先移除**，只保留用户实际输入的文字：

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

### 2. 判断是否有文字内容

清理后如果没有文字内容（长度<3），归类为**"无文字消息"**或**"发送订单卡片-无文字说明"**。

---

## 📊 分类体系

分为两大类：
1. **🔴 大促特有问题**：只在大促期间出现的特定问题
2. **⚪ 日常问题**：日常运营中的常规问题（大促期间可能增多）

单个会话可能属于**多个问题类型**。

---

## 🔴 大促特有问题（3类）

### 1. 免费活动咨询/投诉

**关键词**：
- 核心关键词：`free sale`, `free day`, `free order`, `free cloth`, `free item`, `get free`
- 简单关键词：`free`, `免费`

**判断逻辑**：
```python
free_keywords = ['free sale', 'free day', 'free order', 'free cloth', 'free item', 'get free']
free_simple = ['free', '免费']

has_free = any(kw in content_lower for kw in free_keywords)

# 如果只包含简单关键词，需要结合上下文
if not has_free:
    if any(kw in content_lower for kw in free_simple):
        # 必须同时提到order/sale等，且在询问/投诉
        if any(word in content_lower for word in ['order', 'sale', 'when', 'how', 'get', 'milne', 'kaise']):
            has_free = True

if has_free:
    categories.append('免费活动咨询/投诉')
    is_promo_specific = True
```

**典型案例**：
- "When my order will get free"
- "Free milne wala tha na bhai do na" (免费的应该给我啊)
- "How to get free order"

---

### 2. 优惠券使用问题

**关键词**：`coupon`, `voucher`, `promo code`, `优惠券`

**判断逻辑**：
```python
coupon_keywords = ['coupon', 'voucher', 'promo code', '优惠券']
if any(kw in content_lower for kw in coupon_keywords):
    categories.append('优惠券使用问题')
    is_promo_specific = True
```

**典型案例**：
- "my coupon has just become useless"
- "Give me coupon for free products"

---

### 3. 大促规则不清晰/投诉

**关键词**：
- 大促明确提及：`anniversary sale`, `mega sale`, `522`, `5.22`, `flash sale`, `free sale`, `free day`
- 规则查询词：`how to get`, `how to use`, `how to participate`, `why not me`, `why don't`, `not eligible`, `terms`, `conditions`, `rules`

**判断逻辑（严格）**：
```python
promo_explicit = ['anniversary sale', 'mega sale', '522', '5.22', 'flash sale', 'free sale', 'free day']
promo_query = [
    'how to get', 'how to use', 'how to participate', 'how to join',
    'why not me', 'why don\'t', 'why i don', 'not eligible',
    'who can', 'terms', 'conditions', 'rules', 'details',
    '为什么我没有', '怎么参加', '如何获得', '规则'
]

# 必须同时满足两个条件
has_promo_mention = any(kw in content_lower for kw in promo_explicit)
has_promo_query = any(kw in content_lower for kw in promo_query)

if has_promo_mention and has_promo_query:
    categories.append('大促规则不清晰/投诉')
    is_promo_specific = True
```

**典型案例**：
- "Why you don't give me free offer... Anniversary sale"
- "how to get free sale"

---

## ⚪ 日常问题（17类）

### 4. 订单取消/修改

**关键词**：`cancel`

**判断逻辑**：
```python
if 'cancel' in content_lower:
    categories.append('订单取消/修改')
```

**典型案例**：
- "I want to cancel it i ordered it by mistake"
- "Cancel my order"

---

### 5. 退款/退货

**关键词**：`refund`, `return`, `exchange`, `退款`, `退货`

**判断逻辑**：
```python
refund_keywords = ['refund', 'return', 'exchange', '退款', '退货']
if any(kw in content_lower for kw in refund_keywords):
    categories.append('退款/退货')
```

**典型案例**：
- "Where is my refund"
- "When will I get my refund?"

---

### 6. 配送查询

**关键词**：`delivery`, `shipping`, `dispatch`, `tracking`, `shipped`, `配送`, `物流`, `发货`

**判断逻辑**：
```python
delivery_keywords = ['delivery', 'shipping', 'dispatch', 'tracking', 'shipped', '配送', '物流', '发货']
if any(kw in content_lower for kw in delivery_keywords):
    categories.append('配送查询')
```

**典型案例**：
- "When will my order be shipped"
- "Tracking information"

---

### 7. 支付问题

**关键词**：`payment`, `paid`, `pay`, `debited`, `money`, `cash on delivery`, `cod`, `支付`, `付款`

**判断逻辑**：
```python
payment_keywords = ['payment', 'paid', 'pay', 'debited', 'money', 'cash on delivery', 'cod', '支付', '付款']
if any(kw in content_lower for kw in payment_keywords):
    # 排除已归类为退款的
    if '退款/退货' not in categories:
        categories.append('支付问题')
```

**典型案例**：
- "money has been debited but order not confirmed"
- "I have selected cash on delivery"

---

### 8. 技术问题-App崩溃/卡顿

**关键词**：`crash`, `not working`, `error`, `network`, `unavailable`, `lag`, `freeze`, `slow`, `crashed`

**判断逻辑**：
```python
tech_keywords = ['crash', 'not working', 'error', 'network', 'unavailable', 'lag', 'freeze', 'slow', 'crashed']
if any(kw in content_lower for kw in tech_keywords):
    categories.append('技术问题-App崩溃/卡顿')
```

**特殊标注**：⚠️ **大促期间集中爆发**

**典型案例**：
- "APP is not working"
- "Savana app is crashed?"

---

### 9. 商品咨询

**关键词**：`size`, `color`, `material`, `fabric`, `quality`, `尺码`, `颜色`, `材质`

**排除条件**：不包含价格相关词汇

**判断逻辑**：
```python
product_keywords = ['size', 'color', 'material', 'fabric', 'quality', '尺码', '颜色', '材质']
price_keywords = ['price', 'discount', 'offer', '价格', '折扣']

if any(kw in content_lower for kw in product_keywords):
    if not any(kw in content_lower for kw in price_keywords):
        categories.append('商品咨询')
```

---

### 10. 账户问题

**关键词**：`account`, `login`, `password`, `email`, `phone`, `wallet`, `账户`, `密码`, `钱包`

**判断逻辑**：
```python
account_keywords = ['account', 'login', 'password', 'email', 'phone', 'wallet', '账户', '密码', '钱包']
if any(kw in content_lower for kw in account_keywords):
    categories.append('账户问题')
```

---

### 11. 订单状态查询

**关键词**：`where is my`, `order status`, `track`, `parcel`, `not received`, `not delivered`, `when will`, `kab tak`, `details of my order`

**排除条件**：不与"配送查询"重复

**判断逻辑**：
```python
order_status_keywords = [
    'where is my', 'order status', 'track', 'parcel', 'not received',
    'not delivered', 'when will', 'kab tak', 'details of my order',
    '订单在哪', '物流信息'
]
if any(kw in content_lower for kw in order_status_keywords):
    if '配送查询' not in categories:
        categories.append('订单状态查询')
```

**典型案例**：
- "Please provide details of my order"
- "Where is my parcel"

---

### 12. 下单失败/无法下单

**关键词**：`unable to order`, `can't order`, `cannot place`, `place order`, `not showing`, `can't open cart`, `out of stock`, `not available`

**判断逻辑**：
```python
order_fail_keywords = [
    'unable to order', 'can\'t order', 'cannot place', 'place order',
    'not showing', 'can\'t open cart', 'cart not', 'out of stock',
    'not available', '无法下单', '下单失败'
]
if any(kw in content_lower for kw in order_fail_keywords):
    categories.append('下单失败/无法下单')
```

**典型案例**：
- "I am unable to order"
- "place order option is not showing"

---

### 13. 地址修改

**关键词**：`change address`, `change my address`, `update address`, `wrong address`, `deliver on`, `修改地址`

**判断逻辑**：
```python
address_keywords = ['change address', 'change my address', 'update address', 'wrong address', 'deliver on', '修改地址']
if any(kw in content_lower for kw in address_keywords):
    categories.append('地址修改')
```

---

### 14. 奖励/积分查询

**关键词**：
- 主词：`reward`, `gift`, `points`, `wallet`, `奖励`, `积分`, `礼物`
- 查询词：`how to`, `where is`, `when`, `received`, `get`, `see`, `如何`, `怎么`

**排除条件**：不与"大促规则"或"免费活动"重复

**判断逻辑**：
```python
reward_keywords = ['reward', 'gift', 'points', 'wallet', '奖励', '积分', '礼物']
reward_query = ['how to', 'where is', 'when', 'received', 'get', 'see', '如何', '怎么']

if any(kw in content_lower for kw in reward_keywords):
    if any(q in content_lower for q in reward_query):
        if '大促规则不清晰/投诉' not in categories and '免费活动咨询/投诉' not in categories:
            categories.append('奖励/积分查询')
```

**典型案例**：
- "How to see the reward"
- "Why haven't i received the reward yet?"

---

### 15. 负面投诉

**关键词**：`bad experience`, `disappointed`, `hate`, `fraud`, `worst`, `terrible`, `horrible`, `useless`, `waste`, 脏话

**判断逻辑**：
```python
negative_keywords = [
    'bad experience', 'disappointed', 'hate', 'fraud', 'worst',
    'terrible', 'horrible', 'useless', 'waste', 'shit', 'fuck',
    '很差', '太差', '垃圾', '骗人'
]
if any(kw in content_lower for kw in negative_keywords):
    categories.append('负面投诉')
```

**典型案例**：
- "very bad experience"
- "I hate you savana"

---

### 16. KOL合作请求

**关键词**：`content creator`, `influencer`, `collaborate`, `collaboration`, `work together`, `partnership`, `brand ambassador`, `promote`

**判断逻辑**：
```python
collab_keywords = [
    'content creator', 'influencer', 'collaborate', 'collaboration',
    'work together', 'partnership', 'brand ambassador', 'promote'
]
if any(kw in content_lower for kw in collab_keywords):
    categories.append('KOL合作请求')
```

---

### 17. 社交/祝福

**关键词**：`happy birthday`, `mentioned you in`, `congratulations`, `proud of you`, `wish you`, `生日快乐`, `祝福`

**判断逻辑**：
```python
social_keywords = [
    'happy birthday', 'mentioned you in', 'congratulations',
    'proud of you', 'wish you', '生日快乐', '祝福'
]
if any(kw in content_lower for kw in social_keywords):
    categories.append('社交/祝福')
```

---

### 18. 问候/寒暄

**关键词**：`hello`, `hi`, `hey`, `thank you`, `thanks`

**附加条件**：内容很短（<50字符）

**判断逻辑**：
```python
greetings = ['hello', 'hi', 'hey', 'thank you', 'thanks']
if any(kw in content_lower for kw in greetings) and len(content_text) < 50:
    categories.append('问候/寒暄')
```

---

### 19. 其他

如果经过所有分类判断后，仍然没有任何分类，则归为**"其他"**。

---

## 🎯 分类流程

```python
def classify_by_issue_type(content):
    # 1. 清理JSON
    content_text = clean_content(content)

    # 2. 检查是否有文字
    if not content_text or len(content_text) < 3:
        return ['无文字消息'], False

    content_lower = content_text.lower()
    categories = []
    is_promo_specific = False

    # 3. 按顺序判断（大促特有问题优先）
    # 3.1 免费活动
    # 3.2 优惠券
    # 3.3 大促规则
    # 3.4 订单取消
    # 3.5 退款退货
    # 3.6 配送查询
    # 3.7 支付问题
    # 3.8 技术问题
    # 3.9 商品咨询
    # 3.10 账户问题
    # 3.11 订单状态
    # 3.12 下单失败
    # 3.13 地址修改
    # 3.14 奖励积分
    # 3.15 负面投诉
    # 3.16 KOL合作
    # 3.17 社交祝福
    # 3.18 问候寒暄
    # 3.19 其他

    # 4. 返回结果
    return categories, is_promo_specific
```

---

## ⚠️ 注意事项

1. **多标签分类**：单个会话可能属于多个类型
2. **JSON清理是强制的**：必须先清理再分析
3. **严格匹配**："大促规则不清晰/投诉"需要同时满足两个条件
4. **去重逻辑**：某些类型需要避免与其他类型重复（见具体判断逻辑）
5. **大小写不敏感**：所有关键词匹配都应该用 `content_lower`

---

## 📈 预期分布（基于1,000条样本）

### 大促特有问题：19.6%
- 免费活动咨询/投诉：17.0%
- 优惠券使用问题：3.2%
- 大促规则不清晰/投诉：1.5%

### 日常问题 Top 10：
1. 订单取消/修改：26.8%
2. 其他：20.8%
3. 支付问题：16.1%
4. 退款/退货：10.3%
5. 账户问题：7.2%
6. 订单状态查询：5.4%
7. 下单失败/无法下单：5.4%
8. 配送查询：5.3%
9. 奖励/积分查询：4.8%
10. 技术问题-App崩溃/卡顿：4.0% ⚠️

---

## ✅ 交付要求

分析完成后，请提供：

1. **总体统计**：
   - 样本总数
   - 有文字内容的会话数
   - 大促特有问题数量及占比

2. **问题类型分布表**：
   - 按进线量排序
   - 显示每个类型的数量和占比
   - 标注是否为"大促特有"

3. **大促特有问题详细分析**：
   - 每个类型的详细数据
   - 2-3个典型案例（带会话ID和原文）

4. **日常问题 Top 10**：
   - 按进线量排序
   - 特别标注"技术问题-App崩溃/卡顿"为"大促期间集中爆发"

5. **数据文件**：
   - CSV格式，包含字段：
     - conversation_id
     - created_at
     - hour
     - categories (列表)
     - is_promo_specific (布尔值)
     - content_preview (前200字符)
