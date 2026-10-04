#!/usr/bin/env node
'use strict';

const os = require('node:os');
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');

const BIN_NAME = 'westock';

// CLI 官方发布源（默认下载基址，形如 https://<host>/release/<channel>/cli）。
// 占位符未被替换时（本地直接运行源码）视为空。
const CLI_BASE_DEFAULT = 'https://stockbuddy.qq.com/release/workbuddy/cli';

// 发布时注入的「SHA256.txt 清单文件」自身哈希（信任根，独立于 CDN）。
// 校验链：脚本内固定哈希 → 校验 SHA256.txt 未被篡改 → SHA256.txt 校验二进制。
// 占位符未被替换（本地源码运行）时视为空，退回仅校验二进制（兼容本地开发）。
const PINNED_MANIFEST_SHA256 = 'f2b3fc21beddb82604c3c8e355e6201de9bb281fcf340758c5aaccf01a7b6724';

// 发布时注入的「发布版本 tag」（与该版本 SHA256.txt 信任根配套）。
// 安装时优先用它确定版本（而非 CDN 上的 latest.txt），保证清单哈希信任根
// 始终对应该版本；追新交给 CLI 运行时自检升级。占位符未替换时为空，退回读 latest.txt。
const PINNED_VERSION = 'v0.0.4';

// 是否配置了 pinned 信任根（占位符已被发布流程替换为真实哈希）。
// 哨兵用拼接构造，避免发布期 replaceAll 把这里的比较基准也一并替换。
function hasPinned() {
  const sentinel = '__PINNED_' + 'MANIFEST_SHA256__';
  return PINNED_MANIFEST_SHA256 && PINNED_MANIFEST_SHA256 !== sentinel;
}

// 是否注入了固定发布版本（占位符已被发布流程替换为真实 tag）。
function hasPinnedVersion() {
  const sentinel = '__PINNED_' + 'VERSION__';
  return PINNED_VERSION && PINNED_VERSION !== sentinel;
}

function parseArgs(argv) {
  const opts = {
    base: '',
    bindir: process.env.WESTOCK_INSTALL_DIR || path.join(os.homedir(), '.local', 'bin'),
    version: '',
    dryRun: false,
    yes: false,
    help: false,
  };
  for (let i = 0; i < argv.length; i += 1) {
    const a = argv[i];
    if (a === '-b' || a === '--base') opts.base = argv[++i];
    else if (a === '-d' || a === '--bindir') opts.bindir = argv[++i];
    else if (a === '-v' || a === '--version') opts.version = argv[++i];
    else if (a === '-n' || a === '--dry-run') opts.dryRun = true;
    else if (a === '-y' || a === '--yes') opts.yes = true;
    else if (a === '-h' || a === '--help') opts.help = true;
    else {
      console.error(`未知参数: ${a}`);
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

function resolveBase(opts) {
  if (opts.base) return opts.base.replace(/\/+$/, '');
  if (CLI_BASE_DEFAULT.startsWith('http')) return CLI_BASE_DEFAULT.replace(/\/+$/, '');
  return '';
}

// 语义化版本比较：a > b 返回 1，a < b 返回 -1，相等返回 0
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

// 本地模式（bundled 渠道无 latest.txt 时的兜底）：枚举 base 下 v* 目录返回最大版本 tag
function latestLocalTag(baseDir) {
  let best = '';
  try {
    for (const entry of fs.readdirSync(baseDir, { withFileTypes: true })) {
      if (!entry.isDirectory() || !entry.name.startsWith('v')) continue;
      if (!/^v\d+\.\d+\.\d+/.test(entry.name)) continue;
      if (best === '' || compareVersion(entry.name, best) > 0) best = entry.name;
    }
  } catch {
    // 忽略目录读取错误
  }
  return best;
}

async function main() {
  const opts = parseArgs(process.argv.slice(2));
  if (opts.help) {
    console.log(`westock 安装脚本（跨平台，需 Node ≥ 18）

用法:
  node scripts/setup.cjs                      # 本地安装到 ~/.local/bin
  node scripts/setup.cjs -d /usr/local/bin -v v1.2.3
  node scripts/setup.cjs --help

参数（全部可选）:
  -b, --base URL     远程发布基址 (默认: 官方发布源)
  -d, --bindir DIR   安装目录 (默认 ~/.local/bin 或 WESTOCK_INSTALL_DIR)
  -v, --version VER  指定版本 (默认 latest.txt)
  -n, --dry-run      只打印不执行
  -y, --yes          跳过确认
  -h, --help         显示帮助`);
    process.exit(0);
  }

  const { artifact, ext } = detectArtifact();
  const base = resolveBase(opts);
  const isRemote = base.startsWith('http');

  let version = opts.version;
  // 发布产物注入了固定版本时优先使用，避免读 CDN 的 latest.txt 导致旧包指向新版本、
  // 与包内固定的 SHA256.txt 清单信任根失配（版本 tag 由构建期注入）。
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

  console.log(`将安装: ${BIN_NAME} ${version}`);
  console.log(`  源: ${src}`);
  console.log(`  目标: ${dest}`);
  if (opts.dryRun) {
    console.log('(dry-run) 未做任何改动');
    process.exit(0);
  }

  if (!opts.yes) {
    // 仅在 TTY 下交互确认，非交互环境默认继续
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

  // SHA256 校验
  try {
    let checksumText;
    if (isRemote) {
      checksumText = await httpGetText(`${base}/${version}/SHA256.txt`);
    } else {
      checksumText = fs.readFileSync(path.join(base, version, 'SHA256.txt'), 'utf8');
    }

    // 信任根校验：先确认 SHA256.txt 清单本身未被篡改（独立于 CDN 的固定哈希）。
    if (hasPinned()) {
      const manifestActual = sha256Hex(Buffer.from(checksumText, 'utf8'));
      if (manifestActual !== PINNED_MANIFEST_SHA256.toLowerCase()) {
        console.error('SHA256.txt 清单校验失败（疑似 CDN 被篡改），拒绝安装');
        console.error(`  期望: ${PINNED_MANIFEST_SHA256}`);
        console.error(`  实际: ${manifestActual}`);
        process.exit(1);
      }
    }

    const expected = checksumText
      .split(/\r?\n/)
      .map((l) => l.trim())
      .find((l) => l.endsWith(artifact))
      ?.split(/\s+/)[0]
      ?.toLowerCase();
    if (expected) {
      const actual = sha256Hex(buf);
      if (actual !== expected) {
        console.error(`SHA256 校验失败: ${artifact}`);
        console.error(`  期望: ${expected}`);
        console.error(`  实际: ${actual}`);
        process.exit(1);
      }
    } else {
      console.warn('未找到对应 SHA256 条目，跳过校验');
    }
  } catch (e) {
    // 已配置固定校验值却拿不到/校验不了 SHA256.txt → 拒绝安装（不静默放行）。
    if (hasPinned()) {
      console.error(`无法校验 SHA256.txt，且已配置固定校验值，拒绝安装: ${e.message}`);
      process.exit(1);
    }
    console.warn(`未找到 SHA256.txt，跳过校验: ${e.message}`);
  }

  fs.mkdirSync(opts.bindir, { recursive: true });
  fs.writeFileSync(dest, buf);
  if (ext === '') fs.chmodSync(dest, 0o755);

  console.log(`✅ 已安装 → ${dest}`);

  const pathEnv = process.env.PATH || '';
  if (!pathEnv.split(path.delimiter).includes(opts.bindir)) {
    console.log(`请将 ${opts.bindir} 加入 PATH：`);
    console.log(`  export PATH="${opts.bindir}:$PATH"  # 写入 ~/.${path.basename(process.env.SHELL || 'bash')}rc 后 source`);
  } else {
    console.log(`PATH 已包含 ${opts.bindir}`);
  }
}

main().catch((e) => {
  console.error(e.message || e);
  process.exit(1);
});
