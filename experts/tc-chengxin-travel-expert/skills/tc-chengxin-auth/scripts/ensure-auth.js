#!/usr/bin/env node
'use strict';

const { spawnSync } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { resolveClientContext } = require('../../../scripts/client-context');

const DEFAULT_TIMEOUT_MS = 90 * 1000;
const DEFAULT_POLL_INTERVAL_MS = 2000;

function parseLastJson(text) {
  const lines = String(text || '').split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
  for (let index = lines.length - 1; index >= 0; index -= 1) {
    try { return JSON.parse(lines[index]); } catch (_) { /* ignore CLI notices */ }
  }
  return null;
}

function asInvocation(candidate, env = process.env) {
  if (!candidate) return null;
  if (/\.js$/i.test(candidate)) return { command: process.execPath, prefixArgs: [candidate] };
  return { command: candidate, prefixArgs: [] };
}

function cliInvocation(platform = process.platform, env = process.env) {
  const pluginRoot = path.resolve(__dirname, '..', '..', '..');
  const bundled = path.join(pluginRoot, 'runtime', 'tc-chengxin-cli', 'bin', 'cli.js');
  if (fs.existsSync(bundled)) return asInvocation(bundled, env);
  if (env.TC_CHENGXIN_CLI_PATH) return asInvocation(env.TC_CHENGXIN_CLI_PATH, env);
  const executable = platform === 'win32' ? 'tc-chengxin.cmd' : 'tc-chengxin';
  const workbuddyDir = String(env.WORKBUDDY_CONFIG_DIR || '').trim() || path.join(os.homedir(), '.workbuddy');
  const managed = path.join(workbuddyDir, 'binaries', 'node', 'cli-connector-packages', 'bin', executable);
  return asInvocation(fs.existsSync(managed) ? managed : executable, env);
}

function cliCommand(platform = process.platform, env = process.env) {
  return cliInvocation(platform, env).command;
}

function runCli(args, options = {}) {
  const env = options.env || process.env;
  const invocation = cliInvocation(options.platform, env);
  return spawnSync(invocation.command, [...invocation.prefixArgs, ...args], {
    encoding: 'utf8', env, windowsHide: true
  });
}

function isAuthenticated(result) {
  const data = parseLastJson(result && result.stdout);
  return Boolean(data && data.authenticated === true);
}

function invalidateAuth(executeCli) {
  const result = executeCli(['auth', 'invalidate', '--json']);
  if (result && result.error && result.error.code === 'ENOENT') {
    return { invalidated: false, reason: 'cli-not-found' };
  }
  const data = parseLastJson(result && result.stdout);
  if (result && result.status === 0 && data && data.invalidated === true) {
    return { invalidated: true };
  }
  return { invalidated: false, reason: 'invalidate-failed' };
}

function authFailure(result) {
  const data = parseLastJson(result && result.stdout);
  if (!data || data.authenticated === true) return null;
  if (data.status === 'error') {
    return {
      reason: data.reason === 'oauth_exchange_failed' ? 'oauth-exchange-failed' : 'authorization-failed'
    };
  }
  if (data.status === 'expired') return { reason: 'session-expired' };
  return null;
}

function parseAuthorizeUrl(result) {
  const data = parseLastJson(result && result.stdout);
  const candidate = data && (data.authorize_url || data.verification_url);
  if (!candidate) return null;
  try {
    const parsed = new URL(candidate);
    return parsed.protocol === 'https:' || parsed.protocol === 'http:' ? parsed.toString() : null;
  } catch (_) { return null; }
}

function detectClientType(env = process.env, platform = process.platform) {
  return resolveClientContext(env, platform).clientType;
}

function shouldOpenBrowser(clientType, env = process.env, platform = process.platform) {
  if (!['mac', 'windows', 'linux'].includes(clientType)) return false;
  return resolveClientContext({ ...env, WORKBUDDY_CLIENT_TYPE: clientType }, platform).openBrowser;
}

function openExternal(url, options = {}) {
  const platform = options.platform || process.platform;
  const spawn = options.spawn || spawnSync;
  let command;
  let args;
  if (platform === 'darwin') {
    command = 'open'; args = [url];
  } else if (platform === 'win32') {
    command = 'rundll32.exe'; args = ['url.dll,FileProtocolHandler', url];
  } else {
    command = 'xdg-open'; args = [url];
  }
  const result = spawn(command, args, { stdio: 'ignore', windowsHide: true });
  return Boolean(result && !result.error && result.status === 0);
}

function positiveInteger(value, fallback) {
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed > 0 ? Math.floor(parsed) : fallback;
}

function sleep(ms) { return new Promise((resolve) => setTimeout(resolve, ms)); }

function startAuth(options = {}) {
  const executeCli = options.runCli || ((args) => runCli(args, options));
  const launchBrowser = options.openExternal || ((url) => openExternal(url, options));
  const env = options.env || process.env;
  const clientType = options.clientType || detectClientType(env, options.platform);
  if (options.forceReauth) {
    const invalidation = invalidateAuth(executeCli);
    if (!invalidation.invalidated) return { authenticated: false, reason: invalidation.reason, clientType };
  } else {
    const initial = executeCli(['auth', 'status', '--json']);
    if (isAuthenticated(initial)) return { authenticated: true, alreadyAuthenticated: true, clientType };
    if (initial && initial.error && initial.error.code === 'ENOENT') return { authenticated: false, reason: 'cli-not-found', clientType };
  }

  const login = executeCli(['auth', 'login', '--no-wait', '--json']);
  if (login && login.error && login.error.code === 'ENOENT') return { authenticated: false, reason: 'cli-not-found', clientType };
  const authorizeUrl = parseAuthorizeUrl(login);
  if (!authorizeUrl) return { authenticated: false, reason: 'login-start-failed', clientType };
  const browserOpened = shouldOpenBrowser(clientType, env, options.platform) ? launchBrowser(authorizeUrl) : false;
  const authorizationMode = browserOpened ? 'desktop-browser-poll' : 'login-link';
  return { authenticated: false, authorizationRequired: true, authorizationMode, authorizeUrl, browserOpened, clientType };
}

function checkAuth(options = {}) {
  const executeCli = options.runCli || ((args) => runCli(args, options));
  const status = executeCli(['auth', 'status', '--json']);
  if (isAuthenticated(status)) return { authenticated: true, alreadyAuthenticated: true };
  if (status && status.error && status.error.code === 'ENOENT') return { authenticated: false, reason: 'cli-not-found' };
  const failure = authFailure(status);
  if (failure) return { authenticated: false, ...failure };
  return { authenticated: false, reason: 'pending' };
}

async function pollAuth(options = {}) {
  const executeCli = options.runCli || ((args) => runCli(args, options));
  const wait = options.sleep || sleep;
  const now = options.now || Date.now;
  const timeoutMs = positiveInteger(options.timeoutMs, DEFAULT_TIMEOUT_MS);
  const pollIntervalMs = positiveInteger(options.pollIntervalMs, DEFAULT_POLL_INTERVAL_MS);
  const deadline = now() + timeoutMs;
  while (now() < deadline) {
    const status = executeCli(['auth', 'status', '--json']);
    if (isAuthenticated(status)) return { authenticated: true, alreadyAuthenticated: false };
    if (status && status.error && status.error.code === 'ENOENT') return { authenticated: false, reason: 'cli-not-found' };
    const failure = authFailure(status);
    if (failure) return { authenticated: false, ...failure };
    await wait(pollIntervalMs);
  }
  return { authenticated: false, reason: 'timeout' };
}

async function runAuthFlow(options = {}) {
  const started = startAuth(options);
  if (started.authenticated || !started.authorizationRequired) return started;
  if (options.onEvent) options.onEvent({ type: 'authorization-required', ...started });
  const polled = await pollAuth(options);
  return { ...polled, browserOpened: started.browserOpened, clientType: started.clientType };
}

async function startAuthForClient(options = {}) {
  const started = startAuth(options);
  if (started.authenticated || !started.authorizationRequired || !started.browserOpened) return started;
  if (options.onEvent) options.onEvent({ type: 'desktop-auth-waiting', ...started });
  const polled = await pollAuth(options);
  return {
    ...started,
    ...polled,
    authorizationRequired: !polled.authenticated
  };
}

function printFailure(result) {
  if (result.reason === 'cli-not-found') throw new Error('未找到同程授权组件，请重新安装本专家。');
  if (result.reason === 'invalidate-failed') {
    throw new Error('业务请求判定需要重新授权，但未能清除本地失效授权，请更新完整专家包后重试。');
  }
  if (result.reason === 'timeout') throw new Error('同程登录授权超时，请重新运行授权流程。');
  if (result.reason === 'oauth-exchange-failed') {
    throw new Error('同程登录授权失败：网关换取登录凭证失败，请检查正式 OAuth 客户端配置后重新授权。');
  }
  if (result.reason === 'session-expired') throw new Error('同程登录授权会话已过期，请重新运行授权流程。');
  if (result.reason === 'authorization-failed') throw new Error('同程登录授权失败，请重新运行授权流程。');
  throw new Error('未能创建同程登录授权会话，请稍后重试。');
}

async function main(argv = process.argv.slice(2)) {
  const mode = argv.includes('--start') ? 'start'
    : argv.includes('--check') ? 'check'
      : argv.includes('--poll') ? 'poll' : 'full';
  const common = {
    timeoutMs: positiveInteger(process.env.TC_CHENGXIN_AUTH_TIMEOUT_MS, DEFAULT_TIMEOUT_MS),
    pollIntervalMs: positiveInteger(process.env.TC_CHENGXIN_AUTH_POLL_INTERVAL_MS, DEFAULT_POLL_INTERVAL_MS)
  };
  if (mode === 'start') {
    const result = await startAuthForClient({
      ...common,
      // 本 Skill 只在业务请求返回未登录或 401 后进入。业务结果优先于
      // 本地 status，先清除旧凭证并发起一次全新授权。
      forceReauth: true,
      onEvent(event) {
        if (event.type === 'desktop-auth-waiting') {
          console.log('TC_CHENGXIN_AUTH_BROWSER_OPENED');
          console.log('TC_CHENGXIN_AUTH_MODE=DESKTOP_BROWSER_POLL');
          console.log(`TC_CHENGXIN_CLIENT_TYPE=${event.clientType}`);
          console.log('TC_CHENGXIN_AUTH_WAITING');
        }
      }
    });
    if (result.authenticated) { console.log('TC_CHENGXIN_AUTH_READY'); return; }
    if (!result.authorizationRequired) return printFailure(result);
    console.log('TC_CHENGXIN_AUTH_REQUIRED');
    console.log('TC_CHENGXIN_AUTH_MODE=LOGIN_LINK');
    console.log(`TC_CHENGXIN_CLIENT_TYPE=${result.clientType}`);
    console.log(`TC_CHENGXIN_AUTH_URL=${result.authorizeUrl}`);
    return;
  }
  if (mode === 'check') {
    const result = checkAuth(common);
    if (result.authenticated) { console.log('TC_CHENGXIN_AUTH_READY'); return; }
    if (result.reason === 'pending') { console.log('TC_CHENGXIN_AUTH_PENDING'); return; }
    return printFailure(result);
  }
  if (mode === 'poll') {
    const result = await pollAuth(common);
    if (result.authenticated) { console.log('TC_CHENGXIN_AUTH_READY'); return; }
    return printFailure(result);
  }
  const result = await runAuthFlow({
    ...common,
    onEvent(event) {
      if (event.type === 'authorization-required') {
        console.log('TC_CHENGXIN_AUTH_REQUIRED');
        console.log(`TC_CHENGXIN_CLIENT_TYPE=${event.clientType}`);
        console.log(`TC_CHENGXIN_AUTH_URL=${event.authorizeUrl}`);
      }
    }
  });
  if (result.authenticated) { console.log('TC_CHENGXIN_AUTH_READY'); return; }
  return printFailure(result);
}

if (require.main === module) {
  main().catch((error) => {
    console.error(`TC_CHENGXIN_AUTH_ERROR=${error.message}`);
    process.exitCode = 1;
  });
}

module.exports = {
  checkAuth,
  authFailure,
  cliCommand,
  cliInvocation,
  detectClientType,
  invalidateAuth,
  isAuthenticated,
  openExternal,
  parseAuthorizeUrl,
  parseLastJson,
  pollAuth,
  runAuthFlow,
  shouldOpenBrowser,
  startAuth,
  startAuthForClient
};
