#!/usr/bin/env node
'use strict';

/**
 * ══════════════════════════════════════════════════════════════════
 *  apply-s3.5.js —— S3.5「报告 / 代码分离」装配（v2 提速核心 · P0-A）
 * ══════════════════════════════════════════════════════════════════
 *
 *  归属：cnki-edu-math-ai-lecture
 *
 *  背景：原 S3.5 要求模型「即使零修正也要把整份绘图代码原样重打一遍」，
 *        本题实测输出 80.5 KB（其中 76.8 KB 是重抄的代码）——是全流程第二大
 *        输出黑洞，且重抄本身就是「抄写失真」风险的来源。
 *
 *  本脚本把「代码」从模型手里拿回来：模型只出报告（+ 必要时出局部补丁），
 *  代码由本脚本从 s3.assembled.js 取用/打补丁，产出仍是完整的 s3.5.js。
 *
 *  用法：
 *      node scripts/apply-s3.5.js <S3.5模型产物> <s3.assembled.js> [--out <文件>]
 *
 *  模型产物的三种形态（自动识别，向后兼容）：
 *      ① 报告 + 标记「@@NO_CHANGE@@」            → 报告 + 原代码拼接（零修正，最常见）
 *      ② 报告 + 标记「@@CHANGES_BEGIN@@」…「@@CHANGES_END@@」 → 应用局部补丁
 *         补丁组格式（可多组）：
 *             <<<OLD
 *             <原片段，逐字>
 *             OLD>>>
 *             <<<NEW
 *             <新片段，逐字>
 *             NEW>>>
 *      ③ 直接就是「报告 + 完整代码」（旧格式，passthrough）      → 原样写出
 *
 *  退出码：0 成功 / 1 补丁应用失败或产物非法 / 2 参数错误
 * ══════════════════════════════════════════════════════════════════
 */

const fs = require('fs');
const path = require('path');

const SKILL = path.join(__dirname, '..');

// 输出路径白名单：仅允许写回工作区(cwd)或技能目录(SKILL)内。
function assertSafeOutPath(p) {
    const abs = path.resolve(p);
    const roots = [process.cwd(), SKILL];
    const ok = roots.some(r => { const rp = path.resolve(r); return abs === rp || abs.startsWith(rp + path.sep); });
    if (!ok) { console.error('❌ 输出路径越界（仅允许工作区/技能目录内）：' + abs); process.exit(2); }
    return abs;
}

const argv = process.argv.slice(2);
let outOpt = null;
const positional = [];
for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--out' || a === '-o') { outOpt = argv[++i]; continue; }
    if (a.startsWith('--')) { console.error('未知参数：' + a); process.exit(2); }
    positional.push(a);
}
const [rawPath, asmPath] = positional;
if (!rawPath || !asmPath) {
    console.error('用法：node scripts/apply-s3.5.js <S3.5模型产物> <s3.assembled.js> [--out <文件>]');
    process.exit(2);
}
for (const p of [rawPath, asmPath]) {
    if (!fs.existsSync(p)) { console.error('❌ 文件不存在：' + p); process.exit(2); }
}

const read = p => fs.readFileSync(p, 'utf8').replace(/^\uFEFF/, '').replace(/\r\n/g, '\n');
let raw = read(rawPath).trim();
let asm = read(asmPath).trim();

/* 兜底：剥离 Markdown 代码块包裹 */
raw = raw.replace(/^\s*```[a-zA-Z]*\s*$/gm, '').trim();

const MARK = {
    NO_CHANGE: '@@NO_CHANGE@@',
    CB: '@@CHANGES_BEGIN@@',
    CE: '@@CHANGES_END@@'
};
const has = (s, m) => s.includes(m);

/* 报告段收尾清洗：剥掉标记残留的注释开头（/* 或 //）与空白 */
const tidyReport = s => s
    .replace(/\s*\/\*+\s*$/, '')
    .replace(/\s*\/\/+\s*$/, '')
    .trim();

let mode, report = '', finalCode = asm, applied = 0;

if (has(raw, MARK.NO_CHANGE)) {
    mode = 'nochange';
    report = tidyReport(raw.slice(0, raw.indexOf(MARK.NO_CHANGE)));
} else if (has(raw, MARK.CB) && has(raw, MARK.CE)) {
    mode = 'patch';
    const bi = raw.indexOf(MARK.CB);
    const ei = raw.indexOf(MARK.CE);
    report = tidyReport(raw.slice(0, bi));
    const seg = raw.slice(bi + MARK.CB.length, ei);

    const reGroup = /<<<OLD\r?\n([\s\S]*?)\r?\nOLD>>>[\s\S]*?<<<NEW\r?\n([\s\S]*?)\r?\nNEW>>>/g;
    const groups = [];
    let m;
    while ((m = reGroup.exec(seg)) !== null) groups.push({ old: m[1], neo: m[2] });

    if (!groups.length) {
        console.error('❌ patch 模式但未解析出任何 <<<OLD … OLD>>> <<<NEW … NEW>>> 组');
        process.exit(1);
    }
    for (let i = 0; i < groups.length; i++) {
        const { old, neo } = groups[i];
        const n = finalCode.split(old).length - 1;
        if (n === 0) {
            console.error(`❌ 第 ${i + 1} 组补丁的 OLD 片段在代码中未找到（必须逐字一致）。`);
            console.error('   建议：改用「报告 + 完整代码」旧格式，或修正 OLD 片段。');
            console.error('   OLD 首行：' + JSON.stringify(old.split('\n')[0].slice(0, 80)));
            process.exit(1);
        }
        if (n > 1) {
            console.error(`❌ 第 ${i + 1} 组补丁的 OLD 片段在代码中出现 ${n} 次，无法唯一定位。请扩大上下文使其唯一。`);
            process.exit(1);
        }
        finalCode = finalCode.replace(old, () => neo);
        applied++;
    }
} else {
    mode = 'passthrough';
    finalCode = raw;
    report = '';
}

/* 组装产物 */
let out;
if (mode === 'passthrough') {
    out = raw + '\n';
} else {
    if (!report) {
        console.error('❌ 未识别到校对报告注释块（报告必须是产物的第一段）。');
        process.exit(1);
    }
    out = report + '\n\n' + finalCode + '\n';
}

/* 自检 */
const problems = [];
if (!/window\.__DRAW_TIER__\s*=\s*'[ABC]'/.test(out)) problems.push('产物缺档位声明 window.__DRAW_TIER__');
if (!/抄写自检日志/.test(out)) problems.push('产物缺「抄写自检日志」注释块');
if (report && !/校对报告|校验报告|画布全面校对/.test(report)) problems.push('报告段未见「校对报告」标识');
if (mode === 'patch' && applied === 0) problems.push('patch 模式但零处应用');

const outPath = outOpt || rawPath.replace(/\.(js|md|txt)$/i, '') + '.applied.js';
assertSafeOutPath(outPath);
fs.writeFileSync(outPath, out, 'utf8');

console.log('模式　：' + mode);
console.log('补丁　：' + applied + ' 处应用');
if (!report) console.log('报告　：（passthrough，报告含在产物内）');
else console.log('报告　：' + report.split('\n').length + ' 行');
console.log('产物　：' + outPath + '　（' + Buffer.byteLength(out, 'utf8') + ' 字节）');
console.log('模型侧输出：' + Buffer.byteLength(raw, 'utf8') + ' 字节' +
    (mode === 'passthrough' ? '' : '　（相比重抄全文节省 ' +
        Math.round(100 - Buffer.byteLength(raw, 'utf8') / Buffer.byteLength(asm, 'utf8') * 100) + '%）'));

if (problems.length) {
    console.error('\n❌ 自检未通过：\n  - ' + problems.join('\n  - '));
    process.exit(1);
}
console.log('\n✅ 装配完成，自检通过');
process.exit(0);
