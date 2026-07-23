#!/usr/bin/env node
// pptx-to-images.mjs — 把 .pptx **逐页渲成图**(+ 顺手抽每页文字到 source.txt),
// 全靠专家自带的 Chrome + 一个 2.7MB 的纯 JS 渲染库(@aiden0z/pptx-renderer)——
// **不需要 Office / LibreOffice / 任何本地服务 / 任何系统授权**,谁的机器都能跑。
//
// 用法: node pptx-to-images.mjs <文件.pptx> --out <JOBDIR> [--width 1280]
//   → 产出 <JOBDIR>/NN.png(逐页) + <JOBDIR>/source.txt(逐页文字),打印 JSON。
import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { createRequire } from "node:module";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const RENDER = path.resolve(HERE, "../../../render");   // 依赖 + 自带 chrome 都在这
const fail = (m) => { process.stderr.write(String(m) + "\n"); process.exit(1); };

// 在 render/node_modules 下的 .remotion 缓存里找自带的 chrome-headless-shell 可执行文件。
function findChrome() {
  const root = path.join(RENDER, "node_modules", ".remotion", "chrome-headless-shell");
  if (!fs.existsSync(root)) return null;
  const stack = [root];
  while (stack.length) {
    const d = stack.pop();
    for (const e of fs.readdirSync(d, { withFileTypes: true })) {
      const p = path.join(d, e.name);
      if (e.isDirectory()) stack.push(p);
      else if (e.name === "chrome-headless-shell" || e.name === "chrome-headless-shell.exe") return p;
    }
  }
  return null;
}

async function main() {
  const args = process.argv.slice(2);
  const get = (f) => { const i = args.indexOf(f); return i >= 0 ? args[i + 1] : undefined; };
  const src = args.find((a) => !a.startsWith("--") && a !== get("--out") && a !== get("--width"));
  const outDir = get("--out");
  const width = parseInt(get("--width") || "1280", 10) || 1280;
  if (!src || !outDir) fail("Usage: node pptx-to-images.mjs <file.pptx> --out <JOBDIR> [--width 1280]");
  const srcAbs = path.resolve(src);
  if (!fs.existsSync(srcAbs)) fail(`找不到文件: ${srcAbs}`);
  fs.mkdirSync(outDir, { recursive: true });

  // 从 render/ 解析依赖(脚本在 skills/ 下,依赖在 render/node_modules)
  const require = createRequire(path.join(RENDER, "package.json"));
  let puppeteer, bundlePath;
  try {
    puppeteer = await import(pathToFileURL(require.resolve("puppeteer-core")).href);
    bundlePath = require.resolve("@aiden0z/pptx-renderer/browser");
  } catch (e) {
    fail(`PPTX 渲染依赖未就绪(应由 run.mjs init 装好): ${e.message}`);
  }
  const chrome = findChrome();
  if (!chrome) fail("找不到自带的 chrome-headless-shell(先跑 run.mjs init)");

  // 内联 HTML:import 浏览器版渲染库 → 逐页 renderSlide → 暴露 __render 供 puppeteer 调
  const html = `<!doctype html><html><head><meta charset="utf-8">
<style>body{margin:0;background:#fff}#stage>*{display:block;margin:0}</style></head>
<body><div id="stage"></div>
<script type="module">
import { parseZip, buildPresentation, renderSlide, RECOMMENDED_ZIP_LIMITS } from './pptxr.js';
window.__render = async (url, w) => {
  const buf = await (await fetch(url)).arrayBuffer();
  const files = await parseZip(buf, RECOMMENDED_ZIP_LIMITS);
  const pres = buildPresentation(files);
  const stage = document.getElementById('stage');
  const texts = [];
  for (let i=0;i<pres.slides.length;i++){
    const h = renderSlide(pres, pres.slides[i], { width: w });
    stage.appendChild(h.element); await h.ready;
    // pptx-renderer 把文字渲成 SVG <text>,innerText 抓不到 → 用 textContent 收集所有文字节点。
    const parts = [];
    h.element.querySelectorAll('text,tspan,p,span,div,td,th,a').forEach(n=>{
      const t=(n.textContent||'').trim(); if(t) parts.push(t);
    });
    // 去重相邻重复(SVG text/tspan 可能嵌套导致重复),再拼
    const seen=[]; for(const t of parts){ if(seen[seen.length-1]!==t) seen.push(t); }
    texts.push(seen.join(' ').replace(/\s+/g,' ').trim() || (h.element.textContent||'').trim());
  }
  window.__texts = texts;
  return pres.slides.length;
};
</script></body></html>`;

  // 本地静态服务:/index.html、/pptxr.js(渲染库)、/deck.pptx(原件)
  const server = http.createServer((req, res) => {
    const u = decodeURIComponent((req.url || "/").split("?")[0]);
    if (u === "/" || u === "/index.html") { res.writeHead(200, { "Content-Type": "text/html" }); return res.end(html); }
    if (u === "/pptxr.js") { res.writeHead(200, { "Content-Type": "text/javascript" }); return fs.createReadStream(bundlePath).pipe(res); }
    if (u === "/deck.pptx") { res.writeHead(200, { "Content-Type": "application/octet-stream" }); return fs.createReadStream(srcAbs).pipe(res); }
    res.writeHead(404); res.end("nf");
  });
  await new Promise((r) => server.listen(0, r));
  const port = server.address().port;

  const browser = await puppeteer.launch({ executablePath: chrome, headless: true, args: ["--no-sandbox", "--disable-gpu"] });
  try {
    const page = await browser.newPage();
    await page.setViewport({ width: width + 120, height: 900, deviceScaleFactor: 1.5 });
    const errs = [];
    page.on("pageerror", (e) => errs.push(String(e)));
    await page.goto(`http://localhost:${port}/index.html`, { waitUntil: "networkidle0", timeout: 60000 });
    const n = await page.evaluate((u, w) => window.__render(u, w), `http://localhost:${port}/deck.pptx`, width);
    if (!n) fail(`未渲染出任何幻灯片${errs.length ? ": " + errs[0] : ""}`);
    await new Promise((r) => setTimeout(r, 600));
    const slides = await page.$$("#stage > *");
    const files = [];
    for (let i = 0; i < slides.length; i++) {
      const nn = String(i + 1).padStart(2, "0");
      await slides[i].screenshot({ path: path.join(outDir, `${nn}.png`) });
      files.push(`${nn}.png`);
    }
    // 逐页文字 → source.txt(能抽到就写;抽不到就置空,让 agent 逐页读图理解,和线上 vision 一致)。
    const texts = await page.evaluate(() => window.__texts || []);
    const totalChars = texts.join("").replace(/\s/g, "").length;
    let sourceText = null;
    if (totalChars >= 20) {   // 有实质文字才写(图形化 deck 文字在 canvas/svg 里抽不出,属正常)
      const chunks = texts.map((t, i) => `===== 第 ${String(i + 1).padStart(2, "0")} 页 =====\n` + (t || "(本页无文字)"));
      const sp = path.join(outDir, "source.txt");
      fs.writeFileSync(sp, chunks.join("\n\n"));
      sourceText = sp;
    }

    process.stdout.write(JSON.stringify({
      pages: files.length, backend: "pptx-renderer", files,
      sourceText,
      sourceHint: sourceText ? "先读 source.txt 整体解析,再逐页看图"
        : "PPTX 无可提取文字(图形化页面),**逐页看 NN.png 高保真页面图理解**(和线上 vision 同法)",
    }));
  } finally { await browser.close(); server.close(); }
}
main().catch((e) => fail((e && e.message) || e));
