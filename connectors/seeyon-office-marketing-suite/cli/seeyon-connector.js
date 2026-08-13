#!/usr/bin/env node
"use strict";

/**
 * Seeyon WorkBuddy 连接器认证 CLI。by AI.Coding
 *
 * 环境变量账号认证优先；缺少账号或密码时，启动隔离浏览器并通过 Chrome DevTools
 * Protocol 读取登录后的 Cookie，再将会话加密保存在当前用户目录。
 */

const crypto = require("crypto");
const fs = require("fs");
const http = require("http");
const os = require("os");
const path = require("path");
const { spawn, spawnSync } = require("child_process");

const CONNECTOR_HOME = path.resolve(process.env.SEEYON_CONNECTOR_HOME || path.join(__dirname, ".."));
const CONFIG_PATH = path.join(CONNECTOR_HOME, "connector-config.json");
const STATE_DIR = path.join(os.homedir(), ".workbuddy", "seeyon-connector");
const KEY_PATH = path.join(STATE_DIR, "session.key");
const SESSION_PATH = path.join(STATE_DIR, "session.enc.json");
const AUTH_TRACE_PATH = path.join(STATE_DIR, "auth-trace.log");
const SESSION_MAX_AGE_MS = 12 * 60 * 60 * 1000;

/**
 * 记录不含密码和 Cookie 的本地认证轨迹，便于诊断浏览器地址切换。by AI.Coding
 */
function traceAuth(event, details = {}) {
  try {
    fs.mkdirSync(STATE_DIR, { recursive: true, mode: 0o700 });
    const safeDetails = Object.fromEntries(Object.entries(details).map(([key, value]) => {
      if (key.toLowerCase().includes("url")) {
        try {
          const parsed = new URL(String(value));
          return [key, `${parsed.protocol}//${parsed.host}${parsed.pathname}`];
        } catch {
          return [key, "invalid-url"];
        }
      }
      return [key, value];
    }));
    fs.appendFileSync(AUTH_TRACE_PATH, `${JSON.stringify({ at: new Date().toISOString(), event, ...safeDetails })}\n`, {
      encoding: "utf8",
      mode: 0o600,
    });
    protectFile(AUTH_TRACE_PATH);
  } catch {
    // 诊断日志不可用不能阻断 OA 登录。
  }
}

/** 读取并校验连接器配置。 */
function loadConfig() {
  const config = JSON.parse(fs.readFileSync(CONFIG_PATH, "utf8"));
  const forcedServiceUrl = process.env.OA_BASE_URL?.trim();
  const previousServiceUrl = forcedServiceUrl ? null : loadSession(true)?.serviceUrl;
  const serviceUrl = normalizeServiceUrl(
    forcedServiceUrl || previousServiceUrl || process.env.SEEYON_SERVICE_URL || config.serviceUrl,
  );
  return {
    serviceUrl,
    serviceUrlLocked: Boolean(forcedServiceUrl),
    loginUrl: new URL(config.loginPath || "main.do?method=login", `${serviceUrl}/`).toString(),
    loginTimeoutSeconds: Math.min(Number(config.loginTimeoutSeconds || 280), 280),
  };
}

/** 规范化服务地址，避免把会话发送到非 HTTP(S) 目标。 */
function normalizeServiceUrl(value) {
  const parsed = new URL(String(value || "").trim());
  if (!/^https?:$/.test(parsed.protocol)) {
    throw new Error("OA service URL must use HTTP or HTTPS");
  }
  parsed.hash = "";
  parsed.search = "";
  const segments = parsed.pathname.split("/").filter(Boolean);
  const seeyonIndex = segments.findIndex((segment) => segment.toLowerCase() === "seeyon");
  if (seeyonIndex >= 0) {
    parsed.pathname = `/${segments.slice(0, seeyonIndex + 1).join("/")}`;
  } else if (parsed.pathname.toLowerCase().endsWith(".do")) {
    parsed.pathname = parsed.pathname.replace(/\/[^/]*$/, "");
  }
  return parsed.toString().replace(/\/$/, "");
}

/**
 * 从浏览器页面地址生成可验证的 OA 服务地址候选；强制地址模式下禁止切换。by AI.Coding
 */
function deriveCandidateServiceUrls(targetUrls, config) {
  if (config.serviceUrlLocked) return [config.serviceUrl];
  const candidates = [];
  for (const value of targetUrls) {
    try {
      const parsed = new URL(String(value || "").trim());
      const segments = parsed.pathname.split("/").filter(Boolean);
      const looksLikeSeeyon = segments.some((segment) => segment.toLowerCase() === "seeyon")
        || parsed.pathname.toLowerCase().endsWith(".do");
      if (!/^https?:$/.test(parsed.protocol) || !looksLikeSeeyon) continue;
      const candidate = normalizeServiceUrl(parsed.toString());
      if (!candidates.includes(candidate)) candidates.push(candidate);
    } catch {
      // 地址栏可能处于输入中或打开浏览器内部页面，忽略后继续等待有效 OA 地址。
    }
  }
  if (!candidates.includes(config.serviceUrl)) candidates.push(config.serviceUrl);
  return candidates;
}

/** 限制敏感文件仅由当前用户访问。 */
function protectFile(filePath) {
  try {
    fs.chmodSync(filePath, 0o600);
    if (process.platform === "win32") {
      const user = os.userInfo().username;
      spawnSync("icacls", [filePath, "/inheritance:r", "/grant:r", `${user}:F`], {
        windowsHide: true,
        stdio: "ignore",
      });
    }
  } catch {
    // 用户目录本身仍提供基础保护；权限收紧失败不输出路径或秘密。
  }
}

/** 创建或读取本地 AES-256 密钥。 */
function loadKey() {
  fs.mkdirSync(STATE_DIR, { recursive: true, mode: 0o700 });
  if (!fs.existsSync(KEY_PATH)) {
    fs.writeFileSync(KEY_PATH, crypto.randomBytes(32), { mode: 0o600, flag: "wx" });
    protectFile(KEY_PATH);
  }
  const key = fs.readFileSync(KEY_PATH);
  if (key.length !== 32) throw new Error("Invalid local session key");
  return key;
}

/** 使用 AES-256-GCM 加密保存会话。 */
function saveSession(session) {
  const iv = crypto.randomBytes(12);
  const cipher = crypto.createCipheriv("aes-256-gcm", loadKey(), iv);
  const plaintext = Buffer.from(JSON.stringify(session), "utf8");
  const ciphertext = Buffer.concat([cipher.update(plaintext), cipher.final()]);
  const payload = {
    version: 1,
    iv: iv.toString("base64"),
    tag: cipher.getAuthTag().toString("base64"),
    ciphertext: ciphertext.toString("base64"),
  };
  const tempPath = `${SESSION_PATH}.${process.pid}.tmp`;
  fs.writeFileSync(tempPath, JSON.stringify(payload), { mode: 0o600 });
  fs.renameSync(tempPath, SESSION_PATH);
  protectFile(SESSION_PATH);
}

/** 解密读取本地会话；损坏或过期时返回空。 */
function loadSession(allowExpired = false) {
  if (!fs.existsSync(SESSION_PATH) || !fs.existsSync(KEY_PATH)) return null;
  try {
    const payload = JSON.parse(fs.readFileSync(SESSION_PATH, "utf8"));
    const decipher = crypto.createDecipheriv("aes-256-gcm", loadKey(), Buffer.from(payload.iv, "base64"));
    decipher.setAuthTag(Buffer.from(payload.tag, "base64"));
    const plaintext = Buffer.concat([
      decipher.update(Buffer.from(payload.ciphertext, "base64")),
      decipher.final(),
    ]);
    const session = JSON.parse(plaintext.toString("utf8"));
    if (!allowExpired && Date.now() - Number(session.savedAt || 0) > SESSION_MAX_AGE_MS) return null;
    return session;
  } catch {
    return null;
  }
}

/** 查找 Chrome 或 Edge。 */
function findBrowser() {
  const candidates = process.platform === "win32"
    ? [
        path.join(process.env.PROGRAMFILES || "C:\\Program Files", "Google", "Chrome", "Application", "chrome.exe"),
        path.join(process.env["PROGRAMFILES(X86)"] || "C:\\Program Files (x86)", "Microsoft", "Edge", "Application", "msedge.exe"),
        path.join(process.env.PROGRAMFILES || "C:\\Program Files", "Microsoft", "Edge", "Application", "msedge.exe"),
      ]
    : process.platform === "darwin"
      ? ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"]
      : ["/usr/bin/google-chrome", "/usr/bin/google-chrome-stable", "/usr/bin/microsoft-edge", "/usr/bin/chromium"];
  const found = candidates.find((candidate) => fs.existsSync(candidate));
  if (!found) throw new Error("Chrome or Edge is required for interactive OA login");
  return found;
}

/** 获取一个临时本地端口。 */
function reservePort() {
  return new Promise((resolve, reject) => {
    const server = http.createServer();
    server.once("error", reject);
    server.listen(0, "127.0.0.1", () => {
      const address = server.address();
      server.close(() => resolve(address.port));
    });
  });
}

/** 等待指定时间，不执行阻塞睡眠。 */
function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * 等待登录浏览器主进程退出，避免 Windows 仍占用用户数据目录。by AI.Coding
 */
function waitForChildExit(child, timeoutMs) {
  if (child.exitCode !== null) return Promise.resolve(true);
  return new Promise((resolve) => {
    let settled = false;
    const finish = (exited) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      child.removeListener("exit", onExit);
      resolve(exited);
    };
    const onExit = () => finish(true);
    const timer = setTimeout(() => finish(false), timeoutMs);
    child.once("exit", onExit);
  });
}

/**
 * 关闭隔离登录浏览器，并给 Chromium 子进程释放文件句柄的时间。by AI.Coding
 */
async function closeLoginBrowser(child, webSocketUrl) {
  if (webSocketUrl) await cdpCommand(webSocketUrl, "Browser.close").catch(() => {});
  let exited = await waitForChildExit(child, 5000);
  if (!exited && child.exitCode === null) {
    try {
      child.kill();
    } catch {
      // 浏览器可能恰好已退出；后续目录清理仍会执行带重试的安全回收。
    }
    exited = await waitForChildExit(child, 2000);
  }
  if (exited) await delay(250);
}

/**
 * 安全清理临时浏览器目录；清理失败不能覆盖已经成功的 OA 认证结果。by AI.Coding
 */
function cleanupBrowserProfile(profileDir, options = {}) {
  if (path.dirname(profileDir) !== os.tmpdir() || !path.basename(profileDir).startsWith("seeyon-connector-")) {
    return false;
  }
  const removeSync = options.removeSync || fs.rmSync;
  const warn = options.warn || ((message) => process.stderr.write(`${message}\n`));
  try {
    // Windows 上 Chromium 退出后仍可能短暂锁定 Account Web Data，使用原生重试等待句柄释放。
    removeSync(profileDir, { recursive: true, force: true, maxRetries: 10, retryDelay: 200 });
    return true;
  } catch (error) {
    warn(`Seeyon connector warning: temporary browser profile cleanup was deferred (${error.code || "unknown"}).`);
    return false;
  }
}

/** 从调试端点读取浏览器 WebSocket 地址。 */
async function waitForDebugger(port, deadline) {
  while (Date.now() < deadline) {
    try {
      const response = await fetch(`http://127.0.0.1:${port}/json/version`);
      if (response.ok) {
        const data = await response.json();
        if (data.webSocketDebuggerUrl) return data.webSocketDebuggerUrl;
      }
    } catch {
      // 浏览器仍在启动，继续轮询。
    }
    await delay(250);
  }
  throw new Error("Browser debugging endpoint did not start");
}

/** 执行一个 Chrome DevTools Protocol 命令。 */
function cdpCommand(webSocketUrl, method, params = {}) {
  return new Promise((resolve, reject) => {
    const socket = new WebSocket(webSocketUrl);
    const id = 1;
    const timer = setTimeout(() => {
      socket.close();
      reject(new Error(`CDP command timed out: ${method}`));
    }, 5000);
    socket.addEventListener("open", () => socket.send(JSON.stringify({ id, method, params })));
    socket.addEventListener("message", (event) => {
      const message = JSON.parse(String(event.data));
      if (message.id !== id) return;
      clearTimeout(timer);
      socket.close();
      if (message.error) reject(new Error(`CDP command failed: ${method}`));
      else resolve(message.result || {});
    });
    socket.addEventListener("error", () => {
      clearTimeout(timer);
      reject(new Error(`CDP connection failed: ${method}`));
    });
  });
}

/**
 * 读取全部页面的当前地址，并按用户最近导航后的页面顺序生成 OA 候选地址。by AI.Coding
 */
async function readCandidateServiceUrls(webSocketUrl, config) {
  if (config.serviceUrlLocked) return [config.serviceUrl];
  let pageUrls = [];
  try {
    const endpoint = new URL(webSocketUrl);
    const response = await fetch(`http://${endpoint.host}/json/list`);
    if (response.ok) {
      const targets = await response.json();
      pageUrls = targets.filter((target) => target.type === "page" && target.url).map((target) => target.url);
    }
  } catch {
    // HTTP 调试端点不可用时继续使用 CDP Target 域读取页面。
  }
  if (pageUrls.length === 0) {
    const result = await cdpCommand(webSocketUrl, "Target.getTargets");
    pageUrls = (result.targetInfos || [])
      .filter((target) => target.type === "page" && target.url)
      .map((target) => target.url);
  }
  traceAuth("browser-pages", { count: pageUrls.length, pageUrls: pageUrls.join(" | ") });
  return deriveCandidateServiceUrls(pageUrls, config);
}

/** 读取目标 OA 域的认证 Cookie。 */
async function readAuthCookies(webSocketUrl, serviceUrl) {
  const result = await cdpCommand(webSocketUrl, "Storage.getCookies");
  const hostname = new URL(serviceUrl).hostname.toLowerCase();
  const matchesHost = (domain) => hostname === String(domain || "").replace(/^\./, "").toLowerCase()
    || hostname.endsWith(`.${String(domain || "").replace(/^\./, "").toLowerCase()}`);
  const cookies = (result.cookies || []).filter((cookie) => matchesHost(cookie.domain));
  const findLast = (name) => cookies.filter((cookie) => cookie.name === name && cookie.value).at(-1)?.value || null;
  return { JSESSIONID: findLast("JSESSIONID"), route: findLast("route") };
}

/** 调用只读 meetingInfo 接口验证会话并取得当前登录名。 */
async function verifySession(serviceUrl, cookies) {
  if (!cookies.JSESSIONID) return null;
  const cookieHeader = [`JSESSIONID=${cookies.JSESSIONID}`, cookies.route ? `route=${cookies.route}` : null]
    .filter(Boolean)
    .join("; ");
  const body = new URLSearchParams({
    managerMethod: "meetingInfo",
    arguments: JSON.stringify([{ meetingId: "", templateId: "" }]),
  });
  try {
    const response = await fetch(`${serviceUrl}/ajax.do?method=ajaxAction&managerName=meetingAjaxManager&nn=meetingInfo`, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
        Cookie: cookieHeader,
      },
      body,
      redirect: "manual",
    });
    const text = await response.text();
    if (!response.ok || text.trim() === "__LOGOUT") return null;
    const payload = JSON.parse(text);
    const currentUser = payload.currentUser || {};
    if (currentUser.loginState !== "ok" || !currentUser.loginName) return null;
    return String(currentUser.loginName);
  } catch {
    return null;
  }
}

/** 启动隔离浏览器，等待用户完成 OA 登录并保存会话。 */
async function interactiveAuth(config) {
  const browser = findBrowser();
  const port = await reservePort();
  const profileDir = fs.mkdtempSync(path.join(os.tmpdir(), "seeyon-connector-"));
  const deadline = Date.now() + config.loginTimeoutSeconds * 1000;
  const child = spawn(browser, [
    `--remote-debugging-port=${port}`,
    "--remote-debugging-address=127.0.0.1",
    "--remote-allow-origins=*",
    `--user-data-dir=${profileDir}`,
    "--no-first-run",
    "--no-default-browser-check",
    "--new-window",
    config.loginUrl,
  ], { detached: false, stdio: "ignore", windowsHide: false });
  traceAuth("auth-started", { serviceUrl: config.serviceUrl, locked: config.serviceUrlLocked });

  let webSocketUrl;
  try {
    webSocketUrl = await waitForDebugger(port, deadline);
    while (Date.now() < deadline) {
      const serviceUrls = await readCandidateServiceUrls(webSocketUrl, config).catch(() => [config.serviceUrl]);
      for (const serviceUrl of serviceUrls) {
        const cookies = await readAuthCookies(webSocketUrl, serviceUrl).catch(() => ({ JSESSIONID: null, route: null }));
        traceAuth("candidate-checked", { serviceUrl, hasSession: Boolean(cookies.JSESSIONID) });
        const username = await verifySession(serviceUrl, cookies);
        if (username) {
          // 只保存通过 Seeyon 会话校验的实际地址，地址栏中的无关页面不会改变后续服务目标。
          saveSession({
            serviceUrl,
            username,
            JSESSIONID: cookies.JSESSIONID,
            route: cookies.route,
            savedAt: Date.now(),
          });
          traceAuth("auth-succeeded", { serviceUrl, username });
          return;
        }
      }
      if (child.exitCode !== null) throw new Error("Login browser was closed before authentication completed");
      await delay(1000);
    }
    throw new Error("OA interactive login timed out");
  } finally {
    await closeLoginBrowser(child, webSocketUrl);
    cleanupBrowserProfile(profileDir);
  }
}

/** 环境变量账号密码是否足以让 Skill 自行登录。 */
function hasEnvironmentCredentials(config) {
  return Boolean(config.serviceUrl && process.env.OA_AUTH_USERNAME?.trim() && process.env.OA_AUTH_PASSWORD?.trim());
}

/** 执行授权命令。 */
async function runAuth() {
  const config = loadConfig();
  if (hasEnvironmentCredentials(config)) {
    process.stdout.write("OA environment credentials are configured.\n");
    return;
  }
  await interactiveAuth(config);
  process.stdout.write("OA browser login completed.\n");
}

/** 输出不含秘密的连接状态。 */
function runStatus() {
  const config = loadConfig();
  const authenticated = hasEnvironmentCredentials(config) || Boolean(loadSession());
  process.stdout.write(`${JSON.stringify({ authenticated })}\n`);
  if (!authenticated) process.exitCode = 1;
}

/** 删除持久化浏览器会话，不修改用户环境变量。 */
function runLogout() {
  if (fs.existsSync(SESSION_PATH)) fs.rmSync(SESSION_PATH, { force: true });
  process.stdout.write("Stored OA browser session removed.\n");
}

/** CLI 主入口。 */
async function main(argv = process.argv.slice(2)) {
  const command = argv[0] || "status";
  if (command === "auth") return runAuth();
  if (command === "status") return runStatus();
  if (command === "logout") return runLogout();
  throw new Error("Unknown connector command");
}

if (require.main === module) {
  main().catch((error) => {
    process.stderr.write(`Seeyon connector error: ${error.message}\n`);
    process.exitCode = 1;
  });
}

module.exports = {
  AUTH_TRACE_PATH,
  cleanupBrowserProfile,
  deriveCandidateServiceUrls,
  hasEnvironmentCredentials,
  loadConfig,
  loadSession,
  normalizeServiceUrl,
  readAuthCookies,
  saveSession,
};
