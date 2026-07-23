import { selectComposition, renderMedia } from "@remotion/renderer";
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { validateScenes } from "./scene-schema.mjs";

export async function exportReel({ scenesPath, out, bundleDir, manifestPath }) {
  const scenes = JSON.parse(fs.readFileSync(scenesPath, "utf8"));
  const manifest = JSON.parse(fs.readFileSync(manifestPath, "utf8"));
  const v = validateScenes(scenes, manifest);
  if (!v.ok) { throw new Error("scenes 校验不过: " + JSON.stringify(v.errors)); }
  const inputProps = { scenes };
  const composition = await selectComposition({ serveUrl: bundleDir, id: "Reel", inputProps });
  const part = out + ".part.mp4";
  await renderMedia({ serveUrl: bundleDir, composition, codec: "h264", inputProps, outputLocation: part });
  // 原子落盘:校验后 rename
  execFileSync("ffprobe", ["-v", "error", part], { stdio: "ignore" });
  fs.renameSync(part, out);
  return out;
}

export async function previewReel({ scenesPath, out, bundleDir, manifestPath }) {
  const scenes = JSON.parse(fs.readFileSync(scenesPath, "utf8"));
  const manifest = JSON.parse(fs.readFileSync(manifestPath, "utf8"));
  const v = validateScenes(scenes, manifest);
  if (!v.ok) throw new Error("scenes 校验不过: " + JSON.stringify(v.errors));
  // 内联 bundle 的所有 .js(混淆产物)+ 数据,挂 Player 播放 Reel composition
  const jsFiles = fs.readdirSync(bundleDir).filter((f) => f.endsWith(".js"));
  const inlined = jsFiles.map((f) => `<script>${fs.readFileSync(path.join(bundleDir, f), "utf8")}</script>`).join("\n");
  const total = scenes.reduce((a, s) => a + s.durationInFrames, 0);
  const html = `<!doctype html><meta charset="utf-8"><title>预览</title>
<style>html,body{margin:0;background:#111}#r{width:100vw;height:56.25vw;max-height:100vh}</style>
<div id="r"></div>
<script>window.__SCENES__=${JSON.stringify(scenes)};window.__DUR__=${total};</script>
${inlined}
<script>/* bundle 注册了 Reel composition;用 remotion Player 挂到 #r,inputProps={scenes:__SCENES__} */
/* Player 挂载代码由 host bundle 暴露的入口驱动(见 Task 7 备注) */</script>`;
  fs.writeFileSync(out, html);
  return out;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const a = process.argv.slice(2);
  const get = (f) => { const i = a.indexOf(f); return i >= 0 ? a[i + 1] : undefined; };
  const here = path.dirname(new URL(import.meta.url).pathname);
  const bundleDir = get("--bundle") || path.resolve(here, "../../../render-bundle/bundle");
  const manifestPath = get("--manifest") || path.resolve(here, "../../../render-bundle/manifest.json");
  const scenesPath = get("--scenes"); const out = get("--export"); const preview = get("--preview");
  if (!scenesPath || (!out && !preview)) { console.error("用法: render-reel.mjs --scenes <f> --export <out.mp4> | --preview <out.html>"); process.exit(1); }
  const task = preview
    ? previewReel({ scenesPath, out: preview, bundleDir, manifestPath })
    : exportReel({ scenesPath, out, bundleDir, manifestPath });
  task.then((o) => process.stdout.write(o))
    .catch((e) => { console.error(String(e.message || e)); process.exit(1); });
}
