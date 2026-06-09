#!/bin/bash

# 每日工作汇总定时任务脚本
# 配置环境变量
export PATH="/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin:/opt/homebrew/Caskroom/claude-code/2.1.74:$PATH"
export LARK_USER_ID="ou_cc38ac881bcf17d997f0cad7d9a9a621"

# Claude API (for industry news)
export ANTHROPIC_AUTH_TOKEN="sk-gm5JKc_xaw9olpp0B_T1Cw"
export ANTHROPIC_BASE_URL="https://litellm-sg.mayfair-inc.com"
export ANTHROPIC_MODEL="claude-sonnet-4-5-20250929"

# 日志文件
LOG_FILE="$HOME/daily-work-summary/logs/$(date +%Y%m%d).log"
mkdir -p "$HOME/daily-work-summary/logs"

# 记录开始时间
echo "========================================" >> "$LOG_FILE"
echo "开始时间: $(date)" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

# 刷新 lark-cli token（避免过期）
echo "刷新 lark-cli token..." >> "$LOG_FILE"
lark-cli auth status >> "$LOG_FILE" 2>&1

# 切换到项目目录并运行工作汇总
cd "$HOME/daily-work-summary" && python3 collect_messages.py >> "$LOG_FILE" 2>&1

# 运行竞对动态推送
echo "----------------------------------------" >> "$LOG_FILE"
echo "开始竞对动态推送: $(date)" >> "$LOG_FILE"
echo "----------------------------------------" >> "$LOG_FILE"
python3 collect_industry_news.py >> "$LOG_FILE" 2>&1

# 记录结束时间
echo "结束时间: $(date)" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"
