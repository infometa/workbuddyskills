#!/usr/bin/env node
// run.mjs — 设计感视频师统一 CLI(全程 Bash 调用)。
// 把 render-reel.mjs / tts-microsoft.mjs / build-manifest.mjs 的能力收成子命令,agent 只用这一个入口。
//
// 用法(所有命令 JSON → stdout,错误 → stderr + 非0退出):
//   node run.mjs init                                环境准备(装渲染依赖 + chrome + edge-tts,幂等)
//   node run.mjs unlock                               解锁完整主题库(本地翻标记,不下载)。
//        单 bundle 模型下,完整 manifest(50 主题)早已随插件分发在 render-bundle/manifest.full.json,
//        和 bundle 永远同版本——"解锁"只是在本地写一个标记文件,由 MCP 工具 `verify_connection`
//        (连接 VibeKnow 后调用,门禁在连接本身)通过之后调用本命令。
//        → {status:"unlocked",themes:50}
//   node run.mjs status                               查当前解锁状态(端上确定性检测,只看本地标记)。
//        agent 劝连接/解锁前先调,已 full 就别再劝。→ {unlocked,tier,themes,layouts,markerPath}
//   node run.mjs render <scenes.json> <out.mp4> [--bundle DIR] [--manifest FILE]
//        导出成片 → out.mp4 的路径(纯文本,不是 JSON);--bundle/--manifest 缺省走 resolveBundle()
//        (已 unlock 则用完整主题库,否则只认免费 manifest 的 serious-dark)
//   node run.mjs preview <scenes.json> <out.html> [--bundle DIR] [--manifest FILE]
//        导出自包含预览 HTML → out.html 的路径;--bundle/--manifest 缺省同上走 resolveBundle()
//   node run.mjs tts <文案> --out <NN.mp3> [--voice V]
//        合成旁白(微软 edge-tts,免费/免登录) → {audio_path,duration_sec,engine,voice}
//   node run.mjs build-manifest <JOBDIR>
//        把 JOBDIR 下的 NN.* 配对成 scenes.json → scenes.json 的路径
// 注意:render-reel.mjs / tts-microsoft.mjs / build-manifest.mjs 都不在顶层 import ——
// render-reel.mjs 会 import @remotion/renderer,若顶层 import 会导致 `init` 命令(负责装这个依赖)
// 在模块加载阶段就 ERR_MODULE_NOT_FOUND,先有鸡还是先有蛋。改成各命令处理函数内部按需动态 import。
import { spawnSync } from "node:child_process";
import { mkdirSync, readFileSync, writeFileSync, existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { resolveBundle } from "./resolve-bundle.mjs";
import { unlockMarkerPath } from "./pack-path.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));

const out = (obj) => process.stdout.write(typeof obj === "string" ? obj : JSON.stringify(obj));
const fail = (msg) => { process.stderr.write(String(msg) + "\n"); process.exit(1); };

function parseArgs(argv) {
  const pos = [], flags = {};
  for (let i = 0; i < argv.length; i++) {
    if (argv[i].startsWith("--")) {
      const k = argv[i].slice(2);
      const v = (argv[i + 1] !== undefined && !String(argv[i + 1]).startsWith("--")) ? argv[++i] : true;
      flags[k] = v;
    } else pos.push(argv[i]);
  }
  return { pos, flags };
}

const commands = {};

// 环境准备委托给 setup-env.mjs(同目录)。
commands.init = () => {
  const r = spawnSync(process.execPath, [join(HERE, "setup-env.mjs")], { stdio: "inherit" });
  process.exit(r.status || 0);
};

// 解锁完整主题库:本地翻一个标记文件,不下载任何东西。
// 单 bundle 模型:完整 manifest(50 主题)早已随插件分发在 render-bundle/manifest.full.json,
// 和 bundle 永远同版本——调用方(agent)应在 MCP 工具 `verify_connection` 返回成功(即连接 VibeKnow
// 完成,门禁在连接本身)之后再调用本命令。
commands.unlock = () => {
  const markerPath = unlockMarkerPath();
  mkdirSync(dirname(markerPath), { recursive: true });
  writeFileSync(markerPath, new Date().toISOString());
  const fullManifestPath = join(HERE, "../../../render-bundle/manifest.full.json");
  const themes = existsSync(fullManifestPath)
    ? JSON.parse(readFileSync(fullManifestPath, "utf8")).themes.length
    : 0;
  out({ status: "unlocked", themes });
};

// 端上确定性解锁状态检测:纯看本地标记(resolveBundle)判 tier,不打网、不误判。
// agent 在「主动劝连接 / 提示解锁 / 连接完成后」都应先跑本命令 —— 已 full 就别再劝、别重复 unlock,
// 消除"连了却还弹连接提示"的错位。→ {unlocked, tier, themes, layouts, markerPath}
commands.status = () => {
  const { manifestPath, tier } = resolveBundle();
  const manifest = JSON.parse(readFileSync(manifestPath, "utf8"));
  const count = (x) => (Array.isArray(x) ? x.length : 0);
  out({
    unlocked: tier === "full",
    tier,
    themes: count(manifest.themes),
    layouts: count(manifest.layouts),
    markerPath: unlockMarkerPath(),
  });
};

// 导出成片:scenes.json → out.mp4。--bundle/--manifest 缺省走 resolveBundle()(已 unlock 则完整包,否则免费包)。
commands.render = async (argv) => {
  const { pos, flags } = parseArgs(argv);
  const [scenesPath, outFile] = pos;
  if (!scenesPath || !outFile) fail("render: 用法 node run.mjs render <scenes.json> <out.mp4> [--bundle DIR] [--manifest FILE]");
  mkdirSync(dirname(outFile), { recursive: true });
  const resolved = resolveBundle();
  const bundleDir = typeof flags.bundle === "string" ? flags.bundle : resolved.bundleDir;
  const manifestPath = typeof flags.manifest === "string" ? flags.manifest : resolved.manifestPath;
  const { exportReel } = await import("./render-reel.mjs");
  const result = await exportReel({ scenesPath, out: outFile, bundleDir, manifestPath });
  out(result);
};

// 导出预览:scenes.json → out.html(自包含,可离线打开)。--bundle/--manifest 缺省同上走 resolveBundle()。
commands.preview = async (argv) => {
  const { pos, flags } = parseArgs(argv);
  const [scenesPath, outFile] = pos;
  if (!scenesPath || !outFile) fail("preview: 用法 node run.mjs preview <scenes.json> <out.html> [--bundle DIR] [--manifest FILE]");
  mkdirSync(dirname(outFile), { recursive: true });
  const resolved = resolveBundle();
  const bundleDir = typeof flags.bundle === "string" ? flags.bundle : resolved.bundleDir;
  const manifestPath = typeof flags.manifest === "string" ? flags.manifest : resolved.manifestPath;
  const { previewReel } = await import("./render-reel.mjs");
  const result = await previewReel({ scenesPath, out: outFile, bundleDir, manifestPath });
  out(result);
};

// 合成旁白(微软 edge-tts,免费/免登录)。--out 指定则直接落到该路径(如 <JOBDIR>/NN.mp3)。
commands.tts = async (argv) => {
  const { pos, flags } = parseArgs(argv);
  const text = pos[0] || (typeof flags.text === "string" ? flags.text : "");
  if (!text) fail('tts: 需要文案参数,如 node run.mjs tts "要朗读的旁白" --out 01.mp3');
  const voice = typeof flags.voice === "string" ? flags.voice : undefined;
  const outFile = typeof flags.out === "string" ? flags.out : undefined;
  if (outFile) mkdirSync(dirname(outFile), { recursive: true });
  const { synthesizeMicrosoft } = await import("./tts-microsoft.mjs");
  out(await synthesizeMicrosoft(text, { voice, out: outFile }));
};

// JOBDIR 下的 NN.* → scenes.json。
commands["build-manifest"] = async (argv) => {
  const { pos } = parseArgs(argv);
  const jobdir = pos[0];
  if (!jobdir) fail("build-manifest: 用法 node run.mjs build-manifest <JOBDIR>");
  const { buildManifest } = await import("./build-manifest.mjs");
  out(buildManifest(jobdir));
};

const [cmd, ...rest] = process.argv.slice(2);
const fn = commands[cmd];
if (!fn) fail(`unknown command: ${cmd || "(none)"}\ncommands: init, unlock, status, render, preview, tts, build-manifest`);
Promise.resolve().then(() => fn(rest)).catch((e) => fail((e && e.message) || e));
