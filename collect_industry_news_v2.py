#!/usr/bin/env python3
"""
每日Savana业内动态推送 v2.0
- 使用Serper API提升稳定性
- 智能去重避免重复行动点
- 符合Savana品牌调性
- 追踪持续性话题
"""

import os
import json
import subprocess
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Set


# ===== 配置 =====
LARK_USER_ID = 'ou_cc38ac881bcf17d997f0cad7d9a9a621'
NEWS_PER_SECTION = 10
HISTORY_DAYS = 7  # 保留最近7天的行动点历史

# Serper API配置（主要）
SERPER_API_KEY = os.environ.get('SERPER_API_KEY', '')
SERPER_API_URL = 'https://google.serper.dev/search'

# 搜索关键词（优化后，更聚焦竞对动态）
SEARCH_QUERIES = {
    'india_competitors': [
        'Myntra new features product launch 2026',
        'Meesho marketing campaign India',
        'Ajio fashion sale promotion',
        'Flipkart Fashion technology AI',
        'Nykaa Fashion business strategy',
        'Shein India expansion'
    ],
    'iraq_competitors': [
        'Chicpoint Iraq ecommerce',
        'Trendyol Middle East Iraq',
        'Miswag online shopping',
        'Namshi fashion Kuwait Iraq',
        'Noon Middle East expansion'
    ],
    'tech_trends': [
        'AI size recommendation fashion ecommerce',
        'virtual try-on technology fashion',
        'fashion ecommerce personalization AI',
        'reduce return rate ecommerce solution'
    ],
    'business_trends': [
        'fashion ecommerce COD Middle East',
        'BNPL buy now pay later India Iraq',
        'fashion ecommerce logistics optimization',
        'sustainable fashion trend 2026'
    ]
}

# Savana业务上下文
SAVANA_CONTEXT = """
Savana是面向印度和伊拉克年轻女性的时尚电商平台。

品牌调性：简单、快速、包容、真实、不制造焦虑

当前关注点：
- 退货率优化：尺码问题占61%，正在开发AI尺码推荐MVP
- 伊拉克站挑战：COD为主，拒收率高
- 用户画像：年轻女性，注重性价比，喜欢探索新趋势
- 主要竞对：
  * 印度：Myntra, Meesho, Ajio, Flipkart Fashion, Nykaa Fashion, Shein
  * 伊拉克：Chicpoint, Trendyol, Miswag, Namshi, Noon
"""

# AI总结prompt（符合品牌调性）
SUMMARY_PROMPT = """你是Savana的竞争情报分析师。根据今日新闻和历史行动点，生成每日业内动态推送。

## Savana背景
{context}

## 最近7天的行动点（用于去重）
{history_actions}

## 今日搜索到的新闻
{news_raw}

## 输出要求

### 品牌调性规范（重要！）
- 语气：友好真诚，像朋友聊天
- 表达：简洁直接，不夸大
- 禁用词：完美、最好、紧急、立即、必须
- 推荐词：发现、探索、尝试、简单、值得关注

### 内容结构

## 🌐 Savana 业内动态 | {date}

### 🆕 今日新发现

（3-4条**今天才发现的**动态，不要重复历史行动点中已提过的话题）

1. **简短标题** - 一句话说清楚，与Savana的关系
2. **简短标题** - 同上
3. **简短标题** - 同上

### 💡 值得关注的行动点

| # | 行动建议 | 原因 |
|---|---------|------|
| 1 | 简洁的建议（避免重复历史） | 为什么值得做 |
| 2 | ... | ... |

💡 **去重规则**：如果某个行动点在最近7天已经提过2次以上，本次不要再重复

### 🔄 持续跟进

（如果某个话题在历史中出现过2次以上，标注为持续跟进，提醒"已连续X天出现"）

例如：
- **AI尺码推荐** - 已连续5天出现，竞品Myntra/Nykaa持续发布新功能

### 📰 动态原文

**🇮🇳 印度竞对**

1. 新闻标题（中文简述）
   → [来源](URL)

**🇮🇶 伊拉克竞对**

1. 新闻标题（中文简述）
   → [来源](URL)

**🌍 行业趋势**

1. 新闻标题（中文简述）
   → [来源](URL)

---

## 注意事项
- 遵守品牌调性，文案友好真实，不夸大
- "新发现"只写今天首次出现的话题
- 行动点要具体、简洁，避免重复
- 持续跟进的话题要明确标注
- 不要使用markdown代码块包裹输出
"""


# ===== 历史记录管理 =====

def load_history_actions() -> Dict[str, List[str]]:
    """加载最近7天的行动点历史"""
    history = {}

    for i in range(HISTORY_DAYS):
        date = datetime.now() - timedelta(days=i+1)
        filename = f"news_{date.strftime('%Y%m%d')}.md"
        filepath = Path(filename)

        if not filepath.exists():
            continue

        try:
            content = filepath.read_text(encoding='utf-8')
            # 提取行动点
            actions = extract_actions_from_content(content)
            if actions:
                history[date.strftime('%Y-%m-%d')] = actions
        except Exception as e:
            print(f"   ⚠️ 读取历史文件失败 {filename}: {e}")

    return history


def extract_actions_from_content(content: str) -> List[str]:
    """从历史内容中提取行动点"""
    actions = []

    # 简单提取：找到表格中的行动建议
    lines = content.split('\n')
    in_action_table = False

    for line in lines:
        if '行动建议' in line or '行动点' in line:
            in_action_table = True
            continue

        if in_action_table:
            if line.strip().startswith('|') and not line.strip().startswith('|---|'):
                # 提取表格行
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 3 and parts[2]:  # 第2列是行动建议
                    action = parts[2].strip()
                    if action and action != '行动建议' and not action.startswith('-'):
                        actions.append(action)
            elif line.strip() and not line.strip().startswith('|'):
                # 离开表格
                in_action_table = False

    return actions


def format_history_for_prompt(history: Dict[str, List[str]]) -> str:
    """格式化历史行动点为prompt输入"""
    if not history:
        return "（无历史记录）"

    parts = []
    for date in sorted(history.keys(), reverse=True):
        actions = history[date]
        parts.append(f"\n{date}:")
        for action in actions[:5]:  # 每天最多显示5条
            parts.append(f"  - {action}")

    return '\n'.join(parts)


# ===== 新闻搜索 =====

def search_with_serper(query: str, num_results: int = 5) -> List[Dict]:
    """使用Serper API搜索（主要方式）"""
    if not SERPER_API_KEY:
        print("   ⚠️ 未配置SERPER_API_KEY，跳过")
        return []

    try:
        headers = {
            'X-API-KEY': SERPER_API_KEY,
            'Content-Type': 'application/json'
        }

        payload = {
            'q': query,
            'num': num_results,
            'gl': 'us',  # geo location
            'hl': 'en'   # language
        }

        resp = requests.post(
            SERPER_API_URL,
            headers=headers,
            json=payload,
            timeout=15
        )

        if resp.status_code == 200:
            data = resp.json()
            results = []

            # 提取organic results
            for item in data.get('organic', [])[:num_results]:
                results.append({
                    'title': item.get('title', ''),
                    'url': item.get('link', ''),
                    'snippet': item.get('snippet', '')
                })

            return results
        else:
            print(f"   ⚠️ Serper API错误 [{resp.status_code}]: {resp.text[:100]}")
            return []

    except Exception as e:
        print(f"   ⚠️ Serper搜索失败: {e}")
        return []


def search_with_google_news_rss(query: str, num_results: int = 5) -> List[Dict]:
    """使用Google News RSS（fallback）"""
    try:
        from urllib.parse import quote_plus
        url = f"https://news.google.com/rss/search?q={quote_plus(query)}&hl=en&gl=US&ceid=US:en"

        resp = requests.get(url, timeout=15, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'
        })

        if resp.status_code != 200:
            return []

        import re
        items = re.findall(r'<item>.*?</item>', resp.text, re.DOTALL)
        results = []

        for item in items[:num_results]:
            title = re.search(r'<title>(.*?)</title>', item)
            link = re.search(r'<link/>(.*?)<', item) or re.search(r'<link>(.*?)</link>', item)

            if title:
                results.append({
                    'title': title.group(1).strip(),
                    'url': link.group(1).strip() if link else '',
                    'snippet': ''
                })

        return results

    except Exception as e:
        print(f"   ⚠️ RSS搜索失败: {e}")
        return []


def gather_all_news() -> Dict[str, List[Dict]]:
    """收集所有新闻"""
    all_news = {}

    for category, queries in SEARCH_QUERIES.items():
        print(f"\n🔍 搜索 {category}...")
        category_news = []

        for query in queries:
            print(f"   → {query[:50]}...")

            # 优先使用Serper
            results = search_with_serper(query, num_results=3)

            # fallback到RSS
            if not results:
                results = search_with_google_news_rss(query, num_results=2)

            category_news.extend(results)
            print(f"     ✓ {len(results)}条")

        all_news[category] = category_news

    # 去重
    for category in all_news:
        seen_urls = set()
        unique = []
        for item in all_news[category]:
            url = item.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique.append(item)
        all_news[category] = unique

    return all_news


def format_news_for_prompt(all_news: Dict) -> str:
    """格式化新闻为prompt输入"""
    parts = []

    for category, news_list in all_news.items():
        parts.append(f"\n### {category}")

        if not news_list:
            parts.append("（无搜索结果）")
        else:
            for i, item in enumerate(news_list[:10], 1):
                parts.append(f"\n{i}. {item['title']}")
                if item.get('snippet'):
                    parts.append(f"   {item['snippet']}")
                if item.get('url'):
                    parts.append(f"   {item['url']}")

    return '\n'.join(parts)


# ===== AI生成 =====

def generate_summary_with_ai(news_raw: str, history_actions: str) -> str:
    """调用AI生成推送内容"""
    today_str = datetime.now().strftime('%m月%d日')

    prompt = SUMMARY_PROMPT.format(
        context=SAVANA_CONTEXT,
        history_actions=history_actions,
        news_raw=news_raw,
        date=today_str
    )

    api_base = os.environ.get('ANTHROPIC_BASE_URL', 'https://litellm-sg.mayfair-inc.com')
    api_key = os.environ.get('ANTHROPIC_AUTH_TOKEN', '')
    model = os.environ.get('ANTHROPIC_MODEL', 'claude-sonnet-4-5-20250929')

    if not api_key:
        print("   ❌ 未配置ANTHROPIC_AUTH_TOKEN")
        return None

    print("\n🤖 AI正在生成推送...")

    try:
        resp = requests.post(
            f"{api_base}/v1/messages",
            headers={
                'Content-Type': 'application/json',
                'x-api-key': api_key,
                'anthropic-version': '2023-06-01'
            },
            json={
                'model': model,
                'max_tokens': 4096,
                'messages': [{'role': 'user', 'content': prompt}]
            },
            timeout=120
        )

        if resp.status_code == 200:
            data = resp.json()
            content = data.get('content', [{}])[0].get('text', '')

            if content:
                # 清理可能的markdown代码块
                if content.startswith('```'):
                    lines = content.split('\n')
                    content = '\n'.join(lines[1:-1] if lines[-1].startswith('```') else lines[1:])

                print("   ✅ 生成完成")
                return content
            else:
                print("   ❌ AI返回空内容")
                return None
        else:
            print(f"   ❌ API调用失败 [{resp.status_code}]: {resp.text[:200]}")
            return None

    except requests.Timeout:
        print("   ❌ AI生成超时")
        return None
    except Exception as e:
        print(f"   ❌ AI生成出错: {e}")
        return None


def generate_fallback_summary(all_news: Dict) -> str:
    """兜底：AI失败时使用模板"""
    today_str = datetime.now().strftime('%m月%d日')

    parts = [f"## 🌐 Savana 业内动态 | {today_str}\n"]
    parts.append("### 📰 今日动态\n")

    # 合并所有新闻
    for category, news_list in all_news.items():
        if news_list:
            parts.append(f"**{category}**\n")
            for i, item in enumerate(news_list[:8], 1):
                title = item.get('title', '').strip()
                url = item.get('url', '')
                if title:
                    if url:
                        parts.append(f"{i}. {title}\n   → [{url[:50]}...]({url})\n")
                    else:
                        parts.append(f"{i}. {title}\n")
            parts.append("")

    parts.append("---\n*⚠️ AI分析暂时不可用，稍后补充*")
    return '\n'.join(parts)


# ===== 发送 =====

def send_to_lark(content: str) -> bool:
    """发送到飞书"""
    print("\n📤 发送到飞书...")

    try:
        process = subprocess.Popen(
            ['lark-cli', 'im', '+messages-send',
             '--user-id', LARK_USER_ID,
             '--text', content,
             '--as', 'bot'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        stdout, stderr = process.communicate(timeout=30)

        if process.returncode == 0 and stdout:
            result = json.loads(stdout)
            if result.get('ok'):
                print("   ✅ 推送成功")
                return True
            else:
                print(f"   ❌ 推送失败: {result.get('error', {})}")
                return False
        else:
            print(f"   ❌ 推送失败: {stderr[:200]}")
            return False

    except Exception as e:
        print(f"   ❌ 推送异常: {e}")
        return False


# ===== 主流程 =====

def main():
    print("=" * 70)
    print("🌐 Savana 业内动态推送 v2.0")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # Step 1: 加载历史行动点
    print("\n📚 步骤 1/4: 加载历史行动点...")
    history = load_history_actions()
    print(f"   ✓ 加载了最近{len(history)}天的历史记录")

    # Step 2: 搜索新闻
    print("\n📥 步骤 2/4: 搜索行业新闻...")
    all_news = gather_all_news()
    total = sum(len(v) for v in all_news.values())
    print(f"\n   ✓ 共收集{total}条新闻")

    # Step 3: AI生成
    print("\n📝 步骤 3/4: 生成推送内容...")
    news_raw = format_news_for_prompt(all_news)
    history_text = format_history_for_prompt(history)

    summary = generate_summary_with_ai(news_raw, history_text)

    if not summary:
        print("   ⚠️ 使用兜底模板")
        summary = generate_fallback_summary(all_news)

    # Step 4: 发送
    print("\n📤 步骤 4/4: 推送到飞书...")
    send_to_lark(summary)

    # 保存本地
    output_file = f"news_{datetime.now().strftime('%Y%m%d')}.md"
    Path(output_file).write_text(summary, encoding='utf-8')
    print(f"   ✓ 已保存: {output_file}")

    print("\n" + "=" * 70)
    print("✅ 推送完成")
    print("=" * 70)


if __name__ == "__main__":
    main()
