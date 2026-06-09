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
    """获取昨天的所有消息（周一时获取周五-周日）"""
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    # 判断今天是否是周一（weekday() == 0）
    if today.weekday() == 0:
        # 周一：获取周五、周六、周日的消息
        friday = today - timedelta(days=3)
        start_time = friday.strftime('%Y-%m-%dT00:00:00+08:00')
        end_time = (today - timedelta(seconds=1)).strftime('%Y-%m-%dT23:59:59+08:00')
        print(f"📅 今天是周一，获取周末消息（周五-周日）")
    else:
        # 其他日期：获取昨天的消息
        yesterday_start = today - timedelta(days=1)
        start_time = yesterday_start.strftime('%Y-%m-%dT00:00:00+08:00')
        end_time = (today - timedelta(seconds=1)).strftime('%Y-%m-%dT23:59:59+08:00')

    print(f"📅 获取消息时间范围：{start_time} 到 {end_time}")

    # 搜索消息
    cmd = f'lark-cli im +messages-search --start "{start_time}" --end "{end_time}" --page-size 50 --as user --format json'

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


def is_message_relevant(msg, user_name="易希倩 Queenie Yi", user_id="ou_cc38ac881bcf17d997f0cad7d9a9a621"):
    """判断消息是否与用户相关"""

    # 1. 如果是用户自己发的消息，肯定相关
    sender = msg.get('sender', {})
    sender_id = sender.get('id', '')
    sender_name = sender.get('name', '')

    if sender_id == user_id or sender_name == user_name:
        return True

    # 2. 检查消息内容是否@了用户
    content = msg.get('content', '')

    # 检查多种@格式
    at_patterns = [
        f"@{user_name}",           # @易希倩 Queenie Yi
        f"@易希倩",                 # @易希倩
        f"@Queenie Yi",            # @Queenie Yi
        f"@Queenie",               # @Queenie
        f"ou_cc38ac881bcf17d997f0cad7d9a9a621",  # open_id
    ]

    for pattern in at_patterns:
        if pattern in content:
            return True

    # 3. 对于私聊消息，都相关
    chat_type = msg.get('chat_type', '')
    if chat_type == 'p2p':
        return True

    return False


def filter_relevant_messages(messages):
    """过滤出与用户相关的消息"""
    relevant = []
    filtered_count = 0

    for msg in messages:
        if is_message_relevant(msg):
            relevant.append(msg)
        else:
            filtered_count += 1

    print(f"   ✓ 过滤掉 {filtered_count} 条无关消息")
    print(f"   ✓ 保留 {len(relevant)} 条相关消息")

    return relevant


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
            'msg_type': msg.get('msg_type', 'text'),
            'is_self': msg.get('sender', {}).get('name', '') == '易希倩 Queenie Yi'
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


def translate_to_chinese(content):
    """将英文内容翻译成中文摘要"""
    content_lower = content.lower()

    # AI相关问题
    if 'ai' in content_lower:
        if 'coupon' in content_lower or 'new10' in content_lower:
            return 'AI给客户发送了失效优惠券NEW10'
        elif 'label' in content_lower or 'incorrect' in content_lower:
            return 'AI标注数据大部分错误'
        elif 'chat' in content_lower and 'loading' in content_lower:
            return '聊天加载问题，ticket分配异常'

    # 检查/确认类
    if 'check' in content_lower:
        if 'qc' in content_lower or 'nsz' in content_lower:
            return '确认QC和NSZ取消订单的状态处理'
        return '需要检查确认'

    # 会议/电话
    if 'call' in content_lower and 'tomorrow' in content_lower:
        return '约明天电话沟通'

    # 默认返回简短版本
    return content[:60] + '...' if len(content) > 60 else content


def extract_work_insights(analysis):
    """从消息中提取工作重点和待办事项"""
    insights = {
        'key_discussions': [],  # 关键讨论
        'todos': [],           # 待办事项
        'my_actions': []       # 我的行动
    }

    for chat in analysis['chat_stats']:
        chat_name = chat['name']
        messages = chat['messages']

        my_messages = [m for m in messages if m['is_self']]
        others_messages = [m for m in messages if not m['is_self']]

        # 提取关键讨论
        if len(messages) >= 2:
            discussion = {
                'chat': chat_name,
                'questions': [],
                'my_reply': None
            }

            # 提取别人的所有问题（翻译英文）- 不要遗漏
            for i, msg in enumerate(others_messages):
                content = msg['content']
                if any(q in content for q in ['?', '？', '确认', '看看', '检查', 'check', 'confirm', 'can you']):
                    # 判断是否英文
                    is_english = sum(1 for c in content[:50] if ord(c) < 128) > len(content[:50]) * 0.7

                    # 获取上下文（前一条消息）来理解待办
                    context = ""
                    if i > 0:
                        prev_msg = others_messages[i-1]
                        context = prev_msg['content'][:100]

                    # 生成清晰的待办描述
                    todo_summary = summarize_todo(msg['sender'], content, context, chat_name)

                    discussion['questions'].append({
                        'sender': msg['sender'],
                        'content': todo_summary
                    })

            # 提取我的回复
            if my_messages:
                long_reply = [m for m in my_messages if len(m['content']) > 30]
                if long_reply:
                    discussion['my_reply'] = long_reply[0]['content'][:150]

            if discussion['questions'] or discussion['my_reply']:
                insights['key_discussions'].append(discussion)

        # 提取待办事项 - 只提取真正需要行动的事项
        for i, msg in enumerate(others_messages):
            content = msg['content']

            # 先判断是否包含可能的action关键词
            if any(q in content for q in ['?', '？', '确认', '看看', '检查', 'check', 'confirm', 'can you', '请', '同步', '跟进']):
                # 判断是否真的是待办事项
                if is_actionable_todo(content, my_messages):
                    # 获取上下文
                    context = ""
                    if i > 0:
                        prev_msg = others_messages[i-1]
                        context = prev_msg['content'][:100]

                    # 生成清晰的待办描述
                    todo_summary = summarize_todo(msg['sender'], content, context, chat_name)

                    # 只添加确实有价值的待办（过滤掉总结后仍然不清晰的）
                    if todo_summary and len(todo_summary) > 5 and todo_summary != content[:len(todo_summary)]:
                        insights['todos'].append({
                            'chat': chat_name,
                            'sender': msg['sender'],
                            'content': todo_summary
                        })

        # 提取我的重要行动
        for msg in my_messages:
            if len(msg['content']) > 30:
                insights['my_actions'].append({
                    'chat': chat_name,
                    'content': msg['content'][:150]
                })

    return insights


def is_actionable_todo(content, my_messages):
    """判断是否是真正的待办事项（需要我行动）"""
    content_lower = content.lower()

    # 先检查纯粹的疑问句（在问我问题，不是要我做事）- 优先级最高
    pure_question_patterns = [
        '是不是', '是否', '怎么', '为什么', '为啥', 'why', 'how',
        '也就是说', '意思是', 'you mean', 'do you mean',
        '对吗', '对不对', 'right?', 'correct?'
    ]

    if any(pattern in content or pattern in content_lower for pattern in pure_question_patterns):
        # 这些是在问我问题，不是要我做事，不算待办
        return False

    # 强action信号词
    strong_action_signals = [
        '请', '帮忙', '麻烦', '辛苦', 'please', 'can you', 'could you',
        '需要你', '你看看', '你确认', '你检查', '你处理',
        '同步一下', '跟进', 'follow up', '回复', 'reply'
    ]

    # 如果有强action信号，是待办
    if any(signal in content or signal in content_lower for signal in strong_action_signals):
        return True

    # @mention 需要结合其他信号词才算action
    if '@易希倩' in content or '@Queenie' in content:
        # 有@且有action词，才算待办
        has_action_word = any(word in content for word in ['确认', '看看', '检查', '同步', '跟进'])
        if has_action_word:
            return True

    # 如果包含确认/检查等词，但是我后面已经回复了，不算待办
    if any(kw in content or kw in content_lower for kw in ['确认', 'confirm', '检查', 'check', '同步']):
        # 检查我是否已经回复
        if my_messages:
            return False  # 已经在对话中回复了，不算新待办
        return True  # 还没回复，是待办

    return False


def summarize_todo(sender, content, context, chat_name):
    """将原始消息总结成清晰的待办事项"""
    content_lower = content.lower()

    # 1. 极速退相关
    if '极速退' in chat_name or 'instant' in chat_name.lower():
        if '确认' in content or 'confirm' in content_lower:
            if 'ofp' in content_lower or 'pickup' in content_lower or '地址' in content or '上门取件' in content:
                return '确认极速退OFP/Pickup地址展示逻辑'
            if '白名单' in content or 'whitelist' in content_lower:
                return '确认白名单测试相关'
            return '确认极速退相关逻辑'
        if '同步' in content:
            return '同步极速退功能进展'
        if '测试' in content or 'test' in content_lower:
            return '跟进极速退测试情况'

    # 2. AI/算法相关
    if any(kw in content for kw in ['算法', '图搜', '相似度', 'algorithm', 'ai', 'model']):
        if '找' in content or 'discuss' in content_lower:
            return '找算法团队讨论技术方案'
        if '优化' in content or 'optimize' in content_lower:
            return '讨论算法优化方案'
        return '算法/AI相关事项跟进'

    # 3. 会议安排
    if any(kw in content for kw in ['会议', '开会', '讨论', 'meeting', 'call', 'sanity check']):
        if 'tomorrow' in content_lower or '明天' in content:
            return '约明天的会议/电话讨论'
        return '安排会议讨论'

    # 4. Review/检查类
    if any(kw in content for kw in ['review', '评审', 'check', '看看', '看下', '检查']):
        if 'pr' in content_lower or 'code' in content_lower:
            return 'Review代码/PR'
        if 'doc' in content_lower or '文档' in content:
            return 'Review文档'
        if 'case' in content_lower or '案例' in content:
            return '检查测试案例'
        if context and len(context) > 20:
            # 从上下文提取关键信息
            if 'ofp' in context.lower() or 'pickup' in context.lower():
                return '检查OFP/Pickup相关逻辑'
            if '权限' in context or 'permission' in context.lower():
                return '检查权限设置'
        return '检查确认相关事项'

    # 5. 数据/报表
    if any(kw in content for kw in ['数据', '报表', 'data', 'report', 'dashboard']):
        if 'provide' in content_lower or '提供' in content:
            return '提供数据/报表'
        return '数据分析相关'

    # 6. 问题反馈/Bug
    if any(kw in content for kw in ['issue', 'problem', '问题', 'bug', 'not working', '没有']):
        if context and len(context) > 15:
            # 尝试从上下文理解问题
            if 'bot' in context.lower() or 'ai' in context.lower() or '客服' in context:
                return '处理AI/Bot相关问题'
            if 'cancel' in context.lower() or '取消' in context:
                return '处理订单取消相关问题'
        return '处理反馈的问题'

    # 7. 更新/Update类
    if any(kw in content for kw in ['update', '更新', 'sync', '同步', 'follow up', '跟进']):
        if 'status' in content_lower or '状态' in content or '进展' in content:
            return '同步项目进展/状态'
        return '更新相关信息'

    # 8. 权限/Permission类
    if any(kw in content for kw in ['permission', '权限', 'access', 'edit']):
        return '处理权限/访问相关'

    # 9. 翻译/Translation类
    if any(kw in content for kw in ['翻译', 'translation', 'kurdish', '库尔德']):
        return '协调翻译工作'

    # 10. 从content中提取动词+宾语结构
    if any(verb in content for verb in ['请', '帮忙', '麻烦', '辛苦']):
        # 提取动词后的关键内容
        for verb in ['请', '帮忙', '麻烦', '辛苦']:
            if verb in content:
                after_verb = content.split(verb, 1)[1].strip()
                if len(after_verb) > 5 and len(after_verb) < 40:
                    return after_verb
                elif len(after_verb) >= 40:
                    # 提取第一句话
                    for sep in ['。', '，', '\n', ',']:
                        if sep in after_verb:
                            return after_verb.split(sep)[0]
                    return after_verb[:35] + '...'

    # 11. 如果有上下文，尝试从上下文+消息理解
    if context:
        if '订单' in context and ('cancel' in content_lower or '取消' in content):
            return '确认订单取消规则'
        if '项目' in context:
            return '跟进项目相关事项'
        if '测试' in context and ('问题' in content or 'issue' in content_lower):
            return '处理测试发现的问题'

    # 12. 英文内容 - 提取动词短语
    if sum(1 for c in content[:50] if ord(c) < 128) > len(content[:50]) * 0.7:
        # 提取can you / could you / please后面的内容
        for phrase in ['can you ', 'could you ', 'please ', 'need to ', 'we need ']:
            if phrase in content_lower:
                after_phrase = content_lower.split(phrase, 1)[1]
                # 提取到第一个句号或问号
                for end in ['.', '?', '\n']:
                    if end in after_phrase:
                        action = after_phrase.split(end)[0].strip()
                        if len(action) < 50:
                            return action
                        return action[:45] + '...'
        # fallback: 翻译简短的英文
        if len(content) < 100:
            return content[:80]

    # 13. 默认：智能清理和缩短
    clean_content = content.replace('@易希倩 Queenie Yi', '').replace('@Queenie Yi', '').replace('@易希倩', '').strip()
    clean_content = clean_content.replace('～', '').replace('~', '').strip()

    # 如果是以问号结尾的疑问句，可能不是action item
    if clean_content.endswith('?') or clean_content.endswith('？'):
        # 尝试转换为陈述句action
        if '是不是' in clean_content or '是否' in clean_content:
            clean_content = clean_content.replace('是不是', '确认').replace('是否', '确认')
        elif 'what' in clean_content.lower() or 'why' in clean_content.lower():
            return '回答问题：' + clean_content[:40]

    # 如果太长，提取关键部分
    if len(clean_content) > 50:
        # 尝试提取第一句话或关键短语
        for sep in ['。', '，', ',', '\n', '；']:
            if sep in clean_content:
                first_part = clean_content.split(sep)[0].strip()
                if 8 < len(first_part) < 50:
                    return first_part
        # 提取前50字符
        return clean_content[:50] + '...'

    return clean_content if clean_content and len(clean_content) > 5 else None


def check_vision_alignment(insights):
    """检查工作是否符合 vision.md 原则（针对用户产品）"""
    vision_alerts = []

    all_content = ' '.join([a['content'] for a in insights['my_actions']])

    # 1. 等待场景但无用户反馈
    if any(kw in all_content for kw in ['等待', '加载', 'loading', 'pending', '处理中']):
        if not any(kw in all_content for kw in ['提示', '告知', '反馈', '通知', '显示']):
            vision_alerts.append({
                'principle': '原则一：永远给用户回馈',
                'reminder': '等待场景必须有明确的用户反馈。永远不要让用户面对沉默。'
            })

    # 2. 需要培训/教程
    if any(kw in all_content for kw in ['培训', '教程', '说明', '指引', '教用户']):
        vision_alerts.append({
            'principle': '原则四：零学习成本',
            'reminder': '最好的产品是不言自明的。需要培训说明设计失败了。'
        })

    # 3. 人工介入
    if any(kw in all_content for kw in ['人工', '手动', '手工', '运营介入', '人工审核']):
        vision_alerts.append({
            'principle': '第二关：全面基于AI',
            'reminder': '每个流程必须由AI驱动。没有"以后再自动化"的步骤。'
        })

    # 4. 等待完善
    if any(kw in all_content for kw in ['等数据', '等完善', '再优化', '暂时不', '之后再']):
        vision_alerts.append({
            'principle': '原则三：70%就要出手',
            'reminder': '置信度70%就要输出。等到完美时机往往已经晚了。'
        })

    # 5. 展示但无行动
    if any(kw in all_content for kw in ['展示', '查看', '显示', '呈现']):
        if not any(kw in all_content for kw in ['操作', '点击', '下一步', '可以', '建议']):
            vision_alerts.append({
                'principle': '原则二：指向行动',
                'reminder': '每条信息必须让用户能做决策。看完后不知道该做什么，就删掉。'
            })

    # 6. 只谈技术不谈用户
    tech = any(kw in all_content for kw in ['算法', '模型', '准确率', '性能', '架构'])
    user = any(kw in all_content for kw in ['用户', '客户', '体验', '需求', '痛点'])
    if tech and not user:
        vision_alerts.append({
            'principle': '第一关：让用户过得更美好',
            'reminder': '她的生活多了一点美，少了一点麻烦吗？'
        })

    return vision_alerts


def generate_summary_text(analysis):
    """生成简洁的工作汇总"""
    today = datetime.now()
    today_str = today.strftime('%m月%d日')

    # 判断是否是周一
    if today.weekday() == 0:
        # 周一：显示周末汇总
        title = f"📊 周末汇总（周五-周日）"
        time_desc = "周末"
    else:
        # 其他日期：显示昨天
        yesterday = (today - timedelta(days=1)).strftime('%m月%d日')
        title = f"📊 {yesterday} 工作汇总"
        time_desc = "昨天"

    insights = extract_work_insights(analysis)

    summary = f"{title}\n\n"

    # 1. 关键讨论 - 完整显示所有问题
    if insights['key_discussions']:
        summary += f"## 💡 {time_desc}重点\n\n"
        for disc in insights['key_discussions'][:5]:  # 最多5个群
            # 判断是否是私聊
            is_private = '未知群聊' in disc['chat'] or 'p2p' in disc['chat'].lower()
            emoji = "💬" if is_private else "👥"

            summary += f"{emoji} **{disc['chat']}**\n"
            # 显示所有问题，不遗漏
            for q in disc['questions']:
                summary += f"  🔸 {q['sender']}：{q['content']}\n"
            # 显示你的回复
            if disc['my_reply']:
                summary += f"  ✅ 你：{disc['my_reply']}\n"
            summary += "\n"

    # 2. 今天需要跟进 - 完整列表
    if insights['todos']:
        summary += "## 📋 今天待办\n\n"
        for idx, todo in enumerate(insights['todos'][:8], 1):  # 最多8个
            summary += f"  {idx}️⃣ {todo['sender']}：{todo['content']}\n"
        summary += "\n"

    # 3. Vision 检查
    vision_alerts = check_vision_alignment(insights)
    if vision_alerts:
        summary += "## ⚠️ Vision 提醒\n\n"
        for alert in vision_alerts[:2]:  # 最多2个
            summary += f"  🔔 **{alert['principle']}**\n     {alert['reminder']}\n\n"

    # 4. 简要统计
    summary += f"---\n📅 {today_str} | 🎯 {len(insights['todos'])}项待办"

    return summary


def send_to_lark(summary_text, doc_url=None):
    """发送汇总到飞书"""
    user_id = 'ou_cc38ac881bcf17d997f0cad7d9a9a621'

    message = summary_text
    if doc_url:
        message += f"\n\n📄 [完整报告]({doc_url})"

    try:
        process = subprocess.Popen(
            ['lark-cli', 'im', '+messages-send',
             '--user-id', user_id,
             '--text', message,
             '--as', 'bot'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        stdout, stderr = process.communicate(timeout=30)

        if process.returncode == 0 and stdout:
            result = json.loads(stdout)
            if result.get('ok'):
                print("✅ 消息发送成功")
                return True
            else:
                print("❌ 消息发送失败")
                print(f"   错误: {result.get('error', {})}")
                return False
        else:
            print("❌ 消息发送失败")
            if stderr:
                print(f"   错误: {stderr}")
            return False

    except Exception as e:
        print(f"❌ 发送失败: {str(e)}")
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("🚀 开始执行每日工作汇总任务")
    print(f"⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 1. 获取消息
    print("\n📥 步骤 1/5: 获取昨天的消息...")
    messages = get_yesterday_messages()

    if not messages:
        print("⚠️  没有获取到消息，发送空报告")
        summary_text = "📊 昨天没有消息记录"
        send_to_lark(summary_text)
        return

    # 2. 过滤相关消息
    print("\n🔍 步骤 2/5: 过滤与你相关的消息...")
    relevant_messages = filter_relevant_messages(messages)

    if not relevant_messages:
        print("⚠️  没有与你相关的消息，发送空报告")
        summary_text = "📊 昨天没有与你相关的消息"
        send_to_lark(summary_text)
        return

    # 3. 分析消息
    print("\n🔍 步骤 3/5: 分析消息...")
    analysis = analyze_messages_simple(relevant_messages)
    print("   ✓ 分析完成")

    # 4. 生成汇总文本
    print("\n📝 步骤 4/5: 生成汇总报告...")
    summary_text = generate_summary_text(analysis)
    print("   ✓ 报告生成完成")

    # 5. 发送到飞书
    print("\n📤 步骤 5/5: 发送到飞书...")
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
