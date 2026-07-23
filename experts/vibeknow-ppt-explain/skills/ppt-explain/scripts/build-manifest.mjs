// build-manifest.mjs — 从 JOBDIR 里的文件**按页号 NN 自动配对**生成 scenes.json。
// PPT 讲解版:一页 = 一张文档页图(NN.png)+ 同号旁白音频(NN.mp3,可选)。
// **不需要手绘 vec.json**——画面就是文档原页,运镜/字幕由渲染 Layout 负责。
//
// 规则:目录里每个 `NN.png`(或 .jpg/.jpeg)为一幕;
//   `NN.mp3` 存在则作 audio(每幕时长由它驱动);
//   `NN.txt` 存在则其内容作 narration(用于底部字幕 + 复核)。按 NN 升序排。
//   没有任何 NN.png → 报错退出(surface,不静默)。
// 用法:
//   node build-manifest.mjs <JOBDIR>   → 写 <JOBDIR>/scenes.json 并打印其路径
import { readdirSync, existsSync, readFileSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

export function buildManifest(dir) {
  const files = readdirSync(dir);
  const pages = files
    .map((f) => {
      const m = f.match(/^(\d+)\.(png|jpg|jpeg)$/i);
      return m ? { nn: m[1], img: f } : null;
    })
    .filter(Boolean)
    .sort((a, b) => a.nn.localeCompare(b.nn, undefined, { numeric: true }));

  if (pages.length === 0) throw new Error(`${dir} 里没有 NN.png 页面图(先跑 doc-to-pages.mjs)`);

  const scenes = pages.map(({ nn, img }) => {
    const scene = { gt: join(dir, img) };                 // gt = 文档原页,整页展示
    if (existsSync(join(dir, `${nn}.mp3`))) scene.audio = join(dir, `${nn}.mp3`);
    const txt = join(dir, `${nn}.txt`);
    if (existsSync(txt)) { const t = readFileSync(txt, "utf8").trim(); if (t) scene.narration = t; }
    return scene;
  });

  return scenes;
}

// CLI
if (process.argv[1] && resolve(process.argv[1]) === resolve(fileURLToPath(import.meta.url))) {
  const dir = process.argv[2];
  if (!dir) { console.error("Usage: node build-manifest.mjs <JOBDIR>"); process.exit(1); }
  try {
    const scenes = buildManifest(dir);
    const out = join(dir, "scenes.json");
    writeFileSync(out, JSON.stringify(scenes, null, 2));
    process.stdout.write(out);
  } catch (e) { console.error(String((e && e.message) || e)); process.exit(1); }
}
