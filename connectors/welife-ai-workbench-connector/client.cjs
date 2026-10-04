#!/usr/bin/env node
'use strict';

// Cookie never appears on stdout/stderr or enters the model's MCP arguments.
const crypto = require('node:crypto');
const fs = require('node:fs/promises');
const fsConstants = require('node:fs').constants;
const https = require('node:https');
const os = require('node:os');
const path = require('node:path');
const { spawn } = require('node:child_process');
const { setTimeout: sleep } = require('node:timers/promises');
const { performance } = require('node:perf_hooks');

const VERSION = '2.1.3';
const ORIGIN = 'https://manage.acewill.net';
const PATHS = Object.freeze({
  start: '/newmanage/manageapi/ai/connect/start',
  poll: '/newmanage/manageapi/ai/connect/poll',
  mcp: '/newmanage/manageapi/ai/mcp',
  authorize: '/newmanage/ai/connect/authorize',
});
const MAX_REQUEST_BYTES = 262144;
const MAX_RESPONSE_BYTES = 2097152;
const MAX_CREDENTIAL_BYTES = 8192;
const MAX_STORED_BYTES = 32768;
const LOCAL_TTL_SECONDS = 86400;
const REQUEST_TIMEOUT_MS = 30000;
const STATUS_TIMEOUT_MS = 8000;
const COOKIE_NAMES = ['manager_bid', 'manager_mid', 'manager_sign'];

class ConnectorError extends Error {
  constructor(code, message) { super(message); this.name = 'ConnectorError'; this.code = code; }
}

function fail(code, message) { throw new ConnectorError(code, message); }
function isObject(value) { return value !== null && typeof value === 'object' && !Array.isArray(value); }
function hasExactKeys(value, keys) {
  return isObject(value) && Object.keys(value).length === keys.length && keys.every(key => Object.hasOwn(value, key));
}
function unixNow() { return Math.floor(Date.now() / 1000); }
function safeMessage(error) {
  return error instanceof ConnectorError ? error.message : '连接器操作失败，请稍后重试或联系管理员。';
}
function abortError(signal) {
  return signal && signal.reason instanceof ConnectorError ? signal.reason : new ConnectorError('cancelled', '操作已取消。');
}
function checkAborted(signal) { if (signal && signal.aborted) throw abortError(signal); }
function abortable(operation, signal) {
  return new Promise((resolve, reject) => {
    if (signal.aborted) { reject(abortError(signal)); return; }
    const abort = () => reject(abortError(signal));
    signal.addEventListener('abort', abort, { once: true });
    Promise.resolve().then(operation).then(resolve, reject).finally(() => signal.removeEventListener('abort', abort));
  });
}

// Windows stores only CurrentUser-DPAPI ciphertext. The fixed script receives
// sensitive bytes through stdin, never shell arguments, files, or log messages.
function windowsProtect(bytes, decrypt = false, { spawnProcess = spawn, windowsRoot = process.env.SystemRoot || 'C:\\Windows', signal } = {}) {
  const operation = decrypt ? 'Unprotect' : 'Protect';
  const script = "$ErrorActionPreference='Stop'; Add-Type -AssemblyName System.Security; "
    + '$text=[Console]::In.ReadToEnd(); if($text.Length -gt 65536){exit 10}; '
    + '$bytes=[Convert]::FromBase64String($text); '
    + "$entropy=[Text.Encoding]::UTF8.GetBytes('WeLife AI Connector v2 credentials'); "
    + 'try { $out=[Security.Cryptography.ProtectedData]::' + operation
    + '($bytes,$entropy,[Security.Cryptography.DataProtectionScope]::CurrentUser); '
    + '[Console]::Out.Write([Convert]::ToBase64String($out)); '
    + '} finally { [Array]::Clear($bytes,0,$bytes.Length) }';
  return new Promise((resolve, reject) => {
    let child;
    let timer;
    let settled = false;
    let output = Buffer.alloc(0);
    const finish = (error, value) => {
      if (settled) return;
      settled = true; clearTimeout(timer); output.fill(0);
      if (signal) signal.removeEventListener('abort', aborted);
      if (error) reject(error); else resolve(value);
    };
    const aborted = () => { finish(abortError(signal)); if (child) child.kill(); };
    const failure = () => new ConnectorError('secure_storage_failed', 'Windows 安全凭证存储失败，未降级为明文，请检查当前用户的 DPAPI 环境。');
    try {
      if (signal && signal.aborted) { aborted(); return; }
      if (signal) signal.addEventListener('abort', aborted, { once: true });
      child = spawnProcess(path.win32.join(windowsRoot, 'System32', 'WindowsPowerShell', 'v1.0', 'powershell.exe'),
        ['-NoLogo', '-NoProfile', '-NonInteractive', '-EncodedCommand', Buffer.from(script, 'utf16le').toString('base64')],
        { stdio: ['pipe', 'pipe', 'ignore'], shell: false, windowsHide: true });
      timer = setTimeout(() => { finish(failure()); child.kill(); }, 10000);
      child.on('error', () => finish(failure()));
      child.stdin.on('error', () => finish(failure()));
      child.stdout.on('data', chunk => {
        if (settled) return;
        if (output.length + chunk.length > 65536) { finish(failure()); child.kill(); return; }
        output = Buffer.concat([output, chunk]);
      });
      child.on('close', code => {
        if (settled) return;
        if (code !== 0) { finish(failure()); return; }
        try {
          const decoded = decodeBase64(output.toString('ascii').trim(), undefined, decrypt ? MAX_CREDENTIAL_BYTES : MAX_STORED_BYTES);
          finish(null, decoded);
        } catch (_) { finish(failure()); }
      });
      child.stdin.end(bytes.toString('base64'));
    } catch (_) { finish(failure()); if (child) child.kill(); }
  });
}
function validateId(id) {
  if (typeof id !== 'string' || !/^[a-f0-9]{64}$/.test(id)) fail('invalid_pairing', '授权配对信息不正确。');
}
function validateCookies(cookies) {
  if (!hasExactKeys(cookies, COOKIE_NAMES)) fail('invalid_credentials', '登录凭证格式不正确，请重新授权。');
  for (const name of ['manager_bid', 'manager_mid']) {
    if (typeof cookies[name] !== 'string' || !/^[1-9]\d{0,18}$/.test(cookies[name])
        || BigInt(cookies[name]) > 9223372036854775807n) {
      fail('invalid_credentials', '登录凭证中的账号信息不正确，请重新授权。');
    }
  }
  if (typeof cookies.manager_sign !== 'string' || !/^[a-f0-9]{32}$/.test(cookies.manager_sign)) {
    fail('invalid_credentials', '登录凭证格式不正确，请重新授权。');
  }
  return cookies;
}

function validateCredentials(value, { now = unixNow(), expectedId, allowExpired = false } = {}) {
  if (!hasExactKeys(value, ['version', 'id', 'cookies', 'saved_at', 'local_expires_at']) || value.version !== 1) {
    fail('invalid_credentials', '登录凭证格式不正确，请重新授权。');
  }
  validateId(value.id);
  if (expectedId !== undefined && value.id !== expectedId) fail('pairing_mismatch', '授权配对不匹配，请重新授权。');
  validateCookies(value.cookies);
  if (!Number.isSafeInteger(value.saved_at) || !Number.isSafeInteger(value.local_expires_at)
      || value.saved_at <= 0 || value.saved_at > now + 300
      || value.local_expires_at <= value.saved_at || value.local_expires_at > value.saved_at + LOCAL_TTL_SECONDS) {
    fail('invalid_credentials', '登录凭证有效期不正确，请重新授权。');
  }
  if (!allowExpired && value.local_expires_at <= now) fail('local_expired', '本机授权保存期已结束，请运行 auth login 重新登录。');
  return value;
}

function cookieHeader(cookies) {
  validateCookies(cookies);
  return COOKIE_NAMES.map(name => name + '=' + cookies[name]).join('; ');
}

// No custom server URL, redirects, browser database access, or cookie export API.
function requestJson(route, body, cookies, { timeoutMs = REQUEST_TIMEOUT_MS, signal } = {}) {
  if (![PATHS.start, PATHS.poll, PATHS.mcp].includes(route)) return Promise.reject(new ConnectorError('invalid_route', '请求地址不受支持。'));
  if (cookies !== undefined && route !== PATHS.mcp) return Promise.reject(new ConnectorError('invalid_route', '登录凭证不能发送到该地址。'));
  const rawBody = JSON.stringify(body);
  if (Buffer.byteLength(rawBody) > MAX_REQUEST_BYTES) return Promise.reject(new ConnectorError('request_too_large', '请求过大，请缩小查询范围。'));
  const headers = { 'Content-Type': 'application/json', Accept: 'application/json', 'Content-Length': Buffer.byteLength(rawBody) };
  if (cookies !== undefined) headers.Cookie = cookieHeader(cookies);
  return new Promise((resolve, reject) => {
    let settled = false;
    let timer;
    const finish = (error, value) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      if (error) reject(error); else resolve(value);
    };
    const request = https.request(ORIGIN + route, {
      method: 'POST', headers, signal, rejectUnauthorized: true,
    }, response => {
      const chunks = [];
      let bytes = 0;
      response.on('data', chunk => {
        bytes += chunk.length;
        if (bytes > MAX_RESPONSE_BYTES) {
          finish(new ConnectorError('response_too_large', '接口响应过大，请缩小查询范围。'));
          response.destroy(); request.destroy(); return;
        }
        chunks.push(chunk);
      });
      response.on('aborted', () => finish(new ConnectorError('network_error', '接口连接中断，请稍后重试。')));
      response.on('error', () => finish(new ConnectorError('network_error', '接口连接中断，请稍后重试。')));
      response.on('end', () => {
        const status = response.statusCode || 0;
        if (status >= 300 && status < 400) { finish(new ConnectorError('redirect_rejected', '接口返回了非预期跳转，已停止发送凭证，请联系管理员检查接口地址。')); return; }
        if (status < 200 || status >= 300) { finish(null, { status, body: null }); return; }
        let json = null;
        if (bytes) {
          const type = String(response.headers['content-type'] || '').toLowerCase();
          if (!type.includes('application/json')) { finish(new ConnectorError('invalid_response', '接口未返回有效数据，请稍后重试或联系管理员。')); return; }
          try { json = JSON.parse(Buffer.concat(chunks).toString('utf8')); }
          catch (_) { finish(new ConnectorError('invalid_response', '接口返回的数据格式不正确。')); return; }
        }
        finish(null, { status, body: json });
      });
    });
    timer = setTimeout(() => {
      finish(new ConnectorError('request_timeout', '接口请求超时，请稍后重试；本次请求不会自动重放。'));
      request.destroy();
    }, Math.max(1, Math.min(timeoutMs, REQUEST_TIMEOUT_MS)));
    request.on('error', () => finish(new ConnectorError(signal && signal.aborted ? 'cancelled' : 'network_error', signal && signal.aborted ? '操作已取消。' : '接口连接失败，请检查网络后重试。')));
    request.end(rawBody);
  });
}

// POSIX: private directory + atomic 0600 file. Windows: CurrentUser DPAPI only.
class CredentialStore {
  constructor(directory = path.join(os.homedir(), '.welife-ai-connector'), { platform = process.platform, now = unixNow, protect = windowsProtect } = {}) {
    this.directory = path.resolve(directory);
    this.filename = path.join(this.directory, 'credentials.json');
    this.platform = platform;
    this.now = now;
    this.protect = protect;
  }

  async ensureDirectory(create = false) {
    if (create) {
      try { await fs.mkdir(this.directory, { mode: 0o700 }); }
      catch (error) { if (error.code !== 'EEXIST') throw error; }
    }
    let stat;
    try { stat = await fs.lstat(this.directory); }
    catch (error) { if (error.code === 'ENOENT') fail('not_authorized', '尚未授权，请运行 auth login 登录微生活。'); throw error; }
    if (!stat.isDirectory() || stat.isSymbolicLink()
        || (this.platform !== 'win32' && (typeof process.getuid !== 'function'
          || stat.uid !== process.getuid() || (stat.mode & 0o777) !== 0o700))) {
      fail('unsafe_store', '凭证目录权限不安全，需要当前用户所有的 0700 私有目录。');
    }
  }

  validateFileStat(stat) {
    if (!stat.isFile() || stat.isSymbolicLink() || stat.nlink !== 1 || stat.size > MAX_STORED_BYTES
        || (this.platform !== 'win32' && (stat.uid !== process.getuid() || (stat.mode & 0o777) !== 0o600))) {
      fail('unsafe_store', '凭证文件权限或类型不安全，需要当前用户所有的 0600 普通文件。');
    }
  }

  async read({ signal } = {}) {
    checkAborted(signal);
    await this.ensureDirectory();
    checkAborted(signal);
    let handle;
    let stat;
    try {
      stat = await fs.lstat(this.filename);
      this.validateFileStat(stat);
      handle = await fs.open(this.filename, fsConstants.O_RDONLY | (fsConstants.O_NOFOLLOW || 0));
      const openedStat = await handle.stat();
      this.validateFileStat(openedStat);
      if (openedStat.dev !== stat.dev || openedStat.ino !== stat.ino) fail('unsafe_store', '凭证文件发生变化，请重试。');
      const buffer = Buffer.alloc(MAX_STORED_BYTES + 1);
      const { bytesRead } = await handle.read(buffer, 0, buffer.length, 0);
      if (bytesRead > MAX_STORED_BYTES) fail('invalid_credentials', '登录凭证文件过大，请重新授权。');
      let value;
      let plaintext;
      try {
        checkAborted(signal);
        const persisted = JSON.parse(buffer.subarray(0, bytesRead).toString('utf8'));
        if (this.platform === 'win32') {
          if (!hasExactKeys(persisted, ['version', 'protection', 'blob']) || persisted.version !== 1
              || persisted.protection !== 'windows-dpapi-current-user') fail('invalid_credentials', 'Windows 凭证必须使用当前用户 DPAPI 加密。');
          plaintext = await this.protect(decodeBase64(persisted.blob, undefined, MAX_STORED_BYTES), true, { signal });
          value = JSON.parse(plaintext.toString('utf8'));
        } else { value = persisted; }
      }
      catch (error) { if (error instanceof ConnectorError) throw error; fail('invalid_credentials', '登录凭证文件损坏，请重新授权。'); }
      finally { buffer.fill(0); if (plaintext) plaintext.fill(0); }
      checkAborted(signal);
      return validateCredentials(value, { now: this.now() });
    } catch (error) {
      if (error.code === 'ENOENT') fail('not_authorized', '尚未授权，请运行 auth login 登录微生活。');
      throw error;
    } finally { if (handle) await handle.close(); }
  }

  async removeIfUnchanged(expected) {
    if (!expected) return;
    try {
      const current = await fs.lstat(this.filename);
      if (current.dev === expected.dev && current.ino === expected.ino) await fs.unlink(this.filename);
    } catch (error) { if (error.code !== 'ENOENT') throw error; }
  }

  async write(value) {
    validateCredentials(value, { now: this.now() });
    await this.ensureDirectory(true);
    try { this.validateFileStat(await fs.lstat(this.filename)); }
    catch (error) { if (error.code !== 'ENOENT') throw error; }
    let persisted = value;
    if (this.platform === 'win32') {
      const plaintext = Buffer.from(JSON.stringify(value), 'utf8');
      try {
        const protectedBytes = await this.protect(plaintext, false);
        persisted = { version: 1, protection: 'windows-dpapi-current-user', blob: protectedBytes.toString('base64') };
        protectedBytes.fill(0);
      } finally { plaintext.fill(0); }
    }
    const temporary = path.join(this.directory, '.credentials-' + crypto.randomBytes(16).toString('hex'));
    let handle;
    try {
      handle = await fs.open(temporary, 'wx', 0o600);
      await handle.writeFile(JSON.stringify(persisted), 'utf8');
      await handle.sync();
      await handle.close(); handle = null;
      await fs.rename(temporary, this.filename);
    } finally {
      if (handle) await handle.close();
      try { await fs.unlink(temporary); } catch (error) { if (error.code !== 'ENOENT') throw error; }
    }
  }

  async clear() {
    try { await this.ensureDirectory(); }
    catch (error) { if (error.code === 'not_authorized') return; throw error; }
    try { const stat = await fs.lstat(this.filename); this.validateFileStat(stat); await this.removeIfUnchanged(stat); }
    catch (error) { if (error.code !== 'ENOENT') throw error; }
  }
}

function decodeBase64(value, exactBytes, maximumBytes) {
  if (typeof value !== 'string' || value.length === 0 || value.length > Math.ceil(maximumBytes / 3) * 4
      || !/^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/.test(value)) {
    fail('invalid_envelope', '授权数据加密格式不正确。');
  }
  const buffer = Buffer.from(value, 'base64');
  if (buffer.length > maximumBytes || (exactBytes && buffer.length !== exactBytes) || buffer.toString('base64') !== value) {
    fail('invalid_envelope', '授权数据加密格式不正确。');
  }
  return buffer;
}

function decryptEnvelope(envelope, privateKey, id, now = unixNow()) {
  validateId(id);
  if (!hasExactKeys(envelope, ['algorithm', 'key', 'iv', 'tag', 'ciphertext']) || envelope.algorithm !== 'RSA-OAEP-SHA1+A256GCM') {
    fail('invalid_envelope', '授权数据加密格式不正确。');
  }
  const wrappedKey = decodeBase64(envelope.key, 256, 256);
  const iv = decodeBase64(envelope.iv, 12, 12);
  const tag = decodeBase64(envelope.tag, 16, 16);
  const ciphertext = decodeBase64(envelope.ciphertext, undefined, MAX_CREDENTIAL_BYTES);
  let key;
  let plaintext;
  try {
    key = crypto.privateDecrypt({ key: privateKey, padding: crypto.constants.RSA_PKCS1_OAEP_PADDING, oaepHash: 'sha1' }, wrappedKey);
    if (key.length !== 32) fail('invalid_envelope', '授权数据解密失败。');
    const decipher = crypto.createDecipheriv('aes-256-gcm', key, iv);
    decipher.setAAD(Buffer.from(id, 'utf8'));
    decipher.setAuthTag(tag);
    plaintext = Buffer.concat([decipher.update(ciphertext), decipher.final()]);
    return validateCredentials(JSON.parse(plaintext.toString('utf8')), { expectedId: id, now });
  } catch (error) {
    if (error instanceof ConnectorError) throw error;
    fail('invalid_envelope', '授权数据解密失败，请重新授权。');
  } finally { if (key) key.fill(0); if (plaintext) plaintext.fill(0); }
}

function validateStartResponse(value) {
  if (!isObject(value) || value.status !== 'pending') fail('invalid_pairing', '无法创建授权请求，请稍后重试。');
  validateId(value.id);
  const expectedUrl = ORIGIN + PATHS.authorize + '?id=' + value.id;
  if (value.authorize_url !== expectedUrl || value.verification_code !== value.id.slice(0, 6).toUpperCase()
      || !Number.isInteger(value.expires_in) || value.expires_in < 1 || value.expires_in > 300
      || !Number.isInteger(value.interval) || value.interval < 1 || value.interval > 10) {
    fail('invalid_pairing', '授权地址或配对信息不正确，已停止操作。');
  }
  return value;
}

function assertHttpSuccess(response) {
  if (!response || !Number.isInteger(response.status) || response.status < 100 || response.status > 599) fail('invalid_response', '接口响应格式不正确。');
  if (response.status === 401) fail('session_invalid', '微生活登录已失效，请通过 WorkBuddy 原生连接卡重新连接。');
  if (response.status === 403) fail('access_denied', '当前账号没有访问权限，请联系商户管理员核查权限；无需重新登录。');
  if (response.status < 200 || response.status >= 300) fail('http_error', '微生活接口暂不可用（HTTP ' + response.status + '），请稍后重试。');
}

function validateRpcResponse(body, id) {
  if (!isObject(body) || body.jsonrpc !== '2.0' || body.id !== id
      || Object.hasOwn(body, 'result') === Object.hasOwn(body, 'error')
      || (Object.hasOwn(body, 'error') && (!isObject(body.error)
        || !Number.isSafeInteger(body.error.code) || typeof body.error.message !== 'string'))) {
    fail('invalid_response', '接口返回的数据格式不正确。');
  }
}

async function checkSession(cookies, transport = requestJson, options = {}) {
  const id = 'welife-auth-check';
  const response = await transport(PATHS.mcp, { jsonrpc: '2.0', id, method: 'ping', params: {} }, cookies, options);
  assertHttpSuccess(response);
  validateRpcResponse(response.body, id);
  // Status checks only classify explicit, well-formed authentication/permission failures.
  if (response.body.error && response.body.error.code === -32001) fail('session_invalid', '微生活登录已失效，请通过 WorkBuddy 原生连接卡重新连接。');
  if (response.body.error && response.body.error.code === -32003) fail('access_denied', '当前账号没有访问权限，请联系商户管理员核查权限；无需重新登录。');
  if (response.body.error) fail('session_check_failed', '登录状态检查服务暂不可用，请稍后重试。');
  if (!isObject(response.body.result)) fail('invalid_response', '登录状态检查返回的数据格式不正确。');
}

async function authLogin({ store = new CredentialStore(), transport = requestJson, now = unixNow,
  wait = sleep, output = value => {
    if (value.status === 'pending') process.stdout.write(value.authorize_url + '\n校验码：' + value.verification_code + '\n请在微生活授权页面核对校验码并确认授权。\n');
    else process.stdout.write('授权成功，登录 Cookie 已在本机安全保存。\n');
  }, openBrowser,
  signal, generateKeyPair = () => crypto.generateKeyPairSync('rsa', { modulusLength: 2048 }) } = {}) {
  await store.ensureDirectory(true);
  const { publicKey, privateKey } = generateKeyPair();
  const proof = crypto.randomBytes(32).toString('hex');
  const started = now();
  const startedResponse = await transport(PATHS.start, {
    public_key: publicKey.export({ type: 'spki', format: 'pem' }),
    poll_hash: crypto.createHash('sha256').update(proof, 'utf8').digest('hex'),
  }, undefined, { signal });
  assertHttpSuccess(startedResponse);
  const pairing = validateStartResponse(startedResponse.body);
  const deadline = started + pairing.expires_in;
  output({ status: 'pending', authorize_url: pairing.authorize_url, verification_code: pairing.verification_code, expires_in: pairing.expires_in });
  if (openBrowser) await openBrowser(pairing.authorize_url);
  while (now() < deadline) {
    if (signal && signal.aborted) fail('cancelled', '授权已取消。');
    try { await wait(pairing.interval * 1000, undefined, { signal }); }
    catch (error) { if (signal && signal.aborted) fail('cancelled', '授权已取消。'); throw error; }
    if (now() >= deadline) break;
    const response = await transport(PATHS.poll, { id: pairing.id, poll_proof: proof }, undefined,
      { signal, timeoutMs: Math.min(REQUEST_TIMEOUT_MS, (deadline - now()) * 1000) });
    assertHttpSuccess(response);
    if (!isObject(response.body)) fail('invalid_pairing', '授权状态格式不正确。');
    if (response.body.status === 'pending') continue;
    if (response.body.status === 'denied') fail('denied', '商户已拒绝本次授权。');
    if (response.body.status === 'expired' || response.body.status === 'consumed') fail('pairing_expired', '授权请求已过期或已被领取，请重新授权。');
    if (response.body.status !== 'approved' || now() >= deadline) fail('invalid_pairing', '授权状态不正确，请重新授权。');
    const credentials = decryptEnvelope(response.body.envelope, privateKey, pairing.id, now());
    await checkSession(credentials.cookies, transport, { signal, timeoutMs: Math.min(REQUEST_TIMEOUT_MS, (deadline - now()) * 1000) });
    if (now() >= deadline) fail('pairing_expired', '授权请求已过期，请重新授权。');
    await store.write(credentials);
    // A failed acknowledgment does not undo a verified local login; server envelope expires at 5 minutes.
    let acknowledged = false;
    try {
      const ack = await transport(PATHS.poll, { id: pairing.id, poll_proof: proof, ack: true }, undefined, { signal });
      acknowledged = ack.status === 200 && isObject(ack.body) && ack.body.status === 'consumed';
    } catch (_) { /* Never log network data or credential-bearing errors. */ }
    output({ status: 'authorized', local_expires_at: credentials.local_expires_at, acknowledged });
    return { status: 'authorized', acknowledged };
  }
  fail('pairing_expired', '授权请求已过期，请运行 auth login 重新授权。');
}

async function authStatus({ store = new CredentialStore(), transport = requestJson, timeoutMs = STATUS_TIMEOUT_MS } = {}) {
  // WorkBuddy status probes must finish before its 10-second command deadline.
  // One budget includes filesystem reads, Windows DPAPI, and the HTTP ping.
  const budget = Number.isFinite(timeoutMs) ? Math.max(1, Math.min(timeoutMs, STATUS_TIMEOUT_MS)) : STATUS_TIMEOUT_MS;
  const deadline = performance.now() + budget;
  const controller = new AbortController();
  const timeout = new ConnectorError('status_timeout', '登录状态检查超时，请稍后重试。');
  const timer = setTimeout(() => controller.abort(timeout), budget);
  const signal = controller.signal;
  try {
    const credentials = await abortable(() => store.read({ signal }), signal);
    const remaining = Math.floor(deadline - performance.now());
    if (remaining <= 0) { controller.abort(timeout); throw timeout; }
    await abortable(() => checkSession(credentials.cookies, transport, { signal, timeoutMs: remaining }), signal);
    return { status: 'authorized', local_expires_at: credentials.local_expires_at };
  } finally { clearTimeout(timer); }
}

function rpcError(id, code, message, data) {
  return { jsonrpc: '2.0', id, error: { code, message, ...(data ? { data } : {}) } };
}

function connectorRpcError(id, error) {
  // Recovery metadata is local and allowlisted; never copy upstream errors or credentials.
  if (error instanceof ConnectorError
      && ['not_authorized', 'local_expired', 'session_invalid', 'invalid_credentials'].includes(error.code)) {
    return rpcError(id, -32001, '微生活尚未连接或授权已失效，请通过 WorkBuddy 原生连接卡重新连接；连接完成后继续原任务。',
      { category: 'authentication', recovery: 'native_connection_card' });
  }
  if (error instanceof ConnectorError && error.code === 'access_denied') {
    return rpcError(id, -32003, '当前账号没有访问权限，请联系商户管理员核查权限；无需重新登录。',
      { category: 'permission', recovery: 'request_access' });
  }
  if (error instanceof ConnectorError && ['cancelled', 'denied'].includes(error.code)) {
    return rpcError(id, -32002, '操作已取消，未自动重新发起连接或请求。',
      { category: 'cancelled', recovery: 'none' });
  }
  return rpcError(id, -32002, safeMessage(error), { category: 'service', recovery: 'retry_later' });
}
function validRequest(request) {
  return isObject(request) && request.jsonrpc === '2.0' && typeof request.method === 'string'
    && request.method.length > 0 && request.method.length <= 128
    && (!Object.hasOwn(request, 'id') || request.id === null || typeof request.id === 'string' || Number.isSafeInteger(request.id))
    && (!Object.hasOwn(request, 'params') || isObject(request.params));
}

async function forwardMcp(raw, { store = new CredentialStore(), transport = requestJson } = {}) {
  if (Buffer.byteLength(raw) > MAX_REQUEST_BYTES) return rpcError(null, -32600, '请求过大，请缩小查询范围。');
  let request;
  try { request = JSON.parse(raw); }
  catch (_) { return rpcError(null, -32700, 'JSON 格式不正确。'); }
  if (!validRequest(request)) return rpcError(null, -32600, '请求格式不正确。');
  const hasId = Object.hasOwn(request, 'id');
  try {
    const credentials = await store.read();
    const response = await transport(PATHS.mcp, request, credentials.cookies);
    assertHttpSuccess(response);
    if (!hasId) return null;
    validateRpcResponse(response.body, request.id);
    return response.body;
  } catch (error) {
    if (!hasId) return null;
    return connectorRpcError(request.id, error);
  }
}

// Bounded line framing and sequential forwarding apply backpressure; no unbounded request queue.
async function runMcp({ input = process.stdin, output = process.stdout, ...options } = {}) {
  let partial = Buffer.alloc(0);
  let dropping = false;
  const write = async value => {
    if (value === null) return;
    if (!output.write(JSON.stringify(value) + '\n')) await new Promise((resolve, reject) => {
      const drained = () => { output.off('error', failed); resolve(); };
      const failed = error => { output.off('drain', drained); reject(error); };
      output.once('drain', drained); output.once('error', failed);
    });
  };
  for await (const chunk of input) {
    const buffer = Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk);
    let offset = 0;
    while (offset < buffer.length) {
      const newline = buffer.indexOf(10, offset);
      const end = newline < 0 ? buffer.length : newline;
      const segment = buffer.subarray(offset, end);
      if (!dropping) {
        if (partial.length + segment.length > MAX_REQUEST_BYTES) {
          partial = Buffer.alloc(0); dropping = true;
          await write(rpcError(null, -32600, '请求过大，请缩小查询范围。'));
        } else { partial = Buffer.concat([partial, segment]); }
      }
      if (newline >= 0) {
        if (!dropping && partial.length) await write(await forwardMcp(partial.toString('utf8'), options));
        partial = Buffer.alloc(0); dropping = false;
      }
      offset = newline < 0 ? buffer.length : newline + 1;
    }
  }
  if (!dropping && partial.length) await write(await forwardMcp(partial.toString('utf8'), options));
}

async function openBrowser(url) {
  const parsed = new URL(url);
  if (parsed.origin !== ORIGIN || parsed.pathname !== PATHS.authorize || !/^\?id=[a-f0-9]{64}$/.test(parsed.search) || parsed.hash) {
    fail('invalid_pairing', '授权地址不正确，已停止操作。');
  }
  const command = process.platform === 'darwin' ? 'open' : process.platform === 'linux' ? 'xdg-open'
    : process.platform === 'win32' ? path.win32.join(process.env.SystemRoot || 'C:\\Windows', 'System32', 'rundll32.exe') : null;
  if (!command) fail('unsupported_platform', '当前平台不支持自动打开登录页面，请手动打开授权地址。');
  await new Promise((resolve, reject) => {
    const child = spawn(command, process.platform === 'win32' ? ['url.dll,FileProtocolHandler', url] : [url], { stdio: 'ignore', shell: false, windowsHide: true });
    child.once('error', () => reject(new ConnectorError('browser_open_failed', '无法打开浏览器，请手动打开授权地址后重新登录。')));
    child.once('exit', code => code === 0 ? resolve() : reject(new ConnectorError('browser_open_failed', '无法打开浏览器，请手动打开授权地址后重新登录。')));
  });
}

async function main(args = process.argv.slice(2)) {
  if (args.length === 1 && args[0] === '--version') { process.stdout.write(VERSION + '\n'); return; }
  if (args.length === 1 && args[0] === 'mcp') { await runMcp(); return; }
  if (args[0] !== 'auth' || !['login', 'status', 'logout'].includes(args[1])
      || (args[1] === 'login' ? args.length > 3 || (args[2] && args[2] !== '--open') : args.length !== 2)) {
    fail('usage', '用法：welife-ai-connector --version | auth login [--open] | auth status | auth logout | mcp');
  }
  if (args[1] === 'login') {
    const controller = new AbortController();
    const cancel = () => controller.abort();
    process.once('SIGINT', cancel); process.once('SIGTERM', cancel);
    try { await authLogin({ openBrowser: args[2] === '--open' ? openBrowser : undefined, signal: controller.signal }); }
    finally { process.off('SIGINT', cancel); process.off('SIGTERM', cancel); }
  } else if (args[1] === 'status') {
    process.stdout.write(JSON.stringify(await authStatus()) + '\n');
  } else {
    await new CredentialStore().clear();
    process.stdout.write(JSON.stringify({ status: 'disconnected', message: '已删除本机 Cookie，不会退出浏览器或使其他副本失效。' }) + '\n');
  }
}

// CLI entry shared by direct execution and integrations that import the client.
// Keep errors off stdout (MCP protocol) and never print raw credential/path data.
function runCli(args = process.argv.slice(2)) {
  return main(args).catch(error => {
    process.stderr.write(safeMessage(error) + '\n');
    process.exitCode = 1;
  });
}

module.exports = {
  VERSION, ORIGIN, PATHS, MAX_REQUEST_BYTES, MAX_RESPONSE_BYTES, LOCAL_TTL_SECONDS, STATUS_TIMEOUT_MS,
  ConnectorError, CredentialStore, validateCookies, validateCredentials, cookieHeader,
  windowsProtect,
  requestJson, decodeBase64, decryptEnvelope, validateStartResponse, checkSession,
  authLogin, authStatus, forwardMcp, runMcp, openBrowser, safeMessage, main, runCli,
};

if (require.main === module) {
  runCli();
}
