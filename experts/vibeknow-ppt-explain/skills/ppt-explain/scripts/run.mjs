#!/usr/bin/env node
// run.mjs — 手绘专家统一 CLI（替代 MCP，全程 Bash 调用，零连接器）。
// 复用 mcp/ 下的客户端函数(server.mjs 的 callSynthesize/loadStyles/readTokenObj +
// auth-login.mjs 的设备码登录),把原 MCP 工具变成子命令。
//
// 用法(所有命令 JSON → stdout,错误 → stderr + 非0退出):
//   node run.mjs init                 环境准备(装 render + chrome;mcp 已零依赖)
//   node run.mjs login                发起登录 → {status:"pending",verification_uri,user_code,expires_in}
//   node run.mjs login-status         查登录 → {status:"success"|"pending"|"error"|"idle"}
//   node run.mjs synthesize <文案> [--engine microsoft|vibeknow] [--voice V] [--out FILE]
//        合成旁白 → {audio_path,duration_sec}。默认引擎 microsoft(edge-tts,免费/免登录/不扣积分);
//        vibeknow 为可选高级音色(需登录+积分)。积分不足 → stdout {error:"insufficient_credits",service} + 非0退出。
//   node run.mjs list-styles          列风格 → [{id,name,desc}]
// (手绘绘制用同目录的 handdraw-page.mjs:逐页 NN.png → NN.vec.json,按图名派生、结构上杜绝错位。
//  掏钱前的出图尺寸预检见 check-images.mjs 的 CLI。)
import { spawnSync } from "node:child_process";
import { readFileSync, writeFileSync, existsSync, copyFileSync, mkdirSync } from "node:fs";
import { dirname, join, basename } from "node:path";
import { fileURLToPath } from "node:url";
import { loadStyles, callSynthesize, readTokenObj } from "../../../mcp/server.mjs";
import { synthesizeMicrosoft } from "./tts-microsoft.mjs";
import { requestDeviceCode, pollTokenOnce } from "../../../mcp/auth-login.mjs";
import { tokenFilePath } from "../../../mcp/token-path.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const pendingPath = () => join(dirname(tokenFilePath()), "login-pending.json");
const out = (obj) => process.stdout.write(JSON.stringify(obj));
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

// 发起设备码登录:要码 → 存 pending(供 login-status 轮询) → 打印链接+验证码。
commands.login = async () => {
  if (readTokenObj().access_token) { out({ status: "already_logged_in" }); return; }
  const dc = await requestDeviceCode({});
  mkdirSync(dirname(pendingPath()), { recursive: true });
  writeFileSync(pendingPath(), JSON.stringify({ device_code: dc.device_code, interval: dc.interval || 3 }));
  out({ status: "pending", verification_uri: dc.verification_uri, user_code: dc.user_code, expires_in: dc.expires_in });
};

// 单次查登录:已登录=success;否则用 pending 的 device_code 打一发轮询。
commands["login-status"] = async () => {
  if (readTokenObj().access_token) { out({ status: "success" }); return; }
  if (!existsSync(pendingPath())) { out({ status: "idle" }); return; }
  const p = JSON.parse(readFileSync(pendingPath(), "utf8"));
  out(await pollTokenOnce({ deviceCode: p.device_code }));
};

// 合成旁白;--out 指定则直接落到该路径(如 <JOBDIR>/NN.mp3)。
// 默认引擎 microsoft(免费);vibeknow 为可选高级音色(需登录+积分,余额不足会结构化报错)。
commands.synthesize = async (argv) => {
  const { pos, flags } = parseArgs(argv);
  const text = pos[0] || (typeof flags.text === "string" ? flags.text : "");
  if (!text) fail("synthesize: 需要文案参数,如 node run.mjs synthesize \"要朗读的旁白\"");
  const engine = typeof flags.engine === "string" ? flags.engine : "microsoft";
  const voice = typeof flags.voice === "string" ? flags.voice : undefined;
  const outFile = typeof flags.out === "string" ? flags.out : undefined;
  if (outFile) mkdirSync(dirname(outFile), { recursive: true });
  if (engine === "microsoft") {
    out(synthesizeMicrosoft(text, { voice, out: outFile }));
    return;
  }
  if (engine === "vibeknow") {
    const r = await callSynthesize(text, voice);
    if (outFile) { copyFileSync(r.audio_path, outFile); r.audio_path = outFile; }
    out(r);
    return;
  }
  fail(`synthesize: 未知引擎 ${engine}(可选 microsoft|vibeknow)`);
};

commands["list-styles"] = () => out(loadStyles());

const [cmd, ...rest] = process.argv.slice(2);
const fn = commands[cmd];
if (!fn) fail(`unknown command: ${cmd || "(none)"}\ncommands: init, login, login-status, synthesize, list-styles`);
Promise.resolve(fn(rest)).catch((e) => {
  // 积分不足:结构化输出到 stdout(供 agent 识别 → 引导充值/改引擎)+ 非0退出。
  if (e && e.insufficientCredits) { out({ error: "insufficient_credits", service: e.service || "unknown" }); process.exit(2); }
  fail((e && e.message) || e);
});
