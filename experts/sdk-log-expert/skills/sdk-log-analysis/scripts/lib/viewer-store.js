// scripts/lib/viewer-store.js
// Local web-viewer store: lists decoded log files and serves their raw text,
// precomputed timeline, and room info. Heavy computation is lazy (per-file,
// on first request) and cached to disk so repeated requests are cheap.
// Node built-ins only; reuses timeline.js / roominfo.js / viewer-index.js.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { loadApiData, buildTimeline } from './timeline.js';
import { buildRoomInfo } from './roominfo.js';
import { makeFileId, buildLogIndexRecord } from './viewer-index.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DEFAULT_API_DIR = path.resolve(__dirname, '..', '..', 'data', 'api');
const DEFAULT_CACHE_DIR = path.resolve(__dirname, '..', '..', 'tmp', 'sessions', 'viewer-cache');

// Defensive bound: a pathologically huge log (hundreds of thousands of lines)
// could block the HTTP handler while buildTimeline runs. Cap the number of
// lines fed into the timeline; over-limit logs are computed on a prefix and
// flagged `truncated`.
const DEFAULT_MAX_TIMELINE_LINES = 200000;

// Decoded text logs we serve. Binary .clog/.xlog are skipped (not decoded).
const TEXT_LOG_EXTS = new Set(['.log', '.txt']);

function readLines(filePath) {
  return fs.readFileSync(filePath, 'utf8').split(/\r?\n/);
}

/**
 * Cache key for a file: <id>-<mtimeMs>-<size>. Any edit (mtime or size change)
 * invalidates the cached artifacts.
 */
function cacheKeyFor(filePath) {
  const stat = fs.statSync(filePath);
  return `${stat.mtimeMs}-${stat.size}`;
}

/**
 * Build a store object over the given record map. Shared by both factories.
 * @param {Map<string, object>} records  id -> record ({ id, filePath, logType, ... })
 * @param {{apiDir: string, cacheDir: string, maxTimelineLines: number}} opts
 */
function makeStore(records, { apiDir, cacheDir, maxTimelineLines }) {
  // Load apiData ONCE per store; reused for every getTimeline call (~800KB JSON).
  const apiData = loadApiData(apiDir);

  function cachePathFor(id, name) {
    return path.join(cacheDir, id, name);
  }

  // Read cached artifact if its meta key matches the current file; else
  // recompute via `compute`, persist, and return. `keyExtra` lets a caller
  // fold extra parameters (e.g. maxTimelineLines) into the cache key so a
  // different parameter doesn't return a stale artifact.
  function readOrCompute(record, name, compute, keyExtra = '') {
    const id = record.id;
    const dir = path.join(cacheDir, id);
    const metaPath = cachePathFor(id, name === 'meta.json' ? 'meta.json' : `${name}.meta.json`);
    const artifactPath = cachePathFor(id, name);
    const key = cacheKeyFor(record.filePath) + (keyExtra ? `-${keyExtra}` : '');

    let meta = null;
    try {
      meta = JSON.parse(fs.readFileSync(metaPath, 'utf8'));
    } catch {
      meta = null;
    }

    if (meta && meta.key === key && fs.existsSync(artifactPath)) {
      try {
        return JSON.parse(fs.readFileSync(artifactPath, 'utf8'));
      } catch {
        // fall through to recompute on corrupt cache
      }
    }

    const result = compute();
    fs.mkdirSync(dir, { recursive: true });
    fs.writeFileSync(artifactPath, `${JSON.stringify(result)}\n`);
    // meta.key reflects the file the artifacts were computed from. Stale
    // sibling artifacts for an old key are simply ignored (key won't match).
    fs.writeFileSync(metaPath, `${JSON.stringify({ key })}\n`);
    return result;
  }

  function getRecord(id) {
    return records.get(id);
  }

  return {
    listFiles() {
      return [...records.values()].map((r) => ({
        id: r.id,
        fileName: r.fileName,
        filePath: r.filePath,
        source: r.source,
        logType: r.logType,
        sdk: r.sdk,
        lines: r.lines,
        size: r.size,
        timeRange: r.timeRange,
      }));
    },

    getRaw(id) {
      const record = getRecord(id);
      if (!record) return undefined;
      return fs.readFileSync(record.filePath, 'utf8');
    },

    getTimeline(id) {
      const record = getRecord(id);
      if (!record) return undefined;
      return readOrCompute(record, 'timeline.json', () => {
        const lines = readLines(record.filePath);
        const truncated = lines.length > maxTimelineLines;
        const usedLines = truncated ? lines.slice(0, maxTimelineLines) : lines;
        const tl = buildTimeline(usedLines, { apiData, logType: record.logType, keepTags: true });
        const result = { sdk: tl.sdk, logType: tl.logType, events: tl.events, summary: tl.summary };
        if (truncated) {
          result.truncated = true;
          result.truncatedAt = maxTimelineLines;
        }
        return result;
      }, `mtl${maxTimelineLines}`);
    },

    getRooms(id) {
      const record = getRecord(id);
      if (!record) return undefined;
      return readOrCompute(record, 'rooms.json', () => {
        const lines = readLines(record.filePath);
        const { rooms, info } = buildRoomInfo(lines);
        return { rooms, info };
      });
    },
  };
}

/**
 * Build a store from a directory of decoded text log files (top-level only).
 * Skips binary .clog/.xlog (not decoded).
 * @param {string} dir
 * @param {{apiDir?: string, cacheDir?: string, maxTimelineLines?: number}} options
 */
export function createStoreFromDir(dir, options = {}) {
  const apiDir = options.apiDir || DEFAULT_API_DIR;
  const cacheDir = options.cacheDir || DEFAULT_CACHE_DIR;
  const maxTimelineLines = options.maxTimelineLines || DEFAULT_MAX_TIMELINE_LINES;

  const records = new Map();
  for (const name of fs.readdirSync(dir)) {
    const abs = path.resolve(dir, name);
    let stat;
    try {
      stat = fs.statSync(abs);
    } catch {
      continue;
    }
    if (!stat.isFile()) continue;
    if (!TEXT_LOG_EXTS.has(path.extname(name).toLowerCase())) continue;

    const record = buildLogIndexRecord(abs, { source: 'local' });
    record.id = makeFileId(abs);
    record.filePath = abs;
    records.set(record.id, record);
  }

  return makeStore(records, { apiDir, cacheDir, maxTimelineLines });
}

/**
 * Build a store from a viewer-index.json (array of records, each already has
 * id/filePath/logType metadata).
 * @param {string} indexPath
 * @param {{apiDir?: string, cacheDir?: string, maxTimelineLines?: number}} options
 */
export function createStoreFromIndex(indexPath, options = {}) {
  const apiDir = options.apiDir || DEFAULT_API_DIR;
  const cacheDir = options.cacheDir || DEFAULT_CACHE_DIR;
  const maxTimelineLines = options.maxTimelineLines || DEFAULT_MAX_TIMELINE_LINES;

  const arr = JSON.parse(fs.readFileSync(indexPath, 'utf8'));
  const records = new Map();
  for (const entry of Array.isArray(arr) ? arr : []) {
    if (!entry || !entry.id) continue;
    records.set(entry.id, entry);
  }

  return makeStore(records, { apiDir, cacheDir, maxTimelineLines });
}
