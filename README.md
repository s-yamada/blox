# blox

YAMLでサイトの構造をブロックとして定義し、資料やHTMLモックアップを出力するCLIツール。
共通のWebサイトの構造から、印刷・配布用資料やHTMLモックアップなど、用途に応じて出力することを目的としています。

## できること

- 1つのYAMLから PowerPoint（A4縦）・HTML（Bootstrap 5 / Tailwind CSS）・Markdown・Word を出力
- ヒーロー・実績数字・CTA・ステップ・グリッド・カラムなどのブロックでページを組み立てる
- PowerPoint のカラーテーマ（6種）・独自テンプレートの利用
- プラグインでブロックの種類を追加

## 動作環境

- Python 3
- python-pptx・python-docx・PyYAML・lxml（`requirements.txt`）

## インストール

```bash
# 依存ライブラリのインストールとコマンド登録（~/.local/bin/blox）
bash install.sh
```

手動で実行する場合:

```bash
pip install -r requirements.txt
python blox.py -f input.yaml -o output.pptx
```

## 使い方

```bash
# PowerPoint 出力（テーマ指定）
blox -f examples/sample.yaml --theme nord -o output.pptx

# HTML 出力（Bootstrap 5 / Tailwind CSS）
blox -f examples/sample.yaml --renderer html_bs -o output/
blox -f examples/sample.yaml --renderer html_tw -o output/

# Markdown・Word 出力
blox -f examples/sample.yaml --renderer markdown -o output.md
blox -f examples/sample.yaml --renderer docx -o output.docx

# ヘルプ
blox --help
```

YAMLの書き方・ブロック一覧・テーマ・テンプレートは [docs/usage.md](docs/usage.md)、
ブロックの追加は [docs/plugin.md](docs/plugin.md) を参照してください。

## 利用条件

[LICENSE](LICENSE) を参照
