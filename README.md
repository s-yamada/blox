# blox

Webサイトの構成をYAMLで書き、提案資料やHTMLモックアップを出力するCLIツール。

## Features

- サイトの構成を1つのYAMLで書き、PowerPoint・Word の資料と HTML モックアップを同じ定義から出力できる
- ヒーロー・グリッド・カラムなど、Webサイトでよく使うブロックの組み合わせでページを表す
- 見た目はテーマやテンプレートで差し替えられ、YAMLには内容だけを書けばよい
- 独自のブロックをプラグインとして追加できる

## Requirements

- Python 3
- python-pptx・python-docx・PyYAML・lxml（`requirements.txt`）

## Installation

```bash
# 依存ライブラリのインストールとコマンド登録（~/.local/bin/blox）
bash install.sh
```

手動で実行する場合:

```bash
pip install -r requirements.txt
python blox.py -f input.yaml -o output.pptx
```

## Usage

```bash
# PowerPoint 出力
blox -f examples/sample.yaml -o output.pptx

# HTML 出力（Bootstrap 5）
blox -f examples/sample.yaml --renderer html_bs -o output/
```

コマンドの例・YAMLの書き方・ブロック一覧・テーマ・テンプレートは [docs/usage.md](docs/usage.md)、
ブロックの追加は [docs/plugin.md](docs/plugin.md) を参照してください。

## License

[LICENSE](LICENSE) を参照
