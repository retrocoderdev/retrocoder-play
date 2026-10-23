// サイト全体で使う定数
export const ORIGIN = 'https://play.retrocoder.dev';
export const SITE_NAME = 'プレイ！レトロPC！';
export const SOURCE = 'https://github.com/retrocoderdev/retrocoder-play';
export const FONTS = 'https://fonts.googleapis.com/css2?family=Dela+Gothic+One&family=M+PLUS+1+Code:wght@400;700'
  + '&family=Mochiy+Pop+One&family=Zen+Kaku+Gothic+New:wght@400;700&family=Zen+Maru+Gothic:wght@500&display=swap';

// タグと、その一覧ページの URL の名前（/tags/<名前>/）。work.json の tags に新しいタグを書くときは、ここに足す。
// 機種のタグ（FM77AV / FM77AV40）は自動で付く。並びは一覧のタグの並び
export const TAG_SLUGS = { FM77AV: 'fm77av', FM77AV40: 'fm77av40', デモ: 'demo', ゲーム: 'game', CG: 'cg' } as const;
export type Tag = keyof typeof TAG_SLUGS;
export const TAGS = Object.keys(TAG_SLUGS) as [Tag, ...Tag[]];

// トップとタグの一覧ページの OGP 画像（tools/ogimage.py で作る）
export const LIST_IMAGE = '/og.jpg';
export const LIST_IMAGE_ALT = 'プレイ！レトロPC！のロゴと、キーボードに手を置いて笑う女の子の絵';
