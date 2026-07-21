// build-manifest.mjs — 从 JOBDIR 里的文件**按页号 NN 自动配对**生成 scenes.json,
// 而不是让 LLM 手写清单 —— 从结构上杜绝「data/gt 配错页」。
//
// 规则:目录里每个 `NN.png`(或 .jpg/.jpeg) 必须有同号 `NN.vec.json`;
//   `NN.mp3` 存在则作 audio(旁白);`NN.txt` 存在则其内容作 narration(可选,仅记录)。
//   缺 `NN.vec.json` 的图 → **报错退出**(surface,不静默错渲)。按 NN 升序排。
//   例外:存在同号 `NN.static` 标记文件 → 该页为「降级页」(积分不足时用原图直接定格,
//   不做逐笔绘制),此时**不要求** `NN.vec.json`,scene 记为 { gt, static:true }。降级须显式
//   放 `NN.static`(空文件即可),不会因单纯缺 vec.json 而静默降级 —— 缺数据仍然报错。
// 用法:
//   node build-manifest.mjs <JOBDIR>   → 写 <JOBDIR>/scenes.json 并打印其路径
import { readdirSync, existsSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";

export function buildManifest(dir) {
  const files = readdirSync(dir);
  const pages = files
    .map((f) => {
      const m = f.match(/^(\d+)\.(png|jpg|jpeg)$/i);
      return m ? { nn: m[1], img: f } : null;
    })
    .filter(Boolean)
    .sort((a, b) => a.nn.localeCompare(b.nn, undefined, { numeric: true }));

  if (pages.length === 0) throw new Error(`${dir} 里没有 NN.png 图片`);

  const missing = [];
  const scenes = pages.map(({ nn, img }) => {
    const isStatic = existsSync(join(dir, `${nn}.static`));  // 显式降级标记
    const vec = `${nn}.vec.json`;
    if (!isStatic && !existsSync(join(dir, vec))) { missing.push(`${nn}: 缺 ${vec}`); return null; }
    const scene = isStatic
      ? { gt: join(dir, img), static: true }               // 降级页:原图定格,无绘制数据
      : { data: join(dir, vec), gt: join(dir, img) };
    if (existsSync(join(dir, `${nn}.mp3`))) scene.audio = join(dir, `${nn}.mp3`);
    const txt = join(dir, `${nn}.txt`);
    if (existsSync(txt)) { const t = readFileSync(txt, "utf8").trim(); if (t) scene.narration = t; }
    return scene;
  });

  if (missing.length) {
    throw new Error(`部分页缺绘制数据,请先对这些图跑 handdraw-page.mjs:\n  ${missing.join("\n  ")}`);
  }
  return scenes;
}

// CLI
if (process.argv[1] && import.meta.url === `file://${process.argv[1]}`) {
  const dir = process.argv[2];
  if (!dir) { console.error("Usage: node build-manifest.mjs <JOBDIR>"); process.exit(1); }
  try {
    const scenes = buildManifest(dir);
    const out = join(dir, "scenes.json");
    writeFileSync(out, JSON.stringify(scenes, null, 2));
    process.stdout.write(out);
  } catch (e) { console.error(String((e && e.message) || e)); process.exit(1); }
}
