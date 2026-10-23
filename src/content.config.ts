// 投稿作品（fm7/works/<作品>/work.json）。項目の意味は AGENTS.md の「置き場所」
import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { z } from 'astro/zod';
import { TAGS } from './lib/site';

const NAME_RE = /^[a-z0-9][a-z0-9-]{0,63}$/;
// /fm7/ の下で、作品と同じ所に置く名前（作品の名前には使えない）
const RESERVED = ['credits', 'webm7'];

const works = defineCollection({
  loader: glob({
    pattern: '*/work.json',
    base: './fm7/works',
    // 作品の名前はフォルダーの名前。URL は /fm7/<作品>/
    generateId: ({ entry }) => {
      const name = entry.split('/')[0];
      if (!NAME_RE.test(name)) throw new Error(`${name}: 作品の名前は英小文字・数字・- だけ`);
      if (RESERVED.includes(name)) throw new Error(`${name}: この名前は作品に使えない`);
      return name;
    },
  }),
  schema: z.strictObject({
    title: z.string(),
    // カード・検索・SNS 用の短い説明
    description: z.string().default(''),
    // 紹介文の上の見出し（\n の所で折り返す）
    catch: z.string().optional(),
    // ページに出す紹介文（なければ description）
    lead: z.string().optional(),
    // 「作者よりひとこと」（\n の所で改行）
    comment: z.string().optional(),
    author: z.string().optional(),
    // 機種のタグは自動で付くので、ここにはそれ以外を書く。新しいタグは src/lib/site.ts の TAG_SLUGS に足す
    tags: z.array(z.enum(TAGS)).default([]),
    machine: z.enum(['fm77av40', 'fm77av']).default('fm77av40'),
    boot: z.enum(['basic', 'dos']).default('basic'),
    touch: z.strictObject({
      dpad: z.boolean().optional(),
      buttons: z.array(z.strictObject({ label: z.string(), code: z.string(), key: z.string().optional() })).optional(),
    }).optional(),
    // AV40 だけの機能を使う作品
    av40: z.boolean().default(false),
    published: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, 'published は YYYY-MM-DD').optional(),
    // 公開日の前に取り消し線で置く年（当時の発売日に見せかけた冗談）
    published_strike: z.string().optional(),
    license: z.string().optional(),
    // 画面写真（640×400）。モニターの下に ①② と並べる
    shots: z.array(z.strictObject({ file: z.string(), caption: z.string() })).max(6).default([]),
    // 仕様の表の行。[項目, 値] か [項目, 値, 補足]
    specs: z.array(z.union([z.tuple([z.string(), z.string()]), z.tuple([z.string(), z.string(), z.string()])])).default([]),
  }),
});

export const collections = { works };
