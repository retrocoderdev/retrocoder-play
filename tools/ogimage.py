#!/usr/bin/env python3
"""共有したときの画像（OGP、1200×630）とアイコンを作る。作品やデザインを変えたときに回す。

    python3 tools/ogimage.py

- fm7/works/<作品>/og.png: 帯と題名、モニターに入れたサムネイル（thumb.png）、キャッチコピー
- site/og.jpg: トップ。ぶどう色の地（16 進ダンプと集中線）にヘッダーの絵（art/ のロゴと女の子）と紹介文。PNG では重いので JPEG にする
- site/favicon.svg・site/favicon-32.png・site/apple-touch-icon.png（180×180）: 黒地に横じまと、青い丸の ▶

OGP 画像は手元の Chrome（画面なし）で HTML を撮る（文字を Web フォントで描くため）。Chrome の場所は
環境変数 CHROME で変えられる。アイコンは形が単純なので Python だけで描く。作ったものはリポジトリに置き、
tools/build.py はそれを写すだけ（build.py に Chrome は要らない）。
"""
import html
import json
import os
import struct
import subprocess
import sys
import tempfile
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHROME = os.environ.get('CHROME', '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')
FONTS = ('https://fonts.googleapis.com/css2?family=Dela+Gothic+One&family=Mochiy+Pop+One&family=M+PLUS+1+Code:wght@700'
         '&family=Zen+Kaku+Gothic+New:wght@400;700&display=block')

# 1200×630 の紙面に共通の CSS（色は site/base.css と同じ）
CSS = '''
* { box-sizing: border-box; }
html, body { margin: 0; width: 1200px; height: 630px; overflow: hidden; background: #fbfbf8; color: #111;
  font-family: "Zen Kaku Gothic New", sans-serif; }
.band { background: #0a0a0a; color: #fff; }
.site { font: 700 18px "M PLUS 1 Code", monospace; letter-spacing: .2em; color: #aaa; }
.stripes { height: 20px; background: linear-gradient(#ffe14d 0 22%, transparent 22% 33%, #ffae1f 33% 55%,
  transparent 55% 66%, #f26b1d 66% 82%, transparent 82% 88%, #d7261e 88%); }
.mon { padding: 12px 12px 0; border-radius: 12px; background: linear-gradient(#2c2c30, #151517);
  box-shadow: 0 0 0 1px rgba(0,0,0,.4), 0 18px 30px -16px rgba(0,0,0,.6); }
.mon img { display: block; border-radius: 5px; image-rendering: pixelated; background: #000; }
.chin { height: 30px; display: flex; align-items: center; justify-content: space-between;
  font: 700 12px "M PLUS 1 Code", monospace; letter-spacing: .14em; color: #8d8d92; }
.lamps { display: flex; gap: 14px; align-items: center; }
.lamps span { display: inline-flex; gap: 6px; align-items: center; }
.lamp { width: 16px; height: 6px; border-radius: 2px; background: #3a2c2a; }
.pwr { background: #43e06a; box-shadow: 0 0 6px #43e06a; }
.num { display: inline-grid; place-items: center; width: 15px; height: 15px; background: #000; color: #eee;
  font: 700 11px "Zen Kaku Gothic New", sans-serif; box-shadow: 0 0 0 1px #3a3a3e; }
.disp { font-family: "Dela Gothic One", sans-serif; font-weight: normal; transform: skewX(-10deg); transform-origin: left bottom; }
.badge { display: inline-block; background: #111; color: #fbfbf8; font: 700 18px "M PLUS 1 Code", monospace;
  padding: 2px 12px; letter-spacing: .08em; }
.marker { background: linear-gradient(transparent 62%, #ffe14d 62%, #ffe14d 92%, transparent 92%);
  -webkit-box-decoration-break: clone; box-decoration-break: clone; }
'''


def monitor(img, w, h, label=''):
    lamps = ('<span class="lamps"><span><i class="lamp"></i><b class="num">1</b></span>'
             '<span><i class="lamp"></i><b class="num">0</b></span><span><i class="lamp pwr"></i>電源</span></span>')
    return (f'<div class="mon"><img src="{img.as_uri()}" width="{w}" height="{h}">'
            f'<div class="chin"><span>{html.escape(label)}</span>{lamps}</div></div>')


def work_page(w, thumb):
    e = html.escape
    label = 'FM77AV40' if w.get('av40') else 'FM77AV'
    catch = e(w.get('catch', '')).replace('\n', '<br>')
    return f'''<div class="band" style="padding:30px 48px 0">
  <div class="site" style="font-family:'Mochiy Pop One',sans-serif;letter-spacing:.08em">プレイ！レトロPC！</div>
  <div class="disp" style="font-size:50px;line-height:1.25;margin-top:6px;padding-bottom:22px">{e(w["title"])}</div>
</div>
<div class="stripes"></div>
<div style="display:flex;gap:44px;align-items:center;padding:28px 48px">
  {monitor(thumb, 576, 360, label)}
  <div style="flex:1;min-width:0">
    <span class="badge">{label}</span>
    <div class="disp" style="font-family:'Mochiy Pop One',sans-serif;font-size:32px;line-height:1.6;margin-top:22px;white-space:nowrap"><span class="marker">{catch}</span></div>
  </div>
</div>'''


def top_page(thumbs):
    """トップ: ヘッダー（ぶどう色の地に、左に art/header_logo.png、右に art/header_chara.png）を
    1200×630 に入れ、下に横じまと紹介文。ロゴの元の絵は左右に透明な所がある（文字は横 2172 のうち 352〜1868）ので、
    その分だけ左へずらす。thumbs は使わない（作品が増えても変えない）"""
    logo, chara = (ROOT / f'art/header_{n}.png' for n in ('logo', 'chara'))
    hexdump = ROOT / 'site/img/hexdump.svg'
    burst = 'repeating-conic-gradient(rgba(255,255,255,.075) 0 5deg,transparent 5deg 12deg)'
    return f'''<div style="position:relative;height:520px;overflow:hidden;background:url({hexdump.as_uri()}) 0 0/640px 352px,#3b1d63">
  <div style="position:absolute;left:900px;top:310px;width:3000px;height:3000px;transform:translate(-50%,-50%);background:{burst}"></div>
  <img src="{chara.as_uri()}" style="position:absolute;right:-24px;bottom:-34px;height:480px">
  <img src="{logo.as_uri()}" style="position:absolute;left:-112px;top:104px;height:310px">
</div>
<div class="stripes"></div>
<div style="height:90px;display:grid;place-items:center;font-size:30px;font-weight:700;color:#111">
  レトロ PC の作品を、ブラウザーでそのまま遊べます。</div>'''


def shoot(body, out):
    """out が .jpg なら、撮った PNG を JPEG（品質 82）に直す"""
    page = (f'<!doctype html><html lang="ja"><head><meta charset="utf-8">'
            f'<link rel="stylesheet" href="{FONTS}"><style>{CSS}</style></head><body>{body}</body></html>')
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / 'og.html'
        src.write_text(page)
        png = out if out.suffix == '.png' else Path(tmp) / 'og.png'
        subprocess.run([CHROME, '--headless=new', '--disable-gpu', '--hide-scrollbars', '--force-device-scale-factor=1',
                        '--window-size=1200,630', '--virtual-time-budget=10000', '--allow-file-access-from-files',
                        f'--screenshot={png}', src.as_uri()], check=True, capture_output=True)
        wh = struct.unpack('>II', png.read_bytes()[16:24])
        if out.suffix == '.jpg':
            subprocess.run(['sips', '-s', 'format', 'jpeg', '-s', 'formatOptions', '82', str(png), '--out', str(out)],
                           check=True, capture_output=True)
    if wh != (1200, 630):
        sys.exit(f'{out}: {wh[0]}×{wh[1]} になった（1200×630 のはず）')
    print(f'{out.relative_to(ROOT)}')


# ---- アイコン（Python だけで描く） ----

def icon_pixels(n):
    """n×n の RGB。黒地、下に横じま、真ん中より上に青い丸と外の輪、白い三角（4×4 の点で縁をなめらかに）"""
    bg, blue, white = (10, 10, 10), (31, 111, 209), (255, 255, 255)
    stripes = [(0.80, 0.836, (255, 225, 77)), (0.851, 0.886, (255, 174, 31)), (0.901, 0.928, (242, 107, 29)),
               (0.937, 0.96, (215, 38, 30))]
    cx, cy = 0.5, 0.43
    tri = ((0.42, 0.30), (0.42, 0.56), (0.645, 0.43))  # 重心がほぼ丸の中心に来る

    def color_at(x, y):
        for y0, y1, c in stripes:
            if y0 <= y < y1:
                return c
        d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
        (ax, ay), (bx, by), (qx, qy) = tri

        def side(px, py, x0, y0, x1, y1):
            return (x1 - x0) * (py - y0) - (y1 - y0) * (px - x0)
        s1, s2, s3 = side(x, y, ax, ay, bx, by), side(x, y, bx, by, qx, qy), side(x, y, qx, qy, ax, ay)
        if (s1 <= 0 and s2 <= 0 and s3 <= 0) or (s1 >= 0 and s2 >= 0 and s3 >= 0):
            return white
        if d <= 0.27 or 0.305 <= d <= 0.335:
            return blue
        return bg

    k = 4
    rows = []
    for j in range(n):
        row = bytearray()
        for i in range(n):
            acc = [0, 0, 0]
            for sj in range(k):
                for si in range(k):
                    c = color_at((i + (si + 0.5) / k) / n, (j + (sj + 0.5) / k) / n)
                    acc[0] += c[0]; acc[1] += c[1]; acc[2] += c[2]
            row += bytes(v // (k * k) for v in acc)
        rows.append(bytes(row))
    return rows


def write_png(path, rows):
    h, w = len(rows), len(rows[0]) // 3
    raw = b''.join(b'\x00' + r for r in rows)

    def chunk(t, d):
        return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    path.write_bytes(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
                     + chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b''))
    print(f'{path.relative_to(ROOT)}')


FAVICON_SVG = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
<rect width="100" height="100" fill="#0a0a0a"/>
<rect y="80" width="100" height="3.6" fill="#ffe14d"/><rect y="85.1" width="100" height="3.5" fill="#ffae1f"/>
<rect y="90.1" width="100" height="2.7" fill="#f26b1d"/><rect y="93.7" width="100" height="2.3" fill="#d7261e"/>
<circle cx="50" cy="43" r="32" fill="none" stroke="#1f6fd1" stroke-width="3"/>
<circle cx="50" cy="43" r="27" fill="#1f6fd1"/>
<path d="M42 30v26l22.5-13z" fill="#fff"/>
</svg>
'''


def main():
    site = ROOT / 'site'
    (site / 'favicon.svg').write_text(FAVICON_SVG)
    print('site/favicon.svg')
    write_png(site / 'favicon-32.png', icon_pixels(32))
    write_png(site / 'apple-touch-icon.png', icon_pixels(180))

    thumbs = []
    for work in sorted((ROOT / 'fm7/works').iterdir()):
        if not (work / 'work.json').exists() or not (work / 'thumb.png').exists():
            continue
        w = json.loads((work / 'work.json').read_text())
        shoot(work_page(w, work / 'thumb.png'), work / 'og.png')
        thumbs.append(work / 'thumb.png')
    shoot(top_page(thumbs), site / 'og.jpg')


if __name__ == '__main__':
    main()
