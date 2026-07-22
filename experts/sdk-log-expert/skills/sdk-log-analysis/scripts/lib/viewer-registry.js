// scripts/lib/viewer-registry.js
// 轻量进程注册表：记录已启动的 viewer 服务（pid/port/target），
// 用于「复用已运行服务、列出、停止」，避免 agent 反复调用堆积进程/端口。
// 纯 Node 内置模块；注册表文件落在 tmp/（gitignored，运行时产物）。
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SKILL_DIR = path.resolve(__dirname, '..', '..');
const DEFAULT_REGISTRY = path.join(SKILL_DIR, 'tmp', 'sessions', 'viewer-servers.json');

/** 进程是否存活（signal 0 不真正发信号，仅探测）。 */
export function isAlive(pid) {
  if (!pid || typeof pid !== 'number') return false;
  try {
    process.kill(pid, 0);
    return true;
  } catch (err) {
    // EPERM 表示进程存在但无权限（仍算存活）；ESRCH 表示不存在。
    return err && err.code === 'EPERM';
  }
}

function readRaw(registryPath) {
  try {
    const parsed = JSON.parse(fs.readFileSync(registryPath, 'utf8'));
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function writeRaw(registryPath, entries) {
  fs.mkdirSync(path.dirname(registryPath), { recursive: true });
  fs.writeFileSync(registryPath, `${JSON.stringify(entries, null, 2)}\n`);
}

/** 读取注册表，并顺手剔除已死进程（自愈）。 */
export function listServers(registryPath = DEFAULT_REGISTRY) {
  const entries = readRaw(registryPath);
  const alive = entries.filter(e => isAlive(e.pid));
  if (alive.length !== entries.length) writeRaw(registryPath, alive);
  return alive;
}

/** 把 dir/index 归一化为「目标标识」，用于判断是否同一份日志已有服务在跑。 */
export function targetKey({ dir, index }) {
  if (index) return `index:${path.resolve(index)}`;
  if (dir) return `dir:${path.resolve(dir)}`;
  return '';
}

/** 查找服务同一目标且存活的服务。 */
export function findServer(target, registryPath = DEFAULT_REGISTRY) {
  const key = targetKey(target);
  if (!key) return null;
  return listServers(registryPath).find(e => e.target === key) || null;
}

/** 注册一个服务。 */
export function registerServer(entry, registryPath = DEFAULT_REGISTRY) {
  const entries = listServers(registryPath).filter(e => e.pid !== entry.pid && e.port !== entry.port);
  entries.push(entry);
  writeRaw(registryPath, entries);
  return entry;
}

/** 按 pid 注销。 */
export function unregisterByPid(pid, registryPath = DEFAULT_REGISTRY) {
  const entries = readRaw(registryPath).filter(e => e.pid !== pid);
  writeRaw(registryPath, entries);
}

/**
 * 停止服务。
 * @param {{port?: number, all?: boolean}} opts
 * @returns {{stopped: Array, notFound: boolean}}
 */
export function stopServers(opts = {}, registryPath = DEFAULT_REGISTRY) {
  const alive = listServers(registryPath);
  let targets;
  if (opts.all) targets = alive;
  else if (opts.port != null) targets = alive.filter(e => e.port === Number(opts.port));
  else targets = [];

  const stopped = [];
  for (const e of targets) {
    try {
      process.kill(e.pid, 'SIGTERM');
      stopped.push(e);
    } catch {
      // 已退出，忽略
      stopped.push(e);
    }
  }
  const stoppedPids = new Set(stopped.map(e => e.pid));
  writeRaw(registryPath, alive.filter(e => !stoppedPids.has(e.pid)));
  return { stopped, notFound: targets.length === 0 };
}

export { DEFAULT_REGISTRY };
