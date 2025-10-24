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

3. **仮想環境のセットアップ（推奨）**
   ```bash
   # 仮想環境を作成
   python -m venv .venv
   
   # 仮想環境を有効化
   source .venv/bin/activate
   ```

4. **依存関係のインストール**
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

5. **設定ファイルの作成**
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
