"""
blox - Markdownレンダラー
同じYAMLスキーマからMarkdownを生成する。
レイアウト（grid/col）はコンテンツを縦積みで表現。
"""
import os
from renderers.html_bootstrap import slugify


def _md_filename(page_no, page):
    name = page.get('name') or page.get('title', 'page')
    return f'{page_no:02d}-{slugify(name)}.md'


# ============================================================
# セル Markdown
# ============================================================

def _cell_img_md(cell):
    label = cell.get('image_label', '写真') if isinstance(cell, dict) else str(cell)
    return f'> 📷 *{label}*\n'


def _cell_text_md(cell):
    parts = []
    if cell.get('title'):
        parts.append(f'### {cell["title"]}\n')
    if cell.get('text'):
        # \n を Markdown の強制改行（行末スペース2個）に変換
        parts.append(cell['text'].replace('\n', '  \n') + '\n')
    return '\n'.join(parts) if parts else ''


def _cell_list_md(cell):
    items = cell.get('items', [])
    list_type = cell.get('list_type', 'ul')
    if not items:
        return ''
    title = f'**{cell["title"]}**\n\n' if cell.get('title') else ''
    lines = []
    for i, item in enumerate(items):
        if list_type == 'ol':
            lines.append(f'{i+1}. {item}')
        elif list_type == 'dl':
            sep = '：' if '：' in item else ':'
            if sep in item:
                term, desc = item.split(sep, 1)
                lines.append(f'**{term.strip()}**: {desc.strip()}')
            else:
                lines.append(f'**{item}**')
        else:
            lines.append(f'- {item}')
    return title + '\n'.join(lines) + '\n'


def _cell_card_md(cell):
    parts = []
    label = cell.get('image_label', '')
    if label:
        parts.append(f'> 📷 *{label}*')
    if cell.get('title'):
        parts.append(f'**{cell["title"]}**')
    if cell.get('text'):
        parts.append(cell['text'].replace('\n', '  \n'))
    return '\n'.join(parts) + '\n'


def _cell_table_md(cell):
    headers = cell.get('headers', [])
    items   = cell.get('items', [])
    if not items and not headers:
        return ''
    title = f'**{cell["title"]}**\n\n' if cell.get('title') else ''
    lines = []
    if headers:
        lines.append('| ' + ' | '.join(str(h) for h in headers) + ' |')
        lines.append('| ' + ' | '.join('---' for _ in headers) + ' |')
    for row in items:
        vals = row if isinstance(row, list) else [str(row)]
        lines.append('| ' + ' | '.join(str(v) for v in vals) + ' |')
    return title + '\n'.join(lines) + '\n'


def _cell_form_md(cell):
    items = cell.get('items', [])
    lines = []
    for item in items:
        ftype = item.get('type', 'text')
        label = item.get('label', '')
        if ftype in ('submit', 'button'):
            lines.append(f'[ {label} ]')
        elif ftype == 'buttons':
            btns = '  '.join(f'[ {b.get("label","")} ]' for b in item.get('items', []))
            lines.append(btns)
        elif ftype == 'label':
            lines.append(f'**{label}**: {item.get("value", "")}')
        elif ftype == 'checkbox':
            lines.append(f'☐ {item.get("text") or label}')
        elif ftype == 'radio':
            for o in item.get('options', []):
                lines.append(f'◯ {o}')
        elif ftype == 'select':
            opts = ' / '.join(item.get('options', []))
            lines.append(f'**{label}**: ▾ {opts}')
        else:
            ph = item.get('placeholder', '')
            lines.append(f'**{label}**: [{ph or ftype}]')
    return '\n'.join(lines) + '\n'


def _dispatch_cell_md(cell, kind=None):
    k = kind or (cell.get('kind', 'text') if isinstance(cell, dict) else 'img')
    if k == 'img':    return _cell_img_md(cell)
    elif k == 'text': return _cell_text_md(cell)
    elif k == 'list': return _cell_list_md(cell)
    elif k == 'table': return _cell_table_md(cell)
    elif k == 'card': return _cell_card_md(cell)
    elif k == 'form': return _cell_form_md(cell)
    return ''


# ============================================================
# ブロック Markdown
# ============================================================

def block_hero_md(block):
    label   = block.get('image_label', '写真')
    caption = block.get('caption', '')
    lines = [f'> 📷 *{label}*']
    if caption:
        lines.append(f'> **{caption}**')
    return '\n'.join(lines) + '\n'


def block_stats_md(block):
    items = block.get('items', [])
    if not items:
        return ''
    headers = ' | '.join(s['num'] for s in items)
    labels  = ' | '.join(s['label'] for s in items)
    seps    = ' | '.join('---' for _ in items)
    return f'| {headers} |\n| {seps} |\n| {labels} |\n'


def block_cta_md(block):
    text = block.get('text', 'お問い合わせはこちら')
    return f'> **{text}**\n'


def block_steps_md(block):
    items = block.get('items', [])
    lines = []
    for i, s in enumerate(items):
        num   = s.get('num', f'{i+1:02d}')
        title = s.get('title', '')
        text  = s.get('text', '')
        line  = f'{num}. **{title}**'
        if text:
            line += f' — {text}'
        lines.append(line)
    return '\n'.join(lines) + '\n'


def block_grid_md(block):
    kind  = block.get('kind', 'card')
    items = block.get('items', [])
    parts = []
    for item in items:
        if isinstance(item, str):
            item = {'image_label': item}
        parts.append(_dispatch_cell_md(item, kind))
    return '\n'.join(parts)


def block_col_md(block):
    rows_data = block.get('rows') or [{'cells': block.get('cells', [])}]
    row_parts = []
    for row in rows_data:
        parts = [_dispatch_cell_md(cell) for cell in row.get('cells', [])]
        row_parts.append('\n'.join(parts))
    return '\n\n'.join(row_parts)


def render_block_md(block):
    btype = block.get('type', '')
    heading = f'### {block["title"]}\n\n' if block.get('title') else ''
    fn = globals().get(f'block_{btype}_md')
    return heading + (fn(block) if fn else '')


def render_file(pages, out_path, site_title='ページ一覧'):
    sections = []
    if site_title:
        sections.append(f'# {site_title}\n')
    for i, page in enumerate(pages, 1):
        blocks_md = '\n\n'.join(
            render_block_md(b) for b in page.get('blocks', [])
        )
        sections.append(f'## No.{i:02d} {page["title"]}\n\n{blocks_md}')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('\n\n---\n\n'.join(sections) + '\n')
