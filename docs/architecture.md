# システム設計とアーキテクチャ

## 概要

Airリザーブ自動予約システムのシステム設計とアーキテクチャについて説明します。

## システム構成図

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   スケジューラー   │    │    スクレイパー    │    │    ブッカー      │
│                 │    │                 │    │                 │
│ - 実行タイミング  │───▶│ - ページ監視     │───▶│ - 予約実行      │
│ - ジョブ管理     │    │ - 枠検出        │    │ - フォーム入力   │
│ - エラーハンドリング│    │ - スクリーンショット│    │ - 確認・完了    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   通知マネージャー  │    │    設定管理      │    │    ログ管理      │
│                 │    │                 │    │                 │
│ - 成功通知      │    │ - 環境変数      │    │ - 実行ログ      │
│ - 失敗通知      │    │ - 設定検証      │    │ - エラーログ    │
│ - 検出通知      │    │ - デフォルト値   │    │ - デバッグログ   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## コンポーネント詳細

### 1. スケジューラー (Scheduler)

**責任**:
- 予約公開日時の管理
- 監視ジョブの実行制御
- エラーハンドリング

**主要クラス**:
- `Scheduler`: メインスケジューラー
- `Thread`: 非同期実行管理

**設計パターン**:
- Observer Pattern: 通知システムとの連携
- Strategy Pattern: 実行モードの切り替え

### 2. スクレイパー (Scraper)

**責任**:
- Airリザーブページの監視
- 予約可能枠の検出
- ページ状態の管理

**主要クラス**:
- `AirReserveScraper`: メインスクレイパー
- `async_playwright`: ブラウザ自動化

**設計パターン**:
- Context Manager: リソース管理
- Template Method: スクレイピング処理の統一

### 3. ブッカー (Booker)

**責任**:
- 予約フローの自動実行
- フォーム入力の自動化
- 予約完了の確認

**主要クラス**:
- `AirReserveBooker`: メインブッカー

**設計パターン**:
- Chain of Responsibility: フォーム入力処理
- State Pattern: 予約状態の管理

### 4. 通知マネージャー (Notifier)

**責任**:
- 各種通知の管理
- 通知設定の制御

**主要クラス**:
- `NotificationManager`: 通知管理

**設計パターン**:
- Observer Pattern: イベント通知

## データフロー

### 1. 監視フロー

```
開始 → ブラウザ起動 → ページ読み込み → 枠検出 → 新規枠判定 → 通知
```

### 2. 予約フロー

```
枠検出 → 希望条件判定 → 予約ページ移動 → フォーム入力 → 確認 → 完了
```

### 3. エラーフロー

```
エラー発生 → ログ記録 → 通知 → リトライ判定 → 継続/終了
```

## 設定管理

### 環境変数構造

```python
# 予約者情報
BOOKER_NAME: str
BOOKER_EMAIL: str
BOOKER_PHONE: str
CHILD_NAME: str
CHILD_AGE: str

# 予約設定
TARGET_URL: str
NEXT_RELEASE_DATETIME: str
MONITOR_DURATION_MINUTES: int
PREFERRED_DAYS: List[str]
PREFERRED_TIME_START: str
PREFERRED_TIME_END: str

# 実行モード
DRY_RUN: bool
HEADLESS: bool
DEBUG: bool

# 通知設定
NOTIFY_SUCCESS: bool
NOTIFY_FAILURE: bool
```

### 設定検証

```python
def validate_config():
    """設定値の検証"""
    required_vars = [
        'BOOKER_NAME', 'BOOKER_EMAIL', 'BOOKER_PHONE',
        'CHILD_NAME', 'CHILD_AGE', 'TARGET_URL',
        'NEXT_RELEASE_DATETIME'
    ]
    
    for var in required_vars:
        if not os.getenv(var):
            raise ValueError(f"Required environment variable {var} is not set")
```

## エラーハンドリング

### エラー分類

1. **ネットワークエラー**
   - 接続タイムアウト
   - DNS解決失敗
   - SSL証明書エラー

2. **ページ構造エラー**
   - 要素が見つからない
   - セレクターの変更
   - JavaScript実行エラー

3. **予約エラー**
   - フォーム入力エラー
   - バリデーションエラー
   - システムエラー

4. **設定エラー**
   - 環境変数の不備
   - 日時形式エラー
   - 値の範囲外

### エラー処理戦略

```python
async def handle_error(error: Exception, context: str):
    """エラーハンドリングの統一処理"""
    logger.error(f"Error in {context}: {error}")
    
    if isinstance(error, TimeoutError):
        # タイムアウトエラーの処理
        await retry_with_backoff()
    elif isinstance(error, ElementNotFoundError):
        # 要素が見つからない場合の処理
        await take_screenshot()
        await notify_error(error)
    else:
        # その他のエラー
        await log_error(error)
        await notify_error(error)
```

## パフォーマンス考慮

### 1. メモリ使用量

- ブラウザインスタンスの適切な管理
- ページオブジェクトの適時解放
- ログファイルのローテーション

### 2. CPU使用量

- 非同期処理の活用
- 適切な待機時間の設定
- 不要な処理の削減

### 3. ネットワーク使用量

- 効率的なページ読み込み
- 不要なリクエストの削減
- レート制限の遵守

## セキュリティ考慮

### 1. 認証情報の保護

- 環境変数での管理
- .envファイルのgitignore
- GitHub Secretsの活用

### 2. ネットワークセキュリティ

- HTTPS通信の強制
- SSL証明書の検証
- プロキシ設定の対応

### 3. データ保護

- 個人情報の暗号化
- ログからの個人情報除外
- スクリーンショットの適切な管理

## 拡張性考慮

### 1. プラグインアーキテクチャ

```python
class BookingPlugin:
    """予約プラグインのベースクラス"""
    
    async def execute_booking(self, slot_info: Dict, page: Page) -> bool:
        """予約実行の抽象メソッド"""
        raise NotImplementedError
```

### 2. 設定の動的変更

- 実行時の設定変更
- ホットリロード機能
- 設定のバリデーション

### 3. マルチサイト対応

- サイト固有の設定
- プラグインシステム
- 共通インターフェース

## 監視・運用

### 1. ヘルスチェック

```python
async def health_check():
    """システムの健全性チェック"""
    checks = [
        check_browser_status(),
        check_network_connectivity(),
        check_config_validity(),
        check_disk_space()
    ]
    
    results = await asyncio.gather(*checks, return_exceptions=True)
    return all(isinstance(r, bool) and r for r in results)
```

### 2. メトリクス収集

- 予約成功率
- 平均応答時間
- エラー発生率
- リソース使用量

### 3. アラート設定

- エラー率の閾値
- リソース使用量の閾値
- 予約失敗の通知

## 今後の改善計画

### 1. 短期改善

- エラーハンドリングの強化
- ログ機能の改善
- 設定の柔軟性向上

### 2. 中期改善

- AI/ML機能の追加
- 通知機能の拡張
- パフォーマンス最適化

### 3. 長期改善

- マルチサイト対応
- Web UIの提供
- クラウドネイティブ化
