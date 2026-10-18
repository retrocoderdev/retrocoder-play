// cf が中で使う Wrangler の設定。配るアセットの場所だけを書く（Worker の設定は cloudflare.config.ts）
import { defineWranglerConfig } from "wrangler/experimental-config";

export default defineWranglerConfig({
  assetsDirectory: "dist",
});
