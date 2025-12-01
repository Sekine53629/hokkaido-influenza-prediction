# 次期プロジェクト計画：influenza-forecast-app

**別リポジトリとして実装する実用Webアプリケーション**

---

## プロジェクト概要

本卒業課題で実証した**Phase D拡張版（媒介分析）の成果**を、60店舗薬局チェーンの実務で活用可能なWebアプリとして実装します。

---

## 新規リポジトリ構成

### リポジトリ名
```
influenza-forecast-app
```

### GitHub URL（予定）
```
https://github.com/YOUR_USERNAME/influenza-forecast-app
```

---

## システム構成

### バックエンド（Heroku）

```
技術スタック:
- Python 3.13
- Flask（API）
- PostgreSQL Mini（$5/月）
- APScheduler（定期実行）

主要機能:
- フェイルセーフデータ収集
  - Twitter API（Free $0 or Basic $100/月）
  - Google Trends（無料）
  - 感染症情報センター（スクレイピング）
- 多段階予報エンジン
  - Level 1: 全データ揃う → 高精度
  - Level 2: 一部障害 → 中精度（フォールバック）
  - Level 3: 全API障害 → 低精度（季節性モデル）
  - Level 4: DB障害 → 緊急モード（固定値）
- API提供（/api/forecast, /api/health）
```

### フロントエンド（Vercel）

```
技術スタック:
- React 18 + TypeScript
- Tailwind CSS
- Chart.js / Recharts
- PWA対応

主要機能:
- バナー表示（コンパクトモード）
  - 2週間後予報
  - アラートレベル（高/中/低）
  - 推奨発注量
- 詳細画面（展開モード）
  - 3週間予報グラフ
  - 恐怖指数・会食指数
  - 媒介分析経路図
  - データソース状態
```

---

## 開発フェーズ

### Phase 1: プロトタイプ（6週間）

**Week 1-2**: バックエンド基盤
- [ ] Herokuプロジェクト作成
- [ ] データベースモデル実装
- [ ] フェイルセーフデータ収集実装

**Week 3-4**: 予報エンジン
- [ ] Phase A XGBoostモデル移植
- [ ] Phase D拡張版媒介モデル移植
- [ ] 多段階フォールバック実装

**Week 5-6**: フロントエンド
- [ ] React PWAセットアップ
- [ ] バナーUI実装
- [ ] 詳細画面実装

### Phase 2: テスト・改善（2週間）

- [ ] 実データでの精度検証
- [ ] UI/UX改善
- [ ] 店長フィードバック収集

### Phase 3: 本番展開（2週間）

- [ ] 60店舗への展開
- [ ] 運用マニュアル作成
- [ ] 監視体制構築

---

## コスト試算

| 項目 | プラン | 月額 |
|---|---|---|
| **Heroku Eco dyno** | Web + Worker | $10 |
| **PostgreSQL Mini** | 10GB | $5 |
| **Twitter API** | Free → Basic（必要なら） | $0-100 |
| **Vercel** | Hobby（無料） | $0 |
| **合計** | | **$15-115/月** |

**推奨**: Twitter Freeでスタート → 精度評価 → 必要ならBasic

---

## ROI計算

### 投資
- 開発: 10週間 × 自分の時間（副業として）
- 運用コスト: $15-115/月

### リターン
- 過剰在庫削減: 年間200万円（推定10%削減）
- 欠品防止: 年間150万円（推定5%機会損失回避）
- **合計**: 年間350万円

**ROI**: 初年度で20-200倍のリターン

---

## 技術的な注意点

### 本卒業課題から移植すべき資産

1. **学習済みモデル**
   - `outputs/models/` のXGBoostモデル
   - Phase D拡張版の媒介モデル係数

2. **季節性パターン**
   - 北海道の週別平均値（フォールバック用）

3. **指数計算ロジック**
   - 恐怖指数の加重平均係数
   - 会食指数の加重平均係数

### 新規開発が必要な部分

1. **フェイルセーフ機構**
   - API障害時の自動フォールバック
   - データソース状態管理

2. **PWA化**
   - Service Worker
   - Manifest.json
   - オフライン対応

3. **通知システム**
   - Slack Webhook統合
   - Web Push通知

---

## セットアップ手順（将来実装時）

### 1. リポジトリ作成

```bash
cd /c/Users/imao3/Documents/GitHub
mkdir influenza-forecast-app
cd influenza-forecast-app

git init
git remote add origin https://github.com/YOUR_USERNAME/influenza-forecast-app.git
```

### 2. Python環境構築

```bash
# pyenvで Python 3.13をインストール
pyenv install 3.13.0
pyenv local 3.13.0

# venv作成
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係インストール
pip install -r requirements.txt
```

### 3. Heroku初期設定

```bash
heroku login
heroku create influenza-forecast-hokkaido
heroku addons:create heroku-postgresql:mini
heroku config:set TWITTER_BEARER_TOKEN=xxx
heroku config:set SLACK_WEBHOOK_URL=xxx
```

### 4. Vercel初期設定

```bash
cd frontend
npm install
npx vercel login
npx vercel --prod
```

---

## 参考リンク

- 本卒業課題: `hokkaido-influenza-prediction/`
- 詳細設計: [docs/bot_system_design.md](bot_system_design.md)
- Phase D拡張版コード: `notebooks/09_mediation_analysis_dining.py`

---

## 次のステップ

1. ✅ 卒業課題提出
2. ⏸ 2-3ヶ月休憩
3. 🚀 新規リポジトリ作成・実装開始

---

**作成日**: 2025年12月1日
**ステータス**: 計画段階（卒業後に実装）
