#!/usr/bin/env node
import { readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

function fail(message) {
  throw new Error(message);
}

function nonemptyString(value, label) {
  if (typeof value !== "string" || value.trim().length === 0) fail(`${label} 必须是非空字符串`);
  return value;
}

export function normalizeClientPdf(input) {
  if (!input || typeof input !== "object" || Array.isArray(input)) fail("输入必须是逐页 JSON 对象");
  const { title, sourcePageCount, pages } = input;
  nonemptyString(title, "title");
  if (!Number.isSafeInteger(sourcePageCount) || sourcePageCount < 1 || sourcePageCount > 500) {
    fail("sourcePageCount 必须是原始 PDF/图片列表确认的 1–500 页总数");
  }
  if (!Array.isArray(pages) || pages.length !== sourcePageCount) {
    fail("pages 数量必须与原始文件的 sourcePageCount 完全一致；不能用合并文本猜测分页");
  }
  const normalized = pages.map((page, position) => {
    if (!page || typeof page !== "object" || Array.isArray(page)) fail(`pages[${position}] 必须是对象`);
    const { pageNumber, text, title: pageTitle, imageUrl } = page;
    if (!Number.isSafeInteger(pageNumber) || pageNumber < 0) fail(`pages[${position}].pageNumber 必须是非负整数`);
    if (typeof text !== "string" || text.length > 50000) fail(`第 ${pageNumber} 页 text 必须是最多 50000 字的字符串`);
    if (pageTitle !== undefined && (typeof pageTitle !== "string" || pageTitle.trim().length === 0)) {
      fail(`第 ${pageNumber} 页 title 必须是非空字符串`);
    }
    if (imageUrl !== undefined && (typeof imageUrl !== "string" || !/^(https:\/\/|data:image\/(?:png|jpeg|webp);base64,)/i.test(imageUrl))) {
      fail(`第 ${pageNumber} 页 imageUrl 只允许可信 HTTPS 或内嵌 PNG/JPEG/WebP 图片`);
    }
    return {
      pageNumber,
      index: pageNumber,
      chapterId: `client-page-${pageNumber}`,
      title: pageTitle ?? `第${pageNumber}页`,
      originalText: text,
      blanks: [],
      ...(imageUrl === undefined ? {} : { imageUrl }),
    };
  });
  normalized.sort((a, b) => a.pageNumber - b.pageNumber);
  const first = normalized[0]?.pageNumber;
  if (first !== 0 && first !== 1) fail("页码必须从 0 或 1 开始，不能丢失前面的页面");
  for (let index = 0; index < normalized.length; index += 1) {
    if (normalized[index].pageNumber !== first + index) fail("页码重复或缺失；请按原文件逐页重新提取，不能自动补页");
  }
  return {
    status: "SUCCEEDED",
    source: "client_fallback",
    collectionId: null,
    requiresConfirmation: true,
    title,
    confirmed: false,
    pages: normalized,
  };
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    const args = process.argv.slice(2);
    if (args.length !== 3 || args[1] !== "-o") fail("用法：node scripts/normalize_client_pdf.mjs <逐页输入.json> -o <规范化输出.json>");
    const input = JSON.parse(readFileSync(resolve(args[0]), "utf8"));
    const output = normalizeClientPdf(input);
    writeFileSync(resolve(args[2]), `${JSON.stringify(output, null, 2)}\n`, { encoding: "utf8", flag: "wx" });
    console.log(`[OK] 已规范化 ${output.pages.length} 页客户端解析结果；仍需用户确认 OCR`);
  } catch (error) {
    console.error(`[ERROR] ${error instanceof Error ? error.message : String(error)}`);
    process.exitCode = 1;
  }
}
