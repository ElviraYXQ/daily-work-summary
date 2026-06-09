#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
三围数据分析 v4 - 数据质量清洗
过滤不符合成年女性正常范围的脏数据
"""

import pandas as pd
import numpy as np
import json

# 读取数据
file_path = '/Users/yixiqian/Downloads/区域尺码用户数-三围-2026-04-22 10-13-18.xlsx'
df = pd.read_excel(file_path)

print("=" * 80)
print("数据概览")
print("=" * 80)
print(f"原始数据行数: {len(df):,}")

# 数据清洗：提取测量值并转换单位
def extract_measurement_with_unit(val):
    """提取测量值并识别单位，统一转为厘米"""
    if pd.isna(val):
        return None
    val = str(val).strip()
    if '_' in val:
        parts = val.split('_')
        try:
            number = float(parts[0])
            unit_flag = parts[1]
            # _1 = 英寸, _0 = 厘米
            if unit_flag == '1':
                return number * 2.54  # 英寸转厘米
            else:
                return number
        except:
            return None
    try:
        return float(val)
    except:
        return None

df['waist_cm'] = df['USER_WAIST'].apply(extract_measurement_with_unit)
df['upper_bust_cm'] = df['USER_UPPER_BUST'].apply(extract_measurement_with_unit)
df['user_count'] = df['usr_id'].astype(int)

# 基础过滤：排除 delete 标记
basic_valid_df = df[
    (df['USER_HIP'] != 'delete') &
    (df['USER_BELLY'] != 'delete') &
    (df['waist_cm'].notna()) &
    (df['upper_bust_cm'].notna())
].copy()

basic_total = basic_valid_df['user_count'].sum()
print(f"基础过滤后（排除delete）: {basic_total:,} 人")

# 统计基础过滤后的分布
print(f"\n基础过滤后的尺寸分布:")
print(f"腰围: 最小 {basic_valid_df['waist_cm'].min():.1f}cm, "
      f"最大 {basic_valid_df['waist_cm'].max():.1f}cm, "
      f"平均 {(basic_valid_df['waist_cm'] * basic_valid_df['user_count']).sum() / basic_total:.1f}cm")
print(f"上胸围: 最小 {basic_valid_df['upper_bust_cm'].min():.1f}cm, "
      f"最大 {basic_valid_df['upper_bust_cm'].max():.1f}cm, "
      f"平均 {(basic_valid_df['upper_bust_cm'] * basic_valid_df['user_count']).sum() / basic_total:.1f}cm")

# 查看异常值分布
print("\n【异常值检测】")

# 定义成年女性合理范围（基于亚洲女性人体测量学）
WAIST_MIN = 55  # cm (约 21.7 inch)
WAIST_MAX = 105  # cm (约 41.3 inch)
BUST_MIN = 70  # cm (约 27.6 inch)
BUST_MAX = 120  # cm (约 47.2 inch)

print(f"\n合理范围定义（参考亚洲成年女性人体测量标准）:")
print(f"  腰围: {WAIST_MIN}cm - {WAIST_MAX}cm ({WAIST_MIN/2.54:.1f} - {WAIST_MAX/2.54:.1f} inch)")
print(f"  上胸围: {BUST_MIN}cm - {BUST_MAX}cm ({BUST_MIN/2.54:.1f} - {BUST_MAX/2.54:.1f} inch)")

# 标记异常数据
basic_valid_df['waist_abnormal'] = (basic_valid_df['waist_cm'] < WAIST_MIN) | (basic_valid_df['waist_cm'] > WAIST_MAX)
basic_valid_df['bust_abnormal'] = (basic_valid_df['upper_bust_cm'] < BUST_MIN) | (basic_valid_df['upper_bust_cm'] > BUST_MAX)
basic_valid_df['is_abnormal'] = basic_valid_df['waist_abnormal'] | basic_valid_df['bust_abnormal']

# 统计异常数据
abnormal_df = basic_valid_df[basic_valid_df['is_abnormal']]
abnormal_users = abnormal_df['user_count'].sum()
abnormal_pct = abnormal_users / basic_total * 100

print(f"\n异常数据统计:")
print(f"  异常用户数: {abnormal_users:,} 人 ({abnormal_pct:.2f}%)")

# 按异常类型分类
waist_too_small = basic_valid_df[basic_valid_df['waist_cm'] < WAIST_MIN]['user_count'].sum()
waist_too_large = basic_valid_df[basic_valid_df['waist_cm'] > WAIST_MAX]['user_count'].sum()
bust_too_small = basic_valid_df[basic_valid_df['upper_bust_cm'] < BUST_MIN]['user_count'].sum()
bust_too_large = basic_valid_df[basic_valid_df['upper_bust_cm'] > BUST_MAX]['user_count'].sum()

print(f"\n异常类型分布:")
print(f"  腰围过小 (<{WAIST_MIN}cm): {waist_too_small:,} 人 ({waist_too_small/basic_total*100:.2f}%)")
print(f"  腰围过大 (>{WAIST_MAX}cm): {waist_too_large:,} 人 ({waist_too_large/basic_total*100:.2f}%)")
print(f"  上胸围过小 (<{BUST_MIN}cm): {bust_too_small:,} 人 ({bust_too_small/basic_total*100:.2f}%)")
print(f"  上胸围过大 (>{BUST_MAX}cm): {bust_too_large:,} 人 ({bust_too_large/basic_total*100:.2f}%)")

# 展示一些异常数据样例
print(f"\n异常数据样例（腰围过小）:")
waist_too_small_samples = basic_valid_df[basic_valid_df['waist_cm'] < WAIST_MIN].nlargest(5, 'user_count')
for idx, row in waist_too_small_samples.iterrows():
    print(f"  {row['site_code']}: 腰围 {row['waist_cm']:.1f}cm, 上胸围 {row['upper_bust_cm']:.1f}cm, {row['user_count']} 人")

print(f"\n异常数据样例（上胸围过小）:")
bust_too_small_samples = basic_valid_df[basic_valid_df['upper_bust_cm'] < BUST_MIN].nlargest(5, 'user_count')
for idx, row in bust_too_small_samples.iterrows():
    print(f"  {row['site_code']}: 腰围 {row['waist_cm']:.1f}cm, 上胸围 {row['upper_bust_cm']:.1f}cm, {row['user_count']} 人")

# 按站点统计异常数据
print(f"\n按站点的异常数据分布:")
for site in sorted(basic_valid_df['site_code'].unique()):
    site_df = basic_valid_df[basic_valid_df['site_code'] == site]
    site_total = site_df['user_count'].sum()
    site_abnormal = site_df[site_df['is_abnormal']]['user_count'].sum()
    site_abnormal_pct = site_abnormal / site_total * 100
    print(f"  {site}: {site_abnormal:,} / {site_total:,} ({site_abnormal_pct:.2f}%)")

# 清洗后的数据
valid_df = basic_valid_df[~basic_valid_df['is_abnormal']].copy()
total_users = valid_df['user_count'].sum()

print(f"\n" + "=" * 80)
print(f"数据清洗完成")
print(f"=" * 80)
print(f"清洗前: {basic_total:,} 人")
print(f"清洗后: {total_users:,} 人")
print(f"剔除: {abnormal_users:,} 人 ({abnormal_pct:.2f}%)")

# 创建身材组合标签
def create_body_profile(row):
    """创建整体身材画像标签"""
    hip_type = row['USER_HIP']
    belly_type = row['USER_BELLY']
    waist = row['waist_cm']
    bust = row['upper_bust_cm']

    # 腰围分段（厘米）
    if waist < 66:
        waist_range = "XS腰(<66cm)"
    elif waist < 71:
        waist_range = "S腰(66-71cm)"
    elif waist < 76:
        waist_range = "M腰(71-76cm)"
    elif waist < 81:
        waist_range = "L腰(76-81cm)"
    elif waist < 86:
        waist_range = "XL腰(81-86cm)"
    else:
        waist_range = "XXL腰(86+cm)"

    # 上胸围分段（厘米）
    if bust < 76:
        bust_range = "XS胸(<76cm)"
    elif bust < 81:
        bust_range = "S胸(76-81cm)"
    elif bust < 86:
        bust_range = "M胸(81-86cm)"
    elif bust < 91:
        bust_range = "L胸(86-91cm)"
    elif bust < 96:
        bust_range = "XL胸(91-96cm)"
    else:
        bust_range = "XXL胸(96+cm)"

    body_type = f"{hip_type}臀_{belly_type}腹"

    return pd.Series({
        'body_type': body_type,
        'waist_range': waist_range,
        'bust_range': bust_range,
        'full_profile': f"{body_type}|{waist_range}|{bust_range}"
    })

profiles = valid_df.apply(create_body_profile, axis=1)
valid_df = pd.concat([valid_df, profiles], axis=1)

print("\n" + "=" * 80)
print("清洗后数据分析")
print("=" * 80)

# 1. 整体身材类型分布
print("\n【1】身材类型组合 Top 10")
body_type_dist = valid_df.groupby('body_type')['user_count'].sum().sort_values(ascending=False)
for i, (body_type, count) in enumerate(body_type_dist.head(10).items(), 1):
    pct = count / total_users * 100
    print(f"{i:2d}. {body_type:30s} {count:8,} 人 ({pct:5.2f}%)")

# 2. 腰围分布
print("\n【2】腰围分布")
waist_dist = valid_df.groupby('waist_range')['user_count'].sum().sort_index()
for waist_range, count in waist_dist.items():
    pct = count / total_users * 100
    print(f"    {waist_range:20s} {count:8,} 人 ({pct:5.2f}%)")

# 3. 上胸围分布
print("\n【3】上胸围分布")
bust_dist = valid_df.groupby('bust_range')['user_count'].sum().sort_index()
for bust_range, count in bust_dist.items():
    pct = count / total_users * 100
    print(f"    {bust_range:20s} {count:8,} 人 ({pct:5.2f}%)")

# 4. 统计数据
waist_mean = (valid_df['waist_cm'] * valid_df['user_count']).sum() / total_users
bust_mean = (valid_df['upper_bust_cm'] * valid_df['user_count']).sum() / total_users
waist_median = valid_df.loc[valid_df.index.repeat(valid_df['user_count'])]['waist_cm'].median()
bust_median = valid_df.loc[valid_df.index.repeat(valid_df['user_count'])]['upper_bust_cm'].median()

print("\n【4】尺寸统计数据（清洗后）")
print(f"腰围: 平均 {waist_mean:.1f}cm ({waist_mean/2.54:.1f}\")")
print(f"      中位数 {waist_median:.1f}cm ({waist_median/2.54:.1f}\")")
print(f"上胸围: 平均 {bust_mean:.1f}cm ({bust_mean/2.54:.1f}\")")
print(f"        中位数 {bust_median:.1f}cm ({bust_median/2.54:.1f}\")")

# 5. 完整身材画像 Top 15
print("\n【5】完整身材画像 Top 15")
full_profile_dist = valid_df.groupby('full_profile')['user_count'].sum().sort_values(ascending=False)
for i, (profile, count) in enumerate(full_profile_dist.head(15).items(), 1):
    pct = count / total_users * 100
    print(f"{i:2d}. {profile:70s} {count:7,} 人 ({pct:5.2f}%)")

# 按站点分析
print("\n" + "=" * 80)
print("分站点详细分析（清洗后）")
print("=" * 80)

for site in sorted(valid_df['site_code'].unique()):
    site_df = valid_df[valid_df['site_code'] == site]
    site_users = site_df['user_count'].sum()

    print(f"\n{'▶ ' + site + ' 站点':=^78}")
    print(f"清洗后用户数: {site_users:,}")

    # 站点身材类型 Top 5
    print(f"\n  身材类型 Top 5:")
    for i, (body_type, count) in enumerate(site_df.groupby('body_type')['user_count'].sum().sort_values(ascending=False).head(5).items(), 1):
        pct = count / site_users * 100
        print(f"    {i}. {body_type:30s} {count:7,} 人 ({pct:5.2f}%)")

    # 站点腰围分布
    print(f"\n  腰围分布:")
    for waist_range, count in site_df.groupby('waist_range')['user_count'].sum().sort_index().items():
        pct = count / site_users * 100
        bar = '█' * int(pct / 2)
        print(f"    {waist_range:20s} {count:7,} 人 ({pct:5.2f}%) {bar}")

    # 站点上胸围分布
    print(f"\n  上胸围分布:")
    for bust_range, count in site_df.groupby('bust_range')['user_count'].sum().sort_index().items():
        pct = count / site_users * 100
        bar = '█' * int(pct / 2)
        print(f"    {bust_range:20s} {count:7,} 人 ({pct:5.2f}%) {bar}")

    # 站点尺寸统计
    site_waist_mean = (site_df['waist_cm'] * site_df['user_count']).sum() / site_users
    site_bust_mean = (site_df['upper_bust_cm'] * site_df['user_count']).sum() / site_users

    print(f"\n  尺寸统计:")
    print(f"    腰围: 平均 {site_waist_mean:.1f}cm ({site_waist_mean/2.54:.1f}\")")
    print(f"    上胸围: 平均 {site_bust_mean:.1f}cm ({site_bust_mean/2.54:.1f}\")")

print("\n" + "=" * 80)
print("分析完成")
print("=" * 80)

# 保存清洗后的数据摘要
summary = {
    "data_quality": {
        "original_users": int(basic_total),
        "cleaned_users": int(total_users),
        "removed_users": int(abnormal_users),
        "removed_percentage": round(abnormal_pct, 2),
        "cleaning_rules": {
            "waist_range": f"{WAIST_MIN}-{WAIST_MAX}cm",
            "bust_range": f"{BUST_MIN}-{BUST_MAX}cm"
        }
    },
    "cleaned_statistics": {
        "waist_mean_cm": round(waist_mean, 1),
        "waist_mean_inch": round(waist_mean/2.54, 1),
        "bust_mean_cm": round(bust_mean, 1),
        "bust_mean_inch": round(bust_mean/2.54, 1)
    }
}

output_file = '/Users/yixiqian/daily-work-summary/body_measurements_cleaned_summary.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)

print(f"\n清洗摘要已保存到: {output_file}")
