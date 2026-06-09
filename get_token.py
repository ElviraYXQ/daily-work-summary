#!/usr/bin/env python3
"""
获取飞书 User Access Token 的辅助脚本
"""

import subprocess
import json
import sys

print("=" * 60)
print("🔑 获取飞书 User Access Token")
print("=" * 60)
print()

# 方法1：从 lark-cli 获取
print("📋 方法: 从 lark-cli 状态获取")
print()

try:
    result = subprocess.run(
        ['lark-cli', 'auth', 'status', '--format', 'json'],
        capture_output=True,
        text=True,
        timeout=10
    )

    if result.returncode == 0:
        data = json.loads(result.stdout)

        # 打印完整信息
        print("✅ 成功获取授权信息：")
        print()
        print(f"用户: {data.get('userName', 'N/A')}")
        print(f"用户ID: {data.get('userOpenId', 'N/A')}")
        print(f"Token状态: {data.get('tokenStatus', 'N/A')}")
        print(f"过期时间: {data.get('expiresAt', 'N/A')}")
        print()

        # 尝试获取 token
        # 注意：lark-cli 可能不会直接返回 access_token
        print("⚠️  lark-cli 不会直接显示 access_token（出于安全考虑）")
        print()
        print("📝 需要使用以下替代方案：")
        print()
        print("方案1：在 GitHub Actions 中重新授权")
        print("  - 让 GitHub Actions 运行时执行授权流程")
        print("  - 需要在 workflow 中配置授权步骤")
        print()
        print("方案2：使用本地 lark-cli（推荐）")
        print("  - 在你的 Mac 本地运行脚本")
        print("  - 不需要提取 token")
        print("  - 配置 crontab 定时执行")
        print()

    else:
        print("❌ 无法获取授权信息")
        print(f"错误: {result.stderr}")

except Exception as e:
    print(f"❌ 执行失败: {str(e)}")

print("=" * 60)
print()
print("💡 建议：使用本地定时任务方案更简单可靠")
print()
