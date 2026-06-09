#!/usr/bin/env python3
"""
生成详细的案例报告，用于核对分类准确性
"""
import pandas as pd

# 读取分类结果
df = pd.read_csv('/Users/yixiqian/daily-work-summary/issue_type_analysis_sample.csv')

print("=" * 100)
print("📋 每个问题类型的详细案例（前10条）")
print("=" * 100)

# 统计所有分类
all_cats = []
for cats in df['categories']:
    # 将字符串转回列表
    import ast
    if isinstance(cats, str):
        cats = ast.literal_eval(cats)
    all_cats.extend(cats)

cat_counts = pd.Series(all_cats).value_counts()

# 按照进线量排序展示
for rank, (cat, count) in enumerate(cat_counts.items(), 1):
    pct = count / len(df) * 100

    print(f"\n{'=' * 100}")
    print(f"【{rank}. {cat}】 {count} 条 ({pct:.1f}%)")
    print("=" * 100)

    # 找到包含该分类的会话
    cat_samples = df[df['categories'].apply(
        lambda x: cat in (ast.literal_eval(x) if isinstance(x, str) else x)
    )]

    # 优先展示有实际文字内容的
    samples_with_text = cat_samples[cat_samples['content_preview'].str.len() > 10]

    if len(samples_with_text) == 0:
        samples_with_text = cat_samples

    # 展示前10条
    for idx, row in samples_with_text.head(10).iterrows():
        print(f"\n案例 {idx+1}:")
        print(f"  会话ID: {row['conversation_id']} | 时间: {row['hour']:02d}:00")
        print(f"  是否大促特有: {'✅ 是' if row['is_promo_specific'] else '⚪ 否'}")

        # 解析分类
        import ast
        cats = ast.literal_eval(row['categories']) if isinstance(row['categories'], str) else row['categories']
        print(f"  所有分类: {', '.join(cats)}")

        print(f"  用户消息:")
        if row['content_preview']:
            print(f"  {row['content_preview'][:300]}")
            if len(row['content_preview']) > 300:
                print(f"  ...")
        else:
            print(f"  (无文字内容)")

print("\n" + "=" * 100)
print("✅ 报告生成完成")
print("=" * 100)
