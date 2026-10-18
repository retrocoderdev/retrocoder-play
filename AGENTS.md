# AGENTS.md

「プレイ！レトロPC！」（`play.retrocoder.dev` に置く）は、レトロ PC の作品をブラウザーで遊べるサイトです。サイト名は `tools/build.py` の `SITE_NAME`。作品は機種ごとに `/<機種>/<作品>/` に置き、そのページを開いてクリック（タップ）すると起動します。ディスクの選択やアップロードなどの UI は持ちません。

## 決まり

- **push は人に言われたときだけ**。コミットも、中身を人に見せてから行う。リポジトリを public に切り替えるのは人が決める（このリポジトリは public になる）。秘密の情報、手元のパス、private なリポジトリの名前を書かない
- 人とのやりとりと文書は日本語
- 公開の前に、デザインを人と試行錯誤する。`play.retrocoder.dev` に置くのはその後

## 置き場所

| 場所 | 中身 |
|---|---|
| `site/` | サイトの一番上（`/`）。共通の CSS `base.css`（色・書体・帯・横じま・下の注記）、404 のページ、`robots.txt`、アイコンとトップの OGP 画像（`tools/ogimage.py` で作る） |
| `fm7/player/` | FM-7 / FM77AV のプレイヤー（`player.js`・`player.css`、作品のページの型 `work.html`）と、ライセンスのページ `credits.html`（`/fm7/credits/` に置く） |
| `fm7/works/<作品>/` | 作品ごとに `work.json`（題名、短い説明 `description`（カード・検索・SNS）、紹介文の上の見出し `catch`（キャッチコピー。`\n` の所で折り返す。なければ出さない）、ページの紹介文 `lead`（当時の雑誌の紹介記事の調子。なければ `description`）、エミュレーターの機種 `fm77av40` / `fm77av`、起動モード `basic` / `dos`、タッチのボタン `touch`、仕様の表の行 `specs`（`[項目, 値]` か、値の下に小さく補足を出す `[項目, 値, 補足]`）、AV40 だけの機能を使うときの `av40: true`、タグ `tags`（`["デモ"]` など。機種のタグは自動で付く。新しいタグは `build.py` の `TAG_SLUGS` に URL の名前と一緒に足す）、作者 `author`、紹介文の後の囲み「作者よりひとこと」`comment`（`\n` の所で改行）、公開日 `published`（`YYYY-MM-DD`。表の最後に「公開日」として出す）、公開日の前に取り消し線で置く年 `published_strike`（当時の発売日に見せかけた冗談）、作品のライセンス `license`（`"MIT License"`、`"無断転載・再配布禁止"` など。作者が決める。表の最後に出す。条文を `LICENSE.txt` として置くと、表の値がそこへのリンクになる））、画面写真 `shots`（`[{"file": "shot1.png", "caption": "解説"}]`。モニターの下に ①② と並べる。画像は 640×400）と `disk.d77`、サムネイル `thumb.png`（640×400。一覧のカード、起動前の画面、`og:image`） |
| `vendor/webm7/` | WebM7 のコア・互換 ROM・ライセンスの文書の写し（改変しない）。版は `VERSION` |
| `site/img/` | トップのヘッダーと、作品・ライセンス・404 の題の帯（`build.py` の `whead()`）の絵。地はぶどう色（`base.css` の `--grape`）に、作品のディスクの中身を並べた 16 進ダンプの模様 `hexdump.svg` と集中線（`.burst`、CSS）。絵は透明のロゴ `header_logo_*`（AVIF 640px・1280px）と女の子 `header_chara_*`（AVIF 600px・1200px）。PNG（ロゴ 640px・女の子 600px、256 色に減らしたもの）は AVIF を表示できないブラウザー向け |
| `art/` | ヘッダーの絵の元の PNG（ロゴ `header_logo.png` は 2172×724、女の子 `header_chara.png` は 1448×1086）。git に入れない（`.gitignore`。手元にだけ置く）。`tools/headerimg.py` で `site/img/` に変換し、トップの OGP 画像（`tools/ogimage.py`）にも使う |
| `tools/build.py` | `dist/`（公開するもの。git 管理外）を作る |
| `tools/ogimage.py` | 共有したときの画像（OGP、1200×630。作品の `og.png` とトップの `site/og.jpg`）とアイコンを作る。手元の Chrome（画面なし）と sips を使う。作品の題名・キャッチコピー・サムネイルや、デザインを変えたら回す |
| `tools/headerimg.py` | `art/` の元の絵から `site/img/header_*` を作る（Pillow 11.3 以降が要る）。AVIF は sips で作らない（大きい絵をタイルに分けて書き、透明な所のある絵が Chrome で表示されないことがあった） |

## 使い方

```
python3 tools/build.py --serve     # http://localhost:8078/fm7/<作品>/
```

- ページの `<head>`（title・description・canonical・OGP・アイコン・フォント・`/base.css`）は `build.py` の `head()` が `{{head}}` に入れる。`sitemap.xml` も `build.py` が作る
- トップとタグごとの一覧ページ（`/tags/<名前>/`。JavaScript を使わない静的なページ）は、`site/index.html` をひな形に `build.py` が作る
- 全ページ共通のフッター（サイト名・ライセンス・ソースコードと、著作権の表示）は `build.py` の `FOOTER` が `{{footer}}` に入れる
- 404 のページは `dist/404.html`。Cloudflare Workers は、見つからない URL でこれを返す（下の「公開」）。どの URL でも出るので、中のリンクは `/` から始める
- 作品を足すときは `fm7/works/<作品>/` に `work.json` と `disk.d77` を置く。名前は英小文字・数字・`-`。URL は `/fm7/<作品>/`
- プレイヤーは、作品のページに埋め込んだ設定（`<script id="work">`）を読み、隣の `disk.d77` だけを読み込む
- 表示する機種名は `FM77AV`。AV40 だけの機能を使う作品（`"av40": true`）だけ `FM77AV40` と書く。仕様の表では「対応機種」として「FM77AV 以降」と出す
- 仕様の表の並び: 対応機種 → `specs`（画面モード・媒体・操作方法など）→ 作者 → 公開日 → ライセンス
- モニターの下のランプは本体の前面と同じ並び（左からドライブ 1・ドライブ 0・電源）。ドライブのランプは、コアの `fdc.accessLatch` を毎フレーム読んで点ける（コアは変えない）
- `&debug`（`?debug`）で、届いたキーとコアのキーボードの状態を左上に出す。`?autostart` はクリックなしで起動（確かめる用。音は出ない）

## 公開（Cloudflare Workers）

- Cloudflare の操作には **cf CLI**（`cf`。Cloudflare の公式の CLI）を使う。`wrangler` のコマンドは直接打たない（cf が中で使う道具として入れているだけ）
- 設定: `cloudflare.config.ts`（Worker の名前、見つからない URL で `404.html` を返す `notFoundHandling: "404-page"`、公開するドメイン `play.retrocoder.dev`）と `wrangler.config.ts`（配るフォルダー `dist/`）
- 道具: `package.json` に `cf` と `wrangler` を版を固定して入れる（`npm install` で `node_modules/`）。cf は設定を読むのに、手元の `node_modules` の `cf` を使う
- 手順:
  ```
  python3 tools/build.py      # dist/ を作る（cf は build.py を回さない）
  cf dev                      # http://localhost:8787/ で、本番と同じ振り分けで確かめる
  cf deploy --dry-run         # 送らずに組み立てだけ確かめる
  cf deploy                   # 配る（人に確かめてから）
  ```
- ログインは人が行う（`cf auth login`。ブラウザーを開くため）
- URL の形は Workers の既定（`auto-trailing-slash`）に合わせる: フォルダーは `/x/`（中の `index.html`）、`x.html` は `/x` に転送される。ページを足すときは `x/index.html` にして、`/x/` で指す（ライセンスのページが `/fm7/credits/` なのはこのため）
- `cf dev`・`cf build`・`cf deploy` は `.cloudflare/`（組み立てた結果。git に入れない）を作る
- コマンドの探し方: `cf cli search "<したいこと>"` で探し、見つけたコマンドの `--help` を読む。説明書は `cf docs search "<質問>"`。どちらの検索にも、ドメイン・アカウントの ID・名前などを入れない（したいことと、リソースの種類だけを書く）

## ライセンス

- このリポジトリのライセンスは置き場所で分かれる（`README.md` の表）。サイトの仕組み（`tools/`・`site/`・`fm7/player/`）は MIT（`LICENSE`、© 2026 retrocoder）。投稿作品（`fm7/works/`）は作者のもので、条件は `work.json` の `license`。ロゴとキャラクターの絵（`site/img/`・OGP 画像）は MIT の対象外で転用不可
- 作品を載せるときは、作者に `license` を決めてもらう
- WebM7（MIT）、互換 ROM 7032 Alternative ROMs（MIT）、東雲フォント由来の字形（パブリックドメイン）、fmgen（cisc。独自の条件）。表示は `fm7/player/credits.html`
- fmgen の条件: 無料で配る、原文の readme（`vendor/webm7/core/fmgen_readme.txt`）を改変せずに付ける、商用に組み込むときは作者の合意を得る。有料にしたり広告を付けたりする前に人に確認する
- `vendor/webm7/` は改変しない。更新するときは WebM7 の新しい版をまるごと写し、`VERSION` を書き換え、作品が動くことを確かめる

## 知られていること

- キーを横取りするブラウザーの拡張機能（Vimium など）があると、キーがページに届かない（`?debug` で `keydown=0`）。手当てはしない（見えない入力欄にフォーカスを置く手は、日本語入力の変換、ESC が届かない、スマホのソフトキーボードの副作用がある）。使う人の側で、Vimium なら `i` か、サイトを除外する
- 音はユーザーの操作の中でしか始められないので、クリック（タップ）で電源を入れる
