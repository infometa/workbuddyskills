'use strict';

const gateway = require('../lib/gateway-client');
const store = require('../lib/credential-store');

/**
 * auth logout：撤销并清空本地凭证。
 * @returns {Promise<number>}
 */
async function authLogout() {
  const creds = store.readCredentials();
  if (creds) {
    await gateway.revoke(creds);
  }
  store.clearCredentials();
  store.clearSession();
  process.stdout.write('Logged out\n');
  return 0;
}

module.exports = { authLogout };
