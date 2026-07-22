// scripts/lib/viewer-index.js
// Shared helper for the viewer-index.json file. Node built-ins only.
import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import { detectLogType, parseLogLine } from './timeline.js';

/**
 * Stable short id for a file path: first 12 hex chars of its sha1.
 * @param {string} filePath
 * @returns {string}
 */
export function makeFileId(filePath) {
  return crypto.createHash('sha1').update(String(filePath)).digest('hex').slice(0, 12);
}

/**
 * Read the index array at idxPath (or [] if missing/invalid), upsert each
 * record by its `id` field, write merged pretty JSON back, return merged array.
 * @param {string} idxPath
 * @param {Array<{id: string}>} records
 * @returns {Array<object>}
 */
export function upsertViewerIndex(idxPath, records) {
  let index = [];
  try {
    const parsed = JSON.parse(fs.readFileSync(idxPath, 'utf8'));
    if (Array.isArray(parsed)) index = parsed;
  } catch {
    index = [];
  }

  for (const record of records) {
    const i = index.findIndex((entry) => entry && entry.id === record.id);
    if (i >= 0) index[i] = record;
    else index.push(record);
  }

  fs.mkdirSync(path.dirname(idxPath), { recursive: true });
  fs.writeFileSync(idxPath, `${JSON.stringify(index, null, 2)}\n`);
  return index;
}

/**
 * Build a viewer-index record for a decoded text log file by sniffing its head.
 * Reads up to ~256KB from the file head for type detection + start time.
 * @param {string} filePath
 * @param {{source: string, sdkAppId?: string, userId?: string, roomId?: string}} opts
 * @returns {object}
 */
export function buildLogIndexRecord(filePath, { source, sdkAppId = '', userId = '', roomId = '' } = {}) {
  const stat = fs.statSync(filePath);
  const fd = fs.openSync(filePath, 'r');
  let headText = '';
  try {
    const buf = Buffer.alloc(Math.min(256 * 1024, stat.size));
    const read = fs.readSync(fd, buf, 0, buf.length, 0);
    headText = buf.toString('utf8', 0, read);
  } finally {
    fs.closeSync(fd);
  }
  const headLines = headText.split(/\r?\n/);
  const fileName = path.basename(filePath);
  const { logType } = detectLogType(headLines, { fileNames: [fileName] });
  const firstLine = headLines.find((l) => l.trim()) || '';
  const start = parseLogLine(firstLine).timeText || '';
  return {
    id: makeFileId(path.resolve(filePath)),
    filePath: path.resolve(filePath),
    fileName,
    source,
    logType,
    sdkAppId: String(sdkAppId || ''),
    userId: String(userId || ''),
    roomId: String(roomId || ''),
    size: stat.size,
    timeRange: { start, end: '' },
  };
}
