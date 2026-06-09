#!/usr/bin/env python3
"""
使用新的分类逻辑重新分类已有的1000条样本数据
"""
import pandas as pd
import sys
sys.path.append('/Users/yixiqian/daily-work-summary')
from analyze_by_content import classify_by_content

# 读取已有数据
df = pd.read_csv('/Users/yixiqian/daily-work-summary/content_based_analysis_sample.csv')

print("正在使用新的分类逻辑重新分类...")

# 重新分类
results = []
for idx, row in df.iterrows():
    content = row['full_content'] if pd.notna(row['full_content']) else ''
    level, categories = classify_by_content(content)
    results.append({
        'conversation_id': row['conversation_id'],
        'hour': row['hour'],
        'level': level,
        'categories': categories
    })

results_df = pd.DataFrame(results)

# 统计
print("\n" + "=" * 100)
print("📊 新分类逻辑的结果")
print("=" * 100)

total = len(results_df)
level1 = len(results_df[results_df['level'] == 1])
level2 = len(results_df[results_df['level'] == 2])
level3 = len(results_df[results_df['level'] == 3])

print(f"\n【总体分布】")
print(f"  样本总数: {total}")
print(f"  ├─ 第1层（高置信度大促相关）: {level1} ({level1/total*100:.1f}%)")
print(f"  ├─ 第2层（不确定）: {level2} ({level2/total*100:.1f}%)")
print(f"  └─ 第3层（高置信度非大促）: {level3} ({level3/total*100:.1f}%)")

# 第1层详细
print(f"\n" + "=" * 100)
print(f"第1层：高置信度大促相关（{level1}条）")
print("=" * 100)

level1_df = results_df[results_df['level'] == 1]
if len(level1_df) > 0:
    all_cats = []
    for cats in level1_df['categories']:
        all_cats.extend(cats)

    cat_counts = pd.Series(all_cats).value_counts()
    print(f"\n细分类型分布:")
    for cat, count in cat_counts.items():
        print(f"  {count:4d} ({count/level1*100:5.1f}%) | {cat}")

# 第2层详细
print(f"\n" + "=" * 100)
print(f"第2层：不确定（{level2}条）")
print("=" * 100)

level2_df = results_df[results_df['level'] == 2]
if len(level2_df) > 0:
    all_cats = []
    for cats in level2_df['categories']:
        all_cats.extend(cats)

    cat_counts = pd.Series(all_cats).value_counts()
    print(f"\n细分类型分布:")
    for cat, count in cat_counts.items():
        print(f"  {count:4d} ({count/level2*100:5.1f}%) | {cat}")

# 第3层详细
print(f"\n" + "=" * 100)
print(f"第3层：高置信度非大促（{level3}条）")
print("=" * 100)

level3_df = results_df[results_df['level'] == 3]
if len(level3_df) > 0:
    all_cats = []
    for cats in level3_df['categories']:
        all_cats.extend(cats)

    cat_counts = pd.Series(all_cats).value_counts()
    print(f"\n细分类型分布:")
    for cat, count in cat_counts.items():
        print(f"  {count:4d} ({count/level3*100:5.1f}%) | {cat}")

# 展示第1层的样本
print(f"\n" + "=" * 100)
print("第1层样本展示（每个分类前3条）")
print("=" * 100)

# 合并原始数据
merged = results_df.merge(df[['conversation_id', 'full_content']], on='conversation_id')

# 按细分类型展示
level1_merged = merged[merged['level'] == 1]
if len(level1_merged) > 0:
    all_cats = []
    for cats in level1_merged['categories']:
        all_cats.extend(cats)

    unique_cats = pd.Series(all_cats).unique()

    for cat in unique_cats:
        print(f"\n【{cat}】")
        cat_samples = level1_merged[level1_merged['categories'].apply(lambda x: cat in x)]
        for idx, row in cat_samples.head(3).iterrows():
            print(f"\n  会话{row['conversation_id']} | {row['hour']:02d}:00")
            preview = row['full_content'][:200]
            if len(row['full_content']) > 200:
                preview += "..."
            print(f"  {preview}")
