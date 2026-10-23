// 投稿作品の一覧。work.json（src/content.config.ts）に、ページを作るのに要るものを足す
import { getCollection } from 'astro:content';
import { existsSync } from 'node:fs';
import type { Tag } from './site';
import webm7Version from '../../vendor/webm7/VERSION?raw';
import altromsReadme from '../../vendor/webm7/assets/altroms/README.md?raw';

const has = (id: string, file: string) => existsSync(`fm7/works/${id}/${file}`);

export async function getWorks() {
  const entries = (await getCollection('works')).sort((a, b) => (a.id < b.id ? -1 : 1));
  return entries.map(({ id, data }) => {
    for (const file of ['disk.d77', ...data.shots.map((s) => s.file)]) {
      if (!has(id, file)) throw new Error(`${id}: ${file} がない`);
    }
    // 表示する機種名。AV40 だけの機能を使う作品（"av40": true）だけ FM77AV40 と書く
    const label: Tag = data.av40 ? 'FM77AV40' : 'FM77AV';
    return {
      id,
      data,
      path: `/fm7/${id}/`,
      label,
      tags: [label, ...data.tags],
      // サムネイル（一覧のカード、起動前の画面）と OGP 画像は、なくてもよい
      thumb: has(id, 'thumb.png') ? `/fm7/${id}/thumb.png` : null,
      og: has(id, 'og.png') ? `/fm7/${id}/og.png` : null,
      // 条文 LICENSE.txt があれば、仕様の表のライセンスをそこへのリンクにする
      licenseTxt: has(id, 'LICENSE.txt'),
    };
  });
}

export type Work = Awaited<ReturnType<typeof getWorks>>[number];

// 動作環境に出す版。WebM7 は VERSION の日付、互換 ROM は README の版
export const WEBM7_VERSION = `${webm7Version.match(/\((\d{4}-\d{2}-\d{2})\)/)![1]} 版`;
export const ALTROMS_VERSION = altromsReadme.match(/\/tree\/(v[\d.]+)/)![1];
