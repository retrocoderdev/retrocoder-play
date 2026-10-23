// sitemap.xml: 一覧（トップとタグ）、作品、ライセンスのページ
import type { APIRoute } from 'astro';
import { ORIGIN, TAG_SLUGS, TAGS } from '../lib/site';
import { getWorks } from '../lib/works';

export const GET: APIRoute = async () => {
  const works = await getWorks();
  const tags = TAGS.filter((tag) => works.some((w) => w.tags.includes(tag)));
  const urls = ['/', ...tags.map((t) => `/tags/${TAG_SLUGS[t]}/`), ...works.map((w) => w.path), '/fm7/credits/'];
  return new Response('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    + urls.map((u) => `  <url><loc>${ORIGIN}${u}</loc></url>\n`).join('') + '</urlset>\n',
  { headers: { 'Content-Type': 'application/xml; charset=utf-8' } });
};
