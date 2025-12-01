"""
Phase D拡張版: 媒介分析 - 会食行動を通じた恐怖指数の影響

作成日: 2025年12月1日

目的:
Phase Dで確認した「恐怖指数とインフルエンザ患者数の負の相関（r=-0.239, R²=0.057）」について、
その因果メカニズムを検証します。

仮説:
恐怖レベル低下 → 会食増加 → 接触機会増加 → インフルエンザ増加
恐怖レベル上昇 → 会食減少 → 接触機会減少 → インフルエンザ減少
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import statsmodels.api as sm
import warnings
warnings.filterwarnings('ignore')

# Google Trends API
from pytrends.request import TrendReq
import time
import os

# 日本語フォント設定
plt.rcParams['font.sans-serif'] = ['MS Gothic', 'Yu Gothic', 'Hiragino Sans']
plt.rcParams['axes.unicode_minus'] = False

# 表示設定
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', 100)

print("="*60)
print("Phase D拡張版: 媒介分析")
print("="*60)

# ディレクトリの変更
os.chdir('C:\\Users\\imao3\\Documents\\GitHub\\hokkaido-influenza-prediction')

# ====================
# 1. 既存データの読み込み
# ====================
print("\n[1] 既存データの読み込み")
print("-"*60)

df_fear = pd.read_csv('outputs/tables/fear_index_analysis_data.csv')

print(f"データ期間: {df_fear['year'].min()}年～{df_fear['year'].max()}年")
print(f"データ数: {len(df_fear)}週")
print("\n列名:")
print(df_fear.columns.tolist())

# 恐怖指数として fear_index_weighted を使用
df_fear['fear_index'] = df_fear['fear_index_weighted']

print("\n基本統計量:")
print(df_fear[['fear_index', 'cases_per_sentinel']].describe())

# ====================
# 2. 会食関連データの取得（Google Trends）
# ====================
print("\n[2] 会食関連データの取得（Google Trends）")
print("-"*60)

# Google Trends API初期化
pytrends = TrendReq(hl='ja-JP', tz=540)

# 会食関連キーワード
dining_keywords = [
    '居酒屋',
    '飲み会',
    '忘年会',
    '新年会',
    '歓送迎会'
]

# 北海道のデータを取得
geo = 'JP-01'  # 北海道
timeframe = '2020-01-01 2024-11-30'

print(f"キーワード: {dining_keywords}")
print(f"地域: 北海道")
print(f"期間: {timeframe}")
print("\nGoogle Trendsからデータを取得中...")

try:
    pytrends.build_payload(
        kw_list=dining_keywords,
        geo=geo,
        timeframe=timeframe
    )

    df_dining_trends = pytrends.interest_over_time()

    if not df_dining_trends.empty:
        # 'isPartial'列を削除
        if 'isPartial' in df_dining_trends.columns:
            df_dining_trends = df_dining_trends.drop('isPartial', axis=1)

        print("\nデータ取得成功！")
        print(f"期間: {df_dining_trends.index.min()} ～ {df_dining_trends.index.max()}")
        print(f"データ数: {len(df_dining_trends)}日")
        print("\n最初の5行:")
        print(df_dining_trends.head())

        # 週次集計
        df_dining_trends['year'] = df_dining_trends.index.isocalendar().year
        df_dining_trends['week'] = df_dining_trends.index.isocalendar().week

        df_dining_weekly = df_dining_trends.groupby(['year', 'week']).mean().reset_index()

        print(f"\n週次集計完了: {len(df_dining_weekly)}週")

    else:
        print("\n警告: データが取得できませんでした")
        df_dining_weekly = None

except Exception as e:
    print(f"\nエラー: {e}")
    print("Google Trendsからのデータ取得に失敗しました。")
    df_dining_weekly = None

# ====================
# 3. 会食指数の構築
# ====================
print("\n[3] 会食指数の構築")
print("-"*60)

if df_dining_weekly is not None:
    # 重み設定
    weights = {
        '居酒屋': 3.0,      # 最も直接的
        '飲み会': 2.5,
        '忘年会': 1.5,      # 季節的
        '新年会': 1.5,      # 季節的
        '歓送迎会': 1.0     # 季節的
    }

    # 加重平均で会食指数を計算
    dining_index_components = []
    total_weight = 0

    for keyword in dining_keywords:
        if keyword in df_dining_weekly.columns:
            dining_index_components.append(
                df_dining_weekly[keyword] * weights[keyword]
            )
            total_weight += weights[keyword]

    if len(dining_index_components) > 0:
        df_dining_weekly['dining_index'] = (
            sum(dining_index_components) / total_weight
        )

        print("会食指数の構築完了")
        print(f"使用した指標: {len(dining_index_components)}個")
        print(f"総重み: {total_weight}")
        print("\n会食指数の基本統計量:")
        print(df_dining_weekly['dining_index'].describe())

        df_dining_index = df_dining_weekly[['year', 'week', 'dining_index']].copy()
    else:
        print("エラー: キーワードが見つかりません")
        df_dining_index = None
else:
    print("警告: Google Trendsデータが取得できなかったため、会食指数を構築できません。")
    df_dining_index = None

# ====================
# 4. データの統合
# ====================
print("\n[4] データの統合")
print("-"*60)

if df_dining_index is not None:
    df_mediation = df_fear.merge(
        df_dining_index,
        on=['year', 'week'],
        how='inner'
    )

    print(f"統合データ: {len(df_mediation)}週")
    print(f"期間: {df_mediation['year'].min()}年～{df_mediation['year'].max()}年")

    # 欠損値を削除
    df_mediation = df_mediation.dropna(
        subset=['fear_index', 'dining_index', 'cases_per_sentinel']
    )

    print(f"欠損値削除後: {len(df_mediation)}週")
    print("\n基本統計量:")
    print(df_mediation[['fear_index', 'dining_index', 'cases_per_sentinel']].describe())

else:
    print("エラー: 会食指数が構築できなかったため、媒介分析を実行できません。")
    df_mediation = None

# ====================
# 5. 媒介分析（Mediation Analysis）
# ====================
if df_mediation is not None and len(df_mediation) > 10:
    print("\n" + "="*60)
    print("媒介分析（Mediation Analysis）")
    print("="*60)

    X = df_mediation['fear_index'].values
    M = df_mediation['dining_index'].values
    Y = df_mediation['cases_per_sentinel'].values

    # Step 1: 総合効果（c）
    X_with_const = sm.add_constant(X)
    model_total = sm.OLS(Y, X_with_const).fit()

    c = model_total.params[1]
    c_pvalue = model_total.pvalues[1]

    print("\n[Step 1] 総合効果（X → Y）")
    print(f"係数 c = {c:.4f}")
    print(f"p値 = {c_pvalue:.4f}")
    print(f"R^2 = {model_total.rsquared:.4f}")

    # Step 2: 経路a（X → M）
    model_a = sm.OLS(M, X_with_const).fit()

    a = model_a.params[1]
    a_pvalue = model_a.pvalues[1]

    print("\n[Step 2] 経路a（恐怖指数 → 会食指数）")
    print(f"係数 a = {a:.4f}")
    print(f"p値 = {a_pvalue:.4f}")
    print(f"R^2 = {model_a.rsquared:.4f}")

    if a < 0:
        print("[OK] 期待通り負の係数: 恐怖↑ → 会食↓")
    else:
        print("[NG] 予想と逆の符号: 恐怖↑ → 会食↑")

    # Step 3: 経路b（M → Y、Xを統制）
    X_M = np.column_stack([X, M])
    X_M_with_const = sm.add_constant(X_M)

    model_b = sm.OLS(Y, X_M_with_const).fit()

    c_prime = model_b.params[1]
    b = model_b.params[2]

    c_prime_pvalue = model_b.pvalues[1]
    b_pvalue = model_b.pvalues[2]

    print("\n[Step 3] 経路b（会食指数 → インフルエンザ、恐怖指数を統制）")
    print(f"直接効果 c' = {c_prime:.4f} (p={c_prime_pvalue:.4f})")
    print(f"経路b = {b:.4f} (p={b_pvalue:.4f})")
    print(f"R^2 = {model_b.rsquared:.4f}")

    if b > 0:
        print("[OK] 期待通り正の係数: 会食↑ → インフルエンザ↑")
    else:
        print("[NG] 予想と逆の符号: 会食↑ → インフルエンザ↓")

    # Step 4: 間接効果とSobel検定
    indirect_effect = a * b

    se_a = model_a.bse[1]
    se_b = model_b.bse[2]

    se_indirect = np.sqrt(b**2 * se_a**2 + a**2 * se_b**2)
    z_sobel = indirect_effect / se_indirect
    p_sobel = 2 * (1 - stats.norm.cdf(abs(z_sobel)))

    print("\n[Step 4] 間接効果とSobel検定")
    print(f"間接効果 (a×b) = {indirect_effect:.4f}")
    print(f"標準誤差 = {se_indirect:.4f}")
    print(f"Z統計量 = {z_sobel:.4f}")
    print(f"p値 (Sobel) = {p_sobel:.4f}")

    if p_sobel < 0.05:
        print("[OK] 間接効果は統計的に有意（p<0.05）")
    else:
        print("[NG] 間接効果は統計的に有意でない（p>=0.05）")

    # 検証
    print(f"\n[検証] c = c' + a×b")
    print(f"総合効果 c = {c:.4f}")
    print(f"c' + a×b = {c_prime:.4f} + {indirect_effect:.4f} = {c_prime + indirect_effect:.4f}")
    print(f"差 = {abs(c - (c_prime + indirect_effect)):.6f}")

    # 媒介効果の割合
    if c != 0:
        proportion_mediated = (indirect_effect / c) * 100

        print(f"\n[媒介効果の割合]")
        print(f"間接効果が総合効果に占める割合: {proportion_mediated:.2f}%")
        print(f"直接効果が総合効果に占める割合: {(c_prime/c)*100:.2f}%")

        if abs(proportion_mediated) > 50:
            print("→ 完全媒介に近い（間接効果が支配的）")
        elif abs(proportion_mediated) > 20:
            print("→ 部分媒介（間接効果と直接効果が共存）")
        else:
            print("→ 媒介効果は限定的（直接効果が支配的）")

    # ====================
    # 6. 結果の保存
    # ====================
    print("\n[6] 結果の保存")
    print("-"*60)

    results = pd.DataFrame({
        '効果': ['総合効果 (c)', '経路a (X→M)', '経路b (M→Y)', '直接効果 (c\')', '間接効果 (a×b)'],
        '係数': [c, a, b, c_prime, indirect_effect],
        'p値': [c_pvalue, a_pvalue, b_pvalue, c_prime_pvalue, p_sobel],
        '有意性': [
            '有意' if c_pvalue < 0.05 else '非有意',
            '有意' if a_pvalue < 0.05 else '非有意',
            '有意' if b_pvalue < 0.05 else '非有意',
            '有意' if c_prime_pvalue < 0.05 else '非有意',
            '有意' if p_sobel < 0.05 else '非有意'
        ]
    })

    print("\n媒介分析の結果まとめ:")
    print(results.to_string(index=False))

    # CSVに保存
    results.to_csv('outputs/tables/mediation_analysis_results.csv',
                    index=False, encoding='utf-8-sig')
    print("\n[OK] 結果を保存: outputs/tables/mediation_analysis_results.csv")

    # 統合データも保存
    df_mediation.to_csv('outputs/tables/mediation_analysis_data.csv',
                        index=False, encoding='utf-8-sig')
    print("[OK] 統合データを保存: outputs/tables/mediation_analysis_data.csv")

    print("\n" + "="*60)
    print("媒介分析完了！")
    print("="*60)

else:
    print("\nエラー: 媒介分析を実行できませんでした")
    print("データが不足しているか、取得に失敗しました")
