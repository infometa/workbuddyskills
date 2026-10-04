// =============================================================================
// hook_common.js — 共享工具函数
// =============================================================================
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

function stateKey(name, suffix) { return name.replace(/[/\\]/g, '_') + '_' + suffix; }
function sha256(str) { return crypto.createHash('sha256').update(str).digest('hex').substring(0, 16); }
function nowISO() { return new Date().toISOString(); }

// 稳定序列化：递归按 key 排序后序列化。
// 保证「语义相同、字段顺序不同」的对象得到同一字符串，用于状态 key 的哈希计算，
// 避免 Agent 客户端重试时改变参数顺序导致 key 漂移（同一调用被误判为全新调用）。
function stableStringify(v) {
  if (v === null || typeof v !== 'object') return JSON.stringify(v);
  if (Array.isArray(v)) return '[' + v.map(stableStringify).join(',') + ']';
  return '{' + Object.keys(v).sort().map(function (k) { return JSON.stringify(k) + ':' + stableStringify(v[k]); }).join(',') + '}';
}

function safeName(name) { return name.replace(/[/\\]/g, '_'); }

function readJSON(fp) {
  try { return fs.existsSync(fp) ? JSON.parse(fs.readFileSync(fp, 'utf8')) : {}; }
  catch (_) { return {}; }
}

function patchJSON(fp, updater) {
  const obj = readJSON(fp);
  updater(obj);
  try {
    const dir = path.dirname(fp);
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
    fs.writeFileSync(fp, JSON.stringify(obj, null, 2), 'utf8');
  } catch (err) { console.error('patchJSON 失败:', err && err.message); }
}

// 通用的 stdin 读取 + 解析
async function readStdin() {
  const chunks = [];
  for await (const chunk of process.stdin) chunks.push(chunk);
  const raw = Buffer.concat(chunks).toString('utf8');
  const cleaned = raw.replace(/^[\uFEFF\uFFFE\u200B\u200C\u200D\u2060]+/, '').trim();
  let inputData = {};
  try { inputData = JSON.parse(cleaned); } catch (_) { inputData = { raw }; }
  return inputData;
}

// 通用日志写入
function writeLog(logDir, sessionId, inputData, responseOutput, event) {
  const logFile = path.join(logDir, 'hook-' + sessionId + '.log');
  const entry = [
    '=== [' + nowISO() + '] event=' + (event || 'unknown') + ' ===',
    '>>> INPUT (stdin):', JSON.stringify(inputData, null, 2),
    '<<< OUTPUT (stdout):', JSON.stringify(responseOutput, null, 2),
    '==================================\n\n'
  ].join('\n');
  try { fs.appendFileSync(logFile, entry, 'utf8'); } catch (_) {}
}

// 异步上报拦截事件到 ai-data-platform
// - 使用原生 http/https 模块，零依赖
// - 3 秒超时后 destroy，不阻塞 hook 主流程
// - 所有 error/timeout 静默 catch，不影响安全拦截决策
// - 返回 Promise：resolve 在请求完成（sent/error/timeout/exception）时，供调用方等待上报结束再退出进程
// - logCtx（可选）: { logDir, sessionId } — 传入则将发送行为写入 logs/report-<sessionId>.log
function sendBlockReport(url, data, logCtx) {
  // 默认 logDir 基于 __dirname 推导：hooks/hr-ai-data/script/ -> ../../../logs/
  var logDir = (logCtx && logCtx.logDir) || path.resolve(__dirname, '..', '..', '..', 'logs');
  var sessionId = (logCtx && logCtx.sessionId) || 'no-session';

  function reportLog(status, detail) {
    var logFile = path.join(logDir, 'report-' + sessionId + '.log');
    var lines = [
      '=== [' + nowISO() + '] report=' + status + ' ===',
      '>>> URL: ' + url,
      '>>> DATA: ' + JSON.stringify(data, null, 2)
    ];
    if (detail) lines.push('>>> DETAIL: ' + detail);
    lines.push('==================================\n');
    try { fs.appendFileSync(logFile, lines.join('\n'), 'utf8'); } catch (_) {}
  }

  return new Promise(function (resolve) {
    try {
      reportLog('sending');
      var parsed = new URL(url);
      var lib = parsed.protocol === 'https:' ? require('https') : require('http');
      var body = JSON.stringify(data);
      var options = {
        method: 'POST',
        hostname: parsed.hostname,
        port: parsed.port || (parsed.protocol === 'https:' ? 443 : 80),
        path: parsed.pathname + (parsed.search || ''),
        headers: {
          'Content-Type': 'application/json',
          'Content-Length': Buffer.byteLength(body)
        },
        timeout: 3000
      };
      var req = lib.request(options, function (res) {
        // 收集响应体，便于审计日志记录服务器返回内容
        var respChunks = [];
        res.on('data', function (chunk) { respChunks.push(chunk); });
        res.on('end', function () {
          var bodyText = Buffer.concat(respChunks).toString('utf8');
          reportLog('sent', 'statusCode=' + res.statusCode + (bodyText ? '\n>>> BODY: ' + bodyText.substring(0, 500) : ''));
          resolve(true);
        });
      });
      req.on('error', function (err) {
        reportLog('error', (err && err.message) || String(err));
        resolve(false);
      });
      req.on('timeout', function () {
        reportLog('timeout', '3s exceeded, request destroyed');
        req.destroy();
        resolve(false);
      });
      req.write(body);
      req.end();
    } catch (err) {
      reportLog('exception', (err && err.message) || String(err));
      resolve(false);
    }
  });
}

module.exports = { stateKey, sha256, stableStringify, nowISO, safeName, readJSON, patchJSON, readStdin, writeLog, sendBlockReport };
