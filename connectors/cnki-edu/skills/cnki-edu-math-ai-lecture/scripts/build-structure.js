#!/usr/bin/env node
'use strict';

/**
 * ══════════════════════════════════════════════════════════════════
 *  build-structure.js —— 从 S2 讲题方案自动生成「结构层」代码（P2-3）
 * ══════════════════════════════════════════════════════════════════
 *
 *  归属：cnki-edu-math-ai-lecture
 *
 *  目的：`navigationMap` 与 `drawFunctions` 是**纯结构**（帧号如何分配到各环、
 *        各问），完全由 S2 的 totalIntro/subQuestions[].stages[].subSteps/finalSummary
 *        决定，**不需要模型推理**。把它们交给脚本，模型只专注写 drawFrame_N 主体。
 *
 *  帧分配规则（与 S3 提示词「导航顺序（展平规则）」一致）：
 *      frame 0            ← totalIntro
 *      然后按 subQuestions 顺序，每问依次：审题定向(1) → 破冰搭桥(1)
 *                                        → 规范建模 = subSteps.length
 *                                        → 独立总结(1)
 *      最后一帧            ← finalSummary
 *
 *  用法：
 *      node scripts/build-structure.js <s2.js> [--out <文件>] [--json]
 *      node scripts/build-structure.js <s2.js> --inject <s3.js> [--out <s3.patched.js>]
 *
 *    --inject <s3.js>  用生成结果替换 s3 中已有的 navigationMap…drawFunctions 段
 *    --out   <文件>     写出（默认打印到 stdout）
 *    --json           仅输出结构化摘要
 *
 *  退出码：0 成功 / 1 失败 / 2 参数错误
 * ══════════════════════════════════════════════════════════════════
 */

const fs = require('fs');
const path = require('path');
const vm = require('vm');

const SKILL = path.join(__dirname, '..');

/* ── 安全工具：锁定 vm 解析模型产物 + 输出路径白名单 ── */
function safeRun(code, filename) {
    const sandbox = {
        Math, JSON, Date, Array, Object, String, Number, Boolean, RegExp, Error,
        isNaN, isFinite, parseInt, parseFloat,
        console: { log() {}, error() {}, warn() {} }
    };
    sandbox.globalThis = sandbox;
    sandbox.window = sandbox;
    vm.createContext(sandbox);
    // 包裹成 IIFE：模型产物以 `return (...)` 形式求值（原 new Function 行为），
    // 而在 vm 脚本里顶层 return 非法，必须放进函数体内。
    return vm.runInContext('(function(){\n' + code + '\n})()', sandbox, { filename: filename || 'safe-eval.js' });
}

function assertSafeOutPath(p) {
    const abs = path.resolve(p);
    const roots = [process.cwd(), SKILL];
    const ok = roots.some(r => { const rp = path.resolve(r); return abs === rp || abs.startsWith(rp + path.sep); });
    if (!ok) { console.error('❌ 输出路径越界（仅允许工作区/技能目录内）：' + abs); process.exit(2); }
    return abs;
}

const argv = process.argv.slice(2);
let outOpt = null, injectPath = null, asJson = false, file = null;
for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--out' || a === '-o') { outOpt = argv[++i]; continue; }
    if (a === '--inject') { injectPath = argv[++i]; continue; }
    if (a === '--json') { asJson = true; continue; }
    if (a.startsWith('--')) { console.error('未知参数：' + a); process.exit(2); }
    if (!file) file = a;
}
if (!file || !fs.existsSync(file)) {
    console.error('用法：node scripts/build-structure.js <s2.js> [--out <文件>] [--inject <s3.js>] [--json]');
    process.exit(2);
}

const read = p => fs.readFileSync(p, 'utf8').replace(/^\uFEFF/, '').replace(/\r\n/g, '\n');

/* ── 解析 S2（裸对象） ── */
let s2;
{
    let t = read(file).trim().replace(/;\s*$/, '');
    if (!/^\{/.test(t)) { console.error('❌ S2 不是裸对象（应以 { 开头）'); process.exit(1); }
    try { s2 = safeRun('return (' + t + ');'); }
    catch (e) { console.error('❌ S2 解析失败：' + e.message); process.exit(1); }
}
if (!s2 || !Array.isArray(s2.subQuestions)) { console.error('❌ S2 缺 subQuestions 数组'); process.exit(1); }

/* ── 帧分配 ── */
let cursor = 1;                       // frame 0 = totalIntro
const qBlocks = [];
const errorList = [];

for (const q of s2.subQuestions) {
    const stages = Array.isArray(q.stages) ? q.stages : [];
    if (!stages.length) { errorList.push('第 ' + q.index + ' 问无 stages'); continue; }
    const stageBlocks = [];
    for (const st of stages) {
        const n = Array.isArray(st.subSteps) && st.subSteps.length ? st.subSteps.length : 1;
        if (n === 1) {
            stageBlocks.push({ name: st.stage, frame: cursor });
        } else {
            const arr = [];
            for (let k = 0; k < n; k++) arr.push(cursor + k);
            stageBlocks.push({ name: st.stage, frames: arr });
        }
        cursor += n;
    }
    qBlocks.push({ index: q.index, label: q.label, stages: stageBlocks });
}
const finalFrame = cursor;
const totalFrames = finalFrame + 1;

/* ── 生成代码 ── */
function genNavigationMap() {
    const L = [];
    L.push('const navigationMap = {');
    L.push('  totalIntro: 0,');
    L.push('  subQuestions: [');
    qBlocks.forEach((q, qi) => {
        L.push('    {');
        L.push('      index: ' + q.index + ', label: ' + JSON.stringify(q.label) + ',');
        L.push('      stages: [');
        q.stages.forEach((s, si) => {
            const body = s.frames
                ? 'frames: [' + s.frames.join(', ') + ']'
                : 'frame: ' + s.frame;
            L.push('        { stage: ' + JSON.stringify(s.name) + ', ' + body + ' }' + (si < q.stages.length - 1 ? ',' : ''));
        });
        L.push('      ]');
        L.push('    }' + (qi < qBlocks.length - 1 ? ',' : ''));
    });
    L.push('  ],');
    L.push('  finalSummary: ' + finalFrame);
    L.push('};');
    return L.join('\n');
}

function genDrawFunctions() {
    const items = [];
    for (let i = 0; i < totalFrames; i++) items.push('drawFrame_' + i);
    const L = ['const drawFunctions = ['];
    for (let i = 0; i < items.length; i += 5) {
        const chunk = items.slice(i, i + 5).join(', ');
        L.push('  ' + chunk + (i + 5 < items.length ? ',' : ''));
    }
    L.push('];');
    return L.join('\n');
}

const navCode = genNavigationMap();
const dfCode = genDrawFunctions();
const block = navCode + '\n\n' +
    '// ============================================================\n' +
    '//  5. drawFunctions 数组（脚本生成 · 索引即帧号）\n' +
    '// ============================================================\n\n' +
    dfCode + '\n';

/* ── 注入到 s3（可选） ── */
let injected = null;
if (injectPath) {
    if (!fs.existsSync(injectPath)) { console.error('❌ 找不到 --inject 文件：' + injectPath); process.exit(2); }
    let s3 = read(injectPath);
    const MARK = '@@STRUCTURE@@';
    /* 兼容模型实际写法：裸标记 @@STRUCTURE@@、行注释形式、以及 skill 文档约定的
       块注释形式（定界符包裹占位符）。必须把注释定界符一并替换掉，
       否则展开后的 navigationMap / drawFunctions 会被包进注释、页面加载即 ReferenceError。 */
    const MARK_RE = /\/\*\s*@@STRUCTURE@@\s*\*\/|\/\/\s*@@STRUCTURE@@|@@STRUCTURE@@/;

    if (MARK_RE.test(s3)) {
        /* 首选：S3 提示词要求模型只写占位标记，不写结构层 */
        const navIndent = '  ';
        const newBlock = block.trimEnd().split('\n').map(l => (l ? navIndent + l : l)).join('\n');
        s3 = s3.replace(MARK_RE, newBlock);
        console.log('已展开 S3 中的 ' + MARK + ' 占位标记 → ' + newBlock.split('\n').length + ' 行结构层');
    } else {
        /* 兼容：模型仍手写了结构层 → 整段替换 */
        const i = s3.indexOf('const navigationMap');
        const j = s3.indexOf('const drawFunctions');
        if (i < 0 || j < 0) {
            console.error('❌ s3 中既无 ' + MARK + ' 标记，也定位不到 navigationMap / drawFunctions 段');
            console.error('   请在 S3 产物里写一行 `/* ' + MARK + ' */` 作为占位。');
            process.exit(1);
        }
        const k = s3.indexOf('\n', s3.indexOf('];', j));
        if (k < 0) { console.error('❌ drawFunctions 数组未闭合'); process.exit(1); }
        const indent = '  ';
        const newBlock = block.trimEnd().split('\n').map(l => indent + l).join('\n');
        s3 = s3.slice(0, i) + newBlock + s3.slice(k);
        console.log('已替换 s3 的结构层（旧格式兼容）：' + block.split('\n').length + ' 行');
    }
    injected = s3;
}

/* ── 输出 ── */
const summary = {
    source: file,
    subQuestionCount: qBlocks.length,
    totalFrames,
    finalSummaryFrame: finalFrame,
    framesPerQuestion: qBlocks.map(q => ({ index: q.index, label: q.label, stages: q.stages })),
    errors: errorList
};

if (asJson) {
    console.log(JSON.stringify(summary, null, 2));
    process.exit(errorList.length ? 1 : 0);
}

if (outOpt) {
    assertSafeOutPath(outOpt);
    fs.writeFileSync(outOpt, injected !== null ? injected : block, 'utf8');
    console.log('已写出：' + outOpt + '（' + Buffer.byteLength(injected !== null ? injected : block, 'utf8') + ' 字节）');
} else if (injected === null) {
    console.log(block);
}

console.error('─'.repeat(60));
console.error('S2：' + qBlocks.length + ' 问　总帧数：' + totalFrames + '（0..' + finalFrame + '）');
qBlocks.forEach(q => {
    const parts = q.stages.map(s => s.frames ? (s.name + '=' + s.frames.join('/')) : (s.name + '=' + s.frame));
    console.error('  第' + q.index + '问 ' + q.label + '：' + parts.join('　'));
});
console.error('  总览=0　整题总结=' + finalFrame);
if (errorList.length) { console.error('❌ ' + errorList.join('；')); process.exit(1); }
process.exit(0);
