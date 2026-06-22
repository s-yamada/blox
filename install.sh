#!/bin/bash
# blox インストーラ
# ファイルを ~/.local/share/blox/ にコピーし、~/.local/bin/blox へシンボリックリンクを作成します

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="$HOME/.local/share/blox"
TARGET="$HOME/.local/bin/blox"

# 依存ライブラリをインストール
echo "依存ライブラリをインストールしています..."
pip install -r "$SCRIPT_DIR/requirements.txt" -q

# インストール先にファイルをコピー
echo "ファイルをコピーしています: $INSTALL_DIR"
mkdir -p "$INSTALL_DIR"
cp "$SCRIPT_DIR/blox.py"          "$INSTALL_DIR/"
cp "$SCRIPT_DIR/requirements.txt" "$INSTALL_DIR/"
cp -r "$SCRIPT_DIR/renderers"     "$INSTALL_DIR/"
cp -r "$SCRIPT_DIR/themes"        "$INSTALL_DIR/"
[ -d "$SCRIPT_DIR/plugins" ] && cp -r "$SCRIPT_DIR/plugins" "$INSTALL_DIR/"

# blox.py を実行可能にする
chmod +x "$INSTALL_DIR/blox.py"

# シンボリックリンクを作成
mkdir -p "$HOME/.local/bin"
ln -sf "$INSTALL_DIR/blox.py" "$TARGET"

echo "インストール完了: $TARGET -> $INSTALL_DIR/blox.py"

# PATH チェック
if ! echo "$PATH" | tr ':' '\n' | grep -q "$HOME/.local/bin"; then
    echo ""
    echo "⚠️  ~/.local/bin が PATH に含まれていません。"
    echo "   以下を ~/.zshrc または ~/.bashrc に追加してください:"
    echo '   export PATH="$HOME/.local/bin:$PATH"'
fi
