#!/usr/bin/env node
'use strict';

/**
 * ══════════════════════════════════════════════════════════════════
 *  assemble-artifact.js
 *  把两块真源库注入 Step 3 模型产物（slim 模式专用）
 * ══════════════════════════════════════════════════════════════════
 *
 *  数据流：
 *      slim 提示词 → 模型只写构造区/校验区/帧函数，LIB 内留两行注入标记
 *                  → 本脚本按标记注入真源全文 → 等价于 full 模式的产物
 *
 *  用法：
 *      node assemble-artifact.js <模型产物文件> [--out <输出文件>]
 *      node assemble-artifact.js <产物文件> --check      # 只体检，不写
 *
 *  默认输出：<原名>.assembled.js
 *
 *  注入规则（与「同步内联库.js」写槽位的规则一致，保证与 full 模式产物等价）：
 *      · 标记行被替换为真源全文，逐行按标记行缩进对齐（空行保持空行）
 *      · 先内核、后绘图层
 *
 *  退出码：0 成功 / 1 校验失败 / 2 文件或标记缺失
 * ══════════════════════════════════════════════════════════════════
 */

const fs = require('fs');
const path = require('path');

const SKILL = path.join(__dirname, '..');
const LIBDIR = path.join(SKILL, 'references');

// 输出路径白名单：仅允许写回工作区(cwd)或技能目录(SKILL)内。
function assertSafeOutPath(p) {
    const abs = path.resolve(p);
    const roots = [process.cwd(), SKILL];
    const ok = roots.some(r => { const rp = path.resolve(r); return abs === rp || abs.startsWith(rp + path.sep); });
    if (!ok) { console.error('❌ 输出路径越界（仅允许工作区/技能目录内）：' + abs); process.exit(2); }
    return abs;
}

const BANKS = [
    {
        tag: '几何内核', file: '几何内核.js', ver: 'v2.2',
        mark: 'GEOM_KERNEL',
        fingerprints: ['const DEG = Math.PI / 180;', 'function CKBounds(', 'function CK(']
    },
    {
        tag: '绘图层', file: '绘图层.js', ver: 'v1.1',
        mark: 'DRAW_LAYER',
        fingerprints: ['const _DEG = Math.PI / 180;', 'function drawMathText(']
    }
];

/* ── 参数 ── */
const argv = process.argv.slice(2);
let src = null, outOpt = null;
const flags = new Set();
for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--out' || a === '-o') { outOpt = argv[++i]; continue; }
    if (a.startsWith('--')) { flags.add(a); continue; }
    if (!src) src = a;
}
const CHECK_ONLY = flags.has('--check');
if (!src) {
    console.error('用法：node assemble-artifact.js <模型产物文件> [--out <输出>] [--check]');
    process.exit(2);
}
if (!fs.existsSync(src)) {
    console.error('❌ 找不到产物文件：' + src);
    process.exit(2);
}
const outPath = outOpt
    ? outOpt
    : src.replace(/\.(js|txt|md)$/i, '') + '.assembled.js';

/* ── 读入真源 ── */
for (const b of BANKS) {
    const p = path.join(LIBDIR, b.file);
    if (!fs.existsSync(p)) { console.error('❌ 缺少真源：' + p); process.exit(2); }
    let s = fs.readFileSync(p, 'utf8').replace(/^\uFEFF/, '');
    b.srcLines = s.replace(/\r\n/g, '\n').split('\n');
    b.nonEmpty = b.srcLines.filter(l => l.trim() !== '').length;
}

/* ── 读入产物 ── */
let raw = fs.readFileSync(src, 'utf8').replace(/^\uFEFF/, '').replace(/\r\n/g, '\n');
const lines = raw.split('\n');

console.log('产物　：' + src);
console.log('输出　：' + (CHECK_ONLY ? '（--check，不写出）' : outPath));
console.log('行数　：' + lines.length + '\n');

/* ── 定位标记（优先取 LIB 内的那一个） ── */
const libStart = lines.findIndex(l => /const\s+LIB\s*=\s*\(\s*function\s*\(\s*\)/.test(l));
if (libStart >= 0) console.log('LIB IIFE 起始行：第 ' + (libStart + 1) + ' 行');
else console.log('⚠️ 未找到 `const LIB = (function () {` —— 退化为全文查找标记');

const plans = [];
let fatal = 0;

for (const b of BANKS) {
    const re = new RegExp('@@INJECT:' + b.mark + '@@');
    const hits = [];
    lines.forEach((l, i) => { if (re.test(l)) hits.push(i); });

    if (!hits.length) {
        console.error('❌ 未找到注入标记 @@INJECT:' + b.mark + '@@');
        console.error('   模型产物里应有形如 `/* @@INJECT:' + b.mark + '@@ */` 的一行。');
        fatal++;
        continue;
    }

    let pick = -1;
    if (libStart >= 0) {
        const inLib = hits.filter(i => i > libStart);
        if (inLib.length === 1) pick = inLib[0];
        else if (inLib.length > 1) {
            pick = inLib[0];
            console.log('⚠️ ' + b.tag + '：LIB 内命中 ' + inLib.length + ' 个标记（第 ' +
                inLib.map(i => i + 1).join('、') + ' 行），取第一个；其余将作为普通文本保留，请复核。');
        }
    }
    if (pick < 0) {
        pick = hits[hits.length - 1];
        console.log('⚠️ ' + b.tag + '：未在 LIB 内定位到标记，退化为取最后一个命中（第 ' + (pick + 1) + ' 行）。');
    }

    const base = (lines[pick].match(/^[ \t]*/) || [''])[0];
    const newBlock = b.srcLines.map(l => (l.trim() === '' ? '' : base + l));

    plans.push({ b, at: pick, base, newBlock, allHits: hits });
    console.log('【' + b.tag + '】标记第 ' + (pick + 1) + ' 行（缩进 ' + base.length +
        ' 空格，全文命中 ' + hits.length + ' 处）→ 注入 ' + b.nonEmpty + ' 行非空代码');
}

if (fatal) {
    console.error('\n❌ 有 ' + fatal + ' 个块缺少注入标记，无法装配。');
    console.error('   请让 Step 3 在 LIB 内补写标记行，或改用 full 模式提示词。');
    process.exit(2);
}

/* ── 从后往前替换，避免行号漂移 ── */
let out = lines.slice();
for (const p of plans.sort((a, c) => c.at - a.at)) {
    out = [...out.slice(0, p.at), ...p.newBlock, ...out.slice(p.at + 1)];
}

let text = out.join('\n');

/* ── 校验 ── */
console.log('\n【装配校验】');
const problems = [];

// 1. 无残留注入标记
for (const b of BANKS) {
    const left = (text.match(new RegExp('@@INJECT:' + b.mark + '@@', 'g')) || []).length;
    if (left) problems.push(b.tag + '：仍残留 ' + left + ' 个注入标记（未全部替换）');
    else console.log('  ✅ ' + b.tag + ' 注入标记已全部替换');
}

// 2. 每块各 1 份（副本数量闸门，与同步内联库.js 同口径）
for (const b of BANKS) {
    for (const fp of b.fingerprints) {
        const n = text.split(fp).length - 1;
        if (n === 0) problems.push(b.tag + ' 缺少代码指纹：' + fp);
        else if (n > 1) problems.push(b.tag + ' 代码指纹出现 ' + n + ' 次（应为 1，疑似模型自写重名实现）：' + fp);
    }
    if (!problems.some(p => p.includes(b.tag))) {
        console.log('  ✅ ' + b.tag + ' 指纹唯一、内容完整');
    }
}

// 3. 必备机制抽查
if (/recordToAccumulator\s*\(/.test(text.replace(/\/\/.*$/gm, '')) &&
    !/function\s+recordToAccumulator/.test(text)) {
    // recordToAccumulator 定义在库内，产物区不应出现调用
}
const tier = text.match(/window\.__DRAW_TIER__\s*=\s*'([ABC])'/);
if (tier) console.log('  ✅ 档位声明：' + tier[1] + ' 档');
else problems.push('未找到 window.__DRAW_TIER__ 档位声明');

if (problems.length) {
    console.error('\n⚠️ 装配完成但存在问题：');
    problems.forEach(p => console.error('  · ' + p));
} else {
    console.log('\n✅ 装配通过：两块库已注入，指纹唯一');
}

if (CHECK_ONLY) {
    console.log('\n（--check 模式，未写出文件）');
    process.exit(problems.length ? 1 : 0);
}

assertSafeOutPath(outPath);
fs.writeFileSync(outPath, text, 'utf8');
console.log('\n✅ 已写出：' + outPath);
console.log('   行数：' + lines.length + ' → ' + out.length +
    '（+' + (out.length - lines.length) + '）');
process.exit(problems.length ? 1 : 0);
