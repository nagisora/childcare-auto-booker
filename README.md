# Airリザーブ自動予約システム

保育施設の一時預かり予約を自動化するPythonプログラムです。

## 概要

このプロジェクトは、[Airリザーブ](https://airregi.jp/reserve/)で作成された保育施設「子育て応援拠点こころと（一時預かり）」の予約ページに対して、予約可能枠を自動検知し予約を実行するシステムです。

### 対象サイト
- **URL**: https://airrsv.net/kokoroto-azukari/calendar
- **施設名**: 子育て応援拠点こころと（一時預かり）
- **所在地**: 愛知県名古屋市昭和区雪見町2-14

## 主な機能

### 🔍 スマート監視
- 予約公開日時の3秒前から監視開始
- 公開前後は1秒間隔で継続的にチェック
- 手作業での順次追加に対応

### 🤖 自動予約
- 検出された予約可能枠に対して自動で予約実行
- フォーム入力の自動化（氏名、連絡先など）
- 希望条件に基づく枠の優先選択

### 📊 ログ・通知
- 実行履歴の詳細ログ
- 予約成功・失敗の通知
- スクリーンショット自動保存

### ☁️ クラウド対応
- GitHub Actionsでの自動実行
- ローカル実行もサポート

## 技術スタック

- **OS**: Ubuntu 24.04 LTS対応
- **言語**: Python 3.12
- **ブラウザ自動化**: Playwright
- **スケジューリング**: schedule ライブラリ / GitHub Actions
- **設定管理**: python-dotenv

## 既存ツール調査結果

現時点で、**Airリザーブ専用の既存自動予約プログラムは公開されていません**。一般的な予約サイト向けの自動化ツールは存在しますが、Airリザーブの予約フローに特化したオープンソースプロジェクトは見当たりませんでした。

そのため、このプロジェクトが有用なものになる可能性があります。

## セットアップ

### 前提条件

- Python 3.12以上
- Ubuntu 24.04 LTS（推奨）
- mise（バージョン管理ツール）

### インストール手順

1. **Python環境のセットアップ**
   ```bash
   # miseでPythonをインストール
   mise install python@3.12
   mise use python@3.12
   ```

2. **リポジトリのクローン**
   ```bash
   git clone https://github.com/junyatamaki/childcare-auto-booker.git
   cd childcare-auto-booker
   ```

3. **mise自動venv機能の活用（推奨）**
   ```bash
   # miseでPython環境をセットアップ（自動でvenvも作成される）
   mise install
   
   # 依存関係をインストール
   mise run prerequisites
   
   # Playwrightブラウザをインストール
   mise run setup-playwright
   ```

4. **設定ファイルの作成**
   ```bash
   cp config/.env.example .env
   # .envファイルを編集して予約者情報を設定
   ```

**または、自動セットアップスクリプトを使用：**
```bash
./scripts/setup.sh
```

## 使用方法

詳細な使用方法は [USAGE.md](docs/USAGE.md) を参照してください。

### 基本的な使用方法

```bash
# 監視モード（予約枠の検出のみ）
python main.py --mode monitor

# 予約実行モード
python main.py --mode book

# 定期実行モード（推奨）
python main.py --mode schedule
```

## 設定項目

### 予約者情報
- `BOOKER_NAME`: 予約者氏名
- `BOOKER_EMAIL`: メールアドレス
- `BOOKER_PHONE`: 電話番号
- `CHILD_NAME`: お子様の名前
- `CHILD_AGE`: お子様の年齢

### 予約設定
- `TARGET_URL`: 予約ページのURL
- `NEXT_RELEASE_DATETIME`: 次回予約公開日時
- `MONITOR_DURATION_MINUTES`: 監視時間（分）
- `PREFERRED_DAYS`: 希望曜日
- `PREFERRED_TIME_START`: 希望開始時間
- `PREFERRED_TIME_END`: 希望終了時間

### 実行モード
- `DRY_RUN`: テストモード（実際の予約は実行しない）
- `HEADLESS`: ヘッドレスモード（ブラウザを表示しない）
- `DEBUG`: デバッグモード

### テスト・安全設定
- `STOP_BEFORE_SUBMIT`: 最終送信ボタンを押さずに停止（テスト用、デフォルト: `true`）
- `REQUIRE_MANUAL_CONFIRMATION`: 送信前に手動確認を求める

## 注意事項

### ⚠️ 利用規約の遵守
- 予約サイトの利用規約を必ず確認し遵守してください
- 過度なアクセスを避けるため適切な間隔設定を行ってください
- 個人情報保護のため.envファイルの管理を厳格に行ってください

### 🔒 セキュリティ
- `.env`ファイルはGitにコミットしないでください
- GitHub Actionsを使用する場合は、Secretsで環境変数を管理してください
- 個人情報の取り扱いには十分注意してください

### 📝 倫理的配慮
- このツールは個人の利便性向上を目的としています
- 他の利用者への配慮を忘れずに使用してください
- システムに過度な負荷をかけないよう注意してください

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。詳細は [LICENSE](LICENSE) ファイルを参照してください。

## 開発者向け情報

このプロジェクトを開発・拡張する際は、`docs`フォルダ内のドキュメントを参照してください。これらのドキュメントには、システムの設計思想、実装の詳細、トラブルシューティング情報などが含まれています。

### 主要なドキュメント

#### 実装に直接必要なドキュメント（優先度高）

- **[airreserve-structure.md](docs/airreserve-structure.md)**: Airリザーブの構造情報とスクレイピングに必要な情報
  - セレクター情報（`.dataLinkBox.js-dataLinkBox`, `.ctlListItem.listNext`など）
  - 予約可能枠の判定ロジック（「残0」「満員」などのキーワード）
  - テストサイトと本番サイトの違い
  - **コード変更時は必ず参照**
  
- **[configuration.md](docs/configuration.md)**: 設定項目の詳細説明と検証方法
  - 環境変数の仕様とデフォルト値
  - 設定の検証ロジック
  - **設定関連の変更時は必ず参照**

- **[troubleshooting.md](docs/troubleshooting.md)**: よくある問題と解決方法
  - デバッグ手順
  - エラー解決方法
  - **問題発生時は最初に参照**

#### 設計理解に役立つドキュメント（優先度中）

- **[architecture.md](docs/architecture.md)**: システム設計とアーキテクチャの詳細説明
  - コンポーネント構成（`AirReserveScraper`, `AirReserveBooker`, `Scheduler`など）
  - データフロー
  - **システム全体の理解に有用**

- **[api-flow.md](docs/api-flow.md)**: 予約フローの詳細解析と自動化のポイント
  - 予約フローの各ステップ
  - エラーハンドリングの考え方
  - **予約処理の実装時に参考**

#### 使用方法のドキュメント

- **[USAGE.md](docs/USAGE.md)**: 詳細な使用方法
  - セットアップ手順
  - 実行方法
  - **ユーザー向けドキュメント**

### AI開発者への注意

AI開発ツールを使用してコードを変更・拡張する場合は、**必ず以下のドキュメントを優先的に参照**してください：

1. **コード変更時**: `airreserve-structure.md`を参照し、セレクターや判定ロジックが実装と一致しているか確認
2. **設定変更時**: `configuration.md`を参照し、環境変数の仕様と検証ロジックを確認
3. **エラー発生時**: `troubleshooting.md`を参照し、既知の問題や解決方法を確認
4. **設計変更時**: `architecture.md`と`api-flow.md`を参照し、設計思想を理解してから変更

これらのドキュメントに記載されている実装詳細や設計方針に沿って開発を進めることで、一貫性のあるコードベースを維持できます。

## 貢献

プルリクエストやイシューの報告を歓迎します。詳細は [CONTRIBUTING.md](CONTRIBUTING.md) を参照してください。

## サポート

問題が発生した場合は、[Issues](https://github.com/junyatamaki/childcare-auto-booker/issues) で報告してください。

## 更新履歴

- v1.0.0: 初回リリース
  - Airリザーブ予約ページの自動監視機能
  - 自動予約実行機能
  - GitHub Actions対応
  - ローカル実行対応
