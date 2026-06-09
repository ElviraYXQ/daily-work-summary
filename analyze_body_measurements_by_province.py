"""
省份级三围画像分析
按站点 + 省份输出三围分布，识别区域差异
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# ===========================
# 省份翻译字典
# ===========================
PROVINCE_TRANSLATION = {
    # 印度省份（IN）
    'Andhra Pradesh': '安得拉邦',
    'Arunachal Pradesh': '阿鲁纳恰尔邦',
    'Assam': '阿萨姆邦',
    'Bihar': '比哈尔邦',
    'Chhattisgarh': '恰蒂斯加尔邦',
    'Goa': '果阿邦',
    'Gujarat': '古吉拉特邦',
    'Haryana': '哈里亚纳邦',
    'Himachal Pradesh': '喜马偕尔邦',
    'Jharkhand': '贾坎德邦',
    'Karnataka': '卡纳塔克邦',
    'Kerala': '喀拉拉邦',
    'Madhya Pradesh': '中央邦',
    'Maharashtra': '马哈拉施特拉邦',
    'Manipur': '曼尼普尔邦',
    'Meghalaya': '梅加拉亚邦',
    'Mizoram': '米佐拉姆邦',
    'Nagaland': '那加兰邦',
    'Odisha': '奥迪沙邦',
    'Punjab': '旁遮普邦',
    'Rajasthan': '拉贾斯坦邦',
    'Sikkim': '锡金邦',
    'Tamil Nadu': '泰米尔纳德邦',
    'Telangana': '特伦甘纳邦',
    'Tripura': '特里普拉邦',
    'Uttar Pradesh': '北方邦',
    'Uttarakhand': '北阿坎德邦',
    'West Bengal': '西孟加拉邦',
    'Andaman and Nicobar Islands': '安达曼-尼科巴群岛',
    'Chandigarh': '昌迪加尔',
    'Dadra and Nagar Haveli': '达德拉-纳加尔哈维利',
    'Daman and Diu': '达曼-第乌',
    'Delhi': '德里',
    'Jammu & Kashmir': '查谟-克什米尔',
    'Lakshadweep': '拉克沙群岛',
    'Puducherry': '本地治里',

    # 伊拉克省份（IQ）
    'بغداد': '巴格达',
    'البصرة': '巴士拉',
    'نينوى': '尼尼微',
    'الأنبار': '安巴尔',
    'أربيل': '埃尔比勒',
    'كركوك': '基尔库克',
    'النجف': '纳杰夫',
    'كربلاء': '卡尔巴拉',
    'بابل': '巴比伦',
    'ديالى': '迪亚拉',
    'ذي قار': '济加尔',
    'المثنى': '穆萨纳',
    'القادسية': '卡迪西亚',
    'ميسان': '米桑',
    'واسط': '瓦西特',
    'صلاح الدين': '萨拉赫丁',
    'السليمانية': '苏莱曼尼亚',
    'دهوك': '杜胡克',
    'الديوانية': '迪瓦尼亚',
}

def translate_province(prov_name):
    """翻译省份名称，返回"原始名称（中文翻译）"格式"""
    if pd.isna(prov_name) or prov_name == '':
        return '未知省份'

    prov_name = str(prov_name).strip()
    if prov_name in PROVINCE_TRANSLATION:
        return f"{prov_name}（{PROVINCE_TRANSLATION[prov_name]}）"
    else:
        return f"{prov_name}（待确认翻译）"

# 读取数据
file_path = "/Users/yixiqian/Downloads/区域尺码用户数-三围-2026-04-22 17-50-37.xlsx"
df_raw = pd.read_excel(file_path)

print("=" * 120)
print("省份级三围画像分析报告")
print(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 120)

# ===========================
# 第一步：严格数据清洗
# ===========================
print("\n" + "=" * 120)
print("第一步：严格数据清洗")
print("=" * 120)

df = df_raw.copy()
original_records = len(df)
original_users = df['usr_id'].nunique()

print(f"\n原始数据:")
print(f"  - 原始记录数: {original_records:,}")
print(f"  - 原始用户数: {original_users:,}")

# 检查 usr_id 唯一性
duplicate_users = df[df.duplicated(subset=['usr_id'], keep=False)]
if len(duplicate_users) > 0:
    print(f"\n⚠️ 发现重复用户: {len(duplicate_users):,} 条记录涉及 {duplicate_users['usr_id'].nunique():,} 个用户")
    print(f"  处理方式: 保留每个用户的首次出现记录")
    df = df.drop_duplicates(subset=['usr_id'], keep='first')
    print(f"  去重后记录数: {len(df):,}")
else:
    print(f"\n✓ usr_id 唯一性检查通过")

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

# 计算胸腰差
df['bust_waist_diff'] = df['bust_cm'] - df['waist_cm']

print(f"\n数值解析结果:")
print(f"  - 腰围解析成功: {df['waist_cm'].notna().sum():,} 条")
print(f"  - 胸围解析成功: {df['bust_cm'].notna().sum():,} 条")

# 异常值识别
print(f"\n异常值识别规则:")
print(f"  1. 腰围 < 50 cm 或 > 120 cm")
print(f"  2. 上胸围 < 65 cm 或 > 140 cm")
print(f"  3. 上胸围 <= 腰围")
print(f"  4. 胸腰差 < 3 cm（高风险）")
print(f"  5. 胸腰差 > 40 cm（高风险）")

# 标记异常
df['is_valid'] = True
df['anomaly_reason'] = ''

# 腰围异常
waist_invalid = (df['waist_cm'] < 50) | (df['waist_cm'] > 120)
df.loc[waist_invalid, 'is_valid'] = False
df.loc[waist_invalid, 'anomaly_reason'] += '腰围异常;'

# 胸围异常
bust_invalid = (df['bust_cm'] < 65) | (df['bust_cm'] > 140)
df.loc[bust_invalid, 'is_valid'] = False
df.loc[bust_invalid, 'anomaly_reason'] += '胸围异常;'

# 逻辑异常：胸围小于等于腰围
logic_invalid = df['bust_cm'] <= df['waist_cm']
df.loc[logic_invalid, 'is_valid'] = False
df.loc[logic_invalid, 'anomaly_reason'] += '胸围<=腰围;'

# 胸腰差异常
diff_invalid = (df['bust_waist_diff'] < 3) | (df['bust_waist_diff'] > 40)
df.loc[diff_invalid & df['bust_waist_diff'].notna(), 'is_valid'] = False
df.loc[diff_invalid & df['bust_waist_diff'].notna(), 'anomaly_reason'] += '胸腰差异常;'

# 缺失值
missing_invalid = df['waist_cm'].isna() | df['bust_cm'].isna()
df.loc[missing_invalid, 'is_valid'] = False
df.loc[missing_invalid, 'anomaly_reason'] += '数据缺失;'

# 清洗结果
df_clean = df[df['is_valid']].copy()
cleaned_records = len(df_clean)
cleaned_users = df_clean['usr_id'].nunique()
removed_records = original_records - cleaned_records
removed_users = original_users - cleaned_users

print(f"\n✓ 清洗结果:")
print(f"  - 清洗后记录数: {cleaned_records:,}")
print(f"  - 清洗后用户数: {cleaned_users:,}")
print(f"  - 被剔除记录数: {removed_records:,} ({removed_records/original_records*100:.2f}%)")
print(f"  - 被剔除用户数: {removed_users:,} ({removed_users/original_users*100:.2f}%)")

# 异常类型分布
print(f"\n异常类型分布:")
anomaly_df = df[~df['is_valid']].copy()
anomaly_types = anomaly_df['anomaly_reason'].value_counts()
for reason, count in anomaly_types.head(10).items():
    print(f"  - {reason}: {count:,} 条 ({count/len(anomaly_df)*100:.1f}%)")

# 各站点异常分布
print(f"\n各站点异常类型分布:")
for site in df['site_code'].unique():
    site_anomaly = anomaly_df[anomaly_df['site_code'] == site]
    if len(site_anomaly) > 0:
        print(f"\n  站点 {site}:")
        print(f"    - 异常记录: {len(site_anomaly):,} 条")
        print(f"    - 异常占比: {len(site_anomaly)/len(df[df['site_code']==site])*100:.1f}%")
        top_reasons = site_anomaly['anomaly_reason'].value_counts().head(3)
        for reason, count in top_reasons.items():
            print(f"      • {reason}: {count:,} 条 ({count/len(site_anomaly)*100:.1f}%)")

# 检查是否存在明显脏数据集中省份
print(f"\n脏数据集中省份检查:")
for site in df['site_code'].unique():
    site_df = df[df['site_code'] == site]
    prov_invalid_rate = site_df.groupby('prov_name').apply(
        lambda x: (~x['is_valid']).sum() / len(x) * 100
    ).sort_values(ascending=False)

    high_invalid_provs = prov_invalid_rate[prov_invalid_rate > 50].head(5)
    if len(high_invalid_provs) > 0:
        print(f"\n  站点 {site} - 高异常率省份（> 50%）:")
        for prov, rate in high_invalid_provs.items():
            prov_translated = translate_province(prov)
            prov_count = len(site_df[site_df['prov_name'] == prov])
            print(f"    - {prov_translated}: {rate:.1f}% ({prov_count} 条记录)")

# 体型分类
def classify_body_type(diff):
    """根据胸腰差分类体型"""
    if pd.isna(diff):
        return np.nan
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
# 第二步：省份名称翻译
# ===========================
print("\n" + "=" * 120)
print("第二步：省份名称翻译")
print("=" * 120)

df_clean['prov_name_translated'] = df_clean['prov_name'].apply(translate_province)

print(f"\n✓ 省份翻译完成")
print(f"  所有省份名称已翻译为：原始名称（中文翻译）格式")

# ===========================
# 第三步：按站点 + 省份输出三围画像
# ===========================
print("\n" + "=" * 120)
print("第三步：按站点 + 省份输出三围画像")
print("=" * 120)

# 设置最低样本门槛
MIN_SAMPLE_SIZE = 30

province_profiles = []

for site in sorted(df_clean['site_code'].unique()):
    site_df = df_clean[df_clean['site_code'] == site].copy()

    print(f"\n{'=' * 100}")
    print(f"站点: {site}")
    print(f"{'=' * 100}")

    # 按省份分组
    provinces = site_df.groupby('prov_name')

    for prov_name, prov_df in provinces:
        user_count = len(prov_df)
        prov_translated = translate_province(prov_name)

        # 跳过样本过小的省份（但仍记录）
        if user_count < MIN_SAMPLE_SIZE:
            low_confidence = True
        else:
            low_confidence = False

        # 计算统计量
        profile = {
            'site_code': site,
            'prov_name': prov_name,
            'prov_name_translated': prov_translated,
            'user_count': user_count,
            'low_confidence': low_confidence,

            # 腰围
            'waist_mean': prov_df['waist_cm'].mean(),
            'waist_p50': prov_df['waist_cm'].quantile(0.50),
            'waist_p70': prov_df['waist_cm'].quantile(0.70),
            'waist_p90': prov_df['waist_cm'].quantile(0.90),

            # 胸围
            'bust_mean': prov_df['bust_cm'].mean(),
            'bust_p50': prov_df['bust_cm'].quantile(0.50),
            'bust_p70': prov_df['bust_cm'].quantile(0.70),
            'bust_p90': prov_df['bust_cm'].quantile(0.90),

            # 胸腰差
            'diff_mean': prov_df['bust_waist_diff'].mean(),
            'diff_p50': prov_df['bust_waist_diff'].quantile(0.50),
            'diff_p70': prov_df['bust_waist_diff'].quantile(0.70),
            'diff_p90': prov_df['bust_waist_diff'].quantile(0.90),
        }

        # 体型分布
        body_type_dist = prov_df['body_type'].value_counts(normalize=True)
        for body_type in ['直筒型', '轻曲线型', '标准曲线型', '强曲线型']:
            profile[f'body_type_{body_type}'] = body_type_dist.get(body_type, 0) * 100

        # 主导体型
        if len(body_type_dist) > 0:
            profile['dominant_body_type'] = body_type_dist.idxmax()
        else:
            profile['dominant_body_type'] = '未知'

        province_profiles.append(profile)

        # 打印省份画像
        confidence_tag = " [样本较少，谨慎解读]" if low_confidence else ""
        print(f"\n省份: {prov_translated} (n={user_count}){confidence_tag}")
        print(f"  腰围: 均值={profile['waist_mean']:.1f} cm, P50={profile['waist_p50']:.1f} cm, P70={profile['waist_p70']:.1f} cm, P90={profile['waist_p90']:.1f} cm")
        print(f"  胸围: 均值={profile['bust_mean']:.1f} cm, P50={profile['bust_p50']:.1f} cm, P70={profile['bust_p70']:.1f} cm, P90={profile['bust_p90']:.1f} cm")
        print(f"  胸腰差: 均值={profile['diff_mean']:.1f} cm, P50={profile['diff_p50']:.1f} cm, P70={profile['diff_p70']:.1f} cm, P90={profile['diff_p90']:.1f} cm")
        print(f"  主导体型: {profile['dominant_body_type']}")
        print(f"  体型分布: 直筒型{profile['body_type_直筒型']:.1f}% | 轻曲线型{profile['body_type_轻曲线型']:.1f}% | 标准曲线型{profile['body_type_标准曲线型']:.1f}% | 强曲线型{profile['body_type_强曲线型']:.1f}%")

# 转为 DataFrame
df_profiles = pd.DataFrame(province_profiles)

# ===========================
# 第四步：站点内部省份差异分析
# ===========================
print("\n" + "=" * 120)
print("第四步：站点内部省份差异分析")
print("=" * 120)

for site in sorted(df_profiles['site_code'].unique()):
    site_profiles = df_profiles[df_profiles['site_code'] == site].copy()

    # 只分析样本量足够的省份
    site_profiles_valid = site_profiles[~site_profiles['low_confidence']].copy()

    print(f"\n{'=' * 100}")
    print(f"站点: {site}")
    print(f"  有效省份数: {len(site_profiles_valid)} (样本量 >= {MIN_SAMPLE_SIZE})")
    print(f"  低样本省份数: {site_profiles['low_confidence'].sum()}")
    print(f"{'=' * 100}")

    if len(site_profiles_valid) == 0:
        print(f"  ⚠️ 无足够样本量的省份，跳过差异分析")
        continue

    # 1. 腰围差异
    print(f"\n1️⃣ 腰围差异 (P50)")
    waist_top5_high = site_profiles_valid.nlargest(5, 'waist_p50')[['prov_name_translated', 'waist_p50', 'user_count']]
    waist_top5_low = site_profiles_valid.nsmallest(5, 'waist_p50')[['prov_name_translated', 'waist_p50', 'user_count']]

    print(f"\n  腰围 P50 最高的 Top 5 省份:")
    for idx, row in waist_top5_high.iterrows():
        print(f"    {row['prov_name_translated']}: {row['waist_p50']:.1f} cm (n={int(row['user_count'])})")

    print(f"\n  腰围 P50 最低的 Top 5 省份:")
    for idx, row in waist_top5_low.iterrows():
        print(f"    {row['prov_name_translated']}: {row['waist_p50']:.1f} cm (n={int(row['user_count'])})")

    waist_diff = site_profiles_valid['waist_p50'].max() - site_profiles_valid['waist_p50'].min()
    print(f"\n  >>> 最高与最低省份差值: {waist_diff:.1f} cm")
    if waist_diff > 5:
        print(f"      ⚠️ 差异显著（> 5 cm）")
    else:
        print(f"      ✓ 差异不显著（<= 5 cm）")

    # 2. 胸围差异
    print(f"\n2️⃣ 胸围差异 (P50)")
    bust_top5_high = site_profiles_valid.nlargest(5, 'bust_p50')[['prov_name_translated', 'bust_p50', 'user_count']]
    bust_top5_low = site_profiles_valid.nsmallest(5, 'bust_p50')[['prov_name_translated', 'bust_p50', 'user_count']]

    print(f"\n  胸围 P50 最高的 Top 5 省份:")
    for idx, row in bust_top5_high.iterrows():
        print(f"    {row['prov_name_translated']}: {row['bust_p50']:.1f} cm (n={int(row['user_count'])})")

    print(f"\n  胸围 P50 最低的 Top 5 省份:")
    for idx, row in bust_top5_low.iterrows():
        print(f"    {row['prov_name_translated']}: {row['bust_p50']:.1f} cm (n={int(row['user_count'])})")

    bust_diff = site_profiles_valid['bust_p50'].max() - site_profiles_valid['bust_p50'].min()
    print(f"\n  >>> 最高与最低省份差值: {bust_diff:.1f} cm")

    # 3. 胸腰差差异
    print(f"\n3️⃣ 胸腰差差异 (P50)")
    diff_top5_high = site_profiles_valid.nlargest(5, 'diff_p50')[['prov_name_translated', 'diff_p50', 'user_count']]
    diff_top5_low = site_profiles_valid.nsmallest(5, 'diff_p50')[['prov_name_translated', 'diff_p50', 'user_count']]

    print(f"\n  胸腰差 P50 最高的 Top 5 省份（更偏曲线）:")
    for idx, row in diff_top5_high.iterrows():
        print(f"    {row['prov_name_translated']}: {row['diff_p50']:.1f} cm (n={int(row['user_count'])})")

    print(f"\n  胸腰差 P50 最低的 Top 5 省份（更偏直筒）:")
    for idx, row in diff_top5_low.iterrows():
        print(f"    {row['prov_name_translated']}: {row['diff_p50']:.1f} cm (n={int(row['user_count'])})")

    diff_diff = site_profiles_valid['diff_p50'].max() - site_profiles_valid['diff_p50'].min()
    print(f"\n  >>> 最高与最低省份差值: {diff_diff:.1f} cm")

# ===========================
# 第五步：省份体型分层
# ===========================
print("\n" + "=" * 120)
print("第五步：省份体型分层")
print("=" * 120)

for site in sorted(df_profiles['site_code'].unique()):
    site_profiles = df_profiles[df_profiles['site_code'] == site].copy()
    site_profiles_valid = site_profiles[~site_profiles['low_confidence']].copy()

    if len(site_profiles_valid) == 0:
        continue

    print(f"\n{'=' * 100}")
    print(f"站点: {site}")
    print(f"{'=' * 100}")

    # 计算分位数用于分层
    waist_q33 = site_profiles_valid['waist_p50'].quantile(0.33)
    waist_q67 = site_profiles_valid['waist_p50'].quantile(0.67)

    bust_q33 = site_profiles_valid['bust_p50'].quantile(0.33)
    bust_q67 = site_profiles_valid['bust_p50'].quantile(0.67)

    diff_q33 = site_profiles_valid['diff_p50'].quantile(0.33)
    diff_q67 = site_profiles_valid['diff_p50'].quantile(0.67)

    # 1. 腰围层级
    print(f"\n1️⃣ 腰围层级 (基于 P50)")
    print(f"  分层阈值: {waist_q33:.1f} cm | {waist_q67:.1f} cm")

    waist_small = site_profiles_valid[site_profiles_valid['waist_p50'] < waist_q33]
    waist_medium = site_profiles_valid[(site_profiles_valid['waist_p50'] >= waist_q33) & (site_profiles_valid['waist_p50'] < waist_q67)]
    waist_large = site_profiles_valid[site_profiles_valid['waist_p50'] >= waist_q67]

    print(f"\n  偏小腰围省份 (< {waist_q33:.1f} cm):")
    for idx, row in waist_small.iterrows():
        print(f"    {row['prov_name_translated']}: {row['waist_p50']:.1f} cm")

    print(f"\n  标准腰围省份 ({waist_q33:.1f} - {waist_q67:.1f} cm):")
    for idx, row in waist_medium.iterrows():
        print(f"    {row['prov_name_translated']}: {row['waist_p50']:.1f} cm")

    print(f"\n  偏大腰围省份 (>= {waist_q67:.1f} cm):")
    for idx, row in waist_large.iterrows():
        print(f"    {row['prov_name_translated']}: {row['waist_p50']:.1f} cm")

    # 2. 胸围层级
    print(f"\n2️⃣ 胸围层级 (基于 P50)")
    print(f"  分层阈值: {bust_q33:.1f} cm | {bust_q67:.1f} cm")

    bust_small = site_profiles_valid[site_profiles_valid['bust_p50'] < bust_q33]
    bust_medium = site_profiles_valid[(site_profiles_valid['bust_p50'] >= bust_q33) & (site_profiles_valid['bust_p50'] < bust_q67)]
    bust_large = site_profiles_valid[site_profiles_valid['bust_p50'] >= bust_q67]

    print(f"\n  偏小胸围省份 (< {bust_q33:.1f} cm):")
    for idx, row in bust_small.iterrows():
        print(f"    {row['prov_name_translated']}: {row['bust_p50']:.1f} cm")

    print(f"\n  标准胸围省份 ({bust_q33:.1f} - {bust_q67:.1f} cm):")
    for idx, row in bust_medium.iterrows():
        print(f"    {row['prov_name_translated']}: {row['bust_p50']:.1f} cm")

    print(f"\n  偏大胸围省份 (>= {bust_q67:.1f} cm):")
    for idx, row in bust_large.iterrows():
        print(f"    {row['prov_name_translated']}: {row['bust_p50']:.1f} cm")

    # 3. 胸腰差层级
    print(f"\n3️⃣ 胸腰差层级 (基于 P50)")
    print(f"  分层阈值: {diff_q33:.1f} cm | {diff_q67:.1f} cm")

    diff_straight = site_profiles_valid[site_profiles_valid['diff_p50'] < diff_q33]
    diff_light = site_profiles_valid[(site_profiles_valid['diff_p50'] >= diff_q33) & (site_profiles_valid['diff_p50'] < diff_q67)]
    diff_curved = site_profiles_valid[site_profiles_valid['diff_p50'] >= diff_q67]

    print(f"\n  偏直筒省份 (< {diff_q33:.1f} cm):")
    for idx, row in diff_straight.iterrows():
        print(f"    {row['prov_name_translated']}: 胸腰差 {row['diff_p50']:.1f} cm")

    print(f"\n  轻曲线省份 ({diff_q33:.1f} - {diff_q67:.1f} cm):")
    for idx, row in diff_light.iterrows():
        print(f"    {row['prov_name_translated']}: 胸腰差 {row['diff_p50']:.1f} cm")

    print(f"\n  曲线更明显省份 (>= {diff_q67:.1f} cm):")
    for idx, row in diff_curved.iterrows():
        print(f"    {row['prov_name_translated']}: 胸腰差 {row['diff_p50']:.1f} cm")

# ===========================
# 第六步：臀型和腹部特征的省份差异
# ===========================
print("\n" + "=" * 120)
print("第六步：臀型和腹部特征的省份差异")
print("=" * 120)

# 过滤有效标签
df_clean_labels = df_clean.copy()
df_clean_labels = df_clean_labels[
    (~df_clean_labels['USER_HIP'].isin(['delete', 'null', ''])) &
    (df_clean_labels['USER_HIP'].notna()) &
    (~df_clean_labels['USER_BELLY'].isin(['delete', 'null', ''])) &
    (df_clean_labels['USER_BELLY'].notna())
]

for site in sorted(df_clean_labels['site_code'].unique()):
    site_df = df_clean_labels[df_clean_labels['site_code'] == site].copy()

    print(f"\n{'=' * 100}")
    print(f"站点: {site}")
    print(f"{'=' * 100}")

    # 按省份统计
    prov_hip_belly = []

    for prov_name in site_df['prov_name'].unique():
        prov_df = site_df[site_df['prov_name'] == prov_name]

        if len(prov_df) < MIN_SAMPLE_SIZE:
            continue

        prov_translated = translate_province(prov_name)

        # 最常见的臀型和腹部
        most_common_hip = prov_df['USER_HIP'].mode()[0] if len(prov_df['USER_HIP'].mode()) > 0 else 'N/A'
        most_common_belly = prov_df['USER_BELLY'].mode()[0] if len(prov_df['USER_BELLY'].mode()) > 0 else 'N/A'

        # wider hip / curvier belly 占比
        wider_hip_pct = (prov_df['USER_HIP'] == 'wider').sum() / len(prov_df) * 100
        curvier_belly_pct = (prov_df['USER_BELLY'] == 'curvier').sum() / len(prov_df) * 100

        # 平均胸腰差
        avg_diff = prov_df['bust_waist_diff'].mean()

        prov_hip_belly.append({
            'prov_name': prov_name,
            'prov_name_translated': prov_translated,
            'most_common_hip': most_common_hip,
            'most_common_belly': most_common_belly,
            'wider_hip_pct': wider_hip_pct,
            'curvier_belly_pct': curvier_belly_pct,
            'avg_diff': avg_diff,
            'user_count': len(prov_df)
        })

    df_hip_belly = pd.DataFrame(prov_hip_belly)

    if len(df_hip_belly) == 0:
        print(f"  ⚠️ 无足够样本量的省份标签数据")
        continue

    print(f"\n1️⃣ 各省份最常见的臀型和腹部特征:")
    for idx, row in df_hip_belly.iterrows():
        print(f"  {row['prov_name_translated']}: 臀型={row['most_common_hip']}, 腹部={row['most_common_belly']} (n={row['user_count']})")

    print(f"\n2️⃣ Wider Hip 占比最高的 Top 5 省份:")
    top_wider_hip = df_hip_belly.nlargest(5, 'wider_hip_pct')
    for idx, row in top_wider_hip.iterrows():
        print(f"  {row['prov_name_translated']}: {row['wider_hip_pct']:.1f}% (平均胸腰差 {row['avg_diff']:.1f} cm)")

    print(f"\n3️⃣ Curvier Belly 占比最高的 Top 5 省份:")
    top_curvier_belly = df_hip_belly.nlargest(5, 'curvier_belly_pct')
    for idx, row in top_curvier_belly.iterrows():
        print(f"  {row['prov_name_translated']}: {row['curvier_belly_pct']:.1f}% (平均胸腰差 {row['avg_diff']:.1f} cm)")

    # 相关性分析
    print(f"\n4️⃣ 结构特征与胸腰差相关性:")
    if len(df_hip_belly) > 3:
        corr_hip = df_hip_belly[['wider_hip_pct', 'avg_diff']].corr().iloc[0, 1]
        corr_belly = df_hip_belly[['curvier_belly_pct', 'avg_diff']].corr().iloc[0, 1]

        print(f"  Wider Hip 与胸腰差相关系数: {corr_hip:.3f}")
        if abs(corr_hip) > 0.3:
            print(f"    >>> {'正相关' if corr_hip > 0 else '负相关'}（wider hip 的省份胸腰差{'更高' if corr_hip > 0 else '更低'}）")
        else:
            print(f"    >>> 相关性弱")

        print(f"  Curvier Belly 与胸腰差相关系数: {corr_belly:.3f}")
        if abs(corr_belly) > 0.3:
            print(f"    >>> {'正相关' if corr_belly > 0 else '负相关'}（curvier belly 的省份胸腰差{'更高' if corr_belly > 0 else '更低'}）")
        else:
            print(f"    >>> 相关性弱")

# ===========================
# 第七步：区域画像总结
# ===========================
print("\n" + "=" * 120)
print("第七步：区域画像总结")
print("=" * 120)

for site in sorted(df_profiles['site_code'].unique()):
    site_profiles = df_profiles[df_profiles['site_code'] == site].copy()
    site_profiles_valid = site_profiles[~site_profiles['low_confidence']].copy()

    print(f"\n{'=' * 100}")
    print(f"站点: {site}")
    print(f"{'=' * 100}")

    if len(site_profiles_valid) == 0:
        print(f"  ⚠️ 无足够样本量的省份，无法生成总结")
        continue

    # 1. 省份差异是否明显
    waist_range = site_profiles_valid['waist_p50'].max() - site_profiles_valid['waist_p50'].min()
    bust_range = site_profiles_valid['bust_p50'].max() - site_profiles_valid['bust_p50'].min()
    diff_range = site_profiles_valid['diff_p50'].max() - site_profiles_valid['diff_p50'].min()

    print(f"\n1️⃣ 省份差异评估:")
    print(f"  腰围 P50 跨度: {waist_range:.1f} cm")
    print(f"  胸围 P50 跨度: {bust_range:.1f} cm")
    print(f"  胸腰差 P50 跨度: {diff_range:.1f} cm")

    if waist_range > 5 or bust_range > 6 or diff_range > 5:
        print(f"  >>> 省份差异明显")
    else:
        print(f"  >>> 省份差异不明显")

    # 2. 特征省份
    print(f"\n2️⃣ 特征省份识别:")

    # 小腰围
    small_waist = site_profiles_valid.nsmallest(3, 'waist_p50')
    print(f"  偏小腰围省份:")
    for idx, row in small_waist.iterrows():
        print(f"    {row['prov_name_translated']}: {row['waist_p50']:.1f} cm")

    # 大腰围
    large_waist = site_profiles_valid.nlargest(3, 'waist_p50')
    print(f"  偏大腰围省份:")
    for idx, row in large_waist.iterrows():
        print(f"    {row['prov_name_translated']}: {row['waist_p50']:.1f} cm")

    # 大胸围
    large_bust = site_profiles_valid.nlargest(3, 'bust_p50')
    print(f"  偏大胸围省份:")
    for idx, row in large_bust.iterrows():
        print(f"    {row['prov_name_translated']}: {row['bust_p50']:.1f} cm")

    # 高胸腰差
    high_diff = site_profiles_valid.nlargest(3, 'diff_p50')
    print(f"  高胸腰差省份（更偏曲线）:")
    for idx, row in high_diff.iterrows():
        print(f"    {row['prov_name_translated']}: {row['diff_p50']:.1f} cm")

    # 3. 主要差异维度
    print(f"\n3️⃣ 主要差异维度:")
    max_range = max(waist_range, bust_range, diff_range)
    if max_range == waist_range:
        print(f"  >>> 省份差异主要体现在【腰围】")
    elif max_range == bust_range:
        print(f"  >>> 省份差异主要体现在【胸围】")
    else:
        print(f"  >>> 省份差异主要体现在【胸腰差】")

    # 4. 一句话总结
    print(f"\n4️⃣ 省份三围格局总结:")

    # 计算整体特征
    overall_waist = site_profiles_valid['waist_p50'].median()
    overall_bust = site_profiles_valid['bust_p50'].median()
    overall_diff = site_profiles_valid['diff_p50'].median()

    # 体型分布
    straight_provs = len(site_profiles_valid[site_profiles_valid['diff_p50'] < 10])
    light_curve_provs = len(site_profiles_valid[(site_profiles_valid['diff_p50'] >= 10) & (site_profiles_valid['diff_p50'] < 18)])
    curve_provs = len(site_profiles_valid[site_profiles_valid['diff_p50'] >= 18])

    summary = f"  {site} 站点省份三围格局："
    summary += f"整体中位腰围 {overall_waist:.1f} cm、胸围 {overall_bust:.1f} cm、胸腰差 {overall_diff:.1f} cm，"

    if waist_range > 5:
        summary += f"省份间腰围差异显著（跨度 {waist_range:.1f} cm），"

    if curve_provs > straight_provs:
        summary += f"多数省份偏曲线型"
    else:
        summary += f"多数省份偏直筒型"

    print(summary)

# ===========================
# 补充：区域摘要（供后续融合身高体重数据使用）
# ===========================
print("\n" + "=" * 120)
print("补充：可供后续融合身高体重数据使用的区域摘要")
print("=" * 120)

summary_data = []

for site in sorted(df_profiles['site_code'].unique()):
    site_profiles = df_profiles[df_profiles['site_code'] == site].copy()

    print(f"\n{'=' * 100}")
    print(f"站点: {site}")
    print(f"{'=' * 100}")

    for idx, row in site_profiles.iterrows():
        # 判断是否偏直筒/偏曲线
        if row['diff_p50'] < 10:
            body_tendency = '显著偏直筒'
        elif row['diff_p50'] >= 18:
            body_tendency = '显著偏曲线'
        else:
            body_tendency = '适中'

        summary_item = {
            'site_code': row['site_code'],
            'prov_name': row['prov_name'],
            'prov_name_cn': PROVINCE_TRANSLATION.get(row['prov_name'], '待确认翻译'),
            'user_count': int(row['user_count']),
            'low_confidence': row['low_confidence'],
            'waist_p50': round(row['waist_p50'], 1),
            'bust_p50': round(row['bust_p50'], 1),
            'diff_p50': round(row['diff_p50'], 1),
            'dominant_body_type': row['dominant_body_type'],
            'body_tendency': body_tendency,
        }

        # 获取臀型/腹部特征
        prov_df = df_clean_labels[
            (df_clean_labels['site_code'] == row['site_code']) &
            (df_clean_labels['prov_name'] == row['prov_name'])
        ]

        if len(prov_df) >= MIN_SAMPLE_SIZE:
            most_common_hip = prov_df['USER_HIP'].mode()[0] if len(prov_df['USER_HIP'].mode()) > 0 else 'N/A'
            most_common_belly = prov_df['USER_BELLY'].mode()[0] if len(prov_df['USER_BELLY'].mode()) > 0 else 'N/A'
            summary_item['most_common_hip'] = most_common_hip
            summary_item['most_common_belly'] = most_common_belly
        else:
            summary_item['most_common_hip'] = 'N/A'
            summary_item['most_common_belly'] = 'N/A'

        summary_data.append(summary_item)

        confidence_tag = " [低样本]" if row['low_confidence'] else ""
        print(f"\n{row['prov_name_translated']}{confidence_tag}:")
        print(f"  - 腰围 P50: {summary_item['waist_p50']} cm")
        print(f"  - 胸围 P50: {summary_item['bust_p50']} cm")
        print(f"  - 胸腰差 P50: {summary_item['diff_p50']} cm")
        print(f"  - 主导体型: {summary_item['dominant_body_type']}")
        print(f"  - 体型倾向: {summary_item['body_tendency']}")
        print(f"  - 最主流臀型: {summary_item['most_common_hip']}")
        print(f"  - 最主流腹部: {summary_item['most_common_belly']}")
        print(f"  - 有效用户数: {summary_item['user_count']}")

# 保存区域摘要
summary_df = pd.DataFrame(summary_data)
summary_output_file = '/Users/yixiqian/daily-work-summary/province_body_measurements_summary.json'
summary_df.to_json(summary_output_file, orient='records', force_ascii=False, indent=2)

print(f"\n{'=' * 120}")
print(f"✓ 区域摘要已保存到: {summary_output_file}")
print(f"{'=' * 120}")

print("\n" + "=" * 120)
print("分析完成！")
print("=" * 120)
