# 北海道インフルエンザ患者数予測

回帰モデルを用いた北海道のインフルエンザ週別患者数予測と、COVID-19がインフルエンザ感染に与えた影響の分析

## プロジェクト概要

データサイエンスコースの卒業課題として、2段階で取り組みます：

- **第1段階（卒業課題）**: 気象データと過去のデータに基づき、回帰モデルで北海道のインフルエンザ週別患者数を予測
- **第2段階（発展課題）**: 因果推論手法を用いて、COVID-19対策がインフルエンザ感染抑制に与えた影響を定量化

## 背景

北海道で60店舗以上を管理する薬剤師・DX担当として、医療統計の知見とデータサイエンススキルを組み合わせ、感染症の地域的パターンを理解することを目指します。

## データソース

### インフルエンザデータ
- **出典**: [北海道感染症情報センター](https://www.iph.pref.hokkaido.jp/kansen/501/data.html)
- **期間**: 2015年～2024年
- **形式**: 週別定点当たり報告数
- **変数**: 報告数、年齢階級別、保健所管内別

### 気象データ
- **出典**: [気象庁 過去の気象データ](https://www.data.jma.go.jp/risk/obsdl/index.php)
- **地点**: 札幌（北海道代表地点）
- **期間**: 2015年～2024年
- **変数**: 気温、湿度、降水量（日別→週次集計）

## 分析手法

### 第1段階：回帰予測

**学習期間**: 2015-2019年（コロナ前ベースライン）
**テスト期間**: 2019-2020年シーズン前半（介入前）

**特徴量**:
- 週番号（季節性）
- ラグ特徴量（1週前、2週前、4週前の患者数）
- 週平均気温
- 週平均湿度
- 学校休暇フラグ

**モデル**:
1. 線形回帰（ベースライン）
2. Ridge / Lasso回帰
3. ランダムフォレスト
4. 勾配ブースティング（XGBoost）

**評価指標**: RMSE

### 第2段階：因果推論（発展課題）

**手法**: 中断時系列分析（Interrupted Time Series Analysis）

2015-2019年で学習したモデルを2020-2024年に適用し、「COVID-19対策がなかった場合」の反事実的な患者数を予測。実測値との差分から抑制効果を推定します。

## プロジェクト構成

```
hokkaido-influenza-prediction/
├── README.md                          # このファイル
├── docs/
│   └── data_acquisition_guide.md      # データ取得手順書
├── data/
│   ├── raw/                           # 生データ（Git管理外）
│   └── processed/                     # 前処理済みデータ
├── notebooks/
│   ├── 01_data_exploration.ipynb      # EDA（探索的データ分析）
│   ├── 02_feature_engineering.ipynb   # 特徴量エンジニアリング
│   ├── 03_model_training.ipynb        # モデル学習・比較
│   └── 04_causal_inference.ipynb      # 第2段階の因果推論分析
├── src/
│   └── influenza_prediction.py        # メイン分析スクリプト
├── outputs/
│   ├── figures/                       # グラフ・可視化
│   └── models/                        # 保存済みモデル
├── requirements.txt                   # Python依存パッケージ
└── .gitignore
```

## 必要環境

- Python 3.8以上
- pandas
- numpy
- scikit-learn
- xgboost
- matplotlib
- seaborn
- jupyter

依存パッケージのインストール:
```bash
pip install -r requirements.txt
```

## 実行手順

1. **データ取得**: [docs/data_acquisition_guide.md](docs/data_acquisition_guide.md)に従ってデータをダウンロード
2. **EDA**: `notebooks/01_data_exploration.ipynb`でデータ理解
3. **特徴量作成**: `notebooks/02_feature_engineering.ipynb`で特徴量を設計
4. **モデル学習**: `notebooks/03_model_training.ipynb`でモデルを比較・評価
5. **分析レポート**: プロセス、考察、結果をまとめる

## 提出物（卒業課題）

- [ ] 分析レポート（PDF/Markdown）
- [ ] Jupyter Notebook（詳細なプロセスと考察付き）
- [ ] 最終予測モデル
- [ ] 結果の可視化

## ライセンス

本プロジェクトは教育目的です。データソースは各提供元のライセンスに従います。
