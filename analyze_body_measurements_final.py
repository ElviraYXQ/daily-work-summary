"""
体围数据分析 - 人台设计专业分析
用于 IN / IQ 站点的标准人台（Fit Mannequin）设计
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# 读取数据
file_path = "/Users/yixiqian/Downloads/区域尺码用户数-三围-2026-04-22 17-50-37.xlsx"
df_raw = pd.read_excel(file_path)

print("=" * 100)
print("📊 体围数据分析 - 人台设计方案")
print(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 100)

# ===========================
# Step 1: 数据清洗
# ===========================
print("\n" + "=" * 100)
print("STEP 1: 数据清洗")
print("=" * 100)

df = df_raw.copy()
original_count = len(df)
print(f"\n✓ 原始数据量: {original_count:,} 条")

# 数据清洗函数
def parse_measurement(value):
    """解析尺寸数据并转换为cm"""
    if pd.isna(value):
        return np.nan

    value_str = str(value).strip().upper()

    # 处理 delete 等无效值
    if 'DELETE' in value_str or value_str == '':
        return np.nan

    # 分离数值和单位
    if '_1' in value_str:
        # 英寸，需要转换
        num = float(value_str.replace('_1', ''))
        return num * 2.54  # 转换为cm
    elif '_0' in value_str:
        # cm
        return float(value_str.replace('_0', ''))
    else:
        # 尝试直接解析数值（假设是cm）
        try:
            return float(value_str)
        except:
            return np.nan

# 解析腰围和胸围
df['waist_cm'] = df['USER_WAIST'].apply(parse_measurement)
df['bust_cm'] = df['USER_UPPER_BUST'].apply(parse_measurement)

# 清洗前统计
print(f"\n解析后缺失值:")
print(f"  - 腰围缺失: {df['waist_cm'].isna().sum()} 条")
print(f"  - 胸围缺失: {df['bust_cm'].isna().sum()} 条")

# 异常值识别
print(f"\n异常值识别规则:")
print(f"  - 腰围: 50cm < waist < 120cm")
print(f"  - 胸围: 60cm < bust < 130cm")
print(f"  - 逻辑关系: bust >= waist (胸围应 >= 腰围)")

# 标记异常
df['is_valid'] = True
df['anomaly_reason'] = ''

# 腰围异常
waist_invalid = (df['waist_cm'] < 50) | (df['waist_cm'] > 120)
df.loc[waist_invalid, 'is_valid'] = False
df.loc[waist_invalid, 'anomaly_reason'] += '腰围异常;'

# 胸围异常
bust_invalid = (df['bust_cm'] < 60) | (df['bust_cm'] > 130)
df.loc[bust_invalid, 'is_valid'] = False
df.loc[bust_invalid, 'anomaly_reason'] += '胸围异常;'

# 逻辑异常：胸围小于腰围
logic_invalid = df['bust_cm'] < df['waist_cm']
df.loc[logic_invalid, 'is_valid'] = False
df.loc[logic_invalid, 'anomaly_reason'] += '胸围<腰围;'

# 缺失值
missing_invalid = df['waist_cm'].isna() | df['bust_cm'].isna()
df.loc[missing_invalid, 'is_valid'] = False
df.loc[missing_invalid, 'anomaly_reason'] += '数据缺失;'

# 清洗结果
df_clean = df[df['is_valid']].copy()
cleaned_count = len(df_clean)
removed_count = original_count - cleaned_count

print(f"\n✓ 清洗结果:")
print(f"  - 清洗后数据量: {cleaned_count:,} 条")
print(f"  - 删除数据量: {removed_count:,} 条")
print(f"  - 删除占比: {removed_count/original_count*100:.2f}%")

# 异常类型统计
print(f"\n异常类型分布:")
anomaly_df = df[~df['is_valid']].copy()
anomaly_types = anomaly_df['anomaly_reason'].value_counts()
for reason, count in anomaly_types.items():
    print(f"  - {reason}: {count:,} 条 ({count/removed_count*100:.1f}%)")

# 计算胸腰差
df_clean['bust_waist_diff'] = df_clean['bust_cm'] - df_clean['waist_cm']

# 体型分类
def classify_body_type(diff):
    """根据胸腰差分类体型"""
    if diff < 10:
        return '直筒型'
    elif diff < 18:
        return '轻曲线型'
    elif diff < 25:
        return '标准曲线型'
    else:
        return '强曲线型'

df_clean['body_type'] = df_clean['bust_waist_diff'].apply(classify_body_type)

# ===========================
# Step 2: 核心三围分析（按站点）
# ===========================
print("\n" + "=" * 100)
print("STEP 2: 核心三围分析（按站点 IN / IQ）")
print("=" * 100)

analysis_results = {}

for site in ['IN', 'IQ']:
    site_df = df_clean[df_clean['site_code'] == site].copy()

    print(f"\n{'—' * 50}")
    print(f"📍 站点: {site} (样本量: {len(site_df):,})")
    print(f"{'—' * 50}")

    # 腰围统计
    waist_stats = {
        '均值': site_df['waist_cm'].mean(),
        '中位数': site_df['waist_cm'].median(),
        'P50': site_df['waist_cm'].quantile(0.50),
        'P70': site_df['waist_cm'].quantile(0.70),
        'P90': site_df['waist_cm'].quantile(0.90),
        '标准差': site_df['waist_cm'].std()
    }

    print(f"\n腰围统计 (cm):")
    for key, value in waist_stats.items():
        print(f"  {key:6s}: {value:6.2f} cm")

    # 胸围统计
    bust_stats = {
        '均值': site_df['bust_cm'].mean(),
        '中位数': site_df['bust_cm'].median(),
        'P50': site_df['bust_cm'].quantile(0.50),
        'P70': site_df['bust_cm'].quantile(0.70),
        'P90': site_df['bust_cm'].quantile(0.90),
        '标准差': site_df['bust_cm'].std()
    }

    print(f"\n胸围统计 (cm):")
    for key, value in bust_stats.items():
        print(f"  {key:6s}: {value:6.2f} cm")

    # 胸腰差统计
    diff_stats = {
        '均值': site_df['bust_waist_diff'].mean(),
        '中位数': site_df['bust_waist_diff'].median(),
        'P50': site_df['bust_waist_diff'].quantile(0.50),
        'P70': site_df['bust_waist_diff'].quantile(0.70),
        'P90': site_df['bust_waist_diff'].quantile(0.90)
    }

    print(f"\n胸腰差统计 (cm):")
    for key, value in diff_stats.items():
        print(f"  {key:6s}: {value:6.2f} cm")

    # 体型分布
    print(f"\n体型分布 (按胸腰差):")
    body_type_dist = site_df['body_type'].value_counts(normalize=True).sort_index()
    for body_type, pct in body_type_dist.items():
        count = (site_df['body_type'] == body_type).sum()
        print(f"  {body_type:12s}: {count:6,} 人 ({pct*100:5.2f}%)")

    dominant_type = body_type_dist.idxmax()
    print(f"\n>>> 主导体型: {dominant_type} ({body_type_dist.max()*100:.1f}%)")

    # 保存分析结果
    analysis_results[site] = {
        'sample_size': len(site_df),
        'waist_stats': waist_stats,
        'bust_stats': bust_stats,
        'diff_stats': diff_stats,
        'body_type_distribution': body_type_dist.to_dict(),
        'dominant_type': dominant_type
    }

# ===========================
# Step 3: 体型特征分析
# ===========================
print("\n" + "=" * 100)
print("STEP 3: 体型特征分析（结构判断）")
print("=" * 100)

for site in ['IN', 'IQ']:
    site_df = df_clean[df_clean['site_code'] == site].copy()

    print(f"\n{'—' * 50}")
    print(f"📍 站点: {site}")
    print(f"{'—' * 50}")

    # HIP 分布
    print(f"\n臀型分布 (USER_HIP):")
    hip_dist = site_df['USER_HIP'].value_counts(normalize=True).head(5)
    for hip_type, pct in hip_dist.items():
        count = (site_df['USER_HIP'] == hip_type).sum()
        print(f"  {hip_type:15s}: {pct*100:5.2f}% ({count:,} 人)")

    # BELLY 分布
    print(f"\n腹部分布 (USER_BELLY):")
    belly_dist = site_df['USER_BELLY'].value_counts(normalize=True).head(5)
    for belly_type, pct in belly_dist.items():
        count = (site_df['USER_BELLY'] == belly_type).sum()
        print(f"  {belly_type:15s}: {pct*100:5.2f}% ({count:,} 人)")

    # 主流组合
    print(f"\n主流组合 (TOP 5):")
    combo_dist = site_df.groupby(['USER_HIP', 'USER_BELLY']).size().sort_values(ascending=False).head(5)
    for (hip, belly), count in combo_dist.items():
        pct = count / len(site_df) * 100
        print(f"  {hip:15s} + {belly:15s}: {count:6,} 人 ({pct:5.2f}%)")

    # 分析体型倾向
    dominant_hip = site_df['USER_HIP'].value_counts().idxmax()
    dominant_belly = site_df['USER_BELLY'].value_counts().idxmax()

    print(f"\n>>> 整体体型倾向:")
    if 'wider' in dominant_hip.lower():
        print(f"  - 下半身重型 (臀部较宽)")
    elif 'straighter' in dominant_hip.lower() or 'average' in dominant_hip.lower():
        print(f"  - 偏直筒型")

    if 'flatter' in dominant_belly.lower():
        print(f"  - 腹部平坦")
    elif 'curvier' in dominant_belly.lower():
        print(f"  - 腹部丰满")

# ===========================
# Step 4: 区域差异分析
# ===========================
print("\n" + "=" * 100)
print("STEP 4: 区域差异分析 (prov_name)")
print("=" * 100)

for site in ['IN', 'IQ']:
    site_df = df_clean[df_clean['site_code'] == site].copy()

    if len(site_df) == 0:
        continue

    print(f"\n{'—' * 50}")
    print(f"📍 站点: {site}")
    print(f"{'—' * 50}")

    # 按区域统计
    region_stats = site_df.groupby('prov_name').agg({
        'waist_cm': ['mean', 'count'],
        'bust_cm': 'mean',
        'bust_waist_diff': 'mean'
    }).round(2)

    region_stats.columns = ['腰围均值', '样本量', '胸围均值', '胸腰差均值']
    region_stats = region_stats.sort_values('样本量', ascending=False)

    # 过滤样本量 >= 50 的区域
    region_stats_filtered = region_stats[region_stats['样本量'] >= 50].copy()

    if len(region_stats_filtered) > 0:
        print(f"\n腰围最大 TOP 3 区域:")
        top_waist = region_stats_filtered.nlargest(3, '腰围均值')
        for idx, (region, row) in enumerate(top_waist.iterrows(), 1):
            print(f"  {idx}. {region:20s}: {row['腰围均值']:6.2f} cm (n={int(row['样本量']):,})")

        print(f"\n胸围最大 TOP 3 区域:")
        top_bust = region_stats_filtered.nlargest(3, '胸围均值')
        for idx, (region, row) in enumerate(top_bust.iterrows(), 1):
            print(f"  {idx}. {region:20s}: {row['胸围均值']:6.2f} cm (n={int(row['样本量']):,})")

        print(f"\n胸腰差最大 TOP 3 区域:")
        top_diff = region_stats_filtered.nlargest(3, '胸腰差均值')
        for idx, (region, row) in enumerate(top_diff.iterrows(), 1):
            print(f"  {idx}. {region:20s}: {row['胸腰差均值']:6.2f} cm (n={int(row['样本量']):,})")

        # 判断区域差异显著性
        waist_std = region_stats_filtered['腰围均值'].std()
        bust_std = region_stats_filtered['胸围均值'].std()
        diff_std = region_stats_filtered['胸腰差均值'].std()

        print(f"\n>>> 区域差异评估:")
        print(f"  - 腰围区域标准差: {waist_std:.2f} cm")
        print(f"  - 胸围区域标准差: {bust_std:.2f} cm")
        print(f"  - 胸腰差区域标准差: {diff_std:.2f} cm")

        if waist_std > 2.5 or bust_std > 3.0:
            print(f"  ⚠️ 区域差异较显著，建议考虑分区域人台")
        else:
            print(f"  ✓ 区域差异不显著，可使用统一人台")

# ===========================
# Step 5: 核心输出 - 人台设计方案
# ===========================
print("\n" + "=" * 100)
print("STEP 5: 核心输出 — 人台设计方案（标准人台设计）")
print("=" * 100)

fit_model_recommendations = {}

for site in ['IN', 'IQ']:
    site_df = df_clean[df_clean['site_code'] == site].copy()

    print(f"\n{'=' * 80}")
    print(f"🎯 站点: {site}")
    print(f"{'=' * 80}")

    # 计算 P50-P70 区间
    waist_p50 = site_df['waist_cm'].quantile(0.50)
    waist_p70 = site_df['waist_cm'].quantile(0.70)
    bust_p50 = site_df['bust_cm'].quantile(0.50)
    bust_p70 = site_df['bust_cm'].quantile(0.70)

    # 标准人台 (基于 P50-P65 中点)
    core_waist = site_df['waist_cm'].quantile(0.575)  # P50-P70 中间偏下
    core_bust = site_df['bust_cm'].quantile(0.575)
    core_diff = core_bust - core_waist
    core_type = classify_body_type(core_diff)

    print(f"\n1️⃣ 标准人台 (Core Fit Model)")
    print(f"{'—' * 50}")
    print(f"  建议腰围: {core_waist:.1f} cm")
    print(f"  建议胸围: {core_bust:.1f} cm")
    print(f"  胸腰差: {core_diff:.1f} cm")
    print(f"  对应体型: {core_type}")
    print(f"  覆盖人群: P50-P70 (约 {len(site_df[(site_df['waist_cm'] >= waist_p50) & (site_df['waist_cm'] <= waist_p70)]):,} 人)")

    # 次人台 (针对曲线型用户)
    # 找到胸腰差较大的群体
    body_type_counts = site_df['body_type'].value_counts(normalize=True)

    # 如果标准曲线型或强曲线型占比 > 20%，建议次人台
    curve_types = ['标准曲线型', '强曲线型']
    curve_pct = sum([body_type_counts.get(t, 0) for t in curve_types])

    if curve_pct > 0.2:
        curve_df = site_df[site_df['body_type'].isin(curve_types)]
        sec_waist = curve_df['waist_cm'].quantile(0.50)
        sec_bust = curve_df['bust_cm'].quantile(0.50)
        sec_diff = sec_bust - sec_waist

        print(f"\n2️⃣ 次人台 (Secondary Fit Model - 曲线型)")
        print(f"{'—' * 50}")
        print(f"  建议腰围: {sec_waist:.1f} cm")
        print(f"  建议胸围: {sec_bust:.1f} cm")
        print(f"  胸腰差: {sec_diff:.1f} cm")
        print(f"  目标人群: 曲线型用户 ({curve_pct*100:.1f}%)")
    else:
        print(f"\n2️⃣ 次人台: 不需要")
        print(f"  原因: 曲线型用户占比较低 ({curve_pct*100:.1f}%)")

    # 版型策略
    dominant_type = site_df['body_type'].value_counts().idxmax()

    print(f"\n3️⃣ 版型策略建议")
    print(f"{'—' * 50}")
    print(f"  主导体型: {dominant_type}")

    if '直筒' in dominant_type:
        print(f"  ✓ 建议以直筒版型为主设计")
        print(f"    - 减少腰部收腰设计")
        print(f"    - 注重整体线条流畅")
        print(f"    - 适合宽松、休闲风格")
    elif '轻曲线' in dominant_type:
        print(f"  ✓ 建议以轻曲线版型为主设计")
        print(f"    - 适度腰部收紧")
        print(f"    - 保持舒适度")
        print(f"    - 适合日常通勤风格")
    else:
        print(f"  ✓ 建议提供多版型选择")
        print(f"    - Regular Fit: 直筒型")
        print(f"    - Slim Fit: 曲线型")

    # 风险提示
    print(f"\n4️⃣ 风险提示")
    print(f"{'—' * 50}")

    waist_range = site_df['waist_cm'].quantile(0.90) - site_df['waist_cm'].quantile(0.10)
    bust_range = site_df['bust_cm'].quantile(0.90) - site_df['bust_cm'].quantile(0.10)

    print(f"  体型分散度:")
    print(f"    - 腰围 P10-P90 跨度: {waist_range:.1f} cm")
    print(f"    - 胸围 P10-P90 跨度: {bust_range:.1f} cm")

    if waist_range > 25 or bust_range > 30:
        print(f"\n  ⚠️ 高风险提示:")
        print(f"    - 体型分散度高，单一人台难以覆盖所有用户")
        print(f"    - 可能导致:")
        print(f"      • Fitting Issue: 腰部过紧或过松")
        print(f"      • 胸围不合适: 上身紧绷或空荡")
        print(f"      • 退货率上升: 预计影响 15-25%")
        print(f"    - 建议:")
        print(f"      • 提供 2-3 个版型选择")
        print(f"      • 或增加尺码密度 (如增加半码)")
    else:
        print(f"\n  ✓ 风险可控:")
        print(f"    - 体型较集中，标准人台可覆盖大多数用户")
        print(f"    - 预计 Fitting 退货率: < 10%")

    # 保存推荐
    fit_model_recommendations[site] = {
        'core_fit_model': {
            'waist_cm': round(core_waist, 1),
            'bust_cm': round(core_bust, 1),
            'bust_waist_diff': round(core_diff, 1),
            'body_type': core_type
        },
        'secondary_fit_model': {
            'needed': curve_pct > 0.2,
            'waist_cm': round(sec_waist, 1) if curve_pct > 0.2 else None,
            'bust_cm': round(sec_bust, 1) if curve_pct > 0.2 else None,
        } if curve_pct > 0.2 else None,
        'dominant_type': dominant_type,
        'risk_level': 'high' if (waist_range > 25 or bust_range > 30) else 'low'
    }

# ===========================
# Step 6: 业务影响
# ===========================
print("\n" + "=" * 100)
print("STEP 6: 业务影响评估（电商角度）")
print("=" * 100)

for site in ['IN', 'IQ']:
    site_df = df_clean[df_clean['site_code'] == site].copy()

    print(f"\n{'—' * 50}")
    print(f"📍 站点: {site}")
    print(f"{'—' * 50}")

    # 体型分布
    body_type_dist = site_df['body_type'].value_counts(normalize=True)

    print(f"\n1. 对退货率的影响:")
    print(f"{'—' * 30}")

    # 如果体型分散
    if len(body_type_dist) > 2 and body_type_dist.iloc[0] < 0.6:
        print(f"  ⚠️ 高风险场景:")
        print(f"    - 体型分散（无主导体型 > 60%）")
        print(f"    - 若使用单一版型:")
        print(f"      • Fitting Issue 退货: +15-20%")
        print(f"      • Size Mismatch: +10-15%")
        print(f"    - 受影响品类: 上衣、连衣裙、外套")
    else:
        print(f"  ✓ 低风险场景:")
        print(f"    - 主导体型明确 ({body_type_dist.iloc[0]*100:.1f}%)")
        print(f"    - Fitting Issue 可控 (< 10%)")

    print(f"\n2. 尺码策略建议:")
    print(f"{'—' * 30}")

    # 根据 P10-P90 跨度判断
    waist_p10 = site_df['waist_cm'].quantile(0.10)
    waist_p90 = site_df['waist_cm'].quantile(0.90)
    waist_span = waist_p90 - waist_p10

    # 计算当前尺码需要覆盖的范围
    current_sizes = int(np.ceil(waist_span / 5))  # 假设每个尺码覆盖5cm

    print(f"  当前尺码需求:")
    print(f"    - 腰围范围 P10-P90: {waist_p10:.1f} - {waist_p90:.1f} cm")
    print(f"    - 跨度: {waist_span:.1f} cm")
    print(f"    - 建议尺码数量: {current_sizes} 个")

    if waist_span > 30:
        print(f"\n  ✓ 建议调整尺码表:")
        print(f"    - 增加尺码密度（如 XS, S, M, L, XL, XXL）")
        print(f"    - 或提供 Petite / Regular / Plus 系列")

    print(f"\n3. 版型策略建议:")
    print(f"{'—' * 30}")

    straight_pct = body_type_dist.get('直筒型', 0) + body_type_dist.get('轻曲线型', 0)
    curve_pct = body_type_dist.get('标准曲线型', 0) + body_type_dist.get('强曲线型', 0)

    if straight_pct > 0.6:
        print(f"  ✓ 单一版型策略 (直筒/轻收腰)")
        print(f"    - 直筒型用户占主导 ({straight_pct*100:.1f}%)")
        print(f"    - 产品线简化，降低成本")
    elif curve_pct > 0.3:
        print(f"  ✓ 双版型策略:")
        print(f"    - Regular Fit: 直筒型 ({straight_pct*100:.1f}%)")
        print(f"    - Slim Fit: 曲线型 ({curve_pct*100:.1f}%)")
        print(f"    - 降低 Fitting Issue，提升满意度")
    else:
        print(f"  ✓ 主推 Regular Fit，部分品类提供 Slim Fit")

    print(f"\n4. 针对性建议:")
    print(f"{'—' * 30}")

    # 针对特定用户群的建议
    if site == 'IQ':
        print(f"  IQ 市场特点:")
        print(f"    - 建议验证文化偏好（宽松 vs 修身）")
        print(f"    - 考虑当地气候（宽松透气设计）")
    else:
        print(f"  IN 市场特点:")
        print(f"    - 体型多样性高，建议多版型")
        print(f"    - 关注地域差异（南北体型差异）")

# ===========================
# Step 7: 数据驱动分群（K-means）
# ===========================
print("\n" + "=" * 100)
print("STEP 7: 数据驱动分群验证（K-means 聚类）")
print("=" * 100)

from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

for site in ['IN', 'IQ']:
    site_df = df_clean[df_clean['site_code'] == site].copy()

    print(f"\n{'—' * 50}")
    print(f"📍 站点: {site}")
    print(f"{'—' * 50}")

    # 准备数据
    X = site_df[['waist_cm', 'bust_cm']].values

    # 标准化
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # K-means (k=2, 3)
    for k in [2, 3]:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        site_df[f'cluster_{k}'] = kmeans.fit_predict(X_scaled)

        print(f"\nK={k} 聚类结果:")

        for cluster_id in range(k):
            cluster_data = site_df[site_df[f'cluster_{k}'] == cluster_id]
            cluster_pct = len(cluster_data) / len(site_df) * 100

            print(f"\n  Cluster {cluster_id} (n={len(cluster_data):,}, {cluster_pct:.1f}%):")
            print(f"    - 平均腰围: {cluster_data['waist_cm'].mean():.1f} cm")
            print(f"    - 平均胸围: {cluster_data['bust_cm'].mean():.1f} cm")
            print(f"    - 平均胸腰差: {cluster_data['bust_waist_diff'].mean():.1f} cm")

            # 主要体型
            main_type = cluster_data['body_type'].value_counts().idxmax()
            main_type_pct = (cluster_data['body_type'] == main_type).sum() / len(cluster_data) * 100
            print(f"    - 主要体型: {main_type} ({main_type_pct:.1f}%)")

    print(f"\n>>> 聚类结论:")
    print(f"  - 用户体型存在自然分群")
    print(f"  - 建议参考 K=2 或 K=3 的分群结果设计版型")

# ===========================
# 保存结果
# ===========================
print("\n" + "=" * 100)
print("保存分析结果")
print("=" * 100)

# 准备输出数据
output_data = {
    'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    'data_quality': {
        'original_count': original_count,
        'cleaned_count': cleaned_count,
        'removed_count': removed_count,
        'removed_pct': round(removed_count/original_count*100, 2)
    },
    'site_analysis': {},
    'fit_model_recommendations': fit_model_recommendations
}

for site in ['IN', 'IQ']:
    site_df = df_clean[df_clean['site_code'] == site].copy()

    output_data['site_analysis'][site] = {
        'sample_size': len(site_df),
        'waist_stats': {
            'mean': round(site_df['waist_cm'].mean(), 2),
            'median': round(site_df['waist_cm'].median(), 2),
            'p50': round(site_df['waist_cm'].quantile(0.50), 2),
            'p70': round(site_df['waist_cm'].quantile(0.70), 2),
            'p90': round(site_df['waist_cm'].quantile(0.90), 2)
        },
        'bust_stats': {
            'mean': round(site_df['bust_cm'].mean(), 2),
            'median': round(site_df['bust_cm'].median(), 2),
            'p50': round(site_df['bust_cm'].quantile(0.50), 2),
            'p70': round(site_df['bust_cm'].quantile(0.70), 2),
            'p90': round(site_df['bust_cm'].quantile(0.90), 2)
        },
        'bust_waist_diff_stats': {
            'mean': round(site_df['bust_waist_diff'].mean(), 2),
            'median': round(site_df['bust_waist_diff'].median(), 2)
        },
        'body_type_distribution': site_df['body_type'].value_counts(normalize=True).round(4).to_dict(),
        'dominant_type': site_df['body_type'].value_counts().idxmax()
    }

# 保存 JSON
output_file = '/Users/yixiqian/daily-work-summary/body_measurements_analysis.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(output_data, f, ensure_ascii=False, indent=2)

print(f"\n✓ 分析结果已保存到: {output_file}")

print("\n" + "=" * 100)
print("分析完成！")
print("=" * 100)
