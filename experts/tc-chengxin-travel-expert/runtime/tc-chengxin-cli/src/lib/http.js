'use strict';

const https = require('https');
const http = require('http');
const { URL } = require('url');
const config = require('../config');

const LOOPBACK_HOSTS = new Set(['127.0.0.1', 'localhost', '::1', '[::1]']);

function isLoopbackHost(hostname) {
  return LOOPBACK_HOSTS.has(String(hostname || '').toLowerCase());
}

function assertSupportedUrl(u) {
  if (u.protocol !== 'https:' && u.protocol !== 'http:') {
    throw new Error(`不支持的请求协议: ${u.protocol}`);
  }
  if (u.protocol === 'http:' && !isLoopbackHost(u.hostname)) {
    throw new Error(`非本地请求必须使用 HTTPS: ${u.hostname}`);
  }
}

/**
 * 发起 HTTP(S) 请求并按 JSON 解析响应
 * @param {string} method - GET/POST
 * @param {string} urlStr - 完整 URL
 * @param {object|null} body - 请求体（JSON），GET 传 null
 * @returns {Promise<{status:number, body:object}>}
 */
function request(method, urlStr, body) {
  return new Promise((resolve, reject) => {
    const u = new URL(urlStr);
    assertSupportedUrl(u);

    const useHttp = u.protocol === 'http:';
    const mod = useHttp ? http : https;
    const data = body ? JSON.stringify(body) : null;

    const options = {
      method,
      hostname: u.hostname,
      port: u.port || (useHttp ? 80 : 443),
      path: u.pathname + u.search,
      timeout: config.httpTimeoutMs,
      headers: {
        Accept: 'application/json',
        'User-Agent': 'tc-chengxin-cli'
      }
    };
    if (data) {
      options.headers['Content-Type'] = 'application/json';
      options.headers['Content-Length'] = Buffer.byteLength(data);
    }

    const req = mod.request(options, (res) => {
      let chunks = '';
      res.on('data', (c) => (chunks += c));
      res.on('end', () => {
        let parsed;
        try {
          parsed = chunks ? JSON.parse(chunks) : {};
        } catch (e) {
          parsed = { _raw: chunks };
        }
        resolve({ status: res.statusCode, body: parsed });
      });
    });

    req.on('timeout', () => {
      req.destroy();
      reject(new Error('请求超时'));
    });
    req.on('error', reject);
    if (data) req.write(data);
    req.end();
  });
}

module.exports = {
  postJson: (url, body) => request('POST', url, body || {}),
  getJson: (url) => request('GET', url, null)
};
