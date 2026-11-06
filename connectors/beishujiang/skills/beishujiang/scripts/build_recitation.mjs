#!/usr/bin/env node
/** Build the user's original Vue recitation page from confirmed OCR text. */
import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

function usage() {
  return "用法：node build_recitation.mjs <分页.json> [-o 输出目录]";
}

function parseArgs(args) {
  let input;
  let output;
  for (let index = 0; index < args.length; index += 1) {
    const arg = args[index];
    if (arg === "-h" || arg === "--help") return { help: true };
    if (arg === "-o" || arg === "--output") {
      output = args[++index];
      if (!output) throw new Error("-o 缺少输出路径");
      continue;
    }
    if (arg.startsWith("-")) throw new Error(`未知参数：${arg}`);
    if (input) throw new Error("只能指定一个分页 JSON 文件");
    input = arg;
  }
  if (!input) throw new Error("缺少分页 JSON 文件");
  return { help: false, input, output };
}

function validate(data) {
  if (!data || typeof data !== "object" || Array.isArray(data)) {
    throw new Error("顶层必须是对象");
  }
  if (data.confirmed !== true) {
    throw new Error("必须先向用户确认 OCR 原文，再设置 confirmed: true 构建页面");
  }
  if (typeof data.title !== "string" || !data.title.trim() || data.title.length > 200) {
    throw new Error("title 必须是非空且不超过 200 字的字符串");
  }
  if (!Array.isArray(data.pages) || data.pages.length === 0 || data.pages.length > 500) {
    throw new Error("pages 必须包含 1–500 页");
  }
  const seen = new Set();
  let previousPageNumber = -1;
  data.pages.forEach((page, index) => {
    const label = `第 ${index + 1} 项`;
    if (!page || typeof page !== "object" || Array.isArray(page)) {
      throw new Error(`${label}必须是对象`);
    }
    if (!Number.isSafeInteger(page.pageNumber) || page.pageNumber < 0 || seen.has(page.pageNumber)) {
      throw new Error(`${label}的 pageNumber 必须是未重复的非负整数`);
    }
    if (page.pageNumber <= previousPageNumber) {
      throw new Error("pages 必须按页码升序排列");
    }
    seen.add(page.pageNumber);
    previousPageNumber = page.pageNumber;
    if (page.index !== undefined && page.index !== page.pageNumber) {
      throw new Error(`${label}的 index 必须与 pageNumber 一致`);
    }
    if (page.chapterId !== undefined &&
      (typeof page.chapterId !== "string" || !page.chapterId.trim())) {
      throw new Error(`${label}的 chapterId 必须是非空字符串`);
    }
    if (page.title !== undefined &&
      (typeof page.title !== "string" || !page.title.trim() || page.title.length > 200)) {
      throw new Error(`${label}的 title 必须是非空且不超过 200 字的字符串`);
    }
    if (typeof page.originalText !== "string" || page.originalText.length > 50_000) {
      throw new Error(`${label}的 originalText 必须是最多 50000 字的字符串`);
    }
    if (!Array.isArray(page.blanks)) {
      throw new Error(`${label}缺少 blanks 数组`);
    }
    let previousEnd = 0;
    page.blanks.forEach((blank, blankIndex) => {
      if (
        !blank ||
        !Number.isSafeInteger(blank.start) ||
        !Number.isSafeInteger(blank.end) ||
        blank.start < previousEnd ||
        blank.end <= blank.start ||
        blank.end > page.originalText.length
      ) {
        throw new Error(`${label}的第 ${blankIndex + 1} 个 blanks 偏移无效或重叠`);
      }
      if (typeof blank.text === "string" &&
        page.originalText.slice(blank.start, blank.end) !== blank.text) {
        throw new Error(`${label}的第 ${blankIndex + 1} 个 blanks 与原文不一致`);
      }
      previousEnd = blank.end;
    });
    if (page.imageUrl !== undefined &&
      (typeof page.imageUrl !== "string" ||
        !/^(https:\/\/|data:image\/(?:png|jpeg|webp);base64,)/i.test(page.imageUrl))) {
      throw new Error(`${label}的 imageUrl 只允许 HTTPS 或内嵌 PNG/JPEG/WebP 图片`);
    }
  });
}

function copyTemplateDirectory(source, destination) {
  fs.mkdirSync(destination);
  for (const entry of fs.readdirSync(source, { withFileTypes: true })) {
    const from = path.join(source, entry.name);
    const to = path.join(destination, entry.name);
    if (entry.isDirectory()) {
      copyTemplateDirectory(from, to);
    } else if (entry.isFile()) {
      fs.copyFileSync(from, to, fs.constants.COPYFILE_EXCL);
    } else {
      throw new Error(`模板含不支持的文件类型：${from}`);
    }
  }
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) { console.log(usage()); return; }
  const inputPath = path.resolve(args.input);
  const data = JSON.parse(fs.readFileSync(inputPath, "utf8"));
  validate(data);

  const scriptDir = path.dirname(fileURLToPath(import.meta.url));
  const templateDir = path.resolve(scriptDir, "..", "templates", "recitation-original-dist");
  if (!fs.existsSync(path.join(templateDir, "index.html"))) {
    throw new Error("原版 Vue 页面尚未构建；请先构建 recitation-original-src");
  }
  const outputPath = args.output
    ? path.resolve(args.output)
    : path.join(path.dirname(inputPath), path.parse(inputPath).name + "-背书页面");
  if (fs.existsSync(outputPath)) {
    throw new Error(`输出目录已存在，拒绝覆盖：${outputPath}`);
  }
  const payload = JSON.stringify(data)
    .replace(/\u2028/g, "\\u2028")
    .replace(/\u2029/g, "\\u2029");
  fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  copyTemplateDirectory(templateDir, outputPath);
  fs.writeFileSync(path.join(outputPath, "material.js"), `window.__BSJ_RECITATION__ = ${payload};\n`, "utf8");
  // file:// blocks external module scripts in common browsers. Keep the original
  // compiled Vue code, but inline its entry bundle so index.html opens locally.
  const htmlPath = path.join(outputPath, "index.html");
  const html = fs.readFileSync(htmlPath, "utf8");
  const entry = /<script type="module" crossorigin src="\.\/assets\/([^"/]+\.js)"><\/script>/;
  const match = html.match(entry);
  if (!match) throw new Error("原版 Vue 页面缺少可内嵌的入口脚本");
  const bundlePath = path.join(outputPath, "assets", match[1]);
  const bundle = fs.readFileSync(bundlePath, "utf8").replace(/<\/script/gi, "<\\/script");
  const stylesheet = /<link rel="stylesheet" crossorigin href="\.\/assets\/([^"/]+\.css)">/;
  const cssMatch = html.match(stylesheet);
  if (!cssMatch) throw new Error("原版 Vue 页面缺少样式文件");
  const cssPath = path.join(outputPath, "assets", cssMatch[1]);
  const css = fs.readFileSync(cssPath, "utf8")
    .replace(/url\(\.\//g, "url(./assets/")
    .replace(/<\/style/gi, "<\\/style");
  const inlined = html
    .replace(entry, () => `<script type="module">\n${bundle}\n</script>`)
    .replace(stylesheet, () => `<style>\n${css}\n</style>`);
  fs.writeFileSync(htmlPath, inlined, "utf8");
  fs.unlinkSync(bundlePath);
  fs.unlinkSync(cssPath);
  console.log(`[OK] 已生成原版 Vue 背书页 ${path.join(outputPath, "index.html")}，共 ${data.pages.length} 页`);
}

try {
  main();
} catch (error) {
  console.error(`[错误] ${error instanceof Error ? error.message : String(error)}`);
  process.exitCode = 1;
}
