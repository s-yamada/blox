"""
blox プラグインサンプル: カスタムブロック「banner」の実装例

【命名規則】
  block_{type}_html_bs  ... Bootstrap 5 HTML  (block) -> str
  block_{type}_html_tw  ... Tailwind CSS HTML  (block) -> str
  block_{type}_md       ... Markdown           (block) -> str
  block_{type}_docx     ... Word (.docx)       (doc, block) -> None
  block_{type}_pptx     ... PowerPoint PPTX    (slide, y, block) -> next_y

【使い方】
  1. このファイルを _example.py → banner.py などにコピーしてリネーム
  2. 不要なレンダラー関数は削除してOK（対応しない場合はそのレンダラーでスキップ）
  3. blox を再実行すると自動的に読み込まれる

【YAMLでの使い方】
  - type: banner
    text: "お知らせ：新機能をリリースしました"
    color: "primary"   # primary | warning | danger など
"""

# --- Bootstrap 5 HTML ---
# def block_banner_html_bs(block):
#     text  = block.get('text', '')
#     color = block.get('color', 'primary')
#     return (
#         f'<section class="alert alert-{color} mb-3" role="alert">\n'
#         f'  {text}\n'
#         f'</section>'
#     )


# --- Tailwind CSS HTML ---
# _TW_COLORS = {
#     'primary': 'bg-blue-100 border-blue-400 text-blue-800',
#     'warning': 'bg-yellow-100 border-yellow-400 text-yellow-800',
#     'danger':  'bg-red-100 border-red-400 text-red-800',
# }
# def block_banner_html_tw(block):
#     text  = block.get('text', '')
#     color = block.get('color', 'primary')
#     cls   = _TW_COLORS.get(color, _TW_COLORS['primary'])
#     return (
#         f'<section class="border-l-4 p-4 mb-4 {cls}">\n'
#         f'  {text}\n'
#         f'</section>'
#     )


# --- Markdown ---
# def block_banner_md(block):
#     text = block.get('text', '')
#     return f'> **{text}**\n'


# --- Word (.docx) ---
# def block_banner_docx(doc, block):
#     text = block.get('text', '')
#     p = doc.add_paragraph(f'【お知らせ】 {text}')
#     p.runs[0].bold = True


# --- PowerPoint PPTX ---
# プラグインのPPTX関数は (slide, y, block) を受け取り、次のy座標を返す
# from pptx.util import Mm, Emu
# from renderers.pptx_styles import MARGIN_L, CONTENT_W, GAP
# from themes import C
# import renderers.pptx as _P
#
# def block_banner_pptx(slide, y, block):
#     text = block.get('text', '')
#     h = Mm(block.get('h_mm', 14))
#     bar = _P._add_shape(slide, MARGIN_L, y, CONTENT_W, h, fill_color=C['teal_lt'])
#     _P._set_shape_text(bar, text, _P.F['small'], C['navy'], bold=True)
#     return y + h + GAP
