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

## 実行方法

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
- テストスクリプトは予約を実行しません（読み取り専用）

## 開発履歴

- 2025-10-27: 初版作成
  - セレクターテスト
  - 14日前チェック機能テスト
  - 判定ロジックテスト

