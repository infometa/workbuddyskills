#!/usr/bin/env node
'use strict';

const os = require('node:os');
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const { execFileSync, spawnSync } = require('node:child_process');

const BIN_NAME = 'westock';

const CHANNEL = 'workbuddy';


const WESTOCK_ROOT = process.env.WESTOCK_HOME || path.join(os.homedir(), '.westock');
const CHANNEL_DIR = process.env.WESTOCK_CHANNEL_DIR || path.join(WESTOCK_ROOT, 'channels', CHANNEL, 'bin');

function hasChannel() {
  const sentinel = '__' + 'CHANNEL__';
  return Boolean(CHANNEL) && CHANNEL !== sentinel;
}

const CLI_BASE_DEFAULT = 'https://stockbuddy.gtimg.com/release/workbuddy/cli';

// 「SHA256.txt 清单文件」自身的预期哈希，作为独立于发布源的信任根。
const PINNED_MANIFEST_SHA256 = '31c98307558da497b2077a796aebf6ae6864e75b7b38f173897c60a9bb35affd';

// 本包对应的发布版本 tag（与该版本 SHA256.txt 信任根配套）。
const PINNED_VERSION = 'v0.0.2';

// 是否已配置 pinned 信任根（值为真实哈希而非未填形态）。
function hasPinned() {
  const sentinel = '__PINNED_' + 'MANIFEST_SHA256__';
  return PINNED_MANIFEST_SHA256 && PINNED_MANIFEST_SHA256 !== sentinel;
}

function hasPinnedVersion() {
  const sentinel = '__PINNED_' + 'VERSION__';
  return PINNED_VERSION && PINNED_VERSION !== sentinel;
}

function parseArgs(argv) {
  const opts = {
    base: process.env.WESTOCK_BASE || '',
    bindir: process.env.WESTOCK_INSTALL_DIR || path.join(os.homedir(), '.local', 'bin'),
    version: process.env.WESTOCK_VERSION || '',
    dryRun: false,
    help: false,
    doSwitch: process.env.WESTOCK_SWITCH === '1',
    noSwitch: process.env.WESTOCK_NO_SWITCH === '1',
    force: process.env.WESTOCK_FORCE === '1',
    // 注意：该开关只放宽下载来源，不影响 SHA256 校验（校验始终强制）。
    allowUnofficialBase: process.env.WESTOCK_ALLOW_UNOFFICIAL_BASE === '1',
  };
  for (let i = 0; i < argv.length; i += 1) {
    const a = argv[i];
    if (a === '-n' || a === '--dry-run') opts.dryRun = true;
    else if (a === '-h' || a === '--help') opts.help = true;
    else {
      console.error(`未知参数: ${a}（本脚本零参数执行；可调项见 --help 中的环境变量表）`);
      process.exit(1);
    }
  }
  return opts;
}

function detectArtifact() {
  const platform = os.platform();
  const arch = os.arch();
  let goos;
  let goarch;
  if (platform === 'darwin') goos = 'darwin';
  else if (platform === 'linux') goos = 'linux';
  else if (platform === 'win32') goos = 'windows';
  else {
    console.error(`不支持的操作系统: ${platform}（请使用 setup.sh / setup.ps1）`);
    process.exit(1);
  }
  if (arch === 'x64') goarch = 'amd64';
  else if (arch === 'arm64') goarch = 'arm64';
  else {
    console.error(`不支持的架构: ${arch}`);
    process.exit(1);
  }
  const ext = goos === 'windows' ? '.exe' : '';
  return { artifact: `westock-${goos}-${goarch}${ext}`, ext };
}

async function httpGetText(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status} ${url}`);
  return res.text();
}

async function httpGetBuffer(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status} ${url}`);
  const buf = Buffer.from(await res.arrayBuffer());
  return buf;
}

function readFirstLine(text) {
  return text.split(/\r?\n/).find((l) => l.trim() !== '') || '';
}

function sha256Hex(buf) {
  return crypto.createHash('sha256').update(buf).digest('hex').toLowerCase();
}

function parseManifestEntries(checksumText, artifact) {
  const hashes = [];
  const malformed = [];
  for (const raw of checksumText.split(/\r?\n/)) {
    const line = raw.trim();
    if (line === '') continue;
    const m = line.match(/^([0-9a-fA-F]{64})\s+(.*\S)$/);
    if (m) {
      if (m[2] === artifact) hashes.push(m[1].toLowerCase());
      continue;
    }
    if (line.endsWith(artifact)) malformed.push(line);
  }
  return { hashes, malformed };
}

function resolveBase(opts) {
  if (opts.base) return opts.base.replace(/\/+$/, '');
  if (CLI_BASE_DEFAULT.startsWith('http')) return CLI_BASE_DEFAULT.replace(/\/+$/, '');
  return '';
}

function hostOf(u) {
  try {
    return new URL(u).host;
  } catch {
    return '';
  }
}

function assertTrustedBase(base, isRemote, allowUnofficialBase) {
  if (!isRemote || !CLI_BASE_DEFAULT.startsWith('http')) return;
  const official = hostOf(CLI_BASE_DEFAULT);
  const actual = hostOf(base);
  if (!official || actual === official) return;
  if (!allowUnofficialBase) {
    console.error(`拒绝从非官方域名下载: ${actual}（官方发布源: ${official}）`);
    console.error('确需自建源请显式加 WESTOCK_ALLOW_UNOFFICIAL_BASE=1');
    process.exit(1);
  }
  console.warn(`⚠️  正在使用非官方基址 ${actual}（WESTOCK_ALLOW_UNOFFICIAL_BASE=1）；SHA256 校验仍会强制执行`);
}

function compareVersion(a, b) {
  const pa = a.replace(/^v/, '').split(/[-+]/)[0].split('.').map(Number);
  const pb = b.replace(/^v/, '').split(/[-+]/)[0].split('.').map(Number);
  for (let i = 0; i < 3; i += 1) {
    const x = pa[i] || 0;
    const y = pb[i] || 0;
    if (x > y) return 1;
    if (x < y) return -1;
  }
  return 0;
}

function latestLocalTag(baseDir) {
  let best = '';
  try {
    for (const entry of fs.readdirSync(baseDir, { withFileTypes: true })) {
      if (!entry.isDirectory() || !entry.name.startsWith('v')) continue;
      if (!/^v\d+\.\d+\.\d+/.test(entry.name)) continue;
      if (best === '' || compareVersion(entry.name, best) > 0) best = entry.name;
    }
  } catch {
  }
  return best;
}


function binVersion(bin) {
  try {
    const out = execFileSync(bin, ['version', '--json'], {
      encoding: 'utf8',
      timeout: 5000,
      env: { ...process.env, WESTOCK_NO_AUTO_UPGRADE: '1' },
    });
    const m = out.match(/"version":"([^"]+)"/);
    return m ? m[1] : '';
  } catch {
    return '';
  }
}







function destExists(dest) {
  if (fs.existsSync(dest)) return true;
  try { fs.lstatSync(dest); return true; } catch { return false; }
}

function runInstallSelf(cliPath, opts, version) {
  if (!hasChannel()) return false;
  const args = ['install-self', '--channel', CHANNEL, '--bindir', opts.bindir, '--version', version];
  if (opts.doSwitch) args.push('--switch');
  if (opts.noSwitch) args.push('--no-switch');
  if (opts.force) args.push('--force');
  try {
    const r = spawnSync(cliPath, args, { encoding: 'utf8' });
    if (r.status === 0) {
      console.log('✅ 安装由程序自身完成');
      String(r.stdout || '').split('\n').filter(Boolean).forEach((l) => console.log(`   ${l}`));
      return true;
    }
    const out = `${r.stdout || ''}${r.stderr || ''}`;
    console.log(
      out.includes('unknown command') || out.includes('unknown flag')
        ? '   当前产物不支持自行安装，回退到脚本直接写入'
        : `   CLI 安装未成功（rc=${r.status}），回退到脚本内置安装逻辑`,
    );
  } catch (e) {
    console.log(`   CLI 安装异常（${e.message}），回退到脚本内置安装逻辑`);
  }
  return false;
}

function tryInstallSelf(buf, ext, opts, version) {
  if (!hasChannel()) return false;
  let tmp = '';
  try {
    tmp = path.join(os.tmpdir(), `westock-install-${process.pid}-${Date.now()}${ext}`);
    fs.writeFileSync(tmp, buf);
    if (ext === '') fs.chmodSync(tmp, 0o755);
    return runInstallSelf(tmp, opts, version);
  } catch (e) {
    console.log(`   CLI 安装异常（${e.message}），回退到脚本内置安装逻辑`);
    return false;
  } finally {
    try { if (tmp) fs.unlinkSync(tmp); } catch { /* 忽略清理失败 */ }
  }
}





// 提示如何调用（不修改 PATH / shell 配置）。
function printPathHint(bindir, dest) {
  const pathEnv = process.env.PATH || '';
  if (pathEnv.split(path.delimiter).includes(bindir)) {
    console.log(`PATH 已包含 ${bindir}，可直接用 ${BIN_NAME} 调用`);
  } else {
    console.log(`${bindir} 不在 PATH 中（本脚本不修改 shell 配置与 PATH）`);
    console.log(`  请用绝对路径调用: ${dest} <子命令>`);
  }
}

async function main() {
  const opts = parseArgs(process.argv.slice(2));
  if (opts.help) {
    console.log(`westock 安装脚本（跨平台，需 Node ≥ 18）

用法:
  node scripts/setup.cjs                      # 安装到 ~/.local/bin
  node scripts/setup.cjs -n                   # 预演：只打印计划，不下载、不落盘
  node scripts/setup.cjs --help

参数（全部可选）:
  -n, --dry-run        只打印计划，不下载、不落盘
  -h, --help           显示帮助

环境变量（供部署方 / 平台注入，agent 无需设置）:
  WESTOCK_BASE                    发布基址（默认官方发布源，其次脚本所在目录）
  WESTOCK_ALLOW_UNOFFICIAL_BASE   允许 WESTOCK_BASE 指向非官方域名（危险；SHA256 仍强制）
  WESTOCK_VERSION                 指定版本（默认包内固定版本，其次 latest.txt）
  WESTOCK_INSTALL_DIR             安装目录（默认 ~/.local/bin）
  WESTOCK_HOME                    数据根目录（默认 ~/.westock）
  WESTOCK_CHANNEL_DIR             覆盖实际文件的落盘目录
  WESTOCK_SWITCH                  设为默认入口
  WESTOCK_NO_SWITCH               绝不改动入口（含首次安装）
  WESTOCK_FORCE                   忽略「已安装」判断，强制重新下载

固定约束（无开关可绕过）:
  * SHA256 校验强制执行：清单拿不到、无哈希工具、条目缺失 / 重复 / 畸形、哈希不匹配，
    一律拒绝安装，不存在跳过校验的选项。
  * 二进制只从本脚本认定的官方发布源下载，其它域名一律拒绝
    （需 WESTOCK_ALLOW_UNOFFICIAL_BASE=1 才放行，且校验照旧强制）。
  * 只把二进制写入安装目录，不修改 shell 配置、PATH 或任何环境变量。
    安装目录不在 PATH 中时，直接用绝对路径调用即可。`);
    process.exit(0);
  }

  const { artifact, ext } = detectArtifact();
  const base = resolveBase(opts);
  const isRemote = base.startsWith('http');
  assertTrustedBase(base, isRemote, opts.allowUnofficialBase);

  let version = opts.version;
  // 与包内固定的 SHA256.txt 清单信任根失配。
  if (!version) {
    if (hasPinnedVersion()) {
      version = PINNED_VERSION;
    } else if (isRemote) {
      try {
        version = readFirstLine(await httpGetText(`${base}/latest.txt`)).trim();
      } catch (e) {
        console.error(`无法获取 latest.txt: ${e.message}`);
        process.exit(1);
      }
    } else {
      let v = '';
      try {
        v = readFirstLine(fs.readFileSync(path.join(base, 'latest.txt'), 'utf8')).trim();
      } catch {
        v = latestLocalTag(base);
      }
      if (!v) {
        console.error('未找到 latest.txt，且 scripts/ 下无可用 v* 版本目录，请用 -v 指定版本');
        process.exit(1);
      }
      version = v;
    }
  }
  if (!version.startsWith('v')) version = `v${version}`;

  const relative = `${version}/${artifact}`;
  const src = isRemote ? `${base}/${relative}` : path.join(base, relative);
  const dest = path.join(opts.bindir, `${BIN_NAME}${ext}`);
  const binName = `${BIN_NAME}${ext}`;
  const realBin = hasChannel() ? path.join(CHANNEL_DIR, binName) : dest;

  console.log(`将安装: ${BIN_NAME} ${version}`);
  console.log(`  源: ${src}`);
  console.log(`  目标: ${dest}`);
  console.log('  shell 配置 / PATH: 不修改');
  if (opts.dryRun) {
    console.log('(dry-run) 未做任何改动');
    process.exit(0);
  }

  {
    if (process.stdin.isTTY) {
      const reply = (await new Promise((r) => {
        process.stdout.write('确认安装? [Y/n] ');
        process.stdin.once('data', (d) => r(d.toString()));
      })).trim().toLowerCase();
      if (reply === 'n') {
        console.log('已取消');
        process.exit(0);
      }
      process.stdin.pause();
    }
  }

  if (hasChannel() && !opts.force && fs.existsSync(realBin)) {
    const installedVer = binVersion(realBin);
    if (installedVer && compareVersion(version, installedVer) <= 0) {
      console.log(`   已安装 ${installedVer}（不低于 ${version}），跳过下载`);
      if (!runInstallSelf(realBin, opts, version)) console.log(`✅ 已安装 → ${realBin}`);
      printPathHint(opts.bindir, dest);
      process.exit(0);
    }
  }

  let buf;
  if (isRemote) {
    try {
      buf = await httpGetBuffer(src);
    } catch (e) {
      console.error(`下载失败: ${e.message}`);
      process.exit(1);
    }
  } else {
    if (!fs.existsSync(src)) {
      console.error(`找不到二进制: ${src}`);
      process.exit(1);
    }
    buf = fs.readFileSync(src);
  }

  // SHA256 校验：对任何包无条件强制，不存在跳过分支。
  let checksumText;
  try {
    checksumText = isRemote
      ? await httpGetText(`${base}/${version}/SHA256.txt`)
      : fs.readFileSync(path.join(base, version, 'SHA256.txt'), 'utf8');
  } catch (e) {
    console.error(`无法获取校验清单 SHA256.txt，拒绝安装: ${e.message}`);
    process.exit(1);
  }

  // 信任根校验：用固定哈希确认 SHA256.txt 清单本身未被篡改（独立于发布源）。
  if (hasPinned()) {
    const manifestActual = sha256Hex(Buffer.from(checksumText, 'utf8'));
    if (manifestActual !== PINNED_MANIFEST_SHA256.toLowerCase()) {
      console.error('SHA256.txt 清单校验失败（疑似发布源被篡改），拒绝安装');
      console.error(`  期望: ${PINNED_MANIFEST_SHA256}`);
      console.error(`  实际: ${manifestActual}`);
      process.exit(1);
    }
  }

  const { hashes: candidateHashes, malformed } = parseManifestEntries(checksumText, artifact);
  if (candidateHashes.length === 0) {
    console.error(`SHA256.txt 中未找到 ${artifact} 的合法校验条目，拒绝安装`);
    if (malformed.length > 0) console.error(`  疑似畸形条目: ${malformed.join(' | ')}`);
    process.exit(1);
  }
  if (candidateHashes.length > 1) {
    console.error(`SHA256.txt 中 ${artifact} 存在 ${candidateHashes.length} 条校验条目（清单歧义），拒绝安装`);
    process.exit(1);
  }

  const expected = candidateHashes[0];
  const actual = sha256Hex(buf);
  if (actual !== expected) {
    console.error(`SHA256 校验失败: ${artifact}`);
    console.error(`  期望: ${expected}`);
    console.error(`  实际: ${actual}`);
    process.exit(1);
  }
  console.log(`SHA256 校验通过: ${artifact}`);

  if (tryInstallSelf(buf, ext, opts, version)) {
    printPathHint(opts.bindir, dest);
    return;
  }
  fs.mkdirSync(opts.bindir, { recursive: true });
  fs.writeFileSync(dest, buf);
  if (ext === '') fs.chmodSync(dest, 0o755);
  console.log(`✅ 已安装 → ${dest}（直接安装）`);

  // 只落盘二进制，不碰 shell 配置 / PATH / 环境变量。
  printPathHint(opts.bindir, dest);
}

main().catch((e) => {
  console.error(e.message || e);
  process.exit(1);
});
