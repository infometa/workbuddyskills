#!/usr/bin/env node
// SessionStart Handler：会话开始时从远端 API 拉取配置，按 updatedTime 增量同步本地 JSON 文件。
//
// 输入 (stdin JSON)：
//   { "session_id": "...", "transcript_path": "...", "cwd": "...", "hook_event_name": "SessionStart", "source": "startup" }
// 输出 (stdout JSON)：
//   { "continue": true }
//
// 工作流程：
//   1. GET /api/hook-config/list → 所有配置的 configName + category + updatedTime
//   2. 读 hooks/hr-ai-data/data/_versions.json → 对比 updatedTime，筛选变更的配置
//   3. 如果有变更 → GET /api/hook-config/batch?configNames=... → 1 次请求拿全变更数据
//   4. 写入 JSON 文件 + 删除远端已不存在的本地文件 + 更新 _versions.json
//   5. 如果无变更 → 结束，不发起额外请求
//
// 环境变量：
//   SYS_CONFIG_API_BASE  — API 基础地址（默认 http://9.135.247.190:32376）
//   HOOK_STAFF_ID        — 认证用 staffid（可选）
//   HOOK_STAFF_NAME      — 认证用 staffname（可选）
//   HOOK_API_TIMEOUT_MS  — 请求超时毫秒（默认 10000）

'use strict';

const fs = require('fs');
const path = require('path');
const https = require('https');
const http = require('http');

const PLUGIN_ROOT = path.resolve(__dirname, '..', '..', '..');
const DATA_DIR = path.join(PLUGIN_ROOT, 'hooks', 'hr-ai-data', 'data');
const VERSIONS_FILE = path.join(DATA_DIR, '_versions.json');
// 行为控制配置（与其他 hook 一致：data/config/config_session_start.json）
const CONFIG_FILE = path.join(DATA_DIR, 'config', 'config_session_start.json');

let _config = null;
function loadConfig() {
  if (_config !== null) return _config;
  try { _config = fs.existsSync(CONFIG_FILE) ? JSON.parse(fs.readFileSync(CONFIG_FILE, 'utf8')) : {}; }
  catch (_) { _config = {}; }
  return _config;
}
// 日志开关：默认开启，显式 enable_logging=false 时关闭（与 pre_tool/user_prompt 配置风格一致）
function isLoggingEnabled() { return loadConfig().enable_logging !== false; }

// -- 可配置项 ------------------------------------------------------------------
const API_BASE_URL = process.env.SYS_CONFIG_API_BASE || 'https://text2api.woa.com';
const API_LIST_PATH = '/newApi/hook-config/list';
const API_BATCH_PATH = '/newApi/hook-config/batch';
const BATCH_MAX = 20;
const TIMEOUT_MS = parseInt(process.env.HOOK_API_TIMEOUT_MS, 10) || 10000;
const LOG_DIR = path.join(PLUGIN_ROOT, 'logs');

// -- 双写日志：同时输出到 stderr 和 logs/session_start.log --------------------
// 由 config_session_start.json 的 enable_logging 控制，false 时完全静默
function log(msg) {
  if (!isLoggingEnabled()) return;
  const line = '[' + new Date().toISOString().replace('T', ' ').substring(0, 19) + '] ' + msg;
  console.error(line);
  try {
    if (!fs.existsSync(LOG_DIR)) fs.mkdirSync(LOG_DIR, { recursive: true });
    fs.appendFileSync(path.join(LOG_DIR, 'session_start.log'), line + '\n', 'utf8');
  } catch (_) { /* ignore */ }
}

// -- stdin 读取（兼容 BOM）-----------------------------------------------------
function readStdin() {
  return new Promise((resolve) => {
    let raw = '';
    process.stdin.setEncoding('utf8');
    process.stdin.on('data', (c) => { raw += c; });
    process.stdin.on('end', () => {
      const cleaned = raw.replace(/^[\uFEFF\uFFFE\u200B\u200C\u200D\u2060]+/, '').trim();
      try { resolve(JSON.parse(cleaned)); } catch (_) { resolve({}); }
    });
    process.stdin.on('error', () => resolve({}));
  });
}

// -- HTTP GET ------------------------------------------------------------------
function httpGet(urlPath) {
  return new Promise((resolve, reject) => {
    const url = new URL(urlPath, API_BASE_URL);
    const mod = url.protocol === 'https:' ? https : http;
    const headers = {};
    const staffId = process.env.HOOK_STAFF_ID;
    const staffName = process.env.HOOK_STAFF_NAME;
    if (staffId) headers['staffid'] = staffId;
    if (staffName) headers['staffname'] = staffName;

    const req = mod.get(url.toString(), { timeout: TIMEOUT_MS, headers }, (res) => {
      let body = '';
      res.on('data', (chunk) => { body += chunk; });
      res.on('end', () => {
        try {
          const json = JSON.parse(body);
          if (json.code !== 0) {
            reject(new Error('API returned code ' + json.code));
            return;
          }
          resolve(json);
        } catch (e) {
          reject(new Error('JSON parse error: ' + e.message));
        }
      });
    });
    req.on('error', reject);
    req.on('timeout', () => { req.destroy(); reject(new Error('Request timeout')); });
  });
}

// -- JSON 重建逻辑（使用 JSON.stringify 标准序列化，杜绝尾随逗号）------------
function rebuildJson(configType, description, items) {
  const root = {};

  if (description && description.length > 0) {
    root._comment = description;
  }

  if (configType === 'KV') {
    for (const item of items) {
      const val = item.itemValue === 'true' ? true
                : item.itemValue === 'false' ? false
                : item.itemValue;
      root[item.itemKey] = val;
    }
  } else {
    const groups = {};
    for (const item of items) {
      const type = item.itemType || 'entries';
      if (!groups[type]) groups[type] = [];
      groups[type].push(item.itemValue);
    }

    const keyMap = { tool: 'tools', pattern: 'safe_patterns', domain: 'domains',
                     ip: 'ips', server: 'servers', entry: 'entries' };

    for (const [type, values] of Object.entries(groups)) {
      root[keyMap[type] || 'entries'] = values;
    }
  }

  return JSON.stringify(root, null, 2) + '\n';
}

// -- 版本文件读写 --------------------------------------------------------------
function readVersions() {
  try {
    if (fs.existsSync(VERSIONS_FILE)) {
      return JSON.parse(fs.readFileSync(VERSIONS_FILE, 'utf8'));
    }
  } catch (_) { /* ignore */ }
  return {};
}

function writeVersions(map) {
  try {
    const dir = path.dirname(VERSIONS_FILE);
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
    fs.writeFileSync(VERSIONS_FILE, JSON.stringify(map, null, 2), 'utf8');
  } catch (e) {
    log('[session_start] 写入 _versions.json 失败: ' + e.message);
  }
}

// -- 收集本地已有的配置文件路径 -------------------------------------------------
function collectLocalFiles() {
  const files = [];
  if (!fs.existsSync(DATA_DIR)) return files;

  function walk(dir, prefix) {
    const entries = fs.readdirSync(dir, { withFileTypes: true });
    for (const e of entries) {
      if (e.isDirectory()) {
        walk(path.join(dir, e.name), prefix + e.name + '/');
      } else if (e.isFile() && e.name.endsWith('.json') && e.name !== '_versions.json') {
        files.push(prefix + e.name);
      }
    }
  }
  walk(DATA_DIR, '');
  return files;
}

// -- 删除远端已不存在的本地配置文件 ---------------------------------------------
function removeStaleFiles(serverRelPaths, localFiles) {
  const serverSet = new Set(serverRelPaths);
  for (const relPath of localFiles) {
    if (!serverSet.has(relPath)) {
      const target = path.join(DATA_DIR, relPath);
      try {
        fs.unlinkSync(target);
        log('[session_start] 已删除（远端不存在）: ' + relPath);
      } catch (e) {
        log('[session_start] 删除失败: ' + relPath + ' — ' + e.message);
      }
    }
  }
}

// -- 远端配置拉取（版本比对 + 增量同步）------------------------------------------
async function fetchAndSync() {
  // 1. 获取配置列表（含 updatedTime）
  let listResp;
  try {
    listResp = await httpGet(API_LIST_PATH);
  } catch (e) {
    log('[session_start] 获取配置列表失败（网络不通/未在内网），保留本地文件不变');
    log('[session_start] 错误: ' + e.message);
    return false;
  }

  if (!listResp.data || !Array.isArray(listResp.data)) {
    log('[session_start] 配置列表数据异常，保留本地文件不变');
    return false;
  }

  const configList = listResp.data;
  log('[session_start] 远端 ' + configList.length + ' 个配置');

  // 2. 读本地版本记录，对比 updatedTime
  const oldVersions = readVersions();
  const newVersions = {};
  const changedNames = [];
  const serverRelPaths = [];

  const addedConfigs = [];    // 远端新增（本地无记录）
  const updatedConfigs = [];  // 远端更新（时间不同）
  const detailLog = [];       // 汇总变更明细

  for (const cfg of configList) {
    const relPath = cfg.category + '/' + cfg.configName + '.json';
    serverRelPaths.push(relPath);
    newVersions[relPath] = cfg.updatedTime || '';

    const oldTime = oldVersions[relPath];
    if (!oldTime) {
      // 新增配置
      addedConfigs.push(relPath);
      changedNames.push(cfg.configName);
      detailLog.push('  [新增] ' + relPath + ' → ' + (cfg.updatedTime || '无'));
    } else if (oldTime !== cfg.updatedTime) {
      // 更新配置
      updatedConfigs.push(relPath);
      changedNames.push(cfg.configName);
      detailLog.push('  [更新] ' + relPath + '  ' + oldTime + ' → ' + cfg.updatedTime);
    }
  }

  // 3. 清理远端已删除的本地文件，并记录
  const localFiles = collectLocalFiles();
  const deletedFiles = localFiles.filter(f => !serverRelPaths.includes(f));
  const hasDeletions = deletedFiles.length > 0;

  if (hasDeletions) {
    log('[session_start] 远端已删除，清理本地文件：');
    for (const f of deletedFiles) {
      log('  [删除] ' + f);
    }
  }

  // 输出变更汇总
  if (detailLog.length > 0) {
    log('[session_start] 以下配置文件发生变更：');
    for (const line of detailLog) {
      log(line);
    }
  }

  removeStaleFiles(serverRelPaths, localFiles);

  // 4. 如果没有任何变更（含删除），直接返回
  if (changedNames.length === 0 && !hasDeletions) {
    log('[session_start] 无变更，跳过拉取');
    return true;
  }

  log('[session_start] 共 ' + changedNames.length + ' 个配置变更（新增 ' + addedConfigs.length + '，更新 ' + updatedConfigs.length + '，删除 ' + deletedFiles.length + '），批量拉取...');

  // 5. 分批调用 /batch（上限 BATCH_MAX 个）
  const result = {};
  let batchFailed = false;

  for (let i = 0; i < changedNames.length; i += BATCH_MAX) {
    const batch = changedNames.slice(i, i + BATCH_MAX);
    const qs = batch.map(encodeURIComponent).join(',');
    try {
      const resp = await httpGet(API_BATCH_PATH + '?configNames=' + qs);
      if (resp.data && Array.isArray(resp.data)) {
        for (const detail of resp.data) {
          const cfg = configList.find(c => c.configName === detail.configName);
          if (!cfg) continue;
          const relPath = cfg.category + '/' + cfg.configName + '.json';
          result[relPath] = rebuildJson(detail.configType, detail.description, detail.items || []);
          log('[session_start]   OK: ' + relPath + ' (' + (detail.items || []).length + ' 条)');
        }
      }
    } catch (e) {
      log('[session_start] 批量拉取失败（第 ' + (Math.floor(i / BATCH_MAX) + 1) + ' 批）: ' + e.message);
      batchFailed = true;
      break;
    }
  }

  // 6. 任意一批失败 → 放弃本次写入（保留本地全部文件）
  if (batchFailed) {
    log('[session_start] 批量拉取未全部完成，放弃写入，保留本地文件不变');
    return false;
  }

  // 7. 写入文件 + 更新 _versions.json
  applyConfig(result);
  writeVersions(newVersions);
  log('[session_start] 同步完成');
  return true;
}

// -- 写入配置文件 ----------------------------------------------------------------
function applyConfig(configMap) {
  for (const [relPath, content] of Object.entries(configMap)) {
    if (content === null || content === undefined) continue;
    const target = path.join(DATA_DIR, relPath);
    try {
      fs.mkdirSync(path.dirname(target), { recursive: true });
      fs.writeFileSync(target, content, 'utf8');
    } catch (e) {
      log('[session_start] 写入失败: ' + relPath + ' — ' + e.message);
    }
  }
}

// -- 主流程 --------------------------------------------------------------------
async function main() {
  await readStdin();

  try {
    await fetchAndSync();
  } catch (e) {
    log('[session_start] 执行异常（保留本地文件）: ' + e.message);
  }

  process.stdout.write(JSON.stringify({ continue: true }));
  process.exit(0);
}

main().catch((err) => {
  log('[session_start] 未捕获异常（保留本地文件）: ' + (err && err.message));
  try { process.stdout.write(JSON.stringify({ continue: true })); } catch (_) {}
  process.exit(0);
});
