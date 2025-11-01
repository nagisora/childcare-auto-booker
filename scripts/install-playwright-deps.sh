#!/bin/bash
# Playwright依存関係インストールスクリプト（Ubuntu Noble対応）

set -e

echo "Installing Playwright system dependencies..."

# Playwrightが生成するパッケージリストを取得して、libasound2をlibasound2t64に置き換え
playwright install-deps chromium --dry-run 2>/dev/null | \
  sed 's/libasound2/libasound2t64/g' | \
  sudo bash -

echo "✅ Playwright system dependencies installed successfully"

