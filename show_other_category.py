#!/usr/bin/env python3
"""
查看"其他"类的详细案例
"""
import pandas as pd
import ast

# 读取分类结果
df = pd.read_csv('/Users/yixiqian/daily-work-summary/issue_type_analysis_sample.csv')

print("=" * 100)
print("📋 查看【其他】类的详细案例（50条）")
print("=" * 100)

# 找出被分类为"其他"的会话
other_samples = df[df['categories'].apply(
    lambda x: '其他' in (ast.literal_eval(x) if isinstance(x, str) else x)
)]

print(f"\n总共 {len(other_samples)} 条被归类为【其他】")
print(f"\n展示前50条：\n")

for idx, row in other_samples.head(50).iterrows():
    print(f"{'=' * 80}")
    print(f"案例 {idx+1}:")
    print(f"  会话ID: {row['conversation_id']} | 时间: {row['hour']:02d}:00")

    # 解析分类
    cats = ast.literal_eval(row['categories']) if isinstance(row['categories'], str) else row['categories']
    print(f"  所有分类: {', '.join(cats)}")

    print(f"  用户消息:")
    if row['content_preview']:
        print(f"  {row['content_preview'][:400]}")
        if len(row['content_preview']) > 400:
            print(f"  ...")
    else:
        print(f"  (无文字内容)")
    print()
