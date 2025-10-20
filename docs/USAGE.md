# 使用方法ガイド

Airリザーブ自動予約システムの詳細な使用方法を説明します。

## 目次

1. [インストール手順](#インストール手順)
2. [設定方法](#設定方法)
3. [ローカル実行](#ローカル実行)
4. [GitHub Actions設定](#github-actions設定)
5. [トラブルシューティング](#トラブルシューティング)

## インストール手順

### 1. 前提条件の確認

```bash
# Python 3.12以上がインストールされているか確認
python3 --version

# miseがインストールされているか確認
mise --version
```

### 2. Python環境のセットアップ

```bash
# miseでPython 3.12をインストール
mise install python@3.12
mise use python@3.12

# Pythonのバージョンを確認
python --version
```

### 3. プロジェクトのセットアップ

```bash
# リポジトリをクローン
git clone https://github.com/junyatamaki/childcare-auto-booker.git
cd childcare-auto-booker

# 依存関係をインストール
pip install -r requirements.txt

# Playwrightブラウザをインストール
playwright install chromium
playwright install-deps chromium
```

### 4. 設定ファイルの作成

```bash
# 設定ファイルのテンプレートをコピー
cp config/.env.example .env

# 設定ファイルを編集
nano .env
```

## 設定方法

### .envファイルの設定

```bash
# 予約者情報（必須）
BOOKER_NAME=山田太郎
BOOKER_EMAIL=example@example.com
BOOKER_PHONE=090-1234-5678
CHILD_NAME=山田花子
CHILD_AGE=2

# 予約設定（必須）
TARGET_URL=https://airrsv.net/kokoroto-azukari/calendar
NEXT_RELEASE_DATETIME=2024-11-01 09:30:00
MONITOR_DURATION_MINUTES=10
PREFERRED_DAYS=月,水,金
PREFERRED_TIME_START=09:00
PREFERRED_TIME_END=17:00

# 実行モード（推奨設定）
DRY_RUN=false
HEADLESS=true
DEBUG=false

# 通知設定（オプション）
NOTIFY_SUCCESS=true
NOTIFY_FAILURE=true
```

### 設定項目の詳細説明

#### 予約者情報
- `BOOKER_NAME`: 予約者（保護者）の氏名
- `BOOKER_EMAIL`: 連絡先メールアドレス
- `BOOKER_PHONE`: 連絡先電話番号
- `CHILD_NAME`: お子様の氏名
- `CHILD_AGE`: お子様の年齢（数字のみ）

#### 予約設定
- `TARGET_URL`: 予約ページのURL（通常は変更不要）
- `NEXT_RELEASE_DATETIME`: 次回予約公開日時（YYYY-MM-DD HH:MM:SS形式）
- `MONITOR_DURATION_MINUTES`: 監視時間（分）
- `PREFERRED_DAYS`: 希望曜日（カンマ区切り）
- `PREFERRED_TIME_START`: 希望開始時間（HH:MM形式）
- `PREFERRED_TIME_END`: 希望終了時間（HH:MM形式）

#### 実行モード
- `DRY_RUN`: `true`に設定すると実際の予約は実行されません
- `HEADLESS`: `true`に設定するとブラウザが表示されません
- `DEBUG`: `true`に設定すると詳細なログが出力されます

## ローカル実行

### 1. テスト実行

まず、DRY_RUNモードでテスト実行することを推奨します：

```bash
# DRY_RUNモードで実行
DRY_RUN=true python main.py --mode monitor
```

### 2. 監視モード

予約枠の検出のみを行う場合：

```bash
python main.py --mode monitor
```

### 3. 予約実行モード

検出された枠に対して即座に予約を実行する場合：

```bash
python main.py --mode book
```

### 4. 定期実行モード（推奨）

予約公開日時に基づいて自動実行する場合：

```bash
python main.py --mode schedule
```

## GitHub Actions設定

### 1. リポジトリのSecrets設定

GitHubリポジトリの「Settings」→「Secrets and variables」→「Actions」で以下のSecretsを設定：

```
BOOKER_NAME: 山田太郎
BOOKER_EMAIL: example@example.com
BOOKER_PHONE: 090-1234-5678
CHILD_NAME: 山田花子
CHILD_AGE: 2
TARGET_URL: https://airrsv.net/kokoroto-azukari/calendar
NEXT_RELEASE_DATETIME: 2024-11-01 09:30:00
MONITOR_DURATION_MINUTES: 10
PREFERRED_DAYS: 月,水,金
PREFERRED_TIME_START: 09:00
PREFERRED_TIME_END: 17:00
DRY_RUN: false
```

### 2. ワークフローの実行

- **自動実行**: 毎日9:30に自動実行
- **手動実行**: 「Actions」タブから「Airリザーブ自動予約」を選択して「Run workflow」

### 3. 実行結果の確認

- **ログ**: 「Actions」タブで実行履歴を確認
- **アーティファクト**: ログファイルとスクリーンショットをダウンロード可能

## トラブルシューティング

### よくある問題と解決方法

#### 1. Pythonが見つからない

```bash
# miseでPythonをインストール
mise install python@3.12
mise use python@3.12

# パスを確認
which python
```

#### 2. Playwrightブラウザのエラー

```bash
# ブラウザを再インストール
playwright install chromium
playwright install-deps chromium

# Ubuntuの場合、追加の依存関係が必要な場合があります
sudo apt-get update
sudo apt-get install -y libnss3 libatk-bridge2.0-0 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 libgbm1 libxss1 libasound2
```

#### 3. ページ読み込みエラー

- ネットワーク接続を確認
- 予約ページのURLが正しいか確認
- 一時的にサイトがメンテナンス中でないか確認

#### 4. 予約フォームの入力エラー

- `.env`ファイルの設定が正しいか確認
- 文字エンコーディングの問題がないか確認
- フォームの構造が変更されていないか確認

#### 5. 監視が開始されない

- `NEXT_RELEASE_DATETIME`の設定が正しいか確認
- システム時刻が正確か確認
- ログファイルでエラーメッセージを確認

### ログファイルの確認

```bash
# ログディレクトリの確認
ls -la logs/

# 最新のログファイルを確認
tail -f logs/auto-booker-$(date +%Y%m%d).log

# エラーログの検索
grep -i error logs/auto-booker-*.log
```

### デバッグモードの使用

```bash
# デバッグモードで実行
DEBUG=true python main.py --mode monitor
```

### スクリーンショットの確認

```bash
# スクリーンショットディレクトリの確認
ls -la screenshots/

# 最新のスクリーンショットを確認
ls -lt screenshots/ | head -5
```

## 高度な設定

### カスタム監視間隔

```bash
# 監視間隔を変更（秒）
MONITOR_INTERVAL_SECONDS=2 python main.py --mode monitor
```

### 複数回の予約試行

```bash
# 最大試行回数を設定
MAX_RETRY_COUNT=3 python main.py --mode book
```

### 通知のカスタマイズ

将来的にメール通知やSlack通知を追加予定です。

## サポート

問題が解決しない場合は、以下の情報を含めてIssueを作成してください：

1. 実行環境（OS、Pythonバージョン）
2. エラーメッセージ
3. ログファイルの該当部分
4. 実行したコマンド
5. 設定ファイル（個人情報は除く）
