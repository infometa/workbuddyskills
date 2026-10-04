'use strict';

const fs = require('fs');
const paths = require('./paths');

function ensureHome() {
  fs.mkdirSync(paths.homeDir, { recursive: true, mode: 0o700 });
  try {
    fs.chmodSync(paths.homeDir, 0o700);
  } catch (e) {
    /* ignore */
  }
}

function readJson(file) {
  try {
    return JSON.parse(fs.readFileSync(file, 'utf8'));
  } catch (e) {
    return null;
  }
}

function writeJson(file, obj) {
  ensureHome();
  fs.writeFileSync(file, JSON.stringify(obj, null, 2), { mode: 0o600 });
  try {
    fs.chmodSync(file, 0o600);
  } catch (e) {
    /* ignore */
  }
}

// ---- 登录凭证 ----
function readCredentials() {
  return readJson(paths.credentialsFile);
}
function saveCredentials(c) {
  writeJson(paths.credentialsFile, c);
}
function clearCredentials() {
  try {
    fs.unlinkSync(paths.credentialsFile);
  } catch (e) {
    /* ignore */
  }
}

// ---- 进行中的授权会话 ----
function readSession() {
  return readJson(paths.sessionFile);
}
function saveSession(s) {
  writeJson(paths.sessionFile, s);
}
function clearSession() {
  try {
    fs.unlinkSync(paths.sessionFile);
  } catch (e) {
    /* ignore */
  }
}

module.exports = {
  readCredentials,
  saveCredentials,
  clearCredentials,
  readSession,
  saveSession,
  clearSession
};
