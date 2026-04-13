#!/usr/bin/env python3
"""
飞书每日消息收集脚本
收集前一天的所有消息并生成工作汇总
"""

import os
import json
import subprocess
from datetime import datetime, timedelta
from collections import defaultdict


def run_command(cmd):
    """执行命令并返回结果"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            return json.loads(result.stdout) if result.stdout else None
        else:
            print(f"命令执行失败: {cmd}")
            print(f"错误: {result.stderr}")
            return None
    except Exception as e:
        print(f"执行出错: {str(e)}")
        return None


def get_yesterday_messages():
    """获取昨天的所有消息"""
    # 计算昨天的时间范围
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start = (today - timedelta(days=1)).strftime('%Y-%m-%dT00:00:00+08:00')
    yesterday_end = (today - timedelta(seconds=1)).strftime('%Y-%m-%dT23:59:59+08:00')

    print(f"📅 获取消息时间范围：{yesterday_start} 到 {yesterday_end}")

    # 搜索昨天的消息
    cmd = f'lark-cli im +messages-search --start "{yesterday_start}" --end "{yesterday_end}" --page-size 50 --as user --format json'

    all_messages = []
    page_token = None
    page_count = 0
    max_pages = 20  # 最多获取20页，避免超时

    while page_count < max_pages:
        page_count += 1
        search_cmd = cmd
        if page_token:
            search_cmd += f' --page-token "{page_token}"'

        print(f"📦 获取第 {page_count} 页消息...")
        result = run_command(search_cmd)

        if not result or not result.get('ok'):
            print(f"❌ 获取失败")
            break

        data = result.get('data', {})
        messages = data.get('messages', [])
        all_messages.extend(messages)

        print(f"   ✓ 获取 {len(messages)} 条消息")

        # 检查是否还有更多
        if not data.get('has_more'):
            break

        page_token = data.get('page_token')

    print(f"\n✅ 总共获取 {len(all_messages)} 条消息")
    return all_messages


def categorize_messages(messages):
    """按群聊分类消息"""
    categorized = defaultdict(list)

    for msg in messages:
        chat_name = msg.get('chat_name', '未知群聊')
        chat_type = msg.get('chat_type', 'unknown')

        # 简化消息内容
        simplified_msg = {
            'time': msg.get('create_time', ''),
            'sender': msg.get('sender', {}).get('name', '未知'),
            'content': msg.get('content', '')[:200],  # 截取前200字符预览
            'msg_type': msg.get('msg_type', 'text')
        }

        key = f"{chat_type}:{chat_name}"
        categorized[key].append(simplified_msg)

    return categorized


def analyze_messages_simple(messages):
    """简单分析（不使用AI）"""
    if not messages:
        return {
            'total_count': 0,
            'summary': '昨天没有消息记录'
        }

    categorized = categorize_messages(messages)

    # 统计信息
    total_chats = len(categorized)
    total_messages = len(messages)

    # 按群聊统计
    chat_stats = []
    for chat_key, msgs in sorted(categorized.items(), key=lambda x: len(x[1]), reverse=True):
        chat_type, chat_name = chat_key.split(':', 1)
        chat_stats.append({
            'name': chat_name,
            'type': chat_type,
            'count': len(msgs),
            'messages': msgs[:10]  # 只保留前10条
        })

    return {
        'total_count': total_messages,
        'total_chats': total_chats,
        'chat_stats': chat_stats,
        'summary': f'共 {total_chats} 个会话，{total_messages} 条消息'
    }


def analyze_messages_ai(messages):
    """使用 Claude API 智能分析"""
    api_key = os.environ.get('CLAUDE_API_KEY')

    if not api_key:
        print("⚠️  未配置 CLAUDE_API_KEY，使用简单分析模式")
        return None

    # TODO: 实现 Claude API 调用
    # 这里预留接口，稍后实现
    print("🤖 Claude API 分析功能待实现...")
    return None


def generate_summary_text(analysis):
    """生成文本格式的汇总"""
    summary = f"""
📊 **每日工作汇总 - {(datetime.now() - timedelta(days=1)).strftime('%Y年%m月%d日')}**

## 📈 总体统计

- 消息总数：{analysis['total_count']} 条
- 会话数量：{analysis['total_chats']} 个

## 💬 主要会话

"""

    for idx, chat in enumerate(analysis['chat_stats'][:10], 1):
        chat_type_emoji = "👥" if chat['type'] == 'group' else "💬"
        summary += f"{idx}. {chat_type_emoji} **{chat['name']}** - {chat['count']} 条消息\n"

    summary += "\n---\n💡 *详细内容请查看完整文档*"

    return summary


def send_to_lark(summary_text, doc_url=None):
    """发送汇总到飞书"""
    user_id = os.environ.get('LARK_USER_ID', 'ou_cc38ac881bcf17d997f0cad7d9a9a621')
    app_id = os.environ.get('LARK_APP_ID')
    app_secret = os.environ.get('LARK_APP_SECRET')

    if not all([app_id, app_secret]):
        print("❌ 缺少飞书配置")
        return False

    # 使用 lark-cli 发送消息
    message = summary_text
    if doc_url:
        message += f"\n\n📄 [查看完整报告]({doc_url})"

    # 转义特殊字符
    message_json = json.dumps({'text': message})

    cmd = f'lark-cli im messages create --receive_id_type open_id --receive_id {user_id} --msg_type text --content \'{message_json}\' --as bot --format json'

    result = run_command(cmd)

    if result and result.get('ok'):
        print("✅ 消息发送成功")
        return True
    else:
        print("❌ 消息发送失败")
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("🚀 开始执行每日工作汇总任务")
    print(f"⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 1. 获取消息
    print("\n📥 步骤 1/4: 获取昨天的消息...")
    messages = get_yesterday_messages()

    if not messages:
        print("⚠️  没有获取到消息，发送空报告")
        summary_text = "📊 昨天没有消息记录"
        send_to_lark(summary_text)
        return

    # 2. 分析消息
    print("\n🔍 步骤 2/4: 分析消息...")
    ai_analysis = analyze_messages_ai(messages)

    if ai_analysis:
        analysis = ai_analysis
        print("   ✓ 使用 AI 智能分析")
    else:
        analysis = analyze_messages_simple(messages)
        print("   ✓ 使用简单统计分析")

    # 3. 生成汇总文本
    print("\n📝 步骤 3/4: 生成汇总报告...")
    summary_text = generate_summary_text(analysis)
    print("   ✓ 报告生成完成")

    # 4. 发送到飞书
    print("\n📤 步骤 4/4: 发送到飞书...")
    send_to_lark(summary_text)

    # 保存到本地（用于调试）
    output_file = f"summary_{datetime.now().strftime('%Y%m%d')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, ensure_ascii=False, indent=2)
    print(f"   ✓ 详细数据已保存到: {output_file}")

    print("\n" + "=" * 60)
    print("✅ 任务执行完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
