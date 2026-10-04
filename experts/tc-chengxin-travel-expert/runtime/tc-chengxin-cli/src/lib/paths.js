'use strict';

const os = require('os');
const path = require('path');

// CLI 本地数据根目录
const HOME_DIR = path.join(os.homedir(), '.tc-chengxin');

module.exports = {
  homeDir: HOME_DIR,
  // 登录凭证（access/refresh/expire/user）
  credentialsFile: path.join(HOME_DIR, 'credentials.json'),
  // 进行中的授权会话（session_id/device_secret）
  sessionFile: path.join(HOME_DIR, 'session.json')
};
