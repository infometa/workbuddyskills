'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const runtimeConfig = require('./runtime-config.json');

const TRUSTED_GATEWAY_HOSTS = new Set(['wx.17u.cn', 'wx.t.17u.cn']);
const LOOPBACK_HOSTS = new Set(['127.0.0.1', 'localhost', '::1', '[::1]']);

/**
 * CLI 运行配置
 *
 * 网关地址默认指向同程程心网关（skill-gateway），其上挂载了
 * /api/v1/oauth/cli/* 设备码式授权端点。
 *
 * 网关地址来源优先级：环境变量 TC_GATEWAY_BASE > 本地配置文件
 * ~/.tc-chengxin/cli-config.json 的 gatewayBase > 打包生成的默认值。
 * （WorkBuddy 以子进程方式启动 CLI，未必继承 shell 环境变量，
 *  故本地联调推荐用配置文件指定测试网关。）
 *
 * 安全约束：
 * - 生产/测试网关只允许同程可信域名，并且必须使用 HTTPS。
 * - HTTP 仅允许本机 loopback 地址，避免 token 被配置劫持到不可信网关。
 */
const DEFAULT_GATEWAY_BASE = runtimeConfig.gatewayBase || 'https://wx.17u.cn/skills/gateway';

function fileGatewayBase() {
  try {
    const p = path.join(os.homedir(), '.tc-chengxin', 'cli-config.json');
    const c = JSON.parse(fs.readFileSync(p, 'utf8'));
    return c && c.gatewayBase ? c.gatewayBase : null;
  } catch (e) {
    return null;
  }
}

function isLoopbackHost(hostname) {
  return LOOPBACK_HOSTS.has(String(hostname || '').toLowerCase());
}

function normalizeGatewayBase(rawValue) {
  return String(rawValue || '').trim().replace(/\/+$/, '');
}

function validateGatewayBase(rawValue) {
  const gatewayBase = normalizeGatewayBase(rawValue);
  if (!gatewayBase) {
    throw new Error('网关地址不能为空');
  }

  let u;
  try {
    u = new URL(gatewayBase);
  } catch (e) {
    throw new Error(`非法网关地址: ${gatewayBase}`);
  }

  const hostname = String(u.hostname || '').toLowerCase();
  const loopback = isLoopbackHost(hostname);

  if (u.protocol === 'http:') {
    if (!loopback) {
      throw new Error(`非本地网关必须使用 HTTPS: ${gatewayBase}`);
    }
  } else if (u.protocol !== 'https:') {
    throw new Error(`仅支持 HTTP(S) 网关地址: ${gatewayBase}`);
  }

  if (!loopback && !TRUSTED_GATEWAY_HOSTS.has(hostname)) {
    throw new Error(`不可信网关域名: ${hostname}`);
  }

  return gatewayBase;
}

const gatewayBase = validateGatewayBase(
  process.env.TC_GATEWAY_BASE || fileGatewayBase() || DEFAULT_GATEWAY_BASE
);

module.exports = {
  // 网关 base（不含末尾斜杠）
  gatewayBase,
  // 轮询间隔
  pollIntervalMs: 3000,
  // 交互式登录最长等待（与 WorkBuddy 的 5 分钟一致）
  loginTimeoutMs: 5 * 60 * 1000,
  // access_token 提前 1.5 小时续期。
  // 授权服务返回的有效期为 2 小时；保留服务端真实过期时间，
  // 仅将本地“可继续使用”的截止点前移 1.5 小时，尽量避开服务端提前失效窗口。
  accessSkewMs: 90 * 60 * 1000,
  // HTTP 超时：WorkBuddy 要求 auth/status 在 10 秒内返回
  httpTimeoutMs: 9000,
  _internal: {
    isLoopbackHost,
    validateGatewayBase
  }
};
