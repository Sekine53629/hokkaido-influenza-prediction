# インフルエンザ予報Bot システム設計書

**作成日**: 2025年12月1日
**目的**: Phase D拡張版（媒介分析）の学習結果を活用し、Twitter/X等のリアルタイムデータからインフルエンザ流行を予報するシステムの設計

---

## 1. システム概要

### 1.1 背景

Phase D拡張版（媒介分析）により、以下の因果メカニズムが実証されました：

```
恐怖レベル低下 → 会食行動増加 → 接触機会増加 → インフルエンザ増加
```

- **完全媒介を確認**: 間接効果が総合効果の144%を説明
- **経路aの高い説明力**: 恐怖指数→会食指数のR²=44.9%
- **経路bの有意性**: 会食指数→インフルエンザ（p<0.0001）

この発見を実務に活用するため、**リアルタイムデータ収集**と**自動予報**を行うBotシステムを構築します。

### 1.2 システムの目的

1. **リアルタイム予報**: Twitter/X、Google Trendsから恐怖指数・会食指数をリアルタイム計算
2. **在庫最適化**: 60店舗薬局チェーンの風邪薬・マスク等の発注最適化
3. **早期警戒**: インフルエンザ流行の1-2週間前に予兆を検知
4. **ダッシュボード**: 経営陣・店長向けリアルタイム可視化

### 1.3 主要機能

- **データ収集Bot**: Twitter/X API、Google Trends API、感染症情報センター
- **指数計算エンジン**: 恐怖指数、会食指数の自動計算
- **予報モデル**: Phase A（XGBoost）+ Phase D拡張版（媒介モデル）の統合
- **アラートシステム**: 閾値超過時の自動通知（Slack/メール）
- **Webダッシュボード**: リアルタイム可視化とレポート生成

---

## 2. アーキテクチャ設計

### 2.1 システム構成図

```
┌─────────────────────────────────────────────────────────────┐
│                      データソース層                          │
├─────────────────────────────────────────────────────────────┤
│  Twitter/X API  │ Google Trends │ 感染症情報センター │ 気象庁 │
└────────┬────────┴───────┬───────┴──────────┬─────────┴───────┘
         │                │                   │
         ▼                ▼                   ▼
┌─────────────────────────────────────────────────────────────┐
│                    データ収集Bot層                           │
├─────────────────────────────────────────────────────────────┤
│  tweet_collector.py  │ trends_fetcher.py │ sentinel_scraper.py│
│  (毎時実行)          │  (毎日実行)        │  (毎週実行)         │
└────────┬────────────────┬──────────────────┬─────────────────┘
         │                │                  │
         ▼                ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                   データ処理・蓄積層                          │
├─────────────────────────────────────────────────────────────┤
│  PostgreSQL Database  │  時系列データベース（InfluxDB）        │
│  - ツイート生データ   │  - 日次集計データ                      │
│  - Trendsデータ      │  - 週次集計データ                      │
│  - 感染者数データ    │  - 指数計算結果                        │
└────────┬──────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│                     指数計算エンジン                         │
├─────────────────────────────────────────────────────────────┤
│  fear_index_calculator.py    │  dining_index_calculator.py   │
│  - 恐怖関連キーワード集計     │  - 会食関連キーワード集計      │
│  - 加重平均計算（Phase D）   │  - 加重平均計算（Phase D拡張） │
│  - 異常値検出                │  - 異常値検出                  │
└────────┬────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│                     予報モデル層                             │
├─────────────────────────────────────────────────────────────┤
│  Phase A Base Model (XGBoost)                               │
│  - 気象データ・季節性・ラグ特徴量による基本予測              │
│                                                              │
│  Phase D Extended Mediation Model                           │
│  - 経路a: 恐怖指数 → 会食指数の予測                          │
│  - 経路b: 会食指数 → インフルエンザ患者数の予測              │
│  - 間接効果: a × b による行動変容の影響量推定                │
│                                                              │
│  Combined Forecaster                                        │
│  - Base Model + Mediation Adjustment = 最終予報              │
└────────┬────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│                   アラート・通知層                           │
├─────────────────────────────────────────────────────────────┤
│  alert_system.py                                            │
│  - 閾値判定（恐怖指数低下、会食指数上昇、予報急増）          │
│  - Slack通知（経営陣・店長向け）                             │
│  - メール通知（週次レポート）                                │
└────────┬────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│                  可視化・ダッシュボード層                     │
├─────────────────────────────────────────────────────────────┤
│  Streamlit/Gradio Dashboard                                 │
│  - リアルタイム指数表示（恐怖指数、会食指数）                │
│  - 2週間先までのインフルエンザ予報                           │
│  - 店舗別推奨発注量                                          │
│  - 過去データとの比較グラフ                                  │
│  - 媒介分析の経路図（視覚化）                                │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 技術スタック

| 層 | 技術 | 理由 |
|---|---|---|
| **データ収集** | Python 3.13 | 既存分析コードとの統合 |
| | Twitter/X API v2 | ツイートデータ取得 |
| | pytrends | Google Trends API |
| | BeautifulSoup/Selenium | 感染症情報センター スクレイピング |
| **データベース** | PostgreSQL | リレーショナルデータ管理 |
| | InfluxDB | 時系列データ最適化 |
| **予報モデル** | XGBoost | Phase Aで実績あり |
| | statsmodels | 媒介分析モデル |
| | scikit-learn | 前処理・検証 |
| **タスク管理** | Apache Airflow | 定期実行・依存関係管理 |
| | Celery | 非同期タスク処理 |
| **通知** | Slack API | リアルタイム通知 |
| | SendGrid | メール配信 |
| **可視化** | Streamlit | 高速プロトタイプ |
| | Plotly | インタラクティブグラフ |
| **インフラ** | Docker Compose | ローカル開発環境 |
| | AWS ECS/Fargate | 本番環境（またはAzure） |
| | AWS RDS/Aurora | データベース（PostgreSQL） |
| | AWS S3 | データバックアップ |

---

## 3. データ収集仕様

### 3.1 Twitter/X データ収集

#### 3.1.1 収集対象キーワード

**恐怖関連キーワード（Phase D準拠）**:
```python
fear_keywords = [
    'コロナ 死亡',
    '医療崩壊',
    'コロナ 怖い',
    'インフルエンザ 怖い',
    '感染 不安'
]
```

**会食関連キーワード（Phase D拡張版準拠）**:
```python
dining_keywords = [
    '居酒屋',
    '飲み会',
    '忘年会',
    '新年会',
    '歓送迎会',
    '宴会'
]
```

#### 3.1.2 収集仕様

- **地域フィルタ**: 北海道（緯度経度、プロフィール地名）
- **収集頻度**: 毎時実行（1時間ごと）
- **取得件数**: 各キーワード最大100ツイート/時
- **フィルタリング**: リツイート除外、bot除外、スパム除外
- **保存項目**:
  - ツイート本文
  - 投稿日時（UTC+9）
  - ユーザーID（ハッシュ化）
  - エンゲージメント数（いいね、RT）
  - 位置情報（あれば）

#### 3.1.3 Twitter API プラン

- **プラン**: Basic ($100/月) または Pro ($5,000/月)
- **エンドポイント**: `GET /2/tweets/search/recent`
- **レート制限**: Basic 100リクエスト/15分、Pro 300リクエスト/15分
- **コスト**: 月額$100（Basic）で十分

### 3.2 Google Trends データ収集

#### 3.2.1 収集対象

- **恐怖関連**: Phase Dの5キーワード
- **会食関連**: Phase D拡張版の5キーワード
- **地域**: 北海道（geo='JP-01'）
- **期間**: 過去7日間（daily）

#### 3.2.2 収集頻度

- **1日1回実行**（深夜0時）
- **週次集計**: 日曜日にISO週番号で集計

#### 3.2.3 実装

```python
from pytrends.request import TrendReq

def fetch_google_trends_daily():
    pytrends = TrendReq(hl='ja-JP', tz=540)

    # 恐怖指数
    pytrends.build_payload(
        kw_list=fear_keywords,
        geo='JP-01',
        timeframe='now 7-d'
    )
    fear_data = pytrends.interest_over_time()

    # 会食指数
    pytrends.build_payload(
        kw_list=dining_keywords,
        geo='JP-01',
        timeframe='now 7-d'
    )
    dining_data = pytrends.interest_over_time()

    return fear_data, dining_data
```

### 3.3 感染症情報センター データ収集

#### 3.3.1 収集対象

- **URL**: https://www.iph.pref.hokkaido.jp/kansen/501/data.html
- **データ**: 週次インフルエンザ定点当たり患者数
- **収集頻度**: 毎週木曜日（更新日）

#### 3.3.2 スクレイピング実装

```python
import requests
from bs4 import BeautifulSoup

def scrape_sentinel_data():
    url = 'https://www.iph.pref.hokkaido.jp/kansen/501/data.html'
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # テーブル解析（実装はサイト構造に依存）
    table = soup.find('table', {'class': 'data-table'})
    # ... パース処理

    return data
```

---

## 4. 指数計算エンジン

### 4.1 恐怖指数計算（Phase D準拠）

#### 4.1.1 加重平均方式

```python
# Phase D実績の重み
fear_weights = {
    'コロナ 死亡': 3.0,
    '医療崩壊': 2.5,
    'コロナ 怖い': 2.0,
    'インフルエンザ 怖い': 1.5,
    '感染 不安': 1.0
}

def calculate_fear_index(trends_data, tweet_counts):
    """
    Google Trends + Twitter両方のデータを統合
    """
    fear_index = 0
    total_weight = sum(fear_weights.values())

    for keyword, weight in fear_weights.items():
        # Google Trendsスコア（0-100）
        trends_score = trends_data.get(keyword, 0)

        # Twitterツイート数（正規化）
        tweet_count = tweet_counts.get(keyword, 0)
        tweet_score = min(100, tweet_count / 10)  # 1000ツイート=100スコア

        # 平均を取る
        combined_score = (trends_score + tweet_score) / 2

        fear_index += combined_score * weight

    fear_index /= total_weight
    return fear_index
```

#### 4.1.2 週次集計

```python
import pandas as pd

def aggregate_weekly_fear_index(daily_data):
    """
    日次データをISO週番号で週次集計
    """
    df = pd.DataFrame(daily_data)
    df['year'] = df['date'].dt.isocalendar().year
    df['week'] = df['date'].dt.isocalendar().week

    weekly = df.groupby(['year', 'week']).agg({
        'fear_index': 'mean'
    }).reset_index()

    return weekly
```

### 4.2 会食指数計算（Phase D拡張版準拠）

#### 4.2.1 加重平均方式

```python
# Phase D拡張版実績の重み
dining_weights = {
    '居酒屋': 3.0,      # 最も直接的
    '飲み会': 2.5,
    '忘年会': 1.5,      # 季節的
    '新年会': 1.5,      # 季節的
    '歓送迎会': 1.0     # 季節的
}

def calculate_dining_index(trends_data, tweet_counts):
    """
    会食指数の計算（恐怖指数と同じロジック）
    """
    dining_index = 0
    total_weight = sum(dining_weights.values())

    for keyword, weight in dining_weights.items():
        trends_score = trends_data.get(keyword, 0)
        tweet_count = tweet_counts.get(keyword, 0)
        tweet_score = min(100, tweet_count / 10)
        combined_score = (trends_score + tweet_score) / 2

        dining_index += combined_score * weight

    dining_index /= total_weight
    return dining_index
```

### 4.3 異常値検出

```python
from scipy import stats

def detect_anomalies(index_values, threshold=3.0):
    """
    Z-scoreによる異常値検出
    """
    z_scores = stats.zscore(index_values)
    anomalies = abs(z_scores) > threshold
    return anomalies
```

---

## 5. 予報モデル設計

### 5.1 Phase A Base Model（XGBoost）

#### 5.1.1 入力特徴量

```python
base_features = [
    'week_of_year',          # 季節性
    'avg_temp',              # 平均気温
    'avg_humidity',          # 平均湿度
    'cases_lag_1',           # 1週前の患者数
    'cases_lag_2',           # 2週前の患者数
    'cases_lag_3',           # 3週前の患者数
    'cases_lag_4',           # 4週前の患者数
]
```

#### 5.1.2 出力

- `cases_per_sentinel_base`: 基本予測値（Phase Aのみ）

### 5.2 Phase D Extended Mediation Model

#### 5.2.1 経路aモデル（恐怖指数 → 会食指数）

```python
import statsmodels.api as sm

def predict_dining_from_fear(fear_index):
    """
    Phase D拡張版の経路aモデル
    係数: a = -0.3271, R² = 0.4486
    """
    # 学習済みモデルのロード
    model_a = load_model('models/mediation_path_a.pkl')

    X = sm.add_constant(fear_index)
    dining_index_pred = model_a.predict(X)

    return dining_index_pred
```

#### 5.2.2 経路bモデル（会食指数 → インフルエンザ）

```python
def predict_influenza_from_dining(fear_index, dining_index):
    """
    Phase D拡張版の経路bモデル
    係数: b = 0.7500, c' = 0.0752
    """
    # 学習済みモデルのロード
    model_b = load_model('models/mediation_path_b.pkl')

    X = np.column_stack([fear_index, dining_index])
    X = sm.add_constant(X)
    cases_adjustment = model_b.predict(X)

    return cases_adjustment
```

### 5.3 統合予報モデル

```python
class IntegratedForecastModel:
    def __init__(self):
        self.base_model = load_model('models/xgboost_phase_a.pkl')
        self.mediation_path_a = load_model('models/mediation_path_a.pkl')
        self.mediation_path_b = load_model('models/mediation_path_b.pkl')

    def forecast(self, weather_data, lag_data, fear_index):
        """
        統合予報
        """
        # Step 1: Base予測（Phase A）
        base_features = self._prepare_base_features(
            weather_data, lag_data
        )
        base_forecast = self.base_model.predict(base_features)

        # Step 2: 媒介分析による調整（Phase D拡張版）
        # 経路a: 恐怖指数 → 会食指数
        dining_index_pred = self._predict_path_a(fear_index)

        # 経路b: 会食指数 → インフルエンザ（恐怖指数を統制）
        mediation_adjustment = self._predict_path_b(
            fear_index, dining_index_pred
        )

        # Step 3: 統合予報
        final_forecast = base_forecast + mediation_adjustment

        return {
            'base_forecast': base_forecast,
            'mediation_adjustment': mediation_adjustment,
            'final_forecast': final_forecast,
            'fear_index': fear_index,
            'dining_index_pred': dining_index_pred
        }

    def _prepare_base_features(self, weather_data, lag_data):
        # 特徴量エンジニアリング
        pass

    def _predict_path_a(self, fear_index):
        # 経路aの予測
        pass

    def _predict_path_b(self, fear_index, dining_index):
        # 経路bの予測
        pass
```

---

## 6. アラートシステム

### 6.1 閾値設定

```python
ALERT_THRESHOLDS = {
    'fear_index_drop': -10,      # 恐怖指数が1週間で10pt以上低下
    'dining_index_rise': +15,    # 会食指数が1週間で15pt以上上昇
    'forecast_surge': +5.0,      # 予報が1週間で5人/定点以上増加
    'forecast_high': 10.0,       # 予報が10人/定点以上（流行警報レベル）
}
```

### 6.2 アラートロジック

```python
def check_alerts(current_data, previous_data):
    alerts = []

    # 恐怖指数低下アラート
    fear_change = current_data['fear_index'] - previous_data['fear_index']
    if fear_change < ALERT_THRESHOLDS['fear_index_drop']:
        alerts.append({
            'type': 'fear_index_drop',
            'severity': 'warning',
            'message': f'恐怖指数が{abs(fear_change):.1f}pt低下しました。会食増加の可能性があります。',
            'recommendation': '風邪薬・マスクの在庫確認を推奨'
        })

    # 会食指数上昇アラート
    dining_change = current_data['dining_index'] - previous_data['dining_index']
    if dining_change > ALERT_THRESHOLDS['dining_index_rise']:
        alerts.append({
            'type': 'dining_index_rise',
            'severity': 'warning',
            'message': f'会食指数が{dining_change:.1f}pt上昇しました。接触機会増加の兆候です。',
            'recommendation': 'インフルエンザ関連商品の発注増を推奨'
        })

    # 予報急増アラート
    forecast_change = current_data['final_forecast'] - previous_data['final_forecast']
    if forecast_change > ALERT_THRESHOLDS['forecast_surge']:
        alerts.append({
            'type': 'forecast_surge',
            'severity': 'critical',
            'message': f'インフルエンザ予報が{forecast_change:.1f}人/定点増加。2週間以内に流行拡大の可能性。',
            'recommendation': '緊急発注の検討を推奨'
        })

    # 流行警報レベルアラート
    if current_data['final_forecast'] > ALERT_THRESHOLDS['forecast_high']:
        alerts.append({
            'type': 'forecast_high',
            'severity': 'critical',
            'message': f'予報が{current_data["final_forecast"]:.1f}人/定点に達しました（流行警報レベル）。',
            'recommendation': '全店舗に在庫増強指示を推奨'
        })

    return alerts
```

### 6.3 Slack通知

```python
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

def send_slack_alert(alerts):
    client = WebClient(token=os.environ['SLACK_BOT_TOKEN'])

    for alert in alerts:
        color = 'warning' if alert['severity'] == 'warning' else 'danger'

        message = {
            'channel': '#influenza-forecasts',
            'attachments': [
                {
                    'color': color,
                    'title': f"[{alert['type'].upper()}] {alert['message']}",
                    'fields': [
                        {
                            'title': '推奨アクション',
                            'value': alert['recommendation'],
                            'short': False
                        }
                    ],
                    'footer': 'インフルエンザ予報Bot',
                    'ts': int(time.time())
                }
            ]
        }

        try:
            client.chat_postMessage(**message)
        except SlackApiError as e:
            print(f"Error sending Slack message: {e}")
```

---

## 7. ダッシュボード設計

### 7.1 Streamlit実装

```python
import streamlit as st
import plotly.graph_objects as go

def main():
    st.set_page_config(
        page_title='インフルエンザ予報ダッシュボード',
        page_icon='🦠',
        layout='wide'
    )

    st.title('🦠 北海道インフルエンザ予報システム')
    st.markdown('**Phase D拡張版（媒介分析）による因果モデル予報**')

    # データ取得
    current_data = fetch_latest_data()
    forecast_data = fetch_forecast_data()

    # メトリクス表示
    col1,, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label='恐怖指数',
            value=f"{current_data['fear_index']:.1f}",
            delta=f"{current_data['fear_index_change']:+.1f}pt"
        )

    with col2:
        st.metric(
            label='会食指数',
            value=f"{current_data['dining_index']:.1f}",
            delta=f"{current_data['dining_index_change']:+.1f}pt"
        )

    with col3:
        st.metric(
            label='現在の患者数',
            value=f"{current_data['cases_per_sentinel']:.1f}",
            delta=f"{current_data['cases_change']:+.1f}人/定点"
        )

    with col4:
        st.metric(
            label='2週間後予報',
            value=f"{forecast_data['forecast_2w']:.1f}",
            delta=f"{forecast_data['forecast_2w_change']:+.1f}人/定点"
        )

    # 媒介分析の因果経路図
    st.subheader('📊 因果メカニズム（媒介分析）')
    display_mediation_diagram(current_data)

    # 時系列グラフ
    st.subheader('📈 時系列トレンド')
    display_time_series(forecast_data)

    # アラート表示
    st.subheader('⚠️ アラート')
    display_alerts(current_data)

    # 店舗別推奨発注量
    st.subheader('🏪 店舗別推奨発注量（60店舗）')
    display_store_recommendations(forecast_data)

def display_mediation_diagram(data):
    """
    媒介分析の経路図を表示
    """
    fig = go.Figure()

    # ノード
    fig.add_trace(go.Scatter(
        x=[0, 1, 2],
        y=[0, 1, 0],
        mode='markers+text',
        marker=dict(size=50, color=['lightblue', 'lightgreen', 'salmon']),
        text=['恐怖指数', '会食指数', 'インフルエンザ'],
        textposition='top center',
        textfont=dict(size=14, family='MS Gothic'),
        hoverinfo='text'
    ))

    # 経路a
    fig.add_annotation(
        x=0.5, y=0.5,
        ax=0, ay=0,
        xref='x', yref='y',
        axref='x', ayref='y',
        showarrow=True,
        arrowhead=2,
        arrowsize=1,
        arrowwidth=2,
        arrowcolor='blue',
        text=f'経路a<br>係数: -0.327<br>R²: 44.9%',
        font=dict(size=10)
    )

    # 経路b
    fig.add_annotation(
        x=1.5, y=0.5,
        ax=1, ay=1,
        xref='x', yref='y',
        axref='x', ayref='y',
        showarrow=True,
        arrowhead=2,
        arrowsize=1,
        arrowwidth=2,
        arrowcolor='green',
        text=f'経路b<br>係数: 0.750<br>p<0.0001',
        font=dict(size=10)
    )

    # 直接効果（破線）
    fig.add_annotation(
        x=2, y=0,
        ax=0, ay=0,
        xref='x', yref='y',
        axref='x', ayref='y',
        showarrow=True,
        arrowhead=2,
        arrowsize=1,
        arrowwidth=1,
        arrowcolor='gray',
        arrowdash='dash',
        text=f'直接効果<br>c\': 0.075<br>p=0.183（非有意）',
        font=dict(size=9, color='gray')
    )

    fig.update_layout(
        showlegend=False,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        height=400,
        title='完全媒介モデル（間接効果: 144.2%）'
    )

    st.plotly_chart(fig, use_container_width=True)

def display_time_series(data):
    """
    時系列グラフを表示
    """
    fig = go.Figure()

    # 実測値
    fig.add_trace(go.Scatter(
        x=data['date'],
        y=data['actual'],
        mode='lines+markers',
        name='実測値',
        line=dict(color='blue')
    ))

    # 予報値
    fig.add_trace(go.Scatter(
        x=data['date_forecast'],
        y=data['forecast'],
        mode='lines+markers',
        name='予報値',
        line=dict(color='red', dash='dash')
    ))

    # 恐怖指数（副軸）
    fig.add_trace(go.Scatter(
        x=data['date'],
        y=data['fear_index'],
        mode='lines',
        name='恐怖指数',
        line=dict(color='orange'),
        yaxis='y2'
    ))

    # 会食指数（副軸）
    fig.add_trace(go.Scatter(
        x=data['date'],
        y=data['dining_index'],
        mode='lines',
        name='会食指数',
        line=dict(color='green'),
        yaxis='y2'
    ))

    fig.update_layout(
        title='インフルエンザ患者数と各種指数のトレンド',
        xaxis_title='日付',
        yaxis_title='定点当たり患者数',
        yaxis2=dict(
            title='指数スコア',
            overlaying='y',
            side='right'
        ),
        hovermode='x unified',
        height=500
    )

    st.plotly_chart(fig, use_container_width=True)

def display_alerts(data):
    """
    アラート表示
    """
    alerts = check_alerts(data, previous_data)

    if not alerts:
        st.success('✅ 現在、アラートはありません。')
    else:
        for alert in alerts:
            if alert['severity'] == 'critical':
                st.error(f"🚨 {alert['message']}\n\n**推奨**: {alert['recommendation']}")
            else:
                st.warning(f"⚠️ {alert['message']}\n\n**推奨**: {alert['recommendation']}")

def display_store_recommendations(forecast_data):
    """
    店舗別推奨発注量
    """
    # 予報値に基づく発注量計算
    base_order = forecast_data['forecast_2w'] * 10  # 仮の係数

    stores = fetch_store_list()  # 60店舗リスト

    recommendations = []
    for store in stores:
        store_factor = store['historical_demand_ratio']
        recommended_order = int(base_order * store_factor)

        recommendations.append({
            '店舗名': store['name'],
            '地域': store['region'],
            '推奨発注量（風邪薬）': f"{recommended_order}個",
            '推奨発注量（マスク）': f"{recommended_order * 2}箱",
            '発注優先度': '高' if recommended_order > 100 else '中'
        })

    df_recommendations = pd.DataFrame(recommendations)
    st.dataframe(df_recommendations, use_container_width=True)

if __name__ == '__main__':
    main()
```

---

## 8. デプロイ・運用設計

### 8.1 Docker Compose（ローカル開発）

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: influenza_forecast
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  influxdb:
    image: influxdb:2.7
    environment:
      INFLUXDB_DB: timeseries
      INFLUXDB_ADMIN_USER: admin
      INFLUXDB_ADMIN_PASSWORD: ${INFLUXDB_PASSWORD}
    volumes:
      - influxdb_data:/var/lib/influxdb
    ports:
      - "8086:8086"

  airflow:
    image: apache/airflow:2.7.0
    environment:
      AIRFLOW__CORE__EXECUTOR: LocalExecutor
      AIRFLOW__CORE__SQL_ALCHEMY_CONN: postgresql+psycopg2://admin:${DB_PASSWORD}@postgres/airflow
    volumes:
      - ./dags:/opt/airflow/dags
      - ./logs:/opt/airflow/logs
    ports:
      - "8080:8080"
    depends_on:
      - postgres

  streamlit:
    build: ./dashboard
    ports:
      - "8501:8501"
    environment:
      DATABASE_URL: postgresql://admin:${DB_PASSWORD}@postgres/influenza_forecast
    depends_on:
      - postgres
      - influxdb

volumes:
  postgres_data:
  influxdb_data:
```

### 8.2 AWS本番環境構成

```
┌─────────────────────────────────────────────────────────┐
│                       AWS VPC                            │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌─────────────────┐         ┌─────────────────┐       │
│  │   ECS Fargate   │         │   ECS Fargate   │       │
│  │  (Airflow)      │────────▶│  (Streamlit)    │       │
│  │  - DAG実行      │         │  - Dashboard    │       │
│  │  - データ収集    │         └─────────────────┘       │
│  └─────────────────┘                  │                │
│         │                             │                │
│         ▼                             ▼                │
│  ┌─────────────────┐         ┌─────────────────┐       │
│  │  RDS Aurora     │         │  ElastiCache    │       │
│  │  (PostgreSQL)   │         │  (Redis)        │       │
│  └─────────────────┘         └─────────────────┘       │
│         │                                               │
│         ▼                                               │
│  ┌─────────────────┐                                    │
│  │     S3          │                                    │
│  │  - Backup       │                                    │
│  │  - Logs         │                                    │
│  └─────────────────┘                                    │
│                                                          │
└─────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────┐       ┌─────────────────┐
│  CloudWatch     │       │  SNS/SES        │
│  - Monitoring   │       │  - Alerts       │
└─────────────────┘       └─────────────────┘
```

### 8.3 Apache Airflow DAG

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'influenza-forecast-team',
    'depends_on_past': False,
    'start_date': datetime(2025, 12, 1),
    'email': ['alerts@pharmacy-chain.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'influenza_forecast_pipeline',
    default_args=default_args,
    description='インフルエンザ予報パイプライン',
    schedule_interval='0 */1 * * *',  # 毎時実行
    catchup=False
)

# タスク定義
collect_tweets = PythonOperator(
    task_id='collect_tweets',
    python_callable=collect_twitter_data,
    dag=dag
)

collect_trends = PythonOperator(
    task_id='collect_google_trends',
    python_callable=fetch_google_trends_daily,
    dag=dag
)

calculate_fear = PythonOperator(
    task_id='calculate_fear_index',
    python_callable=calculate_fear_index,
    dag=dag
)

calculate_dining = PythonOperator(
    task_id='calculate_dining_index',
    python_callable=calculate_dining_index,
    dag=dag
)

run_forecast = PythonOperator(
    task_id='run_forecast_model',
    python_callable=run_integrated_forecast,
    dag=dag
)

check_alerts_task = PythonOperator(
    task_id='check_alerts',
    python_callable=check_and_send_alerts,
    dag=dag
)

# 依存関係
[collect_tweets, collect_trends] >> calculate_fear
[collect_tweets, collect_trends] >> calculate_dining
[calculate_fear, calculate_dining] >> run_forecast
run_forecast >> check_alerts_task
```

### 8.4 コスト見積もり

| 項目 | 詳細 | 月額コスト（USD） |
|---|---|---|
| **Twitter/X API** | Basic Plan | $100 |
| **AWS ECS Fargate** | 2タスク×24h稼働 | $50 |
| **AWS RDS Aurora** | db.t3.medium | $100 |
| **AWS ElastiCache** | cache.t3.micro | $15 |
| **AWS S3** | 100GB ストレージ | $3 |
| **CloudWatch** | ログ・メトリクス | $10 |
| **Slack/SendGrid** | 無料枠内 | $0 |
| **ドメイン・SSL** | Route53 + ACM | $1 |
| **合計** | | **約$280/月** |

日本円換算（1 USD = 150円として）: **約42,000円/月**

### 8.5 監視・アラート

```python
# CloudWatch メトリクス
import boto3

cloudwatch = boto3.client('cloudwatch')

def publish_metrics(fear_index, dining_index, forecast):
    cloudwatch.put_metric_data(
        Namespace='InfluenzaForecast',
        MetricData=[
            {
                'MetricName': 'FearIndex',
                'Value': fear_index,
                'Unit': 'None'
            },
            {
                'MetricName': 'DiningIndex',
                'Value': dining_index,
                'Unit': 'None'
            },
            {
                'MetricName': 'ForecastValue',
                'Value': forecast,
                'Unit': 'Count'
            }
        ]
    )
```

---

## 9. セキュリティ・プライバシー

### 9.1 データ保護

- **個人情報の非保持**: ツイートからユーザーIDをハッシュ化、個人特定情報は保存しない
- **暗号化**: データベース暗号化（RDS KMS）、通信はTLS 1.3
- **アクセス制御**: IAM Role-based access control、最小権限の原則

### 9.2 コンプライアンス

- **Twitter API利用規約**: データの二次利用禁止、保存期間制限を遵守
- **GDPR/個人情報保護法**: 個人情報を扱わない設計
- **薬機法**: 医療機器ではなく需要予測ツールとして位置づけ

---

## 10. 開発ロードマップ

### Phase 1: プロトタイプ構築（1-2ヶ月）

- [ ] Twitter API連携とデータ収集Bot
- [ ] Google Trends API連携
- [ ] PostgreSQLデータベース設計・構築
- [ ] 恐怖指数・会食指数の計算エンジン
- [ ] 媒介分析モデルの実装（Phase D拡張版）
- [ ] 統合予報モデルの実装（Phase A + 媒介モデル）
- [ ] Streamlitダッシュボード基本版

### Phase 2: 検証・改善（1ヶ月）

- [ ] 実データでの精度検証
- [ ] バックテスト（過去データでの予報精度評価）
- [ ] モデルパラメータのチューニング
- [ ] ダッシュボードUI/UX改善
- [ ] アラート閾値の調整

### Phase 3: 本番化（1ヶ月）

- [ ] AWS環境構築（Fargate, RDS, S3）
- [ ] Apache Airflow DAG実装
- [ ] Slack/メール通知システム
- [ ] 監視・ロギング体制構築
- [ ] ドキュメント整備（運用マニュアル）

### Phase 4: 運用開始（継続）

- [ ] 60店舗へのダッシュボード展開
- [ ] 週次レポート自動生成
- [ ] フィードバック収集・改善
- [ ] モデル再学習（月次）

---

## 11. 期待される効果

### 11.1 定量的効果

1. **在庫最適化**:
   - 過剰在庫削減: 20%減（約2,000万円/年のコスト削減）
   - 欠品防止: 機会損失5%削減（約1,500万円/年の売上増）

2. **予報精度**:
   - 2週間先予報のR²: 15-20%を目標（Phase A単独の3-4倍）
   - 早期警戒: 流行の1-2週間前に予兆検知

3. **業務効率化**:
   - 発注業務時間: 50%削減（手動判断 → 自動推奨）
   - レポート作成時間: 90%削減（手動集計 → 自動生成）

### 11.2 定性的効果

1. **データドリブン経営の推進**: 感覚に頼らない科学的な意思決定
2. **競争優位性の獲得**: 業界初の因果モデル予報システム
3. **ブランド価値向上**: 先進的DX企業としてのイメージ
4. **学術的貢献**: 媒介分析の実務応用事例として論文化可能

---

## 12. リスクと対策

### 12.1 技術的リスク

| リスク | 影響 | 対策 |
|---|---|---|
| Twitter API制限 | データ収集停止 | Google Trends単独でも動作する設計 |
| モデル精度低下 | 予報外れ | 月次でモデル再学習、人間の最終判断を残す |
| システム障害 | 予報停止 | 冗長化（Multi-AZ）、フェイルオーバー |

### 12.2 運用リスク

| リスク | 影響 | 対策 |
|---|---|---|
| 過度な依存 | 判断力低下 | あくまで補助ツール、人間の判断を重視 |
| データ品質低下 | 予報精度低下 | 異常値検出、データ検証フロー |
| コスト超過 | 予算オーバー | CloudWatch Cost Anomaly Detection |

---

## 13. まとめ

本設計書では、Phase D拡張版（媒介分析）で実証した**因果メカニズム**を実務に活用するBotシステムを提案しました。

### 13.1 システムの核心価値

1. **科学的根拠**: 完全媒介モデル（R²=44.9%、p<0.0001）による高精度予報
2. **リアルタイム性**: Twitter/X、Google Trendsから恐怖指数・会食指数を毎時計算
3. **実用性**: 60店舗薬局チェーンの在庫最適化に直結
4. **拡張性**: 他の感染症（COVID-19、ノロウイルス等）にも応用可能

### 13.2 次のステップ

1. **ユーザー承認**: この設計書をレビューし、実装に進むか判断
2. **Phase 1開始**: プロトタイプ構築（目安: 1-2ヶ月）
3. **技術選定確定**: AWS vs Azure、Streamlit vs Gradio等
4. **予算確保**: 初期開発費 + 運用費（月額4-5万円）

### 13.3 成功のカギ

- **段階的アプローチ**: まずプロトタイプで検証、本番化は慎重に
- **フィードバックループ**: 実測値と予報値の乖離を分析し、モデル改善
- **人間中心設計**: Botは補助、最終判断は人間（店長・経営陣）

---

**この設計書についてのご質問・ご要望がございましたら、お気軽にお申し付けください。**
