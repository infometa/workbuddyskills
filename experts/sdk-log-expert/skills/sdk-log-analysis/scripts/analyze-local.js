#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import readline from 'node:readline';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

import { parseArgs, fail, makeSessionId, isPreviewEnabled } from './lib/args.js';
import { decodeFile } from './lib/decoder.js';
import { upsertViewerIndex, buildLogIndexRecord } from './lib/viewer-index.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SKILL_DIR = path.resolve(__dirname, '..');
const DEFAULT_OUTPUT_DIR = path.join(SKILL_DIR, 'tmp', 'sessions');
const DEFAULT_API_DIR = path.join(SKILL_DIR, 'data', 'api');
const TIMELINE_SCRIPT = path.join(__dirname, 'timeline.js');
const DEFAULT_MAX_TIMELINE_BYTES = 200 * 1024 * 1024;
const DEFAULT_TIMELINE_TIMEOUT_MS = 120_000;
const DEFAULT_DECODE_TIMEOUT_MS = 300_000;
const DEFAULT_TAIL_SCAN_BYTES = 16 * 1024 * 1024;
const BINARY_SAMPLE_BYTES = 8192;

function parsePositiveInteger(value, fallback) {
  if (value == null || value === '') return fallback;
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed > 0 ? Math.floor(parsed) : fallback;
}

function boolArg(args, name, fallback = false) {
  if (args[name] == null) return fallback;
  return args[name] === 'true';
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

async function readHeadLines(file, count) {
  if (count <= 0) return [];
  const input = fs.createReadStream(file, { encoding: 'utf8' });
  const rl = readline.createInterface({ input, crlfDelay: Infinity });
  const lines = [];
  for await (const line of rl) {
    lines.push(line);
    if (lines.length >= count) {
      rl.close();
      input.destroy();
      break;
    }
  }
  return lines;
}

function readTailLines(file, count, maxScanBytes) {
  if (count <= 0) return [];
  const stat = fs.statSync(file);
  const fd = fs.openSync(file, 'r');
  const chunks = [];
  let position = stat.size;
  let scanned = 0;
  try {
    while (position > 0 && scanned < maxScanBytes) {
      const chunkSize = Math.min(64 * 1024, position, maxScanBytes - scanned);
      position -= chunkSize;
      const buffer = Buffer.alloc(chunkSize);
      const bytesRead = fs.readSync(fd, buffer, 0, chunkSize, position);
      if (bytesRead <= 0) break;
      chunks.unshift(buffer.subarray(0, bytesRead));
      scanned += bytesRead;
      const text = Buffer.concat(chunks).toString('utf8');
      const lines = text.split(/\r?\n/);
      if (lines.length > count + 1) break;
    }
  } finally {
    fs.closeSync(fd);
  }
  const text = Buffer.concat(chunks).toString('utf8');
  const lines = text.split(/\r?\n/);
  if (lines.at(-1) === '') lines.pop();
  return lines.slice(-count);
}

async function writeBoundedSample(inputPath, outputPath, { headLines, tailLines, tailScanBytes }) {
  const head = await readHeadLines(inputPath, headLines);
  const tail = readTailLines(inputPath, tailLines, tailScanBytes);
  const joined = [...head, ...tail].filter(line => line.trim()).join('\n');
  fs.writeFileSync(outputPath, `${joined}\n`, 'utf8');
  return { path: outputPath, headLines: head.length, tailLines: tail.length, bytes: fs.statSync(outputPath).size };
}

function runTimeline(logPath, { outputDir, apiDir, workers, loopAllRule, timeoutMs }) {
  const args = [
    TIMELINE_SCRIPT,
    '--logs', logPath,
    '--output-dir', outputDir,
    '--api-dir', apiDir,
    '--workers', String(workers),
  ];
  if (loopAllRule) args.push('--loop-all-rule');
  const result = spawnSync(process.execPath, args, {
    cwd: SKILL_DIR,
    encoding: 'utf8',
    timeout: timeoutMs,
  });
  if (result.error) {
    throw new Error(`timeline failed: ${result.error.message}`);
  }
  if (result.status !== 0) {
    const details = [result.stderr, result.stdout].filter(Boolean).join('\n').trim();
    throw new Error(`timeline exited ${result.status}: ${details}`);
  }
  return {
    stdout: result.stdout,
    timelineMd: result.stdout.match(/^\[timeline-md\]\s+(.+)$/m)?.[1] || null,
    timelineJson: result.stdout.match(/^\[timeline-json\]\s+(.+)$/m)?.[1] || null,
    events: Number(result.stdout.match(/^\[events\]\s+(\d+)$/m)?.[1] || 0),
  };
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help || args.h || !args.logs) {
    process.stdout.write(`Usage:\n  node scripts/analyze-local.js --logs <file> [--output-dir <dir>] [--max-timeline-bytes <bytes>] [--force-timeline] [--no-timeline] [--workers <n>]\n`);
    return;
  }

  const inputPath = path.resolve(String(args.logs));
  if (!fs.existsSync(inputPath)) fail(`日志文件不存在: ${inputPath}`);

  const outBase = path.resolve(args['output-dir'] || DEFAULT_OUTPUT_DIR);
  const runDir = path.join(outBase, makeSessionId('local-analysis'));
  fs.mkdirSync(runDir, { recursive: true });

  const maxTimelineBytes = parsePositiveInteger(args['max-timeline-bytes'], DEFAULT_MAX_TIMELINE_BYTES);
  const timelineTimeoutMs = parsePositiveInteger(args['timeline-timeout-ms'], DEFAULT_TIMELINE_TIMEOUT_MS);
  const decodeTimeoutMs = parsePositiveInteger(args['decode-timeout-ms'], DEFAULT_DECODE_TIMEOUT_MS);
  const workers = parsePositiveInteger(args.workers, Math.min(2, Math.max(1, 2)));
  const headLines = parsePositiveInteger(args['head-lines'], 5000);
  const tailLines = parsePositiveInteger(args['tail-lines'], 5000);
  const tailScanBytes = parsePositiveInteger(args['tail-scan-bytes'], DEFAULT_TAIL_SCAN_BYTES);
  const apiDir = path.resolve(args['api-dir'] || DEFAULT_API_DIR);
  const forceTimeline = boolArg(args, 'force-timeline', false);
  const noTimeline = boolArg(args, 'no-timeline', false);
  const loopAllRule = boolArg(args, 'loop-all-rule', true);

  const inputStat = fs.statSync(inputPath);
  const inputBinary = isProbablyBinary(inputPath);
  let textLogPath = inputPath;
  let decoded = null;

  if (inputBinary) {
    const decodedPath = path.join(runDir, `${path.basename(inputPath)}.log`);
    decoded = decodeFile(inputPath, decodedPath, { skillDir: SKILL_DIR, timeoutMs: decodeTimeoutMs });
    textLogPath = decodedPath;
  }

  const textStat = fs.statSync(textLogPath);
  const manifest = {
    input: { path: inputPath, size: inputStat.size, sizeText: formatBytes(inputStat.size), binary: inputBinary },
    decoded: decoded ? { ...decoded, size: textStat.size, sizeText: formatBytes(textStat.size) } : null,
    textLog: { path: textLogPath, size: textStat.size, sizeText: formatBytes(textStat.size) },
    limits: { maxTimelineBytes, timelineTimeoutMs, decodeTimeoutMs, headLines, tailLines, tailScanBytes },
    sample: null,
    timeline: { mode: 'skipped', reason: noTimeline ? 'no-timeline' : null },
    generatedAt: new Date().toISOString(),
  };

  if (!noTimeline) {
    let timelineInput = textLogPath;
    let mode = 'full';
    let reason = 'within-limit';
    if (textStat.size > maxTimelineBytes && !forceTimeline) {
      mode = 'sample';
      reason = 'input-too-large';
      const samplePath = path.join(runDir, `${path.basename(textLogPath)}.sample.log`);
      manifest.sample = await writeBoundedSample(textLogPath, samplePath, { headLines, tailLines, tailScanBytes });
      timelineInput = samplePath;
    } else if (textStat.size > maxTimelineBytes && forceTimeline) {
      reason = 'forced-large-input';
    }

    const timeline = runTimeline(timelineInput, {
      outputDir: runDir,
      apiDir,
      workers,
      loopAllRule,
      timeoutMs: timelineTimeoutMs,
    });
    manifest.timeline = { mode, reason, input: timelineInput, ...timeline };
  }

  const manifestPath = path.join(runDir, 'manifest.json');
  fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2), 'utf8');

  if (isPreviewEnabled()) {
    const indexRecord = buildLogIndexRecord(textLogPath, { source: 'local' });
    upsertViewerIndex(path.join(runDir, 'viewer-index.json'), [indexRecord]);
  }

  process.stdout.write(`[run-dir]       ${runDir}\n`);
  process.stdout.write(`[input]         ${inputPath}\n`);
  if (decoded) process.stdout.write(`[decoded-log]   ${textLogPath}\n`);
  process.stdout.write(`[text-log]      ${textLogPath}\n`);
  process.stdout.write(`[mode]          ${manifest.timeline.mode}\n`);
  if (manifest.sample) process.stdout.write(`[sample-log]    ${manifest.sample.path}\n`);
  if (manifest.timeline.timelineMd) process.stdout.write(`[timeline-md]   ${manifest.timeline.timelineMd}\n`);
  if (manifest.timeline.timelineJson) process.stdout.write(`[timeline-json] ${manifest.timeline.timelineJson}\n`);
  process.stdout.write(`[manifest]      ${manifestPath}\n`);
  if (manifest.timeline.mode === 'sample') {
    process.stdout.write(`[note]          input too large for full timeline; generated bounded head/tail sample timeline. Use --force-timeline only when you intentionally accept the CPU cost.\n`);
  }
}

main().catch(error => fail(error.message, 2));
