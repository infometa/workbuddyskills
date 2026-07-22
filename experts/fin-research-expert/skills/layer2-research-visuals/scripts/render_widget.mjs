#!/usr/bin/env node

import { readFile, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";

const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));
const REFERENCES_DIR = path.resolve(SCRIPT_DIR, "../references");
const PAYLOAD_TOKEN = "__TONGZHOU_CHART_PAYLOAD__";
const MAX_INPUT_BYTES = 512_000;

const RENDERERS = new Map([
  ["workbuddy-kline-svg/2", { file: "widget-kline-runtime.md", schemas: ["chart-evidence/1"], types: ["candlestick_volume"] }],
  ["workbuddy-trend-svg/2", { file: "widget-trend-runtime.md", schemas: ["chart-evidence/1", "research-visual/1"], types: ["line"] }],
  ["workbuddy-event-svg/2", { file: "widget-event-runtime.md", schemas: ["chart-evidence/1"], types: ["event_return_bar"] }],
  ["workbuddy-compare-svg/1", { file: "widget-compare-runtime.md", schemas: ["research-visual/1"], types: ["column", "grouped_column"] }],
  ["workbuddy-combo-svg/1", { file: "widget-combo-runtime.md", schemas: ["research-visual/1"], types: ["line_column"] }],
  ["workbuddy-radar-svg/1", { file: "widget-radar-runtime.md", schemas: ["research-visual/1"], types: ["radar"] }],
]);

function fail(message) {
  process.stderr.write(`render_widget: ${message}\n`);
  process.exitCode = 2;
}

function parseArguments(argv) {
  const options = { input: "-", output: "-", format: "show-widget" };
  for (let index = 0; index < argv.length; index += 1) {
    const value = argv[index];
    if (!["--input", "--output", "--format"].includes(value)) {
      throw new Error(`unsupported argument: ${value}`);
    }
    const next = argv[index + 1];
    if (!next) throw new Error(`missing value for ${value}`);
    options[value.slice(2)] = next;
    index += 1;
  }
  if (!["show-widget", "widget-code"].includes(options.format)) {
    throw new Error("--format must be show-widget or widget-code");
  }
  return options;
}

async function readInput(inputPath) {
  const raw = inputPath === "-"
    ? await new Promise((resolve, reject) => {
        const chunks = [];
        let size = 0;
        process.stdin.on("data", chunk => {
          size += chunk.length;
          if (size > MAX_INPUT_BYTES) {
            reject(new Error("input exceeds 512000 bytes"));
            process.stdin.destroy();
            return;
          }
          chunks.push(chunk);
        });
        process.stdin.on("end", () => resolve(Buffer.concat(chunks).toString("utf8")));
        process.stdin.on("error", reject);
      })
    : await readFile(inputPath, "utf8");
  if (Buffer.byteLength(raw, "utf8") > MAX_INPUT_BYTES) {
    throw new Error("input exceeds 512000 bytes");
  }
  return raw;
}

function validatePayload(payload) {
  if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
    throw new Error("payload must be a JSON object");
  }
  const renderer = RENDERERS.get(payload.renderer_version);
  if (!renderer) throw new Error("renderer_version is unsupported");
  if (!renderer.schemas.includes(payload.schema_version)) {
    throw new Error("schema_version does not match renderer_version");
  }
  if (!renderer.types.includes(payload.chart_type)) {
    throw new Error("chart_type does not match renderer_version");
  }
  if (!payload.evidence || typeof payload.evidence !== "object" || Array.isArray(payload.evidence)) {
    throw new Error("evidence must be a JSON object");
  }
  return renderer;
}

function extractFragment(markdown) {
  const match = markdown.match(/```html\n(<svg[\s\S]+?<\/script>)\n```/);
  if (!match) throw new Error("renderer template does not contain a Widget fragment");
  const fragment = match[1];
  if (fragment.split(PAYLOAD_TOKEN).length !== 2) {
    throw new Error("renderer template must contain one payload token");
  }
  if (!fragment.includes('type="application/json"')) {
    throw new Error("renderer template must isolate payload from executable JavaScript");
  }
  return fragment;
}

function safeJson(payload) {
  return JSON.stringify(payload)
    .replaceAll("<", "\\u003c")
    .replaceAll(">", "\\u003e")
    .replaceAll("&", "\\u0026");
}

async function render(payload, format) {
  const renderer = validatePayload(payload);
  const markdown = await readFile(path.join(REFERENCES_DIR, renderer.file), "utf8");
  const widgetCode = extractFragment(markdown).replace(PAYLOAD_TOKEN, safeJson(payload));
  if (!widgetCode.startsWith("<svg") || !widgetCode.endsWith("</script>")) {
    throw new Error("rendered Widget boundary is invalid");
  }
  if (format === "widget-code") return widgetCode;
  const rawTitle = typeof payload.title === "string" && payload.title.trim()
    ? payload.title.trim()
    : "同舟金融研究图表";
  return JSON.stringify({ title: rawTitle.slice(0, 80), widget_code: widgetCode });
}

async function main() {
  const options = parseArguments(process.argv.slice(2));
  const raw = await readInput(options.input);
  let payload;
  try {
    payload = JSON.parse(raw);
  } catch {
    throw new Error("input is not valid JSON");
  }
  const output = await render(payload, options.format);
  if (options.output === "-") {
    process.stdout.write(`${output}\n`);
  } else {
    await writeFile(options.output, `${output}\n`, "utf8");
  }
}

main().catch(error => fail(error instanceof Error ? error.message : "unexpected renderer failure"));
