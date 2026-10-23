// Cloudflare Workers の設定（cf CLI が読む）。astro build で作った dist/ を、静的なアセットとして配るだけの Worker。
// dist/ の場所は wrangler.config.ts（cf が中で使う Wrangler に渡す）。手順は AGENTS.md の「公開」
import { defineConfig } from "cf/config";

export default defineConfig({
  worker: {
    name: "retrocoder-play",
    compatibilityDate: "2026-10-06",
    assets: {
      // 見つからない URL には dist/404.html を、404 の状態で返す
      notFoundHandling: "404-page",
    },
    // 公開する場所（retrocoder.dev のゾーンに、このホスト名の DNS レコードと証明書が自動で作られる）
    domains: ["play.retrocoder.dev"],
    // <名前>.<サブドメイン>.workers.dev と、版ごとのプレビューの URL では見せない（公開するのは上のドメインだけ）
    workersDev: false,
    previewUrls: false,
  },
});
