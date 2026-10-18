#!/usr/bin/env python3
"""公開するフォルダー dist/ を作る。

    python3 tools/build.py            # dist/ を作る
    python3 tools/build.py --serve    # 作って http://localhost:8078/ で配る

- site/ は dist/ の一番上にそのまま写す
- fm7/player/ のプレイヤーと vendor/webm7/（WebM7 のコア・互換 ROM・ライセンス）を dist/fm7/ に写す
- fm7/works/<作品>/ ごとに、work.json と player/work.html から dist/fm7/<作品>/index.html を作り、disk.d77 を隣に置く
  （thumb.png があれば写して、一覧のカードと og:image に使う）
- site/index.html をひな形に、トップと、タグごとの一覧ページ（/tags/<名前>/）を作る（{{tagbar}}・{{works}}）
- ページの {{head}} に、共通の <head> の中身（title・description・canonical・OGP・アイコン・フォント・/base.css）を入れる
- sitemap.xml を作る。OGP 画像（作品の og.png とトップの og.jpg）とアイコンは tools/ogimage.py で作ってリポジトリに置いたものを写す
"""
import argparse
import hashlib
import html
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / 'dist'
ORIGIN = 'https://play.retrocoder.dev'
SITE_NAME = 'プレイ！レトロPC！'
FONTS = ('https://fonts.googleapis.com/css2?family=Dela+Gothic+One&family=M+PLUS+1+Code:wght@400;700'
         '&family=Mochiy+Pop+One&family=Zen+Kaku+Gothic+New:wght@400;700&family=Zen+Maru+Gothic:wght@500&display=swap')
NAME_RE = re.compile(r'^[a-z0-9][a-z0-9-]{0,63}$')
MACHINES = ('fm77av40', 'fm77av')
BOOTS = ('basic', 'dos')
# タグと、その一覧ページの URL の名前（/tags/<名前>/）。work.json の tags に新しいタグを書くときは、ここに足す。
# 機種のタグ（FM77AV / FM77AV40）は自動で付く
TAG_SLUGS = {'FM77AV': 'fm77av', 'FM77AV40': 'fm77av40', 'デモ': 'demo', 'ゲーム': 'game'}


SOURCE = 'https://github.com/retrocoderdev/retrocoder-play'
# GitHub のマーク（Octicons の mark-github）。文字と同じ色・大きさで、ソースコードのリンクの左に出す
GITHUB_ICON = ('<svg class="icon" viewBox="0 0 16 16" aria-hidden="true"><path fill="currentColor" d="M8 0C3.58 0 0 3.58 0 8c0 '
               '3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94'
               '-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2'
               '-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 '
               '1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95'
               '.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/></svg>')
# 全ページ共通のフッター（{{footer}}）
FOOTER = f'''<footer class="foot">
  <nav aria-label="サイト"><ul><li><a href="/">{SITE_NAME}</a></li><li><a href="/#works">投稿作品</a></li><li><a href="/#notes">技術解説</a></li><li><a href="/fm7/credits/">ライセンス</a></li><li><a href="{SOURCE}">{GITHUB_ICON}ソースコード</a></li></ul></nav>
  <p>© 2026 retrocoder</p>
</footer>'''


def whead(kind, title):
    """題の帯（作品・ライセンス・404）。kind は題名の上の札の文字"""
    e = html.escape
    return f'''<header class="whead">
  <div class="whead-bg">
    <div class="whead-in">
      <a class="art burst" href="/" aria-label="{SITE_NAME}（トップへ）">
        <picture>
          <source type="image/avif" srcset="/img/header_chara_600.avif 600w, /img/header_chara_1200.avif 1200w" sizes="220px">
          <img class="chara" src="/img/header_chara_600.png" width="600" height="416" alt="">
        </picture>
        <picture>
          <source type="image/avif" srcset="/img/header_logo_640.avif 640w, /img/header_logo_1280.avif 1280w" sizes="220px">
          <img class="logo" src="/img/header_logo_640.png" width="640" height="306" alt="">
        </picture>
      </a>
      <div class="ttl">
        <span class="kind">{e(kind)}</span>
        <h1>{e(title)}</h1>
      </div>
    </div>
  </div>
  <div class="stripes" aria-hidden="true"></div>
</header>'''


def head(title, description, path, image=None, image_alt='', index=True, og_title=None):
    """<head> の中身。path は / から始まるページの場所。image は / から始まる 1200×630 の画像。
    og_title は共有したときの題（サイト名は og:site_name で別に伝わるので、ふつうは付けない）"""
    e = html.escape
    url = ORIGIN + path
    lines = [
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">',
        f'<title>{e(title)}</title>',
        f'<meta name="description" content="{e(description)}">',
        '<meta name="theme-color" content="#3b1d63">',
    ]
    if index:
        lines += [
            f'<link rel="canonical" href="{url}">',
            f'<meta property="og:site_name" content="{SITE_NAME}">',
            '<meta property="og:locale" content="ja_JP">',
            '<meta property="og:type" content="website">',
            f'<meta property="og:title" content="{e(og_title or title)}">',
            f'<meta property="og:description" content="{e(description)}">',
            f'<meta property="og:url" content="{url}">',
        ]
        if image:
            lines += [
                f'<meta property="og:image" content="{ORIGIN}{image}">',
                '<meta property="og:image:width" content="1200">',
                '<meta property="og:image:height" content="630">',
                f'<meta property="og:image:alt" content="{e(image_alt)}">',
                '<meta name="twitter:card" content="summary_large_image">',
            ]
        else:
            lines.append('<meta name="twitter:card" content="summary">')
    else:
        lines.append('<meta name="robots" content="noindex">')
    lines += [
        '<link rel="icon" href="/favicon.svg" type="image/svg+xml">',
        '<link rel="icon" href="/favicon-32.png" sizes="32x32" type="image/png">',
        '<link rel="apple-touch-icon" href="/apple-touch-icon.png">',
        '<link rel="preconnect" href="https://fonts.googleapis.com">',
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>',
        f'<link rel="stylesheet" href="{FONTS}">',
        '<link rel="stylesheet" href="/base.css">',
    ]
    return '\n'.join(lines)


def fill_head(path, **kw):
    """dist/ のページの {{head}} を埋める"""
    page = DIST / path.lstrip('/')
    if path.endswith('/'):
        page = page / 'index.html'
    page.write_text(page.read_text().replace('{{head}}', head(path=path, **kw)))


def build_fm7():
    out = DIST / 'fm7'
    out.mkdir()
    player = ROOT / 'fm7/player'
    for name in ('player.js', 'player.css'):
        shutil.copy2(player / name, out / name)
    # ライセンスのページは /fm7/credits/（フォルダーの index.html）。Workers は credits.html を /fm7/credits へ転送するので、
    # 手元のサーバーと本番で同じ URL になる形にする
    (out / 'credits').mkdir()
    shutil.copy2(player / 'credits.html', out / 'credits/index.html')
    shutil.copytree(ROOT / 'vendor/webm7', out / 'webm7')
    template = (player / 'work.html').read_text()
    # 動作環境に出す版。WebM7 は VERSION の日付、互換 ROM は README の版
    webm7_version = re.search(r'\((\d{4}-\d{2}-\d{2})\)', (ROOT / 'vendor/webm7/VERSION').read_text()).group(1) + ' 版'
    altroms_version = re.search(r'/tree/(v[\d.]+)', (ROOT / 'vendor/webm7/assets/altroms/README.md').read_text()).group(1)
    works = []
    for work in sorted((ROOT / 'fm7/works').iterdir()):
        if not work.is_dir():
            continue
        name = work.name
        if not NAME_RE.match(name):
            sys.exit(f'{name}: 作品の名前は英小文字・数字・- だけ')
        w = json.loads((work / 'work.json').read_text())
        machine = w.get('machine', 'fm77av40')
        if machine not in MACHINES:
            sys.exit(f'{name}: machine は {MACHINES} のどれか')
        # 表示する機種名。AV40 だけの機能を使う作品（"av40": true）だけ FM77AV40 と書く
        label = 'FM77AV40' if w.get('av40') else 'FM77AV'
        e = html.escape
        # 表の値は HTML（spec_row はエスケープしない）。並びは 対応機種 → specs → 作者 → 公開日 → ライセンス
        specs = [('対応機種', f'{label} 以降')] + [(r[0], e(r[1]), *r[2:]) for r in w.get('specs', [])]
        if w.get('author'):
            specs.append(('作者', e(w['author'])))
        # 公開日（発売日の代わり）。"2026-10-18" と書き、表には 2026.10.18 と出す。published_strike を書くと、
        # その年を取り消し線で前に置く（当時の発売日に見せかけた冗談）
        if 'published' in w:
            if not re.match(r'^\d{4}-\d{2}-\d{2}$', w['published']):
                sys.exit(f'{name}: published は YYYY-MM-DD')
            strike = f'<s>{e(w["published_strike"])}</s> ' if w.get('published_strike') else ''
            specs.append(('公開日', strike + w['published'].replace('-', '.')))
        # 作品のライセンス（作品の権利は作者のもので、サイトの MIT License とは別）。"無断転載・再配布禁止"、"CC BY 4.0" など
        if w.get('license'):
            specs.append(('ライセンス', e(w['license'])))
        if w.get('boot', 'basic') not in BOOTS:
            sys.exit(f'{name}: boot は {BOOTS} のどれか')
        pub = {k: w[k] for k in ('title', 'machine', 'boot', 'touch') if k in w}
        # </script> で埋め込みが切れないよう < をエスケープする
        work_json = json.dumps(pub, ensure_ascii=False).replace('<', '\\u003c')
        (out / name).mkdir()
        thumb = (work / 'thumb.png').exists()
        if thumb:
            shutil.copy2(work / 'thumb.png', out / name / 'thumb.png')
        poster = '<img id="poster" src="thumb.png" alt="">' if thumb else ''
        og = (work / 'og.png').exists()
        if og:
            shutil.copy2(work / 'og.png', out / name / 'og.png')
        page = (template
                .replace('{{head}}', head(f'{w["title"]} - {SITE_NAME}', w.get('description', ''), f'/fm7/{name}/',
                                          f'/fm7/{name}/og.png' if og else None, f'{w["title"]}の画面', og_title=w['title']))
                .replace('{{whead}}', whead('投稿作品', w['title']))
                .replace('{{title}}', html.escape(w['title']))
                # lead はページに出す紹介文（なければ description）。description はカード・検索・SNS 用の短い説明
                # キャッチコピーは \n の所で折り返す（日本語は文節で折り返さないため）
                .replace('{{catch}}', f'    <p class="catch"><span>{html.escape(w["catch"]).replace(chr(10), "<br>")}</span></p>'
                         if w.get('catch') else '')
                .replace('{{comment}}', '    <aside class="comment"><h2>作者よりひとこと</h2><p>'
                         + html.escape(w['comment']).replace(chr(10), '<br>') + '</p></aside>' if w.get('comment') else '')
                .replace('{{shots}}', shots_html(w.get('shots', [])))
                .replace('{{lead}}', html.escape(w.get('lead', w.get('description', ''))))
                .replace('{{description}}', html.escape(w.get('description', '')))
                .replace('{{machine_label}}', label)
                .replace('{{poster}}', poster)
                .replace('{{webm7_version}}', webm7_version)
                .replace('{{altroms_version}}', altroms_version)
                .replace('{{specs}}', '\n'.join(spec_row(*r) for r in specs))
                .replace('{{work_json}}', work_json))
        (out / name / 'index.html').write_text(page)
        shutil.copy2(work / 'disk.d77', out / name / 'disk.d77')
        for shot in w.get('shots', []):
            shutil.copy2(work / shot['file'], out / name / shot['file'])
        tags = [label] + w.get('tags', [])
        for t in tags:
            if t not in TAG_SLUGS:
                sys.exit(f'{name}: タグ「{t}」の URL の名前がない（build.py の TAG_SLUGS に足す）')
        works.append({'path': f'/fm7/{name}/', 'title': w['title'], 'description': w.get('description', ''),
                      'tags': tags, 'thumb': f'/fm7/{name}/thumb.png' if thumb else None})
    return works


def shots_html(shots):
    """モニターの下に並べる画面写真。雑誌の紙面のように、白いふちと番号と解説を付ける"""
    if not shots:
        return ''
    e = html.escape
    marks = '①②③④⑤⑥'
    figs = ''.join(f'<figure><img src="{e(s["file"])}" alt="画面写真{marks[i]}" width="640" height="400" loading="lazy">'
                   f'<figcaption><b>{marks[i]}</b>{e(s["caption"])}</figcaption></figure>'
                   for i, s in enumerate(shots))
    return f'    <div class="shots">{figs}</div>'


def spec_row(key, value_html, note=None):
    """仕様の表の 1 行。値は HTML のまま入れる。3 つ目があれば、値の下に小さく補足を出す"""
    e = html.escape
    small = f'<small>{e(note)}</small>' if note else ''
    return f'      <dt>{e(key)}</dt><dd>{value_html}{small}</dd>'


def tag_link(tag, current=None, count=None):
    """タグのリンク。current と同じタグは塗りつぶし（aria-current）"""
    e = html.escape
    here = ' aria-current="page"' if tag == current else ''
    n = f'<small>{count}</small>' if count is not None else ''
    href = '/' if tag is None else f'/tags/{TAG_SLUGS[tag]}/'
    return f'<a class="tag" href="{href}"{here}>{e(tag or "すべて")}{n}</a>'


def work_card(w):
    """一覧のカード。題名のリンクがカード全体を覆い（.title a::after）、タグのリンクはその上に重ねる"""
    e = html.escape
    img = (f'<img src="{e(w["thumb"])}" alt="" width="640" height="400" loading="lazy">' if w['thumb']
           else '<span class="noimg"></span>')
    tags = ''.join(tag_link(t) for t in w['tags'])
    return (f'<li class="work">'
            f'<div class="mon">{img}<div class="chin"><span class="lamps" aria-hidden="true">'
            f'<span class="drive"><i class="lamp"></i><b>1</b></span>'
            f'<span class="drive"><i class="lamp"></i><b>0</b></span>'
            f'<span><i class="lamp pwr"></i>電源</span></span></div></div>'
            f'<div class="stripes"></div>'
            f'<div class="meta"><div class="tags">{tags}</div>'
            f'<h3 class="title"><a href="{e(w["path"])}"><span>{e(w["title"])}</span></a></h3>'
            f'<p class="desc">{e(w["description"])}</p></div></li>')


def build_lists(works):
    """トップ（すべての作品）と、タグごとの一覧ページ /tags/<名前>/ を、同じひな形（site/index.html）から作る。
    作った一覧の場所を返す"""
    template = (ROOT / 'site/index.html').read_text()
    used = [t for t in TAG_SLUGS if any(t in w['tags'] for w in works)]
    paths = []
    for tag in [None] + used:
        listed = [w for w in works if tag is None or tag in w['tags']]
        bar = tag_link(None, tag, len(works)) + ''.join(
            tag_link(t, tag, sum(t in w['tags'] for w in works)) for t in used)
        path = '/' if tag is None else f'/tags/{TAG_SLUGS[tag]}/'
        page = DIST / path.lstrip('/') / 'index.html'
        page.parent.mkdir(parents=True, exist_ok=True)
        page.write_text(template
                        .replace('{{tagbar}}', bar)
                        .replace('{{works}}', '\n'.join(work_card(w) for w in listed)))
        if tag is None:
            fill_head(path, title=SITE_NAME, description='1980 年代のパソコン向けのオリジナルのゲームやデモを、ブラウザーでそのまま遊べる投稿作品のサイト。FM-7 / FM77AV の作品は WebM7 で動きます。',
                      image='/og.jpg', image_alt='プレイ！レトロPC！のロゴと、キーボードに手を置いて笑う女の子の絵')
        else:
            fill_head(path, title=f'{tag}の投稿作品 - {SITE_NAME}', og_title=f'{tag}の投稿作品',
                      description=f'{SITE_NAME}の投稿作品のうち、「{tag}」のもの。',
                      image='/og.jpg', image_alt='プレイ！レトロPC！のロゴと、キーボードに手を置いて笑う女の子の絵')
        paths.append(path)
    return paths


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--serve', action='store_true', help='作ったあと http://localhost:8078/ で配る')
    args = ap.parse_args()

    if DIST.exists():
        shutil.rmtree(DIST)
    shutil.copytree(ROOT / 'site', DIST)
    works = build_fm7()
    lists = build_lists(works)
    fill_head('/fm7/credits/', title=f'ライセンスについて - {SITE_NAME}', og_title='ライセンスについて',
              description='FM-7 / FM77AV の作品のプレイヤーが使っているソフトウェアと素材のライセンス。')
    fill_head('/404.html', title=f'ページが見つかりません - {SITE_NAME}', description='', index=False)
    for page, kind, title in (('fm7/credits/index.html', 'ご案内', 'ライセンスについて'), ('404.html', 'お知らせ', 'ページが見つかりません')):
        f = DIST / page
        f.write_text(f.read_text().replace('{{whead}}', whead(kind, title)))
    # CSS と JS の URL に、中身から作った版（?v=…）を付ける。中身を変えたら URL も変わり、ブラウザーや CDN に
    # 古いものが残っていても新しいものを読む（古い CSS と新しい HTML の組み合わせで、形が崩れたことがあった）
    assets = {ref: hashlib.sha256((DIST / f).read_bytes()).hexdigest()[:10]
              for ref, f in (('/base.css', 'base.css'), ('../player.css', 'fm7/player.css'), ('../player.js', 'fm7/player.js'))}
    for page in DIST.rglob('*.html'):
        text = page.read_text().replace('{{footer}}', FOOTER)
        for ref, v in assets.items():
            text = text.replace(f'"{ref}"', f'"{ref}?v={v}"')
        page.write_text(text)
        if '{{' in page.read_text():
            sys.exit(f'{page.relative_to(DIST)}: 埋めていない {{{{…}}}} が残っている')
    urls = lists + [w['path'] for w in works] + ['/fm7/credits/']
    (DIST / 'sitemap.xml').write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + ''.join(f'  <url><loc>{ORIGIN}{u}</loc></url>\n' for u in urls) + '</urlset>\n')
    names = [w['path'].split('/')[2] for w in works]
    print(f'dist/ を作った（fm7: {", ".join(names)}）')
    if args.serve:
        for n in names:
            print(f'http://localhost:8078/fm7/{n}/')
        subprocess.run([sys.executable, '-m', 'http.server', '8078', '--bind', '127.0.0.1', '-d', str(DIST)])


if __name__ == '__main__':
    main()
