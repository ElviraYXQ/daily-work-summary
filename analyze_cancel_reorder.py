#!/usr/bin/env python3
"""
取消再下单数据分析脚本
目标：分析IQ和IN站点用户的取消原因
"""
import pandas as pd
import json
from datetime import datetime

def analyze_cancel_reasons(file_path):
    """分析取消原因的主函数"""
    df = pd.read_excel(file_path)

    # 基础统计
    print("=" * 80)
    print("📊 数据集基础信息")
    print("=" * 80)
    print(f"时间范围: {df['下单日期'].min().date()} 至 {df['下单日期'].max().date()}")
    print(f"站点: {', '.join(df['site_code'].unique())}")
    print(f"数据行数: {len(df)} (每个站点 {len(df[df['site_code']=='IQ'])} 条记录)")
    print()

    # 按站点汇总
    analysis_results = {}

    for site in ['IQ', 'IN']:
        site_data = df[df['site_code'] == site]

        # 汇总数据
        total_cancel = site_data['取消件数'].sum()
        total_reorder = site_data['再下单件数'].sum()
        total_cancel_uv = site_data['取消uv'].sum()
        total_reorder_uv = site_data['再下单uv'].sum()

        # 计算各类取消原因的占比
        # 1. 包邮门槛相关
        reorder_for_shipping = site_data['再下单件数(再下单包邮之前不包邮)'].sum()
        partial_cancel_for_shipping = site_data['部分取消后满足包邮的件数'].sum()

        # 2. 缺货问题（仅IQ）
        cancel_for_stockout = site_data['凑包邮取消件数(IQ缺货)'].sum()

        # 3. 价格/优惠相关
        reorder_lower_discount = site_data['再下单件数(低折扣价相同商品)'].sum()
        reorder_lower_price = site_data['再下单件数(低成交价相同商品)'].sum()
        reorder_more_coupon = site_data['再下单件数(使用更多优惠券)'].sum()

        # 4. 整单取消
        whole_order_cancel = site_data['整单取消件数'].sum()

        # 5. 再购买超过取消（可能是误操作或改变主意）
        reorder_exceed_cancel = site_data['再下单件数(再购买超过取消)'].sum()

        print("=" * 80)
        print(f"🏪 {site} 站点分析")
        print("=" * 80)
        print(f"\n【整体指标】")
        print(f"  • 总取消件数: {total_cancel:,}")
        print(f"  • 总再下单件数: {total_reorder:,}")
        print(f"  • 再下单率: {total_reorder/total_cancel*100:.2f}%")
        print(f"  • 取消UV: {total_cancel_uv:,}")
        print(f"  • 再下单UV: {total_reorder_uv:,}")
        print(f"  • UV再下单率: {total_reorder_uv/total_cancel_uv*100:.2f}%")

        print(f"\n【可推断的取消原因及占比】")
        print(f"基数：总取消件数 = {total_cancel:,}\n")

        # 包邮门槛
        shipping_related = partial_cancel_for_shipping + cancel_for_stockout
        print(f"1️⃣  包邮门槛相关:")
        print(f"    • 部分取消后满足包邮: {partial_cancel_for_shipping:,} ({partial_cancel_for_shipping/total_cancel*100:.2f}%)")
        if site == 'IQ':
            print(f"    • 凑包邮时缺货取消(IQ): {cancel_for_stockout:,} ({cancel_for_stockout/total_cancel*100:.2f}%)")
        print(f"    → 小计: {shipping_related:,} ({shipping_related/total_cancel*100:.2f}%)")

        # 价格优惠
        price_related = reorder_lower_discount + reorder_lower_price + reorder_more_coupon
        print(f"\n2️⃣  价格/优惠相关 (通过再下单行为推断):")
        print(f"    • 再下单用了更低折扣: {reorder_lower_discount:,} ({reorder_lower_discount/total_cancel*100:.2f}%)")
        print(f"    • 再下单成交价更低: {reorder_lower_price:,} ({reorder_lower_price/total_cancel*100:.2f}%)")
        print(f"    • 再下单使用更多优惠券: {reorder_more_coupon:,} ({reorder_more_coupon/total_cancel*100:.2f}%)")
        print(f"    → 小计: {price_related:,} ({price_related/total_cancel*100:.2f}%)")

        # 整单取消
        print(f"\n3️⃣  整单取消:")
        print(f"    • 整单取消件数: {whole_order_cancel:,} ({whole_order_cancel/total_cancel*100:.2f}%)")

        # 可量化的原因总和
        identifiable_reasons = shipping_related + price_related
        print(f"\n📍 可明确量化的取消原因占比: {identifiable_reasons:,} ({identifiable_reasons/total_cancel*100:.2f}%)")
        print(f"❓ 无法从数据推断原因的占比: {total_cancel - identifiable_reasons:,} ({(total_cancel - identifiable_reasons)/total_cancel*100:.2f}%)")

        print(f"\n【再下单行为特征】")
        reorder_same_product = site_data['再下单件数(相同商品)'].sum()
        print(f"  • 再下单相同商品: {reorder_same_product:,} ({reorder_same_product/total_reorder*100:.2f}% 的再下单)")
        print(f"  • 再下单不同商品: {total_reorder - reorder_same_product:,} ({(total_reorder - reorder_same_product)/total_reorder*100:.2f}%)")

        print()

        # 保存结果
        analysis_results[site] = {
            "站点": site,
            "总取消件数": int(total_cancel),
            "总再下单件数": int(total_reorder),
            "取消再下单率": round(total_reorder/total_cancel*100, 2),
            "可推断原因": {
                "包邮门槛相关": {
                    "件数": int(shipping_related),
                    "占比": round(shipping_related/total_cancel*100, 2)
                },
                "价格优惠相关": {
                    "件数": int(price_related),
                    "占比": round(price_related/total_cancel*100, 2)
                },
                "可量化原因合计": {
                    "件数": int(identifiable_reasons),
                    "占比": round(identifiable_reasons/total_cancel*100, 2)
                }
            },
            "无法推断原因": {
                "件数": int(total_cancel - identifiable_reasons),
                "占比": round((total_cancel - identifiable_reasons)/total_cancel*100, 2)
            }
        }

    # 对比两个站点
    print("=" * 80)
    print("🔄 IQ vs IN 对比分析")
    print("=" * 80)

    iq_results = analysis_results['IQ']
    in_results = analysis_results['IN']

    print(f"\n【取消规模】")
    print(f"  • IQ总取消: {iq_results['总取消件数']:,}")
    print(f"  • IN总取消: {in_results['总取消件数']:,}")
    print(f"  • IN是IQ的: {in_results['总取消件数']/iq_results['总取消件数']:.2f}x")

    print(f"\n【再下单率】")
    print(f"  • IQ: {iq_results['取消再下单率']:.2f}%")
    print(f"  • IN: {in_results['取消再下单率']:.2f}%")
    print(f"  • 差异: IQ比IN高 {iq_results['取消再下单率'] - in_results['取消再下单率']:.2f} 个百分点")

    print(f"\n【包邮门槛问题】")
    print(f"  • IQ: {iq_results['可推断原因']['包邮门槛相关']['占比']:.2f}%")
    print(f"  • IN: {in_results['可推断原因']['包邮门槛相关']['占比']:.2f}%")

    print(f"\n【价格优惠敏感度】")
    print(f"  • IQ: {iq_results['可推断原因']['价格优惠相关']['占比']:.2f}%")
    print(f"  • IN: {in_results['可推断原因']['价格优惠相关']['占比']:.2f}%")

    print()

    # 保存JSON结果
    output = {
        "分析时间": datetime.now().isoformat(),
        "数据时间范围": {
            "开始": df['下单日期'].min().strftime('%Y-%m-%d'),
            "结束": df['下单日期'].max().strftime('%Y-%m-%d')
        },
        "站点分析": analysis_results
    }

    with open('cancel_reorder_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"✅ 分析结果已保存到: cancel_reorder_analysis.json\n")

    return analysis_results

def generate_limitations_report():
    """生成数据局限性报告"""
    print("=" * 80)
    print("⚠️  数据局限性与建议补充数据")
    print("=" * 80)

    limitations = {
        "当前数据可以分析的": [
            "✅ 包邮门槛导致的取消（部分取消后满足包邮、凑包邮缺货）",
            "✅ 价格/优惠敏感导致的再下单（通过再下单行为反推）",
            "✅ 取消后再下单的转化率",
            "✅ IQ vs IN 的取消行为差异"
        ],
        "当前数据无法分析的": [
            "❌ 用户主动选择的取消原因（无用户填写的取消理由字段）",
            "❌ 未再下单用户的取消原因（数据只关注再下单行为）",
            "❌ 商品类目/品类对取消的影响",
            "❌ 具体的缺货SKU信息",
            "❌ 配送问题导致的取消",
            "❌ 尺码不合适导致的取消",
            "❌ 用户改变购买意愿的原因",
            "❌ 支付问题导致的取消"
        ],
        "建议补充的数据": [
            "1. 用户取消时的主动选择理由（下拉选项+自由填写）",
            "2. 取消订单的商品详细信息（SPU/SKU、类目、价格档位）",
            "3. 缺货取消的具体SKU和库存状态",
            "4. 用户画像信息（新老客、历史订单数、会员等级）",
            "5. 订单时间维度（下单时间、支付时间、取消时间）",
            "6. 配送方式和预计送达时间",
            "7. 用户浏览取消前后的行为日志",
            "8. 客服联系记录（如有）"
        ]
    }

    print("\n【✅ 当前数据可以回答的问题】")
    for item in limitations["当前数据可以分析的"]:
        print(f"  {item}")

    print("\n【❌ 当前数据无法回答的问题】")
    for item in limitations["当前数据无法分析的"]:
        print(f"  {item}")

    print("\n【💡 建议补充的数据维度】")
    for item in limitations["建议补充的数据"]:
        print(f"  {item}")

    print()

    return limitations

def main():
    file_path = '/Users/yixiqian/Downloads/取消再下单数据.xlsx'

    print("\n" + "🔍 " * 20)
    print("取消再下单数据分析报告")
    print("🔍 " * 20 + "\n")

    # 主分析
    results = analyze_cancel_reasons(file_path)

    # 局限性报告
    limitations = generate_limitations_report()

    print("=" * 80)
    print("📋 分析结论")
    print("=" * 80)
    print("""
【是否可以得出取消原因？】
✅ 可以部分推断，但有明显局限性

【可信度评估】
• 包邮门槛相关原因：⭐⭐⭐⭐⭐ (高可信度，数据直接反映)
• 价格优惠相关原因：⭐⭐⭐⭐ (较高可信度，通过再下单行为反推)
• 其他取消原因：⚠️  无法从当前数据推断

【核心发现】
1. IQ和IN都有超过85%的取消无法从现有数据推断原因
2. IQ的包邮门槛问题比IN更突出（约10%的取消与包邮相关）
3. 价格优惠敏感度两站点都不高（<4%）
4. IQ的取消再下单率(44%)明显高于IN(32%)

【推荐行动】
1. 紧急补充用户主动填写的取消原因字段（下拉+自由文本）
2. 分析未再下单用户的取消原因（当前数据盲区）
3. 结合商品类目、价格档位、用户画像进行深度分析
    """)

if __name__ == "__main__":
    main()
