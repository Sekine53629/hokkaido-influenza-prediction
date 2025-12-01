"""
北海道インフルエンザ患者数予測
データサイエンスコース卒業課題

このスクリプトは分析の骨格テンプレートです。
Jupyter Notebookに移植して使用することを推奨します。
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split, GridSearchCV, TimeSeriesSplit
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import xgboost as xgb
import warnings
warnings.filterwarnings('ignore')

# 日本語フォント設定
plt.rcParams['font.sans-serif'] = ['MS Gothic', 'Yu Gothic', 'Hiragino Sans']
plt.rcParams['axes.unicode_minus'] = False

# =====================================
# 1. データの読み込み
# =====================================

def load_influenza_data(years=range(2015, 2025)):
    """
    北海道感染症情報センターからダウンロードしたインフルエンザデータを読み込む
    """
    dfs = []
    for year in years:
        try:
            df = pd.read_csv(f'data/raw/influenza/{year}.csv', encoding='shift-jis')
            dfs.append(df)
            print(f'{year}年のデータ読み込み成功')
        except FileNotFoundError:
            print(f'{year}年のデータが見つかりません')

    # 全年データを結合
    df_flu = pd.concat(dfs, ignore_index=True)
    return df_flu


def load_weather_data():
    """
    気象庁からダウンロードした気象データを読み込む
    """
    df_weather = pd.read_csv('data/raw/weather/sapporo_weather_2015-2024.csv',
                             encoding='shift-jis')
    print(f'気象データ読み込み成功: {df_weather.shape}')
    return df_weather


# =====================================
# 2. EDA（探索的データ分析）
# =====================================

def explore_data(df_flu, df_weather):
    """
    データの基本統計量と欠損値を確認
    """
    print("=== インフルエンザデータ ===")
    print(df_flu.head())
    print(df_flu.info())
    print(df_flu.describe())
    print(f"\n欠損値:\n{df_flu.isnull().sum()}")

    print("\n=== 気象データ ===")
    print(df_weather.head())
    print(df_weather.info())
    print(df_weather.describe())
    print(f"\n欠損値:\n{df_weather.isnull().sum()}")


def plot_time_series(df):
    """
    時系列プロット
    """
    plt.figure(figsize=(14, 6))
    plt.plot(df['date'], df['cases_per_sentinel'], marker='o', markersize=3)
    plt.title('北海道インフルエンザ定点当たり報告数の推移 (2015-2024)', fontsize=14)
    plt.xlabel('年月', fontsize=12)
    plt.ylabel('定点当たり報告数', fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.axvline(pd.to_datetime('2020-03-01'), color='red', linestyle='--',
                label='COVID-19介入開始')
    plt.legend()
    plt.tight_layout()
    plt.savefig('outputs/figures/influenza_time_series.png', dpi=300)
    plt.show()


# =====================================
# 3. 特徴量エンジニアリング
# =====================================

def create_features(df):
    """
    予測に使う特徴量を作成
    """
    df = df.copy()

    # 日付型に変換
    df['date'] = pd.to_datetime(df['date'])

    # 週番号（季節性）
    df['week_of_year'] = df['date'].dt.isocalendar().week

    # ラグ特徴量（1週前、2週前、4週前）
    df['lag_1'] = df['cases_per_sentinel'].shift(1)
    df['lag_2'] = df['cases_per_sentinel'].shift(2)
    df['lag_4'] = df['cases_per_sentinel'].shift(4)

    # 移動平均（4週間）
    df['rolling_mean_4'] = df['cases_per_sentinel'].rolling(window=4).mean()

    # 気象データとマージ（週次集計）
    # ※ここでは仮のコード。実際のカラム名に合わせて調整してください
    # df = df.merge(weekly_weather, on='date', how='left')

    # 学校休暇フラグ（仮実装：12-1月、3-4月、7-8月）
    df['is_school_holiday'] = df['date'].dt.month.isin([12, 1, 3, 4, 7, 8]).astype(int)

    # 欠損値を除去
    df = df.dropna()

    return df


# =====================================
# 4. 相関分析
# =====================================

def correlation_analysis(df):
    """
    特徴量間の相関を確認
    """
    features = ['cases_per_sentinel', 'week_of_year', 'lag_1', 'lag_2', 'lag_4',
                'avg_temp', 'avg_humidity', 'is_school_holiday']

    corr_matrix = df[features].corr()

    plt.figure(figsize=(10, 8))
    sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0)
    plt.title('特徴量間の相関係数', fontsize=14)
    plt.tight_layout()
    plt.savefig('outputs/figures/correlation_matrix.png', dpi=300)
    plt.show()

    return corr_matrix


# =====================================
# 5. モデル学習・評価
# =====================================

def prepare_train_test_split(df, test_start_date='2019-09-01'):
    """
    学習データとテストデータに分割
    2015-2019年を学習、2019-2020シーズン前半をテストとする
    """
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])

    train = df[df['date'] < test_start_date]
    test = df[df['date'] >= test_start_date]

    # 特徴量とターゲットを分離
    feature_cols = ['week_of_year', 'lag_1', 'lag_2', 'lag_4',
                    'avg_temp', 'avg_humidity', 'is_school_holiday']

    X_train = train[feature_cols]
    y_train = train['cases_per_sentinel']
    X_test = test[feature_cols]
    y_test = test['cases_per_sentinel']

    return X_train, X_test, y_train, y_test, test


def train_models(X_train, y_train):
    """
    複数のモデルを学習
    """
    models = {
        'Linear Regression': LinearRegression(),
        'Ridge': Ridge(alpha=1.0),
        'Lasso': Lasso(alpha=0.1),
        'Random Forest': RandomForestRegressor(n_estimators=100, random_state=42),
        'Gradient Boosting': GradientBoostingRegressor(n_estimators=100, random_state=42),
        'XGBoost': xgb.XGBRegressor(n_estimators=100, random_state=42)
    }

    trained_models = {}
    for name, model in models.items():
        model.fit(X_train, y_train)
        trained_models[name] = model
        print(f'{name} 学習完了')

    return trained_models


def evaluate_models(models, X_test, y_test):
    """
    各モデルの性能を評価
    """
    results = []

    for name, model in models.items():
        y_pred = model.predict(X_test)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)

        results.append({
            'Model': name,
            'RMSE': rmse,
            'MAE': mae,
            'R2': r2
        })

        print(f'{name}: RMSE={rmse:.4f}, MAE={mae:.4f}, R2={r2:.4f}')

    df_results = pd.DataFrame(results).sort_values('RMSE')
    return df_results


# =====================================
# 6. ハイパーパラメータチューニング
# =====================================

def tune_best_model(X_train, y_train):
    """
    最良モデルのハイパーパラメータチューニング（例：XGBoost）
    """
    param_grid = {
        'n_estimators': [50, 100, 200],
        'max_depth': [3, 5, 7],
        'learning_rate': [0.01, 0.05, 0.1],
        'subsample': [0.7, 0.8, 0.9]
    }

    xgb_model = xgb.XGBRegressor(random_state=42)

    # 時系列交差検証
    tscv = TimeSeriesSplit(n_splits=5)

    grid_search = GridSearchCV(
        xgb_model, param_grid, cv=tscv,
        scoring='neg_root_mean_squared_error', n_jobs=-1, verbose=1
    )

    grid_search.fit(X_train, y_train)

    print(f'最適パラメータ: {grid_search.best_params_}')
    print(f'最良スコア: {-grid_search.best_score_:.4f}')

    return grid_search.best_estimator_


# =====================================
# 7. 特徴量重要度
# =====================================

def plot_feature_importance(model, feature_names):
    """
    特徴量重要度のプロット（Tree-basedモデルのみ）
    """
    if hasattr(model, 'feature_importances_'):
        importances = model.feature_importances_
        indices = np.argsort(importances)[::-1]

        plt.figure(figsize=(10, 6))
        plt.bar(range(len(importances)), importances[indices])
        plt.xticks(range(len(importances)), [feature_names[i] for i in indices],
                   rotation=45, ha='right')
        plt.title('特徴量重要度', fontsize=14)
        plt.ylabel('重要度', fontsize=12)
        plt.tight_layout()
        plt.savefig('outputs/figures/feature_importance.png', dpi=300)
        plt.show()


# =====================================
# 8. 予測結果の可視化
# =====================================

def plot_predictions(test_df, y_test, y_pred, model_name='Best Model'):
    """
    実測値と予測値の比較プロット
    """
    plt.figure(figsize=(14, 6))
    plt.plot(test_df['date'], y_test, label='実測値', marker='o', markersize=4)
    plt.plot(test_df['date'], y_pred, label='予測値', marker='x', markersize=4)
    plt.title(f'{model_name} - 予測結果の比較', fontsize=14)
    plt.xlabel('年月', fontsize=12)
    plt.ylabel('定点当たり報告数', fontsize=12)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(f'outputs/figures/{model_name}_predictions.png', dpi=300)
    plt.show()


# =====================================
# 9. メイン処理
# =====================================

def main():
    """
    分析のメインフロー
    """
    print("=== 1. データ読み込み ===")
    df_flu = load_influenza_data()
    df_weather = load_weather_data()

    print("\n=== 2. EDA ===")
    explore_data(df_flu, df_weather)

    # ※データマージとクリーニングは実際のデータ構造に合わせて調整してください
    # df_merged = merge_data(df_flu, df_weather)

    print("\n=== 3. 特徴量エンジニアリング ===")
    # df_features = create_features(df_merged)

    # ※以下は仮のプレースホルダーです。実データに合わせて調整してください
    # plot_time_series(df_features)
    # corr_matrix = correlation_analysis(df_features)

    print("\n=== 4. モデル学習・評価 ===")
    # X_train, X_test, y_train, y_test, test_df = prepare_train_test_split(df_features)
    # models = train_models(X_train, y_train)
    # results = evaluate_models(models, X_test, y_test)
    # print(results)

    print("\n=== 5. ハイパーパラメータチューニング ===")
    # best_model = tune_best_model(X_train, y_train)

    print("\n=== 6. 特徴量重要度 ===")
    # plot_feature_importance(best_model, X_train.columns)

    print("\n=== 7. 予測結果の可視化 ===")
    # y_pred = best_model.predict(X_test)
    # plot_predictions(test_df, y_test, y_pred, model_name='XGBoost')

    print("\n=== 分析完了 ===")


if __name__ == '__main__':
    main()
