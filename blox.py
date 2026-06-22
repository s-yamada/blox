#!/usr/bin/env python3
"""
blox - メインビルダー
Usage: blox [-o FILE] [--renderer pptx|html_bs|...] [input.yaml]
"""
import argparse
import importlib.util
import os
import sys
import yaml
from pptx import Presentation
from pptx.util import Emu, Mm

import themes
from renderers.pptx_styles import SLIDE_W, SLIDE_H, HEADER_H, GAP, GAP_SM
import renderers.pptx as P


# ============================================================
# プラグインローダー
# ============================================================

_SUFFIX_TO_RENDERER = {
    '_pptx':    ('renderers.pptx',          'pptx'),
    '_html_bs': ('renderers.html_bootstrap', 'html_bs'),
    '_html_tw': ('renderers.html_tailwind',  'html_tw'),
    '_md':      ('renderers.markdown',       'markdown'),
    '_docx':    ('renderers.docx',           'docx'),
}

_plugin_registry: dict = {}   # {(renderer_key, btype): fn}


def _load_plugins():
    """plugins/ ディレクトリを自動スキャンしてプラグインをレジストリに登録する。"""
    plugin_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'plugins')
    if not os.path.isdir(plugin_dir):
        return
    for fname in sorted(os.listdir(plugin_dir)):
        if not fname.endswith('.py') or fname.startswith('_'):
            continue
        path = os.path.join(plugin_dir, fname)
        spec = importlib.util.spec_from_file_location(fname[:-3], path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        for attr in dir(mod):
            if not attr.startswith('block_'):
                continue
            fn = getattr(mod, attr)
            if not callable(fn):
                continue
            for suffix, (_, renderer_key) in _SUFFIX_TO_RENDERER.items():
                if attr.endswith(suffix):
                    btype = attr[len('block_'):-len(suffix)]
                    _plugin_registry[(renderer_key, btype)] = fn
                    break


def _inject_plugins(module, renderer_key):
    """登録済みプラグイン関数をレンダラーモジュールに注入する。"""
    for (rkey, btype), fn in _plugin_registry.items():
        if rkey != renderer_key:
            continue
        if renderer_key == 'pptx':
            setattr(module, f'block_{btype}', fn)
        else:
            suffix = next(s for s, (_, k) in _SUFFIX_TO_RENDERER.items() if k == renderer_key)
            setattr(module, f'block_{btype}{suffix}', fn)


_load_plugins()
_inject_plugins(P, 'pptx')


def build_pptx(conf, out_path=None, template=None, theme=None):
    themes.apply_theme(theme or conf.get('theme', 'gray'))
    themes.shadow = conf.get('shadow', False)

    prs = Presentation(template)
    prs.slide_width  = SLIDE_W
    prs.slide_height = SLIDE_H
    blank_layout = prs.slide_layouts[6]
    _SLIDE_BOTTOM = SLIDE_H - Mm(10)
    _START_Y = HEADER_H + Mm(3)  # ヘッダー後のコンテンツ開始y（定数として近似）

    def _add_slide(page_no, page_title):
        slide = prs.slides.add_slide(blank_layout)
        y = P.add_header(slide, page_no, page_title)
        return slide, y + Mm(3)

    def _iter_assignments(blocks):
        """blocks をスライド番号と描画サブブロックのペアとして生成する。
        col/rows は行単位でスライドをまたいで分割する。
        """
        slide_idx = 0
        y = _START_Y
        for block in blocks:
            if block.get('type') == 'col' and block.get('rows'):
                rows = list(block['rows'])
                item_h = Mm(block.get('item_h_mm', block.get('h_mm', 50)))
                first = True
                while rows:
                    title_h = (P._SECTION_TITLE_H + GAP_SM) if (first and block.get('title')) else Emu(0)
                    available = _SLIDE_BOTTOM - y
                    if available < title_h + item_h and y > _START_Y:
                        slide_idx += 1
                        y = _START_Y
                        available = _SLIDE_BOTTOM - y
                    n_fit = max(1, int((available - title_h + GAP_SM) // (item_h + GAP_SM)))
                    chunk = rows[:n_fit]
                    rows = rows[n_fit:]
                    sub = {k: v for k, v in block.items() if k != 'rows'}
                    sub['rows'] = chunk
                    if not first:
                        sub.pop('title', None)
                    n = len(chunk)
                    y += title_h + item_h * n + GAP_SM * (n - 1) + GAP
                    yield slide_idx, sub
                    first = False
                    if rows:
                        slide_idx += 1
                        y = _START_Y
            else:
                bh = P.measure_block(block)
                if y > _START_Y and y + bh > _SLIDE_BOTTOM:
                    slide_idx += 1
                    y = _START_Y
                yield slide_idx, block
                y += bh

    if conf.get('title'):
        cover_slide = prs.slides.add_slide(blank_layout)
        P.add_cover(cover_slide, conf['title'], conf.get('author', ''))

    for page_no, page in enumerate(conf['pages'], 1):
        blocks     = page.get('blocks', [])
        base_title = page['title']
        assignments = list(_iter_assignments(blocks))
        total = (assignments[-1][0] + 1) if assignments else 1

        def make_title(n, _total=total, _base=base_title):
            return f'{_base} ({n}/{_total})' if _total > 1 else _base

        cur_idx  = 0
        slide_no = 1
        slide, y = _add_slide(page_no, make_title(1))

        for slide_idx, sub_block in assignments:
            if slide_idx > cur_idx:
                slide_no += 1
                slide, y = _add_slide(page_no, make_title(slide_no))
                cur_idx = slide_idx
            y = P.render_block(slide, y, sub_block)

    if out_path:
        if os.path.isdir(out_path):
            print(f'エラー: {out_path} はディレクトリです。'
                  f'--renderer html_bs などでディレクトリ出力してください。', file=sys.stderr)
            sys.exit(1)
        prs.save(out_path)
        print(f'生成完了: {out_path}', file=sys.stderr)
    else:
        prs.save(sys.stdout.buffer)


def _html_out(renderer_mod, conf, out_dir, site_title):
    os.makedirs(out_dir, exist_ok=True)
    renderer_mod.render_site(conf['pages'], out_dir, site_title)
    print(f'生成完了: {out_dir}/', file=sys.stderr)


_BUILTIN_TYPES = {'hero', 'stats', 'cta', 'steps', 'grid', 'col'}


def _circle_num(n):
    if 1 <= n <= 20:  return chr(0x2460 + n - 1)   # ①-⑳
    if 21 <= n <= 35: return chr(0x3251 + n - 21)   # ㉑-㉟
    if 36 <= n <= 50: return chr(0x32B1 + n - 36)   # ㊱-㊿
    return f'({n})'


def _apply_numbering(conf):
    """各ページの可視項目にページ内通し番号を付与した conf のコピーを返す。
    - title と image_label を独立して採番（両方あれば両方に番号が付く）
    - ブロック自体: title → image_label の順（見出しが上に出るため）
    - grid items / col cells: image_label → title の順（画像が上に出るため）
    - steps items: 採番しない（steps 全体を一塊として会話するため）
    """
    import copy

    def _tag_item(item):
        nonlocal n
        if item.get('image_label'):
            n += 1; item['image_label'] = f'{_circle_num(n)}{item["image_label"]}'
        if item.get('title'):
            n += 1; item['title'] = f'{_circle_num(n)}{item["title"]}'
        elif item.get('text'):
            n += 1; item['text'] = f'{_circle_num(n)}{item["text"]}'

    conf = copy.deepcopy(conf)
    for page in conf.get('pages', []):
        n = 0
        for block in page.get('blocks', []):
            btype = block.get('type', '')
            has_rows = btype == 'col' and bool(block.get('rows'))

            # ブロック title: rows構成のcolは採番しない（配下アイテムが採番されるため）
            if block.get('title') and not has_rows:
                n += 1; block['title'] = f'{_circle_num(n)}{block["title"]}'
            if block.get('image_label'):
                n += 1; block['image_label'] = f'{_circle_num(n)}{block["image_label"]}'
            if not block.get('title') and not has_rows and block.get('text'):
                n += 1; block['text'] = f'{_circle_num(n)}{block["text"]}'

            # grid items: image_label → title（title なければ text）
            if btype == 'grid':
                for item in block.get('items', []):
                    if isinstance(item, dict):
                        _tag_item(item)

            elif btype == 'col':
                rows = block.get('rows') or [{'cells': block.get('cells', [])}]
                for row in rows:
                    for cell in row.get('cells', []):
                        if cell.get('image_label'):
                            n += 1; cell['image_label'] = f'{_circle_num(n)}{cell["image_label"]}'
                        if cell.get('title'):
                            n += 1; cell['title'] = f'{_circle_num(n)}{cell["title"]}'
                        elif cell.get('text') and has_rows:
                            # flat cells の bare text は採番しない（本文扱い）
                            # rows 構成の bare text は採番する（行ごとのコンテンツ）
                            n += 1; cell['text'] = f'{_circle_num(n)}{cell["text"]}'
    return conf


def _validate_block_types(conf, renderer):
    plugin_types = {btype for (rkey, btype) in _plugin_registry if rkey == renderer}
    valid = _BUILTIN_TYPES | plugin_types
    errors = []
    for page in conf.get('pages', []):
        for block in page.get('blocks', []):
            btype = block.get('type', '')
            if btype and btype not in valid:
                errors.append(
                    f'  ページ「{page["title"]}」: 未知のブロック type: {btype!r}'
                )
    if errors:
        print('エラー: 不正な type が含まれています', file=sys.stderr)
        for msg in errors:
            print(msg, file=sys.stderr)
        print(f'  使用可能な type: {", ".join(sorted(valid))}', file=sys.stderr)
        sys.exit(1)


def build(yaml_path, out_path=None, renderer='pptx', template=None, theme=None, number=False):
    use_stdin = yaml_path is None or yaml_path == '-'
    f_obj = sys.stdin if use_stdin else open(yaml_path, encoding='utf-8')
    try:
        try:
            conf = yaml.safe_load(f_obj)
        except yaml.reader.ReaderError as e:
            cp = e.character if isinstance(e.character, int) else ord(e.character)
            name = {0x09: '水平タブ', 0x0B: '垂直タブ', 0x0C: '改ページ',
                    0x0D: 'キャリッジリターン'}.get(cp, f'U+{cp:04X}')
            print(f'エラー: YAMLに使用できない文字が含まれています（{name}、位置 {e.position}）', file=sys.stderr)
            print(f'  ヒント: タブ文字・制御文字はテキストエディタの「不可視文字を表示」で確認できます', file=sys.stderr)
            sys.exit(1)
        except yaml.YAMLError as e:
            print('エラー: YAMLの解析に失敗しました', file=sys.stderr)
            if hasattr(e, 'problem_mark') and e.problem_mark:
                m = e.problem_mark
                print(f'  {m.name} の {m.line + 1}行目 {m.column + 1}列目', file=sys.stderr)
            if hasattr(e, 'problem') and e.problem:
                print(f'  {e.problem}', file=sys.stderr)
            if hasattr(e, 'note') and e.note:
                print(f'  ヒント: {e.note}', file=sys.stderr)
            sys.exit(1)
    finally:
        if not use_stdin:
            f_obj.close()

    fallback = 'output' if use_stdin else os.path.splitext(os.path.basename(yaml_path))[0]
    site_title = conf.get('title') or fallback

    _validate_block_types(conf, renderer)

    if number:
        conf = _apply_numbering(conf)

    if renderer == 'pptx':
        build_pptx(conf, out_path, template, theme)

    elif renderer == 'html_bs':
        import renderers.html_bootstrap as R
        _inject_plugins(R, 'html_bs')
        _html_out(R, conf, out_path or 'output', site_title)

    elif renderer == 'html_tw':
        import renderers.html_tailwind as R
        _inject_plugins(R, 'html_tw')
        _html_out(R, conf, out_path or 'output', site_title)

    elif renderer == 'markdown':
        import renderers.markdown as R
        _inject_plugins(R, 'markdown')
        out = out_path or 'output.md'
        R.render_file(conf['pages'], out, site_title)
        print(f'生成完了: {out}', file=sys.stderr)

    elif renderer == 'docx':
        import renderers.docx as _docx_mod
        _inject_plugins(_docx_mod, 'docx')
        from renderers.docx import build_docx
        out = out_path or 'output.docx'
        build_docx(conf, out)
        print(f'生成完了: {out}', file=sys.stderr)

    else:
        print(f'未知のレンダラー: {renderer}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='YAMLブロック定義から資料・モックアップを生成する',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='例:\n'
               '  python blox.py -f sample.yaml -o output.pptx\n'
               '  python blox.py -f input.yaml --renderer html_bs -o output/\n'
               '  python blox.py -f input.yaml --renderer html_tw -o output/\n'
               '  python blox.py -f input.yaml --renderer markdown       -o output.md\n'
               '  python blox.py -f input.yaml --renderer docx           -o output.docx\n'
               '  python blox.py -f input.yaml --template corporate.pptx -o output.pptx',
    )
    parser.add_argument('-f', '--file', metavar='input.yaml',
                        help='入力YAMLファイル')
    parser.add_argument('-o', '--output', metavar='FILE/DIR',
                        help='出力先（pptx/docx/markdown: ファイル、html_*: ディレクトリ）')
    parser.add_argument('--renderer', default='pptx',
                        choices=['pptx', 'html_bs', 'html_tw', 'markdown', 'docx'],
                        help='出力レンダラー（デフォルト: pptx）')
    parser.add_argument('--theme', metavar='NAME',
                        help='PPTXカラーテーマ（gray/navy/warm/green/solarized/nord、YAMLのtheme:より優先）')
    parser.add_argument('--template', metavar='FILE',
                        help='PPTXテンプレートファイル（pptxレンダラー時のみ有効）')
    parser.add_argument('-n', '--number', action='store_true',
                        help='可視項目に通し番号を付与する（例：①タイトル）')
    parser.add_argument('--debug', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    use_stdin = not args.file or args.file == '-'
    if use_stdin:
        if sys.stdin.isatty():
            parser.print_help()
            sys.exit(0)
        args.file = None
    elif not os.path.isfile(args.file):
        print(f'エラー: 入力ファイルが見つかりません: {args.file}', file=sys.stderr)
        sys.exit(1)
    if args.output:
        if args.renderer in ('html_bs', 'html_tw'):
            if os.path.isfile(args.output) or os.path.splitext(args.output)[1]:
                print(f'エラー: {args.renderer} の出力先はディレクトリを指定してください: {args.output}', file=sys.stderr)
                sys.exit(1)
        else:
            parent = os.path.dirname(os.path.abspath(args.output))
            if not os.path.isdir(parent):
                print(f'エラー: 出力先のディレクトリが存在しません: {parent}', file=sys.stderr)
                sys.exit(1)
    if args.template and not os.path.isfile(args.template):
        print(f'エラー: テンプレートファイルが見つかりません: {args.template}', file=sys.stderr)
        sys.exit(1)
    try:
        build(args.file, args.output, args.renderer, args.template, args.theme, args.number)
    except SystemExit:
        raise
    except Exception as e:
        if args.debug:
            raise
        print(f'エラー: {e}', file=sys.stderr)
        print(f'  詳細を確認するには --debug オプションを追加してください', file=sys.stderr)
        sys.exit(1)
