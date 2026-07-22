// scripts/serve-viewer.js
// Zero-dependency HTTP server for the SDK log viewer. Serves a JSON API over a
// viewer-store plus static frontend assets. Node built-ins only.
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { createStoreFromDir, createStoreFromIndex } from './lib/viewer-store.js';
import {
  listServers, findServer, registerServer, unregisterByPid, stopServers, targetKey,
} from './lib/viewer-registry.js';
import { isPreviewEnabled } from './lib/args.js';

if (!isPreviewEnabled()) {
  process.stdout.write('[viewer] 预览已通过 SDK_LOG_PREVIEW=0 禁用（云端 agent 平台模式）\n');
  process.stdout.write('[viewer] 分析结论将以文本形式直接返回给用户\n');
  process.exit(0);
}

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DEFAULT_VIEWER_DIR = path.resolve(__dirname, '..', 'viewer');

const CONTENT_TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.map': 'application/json; charset=utf-8',
  '.woff2': 'font/woff2',
  '.ttf': 'font/ttf',
};

function contentTypeFor(filePath) {
  return CONTENT_TYPES[path.extname(filePath).toLowerCase()] || 'application/octet-stream';
}

function sendJson(res, status, body) {
  const text = JSON.stringify(body);
  res.writeHead(status, { 'Content-Type': 'application/json; charset=utf-8' });
  res.end(text);
}

function sendText(res, status, text, type = 'text/plain; charset=utf-8') {
  res.writeHead(status, { 'Content-Type': type });
  res.end(text);
}

const API_FILE_RE = /^\/api\/file\/([^/]+)\/(raw|timeline|rooms)$/;

/**
 * Serve a static asset from viewerDir for the given URL pathname.
 * Path-traversal-safe: the resolved target must stay within viewerDir.
 * SPA fallback: unknown paths fall back to index.html when present.
 */
function serveStatic(res, viewerDir, pathname) {
  const indexHtml = path.join(viewerDir, 'index.html');

  // Map '/' → index.html.
  let rel = decodeURIComponent(pathname);
  if (rel === '/' || rel === '') rel = '/index.html';

  // Resolve safely under viewerDir.
  const target = path.resolve(viewerDir, `.${rel}`);
  const withinViewer = target === viewerDir || target.startsWith(viewerDir + path.sep);
  if (!withinViewer) {
    sendText(res, 403, 'Forbidden');
    return;
  }

  if (fs.existsSync(target) && fs.statSync(target).isFile()) {
    res.writeHead(200, { 'Content-Type': contentTypeFor(target) });
    res.end(fs.readFileSync(target));
    return;
  }

  // SPA fallback so client-side routing works.
  if (fs.existsSync(indexHtml) && fs.statSync(indexHtml).isFile()) {
    res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
    res.end(fs.readFileSync(indexHtml));
    return;
  }

  sendText(res, 404, 'Not Found');
}

function makeHandler(store, viewerDir) {
  const base = 'http://127.0.0.1';
  return (req, res) => {
    let pathname;
    try {
      pathname = new URL(req.url, base).pathname;
    } catch {
      sendText(res, 400, 'Bad Request');
      return;
    }

    // GET /api/files
    if (pathname === '/api/files') {
      sendJson(res, 200, store.listFiles());
      return;
    }

    // GET /api/file/:id/(raw|timeline|rooms)
    const m = API_FILE_RE.exec(pathname);
    if (m) {
      const id = m[1];
      const kind = m[2];

      if (kind === 'raw') {
        const raw = store.getRaw(id);
        if (raw === undefined) {
          sendText(res, 404, 'Not Found');
          return;
        }
        sendText(res, 200, raw);
        return;
      }

      // timeline / rooms: gate existence via in-memory listFiles().
      const exists = store.listFiles().some((f) => f.id === id);
      if (!exists) {
        sendText(res, 404, 'Not Found');
        return;
      }
      const result = kind === 'timeline' ? store.getTimeline(id) : store.getRooms(id);
      sendJson(res, 200, result);
      return;
    }

    // Everything else → static assets.
    serveStatic(res, viewerDir, pathname);
  };
}

/**
 * Start the viewer HTTP server.
 * @param {{dir?: string, index?: string, port?: number, viewerDir?: string,
 *          apiDir?: string, cacheDir?: string}} [opts]
 * @returns {Promise<{server: http.Server, port: number, url: string}>}
 */
export async function startServer({
  dir, index, port = 0, viewerDir, apiDir, cacheDir, autoPort = false, maxPortTries = 20,
} = {}) {
  const storeOpts = {};
  if (apiDir !== undefined) storeOpts.apiDir = apiDir;
  if (cacheDir !== undefined) storeOpts.cacheDir = cacheDir;

  let store;
  if (index) store = createStoreFromIndex(index, storeOpts);
  else if (dir) store = createStoreFromDir(dir, storeOpts);
  else throw new Error('startServer requires either `dir` or `index`');

  const resolvedViewerDir = viewerDir || DEFAULT_VIEWER_DIR;
  const server = http.createServer(makeHandler(store, resolvedViewerDir));

  // 端口被占用时自动顺延（autoPort=true）。port=0 由系统分配随机端口，无需顺延。
  const tryListen = candidate => new Promise((resolve, reject) => {
    const onError = (err) => {
      server.removeListener('listening', onListening);
      reject(err);
    };
    const onListening = () => {
      server.removeListener('error', onError);
      resolve();
    };
    server.once('error', onError);
    server.once('listening', onListening);
    server.listen(candidate, '127.0.0.1');
  });

  let candidate = port;
  for (let attempt = 0; ; attempt++) {
    try {
      await tryListen(candidate);
      break;
    } catch (err) {
      const canRetry = autoPort && port !== 0 && err && err.code === 'EADDRINUSE' && attempt < maxPortTries;
      if (!canRetry) throw err;
      candidate = port + attempt + 1;
    }
  }

  const actualPort = server.address().port;
  return { server, port: actualPort, url: `http://127.0.0.1:${actualPort}` };
}

// CLI entry (guarded so importing the module in tests does not start a server).
const isCli = process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (isCli) {
  const argv = process.argv.slice(2);
  const args = {};
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (!a.startsWith('--')) continue;
    const eq = a.indexOf('=');
    if (eq >= 0) {
      args[a.slice(2, eq)] = a.slice(eq + 1);
    } else {
      const key = a.slice(2);
      const next = argv[i + 1];
      if (next == null || next.startsWith('--')) args[key] = 'true';
      else {
        args[key] = next;
        i++;
      }
    }
  }

  // ── 管理子命令：列出 / 停止，避免服务无限堆积 ───────────────────────
  if (args.list != null) {
    const servers = listServers();
    if (servers.length === 0) {
      console.log('[viewer] 当前没有运行中的预览服务');
    } else {
      console.log(`[viewer] 运行中的预览服务（${servers.length}）：`);
      for (const s of servers) {
        console.log(`  - http://127.0.0.1:${s.port}  pid=${s.pid}  ${s.target}`);
      }
    }
    process.exit(0);
  }

  if (args['stop-all'] != null) {
    const { stopped } = stopServers({ all: true });
    console.log(`[viewer] 已停止 ${stopped.length} 个预览服务`);
    process.exit(0);
  }

  if (args.stop != null) {
    // --stop <port> 停指定端口；--stop（无值）等价 --stop-all
    if (args.stop === 'true') {
      const { stopped } = stopServers({ all: true });
      console.log(`[viewer] 已停止 ${stopped.length} 个预览服务`);
    } else {
      const { stopped, notFound } = stopServers({ port: Number(args.stop) });
      if (notFound) console.log(`[viewer] 端口 ${args.stop} 上没有登记的预览服务`);
      else console.log(`[viewer] 已停止端口 ${stopped.map(s => s.port).join(', ')} 的预览服务`);
    }
    process.exit(0);
  }

  if (!args.dir && !args.index) {
    console.log(`用法：
  启动：node scripts/serve-viewer.js --dir <解码目录> | --index <viewer-index.json> [--port N] [--force]
  列出：node scripts/serve-viewer.js --list
  停止：node scripts/serve-viewer.js --stop <port>   或   --stop-all`);
    process.exit(0);
  }

  // ── 复用：同一份日志目标若已有服务在跑，直接复用其链接（除非 --force）──
  const key = targetKey({ dir: args.dir, index: args.index });
  if (args.force == null) {
    const existing = findServer({ dir: args.dir, index: args.index });
    if (existing) {
      console.log(`[viewer] 该日志已有预览服务在运行，直接复用：`);
      console.log(`[viewer] http://127.0.0.1:${existing.port}`);
      console.log(`[viewer] 如需强制新建用 --force；停止用 --stop ${existing.port} 或 --stop-all`);
      process.exit(0);
    }
  }

  const requestedPort = args.port != null ? Number(args.port) : 8717;

  // ── --daemon：自我后台化（推荐给 agent 用）──────────────────────────
  // serve-viewer 是常驻进程；若在前台直接跑，会一直阻塞，等 agent 当前命令
  // 轮次结束被 SIGTERM 杀掉（exit 143）。--daemon 让本进程 spawn 一个 detached
  // 子进程真正承载服务，父进程拿到端口后立即退出，命令不再阻塞。
  if (args.daemon != null && !process.env.__VIEWER_DAEMON) {
    const childArgs = process.argv.slice(2).filter(a => a !== '--daemon' && !a.startsWith('--daemon='));
    const logDir = path.resolve(__dirname, '..', 'tmp', 'sessions');
    fs.mkdirSync(logDir, { recursive: true });
    const outLog = fs.openSync(path.join(logDir, 'viewer-daemon.log'), 'a');
    const child = spawn(process.execPath, [fileURLToPath(import.meta.url), ...childArgs], {
      detached: true,
      stdio: ['ignore', outLog, outLog],
      env: { ...process.env, __VIEWER_DAEMON: '1' },
    });
    child.unref();
    // 轮询注册表，等子进程登记好端口再把链接打印出来
    const deadline = Date.now() + 8000;
    const poll = () => {
      const entry = listServers().find(e => e.pid === child.pid || e.target === key);
      if (entry) {
        console.log(`[viewer] ${`http://127.0.0.1:${entry.port}`}`);
        console.log(`[viewer] 已后台启动 (pid=${entry.pid})；停止：node scripts/serve-viewer.js --stop ${entry.port}（或 --stop-all）`);
        process.exit(0);
      }
      if (Date.now() > deadline) {
        console.error('[error] 后台服务启动超时，请查看 tmp/sessions/viewer-daemon.log');
        process.exit(1);
      }
      setTimeout(poll, 200);
    };
    poll();
  } else {
    runForeground();
  }

  function runForeground() {
  // CLI 默认开启端口自动顺延：8717 被占用时自动试 8718、8719…，
  // 避免 agent 因端口冲突报错中断。
  startServer({ dir: args.dir, index: args.index, port: requestedPort, autoPort: true })
    .then(({ url, port, server }) => {
      const mode = args.index ? `index=${args.index}` : `dir=${args.dir}`;
      // 登记到注册表，便于后续 --list / --stop / 复用
      registerServer({ pid: process.pid, port, target: key, startedAt: new Date().toISOString() });
      // 进程退出时自愈注销
      const cleanup = () => { try { unregisterByPid(process.pid); } catch {} };
      process.on('exit', cleanup);
      process.on('SIGTERM', () => { cleanup(); server.close(); process.exit(0); });
      process.on('SIGINT', () => { cleanup(); server.close(); process.exit(0); });

      if (port !== requestedPort) {
        console.log(`[viewer] 端口 ${requestedPort} 被占用，已改用 ${port}`);
      }
      console.log(`[viewer] ${url}`);
      console.log(`[viewer] mode: ${mode}`);
      console.log(`[viewer] 停止本服务：node scripts/serve-viewer.js --stop ${port}（或 --stop-all 停全部）`);
    })
    .catch((err) => {
      process.stderr.write(`[error] ${err.message}\n`);
      process.exit(1);
    });
  }
}
