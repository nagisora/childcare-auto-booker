# テストファイル

このディレクトリには、開発・デバッグ用のテストスクリプトが含まれています。

## テストファイル一覧

### test_final.py
最終的な判定ロジックのテスト。7週分のカレンダーをチェックし、予約可能枠を検出します。

```bash
python tests/test_final.py
```

### test_14days_check.py
14日前チェック機能のテスト。週情報の取得と日付計算を確認します。

```bash
python tests/test_14days_check.py
```

### test_event_date.py
イベントの日時抽出テスト。親要素から日付情報を取得する方法を検証します。

```bash
python tests/test_event_date.py
```

### test_calendar_date.py
カレンダーの日付情報取得テスト。週情報の取得方法を検証します。

```bash
python tests/test_calendar_date.py
```

### test_form_input.py
フォーム入力フローのテスト。予約フォームへの入力から確認画面まで進み、最終送信前に停止します。

- 残0枠でも処理を続行（フォーム入力テストは可能）
- GUI表示モード（headless=False）でブラウザが起動
- WSL環境でのX11フォワーディングに対応
- `.env`ファイルから環境変数を自動読み込み

```bash
# .envファイルを用意する場合（推奨）
cp config/.env.example .env
# .envファイルを編集して必要な設定を入力

# または環境変数を直接設定
export STOP_BEFORE_SUBMIT=true  # 最終送信前に停止（推奨）
export BOOKER_NAME="テスト太郎"
export BOOKER_EMAIL="test@example.com"
export BOOKER_PHONE="09012345678"
export CHILD_NAME="テスト子"
export CHILD_AGE="3"
export SITE_MODE=test  # テストサイトで実行する場合

python tests/test_form_input.py
```

**注意**: このテストスクリプトは確認画面まで進みますが、`STOP_BEFORE_SUBMIT=true`の場合、最終送信は行いません。`.env`ファイルが存在する場合は自動的に読み込まれます。

## 実行方法

### 環境変数の設定

テストスクリプト（特に`test_form_input.py`）は`.env`ファイルから環境変数を読み込みます。

```bash
# .envファイルを作成（初回のみ）
cp config/.env.example .env

# .envファイルを編集
nano .env
```

詳細な設定項目については、`docs/configuration.md`を参照してください。

### 個別実行

```bash
cd /home/junyatamaki/003-dev/childcare-auto-booker
python tests/test_final.py
```

### mise経由での実行

```bash
mise run test-dry-run  # メインシステムのDRY_RUNテスト
```

## 注意事項

- これらのテストスクリプトは実際のAirリザーブサイトにアクセスします
- 過度なアクセスを避けるため、適切な間隔で実行してください
- 読み取り専用のテストスクリプト（`test_final.py`など）は予約を実行しません
- `test_form_input.py`はフォーム入力まで実行しますが、`STOP_BEFORE_SUBMIT=true`の場合は最終送信前に停止します

## 開発履歴

- 2025-10-27: 初版作成
  - セレクターテスト
  - 14日前チェック機能テスト
  - 判定ロジックテスト
- 2025-XX-XX: フォーム入力テスト追加
  - `test_form_input.py`を追加
  - GUI表示モード対応（WSL環境）
  - 残0枠でもフォーム入力テストを実行可能に

