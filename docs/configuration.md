# 設定項目の詳細説明

## 概要

Airリザーブ自動予約システムの設定項目について詳細に説明します。

## 設定ファイルの構造

### .envファイル

```bash
# 予約者情報（必須）
BOOKER_NAME=山田太郎
BOOKER_NAME_KANA=ヤマダ
BOOKER_NAME_KANA_MEI=タロウ
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

## 設定項目の詳細

### 1. 予約者情報

#### BOOKER_NAME
- **説明**: 予約者（保護者）の氏名
- **形式**: 文字列
- **例**: `山田太郎`
- **注意**: 全角文字でも半角文字でも可

#### BOOKER_NAME_KANA
- **説明**: 予約者（保護者）のフリガナ（姓）
- **形式**: 文字列（カタカナ）
- **例**: `ヤマダ`
- **注意**: カタカナで入力してください

#### BOOKER_NAME_KANA_MEI
- **説明**: 予約者（保護者）のフリガナ（名）
- **形式**: 文字列（カタカナ）
- **例**: `タロウ`
- **注意**: カタカナで入力してください

#### BOOKER_EMAIL
- **説明**: 連絡先メールアドレス
- **形式**: メールアドレス形式
- **例**: `example@example.com`
- **注意**: 有効なメールアドレス形式である必要があります

#### BOOKER_PHONE
- **説明**: 連絡先電話番号
- **形式**: 文字列（9-17桁の半角数字）
- **例**: `090-1234-5678`
- **注意**: ハイフンありなしどちらでも可（システムがハイフンを除去して送信します）

#### CHILD_NAME
- **説明**: お子様の氏名
- **形式**: 文字列
- **例**: `山田花子`
- **注意**: 全角文字でも半角文字でも可

#### CHILD_AGE
- **説明**: お子様の年齢
- **形式**: 数字（文字列）
- **例**: `2`
- **注意**: 0-6歳の範囲で設定してください

### 2. 予約設定

#### TARGET_URL
- **説明**: 予約ページのURL（推奨設定方法）
- **形式**: URL形式
- **例**: `https://airrsv.net/kokoroto-azukari/calendar`（本番サイト）
- **例**: `https://airrsv.net/platkokoro2020/calendar`（テストサイト）
- **注意**: 直接URLを指定する場合はこの環境変数を使用してください。設定されていない場合は`SITE_MODE`で切り替えが可能です

#### SITE_MODE
- **説明**: サイトモード（TARGET_URLが未設定の場合のみ有効）
- **形式**: `production` または `test`
- **例**: `production`（本番サイト、デフォルト）
- **例**: `test`（テストサイト）
- **注意**: `TARGET_URL`が設定されている場合は`TARGET_URL`が優先されます。URL管理を一元化するため、テストと本番の切り替えは`.env`ファイルで行えます

#### NEXT_RELEASE_DATETIME
- **説明**: 次回予約公開日時
- **形式**: `YYYY-MM-DD HH:MM:SS`
- **例**: `2024-11-01 09:30:00`
- **注意**: 正確な日時を設定してください

#### MONITOR_DURATION_MINUTES
- **説明**: 監視時間（分）
- **形式**: 整数
- **例**: `10`
- **推奨**: 5-15分の範囲
- **注意**: 長すぎるとサーバーに負荷をかけます

#### PREFERRED_DAYS
- **説明**: 希望曜日
- **形式**: カンマ区切りの文字列
- **例**: `月,水,金`
- **選択肢**: `月,火,水,木,金,土,日`
- **注意**: 複数指定する場合はカンマで区切ってください

#### PREFERRED_TIME_START
- **説明**: 希望開始時間
- **形式**: `HH:MM`
- **例**: `09:00`
- **注意**: 24時間形式で設定してください

#### PREFERRED_TIME_END
- **説明**: 希望終了時間
- **形式**: `HH:MM`
- **例**: `17:00`
- **注意**: 24時間形式で設定してください

### 3. 実行モード

#### DRY_RUN
- **説明**: テストモードの有効/無効
- **形式**: `true` または `false`
- **例**: `false`
- **効果**: `true`の場合、実際の予約は実行されません

#### HEADLESS
- **説明**: ヘッドレスモードの有効/無効
- **形式**: `true` または `false`
- **例**: `true`
- **効果**: `true`の場合、ブラウザが表示されません

#### DEBUG
- **説明**: デバッグモードの有効/無効
- **形式**: `true` または `false`
- **例**: `false`
- **効果**: `true`の場合、詳細なログが出力されます

### 4. 通知設定

#### NOTIFY_SUCCESS
- **説明**: 予約成功時の通知
- **形式**: `true` または `false`
- **例**: `true`
- **効果**: 予約成功時に通知を送信します

#### NOTIFY_FAILURE
- **説明**: 予約失敗時の通知
- **形式**: `true` または `false`
- **例**: `true`
- **効果**: 予約失敗時に通知を送信します

## 設定の検証

### 必須項目の確認

```python
def validate_required_settings():
    """必須設定項目の検証"""
    required_vars = [
        'BOOKER_NAME',
        'BOOKER_EMAIL', 
        'BOOKER_PHONE',
        'CHILD_NAME',
        'CHILD_AGE',
        'TARGET_URL',
        'NEXT_RELEASE_DATETIME'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {missing_vars}")
```

### 形式の検証

```python
def validate_format():
    """設定値の形式検証"""
    # メールアドレスの検証
    email = os.getenv('BOOKER_EMAIL')
    if email and '@' not in email:
        raise ValueError("Invalid email format")
    
    # 日時の検証
    datetime_str = os.getenv('NEXT_RELEASE_DATETIME')
    if datetime_str:
        try:
            datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            raise ValueError("Invalid datetime format. Use YYYY-MM-DD HH:MM:SS")
    
    # 時間の検証
    time_start = os.getenv('PREFERRED_TIME_START')
    time_end = os.getenv('PREFERRED_TIME_END')
    
    if time_start and time_end:
        try:
            start_time = datetime.strptime(time_start, '%H:%M')
            end_time = datetime.strptime(time_end, '%H:%M')
            
            if start_time >= end_time:
                raise ValueError("Start time must be before end time")
        except ValueError:
            raise ValueError("Invalid time format. Use HH:MM")
```

## 設定の例

### 基本的な設定例

```bash
# 平日の午前中を希望する場合
BOOKER_NAME=山田太郎
BOOKER_EMAIL=yamada@example.com
BOOKER_PHONE=090-1234-5678
CHILD_NAME=山田花子
CHILD_AGE=2
TARGET_URL=https://airrsv.net/kokoroto-azukari/calendar
NEXT_RELEASE_DATETIME=2024-11-01 09:30:00
MONITOR_DURATION_MINUTES=10
PREFERRED_DAYS=月,火,水,木,金
PREFERRED_TIME_START=09:00
PREFERRED_TIME_END=12:00
DRY_RUN=false
HEADLESS=true
DEBUG=false
NOTIFY_SUCCESS=true
NOTIFY_FAILURE=true
```

### テスト用の設定例

```bash
# テスト実行用の設定
BOOKER_NAME=テスト太郎
BOOKER_EMAIL=test@example.com
BOOKER_PHONE=090-0000-0000
CHILD_NAME=テスト花子
CHILD_AGE=2
TARGET_URL=https://airrsv.net/kokoroto-azukari/calendar
NEXT_RELEASE_DATETIME=2024-11-01 09:30:00
MONITOR_DURATION_MINUTES=5
PREFERRED_DAYS=月,水,金
PREFERRED_TIME_START=09:00
PREFERRED_TIME_END=17:00
DRY_RUN=true  # テストモード
HEADLESS=false  # ブラウザを表示
DEBUG=true  # デバッグモード
NOTIFY_SUCCESS=true
NOTIFY_FAILURE=true
```

## GitHub Actions用の設定

### Secretsの設定

GitHubリポジトリの「Settings」→「Secrets and variables」→「Actions」で以下のSecretsを設定：

```
BOOKER_NAME: 山田太郎
BOOKER_EMAIL: yamada@example.com
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

### 環境変数の設定

```yaml
env:
  BOOKER_NAME: ${{ secrets.BOOKER_NAME }}
  BOOKER_EMAIL: ${{ secrets.BOOKER_EMAIL }}
  BOOKER_PHONE: ${{ secrets.BOOKER_PHONE }}
  CHILD_NAME: ${{ secrets.CHILD_NAME }}
  CHILD_AGE: ${{ secrets.CHILD_AGE }}
  TARGET_URL: ${{ secrets.TARGET_URL }}
  NEXT_RELEASE_DATETIME: ${{ secrets.NEXT_RELEASE_DATETIME }}
  MONITOR_DURATION_MINUTES: ${{ secrets.MONITOR_DURATION_MINUTES }}
  PREFERRED_DAYS: ${{ secrets.PREFERRED_DAYS }}
  PREFERRED_TIME_START: ${{ secrets.PREFERRED_TIME_START }}
  PREFERRED_TIME_END: ${{ secrets.PREFERRED_TIME_END }}
  DRY_RUN: ${{ secrets.DRY_RUN }}
  HEADLESS: true
  DEBUG: false
  NOTIFY_SUCCESS: true
  NOTIFY_FAILURE: true
```

## 設定の変更方法

### ローカル環境での変更

```bash
# .envファイルを編集
nano .env

# 設定の確認
python -c "from dotenv import load_dotenv; load_dotenv(); print('BOOKER_NAME:', os.getenv('BOOKER_NAME'))"
```

### GitHub Actionsでの変更

1. リポジトリの「Settings」→「Secrets and variables」→「Actions」
2. 変更したいSecretを選択
3. 「Update」をクリック
4. 新しい値を入力して「Update secret」

## 設定のバックアップ

### ローカル環境

```bash
# 設定ファイルのバックアップ
cp .env .env.backup

# 設定の確認
cat .env
```

### GitHub Actions

- Secretsは自動的にバックアップされます
- 設定変更の履歴は「Actions」タブで確認可能

## トラブルシューティング

### 設定エラーの確認

```bash
# 設定の検証
python -c "
import os
from dotenv import load_dotenv
load_dotenv()

# 必須項目の確認
required = ['BOOKER_NAME', 'BOOKER_EMAIL', 'BOOKER_PHONE', 'CHILD_NAME', 'CHILD_AGE']
missing = [var for var in required if not os.getenv(var)]
if missing:
    print(f'Missing variables: {missing}')
else:
    print('All required variables are set')
"
```

### 設定値の確認

```bash
# 現在の設定値を表示
python -c "
import os
from dotenv import load_dotenv
load_dotenv()

for key in ['BOOKER_NAME', 'BOOKER_EMAIL', 'NEXT_RELEASE_DATETIME']:
    print(f'{key}: {os.getenv(key)}')
"
```

## ベストプラクティス

### 1. セキュリティ

- `.env`ファイルはGitにコミットしない
- 個人情報は適切に管理する
- GitHub ActionsではSecretsを使用する

### 2. 設定管理

- 設定変更時は必ずテスト実行する
- 重要な設定はバックアップを取る
- 設定の変更履歴を記録する

### 3. エラー対応

- 設定エラーは早期に発見する
- ログファイルで設定値を確認する
- デバッグモードで詳細な情報を取得する
