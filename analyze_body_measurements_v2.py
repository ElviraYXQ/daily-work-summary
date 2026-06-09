#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
三围数据分析 v2 - 用户整体身材画像
user_id 字段实际是用户数量
"""

import pandas as pd
import numpy as np
from collections import Counter
import json

# 读取数据
file_path = '/Users/yixiqian/Downloads/区域尺码用户数-三围-2026-04-22 10-13-18.xlsx'
df = pd.read_excel(file_path)

print("=" * 80)
print("数据概览")
print("=" * 80)
print(f"数据行数: {len(df):,}")
print(f"站点数量: {df['site_code'].nunique()}")
print(f"字段: {list(df.columns)}")
print(f"\n前5行样例:")
print(df.head())
print()

# 数据清洗：提取腰围和上胸围的数值
def extract_measurement(val):
    """提取测量值的数字部分"""
    if pd.isna(val):
        return None
    val = str(val).strip()
    if '_' in val:
        val = val.split('_')[0]
    try:
        return float(val)
    except:
        return None

df['waist_cm'] = df['USER_WAIST'].apply(extract_measurement)
df['upper_bust_cm'] = df['USER_UPPER_BUST'].apply(extract_measurement)

# 将 usr_id 作为用户数量（重命名为 user_count）
df['user_count'] = df['usr_id'].astype(int)

# 过滤掉标记为 delete 的数据
valid_df = df[
    (df['USER_HIP'] != 'delete') &
    (df['USER_BELLY'] != 'delete') &
    (df['waist_cm'].notna()) &
    (df['upper_bust_cm'].notna())
].copy()

total_users = valid_df['user_count'].sum()
print(f"有效用户总数（排除delete）: {total_users:,}")
print()

# 创建身材组合标签
def create_body_profile(row):
    """创建整体身材画像标签"""
    hip_type = row['USER_HIP']
    belly_type = row['USER_BELLY']
    waist = row['waist_cm']
    bust = row['upper_bust_cm']

    # 腰围分段
    if waist < 26:
        waist_range = "XS腰(<26)"
    elif waist < 28:
        waist_range = "S腰(26-28)"
    elif waist < 30:
        waist_range = "M腰(28-30)"
    elif waist < 32:
        waist_range = "L腰(30-32)"
    elif waist < 34:
        waist_range = "XL腰(32-34)"
    else:
        waist_range = "XXL腰(34+)"

    # 上胸围分段
    if bust < 30:
        bust_range = "XS胸(<30)"
    elif bust < 32:
        bust_range = "S胸(30-32)"
    elif bust < 34:
        bust_range = "M胸(32-34)"
    elif bust < 36:
        bust_range = "L胸(34-36)"
    elif bust < 38:
        bust_range = "XL胸(36-38)"
    else:
        bust_range = "XXL胸(38+)"

    # 组合身材类型
    body_type = f"{hip_type}臀_{belly_type}腹"

    return pd.Series({
        'body_type': body_type,
        'waist_range': waist_range,
        'bust_range': bust_range,
        'full_profile': f"{body_type}|{waist_range}|{bust_range}"
    })

# 应用到所有有效数据
profiles = valid_df.apply(create_body_profile, axis=1)
valid_df = pd.concat([valid_df, profiles], axis=1)

print("=" * 80)
print("全站点汇总分析")
print("=" * 80)

# 1. 整体身材类型分布
print("\n【1】身材类型组合 Top 10 (臀围+腹部)")
body_type_dist = valid_df.groupby('body_type')['user_count'].sum().sort_values(ascending=False)
for i, (body_type, count) in enumerate(body_type_dist.head(10).items(), 1):
    pct = count / total_users * 100
    print(f"{i:2d}. {body_type:30s} {count:8,} 人 ({pct:5.2f}%)")

# 2. 腰围分布
print("\n【2】腰围分布")
waist_dist = valid_df.groupby('waist_range')['user_count'].sum().sort_index()
for waist_range, count in waist_dist.items():
    pct = count / total_users * 100
    print(f"    {waist_range:15s} {count:8,} 人 ({pct:5.2f}%)")

# 3. 上胸围分布
print("\n【3】上胸围分布")
bust_dist = valid_df.groupby('bust_range')['user_count'].sum().sort_index()
for bust_range, count in bust_dist.items():
    pct = count / total_users * 100
    print(f"    {bust_range:15s} {count:8,} 人 ({pct:5.2f}%)")

# 4. 完整身材画像 Top 15
print("\n【4】完整身材画像 Top 15（臀+腹+腰+胸组合）")
full_profile_dist = valid_df.groupby('full_profile')['user_count'].sum().sort_values(ascending=False)
for i, (profile, count) in enumerate(full_profile_dist.head(15).items(), 1):
    pct = count / total_users * 100
    print(f"{i:2d}. {profile:60s} {count:7,} 人 ({pct:5.2f}%)")

# 5. 统计数据（加权平均）
waist_mean = (valid_df['waist_cm'] * valid_df['user_count']).sum() / valid_df['user_count'].sum()
bust_mean = (valid_df['upper_bust_cm'] * valid_df['user_count']).sum() / valid_df['user_count'].sum()

print("\n【5】尺寸统计数据")
print(f"腰围: 加权平均 {waist_mean:.1f}cm")
print(f"上胸围: 加权平均 {bust_mean:.1f}cm")

# 按站点分析
print("\n" + "=" * 80)
print("分站点详细分析")
print("=" * 80)

# 准备输出到飞书文档的结构化数据
feishu_output = {
    "title": "Savana 用户三围画像分析报告",
    "total_users": int(total_users),
    "overall": {},
    "sites": {}
}

for site in sorted(valid_df['site_code'].unique()):
    site_df = valid_df[valid_df['site_code'] == site]
    site_users = site_df['user_count'].sum()

    print(f"\n{'▶ ' + site + ' 站点':=^78}")
    print(f"用户数: {site_users:,}")

    # 站点身材类型 Top 5
    print(f"\n  身材类型 Top 5:")
    body_type_top5 = []
    for i, (body_type, count) in enumerate(site_df.groupby('body_type')['user_count'].sum().sort_values(ascending=False).head(5).items(), 1):
        pct = count / site_users * 100
        print(f"    {i}. {body_type:30s} {count:7,} 人 ({pct:5.2f}%)")
        body_type_top5.append({
            "rank": i,
            "type": body_type,
            "count": int(count),
            "percentage": round(pct, 2)
        })

    # 站点腰围分布
    print(f"\n  腰围分布:")
    waist_dist_site = {}
    for waist_range, count in site_df.groupby('waist_range')['user_count'].sum().sort_index().items():
        pct = count / site_users * 100
        bar = '█' * int(pct / 2)
        print(f"    {waist_range:15s} {count:7,} 人 ({pct:5.2f}%) {bar}")
        waist_dist_site[waist_range] = {
            "count": int(count),
            "percentage": round(pct, 2)
        }

    # 站点上胸围分布
    print(f"\n  上胸围分布:")
    bust_dist_site = {}
    for bust_range, count in site_df.groupby('bust_range')['user_count'].sum().sort_index().items():
        pct = count / site_users * 100
        bar = '█' * int(pct / 2)
        print(f"    {bust_range:15s} {count:7,} 人 ({pct:5.2f}%) {bar}")
        bust_dist_site[bust_range] = {
            "count": int(count),
            "percentage": round(pct, 2)
        }

    # 站点完整身材画像 Top 10
    print(f"\n  完整身材画像 Top 10:")
    full_profile_top10 = []
    for i, (profile, count) in enumerate(site_df.groupby('full_profile')['user_count'].sum().sort_values(ascending=False).head(10).items(), 1):
        pct = count / site_users * 100
        print(f"    {i:2d}. {profile:60s} {count:6,} 人 ({pct:5.2f}%)")
        full_profile_top10.append({
            "rank": i,
            "profile": profile,
            "count": int(count),
            "percentage": round(pct, 2)
        })

    # 站点尺寸统计
    site_waist_mean = (site_df['waist_cm'] * site_df['user_count']).sum() / site_df['user_count'].sum()
    site_bust_mean = (site_df['upper_bust_cm'] * site_df['user_count']).sum() / site_df['user_count'].sum()

    print(f"\n  尺寸统计:")
    print(f"    腰围: 加权平均 {site_waist_mean:.1f}cm")
    print(f"    上胸围: 加权平均 {site_bust_mean:.1f}cm")

    # 保存站点数据
    feishu_output["sites"][site] = {
        "total_users": int(site_users),
        "body_type_top5": body_type_top5,
        "waist_distribution": waist_dist_site,
        "bust_distribution": bust_dist_site,
        "full_profile_top10": full_profile_top10,
        "avg_waist": round(site_waist_mean, 1),
        "avg_bust": round(site_bust_mean, 1)
    }

# 跳过地区分析（数据中无地区字段）
print("\n" + "=" * 80)
print("注意: 数据中无地区字段，跳过地区分析")
print("=" * 80)

# 保存全局统计
feishu_output["overall"] = {
    "body_type_top10": [
        {"rank": i, "type": body_type, "count": int(count), "percentage": round(count / total_users * 100, 2)}
        for i, (body_type, count) in enumerate(body_type_dist.head(10).items(), 1)
    ],
    "waist_distribution": {
        waist_range: {"count": int(count), "percentage": round(count / total_users * 100, 2)}
        for waist_range, count in waist_dist.items()
    },
    "bust_distribution": {
        bust_range: {"count": int(count), "percentage": round(count / total_users * 100, 2)}
        for bust_range, count in bust_dist.items()
    },
    "full_profile_top15": [
        {"rank": i, "profile": profile, "count": int(count), "percentage": round(count / total_users * 100, 2)}
        for i, (profile, count) in enumerate(full_profile_dist.head(15).items(), 1)
    ],
    "avg_waist": round(waist_mean, 1),
    "avg_bust": round(bust_mean, 1)
}

# 保存 JSON 输出
output_file = '/Users/yixiqian/daily-work-summary/body_measurements_analysis.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(feishu_output, f, ensure_ascii=False, indent=2)

print("\n" + "=" * 80)
print("分析完成")
print("=" * 80)
print(f"\n结构化数据已保存到: {output_file}")
