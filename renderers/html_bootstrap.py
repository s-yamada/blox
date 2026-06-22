"""
blox - Bootstrap 5 HTMLレンダラー
同じYAMLスキーマからBootstrap 5製モックアップHTMLを生成する。
mm系パラメータ（h_mm等）はHTMLでは無視し、コンテンツが高さを決める。

高さのルール:
  hero          : aspect-ratio 16/5（横長バナー）
  img プレースホルダー: aspect-ratio 3/2（6:4）
  card 画像部    : aspect-ratio 3/2（6:4）
  その他         : コンテンツ量に依存（固定高さなし）
"""
import os
import re
import unicodedata


_BS_CSS = 'https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css'
_BS_JS  = 'https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js'

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
  <link href="{css}" rel="stylesheet">
  {style}
</head>
<body>
{floating_btn}
{global_nav}
<main class="container py-4">
<h1 class="mb-4 pb-2 border-bottom">{page_title}</h1>
{sections}
</main>
<script src="{js}"></script>
</body>
</html>"""

_INDEX_TEMPLATE = """\
<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{site_title}</title>
  <link href="{css}" rel="stylesheet">
</head>
<body>
<div class="container py-5">
  <h1 class="mb-4">{site_title}</h1>
  <div class="list-group">
{items}
  </div>
</div>
</body>
</html>"""


def slugify(text):
    text = unicodedata.normalize('NFKC', text)
    text = re.sub(r'[^\w\s-]', '', text, flags=re.UNICODE)
    text = re.sub(r'[\s]+', '-', text.strip())
    return text.lower() or 'page'


def page_filename(page_no, page):
    """name フィールドがあればそちらをスラッグ化、なければ title を使う"""
    name = page.get('name') or page.get('title', 'page')
    return f'{page_no:02d}-{slugify(name)}.html'


def render_floating_btn(index_file):
    """常時表示の「一覧へ戻る」浮きボタン"""
    return (
        f'<a href="{index_file}" '
        f'class="position-fixed btn btn-sm btn-secondary shadow-sm" '
        f'style="bottom:1.5rem;right:1.5rem;z-index:1050;opacity:.9;" '
        f'title="一覧へ戻る">←</a>'
    )


def render_global_nav(site_title, nav_pages, current_filename):
    """in_nav: true なページのグローバルナビゲーション（なければ空文字）"""
    if not nav_pages:
        return ''
    items = []
    for page, filename in nav_pages:
        active = ' active" aria-current="page"' if filename == current_filename else '"'
        label = page.get('nav_label') or page.get('name') or page.get('title', '')
        items.append(
            f'<li class="nav-item">'
            f'<a class="nav-link{active} href="{filename}">{label}</a></li>'
        )
    items_html = '\n      '.join(items)
    return (
        f'<nav class="navbar navbar-expand-lg navbar-dark bg-dark ps-3">\n'
        f'  <div class="container-fluid">\n'
        f'    <span class="navbar-brand ms-4">{site_title}</span>\n'
        f'    <ul class="navbar-nav">\n'
        f'      {items_html}\n'
        f'    </ul>\n'
        f'  </div>\n'
        f'</nav>'
    )


# ============================================================
# セル HTML（grid / col から呼び出す）
# ============================================================

def _cell_img_html(cell):
    label = cell.get('image_label', '写真') if isinstance(cell, dict) else str(cell)
    return (
        f'<div class="blox-img bg-secondary text-white d-flex align-items-center '
        f'justify-content-center">'
        f'<span>{label}</span></div>'
    )


def _cell_text_html(cell):
    parts = []
    if cell.get('title'):
        parts.append(
            f'<h3 class="h5 fw-bold border-start border-3 border-success ps-2 mb-2">'
            f'{cell["title"]}</h3>'
        )
    if cell.get('text'):
        for line in cell['text'].split('\n'):
            parts.append(f'<p class="mb-1">{line}</p>')
    return '\n'.join(parts) if parts else ''


def _cell_list_html(cell):
    items = cell.get('items', [])
    list_type = cell.get('list_type', 'ul')
    if not items:
        return ''
    title = (f'<h3 class="h5 fw-bold border-start border-3 border-success ps-2 mb-2">{cell["title"]}</h3>'
             if cell.get('title') else '')
    if list_type == 'dl':
        rows = []
        for item in items:
            sep = '：' if '：' in item else ':'
            if sep in item:
                term, desc = item.split(sep, 1)
                rows.append(f'<dt class="fw-bold">{term}</dt>'
                            f'<dd class="ms-3 mb-1">{desc}</dd>')
            else:
                rows.append(f'<dt>{item}</dt>')
        return title + f'<dl class="mb-0">{"".join(rows)}</dl>'
    tag = list_type
    li_items = ''.join(f'<li>{item}</li>' for item in items)
    return title + f'<{tag} class="mb-0">{li_items}</{tag}>'


def _cell_table_html(cell):
    title   = (f'<h3 class="h5 fw-bold border-start border-3 border-success ps-2 mb-2">{cell["title"]}</h3>'
               if cell.get('title') else '')
    headers = cell.get('headers', [])
    items   = cell.get('items', [])
    thead = ''
    if headers:
        ths = ''.join(f'<th>{h}</th>' for h in headers)
        thead = f'<thead class="table-light"><tr>{ths}</tr></thead>'
    rows = ''.join(
        '<tr>' + ''.join(f'<td>{v}</td>' for v in (r if isinstance(r, list) else [r])) + '</tr>'
        for r in items
    )
    return title + f'<table class="table table-sm table-bordered mb-0">{thead}<tbody>{rows}</tbody></table>'


def _cell_card_html(cell):
    label = cell.get('image_label', '写真')
    title = cell.get('title', '')
    text  = cell.get('text', '')
    return (
        f'<div class="card h-100">'
        f'<div class="blox-img card-img-top bg-secondary text-white '
        f'd-flex align-items-center justify-content-center">'
        f'<span>{label}</span></div>'
        f'<div class="card-body">'
        f'{"<h5 class=\"card-title\">" + title + "</h5>" if title else ""}'
        f'{"<p class=\"card-text\">" + text + "</p>" if text else ""}'
        f'</div></div>'
    )



def _cell_form_html(cell):
    items = cell.get('items', [])
    parts = []
    for item in items:
        ftype = item.get('type', 'text')
        label = item.get('label', '')
        placeholder = item.get('placeholder', '')
        options = item.get('options', [])
        text = item.get('text', '')

        if ftype == 'submit':
            parts.append(
                f'<div class="mb-3">'
                f'<button type="button" class="btn btn-primary">{label}</button>'
                f'</div>'
            )
        elif ftype == 'button':
            color = item.get('color', 'primary')
            parts.append(
                f'<div class="mb-3">'
                f'<button type="button" class="btn btn-{color}">{label}</button>'
                f'</div>'
            )
        elif ftype == 'buttons':
            btns = ''.join(
                f'<button type="button" class="btn btn-{b.get("color", "secondary")}">'
                f'{b.get("label", "")}</button>'
                for b in item.get('items', [])
            )
            parts.append(f'<div class="mb-3 d-flex gap-2">{btns}</div>')
        elif ftype == 'label':
            value = item.get('value', '')
            parts.append(
                f'<div class="mb-3">'
                f'<label class="form-label text-muted small">{label}</label>'
                f'<p class="form-control-plaintext ms-1 mt-0 pt-0">{value}</p>'
                f'</div>'
            )
        elif ftype == 'file':
            parts.append(
                f'<div class="mb-3">'
                f'<label class="form-label">{label}</label>'
                f'<input type="file" class="form-control" disabled>'
                f'</div>'
            )
        elif ftype == 'textarea':
            parts.append(
                f'<div class="mb-3">'
                f'<label class="form-label">{label}</label>'
                f'<textarea class="form-control" rows="3" disabled></textarea>'
                f'</div>'
            )
        elif ftype == 'select':
            opts = ''.join(f'<option>{o}</option>' for o in options)
            parts.append(
                f'<div class="mb-3">'
                f'<label class="form-label">{label}</label>'
                f'<select class="form-select" disabled>{opts}</select>'
                f'</div>'
            )
        elif ftype == 'checkbox':
            parts.append(
                f'<div class="mb-3 form-check">'
                f'<input type="checkbox" class="form-check-input" disabled>'
                f'<label class="form-check-label">{text or label}</label>'
                f'</div>'
            )
        elif ftype == 'radio':
            radios = ''.join(
                f'<div class="form-check">'
                f'<input type="radio" class="form-check-input" disabled>'
                f'<label class="form-check-label">{o}</label>'
                f'</div>'
                for o in options
            )
            parts.append(
                f'<div class="mb-3">'
                f'<label class="form-label">{label}</label>'
                f'{radios}'
                f'</div>'
            )
        else:  # text / email / tel / password など
            ph = f' placeholder="{placeholder}"' if placeholder else ''
            parts.append(
                f'<div class="mb-3">'
                f'<label class="form-label">{label}</label>'
                f'<input type="{ftype}" class="form-control"{ph} disabled>'
                f'</div>'
            )
    return f'<form>{"".join(parts)}</form>'


def _dispatch_cell_html(cell, kind=None):
    k = kind or (cell.get('kind', 'text') if isinstance(cell, dict) else 'img')
    if k == 'img':
        return _cell_img_html(cell)
    elif k == 'text':
        return _cell_text_html(cell)
    elif k == 'list':
        return _cell_list_html(cell)
    elif k == 'table':
        return _cell_table_html(cell)
    elif k == 'card':
        return _cell_card_html(cell)
    elif k == 'form':
        return _cell_form_html(cell)
    return ''


# ============================================================
# ブロック HTML
# ============================================================

def block_hero_html_bs(block):
    label   = block.get('image_label', '写真')
    caption = block.get('caption', '')
    cap_html = (f'<p class="lead text-white mb-0">{caption}</p>'
                if caption else '')
    return (
        f'<section class="blox-hero bg-secondary text-white mb-3 '
        f'd-flex flex-column align-items-center justify-content-center text-center px-3">\n'
        f'  <p class="text-white-50 mb-1">{label}</p>\n'
        f'  {cap_html}\n'
        f'</section>'
    )


def block_stats_html_bs(block):
    items = block.get('items', [])
    cols = ''.join(
        f'<div class="col text-center">'
        f'<div class="fs-3 fw-bold text-primary">{s["num"]}</div>'
        f'<div class="text-muted small">{s["label"]}</div>'
        f'</div>'
        for s in items
    )
    return (
        f'<section class="bg-light py-3 mb-3">\n'
        f'  <div class="row text-center g-2">{cols}</div>\n'
        f'</section>'
    )


def block_cta_html_bs(block):
    text = block.get('text', 'お問い合わせはこちら')
    return (
        f'<section class="bg-dark text-white text-center py-4 mb-3">\n'
        f'  <p class="mb-0 fw-bold">{text}</p>\n'
        f'</section>'
    )


def block_steps_html_bs(block):
    items = block.get('items', [])
    cols = ''.join(
        f'<div class="col text-center">'
        f'<div class="badge bg-dark fs-6 mb-2">{s.get("num", f"{i+1:02d}")}</div>'
        f'<div class="fw-bold">{s.get("title", "")}</div>'
        f'<div class="text-muted small">{s.get("text", "")}</div>'
        f'</div>'
        for i, s in enumerate(items)
    )
    return (
        f'<section class="mb-3">\n'
        f'  <div class="row row-cols-auto g-3 justify-content-center">{cols}</div>\n'
        f'</section>'
    )


def block_grid_html_bs(block):
    kind  = block.get('kind', 'card')
    cols  = block.get('cols', 3)
    items = block.get('items', [])
    cells = []
    for item in items:
        if isinstance(item, str):
            item = {'image_label': item}
        inner = _dispatch_cell_html(item, kind)
        cells.append(f'<div class="col">{inner}</div>')
    return (
        f'<section class="mb-3">\n'
        f'  <div class="row row-cols-{cols} g-3">{"".join(cells)}</div>\n'
        f'</section>'
    )


def block_col_html_bs(block):
    rows_data = block.get('rows') or [{'cells': block.get('cells', [])}]
    rows_html = []
    for row in rows_data:
        divs = []
        for cell in row.get('cells', []):
            span  = cell.get('span', 1)
            inner = _dispatch_cell_html(cell)
            divs.append(f'<div class="col-{span}">{inner}</div>')
        rows_html.append(f'  <div class="row g-3 align-items-start mb-3">{"".join(divs)}</div>')
    return f'<section class="mb-3">\n' + '\n'.join(rows_html) + '\n</section>'


def render_block_html(block):
    btype = block.get('type', '')
    heading = (
        f'<h2 class="h5 fw-bold mt-4 mb-2 pb-1 border-bottom">{block["title"]}</h2>\n'
        if block.get('title') else ''
    )
    fn = globals().get(f'block_{btype}_html_bs')
    content = fn(block) if fn else f'<!-- 未知のブロック: {btype} -->'
    return heading + content


def render_site(pages, out_dir, site_title='ページ一覧'):
    filenames  = [page_filename(i, p) for i, p in enumerate(pages, 1)]
    index_file = 'index.html'

    # in_nav: true のページを収集してグロナビ用リストを作る
    nav_pages = [
        (pages[i], filenames[i])
        for i in range(len(pages))
        if pages[i].get('nav')
    ]

    floating_btn = render_floating_btn(index_file)

    for i, page in enumerate(pages, 1):
        global_nav = render_global_nav(site_title, nav_pages, filenames[i - 1])
        sections   = '\n'.join(render_block_html(b) for b in page.get('blocks', []))
        html = _PAGE_TEMPLATE.format(
            title=f'No.{i:02d} {page["title"]}',
            page_title=page.get('title', ''),
            css=_BS_CSS,
            js=_BS_JS,
            style=_STYLE,
            floating_btn=floating_btn,
            global_nav=global_nav,
            sections=sections,
        )
        with open(os.path.join(out_dir, filenames[i - 1]), 'w', encoding='utf-8') as f:
            f.write(html)

    index_items = '\n'.join(
        f'    <a href="{filenames[i]}" class="list-group-item list-group-item-action">'
        f'<span class="text-muted me-2">No.{i+1:02d}</span>'
        f'{pages[i]["title"]}</a>'
        for i in range(len(pages))
    )
    index_html = _INDEX_TEMPLATE.format(
        css=_BS_CSS,
        site_title=site_title,
        items=index_items,
    )
    with open(os.path.join(out_dir, index_file), 'w', encoding='utf-8') as f:
        f.write(index_html)
