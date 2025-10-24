#!/bin/bash
# Airリザーブ自動予約システム - 初回セットアップスクリプト（mise版）

set -e  # エラー時に停止

echo "🚀 Airリザーブ自動予約システムのセットアップを開始します..."

# プロジェクトルートに移動
cd "$(dirname "$0")/.."

# miseでPythonとvenvをセットアップ
echo "📦 miseでPython環境をセットアップ中..."
if command -v mise &> /dev/null; then
    mise install
    echo "✅ miseでPython環境をセットアップしました"
else
    echo "⚠️  miseがインストールされていません。手動でmiseをインストールしてください。"
    echo "   https://mise.jdx.dev/ を参照してください。"
    exit 1
fi

# 依存関係をインストール
echo "📚 依存関係をインストール中..."
mise run prerequisites

# Playwrightブラウザをインストール
echo "🌐 Playwrightブラウザをインストール中..."
mise run setup-playwright

# 設定ファイルを作成
echo "⚙️  設定ファイルを作成中..."
if [ ! -f ".env" ]; then
    cp config/.env.example .env
    echo "✅ .envファイルを作成しました"
    echo "⚠️  .envファイルを編集して実際の値を設定してください"
else
    echo "ℹ️  .envファイルは既に存在します"
fi

# ログディレクトリを作成
echo "📁 必要なディレクトリを作成中..."
mkdir -p logs screenshots

echo ""
echo "🎉 セットアップが完了しました！"
echo ""
echo "次のステップ:"
echo "1. .envファイルを編集して実際の値を設定"
echo "2. mise run test-dry-run でテスト実行"
echo ""
echo "利用可能なmiseタスク:"
echo "  mise run prerequisites  # 依存関係インストール"
echo "  mise run setup-playwright  # Playwrightブラウザインストール"
echo "  mise run test-dry-run  # DRY_RUNモードでテスト"
echo "  mise run test-monitor  # 監視モード実行"
