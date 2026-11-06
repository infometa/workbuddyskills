#!/usr/bin/env node
// 从客户端已经核对过的正文中按偏移提取出题材料；不联网或生成原文。
import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const MAX_TEXT_LENGTH = 50_000;
const MIN_TEXT_LENGTH = 200;

function nonempty(value) {
  return typeof value === "string" && value.trim().length > 0;
}

export function prepareQuestionMaterial(data) {
  if (!data || typeof data !== "object" || Array.isArray(data)) {
    throw new Error("输入必须是对象");
  }
  const { workTitle, mode, target, selections } = data;
  if (!nonempty(workTitle)) throw new Error("缺少作品名称 workTitle");
  if (mode !== "chapter" && mode !== "work") {
    throw new Error("mode 必须是 chapter 或 work");
  }
  if (mode === "chapter" && !nonempty(target)) {
    throw new Error("章节模式缺少目标章节/情节 target");
  }
  if (!Array.isArray(selections) || selections.length === 0) {
    throw new Error("缺少已核对的原文片段 selections");
  }

  const excerpts = selections.map((selection, index) => {
    if (!selection || typeof selection !== "object" || Array.isArray(selection)) {
      throw new Error(`第 ${index + 1} 段格式无效`);
    }
    const { sourceRef, section, sourceText, start, end } = selection;
    if (!nonempty(sourceRef) || !nonempty(section) || !nonempty(sourceText)) {
      throw new Error(`第 ${index + 1} 段缺少来源、章节或来源正文`);
    }
    if (!Number.isSafeInteger(start) || !Number.isSafeInteger(end)
      || start < 0 || end <= start || end > sourceText.length) {
      throw new Error(`第 ${index + 1} 段截取偏移无效`);
    }
    const text = sourceText.slice(start, end);
    if (!text.trim()) throw new Error(`第 ${index + 1} 段截取结果为空`);
    return {
      text,
      sourceRef: sourceRef.trim(),
      section: section.trim(),
      start,
      end,
    };
  });

  if (mode === "work" && new Set(excerpts.map((item) => item.section)).size < 2) {
    throw new Error("整部作品出题至少选择两个不同章节/情节的原文");
  }

  const text = excerpts.map((item) => item.text).join("\n\n");
  if (text.trim().length < MIN_TEXT_LENGTH) {
    throw new Error("原文片段太短，不能只传作品名称或章节标题");
  }
  if (text.length > MAX_TEXT_LENGTH) {
    throw new Error(`出题文本超过 ${MAX_TEXT_LENGTH} 字符上限，请缩小截取范围`);
  }

  return {
    workTitle: workTitle.trim(),
    mode,
    ...(mode === "chapter" ? { target: target.trim() } : {}),
    text,
    excerpts: excerpts.map(({ sourceRef, section, start, end }) => ({
      sourceRef, section, start, end,
    })),
  };
}

function main() {
  const [input, outputFlag, output] = process.argv.slice(2);
  if (process.argv.includes("-h") || process.argv.includes("--help")) {
    process.stdout.write("用法：node prepare_question_material.mjs <已核对材料.json> -o <出题材料.json>\n");
    return;
  }
  if (!input || outputFlag !== "-o" || !output) {
    throw new Error("用法：node prepare_question_material.mjs <已核对材料.json> -o <出题材料.json>");
  }
  if (path.resolve(input) === path.resolve(output)) {
    throw new Error("输出文件不能覆盖输入文件");
  }
  const data = JSON.parse(fs.readFileSync(input, "utf8"));
  const result = prepareQuestionMaterial(data);
  fs.mkdirSync(path.dirname(path.resolve(output)), { recursive: true });
  fs.writeFileSync(output, JSON.stringify(result, null, 2) + "\n", "utf8");
  process.stdout.write(`已准备 ${result.text.length} 字符、${result.excerpts.length} 段原文；仅将输出文件的 text 传给 MCP。\n`);
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    main();
  } catch (error) {
    process.stderr.write(`材料准备失败：${error instanceof Error ? error.message : String(error)}\n`);
    process.exitCode = 1;
  }
}
