#!/usr/bin/env node
// scripts/evidence.js
// Render selected log lines as safe Markdown evidence blocks. This script does
// not infer conclusions; it only sanitizes untrusted log text for chat output.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { fail, parseArgs } from './lib/args.js';
import { safeCodeBlock, safeEvidenceLine } from './lib/safe-output.js';

export function parseLineRanges(input) {
  const selected = new Set();
  for (const part of String(input || '').split(',')) {
    const token = part.trim();
    if (!token) continue;
    const range = token.match(/^(\d+)\s*-\s*(\d+)$/);
    if (range) {
      const a = Number(range[1]);
      const b = Number(range[2]);
      const start = Math.min(a, b);
      const end = Math.max(a, b);
      for (let line = start; line <= end; line++) selected.add(line);
      continue;
    }
    const line = Number(token);
    if (Number.isInteger(line) && line > 0) selected.add(line);
  }
  return [...selected].sort((a, b) => a - b);
}

function positiveInt(value, fallback) {
  if (value == null || value === '') return fallback;
  const n = Number(value);
  return Number.isFinite(n) && n >= 0 ? Math.floor(n) : fallback;
}

function expandWithContext(lineNumbers, context) {
  const selected = new Set();
  for (const line of lineNumbers) {
    for (let i = Math.max(1, line - context); i <= line + context; i++) selected.add(i);
  }
  return [...selected].sort((a, b) => a - b);
}

export function buildEvidenceBlock({
  logPath,
  lines,
  context = 0,
  maxLines = 80,
  maxLineChars = 1000,
} = {}) {
  if (!logPath) throw new Error('buildEvidenceBlock requires logPath');
  if (!fs.existsSync(logPath)) throw new Error(`日志文件不存在: ${logPath}`);

  const requested = parseLineRanges(lines);
  if (requested.length === 0) throw new Error('必须提供 --lines，例如 123,130-135');

  const allLines = fs.readFileSync(logPath, 'utf8').split(/\r?\n/);
  const expanded = expandWithContext(requested, context).filter(line => line <= allLines.length);
  const shown = expanded.slice(0, maxLines);
  const output = shown.map(line => safeEvidenceLine(line, allLines[line - 1] || '', { maxChars: maxLineChars }));
  const omitted = expanded.length - shown.length;
  if (omitted > 0) output.push(`... omitted ${omitted} line(s) by --max-lines=${maxLines}`);

  return safeCodeBlock(output.join('\n'), 'text');
}

function usage() {
  return `Usage:\n  node scripts/evidence.js --log <decoded.log> --lines <line[,start-end]> [--context N] [--max-lines N] [--max-line-chars N]\n`;
}

const isCli = process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (isCli) {
  const args = parseArgs(process.argv.slice(2));
  if (args.help || args.h || !args.log || !args.lines) {
    process.stdout.write(usage());
    process.exit(args.help || args.h ? 0 : 1);
  }

  try {
    const block = buildEvidenceBlock({
      logPath: path.resolve(String(args.log)),
      lines: String(args.lines),
      context: positiveInt(args.context, 0),
      maxLines: positiveInt(args['max-lines'], 80),
      maxLineChars: positiveInt(args['max-line-chars'], 1000),
    });
    process.stdout.write(`${block}\n`);
  } catch (error) {
    fail(error.message, 2);
  }
}
