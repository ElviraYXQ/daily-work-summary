# 省份级三围画像分析报告

**分析时间**: 2026-04-22
**数据来源**: 区域尺码用户数-三围-2026-04-22 17-50-37.xlsx

---

## 📊 执行摘要

本报告基于 52,809 条原始用户三围数据，经严格数据清洗后保留 30,627 条有效记录，针对 IN（印度）和 IQ（伊拉克）两个站点进行省份级三围画像分析，识别各站点内部的区域差异特征。

### 核心发现

**IN 站点**
- ✅ 省份差异明显（腰围跨度 5.1 cm，胸腰差跨度 7.6 cm）
- 主要差异维度：**胸腰差**
- 东北部省份（Mizoram、Manipur、Meghalaya）显著偏曲线型
- 整体格局：腰围 73.7 cm、胸围 86.4 cm、胸腰差 12.7 cm

**IQ 站点**
- ✅ 省份差异不显著（腰围跨度 3.0 cm，胸腰差跨度 2.0 cm）
- 体型相对均质化，轻曲线型占主导
- 整体格局：腰围 78-80 cm、胸围 93-95 cm、胸腰差 14-15 cm

---

## 1️⃣ 数据质量报告

### 清洗结果

<lark-table column-widths="200,150,150,150" header-row="true">
<lark-tr>
<lark-td>

**指标**

</lark-td>
<lark-td>

**数值**

</lark-td>
<lark-td>

**IN 站点**

</lark-td>
<lark-td>

**IQ 站点**

</lark-td>
</lark-tr>
<lark-tr>
<lark-td>

原始记录数

</lark-td>
<lark-td>

52,809

</lark-td>
<lark-td>

22,675

</lark-td>
<lark-td>

30,134

</lark-td>
</lark-tr>
<lark-tr>
<lark-td>

清洗后记录数

</lark-td>
<lark-td>

30,627

</lark-td>
<lark-td>

15,084

</lark-td>
<lark-td>

15,543

</lark-td>
</lark-tr>
<lark-tr>
<lark-td>

剔除占比

</lark-td>
<lark-td>

42.00%

</lark-td>
<lark-td>

33.5%

</lark-td>
<lark-td>

48.4%

</lark-td>
</lark-tr>
<lark-tr>
<lark-td>

有效省份数
(样本≥30)

</lark-td>
<lark-td>

51

</lark-td>
<lark-td>

32

</lark-td>
<lark-td>

19

</lark-td>
</lark-tr>
</lark-table>

### 清洗规则

<callout emoji="⚙️" background-color="light-blue">

**严格异常值识别标准**

1. 腰围 < 50 cm 或 > 120 cm
2. 上胸围 < 65 cm 或 > 140 cm
3. 上胸围 ≤ 腰围（逻辑异常）
4. 胸腰差 < 3 cm 或 > 40 cm（高风险异常）
5. 单位统一：英寸转换为厘米（1 inch = 2.54 cm）

</callout>

### 脏数据集中省份

<callout emoji="⚠️" background-color="light-yellow">

**IN 站点高异常率省份 (> 50%)**
- Pondicherry: 53.8% 异常
- Ladakh: 50.3% 异常

**IQ 站点高异常率省份 (> 50%)**
- المثنى（穆萨纳）: 58.6%
- واسط（瓦西特）: 57.4%
- ذي قار（济加尔）: 57.1%
- صلاح الدين（萨拉赫丁）: 55.9%
- الأنبار（安巴尔）: 55.6%

</callout>

---

## 2️⃣ IN 站点省份画像

### 区域差异评估

| 维度 | 跨度 | 评估 |
|------|------|------|
| 腰围 P50 | 5.1 cm | ⚠️ 差异显著 |
| 胸围 P50 | 7.2 cm | ⚠️ 差异显著 |
| 胸腰差 P50 | 7.6 cm | ⚠️ 差异显著 |

**主要差异维度**: **胸腰差**（东北部省份显著偏曲线型）

### TOP 5 省份特征

#### 腰围最大省份

| 省份 | 腰围 P50 | 样本量 |
|------|----------|--------|
| Gujarat（古吉拉特邦） | 76.2 cm | 150 |
| Jammu & Kashmir（查谟-克什米尔） | 76.2 cm | 255 |
| Odisha（奥迪沙邦） | 76.2 cm | 238 |
| Goa（果阿邦） | 76.0 cm | 32 |
| Andhra Pradesh（安得拉邦） | 73.7 cm | 163 |

#### 腰围最小省份

| 省份 | 腰围 P50 | 样本量 |
|------|----------|--------|
| Arunachal Pradesh（阿鲁纳恰尔邦） | 71.1 cm | 1,372 |
| Assam（阿萨姆邦） | 71.1 cm | 817 |
| Bihar（比哈尔邦） | 71.1 cm | 175 |
| Jharkhand（贾坎德邦） | 71.1 cm | 233 |
| Kerala（喀拉拉邦） | 71.1 cm | 373 |

#### 胸腰差最大省份（偏曲线型）

| 省份 | 胸腰差 P50 | 体型倾向 | 样本量 |
|------|------------|----------|--------|
| **Mizoram（米佐拉姆邦）** | **17.8 cm** | 显著偏曲线 | 77 |
| **Manipur（曼尼普尔邦）** | **15.2 cm** | 适中 | 103 |
| **Meghalaya（梅加拉亚邦）** | **15.2 cm** | 适中 | 248 |
| Goa（果阿邦） | 15.2 cm | 适中 | 32 |
| Nagaland（那加兰邦） | 15.2 cm | 适中 | 658 |

#### 胸腰差最小省份（偏直筒型）

| 省份 | 胸腰差 P50 | 体型倾向 | 样本量 |
|------|------------|----------|--------|
| Delhi（德里） | 8.9 cm | 显著偏直筒 | 2 [低样本] |
| Pondicherry | 8.9 cm | 显著偏直筒 | 6 [低样本] |
| Chhattisgarh（恰蒂斯加尔邦） | 10.2 cm | 适中 | 219 |
| Gujarat（古吉拉特邦） | 10.2 cm | 适中 | 150 |
| Karnataka（卡纳塔克邦） | 10.2 cm | 适中 | 325 |

### 省份体型分层

#### 腰围层级

**偏小腰围省份（< 71.8 cm）**
- Arunachal Pradesh（阿鲁纳恰尔邦）: 71.1 cm
- Assam（阿萨姆邦）: 71.1 cm
- Bihar（比哈尔邦）: 71.1 cm
- Jharkhand（贾坎德邦）: 71.1 cm
- Kerala（喀拉拉邦）: 71.1 cm
- Manipur（曼尼普尔邦）: 71.1 cm
- Meghalaya（梅加拉亚邦）: 71.1 cm
- Mizoram（米佐拉姆邦）: 71.1 cm
- Nagaland（那加兰邦）: 71.1 cm
- Orissa: 71.1 cm
- Tamil Nadu（泰米尔纳德邦）: 71.6 cm

**偏大腰围省份（≥ 73.7 cm）**
- Gujarat（古吉拉特邦）: 76.2 cm
- Jammu & Kashmir（查谟-克什米尔）: 76.2 cm
- Odisha（奥迪沙邦）: 76.2 cm
- Goa（果阿邦）: 76.0 cm
- Pondicherry: 76.2 cm
- Ladakh: 73.7 cm
- 以及其他 15 个省份

#### 胸腰差层级

**偏直筒省份（< 12.5 cm）**
- Chhattisgarh（恰蒂斯加尔邦）
- Gujarat（古吉拉特邦）
- Karnataka（卡纳塔克邦）
- Madhya Pradesh（中央邦）
- Odisha（奥迪沙邦）
- Rajasthan（拉贾斯坦邦）
- Pondicherry
- Delhi

**曲线更明显省份（≥ 13.3 cm）**
- **Mizoram（米佐拉姆邦）: 17.8 cm** ⭐
- Manipur（曼尼普尔邦）: 15.2 cm
- Meghalaya（梅加拉亚邦）: 15.2 cm
- Nagaland（那加兰邦）: 15.2 cm
- Goa（果阿邦）: 15.2 cm
- Arunachal Pradesh（阿鲁纳恰尔邦）
- Ladakh
- Andhra Pradesh（安得拉邦）

### 区域画像总结

<callout emoji="🎯" background-color="light-green">

**IN 站点省份三围格局**

整体中位数：腰围 73.7 cm、胸围 86.4 cm、胸腰差 12.7 cm

**关键发现**：
1. ✅ 省份差异明显（腰围跨度 5.1 cm），主要体现在胸腰差维度
2. 🌏 **东北部省份**（Mizoram、Manipur、Meghalaya、Nagaland）显著偏曲线型（胸腰差 15-18 cm）
3. 🌏 **中部和西部省份**（Gujarat、Rajasthan、Madhya Pradesh）偏直筒型（胸腰差 10-12 cm）
4. 多数省份体型倾向：轻曲线型（55-70%）

**建议**：东北部省份用户与主流用户体型存在显著差异，建议后续融合身高体重数据时重点关注。

</callout>

---

## 3️⃣ IQ 站点省份画像

### 区域差异评估

| 维度 | 跨度 | 评估 |
|------|------|------|
| 腰围 P50 | 3.0 cm | ✅ 差异不显著 |
| 胸围 P50 | 4.0 cm | ✅ 差异不显著 |
| 胸腰差 P50 | 2.0 cm | ✅ 差异不显著 |

**主要特征**: 省份间体型相对均质化

### TOP 5 省份特征

#### 腰围最大省份

| 省份 | 腰围 P50 | 样本量 |
|------|----------|--------|
| واسط（瓦西特） | 80.0 cm | 308 |
| كربلاء（卡尔巴拉） | 80.0 cm | 762 |
| المثنى（穆萨纳） | 80.0 cm | 193 |
| ديالى（迪亚拉） | 80.0 cm | 496 |
| بغداد（巴格达） | 79.0 cm | 6,063 |

#### 腰围最小省份

| 省份 | 腰围 P50 | 样本量 |
|------|----------|--------|
| صلاح الدين（萨拉赫丁） | 77.0 cm | 356 |
| أربيل（埃尔比勒） | 78.0 cm | 781 |
| الأنبار（安巴尔） | 78.0 cm | 431 |
| البصرة（巴士拉） | 78.0 cm | 1,494 |
| النجف（纳杰夫） | 78.0 cm | 756 |

#### 胸腰差最大省份

| 省份 | 胸腰差 P50 | 样本量 |
|------|------------|--------|
| ميسان（米桑） | 15.0 cm | 258 |
| أربيل（埃尔比勒） | 15.0 cm | 781 |
| السليمانية（苏莱曼尼亚） | 15.0 cm | 528 |
| كركوك（基尔库克） | 15.0 cm | 484 |
| البصرة（巴士拉） | 15.0 cm | 1,494 |

#### 胸腰差最小省份

| 省份 | 胸腰差 P50 | 样本量 |
|------|------------|--------|
| المثنى（穆萨纳） | 13.0 cm | 193 |
| صلاح الدين（萨拉赫丁） | 13.5 cm | 356 |
| الأنبار（安巴尔） | 14.0 cm | 431 |
| دهوك（杜胡克） | 14.0 cm | 299 |
| ذي قار（济加尔） | 14.0 cm | 548 |

### 省份体型分层

#### 腰围层级

**偏小腰围省份（< 78.0 cm）**
- صلاح الدين（萨拉赫丁）: 77.0 cm

**偏大腰围省份（≥ 79.5 cm）**
- واسط（瓦西特）: 80.0 cm
- كربلاء（卡尔巴拉）: 80.0 cm
- المثنى（穆萨纳）: 80.0 cm
- ديالى（迪亚拉）: 80.0 cm
- حي القادسية: 78.0 cm
- بابل（巴比伦）: 78.0 cm

#### 胸腰差层级

所有省份均集中在 **13-15 cm**，体型差异极小，均为**轻曲线型**

### 区域画像总结

<callout emoji="🎯" background-color="light-green">

**IQ 站点省份三围格局**

整体中位数：腰围 78-80 cm、胸围 93-95 cm、胸腰差 14-15 cm

**关键发现**：
1. ✅ 省份差异不显著（腰围跨度仅 3.0 cm）
2. 体型高度均质化，所有省份均为轻曲线型主导
3. 巴格达（بغداد）作为最大样本省份（n=6,063），具有代表性：腰围 79.0 cm、胸围 94.0 cm、胸腰差 15.0 cm
4. 瓦西特（واسط）、卡尔巴拉（كربلاء）等省份腰围略大（80 cm），但差异不显著

**建议**：IQ 站点可使用统一的省份体型画像，无需针对特定省份做差异化处理。

</callout>

---

## 4️⃣ 臀型和腹部特征分析

### IN 站点

**主流体型特征组合**
- **Average 臀型 + Average 腹部**: 26.49%（主流）
- Average 臀型 + Flatter 腹部: 10.79%
- Average 臀型 + Curvier 腹部: 7.57%

**Wider Hip 高占比省份（TOP 5）**
1. Manipur（曼尼普尔邦）: 27.2%（胸腰差 15.4 cm）
2. Meghalaya（梅加拉亚邦）: 23.4%（胸腰差 14.7 cm）
3. Arunachal Pradesh（阿鲁纳恰尔邦）: 20.1%（胸腰差 13.7 cm）

**相关性**: Wider Hip 的省份胸腰差相关系数 +0.42（正相关），说明下半身重型用户通常胸腰差也更高

### IQ 站点

**主流体型特征组合**
- **Average 臀型 + Average 腹部**: 26.32%（主流）
- Average 臀型 + Flatter 腹部: 15.97%
- **Wider 臀型 + Curvier 腹部**: 15.22%（显著特征）

**Wider Hip 高占比省份（TOP 5）**
1. أربيل（埃尔比勒）: 35.3%（胸腰差 15.9 cm）
2. السليمانية（苏莱曼尼亚）: 33.1%（胸腰差 15.7 cm）
3. كركوك（基尔库克）: 31.8%（胸腰差 15.8 cm）

**相关性**: Wider Hip 的省份胸腰差相关系数 +0.51（强正相关），下半身重型用户显著集中在北部库尔德地区

---

## 5️⃣ 区域摘要（供后续融合身高体重数据使用）

### IN 站点关键省份摘要

<lark-table column-widths="180,120,120,120,120,150" header-row="true">
<lark-tr>
<lark-td>

**省份**

</lark-td>
<lark-td>

**腰围P50**

</lark-td>
<lark-td>

**胸围P50**

</lark-td>
<lark-td>

**胸腰差P50**

</lark-td>
<lark-td>

**主导体型**

</lark-td>
<lark-td>

**体型倾向**

</lark-td>
</lark-tr>
<lark-tr>
<lark-td>

Maharashtra
（马哈拉施特拉邦）

</lark-td>
<lark-td>

73.7 cm

</lark-td>
<lark-td>

86.4 cm

</lark-td>
<lark-td>

12.7 cm

</lark-td>
<lark-td>

轻曲线型

</lark-td>
<lark-td>

适中

</lark-td>
</lark-tr>
<lark-tr>
<lark-td>

Arunachal Pradesh
（阿鲁纳恰尔邦）

</lark-td>
<lark-td>

71.1 cm

</lark-td>
<lark-td>

86.4 cm

</lark-td>
<lark-td>

12.7 cm

</lark-td>
<lark-td>

轻曲线型

</lark-td>
<lark-td>

适中

</lark-td>
</lark-tr>
<lark-tr>
<lark-td>

Sikkim
（锡金邦）

</lark-td>
<lark-td>

73.7 cm

</lark-td>
<lark-td>

86.4 cm

</lark-td>
<lark-td>

12.7 cm

</lark-td>
<lark-td>

轻曲线型

</lark-td>
<lark-td>

适中

</lark-td>
</lark-tr>
<lark-tr>
<lark-td>

Uttar Pradesh
（北方邦）

</lark-td>
<lark-td>

73.7 cm

</lark-td>
<lark-td>

86.4 cm

</lark-td>
<lark-td>

12.7 cm

</lark-td>
<lark-td>

轻曲线型

</lark-td>
<lark-td>

适中

</lark-td>
</lark-tr>
<lark-tr>
<lark-td>

**Mizoram
（米佐拉姆邦）**

</lark-td>
<lark-td>

**71.1 cm**

</lark-td>
<lark-td>

**91.0 cm**

</lark-td>
<lark-td>

**17.8 cm**

</lark-td>
<lark-td>

**轻曲线型**

</lark-td>
<lark-td>

**显著偏曲线**

</lark-td>
</lark-tr>
<lark-tr>
<lark-td>

**Manipur
（曼尼普尔邦）**

</lark-td>
<lark-td>

**71.1 cm**

</lark-td>
<lark-td>

**88.9 cm**

</lark-td>
<lark-td>

**15.2 cm**

</lark-td>
<lark-td>

**轻曲线型**

</lark-td>
<lark-td>

**适中**

</lark-td>
</lark-tr>
<lark-tr>
<lark-td>

Gujarat
（古吉拉特邦）

</lark-td>
<lark-td>

76.2 cm

</lark-td>
<lark-td>

86.4 cm

</lark-td>
<lark-td>

10.2 cm

</lark-td>
<lark-td>

轻曲线型

</lark-td>
<lark-td>

适中

</lark-td>
</lark-tr>
<lark-tr>
<lark-td>

Rajasthan
（拉贾斯坦邦）

</lark-td>
<lark-td>

73.7 cm

</lark-td>
<lark-td>

86.4 cm

</lark-td>
<lark-td>

11.4 cm

</lark-td>
<lark-td>

轻曲线型

</lark-td>
<lark-td>

适中

</lark-td>
</lark-tr>
</lark-table>

### IQ 站点关键省份摘要

<lark-table column-widths="180,120,120,120,120,150" header-row="true">
<lark-tr>
<lark-td>

**省份**

</lark-td>
<lark-td>

**腰围P50**

</lark-td>
<lark-td>

**胸围P50**

</lark-td>
<lark-td>

**胸腰差P50**

</lark-td>
<lark-td>

**主导体型**

</lark-td>
<lark-td>

**体型倾向**

</lark-td>
</lark-tr>
<lark-tr>
<lark-td>

**بغداد
（巴格达）**

</lark-td>
<lark-td>

**79.0 cm**

</lark-td>
<lark-td>

**94.0 cm**

</lark-td>
<lark-td>

**15.0 cm**

</lark-td>
<lark-td>

**轻曲线型**

</lark-td>
<lark-td>

**适中**

</lark-td>
</lark-tr>
<lark-tr>
<lark-td>

البصرة
（巴士拉）

</lark-td>
<lark-td>

78.0 cm

</lark-td>
<lark-td>

93.0 cm

</lark-td>
<lark-td>

15.0 cm

</lark-td>
<lark-td>

轻曲线型

</lark-td>
<lark-td>

适中

</lark-td>
</lark-tr>
<lark-tr>
<lark-td>

أربيل
（埃尔比勒）

</lark-td>
<lark-td>

78.0 cm

</lark-td>
<lark-td>

94.0 cm

</lark-td>
<lark-td>

15.0 cm

</lark-td>
<lark-td>

轻曲线型

</lark-td>
<lark-td>

适中

</lark-td>
</lark-tr>
<lark-tr>
<lark-td>

النجف
（纳杰夫）

</lark-td>
<lark-td>

78.0 cm

</lark-td>
<lark-td>

93.0 cm

</lark-td>
<lark-td>

15.0 cm

</lark-td>
<lark-td>

轻曲线型

</lark-td>
<lark-td>

适中

</lark-td>
</lark-tr>
<lark-tr>
<lark-td>

كربلاء
（卡尔巴拉）

</lark-td>
<lark-td>

80.0 cm

</lark-td>
<lark-td>

94.0 cm

</lark-td>
<lark-td>

14.0 cm

</lark-td>
<lark-td>

轻曲线型

</lark-td>
<lark-td>

适中

</lark-td>
</lark-tr>
<lark-tr>
<lark-td>

واسط
（瓦西特）

</lark-td>
<lark-td>

80.0 cm

</lark-td>
<lark-td>

95.0 cm

</lark-td>
<lark-td>

14.0 cm

</lark-td>
<lark-td>

轻曲线型

</lark-td>
<lark-td>

适中

</lark-td>
</lark-tr>
</lark-table>

---

## 6️⃣ 总结与建议

### IN 站点

<callout emoji="🎯" background-color="light-blue">

**核心结论**

1. **省份差异明显**：腰围跨度 5.1 cm，胸腰差跨度 7.6 cm，主要体现在胸腰差维度
2. **东北部省份特殊性**：Mizoram、Manipur、Meghalaya 等东北部省份显著偏曲线型（胸腰差 15-18 cm），与主流用户差异明显
3. **中西部省份同质化**：Gujarat、Rajasthan、Madhya Pradesh 等中西部省份体型相对一致，偏直筒型（胸腰差 10-12 cm）
4. **主流体型特征**：Average 臀型 + Average 腹部（26.5%）

**后续建议**

- 融合身高体重数据时，重点关注东北部省份与主流的差异
- 建议按"东北部 vs 其他地区"进行分层画像
- 样本量不足省份（如 Delhi、Pondicherry）谨慎解读

</callout>

### IQ 站点

<callout emoji="🎯" background-color="light-blue">

**核心结论**

1. **省份差异不显著**：腰围跨度仅 3.0 cm，胸腰差跨度 2.0 cm
2. **体型高度均质化**：所有省份均为轻曲线型主导，无明显区域分化
3. **巴格达代表性**：作为最大样本省份（n=6,063），巴格达的画像（腰围 79 cm、胸围 94 cm、胸腰差 15 cm）可作为全站代表
4. **库尔德地区特征**：北部埃尔比勒、苏莱曼尼亚等地 Wider Hip 占比较高（30-35%），但胸腰差仍与主流一致

**后续建议**

- 可使用统一的省份体型画像，无需针对特定省份做差异化处理
- 融合身高体重数据时，无需特别区分省份，可按全站统一分析

</callout>

---

**报告完成时间**: 2026-04-22
**分析师**: Claude Code（数据科学专家）
**数据文件**: province_body_measurements_summary.json
