// resolve-bundle.mjs — 免费/完整二选一的门禁:render / preview / check-slots 都走这一个函数,
// 不各自写死 render-bundle 路径。
// 单 bundle:全部 53 版式 + 全部主题的渲染数据都已编进 render-bundle/bundle,免费/完整共用
// 同一个 bundleDir——门禁只体现在 manifestPath 上(免费 manifest 只认 serious-dark 一个主题,
// 完整 manifest 认 50 个)。两份 manifest 都随插件一起分发在 render-bundle/ 下,不靠下载,
// 永远和 bundle 同版本。
// 判定纯看本地解锁标记文件是否存在(见 pack-path.mjs)——不额外校验登录态是否仍有效:
// 门禁只管"本地有没有翻过解锁标记",不做在线鉴权。
import { existsSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { unlockMarkerPath } from "./pack-path.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const BUNDLE_DIR = resolve(HERE, "../../../render-bundle/bundle");
const FREE_MANIFEST_PATH = resolve(HERE, "../../../render-bundle/manifest.json");
const FULL_MANIFEST_PATH = resolve(HERE, "../../../render-bundle/manifest.full.json");

export function resolveBundle() {
  if (existsSync(unlockMarkerPath())) {
    return { bundleDir: BUNDLE_DIR, manifestPath: FULL_MANIFEST_PATH, tier: "full" };
  }
  return { bundleDir: BUNDLE_DIR, manifestPath: FREE_MANIFEST_PATH, tier: "free" };
}
