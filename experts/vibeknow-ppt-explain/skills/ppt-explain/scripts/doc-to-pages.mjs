#!/usr/bin/env node
// doc-to-pages.mjs — 把一份文档**逐页转成页面图** `NN.png`(NN=两位页号 01,02,…),
// 落到 JOBDIR 下,供 build-manifest → render 使用。**这是 PPT 讲解专家独有的一步**
// (手绘是生成插画,这里是把文档原页原样转图,不改内容)。
//
// 支持:
//   .pdf                        直接逐页转图
//   .pptx                       纯 JS 渲染(自带 Chrome + @aiden0z/pptx-renderer,见 pptx-to-images.mjs),不装 Office
//   .ppt .docx .doc .odp .key   只用**已装**的 soffice/LibreOffice 或 macOS Keynote 转 PDF,绝不安装;都没有 → 报 NEED_PDF 让用户自己导 PDF
//
// PDF→图 后端(按优先级自动选,第一个可用的就用):
//   1) pymupdf(python3 -c "import fitz")   —— 精确控制页号/DPI,首选
//   2) pdftoppm(poppler)                    —— 批量转 + 重命名兜底
//   都没有 → 报错并给出安装/兜底建议(让用户改上传 PDF / 装 poppler)。
//
// 用法:
//   node doc-to-pages.mjs <文档路径> --out <JOBDIR> [--dpi 144]
//   → 打印 JSON: {pages, dpi, backend, files:[...], sample:{width,height}}
import { spawnSync } from "node:child_process";
import { existsSync, readdirSync, renameSync, mkdirSync, statSync } from "node:fs";
import { join, extname, basename, resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const HERE_DIR = dirname(fileURLToPath(import.meta.url));   // 本脚本所在目录(找同目录 pptx-to-images.mjs)
const DEFAULT_DPI = 144;   // 密度/体积平衡点:16:9 幻灯片 ≈ 1920×1080,足够 720p/1080p

function fail(msg) { process.stderr.write(String(msg) + "\n"); process.exit(1); }
function have(cmd, args = ["--version"]) {
  try { const r = spawnSync(cmd, args, { stdio: "ignore" }); return r.status === 0 || r.status === 1; }
  catch { return false; }
}
function pymupdfAvailable() {
  try { return spawnSync("python3", ["-c", "import fitz"], { stdio: "ignore" }).status === 0; }
  catch { return false; }
}

// PPTX/DOCX/… → PDF。**只用机器上已经装了的引擎,绝不安装任何东西**(700MB LibreOffice 会劝退用户)。
// 按可靠度依次尝试:① 已装的 soffice(headless,安静) ② macOS 已装的 Keynote(每台 Mac 都有,osascript 导出)。
// 都没有 → 报 NEED_PDF,让用户自己导 PDF(最后兜底,不安装)。
function officeToPdf(src, outDir) {
  const outPdf = join(outDir, basename(src).replace(/\.[^.]+$/, "") + ".pdf");

  // ① soffice/LibreOffice —— 仅当**已存在**才用(headless、无窗口、最省事)。不主动安装。
  const soffice = ["soffice", "libreoffice", "/Applications/LibreOffice.app/Contents/MacOS/soffice"]
    .find((c) => have(c, ["--version"]));
  if (soffice) {
    const r = spawnSync(soffice, ["--headless", "--convert-to", "pdf", "--outdir", outDir, src],
      { encoding: "utf8", timeout: 120000 });
    if (r.status === 0 && existsSync(outPdf)) return outPdf;
  }

  // ② macOS:用已装的 Keynote 导 PDF(每台 Mac 预装,零安装)。osascript 打开→导出→关闭。
  if (process.platform === "darwin" && existsSync("/Applications/Keynote.app")) {
    const r = spawnSync("osascript", [
      "-e", "on run argv",
      "-e", 'tell application "Keynote"',
      "-e", "set d to open (POSIX file (item 1 of argv))",
      "-e", "delay 1",
      "-e", "export d to (POSIX file (item 2 of argv)) as PDF",
      "-e", "close d saving no",
      "-e", "end tell", "-e", "end run", src, outPdf,
    ], { encoding: "utf8", timeout: 180000 });
    if (r.status === 0 && existsSync(outPdf)) return outPdf;
  }

  // ③ 都没有可用引擎 → 让用户自己导 PDF(绝不安装 700MB 依赖)。
  fail(`NEED_PDF: 这是 ${extname(src)} 文件,本机暂时没有可直接调用的转换程序。` +
       `请在 PowerPoint / Keynote / WPS 里「导出为 PDF」,把那份 PDF 拖进来重发即可` +
       `(几秒钟、格式和原 PPT 一样、不需要安装任何东西)。`);
  return outPdf;
}

// PDF → NN.png(pymupdf)+ 顺带导出 source.txt(逐页文字,供专家整体解析、写完整稿)。返回文件名数组。
function pdfViaPymupdf(pdf, outDir, dpi) {
  const py = `
import fitz, sys, os
pdf, out, dpi = sys.argv[1], sys.argv[2], int(sys.argv[3])
doc = fitz.open(pdf)
n = doc.page_count
chunks = []
for i in range(n):
    page = doc.load_page(i)
    page.get_pixmap(dpi=dpi).save(os.path.join(out, f"{i+1:02d}.png"))
    chunks.append(f"===== 第 {i+1:02d} 页 =====\\n" + (page.get_text().strip() or "(本页无可提取文字,靠页面图理解)"))
with open(os.path.join(out, "source.txt"), "w", encoding="utf-8") as f:
    f.write("\\n\\n".join(chunks))
print(n)
`;
  const r = spawnSync("python3", ["-c", py, pdf, outDir, String(dpi)], { encoding: "utf8" });
  if (r.status !== 0) fail(`pymupdf 转图失败:${r.stderr || r.stdout}`);
  const n = parseInt(String(r.stdout).trim(), 10);
  return Array.from({ length: n }, (_, i) => `${String(i + 1).padStart(2, "0")}.png`);
}

// PDF → NN.png(pdftoppm 批量 + 重命名)。返回文件名数组。
function pdfViaPdftoppm(pdf, outDir, dpi) {
  const prefix = join(outDir, "__p");
  const r = spawnSync("pdftoppm", ["-r", String(dpi), "-png", pdf, prefix], { encoding: "utf8" });
  if (r.status !== 0) fail(`pdftoppm 转图失败:${r.stderr || r.stdout}`);
  // pdftoppm 产出 __p-1.png / __p-01.png(补零位数=总页数位数),按自然序重命名成 NN.png
  const raw = readdirSync(outDir)
    .filter((f) => /^__p-\d+\.png$/.test(f))
    .sort((a, b) => a.localeCompare(b, undefined, { numeric: true }));
  raw.forEach((f, i) => renameSync(join(outDir, f), join(outDir, `${String(i + 1).padStart(2, "0")}.png`)));
  return raw.map((_, i) => `${String(i + 1).padStart(2, "0")}.png`);
}

// 若 source.txt 还没有(pdftoppm 后端不产文字),用 pdftotext 兜底导出;都没有就跳过(靠页面图理解)。
function ensureSourceText(pdf, outDir) {
  if (existsSync(join(outDir, "source.txt"))) return;
  if (!have("pdftotext", ["-v"])) return;
  const raw = join(outDir, "__src.txt");
  const r = spawnSync("pdftotext", ["-layout", pdf, raw], { encoding: "utf8" });
  if (r.status === 0 && existsSync(raw)) renameSync(raw, join(outDir, "source.txt"));
}

function main() {
  const args = process.argv.slice(2);
  const get = (f) => { const i = args.indexOf(f); return i >= 0 ? args[i + 1] : undefined; };
  const src = args.find((a) => !a.startsWith("--") && a !== get("--out") && a !== get("--dpi"));
  const outDir = get("--out");
  const dpi = parseInt(get("--dpi") || String(DEFAULT_DPI), 10) || DEFAULT_DPI;
  if (!src || !outDir) fail('Usage: node doc-to-pages.mjs <文档路径> --out <JOBDIR> [--dpi 144]');
  const srcAbs = resolve(src);
  if (!existsSync(srcAbs)) fail(`找不到文档:${srcAbs}`);
  mkdirSync(outDir, { recursive: true });

  const ext = extname(srcAbs).toLowerCase();

  // **.pptx 走纯 JS 渲染**(自带 Chrome + @aiden0z/pptx-renderer):直接出逐页图 + source.txt,
  // 不转 PDF、不需要 Office/LibreOffice/授权/服务。谁的机器都能跑,这是 PPTX 的首选路径。
  if (ext === ".pptx") {
    const r = spawnSync(process.execPath, [join(HERE_DIR, "pptx-to-images.mjs"), srcAbs, "--out", outDir],
      { encoding: "utf8", maxBuffer: 1 << 24 });
    if (r.status !== 0) fail(r.stderr || r.stdout || "pptx-to-images 失败");
    process.stdout.write(String(r.stdout).trim());
    return;
  }

  let pdf = srcAbs;
  if (ext !== ".pdf") {
    // .ppt(老二进制)/.docx/.doc/.odp/.key → 只用**已装**的引擎转 PDF,绝不安装(见 officeToPdf)。
    if (![".ppt", ".odp", ".docx", ".doc", ".key"].includes(ext))
      fail(`不支持的文档类型 ${ext}(支持 pdf / pptx / ppt / docx / doc)`);
    pdf = officeToPdf(srcAbs, outDir);
  }

  const want = get("--backend");   // 可选强制后端(测试/兜底用):pymupdf | pdftoppm
  let backend, files;
  if (want === "pdftoppm" || (!want && !pymupdfAvailable() && have("pdftoppm", ["-v"]))) {
    if (!have("pdftoppm", ["-v"])) fail("指定了 --backend pdftoppm,但本机没有 poppler(pdftoppm)");
    backend = "pdftoppm"; files = pdfViaPdftoppm(pdf, outDir, dpi);
  } else if (want === "pymupdf" || pymupdfAvailable()) {
    if (!pymupdfAvailable()) fail("指定了 --backend pymupdf,但本机没有 python3+pymupdf(pip install pymupdf)");
    backend = "pymupdf"; files = pdfViaPymupdf(pdf, outDir, dpi);
  } else {
    fail(`没有可用的 PDF 转图后端。请二选一:\n` +
         `  · pip install pymupdf\n` +
         `  · 安装 poppler(mac: brew install poppler / linux: apt install poppler-utils)`);
  }

  if (!files.length) fail("转图后没有产出任何页,请检查文档是否为空/损坏");
  ensureSourceText(pdf, outDir);   // 保证有 source.txt(供整体解析);扫描件/无 pdftotext 时可能没有
  // 采样第一页尺寸(靠 file 命令探不出宽高,这里用 sips/identify 都不一定有 → 交给 render 阶段读)
  const first = join(outDir, files[0]);
  const bytes = existsSync(first) ? statSync(first).size : 0;
  const sourceTxt = join(outDir, "source.txt");
  const hasSource = existsSync(sourceTxt);
  process.stdout.write(JSON.stringify({
    pages: files.length, dpi, backend, files, first, firstBytes: bytes,
    sourceText: hasSource ? sourceTxt : null,
    sourceHint: hasSource ? "先读 source.txt 整体解析,再逐页看图" : "无可提取文字(扫描件),靠逐页读 NN.png 理解",
  }));
}

main();
