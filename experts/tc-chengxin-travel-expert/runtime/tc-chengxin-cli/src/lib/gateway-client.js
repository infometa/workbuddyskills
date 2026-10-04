'use strict';

const { postJson, getJson } = require('./http');
const config = require('../config');

function base() {
  return config.gatewayBase.replace(/\/+$/, '');
}

/**
 * 发起授权：网关创建一次性会话并返回同程授权 URL
 * @returns {Promise<{session_id:string, device_secret:string, authorize_url:string}>}
 */
async function start() {
  const { status, body } = await postJson(base() + '/api/v1/oauth/cli/start', {});
  if (status !== 200 || !body || !body.authorize_url || !body.session_id) {
    throw new Error('发起授权失败: ' + JSON.stringify(body));
  }
  return body;
}

/**
 * 轮询授权结果
 * @returns {Promise<{status:'pending'|'ready'|'expired'|'error', access_token?:string, refresh_token?:string, expires_in?:number, refresh_expires_in?:number, user?:string}>}
 */
async function poll(sessionId, deviceSecret) {
  const url =
    base() +
    '/api/v1/oauth/cli/poll?session_id=' +
    encodeURIComponent(sessionId) +
    '&device_secret=' +
    encodeURIComponent(deviceSecret || '');
  const { status, body } = await getJson(url);
  if (status !== 200 || !body || !body.status) {
    throw new Error('轮询失败: ' + JSON.stringify(body));
  }
  return body;
}

/**
 * 用 refresh_token 续期
 * @returns {Promise<{access_token:string, expires_in?:number, refresh_token?:string, refresh_expires_in?:number}>}
 */
async function refresh(refreshToken) {
  const { status, body } = await postJson(base() + '/api/v1/oauth/cli/refresh', {
    refresh_token: refreshToken
  });
  if (status !== 200 || !body || !body.access_token) {
    throw new Error('续期失败: ' + JSON.stringify(body));
  }
  return body;
}

/**
 * 撤销/解绑（尽力而为，失败忽略）
 */
async function revoke(creds) {
  try {
    await postJson(base() + '/api/v1/oauth/cli/revoke', {
      refresh_token: creds && creds.refresh_token,
      access_token: creds && creds.access_token
    });
  } catch (e) {
    /* ignore */
  }
}

module.exports = { start, poll, refresh, revoke };
