# retrocoder-play

「プレイ！レトロPC！」（[play.retrocoder.dev](https://play.retrocoder.dev/)）のソースです。レトロ PC の作品を、ブラウザーでそのまま遊べるようにしています。

- FM-7 / FM77AV: [WebM7](https://github.com/7032JP/WebM7) と互換 ROM [7032 Alternative ROMs](https://github.com/7032JP/7032AltROMs) で動かしています。純正 ROM は使っていません

## 手元で動かす

Python 3 だけで動きます（追加のパッケージは要りません）。

```
python3 tools/build.py --serve     # dist/ を作り、http://localhost:8078/ で開く
```

`tools/build.py` が、`site/`・`fm7/` などから公開するファイル一式を `dist/` に作ります。`dist/` は git に入れません。

## デプロイ（Cloudflare Workers）

`dist/` を、Cloudflare Workers の静的なアセットとして配ります。操作には [cf CLI](https://developers.cloudflare.com/cf/)（Cloudflare の公式の CLI）を使います。

### 必要なもの

| もの | 用途 |
|---|---|
| Python 3 | `dist/` を作る（`tools/build.py`） |
| Node.js と npm | cf CLI と、cf が中で使う Wrangler を入れる |
| Cloudflare のアカウント | `retrocoder.dev` のゾーンがあるアカウント |

### 設定ファイル

| ファイル | 中身 |
|---|---|
| `cloudflare.config.ts` | Worker の名前（`retrocoder-play`）、公開するドメイン（`play.retrocoder.dev`）、見つからない URL で `404.html` を返す設定、workers.dev とプレビューの URL を閉じる設定 |
| `wrangler.config.ts` | 配るフォルダー（`dist/`） |
| `package.json` | cf CLI（`cf`）と Wrangler の版。どちらも版を固定している |

アカウント ID などはファイルに書きません。ログインしたアカウントから、cf CLI が決めます。

### 初めてのとき

```
npm install          # cf と wrangler を node_modules/ に入れる
npx cf auth login    # ブラウザーが開くので、Cloudflare にログインする
npx cf auth whoami   # ログインできたかを確かめる
```

`cf` を別に入れている場合は、`npx cf` の代わりに `cf` でかまいません。ただし設定ファイルを読むときは、どちらでも `node_modules/` の `cf` が使われます。

### 毎回の手順

```
python3 tools/build.py        # 1. dist/ を作り直す（cf は build.py を回さない）
npx cf dev                    # 2. http://localhost:8787/ で、本番と同じ振り分けで確かめる（Ctrl+C で止める）
npx cf deploy --dry-run       # 3. 送らずに、組み立てだけを確かめる
npx cf deploy --message "変更の要約"   # 4. 配る
```

1. **`dist/` を作り直す**: `cf deploy` は `dist/` をそのまま送ります。作り直し忘れると、古い中身が公開されます。
2. **`cf dev` で確かめる**: `python3 tools/build.py --serve`（Python の簡易サーバー）と違い、本番と同じ規則で URL を振り分けます。たとえば、見つからない URL で 404 のページが返るか、`x.html` が `/x` に転送されるか、を見られます。
3. **`--dry-run`**: 何も送りません。設定の誤りや、送るファイルの数をここで確かめます。
4. **`cf deploy`**: 前と中身が同じファイルは送り直さず、変わったファイルだけを送ります。`--message` は、あとで履歴（`npx cf workers deployments list`）を見るときの目印になります。コミットの短い ID を入れておくと、どの版を出したかがわかります。

### デプロイしたあとに確かめること

- `https://play.retrocoder.dev/` と作品のページが開き、作品が起動する
- 知らない URL（例: `https://play.retrocoder.dev/nope`）で、404 の状態で「ページが見つかりません」のページが出る
- OGP 画像を作り直したときは、本番の画像が新しくなっている（例: `curl -s https://play.retrocoder.dev/og.jpg | shasum` と `shasum < dist/og.jpg` が一致する）

CSS と JS は、`tools/build.py` が URL に中身から作った版（`?v=…`）を付けます。なので、デプロイのあとにブラウザーや CDN の古いキャッシュが残っていても、新しいものが読まれます。

### 作品や絵を変えたとき

| 変えたもの | デプロイの前に回すもの |
|---|---|
| 作品の題名・キャッチコピー・サムネイル、トップやヘッダーの見た目 | `python3 tools/ogimage.py`（共有したときの画像とアイコン。手元の Chrome を使う） |
| ヘッダーの絵の元の PNG（`art/`。git には入れない） | `python3 tools/headerimg.py`（`site/img/` の絵。Pillow 11.3 以降が要る） |

作ったものはリポジトリに入れて、コミットします（`tools/build.py` は写すだけ）。SNS は、一度読んだカードの画像をしばらく覚えています。前に共有した URL では、古い画像がしばらく出ることがあります。

### 困ったとき

- **`cf deploy` の最後に、カスタムドメインの所で失敗した**（`Custom domains: … failed`、code 10013 など）: Worker 自体は上がっていて、ドメインの割り当てだけが失敗しています。`npx cf workers triggers deploy` で、ドメインの割り当てだけをやり直します（最初のデプロイで一度起き、やり直しで直りました）
- **`Cannot connect to the Docker daemon` と出る**: コンテナを使っていないので、気にしなくてかまいません
- **前の版に戻したい**: 戻したいコミットを取り出し、`python3 tools/build.py` と `npx cf deploy` をやり直します
- **cf のコマンドを探したい**: `npx cf cli search "<したいこと>"`。説明書は `npx cf docs search "<質問>"`

## ライセンス

このリポジトリには、権利の持ち主が違うものが入っています。

| 置き場所 | 中身 | ライセンス |
|---|---|---|
| `tools/`、`site/` の HTML・CSS・アイコン、`fm7/player/` | サイトの仕組み（ページのひな形、プレイヤー、ビルドのスクリプト） | [MIT License](LICENSE)（Copyright (c) 2026 retrocoder） |
| `vendor/webm7/` | WebM7 と互換 ROM（7032 Alternative ROMs）、fmgen の移植 | それぞれのライセンス（`vendor/webm7/` の `LICENSE*`。一覧は [fm7/player/credits.html](fm7/player/credits.html)。サイトでは `/fm7/credits/`） |
| `fm7/works/<作品>/` | 投稿作品（ディスク、画面写真、紹介文） | MIT License の対象外。権利は作品の作者にあり、条件は作品ごと（`work.json` の `license`） |
| `site/img/`、`site/og.jpg`、`fm7/works/<作品>/og.png` | ロゴ、キャラクターの絵、共有したときの画像 | MIT License の対象外。転用はできません（© 2026 retrocoder） |
