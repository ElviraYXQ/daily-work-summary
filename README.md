# 每日工作汇总系统

自动收集前一天的飞书消息并生成工作汇总报告

## 功能

- 📱 自动获取所有飞书聊天消息
- 📊 按群聊/会话分类统计
- 🤖 支持 Claude API 智能分析（可选）
- 📄 生成飞书文档报告
- ⏰ 每天早上 9:00 自动发送

## 配置要求

### GitHub Secrets 配置

在 GitHub 仓库添加以下 Secrets：

| 名称 | 说明 | 必需 |
|------|------|------|
| `LARK_APP_ID` | 飞书应用 ID | ✅ |
| `LARK_APP_SECRET` | 飞书应用密钥 | ✅ |
| `LARK_USER_ID` | 接收消息的用户 ID | ✅ |
| `LARK_USER_TOKEN` | 用户访问 token（用于搜索消息） | ✅ |
| `CLAUDE_API_KEY` | Claude API 密钥（可选，启用 AI 分析） | ⭕ |

### 本地运行

```bash
# 安装依赖
pip install -r requirements.txt

# 配置环境变量
export LARK_APP_ID="your_app_id"
export LARK_APP_SECRET="your_app_secret"
export LARK_USER_ID="your_user_id"
export CLAUDE_API_KEY="your_claude_key"  # 可选

# 运行脚本
python collect_messages.py
```

## 如何工作

1. 每天早上 9:00，GitHub Actions 自动触发
2. 获取前一天的所有飞书消息
3. 分析并生成工作汇总
4. 发送通知到飞书 + 创建详细文档

## 汇总内容

- 📈 消息统计（总数、会话数）
- 💬 主要会话列表
- 🤖 AI 智能分析（如启用）
  - 项目进度提取
  - 待办事项识别
  - 问题和风险总结
  - 重要决策记录

## 文件说明

- `collect_messages.py` - 主脚本
- `.github/workflows/daily-summary.yml` - GitHub Actions 配置
- `requirements.txt` - Python 依赖
