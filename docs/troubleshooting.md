# トラブルシューティングガイド

## 概要

Airリザーブ自動予約システムで発生する可能性のある問題とその解決方法について説明します。

## よくある問題と解決方法

### 1. インストール関連の問題

#### Pythonが見つからない

**症状**:
```
コマンド 'python' が見つかりません
```

**原因**: Pythonがインストールされていない、またはパスが通っていない

**解決方法**:
```bash
# miseでPythonをインストール
mise install python@3.12
mise use python@3.12

# パスを確認
which python
python --version
```

#### Playwrightブラウザのインストールエラー

**症状**:
```
playwright install chromium
Error: Failed to install browsers
```

**原因**: Ubuntu 24.04での依存関係の不足

**解決方法**:
```bash
# システムの依存関係をインストール
sudo apt-get update
sudo apt-get install -y libnss3 libatk-bridge2.0-0 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 libgbm1 libxss1 libasound2

# Playwrightブラウザを再インストール
playwright install chromium
playwright install-deps chromium
```

#### 依存関係のインストールエラー

**症状**:
```
pip install -r requirements.txt
ERROR: Could not find a version that satisfies the requirement
```

**原因**: パッケージのバージョン競合

**解決方法**:
```bash
# 仮想環境を作成
python -m venv venv
source venv/bin/activate

# pipをアップグレード
pip install --upgrade pip

# 依存関係をインストール
pip install -r requirements.txt
```

### 2. 設定関連の問題

#### 環境変数が読み込まれない

**症状**:
```
Missing required environment variables: ['BOOKER_NAME']
```

**原因**: `.env`ファイルが存在しない、または正しく設定されていない

**解決方法**:
```bash
# .envファイルの存在確認
ls -la .env

# テンプレートからコピー
cp config/.env.example .env

# 設定内容の確認
cat .env
```

#### 日時形式エラー

**症状**:
```
Invalid datetime format. Use YYYY-MM-DD HH:MM:SS
```

**原因**: `NEXT_RELEASE_DATETIME`の形式が正しくない

**解決方法**:
```bash
# 正しい形式で設定
NEXT_RELEASE_DATETIME=2024-11-01 09:30:00

# 形式の確認
python -c "
from datetime import datetime
datetime.strptime('2024-11-01 09:30:00', '%Y-%m-%d %H:%M:%S')
print('Format is correct')
"
```

#### メールアドレス形式エラー

**症状**:
```
Invalid email format
```

**原因**: `BOOKER_EMAIL`の形式が正しくない

**解決方法**:
```bash
# 正しいメールアドレス形式で設定
BOOKER_EMAIL=example@example.com

# 形式の確認
python -c "
import re
email = 'example@example.com'
pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
if re.match(pattern, email):
    print('Email format is correct')
else:
    print('Email format is incorrect')
"
```

### 3. 実行関連の問題

#### ページ読み込みエラー

**症状**:
```
Page load timeout
Failed to load page: 404
```

**原因**: ネットワーク接続の問題、またはURLが間違っている

**解決方法**:
```bash
# ネットワーク接続の確認
ping airrsv.net

# URLの確認
curl -I https://airrsv.net/kokoroto-azukari/calendar

# デバッグモードで実行
DEBUG=true python main.py --mode monitor
```

#### ブラウザ起動エラー

**症状**:
```
Browser launch failed
```

**原因**: システムの依存関係不足、または権限の問題

**解決方法**:
```bash
# 依存関係の再インストール
sudo apt-get update
sudo apt-get install -y libnss3 libatk-bridge2.0-0 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 libgbm1 libxss1 libasound2

# Playwrightの再インストール
playwright install chromium
playwright install-deps chromium

# 権限の確認
ls -la ~/.cache/ms-playwright/
```

#### 要素が見つからないエラー

**症状**:
```
Element not found: input[name="booker_name"]
```

**原因**: ページ構造の変更、またはセレクターの間違い

**解決方法**:
```bash
# デバッグモードで実行
DEBUG=true HEADLESS=false python main.py --mode monitor

# スクリーンショットの確認
ls -la screenshots/

# ページのHTMLを確認
python -c "
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto('https://airrsv.net/kokoroto-azukari/calendar')
    print(page.content())
    browser.close()
"
```

### 4. 予約関連の問題

#### フォーム入力エラー

**症状**:
```
Form input failed: Element is not visible
```

**原因**: フォーム要素が表示されていない、または読み込みが完了していない

**解決方法**:
```bash
# 待機時間を増やす
# コード内で wait_for_selector を使用

# デバッグモードで実行
DEBUG=true HEADLESS=false python main.py --mode book
```

#### 予約確認エラー

**症状**:
```
Booking confirmation failed
```

**原因**: 確認ボタンが見つからない、またはクリックできない

**解決方法**:
```bash
# スクリーンショットでページ状態を確認
ls -la screenshots/

# デバッグモードで実行
DEBUG=true HEADLESS=false python main.py --mode book
```

### 5. スケジューラー関連の問題

#### 監視が開始されない

**症状**:
```
Monitoring not started
```

**原因**: 予約公開日時の設定が間違っている、または過去の日時

**解決方法**:
```bash
# 日時の確認
python -c "
from datetime import datetime
release_time = '2024-11-01 09:30:00'
release_datetime = datetime.strptime(release_time, '%Y-%m-%d %H:%M:%S')
now = datetime.now()
print(f'Release time: {release_datetime}')
print(f'Current time: {now}')
print(f'Time difference: {release_datetime - now}')
"

# 正しい日時に設定
NEXT_RELEASE_DATETIME=2024-12-01 09:30:00
```

#### スケジューラーが停止する

**症状**:
```
Scheduler stopped unexpectedly
```

**原因**: エラーによる異常終了

**解決方法**:
```bash
# ログファイルの確認
tail -f logs/auto-booker-$(date +%Y%m%d).log

# エラーログの検索
grep -i error logs/auto-booker-*.log

# デバッグモードで実行
DEBUG=true python main.py --mode schedule
```

### 6. GitHub Actions関連の問題

#### Secretsが設定されていない

**症状**:
```
Missing required environment variables
```

**原因**: GitHub Secretsが設定されていない

**解決方法**:
1. リポジトリの「Settings」→「Secrets and variables」→「Actions」
2. 「New repository secret」をクリック
3. 必要なSecretsを設定

#### ワークフローが実行されない

**症状**:
```
No workflow runs found
```

**原因**: ワークフローファイルの設定ミス、またはcronの設定

**解決方法**:
```bash
# ワークフローファイルの確認
cat .github/workflows/auto-booking.yml

# 手動実行でテスト
# GitHubの「Actions」タブから「Run workflow」をクリック
```

## ログの確認方法

### 1. ログファイルの場所

```bash
# ログディレクトリの確認
ls -la logs/

# 最新のログファイル
ls -lt logs/ | head -5
```

### 2. ログの内容確認

```bash
# 最新のログを表示
tail -f logs/auto-booker-$(date +%Y%m%d).log

# エラーログの検索
grep -i error logs/auto-booker-*.log

# 特定のキーワードで検索
grep -i "booking" logs/auto-booker-*.log
```

### 3. ログレベルの変更

```bash
# デバッグモードで実行
DEBUG=true python main.py --mode monitor

# ログレベルを変更
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
"
```

## デバッグ方法

### 1. デバッグモードの使用

```bash
# デバッグモードで実行
DEBUG=true HEADLESS=false python main.py --mode monitor
```

### 2. スクリーンショットの確認

```bash
# スクリーンショットディレクトリの確認
ls -la screenshots/

# 最新のスクリーンショットを表示
ls -lt screenshots/ | head -5
```

### 3. ページの状態確認

```bash
# ページのHTMLを確認
python -c "
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto('https://airrsv.net/kokoroto-azukari/calendar')
    print(page.title())
    print(page.url)
    browser.close()
"
```

## パフォーマンスの問題

### 1. メモリ使用量の確認

```bash
# メモリ使用量の確認
ps aux | grep python

# メモリ使用量の監視
top -p $(pgrep -f "python main.py")
```

### 2. CPU使用量の確認

```bash
# CPU使用量の確認
htop

# 特定プロセスのCPU使用量
ps -p $(pgrep -f "python main.py") -o pid,ppid,cmd,%cpu,%mem
```

### 3. ディスク使用量の確認

```bash
# ディスク使用量の確認
df -h

# ログファイルのサイズ確認
du -sh logs/
du -sh screenshots/
```

## 緊急時の対応

### 1. プロセスの強制終了

```bash
# Pythonプロセスの確認
ps aux | grep python

# プロセスの強制終了
kill -9 $(pgrep -f "python main.py")
```

### 2. ログファイルのクリア

```bash
# ログファイルのクリア
rm -f logs/auto-booker-*.log

# スクリーンショットのクリア
rm -f screenshots/*
```

### 3. 設定のリセット

```bash
# 設定ファイルのバックアップ
cp .env .env.backup

# デフォルト設定に戻す
cp config/.env.example .env
```

## サポート情報

### 問題報告時の情報

以下の情報を含めてIssueを作成してください：

1. **実行環境**
   - OS: Ubuntu 24.04
   - Python: 3.12
   - Playwright: 1.40.0

2. **エラーメッセージ**
   - 完全なエラーメッセージ
   - スタックトレース

3. **ログファイル**
   - 該当するログファイルの内容
   - エラーが発生した時刻

4. **設定情報**
   - 設定ファイルの内容（個人情報は除く）
   - 実行したコマンド

5. **スクリーンショット**
   - エラー発生時のスクリーンショット
   - ページの状態

### 連絡先

- GitHub Issues: [プロジェクトのIssuesページ](https://github.com/junyatamaki/childcare-auto-booker/issues)
- 緊急時: ログファイルとスクリーンショットを添付してIssueを作成
