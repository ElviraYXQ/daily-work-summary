#!/usr/bin/env python3
"""
展示每个分类的原声案例
"""
import pandas as pd
import json
import re

# 读取已分类数据
df = pd.read_csv('/Users/yixiqian/daily-work-summary/content_based_analysis_sample.csv')

def clean_content(content):
    """移除JSON卡片，只保留用户文字消息"""
    if pd.isna(content):
        return ""

    # 移除JSON格式的卡片
    content = re.sub(r'\{"cardType".*?\}', '', content, flags=re.DOTALL)

    # 清理多余空白
    content = '\n'.join([line.strip() for line in content.split('\n') if line.strip()])

    return content

# 使用新的分类逻辑重新分类
import sys
sys.path.append('/Users/yixiqian/daily-work-summary')
from analyze_by_content import classify_by_content

results = []
for idx, row in df.iterrows():
    content = row['full_content'] if pd.notna(row['full_content']) else ''
    level, categories = classify_by_content(content)

    # 清理内容
    clean = clean_content(content)

    results.append({
        'conversation_id': row['conversation_id'],
        'hour': row['hour'],
        'level': level,
        'categories': categories,
        'full_content': content,
        'clean_content': clean
    })

results_df = pd.DataFrame(results)

print("=" * 100)
print("📋 每个分类的原声案例（移除JSON后）")
print("=" * 100)

# 第1层
print("\n【第1层：高置信度大促相关】\n")

level1_df = results_df[results_df['level'] == 1]
all_cats = []
for cats in level1_df['categories']:
    all_cats.extend(cats)

unique_cats = sorted(pd.Series(all_cats).unique())

for cat in unique_cats:
    print(f"\n{'=' * 80}")
    print(f"【{cat}】")
    print("=" * 80)

    cat_samples = level1_df[level1_df['categories'].apply(lambda x: cat in x)]

    # 找到有实际文字内容的样本
    samples_with_text = cat_samples[cat_samples['clean_content'].str.len() > 10]

    if len(samples_with_text) == 0:
        samples_with_text = cat_samples

    for idx, row in samples_with_text.head(2).iterrows():
        print(f"\n案例 {idx+1}:")
        print(f"会话ID: {row['conversation_id']} | 时间: {row['hour']:02d}:00")
        print(f"用户消息:")

        if row['clean_content']:
            print(row['clean_content'][:300])
        else:
            print("(只有订单卡片，无文字内容)")
        print()

# 第2层
print("\n" + "=" * 100)
print("【第2层：不确定】")
print("=" * 100)

level2_df = results_df[results_df['level'] == 2]
all_cats = []
for cats in level2_df['categories']:
    all_cats.extend(cats)

unique_cats = sorted(pd.Series(all_cats).unique())

for cat in unique_cats:
    print(f"\n{'=' * 80}")
    print(f"【{cat}】")
    print("=" * 80)

    cat_samples = level2_df[level2_df['categories'].apply(lambda x: cat in x)]

    for idx, row in cat_samples.head(2).iterrows():
        print(f"\n案例 {idx+1}:")
        print(f"会话ID: {row['conversation_id']} | 时间: {row['hour']:02d}:00")
        print(f"用户消息:")

        if row['clean_content']:
            print(row['clean_content'][:300])
        else:
            print("(只有订单卡片，无文字内容)")
        print()

# 第3层
print("\n" + "=" * 100)
print("【第3层：高置信度非大促】")
print("=" * 100)

level3_df = results_df[results_df['level'] == 3]
all_cats = []
for cats in level3_df['categories']:
    all_cats.extend(cats)

unique_cats = sorted(pd.Series(all_cats).unique())

for cat in unique_cats:
    print(f"\n{'=' * 80}")
    print(f"【{cat}】")
    print("=" * 80)

    cat_samples = level3_df[level3_df['categories'].apply(lambda x: cat in x)]

    for idx, row in cat_samples.head(2).iterrows():
        print(f"\n案例 {idx+1}:")
        print(f"会话ID: {row['conversation_id']} | 时间: {row['hour']:02d}:00")
        print(f"用户消息:")

        if row['clean_content']:
            print(row['clean_content'][:300])
        else:
            print("(无文字内容)")
        print()
