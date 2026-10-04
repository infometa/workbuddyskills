'use strict';
// Runs from the connector ZIP, independently of the installed CLI version.
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const { randomUUID } = require('node:crypto');

function parseVersion(value) {
  const match = /^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$/.exec(String(value).trim());
  if (!match) throw new Error('Invalid CLI version');
  const pre = match[4] ? match[4].split('.') : [];
  if (pre.some(v => /^0\d+$/.test(v))) throw new Error('Invalid CLI prerelease');
  return { core: match.slice(1, 4).map(BigInt), pre };
}

function compareVersions(a, b) {
  const x = parseVersion(a), y = parseVersion(b);
  const cmp = (l, r) => l < r ? -1 : l > r ? 1 : 0;
  for (let i = 0; i < 3; i++) if (x.core[i] !== y.core[i]) return cmp(x.core[i], y.core[i]);
  if (!x.pre.length || !y.pre.length) return cmp(y.pre.length ? 1 : 0, x.pre.length ? 1 : 0);
  for (let i = 0; i < Math.max(x.pre.length, y.pre.length); i++) {
    if (x.pre[i] === undefined) return -1;
    if (y.pre[i] === undefined) return 1;
    if (x.pre[i] === y.pre[i]) continue;
    const xn = /^\d+$/.test(x.pre[i]), yn = /^\d+$/.test(y.pre[i]);
    if (xn && yn) return cmp(BigInt(x.pre[i]), BigInt(y.pre[i]));
    if (xn !== yn) return xn ? -1 : 1;
    return cmp(x.pre[i], y.pre[i]);
  }
  return 0;
}

function ownerAlive(value) {
  if (!/^[1-9]\d*$/.test(value)) return true;
  try { process.kill(Number(value), 0); return true; }
  catch (error) { return error.code !== 'ESRCH'; }
}

function acquireRecovery(directory) {
  const name = `owner-${process.pid}-${randomUUID()}`;
  const ownFile = path.join(directory, name);
  const busy = () => new Error('Connector lock recovery is active. Retry after it finishes.');
  for (let attempt = 0; attempt < 4; attempt++) {
    try { fs.mkdirSync(directory); }
    catch (error) {
      if (error.code !== 'EEXIST') throw error;
      // Remove only named dead-owner files. rmdir is atomic and refuses to
      // remove a directory in which a live contender has published its claim.
      for (const entry of fs.readdirSync(directory)) {
        const match = /^owner-([1-9]\d*)-/.exec(entry);
        if (!match || ownerAlive(match[1])) throw busy();
        try { fs.unlinkSync(path.join(directory, entry)); }
        catch (e) { if (e.code !== 'ENOENT') throw e; }
      }
      try { fs.rmdirSync(directory); }
      catch (e) { if (e.code !== 'ENOENT') throw busy(); }
      continue;
    }
    try { fs.writeFileSync(ownFile, '', { flag: 'wx' }); }
    catch (error) { if (error.code === 'ENOENT') continue; throw error; }
    const entries = fs.readdirSync(directory);
    if (entries.length !== 1 || entries[0] !== name) {
      fs.unlinkSync(ownFile);
      throw busy();
    }
    return () => {
      fs.unlinkSync(ownFile);
      try { fs.rmdirSync(directory); }
      catch (error) { if (!['ENOENT', 'ENOTEMPTY', 'EEXIST'].includes(error.code)) throw error; }
    };
  }
  throw busy();
}

function acquireLock(file) {
  try { fs.writeFileSync(file, `${process.pid}\n`, { flag: 'wx' }); return; }
  catch (error) { if (error.code !== 'EEXIST') throw error; }
  // Only one process may remove a dead owner's file. Without this guard, two
  // recoverers could unlink each other's newly acquired live lock.
  const recovery = `${file}.recovery`;
  const releaseRecovery = acquireRecovery(recovery);
  try {
    if (fs.existsSync(file)) {
      const owners = fs.readFileSync(file, 'utf8').trim().split(/\s+/);
      // Installers append their own PID before doing any work, so killing only
      // the host cannot make a still-running installation look abandoned.
      const alive = owners.some(ownerAlive);
      if (alive) throw new Error('Another connector check/install is active. Retry after it finishes.');
      fs.unlinkSync(file);
    }
    fs.writeFileSync(file, `${process.pid}\n`, { flag: 'wx' });
  } finally { releaseRecovery(); }
}

function launch(action, options = {}) {
  const out = options.stdout || (s => process.stdout.write(s));
  const err = options.stderr || (s => process.stderr.write(s));
  let lock, locked = false;
  try {
    if (!['version', 'auth', 'status', 'unauth'].includes(action)) throw new Error('Expected version, auth, status or unauth');
    const directory = options.directory || __dirname;
    const platform = options.platform || process.platform;
    if (!['win32', 'darwin', 'linux'].includes(platform)) throw new Error('Unsupported platform');
    const windows = platform === 'win32';
    const home = path.resolve(options.home || process.env.SL_CLI_HOME || path.join(os.homedir(), '.slclaw'));
    if (home === path.parse(home).root || home === path.resolve(os.homedir())) throw new Error('Unsafe SL_CLI_HOME');
    if (fs.existsSync(home) && fs.lstatSync(home).isSymbolicLink()) throw new Error('SL_CLI_HOME must not be a symbolic link');
    const config = JSON.parse(fs.readFileSync(path.join(directory, 'cli.json'), 'utf8').replace(/^\uFEFF/, ''));
    const minimum = config.versionCheck.minVersion;
    parseVersion(minimum);
    const entry = path.join(home, 'bin', windows ? 'sl.cmd' : 'sl');
    const sea = path.join(home, 'bin', windows ? 'sl-sea.exe' : 'sl-sea');
    const complete = () => [entry, sea].every(file => {
      try {
        if (!fs.statSync(file).isFile()) return false;
        if (!windows) fs.accessSync(file, fs.constants.X_OK);
        return true;
      } catch { return false; }
    });
    // Lifecycle calls must not start a second, throttled CLI updater after the
    // connector has made its own minimum-version decision (especially unauth).
    const env = { ...process.env, SL_CLI_HOME: home, SL_CLI_SKIP_UPDATE: '1' };
    const runCli = options.runCli || ((args, capture) => {
      const command = windows ? 'powershell.exe' : entry;
      // Entry travels through the environment, never interpolated into shell code.
      const argv = windows ? ['-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command',
        `& $env:SL_LAUNCH_ENTRY ${args.map(a => "'" + a.replace(/'/g, "''") + "'").join(' ')}; exit $LASTEXITCODE`] : args;
      return spawnSync(command, argv, {
        env: { ...env, SL_LAUNCH_ENTRY: entry }, windowsHide: true,
        stdio: capture ? ['ignore', 'pipe', 'pipe'] : 'inherit', encoding: 'utf8',
        ...(capture ? { timeout: 30000, maxBuffer: 1024 * 1024 } : {}),
      });
    });
    const probe = () => {
      if (!complete()) return null;
      const result = runCli(['--version'], true);
      if (result.status !== 0 || result.error) return null;
      const version = String(result.stdout || '').trim();
      try { parseVersion(version); return version; } catch { return null; }
    };
    const release = () => { if (locked) { fs.unlinkSync(lock); locked = false; } };
    // Serialize probes too: the existing wrapper may activate a pending update.
    fs.mkdirSync(home, { recursive: true });
    lock = path.join(home, '.connector-launch.lock');
    acquireLock(lock);
    locked = true;
    let version = probe();
    if (action === 'version') {
      // WorkBuddy aborts on nonzero exits. Let its minVersion comparison
      // select init, including when there is no usable installed version.
      out((version || '0.0.0') + '\n');
      return 0;
    }
    if (action === 'unauth') {
      release();
      if (!version) throw new Error('Unable to revoke local authorization: CLI is unavailable; credentials have not been cleared. Repair the CLI and retry unauth.');
      return runCli(['connector', 'unauth'], false).status ?? 1;
    }
    if (!version || compareVersions(version, minimum) < 0) {
      if (action === 'status') { out('{"authenticated":false}\n'); return 0; }
      err(`[shanlong-claw] CLI missing, damaged or below ${minimum}; installing/repairing...\n`);
      const install = options.install || (() => spawnSync(windows ? 'powershell.exe' : 'bash',
        windows ? ['-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command',
          '[IO.File]::AppendAllText($env:SL_LAUNCH_LOCK, [string]$PID + [Environment]::NewLine); & $env:SL_LAUNCH_INSTALLER; exit $LASTEXITCODE']
          : ['-c', 'printf "%s\\n" "$$" >> "$SL_LAUNCH_LOCK"; exec bash "$SL_LAUNCH_INSTALLER"'],
        { env: { ...env, SL_LAUNCH_LOCK: lock, SL_LAUNCH_INSTALLER: path.join(directory, windows ? 'install.ps1' : 'install.sh') },
          windowsHide: true, stdio: ['ignore', 2, 2] }));
      const installed = install();
      if (installed.status !== 0 || installed.error) throw new Error(`CLI installation failed (exit ${installed.status ?? 'unknown'}). Check installer stderr.`);
      version = probe();
      if (!version || compareVersions(version, minimum) < 0) throw new Error(`CLI upgrade not active; required >= ${minimum}. Close running CLI processes and retry.`);
    }
    release();
    const result = runCli(['connector', action], false);
    return result.status ?? 1;
  } catch (error) {
    err(`[shanlong-claw] ${error.message}\n`);
    return 1;
  } finally {
    if (locked) { try { fs.unlinkSync(lock); } catch {} }
  }
}

module.exports = { launch, compareVersions, acquireLock };
if (require.main === module) process.exitCode = launch(process.argv[2]);
