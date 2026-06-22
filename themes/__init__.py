"""
blox - PPTXカラーテーマローダー

テーマファイル: themes/<name>.py に THEME 辞書を定義する。
独自テーマは themes/ 配下に同名ファイルを作成し、YAML で theme: <name> と指定する。
"""
import sys
import importlib

# アクティブなカラーパレット（renderers/pptx.py が from themes import C で参照）
C: dict = {}

# シェイプのドロップシャドウ有効フラグ（デフォルト: 無効）
shadow: bool = False


def apply_theme(name='gray'):
    try:
        mod = importlib.import_module(f'themes.{name}')
    except ModuleNotFoundError:
        print(f'警告: テーマ "{name}" が見つかりません、gray を使用します', file=sys.stderr)
        mod = importlib.import_module('themes.gray')
    C.clear()
    C.update(mod.THEME)


apply_theme('gray')  # デフォルト初期化
