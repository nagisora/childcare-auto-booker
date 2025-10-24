#!/bin/bash
# Airリザーブ自動予約システム - 初回セットアップスクリプト

set -e  # エラー時に停止

echo "🚀 Airリザーブ自動予約システムのセットアップを開始します..."

# プロジェクトルートに移動
cd "$(dirname "$0")/.."

# miseでPython 3.12をインストール・使用
echo "📦 Python 3.12をセットアップ中..."
if command -v mise &> /dev/null; then
    mise install python@3.12
    mise use python@3.12
    echo "✅ miseでPython 3.12をセットアップしました"
else
    echo "⚠️  miseがインストールされていません。手動でPython 3.12をインストールしてください。"
    echo "   https://mise.jdx.dev/ を参照してください。"
fi

# 仮想環境を作成
echo "🔧 仮想環境を作成中..."
if [ ! -d ".venv" ]; then
    python -m venv .venv
    echo "✅ 仮想環境を作成しました"
else
    echo "ℹ️  仮想環境は既に存在します"
fi

# 仮想環境を有効化
echo "🔌 仮想環境を有効化中..."
source .venv/bin/activate

# 依存関係をインストール
echo "📚 依存関係をインストール中..."
pip install --upgrade pip
pip install -r requirements.txt

# Playwrightブラウザをインストール
echo "🌐 Playwrightブラウザをインストール中..."
playwright install chromium
playwright install-deps chromium

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
echo "2. DRY_RUN=true python main.py --mode monitor でテスト実行"
echo ""
echo "仮想環境の有効化:"
echo "  source .venv/bin/activate"
echo ""
echo "仮想環境の無効化:"
echo "  deactivate"
