'use strict';

const gateway = require('../lib/gateway-client');
const store = require('../lib/credential-store');
const config = require('../config');

// 把网关返回的 ready 结果落地为本地凭证
function finalizeReady(ready) {
  const now = Date.now();
  const creds = {
    access_token: ready.access_token,
    refresh_token: ready.refresh_token,
    access_expire_at: now + (Number(ready.expires_in) || 7200) * 1000,
    refresh_expire_at: now + (Number(ready.refresh_expires_in) || 7 * 24 * 3600) * 1000,
    user: ready.user || null
  };
  store.saveCredentials(creds);
  return creds;
}

// 确保本地有可用 token：必要时静默续期；返回 creds 或 null
async function ensureFreshToken() {
  let creds = store.readCredentials();
  const now = Date.now();
  if (isAccessTokenUsable(creds, now)) {
    return creds;
  }
  if (creds && creds.refresh_token && now < creds.refresh_expire_at) {
    try {
      const r = await gateway.refresh(creds.refresh_token);
      creds = {
        access_token: r.access_token,
        refresh_token: r.refresh_token || creds.refresh_token,
        access_expire_at: now + (Number(r.expires_in) || 7200) * 1000,
        refresh_expire_at: r.refresh_expires_in
          ? now + Number(r.refresh_expires_in) * 1000
          : creds.refresh_expire_at,
        user: creds.user
      };
      store.saveCredentials(creds);
      return creds;
    } catch (e) {
      return null;
    }
  }
  return null;
}

// 服务端返回的过期时间保留在凭证中；本地在该时间前 accessSkewMs 即进入续期窗口。
// 单独提取为纯函数，便于验证边界条件，避免未来调整刷新策略时引入回归。
function isAccessTokenUsable(creds, now) {
  const accessExpireAt = Number(creds && creds.access_expire_at);
  return Boolean(
    creds &&
      creds.access_token &&
      Number.isFinite(accessExpireAt) &&
      now < accessExpireAt - config.accessSkewMs
  );
}

async function authStatus(opts) {
  // 1) 已有有效/可续期 token
  let creds = await ensureFreshToken();
  if (creds) return emit(true, creds, opts);

  // 2) 有进行中的授权会话 → 轮询
  const session = store.readSession();
  if (session && session.session_id) {
    try {
      const p = await gateway.poll(session.session_id, session.device_secret);
      if (p.status === 'ready') {
        creds = finalizeReady(p);
        store.clearSession();
        return emit(true, creds, opts);
      }
      if (p.status === 'expired' || p.status === 'error') {
        store.clearSession();
        return emit(false, null, opts, {
          status: p.status,
          reason: p.error || (p.status === 'expired' ? 'session_expired' : 'authorization_failed')
        });
      }
    } catch (e) {
      /* 网络问题，视为未认证 */
    }
  }
  return emit(false, null, opts);
}

function emit(authenticated, creds, opts, detail) {
  if (opts && opts.json) {
    process.stdout.write(JSON.stringify({ authenticated: authenticated, ...(detail || {}) }) + '\n');
  } else if (authenticated) {
    process.stdout.write('Logged in' + (creds && creds.user ? ' as ' + creds.user : '') + '\n');
  } else {
    process.stdout.write('Not logged in\n');
  }
  return authenticated ? 0 : 1;
}

module.exports = { authStatus, finalizeReady, ensureFreshToken, isAccessTokenUsable };
