# retrocoder-play

「プレイ！レトロPC！」（[play.retrocoder.dev](https://play.retrocoder.dev/)）のソースです。レトロ PC の作品を、ブラウザーでそのまま遊べるようにしています。

- FM-7 / FM77AV: [WebM7](https://github.com/7032JP/WebM7) と互換 ROM [7032 Alternative ROMs](https://github.com/7032JP/7032AltROMs) で動かしています。純正 ROM は使っていません

```
python3 tools/build.py --serve
```

## ライセンス

このリポジトリには、権利の持ち主が違うものが入っています。

| 置き場所 | 中身 | ライセンス |
|---|---|---|
| `tools/`、`site/` の HTML・CSS・アイコン、`fm7/player/` | サイトの仕組み（ページのひな形、プレイヤー、ビルドのスクリプト） | [MIT License](LICENSE)（Copyright (c) 2026 retrocoder） |
| `vendor/webm7/` | WebM7 と互換 ROM（7032 Alternative ROMs）、fmgen の移植 | それぞれのライセンス（`vendor/webm7/` の `LICENSE*`。一覧は [fm7/player/credits.html](fm7/player/credits.html)） |
| `fm7/works/<作品>/` | 投稿作品（ディスク、画面写真、紹介文） | MIT License の対象外。権利は作品の作者にあり、条件は作品ごと（`work.json` の `license`） |
| `site/img/`、`site/og.jpg`、`fm7/works/<作品>/og.png` | ロゴ、キャラクターの絵、共有したときの画像 | MIT License の対象外。転用はできません（© 2026 retrocoder） |
