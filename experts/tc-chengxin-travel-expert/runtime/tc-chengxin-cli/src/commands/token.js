'use strict';

const { ensureFreshToken } = require('./auth-status');

/**
 * 打印当前有效 access_token（必要时静默续期）。
 * 未登录 / 凭证失效时：不输出 token，非零退出。
 * 供 Skill 用 `export CHENGXIN_API_KEY="$(tc-chengxin token)"` 注入查询脚本。
 */
async function token() {
  const creds = await ensureFreshToken();
  if (creds && creds.access_token) {
    process.stdout.write(creds.access_token + '\n');
    return 0;
  }
  process.stderr.write('未登录或凭证已失效，请在 WorkBuddy 中重新连接「同程旅行」\n');
  return 1;
}

module.exports = { token };
