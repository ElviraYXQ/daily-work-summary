#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
三围数据分析 - 用户整体身材画像
按站点和地区分析用户三围组合分布
"""

import pandas as pd
import numpy as np
from collections import Counter
import json

# 读取数据
file_path = '/Users/yixiqian/Downloads/区域尺码用户数-三围-2026-04-21 19-59-00.csv'
df = pd.read_csv(file_path)

print("=" * 80)
print("数据概览")
print("=" * 80)
print(f"总用户数: {len(df):,}")
print(f"站点数量: {df['site_code'].nunique()}")
print(f"字段: {list(df.columns)}")
print()

# 数据清洗：提取腰围和上胸围的数值
def extract_measurement(val):
    """提取测量值的数字部分"""
    if pd.isna(val):
        return None
    val = str(val).strip()
    # 处理 34.0_1, 34_0 这种格式
    if '_' in val:
        val = val.split('_')[0]
    try:
        return float(val)
    except:
        return None

df['waist_cm'] = df['USER_WAIST'].apply(extract_measurement)
df['upper_bust_cm'] = df['USER_UPPER_BUST'].apply(extract_measurement)

# 过滤掉标记为 delete 的数据
valid_df = df[
    (df['USER_HIP'] != 'delete') &
    (df['USER_BELLY'] != 'delete') &
    (df['waist_cm'].notna()) &
    (df['upper_bust_cm'].notna())
].copy()

print(f"有效用户数（排除delete）: {len(valid_df):,}")
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

    return {
        'body_type': body_type,
        'waist_range': waist_range,
        'bust_range': bust_range,
        'full_profile': f"{body_type}|{waist_range}|{bust_range}"
    }

# 应用到所有有效数据
profiles = valid_df.apply(create_body_profile, axis=1, result_type='expand')
valid_df = pd.concat([valid_df, profiles], axis=1)

print("=" * 80)
print("全站点汇总分析")
print("=" * 80)

# 1. 整体身材类型分布
print("\n【1】身材类型组合 Top 10 (臀围+腹部)")
body_type_dist = valid_df['body_type'].value_counts()
for i, (body_type, count) in enumerate(body_type_dist.head(10).items(), 1):
    pct = count / len(valid_df) * 100
    print(f"{i:2d}. {body_type:25s} {count:6,} 人 ({pct:5.2f}%)")

# 2. 腰围分布
print("\n【2】腰围分布")
waist_dist = valid_df['waist_range'].value_counts().sort_index()
for waist_range, count in waist_dist.items():
    pct = count / len(valid_df) * 100
    print(f"    {waist_range:15s} {count:6,} 人 ({pct:5.2f}%)")

# 3. 上胸围分布
print("\n【3】上胸围分布")
bust_dist = valid_df['bust_range'].value_counts().sort_index()
for bust_range, count in bust_dist.items():
    pct = count / len(valid_df) * 100
    print(f"    {bust_range:15s} {count:6,} 人 ({pct:5.2f}%)")

# 4. 完整身材画像 Top 15
print("\n【4】完整身材画像 Top 15（臀+腹+腰+胸组合）")
full_profile_dist = valid_df['full_profile'].value_counts()
for i, (profile, count) in enumerate(full_profile_dist.head(15).items(), 1):
    pct = count / len(valid_df) * 100
    print(f"{i:2d}. {profile:60s} {count:5,} 人 ({pct:4.2f}%)")

# 5. 统计数据
print("\n【5】尺寸统计数据")
print(f"腰围: 平均 {valid_df['waist_cm'].mean():.1f}cm, "
      f"中位数 {valid_df['waist_cm'].median():.1f}cm, "
      f"标准差 {valid_df['waist_cm'].std():.1f}cm")
print(f"上胸围: 平均 {valid_df['upper_bust_cm'].mean():.1f}cm, "
      f"中位数 {valid_df['upper_bust_cm'].median():.1f}cm, "
      f"标准差 {valid_df['upper_bust_cm'].std():.1f}cm")

# 按站点分析
print("\n" + "=" * 80)
print("分站点详细分析")
print("=" * 80)

for site in sorted(valid_df['site_code'].unique()):
    site_df = valid_df[valid_df['site_code'] == site]

    print(f"\n{'▶ ' + site + ' 站点':=^78}")
    print(f"用户数: {len(site_df):,}")

    # 站点身材类型 Top 5
    print(f"\n  身材类型 Top 5:")
    for i, (body_type, count) in enumerate(site_df['body_type'].value_counts().head(5).items(), 1):
        pct = count / len(site_df) * 100
        print(f"    {i}. {body_type:25s} {count:5,} 人 ({pct:5.2f}%)")

    # 站点腰围分布
    print(f"\n  腰围分布:")
    for waist_range, count in site_df['waist_range'].value_counts().sort_index().items():
        pct = count / len(site_df) * 100
        bar = '█' * int(pct / 2)
        print(f"    {waist_range:15s} {count:5,} 人 ({pct:5.2f}%) {bar}")

    # 站点上胸围分布
    print(f"\n  上胸围分布:")
    for bust_range, count in site_df['bust_range'].value_counts().sort_index().items():
        pct = count / len(site_df) * 100
        bar = '█' * int(pct / 2)
        print(f"    {bust_range:15s} {count:5,} 人 ({pct:5.2f}%) {bar}")

    # 站点完整身材画像 Top 10
    print(f"\n  完整身材画像 Top 10:")
    for i, (profile, count) in enumerate(site_df['full_profile'].value_counts().head(10).items(), 1):
        pct = count / len(site_df) * 100
        print(f"    {i:2d}. {profile:60s} {count:4,} 人 ({pct:4.2f}%)")

    # 站点尺寸统计
    print(f"\n  尺寸统计:")
    print(f"    腰围: 平均 {site_df['waist_cm'].mean():.1f}cm, "
          f"中位数 {site_df['waist_cm'].median():.1f}cm, "
          f"标准差 {site_df['waist_cm'].std():.1f}cm")
    print(f"    上胸围: 平均 {site_df['upper_bust_cm'].mean():.1f}cm, "
          f"中位数 {site_df['upper_bust_cm'].median():.1f}cm, "
          f"标准差 {site_df['upper_bust_cm'].std():.1f}cm")

# 按站点+地区分析（如果有省份信息）
print("\n" + "=" * 80)
print("分站点+地区详细分析")
print("=" * 80)

for site in sorted(valid_df['site_code'].unique()):
    site_df = valid_df[valid_df['site_code'] == site]

    # 过滤掉 (null) 的省份
    provinces = site_df[site_df['prov_name'].notna() & (site_df['prov_name'] != '(null)')]['prov_name'].unique()

    if len(provinces) == 0:
        print(f"\n{site} 站点: 无有效省份数据")
        continue

    print(f"\n{'▶ ' + site + ' 站点 - 分地区分析':=^78}")

    for prov in sorted(provinces):
        prov_df = site_df[site_df['prov_name'] == prov]

        if len(prov_df) < 10:  # 跳过样本量太小的地区
            continue

        print(f"\n  【{prov}】({len(prov_df):,} 人)")

        # 地区身材类型 Top 3
        print(f"    身材类型 Top 3:")
        for i, (body_type, count) in enumerate(prov_df['body_type'].value_counts().head(3).items(), 1):
            pct = count / len(prov_df) * 100
            print(f"      {i}. {body_type:25s} {count:4,} 人 ({pct:5.2f}%)")

        # 地区尺寸统计
        print(f"    尺寸: 腰围均值 {prov_df['waist_cm'].mean():.1f}cm, "
              f"上胸围均值 {prov_df['upper_bust_cm'].mean():.1f}cm")

print("\n" + "=" * 80)
print("分析完成")
print("=" * 80)
