#!/usr/bin/env node

/**
 * 同程程心 API 客户端
 *
 * 提供统一的 API 调用接口和配置管理
 */

const https = require('https');
const http = require('http');
const url = require('url');
const fs = require('fs');
const path = require('path');
const os = require('os');
const child_process = require('child_process');

// 接口基础地址优先级：环境变量 CHENGXIN_API_BASE > 技能根 config.json 的 apiBase
//   > tc-chengxin CLI 的 cli-config.json 的 gatewayBase（本地联调与 CLI 同网关）> 默认生产网关
const DEFAULT_API_BASE = 'https://wx.17u.cn/skills/gateway/api/v1/gateway';
let API_BASE_URL = process.env.CHENGXIN_API_BASE || '';
const API_VERSION = '1.0.0';
const AUTH_ALLOWED_HOSTS = new Set([
  'wx.17u.cn',
  'search.17usoft.com',
  'search.t.17usoft.com',
  '127.0.0.1',
  'localhost',
  '::1'
]);
const CALLER_CHANNELS = new Set([
  'qclaw',
  'clawhub',
  'miclaw',
  'skillhub',
  'xiaoyiclaw',
  'workbuddy'
]);

// 业务查询的 socket 等待/空闲超时（20 秒），不影响 CLI 授权超时。
const API_TIMEOUT = 20000;
const AUTH_INVALIDATE_TIMEOUT = 3000;

// 鉴权 token（优先级：环境变量 > config.json）
let API_KEY = process.env.CHENGXIN_API_KEY;

// 读取技能根 config.json：apiKey（兜底）与可选 apiBase
try {
  const config_path = path.join(__dirname, '..', '..', 'config.json');
  const config = JSON.parse(fs.readFileSync(config_path, 'utf8'));
  if (!API_KEY) {
    API_KEY = config.apiKey;
  }
  if (!API_BASE_URL && config.apiBase) {
    API_BASE_URL = config.apiBase;
  }
} catch (e) {
  // 静默处理：文件不存在走试用额度，其他异常由后续 API 调用的错误码 3 引导配置
}

// 仍未指定网关时，尝试读取 tc-chengxin CLI 的网关配置（本地联调时自动与 CLI 指向同一网关）
if (!API_BASE_URL) {
  try {
    const cli_cfg = JSON.parse(
      fs.readFileSync(path.join(os.homedir(), '.tc-chengxin', 'cli-config.json'), 'utf8')
    );
    if (cli_cfg && cli_cfg.gatewayBase) {
      API_BASE_URL = String(cli_cfg.gatewayBase).replace(/\/+$/, '') + '/api/v1/gateway';
    }
  } catch (e) {
    // 静默处理
  }
}

if (!API_BASE_URL) {
  API_BASE_URL = DEFAULT_API_BASE;
}

/**
 * 获取 API Key
 * @returns {string|null} API Key 或 null
 */
function get_api_key() {
  return API_KEY || null;
}

/**
 * 构建 Authorization Token
 * @param {string} key - API Key
 * @returns {string} Token 字符串
 */
function build_auth_token(key) {
  if (!key) return '';
  return `Bearer ${key}`;
}

/**
 * 调用同程程心 API
 * @param {string} api_path - API 路径（如 /trainResource）
 * @param {object} params - 查询参数
 * @returns {Promise<object>} API 响应
 */
function call_api(api_path, params) {
  return new Promise((resolve, reject) => {
    const api_url = `${API_BASE_URL}${api_path}`;
    const parsed_url = url.parse(api_url);
    const is_https = parsed_url.protocol === 'https:';
    // 安全策略：默认强制 HTTPS；仅本地回环地址(127.0.0.1/localhost)允许 HTTP，便于本地联调
    const is_loopback = is_loopback_host(parsed_url.hostname);
    if (!is_https && !is_loopback) {
      reject(new Error('仅支持 HTTPS 协议（本地回环地址除外），请检查 API_BASE_URL'));
      return;
    }
    if (API_KEY && !is_auth_allowed_host(parsed_url.hostname)) {
      reject(new Error('拒绝向未授权网关发送同程授权令牌，请检查 API_BASE_URL'));
      return;
    }
    const transport = is_https ? https : http;
    const is_workbuddy_expert = String(process.env.CHENGXIN_WORKBUDDY_EXPERT || '').trim() === '1';
    const caller_channel = is_workbuddy_expert
      ? 'workbuddy'
      : normalize_caller_channel(params && params.callerChannel);

    const post_data = JSON.stringify({
      ...params,
      ...(caller_channel ? { callerChannel: caller_channel } : {}),
      version: API_VERSION
    });

    const options = {
      hostname: parsed_url.hostname,
      port: parsed_url.port || (is_https ? 443 : 80),
      path: parsed_url.path,
      method: 'POST',
      timeout: API_TIMEOUT,
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(post_data),
        'User-Agent': `TC-Chengxin-NodeJS/${API_VERSION}`,
        'Accept': 'application/json, text/plain, */*',
        'Origin': 'https://www.ly.com',
        'Referer': 'https://www.ly.com/',
        ...(caller_channel ? { 'X-Skill-Caller-Channel': caller_channel } : {}),
        ...(API_KEY ? { 'Authorization': build_auth_token(API_KEY) } : {})
      }
    };

    const req = transport.request(options, (res) => {
      let data = '';

      res.on('data', (chunk) => {
        data += chunk;
      });

      res.on('end', () => {
        // 检查 HTTP 状态码
        if (res.statusCode < 200 || res.statusCode >= 300) {
          const error = new Error(`HTTP 错误：${res.statusCode} ${res.statusMessage || ''}`);
          error.statusCode = res.statusCode;
          error.callerChannel = caller_channel;
          if (res.statusCode === 401) {
            error.code = 'CHENGXIN_AUTH_REQUIRED';
            if (caller_channel === 'workbuddy') {
              const invalidation = invalidate_workbuddy_auth();
              error.authInvalidated = invalidation.invalidated;
              error.authInvalidationReason = invalidation.reason || '';
            }
          }
          reject(error);
          return;
        }

        try {
          const result = JSON.parse(data);
          resolve(result);
        } catch (e) {
          reject(new Error(`解析响应失败：${e.message}`));
        }
      });
    });

    // 超时处理
    req.on('timeout', () => {
      req.destroy();
      reject(new Error(`请求超时（${API_TIMEOUT / 1000}秒）`));
    });

    req.on('error', (e) => {
      reject(new Error(`请求失败：${e.message}`));
    });

    req.write(post_data);
    req.end();
  });
}

function normalize_caller_channel(value) {
  const normalized = String(value || '').trim().toLowerCase();
  return CALLER_CHANNELS.has(normalized) ? normalized : '';
}

/**
 * 验证 API Key 是否已配置
 * @returns {boolean} 是否已配置
 */
function is_configured() {
  return !!API_KEY;
}

/**
 * 获取配置错误信息
 * @returns {string} 错误信息
 */
function get_config_error() {
  if (!API_KEY) {
    return '未找到 CHENGXIN_API_KEY 环境变量或 config.json 文件\n请设置环境变量或在技能目录下创建 config.json 文件';
  }
  return '';
}

function is_loopback_host(hostname) {
  return ['127.0.0.1', 'localhost', '::1'].includes(String(hostname || '').toLowerCase());
}

function is_auth_allowed_host(hostname) {
  const host = String(hostname || '').toLowerCase();
  return AUTH_ALLOWED_HOSTS.has(host) || host.endsWith('.17u.cn') || host.endsWith('.17usoft.com');
}

function resolve_cli_command(platform = process.platform, env = process.env) {
  if (env.TC_CHENGXIN_CLI_PATH) {
    return env.TC_CHENGXIN_CLI_PATH;
  }
  const executable = platform === 'win32' ? 'tc-chengxin.cmd' : 'tc-chengxin';
  const workbuddy_dir = String(env.WORKBUDDY_CONFIG_DIR || '').trim()
    || path.join(os.homedir(), '.workbuddy');
  const managed_cli = path.join(
    workbuddy_dir,
    'binaries',
    'node',
    'cli-connector-packages',
    'bin',
    executable
  );
  return fs.existsSync(managed_cli) ? managed_cli : executable;
}

/**
 * WorkBuddy 业务接口返回 401 后，仅清除 CLI 本地失效凭证。
 * 不调用 logout/revoke，避免在异常链路上增加远端请求和等待时间。
 */
function invalidate_workbuddy_auth(options = {}) {
  const env = options.env || process.env;
  const platform = options.platform || process.platform;
  const spawn_sync = options.spawnSync || child_process.spawnSync;
  try {
    const result = spawn_sync(resolve_cli_command(platform, env), ['auth', 'invalidate', '--json'], {
      encoding: 'utf8',
      env,
      timeout: AUTH_INVALIDATE_TIMEOUT,
      windowsHide: true
    });
    if (result && !result.error && result.status === 0) {
      return { invalidated: true };
    }
    return {
      invalidated: false,
      reason: result && result.error ? result.error.message : `exit=${result && result.status}`
    };
  } catch (error) {
    return { invalidated: false, reason: error.message };
  }
}

module.exports = {
  API_BASE_URL,
  API_VERSION,
  get_api_key,
  build_auth_token,
  call_api,
  is_configured,
  get_config_error,
  is_auth_allowed_host,
  resolve_cli_command,
  invalidate_workbuddy_auth
};
