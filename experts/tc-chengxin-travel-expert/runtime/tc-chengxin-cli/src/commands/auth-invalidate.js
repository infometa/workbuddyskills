'use strict';

const store = require('../lib/credential-store');

/**
 * 仅使本地授权状态失效，不请求远端 revoke。
 *
 * 业务接口返回 401 时由 WorkBuddy Skill 调用。清除旧凭证后，connector 的
 * auth status 会变为未登录，从而重新进入标准授权流程。
 *
 * @param {{json?: boolean}} [opts]
 * @returns {number}
 */
function authInvalidate(opts) {
  store.clearCredentials();
  store.clearSession();
  if (opts && opts.json) {
    process.stdout.write(JSON.stringify({ invalidated: true, authenticated: false }) + '\n');
  } else {
    process.stdout.write('Authentication invalidated; reauthorization required\n');
  }
  return 0;
}

module.exports = { authInvalidate };
