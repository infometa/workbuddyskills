#!/usr/bin/env node
/**
 * 发票文件预处理：统一「拿到可读的图片」，供多模态视觉识别要素。
 *
 * 用法：
 *   node prepare-image.mjs <文件路径> [输出目录] [--dpi 200]
 *   node prepare-image.mjs 发票.pdf 输出目录
 *   node prepare-image.mjs 发票.png
 *
 * 行为：
 *   - PNG / JPG / JPEG：原样返回路径（stderr 提示可直接读图）
 *   - PDF：逐页转 PNG，后端按 PyMuPDF → pdftoppm → qlmanage 顺序自动回退
 *   - 其他扩展名：报错退出
 *
 * 输出：stdout 每行一个图片绝对路径（PDF 为每页一张）
 * 退出码：0 成功；1 参数/文件问题；2 无可用转换后端
 */
import { existsSync, statSync, readdirSync, mkdirSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { dirname, extname, join, basename } from 'node:path';
import { homedir } from 'node:os';
import { fileURLToPath } from 'node:url';

const argv = process.argv.slice(2);
const dpiIdx = argv.indexOf('--dpi');
const dpi = dpiIdx >= 0 ? argv[dpiIdx + 1] : '200';
// 未传 --dpi 时不能套用下标过滤（dpiIdx=-1 会误删第 0 个位置参数）
const args = dpiIdx >= 0 ? argv.filter((_, i) => i !== dpiIdx && i !== dpiIdx + 1) : argv;

const [input, outdirArg] = args;
if (!input) {
  console.error('用法: node prepare-image.mjs <文件路径> [输出目录] [--dpi 200]');
  process.exit(1);
}
if (!existsSync(input) || !statSync(input).isFile()) {
  console.error(`文件不存在或不是文件：${input}`);
  process.exit(1);
}

const HERE = dirname(fileURLToPath(import.meta.url));
const ext = extname(input).toLowerCase();

function run(cmd, cmdArgs) {
  const r = spawnSync(cmd, cmdArgs, { encoding: 'utf8' });
  return { ok: r.status === 0, stdout: (r.stdout || '').trim(), stderr: (r.stderr || '').trim(), status: r.status };
}

/** 候选 Python：优先已装 pymupdf 的隔离环境 */
function pythonCandidates() {
  return [
    join(homedir(), '.workbuddy', 'binaries', 'python', 'envs', 'default', 'bin', 'python'),
    join(homedir(), '.workbuddy', 'binaries', 'python', 'versions', '3.13.12', 'bin', 'python3'),
    '/usr/local/bin/python3',
    '/usr/bin/python3',
    'python3',
  ];
}

if (['.png', '.jpg', '.jpeg'].includes(ext)) {
  console.log(input);
  process.stderr.write(`✅ 图片文件，直接用多模态视觉读取即可：${input}\n`);
  process.exit(0);
}

if (ext !== '.pdf') {
  console.error(`不支持的文件类型：${ext}（仅支持 PDF / PNG / JPG / JPEG）`);
  process.exit(1);
}

// ---------- PDF → PNG ----------
const base = basename(input, ext);
const outdir = outdirArg || join(dirname(input), `${base}_pages`);

// 1) PyMuPDF
for (const py of pythonCandidates()) {
  const probe = run(py, ['-c', 'import pymupdf']);
  if (!probe.ok) continue;
  const r = run(py, [join(HERE, 'pdf_to_png.py'), input, outdir, '--dpi', dpi]);
  if (r.ok && r.stdout) {
    console.log(r.stdout);
    process.stderr.write(`✅ PyMuPDF 转换完成（${py}）\n${r.stderr}\n`);
    process.exit(0);
  }
}

// 2) poppler pdftoppm
mkdirSync(outdir, { recursive: true });
const ppm = run('pdftoppm', ['-r', dpi, '-png', input, join(outdir, base)]);
if (ppm.ok) {
  const files = readdirSync(outdir)
    .filter((f) => f.startsWith(base) && f.endsWith('.png'))
    .sort()
    .map((f) => join(outdir, f));
  if (files.length) {
    files.forEach((f) => console.log(f));
    process.stderr.write(`✅ pdftoppm 转换完成，共 ${files.length} 张\n`);
    process.exit(0);
  }
}

// 3) macOS QuickLook（qlmanage）
const ql = run('qlmanage', ['-t', '-s', '2000', '-o', outdir, input]);
if (ql.ok) {
  const files = readdirSync(outdir).filter((f) => f.endsWith('.png')).map((f) => join(outdir, f));
  if (files.length) {
    files.forEach((f) => console.log(f));
    process.stderr.write(`⚠️ 使用 QuickLook 兜底转换（清晰度较低），共 ${files.length} 张\n`);
    process.exit(0);
  }
}

console.error(
  '无可用 PDF 转换后端。请任选其一后重试：\n' +
    `  1) ${join(homedir(), '.workbuddy', 'binaries', 'python', 'envs', 'default', 'bin', 'pip')} install pymupdf\n` +
    '  2) brew install poppler   # 提供 pdftoppm',
);
process.exit(2);
