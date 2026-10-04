'use strict';

const gateway = require('../lib/gateway-client');
const store = require('../lib/credential-store');
const config = require('../config');
const { finalizeReady } = require('./auth-status');

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

/**
 * auth login：向网关发起授权会话并给出同程登录 URL。
 *
 * --no-wait：打印授权 URL 后立即退出（WorkBuddy 模式，由其打开浏览器并轮询 status）。
 * 非 --no-wait：打印 URL 后本地轮询直到完成（手工测试用）。
 *
 * @param {{noWait?:boolean, json?:boolean}} opts
 * @returns {Promise<number>}
 */
async function authLogin(opts) {
  const res = await gateway.start();
  store.saveSession({
    session_id: res.session_id,
    device_secret: res.device_secret,
    created_at: Date.now()
  });

  const authorizeUrl = res.authorize_url;

  if (opts.noWait) {
    if (opts.json) {
      process.stdout.write(
        JSON.stringify({
          authorize_url: authorizeUrl,
          verification_url: authorizeUrl,
          session_id: res.session_id
        }) + '\n'
      );
    } else {
      process.stdout.write('请在浏览器中打开以下地址完成同程登录授权：\n' + authorizeUrl + '\n');
    }
    return 0;
  }

  // 交互式：打印 URL 后本地轮询
  process.stdout.write(
    '请在浏览器中打开以下地址完成同程登录授权：\n' + authorizeUrl + '\n等待授权完成...\n'
  );
  const deadline = Date.now() + config.loginTimeoutMs;
  while (Date.now() < deadline) {
    await sleep(config.pollIntervalMs);
    let p;
    try {
      p = await gateway.poll(res.session_id, res.device_secret);
    } catch (e) {
      continue;
    }
    if (p.status === 'ready') {
      finalizeReady(p);
      store.clearSession();
      process.stdout.write('授权成功，已登录。\n');
      return 0;
    }
    if (p.status === 'expired' || p.status === 'error') {
      store.clearSession();
      process.stderr.write('授权失败或会话已失效，请重试。\n');
      return 1;
    }
  }
  store.clearSession();
  process.stderr.write('授权超时（5 分钟未完成）。\n');
  return 1;
}

module.exports = { authLogin };
