#!/usr/bin/env node
'use strict';

/**
 * ══════════════════════════════════════════════════════════════════
 *  assemble-html.js —— S4 脚本化装配（v2 提速核心 · P0-B）
 * ══════════════════════════════════════════════════════════════════
 *
 *  归属：cnki-edu-math-ai-lecture
 *  来源：与 配套快速版 同名脚本同一设计，**代码落在本 skill**。
 *
 *  作用：把「固定 HTML 骨架 + 3 份产物」脚本装配成完整讲题 HTML。
 *       替代原 S4「让模型重新输出整页 HTML（≈126 KB）」——
 *       这是全流程最大一块模型输出，砍掉即最大提速。
 *
 *  用法：
 *      node scripts/assemble-html.js <S1.js> <S2.js> <S3.js> [选项]
 *
 *  输入：
 *      S1 = Step1 产出（裸对象 {sentences, translations} 或两条 const 声明）
 *      S2 = Step2 产出（裸对象 questionData）
 *      S3 = Step3 产出（已经 assemble-artifact.js 注入两块内联库的裸绘图代码；
 *                        若 S3.5 走"报告/代码分离"，传 apply-s3.5.js 的产物）
 *
 *  选项：
 *      --title  "页面标题"    写入 <title>（默认「数学 · 讲题」）
 *      --qtitle "题型标题"    写入 QUESTION_TITLE（默认同 --title）
 *      --out    <文件路径>     输出路径（默认 <S3同名>.html）
 *      --quiet               只输出结论
 *
 *  退出码：0 成功 / 1 失败（含自检未过） / 2 参数错误
 *
 *  ⚠️ 实现要点：所有替换用「函数式 replacement」，避免 $& / $$ 等
 *     被 String.replace 特殊解释——题目文本与绘图代码里都含 $...$ 公式。
 * ══════════════════════════════════════════════════════════════════
 */

const fs = require('fs');
const path = require('path');
const vm = require('vm');

const SKILL = path.join(__dirname, '..');
const TPL_PATH = path.join(SKILL, 'references', 'html-template.html');

/* ── 安全工具：锁定 vm 解析模型产物 + 输出路径白名单 ── */
// safeRun：仅暴露纯数据构造所需最小全局，不挂 process/require/fs，
// 避免模型产物经 new Function 在 Node 主上下文拿到敏感全局（如 process）。
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

// assertSafeOutPath：仅允许写回工作区(cwd)或技能目录(SKILL)内，
// 拒绝越界绝对路径（如系统目录），满足沙箱 FS 检测。
function assertSafeOutPath(p) {
    const abs = path.resolve(p);
    const roots = [process.cwd(), SKILL];
    const ok = roots.some(r => { const rp = path.resolve(r); return abs === rp || abs.startsWith(rp + path.sep); });
    if (!ok) { console.error('❌ 输出路径越界（仅允许工作区/技能目录内）：' + abs); process.exit(2); }
    return abs;
}

/* ── 参数解析 ── */
const argv = process.argv.slice(2);
const flags = {};
const positional = [];
for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--quiet') { flags.quiet = true; continue; }
    if (a === '--title') { flags.title = argv[++i]; continue; }
    if (a === '--qtitle') { flags.qtitle = argv[++i]; continue; }
    if (a === '--out') { flags.out = argv[++i]; continue; }
    if (a === '--generic') { flags.generic = true; continue; }
    if (a.startsWith('--')) { console.error('未知参数：' + a); process.exit(2); }
    positional.push(a);
}
const [s1Path, s2Path, s3Path] = positional;
if (!s1Path || !s2Path || !s3Path) {
    console.error('用法：node scripts/assemble-html.js <S1.js> <S2.js> <S3.js> [--title ...] [--qtitle ...] [--out ...]');
    process.exit(2);
}
for (const p of [s1Path, s2Path, s3Path, TPL_PATH]) {
    if (!fs.existsSync(p)) { console.error('❌ 文件不存在：' + p); process.exit(2); }
}

const read = p => fs.readFileSync(p, 'utf8').replace(/^\uFEFF/, '').replace(/\r\n/g, '\n');
let tpl = read(TPL_PATH);
const s1Src = read(s1Path).trim();
let s2Src = read(s2Path).trim();
let s3Src = read(s3Path).trim();

const IND = '        ';   // 模板 script 内主缩进（8 空格）

/* ── 1) 解析 S1 ── */
function parseS1(src) {
    const cleaned = src.replace(/^\s*\/\/.*$/gm, '').trim();
    let obj;
    if (/^\{/.test(cleaned)) {
        obj = safeRun('return (' + cleaned + ');');
    } else {
        obj = safeRun(cleaned + '\n;return { sentences: sentences, translations: translations };');
    }
    if (!obj || !Array.isArray(obj.sentences) || !Array.isArray(obj.translations)) {
        throw new Error('S1 未能解析出 sentences / translations 数组');
    }
    return obj;
}

let s1;
try { s1 = parseS1(s1Src); }
catch (e) { console.error('❌ S1 解析失败：' + e.message); process.exit(1); }

/* ── 2) 规范化 S2（裸对象 questionData） ── */
s2Src = s2Src.replace(/;\s*$/, '').trim();
if (!/^\{/.test(s2Src)) { console.error('❌ S2 不是裸对象（应以 { 开头）'); process.exit(1); }

/* ── 3) 规范化 S3（裸绘图代码，整体缩进） ── */
s3Src = s3Src.replace(/^\s*```[a-zA-Z]*\s*$/gm, '').trim();   // 兜底剥离代码块包裹
const s3Decl = s3Src.split('\n').map(l => (l ? IND + l : l)).join('\n');

/* ── 4) 生成各槽位正文 ── */
const s1SentencesDecl = 'const sentences = [\n' +
    s1.sentences.map(x => IND + '    ' + JSON.stringify(x)).join(',\n') + '\n' + IND + '];';
const s1TranslationsDecl = 'const translations = [\n' +
    s1.translations.map(t => IND + '    { original: ' + JSON.stringify(t.original) + ', math: ' + JSON.stringify(t.math) + ' }').join(',\n') + '\n' + IND + '];';
const s2Decl = 'const questionData = ' + s2Src + ';';

const title = flags.title || '数学 · 讲题';
const qtitle = flags.qtitle || title;

/* ── 5) 槽位替换（函数式，避免 $ 被特殊解释） ── */
tpl = tpl.replace('/* @@S1_SENTENCES@@ */', () => s1SentencesDecl);
tpl = tpl.replace('/* @@S1_TRANSLATIONS@@ */', () => s1TranslationsDecl);
tpl = tpl.replace('/* @@S2_QUESTIONDATA@@ */', () => s2Decl);
tpl = tpl.replace('/* @@S3_DRAWING@@ */', () => s3Decl);
tpl = tpl.replace('@@PAGE_TITLE@@', () => title);
tpl = tpl.replace('@@QUESTION_TITLE_JSON@@', () => JSON.stringify(qtitle));

/* ── 6) 自检 ── */
const checks = [];
const check = (name, cond, detail) => checks.push({ name, pass: !!cond, detail: detail || '' });

check('产物以 <!DOCTYPE html> 开头', tpl.startsWith('<!DOCTYPE html>'));
check('无残留 @@ 槽位标记', !tpl.includes('@@'));
check('含 sentences 数据', /const\s+sentences\s*=\s*\[[\s\S]*?\];/.test(tpl));
check('含 translations 数据', /const\s+translations\s*=\s*\[[\s\S]*?\];/.test(tpl));
check('含 questionData', /const\s+questionData\s*=\s*\{[\s\S]*\}/.test(tpl));
check('含档位声明 __DRAW_TIER__', /window\.__DRAW_TIER__\s*=\s*'[ABC]'/.test(tpl));
check('含两块库 LIB', /const\s+LIB\s*=\s*\(\s*function\s*\(/.test(tpl));
check('含 qAcc/switchQ/recQ', /\bqAcc\b/.test(tpl) && /function\s+switchQ/.test(tpl) && /function\s+recQ/.test(tpl));
check('含 navigationMap / drawFunctions', /\bnavigationMap\b/.test(tpl) && /\bdrawFunctions\b/.test(tpl));
check('含 cleanVoiceText / latexToSpeech', /function\s+cleanVoiceText/.test(tpl) && /function\s+latexToSpeech/.test(tpl));
check('含 ctx 前置', /const\s+ctx\s*=\s*canvasEl\.getContext\('2d'\)/.test(tpl));
check('含抄写自检日志块', /抄写自检日志/.test(tpl));
check('questionData 无 highlight 字段', !/\bhighlight\s*:/.test(s2Src));

// 主 <script> 语法可编译（vm，不执行，无需 DOM）
let syntaxOk = false, syntaxMsg = '';
{
    const m = tpl.match(/<script>\n([\s\S]*?)\n\s*<\/script>/);
    if (!m) syntaxMsg = '未定位到主 <script> 块';
    else {
        try { new vm.Script(m[1], { filename: 'lecture-inline.js' }); syntaxOk = true; }
        catch (e) { syntaxMsg = e.message; }
    }
}
check('内联主脚本语法可编译', syntaxOk, syntaxMsg);

/* ── 6.5) 通用版横幅（--generic 时注入，替换模板占位） ── */
const genericBanner = flags.generic
    ? '<div class="generic-banner">⚠ 通用版 · 未接入知网基教，本题解析由模型生成，非知网标准解析</div>'
    : '';
tpl = tpl.replace('<!-- @@GENERIC_BANNER@@ -->', genericBanner);

/* ── 7) 写出 ── */
const outPath = flags.out || s3Path.replace(/\.js$/i, '') + '.html';
assertSafeOutPath(outPath);
fs.writeFileSync(outPath, tpl, 'utf8');

const failed = checks.filter(c => !c.pass);
if (!flags.quiet) {
    console.log('产物：' + outPath);
    console.log('行数：' + tpl.split('\n').length + '　字节：' + Buffer.byteLength(tpl, 'utf8'));
    console.log('标题：PAGE=' + JSON.stringify(title) + '　QUESTION_TITLE=' + JSON.stringify(qtitle));
    console.log('─'.repeat(56));
    for (const c of checks) console.log((c.pass ? '  ✅ ' : '  ❌ ') + c.name + (c.detail ? '　—— ' + c.detail : ''));
}
if (failed.length) {
    console.error('\n❌ 装配自检未通过 ' + failed.length + ' 项：' + failed.map(f => f.name).join('；'));
    process.exit(1);
}
if (!flags.quiet) console.log('\n✅ 装配完成，全部 ' + checks.length + ' 项自检通过');
process.exit(0);
