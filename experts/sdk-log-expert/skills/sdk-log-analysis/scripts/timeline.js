#!/usr/bin/env node
import crypto from 'node:crypto';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { Worker } from 'node:worker_threads';

import { parseArgs, fail } from './lib/args.js';
import {
  buildTimeline,
  buildTimelineFromEntries,
  detectLogType,
  groupLogEntries,
  loadApiData,
  renderTimelineMarkdown,
  summarizeEvents,
} from './lib/timeline.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SKILL_DIR = path.resolve(__dirname, '..');
const DEFAULT_OUTPUT_DIR = path.join(SKILL_DIR, 'tmp', 'sessions');
const DEFAULT_API_DIR = path.join(SKILL_DIR, 'data', 'api');
const WORKER_PATH = path.join(__dirname, 'lib', 'timeline-worker.js');
const DEFAULT_MAX_INPUT_BYTES = 200 * 1024 * 1024;
const BINARY_SAMPLE_BYTES = 8192;

function parsePositiveInteger(value, fallback) {
  if (value == null || value === '') return fallback;
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
}

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
  return `${(bytes / 1024 / 1024 / 1024).toFixed(2)} GB`;
}

function isProbablyBinary(file) {
  const ext = path.extname(file).toLowerCase();
  if (ext === '.clog' || ext === '.xlog') return true;
  const fd = fs.openSync(file, 'r');
  try {
    const buffer = Buffer.alloc(BINARY_SAMPLE_BYTES);
    const read = fs.readSync(fd, buffer, 0, buffer.length, 0);
    if (read === 0) return false;
    let suspicious = 0;
    for (let i = 0; i < read; i++) {
      const byte = buffer[i];
      if (byte === 0) return true;
      if (byte < 7 || (byte > 14 && byte < 32)) suspicious += 1;
    }
    return suspicious / read > 0.3;
  } finally {
    fs.closeSync(fd);
  }
}

function assertInputSafeForTimeline(files, args) {
  const maxInputBytes = parsePositiveInteger(args['max-input-bytes'], DEFAULT_MAX_INPUT_BYTES);
  const forceLarge = args['force-large'] === 'true';
  const allowBinary = args['allow-binary'] === 'true';

  for (const file of files) {
    if (!fs.existsSync(file)) fail(`日志文件不存在: ${file}`);
    const stat = fs.statSync(file);
    if (!allowBinary && isProbablyBinary(file)) {
      fail(`timeline.js 只接受解码后的文本日志：${file} 看起来是 .clog/.xlog 或二进制文件，请先用 analyze-local.js 或 clog decoder 解码。`);
    }
    if (!forceLarge && stat.size > maxInputBytes) {
      fail(`输入日志 ${file} 大小 ${formatBytes(stat.size)} 超过 timeline 默认上限 ${formatBytes(maxInputBytes)}。timeline 是 CPU/内存重任务，请先用 analyze-local.js 做有界初筛，或明确传 --force-large / 调大 --max-input-bytes。`);
    }
  }
}

function readInputLines(files) {
  const lines = [];
  const fileNames = [];
  const fileStats = [];
  for (const file of files) {
    if (!fs.existsSync(file)) fail(`日志文件不存在: ${file}`);
    const stat = fs.statSync(file);
    fileNames.push(path.basename(file));
    fileStats.push({ path: file, size: stat.size, mtimeMs: stat.mtimeMs });
    const text = fs.readFileSync(file, 'utf8');
    for (const line of text.split(/\r?\n/)) {
      const trimmed = line.trim();
      if (!trimmed) continue;
      try {
        const obj = JSON.parse(trimmed);
        lines.push(obj.log || obj.logstr || obj.log_str || obj.str_error_msg || obj.M || JSON.stringify(obj));
      } catch {
        lines.push(trimmed);
      }
    }
  }
  return { lines, fileNames, fileStats };
}

function hashFile(hash, file) {
  hash.update(file);
  hash.update('\0');
  hash.update(fs.readFileSync(file));
  hash.update('\0');
}

function computeCacheKey({ files, apiDir, options }) {
  const hash = crypto.createHash('sha256');
  hash.update(JSON.stringify({ version: 3, options }));
  for (const file of files) hashFile(hash, file);
  for (const name of ['log-rule.json', 'timeline.json', 'error-code.json']) {
    hashFile(hash, path.join(apiDir, name));
  }
  return hash.digest('hex').slice(0, 16);
}

function chunkEntries(entries, workerCount) {
  const count = Math.max(1, Math.min(workerCount, entries.length));
  const size = Math.ceil(entries.length / count);
  const chunks = [];
  for (let i = 0; i < entries.length; i += size) chunks.push(entries.slice(i, i + size));
  return chunks;
}

function runWorker(entries, options) {
  return new Promise((resolve, reject) => {
    const worker = new Worker(WORKER_PATH, { workerData: { entries, options } });
    worker.on('message', (message) => {
      if (!message.ok) reject(new Error(message.error));
      else resolve(message.events || []);
    });
    worker.on('error', reject);
    worker.on('exit', (code) => {
      if (code !== 0) reject(new Error(`timeline worker exited with ${code}`));
    });
  });
}

async function buildTimelineMaybeParallel(lines, { apiDir, fileNames, loopAllRule, workers }) {
  const apiData = loadApiData(apiDir);
  const detected = detectLogType(lines, { fileNames });
  const logType = detected.logType;
  const entries = groupLogEntries(lines, logType);
  const workerCount = Math.max(1, Number(workers || 1));

  if (workerCount <= 1 || entries.length < 2) {
    return buildTimeline(lines, { apiData, fileNames, loopAllRule });
  }

  const chunks = chunkEntries(entries, Math.min(workerCount, os.cpus().length || 2));
  const workerOptions = { apiDir, logType, loopAllRule };
  const events = (await Promise.all(chunks.map(chunk => runWorker(chunk, workerOptions)))).flat();
  const first = buildTimelineFromEntries([], workerOptions);
  const summarized = summarizeEvents(events);
  return {
    sdk: first.sdk,
    logType,
    detectReason: detected.reason,
    events: summarized.events,
    summary: summarized.summary,
    timeline: null,
    workers: chunks.length,
  };
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help || args.h || !args.logs) {
    process.stdout.write(`Usage:\n  node scripts/timeline.js --logs <file1[,file2]> [--api-dir <dir>] [--output-dir <dir>] [--workers <n>] [--loop-all-rule] [--no-cache] [--max-input-bytes <bytes>] [--force-large]\n`);
    return;
  }

  const files = String(args.logs).split(',').map(s => path.resolve(s.trim())).filter(Boolean);
  assertInputSafeForTimeline(files, args);
  const apiDir = path.resolve(args['api-dir'] || DEFAULT_API_DIR);
  const outBase = path.resolve(args['output-dir'] || DEFAULT_OUTPUT_DIR);
  const options = {
    loopAllRule: args['loop-all-rule'] === 'true',
    workers: Number(args.workers || 1),
  };
  const cacheKey = computeCacheKey({ files, apiDir, options });
  const runDir = path.join(outBase, 'timeline-cache', cacheKey);
  const timelineJson = path.join(runDir, 'timeline.json');
  const timelineMd = path.join(runDir, 'timeline.md');
  const manifestPath = path.join(runDir, 'manifest.json');

  if (args['no-cache'] !== 'true' && fs.existsSync(timelineJson) && fs.existsSync(timelineMd)) {
    const timeline = JSON.parse(fs.readFileSync(timelineJson, 'utf8'));
    process.stdout.write(`[cache]         hit\n`);
    process.stdout.write(`[run-dir]       ${runDir}\n`);
    process.stdout.write(`[timeline-md]   ${timelineMd}\n`);
    process.stdout.write(`[timeline-json] ${timelineJson}\n`);
    process.stdout.write(`[events]        ${timeline.events.length}\n`);
    return;
  }

  const { lines, fileNames, fileStats } = readInputLines(files);
  const timeline = await buildTimelineMaybeParallel(lines, { apiDir, fileNames, ...options });
  fs.mkdirSync(runDir, { recursive: true });
  fs.writeFileSync(timelineJson, JSON.stringify(timeline, null, 2), 'utf8');
  fs.writeFileSync(timelineMd, renderTimelineMarkdown(timeline), 'utf8');
  fs.writeFileSync(manifestPath, JSON.stringify({
    cacheKey,
    cache: 'miss',
    files: fileStats,
    apiDir,
    options,
    generatedAt: new Date().toISOString(),
    output: { timelineJson, timelineMd },
  }, null, 2), 'utf8');

  process.stdout.write(`[cache]         miss\n`);
  process.stdout.write(`[run-dir]       ${runDir}\n`);
  process.stdout.write(`[timeline-md]   ${timelineMd}\n`);
  process.stdout.write(`[timeline-json] ${timelineJson}\n`);
  process.stdout.write(`[events]        ${timeline.events.length}\n`);
}

main().catch(error => fail(error.message, 2));
