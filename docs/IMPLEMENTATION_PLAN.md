# Airリザーブ自動予約システム実装計画

## 概要

名古屋市の保育施設「子育て応援拠点こころと」のAirリザーブ予約ページ（https://airrsv.net/kokoroto-azukari/calendar）に対して、予約可能枠を自動検知し予約を実行するシステムを構築します。

## 技術スタック

- **OS**: Ubuntu 24.04 LTS対応
- **言語**: Python 3.12（miseで管理）
- **パッケージマネージャ**: mise（バージョン管理）
- **ブラウザ自動化**: Playwright（Chromiumを使用、Ubuntu依存関係を含む）
- **スケジューリング**: 
  - ローカル: schedule ライブラリ
  - クラウド: GitHub Actions (cron)
- **設定管理**: python-dotenv（.env）
- **ログ管理**: logging標準ライブラリ

## プロジェクト構成

```
childcare-auto-booker/
├── .github/
│   └── workflows/
│       └── auto-booking.yml       # GitHub Actions定義
├── src/
│   ├── __init__.py
│   ├── scraper.py                 # Airリザーブページのスクレイピング
│   ├── booker.py                  # 予約実行ロジック
│   ├── notifier.py                # 通知機能（オプション）
│   └── scheduler.py               # スケジューラー
├── docs/
│   ├── research/
│   │   ├── airreserve-analysis.md # Airリザーブの仕様調査
│   │   └── existing-tools.md      # 既存ツール調査結果
│   ├── architecture.md            # システム設計とアーキテクチャ
│   ├── api-flow.md                # 予約フローの詳細解析
│   ├── configuration.md           # 設定項目の詳細説明
│   └── troubleshooting.md         # トラブルシューティングガイド
├── config/
│   └── .env.example               # 環境変数テンプレート
├── logs/                          # ログ出力先（gitignore）
├── .env                           # 実際の設定（gitignore）
├── .gitignore
├── requirements.txt               # Python依存パッケージ
├── README.md                      # プロジェクト説明
├── USAGE.md                       # 使い方ガイド
├── main.py                        # エントリーポイント
└── LICENSE                        # 既存のライセンス
```

## 主要機能

### 1. 予約枠監視（scraper.py）

- **スマート監視**: 予約公開日時の3秒前から監視開始（例: 11/1 9:30公開の場合、9:29:57から監視）
- 公開前後は1秒間隔で継続的にチェック（手作業での順次追加に対応）
- 監視時間は設定可能（デフォルト: 公開後10分間）
- 予約可能な日時を検出（「残○」などの表示を解析）
- 既に予約済みの日時を記録して重複防止
- サーバー負荷を最小限に抑えつつ、新規公開枠を素早く検知

### 2. 自動予約実行（booker.py）

- 検出された予約可能枠に対して予約フローを自動実行
- フォーム入力の自動化（氏名、連絡先など）
- 予約完了の確認とスクリーンショット保存

### 3. 環境変数設定（.env）

```
# 予約者情報
BOOKER_NAME=山田太郎
BOOKER_EMAIL=example@example.com
BOOKER_PHONE=090-1234-5678
CHILD_NAME=山田花子
CHILD_AGE=2

# 予約設定
TARGET_URL=https://airrsv.net/kokoroto-azukari/calendar
NEXT_RELEASE_DATETIME=2024-11-01 09:30:00
MONITOR_DURATION_MINUTES=10
PREFERRED_DAYS=月,水,金
PREFERRED_TIME_START=09:00
PREFERRED_TIME_END=17:00

# 実行モード
DRY_RUN=false  # trueの場合は予約せずに検出のみ
HEADLESS=true  # ブラウザを表示するか
DEBUG=false    # デバッグモード
```

### 4. GitHub Actions設定（auto-booking.yml）

- cron: 毎日9:30に実行（実際の公開日時は月1回なので、その日のみ動作）
- Secretsを使用して環境変数を安全に管理
- 実行結果をArtifactsとして保存（ログ、スクリーンショット）

### 5. ドキュメント

**README.md**:
- プロジェクトの目的と背景
- Airリザーブについての説明
- 既存ツール調査結果
- セットアップ手順
- 使用上の注意（利用規約、倫理的配慮）

**USAGE.md**:
- 詳細なインストール手順
- ローカル実行方法
- GitHub Actions設定方法
- トラブルシューティング

## 実装の優先順位

1. **基本スクレイピング機能**: Playwrightでカレンダーページを読み込み、予約可能枠を検出
2. **予約フロー自動化**: メニュー選択→日時選択→情報入力→確認→予約完了
3. **環境変数管理**: .envファイルでの設定管理と.gitignore設定
4. **ローカル実行**: schedule使用した定期実行スクリプト
5. **ログとエラーハンドリング**: 実行履歴の記録と異常時の対応
6. **GitHub Actions対応**: クラウド自動実行の設定
7. **ドキュメント整備**: README、USAGE、コメント

## 注意事項

- 予約サイトの利用規約を遵守
- 過度なアクセスを避けるため適切な間隔設定
- スクレイピング対策（rate limiting）の実装
- 個人情報保護（.envファイルの厳格な管理）

## 実装状況

### ✅ 完了済み

- [x] プロジェクト構造とgitignore設定
- [x] Playwrightを使用したカレンダースクレイピング機能
- [x] 予約フロー自動化機能の実装
- [x] 環境変数管理と.env.exampleの作成
- [x] ローカル定期実行スクリプト
- [x] GitHub Actionsワークフロー設定
- [x] README.mdとUSAGE.mdの作成
- [x] 詳細ドキュメント（docs/）の作成
- [x] 仮想環境セットアップ対応（2024-12-19）
- [x] 自動セットアップスクリプトの作成
- [x] バグ修正（Pathインポート追加）
- [x] miseとvenvの併用手順の整備
- [x] mise.tomlファイルの作成（自動venv機能対応）
- [x] miseタスクランナー機能の実装
- [x] セットアップスクリプトのmise版への更新
- [x] ドキュメントのmise対応への更新
- [x] 依存関係のインストール完了

### 🔄 次のステップ（次回作業）

#### 1. テスト実行

環境構築が完了したので、次回は実際の動作テストを行います：

```bash
# DRY_RUNモードでテスト実行
mise run test-dry-run
```

#### 2. 動作確認項目

- **スクレイピング機能のテスト**
  - カレンダーページの読み込み確認
  - 予約可能枠の検出確認
  - エラーハンドリングの確認

- **ログ出力の確認**
  - logs/ディレクトリにログファイルが作成されるか
  - エラーメッセージが適切に記録されるか

- **スクリーンショット機能の確認**
  - screenshots/ディレクトリにスクリーンショットが保存されるか

#### 3. 実際の予約ページでの動作確認

```bash
# .envファイルを編集して実際の値を設定
nano .env

# 監視モードでテスト
mise run test-monitor
```

#### 4. ブランチのマージ

動作確認が完了したら、feature/setup-testingブランチをmainにマージ：

```bash
git checkout main
git merge feature/setup-testing
git push origin main
```

#### 5. GitHub Actions設定（オプション）

- Secretsの設定
- ワークフローのテスト実行

#### 6. 本格運用前の最終テスト

- DRY_RUNモードでの動作確認
- ログ出力の確認
- スクリーンショット機能の確認

## 重要な注意事項

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

## 今後の改善計画

### 短期改善
- エラーハンドリングの強化
- ログ機能の改善
- 設定の柔軟性向上

### 中期改善
- AI/ML機能の追加
- 通知機能の拡張
- パフォーマンス最適化

### 長期改善
- マルチサイト対応
- Web UIの提供
- クラウドネイティブ化

---

**作成日**: 2024年12月19日  
**最終更新**: 2024年12月19日（mise完全対応・環境構築完了）  
**ステータス**: 環境構築完了、次回テスト実行予定

## 本日の作業サマリー（2024-12-19）

### 完了した作業
1. ✅ `mise.toml`ファイルの作成（自動venv機能）
2. ✅ miseタスクランナー機能の実装
3. ✅ セットアップスクリプトのmise版への更新
4. ✅ README.md、USAGE.mdのmise対応更新
5. ✅ 依存関係のインストール完了
6. ✅ Playwrightブラウザのインストール完了

### 次回の作業
- DRY_RUNモードでのテスト実行
- スクレイピング機能の動作確認
- ログ出力の確認
- ブランチのマージ

### 環境情報
- Python: 3.12.12 (miseで管理)
- venv: .venv (mise自動作成)
- パッケージ: すべてインストール済み
- Playwright: Chromiumインストール済み
