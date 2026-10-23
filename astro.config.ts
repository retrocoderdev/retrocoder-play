// サイトの組み立て（astro build で dist/ を作る）。dist/ は cf deploy が Cloudflare Workers の静的なアセットとして配る
import { defineConfig } from 'astro/config';
import { readdirSync } from 'node:fs';
import { staticFiles } from './src/integrations/static-files';
import { ORIGIN } from './src/lib/site';

export default defineConfig({
  site: ORIGIN,
  // URL の形は Workers の既定（auto-trailing-slash）に合わせる: ページは /x/（x/index.html）
  trailingSlash: 'always',
  build: { format: 'directory', inlineStylesheets: 'never' },
  integrations: [
    staticFiles(() => [
      { url: '/fm7/webm7/', src: 'vendor/webm7' },
      { url: '/fm7/player.js', src: 'fm7/player/player.js' },
      // 作品のディスク・サムネイル・画面写真・OGP 画像・LICENSE.txt は、作品のページの隣に置く
      ...readdirSync('fm7/works', { withFileTypes: true })
        .filter((d) => d.isDirectory())
        .map((d) => ({ url: `/fm7/${d.name}/`, src: `fm7/works/${d.name}`, skip: ['work.json'] })),
    ]),
  ],
});
