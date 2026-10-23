// Vite に通さず、そのまま配るファイル（WebM7 のコア・互換 ROM、プレイヤーの JS、作品のディスクと画像）。
// public/ に置かず元の場所のまま、開発サーバーではそこから配り、ビルドでは dist/ に写す。
// player.js は ./webm7/core/ を相対で読み、ROM の場所を import.meta.url から決めるので、バンドルすると動かない
import type { AstroIntegration } from 'astro';
import { cpSync, createReadStream, existsSync, statSync } from 'node:fs';
import type { IncomingMessage, ServerResponse } from 'node:http';
import { basename, extname, join, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import type { ViteDevServer } from 'vite';

// url が / で終わるときは src のフォルダーを、そうでなければ src のファイルを、その URL に置く。skip は写さないファイルの名前
export type Mount = { url: string; src: string; skip?: string[] };

const ALWAYS_SKIP = ['.DS_Store'];

// 開発サーバーで返す Content-Type（本番は Cloudflare が決める）
const TYPES: Record<string, string> = {
  '.js': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.md': 'text/markdown; charset=utf-8',
  '.txt': 'text/plain; charset=utf-8',
  '.png': 'image/png',
  // LICENSE・VERSION
  '': 'text/plain; charset=utf-8',
};

const skipped = (m: Mount, file: string) => [...ALWAYS_SKIP, ...(m.skip ?? [])].includes(basename(file));

// URL のパスに当たる手元のファイル。なければ null
function lookup(m: Mount, path: string): string | null {
  if (!m.url.endsWith('/')) return path === m.url ? resolve(m.src) : null;
  if (!path.startsWith(m.url)) return null;
  const root = resolve(m.src);
  const file = resolve(root, path.slice(m.url.length));
  // ../ でフォルダーの外へ出ない
  if (!file.startsWith(root + sep) || skipped(m, file)) return null;
  return existsSync(file) && statSync(file).isFile() ? file : null;
}

// mounts は呼ぶたびに読み直す（開発中に作品を足しても、サーバーを立て直さずに済む）
export function staticFiles(mounts: () => Mount[]): AstroIntegration {
  let devServer: ViteDevServer | undefined;
  const serve = (req: IncomingMessage, res: ServerResponse, next: (err?: unknown) => void) => {
    const path = decodeURIComponent(new URL(req.url ?? '/', 'http://localhost').pathname);
    for (const m of mounts()) {
      const file = lookup(m, path);
      if (!file) continue;
      res.setHeader('Content-Type', TYPES[extname(file)] ?? 'application/octet-stream');
      createReadStream(file).pipe(res);
      return;
    }
    next();
  };
  return {
    name: 'static-files',
    hooks: {
      // Astro のミドルウェアより前に置く（後ろだと、拡張子のない VERSION・LICENSE が trailing slash の処理で 404 になる）。
      // Astro は自分のものをスタックの先頭に入れるので、それが済んだ起動の後で、こちらを先頭に入れる
      'astro:server:setup': ({ server }) => {
        devServer = server;
      },
      'astro:server:start': () => {
        devServer?.middlewares.stack.unshift({ route: '', handle: serve });
      },
      'astro:build:done': ({ dir }) => {
        const out = fileURLToPath(dir);
        for (const m of mounts()) {
          cpSync(m.src, join(out, m.url), { recursive: true, filter: (src) => !skipped(m, src) });
        }
      },
    },
  };
}
