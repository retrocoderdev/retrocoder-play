#!/usr/bin/env python3
"""ヘッダーの絵（art/ の元の PNG）から、公開する site/img/header_* を作る。元の絵を変えたときに回す。

    python3 tools/headerimg.py      # Pillow 11.3 以降（AVIF を書ける版）が要る: pip install pillow

- ロゴ header_logo_*: 透明な縁を切り、AVIF（640px・1280px）と PNG（640px、256 色）
- 女の子 header_chara_*: 透明な縁を切り、AVIF（600px・1200px）と PNG（600px、256 色）

AVIF は macOS の sips で作らない。sips は大きい絵をタイル（grid）に分けて書き、透明な所のある絵では
Chrome で表示されたりされなかったりした。Pillow（libavif）はタイルに分けない。
"""
import sys
from pathlib import Path

try:
    from PIL import Image, features
except ImportError:
    sys.exit('Pillow が要る（pip install pillow）')

ROOT = Path(__file__).resolve().parents[1]
ART, OUT = ROOT / 'art', ROOT / 'site/img'
# 透明な縁を切る範囲（左, 上, 右, 下）。絵の中身が収まる箱を測って、数ドット余裕をとったもの
CROP = {'logo': (352, 0, 1868, 724), 'chara': (8, 77, 1443, 1071)}


def resize(im, w):
    return im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)


def save(im, name, **opts):
    im.save(OUT / name, **opts)
    print(f'site/img/{name}  {(OUT / name).stat().st_size // 1024} KB')


def main():
    if not features.check('avif'):
        sys.exit('この Pillow は AVIF を書けない（11.3 以降にする）')
    for name, small in (('logo', 640), ('chara', 600)):
        im = Image.open(ART / f'header_{name}.png').convert('RGBA').crop(CROP[name])
        for w in (small, small * 2):
            save(resize(im, w), f'header_{name}_{w}.avif', quality=60, speed=4)
        # AVIF を表示できないブラウザー向け。色を減らして軽くする
        png = resize(im, small).quantize(256, method=Image.FASTOCTREE, dither=Image.FLOYDSTEINBERG)
        save(png, f'header_{name}_{small}.png', optimize=True)


if __name__ == '__main__':
    main()
