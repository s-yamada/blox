# ブロックの追加（プラグイン）

`plugins/` ディレクトリに Python ファイルを置くだけで新しいブロック種別を追加できます。  
既存コードの変更は不要です。

```python
# plugins/banner.py
def block_banner_html_bs(block):
    text  = block.get('text', '')
    color = block.get('color', 'primary')
    return f'<section class="alert alert-{color} mb-3">{text}</section>'

def block_banner_md(block):
    return f'> **{block.get("text", "")}**\n'

# block_banner_html_tw(block), block_banner_pptx(slide, y, block) なども同様に定義可（任意）
```

**命名規則：** `block_{type}_{suffix}` の関数を定義するだけで自動登録されます。

| suffix | 対象レンダラー | シグネチャ |
|--------|--------------|----------|
| `_html_bs` | Bootstrap 5 HTML | `(block) -> str` |
| `_html_tw` | Tailwind CSS HTML | `(block) -> str` |
| `_md` | Markdown | `(block) -> str` |
| `_docx` | Word (.docx) | `(doc, block) -> None` |
| `_pptx` | PowerPoint | `(slide, y, block) -> next_y` |

対応しないレンダラーの suffix は省略可（その出力でスキップ＋警告）。  
`plugins/_example.py` に全レンダラー対応のコメント付きサンプルがあります。
