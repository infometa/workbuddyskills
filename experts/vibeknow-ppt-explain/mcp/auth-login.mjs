#!/usr/bin/env node
// auth-login.mjs — go-account 设备码登录(RFC 8628)。token 写入固定路径(见 token-path.mjs)。
// 拆成 requestDeviceCode(要码) + pollForToken(轮询换token) 两半，便于 MCP `login` 工具做 in-chat 免终端登录。
import { writeFileSync } from "node:fs";
import { tokenFilePath, ensureTokenDir } from "./token-path.mjs";

// 默认走生产网关(按首段路由 /account → go-account)。本地/测试用 ACCOUNT_BASE 覆盖。
const DEFAULT_ACCOUNT = "https://vibeknow.com/account/v1";
// 引流来源标记：随设备码登录一起上报，后端据此统计"手绘专家带来的 vibeknow 登录"。
// 纯增量字段——后端不识别会自动忽略，不影响现有登录流程。可用 VIBEKNOW_LOGIN_CHANNEL 覆盖。
const LOGIN_CHANNEL = process.env.VIBEKNOW_LOGIN_CHANNEL || "workbuddy-ppt-explain";
// 引流双保险：把 utm 参数挂到展示给用户的验证链接上，登录页也能据此记录来源。可用 VIBEKNOW_LOGIN_UTM 覆盖。
const LOGIN_UTM = process.env.VIBEKNOW_LOGIN_UTM ?? "utm_source=workbuddy&utm_medium=ppt-explain";
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const accountBaseOf = (b) => b || process.env.ACCOUNT_BASE || DEFAULT_ACCOUNT;

// 给验证链接追加 utm 引流参数（不覆盖已有 query）。空串则原样返回。
function withUtm(url) {
  if (!LOGIN_UTM || typeof url !== "string" || !url) return url;
  return url + (url.includes("?") ? "&" : "?") + LOGIN_UTM;
}

// 持久化到固定路径(或显式 tokenFile)，0600 私有。写前建目录。
function persist(tok, tokenFile) {
  const file = tokenFile || tokenFilePath();
  ensureTokenDir();
  writeFileSync(file, JSON.stringify(tok), { mode: 0o600 });
}

// 解 atlas 标准信封 {code,message,data}：有 data 键则取 data，否则原样(容错扁平)。
function envData(j) {
  return (j && typeof j === "object" && "data" in j) ? j.data : j;
}

// 要设备码：go-account 返回 {code:0,data:{device_code,user_code,verification_uri,interval,expires_in}}。
export async function requestDeviceCode({ accountBase } = {}) {
  const base = accountBaseOf(accountBase);
  const r = await fetch(`${base}/auth/device/code`, {
    method: "POST", headers: { "content-type": "application/json" },
    body: JSON.stringify({ channel: LOGIN_CHANNEL }),
  });
  if (!r.ok) throw new Error(`device/code HTTP ${r.status}`);
  const j = await r.json();
  if (j && typeof j.code === "number" && j.code !== 0) throw new Error(`device/code: ${j.message || j.code}`);
  const data = envData(j);
  // 引流双保险(approach #2)：验证链接挂上 utm，登录页可据此记录来源。
  if (data && typeof data === "object") {
    if (typeof data.verification_uri === "string") data.verification_uri = withUtm(data.verification_uri);
    if (typeof data.verification_uri_complete === "string") data.verification_uri_complete = withUtm(data.verification_uri_complete);
  }
  return data;
}

// 轮询换取 token：go-account device/token 请求需带 grant_type;pending/slow_down/expired/denied
// 均 HTTP 200 + 业务 code(40010 pending / 40011 slow_down / 40012 expired / 40013 denied)。
// 成功 {code:0,data:{access_token,refresh_token,...}}。写入 tokenFile(默认固定路径);超时抛错。
export async function pollForToken({ accountBase, deviceCode, tokenFile, intervalMs = 5000, maxMs = 15 * 60 * 1000 } = {}) {
  const base = accountBaseOf(accountBase);
  const deadline = Date.now() + maxMs;
  let wait = intervalMs;
  for (;;) {
    await sleep(wait);
    const tr = await fetch(`${base}/auth/device/token`, {
      method: "POST", headers: { "content-type": "application/json" },
      body: JSON.stringify({ device_code: deviceCode, grant_type: "urn:ietf:params:oauth:grant-type:device_code" }),
    });
    const tj = await tr.json().catch(() => ({}));
    const data = envData(tj);
    const ok = (tj.code === 0 || tj.code == null);
    if (ok && data && data.access_token) {
      const tok = { access_token: data.access_token, refresh_token: data.refresh_token, obtained_at: Date.now() };
      persist(tok, tokenFile);
      return tok;
    }
    const msg = tj.message || tj.error || "";
    if (tj.code === 40011 || msg === "slow_down") wait += 5000;          // 放慢
    else if (tj.code === 40010 || msg === "authorization_pending") { /* 继续等 */ }
    else throw new Error(`设备码登录失败: ${msg || tj.code || "unknown"}`); // expired/denied/其它
    if (Date.now() > deadline) throw new Error("设备码授权超时，请重新发起登录");
  }
}

// 单次轮询(CLI login-status 用):打一发 device/token,不阻塞。成功即写 token 并返回
// {status:"success"};未授权 {status:"pending"};过期/拒绝/其它 {status:"error",error}。
export async function pollTokenOnce({ accountBase, deviceCode, tokenFile } = {}) {
  const base = accountBaseOf(accountBase);
  const tr = await fetch(`${base}/auth/device/token`, {
    method: "POST", headers: { "content-type": "application/json" },
    body: JSON.stringify({ device_code: deviceCode, grant_type: "urn:ietf:params:oauth:grant-type:device_code" }),
  });
  const tj = await tr.json().catch(() => ({}));
  const data = envData(tj);
  const ok = (tj.code === 0 || tj.code == null);
  if (ok && data && data.access_token) {
    persist({ access_token: data.access_token, refresh_token: data.refresh_token, obtained_at: Date.now() }, tokenFile);
    return { status: "success" };
  }
  const msg = tj.message || tj.error || "";
  if (tj.code === 40010 || msg === "authorization_pending") return { status: "pending" };
  if (tj.code === 40011 || msg === "slow_down") return { status: "pending", slow_down: true };
  return { status: "error", error: msg || String(tj.code || "unknown") };
}

// 完整阻塞式登录（CLI 用）：要码 → 打印 → 轮询。
export async function deviceLogin({ accountBase, tokenFile, pollMs = 3000, log = console.log } = {}) {
  const dc = await requestDeviceCode({ accountBase });
  log(`\n请在浏览器打开:  ${dc.verification_uri}\n输入验证码:      ${dc.user_code}\n等待授权...`);
  const tok = await pollForToken({ accountBase, deviceCode: dc.device_code, tokenFile, intervalMs: dc.interval ? dc.interval * 1000 : pollMs });
  log("登录成功 ✓");
  return tok;
}

export async function refreshAccessToken({ accountBase, refreshToken, tokenFile } = {}) {
  const base = accountBaseOf(accountBase);
  const r = await fetch(`${base}/auth/token/refresh`, {
    method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ refresh_token: refreshToken }),
  });
  if (!r.ok) throw new Error(`token/refresh HTTP ${r.status}`);
  const j = await r.json();
  if (j && typeof j.code === "number" && j.code !== 0) throw new Error(`token/refresh: ${j.message || j.code}`);
  const data = envData(j);
  const tok = { access_token: data.access_token, refresh_token: data.refresh_token || refreshToken, obtained_at: Date.now() };
  persist(tok, tokenFile);
  return tok;
}

// CLI:直接运行即触发阻塞式登录（WorkBuddy 内推荐用 `run.mjs login` + `login-status` 免终端）
if (process.argv[1] && import.meta.url === `file://${process.argv[1]}`) {
  deviceLogin().then(() => process.exit(0)).catch((e) => { console.error(e); process.exit(1); });
}
