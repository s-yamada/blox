"""
blox - Tailwind CSS HTMLレンダラー
同じYAMLスキーマからTailwind CSS製モックアップHTMLを生成する。
Play CDN を使用するためビルドステップ不要。
"""
import os
from renderers.html_bootstrap import slugify, page_filename


_TW_CDN = 'https://cdn.tailwindcss.com'

_STYLE = """\
<style>
.blox-hero { aspect-ratio: 16/5; min-height: 180px; }
.blox-img  { aspect-ratio: 3/2;  width: 100%; }
</style>"""

_PAGE_TEMPLATE = """\
<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <script src="{cdn}"></script>
  {style}
</head>
<body class="bg-white text-gray-800">
{floating_btn}
{global_nav}
<main class="max-w-4xl mx-auto px-4 py-8">
<h1 class="text-3xl font-bold mb-6 pb-2 border-b border-gray-200">{page_title}</h1>
{sections}
</main>
</body>
</html>"""

_INDEX_TEMPLATE = """\
<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{site_title}</title>
  <script src="{cdn}"></script>
</head>
<body class="bg-white">
<div class="max-w-2xl mx-auto px-4 py-12">
  <h1 class="text-3xl font-bold mb-6">{site_title}</h1>
  <ul class="divide-y border rounded">
{items}
  </ul>
</div>
</body>
</html>"""


def _btn_color(color):
    return {
        'primary':   'bg-blue-600 text-white hover:bg-blue-700',
        'secondary': 'bg-gray-500 text-white hover:bg-gray-600',
        'danger':    'bg-red-600 text-white hover:bg-red-700',
        'warning':   'bg-yellow-500 text-white hover:bg-yellow-600',
        'success':   'bg-green-600 text-white hover:bg-green-700',
    }.get(color, 'bg-gray-500 text-white')


# ============================================================
# セル HTML
# ============================================================

def _cell_img_tw(cell):
    label = cell.get('image_label', '写真') if isinstance(cell, dict) else str(cell)
    return (
        f'<div class="blox-img bg-gray-400 text-white flex items-center justify-center">'
        f'<span>{label}</span></div>'
    )


def _cell_text_tw(cell):
    parts = []
    if cell.get('title'):
        parts.append(
            f'<h3 class="font-bold text-base border-l-4 border-green-500 pl-2 mb-2">'
            f'{cell["title"]}</h3>'
        )
    if cell.get('text'):
        for line in cell['text'].split('\n'):
            parts.append(f'<p class="mb-1 text-sm">{line}</p>')
    return '\n'.join(parts) if parts else ''


def _cell_list_tw(cell):
    items = cell.get('items', [])
    list_type = cell.get('list_type', 'ul')
    if not items:
        return ''
    title = (f'<h3 class="font-bold text-base border-l-4 border-green-500 pl-2 mb-2">{cell["title"]}</h3>'
             if cell.get('title') else '')
    if list_type == 'dl':
        rows = []
        for item in items:
            sep = '：' if '：' in item else ':'
            if sep in item:
                term, desc = item.split(sep, 1)
                rows.append(f'<dt class="font-bold">{term}</dt>'
                            f'<dd class="ml-4 mb-1 text-sm">{desc}</dd>')
            else:
                rows.append(f'<dt class="text-sm">{item}</dt>')
        return title + f'<dl class="text-sm">{"".join(rows)}</dl>'
    tag = list_type
    cls = 'list-disc ml-4 text-sm' if tag == 'ul' else 'list-decimal ml-4 text-sm'
    li_items = ''.join(f'<li>{item}</li>' for item in items)
    return title + f'<{tag} class="{cls}">{li_items}</{tag}>'


def _cell_card_tw(cell):
    label = cell.get('image_label', '写真')
    title = cell.get('title', '')
    text  = cell.get('text', '')
    return (
        f'<div class="border rounded overflow-hidden h-full flex flex-col">'
        f'<div class="blox-img bg-gray-400 text-white flex items-center justify-center">'
        f'<span class="text-sm">{label}</span></div>'
        f'<div class="p-3 flex-1">'
        f'{"<p class=\"font-bold text-sm mb-1\">" + title + "</p>" if title else ""}'
        f'{"<p class=\"text-xs text-gray-600\">" + text + "</p>" if text else ""}'
        f'</div></div>'
    )


def _cell_table_tw(cell):
    title   = (f'<h3 class="font-bold text-base border-l-4 border-green-500 pl-2 mb-2">{cell["title"]}</h3>'
               if cell.get('title') else '')
    headers = cell.get('headers', [])
    items   = cell.get('items', [])
    th_cls  = 'border border-gray-300 bg-gray-100 px-3 py-2 text-left text-sm font-semibold'
    td_cls  = 'border border-gray-300 px-3 py-2 text-sm'
    thead = ''
    if headers:
        ths = ''.join(f'<th class="{th_cls}">{h}</th>' for h in headers)
        thead = f'<thead><tr>{ths}</tr></thead>'
    rows = ''.join(
        '<tr>' + ''.join(f'<td class="{td_cls}">{v}</td>' for v in (r if isinstance(r, list) else [r])) + '</tr>'
        for r in items
    )
    return title + f'<table class="w-full border-collapse border border-gray-300">{thead}<tbody>{rows}</tbody></table>'


def _cell_form_tw(cell):
    items = cell.get('items', [])
    parts = []
    base_input = 'w-full border border-gray-300 rounded px-3 py-2 text-sm bg-gray-50'
    for item in items:
        ftype = item.get('type', 'text')
        label = item.get('label', '')
        placeholder = item.get('placeholder', '')
        options = item.get('options', [])
        text = item.get('text', '')
        lbl_html = f'<label class="block text-sm font-medium text-gray-700 mb-1">{label}</label>' if label else ''

        if ftype == 'submit':
            parts.append(f'<div class="mb-4"><button type="button" class="px-4 py-2 rounded text-sm bg-blue-600 text-white">{label}</button></div>')
        elif ftype == 'button':
            c = _btn_color(item.get('color', 'primary'))
            parts.append(f'<div class="mb-4"><button type="button" class="px-4 py-2 rounded text-sm {c}">{label}</button></div>')
        elif ftype == 'buttons':
            btns = ''.join(
                f'<button type="button" class="px-4 py-2 rounded text-sm {_btn_color(b.get("color","secondary"))}">{b.get("label","")}</button>'
                for b in item.get('items', [])
            )
            parts.append(f'<div class="mb-4 flex gap-2">{btns}</div>')
        elif ftype == 'label':
            value = item.get('value', '')
            parts.append(f'<div class="mb-4">{lbl_html}<p class="text-sm py-2 text-gray-900">{value}</p></div>')
        elif ftype == 'textarea':
            parts.append(f'<div class="mb-4">{lbl_html}<textarea class="{base_input}" rows="3" disabled></textarea></div>')
        elif ftype == 'select':
            opts = ''.join(f'<option>{o}</option>' for o in options)
            parts.append(f'<div class="mb-4">{lbl_html}<select class="{base_input}" disabled>{opts}</select></div>')
        elif ftype == 'checkbox':
            parts.append(f'<div class="mb-4 flex items-center gap-2"><input type="checkbox" class="h-4 w-4" disabled><label class="text-sm text-gray-700">{text or label}</label></div>')
        elif ftype == 'radio':
            radios = ''.join(
                f'<div class="flex items-center gap-2"><input type="radio" class="h-4 w-4" disabled><label class="text-sm">{o}</label></div>'
                for o in options
            )
            parts.append(f'<div class="mb-4">{lbl_html}{radios}</div>')
        else:
            ph = f' placeholder="{placeholder}"' if placeholder else ''
            parts.append(f'<div class="mb-4">{lbl_html}<input type="{ftype}" class="{base_input}"{ph} disabled></div>')
    return f'<form>{"".join(parts)}</form>'


def _dispatch_cell_tw(cell, kind=None):
    k = kind or (cell.get('kind', 'text') if isinstance(cell, dict) else 'img')
    if k == 'img':    return _cell_img_tw(cell)
    elif k == 'text': return _cell_text_tw(cell)
    elif k == 'list': return _cell_list_tw(cell)
    elif k == 'table': return _cell_table_tw(cell)
    elif k == 'card': return _cell_card_tw(cell)
    elif k == 'form': return _cell_form_tw(cell)
    return ''


# ============================================================
# ブロック HTML
# ============================================================

def block_hero_html_tw(block):
    label   = block.get('image_label', '写真')
    caption = block.get('caption', '')
    cap_html = f'<p class="text-lg text-white">{caption}</p>' if caption else ''
    return (
        f'<section class="blox-hero bg-gray-400 text-white mb-4 '
        f'flex flex-col items-center justify-center text-center px-4">\n'
        f'  <p class="text-white/70 mb-1 text-sm">{label}</p>\n'
        f'  {cap_html}\n'
        f'</section>'
    )


def block_stats_html_tw(block):
    items = block.get('items', [])
    cols = ''.join(
        f'<div class="text-center px-4">'
        f'<div class="text-3xl font-bold text-blue-600">{s["num"]}</div>'
        f'<div class="text-sm text-gray-500">{s["label"]}</div>'
        f'</div>'
        for s in items
    )
    return (
        f'<section class="bg-gray-100 py-4 mb-4">\n'
        f'  <div class="flex justify-around">{cols}</div>\n'
        f'</section>'
    )


def block_cta_html_tw(block):
    text = block.get('text', 'お問い合わせはこちら')
    return (
        f'<section class="bg-gray-900 text-white text-center py-6 mb-4">\n'
        f'  <p class="font-bold">{text}</p>\n'
        f'</section>'
    )


def block_steps_html_tw(block):
    items = block.get('items', [])
    cols = ''.join(
        f'<div class="text-center px-2">'
        f'<div class="inline-block bg-gray-800 text-white text-sm px-3 py-1 rounded mb-2">{s.get("num", f"{i+1:02d}")}</div>'
        f'<div class="font-bold text-sm">{s.get("title", "")}</div>'
        f'<div class="text-xs text-gray-500">{s.get("text", "")}</div>'
        f'</div>'
        for i, s in enumerate(items)
    )
    n = max(len(items), 1)
    return (
        f'<section class="mb-4">\n'
        f'  <div class="grid gap-4" style="grid-template-columns: repeat({n}, minmax(0, 1fr))">{cols}</div>\n'
        f'</section>'
    )


def block_grid_html_tw(block):
    kind  = block.get('kind', 'card')
    cols  = block.get('cols', 3)
    items = block.get('items', [])
    cells = []
    for item in items:
        if isinstance(item, str):
            item = {'image_label': item}
        inner = _dispatch_cell_tw(item, kind)
        cells.append(f'<div>{inner}</div>')
    return (
        f'<section class="mb-4">\n'
        f'  <div class="grid grid-cols-{cols} gap-4">{"".join(cells)}</div>\n'
        f'</section>'
    )


def block_col_html_tw(block):
    rows_data = block.get('rows') or [{'cells': block.get('cells', [])}]
    total = block.get('cols', 12)
    rows_html = []
    for row in rows_data:
        divs = []
        for cell in row.get('cells', []):
            span  = cell.get('span', 1)
            inner = _dispatch_cell_tw(cell)
            divs.append(f'<div class="col-span-{span}">{inner}</div>')
        rows_html.append(f'  <div class="grid grid-cols-{total} gap-4 items-start mb-4">{"".join(divs)}</div>')
    return f'<section class="mb-4">\n' + '\n'.join(rows_html) + '\n</section>'


def render_block_tw(block):
    btype = block.get('type', '')
    heading = (
        f'<h2 class="text-lg font-bold mt-6 mb-2 pb-1 border-b border-gray-300">'
        f'{block["title"]}</h2>\n'
        if block.get('title') else ''
    )
    fn = globals().get(f'block_{btype}_html_tw')
    content = fn(block) if fn else f'<!-- 未知のブロック: {btype} -->'
    return heading + content


def render_floating_btn(index_file):
    return (
        f'<a href="{index_file}" '
        f'class="fixed bottom-6 right-6 z-50 bg-gray-500 text-white text-sm px-3 py-1 rounded shadow opacity-90" '
        f'title="一覧へ戻る">←</a>'
    )


def render_global_nav(site_title, nav_pages, current_filename):
    if not nav_pages:
        return ''
    items = []
    for page, filename in nav_pages:
        is_active = filename == current_filename
        cls = 'text-white font-bold px-3 py-2' if is_active else 'text-gray-300 hover:text-white px-3 py-2'
        label = page.get('nav_label') or page.get('name') or page.get('title', '')
        items.append(f'<li><a class="{cls}" href="{filename}">{label}</a></li>')
    items_html = '\n    '.join(items)
    return (
        f'<nav class="bg-gray-900 text-white px-6 py-3 flex items-center gap-6">\n'
        f'  <span class="font-bold text-lg ml-8">{site_title}</span>\n'
        f'  <ul class="flex">\n'
        f'    {items_html}\n'
        f'  </ul>\n'
        f'</nav>'
    )


def render_site(pages, out_dir, site_title='ページ一覧'):
    filenames  = [page_filename(i, p) for i, p in enumerate(pages, 1)]
    index_file = 'index.html'
    nav_pages  = [(pages[i], filenames[i]) for i in range(len(pages)) if pages[i].get('nav')]
    floating_btn = render_floating_btn(index_file)

    for i, page in enumerate(pages, 1):
        global_nav = render_global_nav(site_title, nav_pages, filenames[i - 1])
        sections   = '\n'.join(render_block_tw(b) for b in page.get('blocks', []))
        html = _PAGE_TEMPLATE.format(
            title=f'No.{i:02d} {page["title"]}',
            page_title=page.get('title', ''),
            cdn=_TW_CDN,
            style=_STYLE,
            floating_btn=floating_btn,
            global_nav=global_nav,
            sections=sections,
        )
        with open(os.path.join(out_dir, filenames[i - 1]), 'w', encoding='utf-8') as f:
            f.write(html)

    index_items = '\n'.join(
        f'    <a href="{filenames[i]}" class="flex items-center px-4 py-3 hover:bg-gray-50">'
        f'<span class="text-gray-400 text-sm mr-3">No.{i+1:02d}</span>'
        f'{pages[i]["title"]}</a>'
        for i in range(len(pages))
    )
    index_html = _INDEX_TEMPLATE.format(
        cdn=_TW_CDN,
        site_title=site_title,
        items=index_items,
    )
    with open(os.path.join(out_dir, index_file), 'w', encoding='utf-8') as f:
        f.write(index_html)
