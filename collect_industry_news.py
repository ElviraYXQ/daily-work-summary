#!/usr/bin/env python3
"""
每日竞对/行业动态推送脚本
搜索最新行业新闻，AI 总结后推送到飞书
"""

import os
import json
import subprocess
import requests
from datetime import datetime, timedelta
from urllib.parse import quote_plus


# 配置
LARK_USER_ID = 'ou_cc38ac881bcf17d997f0cad7d9a9a621'
NEWS_PER_SECTION = 10

# 搜索关键词
SEARCH_QUERIES = {
    'india': [
        'India women fashion ecommerce 2026',
        'Meesho Myntra Ajio fashion size recommendation',
        'India online fashion return rate size fit',
        'Flipkart Nykaa fashion AI technology',
        'India ecommerce fashion trends',
    ],
    'iraq': [
        'Iraq ecommerce market 2026',
        'Iraq online shopping COD payment',
        'Iraq digital payment ZainCash',
        'Middle East Iraq fashion ecommerce',
        'Kurdistan online shopping women fashion',
    ],
    'global': [
        'SHEIN Temu Middle East expansion 2026',
        'fashion ecommerce size recommendation AI',
        'online fashion return rate solution',
        'BNPL buy now pay later Middle East',
        'Zara H&M ecommerce AI technology 2026',
    ]
}

# Savana 业务上下文（给 AI 做总结用）
SAVANA_CONTEXT = """
Savana 是一家面向印度和伊拉克女性用户的时尚电商平台。
核心业务指标：
- 当前退货率较高，尺码问题占退货原因的 61%
- 正在开发 AI 尺码推荐 MVP（基于已购用户身材数据做相似用户推荐）
- 伊拉克站（IQ）以 COD 为主，面临拒收挑战
- 目标用户：年轻女性，关注性价比和穿搭
- 竞对：Meesho, Myntra, Ajio, SHEIN, Miswag, Orisdi
"""

SUMMARY_PROMPT = """你是 Savana 的竞争情报分析师。根据以下搜索到的行业新闻，生成每日竞对动态推送。

## Savana 背景
{context}

## 今日搜索到的新闻
{news_raw}

## 输出格式要求

严格按以下格式输出，不要添加额外标记：

## 🌐 Savana 业内动态 | {date}

### 📌 中文概览

**本日与 Savana 最相关的动态：**

1. **标题** — 一句话中文概要，说明与 Savana 的关联
2. **标题** — 一句话中文概要
3. **标题** — 一句话中文概要
4. **标题** — 一句话中文概要（如有）

---

### 🎯 Savana 行动点

| # | 行动建议 | 优先级 |
|---|---------|--------|
| 1 | 具体可执行的建议 | P0/P1/P2 |
| 2 | ... | ... |
| 3 | ... | ... |

---

### 📰 动态详情

**🇮🇳 印度市场**

1. 新闻标题或一句话摘要
   → [来源名](URL)

...（约10条）

**🇮🇶 伊拉克市场**

1. 新闻标题或一句话摘要
   → [来源名](URL)

...（约10条）

**🌍 全球/中东趋势**

1. 新闻标题或一句话摘要
   → [来源名](URL)

...（约10条）

---

## 注意事项
- 中文概览只总结与 Savana 业务最相关的 3-4 条
- 行动点要具体、可执行，标注优先级
- 详情部分每个区域约 10 条，保留原始来源链接
- 如果搜索结果中某些新闻不够相关或过时，可用行业已知动态补充，但标注"综合整理"
- 所有内容用中文，新闻标题可中英混合
- 不要使用 markdown 代码块包裹输出
"""


def search_news(query, num_results=5):
    """使用 DuckDuckGo 搜索新闻"""
    url = "https://html.duckduckgo.com/html/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }

    try:
        resp = requests.post(url, data={'q': query, 'df': 'w'}, headers=headers, timeout=15)
        if resp.status_code != 200:
            return []

        # 简单提取搜索结果
        results = []
        text = resp.text

        # 提取结果链接和标题
        import re
        # DuckDuckGo HTML results pattern
        links = re.findall(r'<a rel="nofollow" class="result__a" href="([^"]+)"[^>]*>(.*?)</a>', text)
        snippets = re.findall(r'<a class="result__snippet"[^>]*>(.*?)</a>', text)

        for i, (link, title) in enumerate(links[:num_results]):
            title_clean = re.sub(r'<[^>]+>', '', title).strip()
            snippet = re.sub(r'<[^>]+>', '', snippets[i]).strip() if i < len(snippets) else ''
            results.append({
                'title': title_clean,
                'url': link,
                'snippet': snippet
            })

        return results

    except Exception as e:
        print(f"   ⚠️ 搜索失败 [{query}]: {e}")
        return []


def search_news_alt(query, num_results=5):
    """备用搜索：使用 Google News RSS"""
    try:
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
        print(f"   ⚠️ RSS 搜索失败 [{query}]: {e}")
        return []


def gather_all_news():
    """收集所有区域的新闻"""
    all_news = {'india': [], 'iraq': [], 'global': []}

    for region, queries in SEARCH_QUERIES.items():
        print(f"\n🔍 搜索 {region} 市场新闻...")
        for query in queries:
            print(f"   → {query}")
            results = search_news(query, num_results=4)
            if not results:
                # fallback to Google News RSS
                results = search_news_alt(query, num_results=3)
            all_news[region].extend(results)
            print(f"     找到 {len(results)} 条")

    # 去重（按 URL）
    for region in all_news:
        seen_urls = set()
        unique = []
        for item in all_news[region]:
            url = item.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique.append(item)
        all_news[region] = unique

    return all_news


def format_news_for_prompt(all_news):
    """将新闻格式化为 prompt 输入"""
    parts = []

    for region, label in [('india', '印度市场'), ('iraq', '伊拉克市场'), ('global', '全球/中东')]:
        parts.append(f"\n### {label}")
        news_list = all_news.get(region, [])
        if not news_list:
            parts.append("（无搜索结果，请基于行业知识补充）")
        else:
            for i, item in enumerate(news_list[:15], 1):
                parts.append(f"{i}. {item['title']}")
                if item.get('snippet'):
                    parts.append(f"   摘要: {item['snippet']}")
                if item.get('url'):
                    parts.append(f"   链接: {item['url']}")

    return '\n'.join(parts)


def generate_summary_with_ai(news_raw):
    """调用 AI 生成结构化推送内容（直接调 API）"""
    today_str = datetime.now().strftime('%m月%d日')

    prompt = SUMMARY_PROMPT.format(
        context=SAVANA_CONTEXT,
        news_raw=news_raw,
        date=today_str
    )

    api_base = os.environ.get('ANTHROPIC_BASE_URL', 'https://litellm-sg.mayfair-inc.com')
    api_key = os.environ.get('ANTHROPIC_AUTH_TOKEN', '')
    model = os.environ.get('ANTHROPIC_MODEL', 'claude-sonnet-4-5-20250929')

    if not api_key:
        print("   ❌ 未配置 ANTHROPIC_AUTH_TOKEN")
        return None

    print("\n🤖 AI 正在生成推送内容...")
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
                # 去掉可能的 markdown 代码块包裹
                if content.startswith('```'):
                    lines = content.split('\n')
                    content = '\n'.join(lines[1:-1] if lines[-1].startswith('```') else lines[1:])
                print("   ✓ 生成完成")
                return content
            else:
                print("   ❌ AI 返回空内容")
                return None
        else:
            print(f"   ❌ API 调用失败 [{resp.status_code}]: {resp.text[:200]}")
            return None

    except requests.Timeout:
        print("   ❌ AI 生成超时")
        return None
    except Exception as e:
        print(f"   ❌ AI 生成出错: {e}")
        return None


def generate_fallback_summary(all_news):
    """兜底：如果 AI 生成失败，用模板直接格式化"""
    today_str = datetime.now().strftime('%m月%d日')

    parts = [f"## 🌐 Savana 业内动态 | {today_str}\n"]
    parts.append("### 📰 动态详情\n")

    for region, label, emoji in [
        ('india', '印度市场', '🇮🇳'),
        ('iraq', '伊拉克市场', '🇮🇶'),
        ('global', '全球/中东趋势', '🌍')
    ]:
        parts.append(f"**{emoji} {label}**\n")
        news_list = all_news.get(region, [])
        for i, item in enumerate(news_list[:NEWS_PER_SECTION], 1):
            title = item.get('title', '').strip()
            url = item.get('url', '')
            if title:
                if url:
                    parts.append(f"{i}. {title}\n   → [{url[:50]}...]({url})\n")
                else:
                    parts.append(f"{i}. {title}\n")
        parts.append("")

    parts.append("---\n*⚠️ AI 概览生成失败，仅展示原始搜索结果*")
    return '\n'.join(parts)


def send_to_lark(content):
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
                print("   ✅ 推送发送成功")
                return True
            else:
                print(f"   ❌ 发送失败: {result.get('error', {})}")
                return False
        else:
            print(f"   ❌ 发送失败: {stderr[:200]}")
            return False

    except Exception as e:
        print(f"   ❌ 发送异常: {e}")
        return False


def main():
    print("=" * 60)
    print("🌐 每日竞对动态推送")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 1. 搜索新闻
    print("\n📥 步骤 1/3: 搜索行业新闻...")
    all_news = gather_all_news()

    total = sum(len(v) for v in all_news.values())
    print(f"\n   ✓ 共搜集 {total} 条新闻")

    # 2. AI 生成推送内容
    print("\n📝 步骤 2/3: 生成推送内容...")
    news_raw = format_news_for_prompt(all_news)

    summary = generate_summary_with_ai(news_raw)

    if not summary:
        print("   ⚠️ 使用兜底模板")
        summary = generate_fallback_summary(all_news)

    # 3. 发送
    print("\n📤 步骤 3/3: 推送到飞书...")
    send_to_lark(summary)

    # 保存本地记录
    output_file = f"news_{datetime.now().strftime('%Y%m%d')}.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(summary)
    print(f"   ✓ 内容已保存到: {output_file}")

    print("\n" + "=" * 60)
    print("✅ 竞对动态推送完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
