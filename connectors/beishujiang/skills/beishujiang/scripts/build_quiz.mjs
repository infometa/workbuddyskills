#!/usr/bin/env node
/**
 * 答题卡片构建脚本：把题目 JSON 注入 quiz-template.html，生成可直接打开的单文件答题卡片。
 *
 * 用法：
 *   node build_quiz.mjs <题目.json> [-o 输出.html] [--template 模板.html]
 */

import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const PLACEHOLDER = "/*__QUIZ_DATA__*/ null";
const VALID_TYPES = new Set([
  "single",
  "multiple",
  "true_false",
  "fill_blank",
  "short_answer",
]);

const TYPE_LABELS = {
  single: "单选",
  multiple: "多选",
  true_false: "判断",
  fill_blank: "填空",
  short_answer: "简答",
};

function usage() {
  return [
    "用法：node build_quiz.mjs <题目.json> [-o 输出.html] [--template 模板.html]",
    "",
    "选项：",
    "  -o, --output <路径>    输出 HTML 路径（默认与 JSON 同目录同名）",
    "  --template <路径>      模板路径（默认使用 Skill 内置模板）",
    "  -h, --help             显示帮助",
  ].join("\n");
}

function requireOptionValue(argv, index, option) {
  const value = argv[index + 1];
  if (!value || value.startsWith("-")) {
    throw new Error(`${option} 缺少路径参数`);
  }
  return value;
}

function parseArgs(argv) {
  let questions;
  let output;
  let template;

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];

    if (arg === "-h" || arg === "--help") {
      return { help: true };
    }
    if (arg === "-o" || arg === "--output") {
      output = requireOptionValue(argv, index, arg);
      index += 1;
      continue;
    }
    if (arg === "--template") {
      template = requireOptionValue(argv, index, arg);
      index += 1;
      continue;
    }
    if (arg.startsWith("-")) {
      throw new Error(`未知参数：${arg}`);
    }
    if (questions) {
      throw new Error(`只能指定一个题目 JSON 文件，多余参数：${arg}`);
    }
    questions = arg;
  }

  if (!questions) {
    throw new Error("缺少题目 JSON 文件路径");
  }

  return { help: false, questions, output, template };
}

function isMissingAnswer(question) {
  if (!("answer" in question)) return true;
  if (question.answer === "" || question.answer === null) return true;
  return Array.isArray(question.answer) && question.answer.length === 0;
}

function validate(data) {
  if (!data || typeof data !== "object" || Array.isArray(data) || !Array.isArray(data.questions)) {
    throw new Error("JSON 顶层必须是对象，且包含 questions 数组");
  }
  if (data.questions.length === 0) {
    throw new Error("questions 不能为空");
  }

  data.questions.forEach((question, zeroBasedIndex) => {
    const number = zeroBasedIndex + 1;
    if (!question || typeof question !== "object" || Array.isArray(question)) {
      throw new Error(`第${number}题必须是对象`);
    }
    if (!VALID_TYPES.has(question.type)) {
      throw new Error(
        `第${number}题 type 非法：${question.type}（应为 ${[...VALID_TYPES].sort().join(", ")} 之一）`,
      );
    }
    if (!question.question) {
      throw new Error(`第${number}题缺少 question 题干`);
    }
    if (isMissingAnswer(question)) {
      throw new Error(`第${number}题缺少 answer 答案`);
    }
    if (
      (question.type === "single" || question.type === "multiple")
      && (!Array.isArray(question.choices) || question.choices.length === 0)
    ) {
      throw new Error(`第${number}题为${question.type}，缺少 choices 选项`);
    }
    if (question.type === "single" && typeof question.answer !== "string") {
      throw new Error(`第${number}题单选题 answer 应为字母字符串，如 'B'`);
    }
    if (question.type === "multiple" && !Array.isArray(question.answer)) {
      throw new Error(`第${number}题多选题 answer 应为字母数组，如 ['A','C']`);
    }
    if (question.type === "true_false" && typeof question.answer !== "boolean") {
      throw new Error(`第${number}题判断题 answer 应为 true 或 false`);
    }
  });
}

function defaultOutputPath(questionsPath) {
  const parsed = path.parse(questionsPath);
  return path.join(parsed.dir, `${parsed.name}.html`);
}

function build(questionsPath, outputPath, templatePath) {
  const data = JSON.parse(fs.readFileSync(questionsPath, "utf8"));
  validate(data);

  const template = fs.readFileSync(templatePath, "utf8");
  if (!template.includes(PLACEHOLDER)) {
    throw new Error("模板中找不到数据占位符 /*__QUIZ_DATA__*/，模板可能已损坏");
  }

  const payload = JSON.stringify(data, null, 2).replaceAll("</", "<\\/");
  const html = template.replace(PLACEHOLDER, payload);
  fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  fs.writeFileSync(outputPath, html, "utf8");

  const counts = new Map();
  for (const question of data.questions) {
    counts.set(question.type, (counts.get(question.type) ?? 0) + 1);
  }
  const summary = [...counts.entries()]
    .map(([type, count]) => `${count}道${TYPE_LABELS[type] ?? type}`)
    .join("、");

  console.log(`[OK] 已生成 ${outputPath}`);
  console.log(
    `     标题：${data.title ?? "答题卡片"}｜共 ${data.questions.length} 题（${summary}）`,
  );
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) {
    console.log(usage());
    return;
  }

  const scriptDir = path.dirname(fileURLToPath(import.meta.url));
  const questionsPath = path.resolve(args.questions);
  if (!fs.existsSync(questionsPath)) {
    throw new Error(`找不到题目文件：${questionsPath}`);
  }

  const templatePath = args.template
    ? path.resolve(args.template)
    : path.resolve(scriptDir, "..", "templates", "frontend-template", "quiz-template.html");
  if (!fs.existsSync(templatePath)) {
    throw new Error(`找不到模板文件：${templatePath}`);
  }

  const outputPath = args.output
    ? path.resolve(args.output)
    : defaultOutputPath(questionsPath);
  build(questionsPath, outputPath, templatePath);
}

try {
  main();
} catch (error) {
  const message = error instanceof Error ? error.message : String(error);
  console.error(`[错误] ${message}`);
  process.exitCode = 1;
}
