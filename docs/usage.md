# blox 使い方

YAMLの書き方・ブロック一覧・使用例・カスタマイズ。インストールと基本の使い方は [README](../README.md) を参照。

## コマンドの例

```bash
# PPTX出力
blox -f examples/sample.yaml -o output.pptx

# テーマを指定（CLI指定が YAML の theme: より優先）
blox -f examples/sample.yaml --theme nord -o output.pptx

# Bootstrap 5 HTML出力
blox -f examples/sample.yaml --renderer html_bs -o output/

# Tailwind CSS HTML出力（Play CDN、ビルド不要）
blox -f examples/sample.yaml --renderer html_tw -o output/

# Markdown出力
blox -f examples/sample.yaml --renderer markdown -o output.md

# Word (.docx) 出力
blox -f examples/sample.yaml --renderer docx -o output.docx

# 独自PPTXテンプレートを使用
blox -f input.yaml --template corporate.pptx -o output.pptx

# ページ内通し番号を付与（①タイトル 形式）
blox -f examples/sample.yaml -n -o output.pptx

# 標準入力からYAMLを受け取る（タブ展開などと組み合わせ可）
expand -8 input.yaml | blox --renderer html_bs -o output/

# ヘルプ
blox --help
```

## YAMLの書き方

```yaml
title: "サイトタイトル"   # HTML: グロナビ・index.html のタイトル / PPTX: 表紙タイトル
author: "著者名"          # PPTX: 表紙に表示 / HTML: 無視
theme: navy               # PPTX配色テーマ（省略時は gray）。--theme オプションで上書き可

pages:
  - title: "ページタイトル"    # ページ番号は順番から自動採番
    name: "short-slug"         # 省略可。HTMLファイル名用スラッグ
    nav: true                  # 省略可。グロナビに掲載する場合に指定
    nav_label: "短い名前"      # 省略可。グロナビのラベル（省略時は name → title）
    blocks:
      - type: hero
        h_mm: 55
        image_label: "メインビジュアル"
        caption: "キャッチコピー"

      - type: cta
        text: "お問い合わせはこちら"
```

### ブロック一覧

**スタンドアロンブロック**

| type | 概要 | 主なパラメータ |
|------|------|--------------|
| `hero` | 全幅画像プレースホルダー | `h_mm`, `image_label`, `caption` |
| `stats` | 実績数字バナー（横並び） | `h_mm`, `items: [{num, label}]` |
| `cta` | CTAバナー（全幅） | `h_mm`, `text` |
| `steps` | ステップ図（横並び） | `h_mm`, `items: [{num, title, text}]` |

**レイアウトブロック**

| type | 概要 | 主なパラメータ |
|------|------|--------------|
| `grid` | 同種セルの均等グリッド | `kind`, `cols`, `item_h_mm`, `items: [...]` |
| `col` | 異種セルの横並び | `cols`（総カラム数）, `h_mm`, `cells: [{kind, span, ...}]` |

**セルの kind**（`grid` / `col` 共通）

| kind | 用途 | 主なパラメータ |
|------|------|--------------|
| `card` | 画像＋タイトル＋テキスト | `image_label`, `title`, `text` |
| `img` | 画像プレースホルダー | `image_label` |
| `text` | タイトル＋本文 | `title`, `text` |
| `list` | 箇条書き | `title`（省略可）, `list_type: ul\|ol\|dl`, `items: [...]` |
| `table` | テーブル | `title`（省略可）, `headers: [...]`（省略可）, `items: [[...], ...]` |
| `form` | フォーム（管理画面モックアップ向け） | `items: [{label, type, ...}]` |

`h_mm` は高さをミリメートルで指定します（HTML出力では無視されます）。

### 使用例

```yaml
# カードグリッド（3列）
- type: grid
  kind: card
  cols: 3
  item_h_mm: 60
  items:
    - image_label: "写真"
      title: "製品A"
      text: "説明文"

# 2カラム（画像左＋テキスト右）
- type: col
  cols: 12
  h_mm: 50
  cells:
    - kind: img
      span: 5
      image_label: "写真"
    - kind: text
      span: 7
      title: "見出し"
      text: "本文テキスト"

# サイドバー付きテキスト
- type: col
  cols: 12
  h_mm: 60
  cells:
    - kind: text
      span: 8
      title: "概要"
      text: "本文"
    - kind: list
      span: 4
      list_type: ul
      items:
        - "仕様1"
        - "仕様2"

# rows: で行単位に分割（ページまたぎ対応・PPTX自動分割）
- type: col
  cols: 12
  title: "会社沿革"
  rows:
    - cells:
        - kind: text
          span: 2
          text: "2000年"
        - kind: text
          span: 10
          text: "会社設立"
    - cells:
        - kind: text
          span: 2
          text: "2010年"
        - kind: text
          span: 10
          text: "東京支社開設"

# テーブル（ヘッダーあり）
- type: col
  cols: 12
  h_mm: 50
  cells:
    - kind: table
      span: 12
      headers: ["カテゴリ", "タイトル", "日付"]
      items:
        - ["お知らせ", "新製品を発売しました", "2024-06-01"]
        - ["イベント", "展示会出展のご案内", "2024-05-15"]

# フォーム（管理画面モックアップ）
- type: col
  cols: 12
  h_mm: 100
  cells:
    - kind: form
      span: 8
      items:
        - label: "会社名"
          type: text
          placeholder: "株式会社〇〇"
        - label: "種別"
          type: select
          options: ["製品について", "サービスについて"]
        - label: "同意する"
          type: checkbox
          text: "プライバシーポリシーに同意します"
        - label: "送信する"
          type: submit
```

**form で使える type**

| type | 概要 | 追加パラメータ |
|------|------|--------------|
| `text` / `email` / `tel` / `password` | 1行テキスト入力 | `placeholder` |
| `file` | ファイル選択入力 | — |
| `textarea` | 複数行テキスト入力 | — |
| `select` | プルダウン | `options: [...]` |
| `checkbox` | チェックボックス | `text:` で表示文言 |
| `radio` | ラジオボタン | `options: [...]` |
| `submit` | 送信ボタン（primary固定） | — |
| `button` | 任意色の単ボタン | `color: primary\|secondary\|danger\|...` |
| `buttons` | 横並びボタン群（OK/Cancelなど） | `items: [{label, color}]` |
| `label` | 値表示のみ（確認画面向け） | `value:` で表示内容 |

```yaml
# 確認画面の例
- kind: form
  span: 8
  items:
    - label: "会社名"
      type: label
      value: "株式会社〇〇"
    - label: "お名前"
      type: label
      value: "山田 太郎"
    - type: buttons
      items:
        - label: "送信する"
          color: primary
        - label: "戻る"
          color: secondary
```

---

## カスタマイズ

### PPTXテーマ

`--theme` オプションまたは YAML の `theme:` フィールドで指定します（CLI が優先、省略時は `gray`）。

```bash
blox -f input.yaml --theme nord -o output.pptx
```

| テーマ名 | 概要 |
|---------|------|
| `gray` | グレースケール（デフォルト）。配色を主張しないワイヤーフレーム向け |
| `navy` | ネイビー系ブルー |
| `warm` | テラコッタ・ベージュ系。飲食・ライフスタイル向け |
| `green` | フォレストグリーン系。環境・医療・農業向け |
| `solarized` | Solarized Light（Ethan Schoonover） |
| `nord` | Nord（Arctic Ice Studio）。北欧系ブルー |

独自テーマは `themes/<name>.py` を作成して `THEME` 辞書を定義するだけで使えます。

```python
# themes/mycompany.py
from pptx.dml.color import RGBColor
THEME = {
    'navy': RGBColor(0x00, 0x33, 0x66),
    # ... 他のキーも定義
}
```

```bash
blox -f input.yaml --theme mycompany -o output.pptx
```

### PPTXテンプレート

`--template` オプションで独自の `.pptx` ファイルをテンプレートとして指定できます。

```bash
blox -f input.yaml --template examples/template_corporate.pptx -o output.pptx
```

省略時は python-pptx のデフォルトテンプレートが使われます。

テンプレートが有効な用途はスライドマスターに配置した **ロゴ・フッターライン・背景色** など固定装飾の追加です。blox は全シェイプに色を直接指定するため、テンプレート側のカラーテーマは反映されません。配色を変えたい場合は `--theme` オプションまたは `themes/` への独自テーマ追加を使ってください。

### フォントの変更

`pptx_styles.py` の `FONT` を変更します。

```python
FONT = 'Meiryo UI'
```

ブロックの追加（プラグイン）は [plugin.md](plugin.md) を参照。

## ファイル構成

| ファイル | 役割 |
|---------|------|
| `blox.py` | エントリーポイント |
| `install.sh` | インストーラ（~/.local/share/blox/ にコピー後、~/.local/bin/blox にシンボリックリンクを作成） |
| `renderers/pptx.py` | PPTXブロック描画 |
| `renderers/html_bootstrap.py` | Bootstrap 5 HTML生成 |
| `renderers/html_tailwind.py` | Tailwind CSS HTML生成 |
| `renderers/markdown.py` | Markdown生成 |
| `renderers/docx.py` | Word (.docx) 生成 |
| `renderers/pptx_styles.py` | PPTXレイアウト定数（寸法・フォントサイズ） |
| `themes/__init__.py` | PPTXカラーテーマローダー |
| `themes/<name>.py` | PPTXカラーテーマ定義（gray/navy/warm/green/solarized/nord） |
| `examples/` | サンプルYAMLファイル群 |
